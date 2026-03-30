"""LLM Provider 추상 인터페이스

모든 LLM Provider (vLLM, Ollama, AWS)가 구현해야 하는 공통 인터페이스를 정의합니다.
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class ProviderStatus(str, Enum):
    """Provider 상태"""

    UNKNOWN = "unknown"  # 상태 미확인
    STOPPED = "stopped"  # 중지됨
    STARTING = "starting"  # 시작 중
    RUNNING = "running"  # 실행 중
    STOPPING = "stopping"  # 중지 중
    ERROR = "error"  # 오류 상태


@dataclass
class ProviderHealth:
    """Provider 헬스체크 결과"""

    status: ProviderStatus
    model: str | None = None
    latency_ms: float | None = None
    gpu_memory_used: float | None = None  # MB
    gpu_memory_total: float | None = None  # MB
    last_checked: datetime = field(default_factory=datetime.now)
    error_message: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class GenerationConfig:
    """생성 설정"""

    max_tokens: int = 1500  # 프롬프트 길이 고려
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int | None = None
    min_p: float | None = None
    stop: list[str] | None = None
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0
    # 구조화된 출력
    response_format: dict[str, Any] | None = None  # {"type": "json_object"}
    guided_json: dict | None = None
    guided_choice: list[str] | None = None
    guided_regex: str | None = None


@dataclass
class CompletionResponse:
    """생성 응답"""

    text: str
    finish_reason: str | None = None
    usage: dict[str, int] | None = None
    model: str | None = None
    latency_ms: float | None = None


class LLMProvider(ABC):
    """LLM Provider 추상 인터페이스

    모든 LLM Provider가 구현해야 하는 메서드:
    - start(): Provider 시작 (서버 기동)
    - stop(): Provider 중지 (서버 종료)
    - status(): 현재 상태 확인
    - health(): 헬스체크 (모델 로딩 상태 등)
    - chat(): 채팅 완성
    - chat_stream(): 스트리밍 채팅 완성
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider 이름"""
        pass

    @abstractmethod
    async def start(self) -> bool:
        """Provider 시작

        Returns:
            성공 여부
        """
        pass

    @abstractmethod
    async def stop(self) -> bool:
        """Provider 중지

        Returns:
            성공 여부
        """
        pass

    @abstractmethod
    async def status(self) -> ProviderStatus:
        """현재 상태 확인

        Returns:
            Provider 상태
        """
        pass

    @abstractmethod
    async def health(self) -> ProviderHealth:
        """헬스체크 수행

        Returns:
            상세 헬스 정보
        """
        pass

    @abstractmethod
    async def chat(
        self,
        messages: list[dict[str, str]],
        config: GenerationConfig | None = None,
    ) -> CompletionResponse:
        """채팅 완성 (non-streaming)

        Args:
            messages: 대화 메시지 목록 [{"role": "user", "content": "..."}]
            config: 생성 설정

        Returns:
            생성 결과
        """
        pass

    @abstractmethod
    async def chat_stream(
        self,
        messages: list[dict[str, str]],
        config: GenerationConfig | None = None,
    ) -> AsyncIterator[str]:
        """채팅 완성 (streaming)

        Args:
            messages: 대화 메시지 목록
            config: 생성 설정

        Yields:
            생성된 텍스트 청크
        """
        pass

    async def generate(
        self,
        prompt: str,
        config: GenerationConfig | None = None,
    ) -> CompletionResponse:
        """텍스트 생성 (non-streaming)

        기본 구현: prompt를 user 메시지로 변환하여 chat() 호출
        """
        messages = [{"role": "user", "content": prompt}]
        return await self.chat(messages, config)

    async def generate_stream(
        self,
        prompt: str,
        config: GenerationConfig | None = None,
    ) -> AsyncIterator[str]:
        """텍스트 생성 (streaming)

        기본 구현: prompt를 user 메시지로 변환하여 chat_stream() 호출
        """
        messages = [{"role": "user", "content": prompt}]
        async for chunk in self.chat_stream(messages, config):
            yield chunk

    async def close(self) -> None:
        """리소스 정리 (선택적 구현)"""
        pass

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name}>"
