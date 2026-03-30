"""타로 후처리기

타로 스키마에 맞게 LLM 응답을 정규화합니다.

주요 기능:
- 카드 배열 정규화 (orientation, position_label, orientation_label)
- keywords 기본값 채우기
- summary 필드 기본값 채우기
- lucky 필드 기본값 채우기
"""

import copy
import time
from typing import Any

import structlog

from yeji_ai.services.postprocessor.base import (
    PostprocessError,
    PostprocessErrorType,
)
from yeji_ai.services.postprocessor.extractors import (
    get_nested_value,
    set_nested_value,
)

logger = structlog.get_logger()


# ============================================================
# 기본값 정의
# ============================================================

TAROT_DEFAULTS: dict[str, Any] = {
    "summary.overall_theme": "전체적인 운세 흐름입니다.",
    "summary.past_to_present": "과거에서 현재로의 변화입니다.",
    "summary.present_to_future": "현재에서 미래로의 전망입니다.",
    "summary.advice": "조언을 참고하세요.",
    "lucky.color": "보라색",
    "lucky.number": "7",
    "lucky.element": "물",
}

# orientation 정규화 테이블
ORIENTATION_NORMALIZE: dict[str, str] = {
    "upright": "UPRIGHT",
    "reversed": "REVERSED",
    "Upright": "UPRIGHT",
    "Reversed": "REVERSED",
    "UPRIGHT": "UPRIGHT",
    "REVERSED": "REVERSED",
    # 한글 매핑
    "정위치": "UPRIGHT",
    "역위치": "REVERSED",
}

# orientation 레이블 매핑
ORIENTATION_LABELS: dict[str, str] = {
    "UPRIGHT": "정위치",
    "REVERSED": "역위치",
}

# position 레이블 매핑 (3카드 스프레드)
POSITION_LABELS: dict[str, str] = {
    "PAST": "과거",
    "PRESENT": "현재",
    "FUTURE": "미래",
}

# 기본 키워드 (카드별 keywords 누락 시 사용)
DEFAULT_CARD_KEYWORDS: list[str] = ["해석 키워드"]


# ============================================================
# TarotPostprocessor 구현
# ============================================================


class TarotPostprocessor:
    """타로 후처리기

    타로 스키마에 맞게 LLM 응답을 정규화합니다.

    Attributes:
        default_values: 필드별 기본값 딕셔너리

    사용 예시:
        postprocessor = TarotPostprocessor()
        result = postprocessor.process(raw_llm_response)
    """

    def __init__(
        self,
        default_values: dict[str, Any] | None = None,
    ) -> None:
        """
        Args:
            default_values: 커스텀 기본값 (None이면 TAROT_DEFAULTS 사용)
        """
        self._default_values = default_values or TAROT_DEFAULTS

    def process(self, raw: dict[str, Any]) -> dict[str, Any]:
        """원본 LLM 응답을 후처리하여 정규화된 결과 반환

        Args:
            raw: LLM이 생성한 원본 JSON 딕셔너리

        Returns:
            후처리된 JSON 딕셔너리

        Note:
            처리 실패 시 원본을 그대로 반환합니다 (fail-safe)
        """
        start_time = time.perf_counter()

        try:
            data = copy.deepcopy(raw)  # 원본 보존
            steps_applied: list[str] = []
            errors: list[PostprocessError] = []

            # 단계 1: 카드 배열 정규화
            try:
                data = self._normalize_cards(data)
                steps_applied.append("normalize_cards")
            except Exception as e:
                errors.append(PostprocessError(
                    step_name="normalize_cards",
                    error_type=PostprocessErrorType.CODE_NORMALIZE,
                    message=str(e),
                ))
                logger.warning("tarot_normalize_cards_failed", error=str(e))

            # 단계 2: summary 필드 기본값 채우기
            try:
                data = self._fill_summary(data)
                steps_applied.append("fill_summary")
            except Exception as e:
                errors.append(PostprocessError(
                    step_name="fill_summary",
                    error_type=PostprocessErrorType.FIELD_FILL,
                    message=str(e),
                ))
                logger.warning("tarot_fill_summary_failed", error=str(e))

            # 단계 3: lucky 필드 기본값 채우기
            try:
                data = self._fill_lucky(data)
                steps_applied.append("fill_lucky")
            except Exception as e:
                errors.append(PostprocessError(
                    step_name="fill_lucky",
                    error_type=PostprocessErrorType.FIELD_FILL,
                    message=str(e),
                ))
                logger.warning("tarot_fill_lucky_failed", error=str(e))

            # 단계 4: 기본값 채우기 (나머지 필드)
            try:
                data = self._fill_defaults(data)
                steps_applied.append("fill_defaults")
            except Exception as e:
                errors.append(PostprocessError(
                    step_name="fill_defaults",
                    error_type=PostprocessErrorType.FIELD_FILL,
                    message=str(e),
                ))
                logger.warning("tarot_fill_defaults_failed", error=str(e))

            elapsed_ms = (time.perf_counter() - start_time) * 1000

            logger.info(
                "tarot_postprocess_complete",
                steps_applied=steps_applied,
                error_count=len(errors),
                latency_ms=round(elapsed_ms, 2),
            )

            return data

        except Exception as e:
            # 치명적 오류 발생 시 원본 반환 (fail-safe)
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                "tarot_postprocess_fatal_error",
                error=str(e),
                error_type=type(e).__name__,
                latency_ms=round(elapsed_ms, 2),
            )
            return raw

    def _normalize_cards(self, data: dict[str, Any]) -> dict[str, Any]:
        """카드 배열 정규화

        각 카드에 대해:
        - orientation 대소문자 정규화 (UPRIGHT/REVERSED)
        - position_label 자동 생성 (PAST→과거, PRESENT→현재, FUTURE→미래)
        - orientation_label 자동 생성 (UPRIGHT→정위치, REVERSED→역위치)
        - keywords 없으면 기본값 채우기

        Args:
            data: 원본 데이터

        Returns:
            카드가 정규화된 데이터
        """
        cards = data.get("cards", [])

        if not isinstance(cards, list):
            logger.warning("tarot_cards_not_list", cards_type=type(cards).__name__)
            return data

        normalized_count = 0

        for card in cards:
            if not isinstance(card, dict):
                continue

            # 1. orientation 정규화
            if "orientation" in card:
                orientation = card["orientation"]
                if isinstance(orientation, str):
                    normalized = ORIENTATION_NORMALIZE.get(
                        orientation,
                        orientation.upper()
                    )
                    if normalized != orientation:
                        card["orientation"] = normalized
                        normalized_count += 1

                    # orientation_label 자동 생성
                    if "orientation_label" not in card or not card["orientation_label"]:
                        card["orientation_label"] = ORIENTATION_LABELS.get(
                            normalized,
                            normalized
                        )

            # 2. position_label 자동 생성
            if "position" in card:
                position = card["position"]
                if isinstance(position, str):
                    # position 코드 정규화 (대문자)
                    normalized_position = position.upper()
                    if normalized_position != position:
                        card["position"] = normalized_position
                        normalized_count += 1

                    # position_label 자동 생성
                    if "position_label" not in card or not card["position_label"]:
                        card["position_label"] = POSITION_LABELS.get(
                            normalized_position,
                            normalized_position
                        )

            # 3. keywords 기본값 채우기
            if "keywords" not in card or not card["keywords"]:
                card["keywords"] = DEFAULT_CARD_KEYWORDS.copy()
                logger.debug(
                    "tarot_card_keywords_filled",
                    card_name=card.get("name", "unknown"),
                )

        if normalized_count > 0:
            logger.debug("tarot_cards_normalized", count=normalized_count)

        return data

    def _fill_summary(self, data: dict[str, Any]) -> dict[str, Any]:
        """summary 필드 기본값 채우기

        summary 객체 내 필수 필드들을 확인하고 누락된 경우 기본값을 채웁니다.
        - overall_theme: 전체 주제
        - past_to_present: 과거→현재 흐름
        - present_to_future: 현재→미래 흐름
        - advice: 조언

        Args:
            data: 원본 데이터

        Returns:
            summary가 채워진 데이터
        """
        if "summary" not in data:
            data["summary"] = {}

        summary = data["summary"]
        filled_count = 0

        # 필수 필드 목록
        required_fields = {
            "overall_theme": "전체적인 운세 흐름입니다.",
            "past_to_present": "과거에서 현재로의 변화입니다.",
            "present_to_future": "현재에서 미래로의 전망입니다.",
            "advice": "조언을 참고하세요.",
        }

        for field, default_value in required_fields.items():
            if field not in summary or not summary[field]:
                summary[field] = default_value
                filled_count += 1

        if filled_count > 0:
            logger.debug("tarot_summary_fields_filled", count=filled_count)

        return data

    def _fill_lucky(self, data: dict[str, Any]) -> dict[str, Any]:
        """lucky 필드 기본값 채우기

        lucky 객체 내 필수 필드들을 확인하고 누락된 경우 기본값을 채웁니다.
        - color: 행운의 색상
        - number: 행운의 숫자
        - element: 행운의 원소
        - timing: 타이밍 (선택적)

        Args:
            data: 원본 데이터

        Returns:
            lucky가 채워진 데이터
        """
        if "lucky" not in data:
            data["lucky"] = {}

        lucky = data["lucky"]
        filled_count = 0

        # 필수 필드 목록
        required_fields = {
            "color": "보라색",
            "number": "7",
            "element": "물",
        }

        for field, default_value in required_fields.items():
            if field not in lucky or not lucky[field]:
                lucky[field] = default_value
                filled_count += 1

        # timing은 선택적 (None 허용)
        if "timing" not in lucky:
            lucky["timing"] = None

        if filled_count > 0:
            logger.debug("tarot_lucky_fields_filled", count=filled_count)

        return data

    def _fill_defaults(self, data: dict[str, Any]) -> dict[str, Any]:
        """필수 필드 기본값 채우기

        누락되거나 빈 필드에 기본값을 채웁니다.

        Args:
            data: 원본 데이터

        Returns:
            기본값이 채워진 데이터
        """
        fields_filled = 0

        for path, default_value in self._default_values.items():
            current_value = get_nested_value(data, path)

            # 값이 없거나 빈 문자열인 경우 기본값 적용
            if current_value is None or current_value == "":
                set_nested_value(data, path, default_value)
                fields_filled += 1

        if fields_filled > 0:
            logger.debug("tarot_defaults_filled", count=fields_filled)

        return data
