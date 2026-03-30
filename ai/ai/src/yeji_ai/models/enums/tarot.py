"""타로 Enum 정의

타로 카드, 스프레드 위치, 방향 등
"""

from enum import Enum


class CardTopic(str, Enum):
    """카드 리딩 주제 (질문 카테고리)"""

    MONEY = "MONEY"  # 금전운
    LOVE = "LOVE"  # 연애운
    CAREER = "CAREER"  # 직장운
    HEALTH = "HEALTH"  # 건강운
    STUDY = "STUDY"  # 학업운

    @property
    def label_ko(self) -> str:
        """한글 레이블"""
        _map = {
            "MONEY": "금전운",
            "LOVE": "연애운",
            "CAREER": "직장운",
            "HEALTH": "건강운",
            "STUDY": "학업운",
        }
        return _map[self.value]


class MajorArcana(str, Enum):
    """메이저 아르카나 22장"""

    FOOL = "FOOL"  # 0. 바보
    MAGICIAN = "MAGICIAN"  # 1. 마법사
    HIGH_PRIESTESS = "HIGH_PRIESTESS"  # 2. 여사제
    EMPRESS = "EMPRESS"  # 3. 여제
    EMPEROR = "EMPEROR"  # 4. 황제
    HIEROPHANT = "HIEROPHANT"  # 5. 교황
    LOVERS = "LOVERS"  # 6. 연인
    CHARIOT = "CHARIOT"  # 7. 전차
    STRENGTH = "STRENGTH"  # 8. 힘
    HERMIT = "HERMIT"  # 9. 은둔자
    WHEEL_OF_FORTUNE = "WHEEL_OF_FORTUNE"  # 10. 운명의 수레바퀴
    JUSTICE = "JUSTICE"  # 11. 정의
    HANGED_MAN = "HANGED_MAN"  # 12. 매달린 사람
    DEATH = "DEATH"  # 13. 죽음
    TEMPERANCE = "TEMPERANCE"  # 14. 절제
    DEVIL = "DEVIL"  # 15. 악마
    TOWER = "TOWER"  # 16. 탑
    STAR = "STAR"  # 17. 별
    MOON = "MOON"  # 18. 달
    SUN = "SUN"  # 19. 태양
    JUDGEMENT = "JUDGEMENT"  # 20. 심판
    WORLD = "WORLD"  # 21. 세계

    @property
    def number(self) -> int:
        """카드 번호"""
        _map = {
            "FOOL": 0,
            "MAGICIAN": 1,
            "HIGH_PRIESTESS": 2,
            "EMPRESS": 3,
            "EMPEROR": 4,
            "HIEROPHANT": 5,
            "LOVERS": 6,
            "CHARIOT": 7,
            "STRENGTH": 8,
            "HERMIT": 9,
            "WHEEL_OF_FORTUNE": 10,
            "JUSTICE": 11,
            "HANGED_MAN": 12,
            "DEATH": 13,
            "TEMPERANCE": 14,
            "DEVIL": 15,
            "TOWER": 16,
            "STAR": 17,
            "MOON": 18,
            "SUN": 19,
            "JUDGEMENT": 20,
            "WORLD": 21,
        }
        return _map[self.value]

    @property
    def label_ko(self) -> str:
        """한글 레이블"""
        _map = {
            "FOOL": "바보",
            "MAGICIAN": "마법사",
            "HIGH_PRIESTESS": "여사제",
            "EMPRESS": "여제",
            "EMPEROR": "황제",
            "HIEROPHANT": "교황",
            "LOVERS": "연인",
            "CHARIOT": "전차",
            "STRENGTH": "힘",
            "HERMIT": "은둔자",
            "WHEEL_OF_FORTUNE": "운명의 수레바퀴",
            "JUSTICE": "정의",
            "HANGED_MAN": "매달린 사람",
            "DEATH": "죽음",
            "TEMPERANCE": "절제",
            "DEVIL": "악마",
            "TOWER": "탑",
            "STAR": "별",
            "MOON": "달",
            "SUN": "태양",
            "JUDGEMENT": "심판",
            "WORLD": "세계",
        }
        return _map[self.value]

    @property
    def label_en(self) -> str:
        """영문 레이블"""
        return self.value.replace("_", " ").title()


class MinorSuit(str, Enum):
    """마이너 아르카나 수트 (4종)"""

    WANDS = "WANDS"  # 완드 (막대) - 불
    CUPS = "CUPS"  # 컵 (성배) - 물
    SWORDS = "SWORDS"  # 검 - 공기
    PENTACLES = "PENTACLES"  # 펜타클 (동전) - 흙

    @property
    def label_ko(self) -> str:
        """한글 레이블"""
        _map = {
            "WANDS": "완드",
            "CUPS": "컵",
            "SWORDS": "검",
            "PENTACLES": "펜타클",
        }
        return _map[self.value]

    @property
    def element(self) -> str:
        """원소 (ElementCode 값)"""
        _map = {
            "WANDS": "FIRE",
            "CUPS": "WATER",
            "SWORDS": "AIR",
            "PENTACLES": "EARTH",
        }
        return _map[self.value]

    @property
    def meaning(self) -> str:
        """의미 설명"""
        _map = {
            "WANDS": "열정, 창의성, 행동",
            "CUPS": "감정, 관계, 직관",
            "SWORDS": "지성, 소통, 결정",
            "PENTACLES": "물질, 안정, 실용",
        }
        return _map[self.value]


class MinorRank(str, Enum):
    """마이너 아르카나 랭크"""

    ACE = "ACE"  # 에이스
    TWO = "TWO"  # 2
    THREE = "THREE"  # 3
    FOUR = "FOUR"  # 4
    FIVE = "FIVE"  # 5
    SIX = "SIX"  # 6
    SEVEN = "SEVEN"  # 7
    EIGHT = "EIGHT"  # 8
    NINE = "NINE"  # 9
    TEN = "TEN"  # 10
    PAGE = "PAGE"  # 페이지 (시종)
    KNIGHT = "KNIGHT"  # 기사
    QUEEN = "QUEEN"  # 여왕
    KING = "KING"  # 왕

    @property
    def number(self) -> int | None:
        """숫자 (코트 카드는 None)"""
        _map = {
            "ACE": 1,
            "TWO": 2,
            "THREE": 3,
            "FOUR": 4,
            "FIVE": 5,
            "SIX": 6,
            "SEVEN": 7,
            "EIGHT": 8,
            "NINE": 9,
            "TEN": 10,
            "PAGE": None,
            "KNIGHT": None,
            "QUEEN": None,
            "KING": None,
        }
        return _map[self.value]

    @property
    def is_court(self) -> bool:
        """코트 카드 여부 (Page, Knight, Queen, King)"""
        return self.value in ["PAGE", "KNIGHT", "QUEEN", "KING"]

    @property
    def label_ko(self) -> str:
        """한글 레이블"""
        _map = {
            "ACE": "에이스",
            "TWO": "2",
            "THREE": "3",
            "FOUR": "4",
            "FIVE": "5",
            "SIX": "6",
            "SEVEN": "7",
            "EIGHT": "8",
            "NINE": "9",
            "TEN": "10",
            "PAGE": "페이지",
            "KNIGHT": "기사",
            "QUEEN": "여왕",
            "KING": "왕",
        }
        return _map[self.value]


class CardOrientation(str, Enum):
    """카드 방향"""

    UPRIGHT = "UPRIGHT"  # 정방향
    REVERSED = "REVERSED"  # 역방향

    @property
    def label_ko(self) -> str:
        """한글 레이블"""
        _map = {
            "UPRIGHT": "정방향",
            "REVERSED": "역방향",
        }
        return _map[self.value]

    @property
    def symbol(self) -> str:
        """심볼"""
        _map = {
            "UPRIGHT": "↑",
            "REVERSED": "↓",
        }
        return _map[self.value]


class SpreadPosition(str, Enum):
    """스프레드 위치 (3카드 스프레드)"""

    PAST = "PAST"  # 과거
    PRESENT = "PRESENT"  # 현재
    FUTURE = "FUTURE"  # 미래

    @property
    def label_ko(self) -> str:
        """한글 레이블"""
        _map = {
            "PAST": "과거",
            "PRESENT": "현재",
            "FUTURE": "미래",
        }
        return _map[self.value]

    @property
    def order(self) -> int:
        """순서"""
        _map = {
            "PAST": 1,
            "PRESENT": 2,
            "FUTURE": 3,
        }
        return _map[self.value]


class TarotBadge(str, Enum):
    """타로 전용 배지"""

    # 메이저 아르카나 강조
    MAJOR_ARCANA_HEAVY = "MAJOR_ARCANA_HEAVY"  # 메이저 2개 이상
    ALL_UPRIGHT = "ALL_UPRIGHT"  # 전부 정방향
    ALL_REVERSED = "ALL_REVERSED"  # 전부 역방향
    MIXED_ORIENTATION = "MIXED_ORIENTATION"  # 혼합

    # 수트 강조
    FIRE_DOMINANT = "FIRE_DOMINANT"  # 완드 우세
    WATER_DOMINANT = "WATER_DOMINANT"  # 컵 우세
    AIR_DOMINANT = "AIR_DOMINANT"  # 검 우세
    EARTH_DOMINANT = "EARTH_DOMINANT"  # 펜타클 우세

    # 코트 카드
    COURT_CARDS = "COURT_CARDS"  # 코트 카드 포함

    @property
    def label_ko(self) -> str:
        """한글 레이블"""
        _map = {
            "MAJOR_ARCANA_HEAVY": "메이저 아르카나 강조",
            "ALL_UPRIGHT": "전부 정방향",
            "ALL_REVERSED": "전부 역방향",
            "MIXED_ORIENTATION": "혼합 방향",
            "FIRE_DOMINANT": "완드 우세",
            "WATER_DOMINANT": "컵 우세",
            "AIR_DOMINANT": "검 우세",
            "EARTH_DOMINANT": "펜타클 우세",
            "COURT_CARDS": "코트 카드",
        }
        return _map.get(self.value, self.value)
