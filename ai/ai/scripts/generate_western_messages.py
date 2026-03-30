"""서양 4원소+양태 복합 메시지 생성 스크립트

4원소 2개 조합: C(4,2) = 6쌍 × 6카테고리 × 3변형 = 108개
양태 2개 조합: C(3,2) = 3쌍 × 6카테고리 × 3변형 = 54개
총 162개 메시지
"""

import asyncio
import json
import re
from itertools import combinations
from pathlib import Path

import httpx


# 한국어 필터 (기존 로직 재사용)
def is_clean_korean(text: str) -> bool:
    """순수 한국어인지 확인"""
    if not re.search(r'[가-힣]', text):
        return False
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
    if not (15 <= len(text) <= 70):
        return None
    return text


# vLLM 설정
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

# 4원소 정의
FOUR_ELEMENTS = {
    "fire": {
        "name": "불",
        "traits": ["열정", "행동력", "에너지", "추진력", "활력"],
        "category_hints": {
            "LOVE": "열정적 사랑, 빠른 진전",
            "MONEY": "과감한 투자, 충동 지출",
            "CAREER": "리더십, 추진력",
            "HEALTH": "과로 주의, 에너지 관리",
            "STUDY": "열정적 몰입, 빠른 습득",
            "GENERAL": "열정과 행동력",
        },
    },
    "water": {
        "name": "물",
        "traits": ["감정", "직관", "공감", "깊이", "흐름"],
        "category_hints": {
            "LOVE": "깊은 감정, 감성적 교감",
            "MONEY": "직관적 판단, 감정적 지출",
            "CAREER": "공감 능력, 협력",
            "HEALTH": "감정 관리, 스트레스",
            "STUDY": "직관적 이해, 암기력",
            "GENERAL": "감정과 직관",
        },
    },
    "air": {
        "name": "바람",
        "traits": ["지성", "소통", "아이디어", "논리", "분석"],
        "category_hints": {
            "LOVE": "대화, 지적 교감",
            "MONEY": "정보 기반 투자, 분석",
            "CAREER": "커뮤니케이션, 네트워킹",
            "HEALTH": "호흡기, 정신 건강",
            "STUDY": "논리적 사고, 토론",
            "GENERAL": "지성과 소통",
        },
    },
    "earth": {
        "name": "흙",
        "traits": ["안정", "현실", "실용", "꾸준함", "신뢰"],
        "category_hints": {
            "LOVE": "안정적 관계, 현실적 접근",
            "MONEY": "안전 자산, 실질 수익",
            "CAREER": "안정, 꾸준함",
            "HEALTH": "체력 관리, 규칙적 생활",
            "STUDY": "꾸준한 학습, 실용 지식",
            "GENERAL": "안정과 실용",
        },
    },
}

# 양태 정의
MODALITY = {
    "cardinal": {
        "name": "활동궁",
        "traits": ["시작", "주도", "개척", "리더십", "추진"],
        "signs": ["양자리", "게자리", "천칭자리", "염소자리"],
    },
    "fixed": {
        "name": "고정궁",
        "traits": ["유지", "집중", "끈기", "안정", "고집"],
        "signs": ["황소자리", "사자자리", "전갈자리", "물병자리"],
    },
    "mutable": {
        "name": "변통궁",
        "traits": ["적응", "변화", "유연", "조정", "흐름"],
        "signs": ["쌍둥이자리", "처녀자리", "사수자리", "물고기자리"],
    },
}


def create_element_pair_prompt(
    elem1_key: str,
    elem2_key: str,
    category: str,
) -> tuple[str, str]:
    """4원소 2개 조합 프롬프트"""
    elem1 = FOUR_ELEMENTS[elem1_key]
    elem2 = FOUR_ELEMENTS[elem2_key]
    cat_kr = CATEGORY_KR[category]

    trait1 = elem1["traits"][0]
    trait2 = elem2["traits"][0]
    hint1 = elem1["category_hints"][category]
    hint2 = elem2["category_hints"][category]

    system = f"""운세 메시지 생성기 (서양 4원소 복합).

[절대 규칙]
1. 오직 한국어만 사용 (외국어 절대 금지)
2. 한 문장, 25-55자
3. **반드시 두 원소를 모두 언급** (예: "{elem1['name']}의 {trait1}과 {elem2['name']}의 {trait2}가...")
4. 두 원소의 시너지 효과 강조
5. {cat_kr} 맥락 반영
6. 마침표로 끝
7. 이모지 금지
8. JSON 배열로만 출력

[원소 정보]
- 원소1: {elem1['name']} ({trait1})
  {cat_kr} 관련: {hint1}
- 원소2: {elem2['name']} ({trait2})
  {cat_kr} 관련: {hint2}

[출력 예시]
["{elem1['name']}의 {trait1}과 {elem2['name']}의 {trait2}가 만나 {cat_kr}이 상승합니다.", "{elem1['name']}와 {elem2['name']}의 조화로 긍정적인 흐름이 생깁니다."]"""

    user = f"""{elem1['name']}+{elem2['name']} 복합 {cat_kr} 메시지 3개.
JSON 배열만 출력:"""

    return system, user


def create_modality_pair_prompt(
    mod1_key: str,
    mod2_key: str,
    category: str,
) -> tuple[str, str]:
    """양태 2개 조합 프롬프트"""
    mod1 = MODALITY[mod1_key]
    mod2 = MODALITY[mod2_key]
    cat_kr = CATEGORY_KR[category]

    trait1 = mod1["traits"][0]
    trait2 = mod2["traits"][0]

    system = f"""운세 메시지 생성기 (서양 양태 복합).

[절대 규칙]
1. 오직 한국어만 사용 (외국어 절대 금지)
2. 한 문장, 25-55자
3. **반드시 두 양태를 모두 언급** (예: "{mod1['name']}의 {trait1}과 {mod2['name']}의 {trait2}가...")
4. 두 양태의 조화 효과 강조
5. {cat_kr} 맥락 반영
6. 마침표로 끝
7. 이모지 금지
8. JSON 배열로만 출력

[양태 정보]
- 양태1: {mod1['name']} ({trait1})
- 양태2: {mod2['name']} ({trait2})

[출력 예시]
["{mod1['name']}의 {trait1}과 {mod2['name']}의 {trait2}가 만나 {cat_kr}이 상승합니다.", "{mod1['name']}와 {mod2['name']}의 균형이 좋은 결과를 가져옵니다."]"""

    user = f"""{mod1['name']}+{mod2['name']} 복합 {cat_kr} 메시지 3개.
JSON 배열만 출력:"""

    return system, user


async def generate_messages(
    system: str,
    user: str,
    timeout: float = 60.0,
    max_retries: int = 3,
) -> list[str]:
    """vLLM으로 메시지 생성"""
    for attempt in range(max_retries):
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

            if len(messages) >= 2:
                return messages[:3]

            await asyncio.sleep(0.3)

    # 폴백
    return ["긍정적인 기운이 흐르는 시기입니다.", "좋은 결과를 기대할 수 있습니다."]


async def generate_element_pairs() -> dict[str, list[str]]:
    """4원소 2개 조합 메시지 생성 (108개)"""
    results = {}
    total = 0
    success = 0

    elem_keys = list(FOUR_ELEMENTS.keys())
    pairs = list(combinations(elem_keys, 2))

    print(f"\n4원소 쌍 생성 시작: {len(pairs)}쌍 × 6카테고리 × 3변형 = {len(pairs) * 6 * 3}개")

    for elem1, elem2 in pairs:
        for category in CATEGORIES:
            key = f"{elem1.upper()}_{elem2.upper()}_{category}"
            total += 1

            try:
                system, user = create_element_pair_prompt(elem1, elem2, category)
                messages = await generate_messages(system, user)
                results[key] = messages
                success += 1
                print(f"  [{success}/{total}] {key}: {len(messages)}개")
                await asyncio.sleep(0.5)  # 서버 부하 방지
            except Exception as e:
                print(f"  [실패] {key}: {e}")
                results[key] = ["긍정적인 기운이 흐릅니다."]

    print(f"4원소 쌍 완료: {success}/{total} 성공")
    return results


async def generate_modality_pairs() -> dict[str, list[str]]:
    """양태 2개 조합 메시지 생성 (54개)"""
    results = {}
    total = 0
    success = 0

    mod_keys = list(MODALITY.keys())
    pairs = list(combinations(mod_keys, 2))

    print(f"\n양태 쌍 생성 시작: {len(pairs)}쌍 × 6카테고리 × 3변형 = {len(pairs) * 6 * 3}개")

    for mod1, mod2 in pairs:
        for category in CATEGORIES:
            key = f"{mod1.upper()}_{mod2.upper()}_{category}"
            total += 1

            try:
                system, user = create_modality_pair_prompt(mod1, mod2, category)
                messages = await generate_messages(system, user)
                results[key] = messages
                success += 1
                print(f"  [{success}/{total}] {key}: {len(messages)}개")
                await asyncio.sleep(0.5)
            except Exception as e:
                print(f"  [실패] {key}: {e}")
                results[key] = ["긍정적인 흐름이 이어집니다."]

    print(f"양태 쌍 완료: {success}/{total} 성공")
    return results


async def test_samples():
    """샘플 6개 테스트"""
    print("=" * 60)
    print("서양 복합 메시지 샘플 테스트")
    print("=" * 60)

    test_cases = [
        # 4원소 쌍
        ("fire", "air", "LOVE"),
        ("water", "earth", "MONEY"),
        ("air", "earth", "CAREER"),
        # 양태 쌍
        ("cardinal", "fixed", "GENERAL"),
        ("fixed", "mutable", "HEALTH"),
        ("cardinal", "mutable", "STUDY"),
    ]

    results = {}

    for elem1, elem2, category in test_cases:
        if elem1 in FOUR_ELEMENTS:
            system, user = create_element_pair_prompt(elem1, elem2, category)
            key_type = "4원소"
        else:
            system, user = create_modality_pair_prompt(elem1, elem2, category)
            key_type = "양태"

        key = f"{elem1.upper()}_{elem2.upper()}_{category}"
        print(f"\n[{key_type}] {key}")
        print("-" * 50)

        try:
            messages = await generate_messages(system, user)
            results[key] = messages
            for i, msg in enumerate(messages, 1):
                print(f"  {i}. {msg}")
        except Exception as e:
            print(f"  오류: {e}")
            results[key] = []

    return results


async def main():
    """전체 생성 실행"""
    print("=" * 60)
    print("서양 4원소+양태 복합 메시지 전체 생성")
    print("=" * 60)

    # 데이터 디렉토리 생성
    data_dir = Path(__file__).parent.parent / "data" / "western"
    data_dir.mkdir(parents=True, exist_ok=True)

    # 4원소 쌍 생성
    elements_results = await generate_element_pairs()
    elements_path = data_dir / "elements_pairs.json"
    with open(elements_path, "w", encoding="utf-8") as f:
        json.dump(elements_results, f, ensure_ascii=False, indent=2)
    print(f"\n저장 완료: {elements_path}")

    # 양태 쌍 생성
    modality_results = await generate_modality_pairs()
    modality_path = data_dir / "modality_pairs.json"
    with open(modality_path, "w", encoding="utf-8") as f:
        json.dump(modality_results, f, ensure_ascii=False, indent=2)
    print(f"저장 완료: {modality_path}")

    # 통계
    total_elements = sum(len(msgs) for msgs in elements_results.values())
    total_modality = sum(len(msgs) for msgs in modality_results.values())
    print(f"\n[통계]")
    print(f"4원소 쌍: {len(elements_results)}개 키, {total_elements}개 메시지")
    print(f"양태 쌍: {len(modality_results)}개 키, {total_modality}개 메시지")
    print(f"총합: {total_elements + total_modality}개 메시지")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        asyncio.run(test_samples())
    else:
        asyncio.run(main())
