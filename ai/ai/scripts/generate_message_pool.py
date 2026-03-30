#!/usr/bin/env python3
"""궁합 메시지 풀 생성 스크립트

점수 구간별로 다양한 메시지를 미리 생성하여 JSON 파일로 저장합니다.
런타임에는 점수 계산 → 해당 구간에서 랜덤 선택하는 방식으로 사용합니다.

사용법:
    # 1. 테스트 (한 구간만 10개 생성)
    uv run python scripts/generate_message_pool.py --test

    # 2. 전체 생성 (5구간 × 200개 = 1000개)
    uv run python scripts/generate_message_pool.py --generate --count 200

    # 3. vLLM 사용 (AWS 서버)
    uv run python scripts/generate_message_pool.py --test --provider vllm

    # 4. GPT-5 Mini 사용
    uv run python scripts/generate_message_pool.py --test --provider openai
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import random
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

import httpx

# 프로젝트 루트
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# .env 로드
def load_env():
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ.setdefault(key.strip(), value.strip())

load_env()

# ============================================================
# 설정
# ============================================================

# 동시 요청 설정
MAX_CONCURRENT_REQUESTS = 10  # 동시 API 호출 수
TEMPLATES_PER_REQUEST = 10    # 한 번 호출에 생성할 템플릿 수 (20개는 토큰 초과)
# 구간당 200개 = 20개씩 × 10번 동시 호출

# OpenAI (GPT-5 Mini)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5-mini")

# vLLM (AWS)
VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", "http://localhost:8001")
VLLM_MODEL = os.getenv("VLLM_MODEL", "tellang/yeji-8b-rslora-v7")

# 점수 구간 정의
SCORE_RANGES = [
    ("excellent", 90, 100, "천생연분"),
    ("good", 70, 89, "좋은 궁합"),
    ("average", 50, 69, "보통"),
    ("challenging", 30, 49, "노력 필요"),
    ("difficult", 0, 29, "상극"),
]

# 오행 조합
ELEMENT_PAIRS = [
    ("WOOD", "WOOD", "비화", "같은 목 기운이 만나 숲을 이룹니다"),
    ("WOOD", "FIRE", "상생", "목생화 - 나무가 불을 살립니다"),
    ("WOOD", "EARTH", "상극", "목극토 - 나무가 흙을 뚫습니다"),
    ("WOOD", "METAL", "상극", "금극목 - 쇠가 나무를 베어냅니다"),
    ("WOOD", "WATER", "상생", "수생목 - 물이 나무를 기릅니다"),
    ("FIRE", "FIRE", "비화", "같은 화 기운이 만나 열정이 넘칩니다"),
    ("FIRE", "EARTH", "상생", "화생토 - 불이 흙을 만듭니다"),
    ("FIRE", "METAL", "상극", "화극금 - 불이 쇠를 녹입니다"),
    ("FIRE", "WATER", "상극", "수극화 - 물이 불을 끕니다"),
    ("EARTH", "EARTH", "비화", "같은 토 기운이 만나 안정됩니다"),
    ("EARTH", "METAL", "상생", "토생금 - 흙에서 쇠가 납니다"),
    ("EARTH", "WATER", "상극", "토극수 - 흙이 물길을 막습니다"),
    ("METAL", "METAL", "비화", "같은 금 기운이 만나 단단해집니다"),
    ("METAL", "WATER", "상생", "금생수 - 쇠에서 물이 맺힙니다"),
    ("WATER", "WATER", "비화", "같은 수 기운이 만나 깊어집니다"),
]

# 별자리 원소 조합
ZODIAC_ELEMENT_PAIRS = [
    ("FIRE", "FIRE", "열정적 조합"),
    ("FIRE", "EARTH", "현실과 이상"),
    ("FIRE", "AIR", "환상의 조합"),
    ("FIRE", "WATER", "긴장과 매력"),
    ("EARTH", "EARTH", "안정적 조합"),
    ("EARTH", "AIR", "다른 세계"),
    ("EARTH", "WATER", "조화로운 조합"),
    ("AIR", "AIR", "지적 교류"),
    ("AIR", "WATER", "감성과 이성"),
    ("WATER", "WATER", "깊은 공감"),
]

# ============================================================
# 프롬프트
# ============================================================

SYSTEM_PROMPT_BATCH = """당신은 동양 사주와 서양 점성술에 정통한 궁합 전문가입니다.

<task>
주어진 점수 구간에 맞는 궁합 응답 템플릿을 {count}개 생성해주세요.
</task>

<output_format>
정확히 아래 JSON 구조의 배열로 출력하세요:
{{
  "templates": [
    {{
      "east": {{
        "relationship_dynamics": {{
          "communication": {{ "desc": "소통 설명 2문장" }},
          "flexibility": {{ "desc": "유연성 설명 2문장" }},
          "stability": {{ "desc": "안정성 설명 2문장" }},
          "passion": {{ "desc": "열정 설명 2문장" }},
          "growth": {{ "desc": "성장 설명 2문장" }}
        }},
        "compatibility_summary": {{
          "keywords": ["사자성어1", "사자성어2"],
          "desc": "종합 설명 2-3문장"
        }}
      }},
      "west": {{
        "zodiac": {{
          "aspects": {{
            "moon_resonance": {{ "title": "감정 공명", "desc": "2문장" }},
            "mercury_communication": {{ "title": "의사소통 스타일", "desc": "2문장" }},
            "venus_mars_values": {{ "title": "가치관과 애정 표현", "desc": "2문장" }},
            "saturn_stability": {{ "title": "장기적 안정성", "desc": "2문장" }}
          }}
        }},
        "numerology": {{
          "life_path": {{ "title": "인생의 경로", "desc": "2문장" }},
          "destiny": {{ "title": "운명 수", "desc": "2문장" }},
          "complement": {{ "title": "성격적 보완", "desc": "2문장" }}
        }}
      }}
    }}
  ]
}}
</output_format>

<rules>
1. 모든 텍스트는 한국어로 작성
2. keywords는 점수 구간에 맞는 사자성어 2개
   - 높은 점수(80+): 천생연분, 금슬지락, 백년해로, 이심전심, 비익연리, 일심동체, 부창부수
   - 보통 점수(60-79): 상부상조, 동고동락, 동병상련, 마음합일, 화기애애, 심심상인
   - 낮은 점수(-59): 역지사지, 화이부동, 대기만성, 고진감래, 전화위복, 새옹지마
3. 친근하고 따뜻한 어조 (~해요, ~입니다, ~좋아요, ~될 수 있어요)
4. 구체적이고 실용적인 조언 포함
5. 각 템플릿은 서로 다른 표현으로 작성 (다양성 매우 중요!)
6. title 필드도 다양하게 (예: "감정 공명", "마음의 파장", "정서적 교감" 등)
</rules>"""

USER_PROMPT_BATCH = """점수 구간: {score_min}~{score_max}점 ({grade})

⚠️ 중요: templates 배열에 정확히 {count}개의 템플릿을 생성하세요!

요구사항:
1. templates 배열에 {count}개 생성 (1개가 아님!)
2. 각 템플릿은 서로 다른 표현 사용
3. 다양한 사자성어 조합 사용
4. 모든 desc 필드 채우기

JSON 형식: {{"templates": [템플릿1, 템플릿2, ..., 템플릿{count}]}}"""

# ============================================================
# API 호출
# ============================================================

async def call_openai(
    system_prompt: str,
    user_prompt: str,
    client: httpx.AsyncClient,
) -> list[dict] | None:
    """GPT-5 Mini API 호출 (한 번에 여러 개 생성)"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}",
    }

    payload = {
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_completion_tokens": 16000,
        "response_format": {"type": "json_object"},
    }

    try:
        response = await client.post(
            f"{OPENAI_BASE_URL}/chat/completions",
            json=payload,
            headers=headers,
            timeout=600.0,  # 10분 타임아웃 (200개 배치용)
        )
        response.raise_for_status()

        data = response.json()
        choice = data["choices"][0]
        content = choice["message"]["content"]

        # 빈 응답 체크
        if not content or not content.strip():
            finish_reason = choice.get("finish_reason", "unknown")
            print(f"  [WARNING] 빈 응답 (finish_reason: {finish_reason})")
            return None

        # JSON 파싱
        result = json.loads(content)

        # templates 배열 추출
        if isinstance(result, dict) and "templates" in result:
            return result["templates"]
        elif isinstance(result, list):
            return result
        elif isinstance(result, dict):
            return [result]

        return None

    except Exception as e:
        print(f"  [ERROR] OpenAI API 실패: {e}")
        import traceback
        traceback.print_exc()
        return None


async def call_vllm(
    system_prompt: str,
    user_prompt: str,
    client: httpx.AsyncClient,
) -> list[dict] | None:
    """vLLM API 호출 (AWS 서버)"""
    payload = {
        "model": VLLM_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": 2500,  # 4096 - 입력토큰 여유분
        "temperature": 0.8,
    }

    try:
        response = await client.post(
            f"{VLLM_BASE_URL}/v1/chat/completions",
            json=payload,
            timeout=300.0,  # 5분 타임아웃
        )
        response.raise_for_status()

        data = response.json()
        content = data["choices"][0]["message"]["content"]

        print(f"  [DEBUG] Raw content (first 500 chars): {content[:500]}")

        # JSON 파싱 - vLLM은 종종 ```json 블록으로 감싸서 응답
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        result = json.loads(content)

        # templates 배열 추출
        if isinstance(result, dict) and "templates" in result:
            return result["templates"]
        elif isinstance(result, list):
            return result
        elif isinstance(result, dict):
            return [result]

        return None

    except httpx.HTTPStatusError as e:
        print(f"  [ERROR] vLLM API 실패: {e}")
        print(f"  Response: {e.response.text[:1000]}")
        return None
    except Exception as e:
        print(f"  [ERROR] vLLM API 실패: {e}")
        import traceback
        traceback.print_exc()
        return None


# ============================================================
# 메시지 풀 생성
# ============================================================

async def generate_messages_for_range(
    score_range: tuple[str, int, int, str],
    count: int,
    provider: Literal["openai", "vllm"],
    client: httpx.AsyncClient,
) -> list[dict]:
    """특정 점수 구간의 메시지 생성"""
    range_id, score_min, score_max, grade = score_range

    print(f"\n[{grade}] ({score_min}-{score_max}점) 메시지 {count}개 생성 중...")

    system_prompt = SYSTEM_PROMPT_BATCH.format(count=count)
    user_prompt = USER_PROMPT_BATCH.format(
        score_min=score_min,
        score_max=score_max,
        grade=grade,
        count=count,
    )

    if provider == "openai":
        messages = await call_openai(system_prompt, user_prompt, client)
    else:
        messages = await call_vllm(system_prompt, user_prompt, client)

    if messages:
        print(f"  → {len(messages)}개 생성 완료")
        # range_id 추가
        for msg in messages:
            msg["score_range"] = range_id
        return messages
    else:
        print(f"  → 생성 실패")
        return []


async def generate_single_batch(
    score_range: tuple,
    batch_num: int,
    provider: str,
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
) -> list[dict]:
    """단일 배치 생성 (Semaphore로 동시 요청 제한)"""
    async with semaphore:
        messages = await generate_messages_for_range(
            score_range, TEMPLATES_PER_REQUEST, provider, client
        )
        return messages or []


async def generate_for_single_range(
    score_range: tuple,
    count: int,
    provider: str,
    batch_size: int,
    client: httpx.AsyncClient,
    checkpoint_dir: Path | None = None,
) -> tuple[str, list[dict]]:
    """단일 점수 구간의 메시지 생성 (동시 요청)"""
    range_id = score_range[0]
    grade = score_range[3]
    messages = []

    # 체크포인트에서 복구
    checkpoint_file = None
    if checkpoint_dir:
        checkpoint_file = checkpoint_dir / f"{range_id}_checkpoint.json"
        if checkpoint_file.exists():
            with open(checkpoint_file, "r", encoding="utf-8") as f:
                checkpoint_data = json.load(f)
                messages = checkpoint_data.get("messages", [])
                print(f"  [{grade}] 체크포인트 복구: {len(messages)}개")

    remaining = count - len(messages)
    total = count

    # 필요한 배치 수 계산
    num_batches = (remaining + TEMPLATES_PER_REQUEST - 1) // TEMPLATES_PER_REQUEST

    if num_batches > 0:
        print(f"  [{grade}] {num_batches}개 배치 동시 요청 중... (각 {TEMPLATES_PER_REQUEST}개씩)")

        # Semaphore로 동시 요청 제한
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

        # 모든 배치 동시 실행
        tasks = [
            generate_single_batch(score_range, i, provider, client, semaphore)
            for i in range(num_batches)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 결과 수집
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"  [{grade}] 배치 {i+1} 실패: {result}")
            elif result:
                messages.extend(result)
                # 진행도 출력
                progress = len(messages) / total * 100
                print(f"  [{grade}] {len(messages)}/{total} ({progress:.0f}%)")

        # 체크포인트 저장
        if checkpoint_file:
            with open(checkpoint_file, "w", encoding="utf-8") as f:
                json.dump({"messages": messages, "count": count}, f, ensure_ascii=False)

    # 완료 시 체크포인트 삭제
    if checkpoint_file and checkpoint_file.exists():
        checkpoint_file.unlink()

    print(f"  [{grade}] ✅ 완료! {len(messages)}개 생성")
    return range_id, messages


async def generate_full_pool(
    count_per_range: int,
    provider: Literal["openai", "vllm"],
    batch_size: int = 200,  # GPT-5 Mini 최대 배치
    parallel: bool = True,  # 병렬 실행 여부
    checkpoint_dir: Path | None = None,  # 체크포인트 디렉토리
) -> dict[str, list[dict]]:
    """전체 메시지 풀 생성 (병렬 배치)"""
    pool = {r[0]: [] for r in SCORE_RANGES}

    # 체크포인트 디렉토리 생성
    if checkpoint_dir:
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        print(f"[체크포인트] {checkpoint_dir}")

    async with httpx.AsyncClient() as client:
        if parallel:
            # 5개 구간 병렬 실행
            print(f"[병렬 모드] 5개 구간 동시 생성 중...")
            tasks = [
                generate_for_single_range(sr, count_per_range, provider, batch_size, client, checkpoint_dir)
                for sr in SCORE_RANGES
            ]
            results = await asyncio.gather(*tasks)

            for range_id, messages in results:
                pool[range_id] = messages
        else:
            # 순차 실행 (기존 방식)
            for score_range in SCORE_RANGES:
                range_id = score_range[0]
                remaining = count_per_range

                while remaining > 0:
                    batch = min(batch_size, remaining)
                    messages = await generate_messages_for_range(
                        score_range, batch, provider, client
                    )
                    pool[range_id].extend(messages)
                    remaining -= len(messages)

                    if len(messages) < batch:
                        print(f"  [WARNING] 배치 실패, 재시도...")
                        await asyncio.sleep(1)

    return pool


# ============================================================
# 메인
# ============================================================

async def run_test(provider: str):
    """테스트 실행 (한 구간만 10개)"""
    print("=" * 60)
    print(f"메시지 풀 생성 테스트 (Provider: {provider})")
    print("=" * 60)

    if provider == "openai" and not OPENAI_API_KEY:
        print("[ERROR] OPENAI_API_KEY가 설정되지 않았습니다.")
        return

    # 첫 번째 구간(천생연분)으로 테스트
    test_range = SCORE_RANGES[0]  # excellent (90-100)

    async with httpx.AsyncClient() as client:
        messages = await generate_messages_for_range(
            test_range,
            count=5,  # 테스트니까 5개만
            provider=provider,
            client=client,
        )

    if messages:
        print("\n[생성된 메시지]")
        print(json.dumps(messages, ensure_ascii=False, indent=2))

        print("\n[품질 체크]")
        for i, msg in enumerate(messages, 1):
            keywords = msg.get("keywords", [])
            print(f"{i}. keywords: {keywords}")
    else:
        print("\n[ERROR] 메시지 생성 실패")


async def run_generate(count: int, provider: str, output: str):
    """전체 메시지 풀 생성"""
    print("=" * 60)
    print(f"메시지 풀 생성 (Provider: {provider}, 구간당 {count}개)")
    print("=" * 60)

    start_time = datetime.now()

    # 체크포인트 디렉토리
    output_path = Path(output)
    checkpoint_dir = output_path.parent / ".checkpoints"

    pool = await generate_full_pool(
        count_per_range=count,
        provider=provider,
        checkpoint_dir=checkpoint_dir,
    )

    elapsed = datetime.now() - start_time

    # 통계
    total = sum(len(v) for v in pool.values())
    print(f"\n[완료] 총 {total}개 메시지 생성 (소요 시간: {elapsed})")

    for range_id, messages in pool.items():
        print(f"  - {range_id}: {len(messages)}개")

    # 저장
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "generated_at": datetime.now().isoformat(),
            "provider": provider,
            "total_count": total,
            "pool": pool,
        }, f, ensure_ascii=False, indent=2)

    print(f"\n[저장됨] {output_path}")


def main():
    parser = argparse.ArgumentParser(description="궁합 메시지 풀 생성")

    parser.add_argument("--test", action="store_true", help="테스트 실행")
    parser.add_argument("--generate", action="store_true", help="전체 생성")
    parser.add_argument("--count", type=int, default=200, help="구간당 생성 개수")
    parser.add_argument("--provider", choices=["openai", "vllm"], default="openai", help="LLM Provider")
    parser.add_argument("--output", "-o", default="data/message_pool.json", help="출력 파일")

    args = parser.parse_args()

    if args.test:
        asyncio.run(run_test(args.provider))
    elif args.generate:
        asyncio.run(run_generate(args.count, args.provider, args.output))
    else:
        # 기본은 테스트
        asyncio.run(run_test(args.provider))


if __name__ == "__main__":
    main()
