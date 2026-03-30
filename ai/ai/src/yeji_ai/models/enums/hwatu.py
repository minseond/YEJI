"""화투 카드 Enum 정의

화투 48장 카드에 대한 체계적인 타입 정의 및 매핑을 제공합니다.
"""

from dataclasses import dataclass
from enum import Enum, IntEnum


class HwatuMonth(IntEnum):
    """화투 12개월 Enum"""

    JANUARY = 1  # 소나무 (송학)
    FEBRUARY = 2  # 매화 (매조)
    MARCH = 3  # 벚꽃 (벚꽃)
    APRIL = 4  # 등나무 (흑싸리)
    MAY = 5  # 창포 (난초)
    JUNE = 6  # 모란 (목단)
    JULY = 7  # 싸리 (홍싸리)
    AUGUST = 8  # 공산 (억새)
    SEPTEMBER = 9  # 국화 (국진)
    OCTOBER = 10  # 단풍 (풍)
    NOVEMBER = 11  # 오동 (동)
    DECEMBER = 12  # 비 (비)

    @property
    def label_ko(self) -> str:
        """한국어 라벨"""
        labels = {
            1: "소나무",
            2: "매화",
            3: "벚꽃",
            4: "등나무",
            5: "창포",
            6: "모란",
            7: "싸리",
            8: "공산",
            9: "국화",
            10: "단풍",
            11: "오동",
            12: "비",
        }
        return labels[self.value]

    @property
    def label_en(self) -> str:
        """영어 라벨"""
        labels = {
            1: "Pine",
            2: "Plum Blossom",
            3: "Cherry Blossom",
            4: "Wisteria",
            5: "Iris",
            6: "Peony",
            7: "Bush Clover",
            8: "Pampas Grass",
            9: "Chrysanthemum",
            10: "Maple",
            11: "Paulownia",
            12: "Rain",
        }
        return labels[self.value]

    @property
    def plant(self) -> str:
        """식물명"""
        return self.label_ko

    @property
    def fortune_keywords(self) -> list[str]:
        """점술 키워드"""
        keywords_map = {
            1: ["시작", "고집", "원칙", "근본"],
            2: ["인내", "준비", "사랑", "감성"],
            3: ["유혹", "감정", "불안정", "변화"],
            4: ["관계", "얽힘", "집착", "구속"],
            5: ["경쟁", "힘", "승부욕", "도전"],
            6: ["명예", "과시", "체면", "화려함"],
            7: ["변화", "이동", "횡재", "운"],
            8: ["공허", "거리감", "단절", "고독"],
            9: ["정리", "결론", "완성", "마무리"],
            10: ["욕심", "거래", "이익", "계산"],
            11: ["보호", "성장", "금전", "안정"],
            12: ["반복", "순환", "흐름", "연속"],
        }
        return keywords_map[self.value]


class HwatuCardType(str, Enum):
    """화투 카드 종류 Enum"""

    GWANG = "gwang"  # 광 (5장: 1,3,8,11,12월)
    YEOLKKEUT = "yeolkkeut"  # 열끗/동물 (9장)
    DDI = "ddi"  # 띠 (10장)
    PI = "pi"  # 피 (24장)

    @property
    def label_ko(self) -> str:
        """한국어 라벨"""
        labels = {
            "gwang": "광",
            "yeolkkeut": "열끗",
            "ddi": "띠",
            "pi": "피",
        }
        return labels[self.value]

    @property
    def fortune_keywords(self) -> list[str]:
        """카드 종류별 점술 키워드"""
        keywords_map = {
            "gwang": ["결정적 사건", "강한 운", "명확한 방향", "중대한 변화"],
            "yeolkkeut": ["현실", "실속", "관계의 균형", "구체적 이익"],
            "ddi": ["말", "약속", "인간관계", "소통"],
            "pi": ["소모", "감정 낭비", "사소한 문제", "작은 갈등"],
        }
        return keywords_map[self.value]


@dataclass
class HwatuCard:
    """화투 카드 데이터 클래스"""

    code: int  # 0~47
    month: HwatuMonth
    card_type: HwatuCardType
    name_ko: str  # "1월 광", "3월 홍단"
    name_en: str
    fortune_meaning: str  # 점술 의미
    keywords: list[str]  # 해석 키워드

    def __post_init__(self) -> None:
        """초기화 후 검증"""
        if not 0 <= self.code <= 47:
            raise ValueError(f"카드 코드는 0~47 범위여야 합니다: {self.code}")


# 48장 화투 카드 매핑 테이블
HWATU_CARDS: dict[int, HwatuCard] = {
    # 1월 (소나무) - 0~3
    0: HwatuCard(
        code=0,
        month=HwatuMonth.JANUARY,
        card_type=HwatuCardType.GWANG,
        name_ko="1월 광",
        name_en="Pine Bright",
        fortune_meaning="새로운 시작의 강력한 힘. 원칙을 지키며 나아가는 운.",
        keywords=["시작", "강력함", "원칙", "결정적 사건"],
    ),
    1: HwatuCard(
        code=1,
        month=HwatuMonth.JANUARY,
        card_type=HwatuCardType.YEOLKKEUT,
        name_ko="1월 학",
        name_en="Pine Crane",
        fortune_meaning="고고한 품격. 현실적 이익과 원칙의 균형.",
        keywords=["품격", "균형", "현실", "시작"],
    ),
    2: HwatuCard(
        code=2,
        month=HwatuMonth.JANUARY,
        card_type=HwatuCardType.DDI,
        name_ko="1월 홍단",
        name_en="Pine Red Ribbon",
        fortune_meaning="새로운 약속과 관계의 시작.",
        keywords=["약속", "관계", "시작", "소통"],
    ),
    3: HwatuCard(
        code=3,
        month=HwatuMonth.JANUARY,
        card_type=HwatuCardType.PI,
        name_ko="1월 피",
        name_en="Pine Junk",
        fortune_meaning="시작 단계의 작은 갈등이나 소모.",
        keywords=["소모", "갈등", "시작", "사소함"],
    ),
    # 2월 (매화) - 4~7
    4: HwatuCard(
        code=4,
        month=HwatuMonth.FEBRUARY,
        card_type=HwatuCardType.YEOLKKEUT,
        name_ko="2월 꾀꼬리",
        name_en="Plum Bush Warbler",
        fortune_meaning="인내 끝의 기쁜 소식. 사랑과 감성의 실속.",
        keywords=["기쁜 소식", "인내", "사랑", "실속"],
    ),
    5: HwatuCard(
        code=5,
        month=HwatuMonth.FEBRUARY,
        card_type=HwatuCardType.DDI,
        name_ko="2월 홍단",
        name_en="Plum Red Ribbon",
        fortune_meaning="감성적 약속과 준비된 관계.",
        keywords=["약속", "감성", "준비", "인내"],
    ),
    6: HwatuCard(
        code=6,
        month=HwatuMonth.FEBRUARY,
        card_type=HwatuCardType.PI,
        name_ko="2월 피",
        name_en="Plum Junk",
        fortune_meaning="준비 과정의 사소한 감정 소모.",
        keywords=["소모", "감정", "준비", "인내"],
    ),
    7: HwatuCard(
        code=7,
        month=HwatuMonth.FEBRUARY,
        card_type=HwatuCardType.PI,
        name_ko="2월 피",
        name_en="Plum Junk",
        fortune_meaning="준비 과정의 작은 문제.",
        keywords=["사소한 문제", "준비", "감성", "인내"],
    ),
    # 3월 (벚꽃) - 8~11
    8: HwatuCard(
        code=8,
        month=HwatuMonth.MARCH,
        card_type=HwatuCardType.GWANG,
        name_ko="3월 광",
        name_en="Cherry Blossom Bright",
        fortune_meaning="감정의 강렬한 변화. 유혹과 불안정 속 중대한 선택.",
        keywords=["감정", "유혹", "변화", "결정적 사건"],
    ),
    9: HwatuCard(
        code=9,
        month=HwatuMonth.MARCH,
        card_type=HwatuCardType.YEOLKKEUT,
        name_ko="3월 막패",
        name_en="Cherry Blossom Junk",
        fortune_meaning="감정적 실속 없음. 불안정한 관계.",
        keywords=["불안정", "감정", "실속 없음", "유혹"],
    ),
    10: HwatuCard(
        code=10,
        month=HwatuMonth.MARCH,
        card_type=HwatuCardType.DDI,
        name_ko="3월 홍단",
        name_en="Cherry Blossom Red Ribbon",
        fortune_meaning="불안정한 약속. 감정적 소통.",
        keywords=["약속", "불안정", "감정", "유혹"],
    ),
    11: HwatuCard(
        code=11,
        month=HwatuMonth.MARCH,
        card_type=HwatuCardType.PI,
        name_ko="3월 피",
        name_en="Cherry Blossom Junk",
        fortune_meaning="감정 소모와 불안.",
        keywords=["소모", "불안", "감정", "변화"],
    ),
    # 4월 (등나무) - 12~15
    12: HwatuCard(
        code=12,
        month=HwatuMonth.APRIL,
        card_type=HwatuCardType.YEOLKKEUT,
        name_ko="4월 두견새",
        name_en="Wisteria Cuckoo",
        fortune_meaning="얽힌 관계의 현실적 이익. 집착 속 균형.",
        keywords=["얽힘", "집착", "관계", "현실"],
    ),
    13: HwatuCard(
        code=13,
        month=HwatuMonth.APRIL,
        card_type=HwatuCardType.DDI,
        name_ko="4월 초단",
        name_en="Wisteria Green Ribbon",
        fortune_meaning="복잡한 약속. 얽힌 인간관계.",
        keywords=["약속", "얽힘", "관계", "복잡"],
    ),
    14: HwatuCard(
        code=14,
        month=HwatuMonth.APRIL,
        card_type=HwatuCardType.PI,
        name_ko="4월 피",
        name_en="Wisteria Junk",
        fortune_meaning="관계 얽힘으로 인한 소모.",
        keywords=["소모", "얽힘", "관계", "집착"],
    ),
    15: HwatuCard(
        code=15,
        month=HwatuMonth.APRIL,
        card_type=HwatuCardType.PI,
        name_ko="4월 피",
        name_en="Wisteria Junk",
        fortune_meaning="관계의 작은 구속.",
        keywords=["구속", "관계", "얽힘", "사소함"],
    ),
    # 5월 (창포) - 16~19
    16: HwatuCard(
        code=16,
        month=HwatuMonth.MAY,
        card_type=HwatuCardType.YEOLKKEUT,
        name_ko="5월 다리",
        name_en="Iris Bridge",
        fortune_meaning="경쟁 속 현실적 성과. 승부욕의 실속.",
        keywords=["경쟁", "성과", "승부", "현실"],
    ),
    17: HwatuCard(
        code=17,
        month=HwatuMonth.MAY,
        card_type=HwatuCardType.DDI,
        name_ko="5월 초단",
        name_en="Iris Green Ribbon",
        fortune_meaning="도전적 약속. 힘겨루기의 관계.",
        keywords=["도전", "약속", "경쟁", "힘"],
    ),
    18: HwatuCard(
        code=18,
        month=HwatuMonth.MAY,
        card_type=HwatuCardType.PI,
        name_ko="5월 피",
        name_en="Iris Junk",
        fortune_meaning="경쟁으로 인한 감정 소모.",
        keywords=["소모", "경쟁", "승부", "갈등"],
    ),
    19: HwatuCard(
        code=19,
        month=HwatuMonth.MAY,
        card_type=HwatuCardType.PI,
        name_ko="5월 피",
        name_en="Iris Junk",
        fortune_meaning="도전 과정의 사소한 문제.",
        keywords=["사소함", "도전", "경쟁", "소모"],
    ),
    # 6월 (모란) - 20~23
    20: HwatuCard(
        code=20,
        month=HwatuMonth.JUNE,
        card_type=HwatuCardType.YEOLKKEUT,
        name_ko="6월 나비",
        name_en="Peony Butterfly",
        fortune_meaning="명예와 체면의 현실적 이익.",
        keywords=["명예", "체면", "화려함", "현실"],
    ),
    21: HwatuCard(
        code=21,
        month=HwatuMonth.JUNE,
        card_type=HwatuCardType.DDI,
        name_ko="6월 청단",
        name_en="Peony Blue Ribbon",
        fortune_meaning="명예로운 약속. 체면 유지의 관계.",
        keywords=["약속", "명예", "체면", "과시"],
    ),
    22: HwatuCard(
        code=22,
        month=HwatuMonth.JUNE,
        card_type=HwatuCardType.PI,
        name_ko="6월 피",
        name_en="Peony Junk",
        fortune_meaning="과시로 인한 소모.",
        keywords=["소모", "과시", "명예", "체면"],
    ),
    23: HwatuCard(
        code=23,
        month=HwatuMonth.JUNE,
        card_type=HwatuCardType.PI,
        name_ko="6월 피",
        name_en="Peony Junk",
        fortune_meaning="체면 유지의 작은 갈등.",
        keywords=["갈등", "체면", "화려함", "사소함"],
    ),
    # 7월 (싸리) - 24~27
    24: HwatuCard(
        code=24,
        month=HwatuMonth.JULY,
        card_type=HwatuCardType.YEOLKKEUT,
        name_ko="7월 멧돼지",
        name_en="Bush Clover Boar",
        fortune_meaning="변화와 이동 속 횡재의 실속.",
        keywords=["횡재", "변화", "이동", "현실"],
    ),
    25: HwatuCard(
        code=25,
        month=HwatuMonth.JULY,
        card_type=HwatuCardType.DDI,
        name_ko="7월 초단",
        name_en="Bush Clover Green Ribbon",
        fortune_meaning="변화의 약속. 이동과 관련된 관계.",
        keywords=["약속", "변화", "이동", "운"],
    ),
    26: HwatuCard(
        code=26,
        month=HwatuMonth.JULY,
        card_type=HwatuCardType.PI,
        name_ko="7월 피",
        name_en="Bush Clover Junk",
        fortune_meaning="변화 과정의 소모.",
        keywords=["소모", "변화", "이동", "불안"],
    ),
    27: HwatuCard(
        code=27,
        month=HwatuMonth.JULY,
        card_type=HwatuCardType.PI,
        name_ko="7월 피",
        name_en="Bush Clover Junk",
        fortune_meaning="이동 중 작은 문제.",
        keywords=["사소함", "이동", "변화", "소모"],
    ),
    # 8월 (공산) - 28~31
    28: HwatuCard(
        code=28,
        month=HwatuMonth.AUGUST,
        card_type=HwatuCardType.GWANG,
        name_ko="8월 광",
        name_en="Pampas Grass Bright",
        fortune_meaning="공허함 속 결정적 단절. 거리감의 중대한 선택.",
        keywords=["단절", "거리감", "공허", "결정적 사건"],
    ),
    29: HwatuCard(
        code=29,
        month=HwatuMonth.AUGUST,
        card_type=HwatuCardType.YEOLKKEUT,
        name_ko="8월 기러기",
        name_en="Pampas Grass Geese",
        fortune_meaning="고독 속 현실적 이익. 거리 두기의 균형.",
        keywords=["고독", "거리감", "현실", "단절"],
    ),
    30: HwatuCard(
        code=30,
        month=HwatuMonth.AUGUST,
        card_type=HwatuCardType.PI,
        name_ko="8월 피",
        name_en="Pampas Grass Junk",
        fortune_meaning="단절로 인한 감정 소모.",
        keywords=["소모", "단절", "고독", "공허"],
    ),
    31: HwatuCard(
        code=31,
        month=HwatuMonth.AUGUST,
        card_type=HwatuCardType.PI,
        name_ko="8월 피",
        name_en="Pampas Grass Junk",
        fortune_meaning="거리감의 작은 갈등.",
        keywords=["갈등", "거리감", "단절", "사소함"],
    ),
    # 9월 (국화) - 32~35
    32: HwatuCard(
        code=32,
        month=HwatuMonth.SEPTEMBER,
        card_type=HwatuCardType.YEOLKKEUT,
        name_ko="9월 국진",
        name_en="Chrysanthemum Cup",
        fortune_meaning="정리와 결론의 실속. 완성의 균형.",
        keywords=["정리", "결론", "완성", "현실"],
    ),
    33: HwatuCard(
        code=33,
        month=HwatuMonth.SEPTEMBER,
        card_type=HwatuCardType.DDI,
        name_ko="9월 청단",
        name_en="Chrysanthemum Blue Ribbon",
        fortune_meaning="마무리의 약속. 정리된 관계.",
        keywords=["약속", "정리", "마무리", "결론"],
    ),
    34: HwatuCard(
        code=34,
        month=HwatuMonth.SEPTEMBER,
        card_type=HwatuCardType.PI,
        name_ko="9월 피",
        name_en="Chrysanthemum Junk",
        fortune_meaning="정리 과정의 소모.",
        keywords=["소모", "정리", "마무리", "결론"],
    ),
    35: HwatuCard(
        code=35,
        month=HwatuMonth.SEPTEMBER,
        card_type=HwatuCardType.PI,
        name_ko="9월 피",
        name_en="Chrysanthemum Junk",
        fortune_meaning="완성 단계의 사소한 문제.",
        keywords=["사소함", "완성", "정리", "결론"],
    ),
    # 10월 (단풍) - 36~39
    36: HwatuCard(
        code=36,
        month=HwatuMonth.OCTOBER,
        card_type=HwatuCardType.YEOLKKEUT,
        name_ko="10월 사슴",
        name_en="Maple Deer",
        fortune_meaning="욕심과 거래의 현실적 이익. 계산된 균형.",
        keywords=["욕심", "거래", "이익", "현실"],
    ),
    37: HwatuCard(
        code=37,
        month=HwatuMonth.OCTOBER,
        card_type=HwatuCardType.DDI,
        name_ko="10월 청단",
        name_en="Maple Blue Ribbon",
        fortune_meaning="이익의 약속. 계산된 관계.",
        keywords=["약속", "이익", "거래", "욕심"],
    ),
    38: HwatuCard(
        code=38,
        month=HwatuMonth.OCTOBER,
        card_type=HwatuCardType.PI,
        name_ko="10월 피",
        name_en="Maple Junk",
        fortune_meaning="거래로 인한 소모.",
        keywords=["소모", "거래", "욕심", "계산"],
    ),
    39: HwatuCard(
        code=39,
        month=HwatuMonth.OCTOBER,
        card_type=HwatuCardType.PI,
        name_ko="10월 피",
        name_en="Maple Junk",
        fortune_meaning="욕심의 작은 갈등.",
        keywords=["갈등", "욕심", "이익", "사소함"],
    ),
    # 11월 (오동) - 40~43
    40: HwatuCard(
        code=40,
        month=HwatuMonth.NOVEMBER,
        card_type=HwatuCardType.GWANG,
        name_ko="11월 광",
        name_en="Paulownia Bright",
        fortune_meaning="보호와 성장의 강력한 힘. 금전 운의 결정적 사건.",
        keywords=["보호", "성장", "금전", "결정적 사건"],
    ),
    41: HwatuCard(
        code=41,
        month=HwatuMonth.NOVEMBER,
        card_type=HwatuCardType.YEOLKKEUT,
        name_ko="11월 오동열끗",
        name_en="Paulownia Junk",
        fortune_meaning="안정적 성장의 실속. 금전의 균형.",
        keywords=["성장", "금전", "안정", "현실"],
    ),
    42: HwatuCard(
        code=42,
        month=HwatuMonth.NOVEMBER,
        card_type=HwatuCardType.PI,
        name_ko="11월 피",
        name_en="Paulownia Junk",
        fortune_meaning="성장 과정의 소모.",
        keywords=["소모", "성장", "금전", "보호"],
    ),
    43: HwatuCard(
        code=43,
        month=HwatuMonth.NOVEMBER,
        card_type=HwatuCardType.PI,
        name_ko="11월 피",
        name_en="Paulownia Junk",
        fortune_meaning="안정 과정의 작은 문제.",
        keywords=["사소함", "안정", "성장", "금전"],
    ),
    # 12월 (비) - 44~47
    44: HwatuCard(
        code=44,
        month=HwatuMonth.DECEMBER,
        card_type=HwatuCardType.GWANG,
        name_ko="12월 광",
        name_en="Rain Bright",
        fortune_meaning="반복과 순환의 결정적 변화. 흐름 속 중대한 선택.",
        keywords=["반복", "순환", "흐름", "결정적 사건"],
    ),
    45: HwatuCard(
        code=45,
        month=HwatuMonth.DECEMBER,
        card_type=HwatuCardType.YEOLKKEUT,
        name_ko="12월 제비",
        name_en="Rain Swallow",
        fortune_meaning="연속적 흐름의 실속. 순환의 균형.",
        keywords=["흐름", "연속", "순환", "현실"],
    ),
    46: HwatuCard(
        code=46,
        month=HwatuMonth.DECEMBER,
        card_type=HwatuCardType.DDI,
        name_ko="12월 띠",
        name_en="Rain Ribbon",
        fortune_meaning="반복되는 약속. 순환하는 관계.",
        keywords=["약속", "반복", "순환", "흐름"],
    ),
    47: HwatuCard(
        code=47,
        month=HwatuMonth.DECEMBER,
        card_type=HwatuCardType.PI,
        name_ko="12월 피",
        name_en="Rain Junk",
        fortune_meaning="순환 과정의 소모.",
        keywords=["소모", "순환", "반복", "흐름"],
    ),
}


def get_card_by_code(code: int) -> HwatuCard:
    """card_code로 카드 정보 조회

    Args:
        code: 카드 코드 (0~47)

    Returns:
        카드 정보

    Raises:
        KeyError: 유효하지 않은 카드 코드인 경우
    """
    if code not in HWATU_CARDS:
        raise KeyError(f"유효하지 않은 카드 코드입니다: {code}")
    return HWATU_CARDS[code]


def get_cards_by_month(month: HwatuMonth) -> list[HwatuCard]:
    """월별 카드 4장 조회

    Args:
        month: 화투 월

    Returns:
        해당 월의 카드 4장 리스트
    """
    return [card for card in HWATU_CARDS.values() if card.month == month]


def get_month_fortune_meaning(month: HwatuMonth) -> str:
    """월별 점술 의미 반환

    Args:
        month: 화투 월

    Returns:
        월별 점술 의미
    """
    meanings = {
        HwatuMonth.JANUARY: "시작과 원칙. 고집스럽게 근본을 지키며 나아가는 운.",
        HwatuMonth.FEBRUARY: "인내와 준비. 사랑과 감성을 키우는 시간.",
        HwatuMonth.MARCH: "유혹과 불안정. 감정의 변화가 큰 시기.",
        HwatuMonth.APRIL: "관계의 얽힘. 집착과 구속이 나타나는 운.",
        HwatuMonth.MAY: "경쟁과 승부욕. 힘을 겨루며 도전하는 시기.",
        HwatuMonth.JUNE: "명예와 체면. 과시하고 화려함을 추구하는 운.",
        HwatuMonth.JULY: "변화와 이동. 횡재의 운이 따르는 시기.",
        HwatuMonth.AUGUST: "공허와 단절. 거리감을 느끼는 고독한 운.",
        HwatuMonth.SEPTEMBER: "정리와 결론. 일을 마무리하고 완성하는 시기.",
        HwatuMonth.OCTOBER: "욕심과 거래. 이익을 계산하며 움직이는 운.",
        HwatuMonth.NOVEMBER: "보호와 성장. 금전과 안정을 얻는 시기.",
        HwatuMonth.DECEMBER: "반복과 순환. 흐름을 타고 연속되는 운.",
    }
    return meanings[month]
