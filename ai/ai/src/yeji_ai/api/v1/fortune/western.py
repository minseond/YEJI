"""서양 점성술 API 엔드포인트

## 사용 흐름

```
1. 점성술 분석 요청
   POST /api/v1/fortune/western
   {
     "birth_date": "1990-05-15",
     "birth_time": "14:30",
     "birth_place": "서울"
   }

2. 응답 (fortune_key 저장됨)
   - fortune_key: "western:1990-05-15:14:30"
   - element: 대표 원소 (FIRE, WATER, AIR, EARTH)
   - stats: 별자리/원소/양태/키워드 통계
   - fortune_content: 운세 콘텐츠
   - lucky: 행운 정보

3. Quick Summary에서 상세 분석 조회 가능
   POST /api/v1/fortune/quick-summary
   { "fortune_id": "western:...", "fortune_type": "western", "category": "LOVE" }
```
"""

from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse

from yeji_ai.models.fortune.summary import FortuneSummaryRequest, FortuneSummaryResponse
from yeji_ai.models.fortune.western import WesternFortuneRequest
from yeji_ai.models.user_fortune import FortuneResponse, WesternFortuneDataV2
from yeji_ai.services.fortune_generator import (
    FortuneGenerator,
    FortuneGeneratorError,
    LLMErrorType,
)
from yeji_ai.services.fortune_key_service import (
    generate_western_fortune_key,
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
    "/western",
    response_model=None,  # graceful 모드에서 FortuneResponse 반환 시 검증 충돌 방지
    summary="서양 점성술 분석",
    description="생년월일시와 출생지를 기반으로 출생 차트를 분석합니다.",
    responses={
        200: {
            "description": "분석 성공",
            "content": {
                "application/json": {
                    "example": {
                        "fortune_key": "western:1990-05-15:14:30",
                        "element": "FIRE",
                        "stats": {
                            "main_sign": {"name": "양자리"},
                            "element_summary": "불 원소가 강함",
                            "element_4_distribution": [],
                            "modality_summary": "활동궁이 우세",
                            "modality_3_distribution": [],
                            "keywords_summary": "열정적, 주도적",
                            "keywords": ["열정", "리더십"],
                        },
                        "fortune_content": {
                            "overview": "전체 개요",
                            "detailed_analysis": [],
                            "advice": "조언",
                        },
                        "lucky": {"color": "빨강", "number": "9"},
                    }
                }
            },
        },
        400: {"description": "잘못된 요청"},
        500: {"description": "서버 오류"},
    },
)
async def analyze_western(
    request: WesternFortuneRequest,
    skip_validation: bool = Query(
        default=False,
        description="True: Pydantic 검증 스킵, raw LLM 응답 반환 (테스트용)",
    ),
    graceful: bool = Query(
        default=True,
        description="Graceful Degradation 모드 - 검증 실패해도 200 응답 반환 (기본 활성화)",
    ),
) -> WesternFortuneDataV2 | FortuneResponse | dict[str, Any]:
    """서양 점성술 분석 API

    생년월일시와 출생지를 기반으로 출생 차트를 분석하여 원소, 모달리티, 키워드 해석을 제공합니다.

    **요청:**
    - birth_date (필수): YYYY-MM-DD
    - birth_time (선택): HH:MM
    - birth_place (선택): 출생지역
    - latitude/longitude (선택): 정확한 좌표

    **응답:**
    - fortune_key: 운세 식별자 (예: "western:1990-05-15:14:30")
    - element: 대표 원소 코드
    - stats: 별자리/원소/양태/키워드 통계
    - fortune_content: 운세 콘텐츠 (개요/상세분석/조언)
    - lucky: 행운 정보 (색상/숫자)
    """
    logger.info(
        "western_fortune_request",
        birth_date=request.birth_date,
        birth_time=request.birth_time,
        birth_place=request.birth_place,
        skip_validation=skip_validation,
    )

    try:
        # 캐시 확인 (fortune_key 먼저 생성)
        fortune_key = generate_western_fortune_key(
            birth_date=request.birth_date,
            birth_time=request.birth_time,
        )
        cached = await get_fortune(fortune_key)
        if cached:
            logger.info("western_fortune_cache_hit", fortune_key=fortune_key)
            return cached

        # 날짜/시간 파싱
        birth_parts = request.birth_date.split("-")
        birth_year = int(birth_parts[0])
        birth_month = int(birth_parts[1])
        birth_day = int(birth_parts[2])

        birth_hour = 12  # 기본값
        birth_minute = 0
        if request.birth_time:
            time_parts = request.birth_time.split(":")
            birth_hour = int(time_parts[0])
            if len(time_parts) > 1:
                birth_minute = int(time_parts[1])

        # 좌표 (서울 기본값)
        latitude = request.latitude if request.latitude else 37.5665
        longitude = request.longitude if request.longitude else 126.9780

        birth_data = {
            "birth_year": birth_year,
            "birth_month": birth_month,
            "birth_day": birth_day,
            "birth_hour": birth_hour,
            "birth_minute": birth_minute,
            "latitude": latitude,
            "longitude": longitude,
        }

        generator = await get_generator()

        # graceful=True: Graceful Degradation 모드 (검증 실패해도 200 응답)
        if graceful:
            logger.info("western_fortune_graceful_mode", birth_date=request.birth_date)
            graceful_response = await generator.generate_western_graceful(birth_data)

            # fortune_key 생성 및 저장 (graceful 모드에서도)
            fortune_key = generate_western_fortune_key(
                birth_date=request.birth_date,
                birth_time=request.birth_time,
            )

            # Pydantic 모델 또는 dict 처리
            if hasattr(graceful_response, "model_dump"):
                response_dict = graceful_response.model_dump()
            elif isinstance(graceful_response, dict):
                response_dict = graceful_response
            else:
                response_dict = dict(graceful_response)

            response_dict["fortune_key"] = fortune_key
            await store_fortune(fortune_key, response_dict)

            return response_dict

        # skip_validation=True: raw LLM 응답 반환 (테스트용)
        if skip_validation:
            logger.info("western_fortune_skip_validation", birth_date=request.birth_date)
            raw_response = await generator.generate_western_raw(birth_data)
            return JSONResponse(content=raw_response)

        # 정상 모드: Pydantic 검증 수행
        response = await generator.generate_western(birth_data)

        logger.info(
            "western_fortune_success",
            birth_date=request.birth_date,
            element=response.element,
        )

        # fortune_key 생성 및 저장
        fortune_key = generate_western_fortune_key(
            birth_date=request.birth_date,
            birth_time=request.birth_time,
        )

        # Redis에 fortune 데이터 저장
        response_dict = response.model_dump() if hasattr(response, "model_dump") else response
        response_dict["fortune_key"] = fortune_key
        await store_fortune(fortune_key, response_dict)

        # fortune_key 포함하여 반환
        return response_dict

    except FortuneGeneratorError as e:
        logger.error(
            "western_fortune_generator_error",
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
        logger.warning("western_fortune_validation_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"입력값 오류: {str(e)}",
        )
    except Exception as e:
        logger.error("western_fortune_error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"점성술 분석 중 오류가 발생했습니다: {str(e)}",
        )


@router.get(
    "/western/enums",
    summary="서양 점성술 Enum 목록",
    description="프론트엔드에서 사용 가능한 Enum 목록을 반환합니다.",
    tags=["fortune-enum"],
    include_in_schema=False,  # Enum 조회 - Swagger에서 숨김
)
async def get_western_enums():
    """
    서양 점성술 관련 Enum 목록 조회

    프론트엔드 TypeScript 타입 정의에 사용할 수 있는
    모든 Enum 값과 레이블을 반환합니다.
    """
    from yeji_ai.models.enums import (
        AspectCode,
        AspectNature,
        CommonBadge,
        HouseCode,
        PlanetCode,
        WesternBadge,
        ZodiacCode,
        ZodiacElement,
        ZodiacModality,
    )

    return {
        "zodiac_codes": [
            {
                "code": z.value,
                "label_ko": z.label_ko,
                "symbol": z.symbol,
                "element": z.element,
                "modality": z.modality,
                "ruling_planet": z.ruling_planet,
            }
            for z in ZodiacCode
        ],
        "zodiac_elements": [
            {"code": e.value, "label_ko": e.label_ko, "signs": e.signs}
            for e in ZodiacElement
        ],
        "zodiac_modalities": [
            {"code": m.value, "label_ko": m.label_ko, "meaning": m.meaning, "signs": m.signs}
            for m in ZodiacModality
        ],
        "planet_codes": [
            {
                "code": p.value,
                "label_ko": p.label_ko,
                "symbol": p.symbol,
                "meaning": p.meaning,
                "is_personal": p.is_personal,
            }
            for p in PlanetCode
        ],
        "house_codes": [
            {"code": h.value, "number": h.number, "label_ko": h.label_ko, "meaning": h.meaning}
            for h in HouseCode
        ],
        "aspect_codes": [
            {
                "code": a.value,
                "label_ko": a.label_ko,
                "symbol": a.symbol,
                "degree": a.degree,
                "nature": a.nature,
            }
            for a in AspectCode
        ],
        "aspect_natures": [
            {"code": n.value, "label_ko": n.label_ko}
            for n in AspectNature
        ],
        "western_badges": [
            {"code": b.value, "label_ko": b.label_ko}
            for b in WesternBadge
        ],
        "common_badges": [
            {"code": b.value, "label_ko": b.label_ko}
            for b in CommonBadge
        ],
    }


@router.post(
    "/western/summary",
    response_model=FortuneSummaryResponse,
    summary="서양 점성술 요약 조회",
    description="fortune_key로 점성술 분석 요약을 조회합니다. 캐시된 요약이 없으면 생성합니다.",
    responses={
        200: {"description": "요약 조회 성공"},
        404: {"description": "Fortune 데이터 없음"},
    },
)
async def get_western_summary(
    request: FortuneSummaryRequest,
) -> FortuneSummaryResponse:
    """서양 점성술 요약 API

    fortune_key로 Redis에서 점성술 데이터를 조회하고 요약을 반환합니다.
    요약이 캐시되어 있으면 재사용, 없으면 생성 후 캐시합니다.
    """
    logger.info("western_summary_request", fortune_key=request.fortune_key)

    # fortune_key 유효성 검사
    if not request.fortune_key.startswith("western:"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="잘못된 fortune_key 형식입니다. western:으로 시작해야 합니다.",
        )

    service = get_summary_service()
    result = await service.get_summary_with_metadata(request.fortune_key)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="점성술 분석 데이터를 찾을 수 없습니다. 먼저 /fortune/western API로 분석해주세요.",
        )

    return FortuneSummaryResponse(**result)
