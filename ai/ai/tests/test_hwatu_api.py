"""화투 API 테스트 모듈."""

import pytest
from httpx import ASGITransport, AsyncClient

from yeji_ai.main import app


@pytest.fixture
async def client():
    """비동기 테스트 클라이언트 픽스처."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_hwatu_reading_valid_request(client):
    """정상 요청 테스트 - 4장 카드로 화투 운세 조회."""
    payload = {
        "category": "HWATU",
        "question": "오늘 금전운이 궁금해요",
        "cards": [
            {"position": 1, "card_code": 7, "is_reversed": False},
            {"position": 2, "card_code": 18, "is_reversed": False},
            {"position": 3, "card_code": 32, "is_reversed": False},
            {"position": 4, "card_code": 41, "is_reversed": False},
        ],
    }
    response = await client.post("/v1/fortune/hwatu/reading", json=payload)
    assert response.status_code == 200
    data = response.json()

    # graceful 모드이므로 FortuneResponse 래퍼 확인
    assert data["success"] is True
    assert "data" in data

    # 실제 데이터 구조 확인
    result = data["data"]
    assert "meta" in result
    assert "cards" in result
    assert "summary" in result
    assert "lucky" in result
    assert len(result["cards"]) == 4

    # summary 구조 확인
    summary = result["summary"]
    assert "overall_theme" in summary
    assert "flow_analysis" in summary
    assert "advice" in summary

    # lucky 구조 확인
    lucky = result["lucky"]
    assert "color" in lucky
    assert "number" in lucky
    assert "direction" in lucky


@pytest.mark.asyncio
async def test_hwatu_reading_invalid_position(client):
    """잘못된 position 테스트 - position 5 사용 시 400 에러."""
    payload = {
        "category": "HWATU",
        "question": "테스트 질문",
        "cards": [
            {"position": 5, "card_code": 7, "is_reversed": False},
            {"position": 2, "card_code": 18, "is_reversed": False},
            {"position": 3, "card_code": 32, "is_reversed": False},
            {"position": 4, "card_code": 41, "is_reversed": False},
        ],
    }
    response = await client.post("/v1/fortune/hwatu/reading", json=payload)
    assert response.status_code == 422  # Pydantic 검증 오류


@pytest.mark.asyncio
async def test_hwatu_reading_duplicate_card(client):
    """중복 카드 테스트 - 같은 card_code 2번 사용 시 400 에러."""
    payload = {
        "category": "HWATU",
        "question": "테스트 질문",
        "cards": [
            {"position": 1, "card_code": 7, "is_reversed": False},
            {"position": 2, "card_code": 7, "is_reversed": False},  # 중복
            {"position": 3, "card_code": 32, "is_reversed": False},
            {"position": 4, "card_code": 41, "is_reversed": False},
        ],
    }
    response = await client.post("/v1/fortune/hwatu/reading", json=payload)
    assert response.status_code == 422  # Pydantic 검증 오류


@pytest.mark.asyncio
async def test_hwatu_reading_missing_position(client):
    """position 누락 테스트 - position 1,2,3만 있고 4 누락 시 400 에러."""
    payload = {
        "category": "HWATU",
        "question": "테스트 질문",
        "cards": [
            {"position": 1, "card_code": 7, "is_reversed": False},
            {"position": 2, "card_code": 18, "is_reversed": False},
            {"position": 3, "card_code": 32, "is_reversed": False},
            # position 4 누락
        ],
    }
    response = await client.post("/v1/fortune/hwatu/reading", json=payload)
    assert response.status_code == 422  # Pydantic 검증 오류


@pytest.mark.asyncio
async def test_hwatu_deck(client):
    """카드 목록 조회 테스트 - GET /v1/fortune/hwatu/deck."""
    response = await client.get("/v1/fortune/hwatu/deck")
    assert response.status_code == 200
    data = response.json()

    # 덱 정보 확인
    assert data["total"] == 48
    assert data["months"] == 12
    assert len(data["cards"]) == 48

    # 카드 구조 샘플 확인 (첫 번째 카드)
    first_card = data["cards"][0]
    assert "code" in first_card
    assert "month" in first_card
    assert "name_ko" in first_card
    assert "card_type" in first_card
    assert "fortune_meaning" in first_card
    assert "keywords" in first_card
