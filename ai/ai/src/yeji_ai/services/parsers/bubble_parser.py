"""티키타카 버블 파서 모듈

XML 태그 기반 LLM 출력을 ParsedBubble 객체로 변환합니다.
스트리밍 및 배치 파싱을 모두 지원합니다.
"""

import uuid
from collections.abc import Generator
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import structlog

from yeji_ai.services.parsers.fallback_parsers import (
    FallbackParser,
    ParsedBubble,
)
from yeji_ai.services.parsers.xml_detector import (
    BUBBLE_CLOSE_PATTERN,
    BUBBLE_OPEN_PATTERN,
    DEFAULT_CHARACTER,
    DEFAULT_EMOTION,
    DEFAULT_MESSAGE_TYPE,
    has_incomplete_tag,
    normalize_character,
    normalize_emotion,
    normalize_message_type,
    sanitize_content,
)

logger = structlog.get_logger()


# ============================================================
# 상태 정의
# ============================================================


class ParserState(str, Enum):
    """파서 상태"""

    IDLE = "idle"  # 대기 상태, 버블 외부
    OPENING = "opening"  # 여는 태그 파싱 중
    CONTENT = "content"  # 버블 내용 수집 중
    COMPLETE = "complete"  # 버블 파싱 완료


# ============================================================
# 스트림 이벤트
# ============================================================


@dataclass
class BubbleStreamEvent:
    """버블 스트림 이벤트"""

    event_type: str  # bubble_start, bubble_chunk, bubble_end, error
    bubble_id: str
    data: dict[str, Any] = field(default_factory=dict)

    def to_sse(self) -> str:
        """SSE 형식 문자열로 변환"""
        import json

        event_data = {
            "bubble_id": self.bubble_id,
            **self.data,
        }
        return f"event: {self.event_type}\ndata: {json.dumps(event_data, ensure_ascii=False)}\n\n"


# ============================================================
# 스트리밍 버블 파서
# ============================================================


class BubbleParser:
    """티키타카 버블 파서

    XML 태그 기반 LLM 출력을 ParsedBubble 객체로 변환합니다.
    스트리밍 및 배치 파싱을 모두 지원합니다.
    """

    # 버퍼 최대 크기 (4KB)
    MAX_BUFFER_SIZE = 4096

    def __init__(self, session_id: str | None = None) -> None:
        """파서 초기화

        Args:
            session_id: 로깅용 세션 ID
        """
        self._session_id = session_id
        self._fallback_parser = FallbackParser(session_id=session_id)
        self.reset()

    def reset(self) -> None:
        """파서 상태 초기화"""
        self._state = ParserState.IDLE
        self._buffer = ""
        self._current_bubble_id: str | None = None
        self._current_attributes: dict[str, Any] = {}
        self._current_content = ""
        self._completed_bubbles: list[ParsedBubble] = []

    @property
    def state(self) -> ParserState:
        """현재 파서 상태"""
        return self._state

    def parse(self, text: str) -> list[ParsedBubble]:
        """배치 파싱 - 전체 텍스트에서 버블 추출

        Args:
            text: LLM 출력 텍스트

        Returns:
            파싱된 버블 목록
        """
        if not text or not text.strip():
            return []

        # 폴백 파서 사용 (4단계 폴백 전략 적용)
        return self._fallback_parser.parse(text)

    def parse_stream(self, text: str) -> Generator[ParsedBubble, None, None]:
        """스트리밍 파싱 - 제너레이터 방식

        Args:
            text: LLM 출력 텍스트

        Yields:
            파싱된 버블
        """
        bubbles = self.parse(text)
        yield from bubbles

    def feed(self, chunk: str) -> list[ParsedBubble]:
        """토큰 청크를 입력받아 완성된 버블 리스트 반환

        스트리밍 중 토큰 단위로 호출합니다.

        Args:
            chunk: LLM 출력 토큰 청크

        Returns:
            완성된 버블 리스트 (없으면 빈 리스트)
        """
        if not chunk:
            return []

        # 버퍼에 추가
        self._buffer += chunk

        # 버퍼 오버플로우 방지
        if len(self._buffer) > self.MAX_BUFFER_SIZE:
            logger.warning(
                "bubble_parser_buffer_overflow",
                buffer_size=len(self._buffer),
                max_size=self.MAX_BUFFER_SIZE,
                session_id=self._session_id,
            )
            # 앞부분 삭제
            self._buffer = self._buffer[-self.MAX_BUFFER_SIZE:]

        completed: list[ParsedBubble] = []

        # 상태 머신 처리
        while True:
            if self._state == ParserState.IDLE:
                if not self._process_idle_state():
                    break
            elif self._state == ParserState.OPENING:
                if not self._process_opening_state():
                    break
            elif self._state == ParserState.CONTENT:
                bubble = self._process_content_state()
                if bubble:
                    completed.append(bubble)
                else:
                    break
            elif self._state == ParserState.COMPLETE:
                self._state = ParserState.IDLE

        return completed

    def _process_idle_state(self) -> bool:
        """IDLE 상태 처리 - <bubble 태그 찾기

        Returns:
            상태 전이 발생 여부
        """
        # <bubble 태그 시작 찾기
        idx = self._buffer.find("<bubble")
        if idx == -1:
            # 불완전 태그 체크
            if has_incomplete_tag(self._buffer):
                return False
            # 태그 이전 텍스트 제거 (메모리 관리)
            if len(self._buffer) > 100:
                self._buffer = self._buffer[-100:]
            return False

        # 태그 이전 텍스트 제거
        self._buffer = self._buffer[idx:]
        self._state = ParserState.OPENING
        return True

    def _process_opening_state(self) -> bool:
        """OPENING 상태 처리 - 여는 태그 완성 대기

        Returns:
            상태 전이 발생 여부
        """
        # 여는 태그 완성 확인
        match = BUBBLE_OPEN_PATTERN.match(self._buffer)
        if not match:
            # 태그가 아직 완성되지 않음
            return False

        # 속성 추출
        self._current_bubble_id = f"b_{uuid.uuid4().hex[:8]}"
        self._current_attributes = {
            "character": normalize_character(match.group("character") or ""),
            "emotion": normalize_emotion(match.group("emotion") or ""),
            "type": normalize_message_type(match.group("type") or ""),
            "reply_to": match.group("reply_to"),
        }
        self._current_content = ""

        # 태그 이후부터 버퍼 시작
        self._buffer = self._buffer[match.end():]
        self._state = ParserState.CONTENT
        return True

    def _process_content_state(self) -> ParsedBubble | None:
        """CONTENT 상태 처리 - 내용 수집 및 닫는 태그 찾기

        Returns:
            완성된 버블 (없으면 None)
        """
        # 닫는 태그 찾기
        match = BUBBLE_CLOSE_PATTERN.search(self._buffer)
        if not match:
            # 닫는 태그 없음 - 현재까지 내용 저장
            # 불완전 태그가 있으면 버퍼 유지
            if has_incomplete_tag(self._buffer):
                return None

            # 내용 추가 (마지막 10자는 태그 시작일 수 있으므로 유지)
            if len(self._buffer) > 10:
                self._current_content += self._buffer[:-10]
                self._buffer = self._buffer[-10:]
            return None

        # 닫는 태그 발견 - 버블 완성
        self._current_content += self._buffer[:match.start()]
        self._buffer = self._buffer[match.end():]

        content = sanitize_content(self._current_content)

        # 빈 내용은 스킵
        if not content:
            self._state = ParserState.COMPLETE
            return None

        bubble = ParsedBubble(
            bubble_id=self._current_bubble_id or f"b_{uuid.uuid4().hex[:8]}",
            character=self._current_attributes.get("character", DEFAULT_CHARACTER),
            emotion=self._current_attributes.get("emotion", DEFAULT_EMOTION),
            type=self._current_attributes.get("type", DEFAULT_MESSAGE_TYPE),
            content=content,
            reply_to=self._current_attributes.get("reply_to"),
            is_complete=True,
            parse_method="xml_streaming",
        )

        self._state = ParserState.COMPLETE
        return bubble

    def get_partial_content(self) -> str | None:
        """현재 파싱 중인 버블의 부분 콘텐츠 반환

        Returns:
            부분 콘텐츠 (파싱 중이 아니면 None)
        """
        if self._state == ParserState.CONTENT:
            return sanitize_content(self._current_content + self._buffer)
        return None

    def flush(self) -> list[ParsedBubble]:
        """스트리밍 종료 시 남은 버퍼 처리

        Returns:
            남은 버블 리스트
        """
        bubbles: list[ParsedBubble] = []

        # 파싱 중인 버블이 있으면 불완전 상태로 반환
        if self._state == ParserState.CONTENT and self._current_content:
            content = sanitize_content(self._current_content + self._buffer)
            if content:
                bubbles.append(
                    ParsedBubble(
                        bubble_id=self._current_bubble_id or f"b_{uuid.uuid4().hex[:8]}",
                        character=self._current_attributes.get("character", DEFAULT_CHARACTER),
                        emotion=self._current_attributes.get("emotion", DEFAULT_EMOTION),
                        type=self._current_attributes.get("type", DEFAULT_MESSAGE_TYPE),
                        content=content,
                        reply_to=self._current_attributes.get("reply_to"),
                        is_complete=False,
                        parse_method="xml_streaming_incomplete",
                    )
                )
                logger.warning(
                    "bubble_parser_incomplete_bubble",
                    bubble_id=self._current_bubble_id,
                    content_length=len(content),
                    session_id=self._session_id,
                )

        self.reset()
        return bubbles

    def feed_stream_events(self, chunk: str) -> list[BubbleStreamEvent]:
        """토큰 입력 및 스트림 이벤트 반환

        Args:
            chunk: LLM 출력 토큰

        Returns:
            발생한 이벤트 목록 (없으면 빈 리스트)
        """
        events: list[BubbleStreamEvent] = []
        prev_state = self._state

        bubbles = self.feed(chunk)

        # 상태 전이에 따른 이벤트 생성
        if prev_state == ParserState.IDLE and self._state == ParserState.CONTENT:
            # bubble_start 이벤트
            events.append(
                BubbleStreamEvent(
                    event_type="bubble_start",
                    bubble_id=self._current_bubble_id or "",
                    data={
                        "character": self._current_attributes.get("character"),
                        "emotion": self._current_attributes.get("emotion"),
                        "type": self._current_attributes.get("type"),
                        "reply_to": self._current_attributes.get("reply_to"),
                    },
                )
            )

        # 완성된 버블에 대한 이벤트
        for bubble in bubbles:
            events.append(
                BubbleStreamEvent(
                    event_type="bubble_end",
                    bubble_id=bubble.bubble_id,
                    data={
                        "character": bubble.character,
                        "emotion": bubble.emotion,
                        "type": bubble.type,
                        "content": bubble.content,
                        "reply_to": bubble.reply_to,
                        "is_complete": bubble.is_complete,
                    },
                )
            )

        return events


# ============================================================
# 편의 함수
# ============================================================


def parse_bubbles(
    text: str,
    session_id: str | None = None,
) -> list[ParsedBubble]:
    """텍스트에서 버블 파싱 (배치 모드)

    Args:
        text: LLM 출력 텍스트
        session_id: 로깅용 세션 ID

    Returns:
        파싱된 버블 목록
    """
    parser = BubbleParser(session_id=session_id)
    return parser.parse(text)


def generate_bubble_id() -> str:
    """고유 버블 ID 생성

    Returns:
        "b_" 접두사가 붙은 UUID
    """
    return f"b_{uuid.uuid4().hex[:8]}"
