"""API 라우터 통합"""

from fastapi import APIRouter

from yeji_ai.api.health import router as health_router
from yeji_ai.api.metrics import router as metrics_router
from yeji_ai.api.saju import router as saju_router
from yeji_ai.api.v1.router import v1_router

api_router = APIRouter()

# 헬스체크
api_router.include_router(health_router, tags=["health"])

# 메트릭 모니터링 엔드포인트
api_router.include_router(metrics_router, tags=["metrics"])

# 사주 API (레거시 - 내부 테스트용으로만 유지, Swagger에서 숨김)
api_router.include_router(
    saju_router, prefix="/saju", tags=["saju-legacy"], include_in_schema=False
)

# API v1 (신규 Fortune API)
api_router.include_router(v1_router, prefix="/v1")
