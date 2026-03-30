"""헬스체크 API"""

from fastapi import APIRouter
from pydantic import BaseModel

from yeji_ai import __version__
from yeji_ai.config import get_settings
from yeji_ai.data.fortune_cache import get_cache_stats

router = APIRouter()


class HealthResponse(BaseModel):
    """헬스체크 응답"""

    status: str
    version: str
    service: str
    git_commit: str = "dev"


class ModelStatusResponse(BaseModel):
    """모델 상태 응답"""

    status: str
    model: str
    vllm_url: str
    ready: bool


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """서버 헬스체크"""
    from yeji_ai import __git_commit__

    return HealthResponse(
        status="healthy",
        version=__version__,
        service="yeji-ai",
        git_commit=__git_commit__,
    )


class ReadyResponse(BaseModel):
    """준비 상태 응답"""

    status: str
    vllm_connected: bool


class LiveResponse(BaseModel):
    """생존 상태 응답"""

    status: str


@router.get("/health/ready", response_model=ReadyResponse)
async def readiness_check():
    """준비 상태 체크 (K8s readiness probe)"""
    from yeji_ai.clients.vllm_client import get_vllm_client

    client = get_vllm_client()
    vllm_ok = await client.health_check()

    return ReadyResponse(
        status="ready" if vllm_ok else "degraded",
        vllm_connected=vllm_ok,
    )


@router.get("/health/live", response_model=LiveResponse)
async def liveness_check():
    """생존 상태 체크 (K8s liveness probe)"""
    return LiveResponse(status="alive")


@router.get("/model/status", response_model=ModelStatusResponse)
async def model_status():
    """모델 상태 확인"""
    settings = get_settings()

    # TODO: 실제 vLLM 서버 연결 확인
    return ModelStatusResponse(
        status="ok",
        model=settings.vllm_model,
        vllm_url=settings.vllm_base_url,
        ready=True,  # TODO: 실제 확인 로직
    )


# GPU 필터 헬스체크 (태스크 #98)


class FilterHealthResponse(BaseModel):
    """GPU 필터 헬스체크 응답"""

    enabled: bool
    guard_loaded: bool
    guard_model: str | None
    intent_loaded: bool
    intent_model: str | None
    gpu_memory: dict[str, float] | None


@router.get("/health/filter", response_model=FilterHealthResponse)
async def filter_health() -> FilterHealthResponse:
    """GPU 필터 헬스체크

    GPU 기반 인텐트 필터(Guard, Intent) 상태를 확인합니다.
    """
    settings = get_settings()

    if not settings.gpu_filter_enabled:
        return FilterHealthResponse(
            enabled=False,
            guard_loaded=False,
            guard_model=None,
            intent_loaded=False,
            intent_model=None,
            gpu_memory=None,
        )

    # torch 의존성이 있는 모듈은 GPU 필터 활성화 시에만 import
    try:
        from yeji_ai.services.filter.loader import get_gpu_memory_info
        from yeji_ai.services.filter.pipeline import get_filter_pipeline

        pipeline = get_filter_pipeline()
        gpu_memory = get_gpu_memory_info()

        guard_loaded = pipeline.guard_enabled if pipeline else False
        intent_loaded = pipeline.intent_enabled if pipeline else False

        return FilterHealthResponse(
            enabled=True,
            guard_loaded=guard_loaded,
            guard_model=settings.guard_model if guard_loaded else None,
            intent_loaded=intent_loaded,
            intent_model=settings.intent_embedding_model if intent_loaded else None,
            gpu_memory=gpu_memory,
        )
    except ImportError:
        # torch 미설치 환경
        return FilterHealthResponse(
            enabled=True,
            guard_loaded=False,
            guard_model=None,
            intent_loaded=False,
            intent_model=None,
            gpu_memory=None,
        )


# ============================================================
# 캐시 헬스체크 (#23 - 사전 캐싱 시스템)
# ============================================================


class CacheStatsItem(BaseModel):
    """캐시 통계 항목"""

    cached: int
    total: int
    coverage: str


class CacheHealthResponse(BaseModel):
    """캐시 헬스체크 응답"""

    loaded: bool
    eastern: CacheStatsItem
    western: CacheStatsItem


@router.get("/health/cache", response_model=CacheHealthResponse, tags=["health"])
async def cache_health() -> CacheHealthResponse:
    """운세 캐시 상태 확인

    사전 계산된 운세 캐시의 로드 상태와 커버리지를 확인합니다.

    Returns:
        CacheHealthResponse: 캐시 상태 정보
            - loaded: 캐시 로드 여부
            - eastern: 동양 사주 캐시 통계 (개수/전체/커버리지)
            - western: 서양 점성술 캐시 통계 (개수/전체/커버리지)
    """
    stats = get_cache_stats()

    return CacheHealthResponse(
        loaded=stats["loaded"],
        eastern=CacheStatsItem(
            cached=stats["eastern"]["cached"],
            total=stats["eastern"]["total"],
            coverage=stats["eastern"]["coverage"],
        ),
        western=CacheStatsItem(
            cached=stats["western"]["cached"],
            total=stats["western"]["total"],
            coverage=stats["western"]["coverage"],
        ),
    )
