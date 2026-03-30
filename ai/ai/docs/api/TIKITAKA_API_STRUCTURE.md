# 티키타카 채팅 API 구조

## 개요

동양(사주) + 서양(점성술) 페르소나가 턴 기반으로 대화하며 운세를 해석하는 **SSE 스트리밍 기반 실시간 채팅 API**입니다.

소이설(동양 사주) 과 스텔라(서양 점성술)가 사용자의 생년월일을 기반으로 분석을 수행하고, 그 결과에 대해 대화(티키타카)를 나누며 사용자의 질문에 답변합니다.

---

## 주요 특징

| 특징 | 설명 |
|------|------|
| **SSE 스트리밍** | 버블 단위 실시간 스트리밍으로 자연스러운 UX 제공 |
| **턴 기반 대화** | 최대 10턴 기본, 프리미엄 +3턴 추가 |
| **동양/서양 분석** | 비동기 병렬 처리로 빠른 분석 |
| **토론 상태 추적** | 페르소나 간 합의/토론 상태 실시간 전달 |
| **세션 관리** | 메모리 기반 세션 저장소 (프로덕션에서는 Redis 사용) |
| **에러 복구** | LLM 폴백, 스트리밍 재연결 지원 |

---

## API 엔드포인트

### 1. SSE 스트리밍: `/v1/fortune/tikitaka/stream`

**메인 엔드포인트** - 턴 단위 대화를 SSE로 스트리밍합니다.

#### 요청

```bash
POST /v1/fortune/tikitaka/stream
Content-Type: application/json
```

```json
{
  "session_id": null,
  "message": "운세를 알려주세요",
  "birth_date": "1990-05-15",
  "birth_time": "14:30",
  "is_premium": false
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `session_id` | string | 아니오 | 기존 세션 ID (신규 시 null) |
| `message` | string | 아니오 | 사용자 메시지 (첫 턴은 빈 문자열) |
| `birth_date` | string | 예 | 생년월일 (YYYY-MM-DD) |
| `birth_time` | string | 아니오 | 출생시간 (HH:MM, 점성술 상세 분석용) |
| `is_premium` | boolean | 아니오 | 프리미엄 사용자 여부 (기본값: false) |

#### 응답 (SSE 이벤트 스트림)

**스트림 구성:**

```
session 이벤트
  ↓
phase_change 이벤트
  ↓
bubble_start → bubble_chunk* → bubble_end (반복)
  ↓
turn_update 이벤트
  ↓
debate_status 이벤트
  ↓
complete 이벤트
```

##### SSE 이벤트 타입

###### 1. `session` - 세션 정보

```json
event: session
data: {
  "session_id": "abc123",
  "is_premium": false,
  "max_turns": 10,
  "bonus_turns": 0
}
```

###### 2. `phase_change` - 단계 변경

```json
event: phase_change
data: {
  "from_phase": "GREETING",
  "to_phase": "DIALOGUE"
}
```

**단계 종류:**
- `GREETING` - 인사 단계
- `DIALOGUE` - 대화 단계
- `QUESTION` - 질문 단계
- `SUMMARY` - 요약 단계
- `FAREWELL` - 종료 단계

###### 3. `bubble_start` - 버블 시작

```json
event: bubble_start
data: {
  "bubble_id": "b_a1b2c3d4",
  "character": "SOISEOL",
  "emotion": "HAPPY",
  "type": "GREETING",
  "phase": "GREETING"
}
```

**감정 코드 (emotion):**
- `NEUTRAL`, `HAPPY`, `CURIOUS`, `THOUGHTFUL`, `SURPRISED`
- `CONCERNED`, `CONFIDENT`, `PLAYFUL`, `MYSTERIOUS`, `EMPATHETIC`

**메시지 타입 (type):**
- `GREETING` - 인사
- `INFO_REQUEST` - 정보 요청
- `INTERPRETATION` - 해석
- `DEBATE` - 토론
- `CONSENSUS` - 합의
- `QUESTION` - 질문
- `CHOICE` - 선택지
- `SUMMARY` - 요약
- `FAREWELL` - 종료

###### 4. `bubble_chunk` - 버블 콘텐츠 청크

```json
event: bubble_chunk
data: {
  "bubble_id": "b_a1b2c3d4",
  "content": "안녕하세요~ 반가워요!"
}
```

20자씩 청크 단위로 전송되어 타이핑 효과를 구현합니다.

###### 5. `bubble_end` - 버블 완료

```json
event: bubble_end
data: {
  "bubble_id": "b_a1b2c3d4",
  "content": "안녕하세요~ 반가워요! 저는 소이설이에요.",
  "timestamp": "2026-02-01T15:30:45.123456"
}
```

###### 6. `turn_update` - 턴 정보 업데이트

```json
event: turn_update
data: {
  "current_turn": 1,
  "remaining_turns": 9,
  "is_last_turn": false
}
```

###### 7. `debate_status` - 토론 상태

```json
event: debate_status
data: {
  "is_consensus": true,
  "eastern_opinion": "따뜻한 성격",
  "western_opinion": "긍정적 기운",
  "consensus_point": "둘 다 열정적인 에너지를 가지고 있다",
  "question": "연애운, 직장운, 금전운 중 어떤 것이 가장 궁금하신가요?"
}
```

###### 8. `ui_hint` - UI 힌트 (토론 시)

```json
event: ui_hint
data: {
  "show_choice": true,
  "choices": [
    {
      "value": 1,
      "character": "SOISEOL",
      "label": "소이설의 해석"
    },
    {
      "value": 2,
      "character": "STELLA",
      "label": "스텔라의 해석"
    }
  ]
}
```

###### 9. `pause` - 입력 대기 (생년월일 미입력)

```json
event: pause
data: {
  "waiting_for": "birth_date",
  "placeholder": "생년월일을 입력해주세요 (예: 1990-05-15)"
}
```

###### 10. `error` - 오류

```json
event: error
data: {
  "code": "ANALYSIS_ERROR",
  "message": "분석 중 오류가 발생했습니다.",
  "recoverable": false
}
```

###### 11. `complete` - 스트리밍 완료

```json
event: complete
data: {
  "status": "success",
  "total_bubbles": 3
}
```

---

### 2. 세션 조회: `GET /v1/fortune/tikitaka/session/{session_id}`

기존 세션의 상태를 조회합니다.

#### 요청

```bash
GET /v1/fortune/tikitaka/session/abc123
```

#### 응답

```json
{
  "session_id": "abc123",
  "current_turn": 1,
  "max_turns": 10,
  "bonus_turns": 0,
  "remaining_turns": 9,
  "is_premium": false,
  "phase": "DIALOGUE",
  "has_eastern_result": true,
  "has_western_result": true
}
```

---

## 페르소나 (캐릭터)

### 동양 캐릭터

| 코드 | 이름 | 말투 | 특징 |
|------|------|------|------|
| `SOISEOL` | 소이설 | 하오체 | 따뜻한 사주 전문가 (기본값) |
| `CHEONGWOON` | 청운 | 시적 하오체 | 신선/현자 스타일 |
| `HWARIN` | 화린 | 나른한 해요체 | 비즈니스 중심 |

### 서양 캐릭터

| 코드 | 이름 | 말투 | 특징 |
|------|------|------|------|
| `STELLA` | 스텔라 | 해요체 | 쿨한 점성술 전문가 (기본값) |
| `KYLE` | 카일 | 반말+존댓말 | 도박사/점술가 스타일 |
| `ELARIA` | 엘라리아 | 우아한 해요체 | 공주/외교관 스타일 |

---

## 턴 구조 (Turn Flow)

### Turn 0: 그리팅 (세션 시작)

**요청:**
```json
{
  "session_id": null,
  "birth_date": "1990-05-15",
  "birth_time": "14:30",
  "message": ""
}
```

**처리 흐름:**
1. 세션 생성
2. 생년월일 검증
3. 비동기 병렬로 동양/서양 분석 실행
4. 두 페르소나의 인사 메시지 생성
5. 분석 결과 기반 카테고리별 그리팅
6. 첫 번째 질문 제안

**응답:**
- `bubble_start` (SOISEOL, GREETING)
- `bubble_chunk*` (콘텐츠 스트리밍)
- `bubble_end` (SOISEOL 완료)
- `bubble_start` (STELLA, GREETING)
- `bubble_chunk*`
- `bubble_end` (STELLA 완료)
- `debate_status` (합의/토론 상태)
- `turn_update` (Turn 1로 진행)
- `complete`

### Turn 1~N: 대화 진행

**요청:**
```json
{
  "session_id": "abc123",
  "message": "요즘 연애운이 궁금해요",
  "birth_date": "1990-05-15"
}
```

**처리 흐름:**
1. 기존 세션 조회 (분석 결과 캐시)
2. 사용자 메시지 기반 LLM 대화 생성
3. 소이설 해석 → 스텔라 해석
4. 합의/토론 상태 판단
5. 다음 질문 제안

**응답:**
- `phase_change` (DIALOGUE로 전환)
- `bubble_start` (SOISEOL, INTERPRETATION)
- `bubble_chunk*`
- `bubble_end`
- `bubble_start` (STELLA, INTERPRETATION)
- `bubble_chunk*`
- `bubble_end`
- `debate_status` (합의/토론)
- `ui_hint` (토론 시 선택지)
- `turn_update`
- `complete`

### Turn 3+: 세션 종료 (기본값) / 프리미엄 추가 턴

**기본:** Turn 3 이후 `is_complete: true` 반환
**프리미엄:** Turn 13까지 진행 가능 (+3 보너스 턴)

---

## 세션 상태 관리

### 메모리 구조

```python
class TikitakaSessionStateV2:
    session_id: str              # 세션 고유 ID (UUID 8자리)
    current_turn: int            # 현재 턴 (0부터 시작)
    max_turns: int               # 기본 턴 수 (10)
    bonus_turns: int             # 보너스 턴 (프리미엄 +3)
    remaining_turns: int         # 남은 턴 수
    is_premium: bool             # 프리미엄 여부
    phase: PhaseCode             # 현재 단계
    has_eastern_result: bool     # 동양 분석 완료
    has_western_result: bool     # 서양 분석 완료
```

### 턴 계산

```
기본 사용자:    최대 10턴
프리미엄:       최대 13턴 (10 + 3 보너스)
```

---

## 캐릭터 조합

### 추천 조합

| 동양 | 서양 | 설명 |
|------|------|------|
| SOISEOL | STELLA | 기본 조합 (따뜻함 + 쿨함) |
| CHEONGWOON | ELARIA | 고급 조합 (신비로움 + 우아함) |
| HWARIN | KYLE | 실용 조합 (현실적 + 개성있음) |

### 동적 선택

프론트엔드에서 사용자가 선호하는 캐릭터를 선택하면, API는 그에 맞춰 응답을 커스터마이징합니다.

---

## 데이터 플로우

### 분석 결과 캐싱

```
Turn 0: 분석 실행
  ↓
Eastern Result (사주 분석)
Western Result (점성술 분석)
  ↓
메모리 저장 (Redis 권장)
  ↓
Turn 1~N: 캐시에서 재사용
```

**이점:**
- 같은 생년월일의 재분석 불필요
- 응답 시간 단축
- LLM 호출 비용 절감

### 컨텍스트 전달

```
Session State
  ├─ Eastern Result (오행, 일간, 강약점)
  ├─ Western Result (별자리, 원소, 행운 가이드)
  ├─ Debate History (이전 토론 내용)
  └─ User Preferences (선호 캐릭터, 관심 주제)
     ↓
  LLM Prompt에 포함
     ↓
  풍부한 컨텍스트 기반 응답 생성
```

---

## 에러 처리

### 복구 불가능한 오류

```json
{
  "event": "error",
  "data": {
    "code": "ANALYSIS_ERROR",
    "message": "분석 중 오류가 발생했습니다.",
    "recoverable": false
  }
}
```

**상황:**
- 생년월일 형식 오류
- LLM 서버 영구 다운
- 데이터베이스 접근 불가

### 복구 가능한 오류 (폴백)

```
LLM 호출 실패
  ↓
폴백 메시지 생성 (기본 해석)
  ↓
계속 진행
```

**예시:**
```python
try:
    soiseol_msg = await llm.generate(...)
except:
    soiseol_msg = f"{day_gan} 일간이시오. {strength}"  # 폴백
```

---

## 구현 세부사항

### SSE 스트리밍 메커니즘

```python
async def generate():
    yield format_sse_event("session", {...})
    yield format_sse_event("phase_change", {...})

    async for event in stream_greeting_bubbles():
        yield event

    yield format_sse_event("turn_update", {...})
    yield format_sse_event("complete", {...})

return StreamingResponse(
    generate(),
    media_type="text/event-stream",
    headers={"Cache-Control": "no-cache"}
)
```

### 버블 파싱 (LLM 출력)

LLM에서 생성한 텍스트를 파싱하여 구조화된 버블로 변환:

```xml
<bubble character="SOISEOL" emotion="HAPPY" type="GREETING">
  안녕하세요!
</bubble>

<bubble character="STELLA" emotion="NEUTRAL" type="GREETING">
  안녕하세요.
</bubble>
```

**폴백:** XML 파싱 실패 시 접두사 기반 파싱 또는 전체 텍스트를 단일 버블로 처리

### 감정 코드 매핑

LLM이 생성한 감정 텍스트를 코드로 매핑:

```python
EMOTION_MAP = {
    "happy": EmotionCode.HAPPY,
    "neutral": EmotionCode.NEUTRAL,
    "curious": EmotionCode.CURIOUS,
    ...
}
```

---

## 배포 정보

| 환경 | URL | 브랜치 | 상태 |
|------|-----|--------|------|
| 프로덕션 | https://i14a605.p.ssafy.io/ai | `ai/main` | 수동 배포 |
| 개발 | https://i14a605.p.ssafy.io/ai-dev | `ai/develop` | 자동 배포 |

### 환경변수

```bash
VLLM_BASE_URL=http://<GPU_IP>:8001
VLLM_MODEL=tellang/yeji-8b-rslora-v7-AWQ
CORS_ORIGINS=["https://i14a605.p.ssafy.io"]
LOG_LEVEL=INFO
```

---

## 클라이언트 구현 예시

### JavaScript/TypeScript (SSE)

```typescript
const response = await fetch('/v1/fortune/tikitaka/stream', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    session_id: null,
    birth_date: '1990-05-15',
    is_premium: false
  })
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;

  const text = decoder.decode(value);
  const lines = text.split('\n');

  for (const line of lines) {
    if (line.startsWith('event: ')) {
      const event = line.slice(7);
      // 이벤트 타입별 처리
    }
    if (line.startsWith('data: ')) {
      const data = JSON.parse(line.slice(6));
      // 데이터 처리
    }
  }
}
```

### Python (requests-sse)

```python
import requests_sse

url = "http://localhost:8000/v1/fortune/tikitaka/stream"
payload = {
    "session_id": None,
    "birth_date": "1990-05-15",
    "is_premium": False
}

with requests_sse.get(url, json=payload, stream=True) as r:
    for event in r.iter_sse():
        print(f"Event: {event.event}")
        print(f"Data: {event.data}")
```

---

## 성능 최적화

### 병렬 처리

```python
# 동양/서양 분석 동시 실행
eastern_result, western_result = await asyncio.gather(
    eastern_service.analyze(eastern_req),
    western_service.analyze(western_req)
)
```

**효과:** 순차 처리 대비 ~50% 시간 단축

### 스트리밍 최적화

```python
# 청크 크기: 20자, 간격: 50ms
for i in range(0, len(content), 20):
    chunk = content[i:i+20]
    yield event
    await asyncio.sleep(0.05)
```

**효과:** 자연스러운 타이핑 애니메이션, 메모리 효율적

### 캐싱 전략

```python
# 동양/서양 분석 결과 재사용
if eastern_fortune_id:
    cached = get_fortune(eastern_fortune_id)
    if cached:
        return cached  # LLM 호출 불필요
```

**효과:** 재방문 사용자 응답 시간 80% 단축

---

## 레거시 API (Deprecated)

아래 엔드포인트는 더 이상 사용되지 않습니다:

| 엔드포인트 | 상태 | 대체 API |
|-----------|------|----------|
| `/v1/fortune/chat` | ❌ Deprecated | `/v1/fortune/tikitaka/stream` |
| `/v1/fortune/demo/tikitaka-3turn` | ❌ Deprecated | `/v1/fortune/tikitaka/stream` |

---

## 트러블슈팅

### 세션이 유실되었습니다

**원인:** 서버 재시작, 메모리 부족
**해결:** 클라이언트에서 `session_id=null`로 새 세션 생성

### 버블이 비어있습니다

**원인:** LLM 응답 오류, 네트워크 지연
**상태:** 폴백 메시지로 자동 복구
**확인:** 로그에서 `llm_empty_response` 경고 확인

### 스트림이 끊겼습니다

**원인:** 클라이언트 네트워크 불안정, 프록시 타임아웃
**해결:** 클라이언트에서 재시도, 기존 `session_id` 사용

### 턴이 예상과 다릅니다

**원인:** 프리미엄 플래그 오류
**확인:** `/v1/fortune/tikitaka/session/{id}`에서 `bonus_turns` 확인

---

## 참조

| 문서 | 경로 |
|------|------|
| 시스템 아키텍처 | `docs/ARCHITECTURE.md` |
| LLM 프롬프팅 | `docs/guides/qwen3-prompting-guide.md` |
| 후처리 가이드 | `docs/prd/llm-response-postprocessor.md` |
| Provider 설정 | `docs/PROVIDERS.md` |
| 감정 코드 가이드 | `docs/guides/tikitaka-emotion-guide.md` |
| 스키마 정의 (V2) | `docs/prd/tikitaka-schema-v2.md` |

---

## 분석 API

### POST `/v1/fortune/eastern` - 동양 사주 분석

생년월일시를 기반으로 사주팔자를 분석합니다.

#### 요청

```json
{
  "birth_date": "1990-05-15",
  "birth_time": "14:30",
  "gender": "M"
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `birth_date` | string | 예 | 생년월일 (YYYY-MM-DD) |
| `birth_time` | string | 아니오 | 출생시간 (HH:MM) |
| `gender` | string | 아니오 | 성별 (M/F) |

#### 응답 (SajuDataV2)

```json
{
  "element": "FIRE",
  "chart": {
    "summary": "甲子년 乙丑월 丙寅일",
    "year": {
      "gan_code": "GAPO",
      "ji_code": "JA",
      "element_code": "WOOD"
    },
    "month": {
      "gan_code": "EULA",
      "ji_code": "CUK",
      "element_code": "EARTH"
    },
    "day": {
      "gan_code": "BYUNG",
      "ji_code": "IN",
      "element_code": "FIRE"
    },
    "hour": {
      "gan_code": "KEUN",
      "ji_code": "YO",
      "element_code": "METAL"
    }
  },
  "stats": {
    "cheongan_jiji": {
      "summary": "천간: 목, 토, 화, 금 / 지지: 목, 토, 화, 금",
      "list": [...]
    },
    "five_elements": {
      "summary": "목화토금수 모두 골고루 있어 균형잡힌 구조",
      "list": [
        {"element": "WOOD", "count": 2, "strength": "normal"},
        {"element": "FIRE", "count": 1, "strength": "weak"},
        {"element": "EARTH", "count": 1, "strength": "normal"},
        {"element": "METAL", "count": 1, "strength": "normal"},
        {"element": "WATER", "count": 0, "strength": "deficient"}
      ]
    },
    "yin_yang_ratio": {
      "summary": "음양 비율이 비슷하여 안정적",
      "yin": 50,
      "yang": 50
    },
    "ten_gods": {
      "summary": "정재, 정관, 정인 모두 존재",
      "list": [
        {"god": "JEONG_JAE", "count": 1, "position": "year"},
        {"god": "JEONG_GWAN", "count": 1, "position": "month"}
      ]
    }
  },
  "final_verdict": {
    "summary": "따뜻한 성격, 대인관계 좋음",
    "strength": "정직함, 책임감, 행동력",
    "weakness": "너무 신중할 수 있음",
    "advice": "대담한 도전이 필요한 시기"
  },
  "lucky": {
    "color": "빨강",
    "number": "3",
    "item": "나무로 만든 물품"
  }
}
```

#### Query Parameters

| 파라미터 | 타입 | 설명 |
|---------|------|------|
| `skip_validation` | boolean | true일 경우 검증 없이 raw LLM 응답 반환 (테스트용) |
| `graceful` | boolean | true일 경우 검증 실패해도 200 응답 반환 + 원본 데이터 |

**사용 예시:**
```
POST /v1/fortune/eastern?skip_validation=true
POST /v1/fortune/eastern?graceful=true
```

---

### POST `/v1/fortune/western` - 서양 점성술 분석

생년월일시와 출생지를 기반으로 출생 차트를 분석합니다.

#### 요청

```json
{
  "birth_date": "1990-05-15",
  "birth_time": "14:30",
  "birth_place": "Seoul, Korea",
  "latitude": 37.5665,
  "longitude": 126.9780
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `birth_date` | string | 예 | 생년월일 (YYYY-MM-DD) |
| `birth_time` | string | 아니오 | 출생시간 (HH:MM) |
| `birth_place` | string | 아니오 | 출생지 (도시명) |
| `latitude` | float | 아니오 | 위도 (37.5665) |
| `longitude` | float | 아니오 | 경도 (126.9780) |

#### 응답 (WesternFortuneDataV2)

```json
{
  "element": "FIRE",
  "stats": {
    "main_sign": {
      "name": "황소자리",
      "symbol": "♉"
    },
    "element_summary": "불의 원소를 많이 가져 열정적이고 활동적",
    "element_4_distribution": [
      {"element": "FIRE", "count": 3, "percentage": 42.8},
      {"element": "EARTH", "count": 2, "percentage": 28.6},
      {"element": "AIR", "count": 1, "percentage": 14.3},
      {"element": "WATER", "count": 1, "percentage": 14.3}
    ],
    "modality_summary": "고정(Fixed) 성향으로 안정성 추구",
    "modality_3_distribution": [
      {"modality": "CARDINAL", "count": 2, "percentage": 28.6},
      {"modality": "FIXED", "count": 3, "percentage": 42.8},
      {"modality": "MUTABLE", "count": 2, "percentage": 28.6}
    ],
    "keywords_summary": "안정적, 현실적, 감정 풍부, 창의적",
    "keywords": [
      "안정성",
      "현실감",
      "감정 풍부함",
      "창의성",
      "강인함"
    ]
  },
  "fortune_content": {
    "overview": "진정한 자기 가치를 깨닫는 시기",
    "detailed_analysis": [
      "현재 행성 배치에서 개인적 성장의 기회가 보입니다.",
      "금성의 영향으로 대인관계가 호전될 가능성이 있습니다.",
      "화성의 에너지로 목표 달성에 필요한 행동력을 갖추고 있습니다."
    ],
    "advice": "자신감을 가지고 새로운 도전을 시작하세요."
  },
  "lucky": {
    "color": "황금색",
    "number": "5"
  }
}
```

#### Query Parameters

| 파라미터 | 타입 | 설명 |
|---------|------|------|
| `skip_validation` | boolean | true일 경우 검증 없이 raw LLM 응답 반환 (테스트용) |
| `graceful` | boolean | true일 경우 검증 실패해도 200 응답 반환 + 원본 데이터 |

---

## 요약 API

### GET `/v1/fortune/chat/summary/{session_id}` - 운세 요약

채팅 세션의 운세를 동양/서양 방식으로 요약합니다.

#### 요청

```bash
GET /v1/fortune/chat/summary/{session_id}?type=eastern&category=love
```

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `session_id` | string | 예 | 티키타카 세션 ID |
| `type` | string | 예 | 운세 타입 (eastern 또는 western) |
| `category` | string | 아니오 | 운세 카테고리 (기본값: total) |

**카테고리 예시:**
- `total` - 종합운
- `love` - 연애운
- `career` - 직장운
- `money` - 금전운
- `health` - 건강운

#### 응답

```json
{
  "session_id": "abc123",
  "category": "love",
  "fortune_type": "eastern",
  "fortune": {
    "character": "SOISEOL",
    "score": 85,
    "one_line": "목(木) 기운이 강해 연애운이 상승하는 시기",
    "keywords": [
      "인연 상승",
      "적극적 표현",
      "새 만남"
    ],
    "detail": "일간(甲)을 중심으로 보면, 납음지(納音)의 영향으로 긍정적 에너지가 흐르고 있습니다. 신약(身弱)이 아니므로 자신감 있게 행동할 수 있는 시기입니다."
  }
}
```

**서양 점성술 응답 예시:**

```json
{
  "session_id": "abc123",
  "category": "career",
  "fortune_type": "western",
  "fortune": {
    "character": "STELLA",
    "score": 75,
    "one_line": "현재 행성 배치에서 경력 발전의 기회가 보입니다",
    "keywords": [
      "새로운 기회",
      "사람 네트워크",
      "자기 표현"
    ],
    "detail": "태양(Sun)이 10번 하우스 부근에 위치하여 직업적 성공과 공개적 인정이 증가할 가능성이 높습니다."
  }
}
```

---

## Enum API

### GET `/v1/fortune/eastern/enums` - 동양 Enum 목록

프론트엔드 TypeScript 타입 정의용 Enum 목록을 반환합니다.

#### 응답

```json
{
  "element_codes": [
    {"code": "WOOD", "name": "목(木)", "color": "#2ecc71"},
    {"code": "FIRE", "name": "화(火)", "color": "#e74c3c"},
    {"code": "EARTH", "name": "토(土)", "color": "#f39c12"},
    {"code": "METAL", "name": "금(金)", "color": "#95a5a6"},
    {"code": "WATER", "name": "수(水)", "color": "#3498db"}
  ],
  "cheongan_codes": [
    {"code": "GAPO", "name": "甲", "element": "WOOD", "yinyang": "YANG"},
    {"code": "EULA", "name": "乙", "element": "WOOD", "yinyang": "YIN"},
    ...
  ],
  "jiji_codes": [
    {"code": "JA", "name": "子", "element": "WATER", "yinyang": "YANG"},
    {"code": "CUK", "name": "丑", "element": "EARTH", "yinyang": "YIN"},
    ...
  ],
  "ten_god_codes": [
    {"code": "JEONG_JAE", "name": "正財", "meaning": "정재"},
    {"code": "PYEONG_JAE", "name": "偏財", "meaning": "편재"},
    ...
  ],
  "pillar_keys": [
    "year",
    "month",
    "day",
    "hour"
  ],
  "yinyang_balance": [
    {"yin": 0, "yang": 100, "label": "매우 양(陽)"},
    {"yin": 25, "yang": 75, "label": "양(陽)"},
    {"yin": 50, "yang": 50, "label": "균형"},
    {"yin": 75, "yang": 25, "label": "음(陰)"},
    {"yin": 100, "yang": 0, "label": "매우 음(陰)"}
  ],
  "eastern_badges": [
    {"id": "strength", "label": "강함"},
    {"id": "weakness", "label": "약함"},
    {"id": "balanced", "label": "균형"}
  ]
}
```

### GET `/v1/fortune/western/enums` - 서양 Enum 목록

프론트엔드 TypeScript 타입 정의용 Enum 목록을 반환합니다.

#### 응답

```json
{
  "zodiac_codes": [
    {"code": "ARIES", "name": "양자리", "symbol": "♈", "element": "FIRE"},
    {"code": "TAURUS", "name": "황소자리", "symbol": "♉", "element": "EARTH"},
    {"code": "GEMINI", "name": "쌍둥이자리", "symbol": "♊", "element": "AIR"},
    ...
  ],
  "zodiac_elements": [
    {"code": "FIRE", "name": "불", "color": "#e74c3c", "description": "열정적, 활동적"},
    {"code": "EARTH", "name": "흙", "color": "#f39c12", "description": "현실적, 안정적"},
    {"code": "AIR", "name": "공기", "color": "#3498db", "description": "지적, 사교적"},
    {"code": "WATER", "name": "물", "color": "#9b59b6", "description": "감정적, 직관적"}
  ],
  "zodiac_modalities": [
    {"code": "CARDINAL", "name": "기동(Cardinal)", "description": "주도적, 활동적"},
    {"code": "FIXED", "name": "고정(Fixed)", "description": "안정적, 결정력"},
    {"code": "MUTABLE", "name": "변동(Mutable)", "description": "유연함, 적응력"}
  ],
  "planet_codes": [
    {"code": "SUN", "name": "태양(Sun)", "symbol": "☉"},
    {"code": "MOON", "name": "달(Moon)", "symbol": "☽"},
    {"code": "MERCURY", "name": "수성(Mercury)", "symbol": "☿"},
    ...
  ],
  "house_codes": [
    {"code": "HOUSE_1", "name": "1번 하우스", "meaning": "자신"},
    {"code": "HOUSE_2", "name": "2번 하우스", "meaning": "재물"},
    ...
  ],
  "aspect_codes": [
    {"code": "CONJUNCTION", "name": "합(0°)", "description": "에너지 집중"},
    {"code": "OPPOSITION", "name": "대(180°)", "description": "대립, 균형"},
    ...
  ],
  "western_badges": [
    {"id": "fire_dominant", "label": "불 우위"},
    {"id": "earth_dominant", "label": "흙 우위"},
    {"id": "cardinal_strong", "label": "기동성 강함"}
  ]
}
```

---

## 전체 API 요약표

| 카테고리 | 엔드포인트 | 메서드 | 설명 |
|---------|-----------|--------|------|
| **분석** | `/v1/fortune/eastern` | POST | 동양 사주 분석 |
| **분석** | `/v1/fortune/western` | POST | 서양 점성술 분석 |
| **채팅** | `/v1/fortune/tikitaka/stream` | POST | 턴 단위 티키타카 (메인) |
| **채팅** | `/v1/fortune/tikitaka/session/{id}` | GET | 세션 조회 |
| **요약** | `/v1/fortune/chat/summary/{id}` | GET | 동/서양 요약 |
| **Enum** | `/v1/fortune/eastern/enums` | GET | 동양 Enum 목록 |
| **Enum** | `/v1/fortune/western/enums` | GET | 서양 Enum 목록 |

---

## 권장 사용 플로우

### 1. 기본 플로우 (프론트엔드 / 티키타카 채팅)

```
1. POST /v1/fortune/tikitaka/stream (Turn 0)
   → session_id, 그리팅 메시지 받음
   → 동양/서양 초기 분석 결과 캐싱

2. POST /v1/fortune/tikitaka/stream (Turn 1~3)
   → 사용자 질문에 대한 티키타카 응답
   → 캐시된 분석 결과 활용

3. GET /v1/fortune/chat/summary/{session_id}?type=eastern
   → 동양 방식 운세 요약

4. GET /v1/fortune/chat/summary/{session_id}?type=western
   → 서양 방식 운세 요약
```

**장점:**
- 자연스러운 대화 흐름
- 실시간 스트리밍으로 빠른 응답
- 세션 관리로 컨텍스트 유지

### 2. 단독 분석 (백엔드 연동 / API 직접 호출)

```
1. POST /v1/fortune/eastern
   → 사주 분석 결과 직접 반환

2. POST /v1/fortune/western
   → 점성술 분석 결과 직접 반환

3. GET /v1/fortune/eastern/enums
   → 데이터 포맷 정의 참고

4. GET /v1/fortune/western/enums
   → 데이터 포맷 정의 참고
```

**장점:**
- 분석 결과를 구조화된 JSON으로 즉시 획득
- 별도 세션 관리 불필요
- 대량 분석이나 자동화 작업에 적합

### 3. 하이브리드 플로우 (분석 + 채팅)

```
1. POST /v1/fortune/eastern (또는 western)
   → 기본 분석 결과 획득

2. POST /v1/fortune/tikitaka/stream
   → 세션 생성 (birth_date 포함)
   → 동/서양 분석 자동 실행

3. GET /v1/fortune/chat/summary/{session_id}
   → 채팅 기반 맞춤 요약
```

**사용 사례:**
- 사용자가 이미 분석 결과를 가지고 있는 경우
- 추가 해석이나 상담이 필요한 경우
