"""운세 캐시 시스템 테스트

태스크 #23: 주요 조합 사전 캐싱 시스템
"""

import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from yeji_ai.data.fortune_cache import (
    CacheKeyBuilder,
    clear_cache,
    get_cache_stats,
    get_eastern_cached,
    get_western_cached,
    load_fortune_cache,
)


class TestCacheKeyBuilder:
    """캐시 키 빌더 테스트"""

    def test_build_eastern_key_basic(self):
        """동양 사주 기본 키 생성"""
        key = CacheKeyBuilder.build_eastern_key(
            day_gan_code="GAP",
            dominant_element="WOOD",
            yin_yang="YANG",
        )
        assert key == "GAP_WOOD_YANG"

    def test_build_eastern_key_lowercase(self):
        """소문자 입력도 대문자로 정규화"""
        key = CacheKeyBuilder.build_eastern_key(
            day_gan_code="gap",
            dominant_element="wood",
            yin_yang="yang",
        )
        assert key == "GAP_WOOD_YANG"

    def test_build_eastern_key_yinyang_normalize(self):
        """음양 상태 정규화 (STRONG_YANG -> YANG)"""
        key = CacheKeyBuilder.build_eastern_key(
            day_gan_code="GYEONG",
            dominant_element="METAL",
            yin_yang="STRONG_YANG",
        )
        assert key == "GYEONG_METAL_YANG"

        key = CacheKeyBuilder.build_eastern_key(
            day_gan_code="SIN",
            dominant_element="WATER",
            yin_yang="SLIGHT_YIN",
        )
        assert key == "SIN_WATER_YIN"

    def test_build_western_key_basic(self):
        """서양 점성술 기본 키 생성"""
        key = CacheKeyBuilder.build_western_key(
            sun_sign="ARIES",
            moon_sign="CANCER",
        )
        assert key == "ARIES_CANCER"

    def test_build_western_key_lowercase(self):
        """소문자 입력도 대문자로 정규화"""
        key = CacheKeyBuilder.build_western_key(
            sun_sign="leo",
            moon_sign="scorpio",
        )
        assert key == "LEO_SCORPIO"

    def test_get_all_eastern_keys_count(self):
        """동양 사주 전체 키 수: 10 × 5 × 3 = 150"""
        keys = CacheKeyBuilder.get_all_eastern_keys()
        assert len(keys) == 10 * 5 * 3  # 150

    def test_get_all_eastern_keys_format(self):
        """동양 사주 키 형식 검증"""
        keys = CacheKeyBuilder.get_all_eastern_keys()

        for key in keys:
            parts = key.split("_")
            assert len(parts) == 3
            assert parts[0] in CacheKeyBuilder.EASTERN_DAY_MASTERS
            assert parts[1] in CacheKeyBuilder.EASTERN_ELEMENTS
            assert parts[2] in CacheKeyBuilder.EASTERN_YINYANG

    def test_get_all_western_keys_count(self):
        """서양 점성술 전체 키 수: 12 × 12 = 144"""
        keys = CacheKeyBuilder.get_all_western_keys()
        assert len(keys) == 12 * 12  # 144

    def test_get_all_western_keys_format(self):
        """서양 점성술 키 형식 검증"""
        keys = CacheKeyBuilder.get_all_western_keys()

        for key in keys:
            parts = key.split("_")
            assert len(parts) == 2
            assert parts[0] in CacheKeyBuilder.WESTERN_ZODIACS
            assert parts[1] in CacheKeyBuilder.WESTERN_ZODIACS


class TestCacheOperations:
    """캐시 조회/로드 테스트"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """각 테스트 전 캐시 초기화"""
        clear_cache()

    def test_get_eastern_cached_miss(self):
        """동양 사주 캐시 미스"""
        result = get_eastern_cached(
            day_gan_code="GAP",
            dominant_element="WOOD",
            yin_yang="YANG",
        )
        assert result is None

    def test_get_western_cached_miss(self):
        """서양 점성술 캐시 미스"""
        result = get_western_cached(
            sun_sign="ARIES",
            moon_sign="CANCER",
        )
        assert result is None

    def test_load_fortune_cache_empty(self):
        """빈 캐시 로드"""
        # 캐시 파일이 없거나 빈 경우
        result = load_fortune_cache()

        # 스키마 주석만 있으므로 0개로 카운트됨
        assert "eastern" in result
        assert "western" in result

    def test_get_cache_stats(self):
        """캐시 통계 조회"""
        load_fortune_cache()
        stats = get_cache_stats()

        assert "loaded" in stats
        assert "eastern" in stats
        assert "western" in stats
        assert "cached" in stats["eastern"]
        assert "total" in stats["eastern"]
        assert "coverage" in stats["eastern"]


class TestCacheWithMockData:
    """목 데이터를 사용한 캐시 테스트"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """각 테스트 전 캐시 초기화"""
        clear_cache()

    def test_eastern_cache_hit_with_mock(self):
        """동양 사주 캐시 히트 (목 데이터)"""
        mock_cache: dict[str, Any] = {
            "GAP_WOOD_YANG": {
                "personality": "진취적이고 리더십이 강하오.",
                "strength": "창의력과 추진력이 뛰어나오.",
                "weakness": "급한 성격에 주의하시오.",
                "advice": "차분함을 유지하시오.",
                "summary": "목(木)이 강한 리더형",
                "message": "그대의 사주는 활력 넘치는 기운이 가득하오.",
                "badges": ["WOOD_STRONG", "YANG_DOMINANT"],
                "lucky": {
                    "color": "초록",
                    "color_code": "#228B22",
                    "direction": "동",
                    "direction_code": "E",
                },
            }
        }

        # 캐시 모듈의 전역 변수를 직접 패치
        with patch("yeji_ai.data.fortune_cache._EASTERN_CACHE", mock_cache):
            with patch("yeji_ai.data.fortune_cache._cache_loaded", True):
                result = get_eastern_cached(
                    day_gan_code="GAP",
                    dominant_element="WOOD",
                    yin_yang="YANG",
                )

                assert result is not None
                assert result["personality"] == "진취적이고 리더십이 강하오."
                assert "WOOD_STRONG" in result["badges"]

    def test_western_cache_hit_with_mock(self):
        """서양 점성술 캐시 히트 (목 데이터)"""
        mock_cache: dict[str, Any] = {
            "ARIES_CANCER": {
                "personality": "용감하면서도 감성적인 면이 있어요.",
                "strength": "행동력과 공감능력이 뛰어나요.",
                "weakness": "감정 기복에 주의하세요.",
                "advice": "균형을 유지하세요.",
                "summary": "양자리 태양, 게자리 달의 조합",
                "message": "당신은 열정과 감성을 모두 가졌어요.",
                "badges": ["FIRE_DOMINANT", "MARS_STRONG"],
                "keywords": [
                    {"code": "PASSION", "label": "열정", "weight": 0.9},
                ],
                "lucky": {
                    "day": "화요일",
                    "day_code": "TUE",
                    "color": "빨강",
                    "color_code": "#FF0000",
                },
            }
        }

        with patch("yeji_ai.data.fortune_cache._WESTERN_CACHE", mock_cache):
            with patch("yeji_ai.data.fortune_cache._cache_loaded", True):
                result = get_western_cached(
                    sun_sign="ARIES",
                    moon_sign="CANCER",
                )

                assert result is not None
                assert "용감하면서도" in result["personality"]
                assert "FIRE_DOMINANT" in result["badges"]


class TestCacheKeyEdgeCases:
    """캐시 키 엣지 케이스 테스트"""

    def test_empty_values(self):
        """빈 값 처리"""
        key = CacheKeyBuilder.build_eastern_key(
            day_gan_code="",
            dominant_element="",
            yin_yang="",
        )
        # 빈 값은 기본값으로 대체
        assert key == "GAP_WOOD_BALANCED"

    def test_none_values(self):
        """None 값 처리"""
        key = CacheKeyBuilder.build_eastern_key(
            day_gan_code=None,  # type: ignore
            dominant_element=None,  # type: ignore
            yin_yang=None,  # type: ignore
        )
        assert key == "GAP_WOOD_BALANCED"

    def test_western_empty_values(self):
        """서양 점성술 빈 값 처리"""
        key = CacheKeyBuilder.build_western_key(
            sun_sign="",
            moon_sign="",
        )
        assert key == "ARIES_ARIES"
