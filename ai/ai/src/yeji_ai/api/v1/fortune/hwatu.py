"""화투점 리딩 API 엔드포인트

⚠️ 현재 미구현 상태 (NotImplementedError)

## 계획된 사용 흐름

```
1. 카드 목록 조회 (선택)
   GET /api/v1/fortune/hwatu/deck
   → 48장 화투 카드 정보

2. 화투점 리딩 요청
   POST /api/v1/fortune/hwatu/reading
   {
     "question": "궁합이 어떨까요?"
   }

3. 응답
   - cards: 4장 카드 (본인/상대/과정/결과)
   - interpretation: LLM 해석
```
"""

import asyncio
from typing import Any

import structlog
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, status

from yeji_ai.models.enums import PromptVersion

from yeji_ai.models.fortune.hwatu import (
    HwatuCardInput,
    HwatuReadingRequest,
    HwatuReadingResponse,
    HwatuSingleCardRequest,
    HwatuSingleCardResponse,
    HwatuSummaryRequest,
    HwatuSummaryResponse,
)
from yeji_ai.models.user_fortune import FortuneResponse
from yeji_ai.services.hwatu_service import HwatuService, HwatuServiceError
from yeji_ai.services.progressive_cache_service import (
    get_hwatu_reading_cache,
    store_hwatu_reading_cache,
    get_random_cached_hwatu_reading,
    background_expand_hwatu_cache,
)

logger = structlog.get_logger()

router = APIRouter()

# HwatuService 인스턴스 (싱글톤, 지연 초기화)
_service: HwatuService | None = None


async def get_service() -> HwatuService:
    """HwatuService 싱글톤 인스턴스 반환"""
    global _service
    if _service is None:
        _service = HwatuService()
        await _service.initialize()
    return _service


@router.post(
    "/hwatu/reading",
    response_model=None,
    summary="화투점 4장 스프레드 리딩",
    description="4장 카드(본인/상대/과정/결과)를 기반으로 화투점 리딩을 생성합니다.",
    responses={
        200: {
            "description": "리딩 성공",
            "content": {
                "application/json": {
                    "example": {
                        "meta": {
                            "model": "card-v1",
                            "generated_at": "2026-02-03T02:15:30Z",
                        },
                        "cards": [
                            {
                                "position": 1,
                                "card_code": 7,
                                "is_reversed": False,
                                "interpretation": "지금은 흐름을 읽고 가볍게 접근하는 것이 유리합니다.",
                            },
                            {
                                "position": 2,
                                "card_code": 18,
                                "is_reversed": False,
                                "interpretation": "상대방이나 외부 상황은 변화의 기운을 품고 있습니다.",
                            },
                            {
                                "position": 3,
                                "card_code": 32,
                                "is_reversed": False,
                                "interpretation": "두 힘이 맞물리며 조율과 타협의 과정을 거칩니다.",
                            },
                            {
                                "position": 4,
                                "card_code": 41,
                                "is_reversed": False,
                                "interpretation": "결과적으로 안정과 정리의 시기를 맞이하게 됩니다.",
                            },
                        ],
                        "overall_reading": "전체적으로 큰 승부보다 리스크를 줄이고 흐름을 정리하는 선택이 유리합니다.",
                    }
                }
            },
        },
        400: {"description": "잘못된 요청"},
        503: {"description": "서비스 오류"},
    },
)
async def read_hwatu(
    request: HwatuReadingRequest,
    background_tasks: BackgroundTasks,
    graceful: bool = Query(
        default=True,
        description="Graceful Degradation 모드 - 검증 실패해도 200 응답 + 원본 데이터 반환",
    ),
    force: bool = Query(
        default=False,
        description="True면 캐시 무시하고 강제 재생성",
    ),
    live: bool = Query(
        default=False,
        description="True면 LLM 실시간 생성, False면 캐시된 조합 중 랜덤 반환 + 백그라운드 새 조합 생성",
    ),
    prompt_version: PromptVersion = Query(
        default=PromptVersion.STANDARD,
        description="프롬프트 버전 (standard: 기본, lite: 경량화)",
    ),
) -> HwatuReadingResponse | FortuneResponse | dict[str, Any]:
    """
    화투점 4장 스프레드 리딩 API

    4장의 카드(본인/상대/과정/결과)를 기반으로 화투점 리딩을 생성합니다.

    **요청 파라미터:**
    - **category**: "HWATU" (고정)
    - **question**: 질문 (최대 500자)
    - **cards**: 4장의 카드 (position 1~4, card_code 0~47)

    **응답 구조:**
    - **meta**: 모델 및 생성 시각
    - **cards**: 카드별 해석 (4장)
    - **overall_reading**: 종합 해석

    **예시:**
    ```json
    {
        "category": "HWATU",
        "question": "오늘 금전운이 궁금해요",
        "cards": [
            {"position": 1, "card_code": 7, "is_reversed": false},
            {"position": 2, "card_code": 18, "is_reversed": false},
            {"position": 3, "card_code": 32, "is_reversed": false},
            {"position": 4, "card_code": 41, "is_reversed": false}
        ]
    }
    ```

    **카드 위치 의미:**
    - position 1: 본인/현재 (질문자의 현재 상태, 심리, 주도권)
    - position 2: 상대/환경 (상대방의 마음, 외부 상황, 보이지 않는 변수)
    - position 3: 과정/관계 (두 요소가 맞물리며 흘러가는 방식)
    - position 4: 결과/조언 (가까운 미래의 결론, 행동 지침)

    **에러 응답:**
    - 400: 잘못된 요청 (card_code 범위 초과, position 중복 등)
    - 503: LLM 서비스 오류
    - 500: 내부 오류
    """
    logger.info(
        "hwatu_reading_request",
        question=request.question,
        card_count=len(request.cards),
        force=force,
        live=live,
    )

    # live=False: 캐시된 조합 중 랜덤 반환 + 백그라운드에서 새 조합 생성 (기본 동작)
    if not live and not force:
        random_cached = await get_random_cached_hwatu_reading(request.question)
        if random_cached:
            logger.info("hwatu_random_cache_used", question=request.question)

            # 백그라운드에서 새로운 랜덤 조합 생성 (캐시 풀 확장)
            async def _generate_hwatu_for_cache(cards: list[dict]) -> dict:
                """백그라운드 캐시 생성용 LLM 호출"""
                service = await get_service()
                # 카드 데이터를 HwatuReadingRequest 형태로 변환
                card_inputs = [
                    HwatuCardInput(
                        position=c["position"],
                        card_code=c["card_code"],
                        is_reversed=c.get("is_reversed", False),
                    )
                    for c in cards
                ]
                temp_request = HwatuReadingRequest(
                    category=request.category,
                    question=request.question,
                    cards=card_inputs,
                )
                response = await service.generate_reading(temp_request, prompt_version=prompt_version)
                return response.model_dump()

            background_tasks.add_task(
                background_expand_hwatu_cache,
                request.question,
                _generate_hwatu_for_cache,
            )
            logger.info("hwatu_background_cache_expansion_scheduled", category=request.question)

            return FortuneResponse(
                success=True,
                validated=True,
                type="eastern",
                data=random_cached,
            )
        # 캐시 없으면 아래 로직으로 실시간 생성
        logger.info("hwatu_no_cache_fallback_to_live", question=request.question)

    # 캐시 조회 (force=False일 때만) - 기존 exact-match 캐시
    cards_for_cache = [c.model_dump() for c in request.cards]
    if not force:
        cached = await get_hwatu_reading_cache(request.question, cards_for_cache)
        if cached:
            logger.info("hwatu_reading_cache_used", question=request.question)
            return FortuneResponse(
                success=True,
                validated=True,
                type="eastern",
                data=cached,
            )

    try:
        service = await get_service()

        # graceful=True: Graceful Degradation 모드 (검증 실패해도 200 응답)
        if graceful:
            logger.info("hwatu_reading_graceful_mode", question=request.question)
            try:
                response = await service.generate_reading(
                    request, prompt_version=prompt_version
                )
                response_data = response.model_dump()
                # 캐시 저장
                await store_hwatu_reading_cache(request.question, cards_for_cache, response_data)
                return FortuneResponse(
                    success=True,
                    validated=True,
                    type="eastern",  # TODO: type을 "hwatu"로 변경 (FortuneTypeLiteral 확장 필요)
                    data=response_data,
                )
            except Exception as e:
                logger.warning(
                    "hwatu_reading_validation_error",
                    error=str(e),
                    question=request.question,
                )
                # 검증 실패해도 200 응답 (원본 데이터 반환)
                return FortuneResponse(
                    success=True,
                    validated=False,
                    type="eastern",
                    data={},
                    errors=[str(e)],
                )

        # 정상 모드: Pydantic 검증 수행
        response = await service.generate_reading(request, prompt_version=prompt_version)

        logger.info(
            "hwatu_reading_success",
            question=request.question,
            card_count=len(response.cards),
        )

        return response

    except HwatuServiceError as e:
        logger.error(
            "hwatu_reading_service_error",
            error=str(e),
            error_code=e.error_code,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"화투 서비스 오류: {str(e)}",
        )
    except ValueError as e:
        logger.warning("hwatu_reading_validation_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"입력값 오류: {str(e)}",
        )
    except Exception as e:
        logger.error("hwatu_reading_error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"화투 리딩 중 오류가 발생했습니다: {str(e)}",
        )


@router.get(
    "/hwatu/deck",
    summary="화투 카드 전체 목록",
    description="48장 화투 카드 전체 목록을 반환합니다 (12개월 × 4장).",
    responses={
        200: {
            "description": "카드 목록 반환",
            "content": {
                "application/json": {
                    "example": {
                        "total": 48,
                        "months": 12,
                        "cards_per_month": 4,
                        "cards": [
                            {
                                "card_code": 0,
                                "month": 1,
                                "month_name": "송학",
                                "card_name": "송학 광",
                                "category": "광",
                                "points": 20,
                            },
                            {
                                "card_code": 1,
                                "month": 1,
                                "month_name": "송학",
                                "card_name": "송학 띠",
                                "category": "띠",
                                "points": 10,
                            },
                        ],
                    }
                }
            },
        }
    },
)
async def get_hwatu_deck() -> dict[str, Any]:
    """
    화투 카드 전체 목록 조회

    48장의 화투 카드 전체 목록을 반환합니다.
    - 12개월: 송학(1월) ~ 오동(12월)
    - 각 월 4장 (광, 띠, 피 등)

    프론트엔드에서 카드 선택 UI 구성에 사용할 수 있습니다.

    **카드 구성:**
    - card_code: 0~47 (순차적 코드)
    - month: 1~12 (월)
    - category: 광, 띠, 피, 동물, 홍단, 청단 등
    - points: 화투 점수 (광 20점, 띠/동물 10점, 피 5점 등)
    """
    logger.info("hwatu_deck_request")

    try:
        service = await get_service()
        deck = service.get_full_deck()

        logger.info(
            "hwatu_deck_success",
            total=len(deck),
            months=12,
            cards_per_month=4,
        )

        return {
            "total": len(deck),
            "months": 12,
            "cards_per_month": 4,
            "cards": deck,
        }

    except Exception as e:
        logger.error("hwatu_deck_error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"카드 목록 조회 중 오류가 발생했습니다: {str(e)}",
        )


# ============================================================
# 분할 API (병렬 호출용)
# ============================================================


@router.post(
    "/hwatu/card-reading",
    response_model=HwatuSingleCardResponse,
    summary="화투 카드 1장 해석 (병렬 호출용)",
    description="카드 1장만 해석합니다. FE에서 4개를 병렬로 호출하여 속도를 개선할 수 있습니다.",
)
async def read_single_hwatu_card(
    request: HwatuSingleCardRequest,
) -> HwatuSingleCardResponse:
    """
    화투 카드 1장 해석 API (병렬 호출용)

    **사용법:**
    - FE에서 4장의 카드를 각각 병렬로 호출
    - 각 호출은 ~25초 소요 (전체 97초 → 25초로 단축)

    **요청 파라미터:**
    - card_code: 카드 코드 (0~47)
    - position: 위치 (1~4)
    - question: 질문
    """
    logger.info(
        "hwatu_single_card_request",
        card_code=request.card_code,
        position=request.position,
    )

    try:
        service = await get_service()
        result = await service.generate_single_card_reading(
            card_code=request.card_code,
            position=request.position,
            question=request.question,
        )

        logger.info(
            "hwatu_single_card_success",
            card_code=request.card_code,
            position=request.position,
        )

        return HwatuSingleCardResponse(**result)

    except Exception as e:
        logger.error("hwatu_single_card_error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"카드 해석 중 오류: {str(e)}",
        )


@router.post(
    "/hwatu/summary",
    response_model=HwatuSummaryResponse,
    summary="화투 4장 종합 요약 (카드 해석 후 호출)",
    description="4장 카드 해석이 완료된 후 종합 요약을 생성합니다.",
)
async def generate_hwatu_summary(
    request: HwatuSummaryRequest,
) -> HwatuSummaryResponse:
    """
    화투 종합 요약 API

    **사용법:**
    - 4장 card-reading API 호출 완료 후 호출
    - 각 카드 해석 결과를 card_interpretations에 포함

    **요청 파라미터:**
    - question: 질문
    - card_interpretations: 4장 카드 해석 결과 배열
    """
    logger.info("hwatu_summary_request", question=request.question[:50])

    try:
        service = await get_service()
        result = await service.generate_summary_only(
            question=request.question,
            card_interpretations=request.card_interpretations,
        )

        logger.info("hwatu_summary_success")

        return HwatuSummaryResponse(
            overall_theme=result["overall_theme"],
            flow_analysis=result["flow_analysis"],
            advice=result["advice"],
            lucky=result["lucky"],
        )

    except Exception as e:
        logger.error("hwatu_summary_error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"종합 요약 생성 중 오류: {str(e)}",
        )
