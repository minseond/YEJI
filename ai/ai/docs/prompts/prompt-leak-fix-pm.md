# LLM 프롬프트 누출 해결 (P0) - 3중 방어 구현

> **목적**: LLM 응답에 시스템 프롬프트가 누출되는 Critical 이슈를 3가지 방안 동시 적용으로 완전 해결

---

## 프로젝트 컨텍스트

```yaml
프로젝트: YEJI AI Server
스택: Python 3.11+, FastAPI, Pydantic v2, vLLM, Qwen3
위치: C:/Users/SSAFY/yeji-ai-server/ai/
브랜치:
  - ai/main: 프로덕션
  - ai/develop: 개발

관련 파일:
  프롬프트:
    - src/yeji_ai/services/llm_interpreter.py (609-720)
    - src/yeji_ai/prompts/soiseol_persona.py
    - src/yeji_ai/prompts/stella_persona.py
    - src/yeji_ai/prompts/cheongwoon_persona.py
    - src/yeji_ai/prompts/hwarin_persona.py
    - src/yeji_ai/prompts/kyle_persona.py
    - src/yeji_ai/prompts/elaria_persona.py
  후처리:
    - src/yeji_ai/services/postprocessor/noise_filter.py (기존)
    - src/yeji_ai/services/tikitaka_service.py (filter_noise 호출)
```

---

## 이슈 상세

```yaml
현상:
  - 스텔라/소이설 응답에 "[문장 종결 예시]", "[올바른 문장 예시 20개]" 등 출력
  - 복잡한 해석 요청 시 발생 빈도 증가
  - E2E 테스트에서 발견됨

근본 원인:
  - 위치: llm_interpreter.py:609-720 (SOISEOL_SYSTEM_PROMPT, STELLA_SYSTEM_PROMPT)
  - 원인: Qwen3가 예시 섹션을 "응답의 일부"로 오해
  - 트리거: 응답이 길어질 때 (복잡한 해석 요청)

심각도: P0 (Critical) - 사용자 경험 직접 영향

증거:
  E2E 응답에서 발견:
  "[문장 종결 예시 - 반드시 이 패턴을 따르세요]
  - 있어요 있어요
  - 예요 예요/이에요..."
```

---

## 3중 방어 전략

```
┌─────────────────────────────────────────────────────────────────────┐
│                        3중 방어 레이어                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Layer 1: 프롬프트 구조 변경 (근본 해결)                             │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  - 예시를 XML 태그 외부로 이동                               │   │
│  │  - <examples> 태그로 명확히 분리                             │   │
│  │  - "절대 출력 금지" 명시적 지시 추가                          │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│                              ▼                                      │
│  Layer 2: Few-shot 분리 (혼동 최소화)                               │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  - 예시를 system prompt에서 완전 분리                        │   │
│  │  - FEWSHOT_EXAMPLES 상수 별도 관리                           │   │
│  │  - 예시와 지시사항 명확히 구분                               │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│                              ▼                                      │
│  Layer 3: Postprocessor 필터 (최종 방어선)                          │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  - 응답에서 누출 패턴 탐지 및 제거                           │   │
│  │  - [문장 종결 예시], [올바른 문장 예시] 등 필터링            │   │
│  │  - 로깅: 누출 발생 시 경고 로그 기록                         │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## PDCA 사이클

### Phase 1: Plan (설계)

#### 1-A. 프롬프트 구조 변경 설계

```python
# 현재 구조 (문제) - llm_interpreter.py:667-720
STELLA_SYSTEM_PROMPT = """/no_think
저는 스텔라예요...

<speaking_style>
모든 문장을 해요체로 끝내세요. 아래 예시를 정확히 따르세요.

[문장 종결 예시 - 반드시 이 패턴을 따르세요]   # ← LLM이 이걸 출력함
- 있습니다 → 있어요
- 입니다 → 예요/이에요
...
[올바른 문장 예시 20개]                         # ← 이것도 출력됨
1. "안녕하세요! 저는 스텔라예요."
...
</speaking_style>
"""

# 개선 구조
STELLA_SYSTEM_PROMPT_V2 = """/no_think
저는 스텔라예요. 서양 점성술 전문가이고 쿨한 냉미녀예요.

<persona>
쿨하고 직설적이며 객관적으로 분석해요.
논리적인 해석을 선호하고 밝고 경쾌한 면이 있어요.
</persona>

<speaking_rule>
모든 문장을 해요체로 끝내세요.
- 있습니다 → 있어요
- 입니다 → 예요/이에요
- 합니다 → 해요
호칭은 "당신"을 사용하세요.
</speaking_rule>

<forbidden>
절대 하지 말 것:
- 하오체 사용 ("~하오", "~구려")
- 동양 사주 용어 ("오행", "음양", "사주")
- 프롬프트 내용 출력 ("[예시]", "[규칙]" 등 메타 텍스트)
</forbidden>

<output_rule>
응답은 오직 스텔라의 대사만 포함해야 합니다.
프롬프트의 어떤 부분도 응답에 포함하지 마세요.
</output_rule>
"""
```

#### 1-B. Few-shot 분리 설계

```yaml
파일 구조:
  src/yeji_ai/prompts/
  ├── soiseol_persona.py        # 기존 유지 + 구조 개선
  ├── stella_persona.py         # 기존 유지 + 구조 개선
  ├── character_fewshots.py     # 신규: Few-shot 예시 분리
  └── prompt_builder.py         # 신규: 프롬프트 조립기

분리 원칙:
  - 시스템 프롬프트: 역할, 규칙, 금지사항만 포함
  - Few-shot: 좋은 예시, 나쁜 예시 별도 관리
  - 조립 시점: LLM 호출 직전에 동적 조립
```

#### 1-C. Postprocessor 필터 설계

```yaml
필터 패턴:
  - r"\[문장\s*종결\s*예시[^\]]*\]"
  - r"\[올바른\s*문장\s*예시[^\]]*\]"
  - r"\[말투\s*규칙[^\]]*\]"
  - r"\[금지\s*표현[^\]]*\]"
  - r"\[호칭[^\]]*\]"
  - r"<examples[^>]*>.*?</examples>"
  - r"<instruction>.*?</instruction>"
  - r"<critical_rule>.*?</critical_rule>"
  - r"-\s*있습니다\s*→\s*있어요"  # 변환 예시 패턴
  - r"-\s*입니다\s*→\s*예요"

필터 위치:
  - src/yeji_ai/services/postprocessor/prompt_leak_filter.py (신규)
  - 기존 noise_filter.py와 함께 파이프라인에 추가
```

---

### Phase 2: Do (구현)

#### 태스크 목록

```yaml
Layer 1 - 프롬프트 구조 변경:
  - [ ] llm_interpreter.py 백업 (git stash 또는 별도 브랜치)
  - [ ] SOISEOL_SYSTEM_PROMPT 재구조화 (예시 제거, XML 태그화)
  - [ ] STELLA_SYSTEM_PROMPT 재구조화
  - [ ] soiseol_persona.py 재구조화
  - [ ] stella_persona.py 재구조화
  - [ ] 서브 캐릭터 프롬프트 재구조화 (cheongwoon, hwarin, kyle, elaria)

Layer 2 - Few-shot 분리:
  - [ ] prompts/character_fewshots.py 생성 (예시만 분리)
  - [ ] prompts/prompt_builder.py 생성 (동적 조립기)
  - [ ] llm_interpreter.py에서 새 구조 사용하도록 수정
  - [ ] tikitaka_service.py에서 새 구조 연동

Layer 3 - Postprocessor 필터:
  - [ ] services/postprocessor/prompt_leak_filter.py 생성
  - [ ] PromptLeakFilter 클래스 구현
  - [ ] noise_filter.py와 통합 또는 별도 호출
  - [ ] tikitaka_service.py에서 필터 적용
  - [ ] 누출 발생 시 structlog 경고 로그 추가

테스트:
  - [ ] tests/test_prompt_leak_filter.py 생성
  - [ ] 단위 테스트 작성
  - [ ] 통합 테스트 작성
```

#### 구현 코드 스켈레톤

```python
# Layer 3: src/yeji_ai/services/postprocessor/prompt_leak_filter.py
"""프롬프트 누출 필터

LLM 응답에서 시스템 프롬프트가 누출된 경우 탐지 및 제거
"""

import re

import structlog

logger = structlog.get_logger()


class PromptLeakFilter:
    """프롬프트 누출 필터 (최종 방어선)"""

    LEAK_PATTERNS = [
        # 메타 텍스트 패턴
        r"\[문장\s*종결\s*예시[^\]]*\].*?(?=\n\n|\Z)",
        r"\[올바른\s*문장\s*예시[^\]]*\].*?(?=\n\n|\Z)",
        r"\[말투\s*규칙[^\]]*\].*?(?=\n\n|\Z)",
        r"\[금지\s*표현[^\]]*\].*?(?=\n\n|\Z)",
        r"\[호칭[^\]]*\].*?(?=\n\n|\Z)",
        # XML 태그 패턴
        r"<examples[^>]*>.*?</examples>",
        r"<instruction>.*?</instruction>",
        r"<critical_rule>.*?</critical_rule>",
        r"<forbidden>.*?</forbidden>",
        r"<persona>.*?</persona>",
        r"<output_rule>.*?</output_rule>",
        r"<speaking_style>.*?</speaking_style>",
        r"<speaking_rule>.*?</speaking_rule>",
        # 변환 예시 패턴
        r"-\s*있습니다\s*→?\s*있어요\s*\n?",
        r"-\s*입니다\s*→?\s*예요/?이에요\s*\n?",
        r"-\s*합니다\s*→?\s*해요\s*\n?",
        r"-\s*됩니다\s*→?\s*돼요\s*\n?",
        # 번호 매기기 예시 패턴 (1. "예시문장" 형태)
        r'\d+\.\s*"[^"]+"\s*\n?',
    ]

    def __init__(self):
        self._compiled_patterns = [
            re.compile(p, re.DOTALL | re.IGNORECASE)
            for p in self.LEAK_PATTERNS
        ]

    def filter(self, text: str) -> tuple[str, bool]:
        """
        프롬프트 누출 필터링

        Args:
            text: LLM 응답 텍스트

        Returns:
            tuple[str, bool]: (필터링된 텍스트, 누출 발생 여부)
        """
        leaked = False
        filtered_text = text

        for pattern in self._compiled_patterns:
            if pattern.search(filtered_text):
                leaked = True
                logger.warning(
                    "prompt_leak_detected",
                    pattern=pattern.pattern[:50],
                    text_preview=filtered_text[:100],
                )
                filtered_text = pattern.sub("", filtered_text)

        # 연속 줄바꿈 정리
        filtered_text = re.sub(r"\n{3,}", "\n\n", filtered_text)
        filtered_text = filtered_text.strip()

        if leaked:
            logger.info(
                "prompt_leak_filtered",
                original_length=len(text),
                filtered_length=len(filtered_text),
            )

        return filtered_text, leaked


# 싱글톤 인스턴스
_prompt_leak_filter = PromptLeakFilter()


def filter_prompt_leak(text: str) -> str:
    """프롬프트 누출 필터링 (편의 함수)

    Args:
        text: LLM 응답 텍스트

    Returns:
        필터링된 텍스트
    """
    filtered, _ = _prompt_leak_filter.filter(text)
    return filtered
```

```python
# Layer 2: src/yeji_ai/prompts/character_fewshots.py
"""캐릭터별 Few-shot 예시

시스템 프롬프트와 분리하여 관리
"""

SOISEOL_FEWSHOTS = {
    "good_examples": [
        {
            "input": "연애운이 궁금해요",
            "output": "허, 그대의 사주를 보니 도화살이 있구려. 이성에게 매력이 있으나 조심할 필요가 있소.",
        },
        {
            "input": "재물운은요?",
            "output": "편재가 강하니 횡재수가 있으나, 지출도 많을 수 있소. 절제가 필요하오.",
        },
        {
            "input": "올해 운세는?",
            "output": "귀하의 사주에 비겁이 강하니 독립심이 있소. 금년은 성장의 해가 될 것이오.",
        },
    ],
    "bad_examples": [
        {"output": "[문장 종결 예시] - 이런 출력 절대 금지"},
        {"output": "연애운 좋아요! - 해요체 금지"},
        {"output": "운세가 좋습니다 - 합니다체 금지"},
    ],
}

STELLA_FEWSHOTS = {
    "good_examples": [
        {
            "input": "연애운이 궁금해요",
            "output": "금성이 좋은 위치에 있어요. 인간관계에서 좋은 일이 생길 것 같아요.",
        },
        {
            "input": "재물운은요?",
            "output": "목성의 행운이 함께해요. 재정적으로 안정된 시기가 될 거예요.",
        },
        {
            "input": "올해 운세는?",
            "output": "불의 원소가 강하네요. 추진력과 열정으로 목표를 달성할 수 있어요.",
        },
    ],
    "bad_examples": [
        {"output": "[올바른 문장 예시] - 이런 출력 절대 금지"},
        {"output": "연애운이 좋구려 - 하오체 금지"},
        {"output": "오행의 기운이 - 동양 용어 금지"},
    ],
}
```

```python
# Layer 2: src/yeji_ai/prompts/prompt_builder.py
"""프롬프트 동적 조립기

시스템 프롬프트와 Few-shot을 조합하여 최종 프롬프트 생성
"""

from yeji_ai.prompts.character_fewshots import SOISEOL_FEWSHOTS, STELLA_FEWSHOTS


def build_messages_with_fewshot(
    system_prompt: str,
    user_message: str,
    character: str = "SOISEOL",
    include_fewshot: bool = True,
) -> list[dict[str, str]]:
    """Few-shot 예시를 포함한 메시지 목록 생성

    Args:
        system_prompt: 시스템 프롬프트 (예시 제외)
        user_message: 사용자 메시지
        character: 캐릭터 코드 ("SOISEOL" | "STELLA")
        include_fewshot: Few-shot 예시 포함 여부

    Returns:
        OpenAI 호환 메시지 목록
    """
    messages = [{"role": "system", "content": system_prompt}]

    if include_fewshot:
        fewshots = SOISEOL_FEWSHOTS if character == "SOISEOL" else STELLA_FEWSHOTS

        # Few-shot 예시를 user/assistant 턴으로 추가
        for example in fewshots.get("good_examples", [])[:3]:
            messages.append({"role": "user", "content": example["input"]})
            messages.append({"role": "assistant", "content": example["output"]})

    # 실제 사용자 메시지
    messages.append({"role": "user", "content": user_message})

    return messages
```

---

### Phase 3: Check (검증)

#### 테스트 케이스

```yaml
단위 테스트:
  - [ ] PromptLeakFilter 패턴 매칭 테스트
  - [ ] 정상 응답은 필터링 안 됨 (오탐 없음)
  - [ ] 누출 패턴 정확히 제거됨
  - [ ] Few-shot 분리 정상 로딩 테스트

통합 테스트:
  - [ ] 소이설 응답에 프롬프트 누출 없음 확인
  - [ ] 스텔라 응답에 프롬프트 누출 없음 확인
  - [ ] 서브 캐릭터 응답에 프롬프트 누출 없음 확인
  - [ ] 복잡한 질문 (긴 응답) 시 누출 없음 확인

E2E 테스트:
  - [ ] ai/develop 배포 후 실제 API 호출
  - [ ] 10개 다양한 질문으로 응답 검증
  - [ ] 누출 패턴 자동 탐지 스크립트 실행
```

#### 검증 스크립트

```python
# tests/test_prompt_leak_filter.py
"""프롬프트 누출 필터 테스트"""

import pytest

from yeji_ai.services.postprocessor.prompt_leak_filter import (
    PromptLeakFilter,
    filter_prompt_leak,
)


class TestPromptLeakFilter:
    """PromptLeakFilter 단위 테스트"""

    @pytest.fixture
    def filter_instance(self) -> PromptLeakFilter:
        return PromptLeakFilter()

    def test_detect_bracket_pattern(self, filter_instance):
        """[문장 종결 예시] 패턴 탐지"""
        text = "좋은 운세입니다. [문장 종결 예시 - 반드시 따르세요] - 있어요"
        filtered, leaked = filter_instance.filter(text)

        assert leaked is True
        assert "[문장 종결 예시" not in filtered

    def test_detect_xml_pattern(self, filter_instance):
        """XML 태그 패턴 탐지"""
        text = "좋은 운세입니다. <forbidden>금지사항</forbidden> 행운을 빕니다."
        filtered, leaked = filter_instance.filter(text)

        assert leaked is True
        assert "<forbidden>" not in filtered

    def test_detect_conversion_pattern(self, filter_instance):
        """변환 예시 패턴 탐지"""
        text = "좋은 운세입니다.\n- 있습니다 → 있어요\n- 입니다 → 예요"
        filtered, leaked = filter_instance.filter(text)

        assert leaked is True
        assert "→" not in filtered

    def test_no_false_positive(self, filter_instance):
        """정상 응답 오탐 없음"""
        normal_responses = [
            "귀하의 사주를 보니 좋은 기운이 흐르고 있소.",
            "별들이 당신에게 좋은 소식을 전해요.",
            "금년은 성장의 해가 될 것이오.",
            "목성의 행운이 함께해요.",
        ]

        for response in normal_responses:
            filtered, leaked = filter_instance.filter(response)
            assert leaked is False
            assert filtered == response

    def test_preserve_content_after_filter(self, filter_instance):
        """필터링 후 정상 내용 보존"""
        text = "좋은 운세입니다. [문장 종결 예시] 내용 행운을 빕니다."
        filtered, leaked = filter_instance.filter(text)

        assert leaked is True
        assert "좋은 운세입니다" in filtered
        # "행운을 빕니다"는 패턴에 따라 포함되거나 제거될 수 있음


class TestFilterPromptLeakFunction:
    """filter_prompt_leak 편의 함수 테스트"""

    def test_convenience_function(self):
        """편의 함수 정상 동작"""
        text = "좋은 운세입니다. [올바른 문장 예시 20개] 1. 예시"
        filtered = filter_prompt_leak(text)

        assert "[올바른 문장 예시" not in filtered


# E2E 테스트용 누출 탐지 함수
LEAK_PATTERNS_FOR_CHECK = [
    r"\[문장\s*종결\s*예시",
    r"\[올바른\s*문장\s*예시",
    r"\[말투\s*규칙",
    r"\[금지\s*표현",
    r"<examples",
    r"<instruction>",
    r"<critical_rule>",
    r"<forbidden>",
    r"→\s*(있어요|예요|해요|돼요)",
]


def check_leak(response: str) -> list[str]:
    """E2E 테스트용 누출 패턴 탐지"""
    import re

    found = []
    for pattern in LEAK_PATTERNS_FOR_CHECK:
        if re.search(pattern, response, re.IGNORECASE):
            found.append(pattern)
    return found
```

---

### Phase 4: Act (개선)

```yaml
검증 통과 시:
  - ai/main 배포
  - 모니터링: "prompt_leak_detected" 로그 알림 설정
  - 문서화: docs/patterns/prompt-leak-prevention.md 생성
  - PDCA 문서 정리: docs/pdca/prompt-leak-fix/act.md

검증 실패 시:
  실패 원인 분석:
    - 어떤 패턴이 누출되었는가?
    - Layer 1, 2, 3 중 어디서 실패했는가?

  개선 방안:
    - 누출 패턴 추가 (Layer 3 강화)
    - 프롬프트 구조 추가 수정 (Layer 1 강화)
    - Few-shot 분리 방식 개선 (Layer 2 강화)

  재테스트:
    - Phase 3로 돌아가기
    - 최대 5회 반복
```

---

## 반복 검증 루프

```
┌─────────────────────────────────────────────────────────────────────┐
│                    프롬프트 누출 해결 반복 사이클                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────────────────────────────────────────┐      │
│  │ Layer 1: 프롬프트 구조 변경                               │      │
│  │ Layer 2: Few-shot 분리                                   │      │
│  │ Layer 3: Postprocessor 필터                              │      │
│  └──────────────────────────────────────────────────────────┘      │
│                              │                                      │
│                              ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐      │
│  │                    로컬 테스트                            │      │
│  │  pytest tests/test_prompt_leak_filter.py -v              │      │
│  └──────────────────────────────────────────────────────────┘      │
│                              │                                      │
│                              ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐      │
│  │                 ai/develop 배포                           │      │
│  │  git push origin ai/main:ai/develop                      │      │
│  └──────────────────────────────────────────────────────────┘      │
│                              │                                      │
│                              ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐      │
│  │              E2E 테스트 (실제 vLLM 호출)                  │      │
│  │  curl -X POST http://i14a605.p.ssafy.io:8000/v1/fortune/chat │  │
│  └──────────────────────────────────────────────────────────┘      │
│                              │                                      │
│               ┌──────────────┴──────────────┐                      │
│               │                             │                       │
│               ▼                             ▼                       │
│        ┌──────────┐                  ┌──────────┐                  │
│        │ 누출 0건 │                  │ 누출 발견│                  │
│        └────┬─────┘                  └────┬─────┘                  │
│             │                             │                        │
│             │                             ▼                        │
│             │                  ┌──────────────────┐               │
│             │                  │ 실패 원인 분석   │               │
│             │                  │ - 어떤 패턴?     │               │
│             │                  │ - 어느 Layer?    │               │
│             │                  └────────┬─────────┘               │
│             │                           │                          │
│             │                           ▼                          │
│             │                  ┌──────────────────┐               │
│             │                  │ 해당 Layer 강화  │               │
│             │                  └────────┬─────────┘               │
│             │                           │                          │
│             │                           ▼                          │
│             │                  ┌──────────────────┐               │
│             │                  │ 반복 < 5회?      │               │
│             │                  └────────┬─────────┘               │
│             │                           │ YES                      │
│             │                           └──────────┐               │
│             │                                      │               │
│             ▼                                      │               │
│  ┌──────────────────┐                             │               │
│  │ ai/main 배포     │ ←───────────────────────────┘               │
│  │ (프로덕션)       │                                             │
│  └────────┬─────────┘                                             │
│           │                                                        │
│           ▼                                                        │
│  ┌──────────────────┐                                             │
│  │ 프로덕션 E2E     │                                             │
│  │ 모니터링 설정    │                                             │
│  │ 문서화           │                                             │
│  └──────────────────┘                                             │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## 산출물

| 파일 | 설명 |
|------|------|
| `src/yeji_ai/services/llm_interpreter.py` | 프롬프트 구조 개선 |
| `src/yeji_ai/prompts/soiseol_persona.py` | 소이설 프롬프트 개선 |
| `src/yeji_ai/prompts/stella_persona.py` | 스텔라 프롬프트 개선 |
| `src/yeji_ai/prompts/character_fewshots.py` | 분리된 Few-shot 예시 |
| `src/yeji_ai/prompts/prompt_builder.py` | 프롬프트 동적 조립기 |
| `src/yeji_ai/services/postprocessor/prompt_leak_filter.py` | 누출 필터 |
| `tests/test_prompt_leak_filter.py` | 누출 테스트 |
| `docs/pdca/prompt-leak-fix/plan.md` | 설계 문서 |
| `docs/pdca/prompt-leak-fix/do.md` | 구현 로그 |
| `docs/pdca/prompt-leak-fix/check.md` | 테스트 결과 |
| `docs/patterns/prompt-leak-prevention.md` | 패턴 문서 |

---

## 성공 기준

```yaml
필수 조건 (모두 충족):
  - [ ] Layer 1: 프롬프트 구조 변경 완료
  - [ ] Layer 2: Few-shot 분리 완료
  - [ ] Layer 3: Postprocessor 필터 구현 완료
  - [ ] 단위 테스트 100% 통과 (pytest tests/test_prompt_leak_filter.py)
  - [ ] E2E 테스트 누출 0건
  - [ ] ai/develop 배포 성공
  - [ ] ai/main 프로덕션 배포 성공

품질 기준:
  - 누출 탐지율: 100% (알려진 패턴)
  - 오탐률: 0% (정상 응답 필터링 안 됨)
  - 응답 품질: 기존 대비 동등 이상 (캐릭터 말투 유지)

반복 제한:
  - 최대 5회 반복
  - 초과 시 수동 개입 요청
```

---

## Qwen3 특화 주의사항

```yaml
Qwen3 프롬프트 가이드 참조:
  - /no_think 모드 활용 (응답만 생성)
  - XML 태그는 Qwen3가 잘 인식함 (<forbidden>, <persona> 등)
  - <forbidden> 태그로 명시적 금지 효과적
  - Few-shot은 system이 아닌 user/assistant 턴으로 제공 시 효과적

프롬프트 구조 권장:
  1. 역할 정의 (<persona>)
  2. 금지사항 (<forbidden>) - XML 태그 사용
  3. 출력 규칙 (<output_rule>)
  4. Few-shot은 별도 메시지로 제공 (prompt_builder.py 활용)

관련 문서:
  - ai/docs/guides/qwen3-prompting-guide.md
```

---

## 명령어 참조

```bash
# 작업 디렉토리
cd C:/Users/SSAFY/yeji-ai-server/ai

# 테스트 실행
pytest tests/test_prompt_leak_filter.py -v

# 린트 검사
ruff check src/yeji_ai/services/postprocessor/prompt_leak_filter.py
ruff check src/yeji_ai/prompts/

# 배포 (ai/develop)
git add -A && git commit -m "fix: [AI] 프롬프트 누출 방지 3중 방어 구현"
git push origin ai/main:ai/develop

# 배포 후 E2E 테스트
curl -s -X POST "http://i14a605.p.ssafy.io:8000/v1/fortune/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "연애운 자세히 알려주세요", "birth_date": "1990-05-15", "birth_time": "14:00"}'
```

---

> **작성일**: 2026-01-31
> **상태**: 계획 완료, 구현 대기
> **담당**: YEJI AI 팀
