# vLLM Guided Decoding 구현 계획서

> **문서 버전**: 1.0.0
> **작성일**: 2026-01-31
> **상태**: 계획 (Planning)
> **담당팀**: SSAFY YEJI AI팀
> **관련 문서**: [JSON 정확도 개선 PRD](./json-accuracy-improvement.md), [JSON 정확도 전략 분석](/ai/docs/analysis/json-accuracy-strategy-analysis.md)

---

## 목차

1. [Executive Summary](#1-executive-summary)
2. [현재 상황 분석](#2-현재-상황-분석)
3. [기술 분석: Guided Decoding](#3-기술-분석-guided-decoding)
4. [response_format vs guided_json 비교](#4-response_format-vs-guided_json-비교)
5. [vLLM 서버 지원 여부 확인](#5-vllm-서버-지원-여부-확인)
6. [구현 계획](#6-구현-계획)
7. [코드 변경점 분석](#7-코드-변경점-분석)
8. [폴백 전략](#8-폴백-전략)
9. [테스트 계획](#9-테스트-계획)
10. [리스크 및 완화 방안](#10-리스크-및-완화-방안)
11. [참조 자료](#11-참조-자료)

---

## 1. Executive Summary

### 1.1 목적

yeji-ai-server의 LLM JSON 응답 정확도를 **30% 실패율에서 5% 이하로 개선**하기 위해 vLLM의 **Guided Decoding** 기능 적용 가능성을 분석하고 구현 계획을 수립합니다.

### 1.2 핵심 결론

| 항목 | 결론 |
|------|------|
| **guided_json 지원 여부** | vLLM 0.8+ 버전에서 지원 (확인 필요) |
| **현재 방식과의 차이** | `response_format: json_object`는 단순 JSON 강제, `guided_json`은 스키마 준수 보장 |
| **권장 전략** | **하이브리드 접근** (guided_json + 후처리 파이프라인) |
| **예상 개선 효과** | JSON 검증 성공률 70% → 95-99% |

### 1.3 요약 비교표

| 기능 | `response_format: {"type": "json_object"}` | `guided_json` (extra_body) |
|------|---------------------------------------------|---------------------------|
| JSON 문법 보장 | O (유효한 JSON) | O (유효한 JSON) |
| 스키마 준수 보장 | X | **O (필수 필드, 타입 보장)** |
| Enum 값 강제 | X | **O** |
| 중첩 구조 검증 | X | **O** |
| 레이턴시 오버헤드 | ~0% | 3-10% (캐싱 시 ~5%) |
| vLLM 버전 요구사항 | 0.4+ | **0.8+ (XGrammar/Outlines)** |

---

## 2. 현재 상황 분석

### 2.1 인프라 현황

| 항목 | 값 | 비고 |
|------|-----|------|
| vLLM 서버 | AWS GPU (13.125.68.166:8001) | OpenAI-compatible API |
| 모델 | `tellang/yeji-8b-rslora-v7-AWQ` | Qwen3 8B, AWQ 양자화 |
| 최대 컨텍스트 | 4096 tokens | 긴 프롬프트 제한 |
| 현재 구조화 방식 | `response_format: {"type": "json_object"}` | 기본 JSON 모드만 사용 |

### 2.2 현재 코드 분석

#### 2.2.1 vllm_client.py (이미 guided_json 지원 구현됨)

```python
# clients/vllm_client.py:26-28 - 이미 정의되어 있으나 미사용
@dataclass
class GenerationConfig:
    # ... 기타 설정
    guided_json: dict | None = None  # JSON 스키마로 출력 제약
    guided_choice: list[str] | None = None  # 선택지 제약
    guided_regex: str | None = None  # 정규식 제약

# clients/vllm_client.py:188-198
async def chat(...):
    # vLLM guided decoding 옵션 추가
    extra_body = {}
    if config.guided_json:
        extra_body["guided_json"] = config.guided_json
    if config.guided_choice:
        extra_body["guided_choice"] = config.guided_choice
    if config.guided_regex:
        extra_body["guided_regex"] = config.guided_regex

    if extra_body:
        payload["extra_body"] = extra_body
```

#### 2.2.2 llm_interpreter.py (현재 response_format만 사용)

```python
# services/llm_interpreter.py:946-960
async def _call_llm_structured(...):
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            self.chat_url,
            json={
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                # 현재: vLLM 0.14+ OpenAI 호환 response_format
                "response_format": {"type": "json_object"},  # ← 스키마 강제 없음
            },
        )
```

### 2.3 현재 문제점

| 문제 유형 | 발생 빈도 | 원인 |
|-----------|-----------|------|
| Pydantic 검증 실패 | ~30% | 스키마 미준수 |
| 필수 필드 누락 | ~20% | JSON 모드만으로는 필드 강제 불가 |
| Enum 값 불일치 | ~15% | 대소문자, 유사어 혼동 |
| 구조 불일치 | ~10% | 중첩 구조 오류 |

---

## 3. 기술 분석: Guided Decoding

### 3.1 Guided Decoding이란?

Guided Decoding(구조화된 디코딩)은 LLM 추론 과정에서 **토큰 생성 시점에 유효한 토큰만 선택하도록 제약**을 거는 기술입니다.

```
일반 LLM 생성:
[모든 토큰 확률] → [샘플링] → [출력]
                    ↑ 제약 없음

Guided Decoding:
[모든 토큰 확률] → [유효 토큰 마스킹] → [샘플링] → [출력]
                    ↑ 스키마 기반 제약
```

### 3.2 vLLM의 Guided Decoding 백엔드

vLLM 0.8+ 버전에서는 여러 백엔드를 지원합니다.

| 백엔드 | 특징 | 권장 사용 케이스 |
|--------|------|-----------------|
| **XGrammar** (기본) | 반복 스키마에서 캐싱 최적화, 빠른 TTFT | 정적 스키마, 높은 처리량 |
| **LLGuidance** | 동적/복잡 스키마에서 더 나은 성능 | 복잡한 중첩 구조 |
| **Outlines** | 안정적인 폴백 옵션 | XGrammar 미지원 시 |

### 3.3 지원하는 제약 타입

```python
# vLLM extra_body 또는 structured_outputs 파라미터

# 1. JSON 스키마 제약
"guided_json": {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer"}
    },
    "required": ["name", "age"]
}

# 2. 선택지 제약
"guided_choice": ["positive", "negative", "neutral"]

# 3. 정규식 제약
"guided_regex": r"\d{4}-\d{2}-\d{2}"

# 4. 문법 제약 (EBNF)
"guided_grammar": "root ::= ('yes' | 'no')"
```

### 3.4 2026년 최신 동향

vLLM v0.14+ 버전에서는 두 가지 방식으로 구조화된 출력을 지정할 수 있습니다:

**방식 1: OpenAI 호환 response_format (권장)**
```python
"response_format": {
    "type": "json_schema",
    "json_schema": {
        "name": "my-schema",
        "schema": MyPydanticModel.model_json_schema()
    }
}
```

**방식 2: vLLM 네이티브 extra_body (레거시)**
```python
"extra_body": {
    "guided_json": MyPydanticModel.model_json_schema()
}
```

**방식 3: structured_outputs (최신, v0.12+)**
```python
"extra_body": {
    "structured_outputs": {
        "json": MyPydanticModel.model_json_schema()
    }
}
```

---

## 4. response_format vs guided_json 비교

### 4.1 기능 비교

| 기능 | `response_format: {"type": "json_object"}` | `response_format: {"type": "json_schema", ...}` | `guided_json` (extra_body) |
|------|---------------------------------------------|------------------------------------------------|---------------------------|
| **동작 방식** | 프롬프트에 JSON 출력 지시 | 스키마 기반 토큰 마스킹 | 스키마 기반 토큰 마스킹 |
| **JSON 문법 보장** | O | O | O |
| **필수 필드 보장** | X | **O** | **O** |
| **타입 검증** | X | **O** | **O** |
| **Enum 값 강제** | X | **O** | **O** |
| **중첩 구조 검증** | X | **O** | **O** |
| **OpenAI API 호환** | O | O (vLLM 확장) | X (vLLM 전용) |
| **vLLM 버전 요구** | 0.4+ | 0.8+ | 0.8+ |

### 4.2 상세 동작 차이

#### 4.2.1 response_format: json_object (현재 사용 중)

```python
# 현재 llm_interpreter.py 방식
payload = {
    "model": "tellang/yeji-8b-rslora-v7-AWQ",
    "messages": messages,
    "response_format": {"type": "json_object"}
}
```

**동작**:
- LLM에게 "JSON 형식으로 출력하라"고 지시
- JSON 문법적으로 유효한 출력 보장 (`{...}`)
- **스키마 준수는 보장하지 않음**

**예시 출력 (실패 케이스)**:
```json
{
  "personality": "리더십이 강합니다",
  // 필수 필드 누락
  "badges": ["wood_strong"]  // 대소문자 오류
}
```

#### 4.2.2 guided_json / json_schema (권장 방식)

```python
# 개선된 방식
payload = {
    "model": "tellang/yeji-8b-rslora-v7-AWQ",
    "messages": messages,
    "response_format": {
        "type": "json_schema",
        "json_schema": {
            "name": "eastern-fortune",
            "schema": EasternFullLLMOutput.model_json_schema()
        }
    }
}
```

**동작**:
- 토큰 생성 시점에 스키마 기반 마스킹
- **필수 필드 존재 보장**
- **타입 및 Enum 값 강제**
- 잘못된 토큰은 생성 불가

**예시 출력 (성공 케이스)**:
```json
{
  "personality": "리더십이 강합니다",
  "strength": "결단력과 추진력",
  "weakness": "유연성 부족",
  "advice": "협력을 통해 균형을 맞추세요",
  "summary": "목(木)이 강한 리더형",
  "message": "그대의 사주를 살펴보겠소...",
  "badges": ["WOOD_STRONG", "YANG_DOMINANT"],  // 정확한 Enum 값
  "lucky": { ... }  // 필수 필드 모두 포함
}
```

### 4.3 성능 비교

| 메트릭 | json_object | guided_json/json_schema |
|--------|-------------|------------------------|
| 첫 토큰 지연 (TTFT) | 기준 | +5-15ms (스키마 컴파일) |
| 토큰당 지연 | 기준 | +0.5-2ms (마스킹 연산) |
| 전체 레이턴시 | 기준 | **+3-10%** |
| 스키마 캐싱 시 | - | **+3-5%** (2번째 요청부터) |
| 검증 성공률 | ~70% | **~95-99%** |

### 4.4 장단점 요약

#### guided_json / json_schema 장점

1. **필수 필드 100% 존재 보장**: 스키마에 정의된 required 필드 필수 생성
2. **타입 안전성**: string, integer, array 등 정확한 타입 생성
3. **Enum 값 강제**: `["WOOD", "FIRE", "EARTH", "METAL", "WATER"]` 중에서만 선택
4. **중첩 구조 보장**: 복잡한 객체 구조도 정확히 생성
5. **후처리 부담 감소**: 검증 실패 케이스 대폭 감소

#### guided_json / json_schema 단점

1. **레이턴시 증가**: 3-10% 오버헤드 (캐싱으로 완화 가능)
2. **추론 능력 저하 가능성**: 형식에 집중하여 내용 품질 10-15% 저하 연구 결과 있음
3. **복잡한 스키마 한계**: 매우 복잡한 스키마에서 XGrammar 미지원 가능
4. **vLLM 버전 의존성**: 0.8+ 버전 필요

---

## 5. vLLM 서버 지원 여부 확인

### 5.1 확인 방법

현재 운영 중인 vLLM 서버(13.125.68.166:8001)가 guided_json을 지원하는지 확인하는 방법입니다.

#### 방법 1: 버전 확인 API

```bash
# vLLM 서버 버전 확인
curl http://13.125.68.166:8001/version

# 또는 모델 정보에서 확인
curl http://13.125.68.166:8001/v1/models
```

#### 방법 2: 직접 테스트

```python
import httpx
import asyncio

async def test_guided_json_support():
    """guided_json 지원 여부 테스트"""
    url = "http://13.125.68.166:8001/v1/chat/completions"

    # 간단한 스키마로 테스트
    test_schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"}
        },
        "required": ["name", "age"]
    }

    payload = {
        "model": "tellang/yeji-8b-rslora-v7-AWQ",
        "messages": [
            {"role": "user", "content": "Generate a person with name and age."}
        ],
        "max_tokens": 100,
        # 방식 1: response_format json_schema (vLLM 0.8+)
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "person",
                "schema": test_schema
            }
        }
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(url, json=payload)
            if response.status_code == 200:
                print("✅ json_schema response_format 지원됨")
                print(response.json()["choices"][0]["message"]["content"])
            else:
                print(f"❌ 오류: {response.status_code}")
                print(response.text)
        except Exception as e:
            print(f"❌ 예외: {e}")

    # 방식 2: extra_body guided_json (레거시)
    payload_legacy = {
        "model": "tellang/yeji-8b-rslora-v7-AWQ",
        "messages": [
            {"role": "user", "content": "Generate a person with name and age."}
        ],
        "max_tokens": 100,
        "extra_body": {
            "guided_json": test_schema
        }
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(url, json=payload_legacy)
            if response.status_code == 200:
                print("✅ extra_body guided_json 지원됨")
                print(response.json()["choices"][0]["message"]["content"])
            else:
                print(f"❌ 오류: {response.status_code}")
                print(response.text)
        except Exception as e:
            print(f"❌ 예외: {e}")

asyncio.run(test_guided_json_support())
```

#### 방법 3: 서버 시작 옵션 확인

```bash
# vLLM 서버 시작 시 --guided-decoding-backend 옵션 확인
# SSH로 접속하여 프로세스 확인
ps aux | grep vllm
```

### 5.2 예상 결과 시나리오

| 시나리오 | 상태 | 대응 |
|----------|------|------|
| vLLM 0.8+ & XGrammar 활성화 | **지원** | guided_json/json_schema 사용 |
| vLLM 0.8+ & Outlines 폴백 | **지원** | guided_json/json_schema 사용 |
| vLLM 0.4-0.7 | **미지원** | response_format: json_object + 후처리 강화 |
| guided_json 비활성화 | **미지원** | 서버 재시작 필요 (--guided-decoding-backend 옵션) |

### 5.3 서버 설정 권장사항

guided_json이 미지원되는 경우, vLLM 서버 시작 시 다음 옵션 추가:

```bash
# vLLM 서버 시작 (guided decoding 활성화)
vllm serve tellang/yeji-8b-rslora-v7-AWQ \
    --host 0.0.0.0 \
    --port 8001 \
    --guided-decoding-backend auto  # xgrammar 우선, outlines 폴백

# 또는 특정 백엔드 지정
vllm serve ... --guided-decoding-backend xgrammar
vllm serve ... --guided-decoding-backend outlines
```

---

## 6. 구현 계획

### 6.1 구현 단계

```
Phase 1: 지원 여부 확인 (1일)
    ↓
Phase 2: llm_interpreter.py 수정 (2-3일)
    ↓
Phase 3: 폴백 전략 구현 (1-2일)
    ↓
Phase 4: 테스트 및 벤치마크 (2-3일)
    ↓
Phase 5: 점진적 롤아웃 (1주)
```

### 6.2 Phase 1: 지원 여부 확인 (1일)

**목표**: 현재 vLLM 서버의 guided decoding 지원 여부 확인

**작업 내용**:
1. vLLM 서버 버전 확인
2. 간단한 스키마로 guided_json 테스트
3. XGrammar vs Outlines 백엔드 확인
4. 지원되지 않는 경우 서버 재설정 협의

**산출물**:
- `scripts/test_guided_json.py` (테스트 스크립트)
- 지원 여부 보고서

### 6.3 Phase 2: llm_interpreter.py 수정 (2-3일)

**목표**: guided_json/json_schema 적용

**변경 파일**: `services/llm_interpreter.py`

**변경 내용**:
```python
# 변경 전: response_format: json_object만 사용
"response_format": {"type": "json_object"}

# 변경 후: json_schema로 스키마 강제
"response_format": {
    "type": "json_schema",
    "json_schema": {
        "name": response_schema.__name__.lower(),
        "schema": response_schema.model_json_schema()
    }
}
```

### 6.4 Phase 3: 폴백 전략 구현 (1-2일)

**목표**: guided_json 실패 시 graceful degradation

**구현 내용**:
- json_schema 실패 시 json_object 폴백
- 후처리 파이프라인 연계
- 에러 로깅 및 메트릭 수집

### 6.5 Phase 4: 테스트 및 벤치마크 (2-3일)

**목표**: 성능 및 정확도 검증

**테스트 항목**:
1. 기능 테스트: 모든 스키마에서 정상 동작
2. 성능 테스트: 레이턴시 오버헤드 측정
3. 정확도 테스트: Pydantic 검증 성공률 측정
4. 스트레스 테스트: 동시 요청 처리

### 6.6 Phase 5: 점진적 롤아웃 (1주)

**목표**: 프로덕션 안정적 배포

**롤아웃 단계**:
```
Day 1-2: ai/develop 브랜치 100%
Day 3-4: ai/main 10% (Feature Flag)
Day 5-6: ai/main 50%
Day 7:   ai/main 100%
```

---

## 7. 코드 변경점 분석

### 7.1 llm_interpreter.py 상세 변경

#### 현재 코드 (services/llm_interpreter.py:908-996)

```python
async def _call_llm_structured(
    self,
    system_prompt: str,
    user_prompt: str,
    response_schema: type[T],
    max_tokens: int = 800,
    temperature: float = 0.7,
    max_retries: int = 2,
) -> T:
    """
    구조화된 LLM API 호출 (response_format 사용)

    vLLM 0.14+에서는 response_format: {"type": "json_object"}를 사용합니다.
    """
    # ... 프롬프트 준비 ...

    for attempt in range(max_retries + 1):
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    self.chat_url,
                    json={
                        "model": self.model,
                        "messages": messages,
                        "max_tokens": max_tokens,
                        "temperature": temperature + (attempt * 0.1),
                        "top_p": 0.8,
                        "top_k": 20,
                        "presence_penalty": 1.5,
                        # 현재: 기본 JSON 모드만 사용
                        "response_format": {"type": "json_object"},
                    },
                )
```

#### 변경 후 코드

```python
from yeji_ai.config import get_settings

async def _call_llm_structured(
    self,
    system_prompt: str,
    user_prompt: str,
    response_schema: type[T],
    max_tokens: int = 800,
    temperature: float = 0.7,
    max_retries: int = 2,
    use_guided_json: bool | None = None,  # 새 파라미터
) -> T:
    """
    구조화된 LLM API 호출 (guided decoding 지원)

    vLLM 0.8+에서는 json_schema response_format을 사용하여
    스키마 준수를 보장합니다.

    Args:
        system_prompt: 시스템 프롬프트
        user_prompt: 사용자 프롬프트
        response_schema: 응답 Pydantic 스키마
        max_tokens: 최대 토큰 수
        temperature: 온도
        max_retries: 최대 재시도 횟수
        use_guided_json: guided decoding 사용 여부 (None=설정 따름)

    Returns:
        검증된 Pydantic 모델 인스턴스
    """
    settings = get_settings()

    # guided_json 사용 여부 결정
    if use_guided_json is None:
        use_guided_json = getattr(settings, "enable_guided_json", False)

    # JSON 형식 힌트를 user_prompt에 추가 (프롬프트 보강)
    json_hint = self._build_json_format_hint(response_schema)
    enhanced_prompt = f"{user_prompt}\n\n응답은 반드시 다음 JSON 형식으로만:\n{json_hint}"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": enhanced_prompt},
    ]

    last_error: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            # 요청 페이로드 구성
            payload = {
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature + (attempt * 0.1),
                "top_p": 0.8,
                "top_k": 20,
                "presence_penalty": 1.5,
            }

            # guided_json 활성화 시 json_schema response_format 사용
            if use_guided_json:
                payload["response_format"] = {
                    "type": "json_schema",
                    "json_schema": {
                        "name": response_schema.__name__.lower().replace("_", "-"),
                        "schema": response_schema.model_json_schema(),
                    },
                }
            else:
                # 폴백: 기본 json_object 모드
                payload["response_format"] = {"type": "json_object"}

            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(self.chat_url, json=payload)

                # guided_json 미지원 에러 처리
                if response.status_code == 400:
                    error_data = response.json()
                    if "json_schema" in str(error_data).lower() or "guided" in str(error_data).lower():
                        logger.warning(
                            "guided_json_not_supported",
                            attempt=attempt + 1,
                            error=str(error_data),
                        )
                        # 폴백: json_object 모드로 재시도
                        if use_guided_json:
                            return await self._call_llm_structured(
                                system_prompt=system_prompt,
                                user_prompt=user_prompt,
                                response_schema=response_schema,
                                max_tokens=max_tokens,
                                temperature=temperature,
                                max_retries=max_retries - attempt,
                                use_guided_json=False,  # 폴백
                            )

                response.raise_for_status()
                data = response.json()
                content = data["choices"][0]["message"]["content"]

                # <think> 태그 제거 (Qwen3)
                if "<think>" in content:
                    content = content.split("</think>")[-1].strip()

                # 이상 토큰/패턴 후처리
                content = _clean_llm_response(content)

                # Pydantic 검증
                result = response_schema.model_validate_json(content)

                logger.info(
                    "llm_structured_success",
                    schema=response_schema.__name__,
                    attempt=attempt + 1,
                    guided_json=use_guided_json,
                )
                return result

        except httpx.TimeoutException as e:
            logger.warning("llm_timeout", attempt=attempt + 1)
            last_error = e
        except Exception as e:
            logger.warning(
                "llm_structured_error",
                attempt=attempt + 1,
                error=str(e),
                guided_json=use_guided_json,
            )
            last_error = e

    # 모든 재시도 실패
    logger.error("llm_structured_failed", error=str(last_error))
    raise last_error or RuntimeError("LLM 호출 실패")
```

### 7.2 config.py 변경

```python
# config.py에 설정 추가
class Settings(BaseSettings):
    # ... 기존 설정 ...

    # Guided Decoding 설정
    enable_guided_json: bool = Field(
        default=False,  # 초기에는 비활성화, 검증 후 활성화
        description="vLLM guided_json/json_schema 사용 여부",
    )
    guided_json_backend: str = Field(
        default="auto",
        description="guided decoding 백엔드 (auto/xgrammar/outlines)",
    )
    guided_json_fallback: bool = Field(
        default=True,
        description="guided_json 실패 시 json_object로 폴백",
    )
```

### 7.3 vllm_client.py 활용 (선택적)

`vllm_client.py`에 이미 구현된 `GenerationConfig.guided_json`을 활용하려면:

```python
# llm_interpreter.py에서 VLLMClient 직접 사용
from yeji_ai.clients.vllm_client import VLLMClient, GenerationConfig

class LLMInterpreter:
    def __init__(self, ...):
        # ... 기존 초기화 ...
        self.vllm_client = VLLMClient(
            base_url=self.base_url.replace("/v1", ""),
            model=self.model,
        )

    async def _call_llm_with_vllm_client(
        self,
        messages: list[dict],
        response_schema: type[T],
        max_tokens: int = 800,
        temperature: float = 0.7,
    ) -> T:
        """VLLMClient를 사용한 guided_json 호출"""
        config = GenerationConfig(
            max_tokens=max_tokens,
            temperature=temperature,
            guided_json=response_schema.model_json_schema(),
        )

        response = await self.vllm_client.chat(messages, config)

        # 후처리 및 검증
        content = _clean_llm_response(response.text)
        return response_schema.model_validate_json(content)
```

---

## 8. 폴백 전략

### 8.1 폴백 시나리오

```
[요청 시작]
    ↓
[guided_json 활성화?]
    ↓ Yes
[json_schema response_format으로 호출]
    ↓ 성공 → [Pydantic 검증] → [응답]
    ↓ 실패 (400 Bad Request - schema 미지원)
[json_object response_format으로 폴백]
    ↓ 성공
[후처리 파이프라인 적용]
    ↓
[Pydantic 검증]
    ↓ 성공 → [응답]
    ↓ 실패
[기본값 응답 또는 에러]
```

### 8.2 폴백 구현 코드

```python
async def _call_llm_with_fallback(
    self,
    system_prompt: str,
    user_prompt: str,
    response_schema: type[T],
    max_tokens: int = 800,
    temperature: float = 0.7,
) -> T:
    """guided_json으로 호출하고 실패 시 폴백"""
    settings = get_settings()

    # 1차 시도: guided_json (설정에 따라)
    if settings.enable_guided_json:
        try:
            return await self._call_llm_structured(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_schema=response_schema,
                max_tokens=max_tokens,
                temperature=temperature,
                use_guided_json=True,
            )
        except GuidedJsonNotSupportedError:
            logger.warning(
                "guided_json_fallback_to_json_object",
                schema=response_schema.__name__,
            )
            # 폴백으로 진행

    # 2차 시도: 기본 json_object 모드
    result = await self._call_llm_structured(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        response_schema=response_schema,
        max_tokens=max_tokens,
        temperature=temperature,
        use_guided_json=False,
    )

    # 3차: 후처리 파이프라인 적용 (필요 시)
    if hasattr(result, "model_dump"):
        data = result.model_dump()
        # 후처리 로직 적용
        # from yeji_ai.services.postprocessor import EasternPostprocessor
        # processed = EasternPostprocessor().process(data)
        # return response_schema.model_validate(processed.data)

    return result
```

### 8.3 폴백 시 후처리 파이프라인 연계

guided_json 미지원 시, 기존 후처리 파이프라인을 강화하여 사용:

```python
from yeji_ai.services.postprocessor.eastern import EasternPostprocessor
from yeji_ai.services.postprocessor.western import WesternPostprocessor

async def _apply_postprocessing(
    self,
    raw_data: dict,
    schema_type: str,  # "eastern" or "western"
) -> dict:
    """후처리 파이프라인 적용"""
    if schema_type == "eastern":
        processor = EasternPostprocessor()
    else:
        processor = WesternPostprocessor()

    result = processor.process(raw_data)

    if result.errors:
        logger.warning(
            "postprocess_errors",
            errors=[e.message for e in result.errors],
            steps_applied=result.steps_applied,
        )

    return result.data
```

---

## 9. 테스트 계획

### 9.1 단위 테스트

```python
# tests/test_guided_decoding.py

import pytest
from yeji_ai.models.llm_schemas import EasternFullLLMOutput, WesternFullLLMOutput

class TestGuidedDecoding:
    """guided decoding 관련 단위 테스트"""

    def test_schema_json_generation(self):
        """Pydantic 스키마에서 JSON 스키마 생성 테스트"""
        schema = EasternFullLLMOutput.model_json_schema()

        # 필수 필드 확인
        assert "required" in schema
        assert "personality" in schema.get("required", [])
        assert "badges" in schema.get("required", [])

        # 타입 확인
        properties = schema.get("properties", {})
        assert properties["personality"]["type"] == "string"
        assert properties["badges"]["type"] == "array"

    def test_schema_complexity(self):
        """스키마 복잡도 검증 (XGrammar 호환성)"""
        schema = EasternFullLLMOutput.model_json_schema()

        # 중첩 깊이 측정
        def get_max_depth(obj, depth=0):
            if not isinstance(obj, dict):
                return depth
            max_child_depth = depth
            for v in obj.values():
                if isinstance(v, dict):
                    max_child_depth = max(max_child_depth, get_max_depth(v, depth + 1))
            return max_child_depth

        max_depth = get_max_depth(schema)
        # XGrammar는 깊이 5 이하 권장
        assert max_depth <= 6, f"스키마 중첩 깊이가 너무 깊음: {max_depth}"


@pytest.mark.asyncio
class TestLLMInterpreterGuidedJson:
    """LLMInterpreter guided_json 통합 테스트"""

    async def test_guided_json_call_success(self, mock_vllm_server):
        """guided_json 호출 성공 테스트"""
        interpreter = LLMInterpreter()

        result = await interpreter._call_llm_structured(
            system_prompt="테스트 시스템 프롬프트",
            user_prompt="테스트 사용자 프롬프트",
            response_schema=EasternFullLLMOutput,
            use_guided_json=True,
        )

        assert isinstance(result, EasternFullLLMOutput)
        assert result.personality is not None
        assert len(result.badges) >= 2

    async def test_guided_json_fallback(self, mock_vllm_server_no_guided):
        """guided_json 미지원 시 폴백 테스트"""
        interpreter = LLMInterpreter()

        # guided_json 미지원 서버에서도 동작해야 함
        result = await interpreter._call_llm_structured(
            system_prompt="테스트",
            user_prompt="테스트",
            response_schema=EasternFullLLMOutput,
            use_guided_json=True,  # 시도하지만 폴백됨
        )

        assert isinstance(result, EasternFullLLMOutput)
```

### 9.2 통합 테스트

```python
# tests/test_integration_guided_decoding.py

@pytest.mark.integration
@pytest.mark.asyncio
class TestGuidedDecodingIntegration:
    """실제 vLLM 서버 통합 테스트"""

    @pytest.fixture
    async def interpreter(self):
        """실제 vLLM 서버에 연결된 인터프리터"""
        return LLMInterpreter(
            base_url="http://13.125.68.166:8001/v1",
            model="tellang/yeji-8b-rslora-v7-AWQ",
        )

    async def test_eastern_fortune_guided(self, interpreter):
        """동양 사주 guided_json 테스트"""
        result = await interpreter.interpret_eastern_full(
            response=mock_eastern_response,
        )

        # 필수 필드 검증
        assert "personality" in result
        assert "badges" in result
        assert len(result["badges"]) >= 2

        # Enum 값 검증
        for badge in result["badges"]:
            assert badge.isupper(), f"배지가 대문자가 아님: {badge}"

    async def test_western_fortune_guided(self, interpreter):
        """서양 점성술 guided_json 테스트"""
        # ... 유사한 테스트 ...
```

### 9.3 성능 벤치마크

```python
# tests/benchmark_guided_decoding.py

import time
import statistics

async def benchmark_guided_vs_json_object():
    """guided_json vs json_object 성능 비교"""
    interpreter = LLMInterpreter()

    # 테스트 케이스 10회 반복
    guided_latencies = []
    json_object_latencies = []

    for _ in range(10):
        # guided_json
        start = time.perf_counter()
        await interpreter._call_llm_structured(
            ...,
            use_guided_json=True,
        )
        guided_latencies.append(time.perf_counter() - start)

        # json_object
        start = time.perf_counter()
        await interpreter._call_llm_structured(
            ...,
            use_guided_json=False,
        )
        json_object_latencies.append(time.perf_counter() - start)

    print(f"guided_json 평균: {statistics.mean(guided_latencies):.3f}s")
    print(f"json_object 평균: {statistics.mean(json_object_latencies):.3f}s")
    print(f"오버헤드: {(statistics.mean(guided_latencies) / statistics.mean(json_object_latencies) - 1) * 100:.1f}%")
```

---

## 10. 리스크 및 완화 방안

### 10.1 기술 리스크

| 리스크 | 확률 | 영향 | 완화 방안 |
|--------|------|------|----------|
| vLLM 서버가 guided_json 미지원 | 30% | 높음 | 서버 재설정 또는 후처리 강화로 대체 |
| XGrammar 스키마 컴파일 실패 | 20% | 중간 | 스키마 단순화, Outlines 폴백 |
| 추론 품질 저하 | 30% | 낮음-중간 | 2단계 접근법 병행 (Phase 2) |
| 레이턴시 SLA 초과 | 20% | 중간 | 캐싱, 타임아웃 조정 |

### 10.2 운영 리스크

| 리스크 | 확률 | 영향 | 완화 방안 |
|--------|------|------|----------|
| 배포 중 서비스 장애 | 10% | 높음 | Feature Flag, 점진적 롤아웃 |
| 롤백 필요 | 20% | 중간 | 즉시 롤백 가능 구조 |
| 기존 테스트 실패 | 15% | 중간 | 호환성 테스트 철저히 수행 |

### 10.3 완화 전략

#### Feature Flag 구현

```python
# config.py
class Settings(BaseSettings):
    enable_guided_json: bool = Field(
        default=False,
        description="guided_json 활성화 여부",
    )

# 환경변수로 제어
# ENABLE_GUIDED_JSON=true  # 활성화
# ENABLE_GUIDED_JSON=false # 비활성화 (폴백)
```

#### 점진적 롤아웃

```
Week 1:
├── Day 1-2: ai/develop 100% (개발 환경)
├── Day 3-4: ai/main 10% (Feature Flag)
├── Day 5-6: ai/main 50%
└── Day 7:   ai/main 100%

모니터링 지표:
- 503 에러율 < 1%
- 평균 레이턴시 < 3s
- Pydantic 검증 성공률 > 90%
```

#### 즉시 롤백 프로세스

```bash
# 롤백 명령 (Feature Flag만 변경)
export ENABLE_GUIDED_JSON=false

# 또는 Jenkins에서 이전 빌드 재배포
```

---

## 11. 참조 자료

### 11.1 공식 문서

| 자료 | URL |
|------|-----|
| vLLM Structured Outputs | https://docs.vllm.ai/en/latest/features/structured_outputs/ |
| vLLM OpenAI Compatible Server | https://docs.vllm.ai/en/latest/serving/openai_compatible_server.html |
| XGrammar | https://github.com/mlc-ai/xgrammar |
| Outlines | https://github.com/outlines-dev/outlines |

### 11.2 연구 자료

| 자료 | 설명 |
|------|------|
| Structured Decoding in vLLM (2025) | BentoML 블로그, 기술 소개 |
| Guided Decoding Performance (2025) | Squeezebits 벤치마크 |
| Red Hat: Structured outputs in vLLM (2025) | 구현 가이드 |

### 11.3 내부 문서

| 문서 | 경로 |
|------|------|
| JSON 정확도 개선 PRD | `ai/docs/prd/json-accuracy-improvement.md` |
| JSON 정확도 전략 분석 | `ai/docs/analysis/json-accuracy-strategy-analysis.md` |
| 구조화된 출력 진행사항 | `ai/docs/STRUCTURED_OUTPUT_PROGRESS.md` |
| LLM 응답 후처리 PRD | `ai/docs/prd/llm-response-postprocessor.md` |
| Qwen3 프롬프팅 가이드 | `ai/docs/guides/qwen3-prompting-guide.md` |

### 11.4 관련 코드

| 파일 | 설명 |
|------|------|
| `clients/vllm_client.py` | vLLM API 클라이언트 (guided_json 지원 구현됨) |
| `services/llm_interpreter.py` | LLM 호출 서비스 (수정 대상) |
| `models/llm_schemas.py` | Pydantic 스키마 정의 |
| `services/postprocessor/` | 후처리 파이프라인 |

---

## 변경 이력

| 버전 | 날짜 | 변경 내용 | 작성자 |
|------|------|----------|--------|
| 1.0.0 | 2026-01-31 | 초기 버전 | YEJI AI팀 |

---

## 부록

### A. 테스트 스크립트

```python
#!/usr/bin/env python3
"""vLLM guided_json 지원 여부 테스트 스크립트

사용법:
    python scripts/test_guided_json.py
"""

import asyncio
import httpx
import json

VLLM_URL = "http://13.125.68.166:8001/v1/chat/completions"
MODEL = "tellang/yeji-8b-rslora-v7-AWQ"

async def test_json_schema_support():
    """json_schema response_format 테스트"""
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
            "city": {"type": "string"}
        },
        "required": ["name", "age", "city"]
    }

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": "Generate a person with name, age, and city. 한국어로 작성해주세요."}
        ],
        "max_tokens": 200,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "person",
                "schema": schema
            }
        }
    }

    print("=" * 50)
    print("테스트: json_schema response_format")
    print("=" * 50)

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(VLLM_URL, json=payload)
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                print(f"✅ 지원됨!")
                print(f"응답: {content}")

                # JSON 파싱 테스트
                parsed = json.loads(content)
                print(f"파싱된 데이터: {parsed}")

                # 필수 필드 확인
                for field in ["name", "age", "city"]:
                    if field in parsed:
                        print(f"  ✓ {field}: {parsed[field]}")
                    else:
                        print(f"  ✗ {field}: 누락")

                return True
            else:
                print(f"❌ 오류: {response.status_code}")
                print(response.text)
                return False
        except Exception as e:
            print(f"❌ 예외: {e}")
            return False


async def test_extra_body_guided_json():
    """extra_body guided_json 테스트 (레거시)"""
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"}
        },
        "required": ["name", "age"]
    }

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": "Generate a person with name and age."}
        ],
        "max_tokens": 100,
        "extra_body": {
            "guided_json": schema
        }
    }

    print("\n" + "=" * 50)
    print("테스트: extra_body guided_json (레거시)")
    print("=" * 50)

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(VLLM_URL, json=payload)
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                print(f"✅ 지원됨!")
                print(f"응답: {content}")
                return True
            else:
                print(f"❌ 오류: {response.status_code}")
                print(response.text)
                return False
        except Exception as e:
            print(f"❌ 예외: {e}")
            return False


async def test_json_object_baseline():
    """기본 json_object 모드 테스트 (비교용)"""
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": "Generate a JSON with name, age, city fields. 한국어로 작성해주세요."}
        ],
        "max_tokens": 200,
        "response_format": {"type": "json_object"}
    }

    print("\n" + "=" * 50)
    print("테스트: json_object (기본 모드, 비교용)")
    print("=" * 50)

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(VLLM_URL, json=payload)
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                print(f"✅ 응답 수신")
                print(f"응답: {content}")
                return True
            else:
                print(f"❌ 오류: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 예외: {e}")
            return False


async def main():
    """메인 테스트 실행"""
    print("vLLM Guided Decoding 지원 여부 테스트")
    print(f"서버: {VLLM_URL}")
    print(f"모델: {MODEL}")
    print()

    results = {
        "json_schema": await test_json_schema_support(),
        "extra_body_guided_json": await test_extra_body_guided_json(),
        "json_object_baseline": await test_json_object_baseline(),
    }

    print("\n" + "=" * 50)
    print("테스트 결과 요약")
    print("=" * 50)
    for test_name, passed in results.items():
        status = "✅ 지원" if passed else "❌ 미지원"
        print(f"  {test_name}: {status}")

    # 권장사항
    print("\n권장사항:")
    if results["json_schema"]:
        print("  → json_schema response_format 사용 권장")
    elif results["extra_body_guided_json"]:
        print("  → extra_body guided_json 사용 권장 (레거시)")
    else:
        print("  → guided decoding 미지원. 서버 재설정 필요")
        print("  → 임시: response_format: json_object + 후처리 강화")


if __name__ == "__main__":
    asyncio.run(main())
```

### B. 스키마 복잡도 분석

```python
#!/usr/bin/env python3
"""Pydantic 스키마 복잡도 분석 스크립트

XGrammar 호환성을 위해 스키마 복잡도를 분석합니다.
"""

from yeji_ai.models.llm_schemas import (
    EasternFullLLMOutput,
    WesternFullLLMOutput,
    EasternFortuneResponse,
    WesternFortuneResponse,
)

def analyze_schema(schema_class):
    """스키마 복잡도 분석"""
    schema = schema_class.model_json_schema()

    def count_properties(obj, depth=0):
        """속성 수와 최대 깊이 계산"""
        if not isinstance(obj, dict):
            return 0, depth

        total = 0
        max_depth = depth

        if "properties" in obj:
            total += len(obj["properties"])
            for prop in obj["properties"].values():
                if isinstance(prop, dict):
                    sub_count, sub_depth = count_properties(prop, depth + 1)
                    total += sub_count
                    max_depth = max(max_depth, sub_depth)

        # $defs 처리
        if "$defs" in obj:
            for definition in obj["$defs"].values():
                sub_count, sub_depth = count_properties(definition, depth + 1)
                total += sub_count
                max_depth = max(max_depth, sub_depth)

        return total, max_depth

    total_props, max_depth = count_properties(schema)
    required_count = len(schema.get("required", []))

    return {
        "name": schema_class.__name__,
        "total_properties": total_props,
        "required_fields": required_count,
        "max_depth": max_depth,
        "definitions_count": len(schema.get("$defs", {})),
    }


def main():
    schemas = [
        EasternFullLLMOutput,
        WesternFullLLMOutput,
        EasternFortuneResponse,
        WesternFortuneResponse,
    ]

    print("스키마 복잡도 분석")
    print("=" * 60)
    print(f"{'스키마 이름':<30} {'속성 수':>8} {'필수':>6} {'깊이':>6} {'정의':>6}")
    print("-" * 60)

    for schema_class in schemas:
        result = analyze_schema(schema_class)
        print(
            f"{result['name']:<30} "
            f"{result['total_properties']:>8} "
            f"{result['required_fields']:>6} "
            f"{result['max_depth']:>6} "
            f"{result['definitions_count']:>6}"
        )

    print("-" * 60)
    print("XGrammar 권장: 깊이 ≤ 5, 속성 ≤ 100")


if __name__ == "__main__":
    main()
```

---

> **Note**: 이 문서는 vLLM Guided Decoding 적용을 위한 구현 계획서입니다. 실제 구현 전에 반드시 vLLM 서버의 지원 여부를 확인하고, 테스트 스크립트로 검증한 후 진행하세요.
