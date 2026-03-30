"""SSH Adapter - 원격 서버 커맨드 실행

로컬에서 SSH를 통해 원격 서버(ultra4 등)의 vLLM 서버를 제어합니다.
WSL 내부 커맨드 실행도 지원합니다.
"""

import asyncio
import logging
import shlex
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class SSHConfig:
    """SSH 연결 설정"""

    host: str  # SSH 호스트 (예: ultra4, 100.114.13.51)
    user: str = "user"  # SSH 사용자
    port: int = 22  # SSH 포트
    identity_file: str | None = None  # 키 파일 경로 (예: ~/.ssh/id_rsa)
    use_wsl: bool = False  # WSL 내부 커맨드 실행 여부
    wsl_distro: str = "Ubuntu"  # WSL 배포판 이름
    connect_timeout: int = 10  # 연결 타임아웃 (초)
    command_timeout: int = 60  # 커맨드 실행 타임아웃 (초)
    extra_options: dict[str, str] = field(default_factory=dict)


@dataclass
class CommandResult:
    """커맨드 실행 결과"""

    stdout: str
    stderr: str
    return_code: int
    success: bool
    command: str
    elapsed_ms: float | None = None

    @property
    def output(self) -> str:
        """stdout 또는 stderr 반환"""
        return self.stdout if self.stdout else self.stderr


class SSHAdapter:
    """SSH를 통한 원격 커맨드 실행 어댑터

    사용 예시:
        # ultra4 vLLM 서버 제어
        ssh = SSHAdapter(SSHConfig(host="ultra4", user="user", use_wsl=True))
        result = await ssh.run("source ~/venvs/vllm/bin/activate && vllm serve ...")

        # AWS EC2 vLLM 서버 제어
        ssh = SSHAdapter(SSHConfig(
            host="3.36.89.31",
            user="ubuntu",
            identity_file="~/.ssh/yeji-gpu-key.pem"
        ))
        result = await ssh.run("tmux send-keys -t vllm 'vllm serve ...' Enter")
    """

    def __init__(self, config: SSHConfig):
        self.config = config
        self._connection_tested = False

    def _build_ssh_command(self, remote_command: str) -> list[str]:
        """SSH 커맨드 빌드

        Args:
            remote_command: 원격에서 실행할 커맨드

        Returns:
            로컬에서 실행할 SSH 커맨드 리스트
        """
        cmd = ["ssh"]

        # SSH 옵션
        cmd.extend(["-o", "StrictHostKeyChecking=no"])
        cmd.extend(["-o", f"ConnectTimeout={self.config.connect_timeout}"])
        cmd.extend(["-o", "BatchMode=yes"])  # 비대화형 모드

        if self.config.identity_file:
            cmd.extend(["-i", self.config.identity_file])

        if self.config.port != 22:
            cmd.extend(["-p", str(self.config.port)])

        # 추가 옵션
        for key, value in self.config.extra_options.items():
            cmd.extend(["-o", f"{key}={value}"])

        # 호스트
        cmd.append(f"{self.config.user}@{self.config.host}")

        # WSL 래핑
        if self.config.use_wsl:
            # Windows에서 WSL 내부 커맨드 실행
            wsl_command = (
                f"wsl -d {self.config.wsl_distro} -- bash -lc "
                f"{shlex.quote(remote_command)}"
            )
            cmd.append(wsl_command)
        else:
            cmd.append(remote_command)

        return cmd

    async def run(
        self,
        command: str,
        timeout: int | None = None,
        capture_output: bool = True,
    ) -> CommandResult:
        """원격 커맨드 실행

        Args:
            command: 실행할 커맨드
            timeout: 타임아웃 (초), None이면 config 기본값 사용
            capture_output: 출력 캡처 여부

        Returns:
            커맨드 실행 결과
        """
        import time

        timeout = timeout or self.config.command_timeout
        ssh_cmd = self._build_ssh_command(command)

        logger.debug(f"SSH 커맨드 실행: {' '.join(ssh_cmd)}")

        start_time = time.time()

        try:
            process = await asyncio.create_subprocess_exec(
                *ssh_cmd,
                stdout=asyncio.subprocess.PIPE if capture_output else None,
                stderr=asyncio.subprocess.PIPE if capture_output else None,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout,
                )
            except TimeoutError:
                process.kill()
                await process.wait()
                return CommandResult(
                    stdout="",
                    stderr=f"Command timed out after {timeout}s",
                    return_code=-1,
                    success=False,
                    command=command,
                    elapsed_ms=(time.time() - start_time) * 1000,
                )

            elapsed_ms = (time.time() - start_time) * 1000

            stdout_str = stdout.decode("utf-8", errors="replace") if stdout else ""
            stderr_str = stderr.decode("utf-8", errors="replace") if stderr else ""

            return CommandResult(
                stdout=stdout_str,
                stderr=stderr_str,
                return_code=process.returncode or 0,
                success=process.returncode == 0,
                command=command,
                elapsed_ms=elapsed_ms,
            )

        except FileNotFoundError:
            return CommandResult(
                stdout="",
                stderr="SSH client not found. Install OpenSSH.",
                return_code=-1,
                success=False,
                command=command,
            )
        except Exception as e:
            logger.exception(f"SSH 커맨드 실행 실패: {e}")
            return CommandResult(
                stdout="",
                stderr=str(e),
                return_code=-1,
                success=False,
                command=command,
            )

    async def test_connection(self) -> bool:
        """SSH 연결 테스트

        Returns:
            연결 성공 여부
        """
        result = await self.run("echo 'connection_ok'", timeout=10)
        self._connection_tested = result.success and "connection_ok" in result.stdout
        return self._connection_tested

    async def run_background(
        self,
        command: str,
        session_name: str = "vllm",
    ) -> CommandResult:
        """tmux 세션에서 백그라운드 커맨드 실행

        Args:
            command: 실행할 커맨드
            session_name: tmux 세션 이름

        Returns:
            커맨드 실행 결과
        """
        # tmux 세션 생성 또는 재사용
        create_cmd = (
            f"tmux has-session -t {session_name} 2>/dev/null || "
            f"tmux new-session -d -s {session_name}"
        )
        await self.run(create_cmd)

        # 커맨드 전송
        send_cmd = f"tmux send-keys -t {session_name} {shlex.quote(command)} Enter"
        return await self.run(send_cmd)

    async def kill_session(self, session_name: str = "vllm") -> CommandResult:
        """tmux 세션 종료

        Args:
            session_name: tmux 세션 이름

        Returns:
            커맨드 실행 결과
        """
        return await self.run(f"tmux kill-session -t {session_name} 2>/dev/null || true")

    async def get_session_output(
        self,
        session_name: str = "vllm",
        lines: int = 50,
    ) -> str:
        """tmux 세션 출력 가져오기

        Args:
            session_name: tmux 세션 이름
            lines: 가져올 라인 수

        Returns:
            세션 출력
        """
        result = await self.run(f"tmux capture-pane -t {session_name} -p -S -{lines}")
        return result.stdout if result.success else ""

    async def check_process(self, process_name: str) -> bool:
        """프로세스 실행 여부 확인

        Args:
            process_name: 프로세스 이름 (예: "vllm")

        Returns:
            실행 중 여부
        """
        result = await self.run(f"pgrep -f {shlex.quote(process_name)}")
        return result.success and bool(result.stdout.strip())

    async def get_gpu_info(self) -> dict[str, Any]:
        """GPU 정보 조회 (nvidia-smi)

        Returns:
            GPU 메모리 사용량 등
        """
        result = await self.run(
            "nvidia-smi --query-gpu=memory.used,memory.total,utilization.gpu "
            "--format=csv,noheader,nounits"
        )

        if not result.success:
            return {"error": result.stderr}

        try:
            parts = result.stdout.strip().split(",")
            if len(parts) >= 3:
                return {
                    "memory_used_mb": float(parts[0].strip()),
                    "memory_total_mb": float(parts[1].strip()),
                    "gpu_utilization": float(parts[2].strip()),
                }
        except (ValueError, IndexError):
            pass

        return {"raw": result.stdout}

    def __repr__(self) -> str:
        return f"<SSHAdapter host={self.config.host} user={self.config.user}>"
