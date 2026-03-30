"""만세력 계산기 - 사주팔자 계산"""

from datetime import datetime

import structlog
from korean_lunar_calendar import KoreanLunarCalendar

from yeji_ai.models.saju import (
    CategoryScore,
    EasternAnalysis,
    ElementBalance,
    FourPillars,
    SajuResult,
    WesternAnalysis,
)

logger = structlog.get_logger()

# 천간 (10개)
HEAVENLY_STEMS = ["갑", "을", "병", "정", "무", "기", "경", "신", "임", "계"]

# 지지 (12개)
EARTHLY_BRANCHES = ["자", "축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해"]

# 60갑자 (천간+지지 조합)
SIXTY_CYCLE = [f"{HEAVENLY_STEMS[i % 10]}{EARTHLY_BRANCHES[i % 12]}" for i in range(60)]

# 오행 매핑 (천간)
STEM_ELEMENTS = {
    "갑": "목",
    "을": "목",
    "병": "화",
    "정": "화",
    "무": "토",
    "기": "토",
    "경": "금",
    "신": "금",
    "임": "수",
    "계": "수",
}

# 오행 매핑 (지지)
BRANCH_ELEMENTS = {
    "자": "수",
    "축": "토",
    "인": "목",
    "묘": "목",
    "진": "토",
    "사": "화",
    "오": "화",
    "미": "토",
    "신": "금",
    "유": "금",
    "술": "토",
    "해": "수",
}

# 한자 → 한글 매핑 (천간)
HANJA_TO_HANGUL_STEM = {
    "甲": "갑", "乙": "을", "丙": "병", "丁": "정", "戊": "무",
    "己": "기", "庚": "경", "辛": "신", "壬": "임", "癸": "계",
}

# 한자 → 한글 매핑 (지지)
HANJA_TO_HANGUL_BRANCH = {
    "子": "자", "丑": "축", "寅": "인", "卯": "묘", "辰": "진", "巳": "사",
    "午": "오", "未": "미", "申": "신", "酉": "유", "戌": "술", "亥": "해",
}

# 음양 매핑 (천간) - 양: 갑병무경임, 음: 을정기신계
STEM_YIN_YANG = {
    "갑": "양", "을": "음",
    "병": "양", "정": "음",
    "무": "양", "기": "음",
    "경": "양", "신": "음",
    "임": "양", "계": "음",
    # 한자 버전
    "甲": "양", "乙": "음",
    "丙": "양", "丁": "음",
    "戊": "양", "己": "음",
    "庚": "양", "辛": "음",
    "壬": "양", "癸": "음",
}

# 음양 매핑 (지지) - 양: 자인진오신술, 음: 축묘사미유해
BRANCH_YIN_YANG = {
    "자": "양", "축": "음",
    "인": "양", "묘": "음",
    "진": "양", "사": "음",
    "오": "양", "미": "음",
    "신": "양", "유": "음",
    "술": "양", "해": "음",
    # 한자 버전
    "子": "양", "丑": "음",
    "寅": "양", "卯": "음",
    "辰": "양", "巳": "음",
    "午": "양", "未": "음",
    "申": "양", "酉": "음",
    "戌": "양", "亥": "음",
}

# 오행 상생상극 관계 (십신 계산용)
# 일간 오행 → 대상 오행 → 관계
FIVE_ELEMENT_RELATIONS = {
    # 목(木)
    ("목", "목"): "비겁",   # 같은 오행
    ("목", "화"): "식상",   # 내가 생하는 것
    ("목", "토"): "재성",   # 내가 극하는 것
    ("목", "금"): "관성",   # 나를 극하는 것
    ("목", "수"): "인성",   # 나를 생하는 것
    # 화(火)
    ("화", "화"): "비겁",
    ("화", "토"): "식상",
    ("화", "금"): "재성",
    ("화", "수"): "관성",
    ("화", "목"): "인성",
    # 토(土)
    ("토", "토"): "비겁",
    ("토", "금"): "식상",
    ("토", "수"): "재성",
    ("토", "목"): "관성",
    ("토", "화"): "인성",
    # 금(金)
    ("금", "금"): "비겁",
    ("금", "수"): "식상",
    ("금", "목"): "재성",
    ("금", "화"): "관성",
    ("금", "토"): "인성",
    # 수(水)
    ("수", "수"): "비겁",
    ("수", "목"): "식상",
    ("수", "화"): "재성",
    ("수", "토"): "관성",
    ("수", "금"): "인성",
}

# 음양에 따른 정/편 구분
# True: 음양 동일 → 편, False: 음양 다름 → 정
TEN_GOD_NAMES = {
    ("비겁", True): "비견",    # 음양 동일 (갑/갑, 을/을)
    ("비겁", False): "겁재",   # 음양 다름 (갑/을, 을/갑)
    ("식상", True): "식신",
    ("식상", False): "상관",
    ("재성", True): "편재",
    ("재성", False): "정재",
    ("관성", True): "편관",
    ("관성", False): "정관",
    ("인성", True): "편인",
    ("인성", False): "정인",
}

# 오행 코드 매핑
ELEMENT_TO_CODE = {
    "목": "WOOD", "화": "FIRE", "토": "EARTH", "금": "METAL", "수": "WATER",
}

# 십신 코드 매핑
TEN_GOD_TO_CODE = {
    "비견": "BIGYEON", "겁재": "GEOPJAE",
    "식신": "SIKSIN", "상관": "SANGGWAN",
    "편재": "PYEONJAE", "정재": "JEONGJAE",
    "편관": "PYEONGWAN", "정관": "JEONGGWAN",
    "편인": "PYEONIN", "정인": "JEONGIN",
}

# 별자리 매핑 (태양 별자리) - (이름, 시작월, 시작일, 종료월, 종료일)
ZODIAC_SIGNS = [
    ("염소자리", 12, 22, 1, 19),
    ("물병자리", 1, 20, 2, 18),
    ("물고기자리", 2, 19, 3, 20),
    ("양자리", 3, 21, 4, 19),
    ("황소자리", 4, 20, 5, 20),
    ("쌍둥이자리", 5, 21, 6, 20),
    ("게자리", 6, 21, 7, 22),
    ("사자자리", 7, 23, 8, 22),
    ("처녀자리", 8, 23, 9, 22),
    ("천칭자리", 9, 23, 10, 22),
    ("전갈자리", 10, 23, 11, 21),
    ("사수자리", 11, 22, 12, 21),
]

# 별자리 코드 매핑 (한글 → 코드)
ZODIAC_NAME_TO_CODE = {
    "양자리": "ARIES", "황소자리": "TAURUS", "쌍둥이자리": "GEMINI",
    "게자리": "CANCER", "사자자리": "LEO", "처녀자리": "VIRGO",
    "천칭자리": "LIBRA", "전갈자리": "SCORPIO", "사수자리": "SAGITTARIUS",
    "염소자리": "CAPRICORN", "물병자리": "AQUARIUS", "물고기자리": "PISCES",
}

# 별자리 → 원소 매핑
ZODIAC_ELEMENT_MAP = {
    "ARIES": "FIRE", "LEO": "FIRE", "SAGITTARIUS": "FIRE",
    "TAURUS": "EARTH", "VIRGO": "EARTH", "CAPRICORN": "EARTH",
    "GEMINI": "AIR", "LIBRA": "AIR", "AQUARIUS": "AIR",
    "CANCER": "WATER", "SCORPIO": "WATER", "PISCES": "WATER",
}

# 별자리 → 양태 매핑
ZODIAC_MODALITY_MAP = {
    "ARIES": "CARDINAL", "CANCER": "CARDINAL",
    "LIBRA": "CARDINAL", "CAPRICORN": "CARDINAL",
    "TAURUS": "FIXED", "LEO": "FIXED",
    "SCORPIO": "FIXED", "AQUARIUS": "FIXED",
    "GEMINI": "MUTABLE", "VIRGO": "MUTABLE",
    "SAGITTARIUS": "MUTABLE", "PISCES": "MUTABLE",
}

# 양태 한글 레이블
MODALITY_LABELS = {
    "CARDINAL": "활동궁", "FIXED": "고정궁", "MUTABLE": "변통궁",
}

# 서양 원소 한글 레이블
WESTERN_ELEMENT_LABELS = {
    "FIRE": "불", "EARTH": "흙", "AIR": "공기", "WATER": "물",
}


class SajuCalculator:
    """만세력 계산기"""

    def __init__(self):
        self.calendar = KoreanLunarCalendar()

    def calculate(
        self,
        birth_date: str,
        birth_time: str | None = None,
        gender: str = "M",
    ) -> tuple[FourPillars, ElementBalance]:
        """
        사주팔자 계산

        Args:
            birth_date: 생년월일 (YYYY-MM-DD)
            birth_time: 출생시간 (HH:MM), 선택
            gender: 성별 (M/F)

        Returns:
            (FourPillars, ElementBalance)
        """
        try:
            dt = datetime.strptime(birth_date, "%Y-%m-%d")

            # 연주 계산
            year_idx = (dt.year - 4) % 60
            year_pillar = SIXTY_CYCLE[year_idx]

            # 월주 계산 (간단히 - 실제로는 절기 기준)
            month_idx = ((dt.year - 4) * 12 + dt.month - 1) % 60
            month_pillar = SIXTY_CYCLE[month_idx]

            # 일주 계산
            base_date = datetime(1900, 1, 31)  # 갑자일
            day_diff = (dt - base_date).days
            day_idx = day_diff % 60
            day_pillar = SIXTY_CYCLE[day_idx]

            # 시주 계산
            hour_pillar = None
            if birth_time:
                hour = int(birth_time.split(":")[0])
                hour_branch_idx = ((hour + 1) // 2) % 12
                day_stem_idx = HEAVENLY_STEMS.index(day_pillar[0])
                hour_stem_idx = (day_stem_idx * 2 + hour_branch_idx) % 10
                hour_pillar = f"{HEAVENLY_STEMS[hour_stem_idx]}{EARTHLY_BRANCHES[hour_branch_idx]}"

            four_pillars = FourPillars(
                year=year_pillar,
                month=month_pillar,
                day=day_pillar,
                hour=hour_pillar,
            )

            # 오행 균형 계산
            element_balance = self._calculate_element_balance(four_pillars)

            logger.info(
                "saju_calculated",
                birth_date=birth_date,
                four_pillars=four_pillars.model_dump(),
            )

            return four_pillars, element_balance

        except Exception as e:
            logger.error("saju_calculation_error", error=str(e))
            raise

    def _calculate_element_balance(self, pillars: FourPillars) -> ElementBalance:
        """오행 균형 계산"""
        elements = {"목": 0, "화": 0, "토": 0, "금": 0, "수": 0}

        for pillar in [pillars.year, pillars.month, pillars.day, pillars.hour]:
            if pillar:
                stem = pillar[0]
                branch = pillar[1]
                elements[STEM_ELEMENTS[stem]] += 10
                elements[BRANCH_ELEMENTS[branch]] += 10

        # 정규화 (총합 100)
        total = sum(elements.values())
        if total > 0:
            for key in elements:
                elements[key] = int(elements[key] / total * 100)

        return ElementBalance(
            wood=elements["목"],
            fire=elements["화"],
            earth=elements["토"],
            metal=elements["금"],
            water=elements["수"],
        )

    def get_sun_sign(self, birth_date: str) -> str:
        """태양 별자리 계산 (MEDIUM-2: 경계일 로직 수정)"""
        dt = datetime.strptime(birth_date, "%Y-%m-%d")
        month, day = dt.month, dt.day

        for sign, start_month, start_day, end_month, end_day in ZODIAC_SIGNS:
            # 염소자리 특수 처리 (12월~1월 걸침)
            if start_month > end_month:
                if (month == start_month and day >= start_day) or (
                    month == end_month and day <= end_day
                ):
                    return sign
            else:
                # 일반 별자리 (같은 해 내)
                if (month == start_month and day >= start_day) or (
                    month == end_month and day <= end_day
                ):
                    return sign
                if start_month < month < end_month:
                    return sign

        return "염소자리"  # 기본값 (도달 불가)

    def get_sun_sign_code(self, birth_date: str) -> str:
        """태양 별자리 코드 반환 (예: ARIES, TAURUS)"""
        sign_name = self.get_sun_sign(birth_date)
        return ZODIAC_NAME_TO_CODE.get(sign_name, "ARIES")

    def get_zodiac_element(self, sign_code: str) -> str:
        """별자리 → 원소 코드 반환"""
        return ZODIAC_ELEMENT_MAP.get(sign_code, "FIRE")

    def get_zodiac_modality(self, sign_code: str) -> str:
        """별자리 → 양태 코드 반환"""
        return ZODIAC_MODALITY_MAP.get(sign_code, "CARDINAL")

    def calculate_western_stats(self, birth_date: str) -> dict:
        """서양 점성술 통계 계산

        Args:
            birth_date: 생년월일 (YYYY-MM-DD)

        Returns:
            {
                "main_sign": {"code": "ARIES", "name": "양자리"},
                "element": "FIRE",
                "modality": "CARDINAL",
                "element_4_distribution": [
                    {"code": "FIRE", "label": "불", "percent": 50.0},
                    {"code": "EARTH", "label": "흙", "percent": 16.7},
                    ...
                ],
                "modality_3_distribution": [
                    {"code": "CARDINAL", "label": "활동궁", "percent": 50.0},
                    ...
                ]
            }
        """
        sign_code = self.get_sun_sign_code(birth_date)
        sign_name = self.get_sun_sign(birth_date)
        element = self.get_zodiac_element(sign_code)
        modality = self.get_zodiac_modality(sign_code)

        # 4원소 분포 (태양 별자리 기준: 해당 원소 50%, 나머지 16.7%)
        element_dist = []
        for elem_code in ["FIRE", "EARTH", "AIR", "WATER"]:
            percent = 50.0 if elem_code == element else 16.7
            element_dist.append({
                "code": elem_code,
                "label": WESTERN_ELEMENT_LABELS.get(elem_code, elem_code),
                "percent": percent,
            })

        # 3양태 분포 (태양 별자리 기준: 해당 양태 50%, 나머지 25%)
        modality_dist = []
        for mod_code in ["CARDINAL", "FIXED", "MUTABLE"]:
            percent = 50.0 if mod_code == modality else 25.0
            modality_dist.append({
                "code": mod_code,
                "label": MODALITY_LABELS.get(mod_code, mod_code),
                "percent": percent,
            })

        return {
            "main_sign": {"code": sign_code, "name": sign_name},
            "element": element,
            "modality": modality,
            "element_4_distribution": element_dist,
            "modality_3_distribution": modality_dist,
        }

    def get_day_master(self, day_pillar: str) -> str:
        """일간 추출 (예: 무진 → 무토)"""
        stem = day_pillar[0]
        element = STEM_ELEMENTS[stem]
        return f"{stem}{element}"

    def calculate_five_elements_distribution(
        self, pillars: FourPillars
    ) -> dict:
        """8자(4천간 + 4지지) → 오행 분포 계산

        Args:
            pillars: 사주 4기둥 정보

        Returns:
            {
                "list": [
                    {"code": "WOOD", "label": "목", "count": 2, "percent": 25.0},
                    ...
                ],
                "dominant": "EARTH",
                "weak": ["FIRE", "METAL"]
            }
        """
        elements = {"목": 0, "화": 0, "토": 0, "금": 0, "수": 0}
        total_chars = 0

        for pillar in [pillars.year, pillars.month, pillars.day, pillars.hour]:
            if pillar:
                stem = pillar[0]
                branch = pillar[1]

                # 한자인 경우 한글로 변환
                if stem in HANJA_TO_HANGUL_STEM:
                    stem = HANJA_TO_HANGUL_STEM[stem]
                if branch in HANJA_TO_HANGUL_BRANCH:
                    branch = HANJA_TO_HANGUL_BRANCH[branch]

                if stem in STEM_ELEMENTS:
                    elements[STEM_ELEMENTS[stem]] += 1
                    total_chars += 1
                if branch in BRANCH_ELEMENTS:
                    elements[BRANCH_ELEMENTS[branch]] += 1
                    total_chars += 1

        # 퍼센트 계산
        result_list = []
        for name in ["목", "화", "토", "금", "수"]:
            count = elements[name]
            percent = round(count / total_chars * 100, 1) if total_chars > 0 else 0.0
            result_list.append({
                "code": ELEMENT_TO_CODE[name],
                "label": name,
                "count": count,
                "percent": percent,
            })

        # 강약 판별
        sorted_elements = sorted(result_list, key=lambda x: x["percent"], reverse=True)
        dominant = sorted_elements[0]["code"] if sorted_elements else "WOOD"
        weak = [e["code"] for e in sorted_elements if e["percent"] < 12.5]

        return {
            "list": result_list,
            "dominant": dominant,
            "weak": weak,
        }

    def calculate_yin_yang_ratio(self, pillars: FourPillars) -> dict:
        """8자 → 음양 비율 계산

        Args:
            pillars: 사주 4기둥 정보

        Returns:
            {
                "yin": {"count": 3, "percent": 37.5},
                "yang": {"count": 5, "percent": 62.5},
                "balance": "양성"  # 양성/음성/균형
            }
        """
        yin_count = 0
        yang_count = 0

        for pillar in [pillars.year, pillars.month, pillars.day, pillars.hour]:
            if pillar:
                stem = pillar[0]
                branch = pillar[1]

                # 천간 음양
                if stem in STEM_YIN_YANG:
                    if STEM_YIN_YANG[stem] == "음":
                        yin_count += 1
                    else:
                        yang_count += 1

                # 지지 음양
                if branch in BRANCH_YIN_YANG:
                    if BRANCH_YIN_YANG[branch] == "음":
                        yin_count += 1
                    else:
                        yang_count += 1

        total = yin_count + yang_count
        yin_percent = round(yin_count / total * 100, 1) if total > 0 else 0.0
        yang_percent = round(yang_count / total * 100, 1) if total > 0 else 0.0

        # 균형 판별
        diff = abs(yin_percent - yang_percent)
        if diff <= 20:
            balance = "균형"
        elif yang_percent > yin_percent:
            balance = "양성"
        else:
            balance = "음성"

        return {
            "yin": {"count": yin_count, "percent": yin_percent},
            "yang": {"count": yang_count, "percent": yang_percent},
            "balance": balance,
        }

    def calculate_ten_gods(self, day_stem: str, pillars: FourPillars) -> dict:
        """일간 기준 십신 계산

        Args:
            day_stem: 일간 천간 (한글 또는 한자)
            pillars: 사주 4기둥 정보

        Returns:
            {
                "list": [
                    {"code": "SIKSIN", "label": "식신", "count": 2, "percent": 25.0},
                    ...
                ],
                "dominant": ["SIKSIN", "JEONGIN"],
                "day_master_element": "FIRE"
            }
        """
        # 일간 한글로 변환
        if day_stem in HANJA_TO_HANGUL_STEM:
            day_stem = HANJA_TO_HANGUL_STEM[day_stem]

        # 일간 오행, 음양
        day_element = STEM_ELEMENTS.get(day_stem, "목")
        day_yin_yang = STEM_YIN_YANG.get(day_stem, "양")

        # 십신 카운트
        ten_gods = {
            "비견": 0, "겁재": 0,
            "식신": 0, "상관": 0,
            "편재": 0, "정재": 0,
            "편관": 0, "정관": 0,
            "편인": 0, "정인": 0,
        }

        all_chars = []
        for pillar in [pillars.year, pillars.month, pillars.day, pillars.hour]:
            if pillar:
                all_chars.append(pillar[0])  # 천간
                all_chars.append(pillar[1])  # 지지

        for char in all_chars:
            # 한자 → 한글 변환
            if char in HANJA_TO_HANGUL_STEM:
                char = HANJA_TO_HANGUL_STEM[char]
            if char in HANJA_TO_HANGUL_BRANCH:
                char = HANJA_TO_HANGUL_BRANCH[char]

            # 오행 및 음양 추출
            if char in STEM_ELEMENTS:
                target_element = STEM_ELEMENTS[char]
                target_yin_yang = STEM_YIN_YANG.get(char, "양")
            elif char in BRANCH_ELEMENTS:
                target_element = BRANCH_ELEMENTS[char]
                target_yin_yang = BRANCH_YIN_YANG.get(char, "양")
            else:
                continue

            # 십신 계산
            relation = FIVE_ELEMENT_RELATIONS.get((day_element, target_element))
            if relation:
                same_yin_yang = (day_yin_yang == target_yin_yang)
                ten_god = TEN_GOD_NAMES.get((relation, same_yin_yang))
                if ten_god:
                    ten_gods[ten_god] += 1

        # 결과 생성
        total = sum(ten_gods.values())
        result_list = []
        for name, count in ten_gods.items():
            if count > 0:  # 0이 아닌 것만 포함
                percent = round(count / total * 100, 1) if total > 0 else 0.0
                result_list.append({
                    "code": TEN_GOD_TO_CODE.get(name, name.upper()),
                    "label": name,
                    "count": count,
                    "percent": percent,
                })

        # 빈도순 정렬
        result_list.sort(key=lambda x: x["percent"], reverse=True)

        # 상위 3개 + 기타
        dominant = [item["code"] for item in result_list[:2]] if result_list else []

        return {
            "list": result_list[:4],  # 상위 4개만
            "dominant": dominant,
            "day_master_element": ELEMENT_TO_CODE.get(day_element, "WOOD"),
        }

    async def calculate_mock(self) -> SajuResult:
        """테스트용 Mock 결과 생성"""
        return SajuResult(
            result_id=1,
            total_score=78,
            main_element="화",
            keywords=["열정", "리더십", "창의성", "결단력"],
            category_scores=[
                CategoryScore(
                    category="연애운", score=85, trend="up", description="재회의 기운이 높습니다"
                ),
                CategoryScore(
                    category="금전운", score=72, trend="stable", description="안정적인 흐름"
                ),
                CategoryScore(
                    category="직장운", score=68, trend="down", description="변화가 필요한 시기"
                ),
                CategoryScore(
                    category="건강운", score=75, trend="up", description="활력이 넘칩니다"
                ),
            ],
            eastern=EasternAnalysis(
                four_pillars=FourPillars(year="경오", month="신사", day="무진", hour="기미"),
                day_master="무토",
                element_balance=ElementBalance(wood=15, fire=30, earth=25, metal=15, water=15),
                lucky_elements=["화", "토"],
                interpretation=(
                    "무토 일간으로 태어나 안정적이고 신뢰감 있는 성격입니다. "
                    "화(火)의 기운이 강해 열정적이고 추진력이 있습니다."
                ),
            ),
            western=WesternAnalysis(
                sun_sign="물고기자리",
                moon_sign="전갈자리",
                rising_sign="사자자리",
                dominant_planet="해왕성",
                interpretation=(
                    "물고기자리 태양은 깊은 감수성과 직관력을 부여합니다. "
                    "사자자리 상승궁으로 외적으로는 당당하고 카리스마 있게 보입니다."
                ),
            ),
            combined_opinion=(
                "동양과 서양 모두 당신의 열정적인 성향과 깊은 감수성을 강조합니다. "
                "재회를 원하신다면, 감정에 휩쓸리지 말고 차분하게 접근하는 것이 좋겠습니다."
            ),
            advice=[
                "감정을 표현하기 전 3초 생각하기",
                "물 근처에서 명상하면 기운 균형에 도움",
                "3월 초순에 재회 시도 권장",
            ],
            visualizations=[
                {
                    "type": "radar",
                    "title": "오행 균형",
                    "data": {
                        "labels": ["목", "화", "토", "금", "수"],
                        "values": [15, 30, 25, 15, 15],
                    },
                }
            ],
            suggested_questions=[
                "재회 타이밍을 더 구체적으로 알려줘",
                "상대방의 마음은 어떨까요?",
            ],
        )
