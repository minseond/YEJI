"""운세 API Enum 모듈

공통/동양/서양/타로 태그 시스템 정의
"""

from yeji_ai.models.enums.prompt import PromptVersion
from yeji_ai.models.enums.common import (
    ChartType,
    CommonBadge,
    ElementCode,
    YinYangBalance,
)
from yeji_ai.models.enums.eastern import (
    CheonGanCode,
    EasternBadge,
    JiJiCode,
    PillarKey,
    TenGodCode,
    TenGodGroupCode,
)
from yeji_ai.models.enums.tarot import (
    CardOrientation,
    CardTopic,
    MajorArcana,
    MinorRank,
    MinorSuit,
    SpreadPosition,
    TarotBadge,
)
from yeji_ai.models.enums.western import (
    AspectCode,
    AspectNature,
    HouseCode,
    PlanetCode,
    WesternBadge,
    ZodiacCode,
    ZodiacElement,
    ZodiacModality,
)

__all__ = [
    # 프롬프트
    "PromptVersion",
    # 공통
    "ElementCode",
    "YinYangBalance",
    "CommonBadge",
    "ChartType",
    # 동양
    "CheonGanCode",
    "JiJiCode",
    "TenGodCode",
    "TenGodGroupCode",
    "PillarKey",
    "EasternBadge",
    # 서양
    "ZodiacCode",
    "ZodiacElement",
    "ZodiacModality",
    "PlanetCode",
    "HouseCode",
    "AspectCode",
    "AspectNature",
    "WesternBadge",
    # 타로
    "CardTopic",
    "MajorArcana",
    "MinorSuit",
    "MinorRank",
    "CardOrientation",
    "SpreadPosition",
    "TarotBadge",
]
