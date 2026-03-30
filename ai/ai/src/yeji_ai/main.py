"""YEJI AI Server 메인 진입점"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

import structlog
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from yeji_ai import __version__
from yeji_ai.api.router import api_router
from yeji_ai.config import get_settings
from yeji_ai.data.fortune_cache import get_cache_stats, load_fortune_cache
from yeji_ai.services.response_logger import (
    initialize_response_logger,
    shutdown_response_logger,
)
from yeji_ai.services.validation_monitor import (
    initialize_validation_monitor,
    shutdown_validation_monitor,
)

# 로거 설정
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.dev.ConsoleRenderer()
        if get_settings().debug
        else structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """앱 라이프사이클 관리

    초기화 순서:
    1. LLM 응답 로거
    2. 검증 실패 모니터
    3. GPU 필터 파이프라인 (태스크 #98)

    종료 순서:
    1. GPU 필터 파이프라인
    2. 검증 실패 모니터
    3. LLM 응답 로거
    """
    settings = get_settings()

    # LLM 응답 로거 초기화 (비동기 JSONL 로깅)
    log_dir = Path("logs/llm_responses")
    await initialize_response_logger(base_dir=log_dir)
    logger.info(
        "response_logger_initialized",
        log_dir=str(log_dir),
    )

    # 검증 실패 모니터 초기화 (1분마다 상태 로깅)
    await initialize_validation_monitor()
    logger.info("validation_monitor_initialized")

    # 운세 캐시 로드 (#23 - 사전 캐싱 시스템)
    # 동양 사주: 일간 × 오행 × 음양 조합 (약 150개)
    # 서양 점성술: 태양 × 달 별자리 조합 (144개)
    cache_result = load_fortune_cache()
    cache_stats = get_cache_stats()
    logger.info(
        "fortune_cache_loaded",
        eastern_count=cache_result["eastern"],
        western_count=cache_result["western"],
        eastern_coverage=cache_stats["eastern"]["coverage"],
        western_coverage=cache_stats["western"]["coverage"],
    )

    # GPU 필터 파이프라인 초기화 (태스크 #98)
    # Feature Flag: GPU_FILTER_ENABLED
    if settings.gpu_filter_enabled:
        try:
            from yeji_ai.services.filter import initialize_filter_pipeline

            pipeline = await initialize_filter_pipeline(settings)
            logger.info(
                "gpu_filter_pipeline_initialized",
                guard_enabled=pipeline.guard_enabled,
                intent_enabled=pipeline.intent_enabled,
                guard_model=settings.guard_model if pipeline.guard_enabled else None,
                intent_model=settings.intent_embedding_model if pipeline.intent_enabled else None,
            )
        except ImportError:
            logger.warning(
                "gpu_filter_module_not_available",
                message="filter 모듈이 아직 구현되지 않았습니다",
            )
        except Exception as e:
            logger.error(
                "gpu_filter_pipeline_init_failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            # 필수가 아니면 서버는 계속 시작
            if settings.guard_required or settings.intent_embedding_required:
                raise RuntimeError(f"GPU 필터 초기화 실패: {e}") from e
    else:
        logger.info("gpu_filter_disabled")

    logger.info(
        "yeji_ai_server_started",
        host=settings.host,
        port=settings.port,
        vllm_url=settings.vllm_base_url,
        model=settings.vllm_model,
        gpu_filter_enabled=settings.gpu_filter_enabled,
    )
    yield

    # GPU 필터 파이프라인 종료
    if settings.gpu_filter_enabled:
        try:
            from yeji_ai.services.filter import shutdown_filter_pipeline

            await shutdown_filter_pipeline()
            logger.info("gpu_filter_pipeline_shutdown")
        except ImportError:
            pass  # 모듈이 없으면 종료할 것도 없음
        except Exception as e:
            logger.warning("gpu_filter_shutdown_error", error=str(e))

    # 검증 실패 모니터 종료
    await shutdown_validation_monitor()
    logger.info("validation_monitor_shutdown")

    # LLM 응답 로거 종료 (잔여 로그 플러시)
    await shutdown_response_logger()
    logger.info("response_logger_shutdown")

    logger.info("yeji_ai_server_stopped")


def create_app() -> FastAPI:
    """FastAPI 앱 생성"""
    settings = get_settings()

    # OpenAPI 태그 메타데이터 (Swagger UI 그룹화)
    openapi_tags = [
        # === 핵심 API (상단 배치) ===
        {
            "name": "fortune-turn",
            "description": "🎯 **[핵심] 턴 단위 티키타카** - 프로덕션 메인 API\n\n"
            "**사용 순서:** /chat/turn/start → /chat/turn/continue → /chat/summary\n\n"
            "1. `/chat/turn/start`: 세션 시작 + 그리팅 (Turn 0)\n"
            "2. `/chat/turn/continue`: 대화 진행 (Turn 1+)\n"
            "3. `/chat/summary/{session_id}`: 운세 요약 조회",
        },
        {
            "name": "fortune-util",
            "description": "🔧 유틸리티 - 캐릭터 정보, 서브캐릭터 테스트",
        },
        {
            "name": "fortune-analysis",
            "description": "🔮 **[핵심] 운세 분석** - 동양(사주) / 서양(점성술) 분석",
        },
        {
            "name": "fortune-summary",
            "description": "📊 **[핵심] 운세 요약** - 분석 결과 요약 조회",
        },
        # === 보조 API ===
        {
            "name": "fortune-session",
            "description": "📋 세션 관리 - 채팅 세션 생성/조회/삭제",
        },
        {
            "name": "fortune-enum",
            "description": "📚 Enum 조회 - 프론트엔드 TypeScript 타입 정의용",
        },
        # === 개발/테스트 ===
        {
            "name": "fortune-demo",
            "description": "🧪 데모/테스트 - Swagger에서 바로 실행 가능",
        },
        {
            "name": "fortune-debug",
            "description": "🔧 디버그 - 개발 환경 전용 (시드 생성, 초기화)",
        },
        # === 인프라 ===
        {
            "name": "health",
            "description": "💚 헬스체크 - 서버 상태 확인",
        },
        {
            "name": "metrics",
            "description": "📈 메트릭 - Prometheus 호환 모니터링",
        },
        # === 레거시 ===
        {
            "name": "fortune-chat-legacy",
            "description": "⚠️ [레거시] 기존 채팅 API - /chat/turn 사용 권장",
        },
        {
            "name": "saju-legacy",
            "description": "⚠️ [레거시] 사주 API - /fortune/eastern 사용 권장",
        },
    ]

    app = FastAPI(
        title="YEJI AI Server - 운세 분석 API",
        description='''
## 🔮 YEJI AI 운세 분석 API

동양 사주 + 서양 점성술 결합 AI 운세 서비스

---

### 🚀 Quick Start (3-Step 플로우 - 권장)

**Step 1. 세션 시작 + 그리팅 (Turn 0)**
```json
POST /v1/fortune/chat/turn/start
{
  "birth_date": "1995-03-15",
  "birth_time": "09:30",
  "category": "LOVE",
  "char1_code": "SOISEOL",
  "char2_code": "STELLA"
}
```
→ 응답: `session_id`, 그리팅 메시지, `turn: 1`

**Step 2. 대화 계속 (Turn 1+)**
```json
POST /v1/fortune/chat/turn/continue
{
  "session_id": "0072ded5",
  "message": "썸녀랑 잘 될까요?",
  "extend_turn": false
}
```
→ 응답: 티키타카 대화 + 다음 질문 제안

**Step 3. 요약 조회 (선택)**
```json
GET /v1/fortune/chat/summary/{session_id}?type=eastern
```
→ 응답: 동양/서양 운세 요약

> 💡 **Tip**: `extend_turn: true`로 3턴 이후에도 대화 계속 가능 (최대 10턴)

---

### 🔮 운세 분석 API (선택 - 사전 분석)

- `POST /v1/fortune/eastern` - 동양 사주 분석
- `POST /v1/fortune/western` - 서양 점성술 분석

> 💡 **Note**: turn/start 호출 시 자동으로 분석이 수행되므로 별도 호출 불필요

### 📊 카테고리 (대문자)

`GENERAL` | `LOVE` | `MONEY` | `CAREER` | `HEALTH` | `STUDY`

---

### 📖 문서 링크

| 문서 | 설명 |
|------|------|
| [Swagger UI](/docs) | 인터랙티브 API 테스트 |
| [ReDoc](/redoc) | 상세 API 레퍼런스 |
| [API 구조 문서](/static/api-docs.html) | 전체 구조 가이드 |

---

### 🎭 캐릭터

| 코드 | 이름 | 계열 | 말투 |
|------|------|------|------|
| SOISEOL | 소이설 | 동양 | 하오체 |
| STELLA | 스텔라 | 서양 | 해요체 |
| CHEONGWOON | 청운 | 동양 | 시적 하오체 |
| HWARIN | 화린 | 동양 | 나른한 해요체 |
| KYLE | 카일 | 서양 | 반말+존댓말 |
| ELARIA | 엘라리아 | 서양 | 우아한 해요체 |
''',
        version=__version__,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_tags=openapi_tags,
        root_path=settings.root_path,  # Nginx 프록시 경로 (/ai) 지원
        lifespan=lifespan,
    )

    # CORS 설정 (MEDIUM-3: 메소드 명시)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    # static 디렉토리 마운트
    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
        logger.info("static_files_mounted", path=str(static_dir))

    # 라우터 등록
    app.include_router(api_router)

    # 티키타카 테스트 페이지 라우트
    @app.get("/tikitaka-test", include_in_schema=False)
    async def tikitaka_test_page():
        """티키타카 채팅 테스트 HTML 페이지"""
        html_file = static_dir / "tikitaka_test.html"
        if html_file.exists():
            return FileResponse(html_file)
        return {"error": "테스트 페이지를 찾을 수 없습니다"}

    @app.get("/api-portal", include_in_schema=False)
    async def api_portal_page():
        """API 문서 포털 페이지 - 환경별 API 문서 접근"""
        html_file = static_dir / "api-portal.html"
        if html_file.exists():
            return FileResponse(html_file)
        return {"error": "포털 페이지를 찾을 수 없습니다"}

    @app.get("/simple-test", include_in_schema=False)
    async def simple_test_page():
        """Simple Q&A 테스트 페이지"""
        html_file = static_dir / "simple-test.html"
        if html_file.exists():
            return FileResponse(html_file)
        return {"error": "테스트 페이지를 찾을 수 없습니다"}

    @app.get("/quick-summary-test", include_in_schema=False)
    async def quick_summary_test_page():
        """Quick Summary 테스트 페이지"""
        html_file = static_dir / "quick-summary-test.html"
        if html_file.exists():
            return FileResponse(html_file)
        return {"error": "테스트 페이지를 찾을 수 없습니다"}

    return app


app = create_app()


def main():
    """CLI 진입점"""
    settings = get_settings()
    uvicorn.run(
        "yeji_ai.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
