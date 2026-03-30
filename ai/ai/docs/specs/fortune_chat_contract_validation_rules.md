# Fortune Chat Contract Validation Rules v1.0.0

턴 응답 계약 검증 규칙 명세서

---

## 개요

TurnResponse JSON의 유효성을 검증하기 위한 규칙 정의.
프론트엔드와 백엔드 모두에서 동일한 검증 로직 적용 권장.

---

## 필수 검증 규칙 (MUST)

### 1. 최상위 필수 필드

| 필드 | 타입 | 검증 규칙 |
|------|------|-----------|
| `session_id` | string | 비어있으면 안 됨, 길이 1~100 |
| `turn_id` | integer | >= 1 |
| `bubbles` | array | 최소 1개, 최대 10개 |
| `turn_end` | object | 필수 |
| `meta` | object | 필수 |

```python
# 검증 코드 예시
assert response.session_id and len(response.session_id) <= 100
assert response.turn_id >= 1
assert 1 <= len(response.bubbles) <= 10
assert response.turn_end is not None
assert response.meta is not None
```

### 2. bubbles[] 검증

| 규칙 | 설명 | 에러 메시지 |
|------|------|-------------|
| 비어있음 금지 | 모든 턴에서 최소 1개 버블 필수 | "bubbles는 최소 1개 필수" |
| speaker enum | "EAST" 또는 "WEST"만 허용 | "speaker는 EAST 또는 WEST여야 함" |
| text 필수 | 빈 문자열 금지 | "text는 비어있을 수 없음" |
| text 길이 | 1~500자 | "text는 1~500자 이내여야 함" |
| emotion 필수 | code와 intensity 모두 필수 | "emotion 정보 필수" |
| emotion.code enum | 12가지 코드 중 하나 | "유효하지 않은 emotion.code" |
| emotion.intensity | 0.0 ~ 1.0 범위 | "intensity는 0~1 사이여야 함" |
| bubble_id 중복 금지 | 같은 응답 내 중복 ID 금지 | "bubble_id 중복" |
| timestamp 형식 | ISO 8601 형식 | "유효하지 않은 timestamp 형식" |

```python
# 검증 코드 예시
VALID_SPEAKERS = {"EAST", "WEST"}
VALID_EMOTIONS = {
    "NEUTRAL", "WARM", "EXCITED", "THOUGHTFUL", "ENCOURAGING",
    "PLAYFUL", "MYSTERIOUS", "SURPRISED", "CONCERNED",
    "CONFIDENT", "GENTLE", "CURIOUS"
}

bubble_ids = set()
for bubble in response.bubbles:
    assert bubble.speaker in VALID_SPEAKERS
    assert bubble.text and 1 <= len(bubble.text) <= 500
    assert bubble.emotion.code in VALID_EMOTIONS
    assert 0.0 <= bubble.emotion.intensity <= 1.0
    assert bubble.bubble_id not in bubble_ids
    bubble_ids.add(bubble.bubble_id)
```

### 3. turn_end 상호 배타 규칙

| 규칙 | 설명 |
|------|------|
| type 필수 | "await_user_input" 또는 "completed" 중 하나 |
| await_user_input일 때 | user_prompt 필수, closure 금지 |
| completed일 때 | closure 필수, user_prompt 금지 |

```python
# 검증 코드 예시
if response.turn_end.type == "await_user_input":
    assert response.turn_end.user_prompt is not None
    assert not hasattr(response.turn_end, 'closure') or response.turn_end.closure is None
elif response.turn_end.type == "completed":
    assert response.turn_end.closure is not None
    assert not hasattr(response.turn_end, 'user_prompt') or response.turn_end.user_prompt is None
else:
    raise ValueError("turn_end.type은 await_user_input 또는 completed여야 함")
```

### 4. completed 턴 검증

| 규칙 | 설명 |
|------|------|
| summary 필수 | 최소 1개 SummaryItem |
| next_steps 필수 | 빈 배열 허용 |
| upgrade_hook 필수 | enabled 필드 필수 |
| end_marker 고정값 | 반드시 "END_SESSION" |

```python
# 검증 코드 예시
if response.turn_end.type == "completed":
    closure = response.turn_end.closure
    assert len(closure.summary) >= 1
    assert closure.next_steps is not None  # 빈 배열 허용
    assert closure.upgrade_hook is not None
    assert "enabled" in closure.upgrade_hook
    assert closure.end_marker == "END_SESSION"
```

### 5. meta 검증

| 필드 | 검증 규칙 |
|------|-----------|
| current_turn | >= 1 |
| base_turns | >= 1, 기본값 3 |
| max_turns | >= base_turns |
| is_premium | boolean |
| category | "total", "love", "wealth", "career", "health" 중 하나 |

```python
# 검증 코드 예시
VALID_CATEGORIES = {"total", "love", "wealth", "career", "health"}

assert response.meta.current_turn >= 1
assert response.meta.base_turns >= 1
assert response.meta.max_turns >= response.meta.base_turns
assert isinstance(response.meta.is_premium, bool)
assert response.meta.category in VALID_CATEGORIES
```

---

## 경고 검증 규칙 (SHOULD)

검증 실패해도 응답은 유효하지만, 경고 로그 출력 권장.

| 규칙 | 설명 | 경고 메시지 |
|------|------|-------------|
| 버블 3개 초과 | 권장: 2~3개 | "bubbles 개수가 3개를 초과함 (현재: N개)" |
| 같은 speaker 연속 3회 | 대화 흐름 단조로움 | "같은 speaker가 연속 3회 이상 등장" |
| text 300자 초과 | 가독성 저하 | "버블 텍스트가 300자 초과" |
| intensity 극단값 | 0.0 또는 1.0 사용 | "intensity 극단값 사용 (권장: 0.3~0.8)" |

```python
# 경고 검증 코드 예시
import structlog
logger = structlog.get_logger()

def warn_check(response):
    warnings = []

    # 버블 개수 경고
    if len(response.bubbles) > 3:
        warnings.append(f"bubbles 개수가 3개를 초과함 (현재: {len(response.bubbles)}개)")

    # 연속 speaker 경고
    consecutive = 1
    for i in range(1, len(response.bubbles)):
        if response.bubbles[i].speaker == response.bubbles[i-1].speaker:
            consecutive += 1
            if consecutive >= 3:
                warnings.append("같은 speaker가 연속 3회 이상 등장")
                break
        else:
            consecutive = 1

    # text 길이 경고
    for bubble in response.bubbles:
        if len(bubble.text) > 300:
            warnings.append(f"버블 텍스트가 300자 초과 ({bubble.bubble_id})")

    # intensity 극단값 경고
    for bubble in response.bubbles:
        if bubble.emotion.intensity <= 0.1 or bubble.emotion.intensity >= 0.95:
            warnings.append(f"intensity 극단값 사용 ({bubble.bubble_id})")

    for w in warnings:
        logger.warning("turn_response_warning", message=w)

    return warnings
```

---

## 금지 패턴 (MUST NOT)

### 1. 구조적 금지

| 패턴 | 이유 | 검증 방법 |
|------|------|-----------|
| bubbles가 빈 배열 | 프론트 렌더링 실패 | `len(bubbles) >= 1` |
| completed 턴에 user_prompt | 논리 모순 | type 체크 후 필드 존재 여부 |
| await_user_input에 closure | 논리 모순 | type 체크 후 필드 존재 여부 |
| end_marker 다른 값 | 종료 판정 실패 | `end_marker == "END_SESSION"` |

### 2. 데이터 금지

| 패턴 | 이유 | 검증 방법 |
|------|------|-----------|
| text가 빈 문자열 | 의미 없는 버블 | `len(text.strip()) > 0` |
| speaker가 null | enum 위반 | null 체크 |
| emotion.code가 목록 외 | enum 위반 | 허용 목록 체크 |
| intensity가 음수/1 초과 | 범위 위반 | `0 <= intensity <= 1` |

### 3. 비즈니스 로직 금지

| 패턴 | 이유 | 검증 방법 |
|------|------|-----------|
| current_turn > max_turns | 턴 한도 초과 | 비교 검증 |
| base_turns > max_turns | 설정 오류 | 비교 검증 |
| 프리미엄인데 upgrade_hook 활성화 | UX 오류 | `is_premium && upgrade_hook.enabled` 체크 |

---

## 검증 결과 응답 형식

### ValidationResult 스키마

```typescript
interface ValidationResult {
  valid: boolean;              // 전체 유효성
  errors: ValidationError[];   // 필수 규칙 위반 목록
  warnings: string[];          // 경고 목록
}

interface ValidationError {
  field: string;               // 문제 필드 경로 (예: "bubbles[0].speaker")
  message: string;             // 에러 메시지
  code: string;                // 에러 코드 (예: "INVALID_SPEAKER")
}
```

### 예시: 유효한 응답

```json
{
  "valid": true,
  "errors": [],
  "warnings": ["bubbles 개수가 3개를 초과함 (현재: 4개)"]
}
```

### 예시: 유효하지 않은 응답

```json
{
  "valid": false,
  "errors": [
    {
      "field": "bubbles",
      "message": "bubbles는 최소 1개 필수",
      "code": "EMPTY_BUBBLES"
    },
    {
      "field": "turn_end.type",
      "message": "turn_end.type은 await_user_input 또는 completed여야 함",
      "code": "INVALID_TURN_END_TYPE"
    }
  ],
  "warnings": []
}
```

---

## 에러 코드 목록

| 코드 | 설명 |
|------|------|
| `MISSING_REQUIRED_FIELD` | 필수 필드 누락 |
| `INVALID_TYPE` | 타입 불일치 |
| `EMPTY_BUBBLES` | bubbles 빈 배열 |
| `INVALID_SPEAKER` | speaker enum 위반 |
| `EMPTY_TEXT` | text 빈 문자열 |
| `TEXT_TOO_LONG` | text 500자 초과 |
| `INVALID_EMOTION_CODE` | emotion.code enum 위반 |
| `INVALID_INTENSITY` | intensity 범위 위반 |
| `DUPLICATE_BUBBLE_ID` | bubble_id 중복 |
| `INVALID_TURN_END_TYPE` | turn_end.type 오류 |
| `MUTUAL_EXCLUSION_VIOLATION` | 상호 배타 규칙 위반 |
| `INVALID_END_MARKER` | end_marker 오류 |
| `TURN_LIMIT_EXCEEDED` | 턴 한도 초과 |
| `INVALID_CATEGORY` | category enum 위반 |

---

## 버전 히스토리

| 버전 | 날짜 | 변경 사항 |
|------|------|----------|
| 1.0.0 | 2026-01-30 | 초기 검증 규칙 정의 |
