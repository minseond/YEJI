"""서양 점성술 후처리기

WesternFortuneDataV2 스키마에 맞게 LLM 응답을 정규화합니다.

주요 기능:
- FR-001: keywords_summary에서 keywords 추출
- FR-002: 필수 필드 기본값 채우기
- FR-003: 구조 변환 (객체 -> 배열)
- FR-004: 코드 정규화 (대소문자, 유사어 매핑)
- FR-005: summary 필드 괄호 안 영문 코드 제거
- FR-007: 서버 계산 통계 강제 적용 (원소/양태 분포)
"""

import copy
import re
import time
from typing import Any

import structlog

from yeji_ai.engine.saju_calculator import SajuCalculator
from yeji_ai.services.postprocessor.base import (
    KeywordExtractor,
    PostprocessError,
    PostprocessErrorType,
    PostprocessResult,
)
from yeji_ai.services.postprocessor.extractors import (
    DefaultKeywordExtractor,
    get_nested_value,
    set_nested_value,
)

logger = structlog.get_logger()


# ============================================================
# 기본값 정의
# ============================================================

WESTERN_DEFAULTS: dict[str, Any] = {
    "stats.element_summary": "원소 분석 결과입니다.",
    "stats.modality_summary": "양태 분석 결과입니다.",
    "stats.keywords_summary": "키워드 분석 결과입니다.",
    "fortune_content.overview": "오늘의 운세입니다.",
    "fortune_content.advice": "조언을 참고하세요.",
    "lucky.color": "보라색",
    "lucky.number": "3",
}

# 4원소 코드 정규화 테이블
ELEMENT_CODE_NORMALIZE: dict[str, str] = {
    "fire": "FIRE",
    "earth": "EARTH",
    "air": "AIR",
    "water": "WATER",
    "Fire": "FIRE",
    "Earth": "EARTH",
    "Air": "AIR",
    "Water": "WATER",
    # 한글 매핑
    "불": "FIRE",
    "흙": "EARTH",
    "공기": "AIR",
    "물": "WATER",
}

# 4원소 레이블 매핑
ELEMENT_LABELS: dict[str, str] = {
    "FIRE": "불",
    "EARTH": "흙",
    "AIR": "공기",
    "WATER": "물",
}

# 3양태 코드 정규화 테이블
MODALITY_CODE_NORMALIZE: dict[str, str] = {
    "cardinal": "CARDINAL",
    "fixed": "FIXED",
    "mutable": "MUTABLE",
    "Cardinal": "CARDINAL",
    "Fixed": "FIXED",
    "Mutable": "MUTABLE",
    # 유사어 매핑
    "flexible": "MUTABLE",
    "circular": "CARDINAL",
    # 한글 매핑
    "활동": "CARDINAL",
    "고정": "FIXED",
    "변동": "MUTABLE",
}

# 3양태 레이블 매핑
MODALITY_LABELS: dict[str, str] = {
    "CARDINAL": "활동",
    "FIXED": "고정",
    "MUTABLE": "변동",
}

# keywords 기본값 (최소 3개 보장용)
DEFAULT_KEYWORDS: list[dict[str, Any]] = [
    {"code": "CREATIVITY", "label": "창의적", "weight": 0.8},
    {"code": "PASSION", "label": "열정적", "weight": 0.75},
    {"code": "STABILITY", "label": "성실함", "weight": 0.7},
    {"code": "INTUITION", "label": "직관적", "weight": 0.65},
]

# keywords 최소 개수
MIN_KEYWORDS_COUNT = 3

# 12별자리 코드 정규화 테이블
# LLM이 출력하는 다양한 형식을 표준 코드로 매핑
ZODIAC_CODE_NORMALIZE: dict[str, str] = {
    # 영문 소문자
    "aries": "ARIES",
    "taurus": "TAURUS",
    "gemini": "GEMINI",
    "cancer": "CANCER",
    "leo": "LEO",
    "virgo": "VIRGO",
    "libra": "LIBRA",
    "scorpio": "SCORPIO",
    "sagittarius": "SAGITTARIUS",
    "capricorn": "CAPRICORN",
    "aquarius": "AQUARIUS",
    "pisces": "PISCES",
    # 영문 대문자 (이미 정규화됨)
    "ARIES": "ARIES",
    "TAURUS": "TAURUS",
    "GEMINI": "GEMINI",
    "CANCER": "CANCER",
    "LEO": "LEO",
    "VIRGO": "VIRGO",
    "LIBRA": "LIBRA",
    "SCORPIO": "SCORPIO",
    "SAGITTARIUS": "SAGITTARIUS",
    "CAPRICORN": "CAPRICORN",
    "AQUARIUS": "AQUARIUS",
    "PISCES": "PISCES",
    # 영문 첫글자 대문자
    "Aries": "ARIES",
    "Taurus": "TAURUS",
    "Gemini": "GEMINI",
    "Cancer": "CANCER",
    "Leo": "LEO",
    "Virgo": "VIRGO",
    "Libra": "LIBRA",
    "Scorpio": "SCORPIO",
    "Sagittarius": "SAGITTARIUS",
    "Capricorn": "CAPRICORN",
    "Aquarius": "AQUARIUS",
    "Pisces": "PISCES",
    # 한글 매핑
    "양자리": "ARIES",
    "황소자리": "TAURUS",
    "쌍둥이자리": "GEMINI",
    "게자리": "CANCER",
    "사자자리": "LEO",
    "처녀자리": "VIRGO",
    "천칭자리": "LIBRA",
    "전갈자리": "SCORPIO",
    "사수자리": "SAGITTARIUS",
    "염소자리": "CAPRICORN",
    "물병자리": "AQUARIUS",
    "물고기자리": "PISCES",
    # 한글 축약형 (자리 없이)
    "양": "ARIES",
    "황소": "TAURUS",
    "쌍둥이": "GEMINI",
    "게": "CANCER",
    "사자": "LEO",
    "처녀": "VIRGO",
    "천칭": "LIBRA",
    "전갈": "SCORPIO",
    "사수": "SAGITTARIUS",
    "염소": "CAPRICORN",
    "물병": "AQUARIUS",
    "물고기": "PISCES",
}

# 12별자리 한글 레이블 매핑
ZODIAC_LABELS: dict[str, str] = {
    "ARIES": "양자리",
    "TAURUS": "황소자리",
    "GEMINI": "쌍둥이자리",
    "CANCER": "게자리",
    "LEO": "사자자리",
    "VIRGO": "처녀자리",
    "LIBRA": "천칭자리",
    "SCORPIO": "전갈자리",
    "SAGITTARIUS": "사수자리",
    "CAPRICORN": "염소자리",
    "AQUARIUS": "물병자리",
    "PISCES": "물고기자리",
}

# 별자리 → 원소 매핑 (서버 계산값 덮어쓰기용)
ZODIAC_ELEMENT_MAP: dict[str, str] = {
    "ARIES": "FIRE",
    "LEO": "FIRE",
    "SAGITTARIUS": "FIRE",
    "TAURUS": "EARTH",
    "VIRGO": "EARTH",
    "CAPRICORN": "EARTH",
    "GEMINI": "AIR",
    "LIBRA": "AIR",
    "AQUARIUS": "AIR",
    "CANCER": "WATER",
    "SCORPIO": "WATER",
    "PISCES": "WATER",
}


# ============================================================
# 별자리 정규화 함수
# ============================================================


def normalize_zodiac_sign(value: str | None) -> str | None:
    """별자리 문자열을 표준 코드로 정규화

    LLM이 출력하는 다양한 형식의 별자리 문자열을 표준 코드로 변환합니다.
    지원하는 형식:
    - 영문 대문자: "AQUARIUS"
    - 영문 소문자: "aquarius"
    - 영문 첫글자 대문자: "Aquarius"
    - 한글 전체: "물병자리"
    - 한글 축약: "물병"

    Args:
        value: 정규화할 별자리 문자열 (None이면 None 반환)

    Returns:
        표준 별자리 코드 (예: "AQUARIUS") 또는 None
        매핑되지 않는 값은 대문자로 변환하여 반환

    Examples:
        >>> normalize_zodiac_sign("물병자리")
        'AQUARIUS'
        >>> normalize_zodiac_sign("aquarius")
        'AQUARIUS'
        >>> normalize_zodiac_sign(None)
        None
    """
    if value is None:
        return None

    # 공백 제거 후 매핑 테이블 조회
    stripped = value.strip()
    if stripped in ZODIAC_CODE_NORMALIZE:
        return ZODIAC_CODE_NORMALIZE[stripped]

    # 매핑에 없는 경우 대문자로 변환하여 반환
    return stripped.upper()


# ============================================================
# WesternPostprocessor 구현
# ============================================================


class WesternPostprocessor:
    """서양 점성술 후처리기

    WesternFortuneDataV2 스키마에 맞게 LLM 응답을 정규화합니다.

    Attributes:
        keyword_extractor: 키워드 추출기 인스턴스
        default_values: 필드별 기본값 딕셔너리

    사용 예시:
        postprocessor = WesternPostprocessor()
        result = postprocessor.process(raw_llm_response)
    """

    def __init__(
        self,
        keyword_extractor: KeywordExtractor | None = None,
        default_values: dict[str, Any] | None = None,
    ) -> None:
        """
        Args:
            keyword_extractor: 키워드 추출기 (None이면 기본 추출기 사용)
            default_values: 커스텀 기본값 (None이면 WESTERN_DEFAULTS 사용)
        """
        self._keyword_extractor = keyword_extractor or DefaultKeywordExtractor()
        self._default_values = default_values or WESTERN_DEFAULTS

    def process(
        self,
        raw: dict[str, Any],
        calculated_zodiac: str | None = None,
    ) -> dict[str, Any]:
        """원본 LLM 응답을 후처리하여 정규화된 결과 반환

        Args:
            raw: LLM이 생성한 원본 JSON 딕셔너리
            calculated_zodiac: 서버에서 계산된 별자리 코드 (예: "ARIES")
                LLM이 잘못된 별자리를 생성한 경우 이 값으로 덮어씁니다.

        Returns:
            후처리된 JSON 딕셔너리

        Note:
            처리 실패 시 원본을 그대로 반환합니다 (fail-safe)
        """
        start_time = time.perf_counter()
        data = copy.deepcopy(raw)  # 원본 보존
        steps_applied: list[str] = []
        errors: list[PostprocessError] = []

        # 단계 1: 구조 변환 (FR-003)
        try:
            data = self._convert_structures(data)
            steps_applied.append("convert_structures")
        except Exception as e:
            errors.append(PostprocessError(
                step_name="convert_structures",
                error_type=PostprocessErrorType.STRUCTURE_CONVERT,
                message=str(e),
            ))
            logger.warning("western_structure_convert_failed", error=str(e))

        # 단계 2: 코드 정규화 (FR-004)
        try:
            data = self._normalize_codes(data)
            steps_applied.append("normalize_codes")
        except Exception as e:
            errors.append(PostprocessError(
                step_name="normalize_codes",
                error_type=PostprocessErrorType.CODE_NORMALIZE,
                message=str(e),
            ))
            logger.warning("western_code_normalize_failed", error=str(e))

        # 단계 3: summary 필드 영문 코드 제거 (FR-005)
        try:
            data = self._clean_summary_fields(data)
            steps_applied.append("clean_summary_fields")
        except Exception as e:
            errors.append(PostprocessError(
                step_name="clean_summary_fields",
                error_type=PostprocessErrorType.FIELD_FILL,
                message=str(e),
            ))
            logger.warning("western_clean_summary_failed", error=str(e))

        # 단계 4: keywords 추출 (FR-001)
        try:
            data = self._fill_keywords(data)
            steps_applied.append("fill_keywords")
        except Exception as e:
            errors.append(PostprocessError(
                step_name="fill_keywords",
                error_type=PostprocessErrorType.KEYWORD_EXTRACT,
                message=str(e),
            ))
            logger.warning("western_keyword_extract_failed", error=str(e))

        # 단계 5: 기본값 채우기 (FR-002)
        try:
            data = self._fill_defaults(data)
            steps_applied.append("fill_defaults")
        except Exception as e:
            errors.append(PostprocessError(
                step_name="fill_defaults",
                error_type=PostprocessErrorType.FIELD_FILL,
                message=str(e),
            ))
            logger.warning("western_fill_defaults_failed", error=str(e))

        # 단계 6: 서버 계산값으로 별자리/원소 강제 덮어쓰기
        if calculated_zodiac:
            try:
                data = self._override_with_calculated(data, calculated_zodiac)
                steps_applied.append("override_with_calculated")
            except Exception as e:
                errors.append(PostprocessError(
                    step_name="override_with_calculated",
                    error_type=PostprocessErrorType.FIELD_FILL,
                    message=str(e),
                ))
                logger.warning("western_override_calculated_failed", error=str(e))

            # 단계 7: 서버 계산 통계 강제 적용 (FR-007)
            try:
                data = self._override_stats_with_calculated(data, calculated_zodiac)
                steps_applied.append("override_stats_with_calculated")
            except Exception as e:
                errors.append(PostprocessError(
                    step_name="override_stats_with_calculated",
                    error_type=PostprocessErrorType.FIELD_FILL,
                    message=str(e),
                ))
                logger.warning("western_override_stats_failed", error=str(e))

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        logger.info(
            "western_postprocess_complete",
            steps_applied=steps_applied,
            error_count=len(errors),
            latency_ms=round(elapsed_ms, 2),
        )

        return data

    def _override_with_calculated(
        self,
        data: dict[str, Any],
        zodiac_code: str,
    ) -> dict[str, Any]:
        """서버 계산값으로 별자리/원소 강제 덮어쓰기

        LLM이 프롬프트의 별자리를 무시하고 잘못된 값을 생성하는 문제를 해결합니다.
        후처리 마지막 단계에서 서버 계산값으로 강제 덮어씁니다.

        Args:
            data: 후처리 중인 데이터
            zodiac_code: 서버에서 계산된 별자리 코드 (예: "ARIES")

        Returns:
            별자리/원소가 덮어쓰기된 데이터
        """
        # 정규화된 별자리 코드 확보
        normalized_zodiac = zodiac_code.upper() if zodiac_code else None
        if not normalized_zodiac or normalized_zodiac not in ZODIAC_LABELS:
            logger.warning(
                "invalid_calculated_zodiac",
                zodiac_code=zodiac_code,
            )
            return data

        # stats 객체 가져오기 (없으면 생성)
        stats = data.setdefault("stats", {})

        # 기존 main_sign 값 확인 (로깅용)
        old_main_sign = stats.get("main_sign", {})
        old_code = old_main_sign.get("code") if isinstance(old_main_sign, dict) else old_main_sign

        # main_sign 덮어쓰기
        stats["main_sign"] = {
            "code": normalized_zodiac,
            "name": ZODIAC_LABELS[normalized_zodiac],
        }

        # 원소도 별자리에 맞게 덮어쓰기
        element_code = ZODIAC_ELEMENT_MAP.get(normalized_zodiac, "FIRE")
        element_label = ELEMENT_LABELS.get(element_code, "불")
        stats["element"] = {
            "code": element_code,
            "name": element_label,
        }

        # 최상위 element 필드도 덮어쓰기 (존재하는 경우)
        if "element" in data and not isinstance(data["element"], dict):
            data["element"] = element_code

        # 로깅
        if old_code and old_code != normalized_zodiac:
            logger.info(
                "zodiac_overridden",
                old_zodiac=old_code,
                new_zodiac=normalized_zodiac,
                element=element_code,
            )
        else:
            logger.debug(
                "zodiac_set",
                zodiac=normalized_zodiac,
                element=element_code,
            )

        return data

    def _override_stats_with_calculated(
        self,
        data: dict[str, Any],
        zodiac_code: str,
    ) -> dict[str, Any]:
        """서버 계산 통계로 원소/양태 분포 강제 덮어쓰기 (FR-007)

        LLM이 생성한 원소/양태 비율 대신 서버에서 정확히 계산한 값을 사용합니다.
        summary 필드는 LLM 해석을 유지합니다.

        Args:
            data: 후처리된 데이터
            zodiac_code: 별자리 코드 (예: "ARIES")

        Returns:
            통계가 덮어쓰기된 데이터
        """
        calculator = SajuCalculator()

        # 원소와 양태 계산
        element = calculator.get_zodiac_element(zodiac_code)
        modality = calculator.get_zodiac_modality(zodiac_code)

        # stats 객체 확보
        if "stats" not in data:
            data["stats"] = {}
        stats = data["stats"]

        # 1. 4원소 분포 덮어쓰기
        element_dist = []
        for elem_code in ["FIRE", "EARTH", "AIR", "WATER"]:
            percent = 50.0 if elem_code == element else 16.7
            label_map = {"FIRE": "불", "EARTH": "흙", "AIR": "공기", "WATER": "물"}
            element_dist.append({
                "code": elem_code,
                "label": label_map.get(elem_code, elem_code),
                "percent": percent,
            })

        # summary는 LLM 값 유지, element_4_distribution만 덮어쓰기
        stats["element_4_distribution"] = element_dist

        # 2. 3양태 분포 덮어쓰기
        modality_dist = []
        for mod_code in ["CARDINAL", "FIXED", "MUTABLE"]:
            percent = 50.0 if mod_code == modality else 25.0
            label_map = {"CARDINAL": "활동", "FIXED": "고정", "MUTABLE": "변동"}
            modality_dist.append({
                "code": mod_code,
                "label": label_map.get(mod_code, mod_code),
                "percent": percent,
            })

        # summary는 LLM 값 유지, modality_3_distribution만 덮어쓰기
        stats["modality_3_distribution"] = modality_dist

        logger.info(
            "western_stats_overridden_with_calculated",
            zodiac=zodiac_code,
            element=element,
            modality=modality,
        )

        return data

    def process_with_result(
        self,
        raw: dict[str, Any],
        calculated_zodiac: str | None = None,
    ) -> PostprocessResult:
        """후처리 실행 및 상세 결과 반환

        Args:
            raw: LLM이 생성한 원본 JSON 딕셔너리
            calculated_zodiac: 서버에서 계산된 별자리 코드 (예: "ARIES")

        Returns:
            PostprocessResult 객체 (상세 정보 포함)
        """
        start_time = time.perf_counter()
        original = copy.deepcopy(raw)
        data = copy.deepcopy(raw)
        steps_applied: list[str] = []
        errors: list[PostprocessError] = []

        # 각 단계 실행 (위 process와 동일 로직)
        try:
            data = self._convert_structures(data)
            steps_applied.append("convert_structures")
        except Exception as e:
            errors.append(PostprocessError(
                step_name="convert_structures",
                error_type=PostprocessErrorType.STRUCTURE_CONVERT,
                message=str(e),
            ))

        try:
            data = self._normalize_codes(data)
            steps_applied.append("normalize_codes")
        except Exception as e:
            errors.append(PostprocessError(
                step_name="normalize_codes",
                error_type=PostprocessErrorType.CODE_NORMALIZE,
                message=str(e),
            ))

        try:
            data = self._clean_summary_fields(data)
            steps_applied.append("clean_summary_fields")
        except Exception as e:
            errors.append(PostprocessError(
                step_name="clean_summary_fields",
                error_type=PostprocessErrorType.FIELD_FILL,
                message=str(e),
            ))

        try:
            data = self._fill_keywords(data)
            steps_applied.append("fill_keywords")
        except Exception as e:
            errors.append(PostprocessError(
                step_name="fill_keywords",
                error_type=PostprocessErrorType.KEYWORD_EXTRACT,
                message=str(e),
            ))

        try:
            data = self._fill_defaults(data)
            steps_applied.append("fill_defaults")
        except Exception as e:
            errors.append(PostprocessError(
                step_name="fill_defaults",
                error_type=PostprocessErrorType.FIELD_FILL,
                message=str(e),
            ))

        # 서버 계산값으로 별자리/원소 강제 덮어쓰기
        if calculated_zodiac:
            try:
                data = self._override_with_calculated(data, calculated_zodiac)
                steps_applied.append("override_with_calculated")
            except Exception as e:
                errors.append(PostprocessError(
                    step_name="override_with_calculated",
                    error_type=PostprocessErrorType.FIELD_FILL,
                    message=str(e),
                ))

            # 서버 계산 통계 강제 적용 (FR-007)
            try:
                data = self._override_stats_with_calculated(data, calculated_zodiac)
                steps_applied.append("override_stats_with_calculated")
            except Exception as e:
                errors.append(PostprocessError(
                    step_name="override_stats_with_calculated",
                    error_type=PostprocessErrorType.FIELD_FILL,
                    message=str(e),
                ))

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        return PostprocessResult(
            data=data,
            original=original,
            steps_applied=steps_applied,
            errors=errors,
            latency_ms=round(elapsed_ms, 2),
        )

    def _convert_structures(self, data: dict[str, Any]) -> dict[str, Any]:
        """구조 변환 수행 (FR-003)

        LLM이 잘못된 구조로 생성한 경우 올바른 구조로 변환합니다.
        예: 객체 형태의 분포 -> 배열 형태로 변환

        Args:
            data: 원본 데이터

        Returns:
            구조가 변환된 데이터
        """
        stats = data.get("stats", {})

        # 4원소 분포: 객체 -> 배열 변환
        element_dist = stats.get("element_4_distribution")
        if isinstance(element_dist, dict) and not isinstance(element_dist, list):
            # {"FIRE": 30, "EARTH": 25, ...} ->
            # [{"code": "FIRE", "label": "불", "percent": 30}, ...]
            converted = []
            for code, percent in element_dist.items():
                normalized_code = ELEMENT_CODE_NORMALIZE.get(code, code.upper())
                label = ELEMENT_LABELS.get(normalized_code, code)
                converted.append({
                    "code": normalized_code,
                    "label": label,
                    "percent": float(percent) if isinstance(percent, (int, float)) else 0.0,
                })
            stats["element_4_distribution"] = converted

        # 3양태 분포: 객체 -> 배열 변환
        modality_dist = stats.get("modality_3_distribution")
        if isinstance(modality_dist, dict) and not isinstance(modality_dist, list):
            converted = []
            for code, percent in modality_dist.items():
                normalized_code = MODALITY_CODE_NORMALIZE.get(code, code.upper())
                label = MODALITY_LABELS.get(normalized_code, code)
                converted.append({
                    "code": normalized_code,
                    "label": label,
                    "percent": float(percent) if isinstance(percent, (int, float)) else 0.0,
                })
            stats["modality_3_distribution"] = converted

        # detailed_analysis: 문자열 배열 -> 객체 배열 변환
        fortune_content = data.get("fortune_content", {})
        detailed = fortune_content.get("detailed_analysis")
        if isinstance(detailed, list) and len(detailed) > 0:
            if isinstance(detailed[0], str):
                # ["내용1", "내용2"] -> [{"title": "분석 1", "content": "내용1"}, ...]
                converted = []
                for i, content in enumerate(detailed):
                    converted.append({
                        "title": f"분석 {i + 1}",
                        "content": content,
                    })
                fortune_content["detailed_analysis"] = converted

        return data

    def _normalize_codes(self, data: dict[str, Any]) -> dict[str, Any]:
        """코드 정규화 수행 (FR-004)

        대소문자 통일 및 유사어 매핑을 적용합니다.
        - 원소 코드: fire -> FIRE
        - 양태 코드: cardinal -> CARDINAL
        - 별자리 코드: 물병자리, aquarius -> AQUARIUS

        Args:
            data: 원본 데이터

        Returns:
            코드가 정규화된 데이터
        """
        # 대표 별자리 코드 정규화 (main_sign)
        if "main_sign" in data:
            normalized = normalize_zodiac_sign(data["main_sign"])
            if normalized:
                original = data["main_sign"]
                data["main_sign"] = normalized
                # 레이블 자동 보정 (main_sign_label 필드가 없거나 비어있으면 채움)
                if "main_sign_label" not in data or not data["main_sign_label"]:
                    data["main_sign_label"] = ZODIAC_LABELS.get(normalized, original)
                logger.debug(
                    "zodiac_sign_normalized",
                    original=original,
                    normalized=normalized,
                )

        # 대표 원소 코드 정규화
        if "element" in data:
            element = data["element"]
            if element in ELEMENT_CODE_NORMALIZE:
                data["element"] = ELEMENT_CODE_NORMALIZE[element]
            elif isinstance(element, str):
                data["element"] = element.upper()

        stats = data.get("stats", {})

        # 4원소 분포 코드 정규화
        element_dist = stats.get("element_4_distribution", [])
        if isinstance(element_dist, list):
            for item in element_dist:
                if "code" in item:
                    code = item["code"]
                    if code in ELEMENT_CODE_NORMALIZE:
                        item["code"] = ELEMENT_CODE_NORMALIZE[code]
                    elif isinstance(code, str):
                        item["code"] = code.upper()
                    # 레이블 보정
                    if "label" not in item or not item["label"]:
                        item["label"] = ELEMENT_LABELS.get(item["code"], item["code"])

        # 3양태 분포 코드 정규화
        modality_dist = stats.get("modality_3_distribution", [])
        if isinstance(modality_dist, list):
            for item in modality_dist:
                if "code" in item:
                    code = item["code"]
                    if code in MODALITY_CODE_NORMALIZE:
                        item["code"] = MODALITY_CODE_NORMALIZE[code]
                    elif isinstance(code, str):
                        item["code"] = code.upper()
                    # 레이블 보정
                    if "label" not in item or not item["label"]:
                        item["label"] = MODALITY_LABELS.get(item["code"], item["code"])

        return data

    def _fill_keywords(self, data: dict[str, Any]) -> dict[str, Any]:
        """keywords 배열 채우기 (FR-001)

        keywords 배열이 비어있거나 누락된 경우,
        keywords_summary에서 키워드를 추출하여 채웁니다.
        최소 3개의 키워드를 보장합니다.

        Args:
            data: 원본 데이터

        Returns:
            keywords가 채워진 데이터
        """
        stats = data.get("stats", {})
        keywords = stats.get("keywords", [])

        # keywords가 비어있거나 없는 경우에만 추출
        if not keywords:
            summary = stats.get("keywords_summary", "")
            if summary:
                extracted = self._keyword_extractor.extract(summary)
                if extracted:
                    keywords = extracted
                    stats["keywords"] = keywords
                    logger.debug(
                        "keywords_filled_from_summary",
                        count=len(extracted),
                    )

        # 최소 개수 보장: keywords가 3개 미만이면 기본값 보충
        keywords = stats.get("keywords", [])
        if len(keywords) < MIN_KEYWORDS_COUNT:
            keywords = self._ensure_minimum_keywords(keywords)
            stats["keywords"] = keywords
            logger.debug(
                "keywords_padded_to_minimum",
                final_count=len(keywords),
            )

        return data

    def _ensure_minimum_keywords(
        self,
        keywords: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """keywords가 최소 개수(3개) 미만이면 기본값 보충

        기존 키워드의 code와 중복되지 않는 기본값을 추가합니다.

        Args:
            keywords: 현재 keywords 배열

        Returns:
            최소 3개가 보장된 keywords 배열
        """
        if len(keywords) >= MIN_KEYWORDS_COUNT:
            return keywords

        # 기존 키워드의 code 수집
        existing_codes = {kw.get("code") for kw in keywords if kw.get("code")}

        # 기본값에서 중복되지 않는 항목 추가
        result = list(keywords)  # 원본 복사
        for default_kw in DEFAULT_KEYWORDS:
            if len(result) >= MIN_KEYWORDS_COUNT:
                break
            if default_kw["code"] not in existing_codes:
                result.append(default_kw.copy())
                existing_codes.add(default_kw["code"])

        # 여전히 부족하면 기본값 전체 추가 (중복 허용)
        while len(result) < MIN_KEYWORDS_COUNT:
            for default_kw in DEFAULT_KEYWORDS:
                if len(result) >= MIN_KEYWORDS_COUNT:
                    break
                result.append(default_kw.copy())

        logger.info(
            "keywords_minimum_ensured",
            original_count=len(keywords),
            final_count=len(result),
        )

        return result[:4]  # 최대 4개로 제한

    def _remove_code_in_parentheses(self, text: str) -> str:
        """괄호 안 영문 코드 제거 (FR-005)

        LLM이 생성한 텍스트에서 괄호 안 영문 코드를 제거합니다.
        예: "공기(AIR)의 에너지" → "공기의 에너지"
            "고정(FIXED) 성향" → "고정 성향"

        Args:
            text: 원본 텍스트

        Returns:
            괄호 안 영문 코드가 제거된 텍스트
        """
        # 괄호 앞 공백 포함하여 영문 대문자 + 언더스코어 조합 제거
        # 패턴: 선택적 공백 + 괄호 열기 + 영문 대문자/언더스코어 + 괄호 닫기
        return re.sub(r"\s*\([A-Z_]+\)", "", text)

    def _clean_summary_fields(self, data: dict[str, Any]) -> dict[str, Any]:
        """summary 필드에서 영문 코드 제거 (FR-005)

        stats 내 *_summary 필드들에서 괄호 안 영문 코드를 제거합니다.

        Args:
            data: 원본 데이터

        Returns:
            summary 필드가 정리된 데이터
        """
        stats = data.get("stats", {})
        cleaned_count = 0

        # 정리 대상 summary 필드 목록
        summary_fields = [
            "element_summary",
            "modality_summary",
            "keywords_summary",
        ]

        for field in summary_fields:
            if field in stats and isinstance(stats[field], str):
                original = stats[field]
                cleaned = self._remove_code_in_parentheses(original)
                if original != cleaned:
                    stats[field] = cleaned
                    cleaned_count += 1
                    logger.debug(
                        "summary_code_removed",
                        field=field,
                        original=original,
                        cleaned=cleaned,
                    )

        if cleaned_count > 0:
            logger.debug("summary_fields_cleaned", count=cleaned_count)

        return data

    def _fill_defaults(self, data: dict[str, Any]) -> dict[str, Any]:
        """필수 필드 기본값 채우기 (FR-002)

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
            logger.debug("defaults_filled", count=fields_filled)

        return data
