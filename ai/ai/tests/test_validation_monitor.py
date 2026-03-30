"""검증 실패 모니터링 서비스 테스트

ValidationMonitor의 기능을 테스트합니다:
- 성공/실패 기록
- 실패율 계산
- 에러 타입별 집계
- 운세 타입별 집계
- 시간대별 집계
- 알림 레벨 판단
- Prometheus 형식 출력
"""

import pytest

from yeji_ai.models.metrics import ErrorType
from yeji_ai.services.validation_monitor import (
    ERROR_THRESHOLD,
    WARNING_THRESHOLD,
    ValidationMonitor,
    get_validation_monitor,
)


@pytest.fixture
def monitor() -> ValidationMonitor:
    """테스트용 ValidationMonitor 인스턴스 (초기화됨)"""
    # 싱글톤이므로 기존 인스턴스 초기화
    instance = ValidationMonitor.get_instance()
    instance.reset()
    return instance


class TestValidationMonitor:
    """ValidationMonitor 기본 기능 테스트"""

    def test_singleton_pattern(self) -> None:
        """싱글톤 패턴 동작 확인"""
        # Arrange & Act
        instance1 = ValidationMonitor.get_instance()
        instance2 = ValidationMonitor.get_instance()
        instance3 = get_validation_monitor()

        # Assert
        assert instance1 is instance2
        assert instance2 is instance3

    def test_record_success(self, monitor: ValidationMonitor) -> None:
        """성공 기록 테스트"""
        # Act
        monitor.record_success("eastern")
        monitor.record_success("western")
        monitor.record_success("eastern")

        # Assert
        metrics = monitor.get_metrics()
        assert metrics.total_requests == 3
        assert metrics.success_count == 3
        assert metrics.failure_count == 0
        assert metrics.failure_rate == 0.0

    def test_record_failure(self, monitor: ValidationMonitor) -> None:
        """실패 기록 테스트"""
        # Act
        monitor.record_failure("eastern", ErrorType.VALIDATION)
        monitor.record_failure("western", ErrorType.JSON_PARSE)
        monitor.record_failure("eastern", ErrorType.CONNECTION)

        # Assert
        metrics = monitor.get_metrics()
        assert metrics.total_requests == 3
        assert metrics.success_count == 0
        assert metrics.failure_count == 3
        assert metrics.failure_rate == 100.0

    def test_mixed_success_and_failure(self, monitor: ValidationMonitor) -> None:
        """성공/실패 혼합 테스트"""
        # Arrange - 10개 중 3개 실패 (30%)
        for _ in range(7):
            monitor.record_success("eastern")
        for _ in range(3):
            monitor.record_failure("eastern", ErrorType.VALIDATION)

        # Assert
        metrics = monitor.get_metrics()
        assert metrics.total_requests == 10
        assert metrics.success_count == 7
        assert metrics.failure_count == 3
        assert metrics.failure_rate == 30.0
        assert metrics.success_rate == 70.0


class TestErrorTypeAggregation:
    """에러 타입별 집계 테스트"""

    def test_error_type_counts(self, monitor: ValidationMonitor) -> None:
        """에러 타입별 카운트 테스트"""
        # Arrange
        monitor.record_failure("eastern", ErrorType.VALIDATION)
        monitor.record_failure("eastern", ErrorType.VALIDATION)
        monitor.record_failure("western", ErrorType.JSON_PARSE)
        monitor.record_failure("eastern", ErrorType.CONNECTION)
        monitor.record_failure("western", ErrorType.TIMEOUT)

        # Act
        metrics = monitor.get_metrics()

        # Assert
        error_counts = {et.error_type: et.count for et in metrics.error_type_counts}
        assert error_counts[ErrorType.VALIDATION] == 2
        assert error_counts[ErrorType.JSON_PARSE] == 1
        assert error_counts[ErrorType.CONNECTION] == 1
        assert error_counts[ErrorType.TIMEOUT] == 1

    def test_error_type_percentage(self, monitor: ValidationMonitor) -> None:
        """에러 타입별 비율 테스트"""
        # Arrange - 총 10개 실패
        for _ in range(5):
            monitor.record_failure("eastern", ErrorType.VALIDATION)
        for _ in range(3):
            monitor.record_failure("western", ErrorType.JSON_PARSE)
        for _ in range(2):
            monitor.record_failure("eastern", ErrorType.CONNECTION)

        # Act
        metrics = monitor.get_metrics()

        # Assert
        error_percentages = {et.error_type: et.percentage for et in metrics.error_type_counts}
        assert error_percentages[ErrorType.VALIDATION] == 50.0
        assert error_percentages[ErrorType.JSON_PARSE] == 30.0
        assert error_percentages[ErrorType.CONNECTION] == 20.0


class TestFortuneTypeAggregation:
    """운세 타입별 집계 테스트"""

    def test_fortune_type_metrics(self, monitor: ValidationMonitor) -> None:
        """운세 타입별 메트릭 테스트"""
        # Arrange
        for _ in range(5):
            monitor.record_success("eastern")
        for _ in range(2):
            monitor.record_failure("eastern", ErrorType.VALIDATION)
        for _ in range(8):
            monitor.record_success("western")
        for _ in range(2):
            monitor.record_failure("western", ErrorType.JSON_PARSE)

        # Act
        metrics = monitor.get_metrics()

        # Assert
        fortune_metrics = {ft.fortune_type: ft for ft in metrics.fortune_type_metrics}

        eastern = fortune_metrics["eastern"]
        assert eastern.total_requests == 7
        assert eastern.success_count == 5
        assert eastern.failure_count == 2
        assert eastern.failure_rate == pytest.approx(28.57, rel=0.01)

        western = fortune_metrics["western"]
        assert western.total_requests == 10
        assert western.success_count == 8
        assert western.failure_count == 2
        assert western.failure_rate == 20.0


class TestAlertLevels:
    """알림 레벨 테스트"""

    def test_alert_level_normal(self, monitor: ValidationMonitor) -> None:
        """정상 레벨 테스트 (실패율 < 10%)"""
        # Arrange - 100개 중 5개 실패 (5%)
        for _ in range(95):
            monitor.record_success("eastern")
        for _ in range(5):
            monitor.record_failure("eastern", ErrorType.VALIDATION)

        # Act
        metrics = monitor.get_metrics()

        # Assert
        assert metrics.failure_rate == 5.0
        assert metrics.alert_level == "normal"
        assert metrics.alert_message is None

    def test_alert_level_warning(self, monitor: ValidationMonitor) -> None:
        """경고 레벨 테스트 (10% <= 실패율 < 30%)"""
        # Arrange - 100개 중 15개 실패 (15%)
        for _ in range(85):
            monitor.record_success("eastern")
        for _ in range(15):
            monitor.record_failure("eastern", ErrorType.VALIDATION)

        # Act
        metrics = monitor.get_metrics()

        # Assert
        assert metrics.failure_rate == 15.0
        assert metrics.alert_level == "warning"
        assert metrics.alert_message is not None
        assert "경고" in metrics.alert_message
        assert str(WARNING_THRESHOLD) in metrics.alert_message

    def test_alert_level_error(self, monitor: ValidationMonitor) -> None:
        """에러 레벨 테스트 (실패율 >= 30%)"""
        # Arrange - 100개 중 40개 실패 (40%)
        for _ in range(60):
            monitor.record_success("western")
        for _ in range(40):
            monitor.record_failure("western", ErrorType.CONNECTION)

        # Act
        metrics = monitor.get_metrics()

        # Assert
        assert metrics.failure_rate == 40.0
        assert metrics.alert_level == "error"
        assert metrics.alert_message is not None
        assert "심각" in metrics.alert_message
        assert str(ERROR_THRESHOLD) in metrics.alert_message


class TestPrometheusFormat:
    """Prometheus 형식 출력 테스트"""

    def test_prometheus_metrics_basic(self, monitor: ValidationMonitor) -> None:
        """Prometheus 기본 메트릭 테스트"""
        # Arrange
        monitor.record_success("eastern")
        monitor.record_failure("western", ErrorType.VALIDATION)

        # Act
        prometheus = monitor.get_prometheus_metrics()
        output = prometheus.to_prometheus_format()

        # Assert
        assert "yeji_validation_total 2" in output
        assert "yeji_validation_success_total 1" in output
        assert "yeji_validation_failure_total 1" in output
        assert "yeji_validation_failure_rate 50.0" in output

    def test_prometheus_metrics_with_labels(self, monitor: ValidationMonitor) -> None:
        """Prometheus 라벨 메트릭 테스트"""
        # Arrange
        monitor.record_failure("eastern", ErrorType.VALIDATION)
        monitor.record_failure("western", ErrorType.JSON_PARSE)

        # Act
        prometheus = monitor.get_prometheus_metrics()
        output = prometheus.to_prometheus_format()

        # Assert
        assert 'yeji_validation_failure_by_type{error_type="validation"} 1' in output
        assert 'yeji_validation_failure_by_type{error_type="json_parse"} 1' in output

    def test_prometheus_format_headers(self, monitor: ValidationMonitor) -> None:
        """Prometheus HELP/TYPE 헤더 테스트"""
        # Act
        prometheus = monitor.get_prometheus_metrics()
        output = prometheus.to_prometheus_format()

        # Assert
        assert "# HELP yeji_validation_total" in output
        assert "# TYPE yeji_validation_total counter" in output
        assert "# TYPE yeji_validation_failure_rate gauge" in output


class TestHourlyAggregation:
    """시간대별 집계 테스트"""

    def test_hourly_metrics_recorded(self, monitor: ValidationMonitor) -> None:
        """시간대별 메트릭 기록 테스트"""
        # Arrange
        monitor.record_success("eastern")
        monitor.record_success("western")
        monitor.record_failure("eastern", ErrorType.VALIDATION)

        # Act
        metrics = monitor.get_metrics()

        # Assert - 현재 시간대에 데이터가 있어야 함
        assert len(metrics.hourly_metrics) >= 1
        current_hour = metrics.hourly_metrics[-1]
        assert current_hour.total_requests >= 3
        assert current_hour.success_count >= 2
        assert current_hour.failure_count >= 1


class TestReset:
    """초기화 테스트"""

    def test_reset_clears_all_counters(self, monitor: ValidationMonitor) -> None:
        """초기화 시 모든 카운터 클리어"""
        # Arrange
        monitor.record_success("eastern")
        monitor.record_failure("western", ErrorType.VALIDATION)

        # Act
        monitor.reset()
        metrics = monitor.get_metrics()

        # Assert
        assert metrics.total_requests == 0
        assert metrics.success_count == 0
        assert metrics.failure_count == 0
        assert len(metrics.error_type_counts) == 0
        assert len(metrics.fortune_type_metrics) == 0


class TestThreadSafety:
    """스레드 안전성 테스트 (기본)"""

    def test_concurrent_writes(self, monitor: ValidationMonitor) -> None:
        """동시 쓰기 테스트 (단순화)"""
        import concurrent.futures

        # Arrange
        def record_many():
            for _ in range(100):
                monitor.record_success("eastern")
                monitor.record_failure("western", ErrorType.VALIDATION)

        # Act
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(record_many) for _ in range(4)]
            concurrent.futures.wait(futures)

        # Assert - 총 합계가 맞아야 함
        metrics = monitor.get_metrics()
        assert metrics.total_requests == 800  # 4 threads * 100 iterations * 2 records
        assert metrics.success_count == 400
        assert metrics.failure_count == 400


@pytest.mark.anyio
class TestAsyncOperations:
    """비동기 작업 테스트"""

    async def test_start_stop(self) -> None:
        """모니터 시작/정지 테스트"""
        # Arrange
        monitor = get_validation_monitor()

        # Act
        await monitor.start()
        assert monitor._running is True

        await monitor.stop()
        assert monitor._running is False

    async def test_periodic_task_runs(self) -> None:
        """주기적 태스크 실행 테스트"""
        import asyncio

        # Arrange
        monitor = get_validation_monitor()
        monitor.reset()

        # Act
        await monitor.start()
        monitor.record_success("eastern")
        monitor.record_failure("western", ErrorType.VALIDATION)

        # 짧은 대기 (주기적 로깅이 실행될 시간은 아님)
        await asyncio.sleep(0.1)

        await monitor.stop()

        # Assert
        metrics = monitor.get_metrics()
        assert metrics.total_requests == 2
