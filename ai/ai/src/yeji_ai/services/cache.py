"""Redis 캐싱 레이어

사주/점성술 결과 캐싱으로 LLM 호출 최소화
"""

import hashlib
import json

import structlog
from redis import asyncio as aioredis

logger = structlog.get_logger()

# Redis 클라이언트 (싱글톤)
_redis_client: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis | None:
    """Redis 클라이언트 반환 (연결 실패 시 None)"""
    global _redis_client
    if _redis_client is None:
        try:
            from yeji_ai.config import get_settings

            settings = get_settings()
            redis_url = getattr(settings, "redis_url", "redis://localhost:6379")
            _redis_client = await aioredis.from_url(redis_url, decode_responses=True)
            await _redis_client.ping()
            logger.info("redis_connected", url=redis_url)
        except Exception as e:
            logger.warning("redis_connection_failed", error=str(e))
            return None
    return _redis_client


def generate_cache_key(prefix: str, **kwargs) -> str:
    """캐시 키 생성"""
    data = json.dumps(kwargs, sort_keys=True)
    hash_val = hashlib.md5(data.encode()).hexdigest()[:12]
    return f"{prefix}:{hash_val}"


async def get_cached(key: str) -> dict | None:
    """캐시에서 값 조회"""
    redis = await get_redis()
    if redis is None:
        return None
    try:
        data = await redis.get(key)
        if data:
            logger.debug("cache_hit", key=key)
            return json.loads(data)
        logger.debug("cache_miss", key=key)
        return None
    except Exception as e:
        logger.warning("cache_get_error", key=key, error=str(e))
        return None


async def set_cached(key: str, value: dict, ttl: int = 86400) -> bool:
    """캐시에 값 저장 (기본 TTL: 24시간, 실패 결과 캐싱 방지)"""
    # 실패한 결과는 캐싱하지 않음
    if not value.get("success", True):
        logger.warning("cache_set_skipped_failure", key=key, errors=value.get("errors", []))
        return False
    redis = await get_redis()
    if redis is None:
        return False
    try:
        await redis.setex(key, ttl, json.dumps(value, ensure_ascii=False))
        logger.debug("cache_set", key=key, ttl=ttl)
        return True
    except Exception as e:
        logger.warning("cache_set_error", key=key, error=str(e))
        return False


# 운세별 캐시 헬퍼
async def get_eastern_fortune_cached(birth_date: str, birth_time: str | None) -> dict | None:
    """동양 운세 캐시 조회"""
    key = generate_cache_key("eastern", birth_date=birth_date, birth_time=birth_time)
    return await get_cached(key)


async def set_eastern_fortune_cached(
    birth_date: str, birth_time: str | None, data: dict
) -> bool:
    """동양 운세 캐시 저장 (7일 TTL - 운세는 거의 안 변함)"""
    key = generate_cache_key("eastern", birth_date=birth_date, birth_time=birth_time)
    return await set_cached(key, data, ttl=604800)  # 7일


async def get_western_fortune_cached(
    birth_date: str, birth_location: str | None
) -> dict | None:
    """서양 운세 캐시 조회"""
    key = generate_cache_key("western", birth_date=birth_date, birth_location=birth_location)
    return await get_cached(key)


async def set_western_fortune_cached(
    birth_date: str, birth_location: str | None, data: dict
) -> bool:
    """서양 운세 캐시 저장 (7일 TTL)"""
    key = generate_cache_key("western", birth_date=birth_date, birth_location=birth_location)
    return await set_cached(key, data, ttl=604800)
