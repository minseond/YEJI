"""Fortune Key 생성 및 관리 서비스"""

import json
from typing import Any

import structlog

from yeji_ai.clients.redis_client import get_redis_client

logger = structlog.get_logger()

FORTUNE_TTL = 31536000  # 1년 (365일)
SUMMARY_TTL = 31536000  # 1년 (365일)


def generate_eastern_fortune_key(
    birth_date: str,
    birth_time: str | None,
    gender: str | None,
) -> str:
    """동양 사주 fortune_key 생성

    형식: eastern:{birth_date}:{birth_time|unknown}:{gender|U}
    예시: eastern:1990-05-15:1430:M
    주의: 시간은 HH:MM → HHMM으로 변환하여 구분자 충돌 방지
    """
    time_part = birth_time.replace(":", "") if birth_time else "unknown"
    gender_part = gender if gender else "U"
    return f"eastern:{birth_date}:{time_part}:{gender_part}"


def generate_western_fortune_key(
    birth_date: str,
    birth_time: str | None,
) -> str:
    """서양 점성술 fortune_key 생성

    형식: western:{birth_date}:{birth_time|unknown}
    예시: western:1990-05-15:1430
    주의: 시간은 HH:MM → HHMM으로 변환하여 구분자 충돌 방지
    """
    time_part = birth_time.replace(":", "") if birth_time else "unknown"
    return f"western:{birth_date}:{time_part}"


def parse_fortune_key(fortune_key: str) -> dict[str, str] | None:
    """fortune_key 파싱

    Returns:
        {"type": "eastern"|"western", "birth_date": "...", "birth_time": "...", "gender": "..."}
        또는 None (파싱 실패)
    """
    parts = fortune_key.split(":")

    if len(parts) < 3:
        return None

    fortune_type = parts[0]

    if fortune_type == "eastern" and len(parts) == 4:
        return {
            "type": "eastern",
            "birth_date": parts[1],
            "birth_time": parts[2] if parts[2] != "unknown" else None,
            "gender": parts[3],
        }
    elif fortune_type == "western" and len(parts) == 3:
        return {
            "type": "western",
            "birth_date": parts[1],
            "birth_time": parts[2] if parts[2] != "unknown" else None,
        }

    return None


async def store_fortune(
    fortune_key: str,
    fortune_data: dict[str, Any],
    ttl_seconds: int = FORTUNE_TTL,
) -> bool:
    """Fortune 데이터 Redis에 저장 (실패 결과는 캐싱하지 않음)"""
    # 실패한 결과는 캐싱하지 않음 (cache poisoning 방지)
    if not fortune_data.get("success", True):
        logger.warning(
            "fortune_store_skipped_failure",
            key=fortune_key,
            errors=fortune_data.get("errors", []),
        )
        return False

    client = await get_redis_client()
    if not client:
        return False

    redis_key = f"fortune:{fortune_key}"
    try:
        await client.setex(redis_key, ttl_seconds, json.dumps(fortune_data, ensure_ascii=False))
        logger.info("fortune_stored", key=redis_key, ttl=ttl_seconds)
        return True
    except Exception as e:
        logger.warning("fortune_store_failed", key=redis_key, error=str(e))
        return False


async def get_fortune(fortune_key: str) -> dict[str, Any] | None:
    """Fortune 데이터 Redis에서 조회"""
    client = await get_redis_client()
    if not client:
        return None

    redis_key = f"fortune:{fortune_key}"
    try:
        cached = await client.get(redis_key)
        if cached:
            logger.info("fortune_cache_hit", key=redis_key)
            return json.loads(cached)
        logger.debug("fortune_cache_miss", key=redis_key)
        return None
    except Exception as e:
        logger.warning("fortune_get_failed", key=redis_key, error=str(e))
        return None


async def store_summary(
    fortune_key: str,
    summary: str,
    ttl_seconds: int = SUMMARY_TTL,
) -> bool:
    """Summary 데이터 Redis에 저장"""
    client = await get_redis_client()
    if not client:
        return False

    redis_key = f"summary:{fortune_key}"
    try:
        await client.setex(redis_key, ttl_seconds, summary)
        logger.info("summary_stored", key=redis_key, ttl=ttl_seconds)
        return True
    except Exception as e:
        logger.warning("summary_store_failed", key=redis_key, error=str(e))
        return False


async def get_summary(fortune_key: str) -> str | None:
    """Summary 데이터 Redis에서 조회"""
    client = await get_redis_client()
    if not client:
        return None

    redis_key = f"summary:{fortune_key}"
    try:
        cached = await client.get(redis_key)
        if cached:
            logger.info("summary_cache_hit", key=redis_key)
            return cached
        logger.debug("summary_cache_miss", key=redis_key)
        return None
    except Exception as e:
        logger.warning("summary_get_failed", key=redis_key, error=str(e))
        return None
