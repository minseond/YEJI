"""동양 사주 API 엔드포인트

## 사용 흐름

```
1. 사주 분석 요청
   POST /api/v1/fortune/eastern
   {
     "birth_date": "1990-05-15",
     "birth_time": "14:30",
     "gender": "M"
   }

2. 응답 (fortune_key 저장됨)
   - fortune_key: "eastern:1990-05-15:14:30:M"
   - element: 대표 오행 (FIRE, WATER 등)
   - chart: 사주 차트 (년/월/일/시주)
   - stats: 천간지지/오행/음양/십신 통계
   - final_verdict: 종합 분석
   - lucky: 행운 정보

3. Quick Summary에서 상세 분석 조회 가능
   POST /api/v1/fortune/quick-summary
   { "fortune_id": "eastern:...", "fortune_type": "eastern", "category": "MONEY" }
```
"""

from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse

from yeji_ai.models.fortune.eastern import EasternFortuneRequest
from yeji_ai.models.fortune.summary import FortuneSummaryRequest, FortuneSummaryResponse
from yeji_ai.models.user_fortune import FortuneResponse, SajuDataV2
from yeji_ai.services.fortune_generator import (
    FortuneGenerator,
    FortuneGeneratorError,
    LLMErrorType,
)
from yeji_ai.services.fortune_key_service import (
    generate_eastern_fortune_key,
    get_fortune,
    store_fortune,
)
from yeji_ai.services.summary_service import get_summary_service

logger = structlog.get_logger()

router = APIRouter()

# FortuneGenerator 인스턴스 (싱글톤, 지연 초기화)
_generator: FortuneGenerator | None = None


async def get_generator() -> FortuneGenerator:
    """FortuneGenerator 싱글톤 인스턴스 반환"""
    global _generator
    if _generator is None:
        _generator = FortuneGenerator()
        await _generator.initialize()
    return _generator


@router.post(
    "/eastern",
    response_model=None,  # graceful 모드에서 FortuneResponse 반환 시 검증 충돌 방지
    summary="동양 사주 분석",
    description="생년월일시를 기반으로 사주팔자를 분석합니다.",
    responses={
        200: {
            "description": "분석 성공",
            "content": {
                "application/json": {
                    "example": {
                        "fortune_key": "eastern:1990-05-15:14:30:M",
                        "element": "FIRE",
                        "chart": {
                            "summary": "甲子년 乙丑월 丙寅일",
                            "year": {"gan": "甲", "ji": "子", "element_code": "WOOD"},
                        },
                        "stats": {
                            "cheongan_jiji": {},
                            "five_elements": {"summary": "", "list": []},
                            "yin_yang_ratio": {"summary": "", "yin": 50, "yang": 50},
                            "ten_gods": {"summary": "", "list": []},
                        },
                        "final_verdict": {
                            "summary": "종합 분석",
                            "strength": "강점",
                            "weakness": "약점",
                            "advice": "조언",
                        },
                        "lucky": {"color": "빨강", "number": "7", "item": "부적"},
                        "_debug_stored": True,
                    }
                }
            },
        },
        400: {"description": "잘못된 요청"},
        500: {"description": "서버 오류"},
    },
)
async def analyze_eastern(
    request: EasternFortuneRequest,
    skip_validation: bool = Query(
        default=False,
        description="True: Pydantic 검증 스킵, raw LLM 응답 반환 (테스트용)",
    ),
    graceful: bool = Query(
        default=True,
        description="Graceful Degradation 모드 - 검증 실패해도 200 응답 반환 (기본 활성화)",
    ),
) -> SajuDataV2 | FortuneResponse | dict[str, Any]:
    """동양 사주 분석 API

    생년월일시를 기반으로 사주팔자를 분석하여 오행, 음양, 십신 해석을 제공합니다.

    **요청:**
    - birth_date (필수): YYYY-MM-DD
    - birth_time (선택): HH:MM
    - gender (선택): M/F
    - name (선택)

    **응답:**
    - fortune_key: 운세 식별자 (예: "eastern:1990-05-15:14:30:M")
    - element: 대표 오행 코드
    - chart: 사주 차트 (년/월/일/시주)
    - stats: 천간지지/오행/음양/십신 통계
    - final_verdict: 종합 분석 (강점/약점/조언)
    - lucky: 행운 정보 (색상/숫자/아이템)
    - _debug_stored: Redis 저장 성공 여부 (개발용)
    """
    logger.info(
        "eastern_fortune_request",
        birth_date=request.birth_date,
        birth_time=request.birth_time,
        skip_validation=skip_validation,
    )

    try:
        # 캐시 확인 (fortune_key 먼저 생성)
        fortune_key = generate_eastern_fortune_key(
            birth_date=request.birth_date,
            birth_time=request.birth_time,
            gender=request.gender,
        )
        cached = await get_fortune(fortune_key)
        if cached:
            logger.info("eastern_fortune_cache_hit", fortune_key=fortune_key)
            return cached

        # 날짜/시간 파싱
        birth_parts = request.birth_date.split("-")
        birth_year = int(birth_parts[0])
        birth_month = int(birth_parts[1])
        birth_day = int(birth_parts[2])

        birth_hour = 12  # 기본값
        if request.birth_time:
            birth_hour = int(request.birth_time.split(":")[0])

        gender = "unknown"
        if request.gender:
            gender = "male" if request.gender.upper() == "M" else "female"

        birth_data = {
            "birth_year": birth_year,
            "birth_month": birth_month,
            "birth_day": birth_day,
            "birth_hour": birth_hour,
            "gender": gender,
        }

        generator = await get_generator()

        # graceful=True: Graceful Degradation 모드 (검증 실패해도 200 응답)
        if graceful:
            logger.info("eastern_fortune_graceful_mode", birth_date=request.birth_date)
            graceful_response = await generator.generate_eastern_graceful(birth_data)

            # fortune_key 생성 및 저장 (graceful 모드에서도)
            fortune_key = generate_eastern_fortune_key(
                birth_date=request.birth_date,
                birth_time=request.birth_time,
                gender=request.gender,
            )

            # Pydantic 모델 또는 dict 처리
            if hasattr(graceful_response, "model_dump"):
                response_dict = graceful_response.model_dump()
            elif isinstance(graceful_response, dict):
                response_dict = graceful_response
            else:
                response_dict = dict(graceful_response)

            response_dict["fortune_key"] = fortune_key
            stored = await store_fortune(fortune_key, response_dict)
            logger.info("fortune_store_result", fortune_key=fortune_key, stored=stored)
            response_dict["_debug_stored"] = stored

            return response_dict

        # skip_validation=True: raw LLM 응답 반환 (테스트용)
        if skip_validation:
            logger.info("eastern_fortune_skip_validation", birth_date=request.birth_date)
            raw_response = await generator.generate_eastern_raw(birth_data)
            return JSONResponse(content=raw_response)

        # 정상 모드: Pydantic 검증 수행
        response = await generator.generate_eastern(birth_data)

        logger.info(
            "eastern_fortune_success",
            birth_date=request.birth_date,
            element=response.element,
        )

        # fortune_key 생성 및 저장
        fortune_key = generate_eastern_fortune_key(
            birth_date=request.birth_date,
            birth_time=request.birth_time,
            gender=request.gender,
        )

        # Redis에 fortune 데이터 저장
        response_dict = response.model_dump() if hasattr(response, 'model_dump') else response
        response_dict["fortune_key"] = fortune_key
        await store_fortune(fortune_key, response_dict)

        # fortune_key 포함하여 반환
        return response_dict

    except FortuneGeneratorError as e:
        logger.error(
            "eastern_fortune_generator_error",
            error=str(e),
            error_type=e.error_type.value,
            error_code=e.error_code,
            has_raw_content=e.raw_content is not None,
        )

        # 에러 타입에 따른 HTTP 상태 코드 결정
        # - validation: 502 Bad Gateway (LLM 응답 스키마 불일치)
        # - connection: 503 Service Unavailable (LLM 서비스 연결 불가)
        # - timeout: 504 Gateway Timeout (LLM 응답 타임아웃)
        # - unknown: 503 Service Unavailable (분류되지 않은 에러)
        status_code_map = {
            LLMErrorType.VALIDATION: status.HTTP_502_BAD_GATEWAY,
            LLMErrorType.CONNECTION: status.HTTP_503_SERVICE_UNAVAILABLE,
            LLMErrorType.TIMEOUT: status.HTTP_504_GATEWAY_TIMEOUT,
            LLMErrorType.UNKNOWN: status.HTTP_503_SERVICE_UNAVAILABLE,
        }
        http_status = status_code_map.get(e.error_type, status.HTTP_503_SERVICE_UNAVAILABLE)

        # 표준화된 에러 응답 구조 반환
        raise HTTPException(
            status_code=http_status,
            detail=e.to_error_response(),
        )
    except ValueError as e:
        logger.warning("eastern_fortune_validation_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"입력값 오류: {str(e)}",
        )
    except Exception as e:
        logger.error("eastern_fortune_error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"사주 분석 중 오류가 발생했습니다: {str(e)}",
        )


@router.get(
    "/eastern/enums",
    summary="동양 사주 Enum 목록",
    description="프론트엔드에서 사용 가능한 Enum 목록을 반환합니다.",
    tags=["fortune-enum"],
    include_in_schema=False,  # Enum 조회 - Swagger에서 숨김
)
async def get_eastern_enums():
    """
    동양 사주 관련 Enum 목록 조회

    프론트엔드 TypeScript 타입 정의에 사용할 수 있는
    모든 Enum 값과 레이블을 반환합니다.
    """
    from yeji_ai.models.enums import (
        CheonGanCode,
        CommonBadge,
        EasternBadge,
        ElementCode,
        JiJiCode,
        PillarKey,
        TenGodCode,
        TenGodGroupCode,
        YinYangBalance,
    )

    return {
        "element_codes": [
            {"code": e.value, "label_ko": e.label_ko, "label_hanja": e.label_hanja}
            for e in ElementCode
        ],
        "cheongan_codes": [
            {
                "code": c.value,
                "hangul": c.hangul,
                "hanja": c.hanja,
                "element": c.element,
                "yinyang": c.yinyang,
            }
            for c in CheonGanCode
        ],
        "jiji_codes": [
            {
                "code": j.value,
                "hangul": j.hangul,
                "hanja": j.hanja,
                "element": j.element,
                "yinyang": j.yinyang,
                "zodiac_animal": j.zodiac_animal,
            }
            for j in JiJiCode
        ],
        "ten_god_codes": [
            {
                "code": t.value,
                "label_ko": t.label_ko,
                "hanja": t.hanja,
                "group": t.group,
            }
            for t in TenGodCode
        ],
        "ten_god_group_codes": [
            {"code": g.value, "label_ko": g.label_ko, "meaning": g.meaning}
            for g in TenGodGroupCode
        ],
        "pillar_keys": [
            {"code": p.value, "label_ko": p.label_ko, "meaning": p.meaning}
            for p in PillarKey
        ],
        "yinyang_balance": [
            {"code": y.value, "label_ko": y.label_ko}
            for y in YinYangBalance
        ],
        "eastern_badges": [
            {"code": b.value, "label_ko": b.label_ko}
            for b in EasternBadge
        ],
        "common_badges": [
            {"code": b.value, "label_ko": b.label_ko}
            for b in CommonBadge
        ],
    }


@router.post(
    "/eastern/summary",
    response_model=FortuneSummaryResponse,
    summary="동양 사주 요약 조회",
    description="fortune_key로 사주 분석 요약을 조회합니다. 캐시된 요약이 없으면 생성합니다.",
    responses={
        200: {"description": "요약 조회 성공"},
        404: {"description": "Fortune 데이터 없음"},
    },
)
async def get_eastern_summary(
    request: FortuneSummaryRequest,
) -> FortuneSummaryResponse:
    """동양 사주 요약 API

    fortune_key로 Redis에서 사주 데이터를 조회하고 요약을 반환합니다.
    요약이 캐시되어 있으면 재사용, 없으면 생성 후 캐시합니다.
    """
    logger.info("eastern_summary_request", fortune_key=request.fortune_key)

    # fortune_key 유효성 검사
    if not request.fortune_key.startswith("eastern:"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="잘못된 fortune_key 형식입니다. eastern:으로 시작해야 합니다.",
        )

    service = get_summary_service()
    result = await service.get_summary_with_metadata(request.fortune_key)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사주 분석 데이터를 찾을 수 없습니다. 먼저 /fortune/eastern API로 분석해주세요.",
        )

    return FortuneSummaryResponse(**result)
