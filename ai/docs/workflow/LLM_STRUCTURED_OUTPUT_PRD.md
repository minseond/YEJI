# LLM 구조화된 출력 구현 PRD

> 작성일: 2026-01-29
> 상태: 진행 예정

---

## 1. 개요

### 목표
AWS 8B 모델 (yeji-8b-rslora-v7-AWQ)을 사용하여 프론트엔드 확정 스키마에 맞는 JSON 응답 생성

### 응답 유형
1. **동양 사주 (Eastern)** - `SajuDataV2`
2. **서양 점성술 (Western)** - `WesternFortuneDataV2`
3. ~~티키타카 채팅~~ - 제외 (다이얼로그 제외)

### 핵심 원칙
- 도메인 코드는 **반드시** 정해진 값에서 선택
- 한자/한글/영어 형식 엄격 준수
- 전체 JSON으로 반환

---

## 2. 확정 스키마

### 2.1 동양 사주 (Eastern)

```typescript
interface SajuDataV2 {
  element: ElementCode;  // WOOD|FIRE|EARTH|METAL|WATER

  chart: {
    summary: string;     // LLM 생성
    year: Pillar;
    month: Pillar;
    day: Pillar;
    hour: Pillar;
  };

  stats: {
    cheongan_jiji: {...};  // 천간지지 원형
    five_elements: {
      summary: string;
      list: [{code: ElementCode, label: string, percent: number}] × 5
    };
    yin_yang_ratio: {
      summary: string;
      yin: number;  // 합계 100
      yang: number;
    };
    ten_gods: {
      summary: string;
      list: [{code: TenGodCode, label: string, percent: number}]  // 상위 3개, ETC 제외
    };
  };

  final_verdict: {  // 천기누설 (요약본)
    summary: string;
    strength: string;
    weakness: string;
    advice: string;
  };

  lucky: {
    color: string;      // 한글 (예: "군청색")
    number: string;     // 아라비아 숫자 (예: "1, 6")
    item: string;       // 한글
    direction?: string; // 한글 (예: "북쪽")
    place?: string;     // 한글 (예: "물가, 호수")
  };
}

interface Pillar {
  gan: string;          // 한자 (甲乙丙丁戊己庚辛壬癸)
  ji: string;           // 한자 (子丑寅卯辰巳午未申酉戌亥)
  element_code: ElementCode;
}
```

### 2.2 서양 점성술 (Western)

```typescript
interface WesternFortuneDataV2 {
  element: WestElementCode;  // FIRE|EARTH|AIR|WATER

  stats: {
    main_sign: {
      name: string;  // 한글, 띄어쓰기X (물병자리, 쌍둥이자리)
    };

    element_summary: string;
    element_4_distribution: [{code, label, percent}] × 4;  // 합계 100

    modality_summary: string;
    modality_3_distribution: [{code, label, percent}] × 3;  // CARDINAL|FIXED|MUTABLE, 합계 100

    keywords_summary: string;
    keywords: [{code: KeywordCode, label: string, weight: number}] × 3~5;
  };

  fortune_content: {
    overview: string;           // 의미심장하게
    detailed_analysis: [{title, content}] × 2;  // 2개
    advice: string;             // overview 요약
  };

  lucky: {
    color: string;   // 한글
    number: string;
    item?: string;   // 한글
    place?: string;  // 한글
  };
}
```

---

## 3. 도메인 코드 (엄격 준수)

```python
# 동양 오행
EAST_ELEMENTS = ["WOOD", "FIRE", "EARTH", "METAL", "WATER"]

# 동양 십신
EAST_TEN_GODS = [
    "BI_GYEON", "GANG_JAE",      # 비겁
    "SIK_SIN", "SANG_GWAN",      # 식상
    "PYEON_JAE", "JEONG_JAE",    # 재성
    "PYEON_GWAN", "JEONG_GWAN",  # 관성
    "PYEON_IN", "JEONG_IN",      # 인성
    "DAY_MASTER"                 # 일간
]

# 서양 4원소
WEST_ELEMENTS = ["FIRE", "EARTH", "AIR", "WATER"]

# 서양 3양태
WEST_MODALITIES = ["CARDINAL", "FIXED", "MUTABLE"]

# 서양 키워드
WEST_KEYWORDS = [
    "EMPATHY", "INTUITION", "IMAGINATION", "BOUNDARY",
    "LEADERSHIP", "PASSION", "ANALYSIS", "STABILITY",
    "COMMUNICATION", "INNOVATION"
]

# 별자리 (띄어쓰기 없이)
ZODIAC_SIGNS = [
    "양자리", "황소자리", "쌍둥이자리", "게자리",
    "사자자리", "처녀자리", "천칭자리", "전갈자리",
    "사수자리", "염소자리", "물병자리", "물고기자리"
]

# 천간 (한자)
CHEON_GAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]

# 지지 (한자)
JI_JI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
```

---

## 4. 검증 규칙

| 필드 | 규칙 |
|------|------|
| `element` | 도메인 코드에서 선택 |
| `chart.*.gan` | CHEON_GAN 10개 중 하나 |
| `chart.*.ji` | JI_JI 12개 중 하나 |
| `five_elements.list` | 5개, percent 합계 = 100 |
| `ten_gods.list` | 3개 (상위), ETC 제외 |
| `yin_yang_ratio` | yin + yang = 100 |
| `main_sign.name` | ZODIAC_SIGNS 12개 중 하나, 띄어쓰기X |
| `element_4_distribution` | 4개, percent 합계 = 100 |
| `modality_3_distribution` | 3개, percent 합계 = 100 |
| `keywords` | 3~5개, 도메인 코드 |
| `detailed_analysis` | 2개 |
| `lucky.*` | number만 아라비아, 나머지 한글 |

---

## 5. 참고 예시 (dummyFortuneV2.ts)

실제 더미 데이터 5개 참고:
- Wood/Pisces, Fire/Leo, Water/Capricorn, Metal/Gemini, Earth/Taurus

---

## 6. 제외 항목

- 다이얼로그 (티키타카 채팅) - 일단 제외
- `cheongan_jiji` 섹션 - 있지만 LLM이 채울 필요 없음 (chart에서 파생)
