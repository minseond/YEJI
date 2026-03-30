"""티키타카 대화 생성 스키마

LLM이 생성하는 대화 출력 스키마 정의
코드가 JSON 구조를 조립할 때 사용
"""

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

from yeji_ai.models.fortune.turn import EmotionCode

# ============================================================
# 대화 모드
# ============================================================


class DialogueMode(str, Enum):
    """대화 모드"""

    BATTLE = "battle"  # 대결 모드 (70~80%)
    CONSENSUS = "consensus"  # 합의 모드 (20~30%)


# ============================================================
# LLM 출력 스키마
# ============================================================


class DialogueLine(BaseModel):
    """단일 대화 라인 (LLM이 생성)"""

    speaker: Literal["EAST", "WEST"] = Field(..., description="발화자")
    text: str = Field(..., min_length=10, max_length=300, description="발화 내용")
    emotion_code: EmotionCode = Field(..., description="감정 코드")
    emotion_intensity: float = Field(
        ..., ge=0.0, le=1.0, description="감정 강도 (0.0~1.0)"
    )


class DialogueOutput(BaseModel):
    """LLM 대화 생성 출력

    LLM이 JSON으로 생성하는 대화 데이터.
    코드가 이 데이터를 받아서 TurnResponse를 조립함.
    """

    lines: list[DialogueLine] = Field(
        ..., min_length=2, max_length=4, description="대화 라인 목록"
    )
    user_prompt_text: str = Field(
        ..., min_length=10, max_length=100, description="사용자에게 보여줄 프롬프트"
    )


# ============================================================
# 컨텍스트 모델
# ============================================================


class EasternContext(BaseModel):
    """동양 사주 컨텍스트 (LLM 프롬프트용)"""

    day_master: str = Field(..., description="일간 (예: 병화(丙火))")
    day_element: str = Field(..., description="일간 오행 (예: 火)")
    pillars: str = Field(..., description="사주 기둥 요약")
    five_elements: str = Field(..., description="오행 분포 요약")
    yin_yang: str = Field(..., description="음양 분포 요약")
    strength: str = Field(..., description="강점")
    weakness: str = Field(..., description="약점")


class WesternContext(BaseModel):
    """서양 점성술 컨텍스트 (LLM 프롬프트용)"""

    sun_sign: str = Field(..., description="태양 별자리")
    dominant_element: str = Field(..., description="우세 원소")
    overview: str = Field(..., description="운세 요약")


# ============================================================
# 세션 상태
# ============================================================


class TikitakaSessionState(BaseModel):
    """티키타카 세션 상태"""

    session_id: str = Field(..., description="세션 ID")
    current_turn: int = Field(default=0, ge=0, description="현재 턴 번호")
    base_turns: int = Field(default=3, ge=1, description="기본 턴 수")
    max_turns: int = Field(default=10, ge=1, description="최대 턴 수")
    is_premium: bool = Field(default=False, description="프리미엄 여부")
    category: str = Field(default="total", description="운세 카테고리")

    # 이전 프롬프트 ID (다음 턴에서 user_input_ref로 사용)
    last_prompt_id: str | None = Field(None, description="마지막 프롬프트 ID")

    # 컨텍스트 캐시
    eastern_context: EasternContext | None = Field(None, description="동양 컨텍스트")
    western_context: WesternContext | None = Field(None, description="서양 컨텍스트")

    def get_next_turn_id(self) -> int:
        """다음 턴 ID 반환"""
        return self.current_turn + 1

    def should_complete(self) -> bool:
        """세션 완료 여부 판단"""
        # 기본 턴 수 도달 시 완료 (프리미엄은 max_turns까지)
        if self.is_premium:
            return self.current_turn >= self.max_turns
        return self.current_turn >= self.base_turns

    def get_bubble_id(self, idx: int) -> str:
        """버블 ID 생성"""
        return f"b{self.get_next_turn_id():03d}_{idx}"

    def get_prompt_id(self) -> str:
        """프롬프트 ID 생성"""
        return f"p{self.get_next_turn_id():03d}"
