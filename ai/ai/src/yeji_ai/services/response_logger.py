"""LLM 응답 로깅 서비스

AI Server 응답을 JSONL 파일로 저장하여 평가/최적화에 활용합니다.
비동기 로깅으로 성능 영향을 최소화합니다.
"""

import asyncio
import json
import uuid
from datetime import date, datetime
from pathlib import Path
from typing import Any

import structlog

from yeji_ai.models.logging import (
    LLMResponseLog,
    LogStatus,
    RequestInput,
    TokenUsage,
    ValidationResult,
)

logger = structlog.get_logger()


class ResponseLogger:
    """LLM 응답 로거

    JSONL 형식으로 응답을 저장하며, 일별 로테이션을 지원합니다.
    비동기 큐를 사용하여 로깅이 메인 요청 처리를 지연시키지 않습니다.

    사용 예시:
        logger = ResponseLogger(base_dir="logs/llm_responses")
        await logger.start()

        await logger.log_success(
            fortune_type="eastern",
            request_input={...},
            raw_response="...",
            parsed_response={...},
            latency_ms=1500,
        )

        await logger.stop()
    """

    def __init__(
        self,
        base_dir: str | Path = "logs/llm_responses",
        queue_size: int = 1000,
        flush_interval: float = 5.0,
    ):
        """
        초기화

        Args:
            base_dir: 로그 파일 저장 기본 디렉토리
            queue_size: 비동기 큐 최대 크기 (넘치면 경고 후 드롭)
            flush_interval: 파일 플러시 간격 (초)
        """
        self._base_dir = Path(base_dir)
        self._queue_size = queue_size
        self._flush_interval = flush_interval

        # 비동기 큐 및 태스크
        self._queue: asyncio.Queue[LLMResponseLog | None] = asyncio.Queue(maxsize=queue_size)
        self._worker_task: asyncio.Task | None = None
        self._running = False

        # 현재 로그 파일 핸들 (일별 로테이션)
        self._current_date: date | None = None
        self._current_file: Path | None = None

    @property
    def base_dir(self) -> Path:
        """로그 기본 디렉토리"""
        return self._base_dir

    def _ensure_directory(self) -> None:
        """로그 디렉토리 생성"""
        self._base_dir.mkdir(parents=True, exist_ok=True)

    def _get_log_file_path(self, log_date: date) -> Path:
        """일별 로그 파일 경로 반환

        형식: logs/llm_responses/2025-01-30.jsonl
        """
        filename = f"{log_date.isoformat()}.jsonl"
        return self._base_dir / filename

    def _rotate_if_needed(self) -> None:
        """날짜 변경 시 로그 파일 로테이션"""
        today = date.today()
        if self._current_date != today:
            self._current_date = today
            self._current_file = self._get_log_file_path(today)
            logger.info(
                "response_logger_rotated",
                log_file=str(self._current_file),
                date=today.isoformat(),
            )

    async def start(self) -> None:
        """로거 시작 (백그라운드 워커 실행)"""
        if self._running:
            logger.warning("response_logger_already_running")
            return

        self._ensure_directory()
        self._running = True
        self._worker_task = asyncio.create_task(self._worker())
        logger.info(
            "response_logger_started",
            base_dir=str(self._base_dir),
            queue_size=self._queue_size,
        )

    async def stop(self) -> None:
        """로거 정지 (잔여 로그 플러시 후 종료)"""
        if not self._running:
            return

        self._running = False

        # 종료 신호 전송 (None)
        await self._queue.put(None)

        # 워커 태스크 종료 대기
        if self._worker_task is not None:
            await self._worker_task
            self._worker_task = None

        logger.info("response_logger_stopped")

    async def _worker(self) -> None:
        """백그라운드 로그 처리 워커

        큐에서 로그를 가져와 파일에 기록합니다.
        """
        buffer: list[LLMResponseLog] = []
        last_flush = datetime.utcnow()

        while True:
            try:
                # 타임아웃으로 주기적 플러시 보장
                try:
                    log_entry = await asyncio.wait_for(
                        self._queue.get(), timeout=self._flush_interval
                    )
                except TimeoutError:
                    log_entry = None  # 타임아웃 → 플러시만 수행

                # 종료 신호
                if log_entry is None and not self._running:
                    # 잔여 버퍼 플러시 후 종료
                    if buffer:
                        await self._flush_buffer(buffer)
                    break

                # 유효한 로그 엔트리 → 버퍼에 추가
                if log_entry is not None:
                    buffer.append(log_entry)

                # 플러시 조건: 버퍼가 차거나, 간격 경과
                now = datetime.utcnow()
                time_elapsed = (now - last_flush).total_seconds()
                should_flush = len(buffer) >= 100 or time_elapsed >= self._flush_interval

                if buffer and should_flush:
                    await self._flush_buffer(buffer)
                    buffer = []
                    last_flush = now

            except Exception as e:
                logger.error(
                    "response_logger_worker_error",
                    error=str(e),
                    exc_info=True,
                )
                # 에러 발생해도 계속 실행 (로깅 실패가 서비스 중단 유발하면 안 됨)
                await asyncio.sleep(1.0)

    async def _flush_buffer(self, buffer: list[LLMResponseLog]) -> None:
        """버퍼의 로그 엔트리들을 파일에 기록

        동기 파일 I/O를 별도 스레드에서 실행합니다.
        """
        if not buffer:
            return

        self._rotate_if_needed()

        def _write_sync() -> None:
            """동기 파일 쓰기 (스레드풀에서 실행)"""
            assert self._current_file is not None
            with open(self._current_file, "a", encoding="utf-8") as f:
                for entry in buffer:
                    # Pydantic 모델을 JSON 문자열로 직렬화
                    json_str = entry.model_dump_json()
                    f.write(json_str + "\n")

        # 블로킹 I/O를 스레드풀에서 실행
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, _write_sync)

        logger.debug(
            "response_logger_flushed",
            count=len(buffer),
            file=str(self._current_file),
        )

    def _generate_request_id(self) -> str:
        """고유 요청 ID 생성 (UUID4)"""
        return str(uuid.uuid4())

    def _build_request_input(self, birth_data: dict[str, Any]) -> RequestInput:
        """요청 입력 데이터 구조화"""
        return RequestInput(
            birth_year=birth_data.get("birth_year", 0),
            birth_month=birth_data.get("birth_month", 0),
            birth_day=birth_data.get("birth_day", 0),
            birth_hour=birth_data.get("birth_hour"),
            birth_minute=birth_data.get("birth_minute"),
            gender=birth_data.get("gender"),
            latitude=birth_data.get("latitude"),
            longitude=birth_data.get("longitude"),
        )

    async def log_success(
        self,
        fortune_type: str,
        request_input: dict[str, Any],
        raw_response: str,
        parsed_response: dict[str, Any],
        latency_ms: int,
        attempt_number: int = 1,
        max_retries: int = 2,
        model_name: str | None = None,
        temperature: float | None = None,
        token_usage: dict[str, int] | None = None,
    ) -> str:
        """성공 응답 로깅

        Args:
            fortune_type: 운세 타입 (eastern/western/full)
            request_input: 요청 입력 데이터
            raw_response: LLM 원본 응답
            parsed_response: 파싱된 응답 dict
            latency_ms: 응답 레이턴시 (ms)
            attempt_number: 현재 시도 횟수
            max_retries: 최대 재시도 설정
            model_name: LLM 모델명
            temperature: 생성 온도
            token_usage: 토큰 사용량 dict

        Returns:
            request_id: 생성된 요청 ID
        """
        request_id = self._generate_request_id()

        log_entry = LLMResponseLog(
            request_id=request_id,
            fortune_type=fortune_type,  # type: ignore
            request_input=self._build_request_input(request_input),
            raw_response=raw_response,
            parsed_response=parsed_response,
            validation=ValidationResult(status=LogStatus.SUCCESS),
            latency_ms=latency_ms,
            attempt_number=attempt_number,
            max_retries=max_retries,
            model_name=model_name,
            temperature=temperature,
            token_usage=TokenUsage(**token_usage) if token_usage else None,
        )

        await self._enqueue(log_entry)
        return request_id

    async def log_validation_error(
        self,
        fortune_type: str,
        request_input: dict[str, Any],
        raw_response: str,
        error_message: str,
        validation_errors: list[dict[str, Any]] | None = None,
        latency_ms: int = 0,
        attempt_number: int = 1,
        max_retries: int = 2,
        model_name: str | None = None,
        temperature: float | None = None,
    ) -> str:
        """검증 에러 로깅

        Args:
            fortune_type: 운세 타입
            request_input: 요청 입력 데이터
            raw_response: LLM 원본 응답
            error_message: 에러 메시지
            validation_errors: Pydantic 검증 에러 목록
            latency_ms: 응답 레이턴시
            attempt_number: 현재 시도 횟수
            max_retries: 최대 재시도 설정
            model_name: LLM 모델명
            temperature: 생성 온도

        Returns:
            request_id: 생성된 요청 ID
        """
        request_id = self._generate_request_id()

        # JSON 파싱 시도
        parsed_response: dict[str, Any] | None = None
        try:
            parsed_response = json.loads(raw_response)
        except (json.JSONDecodeError, TypeError):
            pass

        log_entry = LLMResponseLog(
            request_id=request_id,
            fortune_type=fortune_type,  # type: ignore
            request_input=self._build_request_input(request_input),
            raw_response=raw_response,
            parsed_response=parsed_response,
            validation=ValidationResult(
                status=LogStatus.VALIDATION_ERROR,
                error_type="ValidationError",
                error_message=error_message,
                validation_errors=validation_errors,
            ),
            latency_ms=latency_ms,
            attempt_number=attempt_number,
            max_retries=max_retries,
            model_name=model_name,
            temperature=temperature,
        )

        await self._enqueue(log_entry)
        return request_id

    async def log_json_parse_error(
        self,
        fortune_type: str,
        request_input: dict[str, Any],
        raw_response: str,
        error_message: str,
        latency_ms: int = 0,
        attempt_number: int = 1,
        max_retries: int = 2,
        model_name: str | None = None,
        temperature: float | None = None,
    ) -> str:
        """JSON 파싱 에러 로깅

        Args:
            fortune_type: 운세 타입
            request_input: 요청 입력 데이터
            raw_response: LLM 원본 응답
            error_message: 파싱 에러 메시지
            latency_ms: 응답 레이턴시
            attempt_number: 현재 시도 횟수
            max_retries: 최대 재시도 설정
            model_name: LLM 모델명
            temperature: 생성 온도

        Returns:
            request_id: 생성된 요청 ID
        """
        request_id = self._generate_request_id()

        log_entry = LLMResponseLog(
            request_id=request_id,
            fortune_type=fortune_type,  # type: ignore
            request_input=self._build_request_input(request_input),
            raw_response=raw_response,
            parsed_response=None,
            validation=ValidationResult(
                status=LogStatus.JSON_PARSE_ERROR,
                error_type="JSONDecodeError",
                error_message=error_message,
            ),
            latency_ms=latency_ms,
            attempt_number=attempt_number,
            max_retries=max_retries,
            model_name=model_name,
            temperature=temperature,
        )

        await self._enqueue(log_entry)
        return request_id

    async def log_connection_error(
        self,
        fortune_type: str,
        request_input: dict[str, Any],
        error_message: str,
        attempt_number: int = 1,
        max_retries: int = 2,
        model_name: str | None = None,
        temperature: float | None = None,
    ) -> str:
        """연결 에러 로깅

        Args:
            fortune_type: 운세 타입
            request_input: 요청 입력 데이터
            error_message: 연결 에러 메시지
            attempt_number: 현재 시도 횟수
            max_retries: 최대 재시도 설정
            model_name: LLM 모델명
            temperature: 생성 온도

        Returns:
            request_id: 생성된 요청 ID
        """
        request_id = self._generate_request_id()

        log_entry = LLMResponseLog(
            request_id=request_id,
            fortune_type=fortune_type,  # type: ignore
            request_input=self._build_request_input(request_input),
            raw_response=None,
            parsed_response=None,
            validation=ValidationResult(
                status=LogStatus.CONNECTION_ERROR,
                error_type="ConnectError",
                error_message=error_message,
            ),
            latency_ms=0,
            attempt_number=attempt_number,
            max_retries=max_retries,
            model_name=model_name,
            temperature=temperature,
        )

        await self._enqueue(log_entry)
        return request_id

    async def log_timeout_error(
        self,
        fortune_type: str,
        request_input: dict[str, Any],
        error_message: str,
        attempt_number: int = 1,
        max_retries: int = 2,
        model_name: str | None = None,
        temperature: float | None = None,
    ) -> str:
        """타임아웃 에러 로깅

        Args:
            fortune_type: 운세 타입
            request_input: 요청 입력 데이터
            error_message: 타임아웃 에러 메시지
            attempt_number: 현재 시도 횟수
            max_retries: 최대 재시도 설정
            model_name: LLM 모델명
            temperature: 생성 온도

        Returns:
            request_id: 생성된 요청 ID
        """
        request_id = self._generate_request_id()

        log_entry = LLMResponseLog(
            request_id=request_id,
            fortune_type=fortune_type,  # type: ignore
            request_input=self._build_request_input(request_input),
            raw_response=None,
            parsed_response=None,
            validation=ValidationResult(
                status=LogStatus.TIMEOUT_ERROR,
                error_type="TimeoutException",
                error_message=error_message,
            ),
            latency_ms=0,
            attempt_number=attempt_number,
            max_retries=max_retries,
            model_name=model_name,
            temperature=temperature,
        )

        await self._enqueue(log_entry)
        return request_id

    async def log_unknown_error(
        self,
        fortune_type: str,
        request_input: dict[str, Any],
        error_type: str,
        error_message: str,
        raw_response: str | None = None,
        latency_ms: int = 0,
        attempt_number: int = 1,
        max_retries: int = 2,
        model_name: str | None = None,
        temperature: float | None = None,
    ) -> str:
        """알 수 없는 에러 로깅

        Args:
            fortune_type: 운세 타입
            request_input: 요청 입력 데이터
            error_type: 에러 클래스명
            error_message: 에러 메시지
            raw_response: LLM 원본 응답 (있는 경우)
            latency_ms: 응답 레이턴시
            attempt_number: 현재 시도 횟수
            max_retries: 최대 재시도 설정
            model_name: LLM 모델명
            temperature: 생성 온도

        Returns:
            request_id: 생성된 요청 ID
        """
        request_id = self._generate_request_id()

        log_entry = LLMResponseLog(
            request_id=request_id,
            fortune_type=fortune_type,  # type: ignore
            request_input=self._build_request_input(request_input),
            raw_response=raw_response,
            parsed_response=None,
            validation=ValidationResult(
                status=LogStatus.UNKNOWN_ERROR,
                error_type=error_type,
                error_message=error_message,
            ),
            latency_ms=latency_ms,
            attempt_number=attempt_number,
            max_retries=max_retries,
            model_name=model_name,
            temperature=temperature,
        )

        await self._enqueue(log_entry)
        return request_id

    async def _enqueue(self, log_entry: LLMResponseLog) -> None:
        """로그 엔트리를 큐에 추가

        큐가 가득 차면 경고 로그 후 드롭합니다 (서비스 안정성 우선).
        """
        if not self._running:
            logger.warning(
                "response_logger_not_running",
                request_id=log_entry.request_id,
            )
            return

        try:
            self._queue.put_nowait(log_entry)
        except asyncio.QueueFull:
            logger.warning(
                "response_logger_queue_full",
                request_id=log_entry.request_id,
                dropped=True,
            )


# ============================================================
# 글로벌 로거 인스턴스 (싱글톤)
# ============================================================

_global_response_logger: ResponseLogger | None = None


def get_response_logger() -> ResponseLogger:
    """글로벌 ResponseLogger 인스턴스 반환

    서비스 전역에서 동일한 로거 인스턴스를 사용합니다.
    """
    global _global_response_logger
    if _global_response_logger is None:
        _global_response_logger = ResponseLogger()
    return _global_response_logger


async def initialize_response_logger(
    base_dir: str | Path = "logs/llm_responses",
) -> ResponseLogger:
    """글로벌 ResponseLogger 초기화 및 시작

    애플리케이션 시작 시 호출합니다.

    Args:
        base_dir: 로그 저장 디렉토리

    Returns:
        초기화된 ResponseLogger 인스턴스
    """
    global _global_response_logger
    if _global_response_logger is not None:
        await _global_response_logger.stop()

    _global_response_logger = ResponseLogger(base_dir=base_dir)
    await _global_response_logger.start()
    return _global_response_logger


async def shutdown_response_logger() -> None:
    """글로벌 ResponseLogger 종료

    애플리케이션 종료 시 호출합니다.
    """
    global _global_response_logger
    if _global_response_logger is not None:
        await _global_response_logger.stop()
        _global_response_logger = None
