"""Chat Summary API Contract 테스트

FortuneSummaryResponse 스키마 검증 테스트
- 정상 케이스 3개
- 경계 케이스 2개
- 실패 케이스 2개
"""

import pytest
from pydantic import ValidationError

from yeji_ai.models.fortune.chat import (
    FortuneSummary,
    FortuneSummaryResponse,
    FortuneCategory,
)


# ============================================================
# 테스트 데이터
# ============================================================

def get_valid_eastern_summary() -> dict:
    """유효한 동양 운세 요약 데이터"""
    return {
        "session_id": "abc12345",
        "category": "wealth",
        "fortune_type": "eastern",
        "fortune": {
            "character": "SOISEOL",
            "score": 85,
            "one_line": "목(木) 기운이 강해 재물 운이 상승하는 시기예요",
            "keywords": ["재물운 상승", "투자 적기", "절약 필요"],
            "detail": "일간(甲)을 중심으로 월지(卯)가 같은 기둥이 반복되어 '목(木) 기운'이 강조됩니다. 이번 달은 재물 운이 상승하는 시기로, 새로운 투자나 사업 기회를 적극적으로 검토해 보세요.",
        },
    }


def get_valid_western_summary() -> dict:
    """유효한 서양 운세 요약 데이터"""
    return {
        "session_id": "abc12345",
        "category": "love",
        "fortune_type": "western",
        "fortune": {
            "character": "STELLA",
            "score": 72,
            "one_line": "물(WATER) 원소가 강해 감성적인 연애 시기야",
            "keywords": ["감성적", "직관", "경계 필요"],
            "detail": "물(WATER) 기질이 강하면 감수성과 공감이 장점이지만, 과몰입을 경계하는 게 좋아. 이번 기간은 감정의 파도가 커질 수 있어.",
        },
    }


def get_valid_total_summary() -> dict:
    """유효한 종합 운세 요약 데이터"""
    return {
        "session_id": "def67890",
        "category": "total",
        "fortune_type": "eastern",
        "fortune": {
            "character": "SOISEOL",
            "score": 78,
            "one_line": "비견/식신/정관 성향이 조화를 이루는 시기예요",
            "keywords": ["자기주도", "표현력", "규칙", "균형"],
            "detail": "비견/식신/정관 성향이 함께 나타나 '자기주도+표현+규칙/기준'이 공존합니다. 자기주도성이 강하고, 표현 실행이 잘 되며, 기준을 세우는 힘이 있습니다.",
        },
    }


# ============================================================
# 정상 케이스 (3개)
# ============================================================

class TestValidCases:
    """정상 케이스 테스트"""

    def test_valid_eastern_summary(self):
        """정상: 동양 운세 요약"""
        data = get_valid_eastern_summary()
        response = FortuneSummaryResponse(**data)

        assert response.session_id == "abc12345"
        assert response.category == "wealth"
        assert response.fortune_type == "eastern"
        assert response.fortune.character == "SOISEOL"
        assert response.fortune.score == 85
        assert len(response.fortune.keywords) == 3

    def test_valid_western_summary(self):
        """정상: 서양 운세 요약"""
        data = get_valid_western_summary()
        response = FortuneSummaryResponse(**data)

        assert response.session_id == "abc12345"
        assert response.category == "love"
        assert response.fortune_type == "western"
        assert response.fortune.character == "STELLA"
        assert response.fortune.score == 72

    def test_valid_total_summary(self):
        """정상: 종합 운세 요약"""
        data = get_valid_total_summary()
        response = FortuneSummaryResponse(**data)

        assert response.category == "total"
        assert len(response.fortune.keywords) == 4


# ============================================================
# 경계 케이스 (2개)
# ============================================================

class TestBoundaryCases:
    """경계 케이스 테스트"""

    def test_boundary_min_keywords(self):
        """경계: 최소 키워드 개수 (2개)"""
        data = get_valid_eastern_summary()
        data["fortune"]["keywords"] = ["키워드1", "키워드2"]  # 정확히 2개

        response = FortuneSummaryResponse(**data)
        assert len(response.fortune.keywords) == 2

    def test_boundary_max_keywords(self):
        """경계: 최대 키워드 개수 (5개)"""
        data = get_valid_eastern_summary()
        data["fortune"]["keywords"] = ["키워드1", "키워드2", "키워드3", "키워드4", "키워드5"]

        response = FortuneSummaryResponse(**data)
        assert len(response.fortune.keywords) == 5

    def test_boundary_score_zero(self):
        """경계: 점수 0점"""
        data = get_valid_eastern_summary()
        data["fortune"]["score"] = 0

        response = FortuneSummaryResponse(**data)
        assert response.fortune.score == 0

    def test_boundary_score_hundred(self):
        """경계: 점수 100점"""
        data = get_valid_eastern_summary()
        data["fortune"]["score"] = 100

        response = FortuneSummaryResponse(**data)
        assert response.fortune.score == 100

    def test_boundary_min_one_line_length(self):
        """경계: 최소 one_line 길이 (10자)"""
        data = get_valid_eastern_summary()
        data["fortune"]["one_line"] = "1234567890"  # 정확히 10자

        response = FortuneSummaryResponse(**data)
        assert len(response.fortune.one_line) == 10

    def test_boundary_min_detail_length(self):
        """경계: 최소 detail 길이 (50자)"""
        data = get_valid_eastern_summary()
        data["fortune"]["detail"] = "가" * 50  # 정확히 50자

        response = FortuneSummaryResponse(**data)
        assert len(response.fortune.detail) == 50


# ============================================================
# 실패 케이스 (2개+)
# ============================================================

class TestFailureCases:
    """실패 케이스 테스트"""

    def test_fail_missing_fortune_type(self):
        """실패: fortune_type 누락"""
        data = get_valid_eastern_summary()
        del data["fortune_type"]

        with pytest.raises(ValidationError) as exc_info:
            FortuneSummaryResponse(**data)

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("fortune_type",) for e in errors)

    def test_fail_invalid_fortune_type(self):
        """실패: 잘못된 fortune_type 값"""
        data = get_valid_eastern_summary()
        data["fortune_type"] = "northern"  # 유효하지 않음

        with pytest.raises(ValidationError) as exc_info:
            FortuneSummaryResponse(**data)

        errors = exc_info.value.errors()
        assert any("fortune_type" in str(e["loc"]) for e in errors)

    def test_fail_invalid_character(self):
        """실패: 잘못된 character 값"""
        data = get_valid_eastern_summary()
        data["fortune"]["character"] = "UNKNOWN"

        with pytest.raises(ValidationError) as exc_info:
            FortuneSummaryResponse(**data)

        errors = exc_info.value.errors()
        assert len(errors) > 0

    def test_fail_score_out_of_range(self):
        """실패: 점수 범위 초과"""
        data = get_valid_eastern_summary()
        data["fortune"]["score"] = 150  # 100 초과

        with pytest.raises(ValidationError) as exc_info:
            FortuneSummaryResponse(**data)

        errors = exc_info.value.errors()
        assert any("score" in str(e["loc"]) for e in errors)

    def test_fail_too_few_keywords(self):
        """실패: 키워드 개수 부족 (1개)"""
        data = get_valid_eastern_summary()
        data["fortune"]["keywords"] = ["단일키워드"]  # 2개 미만

        with pytest.raises(ValidationError) as exc_info:
            FortuneSummaryResponse(**data)

        errors = exc_info.value.errors()
        assert len(errors) > 0

    def test_fail_too_many_keywords(self):
        """실패: 키워드 개수 초과 (6개)"""
        data = get_valid_eastern_summary()
        data["fortune"]["keywords"] = ["k1", "k2", "k3", "k4", "k5", "k6"]  # 5개 초과

        with pytest.raises(ValidationError) as exc_info:
            FortuneSummaryResponse(**data)

        errors = exc_info.value.errors()
        assert len(errors) > 0

    def test_fail_empty_one_line(self):
        """실패: 빈 one_line"""
        data = get_valid_eastern_summary()
        data["fortune"]["one_line"] = ""

        with pytest.raises(ValidationError) as exc_info:
            FortuneSummaryResponse(**data)

        errors = exc_info.value.errors()
        assert len(errors) > 0

    def test_fail_short_detail(self):
        """실패: detail 길이 부족 (50자 미만)"""
        data = get_valid_eastern_summary()
        data["fortune"]["detail"] = "짧은 내용"  # 50자 미만

        with pytest.raises(ValidationError) as exc_info:
            FortuneSummaryResponse(**data)

        errors = exc_info.value.errors()
        assert len(errors) > 0

    def test_fail_invalid_category(self):
        """실패: 잘못된 category 값"""
        data = get_valid_eastern_summary()
        data["category"] = "invalid_category"

        with pytest.raises(ValidationError) as exc_info:
            FortuneSummaryResponse(**data)

        errors = exc_info.value.errors()
        assert any("category" in str(e["loc"]) for e in errors)


# ============================================================
# 직렬화 테스트
# ============================================================

class TestSerialization:
    """직렬화/역직렬화 테스트"""

    def test_model_dump(self):
        """모델 → dict 변환"""
        data = get_valid_eastern_summary()
        response = FortuneSummaryResponse(**data)

        dumped = response.model_dump()

        assert dumped["session_id"] == "abc12345"
        assert dumped["fortune"]["character"] == "SOISEOL"

    def test_model_dump_json(self):
        """모델 → JSON 문자열 변환"""
        data = get_valid_eastern_summary()
        response = FortuneSummaryResponse(**data)

        json_str = response.model_dump_json()

        assert "abc12345" in json_str
        assert "SOISEOL" in json_str
        assert "eastern" in json_str
