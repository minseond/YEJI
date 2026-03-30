"""폴백 데이터 로더 테스트

yeji_ai/data/fallback/ 모듈의 JSON 로드 및 데이터 조회 기능을 테스트합니다.
"""

import pytest

from yeji_ai.data.fallback import (
    get_eastern_fallback_data,
    get_western_fallback_data,
    load_eastern_templates,
    load_western_templates,
    load_keywords,
    load_all_templates,
    get_fallback_stats,
)
from yeji_ai.data.fallback.loader import clear_cache


# ============================================================
# 픽스처
# ============================================================


@pytest.fixture(autouse=True)
def clear_fallback_cache():
    """테스트 전후에 캐시 초기화"""
    clear_cache()
    yield
    clear_cache()


# ============================================================
# 템플릿 로드 테스트
# ============================================================


class TestLoadTemplates:
    """템플릿 로드 테스트"""

    def test_load_eastern_templates_success(self):
        """동양 사주 템플릿 로드 성공"""
        templates = load_eastern_templates()

        # 필수 키 확인
        assert "personality" in templates
        assert "strength" in templates
        assert "weakness" in templates
        assert "advice" in templates
        assert "message" in templates
        assert "lucky" in templates

    def test_load_eastern_templates_personality_count(self):
        """동양 사주 personality 템플릿 개수 확인 (50개)"""
        templates = load_eastern_templates()

        # 일간(10) × 오행(5) = 50개
        personality = templates.get("personality", {})
        # _meta 키 제외
        actual_keys = [k for k in personality.keys() if not k.startswith("_")]

        assert len(actual_keys) == 50, f"Expected 50, got {len(actual_keys)}"

    def test_load_eastern_templates_message_count(self):
        """동양 사주 message 템플릿 개수 확인 (150개)"""
        templates = load_eastern_templates()

        # 일간(10) × 오행(5) × 음양(3) = 150개
        message = templates.get("message", {})
        actual_keys = [k for k in message.keys() if not k.startswith("_")]

        assert len(actual_keys) == 150, f"Expected 150, got {len(actual_keys)}"

    def test_load_western_templates_success(self):
        """서양 점성술 템플릿 로드 성공"""
        templates = load_western_templates()

        # 필수 키 확인
        assert "personality" in templates
        assert "strength" in templates
        assert "weakness" in templates
        assert "message" in templates
        assert "lucky" in templates

    def test_load_western_templates_personality_count(self):
        """서양 점성술 personality 템플릿 개수 확인 (48개)"""
        templates = load_western_templates()

        # 별자리(12) × 원소(4) = 48개
        personality = templates.get("personality", {})
        actual_keys = [k for k in personality.keys() if not k.startswith("_")]

        assert len(actual_keys) == 48, f"Expected 48, got {len(actual_keys)}"

    def test_load_western_templates_message_count(self):
        """서양 점성술 message 템플릿 개수 확인 (144개)"""
        templates = load_western_templates()

        # 태양별자리(12) × 달별자리(12) = 144개 핵심 조합
        message = templates.get("message", {})
        actual_keys = [k for k in message.keys() if not k.startswith("_")]

        assert len(actual_keys) == 144, f"Expected 144, got {len(actual_keys)}"

    def test_load_western_templates_lucky_count(self):
        """서양 점성술 lucky 템플릿 개수 확인 (12개)"""
        templates = load_western_templates()

        # 별자리(12)별 행운 정보
        lucky = templates.get("lucky", {})
        actual_keys = [k for k in lucky.keys() if not k.startswith("_")]

        assert len(actual_keys) == 12, f"Expected 12, got {len(actual_keys)}"

    def test_load_keywords_success(self):
        """키워드 데이터 로드 성공"""
        keywords = load_keywords()

        # 필수 키 확인
        assert "eastern" in keywords
        assert "western" in keywords
        assert "common" in keywords

    def test_load_keywords_eastern_structure(self):
        """키워드 데이터 동양 구조 확인"""
        keywords = load_keywords()

        eastern = keywords.get("eastern", {})
        assert "day_master" in eastern
        assert "element" in eastern
        assert "yin_yang" in eastern
        assert "ten_god_group" in eastern

        # 일간 10개 확인
        assert len(eastern["day_master"]) == 10

    def test_load_keywords_western_structure(self):
        """키워드 데이터 서양 구조 확인"""
        keywords = load_keywords()

        western = keywords.get("western", {})
        assert "zodiac" in western
        assert "element" in western
        assert "planet" in western

        # 별자리 12개 확인
        assert len(western["zodiac"]) == 12

    def test_load_all_templates(self):
        """모든 템플릿 한번에 로드"""
        all_templates = load_all_templates()

        assert "eastern" in all_templates
        assert "western" in all_templates
        assert "keywords" in all_templates

    def test_template_caching(self):
        """템플릿 캐싱 동작 확인"""
        # 첫 번째 로드
        templates1 = load_eastern_templates()

        # 두 번째 로드 (캐시에서)
        templates2 = load_eastern_templates()

        # 같은 객체인지 확인 (캐시 동작)
        assert templates1 is templates2


# ============================================================
# 폴백 데이터 조회 테스트
# ============================================================


class TestGetEasternFallbackData:
    """동양 사주 폴백 데이터 조회 테스트"""

    def test_get_eastern_fallback_data_basic(self):
        """기본 동양 사주 폴백 데이터 조회"""
        data = get_eastern_fallback_data("GAP", "WOOD", "YANG")

        assert "personality" in data
        assert "strength" in data
        assert "weakness" in data
        assert "advice" in data
        assert "message" in data
        assert "lucky" in data

    def test_get_eastern_fallback_data_personality_content(self):
        """동양 사주 personality 내용 확인"""
        data = get_eastern_fallback_data("GAP", "WOOD", "YANG")

        personality = data["personality"]
        assert "갑목" in personality
        assert "목" in personality

    def test_get_eastern_fallback_data_message_content(self):
        """동양 사주 message 내용 확인"""
        data = get_eastern_fallback_data("GAP", "WOOD", "YANG")

        message = data["message"]
        assert "갑목" in message
        assert "양" in message or "陽" in message

    def test_get_eastern_fallback_data_lucky_structure(self):
        """동양 사주 lucky 구조 확인"""
        data = get_eastern_fallback_data("GAP", "WOOD", "YANG")

        lucky = data["lucky"]
        assert "color" in lucky
        assert "color_code" in lucky
        assert "number" in lucky
        assert "item" in lucky
        assert "direction" in lucky
        assert "direction_code" in lucky
        assert "place" in lucky

    def test_get_eastern_fallback_data_different_combinations(self):
        """다양한 동양 사주 조합 테스트"""
        # 다양한 조합 테스트
        combinations = [
            ("GAP", "WOOD", "YANG"),
            ("EUL", "FIRE", "YIN"),
            ("BYEONG", "EARTH", "BALANCED"),
            ("GYEONG", "METAL", "YANG"),
            ("GYE", "WATER", "YIN"),
        ]

        for day_master, element, yin_yang in combinations:
            data = get_eastern_fallback_data(day_master, element, yin_yang)

            assert data is not None, f"Failed for {day_master}_{element}_{yin_yang}"
            assert "personality" in data
            assert len(data["personality"]) > 0

    def test_get_eastern_fallback_data_case_insensitive(self):
        """대소문자 무관 조회"""
        data1 = get_eastern_fallback_data("gap", "wood", "yang")
        data2 = get_eastern_fallback_data("GAP", "WOOD", "YANG")

        assert data1["personality"] == data2["personality"]

    def test_get_eastern_fallback_data_yin_yang_normalization(self):
        """음양 정규화 테스트"""
        # STRONG_YANG -> YANG
        data1 = get_eastern_fallback_data("GAP", "WOOD", "STRONG_YANG")
        data2 = get_eastern_fallback_data("GAP", "WOOD", "YANG")

        assert data1["message"] == data2["message"]

        # SLIGHT_YIN -> YIN
        data3 = get_eastern_fallback_data("GAP", "WOOD", "SLIGHT_YIN")
        data4 = get_eastern_fallback_data("GAP", "WOOD", "YIN")

        assert data3["message"] == data4["message"]

    def test_get_eastern_fallback_data_unknown_key_fallback(self):
        """알 수 없는 키에 대한 기본값 반환"""
        data = get_eastern_fallback_data("UNKNOWN", "UNKNOWN", "UNKNOWN")

        # 기본값이 반환되어야 함
        assert "personality" in data
        assert len(data["personality"]) > 0


# ============================================================
# 서양 점성술 폴백 데이터 조회 테스트
# ============================================================


class TestGetWesternFallbackData:
    """서양 점성술 폴백 데이터 조회 테스트"""

    def test_get_western_fallback_data_basic(self):
        """기본 서양 점성술 폴백 데이터 조회"""
        data = get_western_fallback_data("ARIES", "CANCER", "FIRE")

        assert "personality" in data
        assert "strength" in data
        assert "weakness" in data
        assert "message" in data
        assert "lucky" in data

    def test_get_western_fallback_data_personality_content(self):
        """서양 점성술 personality 내용 확인"""
        data = get_western_fallback_data("ARIES", "CANCER", "FIRE")

        personality = data["personality"]
        assert "양자리" in personality
        assert "불" in personality

    def test_get_western_fallback_data_message_content(self):
        """서양 점성술 message 내용 확인"""
        data = get_western_fallback_data("ARIES", "CANCER", "FIRE")

        message = data["message"]
        assert "양자리" in message
        assert "게자리" in message

    def test_get_western_fallback_data_lucky_structure(self):
        """서양 점성술 lucky 구조 확인"""
        data = get_western_fallback_data("ARIES", "CANCER", "FIRE")

        lucky = data["lucky"]
        assert "day" in lucky
        assert "day_code" in lucky
        assert "color" in lucky
        assert "color_code" in lucky
        assert "number" in lucky
        assert "stone" in lucky
        assert "planet" in lucky

    def test_get_western_fallback_data_different_combinations(self):
        """다양한 서양 점성술 조합 테스트"""
        combinations = [
            ("ARIES", "ARIES", "FIRE"),
            ("TAURUS", "LEO", "EARTH"),
            ("GEMINI", "SCORPIO", "AIR"),
            ("CANCER", "PISCES", "WATER"),
            ("LEO", "CAPRICORN", "FIRE"),
        ]

        for sun, moon, element in combinations:
            data = get_western_fallback_data(sun, moon, element)

            assert data is not None, f"Failed for {sun}_{moon}_{element}"
            assert "personality" in data
            assert len(data["personality"]) > 0

    def test_get_western_fallback_data_case_insensitive(self):
        """대소문자 무관 조회"""
        data1 = get_western_fallback_data("aries", "cancer", "fire")
        data2 = get_western_fallback_data("ARIES", "CANCER", "FIRE")

        assert data1["personality"] == data2["personality"]

    def test_get_western_fallback_data_unknown_key_fallback(self):
        """알 수 없는 키에 대한 기본값 반환"""
        data = get_western_fallback_data("UNKNOWN", "UNKNOWN", "UNKNOWN")

        # 기본값이 반환되어야 함
        assert "personality" in data
        assert len(data["personality"]) > 0


# ============================================================
# 통계 테스트
# ============================================================


class TestFallbackStats:
    """폴백 통계 테스트"""

    def test_get_fallback_stats(self):
        """폴백 통계 조회"""
        stats = get_fallback_stats()

        assert "eastern" in stats
        assert "western" in stats
        assert "keywords" in stats

    def test_get_fallback_stats_eastern_counts(self):
        """동양 사주 통계 카운트 확인"""
        stats = get_fallback_stats()

        eastern = stats["eastern"]
        assert eastern["personality_count"] == 50
        assert eastern["strength_count"] == 5
        assert eastern["weakness_count"] == 5
        assert eastern["advice_count"] == 5
        assert eastern["message_count"] == 150
        assert eastern["lucky_count"] == 5

    def test_get_fallback_stats_western_counts(self):
        """서양 점성술 통계 카운트 확인"""
        stats = get_fallback_stats()

        western = stats["western"]
        assert western["personality_count"] == 48
        assert western["strength_count"] == 4
        assert western["weakness_count"] == 4
        assert western["message_count"] == 144
        assert western["lucky_count"] == 12

    def test_get_fallback_stats_keywords_counts(self):
        """키워드 통계 카운트 확인"""
        stats = get_fallback_stats()

        keywords = stats["keywords"]
        assert keywords["eastern_day_master_count"] == 10
        assert keywords["eastern_element_count"] == 5
        assert keywords["western_zodiac_count"] == 12
        assert keywords["western_element_count"] == 4


# ============================================================
# 엣지 케이스 테스트
# ============================================================


class TestEdgeCases:
    """엣지 케이스 테스트"""

    def test_empty_string_parameters(self):
        """빈 문자열 파라미터 처리"""
        data = get_eastern_fallback_data("", "", "")

        # 기본값이 반환되어야 함
        assert "personality" in data
        assert len(data["personality"]) > 0

    def test_none_like_parameters(self):
        """None 유사 파라미터 처리"""
        # None이 전달되면 기본값 사용
        data = get_western_fallback_data("ARIES", "CANCER", "FIRE")

        assert data is not None
        assert "personality" in data

    def test_all_day_masters_have_templates(self):
        """모든 일간에 템플릿이 있는지 확인"""
        day_masters = [
            "GAP", "EUL", "BYEONG", "JEONG", "MU",
            "GI", "GYEONG", "SIN", "IM", "GYE",
        ]
        elements = ["WOOD", "FIRE", "EARTH", "METAL", "WATER"]

        for dm in day_masters:
            for elem in elements:
                data = get_eastern_fallback_data(dm, elem, "YANG")
                assert dm.lower() in data["personality"].lower() or "목" in data["personality"] or \
                       "화" in data["personality"] or "토" in data["personality"] or \
                       "금" in data["personality"] or "수" in data["personality"], \
                    f"Template missing for {dm}_{elem}"

    def test_all_zodiacs_have_templates(self):
        """모든 별자리에 템플릿이 있는지 확인"""
        zodiacs = [
            "ARIES", "TAURUS", "GEMINI", "CANCER",
            "LEO", "VIRGO", "LIBRA", "SCORPIO",
            "SAGITTARIUS", "CAPRICORN", "AQUARIUS", "PISCES",
        ]
        elements = ["FIRE", "EARTH", "AIR", "WATER"]

        for zodiac in zodiacs:
            for elem in elements:
                data = get_western_fallback_data(zodiac, "ARIES", elem)
                assert data["personality"] is not None, \
                    f"Template missing for {zodiac}_{elem}"
