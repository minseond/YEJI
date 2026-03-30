"""티키타카 버블 파서 패키지

LLM 출력에서 XML 형식의 버블 태그를 파싱합니다.

주요 컴포넌트:
- BubbleParser: 스트리밍/배치 파싱 지원 메인 파서
- ParsedBubble: 파싱된 버블 데이터 클래스
- FallbackParser: XML 파싱 실패 시 폴백 전략
- ParserState: 스트리밍 파서 상태 Enum

사용 예시:
    # 배치 파싱
    from yeji_ai.services.parsers import parse_bubbles

    bubbles = parse_bubbles(llm_output)
    for bubble in bubbles:
        print(f"{bubble.character}: {bubble.content}")

    # 스트리밍 파싱
    from yeji_ai.services.parsers import BubbleParser

    parser = BubbleParser()
    for chunk in token_stream:
        completed = parser.feed(chunk)
        for bubble in completed:
            yield bubble
    # 스트리밍 종료 시
    remaining = parser.flush()
"""

from yeji_ai.services.parsers.bubble_parser import (
    BubbleParser,
    BubbleStreamEvent,
    ParserState,
    generate_bubble_id,
    parse_bubbles,
)
from yeji_ai.services.parsers.fallback_parsers import (
    FallbackParser,
    ParsedBubble,
    parse_with_fallback,
)
from yeji_ai.services.parsers.xml_detector import (
    DEFAULT_CHARACTER,
    DEFAULT_EMOTION,
    DEFAULT_MESSAGE_TYPE,
    VALID_CHARACTERS,
    VALID_EMOTIONS,
    VALID_MESSAGE_TYPES,
    extract_tikitaka_content,
    find_bubble_tags,
    has_incomplete_tag,
    normalize_character,
    normalize_emotion,
    normalize_message_type,
    sanitize_content,
)

__all__ = [
    # 메인 파서
    "BubbleParser",
    "ParserState",
    "BubbleStreamEvent",
    "parse_bubbles",
    "generate_bubble_id",
    # 폴백 파서
    "FallbackParser",
    "ParsedBubble",
    "parse_with_fallback",
    # XML 감지 유틸리티
    "find_bubble_tags",
    "has_incomplete_tag",
    "extract_tikitaka_content",
    # 정규화 함수
    "normalize_character",
    "normalize_emotion",
    "normalize_message_type",
    "sanitize_content",
    # 상수
    "VALID_CHARACTERS",
    "VALID_EMOTIONS",
    "VALID_MESSAGE_TYPES",
    "DEFAULT_CHARACTER",
    "DEFAULT_EMOTION",
    "DEFAULT_MESSAGE_TYPE",
]
