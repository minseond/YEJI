"""Redis 클라이언트 - 운세 결과 캐싱"""

import json
from typing import Any

import redis.asyncio as redis
import structlog

from yeji_ai.config import get_settings

logger = structlog.get_logger()

_redis_client: redis.Redis | None = None


async def get_redis_client() -> redis.Redis | None:
    """Redis 클라이언트 싱글톤 반환 (연결 실패 시 None)"""
    global _redis_client

    if _redis_client is not None:
        return _redis_client

    settings = get_settings()
    if not settings.redis_url:
        logger.warning("redis_url_not_configured")
        return None

    try:
        _redis_client = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
        # 연결 테스트
        await _redis_client.ping()
        logger.info("redis_connected", url=settings.redis_url[:20] + "...")
        return _redis_client
    except Exception as e:
        logger.warning("redis_connection_failed", error=str(e))
        return None


async def cache_fortune(
    birth_date: str,
    birth_time: str | None,
    fortune_type: str,  # "eastern" | "western"
    result: dict[str, Any],
    ttl_seconds: int = 86400,  # 24시간
) -> bool:
    """운세 결과 캐싱 (실패 결과는 캐싱하지 않음)

    Args:
        birth_date: 생년월일 (YYYY-MM-DD)
        birth_time: 출생시간 (HH:MM 또는 None)
        fortune_type: 운세 타입 ("eastern" | "western")
        result: 캐싱할 운세 결과 (dict)
        ttl_seconds: TTL (기본값: 24시간)

    Returns:
        캐싱 성공 여부
    """
    # 실패한 결과는 캐싱하지 않음 (cache poisoning 방지)
    if not result.get("success", True):
        logger.warning(
            "fortune_cache_skipped_failure",
            fortune_type=fortune_type,
            birth_date=birth_date,
            errors=result.get("errors", []),
        )
        return False

    client = await get_redis_client()
    if not client:
        return False

    key = f"yeji:{fortune_type}:{birth_date}:{birth_time or 'unknown'}"
    try:
        await client.setex(key, ttl_seconds, json.dumps(result, ensure_ascii=False))
        logger.info("fortune_cached", key=key, ttl=ttl_seconds)
        return True
    except Exception as e:
        logger.warning("fortune_cache_failed", key=key, error=str(e))
        return False


async def record_token_usage(
    session_id: str,
    category: str,
    turn: int,
    prompt_tokens: int,
    completion_tokens: int,
) -> bool:
    """토큰 사용량 기록

    Args:
        session_id: 세션 ID
        category: 운세 카테고리 (GENERAL, LOVE, MONEY 등)
        turn: 턴 번호
        prompt_tokens: 입력 토큰 수
        completion_tokens: 출력 토큰 수

    Returns:
        저장 성공 여부
    """
    client = await get_redis_client()
    if not client:
        return False

    try:
        # 세션별 토큰 기록 (리스트로 저장)
        session_key = f"yeji:tokens:session:{session_id}"
        record = json.dumps({
            "turn": turn,
            "category": category,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        }, ensure_ascii=False)
        await client.rpush(session_key, record)
        await client.expire(session_key, 86400)  # 24시간 TTL

        # 카테고리별 누적 통계 (HINCRBY)
        stats_key = f"yeji:tokens:stats:{category}"
        await client.hincrby(stats_key, "total_prompt", prompt_tokens)
        await client.hincrby(stats_key, "total_completion", completion_tokens)
        await client.hincrby(stats_key, "call_count", 1)

        logger.info(
            "token_usage_recorded",
            session_id=session_id,
            category=category,
            turn=turn,
            prompt=prompt_tokens,
            completion=completion_tokens,
        )
        return True
    except Exception as e:
        logger.warning("token_usage_record_failed", error=str(e))
        return False


async def get_token_stats_by_category(category: str | None = None) -> dict[str, Any]:
    """카테고리별 토큰 통계 조회

    Args:
        category: 특정 카테고리 (None이면 전체)

    Returns:
        카테고리별 평균 토큰 통계
    """
    client = await get_redis_client()
    if not client:
        return {"error": "Redis not available"}

    try:
        result = {}
        categories = [category] if category else [
            "GENERAL", "LOVE", "MONEY", "CAREER", "HEALTH", "STUDY"
        ]

        for cat in categories:
            stats_key = f"yeji:tokens:stats:{cat}"
            data = await client.hgetall(stats_key)

            if data:
                total_prompt = int(data.get("total_prompt", 0))
                total_completion = int(data.get("total_completion", 0))
                call_count = int(data.get("call_count", 1))

                result[cat] = {
                    "avg_prompt_tokens": round(total_prompt / call_count, 1),
                    "avg_completion_tokens": round(total_completion / call_count, 1),
                    "avg_total_tokens": round((total_prompt + total_completion) / call_count, 1),
                    "total_calls": call_count,
                }
            else:
                result[cat] = {
                    "avg_prompt_tokens": 0,
                    "avg_completion_tokens": 0,
                    "avg_total_tokens": 0,
                    "total_calls": 0,
                }

        return result
    except Exception as e:
        logger.warning("token_stats_get_failed", error=str(e))
        return {"error": str(e)}


async def get_session_token_history(session_id: str) -> list[dict[str, Any]]:
    """세션별 토큰 사용 이력 조회

    Args:
        session_id: 세션 ID

    Returns:
        턴별 토큰 사용 이력 리스트
    """
    client = await get_redis_client()
    if not client:
        return []

    try:
        session_key = f"yeji:tokens:session:{session_id}"
        records = await client.lrange(session_key, 0, -1)
        return [json.loads(r) for r in records]
    except Exception as e:
        logger.warning("session_token_history_failed", error=str(e))
        return []


async def save_session_to_redis(
    session_id: str,
    session_data: dict[str, Any],
    ttl_seconds: int = 604800,  # 1주일 (7일 * 24시간 * 3600초)
) -> bool:
    """세션 데이터를 Redis에 저장

    Args:
        session_id: 세션 ID
        session_data: 세션 데이터 (직렬화된 dict)
        ttl_seconds: TTL (기본값: 1주일)

    Returns:
        저장 성공 여부
    """
    client = await get_redis_client()
    if not client:
        return False

    key = f"yeji:session:{session_id}"
    try:
        await client.setex(key, ttl_seconds, json.dumps(session_data, ensure_ascii=False))
        logger.info("session_saved_redis", session_id=session_id, ttl=ttl_seconds)
        return True
    except Exception as e:
        logger.warning("session_save_failed", session_id=session_id, error=str(e))
        return False


async def get_session_from_redis(session_id: str) -> dict[str, Any] | None:
    """Redis에서 세션 데이터 조회

    Args:
        session_id: 세션 ID

    Returns:
        세션 데이터 (dict) 또는 None
    """
    client = await get_redis_client()
    if not client:
        return None

    key = f"yeji:session:{session_id}"
    try:
        cached = await client.get(key)
        if cached:
            logger.info("session_cache_hit", session_id=session_id)
            return json.loads(cached)
        logger.debug("session_cache_miss", session_id=session_id)
        return None
    except Exception as e:
        logger.warning("session_get_failed", session_id=session_id, error=str(e))
        return None


async def delete_session_from_redis(session_id: str) -> bool:
    """Redis에서 세션 삭제

    Args:
        session_id: 세션 ID

    Returns:
        삭제 성공 여부
    """
    client = await get_redis_client()
    if not client:
        return False

    key = f"yeji:session:{session_id}"
    try:
        await client.delete(key)
        logger.info("session_deleted_redis", session_id=session_id)
        return True
    except Exception as e:
        logger.warning("session_delete_failed", session_id=session_id, error=str(e))
        return False


async def get_cached_fortune(
    birth_date: str,
    birth_time: str | None,
    fortune_type: str,
) -> dict[str, Any] | None:
    """캐싱된 운세 결과 조회

    Args:
        birth_date: 생년월일 (YYYY-MM-DD)
        birth_time: 출생시간 (HH:MM 또는 None)
        fortune_type: 운세 타입 ("eastern" | "western")

    Returns:
        캐싱된 운세 결과 (dict) 또는 None
    """
    client = await get_redis_client()
    if not client:
        return None

    key = f"yeji:{fortune_type}:{birth_date}:{birth_time or 'unknown'}"
    try:
        cached = await client.get(key)
        if cached:
            logger.info("fortune_cache_hit", key=key)
            return json.loads(cached)
        logger.debug("fortune_cache_miss", key=key)
        return None
    except Exception as e:
        logger.warning("fortune_cache_get_failed", key=key, error=str(e))
        return None
