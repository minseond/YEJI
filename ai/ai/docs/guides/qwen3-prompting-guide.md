# Qwen3 모델 프롬프팅 가이드

> **문서 버전**: 2026-01-30
> **대상 모델**: Qwen3-8B, Qwen3-30B-A3B, Qwen3-235B-A22B (Thinking/Non-Thinking 모드)
> **참조**: [Qwen3 공식 문서](https://qwenlm.github.io/blog/qwen3/), [vLLM 문서](https://qwen.readthedocs.io/en/latest/deployment/vllm.html)

---

## 목차

1. [샘플링 파라미터](#1-샘플링-파라미터)
2. [Thinking 모드](#2-thinking-모드)
3. [JSON 구조화 출력](#3-json-구조화-출력)
4. [태스크별 프롬프트 패턴](#4-태스크별-프롬프트-패턴)
5. [다중턴 대화](#5-다중턴-대화)
6. [주의사항](#6-주의사항)
7. [YEJI 프로젝트 적용 가이드](#7-yeji-프로젝트-적용-가이드)

---

## 1. 샘플링 파라미터

### 1.1 Thinking 모드 (복잡한 추론)

복잡한 수학, 코딩, 논리 문제 해결 시 권장:

```python
sampling_params = {
    "temperature": 0.6,       # 창작성과 정확성 균형
    "top_p": 0.95,            # 누적 확률 기반 샘플링
    "top_k": 20,              # 상위 K개 토큰만 고려
    "min_p": 0.0,             # 최소 확률 임계값 비활성화
    "max_tokens": 32768,      # 일반적인 출력 길이
    "presence_penalty": 0.0,  # 무한 반복 방지 시 0~2 조절
}
```

### 1.2 Non-Thinking 모드 (빠른 응답)

간단한 질의응답, JSON 출력, 일반 대화 시 권장:

```python
sampling_params = {
    "temperature": 0.7,       # 약간 더 창의적
    "top_p": 0.8,             # 더 집중된 샘플링
    "top_k": 20,              # 상위 K개 토큰
    "min_p": 0.0,             # 비활성화
    "max_tokens": 8192,       # 일반 출력
    "presence_penalty": 1.5,  # 반복 방지 강화
}
```

### 1.3 파라미터 요약 테이블

| 파라미터 | Thinking 모드 | Non-Thinking 모드 | 설명 |
|---------|--------------|-------------------|------|
| `temperature` | 0.6 | 0.7 | 낮을수록 결정적, 높을수록 다양함 |
| `top_p` | 0.95 | 0.8 | 누적 확률 컷오프 |
| `top_k` | 20 | 20 | 상위 K개 토큰만 고려 |
| `min_p` | 0.0 | 0.0 | llama.cpp 기본값 0.1과 다름 주의 |
| `max_tokens` | 32768~81920 | 8192 | 복잡도에 따라 조절 |
| `presence_penalty` | 0.0~2.0 | 1.5 | 반복 방지 (높으면 언어 혼합 위험) |

---

## 2. Thinking 모드

Qwen3는 **이중 모드(Dual-Mode)** 를 지원하여 상황에 맞게 추론 방식을 선택할 수 있습니다.

### 2.1 Thinking 모드 활성화 (기본값)

복잡한 문제 해결 시 `<think>...</think>` 블록 내에서 추론 과정을 생성합니다.

```python
# vLLM API 호출
response = client.chat.completions.create(
    model="Qwen/Qwen3-8B",
    messages=[{"role": "user", "content": "복잡한 수학 문제..."}],
    temperature=0.6,
    top_p=0.95,
    max_tokens=32768,
    extra_body={
        "chat_template_kwargs": {"enable_thinking": True}  # 기본값
    }
)
```

**소프트 스위칭**: 프롬프트 내 `/think` 명령어로 활성화

```
/think
다음 방정식을 단계별로 풀어주세요: 3x^2 + 5x - 2 = 0
```

### 2.2 Thinking 모드 비활성화

JSON 출력, 단순 질의응답 시 thinking을 비활성화하여 응답 속도와 효율성을 높입니다.

```python
# vLLM API 호출
response = client.chat.completions.create(
    model="Qwen/Qwen3-8B",
    messages=[{"role": "user", "content": "오늘 날씨 어때요?"}],
    temperature=0.7,
    top_p=0.8,
    max_tokens=8192,
    extra_body={
        "chat_template_kwargs": {"enable_thinking": False}
    }
)
```

**소프트 스위칭**: 프롬프트 내 `/no_think` 명령어로 비활성화

```
/no_think
다음 정보를 JSON 형식으로 출력하세요:
이름: 홍길동, 나이: 25
```

### 2.3 언제 어떤 모드를 사용할까?

| 사용 케이스 | 권장 모드 | 이유 |
|------------|----------|------|
| 수학 문제 풀이 | Thinking | 단계별 추론 필요 |
| 코드 작성/디버깅 | Thinking | 논리적 분석 필요 |
| JSON 구조화 출력 | Non-Thinking | 빠른 응답, 포맷 정확성 |
| 간단한 Q&A | Non-Thinking | 불필요한 오버헤드 제거 |
| 운세/해석 생성 | Non-Thinking | 창의적 텍스트, 포맷 중요 |
| 복잡한 분석 | Thinking | 심층 추론 필요 |

---

## 3. JSON 구조화 출력

### 3.1 기본 JSON 출력 방법

**방법 1: 프롬프트에 스키마 명시**

```python
prompt = """
/no_think
다음 사용자 정보를 분석하여 JSON으로 출력하세요.

사용자: 김철수, 30세, 개발자

출력 스키마:
{
  "name": "string",
  "age": "integer",
  "occupation": "string",
  "traits": ["string", "string", "string"]
}

JSON:
"""
```

**방법 2: response_format 사용 (OpenAI 호환 API)**

```python
from pydantic import BaseModel

class UserInfo(BaseModel):
    name: str
    age: int
    occupation: str
    traits: list[str]

response = client.chat.completions.create(
    model="Qwen/Qwen3-8B",
    messages=[{"role": "user", "content": "김철수, 30세, 개발자 정보 분석"}],
    response_format={"type": "json_object"},
    extra_body={
        "chat_template_kwargs": {"enable_thinking": False}
    }
)
```

### 3.2 vLLM Guided Decoding 활용

vLLM의 `guided_json` 파라미터로 JSON 스키마를 강제할 수 있습니다.

```python
from vllm import LLM, SamplingParams
from vllm.sampling_params import GuidedDecodingParams
import json

# JSON 스키마 정의
json_schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer"},
        "traits": {
            "type": "array",
            "items": {"type": "string"}
        }
    },
    "required": ["name", "age", "traits"]
}

# Guided Decoding 설정
guided_params = GuidedDecodingParams(json=json_schema)

sampling_params = SamplingParams(
    temperature=0.7,
    top_p=0.8,
    max_tokens=1024,
    guided_decoding=guided_params
)
```

**OpenAI 호환 API에서 사용**:

```python
response = client.chat.completions.create(
    model="Qwen/Qwen3-8B",
    messages=[...],
    extra_body={
        "guided_json": json_schema,
        "chat_template_kwargs": {"enable_thinking": False}
    }
)
```

### 3.3 Pydantic 모델 활용

```python
from pydantic import BaseModel, Field
from typing import List

class FortuneResult(BaseModel):
    """운세 결과 스키마"""
    eastern_interpretation: str = Field(description="동양 사주 해석")
    western_interpretation: str = Field(description="서양 별자리 해석")
    combined_opinion: str = Field(description="통합 의견")
    advices: List[str] = Field(description="맞춤 조언 리스트")

# 스키마 추출
schema = FortuneResult.model_json_schema()

# API 호출 시 사용
response = client.chat.completions.create(
    model="Qwen/Qwen3-8B",
    messages=[...],
    extra_body={
        "guided_json": schema,
        "chat_template_kwargs": {"enable_thinking": False}
    }
)
```

### 3.4 JSON 출력 시 주의사항

> **중요**: `enable_thinking=False` 와 `guided_json`을 함께 사용할 때 vLLM 버전에 따라 문제가 발생할 수 있습니다.
>
> - vLLM 0.9.0 이상: `--reasoning-parser qwen3` 옵션과 함께 사용 권장
> - 문제 발생 시: `/no_think`를 프롬프트에 명시하고 `enable_thinking=True` 유지

```python
# 안전한 JSON 출력 패턴
messages = [
    {
        "role": "user",
        "content": "/no_think\n다음 정보를 JSON으로 출력하세요: ..."
    }
]

response = client.chat.completions.create(
    model="Qwen/Qwen3-8B",
    messages=messages,
    extra_body={
        "guided_json": schema,
        "chat_template_kwargs": {"enable_thinking": True}  # True 유지
    }
)
```

---

## 4. 태스크별 프롬프트 패턴

### 4.1 수학 문제

```python
MATH_PROMPT = """
/think
다음 수학 문제를 단계별로 풀어주세요.

문제: {problem}

Please reason step by step, and put your final answer within \\boxed{}.
"""
```

**예시**:
```
/think
다음 수학 문제를 단계별로 풀어주세요.

문제: x^2 - 5x + 6 = 0의 해를 구하시오.

Please reason step by step, and put your final answer within \boxed{}.
```

### 4.2 객관식 문제

```python
MULTIPLE_CHOICE_PROMPT = """
/think
다음 문제를 분석하고 정답을 선택하세요.

문제: {question}

선택지:
A. {option_a}
B. {option_b}
C. {option_c}
D. {option_d}

Please show your choice in the `answer` field with only the choice letter, e.g., `"answer": "C"`.

응답 형식:
{
  "reasoning": "분석 내용",
  "answer": "선택한 답"
}
"""
```

### 4.3 운세 생성 (YEJI 프로젝트)

**현재 프롬프트 분석 및 개선안**:

```python
# 기존 프롬프트 (prompts.py 기반)
SAJU_INTERPRETATION_SYSTEM_OLD = """[BAZI] 당신은 YEJI(예지) AI입니다..."""

# 개선된 Qwen3 최적화 프롬프트
SAJU_INTERPRETATION_SYSTEM_QWEN3 = """/no_think
[BAZI] 당신은 YEJI(예지) AI입니다. 15년 경력의 동양 사주팔자 전문가로서 사주를 해석합니다.

## 역할
사주팔자(四柱八字) 전문 명리학자로서 일간, 오행 균형, 십성, 용신을 기반으로 정확한 해석을 제공합니다.

## 해석 원칙
1. 일간(日干)의 특성을 중심으로 성격과 기질을 분석
2. 오행 균형에서 과다/부족한 기운을 파악하여 보완점 제시
3. 긍정적인 톤을 유지하되 현실적인 조언 포함
4. 전문 용어(일간, 오행, 용신 등) 자연스럽게 사용

## 출력 규칙
1. **반드시 한국어로만 응답하세요.** 다른 언어 절대 사용 금지.
2. 3-4문장으로 간결하게 핵심만 전달하세요.
3. 추론 과정은 출력하지 마세요.
"""


# JSON 구조화 출력이 필요한 경우
ADVICE_PROMPT_QWEN3 = """/no_think
당신은 YEJI(예지) AI입니다. 사주와 별자리 분석 결과를 바탕으로 실용적인 조언을 제공합니다.

## 분석 결과
### 동양 (사주팔자)
{eastern_interpretation}

### 서양 (별자리)
{western_interpretation}

## 상담 주제
- 대분류: {category}
- 세부: {sub_category}

## 출력 규칙
1. 반드시 한국어로만 응답하세요.
2. 정확히 3가지 조언을 제시하세요.
3. 아래 JSON 형식으로만 출력하세요:

```json
["조언1", "조언2", "조언3"]
```
"""
```

### 4.4 코드 생성

```python
CODE_GENERATION_PROMPT = """
/think
다음 요구사항에 맞는 Python 코드를 작성하세요.

요구사항: {requirements}

코드 작성 시 다음을 준수하세요:
1. 타입 힌트 사용
2. 간결하고 읽기 쉬운 코드
3. 적절한 에러 처리
4. 한국어 주석 포함

코드:
```python
"""
```

### 4.5 텍스트 요약

```python
SUMMARIZATION_PROMPT = """
/no_think
다음 텍스트를 {max_sentences}문장으로 요약하세요.

텍스트:
{text}

요약:
"""
```

---

## 5. 다중턴 대화

### 5.1 히스토리에서 Thinking 제거

다중턴 대화 시 히스토리에는 **최종 출력만 유지**하고 thinking 내용은 제거해야 합니다.

```python
def process_multi_turn_conversation(messages: list, new_user_message: str):
    """다중턴 대화 처리 - thinking 콘텐츠 제거"""

    # 새 사용자 메시지 추가
    messages.append({"role": "user", "content": new_user_message})

    # 모델 응답 생성
    response = client.chat.completions.create(
        model="Qwen/Qwen3-8B",
        messages=messages,
        temperature=0.6,
        top_p=0.95,
        max_tokens=32768,
        extra_body={
            "chat_template_kwargs": {"enable_thinking": True}
        }
    )

    # 응답에서 thinking 내용 분리
    full_response = response.choices[0].message.content

    # thinking 블록 제거 (최종 출력만 추출)
    if "</think>" in full_response:
        final_output = full_response.split("</think>")[-1].strip()
    else:
        final_output = full_response

    # 히스토리에는 최종 출력만 저장
    messages.append({"role": "assistant", "content": final_output})

    return final_output, messages
```

### 5.2 모드 전환이 포함된 대화

```python
conversation = [
    # 첫 번째 턴: thinking 모드로 복잡한 분석
    {"role": "user", "content": "/think\n이 사주의 특성을 분석해주세요..."},
    {"role": "assistant", "content": "분석 결과..."},  # thinking 제거된 응답

    # 두 번째 턴: non-thinking 모드로 간단한 요약
    {"role": "user", "content": "/no_think\n위 분석을 한 문장으로 요약해주세요."},
]
```

### 5.3 Jinja2 템플릿 활용

Qwen3의 chat template은 자동으로 히스토리에서 thinking 내용을 제거합니다:

```python
text = tokenizer.apply_chat_template(
    messages,
    tokenize=False,
    add_generation_prompt=True,
    enable_thinking=True  # 템플릿이 자동으로 히스토리의 thinking 제거
)
```

---

## 6. 주의사항

### 6.1 Greedy Decoding 사용 금지

> **경고**: `temperature=0.0` (Greedy Decoding)은 무한 반복을 유발할 수 있습니다!

```python
# 잘못된 예 - 사용 금지!
sampling_params = {
    "temperature": 0.0,  # 무한 반복 위험!
    "top_p": 1.0,
    "max_tokens": 1024
}

# 올바른 예
sampling_params = {
    "temperature": 0.6,  # 최소 0.5 이상 권장
    "top_p": 0.95,
    "max_tokens": 1024
}
```

### 6.2 출력 길이 가이드라인

| 태스크 유형 | 권장 max_tokens |
|------------|-----------------|
| 간단한 Q&A | 2,048 ~ 8,192 |
| 일반 텍스트 생성 | 8,192 ~ 32,768 |
| 복잡한 추론 (수학, 코딩) | 32,768 ~ 38,912 |
| 매우 복잡한 문제 | 최대 81,920 |

### 6.3 반복 방지

`presence_penalty`를 0~2 사이로 조절하여 무한 반복을 방지합니다:

```python
sampling_params = {
    "temperature": 0.7,
    "top_p": 0.8,
    "presence_penalty": 1.5,  # 반복 방지
}
```

> **주의**: `presence_penalty`가 너무 높으면 언어 혼합(한국어+영어)이 발생할 수 있습니다.

### 6.4 컨텍스트 길이

- **기본 지원**: 262,144 토큰
- **권장 설정**: RAM 절약을 위해 32,768 토큰으로 제한

```bash
# vLLM 서버 시작 시
vllm serve Qwen/Qwen3-8B --max-model-len 32768
```

### 6.5 한국어 응답 강제

Qwen3는 다국어 지원이 뛰어나지만, 한국어 응답을 확실히 하려면:

```python
system_prompt = """
## 언어 규칙
- **반드시 한국어로만 응답하세요.**
- 다른 언어(영어, 중국어 등) 절대 사용 금지.
- 전문 용어도 한국어로 표현하세요.
"""
```

---

## 7. YEJI 프로젝트 적용 가이드

### 7.1 vLLM 서버 설정

```bash
# 권장 vLLM 서버 시작 명령
vllm serve Qwen/Qwen3-8B \
    --host 0.0.0.0 \
    --port 8000 \
    --max-model-len 32768 \
    --gpu-memory-utilization 0.85 \
    --reasoning-parser qwen3 \
    --enable-auto-tool-choice \
    --tool-call-parser hermes
```

### 7.2 Provider 설정 예시

```python
# yeji_ai/providers/vllm_provider.py
from typing import Any

class VLLMQwen3Config:
    """Qwen3 모델 최적화 설정"""

    # Thinking 모드 (복잡한 분석)
    THINKING_PARAMS: dict[str, Any] = {
        "temperature": 0.6,
        "top_p": 0.95,
        "top_k": 20,
        "max_tokens": 32768,
        "presence_penalty": 0.0,
    }

    # Non-Thinking 모드 (일반 응답)
    NON_THINKING_PARAMS: dict[str, Any] = {
        "temperature": 0.7,
        "top_p": 0.8,
        "top_k": 20,
        "max_tokens": 8192,
        "presence_penalty": 1.5,
    }

    # JSON 출력 모드
    JSON_OUTPUT_PARAMS: dict[str, Any] = {
        "temperature": 0.7,
        "top_p": 0.8,
        "top_k": 20,
        "max_tokens": 4096,
        "presence_penalty": 1.0,
    }
```

### 7.3 프롬프트 빌더 업데이트

```python
# yeji_ai/engine/prompts.py 업데이트 제안

def build_eastern_prompt_qwen3(
    four_pillars: FourPillars,
    element_balance: ElementBalance,
    day_master: str,
    use_thinking: bool = False
) -> str:
    """Qwen3 최적화 동양 사주 해석 프롬프트"""

    # 모드 지시자
    mode_instruction = "" if use_thinking else "/no_think\n"

    elements = {
        "목(木)": element_balance.wood,
        "화(火)": element_balance.fire,
        "토(土)": element_balance.earth,
        "금(金)": element_balance.metal,
        "수(水)": element_balance.water,
    }
    dominant = max(elements, key=elements.get)
    weak = min(elements, key=elements.get)

    return f"""{mode_instruction}[BAZI] 당신은 YEJI(예지) AI입니다. 15년 경력의 동양 사주팔자 전문가입니다.

## 사주 정보
- 사주 구성: {four_pillars.year}(년주) {four_pillars.month}(월주) {four_pillars.day}(일주) {four_pillars.hour or '미상'}(시주)
- 일간(日干): {day_master}
- 오행 분포: 목{element_balance.wood}% 화{element_balance.fire}% 토{element_balance.earth}% 금{element_balance.metal}% 수{element_balance.water}%
- 왕성한 기운: {dominant} ({elements[dominant]}%)
- 부족한 기운: {weak} ({elements[weak]}%)

## 해석 규칙
1. 일간 특성 중심으로 성격/기질 분석
2. 오행 균형 기반 보완점 제시
3. 긍정적 톤 + 현실적 조언
4. **반드시 한국어로만** 3-4문장 답변

## 해석:
"""
```

### 7.4 JSON 응답 처리

```python
import json
from pydantic import BaseModel, ValidationError

class AdviceResponse(BaseModel):
    """조언 응답 스키마"""
    advices: list[str]

def parse_advice_response(response_text: str) -> list[str]:
    """Qwen3 조언 응답 파싱"""
    try:
        # JSON 배열 직접 파싱 시도
        result = json.loads(response_text.strip())
        if isinstance(result, list):
            return result

        # 객체 형태인 경우
        if isinstance(result, dict) and "advices" in result:
            return result["advices"]

    except json.JSONDecodeError:
        # JSON 블록 추출 시도
        import re
        json_match = re.search(r'\[.*?\]', response_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())

    # 파싱 실패 시 기본값
    return ["파싱 오류: 응답을 처리할 수 없습니다."]
```

---

## 참고 자료

- [Qwen3 공식 블로그](https://qwenlm.github.io/blog/qwen3/)
- [Qwen3 GitHub](https://github.com/QwenLM/Qwen3)
- [vLLM Qwen3 배포 가이드](https://qwen.readthedocs.io/en/latest/deployment/vllm.html)
- [vLLM Structured Output 문서](https://docs.vllm.ai/en/latest/features/structured_outputs.html)
- [Qwen3 Best Practices (swift)](https://swift.readthedocs.io/en/latest/BestPractices/Qwen3-Best-Practice.html)

---

**문서 작성**: YEJI AI 팀
**최종 업데이트**: 2026-01-30
