"""복합 메시지 서비스 테스트"""

import pytest

from yeji_ai.services.compound_message_service import (
    CompoundMessageService,
    MessagePool,
    get_compound_message_or_fallback,
)


# ============================================================
# 픽스처
# ============================================================


@pytest.fixture
def service() -> CompoundMessageService:
    """CompoundMessageService 인스턴스"""
    return CompoundMessageService()


@pytest.fixture
def eastern_fortune_data() -> dict:
    """동양 운세 샘플 데이터"""
    return {
        "element": "FIRE",
        "stats": {
            "five_elements": {
                "summary": "화와 목이 강합니다",
                "list": [
                    {"element": "FIRE", "count": 4, "percent": 40.0},
                    {"element": "WOOD", "count": 3, "percent": 30.0},
                    {"element": "WATER", "count": 2, "percent": 20.0},
                    {"element": "EARTH", "count": 1, "percent": 10.0},
                ],
            },
            "ten_gods": {
                "summary": "비겁과 식상이 강합니다",
                "list": [
                    {"code": "BI_GYEON", "count": 3, "percent": 37.5},
                    {"code": "SIK_SIN", "count": 2, "percent": 25.0},
                    {"code": "JEONG_JAE", "count": 1, "percent": 12.5},
                ],
            },
        },
    }


@pytest.fixture
def western_fortune_data() -> dict:
    """서양 운세 샘플 데이터"""
    return {
        "element": "fire",
        "stats": {
            "element_4_distribution": [
                {"code": "FIRE", "percentage": 50.0},
                {"code": "AIR", "percentage": 30.0},
                {"code": "WATER", "percentage": 15.0},
                {"code": "EARTH", "percentage": 5.0},
            ],
            "modality_3_distribution": [
                {"code": "CARDINAL", "percentage": 50.0},
                {"code": "FIXED", "percentage": 33.3},
                {"code": "MUTABLE", "percentage": 16.7},
            ],
        },
    }


# ============================================================
# MessagePool 테스트
# ============================================================


def test_message_pool_singleton() -> None:
    """MessagePool 싱글톤 패턴 테스트"""
    pool1 = MessagePool()
    pool2 = MessagePool()

    assert pool1 is pool2, "MessagePool은 싱글톤이어야 합니다"


def test_message_pool_initialization() -> None:
    """MessagePool 초기화 테스트"""
    pool = MessagePool()

    # 초기화되어야 함
    assert MessagePool._initialized is True

    # 풀 구조 확인
    assert isinstance(pool.eastern_pools, dict)
    assert isinstance(pool.western_pools, dict)


# ============================================================
# extract_top_two_elements 테스트
# ============================================================


def test_extract_top_two_elements_success(service: CompoundMessageService) -> None:
    """상위 2개 요소 추출 성공 케이스"""
    element_list = [
        {"element": "FIRE", "count": 4},
        {"element": "WOOD", "count": 3},
        {"element": "WATER", "count": 2},
    ]

    result = service.extract_top_two_elements(element_list, key="count")

    assert result is not None
    assert len(result) == 2
    # 알파벳순 정렬 확인
    assert result == ("FIRE", "WOOD")


def test_extract_top_two_elements_sorting(service: CompoundMessageService) -> None:
    """상위 2개 요소가 알파벳순으로 정렬되는지 확인"""
    element_list = [
        {"element": "WOOD", "count": 5},  # 1위
        {"element": "FIRE", "count": 4},  # 2위
        {"element": "WATER", "count": 2},
    ]

    result = service.extract_top_two_elements(element_list, key="count")

    assert result is not None
    # 값은 WOOD, FIRE 순이지만 알파벳순으로 정렬되어야 함
    assert result == ("FIRE", "WOOD")


def test_extract_top_two_elements_with_code_key(service: CompoundMessageService) -> None:
    """code 키를 사용하는 요소 추출"""
    element_list = [
        {"code": "BI_GYEON", "percent": 37.5},
        {"code": "SIK_SIN", "percent": 25.0},
        {"code": "JEONG_JAE", "percent": 12.5},
    ]

    result = service.extract_top_two_elements(element_list, key="percent")

    assert result is not None
    assert len(result) == 2
    # 알파벳순 정렬
    assert result == ("BI_GYEON", "SIK_SIN")


def test_extract_top_two_elements_insufficient(service: CompoundMessageService) -> None:
    """요소가 2개 미만인 경우"""
    element_list = [{"element": "FIRE", "count": 4}]

    result = service.extract_top_two_elements(element_list, key="count")

    assert result is None


def test_extract_top_two_elements_empty(service: CompoundMessageService) -> None:
    """빈 리스트"""
    result = service.extract_top_two_elements([], key="count")

    assert result is None


# ============================================================
# generate_compound_key 테스트
# ============================================================


def test_generate_compound_key(service: CompoundMessageService) -> None:
    """복합 키 생성 테스트"""
    key = service.generate_compound_key("FIRE", "WOOD", "love")

    assert key == "FIRE_WOOD_love"


def test_generate_compound_key_sorting(service: CompoundMessageService) -> None:
    """복합 키 생성 시 알파벳순 정렬 확인"""
    key1 = service.generate_compound_key("WOOD", "FIRE", "love")
    key2 = service.generate_compound_key("FIRE", "WOOD", "love")

    # 순서가 달라도 같은 키 생성
    assert key1 == key2
    assert key1 == "FIRE_WOOD_love"


def test_generate_compound_key_case_insensitive(service: CompoundMessageService) -> None:
    """복합 키 생성 시 대소문자 무시"""
    key1 = service.generate_compound_key("fire", "wood", "love")
    key2 = service.generate_compound_key("FIRE", "WOOD", "love")

    assert key1 == key2


# ============================================================
# get_compound_message 테스트 (동양)
# ============================================================


def test_get_compound_message_eastern_five_elements(
    service: CompoundMessageService,
    eastern_fortune_data: dict,
) -> None:
    """동양 오행 복합 메시지 조회"""
    # 메시지를 찾을 수 있으면 문자열, 없으면 None
    result = service.get_compound_message(
        fortune_data=eastern_fortune_data,
        fortune_type="eastern",
        category="love",
        section="five_elements",
    )

    # 메시지 풀에 데이터가 없으면 None
    assert result is None or isinstance(result, str)


def test_get_compound_message_eastern_ten_gods(
    service: CompoundMessageService,
    eastern_fortune_data: dict,
) -> None:
    """동양 십신 복합 메시지 조회"""
    result = service.get_compound_message(
        fortune_data=eastern_fortune_data,
        fortune_type="eastern",
        category="career",
        section="ten_gods",
    )

    assert result is None or isinstance(result, str)


# ============================================================
# get_compound_message 테스트 (서양)
# ============================================================


def test_get_compound_message_western_elements(
    service: CompoundMessageService,
    western_fortune_data: dict,
) -> None:
    """서양 원소 복합 메시지 조회"""
    result = service.get_compound_message(
        fortune_data=western_fortune_data,
        fortune_type="western",
        category="love",
        section="elements",
    )

    assert result is None or isinstance(result, str)


def test_get_compound_message_western_modality(
    service: CompoundMessageService,
    western_fortune_data: dict,
) -> None:
    """서양 모달리티 복합 메시지 조회"""
    result = service.get_compound_message(
        fortune_data=western_fortune_data,
        fortune_type="western",
        category="career",
        section="modality",
    )

    assert result is None or isinstance(result, str)


# ============================================================
# get_fallback_message 테스트
# ============================================================


def test_get_fallback_message_eastern(service: CompoundMessageService) -> None:
    """동양 폴백 메시지"""
    message = service.get_fallback_message("eastern", "love")

    assert isinstance(message, str)
    assert len(message) > 0


def test_get_fallback_message_western(service: CompoundMessageService) -> None:
    """서양 폴백 메시지"""
    message = service.get_fallback_message("western", "career")

    assert isinstance(message, str)
    assert len(message) > 0


def test_get_fallback_message_unknown_category(service: CompoundMessageService) -> None:
    """알 수 없는 카테고리의 폴백 메시지"""
    message = service.get_fallback_message("eastern", "unknown_category")

    assert isinstance(message, str)
    assert len(message) > 0


# ============================================================
# get_compound_message_or_fallback 테스트
# ============================================================


def test_get_compound_message_or_fallback_eastern(eastern_fortune_data: dict) -> None:
    """동양 운세 복합 메시지 또는 폴백"""
    message = get_compound_message_or_fallback(
        fortune_data=eastern_fortune_data,
        fortune_type="eastern",
        category="love",
        section="five_elements",
    )

    # 항상 메시지 반환 (복합 메시지 또는 폴백)
    assert isinstance(message, str)
    assert len(message) > 0


def test_get_compound_message_or_fallback_western(western_fortune_data: dict) -> None:
    """서양 운세 복합 메시지 또는 폴백"""
    message = get_compound_message_or_fallback(
        fortune_data=western_fortune_data,
        fortune_type="western",
        category="career",
        section="elements",
    )

    assert isinstance(message, str)
    assert len(message) > 0


# ============================================================
# 엣지 케이스 테스트
# ============================================================


def test_get_compound_message_missing_stats(service: CompoundMessageService) -> None:
    """stats가 없는 경우"""
    fortune_data = {"element": "FIRE"}

    result = service.get_compound_message(
        fortune_data=fortune_data,
        fortune_type="eastern",
        category="love",
        section="five_elements",
    )

    assert result is None


def test_get_compound_message_empty_element_list(service: CompoundMessageService) -> None:
    """요소 리스트가 비어있는 경우"""
    fortune_data = {
        "stats": {
            "five_elements": {
                "list": [],
            },
        },
    }

    result = service.get_compound_message(
        fortune_data=fortune_data,
        fortune_type="eastern",
        category="love",
        section="five_elements",
    )

    assert result is None


def test_extract_top_two_elements_flexible_keys(service: CompoundMessageService) -> None:
    """다양한 키 이름 지원 테스트"""
    # percentage 키
    element_list1 = [
        {"code": "FIRE", "percentage": 50.0},
        {"code": "AIR", "percentage": 30.0},
    ]
    result1 = service.extract_top_two_elements(element_list1, key="percentage")
    assert result1 == ("AIR", "FIRE")

    # value 키
    element_list2 = [
        {"element": "WOOD", "value": 5},
        {"element": "EARTH", "value": 3},
    ]
    result2 = service.extract_top_two_elements(element_list2, key="value")
    assert result2 == ("EARTH", "WOOD")
