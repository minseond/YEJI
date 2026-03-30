"""검증 실패 모니터링용 메트릭 모델

LLM 응답 검증 실패율을 실시간으로 모니터링하기 위한 Pydantic 모델입니다.
"""

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, computed_field


class ErrorType(str, Enum):
    """에러 타입 분류 (모니터링용)"""

    VALIDATION = "validation"  # Pydantic 검증 실패
    JSON_PARSE = "json_parse"  # JSON 파싱 실패
    CONNECTION = "connection"  # LLM 연결 실패
    TIMEOUT = "timeout"  # LLM 타임아웃
    UNKNOWN = "unknown"  # 기타 에러


class ErrorTypeCount(BaseModel):
    """에러 타입별 카운트"""

    error_type: ErrorType = Field(..., description="에러 타입")
    count: int = Field(default=0, ge=0, description="발생 횟수")
    percentage: float = Field(default=0.0, ge=0.0, le=100.0, description="전체 실패 중 비율 (%)")


class HourlyMetrics(BaseModel):
    """시간대별 집계 메트릭"""

    hour: str = Field(..., description="시간대 (ISO 형식, 예: 2025-01-30T14:00:00)")
    total_requests: int = Field(default=0, ge=0, description="총 요청 수")
    success_count: int = Field(default=0, ge=0, description="성공 수")
    failure_count: int = Field(default=0, ge=0, description="실패 수")

    @computed_field
    @property
    def failure_rate(self) -> float:
        """실패율 (%) 계산"""
        if self.total_requests == 0:
            return 0.0
        return round((self.failure_count / self.total_requests) * 100, 2)


class FortuneTypeMetrics(BaseModel):
    """운세 타입별 메트릭"""

    fortune_type: Literal["eastern", "western", "full"] = Field(..., description="운세 타입")
    total_requests: int = Field(default=0, ge=0, description="총 요청 수")
    success_count: int = Field(default=0, ge=0, description="성공 수")
    failure_count: int = Field(default=0, ge=0, description="실패 수")

    @computed_field
    @property
    def failure_rate(self) -> float:
        """실패율 (%) 계산"""
        if self.total_requests == 0:
            return 0.0
        return round((self.failure_count / self.total_requests) * 100, 2)


class ValidationMetrics(BaseModel):
    """검증 메트릭 전체 집계

    /metrics 엔드포인트에서 반환하는 메인 응답 모델입니다.
    """

    # 기본 카운터
    total_requests: int = Field(default=0, ge=0, description="총 요청 수")
    success_count: int = Field(default=0, ge=0, description="성공 수 (검증 통과)")
    failure_count: int = Field(default=0, ge=0, description="실패 수 (검증 실패)")

    # 실패율
    @computed_field
    @property
    def failure_rate(self) -> float:
        """전체 실패율 (%)"""
        if self.total_requests == 0:
            return 0.0
        return round((self.failure_count / self.total_requests) * 100, 2)

    @computed_field
    @property
    def success_rate(self) -> float:
        """전체 성공률 (%)"""
        if self.total_requests == 0:
            return 0.0
        return round((self.success_count / self.total_requests) * 100, 2)

    # 에러 타입별 집계
    error_type_counts: list[ErrorTypeCount] = Field(
        default_factory=list, description="에러 타입별 카운트"
    )

    # 운세 타입별 집계
    fortune_type_metrics: list[FortuneTypeMetrics] = Field(
        default_factory=list, description="운세 타입별 메트릭"
    )

    # 시간대별 집계 (최근 24시간)
    hourly_metrics: list[HourlyMetrics] = Field(
        default_factory=list, description="시간대별 메트릭 (최근 24시간)"
    )

    # 메타데이터
    collected_since: datetime = Field(
        default_factory=datetime.utcnow, description="수집 시작 시간 (UTC)"
    )
    last_updated: datetime = Field(
        default_factory=datetime.utcnow, description="마지막 업데이트 시간 (UTC)"
    )

    # 알림 상태
    alert_level: Literal["normal", "warning", "error"] = Field(
        default="normal", description="현재 알림 레벨"
    )
    alert_message: str | None = Field(None, description="알림 메시지 (있는 경우)")


class PrometheusMetric(BaseModel):
    """Prometheus 형식 단일 메트릭"""

    name: str = Field(..., description="메트릭 이름")
    help: str = Field(..., description="메트릭 설명")
    type: Literal["counter", "gauge", "histogram", "summary"] = Field(
        ..., description="메트릭 타입"
    )
    labels: dict[str, str] = Field(default_factory=dict, description="라벨")
    value: float = Field(..., description="메트릭 값")

    def to_prometheus_line(self) -> str:
        """Prometheus 텍스트 형식으로 변환

        Returns:
            Prometheus exposition format 문자열
        """
        labels_str = ""
        if self.labels:
            label_pairs = [f'{k}="{v}"' for k, v in self.labels.items()]
            labels_str = "{" + ",".join(label_pairs) + "}"

        return f"{self.name}{labels_str} {self.value}"


class PrometheusMetrics(BaseModel):
    """Prometheus 형식 메트릭 컬렉션"""

    metrics: list[PrometheusMetric] = Field(default_factory=list, description="메트릭 목록")

    def to_prometheus_format(self) -> str:
        """전체 메트릭을 Prometheus exposition format으로 변환

        Returns:
            Prometheus 텍스트 형식 문자열
        """
        lines: list[str] = []

        # 메트릭별로 그룹핑하여 HELP/TYPE 주석 추가
        current_name: str | None = None
        for metric in self.metrics:
            if metric.name != current_name:
                # 새로운 메트릭 이름이면 HELP/TYPE 추가
                lines.append(f"# HELP {metric.name} {metric.help}")
                lines.append(f"# TYPE {metric.name} {metric.type}")
                current_name = metric.name

            lines.append(metric.to_prometheus_line())

        return "\n".join(lines)
