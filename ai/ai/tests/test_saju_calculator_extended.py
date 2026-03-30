"""사주 계산기 확장 함수 테스트

오행 분포, 음양 비율, 십신 계산, 서양 점성술 통계 테스트
"""

import pytest

from yeji_ai.engine.saju_calculator import SajuCalculator
from yeji_ai.models.saju import FourPillars


@pytest.fixture
def calculator():
    """SajuCalculator 인스턴스"""
    return SajuCalculator()


class TestCalculateFiveElements:
    """오행 분포 계산 테스트"""

    def test_basic_distribution(self, calculator):
        """기본 오행 분포 계산"""
        # 갑자년 을축월 병인일 정묘시
        pillars = FourPillars(year="갑자", month="을축", day="병인", hour="정묘")
        result = calculator.calculate_five_elements_distribution(pillars)

        assert "list" in result
        assert len(result["list"]) == 5
        assert "dominant" in result
        assert "weak" in result

        # 모든 오행이 포함되어야 함
        codes = [e["code"] for e in result["list"]]
        assert set(codes) == {"WOOD", "FIRE", "EARTH", "METAL", "WATER"}

        # 퍼센트 합계가 100에 가까워야 함
        total_percent = sum(e["percent"] for e in result["list"])
        assert 99.0 <= total_percent <= 101.0

    def test_without_hour_pillar(self, calculator):
        """시주 없이 오행 분포 계산"""
        pillars = FourPillars(year="갑자", month="을축", day="병인", hour=None)
        result = calculator.calculate_five_elements_distribution(pillars)

        assert "list" in result
        # 6글자 (3기둥 × 2) 기준으로 계산
        total_count = sum(e["count"] for e in result["list"])
        assert total_count == 6


class TestCalculateYinYang:
    """음양 비율 계산 테스트"""

    def test_basic_ratio(self, calculator):
        """기본 음양 비율 계산"""
        # 갑(양) 자(양) 을(음) 축(음) 병(양) 인(양) 정(음) 묘(음)
        # 양: 4, 음: 4 → 균형
        pillars = FourPillars(year="갑자", month="을축", day="병인", hour="정묘")
        result = calculator.calculate_yin_yang_ratio(pillars)

        assert "yin" in result
        assert "yang" in result
        assert "balance" in result
        assert result["yin"]["percent"] + result["yang"]["percent"] == 100.0

    def test_yang_dominant(self, calculator):
        """양 우세 케이스"""
        # 갑(양) 자(양) 병(양) 인(양) 무(양) 진(양) 경(양) 오(양)
        pillars = FourPillars(year="갑자", month="병인", day="무진", hour="경오")
        result = calculator.calculate_yin_yang_ratio(pillars)

        assert result["yang"]["percent"] > result["yin"]["percent"]
        assert result["balance"] == "양성"


class TestCalculateTenGods:
    """십신 계산 테스트"""

    def test_basic_ten_gods(self, calculator):
        """기본 십신 계산"""
        # 일간: 병(화, 양)
        pillars = FourPillars(year="갑자", month="을축", day="병인", hour="정묘")
        result = calculator.calculate_ten_gods("병", pillars)

        assert "list" in result
        assert "dominant" in result
        assert "day_master_element" in result
        assert result["day_master_element"] == "FIRE"

        # 각 십신에 코드, 라벨, 퍼센트가 있어야 함
        if result["list"]:
            first = result["list"][0]
            assert "code" in first
            assert "label" in first
            assert "percent" in first

    def test_hanja_day_stem(self, calculator):
        """한자 일간 처리"""
        pillars = FourPillars(year="갑자", month="을축", day="병인", hour="정묘")
        result = calculator.calculate_ten_gods("丙", pillars)  # 한자 병

        assert result["day_master_element"] == "FIRE"


class TestWesternStats:
    """서양 점성술 통계 테스트"""

    def test_aries_stats(self, calculator):
        """양자리(3/21~4/19) 통계"""
        result = calculator.calculate_western_stats("1990-04-01")

        assert result["main_sign"]["code"] == "ARIES"
        assert result["main_sign"]["name"] == "양자리"
        assert result["element"] == "FIRE"
        assert result["modality"] == "CARDINAL"

    def test_taurus_stats(self, calculator):
        """황소자리(4/20~5/20) 통계"""
        result = calculator.calculate_western_stats("1990-05-15")

        assert result["main_sign"]["code"] == "TAURUS"
        assert result["element"] == "EARTH"
        assert result["modality"] == "FIXED"

    def test_element_distribution(self, calculator):
        """4원소 분포 테스트"""
        result = calculator.calculate_western_stats("1990-04-01")  # 양자리(불)

        # 불 원소가 50%여야 함
        fire_elem = next(
            e for e in result["element_4_distribution"] if e["code"] == "FIRE"
        )
        assert fire_elem["percent"] == 50.0

        # 나머지는 16.7%씩
        earth_elem = next(
            e for e in result["element_4_distribution"] if e["code"] == "EARTH"
        )
        assert earth_elem["percent"] == 16.7

    def test_modality_distribution(self, calculator):
        """3양태 분포 테스트"""
        result = calculator.calculate_western_stats("1990-04-01")  # 양자리(활동궁)

        # 활동궁이 50%여야 함
        cardinal = next(
            m for m in result["modality_3_distribution"] if m["code"] == "CARDINAL"
        )
        assert cardinal["percent"] == 50.0

        # 나머지는 25%씩
        fixed = next(
            m for m in result["modality_3_distribution"] if m["code"] == "FIXED"
        )
        assert fixed["percent"] == 25.0

    def test_capricorn_boundary(self, calculator):
        """염소자리 경계일 테스트 (12/22~1/19)"""
        # 12월 25일 → 염소자리
        result = calculator.calculate_western_stats("1990-12-25")
        assert result["main_sign"]["code"] == "CAPRICORN"

        # 1월 10일 → 염소자리
        result = calculator.calculate_western_stats("1990-01-10")
        assert result["main_sign"]["code"] == "CAPRICORN"

        # 1월 20일 → 물병자리
        result = calculator.calculate_western_stats("1990-01-20")
        assert result["main_sign"]["code"] == "AQUARIUS"


class TestZodiacHelpers:
    """별자리 헬퍼 함수 테스트"""

    def test_get_sun_sign_code(self, calculator):
        """별자리 코드 반환 테스트"""
        assert calculator.get_sun_sign_code("1990-04-01") == "ARIES"
        assert calculator.get_sun_sign_code("1990-08-15") == "LEO"

    def test_get_zodiac_element(self, calculator):
        """별자리 원소 반환 테스트"""
        assert calculator.get_zodiac_element("ARIES") == "FIRE"
        assert calculator.get_zodiac_element("TAURUS") == "EARTH"
        assert calculator.get_zodiac_element("GEMINI") == "AIR"
        assert calculator.get_zodiac_element("CANCER") == "WATER"

    def test_get_zodiac_modality(self, calculator):
        """별자리 양태 반환 테스트"""
        assert calculator.get_zodiac_modality("ARIES") == "CARDINAL"
        assert calculator.get_zodiac_modality("LEO") == "FIXED"
        assert calculator.get_zodiac_modality("SAGITTARIUS") == "MUTABLE"
