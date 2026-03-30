"""사주 관련 데이터 모델"""

from pydantic import BaseModel, Field


class FourPillars(BaseModel):
    """사주팔자 (연주, 월주, 일주, 시주)"""

    year: str = Field(..., description="연주 (예: 경오)")
    month: str = Field(..., description="월주 (예: 신사)")
    day: str = Field(..., description="일주 (예: 무진)")
    hour: str | None = Field(None, description="시주 (예: 기미)")


class ElementBalance(BaseModel):
    """오행 균형"""

    wood: int = Field(..., ge=0, le=100, description="목 비율")
    fire: int = Field(..., ge=0, le=100, description="화 비율")
    earth: int = Field(..., ge=0, le=100, description="토 비율")
    metal: int = Field(..., ge=0, le=100, description="금 비율")
    water: int = Field(..., ge=0, le=100, description="수 비율")

    def get_dominant(self) -> str:
        """가장 강한 오행 반환"""
        elements = {
            "목": self.wood,
            "화": self.fire,
            "토": self.earth,
            "금": self.metal,
            "수": self.water,
        }
        return max(elements, key=elements.get)

    def get_weak(self) -> str:
        """가장 약한 오행 반환"""
        elements = {
            "목": self.wood,
            "화": self.fire,
            "토": self.earth,
            "금": self.metal,
            "수": self.water,
        }
        return min(elements, key=elements.get)


class EasternAnalysis(BaseModel):
    """동양 분석 결과 (사주팔자)"""

    four_pillars: FourPillars = Field(..., description="사주팔자")
    day_master: str = Field(..., description="일간 (예: 무토)")
    element_balance: ElementBalance = Field(..., description="오행 균형")
    lucky_elements: list[str] = Field(default_factory=list, description="용신")
    interpretation: str = Field("", description="해석")


class WesternAnalysis(BaseModel):
    """서양 분석 결과 (별자리)"""

    sun_sign: str = Field(..., description="태양 별자리")
    moon_sign: str | None = Field(None, description="달 별자리")
    rising_sign: str | None = Field(None, description="상승궁")
    dominant_planet: str | None = Field(None, description="주요 행성")
    interpretation: str = Field("", description="해석")


class CategoryScore(BaseModel):
    """카테고리별 점수"""

    category: str
    score: int = Field(..., ge=0, le=100)
    trend: str = Field("stable", description="추세 (up/down/stable)")
    description: str = ""


class SajuResult(BaseModel):
    """사주 분석 최종 결과"""

    result_id: int = Field(..., description="결과 ID")
    total_score: int = Field(..., ge=0, le=100, description="종합 점수")
    main_element: str = Field(..., description="주요 오행")
    keywords: list[str] = Field(default_factory=list, description="키워드")

    category_scores: list[CategoryScore] = Field(
        default_factory=list, description="카테고리별 점수"
    )

    eastern: EasternAnalysis = Field(..., description="동양 분석")
    western: WesternAnalysis = Field(..., description="서양 분석")

    combined_opinion: str = Field("", description="통합 의견")
    advice: list[str] = Field(default_factory=list, description="조언")

    visualizations: list[dict] = Field(default_factory=list, description="시각화 데이터")
    suggested_questions: list[str] = Field(default_factory=list, description="추천 질문")
