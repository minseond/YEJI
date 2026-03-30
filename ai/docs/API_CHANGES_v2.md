# AI 서버 API 변경사항 (ai/main → ai/develop)

> **버전:** v1.0.1.m → v2.0.0.d
> **작성일:** 2026-02-03
> **대상:** Backend / Frontend 개발자

---

## 목차

1. [주요 변경 요약](#1-주요-변경-요약)
2. [Fortune API 변경](#2-fortune-api-변경)
3. [Chat API 변경](#3-chat-api-변경)
4. [새로운 API: Fortune Summary](#4-새로운-api-fortune-summary)
5. [권장 플로우](#5-권장-플로우)
6. [BE 변경 필요사항](#6-be-변경-필요사항)
7. [FE 변경 필요사항](#7-fe-변경-필요사항)
8. [마이그레이션 가이드](#8-마이그레이션-가이드)

---

## 1. 주요 변경 요약

| 항목 | ai/main (v1.x) | ai/develop (v2.x) | 비고 |
|------|----------------|-------------------|------|
| Fortune 분석 결과 식별 | 없음 | `fortune_key` 반환 | Redis 캐시 키 |
| Fortune 재사용 | 매번 재분석 | `fortune_key`로 재사용 | 비용/시간 절감 |
| Fortune 요약 | 없음 | Summary API 추가 | 채팅 컨텍스트용 |
| 세션 캐릭터 | 고정 (버그) | 선택한 캐릭터 유지 | 버그 수정 |
| Redis 의존성 | 선택적 | 필수 (캐싱) | 인프라 변경 |

---

## 2. Fortune API 변경

### 2.1 Eastern Fortune API

**엔드포인트:** `POST /api/v1/fortune/eastern`

#### 응답 필드 추가

```diff
{
+ "fortune_key": "eastern:1993-07-14:0800:M",  // 새로 추가
  "element": "WOOD",
  "stats": { ... },
  "fortune_content": { ... },
  "lucky": { ... }
}
```

| 필드 | 타입 | 설명 |
|------|------|------|
| `fortune_key` | `string` | 운세 데이터 식별자. 형식: `eastern:{birth_date}:{HHMM}:{gender}` |

#### fortune_key 형식

```
eastern:1993-07-14:0800:M
         │          │    │
         │          │    └─ gender: M/F/U
         │          └────── birth_time: HHMM (구분자 제거)
         └───────────────── birth_date: YYYY-MM-DD
```

### 2.2 Western Fortune API

**엔드포인트:** `POST /api/v1/fortune/western`

#### 응답 필드 추가

```diff
{
+ "fortune_key": "western:1993-07-14:0800",  // 새로 추가
  "element": "FIRE",
  "stats": { ... },
  "fortune_content": { ... },
  "lucky": { ... }
}
```

| 필드 | 타입 | 설명 |
|------|------|------|
| `fortune_key` | `string` | 점성술 데이터 식별자. 형식: `western:{birth_date}:{HHMM}` |

---

## 3. Chat API 변경

### 3.1 Turn Start API (세션 시작)

**엔드포인트:** `POST /api/v1/fortune/chat/turn/start`

#### 요청 필드 추가

```diff
{
  "birth_date": "1993-07-14",
  "birth_time": "08:00",
  "category": "LOVE",
  "char1_code": "SOISEOL",
  "char2_code": "STELLA",
+ "eastern_fortune_key": "eastern:1993-07-14:0800:M",   // 새로 추가 (선택)
+ "western_fortune_key": "western:1993-07-14:0800"      // 새로 추가 (선택)
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `eastern_fortune_key` | `string \| null` | 선택 | 동양 사주 fortune_key (있으면 재분석 생략) |
| `western_fortune_key` | `string \| null` | 선택 | 서양 점성술 fortune_key (있으면 재분석 생략) |

#### 응답 필드 추가

```diff
{
  "session_id": "abc12345",
  "turn": 1,
  "messages": [...],
  "suggested_question": "...",
  "is_complete": false,
+ "eastern_summary": "사주 분석 요약...",      // 새로 추가
+ "western_summary": "점성술 분석 요약...",    // 새로 추가
+ "summary_source": "cached",                  // 새로 추가: "cached" | "generated"
+ "fortune_source": "fortune_key"             // 새로 추가: "fortune_key" | "provided" | "generated"
}
```

| 필드 | 타입 | 설명 |
|------|------|------|
| `eastern_summary` | `string \| null` | 동양 사주 요약본 (채팅 컨텍스트용) |
| `western_summary` | `string \| null` | 서양 점성술 요약본 (채팅 컨텍스트용) |
| `summary_source` | `string \| null` | 요약 출처: `cached` (Redis), `generated` (새로 생성) |
| `fortune_source` | `string \| null` | 사주 데이터 출처 |

#### fortune_source 값

| 값 | 설명 |
|----|------|
| `fortune_key` | fortune_key로 Redis에서 조회 |
| `provided` | (Deprecated) 요청에 fortune_data 직접 전달 |
| `generated` | 새로 LLM 분석 실행 |

### 3.2 Turn Continue API (대화 계속)

**엔드포인트:** `POST /api/v1/fortune/chat/turn/continue`

#### 버그 수정: 캐릭터 선택 유지

**이전 (ai/main):** turn/start에서 선택한 캐릭터가 무시되고 항상 SOISEOL/STELLA로 고정

**이후 (ai/develop):** turn/start에서 선택한 캐릭터가 세션에 저장되어 continue에서도 유지

```python
# 세션에 저장된 캐릭터 사용
session.char1_code = request.char1_code  # turn/start에서 저장
session.char2_code = request.char2_code
```

---

## 4. 새로운 API: Fortune Summary

운세 분석 결과의 요약본을 조회/생성하는 API.

### 4.1 Eastern Summary

**엔드포인트:** `POST /api/v1/fortune/eastern/summary`

#### 요청

```json
{
  "fortune_key": "eastern:1993-07-14:0800:M"
}
```

#### 응답

```json
{
  "fortune_key": "eastern:1993-07-14:0800:M",
  "summary": "사주 분석 요약 텍스트...",
  "source": "cached",
  "cached_at": "2026-02-03T12:00:00Z"
}
```

### 4.2 Western Summary

**엔드포인트:** `POST /api/v1/fortune/western/summary`

#### 요청

```json
{
  "fortune_key": "western:1993-07-14:0800"
}
```

#### 응답

```json
{
  "fortune_key": "western:1993-07-14:0800",
  "summary": "점성술 분석 요약 텍스트...",
  "source": "generated",
  "cached_at": "2026-02-03T12:00:00Z"
}
```

---

## 5. 권장 플로우

### 5.1 최적화된 플로우 (권장)

Fortune 분석 결과를 재사용하여 비용/시간 절감.

```
┌─────────────────────────────────────────────────────────────────┐
│                    최적화된 플로우 (권장)                        │
└─────────────────────────────────────────────────────────────────┘

[FE] ─────────────────────────────────────────────────────────────

1. 생년월일/시간 입력
      │
      ▼
2. POST /fortune/eastern  ──────►  { fortune_key: "eastern:..." }
   POST /fortune/western  ──────►  { fortune_key: "western:..." }
      │
      │  fortune_key 저장
      ▼
3. POST /chat/turn/start
   {
     birth_date, category,
     eastern_fortune_key: "eastern:...",  // 저장한 키 전달
     western_fortune_key: "western:..."
   }
      │
      ▼
4. 응답: { session_id, messages, eastern_summary, western_summary }
      │
      ▼
5. POST /chat/turn/continue
   { session_id, message }
      │
      ▼
6. 반복 (최대 10턴)
```

### 5.2 기존 플로우 (하위 호환)

fortune_key 없이도 동작 (매번 재분석).

```
┌─────────────────────────────────────────────────────────────────┐
│                    기존 플로우 (하위 호환)                       │
└─────────────────────────────────────────────────────────────────┘

[FE] ─────────────────────────────────────────────────────────────

1. 생년월일/시간 입력
      │
      ▼
2. POST /chat/turn/start
   { birth_date, category }  // fortune_key 없음
      │
      │  내부에서 fortune 분석 실행 (LLM 호출)
      ▼
3. 응답: { session_id, messages }
      │
      ▼
4. POST /chat/turn/continue
   { session_id, message }
```

---

## 6. BE 변경 필요사항

### 6.1 DB 스키마 (선택)

fortune_key를 사용자별로 저장하려면:

```sql
-- 사용자별 fortune_key 저장 (선택적)
CREATE TABLE user_fortunes (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    fortune_type ENUM('eastern', 'western') NOT NULL,
    fortune_key VARCHAR(100) NOT NULL,
    birth_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,  -- Redis TTL과 동기화 (24시간)

    INDEX idx_user_fortune (user_id, fortune_type),
    INDEX idx_fortune_key (fortune_key)
);
```

### 6.2 API 연동

```java
// AI 서버 호출 시 fortune_key 활용
public class AiServerClient {

    // Fortune 분석 후 키 저장
    public FortuneResponse analyzeEastern(EasternFortuneRequest req) {
        FortuneResponse response = aiServer.post("/fortune/eastern", req);

        // fortune_key 저장 (Redis TTL: 24시간)
        saveFortuneKey(req.getUserId(), "eastern", response.getFortuneKey());

        return response;
    }

    // 채팅 시작 시 기존 키 활용
    public TurnResponse startChat(ChatStartRequest req) {
        String easternKey = getFortuneKey(req.getUserId(), "eastern");
        String westernKey = getFortuneKey(req.getUserId(), "western");

        TurnStartRequest aiReq = TurnStartRequest.builder()
            .birthDate(req.getBirthDate())
            .category(req.getCategory())
            .easternFortuneKey(easternKey)  // 있으면 전달
            .westernFortuneKey(westernKey)
            .build();

        return aiServer.post("/chat/turn/start", aiReq);
    }
}
```

### 6.3 Redis 연동 (선택)

AI 서버와 동일한 Redis를 공유하려면:

```yaml
# application.yml
spring:
  redis:
    host: yeji-redis  # Docker 네트워크 내 컨테이너명
    port: 6379
```

---

## 7. FE 변경 필요사항

### 7.1 상태 관리

```typescript
// fortune_key 상태 관리
interface FortuneState {
  easternFortuneKey: string | null;
  westernFortuneKey: string | null;
  easternSummary: string | null;
  westernSummary: string | null;
}

// Zustand / Redux 등에서 관리
const useFortuneStore = create<FortuneState>((set) => ({
  easternFortuneKey: null,
  westernFortuneKey: null,
  easternSummary: null,
  westernSummary: null,

  setEasternKey: (key: string) => set({ easternFortuneKey: key }),
  setWesternKey: (key: string) => set({ westernFortuneKey: key }),
}));
```

### 7.2 API 타입 정의

```typescript
// types/fortune.ts

// Fortune API 응답
interface FortuneResponse {
  fortune_key: string;  // 새로 추가
  element: string;
  stats: FortuneStats;
  fortune_content: FortuneContent;
  lucky: LuckyInfo;
}

// Turn Start 요청
interface TurnStartRequest {
  birth_date: string;
  birth_time?: string;
  category: FortuneCategory;
  char1_code?: string;
  char2_code?: string;
  eastern_fortune_key?: string;  // 새로 추가
  western_fortune_key?: string;  // 새로 추가
}

// Turn Start 응답
interface TurnResponse {
  session_id: string;
  turn: number;
  messages: ChatMessage[];
  suggested_question: string;
  is_complete: boolean;
  eastern_summary?: string;   // 새로 추가
  western_summary?: string;   // 새로 추가
  summary_source?: 'cached' | 'generated';  // 새로 추가
  fortune_source?: 'fortune_key' | 'provided' | 'generated';  // 새로 추가
}
```

### 7.3 API 호출 예시

```typescript
// services/fortune.ts

// 1. Fortune 분석 (결과 + fortune_key 저장)
async function analyzeEasternFortune(birthDate: string, birthTime?: string) {
  const response = await api.post<FortuneResponse>('/fortune/eastern', {
    birth_date: birthDate,
    birth_time: birthTime,
    gender: 'M',
  });

  // fortune_key 저장
  useFortuneStore.getState().setEasternKey(response.fortune_key);

  return response;
}

// 2. 채팅 시작 (fortune_key 활용)
async function startChat(params: {
  birthDate: string;
  category: FortuneCategory;
}) {
  const { easternFortuneKey, westernFortuneKey } = useFortuneStore.getState();

  const response = await api.post<TurnResponse>('/chat/turn/start', {
    birth_date: params.birthDate,
    category: params.category,
    eastern_fortune_key: easternFortuneKey,  // 저장된 키 전달
    western_fortune_key: westernFortuneKey,
  });

  // summary 저장 (UI 표시용)
  if (response.eastern_summary) {
    useFortuneStore.getState().setEasternSummary(response.eastern_summary);
  }

  return response;
}
```

### 7.4 캐릭터 선택 UI

이제 turn/start에서 선택한 캐릭터가 세션 전체에서 유지됨.

```typescript
// 캐릭터 선택 시 저장
const [char1Code, setChar1Code] = useState<CharacterCode>('SOISEOL');
const [char2Code, setChar2Code] = useState<CharacterCode>('STELLA');

// turn/start에 전달
const startChat = async () => {
  await api.post('/chat/turn/start', {
    birth_date: birthDate,
    category: selectedCategory,
    char1_code: char1Code,  // 선택한 캐릭터
    char2_code: char2Code,
  });
};
```

---

## 8. 마이그레이션 가이드

### 8.1 단계별 마이그레이션

| 단계 | 작업 | 하위 호환 |
|------|------|----------|
| 1단계 | AI 서버 v2.0.0.d 배포 | ✅ 기존 API 동작 |
| 2단계 | BE: fortune_key 저장 로직 추가 | ✅ |
| 3단계 | FE: fortune_key 상태 관리 추가 | ✅ |
| 4단계 | FE: turn/start에 fortune_key 전달 | ✅ |
| 5단계 | (선택) Summary API 활용 | ✅ |

### 8.2 하위 호환성

- fortune_key 없이 기존 방식으로 호출해도 동작
- 내부에서 자동으로 fortune 분석 실행
- 단, 매번 LLM 호출로 비용/시간 증가

### 8.3 Redis 요구사항

AI 서버 v2.x는 Redis 연결 필수:

```bash
# Docker 환경
docker run -d --name yeji-redis \
  --network yeji-net \
  -p 6379:6379 \
  redis:7-alpine

# AI 서버 환경변수
REDIS_URL=redis://yeji-redis:6379
```

---

## 부록

### A. 캐릭터 코드 목록

| 코드 | 이름 | 전문 분야 | 말투 |
|------|------|----------|------|
| `SOISEOL` | 소이설 | 동양 사주 | 하오체 |
| `STELLA` | 스텔라 | 서양 점성술 | 해요체 |
| `CHEONGWOON` | 청운 | 동양 (신선) | 하오체 (시적) |
| `HWARIN` | 화린 | 동양 (비즈니스) | 해요체 (나른함) |
| `KYLE` | 카일 | 서양 (도박사) | 반말+존댓말 |
| `ELARIA` | 엘라리아 | 서양 (공주) | 해요체 (우아함) |

### B. 카테고리 목록

| 코드 | 설명 |
|------|------|
| `GENERAL` | 종합운 |
| `LOVE` | 애정운 |
| `MONEY` | 재물운 |
| `CAREER` | 직장운 |
| `HEALTH` | 건강운 |
| `STUDY` | 학업운 |

### C. Redis 키 구조

```
fortune:eastern:1993-07-14:0800:M   # 동양 사주 원본 데이터 (TTL: 24h)
fortune:western:1993-07-14:0800     # 서양 점성술 원본 데이터 (TTL: 24h)
summary:eastern:1993-07-14:0800:M   # 동양 요약본 (TTL: 24h)
summary:western:1993-07-14:0800     # 서양 요약본 (TTL: 24h)
```
