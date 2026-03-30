"""티키타카 Turn 응답 스키마

Turn 기반 동/서양 티키타카 운세 채팅 JSON 응답 스키마 정의

fortune_chat_turn_contract.md 스펙 준수
"""

from datetime import datetime
from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, Field

# ============================================================
# Enum 정의
# ============================================================


class Speaker(str, Enum):
    """발화자 (캐릭터)"""

    EAST = "EAST"  # 소이설 (동양 사주학자)
    WEST = "WEST"  # 스텔라 (서양 점성술사)


class EmotionCode(str, Enum):
    """감정 코드 (12종)"""

    NEUTRAL = "NEUTRAL"  # 중립
    WARM = "WARM"  # 따뜻함
    EXCITED = "EXCITED"  # 흥분
    THOUGHTFUL = "THOUGHTFUL"  # 사려깊음
    ENCOURAGING = "ENCOURAGING"  # 격려
    PLAYFUL = "PLAYFUL"  # 장난스러움
    MYSTERIOUS = "MYSTERIOUS"  # 신비로움
    SURPRISED = "SURPRISED"  # 놀람
    CONCERNED = "CONCERNED"  # 걱정
    CONFIDENT = "CONFIDENT"  # 자신감
    GENTLE = "GENTLE"  # 부드러움
    CURIOUS = "CURIOUS"  # 호기심


class FortuneCategory(str, Enum):
    """운세 카테고리"""

    TOTAL = "total"  # 종합운
    LOVE = "love"  # 연애운
    WEALTH = "wealth"  # 금전운
    CAREER = "career"  # 직장운
    HEALTH = "health"  # 건강운


class InputType(str, Enum):
    """입력 타입"""

    TEXT = "text"
    CHOICE = "choice"
    DATE = "date"
    DATETIME = "datetime"


# ============================================================
# Emotion 모델
# ============================================================


class Emotion(BaseModel):
    """감정 정보"""

    code: EmotionCode = Field(..., description="감정 코드")
    intensity: Annotated[float, Field(ge=0.0, le=1.0, description="감정 강도 (0.0~1.0)")]


# ============================================================
# Bubble 모델
# ============================================================


class Bubble(BaseModel):
    """캐릭터 발화 버블"""

    bubble_id: str = Field(..., description="버블 고유 ID (예: b001)")
    speaker: Speaker = Field(..., description="발화 캐릭터")
    text: str = Field(..., min_length=1, max_length=500, description="발화 내용")
    emotion: Emotion = Field(..., description="감정 정보")
    user_input_ref: str | None = Field(None, description="이전 턴 프롬프트 ID 참조")
    timestamp: str = Field(..., description="ISO 8601 타임스탬프")


# ============================================================
# TurnEnd 관련 모델
# ============================================================


class ChoiceOption(BaseModel):
    """선택지 옵션"""

    value: str = Field(..., description="선택 값")
    label: str = Field(..., description="선택지 라벨")


class InputValidation(BaseModel):
    """입력 검증 규칙"""

    required: bool = Field(default=False, description="필수 여부")
    pattern: str | None = Field(None, description="정규식 패턴")
    min_length: int | None = Field(None, description="최소 길이")
    max_length: int | None = Field(None, description="최대 길이")


class InputSchema(BaseModel):
    """입력 스키마"""

    type: InputType = Field(..., description="입력 타입")
    placeholder: str | None = Field(None, description="플레이스홀더")
    options: list[ChoiceOption] | None = Field(None, description="선택지 목록 (choice 타입)")
    validation: InputValidation | None = Field(None, description="검증 규칙")


class UserPrompt(BaseModel):
    """사용자 입력 프롬프트"""

    prompt_id: str = Field(..., description="프롬프트 고유 ID")
    text: str = Field(..., description="안내 문구")
    input_schema: InputSchema = Field(..., description="입력 스키마")


class TurnEndAwaitUserInput(BaseModel):
    """턴 종료: 사용자 입력 대기"""

    type: Literal["await_user_input"] = "await_user_input"
    user_prompt: UserPrompt = Field(..., description="사용자 프롬프트")


class SummaryItem(BaseModel):
    """세션 요약 항목"""

    speaker: Speaker = Field(..., description="요약 발화자")
    key_point: str = Field(..., description="핵심 포인트")


class UpgradeHook(BaseModel):
    """업그레이드 유도"""

    enabled: bool = Field(..., description="활성화 여부")
    message: str | None = Field(None, description="유도 메시지")
    cta_label: str | None = Field(None, description="CTA 버튼 라벨")
    cta_action: str | None = Field(None, description="CTA 액션")


class Closure(BaseModel):
    """세션 종료 정보"""

    summary: list[SummaryItem] = Field(..., min_length=1, description="세션 요약")
    next_steps: list[str] = Field(..., description="다음 단계 제안")
    upgrade_hook: UpgradeHook = Field(..., description="업그레이드 유도")
    end_marker: Literal["END_SESSION"] = Field(
        default="END_SESSION", description="종료 마커"
    )


class TurnEndCompleted(BaseModel):
    """턴 종료: 세션 완료"""

    type: Literal["completed"] = "completed"
    closure: Closure = Field(..., description="종료 정보")


# Union 타입
TurnEnd = TurnEndAwaitUserInput | TurnEndCompleted


# ============================================================
# Meta 모델
# ============================================================


class Meta(BaseModel):
    """턴/세션 메타 정보"""

    current_turn: int = Field(..., ge=1, description="현재 턴 (1~)")
    base_turns: int = Field(default=3, ge=1, description="기본 제공 턴 수")
    max_turns: int = Field(default=10, ge=1, description="최대 가능 턴 수")
    is_premium: bool = Field(default=False, description="프리미엄 여부")
    category: FortuneCategory = Field(
        default=FortuneCategory.TOTAL, description="운세 카테고리"
    )


# ============================================================
# TurnRequest / TurnResponse 모델
# ============================================================


class UserInput(BaseModel):
    """사용자 입력 (Turn 2+)"""

    prompt_id: str = Field(..., description="응답 대상 프롬프트 ID")
    value: str = Field(..., description="사용자 입력 값")


class BirthInfo(BaseModel):
    """출생 정보 (Turn 1)"""

    birth_date: str = Field(..., description="생년월일 (YYYY-MM-DD)")
    birth_time: str | None = Field(None, description="출생시간 (HH:MM)")
    birth_place: str | None = Field(None, description="출생지")


class TurnRequest(BaseModel):
    """턴 요청"""

    session_id: str | None = Field(None, description="세션 ID (신규는 null)")
    turn_id: int | None = Field(None, description="응답할 턴 ID (신규는 null)")
    user_input: UserInput | None = Field(None, description="사용자 입력 (Turn 2+)")
    birth_info: BirthInfo | None = Field(None, description="출생 정보 (Turn 1)")


class TurnResponse(BaseModel):
    """턴 응답"""

    session_id: str = Field(..., description="세션 고유 ID")
    turn_id: int = Field(..., ge=1, description="턴 고유 ID")
    bubbles: list[Bubble] = Field(..., min_length=1, description="버블 목록")
    turn_end: TurnEnd = Field(..., description="턴 종료 정보")
    meta: Meta = Field(..., description="메타 정보")


# ============================================================
# 유틸리티 함수
# ============================================================


def create_bubble(
    bubble_id: str,
    speaker: Speaker,
    text: str,
    emotion_code: EmotionCode,
    emotion_intensity: float,
    user_input_ref: str | None = None,
    timestamp: datetime | None = None,
) -> Bubble:
    """Bubble 객체 생성 헬퍼"""
    if timestamp is None:
        timestamp = datetime.utcnow()

    return Bubble(
        bubble_id=bubble_id,
        speaker=speaker,
        text=text,
        emotion=Emotion(code=emotion_code, intensity=emotion_intensity),
        user_input_ref=user_input_ref,
        timestamp=timestamp.isoformat() + "Z",
    )


def create_await_user_input(
    prompt_id: str,
    text: str,
    input_type: InputType = InputType.TEXT,
    placeholder: str | None = None,
    options: list[ChoiceOption] | None = None,
    required: bool = False,
    max_length: int = 200,
) -> TurnEndAwaitUserInput:
    """await_user_input TurnEnd 생성 헬퍼"""
    return TurnEndAwaitUserInput(
        user_prompt=UserPrompt(
            prompt_id=prompt_id,
            text=text,
            input_schema=InputSchema(
                type=input_type,
                placeholder=placeholder,
                options=options,
                validation=InputValidation(required=required, max_length=max_length),
            ),
        )
    )


def create_completed(
    summary: list[SummaryItem],
    next_steps: list[str],
    is_premium: bool,
    upgrade_message: str | None = None,
) -> TurnEndCompleted:
    """completed TurnEnd 생성 헬퍼"""
    # 프리미엄 사용자면 upgrade_hook 비활성화
    if is_premium:
        upgrade_hook = UpgradeHook(enabled=False)
    else:
        upgrade_hook = UpgradeHook(
            enabled=True,
            message=upgrade_message or "프리미엄으로 업그레이드하면 무제한 상담이 가능해요!",
            cta_label="프리미엄 시작하기",
            cta_action="upgrade_premium",
        )

    return TurnEndCompleted(
        closure=Closure(
            summary=summary,
            next_steps=next_steps,
            upgrade_hook=upgrade_hook,
        )
    )
