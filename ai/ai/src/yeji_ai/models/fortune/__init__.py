"""운세 API 모델 모듈

동양/서양/타로/채팅 API 요청/응답 스키마
"""

from yeji_ai.models.fortune.chat import (
    Character,
    CharacterCode,
    ChatDebateStatus,
    ChatMessage,
    ChatRequest,
    ChatResponse,
    ChatUIHints,
    ChoiceOption,
    MessageType,
)
from yeji_ai.models.fortune.eastern import (
    EasternFortuneRequest,
    EasternFortuneResponse,
    EasternHighlight,
    EasternLucky,
    EasternStats,
    EasternUIHints,
    FiveElementStat,
    Pillar,
    PillarChart,
    TenGodStat,
    YinYangStat,
)
from yeji_ai.models.fortune.tarot import (
    CardInterpretation,
    SpreadCardInput,
    TarotCardInput,
    TarotLucky,
    TarotReadingRequest,
    TarotReadingResponse,
    TarotReadingSummary,
)
from yeji_ai.models.fortune.western import (
    AspectInfo,
    ElementStat,
    HouseInfo,
    ModalityStat,
    PlanetPlacement,
    WesternAspects,
    WesternChart,
    WesternElements,
    WesternFortuneRequest,
    WesternFortuneResponse,
    WesternHighlight,
    WesternLucky,
    WesternModality,
    WesternStats,
    WesternUIHints,
)

__all__ = [
    # 동양
    "Pillar",
    "PillarChart",
    "FiveElementStat",
    "YinYangStat",
    "TenGodStat",
    "EasternStats",
    "EasternHighlight",
    "EasternUIHints",
    "EasternLucky",
    "EasternFortuneRequest",
    "EasternFortuneResponse",
    # 서양
    "PlanetPlacement",
    "HouseInfo",
    "WesternChart",
    "ElementStat",
    "WesternElements",
    "ModalityStat",
    "WesternModality",
    "AspectInfo",
    "WesternAspects",
    "WesternStats",
    "WesternHighlight",
    "WesternUIHints",
    "WesternLucky",
    "WesternFortuneRequest",
    "WesternFortuneResponse",
    # 타로
    "TarotCardInput",
    "SpreadCardInput",
    "TarotReadingRequest",
    "CardInterpretation",
    "TarotReadingSummary",
    "TarotLucky",
    "TarotReadingResponse",
    # 채팅
    "CharacterCode",
    "Character",
    "MessageType",
    "ChatMessage",
    "ChatDebateStatus",
    "ChoiceOption",
    "ChatUIHints",
    "ChatRequest",
    "ChatResponse",
]
