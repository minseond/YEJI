"""빈 괄호 및 한자 누락 필터 테스트

bracket_fixer 모듈의 기능을 검증하는 테스트 케이스입니다.

테스트 시나리오:
- 천간 빈 괄호 한자 자동완성 (갑~계)
- 지지 빈 괄호 한자 자동완성 (자~해)
- 오행 빈 괄호 한자 자동완성 (목화토금수)
- 단독 빈 괄호 제거
- 딕셔너리 재귀 처리
- 엣지 케이스
"""

import pytest

from yeji_ai.services.postprocessor.bracket_fixer import (
    ALL_HANGUL_TO_HANJA,
    CHEONGAN_MAPPING,
    ELEMENT_MAPPING,
    JIJI_MAPPING,
    BracketFixer,
    fix_brackets,
    fix_brackets_in_dict,
    get_hanja_for_hangul,
)


# ============================================================
# 매핑 테이블 테스트
# ============================================================


class TestMappingTables:
    """매핑 테이블 검증"""

    def test_천간_매핑_10개(self) -> None:
        """천간 매핑 테이블이 10개인지 확인"""
        assert len(CHEONGAN_MAPPING) == 10

    def test_지지_매핑_12개(self) -> None:
        """지지 매핑 테이블이 12개인지 확인"""
        assert len(JIJI_MAPPING) == 12

    def test_오행_매핑_5개(self) -> None:
        """오행 매핑 테이블이 5개인지 확인"""
        assert len(ELEMENT_MAPPING) == 5

    def test_천간_한자_정확성(self) -> None:
        """천간 한글-한자 매핑 정확성 검증"""
        expected = {
            "갑": "甲", "을": "乙", "병": "丙", "정": "丁", "무": "戊",
            "기": "己", "경": "庚", "신": "辛", "임": "壬", "계": "癸",
        }
        assert CHEONGAN_MAPPING == expected

    def test_지지_한자_정확성(self) -> None:
        """지지 한글-한자 매핑 정확성 검증"""
        expected = {
            "자": "子", "축": "丑", "인": "寅", "묘": "卯",
            "진": "辰", "사": "巳", "오": "午", "미": "未",
            "신": "申", "유": "酉", "술": "戌", "해": "亥",
        }
        assert JIJI_MAPPING == expected

    def test_오행_한자_정확성(self) -> None:
        """오행 한글-한자 매핑 정확성 검증"""
        expected = {
            "목": "木", "화": "火", "토": "土", "금": "金", "수": "水",
        }
        assert ELEMENT_MAPPING == expected


# ============================================================
# BracketFixer 클래스 테스트
# ============================================================


class TestBracketFixer:
    """BracketFixer 클래스 테스트"""

    # ------------------------------------------------------------
    # 천간 빈 괄호 한자 자동완성
    # ------------------------------------------------------------

    def test_천간_갑_빈괄호_한자완성(self) -> None:
        """갑() -> 갑(甲)"""
        fixer = BracketFixer()
        result, count = fixer.fix("갑()")
        assert result == "갑(甲)"
        assert count == 1

    def test_천간_을_빈괄호_한자완성(self) -> None:
        """을() -> 을(乙)"""
        fixer = BracketFixer()
        result, count = fixer.fix("을()")
        assert result == "을(乙)"
        assert count == 1

    def test_천간_10개_전체_자동완성(self) -> None:
        """천간 10개 전체 빈 괄호 자동완성"""
        fixer = BracketFixer()
        cheongan_list = ["갑", "을", "병", "정", "무", "기", "경", "신", "임", "계"]
        hanja_list = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]

        for hangul, hanja in zip(cheongan_list, hanja_list):
            result, count = fixer.fix(f"{hangul}()")
            assert result == f"{hangul}({hanja})", f"{hangul}() -> {hangul}({hanja})"
            assert count == 1

    def test_천간_복수개_빈괄호_처리(self) -> None:
        """여러 천간 빈 괄호 동시 처리"""
        fixer = BracketFixer()
        result, count = fixer.fix("갑() 을() 병()")
        assert result == "갑(甲) 을(乙) 병(丙)"
        assert count == 3

    # ------------------------------------------------------------
    # 지지 빈 괄호 한자 자동완성
    # ------------------------------------------------------------

    def test_지지_자_빈괄호_한자완성(self) -> None:
        """자() -> 자(子)"""
        fixer = BracketFixer()
        result, count = fixer.fix("자()")
        assert result == "자(子)"
        assert count == 1

    def test_지지_12개_전체_자동완성(self) -> None:
        """지지 12개 전체 빈 괄호 자동완성

        주의: '신'은 천간(辛)과 지지(申) 모두 존재하며, 천간 우선으로 설정됨
        따라서 '신'은 이 테스트에서 제외하고 별도 테스트로 처리
        """
        fixer = BracketFixer()
        # '신'은 천간과 중복되므로 제외
        jiji_list = ["자", "축", "인", "묘", "진", "사", "오", "미", "유", "술", "해"]
        hanja_list = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "酉", "戌", "亥"]

        for hangul, hanja in zip(jiji_list, hanja_list):
            result, count = fixer.fix(f"{hangul}()")
            assert result == f"{hangul}({hanja})", f"{hangul}() -> {hangul}({hanja})"
            assert count == 1

    def test_지지_복수개_빈괄호_처리(self) -> None:
        """여러 지지 빈 괄호 동시 처리"""
        fixer = BracketFixer()
        result, count = fixer.fix("자() 축() 인()")
        assert result == "자(子) 축(丑) 인(寅)"
        assert count == 3

    # ------------------------------------------------------------
    # 오행 빈 괄호 한자 자동완성
    # ------------------------------------------------------------

    def test_오행_목_빈괄호_한자완성(self) -> None:
        """목() -> 목(木)"""
        fixer = BracketFixer()
        result, count = fixer.fix("목()")
        assert result == "목(木)"
        assert count == 1

    def test_오행_5개_전체_자동완성(self) -> None:
        """오행 5개 전체 빈 괄호 자동완성"""
        fixer = BracketFixer()
        element_pairs = [("목", "木"), ("화", "火"), ("토", "土"), ("금", "金"), ("수", "水")]

        for hangul, hanja in element_pairs:
            result, count = fixer.fix(f"{hangul}()")
            assert result == f"{hangul}({hanja})", f"{hangul}() -> {hangul}({hanja})"
            assert count == 1

    def test_오행_비활성화_옵션(self) -> None:
        """오행 자동완성 비활성화 시 빈 괄호만 제거"""
        fixer = BracketFixer(include_elements=False)
        result, count = fixer.fix("목()")
        assert result == "목"  # 매핑에 없으므로 빈 괄호만 제거
        assert count == 1

    # ------------------------------------------------------------
    # 단독 빈 괄호 제거
    # ------------------------------------------------------------

    def test_단독_빈괄호_제거(self) -> None:
        """앞에 한글 없는 빈 괄호 제거"""
        fixer = BracketFixer()
        result, count = fixer.fix("오늘 운세가 () 좋습니다.")
        assert result == "오늘 운세가 좋습니다."
        assert count >= 1

    def test_문장_중간_단독_빈괄호_제거(self) -> None:
        """문장 중간의 단독 빈 괄호 제거"""
        fixer = BracketFixer()
        result, count = fixer.fix("재물운 () 상승")
        assert result == "재물운 상승"
        assert count >= 1

    def test_연속_빈괄호_제거(self) -> None:
        """연속된 빈 괄호 제거"""
        fixer = BracketFixer()
        result, count = fixer.fix("테스트 () () 문장")
        assert "()" not in result
        assert count >= 2

    # ------------------------------------------------------------
    # 복합 케이스
    # ------------------------------------------------------------

    def test_천간지지_혼합_빈괄호(self) -> None:
        """천간과 지지가 혼합된 빈 괄호 처리"""
        fixer = BracketFixer()
        result, count = fixer.fix("연주: 갑() 자()")
        assert result == "연주: 갑(甲) 자(子)"
        assert count == 2

    def test_일부만_빈괄호인_경우(self) -> None:
        """일부만 빈 괄호이고 일부는 이미 한자가 있는 경우"""
        fixer = BracketFixer()
        result, count = fixer.fix("갑(甲) 을()")
        assert result == "갑(甲) 을(乙)"
        assert count == 1

    def test_사주_전체_표현_처리(self) -> None:
        """사주 전체 표현 (년월일시) 빈 괄호 처리"""
        fixer = BracketFixer()
        text = "연주 갑()자() 월주 을()축() 일주 병()인() 시주 정()묘()"
        result, count = fixer.fix(text)
        expected = "연주 갑(甲)자(子) 월주 을(乙)축(丑) 일주 병(丙)인(寅) 시주 정(丁)묘(卯)"
        assert result == expected
        assert count == 8

    def test_괄호_안에_공백있는_경우(self) -> None:
        """괄호 안에 공백이 있는 경우도 처리"""
        fixer = BracketFixer()
        result, count = fixer.fix("갑( )")
        assert result == "갑(甲)"
        assert count == 1

    def test_한글과_괄호_사이_공백(self) -> None:
        """한글과 괄호 사이에 공백이 있는 경우"""
        fixer = BracketFixer()
        result, count = fixer.fix("갑 ()")
        assert result == "갑(甲)"
        assert count == 1

    # ------------------------------------------------------------
    # 이미 완성된 경우 (수정 없음)
    # ------------------------------------------------------------

    def test_이미_한자_있으면_수정안함(self) -> None:
        """이미 한자가 있으면 수정하지 않음"""
        fixer = BracketFixer()
        result, count = fixer.fix("갑(甲) 을(乙) 병(丙)")
        assert result == "갑(甲) 을(乙) 병(丙)"
        assert count == 0

    def test_빈괄호_없으면_수정안함(self) -> None:
        """빈 괄호가 없으면 수정하지 않음"""
        fixer = BracketFixer()
        result, count = fixer.fix("오늘 운세가 좋습니다.")
        assert result == "오늘 운세가 좋습니다."
        assert count == 0

    # ------------------------------------------------------------
    # 엣지 케이스
    # ------------------------------------------------------------

    def test_빈_문자열_처리(self) -> None:
        """빈 문자열 입력"""
        fixer = BracketFixer()
        result, count = fixer.fix("")
        assert result == ""
        assert count == 0

    def test_None_유사_처리(self) -> None:
        """빈 문자열 입력 (None 대신)"""
        fixer = BracketFixer()
        result, count = fixer.fix("")
        assert result == ""
        assert count == 0

    def test_매핑에_없는_한글_빈괄호(self) -> None:
        """매핑에 없는 한글 뒤 빈 괄호는 제거만 함"""
        fixer = BracketFixer()
        result, count = fixer.fix("좋()")  # '좋'은 매핑에 없음
        assert result == "좋"
        assert count == 1

    def test_신_중의성_처리(self) -> None:
        """'신'은 천간과 지지 모두 있음 - 천간 우선 (매핑 순서)"""
        # '신'은 천간에서 '辛', 지지에서 '申'
        # HANGUL_TO_HANJA에서 먼저 CHEONGAN이 들어가므로 '辛'이 됨
        fixer = BracketFixer()
        result, count = fixer.fix("신()")
        # 천간이 먼저이므로 辛이 됨
        assert result == "신(辛)"
        assert count == 1


# ============================================================
# 딕셔너리 처리 테스트
# ============================================================


class TestBracketFixerDict:
    """딕셔너리 처리 테스트"""

    def test_단순_딕셔너리_처리(self) -> None:
        """단순 딕셔너리 내 문자열 처리"""
        fixer = BracketFixer()
        data = {"text": "갑() 을()"}
        result, count = fixer.fix_dict(data)
        assert result["text"] == "갑(甲) 을(乙)"
        assert count == 2

    def test_중첩_딕셔너리_재귀처리(self) -> None:
        """중첩 딕셔너리 재귀 처리"""
        fixer = BracketFixer()
        data = {
            "outer": {
                "inner": "자() 축()"
            }
        }
        result, count = fixer.fix_dict(data)
        assert result["outer"]["inner"] == "자(子) 축(丑)"
        assert count == 2

    def test_리스트_포함_딕셔너리_처리(self) -> None:
        """리스트가 포함된 딕셔너리 처리"""
        fixer = BracketFixer()
        data = {
            "items": ["갑()", "을()", "병()"]
        }
        result, count = fixer.fix_dict(data)
        assert result["items"] == ["갑(甲)", "을(乙)", "병(丙)"]
        assert count == 3

    def test_복합_구조_딕셔너리_처리(self) -> None:
        """복합 구조 딕셔너리 처리"""
        fixer = BracketFixer()
        data = {
            "chart": {
                "year": {"gan": "갑()"},
                "month": {"gan": "을()"},
            },
            "elements": ["목()", "화()"],
            "summary": "연주 갑()자()",
        }
        result, count = fixer.fix_dict(data)
        assert result["chart"]["year"]["gan"] == "갑(甲)"
        assert result["chart"]["month"]["gan"] == "을(乙)"
        assert result["elements"] == ["목(木)", "화(火)"]
        assert result["summary"] == "연주 갑(甲)자(子)"
        assert count == 6

    def test_재귀_비활성화(self) -> None:
        """재귀 처리 비활성화"""
        fixer = BracketFixer()
        data = {
            "outer": {"inner": "갑()"}
        }
        result, count = fixer.fix_dict(data, recursive=False)
        # 재귀 비활성화하면 중첩 딕셔너리는 처리 안함
        assert result["outer"]["inner"] == "갑()"
        assert count == 0


# ============================================================
# 편의 함수 테스트
# ============================================================


class TestConvenienceFunctions:
    """편의 함수 테스트"""

    def test_fix_brackets_함수(self) -> None:
        """fix_brackets 편의 함수"""
        result = fix_brackets("갑() 을()")
        assert result == "갑(甲) 을(乙)"

    def test_fix_brackets_in_dict_함수(self) -> None:
        """fix_brackets_in_dict 편의 함수"""
        data = {"text": "자() 축()"}
        result = fix_brackets_in_dict(data)
        assert result["text"] == "자(子) 축(丑)"

    def test_get_hanja_for_hangul_천간(self) -> None:
        """get_hanja_for_hangul - 천간"""
        assert get_hanja_for_hangul("갑") == "甲"
        assert get_hanja_for_hangul("계") == "癸"

    def test_get_hanja_for_hangul_지지(self) -> None:
        """get_hanja_for_hangul - 지지"""
        assert get_hanja_for_hangul("자") == "子"
        assert get_hanja_for_hangul("해") == "亥"

    def test_get_hanja_for_hangul_오행(self) -> None:
        """get_hanja_for_hangul - 오행"""
        assert get_hanja_for_hangul("목") == "木"
        assert get_hanja_for_hangul("수") == "水"

    def test_get_hanja_for_hangul_없는값(self) -> None:
        """get_hanja_for_hangul - 매핑에 없는 값"""
        assert get_hanja_for_hangul("좋") is None
        assert get_hanja_for_hangul("abc") is None


# ============================================================
# 성능 테스트
# ============================================================


class TestPerformance:
    """성능 테스트"""

    def test_대용량_텍스트_처리_1000자(self) -> None:
        """1000자 이상 텍스트 처리 성능"""
        fixer = BracketFixer()
        # 천간지지 반복 텍스트 생성
        text = "갑() 을() 병() 정() 무() " * 200  # 약 1000자

        import time
        start = time.time()
        result, count = fixer.fix(text)
        elapsed = (time.time() - start) * 1000  # ms

        assert count == 1000
        assert elapsed < 100  # 100ms 이내

    def test_대용량_딕셔너리_처리(self) -> None:
        """대용량 딕셔너리 처리 성능"""
        fixer = BracketFixer()
        data = {f"key_{i}": f"갑() 을() {i}" for i in range(100)}

        import time
        start = time.time()
        result, count = fixer.fix_dict(data)
        elapsed = (time.time() - start) * 1000  # ms

        assert count == 200  # 100개 키 * 2개 빈괄호
        assert elapsed < 200  # 200ms 이내


# ============================================================
# 실제 LLM 출력 시나리오 테스트
# ============================================================


class TestRealScenarios:
    """실제 LLM 출력 시나리오 테스트"""

    def test_운세_결과_빈괄호_처리(self) -> None:
        """운세 결과 텍스트 빈 괄호 처리"""
        fixer = BracketFixer()
        text = """
        연주: 갑()자()
        월주: 을()축()
        일주: 병()인()
        시주: 정()묘()

        일간 병()화가 강하여 열정적인 성격입니다.
        """
        result, count = fixer.fix(text)

        assert "갑(甲)" in result
        assert "자(子)" in result
        assert "병(丙)" in result
        assert "()" not in result
        assert count == 9  # 8개 사주 + 1개 일간

    def test_오행_분석_빈괄호_처리(self) -> None:
        """오행 분석 텍스트 빈 괄호 처리"""
        fixer = BracketFixer()
        text = "목()이 30%, 화()가 25%, 토()가 20%, 금()이 15%, 수()가 10%입니다."
        result, count = fixer.fix(text)

        assert "목(木)" in result
        assert "화(火)" in result
        assert "토(土)" in result
        assert "금(金)" in result
        assert "수(水)" in result
        assert count == 5

    def test_JSON_응답_딕셔너리_처리(self) -> None:
        """JSON 응답 형태 딕셔너리 처리"""
        fixer = BracketFixer()
        data = {
            "chart": {
                "year": {"gan": "갑()", "ji": "자()"},
                "month": {"gan": "을()", "ji": "축()"},
                "day": {"gan": "병()", "ji": "인()"},
                "hour": {"gan": "정()", "ji": "묘()"},
            },
            "stats": {
                "five_elements": {
                    "summary": "목()이 강하고 수()가 부족합니다."
                }
            },
            "fortune_content": {
                "overview": "갑()자() 연주를 가진 분입니다."
            }
        }
        result, count = fixer.fix_dict(data)

        assert result["chart"]["year"]["gan"] == "갑(甲)"
        assert result["chart"]["year"]["ji"] == "자(子)"
        assert "목(木)" in result["stats"]["five_elements"]["summary"]
        assert "수(水)" in result["stats"]["five_elements"]["summary"]
        assert count == 12
