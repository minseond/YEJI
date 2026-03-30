"""vLLM OpenAI-compatible API 클라이언트"""

import json
import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass

import httpx

from yeji_ai.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class GenerationConfig:
    """생성 설정"""

    max_tokens: int = 1500  # 프롬프트 길이 고려
    temperature: float = 0.7
    top_p: float = 0.9
    stop: list[str] | None = None
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0
    # vLLM guided decoding 옵션
    guided_json: dict | None = None  # JSON 스키마로 출력 제약
    guided_choice: list[str] | None = None  # 선택지 제약
    guided_regex: str | None = None  # 정규식 제약


@dataclass
class CompletionResponse:
    """생성 응답"""

    text: str
    finish_reason: str | None = None
    usage: dict[str, int] | None = None


class VLLMClient:
    """vLLM OpenAI-compatible API 클라이언트

    외부 GPU 서버에서 실행 중인 vLLM에 연결합니다.
    Runpod, Lambda Labs, EC2 등 어디서든 동작.
    """

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float = 120.0,
    ):
        settings = get_settings()
        self.base_url = (base_url or settings.vllm_base_url).rstrip("/")
        self.model = model or settings.vllm_model
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """HTTP 클라이언트 반환 (lazy initialization)"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout),
                headers={
                    "Content-Type": "application/json; charset=utf-8",
                    "Accept": "application/json; charset=utf-8",
                },
            )
        return self._client

    async def close(self) -> None:
        """클라이언트 종료"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def health_check(self) -> bool:
        """vLLM 서버 상태 확인"""
        try:
            client = await self._get_client()
            response = await client.get("/health")
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"vLLM 헬스체크 실패: {e}")
            return False

    async def generate(
        self,
        prompt: str,
        config: GenerationConfig | None = None,
    ) -> CompletionResponse:
        """텍스트 생성 (non-streaming)"""
        config = config or GenerationConfig()
        settings = get_settings()

        payload = {
            "model": self.model,
            "prompt": prompt,
            "max_tokens": config.max_tokens or settings.vllm_max_tokens,
            "temperature": config.temperature or settings.vllm_temperature,
            "top_p": config.top_p or settings.vllm_top_p,
            "stop": config.stop,
            "presence_penalty": config.presence_penalty,
            "frequency_penalty": config.frequency_penalty,
        }

        client = await self._get_client()
        response = await client.post("/v1/completions", json=payload)
        response.raise_for_status()

        data = response.json()
        choice = data["choices"][0]

        return CompletionResponse(
            text=choice["text"],
            finish_reason=choice.get("finish_reason"),
            usage=data.get("usage"),
        )

    async def generate_stream(
        self,
        prompt: str,
        config: GenerationConfig | None = None,
    ) -> AsyncIterator[str]:
        """텍스트 생성 (streaming)"""
        config = config or GenerationConfig()
        settings = get_settings()

        payload = {
            "model": self.model,
            "prompt": prompt,
            "max_tokens": config.max_tokens or settings.vllm_max_tokens,
            "temperature": config.temperature or settings.vllm_temperature,
            "top_p": config.top_p or settings.vllm_top_p,
            "stop": config.stop,
            "stream": True,
        }

        client = await self._get_client()
        async with client.stream(
            "POST",
            "/v1/completions",
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
                        text = data["choices"][0].get("text", "")
                        if text:
                            yield text
                except json.JSONDecodeError:
                    logger.warning(f"JSON 파싱 실패: {data_str}")
                    continue

    async def chat(
        self,
        messages: list[dict[str, str]],
        config: GenerationConfig | None = None,
    ) -> CompletionResponse:
        """채팅 완성 (non-streaming)

        Args:
            messages: 대화 메시지 목록
            config: 생성 설정 (guided_json으로 구조화된 출력 가능)

        Returns:
            CompletionResponse: 생성 결과
        """
        config = config or GenerationConfig()
        settings = get_settings()

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": config.max_tokens or settings.vllm_max_tokens,
            "temperature": config.temperature or settings.vllm_temperature,
            "top_p": config.top_p or settings.vllm_top_p,
            "stop": config.stop,
        }

        # vLLM guided decoding 옵션 추가
        extra_body = {}
        if config.guided_json:
            extra_body["guided_json"] = config.guided_json
        if config.guided_choice:
            extra_body["guided_choice"] = config.guided_choice
        if config.guided_regex:
            extra_body["guided_regex"] = config.guided_regex

        if extra_body:
            payload["extra_body"] = extra_body

        client = await self._get_client()
        response = await client.post("/v1/chat/completions", json=payload)
        response.raise_for_status()

        data = response.json()
        choice = data["choices"][0]

        return CompletionResponse(
            text=choice["message"]["content"],
            finish_reason=choice.get("finish_reason"),
            usage=data.get("usage"),
        )

    async def chat_stream(
        self,
        messages: list[dict[str, str]],
        config: GenerationConfig | None = None,
    ) -> AsyncIterator[str]:
        """채팅 완성 (streaming)"""
        config = config or GenerationConfig()
        settings = get_settings()

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": config.max_tokens or settings.vllm_max_tokens,
            "temperature": config.temperature or settings.vllm_temperature,
            "top_p": config.top_p or settings.vllm_top_p,
            "stop": config.stop,
            "stream": True,
        }

        client = await self._get_client()
        async with client.stream(
            "POST",
            "/v1/chat/completions",
            json=payload,
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line or not line.startswith("data: "):
                    continue

                data_str = line[6:]
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


# 싱글톤 인스턴스
_vllm_client: VLLMClient | None = None


def get_vllm_client() -> VLLMClient:
    """vLLM 클라이언트 싱글톤 반환"""
    global _vllm_client
    if _vllm_client is None:
        _vllm_client = VLLMClient()
    return _vllm_client
