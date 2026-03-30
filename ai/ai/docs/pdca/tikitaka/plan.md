# Plan: 티키타카 운세 대화 시스템

## 개요

LLM + 코드 조합으로 개인화된 티키타카 대화(소이설 vs 스텔라) 생성 시스템 구현

### 핵심 원칙

1. **LLM은 텍스트만 생성** - 대화 내용, 감정 코드만 생성
2. **코드가 JSON 구조 조립** - bubble_id, timestamp, turn_end 등 메타 정보는 코드에서 생성
3. **대결 70~80% / 합의 20~30%** - 기본은 대결, 가끔 의외의 의견 일치

---

## 1. 아키텍처 설계

### 1.1 전체 흐름

```
┌─────────────────────────────────────────────────────────────────┐
│                      TikitakaDialogueGenerator                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. 컨텍스트 준비                                               │
│     ┌─────────────┐     ┌─────────────┐                        │
│     │ Eastern     │     │ Western     │                        │
│     │ Fortune     │     │ Fortune     │                        │
│     │ Response    │     │ Data V2     │                        │
│     └──────┬──────┘     └──────┬──────┘                        │
│            │                   │                               │
│            ▼                   ▼                               │
│     ┌─────────────────────────────────────┐                    │
│     │     format_context()                │                    │
│     │  - eastern_context (사주 정보)       │                    │
│     │  - western_context (별자리 정보)     │                    │
│     └──────────────┬──────────────────────┘                    │
│                    │                                           │
│  2. 모드 결정      ▼                                           │
│     ┌─────────────────────────────────────┐                    │
│     │   decide_battle_or_consensus()      │                    │
│     │   - random(0.7~0.8) → BATTLE       │                    │
│     │   - random(0.2~0.3) → CONSENSUS    │                    │
│     └──────────────┬──────────────────────┘                    │
│                    │                                           │
│  3. LLM 호출       ▼                                           │
│     ┌─────────────────────────────────────┐                    │
│     │   generate_dialogues()              │                    │
│     │   - 프롬프트 생성                    │                    │
│     │   - vLLM response_format: json      │                    │
│     │   - DialogueOutput 파싱              │                    │
│     └──────────────┬──────────────────────┘                    │
│                    │                                           │
│  4. JSON 조립      ▼                                           │
│     ┌─────────────────────────────────────┐                    │
│     │   build_turn_response()             │                    │
│     │   - Bubble[] 생성                   │                    │
│     │   - TurnEnd 생성                    │                    │
│     │   - Meta 설정                       │                    │
│     └──────────────┬──────────────────────┘                    │
│                    │                                           │
│                    ▼                                           │
│             TurnResponse JSON                                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 컴포넌트 역할

| 컴포넌트 | 역할 | 입력 | 출력 |
|----------|------|------|------|
| `format_eastern_context()` | 사주 정보 포맷팅 | `EasternFortuneResponse` | `str` |
| `format_western_context()` | 별자리 정보 포맷팅 | `WesternFortuneDataV2` | `str` |
| `decide_battle_or_consensus()` | 대결/합의 모드 결정 | 확률 | `DialogueMode` |
| `generate_dialogues()` | LLM으로 대화 생성 | 컨텍스트, 모드, 주제 | `DialogueOutput` |
| `build_turn_response()` | JSON 구조 조립 | `DialogueOutput` | `TurnResponse` |

---

## 2. LLM 출력 스키마 설계

### 2.1 DialogueOutput (LLM이 생성하는 데이터)

```python
class DialogueLine(BaseModel):
    """단일 대화 라인 (LLM 출력)"""
    speaker: Literal["EAST", "WEST"]
    text: str = Field(..., min_length=10, max_length=300)
    emotion_code: EmotionCode
    emotion_intensity: float = Field(..., ge=0.0, le=1.0)


class DialogueOutput(BaseModel):
    """LLM 대화 생성 출력"""
    lines: list[DialogueLine] = Field(..., min_length=2, max_length=4)
    user_prompt_text: str = Field(..., min_length=10, max_length=100)
```

### 2.2 LLM이 생성하지 않는 필드 (코드가 채움)

| 필드 | 생성 주체 | 로직 |
|------|----------|------|
| `session_id` | 코드 | 세션 관리에서 전달 |
| `turn_id` | 코드 | 세션의 현재 턴 번호 |
| `bubble_id` | 코드 | `f"b{turn_id:03d}_{idx}"` 형식 |
| `timestamp` | 코드 | `datetime.now(timezone.utc)` |
| `user_input_ref` | 코드 | 이전 턴의 `prompt_id` |
| `prompt_id` | 코드 | `f"p{turn_id:03d}"` 형식 |
| `turn_end.type` | 코드 | 턴 번호와 정책에 따라 결정 |
| `meta` | 코드 | 세션 상태에서 계산 |

---

## 3. LLM 프롬프트 설계

### 3.1 대결 모드 프롬프트

```
/no_think

당신은 동양 사주학자 소이설과 서양 점성술사 스텔라입니다.
두 캐릭터가 {topic}에 대해 **서로 다른 관점으로 대결**합니다.

## 컨텍스트

### 동양 사주 (소이설 전용)
{eastern_context}

### 서양 점성술 (스텔라 전용)
{western_context}

## 대화 규칙

1. **대결 구조**
   - 각자의 해석을 자신 있게 주장
   - 상대방 의견에 반박 ("잠깐요!", "허, 그건 아니오")
   - 마지막에 약간의 양보 가능 ("그 점은 인정하오")

2. **캐릭터별 말투**
   - 소이설(EAST): 하오체 ("~하오", "~구려", "~시오")
   - 스텔라(WEST): 해요체 ("~해요", "~네요", "~세요")

3. **순서**: {speaker_order}
4. **라인 수**: 2~4개

## 출력 형식 (JSON만 출력)

{{
  "lines": [
    {{"speaker": "EAST", "text": "...", "emotion_code": "THOUGHTFUL", "emotion_intensity": 0.7}},
    {{"speaker": "WEST", "text": "잠깐요! ...", "emotion_code": "PLAYFUL", "emotion_intensity": 0.6}},
    ...
  ],
  "user_prompt_text": "누구 해석이 더 맞는 것 같으세요?"
}}
```

### 3.2 합의 모드 프롬프트

```
/no_think

당신은 동양 사주학자 소이설과 서양 점성술사 스텔라입니다.
이번에는 두 캐릭터가 {topic}에 대해 **의외로 의견이 일치**합니다!

## 컨텍스트
(동일)

## 대화 규칙

1. **합의 구조**
   - 처음에 각자 해석 제시
   - 상대방 해석에 동의하며 놀람 표현 ("어머, 저도 똑같이 봤어요!")
   - "둘 다 같은 말을 하다니, 이건 확실해요!" 느낌

2. **캐릭터별 말투**: (동일)

3. **순서**: {speaker_order}

## 출력 형식

{{
  "lines": [
    {{"speaker": "EAST", "text": "...", "emotion_code": "THOUGHTFUL", "emotion_intensity": 0.7}},
    {{"speaker": "WEST", "text": "어머! 저도 똑같이 봤어요! ...", "emotion_code": "SURPRISED", "emotion_intensity": 0.8}},
    ...
  ],
  "user_prompt_text": "둘 다 같은 의견이네요! 더 궁금한 게 있으세요?"
}}
```

### 3.3 Emotion Code 매핑 가이드 (프롬프트에 포함)

```
## Emotion Code 선택 가이드

| 상황 | EAST 권장 | WEST 권장 |
|------|-----------|-----------|
| 분석/해석 | THOUGHTFUL (0.6~0.8) | THOUGHTFUL (0.5~0.7) |
| 반박/대결 | CONFIDENT (0.6~0.8) | PLAYFUL (0.5~0.7) |
| 좋은 소식 | WARM (0.5~0.7) | EXCITED (0.6~0.8) |
| 경고/주의 | CONCERNED (0.5~0.6) | GENTLE (0.5~0.6) |
| 의외의 합의 | SURPRISED (0.5~0.6) | SURPRISED (0.7~0.8) |
| 마무리 | ENCOURAGING (0.6~0.7) | WARM (0.7~0.8) |

가능한 코드: NEUTRAL, WARM, EXCITED, THOUGHTFUL, ENCOURAGING,
PLAYFUL, MYSTERIOUS, SURPRISED, CONCERNED, CONFIDENT, GENTLE, CURIOUS
```

---

## 4. 코드 구조 설계

### 4.1 새로운 모듈: `tikitaka_dialogue_generator.py`

```python
# yeji_ai/services/tikitaka_dialogue_generator.py

from enum import Enum
from typing import Literal
from pydantic import BaseModel, Field

class DialogueMode(str, Enum):
    BATTLE = "battle"
    CONSENSUS = "consensus"

class EmotionCode(str, Enum):
    NEUTRAL = "NEUTRAL"
    WARM = "WARM"
    EXCITED = "EXCITED"
    THOUGHTFUL = "THOUGHTFUL"
    ENCOURAGING = "ENCOURAGING"
    PLAYFUL = "PLAYFUL"
    MYSTERIOUS = "MYSTERIOUS"
    SURPRISED = "SURPRISED"
    CONCERNED = "CONCERNED"
    CONFIDENT = "CONFIDENT"
    GENTLE = "GENTLE"
    CURIOUS = "CURIOUS"

class DialogueLine(BaseModel):
    """LLM이 생성하는 단일 대화 라인"""
    speaker: Literal["EAST", "WEST"]
    text: str = Field(..., min_length=10, max_length=300)
    emotion_code: EmotionCode
    emotion_intensity: float = Field(..., ge=0.0, le=1.0)

class DialogueOutput(BaseModel):
    """LLM 대화 생성 결과"""
    lines: list[DialogueLine] = Field(..., min_length=2, max_length=4)
    user_prompt_text: str = Field(..., min_length=10, max_length=100)

class TikitakaDialogueGenerator:
    """티키타카 대화 생성기 (LLM + 코드 조합)"""

    def __init__(self, llm_client):
        self.llm = llm_client

    def decide_battle_or_consensus(self) -> DialogueMode:
        """대결/합의 모드 결정 (70:30 비율)"""
        pass

    def format_eastern_context(self, eastern: EasternFortuneResponse) -> str:
        """동양 사주 컨텍스트 포맷팅"""
        pass

    def format_western_context(self, western: WesternFortuneDataV2) -> str:
        """서양 점성술 컨텍스트 포맷팅"""
        pass

    async def generate_dialogues(
        self,
        topic: str,
        eastern_context: str,
        western_context: str,
        mode: DialogueMode,
        user_input_ref: str | None = None,
    ) -> DialogueOutput:
        """LLM으로 대화 생성"""
        pass

    def build_turn_response(
        self,
        session_id: str,
        turn_id: int,
        dialogue_output: DialogueOutput,
        user_input_ref: str | None,
        meta: dict,
    ) -> dict:
        """TurnResponse JSON 구조 조립"""
        pass
```

### 4.2 TurnResponse 모델: `models/fortune/turn.py`

```python
# yeji_ai/models/fortune/turn.py

from datetime import datetime
from enum import Enum
from typing import Literal
from pydantic import BaseModel, Field

class Speaker(str, Enum):
    EAST = "EAST"
    WEST = "WEST"

class EmotionCode(str, Enum):
    NEUTRAL = "NEUTRAL"
    WARM = "WARM"
    EXCITED = "EXCITED"
    THOUGHTFUL = "THOUGHTFUL"
    ENCOURAGING = "ENCOURAGING"
    PLAYFUL = "PLAYFUL"
    MYSTERIOUS = "MYSTERIOUS"
    SURPRISED = "SURPRISED"
    CONCERNED = "CONCERNED"
    CONFIDENT = "CONFIDENT"
    GENTLE = "GENTLE"
    CURIOUS = "CURIOUS"

class Emotion(BaseModel):
    code: EmotionCode
    intensity: float = Field(..., ge=0.0, le=1.0)

class Bubble(BaseModel):
    bubble_id: str
    speaker: Speaker
    text: str = Field(..., min_length=1, max_length=500)
    emotion: Emotion
    user_input_ref: str | None = None
    timestamp: str  # ISO 8601

class InputSchema(BaseModel):
    type: Literal["text", "choice", "date", "datetime"]
    placeholder: str | None = None
    options: list[dict] | None = None
    validation: dict | None = None

class UserPrompt(BaseModel):
    prompt_id: str
    text: str
    input_schema: InputSchema

class TurnEndAwaitUserInput(BaseModel):
    type: Literal["await_user_input"] = "await_user_input"
    user_prompt: UserPrompt

class SummaryItem(BaseModel):
    speaker: Speaker
    key_point: str

class UpgradeHook(BaseModel):
    enabled: bool
    message: str | None = None
    cta_label: str | None = None
    cta_action: str | None = None

class Closure(BaseModel):
    summary: list[SummaryItem]
    next_steps: list[str]
    upgrade_hook: UpgradeHook
    end_marker: Literal["END_SESSION"] = "END_SESSION"

class TurnEndCompleted(BaseModel):
    type: Literal["completed"] = "completed"
    closure: Closure

TurnEnd = TurnEndAwaitUserInput | TurnEndCompleted

class FortuneCategory(str, Enum):
    TOTAL = "total"
    LOVE = "love"
    WEALTH = "wealth"
    CAREER = "career"
    HEALTH = "health"

class Meta(BaseModel):
    current_turn: int = Field(..., ge=1)
    base_turns: int = Field(default=3, ge=1)
    max_turns: int = Field(default=10, ge=1)
    is_premium: bool = False
    category: FortuneCategory = FortuneCategory.TOTAL

class TurnResponse(BaseModel):
    session_id: str
    turn_id: int = Field(..., ge=1)
    bubbles: list[Bubble] = Field(..., min_length=1)
    turn_end: TurnEnd
    meta: Meta
```

---

## 5. 개인화 전략

### 5.1 컨텍스트 주입으로 개인화

동일한 주제(예: 연애운)라도 사용자의 사주/점성 분석 결과에 따라 다른 대화 생성:

**사용자 A (병화+양자리)**
```
동양 컨텍스트:
- 일간: 병화(丙火) - 밝고 열정적
- 오행: 화(火) 강, 수(水) 약
- 음양: 양 70%

서양 컨텍스트:
- 태양: 양자리 - 리더십, 추진력
- 원소: 불 우세
```

→ LLM 출력:
```json
{
  "lines": [
    {"speaker": "EAST", "text": "병화 일간에 도화살이 강하니, 이성에게 매력이 넘치오. 다만 화(火)가 너무 강하면 감정 기복이 클 수 있소.", ...},
    {"speaker": "WEST", "text": "잠깐요! 양자리 태양에 금성 위치가 좋으니까 적극적으로 나가도 괜찮아요!", ...}
  ]
}
```

**사용자 B (임수+물고기자리)**
```
동양 컨텍스트:
- 일간: 임수(壬水) - 지혜롭고 적응력 강함
- 오행: 수(水) 강, 화(火) 약
- 음양: 음 65%

서양 컨텍스트:
- 태양: 물고기자리 - 감성적, 직관적
- 원소: 물 우세
```

→ LLM 출력:
```json
{
  "lines": [
    {"speaker": "EAST", "text": "임수 일간에 도화살이 있으나 음기가 강하니, 천천히 다가가는 것이 좋겠소. 급하게 행동하면 물 흐르듯 인연이 흘러갈 수 있소.", ...},
    {"speaker": "WEST", "text": "잠깐요! 물고기자리는 감수성이 풍부한데, 너무 신중하면 기회를 놓칠 수 있어요. 직감을 믿어보세요!", ...}
  ]
}
```

### 5.2 대결/합의 모드 변화

같은 사용자라도 턴마다 모드가 달라짐:
- Turn 1: 대결 (성격 분석)
- Turn 2: 대결 (연애운)
- Turn 3: 합의 (금전운) ← "둘 다 좋다고 하네!"

---

## 6. 성공 기준 (정량적)

| 메트릭 | 기대값 | 측정 방법 |
|--------|--------|----------|
| JSON 구조 검증 통과율 | 100% | validator 실행 |
| 대결/합의 비율 | 70:30 ± 10% | 100회 생성 후 통계 |
| LLM 출력 파싱 성공률 | > 95% | Pydantic 검증 |
| 응답 시간 | < 5초 | 평균 응답 시간 |
| 개인화 검증 | 다른 결과 | 사주 A vs B 비교 |

---

## 7. 리스크 및 대응

| 리스크 | 확률 | 영향 | 대응 |
|--------|------|------|------|
| LLM JSON 파싱 실패 | 중 | 높 | 재시도 + 폴백 응답 |
| 캐릭터 말투 일관성 | 중 | 중 | 프롬프트 강화 + 후처리 |
| 대결/합의 비율 편향 | 낮 | 중 | 랜덤 시드 검증 |
| 응답 시간 초과 | 낮 | 높 | 타임아웃 + 캐싱 |

---

## 8. 파일 생성 계획

| 파일 | 설명 |
|------|------|
| `models/fortune/turn.py` | TurnResponse 스키마 정의 |
| `models/fortune/dialogue.py` | DialogueOutput LLM 스키마 |
| `services/tikitaka_dialogue_generator.py` | 대화 생성 서비스 |
| `prompts/tikitaka_prompts.py` | 대결/합의 프롬프트 템플릿 |
| `tests/test_tikitaka_dialogue.py` | 단위/통합 테스트 |

---

## 버전 히스토리

| 버전 | 날짜 | 변경 사항 |
|------|------|----------|
| 1.0.0 | 2026-01-30 | 초기 설계 문서 작성 |
