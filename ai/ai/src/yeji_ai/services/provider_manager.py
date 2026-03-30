"""다중 LLM Provider 관리 및 자동 폴백 메커니즘.

이 모듈은 여러 LLM Provider를 관리하고, Circuit Breaker 패턴을 사용하여
장애 발생 시 자동으로 백업 Provider로 전환합니다.

Example:
    >>> manager = ProviderManager()
    >>> manager.add_provider(VLLMProvider(vllm_config), priority=1)
    >>> manager.add_provider(OpenAIProvider(openai_config), priority=2)
    >>> response = await manager.chat(messages, config)
"""

from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import UTC, datetime

import structlog

from yeji_ai.providers.base import (
    CompletionResponse,
    GenerationConfig,
    LLMProvider,
    ProviderStatus,
)

logger = structlog.get_logger()


@dataclass
class ProviderState:
    """Provider의 Circuit Breaker 상태를 추적합니다.

    Attributes:
        failures: 연속 실패 횟수
        last_failure: 마지막 실패 시각
        is_open: Circuit breaker가 열려 있는지 여부 (True면 일시 차단)
        last_success: 마지막 성공 시각
    """

    failures: int = 0
    last_failure: datetime | None = None
    is_open: bool = False
    last_success: datetime | None = None


class ProviderManager:
    """다중 LLM Provider를 관리하고 자동 폴백을 제공합니다.

    Circuit Breaker 패턴을 사용하여 장애가 발생한 Provider를 일시적으로
    차단하고, 설정된 시간 후 자동으로 복구를 시도합니다.

    Attributes:
        fallback_enabled: 폴백 활성화 여부
        health_check_interval: 헬스체크 간격 (초)
        circuit_breaker_threshold: Circuit breaker를 열기 위한 연속 실패 횟수
        circuit_breaker_timeout: Circuit breaker 차단 해제 시간 (초)
    """

    def __init__(
        self,
        fallback_enabled: bool = True,
        health_check_interval: float = 30.0,
        circuit_breaker_threshold: int = 3,
        circuit_breaker_timeout: float = 60.0,
    ):
        """ProviderManager를 초기화합니다.

        Args:
            fallback_enabled: 자동 폴백 활성화 여부
            health_check_interval: 헬스체크 주기 (초)
            circuit_breaker_threshold: 연속 실패 임계값
            circuit_breaker_timeout: Circuit breaker 차단 해제 대기 시간 (초)
        """
        self._providers: list[tuple[int, LLMProvider]] = []  # (priority, provider)
        self._provider_states: dict[str, ProviderState] = {}
        self.fallback_enabled = fallback_enabled
        self.health_check_interval = health_check_interval
        self.circuit_breaker_threshold = circuit_breaker_threshold
        self.circuit_breaker_timeout = circuit_breaker_timeout

        logger.info(
            "provider_manager_initialized",
            fallback_enabled=fallback_enabled,
            circuit_breaker_threshold=circuit_breaker_threshold,
            circuit_breaker_timeout=circuit_breaker_timeout,
        )

    def add_provider(self, provider: LLMProvider, priority: int = 0) -> None:
        """Provider를 추가합니다.

        낮은 priority 값이 높은 우선순위를 갖습니다.
        (priority=1이 priority=2보다 먼저 시도됨)

        Args:
            provider: 추가할 LLM Provider
            priority: 우선순위 (낮을수록 우선)
        """
        self._providers.append((priority, provider))
        self._providers.sort(key=lambda x: x[0])  # 우선순위로 정렬

        self._provider_states[provider.name] = ProviderState()

        logger.info(
            "provider_added",
            provider_name=provider.name,
            priority=priority,
            total_providers=len(self._providers),
        )

    def remove_provider(self, name: str) -> None:
        """이름으로 Provider를 제거합니다.

        Args:
            name: 제거할 Provider 이름
        """
        self._providers = [
            (pri, prov) for pri, prov in self._providers if prov.name != name
        ]

        if name in self._provider_states:
            del self._provider_states[name]

        logger.info("provider_removed", provider_name=name)

    def get_healthy_provider(self) -> LLMProvider | None:
        """사용 가능한 첫 번째 건강한 Provider를 반환합니다.

        Circuit breaker가 열려 있지 않고 상태가 정상인 Provider를 찾습니다.

        Returns:
            사용 가능한 Provider 또는 None
        """
        now = datetime.now(UTC)

        for _priority, provider in self._providers:
            state = self._provider_states.get(provider.name)
            if state is None:
                continue

            # Circuit breaker가 열려 있는지 확인
            if state.is_open:
                # Timeout이 지났으면 반쯤 열림(half-open) 상태로 전환
                if state.last_failure:
                    elapsed = (now - state.last_failure).total_seconds()
                    if elapsed >= self.circuit_breaker_timeout:
                        logger.info(
                            "circuit_breaker_half_open",
                            provider_name=provider.name,
                            elapsed_seconds=elapsed,
                        )
                        state.is_open = False
                        state.failures = 0
                    else:
                        continue
                else:
                    continue

            # Provider 상태 확인 (_current_status는 모든 Provider가 가진 내부 상태)
            # status()는 async 메서드이므로 _current_status 직접 접근
            current_status = getattr(provider, "_current_status", ProviderStatus.UNKNOWN)
            if current_status in (ProviderStatus.RUNNING, ProviderStatus.UNKNOWN):
                # UNKNOWN은 아직 start() 호출 전이므로 시도 허용
                return provider

        logger.warning("no_healthy_provider_available")
        return None

    def _record_success(self, provider_name: str) -> None:
        """Provider 호출 성공을 기록합니다.

        Args:
            provider_name: Provider 이름
        """
        state = self._provider_states.get(provider_name)
        if state is None:
            return

        state.failures = 0
        state.last_success = datetime.now(UTC)
        state.is_open = False

        logger.debug("provider_success_recorded", provider_name=provider_name)

    def _record_failure(self, provider_name: str) -> None:
        """Provider 호출 실패를 기록하고 Circuit breaker를 업데이트합니다.

        Args:
            provider_name: Provider 이름
        """
        state = self._provider_states.get(provider_name)
        if state is None:
            return

        state.failures += 1
        state.last_failure = datetime.now(UTC)

        # Circuit breaker 임계값 도달 시 차단
        if state.failures >= self.circuit_breaker_threshold:
            state.is_open = True
            logger.warning(
                "circuit_breaker_opened",
                provider_name=provider_name,
                failures=state.failures,
                threshold=self.circuit_breaker_threshold,
            )
        else:
            logger.debug(
                "provider_failure_recorded",
                provider_name=provider_name,
                failures=state.failures,
                threshold=self.circuit_breaker_threshold,
            )

    async def chat(
        self,
        messages: list[dict[str, str]],
        config: GenerationConfig | None = None,
    ) -> CompletionResponse:
        """LLM 채팅 완료 요청을 실행합니다 (자동 폴백 포함).

        Primary provider가 실패하면 fallback_enabled가 True일 때
        자동으로 다음 우선순위의 provider를 시도합니다.

        Args:
            messages: 채팅 메시지 리스트
            config: 생성 설정 (None이면 기본값 사용)

        Returns:
            LLM 응답

        Raises:
            RuntimeError: 모든 Provider가 실패한 경우
        """
        last_error: Exception | None = None

        for priority, provider in self._providers:
            # Circuit breaker 확인
            provider_healthy = self.get_healthy_provider()
            if provider_healthy is None or provider_healthy.name != provider.name:
                continue

            try:
                logger.info(
                    "provider_chat_attempt",
                    provider_name=provider.name,
                    priority=priority,
                )

                response = await provider.chat(messages, config)
                self._record_success(provider.name)

                return response

            except Exception as e:
                last_error = e
                self._record_failure(provider.name)

                logger.warning(
                    "provider_chat_failed",
                    provider_name=provider.name,
                    error=str(e),
                    error_type=type(e).__name__,
                )

                # 폴백이 비활성화되어 있으면 바로 예외 발생
                if not self.fallback_enabled:
                    raise

                # 다음 provider로 폴백 시도
                continue

        # 모든 Provider가 실패
        logger.error(
            "all_providers_failed",
            total_providers=len(self._providers),
            last_error=str(last_error) if last_error else None,
        )

        raise RuntimeError(
            f"모든 Provider가 실패했습니다. 마지막 오류: {last_error}"
        )

    async def chat_stream(
        self,
        messages: list[dict[str, str]],
        config: GenerationConfig | None = None,
    ) -> AsyncIterator[str]:
        """LLM 스트리밍 채팅을 실행합니다 (자동 폴백 포함).

        Args:
            messages: 채팅 메시지 리스트
            config: 생성 설정 (None이면 기본값 사용)

        Yields:
            스트리밍 응답 청크

        Raises:
            RuntimeError: 모든 Provider가 실패한 경우
        """
        last_error: Exception | None = None

        for priority, provider in self._providers:
            # Circuit breaker 확인
            provider_healthy = self.get_healthy_provider()
            if provider_healthy is None or provider_healthy.name != provider.name:
                continue

            try:
                logger.info(
                    "provider_chat_stream_attempt",
                    provider_name=provider.name,
                    priority=priority,
                )

                async for chunk in provider.chat_stream(messages, config):
                    yield chunk

                self._record_success(provider.name)
                return  # 성공적으로 완료

            except Exception as e:
                last_error = e
                self._record_failure(provider.name)

                logger.warning(
                    "provider_chat_stream_failed",
                    provider_name=provider.name,
                    error=str(e),
                    error_type=type(e).__name__,
                )

                # 폴백이 비활성화되어 있으면 바로 예외 발생
                if not self.fallback_enabled:
                    raise

                # 다음 provider로 폴백 시도
                continue

        # 모든 Provider가 실패
        logger.error(
            "all_providers_stream_failed",
            total_providers=len(self._providers),
            last_error=str(last_error) if last_error else None,
        )

        raise RuntimeError(
            f"모든 Provider가 실패했습니다. 마지막 오류: {last_error}"
        )

    def get_provider_status(self) -> dict[str, dict]:
        """모든 Provider의 상태를 반환합니다.

        Returns:
            Provider별 상태 정보 딕셔너리
        """
        status = {}
        for priority, provider in self._providers:
            state = self._provider_states.get(provider.name)
            current_status = getattr(provider, "_current_status", ProviderStatus.UNKNOWN)
            status[provider.name] = {
                "priority": priority,
                "status": current_status.value,
                "failures": state.failures if state else 0,
                "is_open": state.is_open if state else False,
                "last_success": (
                    state.last_success.isoformat() if state and state.last_success else None
                ),
                "last_failure": (
                    state.last_failure.isoformat() if state and state.last_failure else None
                ),
            }
        return status
