"""Intent Classifier 서비스 (태스크 #98)

임베딩 기반 의도 분류기.
gte-multilingual-base 모델을 사용하여 사용자 입력의 의도를 분류합니다.

참조: docs/design/l4-intent-deployment.md
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING

import structlog

from yeji_ai.models.enums.intent import IntentCategory

logger = structlog.get_logger()


if TYPE_CHECKING:
    from yeji_ai.services.filter.loader import LoadedIntentModel


@dataclass
class IntentPrediction:
    """Intent 분류 예측 결과"""

    intent: IntentCategory
    confidence: float
    matched_examples: list[str]
    latency_ms: float


# 인텐트별 대표 예시 문장
INTENT_EXAMPLES: dict[IntentCategory, list[str]] = {
    IntentCategory.FORTUNE_GENERAL: [
        "오늘 운세 알려줘",
        "내 사주가 어떻게 되나요?",
        "팔자 좀 봐줘",
        "운세를 알고 싶어요",
        "내 운명이 궁금해",
        "점 좀 봐줘",
    ],
    IntentCategory.FORTUNE_LOVE: [
        "연애운이 궁금해요",
        "결혼운은 어때?",
        "이성운 봐줘",
        "남자친구랑 궁합이 어떻게 되나요?",
        "사랑운이 알고 싶어",
        "올해 연애가 될까?",
        "애인이 생길까요?",
    ],
    IntentCategory.FORTUNE_CAREER: [
        "취업운 알려줘",
        "이직할까요?",
        "승진이 될까?",
        "사업운은 어때요?",
        "직장운이 궁금해",
        "창업하면 잘 될까?",
        "면접 잘 볼 수 있을까?",
    ],
    IntentCategory.FORTUNE_MONEY: [
        "금전운이 궁금해요",
        "재물운 알려줘",
        "돈이 들어올까?",
        "복권 당첨될까요?",
        "투자 운세 봐줘",
        "올해 돈 많이 벌까?",
        "재운이 어떻게 되나요?",
    ],
    IntentCategory.FORTUNE_HEALTH: [
        "건강운이 어때요?",
        "수명은 얼마나 될까?",
        "질병운 봐줘",
        "건강이 걱정돼요",
        "사고수가 있을까?",
        "건강하게 살 수 있을까?",
    ],
    IntentCategory.FORTUNE_ACADEMIC: [
        "시험운 봐줘",
        "수능 잘 볼까요?",
        "자격증 합격할 수 있을까?",
        "학업운이 궁금해",
        "유학 가면 좋을까?",
        "공부운 어때요?",
        "대학 갈 수 있을까?",
    ],
    IntentCategory.FORTUNE_INTERPERSONAL: [
        "대인관계운이 어때요?",
        "친구운 봐줘",
        "가족관계가 어떻게 될까?",
        "인간관계 운세 알려줘",
        "사람들과 잘 지낼 수 있을까?",
    ],
    IntentCategory.GREETING: [
        "안녕하세요",
        "반가워요",
        "안녕",
        "하이",
        "처음 뵙겠습니다",
        "누구세요?",
        "자기소개 해줘",
    ],
    IntentCategory.FOLLOWUP: [
        "더 자세히 알려줘",
        "왜 그래?",
        "무슨 말이야?",
        "그게 무슨 뜻이에요?",
        "요약해줘",
        "다시 설명해줘",
        "좀 더 구체적으로",
    ],
    IntentCategory.OUT_OF_DOMAIN_ALLOWED: [
        "오늘 날씨 어때?",
        "점심 뭐 먹을까?",
        "심심해",
        "기분이 안 좋아",
        "재밌는 얘기 해줘",
    ],
    IntentCategory.OUT_OF_DOMAIN_REJECTED: [
        "파이썬 코드 짜줘",
        "영어 번역해줘",
        "오늘 뉴스 알려줘",
        "수학 문제 풀어줘",
        "맛집 추천해줘",
        "레시피 알려줘",
        "코딩 도와줘",
    ],
}


class IntentClassifierService:
    """임베딩 기반 Intent 분류 서비스

    gte-multilingual-base 모델로 사용자 입력과
    인텐트별 예시 문장 간의 유사도를 계산하여 분류합니다.
    """

    def __init__(
        self,
        loaded_model: LoadedIntentModel,
        threshold: float = 0.7,
        timeout: float = 0.5,
    ) -> None:
        """Intent 분류기 초기화

        Args:
            loaded_model: 로드된 Intent 모델
            threshold: 분류 신뢰도 임계값 (0.0~1.0)
            timeout: 추론 타임아웃 (초)
        """
        self._model = loaded_model.model
        self._model_id = loaded_model.model_id
        self._threshold = threshold
        self._timeout = timeout

        self._intent_embeddings: dict[IntentCategory, list] = {}
        self._precompute_embeddings()

        logger.info(
            "intent_classifier_service_init",
            model_id=self._model_id,
            threshold=threshold,
            timeout=timeout,
            num_intents=len(self._intent_embeddings),
        )

    def _precompute_embeddings(self) -> None:
        """인텐트별 예시 문장 임베딩 사전 계산"""
        logger.debug("precomputing_intent_embeddings")

        for intent, examples in INTENT_EXAMPLES.items():
            embeddings = self._model.encode(examples, convert_to_tensor=True)
            self._intent_embeddings[intent] = embeddings

        logger.debug(
            "intent_embeddings_computed",
            num_intents=len(self._intent_embeddings),
        )

    async def predict(self, text: str) -> IntentPrediction:
        """사용자 입력의 인텐트 분류

        Args:
            text: 분류할 텍스트

        Returns:
            Intent 분류 결과
        """
        start_time = time.perf_counter()

        try:
            result = await asyncio.wait_for(
                self._run_inference(text),
                timeout=self._timeout,
            )
            result.latency_ms = (time.perf_counter() - start_time) * 1000

            logger.debug(
                "intent_prediction",
                intent=result.intent.value,
                confidence=round(result.confidence, 4),
                latency_ms=round(result.latency_ms, 2),
            )

            return result

        except TimeoutError:
            latency_ms = (time.perf_counter() - start_time) * 1000
            logger.warning(
                "intent_timeout",
                timeout=self._timeout,
                latency_ms=round(latency_ms, 2),
            )
            return IntentPrediction(
                intent=IntentCategory.FORTUNE_GENERAL,
                confidence=0.0,
                matched_examples=[],
                latency_ms=latency_ms,
            )

        except Exception as e:
            latency_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                "intent_prediction_error",
                error=str(e),
                error_type=type(e).__name__,
            )
            return IntentPrediction(
                intent=IntentCategory.FORTUNE_GENERAL,
                confidence=0.0,
                matched_examples=[],
                latency_ms=latency_ms,
            )

    async def _run_inference(self, text: str) -> IntentPrediction:
        """실제 추론 실행"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._inference_sync, text)

    def _inference_sync(self, text: str) -> IntentPrediction:
        """동기 추론 실행"""
        from sentence_transformers import util

        input_embedding = self._model.encode(text, convert_to_tensor=True)

        best_intent = IntentCategory.FORTUNE_GENERAL
        best_score = 0.0
        matched_examples: list[str] = []

        for intent, example_embeddings in self._intent_embeddings.items():
            similarities = util.cos_sim(input_embedding, example_embeddings)
            max_sim = similarities.max().item()

            if max_sim > best_score:
                best_score = max_sim
                best_intent = intent

                max_idx = similarities.argmax().item()
                matched_examples = [INTENT_EXAMPLES[intent][max_idx]]

        if best_score < self._threshold:
            logger.debug(
                "intent_low_confidence",
                best_intent=best_intent.value,
                best_score=round(best_score, 4),
                threshold=self._threshold,
            )
            if self._has_fortune_keywords(text):
                best_intent = IntentCategory.FORTUNE_GENERAL
            else:
                best_intent = IntentCategory.OUT_OF_DOMAIN_ALLOWED

        return IntentPrediction(
            intent=best_intent,
            confidence=best_score,
            matched_examples=matched_examples,
            latency_ms=0.0,
        )

    def _has_fortune_keywords(self, text: str) -> bool:
        """운세 관련 키워드 포함 여부 확인"""
        fortune_keywords = [
            "운세",
            "사주",
            "팔자",
            "점",
            "운명",
            "궁합",
            "재운",
            "금전",
            "연애",
            "취업",
            "건강",
            "시험",
            "별자리",
            "타로",
        ]
        return any(kw in text for kw in fortune_keywords)

    @property
    def threshold(self) -> float:
        """분류 신뢰도 임계값"""
        return self._threshold

    @threshold.setter
    def threshold(self, value: float) -> None:
        """분류 신뢰도 임계값 설정"""
        if not 0.0 <= value <= 1.0:
            raise ValueError("threshold는 0.0~1.0 사이여야 합니다")
        self._threshold = value
        logger.info("intent_threshold_updated", threshold=value)


def create_intent_classifier_service(
    loaded_model: LoadedIntentModel,
    threshold: float = 0.7,
    timeout: float = 0.5,
) -> IntentClassifierService:
    """Intent Classifier 서비스 팩토리"""
    return IntentClassifierService(
        loaded_model=loaded_model,
        threshold=threshold,
        timeout=timeout,
    )
