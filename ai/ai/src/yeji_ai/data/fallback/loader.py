"""폴백 템플릿 데이터 로더

JSON 파일에서 폴백 템플릿 데이터를 로드하고 캐싱합니다.
LRU 캐시를 사용하여 반복 로드를 방지합니다.
"""

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger()

# 데이터 파일 경로
_DATA_DIR = Path(__file__).parent
EASTERN_TEMPLATES_PATH = _DATA_DIR / "eastern_templates.json"
WESTERN_TEMPLATES_PATH = _DATA_DIR / "western_templates.json"
KEYWORDS_PATH = _DATA_DIR / "keywords.json"


# ============================================================
# 템플릿 로드 함수 (LRU 캐싱)
# ============================================================


@lru_cache(maxsize=1)
def load_eastern_templates() -> dict[str, Any]:
    """동양 사주 템플릿 로드 (캐싱)

    Returns:
        동양 사주 템플릿 데이터 dict

    Raises:
        FileNotFoundError: 템플릿 파일이 없는 경우
        json.JSONDecodeError: JSON 파싱 실패한 경우
    """
    logger.debug("eastern_templates_loading", path=str(EASTERN_TEMPLATES_PATH))

    try:
        with open(EASTERN_TEMPLATES_PATH, encoding="utf-8") as f:
            data = json.load(f)

        logger.info(
            "eastern_templates_loaded",
            personality_count=len(data.get("personality", {})),
            message_count=len(data.get("message", {})),
        )
        return data

    except FileNotFoundError:
        logger.error("eastern_templates_file_not_found", path=str(EASTERN_TEMPLATES_PATH))
        raise
    except json.JSONDecodeError as e:
        logger.error("eastern_templates_json_error", error=str(e))
        raise


@lru_cache(maxsize=1)
def load_western_templates() -> dict[str, Any]:
    """서양 점성술 템플릿 로드 (캐싱)

    Returns:
        서양 점성술 템플릿 데이터 dict

    Raises:
        FileNotFoundError: 템플릿 파일이 없는 경우
        json.JSONDecodeError: JSON 파싱 실패한 경우
    """
    logger.debug("western_templates_loading", path=str(WESTERN_TEMPLATES_PATH))

    try:
        with open(WESTERN_TEMPLATES_PATH, encoding="utf-8") as f:
            data = json.load(f)

        logger.info(
            "western_templates_loaded",
            personality_count=len(data.get("personality", {})),
            message_count=len(data.get("message", {})),
        )
        return data

    except FileNotFoundError:
        logger.error("western_templates_file_not_found", path=str(WESTERN_TEMPLATES_PATH))
        raise
    except json.JSONDecodeError as e:
        logger.error("western_templates_json_error", error=str(e))
        raise


@lru_cache(maxsize=1)
def load_keywords() -> dict[str, Any]:
    """키워드 데이터 로드 (캐싱)

    Returns:
        키워드 데이터 dict

    Raises:
        FileNotFoundError: 키워드 파일이 없는 경우
        json.JSONDecodeError: JSON 파싱 실패한 경우
    """
    logger.debug("keywords_loading", path=str(KEYWORDS_PATH))

    try:
        with open(KEYWORDS_PATH, encoding="utf-8") as f:
            data = json.load(f)

        logger.info("keywords_loaded")
        return data

    except FileNotFoundError:
        logger.error("keywords_file_not_found", path=str(KEYWORDS_PATH))
        raise
    except json.JSONDecodeError as e:
        logger.error("keywords_json_error", error=str(e))
        raise


def load_all_templates() -> dict[str, dict[str, Any]]:
    """모든 템플릿 데이터 로드

    서버 시작 시 모든 템플릿을 한번에 로드하여 캐싱합니다.

    Returns:
        {eastern: ..., western: ..., keywords: ...} 형태의 dict
    """
    logger.info("all_templates_loading_start")

    result = {
        "eastern": load_eastern_templates(),
        "western": load_western_templates(),
        "keywords": load_keywords(),
    }

    logger.info("all_templates_loaded")
    return result


# ============================================================
# 폴백 데이터 조회 함수
# ============================================================


def get_eastern_fallback_data(
    day_master: str,
    strong_element: str,
    yin_yang: str,
) -> dict[str, Any]:
    """동양 사주 폴백 데이터 조회

    일간, 강한 오행, 음양 조합에 해당하는 폴백 데이터를 조회합니다.
    템플릿에서 해당 키가 없으면 기본값을 반환합니다.

    Args:
        day_master: 일간 코드 (예: "GAP", "GYEONG")
        strong_element: 강한 오행 코드 (예: "WOOD", "METAL")
        yin_yang: 음양 상태 (예: "YANG", "YIN", "BALANCED")

    Returns:
        폴백 데이터 dict:
        - personality: 성격 분석
        - strength: 강점
        - weakness: 약점
        - advice: 조언
        - message: 상세 메시지
        - lucky: 행운 정보

    Examples:
        >>> data = get_eastern_fallback_data("GAP", "WOOD", "YANG")
        >>> print(data["personality"])
        "갑목(甲木) 일간으로 목(木) 기운이 강하여..."
    """
    templates = load_eastern_templates()

    # 키 정규화
    dm = day_master.upper() if day_master else "GAP"
    elem = strong_element.upper() if strong_element else "WOOD"
    yy = _normalize_yin_yang(yin_yang)

    # 조합 키 생성
    personality_key = f"{dm}_{elem}"
    message_key = f"{dm}_{elem}_{yy}"

    # 데이터 조회 (없으면 기본값)
    personality = templates.get("personality", {}).get(
        personality_key,
        templates.get("personality", {}).get("GAP_WOOD", "밝고 긍정적인 성격을 지니고 있소."),
    )

    strength = templates.get("strength", {}).get(
        elem,
        "타고난 재능과 잠재력이 있소.",
    )

    weakness = templates.get("weakness", {}).get(
        elem,
        "꾸준한 노력으로 부족한 부분을 채워가시오.",
    )

    advice = templates.get("advice", {}).get(
        elem,
        "자신의 장점을 살리고 균형 잡힌 생활을 하시오.",
    )

    message = templates.get("message", {}).get(
        message_key,
        templates.get("message", {}).get(
            "GAP_WOOD_YANG",
            "좋은 기운이 함께하고 있소. 자신감을 가지고 나아가시오.",
        ),
    )

    lucky = templates.get("lucky", {}).get(
        elem,
        {
            "color": "흰색",
            "color_code": "#FFFFFF",
            "number": "7",
            "item": "수정",
            "direction": "동쪽",
            "direction_code": "E",
            "place": "자연 속",
        },
    )

    logger.debug(
        "eastern_fallback_data_retrieved",
        day_master=dm,
        strong_element=elem,
        yin_yang=yy,
    )

    return {
        "personality": personality,
        "strength": strength,
        "weakness": weakness,
        "advice": advice,
        "message": message,
        "lucky": lucky,
    }


def get_western_fallback_data(
    sun_sign: str,
    moon_sign: str,
    dominant_element: str,
) -> dict[str, Any]:
    """서양 점성술 폴백 데이터 조회

    태양 별자리, 달 별자리, 우세 원소 조합에 해당하는 폴백 데이터를 조회합니다.
    템플릿에서 해당 키가 없으면 기본값을 반환합니다.

    Args:
        sun_sign: 태양 별자리 코드 (예: "ARIES", "LEO")
        moon_sign: 달 별자리 코드 (예: "CANCER", "SCORPIO")
        dominant_element: 우세 원소 코드 (예: "FIRE", "WATER")

    Returns:
        폴백 데이터 dict:
        - personality: 성격 분석
        - strength: 강점
        - weakness: 약점
        - message: 상세 메시지
        - lucky: 행운 정보

    Examples:
        >>> data = get_western_fallback_data("ARIES", "CANCER", "FIRE")
        >>> print(data["personality"])
        "양자리 불 원소 타입으로..."
    """
    templates = load_western_templates()

    # 키 정규화
    sun = sun_sign.upper() if sun_sign else "ARIES"
    moon = moon_sign.upper() if moon_sign else "ARIES"
    elem = dominant_element.upper() if dominant_element else "FIRE"

    # 조합 키 생성
    personality_key = f"{sun}_{elem}"
    message_key = f"{sun}_{moon}_{elem}"

    # 데이터 조회 (없으면 기본값)
    personality = templates.get("personality", {}).get(
        personality_key,
        templates.get("personality", {}).get(
            "ARIES_FIRE",
            "밝고 긍정적인 에너지를 가지고 있어요.",
        ),
    )

    strength = templates.get("strength", {}).get(
        elem,
        "타고난 잠재력과 매력이 있어요.",
    )

    weakness = templates.get("weakness", {}).get(
        elem,
        "균형 잡힌 성장이 필요해요.",
    )

    message = templates.get("message", {}).get(
        message_key,
        templates.get("message", {}).get(
            "ARIES_ARIES_FIRE",
            "좋은 에너지가 함께해요. 자신감을 가지세요!",
        ),
    )

    lucky = templates.get("lucky", {}).get(
        sun,
        {
            "day": "일요일",
            "day_code": "SUN",
            "color": "금색",
            "color_code": "#FFD700",
            "number": "1",
            "stone": "호박",
            "planet": "SUN",
        },
    )

    logger.debug(
        "western_fallback_data_retrieved",
        sun_sign=sun,
        moon_sign=moon,
        dominant_element=elem,
    )

    return {
        "personality": personality,
        "strength": strength,
        "weakness": weakness,
        "message": message,
        "lucky": lucky,
    }


# ============================================================
# 유틸리티 함수
# ============================================================


def _normalize_yin_yang(yin_yang: str | None) -> str:
    """음양 상태 정규화

    다양한 형식의 음양 값을 표준 형식(YANG, YIN, BALANCED)으로 정규화합니다.

    Args:
        yin_yang: 음양 값 (예: "STRONG_YANG", "SLIGHT_YIN", "BALANCED")

    Returns:
        정규화된 음양 값 ("YANG", "YIN", "BALANCED" 중 하나)
    """
    if not yin_yang:
        return "BALANCED"

    yy = yin_yang.upper()

    if "YANG" in yy and yy != "YANG":
        return "YANG"
    elif "YIN" in yy and yy != "YIN":
        return "YIN"
    elif yy in ("YANG", "YIN", "BALANCED"):
        return yy
    else:
        return "BALANCED"


def get_fallback_stats() -> dict[str, Any]:
    """폴백 템플릿 통계 반환

    Returns:
        템플릿 통계 정보
    """
    eastern = load_eastern_templates()
    western = load_western_templates()
    keywords = load_keywords()

    return {
        "eastern": {
            "personality_count": len(eastern.get("personality", {})),
            "strength_count": len(eastern.get("strength", {})),
            "weakness_count": len(eastern.get("weakness", {})),
            "advice_count": len(eastern.get("advice", {})),
            "message_count": len(eastern.get("message", {})),
            "lucky_count": len(eastern.get("lucky", {})),
        },
        "western": {
            "personality_count": len(western.get("personality", {})),
            "strength_count": len(western.get("strength", {})),
            "weakness_count": len(western.get("weakness", {})),
            "message_count": len(western.get("message", {})),
            "lucky_count": len(western.get("lucky", {})),
        },
        "keywords": {
            "eastern_day_master_count": len(
                keywords.get("eastern", {}).get("day_master", {})
            ),
            "eastern_element_count": len(
                keywords.get("eastern", {}).get("element", {})
            ),
            "western_zodiac_count": len(
                keywords.get("western", {}).get("zodiac", {})
            ),
            "western_element_count": len(
                keywords.get("western", {}).get("element", {})
            ),
        },
    }


def clear_cache() -> None:
    """캐시 초기화 (테스트용)

    LRU 캐시를 모두 비웁니다.
    """
    load_eastern_templates.cache_clear()
    load_western_templates.cache_clear()
    load_keywords.cache_clear()
    logger.info("fallback_cache_cleared")
