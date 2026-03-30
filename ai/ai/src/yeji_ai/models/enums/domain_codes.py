"""도메인 코드 상수 정의

프론트엔드 확정 스키마 (domainMapping.ts)와 일치하도록 정의.
LLM은 이 코드들만 사용해야 합니다.
"""

from enum import Enum
from typing import Literal

# ============================================================
# 동양 사주 (Eastern) 도메인 코드
# ============================================================


class EastElementCode(str, Enum):
    """동양 오행 코드"""

    WOOD = "WOOD"
    FIRE = "FIRE"
    EARTH = "EARTH"
    METAL = "METAL"
    WATER = "WATER"


# 오행 한글 레이블 매핑
EAST_ELEMENT_LABELS: dict[str, str] = {
    "WOOD": "목",
    "FIRE": "화",
    "EARTH": "토",
    "METAL": "금",
    "WATER": "수",
}


class TenGodCode(str, Enum):
    """동양 십신 코드 (LLM 출력용, ETC 포함)"""

    BI_GYEON = "BI_GYEON"  # 비견
    GANG_JAE = "GANG_JAE"  # 겁재
    SIK_SIN = "SIK_SIN"  # 식신
    SANG_GWAN = "SANG_GWAN"  # 상관
    PYEON_JAE = "PYEON_JAE"  # 편재
    JEONG_JAE = "JEONG_JAE"  # 정재
    PYEON_GWAN = "PYEON_GWAN"  # 편관
    JEONG_GWAN = "JEONG_GWAN"  # 정관
    PYEON_IN = "PYEON_IN"  # 편인
    JEONG_IN = "JEONG_IN"  # 정인
    ETC = "ETC"  # 기타 (나머지 합산용)


# 십신 한글 레이블 매핑
TEN_GOD_LABELS: dict[str, str] = {
    "BI_GYEON": "비견",
    "GANG_JAE": "겁재",
    "SIK_SIN": "식신",
    "SANG_GWAN": "상관",
    "PYEON_JAE": "편재",
    "JEONG_JAE": "정재",
    "PYEON_GWAN": "편관",
    "JEONG_GWAN": "정관",
    "PYEON_IN": "편인",
    "JEONG_IN": "정인",
    "ETC": "기타",
}


# 천간 (한자) - 10개
CHEON_GAN: list[str] = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]

# 지지 (한자) - 12개
JI_JI: list[str] = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]


# ============================================================
# 서양 점성술 (Western) 도메인 코드
# ============================================================


class WestElementCode(str, Enum):
    """서양 4원소 코드"""

    FIRE = "FIRE"
    EARTH = "EARTH"
    AIR = "AIR"
    WATER = "WATER"


# 4원소 한글 레이블 매핑
WEST_ELEMENT_LABELS: dict[str, str] = {
    "FIRE": "불",
    "EARTH": "흙",
    "AIR": "공기",
    "WATER": "물",
}


class ModalityCode(str, Enum):
    """서양 3양태 코드"""

    CARDINAL = "CARDINAL"
    FIXED = "FIXED"
    MUTABLE = "MUTABLE"


# 3양태 한글 레이블 매핑
MODALITY_LABELS: dict[str, str] = {
    "CARDINAL": "활동",
    "FIXED": "고정",
    "MUTABLE": "변동",
}


class WestKeywordCode(str, Enum):
    """서양 키워드 코드"""

    EMPATHY = "EMPATHY"
    INTUITION = "INTUITION"
    IMAGINATION = "IMAGINATION"
    BOUNDARY = "BOUNDARY"
    LEADERSHIP = "LEADERSHIP"
    PASSION = "PASSION"
    ANALYSIS = "ANALYSIS"
    ANALYTICAL = "ANALYTICAL"
    STABILITY = "STABILITY"
    COMMUNICATION = "COMMUNICATION"
    INNOVATION = "INNOVATION"
    COURAGE = "COURAGE"
    INDEPENDENCE = "INDEPENDENCE"
    PATIENCE = "PATIENCE"
    PRACTICALITY = "PRACTICALITY"
    CURIOSITY = "CURIOSITY"
    ADAPTABILITY = "ADAPTABILITY"
    NURTURING = "NURTURING"
    SENSITIVITY = "SENSITIVITY"
    CREATIVITY = "CREATIVITY"
    CONFIDENCE = "CONFIDENCE"
    PERFECTIONISM = "PERFECTIONISM"
    HARMONY = "HARMONY"
    DIPLOMACY = "DIPLOMACY"
    BALANCE = "BALANCE"
    INTENSITY = "INTENSITY"
    TRANSFORMATION = "TRANSFORMATION"
    ADVENTURE = "ADVENTURE"
    OPTIMISM = "OPTIMISM"
    FREEDOM = "FREEDOM"
    AMBITION = "AMBITION"
    DISCIPLINE = "DISCIPLINE"
    RESPONSIBILITY = "RESPONSIBILITY"
    HUMANITARIANISM = "HUMANITARIANISM"
    COMPASSION = "COMPASSION"


# 키워드 한글 레이블 매핑
WEST_KEYWORD_LABELS: dict[str, str] = {
    "EMPATHY": "공감",
    "INTUITION": "직관",
    "IMAGINATION": "상상력",
    "BOUNDARY": "경계 설정",
    "LEADERSHIP": "리더십",
    "PASSION": "열정",
    "ANALYSIS": "분석",
    "ANALYTICAL": "분석적",
    "STABILITY": "안정",
    "COMMUNICATION": "소통",
    "INNOVATION": "혁신",
    "COURAGE": "용기",
    "INDEPENDENCE": "독립성",
    "PATIENCE": "인내",
    "PRACTICALITY": "실용성",
    "CURIOSITY": "호기심",
    "ADAPTABILITY": "적응력",
    "NURTURING": "양육",
    "SENSITIVITY": "감수성",
    "CREATIVITY": "창의성",
    "CONFIDENCE": "자신감",
    "PERFECTIONISM": "완벽주의",
    "HARMONY": "조화",
    "DIPLOMACY": "외교",
    "BALANCE": "균형",
    "INTENSITY": "강렬함",
    "TRANSFORMATION": "변화",
    "ADVENTURE": "모험",
    "OPTIMISM": "낙관",
    "FREEDOM": "자유",
    "AMBITION": "야망",
    "DISCIPLINE": "절제",
    "RESPONSIBILITY": "책임감",
    "HUMANITARIANISM": "인도주의",
    "COMPASSION": "연민",
    "PERSISTENCE": "지속력",
    "STRUCTURE": "구조화",
    "REALISM": "현실주의",
}


class ZodiacSignKR(str, Enum):
    """별자리 한글 코드 (띄어쓰기 없음)"""

    ARIES = "양자리"
    TAURUS = "황소자리"
    GEMINI = "쌍둥이자리"
    CANCER = "게자리"
    LEO = "사자자리"
    VIRGO = "처녀자리"
    LIBRA = "천칭자리"
    SCORPIO = "전갈자리"
    SAGITTARIUS = "사수자리"
    CAPRICORN = "염소자리"
    AQUARIUS = "물병자리"
    PISCES = "물고기자리"


# 별자리 한글 목록 (검증용)
ZODIAC_SIGNS_KR: list[str] = [sign.value for sign in ZodiacSignKR]


# ============================================================
# Literal 타입 정의 (Pydantic 스키마용)
# ============================================================

EastElementLiteral = Literal["WOOD", "FIRE", "EARTH", "METAL", "WATER"]
WestElementLiteral = Literal["FIRE", "EARTH", "AIR", "WATER"]
ModalityLiteral = Literal["CARDINAL", "FIXED", "MUTABLE"]
TenGodLiteral = Literal[
    "BI_GYEON",
    "GANG_JAE",
    "SIK_SIN",
    "SANG_GWAN",
    "PYEON_JAE",
    "JEONG_JAE",
    "PYEON_GWAN",
    "JEONG_GWAN",
    "PYEON_IN",
    "JEONG_IN",
    "ETC",
]
WestKeywordLiteral = Literal[
    "EMPATHY",
    "INTUITION",
    "IMAGINATION",
    "BOUNDARY",
    "LEADERSHIP",
    "PASSION",
    "ANALYSIS",
    "ANALYTICAL",
    "STABILITY",
    "COMMUNICATION",
    "INNOVATION",
    "COURAGE",
    "INDEPENDENCE",
    "PATIENCE",
    "PRACTICALITY",
    "CURIOSITY",
    "ADAPTABILITY",
    "NURTURING",
    "SENSITIVITY",
    "CREATIVITY",
    "CONFIDENCE",
    "PERFECTIONISM",
    "HARMONY",
    "DIPLOMACY",
    "BALANCE",
    "INTENSITY",
    "TRANSFORMATION",
    "ADVENTURE",
    "OPTIMISM",
    "FREEDOM",
    "AMBITION",
    "DISCIPLINE",
    "RESPONSIBILITY",
    "HUMANITARIANISM",
    "COMPASSION",
]
ZodiacSignKRLiteral = Literal[
    "양자리",
    "황소자리",
    "쌍둥이자리",
    "게자리",
    "사자자리",
    "처녀자리",
    "천칭자리",
    "전갈자리",
    "사수자리",
    "염소자리",
    "물병자리",
    "물고기자리",
]
