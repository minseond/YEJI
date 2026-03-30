"""AWS Provider - EC2 인스턴스 기반 vLLM 서버 관리

AWS EC2 GPU 인스턴스를 시작/중지하고 vLLM 서버를 제어합니다.
SSH 터널링을 통해 로컬에서 원격 vLLM에 연결합니다.
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
class AWSConfig:
    """AWS Provider 설정"""

    # EC2 인스턴스 설정
    instance_id: str = ""  # EC2 인스턴스 ID (예: i-0123456789abcdef0)
    region: str = "ap-northeast-2"  # AWS 리전

    # SSH 연결 설정
    ssh_host: str = ""  # EC2 퍼블릭 IP 또는 DNS
    ssh_user: str = "ubuntu"  # SSH 사용자
    ssh_key_file: str = ""  # SSH 키 파일 경로 (예: ~/.ssh/yeji-gpu-key.pem)

    # vLLM API 설정
    base_url: str = ""  # vLLM API URL (직접 지정 시, SSH 터널 무시)
    local_port: int = 8001  # 로컬 포트 (SSH 터널)
    remote_port: int = 8001  # 원격 vLLM 포트
    model: str = "tellang/yeji-8b-rslora-v7"  # 모델 ID
    api_timeout: float = 120.0  # API 요청 타임아웃

    # vLLM 서버 시작 설정
    vllm_command: str = ""  # vLLM 서버 시작 커맨드
    tmux_session: str = "vllm"  # tmux 세션 이름
    startup_wait: int = 60  # 서버 시작 대기 시간 (초)

    # AWS CLI 프로파일
    aws_profile: str | None = None  # AWS CLI 프로파일 이름

    # 기본 생성 설정
    default_max_tokens: int = 1500  # 프롬프트 길이 고려 (max_model_len 4096)
    default_temperature: float = 0.7
    default_top_p: float = 0.9

    # 추가 옵션
    extra: dict[str, Any] = field(default_factory=dict)


class AWSProvider(LLMProvider):
    """AWS EC2 기반 vLLM Provider 구현

    EC2 GPU 인스턴스를 시작/중지하고 SSH 터널을 통해 vLLM에 연결합니다.

    사용 예시:
        provider = AWSProvider(AWSConfig(
            instance_id="i-0123456789abcdef0",
            region="ap-northeast-2",
            ssh_host="3.36.89.31",
            ssh_user="ubuntu",
            ssh_key_file="~/.ssh/yeji-gpu-key.pem",
            vllm_command="source ~/venvs/vllm/bin/activate && vllm serve ...",
        ))

        # EC2 시작 + vLLM 시작 + SSH 터널 연결
        await provider.start()

        # 채팅 (로컬 포트로 연결)
        response = await provider.chat([{"role": "user", "content": "안녕"}])

        # 중지 (vLLM 중지, EC2는 선택적)
        await provider.stop()
    """

    def __init__(self, config: AWSConfig | None = None):
        self.config = config or AWSConfig()
        self._http_client: httpx.AsyncClient | None = None
        self._ssh_adapter: SSHAdapter | None = None
        self._tunnel_process: asyncio.subprocess.Process | None = None
        self._current_status = ProviderStatus.UNKNOWN

        # SSH 어댑터 초기화
        if self.config.ssh_host and self.config.ssh_key_file:
            self._ssh_adapter = SSHAdapter(
                SSHConfig(
                    host=self.config.ssh_host,
                    user=self.config.ssh_user,
                    identity_file=self.config.ssh_key_file,
                )
            )

    @property
    def name(self) -> str:
        return "aws"

    @property
    def _base_url(self) -> str:
        """API 엔드포인트 (base_url 직접 지정 또는 SSH 터널 사용)"""
        if self.config.base_url:
            # 직접 지정된 URL 사용 (Docker 환경 등)
            return self.config.base_url.rstrip("/")
        return f"http://localhost:{self.config.local_port}"

    async def _get_http_client(self) -> httpx.AsyncClient:
        """HTTP 클라이언트 반환"""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                base_url=self._base_url,
                timeout=httpx.Timeout(self.config.api_timeout),
                headers={"Content-Type": "application/json"},
            )
        return self._http_client

    async def _run_aws_cli(self, *args: str) -> tuple[bool, str]:
        """AWS CLI 명령 실행

        Args:
            *args: AWS CLI 인자

        Returns:
            (성공 여부, 출력)
        """
        cmd = ["aws"]

        if self.config.aws_profile:
            cmd.extend(["--profile", self.config.aws_profile])

        cmd.extend(["--region", self.config.region])
        cmd.extend(args)

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()

            output = stdout.decode() if stdout else stderr.decode()
            return process.returncode == 0, output

        except FileNotFoundError:
            return False, "AWS CLI not found. Install awscli."
        except Exception as e:
            return False, str(e)

    async def _get_instance_state(self) -> str:
        """EC2 인스턴스 상태 조회

        Returns:
            인스턴스 상태 (running, stopped, pending, stopping, terminated)
        """
        if not self.config.instance_id:
            return "unknown"

        success, output = await self._run_aws_cli(
            "ec2",
            "describe-instances",
            "--instance-ids",
            self.config.instance_id,
            "--query",
            "Reservations[0].Instances[0].State.Name",
            "--output",
            "text",
        )

        if success:
            return output.strip().lower()
        return "unknown"

    async def _start_instance(self) -> bool:
        """EC2 인스턴스 시작"""
        if not self.config.instance_id:
            logger.warning("instance_id가 설정되지 않음")
            return False

        logger.info(f"EC2 인스턴스 시작: {self.config.instance_id}")

        success, output = await self._run_aws_cli(
            "ec2",
            "start-instances",
            "--instance-ids",
            self.config.instance_id,
        )

        if not success:
            logger.error(f"EC2 시작 실패: {output}")
            return False

        # 인스턴스 running 상태 대기
        for _ in range(120):  # 최대 2분 대기
            await asyncio.sleep(2)
            state = await self._get_instance_state()
            if state == "running":
                logger.info("EC2 인스턴스 running 상태")

                # 퍼블릭 IP 업데이트
                await self._update_public_ip()
                return True

        logger.error("EC2 시작 타임아웃")
        return False

    async def _stop_instance(self) -> bool:
        """EC2 인스턴스 중지"""
        if not self.config.instance_id:
            return False

        logger.info(f"EC2 인스턴스 중지: {self.config.instance_id}")

        success, output = await self._run_aws_cli(
            "ec2",
            "stop-instances",
            "--instance-ids",
            self.config.instance_id,
        )

        if not success:
            logger.error(f"EC2 중지 실패: {output}")
            return False

        return True

    async def _update_public_ip(self) -> None:
        """EC2 퍼블릭 IP 업데이트"""
        success, output = await self._run_aws_cli(
            "ec2",
            "describe-instances",
            "--instance-ids",
            self.config.instance_id,
            "--query",
            "Reservations[0].Instances[0].PublicIpAddress",
            "--output",
            "text",
        )

        if success and output.strip() and output.strip() != "None":
            new_ip = output.strip()
            if new_ip != self.config.ssh_host:
                logger.info(f"퍼블릭 IP 업데이트: {self.config.ssh_host} -> {new_ip}")
                self.config.ssh_host = new_ip

                # SSH 어댑터 재초기화
                if self.config.ssh_key_file:
                    self._ssh_adapter = SSHAdapter(
                        SSHConfig(
                            host=new_ip,
                            user=self.config.ssh_user,
                            identity_file=self.config.ssh_key_file,
                        )
                    )

    async def _start_ssh_tunnel(self) -> bool:
        """SSH 터널 시작

        로컬 포트를 원격 vLLM 포트로 포워딩합니다.
        """
        if not self.config.ssh_host or not self.config.ssh_key_file:
            logger.warning("SSH 설정이 없음 - 터널 생략")
            return True

        # 기존 터널 종료
        await self._stop_ssh_tunnel()

        cmd = [
            "ssh",
            "-o",
            "StrictHostKeyChecking=no",
            "-o",
            "ConnectTimeout=10",
            "-o",
            "ServerAliveInterval=60",
            "-i",
            self.config.ssh_key_file,
            "-L",
            f"{self.config.local_port}:localhost:{self.config.remote_port}",
            "-N",  # 커맨드 실행 안 함
            f"{self.config.ssh_user}@{self.config.ssh_host}",
        ]

        logger.info(
            f"SSH 터널 시작: localhost:{self.config.local_port} -> "
            f"{self.config.ssh_host}:{self.config.remote_port}"
        )

        try:
            self._tunnel_process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )

            # 터널 연결 대기
            await asyncio.sleep(2)

            if self._tunnel_process.returncode is not None:
                logger.error("SSH 터널 시작 실패")
                return False

            logger.info("SSH 터널 연결됨")
            return True

        except Exception as e:
            logger.exception(f"SSH 터널 시작 실패: {e}")
            return False

    async def _stop_ssh_tunnel(self) -> None:
        """SSH 터널 중지"""
        if self._tunnel_process:
            try:
                self._tunnel_process.terminate()
                await asyncio.wait_for(self._tunnel_process.wait(), timeout=5.0)
            except TimeoutError:
                self._tunnel_process.kill()
            except Exception:
                pass
            finally:
                self._tunnel_process = None
                logger.info("SSH 터널 종료됨")

    async def start(self) -> bool:
        """AWS Provider 시작

        1. EC2 인스턴스 시작 (stopped 상태인 경우)
        2. SSH 터널 시작
        3. vLLM 서버 시작 (커맨드가 설정된 경우)
        4. 연결 확인

        Returns:
            성공 여부
        """
        self._current_status = ProviderStatus.STARTING

        # 1. EC2 인스턴스 상태 확인 및 시작
        if self.config.instance_id:
            state = await self._get_instance_state()
            logger.info(f"EC2 인스턴스 상태: {state}")

            if state == "stopped":
                if not await self._start_instance():
                    self._current_status = ProviderStatus.ERROR
                    return False

                # SSH 접속 가능 대기
                logger.info("SSH 접속 대기 중...")
                await asyncio.sleep(30)

            elif state not in ("running", "unknown"):
                logger.error(f"EC2 인스턴스 상태 이상: {state}")
                self._current_status = ProviderStatus.ERROR
                return False

        # 2. SSH 터널 시작
        if not await self._start_ssh_tunnel():
            self._current_status = ProviderStatus.ERROR
            return False

        # 3. vLLM 서버 시작 (원격)
        if self._ssh_adapter and self.config.vllm_command:
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
                logger.error(f"vLLM 시작 실패: {result.stderr}")
                self._current_status = ProviderStatus.ERROR
                return False

        # 4. 서버 시작 대기 및 연결 확인
        logger.info(f"vLLM 서버 시작 대기 ({self.config.startup_wait}s)...")
        for i in range(self.config.startup_wait):
            await asyncio.sleep(1)
            health = await self.health()
            if health.status == ProviderStatus.RUNNING:
                logger.info(f"vLLM 서버 연결 완료 ({i+1}s)")
                self._current_status = ProviderStatus.RUNNING
                return True

        # 타임아웃
        logger.error("vLLM 서버 연결 타임아웃")
        self._current_status = ProviderStatus.ERROR
        return False

    async def stop(self) -> bool:
        """AWS Provider 중지 (EC2 인스턴스는 유지)

        Returns:
            성공 여부
        """
        self._current_status = ProviderStatus.STOPPING

        # HTTP 클라이언트 종료
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
            self._http_client = None

        # vLLM 서버 중지 (원격)
        if self._ssh_adapter:
            await self._ssh_adapter.kill_session(self.config.tmux_session)
            await self._ssh_adapter.run("pkill -f 'vllm serve' || true")

        # SSH 터널 종료
        await self._stop_ssh_tunnel()

        self._current_status = ProviderStatus.STOPPED
        return True

    async def stop_with_instance(self) -> bool:
        """AWS Provider 중지 + EC2 인스턴스 중지

        EC2 인스턴스까지 함께 중지하여 비용을 절감합니다.

        Returns:
            성공 여부
        """
        # 기본 중지 수행
        await self.stop()

        # EC2 인스턴스 중지
        if self.config.instance_id:
            return await self._stop_instance()

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
            response = await client.get("/health", timeout=5.0)

            if response.status_code == 200:
                latency_ms = (time.time() - start_time) * 1000

                # 모델 정보 조회
                model_info = await self._get_model_info()

                # GPU 정보 조회 (SSH 모드에서만)
                gpu_info = {}
                if self._ssh_adapter:
                    gpu_info = await self._ssh_adapter.get_gpu_info()

                # EC2 상태 조회
                instance_state = await self._get_instance_state()

                return ProviderHealth(
                    status=ProviderStatus.RUNNING,
                    model=model_info.get("model", self.config.model),
                    latency_ms=latency_ms,
                    gpu_memory_used=gpu_info.get("memory_used_mb"),
                    gpu_memory_total=gpu_info.get("memory_total_mb"),
                    extra={
                        "instance_id": self.config.instance_id,
                        "instance_state": instance_state,
                        "model_info": model_info,
                        "gpu_info": gpu_info,
                    },
                )

            return ProviderHealth(
                status=ProviderStatus.ERROR,
                error_message=f"Health check failed: {response.status_code}",
            )

        except httpx.ConnectError:
            return ProviderHealth(
                status=ProviderStatus.STOPPED,
                error_message="Connection refused (SSH tunnel or vLLM not running)",
            )
        except httpx.TimeoutException:
            return ProviderHealth(
                status=ProviderStatus.STOPPED,
                error_message="Health check timeout",
            )
        except Exception as e:
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
        """채팅 완성 (non-streaming)"""
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

        # vLLM guided decoding 옵션
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
        """채팅 완성 (streaming)"""
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
                    continue

    async def close(self) -> None:
        """리소스 정리"""
        await self._stop_ssh_tunnel()

        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
            self._http_client = None

    def __repr__(self) -> str:
        return f"<AWSProvider instance_id={self.config.instance_id} region={self.config.region}>"
