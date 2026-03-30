"""타로 서비스 테스트"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from yeji_ai.clients.vllm_client import CompletionResponse
from yeji_ai.models.enums import CardOrientation, MajorArcana, SpreadPosition
from yeji_ai.models.fortune.tarot import (
    SpreadCardInput,
    TarotCardInput,
    TarotReadingRequest,
)
from yeji_ai.services.tarot_service import TarotService


@pytest.fixture
def mock_vllm_client() -> AsyncMock:
    """Mock vLLM 클라이언트"""
    client = AsyncMock()

    # LLM 응답 (JSON 형식)
    llm_response = {
        "cards": [
            {
                "position": "PAST",
                "position_label": "과거",
                "card_code": "THE_FOOL",
                "card_name": "바보",
                "orientation": "UPRIGHT",
                "orientation_label": "정방향",
                "keywords": ["새로운 시작", "순수함", "모험"],
                "interpretation": "과거, 순수한 마음으로 새로운 여정을 시작했습니다.",
            },
            {
                "position": "PRESENT",
                "position_label": "현재",
                "card_code": "THE_MAGICIAN",
                "card_name": "마법사",
                "orientation": "UPRIGHT",
                "orientation_label": "정방향",
                "keywords": ["창조", "의지", "능력"],
                "interpretation": "현재, 모든 도구와 능력을 갖추고 있습니다.",
            },
            {
                "position": "FUTURE",
                "position_label": "미래",
                "card_code": "THE_STAR",
                "card_name": "별",
                "orientation": "UPRIGHT",
                "orientation_label": "정방향",
                "keywords": ["희망", "치유", "영감"],
                "interpretation": "미래에는 별빛 같은 희망이 당신을 비춰줄 것입니다.",
            },
        ],
        "summary": {
            "overall_theme": "순수한 시작이 창조의 힘으로 성장하여 희망으로 완성되는 여정",
            "past_to_present": "과거의 순수한 도전 정신이 현재 창조적 능력으로 발현되고 있습니다.",
            "present_to_future": "현재 발휘하는 능력이 미래에 큰 희망으로 꽃필 것입니다.",
            "advice": "가진 능력을 믿고 행동하세요. 꾸준히 나아가면 평화를 얻게 될 것입니다.",
        },
        "lucky": {
            "color": "은빛 하늘색",
            "number": "1, 7, 17",
            "element": "공기와 별빛의 조화",
            "timing": "새벽 별이 빛나는 순간",
        },
    }

    client.chat.return_value = CompletionResponse(
        text=json.dumps(llm_response, ensure_ascii=False),
        finish_reason="stop",
    )

    return client


@pytest.fixture
def sample_request() -> TarotReadingRequest:
    """샘플 타로 리딩 요청"""
    return TarotReadingRequest(
        question="앞으로의 진로는 어떻게 될까요?",
        cards=[
            SpreadCardInput(
                position=SpreadPosition.PAST,
                card=TarotCardInput(
                    major=MajorArcana.FOOL,
                    orientation=CardOrientation.UPRIGHT,
                ),
            ),
            SpreadCardInput(
                position=SpreadPosition.PRESENT,
                card=TarotCardInput(
                    major=MajorArcana.MAGICIAN,
                    orientation=CardOrientation.UPRIGHT,
                ),
            ),
            SpreadCardInput(
                position=SpreadPosition.FUTURE,
                card=TarotCardInput(
                    major=MajorArcana.STAR,
                    orientation=CardOrientation.UPRIGHT,
                ),
            ),
        ],
    )


@pytest.mark.asyncio
async def test_tarot_service_initialization():
    """타로 서비스 초기화 테스트"""
    service = TarotService()
    assert not service._initialized
    assert service._client is None

    await service.initialize()

    assert service._initialized
    assert service._client is not None


@pytest.mark.asyncio
async def test_generate_reading_with_llm(
    mock_vllm_client: AsyncMock,
    sample_request: TarotReadingRequest,
):
    """LLM을 사용한 타로 리딩 생성 테스트"""
    service = TarotService()
    service._client = mock_vllm_client
    service._initialized = True

    # 타로 리딩 생성
    result = await service.generate_reading(sample_request)

    # 기본 검증
    assert result is not None
    assert result.category == "tarot"
    assert result.spread_type == "THREE_CARD"
    assert result.question == sample_request.question

    # 카드 해석 검증
    assert len(result.cards) == 3
    assert result.cards[0].position == SpreadPosition.PAST
    assert result.cards[0].card_name == "바보"
    assert result.cards[0].orientation == CardOrientation.UPRIGHT
    assert len(result.cards[0].keywords) > 0
    assert len(result.cards[0].interpretation) > 0

    # 종합 해석 검증
    assert result.summary is not None
    assert len(result.summary.overall_theme) > 0
    assert len(result.summary.advice) > 0

    # 행운 정보 검증
    assert result.lucky is not None
    assert len(result.lucky.color) > 0
    assert len(result.lucky.element) > 0

    # 배지 검증
    assert len(result.badges) > 0

    # LLM 호출 검증
    mock_vllm_client.chat.assert_called_once()


@pytest.mark.asyncio
async def test_generate_reading_llm_fallback(sample_request: TarotReadingRequest):
    """LLM 실패 시 폴백 테스트"""
    service = TarotService()

    # LLM 클라이언트 없이 실행 (폴백 테스트)
    service._client = AsyncMock()
    service._client.chat.side_effect = Exception("Connection failed")
    service._initialized = True

    result = await service.generate_reading(sample_request)

    # 폴백으로도 정상 응답 반환
    assert result is not None
    assert len(result.cards) == 3
    assert result.summary is not None
    assert result.lucky is not None


@pytest.mark.asyncio
async def test_parse_cards_from_llm(sample_request: TarotReadingRequest):
    """LLM 응답에서 카드 파싱 테스트"""
    service = TarotService()

    llm_response = {
        "cards": [
            {
                "position": "PAST",
                "position_label": "과거",
                "card_code": "THE_FOOL",
                "card_name": "바보",
                "orientation": "UPRIGHT",
                "orientation_label": "정방향",
                "keywords": ["새로운 시작", "순수함"],
                "interpretation": "과거의 해석입니다.",
            },
            {
                "position": "PRESENT",
                "position_label": "현재",
                "card_code": "THE_MAGICIAN",
                "card_name": "마법사",
                "orientation": "UPRIGHT",
                "orientation_label": "정방향",
                "keywords": ["창조", "의지"],
                "interpretation": "현재의 해석입니다.",
            },
            {
                "position": "FUTURE",
                "position_label": "미래",
                "card_code": "THE_STAR",
                "card_name": "별",
                "orientation": "UPRIGHT",
                "orientation_label": "정방향",
                "keywords": ["희망", "치유"],
                "interpretation": "미래의 해석입니다.",
            },
        ]
    }

    cards = service._parse_cards_from_llm(llm_response, sample_request)

    assert len(cards) == 3
    assert cards[0].position == SpreadPosition.PAST
    assert cards[0].card_code == "THE_FOOL"
    assert cards[0].keywords == ["새로운 시작", "순수함"]


@pytest.mark.asyncio
async def test_parse_summary_from_llm():
    """LLM 응답에서 종합 해석 파싱 테스트"""
    service = TarotService()

    llm_response = {
        "summary": {
            "overall_theme": "전체 주제",
            "past_to_present": "과거에서 현재로",
            "present_to_future": "현재에서 미래로",
            "advice": "조언",
        }
    }

    summary = service._parse_summary_from_llm(llm_response)

    assert summary.overall_theme == "전체 주제"
    assert summary.past_to_present == "과거에서 현재로"
    assert summary.present_to_future == "현재에서 미래로"
    assert summary.advice == "조언"


@pytest.mark.asyncio
async def test_parse_lucky_from_llm():
    """LLM 응답에서 행운 정보 파싱 테스트"""
    service = TarotService()

    llm_response = {
        "lucky": {
            "color": "빨강",
            "number": "3, 7",
            "element": "불",
            "timing": "정오",
        }
    }

    lucky = service._parse_lucky_from_llm(llm_response)

    assert lucky.color == "빨강"
    assert lucky.number == "3, 7"
    assert lucky.element == "불"
    assert lucky.timing == "정오"


@pytest.mark.asyncio
async def test_get_full_deck():
    """78장 타로 덱 조회 테스트"""
    service = TarotService()
    deck = service.get_full_deck()

    # 78장 확인 (메이저 22 + 마이너 56)
    assert len(deck) == 78

    # 메이저 아르카나 검증
    major_cards = [c for c in deck if c["type"] == "major"]
    assert len(major_cards) == 22

    # 마이너 아르카나 검증
    minor_cards = [c for c in deck if c["type"] == "minor"]
    assert len(minor_cards) == 56

    # 첫 번째 카드 구조 검증
    first_card = deck[0]
    assert "code" in first_card
    assert "name_ko" in first_card
    assert "type" in first_card
