"""오행 2개 조합 복합 메시지 생성 스크립트

오행 5개 중 2개씩 조합 (C(5,2) = 10쌍)
각 조합 × 6개 카테고리 × 3개 변형 = 180개 메시지 생성
"""

import asyncio
import json
import re
from itertools import combinations
from pathlib import Path

import httpx


# 외래 문자 필터 (한글, 숫자, 기본 문장부호만 허용)
def is_clean_korean(text: str) -> bool:
    """순수 한국어인지 확인"""
    if not re.search(r'[가-힣]', text):
        return False
    # 외래 문자 감지
    foreign_ranges = [
        (0x0E00, 0x0E7F),   # Thai
        (0x0600, 0x06FF),   # Arabic
        (0x0590, 0x05FF),   # Hebrew
        (0x0900, 0x097F),   # Devanagari
        (0x3040, 0x309F),   # Hiragana
        (0x30A0, 0x30FF),   # Katakana
    ]
    for char in text:
        code = ord(char)
        for start, end in foreign_ranges:
            if start <= code <= end:
                return False
    return True


def clean_message(text: str) -> str | None:
    """메시지 정제"""
    if not text or len(text) < 10:
        return None
    text = text.strip().strip('"').strip("'").strip()
    if not is_clean_korean(text):
        return None
    # 복합 메시지는 조금 더 길 수 있음 (40-80자)
    if not (30 <= len(text) <= 80):
        return None
    return text


# vLLM 서버 설정
VLLM_URL = "http://13.125.68.166:8001/v1/chat/completions"
MODEL = "tellang/yeji-8b-rslora-v7"

# 카테고리
CATEGORIES = ["GENERAL", "LOVE", "MONEY", "CAREER", "HEALTH", "STUDY"]
CATEGORY_KR = {
    "GENERAL": "총운",
    "LOVE": "연애운",
    "MONEY": "금전운",
    "CAREER": "직장운",
    "HEALTH": "건강운",
    "STUDY": "학업운",
}

# 오행 요소 정보 (fallback_message_generator.py에서 참조)
FIVE_ELEMENTS = {
    "WOOD": {
        "name": "목(木)",
        "meaning": "성장, 창의력, 시작",
        "category_hints": {
            "LOVE": "새로운 만남, 관계 시작",
            "MONEY": "투자 성장, 장기 계획",
            "CAREER": "승진, 새 프로젝트",
            "HEALTH": "간, 눈 건강",
            "STUDY": "창의적 학습, 새 분야",
            "GENERAL": "성장과 발전",
        },
    },
    "FIRE": {
        "name": "화(火)",
        "meaning": "열정, 표현력, 활력",
        "category_hints": {
            "LOVE": "열정적 사랑, 표현",
            "MONEY": "과감한 투자, 지출 주의",
            "CAREER": "리더십, 주목받음",
            "HEALTH": "심장, 혈압 관리",
            "STUDY": "집중력, 열정적 몰입",
            "GENERAL": "활력과 열정",
        },
    },
    "EARTH": {
        "name": "토(土)",
        "meaning": "안정, 신뢰, 중재",
        "category_hints": {
            "LOVE": "안정적 관계, 신뢰 구축",
            "MONEY": "안전 자산, 저축",
            "CAREER": "안정, 팀워크",
            "HEALTH": "소화기, 비장",
            "STUDY": "기초 다지기, 꾸준함",
            "GENERAL": "안정과 균형",
        },
    },
    "METAL": {
        "name": "금(金)",
        "meaning": "결단력, 정리, 수확",
        "category_hints": {
            "LOVE": "명확한 관계 정리",
            "MONEY": "수익 실현, 정리",
            "CAREER": "성과 정리, 인정",
            "HEALTH": "폐, 피부 관리",
            "STUDY": "정리, 요약, 마무리",
            "GENERAL": "결실과 수확",
        },
    },
    "WATER": {
        "name": "수(水)",
        "meaning": "지혜, 유연성, 적응",
        "category_hints": {
            "LOVE": "깊은 교감, 감정 흐름",
            "MONEY": "유동 자산, 흐름 관리",
            "CAREER": "적응, 네트워킹",
            "HEALTH": "신장, 비뇨기",
            "STUDY": "암기, 이해력",
            "GENERAL": "지혜와 적응",
        },
    },
}


def create_compound_prompt(category: str, elem1_key: str, elem2_key: str) -> tuple[str, str]:
    """오행 2개 조합 복합 메시지 생성 프롬프트

    Args:
        category: LOVE, MONEY, CAREER 등
        elem1_key: WOOD, FIRE 등 (첫 번째 요소)
        elem2_key: WATER, METAL 등 (두 번째 요소)

    Returns:
        (system_prompt, user_prompt)
    """
    cat_kr = CATEGORY_KR.get(category, "총운")

    elem1_data = FIVE_ELEMENTS[elem1_key]
    elem2_data = FIVE_ELEMENTS[elem2_key]

    elem1_name = elem1_data["name"]
    elem2_name = elem2_data["name"]

    elem1_meaning = elem1_data["meaning"]
    elem2_meaning = elem2_data["meaning"]

    elem1_hint = elem1_data["category_hints"].get(category, "")
    elem2_hint = elem2_data["category_hints"].get(category, "")

    system = f"""운세 메시지 생성기. 두 오행 요소를 결합한 복합 해석을 제공합니다.

[절대 규칙]
1. 오직 한국어만 사용 (외국어 절대 금지)
2. 한 문장, 40-70자
3. **두 요소를 모두 언급** 필수
4. 구조: "[요소1] 기운 때문에 [효과1], [요소2]도 있어서 [효과2]!"
5. 마침표 또는 느낌표로 끝
6. 이모지 금지
7. JSON 배열로만 출력

[요소 정보]
- 요소1: {elem1_name} - {elem1_meaning}
  {cat_kr} 관련: {elem1_hint}

- 요소2: {elem2_name} - {elem2_meaning}
  {cat_kr} 관련: {elem2_hint}

[출력 예시]
["{elem1_name} 기운이 강해 {elem1_hint.split(',')[0]}하고, {elem2_name}도 있어서 {elem2_hint.split(',')[0]}합니다!", "..."]"""

    user = f"""{elem1_name}과 {elem2_name} 복합 기운에 대한 {cat_kr} 메시지 3개.
두 요소를 모두 언급하며, 상호작용을 표현하세요.
JSON 배열만 출력:"""

    return system, user


async def generate_compound_messages(
    category: str,
    elem1_key: str,
    elem2_key: str,
    timeout: float = 60.0,
    max_retries: int = 3,
) -> list[str]:
    """vLLM으로 복합 메시지 생성 (필터 + 재시도)"""
    system, user = create_compound_prompt(category, elem1_key, elem2_key)

    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    VLLM_URL,
                    json={
                        "model": MODEL,
                        "messages": [
                            {"role": "system", "content": system},
                            {"role": "user", "content": user},
                        ],
                        "max_tokens": 200,
                        "temperature": 0.6 + (attempt * 0.1),
                    },
                )
                response.raise_for_status()
                data = response.json()
                content = data["choices"][0]["message"]["content"]

                # JSON 파싱
                messages = []
                try:
                    match = re.search(r'\[.*?\]', content, re.DOTALL)
                    if match:
                        raw_messages = json.loads(match.group())
                        messages = [clean_message(m) for m in raw_messages if isinstance(m, str)]
                        messages = [m for m in messages if m]
                except json.JSONDecodeError:
                    pass

                # JSON 실패시 줄 단위 파싱
                if not messages:
                    for line in content.split('\n'):
                        cleaned = clean_message(line)
                        if cleaned:
                            messages.append(cleaned)

                # 최소 2개 이상 유효 메시지
                if len(messages) >= 2:
                    return messages[:3]

                await asyncio.sleep(0.3)

        except Exception as e:
            print(f"    재시도 {attempt+1}/{max_retries}: {e}")
            await asyncio.sleep(1.0)

    # 모든 재시도 실패시 기본 메시지
    cat_kr = CATEGORY_KR.get(category, "총운")
    elem1_name = FIVE_ELEMENTS[elem1_key]["name"]
    elem2_name = FIVE_ELEMENTS[elem2_key]["name"]
    return [
        f"{elem1_name}과 {elem2_name}이 조화를 이루어 {cat_kr}에 긍정적입니다.",
        f"{elem1_name}과 {elem2_name}의 복합 기운이 {cat_kr}을 돕습니다.",
    ]


async def test_sample_generation():
    """샘플 10개 생성 테스트"""
    print("=" * 60)
    print("오행 2개 조합 복합 메시지 생성 테스트 (샘플 10개)")
    print("=" * 60)

    # 오행 조합 생성
    elements = list(FIVE_ELEMENTS.keys())
    element_pairs = list(combinations(elements, 2))

    print(f"\n총 오행 조합: {len(element_pairs)}개")
    print(f"테스트할 조합: {element_pairs[:2]}")  # 첫 2개 조합만

    test_cases = []
    for elem1, elem2 in element_pairs[:2]:  # 첫 2개 조합
        for category in ["GENERAL", "LOVE", "MONEY", "CAREER", "HEALTH"]:  # 5개 카테고리
            test_cases.append((category, elem1, elem2))

    test_cases = test_cases[:10]  # 정확히 10개만

    results = {}

    for i, (category, elem1, elem2) in enumerate(test_cases, 1):
        # 키 형식: ELEM1_ELEM2_CATEGORY (알파벳순)
        sorted_elems = sorted([elem1, elem2])
        key = f"{sorted_elems[0]}_{sorted_elems[1]}_{category}"

        elem1_name = FIVE_ELEMENTS[elem1]["name"]
        elem2_name = FIVE_ELEMENTS[elem2]["name"]
        cat_kr = CATEGORY_KR[category]

        print(f"\n[{i}/10] {key}")
        print(f"  요소: {elem1_name} + {elem2_name}")
        print(f"  카테고리: {cat_kr}")
        print("-" * 50)

        try:
            messages = await generate_compound_messages(category, elem1, elem2)
            results[key] = messages
            for j, msg in enumerate(messages, 1):
                # 두 요소 모두 언급 여부 체크
                has_elem1 = elem1_name.split("(")[0] in msg
                has_elem2 = elem2_name.split("(")[0] in msg
                mark = "✓✓" if (has_elem1 and has_elem2) else "✓" if (has_elem1 or has_elem2) else "✗"
                print(f"  {j}. [{mark}] {msg}")
        except Exception as e:
            print(f"  오류: {e}")
            results[key] = []

        await asyncio.sleep(0.5)  # 서버 부하 방지

    # 결과 저장
    output_path = Path(__file__).parent / "sample_compound_messages.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"테스트 완료! 결과 저장: {output_path}")
    print(f"{'='*60}")
    return results


async def generate_all_combinations():
    """전체 180개 조합 생성 (10개 조합 × 6개 카테고리 × 3개 변형)"""
    print("=" * 60)
    print("오행 2개 조합 전체 메시지 생성 시작")
    print("=" * 60)

    # 오행 조합 생성
    elements = list(FIVE_ELEMENTS.keys())
    element_pairs = list(combinations(elements, 2))

    print(f"\n총 오행 조합: {len(element_pairs)}개")
    print(f"카테고리: {len(CATEGORIES)}개")
    print(f"예상 총 메시지: {len(element_pairs)} × {len(CATEGORIES)} × 3 = {len(element_pairs) * len(CATEGORIES) * 3}개")

    all_results = {}
    total_tasks = len(element_pairs) * len(CATEGORIES)
    completed = 0

    for elem1, elem2 in element_pairs:
        sorted_elems = sorted([elem1, elem2])
        elem1_sorted, elem2_sorted = sorted_elems

        for category in CATEGORIES:
            key = f"{elem1_sorted}_{elem2_sorted}_{category}"

            elem1_name = FIVE_ELEMENTS[elem1]["name"]
            elem2_name = FIVE_ELEMENTS[elem2]["name"]
            cat_kr = CATEGORY_KR[category]

            completed += 1
            progress = (completed / total_tasks) * 100

            print(f"\n[{completed}/{total_tasks}] ({progress:.1f}%) {key}")
            print(f"  {elem1_name} + {elem2_name} | {cat_kr}")

            try:
                messages = await generate_compound_messages(category, elem1, elem2)
                all_results[key] = messages
                print(f"  ✓ {len(messages)}개 생성")
            except Exception as e:
                print(f"  ✗ 오류: {e}")
                all_results[key] = []

            # 서버 부하 방지
            await asyncio.sleep(0.3)

    # 최종 저장
    output_path = Path(__file__).parent.parent / "data" / "eastern" / "five_elements_pairs.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"전체 생성 완료!")
    print(f"결과 저장: {output_path}")
    print(f"총 조합: {len(all_results)}개")
    print(f"{'='*60}")

    return all_results


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--full":
        asyncio.run(generate_all_combinations())
    else:
        print("샘플 테스트 모드 (10개)")
        print("전체 생성: python generate_compound_messages.py --full")
        asyncio.run(test_sample_generation())
