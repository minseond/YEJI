# Plan: LLM 구조화된 출력 시스템 구현

> 작성일: 2026-01-29
> 상태: Wave 1 진행 중

---

## 1. 가설 (Hypothesis)

프론트엔드 확정 스키마 (`dummyFortuneV2.ts`)와 현재 백엔드 스키마 (`llm_schemas.py`)를 비교 분석한 결과, **스키마 불일치**가 발견되었습니다.

### 핵심 가설
> **프론트엔드 스키마(`UserFortune`)에 맞춘 새로운 Pydantic 모델을 생성하고, 도메인 코드를 엄격히 검증하면, AWS 8B 모델이 유효한 JSON을 생성할 수 있다.**

---

## 2. 스키마 Gap 분석

### 2.1 동양 사주 (Eastern) - Gap 분석

| 필드 | 프론트엔드 스키마 | 백엔드 스키마 | Gap |
|------|------------------|--------------|-----|
| `element` | `string` (WOOD/FIRE/EARTH/METAL/WATER) | 없음 (top-level) | ❌ 추가 필요 |
| `chart.*.gan` | 한자 (甲乙丙丁戊己庚辛壬癸) | 한자 + `gan_code` | ✅ 호환 (한자만 추출) |
| `chart.*.ji` | 한자 (子丑寅卯辰巳午未申酉戌亥) | 한자 + `ji_code` | ✅ 호환 (한자만 추출) |
| `chart.*.element_code` | `string` (WOOD/FIRE/EARTH/METAL/WATER) | `ElementCode` Literal | ✅ 호환 |
| `stats.cheongan_jiji` | 별도 섹션 (chart에서 파생) | 없음 | ⚠️ LLM이 채울 필요 없음 |
| `stats.five_elements.list` | 5개, `code`+`label`+`percent` | 5개, `code`+`label`+`value`+`percent` | ⚠️ `value` 제거 필요 |
| `stats.yin_yang_ratio` | `yin` + `yang` = 100 | `yin` + `yang` + `balance` | ⚠️ `balance` 제거 |
| `stats.ten_gods.list` | 상위 3개 + ETC, `code`+`label`+`percent` | `code`+`label`+`group_code`+`value`+`percent` | ⚠️ `group_code`, `value` 제거 |
| `final_verdict` | `summary`+`strength`+`weakness`+`advice` | 없음 (stats에 포함) | ❌ 추가 필요 |
| `lucky` | `color`+`number`+`item`+`direction?`+`place?` | 더 많은 필드 | ⚠️ 간소화 필요 |

### 2.2 서양 점성술 (Western) - Gap 분석

| 필드 | 프론트엔드 스키마 | 백엔드 스키마 | Gap |
|------|------------------|--------------|-----|
| `element` | `string` (FIRE/EARTH/AIR/WATER) | 없음 (top-level) | ❌ 추가 필요 |
| `stats.main_sign.name` | 한글 별자리 (물병자리, 띄어쓰기X) | `ZodiacCode` (영문) | ❌ 변환 필요 |
| `stats.element_summary` | `string` | 없음 | ❌ 추가 필요 |
| `stats.element_4_distribution` | 4개, `code`+`label`+`percent` | 4개, `code`+`label`+`value`+`percent` | ⚠️ `value` 제거 |
| `stats.modality_summary` | `string` | 없음 | ❌ 추가 필요 |
| `stats.modality_3_distribution` | 3개, `code`+`label`+`percent` | 3개, `code`+`label`+`value`+`percent` | ⚠️ `value` 제거 |
| `stats.keywords_summary` | `string` | 없음 | ❌ 추가 필요 |
| `stats.keywords` | 3~5개, `code`+`label`+`weight` | 없음 | ❌ 추가 필요 |
| `fortune_content` | `overview`+`detailed_analysis`(2개)+`advice` | 없음 | ❌ 추가 필요 |
| `lucky` | `color`+`number`+`item?`+`place?` | 더 많은 필드 | ⚠️ 간소화 필요 |

---

## 3. 도메인 코드 정의 (엄격 준수)

### 3.1 동양 (Eastern)

```python
# 오행 코드
EAST_ELEMENT_CODES = ["WOOD", "FIRE", "EARTH", "METAL", "WATER"]

# 오행 한글 레이블
EAST_ELEMENT_LABELS = {"WOOD": "목", "FIRE": "화", "EARTH": "토", "METAL": "금", "WATER": "수"}

# 십신 코드 (LLM은 상위 3개만 선택, DAY_MASTER와 ETC 제외)
EAST_TEN_GOD_CODES = [
    "BI_GYEON", "GANG_JAE",      # 비겁
    "SIK_SIN", "SANG_GWAN",      # 식상
    "PYEON_JAE", "JEONG_JAE",    # 재성
    "PYEON_GWAN", "JEONG_GWAN",  # 관성
    "PYEON_IN", "JEONG_IN",      # 인성
]

# 십신 한글 레이블
EAST_TEN_GOD_LABELS = {
    "BI_GYEON": "비견", "GANG_JAE": "겁재",
    "SIK_SIN": "식신", "SANG_GWAN": "상관",
    "PYEON_JAE": "편재", "JEONG_JAE": "정재",
    "PYEON_GWAN": "편관", "JEONG_GWAN": "정관",
    "PYEON_IN": "편인", "JEONG_IN": "정인",
}

# 천간 (한자)
CHEON_GAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]

# 지지 (한자)
JI_JI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
```

### 3.2 서양 (Western)

```python
# 4원소 코드
WEST_ELEMENT_CODES = ["FIRE", "EARTH", "AIR", "WATER"]

# 4원소 한글 레이블
WEST_ELEMENT_LABELS = {"FIRE": "불", "EARTH": "흙", "AIR": "공기", "WATER": "물"}

# 3양태 코드
WEST_MODALITY_CODES = ["CARDINAL", "FIXED", "MUTABLE"]

# 3양태 한글 레이블
WEST_MODALITY_LABELS = {"CARDINAL": "활동", "FIXED": "고정", "MUTABLE": "변동"}

# 키워드 코드
WEST_KEYWORD_CODES = [
    "EMPATHY", "INTUITION", "IMAGINATION", "BOUNDARY",
    "LEADERSHIP", "PASSION", "ANALYSIS", "STABILITY",
    "COMMUNICATION", "INNOVATION"
]

# 키워드 한글 레이블
WEST_KEYWORD_LABELS = {
    "EMPATHY": "공감", "INTUITION": "직관", "IMAGINATION": "상상력",
    "BOUNDARY": "경계 설정", "LEADERSHIP": "리더십", "PASSION": "열정",
    "ANALYSIS": "분석", "STABILITY": "안정", "COMMUNICATION": "소통",
    "INNOVATION": "혁신"
}

# 별자리 (한글, 띄어쓰기 없음)
ZODIAC_SIGNS_KR = [
    "양자리", "황소자리", "쌍둥이자리", "게자리",
    "사자자리", "처녀자리", "천칭자리", "전갈자리",
    "사수자리", "염소자리", "물병자리", "물고기자리"
]
```

---

## 4. 검증 규칙 (Validation Rules)

### 4.1 동양 사주 검증

| 규칙 ID | 필드 | 검증 규칙 |
|---------|------|----------|
| E-001 | `element` | `EAST_ELEMENT_CODES` 중 하나 |
| E-002 | `chart.*.gan` | `CHEON_GAN` 10개 중 하나 |
| E-003 | `chart.*.ji` | `JI_JI` 12개 중 하나 |
| E-004 | `chart.*.element_code` | `EAST_ELEMENT_CODES` 중 하나 |
| E-005 | `five_elements.list` | 정확히 5개 |
| E-006 | `five_elements.list[].percent` | 합계 = 100 |
| E-007 | `yin_yang_ratio.yin + yang` | = 100 |
| E-008 | `ten_gods.list` | 상위 3개 (ETC 제외, 또는 ETC 포함 시 4개) |
| E-009 | `ten_gods.list[].code` | `EAST_TEN_GOD_CODES` 중 하나 (ETC 허용) |
| E-010 | `lucky.number` | 아라비아 숫자 문자열 |
| E-011 | `lucky.color/item/direction/place` | 한글 |

### 4.2 서양 점성술 검증

| 규칙 ID | 필드 | 검증 규칙 |
|---------|------|----------|
| W-001 | `element` | `WEST_ELEMENT_CODES` 중 하나 |
| W-002 | `stats.main_sign.name` | `ZODIAC_SIGNS_KR` 중 하나 (띄어쓰기 없음) |
| W-003 | `element_4_distribution` | 정확히 4개 |
| W-004 | `element_4_distribution[].percent` | 합계 = 100 |
| W-005 | `modality_3_distribution` | 정확히 3개 |
| W-006 | `modality_3_distribution[].percent` | 합계 = 100 |
| W-007 | `keywords` | 3~5개 |
| W-008 | `keywords[].code` | `WEST_KEYWORD_CODES` 중 하나 |
| W-009 | `detailed_analysis` | 정확히 2개 |
| W-010 | `lucky.number` | 아라비아 숫자 문자열 |
| W-011 | `lucky.color/item/place` | 한글 |

---

## 5. 설계 (Architecture)

### 5.1 파일 구조

```
ai/src/yeji_ai/
├── models/
│   ├── user_fortune.py        # 새로 생성: 프론트엔드 스키마 매칭
│   │   ├── EastElementCode    # Enum
│   │   ├── WestElementCode    # Enum
│   │   ├── TenGodCode         # Enum (ETC 포함)
│   │   ├── WestKeywordCode    # Enum
│   │   ├── ZodiacSignKR       # Enum (한글 별자리)
│   │   ├── SajuDataV2         # 동양 사주 Pydantic 모델
│   │   ├── WesternFortuneDataV2  # 서양 점성술 Pydantic 모델
│   │   └── UserFortune        # 통합 모델
│   └── enums/
│       └── domain_codes.py    # 도메인 코드 상수
├── prompts/
│   └── fortune_prompts.py     # 새로 생성: 프롬프트 템플릿
│       ├── EASTERN_SYSTEM_PROMPT
│       ├── WESTERN_SYSTEM_PROMPT
│       ├── EASTERN_SCHEMA_INSTRUCTION
│       └── WESTERN_SCHEMA_INSTRUCTION
└── services/
    └── fortune_generator.py   # 새로 생성: LLM 호출 서비스
        ├── generate_eastern()
        ├── generate_western()
        └── generate_full()
```

### 5.2 프롬프트 전략

```
시스템 프롬프트 구조:
1. 역할 정의 (소이설/스텔라 캐릭터)
2. /no_think 모드 지시
3. <constraints> XML 태그로 도메인 코드 제약
4. JSON 스키마 명시
5. 검증 규칙 강조

예시:
<constraints>
element 필드는 반드시 다음 중 하나: WOOD, FIRE, EARTH, METAL, WATER
chart.*.gan 필드는 반드시 다음 중 하나: 甲, 乙, 丙, 丁, 戊, 己, 庚, 辛, 壬, 癸
five_elements.list는 정확히 5개, percent 합계 = 100
...
</constraints>
```

---

## 6. 예상 결과 (Expected Outcomes)

| 지표 | 목표 |
|------|------|
| 스키마 일치율 | 100% (프론트엔드 타입과 완전 호환) |
| 도메인 코드 유효율 | 100% (허용된 값만 사용) |
| percent 합계 정확도 | 100% (항상 100) |
| 테스트 케이스 통과율 | 5개+ 통과 |

---

## 7. 리스크 및 대응

| 리스크 | 확률 | 대응 |
|--------|------|------|
| LLM이 도메인 코드 외 값 생성 | 중 | @field_validator로 강제 검증 |
| percent 합계 != 100 | 중 | @model_validator로 합계 검증 |
| 한자/한글 혼동 | 저 | 명시적 지시 + 예시 제공 |
| 필수 필드 누락 | 저 | Pydantic required 필드로 강제 |

---

## 8. 다음 단계

- [ ] Wave 2: `user_fortune.py` Pydantic 스키마 구현
- [ ] Wave 2: `domain_codes.py` Enum 상수 구현
- [ ] Wave 2: `fortune_prompts.py` 프롬프트 템플릿 구현
- [ ] Wave 2: `fortune_generator.py` 서비스 구현
- [ ] Wave 3: AWS 8B 모델 테스트
