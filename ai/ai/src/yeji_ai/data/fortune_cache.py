"""운세 사전 캐싱 시스템

생년월일/성별의 주요 조합에 대해 미리 LLM 응답을 생성해서 캐싱해두고,
요청 시 캐시에서 조회하여 빠르게 응답합니다.

캐시 키 설계:
- 동양 사주 (약 60개 조합): 일간(10) × 강한오행(5) + 음양(3) → 약 60개
  예: "GAP_WOOD_YANG", "GYEONG_METAL_YIN"

- 서양 점성술 (약 144개 조합): 태양별자리(12) × 달별자리(12) → 144개
  예: "ARIES_CANCER", "LEO_SCORPIO"
"""

import json
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger()

# 캐시 저장소
_EASTERN_CACHE: dict[str, dict[str, Any]] = {}
_WESTERN_CACHE: dict[str, dict[str, Any]] = {}

# 캐시 파일 경로
_CACHE_DIR = Path(__file__).parent
EASTERN_CACHE_PATH = _CACHE_DIR / "eastern_cache.json"
WESTERN_CACHE_PATH = _CACHE_DIR / "western_cache.json"

# 캐시 로드 상태
_cache_loaded = False


# ============================================================
# 캐시 키 빌더
# ============================================================


class CacheKeyBuilder:
    """캐시 키 생성 유틸리티

    동양 사주와 서양 점성술의 캐시 키를 일관되게 생성합니다.
    """

    # 동양 사주: 일간 코드 (10개)
    EASTERN_DAY_MASTERS = [
        "GAP",
        "EUL",
        "BYEONG",
        "JEONG",
        "MU",
        "GI",
        "GYEONG",
        "SIN",
        "IM",
        "GYE",
    ]

    # 동양 사주: 오행 코드 (5개)
    EASTERN_ELEMENTS = ["WOOD", "FIRE", "EARTH", "METAL", "WATER"]

    # 동양 사주: 음양 (3개 상태)
    EASTERN_YINYANG = ["YIN", "YANG", "BALANCED"]

    # 서양 점성술: 12별자리
    WESTERN_ZODIACS = [
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

    @classmethod
    def build_eastern_key(
        cls,
        day_gan_code: str,
        dominant_element: str,
        yin_yang: str,
    ) -> str:
        """동양 사주 캐시 키 생성

        Args:
            day_gan_code: 일간 천간 코드 (예: "GAP", "GYEONG")
            dominant_element: 강한 오행 코드 (예: "WOOD", "METAL")
            yin_yang: 음양 상태 (예: "YANG", "YIN", "BALANCED")

        Returns:
            캐시 키 문자열 (예: "GAP_WOOD_YANG")
        """
        # 코드 정규화 (대문자)
        day_gan = day_gan_code.upper() if day_gan_code else "GAP"
        element = dominant_element.upper() if dominant_element else "WOOD"
        yy = yin_yang.upper() if yin_yang else "BALANCED"

        # 음양 상태 정규화 (STRONG_YANG -> YANG, STRONG_YIN -> YIN 등)
        if "YANG" in yy and yy != "YANG":
            yy = "YANG"
        elif "YIN" in yy and yy != "YIN":
            yy = "YIN"
        elif yy == "BALANCED" or yy not in cls.EASTERN_YINYANG:
            yy = "BALANCED"

        return f"{day_gan}_{element}_{yy}"

    @classmethod
    def build_western_key(
        cls,
        sun_sign: str,
        moon_sign: str,
    ) -> str:
        """서양 점성술 캐시 키 생성

        Args:
            sun_sign: 태양 별자리 코드 (예: "ARIES", "LEO")
            moon_sign: 달 별자리 코드 (예: "CANCER", "SCORPIO")

        Returns:
            캐시 키 문자열 (예: "ARIES_CANCER")
        """
        sun = sun_sign.upper() if sun_sign else "ARIES"
        moon = moon_sign.upper() if moon_sign else "ARIES"

        return f"{sun}_{moon}"

    @classmethod
    def get_all_eastern_keys(cls) -> list[str]:
        """모든 동양 사주 캐시 키 생성 (약 150개)

        10 (일간) × 5 (오행) × 3 (음양) = 150개 조합

        Returns:
            모든 가능한 캐시 키 리스트
        """
        keys = []
        for day_master in cls.EASTERN_DAY_MASTERS:
            for element in cls.EASTERN_ELEMENTS:
                for yin_yang in cls.EASTERN_YINYANG:
                    keys.append(f"{day_master}_{element}_{yin_yang}")
        return keys

    @classmethod
    def get_all_western_keys(cls) -> list[str]:
        """모든 서양 점성술 캐시 키 생성 (144개)

        12 (태양) × 12 (달) = 144개 조합

        Returns:
            모든 가능한 캐시 키 리스트
        """
        keys = []
        for sun in cls.WESTERN_ZODIACS:
            for moon in cls.WESTERN_ZODIACS:
                keys.append(f"{sun}_{moon}")
        return keys


# ============================================================
# 캐시 로드/저장
# ============================================================


def load_fortune_cache(force_reload: bool = False) -> dict[str, int]:
    """서버 시작 시 캐시 파일 로드

    JSON 파일에서 캐시 데이터를 메모리로 로드합니다.
    이미 로드되어 있으면 스킵합니다 (force_reload=True로 강제 리로드 가능).

    Args:
        force_reload: True면 기존 캐시 무시하고 다시 로드

    Returns:
        로드된 캐시 항목 수 {eastern: N, western: M}
    """
    global _EASTERN_CACHE, _WESTERN_CACHE, _cache_loaded

    if _cache_loaded and not force_reload:
        logger.debug("cache_already_loaded")
        return {
            "eastern": len(_EASTERN_CACHE),
            "western": len(_WESTERN_CACHE),
        }

    # 동양 사주 캐시 로드
    eastern_count = 0
    if EASTERN_CACHE_PATH.exists():
        try:
            with open(EASTERN_CACHE_PATH, encoding="utf-8") as f:
                _EASTERN_CACHE = json.load(f)
            eastern_count = len(_EASTERN_CACHE)
            logger.info(
                "eastern_cache_loaded",
                count=eastern_count,
                path=str(EASTERN_CACHE_PATH),
            )
        except Exception as e:
            logger.warning(
                "eastern_cache_load_failed",
                error=str(e),
                path=str(EASTERN_CACHE_PATH),
            )
            _EASTERN_CACHE = {}
    else:
        logger.info(
            "eastern_cache_file_not_found",
            path=str(EASTERN_CACHE_PATH),
        )

    # 서양 점성술 캐시 로드
    western_count = 0
    if WESTERN_CACHE_PATH.exists():
        try:
            with open(WESTERN_CACHE_PATH, encoding="utf-8") as f:
                _WESTERN_CACHE = json.load(f)
            western_count = len(_WESTERN_CACHE)
            logger.info(
                "western_cache_loaded",
                count=western_count,
                path=str(WESTERN_CACHE_PATH),
            )
        except Exception as e:
            logger.warning(
                "western_cache_load_failed",
                error=str(e),
                path=str(WESTERN_CACHE_PATH),
            )
            _WESTERN_CACHE = {}
    else:
        logger.info(
            "western_cache_file_not_found",
            path=str(WESTERN_CACHE_PATH),
        )

    _cache_loaded = True
    return {"eastern": eastern_count, "western": western_count}


def save_eastern_cache(cache_data: dict[str, dict[str, Any]]) -> None:
    """동양 사주 캐시 저장

    Args:
        cache_data: 저장할 캐시 데이터
    """
    global _EASTERN_CACHE

    with open(EASTERN_CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache_data, f, ensure_ascii=False, indent=2)

    _EASTERN_CACHE = cache_data
    logger.info(
        "eastern_cache_saved",
        count=len(cache_data),
        path=str(EASTERN_CACHE_PATH),
    )


def save_western_cache(cache_data: dict[str, dict[str, Any]]) -> None:
    """서양 점성술 캐시 저장

    Args:
        cache_data: 저장할 캐시 데이터
    """
    global _WESTERN_CACHE

    with open(WESTERN_CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache_data, f, ensure_ascii=False, indent=2)

    _WESTERN_CACHE = cache_data
    logger.info(
        "western_cache_saved",
        count=len(cache_data),
        path=str(WESTERN_CACHE_PATH),
    )


# ============================================================
# 캐시 조회
# ============================================================


def get_eastern_cached(
    day_gan_code: str,
    dominant_element: str,
    yin_yang: str,
) -> dict[str, Any] | None:
    """동양 사주 캐시 조회

    캐시에서 해당 조합의 사전 생성된 운세를 조회합니다.
    캐시 미스 시 None을 반환하고, 호출자가 LLM을 호출해야 합니다.

    Args:
        day_gan_code: 일간 천간 코드 (예: "GAP", "GYEONG")
        dominant_element: 강한 오행 코드 (예: "WOOD", "METAL")
        yin_yang: 음양 상태 (예: "YANG", "YIN", "BALANCED")

    Returns:
        캐시된 운세 dict 또는 None (캐시 미스)

    Examples:
        >>> result = get_eastern_cached("GAP", "WOOD", "YANG")
        >>> if result:
        ...     return result  # 캐시 히트
        >>> else:
        ...     return await call_llm()  # 캐시 미스
    """
    # 캐시 로드 확인
    if not _cache_loaded:
        load_fortune_cache()

    cache_key = CacheKeyBuilder.build_eastern_key(day_gan_code, dominant_element, yin_yang)

    cached = _EASTERN_CACHE.get(cache_key)

    if cached:
        logger.info(
            "eastern_cache_hit",
            key=cache_key,
        )
        return cached
    else:
        logger.debug(
            "eastern_cache_miss",
            key=cache_key,
        )
        return None


def get_western_cached(
    sun_sign: str,
    moon_sign: str,
) -> dict[str, Any] | None:
    """서양 점성술 캐시 조회

    캐시에서 해당 조합의 사전 생성된 운세를 조회합니다.
    캐시 미스 시 None을 반환하고, 호출자가 LLM을 호출해야 합니다.

    Args:
        sun_sign: 태양 별자리 코드 (예: "ARIES", "LEO")
        moon_sign: 달 별자리 코드 (예: "CANCER", "SCORPIO")

    Returns:
        캐시된 운세 dict 또는 None (캐시 미스)

    Examples:
        >>> result = get_western_cached("ARIES", "CANCER")
        >>> if result:
        ...     return result  # 캐시 히트
        >>> else:
        ...     return await call_llm()  # 캐시 미스
    """
    # 캐시 로드 확인
    if not _cache_loaded:
        load_fortune_cache()

    cache_key = CacheKeyBuilder.build_western_key(sun_sign, moon_sign)

    cached = _WESTERN_CACHE.get(cache_key)

    if cached:
        logger.info(
            "western_cache_hit",
            key=cache_key,
        )
        return cached
    else:
        logger.debug(
            "western_cache_miss",
            key=cache_key,
        )
        return None


# ============================================================
# 캐시 통계
# ============================================================


def get_cache_stats() -> dict[str, Any]:
    """캐시 통계 반환

    Returns:
        캐시 통계 정보
    """
    eastern_total = len(CacheKeyBuilder.get_all_eastern_keys())
    western_total = len(CacheKeyBuilder.get_all_western_keys())

    return {
        "loaded": _cache_loaded,
        "eastern": {
            "cached": len(_EASTERN_CACHE),
            "total": eastern_total,
            "coverage": f"{len(_EASTERN_CACHE) / eastern_total * 100:.1f}%"
            if eastern_total > 0
            else "0%",
        },
        "western": {
            "cached": len(_WESTERN_CACHE),
            "total": western_total,
            "coverage": f"{len(_WESTERN_CACHE) / western_total * 100:.1f}%"
            if western_total > 0
            else "0%",
        },
    }


def clear_cache() -> None:
    """캐시 초기화 (테스트용)"""
    global _EASTERN_CACHE, _WESTERN_CACHE, _cache_loaded

    _EASTERN_CACHE = {}
    _WESTERN_CACHE = {}
    _cache_loaded = False
    logger.info("cache_cleared")
