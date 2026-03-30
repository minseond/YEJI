"""폴백 파서 모듈

XML 파싱 실패 시 사용하는 폴백 전략들을 제공합니다.

폴백 계층:
1. XML 태그 파싱 (정규 패턴)
2. 유연한 XML 파싱 (속성 순서 무관)
3. 접두사 기반 파싱 ([소이설], [스텔라])
4. 전체 텍스트를 단일 버블로 처리
"""

import re
import uuid
from dataclasses import dataclass, field

import structlog

from yeji_ai.services.parsers.xml_detector import (
    BUBBLE_FLEXIBLE_PATTERN,
    BUBBLE_STRICT_PATTERN,
    DEFAULT_CHARACTER,
    DEFAULT_EMOTION,
    DEFAULT_MESSAGE_TYPE,
    extract_tikitaka_content,
    normalize_character,
    normalize_emotion,
    normalize_message_type,
    sanitize_content,
)

logger = structlog.get_logger()


# ============================================================
# 데이터 클래스
# ============================================================


@dataclass
class ParsedBubble:
    """파싱된 버블 데이터"""

    character: str  # SOISEOL, STELLA, SYSTEM
    emotion: str  # NEUTRAL, HAPPY, CURIOUS, etc.
    type: str  # INTERPRETATION, GREETING, etc.
    content: str
    reply_to: str | None = None
    bubble_id: str = field(default_factory=lambda: f"b_{uuid.uuid4().hex[:8]}")
    is_complete: bool = True  # 스트리밍 중 부분 버블 여부
    parse_method: str = "xml"  # 파싱 방법 (xml, xml_flexible, prefix, fallback)


# ============================================================
# 접두사 기반 파싱 패턴
# ============================================================

# 접두사 패턴: [소이설], [스텔라], [SOISEOL], [STELLA]
PREFIX_PATTERN = re.compile(
    r'\[(?P<character>소이설|스텔라|시스템|SOISEOL|STELLA|SYSTEM)\]\s*'
    r'(?P<content>.+?)'
    r'(?=\[(?:소이설|스텔라|시스템|SOISEOL|STELLA|SYSTEM)\]|$)',
    re.DOTALL,
)


# ============================================================
# 폴백 파서 클래스
# ============================================================


class FallbackParser:
    """폴백 파서 체인

    XML 파싱 실패 시 순차적으로 폴백 전략을 적용합니다.
    """

    def __init__(self, session_id: str | None = None) -> None:
        """폴백 파서 초기화

        Args:
            session_id: 로깅용 세션 ID
        """
        self._session_id = session_id

    def parse(self, text: str) -> list[ParsedBubble]:
        """폴백 파싱 실행

        4단계 폴백 전략을 순차적으로 적용합니다.

        Args:
            text: 원본 텍스트

        Returns:
            파싱된 버블 목록
        """
        if not text or not text.strip():
            return []

        # tikitaka 래퍼 제거
        content = extract_tikitaka_content(text)

        # 시도 1: 정규 XML 패턴
        bubbles = self._parse_with_strict_xml(content)
        if bubbles:
            return bubbles

        # 시도 2: 유연한 XML 패턴
        bubbles = self._parse_with_flexible_xml(content)
        if bubbles:
            return bubbles

        # 시도 3: 접두사 기반 파싱
        bubbles = self._parse_with_prefix(content)
        if bubbles:
            return bubbles

        # 시도 4: 전체를 단일 버블로
        return self._parse_as_single(content)

    def _parse_with_strict_xml(self, text: str) -> list[ParsedBubble]:
        """정규 XML 패턴으로 파싱 (속성 순서 고정)

        Args:
            text: 파싱할 텍스트

        Returns:
            파싱된 버블 목록 (실패 시 빈 리스트)
        """
        bubbles: list[ParsedBubble] = []

        for match in BUBBLE_STRICT_PATTERN.finditer(text):
            content = sanitize_content(match.group("content") or "")

            # 빈 내용은 스킵
            if not content:
                continue

            bubbles.append(
                ParsedBubble(
                    character=normalize_character(match.group("character") or ""),
                    emotion=normalize_emotion(match.group("emotion") or ""),
                    type=normalize_message_type(match.group("type") or ""),
                    content=content,
                    reply_to=match.group("reply_to"),
                    parse_method="xml",
                )
            )

        return bubbles

    def _parse_with_flexible_xml(self, text: str) -> list[ParsedBubble]:
        """유연한 XML 패턴으로 파싱 (속성 순서 무관)

        Args:
            text: 파싱할 텍스트

        Returns:
            파싱된 버블 목록 (실패 시 빈 리스트)
        """
        bubbles: list[ParsedBubble] = []

        for match in BUBBLE_FLEXIBLE_PATTERN.finditer(text):
            content = sanitize_content(match.group("content") or "")

            # 빈 내용은 스킵
            if not content:
                continue

            bubbles.append(
                ParsedBubble(
                    character=normalize_character(match.group("character") or ""),
                    emotion=normalize_emotion(match.group("emotion") or ""),
                    type=normalize_message_type(match.group("type") or ""),
                    content=content,
                    reply_to=match.group("reply_to"),
                    parse_method="xml_flexible",
                )
            )

        if bubbles:
            logger.info(
                "bubble_parser_fallback",
                level=2,
                strategy="xml_flexible",
                bubble_count=len(bubbles),
                session_id=self._session_id,
            )

        return bubbles

    def _parse_with_prefix(self, text: str) -> list[ParsedBubble]:
        """접두사 기반 파싱 ([소이설], [스텔라])

        Args:
            text: 파싱할 텍스트

        Returns:
            파싱된 버블 목록 (실패 시 빈 리스트)
        """
        bubbles: list[ParsedBubble] = []

        for match in PREFIX_PATTERN.finditer(text):
            content = sanitize_content(match.group("content") or "")

            # 빈 내용은 스킵
            if not content:
                continue

            bubbles.append(
                ParsedBubble(
                    character=normalize_character(match.group("character") or ""),
                    emotion=DEFAULT_EMOTION,
                    type=DEFAULT_MESSAGE_TYPE,
                    content=content,
                    reply_to=None,
                    parse_method="prefix",
                )
            )

        if bubbles:
            logger.warning(
                "bubble_parser_fallback",
                level=3,
                strategy="prefix",
                bubble_count=len(bubbles),
                original_text=text[:100],
                session_id=self._session_id,
            )

        return bubbles

    def _parse_as_single(self, text: str) -> list[ParsedBubble]:
        """전체 텍스트를 단일 버블로 처리

        Args:
            text: 원본 텍스트

        Returns:
            단일 버블 리스트
        """
        content = sanitize_content(text)

        # 빈 내용이면 빈 리스트 반환
        if not content:
            return []

        logger.warning(
            "bubble_parser_fallback",
            level=4,
            strategy="single_bubble",
            content_length=len(content),
            original_text=text[:100],
            session_id=self._session_id,
        )

        return [
            ParsedBubble(
                character=DEFAULT_CHARACTER,
                emotion=DEFAULT_EMOTION,
                type=DEFAULT_MESSAGE_TYPE,
                content=content,
                reply_to=None,
                parse_method="fallback",
            )
        ]


# ============================================================
# 편의 함수
# ============================================================


def parse_with_fallback(
    text: str,
    session_id: str | None = None,
) -> list[ParsedBubble]:
    """폴백 전략을 적용하여 텍스트 파싱

    Args:
        text: 파싱할 텍스트
        session_id: 로깅용 세션 ID

    Returns:
        파싱된 버블 목록
    """
    parser = FallbackParser(session_id=session_id)
    return parser.parse(text)
