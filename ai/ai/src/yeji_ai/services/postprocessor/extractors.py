"""키워드 추출 및 유틸리티 함수

keywords_summary 텍스트에서 도메인 키워드를 추출하는 기능을 제공합니다.
"""

from typing import Any

import structlog

logger = structlog.get_logger()


# ============================================================
# 키워드 매핑 테이블
# ============================================================

KEYWORD_MAPPING: dict[str, str] = {
    # 기본 키워드 (PRD 정의)
    "공감": "EMPATHY",
    "직관": "INTUITION",
    "상상력": "IMAGINATION",
    "경계": "BOUNDARY",
    "리더십": "LEADERSHIP",
    "열정": "PASSION",
    "분석": "ANALYSIS",
    "안정": "STABILITY",
    "소통": "COMMUNICATION",
    "혁신": "INNOVATION",
    # 확장 키워드 (domain_codes.py 기반)
    "용기": "COURAGE",
    "독립성": "INDEPENDENCE",
    "인내": "PATIENCE",
    "실용성": "PRACTICALITY",
    "호기심": "CURIOSITY",
    "적응력": "ADAPTABILITY",
    "양육": "NURTURING",
    "감수성": "SENSITIVITY",
    "창의성": "CREATIVITY",
    "자신감": "CONFIDENCE",
    "완벽주의": "PERFECTIONISM",
    "조화": "HARMONY",
    "외교": "DIPLOMACY",
    "균형": "BALANCE",
    "강렬함": "INTENSITY",
    "변화": "TRANSFORMATION",
    "모험": "ADVENTURE",
    "낙관": "OPTIMISM",
    "자유": "FREEDOM",
    "야망": "AMBITION",
    "절제": "DISCIPLINE",
    "책임감": "RESPONSIBILITY",
    "인도주의": "HUMANITARIANISM",
    "연민": "COMPASSION",
    # 추가 유사어 매핑 (LLM이 다양하게 표현할 수 있음)
    "경계 설정": "BOUNDARY",
    "분석적": "ANALYTICAL",
    "분석력": "ANALYSIS",
    "의사소통": "COMMUNICATION",
    "커뮤니케이션": "COMMUNICATION",
    "창의력": "CREATIVITY",
    "독립심": "INDEPENDENCE",
    "참을성": "PATIENCE",
    "실용": "PRACTICALITY",
    "호기": "CURIOSITY",
    "민감성": "SENSITIVITY",
    "섬세함": "SENSITIVITY",
    "자기확신": "CONFIDENCE",
    "변화 추구": "TRANSFORMATION",
    "자유로움": "FREEDOM",
    "책임": "RESPONSIBILITY",
}

# 역방향 매핑 (코드 -> 한글 레이블)
CODE_TO_LABEL: dict[str, str] = {v: k for k, v in KEYWORD_MAPPING.items()}


# ============================================================
# 키워드 추출 설정
# ============================================================

# 추출 키워드 수 제한
MIN_KEYWORDS = 2
MAX_KEYWORDS = 5

# 가중치 시작값 및 감소량
WEIGHT_START = 0.9
WEIGHT_DECREMENT = 0.05


# ============================================================
# DefaultKeywordExtractor 구현
# ============================================================


class DefaultKeywordExtractor:
    """기본 키워드 추출기

    keywords_summary 텍스트에서 한글 키워드를 탐색하고
    도메인 코드로 변환합니다.

    Attributes:
        keyword_mapping: 한글 -> 코드 매핑 딕셔너리
        min_keywords: 최소 추출 키워드 수
        max_keywords: 최대 추출 키워드 수

    사용 예시:
        extractor = DefaultKeywordExtractor()
        keywords = extractor.extract("리더십과 열정이 핵심입니다.")
        # [{"code": "LEADERSHIP", "label": "리더십", "weight": 0.9}, ...]
    """

    def __init__(
        self,
        keyword_mapping: dict[str, str] | None = None,
        min_keywords: int = MIN_KEYWORDS,
        max_keywords: int = MAX_KEYWORDS,
    ) -> None:
        """
        Args:
            keyword_mapping: 커스텀 키워드 매핑 (None이면 기본값 사용)
            min_keywords: 최소 추출 키워드 수
            max_keywords: 최대 추출 키워드 수
        """
        self._mapping = keyword_mapping or KEYWORD_MAPPING
        self._min_keywords = min_keywords
        self._max_keywords = max_keywords

    def extract(self, text: str) -> list[dict[str, Any]]:
        """텍스트에서 키워드 추출

        Args:
            text: 분석할 텍스트

        Returns:
            추출된 키워드 목록
        """
        if not text:
            logger.warning("keyword_extract_empty_text")
            return []

        found_keywords: list[dict[str, Any]] = []
        found_codes: set[str] = set()  # 중복 방지

        # 긴 키워드부터 먼저 매칭 (예: "경계 설정" 우선)
        sorted_keywords = sorted(self._mapping.keys(), key=len, reverse=True)

        for label in sorted_keywords:
            if label in text:
                code = self._mapping[label]

                # 중복 코드 방지
                if code in found_codes:
                    continue

                # 가중치 계산 (발견 순서 기반)
                weight = WEIGHT_START - (len(found_keywords) * WEIGHT_DECREMENT)
                weight = max(weight, 0.5)  # 최소 0.5 보장

                found_keywords.append({
                    "code": code,
                    "label": self._get_primary_label(code),
                    "weight": round(weight, 2),
                })
                found_codes.add(code)

                # 최대 개수 도달 시 종료
                if len(found_keywords) >= self._max_keywords:
                    break

        logger.debug(
            "keywords_extracted",
            text_length=len(text),
            keywords_found=len(found_keywords),
        )

        return found_keywords

    def _get_primary_label(self, code: str) -> str:
        """코드에 대한 대표 한글 레이블 반환

        Args:
            code: 도메인 코드 (예: "LEADERSHIP")

        Returns:
            한글 레이블 (예: "리더십")
        """
        # 역방향 매핑에서 찾기
        if code in CODE_TO_LABEL:
            return CODE_TO_LABEL[code]

        # 없으면 코드를 소문자로 변환하여 반환
        return code.lower().replace("_", " ")


# ============================================================
# 유틸리티 함수
# ============================================================


def extract_first_json(text: str) -> dict[str, Any]:
    """텍스트에서 첫 번째 완전한 JSON 객체 추출

    LLM이 JSON 이후 추가 텍스트를 생성하는 경우를 처리합니다.

    Args:
        text: LLM 원본 응답 텍스트

    Returns:
        파싱된 JSON 딕셔너리

    Raises:
        ValueError: 유효한 JSON을 찾을 수 없는 경우
    """
    import json

    depth = 0
    start = -1

    for i, char in enumerate(text):
        if char == "{":
            if depth == 0:
                start = i
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0 and start != -1:
                try:
                    return json.loads(text[start : i + 1])
                except json.JSONDecodeError:
                    # 파싱 실패 시 다음 JSON 블록 시도
                    start = -1
                    continue

    raise ValueError("유효한 JSON을 찾을 수 없습니다")


def get_nested_value(data: dict[str, Any], path: str) -> Any:
    """중첩된 딕셔너리에서 경로로 값 조회

    Args:
        data: 딕셔너리
        path: 점으로 구분된 경로 (예: "stats.keywords_summary")

    Returns:
        해당 경로의 값 (없으면 None)
    """
    keys = path.split(".")
    current = data

    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return None

    return current


def set_nested_value(data: dict[str, Any], path: str, value: Any) -> dict[str, Any]:
    """중첩된 딕셔너리에서 경로로 값 설정

    Args:
        data: 딕셔너리 (원본이 수정됨)
        path: 점으로 구분된 경로
        value: 설정할 값

    Returns:
        수정된 딕셔너리
    """
    keys = path.split(".")
    current = data

    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]

    current[keys[-1]] = value
    return data
