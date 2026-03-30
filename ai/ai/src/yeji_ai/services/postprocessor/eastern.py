"""동양 사주 후처리기

SajuDataV2 스키마에 맞게 LLM 응답을 정규화합니다.

주요 기능:
- FR-002: 필수 필드 기본값 채우기
- FR-003: 구조 변환 (오행/십신 객체 -> 배열)
- FR-004: 코드 정규화 (천간지지, 오행 코드)
- FR-007: 서버 계산 통계 강제 적용 (오행/음양/십신 분포)
"""

import copy
import time
from typing import Any

import structlog

from yeji_ai.engine.saju_calculator import SajuCalculator
from yeji_ai.models.saju import FourPillars
from yeji_ai.services.postprocessor.base import (
    PostprocessError,
    PostprocessErrorType,
    PostprocessResult,
)
from yeji_ai.services.postprocessor.extractors import (
    get_nested_value,
    set_nested_value,
)

logger = structlog.get_logger()


# ============================================================
# 기본값 정의
# ============================================================

EASTERN_DEFAULTS: dict[str, Any] = {
    "chart.summary": "사주 분석 결과입니다.",
    "stats.five_elements.summary": "오행 분포 분석입니다.",
    "stats.yin_yang_ratio.summary": "음양 균형 분석입니다.",
    "stats.ten_gods.summary": "십신 분포 분석입니다.",
    "final_verdict.summary": "종합 분석 결과입니다.",
    "final_verdict.strength": "강점을 분석 중입니다.",
    "final_verdict.weakness": "보완점을 분석 중입니다.",
    "final_verdict.advice": "조언을 준비 중입니다.",
    "lucky.color": "파란색",
    "lucky.number": "7",
    "lucky.item": "행운의 물건",
}

# 오행 코드 정규화 테이블
ELEMENT_CODE_NORMALIZE: dict[str, str] = {
    "wood": "WOOD",
    "fire": "FIRE",
    "earth": "EARTH",
    "metal": "METAL",
    "water": "WATER",
    "Wood": "WOOD",
    "Fire": "FIRE",
    "Earth": "EARTH",
    "Metal": "METAL",
    "Water": "WATER",
    # 한글 매핑
    "목": "WOOD",
    "화": "FIRE",
    "토": "EARTH",
    "금": "METAL",
    "수": "WATER",
}

# 오행 레이블 매핑
ELEMENT_LABELS: dict[str, str] = {
    "WOOD": "목",
    "FIRE": "화",
    "EARTH": "토",
    "METAL": "금",
    "WATER": "수",
}

# 십신 코드 정규화 테이블
TEN_GOD_CODE_NORMALIZE: dict[str, str] = {
    # 소문자/혼합 케이스 -> 대문자
    "bi_gyeon": "BI_GYEON",
    "gang_jae": "GANG_JAE",
    "sik_sin": "SIK_SIN",
    "sang_gwan": "SANG_GWAN",
    "pyeon_jae": "PYEON_JAE",
    "jeong_jae": "JEONG_JAE",
    "pyeon_gwan": "PYEON_GWAN",
    "jeong_gwan": "JEONG_GWAN",
    "pyeon_in": "PYEON_IN",
    "jeong_in": "JEONG_IN",
    "etc": "ETC",
    # 한글 매핑
    "비견": "BI_GYEON",
    "겁재": "GANG_JAE",
    "식신": "SIK_SIN",
    "상관": "SANG_GWAN",
    "편재": "PYEON_JAE",
    "정재": "JEONG_JAE",
    "편관": "PYEON_GWAN",
    "정관": "JEONG_GWAN",
    "편인": "PYEON_IN",
    "정인": "JEONG_IN",
    "기타": "ETC",
    # 한자 매핑 (LLM 한자 혼용 출력 대응)
    "比肩": "BI_GYEON",
    "劫財": "GANG_JAE",
    "食神": "SIK_SIN",
    "傷官": "SANG_GWAN",
    "偏財": "PYEON_JAE",
    "正財": "JEONG_JAE",
    "偏官": "PYEON_GWAN",
    "正官": "JEONG_GWAN",
    "偏印": "PYEON_IN",
    "正印": "JEONG_IN",
}

# 십신 레이블 매핑
TEN_GOD_LABELS: dict[str, str] = {
    "BI_GYEON": "비견",
    "GANG_JAE": "겁재",
    "SIK_SIN": "식신",
    "SANG_GWAN": "상관",
    "PYEON_JAE": "편재",
    "JEONG_JAE": "정재",
    "PYEON_GWAN": "편관",
    "JEONG_GWAN": "정관",
    "PYEON_IN": "편인",
    "JEONG_IN": "정인",
    "ETC": "기타",
}

# 십신 한자 → 한글 레이블 매핑 (label 필드 한자 혼용 수정용)
TEN_GOD_HANJA_TO_KR: dict[str, str] = {
    "比肩": "비견",
    "劫財": "겁재",
    "食神": "식신",
    "傷官": "상관",
    "偏財": "편재",
    "正財": "정재",
    "偏官": "편관",
    "正官": "정관",
    "偏印": "편인",
    "正印": "정인",
    # 한자 혼용 패턴 (한글+한자)
    "비肩": "비견",
    "겁財": "겁재",
    "식神": "식신",
    "상官": "상관",
    "편財": "편재",
    "정財": "정재",
    "편官": "편관",
    "정官": "정관",
    "편印": "편인",
    "정印": "정인",
}

# 천간 목록 (검증용)
CHEON_GAN: list[str] = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]

# 지지 목록 (검증용)
JI_JI: list[str] = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

# ============================================================
# 천간/지지 코드 매핑 테이블 (FR-005: 필드 자동 생성)
# ============================================================

# 천간 한자 -> 코드 매핑
GAN_TO_CODE: dict[str, str] = {
    "甲": "GAP",
    "乙": "EUL",
    "丙": "BYEONG",
    "丁": "JEONG",
    "戊": "MU",
    "己": "GI",
    "庚": "GYEONG",
    "辛": "SIN",
    "壬": "IM",
    "癸": "GYE",
}

# 지지 한자 -> 코드 매핑
JI_TO_CODE: dict[str, str] = {
    "子": "JA",
    "丑": "CHUK",
    "寅": "IN",
    "卯": "MYO",
    "辰": "JIN",
    "巳": "SA",
    "午": "O",
    "未": "MI",
    "申": "SHIN",
    "酉": "YU",
    "戌": "SUL",
    "亥": "HAE",
}

# 천간 오행 매핑 (십신 계산용)
GAN_TO_ELEMENT: dict[str, str] = {
    "甲": "WOOD", "乙": "WOOD",
    "丙": "FIRE", "丁": "FIRE",
    "戊": "EARTH", "己": "EARTH",
    "庚": "METAL", "辛": "METAL",
    "壬": "WATER", "癸": "WATER",
}

# 천간 음양 매핑 (십신 계산용)
GAN_TO_YINYANG: dict[str, str] = {
    "甲": "YANG", "乙": "YIN",
    "丙": "YANG", "丁": "YIN",
    "戊": "YANG", "己": "YIN",
    "庚": "YANG", "辛": "YIN",
    "壬": "YANG", "癸": "YIN",
}

# 오행 상생상극 관계 (십신 계산용)
# 일간 오행 기준으로 다른 오행과의 관계
# 비겁(같음), 식상(생), 재성(극), 관성(피극), 인성(생받음)
ELEMENT_RELATIONS: dict[str, dict[str, str]] = {
    "WOOD": {"WOOD": "BI", "FIRE": "SIK", "EARTH": "JAE", "METAL": "GWAN", "WATER": "IN"},
    "FIRE": {"FIRE": "BI", "EARTH": "SIK", "METAL": "JAE", "WATER": "GWAN", "WOOD": "IN"},
    "EARTH": {"EARTH": "BI", "METAL": "SIK", "WATER": "JAE", "WOOD": "GWAN", "FIRE": "IN"},
    "METAL": {"METAL": "BI", "WATER": "SIK", "WOOD": "JAE", "FIRE": "GWAN", "EARTH": "IN"},
    "WATER": {"WATER": "BI", "WOOD": "SIK", "FIRE": "JAE", "EARTH": "GWAN", "METAL": "IN"},
}

# 십신 관계 -> 코드 매핑 (음양 조합)
# (관계, 음양일치여부) -> 십신코드
TEN_GOD_MAP: dict[tuple[str, bool], str] = {
    ("BI", True): "BI_GYEON",    # 비견 (같은 오행, 같은 음양)
    ("BI", False): "GANG_JAE",   # 겁재 (같은 오행, 다른 음양)
    ("SIK", True): "SIK_SIN",    # 식신 (생하는 오행, 같은 음양)
    ("SIK", False): "SANG_GWAN", # 상관 (생하는 오행, 다른 음양)
    ("JAE", True): "PYEON_JAE",  # 편재 (극하는 오행, 같은 음양)
    ("JAE", False): "JEONG_JAE", # 정재 (극하는 오행, 다른 음양)
    ("GWAN", True): "PYEON_GWAN", # 편관 (극당하는 오행, 같은 음양)
    ("GWAN", False): "JEONG_GWAN", # 정관 (극당하는 오행, 다른 음양)
    ("IN", True): "PYEON_IN",    # 편인 (생받는 오행, 같은 음양)
    ("IN", False): "JEONG_IN",   # 정인 (생받는 오행, 다른 음양)
}


# ============================================================
# EasternPostprocessor 구현
# ============================================================


class EasternPostprocessor:
    """동양 사주 후처리기

    SajuDataV2 스키마에 맞게 LLM 응답을 정규화합니다.

    Attributes:
        default_values: 필드별 기본값 딕셔너리

    사용 예시:
        postprocessor = EasternPostprocessor()
        result = postprocessor.process(raw_llm_response)
    """

    def __init__(
        self,
        default_values: dict[str, Any] | None = None,
    ) -> None:
        """
        Args:
            default_values: 커스텀 기본값 (None이면 EASTERN_DEFAULTS 사용)
        """
        self._default_values = default_values or EASTERN_DEFAULTS

    def process(
        self,
        raw: dict[str, Any],
        calculated_saju: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """원본 LLM 응답을 후처리하여 정규화된 결과 반환

        Args:
            raw: LLM이 생성한 원본 JSON 딕셔너리
            calculated_saju: 서버에서 계산된 사주 정보 (만세력 기반)
                - year_pillar_hanja: 연주 한자 (예: "壬申")
                - month_pillar_hanja: 월주 한자 (예: "甲辰")
                - day_pillar_hanja: 일주 한자 (예: "辛未")
                - hour_pillar_hanja: 시주 한자 (예: "庚午") 또는 None

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
            logger.warning("eastern_structure_convert_failed", error=str(e))

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
            logger.warning("eastern_code_normalize_failed", error=str(e))

        # 단계 3: 사주 기둥 정규화
        try:
            data = self._normalize_pillars(data)
            steps_applied.append("normalize_pillars")
        except Exception as e:
            errors.append(PostprocessError(
                step_name="normalize_pillars",
                error_type=PostprocessErrorType.CODE_NORMALIZE,
                message=str(e),
            ))
            logger.warning("eastern_pillar_normalize_failed", error=str(e))

        # 단계 4: 천간지지 동기화
        try:
            data = self._sync_cheongan_jiji(data)
            steps_applied.append("sync_cheongan_jiji")
        except Exception as e:
            errors.append(PostprocessError(
                step_name="sync_cheongan_jiji",
                error_type=PostprocessErrorType.STRUCTURE_CONVERT,
                message=str(e),
            ))
            logger.warning("eastern_sync_cheongan_jiji_failed", error=str(e))

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
            logger.warning("eastern_fill_defaults_failed", error=str(e))

        # 단계 6: 서버 계산값으로 사주 강제 덮어쓰기 (FR-006)
        if calculated_saju:
            try:
                data = self._override_with_calculated(data, calculated_saju)
                steps_applied.append("override_with_calculated")
            except Exception as e:
                errors.append(PostprocessError(
                    step_name="override_with_calculated",
                    error_type=PostprocessErrorType.STRUCTURE_CONVERT,
                    message=str(e),
                ))
                logger.warning("eastern_override_with_calculated_failed", error=str(e))

        # 단계 7: 서버 계산 통계 강제 적용 - 오행/음양/십신 분포 (FR-007)
        if calculated_saju:
            try:
                data = self._override_stats_with_calculated(data, calculated_saju)
                steps_applied.append("override_stats_with_calculated")
            except Exception as e:
                errors.append(PostprocessError(
                    step_name="override_stats_with_calculated",
                    error_type=PostprocessErrorType.STRUCTURE_CONVERT,
                    message=str(e),
                ))
                logger.warning("eastern_override_stats_failed", error=str(e))

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        logger.info(
            "eastern_postprocess_complete",
            steps_applied=steps_applied,
            error_count=len(errors),
            latency_ms=round(elapsed_ms, 2),
        )

        return data

    def process_with_result(
        self,
        raw: dict[str, Any],
        calculated_saju: dict[str, Any] | None = None,
    ) -> PostprocessResult:
        """후처리 실행 및 상세 결과 반환

        Args:
            raw: LLM이 생성한 원본 JSON 딕셔너리
            calculated_saju: 서버에서 계산된 사주 정보 (만세력 기반)

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
            data = self._normalize_pillars(data)
            steps_applied.append("normalize_pillars")
        except Exception as e:
            errors.append(PostprocessError(
                step_name="normalize_pillars",
                error_type=PostprocessErrorType.CODE_NORMALIZE,
                message=str(e),
            ))

        try:
            data = self._sync_cheongan_jiji(data)
            steps_applied.append("sync_cheongan_jiji")
        except Exception as e:
            errors.append(PostprocessError(
                step_name="sync_cheongan_jiji",
                error_type=PostprocessErrorType.STRUCTURE_CONVERT,
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

        # 서버 계산값으로 사주 강제 덮어쓰기 (FR-006)
        if calculated_saju:
            try:
                data = self._override_with_calculated(data, calculated_saju)
                steps_applied.append("override_with_calculated")
            except Exception as e:
                errors.append(PostprocessError(
                    step_name="override_with_calculated",
                    error_type=PostprocessErrorType.STRUCTURE_CONVERT,
                    message=str(e),
                ))

        # 서버 계산 통계 강제 적용 (FR-007)
        if calculated_saju:
            try:
                data = self._override_stats_with_calculated(data, calculated_saju)
                steps_applied.append("override_stats_with_calculated")
            except Exception as e:
                errors.append(PostprocessError(
                    step_name="override_stats_with_calculated",
                    error_type=PostprocessErrorType.STRUCTURE_CONVERT,
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

        Args:
            data: 원본 데이터

        Returns:
            구조가 변환된 데이터
        """
        stats = data.get("stats", {})

        # 오행 분포: 객체 -> 배열 변환
        five_elements = stats.get("five_elements", {})
        elements_list = five_elements.get("list") or five_elements.get("elements_list")

        # {"WOOD": 20, "FIRE": 30, ...} 형태인 경우 변환
        if elements_list is None:
            # five_elements 자체가 분포 객체인 경우
            potential_dist = {
                k: v for k, v in five_elements.items()
                if k not in ("summary", "list", "elements_list") and isinstance(v, (int, float))
            }
            if potential_dist:
                converted = []
                for code, percent in potential_dist.items():
                    normalized_code = ELEMENT_CODE_NORMALIZE.get(code, code.upper())
                    label = ELEMENT_LABELS.get(normalized_code, code)
                    converted.append({
                        "code": normalized_code,
                        "label": label,
                        "percent": float(percent),
                    })
                five_elements["list"] = converted
                # 분포 키 제거
                for key in potential_dist.keys():
                    five_elements.pop(key, None)

        # 십신 분포: 객체 -> 배열 변환
        ten_gods = stats.get("ten_gods", {})
        gods_list = ten_gods.get("list") or ten_gods.get("gods_list")

        if gods_list is None:
            potential_dist = {
                k: v for k, v in ten_gods.items()
                if k not in ("summary", "list", "gods_list") and isinstance(v, (int, float))
            }
            if potential_dist:
                converted = []
                for code, percent in potential_dist.items():
                    normalized_code = TEN_GOD_CODE_NORMALIZE.get(code, code.upper())
                    label = TEN_GOD_LABELS.get(normalized_code, code)
                    converted.append({
                        "code": normalized_code,
                        "label": label,
                        "percent": float(percent),
                    })
                ten_gods["list"] = converted
                for key in potential_dist.keys():
                    ten_gods.pop(key, None)

        return data

    def _normalize_codes(self, data: dict[str, Any]) -> dict[str, Any]:
        """코드 정규화 수행 (FR-004)

        대소문자 통일 및 유사어 매핑을 적용합니다.

        Args:
            data: 원본 데이터

        Returns:
            코드가 정규화된 데이터
        """
        # 대표 오행 코드 정규화
        if "element" in data:
            element = data["element"]
            if element in ELEMENT_CODE_NORMALIZE:
                data["element"] = ELEMENT_CODE_NORMALIZE[element]
            elif isinstance(element, str):
                data["element"] = element.upper()

        stats = data.get("stats", {})

        # 오행 분포 코드 정규화
        five_elements = stats.get("five_elements", {})
        elements_list = five_elements.get("list") or five_elements.get("elements_list", [])
        if isinstance(elements_list, list):
            for item in elements_list:
                if "code" in item:
                    code = item["code"]
                    if code in ELEMENT_CODE_NORMALIZE:
                        item["code"] = ELEMENT_CODE_NORMALIZE[code]
                    elif isinstance(code, str):
                        item["code"] = code.upper()
                    # 레이블 보정
                    if "label" not in item or not item["label"]:
                        item["label"] = ELEMENT_LABELS.get(item["code"], item["code"])

        # 십신 분포 코드 정규화
        ten_gods = stats.get("ten_gods", {})
        gods_list = ten_gods.get("list") or ten_gods.get("gods_list", [])
        if isinstance(gods_list, list):
            for item in gods_list:
                if "code" in item:
                    code = item["code"]
                    if code in TEN_GOD_CODE_NORMALIZE:
                        item["code"] = TEN_GOD_CODE_NORMALIZE[code]
                    elif isinstance(code, str):
                        item["code"] = code.upper()
                    # 레이블 보정: 한자 혼용 → 한글 변환
                    label = item.get("label", "")
                    if label in TEN_GOD_HANJA_TO_KR:
                        # 한자 또는 한자 혼용 레이블을 한글로 변환
                        item["label"] = TEN_GOD_HANJA_TO_KR[label]
                    elif not label:
                        # 레이블이 비어있으면 코드에서 한글 레이블 생성
                        item["label"] = TEN_GOD_LABELS.get(item["code"], item["code"])

        return data

    def _normalize_pillars(self, data: dict[str, Any]) -> dict[str, Any]:
        """사주 기둥 정규화

        chart의 년/월/일/시주 데이터를 검증하고 정규화합니다.
        누락된 gan_code, ji_code, ten_god_code를 자동 생성합니다. (FR-005)

        Args:
            data: 원본 데이터

        Returns:
            기둥이 정규화된 데이터
        """
        chart = data.get("chart", {})
        pillar_keys = ["year", "month", "day", "hour"]

        # 일간(day master) 정보 추출 (십신 계산용)
        day_pillar = chart.get("day", {})
        day_gan = day_pillar.get("gan", "")
        day_element = GAN_TO_ELEMENT.get(day_gan)
        day_yinyang = GAN_TO_YINYANG.get(day_gan)

        for key in pillar_keys:
            pillar = chart.get(key, {})
            if not pillar:
                continue

            # element_code 정규화
            if "element_code" in pillar:
                code = pillar["element_code"]
                if code in ELEMENT_CODE_NORMALIZE:
                    pillar["element_code"] = ELEMENT_CODE_NORMALIZE[code]
                elif isinstance(code, str):
                    pillar["element_code"] = code.upper()

            # gan_code 자동 생성 (FR-005)
            if "gan_code" not in pillar and "gan" in pillar:
                gan = pillar["gan"]
                gan_code = GAN_TO_CODE.get(gan)
                if gan_code:
                    pillar["gan_code"] = gan_code
                    logger.debug("gan_code_generated", pillar=key, gan=gan, code=gan_code)
                else:
                    # 매핑 불가 시 로그 남기고 폴백 없음 (Pydantic에서 검증)
                    logger.warning(
                        "gan_code_mapping_failed",
                        pillar=key,
                        gan=gan,
                        valid_values=list(GAN_TO_CODE.keys()),
                    )

            # ji_code 자동 생성 (FR-005)
            if "ji_code" not in pillar and "ji" in pillar:
                ji = pillar["ji"]
                ji_code = JI_TO_CODE.get(ji)
                if ji_code:
                    pillar["ji_code"] = ji_code
                    logger.debug("ji_code_generated", pillar=key, ji=ji, code=ji_code)
                else:
                    logger.warning(
                        "ji_code_mapping_failed",
                        pillar=key,
                        ji=ji,
                        valid_values=list(JI_TO_CODE.keys()),
                    )

            # ten_god_code 자동 생성 (FR-005)
            if "ten_god_code" not in pillar:
                ten_god_code = self._calculate_ten_god(
                    pillar_key=key,
                    pillar_gan=pillar.get("gan", ""),
                    day_element=day_element,
                    day_yinyang=day_yinyang,
                )
                if ten_god_code:
                    pillar["ten_god_code"] = ten_god_code
                    logger.debug(
                        "ten_god_code_generated",
                        pillar=key,
                        gan=pillar.get("gan"),
                        code=ten_god_code,
                    )

        return data

    def _calculate_ten_god(
        self,
        pillar_key: str,
        pillar_gan: str,
        day_element: str | None,
        day_yinyang: str | None,
    ) -> str | None:
        """십신 코드 계산

        일간(day master) 기준으로 다른 기둥의 천간에 대한 십신을 계산합니다.

        Args:
            pillar_key: 기둥 키 (year/month/day/hour)
            pillar_gan: 해당 기둥의 천간 한자
            day_element: 일간의 오행
            day_yinyang: 일간의 음양

        Returns:
            십신 코드 또는 None (계산 불가 시)
        """
        # 일주(day)는 일간 자체이므로 DAY_MASTER
        if pillar_key == "day":
            return "DAY_MASTER"

        # 일간 정보가 없으면 계산 불가
        if not day_element or not day_yinyang or not pillar_gan:
            logger.warning(
                "ten_god_calculation_skipped",
                pillar=pillar_key,
                reason="missing_day_master_info",
            )
            return None

        # 해당 기둥 천간의 오행과 음양
        pillar_element = GAN_TO_ELEMENT.get(pillar_gan)
        pillar_yinyang = GAN_TO_YINYANG.get(pillar_gan)

        if not pillar_element or not pillar_yinyang:
            logger.warning(
                "ten_god_calculation_failed",
                pillar=pillar_key,
                gan=pillar_gan,
                reason="unknown_gan",
            )
            return None

        # 오행 관계 판정
        relation = ELEMENT_RELATIONS.get(day_element, {}).get(pillar_element)
        if not relation:
            logger.warning(
                "ten_god_relation_unknown",
                pillar=pillar_key,
                day_element=day_element,
                pillar_element=pillar_element,
            )
            return None

        # 음양 일치 여부
        same_yinyang = day_yinyang == pillar_yinyang

        # 십신 코드 조회
        ten_god_code = TEN_GOD_MAP.get((relation, same_yinyang))

        return ten_god_code

    def _sync_cheongan_jiji(self, data: dict[str, Any]) -> dict[str, Any]:
        """chart에서 cheongan_jiji 동기화

        chart의 사주 기둥에서 cheongan_jiji 필드를 자동 생성합니다.

        Args:
            data: 원본 데이터

        Returns:
            cheongan_jiji가 동기화된 데이터
        """
        chart = data.get("chart", {})
        stats = data.get("stats", {})

        # cheongan_jiji가 없으면 chart에서 생성
        if "cheongan_jiji" not in stats:
            stats["cheongan_jiji"] = {"summary": ""}

        cheongan_jiji = stats["cheongan_jiji"]
        pillar_keys = ["year", "month", "day", "hour"]

        for key in pillar_keys:
            pillar = chart.get(key, {})
            if pillar and key not in cheongan_jiji:
                cheongan_jiji[key] = {
                    "cheon_gan": pillar.get("gan", ""),
                    "ji_ji": pillar.get("ji", ""),
                }

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

    def _override_with_calculated(
        self,
        data: dict[str, Any],
        calculated_saju: dict[str, Any],
    ) -> dict[str, Any]:
        """서버 계산값으로 사주 강제 덮어쓰기 (FR-006)

        LLM이 프롬프트의 사주 계산값을 무시하고 잘못 생성하는 경우를 방지합니다.
        예: 辛(신) → 甲(갑) 잘못 생성 문제 해결

        Args:
            data: 후처리된 데이터
            calculated_saju: 서버에서 계산된 사주 정보 (만세력 기반)
                - year_pillar_hanja: 연주 한자 (예: "壬申")
                - month_pillar_hanja: 월주 한자 (예: "甲辰")
                - day_pillar_hanja: 일주 한자 (예: "辛未")
                - hour_pillar_hanja: 시주 한자 (예: "庚午") 또는 None

        Returns:
            사주가 덮어쓰기된 데이터
        """
        chart = data.get("chart", {})
        if not chart:
            data["chart"] = {}
            chart = data["chart"]

        # 기둥별 매핑 (calculated_saju 키 -> chart 키)
        pillar_mapping = {
            "year": "year_pillar_hanja",
            "month": "month_pillar_hanja",
            "day": "day_pillar_hanja",
            "hour": "hour_pillar_hanja",
        }

        overridden_pillars: list[str] = []

        for chart_key, saju_key in pillar_mapping.items():
            pillar_hanja = calculated_saju.get(saju_key)
            if not pillar_hanja:
                continue

            # 한자 기둥에서 천간/지지 분리 (예: "辛未" -> gan="辛", ji="未")
            if len(pillar_hanja) < 2:
                logger.warning(
                    "invalid_pillar_hanja",
                    pillar=chart_key,
                    hanja=pillar_hanja,
                )
                continue

            gan = pillar_hanja[0]  # 첫 글자: 천간
            ji = pillar_hanja[1]   # 두번째 글자: 지지

            # 천간/지지 유효성 검증
            if gan not in GAN_TO_CODE:
                logger.warning(
                    "invalid_gan_in_calculated",
                    pillar=chart_key,
                    gan=gan,
                    valid_values=list(GAN_TO_CODE.keys()),
                )
                continue

            if ji not in JI_TO_CODE:
                logger.warning(
                    "invalid_ji_in_calculated",
                    pillar=chart_key,
                    ji=ji,
                    valid_values=list(JI_TO_CODE.keys()),
                )
                continue

            # 기존 기둥 데이터 가져오기 (없으면 새로 생성)
            if chart_key not in chart:
                chart[chart_key] = {}
            pillar = chart[chart_key]

            # LLM 값과 다른 경우 로깅
            old_gan = pillar.get("gan")
            old_ji = pillar.get("ji")
            if old_gan and old_gan != gan:
                logger.info(
                    "saju_gan_overridden",
                    pillar=chart_key,
                    old_gan=old_gan,
                    new_gan=gan,
                )
            if old_ji and old_ji != ji:
                logger.info(
                    "saju_ji_overridden",
                    pillar=chart_key,
                    old_ji=old_ji,
                    new_ji=ji,
                )

            # 천간/지지 강제 덮어쓰기
            pillar["gan"] = gan
            pillar["ji"] = ji

            # 코드도 함께 업데이트
            pillar["gan_code"] = GAN_TO_CODE[gan]
            pillar["ji_code"] = JI_TO_CODE[ji]

            # 오행 코드 업데이트 (천간 기준)
            pillar["element_code"] = GAN_TO_ELEMENT.get(gan, "")

            overridden_pillars.append(chart_key)

        # 일간 기준 십신 재계산 (덮어쓰기 후)
        if overridden_pillars and "day" in chart:
            day_gan = chart["day"].get("gan", "")
            day_element = GAN_TO_ELEMENT.get(day_gan)
            day_yinyang = GAN_TO_YINYANG.get(day_gan)

            for pillar_key in ["year", "month", "hour"]:
                if pillar_key in chart:
                    pillar = chart[pillar_key]
                    ten_god_code = self._calculate_ten_god(
                        pillar_key=pillar_key,
                        pillar_gan=pillar.get("gan", ""),
                        day_element=day_element,
                        day_yinyang=day_yinyang,
                    )
                    if ten_god_code:
                        pillar["ten_god_code"] = ten_god_code

            # 일주는 항상 DAY_MASTER
            chart["day"]["ten_god_code"] = "DAY_MASTER"

        # cheongan_jiji도 동기화
        stats = data.get("stats", {})
        if "cheongan_jiji" in stats:
            cheongan_jiji = stats["cheongan_jiji"]
            for pillar_key in overridden_pillars:
                if pillar_key in chart:
                    pillar = chart[pillar_key]
                    cheongan_jiji[pillar_key] = {
                        "cheon_gan": pillar.get("gan", ""),
                        "ji_ji": pillar.get("ji", ""),
                    }

        if overridden_pillars:
            logger.info(
                "saju_overridden_with_calculated",
                overridden_pillars=overridden_pillars,
                calculated_day_pillar=calculated_saju.get("day_pillar_hanja"),
            )

        return data

    def _override_stats_with_calculated(
        self,
        data: dict[str, Any],
        calculated_saju: dict[str, Any],
    ) -> dict[str, Any]:
        """서버 계산 통계로 오행/음양/십신 분포 강제 덮어쓰기 (FR-007)

        LLM이 생성한 오행/음양/십신 비율 대신 서버에서 정확히 계산한 값을 사용합니다.
        summary 필드는 LLM 해석을 유지합니다.

        Args:
            data: 후처리된 데이터
            calculated_saju: 서버에서 계산된 사주 정보

        Returns:
            통계가 덮어쓰기된 데이터
        """
        # 사주 4기둥 생성 (한자 → 한글 변환)
        pillars = self._build_four_pillars(calculated_saju)
        if not pillars:
            logger.warning("eastern_stats_override_skipped", reason="pillars_not_found")
            return data

        calculator = SajuCalculator()

        # stats 객체 확보
        if "stats" not in data:
            data["stats"] = {}
        stats = data["stats"]

        # 1. 오행 분포 덮어쓰기
        five_elem_result = calculator.calculate_five_elements_distribution(pillars)
        if "five_elements" not in stats:
            stats["five_elements"] = {}

        # summary는 LLM 값 유지, list는 서버 계산값으로 교체
        old_summary = stats["five_elements"].get("summary", "오행 분포 분석입니다.")
        stats["five_elements"] = {
            "summary": old_summary,
            "list": five_elem_result["list"],
        }

        # 2. 음양 비율 덮어쓰기
        yin_yang_result = calculator.calculate_yin_yang_ratio(pillars)
        if "yin_yang_ratio" not in stats:
            stats["yin_yang_ratio"] = {}

        old_yy_summary = stats["yin_yang_ratio"].get("summary", "음양 균형 분석입니다.")
        stats["yin_yang_ratio"] = {
            "summary": old_yy_summary,
            "yin": yin_yang_result["yin"]["percent"],
            "yang": yin_yang_result["yang"]["percent"],
        }

        # 3. 십신 분포 덮어쓰기
        day_stem = calculated_saju.get("day_pillar_hanja", "")[:1]  # 일간 (첫 글자)
        if day_stem:
            ten_gods_result = calculator.calculate_ten_gods(day_stem, pillars)
            if "ten_gods" not in stats:
                stats["ten_gods"] = {}

            old_tg_summary = stats["ten_gods"].get("summary", "십신 분포 분석입니다.")

            # 코드 변환: SIKSIN → SIK_SIN (기존 스키마 호환)
            converted_list = []
            for item in ten_gods_result["list"]:
                # 기존 스키마의 십신 코드 형식으로 변환
                code = self._convert_ten_god_code(item["code"])
                converted_list.append({
                    "code": code,
                    "label": item["label"],
                    "percent": item["percent"],
                })

            # 상위 3개 + ETC 형식으로 조정
            if len(converted_list) > 3:
                top3 = converted_list[:3]
                etc_percent = sum(item["percent"] for item in converted_list[3:])
                top3.append({
                    "code": "ETC",
                    "label": "기타",
                    "percent": round(etc_percent, 1),
                })
                converted_list = top3

            stats["ten_gods"] = {
                "summary": old_tg_summary,
                "list": converted_list,
            }

        # 4. element 필드도 서버 계산값으로 덮어쓰기 (일간 오행)
        day_stem_element = calculated_saju.get("day_stem_element", "")
        element_map = {"목": "WOOD", "화": "FIRE", "토": "EARTH", "금": "METAL", "수": "WATER"}
        if day_stem_element in element_map:
            data["element"] = element_map[day_stem_element]

        logger.info(
            "eastern_stats_overridden_with_calculated",
            five_elements_dominant=five_elem_result.get("dominant"),
            yin_yang_balance=yin_yang_result.get("balance"),
        )

        return data

    def _build_four_pillars(
        self,
        calculated_saju: dict[str, Any],
    ) -> FourPillars | None:
        """calculated_saju에서 FourPillars 객체 생성"""
        try:
            year = calculated_saju.get("year_pillar_hanja", "")
            month = calculated_saju.get("month_pillar_hanja", "")
            day = calculated_saju.get("day_pillar_hanja", "")
            hour = calculated_saju.get("hour_pillar_hanja")

            if not (year and month and day):
                return None

            return FourPillars(
                year=year,
                month=month,
                day=day,
                hour=hour,
            )
        except Exception as e:
            logger.warning("build_four_pillars_failed", error=str(e))
            return None

    def _convert_ten_god_code(self, code: str) -> str:
        """십신 코드 변환 (신규 형식 → 기존 스키마 형식)

        예: BIGYEON → BI_GYEON, SIKSIN → SIK_SIN
        """
        code_map = {
            "BIGYEON": "BI_GYEON",
            "GEOPJAE": "GANG_JAE",  # 겁재
            "SIKSIN": "SIK_SIN",
            "SANGGWAN": "SANG_GWAN",
            "PYEONJAE": "PYEON_JAE",
            "JEONGJAE": "JEONG_JAE",
            "PYEONGWAN": "PYEON_GWAN",
            "JEONGGWAN": "JEONG_GWAN",
            "PYEONIN": "PYEON_IN",
            "JEONGIN": "JEONG_IN",
        }
        return code_map.get(code, code)
