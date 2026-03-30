# 티키타카 세션 라이프사이클 설계

> **문서 버전**: v1.0
> **작성일**: 2026-01-30
> **상태**: 설계 (Design)
> **담당팀**: SSAFY YEJI AI팀

---

## 목차

1. [개요](#1-개요)
2. [세션 종료 조건 정의](#2-세션-종료-조건-정의)
3. [세션 상태 전이 다이어그램](#3-세션-상태-전이-다이어그램)
4. [요약 페이즈 진입 조건](#4-요약-페이즈-진입-조건)
5. [Redis 세션 관리](#5-redis-세션-관리)
6. [프론트엔드 알림 이벤트](#6-프론트엔드-알림-이벤트)
7. [타임아웃 및 정리 정책](#7-타임아웃-및-정리-정책)
8. [에러 처리 및 복구](#8-에러-처리-및-복구)
9. [구현 가이드](#9-구현-가이드)
10. [참조 문서](#10-참조-문서)

---

## 1. 개요

### 1.1 목적

티키타카 세션의 시작부터 종료까지의 전체 라이프사이클을 정의하고, 세션 종료 조건 및 정리 절차를 명확히 합니다.

### 1.2 범위

- 세션 종료 조건 (정상/비정상)
- 요약 페이즈 (SUMMARY) 진입 로직
- Redis 세션 데이터 정리
- 프론트엔드 알림 이벤트 설계

### 1.3 현재 시스템 분석

**기존 세션 관리 (tikitaka_service.py)**:
```
TikitakaSession
├── session_id: str           # 세션 식별자
├── turn: int                 # 현재 턴 번호
├── messages: list            # 대화 메시지 목록
├── user_info: dict           # 사용자 정보
├── eastern_result: Response  # 동양 분석 결과
├── western_result: Response  # 서양 분석 결과
├── last_topic: str | None    # 마지막 주제
└── created_at: datetime      # 생성 시간
```

**기존 세션 저장소**: 인메모리 딕셔너리 (`_sessions: dict`)

**문제점**:
- 세션 종료 조건 미정의
- 요약 페이즈 미구현
- 세션 만료/정리 로직 부재
- 서버 재시작 시 세션 유실

### 1.4 V2 스키마 연동

티키타카 스키마 V2 (tikitaka-schema-v2.md)에서 정의된 세션 상태:

```typescript
interface SessionState {
  session_id: string;
  current_turn: number;     // 현재 턴 (0부터 시작)
  max_turns: number;        // 최대 턴 (기본: 10)
  bonus_turns: number;      // 보너스 턴 (프리미엄: 3, 일반: 0)
  remaining_turns: number;  // 남은 턴
  is_premium: boolean;
  phase: PhaseCode;         // GREETING, DIALOGUE, QUESTION, SUMMARY, FAREWELL
  has_eastern_result: boolean;
  has_western_result: boolean;
}
```

---

## 2. 세션 종료 조건 정의

### 2.1 종료 조건 유형

| 유형 | 조건 코드 | 설명 | 우선순위 |
|------|----------|------|----------|
| **정상 종료** | `TURNS_EXHAUSTED` | 모든 턴 소진 (max_turns + bonus_turns) | P1 |
| **정상 종료** | `USER_EXPLICIT_END` | 사용자 명시적 종료 요청 | P1 |
| **정상 종료** | `NATURAL_CONCLUSION` | 대화가 자연스럽게 마무리됨 | P2 |
| **비정상 종료** | `SESSION_TIMEOUT` | 세션 비활성 타임아웃 | P3 |
| **비정상 종료** | `USER_DISCONNECT` | 클라이언트 연결 끊김 | P3 |
| **비정상 종료** | `SYSTEM_ERROR` | 시스템 오류로 인한 강제 종료 | P4 |
| **비정상 종료** | `ADMIN_FORCE_END` | 관리자 강제 종료 | P5 |

### 2.2 종료 조건 상세

#### 2.2.1 턴 소진 (TURNS_EXHAUSTED)

**트리거 조건**:
```
remaining_turns == 0
```

**계산 로직**:
```
remaining_turns = max_turns + bonus_turns - current_turn

- 일반 사용자: 10 + 0 = 10턴
- 프리미엄 사용자: 10 + 3 = 13턴
```

**동작 흐름**:
1. 마지막 턴 응답 완료
2. `remaining_turns` 확인
3. 0이면 자동으로 SUMMARY 페이즈 진입
4. 요약 메시지 생성 후 FAREWELL 페이즈

#### 2.2.2 사용자 명시적 종료 (USER_EXPLICIT_END)

**트리거 조건**:
- 사용자가 "종료", "끝", "그만" 등 종료 의도 표현
- UI의 "대화 종료" 버튼 클릭
- 특수 명령어 입력 (예: `/end`, `/quit`)

**종료 키워드 목록**:
```python
END_KEYWORDS = [
    "종료", "끝", "그만", "나갈게", "끝내자",
    "bye", "end", "quit", "exit",
    "/end", "/quit", "/exit",
]
```

**동작 흐름**:
1. 사용자 메시지에서 종료 키워드 감지
2. 확인 메시지 전송 (선택적)
3. SUMMARY 페이즈 진입
4. 요약 메시지 생성 후 FAREWELL 페이즈

#### 2.2.3 자연스러운 마무리 (NATURAL_CONCLUSION)

**트리거 조건**:
- LLM이 대화 완료 판단 (FAREWELL 타입 메시지 생성)
- 사용자가 더 이상 질문하지 않음 (연속 2회 이상 단답)
- 모든 주제에 대한 해석 완료

**판단 기준**:
```python
def is_natural_conclusion(session: TikitakaSession) -> bool:
    """자연스러운 마무리 여부 판단"""

    # 최근 메시지가 FAREWELL 타입인 경우
    if session.messages[-1].type == MessageType.FAREWELL:
        return True

    # 사용자 연속 단답 (5자 이하) 2회 이상
    user_messages = [m for m in session.messages if m.character == "USER"]
    recent_user = user_messages[-2:] if len(user_messages) >= 2 else []
    if all(len(m.content) <= 5 for m in recent_user):
        return True

    return False
```

#### 2.2.4 세션 타임아웃 (SESSION_TIMEOUT)

**타임아웃 값**:
| 구분 | 비활성 타임아웃 | 절대 타임아웃 |
|------|---------------|-------------|
| 일반 사용자 | 15분 | 1시간 |
| 프리미엄 사용자 | 30분 | 2시간 |

**비활성 타임아웃**: 마지막 활동 이후 경과 시간
**절대 타임아웃**: 세션 생성 이후 총 경과 시간

**동작 흐름**:
1. 타임아웃 감지 (백그라운드 태스크 또는 다음 요청 시)
2. 세션 상태를 `EXPIRED`로 변경
3. 간소화된 SUMMARY 메시지 생성 (선택적)
4. 세션 정리

#### 2.2.5 사용자 연결 끊김 (USER_DISCONNECT)

**트리거 조건**:
- SSE 연결 끊김 (클라이언트측 종료)
- WebSocket 연결 종료 (향후 구현 시)

**동작 흐름**:
1. 연결 끊김 감지
2. 일정 시간 대기 (재연결 유예: 30초)
3. 재연결 없으면 세션 일시 정지 (PAUSED)
4. 비활성 타임아웃 적용

### 2.3 종료 조건 열거형

```python
class TerminationReason(str, Enum):
    """세션 종료 사유"""

    # 정상 종료
    TURNS_EXHAUSTED = "turns_exhausted"     # 턴 소진
    USER_EXPLICIT_END = "user_explicit_end" # 사용자 종료 요청
    NATURAL_CONCLUSION = "natural_conclusion" # 자연스러운 마무리

    # 비정상 종료
    SESSION_TIMEOUT = "session_timeout"     # 세션 타임아웃
    USER_DISCONNECT = "user_disconnect"     # 사용자 연결 끊김
    SYSTEM_ERROR = "system_error"           # 시스템 오류
    ADMIN_FORCE_END = "admin_force_end"     # 관리자 강제 종료
```

---

## 3. 세션 상태 전이 다이어그램

### 3.1 세션 상태 정의

```python
class SessionStatus(str, Enum):
    """세션 상태"""

    CREATED = "created"         # 생성됨 (초기화 중)
    ACTIVE = "active"           # 활성 (대화 진행 중)
    PAUSED = "paused"           # 일시 정지 (재연결 대기)
    SUMMARIZING = "summarizing" # 요약 중
    COMPLETED = "completed"     # 정상 완료
    EXPIRED = "expired"         # 만료됨 (타임아웃)
    TERMINATED = "terminated"   # 강제 종료됨
```

### 3.2 상태 전이 다이어그램

```
                          ┌──────────────────────────────────────────────────────┐
                          │                     [시스템 오류]                     │
                          │                   SYSTEM_ERROR                       │
                          ▼                                                      │
┌─────────┐    ┌─────────┐    ┌────────────┐    ┌─────────────┐    ┌──────────┐ │
│ CREATED │───▶│ ACTIVE  │───▶│ SUMMARIZING│───▶│  COMPLETED  │    │TERMINATED│◀┘
└─────────┘    └─────────┘    └────────────┘    └─────────────┘    └──────────┘
     │              │  ▲              │
     │              │  │              │
     │              │  └──────────────┘
     │              │       [요약 실패시
     │              │        재시도]
     │              │
     │              │    ┌─────────┐
     │              └───▶│ PAUSED  │
     │                   └─────────┘
     │                        │
     │                        │ [타임아웃]
     │                        ▼
     │                   ┌─────────┐
     └──────────────────▶│ EXPIRED │
         [초기화 실패]    └─────────┘
```

### 3.3 상태 전이 규칙

| 현재 상태 | 이벤트 | 다음 상태 | 설명 |
|----------|--------|----------|------|
| CREATED | 초기화 완료 | ACTIVE | 분석 결과 로드, 인사 메시지 전송 |
| CREATED | 초기화 실패 | EXPIRED | 분석 실패, 타임아웃 |
| ACTIVE | 턴 진행 | ACTIVE | 대화 계속 |
| ACTIVE | 종료 조건 충족 | SUMMARIZING | 요약 페이즈 진입 |
| ACTIVE | 연결 끊김 | PAUSED | 재연결 대기 |
| ACTIVE | 시스템 오류 | TERMINATED | 강제 종료 |
| PAUSED | 재연결 | ACTIVE | 대화 재개 |
| PAUSED | 타임아웃 | EXPIRED | 세션 만료 |
| SUMMARIZING | 요약 완료 | COMPLETED | 정상 종료 |
| SUMMARIZING | 요약 실패 | SUMMARIZING | 재시도 (최대 2회) |
| SUMMARIZING | 재시도 초과 | TERMINATED | 강제 종료 |

### 3.4 페이즈(Phase)와 상태(Status)의 관계

페이즈(Phase)는 대화 단계, 상태(Status)는 세션 상태입니다.

| Phase | 허용되는 Status |
|-------|----------------|
| GREETING | CREATED, ACTIVE |
| DIALOGUE | ACTIVE |
| QUESTION | ACTIVE, PAUSED |
| SUMMARY | SUMMARIZING |
| FAREWELL | COMPLETED |

---

## 4. 요약 페이즈 진입 조건

### 4.1 진입 조건 체크 로직

```python
def should_enter_summary_phase(session: SessionState) -> tuple[bool, TerminationReason | None]:
    """요약 페이즈 진입 여부 판단

    Returns:
        (진입 여부, 종료 사유)
    """
    # 1. 턴 소진 확인
    if session.remaining_turns <= 0:
        return True, TerminationReason.TURNS_EXHAUSTED

    # 2. 사용자 명시적 종료 요청 확인
    if _has_user_end_request(session):
        return True, TerminationReason.USER_EXPLICIT_END

    # 3. 자연스러운 마무리 확인
    if _is_natural_conclusion(session):
        return True, TerminationReason.NATURAL_CONCLUSION

    return False, None
```

### 4.2 요약 페이즈 처리 흐름

```
┌───────────────────────────────────────────────────────────────────┐
│                      요약 페이즈 진입                              │
└───────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────┐
│ 1. 세션 상태 변경: ACTIVE → SUMMARIZING                           │
│    phase: DIALOGUE → SUMMARY                                       │
└───────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────┐
│ 2. phase_change 이벤트 전송                                        │
│    event: phase_change                                             │
│    data: {"phase": "SUMMARY", "reason": "turns_exhausted"}         │
└───────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────┐
│ 3. 요약 메시지 생성 (LLM)                                          │
│    - 소이설 요약: 동양 관점 핵심 포인트                             │
│    - 스텔라 요약: 서양 관점 핵심 포인트                             │
│    - 공통 합의점 정리                                              │
└───────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────┐
│ 4. 요약 버블 스트리밍                                              │
│    bubble_start → bubble_chunk* → bubble_end                       │
│    (type: SUMMARY)                                                 │
└───────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────┐
│ 5. 마무리 페이즈 전환                                              │
│    phase: SUMMARY → FAREWELL                                       │
│    status: SUMMARIZING → COMPLETED                                 │
└───────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────┐
│ 6. 마무리 메시지 전송                                              │
│    - 소이설: "오늘 대화 즐거웠어요~"                               │
│    - 스텔라: "...또 와."                                          │
└───────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────┐
│ 7. 세션 종료 이벤트 전송                                           │
│    event: session_end                                              │
│    data: {...}                                                     │
└───────────────────────────────────────────────────────────────────┘
```

### 4.3 요약 메시지 생성 구조

```python
@dataclass
class SummaryContent:
    """요약 콘텐츠"""

    # 동양 요약
    eastern_summary: str           # 소이설의 핵심 해석
    eastern_keywords: list[str]    # 핵심 키워드 (최대 5개)

    # 서양 요약
    western_summary: str           # 스텔라의 핵심 해석
    western_keywords: list[str]    # 핵심 키워드 (최대 5개)

    # 합의점
    consensus_points: list[str]    # 동서양 공통 해석 (1-3개)

    # 조언
    final_advice: str              # 최종 조언 메시지

    # 행운 정보
    lucky_info: dict[str, str]     # {"color": "...", "number": "...", "direction": "..."}
```

### 4.4 요약 생성 프롬프트 구조

```xml
<tikitaka_summary>
  <context>
    {대화 히스토리 요약}
  </context>

  <eastern_analysis>
    {동양 분석 결과 요약}
  </eastern_analysis>

  <western_analysis>
    {서양 분석 결과 요약}
  </western_analysis>

  <instruction>
    위 대화와 분석을 바탕으로 최종 요약을 작성하세요:
    1. 소이설 요약 (2-3문장, 따뜻한 어투)
    2. 스텔라 요약 (2-3문장, 쿨한 어투)
    3. 공통점 (1-3개)
    4. 최종 조언 (1-2문장)
  </instruction>
</tikitaka_summary>
```

---

## 5. Redis 세션 관리

### 5.1 Redis 키 구조

```
# 세션 데이터
tikitaka:session:{session_id}          # 메인 세션 데이터 (Hash)
tikitaka:session:{session_id}:bubbles  # 버블 목록 (List)
tikitaka:session:{session_id}:results  # 분석 결과 캐시 (Hash)

# 인덱스
tikitaka:user:{user_id}:sessions       # 사용자별 세션 목록 (Set)
tikitaka:active_sessions               # 활성 세션 목록 (Sorted Set, score=updated_at)

# 만료 대기 세션
tikitaka:expiring_sessions             # 만료 예정 세션 (Sorted Set, score=expire_at)
```

### 5.2 세션 데이터 스키마 (Redis Hash)

```json
{
  "session_id": "abc123",
  "user_id": "12345",
  "status": "active",
  "phase": "DIALOGUE",

  "turn": {
    "current": 5,
    "max": 10,
    "bonus": 3,
    "remaining": 8
  },

  "is_premium": true,

  "results": {
    "has_eastern": true,
    "has_western": true
  },

  "timestamps": {
    "created_at": "2026-01-30T15:30:00Z",
    "updated_at": "2026-01-30T15:35:00Z",
    "last_activity_at": "2026-01-30T15:35:00Z"
  },

  "termination": {
    "reason": null,
    "terminated_at": null
  },

  "ttl": 3600
}
```

### 5.3 세션 정리 절차

#### 5.3.1 정상 종료 시 정리

```python
async def cleanup_session_on_complete(session_id: str) -> None:
    """정상 종료 시 세션 정리"""

    # 1. 세션 데이터 아카이브 (선택적)
    await archive_session_data(session_id)

    # 2. 세션 상태 업데이트
    await redis.hset(
        f"tikitaka:session:{session_id}",
        mapping={
            "status": "completed",
            "termination.reason": reason.value,
            "termination.terminated_at": datetime.utcnow().isoformat(),
        }
    )

    # 3. 활성 세션 인덱스에서 제거
    await redis.zrem("tikitaka:active_sessions", session_id)

    # 4. 세션 데이터에 짧은 TTL 설정 (데이터 보존 기간)
    await redis.expire(f"tikitaka:session:{session_id}", 86400)  # 24시간
    await redis.expire(f"tikitaka:session:{session_id}:bubbles", 86400)
    await redis.expire(f"tikitaka:session:{session_id}:results", 86400)

    # 5. 완료 로그 기록
    logger.info(
        "session_completed",
        session_id=session_id,
        reason=reason.value,
        total_turns=session.current_turn,
    )
```

#### 5.3.2 타임아웃 시 정리 (백그라운드 태스크)

```python
async def cleanup_expired_sessions() -> int:
    """만료된 세션 정리 (백그라운드 태스크)

    Returns:
        정리된 세션 수
    """
    now = datetime.utcnow().timestamp()

    # 1. 만료된 세션 ID 조회
    expired_sessions = await redis.zrangebyscore(
        "tikitaka:expiring_sessions",
        "-inf",
        now,
        limit=(0, 100),  # 배치 처리
    )

    cleaned_count = 0
    for session_id in expired_sessions:
        try:
            # 2. 세션 상태 확인 (이미 정리되었는지)
            status = await redis.hget(f"tikitaka:session:{session_id}", "status")
            if status in ("completed", "expired", "terminated"):
                continue

            # 3. 간소화된 요약 생성 (선택적)
            await generate_timeout_summary(session_id)

            # 4. 세션 상태 업데이트
            await redis.hset(
                f"tikitaka:session:{session_id}",
                mapping={
                    "status": "expired",
                    "termination.reason": "session_timeout",
                    "termination.terminated_at": datetime.utcnow().isoformat(),
                }
            )

            # 5. 인덱스에서 제거
            await redis.zrem("tikitaka:active_sessions", session_id)
            await redis.zrem("tikitaka:expiring_sessions", session_id)

            # 6. TTL 설정
            await redis.expire(f"tikitaka:session:{session_id}", 3600)  # 1시간

            cleaned_count += 1

            logger.info("session_expired", session_id=session_id)

        except Exception as e:
            logger.error("session_cleanup_error", session_id=session_id, error=str(e))

    return cleaned_count
```

### 5.4 세션 TTL 정책

| 세션 상태 | TTL | 설명 |
|----------|-----|------|
| ACTIVE | 없음 (만료 모니터링) | 비활성 타임아웃으로 관리 |
| PAUSED | 30분 | 재연결 유예 기간 |
| COMPLETED | 24시간 | 데이터 보존 (통계/분석용) |
| EXPIRED | 1시간 | 빠른 정리 |
| TERMINATED | 1시간 | 빠른 정리 |

### 5.5 세션 데이터 아카이브

장기 보존이 필요한 세션 데이터는 별도 저장소로 이동:

```python
async def archive_session_data(session_id: str) -> None:
    """세션 데이터 아카이브 (장기 보존)"""

    # 1. 세션 데이터 조회
    session_data = await redis.hgetall(f"tikitaka:session:{session_id}")
    bubbles = await redis.lrange(f"tikitaka:session:{session_id}:bubbles", 0, -1)

    # 2. 아카이브 데이터 구성
    archive = {
        "session_id": session_id,
        "session_data": session_data,
        "bubbles": [json.loads(b) for b in bubbles],
        "archived_at": datetime.utcnow().isoformat(),
    }

    # 3. 저장소로 이동 (예: S3, MongoDB, PostgreSQL)
    await archive_storage.save(
        key=f"tikitaka/{session_id[:2]}/{session_id}.json",
        data=json.dumps(archive, ensure_ascii=False),
    )

    logger.info("session_archived", session_id=session_id)
```

---

## 6. 프론트엔드 알림 이벤트

### 6.1 세션 라이프사이클 SSE 이벤트

| 이벤트 | 발생 시점 | 용도 |
|--------|----------|------|
| `session_start` | 세션 생성 완료 | 세션 정보 전달 |
| `phase_change` | 페이즈 전환 시 | UI 상태 변경 |
| `turn_update` | 턴 진행 시 | 남은 턴 표시 갱신 |
| `warning_low_turns` | 남은 턴 3 이하 | 종료 임박 알림 |
| `summary_start` | 요약 페이즈 진입 | 요약 UI 표시 |
| `session_end` | 세션 종료 | 종료 UI 표시 |
| `session_expired` | 타임아웃 종료 | 만료 알림 |
| `reconnect_available` | 재연결 가능 | 재연결 버튼 표시 |

### 6.2 이벤트 페이로드 상세

#### 6.2.1 session_start

```json
{
  "event": "session_start",
  "data": {
    "session_id": "abc123",
    "is_premium": true,
    "max_turns": 10,
    "bonus_turns": 3,
    "total_turns": 13,
    "characters": [
      {"code": "SOISEOL", "name": "소이설", "specialty": "eastern"},
      {"code": "STELLA", "name": "스텔라", "specialty": "western"}
    ]
  }
}
```

#### 6.2.2 phase_change

```json
{
  "event": "phase_change",
  "data": {
    "from_phase": "DIALOGUE",
    "to_phase": "SUMMARY",
    "reason": "turns_exhausted",
    "remaining_turns": 0,
    "ui_hint": {
      "show_input": false,
      "show_end_button": false,
      "animation": "summary_transition"
    }
  }
}
```

#### 6.2.3 turn_update

```json
{
  "event": "turn_update",
  "data": {
    "current_turn": 8,
    "remaining_turns": 5,
    "is_last_turn": false,
    "is_bonus_turn": false
  }
}
```

#### 6.2.4 warning_low_turns

```json
{
  "event": "warning_low_turns",
  "data": {
    "remaining_turns": 3,
    "message": "대화가 곧 마무리됩니다. 궁금한 점이 있다면 지금 물어보세요!",
    "ui_hint": {
      "highlight_turns": true,
      "show_warning_badge": true
    }
  }
}
```

#### 6.2.5 summary_start

```json
{
  "event": "summary_start",
  "data": {
    "reason": "turns_exhausted",
    "message": "대화를 정리하고 있어요...",
    "ui_hint": {
      "show_loading": true,
      "disable_input": true,
      "estimated_time_seconds": 10
    }
  }
}
```

#### 6.2.6 session_end

```json
{
  "event": "session_end",
  "data": {
    "session_id": "abc123",
    "reason": "turns_exhausted",
    "status": "completed",
    "stats": {
      "total_turns": 13,
      "total_bubbles": 42,
      "duration_seconds": 1800,
      "topics_discussed": ["연애운", "직장운", "금전운"]
    },
    "summary": {
      "eastern_keywords": ["병화", "목기운", "리더십"],
      "western_keywords": ["양자리", "화성", "추진력"],
      "consensus": "둘 다 리더십과 추진력이 강점"
    },
    "ui_hint": {
      "show_restart_button": true,
      "show_share_button": true,
      "show_rating_modal": true
    }
  }
}
```

#### 6.2.7 session_expired

```json
{
  "event": "session_expired",
  "data": {
    "session_id": "abc123",
    "reason": "session_timeout",
    "message": "오랜 시간 활동이 없어 세션이 종료되었습니다.",
    "last_activity_at": "2026-01-30T15:00:00Z",
    "ui_hint": {
      "show_restart_button": true,
      "show_reconnect_button": false
    }
  }
}
```

#### 6.2.8 reconnect_available

```json
{
  "event": "reconnect_available",
  "data": {
    "session_id": "abc123",
    "remaining_time_seconds": 120,
    "message": "연결이 끊겼습니다. 2분 내에 재연결하면 대화를 이어갈 수 있습니다.",
    "ui_hint": {
      "show_reconnect_button": true,
      "countdown_timer": true
    }
  }
}
```

### 6.3 SSE 이벤트 스트림 예시 (전체 라이프사이클)

```
# 1. 세션 시작
event: session_start
data: {"session_id": "abc123", "is_premium": false, "max_turns": 10, ...}

# 2. 인사 페이즈
event: phase_change
data: {"to_phase": "GREETING", ...}

event: bubble_start
data: {"bubble_id": "b_001", "character": "SOISEOL", ...}

event: bubble_chunk
data: {"bubble_id": "b_001", "content": "안녕하세요~", ...}

event: bubble_end
data: {"bubble_id": "b_001", ...}

# ... 대화 진행 ...

# 3. 턴 업데이트
event: turn_update
data: {"current_turn": 7, "remaining_turns": 3, ...}

# 4. 낮은 턴 경고
event: warning_low_turns
data: {"remaining_turns": 3, "message": "...", ...}

# ... 계속 진행 ...

# 5. 마지막 턴
event: turn_update
data: {"current_turn": 10, "remaining_turns": 0, "is_last_turn": true, ...}

# 6. 요약 페이즈 진입
event: phase_change
data: {"from_phase": "DIALOGUE", "to_phase": "SUMMARY", "reason": "turns_exhausted", ...}

event: summary_start
data: {"reason": "turns_exhausted", ...}

# 7. 요약 메시지 스트리밍
event: bubble_start
data: {"bubble_id": "b_summary_1", "character": "SOISEOL", "type": "SUMMARY", ...}

event: bubble_chunk
data: {"bubble_id": "b_summary_1", "content": "오늘 대화를 정리해볼게요~", ...}

event: bubble_end
data: {"bubble_id": "b_summary_1", ...}

# 8. 마무리 페이즈
event: phase_change
data: {"from_phase": "SUMMARY", "to_phase": "FAREWELL", ...}

# 9. 마무리 메시지
event: bubble_start
data: {"bubble_id": "b_farewell_1", "character": "SOISEOL", "type": "FAREWELL", ...}

event: bubble_end
data: {"bubble_id": "b_farewell_1", "content": "오늘 즐거웠어요~ 또 만나요!", ...}

event: bubble_start
data: {"bubble_id": "b_farewell_2", "character": "STELLA", "type": "FAREWELL", ...}

event: bubble_end
data: {"bubble_id": "b_farewell_2", "content": "...또 와.", ...}

# 10. 세션 종료
event: session_end
data: {"session_id": "abc123", "reason": "turns_exhausted", "status": "completed", ...}

# 11. SSE 스트림 완료
event: complete
data: {"status": "success"}
```

---

## 7. 타임아웃 및 정리 정책

### 7.1 타임아웃 설정값

```python
@dataclass
class TimeoutConfig:
    """타임아웃 설정"""

    # 비활성 타임아웃 (마지막 활동 이후)
    inactivity_timeout_normal: int = 900       # 일반: 15분 (초)
    inactivity_timeout_premium: int = 1800     # 프리미엄: 30분 (초)

    # 절대 타임아웃 (세션 생성 이후)
    absolute_timeout_normal: int = 3600        # 일반: 1시간 (초)
    absolute_timeout_premium: int = 7200       # 프리미엄: 2시간 (초)

    # 재연결 유예 시간
    reconnect_grace_period: int = 30           # 30초

    # 일시정지 타임아웃
    pause_timeout: int = 1800                  # 30분

    # 사용자 입력 대기 타임아웃
    user_input_timeout: int = 300              # 5분

    # 백그라운드 정리 주기
    cleanup_interval: int = 60                 # 1분
```

### 7.2 타임아웃 경고 이벤트

| 남은 시간 | 이벤트 | 메시지 |
|----------|--------|--------|
| 5분 | `timeout_warning` | "5분 후 세션이 종료됩니다." |
| 2분 | `timeout_warning` | "2분 후 세션이 종료됩니다. 대화를 계속하시려면 메시지를 보내주세요." |
| 30초 | `timeout_imminent` | "30초 후 세션이 종료됩니다!" |

### 7.3 백그라운드 정리 태스크

```python
class SessionCleanupTask:
    """세션 정리 백그라운드 태스크"""

    def __init__(self, config: TimeoutConfig):
        self.config = config
        self._running = False

    async def start(self) -> None:
        """정리 태스크 시작"""
        self._running = True
        while self._running:
            try:
                await self._cleanup_cycle()
            except Exception as e:
                logger.error("cleanup_task_error", error=str(e))
            await asyncio.sleep(self.config.cleanup_interval)

    async def stop(self) -> None:
        """정리 태스크 중지"""
        self._running = False

    async def _cleanup_cycle(self) -> None:
        """정리 사이클 실행"""
        now = datetime.utcnow().timestamp()

        # 1. 만료된 세션 정리
        expired_count = await cleanup_expired_sessions()

        # 2. 타임아웃 경고 전송
        await self._send_timeout_warnings(now)

        # 3. 일시정지 세션 처리
        await self._process_paused_sessions(now)

        # 4. 통계 로깅
        if expired_count > 0:
            logger.info("cleanup_cycle_complete", expired_count=expired_count)

    async def _send_timeout_warnings(self, now: float) -> None:
        """타임아웃 경고 전송"""
        # 5분 경고 대상 조회
        warning_5m = await redis.zrangebyscore(
            "tikitaka:expiring_sessions",
            now + 240,  # 4분 후
            now + 360,  # 6분 후
        )

        for session_id in warning_5m:
            await send_timeout_warning(session_id, remaining_seconds=300)

        # 2분 경고 대상 조회
        warning_2m = await redis.zrangebyscore(
            "tikitaka:expiring_sessions",
            now + 90,   # 1.5분 후
            now + 150,  # 2.5분 후
        )

        for session_id in warning_2m:
            await send_timeout_warning(session_id, remaining_seconds=120)
```

---

## 8. 에러 처리 및 복구

### 8.1 종료 시 발생 가능한 에러

| 에러 유형 | 설명 | 처리 방법 |
|----------|------|----------|
| `SUMMARY_GENERATION_FAILED` | LLM 요약 생성 실패 | 폴백 템플릿 사용 |
| `REDIS_CONNECTION_ERROR` | Redis 연결 오류 | 재시도 (최대 3회) |
| `SSE_STREAM_ERROR` | SSE 스트림 오류 | 에러 이벤트 전송 후 종료 |
| `SESSION_NOT_FOUND` | 세션 데이터 없음 | 새 세션 생성 안내 |
| `INVALID_STATE_TRANSITION` | 잘못된 상태 전이 | 현재 상태 유지, 로그 기록 |

### 8.2 요약 생성 실패 시 폴백

```python
FALLBACK_SUMMARY_TEMPLATES = {
    "eastern": {
        "SOISEOL": "오늘 함께 나눈 이야기가 도움이 되셨길 바라요~ 동양의 지혜가 늘 함께하길 바랍니다!",
    },
    "western": {
        "STELLA": "...별의 인도가 함께할 거야. 또 봐.",
    },
    "consensus": "동양의 사주와 서양의 별자리가 보여주는 당신만의 길을 믿어보세요.",
}

async def generate_summary_with_fallback(session: SessionState) -> SummaryContent:
    """폴백 포함 요약 생성"""
    try:
        return await generate_llm_summary(session)
    except Exception as e:
        logger.warning(
            "summary_generation_fallback",
            session_id=session.session_id,
            error=str(e),
        )
        return SummaryContent(
            eastern_summary=FALLBACK_SUMMARY_TEMPLATES["eastern"]["SOISEOL"],
            western_summary=FALLBACK_SUMMARY_TEMPLATES["western"]["STELLA"],
            consensus_points=[FALLBACK_SUMMARY_TEMPLATES["consensus"]],
            final_advice="행운을 빕니다!",
        )
```

### 8.3 Redis 연결 에러 시 재시도

```python
async def update_session_with_retry(
    session_id: str,
    updates: dict,
    max_retries: int = 3,
) -> bool:
    """재시도 포함 세션 업데이트"""
    for attempt in range(max_retries):
        try:
            await redis.hset(f"tikitaka:session:{session_id}", mapping=updates)
            return True
        except RedisConnectionError as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(0.5 * (attempt + 1))  # 지수 백오프
                logger.warning(
                    "redis_retry",
                    session_id=session_id,
                    attempt=attempt + 1,
                    error=str(e),
                )
            else:
                logger.error(
                    "redis_connection_failed",
                    session_id=session_id,
                    error=str(e),
                )
                raise
    return False
```

### 8.4 복구 가능 상태 전이

```python
RECOVERABLE_TRANSITIONS = {
    # 현재 상태 -> 복구 가능한 이전 상태
    SessionStatus.EXPIRED: [SessionStatus.ACTIVE, SessionStatus.PAUSED],
    SessionStatus.TERMINATED: [],  # 복구 불가
}

async def attempt_session_recovery(
    session_id: str,
    current_status: SessionStatus,
) -> bool:
    """세션 복구 시도"""
    if current_status not in RECOVERABLE_TRANSITIONS:
        return False

    allowed_from = RECOVERABLE_TRANSITIONS[current_status]
    if not allowed_from:
        return False

    # 세션 만료 시간이 복구 유예 기간 내인지 확인
    session_data = await redis.hgetall(f"tikitaka:session:{session_id}")
    terminated_at = datetime.fromisoformat(session_data.get("termination.terminated_at", ""))

    recovery_grace_period = timedelta(minutes=5)
    if datetime.utcnow() - terminated_at > recovery_grace_period:
        return False

    # 복구 실행
    await redis.hset(
        f"tikitaka:session:{session_id}",
        mapping={
            "status": SessionStatus.ACTIVE.value,
            "termination.reason": None,
            "termination.terminated_at": None,
        }
    )

    logger.info("session_recovered", session_id=session_id)
    return True
```

---

## 9. 구현 가이드

### 9.1 파일 구조

```
yeji-ai-server/ai/src/yeji_ai/
├── services/
│   ├── tikitaka_service.py        # 기존 (수정)
│   ├── session/                   # 새로 추가: 세션 관리 모듈
│   │   ├── __init__.py
│   │   ├── manager.py             # SessionManager
│   │   ├── lifecycle.py           # SessionLifecycle (상태 전이)
│   │   ├── termination.py         # TerminationHandler (종료 처리)
│   │   ├── summary_generator.py   # SummaryGenerator (요약 생성)
│   │   └── cleanup.py             # SessionCleanupTask (정리 태스크)
│   └── ...
├── models/
│   ├── session.py                 # 새로 추가: 세션 모델
│   └── ...
└── config.py                      # 설정 확장
```

### 9.2 주요 클래스 책임

| 클래스 | 책임 |
|--------|------|
| `SessionManager` | 세션 CRUD, Redis 연동 |
| `SessionLifecycle` | 상태 전이 로직, 전이 유효성 검증 |
| `TerminationHandler` | 종료 조건 감지, 종료 처리 조율 |
| `SummaryGenerator` | 요약 콘텐츠 생성 (LLM + 폴백) |
| `SessionCleanupTask` | 백그라운드 정리, 타임아웃 경고 |

### 9.3 구현 우선순위

| 순서 | 항목 | 우선순위 | 예상 공수 |
|------|------|----------|----------|
| 1 | 종료 조건 감지 로직 | P0 | 0.5일 |
| 2 | 세션 상태 모델 + Redis 스키마 | P0 | 0.5일 |
| 3 | 요약 페이즈 처리 흐름 | P0 | 1일 |
| 4 | 프론트엔드 SSE 이벤트 | P0 | 0.5일 |
| 5 | 타임아웃 처리 + 백그라운드 태스크 | P1 | 1일 |
| 6 | 에러 처리 + 폴백 | P1 | 0.5일 |
| 7 | 세션 아카이브 | P2 | 0.5일 |

**총 예상 공수**: 4.5일

### 9.4 테스트 시나리오

| 시나리오 | 설명 | 검증 포인트 |
|----------|------|------------|
| 턴 소진 종료 | 10턴 진행 후 자동 종료 | 요약 생성, 이벤트 전송 |
| 사용자 명시적 종료 | "종료" 입력 시 종료 | 종료 키워드 감지, 확인 메시지 |
| 타임아웃 종료 | 15분 비활성 후 종료 | 경고 이벤트, 만료 처리 |
| 재연결 복구 | 연결 끊김 후 30초 내 재연결 | 세션 복구, 대화 이어가기 |
| 요약 생성 실패 | LLM 오류 시 폴백 | 폴백 템플릿 사용 |
| 프리미엄 보너스 턴 | 13턴까지 진행 | 보너스 턴 소진 후 종료 |

---

## 10. 참조 문서

| 문서 | 경로 | 설명 |
|------|------|------|
| 티키타카 스키마 V2 | `ai/docs/prd/tikitaka-schema-v2.md` | 스키마 정의 |
| 티키타카 서비스 | `ai/src/yeji_ai/services/tikitaka_service.py` | 기존 구현 |
| 티키타카 생성기 | `ai/src/yeji_ai/engine/tikitaka_generator.py` | LLM 생성 |
| 채팅 모델 | `ai/src/yeji_ai/models/fortune/chat.py` | 채팅 스키마 |
| 공통 스키마 | `ai/src/yeji_ai/models/schemas.py` | SSE 이벤트 |
| LLM 폴백 체인 | `ai/docs/design/llm-fallback-chain.md` | 폴백 설계 참고 |

---

## 변경 이력

| 버전 | 날짜 | 변경 내용 | 작성자 |
|------|------|----------|--------|
| 1.0 | 2026-01-30 | 초기 버전 | YEJI AI팀 |

---

> **Note**: 이 문서는 설계 단계이며, 구현 시 세부 사항이 변경될 수 있습니다.
> tikitaka-schema-v2.md PRD와 연계하여 참고하세요.
