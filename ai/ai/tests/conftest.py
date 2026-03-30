"""pytest 공통 설정 및 픽스처"""

import pytest
from httpx import ASGITransport, AsyncClient

from yeji_ai.main import app


@pytest.fixture
def anyio_backend():
    """anyio 백엔드 설정"""
    return "asyncio"


@pytest.fixture
async def client():
    """테스트용 AsyncClient"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
