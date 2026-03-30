#!/usr/bin/env python3
"""20대 남녀 출생 조합 테스트 데이터 생성 스크립트

1995-2005년생 남녀 각 5명씩 총 10명의 출생 데이터를 생성하고
사주 계산 및 점성술 데이터 생성, 품질 검증을 수행합니다.
"""

import json
import random
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

import structlog

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(project_root))

from yeji_ai.engine.saju_calculator import SajuCalculator

logger = structlog.get_logger()

# ============================================================
# 점성술 상수 정의
# ============================================================

# 12별자리 (생일 기준)
ZODIAC_SIGNS = [
    {"code": "CAPRICORN", "label": "염소자리", "start": (1, 1), "end": (1, 19), "element": "EARTH", "modality": "CARDINAL"},
    {"code": "AQUARIUS", "label": "물병자리", "start": (1, 20), "end": (2, 18), "element": "AIR", "modality": "FIXED"},
    {"code": "PISCES", "label": "물고기자리", "start": (2, 19), "end": (3, 20), "element": "WATER", "modality": "MUTABLE"},
    {"code": "ARIES", "label": "양자리", "start": (3, 21), "end": (4, 19), "element": "FIRE", "modality": "CARDINAL"},
    {"code": "TAURUS", "label": "황소자리", "start": (4, 20), "end": (5, 20), "element": "EARTH", "modality": "FIXED"},
    {"code": "GEMINI", "label": "쌍둥이자리", "start": (5, 21), "end": (6, 20), "element": "AIR", "modality": "MUTABLE"},
    {"code": "CANCER", "label": "게자리", "start": (6, 21), "end": (7, 22), "element": "WATER", "modality": "CARDINAL"},
    {"code": "LEO", "label": "사자자리", "start": (7, 23), "end": (8, 22), "element": "FIRE", "modality": "FIXED"},
    {"code": "VIRGO", "label": "처녀자리", "start": (8, 23), "end": (9, 22), "element": "EARTH", "modality": "MUTABLE"},
    {"code": "LIBRA", "label": "천칭자리", "start": (9, 23), "end": (10, 22), "element": "AIR", "modality": "CARDINAL"},
    {"code": "SCORPIO", "label": "전갈자리", "start": (10, 23), "end": (11, 21), "element": "WATER", "modality": "FIXED"},
    {"code": "SAGITTARIUS", "label": "사수자리", "start": (11, 22), "end": (12, 21), "element": "FIRE", "modality": "MUTABLE"},
    {"code": "CAPRICORN", "label": "염소자리", "start": (12, 22), "end": (12, 31), "element": "EARTH", "modality": "CARDINAL"},
]

ELEMENT_LABELS = {"FIRE": "불", "WATER": "물", "AIR": "공기", "EARTH": "흙"}
MODALITY_LABELS = {"CARDINAL": "활동궁", "FIXED": "고정궁", "MUTABLE": "변통궁"}


def get_zodiac_sign(month: int, day: int) -> dict:
    """생년월일로 별자리 찾기"""
    for sign in ZODIAC_SIGNS:
        start_m, start_d = sign["start"]
        end_m, end_d = sign["end"]

        if start_m == end_m:
            if month == start_m and start_d <= day <= end_d:
                return sign
        elif month == start_m and day >= start_d:
            return sign
        elif month == end_m and day <= end_d:
            return sign

    return ZODIAC_SIGNS[0]  # 기본값: 염소자리


def calculate_western_astrology(birth_date: str, birth_time: str, month: int, day: int, hour: int) -> dict:
    """점성술 데이터 계산 (실서비스 API 양식 - WesternFortuneDataV2)

    Args:
        birth_date: 생년월일 (YYYY-MM-DD)
        birth_time: 생시 (HH:MM)
        month: 생월
        day: 생일
        hour: 생시

    Returns:
        WesternFortuneDataV2 형식의 점성술 데이터 딕셔너리
    """
    # 태양 별자리 (생일 기준)
    sun_sign = get_zodiac_sign(month, day)

    # 달 별자리 (간략화: 태양 별자리 + 2~3칸)
    moon_offset = (day % 4) + 1
    moon_idx = (ZODIAC_SIGNS.index(sun_sign) + moon_offset) % 12
    moon_sign = ZODIAC_SIGNS[moon_idx]

    # 상승궁 (생시 기준 - 2시간당 1별자리)
    rising_idx = (hour // 2) % 12
    rising_sign = ZODIAC_SIGNS[rising_idx]

    # 4원소 분포 계산 (빅3 기준)
    elements = {"FIRE": 0, "WATER": 0, "AIR": 0, "EARTH": 0}
    elements[sun_sign["element"]] += 3  # 태양: 가중치 3
    elements[moon_sign["element"]] += 2  # 달: 가중치 2
    elements[rising_sign["element"]] += 1  # 상승: 가중치 1

    # 랜덤하게 나머지 행성 분포 추가 (총 10개 행성 기준)
    for _ in range(4):
        random_elem = random.choice(list(elements.keys()))
        elements[random_elem] += 1

    total_elem = sum(elements.values())
    element_4_distribution = [
        {
            "code": code,
            "label": ELEMENT_LABELS[code],
            "percent": round(value / total_elem * 100, 1),
        }
        for code, value in elements.items()
    ]

    # 3양태 분포 계산
    modalities = {"CARDINAL": 0, "FIXED": 0, "MUTABLE": 0}
    modalities[sun_sign["modality"]] += 3
    modalities[moon_sign["modality"]] += 2
    modalities[rising_sign["modality"]] += 1

    for _ in range(4):
        random_mod = random.choice(list(modalities.keys()))
        modalities[random_mod] += 1

    total_mod = sum(modalities.values())
    modality_3_distribution = [
        {
            "code": code,
            "label": MODALITY_LABELS[code],
            "percent": round(value / total_mod * 100, 1),
        }
        for code, value in modalities.items()
    ]

    # 우세 원소/양태
    dominant_element = max(elements, key=elements.get)
    dominant_modality = max(modalities, key=modalities.get)

    # 키워드 생성 (원소와 양태 기반) - 유효한 WestKeywordCode 사용
    element_keyword_codes = {
        "FIRE": ["PASSION", "LEADERSHIP", "COURAGE"],
        "EARTH": ["STABILITY", "PRACTICALITY", "PATIENCE"],
        "AIR": ["COMMUNICATION", "CURIOSITY", "ADAPTABILITY"],
        "WATER": ["EMPATHY", "INTUITION", "SENSITIVITY"],
    }
    modality_keyword_codes = {
        "CARDINAL": ["LEADERSHIP", "COURAGE"],
        "FIXED": ["STABILITY", "DISCIPLINE"],
        "MUTABLE": ["ADAPTABILITY", "CURIOSITY"],
    }

    # WestKeywordCode 레이블 매핑 (간소화)
    keyword_labels = {
        "PASSION": "열정",
        "LEADERSHIP": "리더십",
        "COURAGE": "용기",
        "STABILITY": "안정성",
        "PRACTICALITY": "실용성",
        "PATIENCE": "인내심",
        "COMMUNICATION": "소통",
        "CURIOSITY": "호기심",
        "ADAPTABILITY": "적응력",
        "EMPATHY": "공감",
        "INTUITION": "직관",
        "SENSITIVITY": "감수성",
        "DISCIPLINE": "절제",
    }

    keywords = []
    # 우세 원소 키워드 2개
    elem_kws = element_keyword_codes.get(dominant_element, ["BALANCE"])
    for i, code in enumerate(elem_kws[:2]):
        keywords.append({
            "code": code,
            "label": keyword_labels.get(code, code),
            "weight": round(0.8 - i * 0.1, 1),
        })
    # 우세 양태 키워드 1개
    mod_kws = modality_keyword_codes.get(dominant_modality, ["BALANCE"])
    mod_code = mod_kws[0]
    keywords.append({
        "code": mod_code,
        "label": keyword_labels.get(mod_code, mod_code),
        "weight": 0.6,
    })

    # fortune_key 생성
    fortune_key = f"western:{birth_date}:{birth_time}"

    # 실서비스 API 양식 (WesternFortuneDataV2)
    return {
        "fortune_key": fortune_key,
        "element": dominant_element,
        "stats": {
            "main_sign": {
                "code": sun_sign["code"],
                "name": sun_sign["label"],
            },
            "element_summary": f"{ELEMENT_LABELS[dominant_element]} 원소가 강합니다",
            "element_4_distribution": element_4_distribution,
            "modality_summary": f"{MODALITY_LABELS[dominant_modality]}이 우세합니다",
            "modality_3_distribution": modality_3_distribution,
            "keywords_summary": f"{ELEMENT_LABELS[dominant_element]} 원소 기반의 {MODALITY_LABELS[dominant_modality]} 성향",
            "keywords": keywords,
        },
        "fortune_content": {
            "overview": f"{sun_sign['label']} 태양과 함께 {ELEMENT_LABELS[dominant_element]} 원소가 지배하는 운세입니다.",
            "detailed_analysis": [
                {
                    "title": "성격 분석",
                    "content": f"{ELEMENT_LABELS[dominant_element]} 원소의 영향으로 {keywords[0]['label']} 성향이 강합니다.",
                },
                {
                    "title": "운세 해석",
                    "content": f"{MODALITY_LABELS[dominant_modality]} 양태로 인해 {keywords[-1]['label']} 특성이 두드러집니다.",
                },
            ],
            "advice": f"{sun_sign['label']}의 강점을 활용하세요.",
        },
        "lucky": {
            "color": "빨강" if dominant_element == "FIRE" else "파랑" if dominant_element == "WATER" else "초록" if dominant_element == "EARTH" else "노랑",
            "number": str((month + day) % 10),
            "item": "반지" if dominant_element == "FIRE" else "목걸이",
            "place": "산" if dominant_element == "EARTH" else "바다" if dominant_element == "WATER" else "도시",
        },
        # 레거시 필드 (검증용)
        "_legacy": {
            "sun_sign": sun_sign,
            "moon_sign": moon_sign,
            "rising_sign": rising_sign,
            "dominant_element": dominant_element,
            "dominant_modality": dominant_modality,
        },
    }


def generate_birth_combinations() -> list[dict]:
    """20대 남녀 출생 조합 생성

    Returns:
        출생 데이터 리스트 (남 5명 + 여 5명)
    """
    birth_years = [1995, 1998, 2000, 2002, 2005]
    combinations = []

    # 남성 5명
    for year in birth_years:
        month = random.randint(1, 12)
        day = random.randint(1, 28)  # 모든 월에 안전한 1-28일
        hour = random.randint(0, 23)

        combinations.append({
            "name": f"남성_{year}년생",
            "gender": "male",
            "birth_year": year,
            "birth_month": month,
            "birth_day": day,
            "birth_hour": hour,
            "birth_date": f"{year}-{month:02d}-{day:02d}",
            "birth_time": f"{hour:02d}:00",
        })

    # 여성 5명
    for year in birth_years:
        month = random.randint(1, 12)
        day = random.randint(1, 28)
        hour = random.randint(0, 23)

        combinations.append({
            "name": f"여성_{year}년생",
            "gender": "female",
            "birth_year": year,
            "birth_month": month,
            "birth_day": day,
            "birth_hour": hour,
            "birth_date": f"{year}-{month:02d}-{day:02d}",
            "birth_time": f"{hour:02d}:00",
        })

    return combinations


def calculate_saju_for_combination(combo: dict) -> dict:
    """조합에 대한 사주 계산

    Args:
        combo: 출생 조합 딕셔너리

    Returns:
        사주 계산 결과 포함 딕셔너리
    """
    try:
        calculator = SajuCalculator()

        # 날짜/시간 문자열 포맷
        birth_date_str = combo["birth_date"]
        birth_time_str = combo["birth_time"]
        gender_code = "M" if combo["gender"] == "male" else "F"

        # 사주 계산
        four_pillars, element_balance = calculator.calculate(
            birth_date=birth_date_str,
            birth_time=birth_time_str,
            gender=gender_code,
        )

        # 일간 추출 (일주의 첫 글자)
        day_master = four_pillars.day[0]

        # 점성술 데이터 계산
        western_data = calculate_western_astrology(
            birth_date=combo["birth_date"],
            birth_time=combo["birth_time"],
            month=combo["birth_month"],
            day=combo["birth_day"],
            hour=combo["birth_hour"],
        )

        # 결과 추출
        result = {
            **combo,
            "saju_success": True,
            # 동양 사주
            "eastern": {
                "four_pillars": {
                    "year": four_pillars.year,
                    "month": four_pillars.month,
                    "day": four_pillars.day,
                    "hour": four_pillars.hour,
                },
                "day_master": day_master,
                "element_balance": {
                    "wood": element_balance.wood,
                    "fire": element_balance.fire,
                    "earth": element_balance.earth,
                    "metal": element_balance.metal,
                    "water": element_balance.water,
                },
                "dominant_element": element_balance.get_dominant(),
                "weak_element": element_balance.get_weak(),
            },
            # 서양 점성술
            "western": western_data,
        }

        logger.info(
            "saju_calculated",
            name=combo["name"],
            four_pillars=result["eastern"]["four_pillars"],
            day_master=result["eastern"]["day_master"],
            sun_sign=result["western"]["stats"]["main_sign"]["name"],
            fortune_key=result["western"]["fortune_key"],
        )

        return result

    except Exception as e:
        logger.error(
            "saju_calculation_failed",
            name=combo["name"],
            error=str(e),
            error_type=type(e).__name__,
        )
        return {
            **combo,
            "saju_success": False,
            "error": str(e),
        }


def validate_quality(results: list[dict]) -> dict:
    """품질 검증

    Args:
        results: 사주 계산 결과 리스트

    Returns:
        검증 결과 딕셔너리
    """
    validation = {
        "total_count": len(results),
        "success_count": sum(1 for r in results if r.get("saju_success")),
        "failure_count": sum(1 for r in results if not r.get("saju_success")),
        "eastern": {},
        "western": {},
        "gender_distribution": {},
    }

    # 성공한 결과만 분석
    successful = [r for r in results if r.get("saju_success")]

    if not successful:
        logger.warning("no_successful_calculations")
        return validation

    # ============================================================
    # 동양 사주 통계
    # ============================================================
    eastern_data = [r["eastern"] for r in successful]

    # 오행 분포 (주도 오행)
    dominant_elements = [e["dominant_element"] for e in eastern_data]
    validation["eastern"]["element_distribution"] = dict(Counter(dominant_elements))

    # 일간 분포
    day_masters = [e["day_master"] for e in eastern_data]
    validation["eastern"]["day_master_distribution"] = dict(Counter(day_masters))

    # 오행 균형 통계
    element_stats = {"wood": [], "fire": [], "earth": [], "metal": [], "water": []}
    for e in eastern_data:
        balance = e["element_balance"]
        for elem in element_stats:
            element_stats[elem].append(balance[elem])

    validation["eastern"]["element_balance_stats"] = {
        elem: {
            "min": min(values),
            "max": max(values),
            "avg": round(sum(values) / len(values), 1),
        }
        for elem, values in element_stats.items()
    }

    # ============================================================
    # 서양 점성술 통계
    # ============================================================
    western_data = [r["western"] for r in successful]

    # fortune_key 검증
    fortune_keys = [w.get("fortune_key", "") for w in western_data]
    validation["western"]["fortune_key_sample"] = fortune_keys[:3]  # 샘플 3개

    # 태양 별자리 분포 (새 구조)
    sun_signs = [w["stats"]["main_sign"]["code"] for w in western_data]
    validation["western"]["sun_sign_distribution"] = dict(Counter(sun_signs))

    # 우세 원소 분포 (새 구조)
    dominant_elements_w = [w["element"] for w in western_data]
    validation["western"]["element_distribution"] = dict(Counter(dominant_elements_w))

    # 우세 양태 분포 (레거시 필드 사용)
    dominant_modalities = [w.get("_legacy", {}).get("dominant_modality", "UNKNOWN") for w in western_data]
    validation["western"]["modality_distribution"] = dict(Counter(dominant_modalities))

    # 새 필드 검증
    validation["western"]["has_element_summary"] = all(
        "element_summary" in w["stats"] for w in western_data
    )
    validation["western"]["has_keywords"] = all(
        "keywords" in w["stats"] and len(w["stats"]["keywords"]) >= 3 for w in western_data
    )
    validation["western"]["has_fortune_content"] = all(
        "fortune_content" in w for w in western_data
    )

    # 성별 분포
    genders = [r["gender"] for r in successful]
    validation["gender_distribution"] = dict(Counter(genders))

    logger.info(
        "quality_validation_complete",
        success_rate=f"{validation['success_count']}/{validation['total_count']}",
        eastern_elements=validation["eastern"]["element_distribution"],
        western_elements=validation["western"]["element_distribution"],
    )

    return validation


def main() -> None:
    """메인 실행 함수"""
    logger.info("test_data_generation_start")

    # 1. 출생 조합 생성
    logger.info("generating_birth_combinations")
    combinations = generate_birth_combinations()
    logger.info("birth_combinations_generated", count=len(combinations))

    # 2. 사주 계산
    logger.info("calculating_saju")
    results = []
    for combo in combinations:
        result = calculate_saju_for_combination(combo)
        results.append(result)

    # 3. 품질 검증
    logger.info("validating_quality")
    validation = validate_quality(results)

    # 4. 결과 저장
    output_file = Path(__file__).parent.parent / "data" / "test" / "birth_combinations_20s.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    output_data = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "total_combinations": len(results),
            "description": "20대 남녀 출생 조합 테스트 데이터 (1995-2005년생)",
        },
        "validation": validation,
        "combinations": results,
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    logger.info(
        "test_data_saved",
        output_file=str(output_file),
        total_count=len(results),
        success_count=validation["success_count"],
    )

    # 5. 결과 요약 출력
    print("\n" + "="*60)
    print("20대 남녀 출생 조합 데이터 생성 완료 (동양+서양)")
    print("="*60)
    print(f"\n📊 기본 통계:")
    print(f"  - 전체 조합: {validation['total_count']}개")
    print(f"  - 성공: {validation['success_count']}개")
    print(f"  - 실패: {validation['failure_count']}개")
    print(f"  - 성공률: {validation['success_count']/validation['total_count']*100:.1f}%")

    print(f"\n👥 성별 분포:")
    for gender, count in validation["gender_distribution"].items():
        print(f"  - {gender}: {count}개")

    # 동양 사주 통계
    print("\n" + "-"*40)
    print("🔮 동양 사주 통계")
    print("-"*40)

    eastern = validation.get("eastern", {})
    if eastern.get("element_distribution"):
        print(f"\n🔥 오행 분포 (주도 오행):")
        for elem, count in eastern["element_distribution"].items():
            print(f"  - {elem}: {count}개")

    if eastern.get("day_master_distribution"):
        print(f"\n⚖️ 일간 분포:")
        for day_master, count in eastern["day_master_distribution"].items():
            print(f"  - {day_master}: {count}개")

    if eastern.get("element_balance_stats"):
        print(f"\n📈 오행 균형 통계:")
        for elem, stats in eastern["element_balance_stats"].items():
            print(f"  - {elem}: 최소={stats['min']}%, 최대={stats['max']}%, 평균={stats['avg']}%")

    # 서양 점성술 통계
    print("\n" + "-"*40)
    print("⭐ 서양 점성술 통계 (WesternFortuneDataV2)")
    print("-"*40)

    western = validation.get("western", {})

    # fortune_key 샘플 출력
    if western.get("fortune_key_sample"):
        print(f"\n🔑 Fortune Key 샘플:")
        for key in western["fortune_key_sample"]:
            print(f"  - {key}")

    # 새 필드 검증 결과
    print(f"\n✅ 필드 검증:")
    print(f"  - element_summary 존재: {western.get('has_element_summary', False)}")
    print(f"  - keywords (3개 이상): {western.get('has_keywords', False)}")
    print(f"  - fortune_content 존재: {western.get('has_fortune_content', False)}")

    if western.get("sun_sign_distribution"):
        print(f"\n☀️ 태양 별자리 분포:")
        for sign, count in western["sun_sign_distribution"].items():
            print(f"  - {sign}: {count}개")

    if western.get("element_distribution"):
        print(f"\n🌊 4원소 분포 (대표 원소):")
        for elem, count in western["element_distribution"].items():
            label = ELEMENT_LABELS.get(elem, elem)
            print(f"  - {label}({elem}): {count}개")

    if western.get("modality_distribution"):
        print(f"\n🔄 양태 분포 (우세 양태):")
        for mod, count in western["modality_distribution"].items():
            label = MODALITY_LABELS.get(mod, mod)
            print(f"  - {label}({mod}): {count}개")

    print(f"\n💾 저장 위치: {output_file}")
    print("="*60)

    # 실패 케이스 출력
    if validation["failure_count"] > 0:
        print("\n⚠️ 실패 케이스:")
        for result in results:
            if not result.get("saju_success"):
                print(f"  - {result['name']}: {result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    main()
