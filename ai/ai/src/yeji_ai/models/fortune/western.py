"""서양 점성술 API 모델

요청/응답 Pydantic 스키마 정의
"""

from typing import Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator

from yeji_ai.models.enums import (
    AspectCode,
    AspectNature,
    ChartType,
    CommonBadge,
    HouseCode,
    PlanetCode,
    WesternBadge,
    ZodiacCode,
    ZodiacElement,
    ZodiacModality,
)

# ============================================================
# 기본 구성 요소
# ============================================================


class PlanetPlacement(BaseModel):
    """행성 배치"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "planet_code": "SUN",
                "sign_code": "ARIES",
                "house_number": 1,
                "degree": 15,
                "minute": 30,
                "is_retrograde": False,
            }
        }
    )

    planet_code: PlanetCode = Field(..., description="행성 코드")
    sign_code: ZodiacCode = Field(..., description="별자리 코드")
    house_number: int = Field(..., ge=1, le=12, description="하우스 번호")
    degree: int = Field(..., ge=0, lt=30, description="도 (0-29)")
    minute: int = Field(..., ge=0, lt=60, description="분 (0-59)")
    is_retrograde: bool = Field(False, description="역행 여부")


class HouseInfo(BaseModel):
    """하우스 정보"""

    number: int = Field(..., ge=1, le=12, description="하우스 번호")
    code: HouseCode = Field(..., description="하우스 코드")
    sign_code: ZodiacCode = Field(..., description="하우스 시작 별자리")
    planets: list[PlanetCode] = Field(
        default_factory=list, description="하우스 내 행성들"
    )


class BigThree(BaseModel):
    """빅3 (태양/달/상승궁)"""

    sign_code: ZodiacCode = Field(..., description="별자리 코드")
    house_number: int | None = Field(None, ge=1, le=12, description="하우스 번호")
    summary: str = Field(..., description="해석 요약")


class WesternChart(BaseModel):
    """서양 출생 차트"""

    summary: str = Field(..., description="차트 요약")

    # 빅3
    sun: BigThree = Field(..., description="태양궁")
    moon: BigThree = Field(..., description="달궁")
    rising: BigThree = Field(..., description="상승궁 (ASC)")

    # 전체 행성 배치
    planets: list[PlanetPlacement] = Field(
        default_factory=list, description="행성 배치 목록"
    )

    # 하우스
    houses: list[HouseInfo] = Field(
        default_factory=list, description="12하우스 정보"
    )


# ============================================================
# 통계 분석
# ============================================================


class ElementStat(BaseModel):
    """원소 통계 항목"""

    code: ZodiacElement
    label: str = Field(..., description="한글 레이블 (불, 흙, 공기, 물)")
    value: int = Field(..., ge=0, description="개수")
    percent: float = Field(..., ge=0, le=100, description="비율")


class WesternElements(BaseModel):
    """원소 분포 분석"""

    summary: str = Field(..., description="원소 분포 요약")
    distribution: list[ElementStat] = Field(
        default_factory=list, description="원소별 분포"
    )
    dominant: ZodiacElement = Field(..., description="우세 원소")


class ModalityStat(BaseModel):
    """모달리티 통계 항목"""

    code: ZodiacModality
    label: str = Field(..., description="한글 레이블 (카디널, 고정, 변통)")
    value: int = Field(..., ge=0, description="개수")
    percent: float = Field(..., ge=0, le=100, description="비율")


class WesternModality(BaseModel):
    """모달리티 분포 분석"""

    summary: str = Field(..., description="모달리티 분포 요약")
    distribution: list[ModalityStat] = Field(
        default_factory=list, description="모달리티별 분포"
    )
    dominant: ZodiacModality = Field(..., description="우세 모달리티")


class AspectInfo(BaseModel):
    """애스펙트 정보"""

    planet1: PlanetCode = Field(..., description="첫 번째 행성")
    planet2: PlanetCode = Field(..., description="두 번째 행성")
    aspect_code: AspectCode = Field(..., description="애스펙트 코드")
    nature: AspectNature = Field(..., description="애스펙트 성질")
    orb: float = Field(..., ge=0, description="오브 (허용 오차)")
    interpretation: str = Field(..., description="해석")


class WesternAspects(BaseModel):
    """애스펙트 분석"""

    summary: str = Field(..., description="애스펙트 요약")
    major_aspects: list[AspectInfo] = Field(
        default_factory=list, description="주요 애스펙트 목록"
    )


class WesternStats(BaseModel):
    """서양 점성술 통계 분석"""

    # 원소 분포
    elements: WesternElements = Field(..., description="원소 분포")

    # 모달리티 분포
    modality: WesternModality = Field(..., description="모달리티 분포")

    # 주요 애스펙트
    aspects: WesternAspects = Field(..., description="애스펙트 분석")

    # 강약점
    strength: str = Field(..., description="강점 설명")
    weakness: str = Field(..., description="약점 설명")


# ============================================================
# UI 힌트
# ============================================================


class WesternHighlight(BaseModel):
    """서양 점성술 하이라이트"""

    sun_sign: ZodiacCode = Field(..., description="태양 별자리")
    moon_sign: ZodiacCode = Field(..., description="달 별자리")
    rising_sign: ZodiacCode = Field(..., description="상승 별자리")
    dominant_planet: PlanetCode = Field(..., description="우세 행성")


class WesternUIHints(BaseModel):
    """서양 점성술 UI 힌트"""

    badges: list[WesternBadge | CommonBadge] = Field(
        default_factory=list, description="표시할 배지 목록"
    )
    recommend_chart: ChartType = Field(
        default=ChartType.WHEEL, description="추천 차트 타입"
    )
    highlight: WesternHighlight = Field(..., description="하이라이트 요소")


# ============================================================
# 행운 정보
# ============================================================


class WesternLucky(BaseModel):
    """서양 점성술 행운 정보"""

    day: str = Field(..., description="행운의 요일")
    day_code: Literal["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"] | None = Field(
        None, description="요일 코드"
    )
    color: str = Field(..., description="행운의 색상")
    color_code: str | None = Field(None, description="색상 HEX 코드")
    number: str = Field(..., description="행운의 숫자")
    stone: str = Field(..., description="행운의 보석")
    planet: PlanetCode = Field(..., description="수호 행성")


# ============================================================
# 요청/응답
# ============================================================


class WesternFortuneRequest(BaseModel):
    """서양 점성술 분석 요청"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "birth_date": "1990-05-15",
                "birth_time": "14:30",
                "birth_place": "Seoul, Korea",
                "latitude": 37.5665,
                "longitude": 126.9780,
                "name": "홍길동",
            }
        }
    )

    birth_date: str = Field(
        ..., description="생년월일 (YYYY-MM-DD)", pattern=r"^\d{4}-\d{2}-\d{2}$"
    )
    birth_time: str | None = Field(
        None, description="출생시간 (HH:MM)", pattern=r"^\d{2}:\d{2}$"
    )
    birth_place: str | None = Field(None, description="출생지역 (위도/경도 계산용)")
    latitude: float | None = Field(None, ge=-90, le=90, description="위도")
    longitude: float | None = Field(None, ge=-180, le=180, description="경도")
    gender: Literal["M", "F"] = Field(..., description="성별 (필수)")
    name: str = Field(
        ...,
        description="이름 (필수)",
        validation_alias=AliasChoices("name", "name_kor"),
    )

    @field_validator("birth_time", mode="before")
    @classmethod
    def empty_string_to_none(cls, v: str | None) -> str | None:
        """빈 문자열을 None으로 변환"""
        if v == "" or v is None:
            return None
        return v


class WesternFortuneResponse(BaseModel):
    """서양 점성술 분석 응답"""

    category: Literal["western"] = "western"

    # 출생 차트
    chart: WesternChart = Field(..., description="출생 차트")

    # 통계 분석
    stats: WesternStats = Field(..., description="통계 분석")

    # 종합 해석
    summary: str = Field(..., description="종합 해석 요약")
    message: str = Field(..., description="상세 해석 메시지")

    # UI 힌트
    ui_hints: WesternUIHints = Field(..., description="UI 렌더링 힌트")

    # 행운 정보
    lucky: WesternLucky = Field(..., description="행운 정보")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "category": "western",
                "chart": {
                    "summary": "태양 양자리, 달 전갈자리, 상승 사자자리",
                    "sun": {
                        "sign_code": "ARIES",
                        "house_number": 9,
                        "summary": "양자리 태양은 열정적이고 선구자적인 성격을 부여합니다.",
                    },
                    "moon": {
                        "sign_code": "SCORPIO",
                        "house_number": 4,
                        "summary": "전갈자리 달은 깊은 감정과 직관력을 나타냅니다.",
                    },
                    "rising": {
                        "sign_code": "LEO",
                        "house_number": 1,
                        "summary": "사자자리 상승궁은 당당하고 카리스마 있는 첫인상을 줍니다.",
                    },
                    "planets": [],
                    "houses": [],
                },
                "stats": {
                    "elements": {
                        "summary": "불 원소가 우세합니다",
                        "distribution": [
                            {"code": "FIRE", "label": "불", "value": 4, "percent": 40.0},
                        ],
                        "dominant": "FIRE",
                    },
                    "modality": {
                        "summary": "카디널 모드가 우세합니다",
                        "distribution": [],
                        "dominant": "CARDINAL",
                    },
                    "aspects": {
                        "summary": "태양과 달의 스퀘어가 내면의 갈등을 나타냅니다",
                        "major_aspects": [],
                    },
                    "strength": "리더십과 추진력이 뛰어남",
                    "weakness": "인내심이 부족할 수 있음",
                },
                "summary": "양자리 태양으로 태어나 열정적이고 적극적인 성격입니다.",
                "message": "불 원소가 강하여 행동력과 추진력이 뛰어납니다...",
                "ui_hints": {
                    "badges": ["FIRE_DOMINANT", "CARDINAL_DOMINANT", "MARS_STRONG"],
                    "recommend_chart": "WHEEL",
                    "highlight": {
                        "sun_sign": "ARIES",
                        "moon_sign": "SCORPIO",
                        "rising_sign": "LEO",
                        "dominant_planet": "MARS",
                    },
                },
                "lucky": {
                    "day": "화요일",
                    "day_code": "TUE",
                    "color": "빨간색",
                    "color_code": "#FF0000",
                    "number": "9",
                    "stone": "다이아몬드",
                    "planet": "MARS",
                },
            }
        }
    )
