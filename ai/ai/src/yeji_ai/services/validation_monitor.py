"""검증 실패 모니터링 서비스

LLM 응답 검증 실패율을 실시간으로 모니터링하여 품질 저하를 감지합니다.
싱글톤 패턴으로 구현되어 애플리케이션 전역에서 동일한 인스턴스를 사용합니다.
"""

import asyncio
from collections import Counter
from datetime import datetime, timedelta
from threading import Lock
from typing import Any, Literal

import structlog

from yeji_ai.models.metrics import (
    ErrorType,
    ErrorTypeCount,
    FortuneTypeMetrics,
    HourlyMetrics,
    PrometheusMetric,
    PrometheusMetrics,
    ValidationMetrics,
)

logger = structlog.get_logger()

# 알림 임계값 상수
WARNING_THRESHOLD = 10.0  # 실패율 10% 이상 → WARNING
ERROR_THRESHOLD = 30.0  # 실패율 30% 이상 → ERROR

# 주기적 로깅 간격 (초)
PERIODIC_LOG_INTERVAL = 60.0  # 1분마다 로깅


class ValidationMonitor:
    """검증 실패 모니터링 서비스

    인메모리 카운터를 사용하여 LLM 응답 검증 결과를 추적합니다.
    주기적으로 상태를 로깅하고, 실패율 임계값 초과 시 경고를 발생시킵니다.

    사용 예시:
        monitor = ValidationMonitor.get_instance()
        await monitor.start()

        # 성공 시
        monitor.record_success("eastern")

        # 실패 시
        monitor.record_failure("western", ErrorType.VALIDATION)

        # 메트릭 조회
        metrics = monitor.get_metrics()

        await monitor.stop()
    """

    _instance: "ValidationMonitor | None" = None
    _lock: Lock = Lock()

    def __new__(cls) -> "ValidationMonitor":
        """싱글톤 패턴: 항상 동일한 인스턴스 반환"""
        with cls._lock:
            if cls._instance is None:
                instance = super().__new__(cls)
                instance._initialized = False
                cls._instance = instance
            return cls._instance

    def __init__(self) -> None:
        """초기화 (싱글톤이므로 한 번만 실행)"""
        if getattr(self, "_initialized", False):
            return

        # 기본 카운터
        self._total_requests: int = 0
        self._success_count: int = 0
        self._failure_count: int = 0

        # 에러 타입별 카운터
        self._error_type_counts: Counter[ErrorType] = Counter()

        # 운세 타입별 카운터 (성공/실패 분리)
        self._fortune_type_success: Counter[str] = Counter()
        self._fortune_type_failure: Counter[str] = Counter()

        # 시간대별 카운터 (최근 24시간)
        # 키: ISO 형식 시간 문자열 (예: "2025-01-30T14:00:00")
        self._hourly_success: Counter[str] = Counter()
        self._hourly_failure: Counter[str] = Counter()

        # 수집 시작 시간
        self._collected_since: datetime = datetime.utcnow()
        self._last_updated: datetime = datetime.utcnow()

        # 백그라운드 태스크
        self._periodic_task: asyncio.Task | None = None
        self._running: bool = False

        # 스레드 안전을 위한 락
        self._counter_lock: Lock = Lock()

        self._initialized = True

    @classmethod
    def get_instance(cls) -> "ValidationMonitor":
        """싱글톤 인스턴스 반환

        Returns:
            ValidationMonitor 인스턴스
        """
        return cls()

    def _get_current_hour_key(self) -> str:
        """현재 시간대 키 생성 (시간 단위로 절삭)

        Returns:
            ISO 형식 시간 문자열 (분/초 제외)
        """
        now = datetime.utcnow()
        truncated = now.replace(minute=0, second=0, microsecond=0)
        return truncated.isoformat()

    def _cleanup_old_hourly_data(self) -> None:
        """24시간 이상 된 시간대별 데이터 정리"""
        cutoff = datetime.utcnow() - timedelta(hours=24)
        cutoff_key = cutoff.replace(minute=0, second=0, microsecond=0).isoformat()

        # 오래된 키 삭제
        old_keys = [
            key
            for key in list(self._hourly_success.keys()) + list(self._hourly_failure.keys())
            if key < cutoff_key
        ]
        for key in set(old_keys):
            self._hourly_success.pop(key, None)
            self._hourly_failure.pop(key, None)

    def record_success(
        self,
        fortune_type: Literal["eastern", "western", "full"],
    ) -> None:
        """검증 성공 기록

        Args:
            fortune_type: 운세 타입 (eastern/western/full)
        """
        with self._counter_lock:
            self._total_requests += 1
            self._success_count += 1
            self._fortune_type_success[fortune_type] += 1

            hour_key = self._get_current_hour_key()
            self._hourly_success[hour_key] += 1

            self._last_updated = datetime.utcnow()

        logger.debug(
            "validation_success_recorded",
            fortune_type=fortune_type,
            total_requests=self._total_requests,
            success_count=self._success_count,
        )

    def record_failure(
        self,
        fortune_type: Literal["eastern", "western", "full"],
        error_type: ErrorType,
        error_message: str | None = None,
    ) -> None:
        """검증 실패 기록

        Args:
            fortune_type: 운세 타입 (eastern/western/full)
            error_type: 에러 타입
            error_message: 에러 메시지 (로깅용, 선택)
        """
        with self._counter_lock:
            self._total_requests += 1
            self._failure_count += 1
            self._error_type_counts[error_type] += 1
            self._fortune_type_failure[fortune_type] += 1

            hour_key = self._get_current_hour_key()
            self._hourly_failure[hour_key] += 1

            self._last_updated = datetime.utcnow()

            # 실패율 계산 (락 내에서 수행)
            failure_rate = self._get_failure_rate_unlocked()

        # 알림 레벨 확인 (락 해제 후)
        alert_level = self._get_alert_level(failure_rate)

        # 알림 레벨에 따른 로깅
        log_data: dict[str, Any] = {
            "fortune_type": fortune_type,
            "error_type": error_type.value,
            "total_requests": self._total_requests,
            "failure_count": self._failure_count,
            "failure_rate": failure_rate,
        }
        if error_message:
            log_data["error_message"] = error_message[:200]  # 최대 200자

        if alert_level == "error":
            logger.error("validation_failure_recorded_critical", **log_data)
        elif alert_level == "warning":
            logger.warning("validation_failure_recorded_warning", **log_data)
        else:
            logger.debug("validation_failure_recorded", **log_data)

    def _get_failure_rate_unlocked(self) -> float:
        """실패율 반환 (락 없이, 내부 사용 전용)

        주의: 이미 락이 획득된 상태에서 호출하거나,
        락이 필요 없는 단순 읽기에서만 사용합니다.

        Returns:
            실패율 (%, 0.0 ~ 100.0)
        """
        if self._total_requests == 0:
            return 0.0
        return round((self._failure_count / self._total_requests) * 100, 2)

    def get_failure_rate(self) -> float:
        """현재 실패율 반환

        Returns:
            실패율 (%, 0.0 ~ 100.0)
        """
        with self._counter_lock:
            return self._get_failure_rate_unlocked()

    def _get_alert_level(self, failure_rate: float) -> Literal["normal", "warning", "error"]:
        """실패율에 따른 알림 레벨 결정

        Args:
            failure_rate: 실패율 (%)

        Returns:
            알림 레벨 (normal/warning/error)
        """
        if failure_rate >= ERROR_THRESHOLD:
            return "error"
        elif failure_rate >= WARNING_THRESHOLD:
            return "warning"
        return "normal"

    def _get_alert_message(
        self,
        alert_level: Literal["normal", "warning", "error"],
        failure_rate: float,
    ) -> str | None:
        """알림 메시지 생성

        Args:
            alert_level: 알림 레벨
            failure_rate: 실패율

        Returns:
            알림 메시지 (normal이면 None)
        """
        if alert_level == "error":
            return (
                f"심각: 검증 실패율 {failure_rate:.1f}%가 임계값 {ERROR_THRESHOLD}%를 초과했습니다."
            )
        elif alert_level == "warning":
            return (
                f"경고: 검증 실패율 {failure_rate:.1f}%가 주의 수준 "
                f"{WARNING_THRESHOLD}%를 초과했습니다."
            )
        return None

    def get_metrics(self) -> ValidationMetrics:
        """현재 메트릭 조회

        Returns:
            ValidationMetrics 모델 (전체 집계 정보)
        """
        with self._counter_lock:
            # 오래된 시간대별 데이터 정리
            self._cleanup_old_hourly_data()

            # 에러 타입별 집계
            total_failures = self._failure_count or 1  # 0으로 나누기 방지
            error_type_counts = [
                ErrorTypeCount(
                    error_type=error_type,
                    count=count,
                    percentage=round((count / total_failures) * 100, 2)
                    if self._failure_count > 0
                    else 0.0,
                )
                for error_type, count in self._error_type_counts.items()
            ]

            # 운세 타입별 집계
            fortune_types: list[Literal["eastern", "western", "full"]] = [
                "eastern",
                "western",
                "full",
            ]
            fortune_type_metrics = []
            for ft in fortune_types:
                success = self._fortune_type_success.get(ft, 0)
                failure = self._fortune_type_failure.get(ft, 0)
                total = success + failure
                if total > 0:  # 요청이 있는 경우만 포함
                    fortune_type_metrics.append(
                        FortuneTypeMetrics(
                            fortune_type=ft,
                            total_requests=total,
                            success_count=success,
                            failure_count=failure,
                        )
                    )

            # 시간대별 집계 (정렬)
            all_hours = set(self._hourly_success.keys()) | set(self._hourly_failure.keys())
            hourly_metrics = []
            for hour_key in sorted(all_hours):
                success = self._hourly_success.get(hour_key, 0)
                failure = self._hourly_failure.get(hour_key, 0)
                hourly_metrics.append(
                    HourlyMetrics(
                        hour=hour_key,
                        total_requests=success + failure,
                        success_count=success,
                        failure_count=failure,
                    )
                )

            # 알림 레벨 및 메시지 (락 내에서 계산)
            failure_rate = self._get_failure_rate_unlocked()
            alert_level = self._get_alert_level(failure_rate)
            alert_message = self._get_alert_message(alert_level, failure_rate)

            return ValidationMetrics(
                total_requests=self._total_requests,
                success_count=self._success_count,
                failure_count=self._failure_count,
                error_type_counts=error_type_counts,
                fortune_type_metrics=fortune_type_metrics,
                hourly_metrics=hourly_metrics,
                collected_since=self._collected_since,
                last_updated=self._last_updated,
                alert_level=alert_level,
                alert_message=alert_message,
            )

    def get_prometheus_metrics(self) -> PrometheusMetrics:
        """Prometheus 형식 메트릭 반환

        Returns:
            PrometheusMetrics 모델 (Prometheus exposition format 지원)
        """
        metrics: list[PrometheusMetric] = []

        with self._counter_lock:
            # 기본 카운터
            metrics.append(
                PrometheusMetric(
                    name="yeji_validation_total",
                    help="검증 요청 총 수",
                    type="counter",
                    value=float(self._total_requests),
                )
            )
            metrics.append(
                PrometheusMetric(
                    name="yeji_validation_success_total",
                    help="검증 성공 총 수",
                    type="counter",
                    value=float(self._success_count),
                )
            )
            metrics.append(
                PrometheusMetric(
                    name="yeji_validation_failure_total",
                    help="검증 실패 총 수",
                    type="counter",
                    value=float(self._failure_count),
                )
            )

            # 실패율 (게이지) - 락 내에서 계산
            metrics.append(
                PrometheusMetric(
                    name="yeji_validation_failure_rate",
                    help="현재 검증 실패율 (%)",
                    type="gauge",
                    value=self._get_failure_rate_unlocked(),
                )
            )

            # 에러 타입별 카운터
            for error_type, count in self._error_type_counts.items():
                metrics.append(
                    PrometheusMetric(
                        name="yeji_validation_failure_by_type",
                        help="에러 타입별 검증 실패 수",
                        type="counter",
                        labels={"error_type": error_type.value},
                        value=float(count),
                    )
                )

            # 운세 타입별 성공 카운터
            for fortune_type, count in self._fortune_type_success.items():
                metrics.append(
                    PrometheusMetric(
                        name="yeji_validation_success_by_fortune_type",
                        help="운세 타입별 검증 성공 수",
                        type="counter",
                        labels={"fortune_type": fortune_type},
                        value=float(count),
                    )
                )

            # 운세 타입별 실패 카운터
            for fortune_type, count in self._fortune_type_failure.items():
                metrics.append(
                    PrometheusMetric(
                        name="yeji_validation_failure_by_fortune_type",
                        help="운세 타입별 검증 실패 수",
                        type="counter",
                        labels={"fortune_type": fortune_type},
                        value=float(count),
                    )
                )

        return PrometheusMetrics(metrics=metrics)

    def reset(self) -> None:
        """모든 카운터 초기화 (테스트용)"""
        with self._counter_lock:
            self._total_requests = 0
            self._success_count = 0
            self._failure_count = 0
            self._error_type_counts.clear()
            self._fortune_type_success.clear()
            self._fortune_type_failure.clear()
            self._hourly_success.clear()
            self._hourly_failure.clear()
            self._collected_since = datetime.utcnow()
            self._last_updated = datetime.utcnow()

        logger.info("validation_monitor_reset")

    async def start(self) -> None:
        """모니터 시작 (주기적 로깅 태스크 실행)"""
        if self._running:
            logger.warning("validation_monitor_already_running")
            return

        self._running = True
        self._periodic_task = asyncio.create_task(self._periodic_logger())
        logger.info(
            "validation_monitor_started",
            log_interval_seconds=PERIODIC_LOG_INTERVAL,
            warning_threshold=WARNING_THRESHOLD,
            error_threshold=ERROR_THRESHOLD,
        )

    async def stop(self) -> None:
        """모니터 정지"""
        if not self._running:
            return

        self._running = False
        if self._periodic_task is not None:
            self._periodic_task.cancel()
            try:
                await self._periodic_task
            except asyncio.CancelledError:
                pass
            self._periodic_task = None

        logger.info("validation_monitor_stopped")

    async def _periodic_logger(self) -> None:
        """주기적 상태 로깅 (1분마다)

        실패율에 따라 다른 로그 레벨을 사용합니다:
        - 실패율 > 30%: ERROR
        - 실패율 > 10%: WARNING
        - 그 외: INFO
        """
        while self._running:
            try:
                await asyncio.sleep(PERIODIC_LOG_INTERVAL)

                if not self._running:
                    break

                # 현재 상태 수집
                failure_rate = self.get_failure_rate()
                alert_level = self._get_alert_level(failure_rate)

                log_data: dict[str, Any] = {
                    "total_requests": self._total_requests,
                    "success_count": self._success_count,
                    "failure_count": self._failure_count,
                    "failure_rate": failure_rate,
                    "alert_level": alert_level,
                }

                # 에러 타입별 상위 3개
                top_errors = self._error_type_counts.most_common(3)
                if top_errors:
                    log_data["top_errors"] = [{"type": e.value, "count": c} for e, c in top_errors]

                # 알림 레벨에 따른 로깅
                if alert_level == "error":
                    logger.error("validation_monitor_periodic_report", **log_data)
                elif alert_level == "warning":
                    logger.warning("validation_monitor_periodic_report", **log_data)
                else:
                    logger.info("validation_monitor_periodic_report", **log_data)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(
                    "validation_monitor_periodic_error",
                    error=str(e),
                    exc_info=True,
                )
                await asyncio.sleep(PERIODIC_LOG_INTERVAL)


# ============================================================
# 글로벌 인스턴스 접근 함수
# ============================================================


def get_validation_monitor() -> ValidationMonitor:
    """글로벌 ValidationMonitor 인스턴스 반환

    싱글톤 패턴으로 항상 동일한 인스턴스를 반환합니다.

    Returns:
        ValidationMonitor 인스턴스
    """
    return ValidationMonitor.get_instance()


async def initialize_validation_monitor() -> ValidationMonitor:
    """ValidationMonitor 초기화 및 시작

    애플리케이션 시작 시 호출합니다.

    Returns:
        초기화된 ValidationMonitor 인스턴스
    """
    monitor = get_validation_monitor()
    await monitor.start()
    return monitor


async def shutdown_validation_monitor() -> None:
    """ValidationMonitor 종료

    애플리케이션 종료 시 호출합니다.
    """
    monitor = get_validation_monitor()
    await monitor.stop()
