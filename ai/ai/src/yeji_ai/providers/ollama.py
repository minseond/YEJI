"""Ollama Provider - 로컬 Ollama 서버 통합 관리

Ollama API를 통해 로컬 LLM 모델을 제어합니다.
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

logger = logging.getLogger(__name__)


@dataclass
class OllamaConfig:
    """Ollama Provider 설정"""

    # API 연결 설정
    base_url: str = "http://localhost:11434"  # Ollama 서버 URL
    model: str = "qwen3:4b"  # 모델 이름
    api_timeout: float = 120.0  # API 요청 타임아웃

    # 자동 시작 설정
    auto_start: bool = True  # Ollama 서비스 자동 시작
    startup_wait: int = 30  # 서버 시작 대기 시간 (초)

    # 모델 풀링 설정
    auto_pull: bool = True  # 모델이 없으면 자동 다운로드

    # 기본 생성 설정
    default_max_tokens: int = 1500  # 프롬프트 길이 고려 (max_model_len 4096)
    default_temperature: float = 0.7
    default_top_p: float = 0.9

    # 추가 옵션
    extra: dict[str, Any] = field(default_factory=dict)


class OllamaProvider(LLMProvider):
    """Ollama Provider 구현

    사용 예시:
        provider = OllamaProvider(OllamaConfig(
            model="qwen3:4b",
            auto_start=True,
            auto_pull=True,
        ))

        # Provider 시작 (Ollama 서비스 + 모델 로딩)
        await provider.start()

        # 채팅
        response = await provider.chat([{"role": "user", "content": "안녕"}])
        print(response.text)

        # 중지
        await provider.stop()
    """

    def __init__(self, config: OllamaConfig | None = None):
        self.config = config or OllamaConfig()
        self._http_client: httpx.AsyncClient | None = None
        self._current_status = ProviderStatus.UNKNOWN

    @property
    def name(self) -> str:
        return "ollama"

    async def _get_http_client(self) -> httpx.AsyncClient:
        """HTTP 클라이언트 반환 (lazy initialization)"""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                base_url=self.config.base_url,
                timeout=httpx.Timeout(self.config.api_timeout),
                headers={"Content-Type": "application/json"},
            )
        return self._http_client

    async def _start_ollama_service(self) -> bool:
        """Ollama 서비스 시작 (Windows/Mac/Linux)"""
        import platform

        system = platform.system().lower()

        try:
            if system == "windows":
                # Windows: Ollama 앱 실행 (CREATE_NO_WINDOW 플래그 사용)
                import subprocess
                subprocess.Popen(
                    ["ollama", "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
            elif system == "darwin":
                # macOS: 직접 실행
                await asyncio.create_subprocess_exec(
                    "ollama", "serve",
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                )
            else:
                # Linux: systemctl 확인 후 직접 실행
                process = await asyncio.create_subprocess_exec(
                    "systemctl", "is-active", "ollama",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await process.communicate()

                if process.returncode != 0:
                    await asyncio.create_subprocess_exec(
                        "ollama", "serve",
                        stdout=asyncio.subprocess.DEVNULL,
                        stderr=asyncio.subprocess.DEVNULL,
                    )

            logger.info("Ollama 서비스 시작 요청")
            return True

        except FileNotFoundError:
            logger.error("Ollama가 설치되어 있지 않습니다")
            return False
        except Exception as e:
            logger.exception(f"Ollama 서비스 시작 실패: {e}")
            return False

    async def _stop_ollama_service(self) -> bool:
        """Ollama 서비스 중지"""
        import platform

        system = platform.system().lower()

        try:
            if system == "linux":
                process = await asyncio.create_subprocess_exec(
                    "systemctl", "stop", "ollama",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await process.communicate()
            elif system == "windows":
                # Windows: taskkill로 프로세스 종료
                process = await asyncio.create_subprocess_exec(
                    "taskkill", "/F", "/IM", "ollama.exe",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await process.communicate()
            else:
                # macOS: pkill로 프로세스 종료
                process = await asyncio.create_subprocess_exec(
                    "pkill", "-f", "ollama",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await process.communicate()

            logger.info("Ollama 서비스 중지 요청")
            return True

        except Exception as e:
            logger.exception(f"Ollama 서비스 중지 실패: {e}")
            return False

    async def _pull_model(self) -> bool:
        """모델 다운로드 (pull)"""
        try:
            client = await self._get_http_client()

            logger.info(f"모델 다운로드 시작: {self.config.model}")

            # Ollama pull API 호출 (스트리밍)
            async with client.stream(
                "POST",
                "/api/pull",
                json={"name": self.config.model},
                timeout=None,  # 다운로드는 시간 제한 없음
            ) as response:
                if response.status_code != 200:
                    logger.error(f"모델 다운로드 실패: {response.status_code}")
                    return False

                async for line in response.aiter_lines():
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        status = data.get("status", "")
                        if "pulling" in status:
                            completed = data.get("completed", 0)
                            total = data.get("total", 0)
                            if total > 0:
                                progress = (completed / total) * 100
                                logger.debug(f"다운로드 진행: {progress:.1f}%")
                        elif status == "success":
                            logger.info(f"모델 다운로드 완료: {self.config.model}")
                            return True
                    except json.JSONDecodeError:
                        continue

            return True

        except Exception as e:
            logger.exception(f"모델 다운로드 실패: {e}")
            return False

    async def _is_model_available(self) -> bool:
        """모델 로컬 존재 여부 확인"""
        try:
            client = await self._get_http_client()
            response = await client.get("/api/tags", timeout=5.0)

            if response.status_code == 200:
                data = response.json()
                models = [m.get("name", "") for m in data.get("models", [])]
                # 정확한 이름 또는 태그 없는 이름으로 매칭
                model_base = self.config.model.split(":")[0]
                return any(
                    m == self.config.model or m.startswith(f"{model_base}:")
                    for m in models
                )

        except Exception:
            pass
        return False

    async def start(self) -> bool:
        """Ollama Provider 시작

        1. Ollama 서비스 시작 (auto_start=True인 경우)
        2. 모델 다운로드 (auto_pull=True이고 모델이 없는 경우)
        3. 모델 로딩 확인

        Returns:
            성공 여부
        """
        self._current_status = ProviderStatus.STARTING

        # 1. 서비스 연결 확인 및 시작
        health = await self.health()

        if health.status != ProviderStatus.RUNNING:
            if self.config.auto_start:
                logger.info("Ollama 서비스 시작 중...")

                if not await self._start_ollama_service():
                    self._current_status = ProviderStatus.ERROR
                    return False

                # 서비스 시작 대기
                for i in range(self.config.startup_wait):
                    await asyncio.sleep(1)
                    health = await self.health()
                    if health.status == ProviderStatus.RUNNING:
                        logger.info(f"Ollama 서비스 시작 완료 ({i+1}s)")
                        break
                else:
                    logger.error("Ollama 서비스 시작 타임아웃")
                    self._current_status = ProviderStatus.ERROR
                    return False
            else:
                logger.error("Ollama 서비스가 실행 중이 아닙니다")
                self._current_status = ProviderStatus.ERROR
                return False

        # 2. 모델 확인 및 다운로드
        if not await self._is_model_available():
            if self.config.auto_pull:
                logger.info(f"모델 다운로드 필요: {self.config.model}")
                if not await self._pull_model():
                    self._current_status = ProviderStatus.ERROR
                    return False
            else:
                logger.error(f"모델이 없습니다: {self.config.model}")
                self._current_status = ProviderStatus.ERROR
                return False

        self._current_status = ProviderStatus.RUNNING
        logger.info(f"Ollama Provider 시작 완료: {self.config.model}")
        return True

    async def stop(self) -> bool:
        """Ollama Provider 중지

        Returns:
            성공 여부
        """
        self._current_status = ProviderStatus.STOPPING

        # HTTP 클라이언트 종료
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
            self._http_client = None

        # 서비스 중지는 선택적 (다른 앱이 사용할 수 있음)
        # await self._stop_ollama_service()

        self._current_status = ProviderStatus.STOPPED
        return True

    async def status(self) -> ProviderStatus:
        """현재 상태 확인"""
        if self._current_status in (ProviderStatus.STARTING, ProviderStatus.STOPPING):
            return self._current_status

        health = await self.health()
        return health.status

    async def health(self) -> ProviderHealth:
        """헬스체크 수행"""
        start_time = time.time()

        try:
            client = await self._get_http_client()

            # Ollama 버전 API로 서비스 상태 확인
            response = await client.get("/api/version", timeout=5.0)

            if response.status_code == 200:
                latency_ms = (time.time() - start_time) * 1000
                version_data = response.json()

                # 모델 목록 조회
                models_response = await client.get("/api/tags", timeout=5.0)
                models = []
                if models_response.status_code == 200:
                    models = models_response.json().get("models", [])

                return ProviderHealth(
                    status=ProviderStatus.RUNNING,
                    model=self.config.model,
                    latency_ms=latency_ms,
                    extra={
                        "version": version_data.get("version"),
                        "models": [m.get("name") for m in models],
                    },
                )

            return ProviderHealth(
                status=ProviderStatus.ERROR,
                error_message=f"Ollama API error: {response.status_code}",
            )

        except httpx.ConnectError:
            return ProviderHealth(
                status=ProviderStatus.STOPPED,
                error_message="Ollama service not running",
            )
        except httpx.TimeoutException:
            return ProviderHealth(
                status=ProviderStatus.STOPPED,
                error_message="Connection timeout",
            )
        except Exception as e:
            return ProviderHealth(
                status=ProviderStatus.ERROR,
                error_message=str(e),
            )

    async def chat(
        self,
        messages: list[dict[str, str]],
        config: GenerationConfig | None = None,
    ) -> CompletionResponse:
        """채팅 완성 (non-streaming)"""
        config = config or GenerationConfig()
        start_time = time.time()

        # Ollama chat API 형식
        payload: dict[str, Any] = {
            "model": self.config.model,
            "messages": messages,
            "stream": False,
            "options": {
                "num_predict": (
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
            },
        }

        if config.stop:
            payload["options"]["stop"] = config.stop

        # JSON 형식 강제 (Ollama 방식)
        if config.response_format and config.response_format.get("type") == "json_object":
            payload["format"] = "json"

        client = await self._get_http_client()
        response = await client.post("/api/chat", json=payload)
        response.raise_for_status()

        data = response.json()
        latency_ms = (time.time() - start_time) * 1000

        return CompletionResponse(
            text=data.get("message", {}).get("content", ""),
            finish_reason=data.get("done_reason"),
            usage={
                "prompt_tokens": data.get("prompt_eval_count", 0),
                "completion_tokens": data.get("eval_count", 0),
                "total_tokens": (
                    data.get("prompt_eval_count", 0) + data.get("eval_count", 0)
                ),
            },
            model=data.get("model"),
            latency_ms=latency_ms,
        )

    async def chat_stream(
        self,
        messages: list[dict[str, str]],
        config: GenerationConfig | None = None,
    ) -> AsyncIterator[str]:
        """채팅 완성 (streaming)"""
        config = config or GenerationConfig()

        payload: dict[str, Any] = {
            "model": self.config.model,
            "messages": messages,
            "stream": True,
            "options": {
                "num_predict": (
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
            },
        }

        if config.stop:
            payload["options"]["stop"] = config.stop

        client = await self._get_http_client()

        async with client.stream(
            "POST",
            "/api/chat",
            json=payload,
        ) as response:
            response.raise_for_status()

            async for line in response.aiter_lines():
                if not line:
                    continue

                try:
                    data = json.loads(line)
                    content = data.get("message", {}).get("content", "")
                    if content:
                        yield content

                    if data.get("done"):
                        break
                except json.JSONDecodeError:
                    logger.warning(f"JSON 파싱 실패: {line}")
                    continue

    async def close(self) -> None:
        """리소스 정리"""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
            self._http_client = None

    async def list_models(self) -> list[dict[str, Any]]:
        """로컬 모델 목록 조회"""
        try:
            client = await self._get_http_client()
            response = await client.get("/api/tags", timeout=5.0)
            if response.status_code == 200:
                return response.json().get("models", [])
        except Exception:
            pass
        return []

    async def delete_model(self, model_name: str) -> bool:
        """모델 삭제"""
        try:
            client = await self._get_http_client()
            response = await client.delete("/api/delete", json={"name": model_name})
            return response.status_code == 200
        except Exception as e:
            logger.exception(f"모델 삭제 실패: {e}")
            return False

    def __repr__(self) -> str:
        return f"<OllamaProvider model={self.config.model} base_url={self.config.base_url}>"
