"""LLM Provider 어댑터 - 모델 API 변경 용이성을 위한 추상화

다양한 LLM Provider(OpenAI, vLLM, Ollama 등)를 동일한 인터페이스로 사용할 수 있게 함.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any

import structlog

logger = structlog.get_logger()


class LLMProviderType(Enum):
    """지원하는 LLM Provider 타입"""

    OPENAI = "openai"  # OpenAI API (GPT-5-mini 등)
    VLLM = "vllm"  # 로컬 vLLM 서버
    OLLAMA = "ollama"  # Ollama
    AWS_BEDROCK = "bedrock"  # AWS Bedrock


@dataclass
class LLMResponse:
    """LLM 응답 표준화"""

    text: str
    model: str | None = None
    usage: dict[str, Any] | None = None
    latency_ms: float | None = None
    provider: str | None = None


class BaseLLMAdapter(ABC):
    """LLM Adapter 추상 기본 클래스

    모든 LLM Provider는 이 인터페이스를 구현해야 함.
    """

    @property
    @abstractmethod
    def provider_type(self) -> LLMProviderType:
        """Provider 타입 반환"""
        pass

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Provider 사용 가능 여부"""
        pass

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        **kwargs,
    ) -> LLMResponse:
        """텍스트 생성

        Args:
            prompt: 사용자 프롬프트
            system_prompt: 시스템 프롬프트 (옵션)
            **kwargs: Provider별 추가 옵션

        Returns:
            표준화된 LLM 응답
        """
        pass

    @abstractmethod
    async def chat(
        self,
        messages: list[dict[str, str]],
        **kwargs,
    ) -> LLMResponse:
        """채팅 완성

        Args:
            messages: [{"role": "...", "content": "..."}] 형식
            **kwargs: Provider별 추가 옵션

        Returns:
            표준화된 LLM 응답
        """
        pass

    @abstractmethod
    async def start(self) -> bool:
        """Provider 시작/연결"""
        pass

    @abstractmethod
    async def stop(self) -> bool:
        """Provider 종료"""
        pass


class OpenAIAdapter(BaseLLMAdapter):
    """OpenAI API 어댑터 (GPT-5-mini 등)"""

    def __init__(self, model: str = "gpt-5-mini", **config):
        from yeji_ai.providers.openai import OpenAIConfig, OpenAIProvider

        self._config = OpenAIConfig(model=model, **config)
        self._provider = OpenAIProvider(self._config)
        self._started = False

    @property
    def provider_type(self) -> LLMProviderType:
        return LLMProviderType.OPENAI

    @property
    def is_available(self) -> bool:
        return self._started

    async def start(self) -> bool:
        result = await self._provider.start()
        self._started = result
        return result

    async def stop(self) -> bool:
        result = await self._provider.stop()
        self._started = False
        return result

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        **kwargs,
    ) -> LLMResponse:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        return await self.chat(messages, **kwargs)

    async def chat(
        self,
        messages: list[dict[str, str]],
        **kwargs,
    ) -> LLMResponse:
        response = await self._provider.chat(messages)
        return LLMResponse(
            text=response.text,
            model=response.model,
            usage=response.usage,
            latency_ms=response.latency_ms,
            provider="openai",
        )


class VLLMAdapter(BaseLLMAdapter):
    """vLLM 로컬 서버 어댑터"""

    def __init__(self, base_url: str = "http://localhost:8001", model: str = "yeji-8b", **config):
        from yeji_ai.providers.vllm import VLLMConfig, VLLMProvider

        self._config = VLLMConfig(vllm_base_url=base_url, vllm_model=model, **config)
        self._provider = VLLMProvider(self._config)
        self._started = False

    @property
    def provider_type(self) -> LLMProviderType:
        return LLMProviderType.VLLM

    @property
    def is_available(self) -> bool:
        return self._started

    async def start(self) -> bool:
        result = await self._provider.start()
        self._started = result
        return result

    async def stop(self) -> bool:
        result = await self._provider.stop()
        self._started = False
        return result

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        **kwargs,
    ) -> LLMResponse:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        return await self.chat(messages, **kwargs)

    async def chat(
        self,
        messages: list[dict[str, str]],
        **kwargs,
    ) -> LLMResponse:
        response = await self._provider.chat(messages)
        return LLMResponse(
            text=response.text,
            model=response.model,
            usage=response.usage,
            latency_ms=response.latency_ms,
            provider="vllm",
        )


class LLMAdapterFactory:
    """LLM 어댑터 팩토리

    Provider 타입에 따라 적절한 어댑터를 생성합니다.

    Usage:
        # GPT-5-mini 어댑터
        adapter = LLMAdapterFactory.create("openai", model="gpt-5-mini")

        # vLLM 어댑터
        adapter = LLMAdapterFactory.create("vllm", base_url="http://localhost:8001")

        # 시작 및 사용
        await adapter.start()
        response = await adapter.generate("안녕하세요", system_prompt="운세 전문가입니다.")
        await adapter.stop()
    """

    _adapters: dict[str, type[BaseLLMAdapter]] = {
        "openai": OpenAIAdapter,
        "gpt": OpenAIAdapter,  # alias
        "gpt-5-mini": OpenAIAdapter,  # alias
        "vllm": VLLMAdapter,
        "local": VLLMAdapter,  # alias
    }

    @classmethod
    def create(cls, provider_type: str, **config) -> BaseLLMAdapter:
        """어댑터 생성

        Args:
            provider_type: "openai", "vllm" 등
            **config: Provider별 설정

        Returns:
            해당 Provider의 어댑터 인스턴스

        Raises:
            ValueError: 지원하지 않는 provider_type인 경우
        """
        provider_type = provider_type.lower()

        if provider_type not in cls._adapters:
            available = list(cls._adapters.keys())
            raise ValueError(f"지원하지 않는 Provider: {provider_type}. 가능한 옵션: {available}")

        adapter_class = cls._adapters[provider_type]
        return adapter_class(**config)

    @classmethod
    def register(cls, name: str, adapter_class: type[BaseLLMAdapter]):
        """새 어댑터 등록

        Args:
            name: 어댑터 이름
            adapter_class: BaseLLMAdapter를 상속한 클래스
        """
        cls._adapters[name.lower()] = adapter_class
        logger.info("llm_adapter_registered", name=name)


def get_llm_adapter(provider: str = "openai", **config) -> BaseLLMAdapter:
    """LLM 어댑터 생성 편의 함수

    Args:
        provider: "openai", "vllm" 등
        **config: Provider별 설정

    Returns:
        어댑터 인스턴스
    """
    return LLMAdapterFactory.create(provider, **config)
