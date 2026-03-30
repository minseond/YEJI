"""동양 사주 API 모델

요청/응답 Pydantic 스키마 정의
"""

from typing import Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator

from yeji_ai.models.enums import (
    ChartType,
    CheonGanCode,
    CommonBadge,
    EasternBadge,
    ElementCode,
    JiJiCode,
    PillarKey,
    TenGodCode,
    TenGodGroupCode,
    YinYangBalance,
)

# ============================================================
# 기본 구성 요소
# ============================================================


class Pillar(BaseModel):
    """사주 기둥 (연주/월주/일주/시주)"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "gan": "甲",
                "gan_code": "GAP",
                "ji": "子",
                "ji_code": "JA",
                "element_code": "WOOD",
                "ten_god_code": "BI_GYEON",
            }
        }
    )

    gan: str = Field(..., description="천간 한자 (예: 甲)")
    gan_code: CheonGanCode = Field(..., description="천간 코드")
    ji: str = Field(..., description="지지 한자 (예: 子)")
    ji_code: JiJiCode = Field(..., description="지지 코드")
    element_code: ElementCode = Field(..., description="기둥 오행")
    ten_god_code: TenGodCode = Field(..., description="십신")


class PillarChart(BaseModel):
    """사주 팔자 (4기둥)"""

    summary: str = Field(..., description="사주 요약")
    year: Pillar = Field(..., description="연주")
    month: Pillar = Field(..., description="월주")
    day: Pillar = Field(..., description="일주")
    hour: Pillar | None = Field(None, description="시주 (시간 미입력 시 null)")


# ============================================================
# 통계 분석
# ============================================================


class FiveElementStat(BaseModel):
    """오행 통계 항목"""

    code: ElementCode
    label: str = Field(..., description="한글 레이블 (목, 화, 토, 금, 수)")
    value: int = Field(..., ge=0, description="개수")
    percent: float = Field(..., ge=0, le=100, description="비율")


class YinYangStat(BaseModel):
    """음양 통계"""

    summary: str = Field(..., description="음양 요약")
    yin: int = Field(..., ge=0, le=100, description="음 비율")
    yang: int = Field(..., ge=0, le=100, description="양 비율")
    balance: YinYangBalance = Field(..., description="균형 상태")


class TenGodStat(BaseModel):
    """십신 통계 항목"""

    code: TenGodCode
    label: str = Field(..., description="한글 레이블")
    group_code: TenGodGroupCode = Field(..., description="십신 그룹")
    value: int = Field(..., ge=0, description="개수")
    percent: float = Field(..., ge=0, le=100, description="비율")


class EasternStats(BaseModel):
    """동양 사주 통계 분석"""

    # 오행 분포
    five_elements: dict = Field(
        ...,
        description="오행 분포 분석",
        json_schema_extra={
            "example": {
                "summary": "목과 화가 강하고 수가 약합니다",
                "elements": [],
                "strong": "WOOD",
                "weak": "WATER",
            }
        },
    )

    # 음양 비율
    yin_yang: YinYangStat = Field(..., description="음양 분석")

    # 십신 분포
    ten_gods: dict = Field(
        ...,
        description="십신 분포 분석",
        json_schema_extra={
            "example": {
                "summary": "비겁이 강하여 자아가 강합니다",
                "gods": [],
                "dominant": "BI_GYEOP",
            }
        },
    )

    # 강약점
    strength: str = Field(..., description="강점 설명")
    weakness: str = Field(..., description="약점 설명")


# ============================================================
# UI 힌트
# ============================================================


class EasternHighlight(BaseModel):
    """동양 사주 하이라이트"""

    day_master: PillarKey = Field(default=PillarKey.DAY, description="일간 위치")
    strong_element: ElementCode = Field(..., description="강한 오행")
    weak_element: ElementCode = Field(..., description="약한 오행")


class EasternUIHints(BaseModel):
    """동양 사주 UI 힌트"""

    badges: list[EasternBadge | CommonBadge] = Field(
        default_factory=list, description="표시할 배지 목록"
    )
    recommend_chart: ChartType = Field(
        default=ChartType.RADAR, description="추천 차트 타입"
    )
    highlight: EasternHighlight = Field(..., description="하이라이트 요소")


# ============================================================
# 행운 정보
# ============================================================


class EasternLucky(BaseModel):
    """동양 사주 행운 정보"""

    color: str = Field(..., description="행운의 색상")
    color_code: str | None = Field(None, description="색상 HEX 코드")
    number: str = Field(..., description="행운의 숫자")
    item: str = Field(..., description="행운의 아이템")
    direction: str = Field(..., description="행운의 방향")
    direction_code: Literal["N", "NE", "E", "SE", "S", "SW", "W", "NW"] | None = Field(
        None, description="방향 코드"
    )
    place: str = Field(..., description="행운의 장소")


# ============================================================
# 요청/응답
# ============================================================


class EasternFortuneRequest(BaseModel):
    """동양 사주 분석 요청"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "birth_date": "1990-05-15",
                "birth_time": "14:30",
                "gender": "M",
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
    birth_place: str | None = Field(None, description="출생지역")
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


class EasternFortuneResponse(BaseModel):
    """동양 사주 분석 응답"""

    category: Literal["eastern"] = "eastern"

    # 사주 팔자
    chart: PillarChart = Field(..., description="사주 차트")

    # 통계 분석
    stats: EasternStats = Field(..., description="통계 분석")

    # 종합 해석
    summary: str = Field(..., description="종합 해석 요약")
    message: str = Field(..., description="상세 해석 메시지")

    # UI 힌트
    ui_hints: EasternUIHints = Field(..., description="UI 렌더링 힌트")

    # 행운 정보
    lucky: EasternLucky = Field(..., description="행운 정보")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "category": "eastern",
                "chart": {
                    "summary": "갑자년 을축월 병인일 정묘시",
                    "year": {
                        "gan": "甲",
                        "gan_code": "GAP",
                        "ji": "子",
                        "ji_code": "JA",
                        "element_code": "WOOD",
                        "ten_god_code": "PYEON_IN",
                    },
                    "month": {
                        "gan": "乙",
                        "gan_code": "EUL",
                        "ji": "丑",
                        "ji_code": "CHUK",
                        "element_code": "WOOD",
                        "ten_god_code": "JEONG_IN",
                    },
                    "day": {
                        "gan": "丙",
                        "gan_code": "BYEONG",
                        "ji": "寅",
                        "ji_code": "IN",
                        "element_code": "FIRE",
                        "ten_god_code": "DAY_MASTER",
                    },
                    "hour": {
                        "gan": "丁",
                        "gan_code": "JEONG",
                        "ji": "卯",
                        "ji_code": "MYO",
                        "element_code": "FIRE",
                        "ten_god_code": "BI_GYEON",
                    },
                },
                "stats": {
                    "five_elements": {
                        "summary": "목과 화가 강하고 금이 약합니다",
                        "elements": [
                            {"code": "WOOD", "label": "목", "value": 3, "percent": 37.5},
                            {"code": "FIRE", "label": "화", "value": 2, "percent": 25.0},
                        ],
                        "strong": "WOOD",
                        "weak": "METAL",
                    },
                    "yin_yang": {
                        "summary": "양이 약간 우세합니다",
                        "yin": 37,
                        "yang": 63,
                        "balance": "SLIGHT_YANG",
                    },
                    "ten_gods": {
                        "summary": "인성이 강하여 학문과 지혜가 뛰어납니다",
                        "gods": [],
                        "dominant": "IN_SEONG",
                    },
                    "strength": "창의력과 리더십이 뛰어남",
                    "weakness": "결단력이 부족할 수 있음",
                },
                "summary": "병화 일간으로 태어나 밝고 열정적인 성격입니다.",
                "message": "목의 기운이 강하여 성장과 발전의 에너지가 넘칩니다...",
                "ui_hints": {
                    "badges": ["WOOD_STRONG", "IN_SEONG_DOMINANT"],
                    "recommend_chart": "RADAR",
                    "highlight": {
                        "day_master": "day",
                        "strong_element": "WOOD",
                        "weak_element": "METAL",
                    },
                },
                "lucky": {
                    "color": "빨간색",
                    "color_code": "#FF0000",
                    "number": "3, 7",
                    "item": "목걸이",
                    "direction": "남쪽",
                    "direction_code": "S",
                    "place": "산 근처",
                },
            }
        }
    )
