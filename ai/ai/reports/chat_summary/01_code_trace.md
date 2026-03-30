# Task 1: SUMMARY 생성 지점 코드 트레이스

## 분석 결과

### 현재 상태: SUMMARY 로직 미존재

**결론: chat.py 및 관련 서비스에 SUMMARY 응답 로직이 없습니다.**

---

## 1. 현재 API 구조

### chat.py (활성 라우터)

| 엔드포인트 | 응답 모델 | SUMMARY 포함 |
|-----------|----------|-------------|
| `POST /fortune/chat` | `ChatResponse` | ❌ 없음 |
| `POST /fortune/chat/stream` | SSE | ❌ 없음 |
| `GET /fortune/chat/characters` | dict | ❌ 없음 |

### ChatResponse 현재 구조 (L183-189)

```python
class ChatResponse(BaseModel):
    session_id: str
    turn: int
    messages: list[ChatMessage]
    debate_status: ChatDebateStatus
    ui_hints: ChatUIHints
```

**사용자가 원하는 SUMMARY 필드 없음:**
- ❌ `category`
- ❌ `fortune_type`
- ❌ `fortune` (score, one_line, keywords, detail)

---

## 2. 데이터 흐름 분석

```
[요청] ChatRequest
    ↓
[chat.py:chat()]
    ↓
[TikitakaService]
    ├─ create_greeting_messages() → 인사
    ├─ analyze_both() → Eastern/Western 분석
    ├─ create_interpretation_messages() → LLM 해석
    ├─ create_topic_messages() → 주제별 해석
    └─ handle_choice() → 선택 응답
    ↓
[응답] ChatResponse
```

### 분석 결과 저장 위치

| 데이터 | 위치 | 형식 |
|--------|------|------|
| 동양 분석 | `session.eastern_result` | `EasternFortuneResponse` |
| 서양 분석 | `session.western_result` | `WesternFortuneResponse` |
| 메시지 | `session.messages` | `list[ChatMessage]` |

**SUMMARY 생성 지점: 없음** - 세션에 분석 결과가 저장되지만, 이를 "요약형 응답"으로 변환하는 로직 부재

---

## 3. 프론트엔드 스키마 (dummyFortuneV2.ts)

### 사용자 요청 스키마 (분리형)

```typescript
// 사용자가 원하는 형태
{
  session_id: string;
  category: FortuneCategory;  // "total" | "love" | "wealth" | "career" | "health"
  fortune_type: "eastern" | "western";
  fortune: {
    character: "SOISEOL" | "STELLA";
    score: number;
    one_line: string;
    keywords: string[];
    detail: string;
  }
}
```

### 현재 프론트 스키마 (dummyFortuneV2.ts)

```typescript
// SajuDataV2 (동양)
interface SajuDataV2 {
    chart: SajuChart;
    stats: SajuStats;
    summary: string;        // ← 요약
    message: string;        // ← 상세
    ui_hints: {...};
    category: FortuneCategory;
    lucky: {...};
}

// WesternFortuneDataV2 (서양)
interface WesternFortuneDataV2 {
    summary: string;        // ← 요약
    subSummary: string;
    overview: string;       // ← 상세
    sections: {...}[];
    message: string;
    ...
}
```

---

## 4. SSOT 위치 확정

### 새로 구현해야 할 위치

| 컴포넌트 | 파일 | 역할 |
|----------|------|------|
| **스키마** | `models/fortune/chat.py` | `FortuneSummaryResponse` 모델 추가 |
| **엔드포인트** | `api/v1/fortune/chat.py` | `GET /chat/summary/{session_id}` 추가 |
| **서비스** | `services/tikitaka_service.py` | `create_summary()` 메서드 추가 |

### 데이터 소스

```
session.eastern_result (EasternFortuneResponse)
    └─ summary, stats, chart → fortune_type="eastern"

session.western_result (WesternFortuneResponse)
    └─ summary, stats, chart → fortune_type="western"
```

---

## 5. 필요한 변환 로직

### Eastern → FortuneSummary

```python
{
    "character": "SOISEOL",
    "score": 85,  # stats에서 계산 필요
    "one_line": eastern.summary,  # 또는 새로 생성
    "keywords": [stats.strength 에서 추출],
    "detail": eastern.message
}
```

### Western → FortuneSummary

```python
{
    "character": "STELLA",
    "score": 78,  # stats에서 계산 필요
    "one_line": western.summary,
    "keywords": [stats.keywords에서 추출],
    "detail": western.overview
}
```

---

## Acceptance Criteria ✅

- [x] SUMMARY의 SSOT 위치 확정: **새로 구현 필요**
  - 스키마: `models/fortune/chat.py`
  - 엔드포인트: `api/v1/fortune/chat.py`
  - 서비스: `services/tikitaka_service.py`

---

## 다음 단계

Task 2에서 정확한 스키마 설계 진행:
1. `FortuneSummaryResponse` Pydantic 모델 정의
2. score 계산 로직 설계
3. keywords 추출 로직 설계
4. 폴백 정책 정의
