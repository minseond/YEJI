"""LLM 응답 로깅용 Pydantic 모델

AI Server 응답을 체계적으로 수집하여 평가/최적화에 활용합니다.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class LogStatus(str, Enum):
    """로깅 상태 (성공/실패 분류)"""

    SUCCESS = "success"  # 검증 성공
    VALIDATION_ERROR = "validation_error"  # Pydantic 검증 실패
    JSON_PARSE_ERROR = "json_parse_error"  # JSON 파싱 실패
    CONNECTION_ERROR = "connection_error"  # LLM 연결 실패
    TIMEOUT_ERROR = "timeout_error"  # LLM 타임아웃
    UNKNOWN_ERROR = "unknown_error"  # 기타 에러


class RequestInput(BaseModel):
    """LLM 요청 입력 데이터"""

    # 출생 정보 (동양/서양 공통)
    birth_year: int = Field(..., description="출생 연도")
    birth_month: int = Field(..., description="출생 월")
    birth_day: int = Field(..., description="출생 일")
    birth_hour: int | None = Field(None, description="출생 시 (동양 필수)")
    birth_minute: int | None = Field(None, description="출생 분 (서양 옵션)")
    gender: str | None = Field(None, description="성별 (male/female/unknown)")

    # 서양 점성술 추가 정보
    latitude: float | None = Field(None, description="출생지 위도")
    longitude: float | None = Field(None, description="출생지 경도")


class ValidationResult(BaseModel):
    """검증 결과 정보"""

    status: LogStatus = Field(..., description="검증 상태")
    error_type: str | None = Field(None, description="에러 타입 (클래스명)")
    error_message: str | None = Field(None, description="에러 메시지")
    validation_errors: list[dict[str, Any]] | None = Field(
        None, description="Pydantic 검증 에러 목록"
    )


class TokenUsage(BaseModel):
    """토큰 사용량 정보"""

    prompt_tokens: int | None = Field(None, description="프롬프트 토큰 수")
    completion_tokens: int | None = Field(None, description="응답 토큰 수")
    total_tokens: int | None = Field(None, description="총 토큰 수")


class LLMResponseLog(BaseModel):
    """LLM 응답 로그 엔트리

    JSONL 형식으로 저장되는 개별 로그 레코드입니다.
    평가/최적화 파이프라인에서 활용됩니다.
    """

    # 식별 정보
    request_id: str = Field(..., description="고유 요청 ID (UUID)")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="UTC 타임스탬프")

    # 요청 정보
    fortune_type: Literal["eastern", "western", "full"] = Field(..., description="운세 타입")
    request_input: RequestInput = Field(..., description="요청 입력 데이터")

    # 응답 정보
    raw_response: str | None = Field(None, description="LLM 원본 응답 텍스트")
    parsed_response: dict[str, Any] | None = Field(
        None, description="JSON 파싱된 응답 (파싱 성공 시)"
    )

    # 검증 결과
    validation: ValidationResult = Field(..., description="검증 결과")

    # 성능 메트릭
    latency_ms: float = Field(default=0.0, description="응답 레이턴시 (ms)")
    token_usage: TokenUsage | None = Field(None, description="토큰 사용량")

    # 재시도 정보
    attempt_number: int = Field(default=1, description="시도 횟수 (1부터 시작)")
    max_retries: int = Field(default=2, description="최대 재시도 설정 값")

    # 메타데이터
    model_name: str | None = Field(None, description="사용된 LLM 모델명")
    temperature: float | None = Field(None, description="생성 온도 설정")

    # Pydantic v2: datetime은 기본적으로 ISO 형식으로 직렬화됨
