"""메트릭 API 엔드포인트 테스트

/metrics 엔드포인트의 기능을 테스트합니다:
- JSON 형식 메트릭 조회
- Prometheus 형식 메트릭 조회
- 메트릭 초기화
- 상태 확인
"""

import pytest
from httpx import ASGITransport, AsyncClient

from yeji_ai.main import app
from yeji_ai.models.metrics import ErrorType
from yeji_ai.services.validation_monitor import get_validation_monitor


@pytest.fixture
async def client():
    """테스트용 AsyncClient"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def monitor():
    """테스트용 모니터 (초기화됨)"""
    instance = get_validation_monitor()
    instance.reset()
    return instance


@pytest.mark.anyio
class TestMetricsEndpoint:
    """GET /metrics 테스트"""

    async def test_get_metrics_empty(self, client: AsyncClient, monitor) -> None:
        """빈 메트릭 조회"""
        # Act
        response = await client.get("/metrics")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total_requests"] == 0
        assert data["success_count"] == 0
        assert data["failure_count"] == 0
        assert data["failure_rate"] == 0.0
        assert data["alert_level"] == "normal"

    async def test_get_metrics_with_data(self, client: AsyncClient, monitor) -> None:
        """데이터가 있는 메트릭 조회"""
        # Arrange
        monitor.record_success("eastern")
        monitor.record_success("western")
        monitor.record_failure("eastern", ErrorType.VALIDATION)

        # Act
        response = await client.get("/metrics")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total_requests"] == 3
        assert data["success_count"] == 2
        assert data["failure_count"] == 1
        assert pytest.approx(data["failure_rate"], rel=0.01) == 33.33

    async def test_get_metrics_structure(self, client: AsyncClient, monitor) -> None:
        """메트릭 응답 구조 확인"""
        # Arrange
        monitor.record_success("eastern")
        monitor.record_failure("western", ErrorType.JSON_PARSE)

        # Act
        response = await client.get("/metrics")

        # Assert
        data = response.json()

        # 필수 필드 존재 확인
        assert "total_requests" in data
        assert "success_count" in data
        assert "failure_count" in data
        assert "failure_rate" in data
        assert "success_rate" in data
        assert "error_type_counts" in data
        assert "fortune_type_metrics" in data
        assert "hourly_metrics" in data
        assert "collected_since" in data
        assert "last_updated" in data
        assert "alert_level" in data


@pytest.mark.anyio
class TestPrometheusEndpoint:
    """GET /metrics/prometheus 테스트"""

    async def test_get_prometheus_metrics(self, client: AsyncClient, monitor) -> None:
        """Prometheus 형식 메트릭 조회"""
        # Arrange
        monitor.record_success("eastern")
        monitor.record_failure("western", ErrorType.VALIDATION)

        # Act
        response = await client.get("/metrics/prometheus")

        # Assert
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]

        content = response.text
        assert "yeji_validation_total 2" in content
        assert "yeji_validation_success_total 1" in content
        assert "yeji_validation_failure_total 1" in content

    async def test_prometheus_headers(self, client: AsyncClient, monitor) -> None:
        """Prometheus HELP/TYPE 헤더 확인"""
        # Act
        response = await client.get("/metrics/prometheus")

        # Assert
        content = response.text
        assert "# HELP yeji_validation_total" in content
        assert "# TYPE yeji_validation_total counter" in content

    async def test_prometheus_labels(self, client: AsyncClient, monitor) -> None:
        """Prometheus 라벨 형식 확인"""
        # Arrange
        monitor.record_failure("eastern", ErrorType.VALIDATION)
        monitor.record_failure("western", ErrorType.TIMEOUT)

        # Act
        response = await client.get("/metrics/prometheus")

        # Assert
        content = response.text
        assert 'error_type="validation"' in content
        assert 'error_type="timeout"' in content


@pytest.mark.anyio
class TestResetEndpoint:
    """POST /metrics/reset 테스트"""

    async def test_reset_without_confirm(self, client: AsyncClient, monitor) -> None:
        """confirm=false 시 초기화하지 않음"""
        # Arrange
        monitor.record_success("eastern")
        monitor.record_failure("western", ErrorType.VALIDATION)

        # Act
        response = await client.post("/metrics/reset")

        # Assert
        assert response.status_code == 200
        data = response.json()
        # 데이터가 유지되어야 함
        assert data["total_requests"] == 2

    async def test_reset_with_confirm(self, client: AsyncClient, monitor) -> None:
        """confirm=true 시 초기화"""
        # Arrange
        monitor.record_success("eastern")
        monitor.record_failure("western", ErrorType.VALIDATION)

        # Act
        response = await client.post("/metrics/reset?confirm=true")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total_requests"] == 0
        assert data["success_count"] == 0
        assert data["failure_count"] == 0


@pytest.mark.anyio
class TestHealthEndpoint:
    """GET /metrics/health 테스트"""

    async def test_health_endpoint(self, client: AsyncClient, monitor) -> None:
        """상태 확인 엔드포인트"""
        # Act
        response = await client.get("/metrics/health")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "alert_level" in data
        assert "failure_rate" in data
        assert "total_requests" in data
        assert "success_rate" in data

    async def test_health_reflects_alert_level(self, client: AsyncClient, monitor) -> None:
        """상태가 알림 레벨을 반영"""
        # Arrange - 40% 실패율 (ERROR 레벨)
        for _ in range(6):
            monitor.record_success("eastern")
        for _ in range(4):
            monitor.record_failure("eastern", ErrorType.VALIDATION)

        # Act
        response = await client.get("/metrics/health")

        # Assert
        data = response.json()
        assert data["alert_level"] == "error"
        assert data["failure_rate"] == 40.0


@pytest.mark.anyio
class TestAlertLevels:
    """알림 레벨 API 테스트"""

    async def test_normal_level(self, client: AsyncClient, monitor) -> None:
        """정상 레벨 (< 10%)"""
        # Arrange
        for _ in range(95):
            monitor.record_success("eastern")
        for _ in range(5):
            monitor.record_failure("eastern", ErrorType.VALIDATION)

        # Act
        response = await client.get("/metrics")

        # Assert
        data = response.json()
        assert data["alert_level"] == "normal"
        assert data["alert_message"] is None

    async def test_warning_level(self, client: AsyncClient, monitor) -> None:
        """경고 레벨 (10% - 30%)"""
        # Arrange
        for _ in range(80):
            monitor.record_success("eastern")
        for _ in range(20):
            monitor.record_failure("eastern", ErrorType.VALIDATION)

        # Act
        response = await client.get("/metrics")

        # Assert
        data = response.json()
        assert data["alert_level"] == "warning"
        assert data["alert_message"] is not None

    async def test_error_level(self, client: AsyncClient, monitor) -> None:
        """에러 레벨 (>= 30%)"""
        # Arrange
        for _ in range(50):
            monitor.record_success("eastern")
        for _ in range(50):
            monitor.record_failure("eastern", ErrorType.VALIDATION)

        # Act
        response = await client.get("/metrics")

        # Assert
        data = response.json()
        assert data["alert_level"] == "error"
        assert data["alert_message"] is not None
