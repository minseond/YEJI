"""티키타카 V2 SSE 스트리밍 API 엔드포인트

## 사용 흐름

```
1. 스트리밍 대화 시작
   POST /api/v1/fortune/tikitaka/stream
   {
     "session_id": null,  // 첫 요청시 null
     "message": "운세를 알려주세요",
     "birth_date": "1990-05-15",
     "birth_time": "14:30",
     "is_premium": false
   }

2. SSE 이벤트 수신
   - session: 세션 정보
   - bubble_start: 버블 시작 (character, emotion)
   - bubble_chunk: 텍스트 청크
   - bubble_end: 버블 종료
   - complete: 대화 완료
```

## V2 스키마

- EmotionCode: NEUTRAL, HAPPY, CURIOUS 등 10종
- PhaseCode: GREETING, DIALOGUE, QUESTION, SUMMARY, FAREWELL
- BubbleParser: XML 태그 기반 버블 파싱
"""

import asyncio
import json
import re
import uuid
from datetime import datetime
from enum import Enum
from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from yeji_ai.services.tikitaka_service import TikitakaService, get_or_create_session

logger = structlog.get_logger()

router = APIRouter()

# 서비스 인스턴스 (싱글톤)
_service = TikitakaService()


# ============================================================
# V2 스키마 Enum 정의
# ============================================================


class EmotionCode(str, Enum):
    """감정 코드 (10종)"""

    NEUTRAL = "NEUTRAL"
    HAPPY = "HAPPY"
    CURIOUS = "CURIOUS"
    THOUGHTFUL = "THOUGHTFUL"
    SURPRISED = "SURPRISED"
    CONCERNED = "CONCERNED"
    CONFIDENT = "CONFIDENT"
    PLAYFUL = "PLAYFUL"
    MYSTERIOUS = "MYSTERIOUS"
    EMPATHETIC = "EMPATHETIC"


class PhaseCode(str, Enum):
    """대화 단계"""

    GREETING = "GREETING"
    DIALOGUE = "DIALOGUE"
    QUESTION = "QUESTION"
    SUMMARY = "SUMMARY"
    FAREWELL = "FAREWELL"


class SSEEventType(str, Enum):
    """SSE 이벤트 타입"""

    SESSION = "session"
    PHASE_CHANGE = "phase_change"
    BUBBLE_START = "bubble_start"
    BUBBLE_CHUNK = "bubble_chunk"
    BUBBLE_END = "bubble_end"
    TURN_UPDATE = "turn_update"
    DEBATE_STATUS = "debate_status"
    UI_HINT = "ui_hint"
    PAUSE = "pause"
    COMPLETE = "complete"
    ERROR = "error"


# ============================================================
# V2 요청/응답 모델
# ============================================================


class TikitakaStreamRequest(BaseModel):
    """티키타카 스트리밍 요청"""

    session_id: str | None = Field(None, description="세션 ID (신규 시 null)")
    message: str | None = Field(None, description="사용자 메시지")
    birth_date: str | None = Field(
        None, description="생년월일 (YYYY-MM-DD)", pattern=r"^\d{4}-\d{2}-\d{2}$"
    )
    birth_time: str | None = Field(None, description="출생시간 (HH:MM)", pattern=r"^\d{2}:\d{2}$")
    is_premium: bool = Field(False, description="프리미엄 사용자 여부")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": None,
                "message": "운세를 알려주세요",
                "birth_date": "1990-05-15",
                "birth_time": "14:30",
                "is_premium": False,
            }
        }


# ============================================================
# 버블 파서
# ============================================================


class BubbleParser:
    """XML 태그 기반 버블 파서

    LLM 출력에서 <bubble> 태그를 파싱하여 버블 데이터를 추출합니다.
    """

    # XML 버블 태그 패턴
    BUBBLE_PATTERN = re.compile(
        r"<bubble\s+"
        r'character="(?P<character>\w+)"\s+'
        r'emotion="(?P<emotion>\w+)"\s+'
        r'type="(?P<type>\w+)"'
        r'(?:\s+reply_to="(?P<reply_to>[\w-]+)")?'
        r"\s*>"
        r"(?P<content>[\s\S]*?)"
        r"</bubble>",
        re.DOTALL,
    )

    # 접두사 폴백 패턴
    PREFIX_PATTERN = re.compile(
        r"\[(?P<character>소이설|스텔라|SOISEOL|STELLA)\]\s*"
        r"(?P<content>.+?)(?=\[소이설\]|\[스텔라\]|\[SOISEOL\]|\[STELLA\]|$)",
        re.DOTALL,
    )

    # 유효한 값 집합
    VALID_CHARACTERS = {"SOISEOL", "STELLA", "SYSTEM"}
    VALID_EMOTIONS = {
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
    VALID_MESSAGE_TYPES = {
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

    # 캐릭터 매핑 (한글 -> 코드)
    CHARACTER_MAP = {
        "소이설": "SOISEOL",
        "스텔라": "STELLA",
        "SOISEOL": "SOISEOL",
        "STELLA": "STELLA",
    }

    def parse(self, text: str) -> list[dict[str, Any]]:
        """XML 텍스트에서 버블 추출

        Args:
            text: LLM 출력 텍스트

        Returns:
            파싱된 버블 목록
        """
        bubbles = []

        # XML 패턴 시도
        for match in self.BUBBLE_PATTERN.finditer(text):
            bubble = self._create_bubble_from_match(match)
            if bubble:
                bubbles.append(bubble)

        # XML 패턴 실패 시 폴백
        if not bubbles:
            bubbles = self._parse_fallback(text)

        return bubbles

    def _create_bubble_from_match(self, match: re.Match) -> dict[str, Any] | None:
        """정규식 매치에서 버블 생성"""
        character = match.group("character").upper()
        emotion = match.group("emotion").upper()
        msg_type = match.group("type").upper()
        content = match.group("content").strip()
        reply_to = match.group("reply_to")

        # 유효성 검증 및 기본값 적용
        if character not in self.VALID_CHARACTERS:
            character = "SOISEOL"
        if emotion not in self.VALID_EMOTIONS:
            emotion = "NEUTRAL"
        if msg_type not in self.VALID_MESSAGE_TYPES:
            msg_type = "INTERPRETATION"

        if not content:
            return None

        return {
            "bubble_id": self._generate_bubble_id(),
            "character": character,
            "emotion": emotion,
            "type": msg_type,
            "content": content,
            "reply_to": reply_to,
        }

    def _parse_fallback(self, text: str) -> list[dict[str, Any]]:
        """폴백 파싱 (접두사 기반)

        XML 파싱 실패 시 [소이설], [스텔라] 접두사로 파싱
        """
        bubbles = []

        for match in self.PREFIX_PATTERN.finditer(text):
            char_raw = match.group("character")
            character = self.CHARACTER_MAP.get(char_raw, "SOISEOL")
            content = match.group("content").strip()

            if content:
                bubbles.append(
                    {
                        "bubble_id": self._generate_bubble_id(),
                        "character": character,
                        "emotion": "NEUTRAL",
                        "type": "INTERPRETATION",
                        "content": content,
                        "reply_to": None,
                    }
                )

        # 폴백도 실패 시 전체 텍스트를 단일 버블로
        if not bubbles and text.strip():
            bubbles.append(
                {
                    "bubble_id": self._generate_bubble_id(),
                    "character": "SOISEOL",
                    "emotion": "NEUTRAL",
                    "type": "INTERPRETATION",
                    "content": text.strip(),
                    "reply_to": None,
                }
            )

        return bubbles

    def _generate_bubble_id(self) -> str:
        """고유 버블 ID 생성"""
        return f"b_{uuid.uuid4().hex[:8]}"


# 파서 인스턴스
_parser = BubbleParser()


# ============================================================
# SSE 이벤트 포매터
# ============================================================


def format_sse_event(event_type: str, data: dict[str, Any]) -> str:
    """SSE 이벤트 문자열 생성

    Args:
        event_type: 이벤트 타입
        data: 이벤트 데이터

    Returns:
        SSE 형식 문자열
    """
    json_data = json.dumps(data, ensure_ascii=False)
    return f"event: {event_type}\ndata: {json_data}\n\n"


# ============================================================
# 세션 상태 관리
# ============================================================


class TikitakaSessionStateV2:
    """V2 세션 상태 관리"""

    DEFAULT_MAX_TURNS = 10
    PREMIUM_BONUS_TURNS = 3

    def __init__(self, session_id: str, is_premium: bool = False):
        self.session_id = session_id
        self.current_turn = 0
        self.max_turns = self.DEFAULT_MAX_TURNS
        self.bonus_turns = self.PREMIUM_BONUS_TURNS if is_premium else 0
        self.is_premium = is_premium
        self.phase = PhaseCode.GREETING
        self.has_eastern_result = False
        self.has_western_result = False

    @property
    def remaining_turns(self) -> int:
        """남은 턴 수"""
        total = self.max_turns + self.bonus_turns
        return max(0, total - self.current_turn)

    @property
    def is_finished(self) -> bool:
        """대화 종료 여부"""
        return self.remaining_turns == 0

    def advance_turn(self) -> bool:
        """턴 진행 (성공 시 True)"""
        if self.is_finished:
            return False
        self.current_turn += 1
        return True

    def to_dict(self) -> dict[str, Any]:
        """직렬화"""
        return {
            "session_id": self.session_id,
            "current_turn": self.current_turn,
            "max_turns": self.max_turns,
            "bonus_turns": self.bonus_turns,
            "remaining_turns": self.remaining_turns,
            "is_premium": self.is_premium,
            "phase": self.phase.value,
            "has_eastern_result": self.has_eastern_result,
            "has_western_result": self.has_western_result,
        }


# V2 세션 저장소
_sessions_v2: dict[str, TikitakaSessionStateV2] = {}


def get_or_create_session_v2(
    session_id: str | None, is_premium: bool = False
) -> TikitakaSessionStateV2:
    """V2 세션 조회 또는 생성"""
    if session_id and session_id in _sessions_v2:
        return _sessions_v2[session_id]

    new_id = str(uuid.uuid4())[:8]
    session = TikitakaSessionStateV2(new_id, is_premium)
    _sessions_v2[new_id] = session
    return session


# ============================================================
# SSE 스트리밍 엔드포인트
# ============================================================


@router.post(
    "/tikitaka/stream",
    summary="티키타카 SSE 스트리밍",
    description="V2 스키마 기반 SSE 스트리밍으로 실시간 버블 응답을 받습니다.",
    responses={
        200: {
            "description": "스트리밍 성공",
            "content": {"text/event-stream": {}},
        },
        400: {"description": "잘못된 요청"},
        500: {"description": "서버 오류"},
    },
)
async def tikitaka_stream(request: TikitakaStreamRequest):
    """
    티키타카 SSE 스트리밍 API (V2)

    Server-Sent Events로 버블 단위 실시간 응답을 스트리밍합니다.

    **SSE 이벤트 타입:**
    - `session`: 세션 정보
    - `phase_change`: 단계 변경
    - `bubble_start`: 버블 시작 (character, emotion, type, phase)
    - `bubble_chunk`: 버블 청크 (content 조각)
    - `bubble_end`: 버블 완료 (전체 content, timestamp)
    - `turn_update`: 턴 업데이트
    - `debate_status`: 토론 상태
    - `complete`: 스트리밍 완료
    - `error`: 오류 발생

    **버블 스트리밍 시퀀스:**
    ```
    bubble_start -> bubble_chunk* -> bubble_end
    ```
    """
    logger.info(
        "tikitaka_stream_request",
        session_id=request.session_id,
        birth_date=request.birth_date,
        is_premium=request.is_premium,
    )

    async def generate():
        try:
            # V1 세션 조회/생성 (기존 서비스 연동)
            session_v1 = get_or_create_session(request.session_id)
            session_v1.turn += 1

            # V2 세션 상태 생성
            session_v2 = get_or_create_session_v2(session_v1.session_id, request.is_premium)

            # 사용자 정보 저장
            if request.birth_date:
                session_v1.user_info["birth_date"] = request.birth_date
            if request.birth_time:
                session_v1.user_info["birth_time"] = request.birth_time

            # 1. 세션 이벤트 전송
            yield format_sse_event(
                SSEEventType.SESSION.value,
                {
                    "session_id": session_v1.session_id,
                    "is_premium": request.is_premium,
                    "max_turns": session_v2.max_turns,
                    "bonus_turns": session_v2.bonus_turns,
                },
            )

            # 생년월일 확인
            birth_date = request.birth_date or session_v1.user_info.get("birth_date")
            if not birth_date:
                # 생년월일 미입력: INFO_REQUEST 버블 전송
                yield format_sse_event(
                    SSEEventType.PHASE_CHANGE.value,
                    {"phase": PhaseCode.GREETING.value},
                )

                # 인사 버블 스트리밍
                async for event in _stream_greeting_bubbles(session_v2):
                    yield event

                # 정보 요청 버블
                yield format_sse_event(
                    SSEEventType.PAUSE.value,
                    {
                        "waiting_for": "birth_date",
                        "placeholder": "생년월일을 입력해주세요 (예: 1990-05-15)",
                    },
                )

                yield format_sse_event(
                    SSEEventType.COMPLETE.value,
                    {"status": "waiting_input"},
                )
                return

            # 2. 분석 실행 (결과가 없는 경우)
            if not session_v1.eastern_result:
                yield format_sse_event(
                    SSEEventType.PHASE_CHANGE.value,
                    {"phase": PhaseCode.GREETING.value},
                )

                # 인사 버블 스트리밍
                async for event in _stream_greeting_bubbles(session_v2):
                    yield event

                # 분석 시작 알림
                yield format_sse_event(
                    "status",
                    {"message": "분석 중입니다..."},
                )

                birth_time = request.birth_time or session_v1.user_info.get("birth_time")
                try:
                    eastern_result, western_result = await _service.analyze_both(
                        birth_date=birth_date,
                        birth_time=birth_time,
                    )
                    session_v1.eastern_result = eastern_result
                    session_v1.western_result = western_result
                    session_v2.has_eastern_result = True
                    session_v2.has_western_result = True
                except Exception as e:
                    logger.error("analysis_error", error=str(e))
                    yield format_sse_event(
                        SSEEventType.ERROR.value,
                        {
                            "code": "ANALYSIS_ERROR",
                            "message": "분석 중 오류가 발생했습니다.",
                            "recoverable": False,
                        },
                    )
                    return

            # 3. 대화 단계로 전환
            session_v2.phase = PhaseCode.DIALOGUE
            yield format_sse_event(
                SSEEventType.PHASE_CHANGE.value,
                {"from_phase": PhaseCode.GREETING.value, "to_phase": PhaseCode.DIALOGUE.value},
            )

            # 4. 해석 버블 스트리밍
            async for event in _stream_interpretation_bubbles(session_v1, session_v2, _service):
                yield event

            # 5. 턴 업데이트
            session_v2.advance_turn()
            yield format_sse_event(
                SSEEventType.TURN_UPDATE.value,
                {
                    "current_turn": session_v2.current_turn,
                    "remaining_turns": session_v2.remaining_turns,
                    "is_last_turn": session_v2.remaining_turns <= 1,
                },
            )

            # 6. 완료 이벤트
            yield format_sse_event(
                SSEEventType.COMPLETE.value,
                {
                    "status": "success",
                    "total_bubbles": 3,  # 소이설, 스텔라, 합의 메시지
                },
            )

        except Exception as e:
            logger.error("tikitaka_stream_error", error=str(e), exc_info=True)
            yield format_sse_event(
                SSEEventType.ERROR.value,
                {
                    "code": "STREAM_ERROR",
                    "message": str(e),
                    "recoverable": False,
                },
            )

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ============================================================
# 버블 스트리밍 헬퍼 함수
# ============================================================


async def _stream_greeting_bubbles(session: TikitakaSessionStateV2):
    """인사 버블 스트리밍 생성기

    Args:
        session: V2 세션 상태

    Yields:
        SSE 이벤트 문자열
    """
    # 소이설 인사
    soiseol_greeting = (
        "안녕하세요~ 반가워요! 저는 소이설이에요. "
        "사주로 당신의 타고난 기운을 따뜻하게 읽어드릴게요."
    )
    async for event in _stream_single_bubble(
        bubble_id=f"b_{uuid.uuid4().hex[:8]}",
        character="SOISEOL",
        emotion="HAPPY",
        msg_type="GREETING",
        phase=PhaseCode.GREETING.value,
        content=soiseol_greeting,
        reply_to=None,
    ):
        yield event

    await asyncio.sleep(0.3)  # 버블 간 간격

    # 스텔라 인사
    stella_greeting = "...스텔라야. 별자리와 행성 배치로 운명을 분석해줄게."
    async for event in _stream_single_bubble(
        bubble_id=f"b_{uuid.uuid4().hex[:8]}",
        character="STELLA",
        emotion="NEUTRAL",
        msg_type="GREETING",
        phase=PhaseCode.GREETING.value,
        content=stella_greeting,
        reply_to=None,
    ):
        yield event


async def _stream_interpretation_bubbles(
    session_v1, session_v2: TikitakaSessionStateV2, service: TikitakaService
):
    """해석 버블 스트리밍 생성기

    Args:
        session_v1: V1 세션 (분석 결과 포함)
        session_v2: V2 세션 상태
        service: 티키타카 서비스

    Yields:
        SSE 이벤트 문자열
    """
    eastern = session_v1.eastern_result
    western = session_v1.western_result

    # 동양 컨텍스트 생성
    eastern_context = service._format_eastern_context(eastern)
    western_context = service._format_western_context(western)

    # 1. 소이설 해석 메시지 생성
    try:
        soiseol_msg = await service.llm.generate_soiseol_message("기본 성격 분석", eastern_context)
    except Exception as e:
        logger.warning("soiseol_message_fallback", error=str(e))
        soiseol_msg = f"{eastern.chart.day.gan_code.hangul} 일간이시네요~ {eastern.stats.strength}"

    soiseol_bubble_id = f"b_{uuid.uuid4().hex[:8]}"
    async for event in _stream_single_bubble(
        bubble_id=soiseol_bubble_id,
        character="SOISEOL",
        emotion="CURIOUS",
        msg_type="INTERPRETATION",
        phase=PhaseCode.DIALOGUE.value,
        content=soiseol_msg,
        reply_to=None,
    ):
        yield event

    await asyncio.sleep(0.3)

    # 2. 스텔라 해석 메시지 생성
    try:
        stella_msg = await service.llm.generate_stella_message("기본 성격 분석", western_context)
    except Exception as e:
        logger.warning("stella_message_fallback", error=str(e))
        stella_msg = f"{western.chart.sun.sign_code.label_ko} 태양이군. 분석해볼게."

    stella_bubble_id = f"b_{uuid.uuid4().hex[:8]}"
    async for event in _stream_single_bubble(
        bubble_id=stella_bubble_id,
        character="STELLA",
        emotion="THOUGHTFUL",
        msg_type="INTERPRETATION",
        phase=PhaseCode.DIALOGUE.value,
        content=stella_msg,
        reply_to=soiseol_bubble_id,  # 소이설에 응답
    ):
        yield event

    await asyncio.sleep(0.3)

    # 3. 공통점 찾기 및 합의 메시지
    consensus_point = service._find_consensus(eastern, western)

    if consensus_point:
        consensus_msg = f"스텔라도 비슷하게 봤네요! {consensus_point} 더 궁금한 운세가 있으신가요?"
        consensus_bubble_id = f"b_{uuid.uuid4().hex[:8]}"
        async for event in _stream_single_bubble(
            bubble_id=consensus_bubble_id,
            character="SOISEOL",
            emotion="EMPATHETIC",
            msg_type="CONSENSUS",
            phase=PhaseCode.DIALOGUE.value,
            content=consensus_msg,
            reply_to=stella_bubble_id,
        ):
            yield event

        # 토론 상태: 합의
        yield format_sse_event(
            SSEEventType.DEBATE_STATUS.value,
            {
                "is_consensus": True,
                "eastern_opinion": eastern.stats.strength,
                "western_opinion": western.summary,
                "consensus_point": consensus_point,
                "question": "연애운, 직장운, 금전운 중 어떤 것이 가장 궁금하신가요?",
            },
        )
    else:
        # 의견 차이 메시지
        debate_msg = (
            "소이설과는 조금 다른 관점이야. 동양과 서양이 보는 방식이 다르거든. "
            "어느 해석이 더 와닿아?"
        )
        debate_bubble_id = f"b_{uuid.uuid4().hex[:8]}"
        async for event in _stream_single_bubble(
            bubble_id=debate_bubble_id,
            character="STELLA",
            emotion="CONFIDENT",
            msg_type="DEBATE",
            phase=PhaseCode.DIALOGUE.value,
            content=debate_msg,
            reply_to=stella_bubble_id,
        ):
            yield event

        # 토론 상태: 불합의
        yield format_sse_event(
            SSEEventType.DEBATE_STATUS.value,
            {
                "is_consensus": False,
                "eastern_opinion": eastern.stats.strength,
                "western_opinion": western.summary,
                "question": "어느 해석이 더 와닿으시나요?",
            },
        )

        # UI 힌트: 선택 UI 표시
        yield format_sse_event(
            SSEEventType.UI_HINT.value,
            {
                "show_choice": True,
                "choices": [
                    {"value": 1, "character": "SOISEOL", "label": "소이설의 해석"},
                    {"value": 2, "character": "STELLA", "label": "스텔라의 해석"},
                ],
            },
        )


async def _stream_single_bubble(
    bubble_id: str,
    character: str,
    emotion: str,
    msg_type: str,
    phase: str,
    content: str,
    reply_to: str | None = None,
    chunk_size: int = 20,
):
    """단일 버블 스트리밍

    bubble_start -> bubble_chunk* -> bubble_end 시퀀스 생성

    Args:
        bubble_id: 버블 고유 ID
        character: 캐릭터 코드
        emotion: 감정 코드
        msg_type: 메시지 타입
        phase: 대화 단계
        content: 전체 메시지 내용
        reply_to: 응답 대상 버블 ID
        chunk_size: 청크 크기 (문자 단위)

    Yields:
        SSE 이벤트 문자열
    """
    now = datetime.now()

    # 1. bubble_start 이벤트
    start_data = {
        "bubble_id": bubble_id,
        "character": character,
        "emotion": emotion,
        "type": msg_type,
        "phase": phase,
    }
    if reply_to:
        start_data["reply_to"] = reply_to

    yield format_sse_event(SSEEventType.BUBBLE_START.value, start_data)

    # 2. bubble_chunk 이벤트 (청크 단위 스트리밍)
    for i in range(0, len(content), chunk_size):
        chunk = content[i : i + chunk_size]
        yield format_sse_event(
            SSEEventType.BUBBLE_CHUNK.value,
            {
                "bubble_id": bubble_id,
                "content": chunk,
            },
        )
        await asyncio.sleep(0.05)  # 스트리밍 효과

    # 3. bubble_end 이벤트
    yield format_sse_event(
        SSEEventType.BUBBLE_END.value,
        {
            "bubble_id": bubble_id,
            "content": content,
            "timestamp": now.isoformat(),
        },
    )


# ============================================================
# 세션 조회 엔드포인트
# ============================================================


@router.get(
    "/tikitaka/session/{session_id}",
    summary="티키타카 세션 상태 조회",
    description="V2 세션 상태를 조회합니다.",
    responses={
        200: {
            "description": "세션 조회 성공",
            "content": {
                "application/json": {
                    "example": {
                        "session_id": "abc12345",
                        "current_turn": 3,
                        "max_turns": 10,
                        "bonus_turns": 0,
                        "remaining_turns": 7,
                        "is_premium": False,
                        "phase": "DIALOGUE",
                        "has_eastern_result": True,
                        "has_western_result": True,
                    }
                }
            },
        },
        404: {"description": "세션을 찾을 수 없음"},
    },
)
async def get_tikitaka_session(session_id: str):
    """티키타카 세션 상태 조회"""
    if session_id not in _sessions_v2:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"세션을 찾을 수 없습니다: {session_id}",
        )

    session = _sessions_v2[session_id]
    return session.to_dict()


# ============================================================
# GPT-5-mini 멀티 버블 테스트 엔드포인트 (핫픽스)
# ============================================================


class MultiBubbleTestRequest(BaseModel):
    """멀티 버블 테스트 요청"""

    prompt: str = Field(..., description="테스트 프롬프트")
    birth_date: str | None = Field(None, description="생년월일 (YYYY-MM-DD)")


class BubbleResponse(BaseModel):
    """파싱된 버블"""

    character: str
    emotion: str
    type: str
    content: str
    reply_to: str | None = None


class MultiBubbleTestResponse(BaseModel):
    """멀티 버블 테스트 응답"""

    success: bool
    bubbles: list[BubbleResponse]
    raw_response: str
    parse_method: str  # "xml", "flexible_xml", "prefix", "single"


@router.post(
    "/test/multi-bubble",
    response_model=MultiBubbleTestResponse,
    summary="GPT-5-mini 멀티 버블 테스트",
    description="GPT-5-mini API를 사용하여 멀티 버블 XML 파싱을 테스트합니다.",
    tags=["tikitaka", "test"],
)
async def test_multi_bubble(request: MultiBubbleTestRequest):
    """GPT-5-mini 멀티 버블 파싱 테스트

    로컬 모델(yeji-8b) 대신 GPT-5-mini를 사용하여
    XML 멀티 버블 형식이 제대로 동작하는지 테스트합니다.
    """
    try:
        # 동적 import (모듈 없을 때 서버 시작 오류 방지)
        from yeji_ai.providers.openai import OpenAIConfig, OpenAIProvider

        try:
            from yeji_ai.services.parsers.bubble_parser import BubbleParser
        except ImportError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="버블 파서 모듈이 아직 설치되지 않았습니다",
            )

        # GPT-5-mini Provider 초기화
        provider = OpenAIProvider(OpenAIConfig(model="gpt-5-mini"))
        await provider.start()

        # 시스템 프롬프트
        system_prompt = """당신은 티키타카 운세 대화 시스템입니다.
응답은 반드시 다음 XML 형식으로 작성하세요:

<tikitaka>
<bubble character="SOISEOL" emotion="HAPPY" type="INTERPRETATION">
소이설(동양 운세 전문가)의 해석 메시지
</bubble>
<bubble character="STELLA" emotion="THOUGHTFUL" type="INTERPRETATION">
스텔라(서양 운세 전문가)의 해석 메시지
</bubble>
</tikitaka>

character: SOISEOL(동양), STELLA(서양), SYSTEM(시스템)
emotion: NEUTRAL, HAPPY, CURIOUS, THOUGHTFUL, SURPRISED, CONCERNED,
        CONFIDENT, PLAYFUL, MYSTERIOUS, EMPATHETIC
type: GREETING, INTERPRETATION, DEBATE, CONSENSUS, QUESTION, SUMMARY, FAREWELL"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": request.prompt},
        ]

        # LLM 호출
        response = await provider.chat(messages)
        raw_text = response.text

        # 버블 파싱
        parser = BubbleParser()
        bubbles = parser.feed(raw_text)
        parse_method = getattr(parser, "last_parse_method", "unknown")

        # Provider 정리
        await provider.stop()

        return MultiBubbleTestResponse(
            success=len(bubbles) > 0,
            bubbles=[
                BubbleResponse(
                    character=b.character,
                    emotion=b.emotion,
                    type=b.type,
                    content=b.content,
                    reply_to=b.reply_to,
                )
                for b in bubbles
            ],
            raw_response=raw_text,
            parse_method=parse_method,
        )

    except HTTPException:
        raise
    except ImportError as e:
        logger.error("Import 오류 - 모듈 확인 필요", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"모듈 임포트 실패: {e}",
        )
    except Exception as e:
        logger.exception("멀티 버블 테스트 실패", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
