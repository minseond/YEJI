# LLM 출력 품질 분석 보고서

> **문서 버전**: 1.0.0
> **작성일**: 2026-01-29
> **분석 대상**: tellang/yeji-8b-rslora-v7-AWQ
> **테스트 환경**: AWS EC2 g6.xlarge + vLLM

---

## 1. 개요

### 1.1 분석 목적

실제 v7 모델의 출력을 Output Convention Spec과 비교하여 **스키마 준수 여부 및 품질 이슈**를 분석합니다.

### 1.2 테스트 조건

| 항목 | 값 |
|------|-----|
| 모델 | tellang/yeji-8b-rslora-v7-AWQ |
| max_tokens | 1500~2048 |
| temperature | 0.7 |
| top_p | 0.9 |
| 프롬프트 | fortune_prompts.py 기반 |

---

## 2. EAST (동양 사주) 분석

### 2.1 실제 응답 (요약)

```json
{
  "element": "FIRE",
  "chart": [
    {"gan": "丙", "ji": "午", "position": 1},
    {"gan": "戊", "ji": "戌", "position": 2},
    {"gan": "辛", "ji": "酉", "position": 3},
    {"gan": "己", "ji": "未", "position": 4},
    {"gan": "乙", "ji": "寅", "position": 5}
  ],
  "stats": {
    "five_elements": {
      "WOOD": 20, "FIRE": 30, "EARTH": 20, "METAL": 20, "WATER": 10
    },
    "yin_yang_ratio": {"yin": 40, "yang": 60},
    "ten_gods": {
      "丙": 10, "戊": 10, "辛": 10, "己": 10, "乙": 10, "ETC": 10
    }
  },
  "lucky": {"number": "7"}
}
```

### 2.2 스키마 불일치 상세

#### 이슈 #1: chart 구조 불일치

| 구분 | 기대값 | 실제값 | 심각도 |
|------|--------|--------|--------|
| 구조 | year/month/day/hour 객체 | position 기반 배열 | **Critical** |
| 개수 | 4개 (년/월/일/시) | 5개 | **Critical** |

**기대 구조:**
```json
{
  "chart": {
    "summary": "string",
    "year": {"gan": "庚", "ji": "午", "element_code": "METAL"},
    "month": {"gan": "己", "ji": "卯", "element_code": "EARTH"},
    "day": {"gan": "甲", "ji": "子", "element_code": "WOOD"},
    "hour": {"gan": "辛", "ji": "未", "element_code": "METAL"}
  }
}
```

**실제 출력:**
```json
{
  "chart": [
    {"gan": "丙", "ji": "午", "position": 1},
    ...
  ]
}
```

**원인 분석:**
- 프롬프트에서 `year/month/day/hour` 구조를 명시했으나 모델이 배열로 해석
- `position` 필드가 임의로 추가됨
- `element_code` 필드 누락
- `summary` 필드 누락

---

#### 이슈 #2: five_elements 구조 불일치

| 구분 | 기대값 | 실제값 | 심각도 |
|------|--------|--------|--------|
| 구조 | list 배열 (code/label/percent) | 객체 (key: value) | **High** |
| label | "목", "화", "토", "금", "수" | 없음 | **High** |

**기대 구조:**
```json
{
  "five_elements": {
    "summary": "string",
    "list": [
      {"code": "WOOD", "label": "목", "percent": 25.0},
      {"code": "FIRE", "label": "화", "percent": 25.0},
      ...
    ]
  }
}
```

**실제 출력:**
```json
{
  "five_elements": {
    "WOOD": 20, "FIRE": 30, "EARTH": 20, "METAL": 20, "WATER": 10
  }
}
```

**원인 분석:**
- 단순 key-value 형태로 출력하여 `list` 배열 구조 무시
- `code`, `label`, `percent` 분리 구조 미준수
- `summary` 필드 누락

---

#### 이슈 #3: ten_gods 코드 불일치

| 구분 | 기대값 | 실제값 | 심각도 |
|------|--------|--------|--------|
| code | BI_GYEON, SIK_SIN 등 | 한자 (丙, 戊 등) | **Critical** |
| label | 비견, 식신 등 | 없음 | **High** |

**기대 구조:**
```json
{
  "ten_gods": {
    "summary": "string",
    "list": [
      {"code": "BI_GYEON", "label": "비견", "percent": 33.3},
      {"code": "SIK_SIN", "label": "식신", "percent": 33.3},
      ...
    ]
  }
}
```

**실제 출력:**
```json
{
  "ten_gods": {
    "丙": 10, "戊": 10, "辛": 10, "己": 10, "乙": 10, "ETC": 10
  }
}
```

**원인 분석:**
- 십신 코드(BI_GYEON 등) 대신 천간 한자(丙, 戊)를 키로 사용
- 십신 계산 로직 자체가 잘못됨 (천간 ≠ 십신)
- 십신은 일간 기준 상대적 관계인데, 단순 천간 나열

---

#### 이슈 #4: 누락된 필수 필드

| 필드 | 상태 | 심각도 |
|------|------|--------|
| chart.summary | 누락 | Medium |
| stats.cheongan_jiji | 누락 | High |
| stats.five_elements.summary | 누락 | Medium |
| stats.yin_yang_ratio.summary | 누락 | Medium |
| stats.ten_gods.summary | 누락 | Medium |
| final_verdict | 전체 누락 | **Critical** |
| lucky.color | 누락 | Medium |
| lucky.item | 누락 | Medium |

---

## 3. WEST (서양 점성술) 분석

### 3.1 실제 응답 (요약)

```json
{
  "element": "AIR",
  "stats": {
    "main_sign": {"name": "물병자리"},
    "element_4_distribution": {
      "FIRE": 25, "EARTH": 25, "AIR": 25, "WATER": 25
    },
    "modality_3_distribution": {
      "fixed": 33.33, "flexible": 33.33, "circular": 33.34
    },
    "keywords": [
      {"name": "창의성", "weight": 0.8},
      {"name": "소통", "weight": 0.7},
      {"name": "변화", "weight": 0.6}
    ]
  },
  "fortune_content": {
    "detailed_analysis": [
      "이 해는 새로운 지적 도전과 창의적 기회가...",
      "주의해야 할 점은 감정의 기복과..."
    ]
  },
  "lucky": {"number": "15"}
}
```

### 3.2 스키마 불일치 상세

#### 이슈 #5: element_4_distribution 구조 불일치

| 구분 | 기대값 | 실제값 | 심각도 |
|------|--------|--------|--------|
| 구조 | list 배열 (code/label/percent) | 객체 (key: value) | **High** |
| label | "불", "흙", "공기", "물" | 없음 | **High** |

**기대 구조:**
```json
{
  "element_4_distribution": [
    {"code": "FIRE", "label": "불", "percent": 25.0},
    {"code": "EARTH", "label": "흙", "percent": 25.0},
    {"code": "AIR", "label": "공기", "percent": 25.0},
    {"code": "WATER", "label": "물", "percent": 25.0}
  ]
}
```

**실제 출력:**
```json
{
  "element_4_distribution": {
    "FIRE": 25, "EARTH": 25, "AIR": 25, "WATER": 25
  }
}
```

---

#### 이슈 #6: modality_3_distribution 코드 불일치

| 구분 | 기대값 | 실제값 | 심각도 |
|------|--------|--------|--------|
| 코드 | CARDINAL, FIXED, MUTABLE | fixed, flexible, circular | **Critical** |
| 구조 | list 배열 | 객체 | **High** |

**기대 구조:**
```json
{
  "modality_3_distribution": [
    {"code": "CARDINAL", "label": "활동", "percent": 33.33},
    {"code": "FIXED", "label": "고정", "percent": 33.33},
    {"code": "MUTABLE", "label": "변동", "percent": 33.34}
  ]
}
```

**실제 출력:**
```json
{
  "modality_3_distribution": {
    "fixed": 33.33, "flexible": 33.33, "circular": 33.34
  }
}
```

**원인 분석:**
- 정의된 코드 (CARDINAL, FIXED, MUTABLE) 대신 임의 영어 단어 사용
- "flexible"은 "MUTABLE"의 의미이지만 다른 단어
- "circular"는 정의되지 않은 용어

---

#### 이슈 #7: keywords 코드 불일치

| 구분 | 기대값 | 실제값 | 심각도 |
|------|--------|--------|--------|
| 필드명 | code | name | **High** |
| 코드값 | EMPATHY, INTUITION 등 | 한글 (창의성, 소통) | **Critical** |
| label | 공감, 직관 등 | 없음 | **High** |

**기대 구조:**
```json
{
  "keywords": [
    {"code": "INNOVATION", "label": "혁신", "weight": 0.9},
    {"code": "COMMUNICATION", "label": "소통", "weight": 0.85},
    ...
  ]
}
```

**실제 출력:**
```json
{
  "keywords": [
    {"name": "창의성", "weight": 0.8},
    {"name": "소통", "weight": 0.7},
    {"name": "변화", "weight": 0.6}
  ]
}
```

**원인 분석:**
- `code` 필드 대신 `name` 필드 사용
- 정의된 키워드 코드 (EMPATHY, INTUITION 등) 대신 임의 한글 사용
- "창의성"은 정의된 키워드 목록에 없음

---

#### 이슈 #8: 누락된 필수 필드

| 필드 | 상태 | 심각도 |
|------|------|--------|
| stats.element_summary | 누락 | **High** |
| stats.modality_summary | 누락 | **High** |
| stats.keywords_summary | 누락 | **High** |
| fortune_content.overview | 누락 | **Critical** |
| fortune_content.advice | 누락 | **Critical** |
| lucky.color | 누락 | Medium |

---

#### 이슈 #9: detailed_analysis 구조 불일치

| 구분 | 기대값 | 실제값 | 심각도 |
|------|--------|--------|--------|
| 구조 | {title, content} 객체 배열 | 문자열 배열 | **High** |

**기대 구조:**
```json
{
  "detailed_analysis": [
    {"title": "내면의 별자리 지도", "content": "..."},
    {"title": "우주가 전하는 메시지", "content": "..."}
  ]
}
```

**실제 출력:**
```json
{
  "detailed_analysis": [
    "이 해는 새로운 지적 도전과...",
    "주의해야 할 점은..."
  ]
}
```

---

## 4. 공통 이슈

### 4.1 응답 반복 문제

| 구분 | 설명 | 심각도 |
|------|------|--------|
| 현상 | 동일 JSON이 여러 번 반복 출력 | **Critical** |
| 원인 | max_tokens 초과 전까지 계속 생성 | - |
| 영향 | JSON 파싱 실패, 토큰 낭비 | High |

**실제 응답 패턴:**
```
{...valid JSON...}
user
다음 사주를 분석하고...
assistant
{...same JSON again...}
```

**원인 분석:**
- `/no_think` 모드에서 stop 토큰 미작동
- 모델이 대화 계속 시뮬레이션
- few-shot 예시 패턴 학습으로 인한 반복

---

### 4.2 톤/언어 규칙 미준수

| 항목 | EAST 기대 | EAST 실제 | WEST 기대 | WEST 실제 |
|------|----------|----------|----------|----------|
| 한자 병기 | 목(木), 화(火) | 없음 | - | - |
| 순수 한글 | - | - | 활동, 고정, 변동 | fixed, flexible, circular |
| summary 필드 | 따뜻한 해석 | 누락 | 시적 해석 | 누락 |

---

## 5. 심각도별 이슈 요약

### 5.1 Critical (즉시 수정 필요)

| ID | 도메인 | 이슈 | Pydantic 검증 |
|----|--------|------|--------------|
| #1 | EAST | chart 구조 불일치 | ValidationError |
| #3 | EAST | ten_gods 코드 불일치 | ValidationError |
| #4 | EAST | final_verdict 누락 | ValidationError |
| #6 | WEST | modality 코드 불일치 | ValidationError |
| #7 | WEST | keywords 코드 불일치 | ValidationError |
| #8 | WEST | overview/advice 누락 | ValidationError |
| #10 | 공통 | 응답 반복 | JSON ParseError |

### 5.2 High (조속히 수정 필요)

| ID | 도메인 | 이슈 |
|----|--------|------|
| #2 | EAST | five_elements 구조 (list vs object) |
| #4 | EAST | cheongan_jiji 누락 |
| #5 | WEST | element_4_distribution 구조 |
| #8 | WEST | summary 필드들 누락 |
| #9 | WEST | detailed_analysis 구조 |

### 5.3 Medium (개선 권장)

| ID | 도메인 | 이슈 |
|----|--------|------|
| #4 | EAST | summary 필드들 누락 |
| #4 | EAST | lucky 세부 필드 누락 |
| #8 | WEST | lucky.color 누락 |

---

## 6. 원인 분석

### 6.1 프롬프트 구조 문제

| 문제 | 설명 | 영향 |
|------|------|------|
| 스키마 복잡도 | 중첩 구조가 깊어 모델이 단순화 | 구조 불일치 |
| 예시 부재 | Few-shot 예시 미제공 | 임의 해석 |
| 제약 조건 분산 | constraints가 길어 일부 무시 | 코드 불일치 |

### 6.2 모델 한계

| 문제 | 설명 | 영향 |
|------|------|------|
| 8B 파라미터 | 복잡한 스키마 완벽 준수 어려움 | 구조 변형 |
| 도메인 지식 | 십신 계산 로직 미학습 | 잘못된 값 |
| 반복 생성 | stop 토큰 인식 부족 | 응답 반복 |

### 6.3 vLLM 설정 문제

| 문제 | 설명 | 해결 방안 |
|------|------|----------|
| stop 토큰 | 명시적 stop 미설정 | `stop: ["}"]` 추가 |
| response_format | json_object 미사용 | 설정 추가 |

---

## 7. 개선 권장사항

### 7.1 프롬프트 개선 (P0)

1. **Few-shot 예시 추가**
   - 완전한 JSON 예시 1~2개 제공
   - 특히 복잡한 구조(chart, ten_gods) 예시 필수

2. **스키마 단순화**
   - 중첩 구조 최소화
   - 필수/선택 필드 명확히 구분

3. **제약 조건 강화**
   - 도메인 코드를 명시적 열거
   - "반드시 다음 중 하나만 사용" 강조

### 7.2 vLLM 설정 개선 (P0)

```python
config = GenerationConfig(
    max_tokens=1500,
    temperature=0.7,
    stop=["\n\n", "user", "assistant"],  # 반복 방지
    response_format={"type": "json_object"},  # JSON 강제
)
```

### 7.3 후처리 로직 추가 (P1)

1. **JSON 추출**
   - 첫 번째 `{...}` 블록만 파싱
   - 반복된 내용 제거

2. **코드 매핑**
   - 잘못된 코드를 올바른 코드로 변환
   - 예: "fixed" → "FIXED", "창의성" → "INNOVATION"

3. **구조 변환**
   - 객체 형태를 list 배열로 변환
   - 누락 필드 기본값 채우기

### 7.4 모델 재학습 고려 (P2)

- 현재 모델이 스키마를 정확히 따르지 못함
- 올바른 구조의 Golden Sample로 추가 파인튜닝 검토
- 또는 larger 모델(70B) 사용 검토

---

## 8. 다음 단계

| 단계 | 작업 | 담당 | 우선순위 |
|------|------|------|----------|
| 1 | 프롬프트에 Few-shot 예시 추가 | AI | P0 |
| 2 | vLLM stop 토큰 설정 | Backend | P0 |
| 3 | JSON 후처리 로직 구현 | Backend | P1 |
| 4 | 개선된 프롬프트로 재테스트 | QA | P1 |
| 5 | G-Eval 평가 파이프라인 구축 | AI | P2 |

---

## 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|----------|
| 1.0.0 | 2026-01-29 | 초기 버전 - v7 모델 출력 분석 |

---

## 9. 프롬프트 개선 후 재테스트 결과 (2026-01-29)

### 9.1 개선 사항

#### 프롬프트 변경 내용

1. **Few-shot 예시 추가**: `<example>` 태그로 완전한 JSON 예시 삽입
2. **제약 조건 강화**: 배열 vs 객체 구조 명확히 구분
3. **금지 사항 명시**: "position 필드 사용 금지", "한자 코드 사용 금지" 등
4. **stop 토큰 추가**: `["\n\nuser", "\nassistant", "<|im_end|>", "<|endoftext|>", "</s>"]`

#### EAST 개선 결과

| 이슈 | 개선 전 | 개선 후 | 상태 |
|------|---------|---------|------|
| #1 chart 구조 | position 배열 | year/month/day/hour 객체 | ✅ **해결** |
| #3 ten_gods 코드 | 한자 (丙, 戊) | 영문 (JEONG_JAE, PYEON_JAE) | ✅ **해결** |
| #4 final_verdict | 누락 | 4개 필드 모두 포함 | ✅ **해결** |
| #2 five_elements | 객체 형태 | list 배열 형태 | ✅ **해결** |

#### WEST 개선 결과

| 이슈 | 개선 전 | 개선 후 | 상태 |
|------|---------|---------|------|
| #5 element_4_distribution | 객체 형태 | 배열 형태 | ✅ **해결** |
| #6 modality 코드 | fixed, flexible, circular | CARDINAL, FIXED, MUTABLE | ✅ **해결** |
| #7 keywords | name 필드, 한글 값 | code 필드, 영문 코드 | ✅ **해결** |
| #9 detailed_analysis | 문자열 배열 | {title, content} 객체 배열 | ✅ **해결** |
| #8 overview/advice | 누락 | 포함됨 | ✅ **해결** |

### 9.2 미해결 이슈

#### 모델 한계 (프롬프트로 해결 불가)

| 이슈 | 설명 | 근본 원인 |
|------|------|-----------|
| #10 응답 반복 | JSON 후 대화 시뮬레이션 계속 | stop 토큰 미인식 |
| 다국어 쓰레기 | 태국어, 아랍어 등 무작위 문자 | 학습 데이터 오염 |
| 반복 패턴 | `"label": "기타"` 무한 반복 | 디코딩 루프 |

### 9.3 권장 대응 방안

#### 즉시 적용 가능 (P0)

```python
# JSON 후처리 로직
def extract_first_json(text: str) -> dict:
    """첫 번째 완전한 JSON만 추출"""
    depth = 0
    start = -1
    for i, char in enumerate(text):
        if char == "{":
            if depth == 0:
                start = i
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0 and start != -1:
                try:
                    return json.loads(text[start:i+1])
                except:
                    start = -1
    raise ValueError("Valid JSON not found")
```

#### 모델 재학습 필요 (P2)

1. **stop 토큰 학습**: 파인튜닝 데이터에 명시적 종료 토큰 포함
2. **다국어 제거**: 한국어/영어/한자만 포함된 데이터로 정제
3. **반복 방지**: repetition_penalty 튜닝 또는 LoRA 재학습

### 9.4 결론

Few-shot 예시 추가로 **스키마 준수율이 크게 개선**되었습니다:

- EAST: 7개 Critical/High 이슈 중 **4개 해결**
- WEST: 5개 Critical/High 이슈 중 **5개 해결**

**남은 문제는 모델 자체의 한계**로, JSON 후처리 로직으로 대응하거나 모델 재학습이 필요합니다.

---

## 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|----------|
| 1.0.0 | 2026-01-29 | 초기 버전 - v7 모델 출력 분석 |
| 1.1.0 | 2026-01-29 | 프롬프트 개선 후 재테스트 결과 추가 |

---

> **Note**: 이 문서는 실제 v7 모델 응답을 기반으로 작성되었습니다.
> 프롬프트 개선으로 스키마 준수율이 크게 향상되었으나, 모델 자체의 반복/다국어 문제는 후처리로 대응해야 합니다.
