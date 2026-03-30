"""화투점 리딩 API 모델

요청/응답 Pydantic 스키마 정의
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# ============================================================
# 화투 위치별 의미 상수
# ============================================================

HWATU_POSITIONS = {
    1: {"name": "본인/현재", "description": "질문자의 현재 상태, 심리, 주도권"},
    2: {"name": "상대/환경", "description": "상대방의 마음, 외부 상황, 보이지 않는 변수"},
    3: {"name": "과정/관계", "description": "두 요소가 맞물리며 흘러가는 방식"},
    4: {"name": "결과/조언", "description": "가까운 미래의 결론, 행동 지침"},
}

# ============================================================
# 요청 모델
# ============================================================


class HwatuCardInput(BaseModel):
    """화투 카드 입력 (요청용)

    snake_case, camelCase 모두 허용:
      - card_code / cardCode
      - is_reversed / isReversed
    """

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "position": 1,
                "card_code": 7,
                "is_reversed": False,
            }
        },
    )

    position: int = Field(..., ge=1, le=4, description="카드 위치 (1~4)")
    card_code: int = Field(..., ge=0, le=47, alias="cardCode", description="카드 코드 (0~47)")
    is_reversed: bool = Field(False, alias="isReversed", description="역방향 여부 (화투는 항상 false)")

    @field_validator("is_reversed")
    @classmethod
    def validate_reversed(cls, v: bool) -> bool:
        """화투는 역방향이 없음"""
        if v is True:
            raise ValueError("화투 카드는 역방향이 없습니다 (is_reversed는 항상 false)")
        return v


class HwatuReadingRequest(BaseModel):
    """화투점 리딩 요청"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "category": "HWATU",
                "question": "오늘 금전운이 궁금해요",
                "cards": [
                    {"position": 1, "card_code": 7, "is_reversed": False},
                    {"position": 2, "card_code": 18, "is_reversed": False},
                    {"position": 3, "card_code": 32, "is_reversed": False},
                    {"position": 4, "card_code": 41, "is_reversed": False},
                ],
            }
        }
    )

    category: Literal["HWATU"] = "HWATU"
    question: str = Field(..., description="질문 (topic도 허용)", max_length=500)
    cards: list[HwatuCardInput] = Field(..., min_length=4, max_length=4, description="4장의 카드")

    @model_validator(mode="before")
    @classmethod
    def _map_topic_to_question(cls, data: dict) -> dict:
        """프론트엔드 호환: topic → question 매핑"""
        if isinstance(data, dict) and "topic" in data and "question" not in data:
            data["question"] = data.pop("topic")
        return data

    @field_validator("cards")
    @classmethod
    def validate_cards(cls, v: list[HwatuCardInput]) -> list[HwatuCardInput]:
        """카드 검증: position 1,2,3,4 모두 존재, card_code 중복 불가"""
        positions = {card.position for card in v}
        required_positions = {1, 2, 3, 4}

        if positions != required_positions:
            raise ValueError("position 1, 2, 3, 4가 모두 필요합니다")

        # card_code 중복 검증
        card_codes = [card.card_code for card in v]
        if len(card_codes) != len(set(card_codes)):
            raise ValueError("card_code는 중복될 수 없습니다")

        return v


# ============================================================
# 응답 모델
# ============================================================


class HwatuReadingMeta(BaseModel):
    """화투점 메타 정보"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "model": "card-v1",
                "generated_at": "2026-02-03T02:15:30Z",
            }
        }
    )

    model: str = Field(default="card-v1", description="모델 버전")
    generated_at: datetime = Field(..., description="생성 시각 (ISO 8601)")


class HwatuCardInterpretation(BaseModel):
    """화투 카드별 해석 (응답용)"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "position": 1,
                "position_label": "본인/현재",
                "card_code": 7,
                "card_name": "칠월 싸리 피",
                "card_type": "피",
                "card_month": 7,
                "keywords": ["가벼움", "유연함", "흐름"],
                "is_reversed": False,
                "interpretation": "지금은 흐름을 읽고 가볍게 접근하는 것이 유리합니다.",
            }
        }
    )

    position: int = Field(..., ge=1, le=4, description="카드 위치 (1~4)")
    position_label: str = Field(..., description="위치 한글 레이블 (본인/현재, 상대/환경 등)")
    card_code: int = Field(..., ge=0, le=47, description="카드 코드 (0~47)")
    card_name: str = Field(..., description="카드 한글 이름 (송학 광, 매 열끗 등)")
    card_type: str = Field(..., description="카드 등급 (광, 열끗, 띠, 피)")
    card_month: int = Field(..., ge=1, le=12, description="카드 월 (1~12)")
    keywords: list[str] = Field(..., description="키워드 목록 (2-5개)", min_length=2, max_length=5)
    is_reversed: bool = Field(False, description="역방향 여부 (화투는 항상 false)")
    interpretation: str = Field(..., description="카드 해석", min_length=10)


class HwatuReadingSummary(BaseModel):
    """화투점 종합 해석"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "overall_theme": "흐름을 타고 안정을 찾아가는 과정",
                "flow_analysis": "가벼움(1) → 변화(2) → 조율(3) → 안정(4)의 흐름",
                "advice": "큰 승부보다 리스크를 줄이고 흐름을 정리하는 선택이 유리합니다",
            }
        }
    )

    overall_theme: str = Field(..., description="전체 주제")
    flow_analysis: str = Field(..., description="4장 흐름 분석 (1→2→3→4)")
    advice: str = Field(..., description="실행 가능한 조언")


class HwatuLucky(BaseModel):
    """화투점 행운 정보"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "color": "붉은색",
                "number": "7",
                "direction": "남쪽",
                "timing": "오후",
            }
        }
    )

    color: str = Field(..., description="행운의 색상")
    number: str = Field(..., description="행운의 숫자")
    direction: str = Field(..., description="행운의 방향 (동/서/남/북)")
    timing: str | None = Field(None, description="행운의 시간대 (선택)")


class HwatuReadingResponse(BaseModel):
    """화투점 리딩 응답"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "meta": {
                    "model": "card-v1",
                    "generated_at": "2026-02-03T02:15:30Z",
                },
                "cards": [
                    {
                        "position": 1,
                        "position_label": "본인/현재",
                        "card_code": 7,
                        "card_name": "칠월 싸리 피",
                        "card_type": "피",
                        "card_month": 7,
                        "keywords": ["가벼움", "유연함", "흐름"],
                        "is_reversed": False,
                        "interpretation": "지금은 흐름을 읽고 가볍게 접근하는 것이 유리합니다.",
                    },
                    {
                        "position": 2,
                        "position_label": "상대/환경",
                        "card_code": 18,
                        "card_name": "팔월 공산 피",
                        "card_type": "피",
                        "card_month": 8,
                        "keywords": ["변화", "움직임", "외부"],
                        "is_reversed": False,
                        "interpretation": "상대방이나 외부 상황은 변화의 기운을 품고 있습니다.",
                    },
                    {
                        "position": 3,
                        "position_label": "과정/관계",
                        "card_code": 32,
                        "card_name": "십일월 오동 피",
                        "card_type": "피",
                        "card_month": 11,
                        "keywords": ["조율", "타협", "과정"],
                        "is_reversed": False,
                        "interpretation": "두 힘이 맞물리며 조율과 타협의 과정을 거칩니다.",
                    },
                    {
                        "position": 4,
                        "position_label": "결과/조언",
                        "card_code": 41,
                        "card_name": "십이월 비 피",
                        "card_type": "피",
                        "card_month": 12,
                        "keywords": ["안정", "정리", "결과"],
                        "is_reversed": False,
                        "interpretation": "결과적으로 안정과 정리의 시기를 맞이하게 됩니다.",
                    },
                ],
                "summary": {
                    "overall_theme": "흐름을 타고 안정을 찾아가는 과정",
                    "flow_analysis": "가벼움(1) → 변화(2) → 조율(3) → 안정(4)의 흐름",
                    "advice": "큰 승부보다 리스크를 줄이고 흐름을 정리하는 선택이 유리합니다",
                },
                "lucky": {
                    "color": "붉은색",
                    "number": "7",
                    "direction": "남쪽",
                    "timing": "오후",
                },
            }
        }
    )

    meta: HwatuReadingMeta = Field(..., description="메타 정보")
    cards: list[HwatuCardInterpretation] = Field(
        ..., min_length=4, max_length=4, description="카드별 해석 (4장)"
    )
    summary: HwatuReadingSummary = Field(..., description="종합 해석")
    lucky: HwatuLucky = Field(..., description="행운 정보")

    @field_validator("cards")
    @classmethod
    def validate_cards_positions(cls, v: list[HwatuCardInterpretation]) -> list[HwatuCardInterpretation]:
        """카드 검증: position 1,2,3,4 모두 존재"""
        positions = {card.position for card in v}
        required_positions = {1, 2, 3, 4}

        if positions != required_positions:
            raise ValueError("응답에는 position 1, 2, 3, 4가 모두 포함되어야 합니다")

        return v


# ============================================================
# 분할 API 요청/응답 모델 (병렬 호출용)
# ============================================================


class HwatuSingleCardRequest(BaseModel):
    """화투 카드 1장 해석 요청 (병렬 호출용)"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "card_code": 0,
                "position": 1,
                "question": "오늘 금전운이 궁금해요",
            }
        }
    )

    card_code: int = Field(..., ge=0, le=47, description="카드 코드 (0~47)")
    position: int = Field(..., ge=1, le=4, description="카드 위치 (1~4)")
    question: str = Field(..., description="질문", max_length=500)


class HwatuSingleCardResponse(BaseModel):
    """화투 카드 1장 해석 응답"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "position": 1,
                "position_label": "본인/현재",
                "card_code": 0,
                "card_name": "송학 광",
                "card_type": "광",
                "card_month": 1,
                "keywords": ["시작", "높은 뜻", "강력한 의지"],
                "interpretation": "당신은 현재 높은 뜻을 품고 새로운 시작을 준비하고 있습니다.",
            }
        }
    )

    position: int = Field(..., ge=1, le=4, description="카드 위치")
    position_label: str = Field(..., description="위치 한글 레이블")
    card_code: int = Field(..., ge=0, le=47, description="카드 코드")
    card_name: str = Field(..., description="카드 한글 이름")
    card_type: str = Field(..., description="카드 등급")
    card_month: int = Field(..., ge=1, le=12, description="카드 월")
    keywords: list[str] = Field(..., description="키워드 목록")
    interpretation: str = Field(..., description="카드 해석")


class HwatuSummaryRequest(BaseModel):
    """화투 종합 요약 요청 (4장 해석 후 호출)"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "question": "오늘 금전운이 궁금해요",
                "card_interpretations": [
                    {"position": 1, "card_name": "송학 광", "interpretation": "..."},
                    {"position": 2, "card_name": "매 열끗", "interpretation": "..."},
                    {"position": 3, "card_name": "벚꽃 띠", "interpretation": "..."},
                    {"position": 4, "card_name": "흑싸리 피", "interpretation": "..."},
                ],
            }
        }
    )

    question: str = Field(..., description="질문", max_length=500)
    card_interpretations: list[dict] = Field(
        ..., min_length=4, max_length=4, description="4장 카드 해석 결과"
    )


class HwatuSummaryResponse(BaseModel):
    """화투 종합 요약 응답"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "overall_theme": "높은 뜻과 밝은 기회가 만나 풍요로운 결실",
                "flow_analysis": "송학 광의 순수한 의지가 공산 광의 명확한 기회와 만나...",
                "advice": "높은 뜻을 잃지 말고 주변과 조화롭게 소통하세요.",
                "lucky": {
                    "color": "황금색",
                    "number": "8",
                    "direction": "동",
                    "timing": "오전",
                },
            }
        }
    )

    overall_theme: str = Field(..., description="전체 주제")
    flow_analysis: str = Field(..., description="4장 흐름 분석")
    advice: str = Field(..., description="실행 가능한 조언")
    lucky: HwatuLucky = Field(..., description="행운 정보")
