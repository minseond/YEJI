# PRD: Fortune Summary API

## 개요

사주/점성술 분석 결과를 요약하여 반환하는 API 설계.
Chat API의 그리팅 생성 시 사용하는 요약 컨텍스트를 별도 API로 제공.

---

## 배경 및 목적

### 문제점
1. **중복 분석 방지**: 프론트엔드가 Fortune API로 분석 후, Chat API에서 다시 분석하는 비효율
2. **요약 재사용**: 동일 사용자의 요약 데이터를 여러 곳에서 재사용 필요
3. **토큰 절약**: LLM 컨텍스트에 전체 데이터 대신 ~100토큰 요약본 사용

### 해결책
- Fortune API 결과에 `fortune_key` 추가
- Summary API로 요약본 조회/생성
- Chat API는 `fortune_key`로 캐시된 요약본 사용

---

## 전체 흐름

```
┌─────────────────────────────────────────────────────────────────┐
│                        프론트엔드 흐름                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. POST /fortune/eastern                                       │
│     └─ 응답: { ...분석결과, fortune_key: "eastern:..." }         │
│                                                                 │
│  2. POST /fortune/western                                       │
│     └─ 응답: { ...분석결과, fortune_key: "western:..." }         │
│                                                                 │
│  3. POST /fortune/eastern/summary  (선택적)                      │
│     └─ 응답: { fortune_key, summary, source: "cached|generated" }│
│                                                                 │
│  4. POST /fortune/western/summary  (선택적)                      │
│     └─ 응답: { fortune_key, summary, source: "cached|generated" }│
│                                                                 │
│  5. POST /fortune/chat/turn/start                               │
│     └─ 요청: { eastern_fortune_key, western_fortune_key, ... }  │
│     └─ 내부: 요약 캐시 확인 → 없으면 생성                          │
│                                                                 │
│  6. POST /fortune/chat/turn/continue                            │
│     └─ 요청: { session_id, message }                            │
│     └─ 인사/그리팅 없이 대화 진행                                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## API 명세

### 1. 동양 사주 요약 API

**Endpoint**: `POST /api/v1/fortune/eastern/summary`

**Request**:
```json
{
    "fortune_key": "eastern:1990-05-15:14:30:M"
}
```

**Response (200)**:
```json
{
    "fortune_key": "eastern:1990-05-15:14:30:M",
    "summary": "병화 일간, 목 기운 강함, 양 우세(63%), 인성 강함. 창의력과 리더십이 뛰어나며 성장 에너지가 넘침.",
    "source": "cached",
    "cached_at": "2024-01-15T10:30:00Z"
}
```

**Response (404)**: Fortune 데이터 없음
```json
{
    "detail": "사주 분석 데이터를 찾을 수 없습니다. 먼저 /fortune/eastern API로 분석해주세요.",
    "fortune_key": "eastern:1990-05-15:14:30:M"
}
```

---

### 2. 서양 점성술 요약 API

**Endpoint**: `POST /api/v1/fortune/western/summary`

**Request**:
```json
{
    "fortune_key": "western:1990-05-15:14:30"
}
```

**Response (200)**:
```json
{
    "fortune_key": "western:1990-05-15:14:30",
    "summary": "황소자리 태양, 불 원소 우세, 카디널 모드 지배. 열정적이고 추진력 있으며 리더십이 뛰어남.",
    "source": "generated",
    "cached_at": "2024-01-15T10:30:00Z"
}
```

**Response (404)**: Fortune 데이터 없음
```json
{
    "detail": "점성술 분석 데이터를 찾을 수 없습니다. 먼저 /fortune/western API로 분석해주세요.",
    "fortune_key": "western:1990-05-15:14:30"
}
```

---

## fortune_key 구조

### 동양 사주 (Eastern)
```
eastern:{birth_date}:{birth_time|unknown}:{gender}
```

| 필드 | 설명 | 예시 |
|------|------|------|
| birth_date | 생년월일 (YYYY-MM-DD) | 1990-05-15 |
| birth_time | 출생시간 (HH:MM) 또는 unknown | 14:30, unknown |
| gender | 성별 (M/F) | M, F |

**예시**:
- `eastern:1990-05-15:14:30:M`
- `eastern:1990-05-15:unknown:F`

### 서양 점성술 (Western)
```
western:{birth_date}:{birth_time|unknown}
```

| 필드 | 설명 | 예시 |
|------|------|------|
| birth_date | 생년월일 (YYYY-MM-DD) | 1990-05-15 |
| birth_time | 출생시간 (HH:MM) 또는 unknown | 14:30, unknown |

**예시**:
- `western:1990-05-15:14:30`
- `western:1990-05-15:unknown`

**참고**: 서양 점성술은 성별이 차트 계산에 영향 없음

---

## Redis 키 구조

### Fortune 데이터 저장
```
fortune:{fortune_key}
TTL: 24시간

예시:
- fortune:eastern:1990-05-15:14:30:M → { 전체 사주 데이터 JSON }
- fortune:western:1990-05-15:14:30 → { 전체 점성술 데이터 JSON }
```

### Summary 캐시
```
summary:{fortune_key}
TTL: 24시간

예시:
- summary:eastern:1990-05-15:14:30:M → "병화 일간, 목 기운 강함..."
- summary:western:1990-05-15:14:30 → "황소자리 태양, 불 원소 우세..."
```

---

## Fortune API 변경사항

### EasternFortuneRequest 변경

```python
class EasternFortuneRequest(BaseModel):
    birth_date: str = Field(..., description="생년월일 (YYYY-MM-DD)")
    birth_time: str | None = Field(None, description="출생시간 (HH:MM)")
    gender: Literal["M", "F"] = Field(..., description="성별 (필수)")  # 필수로 변경
    name: str = Field(..., description="이름 (필수)")  # 필수로 변경
```

### WesternFortuneRequest 변경

```python
class WesternFortuneRequest(BaseModel):
    birth_date: str = Field(..., description="생년월일 (YYYY-MM-DD)")
    birth_time: str | None = Field(None, description="출생시간 (HH:MM)")
    gender: Literal["M", "F"] = Field(..., description="성별 (필수)")  # 필수로 변경
    name: str = Field(..., description="이름 (필수)")  # 필수로 변경
    birth_place: str | None = Field(None, description="출생지역")
    latitude: float | None = Field(None, description="위도")
    longitude: float | None = Field(None, description="경도")
```

### Fortune 응답에 fortune_key 추가

```python
# EasternFortuneResponse
{
    "category": "eastern",
    "chart": {...},
    "stats": {...},
    "summary": "...",
    "message": "...",
    "ui_hints": {...},
    "lucky": {...},
    "fortune_key": "eastern:1990-05-15:14:30:M"  # 새로 추가
}

# WesternFortuneResponse
{
    "category": "western",
    "chart": {...},
    "stats": {...},
    "summary": "...",
    "message": "...",
    "ui_hints": {...},
    "lucky": {...},
    "fortune_key": "western:1990-05-15:14:30"  # 새로 추가
}
```

---

## Chat API 변경사항

### TurnStartRequest 변경

```python
class TurnStartRequest(BaseModel):
    # 기존 birth_date, birth_time, gender 제거
    eastern_fortune_key: str | None = Field(None, description="동양 사주 키")
    western_fortune_key: str | None = Field(None, description="서양 점성술 키")
    category: FortuneCategory | None = Field(None, description="카테고리 (없으면 GENERAL)")
    char1_code: str = Field("SOISEOL", description="캐릭터1 코드")
    char2_code: str = Field("STELLA", description="캐릭터2 코드")
```

### TurnResponse 변경

```python
class TurnResponse(BaseModel):
    session_id: str
    turn: int
    messages: list[ChatMessage]
    suggested_question: str
    is_complete: bool
    summary_source: str | None = Field(None, description="요약 출처 (cached/generated)")
```

---

## 요약 생성 로직

### create_summarized_eastern_context()
```python
def create_summarized_eastern_context(eastern_data: dict) -> str:
    """
    동양 사주 데이터를 ~100토큰 요약으로 변환

    출력 예시:
    "병화 일간, 목 기운 강함(37%), 양 우세(63%), 인성 강함.
     창의력과 리더십이 뛰어나며 성장 에너지가 넘침."
    """
```

### create_summarized_western_context()
```python
def create_summarized_western_context(western_data: dict) -> str:
    """
    서양 점성술 데이터를 ~100토큰 요약으로 변환

    출력 예시:
    "황소자리 태양, 전갈자리 달, 사자자리 상승.
     불 원소 우세(40%), 카디널 모드 지배.
     열정적이고 추진력 있으며 리더십이 뛰어남."
    """
```

---

## 프롬프트 변경사항

### Start 프롬프트 (인사 포함)
```
당신은 {char1_name}입니다.
사용자의 사주/점성술 요약: {summary}
카테고리: {category}

첫 대화이므로 친근하게 인사하고, {category} 관련 이야기를 시작하세요.
```

### Continue 프롬프트 (인사 제외)
```
당신은 {char1_name}입니다.
사용자의 사주/점성술 요약: {summary}
카테고리: {category}
이전 대화: {history}

인사나 그리팅 없이 바로 대화를 이어가세요.
사용자 메시지: {user_message}
```

---

## Pydantic 모델 정의

### SummaryRequest
```python
class FortuneSummaryRequest(BaseModel):
    """요약 조회 요청"""
    fortune_key: str = Field(..., description="Fortune API에서 받은 키")
```

### SummaryResponse
```python
class FortuneSummaryResponse(BaseModel):
    """요약 조회 응답"""
    fortune_key: str = Field(..., description="요청한 키")
    summary: str = Field(..., description="요약 텍스트 (~100토큰)")
    source: Literal["cached", "generated"] = Field(..., description="요약 출처")
    cached_at: str | None = Field(None, description="캐시 시간 (ISO8601)")
```

---

## 구현 체크리스트

### Phase 1: Fortune API 변경
- [ ] `EasternFortuneRequest`에 gender, name 필수 추가
- [ ] `WesternFortuneRequest`에 gender, name 필수 추가
- [ ] `generate_fortune_key()` 함수 구현
- [ ] Fortune API 응답에 `fortune_key` 추가
- [ ] Redis에 Fortune 데이터 저장 (키: `fortune:{fortune_key}`)

### Phase 2: Summary API 구현
- [ ] `FortuneSummaryRequest` 모델 정의
- [ ] `FortuneSummaryResponse` 모델 정의
- [ ] `POST /fortune/eastern/summary` 엔드포인트 구현
- [ ] `POST /fortune/western/summary` 엔드포인트 구현
- [ ] Summary 캐시 로직 (Redis 키: `summary:{fortune_key}`)

### Phase 3: Chat API 변경
- [ ] `TurnStartRequest`에서 birth_date 등 제거, fortune_key 추가
- [ ] `TurnResponse`에 `summary_source` 추가
- [ ] Start 로직: fortune_key로 조회 → 요약 캐시 확인 → 그리팅 생성
- [ ] Continue 로직: 인사/그리팅 제외 프롬프트 적용

### Phase 4: 테스트
- [ ] Fortune API fortune_key 생성 테스트
- [ ] Summary API 캐시 hit/miss 테스트
- [ ] Chat API fortune_key 기반 흐름 테스트
- [ ] Continue 인사 제외 확인 테스트

---

## 에러 처리

| 상황 | HTTP 코드 | 에러 메시지 |
|------|-----------|-------------|
| fortune_key 형식 오류 | 400 | "잘못된 fortune_key 형식입니다" |
| Fortune 데이터 없음 | 404 | "사주 분석 데이터를 찾을 수 없습니다" |
| Redis 연결 실패 | 503 | "캐시 서버 연결 실패" |
| 요약 생성 실패 | 500 | "요약 생성 중 오류 발생" |

---

## 마이그레이션

### 기존 API 호환성
- Fortune API: `fortune_key` 필드 추가 (기존 필드 유지)
- Chat API: 기존 `birth_date` 등 파라미터 deprecated 처리 후 제거 예정

### 프론트엔드 변경사항
1. Fortune API 호출 시 `gender`, `name` 필수 전달
2. Fortune API 응답에서 `fortune_key` 저장
3. Chat API 호출 시 `fortune_key` 전달 (birth_date 등 제거)

---

## 참고

- 기존 요약 함수: `tikitaka_service.py`의 `create_summarized_eastern_context()`, `create_summarized_western_context()`
- Redis 클라이언트: 기존 tikitaka_service의 Redis 연결 재사용
- TTL: Fortune 데이터 및 요약 모두 24시간
