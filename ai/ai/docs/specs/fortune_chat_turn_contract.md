# Fortune Chat Turn Contract v1.0.0

동/서양 티키타카 운세 채팅의 **턴 단위** JSON 응답 계약 명세서

---

## 개요

### 티키타카 컨셉: 동양 vs 서양 대결!

**핵심 아이덴티티**: 소이설(동양 사주)과 스텔라(서양 점성술)가 **서로 다른 관점으로 티격태격하며 대결**하는 운세 상담

- **서로 반박하고 논쟁함**: "잠깐요, 소이설!", "허, 스텔라는 표면만 보는구려"
- **각자의 해석을 자신 있게 주장**: 동양은 깊이, 서양은 밝음
- **대결 끝에 약간의 인정**: "그 점은 인정하오", "뭐, 소이설 말도 일리가..."
- **사용자가 승자를 선택**: "누구 해석이 더 맞는 것 같으세요?"

### 의외의 의견 일치 (매력 포인트!)

**기본은 대결이지만, 가끔 의견이 일치하는 순간이 있어야 더 재미있음**

- 대결 비율: **70~80%** (기본 톤)
- 의견 일치: **20~30%** (의외성, 신뢰감)

**의견 일치 시 패턴**:
```
[EAST] "이건... 스텔라 말이 맞소. 이번엔 동양과 서양이 같은 곳을 가리키고 있구려."
[WEST] "어머, 소이설이 동의하다니! 이건 정말 확실한 거예요!"
```

**효과**:
- "둘이 맨날 싸우더니 이건 같은 말 하네?" → 신뢰도 상승
- 의견 일치 순간의 희소성 → 더 임팩트 있음
- 단조로운 대결만 하면 지루함 → 변화로 재미 유지

### 핵심 원칙

1. **"1턴 = 유저 입력(또는 세션 완료)까지"**
   - 각 턴은 `bubbles[]` + `turn_end`를 반드시 포함
   - `turn_end.type`이 `await_user_input`이면 사용자 입력 대기
   - `turn_end.type`이 `completed`이면 세션 종료

2. **버블 순서 자유 (대결 흐름 유지)**
   - EAST(소이설) / WEST(스텔라) 혼합 순서는 임의
   - 예: 동-서-동, 서-동-서, 동-서-동-서 등
   - **반드시 반박/논쟁 흐름**이 자연스럽게 이어져야 함
   - 합의보다는 **대립 → 약간의 양보** 패턴 권장

3. **감정 표현**
   - 각 버블에 `emotion.code` + `intensity(0~1)` 포함
   - 대결 시 `PLAYFUL`, `CONFIDENT` 코드 권장
   - 페르소나별 기본 톤 권장 (emotion_codebook.md 참조)

4. **턴 확장 정책**
   - 기본 3턴 (`base_turns=3`)
   - 옵션/유료 시 `max_turns`까지 확장 가능

### 대결 대화 패턴 예시

```
[EAST] "귀하의 사주에서 도화살이 보이오. 조심해야 하오."
[WEST] "잠깐요! 금성이 좋은 위치인데 왜 조심하라는 거예요?"
[EAST] "허, 스텔라는 표면만 보는구려. 사주는 깊은 이치를 읽는 것이오."
[WEST] "깊은 이치요? 별들도 충분히 깊어요! 흥!"
```

---

## TurnRequest

사용자가 서버에 보내는 요청

### 스키마

```typescript
interface TurnRequest {
  session_id: string | null;     // 세션 ID (신규 세션은 null)
  turn_id: number | null;        // 응답할 턴 ID (신규 세션은 null)
  user_input?: {                 // Turn 2+ 에서 필수
    prompt_id: string;           // 응답 대상 프롬프트 ID
    value: string;               // 사용자 입력 값
  };
  birth_info?: {                 // Turn 1에서 필수
    birth_date: string;          // YYYY-MM-DD
    birth_time?: string;         // HH:MM (선택)
    birth_place?: string;        // 출생지 (선택)
  };
}
```

### 예시

**Turn 1 (신규 세션)**
```json
{
  "session_id": null,
  "turn_id": null,
  "birth_info": {
    "birth_date": "1990-05-15",
    "birth_time": "14:30"
  }
}
```

**Turn 2+ (기존 세션)**
```json
{
  "session_id": "sess_abc123",
  "turn_id": 2,
  "user_input": {
    "prompt_id": "p001",
    "value": "연애운이 궁금해요"
  }
}
```

---

## TurnResponse

서버가 클라이언트에 반환하는 응답

### 스키마

```typescript
interface TurnResponse {
  session_id: string;            // 세션 고유 ID
  turn_id: number;               // 턴 고유 ID (1부터 시작)
  bubbles: Bubble[];             // 버블 목록 (최소 1개)
  turn_end: TurnEnd;             // 턴 종료 정보
  meta: Meta;                    // 메타 정보
}
```

---

## Bubble

캐릭터 발화 단위

### 스키마

```typescript
interface Bubble {
  bubble_id: string;             // 버블 고유 ID (예: "b001")
  speaker: "EAST" | "WEST";      // 발화 캐릭터
  text: string;                  // 발화 내용 (1~500자)
  emotion: Emotion;              // 감정 정보
  user_input_ref?: string;       // 이전 턴 프롬프트 ID 참조 (Turn 2+)
  timestamp: string;             // ISO 8601 타임스탬프
}

interface Emotion {
  code: EmotionCode;             // 감정 코드 (12종)
  intensity: number;             // 감정 강도 (0.0 ~ 1.0)
}
```

### Speaker enum

| 값 | 캐릭터 | 설명 |
|-----|--------|------|
| `EAST` | 소이설 | 동양 사주학자, 하오체/하게체 |
| `WEST` | 스텔라 | 서양 점성술사, 해요체 |

### 예시

```json
{
  "bubble_id": "b001",
  "speaker": "EAST",
  "text": "귀하의 사주를 살펴보았소. 병화(丙火) 일간이시구려.",
  "emotion": {
    "code": "THOUGHTFUL",
    "intensity": 0.7
  },
  "timestamp": "2026-01-30T10:30:00Z"
}
```

---

## TurnEnd

턴 종료 정보 (상호 배타적)

### Type 1: await_user_input

사용자 입력 대기 상태

```typescript
interface TurnEndAwaitUserInput {
  type: "await_user_input";
  user_prompt: UserPrompt;
}

interface UserPrompt {
  prompt_id: string;             // 프롬프트 고유 ID
  text: string;                  // 안내 문구
  input_schema: InputSchema;     // 입력 스키마
}

interface InputSchema {
  type: "text" | "choice" | "date" | "datetime";
  placeholder?: string;
  options?: Array<{value: string; label: string}>;  // choice 타입용
  validation?: {
    required?: boolean;
    pattern?: string;
    min_length?: number;
    max_length?: number;
  };
}
```

### Type 2: completed

세션 완료 상태

```typescript
interface TurnEndCompleted {
  type: "completed";
  closure: Closure;
}

interface Closure {
  summary: SummaryItem[];        // 세션 요약 (최소 1개)
  next_steps: string[];          // 다음 단계 제안
  upgrade_hook: UpgradeHook;     // 업그레이드 유도
  end_marker: "END_SESSION";     // 종료 마커 (고정값)
}

interface SummaryItem {
  speaker: "EAST" | "WEST";
  key_point: string;
}

interface UpgradeHook {
  enabled: boolean;
  message?: string;              // enabled=true 시 필수
  cta_label?: string;
  cta_action?: string;
}
```

---

## Meta

턴/세션 메타 정보

```typescript
interface Meta {
  current_turn: number;          // 현재 턴 (1~)
  base_turns: number;            // 기본 제공 턴 수 (기본값: 3)
  max_turns: number;             // 최대 가능 턴 수
  is_premium: boolean;           // 프리미엄 여부
  category: FortuneCategory;     // 운세 카테고리
}

type FortuneCategory = "total" | "love" | "wealth" | "career" | "health";
```

---

## 전체 예시

### Turn 1 응답 (await_user_input)

```json
{
  "session_id": "sess_abc123",
  "turn_id": 1,
  "bubbles": [
    {
      "bubble_id": "b001",
      "speaker": "EAST",
      "text": "귀하의 사주를 살펴보았소. 병화(丙火) 일간이시구려. 밝고 열정적인 기운이 가득하오.",
      "emotion": { "code": "THOUGHTFUL", "intensity": 0.7 },
      "timestamp": "2026-01-30T10:30:00Z"
    },
    {
      "bubble_id": "b002",
      "speaker": "WEST",
      "text": "양자리 태양이시네요! 리더십과 추진력이 강한 분이에요.",
      "emotion": { "code": "EXCITED", "intensity": 0.6 },
      "timestamp": "2026-01-30T10:30:05Z"
    },
    {
      "bubble_id": "b003",
      "speaker": "EAST",
      "text": "스텔라도 비슷하게 보았구려. 열정적이고 행동력이 강한 분이오.",
      "emotion": { "code": "WARM", "intensity": 0.5 },
      "timestamp": "2026-01-30T10:30:10Z"
    }
  ],
  "turn_end": {
    "type": "await_user_input",
    "user_prompt": {
      "prompt_id": "p001",
      "text": "더 궁금한 운세가 있으시오?",
      "input_schema": {
        "type": "choice",
        "options": [
          { "value": "love", "label": "연애운" },
          { "value": "wealth", "label": "금전운" },
          { "value": "career", "label": "직장운" },
          { "value": "health", "label": "건강운" }
        ]
      }
    }
  },
  "meta": {
    "current_turn": 1,
    "base_turns": 3,
    "max_turns": 10,
    "is_premium": false,
    "category": "total"
  }
}
```

### Turn 3 응답 (completed, 업그레이드 훅 활성화)

```json
{
  "session_id": "sess_abc123",
  "turn_id": 3,
  "bubbles": [
    {
      "bubble_id": "b007",
      "speaker": "WEST",
      "text": "오늘 상담 정말 즐거웠어요! 별들이 당신의 밝은 미래를 비추고 있어요.",
      "emotion": { "code": "WARM", "intensity": 0.8 },
      "timestamp": "2026-01-30T10:35:00Z"
    },
    {
      "bubble_id": "b008",
      "speaker": "EAST",
      "text": "귀하의 앞날에 좋은 기운이 함께하기를 바라오. 언제든 다시 찾아오시오.",
      "emotion": { "code": "ENCOURAGING", "intensity": 0.7 },
      "timestamp": "2026-01-30T10:35:05Z"
    }
  ],
  "turn_end": {
    "type": "completed",
    "closure": {
      "summary": [
        { "speaker": "EAST", "key_point": "병화 일간으로 열정과 리더십이 강함" },
        { "speaker": "WEST", "key_point": "양자리 태양으로 추진력과 독립심이 뛰어남" }
      ],
      "next_steps": [
        "오늘의 행운 아이템 확인하기",
        "상세 연애운 분석 받기",
        "친구에게 공유하기"
      ],
      "upgrade_hook": {
        "enabled": true,
        "message": "더 깊은 운세 분석을 원하시나요? 프리미엄으로 업그레이드하면 무제한 상담이 가능해요!",
        "cta_label": "프리미엄 시작하기",
        "cta_action": "upgrade_premium"
      },
      "end_marker": "END_SESSION"
    }
  },
  "meta": {
    "current_turn": 3,
    "base_turns": 3,
    "max_turns": 10,
    "is_premium": false,
    "category": "total"
  }
}
```

---

## 검증 규칙

### 필수 규칙

1. **bubbles[] 비어있음 금지**: 모든 턴에서 최소 1개 버블 필수
2. **turn_end 상호 배타**: `await_user_input` 또는 `completed` 중 하나만
3. **completed 턴에서 user_prompt 금지**: 세션 종료 시 추가 입력 요청 불가
4. **end_marker 고정값**: completed 시 반드시 `"END_SESSION"`

### 경고 규칙

1. 버블 3개 초과 시 경고 (권장: 2~3개)
2. 같은 speaker 연속 3회 초과 시 경고
3. text 길이 300자 초과 시 경고

---

## 버전 히스토리

| 버전 | 날짜 | 변경 사항 |
|------|------|----------|
| 1.0.0 | 2026-01-30 | 초기 스키마 정의 |
