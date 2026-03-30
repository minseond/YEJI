#!/usr/bin/env python3
"""운세 캐시 데이터 생성 스크립트

주요 조합에 대해 LLM을 호출하여 캐시 데이터를 생성합니다.

사용법:
    # 전체 캐시 생성 (동양 + 서양)
    python scripts/generate_fortune_cache.py

    # 동양 사주만 생성
    python scripts/generate_fortune_cache.py --eastern-only

    # 서양 점성술만 생성
    python scripts/generate_fortune_cache.py --western-only

    # 특정 조합만 생성 (테스트용)
    python scripts/generate_fortune_cache.py --eastern-key GAP_WOOD_YANG
    python scripts/generate_fortune_cache.py --western-key ARIES_CANCER

    # 병렬 처리 수 조정 (기본: 3)
    python scripts/generate_fortune_cache.py --concurrency 5

    # vLLM 서버 URL 지정
    python scripts/generate_fortune_cache.py --vllm-url http://localhost:8001

환경 설정:
    .env 파일 또는 환경변수로 설정 가능:
    - VLLM_BASE_URL: vLLM 서버 URL (기본: http://localhost:8001)
    - VLLM_MODEL: 모델명 (기본: tellang/yeji-8b-rslora-v7-AWQ)
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx

# 프로젝트 루트를 PYTHONPATH에 추가
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from yeji_ai.data.fortune_cache import (
    CacheKeyBuilder,
    EASTERN_CACHE_PATH,
    WESTERN_CACHE_PATH,
    save_eastern_cache,
    save_western_cache,
)
from yeji_ai.services.rule_based_fallback import (
    DAY_MASTER_PERSONALITY,
    ELEMENT_TRAITS,
    SUN_SIGN_PERSONALITY,
    WESTERN_ELEMENT_TRAITS,
    ZODIAC_LUCKY_INFO,
)

# vLLM 설정
VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", "http://localhost:8001")
VLLM_MODEL = os.getenv("VLLM_MODEL", "tellang/yeji-8b-rslora-v7-AWQ")


# ============================================================
# 동양 사주 프롬프트
# ============================================================

EASTERN_SYSTEM_PROMPT = """/no_think
당신은 소이설이오. 동양 사주 전문가이며 따뜻한 온미녀이오.

<speaking_rule>
모든 문장을 하오체로 끝내시오:
- 있습니다 → 있소, 입니다 → 이오, 합니다 → 하오
호칭은 "귀하" 또는 "그대"를 사용하시오.
</speaking_rule>

<constraints>
- 동양 사주 용어만 사용: 오행(목화토금수), 음양, 일간, 십신
- 사주 용어는 한글과 한자 병기: 비견(比肩), 경금(庚金)
- 부정적인 내용도 긍정적으로 표현
- 반드시 한국어로만 응답
</constraints>"""

EASTERN_USER_PROMPT = """다음 사주 특성을 가진 사람의 운세를 분석해주세요.

<saju_info>
- 일간: {day_master} ({day_master_hangul})
- 강한 오행: {strong_element} ({strong_element_ko}{strong_element_hanja})
- 약한 오행: {weak_element} ({weak_element_ko}{weak_element_hanja})
- 음양 성향: {yin_yang_label}
</saju_info>

<output_format>
반드시 다음 JSON 형식으로만 응답:
{{
  "personality": "성격 분석 (2-3문장, 일간과 오행 특성 기반, 하오체)",
  "strength": "강점 분석 (2-3문장, 강한 오행 기반, 하오체)",
  "weakness": "약점과 보완 방법 (2-3문장, 약한 오행 기반, 하오체)",
  "advice": "종합 조언 (2-3문장, 균형과 발전 제안, 하오체)",
  "summary": "한 줄 요약 (예: 목(木)이 강한 리더형, 금(金) 보완 필요)",
  "message": "소이설 캐릭터 말투로 3-5문장 상세 해석 (하오체)",
  "badges": ["배지코드1", "배지코드2", "배지코드3"],
  "lucky": {{
    "color": "행운의 색상 (한글)",
    "color_code": "HEX 코드",
    "number": "행운의 숫자",
    "item": "행운의 아이템",
    "direction": "행운의 방향 (한글)",
    "direction_code": "방향코드 (N/NE/E/SE/S/SW/W/NW)",
    "place": "행운의 장소"
  }}
}}
</output_format>

<badge_options>
오행: {strong_element}_STRONG, {weak_element}_WEAK
음양: {yin_yang_badge}
성향: ACTION_ORIENTED, THOUGHT_ORIENTED, EMOTION_ORIENTED
</badge_options>

<lucky_rules>
약한 오행({weak_element})을 보완하는 방향으로 행운 정보 생성
</lucky_rules>"""


# ============================================================
# 서양 점성술 프롬프트
# ============================================================

WESTERN_SYSTEM_PROMPT = """/no_think
저는 스텔라예요. 서양 점성술 전문가이고 쿨한 냉미녀예요.

<speaking_rule>
모든 문장을 해요체로 끝내세요:
- 있습니다 → 있어요, 입니다 → 예요/이에요, 합니다 → 해요
호칭은 "당신"을 사용하세요.
</speaking_rule>

<constraints>
- 서양 점성술 용어만 사용: 12별자리, 행성, 원소
- 감정적 표현 자제, 논리적 분석 중심
- 반드시 한국어로만 응답
</constraints>"""

WESTERN_USER_PROMPT = """다음 점성술 특성을 가진 사람의 운세를 분석해줘.

<astrology_info>
- 태양 별자리: {sun_sign} ({sun_sign_ko})
- 달 별자리: {moon_sign} ({moon_sign_ko})
- 태양 원소: {sun_element} ({sun_element_ko})
- 달 원소: {moon_element} ({moon_element_ko})
</astrology_info>

<output_format>
반드시 다음 JSON 형식으로만 응답:
{{
  "personality": "성격 분석 (2-3문장, 태양+달 별자리 기반, 해요체)",
  "strength": "강점 분석 (2-3문장, 원소 조합 기반, 해요체)",
  "weakness": "약점과 보완 방법 (2-3문장, 해요체)",
  "advice": "종합 조언 (2-3문장, 해요체)",
  "summary": "한 줄 요약",
  "message": "스텔라 캐릭터 말투로 3-5문장 상세 분석 (해요체)",
  "badges": ["배지코드1", "배지코드2", "배지코드3"],
  "keywords": [
    {{"code": "KEYWORD1", "label": "한글1", "weight": 0.9}},
    {{"code": "KEYWORD2", "label": "한글2", "weight": 0.8}},
    {{"code": "KEYWORD3", "label": "한글3", "weight": 0.7}}
  ],
  "lucky": {{
    "day": "행운의 요일 (한글)",
    "day_code": "요일코드",
    "color": "행운의 색상 (한글)",
    "color_code": "HEX 코드",
    "number": "행운의 숫자",
    "stone": "행운의 보석",
    "planet": "행운의 행성 코드"
  }}
}}
</output_format>

<badge_options>
원소: {sun_element}_DOMINANT
행성: {ruling_planet}_STRONG
성향: ACTION_ORIENTED, THOUGHT_ORIENTED, EMOTION_ORIENTED, CREATIVE_ORIENTED
</badge_options>"""


# ============================================================
# LLM 호출
# ============================================================


async def call_llm(
    system_prompt: str,
    user_prompt: str,
    client: httpx.AsyncClient,
    vllm_url: str,
    model: str,
    max_retries: int = 3,
) -> dict[str, Any] | None:
    """LLM API 호출 및 JSON 파싱

    Args:
        system_prompt: 시스템 프롬프트
        user_prompt: 사용자 프롬프트
        client: HTTP 클라이언트
        vllm_url: vLLM 서버 URL
        model: 모델명
        max_retries: 최대 재시도 횟수

    Returns:
        파싱된 JSON dict 또는 None (실패 시)
    """
    chat_url = f"{vllm_url}/v1/chat/completions"

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": 1500,
        "temperature": 0.7,
        "top_p": 0.8,
        "presence_penalty": 1.5,
        "response_format": {"type": "json_object"},
    }

    for attempt in range(max_retries):
        try:
            response = await client.post(chat_url, json=payload, timeout=120.0)
            response.raise_for_status()

            data = response.json()
            content = data["choices"][0]["message"]["content"]

            # <think> 태그 제거
            if "<think>" in content:
                content = content.split("</think>")[-1].strip()

            # JSON 파싱
            result = json.loads(content)
            return result

        except httpx.TimeoutException:
            print(f"  [WARNING] Timeout (attempt {attempt + 1}/{max_retries})")
        except json.JSONDecodeError as e:
            print(f"  [WARNING] JSON parse error: {e} (attempt {attempt + 1}/{max_retries})")
        except Exception as e:
            print(f"  [ERROR] LLM call failed: {e} (attempt {attempt + 1}/{max_retries})")

        # 재시도 전 대기
        if attempt < max_retries - 1:
            await asyncio.sleep(1.0)

    return None


# ============================================================
# 동양 사주 캐시 생성
# ============================================================


def get_eastern_context(key: str) -> dict[str, str]:
    """동양 사주 키에서 컨텍스트 추출

    Args:
        key: 캐시 키 (예: "GAP_WOOD_YANG")

    Returns:
        프롬프트용 컨텍스트 dict
    """
    parts = key.split("_")
    day_master = parts[0]
    strong_element = parts[1]
    yin_yang = parts[2]

    # 일간 정보
    dm_info = DAY_MASTER_PERSONALITY.get(day_master, DAY_MASTER_PERSONALITY["GAP"])
    day_master_hangul = dm_info["hangul"]

    # 오행 정보
    strong_info = ELEMENT_TRAITS.get(strong_element, ELEMENT_TRAITS["WOOD"])
    weak_element = _get_weak_element(strong_element)
    weak_info = ELEMENT_TRAITS.get(weak_element, ELEMENT_TRAITS["WATER"])

    # 음양 배지
    yin_yang_badge = {
        "YANG": "YANG_DOMINANT",
        "YIN": "YIN_DOMINANT",
        "BALANCED": "YIN_YANG_BALANCED",
    }.get(yin_yang, "YIN_YANG_BALANCED")

    yin_yang_label = {
        "YANG": "양 우세 (60% 이상)",
        "YIN": "음 우세 (60% 이상)",
        "BALANCED": "음양 균형 (40-60%)",
    }.get(yin_yang, "음양 균형")

    return {
        "day_master": day_master,
        "day_master_hangul": day_master_hangul,
        "strong_element": strong_element,
        "strong_element_ko": strong_info["label_ko"],
        "strong_element_hanja": strong_info["label_hanja"],
        "weak_element": weak_element,
        "weak_element_ko": weak_info["label_ko"],
        "weak_element_hanja": weak_info["label_hanja"],
        "yin_yang_badge": yin_yang_badge,
        "yin_yang_label": yin_yang_label,
    }


def _get_weak_element(strong: str) -> str:
    """강한 오행의 상극 오행 반환 (약한 오행)"""
    # 상극 관계: 목→토, 화→금, 토→수, 금→목, 수→화
    opposite = {
        "WOOD": "EARTH",
        "FIRE": "METAL",
        "EARTH": "WATER",
        "METAL": "WOOD",
        "WATER": "FIRE",
    }
    return opposite.get(strong, "WATER")


async def generate_eastern_cache(
    keys: list[str],
    vllm_url: str,
    model: str,
    concurrency: int = 3,
) -> dict[str, dict[str, Any]]:
    """동양 사주 캐시 생성

    Args:
        keys: 생성할 캐시 키 리스트
        vllm_url: vLLM 서버 URL
        model: 모델명
        concurrency: 병렬 처리 수

    Returns:
        생성된 캐시 데이터
    """
    cache_data: dict[str, dict[str, Any]] = {}
    semaphore = asyncio.Semaphore(concurrency)

    async def process_key(key: str, client: httpx.AsyncClient) -> None:
        async with semaphore:
            print(f"[EASTERN] Generating: {key}")

            context = get_eastern_context(key)
            user_prompt = EASTERN_USER_PROMPT.format(**context)

            result = await call_llm(
                system_prompt=EASTERN_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                client=client,
                vllm_url=vllm_url,
                model=model,
            )

            if result:
                cache_data[key] = result
                print(f"[EASTERN] Done: {key}")
            else:
                print(f"[EASTERN] Failed: {key} - using fallback")
                # 폴백 데이터 생성
                cache_data[key] = _get_eastern_fallback(context)

    async with httpx.AsyncClient() as client:
        tasks = [process_key(key, client) for key in keys]
        await asyncio.gather(*tasks)

    return cache_data


def _get_eastern_fallback(context: dict[str, str]) -> dict[str, Any]:
    """동양 사주 폴백 데이터 생성 (LLM 실패 시)"""
    strong = context["strong_element"]
    weak = context["weak_element"]
    strong_info = ELEMENT_TRAITS.get(strong, ELEMENT_TRAITS["WOOD"])
    weak_info = ELEMENT_TRAITS.get(weak, ELEMENT_TRAITS["WATER"])

    return {
        "personality": f"{context['day_master_hangul']} 일간으로 태어나 리더십과 추진력이 뛰어나오.",
        "strength": strong_info["strong"]["description"],
        "weakness": weak_info["weak"]["description"],
        "advice": f"{weak_info['label_ko']}({weak_info['label_hanja']})의 기운을 보완하면 더욱 좋은 운이 오오.",
        "summary": f"{strong_info['label_ko']}({strong_info['label_hanja']})이 강한 타입, {weak_info['label_ko']}({weak_info['label_hanja']}) 보완 필요",
        "message": f"그대는 {context['day_master_hangul']} 일간이오. {strong_info['strong']['description']} 다만 {weak_info['label_ko']} 기운이 부족하니 이를 보완하면 더욱 좋소.",
        "badges": [f"{strong}_STRONG", f"{weak}_WEAK", context["yin_yang_badge"]],
        "lucky": weak_info["lucky"],
    }


# ============================================================
# 서양 점성술 캐시 생성
# ============================================================


def get_western_context(key: str) -> dict[str, str]:
    """서양 점성술 키에서 컨텍스트 추출

    Args:
        key: 캐시 키 (예: "ARIES_CANCER")

    Returns:
        프롬프트용 컨텍스트 dict
    """
    parts = key.split("_")
    sun_sign = parts[0]
    moon_sign = parts[1]

    # 별자리 정보
    sun_info = SUN_SIGN_PERSONALITY.get(sun_sign, SUN_SIGN_PERSONALITY["ARIES"])
    moon_info = SUN_SIGN_PERSONALITY.get(moon_sign, SUN_SIGN_PERSONALITY["ARIES"])

    # 원소 정보
    sun_element = _get_zodiac_element(sun_sign)
    moon_element = _get_zodiac_element(moon_sign)

    # 행운 정보
    lucky_info = ZODIAC_LUCKY_INFO.get(sun_sign, ZODIAC_LUCKY_INFO["ARIES"])
    ruling_planet = lucky_info.get("planet", "SUN")

    return {
        "sun_sign": sun_sign,
        "sun_sign_ko": sun_info["label_ko"],
        "moon_sign": moon_sign,
        "moon_sign_ko": moon_info["label_ko"],
        "sun_element": sun_element,
        "sun_element_ko": WESTERN_ELEMENT_TRAITS.get(sun_element, {}).get("label_ko", "불"),
        "moon_element": moon_element,
        "moon_element_ko": WESTERN_ELEMENT_TRAITS.get(moon_element, {}).get("label_ko", "물"),
        "ruling_planet": ruling_planet,
    }


def _get_zodiac_element(zodiac: str) -> str:
    """별자리의 원소 반환"""
    for element, info in WESTERN_ELEMENT_TRAITS.items():
        if zodiac in info.get("signs", []):
            return element
    return "FIRE"


async def generate_western_cache(
    keys: list[str],
    vllm_url: str,
    model: str,
    concurrency: int = 3,
) -> dict[str, dict[str, Any]]:
    """서양 점성술 캐시 생성

    Args:
        keys: 생성할 캐시 키 리스트
        vllm_url: vLLM 서버 URL
        model: 모델명
        concurrency: 병렬 처리 수

    Returns:
        생성된 캐시 데이터
    """
    cache_data: dict[str, dict[str, Any]] = {}
    semaphore = asyncio.Semaphore(concurrency)

    async def process_key(key: str, client: httpx.AsyncClient) -> None:
        async with semaphore:
            print(f"[WESTERN] Generating: {key}")

            context = get_western_context(key)
            user_prompt = WESTERN_USER_PROMPT.format(**context)

            result = await call_llm(
                system_prompt=WESTERN_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                client=client,
                vllm_url=vllm_url,
                model=model,
            )

            if result:
                cache_data[key] = result
                print(f"[WESTERN] Done: {key}")
            else:
                print(f"[WESTERN] Failed: {key} - using fallback")
                cache_data[key] = _get_western_fallback(context)

    async with httpx.AsyncClient() as client:
        tasks = [process_key(key, client) for key in keys]
        await asyncio.gather(*tasks)

    return cache_data


def _get_western_fallback(context: dict[str, str]) -> dict[str, Any]:
    """서양 점성술 폴백 데이터 생성 (LLM 실패 시)"""
    sun_info = SUN_SIGN_PERSONALITY.get(context["sun_sign"], SUN_SIGN_PERSONALITY["ARIES"])
    lucky_info = ZODIAC_LUCKY_INFO.get(context["sun_sign"], ZODIAC_LUCKY_INFO["ARIES"])

    return {
        "personality": sun_info["description"],
        "strength": f"{context['sun_element_ko']} 원소가 강하여 {', '.join(sun_info['traits'][:2])}이 뛰어나요.",
        "weakness": "균형 잡힌 성장이 필요해요. 다른 원소의 특성도 발전시켜 보세요.",
        "advice": f"{context['sun_sign_ko']}인 당신은 타고난 장점을 잘 살리세요.",
        "summary": f"{context['sun_sign_ko']} 태양, {context['moon_sign_ko']} 달의 조합",
        "message": sun_info["description"]
        + f" {context['moon_sign_ko']} 달이 감정적 균형을 맞춰줘요.",
        "badges": [f"{context['sun_element']}_DOMINANT", f"{lucky_info['planet']}_STRONG"],
        "keywords": [
            {
                "code": sun_info["traits"][0].upper().replace(" ", "_"),
                "label": sun_info["traits"][0],
                "weight": 0.9,
            },
            {
                "code": sun_info["traits"][1].upper().replace(" ", "_"),
                "label": sun_info["traits"][1],
                "weight": 0.8,
            },
        ],
        "lucky": lucky_info,
    }


# ============================================================
# 메인
# ============================================================


async def main():
    parser = argparse.ArgumentParser(description="운세 캐시 데이터 생성")
    parser.add_argument("--eastern-only", action="store_true", help="동양 사주만 생성")
    parser.add_argument("--western-only", action="store_true", help="서양 점성술만 생성")
    parser.add_argument(
        "--eastern-key", type=str, help="특정 동양 사주 키만 생성 (예: GAP_WOOD_YANG)"
    )
    parser.add_argument(
        "--western-key", type=str, help="특정 서양 점성술 키만 생성 (예: ARIES_CANCER)"
    )
    parser.add_argument("--concurrency", type=int, default=3, help="병렬 처리 수 (기본: 3)")
    parser.add_argument("--vllm-url", type=str, default=VLLM_BASE_URL, help="vLLM 서버 URL")
    parser.add_argument("--model", type=str, default=VLLM_MODEL, help="모델명")
    parser.add_argument("--dry-run", action="store_true", help="실제 저장 없이 테스트")

    args = parser.parse_args()

    print("=" * 60)
    print("운세 캐시 생성 스크립트")
    print("=" * 60)
    print(f"vLLM URL: {args.vllm_url}")
    print(f"모델: {args.model}")
    print(f"병렬 처리: {args.concurrency}")
    print("=" * 60)

    start_time = datetime.now()

    # 동양 사주 캐시 생성
    if not args.western_only:
        if args.eastern_key:
            eastern_keys = [args.eastern_key]
        else:
            eastern_keys = CacheKeyBuilder.get_all_eastern_keys()

        print(f"\n[EASTERN] 생성할 키 수: {len(eastern_keys)}")

        eastern_cache = await generate_eastern_cache(
            keys=eastern_keys,
            vllm_url=args.vllm_url,
            model=args.model,
            concurrency=args.concurrency,
        )

        if not args.dry_run:
            # 기존 캐시와 병합
            if EASTERN_CACHE_PATH.exists():
                with open(EASTERN_CACHE_PATH, "r", encoding="utf-8") as f:
                    existing = json.load(f)
                    # 메타데이터 제외
                    existing = {k: v for k, v in existing.items() if not k.startswith("_")}
                    existing.update(eastern_cache)
                    eastern_cache = existing

            save_eastern_cache(eastern_cache)
            print(f"[EASTERN] 저장 완료: {len(eastern_cache)}개")
        else:
            print(f"[EASTERN] (dry-run) 생성 완료: {len(eastern_cache)}개")

    # 서양 점성술 캐시 생성
    if not args.eastern_only:
        if args.western_key:
            western_keys = [args.western_key]
        else:
            western_keys = CacheKeyBuilder.get_all_western_keys()

        print(f"\n[WESTERN] 생성할 키 수: {len(western_keys)}")

        western_cache = await generate_western_cache(
            keys=western_keys,
            vllm_url=args.vllm_url,
            model=args.model,
            concurrency=args.concurrency,
        )

        if not args.dry_run:
            # 기존 캐시와 병합
            if WESTERN_CACHE_PATH.exists():
                with open(WESTERN_CACHE_PATH, "r", encoding="utf-8") as f:
                    existing = json.load(f)
                    existing = {k: v for k, v in existing.items() if not k.startswith("_")}
                    existing.update(western_cache)
                    western_cache = existing

            save_western_cache(western_cache)
            print(f"[WESTERN] 저장 완료: {len(western_cache)}개")
        else:
            print(f"[WESTERN] (dry-run) 생성 완료: {len(western_cache)}개")

    elapsed = datetime.now() - start_time
    print("\n" + "=" * 60)
    print(f"완료! 소요 시간: {elapsed}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
