"""LLM 완전 실패 시 규칙 기반 폴백 시스템 테스트

EasternFallbackGenerator와 WesternFallbackGenerator의 동작을 검증합니다.
"""

from unittest.mock import MagicMock

import pytest

from yeji_ai.services.rule_based_fallback import (
    DAY_MASTER_PERSONALITY,
    ELEMENT_TRAITS,
    EasternFallbackGenerator,
    SUN_SIGN_PERSONALITY,
    WesternFallbackGenerator,
    WESTERN_ELEMENT_TRAITS,
    ZODIAC_LUCKY_INFO,
    get_eastern_fallback,
    get_western_fallback,
)


# ============================================================
# 테스트 픽스처
# ============================================================


@pytest.fixture
def mock_eastern_chart() -> MagicMock:
    """동양 사주 차트 Mock 객체"""
    chart = MagicMock()

    # 일주 설정
    chart.day.gan = "甲"
    chart.day.gan_code.value = "GAP"
    chart.day.gan_code.hangul = "갑"
    chart.day.ji = "子"
    chart.day.ji_code.value = "JA"
    chart.day.ji_code.hangul = "자"
    chart.day.element_code.label_ko = "목"

    # 연주 설정
    chart.year.gan = "己"
    chart.year.gan_code.hangul = "기"
    chart.year.ji = "卯"
    chart.year.ji_code.hangul = "묘"

    # 월주 설정
    chart.month.gan = "丁"
    chart.month.gan_code.hangul = "정"
    chart.month.ji = "卯"
    chart.month.ji_code.hangul = "묘"

    # 시주 없음
    chart.hour = None

    return chart


@pytest.fixture
def mock_eastern_stats() -> MagicMock:
    """동양 사주 통계 Mock 객체"""
    stats = MagicMock()

    # 오행 통계
    stats.five_elements = {
        "summary": "목(木)이 강하고 수(水)가 약합니다.",
        "elements": [
            {"code": "WOOD", "label": "목", "value": 3, "percent": 37.5},
            {"code": "FIRE", "label": "화", "value": 2, "percent": 25.0},
            {"code": "EARTH", "label": "토", "value": 1, "percent": 12.5},
            {"code": "METAL", "label": "금", "value": 2, "percent": 25.0},
            {"code": "WATER", "label": "수", "value": 0, "percent": 0.0},
        ],
        "strong": "WOOD",
        "weak": "WATER",
    }

    # 음양 통계
    stats.yin_yang.yang = 55
    stats.yin_yang.yin = 45
    stats.yin_yang.balance.label_ko = "약간 양"

    # 십신 통계
    stats.ten_gods = {
        "summary": "비겁이 우세하여 자기주도성이 강합니다.",
        "gods": [
            {
                "code": "BI_GYEON",
                "label": "비견",
                "group_code": "BI_GYEOP",
                "value": 2,
                "percent": 33.3,
            },
        ],
        "dominant": "BI_GYEOP",
    }

    # 강약점
    stats.strength = "창의력과 리더십이 뛰어남"
    stats.weakness = "결단력이 부족할 수 있음"

    return stats


@pytest.fixture
def mock_western_big_three() -> dict:
    """서양 빅3 Mock 객체"""
    return {
        "sun": {"sign_code": "ARIES", "house_number": 1, "summary": "양자리 태양"},
        "moon": {"sign_code": "SCORPIO", "house_number": 4, "summary": "전갈자리 달"},
        "rising": {"sign_code": "LEO", "house_number": 1, "summary": "사자자리 상승궁"},
    }


@pytest.fixture
def mock_western_element_stats() -> dict:
    """서양 원소 통계 Mock 객체"""
    return {
        "summary": "불 원소가 우세합니다",
        "distribution": [
            {"code": "FIRE", "label": "불", "value": 4, "percent": 40.0},
            {"code": "EARTH", "label": "흙", "value": 2, "percent": 20.0},
            {"code": "AIR", "label": "공기", "value": 2, "percent": 20.0},
            {"code": "WATER", "label": "물", "value": 2, "percent": 20.0},
        ],
        "dominant": "FIRE",
    }


# ============================================================
# 매핑 테이블 테스트
# ============================================================


class TestMappingTables:
    """매핑 테이블 데이터 검증"""

    def test_day_master_personality_has_all_10_codes(self) -> None:
        """일간 성격 매핑 테이블에 10개 천간이 모두 있는지 확인"""
        expected_codes = ["GAP", "EUL", "BYEONG", "JEONG", "MU", "GI", "GYEONG", "SIN", "IM", "GYE"]
        for code in expected_codes:
            assert code in DAY_MASTER_PERSONALITY
            assert "hangul" in DAY_MASTER_PERSONALITY[code]
            assert "traits" in DAY_MASTER_PERSONALITY[code]
            assert "description" in DAY_MASTER_PERSONALITY[code]
            assert len(DAY_MASTER_PERSONALITY[code]["traits"]) >= 3

    def test_element_traits_has_all_5_elements(self) -> None:
        """오행 특성 매핑 테이블에 5개 오행이 모두 있는지 확인"""
        expected_elements = ["WOOD", "FIRE", "EARTH", "METAL", "WATER"]
        for element in expected_elements:
            assert element in ELEMENT_TRAITS
            assert "label_ko" in ELEMENT_TRAITS[element]
            assert "label_hanja" in ELEMENT_TRAITS[element]
            assert "strong" in ELEMENT_TRAITS[element]
            assert "weak" in ELEMENT_TRAITS[element]
            assert "lucky" in ELEMENT_TRAITS[element]

    def test_element_lucky_has_required_fields(self) -> None:
        """오행 행운 정보에 필수 필드가 있는지 확인"""
        required_fields = ["color", "color_code", "direction", "direction_code", "place"]
        for element, info in ELEMENT_TRAITS.items():
            for field in required_fields:
                assert field in info["lucky"], f"{element}의 lucky에 {field}가 없음"

    def test_sun_sign_personality_has_all_12_signs(self) -> None:
        """태양 별자리 성격 매핑 테이블에 12개 별자리가 모두 있는지 확인"""
        expected_signs = [
            "ARIES",
            "TAURUS",
            "GEMINI",
            "CANCER",
            "LEO",
            "VIRGO",
            "LIBRA",
            "SCORPIO",
            "SAGITTARIUS",
            "CAPRICORN",
            "AQUARIUS",
            "PISCES",
        ]
        for sign in expected_signs:
            assert sign in SUN_SIGN_PERSONALITY
            assert "label_ko" in SUN_SIGN_PERSONALITY[sign]
            assert "traits" in SUN_SIGN_PERSONALITY[sign]
            assert "description" in SUN_SIGN_PERSONALITY[sign]

    def test_zodiac_lucky_info_has_all_12_signs(self) -> None:
        """별자리 행운 정보에 12개 별자리가 모두 있는지 확인"""
        expected_signs = [
            "ARIES",
            "TAURUS",
            "GEMINI",
            "CANCER",
            "LEO",
            "VIRGO",
            "LIBRA",
            "SCORPIO",
            "SAGITTARIUS",
            "CAPRICORN",
            "AQUARIUS",
            "PISCES",
        ]
        required_fields = ["day", "day_code", "color", "color_code", "number", "stone", "planet"]
        for sign in expected_signs:
            assert sign in ZODIAC_LUCKY_INFO
            for field in required_fields:
                assert field in ZODIAC_LUCKY_INFO[sign], f"{sign}의 lucky에 {field}가 없음"

    def test_western_element_traits_has_all_4_elements(self) -> None:
        """서양 원소 특성에 4개 원소가 모두 있는지 확인"""
        expected_elements = ["FIRE", "EARTH", "AIR", "WATER"]
        for element in expected_elements:
            assert element in WESTERN_ELEMENT_TRAITS
            assert "label_ko" in WESTERN_ELEMENT_TRAITS[element]
            assert "signs" in WESTERN_ELEMENT_TRAITS[element]
            assert "badge" in WESTERN_ELEMENT_TRAITS[element]


# ============================================================
# 동양 사주 폴백 생성기 테스트
# ============================================================


class TestEasternFallbackGenerator:
    """동양 사주 폴백 생성기 테스트"""

    def test_generate_returns_all_required_fields(
        self,
        mock_eastern_chart: MagicMock,
        mock_eastern_stats: MagicMock,
    ) -> None:
        """생성 결과에 모든 필수 필드가 있는지 확인"""
        generator = EasternFallbackGenerator()
        result = generator.generate(mock_eastern_chart, mock_eastern_stats)

        required_fields = [
            "personality",
            "strength",
            "weakness",
            "advice",
            "badges",
            "lucky",
            "message",
            "summary",
        ]
        for field in required_fields:
            assert field in result, f"결과에 {field}가 없음"

    def test_generate_personality_contains_day_master_info(
        self,
        mock_eastern_chart: MagicMock,
        mock_eastern_stats: MagicMock,
    ) -> None:
        """성격 분석에 일간 정보가 포함되는지 확인"""
        generator = EasternFallbackGenerator()
        result = generator.generate(mock_eastern_chart, mock_eastern_stats)

        # 갑목 일간 정보가 포함되어야 함
        assert "갑목" in result["personality"]

    def test_generate_badges_contains_element_badges(
        self,
        mock_eastern_chart: MagicMock,
        mock_eastern_stats: MagicMock,
    ) -> None:
        """배지 목록에 오행 배지가 포함되는지 확인"""
        generator = EasternFallbackGenerator()
        result = generator.generate(mock_eastern_chart, mock_eastern_stats)

        badges = result["badges"]
        assert "WOOD_STRONG" in badges  # 강한 오행
        assert "WATER_WEAK" in badges  # 약한 오행

    def test_generate_badges_contains_ten_god_badge(
        self,
        mock_eastern_chart: MagicMock,
        mock_eastern_stats: MagicMock,
    ) -> None:
        """배지 목록에 십신 배지가 포함되는지 확인"""
        generator = EasternFallbackGenerator()
        result = generator.generate(mock_eastern_chart, mock_eastern_stats)

        badges = result["badges"]
        assert "BI_GYEOP_DOMINANT" in badges  # 비겁 우세

    def test_generate_lucky_based_on_weak_element(
        self,
        mock_eastern_chart: MagicMock,
        mock_eastern_stats: MagicMock,
    ) -> None:
        """행운 정보가 약한 오행(수)을 보완하는 방향인지 확인"""
        generator = EasternFallbackGenerator()
        result = generator.generate(mock_eastern_chart, mock_eastern_stats)

        lucky = result["lucky"]
        # 수(WATER)가 약하면 검정/파랑, 북쪽 방향 추천
        assert lucky["direction_code"] == "N"  # 북쪽
        assert "검정" in lucky["color"] or "파랑" in lucky["color"]

    def test_generate_message_uses_hao_style(
        self,
        mock_eastern_chart: MagicMock,
        mock_eastern_stats: MagicMock,
    ) -> None:
        """메시지가 하오체로 작성되는지 확인"""
        generator = EasternFallbackGenerator()
        result = generator.generate(mock_eastern_chart, mock_eastern_stats)

        message = result["message"]
        # 하오체 종결어미 확인
        assert "소" in message or "오" in message

    def test_generate_summary_format(
        self,
        mock_eastern_chart: MagicMock,
        mock_eastern_stats: MagicMock,
    ) -> None:
        """요약이 올바른 형식인지 확인"""
        generator = EasternFallbackGenerator()
        result = generator.generate(mock_eastern_chart, mock_eastern_stats)

        summary = result["summary"]
        # "X이 강한 Y형, Z 보완 필요" 형식
        assert "강한" in summary
        assert "보완" in summary

    def test_generate_handles_missing_hour_pillar(
        self,
        mock_eastern_chart: MagicMock,
        mock_eastern_stats: MagicMock,
    ) -> None:
        """시주가 없어도 정상 동작하는지 확인"""
        mock_eastern_chart.hour = None
        generator = EasternFallbackGenerator()
        result = generator.generate(mock_eastern_chart, mock_eastern_stats)

        assert result is not None
        assert "personality" in result


# ============================================================
# 서양 점성술 폴백 생성기 테스트
# ============================================================


class TestWesternFallbackGenerator:
    """서양 점성술 폴백 생성기 테스트"""

    def test_generate_returns_all_required_fields(
        self,
        mock_western_big_three: dict,
        mock_western_element_stats: dict,
    ) -> None:
        """생성 결과에 모든 필수 필드가 있는지 확인"""
        generator = WesternFallbackGenerator()
        result = generator.generate(mock_western_big_three, mock_western_element_stats)

        required_fields = [
            "personality",
            "strength",
            "weakness",
            "advice",
            "badges",
            "lucky",
            "message",
            "summary",
        ]
        for field in required_fields:
            assert field in result, f"결과에 {field}가 없음"

    def test_generate_with_sun_sign_only(self) -> None:
        """sun_sign만 제공해도 정상 동작하는지 확인"""
        generator = WesternFallbackGenerator()
        result = generator.generate(sun_sign="LEO")

        assert result is not None
        # 사자자리의 특성(자신감, 카리스마)이 포함되어야 함
        assert "자신감" in result["personality"] or "카리스마" in result["personality"]

    def test_generate_personality_contains_sun_sign_info(
        self,
        mock_western_big_three: dict,
        mock_western_element_stats: dict,
    ) -> None:
        """성격 분석에 태양 별자리 정보가 포함되는지 확인"""
        generator = WesternFallbackGenerator()
        result = generator.generate(mock_western_big_three, mock_western_element_stats)

        # 양자리 정보가 포함되어야 함
        assert "용감" in result["personality"] or "열정" in result["personality"]

    def test_generate_badges_contains_element_badge(
        self,
        mock_western_big_three: dict,
        mock_western_element_stats: dict,
    ) -> None:
        """배지 목록에 원소 배지가 포함되는지 확인"""
        generator = WesternFallbackGenerator()
        result = generator.generate(mock_western_big_three, mock_western_element_stats)

        badges = result["badges"]
        assert "FIRE_DOMINANT" in badges  # 불 원소 우세

    def test_generate_lucky_based_on_sun_sign(
        self,
        mock_western_big_three: dict,
        mock_western_element_stats: dict,
    ) -> None:
        """행운 정보가 태양 별자리 기반인지 확인"""
        generator = WesternFallbackGenerator()
        result = generator.generate(mock_western_big_three, mock_western_element_stats)

        lucky = result["lucky"]
        # 양자리 = 화요일, 화성
        assert lucky["day_code"] == "TUE"
        assert lucky["planet"] == "MARS"

    def test_generate_message_uses_heyo_style(
        self,
        mock_western_big_three: dict,
        mock_western_element_stats: dict,
    ) -> None:
        """메시지가 해요체로 작성되는지 확인"""
        generator = WesternFallbackGenerator()
        result = generator.generate(mock_western_big_three, mock_western_element_stats)

        message = result["message"]
        # 해요체 종결어미 확인
        assert "요" in message

    def test_generate_without_big_three(self) -> None:
        """big_three 없이도 정상 동작하는지 확인"""
        generator = WesternFallbackGenerator()
        result = generator.generate(sun_sign="TAURUS")

        assert result is not None
        # 황소자리의 특성(안정적, 인내심)이 포함되어야 함
        assert "안정" in result["personality"] or "인내" in result["personality"]

    def test_generate_infers_element_from_sun_sign(self) -> None:
        """태양 별자리에서 원소를 추론하는지 확인"""
        generator = WesternFallbackGenerator()

        # 게자리는 물 원소
        result = generator.generate(sun_sign="CANCER")
        assert "WATER_DOMINANT" in result["badges"]

        # 쌍둥이자리는 공기 원소
        result = generator.generate(sun_sign="GEMINI")
        assert "AIR_DOMINANT" in result["badges"]


# ============================================================
# 통합 함수 테스트
# ============================================================


class TestIntegrationFunctions:
    """통합 폴백 함수 테스트"""

    def test_get_eastern_fallback_returns_valid_result(
        self,
        mock_eastern_chart: MagicMock,
        mock_eastern_stats: MagicMock,
    ) -> None:
        """get_eastern_fallback이 유효한 결과를 반환하는지 확인"""
        result = get_eastern_fallback(mock_eastern_chart, mock_eastern_stats)

        assert result is not None
        assert "personality" in result
        assert "badges" in result
        assert "lucky" in result

    def test_get_western_fallback_returns_valid_result(
        self,
        mock_western_big_three: dict,
        mock_western_element_stats: dict,
    ) -> None:
        """get_western_fallback이 유효한 결과를 반환하는지 확인"""
        result = get_western_fallback(mock_western_big_three, mock_western_element_stats)

        assert result is not None
        assert "personality" in result
        assert "badges" in result
        assert "lucky" in result

    def test_get_eastern_fallback_uses_singleton(
        self,
        mock_eastern_chart: MagicMock,
        mock_eastern_stats: MagicMock,
    ) -> None:
        """get_eastern_fallback이 싱글톤 패턴을 사용하는지 확인"""
        result1 = get_eastern_fallback(mock_eastern_chart, mock_eastern_stats)
        result2 = get_eastern_fallback(mock_eastern_chart, mock_eastern_stats)

        # 동일한 입력에 대해 동일한 구조의 결과
        assert result1.keys() == result2.keys()

    def test_get_western_fallback_with_sun_sign_only(self) -> None:
        """sun_sign만으로도 get_western_fallback이 동작하는지 확인"""
        result = get_western_fallback(sun_sign="VIRGO")

        assert result is not None
        # 처녀자리의 특성(분석력, 완벽)이 포함되어야 함
        assert "분석" in result["personality"] or "완벽" in result["personality"]


# ============================================================
# 엣지 케이스 테스트
# ============================================================


class TestEdgeCases:
    """엣지 케이스 테스트"""

    def test_eastern_fallback_with_invalid_day_master(self) -> None:
        """잘못된 일간 코드도 처리되는지 확인"""
        chart = MagicMock()
        chart.day.gan_code.value = "INVALID"
        chart.day.gan_code.hangul = "?"
        chart.day.element_code.label_ko = "?"

        stats = MagicMock()
        stats.five_elements = {"strong": "WOOD", "weak": "WATER"}
        stats.yin_yang.yang = 50
        stats.ten_gods = {"dominant": "BI_GYEOP"}

        generator = EasternFallbackGenerator()
        result = generator.generate(chart, stats)

        # 기본값(GAP)으로 폴백
        assert result is not None
        assert "personality" in result

    def test_eastern_fallback_with_missing_stats(self) -> None:
        """통계 정보가 누락되어도 처리되는지 확인"""
        chart = MagicMock()
        chart.day.gan_code.value = "GAP"

        stats = MagicMock()
        # 빈 dict 설정
        stats.five_elements = {}
        stats.yin_yang.yang = 50
        stats.ten_gods = {}

        generator = EasternFallbackGenerator()
        result = generator.generate(chart, stats)

        # 기본값으로 폴백
        assert result is not None

    def test_western_fallback_with_invalid_sun_sign(self) -> None:
        """잘못된 태양 별자리도 처리되는지 확인"""
        generator = WesternFallbackGenerator()
        result = generator.generate(sun_sign="INVALID_SIGN")

        # 기본값(ARIES)으로 폴백
        assert result is not None
        assert "personality" in result

    def test_eastern_fallback_lucky_item_varies_by_element(self) -> None:
        """약한 오행에 따라 행운 아이템이 다른지 확인"""
        generator = EasternFallbackGenerator()

        chart = MagicMock()
        chart.day.gan_code.value = "GAP"

        # WATER 약함
        stats_water = MagicMock()
        stats_water.five_elements = {"strong": "WOOD", "weak": "WATER"}
        stats_water.yin_yang.yang = 50
        stats_water.ten_gods = {"dominant": "BI_GYEOP"}

        result_water = generator.generate(chart, stats_water)

        # FIRE 약함
        stats_fire = MagicMock()
        stats_fire.five_elements = {"strong": "WOOD", "weak": "FIRE"}
        stats_fire.yin_yang.yang = 50
        stats_fire.ten_gods = {"dominant": "BI_GYEOP"}

        result_fire = generator.generate(chart, stats_fire)

        # 서로 다른 행운 아이템
        assert result_water["lucky"]["item"] != result_fire["lucky"]["item"]


# ============================================================
# 성능 테스트
# ============================================================


class TestPerformance:
    """성능 관련 테스트"""

    def test_eastern_fallback_is_fast(
        self,
        mock_eastern_chart: MagicMock,
        mock_eastern_stats: MagicMock,
    ) -> None:
        """동양 폴백 생성이 빠른지 확인 (< 10ms)"""
        import time

        generator = EasternFallbackGenerator()

        start = time.time()
        for _ in range(100):
            generator.generate(mock_eastern_chart, mock_eastern_stats)
        elapsed = time.time() - start

        # 100회 실행에 1초 미만 (개당 10ms 미만)
        assert elapsed < 1.0

    def test_western_fallback_is_fast(
        self,
        mock_western_big_three: dict,
        mock_western_element_stats: dict,
    ) -> None:
        """서양 폴백 생성이 빠른지 확인 (< 10ms)"""
        import time

        generator = WesternFallbackGenerator()

        start = time.time()
        for _ in range(100):
            generator.generate(mock_western_big_three, mock_western_element_stats)
        elapsed = time.time() - start

        # 100회 실행에 1초 미만 (개당 10ms 미만)
        assert elapsed < 1.0
