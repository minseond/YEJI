"""동양 사주 Enum 정의

천간, 지지, 십신, 기둥 키, 배지 등
"""

from enum import Enum


class CheonGanCode(str, Enum):
    """천간 (Heavenly Stems) - 10개

    갑을병정무기경신임계
    """

    GAP = "GAP"         # 갑(甲) - 목 양
    EUL = "EUL"         # 을(乙) - 목 음
    BYEONG = "BYEONG"   # 병(丙) - 화 양
    JEONG = "JEONG"     # 정(丁) - 화 음
    MU = "MU"           # 무(戊) - 토 양
    GI = "GI"           # 기(己) - 토 음
    GYEONG = "GYEONG"   # 경(庚) - 금 양
    SIN = "SIN"         # 신(辛) - 금 음
    IM = "IM"           # 임(壬) - 수 양
    GYE = "GYE"         # 계(癸) - 수 음

    @property
    def hanja(self) -> str:
        """한자"""
        _map = {
            "GAP": "甲", "EUL": "乙", "BYEONG": "丙", "JEONG": "丁", "MU": "戊",
            "GI": "己", "GYEONG": "庚", "SIN": "辛", "IM": "壬", "GYE": "癸",
        }
        return _map[self.value]

    @property
    def hangul(self) -> str:
        """한글"""
        _map = {
            "GAP": "갑", "EUL": "을", "BYEONG": "병", "JEONG": "정", "MU": "무",
            "GI": "기", "GYEONG": "경", "SIN": "신", "IM": "임", "GYE": "계",
        }
        return _map[self.value]

    @property
    def element(self) -> str:
        """오행 (ElementCode 값)"""
        _map = {
            "GAP": "WOOD", "EUL": "WOOD", "BYEONG": "FIRE", "JEONG": "FIRE",
            "MU": "EARTH", "GI": "EARTH", "GYEONG": "METAL", "SIN": "METAL",
            "IM": "WATER", "GYE": "WATER",
        }
        return _map[self.value]

    @property
    def yinyang(self) -> str:
        """음양"""
        _map = {
            "GAP": "YANG", "EUL": "YIN", "BYEONG": "YANG", "JEONG": "YIN",
            "MU": "YANG", "GI": "YIN", "GYEONG": "YANG", "SIN": "YIN",
            "IM": "YANG", "GYE": "YIN",
        }
        return _map[self.value]

    @classmethod
    def from_hangul(cls, hangul: str) -> "CheonGanCode":
        """한글로부터 코드 찾기"""
        _map = {
            "갑": "GAP", "을": "EUL", "병": "BYEONG", "정": "JEONG", "무": "MU",
            "기": "GI", "경": "GYEONG", "신": "SIN", "임": "IM", "계": "GYE",
        }
        if hangul in _map:
            return cls(_map[hangul])
        raise ValueError(f"Unknown hangul: {hangul}")

    @classmethod
    def from_hanja(cls, hanja: str) -> "CheonGanCode":
        """한자로부터 코드 찾기"""
        _map = {
            "甲": "GAP", "乙": "EUL", "丙": "BYEONG", "丁": "JEONG", "戊": "MU",
            "己": "GI", "庚": "GYEONG", "辛": "SIN", "壬": "IM", "癸": "GYE",
        }
        if hanja in _map:
            return cls(_map[hanja])
        raise ValueError(f"Unknown hanja: {hanja}")


class JiJiCode(str, Enum):
    """지지 (Earthly Branches) - 12개

    자축인묘진사오미신유술해
    """

    JA = "JA"       # 자(子) - 수 양
    CHUK = "CHUK"   # 축(丑) - 토 음
    IN = "IN"       # 인(寅) - 목 양
    MYO = "MYO"     # 묘(卯) - 목 음
    JIN = "JIN"     # 진(辰) - 토 양
    SA = "SA"       # 사(巳) - 화 음
    O = "O"         # 오(午) - 화 양
    MI = "MI"       # 미(未) - 토 음
    SHIN = "SHIN"   # 신(申) - 금 양
    YU = "YU"       # 유(酉) - 금 음
    SUL = "SUL"     # 술(戌) - 토 양
    HAE = "HAE"     # 해(亥) - 수 음

    @property
    def hanja(self) -> str:
        """한자"""
        _map = {
            "JA": "子", "CHUK": "丑", "IN": "寅", "MYO": "卯",
            "JIN": "辰", "SA": "巳", "O": "午", "MI": "未",
            "SHIN": "申", "YU": "酉", "SUL": "戌", "HAE": "亥",
        }
        return _map[self.value]

    @property
    def hangul(self) -> str:
        """한글"""
        _map = {
            "JA": "자", "CHUK": "축", "IN": "인", "MYO": "묘",
            "JIN": "진", "SA": "사", "O": "오", "MI": "미",
            "SHIN": "신", "YU": "유", "SUL": "술", "HAE": "해",
        }
        return _map[self.value]

    @property
    def element(self) -> str:
        """오행 (ElementCode 값)"""
        _map = {
            "JA": "WATER", "CHUK": "EARTH", "IN": "WOOD", "MYO": "WOOD",
            "JIN": "EARTH", "SA": "FIRE", "O": "FIRE", "MI": "EARTH",
            "SHIN": "METAL", "YU": "METAL", "SUL": "EARTH", "HAE": "WATER",
        }
        return _map[self.value]

    @property
    def yinyang(self) -> str:
        """음양"""
        _map = {
            "JA": "YANG", "CHUK": "YIN", "IN": "YANG", "MYO": "YIN",
            "JIN": "YANG", "SA": "YIN", "O": "YANG", "MI": "YIN",
            "SHIN": "YANG", "YU": "YIN", "SUL": "YANG", "HAE": "YIN",
        }
        return _map[self.value]

    @property
    def zodiac_animal(self) -> str:
        """띠 동물"""
        _map = {
            "JA": "쥐", "CHUK": "소", "IN": "호랑이", "MYO": "토끼",
            "JIN": "용", "SA": "뱀", "O": "말", "MI": "양",
            "SHIN": "원숭이", "YU": "닭", "SUL": "개", "HAE": "돼지",
        }
        return _map[self.value]

    @classmethod
    def from_hangul(cls, hangul: str) -> "JiJiCode":
        """한글로부터 코드 찾기"""
        _map = {
            "자": "JA", "축": "CHUK", "인": "IN", "묘": "MYO",
            "진": "JIN", "사": "SA", "오": "O", "미": "MI",
            "신": "SHIN", "유": "YU", "술": "SUL", "해": "HAE",
        }
        if hangul in _map:
            return cls(_map[hangul])
        raise ValueError(f"Unknown hangul: {hangul}")


class TenGodCode(str, Enum):
    """십신 (Ten Gods) - 11개 (일간 포함)

    일간을 기준으로 다른 간지와의 관계
    """

    DAY_MASTER = "DAY_MASTER"   # 일간 (나)
    BI_GYEON = "BI_GYEON"       # 비견 (比肩)
    GANG_JAE = "GANG_JAE"       # 겁재 (劫財)
    SIK_SIN = "SIK_SIN"         # 식신 (食神)
    SANG_GWAN = "SANG_GWAN"     # 상관 (傷官)
    PYEON_JAE = "PYEON_JAE"     # 편재 (偏財)
    JEONG_JAE = "JEONG_JAE"     # 정재 (正財)
    PYEON_GWAN = "PYEON_GWAN"   # 편관 (偏官) - 칠살
    JEONG_GWAN = "JEONG_GWAN"   # 정관 (正官)
    PYEON_IN = "PYEON_IN"       # 편인 (偏印) - 효신
    JEONG_IN = "JEONG_IN"       # 정인 (正印)

    @property
    def label_ko(self) -> str:
        """한글 레이블"""
        _map = {
            "DAY_MASTER": "일간",
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
        }
        return _map[self.value]

    @property
    def hanja(self) -> str:
        """한자"""
        _map = {
            "DAY_MASTER": "日干",
            "BI_GYEON": "比肩",
            "GANG_JAE": "劫財",
            "SIK_SIN": "食神",
            "SANG_GWAN": "傷官",
            "PYEON_JAE": "偏財",
            "JEONG_JAE": "正財",
            "PYEON_GWAN": "偏官",
            "JEONG_GWAN": "正官",
            "PYEON_IN": "偏印",
            "JEONG_IN": "正印",
        }
        return _map[self.value]

    @property
    def group(self) -> str:
        """십신 그룹 (TenGodGroupCode 값)"""
        _map = {
            "DAY_MASTER": "BI_GYEOP",
            "BI_GYEON": "BI_GYEOP",
            "GANG_JAE": "BI_GYEOP",
            "SIK_SIN": "SIK_SANG",
            "SANG_GWAN": "SIK_SANG",
            "PYEON_JAE": "JAE_SEONG",
            "JEONG_JAE": "JAE_SEONG",
            "PYEON_GWAN": "GWAN_SEONG",
            "JEONG_GWAN": "GWAN_SEONG",
            "PYEON_IN": "IN_SEONG",
            "JEONG_IN": "IN_SEONG",
        }
        return _map[self.value]


class TenGodGroupCode(str, Enum):
    """십신 그룹 (5개)

    십신을 5개 그룹으로 분류
    """

    BI_GYEOP = "BI_GYEOP"       # 비겁 (비견+겁재)
    SIK_SANG = "SIK_SANG"       # 식상 (식신+상관)
    JAE_SEONG = "JAE_SEONG"     # 재성 (편재+정재)
    GWAN_SEONG = "GWAN_SEONG"   # 관성 (편관+정관)
    IN_SEONG = "IN_SEONG"       # 인성 (편인+정인)

    @property
    def label_ko(self) -> str:
        """한글 레이블"""
        _map = {
            "BI_GYEOP": "비겁",
            "SIK_SANG": "식상",
            "JAE_SEONG": "재성",
            "GWAN_SEONG": "관성",
            "IN_SEONG": "인성",
        }
        return _map[self.value]

    @property
    def meaning(self) -> str:
        """의미 설명"""
        _map = {
            "BI_GYEOP": "자아, 경쟁, 형제",
            "SIK_SANG": "표현, 재능, 자녀",
            "JAE_SEONG": "재물, 현실, 아버지",
            "GWAN_SEONG": "명예, 직업, 남편",
            "IN_SEONG": "학문, 어머니, 인덕",
        }
        return _map[self.value]


class PillarKey(str, Enum):
    """사주 기둥 키 (Four Pillars)"""

    YEAR = "year"    # 연주
    MONTH = "month"  # 월주
    DAY = "day"      # 일주
    HOUR = "hour"    # 시주

    @property
    def label_ko(self) -> str:
        """한글 레이블"""
        _map = {
            "year": "연주",
            "month": "월주",
            "day": "일주",
            "hour": "시주",
        }
        return _map[self.value]

    @property
    def meaning(self) -> str:
        """의미 설명"""
        _map = {
            "year": "조상, 사회적 환경",
            "month": "부모, 성장 환경",
            "day": "본인, 배우자",
            "hour": "자녀, 말년",
        }
        return _map[self.value]


class EasternBadge(str, Enum):
    """동양 사주 전용 배지

    십신 우세, 특수 구조 등
    """

    # 십신 그룹 우세
    BI_GYEOP_DOMINANT = "BI_GYEOP_DOMINANT"     # 비겁 우세
    SIK_SANG_DOMINANT = "SIK_SANG_DOMINANT"     # 식상 우세
    JAE_SEONG_DOMINANT = "JAE_SEONG_DOMINANT"   # 재성 우세
    GWAN_SEONG_DOMINANT = "GWAN_SEONG_DOMINANT" # 관성 우세
    IN_SEONG_DOMINANT = "IN_SEONG_DOMINANT"     # 인성 우세

    # 특수 구조 (격국)
    GWON_MOK = "GWON_MOK"                 # 건록격
    YANG_IN = "YANG_IN"                   # 양인격
    SIK_SIN_SAENG_JAE = "SIK_SIN_SAENG_JAE"     # 식신생재
    GWAN_IN_SANG_SAENG = "GWAN_IN_SANG_SAENG"   # 관인상생
    JAE_GWAN_SSANG_MI = "JAE_GWAN_SSANG_MI"     # 재관쌍미

    # 신살 (확장 예정)
    YEOK_MA = "YEOK_MA"     # 역마
    DO_HWA = "DO_HWA"       # 도화
    GWAE_GANG = "GWAE_GANG" # 괴강

    @property
    def label_ko(self) -> str:
        """한글 레이블"""
        _map = {
            "BI_GYEOP_DOMINANT": "비겁 우세",
            "SIK_SANG_DOMINANT": "식상 우세",
            "JAE_SEONG_DOMINANT": "재성 우세",
            "GWAN_SEONG_DOMINANT": "관성 우세",
            "IN_SEONG_DOMINANT": "인성 우세",
            "GWON_MOK": "건록격",
            "YANG_IN": "양인격",
            "SIK_SIN_SAENG_JAE": "식신생재",
            "GWAN_IN_SANG_SAENG": "관인상생",
            "JAE_GWAN_SSANG_MI": "재관쌍미",
            "YEOK_MA": "역마",
            "DO_HWA": "도화",
            "GWAE_GANG": "괴강",
        }
        return _map.get(self.value, self.value)
