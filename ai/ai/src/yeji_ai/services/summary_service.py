"""Fortune Summary 서비스

사주/점성술 분석 결과를 요약하여 캐시/반환하는 서비스
"""

from datetime import UTC, datetime
from typing import Any, Literal

import structlog

from yeji_ai.services.fortune_key_service import (
    get_fortune,
    get_summary,
    parse_fortune_key,
    store_summary,
)
from yeji_ai.services.tikitaka_service import (
    create_summarized_eastern_context,
    create_summarized_western_context,
)

logger = structlog.get_logger()


class SummaryService:
    """Fortune Summary 서비스 클래스"""

    async def get_or_create_eastern_summary(
        self,
        fortune_key: str,
    ) -> tuple[str, Literal["cached", "generated"]] | None:
        """동양 사주 요약 조회 또는 생성

        Args:
            fortune_key: eastern:{birth_date}:{birth_time}:{gender} 형식

        Returns:
            (summary, source) 튜플 또는 None (fortune 데이터 없음)
        """
        # 1. 요약 캐시 확인
        cached_summary = await get_summary(fortune_key)
        if cached_summary:
            logger.info("eastern_summary_cache_hit", fortune_key=fortune_key)
            return cached_summary, "cached"

        # 2. Fortune 데이터 조회
        fortune_data = await get_fortune(fortune_key)
        if not fortune_data:
            logger.warning("eastern_fortune_not_found", fortune_key=fortune_key)
            return None

        # 3. 요약 생성 (data 필드 안의 실제 데이터 추출)
        actual_data = fortune_data.get("data", fortune_data)
        summary = create_summarized_eastern_context(actual_data)

        # 4. 요약 캐시 저장
        await store_summary(fortune_key, summary)
        logger.info("eastern_summary_generated", fortune_key=fortune_key)

        return summary, "generated"

    async def get_or_create_western_summary(
        self,
        fortune_key: str,
    ) -> tuple[str, Literal["cached", "generated"]] | None:
        """서양 점성술 요약 조회 또는 생성

        Args:
            fortune_key: western:{birth_date}:{birth_time} 형식

        Returns:
            (summary, source) 튜플 또는 None (fortune 데이터 없음)
        """
        # 1. 요약 캐시 확인
        cached_summary = await get_summary(fortune_key)
        if cached_summary:
            logger.info("western_summary_cache_hit", fortune_key=fortune_key)
            return cached_summary, "cached"

        # 2. Fortune 데이터 조회
        fortune_data = await get_fortune(fortune_key)
        if not fortune_data:
            logger.warning("western_fortune_not_found", fortune_key=fortune_key)
            return None

        # 3. 요약 생성 (data 필드 안의 실제 데이터 추출)
        actual_data = fortune_data.get("data", fortune_data)
        summary = create_summarized_western_context(actual_data)

        # 4. 요약 캐시 저장
        await store_summary(fortune_key, summary)
        logger.info("western_summary_generated", fortune_key=fortune_key)

        return summary, "generated"

    async def get_summary_with_metadata(
        self,
        fortune_key: str,
    ) -> dict[str, Any] | None:
        """요약 조회 (메타데이터 포함)

        Returns:
            {
                "fortune_key": str,
                "summary": str,
                "source": "cached" | "generated",
                "cached_at": str (ISO8601) | None
            }
        """
        parsed = parse_fortune_key(fortune_key)
        if not parsed:
            logger.warning("invalid_fortune_key", fortune_key=fortune_key)
            return None

        fortune_type = parsed["type"]

        if fortune_type == "eastern":
            result = await self.get_or_create_eastern_summary(fortune_key)
        elif fortune_type == "western":
            result = await self.get_or_create_western_summary(fortune_key)
        else:
            logger.warning("unknown_fortune_type", fortune_key=fortune_key)
            return None

        if not result:
            return None

        summary, source = result

        return {
            "fortune_key": fortune_key,
            "summary": summary,
            "source": source,
            "cached_at": (
                datetime.now(UTC).isoformat()
                if source == "generated"
                else None
            ),
        }


# 싱글톤 인스턴스
_summary_service: SummaryService | None = None


def get_summary_service() -> SummaryService:
    """SummaryService 싱글톤 반환"""
    global _summary_service
    if _summary_service is None:
        _summary_service = SummaryService()
    return _summary_service
