"""타로 리딩 API 엔드포인트

## 사용 흐름

```
1. 카드 목록 조회 (선택)
   GET /api/v1/fortune/tarot/deck
   → 78장 전체 카드 정보

2. 타로 리딩 요청
   POST /api/v1/fortune/tarot/reading
   {
     "question": "오늘 연애운은?",
     "spread_type": "THREE_CARD"  // 기본값
   }

3. 응답
   - cards: 3장 카드 (과거/현재/미래)
   - interpretation: LLM 해석
   - overall_message: 종합 메시지
```
"""

import asyncio
from typing import Any

import structlog
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, status

from yeji_ai.models.fortune.tarot import TarotReadingRequest, TarotReadingResponse
from yeji_ai.models.user_fortune import FortuneResponse
from yeji_ai.services.progressive_cache_service import (
    get_tarot_reading_cache,
    store_tarot_reading_cache,
    get_random_cached_tarot_reading,
    background_expand_tarot_cache,
)
from yeji_ai.services.tarot_service import TarotService, TarotServiceError

logger = structlog.get_logger()

router = APIRouter()

# TarotService 인스턴스 (싱글톤, 지연 초기화)
_service: TarotService | None = None


async def get_service() -> TarotService:
    """TarotService 싱글톤 인스턴스 반환"""
    global _service
    if _service is None:
        _service = TarotService()
        await _service.initialize()
    return _service


@router.post(
    "/tarot/reading",
    response_model=None,
    summary="타로 3장 스프레드 리딩",
    description="3장 카드(과거/현재/미래)를 기반으로 타로 리딩을 생성합니다.",
    responses={
        200: {
            "description": "리딩 성공",
            "content": {
                "application/json": {
                    "example": {
                        "category": "tarot",
                        "spread_type": "THREE_CARD",
                        "question": "LOVE",
                        "cards": [
                            {
                                "position": "PAST",
                                "position_label": "과거",
                                "card_code": "FOOL",
                                "card_name": "바보",
                                "orientation": "UPRIGHT",
                                "orientation_label": "정방향",
                                "keywords": ["새로운 시작", "순수함", "모험"],
                                "interpretation": "과거에는 새로운 시작과 순수한 마음으로...",
                            },
                        ],
                        "summary": {
                            "overall_theme": "새로운 사랑의 시작과 성장",
                            "past_to_present": "과거의 순수한 마음이 현재의 감정으로...",
                            "present_to_future": "현재의 감정이 미래에 아름다운 관계로...",
                            "advice": "마음을 열고 솔직하게 다가가세요.",
                        },
                        "lucky": {
                            "color": "흰색",
                            "number": "0",
                            "element": "공기",
                            "timing": "새벽",
                        },
                    }
                }
            },
        },
        400: {"description": "잘못된 요청"},
        503: {"description": "서비스 오류"},
    },
)
async def read_tarot(
    request: TarotReadingRequest,
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
) -> TarotReadingResponse | FortuneResponse | dict[str, Any]:
    """
    타로 3장 스프레드 리딩 API

    3장의 카드(과거/현재/미래)를 기반으로 타로 리딩을 생성합니다.

    **요청 파라미터:**
    - **question**: 질문 (선택, 최대 500자)
    - **cards**: 3장의 카드 (PAST, PRESENT, FUTURE 필수)

    **응답 구조:**
    - **category**: "tarot" (고정)
    - **spread_type**: "THREE_CARD" (고정)
    - **question**: 질문 (없으면 null)
    - **cards**: 카드별 해석 (3장)
    - **summary**: 종합 해석
    - **lucky**: 행운 정보

    **예시:**
    ```json
    {
        "question": "LOVE",
        "cards": [
            {
                "position": "PAST",
                "card": {
                    "major": "FOOL",
                    "orientation": "UPRIGHT"
                }
            },
            {
                "position": "PRESENT",
                "card": {
                    "suit": "CUPS",
                    "rank": "ACE",
                    "orientation": "UPRIGHT"
                }
            },
            {
                "position": "FUTURE",
                "card": {
                    "major": "LOVERS",
                    "orientation": "UPRIGHT"
                }
            }
        ]
    }
    ```
    """
    logger.info(
        "tarot_reading_request",
        question=request.question.value,
        card_count=len(request.cards),
        force=force,
        live=live,
    )

    # live=False: 캐시된 조합 중 랜덤 반환 + 백그라운드에서 새 조합 생성 (기본 동작)
    if not live and not force:
        random_cached = await get_random_cached_tarot_reading(request.question.value)
        if random_cached:
            logger.info("tarot_random_cache_used", category=request.question.value)

            # 백그라운드에서 새로운 랜덤 조합 생성 (캐시 풀 확장)
            async def _generate_tarot_for_cache(cards: list[dict]) -> dict:
                """백그라운드 캐시 생성용 LLM 호출"""
                service = await get_service()
                # 카드 데이터를 TarotReadingRequest 형태로 변환
                from yeji_ai.models.fortune.tarot import TarotCardInput, SpreadCardInput
                from yeji_ai.models.enums import CardOrientation, SpreadPosition

                spread_cards = []
                for c in cards:
                    card_data = c["card"]
                    if "major" in card_data:
                        card_input = TarotCardInput(
                            major=card_data["major"],
                            orientation=CardOrientation(card_data["orientation"]),
                        )
                    else:
                        card_input = TarotCardInput(
                            suit=card_data["suit"],
                            rank=card_data["rank"],
                            orientation=CardOrientation(card_data["orientation"]),
                        )
                    spread_cards.append(SpreadCardInput(
                        position=SpreadPosition(c["position"]),
                        card=card_input,
                    ))

                temp_request = TarotReadingRequest(
                    question=request.question,
                    cards=spread_cards,
                )
                response = await service.generate_reading(temp_request)
                return response.model_dump()

            background_tasks.add_task(
                background_expand_tarot_cache,
                request.question.value,
                _generate_tarot_for_cache,
            )
            logger.info("tarot_background_cache_expansion_scheduled", category=request.question.value)

            return FortuneResponse(
                success=True,
                validated=True,
                type="eastern",
                data=random_cached,
            )
        # 캐시 없으면 아래 로직으로 실시간 생성
        logger.info("tarot_no_cache_fallback_to_live", category=request.question.value)

    # 캐시 조회 (force=False일 때만) - 기존 exact-match 캐시
    cards_for_cache = [{"position": c.position, "card": c.card.model_dump()} for c in request.cards]
    if not force:
        cached = await get_tarot_reading_cache(request.question.value, cards_for_cache)
        if cached:
            logger.info("tarot_reading_cache_used", question=request.question.value)
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
            logger.info("tarot_reading_graceful_mode", question=request.question.value)
            try:
                response = await service.generate_reading(request)
                response_data = response.model_dump()
                # 캐시 저장
                await store_tarot_reading_cache(request.question.value, cards_for_cache, response_data)
                return FortuneResponse(
                    success=True,
                    validated=True,
                    type="eastern",  # TODO: type을 "tarot"로 변경 (FortuneTypeLiteral 확장 필요)
                    data=response_data,
                )
            except Exception as e:
                logger.warning(
                    "tarot_reading_validation_error",
                    error=str(e),
                    question=request.question.value,
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
        response = await service.generate_reading(request)

        logger.info(
            "tarot_reading_success",
            question=request.question.value,
            card_count=len(response.cards),
        )

        return response

    except TarotServiceError as e:
        logger.error(
            "tarot_reading_service_error",
            error=str(e),
            error_code=e.error_code,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"타로 서비스 오류: {str(e)}",
        )
    except ValueError as e:
        logger.warning("tarot_reading_validation_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"입력값 오류: {str(e)}",
        )
    except Exception as e:
        logger.error("tarot_reading_error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"타로 리딩 중 오류가 발생했습니다: {str(e)}",
        )


@router.get(
    "/tarot/deck",
    summary="타로 카드 전체 목록",
    description="78장 타로 카드 전체 목록을 반환합니다 (메이저 22장 + 마이너 56장).",
    responses={
        200: {
            "description": "카드 목록 반환",
            "content": {
                "application/json": {
                    "example": {
                        "total": 78,
                        "major_count": 22,
                        "minor_count": 56,
                        "cards": [
                            {
                                "type": "major",
                                "code": "FOOL",
                                "number": 0,
                                "name_ko": "바보",
                                "name_en": "Fool",
                            },
                            {
                                "type": "minor",
                                "code": "CUPS_ACE",
                                "suit": "CUPS",
                                "suit_ko": "컵",
                                "rank": "ACE",
                                "rank_ko": "에이스",
                                "name_ko": "컵 에이스",
                                "name_en": "ACE of CUPS",
                                "element": "WATER",
                                "is_court": False,
                            },
                        ],
                    }
                }
            },
        }
    },
)
async def get_tarot_deck() -> dict[str, Any]:
    """
    타로 카드 전체 목록 조회

    78장의 타로 카드 전체 목록을 반환합니다.
    - 메이저 아르카나: 22장
    - 마이너 아르카나: 56장 (4 suits × 14 ranks)

    프론트엔드에서 카드 선택 UI 구성에 사용할 수 있습니다.
    """
    logger.info("tarot_deck_request")

    try:
        service = await get_service()
        deck = service.get_full_deck()

        major_count = sum(1 for card in deck if card["type"] == "major")
        minor_count = sum(1 for card in deck if card["type"] == "minor")

        logger.info(
            "tarot_deck_success",
            total=len(deck),
            major_count=major_count,
            minor_count=minor_count,
        )

        return {
            "total": len(deck),
            "major_count": major_count,
            "minor_count": minor_count,
            "cards": deck,
        }

    except Exception as e:
        logger.error("tarot_deck_error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"카드 목록 조회 중 오류가 발생했습니다: {str(e)}",
        )
