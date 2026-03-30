# Pattern: 티키타카 대화 생성 (LLM + 코드 조합)

## 개요

LLM과 코드를 분리하여 일관된 JSON 구조를 보장하면서 개인화된 대화를 생성하는 패턴

---

## 문제

LLM에게 복잡한 JSON 구조를 직접 생성하게 하면:
- JSON 형식 오류 발생 가능
- 필수 필드 누락
- ID/timestamp 형식 불일치
- 검증 규칙 위반

---

## 해결책

### 역할 분리

| 역할 | LLM | 코드 |
|------|-----|------|
| 대화 텍스트 | ✅ 생성 | 조립 |
| 감정 코드 | ✅ 선택 | 조립 |
| bubble_id | - | ✅ 생성 |
| timestamp | - | ✅ 생성 |
| turn_end | - | ✅ 생성 |
| meta | - | ✅ 생성 |

### 아키텍처

```
┌─────────────────────────────────────────────────────┐
│                   컨텍스트 준비                      │
│  EasternFortuneResponse → eastern_context (str)     │
│  WesternFortuneDataV2   → western_context (str)     │
└─────────────────────────┬───────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────┐
│                    LLM 호출                         │
│  프롬프트 → vLLM → DialogueOutput                   │
│  {                                                  │
│    "lines": [                                       │
│      {"speaker": "EAST", "text": "...", ...}       │
│    ],                                               │
│    "user_prompt_text": "..."                       │
│  }                                                  │
└─────────────────────────┬───────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────┐
│                  JSON 조립                          │
│  DialogueOutput + 세션상태 → TurnResponse           │
│  - bubble_id 생성                                   │
│  - timestamp 생성                                   │
│  - turn_end 결정                                    │
│  - meta 설정                                        │
└─────────────────────────┬───────────────────────────┘
                          ▼
                   TurnResponse JSON
```

---

## 구현

### 1. LLM 출력 스키마 (가볍게)

```python
class DialogueLine(BaseModel):
    """LLM이 생성하는 단일 라인"""
    speaker: Literal["EAST", "WEST"]
    text: str = Field(..., min_length=10, max_length=300)
    emotion_code: EmotionCode
    emotion_intensity: float = Field(..., ge=0.0, le=1.0)

class DialogueOutput(BaseModel):
    """LLM 대화 생성 결과"""
    lines: list[DialogueLine]
    user_prompt_text: str
```

### 2. 코드가 조립하는 TurnResponse

```python
class TurnResponse(BaseModel):
    session_id: str           # 세션에서
    turn_id: int              # 세션에서
    bubbles: list[Bubble]     # LLM lines + 코드 메타
    turn_end: TurnEnd         # 코드 로직
    meta: Meta                # 세션에서
```

### 3. 조립 함수

```python
def build_turn_response(
    session: TikitakaSessionState,
    dialogue_output: DialogueOutput,
) -> TurnResponse:
    turn_id = session.get_next_turn_id()
    now = datetime.now(timezone.utc)

    # Bubbles 생성 (LLM 텍스트 + 코드 메타)
    bubbles = []
    for idx, line in enumerate(dialogue_output.lines):
        bubble = Bubble(
            bubble_id=session.get_bubble_id(idx),  # 코드 생성
            speaker=Speaker(line.speaker),
            text=line.text,                         # LLM 생성
            emotion=Emotion(
                code=line.emotion_code,             # LLM 선택
                intensity=line.emotion_intensity,   # LLM 선택
            ),
            timestamp=now.isoformat() + "Z",        # 코드 생성
        )
        bubbles.append(bubble)

    # TurnEnd (코드 로직)
    turn_end = _build_turn_end(session, dialogue_output, turn_id)

    return TurnResponse(
        session_id=session.session_id,
        turn_id=turn_id,
        bubbles=bubbles,
        turn_end=turn_end,
        meta=Meta(...),
    )
```

---

## 폴백 전략

LLM 호출 실패 시:

```python
def _create_fallback_dialogue(mode: DialogueMode) -> DialogueOutput:
    """미리 정의된 폴백 응답"""
    if mode == DialogueMode.CONSENSUS:
        return DialogueOutput(
            lines=[
                DialogueLine(
                    speaker="EAST",
                    text="좋은 기운이 흐르고 있소.",
                    emotion_code=EmotionCode.THOUGHTFUL,
                    emotion_intensity=0.7,
                ),
                DialogueLine(
                    speaker="WEST",
                    text="어머! 저도 똑같이 봤어요!",
                    emotion_code=EmotionCode.SURPRISED,
                    emotion_intensity=0.8,
                ),
            ],
            user_prompt_text="둘 다 같은 의견이네요!",
        )
    # ... 다른 모드
```

---

## 장점

1. **JSON 100% 일관성**
   - ID 형식, timestamp, 필수 필드 보장

2. **LLM 실패 내성**
   - 폴백으로 서비스 유지

3. **검증 용이**
   - 코드 로직은 단위 테스트 가능
   - LLM 출력만 별도 검증

4. **확장성**
   - 새로운 필드 추가 시 코드만 수정
   - LLM 프롬프트 변경 최소화

---

## 적용 사례

- 티키타카 대화 생성 (본 문서)
- 캐릭터 메시지 생성
- 운세 요약 생성

---

## 참고

- `services/tikitaka_dialogue_generator.py`
- `models/fortune/turn.py`
- `models/fortune/dialogue.py`
- `docs/specs/fortune_chat_turn_contract.md`
