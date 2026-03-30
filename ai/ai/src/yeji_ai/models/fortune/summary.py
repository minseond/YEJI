"""Fortune Summary API 모델"""

from typing import Literal

from pydantic import BaseModel, Field


class FortuneSummaryRequest(BaseModel):
    """요약 조회 요청"""

    fortune_key: str = Field(..., description="Fortune API에서 받은 키")


class FortuneSummaryResponse(BaseModel):
    """요약 조회 응답"""

    fortune_key: str = Field(..., description="요청한 키")
    summary: str = Field(..., description="요약 텍스트 (~100토큰)")
    source: Literal["cached", "generated"] = Field(..., description="요약 출처")
    cached_at: str | None = Field(None, description="캐시 시간 (ISO8601)")
