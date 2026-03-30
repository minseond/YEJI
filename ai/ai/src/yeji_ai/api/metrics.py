"""메트릭 API 엔드포인트

검증 실패 모니터링 메트릭을 제공하는 API입니다.
Prometheus 형식(text/plain)과 JSON 형식 모두 지원합니다.
"""

from fastapi import APIRouter, Query
from fastapi.responses import PlainTextResponse

from yeji_ai.models.metrics import ValidationMetrics
from yeji_ai.services.validation_monitor import get_validation_monitor

router = APIRouter()


@router.get(
    "/metrics",
    response_model=ValidationMetrics,
    summary="검증 메트릭 조회",
    description="LLM 응답 검증 실패율 및 관련 메트릭을 JSON 형식으로 반환합니다.",
    responses={
        200: {
            "description": "검증 메트릭",
            "content": {
                "application/json": {
                    "example": {
                        "total_requests": 1000,
                        "success_count": 950,
                        "failure_count": 50,
                        "failure_rate": 5.0,
                        "success_rate": 95.0,
                        "error_type_counts": [
                            {"error_type": "validation", "count": 30, "percentage": 60.0},
                            {"error_type": "json_parse", "count": 15, "percentage": 30.0},
                        ],
                        "alert_level": "normal",
                    }
                }
            },
        }
    },
)
async def get_metrics() -> ValidationMetrics:
    """검증 메트릭 조회 (JSON 형식)

    현재까지 수집된 LLM 응답 검증 메트릭을 반환합니다.
    - 총 요청 수, 성공/실패 수
    - 에러 타입별 카운트
    - 운세 타입별 메트릭
    - 시간대별 집계 (최근 24시간)
    - 알림 레벨 (normal/warning/error)

    Returns:
        ValidationMetrics: 검증 메트릭 전체 집계
    """
    monitor = get_validation_monitor()
    return monitor.get_metrics()


@router.get(
    "/metrics/prometheus",
    response_class=PlainTextResponse,
    summary="Prometheus 메트릭 조회",
    description="LLM 응답 검증 메트릭을 Prometheus exposition format으로 반환합니다.",
    responses={
        200: {
            "description": "Prometheus 형식 메트릭",
            "content": {
                "text/plain": {
                    "example": """# HELP yeji_validation_total 검증 요청 총 수
# TYPE yeji_validation_total counter
yeji_validation_total 1000
# HELP yeji_validation_failure_rate 현재 검증 실패율 (%)
# TYPE yeji_validation_failure_rate gauge
yeji_validation_failure_rate 5.0"""
                }
            },
        }
    },
)
async def get_prometheus_metrics() -> PlainTextResponse:
    """Prometheus 형식 메트릭 조회

    Prometheus scraping을 위한 텍스트 형식 메트릭을 반환합니다.
    - yeji_validation_total: 총 요청 수
    - yeji_validation_success_total: 성공 수
    - yeji_validation_failure_total: 실패 수
    - yeji_validation_failure_rate: 실패율 (%)
    - yeji_validation_failure_by_type: 에러 타입별 실패 수
    - yeji_validation_success_by_fortune_type: 운세 타입별 성공 수
    - yeji_validation_failure_by_fortune_type: 운세 타입별 실패 수

    Returns:
        PlainTextResponse: Prometheus exposition format 텍스트
    """
    monitor = get_validation_monitor()
    prometheus_metrics = monitor.get_prometheus_metrics()
    return PlainTextResponse(
        content=prometheus_metrics.to_prometheus_format(),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )


@router.post(
    "/metrics/reset",
    response_model=ValidationMetrics,
    summary="메트릭 초기화",
    description="모든 검증 메트릭 카운터를 초기화합니다. (개발/테스트용)",
    responses={
        200: {"description": "초기화된 메트릭"},
    },
)
async def reset_metrics(
    confirm: bool = Query(
        default=False,
        description="초기화 확인 (true로 설정해야 실제 초기화 수행)",
    ),
) -> ValidationMetrics:
    """메트릭 초기화 (개발/테스트용)

    모든 카운터를 0으로 초기화하고 수집 시작 시간을 갱신합니다.
    confirm=true 쿼리 파라미터가 필요합니다.

    Args:
        confirm: 초기화 확인 플래그 (기본값 False)

    Returns:
        ValidationMetrics: 초기화된 메트릭 (모두 0)
    """
    monitor = get_validation_monitor()

    if confirm:
        monitor.reset()

    return monitor.get_metrics()


@router.get(
    "/metrics/health",
    response_model=dict,
    summary="모니터링 상태 확인",
    description="모니터링 시스템의 현재 상태를 간단히 반환합니다.",
    responses={
        200: {
            "description": "모니터링 상태",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "alert_level": "normal",
                        "failure_rate": 5.0,
                        "total_requests": 1000,
                    }
                }
            },
        }
    },
)
async def get_metrics_health() -> dict:
    """모니터링 상태 확인

    빠른 상태 확인을 위한 경량 엔드포인트입니다.

    Returns:
        dict: 현재 상태 요약
    """
    monitor = get_validation_monitor()
    metrics = monitor.get_metrics()

    return {
        "status": "healthy",
        "alert_level": metrics.alert_level,
        "failure_rate": metrics.failure_rate,
        "total_requests": metrics.total_requests,
        "success_rate": metrics.success_rate,
    }
