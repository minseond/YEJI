"""API v1 라우터 통합

## 엔드포인트 태그 구조

| 태그 | 설명 |
|------|------|
| fortune-analysis | 운세 분석 (eastern, western, tarot, hwatu) |
| fortune-turn | 티키타카 대화 |
| fortune-simple | 단순 Q&A |
| fortune-summary | 빠른 요약 |
| fortune-demo | 데모 API (Swagger 숨김) |
"""

from fastapi import APIRouter

from yeji_ai.api.v1.fortune.chat import router as chat_router
from yeji_ai.api.v1.fortune.compatibility import router as compatibility_router
from yeji_ai.api.v1.fortune.demo import router as demo_router
from yeji_ai.api.v1.fortune.eastern import router as eastern_router
from yeji_ai.api.v1.fortune.hwatu import router as hwatu_router
from yeji_ai.api.v1.fortune.quick_summary import router as quick_summary_router
from yeji_ai.api.v1.fortune.simple import router as simple_router
from yeji_ai.api.v1.fortune.tarot import router as tarot_router
from yeji_ai.api.v1.fortune.western import router as western_router

v1_router = APIRouter()

# Demo API 등록 (Swagger에서 숨김)
v1_router.include_router(
    demo_router,
    prefix="/fortune",
    tags=["fortune-demo"],
    include_in_schema=False,  # 데모 - Swagger에서 숨김
)

# Fortune API 등록
v1_router.include_router(
    eastern_router,
    prefix="/fortune",
    tags=["fortune-analysis"],
)
v1_router.include_router(
    western_router,
    prefix="/fortune",
    tags=["fortune-analysis"],
)
v1_router.include_router(
    tarot_router,
    prefix="/fortune",
    tags=["fortune-analysis"],
)
v1_router.include_router(
    hwatu_router,
    prefix="/fortune",
    tags=["fortune-analysis"],
)
v1_router.include_router(
    chat_router,
    prefix="/fortune",
    tags=["fortune-turn"],  # 메인 채팅 API는 fortune-turn 태그
)
v1_router.include_router(
    simple_router,
    prefix="/fortune",
    tags=["fortune-simple"],
)
v1_router.include_router(
    quick_summary_router,
    prefix="/fortune",
    tags=["fortune-summary"],
)
v1_router.include_router(
    compatibility_router,
    prefix="/fortune",
    tags=["fortune-compatibility"],
)
