"""LLM 구조화된 출력을 위한 Pydantic 스키마

api_enum_spec.json의 EasternFortuneResponse / WesternFortuneResponse 스펙과 일치하도록 설계.

Qwen3 프롬프팅 가이드 적용:
- /no_think 모드 사용
- <constraints> XML 태그로 도메인 제약
- presence_penalty=1.5 권장
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# ============================================================
# 공통 Enum 타입 - api_enum_spec.json/enums/common
# ============================================================

ElementCode = Literal["WOOD", "FIRE", "EARTH", "METAL", "WATER"]

YinYangBalance = Literal[
    "STRONG_YIN", "SLIGHT_YIN", "BALANCED", "SLIGHT_YANG", "STRONG_YANG"
]

ChartType = Literal["PIE", "RADAR", "BAR", "WHEEL", "TIMELINE"]

DirectionCode = Literal["N", "NE", "E", "SE", "S", "SW", "W", "NW"]

DayCode = Literal["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]

# 공통 배지 - api_enum_spec.json/enums/common/CommonBadge
CommonBadge = Literal[
    "WOOD_STRONG", "WOOD_WEAK",
    "FIRE_STRONG", "FIRE_WEAK",
    "EARTH_STRONG", "EARTH_WEAK",
    "METAL_STRONG", "METAL_WEAK",
    "WATER_STRONG", "WATER_WEAK",
    "YIN_DOMINANT", "YANG_DOMINANT", "YIN_YANG_BALANCED",
    "ACTION_ORIENTED", "THOUGHT_ORIENTED",
    "EMOTION_ORIENTED", "SOCIAL_ORIENTED", "CREATIVE_ORIENTED",
]


# ============================================================
# 동양 사주 Enum 타입 - api_enum_spec.json/enums/eastern
# ============================================================

CheonGanCode = Literal[
    "GAP", "EUL", "BYEONG", "JEONG", "MU",
    "GI", "GYEONG", "SIN", "IM", "GYE"
]

JiJiCode = Literal[
    "JA", "CHUK", "IN", "MYO", "JIN", "SA",
    "O", "MI", "SHIN", "YU", "SUL", "HAE"
]

TenGodCode = Literal[
    "DAY_MASTER",
    "BI_GYEON", "GANG_JAE",
    "SIK_SIN", "SANG_GWAN",
    "PYEON_JAE", "JEONG_JAE",
    "PYEON_GWAN", "JEONG_GWAN",
    "PYEON_IN", "JEONG_IN",
]

TenGodGroupCode = Literal[
    "BI_GYEOP", "SIK_SANG", "JAE_SEONG", "GWAN_SEONG", "IN_SEONG"
]

PillarKey = Literal["year", "month", "day", "hour"]

# 동양 사주 전용 배지 - api_enum_spec.json/enums/eastern/EasternBadge
EasternBadge = Literal[
    "BI_GYEOP_DOMINANT", "SIK_SANG_DOMINANT", "JAE_SEONG_DOMINANT",
    "GWAN_SEONG_DOMINANT", "IN_SEONG_DOMINANT",
    "GWON_MOK", "YANG_IN", "SIK_SIN_SAENG_JAE",
    "GWAN_IN_SANG_SAENG", "JAE_GWAN_SSANG_MI",
    "YEOK_MA", "DO_HWA", "GWAE_GANG",
]


# ============================================================
# 서양 점성술 Enum 타입 - api_enum_spec.json/enums/western
# ============================================================

ZodiacCode = Literal[
    "ARIES", "TAURUS", "GEMINI", "CANCER",
    "LEO", "VIRGO", "LIBRA", "SCORPIO",
    "SAGITTARIUS", "CAPRICORN", "AQUARIUS", "PISCES",
]

ZodiacElement = Literal["FIRE", "EARTH", "AIR", "WATER"]

ZodiacModality = Literal["CARDINAL", "FIXED", "MUTABLE"]

PlanetCode = Literal[
    "SUN", "MOON", "MERCURY", "VENUS", "MARS",
    "JUPITER", "SATURN", "URANUS", "NEPTUNE", "PLUTO",
]

AspectCode = Literal["CONJUNCTION", "SEXTILE", "SQUARE", "TRINE", "OPPOSITION"]

AspectNature = Literal["HARMONIOUS", "CHALLENGING", "NEUTRAL"]

# 서양 점성술 전용 배지 - api_enum_spec.json/enums/western/WesternBadge
WesternBadge = Literal[
    "FIRE_DOMINANT", "EARTH_DOMINANT", "AIR_DOMINANT", "WATER_DOMINANT",
    "CARDINAL_DOMINANT", "FIXED_DOMINANT", "MUTABLE_DOMINANT",
    "SUN_STRONG", "MOON_STRONG", "MERCURY_STRONG", "VENUS_STRONG",
    "MARS_STRONG", "JUPITER_STRONG", "SATURN_STRONG",
    "URANUS_STRONG", "NEPTUNE_STRONG", "PLUTO_STRONG",
    "GRAND_TRINE", "GRAND_CROSS", "T_SQUARE", "YOD", "STELLIUM",
]


# ============================================================
# 동양 사주 스키마 - EasternFortuneResponse
# ============================================================

class Pillar(BaseModel):
    """사주 기둥 - api_enum_spec.json/schemas/Pillar"""
    gan: str = Field(..., description="천간 한자 (甲乙丙丁戊己庚辛壬癸)")
    gan_code: CheonGanCode = Field(..., description="천간 코드")
    ji: str = Field(..., description="지지 한자 (子丑寅卯辰巳午未申酉戌亥)")
    ji_code: JiJiCode = Field(..., description="지지 코드")
    element_code: ElementCode = Field(..., description="오행 코드")
    ten_god_code: TenGodCode = Field(..., description="십신 코드")


class EasternChart(BaseModel):
    """동양 사주 차트 - EasternFortuneResponse.chart"""
    summary: str = Field(..., description="차트 요약")
    year: Pillar = Field(..., description="년주")
    month: Pillar = Field(..., description="월주")
    day: Pillar = Field(..., description="일주")
    hour: Pillar | None = Field(None, description="시주 (없을 수 있음)")


class FiveElementItem(BaseModel):
    """오행 항목"""
    code: ElementCode = Field(..., description="오행 코드")
    label: str = Field(..., description="오행 한글 (목/화/토/금/수)")
    value: int = Field(..., ge=0, description="개수")
    percent: float = Field(..., ge=0, le=100, description="비율 (%)")


class FiveElements(BaseModel):
    """오행 분포 - EasternFortuneResponse.stats.five_elements"""
    summary: str = Field(..., description="오행 분석 요약")
    elements: list[FiveElementItem] = Field(
        ..., min_length=5, max_length=5, description="오행 분포"
    )
    strong: ElementCode = Field(..., description="강한 오행")
    weak: ElementCode = Field(..., description="약한 오행")


class YinYang(BaseModel):
    """음양 비율 - EasternFortuneResponse.stats.yin_yang"""
    summary: str = Field(..., description="음양 균형 설명")
    yin: float = Field(..., ge=0, le=100, description="음 비율 (%)")
    yang: float = Field(..., ge=0, le=100, description="양 비율 (%)")
    balance: YinYangBalance = Field(..., description="균형 상태 코드")


class TenGodItem(BaseModel):
    """십신 항목"""
    code: TenGodCode = Field(..., description="십신 코드")
    label: str = Field(..., description="십신 한글")
    group_code: TenGodGroupCode = Field(..., description="십신 그룹 코드")
    value: int = Field(..., ge=0, description="개수")
    percent: float = Field(..., ge=0, le=100, description="비율 (%)")


class TenGods(BaseModel):
    """십신 분포 - EasternFortuneResponse.stats.ten_gods"""
    summary: str = Field(..., description="십신 분석 요약")
    gods: list[TenGodItem] = Field(..., min_length=1, description="십신 목록")
    dominant: TenGodGroupCode = Field(..., description="우세 십신 그룹")


class EasternStats(BaseModel):
    """동양 사주 통계 - EasternFortuneResponse.stats"""
    five_elements: FiveElements = Field(..., description="오행 분포")
    yin_yang: YinYang = Field(..., description="음양 비율")
    ten_gods: TenGods = Field(..., description="십신 분포")
    strength: str = Field(..., description="강점 분석")
    weakness: str = Field(..., description="약점 분석")


class EasternHighlight(BaseModel):
    """동양 사주 하이라이트 - EasternFortuneResponse.ui_hints.highlight"""
    day_master: PillarKey = Field(default="day", description="일간 위치")
    strong_element: ElementCode = Field(..., description="강한 오행")
    weak_element: ElementCode = Field(..., description="약한 오행")


class EasternUIHints(BaseModel):
    """동양 사주 UI 힌트 - EasternFortuneResponse.ui_hints"""
    badges: list[str] = Field(..., min_length=2, max_length=6, description="배지 코드 목록")
    recommend_chart: ChartType = Field(..., description="추천 차트 타입")
    highlight: EasternHighlight = Field(..., description="하이라이트")


class EasternLucky(BaseModel):
    """동양 사주 행운 정보 - EasternFortuneResponse.lucky"""
    color: str = Field(..., description="행운의 색상 (한글)")
    color_code: str | None = Field(None, description="색상 HEX 코드")
    number: str = Field(..., description="행운의 숫자")
    item: str = Field(..., description="행운의 아이템")
    direction: str = Field(..., description="행운의 방향 (한글)")
    direction_code: DirectionCode | None = Field(None, description="방향 코드")
    place: str = Field(..., description="행운의 장소")


class EasternFortuneResponse(BaseModel):
    """동양 사주 전체 응답 - api_enum_spec.json/schemas/EasternFortuneResponse

    LLM이 생성하는 완전한 동양 사주 분석 결과입니다.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "category": "eastern",
                "chart": {
                    "summary": (
                        "일간(甲)을 중심으로 월지(卯)가 반복되어 "
                        "'목(木) 기운'이 강조됩니다."
                    ),
                    "year": {
                        "gan": "己",
                        "gan_code": "GI",
                        "ji": "卯",
                        "ji_code": "MYO",
                        "element_code": "EARTH",
                        "ten_god_code": "JEONG_JAE",
                    },
                    "month": {
                        "gan": "丁",
                        "gan_code": "JEONG",
                        "ji": "卯",
                        "ji_code": "MYO",
                        "element_code": "FIRE",
                        "ten_god_code": "SANG_GWAN",
                    },
                    "day": {
                        "gan": "甲",
                        "gan_code": "GAP",
                        "ji": "子",
                        "ji_code": "JA",
                        "element_code": "WOOD",
                        "ten_god_code": "DAY_MASTER",
                    },
                    "hour": {
                        "gan": "辛",
                        "gan_code": "SIN",
                        "ji": "未",
                        "ji_code": "MI",
                        "element_code": "METAL",
                        "ten_god_code": "JEONG_GWAN",
                    },
                },
                "stats": {
                    "five_elements": {
                        "summary": "목(木)이 강하고 수(水)가 약합니다.",
                        "elements": [
                            {"code": "WOOD", "label": "목", "value": 3, "percent": 37.5},
                            {"code": "FIRE", "label": "화", "value": 2, "percent": 25.0},
                            {"code": "EARTH", "label": "토", "value": 1, "percent": 12.5},
                            {"code": "METAL", "label": "금", "value": 2, "percent": 25.0},
                            {"code": "WATER", "label": "수", "value": 0, "percent": 0.0}
                        ],
                        "strong": "WOOD",
                        "weak": "WATER"
                    },
                    "yin_yang": {
                        "summary": "음/양 균형은 약간 음(陰) 쪽으로 치우쳐 있습니다.",
                        "yin": 55.0,
                        "yang": 45.0,
                        "balance": "SLIGHT_YIN"
                    },
                    "ten_gods": {
                        "summary": "비겁이 우세하여 자기주도성이 강합니다.",
                        "gods": [
                            {
                                "code": "BI_GYEON",
                                "label": "비견",
                                "group_code": "BI_GYEOP",
                                "value": 2,
                                "percent": 33.3,
                            },
                            {
                                "code": "SIK_SIN",
                                "label": "식신",
                                "group_code": "SIK_SANG",
                                "value": 2,
                                "percent": 33.3,
                            },
                            {
                                "code": "JEONG_GWAN",
                                "label": "정관",
                                "group_code": "GWAN_SEONG",
                                "value": 1,
                                "percent": 16.7,
                            }
                        ],
                        "dominant": "BI_GYEOP"
                    },
                    "strength": "자기주도성이 강하고 표현·실행력이 뛰어납니다.",
                    "weakness": "수(水)가 약하여 휴식과 회복 루틴이 필요합니다."
                },
                "summary": "목(木)이 강한 리더형, 수(水) 보완 필요",
                "message": (
                    "사주 기준으로는 '강한 추진력 + 표현력'이 장점입니다. "
                    "다만 수(水)가 약한 편이니 휴식 루틴을 꾸준히 잡으세요."
                ),
                "ui_hints": {
                    "badges": ["WOOD_STRONG", "WATER_WEAK", "BI_GYEOP_DOMINANT", "ACTION_ORIENTED"],
                    "recommend_chart": "PIE",
                    "highlight": {
                        "day_master": "day",
                        "strong_element": "WOOD",
                        "weak_element": "WATER",
                    }
                },
                "lucky": {
                    "color": "군청색",
                    "color_code": "#191970",
                    "number": "1, 6",
                    "item": "수정 팔찌",
                    "direction": "북쪽",
                    "direction_code": "N",
                    "place": "물가, 호수"
                }
            }
        }
    )

    category: Literal["eastern"] = Field(default="eastern", description="카테고리")
    chart: EasternChart = Field(..., description="사주 차트")
    stats: EasternStats = Field(..., description="사주 통계")
    summary: str = Field(..., description="종합 요약")
    message: str = Field(..., description="사용자에게 전달할 메시지")
    ui_hints: EasternUIHints = Field(..., description="UI 힌트")
    lucky: EasternLucky = Field(..., description="행운 정보")


# ============================================================
# 서양 점성술 스키마 - WesternFortuneResponse
# ============================================================

class BigThree(BaseModel):
    """빅3 항목 - api_enum_spec.json/schemas/BigThree"""
    sign_code: ZodiacCode = Field(..., description="별자리 코드")
    house_number: int | None = Field(None, ge=1, le=12, description="하우스 번호")
    summary: str = Field(..., description="요약")


class PlanetPlacement(BaseModel):
    """행성 배치 - api_enum_spec.json/schemas/PlanetPlacement"""
    planet_code: PlanetCode = Field(..., description="행성 코드")
    sign_code: ZodiacCode = Field(..., description="별자리 코드")
    house_number: int = Field(..., ge=1, le=12, description="하우스 번호")
    degree: float = Field(..., ge=0, lt=30, description="도수 (0-29)")
    minute: int = Field(..., ge=0, lt=60, description="분 (0-59)")
    is_retrograde: bool = Field(default=False, description="역행 여부")


class WesternChart(BaseModel):
    """서양 점성술 차트 - WesternFortuneResponse.chart"""
    summary: str = Field(..., description="차트 요약")
    sun: BigThree = Field(..., description="태양")
    moon: BigThree = Field(..., description="달")
    rising: BigThree = Field(..., description="상승궁")
    planets: list[PlanetPlacement] = Field(..., description="행성 배치 목록")


class ElementDistribution(BaseModel):
    """원소 분포 항목"""
    code: ZodiacElement = Field(..., description="원소 코드")
    label: str = Field(..., description="원소 한글")
    value: int = Field(..., ge=0, description="개수")
    percent: float = Field(..., ge=0, le=100, description="비율 (%)")


class WesternElements(BaseModel):
    """원소 분포 - WesternFortuneResponse.stats.elements"""
    summary: str = Field(..., description="원소 분석 요약")
    distribution: list[ElementDistribution] = Field(..., min_length=4, max_length=4)
    dominant: ZodiacElement = Field(..., description="우세 원소")


class ModalityDistribution(BaseModel):
    """모달리티 분포 항목"""
    code: ZodiacModality = Field(..., description="모달리티 코드")
    label: str = Field(..., description="모달리티 한글")
    value: int = Field(..., ge=0, description="개수")
    percent: float = Field(..., ge=0, le=100, description="비율 (%)")


class WesternModality(BaseModel):
    """모달리티 분포 - WesternFortuneResponse.stats.modality"""
    summary: str = Field(..., description="모달리티 분석 요약")
    distribution: list[ModalityDistribution] = Field(..., min_length=3, max_length=3)
    dominant: ZodiacModality = Field(..., description="우세 모달리티")


class AspectItem(BaseModel):
    """애스펙트 항목"""
    planet1: PlanetCode = Field(..., description="첫 번째 행성")
    planet2: PlanetCode = Field(..., description="두 번째 행성")
    aspect_code: AspectCode = Field(..., description="애스펙트 코드")
    nature: AspectNature = Field(..., description="애스펙트 성질")
    orb: float = Field(..., ge=0, description="오브 (허용 오차)")


class WesternAspects(BaseModel):
    """애스펙트 - WesternFortuneResponse.stats.aspects"""
    summary: str = Field(..., description="애스펙트 분석 요약")
    major_aspects: list[AspectItem] = Field(..., description="주요 애스펙트 목록")


class WesternStats(BaseModel):
    """서양 점성술 통계 - WesternFortuneResponse.stats"""
    elements: WesternElements = Field(..., description="원소 분포")
    modality: WesternModality = Field(..., description="모달리티 분포")
    aspects: WesternAspects = Field(..., description="애스펙트")
    strength: str = Field(..., description="강점 분석")
    weakness: str = Field(..., description="약점 분석")


class WesternHighlight(BaseModel):
    """서양 점성술 하이라이트 - WesternFortuneResponse.ui_hints.highlight"""
    sun_sign: ZodiacCode = Field(..., description="태양 별자리")
    moon_sign: ZodiacCode = Field(..., description="달 별자리")
    rising_sign: ZodiacCode = Field(..., description="상승 별자리")
    dominant_planet: PlanetCode = Field(..., description="지배 행성")


class WesternUIHints(BaseModel):
    """서양 점성술 UI 힌트 - WesternFortuneResponse.ui_hints"""
    badges: list[str] = Field(..., min_length=2, max_length=6, description="배지 코드 목록")
    recommend_chart: ChartType = Field(..., description="추천 차트 타입")
    highlight: WesternHighlight = Field(..., description="하이라이트")


class WesternLucky(BaseModel):
    """서양 점성술 행운 정보 - WesternFortuneResponse.lucky"""
    day: str = Field(..., description="행운의 요일 (한글)")
    day_code: DayCode | None = Field(None, description="요일 코드")
    color: str = Field(..., description="행운의 색상 (한글)")
    color_code: str | None = Field(None, description="색상 HEX 코드")
    number: str = Field(..., description="행운의 숫자")
    stone: str = Field(..., description="행운의 보석")
    planet: PlanetCode = Field(..., description="행운의 행성")


class WesternFortuneResponse(BaseModel):
    """서양 점성술 전체 응답 - api_enum_spec.json/schemas/WesternFortuneResponse

    LLM이 생성하는 완전한 서양 점성술 분석 결과입니다.
    """
    category: Literal["western"] = Field(default="western", description="카테고리")
    chart: WesternChart = Field(..., description="차트")
    stats: WesternStats = Field(..., description="통계")
    summary: str = Field(..., description="종합 요약")
    message: str = Field(..., description="사용자에게 전달할 메시지")
    ui_hints: WesternUIHints = Field(..., description="UI 힌트")
    lucky: WesternLucky = Field(..., description="행운 정보")


# ============================================================
# 레거시 호환 스키마
# ============================================================

class EasternLuckyInfo(BaseModel):
    """동양 사주 행운 정보 (레거시)"""
    color: str = Field(..., description="행운의 색상")
    number: str = Field(..., description="행운의 숫자")
    item: str = Field(..., description="행운의 아이템")
    direction: str = Field(..., description="행운의 방향")
    place: str = Field(..., description="행운의 장소")


class WesternLuckyInfo(BaseModel):
    """서양 점성술 행운 정보 (레거시)"""
    day: str = Field(..., description="행운의 요일")
    day_code: str = Field(..., description="요일 코드")
    color: str = Field(..., description="행운의 색상")
    color_code: str = Field(..., description="색상 HEX 코드")
    number: str = Field(..., description="행운의 숫자")
    stone: str = Field(..., description="행운의 보석")


class KeywordItem(BaseModel):
    """키워드 항목 - 서양 점성술 keywords 배열용"""
    code: str = Field(..., description="키워드 코드 (영문 대문자, 예: INTUITION, CREATIVITY)")
    label: str = Field(..., description="키워드 한글 (예: 직관, 창의성)")
    weight: float = Field(..., ge=0.0, le=1.0, description="중요도 (0.0~1.0)")


class EasternFullLLMOutput(BaseModel):
    """동양 사주 LLM 출력 (간소화 버전)"""
    personality: str = Field(..., description="성격 분석")
    strength: str = Field(..., description="강점 분석")
    weakness: str = Field(..., description="약점과 보완 방법")
    advice: str = Field(..., description="종합 조언")
    summary: str = Field(..., description="종합 해석 요약")
    message: str = Field(..., description="상세 해석 메시지")
    badges: list[str] = Field(..., description="배지 코드 목록")
    lucky: EasternLuckyInfo = Field(..., description="행운 정보")


class WesternFullLLMOutput(BaseModel):
    """서양 점성술 LLM 출력 (간소화 버전)"""
    personality: str = Field(..., description="성격 분석")
    strength: str = Field(..., description="강점 분석")
    weakness: str = Field(..., description="약점과 보완 방법")
    advice: str = Field(..., description="종합 조언")
    summary: str = Field(..., description="종합 해석 요약")
    message: str = Field(..., description="상세 해석 메시지")
    badges: list[str] = Field(..., description="배지 코드 목록")
    keywords: list[KeywordItem] = Field(
        default_factory=list,
        description="키워드 목록 (code, label, weight 필수)",
    )
    lucky: WesternLuckyInfo = Field(..., description="행운 정보")


class InterpretationResult(BaseModel):
    """사주 해석 결과 (레거시)"""
    personality: str = Field(..., description="성격 분석")
    strength: str = Field(..., description="강점 분석")
    weakness: str = Field(..., description="약점과 보완 방법")
    advice: str = Field(..., description="종합 조언")


class EasternInterpretationResult(BaseModel):
    """동양 사주 해석 결과"""
    personality: str = Field(..., description="성격 분석")
    strength: str = Field(..., description="강점 분석")
    weakness: str = Field(..., description="약점과 보완 방법")
    advice: str = Field(..., description="종합 조언")
    five_elements_analysis: str = Field(default="", description="오행 분석")
    ten_gods_analysis: str = Field(default="", description="십신 분석")


class WesternInterpretationResult(BaseModel):
    """서양 점성술 해석 결과"""
    personality: str = Field(..., description="성격 분석")
    strength: str = Field(..., description="강점 분석")
    weakness: str = Field(..., description="약점과 보완 방법")
    advice: str = Field(..., description="종합 조언")
    big_three_analysis: str = Field(default="", description="태양/달/상승 분석")
    elements_analysis: str = Field(default="", description="원소 분석")


class CharacterMessage(BaseModel):
    """캐릭터 메시지"""
    message: str = Field(..., description="캐릭터 스타일의 메시지")
    # LLM이 예측 불가능한 tone 값을 반환하므로 str로 완전 개방
    # 어떤 값이든 허용하여 Pydantic 검증 실패 방지
    tone: str = Field(default="warm", description="메시지 톤 (자유 형식)")


class LuckyInfo(BaseModel):
    """행운 정보 (레거시)"""
    color: str = Field(..., description="행운의 색상")
    number: str = Field(..., description="행운의 숫자")
    item: str = Field(..., description="행운의 아이템")
    direction: str = Field(..., description="행운의 방향")
    place: str = Field(..., description="행운의 장소")


class DailyFortuneResult(BaseModel):
    """일일 운세 결과"""
    overall: str = Field(..., description="종합 운세")
    love: str = Field(..., description="애정운")
    career: str = Field(..., description="직장운")
    wealth: str = Field(..., description="재물운")
    health: str = Field(..., description="건강운")
    lucky: LuckyInfo = Field(..., description="행운 정보")
    advice: str = Field(..., description="오늘의 조언")


class CompatibilityResult(BaseModel):
    """궁합 분석 결과"""
    score: int = Field(..., ge=0, le=100, description="궁합 점수")
    summary: str = Field(..., description="궁합 요약")
    strengths: list[str] = Field(..., description="잘 맞는 부분")
    weaknesses: list[str] = Field(..., description="보완이 필요한 부분")
    advice: str = Field(..., description="궁합 조언")
