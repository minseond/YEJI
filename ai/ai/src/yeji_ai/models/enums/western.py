"""서양 점성술 Enum 정의

별자리, 행성, 하우스, 애스펙트, 배지 등
"""

from enum import Enum


class ZodiacCode(str, Enum):
    """12별자리 (Zodiac Signs)"""

    ARIES = "ARIES"             # 양자리 ♈
    TAURUS = "TAURUS"           # 황소자리 ♉
    GEMINI = "GEMINI"           # 쌍둥이자리 ♊
    CANCER = "CANCER"           # 게자리 ♋
    LEO = "LEO"                 # 사자자리 ♌
    VIRGO = "VIRGO"             # 처녀자리 ♍
    LIBRA = "LIBRA"             # 천칭자리 ♎
    SCORPIO = "SCORPIO"         # 전갈자리 ♏
    SAGITTARIUS = "SAGITTARIUS" # 사수자리 ♐
    CAPRICORN = "CAPRICORN"     # 염소자리 ♑
    AQUARIUS = "AQUARIUS"       # 물병자리 ♒
    PISCES = "PISCES"           # 물고기자리 ♓

    @property
    def label_ko(self) -> str:
        """한글 레이블"""
        _map = {
            "ARIES": "양자리",
            "TAURUS": "황소자리",
            "GEMINI": "쌍둥이자리",
            "CANCER": "게자리",
            "LEO": "사자자리",
            "VIRGO": "처녀자리",
            "LIBRA": "천칭자리",
            "SCORPIO": "전갈자리",
            "SAGITTARIUS": "사수자리",
            "CAPRICORN": "염소자리",
            "AQUARIUS": "물병자리",
            "PISCES": "물고기자리",
        }
        return _map[self.value]

    @property
    def symbol(self) -> str:
        """유니코드 심볼"""
        _map = {
            "ARIES": "♈", "TAURUS": "♉", "GEMINI": "♊", "CANCER": "♋",
            "LEO": "♌", "VIRGO": "♍", "LIBRA": "♎", "SCORPIO": "♏",
            "SAGITTARIUS": "♐", "CAPRICORN": "♑", "AQUARIUS": "♒", "PISCES": "♓",
        }
        return _map[self.value]

    @property
    def element(self) -> str:
        """원소 (ZodiacElement 값)"""
        _map = {
            "ARIES": "FIRE", "TAURUS": "EARTH", "GEMINI": "AIR", "CANCER": "WATER",
            "LEO": "FIRE", "VIRGO": "EARTH", "LIBRA": "AIR", "SCORPIO": "WATER",
            "SAGITTARIUS": "FIRE", "CAPRICORN": "EARTH", "AQUARIUS": "AIR", "PISCES": "WATER",
        }
        return _map[self.value]

    @property
    def modality(self) -> str:
        """모달리티 (ZodiacModality 값)"""
        _map = {
            "ARIES": "CARDINAL", "TAURUS": "FIXED", "GEMINI": "MUTABLE",
            "CANCER": "CARDINAL", "LEO": "FIXED", "VIRGO": "MUTABLE",
            "LIBRA": "CARDINAL", "SCORPIO": "FIXED", "SAGITTARIUS": "MUTABLE",
            "CAPRICORN": "CARDINAL", "AQUARIUS": "FIXED", "PISCES": "MUTABLE",
        }
        return _map[self.value]

    @property
    def ruling_planet(self) -> str:
        """지배 행성 (PlanetCode 값)"""
        _map = {
            "ARIES": "MARS", "TAURUS": "VENUS", "GEMINI": "MERCURY",
            "CANCER": "MOON", "LEO": "SUN", "VIRGO": "MERCURY",
            "LIBRA": "VENUS", "SCORPIO": "PLUTO", "SAGITTARIUS": "JUPITER",
            "CAPRICORN": "SATURN", "AQUARIUS": "URANUS", "PISCES": "NEPTUNE",
        }
        return _map[self.value]


class ZodiacElement(str, Enum):
    """별자리 원소 (4원소)"""

    FIRE = "FIRE"    # 불
    EARTH = "EARTH"  # 흙
    AIR = "AIR"      # 공기
    WATER = "WATER"  # 물

    @property
    def label_ko(self) -> str:
        """한글 레이블"""
        _map = {
            "FIRE": "불",
            "EARTH": "흙",
            "AIR": "공기",
            "WATER": "물",
        }
        return _map[self.value]

    @property
    def signs(self) -> list[str]:
        """해당 원소의 별자리들"""
        _map = {
            "FIRE": ["ARIES", "LEO", "SAGITTARIUS"],
            "EARTH": ["TAURUS", "VIRGO", "CAPRICORN"],
            "AIR": ["GEMINI", "LIBRA", "AQUARIUS"],
            "WATER": ["CANCER", "SCORPIO", "PISCES"],
        }
        return _map[self.value]


class ZodiacModality(str, Enum):
    """별자리 모달리티 (3모드)"""

    CARDINAL = "CARDINAL"  # 카디널 (시작, 개척)
    FIXED = "FIXED"        # 고정 (유지, 안정)
    MUTABLE = "MUTABLE"    # 변통 (변화, 적응)

    @property
    def label_ko(self) -> str:
        """한글 레이블"""
        _map = {
            "CARDINAL": "카디널",
            "FIXED": "고정",
            "MUTABLE": "변통",
        }
        return _map[self.value]

    @property
    def meaning(self) -> str:
        """의미 설명"""
        _map = {
            "CARDINAL": "시작, 개척, 리더십",
            "FIXED": "유지, 안정, 집중력",
            "MUTABLE": "변화, 적응, 유연성",
        }
        return _map[self.value]

    @property
    def signs(self) -> list[str]:
        """해당 모달리티의 별자리들"""
        _map = {
            "CARDINAL": ["ARIES", "CANCER", "LIBRA", "CAPRICORN"],
            "FIXED": ["TAURUS", "LEO", "SCORPIO", "AQUARIUS"],
            "MUTABLE": ["GEMINI", "VIRGO", "SAGITTARIUS", "PISCES"],
        }
        return _map[self.value]


class PlanetCode(str, Enum):
    """10행성 (Classical + Modern)"""

    SUN = "SUN"           # 태양 ☉
    MOON = "MOON"         # 달 ☽
    MERCURY = "MERCURY"   # 수성 ☿
    VENUS = "VENUS"       # 금성 ♀
    MARS = "MARS"         # 화성 ♂
    JUPITER = "JUPITER"   # 목성 ♃
    SATURN = "SATURN"     # 토성 ♄
    URANUS = "URANUS"     # 천왕성 ♅
    NEPTUNE = "NEPTUNE"   # 해왕성 ♆
    PLUTO = "PLUTO"       # 명왕성 ♇

    @property
    def label_ko(self) -> str:
        """한글 레이블"""
        _map = {
            "SUN": "태양", "MOON": "달", "MERCURY": "수성", "VENUS": "금성",
            "MARS": "화성", "JUPITER": "목성", "SATURN": "토성",
            "URANUS": "천왕성", "NEPTUNE": "해왕성", "PLUTO": "명왕성",
        }
        return _map[self.value]

    @property
    def symbol(self) -> str:
        """유니코드 심볼"""
        _map = {
            "SUN": "☉", "MOON": "☽", "MERCURY": "☿", "VENUS": "♀",
            "MARS": "♂", "JUPITER": "♃", "SATURN": "♄",
            "URANUS": "♅", "NEPTUNE": "♆", "PLUTO": "♇",
        }
        return _map[self.value]

    @property
    def meaning(self) -> str:
        """의미 설명"""
        _map = {
            "SUN": "자아, 정체성, 활력",
            "MOON": "감정, 무의식, 어머니",
            "MERCURY": "소통, 지성, 학습",
            "VENUS": "사랑, 아름다움, 가치",
            "MARS": "행동, 욕망, 에너지",
            "JUPITER": "행운, 확장, 철학",
            "SATURN": "책임, 제한, 훈련",
            "URANUS": "혁신, 자유, 변화",
            "NEPTUNE": "영감, 환상, 직관",
            "PLUTO": "변혁, 권력, 재생",
        }
        return _map[self.value]

    @property
    def is_personal(self) -> bool:
        """개인 행성 여부 (Sun-Mars)"""
        _map = {
            "SUN": True, "MOON": True, "MERCURY": True, "VENUS": True, "MARS": True,
            "JUPITER": False, "SATURN": False, "URANUS": False, "NEPTUNE": False, "PLUTO": False,
        }
        return _map[self.value]


class HouseCode(str, Enum):
    """12하우스 (Houses)"""

    H1_SELF = "H1_SELF"                     # 1하우스: 자아
    H2_POSSESSIONS = "H2_POSSESSIONS"       # 2하우스: 재물
    H3_COMMUNICATION = "H3_COMMUNICATION"   # 3하우스: 소통
    H4_HOME = "H4_HOME"                     # 4하우스: 가정
    H5_CREATIVITY = "H5_CREATIVITY"         # 5하우스: 창의성/연애
    H6_HEALTH = "H6_HEALTH"                 # 6하우스: 건강/일상
    H7_PARTNERSHIP = "H7_PARTNERSHIP"       # 7하우스: 파트너십
    H8_TRANSFORMATION = "H8_TRANSFORMATION" # 8하우스: 변화/유산
    H9_PHILOSOPHY = "H9_PHILOSOPHY"         # 9하우스: 철학/여행
    H10_CAREER = "H10_CAREER"               # 10하우스: 커리어
    H11_COMMUNITY = "H11_COMMUNITY"         # 11하우스: 커뮤니티
    H12_SUBCONSCIOUS = "H12_SUBCONSCIOUS"   # 12하우스: 무의식

    @property
    def label_ko(self) -> str:
        """한글 레이블"""
        _map = {
            "H1_SELF": "1하우스 (자아)",
            "H2_POSSESSIONS": "2하우스 (재물)",
            "H3_COMMUNICATION": "3하우스 (소통)",
            "H4_HOME": "4하우스 (가정)",
            "H5_CREATIVITY": "5하우스 (창의/연애)",
            "H6_HEALTH": "6하우스 (건강/일상)",
            "H7_PARTNERSHIP": "7하우스 (파트너십)",
            "H8_TRANSFORMATION": "8하우스 (변화/유산)",
            "H9_PHILOSOPHY": "9하우스 (철학/여행)",
            "H10_CAREER": "10하우스 (커리어)",
            "H11_COMMUNITY": "11하우스 (커뮤니티)",
            "H12_SUBCONSCIOUS": "12하우스 (무의식)",
        }
        return _map[self.value]

    @property
    def number(self) -> int:
        """하우스 번호"""
        _map = {
            "H1_SELF": 1, "H2_POSSESSIONS": 2, "H3_COMMUNICATION": 3,
            "H4_HOME": 4, "H5_CREATIVITY": 5, "H6_HEALTH": 6,
            "H7_PARTNERSHIP": 7, "H8_TRANSFORMATION": 8, "H9_PHILOSOPHY": 9,
            "H10_CAREER": 10, "H11_COMMUNITY": 11, "H12_SUBCONSCIOUS": 12,
        }
        return _map[self.value]

    @property
    def meaning(self) -> str:
        """의미 설명"""
        _map = {
            "H1_SELF": "외모, 성격, 첫인상",
            "H2_POSSESSIONS": "돈, 소유물, 가치관",
            "H3_COMMUNICATION": "형제, 이웃, 단거리 여행",
            "H4_HOME": "가족, 뿌리, 부동산",
            "H5_CREATIVITY": "연애, 자녀, 취미",
            "H6_HEALTH": "건강, 직장, 일상루틴",
            "H7_PARTNERSHIP": "결혼, 계약, 공개적 적",
            "H8_TRANSFORMATION": "성, 죽음, 유산, 타인의 돈",
            "H9_PHILOSOPHY": "고등교육, 해외여행, 종교",
            "H10_CAREER": "직업, 명성, 사회적 지위",
            "H11_COMMUNITY": "친구, 희망, 단체활동",
            "H12_SUBCONSCIOUS": "비밀, 고독, 영성",
        }
        return _map[self.value]

    @classmethod
    def from_number(cls, number: int) -> "HouseCode":
        """번호로부터 HouseCode 찾기"""
        _map = {
            1: "H1_SELF", 2: "H2_POSSESSIONS", 3: "H3_COMMUNICATION",
            4: "H4_HOME", 5: "H5_CREATIVITY", 6: "H6_HEALTH",
            7: "H7_PARTNERSHIP", 8: "H8_TRANSFORMATION", 9: "H9_PHILOSOPHY",
            10: "H10_CAREER", 11: "H11_COMMUNITY", 12: "H12_SUBCONSCIOUS",
        }
        if number in _map:
            return cls(_map[number])
        raise ValueError(f"Invalid house number: {number}")


class AspectCode(str, Enum):
    """애스펙트 (행성 간 각도 관계)"""

    CONJUNCTION = "CONJUNCTION"   # 합 (0°) ☌
    SEXTILE = "SEXTILE"           # 육분위 (60°) ⚹
    SQUARE = "SQUARE"             # 스퀘어 (90°) □
    TRINE = "TRINE"               # 삼합 (120°) △
    OPPOSITION = "OPPOSITION"     # 충 (180°) ☍

    @property
    def label_ko(self) -> str:
        """한글 레이블"""
        _map = {
            "CONJUNCTION": "합",
            "SEXTILE": "육분위",
            "SQUARE": "스퀘어",
            "TRINE": "삼합",
            "OPPOSITION": "충",
        }
        return _map[self.value]

    @property
    def symbol(self) -> str:
        """유니코드 심볼"""
        _map = {
            "CONJUNCTION": "☌",
            "SEXTILE": "⚹",
            "SQUARE": "□",
            "TRINE": "△",
            "OPPOSITION": "☍",
        }
        return _map[self.value]

    @property
    def degree(self) -> int:
        """각도"""
        _map = {
            "CONJUNCTION": 0,
            "SEXTILE": 60,
            "SQUARE": 90,
            "TRINE": 120,
            "OPPOSITION": 180,
        }
        return _map[self.value]

    @property
    def nature(self) -> str:
        """성질 (AspectNature 값)"""
        _map = {
            "CONJUNCTION": "NEUTRAL",
            "SEXTILE": "HARMONIOUS",
            "SQUARE": "CHALLENGING",
            "TRINE": "HARMONIOUS",
            "OPPOSITION": "CHALLENGING",
        }
        return _map[self.value]


class AspectNature(str, Enum):
    """애스펙트 성질"""

    HARMONIOUS = "HARMONIOUS"     # 조화 (삼합, 육분위)
    CHALLENGING = "CHALLENGING"   # 도전 (스퀘어, 충)
    NEUTRAL = "NEUTRAL"           # 중립 (합)

    @property
    def label_ko(self) -> str:
        """한글 레이블"""
        _map = {
            "HARMONIOUS": "조화",
            "CHALLENGING": "도전",
            "NEUTRAL": "중립",
        }
        return _map[self.value]


class WesternBadge(str, Enum):
    """서양 점성술 전용 배지"""

    # 원소 우세
    FIRE_DOMINANT = "FIRE_DOMINANT"
    EARTH_DOMINANT = "EARTH_DOMINANT"
    AIR_DOMINANT = "AIR_DOMINANT"
    WATER_DOMINANT = "WATER_DOMINANT"

    # 모달리티 우세
    CARDINAL_DOMINANT = "CARDINAL_DOMINANT"
    FIXED_DOMINANT = "FIXED_DOMINANT"
    MUTABLE_DOMINANT = "MUTABLE_DOMINANT"

    # 행성 강조
    SUN_STRONG = "SUN_STRONG"
    MOON_STRONG = "MOON_STRONG"
    MERCURY_STRONG = "MERCURY_STRONG"
    VENUS_STRONG = "VENUS_STRONG"
    MARS_STRONG = "MARS_STRONG"
    JUPITER_STRONG = "JUPITER_STRONG"
    SATURN_STRONG = "SATURN_STRONG"
    URANUS_STRONG = "URANUS_STRONG"
    NEPTUNE_STRONG = "NEPTUNE_STRONG"
    PLUTO_STRONG = "PLUTO_STRONG"

    # 특수 패턴
    GRAND_TRINE = "GRAND_TRINE"       # 그랜드 트라인
    GRAND_CROSS = "GRAND_CROSS"       # 그랜드 크로스
    T_SQUARE = "T_SQUARE"             # T스퀘어
    YOD = "YOD"                       # 요드 (신의 손가락)
    STELLIUM = "STELLIUM"             # 스텔리움 (3개 이상 행성 집중)

    @property
    def label_ko(self) -> str:
        """한글 레이블"""
        _map = {
            "FIRE_DOMINANT": "불 원소 우세",
            "EARTH_DOMINANT": "흙 원소 우세",
            "AIR_DOMINANT": "공기 원소 우세",
            "WATER_DOMINANT": "물 원소 우세",
            "CARDINAL_DOMINANT": "카디널 우세",
            "FIXED_DOMINANT": "고정 우세",
            "MUTABLE_DOMINANT": "변통 우세",
            "SUN_STRONG": "태양 강조",
            "MOON_STRONG": "달 강조",
            "MERCURY_STRONG": "수성 강조",
            "VENUS_STRONG": "금성 강조",
            "MARS_STRONG": "화성 강조",
            "JUPITER_STRONG": "목성 강조",
            "SATURN_STRONG": "토성 강조",
            "URANUS_STRONG": "천왕성 강조",
            "NEPTUNE_STRONG": "해왕성 강조",
            "PLUTO_STRONG": "명왕성 강조",
            "GRAND_TRINE": "그랜드 트라인",
            "GRAND_CROSS": "그랜드 크로스",
            "T_SQUARE": "T스퀘어",
            "YOD": "요드",
            "STELLIUM": "스텔리움",
        }
        return _map.get(self.value, self.value)
