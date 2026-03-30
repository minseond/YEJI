"""타로/화투 랜덤 캐시 테스트

live 파라미터 기능:
- live=false: 카테고리별 캐시된 조합 중 랜덤 반환
- live=true: 요청한 카드 조합으로 실시간 생성
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestRandomCacheLogic:
    """랜덤 캐시 로직 단위 테스트 (Redis 모킹)"""

    @pytest.mark.asyncio
    async def test_store_tarot_adds_to_set(self):
        """타로 캐시 저장 시 SET에도 추가되는지 확인"""
        mock_client = AsyncMock()
        mock_client.setex = AsyncMock(return_value=True)
        mock_client.sadd = AsyncMock(return_value=1)
        mock_client.expire = AsyncMock(return_value=True)

        with patch(
            "yeji_ai.services.progressive_cache_service.get_redis_client",
            return_value=mock_client,
        ):
            from yeji_ai.services.progressive_cache_service import store_tarot_reading_cache

            result = await store_tarot_reading_cache(
                question="LOVE",
                cards=[
                    {"position": "PAST", "card": {"major": "FOOL", "orientation": "UPRIGHT"}},
                    {"position": "PRESENT", "card": {"major": "MAGICIAN", "orientation": "UPRIGHT"}},
                    {"position": "FUTURE", "card": {"major": "LOVERS", "orientation": "REVERSED"}},
                ],
                reading_data={"cards": [], "summary": "테스트"},
            )

            # 저장 성공
            assert result is True

            # setex 호출 확인 (캐시 저장)
            mock_client.setex.assert_called_once()
            call_args = mock_client.setex.call_args
            assert "tarot_reading:LOVE:" in call_args[0][0]

            # sadd 호출 확인 (SET에 추가)
            mock_client.sadd.assert_called_once()
            sadd_args = mock_client.sadd.call_args
            assert sadd_args[0][0] == "tarot_cache_keys:LOVE"

            # expire 호출 확인 (SET TTL)
            mock_client.expire.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_random_tarot_from_set(self):
        """SET에서 랜덤 키 조회 후 캐시 데이터 반환"""
        mock_client = AsyncMock()
        mock_client.srandmember = AsyncMock(return_value=b"tarot_reading:LOVE:abc123")
        mock_client.get = AsyncMock(
            return_value=json.dumps({"cards": [{"card_code": "FOOL"}], "summary": "랜덤 캐시"})
        )

        with patch(
            "yeji_ai.services.progressive_cache_service.get_redis_client",
            return_value=mock_client,
        ):
            from yeji_ai.services.progressive_cache_service import get_random_cached_tarot_reading

            result = await get_random_cached_tarot_reading("LOVE")

            # srandmember 호출 확인
            mock_client.srandmember.assert_called_once_with("tarot_cache_keys:LOVE")

            # get 호출 확인
            mock_client.get.assert_called_once_with("tarot_reading:LOVE:abc123")

            # 결과 확인
            assert result is not None
            assert result["summary"] == "랜덤 캐시"

    @pytest.mark.asyncio
    async def test_get_random_tarot_empty_set(self):
        """SET이 비어있을 때 None 반환"""
        mock_client = AsyncMock()
        mock_client.srandmember = AsyncMock(return_value=None)

        with patch(
            "yeji_ai.services.progressive_cache_service.get_redis_client",
            return_value=mock_client,
        ):
            from yeji_ai.services.progressive_cache_service import get_random_cached_tarot_reading

            result = await get_random_cached_tarot_reading("CAREER")

            assert result is None

    @pytest.mark.asyncio
    async def test_get_random_tarot_expired_key_cleanup(self):
        """만료된 캐시 키는 SET에서 제거"""
        mock_client = AsyncMock()
        mock_client.srandmember = AsyncMock(return_value=b"tarot_reading:LOVE:expired123")
        mock_client.get = AsyncMock(return_value=None)  # 만료됨
        mock_client.srem = AsyncMock(return_value=1)

        with patch(
            "yeji_ai.services.progressive_cache_service.get_redis_client",
            return_value=mock_client,
        ):
            from yeji_ai.services.progressive_cache_service import get_random_cached_tarot_reading

            result = await get_random_cached_tarot_reading("LOVE")

            # srem 호출 확인 (만료된 키 제거)
            mock_client.srem.assert_called_once_with(
                "tarot_cache_keys:LOVE", "tarot_reading:LOVE:expired123"
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_store_hwatu_adds_to_set(self):
        """화투 캐시 저장 시 SET에도 추가되는지 확인"""
        mock_client = AsyncMock()
        mock_client.setex = AsyncMock(return_value=True)
        mock_client.sadd = AsyncMock(return_value=1)
        mock_client.expire = AsyncMock(return_value=True)

        with patch(
            "yeji_ai.services.progressive_cache_service.get_redis_client",
            return_value=mock_client,
        ):
            from yeji_ai.services.progressive_cache_service import store_hwatu_reading_cache

            result = await store_hwatu_reading_cache(
                question="MONEY",
                cards=[
                    {"position": 1, "card_code": 0, "is_reversed": False},
                    {"position": 2, "card_code": 12, "is_reversed": False},
                    {"position": 3, "card_code": 24, "is_reversed": False},
                    {"position": 4, "card_code": 36, "is_reversed": False},
                ],
                reading_data={"cards": [], "summary": "화투 테스트"},
            )

            assert result is True
            mock_client.sadd.assert_called_once()
            assert "hwatu_cache_keys:MONEY" in mock_client.sadd.call_args[0][0]

    @pytest.mark.asyncio
    async def test_get_random_hwatu_from_set(self):
        """화투 SET에서 랜덤 키 조회"""
        mock_client = AsyncMock()
        mock_client.srandmember = AsyncMock(return_value=b"hwatu_reading:CAREER:xyz789")
        mock_client.get = AsyncMock(
            return_value=json.dumps({"cards": [{"card_code": 0}], "summary": "화투 랜덤"})
        )

        with patch(
            "yeji_ai.services.progressive_cache_service.get_redis_client",
            return_value=mock_client,
        ):
            from yeji_ai.services.progressive_cache_service import get_random_cached_hwatu_reading

            result = await get_random_cached_hwatu_reading("CAREER")

            mock_client.srandmember.assert_called_once_with("hwatu_cache_keys:CAREER")
            assert result is not None
            assert result["summary"] == "화투 랜덤"


class TestRandomCacheIntegration:
    """랜덤 캐시 통합 테스트 (실제 Redis 필요)"""

    @pytest.mark.asyncio
    async def test_tarot_store_and_random_get(self):
        """타로 저장 후 랜덤 조회 (Redis 연결 시)"""
        from yeji_ai.services.progressive_cache_service import (
            get_random_cached_tarot_reading,
            store_tarot_reading_cache,
        )

        # 테스트 데이터 저장
        stored = await store_tarot_reading_cache(
            question="STUDY",
            cards=[
                {"position": "PAST", "card": {"major": "STAR", "orientation": "UPRIGHT"}},
                {"position": "PRESENT", "card": {"major": "MOON", "orientation": "REVERSED"}},
                {"position": "FUTURE", "card": {"major": "SUN", "orientation": "UPRIGHT"}},
            ],
            reading_data={
                "cards": [{"card_code": "STAR"}, {"card_code": "MOON"}, {"card_code": "SUN"}],
                "summary": "학업운 테스트",
            },
            ttl_seconds=60,  # 테스트용 짧은 TTL
        )

        if not stored:
            pytest.skip("Redis 연결 불가 - 통합 테스트 스킵")

        # 랜덤 조회
        result = await get_random_cached_tarot_reading("STUDY")
        assert result is not None
        assert "summary" in result

    @pytest.mark.asyncio
    async def test_hwatu_store_and_random_get(self):
        """화투 저장 후 랜덤 조회 (Redis 연결 시)"""
        from yeji_ai.services.progressive_cache_service import (
            get_random_cached_hwatu_reading,
            store_hwatu_reading_cache,
        )

        stored = await store_hwatu_reading_cache(
            question="HEALTH",
            cards=[
                {"position": 1, "card_code": 1, "is_reversed": False},
                {"position": 2, "card_code": 13, "is_reversed": False},
                {"position": 3, "card_code": 25, "is_reversed": False},
                {"position": 4, "card_code": 37, "is_reversed": False},
            ],
            reading_data={
                "cards": [{"card_code": 1}, {"card_code": 13}, {"card_code": 25}, {"card_code": 37}],
                "summary": "건강운 테스트",
            },
            ttl_seconds=60,
        )

        if not stored:
            pytest.skip("Redis 연결 불가 - 통합 테스트 스킵")

        result = await get_random_cached_hwatu_reading("HEALTH")
        assert result is not None
        assert "summary" in result
