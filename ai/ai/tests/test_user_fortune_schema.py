"""UserFortune 스키마 검증 테스트

동양 사주(SajuDataV2) 및 서양 점성술(WesternFortuneDataV2) 모델의
유효성 검증 로직을 테스트합니다.
"""

import pytest
from pydantic import ValidationError

from yeji_ai.models.user_fortune import (
    UserFortune,
    SajuDataV2,
    WesternFortuneDataV2,
    EasternChart,
    EasternStats,
    FinalVerdict,
    EasternLucky,
    WesternStats,
    FortuneContent,
    WesternLucky,
    Pillar,
    CheonganJiji,
    FiveElements,
    YinYangRatio,
    TenGods,
    SajuElement,
    WesternElement,
    WesternKeyword,
    MainSign,
    DetailedAnalysis,
)


# ============================================================
# 테스트용 예시 데이터 (EASTERN_EXAMPLE 기반)
# ============================================================

def create_valid_eastern_data() -> dict:
    """유효한 동양 사주 데이터 생성"""
    return {
        "element": "WOOD",
        "chart": {
            "summary": "갑자일주로 목기운이 강한 사주입니다.",
            "year": {
                "gan": "甲",
                "gan_code": "GAP",
                "ji": "子",
                "ji_code": "JA",
                "element_code": "WOOD",
                "ten_god_code": "BI_GYEON",
            },
            "month": {
                "gan": "乙",
                "gan_code": "EUL",
                "ji": "丑",
                "ji_code": "CHUK",
                "element_code": "WOOD",
                "ten_god_code": "GANG_JAE",
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
                "ten_god_code": "SIK_SIN",
            },
        },
        "stats": {
            "cheongan_jiji": {
                "summary": "천간지지 요약",
                "year": {"cheon_gan": "甲", "ji_ji": "子"},
                "month": {"cheon_gan": "乙", "ji_ji": "丑"},
                "day": {"cheon_gan": "丙", "ji_ji": "寅"},
                "hour": {"cheon_gan": "丁", "ji_ji": "卯"},
            },
            "five_elements": {
                "summary": "목과 화의 기운이 강합니다.",
                "list": [
                    {"code": "WOOD", "label": "목", "percent": 35.0},
                    {"code": "FIRE", "label": "화", "percent": 25.0},
                    {"code": "EARTH", "label": "토", "percent": 15.0},
                    {"code": "METAL", "label": "금", "percent": 15.0},
                    {"code": "WATER", "label": "수", "percent": 10.0},
                ],
            },
            "yin_yang_ratio": {
                "summary": "양의 기운이 약간 우세합니다.",
                "yin": 45.0,
                "yang": 55.0,
            },
            "ten_gods": {
                "summary": "비견과 식신이 강합니다.",
                "list": [
                    {"code": "BI_GYEON", "label": "비견", "percent": 30.0},
                    {"code": "SIK_SIN", "label": "식신", "percent": 25.0},
                    {"code": "JEONG_JAE", "label": "정재", "percent": 20.0},
                    {"code": "ETC", "label": "기타", "percent": 25.0},
                ],
            },
        },
        "final_verdict": {
            "summary": "창의력과 리더십이 뛰어난 사주입니다.",
            "strength": "목 기운이 강해 성장과 발전의 에너지가 충만합니다.",
            "weakness": "수 기운이 부족해 유연성이 다소 부족할 수 있습니다.",
            "advice": "명상과 물가 산책으로 수 기운을 보충하세요.",
        },
        "lucky": {
            "color": "초록색",
            "number": "3",
            "item": "나무 액세서리",
            "direction": "동쪽",
            "place": "숲",
        },
    }


# ============================================================
# 테스트용 예시 데이터 (WESTERN_EXAMPLE 기반)
# ============================================================

def create_valid_western_data() -> dict:
    """유효한 서양 점성술 데이터 생성"""
    return {
        "element": "FIRE",
        "stats": {
            "main_sign": {"name": "사자자리"},
            "element_summary": "불의 기운이 강해 열정적입니다.",
            "element_4_distribution": [
                {"code": "FIRE", "label": "불", "percent": 40.0},
                {"code": "EARTH", "label": "흙", "percent": 20.0},
                {"code": "AIR", "label": "공기", "percent": 25.0},
                {"code": "WATER", "label": "물", "percent": 15.0},
            ],
            "modality_summary": "고정 에너지가 강해 안정적입니다.",
            "modality_3_distribution": [
                {"code": "CARDINAL", "label": "활동", "percent": 30.0},
                {"code": "FIXED", "label": "고정", "percent": 45.0},
                {"code": "MUTABLE", "label": "변동", "percent": 25.0},
            ],
            "keywords_summary": "리더십과 열정이 핵심 키워드입니다.",
            "keywords": [
                {"code": "LEADERSHIP", "label": "리더십", "weight": 0.9},
                {"code": "PASSION", "label": "열정", "weight": 0.85},
                {"code": "STABILITY", "label": "안정", "weight": 0.7},
            ],
        },
        "fortune_content": {
            "overview": "오늘은 창의적인 에너지가 넘치는 하루입니다.",
            "detailed_analysis": [
                {"title": "애정운", "content": "연인과의 관계가 더욱 깊어집니다."},
                {"title": "금전운", "content": "예상치 못한 수입이 있을 수 있습니다."},
            ],
            "advice": "창의적인 활동에 집중하세요.",
        },
        "lucky": {
            "color": "빨간색",
            "number": "1",
            "item": "금반지",
            "place": "극장",
        },
    }


# ============================================================
# 테스트 케이스 1: 유효한 동양 사주 데이터 검증
# ============================================================

class TestValidEasternData:
    """유효한 동양 사주 데이터 검증 테스트"""

    def test_valid_saju_data_v2_creation(self):
        """유효한 SajuDataV2 객체 생성 테스트"""
        # Arrange
        data = create_valid_eastern_data()

        # Act
        saju = SajuDataV2(**data)

        # Assert
        assert saju.element == "WOOD"
        assert saju.chart.summary == "갑자일주로 목기운이 강한 사주입니다."
        assert saju.chart.year.gan == "甲"
        assert saju.chart.year.ji == "子"

    def test_valid_pillar_creation(self):
        """유효한 Pillar 객체 생성 테스트"""
        # Arrange
        pillar_data = {
            "gan": "甲",
            "gan_code": "GAP",
            "ji": "子",
            "ji_code": "JA",
            "element_code": "WOOD",
            "ten_god_code": "BI_GYEON",
        }

        # Act
        pillar = Pillar(**pillar_data)

        # Assert
        assert pillar.gan == "甲"
        assert pillar.gan_code == "GAP"
        assert pillar.ji == "子"
        assert pillar.ji_code == "JA"
        assert pillar.element_code == "WOOD"
        assert pillar.ten_god_code == "BI_GYEON"

    def test_valid_five_elements_percent_sum_100(self):
        """오행 percent 합계가 100인 경우 검증 성공"""
        # Arrange
        data = {
            "summary": "오행 분석",
            "list": [
                {"code": "WOOD", "label": "목", "percent": 20.0},
                {"code": "FIRE", "label": "화", "percent": 20.0},
                {"code": "EARTH", "label": "토", "percent": 20.0},
                {"code": "METAL", "label": "금", "percent": 20.0},
                {"code": "WATER", "label": "수", "percent": 20.0},
            ],
        }

        # Act
        five_elements = FiveElements(**data)

        # Assert
        total = sum(item.percent for item in five_elements.elements_list)
        assert total == 100.0

    def test_valid_yin_yang_ratio(self):
        """유효한 음양 비율 검증"""
        # Arrange
        data = {"summary": "음양 분석", "yin": 40.0, "yang": 60.0}

        # Act
        ratio = YinYangRatio(**data)

        # Assert
        assert ratio.yin + ratio.yang == 100.0

    def test_eastern_chart_all_pillars(self):
        """사주 차트의 4주(년/월/일/시) 검증"""
        # Arrange
        data = create_valid_eastern_data()

        # Act
        saju = SajuDataV2(**data)

        # Assert
        assert saju.chart.year is not None
        assert saju.chart.month is not None
        assert saju.chart.day is not None
        assert saju.chart.hour is not None


# ============================================================
# 테스트 케이스 2: 유효한 서양 점성술 데이터 검증
# ============================================================

class TestValidWesternData:
    """유효한 서양 점성술 데이터 검증 테스트"""

    def test_valid_western_fortune_data_creation(self):
        """유효한 WesternFortuneDataV2 객체 생성 테스트"""
        # Arrange
        data = create_valid_western_data()

        # Act
        western = WesternFortuneDataV2(**data)

        # Assert
        assert western.element == "FIRE"
        assert western.stats.main_sign.name == "사자자리"

    def test_valid_main_sign_zodiac(self):
        """유효한 별자리 검증"""
        # Arrange
        data = {"name": "물고기자리"}

        # Act
        main_sign = MainSign(**data)

        # Assert
        assert main_sign.name == "물고기자리"

    def test_valid_element_4_distribution(self):
        """4원소 분포 검증 성공"""
        # Arrange
        data = create_valid_western_data()

        # Act
        western = WesternFortuneDataV2(**data)

        # Assert
        codes = [item.code for item in western.stats.element_4_distribution]
        assert set(codes) == {"FIRE", "EARTH", "AIR", "WATER"}

    def test_valid_modality_3_distribution(self):
        """3양태 분포 검증 성공"""
        # Arrange
        data = create_valid_western_data()

        # Act
        western = WesternFortuneDataV2(**data)

        # Assert
        codes = [item.code for item in western.stats.modality_3_distribution]
        assert set(codes) == {"CARDINAL", "FIXED", "MUTABLE"}

    def test_valid_western_keywords(self):
        """서양 키워드 검증 성공"""
        # Arrange
        data = create_valid_western_data()

        # Act
        western = WesternFortuneDataV2(**data)

        # Assert
        assert len(western.stats.keywords) >= 3
        assert len(western.stats.keywords) <= 5

    def test_valid_fortune_content_two_analysis(self):
        """상세 분석이 정확히 2개인지 검증"""
        # Arrange
        data = create_valid_western_data()

        # Act
        western = WesternFortuneDataV2(**data)

        # Assert
        assert len(western.fortune_content.detailed_analysis) == 2


# ============================================================
# 테스트 케이스 3: 잘못된 도메인 코드 검증 실패 테스트
# ============================================================

class TestInvalidDomainCodes:
    """잘못된 도메인 코드 검증 실패 테스트"""

    def test_invalid_cheongan_code(self):
        """잘못된 천간 코드로 검증 실패"""
        # Arrange
        pillar_data = {
            "gan": "X",
            "gan_code": "GAP",
            "ji": "子",
            "ji_code": "JA",
            "element_code": "WOOD",
            "ten_god_code": "BI_GYEON",
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Pillar(**pillar_data)
        assert "천간" in str(exc_info.value)

    def test_invalid_jiji_code(self):
        """잘못된 지지 코드로 검증 실패"""
        # Arrange
        pillar_data = {
            "gan": "甲",
            "gan_code": "GAP",
            "ji": "X",
            "ji_code": "JA",
            "element_code": "WOOD",
            "ten_god_code": "BI_GYEON",
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Pillar(**pillar_data)
        assert "지지" in str(exc_info.value)

    def test_invalid_east_element_code(self):
        """잘못된 동양 오행 코드로 검증 실패"""
        # Arrange
        data = create_valid_eastern_data()
        data["element"] = "INVALID_ELEMENT"

        # Act & Assert
        with pytest.raises(ValidationError):
            SajuDataV2(**data)

    def test_invalid_west_element_code(self):
        """잘못된 서양 원소 코드로 검증 실패"""
        # Arrange
        data = create_valid_western_data()
        data["element"] = "INVALID_ELEMENT"

        # Act & Assert
        with pytest.raises(ValidationError):
            WesternFortuneDataV2(**data)

    def test_invalid_zodiac_sign(self):
        """잘못된 별자리로 검증 실패"""
        # Arrange
        data = {"name": "없는자리"}

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            MainSign(**data)
        # Literal 타입 검증 실패 시 "literal_error" 또는 별자리 검증 실패 메시지 확인
        error_str = str(exc_info.value)
        assert "name" in error_str or "별자리" in error_str

    def test_invalid_modality_code(self):
        """잘못된 양태 코드로 검증 실패"""
        # Arrange
        data = create_valid_western_data()
        data["stats"]["modality_3_distribution"][0]["code"] = "INVALID"

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            WesternFortuneDataV2(**data)
        assert "양태" in str(exc_info.value)

    def test_invalid_keyword_code(self):
        """잘못된 키워드 코드로 검증 실패"""
        # Arrange
        data = create_valid_western_data()
        data["stats"]["keywords"][0]["code"] = "INVALID_KEYWORD"

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            WesternFortuneDataV2(**data)
        # Literal 타입 검증 실패 시 "literal_error" 또는 keywords/code 관련 에러 메시지 확인
        error_str = str(exc_info.value)
        assert "keywords" in error_str or "code" in error_str or "키워드" in error_str

    def test_invalid_ten_god_code(self):
        """잘못된 십신 코드로 검증 실패"""
        # Arrange
        data = create_valid_eastern_data()
        data["stats"]["ten_gods"]["list"][0]["code"] = "INVALID_GOD"

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            SajuDataV2(**data)
        assert "십신" in str(exc_info.value)

    def test_incomplete_five_elements(self):
        """오행이 모두 포함되지 않은 경우 검증 실패"""
        # Arrange
        data = {
            "summary": "오행 분석",
            "list": [
                {"code": "WOOD", "label": "목", "percent": 25.0},
                {"code": "FIRE", "label": "화", "percent": 25.0},
                {"code": "EARTH", "label": "토", "percent": 25.0},
                {"code": "METAL", "label": "금", "percent": 25.0},
                # WATER 누락
                {"code": "WOOD", "label": "목", "percent": 0.0},  # 중복
            ],
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            FiveElements(**data)
        assert "WOOD, FIRE, EARTH, METAL, WATER 모두 포함" in str(exc_info.value)


# ============================================================
# 테스트 케이스 4: percent 합계 검증 실패 테스트
# ============================================================

class TestPercentSumValidation:
    """percent 합계 검증 실패 테스트 (LLM 오차 허용: 50~150 범위)"""

    def test_five_elements_percent_sum_exceeds_150(self):
        """오행 percent 합계가 150을 초과하면 검증 실패"""
        # Arrange
        data = {
            "summary": "오행 분석",
            "list": [
                {"code": "WOOD", "label": "목", "percent": 40.0},
                {"code": "FIRE", "label": "화", "percent": 40.0},
                {"code": "EARTH", "label": "토", "percent": 40.0},
                {"code": "METAL", "label": "금", "percent": 40.0},
                {"code": "WATER", "label": "수", "percent": 40.0},  # 합계 200
            ],
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            FiveElements(**data)
        assert "오행 percent 합계가 범위를 벗어났습니다" in str(exc_info.value)

    def test_five_elements_percent_sum_below_50(self):
        """오행 percent 합계가 50 미만이면 검증 실패"""
        # Arrange
        data = {
            "summary": "오행 분석",
            "list": [
                {"code": "WOOD", "label": "목", "percent": 5.0},
                {"code": "FIRE", "label": "화", "percent": 5.0},
                {"code": "EARTH", "label": "토", "percent": 5.0},
                {"code": "METAL", "label": "금", "percent": 5.0},
                {"code": "WATER", "label": "수", "percent": 5.0},  # 합계 25
            ],
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            FiveElements(**data)
        assert "오행 percent 합계가 범위를 벗어났습니다" in str(exc_info.value)

    def test_yin_yang_ratio_sum_exceeds_150(self):
        """음양 합계가 150을 초과하면 검증 실패"""
        # Arrange
        data = {"summary": "음양 분석", "yin": 80.0, "yang": 80.0}  # 합계 160

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            YinYangRatio(**data)
        assert "음양 합계가 범위를 벗어났습니다" in str(exc_info.value)

    def test_yin_yang_ratio_sum_below_50(self):
        """음양 합계가 50 미만이면 검증 실패"""
        # Arrange
        data = {"summary": "음양 분석", "yin": 20.0, "yang": 20.0}  # 합계 40

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            YinYangRatio(**data)
        assert "음양 합계가 범위를 벗어났습니다" in str(exc_info.value)

    def test_western_element_percent_sum_exceeds_150(self):
        """서양 4원소 percent 합계가 150을 초과하면 검증 실패"""
        # Arrange
        data = create_valid_western_data()
        data["stats"]["element_4_distribution"] = [
            {"code": "FIRE", "label": "불", "percent": 50.0},
            {"code": "EARTH", "label": "흙", "percent": 50.0},
            {"code": "AIR", "label": "공기", "percent": 50.0},
            {"code": "WATER", "label": "물", "percent": 50.0},  # 합계 200
        ]

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            WesternFortuneDataV2(**data)
        assert "4원소 percent 합계가 범위를 벗어났습니다" in str(exc_info.value)

    def test_western_modality_percent_sum_below_50(self):
        """서양 3양태 percent 합계가 50 미만이면 검증 실패"""
        # Arrange
        data = create_valid_western_data()
        data["stats"]["modality_3_distribution"] = [
            {"code": "CARDINAL", "label": "활동", "percent": 10.0},
            {"code": "FIXED", "label": "고정", "percent": 10.0},
            {"code": "MUTABLE", "label": "변동", "percent": 10.0},  # 합계 30
        ]

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            WesternFortuneDataV2(**data)
        assert "3양태 percent 합계가 범위를 벗어났습니다" in str(exc_info.value)

    def test_percent_sum_with_wide_tolerance(self):
        """percent 합계가 50~150 범위 내면 검증 성공 (LLM 오차 허용)"""
        # Arrange
        data = {
            "summary": "오행 분석",
            "list": [
                {"code": "WOOD", "label": "목", "percent": 20.0},
                {"code": "FIRE", "label": "화", "percent": 20.0},
                {"code": "EARTH", "label": "토", "percent": 20.0},
                {"code": "METAL", "label": "금", "percent": 20.0},
                {"code": "WATER", "label": "수", "percent": 40.0},  # 합계 120 (범위 내)
            ],
        }

        # Act
        five_elements = FiveElements(**data)

        # Assert
        total = sum(item.percent for item in five_elements.elements_list)
        assert 50.0 <= total <= 150.0


# ============================================================
# 테스트 케이스 5: 필수 필드 누락 테스트
# ============================================================

class TestRequiredFieldsMissing:
    """필수 필드 누락 테스트"""

    def test_saju_data_missing_element(self):
        """SajuDataV2에서 element 필드 누락 시 검증 실패"""
        # Arrange
        data = create_valid_eastern_data()
        del data["element"]

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            SajuDataV2(**data)
        assert "element" in str(exc_info.value)

    def test_saju_data_missing_chart(self):
        """SajuDataV2에서 chart 필드 누락 시 검증 실패"""
        # Arrange
        data = create_valid_eastern_data()
        del data["chart"]

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            SajuDataV2(**data)
        assert "chart" in str(exc_info.value)

    def test_pillar_missing_gan(self):
        """Pillar에서 gan 필드 누락 시 검증 실패"""
        # Arrange
        pillar_data = {
            "gan_code": "GAP",
            "ji": "子",
            "ji_code": "JA",
            "element_code": "WOOD",
            "ten_god_code": "BI_GYEON",
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Pillar(**pillar_data)
        assert "gan" in str(exc_info.value)

    def test_pillar_missing_ji(self):
        """Pillar에서 ji 필드 누락 시 검증 실패"""
        # Arrange
        pillar_data = {
            "gan": "甲",
            "gan_code": "GAP",
            "ji_code": "JA",
            "element_code": "WOOD",
            "ten_god_code": "BI_GYEON",
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Pillar(**pillar_data)
        assert "ji" in str(exc_info.value)

    def test_five_elements_missing_summary(self):
        """FiveElements에서 summary 필드 누락 시 검증 실패"""
        # Arrange
        data = {
            "list": [
                {"code": "WOOD", "label": "목", "percent": 20.0},
                {"code": "FIRE", "label": "화", "percent": 20.0},
                {"code": "EARTH", "label": "토", "percent": 20.0},
                {"code": "METAL", "label": "금", "percent": 20.0},
                {"code": "WATER", "label": "수", "percent": 20.0},
            ],
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            FiveElements(**data)
        assert "summary" in str(exc_info.value)

    def test_western_fortune_missing_stats(self):
        """WesternFortuneDataV2에서 stats 필드 누락 시 검증 실패"""
        # Arrange
        data = create_valid_western_data()
        del data["stats"]

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            WesternFortuneDataV2(**data)
        assert "stats" in str(exc_info.value)

    def test_western_stats_missing_main_sign(self):
        """WesternStats에서 main_sign 필드 누락 시 검증 실패"""
        # Arrange
        data = create_valid_western_data()
        del data["stats"]["main_sign"]

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            WesternFortuneDataV2(**data)
        assert "main_sign" in str(exc_info.value)

    def test_fortune_content_missing_overview(self):
        """FortuneContent에서 overview 필드 누락 시 검증 실패"""
        # Arrange
        data = {
            "detailed_analysis": [
                {"title": "애정운", "content": "좋습니다."},
                {"title": "금전운", "content": "좋습니다."},
            ],
            "advice": "조언입니다.",
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            FortuneContent(**data)
        assert "overview" in str(exc_info.value)

    def test_user_fortune_missing_eastern(self):
        """UserFortune에서 eastern 필드 누락 시 검증 실패"""
        # Arrange
        data = {"western": create_valid_western_data()}

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            UserFortune(**data)
        assert "eastern" in str(exc_info.value)

    def test_user_fortune_missing_western(self):
        """UserFortune에서 western 필드 누락 시 검증 실패"""
        # Arrange
        data = {"eastern": create_valid_eastern_data()}

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            UserFortune(**data)
        assert "western" in str(exc_info.value)

    def test_saju_element_missing_code(self):
        """SajuElement에서 code 필드 누락 시 검증 실패"""
        # Arrange
        data = {"label": "목", "percent": 20.0}

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            SajuElement(**data)
        assert "code" in str(exc_info.value)

    def test_western_keyword_missing_weight(self):
        """WesternKeyword에서 weight 필드 누락 시 검증 실패"""
        # Arrange
        data = {"code": "EMPATHY", "label": "공감"}

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            WesternKeyword(**data)
        assert "weight" in str(exc_info.value)


# ============================================================
# 통합 테스트: UserFortune 전체 검증
# ============================================================

class TestUserFortuneIntegration:
    """UserFortune 통합 검증 테스트"""

    def test_valid_user_fortune_creation(self):
        """유효한 UserFortune 객체 생성 테스트"""
        # Arrange
        data = {
            "eastern": create_valid_eastern_data(),
            "western": create_valid_western_data(),
        }

        # Act
        user_fortune = UserFortune(**data)

        # Assert
        assert user_fortune.eastern.element == "WOOD"
        assert user_fortune.western.element == "FIRE"
        assert user_fortune.eastern.chart.year.gan == "甲"
        assert user_fortune.western.stats.main_sign.name == "사자자리"

    def test_user_fortune_serialization(self):
        """UserFortune JSON 직렬화 테스트"""
        # Arrange
        data = {
            "eastern": create_valid_eastern_data(),
            "western": create_valid_western_data(),
        }
        user_fortune = UserFortune(**data)

        # Act
        json_data = user_fortune.model_dump()

        # Assert
        assert "eastern" in json_data
        assert "western" in json_data
        assert json_data["eastern"]["element"] == "WOOD"
        assert json_data["western"]["element"] == "FIRE"
