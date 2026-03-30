"""헬스체크 API 테스트"""

import pytest


@pytest.mark.anyio
async def test_health_check(client):
    """헬스체크 엔드포인트 테스트"""
    response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "yeji-ai"


@pytest.mark.anyio
async def test_readiness_check(client):
    """준비 상태 체크 테스트"""
    response = await client.get("/health/ready")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["ready", "degraded"]


@pytest.mark.anyio
async def test_liveness_check(client):
    """생존 상태 체크 테스트"""
    response = await client.get("/health/live")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"
