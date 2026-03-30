"""궁합 서비스 - 점수 계산 + 메시지 풀 기반 응답 생성

두 사람의 생년월일을 받아 궁합 점수를 계산하고,
해당 점수 구간의 메시지 풀에서 랜덤 메시지를 반환합니다.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

import structlog

logger = structlog.get_logger()

# ============================================================
# 상수 정의
# ============================================================

# 천간 (10개)
CHEON_GAN_CODES = ["GAP", "EUL", "BYEONG", "JEONG", "MU", "GI", "GYEONG", "SIN", "IM", "GYE"]

# 지지 (12개)
JI_JI_CODES = ["JA", "CHUK", "IN", "MYO", "JIN", "SA", "O", "MI", "SHIN", "YU", "SUL", "HAE"]

# 천간 → 오행 매핑
CHEON_GAN_TO_ELEMENT = {
    "GAP": "WOOD", "EUL": "WOOD",
    "BYEONG": "FIRE", "JEONG": "FIRE",
    "MU": "EARTH", "GI": "EARTH",
    "GYEONG": "METAL", "SIN": "METAL",
    "IM": "WATER", "GYE": "WATER",
}

# 지지 → 오행 매핑
JI_JI_TO_ELEMENT = {
    "IN": "WOOD", "MYO": "WOOD",
    "SA": "FIRE", "O": "FIRE",
    "JIN": "EARTH", "SUL": "EARTH",
    "CHUK": "EARTH", "MI": "EARTH",
    "SHIN": "METAL", "YU": "METAL",
    "HAE": "WATER", "JA": "WATER",
}

# 오행 상생/상극
SANG_SAENG = {"WOOD": "FIRE", "FIRE": "EARTH", "EARTH": "METAL", "METAL": "WATER", "WATER": "WOOD"}
SANG_GEUK = {"WOOD": "EARTH", "FIRE": "METAL", "EARTH": "WATER", "METAL": "WOOD", "WATER": "FIRE"}

# 지지 관계
JI_JI_YUKAP = [("JA", "CHUK"), ("IN", "HAE"), ("MYO", "SUL"), ("JIN", "YU"), ("SA", "SHIN"), ("O", "MI")]
JI_JI_SAMHAP = [("IN", "O", "SUL"), ("HAE", "MYO", "MI"), ("SHIN", "JA", "JIN"), ("SA", "YU", "CHUK")]
JI_JI_CHUNG = [("JA", "O"), ("CHUK", "MI"), ("IN", "SHIN"), ("MYO", "YU"), ("JIN", "SUL"), ("SA", "HAE")]

# 별자리
ZODIAC_SIGNS = ["ARIES", "TAURUS", "GEMINI", "CANCER", "LEO", "VIRGO",
                "LIBRA", "SCORPIO", "SAGITTARIUS", "CAPRICORN", "AQUARIUS", "PISCES"]

ZODIAC_TO_ELEMENT = {
    "ARIES": "FIRE", "LEO": "FIRE", "SAGITTARIUS": "FIRE",
    "TAURUS": "EARTH", "VIRGO": "EARTH", "CAPRICORN": "EARTH",
    "GEMINI": "AIR", "LIBRA": "AIR", "AQUARIUS": "AIR",
    "CANCER": "WATER", "SCORPIO": "WATER", "PISCES": "WATER",
}

ZODIAC_TO_MODALITY = {
    "ARIES": "CARDINAL", "CANCER": "CARDINAL", "LIBRA": "CARDINAL", "CAPRICORN": "CARDINAL",
    "TAURUS": "FIXED", "LEO": "FIXED", "SCORPIO": "FIXED", "AQUARIUS": "FIXED",
    "GEMINI": "MUTABLE", "VIRGO": "MUTABLE", "SAGITTARIUS": "MUTABLE", "PISCES": "MUTABLE",
}

# 점수표
ZODIAC_COMPATIBILITY = {0: 85, 1: 65, 2: 80, 3: 55, 4: 90, 5: 65, 6: 70}

WESTERN_ELEMENT_COMPATIBILITY = {
    ("AIR", "AIR"): 80, ("AIR", "EARTH"): 55, ("AIR", "FIRE"): 90, ("AIR", "WATER"): 65,
    ("EARTH", "EARTH"): 85, ("EARTH", "FIRE"): 60, ("EARTH", "WATER"): 90,
    ("FIRE", "FIRE"): 80, ("FIRE", "WATER"): 50, ("WATER", "WATER"): 80,
}

MODALITY_COMPATIBILITY = {
    ("CARDINAL", "CARDINAL"): 65, ("CARDINAL", "FIXED"): 75, ("CARDINAL", "MUTABLE"): 85,
    ("FIXED", "FIXED"): 60, ("FIXED", "MUTABLE"): 80, ("MUTABLE", "MUTABLE"): 70,
}

LIFE_PATH_COMPATIBILITY = {
    (1, 1): 70, (1, 2): 65, (1, 3): 85, (1, 4): 60, (1, 5): 90,
    (1, 6): 75, (1, 7): 70, (1, 8): 80, (1, 9): 85,
    (2, 2): 80, (2, 3): 75, (2, 4): 85, (2, 5): 65, (2, 6): 90,
    (2, 7): 75, (2, 8): 80, (2, 9): 70,
    (3, 3): 85, (3, 4): 60, (3, 5): 90, (3, 6): 85, (3, 7): 70,
    (3, 8): 65, (3, 9): 80,
    (4, 4): 75, (4, 5): 55, (4, 6): 80, (4, 7): 85, (4, 8): 90, (4, 9): 65,
    (5, 5): 70, (5, 6): 65, (5, 7): 80, (5, 8): 75, (5, 9): 85,
    (6, 6): 85, (6, 7): 70, (6, 8): 75, (6, 9): 90,
    (7, 7): 80, (7, 8): 65, (7, 9): 75,
    (8, 8): 85, (8, 9): 70,
    (9, 9): 80,
}

# 점수 구간
SCORE_RANGES = [
    ("excellent", 90, 100),
    ("good", 70, 89),
    ("average", 50, 69),
    ("challenging", 30, 49),
    ("difficult", 0, 29),
]


# ============================================================
# 데이터 클래스
# ============================================================

@dataclass
class PersonInput:
    """궁합 요청용 개인 정보"""
    birth_date: str  # YYYY-MM-DD
    gender: Literal["M", "F"] | None = None
    name: str | None = None


@dataclass
class CompatibilityResult:
    """궁합 결과"""
    score: int
    grade: str
    grade_label: str
    east_score: int
    west_score: int
    message: dict[str, Any]


# ============================================================
# 메시지 풀 로더
# ============================================================

class MessagePoolLoader:
    """메시지 풀 싱글톤 로더"""

    _instance: MessagePoolLoader | None = None
    _pool: dict[str, list[dict]] | None = None

    def __new__(cls) -> MessagePoolLoader:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load(self, path: str | Path | None = None) -> dict[str, list[dict]]:
        """메시지 풀 로드 (캐싱)"""
        if self._pool is not None:
            return self._pool

        if path is None:
            # 기본 경로: src/yeji_ai 기준으로 data 폴더
            base_dir = Path(__file__).parent.parent.parent.parent  # ai/
            path = base_dir / "data" / "message_pool.json"

        path = Path(path)
        if not path.exists():
            logger.warning("message_pool_not_found", path=str(path))
            return {}

        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        self._pool = data.get("pool", {})
        logger.info("message_pool_loaded",
                   total=sum(len(v) for v in self._pool.values()),
                   ranges=list(self._pool.keys()))
        return self._pool

    def get_random_message(self, grade: str) -> dict[str, Any] | None:
        """해당 등급에서 랜덤 메시지 반환"""
        pool = self.load()
        messages = pool.get(grade, [])
        if not messages:
            logger.warning("no_messages_for_grade", grade=grade)
            return None
        return random.choice(messages)


# ============================================================
# 계산 함수
# ============================================================

def get_day_master_from_birth(birth_date: str) -> tuple[str, str]:
    """생년월일로 일간/일지 계산"""
    year, month, day = map(int, birth_date.split("-"))
    base_date = datetime(1900, 1, 1)
    target_date = datetime(year, month, day)
    days_diff = (target_date - base_date).days

    gan_index = days_diff % 10
    ji_index = days_diff % 12

    return CHEON_GAN_CODES[gan_index], JI_JI_CODES[ji_index]


def get_zodiac_sign(birth_date: str) -> str:
    """생년월일로 태양 별자리 계산"""
    month, day = int(birth_date.split("-")[1]), int(birth_date.split("-")[2])

    zodiac_dates = [
        (1, 20, 2, 18, "AQUARIUS"), (2, 19, 3, 20, "PISCES"),
        (3, 21, 4, 19, "ARIES"), (4, 20, 5, 20, "TAURUS"),
        (5, 21, 6, 20, "GEMINI"), (6, 21, 7, 22, "CANCER"),
        (7, 23, 8, 22, "LEO"), (8, 23, 9, 22, "VIRGO"),
        (9, 23, 10, 22, "LIBRA"), (10, 23, 11, 21, "SCORPIO"),
        (11, 22, 12, 21, "SAGITTARIUS"), (12, 22, 1, 19, "CAPRICORN"),
    ]

    for start_m, start_d, end_m, end_d, sign in zodiac_dates:
        if start_m == 12 and end_m == 1:
            if (month == 12 and day >= start_d) or (month == 1 and day <= end_d):
                return sign
        elif (month == start_m and day >= start_d) or (month == end_m and day <= end_d):
            return sign

    return "ARIES"


def calculate_life_path_number(birth_date: str) -> int:
    """생년월일로 생명수 계산"""
    digits = [int(d) for d in birth_date.replace("-", "")]
    total = sum(digits)

    while total > 9 and total not in (11, 22, 33):
        total = sum(int(d) for d in str(total))

    return total


def calculate_element_balance(birth_date: str) -> dict[str, int]:
    """오행 균형 계산"""
    gan_code, ji_code = get_day_master_from_birth(birth_date)

    balance = {"WOOD": 20, "FIRE": 20, "EARTH": 20, "METAL": 20, "WATER": 20}
    balance[CHEON_GAN_TO_ELEMENT[gan_code]] += 30
    balance[JI_JI_TO_ELEMENT[ji_code]] += 20

    total = sum(balance.values())
    return {k: int(v / total * 100) for k, v in balance.items()}


# 점수 계산 함수들
def calc_day_master_score(elem1: str, elem2: str) -> int:
    """일간 오행 점수 (20점 만점)"""
    if elem1 == elem2:
        return 15
    if SANG_SAENG.get(elem1) == elem2:
        return 18
    if SANG_SAENG.get(elem2) == elem1:
        return 20
    if SANG_GEUK.get(elem1) == elem2:
        return 10
    if SANG_GEUK.get(elem2) == elem1:
        return 8
    return 12


def calc_element_balance_score(balance1: dict, balance2: dict) -> int:
    """오행 보완 점수 (15점 만점)"""
    score = 0
    weak1, strong1 = min(balance1, key=balance1.get), max(balance1, key=balance1.get)
    weak2, strong2 = min(balance2, key=balance2.get), max(balance2, key=balance2.get)

    if strong1 == weak2:
        score += 5
    if strong2 == weak1:
        score += 5

    diff_sum = sum(abs(balance1[e] - balance2[e]) for e in balance1)
    if diff_sum < 50:
        score += 5
    elif diff_sum < 100:
        score += 3
    else:
        score += 1

    return min(15, score)


def calc_branch_relation_score(ji1: str, ji2: str) -> int:
    """지지 충합 점수 (15점 만점)"""
    for pair in JI_JI_YUKAP:
        if (ji1, ji2) in [pair, pair[::-1]]:
            return 15
    for trio in JI_JI_SAMHAP:
        if ji1 in trio and ji2 in trio:
            return 12
    for pair in JI_JI_CHUNG:
        if (ji1, ji2) in [pair, pair[::-1]]:
            return 5
    return 10


def calc_zodiac_score(sign1: str, sign2: str) -> int:
    """별자리 궁합 점수 (20점 만점)"""
    idx1 = ZODIAC_SIGNS.index(sign1)
    idx2 = ZODIAC_SIGNS.index(sign2)
    distance = min(abs(idx1 - idx2), 12 - abs(idx1 - idx2))
    base_score = ZODIAC_COMPATIBILITY.get(distance, 70)
    return int(base_score / 100 * 20)


def calc_western_element_score(elem1: str, elem2: str) -> int:
    """서양 원소 점수 (15점 만점)"""
    key = tuple(sorted([elem1, elem2]))
    base_score = WESTERN_ELEMENT_COMPATIBILITY.get(key, 70)
    return int(base_score / 100 * 15)


def calc_modality_score(mod1: str, mod2: str) -> int:
    """양태 점수 (10점 만점)"""
    key = tuple(sorted([mod1, mod2]))
    base_score = MODALITY_COMPATIBILITY.get(key, 70)
    return int(base_score / 100 * 10)


def calc_life_path_score(num1: int, num2: int) -> int:
    """생명수 점수 (5점 만점)"""
    def reduce(n):
        while n > 9 and n not in (11, 22, 33):
            n = sum(int(d) for d in str(n))
        return n

    n1, n2 = reduce(num1), reduce(num2)
    key = (min(n1, n2), max(n1, n2))
    base_score = LIFE_PATH_COMPATIBILITY.get(key, 70)
    return int(base_score / 100 * 5)


def get_grade_from_score(score: int) -> tuple[str, str]:
    """점수로 등급 결정"""
    for grade, min_score, max_score in SCORE_RANGES:
        if min_score <= score <= max_score:
            labels = {
                "excellent": "천생연분",
                "good": "좋은 궁합",
                "average": "보통",
                "challenging": "노력 필요",
                "difficult": "상극",
            }
            return grade, labels[grade]
    return "average", "보통"


# ============================================================
# 메인 서비스 함수
# ============================================================

def calculate_compatibility(
    person1: PersonInput,
    person2: PersonInput,
) -> CompatibilityResult:
    """궁합 점수 계산 및 메시지 반환

    Args:
        person1: 첫 번째 사람 정보
        person2: 두 번째 사람 정보

    Returns:
        점수, 등급, 메시지를 포함한 결과
    """
    # 동양 데이터
    gan1, ji1 = get_day_master_from_birth(person1.birth_date)
    gan2, ji2 = get_day_master_from_birth(person2.birth_date)
    elem1 = CHEON_GAN_TO_ELEMENT[gan1]
    elem2 = CHEON_GAN_TO_ELEMENT[gan2]
    balance1 = calculate_element_balance(person1.birth_date)
    balance2 = calculate_element_balance(person2.birth_date)

    # 서양 데이터
    sign1 = get_zodiac_sign(person1.birth_date)
    sign2 = get_zodiac_sign(person2.birth_date)
    west_elem1 = ZODIAC_TO_ELEMENT[sign1]
    west_elem2 = ZODIAC_TO_ELEMENT[sign2]
    mod1 = ZODIAC_TO_MODALITY[sign1]
    mod2 = ZODIAC_TO_MODALITY[sign2]
    life1 = calculate_life_path_number(person1.birth_date)
    life2 = calculate_life_path_number(person2.birth_date)

    # 동양 점수 (50점)
    east_day_master = calc_day_master_score(elem1, elem2)
    east_element = calc_element_balance_score(balance1, balance2)
    east_branch = calc_branch_relation_score(ji1, ji2)
    east_total = east_day_master + east_element + east_branch

    # 서양 점수 (50점)
    west_zodiac = calc_zodiac_score(sign1, sign2)
    west_element = calc_western_element_score(west_elem1, west_elem2)
    west_modality = calc_modality_score(mod1, mod2)
    west_numerology = calc_life_path_score(life1, life2)
    west_total = west_zodiac + west_element + west_modality + west_numerology

    # 총점
    total_score = east_total + west_total
    grade, grade_label = get_grade_from_score(total_score)

    # 메시지 풀에서 랜덤 메시지 가져오기
    loader = MessagePoolLoader()
    message = loader.get_random_message(grade)

    if message is None:
        # 풀백 메시지
        message = {
            "east": {
                "relationship_dynamics": {},
                "compatibility_summary": {
                    "keywords": [grade_label],
                    "desc": f"두 분의 궁합 점수는 {total_score}점입니다.",
                },
            },
            "west": {
                "zodiac": {"aspects": {}},
                "numerology": {},
            },
        }

    logger.info(
        "compatibility_calculated",
        score=total_score,
        grade=grade,
        east=east_total,
        west=west_total,
    )

    return CompatibilityResult(
        score=total_score,
        grade=grade,
        grade_label=grade_label,
        east_score=east_total,
        west_score=west_total,
        message=message,
    )
