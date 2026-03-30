"""XML 태그 감지 모듈

티키타카 버블 XML 태그를 감지하고 파싱하기 위한 정규식 패턴과 유틸리티.
"""

import re
from typing import TypedDict

# ============================================================
# 유효한 값 집합 정의
# ============================================================

VALID_CHARACTERS: set[str] = {"SOISEOL", "STELLA", "SYSTEM"}

VALID_EMOTIONS: set[str] = {
    "NEUTRAL",
    "HAPPY",
    "CURIOUS",
    "THOUGHTFUL",
    "SURPRISED",
    "CONCERNED",
    "CONFIDENT",
    "PLAYFUL",
    "MYSTERIOUS",
    "EMPATHETIC",
}

VALID_MESSAGE_TYPES: set[str] = {
    "GREETING",
    "INFO_REQUEST",
    "INTERPRETATION",
    "DEBATE",
    "CONSENSUS",
    "QUESTION",
    "CHOICE",
    "SUMMARY",
    "FAREWELL",
}

# 기본값
DEFAULT_CHARACTER = "SOISEOL"
DEFAULT_EMOTION = "NEUTRAL"
DEFAULT_MESSAGE_TYPE = "INTERPRETATION"


# ============================================================
# 정규식 패턴 (사전 컴파일)
# ============================================================

# 정규 순서 버블 태그 패턴 (character, emotion, type 순서)
BUBBLE_STRICT_PATTERN = re.compile(
    r'<bubble\s+'
    r'character="(?P<character>\w+)"\s+'
    r'emotion="(?P<emotion>\w+)"\s+'
    r'type="(?P<type>\w+)"'
    r'(?:\s+reply_to="(?P<reply_to>[\w-]+)")?'
    r'\s*>'
    r'(?P<content>[\s\S]*?)'
    r'</bubble>',
    re.DOTALL,
)

# 유연한 순서 버블 태그 패턴 (속성 순서 무관)
BUBBLE_FLEXIBLE_PATTERN = re.compile(
    r'<bubble\s+'
    r'(?=(?:[^>]*\bcharacter="(?P<character>\w+)"))'
    r'(?=(?:[^>]*\bemotion="(?P<emotion>\w+)"))'
    r'(?=(?:[^>]*\btype="(?P<type>\w+)"))'
    r'(?:[^>]*\breply_to="(?P<reply_to>[\w-]+)")?'
    r'[^>]*>'
    r'(?P<content>[\s\S]*?)'
    r'</bubble>',
    re.DOTALL,
)

# 여는 태그만 파싱 (스트리밍용)
BUBBLE_OPEN_PATTERN = re.compile(
    r'<bubble\s+'
    r'(?=(?:[^>]*\bcharacter="(?P<character>\w+)"))'
    r'(?=(?:[^>]*\bemotion="(?P<emotion>\w+)"))'
    r'(?=(?:[^>]*\btype="(?P<type>\w+)"))'
    r'(?:[^>]*\breply_to="(?P<reply_to>[\w-]+)")?'
    r'[^>]*>',
    re.DOTALL,
)

# 닫는 태그 패턴
BUBBLE_CLOSE_PATTERN = re.compile(r'</bubble>')

# 불완전 태그 감지 패턴 (스트리밍 중 버퍼링 판단용)
INCOMPLETE_OPEN_PATTERN = re.compile(r'<bubble(?:\s+[^>]*)?$')
INCOMPLETE_CLOSE_PATTERN = re.compile(r'</bubbl?e?$')

# tikitaka 래퍼 태그 패턴
TIKITAKA_WRAPPER_PATTERN = re.compile(
    r'<tikitaka>\s*(?P<inner>[\s\S]*?)\s*</tikitaka>',
    re.DOTALL,
)


# ============================================================
# 타입 정의
# ============================================================


class BubbleAttributes(TypedDict):
    """버블 속성 딕셔너리 타입"""

    character: str
    emotion: str
    type: str
    reply_to: str | None


class ParsedTagResult(TypedDict):
    """파싱된 태그 결과 타입"""

    attributes: BubbleAttributes
    content: str
    raw_match: str
    start_pos: int
    end_pos: int


# ============================================================
# 유틸리티 함수
# ============================================================


def normalize_character(value: str) -> str:
    """캐릭터 코드 정규화

    Args:
        value: 입력값 (한글 또는 영문)

    Returns:
        정규화된 캐릭터 코드 (유효하지 않으면 기본값)
    """
    # 한글 매핑
    korean_mapping = {
        "소이설": "SOISEOL",
        "스텔라": "STELLA",
        "시스템": "SYSTEM",
    }

    normalized = value.strip()

    # 한글인 경우 변환
    if normalized in korean_mapping:
        normalized = korean_mapping[normalized]
    else:
        normalized = normalized.upper()

    # 유효성 검사
    if normalized in VALID_CHARACTERS:
        return normalized

    return DEFAULT_CHARACTER


def normalize_emotion(value: str) -> str:
    """감정 코드 정규화

    Args:
        value: 입력값

    Returns:
        정규화된 감정 코드 (유효하지 않으면 기본값)
    """
    normalized = value.strip().upper()

    if normalized in VALID_EMOTIONS:
        return normalized

    return DEFAULT_EMOTION


def normalize_message_type(value: str) -> str:
    """메시지 타입 정규화

    Args:
        value: 입력값

    Returns:
        정규화된 메시지 타입 (유효하지 않으면 기본값)
    """
    normalized = value.strip().upper()

    if normalized in VALID_MESSAGE_TYPES:
        return normalized

    return DEFAULT_MESSAGE_TYPE


def sanitize_content(content: str) -> str:
    """버블 내용 정제

    - 앞뒤 공백 제거
    - 연속 개행 정리
    - XML 엔티티 디코딩

    Args:
        content: 원본 내용

    Returns:
        정제된 내용
    """
    if not content:
        return ""

    # 앞뒤 공백 제거
    result = content.strip()

    # 연속 개행을 단일 개행으로
    result = re.sub(r'\n{3,}', '\n\n', result)

    # 기본 XML 엔티티 디코딩
    xml_entities = {
        '&lt;': '<',
        '&gt;': '>',
        '&amp;': '&',
        '&quot;': '"',
        '&apos;': "'",
    }
    for entity, char in xml_entities.items():
        result = result.replace(entity, char)

    return result


def extract_tikitaka_content(text: str) -> str:
    """tikitaka 래퍼 태그 내부 콘텐츠 추출

    Args:
        text: 전체 텍스트

    Returns:
        tikitaka 태그 내부 콘텐츠 (없으면 원본 반환)
    """
    match = TIKITAKA_WRAPPER_PATTERN.search(text)
    if match:
        return match.group("inner")
    return text


def has_incomplete_tag(text: str) -> bool:
    """불완전한 태그가 있는지 확인 (스트리밍 버퍼링 판단용)

    Args:
        text: 버퍼 텍스트

    Returns:
        불완전한 태그 존재 여부
    """
    # 마지막 100자만 검사 (성능 최적화)
    tail = text[-100:] if len(text) > 100 else text

    return bool(
        INCOMPLETE_OPEN_PATTERN.search(tail)
        or INCOMPLETE_CLOSE_PATTERN.search(tail)
    )


def find_bubble_tags(text: str, flexible: bool = True) -> list[ParsedTagResult]:
    """텍스트에서 모든 버블 태그 찾기

    Args:
        text: 검색할 텍스트
        flexible: 유연한 패턴 사용 여부

    Returns:
        파싱된 태그 결과 리스트
    """
    # tikitaka 래퍼 제거
    content = extract_tikitaka_content(text)

    pattern = BUBBLE_FLEXIBLE_PATTERN if flexible else BUBBLE_STRICT_PATTERN
    results: list[ParsedTagResult] = []

    for match in pattern.finditer(content):
        attributes: BubbleAttributes = {
            "character": normalize_character(match.group("character") or ""),
            "emotion": normalize_emotion(match.group("emotion") or ""),
            "type": normalize_message_type(match.group("type") or ""),
            "reply_to": match.group("reply_to"),
        }

        results.append({
            "attributes": attributes,
            "content": sanitize_content(match.group("content") or ""),
            "raw_match": match.group(0),
            "start_pos": match.start(),
            "end_pos": match.end(),
        })

    return results
