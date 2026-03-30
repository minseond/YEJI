# YEJI AI Server API 사용 가이드

> **버전**: 0.4.2
> **Base URL**:
>   - Production: `https://i14a605.p.ssafy.io/ai`
>   - Development: `https://i14a605.p.ssafy.io/ai-dev`
> **문서 작성일**: 2026-02-05

---

## 목차

1. [Quick Start (3-Step 플로우)](#1-quick-start-3-step-플로우---권장)
2. [API 구조](#2-api-구조)
3. [카테고리 및 캐릭터 코드](#3-카테고리-및-캐릭터-코드)
4. [채팅 API (권장)](#4-채팅-api-권장)
5. [운세 분석 API](#5-운세-분석-api)
6. [레거시 API (Deprecated)](#6-레거시-api-deprecated)
7. [헬스체크 API](#7-헬스체크-api)
8. [에러 처리](#8-에러-처리)
9. [cURL 예시](#9-curl-예시)

---

## 1. Quick Start (3-Step 플로우) - 권장

티키타카 운세 서비스의 기본 플로우입니다. 3단계로 간단하게 운세 대화를 시작할 수 있습니다.

### Step 1. 세션 시작 + 그리팅 (Turn 0)

```http
POST /v1/fortune/chat/turn/start
Content-Type: application/json

{
  "birth_date": "1995-03-15",
  "birth_time": "09:30",
  "category": "LOVE",
  "char1_code": "SOISEOL",
  "char2_code": "STELLA"
}
```

**응답:**
```json
{
  "session_id": "0072ded5",
  "turn": 1,
  "messages": [
    {
      "character": "SOISEOL",
      "type": "GREETING",
      "content": "연애운을 보러 온 귀하를 환영하오. 병화 일간이시니...",
      "timestamp": "2024-01-27T15:30:00"
    },
    {
      "character": "STELLA",
      "type": "GREETING",
      "content": "황소자리 태양이시군요! 안정적인 사랑을 추구하는 타입이에요.",
      "timestamp": "2024-01-27T15:30:05"
    }
  ],
  "debate_status": { "is_consensus": true },
  "ui_hints": { "show_choice": false }
}
```

### Step 2. 대화 계속 (Turn 1+)

```http
POST /v1/fortune/chat/turn/continue
Content-Type: application/json

{
  "session_id": "0072ded5",
  "message": "썸녀랑 잘 될까요?",
  "extend_turn": false
}
```

**응답:**
```json
{
  "session_id": "0072ded5",
  "turn": 2,
  "messages": [
    {
      "character": "SOISEOL",
      "type": "INTERPRETATION",
      "content": "정관의 기운이 강해지는 시기니, 진지한 만남의 기회가 있겠소.",
      "timestamp": "2024-01-27T15:31:00"
    },
    {
      "character": "STELLA",
      "type": "INTERPRETATION",
      "content": "금성이 7하우스를 지나고 있어요. 파트너십에 좋은 에너지가 흐르고 있네요.",
      "timestamp": "2024-01-27T15:31:05"
    }
  ],
  "debate_status": { "is_consensus": true },
  "ui_hints": { "show_choice": false }
}
```

### Step 3. 요약 조회 (선택)

```http
GET /v1/fortune/chat/summary/{session_id}?type=eastern
```

**응답:**
```json
{
  "session_id": "0072ded5",
  "category": "love",
  "fortune_type": "eastern",
  "fortune": {
    "character": "SOISEOL",
    "score": 85,
    "one_line": "정관의 기운으로 진지한 인연이 찾아올 시기예요",
    "keywords": ["정관운", "진지한 만남", "하반기 유리"],
    "detail": "병화 일간으로 밝고 열정적인 성격..."
  }
}
```

> **Tip**: `extend_turn: true`로 설정하면 기본 3턴 이후에도 대화를 계속할 수 있습니다 (최대 10턴).

---

## 2. API 구조

```
/health                          # 헬스체크
/health/ready                    # K8s readiness probe
/health/live                     # K8s liveness probe
/model/status                    # vLLM 모델 상태

/api/v1/fortune/
  ├── chat/turn/start            # POST - 세션 시작 + 그리팅 (권장)
  ├── chat/turn/continue         # POST - 대화 계속 (권장)
  ├── chat/summary/{session_id}  # GET  - 운세 요약 조회
  ├── chat/greeting              # POST - 카테고리별 그리팅
  ├── chat/characters            # GET  - 캐릭터 목록
  │
  ├── eastern                    # POST - 동양 사주 분석
  ├── eastern/enums              # GET  - 동양 Enum 목록
  ├── western                    # POST - 서양 점성술 분석
  ├── western/enums              # GET  - 서양 Enum 목록
  ├── tarot/reading              # POST - 타로 리딩
  └── hwatu/reading              # POST - 화투점 리딩
```

### 공통 헤더

```http
Content-Type: application/json
Accept: application/json
```

---

## 3. 카테고리 및 캐릭터 코드

### 운세 카테고리 (대문자)

| 코드 | 설명 | 한글 |
|------|------|------|
| `GENERAL` | 종합운 | 종합운 |
| `LOVE` | 애정운 | 애정운 |
| `MONEY` | 재물운 | 재물운 |
| `CAREER` | 직장운 | 직장운 |
| `HEALTH` | 건강운 | 건강운 |
| `STUDY` | 학업운 | 학업운 |

> **Note**: API는 대소문자 무관하게 처리합니다 (`LOVE`, `love` 모두 가능).

### 캐릭터 코드

| 코드 | 이름 | 타입 | 전문 분야 | 성격 |
|------|------|------|----------|------|
| `SOISEOL` | 소이설 | 메인 | eastern (동양 사주) | 따뜻한 온미녀, 하오체 |
| `STELLA` | 스텔라 | 메인 | western (서양 점성술) | 쿨한 냉미녀, 해요체 |
| `CHEONGWOON` | 청운 | 서브 | eastern | 신선/현자, 시적 하오체 |
| `HWARIN` | 화린 | 서브 | eastern | 비즈니스, 나른한 해요체 |
| `KYLE` | 카일 | 서브 | western | 도박사, 반말+존댓말 혼용 |
| `ELARIA` | 엘라리아 | 서브 | western | 공주/외교관, 우아한 해요체 |

---

## 4. 채팅 API (권장)

### 4.1 세션 시작 - POST /v1/fortune/chat/turn/start

새 대화 세션을 시작하고 첫 그리팅 메시지를 받습니다.

**요청 파라미터:**

| 필드 | 타입 | 필수 | 설명 |
|------|------|:----:|------|
| `birth_date` | string | **필수** | 생년월일 (YYYY-MM-DD) |
| `birth_time` | string | 선택 | 출생시간 (HH:MM) |
| `category` | string | **필수** | 운세 카테고리 (GENERAL/LOVE/MONEY/CAREER/HEALTH/STUDY) |
| `char1_code` | string | 선택 | 캐릭터1 코드 (기본: SOISEOL) |
| `char2_code` | string | 선택 | 캐릭터2 코드 (기본: STELLA) |

**요청 예시:**
```json
{
  "birth_date": "1995-03-15",
  "birth_time": "09:30",
  "category": "LOVE",
  "char1_code": "SOISEOL",
  "char2_code": "STELLA"
}
```

**응답 구조:**

| 필드 | 타입 | 설명 |
|------|------|------|
| `session_id` | string | 세션 ID (후속 요청에 사용) |
| `turn` | int | 현재 턴 번호 (시작 시 1) |
| `messages` | array | 캐릭터 메시지 목록 |
| `debate_status` | object | 토론 상태 |
| `ui_hints` | object | UI 힌트 |

---

### 4.2 대화 계속 - POST /v1/fortune/chat/turn/continue

기존 세션에서 대화를 이어갑니다.

**요청 파라미터:**

| 필드 | 타입 | 필수 | 설명 |
|------|------|:----:|------|
| `session_id` | string | **필수** | 세션 ID |
| `message` | string | **필수** | 사용자 메시지 |
| `char1_code` | string | 선택 | 캐릭터1 코드 (기본: SOISEOL) |
| `char2_code` | string | 선택 | 캐릭터2 코드 (기본: STELLA) |
| `extend_turn` | bool | 선택 | 추가 턴 요청 (기본: false, 최대 10턴) |

**요청 예시:**
```json
{
  "session_id": "abc12345",
  "message": "연애운이 궁금해요",
  "extend_turn": false
}
```

---

### 4.3 요약 조회 - GET /v1/fortune/chat/summary/{session_id}

세션의 운세 요약 정보를 조회합니다.

**경로 파라미터:**
- `session_id`: 세션 ID

**쿼리 파라미터:**
- `type`: `eastern` 또는 `western`

**응답 구조:**

| 필드 | 타입 | 설명 |
|------|------|------|
| `session_id` | string | 세션 ID |
| `category` | string | 운세 카테고리 |
| `fortune_type` | string | 운세 타입 (eastern/western) |
| `fortune.character` | string | 캐릭터 (SOISEOL/STELLA) |
| `fortune.score` | int | 운세 점수 (0-100) |
| `fortune.one_line` | string | 한 줄 요약 |
| `fortune.keywords` | array | 키워드 목록 |
| `fortune.detail` | string | 상세 내용 |

---

### 4.4 카테고리별 그리팅 - POST /v1/fortune/chat/greeting

특정 카테고리의 그리팅 메시지만 조회합니다.

**요청 파라미터:**

| 필드 | 타입 | 필수 | 설명 |
|------|------|:----:|------|
| `birth_date` (또는 `birthDate`) | string | **필수** | 생년월일 (YYYY-MM-DD) |
| `birth_time` (또는 `birthTime`) | string | 선택 | 출생시간 (HH:MM) |
| `category` | string | **필수** | 운세 카테고리 |
| `char1_code` (또는 `char1Code`) | string | 선택 | 캐릭터1 코드 |
| `char2_code` (또는 `char2Code`) | string | 선택 | 캐릭터2 코드 |
| `eastern_fortune_data` | object | 선택 | 동양 운세 데이터 (직접 전달) |
| `western_fortune_data` | object | 선택 | 서양 운세 데이터 (직접 전달) |

> **Note**: Java 백엔드 호환을 위해 camelCase alias도 지원합니다.

---

### 4.5 캐릭터 목록 - GET /v1/fortune/chat/characters

사용 가능한 캐릭터 목록을 조회합니다.

**응답 예시:**
```json
{
  "main_characters": [
    {
      "code": "SOISEOL",
      "name": "소이설",
      "category": "eastern",
      "description": "따뜻하고 지혜로운 사주 해석가",
      "tone": "따뜻하고 격려하는 말투"
    },
    {
      "code": "STELLA",
      "name": "스텔라",
      "category": "western",
      "description": "쿨하고 신비로운 점성술사",
      "tone": "시적이고 신비로운 말투"
    }
  ],
  "sub_characters": [
    {
      "code": "CHEONGWOON",
      "name": "청운",
      "category": "eastern"
    },
    {
      "code": "HWARIN",
      "name": "화린",
      "category": "eastern"
    },
    {
      "code": "KYLE",
      "name": "카일",
      "category": "western"
    },
    {
      "code": "ELARIA",
      "name": "엘라리아",
      "category": "western"
    }
  ]
}
```

---

## 5. 운세 분석 API

### 5.1 동양 사주 분석 - POST /v1/fortune/eastern

**요청 파라미터:**

| 필드 | 타입 | 필수 | 설명 |
|------|------|:----:|------|
| `birth_date` | string | **필수** | 생년월일 (YYYY-MM-DD) |
| `birth_time` | string | 선택 | 출생시간 (HH:MM) - 시주 계산용 |
| `birth_place` | string | 선택 | 출생지역 |
| `gender` | string | **필수** | 성별 (`M` 또는 `F`) - 대운 계산용 |
| `name` | string | **필수** | 이름 |

**요청 예시:**
```json
{
  "birth_date": "1990-05-15",
  "birth_time": "14:30",
  "gender": "M",
  "name": "홍길동"
}
```

**응답 구조:**

| 필드 | 타입 | 설명 |
|------|------|------|
| `category` | string | `"eastern"` |
| `chart` | object | 사주 차트 (4기둥) |
| `chart.summary` | string | 차트 요약 (예: "갑자년 을축월 병인일 정묘시") |
| `chart.year/month/day/hour` | object | 각 기둥 정보 (gan, ji, element_code, ten_god_code) |
| `stats` | object | 통계 분석 (오행, 음양, 십신) |
| `summary` | string | 종합 해석 요약 |
| `message` | string | 상세 해석 메시지 |
| `ui_hints` | object | UI 렌더링 힌트 |
| `lucky` | object | 행운 정보 (색상, 숫자, 아이템, 방향, 장소) |

---

### 5.2 서양 점성술 분석 - POST /v1/fortune/western

**요청 파라미터:**

| 필드 | 타입 | 필수 | 설명 |
|------|------|:----:|------|
| `birth_date` | string | **필수** | 생년월일 (YYYY-MM-DD) |
| `birth_time` | string | 선택 | 출생시간 (HH:MM) - 상승궁 계산용 |
| `birth_place` | string | 선택 | 출생지역명 |
| `latitude` | float | 선택 | 위도 (-90 ~ 90) |
| `longitude` | float | 선택 | 경도 (-180 ~ 180) |
| `gender` | string | **필수** | 성별 (`M` 또는 `F`) |
| `name` | string | **필수** | 이름 |

**요청 예시:**
```json
{
  "birth_date": "1990-05-15",
  "birth_time": "14:30",
  "birth_place": "Seoul, Korea",
  "latitude": 37.5665,
  "longitude": 126.9780,
  "gender": "M",
  "name": "홍길동"
}
```

**응답 구조:**

| 필드 | 타입 | 설명 |
|------|------|------|
| `category` | string | `"western"` |
| `chart` | object | 출생 차트 |
| `chart.summary` | string | 차트 요약 (예: "태양 양자리, 달 전갈자리, 상승 사자자리") |
| `chart.sun/moon/rising` | object | 빅3 정보 (sign_code, house_number, summary) |
| `chart.planets` | array | 행성 배치 목록 |
| `chart.houses` | array | 12하우스 정보 |
| `stats` | object | 통계 분석 (원소, 모달리티, 애스펙트) |
| `summary` | string | 종합 해석 요약 |
| `message` | string | 상세 해석 메시지 |
| `ui_hints` | object | UI 렌더링 힌트 |
| `lucky` | object | 행운 정보 (요일, 색상, 숫자, 보석, 수호 행성) |

---

### 5.3 타로 리딩 - POST /v1/fortune/tarot/reading

3장 스프레드 타로 리딩을 수행합니다.

**요청 파라미터:**

| 필드 | 타입 | 필수 | 설명 |
|------|------|:----:|------|
| `question` | string | 선택 | 질문 (최대 500자) |
| `cards` | array | **필수** | 3장의 카드 (PAST, PRESENT, FUTURE) |

**카드 객체 구조:**

| 필드 | 타입 | 필수 | 설명 |
|------|------|:----:|------|
| `position` | string | **필수** | 위치: `PAST`, `PRESENT`, `FUTURE` |
| `card.major` | string | 조건부 | 메이저 아르카나 (예: `FOOL`, `LOVERS`) |
| `card.suit` | string | 조건부 | 마이너 수트 (예: `CUPS`, `WANDS`) |
| `card.rank` | string | 조건부 | 마이너 랭크 (예: `ACE`, `TWO`) |
| `card.orientation` | string | 선택 | 방향: `UPRIGHT`(정방향) / `REVERSED`(역방향) |

> **Note**: `major` 또는 (`suit` + `rank`) 중 하나만 지정해야 합니다.

**요청 예시:**
```json
{
  "question": "오늘 나의 연애운은 어떤가요?",
  "cards": [
    {
      "position": "PAST",
      "card": { "major": "FOOL", "orientation": "UPRIGHT" }
    },
    {
      "position": "PRESENT",
      "card": { "suit": "CUPS", "rank": "ACE", "orientation": "UPRIGHT" }
    },
    {
      "position": "FUTURE",
      "card": { "major": "LOVERS", "orientation": "UPRIGHT" }
    }
  ]
}
```

**응답 구조:**

| 필드 | 타입 | 설명 |
|------|------|------|
| `category` | string | `"tarot"` |
| `spread_type` | string | `"THREE_CARD"` |
| `question` | string | 질문 |
| `cards` | array | 카드별 해석 (position, card_name, keywords, interpretation) |
| `summary` | object | 종합 해석 (overall_theme, past_to_present, present_to_future, advice) |
| `lucky` | object | 행운 정보 (color, number, element, timing) |

---

### 5.4 화투점 리딩 - POST /v1/fortune/hwatu/reading

4장 화투점 리딩을 수행합니다.

**요청 파라미터:**

| 필드 | 타입 | 필수 | 설명 |
|------|------|:----:|------|
| `category` | string | **필수** | `"HWATU"` 고정 |
| `question` | string | **필수** | 질문 (최대 500자) |
| `cards` | array | **필수** | 4장의 카드 (position 1~4) |

**카드 객체 구조:**

| 필드 | 타입 | 필수 | 설명 |
|------|------|:----:|------|
| `position` | int | **필수** | 위치 (1~4) |
| `card_code` | int | **필수** | 카드 코드 (0~47) |
| `is_reversed` | bool | 선택 | 역방향 여부 (화투는 항상 `false`) |

**위치별 의미:**

| Position | 이름 | 설명 |
|----------|------|------|
| 1 | 본인/현재 | 질문자의 현재 상태, 심리, 주도권 |
| 2 | 상대/환경 | 상대방의 마음, 외부 상황, 보이지 않는 변수 |
| 3 | 과정/관계 | 두 요소가 맞물리며 흘러가는 방식 |
| 4 | 결과/조언 | 가까운 미래의 결론, 행동 지침 |

**요청 예시:**
```json
{
  "category": "HWATU",
  "question": "오늘 금전운이 궁금해요",
  "cards": [
    { "position": 1, "card_code": 7, "is_reversed": false },
    { "position": 2, "card_code": 18, "is_reversed": false },
    { "position": 3, "card_code": 32, "is_reversed": false },
    { "position": 4, "card_code": 41, "is_reversed": false }
  ]
}
```

**응답 구조:**

| 필드 | 타입 | 설명 |
|------|------|------|
| `meta` | object | 메타 정보 (model, generated_at) |
| `cards` | array | 카드별 해석 (4장) |
| `cards[].position_label` | string | 위치 레이블 (본인/현재, 상대/환경 등) |
| `cards[].card_name` | string | 카드 이름 (예: "칠월 싸리 피") |
| `cards[].card_type` | string | 카드 등급 (광, 열끗, 띠, 피) |
| `cards[].keywords` | array | 키워드 목록 |
| `cards[].interpretation` | string | 해석 |
| `summary` | object | 종합 해석 (overall_theme, flow_analysis, advice) |
| `lucky` | object | 행운 정보 (color, number, direction, timing) |

---

## 6. 레거시 API (Deprecated)

> **Warning**: 아래 API들은 더 이상 권장되지 않습니다. 신규 개발 시 위의 채팅 API를 사용하세요.

| 엔드포인트 | 상태 | 대체 API |
|-----------|------|----------|
| `POST /v1/fortune/chat` | Deprecated | `POST /v1/fortune/chat/turn/start` + `turn/continue` |
| `POST /v1/fortune/chat/stream` | Deprecated | 향후 스트리밍 지원 예정 |
| `POST /v1/fortune/chat/turn` | Deprecated | `turn/start` 및 `turn/continue`로 분리됨 |

---

## 7. 헬스체크 API

### 7.1 기본 헬스체크

```http
GET /health
```

**응답:**
```json
{
  "status": "healthy",
  "version": "0.4.2",
  "service": "yeji-ai"
}
```

### 7.2 Readiness Probe

```http
GET /health/ready
```

**응답:**
```json
{
  "status": "ready",
  "vllm_connected": true
}
```

### 7.3 Liveness Probe

```http
GET /health/live
```

**응답:**
```json
{
  "status": "alive"
}
```

### 7.4 모델 상태

```http
GET /model/status
```

**응답:**
```json
{
  "status": "ok",
  "model": "tellang/yeji-8b-rslora-v7-AWQ",
  "vllm_url": "http://localhost:8001",
  "ready": true
}
```

---

## 8. 에러 처리

### 에러 응답 형식

```json
{
  "detail": "에러 메시지"
}
```

### HTTP 상태 코드

| 코드 | 설명 |
|------|------|
| 200 | 성공 |
| 400 | 잘못된 요청 (입력값 오류) |
| 404 | 리소스 없음 (세션 만료 등) |
| 422 | 검증 실패 (Pydantic validation) |
| 500 | 서버 내부 오류 |

### 에러 예시

**400 Bad Request:**
```json
{
  "detail": "입력값 오류: birth_date 형식이 올바르지 않습니다. (YYYY-MM-DD)"
}
```

**404 Not Found:**
```json
{
  "detail": "세션을 찾을 수 없습니다: abc12345"
}
```

**422 Validation Error:**
```json
{
  "detail": [
    {
      "loc": ["body", "gender"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**500 Internal Server Error:**
```json
{
  "detail": "사주 분석 중 오류가 발생했습니다: vLLM 서버 연결 실패"
}
```

---

## 9. cURL 예시

### 9.1 세션 시작 (권장 플로우)

```bash
curl -X POST https://i14a605.p.ssafy.io/ai/api/v1/fortune/chat/turn/start \
  -H "Content-Type: application/json" \
  -d '{
    "birth_date": "1995-03-15",
    "birth_time": "09:30",
    "category": "LOVE"
  }'
```

### 9.2 대화 계속

```bash
curl -X POST https://i14a605.p.ssafy.io/ai/api/v1/fortune/chat/turn/continue \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "abc12345",
    "message": "연애운이 궁금해요"
  }'
```

### 9.3 동양 사주 분석

```bash
curl -X POST https://i14a605.p.ssafy.io/ai/api/v1/fortune/eastern \
  -H "Content-Type: application/json" \
  -d '{
    "birth_date": "1990-05-15",
    "birth_time": "14:30",
    "gender": "M",
    "name": "홍길동"
  }'
```

### 9.4 서양 점성술 분석

```bash
curl -X POST https://i14a605.p.ssafy.io/ai/api/v1/fortune/western \
  -H "Content-Type: application/json" \
  -d '{
    "birth_date": "1990-05-15",
    "birth_time": "14:30",
    "birth_place": "Seoul",
    "gender": "M",
    "name": "홍길동"
  }'
```

### 9.5 타로 리딩

```bash
curl -X POST https://i14a605.p.ssafy.io/ai/api/v1/fortune/tarot/reading \
  -H "Content-Type: application/json" \
  -d '{
    "question": "오늘의 운세는?",
    "cards": [
      {"position": "PAST", "card": {"major": "FOOL", "orientation": "UPRIGHT"}},
      {"position": "PRESENT", "card": {"major": "MAGICIAN", "orientation": "UPRIGHT"}},
      {"position": "FUTURE", "card": {"major": "LOVERS", "orientation": "UPRIGHT"}}
    ]
  }'
```

### 9.6 화투점 리딩

```bash
curl -X POST https://i14a605.p.ssafy.io/ai/api/v1/fortune/hwatu/reading \
  -H "Content-Type: application/json" \
  -d '{
    "category": "HWATU",
    "question": "오늘 금전운이 궁금해요",
    "cards": [
      {"position": 1, "card_code": 7, "is_reversed": false},
      {"position": 2, "card_code": 18, "is_reversed": false},
      {"position": 3, "card_code": 32, "is_reversed": false},
      {"position": 4, "card_code": 41, "is_reversed": false}
    ]
  }'
```

---

## 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|----------|
| 0.4.2 | 2026-02-05 | API 가이드 전면 개편: Quick Start 3-Step 플로우 추가, 신규 API (turn/start, turn/continue, tarot, hwatu) 문서화, 레거시 API Deprecated 표시, 필수 필드 정확히 반영 (gender, name 등) |
| 0.2.0 | 2026-01-31 | 서브 캐릭터 API 추가, 캐릭터 목록 업데이트, 티키타카 3턴 대화 예시 추가 |
| 0.1.0 | 2026-01-29 | 초기 버전 작성 |
