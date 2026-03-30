# JSON 정확도 개선 전략 검증 분석

> **문서 버전**: 1.0.0
> **작성일**: 2026-01-30
> **Task**: #64
> **담당팀**: SSAFY YEJI AI팀

---

## 목차

1. [현재 환경 분석](#1-현재-환경-분석)
2. [검증 대상 전략 개요](#2-검증-대상-전략-개요)
3. [전략별 상세 분석](#3-전략별-상세-분석)
4. [리스크 평가표](#4-리스크-평가표)
5. [권장 전략 순위](#5-권장-전략-순위)
6. [구현 로드맵](#6-구현-로드맵)
7. [결론](#7-결론)

---

## 1. 현재 환경 분석

### 1.1 인프라 현황

| 항목 | 값 | 비고 |
|------|-----|------|
| LLM 서버 | vLLM (AWS GPU 3.36.89.31:8001) | OpenAI-compatible API |
| 모델 | `tellang/yeji-8b-rslora-v7-AWQ` | 8B 파라미터, AWQ 양자화 |
| 최대 컨텍스트 | 4096 tokens | 긴 프롬프트 제한 |
| 현재 구조화 방식 | `response_format: {"type": "json_object"}` | vLLM 기본 JSON 모드 |

### 1.2 현재 JSON 정확도 현황

| 문제 유형 | 빈도 | 영향 |
|-----------|------|------|
| Pydantic 검증 실패 | ~30% | 503 에러 |
| 필수 필드 누락 | ~20% | UX 저하 |
| 코드 불일치 (대소문자) | ~15% | 검증 실패 |
| 구조 불일치 | ~10% | JSON 파싱 실패 |
| 언어 혼동 (영어/한국어) | ~5% | 프론트엔드 표시 문제 |

### 1.3 현재 코드베이스 구조

```
yeji-ai-server/ai/src/yeji_ai/
├── clients/vllm_client.py        # guided_json 옵션 지원 (미사용)
├── providers/vllm.py             # guided_json, guided_choice, guided_regex 지원
├── services/
│   ├── llm_interpreter.py        # response_format: json_object 사용
│   └── postprocessor/            # 후처리 파이프라인 (구현 완료)
│       ├── base.py               # PostprocessResult, Protocol 정의
│       ├── eastern.py            # 동양 사주 후처리기
│       ├── western.py            # 서양 점성술 후처리기
│       └── extractors.py         # 키워드 추출, JSON 추출 유틸
└── models/llm_schemas.py         # Pydantic v2 스키마 정의
```

---

## 2. 검증 대상 전략 개요

| 전략 | 핵심 기술 | 적용 레이어 | 구현 복잡도 |
|------|----------|------------|------------|
| 1. vLLM guided_json | XGrammar/Outlines | 추론 레이어 | 중간 |
| 2. Instructor 라이브러리 | Pydantic + 자동 재시도 | 서비스 레이어 | 낮음 |
| 3. 후처리 파이프라인 강화 | 규칙 기반 변환 | 서비스 레이어 | 낮음 |
| 4. 2단계 접근법 | 추론 → 구조화 분리 | 서비스 레이어 | 중간 |
| 5. 스키마 분할 + 병렬 호출 | 작은 스키마 병렬 처리 | 서비스 레이어 | 높음 |

---

## 3. 전략별 상세 분석

### 3.1 전략 1: vLLM guided_json (XGrammar/Outlines)

#### 개요

vLLM 0.8+ 버전에서 제공하는 **guided decoding** 기능을 활용하여 LLM 출력을 JSON 스키마에 맞게 제약합니다. 현재 코드베이스에서 `GenerationConfig.guided_json` 옵션이 이미 정의되어 있으나 **실제 사용되지 않고 있습니다**.

#### 2026년 최신 동향

- **XGrammar**: vLLM의 기본 guided decoding 백엔드로, 반복되는 스키마에서 캐싱을 통해 최적의 성능 제공
- **LLGuidance**: 동적/복잡한 스키마에서 더 나은 성능
- **Outlines**: 폴백 옵션으로 지원

```python
# 현재 코드 (vllm_client.py:26-28) - 이미 정의됨
guided_json: dict | None = None  # JSON 스키마로 출력 제약
guided_choice: list[str] | None = None  # 선택지 제약
guided_regex: str | None = None  # 정규식 제약
```

#### 적용 가능성 평가

| 평가 항목 | 점수 | 비고 |
|-----------|------|------|
| 현재 환경 호환성 | **높음** | vLLM API에 이미 구현됨 |
| 구현 난이도 | **낮음** | 코드 변경 최소화 |
| 예상 성공률 | **90-95%** | 문법적으로 유효한 JSON 보장 |
| 레이턴시 영향 | **낮음-중간** | 캐싱 시 ~5% 오버헤드 |
| 유지보수성 | **높음** | vLLM 업데이트 자동 반영 |

#### 예상 성공/실패 시나리오

**성공 시나리오**:
- JSON 문법 오류 100% 제거
- 필수 필드 존재 보장
- Enum 값 강제 가능

**실패 시나리오**:
- 복잡한 중첩 스키마에서 XGrammar 미지원 오류 발생 가능
- 스키마 컴파일 시간으로 인한 첫 요청 지연
- 모델의 "추론 능력" 10-15% 저하 가능 (포맷 제약에 집중)

#### 구현 방법

```python
# llm_interpreter.py 수정 예시
from yeji_ai.models.llm_schemas import EasternFullLLMOutput

config = GenerationConfig(
    max_tokens=1500,
    temperature=0.7,
    guided_json=EasternFullLLMOutput.model_json_schema(),
)
response = await vllm_client.chat(messages, config)
```

---

### 3.2 전략 2: Instructor 라이브러리 (자동 재시도)

#### 개요

[Instructor](https://github.com/567-labs/instructor)는 Pydantic 모델을 기반으로 LLM에서 구조화된 출력을 추출하는 라이브러리입니다. **자동 재시도, 검증 에러 피드백, 다양한 Provider 지원**이 핵심 기능입니다.

#### 2026년 최신 동향

- **버전 1.14.5** (2026-01-29 릴리즈)
- 15+ Provider 지원 (OpenAI, Anthropic, Ollama 등)
- `max_retries` 옵션으로 검증 실패 시 자동 재시도
- 재시도 시 에러 메시지를 프롬프트에 포함하여 자기 수정

#### 적용 가능성 평가

| 평가 항목 | 점수 | 비고 |
|-----------|------|------|
| 현재 환경 호환성 | **중간** | OpenAI-compatible API 지원, 커스텀 설정 필요 |
| 구현 난이도 | **낮음-중간** | 새 의존성 추가, API 패턴 변경 |
| 예상 성공률 | **85-95%** | 재시도로 성공률 향상 |
| 레이턴시 영향 | **중간-높음** | 재시도 시 2-3배 지연 |
| 유지보수성 | **중간** | 외부 라이브러리 의존성 |

#### 예상 성공/실패 시나리오

**성공 시나리오**:
- 첫 시도 실패 시 에러 피드백으로 자기 수정
- Pydantic v2 완전 호환
- 스트리밍 부분 객체 지원

**실패 시나리오**:
- vLLM 커스텀 설정과의 충돌 가능성
- 재시도로 인한 비용/레이턴시 증가
- 8B 모델의 자기 수정 능력 한계

#### 구현 방법

```python
import instructor
from openai import AsyncOpenAI

client = instructor.from_openai(AsyncOpenAI(
    base_url="http://3.36.89.31:8001/v1",
    api_key="dummy",
))

result = await client.chat.completions.create(
    model="tellang/yeji-8b-rslora-v7-AWQ",
    messages=[{"role": "user", "content": prompt}],
    response_model=EasternFullLLMOutput,
    max_retries=3,
)
```

---

### 3.3 전략 3: 후처리 파이프라인 강화

#### 개요

**현재 구현된** `postprocessor/` 모듈을 강화하여 LLM 출력의 구조적 오류를 수정합니다. 이미 `EasternPostprocessor`와 `WesternPostprocessor`가 구현되어 있습니다.

#### 현재 구현 상태

```python
# services/postprocessor/base.py
class PostprocessResult:
    data: dict[str, Any]
    original: dict[str, Any]
    steps_applied: list[str]
    errors: list[PostprocessError]
    latency_ms: float

# 후처리 단계
1. convert_structures  # 객체 → 배열 변환
2. normalize_codes     # 대소문자, 유사어 매핑
3. normalize_pillars   # 사주 기둥 정규화
4. sync_cheongan_jiji  # 천간지지 동기화
5. fill_defaults       # 기본값 채우기
```

#### 적용 가능성 평가

| 평가 항목 | 점수 | 비고 |
|-----------|------|------|
| 현재 환경 호환성 | **매우 높음** | 이미 구현 완료 |
| 구현 난이도 | **매우 낮음** | 기존 코드 확장만 필요 |
| 예상 성공률 | **70-85%** | 규칙 기반 한계 |
| 레이턴시 영향 | **매우 낮음** | < 50ms |
| 유지보수성 | **높음** | 팀 내 완전 제어 |

#### 강화 방안

1. **키워드 추출 개선**: `extractors.py`의 `KEYWORD_MAPPING` 확장
2. **JSON 복구 로직 강화**: 불완전한 JSON 자동 복구
3. **Enum 값 퍼지 매칭**: 유사 문자열 자동 변환
4. **누락 필드 추론**: 컨텍스트 기반 기본값 생성

#### 예상 성공/실패 시나리오

**성공 시나리오**:
- 레이턴시 최소화 (< 50ms)
- LLM 호출 추가 없음
- 기존 시스템과 완벽 호환

**실패 시나리오**:
- 의미적 오류 수정 불가 (예: 잘못된 오행 분석)
- 복잡한 구조 변환 한계
- 규칙 유지보수 부담 증가

---

### 3.4 전략 4: 2단계 접근법 (추론 → 구조화)

#### 개요

**최신 연구 결과**에 따르면, LLM에게 JSON 포맷을 강제하면 추론 능력이 10-15% 저하됩니다. 이를 해결하기 위해:

1. **1단계**: 자유 형식으로 분석/추론 수행
2. **2단계**: 추론 결과를 구조화된 JSON으로 변환

#### 2026년 최신 연구

> "When we tested this for our customer analysis pipeline, the results matched what the research predicted. Total accuracy on aggregation tasks went from 48% to 61%."
> — [Beyond JSON: Picking the Right Format for LLM Pipelines](https://linkedin.com/pulse/beyond-json)

#### 적용 가능성 평가

| 평가 항목 | 점수 | 비고 |
|-----------|------|------|
| 현재 환경 호환성 | **높음** | 기존 API 패턴 확장 |
| 구현 난이도 | **중간** | 2단계 호출 로직 구현 |
| 예상 성공률 | **90-95%** | 추론 품질 + 구조 정확도 |
| 레이턴시 영향 | **높음** | LLM 호출 2배 |
| 유지보수성 | **중간** | 프롬프트 2세트 관리 |

#### 구현 방법

```python
# 1단계: 자유 형식 분석
reasoning_prompt = """
다음 사주 정보를 분석해주세요. 형식에 구애받지 말고 자유롭게 분석하세요.

[사주 정보]
...
"""
reasoning_result = await vllm_client.chat([
    {"role": "user", "content": reasoning_prompt}
], GenerationConfig(temperature=0.7))

# 2단계: 구조화 (guided_json 사용)
structure_prompt = f"""
다음 분석 결과를 JSON 형식으로 변환해주세요.

[분석 결과]
{reasoning_result.text}
"""
structured_result = await vllm_client.chat([
    {"role": "user", "content": structure_prompt}
], GenerationConfig(
    temperature=0.3,  # 낮은 온도로 정확도 향상
    guided_json=EasternFullLLMOutput.model_json_schema()
))
```

#### 예상 성공/실패 시나리오

**성공 시나리오**:
- 복잡한 분석 작업에서 정확도 향상
- 추론 품질과 구조 정확도 모두 달성
- 1단계 결과를 캐싱하여 재사용 가능

**실패 시나리오**:
- 레이턴시 2배 증가 (240ms → 480ms+)
- 토큰 비용 증가 (~112%)
- 2단계에서 1단계 정보 손실 가능

---

### 3.5 전략 5: 스키마 분할 + 병렬 호출

#### 개요

복잡한 스키마(`EasternFortuneResponse`)를 작은 단위로 분할하여 병렬로 생성한 후 병합합니다.

```
EasternFortuneResponse
├── chart (사주 차트)      → 호출 1
├── stats (통계)          → 호출 2
├── ui_hints (UI 힌트)    → 호출 3
└── lucky (행운 정보)     → 호출 4
```

#### 적용 가능성 평가

| 평가 항목 | 점수 | 비고 |
|-----------|------|------|
| 현재 환경 호환성 | **중간** | API 구조 변경 필요 |
| 구현 난이도 | **높음** | 병렬 처리, 병합 로직 |
| 예상 성공률 | **85-90%** | 개별 스키마 단순화 |
| 레이턴시 영향 | **중간** | 병렬 처리로 상쇄 |
| 유지보수성 | **낮음** | 복잡한 조율 로직 |

#### 예상 성공/실패 시나리오

**성공 시나리오**:
- 각 호출의 스키마 복잡도 감소
- 병렬 처리로 전체 레이턴시 유지
- 부분 실패 시 해당 섹션만 재시도

**실패 시나리오**:
- 섹션 간 일관성 문제 (예: chart의 오행과 stats의 오행 불일치)
- 병합 로직 복잡성
- 오류 추적 어려움

---

## 4. 리스크 평가표

### 4.1 전략별 리스크 매트릭스

| 전략 | 구현 리스크 | 운영 리스크 | 성능 리스크 | 비용 리스크 | 종합 리스크 |
|------|-----------|-----------|-----------|-----------|-----------|
| 1. vLLM guided_json | 낮음 | 낮음 | 중간 | 낮음 | **낮음** |
| 2. Instructor | 중간 | 중간 | 중간 | 중간 | **중간** |
| 3. 후처리 강화 | 매우 낮음 | 낮음 | 낮음 | 매우 낮음 | **매우 낮음** |
| 4. 2단계 접근법 | 중간 | 중간 | 높음 | 높음 | **중간-높음** |
| 5. 스키마 분할 | 높음 | 높음 | 중간 | 중간 | **높음** |

### 4.2 상세 리스크 분석

#### 전략 1 (vLLM guided_json) 리스크

| 리스크 | 확률 | 영향 | 완화 방안 |
|--------|------|------|----------|
| XGrammar 스키마 미지원 | 20% | 중간 | Outlines 폴백 설정 |
| 추론 능력 저하 | 50% | 낮음-중간 | 2단계 접근법 병행 |
| vLLM 버전 호환성 | 10% | 높음 | 버전 고정 및 테스트 |

#### 전략 2 (Instructor) 리스크

| 리스크 | 확률 | 영향 | 완화 방안 |
|--------|------|------|----------|
| vLLM 설정 충돌 | 30% | 높음 | 커스텀 Provider 구현 |
| 재시도 비용 증가 | 60% | 중간 | max_retries 제한 |
| 8B 모델 자기수정 한계 | 40% | 중간 | 에러 피드백 프롬프트 최적화 |

#### 전략 3 (후처리 강화) 리스크

| 리스크 | 확률 | 영향 | 완화 방안 |
|--------|------|------|----------|
| 규칙 커버리지 부족 | 30% | 낮음 | 지속적 규칙 추가 |
| 의미적 오류 미수정 | 50% | 낮음 | 다른 전략과 병행 |
| 유지보수 부담 | 20% | 낮음 | 테스트 커버리지 확보 |

#### 전략 4 (2단계 접근법) 리스크

| 리스크 | 확률 | 영향 | 완화 방안 |
|--------|------|------|----------|
| 레이턴시 초과 | 70% | 높음 | 병렬 처리, 캐싱 |
| 토큰 비용 증가 | 90% | 중간 | 중요 요청만 적용 |
| 정보 손실 | 20% | 중간 | 프롬프트 최적화 |

#### 전략 5 (스키마 분할) 리스크

| 리스크 | 확률 | 영향 | 완화 방안 |
|--------|------|------|----------|
| 섹션 간 불일치 | 40% | 높음 | 공유 컨텍스트 전달 |
| 병합 로직 버그 | 30% | 중간 | 철저한 테스트 |
| 복잡성 증가 | 80% | 중간 | 단계적 도입 |

---

## 5. 권장 전략 순위

### 5.1 종합 평가 결과

| 순위 | 전략 | 종합 점수 | 권장 이유 |
|------|------|----------|----------|
| **1위** | **후처리 파이프라인 강화** | 9.0/10 | 이미 구현됨, 리스크 최소, 즉시 적용 가능 |
| **2위** | **vLLM guided_json** | 8.5/10 | 인프라 레벨 해결, 높은 성공률 |
| **3위** | **2단계 접근법** | 7.5/10 | 복잡한 분석에 적합, 비용 트레이드오프 |
| **4위** | **Instructor 라이브러리** | 7.0/10 | 빠른 프로토타이핑, 외부 의존성 |
| **5위** | **스키마 분할 + 병렬** | 5.5/10 | 복잡성 대비 이점 부족 |

### 5.2 권장 조합 전략

**최적 조합: 전략 1 + 전략 3 (Hybrid Approach)**

```
[LLM 호출]
    ↓ guided_json (vLLM)
[구조적으로 유효한 JSON]
    ↓ 후처리 파이프라인
[정규화된 최종 JSON]
    ↓ Pydantic 검증
[API 응답]
```

**장점**:
- **guided_json**: 문법적으로 유효한 JSON 보장 (90-95%)
- **후처리**: 의미적 정규화 및 엣지 케이스 처리 (추가 5-10%)
- **결합 성공률**: **95-99%**

### 5.3 상황별 권장 전략

| 상황 | 권장 전략 | 이유 |
|------|----------|------|
| **빠른 개선 필요** | 전략 3 (후처리 강화) | 이미 구현됨, 규칙만 추가 |
| **안정적 운영 목표** | 전략 1 + 3 (하이브리드) | 다중 방어선 |
| **복잡한 분석 품질** | 전략 4 (2단계) | 추론 품질 우선 |
| **프로토타이핑** | 전략 2 (Instructor) | 빠른 실험 |

---

## 6. 구현 로드맵

### 6.1 Phase 1: 즉시 적용 (1-2일)

**전략 3: 후처리 파이프라인 강화**

1. `extractors.py`의 `KEYWORD_MAPPING` 확장
2. 누락된 코드 정규화 규칙 추가
3. JSON 복구 로직 개선

```python
# extractors.py에 추가할 키워드 매핑 예시
KEYWORD_MAPPING_EXTENDED = {
    **KEYWORD_MAPPING,
    # 추가 키워드
    "결단력": "CONFIDENCE",
    "유연성": "ADAPTABILITY",
    "협동심": "COMMUNICATION",
    # ...
}
```

### 6.2 Phase 2: 인프라 레벨 개선 (3-5일)

**전략 1: vLLM guided_json 활성화**

1. `llm_interpreter.py`에서 `guided_json` 옵션 활성화
2. 스키마 호환성 테스트
3. XGrammar vs Outlines 벤치마크

```python
# llm_interpreter.py 수정
async def _call_llm_structured(
    self,
    system_prompt: str,
    user_prompt: str,
    response_schema: type[T],
    ...
) -> T:
    # guided_json 활성화
    payload = {
        "model": self.model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        # 기존 response_format 대신 guided_json 사용
        "extra_body": {
            "guided_json": response_schema.model_json_schema()
        }
    }
```

### 6.3 Phase 3: 고급 최적화 (선택, 1주+)

**전략 4: 2단계 접근법 (복잡한 분석용)**

1. 분석 품질이 중요한 엔드포인트에만 적용
2. 1단계 결과 캐싱 구현
3. A/B 테스트로 효과 검증

---

## 7. 결론

### 7.1 핵심 권장사항

1. **즉시 적용**: 기존 후처리 파이프라인 강화 (전략 3)
2. **단기 목표**: vLLM guided_json 활성화 (전략 1)
3. **장기 목표**: 하이브리드 접근법 (전략 1 + 3)

### 7.2 예상 성과

| 지표 | 현재 | 전략 3 적용 후 | 전략 1+3 적용 후 |
|------|------|---------------|----------------|
| Pydantic 검증 실패율 | 30% | 15% | **5% 이하** |
| 503 에러 발생률 | 3% | 1.5% | **0.5% 이하** |
| 빈 keywords 응답률 | 100% | 20% | **10% 이하** |

### 7.3 주의사항

1. **vLLM guided_json 적용 시**: XGrammar 스키마 호환성 사전 테스트 필수
2. **2단계 접근법 적용 시**: 레이턴시 SLA 재검토 필요
3. **Instructor 도입 시**: vLLM 커스텀 설정과의 충돌 테스트 필요

### 7.4 모니터링 지표

```python
# 추가 모니터링 메트릭
METRICS = {
    "guided_json_success_rate": "guided_json으로 생성된 응답 비율",
    "postprocess_correction_count": "후처리에서 수정된 필드 수",
    "schema_validation_errors": "스키마별 검증 실패 유형",
    "retry_count": "재시도 발생 횟수 (Instructor 사용 시)",
}
```

---

## 참고 자료

### 논문 및 블로그

1. [Structured Decoding in vLLM: a gentle introduction](https://blog.vllm.ai/2025/01/14/struct-decode-intro.html)
2. [Beyond JSON: Picking the Right Format for LLM Pipelines](https://linkedin.com/pulse/beyond-json)
3. [Guided Decoding Performance on vLLM and SGLang](https://blog.squeezebits.com/guided-decoding-performance-vllm-sglang)

### 관련 라이브러리

- [vLLM Structured Outputs](https://docs.vllm.ai/en/latest/features/structured_outputs/)
- [Instructor](https://python.useinstructor.com/)
- [XGrammar](https://github.com/mlc-ai/xgrammar)
- [Outlines](https://github.com/outlines-dev/outlines)

### 내부 문서

- `docs/STRUCTURED_OUTPUT_PROGRESS.md`
- `docs/prd/llm-response-postprocessor.md`
- `docs/guides/qwen3-prompting-guide.md`

---

## 변경 이력

| 버전 | 날짜 | 변경 내용 | 작성자 |
|------|------|----------|--------|
| 1.0.0 | 2026-01-30 | 초기 버전 | YEJI AI팀 |

---

> **Note**: 이 분석은 2026년 1월 기준 최신 정보를 반영합니다. vLLM, Instructor 등의 라이브러리는 빠르게 발전하고 있으므로 구현 전 최신 문서를 확인하세요.
