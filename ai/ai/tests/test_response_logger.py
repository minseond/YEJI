"""LLM 응답 로거 테스트

response_logger.py의 기능을 테스트합니다.
"""

import asyncio
import json
import tempfile
from datetime import date
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from yeji_ai.models.logging import (
    LLMResponseLog,
    LogStatus,
    RequestInput,
    ValidationResult,
)
from yeji_ai.services.response_logger import (
    ResponseLogger,
    get_response_logger,
    initialize_response_logger,
    shutdown_response_logger,
)


# ============================================================
# 모델 테스트
# ============================================================


class TestLoggingModels:
    """로깅 모델 테스트"""

    def test_request_input_model(self):
        """RequestInput 모델 생성 테스트"""
        # Arrange & Act
        request_input = RequestInput(
            birth_year=1990,
            birth_month=3,
            birth_day=15,
            birth_hour=14,
            gender="male",
        )

        # Assert
        assert request_input.birth_year == 1990
        assert request_input.birth_month == 3
        assert request_input.birth_day == 15
        assert request_input.birth_hour == 14
        assert request_input.gender == "male"

    def test_validation_result_success(self):
        """ValidationResult 성공 상태 테스트"""
        # Arrange & Act
        result = ValidationResult(status=LogStatus.SUCCESS)

        # Assert
        assert result.status == LogStatus.SUCCESS
        assert result.error_type is None
        assert result.error_message is None

    def test_validation_result_error(self):
        """ValidationResult 에러 상태 테스트"""
        # Arrange & Act
        result = ValidationResult(
            status=LogStatus.VALIDATION_ERROR,
            error_type="ValidationError",
            error_message="필드 누락",
            validation_errors=[{"loc": ["element"], "msg": "필수 필드"}],
        )

        # Assert
        assert result.status == LogStatus.VALIDATION_ERROR
        assert result.error_type == "ValidationError"
        assert result.error_message == "필드 누락"
        assert len(result.validation_errors) == 1

    def test_llm_response_log_model(self):
        """LLMResponseLog 모델 생성 테스트"""
        # Arrange & Act
        log = LLMResponseLog(
            request_id="test-uuid-1234",
            fortune_type="eastern",
            request_input=RequestInput(
                birth_year=1990,
                birth_month=3,
                birth_day=15,
                birth_hour=14,
            ),
            raw_response='{"element": "WOOD"}',
            parsed_response={"element": "WOOD"},
            validation=ValidationResult(status=LogStatus.SUCCESS),
            latency_ms=1500,
            model_name="test-model",
            temperature=0.7,
        )

        # Assert
        assert log.request_id == "test-uuid-1234"
        assert log.fortune_type == "eastern"
        assert log.latency_ms == 1500
        assert log.validation.status == LogStatus.SUCCESS

    def test_llm_response_log_json_serialization(self):
        """LLMResponseLog JSON 직렬화 테스트"""
        # Arrange
        log = LLMResponseLog(
            request_id="test-uuid-1234",
            fortune_type="western",
            request_input=RequestInput(
                birth_year=1990,
                birth_month=3,
                birth_day=15,
            ),
            validation=ValidationResult(status=LogStatus.SUCCESS),
        )

        # Act
        json_str = log.model_dump_json()
        parsed = json.loads(json_str)

        # Assert
        assert parsed["request_id"] == "test-uuid-1234"
        assert parsed["fortune_type"] == "western"
        assert "timestamp" in parsed


# ============================================================
# 로거 테스트
# ============================================================


class TestResponseLogger:
    """ResponseLogger 테스트"""

    @pytest.fixture
    def temp_log_dir(self):
        """임시 로그 디렉토리 생성"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    async def logger_instance(self, temp_log_dir):
        """테스트용 로거 인스턴스"""
        logger = ResponseLogger(
            base_dir=temp_log_dir,
            queue_size=100,
            flush_interval=0.1,  # 빠른 플러시
        )
        await logger.start()
        yield logger
        await logger.stop()

    @pytest.mark.asyncio
    async def test_logger_start_stop(self, temp_log_dir):
        """로거 시작/종료 테스트"""
        # Arrange
        logger = ResponseLogger(base_dir=temp_log_dir)

        # Act - 시작
        await logger.start()

        # Assert - 디렉토리 생성 확인
        assert temp_log_dir.exists()

        # Act - 종료
        await logger.stop()

        # 중복 종료 호출도 안전해야 함
        await logger.stop()

    @pytest.mark.asyncio
    async def test_log_success(self, logger_instance, temp_log_dir):
        """성공 로깅 테스트"""
        # Arrange
        birth_data = {
            "birth_year": 1990,
            "birth_month": 3,
            "birth_day": 15,
            "birth_hour": 14,
            "gender": "male",
        }

        # Act
        request_id = await logger_instance.log_success(
            fortune_type="eastern",
            request_input=birth_data,
            raw_response='{"element": "WOOD"}',
            parsed_response={"element": "WOOD"},
            latency_ms=1500,
            model_name="test-model",
            temperature=0.7,
        )

        # 플러시 대기
        await asyncio.sleep(0.2)

        # Assert
        assert request_id is not None
        assert len(request_id) == 36  # UUID 길이

        # 로그 파일 확인
        today = date.today()
        log_file = temp_log_dir / f"{today.isoformat()}.jsonl"
        assert log_file.exists()

        # 로그 내용 확인
        with open(log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            assert len(lines) == 1
            log_entry = json.loads(lines[0])
            assert log_entry["request_id"] == request_id
            assert log_entry["fortune_type"] == "eastern"
            assert log_entry["validation"]["status"] == "success"
            assert log_entry["latency_ms"] == 1500

    @pytest.mark.asyncio
    async def test_log_validation_error(self, logger_instance, temp_log_dir):
        """검증 에러 로깅 테스트"""
        # Arrange
        birth_data = {
            "birth_year": 1990,
            "birth_month": 3,
            "birth_day": 15,
        }
        validation_errors = [
            {"loc": ["element"], "msg": "필수 필드", "type": "missing"},
        ]

        # Act
        request_id = await logger_instance.log_validation_error(
            fortune_type="western",
            request_input=birth_data,
            raw_response='{"invalid": "data"}',
            error_message="검증 실패",
            validation_errors=validation_errors,
            latency_ms=1200,
        )

        # 플러시 대기
        await asyncio.sleep(0.2)

        # Assert
        today = date.today()
        log_file = temp_log_dir / f"{today.isoformat()}.jsonl"

        with open(log_file, "r", encoding="utf-8") as f:
            log_entry = json.loads(f.readline())
            assert log_entry["validation"]["status"] == "validation_error"
            assert log_entry["validation"]["error_message"] == "검증 실패"
            assert len(log_entry["validation"]["validation_errors"]) == 1

    @pytest.mark.asyncio
    async def test_log_json_parse_error(self, logger_instance, temp_log_dir):
        """JSON 파싱 에러 로깅 테스트"""
        # Arrange
        birth_data = {"birth_year": 1990, "birth_month": 3, "birth_day": 15}

        # Act
        request_id = await logger_instance.log_json_parse_error(
            fortune_type="eastern",
            request_input=birth_data,
            raw_response="invalid json {{{",
            error_message="Expecting property name",
            latency_ms=800,
        )

        # 플러시 대기
        await asyncio.sleep(0.2)

        # Assert
        today = date.today()
        log_file = temp_log_dir / f"{today.isoformat()}.jsonl"

        with open(log_file, "r", encoding="utf-8") as f:
            log_entry = json.loads(f.readline())
            assert log_entry["validation"]["status"] == "json_parse_error"
            assert log_entry["parsed_response"] is None

    @pytest.mark.asyncio
    async def test_log_connection_error(self, logger_instance, temp_log_dir):
        """연결 에러 로깅 테스트"""
        # Arrange
        birth_data = {"birth_year": 1990, "birth_month": 3, "birth_day": 15}

        # Act
        request_id = await logger_instance.log_connection_error(
            fortune_type="eastern",
            request_input=birth_data,
            error_message="Connection refused",
        )

        # 플러시 대기
        await asyncio.sleep(0.2)

        # Assert
        today = date.today()
        log_file = temp_log_dir / f"{today.isoformat()}.jsonl"

        with open(log_file, "r", encoding="utf-8") as f:
            log_entry = json.loads(f.readline())
            assert log_entry["validation"]["status"] == "connection_error"
            assert log_entry["latency_ms"] == 0

    @pytest.mark.asyncio
    async def test_log_timeout_error(self, logger_instance, temp_log_dir):
        """타임아웃 에러 로깅 테스트"""
        # Arrange
        birth_data = {"birth_year": 1990, "birth_month": 3, "birth_day": 15}

        # Act
        request_id = await logger_instance.log_timeout_error(
            fortune_type="western",
            request_input=birth_data,
            error_message="Read timeout",
        )

        # 플러시 대기
        await asyncio.sleep(0.2)

        # Assert
        today = date.today()
        log_file = temp_log_dir / f"{today.isoformat()}.jsonl"

        with open(log_file, "r", encoding="utf-8") as f:
            log_entry = json.loads(f.readline())
            assert log_entry["validation"]["status"] == "timeout_error"

    @pytest.mark.asyncio
    async def test_multiple_logs_batch_flush(self, logger_instance, temp_log_dir):
        """여러 로그 배치 플러시 테스트"""
        # Arrange
        birth_data = {"birth_year": 1990, "birth_month": 3, "birth_day": 15}

        # Act - 여러 로그 기록
        for i in range(5):
            await logger_instance.log_success(
                fortune_type="eastern",
                request_input=birth_data,
                raw_response=f'{{"test": {i}}}',
                parsed_response={"test": i},
                latency_ms=1000 + i * 100,
            )

        # 플러시 대기
        await asyncio.sleep(0.3)

        # Assert
        today = date.today()
        log_file = temp_log_dir / f"{today.isoformat()}.jsonl"

        with open(log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            assert len(lines) == 5


# ============================================================
# 글로벌 인스턴스 테스트
# ============================================================


class TestGlobalLogger:
    """글로벌 로거 인스턴스 테스트"""

    @pytest.mark.asyncio
    async def test_get_response_logger_singleton(self):
        """get_response_logger 싱글톤 테스트"""
        # Act
        logger1 = get_response_logger()
        logger2 = get_response_logger()

        # Assert
        assert logger1 is logger2

    @pytest.mark.asyncio
    async def test_initialize_and_shutdown_response_logger(self):
        """글로벌 로거 초기화/종료 테스트"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Act - 초기화
            logger = await initialize_response_logger(base_dir=Path(tmpdir))

            # Assert
            assert logger is not None
            assert Path(tmpdir).exists()

            # Act - 종료
            await shutdown_response_logger()
