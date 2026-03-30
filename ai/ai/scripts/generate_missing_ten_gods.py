#!/usr/bin/env python3
"""누락된 십신 복합 메시지 생성 스크립트

누락된 224개 키에 대해 각 3개씩 메시지를 생성합니다.
10개마다 중간 저장합니다.
"""

import asyncio
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx


class SimpleLogger:
    """간단한 로거 클래스"""

    def info(self, msg: str, **kwargs: Any) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        extras = " ".join(f"{k}={v}" for k, v in kwargs.items())
        print(f"[{timestamp}] {msg} {extras}")

    def error(self, msg: str, **kwargs: Any) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        extras = " ".join(f"{k}={v}" for k, v in kwargs.items())
        print(f"[{timestamp}] ERROR: {msg} {extras}")


logger = SimpleLogger()

# vLLM API 설정
VLLM_BASE_URL = "http://13.125.68.166:8001"
VLLM_MODEL = "tellang/yeji-8b-rslora-v7"
VLLM_TIMEOUT = 120.0

# 십신 정보
TEN_GODS_INFO = {
    "BIJEON": {"name": "비견", "traits": ["독립심", "자존심", "동료애"]},
    "GEOBJE": {"name": "겁재", "traits": ["모험심", "도전정신", "순발력"]},
    "SIKSHIN": {"name": "식신", "traits": ["창의력", "표현력", "낙천성"]},
    "SANGGWAN": {"name": "상관", "traits": ["재능", "예술성", "자유로움"]},
    "PYEONJAE": {"name": "편재", "traits": ["투기성", "활동력", "사교성"]},
    "JEONGJAE": {"name": "정재", "traits": ["안정성", "꾸준함", "책임감"]},
    "PYEONGWAN": {"name": "편관", "traits": ["권력지향", "추진력", "결단력"]},
    "JEONGGWAN": {"name": "정관", "traits": ["명예심", "규율", "충성심"]},
    "PYEONIN": {"name": "편인", "traits": ["학구열", "직관력", "독창성"]},
    "JEONGIN": {"name": "정인", "traits": ["보호본능", "학습능력", "인내심"]},
}

CATEGORY_MAP = {
    "MONEY": "재물운",
    "HEALTH": "건강운",
    "LOVE": "애정운",
    "CAREER": "직업운",
    "STUDY": "학업운",
    "SOCIAL": "대인운",
}

# 파일 경로
OUTPUT_DIR = Path("C:/Users/SSAFY/yeji-ai-server/ai/data/eastern")
OUTPUT_FILE = OUTPUT_DIR / "ten_gods_pairs.json"


def clean_korean_text(text: str) -> str:
    """한국어와 기본 문장부호만 남기고 정제"""
    pattern = r"[^가-힣0-9\s.,!?~\-]"
    cleaned = re.sub(pattern, "", text)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


async def call_vllm_api(prompt: str, temperature: float = 0.8) -> str:
    """vLLM API 호출"""
    url = f"{VLLM_BASE_URL}/v1/chat/completions"

    payload = {
        "model": VLLM_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": 150,
        "stream": False,
    }

    async with httpx.AsyncClient(timeout=VLLM_TIMEOUT) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        return clean_korean_text(content)


def generate_prompt(god1: str, god2: str, category: str, variation: int) -> str:
    """십신 조합 프롬프트 생성 (변형 포함)"""
    god1_info = TEN_GODS_INFO[god1]
    god2_info = TEN_GODS_INFO[god2]
    category_kr = CATEGORY_MAP[category]

    # 동일 십신인 경우 다른 프롬프트
    if god1 == god2:
        variation_prompts = [
            f"{god1_info['name']}의 기운이 두 배로 강해져 {category_kr}에 큰 힘이 됩니다.",
            f"{god1_info['name']}의 에너지가 증폭되어 {category_kr}이 상승합니다.",
            f"{god1_info['name']}이 겹쳐 그 특성이 극대화되어 {category_kr}에 좋은 영향을 줍니다.",
        ]

        prompt = f"""당신은 사주명리학 전문가입니다.

십신 정보:
- {god1_info["name"]}({god1}): {', '.join(god1_info["traits"])}

카테고리: {category_kr}

동일한 십신({god1_info["name"]})이 겹쳤을 때 {category_kr}에 미치는 긍정적인 영향을 한 문장으로 표현하세요.

참고 표현: {variation_prompts[variation]}

요구사항:
1. 밝고 긍정적인 톤
2. 자연스러운 한국어
3. 30-50자 길이
4. 이모지 없이 순수 한글만 사용

답변:"""
    else:
        trait_combos = [
            (god1_info["traits"][0], god2_info["traits"][0]),
            (god1_info["traits"][1], god2_info["traits"][1]),
            (god1_info["traits"][2 % len(god1_info["traits"])], god2_info["traits"][2 % len(god2_info["traits"])]),
        ]
        t1, t2 = trait_combos[variation]

        prompt = f"""당신은 사주명리학 전문가입니다.

십신 조합 정보:
- {god1_info["name"]}({god1}): {', '.join(god1_info["traits"])}
- {god2_info["name"]}({god2}): {', '.join(god2_info["traits"])}

카테고리: {category_kr}

위 두 십신의 특성({t1}, {t2})이 조화를 이뤄 {category_kr}에 미치는 긍정적인 영향을 한 문장으로 표현하세요.

요구사항:
1. 형식: "[십신1]의 [특성]과 [십신2]의 [특성]이 만나 [효과]"
2. 밝고 긍정적인 톤
3. 자연스러운 한국어
4. 30-50자 길이
5. 이모지 없이 순수 한글만 사용

답변:"""

    return prompt


def get_missing_keys() -> list[str]:
    """누락된 키 목록 반환"""
    TEN_GODS = [
        "BIJEON", "GEOBJE", "SIKSHIN", "SANGGWAN", "PYEONJAE",
        "JEONGJAE", "PYEONGWAN", "JEONGGWAN", "PYEONIN", "JEONGIN"
    ]
    CATEGORIES = ["MONEY", "HEALTH", "LOVE", "CAREER", "STUDY", "SOCIAL"]

    # 모든 가능한 키 (동일 십신 조합 포함)
    all_keys = set()
    for god1 in TEN_GODS:
        for god2 in TEN_GODS:
            for cat in CATEGORIES:
                g1, g2 = sorted([god1, god2])
                key = f"{g1}_{g2}_{cat}"
                all_keys.add(key)

    # 현재 존재하는 키
    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    existing_keys = set(data.keys())

    # 누락된 키
    missing = sorted(all_keys - existing_keys)
    return missing


async def generate_messages_for_key(key: str) -> list[str]:
    """하나의 키에 대해 3개의 메시지 생성"""
    parts = key.split("_")
    god1, god2, category = parts[0], parts[1], parts[2]

    messages = []
    for i in range(3):
        try:
            prompt = generate_prompt(god1, god2, category, i)
            msg = await call_vllm_api(prompt, temperature=0.8 + i * 0.05)
            messages.append(msg)
        except Exception as e:
            logger.error(f"Failed to generate", key=key, variation=i, error=str(e))
            # 폴백 메시지
            god1_name = TEN_GODS_INFO[god1]["name"]
            god2_name = TEN_GODS_INFO[god2]["name"]
            if god1 == god2:
                messages.append(f"{god1_name}의 기운이 두 배로 강해집니다.")
            else:
                messages.append(f"{god1_name}과 {god2_name}의 조화로운 기운이 함께합니다.")

    return messages


def save_data(data: dict[str, list[str]]) -> None:
    """데이터 저장"""
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


async def main() -> None:
    """메인 실행"""
    logger.info("Script started")

    # 현재 데이터 로드
    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 누락된 키 확인
    missing_keys = get_missing_keys()
    logger.info(f"Missing keys: {len(missing_keys)}")

    if not missing_keys:
        logger.info("No missing keys. Done.")
        return

    total = len(missing_keys)
    completed = 0
    errors = 0

    for key in missing_keys:
        try:
            messages = await generate_messages_for_key(key)
            data[key] = messages
            completed += 1

            logger.info(f"Generated", key=key, progress=f"{completed}/{total}")

            # 10개마다 중간 저장
            if completed % 10 == 0:
                save_data(data)
                logger.info(f"Checkpoint saved at {completed}")

        except Exception as e:
            logger.error(f"Failed", key=key, error=str(e))
            errors += 1
            # 폴백 메시지 추가
            parts = key.split("_")
            god1, god2 = parts[0], parts[1]
            god1_name = TEN_GODS_INFO[god1]["name"]
            god2_name = TEN_GODS_INFO[god2]["name"]
            if god1 == god2:
                data[key] = [f"{god1_name}의 기운이 강해집니다."] * 3
            else:
                data[key] = [f"{god1_name}과 {god2_name}의 조화"] * 3

    # 최종 저장
    save_data(data)
    logger.info(f"Complete", total_keys=len(data), generated=completed, errors=errors)


if __name__ == "__main__":
    asyncio.run(main())
