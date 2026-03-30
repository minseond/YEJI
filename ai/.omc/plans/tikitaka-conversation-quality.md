# 티키타카 대화 품질 개선 계획 (v3)

> **Iteration**: 2/5
> **Critic 피드백 반영**: TODO 5 구체화, AC2 범위 통일, 테스트 파일 확인

## 문제 정의

### 현재 상태
- 동양/서양 캐릭터가 각자 **긴 독백** (500자+)을 함
- **고정 패턴**: 항상 "동양 → 서양 → 동양" 순서
- 실제 **대화(티키타카)가 아닌 발표** 형태

### 목표 상태
- 각 발화 **50~150자** 정도로 짧게
- **동적 패턴**: "동→서→동→서→동→서" 등 여러 턴
- **버블 수 동적**: 4~8개

---

## 실제 코드 구조 분석

### 1. 현재 메시지 생성 흐름

```
create_topic_messages() [Line 1124]
  ↓
llm.generate_character_message() [Line 1170-1173]
  ↓ (각 캐릭터별 1개 메시지 생성)
filter_noise() + filter_prompt_leak() + fix_brackets() [Line 1175-1176]
  ↓ (truncate 미적용!)
ChatMessage 생성 [Line 1191-1203]
```

### 2. 핵심 파일 및 위치

| 파일 | 위치 | 역할 |
|------|------|------|
| `prompts/tikitaka_prompts.py` | Line 73 | 발화 길이 지시 |
| `prompts/tikitaka_prompts.py` | Line 126 | 라인 수 지시 (BATTLE_MODE) |
| `prompts/tikitaka_prompts.py` | Line 181 | 라인 수 지시 (CONSENSUS_MODE) |
| `services/tikitaka_service.py` | Line 1124-1219 | `create_topic_messages()` |
| `services/tikitaka_service.py` | Line 1175-1176 | 후처리 (truncate 누락) |
| `services/tikitaka_service.py` | Line 844-862 | `_truncate_message()` 메서드 |

### 3. 테스트 파일
- `tests/test_tikitaka_dialogue.py` ✅ 존재 확인

---

## 구현 태스크

### TODO 1: 시스템 프롬프트 발화 길이 변경
**파일**: `prompts/tikitaka_prompts.py`
**위치**: Line 73

**현재**:
```python
4. **각 발화는 5-7문장, 100~600자로 풍부하게 작성**
```

**변경**:
```python
4. **각 발화는 1-3문장, 50~150자로 짧고 간결하게 작성**
   - 대화처럼 주고받는 느낌
   - 상대가 반응할 여지를 남기세요
```

---

### TODO 2: 대결 모드 라인 수 변경
**파일**: `prompts/tikitaka_prompts.py`
**위치**: Line 126

**현재**:
```python
3. **라인 수**: 2~4개 (정확히 발화 순서대로 생성)
```

**변경**:
```python
3. **라인 수**: 4~8개 (자연스러운 대화처럼 주고받기)
   - 같은 캐릭터가 연속 2회 발화 가능
```

---

### TODO 3: 합의 모드 라인 수 변경
**파일**: `prompts/tikitaka_prompts.py`
**위치**: Line 181

동일하게 `4~8개`로 변경

---

### TODO 4: JSON 예시 변경
**파일**: `prompts/tikitaka_prompts.py`
**위치**: Line 141-148

**변경 예시** (짧은 대화 6개):
```json
{
  "lines": [
    {"speaker": "{char1_code}", "text": "오늘 기운이 참 좋소!", "emotion_code": "HAPPY", "emotion_intensity": 0.8},
    {"speaker": "{char2_code}", "text": "맞아요, 금성이 순행 중이에요.", "emotion_code": "CONFIDENT", "emotion_intensity": 0.7},
    {"speaker": "{char1_code}", "text": "허허, 연애운이 좋겠구려?", "emotion_code": "CURIOUS", "emotion_intensity": 0.6},
    {"speaker": "{char2_code}", "text": "네! 특히 이번 주가 좋아요.", "emotion_code": "HAPPY", "emotion_intensity": 0.8},
    {"speaker": "{char1_code}", "text": "듣기 좋은 말이오.", "emotion_code": "PLAYFUL", "emotion_intensity": 0.5},
    {"speaker": "{char2_code}", "text": "용기 내보세요!", "emotion_code": "EMPATHETIC", "emotion_intensity": 0.7}
  ],
  "user_prompt_text": "더 자세히 알고 싶은 부분이 있나요?"
}
```

---

### TODO 5: create_topic_messages()에 truncate 적용
**파일**: `services/tikitaka_service.py`
**위치**: Line 1175-1176 이후 (Line 1177에 추가)

**현재 코드** (Line 1175-1176):
```python
soiseol_msg = fix_brackets(filter_prompt_leak(filter_noise(soiseol_msg, aggressive=False)))
stella_msg = fix_brackets(filter_prompt_leak(filter_noise(stella_msg, aggressive=False)))
```

**변경 (Line 1177-1178에 추가)**:
```python
# 메시지 길이 제한 (150자)
soiseol_msg = self._truncate_message(soiseol_msg, max_length=150)
stella_msg = self._truncate_message(stella_msg, max_length=150)
```

---

## 수용 기준 (Acceptance Criteria)

| # | 기준 | 검증 방법 |
|---|------|----------|
| AC1 | 각 메시지가 200자 이하 | `len(msg.content) <= 200` |
| AC2 | lines 배열이 4~8개 | `4 <= len(lines) <= 8` |
| AC3 | 연속 동일 speaker 허용 | 패턴 제약 없음 확인 |
| AC4 | 기존 테스트 통과 | `pytest tests/test_tikitaka_dialogue.py` |

---

## 리스크 및 완화

| 리스크 | 영향 | 완화 방안 |
|--------|------|----------|
| LLM이 지시 무시 | 여전히 긴 응답 | `_truncate_message()` 강제 적용 (TODO 5) |
| 메시지 수 부족 | 대화가 너무 짧음 | 프롬프트에서 최소 4개 지시 |
| 문맥 손실 | truncate 시 의미 손실 | 문장 단위 자르기 (기존 로직) |

---

## 구현 순서

1. `tikitaka_prompts.py` Line 73 수정 (TODO 1)
2. `tikitaka_prompts.py` Line 126 수정 (TODO 2)
3. `tikitaka_prompts.py` Line 181 수정 (TODO 3)
4. `tikitaka_prompts.py` Line 141-148 수정 (TODO 4)
5. `tikitaka_service.py` Line 1177-1178 추가 (TODO 5)
6. `pytest tests/test_tikitaka_dialogue.py` 실행

---

**PLAN_READY: .omc/plans/tikitaka-conversation-quality.md**
