# Chat Summary API 스키마 명세 v1.0.0

## 개요

티키타카 채팅 세션의 운세 분석 결과를 **요약형**으로 제공하는 API 스키마입니다.
동양(eastern)/서양(western) 운세를 **분리된 응답**으로 반환합니다.

---

## 엔드포인트

```
GET /api/v1/fortune/chat/summary/{session_id}
```

### Query Parameters

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `type` | string | ✅ | `eastern` 또는 `western` |

### 예시 요청

```bash
# 동양 운세 요약
GET /api/v1/fortune/chat/summary/abc12345?type=eastern

# 서양 운세 요약
GET /api/v1/fortune/chat/summary/abc12345?type=western
```

---

## 응답 스키마

### FortuneSummaryResponse

```python
class FortuneSummaryResponse(BaseModel):
    """채팅 세션 운세 요약 응답"""

    session_id: str = Field(..., description="세션 ID")
    category: FortuneCategory = Field(..., description="운세 카테고리")
    fortune_type: Literal["eastern", "western"] = Field(..., description="운세 타입")
    fortune: FortuneSummary = Field(..., description="운세 요약 데이터")
```

### FortuneSummary

```python
class FortuneSummary(BaseModel):
    """운세 요약 데이터"""

    character: Literal["SOISEOL", "STELLA"] = Field(..., description="캐릭터 코드")
    score: int = Field(..., ge=0, le=100, description="운세 점수 (0-100)")
    one_line: str = Field(..., min_length=10, max_length=100, description="한 줄 요약")
    keywords: list[str] = Field(..., min_length=2, max_length=5, description="키워드 목록")
    detail: str = Field(..., min_length=50, max_length=500, description="상세 내용")
```

### FortuneCategory

```python
FortuneCategory = Literal["total", "love", "wealth", "career", "health"]
```

---

## 응답 예시

### 예시 1: 동양 운세 (금전운)

```json
{
  "session_id": "abc12345",
  "category": "wealth",
  "fortune_type": "eastern",
  "fortune": {
    "character": "SOISEOL",
    "score": 85,
    "one_line": "목(木) 기운이 강해 재물 운이 상승하는 시기예요",
    "keywords": ["재물운 상승", "투자 적기", "절약 필요"],
    "detail": "일간(甲)을 중심으로 월지(卯)가 같은 기둥이 반복되어 '목(木) 기운'이 강조됩니다. 이번 달은 재물 운이 상승하는 시기로, 새로운 투자나 사업 기회를 적극적으로 검토해 보세요. 다만 수(水)가 약한 편이라 충동적인 지출은 피하는 것이 좋습니다."
  }
}
```

### 예시 2: 서양 운세 (연애운)

```json
{
  "session_id": "abc12345",
  "category": "love",
  "fortune_type": "western",
  "fortune": {
    "character": "STELLA",
    "score": 72,
    "one_line": "물(WATER) 원소가 강해 감성적인 연애 시기야",
    "keywords": ["감성적", "직관", "경계 필요"],
    "detail": "물(WATER) 기질이 강하면 감수성과 공감이 장점이지만, 과몰입을 경계하는 게 좋아. 이번 기간은 감정의 파도가 커질 수 있어. 관계에서는 '상대의 의도 확인 → 내 감정 정리 → 표현' 순서를 지키면 충돌을 줄일 수 있어."
  }
}
```

### 예시 3: 동양 운세 (종합운)

```json
{
  "session_id": "def67890",
  "category": "total",
  "fortune_type": "eastern",
  "fortune": {
    "character": "SOISEOL",
    "score": 78,
    "one_line": "비견/식신/정관 성향이 조화를 이루는 시기예요",
    "keywords": ["자기주도", "표현력", "규칙", "균형"],
    "detail": "비견/식신/정관 성향이 함께 나타나 '자기주도+표현+규칙/기준'이 공존합니다. 자기주도성이 강하고(비견), 표현·실행이 잘 되며(식신), 기준을 세우는 힘(정관)이 있습니다. 다만 수(水)가 약한 편이면 회복 루틴(수면/휴식/감정 정리)을 꾸준히 잡는 것이 중요합니다."
  }
}
```

---

## 필드별 검증 규칙

### score (운세 점수)

| 규칙 | 값 |
|------|-----|
| 타입 | int |
| 최솟값 | 0 |
| 최댓값 | 100 |
| 계산 방식 | stats 기반 가중 평균 |

**계산 로직:**
```python
# Eastern
score = (
    yin_yang_balance_score * 0.3 +    # 음양 균형
    five_elements_score * 0.4 +        # 오행 분포
    ten_gods_score * 0.3               # 십신 분포
)

# Western
score = (
    element_balance_score * 0.4 +      # 4원소 균형
    modality_score * 0.3 +             # 3양태 분포
    keyword_weight_avg * 0.3           # 키워드 가중치
)
```

### one_line (한 줄 요약)

| 규칙 | 값 |
|------|-----|
| 타입 | str |
| 최소 길이 | 10자 |
| 최대 길이 | 100자 |
| 언어 | 한국어 |
| 말투 | eastern=소이설(~요), western=스텔라(~야/~해) |

### keywords (키워드)

| 규칙 | 값 |
|------|-----|
| 타입 | list[str] |
| 최소 개수 | 2개 |
| 최대 개수 | 5개 |
| 각 키워드 길이 | 2-10자 |

**소스:**
- Eastern: `stats.strength`, `stats.weakness`, `five_elements.dominant`
- Western: `stats.keywords[].label`

### detail (상세 내용)

| 규칙 | 값 |
|------|-----|
| 타입 | str |
| 최소 길이 | 50자 |
| 최대 길이 | 500자 |
| 언어 | 한국어 |

---

## 금지 패턴

### 절대 금지

| 패턴 | 이유 |
|------|------|
| 빈 문자열 `""` | 프론트 렌더링 오류 |
| `null` 값 | 필수 필드 누락 |
| `"UNKNOWN"`, `"N/A"` | 무의미한 값 |
| 영문 전용 응답 | 한국어 필수 |
| 이모지 포함 | 일관성 |

### 경고 패턴

| 패턴 | 권장 |
|------|------|
| 100자 초과 one_line | 앞 100자 잘라서 사용 |
| 1개 keyword | 최소 2개 보장 |
| 50자 미만 detail | 폴백 문구 추가 |

---

## 폴백 정책

### 세션 미존재 (404)

```json
{
  "detail": "세션을 찾을 수 없습니다: {session_id}"
}
```

### 분석 결과 미존재 (400)

```json
{
  "detail": "운세 분석이 아직 완료되지 않았습니다. 먼저 채팅을 진행해주세요."
}
```

### score 계산 실패

```python
# 폴백: 기본 점수 50 + 랜덤 ±20
score = 50 + random.randint(-20, 20)
```

### keywords 부족

```python
# 폴백: 기본 키워드 추가
if len(keywords) < 2:
    keywords.extend(["긍정적", "균형"])
```

### detail 부족

```python
# 폴백: 기본 문구 추가
if len(detail) < 50:
    detail += " 더 자세한 운세는 채팅에서 확인해보세요."
```

---

## 에러 응답

### 400 Bad Request

```json
{
  "detail": "type 파라미터는 'eastern' 또는 'western'이어야 합니다."
}
```

### 404 Not Found

```json
{
  "detail": "세션을 찾을 수 없습니다: {session_id}"
}
```

### 500 Internal Server Error

```json
{
  "detail": "요약 생성 중 오류가 발생했습니다: {error_message}"
}
```

---

## 버전 히스토리

| 버전 | 날짜 | 변경 사항 |
|------|------|----------|
| 1.0.0 | 2026-01-30 | 초기 스키마 정의 |
