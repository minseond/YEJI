"""Fortune Summary API 통합 테스트

Fortune API (eastern/western)와 Summary API의 통합 테스트.
실제 서버에 요청을 보내 fortune_key 생성 및 Summary 조회를 검증합니다.
"""

import os

import pytest
from httpx import AsyncClient


# 서버 URL (환경변수 또는 기본값)
BASE_URL = os.getenv("TEST_API_URL", "http://localhost:8000")


@pytest.fixture
async def api_client():
    """실제 API 서버용 AsyncClient"""
    async with AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        yield client


class TestEasternFortuneAPI:
    """동양 사주 API 테스트"""

    @pytest.mark.anyio
    async def test_eastern_fortune_returns_fortune_key(self, api_client):
        """동양 사주 API가 fortune_key를 반환하는지 확인"""
        request_data = {
            "birth_date": "1990-05-15",
            "birth_time": "14:30",
            "gender": "M",
            "name": "홍길동",
        }

        response = await api_client.post("/v1/fortune/eastern", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # fortune_key 존재 확인
        assert "fortune_key" in data, "응답에 fortune_key가 없습니다"

        # fortune_key 형식 검증: eastern:{birth_date}:{birth_time}:{gender}
        fortune_key = data["fortune_key"]
        assert fortune_key.startswith("eastern:"), "fortune_key가 'eastern:'으로 시작하지 않습니다"
        assert "1990-05-15" in fortune_key, "fortune_key에 birth_date가 포함되지 않았습니다"
        assert "14:30" in fortune_key, "fortune_key에 birth_time이 포함되지 않았습니다"
        assert "M" in fortune_key, "fortune_key에 gender가 포함되지 않았습니다"

    @pytest.mark.anyio
    async def test_eastern_fortune_without_birth_time(self, api_client):
        """출생시간 없이 동양 사주 API 호출 시 fortune_key 형식 확인"""
        request_data = {
            "birth_date": "1985-03-20",
            "gender": "F",
            "name": "김영희",
        }

        response = await api_client.post("/v1/fortune/eastern", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # fortune_key에 "unknown" 포함 확인
        fortune_key = data["fortune_key"]
        assert "unknown" in fortune_key, "출생시간 없을 때 fortune_key에 'unknown'이 포함되지 않았습니다"


class TestWesternFortuneAPI:
    """서양 점성술 API 테스트"""

    @pytest.mark.anyio
    async def test_western_fortune_returns_fortune_key(self, api_client):
        """서양 점성술 API가 fortune_key를 반환하는지 확인"""
        request_data = {
            "birth_date": "1992-08-10",
            "birth_time": "09:15",
            "gender": "F",
            "name": "이지은",
        }

        response = await api_client.post("/v1/fortune/western", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # fortune_key 존재 확인
        assert "fortune_key" in data, "응답에 fortune_key가 없습니다"

        # fortune_key 형식 검증: western:{birth_date}:{birth_time}
        fortune_key = data["fortune_key"]
        assert fortune_key.startswith("western:"), "fortune_key가 'western:'으로 시작하지 않습니다"
        assert "1992-08-10" in fortune_key, "fortune_key에 birth_date가 포함되지 않았습니다"
        assert "09:15" in fortune_key, "fortune_key에 birth_time이 포함되지 않았습니다"

    @pytest.mark.anyio
    async def test_western_fortune_without_birth_time(self, api_client):
        """출생시간 없이 서양 점성술 API 호출 시 fortune_key 형식 확인"""
        request_data = {
            "birth_date": "1995-12-25",
            "gender": "M",
            "name": "박민수",
        }

        response = await api_client.post("/v1/fortune/western", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # fortune_key에 "unknown" 포함 확인
        fortune_key = data["fortune_key"]
        assert "unknown" in fortune_key, "출생시간 없을 때 fortune_key에 'unknown'이 포함되지 않았습니다"


class TestEasternSummaryAPI:
    """동양 사주 Summary API 테스트"""

    @pytest.mark.anyio
    async def test_eastern_summary_with_valid_key(self, api_client):
        """유효한 fortune_key로 동양 사주 요약 조회"""
        # 1단계: 동양 사주 생성
        eastern_request = {
            "birth_date": "1988-11-03",
            "birth_time": "18:00",
            "gender": "M",
            "name": "최태민",
        }
        eastern_response = await api_client.post("/v1/fortune/eastern", json=eastern_request)
        assert eastern_response.status_code == 200
        fortune_key = eastern_response.json()["fortune_key"]

        # 2단계: Summary 조회
        summary_request = {"fortune_key": fortune_key}
        summary_response = await api_client.post("/v1/fortune/eastern/summary", json=summary_request)

        assert summary_response.status_code == 200
        data = summary_response.json()

        # 응답 필드 검증
        assert "fortune_key" in data
        assert "summary" in data
        assert "source" in data
        assert data["source"] in ["cached", "generated"]
        assert len(data["summary"]) > 0, "요약 텍스트가 비어있습니다"

    @pytest.mark.anyio
    async def test_eastern_summary_with_western_key(self, api_client):
        """잘못된 fortune_key (western 형식) 사용 시 400 에러"""
        # western 형식의 키 생성
        western_request = {
            "birth_date": "1990-01-01",
            "birth_time": "12:00",
            "gender": "F",
            "name": "테스트",
        }
        western_response = await api_client.post("/v1/fortune/western", json=western_request)
        western_key = western_response.json()["fortune_key"]

        # eastern summary API에 western key 전달
        summary_request = {"fortune_key": western_key}
        summary_response = await api_client.post("/v1/fortune/eastern/summary", json=summary_request)

        assert summary_response.status_code == 400
        assert "잘못된 fortune_key 형식" in summary_response.json()["detail"]

    @pytest.mark.anyio
    async def test_eastern_summary_with_nonexistent_key(self, api_client):
        """존재하지 않는 fortune_key 사용 시 404 에러"""
        summary_request = {"fortune_key": "eastern:9999-99-99:99:99:M"}
        summary_response = await api_client.post("/v1/fortune/eastern/summary", json=summary_request)

        assert summary_response.status_code == 404
        assert "찾을 수 없습니다" in summary_response.json()["detail"]


class TestWesternSummaryAPI:
    """서양 점성술 Summary API 테스트"""

    @pytest.mark.anyio
    async def test_western_summary_with_valid_key(self, api_client):
        """유효한 fortune_key로 서양 점성술 요약 조회"""
        # 1단계: 서양 점성술 생성
        western_request = {
            "birth_date": "1993-07-22",
            "birth_time": "06:30",
            "gender": "F",
            "name": "정수연",
        }
        western_response = await api_client.post("/v1/fortune/western", json=western_request)
        assert western_response.status_code == 200
        fortune_key = western_response.json()["fortune_key"]

        # 2단계: Summary 조회
        summary_request = {"fortune_key": fortune_key}
        summary_response = await api_client.post("/v1/fortune/western/summary", json=summary_request)

        assert summary_response.status_code == 200
        data = summary_response.json()

        # 응답 필드 검증
        assert "fortune_key" in data
        assert "summary" in data
        assert "source" in data
        assert data["source"] in ["cached", "generated"]
        assert len(data["summary"]) > 0, "요약 텍스트가 비어있습니다"

    @pytest.mark.anyio
    async def test_western_summary_with_eastern_key(self, api_client):
        """잘못된 fortune_key (eastern 형식) 사용 시 400 에러"""
        # eastern 형식의 키 생성
        eastern_request = {
            "birth_date": "1991-04-05",
            "birth_time": "20:00",
            "gender": "M",
            "name": "테스트",
        }
        eastern_response = await api_client.post("/v1/fortune/eastern", json=eastern_request)
        eastern_key = eastern_response.json()["fortune_key"]

        # western summary API에 eastern key 전달
        summary_request = {"fortune_key": eastern_key}
        summary_response = await api_client.post("/v1/fortune/western/summary", json=summary_request)

        assert summary_response.status_code == 400
        assert "잘못된 fortune_key 형식" in summary_response.json()["detail"]

    @pytest.mark.anyio
    async def test_western_summary_with_nonexistent_key(self, api_client):
        """존재하지 않는 fortune_key 사용 시 404 에러"""
        summary_request = {"fortune_key": "western:8888-88-88:88:88"}
        summary_response = await api_client.post("/v1/fortune/western/summary", json=summary_request)

        assert summary_response.status_code == 404
        assert "찾을 수 없습니다" in summary_response.json()["detail"]


class TestSummaryCaching:
    """요약 캐싱 동작 테스트"""

    @pytest.mark.anyio
    async def test_summary_cached_on_second_call(self, api_client):
        """동일한 fortune_key로 두 번 요청 시 캐싱 확인"""
        # 1단계: Fortune 생성
        eastern_request = {
            "birth_date": "1987-02-14",
            "birth_time": "15:45",
            "gender": "F",
            "name": "윤서희",
        }
        eastern_response = await api_client.post("/v1/fortune/eastern", json=eastern_request)
        fortune_key = eastern_response.json()["fortune_key"]

        # 2단계: 첫 번째 Summary 조회 (생성)
        summary_request = {"fortune_key": fortune_key}
        first_response = await api_client.post("/v1/fortune/eastern/summary", json=summary_request)
        first_data = first_response.json()

        # 3단계: 두 번째 Summary 조회 (캐시됨)
        second_response = await api_client.post("/v1/fortune/eastern/summary", json=summary_request)
        second_data = second_response.json()

        # 두 응답 모두 성공
        assert first_response.status_code == 200
        assert second_response.status_code == 200

        # 요약 내용 동일
        assert first_data["summary"] == second_data["summary"]

        # 두 번째는 캐시됨
        assert second_data["source"] == "cached", "두 번째 요청이 캐시에서 반환되지 않았습니다"
        assert second_data["cached_at"] is not None, "캐시 시간이 없습니다"
