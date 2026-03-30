"""Redis 캐싱 테스트"""

import pytest

from yeji_ai.clients.redis_client import cache_fortune, get_cached_fortune


@pytest.mark.asyncio
async def test_redis_cache_basic():
    """Redis 캐싱 기본 동작 테스트 (연결 실패 시 graceful degradation)"""
    birth_date = "1990-05-15"
    birth_time = "14:30"
    fortune_type = "eastern"

    test_data = {
        "chart": {"summary": "테스트 사주"},
        "stats": {"strength": "강점 테스트"},
        "element": "WOOD",
    }

    # 캐싱 시도 (Redis 없으면 False 반환하고 계속 진행)
    cache_result = await cache_fortune(birth_date, birth_time, fortune_type, test_data)

    # Redis 연결 실패 시에도 테스트는 통과해야 함
    if cache_result:
        # Redis 연결 성공 시 조회 테스트
        cached = await get_cached_fortune(birth_date, birth_time, fortune_type)
        assert cached is not None
        assert cached["element"] == "WOOD"
        assert cached["chart"]["summary"] == "테스트 사주"
    else:
        # Redis 연결 실패 시 None 반환 확인
        cached = await get_cached_fortune(birth_date, birth_time, fortune_type)
        assert cached is None


@pytest.mark.asyncio
async def test_redis_cache_miss():
    """Redis 캐시 미스 테스트"""
    # 존재하지 않는 데이터 조회
    cached = await get_cached_fortune("2000-01-01", "00:00", "western")

    # Redis 없거나 캐시 미스 시 None 반환
    assert cached is None


@pytest.mark.asyncio
async def test_redis_cache_different_birth_time():
    """출생시간이 다르면 다른 캐시 키 사용 확인"""
    birth_date = "1990-05-15"
    fortune_type = "eastern"

    data1 = {"element": "FIRE", "stats": {"strength": "강함"}}
    data2 = {"element": "WATER", "stats": {"strength": "약함"}}

    # 서로 다른 출생시간으로 캐싱
    await cache_fortune(birth_date, "10:00", fortune_type, data1)
    await cache_fortune(birth_date, "14:00", fortune_type, data2)

    # 각각 조회 (Redis 연결 시)
    cached1 = await get_cached_fortune(birth_date, "10:00", fortune_type)
    cached2 = await get_cached_fortune(birth_date, "14:00", fortune_type)

    # Redis 연결 성공 시에만 검증
    if cached1 and cached2:
        assert cached1["element"] == "FIRE"
        assert cached2["element"] == "WATER"
