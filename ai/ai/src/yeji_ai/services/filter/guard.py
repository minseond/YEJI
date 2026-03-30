"""Prompt Guard 서비스 (태스크 #98)

Llama Prompt Guard 2 86M 모델을 사용하여 악성 프롬프트를 탐지합니다.

탐지 대상:
- 프롬프트 인젝션 (Injection)
- 탈옥 시도 (Jailbreak)
- 간접 공격 (Indirect Attack)

참조: docs/design/l4-intent-deployment.md
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING

import structlog

from yeji_ai.models.enums.intent import GuardLabel, MaliciousCategory

logger = structlog.get_logger()


if TYPE_CHECKING:
    from yeji_ai.services.filter.loader import LoadedGuardModel


@dataclass
class GuardPrediction:
    """Guard 모델 예측 결과"""

    label: GuardLabel
    is_malicious: bool
    score: float
    category: MaliciousCategory | None
    latency_ms: float


class PromptGuardService:
    """Prompt Guard 악성 탐지 서비스

    Llama Prompt Guard 2 86M 모델을 사용하여
    프롬프트 인젝션, 탈옥, 간접 공격을 탐지합니다.
    """

    LABEL_MAPPING = {
        0: GuardLabel.BENIGN,
        1: GuardLabel.MALICIOUS,
    }

    def __init__(
        self,
        loaded_model: LoadedGuardModel,
        threshold: float = 0.8,
        timeout: float = 1.0,
    ) -> None:
        """Guard 서비스 초기화

        Args:
            loaded_model: 로드된 Guard 모델
            threshold: 악성 판정 임계값 (0.0~1.0)
            timeout: 추론 타임아웃 (초)
        """
        self._model = loaded_model.model
        self._tokenizer = loaded_model.tokenizer
        self._model_id = loaded_model.model_id
        self._threshold = threshold
        self._timeout = timeout

        logger.info(
            "prompt_guard_service_init",
            model_id=self._model_id,
            threshold=threshold,
            timeout=timeout,
        )

    async def predict(self, text: str) -> GuardPrediction:
        """악성 프롬프트 여부 예측

        Args:
            text: 검사할 텍스트

        Returns:
            Guard 예측 결과
        """
        start_time = time.perf_counter()

        try:
            result = await asyncio.wait_for(
                self._run_inference(text),
                timeout=self._timeout,
            )
            result.latency_ms = (time.perf_counter() - start_time) * 1000

            logger.debug(
                "guard_prediction",
                is_malicious=result.is_malicious,
                score=round(result.score, 4),
                category=result.category.value if result.category else None,
                latency_ms=round(result.latency_ms, 2),
            )

            return result

        except TimeoutError:
            latency_ms = (time.perf_counter() - start_time) * 1000
            logger.warning(
                "guard_timeout",
                timeout=self._timeout,
                latency_ms=round(latency_ms, 2),
            )
            return GuardPrediction(
                label=GuardLabel.BENIGN,
                is_malicious=False,
                score=0.0,
                category=None,
                latency_ms=latency_ms,
            )

        except Exception as e:
            latency_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                "guard_prediction_error",
                error=str(e),
                error_type=type(e).__name__,
            )
            return GuardPrediction(
                label=GuardLabel.BENIGN,
                is_malicious=False,
                score=0.0,
                category=None,
                latency_ms=latency_ms,
            )

    async def _run_inference(self, text: str) -> GuardPrediction:
        """실제 추론 실행"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._inference_sync, text)

    def _inference_sync(self, text: str) -> GuardPrediction:
        """동기 추론 실행"""
        import torch

        inputs = self._tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
        )

        if hasattr(self._model, "device"):
            device = self._model.device
            inputs = {k: v.to(device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self._model(**inputs)
            logits = outputs.logits

        probs = torch.softmax(logits, dim=-1)
        predicted_class = torch.argmax(probs, dim=-1).item()
        malicious_prob = probs[0, 1].item()

        label = self.LABEL_MAPPING.get(predicted_class, GuardLabel.BENIGN)
        is_malicious = malicious_prob >= self._threshold

        category = None
        if is_malicious:
            category = self._estimate_malicious_category(text)

        return GuardPrediction(
            label=label,
            is_malicious=is_malicious,
            score=malicious_prob,
            category=category,
            latency_ms=0.0,
        )

    def _estimate_malicious_category(self, text: str) -> MaliciousCategory:
        """악성 카테고리 추정 (휴리스틱)"""
        text_lower = text.lower()

        jailbreak_patterns = [
            "dan 모드",
            "dan mode",
            "역할을 잊",
            "제한 없이",
            "no restrictions",
            "ignore your instructions",
            "bypass",
            "무시하고",
        ]
        if any(p in text_lower for p in jailbreak_patterns):
            return MaliciousCategory.JAILBREAK

        indirect_patterns = [
            "[[",
            "]]",
            "<!--",
            "-->",
            "ignore safety",
            "ignore previous",
        ]
        if any(p in text_lower for p in indirect_patterns):
            return MaliciousCategory.INDIRECT_ATTACK

        return MaliciousCategory.INJECTION

    @property
    def threshold(self) -> float:
        """악성 판정 임계값"""
        return self._threshold

    @threshold.setter
    def threshold(self, value: float) -> None:
        """악성 판정 임계값 설정"""
        if not 0.0 <= value <= 1.0:
            raise ValueError("threshold는 0.0~1.0 사이여야 합니다")
        self._threshold = value
        logger.info("guard_threshold_updated", threshold=value)


def create_prompt_guard_service(
    loaded_model: LoadedGuardModel,
    threshold: float = 0.8,
    timeout: float = 1.0,
) -> PromptGuardService:
    """Prompt Guard 서비스 팩토리"""
    return PromptGuardService(
        loaded_model=loaded_model,
        threshold=threshold,
        timeout=timeout,
    )
