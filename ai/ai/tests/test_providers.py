"""LLM Provider 테스트

Provider 추상 인터페이스 및 구현체 테스트.
실제 서버 연결 없이 단위 테스트 가능.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from yeji_ai.providers import (
    LLMProvider,
    ProviderStatus,
    ProviderHealth,
    GenerationConfig,
    CompletionResponse,
    SSHAdapter,
    SSHConfig,
    VLLMProvider,
    VLLMConfig,
    OllamaProvider,
    OllamaConfig,
    AWSProvider,
    AWSConfig,
)


class TestProviderBase:
    """Provider 기본 타입 테스트"""

    def test_provider_status_values(self):
        """ProviderStatus enum 값 확인"""
        assert ProviderStatus.UNKNOWN == "unknown"
        assert ProviderStatus.STOPPED == "stopped"
        assert ProviderStatus.STARTING == "starting"
        assert ProviderStatus.RUNNING == "running"
        assert ProviderStatus.STOPPING == "stopping"
        assert ProviderStatus.ERROR == "error"

    def test_generation_config_defaults(self):
        """GenerationConfig 기본값 확인"""
        config = GenerationConfig()
        assert config.max_tokens == 1500  # v0.3.2: 토큰 최적화 (2048 → 1500)
        assert config.temperature == 0.7
        assert config.top_p == 0.9
        assert config.stop is None
        assert config.presence_penalty == 0.0
        assert config.frequency_penalty == 0.0

    def test_generation_config_custom(self):
        """GenerationConfig 커스텀 값 확인"""
        config = GenerationConfig(
            max_tokens=1000,
            temperature=0.5,
            response_format={"type": "json_object"},
        )
        assert config.max_tokens == 1000
        assert config.temperature == 0.5
        assert config.response_format == {"type": "json_object"}

    def test_completion_response(self):
        """CompletionResponse 생성 확인"""
        response = CompletionResponse(
            text="Hello, world!",
            finish_reason="stop",
            usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            model="test-model",
            latency_ms=100.5,
        )
        assert response.text == "Hello, world!"
        assert response.finish_reason == "stop"
        assert response.usage["total_tokens"] == 15
        assert response.latency_ms == 100.5

    def test_provider_health(self):
        """ProviderHealth 생성 확인"""
        health = ProviderHealth(
            status=ProviderStatus.RUNNING,
            model="test-model",
            latency_ms=50.0,
            gpu_memory_used=4000.0,
            gpu_memory_total=8000.0,
        )
        assert health.status == ProviderStatus.RUNNING
        assert health.model == "test-model"
        assert health.gpu_memory_used == 4000.0


class TestSSHAdapter:
    """SSHAdapter 테스트"""

    def test_ssh_config_defaults(self):
        """SSHConfig 기본값 확인"""
        config = SSHConfig(host="test-host")
        assert config.host == "test-host"
        assert config.user == "user"
        assert config.port == 22
        assert config.identity_file is None
        assert config.use_wsl is False
        assert config.connect_timeout == 10
        assert config.command_timeout == 60

    def test_ssh_adapter_creation(self):
        """SSHAdapter 생성 확인"""
        config = SSHConfig(
            host="ultra4",
            user="user",
            use_wsl=True,
        )
        adapter = SSHAdapter(config)
        assert adapter.config.host == "ultra4"
        assert adapter.config.use_wsl is True

    def test_ssh_command_build(self):
        """SSH 커맨드 빌드 확인"""
        config = SSHConfig(
            host="192.168.1.1",
            user="ubuntu",
            identity_file="/path/to/key.pem",
        )
        adapter = SSHAdapter(config)
        cmd = adapter._build_ssh_command("echo test")

        assert "ssh" in cmd
        assert "-i" in cmd
        assert "/path/to/key.pem" in cmd
        assert "ubuntu@192.168.1.1" in cmd

    def test_ssh_adapter_repr(self):
        """SSHAdapter repr 확인"""
        config = SSHConfig(host="test-host", user="test-user")
        adapter = SSHAdapter(config)
        repr_str = repr(adapter)
        assert "SSHAdapter" in repr_str
        assert "test-host" in repr_str


class TestVLLMProvider:
    """VLLMProvider 테스트"""

    def test_vllm_config_defaults(self):
        """VLLMConfig 기본값 확인"""
        config = VLLMConfig()
        assert config.base_url == "http://localhost:8001"
        assert config.model == "tellang/yeji-8b-rslora-v7-AWQ"
        assert config.api_timeout == 120.0
        assert config.ssh_config is None

    def test_vllm_provider_creation(self):
        """VLLMProvider 생성 확인"""
        provider = VLLMProvider()
        assert provider.name == "vllm"
        assert provider._ssh_adapter is None

    def test_vllm_provider_with_ssh(self):
        """VLLMProvider SSH 모드 생성 확인"""
        config = VLLMConfig(
            base_url="http://100.114.13.51:8001",
            ssh_config=SSHConfig(host="ultra4", user="user"),
        )
        provider = VLLMProvider(config)
        assert provider._ssh_adapter is not None
        assert provider.config.ssh_config.host == "ultra4"

    def test_vllm_provider_repr(self):
        """VLLMProvider repr 확인"""
        provider = VLLMProvider()
        repr_str = repr(provider)
        assert "VLLMProvider" in repr_str
        assert "Local" in repr_str

    @pytest.mark.anyio
    async def test_vllm_health_connection_refused(self):
        """VLLMProvider 연결 실패 시 헬스체크"""
        config = VLLMConfig(base_url="http://localhost:9999")
        provider = VLLMProvider(config)

        health = await provider.health()
        assert health.status == ProviderStatus.STOPPED
        assert "Connection" in health.error_message or "refused" in health.error_message.lower()

        await provider.close()


class TestOllamaProvider:
    """OllamaProvider 테스트"""

    def test_ollama_config_defaults(self):
        """OllamaConfig 기본값 확인"""
        config = OllamaConfig()
        assert config.base_url == "http://localhost:11434"
        assert config.model == "qwen3:4b"
        assert config.auto_start is True
        assert config.auto_pull is True

    def test_ollama_provider_creation(self):
        """OllamaProvider 생성 확인"""
        provider = OllamaProvider()
        assert provider.name == "ollama"

    def test_ollama_provider_repr(self):
        """OllamaProvider repr 확인"""
        config = OllamaConfig(model="llama3:8b")
        provider = OllamaProvider(config)
        repr_str = repr(provider)
        assert "OllamaProvider" in repr_str
        assert "llama3:8b" in repr_str

    @pytest.mark.anyio
    async def test_ollama_health_connection_refused(self):
        """OllamaProvider 연결 실패 시 헬스체크"""
        config = OllamaConfig(base_url="http://localhost:9999")
        provider = OllamaProvider(config)

        health = await provider.health()
        assert health.status == ProviderStatus.STOPPED

        await provider.close()


class TestAWSProvider:
    """AWSProvider 테스트"""

    def test_aws_config_defaults(self):
        """AWSConfig 기본값 확인"""
        config = AWSConfig()
        assert config.instance_id == ""
        assert config.region == "ap-northeast-2"
        assert config.ssh_user == "ubuntu"
        assert config.local_port == 8001
        assert config.remote_port == 8001

    def test_aws_provider_creation(self):
        """AWSProvider 생성 확인"""
        config = AWSConfig(
            instance_id="i-0123456789",
            ssh_host="3.36.89.31",
            ssh_key_file="~/.ssh/key.pem",
        )
        provider = AWSProvider(config)
        assert provider.name == "aws"
        assert provider._ssh_adapter is not None

    def test_aws_provider_repr(self):
        """AWSProvider repr 확인"""
        config = AWSConfig(instance_id="i-test123")
        provider = AWSProvider(config)
        repr_str = repr(provider)
        assert "AWSProvider" in repr_str
        assert "i-test123" in repr_str

    def test_aws_base_url(self):
        """AWS Provider 로컬 URL 확인"""
        config = AWSConfig(local_port=9001)
        provider = AWSProvider(config)
        assert provider._base_url == "http://localhost:9001"

    @pytest.mark.anyio
    async def test_aws_health_connection_refused(self):
        """AWSProvider 연결 실패 시 헬스체크"""
        config = AWSConfig(local_port=9999)
        provider = AWSProvider(config)

        health = await provider.health()
        assert health.status == ProviderStatus.STOPPED

        await provider.close()


class TestProviderIntegration:
    """Provider 통합 시나리오 테스트"""

    @pytest.mark.anyio
    async def test_provider_lifecycle_mock(self):
        """Provider 라이프사이클 Mock 테스트"""
        provider = VLLMProvider()

        # 초기 상태
        assert provider._current_status == ProviderStatus.UNKNOWN

        # start() 호출 시 STARTING 상태로 변경
        provider._current_status = ProviderStatus.STARTING
        assert provider._current_status == ProviderStatus.STARTING

        # 실제 연결 없이 상태만 확인
        provider._current_status = ProviderStatus.RUNNING

        # stop() 호출 시 STOPPING -> STOPPED
        await provider.stop()
        assert provider._current_status == ProviderStatus.STOPPED

    @pytest.mark.anyio
    async def test_generation_config_json_format(self):
        """JSON 형식 설정 확인"""
        config = GenerationConfig(
            max_tokens=1000,
            temperature=0.5,
            response_format={"type": "json_object"},
            guided_json={"type": "object", "properties": {"name": {"type": "string"}}},
        )

        assert config.response_format["type"] == "json_object"
        assert config.guided_json["type"] == "object"


class TestTemperatureZero:
    """temperature=0 설정 테스트 (P0-1 버그 검증)"""

    def test_generation_config_temperature_zero(self):
        """GenerationConfig에서 temperature=0 설정 가능"""
        config = GenerationConfig(temperature=0, top_p=0, max_tokens=100)

        assert config.temperature == 0
        assert config.top_p == 0
        assert config.max_tokens == 100

    def test_generation_config_none_vs_zero(self):
        """None과 0은 다른 값으로 처리되어야 함"""
        config_zero = GenerationConfig(temperature=0)
        config_default = GenerationConfig()

        # 0은 명시적 설정, 0.7은 기본값
        assert config_zero.temperature == 0
        assert config_default.temperature == 0.7

        # None 체크로 구분 가능
        assert config_zero.temperature is not None
        assert 0 is not None  # 0은 None이 아님

    def test_vllm_config_defaults(self):
        """VLLMConfig 기본값 확인"""
        config = VLLMConfig()

        assert config.default_temperature == 0.7
        assert config.default_top_p == 0.9
        assert config.default_max_tokens == 1500  # v0.3.2: 토큰 최적화


class TestProviderPolymorphism:
    """Provider 다형성 테스트"""

    def test_all_providers_implement_interface(self):
        """모든 Provider가 LLMProvider 인터페이스 구현"""
        providers = [
            VLLMProvider(),
            OllamaProvider(),
            AWSProvider(),
        ]

        for provider in providers:
            # 추상 메서드 존재 확인
            assert hasattr(provider, "start")
            assert hasattr(provider, "stop")
            assert hasattr(provider, "status")
            assert hasattr(provider, "health")
            assert hasattr(provider, "chat")
            assert hasattr(provider, "chat_stream")
            assert hasattr(provider, "name")

            # name 속성 확인
            assert isinstance(provider.name, str)
            assert len(provider.name) > 0

    def test_provider_name_uniqueness(self):
        """각 Provider의 name이 고유함"""
        providers = [
            VLLMProvider(),
            OllamaProvider(),
            AWSProvider(),
        ]

        names = [p.name for p in providers]
        assert len(names) == len(set(names)), "Provider name은 고유해야 함"

    @pytest.mark.anyio
    async def test_aws_provider_stop_signature(self):
        """AWSProvider.stop()이 부모 클래스 시그니처와 일치"""
        provider = AWSProvider()

        # stop()은 인자 없이 호출 가능해야 함
        result = await provider.stop()
        assert isinstance(result, bool)

        # stop_with_instance()는 별도 메서드로 존재
        assert hasattr(provider, "stop_with_instance")

    @pytest.mark.anyio
    async def test_all_providers_stop_without_args(self):
        """모든 Provider의 stop()이 인자 없이 호출 가능"""
        providers = [
            VLLMProvider(),
            OllamaProvider(),
            AWSProvider(),
        ]

        for provider in providers:
            # stop()은 인자 없이 호출 가능해야 함 (부모 클래스 시그니처)
            result = await provider.stop()
            assert isinstance(result, bool), f"{provider.name} stop()은 bool 반환해야 함"
