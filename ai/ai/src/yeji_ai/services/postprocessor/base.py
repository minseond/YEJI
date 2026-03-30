"""후처리기 기본 Protocol 및 타입 정의

모든 후처리기가 구현해야 하는 인터페이스와 공통 타입을 정의합니다.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol, runtime_checkable


class PostprocessErrorType(str, Enum):
    """후처리 에러 타입

    각 에러 타입은 후처리 파이프라인의 특정 단계에서 발생하는 문제를 나타냅니다.
    """

    JSON_PARSE = "json_parse"
    """JSON 파싱 실패"""

    STRUCTURE_CONVERT = "structure"
    """구조 변환 실패 (예: 객체 -> 배열)"""

    FIELD_FILL = "field_fill"
    """필드 기본값 채우기 실패"""

    CODE_NORMALIZE = "code_normalize"
    """코드 정규화 실패 (예: 대소문자, 유사어 매핑)"""

    KEYWORD_EXTRACT = "keyword_extract"
    """키워드 추출 실패"""

    UNKNOWN = "unknown"
    """분류되지 않은 에러"""


@dataclass
class PostprocessError:
    """후처리 단계에서 발생한 에러

    Attributes:
        step_name: 에러가 발생한 단계 이름
        error_type: 에러 타입
        message: 에러 메시지
        field_path: 문제가 발생한 필드 경로 (예: "stats.keywords")
        original_value: 문제가 된 원본 값
    """

    step_name: str
    error_type: PostprocessErrorType
    message: str
    field_path: str | None = None
    original_value: Any = None


@dataclass
class PostprocessResult:
    """후처리 결과

    파이프라인 실행 결과를 담는 데이터 클래스입니다.
    후처리 성공 여부와 관계없이 항상 결과를 반환합니다 (fail-safe).

    Attributes:
        data: 후처리된 데이터 (실패 시 원본과 동일)
        original: 원본 데이터 (변경되지 않은 상태)
        steps_applied: 성공적으로 적용된 단계 목록
        errors: 발생한 에러 목록 (단계별)
        latency_ms: 후처리 소요 시간 (밀리초)
    """

    data: dict[str, Any]
    original: dict[str, Any]
    steps_applied: list[str] = field(default_factory=list)
    errors: list[PostprocessError] = field(default_factory=list)
    latency_ms: float = 0.0

    @property
    def is_success(self) -> bool:
        """모든 단계가 에러 없이 완료되었는지 확인"""
        return len(self.errors) == 0

    @property
    def partial_success(self) -> bool:
        """일부 단계만 성공했는지 확인"""
        return len(self.steps_applied) > 0 and len(self.errors) > 0


@runtime_checkable
class ResponsePostprocessor(Protocol):
    """LLM 응답 후처리기 인터페이스

    모든 후처리기 (Western, Eastern)는 이 Protocol을 구현해야 합니다.
    Protocol을 사용하여 덕 타이핑을 지원합니다.

    사용 예시:
        class CustomPostprocessor:
            def process(self, raw: dict[str, Any]) -> dict[str, Any]:
                # 커스텀 후처리 로직
                return raw

        # Protocol 검증
        pp: ResponsePostprocessor = CustomPostprocessor()
    """

    def process(self, raw: dict[str, Any]) -> dict[str, Any]:
        """원본 LLM 응답을 후처리하여 정규화된 결과 반환

        Args:
            raw: LLM이 생성한 원본 JSON 딕셔너리

        Returns:
            후처리된 JSON 딕셔너리

        Note:
            - 처리 실패 시 원본을 그대로 반환합니다 (fail-safe)
            - 부분 실패 시 성공한 변환만 적용된 결과를 반환합니다
        """
        ...


@runtime_checkable
class PipelineStep(Protocol):
    """파이프라인 단계 인터페이스

    후처리 파이프라인의 각 단계를 나타냅니다.
    각 단계는 독립적으로 실행되며, 실패해도 다음 단계로 진행됩니다.
    """

    @property
    def name(self) -> str:
        """단계 이름 (로깅/모니터링용)

        Returns:
            고유한 단계 식별자 (예: "fill_keywords", "normalize_codes")
        """
        ...

    def transform(self, data: dict[str, Any]) -> dict[str, Any]:
        """데이터 변환 수행

        Args:
            data: 이전 단계의 출력 (또는 원본 데이터)

        Returns:
            변환된 데이터

        Raises:
            ValueError: 변환 불가능한 데이터 구조
        """
        ...


@runtime_checkable
class KeywordExtractor(Protocol):
    """키워드 추출기 인터페이스

    텍스트에서 도메인 키워드를 추출하는 기능을 정의합니다.
    주로 keywords_summary에서 keywords 배열을 생성하는 데 사용됩니다.
    """

    def extract(self, text: str) -> list[dict[str, Any]]:
        """텍스트에서 키워드 추출

        Args:
            text: 분석할 텍스트 (keywords_summary 등)

        Returns:
            추출된 키워드 목록. 각 키워드는 다음 구조를 따릅니다:
            [
                {"code": "LEADERSHIP", "label": "리더십", "weight": 0.9},
                {"code": "PASSION", "label": "열정", "weight": 0.85},
                ...
            ]

        Note:
            - 최소 2개, 최대 5개 키워드를 추출합니다
            - weight는 발견 순서에 따라 0.9, 0.85, 0.8 ... 순으로 부여됩니다
        """
        ...
