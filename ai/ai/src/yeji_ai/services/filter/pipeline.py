"""Filter Pipeline (태스크 #98)

Guard -> Intent 통합 필터 파이프라인.
GPU 모델 기반 악성 탐지 및 의도 분류를 순차적으로 수행합니다.

참조: docs/design/l4-intent-deployment.md
"""

from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING

import structlog

from yeji_ai.config import Settings, get_settings
from yeji_ai.models.enums.intent import FilterAction, GuardLabel, IntentCategory
from yeji_ai.models.intent import (
    FilterRequest,
    FilterResult,
    GuardResult,
    IntentResult,
)
from yeji_ai.services.filter.guard import PromptGuardService, create_prompt_guard_service
from yeji_ai.services.filter.intent_classifier import (
    IntentClassifierService,
    create_intent_classifier_service,
)
from yeji_ai.services.filter.loader import (
    ModelLoader,
    log_gpu_memory_status,
)

logger = structlog.get_logger()


if TYPE_CHECKING:
    pass


class FilterPipeline:
    """GPU 기반 필터 파이프라인

    Guard(악성 탐지) -> Intent(의도 분류) 순서로
    사용자 입력을 필터링합니다.
    """

    def __init__(
        self,
        guard_service: PromptGuardService | None,
        intent_service: IntentClassifierService | None,
        settings: Settings,
    ) -> None:
        """파이프라인 초기화

        Args:
            guard_service: Guard 서비스 (None이면 비활성화)
            intent_service: Intent 서비스 (None이면 비활성화)
            settings: 애플리케이션 설정
        """
        self._guard_service = guard_service
        self._intent_service = intent_service
        self._settings = settings

        self._guard_mode = settings.guard_mode
        self._intent_mode = settings.intent_embedding_mode

        logger.info(
            "filter_pipeline_init",
            guard_enabled=guard_service is not None,
            intent_enabled=intent_service is not None,
            guard_mode=self._guard_mode,
            intent_mode=self._intent_mode,
        )

    @classmethod
    async def create(
        cls,
        settings: Settings | None = None,
    ) -> FilterPipeline:
        """파이프라인 팩토리 메서드

        Args:
            settings: 애플리케이션 설정

        Returns:
            초기화된 FilterPipeline
        """
        settings = settings or get_settings()

        guard_service = None
        intent_service = None

        if not settings.gpu_filter_enabled:
            logger.info("gpu_filter_disabled")
            return cls(
                guard_service=None,
                intent_service=None,
                settings=settings,
            )

        loader = ModelLoader(device=settings.gpu_device)

        try:
            guard_model = await loader.load_prompt_guard(
                model_id=settings.guard_model,
            )
            guard_service = create_prompt_guard_service(
                loaded_model=guard_model,
                threshold=settings.guard_threshold,
                timeout=settings.guard_timeout,
            )
        except Exception as e:
            logger.error("guard_load_failed", error=str(e))
            if settings.guard_required:
                raise
            logger.warning("guard_disabled_due_to_load_failure")

        try:
            intent_model = await loader.load_intent_classifier(
                model_id=settings.intent_embedding_model,
            )
            intent_service = create_intent_classifier_service(
                loaded_model=intent_model,
                threshold=settings.intent_embedding_threshold,
                timeout=settings.intent_embedding_timeout,
            )
        except Exception as e:
            logger.error("intent_load_failed", error=str(e))
            if settings.intent_embedding_required:
                raise
            logger.warning("intent_disabled_due_to_load_failure")

        log_gpu_memory_status()

        return cls(
            guard_service=guard_service,
            intent_service=intent_service,
            settings=settings,
        )

    async def filter(self, request: FilterRequest | str) -> FilterResult:
        """사용자 입력 필터링

        Args:
            request: 필터링 요청 또는 텍스트

        Returns:
            필터링 결과
        """
        start_time = time.perf_counter()

        if isinstance(request, str):
            if not request or not request.strip():
                return FilterResult.create_bypass()
            request = FilterRequest(text=request)

        if not self._settings.gpu_filter_enabled:
            return FilterResult.create_bypass()

        if not request.text or not request.text.strip():
            return FilterResult.create_bypass()

        text = request.text.strip()

        # P2 비동기 최적화: guard_mode가 block이 아니면 병렬 실행
        if self._guard_mode != "block":
            # 병렬 실행 (early return 필요 없음)
            guard_result, intent_result = await asyncio.gather(
                self._run_guard(text),
                self._run_intent(text),
            )
        else:
            # 직렬 실행 (early return 필요 시)
            guard_result = await self._run_guard(text)

            if guard_result.is_malicious:
                total_latency = (time.perf_counter() - start_time) * 1000
                category_label = (
                    guard_result.category.value if guard_result.category else "unknown"
                )
                return FilterResult(
                    guard=guard_result,
                    intent=self._create_empty_intent_result(guard_result.latency_ms),
                    should_proceed=False,
                    action=FilterAction.BLOCK_MALICIOUS,
                    reject_reason=f"악성 입력 감지: {category_label}",
                    total_latency_ms=total_latency,
                )

            intent_result = await self._run_intent(text)

        action, should_proceed, reject_reason = self._determine_action(
            guard_result,
            intent_result,
        )

        total_latency = (time.perf_counter() - start_time) * 1000

        result = FilterResult(
            guard=guard_result,
            intent=intent_result,
            should_proceed=should_proceed,
            action=action,
            reject_reason=reject_reason,
            total_latency_ms=total_latency,
        )

        logger.info(
            "filter_pipeline_complete",
            is_malicious=guard_result.is_malicious,
            intent=intent_result.intent.value,
            action=action.value,
            should_proceed=should_proceed,
            total_latency_ms=round(total_latency, 2),
        )

        return result

    async def _run_guard(self, text: str) -> GuardResult:
        """Guard 검사 실행"""
        if self._guard_service is None:
            return GuardResult(
                label=GuardLabel.BENIGN,
                is_malicious=False,
                score=0.0,
                category=None,
                latency_ms=0.0,
            )

        try:
            prediction = await self._guard_service.predict(text)
            return GuardResult(
                label=prediction.label,
                is_malicious=prediction.is_malicious,
                score=prediction.score,
                category=prediction.category,
                latency_ms=prediction.latency_ms,
            )
        except Exception as e:
            logger.error("guard_error", error=str(e))
            return GuardResult(
                label=GuardLabel.BENIGN,
                is_malicious=False,
                score=0.0,
                category=None,
                latency_ms=0.0,
            )

    async def _run_intent(self, text: str) -> IntentResult:
        """Intent 분류 실행"""
        if self._intent_service is None:
            return IntentResult(
                intent=IntentCategory.FORTUNE_GENERAL,
                confidence=1.0,
                matched_keywords=[],
                latency_ms=0.0,
            )

        try:
            prediction = await self._intent_service.predict(text)
            return IntentResult(
                intent=prediction.intent,
                confidence=prediction.confidence,
                matched_keywords=prediction.matched_examples,
                latency_ms=prediction.latency_ms,
            )
        except Exception as e:
            logger.error("intent_error", error=str(e))
            return IntentResult(
                intent=IntentCategory.FORTUNE_GENERAL,
                confidence=0.0,
                matched_keywords=[],
                latency_ms=0.0,
            )

    def _create_empty_intent_result(self, latency_ms: float = 0.0) -> IntentResult:
        """빈 Intent 결과 생성"""
        return IntentResult(
            intent=IntentCategory.FORTUNE_GENERAL,
            confidence=0.0,
            matched_keywords=[],
            latency_ms=latency_ms,
        )

    def _determine_action(
        self,
        guard_result: GuardResult,
        intent_result: IntentResult,
    ) -> tuple[FilterAction, bool, str | None]:
        """필터 액션 결정"""
        if guard_result.is_malicious:
            if self._guard_mode == "block":
                category_label = (
                    guard_result.category.value if guard_result.category else "unknown"
                )
                return (
                    FilterAction.BLOCK_MALICIOUS,
                    False,
                    f"악성 입력 감지: {category_label}",
                )
            logger.warning(
                "guard_malicious_logged",
                mode=self._guard_mode,
                category=guard_result.category.value if guard_result.category else None,
            )

        intent = intent_result.intent

        if intent == IntentCategory.OUT_OF_DOMAIN_REJECTED:
            if self._intent_mode == "block":
                return (
                    FilterAction.REJECT_OOD,
                    False,
                    "서비스 범위 외 요청",
                )

        if intent == IntentCategory.OUT_OF_DOMAIN_ALLOWED:
            if self._intent_mode == "block":
                return (
                    FilterAction.REJECT_OOD,
                    False,
                    "도메인 외 요청 (안내 응답)",
                )

        if intent == IntentCategory.GREETING:
            return (
                FilterAction.DIRECT_RESPONSE,
                False,
                None,
            )

        return (
            FilterAction.PROCEED,
            True,
            None,
        )

    @property
    def guard_enabled(self) -> bool:
        """Guard 활성화 여부"""
        return self._guard_service is not None

    @property
    def intent_enabled(self) -> bool:
        """Intent 활성화 여부"""
        return self._intent_service is not None


# 싱글톤 및 라이프사이클 관리

_pipeline_instance: FilterPipeline | None = None


def get_filter_pipeline() -> FilterPipeline | None:
    """필터 파이프라인 싱글톤 반환"""
    return _pipeline_instance


async def initialize_filter_pipeline(
    settings: Settings | None = None,
) -> FilterPipeline:
    """필터 파이프라인 초기화

    앱 시작 시 호출하여 GPU 모델을 로드하고 파이프라인을 초기화합니다.
    """
    global _pipeline_instance

    settings = settings or get_settings()

    if not settings.gpu_filter_enabled:
        logger.info("gpu_filter_disabled_skipping_init")
        _pipeline_instance = FilterPipeline(
            guard_service=None,
            intent_service=None,
            settings=settings,
        )
        return _pipeline_instance

    logger.info("initializing_filter_pipeline")
    _pipeline_instance = await FilterPipeline.create(settings)
    logger.info(
        "filter_pipeline_initialized",
        guard_enabled=_pipeline_instance.guard_enabled,
        intent_enabled=_pipeline_instance.intent_enabled,
    )

    return _pipeline_instance


async def shutdown_filter_pipeline() -> None:
    """필터 파이프라인 종료

    앱 종료 시 호출하여 리소스를 정리합니다.
    """
    global _pipeline_instance

    if _pipeline_instance is not None:
        logger.info("shutting_down_filter_pipeline")
        try:
            import torch

            torch.cuda.empty_cache()
            logger.info("cuda_cache_cleared")
        except ImportError:
            pass
        except Exception as e:
            logger.warning("cuda_cache_clear_error", error=str(e))

        _pipeline_instance = None
        logger.info("filter_pipeline_shutdown")
