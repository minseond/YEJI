"""서양 점성술 분석 서비스

출생 차트 계산 및 분석 로직
"""

from datetime import datetime
from typing import Any

import structlog

from yeji_ai.models.enums import (
    PlanetCode,
    ZodiacCode,
    ZodiacElement,
    ZodiacModality,
)
from yeji_ai.models.enums.domain_codes import (
    MODALITY_LABELS,
    WEST_ELEMENT_LABELS,
    WEST_KEYWORD_LABELS,
)
from yeji_ai.models.fortune.western import WesternFortuneRequest
from yeji_ai.models.user_fortune import (
    DetailedAnalysis,
    FortuneContent,
    MainSign,
    WesternElement,
    WesternFortuneDataV2,
    WesternKeyword,
    WesternLucky,
    WesternStats,
)

logger = structlog.get_logger()


# ============================================================
# 상수 정의
# ============================================================

# 별자리 날짜 범위 (시작월, 시작일, 종료월, 종료일)
ZODIAC_DATES: dict[ZodiacCode, tuple[int, int, int, int]] = {
    ZodiacCode.ARIES: (3, 21, 4, 19),
    ZodiacCode.TAURUS: (4, 20, 5, 20),
    ZodiacCode.GEMINI: (5, 21, 6, 20),
    ZodiacCode.CANCER: (6, 21, 7, 22),
    ZodiacCode.LEO: (7, 23, 8, 22),
    ZodiacCode.VIRGO: (8, 23, 9, 22),
    ZodiacCode.LIBRA: (9, 23, 10, 22),
    ZodiacCode.SCORPIO: (10, 23, 11, 21),
    ZodiacCode.SAGITTARIUS: (11, 22, 12, 21),
    ZodiacCode.CAPRICORN: (12, 22, 1, 19),
    ZodiacCode.AQUARIUS: (1, 20, 2, 18),
    ZodiacCode.PISCES: (2, 19, 3, 20),
}

# 별자리 → 원소 매핑
ZODIAC_ELEMENT: dict[ZodiacCode, ZodiacElement] = {
    ZodiacCode.ARIES: ZodiacElement.FIRE,
    ZodiacCode.TAURUS: ZodiacElement.EARTH,
    ZodiacCode.GEMINI: ZodiacElement.AIR,
    ZodiacCode.CANCER: ZodiacElement.WATER,
    ZodiacCode.LEO: ZodiacElement.FIRE,
    ZodiacCode.VIRGO: ZodiacElement.EARTH,
    ZodiacCode.LIBRA: ZodiacElement.AIR,
    ZodiacCode.SCORPIO: ZodiacElement.WATER,
    ZodiacCode.SAGITTARIUS: ZodiacElement.FIRE,
    ZodiacCode.CAPRICORN: ZodiacElement.EARTH,
    ZodiacCode.AQUARIUS: ZodiacElement.AIR,
    ZodiacCode.PISCES: ZodiacElement.WATER,
}

# 별자리 → 모달리티 매핑
ZODIAC_MODALITY: dict[ZodiacCode, ZodiacModality] = {
    ZodiacCode.ARIES: ZodiacModality.CARDINAL,
    ZodiacCode.TAURUS: ZodiacModality.FIXED,
    ZodiacCode.GEMINI: ZodiacModality.MUTABLE,
    ZodiacCode.CANCER: ZodiacModality.CARDINAL,
    ZodiacCode.LEO: ZodiacModality.FIXED,
    ZodiacCode.VIRGO: ZodiacModality.MUTABLE,
    ZodiacCode.LIBRA: ZodiacModality.CARDINAL,
    ZodiacCode.SCORPIO: ZodiacModality.FIXED,
    ZodiacCode.SAGITTARIUS: ZodiacModality.MUTABLE,
    ZodiacCode.CAPRICORN: ZodiacModality.CARDINAL,
    ZodiacCode.AQUARIUS: ZodiacModality.FIXED,
    ZodiacCode.PISCES: ZodiacModality.MUTABLE,
}

# 별자리 → 지배 행성 매핑
ZODIAC_RULER: dict[ZodiacCode, PlanetCode] = {
    ZodiacCode.ARIES: PlanetCode.MARS,
    ZodiacCode.TAURUS: PlanetCode.VENUS,
    ZodiacCode.GEMINI: PlanetCode.MERCURY,
    ZodiacCode.CANCER: PlanetCode.MOON,
    ZodiacCode.LEO: PlanetCode.SUN,
    ZodiacCode.VIRGO: PlanetCode.MERCURY,
    ZodiacCode.LIBRA: PlanetCode.VENUS,
    ZodiacCode.SCORPIO: PlanetCode.PLUTO,
    ZodiacCode.SAGITTARIUS: PlanetCode.JUPITER,
    ZodiacCode.CAPRICORN: PlanetCode.SATURN,
    ZodiacCode.AQUARIUS: PlanetCode.URANUS,
    ZodiacCode.PISCES: PlanetCode.NEPTUNE,
}

# 행성 → 행운의 요일 매핑
PLANET_DAY: dict[PlanetCode, tuple[str, str]] = {
    PlanetCode.SUN: ("일요일", "SUN"),
    PlanetCode.MOON: ("월요일", "MON"),
    PlanetCode.MARS: ("화요일", "TUE"),
    PlanetCode.MERCURY: ("수요일", "WED"),
    PlanetCode.JUPITER: ("목요일", "THU"),
    PlanetCode.VENUS: ("금요일", "FRI"),
    PlanetCode.SATURN: ("토요일", "SAT"),
    PlanetCode.URANUS: ("수요일", "WED"),
    PlanetCode.NEPTUNE: ("목요일", "THU"),
    PlanetCode.PLUTO: ("화요일", "TUE"),
}

# 별자리별 행운 정보
ZODIAC_LUCKY: dict[ZodiacCode, dict[str, Any]] = {
    ZodiacCode.ARIES: {
        "color": "빨간색", "color_code": "#FF0000",
        "number": "9", "stone": "다이아몬드",
    },
    ZodiacCode.TAURUS: {
        "color": "초록색", "color_code": "#228B22",
        "number": "6", "stone": "에메랄드",
    },
    ZodiacCode.GEMINI: {
        "color": "노란색", "color_code": "#FFD700",
        "number": "5", "stone": "아게이트",
    },
    ZodiacCode.CANCER: {
        "color": "흰색", "color_code": "#FFFFFF",
        "number": "2", "stone": "진주",
    },
    ZodiacCode.LEO: {
        "color": "금색", "color_code": "#FFD700",
        "number": "1", "stone": "루비",
    },
    ZodiacCode.VIRGO: {
        "color": "베이지", "color_code": "#F5F5DC",
        "number": "5", "stone": "사파이어",
    },
    ZodiacCode.LIBRA: {
        "color": "파란색", "color_code": "#4169E1",
        "number": "6", "stone": "오팔",
    },
    ZodiacCode.SCORPIO: {
        "color": "검은색", "color_code": "#000000",
        "number": "8", "stone": "토파즈",
    },
    ZodiacCode.SAGITTARIUS: {
        "color": "보라색", "color_code": "#800080",
        "number": "3", "stone": "터키석",
    },
    ZodiacCode.CAPRICORN: {
        "color": "갈색", "color_code": "#8B4513",
        "number": "8", "stone": "가넷",
    },
    ZodiacCode.AQUARIUS: {
        "color": "하늘색", "color_code": "#87CEEB",
        "number": "4", "stone": "자수정",
    },
    ZodiacCode.PISCES: {
        "color": "바다색", "color_code": "#20B2AA",
        "number": "7", "stone": "아쿠아마린",
    },
}


class WesternFortuneService:
    """서양 점성술 분석 서비스"""

    def __init__(self):
        """초기화"""
        pass

    def get_sun_sign(self, month: int, day: int) -> ZodiacCode:
        """
        태양 별자리 계산

        Args:
            month: 월 (1-12)
            day: 일 (1-31)

        Returns:
            별자리 코드
        """
        # (월, 일)을 정수로 변환하여 비교 (예: 4월 5일 → 405)
        date_num = month * 100 + day

        for zodiac, (start_month, start_day, end_month, end_day) in ZODIAC_DATES.items():
            start_num = start_month * 100 + start_day
            end_num = end_month * 100 + end_day

            # 염소자리 특수 처리 (연말~연초 걸침: 12/22 ~ 1/19)
            if start_month > end_month:
                # 12월 22일 이후 또는 1월 19일 이전
                if date_num >= start_num or date_num <= end_num:
                    return zodiac
            else:
                # 일반적인 경우: 시작일 ~ 종료일 범위 내
                if start_num <= date_num <= end_num:
                    return zodiac

        # 기본값 (도달하지 않아야 함)
        return ZodiacCode.CAPRICORN

    def get_moon_sign(self, birth_date: datetime) -> ZodiacCode:
        """
        달 별자리 계산 (간략화된 버전)

        실제로는 정확한 출생시간과 위치가 필요합니다.
        여기서는 생년월일 기반 추정값을 사용합니다.
        """
        # 달의 황도대 이동 주기 약 2.5일
        day_of_year = birth_date.timetuple().tm_yday
        year = birth_date.year

        # 간단한 계산 (정확하지 않음, flatlib 사용 권장)
        base_offset = (year % 19) * 11 + day_of_year
        moon_index = (base_offset // 2) % 12

        zodiac_list = list(ZodiacCode)
        return zodiac_list[moon_index]

    def get_rising_sign(
        self,
        birth_date: datetime,
        birth_hour: int | None = None,
    ) -> ZodiacCode:
        """
        상승궁 계산 (간략화된 버전)

        실제로는 정확한 출생시간과 위치가 필요합니다.
        """
        if birth_hour is None:
            # 시간 없으면 태양 별자리 반환
            return self.get_sun_sign(birth_date.month, birth_date.day)

        # 상승궁 = 대략 2시간마다 별자리 변경
        sun_sign = self.get_sun_sign(birth_date.month, birth_date.day)
        sun_index = list(ZodiacCode).index(sun_sign)

        # 출생 시간에 따른 오프셋 (매우 간략화)
        hour_offset = birth_hour // 2
        rising_index = (sun_index + hour_offset) % 12

        return list(ZodiacCode)[rising_index]

    def calculate_element_stats(
        self,
        sun_sign: ZodiacCode,
        moon_sign: ZodiacCode,
        rising_sign: ZodiacCode,
    ) -> tuple[list[WesternElement], ZodiacElement, str]:
        """
        4원소 분포 계산 (신버전 스키마)

        Args:
            sun_sign: 태양 별자리
            moon_sign: 달 별자리
            rising_sign: 상승 별자리

        Returns:
            (4원소 분포 리스트, 우세 원소, 요약)
        """
        counts: dict[ZodiacElement, int] = {e: 0 for e in ZodiacElement}

        # 태양, 달, 상승궁에 가중치
        counts[ZODIAC_ELEMENT[sun_sign]] += 3
        counts[ZODIAC_ELEMENT[moon_sign]] += 2
        counts[ZODIAC_ELEMENT[rising_sign]] += 1

        total = sum(counts.values())
        dominant = max(counts, key=counts.get)

        distribution = []
        for element in ZodiacElement:
            distribution.append(WesternElement(
                code=element.value,
                label=WEST_ELEMENT_LABELS.get(element.value, element.label_ko),
                percent=round(counts[element] / total * 100, 1) if total > 0 else 0,
            ))

        summary = f"{dominant.label_ko} 원소가 우세합니다"

        return distribution, dominant, summary

    def calculate_modality_stats(
        self,
        sun_sign: ZodiacCode,
        moon_sign: ZodiacCode,
        rising_sign: ZodiacCode,
    ) -> tuple[list[WesternElement], ZodiacModality, str]:
        """
        3양태 분포 계산 (신버전 스키마)

        Args:
            sun_sign: 태양 별자리
            moon_sign: 달 별자리
            rising_sign: 상승 별자리

        Returns:
            (3양태 분포 리스트, 우세 양태, 요약)
        """
        counts: dict[ZodiacModality, int] = {m: 0 for m in ZodiacModality}

        # 태양, 달, 상승궁에 가중치
        counts[ZODIAC_MODALITY[sun_sign]] += 3
        counts[ZODIAC_MODALITY[moon_sign]] += 2
        counts[ZODIAC_MODALITY[rising_sign]] += 1

        total = sum(counts.values())
        dominant = max(counts, key=counts.get)

        distribution = []
        for modality in ZodiacModality:
            distribution.append(WesternElement(
                code=modality.value,
                label=MODALITY_LABELS.get(modality.value, modality.label_ko),
                percent=round(counts[modality] / total * 100, 1) if total > 0 else 0,
            ))

        modality_desc = {
            ZodiacModality.CARDINAL: "시작하고 개척하는",
            ZodiacModality.FIXED: "안정적이고 지속적인",
            ZodiacModality.MUTABLE: "유연하고 적응력 있는",
        }
        summary = f"{modality_desc[dominant]} 성향이 강합니다"

        return distribution, dominant, summary

    def generate_keywords(
        self,
        sun_sign: ZodiacCode,
        dominant_element: ZodiacElement,
    ) -> tuple[list[WesternKeyword], str]:
        """
        키워드 생성 (신버전 스키마)

        Args:
            sun_sign: 태양 별자리
            dominant_element: 우세 원소

        Returns:
            (키워드 리스트, 요약)
        """
        # 별자리별 키워드 매핑
        sign_keywords = {
            ZodiacCode.ARIES: ["LEADERSHIP", "COURAGE", "INDEPENDENCE"],
            ZodiacCode.TAURUS: ["STABILITY", "PATIENCE", "PRACTICALITY"],
            ZodiacCode.GEMINI: ["COMMUNICATION", "CURIOSITY", "ADAPTABILITY"],
            ZodiacCode.CANCER: ["NURTURING", "INTUITION", "SENSITIVITY"],
            ZodiacCode.LEO: ["LEADERSHIP", "CREATIVITY", "CONFIDENCE"],
            ZodiacCode.VIRGO: ["ANALYTICAL", "PRACTICALITY", "PERFECTIONISM"],
            ZodiacCode.LIBRA: ["HARMONY", "DIPLOMACY", "BALANCE"],
            ZodiacCode.SCORPIO: ["INTENSITY", "INTUITION", "TRANSFORMATION"],
            ZodiacCode.SAGITTARIUS: ["ADVENTURE", "OPTIMISM", "FREEDOM"],
            ZodiacCode.CAPRICORN: ["AMBITION", "DISCIPLINE", "RESPONSIBILITY"],
            ZodiacCode.AQUARIUS: ["INNOVATION", "INDEPENDENCE", "HUMANITARIANISM"],
            ZodiacCode.PISCES: ["INTUITION", "CREATIVITY", "COMPASSION"],
        }

        keyword_codes = sign_keywords.get(sun_sign, ["BALANCE", "HARMONY", "INTUITION"])

        keywords = []
        for i, code in enumerate(keyword_codes[:3]):
            keywords.append(WesternKeyword(
                code=code,
                label=WEST_KEYWORD_LABELS.get(code, code),
                weight=round(0.9 - (i * 0.2), 1),
            ))

        summary = f"{sun_sign.label_ko}의 특성으로 {keywords[0].label}이(가) 두드러집니다"

        return keywords, summary

    def generate_lucky_info(
        self,
        sun_sign: ZodiacCode,
    ) -> WesternLucky:
        """
        행운 정보 생성 (신버전 스키마)

        Args:
            sun_sign: 태양 별자리

        Returns:
            행운 정보 (WesternLucky)
        """
        lucky_data = ZODIAC_LUCKY[sun_sign]

        return WesternLucky(
            color=lucky_data["color"],
            number=lucky_data["number"],
            item=lucky_data["stone"],
            place=None,
        )

    async def analyze(
        self,
        request: WesternFortuneRequest,
    ) -> WesternFortuneDataV2:
        """
        서양 점성술 분석 실행 (프론트엔드 확정 스키마)

        Args:
            request: 분석 요청

        Returns:
            WesternFortuneDataV2 응답
        """
        logger.info("western_analysis_start", birth_date=request.birth_date)

        # 1. 날짜 파싱
        birth_dt = datetime.strptime(request.birth_date, "%Y-%m-%d")
        birth_hour = None
        if request.birth_time:
            birth_hour = int(request.birth_time.split(":")[0])

        # 2. 빅3 계산
        sun_sign = self.get_sun_sign(birth_dt.month, birth_dt.day)
        moon_sign = self.get_moon_sign(birth_dt)
        rising_sign = self.get_rising_sign(birth_dt, birth_hour)

        # 3. 통계 계산 (신버전 스키마)
        element_distribution, dominant_element, element_summary = self.calculate_element_stats(
            sun_sign, moon_sign, rising_sign
        )
        modality_distribution, dominant_modality, modality_summary = self.calculate_modality_stats(
            sun_sign, moon_sign, rising_sign
        )
        keywords, keywords_summary = self.generate_keywords(sun_sign, dominant_element)

        # 4. MainSign 생성
        # ZodiacCode에서 한글 이름 추출 (띄어쓰기 없음, 도메인 매핑 준수)
        zodiac_kr_map = {
            ZodiacCode.ARIES: "양자리",
            ZodiacCode.TAURUS: "황소자리",
            ZodiacCode.GEMINI: "쌍둥이자리",
            ZodiacCode.CANCER: "게자리",
            ZodiacCode.LEO: "사자자리",
            ZodiacCode.VIRGO: "처녀자리",
            ZodiacCode.LIBRA: "천칭자리",
            ZodiacCode.SCORPIO: "전갈자리",
            ZodiacCode.SAGITTARIUS: "사수자리",
            ZodiacCode.CAPRICORN: "염소자리",
            ZodiacCode.AQUARIUS: "물병자리",
            ZodiacCode.PISCES: "물고기자리",
        }
        main_sign = MainSign(name=zodiac_kr_map[sun_sign])

        # 5. WesternStats 생성 (신버전)
        stats = WesternStats(
            main_sign=main_sign,
            element_summary=element_summary,
            element_4_distribution=element_distribution,
            modality_summary=modality_summary,
            modality_3_distribution=modality_distribution,
            keywords_summary=keywords_summary,
            keywords=keywords,
        )

        # 6. FortuneContent 생성 (의미심장하게)
        element_descriptions = {
            ZodiacElement.FIRE: "불꽃처럼 타오르는 열정이 당신의 영혼을 밝힙니다",
            ZodiacElement.EARTH: "대지처럼 굳건한 당신의 발걸음이 안정을 만듭니다",
            ZodiacElement.AIR: "바람처럼 자유로운 사고가 당신을 새로운 곳으로 이끕니다",
            ZodiacElement.WATER: "물처럼 깊은 감성이 당신의 직관을 깨웁니다",
        }

        overview = (
            f"별들이 {zodiac_kr_map[sun_sign]}의 자리에서 당신을 맞이했습니다. "
            f"{element_descriptions[dominant_element]}."
        )

        detailed_analysis = [
            DetailedAnalysis(
                title="내면의 빛",
                content=(
                    f"{zodiac_kr_map[sun_sign]}의 태양 아래 태어난 당신은 "
                    f"{element_descriptions[ZODIAC_ELEMENT[sun_sign]]}. "
                    f"{zodiac_kr_map[moon_sign]}의 달은 당신의 내면에 숨겨진 "
                    "감정의 바다를 비춥니다."
                ),
            ),
            DetailedAnalysis(
                title="세상과의 대화",
                content=(
                    f"{zodiac_kr_map[rising_sign]}의 기운이 당신의 첫인상을 형성합니다. "
                    f"세상은 당신을 통해 {zodiac_kr_map[rising_sign]}의 에너지를 느끼게 됩니다."
                ),
            ),
        ]

        advice = (
            f"당신 안의 {dominant_element.label_ko} 원소를 믿으세요. "
            "균형 속에서 진정한 빛을 발하게 될 것입니다."
        )

        fortune_content = FortuneContent(
            overview=overview,
            detailed_analysis=detailed_analysis,
            advice=advice,
        )

        # 7. 행운 정보
        lucky = self.generate_lucky_info(sun_sign)

        logger.info("western_analysis_complete", birth_date=request.birth_date)

        return WesternFortuneDataV2(
            element=dominant_element.value,
            stats=stats,
            fortune_content=fortune_content,
            lucky=lucky,
        )
