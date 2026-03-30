"""세션 관리 API 테스트

티키타카 API의 세션 관리 기능 테스트
- 세션 생성/조회/삭제
- 디버그 엔드포인트
- Fortune 목록 조회
"""

import pytest

from yeji_ai.services.tikitaka_service import (
    _fortune_store,
    _sessions,
    clear_all_data,
    create_session,
    delete_session,
    get_session,
    list_fortunes,
    list_sessions,
    store_fortune,
)


# ============================================================
# Fixtures
# ============================================================


@pytest.fixture(autouse=True)
def clear_stores():
    """각 테스트 전후로 저장소 초기화"""
    _sessions.clear()
    _fortune_store.clear()
    yield
    _sessions.clear()
    _fortune_store.clear()


# ============================================================
# 세션 생성 테스트
# ============================================================


class TestCreateSession:
    """세션 생성 테스트"""

    def test_create_session_basic(self):
        """기본 세션 생성"""
        session = create_session()

        assert session is not None
        assert session.session_id is not None
        assert len(session.session_id) == 8
        assert session.turn == 0
        assert session.eastern_result is None
        assert session.western_result is None

    def test_create_session_with_birth_info(self):
        """생년월일 포함 세션 생성"""
        session = create_session(
            birth_date="1990-05-15",
            birth_time="14:30",
        )

        assert session.user_info["birth_date"] == "1990-05-15"
        assert session.user_info["birth_time"] == "14:30"

    def test_create_multiple_sessions(self):
        """여러 세션 생성 시 고유 ID"""
        session1 = create_session()
        session2 = create_session()
        session3 = create_session()

        assert session1.session_id != session2.session_id
        assert session2.session_id != session3.session_id
        assert len(_sessions) == 3


# ============================================================
# 세션 조회 테스트
# ============================================================


class TestGetSession:
    """세션 조회 테스트"""

    def test_get_existing_session(self):
        """존재하는 세션 조회"""
        created = create_session(birth_date="1990-05-15")
        retrieved = get_session(created.session_id)

        assert retrieved is not None
        assert retrieved.session_id == created.session_id
        assert retrieved.user_info["birth_date"] == "1990-05-15"

    def test_get_nonexistent_session(self):
        """존재하지 않는 세션 조회"""
        result = get_session("nonexistent_id")
        assert result is None

    def test_get_session_preserves_state(self):
        """세션 상태 유지 확인"""
        session = create_session()
        session.turn = 5
        session.last_topic = "연애운"

        retrieved = get_session(session.session_id)
        assert retrieved.turn == 5
        assert retrieved.last_topic == "연애운"


# ============================================================
# 세션 삭제 테스트
# ============================================================


class TestDeleteSession:
    """세션 삭제 테스트"""

    def test_delete_existing_session(self):
        """존재하는 세션 삭제"""
        session = create_session()
        session_id = session.session_id

        result = delete_session(session_id)

        assert result is True
        assert get_session(session_id) is None
        assert session_id not in _sessions

    def test_delete_nonexistent_session(self):
        """존재하지 않는 세션 삭제"""
        result = delete_session("nonexistent_id")
        assert result is False


# ============================================================
# 세션 목록 조회 테스트
# ============================================================


class TestListSessions:
    """세션 목록 조회 테스트"""

    def test_list_empty_sessions(self):
        """빈 세션 목록"""
        sessions = list_sessions()
        assert sessions == []

    def test_list_multiple_sessions(self):
        """여러 세션 목록"""
        create_session(birth_date="1990-01-01")
        create_session(birth_date="1995-06-15")
        create_session(birth_date="2000-12-25")

        sessions = list_sessions()

        assert len(sessions) == 3
        for s in sessions:
            assert "session_id" in s
            assert "turn" in s
            assert "has_eastern" in s
            assert "has_western" in s
            assert "created_at" in s

    def test_list_sessions_includes_fortune_ids(self):
        """세션 목록에 Fortune ID 포함"""
        session = create_session()
        session.eastern_fortune_id = "east1234"
        session.western_fortune_id = "west5678"

        sessions = list_sessions()

        assert sessions[0]["eastern_fortune_id"] == "east1234"
        assert sessions[0]["western_fortune_id"] == "west5678"


# ============================================================
# Fortune 목록 조회 테스트
# ============================================================


class TestListFortunes:
    """Fortune 목록 조회 테스트"""

    def test_list_empty_fortunes(self):
        """빈 Fortune 목록"""
        fortunes = list_fortunes()
        assert fortunes == []

    def test_list_fortunes_after_store(self):
        """Fortune 저장 후 목록 조회"""
        # Mock 객체 대신 간단한 객체 사용
        class MockEastern:
            pass

        class MockWestern:
            pass

        store_fortune("east1", MockEastern())
        store_fortune("west1", MockWestern())

        fortunes = list_fortunes()

        assert len(fortunes) == 2
        fortune_ids = [f["fortune_id"] for f in fortunes]
        assert "east1" in fortune_ids
        assert "west1" in fortune_ids


# ============================================================
# 데이터 초기화 테스트
# ============================================================


class TestClearAllData:
    """데이터 초기화 테스트"""

    def test_clear_all_data(self):
        """모든 데이터 초기화"""
        # 세션 생성
        create_session()
        create_session()

        # Fortune 저장
        store_fortune("east1", object())
        store_fortune("west1", object())

        # 초기화 전 확인
        assert len(_sessions) == 2
        assert len(_fortune_store) == 2

        # 초기화 실행
        result = clear_all_data()

        # 결과 확인
        assert result["cleared_sessions"] == 2
        assert result["cleared_fortunes"] == 2
        assert len(_sessions) == 0
        assert len(_fortune_store) == 0

    def test_clear_empty_data(self):
        """빈 데이터 초기화"""
        result = clear_all_data()

        assert result["cleared_sessions"] == 0
        assert result["cleared_fortunes"] == 0


# ============================================================
# 통합 시나리오 테스트
# ============================================================


class TestSessionLifecycle:
    """세션 라이프사이클 통합 테스트"""

    def test_full_lifecycle(self):
        """전체 세션 라이프사이클"""
        # 1. 세션 생성
        session = create_session(birth_date="1990-05-15", birth_time="14:30")
        session_id = session.session_id

        # 2. 세션 조회
        retrieved = get_session(session_id)
        assert retrieved is not None
        assert retrieved.user_info["birth_date"] == "1990-05-15"

        # 3. 세션 목록 확인
        sessions = list_sessions()
        assert len(sessions) == 1
        assert sessions[0]["session_id"] == session_id

        # 4. 세션 상태 변경
        session.turn = 3
        session.eastern_fortune_id = "east1234"

        # 5. 변경된 상태 확인
        retrieved2 = get_session(session_id)
        assert retrieved2.turn == 3
        assert retrieved2.eastern_fortune_id == "east1234"

        # 6. 세션 삭제
        delete_session(session_id)
        assert get_session(session_id) is None
        assert len(list_sessions()) == 0

    def test_multiple_sessions_independent(self):
        """여러 세션 독립성 확인"""
        # 세션 생성
        session1 = create_session(birth_date="1990-01-01")
        session2 = create_session(birth_date="2000-12-25")

        # 독립적 상태 변경
        session1.turn = 5
        session2.turn = 10

        # 독립성 확인
        assert get_session(session1.session_id).turn == 5
        assert get_session(session2.session_id).turn == 10

        # 하나만 삭제
        delete_session(session1.session_id)

        # 다른 세션 유지 확인
        assert get_session(session1.session_id) is None
        assert get_session(session2.session_id) is not None
        assert get_session(session2.session_id).turn == 10
