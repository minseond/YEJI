"""공통 Enum 정의

오행, 음양, 배지, 차트 타입 등 동양/서양 공통 사용
"""

from enum import Enum


class ElementCode(str, Enum):
    """오행 (Five Elements)

    동양: 목화토금수
    서양에서도 원소 개념으로 매핑 가능
    """

    WOOD = "WOOD"    # 목(木)
    FIRE = "FIRE"    # 화(火)
    EARTH = "EARTH"  # 토(土)
    METAL = "METAL"  # 금(金)
    WATER = "WATER"  # 수(水)

    @property
    def label_ko(self) -> str:
        """한글 레이블"""
        labels = {
            "WOOD": "목",
            "FIRE": "화",
            "EARTH": "토",
            "METAL": "금",
            "WATER": "수",
        }
        return labels[self.value]

    @property
    def label_hanja(self) -> str:
        """한자 레이블"""
        labels = {
            "WOOD": "木",
            "FIRE": "火",
            "EARTH": "土",
            "METAL": "金",
            "WATER": "水",
        }
        return labels[self.value]


class YinYangBalance(str, Enum):
    """음양 균형 상태

    퍼센트 기준:
    - STRONG_YIN: 음 > 65%
    - SLIGHT_YIN: 음 55-65%
    - BALANCED: 45-55%
    - SLIGHT_YANG: 양 55-65%
    - STRONG_YANG: 양 > 65%
    """

    STRONG_YIN = "STRONG_YIN"     # 음 우세 (>65%)
    SLIGHT_YIN = "SLIGHT_YIN"     # 약간 음 (55-65%)
    BALANCED = "BALANCED"          # 균형 (45-55%)
    SLIGHT_YANG = "SLIGHT_YANG"   # 약간 양 (55-65%)
    STRONG_YANG = "STRONG_YANG"   # 양 우세 (>65%)

    @property
    def label_ko(self) -> str:
        """한글 레이블"""
        labels = {
            "STRONG_YIN": "음 우세",
            "SLIGHT_YIN": "약간 음",
            "BALANCED": "균형",
            "SLIGHT_YANG": "약간 양",
            "STRONG_YANG": "양 우세",
        }
        return labels[self.value]

    @classmethod
    def from_ratio(cls, yang_percent: float) -> "YinYangBalance":
        """양 비율로부터 균형 상태 계산

        Args:
            yang_percent: 양의 비율 (0-100)
        """
        if yang_percent > 65:
            return cls.STRONG_YANG
        elif yang_percent > 55:
            return cls.SLIGHT_YANG
        elif yang_percent >= 45:
            return cls.BALANCED
        elif yang_percent >= 35:
            return cls.SLIGHT_YIN
        else:
            return cls.STRONG_YIN


class CommonBadge(str, Enum):
    """공통 UI 배지

    프론트엔드에서 배지 컴포넌트 렌더링에 사용
    """

    # 오행 강약
    WOOD_STRONG = "WOOD_STRONG"
    WOOD_WEAK = "WOOD_WEAK"
    FIRE_STRONG = "FIRE_STRONG"
    FIRE_WEAK = "FIRE_WEAK"
    EARTH_STRONG = "EARTH_STRONG"
    EARTH_WEAK = "EARTH_WEAK"
    METAL_STRONG = "METAL_STRONG"
    METAL_WEAK = "METAL_WEAK"
    WATER_STRONG = "WATER_STRONG"
    WATER_WEAK = "WATER_WEAK"

    # 음양
    YIN_DOMINANT = "YIN_DOMINANT"
    YANG_DOMINANT = "YANG_DOMINANT"
    YIN_YANG_BALANCED = "YIN_YANG_BALANCED"

    # 성향
    ACTION_ORIENTED = "ACTION_ORIENTED"       # 행동파
    THOUGHT_ORIENTED = "THOUGHT_ORIENTED"     # 사고파
    EMOTION_ORIENTED = "EMOTION_ORIENTED"     # 감성파
    SOCIAL_ORIENTED = "SOCIAL_ORIENTED"       # 사회파
    CREATIVE_ORIENTED = "CREATIVE_ORIENTED"   # 창의파

    @property
    def label_ko(self) -> str:
        """한글 레이블"""
        labels = {
            "WOOD_STRONG": "목 강",
            "WOOD_WEAK": "목 약",
            "FIRE_STRONG": "화 강",
            "FIRE_WEAK": "화 약",
            "EARTH_STRONG": "토 강",
            "EARTH_WEAK": "토 약",
            "METAL_STRONG": "금 강",
            "METAL_WEAK": "금 약",
            "WATER_STRONG": "수 강",
            "WATER_WEAK": "수 약",
            "YIN_DOMINANT": "음 우세",
            "YANG_DOMINANT": "양 우세",
            "YIN_YANG_BALANCED": "음양 균형",
            "ACTION_ORIENTED": "행동파",
            "THOUGHT_ORIENTED": "사고파",
            "EMOTION_ORIENTED": "감성파",
            "SOCIAL_ORIENTED": "사회파",
            "CREATIVE_ORIENTED": "창의파",
        }
        return labels.get(self.value, self.value)


class ChartType(str, Enum):
    """차트 타입

    프론트엔드에서 추천 차트 렌더링에 사용
    """

    PIE = "PIE"           # 원형 차트 (오행 분포)
    RADAR = "RADAR"       # 레이더 차트 (십신/행성 영향력)
    BAR = "BAR"           # 막대 차트 (음양 비율)
    WHEEL = "WHEEL"       # 휠 차트 (사주 팔자 / 출생 차트)
    TIMELINE = "TIMELINE" # 타임라인 (대운/운세 흐름)

    @property
    def label_ko(self) -> str:
        """한글 레이블"""
        labels = {
            "PIE": "원형 차트",
            "RADAR": "레이더 차트",
            "BAR": "막대 차트",
            "WHEEL": "휠 차트",
            "TIMELINE": "타임라인",
        }
        return labels[self.value]
