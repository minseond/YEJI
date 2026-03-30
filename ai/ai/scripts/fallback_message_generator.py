"""폴백 메시지 생성기 - 네트워크 협상식 배치 생성

품질 확인하면서 시추 → 스케일업
"""

import asyncio
import json
import random
import re
from pathlib import Path

import httpx


# 외래 문자 필터 (한글, 숫자, 기본 문장부호만 허용)
KOREAN_PATTERN = re.compile(r'^[가-힣0-9\s.,!?~\-()""\'\']+$')


def is_clean_korean(text: str) -> bool:
    """순수 한국어인지 확인"""
    # 한글이 하나라도 있어야 함
    if not re.search(r'[가-힣]', text):
        return False
    # 외래 문자 감지 (태국어, 아랍어, 히브리어 등)
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
    """메시지 정제 - 외래 문자 제거"""
    if not text or len(text) < 10:
        return None
    # 양쪽 공백 및 따옴표 제거
    text = text.strip().strip('"').strip("'").strip()
    # 순수 한국어 체크
    if not is_clean_korean(text):
        return None
    # 길이 체크 (20-60자)
    if not (15 <= len(text) <= 60):
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

# 동양 사주 조합 (요소 맥락 포함)
EASTERN_ELEMENTS = {
    # 음양 (레벨별)
    "YIN_YANG": {
        "YIN": {
            "name": "음(陰)",
            "meaning": "내향적, 수용적, 신중함",
            "levels": {
                "LOW": {"range": "0-30%", "trait": "양 성향이 강해 적극적이고 외향적"},
                "MID": {"range": "40-60%", "trait": "음양 균형이 잡혀 조화로움"},
                "HIGH": {"range": "70-100%", "trait": "음 성향이 강해 신중하고 내향적"},
            },
        },
        "YANG": {
            "name": "양(陽)",
            "meaning": "외향적, 적극적, 추진력",
            "levels": {
                "LOW": {"range": "0-30%", "trait": "음 성향이 강해 신중하고 보수적"},
                "MID": {"range": "40-60%", "trait": "음양 균형이 잡혀 조화로움"},
                "HIGH": {"range": "70-100%", "trait": "양 성향이 강해 적극적이고 추진력 있음"},
            },
        },
    },
    # 오행 (각 원소별)
    "FIVE_ELEMENTS": {
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
    },
    # 십신
    "TEN_GODS": {
        "BIJEON": {"name": "비견(比肩)", "meaning": "동료, 경쟁, 자존심", "keyword": "경쟁과 협력"},
        "GEUPJAE": {"name": "겁재(劫財)", "meaning": "모험, 손재, 도전", "keyword": "도전과 손실"},
        "SIKSHIN": {"name": "식신(食神)", "meaning": "표현, 창작, 건강", "keyword": "표현과 건강"},
        "SANGGWAN": {"name": "상관(傷官)", "meaning": "반항, 재능, 예술", "keyword": "재능과 예술"},
        "PYEONJAE": {"name": "편재(偏財)", "meaning": "투기, 횡재, 아버지", "keyword": "횡재와 투기"},
        "JEONGJAE": {"name": "정재(正財)", "meaning": "안정 재물, 꾸준함", "keyword": "안정적 재물"},
        "PYEONGWAN": {"name": "편관(偏官)", "meaning": "권력, 도전, 스트레스", "keyword": "권력과 도전"},
        "JEONGGWAN": {"name": "정관(正官)", "meaning": "명예, 직장, 규율", "keyword": "명예와 직장"},
        "PYEONIN": {"name": "편인(偏印)", "meaning": "학문, 비밀, 고독", "keyword": "학문과 통찰"},
        "JEONGIN": {"name": "정인(正印)", "meaning": "어머니, 보호, 학습", "keyword": "보호와 학습"},
    },
}

# 서양 점성 조합 (요소 맥락 포함)
WESTERN_ELEMENTS = {
    # 4원소
    "FOUR_ELEMENTS": {
        "FIRE": {
            "name": "불(Fire)",
            "meaning": "열정, 행동력, 에너지",
            "category_hints": {
                "LOVE": "열정적 사랑, 빠른 진전",
                "MONEY": "과감한 투자, 충동 지출",
                "CAREER": "리더십, 추진력",
                "HEALTH": "과로 주의, 에너지 관리",
                "STUDY": "열정적 몰입, 빠른 습득",
                "GENERAL": "열정과 행동력",
            },
        },
        "WATER": {
            "name": "물(Water)",
            "meaning": "감정, 직관, 공감",
            "category_hints": {
                "LOVE": "깊은 감정, 감성적 교감",
                "MONEY": "직관적 판단, 감정적 지출",
                "CAREER": "공감 능력, 협력",
                "HEALTH": "감정 관리, 스트레스",
                "STUDY": "직관적 이해, 암기력",
                "GENERAL": "감정과 직관",
            },
        },
        "AIR": {
            "name": "바람(Air)",
            "meaning": "지성, 소통, 아이디어",
            "category_hints": {
                "LOVE": "대화, 지적 교감",
                "MONEY": "정보 기반 투자, 분석",
                "CAREER": "커뮤니케이션, 네트워킹",
                "HEALTH": "호흡기, 정신 건강",
                "STUDY": "논리적 사고, 토론",
                "GENERAL": "지성과 소통",
            },
        },
        "EARTH": {
            "name": "흙(Earth)",
            "meaning": "안정, 현실, 실용",
            "category_hints": {
                "LOVE": "안정적 관계, 현실적 접근",
                "MONEY": "안전 자산, 실질 수익",
                "CAREER": "안정, 꾸준함",
                "HEALTH": "체력 관리, 규칙적 생활",
                "STUDY": "꾸준한 학습, 실용 지식",
                "GENERAL": "안정과 실용",
            },
        },
    },
    # 양태 (Modality)
    "MODALITY": {
        "CARDINAL": {
            "name": "활동궁(Cardinal)",
            "meaning": "시작, 주도, 개척",
            "signs": ["양자리", "게자리", "천칭자리", "염소자리"],
        },
        "FIXED": {
            "name": "고정궁(Fixed)",
            "meaning": "유지, 집중, 끈기",
            "signs": ["황소자리", "사자자리", "전갈자리", "물병자리"],
        },
        "MUTABLE": {
            "name": "변통궁(Mutable)",
            "meaning": "적응, 변화, 유연",
            "signs": ["쌍둥이자리", "처녀자리", "사수자리", "물고기자리"],
        },
    },
}


def create_prompt(category: str, element_key: str, element_data: dict, level: str | None = None) -> tuple[str, str]:
    """요소 맥락 포함 메시지 생성용 프롬프트

    Args:
        category: LOVE, MONEY, CAREER 등
        element_key: WOOD, FIRE, YANG 등
        element_data: 요소 정보 dict (name, meaning, category_hints 등)
        level: LOW, MID, HIGH (음양용)
    """
    cat_kr = CATEGORY_KR.get(category, "총운")
    element_name = element_data.get("name", element_key)
    element_meaning = element_data.get("meaning", "")

    # 카테고리별 힌트
    category_hint = ""
    if "category_hints" in element_data:
        category_hint = element_data["category_hints"].get(category, "")

    # 레벨 정보 (음양)
    level_info = ""
    if level and "levels" in element_data:
        lv = element_data["levels"].get(level, {})
        level_info = f"({lv.get('range', '')}, {lv.get('trait', '')})"

    system = f"""운세 메시지 생성기.

[절대 규칙]
1. 오직 한국어만 사용 (외국어 절대 금지)
2. 한 문장, 25-50자
3. **반드시 요소 이름을 언급** (예: "{element_name}의 기운이...")
4. 요소 특성과 카테고리({cat_kr})를 연결
5. 마침표로 끝
6. 이모지 금지
7. JSON 배열로만 출력

[요소 정보]
- 요소: {element_name}
- 의미: {element_meaning}
- {cat_kr} 관련: {category_hint}

[출력 예시]
["{element_name}의 기운이 강해 {cat_kr}에 긍정적입니다.", "{element_name} 특유의 {element_meaning}이 빛을 발합니다."]"""

    user = f"""{element_name} 기운에 대한 {cat_kr} 메시지 3개.
{level_info}
JSON 배열만 출력:"""

    return system, user


async def generate_messages(
    category: str,
    element_key: str,
    element_data: dict,
    level: str | None = None,
    timeout: float = 60.0,
    max_retries: int = 3,
) -> list[str]:
    """vLLM으로 메시지 생성 (필터 + 재시도)"""
    system, user = create_prompt(category, element_key, element_data, level)

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
                    "max_tokens": 150,
                    "temperature": 0.5 + (attempt * 0.1),  # 재시도시 온도 살짝 증가
                },
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]

            # JSON 파싱 시도
            messages = []
            try:
                match = re.search(r'\[.*?\]', content, re.DOTALL)
                if match:
                    raw_messages = json.loads(match.group())
                    messages = [clean_message(m) for m in raw_messages if isinstance(m, str)]
                    messages = [m for m in messages if m]  # None 제거
            except json.JSONDecodeError:
                pass

            # JSON 실패시 줄 단위 파싱
            if not messages:
                for line in content.split('\n'):
                    cleaned = clean_message(line)
                    if cleaned:
                        messages.append(cleaned)

            # 최소 2개 이상 유효한 메시지가 있으면 성공
            if len(messages) >= 2:
                return messages[:3]

            # 재시도 전 짧은 대기
            await asyncio.sleep(0.3)

    # 모든 재시도 실패시 기본 메시지 반환
    cat_kr = CATEGORY_KR.get(category, "총운")
    return [f"{cat_kr}이 순조롭게 흘러가는 시기입니다.", f"긍정적인 기운이 {cat_kr}에 작용합니다."]


async def test_sample_generation():
    """샘플 생성 테스트 (요소 맥락 포함)"""
    print("=" * 60)
    print("폴백 메시지 생성 테스트 (요소 맥락 포함)")
    print("=" * 60)

    # 테스트 케이스: (카테고리, 요소키, 요소데이터, 레벨)
    test_cases = [
        # 동양 - 음양 (레벨별)
        ("LOVE", "YANG", EASTERN_ELEMENTS["YIN_YANG"]["YANG"], "HIGH"),
        ("MONEY", "YIN", EASTERN_ELEMENTS["YIN_YANG"]["YIN"], "LOW"),
        # 동양 - 오행
        ("CAREER", "WOOD", EASTERN_ELEMENTS["FIVE_ELEMENTS"]["WOOD"], None),
        ("HEALTH", "FIRE", EASTERN_ELEMENTS["FIVE_ELEMENTS"]["FIRE"], None),
        ("GENERAL", "METAL", EASTERN_ELEMENTS["FIVE_ELEMENTS"]["METAL"], None),
        # 동양 - 십신
        ("MONEY", "PYEONJAE", EASTERN_ELEMENTS["TEN_GODS"]["PYEONJAE"], None),
        ("CAREER", "JEONGGWAN", EASTERN_ELEMENTS["TEN_GODS"]["JEONGGWAN"], None),
        # 서양 - 4원소
        ("LOVE", "FIRE", WESTERN_ELEMENTS["FOUR_ELEMENTS"]["FIRE"], None),
        ("STUDY", "AIR", WESTERN_ELEMENTS["FOUR_ELEMENTS"]["AIR"], None),
        # 서양 - 양태
        ("GENERAL", "FIXED", WESTERN_ELEMENTS["MODALITY"]["FIXED"], None),
    ]

    results = {}

    for category, element_key, element_data, level in test_cases:
        key = f"{category}_{element_key}" + (f"_{level}" if level else "")
        element_name = element_data.get("name", element_key)
        print(f"\n[{key}] {element_name}")
        print("-" * 50)

        try:
            messages = await generate_messages(category, element_key, element_data, level)
            results[key] = messages
            for i, msg in enumerate(messages, 1):
                # 요소 이름 포함 여부 표시
                has_element = element_name.split("(")[0] in msg or element_key.lower() in msg.lower()
                mark = "✓" if has_element else "✗"
                print(f"  {i}. [{mark}] {msg}")
        except Exception as e:
            print(f"  오류: {e}")
            results[key] = []

    # 결과 저장
    output_path = Path(__file__).parent / "sample_messages.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n결과 저장: {output_path}")
    return results


async def batch_generate(
    combinations: list[tuple],
    batch_size: int = 3,
    delay: float = 0.5,
) -> dict:
    """배치 생성 (네트워크 협상식)

    - 작은 배치로 시작
    - 성공률 확인
    - 점진적 스케일업
    """
    results = {}
    total = len(combinations)
    success = 0
    failed = 0

    print(f"\n배치 생성 시작: 총 {total}개, 배치 크기 {batch_size}")

    for i in range(0, total, batch_size):
        batch = combinations[i:i+batch_size]
        tasks = []

        for category, element_type, element_info in batch:
            tasks.append(generate_messages(category, element_type, element_info))

        # 배치 실행
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)

        for j, result in enumerate(batch_results):
            key = f"{batch[j][0]}_{batch[j][1]}_{batch[j][2].get('key', j)}"
            if isinstance(result, Exception):
                failed += 1
                print(f"  [실패] {key}: {result}")
            else:
                success += 1
                results[key] = result

        # 진행률
        progress = (i + len(batch)) / total * 100
        print(f"  진행: {progress:.1f}% ({success} 성공, {failed} 실패)")

        # 딜레이 (서버 부하 방지)
        await asyncio.sleep(delay)

    return results


if __name__ == "__main__":
    asyncio.run(test_sample_generation())
