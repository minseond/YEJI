# Fortune Key API 변경사항

> **브랜치**: ai/develop
> **작성일**: 2026-02-04
> **목적**: 백엔드 연동을 위한 API 스키마 변경 문서

---

## 1. 개요

### 변경 목적
- 사주/점성 분석 결과를 **재사용**할 수 있도록 `fortune_key` 도입
- **Quick Summary API**로 항목별 상세 해석 제공
- Redis 캐싱으로 중복 LLM 호출 방지

### 영향받는 API
| API | 변경 내용 |
|-----|----------|
| `POST /v1/fortune/eastern` | `fortune_key` 응답 필드 추가 |
| `POST /v1/fortune/western` | `fortune_key` 응답 필드 추가 |
| `POST /v1/fortune/chat/turn/start` | `eastern_fortune_key`, `western_fortune_key` 요청 파라미터 추가 |
| `POST /v1/fortune/quick-summary` | **신규 API** |

---

## 2. Eastern Fortune API 변경

### 엔드포인트
```
POST /v1/fortune/eastern
```

### 요청 (변경 없음)
```json
{
  "birth_date": "1990-05-15",
  "birth_time": "14:30",
  "gender": "M",
  "name": "홍길동"
}
```

### 응답 (fortune_key 추가)
```json
{
  "fortune_key": "eastern:1990-05-15:14:30:M",  // 신규
  "element": "FIRE",
  "chart": {
    "summary": "甲子년 乙丑월 丙寅일",
    "year": {"gan": "甲", "ji": "子", "element_code": "WOOD"},
    "month": {...},
    "day": {...},
    "hour": {...}
  },
  "stats": {
    "cheongan_jiji": {...},
    "five_elements": {"summary": "...", "list": [...]},
    "yin_yang_ratio": {"summary": "...", "yin": 40, "yang": 60},
    "ten_gods": {"summary": "...", "list": [...]}
  },
  "final_verdict": {
    "summary": "...",
    "strength": "...",
    "weakness": "...",
    "advice": "..."
  },
  "lucky": {"color": "빨강", "number": "7", "item": "부적"},
  "_debug_stored": true  // Redis 저장 성공 여부 (개발용)
}
```

### fortune_key 형식
```
eastern:{birth_date}:{birth_time}:{gender}

예시:
- eastern:1990-05-15:14:30:M
- eastern:1990-05-15:unknown:F  (시간 미입력 시)
```

---

## 3. Western Fortune API 변경

### 엔드포인트
```
POST /v1/fortune/western
```

### 요청 (변경 없음)
```json
{
  "birth_date": "1990-05-15",
  "birth_time": "14:30",
  "birth_place": "서울",
  "latitude": 37.5665,
  "longitude": 126.9780
}
```

### 응답 (fortune_key 추가)
```json
{
  "fortune_key": "western:1990-05-15:14:30",  // 신규
  "element": "FIRE",
  "stats": {
    "main_sign": {"name": "황소자리", "code": "TAURUS"},
    "element_summary": "...",
    "element_4_distribution": [...],
    "modality_summary": "...",
    "modality_3_distribution": [...],
    "keywords_summary": "...",
    "keywords": [...]
  },
  "fortune_content": {
    "overview": "...",
    "detailed_analysis": [...]
  },
  "lucky": {"color": "...", "number": "...", "item": "..."},
  "_debug_stored": true
}
```

### fortune_key 형식
```
western:{birth_date}:{birth_time}

예시:
- western:1990-05-15:14:30
- western:1990-05-15:unknown
```

---

## 4. Quick Summary API (신규)

### 엔드포인트
```
POST /v1/fortune/quick-summary
```

### 목적
- 사주/점성 분석 결과에서 **특정 항목의 상세 해석** 제공
- 카테고리(연애운, 금전운 등)에 맞는 맞춤 해석

### 요청
```json
{
  "birth_date": "1990-05-15",
  "birth_time": "14:30",
  "gender": "M",
  "fortune_type": "eastern",  // "eastern" | "western"
  "category": "MONEY",        // LOVE, MONEY, CAREER, HEALTH, STUDY, GENERAL
  "item_code": "FIVE_ELEMENTS" // 선택: 특정 항목만 조회
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `birth_date` | string | O | 생년월일 (YYYY-MM-DD) |
| `birth_time` | string | X | 출생시간 (HH:MM) |
| `gender` | string | X | 성별 (M/F) |
| `fortune_type` | string | O | "eastern" 또는 "western" |
| `category` | string | O | 운세 카테고리 |
| `item_code` | string | X | 특정 항목만 조회 |

### 응답
```json
{
  "fortune_type": "eastern",
  "category": "MONEY",
  "overall": {
    "score": "丙火",           // 동양: 한자, 서양: 숫자
    "keyword": "적극적 투자 성향",
    "summary": "양의 기운이 80%로 강하여 적극적인 자산 관리가 필요합니다."
  },
  "items": [
    {
      "code": "YIN_YANG",
      "name": "음양",
      "score": "양 80%",
      "keyword": "외향적, 적극적",
      "summary": "당신은 양이 80%! 따라서 적극적이고 외향적인 투자계획을 세우세요."
    },
    {
      "code": "FIVE_ELEMENTS",
      "name": "오행",
      "score": "火 40%",
      "keyword": "열정, 추진력",
      "summary": "불의 기운이 강합니다. 급한 투자는 손실로 이어질 수 있어요."
    },
    {
      "code": "TEN_GODS",
      "name": "십신",
      "score": "비견",
      "keyword": "경쟁, 자립",
      "summary": "비견이 강하니 공동 투자보다 단독 투자가 유리합니다."
    }
  ],
  "source": "redis"  // "redis" | "generated"
}
```

### 항목 코드 (item_code)

**동양 (eastern)**:
| 코드 | 이름 | 설명 |
|------|------|------|
| `YIN_YANG` | 음양 | 음양 비율 분석 |
| `FIVE_ELEMENTS` | 오행 | 목화토금수 분석 |
| `TEN_GODS` | 십신 | 비견, 겁재, 식신 등 |
| `CHEONGAN` | 천간 | 갑을병정무기경신임계 |
| `JIJI` | 지지 | 자축인묘진사오미신유술해 |

**서양 (western)**:
| 코드 | 이름 | 설명 |
|------|------|------|
| `ELEMENT` | 4원소 | 불/물/공기/흙 |
| `MODALITY` | 3양태 | 카디널/픽스드/뮤터블 |
| `SIGN` | 별자리 | 12궁 별자리 |
| `HOUSE` | 하우스 | 12하우스 영역 |
| `PLANET` | 행성 | 태양/달/수성 등 |

---

## 5. Chat Turn Start API 변경

### 엔드포인트
```
POST /v1/fortune/chat/turn/start
```

### 요청 (파라미터 추가)
```json
{
  "birth_date": "1990-05-15",
  "birth_time": "14:30",
  "category": "LOVE",
  "char1_code": "SOISEOL",
  "char2_code": "STELLA",

  // 신규 파라미터 (선택)
  "eastern_fortune_key": "eastern:1990-05-15:14:30:M",
  "western_fortune_key": "western:1990-05-15:14:30"
}
```

| 신규 필드 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `eastern_fortune_key` | string | X | 기존 동양 분석 결과 키 |
| `western_fortune_key` | string | X | 기존 서양 분석 결과 키 |

### fortune_key 사용 시 이점
1. **LLM 호출 생략**: Redis에서 캐시된 결과 사용
2. **응답 속도 향상**: 2-3초 → 즉시
3. **토큰 절약**: 분석 재사용으로 비용 절감

### 응답 (필드 추가)
```json
{
  "session_id": "abc12345",
  "turn": 1,
  "messages": [...],
  "suggested_question": "...",
  "is_complete": false,

  // 신규 응답 필드
  "eastern_summary": "음양 균형이 좋고 화기가 강한 사주입니다...",
  "western_summary": "황소자리 태양과 물의 원소가 조화를 이룹니다...",
  "fortune_source": "redis",  // "redis" | "generated" | "provided"
  "summary_source": "cached"  // "cached" | "generated"
}
```

---

## 6. Redis 키 구조

### Fortune 캐싱
```
yeji:eastern:{birth_date}:{birth_time}
yeji:western:{birth_date}:{birth_time}

예시:
- yeji:eastern:1990-05-15:14:30
- yeji:western:1990-05-15:unknown
```

### TTL
- 운세 결과: 24시간 (86400초)
- 세션 데이터: 7일 (604800초)

---

## 7. 백엔드 연동 가이드

### 권장 플로우

```
[사용자 첫 접속]
    ↓
1. POST /fortune/eastern (동양 분석)
   → fortune_key 저장
    ↓
2. POST /fortune/western (서양 분석)
   → fortune_key 저장
    ↓
[운세 결과 페이지]
    ↓
3. POST /fortune/quick-summary (항목별 해석)
   → 사용자가 클릭한 항목 해석 표시
    ↓
[티키타카 채팅]
    ↓
4. POST /chat/turn/start (fortune_key 전달)
   → 기존 분석 재사용
```

### 백엔드 DTO 변경 필요

**요청 DTO 추가 필드**:
```java
// UnseAnalyzeRequest 또는 SajuAiRequest
private String easternFortuneKey;  // 선택
private String westernFortuneKey;  // 선택
```

**응답 DTO 추가 필드**:
```java
// 동양/서양 분석 응답
private String fortuneKey;

// Chat Greeting 응답
private String easternSummary;
private String westernSummary;
private String fortuneSource;
private String summarySource;
```

---

## 8. 변경 이력

| 날짜 | 버전 | 변경 내용 |
|------|------|----------|
| 2026-02-04 | v1.0 | Fortune Key 시스템 도입 |
| 2026-02-04 | v1.0 | Quick Summary API 추가 |
| 2026-02-04 | v1.0 | Chat API fortune_key 파라미터 추가 |
