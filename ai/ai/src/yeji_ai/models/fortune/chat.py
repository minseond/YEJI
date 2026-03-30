"""티키타카 채팅 API 모델

소이설/스텔라 캐릭터 대화 스키마 정의
"""

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# ============================================================
# 운세 카테고리
# ============================================================



class FortuneCategory(str, Enum):
    """운세 카테고리 Enum"""

    GENERAL = "GENERAL"  # 종합운
    LOVE = "LOVE"        # 애정운
    MONEY = "MONEY"      # 재물운
    CAREER = "CAREER"    # 직장운
    HEALTH = "HEALTH"    # 건강운
    STUDY = "STUDY"      # 학업운

    @property
    def label_ko(self) -> str:
        """한글 레이블"""
        labels = {
            "GENERAL": "종합운",
            "LOVE": "애정운",
            "MONEY": "재물운",
            "CAREER": "직장운",
            "HEALTH": "건강운",
            "STUDY": "학업운",
        }
        return labels[self.value]


# 하위 호환성을 위한 Literal 타입 (API 쿼리 파라미터용)
FortuneCategoryLiteral = Literal["total", "love", "wealth", "career", "health"]
"""운세 카테고리: 종합, 연애, 금전, 직장, 건강"""


class CharacterCode(str, Enum):
    """캐릭터 코드 - 6개 캐릭터 지원"""

    # 메인 캐릭터
    SOISEOL = "SOISEOL"      # 소이설 (동양 사주) - 하오체
    STELLA = "STELLA"        # 스텔라 (서양 점성술) - 해요체

    # 서브 캐릭터
    CHEONGWOON = "CHEONGWOON"  # 청운 (신선/현자) - 하오체 (시적)
    HWARIN = "HWARIN"          # 화린 (비즈니스) - 해요체 (나른함)
    KYLE = "KYLE"              # 카일 (도박사) - 반말+존댓말 혼용
    ELARIA = "ELARIA"          # 엘라리아 (공주) - 해요체 (우아함)


class Character(BaseModel):
    """캐릭터 정보"""

    code: CharacterCode
    name_kr: str = Field(..., description="한글 이름")
    specialty: Literal["eastern", "western"] = Field(..., description="전문 분야")
    personality: str = Field(..., description="성격 설명")
    emoji: str = Field("", description="캐릭터 이모지")

    @classmethod
    def soiseol(cls) -> "Character":
        """소이설 캐릭터 생성"""
        return cls(
            code=CharacterCode.SOISEOL,
            name_kr="소이설",
            specialty="eastern",
            personality="따뜻한 온미녀",
            emoji="🌸",
        )

    @classmethod
    def stella(cls) -> "Character":
        """스텔라 캐릭터 생성"""
        return cls(
            code=CharacterCode.STELLA,
            name_kr="스텔라",
            specialty="western",
            personality="쿨한 냉미녀",
            emoji="❄️",
        )

    @classmethod
    def cheongwoon(cls) -> "Character":
        """청운 캐릭터 생성"""
        return cls(
            code=CharacterCode.CHEONGWOON,
            name_kr="청운",
            specialty="eastern",
            personality="신선/현자 (시적 하오체)",
            emoji="🌙",
        )

    @classmethod
    def hwarin(cls) -> "Character":
        """화린 캐릭터 생성"""
        return cls(
            code=CharacterCode.HWARIN,
            name_kr="화린",
            specialty="eastern",
            personality="비즈니스/정보상 (나른한 해요체)",
            emoji="🌸",
        )

    @classmethod
    def kyle(cls) -> "Character":
        """카일 캐릭터 생성"""
        return cls(
            code=CharacterCode.KYLE,
            name_kr="카일",
            specialty="western",
            personality="도박사 (반말+존댓말 혼용)",
            emoji="🎲",
        )

    @classmethod
    def elaria(cls) -> "Character":
        """엘라리아 캐릭터 생성"""
        return cls(
            code=CharacterCode.ELARIA,
            name_kr="엘라리아",
            specialty="western",
            personality="공주/외교관 (우아한 해요체)",
            emoji="👑",
        )


class MessageType(str, Enum):
    """메시지 타입"""

    GREETING = "GREETING"              # 인사
    INFO_REQUEST = "INFO_REQUEST"      # 정보 요청 (생년월일 등)
    INTERPRETATION = "INTERPRETATION"  # 해석
    DEBATE = "DEBATE"                  # 토론
    CONSENSUS = "CONSENSUS"            # 합의
    QUESTION = "QUESTION"              # 후속 질문
    CHOICE = "CHOICE"                  # 선택 요청


class ChatMessage(BaseModel):
    """채팅 메시지"""

    character: CharacterCode = Field(..., description="발화 캐릭터")
    type: MessageType = Field(..., description="메시지 타입")
    content: str = Field(..., description="메시지 내용")
    timestamp: datetime = Field(default_factory=datetime.now, description="타임스탬프")


class ChatDebateStatus(BaseModel):
    """토론 상태"""

    is_consensus: bool = Field(False, description="합의 여부")
    eastern_opinion: str | None = Field(None, description="동양 의견 요약")
    western_opinion: str | None = Field(None, description="서양 의견 요약")
    question: str | None = Field(None, description="후속 질문")


class ChoiceOption(BaseModel):
    """선택지"""

    value: Literal[1, 2] = Field(..., description="선택 값")
    character: CharacterCode = Field(..., description="선택 캐릭터")
    label: str = Field(..., description="선택지 라벨")


class ChatUIHints(BaseModel):
    """채팅 UI 힌트"""

    show_choice: bool = Field(False, description="선택형 UI 표시 여부")
    choices: list[ChoiceOption] | None = Field(None, description="선택지 목록")


class ChatRequest(BaseModel):
    """티키타카 채팅 요청"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "session_id": None,
                "message": "1990년 5월 15일 오후 2시 30분에 태어났어요",
                "birth_date": "1990-05-15",
                "birth_time": "14:30",
                "category": "GENERAL",  # 필수: 운세 서비스 진입 시 선택됨
                "eastern_fortune_id": None,
                "western_fortune_id": None,
            }
        }
    )

    session_id: str | None = Field(None, description="세션 ID (신규 시 null)")
    message: str = Field(..., description="사용자 메시지")

    # 운세 카테고리 (필수 - 운세 서비스 진입 시 선택)
    category: FortuneCategory = Field(
        ...,
        description="운세 카테고리 (GENERAL/LOVE/MONEY/CAREER/HEALTH/STUDY)",
    )

    # 사용자 정보 (첫 요청 시 필수)
    birth_date: str | None = Field(
        None, description="생년월일 (YYYY-MM-DD)", pattern=r"^\d{4}-\d{2}-\d{2}$"
    )
    birth_time: str | None = Field(
        None, description="출생시간 (HH:MM)", pattern=r"^\d{2}:\d{2}$"
    )

    # 선택 응답 (선택형 질문 후)
    choice: Literal[1, 2] | None = Field(None, description="사용자 선택 (1 또는 2)")

    # 기존 운세 재사용 (Fortune ID)
    eastern_fortune_id: str | None = Field(
        None,
        description="기존 동양 운세 ID (있으면 재사용, 없으면 신규 생성)",
    )
    western_fortune_id: str | None = Field(
        None,
        description="기존 서양 운세 ID (있으면 재사용, 없으면 신규 생성)",
    )


class FortuneReference(BaseModel):
    """사용된 운세 참조 정보"""

    eastern_id: str = Field(..., description="동양 운세 ID")
    western_id: str = Field(..., description="서양 운세 ID")
    source: Literal["created", "cached"] = Field(
        ..., description="생성 방식 (created: 신규 생성, cached: 캐시 조회)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "eastern_id": "east1234",
                "western_id": "west5678",
                "source": "created",
            }
        }
    )


class ChatResponse(BaseModel):
    """티키타카 채팅 응답"""

    session_id: str = Field(..., description="세션 ID")
    turn: int = Field(..., ge=1, description="대화 턴 번호")

    # 메시지 목록
    messages: list[ChatMessage] = Field(
        default_factory=list, description="캐릭터 메시지 목록"
    )

    # 토론 상태
    debate_status: ChatDebateStatus = Field(..., description="토론 상태")

    # UI 힌트
    ui_hints: ChatUIHints = Field(..., description="UI 힌트")

    # 운세 참조 정보 (첫 턴에만 포함)
    fortune_ref: FortuneReference | None = Field(
        None,
        description="사용된 운세 참조 (운세 분석 완료 시 포함)",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "session_id": "abc123",
                "turn": 1,
                "messages": [
                    {
                        "character": "SOISEOL",
                        "type": "INTERPRETATION",
                        "content": "병화 일간이시네요~ 밝고 열정적인 성격이에요.",
                        "timestamp": "2024-01-27T15:30:00",
                    },
                    {
                        "character": "STELLA",
                        "type": "INTERPRETATION",
                        "content": "양자리 태양이군. 리더십과 추진력이 강해.",
                        "timestamp": "2024-01-27T15:30:05",
                    },
                ],
                "debate_status": {
                    "is_consensus": True,
                    "eastern_opinion": "열정적이고 행동력이 강함",
                    "western_opinion": "리더십과 추진력이 뛰어남",
                    "question": "연애운이 궁금하신가요?",
                },
                "ui_hints": {
                    "show_choice": False,
                    "choices": None,
                },
                "fortune_ref": {
                    "eastern_id": "east1234",
                    "western_id": "west5678",
                    "source": "created",
                },
            }
        }
    )


# ============================================================
# 카테고리별 그리팅 API 모델
# ============================================================


class CategoryGreetingRequest(BaseModel):
    """카테고리별 그리팅 요청

    Java 백엔드 호환을 위해 camelCase alias 지원
    - snake_case (Python): birth_date, eastern_fortune_data
    - camelCase (Java): birthDate, easternFortuneData
    """

    birth_date: str = Field(
        ...,
        alias="birthDate",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="생년월일 (YYYY-MM-DD)"
    )
    birth_time: str | None = Field(
        None,
        alias="birthTime",
        pattern=r"^\d{2}:\d{2}$",
        description="출생시간 (HH:MM)"
    )
    birth_place: str | None = Field(None, alias="birthPlace", description="출생장소")
    latitude: float | None = Field(None, description="위도")
    longitude: float | None = Field(None, description="경도")

    category: FortuneCategory = Field(
        ...,
        description="운세 카테고리 (GENERAL/LOVE/MONEY/CAREER/HEALTH/STUDY)",
    )

    char1_code: str = Field(default="SOISEOL", alias="char1Code", description="첫 번째 캐릭터 코드")
    char2_code: str = Field(default="STELLA", alias="char2Code", description="두 번째 캐릭터 코드")

    eastern_fortune_id: str | None = Field(
        None, alias="easternFortuneId", description="기존 동양 운세 ID (재사용)"
    )
    western_fortune_id: str | None = Field(
        None, alias="westernFortuneId", description="기존 서양 운세 ID (재사용)"
    )

    # 분석 결과 직접 전달 (ID 대신 객체로 전달 시 사용)
    eastern_fortune_data: dict | None = Field(
        None,
        alias="easternFortuneData",
        description="동양 사주 분석 결과 객체 (POST /fortune/eastern 응답 형식)"
    )
    western_fortune_data: dict | None = Field(
        None,
        alias="westernFortuneData",
        description="서양 점성술 분석 결과 객체 (POST /fortune/western 응답 형식)"
    )

    model_config = ConfigDict(
        populate_by_name=True,  # alias와 원래 필드명 둘 다 허용
        json_schema_extra={
            "example": {
                "birthDate": "1990-05-15",
                "birthTime": "14:30",
                "category": "LOVE",
                "char1Code": "SOISEOL",
                "char2Code": "STELLA",
                "easternFortuneData": None,
                "westernFortuneData": None,
            }
        }
    )


class CategoryGreetingResponse(BaseModel):
    """카테고리별 그리팅 응답"""

    session_id: str = Field(..., description="세션 ID")
    category: FortuneCategory = Field(..., description="운세 카테고리")
    messages: list[ChatMessage] = Field(..., description="그리팅 메시지 목록")
    eastern_fortune_id: str = Field(..., description="동양 운세 ID")
    western_fortune_id: str = Field(..., description="서양 운세 ID")
    eastern_summary: str = Field(..., description="동양 운세 요약")
    western_summary: str = Field(..., description="서양 운세 요약")
    fortune_source: str = Field(
        ...,
        description=(
            "운세 데이터 출처 (provided: 직접 전달, cached: ID로 캐시 조회, "
            "created: 실시간 분석)"
        )
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "session_id": "abc123",
                "category": "LOVE",
                "messages": [
                    {
                        "character": "SOISEOL",
                        "type": "GREETING",
                        "content": "병화 일간이시오. 비견이 강하니 독립적인 연애를 선호하시겠소.",
                        "timestamp": "2024-01-27T15:30:00",
                    },
                    {
                        "character": "STELLA",
                        "type": "GREETING",
                        "content": "황소자리 태양이네요! 안정된 사랑을 추구하는 스타일이에요.",
                        "timestamp": "2024-01-27T15:30:05",
                    },
                ],
                "eastern_fortune_id": "e12345",
                "western_fortune_id": "w67890",
                "eastern_summary": "병화 일간 (화)",
                "western_summary": "황소자리 태양",
                "fortune_source": "provided",
            }
        }
    )


# ============================================================
# 운세 요약 모델 (분리형)
# ============================================================


class FortuneSummary(BaseModel):
    """운세 요약 데이터

    캐릭터별 운세 요약을 담는 모델입니다.
    프론트엔드에서 바로 렌더링 가능한 형태로 제공합니다.
    """

    character: Literal["SOISEOL", "STELLA"] = Field(..., description="캐릭터 코드")
    score: int = Field(..., ge=0, le=100, description="운세 점수 (0-100)")
    one_line: str = Field(..., min_length=10, max_length=100, description="한 줄 요약")
    keywords: list[str] = Field(..., min_length=2, max_length=5, description="키워드 목록")
    detail: str = Field(..., min_length=50, max_length=500, description="상세 내용")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "character": "SOISEOL",
                "score": 85,
                "one_line": "목(木) 기운이 강해 재물 운이 상승하는 시기예요",
                "keywords": ["재물운 상승", "투자 적기", "절약 필요"],
                "detail": (
                    "일간(甲)을 중심으로 월지(卯)가 같은 기둥이 반복되어 "
                    "'목(木) 기운'이 강조됩니다."
                ),
            }
        }
    )


class FortuneSummaryResponse(BaseModel):
    """채팅 세션 운세 요약 응답

    GET /api/v1/fortune/chat/summary/{session_id}?type=eastern|western
    """

    session_id: str = Field(..., description="세션 ID")
    category: FortuneCategoryLiteral = Field(..., description="운세 카테고리")
    fortune_type: Literal["eastern", "western"] = Field(..., description="운세 타입")
    fortune: FortuneSummary = Field(..., description="운세 요약 데이터")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "session_id": "abc12345",
                "category": "wealth",
                "fortune_type": "eastern",
                "fortune": {
                    "character": "SOISEOL",
                    "score": 85,
                    "one_line": "목(木) 기운이 강해 재물 운이 상승하는 시기예요",
                    "keywords": ["재물운 상승", "투자 적기", "절약 필요"],
                    "detail": (
                        "일간(甲)을 중심으로 월지(卯)가 같은 기둥이 반복되어 "
                        "'목(木) 기운'이 강조됩니다."
                    ),
                },
            }
        }
    )
