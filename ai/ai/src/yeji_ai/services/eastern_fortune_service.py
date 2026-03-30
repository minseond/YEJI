"""동양 사주 분석 서비스

사주팔자 계산 및 분석 로직
"""

from datetime import datetime
from typing import Any

import structlog

from yeji_ai.models.enums import (
    CheonGanCode,
    ElementCode,
    JiJiCode,
    TenGodCode,
    TenGodGroupCode,
    YinYangBalance,
)
from yeji_ai.models.enums.domain_codes import EAST_ELEMENT_LABELS, TEN_GOD_LABELS
from yeji_ai.models.fortune.eastern import EasternFortuneRequest
from yeji_ai.models.user_fortune import (
    CheonganJiji,
    CheonganJijiItem,
    EasternChart,
    EasternLucky,
    EasternStats,
    FinalVerdict,
    FiveElements,
    Pillar,
    SajuDataV2,
    SajuElement,
    TenGods,
    YinYangRatio,
)

logger = structlog.get_logger()


# ============================================================
# 상수 정의
# ============================================================

# 천간 (10개)
HEAVENLY_STEMS = ["갑", "을", "병", "정", "무", "기", "경", "신", "임", "계"]
HEAVENLY_STEMS_HANJA = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]

# 지지 (12개)
EARTHLY_BRANCHES = ["자", "축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해"]
EARTHLY_BRANCHES_HANJA = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

# 60갑자
SIXTY_CYCLE = [
    f"{HEAVENLY_STEMS[i % 10]}{EARTHLY_BRANCHES[i % 12]}" for i in range(60)
]

# 천간 → CheonGanCode 매핑
STEM_TO_CODE: dict[str, CheonGanCode] = {
    "갑": CheonGanCode.GAP,
    "을": CheonGanCode.EUL,
    "병": CheonGanCode.BYEONG,
    "정": CheonGanCode.JEONG,
    "무": CheonGanCode.MU,
    "기": CheonGanCode.GI,
    "경": CheonGanCode.GYEONG,
    "신": CheonGanCode.SIN,
    "임": CheonGanCode.IM,
    "계": CheonGanCode.GYE,
}

# 지지 → JiJiCode 매핑
BRANCH_TO_CODE: dict[str, JiJiCode] = {
    "자": JiJiCode.JA,
    "축": JiJiCode.CHUK,
    "인": JiJiCode.IN,
    "묘": JiJiCode.MYO,
    "진": JiJiCode.JIN,
    "사": JiJiCode.SA,
    "오": JiJiCode.O,
    "미": JiJiCode.MI,
    "신": JiJiCode.SHIN,
    "유": JiJiCode.YU,
    "술": JiJiCode.SUL,
    "해": JiJiCode.HAE,
}

# 천간 → 오행 매핑
STEM_TO_ELEMENT: dict[str, ElementCode] = {
    "갑": ElementCode.WOOD,
    "을": ElementCode.WOOD,
    "병": ElementCode.FIRE,
    "정": ElementCode.FIRE,
    "무": ElementCode.EARTH,
    "기": ElementCode.EARTH,
    "경": ElementCode.METAL,
    "신": ElementCode.METAL,
    "임": ElementCode.WATER,
    "계": ElementCode.WATER,
}

# 지지 → 오행 매핑
BRANCH_TO_ELEMENT: dict[str, ElementCode] = {
    "자": ElementCode.WATER,
    "축": ElementCode.EARTH,
    "인": ElementCode.WOOD,
    "묘": ElementCode.WOOD,
    "진": ElementCode.EARTH,
    "사": ElementCode.FIRE,
    "오": ElementCode.FIRE,
    "미": ElementCode.EARTH,
    "신": ElementCode.METAL,
    "유": ElementCode.METAL,
    "술": ElementCode.EARTH,
    "해": ElementCode.WATER,
}

# 천간 → 음양 매핑 (True = 양)
STEM_IS_YANG: dict[str, bool] = {
    "갑": True, "을": False,
    "병": True, "정": False,
    "무": True, "기": False,
    "경": True, "신": False,
    "임": True, "계": False,
}

# 지지 → 음양 매핑
BRANCH_IS_YANG: dict[str, bool] = {
    "자": True, "축": False,
    "인": True, "묘": False,
    "진": True, "사": False,
    "오": True, "미": False,
    "신": True, "유": False,
    "술": True, "해": False,
}

# 십신 계산 테이블 (일간 기준 오행 관계)
# key: (일간 오행, 대상 오행), value: (같은 음양 십신, 다른 음양 십신)
TEN_GOD_TABLE: dict[tuple[ElementCode, ElementCode], tuple[TenGodCode, TenGodCode]] = {
    # 목 일간
    (ElementCode.WOOD, ElementCode.WOOD): (TenGodCode.BI_GYEON, TenGodCode.GANG_JAE),
    (ElementCode.WOOD, ElementCode.FIRE): (TenGodCode.SIK_SIN, TenGodCode.SANG_GWAN),
    (ElementCode.WOOD, ElementCode.EARTH): (TenGodCode.PYEON_JAE, TenGodCode.JEONG_JAE),
    (ElementCode.WOOD, ElementCode.METAL): (TenGodCode.PYEON_GWAN, TenGodCode.JEONG_GWAN),
    (ElementCode.WOOD, ElementCode.WATER): (TenGodCode.PYEON_IN, TenGodCode.JEONG_IN),
    # 화 일간
    (ElementCode.FIRE, ElementCode.FIRE): (TenGodCode.BI_GYEON, TenGodCode.GANG_JAE),
    (ElementCode.FIRE, ElementCode.EARTH): (TenGodCode.SIK_SIN, TenGodCode.SANG_GWAN),
    (ElementCode.FIRE, ElementCode.METAL): (TenGodCode.PYEON_JAE, TenGodCode.JEONG_JAE),
    (ElementCode.FIRE, ElementCode.WATER): (TenGodCode.PYEON_GWAN, TenGodCode.JEONG_GWAN),
    (ElementCode.FIRE, ElementCode.WOOD): (TenGodCode.PYEON_IN, TenGodCode.JEONG_IN),
    # 토 일간
    (ElementCode.EARTH, ElementCode.EARTH): (TenGodCode.BI_GYEON, TenGodCode.GANG_JAE),
    (ElementCode.EARTH, ElementCode.METAL): (TenGodCode.SIK_SIN, TenGodCode.SANG_GWAN),
    (ElementCode.EARTH, ElementCode.WATER): (TenGodCode.PYEON_JAE, TenGodCode.JEONG_JAE),
    (ElementCode.EARTH, ElementCode.WOOD): (TenGodCode.PYEON_GWAN, TenGodCode.JEONG_GWAN),
    (ElementCode.EARTH, ElementCode.FIRE): (TenGodCode.PYEON_IN, TenGodCode.JEONG_IN),
    # 금 일간
    (ElementCode.METAL, ElementCode.METAL): (TenGodCode.BI_GYEON, TenGodCode.GANG_JAE),
    (ElementCode.METAL, ElementCode.WATER): (TenGodCode.SIK_SIN, TenGodCode.SANG_GWAN),
    (ElementCode.METAL, ElementCode.WOOD): (TenGodCode.PYEON_JAE, TenGodCode.JEONG_JAE),
    (ElementCode.METAL, ElementCode.FIRE): (TenGodCode.PYEON_GWAN, TenGodCode.JEONG_GWAN),
    (ElementCode.METAL, ElementCode.EARTH): (TenGodCode.PYEON_IN, TenGodCode.JEONG_IN),
    # 수 일간
    (ElementCode.WATER, ElementCode.WATER): (TenGodCode.BI_GYEON, TenGodCode.GANG_JAE),
    (ElementCode.WATER, ElementCode.WOOD): (TenGodCode.SIK_SIN, TenGodCode.SANG_GWAN),
    (ElementCode.WATER, ElementCode.FIRE): (TenGodCode.PYEON_JAE, TenGodCode.JEONG_JAE),
    (ElementCode.WATER, ElementCode.EARTH): (TenGodCode.PYEON_GWAN, TenGodCode.JEONG_GWAN),
    (ElementCode.WATER, ElementCode.METAL): (TenGodCode.PYEON_IN, TenGodCode.JEONG_IN),
}

# 오행별 행운 정보
ELEMENT_LUCKY: dict[ElementCode, dict[str, Any]] = {
    ElementCode.WOOD: {
        "color": "초록색",
        "color_code": "#228B22",
        "number": "3, 8",
        "direction": "동쪽",
        "direction_code": "E",
        "place": "숲, 공원, 나무가 많은 곳",
        "item": "나무 액세서리, 식물",
    },
    ElementCode.FIRE: {
        "color": "빨간색",
        "color_code": "#FF4500",
        "number": "2, 7",
        "direction": "남쪽",
        "direction_code": "S",
        "place": "따뜻한 곳, 햇살이 드는 곳",
        "item": "빨간 악세서리, 양초",
    },
    ElementCode.EARTH: {
        "color": "노란색",
        "color_code": "#FFD700",
        "number": "5, 10",
        "direction": "중앙",
        "direction_code": None,
        "place": "평지, 황토방",
        "item": "도자기, 황토 제품",
    },
    ElementCode.METAL: {
        "color": "흰색",
        "color_code": "#FFFFFF",
        "number": "4, 9",
        "direction": "서쪽",
        "direction_code": "W",
        "place": "높은 곳, 깨끗한 곳",
        "item": "금속 액세서리, 시계",
    },
    ElementCode.WATER: {
        "color": "검정색",
        "color_code": "#000080",
        "number": "1, 6",
        "direction": "북쪽",
        "direction_code": "N",
        "place": "물가, 호수, 바다",
        "item": "수정, 유리 제품",
    },
}


class EasternFortuneService:
    """동양 사주 분석 서비스"""

    def __init__(self):
        """초기화"""
        pass

    def calculate_four_pillars(
        self,
        birth_date: str,
        birth_time: str | None = None,
    ) -> tuple[str, str, str, str | None]:
        """
        사주팔자(4기둥) 계산

        Args:
            birth_date: 생년월일 (YYYY-MM-DD)
            birth_time: 출생시간 (HH:MM)

        Returns:
            (연주, 월주, 일주, 시주) 튜플
        """
        dt = datetime.strptime(birth_date, "%Y-%m-%d")

        # 연주 계산 (입춘 기준이지만 간략화)
        year_idx = (dt.year - 4) % 60
        year_pillar = SIXTY_CYCLE[year_idx]

        # 월주 계산 (절기 기준이지만 간략화)
        # 연간 기준 월주 계산
        year_stem_idx = (dt.year - 4) % 10
        month_stem_idx = (year_stem_idx * 2 + dt.month) % 10
        month_branch_idx = (dt.month + 1) % 12  # 인월(1월)부터 시작
        month_pillar = f"{HEAVENLY_STEMS[month_stem_idx]}{EARTHLY_BRANCHES[month_branch_idx]}"

        # 일주 계산
        base_date = datetime(1900, 1, 31)  # 갑자일
        day_diff = (dt - base_date).days
        day_idx = day_diff % 60
        day_pillar = SIXTY_CYCLE[day_idx]

        # 시주 계산
        hour_pillar = None
        if birth_time:
            hour = int(birth_time.split(":")[0])
            # 시지 계산 (23-01: 자시, 01-03: 축시, ...)
            hour_branch_idx = ((hour + 1) // 2) % 12
            # 일간에 따른 시간 계산
            day_stem_idx = HEAVENLY_STEMS.index(day_pillar[0])
            hour_stem_idx = (day_stem_idx * 2 + hour_branch_idx) % 10
            hour_pillar = f"{HEAVENLY_STEMS[hour_stem_idx]}{EARTHLY_BRANCHES[hour_branch_idx]}"

        logger.debug(
            "four_pillars_calculated",
            year=year_pillar,
            month=month_pillar,
            day=day_pillar,
            hour=hour_pillar,
        )

        return year_pillar, month_pillar, day_pillar, hour_pillar

    def get_ten_god(
        self,
        day_stem: str,
        target_stem: str,
    ) -> TenGodCode:
        """
        십신 계산

        Args:
            day_stem: 일간 (갑, 을, 병, ...)
            target_stem: 대상 천간

        Returns:
            십신 코드
        """
        if day_stem == target_stem:
            return TenGodCode.DAY_MASTER

        day_element = STEM_TO_ELEMENT[day_stem]
        target_element = STEM_TO_ELEMENT[target_stem]

        day_is_yang = STEM_IS_YANG[day_stem]
        target_is_yang = STEM_IS_YANG[target_stem]

        same_yinyang = day_is_yang == target_is_yang

        ten_god_pair = TEN_GOD_TABLE[(day_element, target_element)]
        return ten_god_pair[0] if same_yinyang else ten_god_pair[1]

    def pillar_to_model(
        self,
        pillar: str,
        day_stem: str,
        is_day_pillar: bool = False,
    ) -> Pillar:
        """
        간지 문자열을 Pillar 모델로 변환 (신버전 스키마)

        Args:
            pillar: 간지 (예: "갑자")
            day_stem: 일간 (십신 계산용)
            is_day_pillar: 일주 여부

        Returns:
            Pillar 모델 (신버전)
        """
        stem = pillar[0]
        branch = pillar[1]

        # 기둥 전체의 오행 (천간 기준)
        element = STEM_TO_ELEMENT[stem]

        # 한자 변환
        stem_idx = HEAVENLY_STEMS.index(stem)
        branch_idx = EARTHLY_BRANCHES.index(branch)

        # 천간/지지 코드
        gan_code = STEM_TO_CODE[stem]
        ji_code = BRANCH_TO_CODE[branch]

        # 십신 계산 (일주는 DAY_MASTER)
        if is_day_pillar:
            ten_god_code = TenGodCode.DAY_MASTER
        else:
            ten_god_code = self.get_ten_god(day_stem, stem)

        return Pillar(
            gan=HEAVENLY_STEMS_HANJA[stem_idx],
            gan_code=gan_code,
            ji=EARTHLY_BRANCHES_HANJA[branch_idx],
            ji_code=ji_code,
            element_code=element,
            ten_god_code=ten_god_code,
        )

    def calculate_element_stats(
        self,
        pillars: list[str],
    ) -> dict[str, Any]:
        """
        오행 통계 계산

        Args:
            pillars: 간지 목록

        Returns:
            오행 분포 딕셔너리
        """
        counts: dict[ElementCode, int] = {e: 0 for e in ElementCode}

        for pillar in pillars:
            if pillar:
                stem = pillar[0]
                branch = pillar[1]
                counts[STEM_TO_ELEMENT[stem]] += 1
                counts[BRANCH_TO_ELEMENT[branch]] += 1

        total = sum(counts.values())

        elements = []
        for element in ElementCode:
            elements.append({
                "code": element.value,
                "label": element.label_ko,
                "value": counts[element],
                "percent": round(counts[element] / total * 100, 1) if total > 0 else 0,
            })

        # 강/약 오행
        strong = max(counts, key=counts.get)
        weak = min(counts, key=counts.get)

        # 요약 생성
        strong_name = strong.label_ko
        weak_name = weak.label_ko
        summary = f"{strong_name}이(가) 강하고 {weak_name}이(가) 약합니다"

        return {
            "summary": summary,
            "elements": elements,
            "strong": strong.value,
            "weak": weak.value,
        }

    def calculate_yinyang_stats(
        self,
        pillars: list[str],
    ) -> YinYangRatio:
        """
        음양 통계 계산 (신버전 스키마)

        Args:
            pillars: 간지 목록

        Returns:
            음양 비율 (YinYangRatio)
        """
        yang_count = 0
        yin_count = 0

        for pillar in pillars:
            if pillar:
                stem = pillar[0]
                branch = pillar[1]

                if STEM_IS_YANG[stem]:
                    yang_count += 1
                else:
                    yin_count += 1

                if BRANCH_IS_YANG[branch]:
                    yang_count += 1
                else:
                    yin_count += 1

        total = yang_count + yin_count
        yang_percent = round(yang_count / total * 100, 1) if total > 0 else 50.0
        yin_percent = round(100 - yang_percent, 1)

        balance = YinYangBalance.from_ratio(int(yang_percent))

        if balance == YinYangBalance.STRONG_YANG:
            summary = "양의 기운이 매우 강합니다"
        elif balance == YinYangBalance.SLIGHT_YANG:
            summary = "양이 약간 우세합니다"
        elif balance == YinYangBalance.BALANCED:
            summary = "음양이 균형을 이룹니다"
        elif balance == YinYangBalance.SLIGHT_YIN:
            summary = "음이 약간 우세합니다"
        else:
            summary = "음의 기운이 매우 강합니다"

        return YinYangRatio(
            summary=summary,
            yin=yin_percent,
            yang=yang_percent,
        )

    def calculate_ten_god_stats(
        self,
        pillars: list[str],
        day_stem: str,
    ) -> dict[str, Any]:
        """
        십신 통계 계산

        Args:
            pillars: 간지 목록
            day_stem: 일간

        Returns:
            십신 분포 딕셔너리
        """
        counts: dict[TenGodCode, int] = {t: 0 for t in TenGodCode}

        for pillar in pillars:
            if pillar:
                stem = pillar[0]
                ten_god = self.get_ten_god(day_stem, stem)
                counts[ten_god] += 1

        # 일간 제외하고 계산
        counts[TenGodCode.DAY_MASTER] = 0

        total = sum(counts.values())

        gods = []
        for ten_god in TenGodCode:
            if ten_god == TenGodCode.DAY_MASTER:
                continue
            # 모든 십신 반환 (0%도 포함)
            gods.append({
                "code": ten_god.value,
                "label": ten_god.label_ko,
                "group_code": ten_god.group,
                "value": counts[ten_god],
                "percent": round(counts[ten_god] / total * 100, 1) if total > 0 else 0,
            })

        # 그룹별 합계
        group_counts: dict[TenGodGroupCode, int] = {g: 0 for g in TenGodGroupCode}
        for ten_god, count in counts.items():
            if ten_god != TenGodCode.DAY_MASTER:
                group_counts[TenGodGroupCode(ten_god.group)] += count

        dominant_group = max(group_counts, key=group_counts.get)

        # 요약 생성
        group_meanings = {
            TenGodGroupCode.BI_GYEOP: "자아와 경쟁심이 강합니다",
            TenGodGroupCode.SIK_SANG: "표현력과 창의성이 뛰어납니다",
            TenGodGroupCode.JAE_SEONG: "재물 복과 현실 감각이 좋습니다",
            TenGodGroupCode.GWAN_SEONG: "명예와 책임감이 강합니다",
            TenGodGroupCode.IN_SEONG: "학문과 지혜가 뛰어납니다",
        }
        summary = f"{dominant_group.label_ko}이(가) 강하여 {group_meanings[dominant_group]}"

        return {
            "summary": summary,
            "gods": gods,
            "dominant": dominant_group.value,
        }

    def generate_lucky_info(
        self,
        weak_element: ElementCode,
    ) -> EasternLucky:
        """
        행운 정보 생성 (신버전 스키마)

        Args:
            weak_element: 약한 오행

        Returns:
            행운 정보 (EasternLucky)
        """
        lucky_data = ELEMENT_LUCKY[weak_element]

        return EasternLucky(
            color=lucky_data["color"],
            number=lucky_data["number"],
            item=lucky_data["item"],
            direction=lucky_data["direction"],
            place=lucky_data["place"],
        )

    async def analyze(
        self,
        request: EasternFortuneRequest,
    ) -> SajuDataV2:
        """
        동양 사주 분석 실행 (프론트엔드 확정 스키마)

        Args:
            request: 분석 요청

        Returns:
            SajuDataV2 응답
        """
        logger.info("eastern_analysis_start", birth_date=request.birth_date)

        # 1. 사주팔자 계산
        year, month, day, hour = self.calculate_four_pillars(
            request.birth_date,
            request.birth_time,
        )

        pillars = [year, month, day, hour] if hour else [year, month, day]
        day_stem = day[0]

        # 2. Pillar 모델 생성 (신버전)
        year_pillar = self.pillar_to_model(year, day_stem)
        month_pillar = self.pillar_to_model(month, day_stem)
        day_pillar = self.pillar_to_model(day, day_stem, is_day_pillar=True)
        hour_pillar = self.pillar_to_model(hour, day_stem) if hour else Pillar(
            gan="己",  # 기(己) - 천간 한자
            gan_code=CheonGanCode.GI,  # 기 - 토 오행
            ji="未",  # 미(未) - 지지 한자
            ji_code=JiJiCode.MI,  # 미 - 토 오행
            element_code=ElementCode.EARTH,
            ten_god_code=TenGodCode.BI_GYEON,  # 기본값
        )

        # 사주 요약 (한자)
        chart_summary = (
            f"{year_pillar.gan}{year_pillar.ji}년 "
            f"{month_pillar.gan}{month_pillar.ji}월 "
            f"{day_pillar.gan}{day_pillar.ji}일"
        )
        if hour:
            chart_summary += f" {hour_pillar.gan}{hour_pillar.ji}시"

        chart = EasternChart(
            summary=chart_summary,
            year=year_pillar,
            month=month_pillar,
            day=day_pillar,
            hour=hour_pillar,
        )

        # 3. 통계 계산
        element_stats = self.calculate_element_stats(pillars)
        yinyang_ratio = self.calculate_yinyang_stats(pillars)
        ten_god_stats = self.calculate_ten_god_stats(pillars, day_stem)

        # 강/약 오행
        strong_element = ElementCode(element_stats["strong"])
        weak_element = ElementCode(element_stats["weak"])

        # 4. CheonganJiji 생성 (프론트엔드 스키마에 맞춤)
        cheongan_jiji = CheonganJiji(
            summary=chart_summary,
            year=CheonganJijiItem(cheon_gan=year_pillar.gan, ji_ji=year_pillar.ji),
            month=CheonganJijiItem(cheon_gan=month_pillar.gan, ji_ji=month_pillar.ji),
            day=CheonganJijiItem(cheon_gan=day_pillar.gan, ji_ji=day_pillar.ji),
            hour=CheonganJijiItem(cheon_gan=hour_pillar.gan, ji_ji=hour_pillar.ji),
        )

        # 5. FiveElements 생성 (신버전 스키마)
        five_elements_list = []
        for elem in element_stats["elements"]:
            five_elements_list.append(SajuElement(
                code=elem["code"],
                label=EAST_ELEMENT_LABELS.get(elem["code"], elem["label"]),
                percent=elem["percent"],
            ))

        five_elements = FiveElements(
            summary=element_stats["summary"],
            elements_list=five_elements_list,
        )

        # 6. TenGods 생성 (상위 3개 이상, ETC는 옵션)
        gods_list = []
        sorted_gods = sorted(ten_god_stats["gods"], key=lambda x: x["percent"], reverse=True)

        # 최소 3개 보장 (값이 있는 것만)
        non_zero_gods = [g for g in sorted_gods if g["percent"] > 0]
        top_gods = non_zero_gods[:3] if len(non_zero_gods) >= 3 else non_zero_gods

        # 3개 미만이면 0%인 것도 포함하여 3개 채우기
        if len(top_gods) < 3:
            remaining_gods = [g for g in sorted_gods if g not in top_gods][:3 - len(top_gods)]
            top_gods.extend(remaining_gods)

        # ETC 계산 (상위 3개 이외의 합)
        etc_percent = sum(g["percent"] for g in sorted_gods[3:]) if len(sorted_gods) > 3 else 0

        for god in top_gods:
            gods_list.append(SajuElement(
                code=god["code"],
                label=TEN_GOD_LABELS.get(god["code"], god["label"]),
                percent=god["percent"],
            ))

        if etc_percent > 0:
            gods_list.append(SajuElement(
                code="ETC",
                label="기타",
                percent=round(etc_percent, 1),
            ))

        ten_gods = TenGods(
            summary=ten_god_stats["summary"],
            gods_list=gods_list,
        )

        # 7. EasternStats 생성 (신버전)
        stats = EasternStats(
            cheongan_jiji=cheongan_jiji,
            five_elements=five_elements,
            yin_yang_ratio=yinyang_ratio,
            ten_gods=ten_gods,
        )

        # 8. FinalVerdict 생성
        strength_meanings = {
            ElementCode.WOOD: "성장과 발전의 에너지가 넘칩니다",
            ElementCode.FIRE: "열정과 리더십이 뛰어납니다",
            ElementCode.EARTH: "안정감과 신뢰성이 높습니다",
            ElementCode.METAL: "결단력과 실행력이 강합니다",
            ElementCode.WATER: "지혜와 유연성이 뛰어납니다",
        }
        weakness_meanings = {
            ElementCode.WOOD: "유연성이 부족할 수 있습니다",
            ElementCode.FIRE: "추진력이 약할 수 있습니다",
            ElementCode.EARTH: "안정감이 부족할 수 있습니다",
            ElementCode.METAL: "결단력이 약할 수 있습니다",
            ElementCode.WATER: "적응력이 부족할 수 있습니다",
        }

        day_element = STEM_TO_ELEMENT[day_stem]
        summary_text = (
            f"{day_stem} 일간({day_element.label_ko})으로 태어나셨습니다. "
            f"{strong_element.label_ko}의 기운이 강하고 "
            f"{weak_element.label_ko}의 기운이 약합니다."
        )

        final_verdict = FinalVerdict(
            summary=summary_text,
            strength=(
                f"{strong_element.label_ko}의 기운이 강하여 "
                f"{strength_meanings[strong_element]}"
            ),
            weakness=(
                f"{weak_element.label_ko}의 기운이 부족하여 "
                f"{weakness_meanings[weak_element]}"
            ),
            advice=(
                f"{weak_element.label_ko}의 기운을 보완하면 "
                "더욱 균형 잡힌 운세를 만들 수 있습니다."
            ),
        )

        # 9. 행운 정보
        lucky = self.generate_lucky_info(weak_element)

        logger.info("eastern_analysis_complete", birth_date=request.birth_date)

        return SajuDataV2(
            element=strong_element.value,
            chart=chart,
            stats=stats,
            final_verdict=final_verdict,
            lucky=lucky,
        )
