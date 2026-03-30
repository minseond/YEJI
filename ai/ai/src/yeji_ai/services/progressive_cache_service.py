"""Progressive Caching 서비스

Quick Summary API를 위한 점진적 캐싱 서비스.
Fortune ID 기반으로 요약 데이터를 Redis에 캐싱하여 성능 향상.

## 핵심 기능: 백그라운드 캐시 확장

live=false 요청 시:
1. 캐시에서 랜덤 데이터 즉시 반환 (빠른 응답)
2. 백그라운드에서 새로운 랜덤 조합 생성 (캐시 풀 확장)
   - 같은 카테고리에서 아직 캐싱되지 않은 조합 선택
   - LLM으로 새 해석 생성 후 캐시에 저장
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import random
from datetime import datetime
from typing import Any, Callable, Coroutine, Literal

import structlog


def _json_serializer(obj: Any) -> str:
    """JSON 직렬화를 위한 커스텀 핸들러"""
    if isinstance(obj, datetime):
        return obj.isoformat()


# 폴백 데이터 시그니처 (LLM 실패 시 생성되는 더미 데이터)
_HWATU_FALLBACK_SIGNATURES = {
    "overall_theme": "안정적 흐름",
    "advice": "현재 상황을 유지하며 점진적으로 개선하세요.",
}
_TAROT_FALLBACK_SIGNATURES = {
    "overall_theme": "새로운 시작과 변화의 흐름",
}
_FALLBACK_INTERPRETATION_PATTERN = "카드가 나왔습니다"


def _is_fallback_reading(reading_data: dict[str, Any]) -> bool:
    """캐시 저장 전 폴백(더미) 데이터인지 검사

    Args:
        reading_data: 리딩 데이터

    Returns:
        폴백 데이터이면 True
    """
    summary = reading_data.get("summary", {})
    if isinstance(summary, dict):
        theme = summary.get("overall_theme", "")
        advice = summary.get("advice", "")

        # 화투 폴백 시그니처
        if (
            theme == _HWATU_FALLBACK_SIGNATURES["overall_theme"]
            and advice == _HWATU_FALLBACK_SIGNATURES["advice"]
        ):
            return True

        # 타로 폴백 시그니처
        if theme == _TAROT_FALLBACK_SIGNATURES["overall_theme"]:
            return True

    # interpretation에 더미 패턴이 있는지 확인
    cards = reading_data.get("cards", [])
    if cards:
        fallback_count = sum(
            1 for c in cards
            if isinstance(c, dict)
            and _FALLBACK_INTERPRETATION_PATTERN in c.get("interpretation", "")
        )
        # 전체 카드의 절반 이상이 폴백 패턴이면 폴백으로 판단
        if fallback_count > len(cards) / 2:
            return True

    return False
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

from yeji_ai.clients.redis_client import get_redis_client

logger = structlog.get_logger()

# TTL 설정
QUICK_SUMMARY_TTL = 31536000  # 1년


async def get_quick_summary_cache(
    fortune_id: str,
    category: str,
) -> dict[str, Any] | None:
    """Quick Summary 캐시 조회

    Args:
        fortune_id: 운세 ID (eastern 또는 western)
        category: 운세 카테고리

    Returns:
        캐싱된 요약 데이터 또는 None
    """
    client = await get_redis_client()
    if not client:
        return None

    cache_key = f"quick_summary:{fortune_id}:{category}"
    try:
        cached = await client.get(cache_key)
        if cached:
            logger.info("quick_summary_cache_hit", key=cache_key)
            return json.loads(cached)
        logger.debug("quick_summary_cache_miss", key=cache_key)
        return None
    except Exception as e:
        logger.warning("quick_summary_cache_get_failed", key=cache_key, error=str(e))
        return None


async def store_quick_summary_cache(
    fortune_id: str,
    category: str,
    summary_data: dict[str, Any],
    ttl_seconds: int = QUICK_SUMMARY_TTL,
) -> bool:
    """Quick Summary 캐시 저장

    Args:
        fortune_id: 운세 ID
        category: 운세 카테고리
        summary_data: 요약 데이터
        ttl_seconds: TTL (기본값: 24시간)

    Returns:
        저장 성공 여부
    """
    client = await get_redis_client()
    if not client:
        return False

    cache_key = f"quick_summary:{fortune_id}:{category}"
    try:
        await client.setex(cache_key, ttl_seconds, json.dumps(summary_data, ensure_ascii=False))
        logger.info("quick_summary_cached", key=cache_key, ttl=ttl_seconds)
        return True
    except Exception as e:
        logger.warning("quick_summary_cache_failed", key=cache_key, error=str(e))
        return False


class ProgressiveCacheService:
    """Progressive Caching 서비스 클래스"""

    def __init__(self):
        """초기화"""
        pass

    async def get_or_generate(
        self,
        fortune_id: str,
        category: str,
        generator_func: Any,
    ) -> tuple[dict[str, Any], Literal["cache", "generated"]]:
        """캐시 조회 또는 생성

        Args:
            fortune_id: 운세 ID
            category: 운세 카테고리
            generator_func: 생성 함수 (async callable)

        Returns:
            (데이터, 소스) 튜플. 소스는 "cache" 또는 "generated"
        """
        # 캐시 조회
        cached = await get_quick_summary_cache(fortune_id, category)
        if cached:
            return cached, "cache"

        # 캐시 미스 - 생성
        logger.info("cache_miss_generating", fortune_id=fortune_id, category=category)
        generated = await generator_func()

        # 캐싱 (비동기로 저장, 실패해도 무시)
        await store_quick_summary_cache(fortune_id, category, generated)

        return generated, "generated"


def get_progressive_cache_service() -> ProgressiveCacheService:
    """Progressive Cache 서비스 싱글톤 반환"""
    return ProgressiveCacheService()


# ============================================================
# 화투/타로 캐싱
# ============================================================

HWATU_READING_TTL = 31536000  # 1년
TAROT_READING_TTL = 31536000  # 1년


def _generate_cards_hash(cards: list[dict[str, Any]]) -> str:
    """카드 리스트를 해시 문자열로 변환

    Args:
        cards: 카드 리스트 (position, card_code 등 포함)

    Returns:
        카드 조합을 나타내는 해시 문자열
    """
    # 카드 정보를 정렬된 문자열로 변환
    card_strs = []
    for card in sorted(cards, key=lambda x: x.get("position", 0)):
        pos = card.get("position", 0)
        code = card.get("card_code", card.get("card", {}).get("major", "unknown"))
        reversed_flag = "R" if card.get("is_reversed", False) else "U"
        card_strs.append(f"{pos}_{code}_{reversed_flag}")
    return "-".join(card_strs)


async def get_hwatu_reading_cache(
    question: str | None,
    cards: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """화투 리딩 캐시 조회

    Args:
        question: 질문
        cards: 카드 리스트

    Returns:
        캐싱된 리딩 데이터 또는 None
    """
    client = await get_redis_client()
    if not client:
        return None

    cards_hash = _generate_cards_hash(cards)
    q_hash = (question or "none")[:50]  # 질문 앞 50자만 사용
    cache_key = f"hwatu_reading:{q_hash}:{cards_hash}"

    try:
        cached = await client.get(cache_key)
        if cached:
            logger.info("hwatu_reading_cache_hit", key=cache_key)
            return json.loads(cached)
        logger.debug("hwatu_reading_cache_miss", key=cache_key)
        return None
    except Exception as e:
        logger.warning("hwatu_reading_cache_get_failed", key=cache_key, error=str(e))
        return None


async def store_hwatu_reading_cache(
    question: str | None,
    cards: list[dict[str, Any]],
    reading_data: dict[str, Any],
    ttl_seconds: int = HWATU_READING_TTL,
) -> bool:
    """화투 리딩 캐시 저장

    Args:
        question: 질문
        cards: 카드 리스트
        reading_data: 리딩 데이터
        ttl_seconds: TTL (기본값: 24시간)

    Returns:
        저장 성공 여부
    """
    # 폴백 데이터는 캐시에 저장하지 않음
    if _is_fallback_reading(reading_data):
        logger.warning("hwatu_fallback_cache_skipped", question=question)
        return False

    client = await get_redis_client()
    if not client:
        return False

    cards_hash = _generate_cards_hash(cards)
    q_hash = (question or "none")[:50]
    cache_key = f"hwatu_reading:{q_hash}:{cards_hash}"

    try:
        await client.setex(cache_key, ttl_seconds, json.dumps(reading_data, ensure_ascii=False, default=_json_serializer))
        # 카테고리별 캐시 키 SET에 추가 (O(1) 랜덤 조회용)
        category_set_key = f"hwatu_cache_keys:{q_hash}"
        await client.sadd(category_set_key, cache_key)
        await client.expire(category_set_key, ttl_seconds)  # SET도 동일 TTL 적용
        logger.info("hwatu_reading_cached", key=cache_key, ttl=ttl_seconds)
        return True
    except Exception as e:
        logger.warning("hwatu_reading_cache_failed", key=cache_key, error=str(e))
        return False


async def get_random_cached_hwatu_reading(
    category: str,
) -> dict[str, Any] | None:
    """카테고리별 캐시된 화투 리딩 중 랜덤 반환 (O(1) SET 기반)

    Args:
        category: 운세 카테고리 (LOVE, MONEY, CAREER, HEALTH, STUDY 또는 질문 앞 50자)

    Returns:
        캐싱된 리딩 데이터 또는 None (캐시 없음)
    """
    client = await get_redis_client()
    if not client:
        return None

    # SET에서 랜덤 키 조회 (O(1))
    q_hash = (category or "none")[:50]
    category_set_key = f"hwatu_cache_keys:{q_hash}"

    try:
        # SRANDMEMBER: O(1)로 랜덤 키 조회
        random_key = await client.srandmember(category_set_key)

        if not random_key:
            logger.debug("no_cached_hwatu_for_category", category=category)
            return None

        # 키가 bytes인 경우 디코딩
        if isinstance(random_key, bytes):
            random_key = random_key.decode("utf-8")

        cached = await client.get(random_key)

        if cached:
            logger.info("random_hwatu_cache_hit", category=category, key=random_key)
            return json.loads(cached)

        # 캐시 키는 있지만 데이터가 없으면 (만료됨) SET에서 제거
        await client.srem(category_set_key, random_key)
        return None

    except Exception as e:
        logger.warning("random_hwatu_cache_failed", category=category, error=str(e))
        return None


async def get_tarot_reading_cache(
    question: str | None,
    cards: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """타로 리딩 캐시 조회

    Args:
        question: 질문
        cards: 카드 리스트

    Returns:
        캐싱된 리딩 데이터 또는 None
    """
    client = await get_redis_client()
    if not client:
        return None

    cards_hash = _generate_cards_hash(cards)
    q_hash = (question or "none")[:50]
    cache_key = f"tarot_reading:{q_hash}:{cards_hash}"

    try:
        cached = await client.get(cache_key)
        if cached:
            logger.info("tarot_reading_cache_hit", key=cache_key)
            return json.loads(cached)
        logger.debug("tarot_reading_cache_miss", key=cache_key)
        return None
    except Exception as e:
        logger.warning("tarot_reading_cache_get_failed", key=cache_key, error=str(e))
        return None


async def store_tarot_reading_cache(
    question: str | None,
    cards: list[dict[str, Any]],
    reading_data: dict[str, Any],
    ttl_seconds: int = TAROT_READING_TTL,
) -> bool:
    """타로 리딩 캐시 저장

    Args:
        question: 질문
        cards: 카드 리스트
        reading_data: 리딩 데이터
        ttl_seconds: TTL (기본값: 24시간)

    Returns:
        저장 성공 여부
    """
    # 폴백 데이터는 캐시에 저장하지 않음
    if _is_fallback_reading(reading_data):
        logger.warning("tarot_fallback_cache_skipped", question=question)
        return False

    client = await get_redis_client()
    if not client:
        return False

    cards_hash = _generate_cards_hash(cards)
    q_hash = (question or "none")[:50]
    cache_key = f"tarot_reading:{q_hash}:{cards_hash}"

    try:
        await client.setex(cache_key, ttl_seconds, json.dumps(reading_data, ensure_ascii=False, default=_json_serializer))
        # 카테고리별 캐시 키 SET에 추가 (O(1) 랜덤 조회용)
        category_set_key = f"tarot_cache_keys:{q_hash}"
        await client.sadd(category_set_key, cache_key)
        await client.expire(category_set_key, ttl_seconds)  # SET도 동일 TTL 적용
        logger.info("tarot_reading_cached", key=cache_key, ttl=ttl_seconds)
        return True
    except Exception as e:
        logger.warning("tarot_reading_cache_failed", key=cache_key, error=str(e))
        return False


async def get_random_cached_tarot_reading(
    category: str,
) -> dict[str, Any] | None:
    """카테고리별 캐시된 타로 리딩 중 랜덤 반환 (O(1) SET 기반)

    Args:
        category: 운세 카테고리 (LOVE, MONEY, CAREER, HEALTH, STUDY)

    Returns:
        캐싱된 리딩 데이터 또는 None (캐시 없음)
    """
    client = await get_redis_client()
    if not client:
        return None

    # SET에서 랜덤 키 조회 (O(1))
    category_set_key = f"tarot_cache_keys:{category}"

    try:
        # SRANDMEMBER: O(1)로 랜덤 키 조회
        random_key = await client.srandmember(category_set_key)

        if not random_key:
            logger.debug("no_cached_tarot_for_category", category=category)
            return None

        # 키가 bytes인 경우 디코딩
        if isinstance(random_key, bytes):
            random_key = random_key.decode("utf-8")

        cached = await client.get(random_key)

        if cached:
            logger.info("random_tarot_cache_hit", category=category, key=random_key)
            return json.loads(cached)

        # 캐시 키는 있지만 데이터가 없으면 (만료됨) SET에서 제거
        await client.srem(category_set_key, random_key)
        return None

    except Exception as e:
        logger.warning("random_tarot_cache_failed", category=category, error=str(e))
        return None


# ============================================================
# 백그라운드 캐시 확장 (핵심 기능)
# ============================================================

# 타로: 78장 × 2방향 × 3포지션 중에서 랜덤 조합 생성
# 화투: 48장 × 2방향 × 4포지션 중에서 랜덤 조합 생성

# 타로 카드 풀 (메이저 22장)
TAROT_MAJOR_ARCANA = [
    "FOOL", "MAGICIAN", "HIGH_PRIESTESS", "EMPRESS", "EMPEROR",
    "HIEROPHANT", "LOVERS", "CHARIOT", "STRENGTH", "HERMIT",
    "WHEEL_OF_FORTUNE", "JUSTICE", "HANGED_MAN", "DEATH", "TEMPERANCE",
    "DEVIL", "TOWER", "STAR", "MOON", "SUN", "JUDGEMENT", "WORLD",
]

# 타로 마이너 수트 및 랭크
TAROT_MINOR_SUITS = ["WANDS", "CUPS", "SWORDS", "PENTACLES"]
TAROT_MINOR_RANKS = [
    "ACE", "TWO", "THREE", "FOUR", "FIVE", "SIX", "SEVEN",
    "EIGHT", "NINE", "TEN", "PAGE", "KNIGHT", "QUEEN", "KING",
]

TAROT_ORIENTATIONS = ["UPRIGHT", "REVERSED"]
TAROT_POSITIONS = ["PAST", "PRESENT", "FUTURE"]

# 화투 카드 48장 (0~47)
HWATU_CARD_CODES = list(range(48))
HWATU_POSITIONS = [1, 2, 3, 4]  # 본인/상대/과정/결과


def _generate_random_tarot_cards() -> list[dict[str, Any]]:
    """랜덤 타로 카드 3장 생성 (중복 없음)

    Returns:
        3장 카드 리스트 (PAST, PRESENT, FUTURE)
    """
    # 전체 카드 풀 생성
    all_cards = []

    # 메이저 아르카나
    for major in TAROT_MAJOR_ARCANA:
        all_cards.append({"type": "major", "major": major})

    # 마이너 아르카나
    for suit in TAROT_MINOR_SUITS:
        for rank in TAROT_MINOR_RANKS:
            all_cards.append({"type": "minor", "suit": suit, "rank": rank})

    # 중복 없이 3장 선택
    selected_cards = random.sample(all_cards, 3)

    # 포지션과 방향 할당
    cards = []
    for i, card in enumerate(selected_cards):
        position = TAROT_POSITIONS[i]
        orientation = random.choice(TAROT_ORIENTATIONS)

        if card["type"] == "major":
            cards.append({
                "position": position,
                "card": {
                    "major": card["major"],
                    "orientation": orientation,
                },
            })
        else:
            cards.append({
                "position": position,
                "card": {
                    "suit": card["suit"],
                    "rank": card["rank"],
                    "orientation": orientation,
                },
            })

    return cards


def _generate_random_hwatu_cards() -> list[dict[str, Any]]:
    """랜덤 화투 카드 4장 생성 (중복 없음)

    Returns:
        4장 카드 리스트 (position 1~4)
    """
    # 중복 없이 4장 선택
    selected_codes = random.sample(HWATU_CARD_CODES, 4)

    cards = []
    for i, code in enumerate(selected_codes):
        cards.append({
            "position": HWATU_POSITIONS[i],
            "card_code": code,
            "is_reversed": False,  # 화투는 역방향 없음
        })

    return cards


async def _is_tarot_combination_cached(category: str, cards: list[dict[str, Any]]) -> bool:
    """타로 카드 조합이 이미 캐싱되어 있는지 확인

    Args:
        category: 운세 카테고리 (LOVE, MONEY 등)
        cards: 카드 조합

    Returns:
        캐싱 여부
    """
    client = await get_redis_client()
    if not client:
        return False

    cards_hash = _generate_cards_hash(cards)
    cache_key = f"tarot_reading:{category}:{cards_hash}"

    try:
        exists = await client.exists(cache_key)
        return bool(exists)
    except Exception as e:
        logger.warning("check_tarot_cache_exists_failed", error=str(e))
        return False


async def _is_hwatu_combination_cached(category: str, cards: list[dict[str, Any]]) -> bool:
    """화투 카드 조합이 이미 캐싱되어 있는지 확인

    Args:
        category: 운세 카테고리
        cards: 카드 조합

    Returns:
        캐싱 여부
    """
    client = await get_redis_client()
    if not client:
        return False

    cards_hash = _generate_cards_hash(cards)
    q_hash = (category or "none")[:50]
    cache_key = f"hwatu_reading:{q_hash}:{cards_hash}"

    try:
        exists = await client.exists(cache_key)
        return bool(exists)
    except Exception as e:
        logger.warning("check_hwatu_cache_exists_failed", error=str(e))
        return False


async def generate_and_cache_random_tarot(
    category: str,
    generator_func: Callable[..., Coroutine[Any, Any, dict[str, Any]]],
    max_attempts: int = 10,
) -> bool:
    """백그라운드에서 캐싱되지 않은 새로운 타로 조합 생성 및 캐싱

    Args:
        category: 운세 카테고리 (LOVE, MONEY, CAREER, HEALTH, STUDY)
        generator_func: LLM 리딩 생성 함수 (cards를 인자로 받음)
        max_attempts: 새로운 조합을 찾기 위한 최대 시도 횟수

    Returns:
        성공 여부
    """
    logger.info("background_tarot_generation_start", category=category)

    try:
        # 캐싱되지 않은 새로운 조합 찾기
        for attempt in range(max_attempts):
            cards = _generate_random_tarot_cards()

            if not await _is_tarot_combination_cached(category, cards):
                logger.info(
                    "background_tarot_new_combination_found",
                    category=category,
                    attempt=attempt + 1,
                )
                break
        else:
            # 모든 시도에서 새로운 조합을 못 찾음 (캐시가 이미 충분히 채워짐)
            logger.info(
                "background_tarot_all_combinations_cached",
                category=category,
                max_attempts=max_attempts,
            )
            return False

        # LLM으로 리딩 생성
        reading_data = await generator_func(cards)

        # 캐시 저장
        # cards_for_cache 형태로 변환
        cards_for_cache = [{"position": c["position"], "card": c["card"]} for c in cards]
        success = await store_tarot_reading_cache(category, cards_for_cache, reading_data)

        if success:
            logger.info(
                "background_tarot_cache_stored",
                category=category,
            )
        return success

    except Exception as e:
        logger.error(
            "background_tarot_generation_failed",
            category=category,
            error=str(e),
            exc_info=True,
        )
        return False


async def generate_and_cache_random_hwatu(
    category: str,
    generator_func: Callable[..., Coroutine[Any, Any, dict[str, Any]]],
    max_attempts: int = 10,
) -> bool:
    """백그라운드에서 캐싱되지 않은 새로운 화투 조합 생성 및 캐싱

    Args:
        category: 운세 카테고리 (LOVE, MONEY, CAREER, HEALTH, STUDY)
        generator_func: LLM 리딩 생성 함수 (cards를 인자로 받음)
        max_attempts: 새로운 조합을 찾기 위한 최대 시도 횟수

    Returns:
        성공 여부
    """
    logger.info("background_hwatu_generation_start", category=category)

    try:
        # 캐싱되지 않은 새로운 조합 찾기
        for attempt in range(max_attempts):
            cards = _generate_random_hwatu_cards()

            if not await _is_hwatu_combination_cached(category, cards):
                logger.info(
                    "background_hwatu_new_combination_found",
                    category=category,
                    attempt=attempt + 1,
                )
                break
        else:
            # 모든 시도에서 새로운 조합을 못 찾음
            logger.info(
                "background_hwatu_all_combinations_cached",
                category=category,
                max_attempts=max_attempts,
            )
            return False

        # LLM으로 리딩 생성
        reading_data = await generator_func(cards)

        # 캐시 저장
        success = await store_hwatu_reading_cache(category, cards, reading_data)

        if success:
            logger.info(
                "background_hwatu_cache_stored",
                category=category,
            )
        return success

    except Exception as e:
        logger.error(
            "background_hwatu_generation_failed",
            category=category,
            error=str(e),
            exc_info=True,
        )
        return False


async def background_expand_tarot_cache(
    category: str,
    generator_func: Callable[..., Coroutine[Any, Any, dict[str, Any]]],
) -> None:
    """백그라운드 태스크: 타로 캐시 확장 (fire-and-forget)

    이 함수는 FastAPI BackgroundTasks에서 호출됩니다.
    응답 반환 후 비동기로 실행되어 캐시 풀을 확장합니다.

    Args:
        category: 운세 카테고리
        generator_func: LLM 리딩 생성 함수
    """
    try:
        await generate_and_cache_random_tarot(category, generator_func)
    except Exception as e:
        # 백그라운드 태스크 실패는 로그만 남기고 무시
        logger.error(
            "background_expand_tarot_cache_failed",
            category=category,
            error=str(e),
        )


async def background_expand_hwatu_cache(
    category: str,
    generator_func: Callable[..., Coroutine[Any, Any, dict[str, Any]]],
) -> None:
    """백그라운드 태스크: 화투 캐시 확장 (fire-and-forget)

    Args:
        category: 운세 카테고리
        generator_func: LLM 리딩 생성 함수
    """
    try:
        await generate_and_cache_random_hwatu(category, generator_func)
    except Exception as e:
        logger.error(
            "background_expand_hwatu_cache_failed",
            category=category,
            error=str(e),
        )
