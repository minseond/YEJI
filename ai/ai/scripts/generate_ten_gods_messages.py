#!/usr/bin/env python3
"""십신 2개 조합 복합 메시지 생성 스크립트

십신 45개 조합(C(10,2)) × 6개 카테고리 × 3개 변형 = 810개 메시지 생성
현재는 샘플로 각 조합당 1개씩 45개 생성 후 품질 확인
"""

import asyncio
import json
import re
from collections.abc import AsyncGenerator
from datetime import datetime
from itertools import combinations
from pathlib import Path
from typing import Any

import httpx


class SimpleLogger:
    """간단한 로거 클래스"""

    def info(self, msg: str, **kwargs: Any) -> None:
        timestamp = datetime.now().isoformat()
        print(f"[INFO] {timestamp} {msg} {kwargs}")

    def error(self, msg: str, **kwargs: Any) -> None:
        timestamp = datetime.now().isoformat()
        print(f"[ERROR] {timestamp} {msg} {kwargs}")


logger = SimpleLogger()

# vLLM API 설정
VLLM_BASE_URL = "http://13.125.68.166:8001"
VLLM_MODEL = "tellang/yeji-8b-rslora-v7"
VLLM_TIMEOUT = 120.0

# 십신 목록
TEN_GODS = [
    "BIJEON",      # 비견
    "GEOBJE",      # 겁재
    "SIKSHIN",     # 식신
    "SANGGWAN",    # 상관
    "PYEONJAE",    # 편재
    "JEONGJAE",    # 정재
    "PYEONGWAN",   # 편관
    "JEONGGWAN",   # 정관
    "PYEONIN",     # 편인
    "JEONGIN",     # 정인
]

# 십신 정보 (특성)
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

# 카테고리 목록
CATEGORIES = ["MONEY", "HEALTH", "LOVE", "CAREER", "STUDY", "SOCIAL"]

# 출력 경로
OUTPUT_DIR = Path("C:/Users/SSAFY/yeji-ai-server/ai/data/eastern")
OUTPUT_FILE = OUTPUT_DIR / "ten_gods_pairs.json"


def clean_korean_text(text: str) -> str:
    """한국어와 기본 문장부호만 남기고 외래 문자 제거

    Args:
        text: 입력 텍스트

    Returns:
        정제된 한국어 텍스트
    """
    # 한글, 숫자, 공백, 기본 문장부호만 허용
    pattern = r"[^가-힣0-9\s.,!?~\-]"
    cleaned = re.sub(pattern, "", text)

    # 연속 공백 제거
    cleaned = re.sub(r"\s+", " ", cleaned)

    return cleaned.strip()


async def call_vllm_api(
    prompt: str,
    temperature: float = 0.8,
    max_tokens: int = 150,
) -> str:
    """vLLM API 호출

    Args:
        prompt: 프롬프트
        temperature: 샘플링 온도
        max_tokens: 최대 토큰 수

    Returns:
        생성된 텍스트

    Raises:
        httpx.HTTPError: API 호출 실패
    """
    url = f"{VLLM_BASE_URL}/v1/chat/completions"

    payload = {
        "model": VLLM_MODEL,
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }

    async with httpx.AsyncClient(timeout=VLLM_TIMEOUT) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()

        data = response.json()
        content = data["choices"][0]["message"]["content"]

        return clean_korean_text(content)


def generate_prompt(god1: str, god2: str, category: str) -> str:
    """십신 2개 조합 프롬프트 생성

    Args:
        god1: 첫 번째 십신 (알파벳순)
        god2: 두 번째 십신 (알파벳순)
        category: 카테고리

    Returns:
        생성된 프롬프트
    """
    god1_info = TEN_GODS_INFO[god1]
    god2_info = TEN_GODS_INFO[god2]

    category_map = {
        "MONEY": "재물운",
        "HEALTH": "건강운",
        "LOVE": "애정운",
        "CAREER": "직업운",
        "STUDY": "학업운",
        "SOCIAL": "대인운",
    }

    category_kr = category_map[category]

    prompt = f"""당신은 사주명리학 전문가입니다.

십신 조합 정보:
- {god1_info["name"]}({god1}): {', '.join(god1_info["traits"])}
- {god2_info["name"]}({god2}): {', '.join(god2_info["traits"])}

카테고리: {category_kr}

위 두 십신의 특성이 조화를 이뤄 {category_kr}에 미치는 긍정적인 영향을 한 문장으로 표현하세요.

요구사항:
1. 형식: "[십신1]의 [특성]과 [십신2]의 [특성]이 만나 [효과]"
2. 밝고 긍정적인 톤
3. 자연스러운 한국어 (존댓말 또는 반말 통일)
4. 30-50자 길이
5. 이모지 없이 순수 한글만 사용

예시: "비견의 독립심과 식신의 창의력이 만나 새로운 수익 기회가 열려요!"

답변:"""

    return prompt


async def generate_message(god1: str, god2: str, category: str) -> str:
    """십신 조합 메시지 생성

    Args:
        god1: 첫 번째 십신
        god2: 두 번째 십신
        category: 카테고리

    Returns:
        생성된 메시지
    """
    prompt = generate_prompt(god1, god2, category)

    logger.info(
        "generate_message_start",
        god1=god1,
        god2=god2,
        category=category,
    )

    try:
        message = await call_vllm_api(prompt, temperature=0.8, max_tokens=150)

        logger.info(
            "generate_message_complete",
            god1=god1,
            god2=god2,
            category=category,
            message_length=len(message),
        )

        return message

    except Exception as e:
        logger.error(
            "generate_message_error",
            god1=god1,
            god2=god2,
            category=category,
            error=str(e),
        )
        raise


async def generate_all_messages(sample_mode: bool = True) -> dict[str, list[str]]:
    """모든 십신 조합 메시지 생성

    Args:
        sample_mode: True면 각 조합당 1개씩만 (45개), False면 전체 (810개)

    Returns:
        {key: [message1, message2, message3]} 형태의 딕셔너리
    """
    results: dict[str, list[str]] = {}

    # 십신 조합 생성 (C(10,2) = 45개)
    god_pairs = list(combinations(TEN_GODS, 2))

    logger.info(
        "generation_start",
        total_pairs=len(god_pairs),
        categories=len(CATEGORIES),
        sample_mode=sample_mode,
    )

    total_count = 0
    error_count = 0

    for god1, god2 in god_pairs:
        # 알파벳순 정렬 (일관성)
        if god1 > god2:
            god1, god2 = god2, god1

        for category in CATEGORIES:
            key = f"{god1}_{god2}_{category}"

            if sample_mode:
                # 샘플 모드: 1개만 생성
                try:
                    message = await generate_message(god1, god2, category)
                    results[key] = [message]
                    total_count += 1

                    # 진행 상황 로깅 (10개마다)
                    if total_count % 10 == 0:
                        logger.info("progress", completed=total_count, total=45 * 6)

                except Exception as e:
                    logger.error("message_generation_failed", key=key, error=str(e))
                    error_count += 1
                    results[key] = [f"[생성 실패] {god1}과 {god2}의 조화"]

            else:
                # 전체 모드: 3개 변형 생성
                messages = []
                for i in range(3):
                    try:
                        message = await generate_message(god1, god2, category)
                        messages.append(message)
                        total_count += 1

                        # 진행 상황 로깅 (30개마다)
                        if total_count % 30 == 0:
                            logger.info("progress", completed=total_count, total=45 * 6 * 3)

                    except Exception as e:
                        logger.error("message_generation_failed", key=key, index=i, error=str(e))
                        error_count += 1
                        messages.append(f"[생성 실패] {god1}과 {god2}의 조화")

                results[key] = messages

    logger.info(
        "generation_complete",
        total_generated=total_count,
        errors=error_count,
        unique_keys=len(results),
    )

    return results


async def main() -> None:
    """메인 실행 함수"""
    logger.info("script_start", mode="sample")

    # 출력 디렉토리 생성
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 샘플 모드로 메시지 생성 (각 조합당 1개씩 45*6=270개)
    messages = await generate_all_messages(sample_mode=True)

    # JSON 저장
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)

    logger.info(
        "script_complete",
        output_file=str(OUTPUT_FILE),
        total_keys=len(messages),
        file_size_kb=OUTPUT_FILE.stat().st_size / 1024,
    )

    # 샘플 출력 (첫 5개)
    print("\n=== 생성된 메시지 샘플 (처음 5개) ===")
    for i, (key, msgs) in enumerate(list(messages.items())[:5]):
        print(f"\n{i+1}. {key}:")
        for j, msg in enumerate(msgs):
            print(f"   [{j+1}] {msg}")


if __name__ == "__main__":
    asyncio.run(main())
