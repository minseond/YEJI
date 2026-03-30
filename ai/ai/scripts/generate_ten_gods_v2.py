#!/usr/bin/env python3
"""십신 복합 메시지 생성 스크립트 v2 - 품질 강화 버전"""

import json
import time
import re
import httpx
from itertools import combinations
from pathlib import Path

# 설정
VLLM_URL = "http://13.125.68.166:8001/v1/completions"
MODEL = "tellang/yeji-8b-rslora-v7"
OUTPUT_FILE = Path("C:/Users/SSAFY/yeji-ai-server/ai/data/eastern/ten_gods_pairs.json")

# 십신 정의
TEN_GODS = ["BIJEON", "GEOBJE", "SIKSHIN", "SANGGWAN", "PYEONJAE", "JEONGJAE", "PYEONGWAN", "JEONGGWAN", "PYEONIN", "JEONGIN"]
TEN_GODS_NAMES = {
    "BIJEON": "비견", "GEOBJE": "겁재", "SIKSHIN": "식신", "SANGGWAN": "상관",
    "PYEONJAE": "편재", "JEONGJAE": "정재", "PYEONGWAN": "편관", "JEONGGWAN": "정관",
    "PYEONIN": "편인", "JEONGIN": "정인",
}

# 카테고리 정의
CATEGORIES = ["GENERAL", "LOVE", "MONEY", "CAREER", "HEALTH", "STUDY"]
CATEGORY_KR = {
    "GENERAL": "총운", "LOVE": "연애운", "MONEY": "금전운",
    "CAREER": "직장운", "HEALTH": "건강운", "STUDY": "학업운"
}

# 카테고리별 좋은 예시
CATEGORY_EXAMPLES = {
    "GENERAL": "의 기운이 만나 운세가 상승하고 좋은 흐름이 이어집니다.",
    "LOVE": "의 조화로 연애운이 밝아지고 새로운 인연이 다가옵니다.",
    "MONEY": "의 결합으로 금전운이 상승하고 재물이 늘어납니다.",
    "CAREER": "의 시너지로 직장운이 좋아지고 승진 기회가 옵니다.",
    "HEALTH": "의 균형으로 건강운이 회복되고 활력이 넘칩니다.",
    "STUDY": "의 결합으로 학업운이 상승하고 성적이 오릅니다.",
}


def validate_message(msg: str, name1: str, name2: str) -> bool:
    """메시지 품질 검증"""
    # 길이 체크 (30-80자)
    if not (30 <= len(msg) <= 80):
        return False
    # 십신 이름 체크
    if name1 not in msg or name2 not in msg:
        return False
    # 메타텍스트 체크
    bad_words = ["템플릿", "요약", "분석", "질문", "답변", "다시", "요구사항", "예시", "설명", "해드", "드리"]
    if any(w in msg for w in bad_words):
        return False
    # 반복 체크
    if msg.count(name1) > 2 or msg.count(name2) > 2:
        return False
    # 마침표 체크
    if not msg.endswith(".") and not msg.endswith("!") and not msg.endswith("다"):
        return False
    return True


def clean_message(msg: str) -> str:
    """메시지 정제"""
    # 앞뒤 공백 제거
    msg = msg.strip()
    # 외국어 문자 제거
    msg = re.sub(r'[^\uAC00-\uD7A3\u3131-\u3163a-zA-Z0-9\s.,!?()~\-]', '', msg)
    # 연속 공백 제거
    msg = re.sub(r'\s+', ' ', msg)
    # 첫 문장만 추출
    for sep in ['. ', '! ', '? ', '\n']:
        if sep in msg:
            msg = msg.split(sep)[0] + sep[0]
            break
    return msg.strip()


def generate_message(name1: str, name2: str, category: str, category_kr: str, attempt: int = 1) -> str | None:
    """단일 메시지 생성"""

    # 개선된 프롬프트
    system_prompt = f"""사주 운세 한 문장 작성기.
규칙: "{name1}"와 "{name2}" 필수 포함, 40-60자, 마침표 끝.

좋은 예:
- {name1}의 자립심과 {name2}의 협력이 만나 {category_kr}이 상승합니다.
- {name1}의 기운과 {name2}의 힘이 조화를 이루어 {category_kr}이 좋아집니다.
- {name1}과 {name2}{CATEGORY_EXAMPLES[category]}

나쁜 예 (절대 금지):
- 템플릿을 제시해주세요 (X)
- 분석해드리겠습니다 (X)"""

    user_prompt = f"{name1}+{name2} {category_kr}:"

    full_prompt = f"<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\n{user_prompt}<|im_end|>\n<|im_start|>assistant\n"

    try:
        with httpx.Client(timeout=30) as client:
            resp = client.post(
                VLLM_URL,
                json={
                    "model": MODEL,
                    "prompt": full_prompt,
                    "max_tokens": 80,
                    "temperature": 0.6 + (attempt * 0.1),
                    "stop": ["<|im_end|>", "\n", ".", "!"],
                }
            )

            if resp.status_code == 200:
                text = resp.json()["choices"][0]["text"].strip()
                # 마침표 추가
                if not text.endswith((".", "!", "다")):
                    text += "."
                return clean_message(text)
    except Exception as e:
        print(f"    오류: {e}")

    return None


def generate_messages_for_pair(god1: str, god2: str, category: str) -> list[str]:
    """쌍에 대해 3개 메시지 생성"""
    name1 = TEN_GODS_NAMES[god1]
    name2 = TEN_GODS_NAMES[god2]
    category_kr = CATEGORY_KR[category]

    messages = []
    max_attempts = 10
    attempt = 0

    while len(messages) < 3 and attempt < max_attempts:
        attempt += 1
        msg = generate_message(name1, name2, category, category_kr, attempt)

        if msg and validate_message(msg, name1, name2):
            # 중복 체크
            if msg not in messages:
                messages.append(msg)

        time.sleep(0.3)  # rate limit

    return messages


def main():
    print("=" * 60)
    print("십신 복합 메시지 생성 v2 (품질 강화)")
    print("=" * 60)

    # 45쌍 생성
    pairs = list(combinations(TEN_GODS, 2))
    total_combos = len(pairs) * len(CATEGORIES)

    print(f"\n총 십신 조합: {len(pairs)}쌍")
    print(f"총 생성 목표: {total_combos}개 키 × 3개 = {total_combos * 3}개 메시지")
    print()

    results = {}
    completed = 0
    total_messages = 0

    for god1, god2 in pairs:
        for category in CATEGORIES:
            completed += 1
            key = f"{god1}_{god2}_{category}"
            name1 = TEN_GODS_NAMES[god1]
            name2 = TEN_GODS_NAMES[god2]

            print(f"[{completed}/{total_combos}] ({completed*100//total_combos}%) {key}")
            print(f"  {name1} + {name2} | {CATEGORY_KR[category]}")

            messages = generate_messages_for_pair(god1, god2, category)
            results[key] = messages
            total_messages += len(messages)

            print(f"  ✓ {len(messages)}개 생성")

            # 중간 저장 (10개마다)
            if completed % 10 == 0:
                OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
                with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
                print(f"  [중간 저장: {len(results)}개 키]")

    # 최종 저장
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print()
    print("=" * 60)
    print(f"완료! 총 {len(results)}개 키, {total_messages}개 메시지 생성")
    print(f"저장: {OUTPUT_FILE}")
    print("=" * 60)


if __name__ == "__main__":
    main()
