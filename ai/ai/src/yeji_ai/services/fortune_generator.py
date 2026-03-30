"""운세 생성 서비스

AWS Provider를 사용하여 LLM으로 동양/서양 운세를 생성합니다.
response_format: {"type": "json_object"}로 구조화된 JSON 출력을 보장합니다.
"""

import asyncio
import json
from enum import Enum
from typing import Any, TypeVar

import httpx
import structlog
from pydantic import BaseModel, ValidationError

from yeji_ai.config import get_settings
from yeji_ai.models.enums import ZodiacCode
from yeji_ai.models.metrics import ErrorType
from yeji_ai.models.user_fortune import (
    FortuneResponse,
    SajuDataV2,
    UserFortune,
    WesternFortuneDataV2,
)
from yeji_ai.prompts.fortune_prompts import (
    EASTERN_SYSTEM_PROMPT,
    WESTERN_SYSTEM_PROMPT,
    build_eastern_generation_prompt,
    build_western_generation_prompt,
)
from yeji_ai.providers.aws import AWSConfig, AWSProvider
from yeji_ai.providers.base import GenerationConfig
from yeji_ai.services.postprocessor import EasternPostprocessor, WesternPostprocessor
from yeji_ai.services.response_logger import ResponseLogger, get_response_logger
from yeji_ai.services.validation_monitor import ValidationMonitor, get_validation_monitor

logger = structlog.get_logger()

T = TypeVar("T", bound=BaseModel)

# ============================================================
# 별자리 계산 헬퍼 (WesternFortuneService.get_sun_sign 로직 재사용)
# ============================================================

# 별자리 날짜 범위 (시작월, 시작일, 종료월, 종료일)
ZODIAC_DATES: dict[ZodiacCode, tuple[int, int, int, int]] = {
    ZodiacCode.ARIES: (3, 21, 4, 19),
    ZodiacCode.TAURUS: (4, 20, 5, 20),
    ZodiacCode.GEMINI: (5, 21, 6, 20),
    ZodiacCode.CANCER: (6, 21, 7, 22),
    ZodiacCode.LEO: (7, 23, 8, 22),
    ZodiacCode.VIRGO: (8, 23, 9, 22),
    ZodiacCode.LIBRA: (9, 23, 10, 22),
    ZodiacCode.SCORPIO: (10, 23, 11, 21),
    ZodiacCode.SAGITTARIUS: (11, 22, 12, 21),
    ZodiacCode.CAPRICORN: (12, 22, 1, 19),
    ZodiacCode.AQUARIUS: (1, 20, 2, 18),
    ZodiacCode.PISCES: (2, 19, 3, 20),
}

# 별자리 한글명 매핑 (프론트엔드 도메인 매핑 준수)
ZODIAC_KR_MAP: dict[ZodiacCode, str] = {
    ZodiacCode.ARIES: "양자리",
    ZodiacCode.TAURUS: "황소자리",
    ZodiacCode.GEMINI: "쌍둥이자리",
    ZodiacCode.CANCER: "게자리",
    ZodiacCode.LEO: "사자자리",
    ZodiacCode.VIRGO: "처녀자리",
    ZodiacCode.LIBRA: "천칭자리",
    ZodiacCode.SCORPIO: "전갈자리",
    ZodiacCode.SAGITTARIUS: "사수자리",
    ZodiacCode.CAPRICORN: "염소자리",
    ZodiacCode.AQUARIUS: "물병자리",
    ZodiacCode.PISCES: "물고기자리",
}


def get_sun_sign(month: int, day: int) -> ZodiacCode:
    """
    태양 별자리 계산

    Args:
        month: 월 (1-12)
        day: 일 (1-31)

    Returns:
        별자리 코드
    """
    # (월, 일)을 정수로 변환하여 비교 (예: 4월 5일 → 405)
    date_num = month * 100 + day

    for zodiac, (start_month, start_day, end_month, end_day) in ZODIAC_DATES.items():
        start_num = start_month * 100 + start_day
        end_num = end_month * 100 + end_day

        # 염소자리 특수 처리 (연말~연초 걸침: 12/22 ~ 1/19)
        if start_month > end_month:
            # 12월 22일 이후 또는 1월 19일 이전
            if date_num >= start_num or date_num <= end_num:
                return zodiac
        else:
            # 일반적인 경우: 시작일 ~ 종료일 범위 내
            if start_num <= date_num <= end_num:
                return zodiac

    # 기본값 (도달하지 않아야 함)
    return ZodiacCode.CAPRICORN


def get_sun_sign_kr(month: int, day: int) -> str:
    """
    태양 별자리 한글명 반환

    Args:
        month: 월 (1-12)
        day: 일 (1-31)

    Returns:
        별자리 한글명 (예: "양자리")
    """
    zodiac = get_sun_sign(month, day)
    return ZODIAC_KR_MAP[zodiac]


# ============================================================
# 사주 계산 헬퍼 (만세력 기반)
# ============================================================

# 천간 (10개)
HEAVENLY_STEMS = ["갑", "을", "병", "정", "무", "기", "경", "신", "임", "계"]
HEAVENLY_STEMS_HANJA = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]

# 지지 (12개)
EARTHLY_BRANCHES = ["자", "축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해"]
EARTHLY_BRANCHES_HANJA = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

# 60갑자
SIXTY_CYCLE = [f"{HEAVENLY_STEMS[i % 10]}{EARTHLY_BRANCHES[i % 12]}" for i in range(60)]

# 천간 → 오행 매핑
STEM_TO_ELEMENT = {
    "갑": "목", "을": "목",
    "병": "화", "정": "화",
    "무": "토", "기": "토",
    "경": "금", "신": "금",
    "임": "수", "계": "수",
}


def calculate_four_pillars(
    birth_year: int,
    birth_month: int,
    birth_day: int,
    birth_hour: int,
) -> dict[str, str | None]:
    """
    사주팔자(4기둥) 계산 - 만세력 기반 정확한 계산

    Args:
        birth_year: 출생 연도
        birth_month: 출생 월
        birth_day: 출생 일
        birth_hour: 출생 시

    Returns:
        계산된 사주 정보 딕셔너리
            - year_pillar: 연주 한글 (예: "임신")
            - month_pillar: 월주 한글 (예: "갑진")
            - day_pillar: 일주 한글 (예: "신미")
            - hour_pillar: 시주 한글 (예: "경오") 또는 None
            - year_pillar_hanja: 연주 한자 (예: "壬申")
            - month_pillar_hanja: 월주 한자 (예: "甲辰")
            - day_pillar_hanja: 일주 한자 (예: "辛未")
            - hour_pillar_hanja: 시주 한자 (예: "庚午") 또는 None
            - day_stem: 일간 한글 (예: "신")
            - day_stem_element: 일간 오행 (예: "금")
    """
    from datetime import datetime

    dt = datetime(birth_year, birth_month, birth_day)

    # 연주 계산 (입춘 기준이지만 간략화)
    year_idx = (birth_year - 4) % 60
    year_pillar = SIXTY_CYCLE[year_idx]

    # 월주 계산 (절기 기준이지만 간략화)
    year_stem_idx = (birth_year - 4) % 10
    month_stem_idx = (year_stem_idx * 2 + birth_month) % 10
    month_branch_idx = (birth_month + 1) % 12  # 인월(1월)부터 시작
    month_pillar = f"{HEAVENLY_STEMS[month_stem_idx]}{EARTHLY_BRANCHES[month_branch_idx]}"

    # 일주 계산 (1900-01-31 갑자일 기준)
    base_date = datetime(1900, 1, 31)
    day_diff = (dt - base_date).days
    day_idx = day_diff % 60
    day_pillar = SIXTY_CYCLE[day_idx]

    # 시주 계산
    hour_pillar: str | None = None
    if birth_hour >= 0:
        hour_branch_idx = ((birth_hour + 1) // 2) % 12
        day_stem_idx = HEAVENLY_STEMS.index(day_pillar[0])
        hour_stem_idx = (day_stem_idx * 2 + hour_branch_idx) % 10
        hour_pillar = f"{HEAVENLY_STEMS[hour_stem_idx]}{EARTHLY_BRANCHES[hour_branch_idx]}"

    # 일간 정보
    day_stem = day_pillar[0]
    day_stem_element = STEM_TO_ELEMENT[day_stem]

    # 한자 변환 헬퍼
    def to_hanja(pillar: str) -> str:
        stem_idx = HEAVENLY_STEMS.index(pillar[0])
        branch_idx = EARTHLY_BRANCHES.index(pillar[1])
        return f"{HEAVENLY_STEMS_HANJA[stem_idx]}{EARTHLY_BRANCHES_HANJA[branch_idx]}"

    result: dict[str, str | None] = {
        "year_pillar": year_pillar,
        "month_pillar": month_pillar,
        "day_pillar": day_pillar,
        "hour_pillar": hour_pillar,
        "year_pillar_hanja": to_hanja(year_pillar),
        "month_pillar_hanja": to_hanja(month_pillar),
        "day_pillar_hanja": to_hanja(day_pillar),
        "hour_pillar_hanja": to_hanja(hour_pillar) if hour_pillar else None,
        "day_stem": day_stem,
        "day_stem_element": day_stem_element,
    }

    logger.debug(
        "four_pillars_calculated",
        year=year_pillar,
        month=month_pillar,
        day=day_pillar,
        hour=hour_pillar,
        day_stem=day_stem,
        day_stem_element=day_stem_element,
    )

    return result


class LLMErrorType(str, Enum):
    """LLM 에러 타입 분류

    각 에러 타입에 따라 다른 HTTP 상태 코드를 반환합니다:
    - VALIDATION: 502 Bad Gateway (LLM 응답 스키마 불일치)
    - CONNECTION: 503 Service Unavailable (LLM 서비스 연결 불가)
    - TIMEOUT: 504 Gateway Timeout (LLM 응답 타임아웃)
    - UNKNOWN: 503 Service Unavailable (분류되지 않은 에러)
    """

    VALIDATION = "validation"  # LLM 응답 스키마 불일치 → 502
    CONNECTION = "connection"  # LLM 서비스 연결 불가 → 503
    TIMEOUT = "timeout"  # LLM 응답 타임아웃 → 504
    UNKNOWN = "unknown"  # 분류되지 않은 에러 → 503


# LLM 에러 코드 매핑
LLM_ERROR_CODES = {
    LLMErrorType.VALIDATION: "LLM_VALIDATION_FAILED",
    LLMErrorType.CONNECTION: "LLM_CONNECTION_FAILED",
    LLMErrorType.TIMEOUT: "LLM_TIMEOUT",
    LLMErrorType.UNKNOWN: "LLM_UNKNOWN_ERROR",
}


class FortuneGeneratorError(Exception):
    """운세 생성 중 발생한 에러

    Attributes:
        message: 에러 메시지
        error_type: 에러 타입 (validation, connection, timeout, unknown)
        error_code: 에러 코드 (예: LLM_VALIDATION_FAILED)
        raw_content: LLM 원본 응답 (검증 실패 시 디버깅용)
        details: 추가 에러 상세 정보
    """

    def __init__(
        self,
        message: str,
        error_type: LLMErrorType = LLMErrorType.UNKNOWN,
        raw_content: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_type = error_type
        self.error_code = LLM_ERROR_CODES[error_type]
        self.raw_content = raw_content
        self.details = details or {}

    def to_error_response(self) -> dict[str, Any]:
        """에러 응답 구조로 변환

        Returns:
            표준화된 에러 응답 딕셔너리
        """
        response: dict[str, Any] = {
            "error": {
                "code": self.error_code,
                "message": self.message,
                "details": self.details,
            }
        }
        # 검증 실패 시 원본 응답 포함 (디버깅용)
        if self.raw_content and self.error_type == LLMErrorType.VALIDATION:
            response["error"]["details"]["raw_content"] = self.raw_content[:2000]
        return response


class FortuneGenerator:
    """운세 생성 서비스

    AWS Provider를 사용하여 동양 사주(SajuDataV2)와
    서양 점성술(WesternFortuneDataV2)을 LLM으로 생성합니다.

    사용 예시:
        generator = FortuneGenerator()
        await generator.initialize()

        # 동양 사주 생성
        eastern = await generator.generate_eastern({
            "birth_year": 1990,
            "birth_month": 3,
            "birth_day": 15,
            "birth_hour": 14,
            "gender": "male",
        })

        # 서양 점성술 생성
        western = await generator.generate_western({
            "birth_year": 1990,
            "birth_month": 3,
            "birth_day": 15,
            "birth_hour": 14,
            "birth_minute": 30,
            "latitude": 37.5665,
            "longitude": 126.9780,
        })

        # 전체 운세 생성
        full = await generator.generate_full({...})

        await generator.close()
    """

    def __init__(
        self,
        provider: AWSProvider | None = None,
        max_retries: int = 2,
        max_tokens: int = 1500,  # 프롬프트 길이 고려 (max_model_len 4096)
        temperature: float = 0.7,
        skip_validation: bool | None = None,
        response_logger: ResponseLogger | None = None,
        validation_monitor: ValidationMonitor | None = None,
        enable_postprocess: bool | None = None,
        enable_eastern_postprocess: bool | None = None,
        enable_western_postprocess: bool | None = None,
    ):
        """
        초기화

        Args:
            provider: AWS Provider 인스턴스 (없으면 기본 설정으로 생성)
            max_retries: 최대 재시도 횟수
            max_tokens: 생성 최대 토큰 수
            temperature: 생성 온도
            skip_validation: Pydantic 검증 스킵 여부 (None이면 설정에서 로드)
            response_logger: LLM 응답 로거 (없으면 글로벌 인스턴스 사용)
            validation_monitor: 검증 실패 모니터 (없으면 글로벌 인스턴스 사용)
            enable_postprocess: 전체 후처리 활성화 여부 (None이면 설정에서 로드)
            enable_eastern_postprocess: 동양 후처리 활성화 (None이면 설정에서 로드)
            enable_western_postprocess: 서양 후처리 활성화 (None이면 설정에서 로드)
        """
        self._settings = get_settings()
        self._provider = provider
        self._max_retries = max_retries
        self._max_tokens = max_tokens
        self._temperature = temperature
        self._initialized = False
        self._skip_validation = (
            skip_validation if skip_validation is not None else self._settings.skip_validation
        )
        # LLM 응답 로거 (글로벌 싱글톤 사용 또는 주입)
        self._response_logger = response_logger
        # 검증 실패 모니터 (글로벌 싱글톤 사용 또는 주입)
        self._validation_monitor = validation_monitor

        # 후처리 Feature Flag 설정 (환경변수 우선, 인자로 오버라이드 가능)
        self._enable_postprocess = (
            enable_postprocess
            if enable_postprocess is not None
            else self._settings.enable_postprocess
        )
        self._enable_eastern_postprocess = (
            enable_eastern_postprocess
            if enable_eastern_postprocess is not None
            else self._settings.postprocess_eastern_enabled
        )
        self._enable_western_postprocess = (
            enable_western_postprocess
            if enable_western_postprocess is not None
            else self._settings.postprocess_western_enabled
        )

        # 후처리기 인스턴스 (lazy initialization)
        self._eastern_postprocessor: EasternPostprocessor | None = None
        self._western_postprocessor: WesternPostprocessor | None = None

    @property
    def provider(self) -> AWSProvider:
        """AWS Provider 반환 (초기화 필요)"""
        if self._provider is None:
            raise FortuneGeneratorError(
                "Provider가 초기화되지 않았습니다. initialize()를 먼저 호출하세요."
            )
        return self._provider

    @property
    def response_logger(self) -> ResponseLogger:
        """LLM 응답 로거 반환 (글로벌 싱글톤 또는 주입된 인스턴스)"""
        if self._response_logger is None:
            self._response_logger = get_response_logger()
        return self._response_logger

    @property
    def validation_monitor(self) -> ValidationMonitor:
        """검증 실패 모니터 반환 (글로벌 싱글톤 또는 주입된 인스턴스)"""
        if self._validation_monitor is None:
            self._validation_monitor = get_validation_monitor()
        return self._validation_monitor

    @property
    def eastern_postprocessor(self) -> EasternPostprocessor:
        """동양 사주 후처리기 반환 (lazy initialization)"""
        if self._eastern_postprocessor is None:
            self._eastern_postprocessor = EasternPostprocessor()
        return self._eastern_postprocessor

    @property
    def western_postprocessor(self) -> WesternPostprocessor:
        """서양 점성술 후처리기 반환 (lazy initialization)"""
        if self._western_postprocessor is None:
            self._western_postprocessor = WesternPostprocessor()
        return self._western_postprocessor

    async def initialize(self) -> None:
        """Provider 초기화

        외부에서 Provider를 주입하지 않은 경우 기본 설정으로 생성합니다.
        """
        if self._initialized:
            return

        if self._provider is None:
            # 기본 AWS Provider 생성 (설정에서 로드)
            config = AWSConfig(
                base_url=self._settings.vllm_base_url,  # 환경변수에서 URL 로드
                model=self._settings.vllm_model,
                local_port=8001,
                remote_port=8001,
                default_max_tokens=self._max_tokens,
                default_temperature=self._temperature,
            )
            self._provider = AWSProvider(config)

        self._initialized = True
        logger.info(
            "fortune_generator_initialized",
            model=self._provider.config.model,
        )

    async def close(self) -> None:
        """리소스 정리"""
        if self._provider is not None:
            await self._provider.close()
            logger.info("fortune_generator_closed")

    async def _call_llm_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: type[T],
        calculated_saju: dict[str, Any] | None = None,
        calculated_zodiac: str | None = None,
    ) -> T:
        """
        구조화된 LLM API 호출

        response_format: {"type": "json_object"}를 사용하여
        JSON 출력을 강제하고, Pydantic 모델로 검증합니다.

        Args:
            system_prompt: 시스템 프롬프트
            user_prompt: 사용자 프롬프트
            response_schema: 응답 Pydantic 스키마
            calculated_saju: 서버에서 계산된 사주 정보 (동양 사주용)
            calculated_zodiac: 서버에서 계산된 별자리 코드 (서양 점성술용, 예: "ARIES")

        Returns:
            검증된 Pydantic 모델 인스턴스

        Raises:
            FortuneGeneratorError: LLM 호출 또는 파싱 실패
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        # 생성 설정 (JSON 모드 활성화)
        gen_config = GenerationConfig(
            max_tokens=self._max_tokens,
            temperature=self._temperature,
            top_p=0.8,
            presence_penalty=1.5,  # Qwen3 AWQ 반복 방지
            response_format={"type": "json_object"},
        )

        last_error: Exception | None = None
        last_error_type: LLMErrorType = LLMErrorType.UNKNOWN
        content: str = ""

        for attempt in range(self._max_retries + 1):
            try:
                # 온도 약간 증가 (재시도 시)
                if attempt > 0:
                    gen_config.temperature = self._temperature + (attempt * 0.1)

                # LLM 호출
                response = await self.provider.chat(messages, gen_config)
                content = response.text

                # <think> 태그 제거 (Qwen3)
                if "<think>" in content:
                    content = content.split("</think>")[-1].strip()

                # JSON 파싱
                parsed_data = json.loads(content)

                # 스키마별 후처리 적용 (FR-005, FR-006)
                if self._enable_postprocess:
                    if (
                        response_schema.__name__ == "SajuDataV2"
                        and self._enable_eastern_postprocess
                    ):
                        try:
                            # calculated_saju를 전달하여 서버 계산값으로 덮어쓰기
                            parsed_data = self.eastern_postprocessor.process(
                                parsed_data,
                                calculated_saju=calculated_saju,
                            )
                            logger.debug("eastern_postprocess_applied_in_structured")
                        except Exception as e:
                            logger.warning("eastern_postprocess_failed_in_structured", error=str(e))
                    elif (
                        response_schema.__name__ == "WesternFortuneDataV2"
                        and self._enable_western_postprocess
                    ):
                        try:
                            # calculated_zodiac을 전달하여 서버 계산값으로 덮어쓰기 (FR-006)
                            parsed_data = self.western_postprocessor.process(
                                parsed_data,
                                calculated_zodiac=calculated_zodiac,
                            )
                            logger.debug("western_postprocess_applied_in_structured")
                        except Exception as e:
                            logger.warning("western_postprocess_failed_in_structured", error=str(e))

                # Pydantic 검증
                result = response_schema.model_validate(parsed_data)

                logger.info(
                    "llm_structured_success",
                    schema=response_schema.__name__,
                    attempt=attempt + 1,
                    latency_ms=response.latency_ms,
                )
                return result

            except ValidationError as e:
                # 검증 실패 (LLM 응답 스키마 불일치)
                logger.warning(
                    "llm_validation_error",
                    schema=response_schema.__name__,
                    attempt=attempt + 1,
                    error=str(e),
                    llm_response=content[:2000] if content else None,
                )
                last_error = e
                last_error_type = LLMErrorType.VALIDATION

            except httpx.ConnectError as e:
                # 연결 실패 (LLM 서비스 연결 불가)
                logger.warning(
                    "llm_connection_error",
                    attempt=attempt + 1,
                    error=str(e),
                )
                last_error = e
                last_error_type = LLMErrorType.CONNECTION

            except httpx.TimeoutException as e:
                # 타임아웃 (LLM 응답 타임아웃)
                logger.warning(
                    "llm_timeout_error",
                    attempt=attempt + 1,
                    error=str(e),
                )
                last_error = e
                last_error_type = LLMErrorType.TIMEOUT

            except Exception as e:
                # 분류되지 않은 에러
                logger.warning(
                    "llm_call_error",
                    attempt=attempt + 1,
                    error=str(e),
                    error_type=type(e).__name__,
                )
                last_error = e
                # 에러 타입 추론 (httpx 에러 세부 분류)
                if isinstance(e, httpx.HTTPStatusError):
                    last_error_type = LLMErrorType.CONNECTION
                else:
                    last_error_type = LLMErrorType.UNKNOWN

        # 모든 재시도 실패 - 에러 타입에 따른 FortuneGeneratorError 생성
        logger.error(
            "llm_structured_failed",
            schema=response_schema.__name__,
            error=str(last_error),
            error_type=last_error_type.value,
            raw_content=content[:2000] if content else None,
        )

        # 에러 상세 정보 구성
        error_details: dict[str, Any] = {
            "schema": response_schema.__name__,
            "attempts": self._max_retries + 1,
            "original_error": str(last_error),
        }

        # 검증 에러인 경우 Pydantic 에러 목록 추가
        if last_error_type == LLMErrorType.VALIDATION and isinstance(last_error, ValidationError):
            error_details["validation_errors"] = [
                {"loc": list(err["loc"]), "msg": err["msg"], "type": err["type"]}
                for err in last_error.errors()[:10]  # 최대 10개
            ]

        raise FortuneGeneratorError(
            message=f"LLM 구조화된 출력 생성 실패: {last_error}",
            error_type=last_error_type,
            raw_content=content if last_error_type == LLMErrorType.VALIDATION else None,
            details=error_details,
        ) from last_error

    async def _call_llm_raw(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> dict[str, Any]:
        """
        Raw LLM API 호출 (Pydantic 검증 없음)

        테스트/디버그용으로 LLM 응답을 그대로 반환합니다.

        Args:
            system_prompt: 시스템 프롬프트
            user_prompt: 사용자 프롬프트

        Returns:
            LLM 응답 dict (파싱된 JSON 또는 원본 텍스트 포함)
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        gen_config = GenerationConfig(
            max_tokens=self._max_tokens,
            temperature=self._temperature,
            top_p=0.8,
            presence_penalty=1.5,
            response_format={"type": "json_object"},
        )

        try:
            response = await self.provider.chat(messages, gen_config)
            content = response.text

            # <think> 태그 제거 (Qwen3)
            if "<think>" in content:
                content = content.split("</think>")[-1].strip()

            # JSON 파싱 시도
            try:
                parsed = json.loads(content)
                return {
                    "success": True,
                    "data": parsed,
                    "raw_content": content,
                    "latency_ms": response.latency_ms,
                }
            except json.JSONDecodeError as e:
                return {
                    "success": False,
                    "error": f"JSON 파싱 실패: {e}",
                    "raw_content": content,
                    "latency_ms": response.latency_ms,
                }

        except Exception as e:
            logger.error("llm_raw_call_error", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "raw_content": None,
            }

    async def generate_eastern_raw(
        self,
        birth_data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        동양 사주 운세 생성 (Raw 모드 - 검증 스킵)

        Pydantic 검증 없이 LLM 응답을 그대로 반환합니다.
        테스트/디버그용입니다.

        Args:
            birth_data: 출생 정보

        Returns:
            Raw LLM 응답 dict
        """
        required_fields = ["birth_year", "birth_month", "birth_day", "birth_hour"]
        for field in required_fields:
            if field not in birth_data:
                return {"success": False, "error": f"필수 필드 누락: {field}"}

        # 서버에서 사주 계산 (만세력 기반)
        calculated_saju = calculate_four_pillars(
            birth_year=birth_data["birth_year"],
            birth_month=birth_data["birth_month"],
            birth_day=birth_data["birth_day"],
            birth_hour=birth_data["birth_hour"],
        )

        user_prompt = build_eastern_generation_prompt(
            birth_year=birth_data["birth_year"],
            birth_month=birth_data["birth_month"],
            birth_day=birth_data["birth_day"],
            birth_hour=birth_data["birth_hour"],
            gender=birth_data.get("gender", "unknown"),
            calculated_saju=calculated_saju,
        )

        return await self._call_llm_raw(
            system_prompt=EASTERN_SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

    async def generate_eastern(
        self,
        birth_data: dict[str, Any],
    ) -> SajuDataV2:
        """
        동양 사주 운세 생성

        Args:
            birth_data: 출생 정보
                - birth_year: int (필수) 출생 연도
                - birth_month: int (필수) 출생 월
                - birth_day: int (필수) 출생 일
                - birth_hour: int (필수) 출생 시
                - gender: str (선택) 성별 (male/female/unknown)

        Returns:
            SajuDataV2 모델 (프론트엔드 확정 스키마)

        Raises:
            FortuneGeneratorError: 생성 실패
        """
        # 필수 필드 검증
        required_fields = ["birth_year", "birth_month", "birth_day", "birth_hour"]
        for field in required_fields:
            if field not in birth_data:
                raise FortuneGeneratorError(f"필수 필드 누락: {field}")

        birth_year = birth_data["birth_year"]
        birth_month = birth_data["birth_month"]
        birth_day = birth_data["birth_day"]
        birth_hour = birth_data["birth_hour"]
        gender = birth_data.get("gender", "unknown")

        # 서버에서 사주 계산 (만세력 기반)
        calculated_saju = calculate_four_pillars(
            birth_year=birth_year,
            birth_month=birth_month,
            birth_day=birth_day,
            birth_hour=birth_hour,
        )

        logger.info(
            "generate_eastern_start",
            birth_year=birth_year,
            birth_month=birth_month,
            birth_day=birth_day,
            birth_hour=birth_hour,
            day_pillar=calculated_saju["day_pillar"],
            day_stem=calculated_saju["day_stem"],
        )

        # 프롬프트 생성 (계산된 사주 정보 전달)
        user_prompt = build_eastern_generation_prompt(
            birth_year=birth_year,
            birth_month=birth_month,
            birth_day=birth_day,
            birth_hour=birth_hour,
            gender=gender,
            calculated_saju=calculated_saju,
        )

        # LLM 호출 및 응답 검증 (calculated_saju 전달로 서버 계산값 강제 적용)
        result = await self._call_llm_structured(
            system_prompt=EASTERN_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_schema=SajuDataV2,
            calculated_saju=calculated_saju,
        )

        logger.info(
            "generate_eastern_complete",
            element=result.element,
        )

        return result

    async def generate_western_raw(
        self,
        birth_data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        서양 점성술 운세 생성 (Raw 모드 - 검증 스킵)

        Pydantic 검증 없이 LLM 응답을 그대로 반환합니다.
        테스트/디버그용입니다.

        Args:
            birth_data: 출생 정보

        Returns:
            Raw LLM 응답 dict
        """
        required_fields = ["birth_year", "birth_month", "birth_day"]
        for field in required_fields:
            if field not in birth_data:
                return {"success": False, "error": f"필수 필드 누락: {field}"}

        # 서버에서 별자리 계산
        sun_sign_kr = get_sun_sign_kr(
            month=birth_data["birth_month"],
            day=birth_data["birth_day"],
        )

        user_prompt = build_western_generation_prompt(
            birth_year=birth_data["birth_year"],
            birth_month=birth_data["birth_month"],
            birth_day=birth_data["birth_day"],
            birth_hour=birth_data.get("birth_hour", 12),
            birth_minute=birth_data.get("birth_minute", 0),
            latitude=birth_data.get("latitude", 37.5665),
            longitude=birth_data.get("longitude", 126.9780),
            sun_sign=sun_sign_kr,
        )

        return await self._call_llm_raw(
            system_prompt=WESTERN_SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

    async def generate_western(
        self,
        birth_data: dict[str, Any],
    ) -> WesternFortuneDataV2:
        """
        서양 점성술 운세 생성

        Args:
            birth_data: 출생 정보
                - birth_year: int (필수) 출생 연도
                - birth_month: int (필수) 출생 월
                - birth_day: int (필수) 출생 일
                - birth_hour: int (선택, 기본: 12) 출생 시
                - birth_minute: int (선택, 기본: 0) 출생 분
                - latitude: float (선택, 기본: 37.5665) 출생지 위도
                - longitude: float (선택, 기본: 126.9780) 출생지 경도

        Returns:
            WesternFortuneDataV2 모델 (프론트엔드 확정 스키마)

        Raises:
            FortuneGeneratorError: 생성 실패
        """
        # 필수 필드 검증
        required_fields = ["birth_year", "birth_month", "birth_day"]
        for field in required_fields:
            if field not in birth_data:
                raise FortuneGeneratorError(f"필수 필드 누락: {field}")

        birth_year = birth_data["birth_year"]
        birth_month = birth_data["birth_month"]
        birth_day = birth_data["birth_day"]
        birth_hour = birth_data.get("birth_hour", 12)
        birth_minute = birth_data.get("birth_minute", 0)
        latitude = birth_data.get("latitude", 37.5665)  # 서울 기본값
        longitude = birth_data.get("longitude", 126.9780)

        # 서버에서 별자리 계산
        sun_sign = get_sun_sign(month=birth_month, day=birth_day)
        sun_sign_kr = ZODIAC_KR_MAP[sun_sign]

        logger.info(
            "generate_western_start",
            birth_year=birth_year,
            birth_month=birth_month,
            birth_day=birth_day,
            sun_sign=sun_sign_kr,
            sun_sign_code=sun_sign.value,
        )

        # 프롬프트 생성 (서버에서 계산된 별자리 전달)
        user_prompt = build_western_generation_prompt(
            birth_year=birth_year,
            birth_month=birth_month,
            birth_day=birth_day,
            birth_hour=birth_hour,
            birth_minute=birth_minute,
            latitude=latitude,
            longitude=longitude,
            sun_sign=sun_sign_kr,
        )

        # LLM 호출 및 응답 검증 (calculated_zodiac 전달로 서버 계산값 강제 적용)
        result = await self._call_llm_structured(
            system_prompt=WESTERN_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_schema=WesternFortuneDataV2,
            calculated_zodiac=sun_sign.value,
        )

        logger.info(
            "generate_western_complete",
            element=result.element,
            main_sign=result.stats.main_sign.name,
        )

        return result

    async def generate_full(
        self,
        birth_data: dict[str, Any],
    ) -> UserFortune:
        """
        전체 운세 생성 (동양 + 서양)

        동양 사주와 서양 점성술을 모두 생성하여 통합 결과를 반환합니다.

        Args:
            birth_data: 출생 정보
                - birth_year: int (필수) 출생 연도
                - birth_month: int (필수) 출생 월
                - birth_day: int (필수) 출생 일
                - birth_hour: int (필수) 출생 시
                - birth_minute: int (선택, 기본: 0) 출생 분
                - gender: str (선택) 성별 (male/female/unknown)
                - latitude: float (선택, 기본: 37.5665) 출생지 위도
                - longitude: float (선택, 기본: 126.9780) 출생지 경도

        Returns:
            UserFortune 모델 (eastern + western 통합)

        Raises:
            FortuneGeneratorError: 생성 실패
        """
        # 필수 필드 검증
        required_fields = ["birth_year", "birth_month", "birth_day", "birth_hour"]
        for field in required_fields:
            if field not in birth_data:
                raise FortuneGeneratorError(f"필수 필드 누락: {field}")

        logger.info(
            "generate_full_start",
            birth_year=birth_data["birth_year"],
            birth_month=birth_data["birth_month"],
            birth_day=birth_data["birth_day"],
        )

        # 동양/서양 동시 생성 (P0 비동기 최적화)
        eastern, western = await asyncio.gather(
            self.generate_eastern(birth_data),
            self.generate_western(birth_data),
        )

        # 통합 결과 생성
        result = UserFortune(
            eastern=eastern,
            western=western,
        )

        logger.info(
            "generate_full_complete",
            eastern_element=eastern.element,
            western_element=western.element,
        )

        return result

    # ============================================================
    # Graceful Degradation 메서드 (검증 실패해도 응답 반환)
    # ============================================================

    async def generate_eastern_graceful(
        self,
        birth_data: dict[str, Any],
    ) -> FortuneResponse:
        """
        동양 사주 운세 생성 (Graceful Degradation)

        검증 실패해도 200 응답을 반환합니다.
        - 검증 성공: validated=True, data=검증된 데이터
        - 검증 실패: validated=False, data=원본 LLM 출력, errors=에러 목록

        Args:
            birth_data: 출생 정보

        Returns:
            FortuneResponse (항상 성공, validated 필드로 검증 상태 구분)
        """
        # 필수 필드 검증
        required_fields = ["birth_year", "birth_month", "birth_day", "birth_hour"]
        for field in required_fields:
            if field not in birth_data:
                return FortuneResponse(
                    success=False,
                    validated=False,
                    type="eastern",
                    data={},
                    errors=[f"필수 필드 누락: {field}"],
                    latency_ms=0,
                )

        # 서버에서 사주 계산 (만세력 기반)
        calculated_saju = calculate_four_pillars(
            birth_year=birth_data["birth_year"],
            birth_month=birth_data["birth_month"],
            birth_day=birth_data["birth_day"],
            birth_hour=birth_data["birth_hour"],
        )

        user_prompt = build_eastern_generation_prompt(
            birth_year=birth_data["birth_year"],
            birth_month=birth_data["birth_month"],
            birth_day=birth_data["birth_day"],
            birth_hour=birth_data["birth_hour"],
            gender=birth_data.get("gender", "unknown"),
            calculated_saju=calculated_saju,
        )

        # LLM 호출
        messages = [
            {"role": "system", "content": EASTERN_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        gen_config = GenerationConfig(
            max_tokens=self._max_tokens,
            temperature=self._temperature,
            top_p=0.8,
            presence_penalty=1.5,
            response_format={"type": "json_object"},
        )

        # 로깅 메타데이터 (안전하게 가져오기)
        try:
            model_name = self._provider.config.model if self._provider else None
        except AttributeError:
            model_name = None

        try:
            response = await self.provider.chat(messages, gen_config)
            content = response.text
            latency_ms = response.latency_ms

            # <think> 태그 제거 (Qwen3)
            if "<think>" in content:
                content = content.split("</think>")[-1].strip()

            # JSON 파싱
            try:
                parsed = json.loads(content)
            except json.JSONDecodeError as e:
                logger.warning("eastern_graceful_json_error", error=str(e))
                # JSON 파싱 에러 로깅
                await self.response_logger.log_json_parse_error(
                    fortune_type="eastern",
                    request_input=birth_data,
                    raw_response=content,
                    error_message=str(e),
                    latency_ms=latency_ms,
                    model_name=model_name,
                    temperature=self._temperature,
                )
                # 검증 실패 모니터에 기록
                self.validation_monitor.record_failure(
                    fortune_type="eastern",
                    error_type=ErrorType.JSON_PARSE,
                    error_message=str(e),
                )
                return FortuneResponse(
                    success=True,
                    validated=False,
                    type="eastern",
                    data={"raw_content": content},
                    errors=[f"JSON 파싱 실패: {e}"],
                    latency_ms=latency_ms,
                )

            # 후처리 적용 (전체 활성화 + 동양 후처리 활성화된 경우)
            # calculated_saju를 전달하여 서버 계산값으로 강제 덮어쓰기 (FR-006)
            if self._enable_postprocess and self._enable_eastern_postprocess:
                try:
                    parsed = self.eastern_postprocessor.process(
                        parsed,
                        calculated_saju=calculated_saju,
                    )
                    logger.debug("eastern_postprocess_applied")
                except Exception as e:
                    logger.warning("eastern_postprocess_failed", error=str(e))
                    # 후처리 실패해도 원본으로 계속 진행 (fail-safe)

            # Pydantic 검증 시도
            try:
                validated_data = SajuDataV2.model_validate(parsed)
                logger.info("eastern_graceful_validated", element=validated_data.element)
                # 성공 로깅
                await self.response_logger.log_success(
                    fortune_type="eastern",
                    request_input=birth_data,
                    raw_response=content,
                    parsed_response=validated_data.model_dump(),
                    latency_ms=latency_ms,
                    model_name=model_name,
                    temperature=self._temperature,
                )
                # 검증 성공 모니터에 기록
                self.validation_monitor.record_success(fortune_type="eastern")
                return FortuneResponse(
                    success=True,
                    validated=True,
                    type="eastern",
                    data=validated_data.model_dump(),
                    errors=None,
                    latency_ms=latency_ms,
                )
            except ValidationError as e:
                # 검증 실패 → 원본 데이터 + 에러 목록 반환
                error_messages = [f"{err['loc']}: {err['msg']}" for err in e.errors()]
                validation_errors = [
                    {"loc": list(err["loc"]), "msg": err["msg"], "type": err["type"]}
                    for err in e.errors()[:10]
                ]
                logger.warning(
                    "eastern_graceful_validation_failed",
                    errors=error_messages[:5],  # 최대 5개만 로깅
                )
                # 검증 에러 로깅
                await self.response_logger.log_validation_error(
                    fortune_type="eastern",
                    request_input=birth_data,
                    raw_response=content,
                    error_message=str(e),
                    validation_errors=validation_errors,
                    latency_ms=latency_ms,
                    model_name=model_name,
                    temperature=self._temperature,
                )
                # 검증 실패 모니터에 기록
                self.validation_monitor.record_failure(
                    fortune_type="eastern",
                    error_type=ErrorType.VALIDATION,
                    error_message=str(e)[:200],
                )
                return FortuneResponse(
                    success=True,
                    validated=False,
                    type="eastern",
                    data=parsed,  # 원본 LLM 출력 그대로
                    errors=error_messages,
                    latency_ms=latency_ms,
                )

        except httpx.ConnectError as e:
            logger.error("eastern_graceful_connection_error", error=str(e))
            # 연결 에러 로깅
            await self.response_logger.log_connection_error(
                fortune_type="eastern",
                request_input=birth_data,
                error_message=str(e),
                model_name=model_name,
                temperature=self._temperature,
            )
            # 연결 실패 모니터에 기록
            self.validation_monitor.record_failure(
                fortune_type="eastern",
                error_type=ErrorType.CONNECTION,
                error_message=str(e),
            )
            return FortuneResponse(
                success=False,
                validated=False,
                type="eastern",
                data={},
                errors=[f"LLM 연결 실패: {str(e)}"],
                latency_ms=0,
            )

        except httpx.TimeoutException as e:
            logger.error("eastern_graceful_timeout_error", error=str(e))
            # 타임아웃 에러 로깅
            await self.response_logger.log_timeout_error(
                fortune_type="eastern",
                request_input=birth_data,
                error_message=str(e),
                model_name=model_name,
                temperature=self._temperature,
            )
            # 타임아웃 실패 모니터에 기록
            self.validation_monitor.record_failure(
                fortune_type="eastern",
                error_type=ErrorType.TIMEOUT,
                error_message=str(e),
            )
            return FortuneResponse(
                success=False,
                validated=False,
                type="eastern",
                data={},
                errors=[f"LLM 타임아웃: {str(e)}"],
                latency_ms=0,
            )

        except Exception as e:
            logger.error("eastern_graceful_error", error=str(e), exc_info=True)
            # 알 수 없는 에러 로깅
            await self.response_logger.log_unknown_error(
                fortune_type="eastern",
                request_input=birth_data,
                error_type=type(e).__name__,
                error_message=str(e),
                model_name=model_name,
                temperature=self._temperature,
            )
            # 알 수 없는 에러 모니터에 기록
            self.validation_monitor.record_failure(
                fortune_type="eastern",
                error_type=ErrorType.UNKNOWN,
                error_message=str(e),
            )
            return FortuneResponse(
                success=False,
                validated=False,
                type="eastern",
                data={},
                errors=[f"LLM 호출 실패: {str(e)}"],
                latency_ms=0,
            )

    async def generate_western_graceful(
        self,
        birth_data: dict[str, Any],
    ) -> FortuneResponse:
        """
        서양 점성술 운세 생성 (Graceful Degradation)

        검증 실패해도 200 응답을 반환합니다.
        - 검증 성공: validated=True, data=검증된 데이터
        - 검증 실패: validated=False, data=원본 LLM 출력, errors=에러 목록

        Args:
            birth_data: 출생 정보

        Returns:
            FortuneResponse (항상 성공, validated 필드로 검증 상태 구분)
        """
        # 필수 필드 검증
        required_fields = ["birth_year", "birth_month", "birth_day"]
        for field in required_fields:
            if field not in birth_data:
                return FortuneResponse(
                    success=False,
                    validated=False,
                    type="western",
                    data={},
                    errors=[f"필수 필드 누락: {field}"],
                    latency_ms=0,
                )

        # 서버에서 별자리 계산
        sun_sign = get_sun_sign(
            month=birth_data["birth_month"],
            day=birth_data["birth_day"],
        )
        sun_sign_kr = ZODIAC_KR_MAP[sun_sign]

        user_prompt = build_western_generation_prompt(
            birth_year=birth_data["birth_year"],
            birth_month=birth_data["birth_month"],
            birth_day=birth_data["birth_day"],
            birth_hour=birth_data.get("birth_hour", 12),
            birth_minute=birth_data.get("birth_minute", 0),
            latitude=birth_data.get("latitude", 37.5665),
            longitude=birth_data.get("longitude", 126.9780),
            sun_sign=sun_sign_kr,
        )

        # LLM 호출
        messages = [
            {"role": "system", "content": WESTERN_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        gen_config = GenerationConfig(
            max_tokens=self._max_tokens,
            temperature=self._temperature,
            top_p=0.8,
            presence_penalty=1.5,
            response_format={"type": "json_object"},
        )

        # 로깅 메타데이터 (안전하게 가져오기)
        try:
            model_name = self._provider.config.model if self._provider else None
        except AttributeError:
            model_name = None

        try:
            response = await self.provider.chat(messages, gen_config)
            content = response.text
            latency_ms = response.latency_ms

            # <think> 태그 제거 (Qwen3)
            if "<think>" in content:
                content = content.split("</think>")[-1].strip()

            # JSON 파싱
            try:
                parsed = json.loads(content)
            except json.JSONDecodeError as e:
                logger.warning("western_graceful_json_error", error=str(e))
                # JSON 파싱 에러 로깅
                await self.response_logger.log_json_parse_error(
                    fortune_type="western",
                    request_input=birth_data,
                    raw_response=content,
                    error_message=str(e),
                    latency_ms=latency_ms,
                    model_name=model_name,
                    temperature=self._temperature,
                )
                # 검증 실패 모니터에 기록
                self.validation_monitor.record_failure(
                    fortune_type="western",
                    error_type=ErrorType.JSON_PARSE,
                    error_message=str(e),
                )
                return FortuneResponse(
                    success=True,
                    validated=False,
                    type="western",
                    data={"raw_content": content},
                    errors=[f"JSON 파싱 실패: {e}"],
                    latency_ms=latency_ms,
                )

            # 후처리 적용 (전체 활성화 + 서양 후처리 활성화된 경우)
            # calculated_zodiac을 전달하여 서버 계산값으로 강제 덮어쓰기 (FR-006)
            if self._enable_postprocess and self._enable_western_postprocess:
                try:
                    parsed = self.western_postprocessor.process(
                        parsed,
                        calculated_zodiac=sun_sign.value,
                    )
                    logger.debug("western_postprocess_applied")
                except Exception as e:
                    logger.warning("western_postprocess_failed", error=str(e))
                    # 후처리 실패해도 원본으로 계속 진행 (fail-safe)

            # Pydantic 검증 시도
            try:
                validated_data = WesternFortuneDataV2.model_validate(parsed)
                logger.info(
                    "western_graceful_validated",
                    element=validated_data.element,
                    main_sign=validated_data.stats.main_sign.name,
                )
                # 성공 로깅
                await self.response_logger.log_success(
                    fortune_type="western",
                    request_input=birth_data,
                    raw_response=content,
                    parsed_response=validated_data.model_dump(),
                    latency_ms=latency_ms,
                    model_name=model_name,
                    temperature=self._temperature,
                )
                # 검증 성공 모니터에 기록
                self.validation_monitor.record_success(fortune_type="western")
                return FortuneResponse(
                    success=True,
                    validated=True,
                    type="western",
                    data=validated_data.model_dump(),
                    errors=None,
                    latency_ms=latency_ms,
                )
            except ValidationError as e:
                # 검증 실패 → 원본 데이터 + 에러 목록 반환
                error_messages = [f"{err['loc']}: {err['msg']}" for err in e.errors()]
                validation_errors = [
                    {"loc": list(err["loc"]), "msg": err["msg"], "type": err["type"]}
                    for err in e.errors()[:10]
                ]
                logger.warning(
                    "western_graceful_validation_failed",
                    errors=error_messages[:5],  # 최대 5개만 로깅
                )
                # 검증 에러 로깅
                await self.response_logger.log_validation_error(
                    fortune_type="western",
                    request_input=birth_data,
                    raw_response=content,
                    error_message=str(e),
                    validation_errors=validation_errors,
                    latency_ms=latency_ms,
                    model_name=model_name,
                    temperature=self._temperature,
                )
                # 검증 실패 모니터에 기록
                self.validation_monitor.record_failure(
                    fortune_type="western",
                    error_type=ErrorType.VALIDATION,
                    error_message=str(e)[:200],
                )
                return FortuneResponse(
                    success=True,
                    validated=False,
                    type="western",
                    data=parsed,  # 원본 LLM 출력 그대로
                    errors=error_messages,
                    latency_ms=latency_ms,
                )

        except httpx.ConnectError as e:
            logger.error("western_graceful_connection_error", error=str(e))
            # 연결 에러 로깅
            await self.response_logger.log_connection_error(
                fortune_type="western",
                request_input=birth_data,
                error_message=str(e),
                model_name=model_name,
                temperature=self._temperature,
            )
            # 연결 실패 모니터에 기록
            self.validation_monitor.record_failure(
                fortune_type="western",
                error_type=ErrorType.CONNECTION,
                error_message=str(e),
            )
            return FortuneResponse(
                success=False,
                validated=False,
                type="western",
                data={},
                errors=[f"LLM 연결 실패: {str(e)}"],
                latency_ms=0,
            )

        except httpx.TimeoutException as e:
            logger.error("western_graceful_timeout_error", error=str(e))
            # 타임아웃 에러 로깅
            await self.response_logger.log_timeout_error(
                fortune_type="western",
                request_input=birth_data,
                error_message=str(e),
                model_name=model_name,
                temperature=self._temperature,
            )
            # 타임아웃 실패 모니터에 기록
            self.validation_monitor.record_failure(
                fortune_type="western",
                error_type=ErrorType.TIMEOUT,
                error_message=str(e),
            )
            return FortuneResponse(
                success=False,
                validated=False,
                type="western",
                data={},
                errors=[f"LLM 타임아웃: {str(e)}"],
                latency_ms=0,
            )

        except Exception as e:
            logger.error("western_graceful_error", error=str(e), exc_info=True)
            # 알 수 없는 에러 로깅
            await self.response_logger.log_unknown_error(
                fortune_type="western",
                request_input=birth_data,
                error_type=type(e).__name__,
                error_message=str(e),
                model_name=model_name,
                temperature=self._temperature,
            )
            # 알 수 없는 에러 모니터에 기록
            self.validation_monitor.record_failure(
                fortune_type="western",
                error_type=ErrorType.UNKNOWN,
                error_message=str(e),
            )
            return FortuneResponse(
                success=False,
                validated=False,
                type="western",
                data={},
                errors=[f"LLM 호출 실패: {str(e)}"],
                latency_ms=0,
            )


# ============================================================
# 팩토리 함수 (의존성 주입용)
# ============================================================


async def create_fortune_generator(
    provider: AWSProvider | None = None,
) -> FortuneGenerator:
    """
    FortuneGenerator 인스턴스 생성 및 초기화

    FastAPI 의존성 주입에 사용합니다.

    Args:
        provider: AWS Provider 인스턴스 (옵션)

    Returns:
        초기화된 FortuneGenerator

    사용 예시 (FastAPI):
        @router.post("/fortune")
        async def create_fortune(
            generator: FortuneGenerator = Depends(create_fortune_generator)
        ):
            ...
    """
    generator = FortuneGenerator(provider=provider)
    await generator.initialize()
    return generator
