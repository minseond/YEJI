"""프론트엔드 확정 스키마와 일치하는 UserFortune Pydantic 모델

dummyFortuneV2.ts의 UserFortune 인터페이스를 Python으로 구현.
도메인 코드 엄격 검증 포함.
"""

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from yeji_ai.models.enums import (
    CheonGanCode,
    ElementCode,
    JiJiCode,
    TenGodCode,
    YinYangBalance,
)
from yeji_ai.models.enums.domain_codes import (
    CHEON_GAN,
    EAST_ELEMENT_LABELS,
    JI_JI,
    MODALITY_LABELS,
    WEST_ELEMENT_LABELS,
    WEST_KEYWORD_LABELS,
    ZODIAC_SIGNS_KR,
    EastElementLiteral,
    WestElementLiteral,
    WestKeywordLiteral,
    ZodiacSignKRLiteral,
)

# ============================================================
# 공통 타입
# ============================================================


class SajuElement(BaseModel):
    """동양 오행/십신 분포 아이템"""

    code: str = Field(..., description="도메인 코드")
    label: str = Field(..., description="한글 레이블")
    percent: float = Field(..., ge=0, le=100, description="비율 (%)")


class WesternElement(BaseModel):
    """서양 원소/양태 분포 아이템"""

    code: str = Field(..., description="도메인 코드")
    label: str = Field(..., description="한글 레이블")
    percent: float = Field(..., ge=0, le=100, description="비율 (%)")


class WesternKeyword(BaseModel):
    """서양 키워드 아이템"""

    code: WestKeywordLiteral = Field(..., description="키워드 코드")
    label: str = Field(..., description="한글 레이블")
    weight: float = Field(..., ge=0, le=1, description="가중치 (0~1)")

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        """키워드 코드 검증"""
        valid_codes = list(WEST_KEYWORD_LABELS.keys())
        if v not in valid_codes:
            raise ValueError(f"키워드 코드는 다음 중 하나여야 합니다: {valid_codes}")
        return v


# ============================================================
# 동양 사주 (Eastern / SajuDataV2)
# ============================================================


class Pillar(BaseModel):
    """사주 기둥 (년/월/일/시)"""

    gan: str = Field(..., description="천간 한자")
    gan_code: CheonGanCode = Field(..., description="천간 코드")
    ji: str = Field(..., description="지지 한자")
    ji_code: JiJiCode = Field(..., description="지지 코드")
    element_code: ElementCode = Field(..., description="오행 코드")
    ten_god_code: TenGodCode = Field(..., description="십신 코드")

    @field_validator("gan")
    @classmethod
    def validate_gan(cls, v: str) -> str:
        """천간은 10개 한자 중 하나"""
        if v not in CHEON_GAN:
            raise ValueError(f"천간은 다음 중 하나여야 합니다: {CHEON_GAN}")
        return v

    @field_validator("ji")
    @classmethod
    def validate_ji(cls, v: str) -> str:
        """지지는 12개 한자 중 하나"""
        if v not in JI_JI:
            raise ValueError(f"지지는 다음 중 하나여야 합니다: {JI_JI}")
        return v


class EasternChart(BaseModel):
    """동양 사주 차트"""

    summary: str = Field(..., description="차트 요약 (LLM 생성)")
    year: Pillar = Field(..., description="년주")
    month: Pillar = Field(..., description="월주")
    day: Pillar = Field(..., description="일주")
    hour: Pillar = Field(..., description="시주")


class CheonganJijiItem(BaseModel):
    """천간지지 아이템 (년/월/일/시주)"""

    cheon_gan: str = Field(..., description="천간 한자")
    ji_ji: str = Field(..., description="지지 한자")


class CheonganJiji(BaseModel):
    """천간지지 원형 (chart에서 파생, LLM이 채울 필요 없음)"""

    summary: str = Field(default="", description="요약")
    year: CheonganJijiItem = Field(..., description="년주 천간/지지")
    month: CheonganJijiItem = Field(..., description="월주 천간/지지")
    day: CheonganJijiItem = Field(..., description="일주 천간/지지")
    hour: CheonganJijiItem = Field(..., description="시주 천간/지지")


class FiveElements(BaseModel):
    """오행 분포"""

    summary: str = Field(..., description="오행 분석 요약")
    elements_list: list[SajuElement] = Field(
        ..., min_length=5, max_length=5, description="오행 분포 (5개)", alias="list"
    )

    model_config = {"populate_by_name": True}

    @field_validator("elements_list")
    @classmethod
    def validate_list(cls, v: list[SajuElement]) -> list[SajuElement]:
        """오행 코드 검증"""
        valid_codes = list(EAST_ELEMENT_LABELS.keys())
        codes = [item.code for item in v]
        for code in codes:
            if code not in valid_codes:
                raise ValueError(f"오행 코드는 다음 중 하나여야 합니다: {valid_codes}")
        # 모든 오행 코드가 포함되어야 함
        if set(codes) != set(valid_codes):
            raise ValueError("오행 분포는 WOOD, FIRE, EARTH, METAL, WATER 모두 포함해야 합니다")
        return v

    @model_validator(mode="after")
    def validate_percent_sum(self) -> "FiveElements":
        """percent 합계 검증 (LLM 오차 허용)"""
        total = sum(item.percent for item in self.elements_list)
        if not (50.0 <= total <= 150.0):
            raise ValueError(f"오행 percent 합계가 범위를 벗어났습니다 (현재: {total})")
        return self

    @property
    def dominant(self) -> str:
        """우세 오행 레이블 반환"""
        if not self.elements_list:
            return "균형"
        max_elem = max(self.elements_list, key=lambda x: x.percent)
        return max_elem.label

    @property
    def strong(self) -> str:
        """강한 오행 레이블 반환 (dominant와 동일)"""
        return self.dominant

    @property
    def weak(self) -> str:
        """약한 오행 레이블 반환"""
        if not self.elements_list:
            return "균형"
        min_elem = min(self.elements_list, key=lambda x: x.percent)
        return min_elem.label

    def get(self, key: str, default: str = "") -> str:
        """dict 호환용 get 메서드"""
        if key == "dominant":
            return self.dominant
        if key == "strong":
            return self.strong
        if key == "weak":
            return self.weak
        if key == "summary":
            return self.summary
        return default


class YinYangRatio(BaseModel):
    """음양 비율"""

    summary: str = Field(..., description="음양 균형 설명")
    yin: float = Field(..., ge=0, le=100, description="음 비율 (%)")
    yang: float = Field(..., ge=0, le=100, description="양 비율 (%)")

    @model_validator(mode="after")
    def validate_ratio_sum(self) -> "YinYangRatio":
        """yin + yang = 100 검증 (LLM 오차 허용)"""
        total = self.yin + self.yang
        if not (50.0 <= total <= 150.0):
            raise ValueError(f"음양 합계가 범위를 벗어났습니다 (현재: {total})")
        return self

    @property
    def balance(self) -> YinYangBalance:
        """음양 균형 상태 계산

        Returns:
            YinYangBalance: 양 비율에 따른 균형 상태
        """
        return YinYangBalance.from_ratio(self.yang)


class TenGods(BaseModel):
    """십신 분포"""

    summary: str = Field(..., description="십신 분석 요약")
    gods_list: list[SajuElement] = Field(
        ..., min_length=3, max_length=4, description="상위 3개 이상 + ETC (옵션)", alias="list"
    )

    model_config = {"populate_by_name": True}

    @field_validator("gods_list")
    @classmethod
    def validate_gods_list(cls, v: "list[SajuElement]") -> "list[SajuElement]":
        """십신 코드 검증 (상위 3개 이상, ETC는 선택)"""
        valid_codes = [
            "BI_GYEON",
            "GANG_JAE",
            "SIK_SIN",
            "SANG_GWAN",
            "PYEON_JAE",
            "JEONG_JAE",
            "PYEON_GWAN",
            "JEONG_GWAN",
            "PYEON_IN",
            "JEONG_IN",
            "ETC",
        ]
        for item in v:
            if item.code not in valid_codes:
                raise ValueError(f"십신 코드는 다음 중 하나여야 합니다: {valid_codes}")

        # ETC 제외한 십신이 최소 3개 이상인지 확인
        non_etc_count = sum(1 for item in v if item.code != "ETC")
        if non_etc_count < 3:
            raise ValueError("ETC 제외 십신이 최소 3개 이상 필요합니다")

        return v

    @property
    def dominant(self) -> str:
        """우세 십신 코드 반환"""
        if not self.gods_list:
            return ""
        max_god = max(self.gods_list, key=lambda x: x.percent)
        return max_god.code

    def get(self, key: str, default: str = "") -> str:
        """dict 호환용 get 메서드"""
        if key == "dominant":
            return self.dominant or default
        if key == "summary":
            return self.summary
        return default


class EasternStats(BaseModel):
    """동양 사주 통계"""

    cheongan_jiji: CheonganJiji = Field(..., description="천간지지 원형")
    five_elements: FiveElements = Field(..., description="오행 분포")
    yin_yang_ratio: YinYangRatio = Field(..., description="음양 비율")
    ten_gods: TenGods = Field(..., description="십신 분포")

    @property
    def yin_yang(self) -> YinYangRatio:
        """yin_yang_ratio의 별칭 (하위 호환용)"""
        return self.yin_yang_ratio

    @property
    def strength(self) -> str:
        """강한 오행 정보 (five_elements.dominant의 별칭)"""
        return self.five_elements.dominant

    @property
    def weakness(self) -> str:
        """약한 오행 정보 (five_elements.weak의 별칭)"""
        return self.five_elements.weak


class FinalVerdict(BaseModel):
    """천기누설 (종합 분석)"""

    summary: str = Field(..., description="종합 요약")
    strength: str = Field(..., description="강점")
    weakness: str = Field(..., description="약점")
    advice: str = Field(..., description="조언")


class EasternLucky(BaseModel):
    """동양 사주 행운 정보"""

    color: str = Field(..., description="행운의 색상 (한글)")
    number: str = Field(..., description="행운의 숫자 (아라비아)")
    item: str = Field(..., description="행운의 아이템 (한글)")
    direction: str | None = Field(None, description="행운의 방향 (한글)")
    place: str | None = Field(None, description="행운의 장소 (한글)")


class SajuDataV2(BaseModel):
    """동양 사주 데이터 (프론트엔드 확정 스키마)

    dummyFortuneV2.ts의 UserFortune['eastern']과 일치.
    """

    element: EastElementLiteral = Field(..., description="대표 오행")
    chart: EasternChart = Field(..., description="사주 차트")
    stats: EasternStats = Field(..., description="사주 통계")
    final_verdict: FinalVerdict = Field(..., description="천기누설")
    lucky: EasternLucky = Field(..., description="행운 정보")


# ============================================================
# 서양 점성술 (Western / WesternFortuneDataV2)
# ============================================================


class MainSign(BaseModel):
    """태양 별자리"""

    name: ZodiacSignKRLiteral = Field(..., description="별자리 이름 (한글, 띄어쓰기X)")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """별자리 이름 검증"""
        if v not in ZODIAC_SIGNS_KR:
            raise ValueError(f"별자리는 다음 중 하나여야 합니다: {ZODIAC_SIGNS_KR}")
        return v


class WesternStats(BaseModel):
    """서양 점성술 통계"""

    main_sign: MainSign = Field(..., description="태양 별자리")

    element_summary: str = Field(..., description="원소 분석 요약")
    element_4_distribution: list[WesternElement] = Field(
        ..., min_length=4, max_length=4, description="4원소 분포"
    )

    modality_summary: str = Field(..., description="양태 분석 요약")
    modality_3_distribution: list[WesternElement] = Field(
        ..., min_length=3, max_length=3, description="3양태 분포"
    )

    keywords_summary: str = Field(..., description="키워드 분석 요약")
    keywords: list[WesternKeyword] = Field(
        ..., min_length=3, max_length=5, description="키워드 (3~5개)"
    )

    @field_validator("element_4_distribution")
    @classmethod
    def validate_elements(cls, v: list[WesternElement]) -> list[WesternElement]:
        """4원소 코드 검증"""
        valid_codes = list(WEST_ELEMENT_LABELS.keys())
        codes = [item.code for item in v]
        for code in codes:
            if code not in valid_codes:
                raise ValueError(f"원소 코드는 다음 중 하나여야 합니다: {valid_codes}")
        if set(codes) != set(valid_codes):
            raise ValueError("4원소 분포는 FIRE, EARTH, AIR, WATER 모두 포함해야 합니다")
        return v

    @field_validator("modality_3_distribution")
    @classmethod
    def validate_modality(cls, v: list[WesternElement]) -> list[WesternElement]:
        """3양태 코드 검증"""
        valid_codes = list(MODALITY_LABELS.keys())
        codes = [item.code for item in v]
        for code in codes:
            if code not in valid_codes:
                raise ValueError(f"양태 코드는 다음 중 하나여야 합니다: {valid_codes}")
        if set(codes) != set(valid_codes):
            raise ValueError("3양태 분포는 CARDINAL, FIXED, MUTABLE 모두 포함해야 합니다")
        return v

    @model_validator(mode="after")
    def validate_percent_sums(self) -> "WesternStats":
        """percent 합계 검증 (LLM 오차 허용)"""
        element_total = sum(item.percent for item in self.element_4_distribution)
        if not (50.0 <= element_total <= 150.0):
            raise ValueError(f"4원소 percent 합계가 범위를 벗어났습니다 (현재: {element_total})")

        modality_total = sum(item.percent for item in self.modality_3_distribution)
        if not (50.0 <= modality_total <= 150.0):
            raise ValueError(f"3양태 percent 합계가 범위를 벗어났습니다 (현재: {modality_total})")

        return self


class DetailedAnalysis(BaseModel):
    """상세 분석 항목"""

    title: str = Field(..., description="제목")
    content: str = Field(..., description="내용")


class FortuneContent(BaseModel):
    """운세 콘텐츠"""

    overview: str = Field(..., description="개요 (의미심장하게)")
    detailed_analysis: list[DetailedAnalysis] = Field(
        ..., min_length=2, max_length=2, description="상세 분석 (정확히 2개)"
    )
    advice: str = Field(..., description="조언 (overview 요약)")


class WesternLucky(BaseModel):
    """서양 점성술 행운 정보"""

    color: str = Field(..., description="행운의 색상 (한글)")
    number: str = Field(..., description="행운의 숫자 (아라비아)")
    item: str | None = Field(None, description="행운의 아이템 (한글)")
    place: str | None = Field(None, description="행운의 장소 (한글)")


class WesternFortuneDataV2(BaseModel):
    """서양 점성술 데이터 (프론트엔드 확정 스키마)

    dummyFortuneV2.ts의 UserFortune['western']과 일치.
    """

    element: WestElementLiteral = Field(..., description="대표 원소")
    stats: WesternStats = Field(..., description="점성술 통계")
    fortune_content: FortuneContent = Field(..., description="운세 콘텐츠")
    lucky: WesternLucky = Field(..., description="행운 정보")


# ============================================================
# 통합 모델 (UserFortune)
# ============================================================


class UserFortune(BaseModel):
    """사용자 운세 통합 모델 (프론트엔드 확정 스키마)

    dummyFortuneV2.ts의 UserFortune 인터페이스와 완전 호환.
    LLM이 생성하는 최종 JSON 형식.
    """

    eastern: SajuDataV2 = Field(..., description="동양 사주")
    western: WesternFortuneDataV2 = Field(..., description="서양 점성술")


# ============================================================
# Graceful Degradation 응답 래퍼
# ============================================================


FortuneTypeLiteral = Literal["eastern", "western"]


class FortuneResponse(BaseModel):
    """운세 API 통합 응답 래퍼 (Graceful Degradation 지원)

    검증 실패해도 200 응답을 반환하여 LLM 출력을 확인할 수 있도록 합니다.

    Attributes:
        success: LLM 호출 성공 여부 (네트워크/서버 오류 없음)
        validated: Pydantic 검증 통과 여부
        type: 운세 타입 (eastern/western)
        data: 검증된 데이터 또는 원본 LLM 출력 (dict)
        errors: 검증 에러 목록 (validated=False일 때)
        latency_ms: LLM 응답 시간 (ms)
    """

    success: bool = Field(..., description="LLM 호출 성공 여부")
    validated: bool = Field(..., description="Pydantic 검증 통과 여부")
    type: FortuneTypeLiteral = Field(..., description="운세 타입 (eastern/western)")
    data: dict = Field(..., description="운세 데이터 (검증됨 또는 원본)")
    errors: list[str] | None = Field(default=None, description="검증 에러 목록")
    latency_ms: int | float = Field(default=0, description="LLM 응답 시간 (ms)")


# ============================================================
# 타입 별칭 (하위 호환성)
# ============================================================

IntegratedFortuneResult = UserFortune
SajuChart = EasternChart
SajuStats = EasternStats
WesternFortuneContent = FortuneContent
