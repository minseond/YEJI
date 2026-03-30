"""OpenAI Provider - OpenAI API 통합

GPT-5-mini를 포함한 OpenAI 모델을 사용할 수 있는 Provider입니다.
"""

import json
import logging
import os
import time
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any

import httpx

from yeji_ai.providers.base import (
    CompletionResponse,
    GenerationConfig,
    LLMProvider,
    ProviderHealth,
    ProviderStatus,
)

logger = logging.getLogger(__name__)


@dataclass
class OpenAIConfig:
    """OpenAI Provider 설정"""

    # API 연결 설정
    api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    base_url: str = "https://api.openai.com/v1"  # 로컬 호환 서버 사용 시 변경 가능
    model: str = "gpt-5-mini"  # 모델 ID
    api_timeout: float = 120.0  # API 요청 타임아웃

    # 조직 설정 (옵션)
    organization: str | None = None  # OpenAI 조직 ID

    # 기본 생성 설정
    default_max_tokens: int = 3000  # 티키타카 응답 500~1500 토큰 + 버퍼
    default_temperature: float = 0.7
    default_top_p: float = 0.9

    # 추가 옵션
    extra: dict[str, Any] = field(default_factory=dict)


class OpenAIProvider(LLMProvider):
    """OpenAI Provider 구현

    사용 예시:
        # 기본 사용 (환경변수에서 API 키 자동 로드)
        provider = OpenAIProvider()

        # 커스텀 설정
        provider = OpenAIProvider(OpenAIConfig(
            api_key="sk-...",
            model="gpt-5-mini",
            base_url="https://api.openai.com/v1",
        ))

        # 로컬 호환 서버 (예: LocalAI, vLLM with OpenAI API)
        provider = OpenAIProvider(OpenAIConfig(
            api_key="dummy",
            base_url="http://localhost:8001/v1",
            model="custom-model",
        ))

        # Provider 시작
        await provider.start()

        # 채팅
        response = await provider.chat([{"role": "user", "content": "안녕"}])
        print(response.text)

        # 스트리밍
        async for chunk in provider.chat_stream([{"role": "user", "content": "안녕"}]):
            print(chunk, end="", flush=True)

        # 중지
        await provider.stop()
    """

    def __init__(self, config: OpenAIConfig | None = None):
        self.config = config or OpenAIConfig()
        self._http_client: httpx.AsyncClient | None = None
        self._current_status = ProviderStatus.UNKNOWN

        # API 키 검증
        if not self.config.api_key:
            logger.warning(
                "OpenAI API 키가 설정되지 않았습니다. 환경변수 OPENAI_API_KEY를 확인하세요."
            )

    @property
    def name(self) -> str:
        return "openai"

    async def _get_http_client(self) -> httpx.AsyncClient:
        """HTTP 클라이언트 반환 (lazy initialization)"""
        if self._http_client is None or self._http_client.is_closed:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.config.api_key}",
            }

            # 조직 ID가 있으면 헤더에 추가
            if self.config.organization:
                headers["OpenAI-Organization"] = self.config.organization

            self._http_client = httpx.AsyncClient(
                base_url=self.config.base_url,
                timeout=httpx.Timeout(self.config.api_timeout),
                headers=headers,
            )
        return self._http_client

    async def start(self) -> bool:
        """OpenAI API 연결 시작

        API 키를 검증하고 연결을 테스트합니다.

        Returns:
            성공 여부
        """
        self._current_status = ProviderStatus.STARTING

        # API 키 확인
        if not self.config.api_key:
            logger.error("OpenAI API 키가 없습니다.")
            self._current_status = ProviderStatus.ERROR
            return False

        # 헬스체크로 연결 확인
        logger.info(f"OpenAI API 연결 시작: {self.config.base_url}")
        health = await self.health()

        if health.status == ProviderStatus.RUNNING:
            self._current_status = ProviderStatus.RUNNING
            logger.info(f"OpenAI API 연결 성공 (model: {health.model})")
            return True
        else:
            logger.error(f"OpenAI API 연결 실패: {health.error_message}")
            self._current_status = ProviderStatus.ERROR
            return False

    async def stop(self) -> bool:
        """OpenAI API 연결 중지

        Returns:
            성공 여부
        """
        self._current_status = ProviderStatus.STOPPING

        # HTTP 클라이언트 종료
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
            self._http_client = None

        self._current_status = ProviderStatus.STOPPED
        logger.info("OpenAI API 연결 종료")
        return True

    async def status(self) -> ProviderStatus:
        """현재 상태 확인

        Returns:
            Provider 상태
        """
        # 캐시된 상태가 STARTING/STOPPING이면 그대로 반환
        if self._current_status in (ProviderStatus.STARTING, ProviderStatus.STOPPING):
            return self._current_status

        # 헬스체크로 실제 상태 확인
        health = await self.health()
        return health.status

    async def health(self) -> ProviderHealth:
        """헬스체크 수행

        /v1/models 엔드포인트로 API 상태와 모델 정보를 확인합니다.

        Returns:
            상세 헬스 정보
        """
        start_time = time.time()

        try:
            client = await self._get_http_client()
            response = await client.get("/models", timeout=10.0)

            if response.status_code == 200:
                latency_ms = (time.time() - start_time) * 1000
                data = response.json()

                # 사용 가능한 모델 목록에서 현재 모델 찾기
                available_models = data.get("data", [])
                current_model = None
                for model_data in available_models:
                    if model_data.get("id") == self.config.model:
                        current_model = model_data
                        break

                return ProviderHealth(
                    status=ProviderStatus.RUNNING,
                    model=self.config.model,
                    latency_ms=latency_ms,
                    extra={
                        "model_info": current_model,
                        "available_models_count": len(available_models),
                    },
                )

            # 401 Unauthorized
            if response.status_code == 401:
                return ProviderHealth(
                    status=ProviderStatus.ERROR,
                    error_message="API 키가 유효하지 않습니다 (401 Unauthorized)",
                )

            return ProviderHealth(
                status=ProviderStatus.ERROR,
                error_message=f"Health check failed: {response.status_code}",
            )

        except httpx.ConnectError as e:
            return ProviderHealth(
                status=ProviderStatus.STOPPED,
                error_message=f"Connection refused: {e}",
            )
        except httpx.TimeoutException:
            return ProviderHealth(
                status=ProviderStatus.STOPPED,
                error_message="Health check timeout",
            )
        except Exception as e:
            logger.exception(f"헬스체크 실패: {e}")
            return ProviderHealth(
                status=ProviderStatus.ERROR,
                error_message=str(e),
            )

    async def chat(
        self,
        messages: list[dict[str, str]],
        config: GenerationConfig | None = None,
    ) -> CompletionResponse:
        """채팅 완성 (non-streaming)

        OpenAI Chat Completions API를 호출합니다.

        Args:
            messages: 대화 메시지 목록
            config: 생성 설정

        Returns:
            생성 결과
        """
        config = config or GenerationConfig()
        start_time = time.time()

        # GPT-5-mini는 max_completion_tokens 사용, temperature 고정
        is_gpt5_mini = "gpt-5" in self.config.model.lower()

        max_tokens_value = (
            config.max_tokens
            if config.max_tokens is not None
            else self.config.default_max_tokens
        )

        payload: dict[str, Any] = {
            "model": self.config.model,
            "messages": messages,
        }

        # GPT-5-mini는 max_completion_tokens 사용
        if is_gpt5_mini:
            payload["max_completion_tokens"] = max_tokens_value
            # temperature는 GPT-5-mini에서 고정이므로 제외
        else:
            payload["max_tokens"] = max_tokens_value
            payload["temperature"] = (
                config.temperature
                if config.temperature is not None
                else self.config.default_temperature
            )
            payload["top_p"] = (
                config.top_p if config.top_p is not None else self.config.default_top_p
            )
            payload["presence_penalty"] = config.presence_penalty
            payload["frequency_penalty"] = config.frequency_penalty

        # stop 시퀀스
        if config.stop:
            payload["stop"] = config.stop

        # 구조화된 출력 설정 (response_format)
        if config.response_format:
            payload["response_format"] = config.response_format

        client = await self._get_http_client()
        response = await client.post("/chat/completions", json=payload)
        response.raise_for_status()

        data = response.json()
        choice = data["choices"][0]
        latency_ms = (time.time() - start_time) * 1000

        return CompletionResponse(
            text=choice["message"]["content"],
            finish_reason=choice.get("finish_reason"),
            usage=data.get("usage"),
            model=data.get("model"),
            latency_ms=latency_ms,
        )

    async def chat_stream(
        self,
        messages: list[dict[str, str]],
        config: GenerationConfig | None = None,
    ) -> AsyncIterator[str]:
        """채팅 완성 (streaming)

        OpenAI Streaming API를 사용하여 SSE 형식으로 응답을 받습니다.

        Args:
            messages: 대화 메시지 목록
            config: 생성 설정

        Yields:
            생성된 텍스트 청크
        """
        config = config or GenerationConfig()

        # GPT-5-mini는 max_completion_tokens 사용, temperature 고정
        is_gpt5_mini = "gpt-5" in self.config.model.lower()

        max_tokens_value = (
            config.max_tokens
            if config.max_tokens is not None
            else self.config.default_max_tokens
        )

        payload: dict[str, Any] = {
            "model": self.config.model,
            "messages": messages,
            "stream": True,
        }

        # GPT-5-mini는 max_completion_tokens 사용
        if is_gpt5_mini:
            payload["max_completion_tokens"] = max_tokens_value
            # temperature는 GPT-5-mini에서 고정이므로 제외
        else:
            payload["max_tokens"] = max_tokens_value
            payload["temperature"] = (
                config.temperature
                if config.temperature is not None
                else self.config.default_temperature
            )
            payload["top_p"] = (
                config.top_p if config.top_p is not None else self.config.default_top_p
            )

        # stop 시퀀스
        if config.stop:
            payload["stop"] = config.stop

        client = await self._get_http_client()

        async with client.stream(
            "POST",
            "/chat/completions",
            json=payload,
        ) as response:
            response.raise_for_status()

            async for line in response.aiter_lines():
                if not line or not line.startswith("data: "):
                    continue

                data_str = line[6:]  # "data: " 제거
                if data_str == "[DONE]":
                    break

                try:
                    data = json.loads(data_str)
                    if "choices" in data and data["choices"]:
                        delta = data["choices"][0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield content
                except json.JSONDecodeError:
                    logger.warning(f"JSON 파싱 실패: {data_str}")
                    continue

    async def close(self) -> None:
        """리소스 정리"""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
            self._http_client = None

    def __repr__(self) -> str:
        return f"<OpenAIProvider model={self.config.model} base_url={self.config.base_url}>"
