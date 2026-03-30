"""양태(Modality) 2개 조합 복합 메시지 생성 스크립트

양태 3개 중 2개씩 조합 (C(3,2) = 3쌍)
각 조합 × 6개 카테고리 × 3개 변형 = 54개 메시지 생성
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

# 양태 정보
MODALITIES = {
    "CARDINAL": {
        "name": "활동궁",
        "meaning": "시작, 추진력, 개척",
        "category_hints": {
            "LOVE": "새로운 만남 시작, 적극적 표현",
            "MONEY": "새로운 수익원 개척, 투자 시작",
            "CAREER": "새 프로젝트 착수, 리더십 발휘",
            "HEALTH": "신진대사 활성화, 운동 시작",
            "STUDY": "새로운 학습 시작, 목표 설정",
            "GENERAL": "새로운 계획 실행, 행동 개시",
        },
    },
    "FIXED": {
        "name": "고정궁",
        "meaning": "안정, 지속, 고집",
        "category_hints": {
            "LOVE": "관계 안정화, 신뢰 구축",
            "MONEY": "자산 보존, 안정적 수익",
            "CAREER": "업무 안정성, 꾸준한 성과",
            "HEALTH": "체력 유지, 면역력 강화",
            "STUDY": "기초 다지기, 꾸준한 학습",
            "GENERAL": "현상 유지, 안정적 흐름",
        },
    },
    "MUTABLE": {
        "name": "변통궁",
        "meaning": "유연성, 적응, 변화",
        "category_hints": {
            "LOVE": "관계 조정, 대화로 해결",
            "MONEY": "유동적 자산 관리, 흐름 대응",
            "CAREER": "업무 적응력, 다재다능함",
            "HEALTH": "스트레스 대응, 유연성 향상",
            "STUDY": "학습 방법 조정, 다양한 접근",
            "GENERAL": "상황 적응, 유연한 대처",
        },
    },
}


def validate_message_has_both_names(message: str, name1: str, name2: str) -> bool:
    """메시지에 두 양태 이름이 모두 포함되어 있는지 검증

    "활동궁", "고정궁", "변통궁" 전체 이름이 포함되어야 함
    "활동"만 있고 "활동궁"이 없으면 False
    """
    return name1 in message and name2 in message


def create_modality_prompt(category: str, mod1_key: str, mod2_key: str) -> tuple[str, str]:
    """양태 2개 조합 복합 메시지 생성 프롬프트

    Args:
        category: LOVE, MONEY, CAREER 등
        mod1_key: CARDINAL, FIXED 등 (첫 번째 양태)
        mod2_key: FIXED, MUTABLE 등 (두 번째 양태)

    Returns:
        (system_prompt, user_prompt)
    """
    cat_kr = CATEGORY_KR.get(category, "총운")

    mod1_data = MODALITIES[mod1_key]
    mod2_data = MODALITIES[mod2_key]

    mod1_name = mod1_data["name"]
    mod2_name = mod2_data["name"]

    mod1_meaning = mod1_data["meaning"]
    mod2_meaning = mod2_data["meaning"]

    mod1_hint = mod1_data["category_hints"].get(category, "")
    mod2_hint = mod2_data["category_hints"].get(category, "")

    system = f"""당신은 점성술 운세 전문가입니다.
두 양태(Modality) 기운을 조합해서 {cat_kr} 메시지를 작성하세요.

[절대 규칙]
1. **"{mod1_name}" 전체와 "{mod2_name}" 전체가 반드시 문장에 포함**
   - 잘못된 예: "활동의 추진력..." (✗ "활동"만 쓰면 안됨)
   - 올바른 예: "활동궁의 추진력..." (✓ "활동궁" 전체 사용)
2. 오직 한국어만 사용 (외국어 절대 금지)
3. 한 문장, 40-70자
4. 두 양태를 모두 언급 필수
5. 마침표 또는 느낌표로 끝
6. 이모지 금지
7. JSON 배열로만 출력

[양태 정보]
- 양태1: {mod1_name} - {mod1_meaning}
  {cat_kr} 관련: {mod1_hint}

- 양태2: {mod2_name} - {mod2_meaning}
  {cat_kr} 관련: {mod2_hint}

[출력 예시]
["{mod1_name}의 추진력과 {mod2_name}의 안정감이 조화를 이루어 {cat_kr}이 상승합니다.", "..."]"""

    user = f"""{mod1_name}와 {mod2_name} 복합 기운에 대한 {cat_kr} 메시지 3개.
반드시 "{mod1_name}"와 "{mod2_name}" 전체 이름을 모두 사용하세요.
JSON 배열만 출력:"""

    return system, user


async def generate_modality_messages(
    category: str,
    mod1_key: str,
    mod2_key: str,
    timeout: float = 60.0,
    max_retries: int = 5,
) -> list[str]:
    """vLLM으로 양태 복합 메시지 생성 (필터 + 재시도)"""
    system, user = create_modality_prompt(category, mod1_key, mod2_key)

    mod1_name = MODALITIES[mod1_key]["name"]
    mod2_name = MODALITIES[mod2_key]["name"]

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

                # 양태 이름 검증 (필수!)
                validated_messages = [
                    m for m in messages
                    if validate_message_has_both_names(m, mod1_name, mod2_name)
                ]

                # 최소 2개 이상 유효 메시지
                if len(validated_messages) >= 2:
                    print(f"    ✓ 시도 {attempt+1}: {len(validated_messages)}개 생성 (검증 통과)")
                    return validated_messages[:3]

                print(f"    ✗ 시도 {attempt+1}: 검증 실패 ({len(messages)}개 생성, {len(validated_messages)}개만 통과)")
                await asyncio.sleep(0.5)

        except Exception as e:
            print(f"    재시도 {attempt+1}/{max_retries}: {e}")
            await asyncio.sleep(1.0)

    # 모든 재시도 실패시 기본 메시지
    cat_kr = CATEGORY_KR.get(category, "총운")
    return [
        f"{mod1_name}의 에너지와 {mod2_name}의 특성이 조화를 이루어 {cat_kr}에 긍정적입니다.",
        f"{mod1_name}과 {mod2_name}의 복합 기운이 {cat_kr}을 돕습니다.",
    ]


async def generate_all_modality_combinations():
    """전체 54개 조합 생성 (3개 조합 × 6개 카테고리 × 3개 변형)"""
    print("=" * 60)
    print("양태(Modality) 2개 조합 전체 메시지 생성 시작")
    print("=" * 60)

    # 양태 조합 생성
    modalities = list(MODALITIES.keys())
    modality_pairs = list(combinations(modalities, 2))

    print(f"\n총 양태 조합: {len(modality_pairs)}개")
    print(f"카테고리: {len(CATEGORIES)}개")
    print(f"예상 총 메시지: {len(modality_pairs)} × {len(CATEGORIES)} × 3 = {len(modality_pairs) * len(CATEGORIES) * 3}개")

    all_results = {}
    total_tasks = len(modality_pairs) * len(CATEGORIES)
    completed = 0

    for mod1, mod2 in modality_pairs:
        sorted_mods = sorted([mod1, mod2])
        mod1_sorted, mod2_sorted = sorted_mods

        for category in CATEGORIES:
            key = f"{mod1_sorted}_{mod2_sorted}_{category}"

            mod1_name = MODALITIES[mod1]["name"]
            mod2_name = MODALITIES[mod2]["name"]
            cat_kr = CATEGORY_KR[category]

            completed += 1
            progress = (completed / total_tasks) * 100

            print(f"\n[{completed}/{total_tasks}] ({progress:.1f}%) {key}")
            print(f"  {mod1_name} + {mod2_name} | {cat_kr}")

            try:
                messages = await generate_modality_messages(category, mod1, mod2)
                all_results[key] = messages

                # 검증 결과 표시
                for i, msg in enumerate(messages, 1):
                    has_both = validate_message_has_both_names(msg, mod1_name, mod2_name)
                    mark = "✓✓" if has_both else "✗"
                    print(f"  {i}. [{mark}] {msg}")

            except Exception as e:
                print(f"  ✗ 오류: {e}")
                all_results[key] = []

            # 서버 부하 방지
            await asyncio.sleep(0.3)

    # 최종 저장
    output_path = Path(__file__).parent.parent / "data" / "western" / "modality_pairs.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"전체 생성 완료!")
    print(f"결과 저장: {output_path}")
    print(f"총 조합: {len(all_results)}개")

    # 최종 검증 통계
    total_messages = sum(len(msgs) for msgs in all_results.values())
    print(f"총 메시지: {total_messages}개")

    # 양태 이름 검증
    validation_stats = {"pass": 0, "fail": 0}
    for key, messages in all_results.items():
        # 키에서 양태 이름 추출
        parts = key.split("_")
        mod1_key, mod2_key = parts[0], parts[1]
        mod1_name = MODALITIES[mod1_key]["name"]
        mod2_name = MODALITIES[mod2_key]["name"]

        for msg in messages:
            if validate_message_has_both_names(msg, mod1_name, mod2_name):
                validation_stats["pass"] += 1
            else:
                validation_stats["fail"] += 1

    print(f"검증 통과: {validation_stats['pass']}개")
    print(f"검증 실패: {validation_stats['fail']}개")
    print(f"{'='*60}")

    return all_results


if __name__ == "__main__":
    asyncio.run(generate_all_modality_combinations())
