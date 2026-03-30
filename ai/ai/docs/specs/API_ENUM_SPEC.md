# YEJI AI API - Enum 및 응답 스키마 명세서

> 프론트엔드 TypeScript 타입 정의 및 UI 렌더링을 위한 완전한 Enum/태그 목록

---

## 1. 공통 Enum (Common)

### 1.1 ElementCode (오행)

동양 사주와 서양 점성술 모두에서 사용하는 원소/오행 코드

| Code | 한글 | 한자 | 설명 |
|------|------|------|------|
| `WOOD` | 목 | 木 | 성장, 시작, 봄 |
| `FIRE` | 화 | 火 | 열정, 확장, 여름 |
| `EARTH` | 토 | 土 | 안정, 중심, 환절기 |
| `METAL` | 금 | 金 | 결실, 수렴, 가을 |
| `WATER` | 수 | 水 | 지혜, 저장, 겨울 |

```typescript
type ElementCode = "WOOD" | "FIRE" | "EARTH" | "METAL" | "WATER";
```

### 1.2 YinYangBalance (음양 균형)

| Code | 한글 | 조건 |
|------|------|------|
| `STRONG_YIN` | 음 우세 | 음 > 65% |
| `SLIGHT_YIN` | 약간 음 | 음 55-65% |
| `BALANCED` | 균형 | 45-55% |
| `SLIGHT_YANG` | 약간 양 | 양 55-65% |
| `STRONG_YANG` | 양 우세 | 양 > 65% |

```typescript
type YinYangBalance = "STRONG_YIN" | "SLIGHT_YIN" | "BALANCED" | "SLIGHT_YANG" | "STRONG_YANG";
```

### 1.3 CommonBadge (공통 배지)

프론트엔드 UI 배지 컴포넌트용 태그

```typescript
type CommonBadge =
  // 오행 강약
  | "WOOD_STRONG" | "WOOD_WEAK"
  | "FIRE_STRONG" | "FIRE_WEAK"
  | "EARTH_STRONG" | "EARTH_WEAK"
  | "METAL_STRONG" | "METAL_WEAK"
  | "WATER_STRONG" | "WATER_WEAK"
  // 음양
  | "YIN_DOMINANT" | "YANG_DOMINANT" | "YIN_YANG_BALANCED"
  // 성향
  | "ACTION_ORIENTED"    // 행동파
  | "THOUGHT_ORIENTED"   // 사고파
  | "EMOTION_ORIENTED"   // 감성파
  | "SOCIAL_ORIENTED"    // 사회파
  | "CREATIVE_ORIENTED"; // 창의파
```

### 1.4 ChartType (차트 타입)

추천 차트 렌더링 타입

| Code | 한글 | 용도 |
|------|------|------|
| `PIE` | 원형 차트 | 오행 분포 |
| `RADAR` | 레이더 차트 | 십신/행성 영향력 |
| `BAR` | 막대 차트 | 음양 비율 |
| `WHEEL` | 휠 차트 | 사주 팔자 / 출생 차트 |
| `TIMELINE` | 타임라인 | 대운/운세 흐름 |

```typescript
type ChartType = "PIE" | "RADAR" | "BAR" | "WHEEL" | "TIMELINE";
```

---

## 2. 동양 사주 Enum (Eastern)

### 2.1 CheonGanCode (천간 - 10개)

| Code | 한글 | 한자 | 오행 | 음양 |
|------|------|------|------|------|
| `GAP` | 갑 | 甲 | WOOD | YANG |
| `EUL` | 을 | 乙 | WOOD | YIN |
| `BYEONG` | 병 | 丙 | FIRE | YANG |
| `JEONG` | 정 | 丁 | FIRE | YIN |
| `MU` | 무 | 戊 | EARTH | YANG |
| `GI` | 기 | 己 | EARTH | YIN |
| `GYEONG` | 경 | 庚 | METAL | YANG |
| `SIN` | 신 | 辛 | METAL | YIN |
| `IM` | 임 | 壬 | WATER | YANG |
| `GYE` | 계 | 癸 | WATER | YIN |

```typescript
type CheonGanCode = "GAP" | "EUL" | "BYEONG" | "JEONG" | "MU" | "GI" | "GYEONG" | "SIN" | "IM" | "GYE";
```

### 2.2 JiJiCode (지지 - 12개)

| Code | 한글 | 한자 | 오행 | 음양 | 띠 |
|------|------|------|------|------|-----|
| `JA` | 자 | 子 | WATER | YANG | 쥐 |
| `CHUK` | 축 | 丑 | EARTH | YIN | 소 |
| `IN` | 인 | 寅 | WOOD | YANG | 호랑이 |
| `MYO` | 묘 | 卯 | WOOD | YIN | 토끼 |
| `JIN` | 진 | 辰 | EARTH | YANG | 용 |
| `SA` | 사 | 巳 | FIRE | YIN | 뱀 |
| `O` | 오 | 午 | FIRE | YANG | 말 |
| `MI` | 미 | 未 | EARTH | YIN | 양 |
| `SHIN` | 신 | 申 | METAL | YANG | 원숭이 |
| `YU` | 유 | 酉 | METAL | YIN | 닭 |
| `SUL` | 술 | 戌 | EARTH | YANG | 개 |
| `HAE` | 해 | 亥 | WATER | YIN | 돼지 |

```typescript
type JiJiCode = "JA" | "CHUK" | "IN" | "MYO" | "JIN" | "SA" | "O" | "MI" | "SHIN" | "YU" | "SUL" | "HAE";
```

### 2.3 TenGodCode (십신 - 11개)

| Code | 한글 | 한자 | 그룹 |
|------|------|------|------|
| `DAY_MASTER` | 일간 (나) | 日干 | BI_GYEOP |
| `BI_GYEON` | 비견 | 比肩 | BI_GYEOP |
| `GANG_JAE` | 겁재 | 劫財 | BI_GYEOP |
| `SIK_SIN` | 식신 | 食神 | SIK_SANG |
| `SANG_GWAN` | 상관 | 傷官 | SIK_SANG |
| `PYEON_JAE` | 편재 | 偏財 | JAE_SEONG |
| `JEONG_JAE` | 정재 | 正財 | JAE_SEONG |
| `PYEON_GWAN` | 편관 (칠살) | 偏官 | GWAN_SEONG |
| `JEONG_GWAN` | 정관 | 正官 | GWAN_SEONG |
| `PYEON_IN` | 편인 (효신) | 偏印 | IN_SEONG |
| `JEONG_IN` | 정인 | 正印 | IN_SEONG |

```typescript
type TenGodCode =
  | "DAY_MASTER"
  | "BI_GYEON" | "GANG_JAE"
  | "SIK_SIN" | "SANG_GWAN"
  | "PYEON_JAE" | "JEONG_JAE"
  | "PYEON_GWAN" | "JEONG_GWAN"
  | "PYEON_IN" | "JEONG_IN";
```

### 2.4 TenGodGroupCode (십신 그룹 - 5개)

| Code | 한글 | 의미 | 포함 십신 |
|------|------|------|----------|
| `BI_GYEOP` | 비겁 | 자아, 경쟁, 형제 | 일간, 비견, 겁재 |
| `SIK_SANG` | 식상 | 표현, 재능, 자녀 | 식신, 상관 |
| `JAE_SEONG` | 재성 | 재물, 현실, 아버지 | 편재, 정재 |
| `GWAN_SEONG` | 관성 | 명예, 직업, 남편 | 편관, 정관 |
| `IN_SEONG` | 인성 | 학문, 어머니, 인덕 | 편인, 정인 |

```typescript
type TenGodGroupCode = "BI_GYEOP" | "SIK_SANG" | "JAE_SEONG" | "GWAN_SEONG" | "IN_SEONG";
```

### 2.5 PillarKey (사주 기둥)

| Code | 한글 | 의미 |
|------|------|------|
| `year` | 연주 | 조상, 사회적 환경 |
| `month` | 월주 | 부모, 성장 환경 |
| `day` | 일주 | 본인, 배우자 |
| `hour` | 시주 | 자녀, 말년 |

```typescript
type PillarKey = "year" | "month" | "day" | "hour";
```

### 2.6 EasternBadge (동양 사주 전용 배지)

```typescript
type EasternBadge =
  // 십신 그룹 우세
  | "BI_GYEOP_DOMINANT"    // 비겁 우세
  | "SIK_SANG_DOMINANT"    // 식상 우세
  | "JAE_SEONG_DOMINANT"   // 재성 우세
  | "GWAN_SEONG_DOMINANT"  // 관성 우세
  | "IN_SEONG_DOMINANT"    // 인성 우세
  // 특수 구조 (격국)
  | "GWON_MOK"             // 건록격
  | "YANG_IN"              // 양인격
  | "SIK_SIN_SAENG_JAE"    // 식신생재
  | "GWAN_IN_SANG_SAENG"   // 관인상생
  | "JAE_GWAN_SSANG_MI"    // 재관쌍미
  // 신살
  | "YEOK_MA"              // 역마
  | "DO_HWA"               // 도화
  | "GWAE_GANG";           // 괴강
```

---

## 3. 서양 점성술 Enum (Western)

### 3.1 ZodiacCode (12별자리)

| Code | 한글 | 심볼 | 원소 | 모달리티 | 지배 행성 |
|------|------|------|------|----------|----------|
| `ARIES` | 양자리 | ♈ | FIRE | CARDINAL | MARS |
| `TAURUS` | 황소자리 | ♉ | EARTH | FIXED | VENUS |
| `GEMINI` | 쌍둥이자리 | ♊ | AIR | MUTABLE | MERCURY |
| `CANCER` | 게자리 | ♋ | WATER | CARDINAL | MOON |
| `LEO` | 사자자리 | ♌ | FIRE | FIXED | SUN |
| `VIRGO` | 처녀자리 | ♍ | EARTH | MUTABLE | MERCURY |
| `LIBRA` | 천칭자리 | ♎ | AIR | CARDINAL | VENUS |
| `SCORPIO` | 전갈자리 | ♏ | WATER | FIXED | PLUTO |
| `SAGITTARIUS` | 사수자리 | ♐ | FIRE | MUTABLE | JUPITER |
| `CAPRICORN` | 염소자리 | ♑ | EARTH | CARDINAL | SATURN |
| `AQUARIUS` | 물병자리 | ♒ | AIR | FIXED | URANUS |
| `PISCES` | 물고기자리 | ♓ | WATER | MUTABLE | NEPTUNE |

```typescript
type ZodiacCode =
  | "ARIES" | "TAURUS" | "GEMINI" | "CANCER"
  | "LEO" | "VIRGO" | "LIBRA" | "SCORPIO"
  | "SAGITTARIUS" | "CAPRICORN" | "AQUARIUS" | "PISCES";
```

### 3.2 ZodiacElement (4원소)

| Code | 한글 | 별자리들 |
|------|------|----------|
| `FIRE` | 불 | ARIES, LEO, SAGITTARIUS |
| `EARTH` | 흙 | TAURUS, VIRGO, CAPRICORN |
| `AIR` | 공기 | GEMINI, LIBRA, AQUARIUS |
| `WATER` | 물 | CANCER, SCORPIO, PISCES |

```typescript
type ZodiacElement = "FIRE" | "EARTH" | "AIR" | "WATER";
```

### 3.3 ZodiacModality (3모드)

| Code | 한글 | 의미 | 별자리들 |
|------|------|------|----------|
| `CARDINAL` | 카디널 | 시작, 개척, 리더십 | ARIES, CANCER, LIBRA, CAPRICORN |
| `FIXED` | 고정 | 유지, 안정, 집중력 | TAURUS, LEO, SCORPIO, AQUARIUS |
| `MUTABLE` | 변통 | 변화, 적응, 유연성 | GEMINI, VIRGO, SAGITTARIUS, PISCES |

```typescript
type ZodiacModality = "CARDINAL" | "FIXED" | "MUTABLE";
```

### 3.4 PlanetCode (10행성)

| Code | 한글 | 심볼 | 의미 | 개인행성 |
|------|------|------|------|---------|
| `SUN` | 태양 | ☉ | 자아, 정체성, 활력 | O |
| `MOON` | 달 | ☽ | 감정, 무의식, 어머니 | O |
| `MERCURY` | 수성 | ☿ | 소통, 지성, 학습 | O |
| `VENUS` | 금성 | ♀ | 사랑, 아름다움, 가치 | O |
| `MARS` | 화성 | ♂ | 행동, 욕망, 에너지 | O |
| `JUPITER` | 목성 | ♃ | 행운, 확장, 철학 | X |
| `SATURN` | 토성 | ♄ | 책임, 제한, 훈련 | X |
| `URANUS` | 천왕성 | ♅ | 혁신, 자유, 변화 | X |
| `NEPTUNE` | 해왕성 | ♆ | 영감, 환상, 직관 | X |
| `PLUTO` | 명왕성 | ♇ | 변혁, 권력, 재생 | X |

```typescript
type PlanetCode =
  | "SUN" | "MOON" | "MERCURY" | "VENUS" | "MARS"
  | "JUPITER" | "SATURN" | "URANUS" | "NEPTUNE" | "PLUTO";
```

### 3.5 HouseCode (12하우스)

| Code | 번호 | 한글 | 의미 |
|------|------|------|------|
| `H1_SELF` | 1 | 자아 | 외모, 성격, 첫인상 |
| `H2_POSSESSIONS` | 2 | 재물 | 돈, 소유물, 가치관 |
| `H3_COMMUNICATION` | 3 | 소통 | 형제, 이웃, 단거리 여행 |
| `H4_HOME` | 4 | 가정 | 가족, 뿌리, 부동산 |
| `H5_CREATIVITY` | 5 | 창의/연애 | 연애, 자녀, 취미 |
| `H6_HEALTH` | 6 | 건강/일상 | 건강, 직장, 일상루틴 |
| `H7_PARTNERSHIP` | 7 | 파트너십 | 결혼, 계약, 공개적 적 |
| `H8_TRANSFORMATION` | 8 | 변화/유산 | 성, 죽음, 유산, 타인의 돈 |
| `H9_PHILOSOPHY` | 9 | 철학/여행 | 고등교육, 해외여행, 종교 |
| `H10_CAREER` | 10 | 커리어 | 직업, 명성, 사회적 지위 |
| `H11_COMMUNITY` | 11 | 커뮤니티 | 친구, 희망, 단체활동 |
| `H12_SUBCONSCIOUS` | 12 | 무의식 | 비밀, 고독, 영성 |

```typescript
type HouseCode =
  | "H1_SELF" | "H2_POSSESSIONS" | "H3_COMMUNICATION"
  | "H4_HOME" | "H5_CREATIVITY" | "H6_HEALTH"
  | "H7_PARTNERSHIP" | "H8_TRANSFORMATION" | "H9_PHILOSOPHY"
  | "H10_CAREER" | "H11_COMMUNITY" | "H12_SUBCONSCIOUS";
```

### 3.6 AspectCode (애스펙트)

| Code | 한글 | 심볼 | 각도 | 성질 |
|------|------|------|------|------|
| `CONJUNCTION` | 합 | ☌ | 0° | NEUTRAL |
| `SEXTILE` | 육분위 | ⚹ | 60° | HARMONIOUS |
| `SQUARE` | 스퀘어 | □ | 90° | CHALLENGING |
| `TRINE` | 삼합 | △ | 120° | HARMONIOUS |
| `OPPOSITION` | 충 | ☍ | 180° | CHALLENGING |

```typescript
type AspectCode = "CONJUNCTION" | "SEXTILE" | "SQUARE" | "TRINE" | "OPPOSITION";
type AspectNature = "HARMONIOUS" | "CHALLENGING" | "NEUTRAL";
```

### 3.7 WesternBadge (서양 점성술 전용 배지)

```typescript
type WesternBadge =
  // 원소 우세
  | "FIRE_DOMINANT" | "EARTH_DOMINANT" | "AIR_DOMINANT" | "WATER_DOMINANT"
  // 모달리티 우세
  | "CARDINAL_DOMINANT" | "FIXED_DOMINANT" | "MUTABLE_DOMINANT"
  // 행성 강조
  | "SUN_STRONG" | "MOON_STRONG" | "MERCURY_STRONG" | "VENUS_STRONG" | "MARS_STRONG"
  | "JUPITER_STRONG" | "SATURN_STRONG" | "URANUS_STRONG" | "NEPTUNE_STRONG" | "PLUTO_STRONG"
  // 특수 패턴
  | "GRAND_TRINE"    // 그랜드 트라인
  | "GRAND_CROSS"    // 그랜드 크로스
  | "T_SQUARE"       // T스퀘어
  | "YOD"            // 요드 (신의 손가락)
  | "STELLIUM";      // 스텔리움 (3개 이상 행성 집중)
```

---

## 4. 티키타카 채팅 Enum

### 4.1 CharacterCode (캐릭터)

| Code | 한글 | 전문 분야 | 성격 |
|------|------|----------|------|
| `SOISEOL` | 소이설 | 동양 사주 | 따뜻한 온미녀 |
| `STELLA` | 스텔라 | 서양 점성술 | 쿨한 냉미녀 |

```typescript
type CharacterCode = "SOISEOL" | "STELLA";
```

### 4.2 MessageType (메시지 타입)

| Code | 한글 | 설명 |
|------|------|------|
| `GREETING` | 인사 | 첫 인사 메시지 |
| `INFO_REQUEST` | 정보 요청 | 생년월일 등 요청 |
| `INTERPRETATION` | 해석 | 운세 해석 메시지 |
| `DEBATE` | 토론 | 캐릭터 간 의견 교환 |
| `CONSENSUS` | 합의 | 의견 일치 메시지 |
| `QUESTION` | 후속 질문 | 추가 질문 |
| `CHOICE` | 선택 요청 | 사용자 선택 유도 |

```typescript
type MessageType = "GREETING" | "INFO_REQUEST" | "INTERPRETATION" | "DEBATE" | "CONSENSUS" | "QUESTION" | "CHOICE";
```

---

## 5. API 응답 스키마

### 5.1 동양 사주 응답 (EasternFortuneResponse)

```typescript
interface EasternFortuneResponse {
  category: "eastern";

  // 사주 팔자
  chart: {
    summary: string;  // "갑자년 을축월 병인일 정묘시"
    year: Pillar;
    month: Pillar;
    day: Pillar;
    hour: Pillar | null;
  };

  // 통계 분석
  stats: {
    five_elements: {
      summary: string;
      elements: Array<{ code: ElementCode; label: string; value: number; percent: number }>;
      strong: ElementCode;
      weak: ElementCode;
    };
    yin_yang: {
      summary: string;
      yin: number;
      yang: number;
      balance: YinYangBalance;
    };
    ten_gods: {
      summary: string;
      gods: Array<{ code: TenGodCode; label: string; group_code: TenGodGroupCode; value: number; percent: number }>;
      dominant: TenGodGroupCode;
    };
    strength: string;
    weakness: string;
  };

  // 종합 해석
  summary: string;
  message: string;

  // UI 힌트
  ui_hints: {
    badges: Array<EasternBadge | CommonBadge>;
    recommend_chart: ChartType;
    highlight: {
      day_master: PillarKey;
      strong_element: ElementCode;
      weak_element: ElementCode;
    };
  };

  // 행운 정보
  lucky: {
    color: string;
    color_code: string | null;
    number: string;
    item: string;
    direction: string;
    direction_code: "N" | "NE" | "E" | "SE" | "S" | "SW" | "W" | "NW" | null;
    place: string;
  };
}

interface Pillar {
  gan: string;           // 한자 "甲"
  gan_code: CheonGanCode;
  ji: string;            // 한자 "子"
  ji_code: JiJiCode;
  element_code: ElementCode;
  ten_god_code: TenGodCode;
}
```

### 5.2 서양 점성술 응답 (WesternFortuneResponse)

```typescript
interface WesternFortuneResponse {
  category: "western";

  // 출생 차트
  chart: {
    summary: string;  // "태양 양자리, 달 전갈자리, 상승 사자자리"
    sun: BigThree;
    moon: BigThree;
    rising: BigThree;
    planets: PlanetPlacement[];
    houses: HouseInfo[];
  };

  // 통계 분석
  stats: {
    elements: {
      summary: string;
      distribution: Array<{ code: ZodiacElement; label: string; value: number; percent: number }>;
      dominant: ZodiacElement;
    };
    modality: {
      summary: string;
      distribution: Array<{ code: ZodiacModality; label: string; value: number; percent: number }>;
      dominant: ZodiacModality;
    };
    aspects: {
      summary: string;
      major_aspects: AspectInfo[];
    };
    strength: string;
    weakness: string;
  };

  // 종합 해석
  summary: string;
  message: string;

  // UI 힌트
  ui_hints: {
    badges: Array<WesternBadge | CommonBadge>;
    recommend_chart: ChartType;
    highlight: {
      sun_sign: ZodiacCode;
      moon_sign: ZodiacCode;
      rising_sign: ZodiacCode;
      dominant_planet: PlanetCode;
    };
  };

  // 행운 정보
  lucky: {
    day: string;
    day_code: "MON" | "TUE" | "WED" | "THU" | "FRI" | "SAT" | "SUN" | null;
    color: string;
    color_code: string | null;
    number: string;
    stone: string;
    planet: PlanetCode;
  };
}

interface BigThree {
  sign_code: ZodiacCode;
  house_number: number | null;
  summary: string;
}

interface PlanetPlacement {
  planet_code: PlanetCode;
  sign_code: ZodiacCode;
  house_number: number;
  degree: number;
  minute: number;
  is_retrograde: boolean;
}
```

### 5.3 티키타카 채팅 응답 (ChatResponse)

```typescript
interface ChatResponse {
  session_id: string;
  turn: number;

  messages: Array<{
    character: CharacterCode;
    type: MessageType;
    content: string;
    timestamp: string;
  }>;

  debate_status: {
    is_consensus: boolean;
    eastern_opinion: string | null;
    western_opinion: string | null;
    question: string | null;
  };

  ui_hints: {
    show_choice: boolean;
    choices: Array<{
      value: 1 | 2;
      character: CharacterCode;
      label: string;
    }> | null;
  };
}
```

---

## 6. 프론트엔드 TypeScript 매핑 헬퍼

```typescript
// 십신 한글 매핑
export const TEN_GODS_KOR: Record<TenGodCode, string> = {
  DAY_MASTER: "일간 (나)",
  BI_GYEON: "비견",
  GANG_JAE: "겁재",
  SIK_SIN: "식신",
  SANG_GWAN: "상관",
  PYEON_JAE: "편재",
  JEONG_JAE: "정재",
  PYEON_GWAN: "편관",
  JEONG_GWAN: "정관",
  PYEON_IN: "편인",
  JEONG_IN: "정인",
};

// 천간 한글 매핑
export const CHEONGAN_KOR: Record<CheonGanCode, string> = {
  GAP: "갑", EUL: "을", BYEONG: "병", JEONG: "정", MU: "무",
  GI: "기", GYEONG: "경", SIN: "신", IM: "임", GYE: "계",
};

// 지지 한글 매핑
export const JIJI_KOR: Record<JiJiCode, string> = {
  JA: "자", CHUK: "축", IN: "인", MYO: "묘",
  JIN: "진", SA: "사", O: "오", MI: "미",
  SHIN: "신", YU: "유", SUL: "술", HAE: "해",
};

// 별자리 한글 매핑
export const ZODIAC_KOR: Record<ZodiacCode, string> = {
  ARIES: "양자리", TAURUS: "황소자리", GEMINI: "쌍둥이자리", CANCER: "게자리",
  LEO: "사자자리", VIRGO: "처녀자리", LIBRA: "천칭자리", SCORPIO: "전갈자리",
  SAGITTARIUS: "사수자리", CAPRICORN: "염소자리", AQUARIUS: "물병자리", PISCES: "물고기자리",
};

// 행성 한글 매핑
export const PLANET_KOR: Record<PlanetCode, string> = {
  SUN: "태양", MOON: "달", MERCURY: "수성", VENUS: "금성", MARS: "화성",
  JUPITER: "목성", SATURN: "토성", URANUS: "천왕성", NEPTUNE: "해왕성", PLUTO: "명왕성",
};
```

---

## 7. API 엔드포인트

| Method | Endpoint | 설명 |
|--------|----------|------|
| `POST` | `/api/v1/fortune/eastern` | 동양 사주 분석 |
| `GET` | `/api/v1/fortune/eastern/enums` | 동양 Enum 목록 |
| `POST` | `/api/v1/fortune/western` | 서양 점성술 분석 |
| `GET` | `/api/v1/fortune/western/enums` | 서양 Enum 목록 |
| `POST` | `/api/v1/fortune/chat` | 티키타카 대화 |
| `POST` | `/api/v1/fortune/chat/stream` | 티키타카 SSE 스트리밍 |
| `GET` | `/api/v1/fortune/chat/characters` | 캐릭터 정보 |

---

## 8. 버전 정보

- **문서 버전**: 1.0.0
- **API 버전**: v1
- **최종 업데이트**: 2026-01-27
