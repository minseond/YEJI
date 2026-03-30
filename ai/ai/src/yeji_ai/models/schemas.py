"""API 요청/응답 스키마 (Pydantic 모델)"""

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field

# ============================================================
# Enum 정의
# ============================================================


class Gender(str, Enum):
    """성별"""

    MALE = "M"
    FEMALE = "F"


class Character(str, Enum):
    """캐릭터 (티키타카)"""

    DOSA = "도사"  # 동양 관점
    ASTROLOGER = "점성술사"  # 서양 관점
    SYSTEM = "시스템"
    USER = "사용자"


class Element(str, Enum):
    """오행"""

    WOOD = "목"
    FIRE = "화"
    EARTH = "토"
    METAL = "금"
    WATER = "수"


class FortuneCategory(str, Enum):
    """운세 대분류"""

    LOVE = "연애운"
    CAREER = "직장운"
    MONEY = "금전운"
    HEALTH = "건강운"
    STUDY = "학업운"
    GENERAL = "종합운"


class SessionPhase(str, Enum):
    """세션 단계"""

    ANALYZING = "analyzing"
    RESULT_STREAMING = "result_streaming"
    DISCUSSION = "discussion"
    USER_QUESTION = "user_question"
    CHAT = "chat"
    COMPLETE = "complete"


class MessageType(str, Enum):
    """메시지 타입"""

    TEXT = "text"
    QUESTION = "question"
    DISCUSSION = "discussion"
    SUMMARY = "summary"
    VISUALIZATION = "visualization"
    CHAT = "chat"


# ============================================================
# 공통 모델
# ============================================================


class BaseResponse(BaseModel):
    """기본 응답 형식"""

    success: bool = True
    message: str = ""
    data: Any | None = None


class SajuProfile(BaseModel):
    """사주 프로필 (가입 시 수집)"""

    name: str = Field(..., description="이름")
    gender: Gender = Field(..., description="성별")
    birth_date: str = Field(..., description="생년월일 (YYYY-MM-DD)")
    birth_time: str | None = Field(None, description="출생시간 (HH:MM)")
    birth_place: str | None = Field(None, description="출생지역")


class QuestionOption(BaseModel):
    """질문 선택지"""

    id: str
    label: str
    value: str


class ChatMessage(BaseModel):
    """채팅 메시지"""

    id: str = Field(default_factory=lambda: str(__import__("uuid").uuid4()))
    character: Character
    message_type: MessageType = MessageType.TEXT
    content: str
    options: list[QuestionOption] | None = None
    timestamp: datetime = Field(default_factory=datetime.now)


class SessionState(BaseModel):
    """세션 상태"""

    session_id: str
    user_id: int
    phase: SessionPhase = SessionPhase.ANALYZING
    category: FortuneCategory | None = None
    sub_category: str | None = None
    turn_count: int = 0
    question_count: int = 0
    user_answers: list[str] = Field(default_factory=list)


# ============================================================
# 요청 스키마
# ============================================================


class AnalyzeRequest(BaseModel):
    """사주 분석 요청"""

    user_id: int = Field(..., description="사용자 ID")
    saju_profile: SajuProfile = Field(..., description="사주 프로필")
    category: FortuneCategory = Field(..., description="운세 대분류")
    sub_category: str = Field(..., description="운세 소분류")


class AnswerRequest(BaseModel):
    """중간 질문 응답"""

    session_id: str = Field(..., description="세션 ID")
    question_id: str = Field(..., description="질문 ID")
    value: str = Field(..., description="선택한 값")
    input_type: Literal["select", "text"] = "select"


class ChatRequest(BaseModel):
    """추가 채팅 요청"""

    session_id: str = Field(..., description="세션 ID")
    message: str = Field(..., description="사용자 메시지")


# ============================================================
# SSE 이벤트 스키마
# ============================================================


class SSEEvent(BaseModel):
    """SSE 이벤트"""

    event: str
    data: dict[str, Any]

    def to_sse(self) -> str:
        """SSE 포맷 문자열 반환"""
        import json

        return f"event: {self.event}\ndata: {json.dumps(self.data, ensure_ascii=False)}\n\n"
