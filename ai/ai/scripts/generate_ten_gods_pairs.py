"""십신 2개 조합 복합 메시지 생성 스크립트

십신 10개 중 2개씩 조합 (C(10,2) = 45쌍)
각 조합 × 6개 카테고리 × 3개 변형 = 810개 메시지 생성
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
    # 십신 복합 메시지는 40-80자
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

# 십신 한글명 매핑
TEN_GODS_NAMES = {
    "BIJEON": "비견",
    "GEOBJE": "겁재",
    "SIKSHIN": "식신",
    "SANGGWAN": "상관",
    "PYEONJAE": "편재",
    "JEONGJAE": "정재",
    "PYEONGWAN": "편관",
    "JEONGGWAN": "정관",
    "PYEONIN": "편인",
    "JEONGIN": "정인",
}

# 십신 의미 및 카테고리별 힌트
TEN_GODS_DATA = {
    "BIJEON": {
        "name": "비견",
        "meaning": "독립성, 경쟁, 자립",
        "category_hints": {
            "LOVE": "독립적 관계, 경쟁 심리",
            "MONEY": "자립 투자, 경쟁 수익",
            "CAREER": "독립 사업, 경쟁 우위",
            "HEALTH": "활력, 자기 관리",
            "STUDY": "자기 주도 학습",
            "GENERAL": "독립과 자립",
        },
    },
    "GEOBJE": {
        "name": "겁재",
        "meaning": "협력, 팀워크, 공동 노력",
        "category_hints": {
            "LOVE": "협력 관계, 공동 목표",
            "MONEY": "공동 투자, 협력 수익",
            "CAREER": "팀워크, 협업",
            "HEALTH": "상호 지원, 공동 관리",
            "STUDY": "그룹 스터디, 협력 학습",
            "GENERAL": "협력과 연대",
        },
    },
    "SIKSHIN": {
        "name": "식신",
        "meaning": "표현력, 창의성, 여유",
        "category_hints": {
            "LOVE": "자유로운 표현, 여유 관계",
            "MONEY": "창의적 수익, 부수입",
            "CAREER": "창의적 업무, 표현",
            "HEALTH": "여유, 스트레스 해소",
            "STUDY": "창의적 학습, 표현력",
            "GENERAL": "창의와 여유",
        },
    },
    "SANGGWAN": {
        "name": "상관",
        "meaning": "반골, 개성, 돌파력",
        "category_hints": {
            "LOVE": "개성적 표현, 돌파",
            "MONEY": "파격적 수익, 모험",
            "CAREER": "개성 발휘, 혁신",
            "HEALTH": "활력, 돌발 주의",
            "STUDY": "독창적 사고, 비판",
            "GENERAL": "개성과 혁신",
        },
    },
    "PYEONJAE": {
        "name": "편재",
        "meaning": "유동 재물, 기회 포착",
        "category_hints": {
            "LOVE": "다양한 만남, 기회",
            "MONEY": "유동 자산, 단기 수익",
            "CAREER": "기회 포착, 네트워킹",
            "HEALTH": "활동적, 변화 적응",
            "STUDY": "다양한 관심, 기회 학습",
            "GENERAL": "기회와 변화",
        },
    },
    "JEONGJAE": {
        "name": "정재",
        "meaning": "안정 재물, 꾸준한 축적",
        "category_hints": {
            "LOVE": "안정적 관계, 신뢰",
            "MONEY": "정기 수익, 저축",
            "CAREER": "안정 직장, 꾸준함",
            "HEALTH": "규칙적 관리, 안정",
            "STUDY": "꾸준한 학습, 기본",
            "GENERAL": "안정과 축적",
        },
    },
    "PYEONGWAN": {
        "name": "편관",
        "meaning": "도전, 압박, 극복",
        "category_hints": {
            "LOVE": "도전적 관계, 긴장",
            "MONEY": "압박 극복, 위기 관리",
            "CAREER": "도전 과제, 압박 극복",
            "HEALTH": "스트레스 관리, 극복",
            "STUDY": "어려운 과제, 극복",
            "GENERAL": "도전과 극복",
        },
    },
    "JEONGGWAN": {
        "name": "정관",
        "meaning": "책임감, 명예, 질서",
        "category_hints": {
            "LOVE": "책임감, 진지한 관계",
            "MONEY": "질서 있는 관리, 명예",
            "CAREER": "책임 업무, 승진",
            "HEALTH": "질서 있는 관리",
            "STUDY": "책임감, 성실함",
            "GENERAL": "책임과 명예",
        },
    },
    "PYEONIN": {
        "name": "편인",
        "meaning": "독창적 학습, 특별한 지혜",
        "category_hints": {
            "LOVE": "독특한 이해, 특별한 교감",
            "MONEY": "독창적 수익, 전문성",
            "CAREER": "전문 분야, 독특한 접근",
            "HEALTH": "특별한 관리, 대체 요법",
            "STUDY": "독창적 학습, 전문 지식",
            "GENERAL": "독창성과 전문성",
        },
    },
    "JEONGIN": {
        "name": "정인",
        "meaning": "학습, 지혜, 보호",
        "category_hints": {
            "LOVE": "보호받는 관계, 지혜",
            "MONEY": "안정적 지원, 보호",
            "CAREER": "학습 기회, 지원",
            "HEALTH": "보호, 치유",
            "STUDY": "정통 학습, 지혜 축적",
            "GENERAL": "학습과 보호",
        },
    },
}


def create_ten_gods_prompt(category: str, god1_key: str, god2_key: str) -> tuple[str, str]:
    """십신 2개 조합 복합 메시지 생성 프롬프트

    Args:
        category: LOVE, MONEY, CAREER 등
        god1_key: BIJEON, SIKSHIN 등 (첫 번째 십신)
        god2_key: JEONGJAE, PYEONGWAN 등 (두 번째 십신)

    Returns:
        (system_prompt, user_prompt)
    """
    cat_kr = CATEGORY_KR.get(category, "총운")

    god1_data = TEN_GODS_DATA[god1_key]
    god2_data = TEN_GODS_DATA[god2_key]

    god1_name = god1_data["name"]
    god2_name = god2_data["name"]

    god1_meaning = god1_data["meaning"]
    god2_meaning = god2_data["meaning"]

    god1_hint = god1_data["category_hints"].get(category, "")
    god2_hint = god2_data["category_hints"].get(category, "")

    system = f"""당신은 사주 운세 전문가입니다.
두 십신 기운을 조합해서 {cat_kr} 메시지를 작성하세요.

[조건]
- "{god1_name}"와 "{god2_name}" 두 글자가 반드시 문장에 포함
- 40-60자 한 문장
- 마침표로 끝
- 외국어 절대 금지, 한국어만 사용
- JSON 배열로만 출력

[십신 정보]
- {god1_name}: {god1_meaning}
  {cat_kr} 관련: {god1_hint}

- {god2_name}: {god2_meaning}
  {cat_kr} 관련: {god2_hint}

[예시]
["{god1_name}의 기운과 {god2_name}의 힘이 만나 {cat_kr}이 상승합니다.", "..."]"""

    user = (
        f"{god1_name}와 {god2_name} 기운의 {cat_kr} 메시지 3개. "
        f"두 십신을 모두 언급하며 조화를 표현하세요. "
        f"JSON 배열만 출력:"
    )

    return system, user


async def generate_ten_gods_messages(
    category: str,
    god1_key: str,
    god2_key: str,
    timeout: float = 60.0,
    max_retries: int = 3,
) -> list[str]:
    """vLLM으로 십신 복합 메시지 생성 (필터 + 재시도)"""
    system, user = create_ten_gods_prompt(category, god1_key, god2_key)

    god1_name = TEN_GODS_DATA[god1_key]["name"]
    god2_name = TEN_GODS_DATA[god2_key]["name"]

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

                # 두 십신 이름 모두 포함 여부 검증
                valid_messages = []
                for msg in messages:
                    if god1_name in msg and god2_name in msg:
                        valid_messages.append(msg)

                # 최소 2개 이상 유효 메시지
                if len(valid_messages) >= 2:
                    return valid_messages[:3]

                await asyncio.sleep(0.3)

        except Exception as e:
            print(f"    재시도 {attempt+1}/{max_retries}: {e}")
            await asyncio.sleep(1.0)

    # 모든 재시도 실패시 기본 메시지
    cat_kr = CATEGORY_KR.get(category, "총운")
    return [
        f"{god1_name}과 {god2_name}이 조화를 이루어 {cat_kr}에 긍정적입니다.",
        f"{god1_name}과 {god2_name}의 복합 기운이 {cat_kr}을 돕습니다.",
    ]


async def test_sample_generation():
    """샘플 10개 생성 테스트"""
    print("=" * 60)
    print("십신 2개 조합 복합 메시지 생성 테스트 (샘플 10개)")
    print("=" * 60)

    # 십신 조합 생성
    gods = list(TEN_GODS_DATA.keys())
    god_pairs = list(combinations(gods, 2))

    print(f"\n총 십신 조합: {len(god_pairs)}개 (C(10,2) = 45)")
    print(f"테스트할 조합: {god_pairs[:2]}")  # 첫 2개 조합만

    test_cases = []
    for god1, god2 in god_pairs[:2]:  # 첫 2개 조합
        for category in ["GENERAL", "LOVE", "MONEY", "CAREER", "HEALTH"]:  # 5개 카테고리
            test_cases.append((category, god1, god2))

    test_cases = test_cases[:10]  # 정확히 10개만

    results = {}

    for i, (category, god1, god2) in enumerate(test_cases, 1):
        # 키 형식: GOD1_GOD2_CATEGORY (알파벳순)
        sorted_gods = sorted([god1, god2])
        key = f"{sorted_gods[0]}_{sorted_gods[1]}_{category}"

        god1_name = TEN_GODS_DATA[god1]["name"]
        god2_name = TEN_GODS_DATA[god2]["name"]
        cat_kr = CATEGORY_KR[category]

        print(f"\n[{i}/10] {key}")
        print(f"  십신: {god1_name} + {god2_name}")
        print(f"  카테고리: {cat_kr}")
        print("-" * 50)

        try:
            messages = await generate_ten_gods_messages(category, god1, god2)
            results[key] = messages
            for j, msg in enumerate(messages, 1):
                # 두 십신 모두 언급 여부 체크
                has_god1 = god1_name in msg
                has_god2 = god2_name in msg
                mark = "✓✓" if (has_god1 and has_god2) else "✓" if (has_god1 or has_god2) else "✗"
                print(f"  {j}. [{mark}] {msg}")
        except Exception as e:
            print(f"  오류: {e}")
            results[key] = []

        await asyncio.sleep(0.5)  # 서버 부하 방지

    # 결과 저장
    output_path = Path(__file__).parent / "sample_ten_gods_pairs.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"테스트 완료! 결과 저장: {output_path}")
    print(f"{'='*60}")
    return results


async def generate_all_combinations():
    """전체 270개 조합 생성 (45개 조합 × 6개 카테고리 × 3개 변형)"""
    print("=" * 60)
    print("십신 2개 조합 전체 메시지 생성 시작")
    print("=" * 60)

    # 십신 조합 생성
    gods = list(TEN_GODS_DATA.keys())
    god_pairs = list(combinations(gods, 2))

    print(f"\n총 십신 조합: {len(god_pairs)}개")
    print(f"카테고리: {len(CATEGORIES)}개")
    print(f"예상 총 메시지: {len(god_pairs)} × {len(CATEGORIES)} × 3 = {len(god_pairs) * len(CATEGORIES) * 3}개")

    all_results = {}
    total_tasks = len(god_pairs) * len(CATEGORIES)
    completed = 0

    for god1, god2 in god_pairs:
        sorted_gods = sorted([god1, god2])
        god1_sorted, god2_sorted = sorted_gods

        for category in CATEGORIES:
            key = f"{god1_sorted}_{god2_sorted}_{category}"

            god1_name = TEN_GODS_DATA[god1]["name"]
            god2_name = TEN_GODS_DATA[god2]["name"]
            cat_kr = CATEGORY_KR[category]

            completed += 1
            progress = (completed / total_tasks) * 100

            print(f"\n[{completed}/{total_tasks}] ({progress:.1f}%) {key}")
            print(f"  {god1_name} + {god2_name} | {cat_kr}")

            try:
                messages = await generate_ten_gods_messages(category, god1, god2)
                all_results[key] = messages

                # 검증: 두 십신 모두 포함 확인
                valid_count = sum(1 for m in messages if god1_name in m and god2_name in m)
                print(f"  ✓ {len(messages)}개 생성 (검증 통과: {valid_count}개)")
            except Exception as e:
                print(f"  ✗ 오류: {e}")
                all_results[key] = []

            # 서버 부하 방지
            await asyncio.sleep(0.3)

    # 최종 저장
    output_path = Path(__file__).parent.parent / "data" / "eastern" / "ten_gods_pairs.json"
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
        print("전체 생성: python generate_ten_gods_pairs.py --full")
        asyncio.run(test_sample_generation())
