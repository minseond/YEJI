"""GPU 기반 인텐트 필터 모듈 (태스크 #98)

L4 GPU에서 Prompt Guard + Intent Classifier를 실행하여
악성 프롬프트 탐지 및 의도 분류를 수행합니다.

주요 컴포넌트:
- ModelLoader: GPU 모델 로딩 (FP16)
- PromptGuardService: 악성 프롬프트 탐지
- IntentClassifierService: 임베딩 기반 의도 분류
- FilterPipeline: Guard -> Intent 통합 파이프라인

사용 예시:
    from yeji_ai.services.filter import FilterPipeline, get_filter_pipeline

    pipeline = get_filter_pipeline()
    result = await pipeline.filter("연애운이 궁금해요")

    if result.guard.is_malicious:
        # 악성 프롬프트 처리
        pass
    elif result.should_proceed:
        # LLM 처리 진행
        pass

참조: docs/design/l4-intent-deployment.md

주의: torch 의존성이 없는 환경에서는 이 모듈의 import가 실패합니다.
      GPU_FILTER_ENABLED=False인 경우 main.py에서 조건부 import를 사용합니다.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

# Lazy import: torch 의존성이 없는 환경에서 앱 시작 실패 방지
# 실제 사용 시점에 import됨 (main.py lifespan에서 조건부 import)
if TYPE_CHECKING:
    from yeji_ai.services.filter.guard import PromptGuardService
    from yeji_ai.services.filter.intent_classifier import IntentClassifierService
    from yeji_ai.services.filter.loader import ModelLoader
    from yeji_ai.services.filter.pipeline import (
        FilterPipeline,
        get_filter_pipeline,
        initialize_filter_pipeline,
        shutdown_filter_pipeline,
    )


def __getattr__(name: str):
    """Lazy import를 통해 torch 의존성을 실제 사용 시점까지 지연"""
    if name == "ModelLoader":
        from yeji_ai.services.filter.loader import ModelLoader

        return ModelLoader
    if name == "PromptGuardService":
        from yeji_ai.services.filter.guard import PromptGuardService

        return PromptGuardService
    if name == "IntentClassifierService":
        from yeji_ai.services.filter.intent_classifier import IntentClassifierService

        return IntentClassifierService
    if name == "FilterPipeline":
        from yeji_ai.services.filter.pipeline import FilterPipeline

        return FilterPipeline
    if name == "get_filter_pipeline":
        from yeji_ai.services.filter.pipeline import get_filter_pipeline

        return get_filter_pipeline
    if name == "initialize_filter_pipeline":
        from yeji_ai.services.filter.pipeline import initialize_filter_pipeline

        return initialize_filter_pipeline
    if name == "shutdown_filter_pipeline":
        from yeji_ai.services.filter.pipeline import shutdown_filter_pipeline

        return shutdown_filter_pipeline
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    # 모델 로더
    "ModelLoader",
    # 서비스
    "PromptGuardService",
    "IntentClassifierService",
    # 파이프라인
    "FilterPipeline",
    "get_filter_pipeline",
    "initialize_filter_pipeline",
    "shutdown_filter_pipeline",
]
