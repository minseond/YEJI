"""빈 괄호 및 한자 누락 후처리 필터

LLM 응답에서 빈 괄호 `()` 제거 또는 천간/지지 한자 자동 완성을 수행합니다.

사용 예시:
    from yeji_ai.services.postprocessor.bracket_fixer import (
        fix_brackets,
        BracketFixer,
    )

    # 간편 함수 사용
    text = "갑() 을()"
    fixed = fix_brackets(text)  # "갑(甲) 을(乙)"

    # 클래스 사용 (상세 결과)
    fixer = BracketFixer()
    result, fixed_count = fixer.fix(text)
"""

import re

import structlog

logger = structlog.get_logger()

# ============================================================
# 천간/지지 한글 -> 한자 매핑 테이블
# ============================================================

# 천간 (天干) - 10개
CHEONGAN_MAPPING: dict[str, str] = {
    "갑": "甲",
    "을": "乙",
    "병": "丙",
    "정": "丁",
    "무": "戊",
    "기": "己",
    "경": "庚",
    "신": "辛",
    "임": "壬",
    "계": "癸",
}

# 지지 (地支) - 12개
JIJI_MAPPING: dict[str, str] = {
    "자": "子",
    "축": "丑",
    "인": "寅",
    "묘": "卯",
    "진": "辰",
    "사": "巳",
    "오": "午",
    "미": "未",
    "신": "申",
    "유": "酉",
    "술": "戌",
    "해": "亥",
}

# 통합 매핑 (천간 + 지지)
# 주의: '신'은 천간(辛)과 지지(申) 모두 존재함 - 천간 우선 적용
# 지지를 먼저 병합하고 천간을 나중에 병합하여 천간이 덮어쓰도록 함
HANGUL_TO_HANJA: dict[str, str] = {**JIJI_MAPPING, **CHEONGAN_MAPPING}

# 오행 (五行) - 한글/한자 매핑 (보조용)
ELEMENT_MAPPING: dict[str, str] = {
    "목": "木",
    "화": "火",
    "토": "土",
    "금": "金",
    "수": "水",
}

# 모든 매핑 통합 (천간 + 지지 + 오행)
ALL_HANGUL_TO_HANJA: dict[str, str] = {**HANGUL_TO_HANJA, **ELEMENT_MAPPING}


class BracketFixer:
    """빈 괄호 및 한자 누락 수정기

    LLM이 생성한 텍스트에서 다음과 같은 패턴을 수정합니다:
    1. 빈 괄호 `()` 제거
    2. 천간/지지 한글 뒤 빈 괄호에 한자 자동 완성 (예: "갑()" → "갑(甲)")
    3. 오행 한글 뒤 빈 괄호에 한자 자동 완성 (예: "목()" → "목(木)")
    """

    # 빈 괄호 패턴: 한글 1글자 + 빈 괄호
    # 예: 갑(), 을(), 자(), 축() 등
    HANGUL_EMPTY_BRACKET_PATTERN = re.compile(r"([가-힣])\s*\(\s*\)")

    # 완전한 빈 괄호 패턴 (앞에 한글 없이 단독으로 존재)
    # 예: "운세가 () 좋습니다" → "운세가 좋습니다"
    STANDALONE_EMPTY_BRACKET_PATTERN = re.compile(r"\s*\(\s*\)\s*")

    # 중복 공백 패턴
    MULTIPLE_SPACES_PATTERN = re.compile(r"\s{2,}")

    def __init__(self, include_elements: bool = True):
        """초기화

        Args:
            include_elements: 오행(목화토금수) 한자 자동완성 포함 여부
        """
        self._mapping = ALL_HANGUL_TO_HANJA if include_elements else HANGUL_TO_HANJA

    def fix(self, text: str) -> tuple[str, int]:
        """빈 괄호 수정

        Args:
            text: 원본 텍스트

        Returns:
            tuple[str, int]: (수정된 텍스트, 수정 횟수)
        """
        if not text:
            return text, 0

        fixed_count = 0
        result = text

        # 1. 한글 + 빈 괄호 패턴 처리 (한자 자동 완성)
        def replace_with_hanja(match: re.Match) -> str:
            nonlocal fixed_count
            hangul = match.group(1)
            if hangul in self._mapping:
                fixed_count += 1
                return f"{hangul}({self._mapping[hangul]})"
            else:
                # 매핑에 없으면 빈 괄호 제거
                fixed_count += 1
                return hangul

        result = self.HANGUL_EMPTY_BRACKET_PATTERN.sub(replace_with_hanja, result)

        # 2. 단독 빈 괄호 제거 (앞에 한글 없이 존재하는 빈 괄호)
        standalone_matches = list(self.STANDALONE_EMPTY_BRACKET_PATTERN.finditer(result))
        if standalone_matches:
            fixed_count += len(standalone_matches)
            result = self.STANDALONE_EMPTY_BRACKET_PATTERN.sub(" ", result)

        # 3. 중복 공백 정리
        result = self.MULTIPLE_SPACES_PATTERN.sub(" ", result)
        result = result.strip()

        if fixed_count > 0:
            logger.debug(
                "bracket_fix_applied",
                fixed_count=fixed_count,
                original_length=len(text),
                result_length=len(result),
            )

        return result, fixed_count

    def fix_dict(self, data: dict, recursive: bool = True) -> tuple[dict, int]:
        """딕셔너리 내 모든 문자열 값에서 빈 괄호 수정

        Args:
            data: 원본 딕셔너리
            recursive: 중첩 딕셔너리/리스트 재귀 처리 여부

        Returns:
            tuple[dict, int]: (수정된 딕셔너리, 총 수정 횟수)
        """
        total_fixed = 0

        def process_value(value):
            nonlocal total_fixed
            if isinstance(value, str):
                fixed, count = self.fix(value)
                total_fixed += count
                return fixed
            elif isinstance(value, dict) and recursive:
                return {k: process_value(v) for k, v in value.items()}
            elif isinstance(value, list) and recursive:
                return [process_value(item) for item in value]
            return value

        result = {k: process_value(v) for k, v in data.items()}
        return result, total_fixed


# 싱글톤 인스턴스
_bracket_fixer = BracketFixer()


def fix_brackets(text: str) -> str:
    """빈 괄호 수정 (편의 함수)

    Args:
        text: 원본 텍스트

    Returns:
        수정된 텍스트
    """
    result, _ = _bracket_fixer.fix(text)
    return result


def fix_brackets_in_dict(data: dict) -> dict:
    """딕셔너리 내 빈 괄호 수정 (편의 함수)

    Args:
        data: 원본 딕셔너리

    Returns:
        수정된 딕셔너리
    """
    result, _ = _bracket_fixer.fix_dict(data)
    return result


def get_hanja_for_hangul(hangul: str) -> str | None:
    """한글에 해당하는 한자 반환

    Args:
        hangul: 한글 1글자 (천간/지지/오행)

    Returns:
        해당 한자 또는 None
    """
    return ALL_HANGUL_TO_HANJA.get(hangul)


# 테스트용
if __name__ == "__main__":
    test_texts = [
        "갑() 을()",  # 천간 빈 괄호
        "자() 축() 인()",  # 지지 빈 괄호
        "갑(甲) 을(乙)",  # 이미 한자 있음
        "오늘 운세가 () 좋습니다.",  # 단독 빈 괄호
        "목() 화() 토()",  # 오행 빈 괄호
        "연주: 갑() 자()",  # 복합 케이스
        "병(丙)화 정()화",  # 일부만 누락
    ]

    fixer = BracketFixer()
    for text in test_texts:
        fixed, count = fixer.fix(text)
        print(f"원본: {text}")
        print(f"수정: {fixed} (수정 횟수: {count})")
        print()
