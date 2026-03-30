"""LLM 완전 실패 시 코드 기반 기본값 폴백 시스템

LLM 호출이 모두 실패했을 때 사주/점성술 정보를 기반으로
규칙 기반 기본값을 생성합니다.

JSON 템플릿 기반 폴백 데이터:
- yeji_ai/data/fallback/eastern_templates.json: 동양 사주 템플릿
- yeji_ai/data/fallback/western_templates.json: 서양 점성술 템플릿
- yeji_ai/data/fallback/keywords.json: 키워드 데이터
"""

from typing import Any

import structlog

from yeji_ai.data.fallback import (
    get_eastern_fallback_data,
    get_western_fallback_data,
)

logger = structlog.get_logger()


# ============================================================
# 동양 사주 매핑 테이블
# ============================================================

# 일간(천간)별 성격 매핑 (10개)
DAY_MASTER_PERSONALITY: dict[str, dict[str, Any]] = {
    "GAP": {
        "hangul": "갑목(甲木)",
        "traits": ["리더십", "진취적", "정의감"],
        "description": "강직하고 곧은 성격으로, 리더십이 뛰어나고 진취적인 기질을 지니고 있소.",
    },
    "EUL": {
        "hangul": "을목(乙木)",
        "traits": ["유연함", "적응력", "협조적"],
        "description": "유연하고 부드러운 성격으로, 어떤 환경에도 잘 적응하며 협조적인 면이 있소.",
    },
    "BYEONG": {
        "hangul": "병화(丙火)",
        "traits": ["열정적", "밝음", "표현력"],
        "description": "밝고 열정적인 성격으로, 표현력이 뛰어나고 주변을 환하게 비추는 힘이 있소.",
    },
    "JEONG": {
        "hangul": "정화(丁火)",
        "traits": ["섬세함", "따뜻함", "배려"],
        "description": "섬세하고 따뜻한 성격으로, 타인을 배려하는 마음이 깊소.",
    },
    "MU": {
        "hangul": "무토(戊土)",
        "traits": ["안정적", "신뢰감", "중재력"],
        "description": "안정적이고 듬직한 성격으로, 주변에 신뢰감을 주며 중재력이 있소.",
    },
    "GI": {
        "hangul": "기토(己土)",
        "traits": ["포용력", "현실적", "실용적"],
        "description": "포용력이 크고 현실적인 성격으로, 실용적인 접근을 선호하오.",
    },
    "GYEONG": {
        "hangul": "경금(庚金)",
        "traits": ["결단력", "원칙", "추진력"],
        "description": "결단력이 있고 원칙을 중시하는 성격으로, 강한 추진력을 지니고 있소.",
    },
    "SIN": {
        "hangul": "신금(辛金)",
        "traits": ["세련됨", "분석력", "정교함"],
        "description": "세련되고 정교한 성격으로, 뛰어난 분석력과 심미안을 가지고 있소.",
    },
    "IM": {
        "hangul": "임수(壬水)",
        "traits": ["지혜", "유연함", "포용력"],
        "description": "지혜롭고 유연한 성격으로, 넓은 포용력과 깊은 통찰력을 가지고 있소.",
    },
    "GYE": {
        "hangul": "계수(癸水)",
        "traits": ["섬세함", "직관력", "감수성"],
        "description": "섬세하고 직관력이 뛰어난 성격으로, 깊은 감수성을 지니고 있소.",
    },
}

# 오행별 강점/약점 템플릿
ELEMENT_TRAITS: dict[str, dict[str, Any]] = {
    "WOOD": {
        "label_ko": "목",
        "label_hanja": "木",
        "strong": {
            "traits": ["창의력", "성장력"],
            "description": "창의력과 성장력이 뛰어나 새로운 것을 시작하는 능력이 탁월하오.",
        },
        "weak": {
            "traits": ["계획성 부족"],
            "description": "목(木)의 기운이 부족하여 계획성이 약할 수 있으니 꼼꼼히 준비하시오.",
        },
        "lucky": {
            "color": "초록",
            "color_code": "#228B22",
            "direction": "동쪽",
            "direction_code": "E",
            "place": "숲이나 공원",
        },
    },
    "FIRE": {
        "label_ko": "화",
        "label_hanja": "火",
        "strong": {
            "traits": ["열정", "표현력"],
            "description": "열정과 표현력이 넘쳐 주변을 밝게 비추는 힘이 있소.",
        },
        "weak": {
            "traits": ["인내심 부족"],
            "description": "화(火)의 기운이 부족하여 인내심이 약할 수 있으니 꾸준함을 기르시오.",
        },
        "lucky": {
            "color": "빨강",
            "color_code": "#FF4500",
            "direction": "남쪽",
            "direction_code": "S",
            "place": "햇빛 좋은 양지",
        },
    },
    "EARTH": {
        "label_ko": "토",
        "label_hanja": "土",
        "strong": {
            "traits": ["안정감", "신뢰"],
            "description": "안정감과 신뢰감이 있어 주변에 든든한 버팀목이 되오.",
        },
        "weak": {
            "traits": ["융통성 부족"],
            "description": "토(土)의 기운이 부족하여 융통성이 약할 수 있으니 유연함을 기르시오.",
        },
        "lucky": {
            "color": "노랑",
            "color_code": "#FFD700",
            "direction": "중앙",
            "direction_code": "E",  # 중앙은 별도 코드 없어 E로 대체
            "place": "평지나 들판",
        },
    },
    "METAL": {
        "label_ko": "금",
        "label_hanja": "金",
        "strong": {
            "traits": ["결단력", "추진력"],
            "description": "결단력과 추진력이 강하여 목표를 향해 나아가는 힘이 있소.",
        },
        "weak": {
            "traits": ["유연성 부족"],
            "description": "금(金)의 기운이 부족하여 유연성이 약할 수 있으니 부드러움을 기르시오.",
        },
        "lucky": {
            "color": "흰색",
            "color_code": "#FFFFFF",
            "direction": "서쪽",
            "direction_code": "W",
            "place": "도시나 빌딩가",
        },
    },
    "WATER": {
        "label_ko": "수",
        "label_hanja": "水",
        "strong": {
            "traits": ["지혜", "적응력"],
            "description": "지혜와 적응력이 뛰어나 어떤 상황에서도 유연하게 대처하오.",
        },
        "weak": {
            "traits": ["결단력 부족"],
            "description": "수(水)의 기운이 부족하여 결단력이 약할 수 있으니 과감함을 기르시오.",
        },
        "lucky": {
            "color": "검정",
            "color_code": "#191970",
            "direction": "북쪽",
            "direction_code": "N",
            "place": "물가나 분수대",
        },
    },
}

# 십신 그룹별 배지 매핑
TEN_GOD_GROUP_BADGES: dict[str, str] = {
    "BI_GYEOP": "BI_GYEOP_DOMINANT",
    "SIK_SANG": "SIK_SANG_DOMINANT",
    "JAE_SEONG": "JAE_SEONG_DOMINANT",
    "GWAN_SEONG": "GWAN_SEONG_DOMINANT",
    "IN_SEONG": "IN_SEONG_DOMINANT",
}

# 오행별 성향 배지 매핑
ELEMENT_ORIENTATION_BADGES: dict[str, str] = {
    "WOOD": "ACTION_ORIENTED",
    "FIRE": "ACTION_ORIENTED",
    "EARTH": "THOUGHT_ORIENTED",
    "METAL": "THOUGHT_ORIENTED",
    "WATER": "EMOTION_ORIENTED",
}


# ============================================================
# 서양 점성술 매핑 테이블
# ============================================================

# 태양 별자리별 성격 (12개)
SUN_SIGN_PERSONALITY: dict[str, dict[str, Any]] = {
    "ARIES": {
        "label_ko": "양자리",
        "traits": ["용감함", "열정적", "개척정신"],
        "description": (
            "당신은 용감하고 열정적인 개척자예요. "
            "도전을 두려워하지 않는 강한 추진력이 있어요."
        ),
    },
    "TAURUS": {
        "label_ko": "황소자리",
        "traits": ["안정적", "인내심", "감각적"],
        "description": (
            "당신은 안정적이고 인내심이 강해요. "
            "오감을 즐기며 현실적인 목표를 향해 꾸준히 나아가요."
        ),
    },
    "GEMINI": {
        "label_ko": "쌍둥이자리",
        "traits": ["지적 호기심", "소통력", "다재다능"],
        "description": (
            "당신은 지적 호기심이 넘치고 소통 능력이 뛰어나요. "
            "다양한 분야에 관심을 가지는 다재다능한 면이 있어요."
        ),
    },
    "CANCER": {
        "label_ko": "게자리",
        "traits": ["감성적", "보호본능", "가정적"],
        "description": (
            "당신은 감성이 풍부하고 보호본능이 강해요. "
            "가족과 소중한 사람들을 깊이 아끼는 따뜻한 마음을 가졌어요."
        ),
    },
    "LEO": {
        "label_ko": "사자자리",
        "traits": ["자신감", "카리스마", "관대함"],
        "description": (
            "당신은 자신감 넘치는 카리스마가 있어요. "
            "관대하고 따뜻한 리더십으로 주변을 빛나게 해요."
        ),
    },
    "VIRGO": {
        "label_ko": "처녀자리",
        "traits": ["분석력", "완벽주의", "실용적"],
        "description": (
            "당신은 분석력이 뛰어나고 완벽을 추구해요. "
            "실용적이고 세심한 접근으로 문제를 해결해요."
        ),
    },
    "LIBRA": {
        "label_ko": "천칭자리",
        "traits": ["균형감각", "외교적", "심미안"],
        "description": (
            "당신은 균형과 조화를 중시해요. "
            "외교적인 소통 능력과 아름다움을 추구하는 심미안이 있어요."
        ),
    },
    "SCORPIO": {
        "label_ko": "전갈자리",
        "traits": ["통찰력", "열정적", "집중력"],
        "description": (
            "당신은 깊은 통찰력과 강한 열정을 가졌어요. "
            "한번 마음먹은 일에 놀라운 집중력을 발휘해요."
        ),
    },
    "SAGITTARIUS": {
        "label_ko": "사수자리",
        "traits": ["자유로움", "낙관적", "모험정신"],
        "description": (
            "당신은 자유로운 영혼이에요. "
            "낙관적인 태도와 모험정신으로 넓은 세상을 탐험해요."
        ),
    },
    "CAPRICORN": {
        "label_ko": "염소자리",
        "traits": ["야망", "책임감", "현실적"],
        "description": (
            "당신은 야망이 크고 책임감이 강해요. "
            "현실적인 목표를 세우고 꾸준히 성취해나가요."
        ),
    },
    "AQUARIUS": {
        "label_ko": "물병자리",
        "traits": ["독창성", "혁신적", "인도주의"],
        "description": (
            "당신은 독창적이고 혁신적인 사고를 해요. "
            "인류를 위한 더 나은 미래를 꿈꾸는 이상주의자예요."
        ),
    },
    "PISCES": {
        "label_ko": "물고기자리",
        "traits": ["상상력", "공감능력", "직관적"],
        "description": (
            "당신은 상상력이 풍부하고 공감능력이 뛰어나요. "
            "직관적인 통찰로 보이지 않는 것을 느껴요."
        ),
    },
}

# 서양 원소별 특성
WESTERN_ELEMENT_TRAITS: dict[str, dict[str, Any]] = {
    "FIRE": {
        "label_ko": "불",
        "signs": ["ARIES", "LEO", "SAGITTARIUS"],
        "strong": {"traits": ["열정", "행동력", "리더십"]},
        "weak": {"traits": ["인내심 부족", "충동성"]},
        "badge": "FIRE_DOMINANT",
    },
    "EARTH": {
        "label_ko": "흙",
        "signs": ["TAURUS", "VIRGO", "CAPRICORN"],
        "strong": {"traits": ["현실감", "안정감", "인내심"]},
        "weak": {"traits": ["유연성 부족", "고집"]},
        "badge": "EARTH_DOMINANT",
    },
    "AIR": {
        "label_ko": "공기",
        "signs": ["GEMINI", "LIBRA", "AQUARIUS"],
        "strong": {"traits": ["지성", "소통력", "사교성"]},
        "weak": {"traits": ["감정 표현 부족", "우유부단"]},
        "badge": "AIR_DOMINANT",
    },
    "WATER": {
        "label_ko": "물",
        "signs": ["CANCER", "SCORPIO", "PISCES"],
        "strong": {"traits": ["감성", "직관력", "공감능력"]},
        "weak": {"traits": ["감정 기복", "과민함"]},
        "badge": "WATER_DOMINANT",
    },
}

# 태양 별자리별 행운 정보
ZODIAC_LUCKY_INFO: dict[str, dict[str, Any]] = {
    "ARIES": {
        "day": "화요일",
        "day_code": "TUE",
        "color": "빨강",
        "color_code": "#FF0000",
        "number": "9",
        "stone": "다이아몬드",
        "planet": "MARS",
    },
    "TAURUS": {
        "day": "금요일",
        "day_code": "FRI",
        "color": "녹색",
        "color_code": "#228B22",
        "number": "6",
        "stone": "에메랄드",
        "planet": "VENUS",
    },
    "GEMINI": {
        "day": "수요일",
        "day_code": "WED",
        "color": "노랑",
        "color_code": "#FFFF00",
        "number": "5",
        "stone": "사파이어",
        "planet": "MERCURY",
    },
    "CANCER": {
        "day": "월요일",
        "day_code": "MON",
        "color": "은색",
        "color_code": "#C0C0C0",
        "number": "2",
        "stone": "진주",
        "planet": "MOON",
    },
    "LEO": {
        "day": "일요일",
        "day_code": "SUN",
        "color": "금색",
        "color_code": "#FFD700",
        "number": "1",
        "stone": "호박",
        "planet": "SUN",
    },
    "VIRGO": {
        "day": "수요일",
        "day_code": "WED",
        "color": "회색",
        "color_code": "#808080",
        "number": "5",
        "stone": "사파이어",
        "planet": "MERCURY",
    },
    "LIBRA": {
        "day": "금요일",
        "day_code": "FRI",
        "color": "분홍",
        "color_code": "#FFC0CB",
        "number": "6",
        "stone": "오팔",
        "planet": "VENUS",
    },
    "SCORPIO": {
        "day": "화요일",
        "day_code": "TUE",
        "color": "진홍",
        "color_code": "#DC143C",
        "number": "9",
        "stone": "루비",
        "planet": "MARS",
    },
    "SAGITTARIUS": {
        "day": "목요일",
        "day_code": "THU",
        "color": "파랑",
        "color_code": "#0000FF",
        "number": "3",
        "stone": "자수정",
        "planet": "JUPITER",
    },
    "CAPRICORN": {
        "day": "토요일",
        "day_code": "SAT",
        "color": "검정",
        "color_code": "#000000",
        "number": "8",
        "stone": "오닉스",
        "planet": "SATURN",
    },
    "AQUARIUS": {
        "day": "토요일",
        "day_code": "SAT",
        "color": "남색",
        "color_code": "#000080",
        "number": "4",
        "stone": "가넷",
        "planet": "SATURN",
    },
    "PISCES": {
        "day": "목요일",
        "day_code": "THU",
        "color": "보라",
        "color_code": "#800080",
        "number": "7",
        "stone": "아쿠아마린",
        "planet": "JUPITER",
    },
}


# ============================================================
# 동양 사주 폴백 생성기
# ============================================================


class EasternFallbackGenerator:
    """사주 정보 기반 기본값 생성기

    LLM 호출이 완전히 실패했을 때 chart와 stats 정보를 기반으로
    규칙 기반 기본값을 생성합니다.
    """

    def generate(self, chart: Any, stats: Any) -> dict[str, Any]:
        """사주 폴백 응답 생성

        JSON 템플릿 기반으로 폴백 데이터를 생성합니다.
        템플릿에서 해당 키를 찾지 못하면 기본 로직으로 생성합니다.

        Args:
            chart: PillarChart 객체 (year, month, day, hour 기둥 정보)
            stats: EasternStats 객체 (five_elements, yin_yang, ten_gods 통계)

        Returns:
            LLM 응답과 동일한 구조의 dict:
            - personality: 일간 + 오행 기반 성격
            - strength: 강한 오행 기반 강점
            - weakness: 약한 오행 기반 약점
            - advice: 부족한 오행 보완 조언
            - badges: 오행/십신 통계 기반 배지
            - lucky: 약한 오행 보완 색상/방향/장소
            - message: 조합된 기본 메시지 (하오체)
            - summary: 한줄 요약
        """
        logger.info("eastern_fallback_generate_start")

        try:
            # 일간 정보 추출
            day_master_code = self._get_day_master_code(chart)

            # 오행 통계 추출
            strong_element = self._get_strong_element(stats)
            weak_element = self._get_weak_element(stats)

            # 십신 통계 추출
            dominant_ten_god = self._get_dominant_ten_god(stats)

            # 음양 통계 추출
            yin_yang = self._get_yin_yang_info(stats)

            # 음양 상태 문자열 변환
            yang_percent = yin_yang.get("yang", 50)
            if yang_percent >= 60:
                yin_yang_str = "YANG"
            elif yang_percent <= 40:
                yin_yang_str = "YIN"
            else:
                yin_yang_str = "BALANCED"

            # JSON 템플릿에서 기본 데이터 조회
            template_data = get_eastern_fallback_data(
                day_master=day_master_code,
                strong_element=strong_element,
                yin_yang=yin_yang_str,
            )

            # 템플릿 데이터 우선 사용, 없으면 기존 로직으로 생성
            personality = template_data.get("personality") or self._generate_personality(
                day_master_code, strong_element
            )
            strength = template_data.get("strength") or self._generate_strength(strong_element)
            weakness = self._generate_weakness(weak_element)  # weak_element 기반이므로 별도 생성
            advice = self._generate_advice(weak_element)  # weak_element 기반이므로 별도 생성
            badges = self._generate_badges(strong_element, weak_element, yin_yang, dominant_ten_god)
            lucky = self._generate_lucky(weak_element)  # weak_element 기반 행운 정보
            message = template_data.get("message") or self._generate_message(
                personality, strength, weak_element
            )
            summary = self._generate_summary(day_master_code, strong_element, weak_element)

            result = {
                "personality": personality,
                "strength": strength,
                "weakness": weakness,
                "advice": advice,
                "badges": badges,
                "lucky": lucky,
                "message": message,
                "summary": summary,
            }

            logger.info(
                "eastern_fallback_generate_complete",
                day_master=day_master_code,
                strong=strong_element,
                weak=weak_element,
                template_used=bool(template_data.get("personality")),
            )

            return result

        except Exception as e:
            logger.error("eastern_fallback_generate_error", error=str(e))
            # 최소한의 기본값 반환
            return self._get_minimal_fallback()

    def _get_day_master_code(self, chart: Any) -> str:
        """일간 코드 추출"""
        try:
            # chart.day.gan_code가 Enum일 수 있음
            gan_code = chart.day.gan_code
            if hasattr(gan_code, "value"):
                return gan_code.value
            return str(gan_code)
        except Exception:
            return "GAP"  # 기본값

    def _get_strong_element(self, stats: Any) -> str:
        """강한 오행 추출"""
        try:
            five_elements = stats.five_elements
            if isinstance(five_elements, dict):
                return five_elements.get("strong", "WOOD")
            return getattr(five_elements, "strong", "WOOD")
        except Exception:
            return "WOOD"

    def _get_weak_element(self, stats: Any) -> str:
        """약한 오행 추출"""
        try:
            five_elements = stats.five_elements
            if isinstance(five_elements, dict):
                return five_elements.get("weak", "WATER")
            return getattr(five_elements, "weak", "WATER")
        except Exception:
            return "WATER"

    def _get_dominant_ten_god(self, stats: Any) -> str:
        """우세 십신 그룹 추출"""
        try:
            ten_gods = stats.ten_gods
            if isinstance(ten_gods, dict):
                return ten_gods.get("dominant", "BI_GYEOP")
            return getattr(ten_gods, "dominant", "BI_GYEOP")
        except Exception:
            return "BI_GYEOP"

    def _get_yin_yang_info(self, stats: Any) -> dict[str, Any]:
        """음양 정보 추출"""
        try:
            yin_yang = stats.yin_yang
            yang = getattr(yin_yang, "yang", 50)
            return {"yang": yang, "yin": 100 - yang}
        except Exception:
            return {"yang": 50, "yin": 50}

    def _generate_personality(self, day_master_code: str, strong_element: str) -> str:
        """성격 분석 생성"""
        master_info = DAY_MASTER_PERSONALITY.get(day_master_code, DAY_MASTER_PERSONALITY["GAP"])
        element_info = ELEMENT_TRAITS.get(strong_element, ELEMENT_TRAITS["WOOD"])

        traits = master_info["traits"]
        element_traits = element_info["strong"]["traits"]

        return (
            f"{master_info['hangul']} 일간으로 태어나 "
            f"{', '.join(traits[:2])}의 성향을 가지고 있소. "
            f"{element_info['label_ko']}({element_info['label_hanja']}) 기운이 강하여 "
            f"{', '.join(element_traits)}이 뛰어나오."
        )

    def _generate_strength(self, strong_element: str) -> str:
        """강점 분석 생성"""
        element_info = ELEMENT_TRAITS.get(strong_element, ELEMENT_TRAITS["WOOD"])
        return element_info["strong"]["description"]

    def _generate_weakness(self, weak_element: str) -> str:
        """약점 분석 생성"""
        element_info = ELEMENT_TRAITS.get(weak_element, ELEMENT_TRAITS["WATER"])
        return element_info["weak"]["description"]

    def _generate_advice(self, weak_element: str) -> str:
        """조언 생성"""
        element_info = ELEMENT_TRAITS.get(weak_element, ELEMENT_TRAITS["WATER"])
        lucky = element_info["lucky"]

        return (
            f"{element_info['label_ko']}({element_info['label_hanja']})의 기운을 보완하기 위해 "
            f"{lucky['color']}색 계열의 물건을 활용하고, {lucky['direction']} 방향의 "
            f"{lucky['place']}을 자주 방문하시오."
        )

    def _generate_badges(
        self,
        strong_element: str,
        weak_element: str,
        yin_yang: dict[str, Any],
        dominant_ten_god: str,
    ) -> list[str]:
        """배지 목록 생성"""
        badges = []

        # 오행 강약 배지
        badges.append(f"{strong_element}_STRONG")
        badges.append(f"{weak_element}_WEAK")

        # 음양 배지
        yang = yin_yang.get("yang", 50)
        if yang >= 60:
            badges.append("YANG_DOMINANT")
        elif yang <= 40:
            badges.append("YIN_DOMINANT")
        else:
            badges.append("YIN_YANG_BALANCED")

        # 십신 배지
        ten_god_badge = TEN_GOD_GROUP_BADGES.get(dominant_ten_god)
        if ten_god_badge:
            badges.append(ten_god_badge)

        # 성향 배지 (강한 오행 기반)
        orientation_badge = ELEMENT_ORIENTATION_BADGES.get(strong_element)
        if orientation_badge and len(badges) < 5:
            badges.append(orientation_badge)

        return badges

    def _generate_lucky(self, weak_element: str) -> dict[str, str]:
        """행운 정보 생성 (약한 오행 보완)"""
        element_info = ELEMENT_TRAITS.get(weak_element, ELEMENT_TRAITS["WATER"])
        lucky = element_info["lucky"]

        return {
            "color": lucky["color"],
            "color_code": lucky["color_code"],
            "number": str((list(ELEMENT_TRAITS.keys()).index(weak_element) + 1) * 2 + 1),
            "item": self._get_lucky_item(weak_element),
            "direction": lucky["direction"],
            "direction_code": lucky["direction_code"],
            "place": lucky["place"],
        }

    def _get_lucky_item(self, element: str) -> str:
        """오행별 행운 아이템"""
        items = {
            "WOOD": "나무 소품",
            "FIRE": "붉은 수정",
            "EARTH": "황옥 팔찌",
            "METAL": "은 반지",
            "WATER": "물병 장식",
        }
        return items.get(element, "수정")

    def _generate_message(self, personality: str, strength: str, weak_element: str) -> str:
        """상세 메시지 생성 (하오체)"""
        element_info = ELEMENT_TRAITS.get(weak_element, ELEMENT_TRAITS["WATER"])

        return (
            f"{personality} "
            f"{strength} "
            f"다만 {element_info['label_ko']}({element_info['label_hanja']}) 기운이 부족하니 "
            f"이를 보완하면 더욱 좋은 운을 맞이할 수 있소."
        )

    def _generate_summary(
        self, day_master_code: str, strong_element: str, weak_element: str
    ) -> str:
        """한줄 요약 생성"""
        master_info = DAY_MASTER_PERSONALITY.get(day_master_code, DAY_MASTER_PERSONALITY["GAP"])
        strong_info = ELEMENT_TRAITS.get(strong_element, ELEMENT_TRAITS["WOOD"])
        weak_info = ELEMENT_TRAITS.get(weak_element, ELEMENT_TRAITS["WATER"])

        return (
            f"{strong_info['label_ko']}({strong_info['label_hanja']})이 강한 "
            f"{master_info['traits'][0]}형, "
            f"{weak_info['label_ko']}({weak_info['label_hanja']}) 보완 필요"
        )

    def _get_minimal_fallback(self) -> dict[str, Any]:
        """최소한의 기본값"""
        return {
            "personality": "밝고 긍정적인 성격을 지니고 있소.",
            "strength": "타고난 재능과 잠재력이 있소.",
            "weakness": "꾸준한 노력으로 부족한 부분을 채워가시오.",
            "advice": "자신의 장점을 살리고 균형 잡힌 생활을 하시오.",
            "badges": ["YIN_YANG_BALANCED"],
            "lucky": {
                "color": "흰색",
                "color_code": "#FFFFFF",
                "number": "7",
                "item": "수정",
                "direction": "동쪽",
                "direction_code": "E",
                "place": "자연 속",
            },
            "message": "좋은 기운이 함께하고 있소. 자신감을 가지고 나아가시오.",
            "summary": "균형 잡힌 사주, 꾸준한 노력이 열쇠",
        }


# ============================================================
# 서양 점성술 폴백 생성기
# ============================================================


class WesternFallbackGenerator:
    """점성술 정보 기반 기본값 생성기

    LLM 호출이 완전히 실패했을 때 big_three와 element_stats 정보를 기반으로
    규칙 기반 기본값을 생성합니다.
    """

    def generate(
        self,
        big_three: dict[str, Any] | None = None,
        element_stats: dict[str, Any] | None = None,
        sun_sign: str | None = None,
    ) -> dict[str, Any]:
        """점성술 폴백 응답 생성

        JSON 템플릿 기반으로 폴백 데이터를 생성합니다.
        템플릿에서 해당 키를 찾지 못하면 기본 로직으로 생성합니다.

        Args:
            big_three: 빅3 정보 (sun, moon, rising)
            element_stats: 원소 통계 (fire, earth, air, water)
            sun_sign: 태양 별자리 코드 (big_three가 없을 때 사용)

        Returns:
            LLM 응답과 동일한 구조의 dict
        """
        logger.info("western_fallback_generate_start")

        try:
            # 태양 별자리 추출
            sun_sign_code = self._get_sun_sign(big_three, sun_sign)

            # 달 별자리 추출
            moon_sign_code = self._get_moon_sign(big_three)

            # 우세 원소 추출
            dominant_element = self._get_dominant_element(element_stats, sun_sign_code)

            # JSON 템플릿에서 기본 데이터 조회
            template_data = get_western_fallback_data(
                sun_sign=sun_sign_code,
                moon_sign=moon_sign_code,
                dominant_element=dominant_element,
            )

            # 템플릿 데이터 우선 사용, 없으면 기존 로직으로 생성
            personality = template_data.get("personality") or self._generate_personality(
                sun_sign_code
            )
            strength = template_data.get("strength") or self._generate_strength(dominant_element)
            weakness = template_data.get("weakness") or self._generate_weakness(dominant_element)
            advice = self._generate_advice(sun_sign_code, dominant_element)
            badges = self._generate_badges(sun_sign_code, dominant_element)
            lucky = template_data.get("lucky") or self._generate_lucky(sun_sign_code)
            message = template_data.get("message") or self._generate_message(
                sun_sign_code, dominant_element
            )
            summary = self._generate_summary(sun_sign_code, dominant_element)

            result = {
                "personality": personality,
                "strength": strength,
                "weakness": weakness,
                "advice": advice,
                "badges": badges,
                "lucky": lucky,
                "message": message,
                "summary": summary,
            }

            logger.info(
                "western_fallback_generate_complete",
                sun_sign=sun_sign_code,
                moon_sign=moon_sign_code,
                dominant_element=dominant_element,
                template_used=bool(template_data.get("personality")),
            )

            return result

        except Exception as e:
            logger.error("western_fallback_generate_error", error=str(e))
            return self._get_minimal_fallback()

    def _get_sun_sign(
        self,
        big_three: dict[str, Any] | None,
        sun_sign: str | None,
    ) -> str:
        """태양 별자리 추출"""
        if sun_sign:
            return sun_sign

        if big_three:
            try:
                sun_info = big_three.get("sun", {})
                if isinstance(sun_info, dict):
                    sign_code = sun_info.get("sign_code", "ARIES")
                else:
                    sign_code = getattr(sun_info, "sign_code", "ARIES")
                if hasattr(sign_code, "value"):
                    return sign_code.value
                return str(sign_code)
            except Exception:
                pass

        return "ARIES"

    def _get_moon_sign(
        self,
        big_three: dict[str, Any] | None,
    ) -> str:
        """달 별자리 추출"""
        if big_three:
            try:
                moon_info = big_three.get("moon", {})
                if isinstance(moon_info, dict):
                    sign_code = moon_info.get("sign_code", "ARIES")
                else:
                    sign_code = getattr(moon_info, "sign_code", "ARIES")
                if hasattr(sign_code, "value"):
                    return sign_code.value
                return str(sign_code)
            except Exception:
                pass

        return "ARIES"

    def _get_dominant_element(
        self,
        element_stats: dict[str, Any] | None,
        sun_sign_code: str,
    ) -> str:
        """우세 원소 추출"""
        if element_stats:
            try:
                if isinstance(element_stats, dict):
                    return element_stats.get("dominant", "FIRE")
                return getattr(element_stats, "dominant", "FIRE")
            except Exception:
                pass

        # 태양 별자리에서 원소 추론
        for element, info in WESTERN_ELEMENT_TRAITS.items():
            if sun_sign_code in info["signs"]:
                return element

        return "FIRE"

    def _generate_personality(self, sun_sign_code: str) -> str:
        """성격 분석 생성"""
        sign_info = SUN_SIGN_PERSONALITY.get(sun_sign_code, SUN_SIGN_PERSONALITY["ARIES"])
        return sign_info["description"]

    def _generate_strength(self, dominant_element: str) -> str:
        """강점 분석 생성"""
        element_info = WESTERN_ELEMENT_TRAITS.get(dominant_element, WESTERN_ELEMENT_TRAITS["FIRE"])
        traits = element_info["strong"]["traits"]

        return f"{element_info['label_ko']} 원소가 강하여 {', '.join(traits)}이 뛰어나요."

    def _generate_weakness(self, dominant_element: str) -> str:
        """약점 분석 생성"""
        element_info = WESTERN_ELEMENT_TRAITS.get(dominant_element, WESTERN_ELEMENT_TRAITS["FIRE"])
        traits = element_info["weak"]["traits"]

        return f"{', '.join(traits)}에 주의가 필요해요. 균형을 맞추는 것이 중요해요."

    def _generate_advice(self, sun_sign_code: str, dominant_element: str) -> str:
        """조언 생성"""
        sign_info = SUN_SIGN_PERSONALITY.get(sun_sign_code, SUN_SIGN_PERSONALITY["ARIES"])

        return (
            f"{sign_info['label_ko']}인 당신은 {sign_info['traits'][0]}을 살리되, "
            f"다른 원소의 특성도 균형있게 발전시켜 보세요."
        )

    def _generate_badges(self, sun_sign_code: str, dominant_element: str) -> list[str]:
        """배지 목록 생성"""
        badges = []

        # 원소 배지
        element_info = WESTERN_ELEMENT_TRAITS.get(dominant_element)
        if element_info:
            badges.append(element_info["badge"])

        # 태양 별자리 지배행성 배지
        lucky_info = ZODIAC_LUCKY_INFO.get(sun_sign_code)
        if lucky_info:
            planet = lucky_info.get("planet", "SUN")
            badges.append(f"{planet}_STRONG")

        # 성향 배지
        if dominant_element in ["FIRE", "AIR"]:
            badges.append("ACTION_ORIENTED")
        elif dominant_element in ["EARTH"]:
            badges.append("THOUGHT_ORIENTED")
        else:
            badges.append("EMOTION_ORIENTED")

        return badges

    def _generate_lucky(self, sun_sign_code: str) -> dict[str, str]:
        """행운 정보 생성"""
        lucky_info = ZODIAC_LUCKY_INFO.get(sun_sign_code, ZODIAC_LUCKY_INFO["ARIES"])
        return {
            "day": lucky_info["day"],
            "day_code": lucky_info["day_code"],
            "color": lucky_info["color"],
            "color_code": lucky_info["color_code"],
            "number": lucky_info["number"],
            "stone": lucky_info["stone"],
            "planet": lucky_info["planet"],
        }

    def _generate_message(self, sun_sign_code: str, dominant_element: str) -> str:
        """상세 메시지 생성 (해요체)"""
        sign_info = SUN_SIGN_PERSONALITY.get(sun_sign_code, SUN_SIGN_PERSONALITY["ARIES"])
        element_info = WESTERN_ELEMENT_TRAITS.get(dominant_element, WESTERN_ELEMENT_TRAITS["FIRE"])

        return (
            f"{sign_info['description']} "
            f"{element_info['label_ko']} 원소가 강하게 나타나서 "
            f"{', '.join(element_info['strong']['traits'][:2])}이 강점이에요. "
            f"이런 장점을 잘 살려보세요!"
        )

    def _generate_summary(self, sun_sign_code: str, dominant_element: str) -> str:
        """한줄 요약 생성"""
        sign_info = SUN_SIGN_PERSONALITY.get(sun_sign_code, SUN_SIGN_PERSONALITY["ARIES"])
        element_info = WESTERN_ELEMENT_TRAITS.get(dominant_element, WESTERN_ELEMENT_TRAITS["FIRE"])

        return (
            f"{sign_info['label_ko']} {element_info['label_ko']} 타입, "
            f"{sign_info['traits'][0]}이 매력"
        )

    def _get_minimal_fallback(self) -> dict[str, Any]:
        """최소한의 기본값"""
        return {
            "personality": "밝고 긍정적인 에너지를 가지고 있어요.",
            "strength": "타고난 잠재력과 매력이 있어요.",
            "weakness": "균형 잡힌 성장이 필요해요.",
            "advice": "자신의 장점을 살리며 나아가세요.",
            "badges": ["SUN_STRONG"],
            "lucky": {
                "day": "일요일",
                "day_code": "SUN",
                "color": "금색",
                "color_code": "#FFD700",
                "number": "1",
                "stone": "호박",
                "planet": "SUN",
            },
            "message": "좋은 에너지가 함께해요. 자신감을 가지세요!",
            "summary": "빛나는 매력의 소유자",
        }


# ============================================================
# 통합 폴백 함수
# ============================================================

# 싱글톤 인스턴스
_eastern_generator: EasternFallbackGenerator | None = None
_western_generator: WesternFallbackGenerator | None = None


def get_eastern_fallback(chart: Any, stats: Any) -> dict[str, Any]:
    """동양 사주 폴백 응답 생성

    LLM 호출이 완전히 실패했을 때 호출됩니다.
    chart와 stats 정보를 기반으로 규칙 기반 기본값을 생성합니다.

    Args:
        chart: PillarChart 객체
        stats: EasternStats 객체

    Returns:
        폴백 응답 dict
    """
    global _eastern_generator
    if _eastern_generator is None:
        _eastern_generator = EasternFallbackGenerator()

    return _eastern_generator.generate(chart, stats)


def get_western_fallback(
    big_three: dict[str, Any] | None = None,
    element_stats: dict[str, Any] | None = None,
    sun_sign: str | None = None,
) -> dict[str, Any]:
    """서양 점성술 폴백 응답 생성

    LLM 호출이 완전히 실패했을 때 호출됩니다.

    Args:
        big_three: 빅3 정보 dict
        element_stats: 원소 통계 dict
        sun_sign: 태양 별자리 코드 (옵션)

    Returns:
        폴백 응답 dict
    """
    global _western_generator
    if _western_generator is None:
        _western_generator = WesternFallbackGenerator()

    return _western_generator.generate(big_three, element_stats, sun_sign)
