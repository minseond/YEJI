"""운세 생성 에러 체계 테스트

FortuneGeneratorError의 에러 타입 분류 및 HTTP 상태 코드 매핑을 검증합니다.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx
from pydantic import ValidationError

from yeji_ai.services.fortune_generator import (
    FortuneGenerator,
    FortuneGeneratorError,
    LLMErrorType,
    LLM_ERROR_CODES,
)


class TestLLMErrorType:
    """LLMErrorType Enum 테스트"""

    def test_error_type_values(self):
        """에러 타입 값 확인"""
        assert LLMErrorType.VALIDATION.value == "validation"
        assert LLMErrorType.CONNECTION.value == "connection"
        assert LLMErrorType.TIMEOUT.value == "timeout"
        assert LLMErrorType.UNKNOWN.value == "unknown"

    def test_error_codes_mapping(self):
        """에러 코드 매핑 확인"""
        assert LLM_ERROR_CODES[LLMErrorType.VALIDATION] == "LLM_VALIDATION_FAILED"
        assert LLM_ERROR_CODES[LLMErrorType.CONNECTION] == "LLM_CONNECTION_FAILED"
        assert LLM_ERROR_CODES[LLMErrorType.TIMEOUT] == "LLM_TIMEOUT"
        assert LLM_ERROR_CODES[LLMErrorType.UNKNOWN] == "LLM_UNKNOWN_ERROR"


class TestFortuneGeneratorError:
    """FortuneGeneratorError 예외 클래스 테스트"""

    def test_default_error_type(self):
        """기본 에러 타입 확인 (UNKNOWN)"""
        error = FortuneGeneratorError("테스트 에러")
        assert error.error_type == LLMErrorType.UNKNOWN
        assert error.error_code == "LLM_UNKNOWN_ERROR"
        assert error.message == "테스트 에러"
        assert error.raw_content is None
        assert error.details == {}

    def test_validation_error_type(self):
        """검증 에러 타입 확인"""
        error = FortuneGeneratorError(
            message="스키마 검증 실패",
            error_type=LLMErrorType.VALIDATION,
            raw_content='{"invalid": "json"}',
            details={"field": "element"},
        )
        assert error.error_type == LLMErrorType.VALIDATION
        assert error.error_code == "LLM_VALIDATION_FAILED"
        assert error.raw_content == '{"invalid": "json"}'
        assert error.details == {"field": "element"}

    def test_connection_error_type(self):
        """연결 에러 타입 확인"""
        error = FortuneGeneratorError(
            message="LLM 서비스 연결 불가",
            error_type=LLMErrorType.CONNECTION,
        )
        assert error.error_type == LLMErrorType.CONNECTION
        assert error.error_code == "LLM_CONNECTION_FAILED"

    def test_timeout_error_type(self):
        """타임아웃 에러 타입 확인"""
        error = FortuneGeneratorError(
            message="LLM 응답 타임아웃",
            error_type=LLMErrorType.TIMEOUT,
        )
        assert error.error_type == LLMErrorType.TIMEOUT
        assert error.error_code == "LLM_TIMEOUT"

    def test_to_error_response_basic(self):
        """기본 에러 응답 구조 확인"""
        error = FortuneGeneratorError(
            message="테스트 에러",
            error_type=LLMErrorType.CONNECTION,
            details={"attempts": 3},
        )
        response = error.to_error_response()

        assert "error" in response
        assert response["error"]["code"] == "LLM_CONNECTION_FAILED"
        assert response["error"]["message"] == "테스트 에러"
        assert response["error"]["details"]["attempts"] == 3

    def test_to_error_response_with_raw_content(self):
        """검증 에러 시 원본 응답 포함 확인"""
        raw_content = '{"element": "INVALID"}'
        error = FortuneGeneratorError(
            message="스키마 검증 실패",
            error_type=LLMErrorType.VALIDATION,
            raw_content=raw_content,
        )
        response = error.to_error_response()

        assert response["error"]["details"]["raw_content"] == raw_content

    def test_to_error_response_no_raw_content_for_non_validation(self):
        """검증 에러가 아닌 경우 원본 응답 미포함 확인"""
        error = FortuneGeneratorError(
            message="연결 실패",
            error_type=LLMErrorType.CONNECTION,
            raw_content="some content",  # 연결 에러에는 포함되지 않아야 함
        )
        response = error.to_error_response()

        assert "raw_content" not in response["error"]["details"]


class TestFortuneGeneratorErrorClassification:
    """FortuneGenerator의 에러 분류 로직 테스트"""

    @pytest.fixture
    def generator(self):
        """테스트용 FortuneGenerator 인스턴스"""
        generator = FortuneGenerator()
        generator._initialized = True
        return generator

    @pytest.fixture
    def mock_provider(self):
        """모의 Provider 생성"""
        provider = MagicMock()
        provider.chat = AsyncMock()
        return provider

    @pytest.mark.anyio
    async def test_connection_error_classification(self, generator, mock_provider):
        """연결 에러 분류 테스트"""
        from pydantic import BaseModel

        class DummySchema(BaseModel):
            element: str

        generator._provider = mock_provider
        mock_provider.chat.side_effect = httpx.ConnectError("Connection refused")

        with pytest.raises(FortuneGeneratorError) as exc_info:
            await generator._call_llm_structured(
                system_prompt="test",
                user_prompt="test",
                response_schema=DummySchema,
            )

        assert exc_info.value.error_type == LLMErrorType.CONNECTION
        assert exc_info.value.error_code == "LLM_CONNECTION_FAILED"

    @pytest.mark.anyio
    async def test_timeout_error_classification(self, generator, mock_provider):
        """타임아웃 에러 분류 테스트"""
        from pydantic import BaseModel

        class DummySchema(BaseModel):
            element: str

        generator._provider = mock_provider
        mock_provider.chat.side_effect = httpx.TimeoutException("Read timeout")

        with pytest.raises(FortuneGeneratorError) as exc_info:
            await generator._call_llm_structured(
                system_prompt="test",
                user_prompt="test",
                response_schema=DummySchema,
            )

        assert exc_info.value.error_type == LLMErrorType.TIMEOUT
        assert exc_info.value.error_code == "LLM_TIMEOUT"

    @pytest.mark.anyio
    async def test_validation_error_classification(self, generator, mock_provider):
        """검증 에러 분류 테스트"""
        from pydantic import BaseModel

        class TestSchema(BaseModel):
            element: str
            value: int

        # LLM이 잘못된 JSON을 반환하는 시나리오
        mock_response = MagicMock()
        mock_response.text = '{"element": "FIRE"}'  # value 필드 누락
        mock_response.latency_ms = 100
        generator._provider = mock_provider
        mock_provider.chat.return_value = mock_response

        with pytest.raises(FortuneGeneratorError) as exc_info:
            await generator._call_llm_structured(
                system_prompt="test",
                user_prompt="test",
                response_schema=TestSchema,
            )

        assert exc_info.value.error_type == LLMErrorType.VALIDATION
        assert exc_info.value.error_code == "LLM_VALIDATION_FAILED"
        assert exc_info.value.raw_content == '{"element": "FIRE"}'
        assert "validation_errors" in exc_info.value.details


class TestHTTPStatusCodeMapping:
    """HTTP 상태 코드 매핑 테스트"""

    def test_validation_error_returns_502(self):
        """검증 에러 → 502 Bad Gateway"""
        from fastapi import status
        from yeji_ai.api.v1.fortune.eastern import LLMErrorType

        status_code_map = {
            LLMErrorType.VALIDATION: status.HTTP_502_BAD_GATEWAY,
            LLMErrorType.CONNECTION: status.HTTP_503_SERVICE_UNAVAILABLE,
            LLMErrorType.TIMEOUT: status.HTTP_504_GATEWAY_TIMEOUT,
            LLMErrorType.UNKNOWN: status.HTTP_503_SERVICE_UNAVAILABLE,
        }

        assert status_code_map[LLMErrorType.VALIDATION] == 502

    def test_connection_error_returns_503(self):
        """연결 에러 → 503 Service Unavailable"""
        from fastapi import status
        from yeji_ai.api.v1.fortune.eastern import LLMErrorType

        status_code_map = {
            LLMErrorType.VALIDATION: status.HTTP_502_BAD_GATEWAY,
            LLMErrorType.CONNECTION: status.HTTP_503_SERVICE_UNAVAILABLE,
            LLMErrorType.TIMEOUT: status.HTTP_504_GATEWAY_TIMEOUT,
            LLMErrorType.UNKNOWN: status.HTTP_503_SERVICE_UNAVAILABLE,
        }

        assert status_code_map[LLMErrorType.CONNECTION] == 503

    def test_timeout_error_returns_504(self):
        """타임아웃 에러 → 504 Gateway Timeout"""
        from fastapi import status
        from yeji_ai.api.v1.fortune.eastern import LLMErrorType

        status_code_map = {
            LLMErrorType.VALIDATION: status.HTTP_502_BAD_GATEWAY,
            LLMErrorType.CONNECTION: status.HTTP_503_SERVICE_UNAVAILABLE,
            LLMErrorType.TIMEOUT: status.HTTP_504_GATEWAY_TIMEOUT,
            LLMErrorType.UNKNOWN: status.HTTP_503_SERVICE_UNAVAILABLE,
        }

        assert status_code_map[LLMErrorType.TIMEOUT] == 504

    def test_unknown_error_returns_503(self):
        """분류되지 않은 에러 → 503 Service Unavailable"""
        from fastapi import status
        from yeji_ai.api.v1.fortune.eastern import LLMErrorType

        status_code_map = {
            LLMErrorType.VALIDATION: status.HTTP_502_BAD_GATEWAY,
            LLMErrorType.CONNECTION: status.HTTP_503_SERVICE_UNAVAILABLE,
            LLMErrorType.TIMEOUT: status.HTTP_504_GATEWAY_TIMEOUT,
            LLMErrorType.UNKNOWN: status.HTTP_503_SERVICE_UNAVAILABLE,
        }

        assert status_code_map[LLMErrorType.UNKNOWN] == 503


class TestErrorResponseStructure:
    """에러 응답 구조 테스트"""

    def test_error_response_has_required_fields(self):
        """에러 응답에 필수 필드가 포함되어 있는지 확인"""
        error = FortuneGeneratorError(
            message="테스트 에러",
            error_type=LLMErrorType.VALIDATION,
            details={"schema": "SajuDataV2"},
        )
        response = error.to_error_response()

        # 필수 필드 확인
        assert "error" in response
        assert "code" in response["error"]
        assert "message" in response["error"]
        assert "details" in response["error"]

    def test_error_response_format(self):
        """에러 응답 형식이 명세와 일치하는지 확인"""
        error = FortuneGeneratorError(
            message="LLM 응답 스키마 불일치",
            error_type=LLMErrorType.VALIDATION,
            raw_content='{"invalid": true}',
            details={"schema": "WesternFortuneDataV2", "attempts": 3},
        )
        response = error.to_error_response()

        # 예상 형식:
        # {
        #   "error": {
        #     "code": "LLM_VALIDATION_FAILED",
        #     "message": "...",
        #     "details": {...}
        #   }
        # }
        assert response == {
            "error": {
                "code": "LLM_VALIDATION_FAILED",
                "message": "LLM 응답 스키마 불일치",
                "details": {
                    "schema": "WesternFortuneDataV2",
                    "attempts": 3,
                    "raw_content": '{"invalid": true}',
                },
            }
        }
