"""사주 API 테스트"""

import pytest


@pytest.mark.anyio
async def test_analyze_request_validation(client):
    """분석 요청 유효성 검사 테스트"""
    # 필수 필드 누락
    response = await client.post("/saju/analyze", json={})
    assert response.status_code == 422


@pytest.mark.anyio
async def test_analyze_request_success(client):
    """분석 요청 성공 테스트"""
    request_data = {
        "user_id": 1,
        "saju_profile": {
            "name": "홍길동",
            "gender": "M",
            "birth_date": "1990-01-15",
            "birth_time": "10:30",
        },
        "category": "연애운",
        "sub_category": "올해 연애운",
    }

    response = await client.post("/saju/analyze", json=request_data)

    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert data["status"] == "analyzing"


@pytest.mark.anyio
async def test_stream_without_session(client):
    """세션 없이 스트림 요청 테스트"""
    response = await client.get("/saju/stream/nonexistent-session")

    # 세션이 없으면 404
    assert response.status_code == 404


@pytest.mark.anyio
async def test_chat_without_session(client):
    """세션 없이 채팅 요청 테스트"""
    request_data = {
        "session_id": "nonexistent",
        "message": "테스트 메시지",
    }

    response = await client.post("/saju/chat", json=request_data)

    # 세션이 없으면 404
    assert response.status_code == 404


@pytest.mark.anyio
async def test_result_without_session(client):
    """세션 없이 결과 조회 테스트"""
    response = await client.get("/saju/result/nonexistent-session")

    assert response.status_code == 404
