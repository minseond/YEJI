"""vLLM Provider - 원격/로컬 vLLM 서버 통합 관리

SSH를 통한 원격 서버 제어 또는 로컬 vLLM 서버와 연동합니다.
"""

import asyncio
import json
import logging
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
from yeji_ai.providers.ssh_adapter import SSHAdapter, SSHConfig

logger = logging.getLogger(__name__)


@dataclass
class VLLMConfig:
    """vLLM Provider 설정"""

    # API 연결 설정
    base_url: str = "http://localhost:8001"  # vLLM 서버 URL
    model: str = "tellang/yeji-8b-rslora-v7"  # 모델 ID
    api_timeout: float = 120.0  # API 요청 타임아웃

    # SSH 원격 제어 설정 (옵션)
    ssh_config: SSHConfig | None = None  # SSH 설정 (None이면 로컬 모드)

    # vLLM 서버 시작 설정
    vllm_command: str = ""  # vLLM 서버 시작 커맨드
    tmux_session: str = "vllm"  # tmux 세션 이름
    startup_wait: int = 30  # 서버 시작 대기 시간 (초)

    # 기본 생성 설정
    default_max_tokens: int = 1500  # 프롬프트 길이 고려
    default_temperature: float = 0.7
    default_top_p: float = 0.9

    # 추가 옵션
    extra: dict[str, Any] = field(default_factory=dict)


class VLLMProvider(LLMProvider):
    """vLLM Provider 구현

    사용 예시:
        # 로컬 vLLM (이미 실행 중)
        provider = VLLMProvider(VLLMConfig(base_url="http://localhost:8001"))

        # ultra4 원격 vLLM
        provider = VLLMProvider(VLLMConfig(
            base_url="http://100.114.13.51:8001",
            ssh_config=SSHConfig(host="ultra4", user="user", use_wsl=True),
            vllm_command=(
                "source ~/venvs/vllm/bin/activate && "
                "vllm serve Qwen/Qwen3-4B-AWQ --port 8001"
            ),
        ))

        # AWS EC2 vLLM
        provider = VLLMProvider(VLLMConfig(
            base_url="http://localhost:8001",  # SSH 터널 사용
            ssh_config=SSHConfig(
                host="3.36.89.31",
                user="ubuntu",
                identity_file="~/.ssh/yeji-gpu-key.pem",
            ),
        ))

        # Provider 시작
        await provider.start()

        # 채팅
        response = await provider.chat([{"role": "user", "content": "안녕"}])
        print(response.text)

        # 중지
        await provider.stop()
    """

    def __init__(self, config: VLLMConfig | None = None):
        self.config = config or VLLMConfig()
        self._http_client: httpx.AsyncClient | None = None
        self._ssh_adapter: SSHAdapter | None = None
        self._current_status = ProviderStatus.UNKNOWN

        # SSH 어댑터 초기화
        if self.config.ssh_config:
            self._ssh_adapter = SSHAdapter(self.config.ssh_config)

    @property
    def name(self) -> str:
        return "vllm"

    async def _get_http_client(self) -> httpx.AsyncClient:
        """HTTP 클라이언트 반환 (lazy initialization)"""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                base_url=self.config.base_url,
                timeout=httpx.Timeout(self.config.api_timeout),
                headers={"Content-Type": "application/json"},
            )
        return self._http_client

    async def start(self) -> bool:
        """vLLM 서버 시작

        SSH 설정이 있으면 원격 서버에서 vLLM을 시작합니다.
        SSH 설정이 없으면 이미 실행 중인 로컬 서버에 연결만 합니다.

        Returns:
            성공 여부
        """
        self._current_status = ProviderStatus.STARTING

        # SSH 원격 제어 모드
        if self._ssh_adapter and self.config.vllm_command:
            logger.info(f"원격 vLLM 서버 시작: {self.config.ssh_config.host}")

            # 연결 테스트
            if not await self._ssh_adapter.test_connection():
                logger.error("SSH 연결 실패")
                self._current_status = ProviderStatus.ERROR
                return False

            # 기존 세션 종료
            await self._ssh_adapter.kill_session(self.config.tmux_session)

            # vLLM 서버 시작
            result = await self._ssh_adapter.run_background(
                self.config.vllm_command,
                session_name=self.config.tmux_session,
            )

            if not result.success:
                logger.error(f"vLLM 시작 커맨드 실패: {result.stderr}")
                self._current_status = ProviderStatus.ERROR
                return False

            # 서버 시작 대기
            logger.info(f"vLLM 서버 시작 대기 ({self.config.startup_wait}s)...")
            for i in range(self.config.startup_wait):
                await asyncio.sleep(1)
                health = await self.health()
                if health.status == ProviderStatus.RUNNING:
                    logger.info(f"vLLM 서버 시작 완료 ({i+1}s)")
                    self._current_status = ProviderStatus.RUNNING
                    return True

            # 타임아웃
            logger.error("vLLM 서버 시작 타임아웃")
            self._current_status = ProviderStatus.ERROR
            return False

        # 로컬 모드: 연결만 확인
        logger.info(f"로컬 vLLM 서버 연결: {self.config.base_url}")
        health = await self.health()

        if health.status == ProviderStatus.RUNNING:
            self._current_status = ProviderStatus.RUNNING
            return True
        else:
            logger.warning(f"vLLM 서버에 연결할 수 없음: {health.error_message}")
            self._current_status = ProviderStatus.ERROR
            return False

    async def stop(self) -> bool:
        """vLLM 서버 중지

        Returns:
            성공 여부
        """
        self._current_status = ProviderStatus.STOPPING

        # HTTP 클라이언트 종료
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
            self._http_client = None

        # SSH 원격 제어 모드: 서버 종료
        if self._ssh_adapter:
            logger.info(f"원격 vLLM 서버 중지: {self.config.ssh_config.host}")

            # tmux 세션 종료
            result = await self._ssh_adapter.kill_session(self.config.tmux_session)

            # 프로세스 강제 종료
            await self._ssh_adapter.run("pkill -f 'vllm serve' || true")

            self._current_status = ProviderStatus.STOPPED
            return result.success

        # 로컬 모드: 연결만 해제
        self._current_status = ProviderStatus.STOPPED
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

        Returns:
            상세 헬스 정보
        """
        start_time = time.time()

        try:
            client = await self._get_http_client()
            response = await client.get("/health", timeout=5.0)

            if response.status_code == 200:
                latency_ms = (time.time() - start_time) * 1000

                # 모델 정보 조회 시도
                model_info = await self._get_model_info()

                # GPU 정보 조회 (SSH 모드에서만)
                gpu_info = {}
                if self._ssh_adapter:
                    gpu_info = await self._ssh_adapter.get_gpu_info()

                return ProviderHealth(
                    status=ProviderStatus.RUNNING,
                    model=model_info.get("model", self.config.model),
                    latency_ms=latency_ms,
                    gpu_memory_used=gpu_info.get("memory_used_mb"),
                    gpu_memory_total=gpu_info.get("memory_total_mb"),
                    extra={"model_info": model_info, "gpu_info": gpu_info},
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

    async def _get_model_info(self) -> dict[str, Any]:
        """모델 정보 조회"""
        try:
            client = await self._get_http_client()
            response = await client.get("/v1/models", timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                if data.get("data"):
                    return data["data"][0]
        except Exception:
            pass
        return {}

    async def chat(
        self,
        messages: list[dict[str, str]],
        config: GenerationConfig | None = None,
    ) -> CompletionResponse:
        """채팅 완성 (non-streaming)

        Args:
            messages: 대화 메시지 목록
            config: 생성 설정

        Returns:
            생성 결과
        """
        config = config or GenerationConfig()
        start_time = time.time()

        payload: dict[str, Any] = {
            "model": self.config.model,
            "messages": messages,
            "max_tokens": (
                config.max_tokens
                if config.max_tokens is not None
                else self.config.default_max_tokens
            ),
            "temperature": (
                config.temperature
                if config.temperature is not None
                else self.config.default_temperature
            ),
            "top_p": (
                config.top_p
                if config.top_p is not None
                else self.config.default_top_p
            ),
            "stop": config.stop,
            "presence_penalty": config.presence_penalty,
            "frequency_penalty": config.frequency_penalty,
        }

        # 구조화된 출력 설정
        if config.response_format:
            payload["response_format"] = config.response_format

        # vLLM guided decoding 옵션 (extra_body)
        extra_body: dict[str, Any] = {}
        if config.guided_json:
            extra_body["guided_json"] = config.guided_json
        if config.guided_choice:
            extra_body["guided_choice"] = config.guided_choice
        if config.guided_regex:
            extra_body["guided_regex"] = config.guided_regex

        if extra_body:
            payload["extra_body"] = extra_body

        client = await self._get_http_client()
        response = await client.post("/v1/chat/completions", json=payload)
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

        Args:
            messages: 대화 메시지 목록
            config: 생성 설정

        Yields:
            생성된 텍스트 청크
        """
        config = config or GenerationConfig()

        payload: dict[str, Any] = {
            "model": self.config.model,
            "messages": messages,
            "max_tokens": (
                config.max_tokens
                if config.max_tokens is not None
                else self.config.default_max_tokens
            ),
            "temperature": (
                config.temperature
                if config.temperature is not None
                else self.config.default_temperature
            ),
            "top_p": (
                config.top_p
                if config.top_p is not None
                else self.config.default_top_p
            ),
            "stop": config.stop,
            "stream": True,
        }

        client = await self._get_http_client()

        async with client.stream(
            "POST",
            "/v1/chat/completions",
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
        mode = "SSH" if self._ssh_adapter else "Local"
        return f"<VLLMProvider mode={mode} base_url={self.config.base_url}>"
