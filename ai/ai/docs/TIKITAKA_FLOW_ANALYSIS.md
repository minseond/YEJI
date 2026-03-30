# 운세 티키타카 흐름 분석

> 작성일: 2026-02-02
> 분석 대상: ai/main, ai/develop, ai/ultra4 브랜치

## 목차

1. [전체 흐름](#1-전체-흐름)
2. [API 엔드포인트](#2-api-엔드포인트)
3. [세션 및 ID 관리](#3-세션-및-id-관리)
4. [데이터 필드 양식](#4-데이터-필드-양식)
5. [브랜치별 차이점](#5-브랜치별-차이점)
6. [에러 처리](#6-에러-처리)

---

## 1. 전체 흐름

```
[클라이언트]
    │
    ├─(옵션1)─► POST /fortune/eastern + POST /fortune/western
    │              └─► eastern_fortune_data, western_fortune_data 획득
    │
    ├─(옵션2)─► 기존 fortune_id 재사용
    │
    └─(옵션3)─► birth_date만 전달 (greeting에서 자동 분석)

    │
    ▼
POST /chat/greeting
    ├─ Request: birth_date, category, [eastern_fortune_data], [western_fortune_data]
    └─ Response: session_id, messages[], eastern_fortune_id, western_fortune_id

    │
    ▼ (Turn 1~3 반복)
POST /chat/turn
    ├─ Request: session_id, birth_date, category, message
    └─ Response: session_id, turn, messages[], suggested_question, is_complete

    │
    ▼ (3턴 완료 후)
GET /chat/summary/{session_id}?type=eastern|western
    └─ Response: fortune (score, one_line, keywords, detail)
```

### 흐름 단계별 설명

| 단계 | 이름 | API | 설명 |
|------|------|-----|------|
| 0 | 동양 분석 | `POST /fortune/eastern` | 사주팔자 분석 |
| 0 | 서양 분석 | `POST /fortune/western` | 점성술 분석 |
| 1 | 그리팅 | `POST /chat/greeting` | 캐릭터 인사 + session_id 생성 |
| 2 | 턴 1 | `POST /chat/turn` | 첫 번째 대화 |
| 3 | 턴 2 | `POST /chat/turn` | 두 번째 대화 |
| 4 | 턴 3 | `POST /chat/turn` | 세 번째 대화 (is_complete=true) |
| 5 | 섬머리 | `GET /chat/summary/{session_id}` | 운세 요약 조회 |

---

## 2. API 엔드포인트

### 2.1 Chat API (fortune-turn)

| 엔드포인트 | 메서드 | 설명 |
|------------|--------|------|
| `/api/v1/fortune/chat/greeting` | POST | 카테고리별 그리팅 |
| `/api/v1/fortune/chat/turn` | POST | 턴 단위 티키타카 |
| `/api/v1/fortune/chat/complete` | POST | Non-Streaming 전체 응답 |

### 2.2 Summary API (fortune-summary)

| 엔드포인트 | 메서드 | 설명 |
|------------|--------|------|
| `/api/v1/fortune/chat/summary/{session_id}` | GET | 운세 요약 조회 |

### 2.3 Session API (fortune-session)

| 엔드포인트 | 메서드 | 설명 |
|------------|--------|------|
| `/api/v1/fortune/chat/session` | POST | 세션 생성 |
| `/api/v1/fortune/chat/session/{session_id}` | GET | 세션 조회 |
| `/api/v1/fortune/chat/session/{session_id}` | DELETE | 세션 삭제 |

### 2.4 Utility API (fortune-util)

| 엔드포인트 | 메서드 | 설명 |
|------------|--------|------|
| `/api/v1/fortune/chat/characters` | GET | 캐릭터 정보 조회 |
| `/api/v1/fortune/chat/sub-characters` | GET | 서브 캐릭터 목록 |
| `/api/v1/fortune/chat/test-character` | POST | 서브 캐릭터 테스트 |

### 2.5 Tikitaka SSE API (V2)

| 엔드포인트 | 메서드 | 설명 |
|------------|--------|------|
| `/api/v1/fortune/tikitaka/stream` | POST | SSE 스트리밍 |
| `/api/v1/fortune/tikitaka/session/{session_id}` | GET | V2 세션 상태 조회 |

---

## 3. 세션 및 ID 관리

### 3.1 Session 관리

| 항목 | 위치 | 설명 |
|------|------|------|
| `session_id` | `tikitaka_service.py` | UUID 8자리 (`uuid.uuid4()[:8]`) |
| 저장소 | `_sessions: dict` | 메모리 기반 딕셔너리 |
| 생성 | `create_session()` | 명시적 생성 또는 자동 생성 |
| 삭제 | `delete_session()` | 세션 ID로 삭제 |

### 3.2 Fortune ID 관리

| ID 종류 | 생성 위치 | 저장 위치 | 용도 |
|---------|----------|----------|------|
| `eastern_fortune_id` | `get_or_create_fortunes()` | `TikitakaSession` | 동양 운세 참조 |
| `western_fortune_id` | `get_or_create_fortunes()` | `TikitakaSession` | 서양 운세 참조 |
| Fortune 저장소 | `_fortune_store` | 메모리 (dict) | 운세 결과 재사용 |

> **참고**: `_fortune_store`는 인메모리 딕셔너리입니다. Redis 설정은 config에 존재하지만, 실제 fortune 저장은 메모리 기반입니다.

### 3.3 Fortune Source (운세 출처)

| 값 | 의미 | 발생 조건 |
|----|------|----------|
| `"provided"` | 직접 전달 | `eastern_fortune_data` 객체 전달 시 |
| `"cached"` | 캐시 조회 | `eastern_fortune_id`로 재사용 시 |
| `"created"` | 실시간 생성 | ID/데이터 없이 birth_date만 전달 시 |

### 3.4 TikitakaSession 클래스

```python
class TikitakaSession:
    session_id: str                    # UUID 8자리
    turn: int                          # 현재 턴 (0부터 시작)
    messages: list[ChatMessage]        # 대화 히스토리
    user_info: dict                    # {"birth_date": "...", "birth_time": "..."}
    eastern_result: EasternFortuneResponse | None
    western_result: WesternFortuneDataV2 | None
    last_topic: str | None             # 마지막 토론 주제
    created_at: datetime

    # Fortune ID
    eastern_fortune_id: str | None
    western_fortune_id: str | None
    fortune_source: str | None         # "created" | "cached" | "provided"

    # 카테고리
    category: FortuneCategory

    # 맥락 유지 (v2)
    debate_history: list[dict]         # 토론 이력 (최대 10개)
    user_preferences: dict             # 사용자 선호 캐릭터
    conversation_themes: list[str]     # 대화 주제들 (최대 10개)
```

---

## 4. 데이터 필드 양식

### 4.1 CategoryGreetingRequest (그리팅 요청)

| 필드명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| `birth_date` | `str` | **필수** | `YYYY-MM-DD` 형식 |
| `birth_time` | `str \| None` | 선택 | `HH:MM` 형식 |
| `birth_place` | `str \| None` | 선택 | 출생장소 |
| `latitude` | `float \| None` | 선택 | 위도 |
| `longitude` | `float \| None` | 선택 | 경도 |
| `category` | `FortuneCategory` | **필수** | GENERAL, LOVE, MONEY, CAREER, HEALTH, STUDY |
| `char1_code` | `str` | 선택 | 캐릭터1 (기본: SOISEOL) |
| `char2_code` | `str` | 선택 | 캐릭터2 (기본: STELLA) |
| `eastern_fortune_id` | `str \| None` | 선택 | 기존 동양 운세 ID |
| `western_fortune_id` | `str \| None` | 선택 | 기존 서양 운세 ID |
| `eastern_fortune_data` | `dict \| None` | 선택 | 동양 분석 결과 객체 |
| `western_fortune_data` | `dict \| None` | 선택 | 서양 분석 결과 객체 |

### 4.2 TurnRequest (턴 요청)

| 필드명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| `session_id` | `str \| None` | 조건부 | Turn 1+에서 필수 |
| `birth_date` | `str` | **필수** | `YYYY-MM-DD` 형식 |
| `birth_time` | `str \| None` | 선택 | `HH:MM` 형식 |
| `category` | `FortuneCategory` | **필수** | 운세 카테고리 |
| `message` | `str \| None` | 조건부 | 사용자 메시지 |
| `char1_code` | `str` | 선택 | 캐릭터1 |
| `char2_code` | `str` | 선택 | 캐릭터2 |

### 4.3 ChatMessage (응답 메시지)

| 필드명 | 타입 | 설명 |
|--------|------|------|
| `character` | `CharacterCode` | SOISEOL, STELLA, CHEONGWOON, HWARIN, KYLE, ELARIA |
| `type` | `MessageType` | GREETING, INFO_REQUEST, INTERPRETATION, DEBATE, CONSENSUS, QUESTION, CHOICE |
| `content` | `str` | 메시지 내용 |
| `timestamp` | `datetime` | 타임스탬프 |

### 4.4 FortuneCategory (Enum)

```python
class FortuneCategory(str, Enum):
    GENERAL = "GENERAL"   # 종합운
    LOVE = "LOVE"         # 연애운
    MONEY = "MONEY"       # 금전운
    CAREER = "CAREER"     # 직장운
    HEALTH = "HEALTH"     # 건강운
    STUDY = "STUDY"       # 학업운
```

### 4.5 CharacterCode (Enum)

```python
class CharacterCode(str, Enum):
    SOISEOL = "SOISEOL"       # 소이설 (동양, 메인)
    STELLA = "STELLA"         # 스텔라 (서양, 메인)
    CHEONGWOON = "CHEONGWOON" # 청운 (동양, 서브)
    HWARIN = "HWARIN"         # 화린 (동양, 서브)
    KYLE = "KYLE"             # 카일 (서양, 서브)
    ELARIA = "ELARIA"         # 엘라리아 (서양, 서브)
```

---

## 5. 브랜치별 차이점

### 5.1 현재 브랜치 상태

| 브랜치 | 상태 | 특징 |
|--------|------|------|
| `ai/main` | Production | 기본 티키타카 시스템 |
| `ai/develop` | Development | GPT-5-mini 폴백 + Redis |
| `ai/ultra4` | Experimental | GPT-5-mini 기본 모드 |

### 5.2 기능 비교

| 기능 | ai/main | ai/develop | ai/ultra4 |
|------|---------|------------|-----------|
| LLM Provider | yeji-8b | yeji-8b + GPT폴백 | GPT-5-mini 기본 |
| Redis 캐싱 | ❌ | ✅ | ✅ |
| 멀티 버블 파서 | ❌ | ✅ | ✅ |
| 노이즈 필터 | 기본 | aggressive | aggressive |
| Summary 분리 | ❌ | ✅ | ✅ |
| 배포 포트 | 8000 | 8002 | 8003 |

### 5.3 주요 커밋 차이 (develop vs main)

| 커밋 | 변경 내용 |
|------|----------|
| `/chat/turn` session 파라미터 | 대화 히스토리 전달 지원 |
| GPT-5-mini 멀티 버블 파서 | LLM 어댑터 구현 |
| 노이즈 필터 강화 | aggressive 모드 적용 |
| Summary 분리 | greeting에서 summary 생성 로직 제거 |
| Redis 의존성 | uv.lock에 redis 추가 |

---

## 6. 에러 처리

### 6.1 필드 검증 에러

| 상황 | HTTP 코드 | 설명 |
|------|----------|------|
| 필수 필드 누락 | `422` | birth_date, category 누락 시 |
| 패턴 불일치 | `422` | YYYY/MM/DD 형식 사용 시 |
| 잘못된 Enum | `422` | category: "INVALID" 등 |
| 잘못된 타입 | `422` | session_id: 123 (숫자) |
| **존재하지 않는 필드** | **무시됨** | Pydantic v2 기본값 (unknown fields 무시) |

### 6.2 세션 관련 에러

| 상황 | HTTP 코드 | 설명 |
|------|----------|------|
| 세션 없음 | `404` | 존재하지 않는 session_id |
| 세션 만료 | `410` | 오래된 세션 (메모리에서 삭제됨) |

### 6.3 LLM 관련 에러

| 상황 | HTTP 코드 | 설명 |
|------|----------|------|
| LLM 연결 실패 | `503` | vLLM 서버 다운 |
| LLM 타임아웃 | `504` | 응답 지연 (120초 초과) |
| 폴백 응답 | `200` | LLM 실패 시 기본 응답 반환 |

---

## 7. 핵심 파일 위치

| 역할 | 경로 |
|------|------|
| Chat API | `src/yeji_ai/api/v1/fortune/chat.py` |
| Tikitaka SSE API | `src/yeji_ai/api/v1/fortune/tikitaka.py` |
| 티키타카 서비스 | `src/yeji_ai/services/tikitaka_service.py` |
| Chat 모델 | `src/yeji_ai/models/fortune/chat.py` |
| Turn 스키마 | `src/yeji_ai/models/fortune/turn.py` |
| 동양 운세 모델 | `src/yeji_ai/models/fortune/eastern.py` |
| 서양 운세 모델 | `src/yeji_ai/models/fortune/western.py` |
