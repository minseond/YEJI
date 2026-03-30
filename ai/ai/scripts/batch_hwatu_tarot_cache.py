#!/usr/bin/env python3
"""화투/타로 캐시 일괄 생성 스크립트

병렬 비동기로 화투/타로 리딩을 생성하고 Redis에 캐싱합니다.
네트워크 협상식 동시성 제어 (Semaphore)로 LLM 서버 부하를 관리합니다.

사용법:
    # 화투 테스트 (5개)
    uv run python scripts/batch_hwatu_tarot_cache.py --type hwatu --count 5

    # 타로 테스트 (5개)
    uv run python scripts/batch_hwatu_tarot_cache.py --type tarot --count 5

    # 둘 다 (각 10개씩)
    uv run python scripts/batch_hwatu_tarot_cache.py --type both --count 10

    # 동시성 조절 (기본 2)
    uv run python scripts/batch_hwatu_tarot_cache.py --type hwatu --count 10 --concurrency 3
"""

from __future__ import annotations

import argparse
import asyncio
import random
import sys
import time
from pathlib import Path

# 프로젝트 루트 추가
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import structlog

from yeji_ai.models.fortune.hwatu import HwatuCardInput, HwatuReadingRequest
from yeji_ai.models.fortune.tarot import SpreadCardInput, TarotCardInput, TarotReadingRequest
from yeji_ai.models.enums import MajorArcana, SpreadPosition, CardOrientation
from yeji_ai.services.hwatu_service import HwatuService
from yeji_ai.services.tarot_service import TarotService
from yeji_ai.services.progressive_cache_service import (
    store_hwatu_reading_cache,
    store_tarot_reading_cache,
)

logger = structlog.get_logger()

# 질문 템플릿
HWATU_QUESTIONS = [
    "오늘 금전운이 궁금해요",
    "이번 주 연애운은 어떨까요?",
    "직장에서의 운세가 궁금합니다",
    "건강운을 봐주세요",
    "시험운이 어떨지 궁금해요",
    "사업 전망이 어떨까요?",
    "이사 운세를 봐주세요",
    "여행운이 궁금합니다",
    "대인관계 운세가 어떨까요?",
    "오늘 하루 전체 운세를 봐주세요",
]

TAROT_QUESTIONS = [
    "오늘 나의 연애운은 어떤가요?",
    "이번 달 재물운이 궁금해요",
    "직장에서 승진할 수 있을까요?",
    "건강 상태가 어떨지 봐주세요",
    "새로운 시작을 해도 될까요?",
    "현재 고민에 대한 조언이 필요해요",
    "앞으로의 인간관계가 궁금합니다",
    "학업운을 봐주세요",
    "이사를 해도 될까요?",
    "전체적인 운세 흐름이 궁금해요",
]

# 메이저 아르카나 목록
MAJOR_ARCANA_LIST = list(MajorArcana)


def generate_random_hwatu_cards() -> list[HwatuCardInput]:
    """랜덤 화투 카드 4장 생성"""
    card_codes = random.sample(range(48), 4)  # 0-47 중 4개 선택
    return [
        HwatuCardInput(
            position=i + 1,
            card_code=code,
            is_reversed=False,  # 화투는 역방향 없음
        )
        for i, code in enumerate(card_codes)
    ]


def generate_random_tarot_cards() -> list[SpreadCardInput]:
    """랜덤 타로 카드 3장 생성 (과거/현재/미래)"""
    majors = random.sample(MAJOR_ARCANA_LIST, 3)
    positions = [SpreadPosition.PAST, SpreadPosition.PRESENT, SpreadPosition.FUTURE]

    return [
        SpreadCardInput(
            position=pos,
            card=TarotCardInput(
                major=major,
                orientation=random.choice([CardOrientation.UPRIGHT, CardOrientation.REVERSED]),
            ),
        )
        for pos, major in zip(positions, majors)
    ]


async def generate_hwatu_reading(
    service: HwatuService,
    semaphore: asyncio.Semaphore,
    index: int,
) -> dict | None:
    """화투 리딩 생성 및 캐싱"""
    async with semaphore:
        question = random.choice(HWATU_QUESTIONS)
        cards = generate_random_hwatu_cards()

        request = HwatuReadingRequest(
            category="HWATU",
            question=question,
            cards=cards,
        )

        logger.info(f"[{index}] 화투 생성 시작", question=question[:20])
        start = time.time()

        try:
            response = await service.generate_reading(request)
            response_data = response.model_dump()

            # 캐시 저장
            cards_for_cache = [c.model_dump() for c in cards]
            await store_hwatu_reading_cache(question, cards_for_cache, response_data)

            elapsed = time.time() - start
            logger.info(f"[{index}] 화투 생성 완료", elapsed=f"{elapsed:.1f}s")

            return {
                "index": index,
                "type": "hwatu",
                "question": question,
                "elapsed": elapsed,
                "summary": response_data.get("summary", {}).get("overall_theme", "")[:50],
            }
        except Exception as e:
            logger.error(f"[{index}] 화투 생성 실패", error=str(e))
            return None


async def generate_tarot_reading(
    service: TarotService,
    semaphore: asyncio.Semaphore,
    index: int,
) -> dict | None:
    """타로 리딩 생성 및 캐싱"""
    async with semaphore:
        question = random.choice(TAROT_QUESTIONS)
        cards = generate_random_tarot_cards()

        request = TarotReadingRequest(
            question=question,
            cards=cards,
        )

        logger.info(f"[{index}] 타로 생성 시작", question=question[:20])
        start = time.time()

        try:
            response = await service.generate_reading(request)
            response_data = response.model_dump()

            # 캐시 저장
            cards_for_cache = [{"position": c.position.value, "card": c.card.model_dump()} for c in cards]
            await store_tarot_reading_cache(question, cards_for_cache, response_data)

            elapsed = time.time() - start
            logger.info(f"[{index}] 타로 생성 완료", elapsed=f"{elapsed:.1f}s")

            return {
                "index": index,
                "type": "tarot",
                "question": question,
                "elapsed": elapsed,
                "summary": response_data.get("summary", {}).get("overall_theme", "")[:50],
            }
        except Exception as e:
            logger.error(f"[{index}] 타로 생성 실패", error=str(e))
            return None


async def run_batch(
    batch_type: str,
    count: int,
    concurrency: int,
) -> None:
    """배치 실행"""
    semaphore = asyncio.Semaphore(concurrency)
    tasks = []
    results = []

    print(f"\n{'='*60}")
    print(f"화투/타로 캐시 일괄 생성")
    print(f"타입: {batch_type}, 개수: {count}, 동시성: {concurrency}")
    print(f"{'='*60}\n")

    start_time = time.time()

    if batch_type in ("hwatu", "both"):
        hwatu_service = HwatuService()
        await hwatu_service.initialize()

        hwatu_count = count if batch_type == "hwatu" else count // 2
        for i in range(hwatu_count):
            tasks.append(generate_hwatu_reading(hwatu_service, semaphore, i + 1))

    if batch_type in ("tarot", "both"):
        tarot_service = TarotService()
        await tarot_service.initialize()

        tarot_count = count if batch_type == "tarot" else count // 2
        offset = count // 2 if batch_type == "both" else 0
        for i in range(tarot_count):
            tasks.append(generate_tarot_reading(tarot_service, semaphore, offset + i + 1))

    # 병렬 실행
    results = await asyncio.gather(*tasks)

    total_time = time.time() - start_time

    # 결과 요약
    success_results = [r for r in results if r is not None]
    failed_count = len(results) - len(success_results)

    print(f"\n{'='*60}")
    print("결과 요약")
    print(f"{'='*60}")
    print(f"총 소요 시간: {total_time:.1f}s")
    print(f"성공: {len(success_results)}, 실패: {failed_count}")

    if success_results:
        avg_time = sum(r["elapsed"] for r in success_results) / len(success_results)
        print(f"평균 생성 시간: {avg_time:.1f}s")

        print(f"\n생성된 캐시:")
        for r in success_results:
            print(f"  [{r['type']}] {r['question'][:30]}... → {r['summary']}...")


def main():
    parser = argparse.ArgumentParser(description="화투/타로 캐시 일괄 생성")
    parser.add_argument(
        "--type",
        choices=["hwatu", "tarot", "both"],
        default="both",
        help="생성 타입 (기본: both)",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=5,
        help="생성 개수 (기본: 5)",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=2,
        help="동시성 (기본: 2)",
    )

    args = parser.parse_args()

    asyncio.run(run_batch(args.type, args.count, args.concurrency))


if __name__ == "__main__":
    main()
