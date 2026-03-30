"""타로 카드 리딩 API 모델

요청/응답 Pydantic 스키마 정의
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from yeji_ai.models.enums import (
    CardOrientation,
    CardTopic,
    CommonBadge,
    MajorArcana,
    MinorRank,
    MinorSuit,
    SpreadPosition,
    TarotBadge,
)

# ============================================================
# 요청 모델
# ============================================================


class TarotCardInput(BaseModel):
    """타로 카드 입력 (요청용)"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "major": "FOOL",
                "suit": None,
                "rank": None,
                "orientation": "UPRIGHT",
            }
        }
    )

    major: MajorArcana | None = Field(None, description="메이저 아르카나")
    suit: MinorSuit | None = Field(None, description="마이너 수트")
    rank: MinorRank | None = Field(None, description="마이너 랭크")
    orientation: CardOrientation = Field(CardOrientation.UPRIGHT, description="카드 방향")

    @property
    def card_name(self) -> str:
        """카드 영문 이름"""
        if self.major:
            return self.major.label_en
        elif self.suit and self.rank:
            return f"{self.rank.label_ko} of {self.suit.value}"
        return "Unknown Card"

    @property
    def card_name_ko(self) -> str:
        """카드 한글 이름"""
        if self.major:
            return self.major.label_ko
        elif self.suit and self.rank:
            return f"{self.suit.label_ko} {self.rank.label_ko}"
        return "알 수 없는 카드"

    @model_validator(mode="after")
    def validate_card(self) -> "TarotCardInput":
        """카드 검증: 메이저 또는 마이너 중 하나만 존재"""
        has_major = self.major is not None
        has_minor = self.suit is not None or self.rank is not None

        if has_major and has_minor:
            raise ValueError("메이저와 마이너 카드를 동시에 지정할 수 없습니다")

        if not has_major and not has_minor:
            raise ValueError("메이저 또는 마이너 카드 중 하나를 지정해야 합니다")

        # 마이너 카드는 suit과 rank 둘 다 필요
        if has_minor:
            if self.suit is None or self.rank is None:
                raise ValueError("마이너 카드는 suit과 rank를 모두 지정해야 합니다")

        return self


class SpreadCardInput(BaseModel):
    """스프레드 내 카드 위치"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "position": "PAST",
                "card": {
                    "major": "FOOL",
                    "suit": None,
                    "rank": None,
                    "orientation": "UPRIGHT",
                },
            }
        }
    )

    position: SpreadPosition = Field(..., description="스프레드 위치")
    card: TarotCardInput = Field(..., description="카드")


class TarotReadingRequest(BaseModel):
    """타로 리딩 요청"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "question": "LOVE",
                "cards": [
                    {
                        "position": "PAST",
                        "card": {
                            "major": "HANGED_MAN",
                            "orientation": "UPRIGHT",
                        },
                    },
                    {
                        "position": "PRESENT",
                        "card": {
                            "suit": "CUPS",
                            "rank": "THREE",
                            "orientation": "REVERSED",
                        },
                    },
                    {
                        "position": "FUTURE",
                        "card": {
                            "suit": "WANDS",
                            "rank": "KING",
                            "orientation": "UPRIGHT",
                        },
                    },
                ],
            }
        }
    )

    question: CardTopic = Field(..., description="질문 카테고리 (MONEY/LOVE/CAREER/HEALTH/STUDY)")
    cards: list[SpreadCardInput] = Field(..., description="3장의 카드", min_length=3, max_length=3)

    @model_validator(mode="before")
    @classmethod
    def _map_topic_to_question(cls, data: dict) -> dict:
        """프론트엔드 호환: topic → question 매핑"""
        if isinstance(data, dict) and "topic" in data and "question" not in data:
            data["question"] = data.pop("topic")
        return data

    @field_validator("cards")
    @classmethod
    def validate_cards(cls, v: list[SpreadCardInput]) -> list[SpreadCardInput]:
        """카드 검증: PAST, PRESENT, FUTURE 모두 존재"""
        positions = {card.position for card in v}
        required = {SpreadPosition.PAST, SpreadPosition.PRESENT, SpreadPosition.FUTURE}

        if positions != required:
            raise ValueError("PAST, PRESENT, FUTURE 위치가 모두 필요합니다")

        return v


# ============================================================
# 응답 모델
# ============================================================


class CardInterpretation(BaseModel):
    """카드 해석 (응답용)"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "position": "PAST",
                "position_label": "과거",
                "card_code": "FOOL",
                "card_name": "바보",
                "orientation": "UPRIGHT",
                "orientation_label": "정방향",
                "keywords": ["새로운 시작", "순수함", "모험"],
                "interpretation": "과거에는 새로운 시작과 순수한 마음으로 모험을 시작했습니다.",
            }
        }
    )

    position: SpreadPosition = Field(..., description="스프레드 위치")
    position_label: str = Field(..., description="위치 한글 레이블")
    card_code: str = Field(..., description="카드 코드 (FOOL, CUPS_ACE 등)")
    card_name: str = Field(..., description="카드 한글 이름")
    orientation: CardOrientation = Field(..., description="카드 방향")
    orientation_label: str = Field(..., description="방향 한글 레이블")
    keywords: list[str] = Field(..., description="키워드 목록 (2-5개)", min_length=2, max_length=5)
    interpretation: str = Field(..., description="해석 내용")


class TarotReadingSummary(BaseModel):
    """타로 리딩 종합 해석"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "overall_theme": "새로운 사랑의 시작과 성장",
                "past_to_present": "과거의 순수한 마음이 현재의 감정으로 발전했습니다.",
                "present_to_future": "현재의 감정이 미래에 아름다운 관계로 이어질 것입니다.",
                "advice": "마음을 열고 솔직하게 다가가세요.",
            }
        }
    )

    overall_theme: str = Field(..., description="전체 주제")
    past_to_present: str = Field(..., description="과거→현재 흐름 해석")
    present_to_future: str = Field(..., description="현재→미래 흐름 해석")
    advice: str = Field(..., description="조언")


class TarotLucky(BaseModel):
    """타로 행운 정보"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "color": "흰색",
                "number": "0",
                "element": "공기",
                "timing": "새벽",
            }
        }
    )

    color: str = Field(..., description="행운의 색상")
    number: str = Field(..., description="행운의 숫자")
    element: str = Field(..., description="행운의 원소")
    timing: str | None = Field(None, description="행운의 시간대 (선택)")


class TarotReadingResponse(BaseModel):
    """타로 리딩 응답"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "category": "tarot",
                "spread_type": "THREE_CARD",
                "question": "LOVE",
                "cards": [
                    {
                        "position": "PAST",
                        "position_label": "과거",
                        "card_code": "FOOL",
                        "card_name": "바보",
                        "orientation": "UPRIGHT",
                        "orientation_label": "정방향",
                        "keywords": ["새로운 시작", "순수함", "모험"],
                        "interpretation": "과거에는 새로운 시작과 순수한 마음으로...",
                    },
                ],
                "summary": {
                    "overall_theme": "새로운 사랑의 시작과 성장",
                    "past_to_present": "과거의 순수한 마음이 현재의 감정으로...",
                    "present_to_future": "현재의 감정이 미래에 아름다운 관계로...",
                    "advice": "마음을 열고 솔직하게 다가가세요.",
                },
                "lucky": {
                    "color": "흰색",
                    "number": "0",
                    "element": "공기",
                    "timing": "새벽",
                },
            }
        }
    )

    category: Literal["tarot"] = "tarot"
    spread_type: Literal["THREE_CARD"] = "THREE_CARD"
    question: CardTopic | None = Field(None, description="질문 카테고리 (MONEY/LOVE/CAREER/HEALTH/STUDY)")
    cards: list[CardInterpretation] = Field(..., description="카드 해석 목록 (3장)")
    summary: TarotReadingSummary = Field(..., description="종합 해석")
    lucky: TarotLucky = Field(..., description="행운 정보")

    # UI 힌트 (선택)
    badges: list[TarotBadge | CommonBadge] = Field(
        default_factory=list, description="표시할 배지 목록"
    )
