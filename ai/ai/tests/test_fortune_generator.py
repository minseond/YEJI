"""FortuneGenerator 서비스 테스트

운세 생성 서비스의 초기화, 동양/서양 운세 생성, 에러 처리,
graceful degradation 모드 등을 테스트합니다.

테스트 커버리지 목표: 80% 이상
"""

import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from pydantic import BaseModel

from yeji_ai.models.user_fortune import (
    FortuneResponse,
    SajuDataV2,
    UserFortune,
    WesternFortuneDataV2,
)
from yeji_ai.providers.aws import AWSConfig, AWSProvider
from yeji_ai.providers.base import CompletionResponse
from yeji_ai.services.fortune_generator import (
    FortuneGenerator,
    FortuneGeneratorError,
    LLMErrorType,
    create_fortune_generator,
)

# ============================================================
# 테스트용 모의 데이터
# ============================================================


def get_valid_eastern_data() -> dict[str, Any]:
    """유효한 동양 사주 응답 데이터

    Note:
        - gan_code, ji_code, ten_god_code는 후처리기가 자동 생성합니다.
        - ten_gods.list는 최소 3개 이상의 항목이 필요합니다.
    """
    return {
        "element": "WOOD",
        "chart": {
            "summary": "목(木) 기운이 강한 사주입니다.",
            "year": {"gan": "甲", "ji": "子", "element_code": "WOOD"},
            "month": {"gan": "乙", "ji": "丑", "element_code": "WOOD"},
            "day": {"gan": "丙", "ji": "寅", "element_code": "FIRE"},
            "hour": {"gan": "丁", "ji": "卯", "element_code": "FIRE"},
        },
        "stats": {
            "cheongan_jiji": {
                "summary": "천간지지 요약",
                "year": {"cheon_gan": "甲", "ji_ji": "子"},
                "month": {"cheon_gan": "乙", "ji_ji": "丑"},
                "day": {"cheon_gan": "丙", "ji_ji": "寅"},
                "hour": {"cheon_gan": "丁", "ji_ji": "卯"},
            },
            "five_elements": {
                "summary": "오행 분석 요약",
                "list": [
                    {"code": "WOOD", "label": "목", "percent": 40.0},
                    {"code": "FIRE", "label": "화", "percent": 30.0},
                    {"code": "EARTH", "label": "토", "percent": 10.0},
                    {"code": "METAL", "label": "금", "percent": 10.0},
                    {"code": "WATER", "label": "수", "percent": 10.0},
                ],
            },
            "yin_yang_ratio": {
                "summary": "음양 균형 설명",
                "yin": 40.0,
                "yang": 60.0,
            },
            "ten_gods": {
                "summary": "십신 분석 요약",
                "list": [
                    {"code": "BI_GYEON", "label": "비견", "percent": 25.0},
                    {"code": "GANG_JAE", "label": "겁재", "percent": 25.0},
                    {"code": "SIK_SIN", "label": "식신", "percent": 20.0},
                    {"code": "ETC", "label": "기타", "percent": 30.0},
                ],
            },
        },
        "final_verdict": {
            "summary": "종합 요약",
            "strength": "리더십",
            "weakness": "성급함",
            "advice": "인내심을 기르세요.",
        },
        "lucky": {
            "color": "초록색",
            "number": "3",
            "item": "나무 장식",
            "direction": "동쪽",
            "place": "숲",
        },
    }


def get_valid_western_data() -> dict[str, Any]:
    """유효한 서양 점성술 응답 데이터

    Note:
        - keywords는 최소 3개 이상 필요합니다.
        - detailed_analysis는 정확히 2개 필요합니다.
        - keywords 코드는 WEST_KEYWORD_LABELS에 정의된 것만 유효합니다.
    """
    return {
        "element": "FIRE",
        "stats": {
            "main_sign": {"name": "양자리"},
            "element_summary": "원소 분석 요약",
            "element_4_distribution": [
                {"code": "FIRE", "label": "불", "percent": 50.0},
                {"code": "EARTH", "label": "흙", "percent": 20.0},
                {"code": "AIR", "label": "공기", "percent": 20.0},
                {"code": "WATER", "label": "물", "percent": 10.0},
            ],
            "modality_summary": "양태 분석 요약",
            "modality_3_distribution": [
                {"code": "CARDINAL", "label": "활동궁", "percent": 50.0},
                {"code": "FIXED", "label": "고정궁", "percent": 30.0},
                {"code": "MUTABLE", "label": "변통궁", "percent": 20.0},
            ],
            "keywords_summary": "키워드 분석 요약",
            "keywords": [
                {"code": "LEADERSHIP", "label": "리더십", "weight": 0.8},
                {"code": "PASSION", "label": "열정", "weight": 0.7},
                {"code": "COURAGE", "label": "용기", "weight": 0.6},
            ],
        },
        "fortune_content": {
            "overview": "오늘은 에너지가 넘치는 하루가 될 것입니다.",
            "detailed_analysis": [
                {"title": "사랑운", "content": "새로운 만남이 기대됩니다."},
                {"title": "재물운", "content": "금전적 행운이 따릅니다."},
            ],
            "advice": "열정을 잃지 마세요.",
        },
        "lucky": {
            "color": "빨간색",
            "number": "9",
            "item": "양초",
            "place": "화산",
        },
    }


def get_birth_data_eastern() -> dict[str, Any]:
    """동양 사주 생성용 출생 데이터"""
    return {
        "birth_year": 1990,
        "birth_month": 3,
        "birth_day": 15,
        "birth_hour": 14,
        "gender": "male",
    }


def get_birth_data_western() -> dict[str, Any]:
    """서양 점성술 생성용 출생 데이터"""
    return {
        "birth_year": 1990,
        "birth_month": 3,
        "birth_day": 15,
        "birth_hour": 14,
        "birth_minute": 30,
        "latitude": 37.5665,
        "longitude": 126.9780,
    }


# ============================================================
# FortuneGenerator 초기화 테스트
# ============================================================


class TestFortuneGeneratorInit:
    """FortuneGenerator 초기화 테스트"""

    def test_default_initialization(self) -> None:
        """기본 초기화 테스트"""
        # Arrange & Act
        generator = FortuneGenerator()

        # Assert
        assert generator._provider is None
        assert generator._max_retries == 2
        assert generator._max_tokens == 1500  # v0.3.2: 토큰 최적화
        assert generator._temperature == 0.7
        assert generator._initialized is False

    def test_custom_parameters(self) -> None:
        """사용자 정의 파라미터 테스트"""
        # Arrange
        mock_provider = MagicMock(spec=AWSProvider)

        # Act
        generator = FortuneGenerator(
            provider=mock_provider,
            max_retries=5,
            max_tokens=3000,
            temperature=0.5,
            skip_validation=True,
        )

        # Assert
        assert generator._provider is mock_provider
        assert generator._max_retries == 5
        assert generator._max_tokens == 3000
        assert generator._temperature == 0.5
        assert generator._skip_validation is True

    def test_provider_property_raises_error_when_not_initialized(self) -> None:
        """초기화 전 provider 접근 시 에러 발생 테스트"""
        # Arrange
        generator = FortuneGenerator()

        # Act & Assert
        with pytest.raises(FortuneGeneratorError) as exc_info:
            _ = generator.provider

        assert "초기화되지 않았습니다" in str(exc_info.value)

    @pytest.mark.anyio
    async def test_initialize_creates_default_provider(self) -> None:
        """initialize()가 기본 provider를 생성하는지 테스트"""
        # Arrange
        generator = FortuneGenerator()

        # Act
        with patch("yeji_ai.services.fortune_generator.get_settings") as mock_settings:
            mock_settings.return_value.vllm_model = "test-model"
            mock_settings.return_value.skip_validation = False
            await generator.initialize()

        # Assert
        assert generator._initialized is True
        assert generator._provider is not None
        assert isinstance(generator._provider, AWSProvider)

    @pytest.mark.anyio
    async def test_initialize_uses_injected_provider(self) -> None:
        """주입된 provider를 사용하는지 테스트"""
        # Arrange
        mock_provider = MagicMock(spec=AWSProvider)
        mock_provider.config = AWSConfig(model="injected-model")
        generator = FortuneGenerator(provider=mock_provider)

        # Act
        await generator.initialize()

        # Assert
        assert generator._initialized is True
        assert generator._provider is mock_provider

    @pytest.mark.anyio
    async def test_initialize_idempotent(self) -> None:
        """initialize() 중복 호출 시 안전한지 테스트"""
        # Arrange
        mock_provider = MagicMock(spec=AWSProvider)
        mock_provider.config = AWSConfig(model="test-model")
        generator = FortuneGenerator(provider=mock_provider)

        # Act - 두 번 호출
        await generator.initialize()
        await generator.initialize()

        # Assert - 에러 없이 완료
        assert generator._initialized is True

    @pytest.mark.anyio
    async def test_close_calls_provider_close(self) -> None:
        """close()가 provider.close()를 호출하는지 테스트"""
        # Arrange
        mock_provider = MagicMock(spec=AWSProvider)
        mock_provider.close = AsyncMock()
        generator = FortuneGenerator(provider=mock_provider)

        # Act
        await generator.close()

        # Assert
        mock_provider.close.assert_called_once()


# ============================================================
# generate_eastern 테스트
# ============================================================


class TestGenerateEastern:
    """동양 사주 생성 테스트"""

    @pytest.fixture
    def generator_with_mock_provider(self) -> FortuneGenerator:
        """모의 provider가 주입된 generator 픽스처"""
        mock_provider = MagicMock(spec=AWSProvider)
        mock_provider.chat = AsyncMock()
        generator = FortuneGenerator(provider=mock_provider)
        generator._initialized = True
        return generator

    @pytest.mark.anyio
    async def test_generate_eastern_success(
        self, generator_with_mock_provider: FortuneGenerator
    ) -> None:
        """동양 사주 생성 성공 테스트"""
        # Arrange
        generator = generator_with_mock_provider
        valid_data = get_valid_eastern_data()

        mock_response = MagicMock(spec=CompletionResponse)
        mock_response.text = json.dumps(valid_data)
        mock_response.latency_ms = 100
        generator._provider.chat.return_value = mock_response

        birth_data = get_birth_data_eastern()

        # Act
        result = await generator.generate_eastern(birth_data)

        # Assert
        assert isinstance(result, SajuDataV2)
        # 후처리기가 calculate_four_pillars의 day_stem_element로 element를 덮어씀
        # 1990-03-15 -> 일간 '기'(己) -> EARTH
        assert result.element == "EARTH"
        generator._provider.chat.assert_called_once()

    @pytest.mark.anyio
    async def test_generate_eastern_missing_required_field(
        self, generator_with_mock_provider: FortuneGenerator
    ) -> None:
        """필수 필드 누락 시 에러 테스트"""
        # Arrange
        generator = generator_with_mock_provider
        incomplete_data = {
            "birth_year": 1990,
            "birth_month": 3,
            # birth_day, birth_hour 누락
        }

        # Act & Assert
        with pytest.raises(FortuneGeneratorError) as exc_info:
            await generator.generate_eastern(incomplete_data)

        assert "필수 필드 누락" in str(exc_info.value)

    @pytest.mark.anyio
    async def test_generate_eastern_with_think_tag_removal(
        self, generator_with_mock_provider: FortuneGenerator
    ) -> None:
        """<think> 태그 제거 테스트 (Qwen3 모델)"""
        # Arrange
        generator = generator_with_mock_provider
        valid_data = get_valid_eastern_data()

        # <think> 태그가 포함된 응답
        response_with_think = f"<think>reasoning...</think>{json.dumps(valid_data)}"
        mock_response = MagicMock(spec=CompletionResponse)
        mock_response.text = response_with_think
        mock_response.latency_ms = 100
        generator._provider.chat.return_value = mock_response

        birth_data = get_birth_data_eastern()

        # Act
        result = await generator.generate_eastern(birth_data)

        # Assert
        assert isinstance(result, SajuDataV2)
        # 후처리기가 calculate_four_pillars의 day_stem_element로 element를 덮어씀
        # 1990-03-15 -> 일간 '기'(己) -> EARTH
        assert result.element == "EARTH"

    @pytest.mark.anyio
    async def test_generate_eastern_retries_on_validation_error(
        self, generator_with_mock_provider: FortuneGenerator
    ) -> None:
        """검증 실패 시 재시도 테스트"""
        # Arrange
        generator = generator_with_mock_provider
        generator._max_retries = 2

        # 첫 번째, 두 번째 호출: 잘못된 응답
        # 세 번째 호출: 올바른 응답
        invalid_response = MagicMock(spec=CompletionResponse)
        invalid_response.text = '{"invalid": "data"}'
        invalid_response.latency_ms = 50

        valid_response = MagicMock(spec=CompletionResponse)
        valid_response.text = json.dumps(get_valid_eastern_data())
        valid_response.latency_ms = 100

        generator._provider.chat.side_effect = [
            invalid_response,
            invalid_response,
            valid_response,
        ]

        birth_data = get_birth_data_eastern()

        # Act
        result = await generator.generate_eastern(birth_data)

        # Assert
        assert isinstance(result, SajuDataV2)
        assert generator._provider.chat.call_count == 3


# ============================================================
# generate_western 테스트
# ============================================================


class TestGenerateWestern:
    """서양 점성술 생성 테스트"""

    @pytest.fixture
    def generator_with_mock_provider(self) -> FortuneGenerator:
        """모의 provider가 주입된 generator 픽스처"""
        mock_provider = MagicMock(spec=AWSProvider)
        mock_provider.chat = AsyncMock()
        generator = FortuneGenerator(provider=mock_provider)
        generator._initialized = True
        return generator

    @pytest.mark.anyio
    async def test_generate_western_success(
        self, generator_with_mock_provider: FortuneGenerator
    ) -> None:
        """서양 점성술 생성 성공 테스트"""
        # Arrange
        generator = generator_with_mock_provider
        valid_data = get_valid_western_data()

        mock_response = MagicMock(spec=CompletionResponse)
        mock_response.text = json.dumps(valid_data)
        mock_response.latency_ms = 100
        generator._provider.chat.return_value = mock_response

        birth_data = get_birth_data_western()

        # Act
        result = await generator.generate_western(birth_data)

        # Assert
        assert isinstance(result, WesternFortuneDataV2)
        # 후처리기가 zodiac 기반으로 element 계산 (물고기자리 → WATER)
        assert result.element == "WATER"
        assert result.stats.main_sign.name == "물고기자리"

    @pytest.mark.anyio
    async def test_generate_western_missing_required_field(
        self, generator_with_mock_provider: FortuneGenerator
    ) -> None:
        """필수 필드 누락 시 에러 테스트"""
        # Arrange
        generator = generator_with_mock_provider
        incomplete_data = {
            "birth_year": 1990,
            # birth_month, birth_day 누락
        }

        # Act & Assert
        with pytest.raises(FortuneGeneratorError) as exc_info:
            await generator.generate_western(incomplete_data)

        assert "필수 필드 누락" in str(exc_info.value)

    @pytest.mark.anyio
    async def test_generate_western_with_default_values(
        self, generator_with_mock_provider: FortuneGenerator
    ) -> None:
        """선택적 필드에 기본값 사용 테스트"""
        # Arrange
        generator = generator_with_mock_provider
        valid_data = get_valid_western_data()

        mock_response = MagicMock(spec=CompletionResponse)
        mock_response.text = json.dumps(valid_data)
        mock_response.latency_ms = 100
        generator._provider.chat.return_value = mock_response

        # 필수 필드만 제공 (선택적 필드는 기본값 사용)
        minimal_birth_data = {
            "birth_year": 1990,
            "birth_month": 3,
            "birth_day": 15,
        }

        # Act
        result = await generator.generate_western(minimal_birth_data)

        # Assert
        assert isinstance(result, WesternFortuneDataV2)


# ============================================================
# _call_llm_structured 에러 타입별 테스트
# ============================================================


class TestCallLLMStructuredErrors:
    """_call_llm_structured 메서드 에러 처리 테스트"""

    @pytest.fixture
    def generator_with_mock_provider(self) -> FortuneGenerator:
        """모의 provider가 주입된 generator 픽스처"""
        mock_provider = MagicMock(spec=AWSProvider)
        mock_provider.chat = AsyncMock()
        generator = FortuneGenerator(provider=mock_provider)
        generator._initialized = True
        generator._max_retries = 0  # 재시도 비활성화
        return generator

    @pytest.mark.anyio
    async def test_connection_error_raises_fortune_generator_error(
        self, generator_with_mock_provider: FortuneGenerator
    ) -> None:
        """연결 에러 분류 테스트"""
        # Arrange
        generator = generator_with_mock_provider
        generator._provider.chat.side_effect = httpx.ConnectError("Connection refused")

        class TestSchema(BaseModel):
            value: str

        # Act & Assert
        with pytest.raises(FortuneGeneratorError) as exc_info:
            await generator._call_llm_structured(
                system_prompt="test",
                user_prompt="test",
                response_schema=TestSchema,
            )

        assert exc_info.value.error_type == LLMErrorType.CONNECTION
        assert exc_info.value.error_code == "LLM_CONNECTION_FAILED"

    @pytest.mark.anyio
    async def test_timeout_error_raises_fortune_generator_error(
        self, generator_with_mock_provider: FortuneGenerator
    ) -> None:
        """타임아웃 에러 분류 테스트"""
        # Arrange
        generator = generator_with_mock_provider
        generator._provider.chat.side_effect = httpx.TimeoutException("Read timeout")

        class TestSchema(BaseModel):
            value: str

        # Act & Assert
        with pytest.raises(FortuneGeneratorError) as exc_info:
            await generator._call_llm_structured(
                system_prompt="test",
                user_prompt="test",
                response_schema=TestSchema,
            )

        assert exc_info.value.error_type == LLMErrorType.TIMEOUT
        assert exc_info.value.error_code == "LLM_TIMEOUT"

    @pytest.mark.anyio
    async def test_validation_error_includes_raw_content(
        self, generator_with_mock_provider: FortuneGenerator
    ) -> None:
        """검증 에러 시 원본 응답 포함 테스트"""
        # Arrange
        generator = generator_with_mock_provider

        # 스키마와 일치하지 않는 응답
        invalid_json = '{"wrong_field": "value"}'
        mock_response = MagicMock(spec=CompletionResponse)
        mock_response.text = invalid_json
        mock_response.latency_ms = 100
        generator._provider.chat.return_value = mock_response

        class TestSchema(BaseModel):
            required_field: str

        # Act & Assert
        with pytest.raises(FortuneGeneratorError) as exc_info:
            await generator._call_llm_structured(
                system_prompt="test",
                user_prompt="test",
                response_schema=TestSchema,
            )

        assert exc_info.value.error_type == LLMErrorType.VALIDATION
        assert exc_info.value.error_code == "LLM_VALIDATION_FAILED"
        assert exc_info.value.raw_content == invalid_json
        assert "validation_errors" in exc_info.value.details

    @pytest.mark.anyio
    async def test_http_status_error_classified_as_connection(
        self, generator_with_mock_provider: FortuneGenerator
    ) -> None:
        """HTTPStatusError가 CONNECTION 타입으로 분류되는지 테스트"""
        # Arrange
        generator = generator_with_mock_provider

        # 500 에러 응답 모의
        mock_request = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 500
        generator._provider.chat.side_effect = httpx.HTTPStatusError(
            "Internal Server Error",
            request=mock_request,
            response=mock_response,
        )

        class TestSchema(BaseModel):
            value: str

        # Act & Assert
        with pytest.raises(FortuneGeneratorError) as exc_info:
            await generator._call_llm_structured(
                system_prompt="test",
                user_prompt="test",
                response_schema=TestSchema,
            )

        assert exc_info.value.error_type == LLMErrorType.CONNECTION

    @pytest.mark.anyio
    async def test_unknown_error_type(self, generator_with_mock_provider: FortuneGenerator) -> None:
        """분류되지 않은 에러 타입 테스트"""
        # Arrange
        generator = generator_with_mock_provider
        generator._provider.chat.side_effect = RuntimeError("Unknown error")

        class TestSchema(BaseModel):
            value: str

        # Act & Assert
        with pytest.raises(FortuneGeneratorError) as exc_info:
            await generator._call_llm_structured(
                system_prompt="test",
                user_prompt="test",
                response_schema=TestSchema,
            )

        assert exc_info.value.error_type == LLMErrorType.UNKNOWN
        assert exc_info.value.error_code == "LLM_UNKNOWN_ERROR"

    @pytest.mark.anyio
    async def test_temperature_increases_on_retry(
        self, generator_with_mock_provider: FortuneGenerator
    ) -> None:
        """재시도 시 온도가 증가하는지 테스트"""
        # Arrange
        generator = generator_with_mock_provider
        generator._max_retries = 2
        generator._temperature = 0.7

        valid_data = {"value": "test"}
        mock_response = MagicMock(spec=CompletionResponse)
        mock_response.text = json.dumps(valid_data)
        mock_response.latency_ms = 100

        # 첫 두 번은 실패, 세 번째 성공
        invalid_response = MagicMock(spec=CompletionResponse)
        invalid_response.text = '{"wrong": "data"}'
        invalid_response.latency_ms = 50

        call_configs: list[Any] = []

        async def capture_config(messages: Any, config: Any) -> MagicMock:
            call_configs.append(config.temperature)
            if len(call_configs) < 3:
                return invalid_response
            return mock_response

        generator._provider.chat.side_effect = capture_config

        class TestSchema(BaseModel):
            value: str

        # Act
        await generator._call_llm_structured(
            system_prompt="test",
            user_prompt="test",
            response_schema=TestSchema,
        )

        # Assert - 온도가 점진적으로 증가 (부동소수점 비교를 위해 approx 사용)
        assert call_configs[0] == pytest.approx(0.7)  # 첫 번째 시도
        assert call_configs[1] == pytest.approx(0.8)  # 두 번째 시도 (0.7 + 0.1)
        assert call_configs[2] == pytest.approx(0.9)  # 세 번째 시도 (0.7 + 0.2)


# ============================================================
# Graceful Degradation 모드 테스트
# ============================================================


class TestGracefulDegradation:
    """Graceful Degradation 모드 테스트"""

    @pytest.fixture
    def generator_with_mock_provider(self) -> FortuneGenerator:
        """모의 provider가 주입된 generator 픽스처"""
        mock_provider = MagicMock(spec=AWSProvider)
        mock_provider.chat = AsyncMock()
        generator = FortuneGenerator(provider=mock_provider)
        generator._initialized = True
        return generator

    @pytest.mark.anyio
    async def test_generate_eastern_graceful_success_validated(
        self, generator_with_mock_provider: FortuneGenerator
    ) -> None:
        """graceful 모드 - 검증 성공 테스트"""
        # Arrange
        generator = generator_with_mock_provider
        valid_data = get_valid_eastern_data()

        mock_response = MagicMock(spec=CompletionResponse)
        mock_response.text = json.dumps(valid_data)
        mock_response.latency_ms = 100
        generator._provider.chat.return_value = mock_response

        birth_data = get_birth_data_eastern()

        # Act
        result = await generator.generate_eastern_graceful(birth_data)

        # Assert
        assert isinstance(result, FortuneResponse)
        assert result.success is True
        assert result.validated is True
        assert result.type == "eastern"
        assert result.errors is None
        assert result.latency_ms == 100

    @pytest.mark.anyio
    async def test_generate_eastern_graceful_validation_failed(
        self, generator_with_mock_provider: FortuneGenerator
    ) -> None:
        """graceful 모드 - 검증 실패 시 후처리된 데이터 반환 테스트"""
        # Arrange
        generator = generator_with_mock_provider

        # 유효하지 않은 응답 (필수 필드 누락)
        invalid_data = {"element": "INVALID_ELEMENT", "partial": "data"}
        mock_response = MagicMock(spec=CompletionResponse)
        mock_response.text = json.dumps(invalid_data)
        mock_response.latency_ms = 100
        generator._provider.chat.return_value = mock_response

        birth_data = get_birth_data_eastern()

        # Act
        result = await generator.generate_eastern_graceful(birth_data)

        # Assert
        assert isinstance(result, FortuneResponse)
        assert result.success is True  # LLM 호출은 성공
        assert result.validated is False  # 검증은 실패
        assert result.type == "eastern"
        # 후처리기가 calculated_saju의 day_stem_element로 element를 덮어씀
        # 1990-03-15 -> 일간 '기'(己) -> EARTH
        assert result.data["element"] == "EARTH"
        assert result.data["partial"] == "data"  # 원본 필드 유지
        assert result.errors is not None
        assert len(result.errors) > 0

    @pytest.mark.anyio
    async def test_generate_eastern_graceful_json_parse_failed(
        self, generator_with_mock_provider: FortuneGenerator
    ) -> None:
        """graceful 모드 - JSON 파싱 실패 테스트"""
        # Arrange
        generator = generator_with_mock_provider

        # 잘못된 JSON
        mock_response = MagicMock(spec=CompletionResponse)
        mock_response.text = "This is not JSON"
        mock_response.latency_ms = 100
        generator._provider.chat.return_value = mock_response

        birth_data = get_birth_data_eastern()

        # Act
        result = await generator.generate_eastern_graceful(birth_data)

        # Assert
        assert result.success is True
        assert result.validated is False
        assert "JSON 파싱 실패" in result.errors[0]
        assert result.data["raw_content"] == "This is not JSON"

    @pytest.mark.anyio
    async def test_generate_eastern_graceful_missing_required_field(
        self, generator_with_mock_provider: FortuneGenerator
    ) -> None:
        """graceful 모드 - 필수 필드 누락 테스트"""
        # Arrange
        generator = generator_with_mock_provider
        incomplete_data = {"birth_year": 1990}  # 필수 필드 누락

        # Act
        result = await generator.generate_eastern_graceful(incomplete_data)

        # Assert
        assert result.success is False
        assert result.validated is False
        assert "필수 필드 누락" in result.errors[0]

    @pytest.mark.anyio
    async def test_generate_eastern_graceful_llm_error(
        self, generator_with_mock_provider: FortuneGenerator
    ) -> None:
        """graceful 모드 - LLM 호출 에러 테스트"""
        # Arrange
        generator = generator_with_mock_provider
        generator._provider.chat.side_effect = httpx.ConnectError("Connection refused")

        birth_data = get_birth_data_eastern()

        # Act
        result = await generator.generate_eastern_graceful(birth_data)

        # Assert
        assert result.success is False
        assert result.validated is False
        # 연결 에러는 "LLM 연결 실패"로 구분됨 (로깅 시스템 도입 후)
        assert "LLM 연결 실패" in result.errors[0] or "LLM 호출 실패" in result.errors[0]
        assert result.latency_ms == 0

    @pytest.mark.anyio
    async def test_generate_western_graceful_success_validated(
        self, generator_with_mock_provider: FortuneGenerator
    ) -> None:
        """서양 운세 graceful 모드 - 검증 성공 테스트"""
        # Arrange
        generator = generator_with_mock_provider
        valid_data = get_valid_western_data()

        mock_response = MagicMock(spec=CompletionResponse)
        mock_response.text = json.dumps(valid_data)
        mock_response.latency_ms = 150
        generator._provider.chat.return_value = mock_response

        birth_data = get_birth_data_western()

        # Act
        result = await generator.generate_western_graceful(birth_data)

        # Assert
        assert isinstance(result, FortuneResponse)
        assert result.success is True
        assert result.validated is True
        assert result.type == "western"
        assert result.errors is None
        assert result.latency_ms == 150

    @pytest.mark.anyio
    async def test_generate_western_graceful_validation_failed(
        self, generator_with_mock_provider: FortuneGenerator
    ) -> None:
        """서양 운세 graceful 모드 - 검증 실패 시 후처리된 데이터 반환 테스트"""
        # Arrange
        generator = generator_with_mock_provider

        # 유효하지 않은 응답
        invalid_data = {"element": "INVALID", "partial": "data"}
        mock_response = MagicMock(spec=CompletionResponse)
        mock_response.text = json.dumps(invalid_data)
        mock_response.latency_ms = 100
        generator._provider.chat.return_value = mock_response

        birth_data = get_birth_data_western()

        # Act
        result = await generator.generate_western_graceful(birth_data)

        # Assert
        assert result.success is True
        assert result.validated is False
        assert result.type == "western"
        # 서양 운세도 후처리기가 zodiac 기반으로 element 계산
        assert result.data["element"] == "WATER"  # 후처리기가 계산값으로 덮어씀
        assert result.data["partial"] == "data"  # 원본 필드 유지
        assert result.errors is not None

    @pytest.mark.anyio
    async def test_generate_western_graceful_missing_required_field(
        self, generator_with_mock_provider: FortuneGenerator
    ) -> None:
        """서양 운세 graceful 모드 - 필수 필드 누락 테스트"""
        # Arrange
        generator = generator_with_mock_provider
        incomplete_data = {"birth_year": 1990}  # birth_month, birth_day 누락

        # Act
        result = await generator.generate_western_graceful(incomplete_data)

        # Assert
        assert result.success is False
        assert result.validated is False
        assert "필수 필드 누락" in result.errors[0]

    @pytest.mark.anyio
    async def test_generate_western_graceful_with_think_tag(
        self, generator_with_mock_provider: FortuneGenerator
    ) -> None:
        """서양 운세 graceful 모드 - <think> 태그 제거 테스트"""
        # Arrange
        generator = generator_with_mock_provider
        valid_data = get_valid_western_data()

        response_with_think = f"<think>reasoning...</think>{json.dumps(valid_data)}"
        mock_response = MagicMock(spec=CompletionResponse)
        mock_response.text = response_with_think
        mock_response.latency_ms = 100
        generator._provider.chat.return_value = mock_response

        birth_data = get_birth_data_western()

        # Act
        result = await generator.generate_western_graceful(birth_data)

        # Assert
        assert result.validated is True


# ============================================================
# generate_full 테스트
# ============================================================


class TestGenerateFull:
    """전체 운세 생성 테스트"""

    @pytest.fixture
    def generator_with_mock_provider(self) -> FortuneGenerator:
        """모의 provider가 주입된 generator 픽스처"""
        mock_provider = MagicMock(spec=AWSProvider)
        mock_provider.chat = AsyncMock()
        generator = FortuneGenerator(provider=mock_provider)
        generator._initialized = True
        return generator

    @pytest.mark.anyio
    async def test_generate_full_success(
        self, generator_with_mock_provider: FortuneGenerator
    ) -> None:
        """전체 운세 생성 성공 테스트"""
        # Arrange
        generator = generator_with_mock_provider

        eastern_data = get_valid_eastern_data()
        western_data = get_valid_western_data()

        # 첫 번째 호출: 동양 사주, 두 번째 호출: 서양 점성술
        mock_eastern_response = MagicMock(spec=CompletionResponse)
        mock_eastern_response.text = json.dumps(eastern_data)
        mock_eastern_response.latency_ms = 100

        mock_western_response = MagicMock(spec=CompletionResponse)
        mock_western_response.text = json.dumps(western_data)
        mock_western_response.latency_ms = 150

        generator._provider.chat.side_effect = [
            mock_eastern_response,
            mock_western_response,
        ]

        birth_data = {
            "birth_year": 1990,
            "birth_month": 3,
            "birth_day": 15,
            "birth_hour": 14,
            "gender": "male",
        }

        # Act
        result = await generator.generate_full(birth_data)

        # Assert
        assert isinstance(result, UserFortune)
        assert isinstance(result.eastern, SajuDataV2)
        assert isinstance(result.western, WesternFortuneDataV2)
        # 후처리기가 calculate_four_pillars의 day_stem_element로 element를 덮어씀
        # 1990-03-15 -> 일간 '기'(己) -> EARTH
        assert result.eastern.element == "EARTH"
        assert result.western.element == "WATER"  # 후처리기가 zodiac 기반으로 계산

    @pytest.mark.anyio
    async def test_generate_full_missing_required_field(
        self, generator_with_mock_provider: FortuneGenerator
    ) -> None:
        """전체 운세 생성 - 필수 필드 누락 테스트"""
        # Arrange
        generator = generator_with_mock_provider
        incomplete_data = {
            "birth_year": 1990,
            "birth_month": 3,
            # birth_day, birth_hour 누락
        }

        # Act & Assert
        with pytest.raises(FortuneGeneratorError) as exc_info:
            await generator.generate_full(incomplete_data)

        assert "필수 필드 누락" in str(exc_info.value)


# ============================================================
# Raw 모드 테스트
# ============================================================


class TestRawMode:
    """Raw 모드 (검증 스킵) 테스트"""

    @pytest.fixture
    def generator_with_mock_provider(self) -> FortuneGenerator:
        """모의 provider가 주입된 generator 픽스처"""
        mock_provider = MagicMock(spec=AWSProvider)
        mock_provider.chat = AsyncMock()
        generator = FortuneGenerator(provider=mock_provider)
        generator._initialized = True
        return generator

    @pytest.mark.anyio
    async def test_generate_eastern_raw_success(
        self, generator_with_mock_provider: FortuneGenerator
    ) -> None:
        """동양 사주 raw 모드 성공 테스트"""
        # Arrange
        generator = generator_with_mock_provider
        raw_data = {"some": "data", "element": "WOOD"}

        mock_response = MagicMock(spec=CompletionResponse)
        mock_response.text = json.dumps(raw_data)
        mock_response.latency_ms = 100
        generator._provider.chat.return_value = mock_response

        birth_data = get_birth_data_eastern()

        # Act
        result = await generator.generate_eastern_raw(birth_data)

        # Assert
        assert result["success"] is True
        assert result["data"] == raw_data
        assert result["latency_ms"] == 100

    @pytest.mark.anyio
    async def test_generate_eastern_raw_missing_field(
        self, generator_with_mock_provider: FortuneGenerator
    ) -> None:
        """동양 사주 raw 모드 - 필수 필드 누락 테스트"""
        # Arrange
        generator = generator_with_mock_provider
        incomplete_data = {"birth_year": 1990}  # 필수 필드 누락

        # Act
        result = await generator.generate_eastern_raw(incomplete_data)

        # Assert
        assert result["success"] is False
        assert "필수 필드 누락" in result["error"]

    @pytest.mark.anyio
    async def test_generate_western_raw_success(
        self, generator_with_mock_provider: FortuneGenerator
    ) -> None:
        """서양 점성술 raw 모드 성공 테스트"""
        # Arrange
        generator = generator_with_mock_provider
        raw_data = {"some": "western_data", "element": "FIRE"}

        mock_response = MagicMock(spec=CompletionResponse)
        mock_response.text = json.dumps(raw_data)
        mock_response.latency_ms = 100
        generator._provider.chat.return_value = mock_response

        birth_data = get_birth_data_western()

        # Act
        result = await generator.generate_western_raw(birth_data)

        # Assert
        assert result["success"] is True
        assert result["data"] == raw_data

    @pytest.mark.anyio
    async def test_generate_western_raw_missing_field(
        self, generator_with_mock_provider: FortuneGenerator
    ) -> None:
        """서양 점성술 raw 모드 - 필수 필드 누락 테스트"""
        # Arrange
        generator = generator_with_mock_provider
        incomplete_data = {"birth_year": 1990}  # 필수 필드 누락

        # Act
        result = await generator.generate_western_raw(incomplete_data)

        # Assert
        assert result["success"] is False
        assert "필수 필드 누락" in result["error"]

    @pytest.mark.anyio
    async def test_call_llm_raw_json_parse_error(
        self, generator_with_mock_provider: FortuneGenerator
    ) -> None:
        """_call_llm_raw JSON 파싱 실패 테스트"""
        # Arrange
        generator = generator_with_mock_provider

        mock_response = MagicMock(spec=CompletionResponse)
        mock_response.text = "Not valid JSON"
        mock_response.latency_ms = 100
        generator._provider.chat.return_value = mock_response

        # Act
        result = await generator._call_llm_raw(
            system_prompt="test",
            user_prompt="test",
        )

        # Assert
        assert result["success"] is False
        assert "JSON 파싱 실패" in result["error"]
        assert result["raw_content"] == "Not valid JSON"

    @pytest.mark.anyio
    async def test_call_llm_raw_exception(
        self, generator_with_mock_provider: FortuneGenerator
    ) -> None:
        """_call_llm_raw 예외 발생 테스트"""
        # Arrange
        generator = generator_with_mock_provider
        generator._provider.chat.side_effect = Exception("Unexpected error")

        # Act
        result = await generator._call_llm_raw(
            system_prompt="test",
            user_prompt="test",
        )

        # Assert
        assert result["success"] is False
        assert "Unexpected error" in result["error"]
        assert result["raw_content"] is None


# ============================================================
# 팩토리 함수 테스트
# ============================================================


class TestCreateFortuneGenerator:
    """create_fortune_generator 팩토리 함수 테스트"""

    @pytest.mark.anyio
    async def test_create_fortune_generator_with_provider(self) -> None:
        """provider 주입 시 초기화된 generator 반환 테스트"""
        # Arrange
        mock_provider = MagicMock(spec=AWSProvider)
        mock_provider.config = AWSConfig(model="test-model")

        # Act
        generator = await create_fortune_generator(provider=mock_provider)

        # Assert
        assert generator._initialized is True
        assert generator._provider is mock_provider

    @pytest.mark.anyio
    async def test_create_fortune_generator_default(self) -> None:
        """기본 설정으로 generator 생성 테스트"""
        # Act
        with patch("yeji_ai.services.fortune_generator.get_settings") as mock_settings:
            mock_settings.return_value.vllm_model = "default-model"
            mock_settings.return_value.skip_validation = False
            generator = await create_fortune_generator()

        # Assert
        assert generator._initialized is True
        assert generator._provider is not None


# ============================================================
# 사주 계산 헬퍼 함수 테스트
# ============================================================


class TestCalculateFourPillars:
    """calculate_four_pillars 사주 계산 함수 테스트"""

    def test_calculate_four_pillars_1992_04_05(self) -> None:
        """1992년 4월 5일 12시 사주 계산 - 일간 신(辛, 금) 검증"""
        from yeji_ai.services.fortune_generator import calculate_four_pillars

        # Act
        result = calculate_four_pillars(1992, 4, 5, 12)

        # Assert - 일주 검증
        assert result["day_pillar"] == "신미", f"일주가 신미가 아님: {result['day_pillar']}"
        assert result["day_pillar_hanja"] == "辛未", f"일주 한자가 辛未가 아님: {result['day_pillar_hanja']}"

        # Assert - 일간 검증
        assert result["day_stem"] == "신", f"일간이 신이 아님: {result['day_stem']}"
        assert result["day_stem_element"] == "금", f"일간 오행이 금이 아님: {result['day_stem_element']}"

    def test_calculate_four_pillars_returns_all_fields(self) -> None:
        """사주 계산 결과에 모든 필수 필드가 포함되어 있는지 검증"""
        from yeji_ai.services.fortune_generator import calculate_four_pillars

        # Act
        result = calculate_four_pillars(1990, 1, 1, 0)

        # Assert - 필수 필드 존재 확인
        required_fields = [
            "year_pillar", "month_pillar", "day_pillar", "hour_pillar",
            "year_pillar_hanja", "month_pillar_hanja", "day_pillar_hanja", "hour_pillar_hanja",
            "day_stem", "day_stem_element",
        ]
        for field in required_fields:
            assert field in result, f"필수 필드 누락: {field}"

    def test_calculate_four_pillars_hanja_format(self) -> None:
        """한자 변환이 올바른 형식인지 검증"""
        from yeji_ai.services.fortune_generator import calculate_four_pillars

        # 유효한 천간/지지 한자 목록
        valid_stems_hanja = {"甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"}
        valid_branches_hanja = {"子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"}

        # Act
        result = calculate_four_pillars(2000, 6, 15, 14)

        # Assert - 한자 형식 검증
        for pillar_key in ["year_pillar_hanja", "month_pillar_hanja", "day_pillar_hanja"]:
            pillar = result[pillar_key]
            assert len(pillar) == 2, f"{pillar_key}는 2글자여야 함: {pillar}"
            assert pillar[0] in valid_stems_hanja, f"유효하지 않은 천간 한자: {pillar[0]}"
            assert pillar[1] in valid_branches_hanja, f"유효하지 않은 지지 한자: {pillar[1]}"

    def test_calculate_four_pillars_day_stem_element_mapping(self) -> None:
        """일간과 오행 매핑이 올바른지 검증"""
        from yeji_ai.services.fortune_generator import calculate_four_pillars

        # 천간 → 오행 매핑
        expected_mapping = {
            "갑": "목", "을": "목",
            "병": "화", "정": "화",
            "무": "토", "기": "토",
            "경": "금", "신": "금",
            "임": "수", "계": "수",
        }

        # 다양한 날짜로 테스트
        test_dates = [
            (1990, 1, 1, 12),
            (1995, 6, 15, 8),
            (2000, 12, 31, 23),
            (2010, 3, 20, 6),
        ]

        for year, month, day, hour in test_dates:
            result = calculate_four_pillars(year, month, day, hour)
            day_stem = result["day_stem"]
            day_element = result["day_stem_element"]

            assert day_stem in expected_mapping, f"유효하지 않은 일간: {day_stem}"
            assert day_element == expected_mapping[day_stem], (
                f"일간 {day_stem}의 오행이 {expected_mapping[day_stem]}이어야 하나 {day_element}임"
            )

    def test_calculate_four_pillars_hour_pillar_calculation(self) -> None:
        """시주 계산이 올바른지 검증 (시간에 따른 지지 변화)"""
        from yeji_ai.services.fortune_generator import calculate_four_pillars

        # 같은 날짜, 다른 시간으로 시주 지지가 달라지는지 확인
        result_0h = calculate_four_pillars(2000, 1, 1, 0)  # 자시
        result_12h = calculate_four_pillars(2000, 1, 1, 12)  # 오시

        # 시주의 지지(두 번째 글자)가 달라야 함
        hour_branch_0h = result_0h["hour_pillar"][1] if result_0h["hour_pillar"] else None
        hour_branch_12h = result_12h["hour_pillar"][1] if result_12h["hour_pillar"] else None

        assert hour_branch_0h != hour_branch_12h, (
            f"0시와 12시의 시주 지지가 같음: {hour_branch_0h}"
        )


class TestBuildEasternGenerationPrompt:
    """build_eastern_generation_prompt 프롬프트 빌더 함수 테스트"""

    def test_prompt_includes_calculated_saju(self) -> None:
        """calculated_saju 전달 시 프롬프트에 사주 정보가 포함되는지 검증"""
        from yeji_ai.prompts.fortune_prompts import build_eastern_generation_prompt
        from yeji_ai.services.fortune_generator import calculate_four_pillars

        # Arrange
        calculated_saju = calculate_four_pillars(1992, 4, 5, 12)

        # Act
        prompt = build_eastern_generation_prompt(
            birth_year=1992,
            birth_month=4,
            birth_day=5,
            birth_hour=12,
            gender="male",
            calculated_saju=calculated_saju,
        )

        # Assert - 프롬프트에 계산된 사주 정보가 포함되어야 함
        assert "서버에서 계산된 사주팔자" in prompt
        assert "辛未" in prompt, "일주 한자(辛未)가 프롬프트에 없음"
        assert "신미" in prompt, "일주 한글(신미)이 프롬프트에 없음"
        assert "신 (금 오행)" in prompt, "일간 정보가 프롬프트에 없음"
        assert "절대로 직접 사주를 계산하지 마세요" in prompt

    def test_prompt_without_calculated_saju(self) -> None:
        """calculated_saju 미전달 시 기존 방식 프롬프트 생성 검증"""
        from yeji_ai.prompts.fortune_prompts import build_eastern_generation_prompt

        # Act
        prompt = build_eastern_generation_prompt(
            birth_year=1992,
            birth_month=4,
            birth_day=5,
            birth_hour=12,
            gender="male",
            calculated_saju=None,
        )

        # Assert - 서버 계산 사주가 아닌 LLM 계산 지시가 있어야 함
        assert "서버에서 계산된 사주팔자" not in prompt
        assert "위 생년월일시를 기반으로 사주팔자" in prompt

    def test_prompt_includes_all_pillars(self) -> None:
        """프롬프트에 연주, 월주, 일주, 시주 모두 포함되는지 검증"""
        from yeji_ai.prompts.fortune_prompts import build_eastern_generation_prompt
        from yeji_ai.services.fortune_generator import calculate_four_pillars

        # Arrange
        calculated_saju = calculate_four_pillars(2000, 6, 15, 14)

        # Act
        prompt = build_eastern_generation_prompt(
            birth_year=2000,
            birth_month=6,
            birth_day=15,
            birth_hour=14,
            calculated_saju=calculated_saju,
        )

        # Assert
        assert "연주(年柱):" in prompt
        assert "월주(月柱):" in prompt
        assert "일주(日柱):" in prompt
        assert "시주(時柱):" in prompt
        assert calculated_saju["year_pillar_hanja"] in prompt
        assert calculated_saju["month_pillar_hanja"] in prompt
        assert calculated_saju["day_pillar_hanja"] in prompt
        if calculated_saju["hour_pillar_hanja"]:
            assert calculated_saju["hour_pillar_hanja"] in prompt
