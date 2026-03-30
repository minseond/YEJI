"""궁합 점수 기계적 계산 모듈

두 사람의 사주/점성 데이터를 비교하여 기계적으로 궁합 점수를 산출합니다.
LLM은 이 점수를 기반으로 설명만 생성합니다.

점수 체계:
- 동양 궁합: 50점 만점
  - 일간 상생상극: 20점
  - 오행 보완: 15점
  - 지지 충합: 15점
- 서양 궁합: 50점 만점
  - 태양 별자리: 20점
  - 4원소 조화: 15점
  - 양태 조화: 10점
  - 수비학: 5점
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

# ============================================================
# 상수 정의
# ============================================================

# 천간 (10개)
CHEON_GAN = ["갑", "을", "병", "정", "무", "기", "경", "신", "임", "계"]
CHEON_GAN_CODES = ["GAP", "EUL", "BYEONG", "JEONG", "MU", "GI", "GYEONG", "SIN", "IM", "GYE"]

# 지지 (12개)
JI_JI = ["자", "축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해"]
JI_JI_CODES = ["JA", "CHUK", "IN", "MYO", "JIN", "SA", "O", "MI", "SHIN", "YU", "SUL", "HAE"]

# 천간 → 오행 매핑
CHEON_GAN_TO_ELEMENT = {
    "GAP": "WOOD", "EUL": "WOOD",      # 갑을 → 목
    "BYEONG": "FIRE", "JEONG": "FIRE", # 병정 → 화
    "MU": "EARTH", "GI": "EARTH",      # 무기 → 토
    "GYEONG": "METAL", "SIN": "METAL", # 경신 → 금
    "IM": "WATER", "GYE": "WATER",     # 임계 → 수
}

# 지지 → 오행 매핑
JI_JI_TO_ELEMENT = {
    "IN": "WOOD", "MYO": "WOOD",       # 인묘 → 목
    "SA": "FIRE", "O": "FIRE",         # 사오 → 화
    "JIN": "EARTH", "SUL": "EARTH",    # 진술 → 토
    "CHUK": "EARTH", "MI": "EARTH",    # 축미 → 토
    "SHIN": "METAL", "YU": "METAL",    # 신유 → 금
    "HAE": "WATER", "JA": "WATER",     # 해자 → 수
}

# 오행 상생 관계 (A → B: A가 B를 생함)
SANG_SAENG = {
    "WOOD": "FIRE",   # 목생화
    "FIRE": "EARTH",  # 화생토
    "EARTH": "METAL", # 토생금
    "METAL": "WATER", # 금생수
    "WATER": "WOOD",  # 수생목
}

# 오행 상극 관계 (A → B: A가 B를 극함)
SANG_GEUK = {
    "WOOD": "EARTH",  # 목극토
    "FIRE": "METAL",  # 화극금
    "EARTH": "WATER", # 토극수
    "METAL": "WOOD",  # 금극목
    "WATER": "FIRE",  # 수극화
}

# 지지 육합 (가장 좋은 관계)
JI_JI_YUKAP = [
    ("JA", "CHUK"),   # 자축합
    ("IN", "HAE"),    # 인해합
    ("MYO", "SUL"),   # 묘술합
    ("JIN", "YU"),    # 진유합
    ("SA", "SHIN"),   # 사신합
    ("O", "MI"),      # 오미합
]

# 지지 삼합 (좋은 관계)
JI_JI_SAMHAP = [
    ("IN", "O", "SUL"),    # 인오술 화국
    ("HAE", "MYO", "MI"),  # 해묘미 목국
    ("SHIN", "JA", "JIN"), # 신자진 수국
    ("SA", "YU", "CHUK"),  # 사유축 금국
]

# 지지 충 (나쁜 관계)
JI_JI_CHUNG = [
    ("JA", "O"),      # 자오충
    ("CHUK", "MI"),   # 축미충
    ("IN", "SHIN"),   # 인신충
    ("MYO", "YU"),    # 묘유충
    ("JIN", "SUL"),   # 진술충
    ("SA", "HAE"),    # 사해충
]

# 12별자리
ZODIAC_SIGNS = [
    "ARIES", "TAURUS", "GEMINI", "CANCER",
    "LEO", "VIRGO", "LIBRA", "SCORPIO",
    "SAGITTARIUS", "CAPRICORN", "AQUARIUS", "PISCES"
]

# 별자리 → 원소
ZODIAC_TO_ELEMENT = {
    "ARIES": "FIRE", "LEO": "FIRE", "SAGITTARIUS": "FIRE",
    "TAURUS": "EARTH", "VIRGO": "EARTH", "CAPRICORN": "EARTH",
    "GEMINI": "AIR", "LIBRA": "AIR", "AQUARIUS": "AIR",
    "CANCER": "WATER", "SCORPIO": "WATER", "PISCES": "WATER",
}

# 별자리 → 양태
ZODIAC_TO_MODALITY = {
    "ARIES": "CARDINAL", "CANCER": "CARDINAL", "LIBRA": "CARDINAL", "CAPRICORN": "CARDINAL",
    "TAURUS": "FIXED", "LEO": "FIXED", "SCORPIO": "FIXED", "AQUARIUS": "FIXED",
    "GEMINI": "MUTABLE", "VIRGO": "MUTABLE", "SAGITTARIUS": "MUTABLE", "PISCES": "MUTABLE",
}

# 별자리 궁합 점수표 (전통 점성술 기반)
# 0: 같은 별자리, 1-6: 거리 (트라인=4, 스퀘어=3, 섹스타일=2, 컨정션=0, 오포지션=6)
ZODIAC_COMPATIBILITY = {
    0: 85,   # 같은 별자리 (합)
    1: 65,   # 30도 (세미섹스타일)
    2: 80,   # 60도 (섹스타일) - 좋음
    3: 55,   # 90도 (스퀘어) - 긴장
    4: 90,   # 120도 (트라인) - 최고
    5: 65,   # 150도 (퀸컹스)
    6: 70,   # 180도 (오포지션) - 끌림+긴장
}

# 서양 원소 궁합
WESTERN_ELEMENT_COMPATIBILITY = {
    ("FIRE", "FIRE"): 80,
    ("FIRE", "AIR"): 90,   # 불+공기 = 상생
    ("FIRE", "EARTH"): 60,
    ("FIRE", "WATER"): 50, # 불+물 = 상극
    ("AIR", "AIR"): 80,
    ("AIR", "EARTH"): 55,
    ("AIR", "WATER"): 65,
    ("EARTH", "EARTH"): 85,
    ("EARTH", "WATER"): 90, # 흙+물 = 상생
    ("WATER", "WATER"): 80,
}

# 양태 궁합
MODALITY_COMPATIBILITY = {
    ("CARDINAL", "CARDINAL"): 65,  # 둘 다 리더 → 충돌
    ("CARDINAL", "FIXED"): 75,     # 시작+유지 = 보완
    ("CARDINAL", "MUTABLE"): 85,   # 시작+적응 = 좋음
    ("FIXED", "FIXED"): 60,        # 둘 다 고집 → 충돌
    ("FIXED", "MUTABLE"): 80,      # 안정+유연 = 보완
    ("MUTABLE", "MUTABLE"): 70,    # 둘 다 변화 → 불안정
}

# 생명수 궁합
LIFE_PATH_COMPATIBILITY = {
    (1, 1): 70, (1, 2): 65, (1, 3): 85, (1, 4): 60, (1, 5): 90,
    (1, 6): 75, (1, 7): 70, (1, 8): 80, (1, 9): 85,
    (2, 2): 80, (2, 3): 75, (2, 4): 85, (2, 5): 65, (2, 6): 90,
    (2, 7): 75, (2, 8): 80, (2, 9): 70,
    (3, 3): 85, (3, 4): 60, (3, 5): 90, (3, 6): 85, (3, 7): 70,
    (3, 8): 65, (3, 9): 80,
    (4, 4): 75, (4, 5): 55, (4, 6): 80, (4, 7): 85, (4, 8): 90,
    (4, 9): 65,
    (5, 5): 70, (5, 6): 65, (5, 7): 80, (5, 8): 75, (5, 9): 85,
    (6, 6): 85, (6, 7): 70, (6, 8): 75, (6, 9): 90,
    (7, 7): 80, (7, 8): 65, (7, 9): 75,
    (8, 8): 85, (8, 9): 70,
    (9, 9): 80,
    # 마스터 넘버
    (11, 11): 90, (11, 22): 85, (11, 33): 80,
    (22, 22): 85, (22, 33): 90,
    (33, 33): 95,
}


# ============================================================
# 데이터 클래스
# ============================================================

@dataclass
class PersonData:
    """개인 데이터"""
    name: str
    gender: Literal["M", "F"]
    birth_date: str  # YYYY-MM-DD
    birth_time: str | None  # HH:MM or None


@dataclass
class EasternData:
    """동양 사주 분석 결과"""
    day_master_code: str  # 일간 코드 (GAP~GYE)
    day_master_element: str  # 일간 오행 (WOOD~WATER)
    day_branch_code: str  # 일지 코드 (JA~HAE)
    strong_element: str  # 가장 강한 오행
    weak_element: str  # 가장 약한 오행
    element_balance: dict[str, int]  # 오행별 비율


@dataclass
class WesternData:
    """서양 점성술 분석 결과"""
    sun_sign: str  # 태양 별자리
    sun_element: str  # 태양 원소
    sun_modality: str  # 태양 양태
    life_path_number: int  # 생명수


@dataclass
class CompatibilityScores:
    """궁합 점수 결과"""
    # 동양 (50점 만점)
    east_day_master: int  # 일간 상생상극 (20점)
    east_element_balance: int  # 오행 보완 (15점)
    east_branch_relation: int  # 지지 충합 (15점)
    east_total: int  # 동양 총점 (50점)

    # 서양 (50점 만점)
    west_zodiac: int  # 별자리 궁합 (20점)
    west_element: int  # 원소 조화 (15점)
    west_modality: int  # 양태 조화 (10점)
    west_numerology: int  # 수비학 (5점)
    west_total: int  # 서양 총점 (50점)

    # 종합
    total: int  # 총점 (100점)


# ============================================================
# 계산 함수
# ============================================================

def get_day_master_from_birth(birth_date: str) -> tuple[str, str]:
    """생년월일로 일간/일지 계산 (간단 버전)

    실제로는 만세력 라이브러리를 사용해야 하지만,
    여기서는 간단한 계산으로 대체합니다.
    """
    # 실제 구현에서는 yeji_ai.engine.saju_calculator 사용
    # 여기서는 테스트용 간단 계산
    year, month, day = map(int, birth_date.split("-"))

    # 일진 계산 (간략화된 버전)
    # 실제로는 만세력 데이터 필요
    base_date = datetime(1900, 1, 1)  # 기준일: 1900-01-01 = 갑자일
    target_date = datetime(year, month, day)
    days_diff = (target_date - base_date).days

    gan_index = days_diff % 10
    ji_index = days_diff % 12

    return CHEON_GAN_CODES[gan_index], JI_JI_CODES[ji_index]


def get_zodiac_sign(birth_date: str) -> str:
    """생년월일로 태양 별자리 계산"""
    month, day = int(birth_date.split("-")[1]), int(birth_date.split("-")[2])

    zodiac_dates = [
        (1, 20, 2, 18, "AQUARIUS"),
        (2, 19, 3, 20, "PISCES"),
        (3, 21, 4, 19, "ARIES"),
        (4, 20, 5, 20, "TAURUS"),
        (5, 21, 6, 20, "GEMINI"),
        (6, 21, 7, 22, "CANCER"),
        (7, 23, 8, 22, "LEO"),
        (8, 23, 9, 22, "VIRGO"),
        (9, 23, 10, 22, "LIBRA"),
        (10, 23, 11, 21, "SCORPIO"),
        (11, 22, 12, 21, "SAGITTARIUS"),
        (12, 22, 1, 19, "CAPRICORN"),
    ]

    for start_m, start_d, end_m, end_d, sign in zodiac_dates:
        if start_m == 12 and end_m == 1:
            if (month == 12 and day >= start_d) or (month == 1 and day <= end_d):
                return sign
        elif (month == start_m and day >= start_d) or (month == end_m and day <= end_d):
            return sign

    return "ARIES"  # 기본값


def calculate_life_path_number(birth_date: str) -> int:
    """생년월일로 생명수 계산"""
    digits = [int(d) for d in birth_date.replace("-", "")]
    total = sum(digits)

    # 마스터 넘버 체크 (11, 22, 33)
    while total > 9 and total not in (11, 22, 33):
        total = sum(int(d) for d in str(total))

    return total


def calculate_element_balance(birth_date: str) -> dict[str, int]:
    """오행 균형 계산 (간략화)"""
    # 실제로는 사주팔자 8글자 모두 분석
    # 여기서는 간단히 일간 기준으로만 계산
    gan_code, ji_code = get_day_master_from_birth(birth_date)

    balance = {"WOOD": 20, "FIRE": 20, "EARTH": 20, "METAL": 20, "WATER": 20}

    # 일간 오행 강화
    day_element = CHEON_GAN_TO_ELEMENT.get(gan_code, "WOOD")
    balance[day_element] += 30

    # 일지 오행 강화
    branch_element = JI_JI_TO_ELEMENT.get(ji_code, "WOOD")
    balance[branch_element] += 20

    # 정규화
    total = sum(balance.values())
    return {k: int(v / total * 100) for k, v in balance.items()}


# ============================================================
# 궁합 점수 계산
# ============================================================

def calc_day_master_score(elem1: str, elem2: str) -> int:
    """일간 오행 상생상극 점수 (20점 만점)"""
    # 같은 오행 (비화)
    if elem1 == elem2:
        return 15  # 75%

    # 상생 관계 (내가 생해주거나 생해받거나)
    if SANG_SAENG.get(elem1) == elem2:
        return 18  # 90% - 내가 생해줌
    if SANG_SAENG.get(elem2) == elem1:
        return 20  # 100% - 상대가 생해줌 (최고)

    # 상극 관계
    if SANG_GEUK.get(elem1) == elem2:
        return 10  # 50% - 내가 극함
    if SANG_GEUK.get(elem2) == elem1:
        return 8   # 40% - 내가 극당함 (최악)

    return 12  # 기본값


def calc_element_balance_score(balance1: dict, balance2: dict) -> int:
    """오행 보완 점수 (15점 만점)

    한 사람의 약한 오행을 다른 사람이 보완해주는지 확인
    """
    score = 0

    # 각자의 가장 약한/강한 오행 찾기
    weak1 = min(balance1, key=balance1.get)
    strong1 = max(balance1, key=balance1.get)
    weak2 = min(balance2, key=balance2.get)
    strong2 = max(balance2, key=balance2.get)

    # 서로의 약점을 보완하는지 확인
    if strong1 == weak2:
        score += 5  # 내 강점이 상대 약점 보완
    if strong2 == weak1:
        score += 5  # 상대 강점이 내 약점 보완

    # 오행 분포 유사도 (너무 다르면 감점)
    diff_sum = sum(abs(balance1[e] - balance2[e]) for e in balance1)
    if diff_sum < 50:
        score += 5  # 균형 잡힌 조합
    elif diff_sum < 100:
        score += 3
    else:
        score += 1

    return min(15, score)


def calc_branch_relation_score(ji1: str, ji2: str) -> int:
    """지지 충합 점수 (15점 만점)"""
    # 육합 (최고)
    for pair in JI_JI_YUKAP:
        if (ji1, ji2) in [pair, pair[::-1]]:
            return 15  # 100%

    # 삼합 (좋음)
    for trio in JI_JI_SAMHAP:
        if ji1 in trio and ji2 in trio:
            return 12  # 80%

    # 충 (나쁨)
    for pair in JI_JI_CHUNG:
        if (ji1, ji2) in [pair, pair[::-1]]:
            return 5   # 33%

    # 일반
    return 10  # 67%


def calc_zodiac_score(sign1: str, sign2: str) -> int:
    """별자리 궁합 점수 (20점 만점)"""
    idx1 = ZODIAC_SIGNS.index(sign1)
    idx2 = ZODIAC_SIGNS.index(sign2)

    # 거리 계산 (0-6)
    distance = min(abs(idx1 - idx2), 12 - abs(idx1 - idx2))

    # 점수 변환 (100점 → 20점)
    base_score = ZODIAC_COMPATIBILITY.get(distance, 70)
    return int(base_score / 100 * 20)


def calc_western_element_score(elem1: str, elem2: str) -> int:
    """서양 원소 궁합 점수 (15점 만점)"""
    key = (elem1, elem2) if elem1 <= elem2 else (elem2, elem1)
    base_score = WESTERN_ELEMENT_COMPATIBILITY.get(key, 70)
    return int(base_score / 100 * 15)


def calc_modality_score(mod1: str, mod2: str) -> int:
    """양태 궁합 점수 (10점 만점)"""
    key = (mod1, mod2) if mod1 <= mod2 else (mod2, mod1)
    base_score = MODALITY_COMPATIBILITY.get(key, 70)
    return int(base_score / 100 * 10)


def calc_life_path_score(num1: int, num2: int) -> int:
    """생명수 궁합 점수 (5점 만점)"""
    # 마스터 넘버를 기본 수로 변환
    def reduce(n):
        if n in (11, 22, 33):
            return n
        while n > 9:
            n = sum(int(d) for d in str(n))
        return n

    n1, n2 = reduce(num1), reduce(num2)
    key = (min(n1, n2), max(n1, n2))

    base_score = LIFE_PATH_COMPATIBILITY.get(key, 70)
    return int(base_score / 100 * 5)


# ============================================================
# 메인 계산 함수
# ============================================================

def calculate_compatibility(
    person1: PersonData,
    person2: PersonData,
) -> tuple[CompatibilityScores, EasternData, EasternData, WesternData, WesternData]:
    """두 사람의 궁합 점수 계산

    Returns:
        (점수, 사람1_동양데이터, 사람2_동양데이터, 사람1_서양데이터, 사람2_서양데이터)
    """
    # 동양 데이터 계산
    gan1, ji1 = get_day_master_from_birth(person1.birth_date)
    gan2, ji2 = get_day_master_from_birth(person2.birth_date)

    elem1 = CHEON_GAN_TO_ELEMENT[gan1]
    elem2 = CHEON_GAN_TO_ELEMENT[gan2]

    balance1 = calculate_element_balance(person1.birth_date)
    balance2 = calculate_element_balance(person2.birth_date)

    east1 = EasternData(
        day_master_code=gan1,
        day_master_element=elem1,
        day_branch_code=ji1,
        strong_element=max(balance1, key=balance1.get),
        weak_element=min(balance1, key=balance1.get),
        element_balance=balance1,
    )
    east2 = EasternData(
        day_master_code=gan2,
        day_master_element=elem2,
        day_branch_code=ji2,
        strong_element=max(balance2, key=balance2.get),
        weak_element=min(balance2, key=balance2.get),
        element_balance=balance2,
    )

    # 서양 데이터 계산
    sign1 = get_zodiac_sign(person1.birth_date)
    sign2 = get_zodiac_sign(person2.birth_date)

    west1 = WesternData(
        sun_sign=sign1,
        sun_element=ZODIAC_TO_ELEMENT[sign1],
        sun_modality=ZODIAC_TO_MODALITY[sign1],
        life_path_number=calculate_life_path_number(person1.birth_date),
    )
    west2 = WesternData(
        sun_sign=sign2,
        sun_element=ZODIAC_TO_ELEMENT[sign2],
        sun_modality=ZODIAC_TO_MODALITY[sign2],
        life_path_number=calculate_life_path_number(person2.birth_date),
    )

    # 동양 점수 계산
    east_day_master = calc_day_master_score(elem1, elem2)
    east_element_balance = calc_element_balance_score(balance1, balance2)
    east_branch_relation = calc_branch_relation_score(ji1, ji2)
    east_total = east_day_master + east_element_balance + east_branch_relation

    # 서양 점수 계산
    west_zodiac = calc_zodiac_score(sign1, sign2)
    west_element = calc_western_element_score(west1.sun_element, west2.sun_element)
    west_modality = calc_modality_score(west1.sun_modality, west2.sun_modality)
    west_numerology = calc_life_path_score(west1.life_path_number, west2.life_path_number)
    west_total = west_zodiac + west_element + west_modality + west_numerology

    scores = CompatibilityScores(
        east_day_master=east_day_master,
        east_element_balance=east_element_balance,
        east_branch_relation=east_branch_relation,
        east_total=east_total,
        west_zodiac=west_zodiac,
        west_element=west_element,
        west_modality=west_modality,
        west_numerology=west_numerology,
        west_total=west_total,
        total=east_total + west_total,
    )

    return scores, east1, east2, west1, west2


# ============================================================
# 테스트
# ============================================================

if __name__ == "__main__":
    # 테스트 데이터
    person1 = PersonData(
        name="홍길동",
        gender="M",
        birth_date="2002-03-13",
        birth_time="14:30",
    )
    person2 = PersonData(
        name="김민수",
        gender="M",
        birth_date="2002-09-27",
        birth_time="08:10",
    )

    scores, east1, east2, west1, west2 = calculate_compatibility(person1, person2)

    print("=" * 60)
    print("궁합 점수 계산 결과")
    print("=" * 60)

    print(f"\n[{person1.name}] 동양 데이터:")
    print(f"  일간: {east1.day_master_code} ({east1.day_master_element})")
    print(f"  일지: {east1.day_branch_code}")
    print(f"  강한 오행: {east1.strong_element}")
    print(f"  약한 오행: {east1.weak_element}")

    print(f"\n[{person2.name}] 동양 데이터:")
    print(f"  일간: {east2.day_master_code} ({east2.day_master_element})")
    print(f"  일지: {east2.day_branch_code}")
    print(f"  강한 오행: {east2.strong_element}")
    print(f"  약한 오행: {east2.weak_element}")

    print(f"\n[{person1.name}] 서양 데이터:")
    print(f"  별자리: {west1.sun_sign} ({west1.sun_element})")
    print(f"  양태: {west1.sun_modality}")
    print(f"  생명수: {west1.life_path_number}")

    print(f"\n[{person2.name}] 서양 데이터:")
    print(f"  별자리: {west2.sun_sign} ({west2.sun_element})")
    print(f"  양태: {west2.sun_modality}")
    print(f"  생명수: {west2.life_path_number}")

    print("\n" + "=" * 60)
    print("궁합 점수")
    print("=" * 60)

    print(f"\n[동양 궁합] {scores.east_total}/50점")
    print(f"  - 일간 상생상극: {scores.east_day_master}/20점")
    print(f"  - 오행 보완: {scores.east_element_balance}/15점")
    print(f"  - 지지 충합: {scores.east_branch_relation}/15점")

    print(f"\n[서양 궁합] {scores.west_total}/50점")
    print(f"  - 별자리 궁합: {scores.west_zodiac}/20점")
    print(f"  - 원소 조화: {scores.west_element}/15점")
    print(f"  - 양태 조화: {scores.west_modality}/10점")
    print(f"  - 수비학: {scores.west_numerology}/5점")

    print(f"\n[종합 점수] {scores.total}/100점")

    # 점수 해석
    if scores.total >= 80:
        grade = "천생연분 💕"
    elif scores.total >= 65:
        grade = "좋은 궁합 ✨"
    elif scores.total >= 50:
        grade = "보통 궁합 👍"
    else:
        grade = "노력이 필요한 궁합 💪"

    print(f"[등급] {grade}")
