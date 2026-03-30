#!/usr/bin/env python3
"""Quick Summary 일괄 캐싱 스크립트

기존 Fortune 캐시를 순회하며 Quick Summary 캐시를 일괄 생성합니다.

사용법:
    # 로컬에서 dev 서버 대상 실행
    python scripts/batch_quick_summary_cache.py --api-base https://i14a605.p.ssafy.io/ai-dev

    # dry-run (실제 호출 없이 대상만 확인)
    python scripts/batch_quick_summary_cache.py --dry-run

    # 특정 타입만 처리
    python scripts/batch_quick_summary_cache.py --type eastern
    python scripts/batch_quick_summary_cache.py --type western
"""

from __future__ import annotations

import argparse
import asyncio
import re
import sys
from dataclasses import dataclass
from typing import Literal

import httpx

# 카테고리 목록
CATEGORIES = ["GENERAL", "LOVE", "MONEY", "CAREER", "HEALTH"]

# Fortune 키 패턴
# Eastern: fortune:eastern:YYYY-MM-DD:HHMM:M/F 또는 fortune:eastern:YYYY-MM-DD:HH:MM:M/F
# Western: fortune:western:YYYY-MM-DD:HHMM 또는 fortune:western:YYYY-MM-DD:HH:MM
EASTERN_PATTERN = re.compile(r"^fortune:eastern:(\d{4}-\d{2}-\d{2}:\d{2}:?\d{2}:[MF])$")
WESTERN_PATTERN = re.compile(r"^fortune:western:(\d{4}-\d{2}-\d{2}:\d{2}:?\d{2})$")


@dataclass
class FortuneKey:
    """Fortune 키 정보"""
    fortune_type: Literal["eastern", "western"]
    fortune_id: str  # "eastern:YYYY-MM-DD:HHMM:M" 또는 "western:YYYY-MM-DD:HHMM"
    raw_key: str


def parse_fortune_key(redis_key: str) -> FortuneKey | None:
    """Redis 키를 파싱하여 FortuneKey 반환

    Args:
        redis_key: fortune:eastern:1990-05-15:1430:M 형태의 키

    Returns:
        FortuneKey 또는 None (파싱 실패 시)
    """
    # 테스트/디버그 키 제외
    if "test" in redis_key or "debug" in redis_key:
        return None

    # Eastern 패턴 매칭
    if redis_key.startswith("fortune:eastern:"):
        match = EASTERN_PATTERN.match(redis_key)
        if match:
            fortune_id = f"eastern:{match.group(1)}"
            return FortuneKey(
                fortune_type="eastern",
                fortune_id=fortune_id,
                raw_key=redis_key,
            )

    # Western 패턴 매칭
    if redis_key.startswith("fortune:western:"):
        match = WESTERN_PATTERN.match(redis_key)
        if match:
            fortune_id = f"western:{match.group(1)}"
            return FortuneKey(
                fortune_type="western",
                fortune_id=fortune_id,
                raw_key=redis_key,
            )

    return None


async def call_quick_summary(
    client: httpx.AsyncClient,
    api_base: str,
    fortune_key: FortuneKey,
    category: str,
) -> tuple[bool, str]:
    """Quick Summary API 호출

    Returns:
        (성공여부, 메시지)
    """
    url = f"{api_base}/v1/fortune/quick-summary"
    payload = {
        "fortune_id": fortune_key.fortune_id,
        "fortune_type": fortune_key.fortune_type,
        "category": category,
    }

    try:
        response = await client.post(url, json=payload, timeout=30.0)
        if response.status_code == 200:
            data = response.json()
            cache_source = data.get("cache_source", "unknown")
            return True, f"✅ {cache_source}"
        else:
            return False, f"❌ HTTP {response.status_code}"
    except httpx.TimeoutException:
        return False, "❌ Timeout"
    except Exception as e:
        return False, f"❌ {type(e).__name__}: {e}"


async def process_fortune_key(
    client: httpx.AsyncClient,
    api_base: str,
    fortune_key: FortuneKey,
    categories: list[str],
    dry_run: bool = False,
) -> dict[str, bool]:
    """하나의 Fortune 키에 대해 모든 카테고리 처리

    Returns:
        {category: success} 딕셔너리
    """
    results = {}

    for category in categories:
        if dry_run:
            print(f"  [DRY-RUN] {fortune_key.fortune_id} / {category}")
            results[category] = True
            continue

        success, msg = await call_quick_summary(client, api_base, fortune_key, category)
        results[category] = success
        status = "✅" if success else "❌"
        print(f"  {status} {category}: {msg}")

        # Rate limiting - 100ms 간격
        await asyncio.sleep(0.1)

    return results


async def get_fortune_keys_from_redis(redis_host: str = "localhost", redis_port: int = 6379) -> list[str]:
    """Redis에서 fortune:* 키 목록 조회 (SSH 터널 또는 직접 연결)"""
    # 여기서는 명령줄에서 키 목록을 전달받는 방식 사용
    # 실제 사용 시 redis-py 사용 가능
    raise NotImplementedError("Redis 직접 연결은 구현되지 않음. --keys 옵션으로 키 전달 필요")


async def main():
    parser = argparse.ArgumentParser(description="Quick Summary 일괄 캐싱")
    parser.add_argument(
        "--api-base",
        default="https://i14a605.p.ssafy.io/ai-dev",
        help="API 서버 베이스 URL",
    )
    parser.add_argument(
        "--type",
        choices=["eastern", "western", "all"],
        default="all",
        help="처리할 운세 타입",
    )
    parser.add_argument(
        "--categories",
        nargs="+",
        choices=CATEGORIES,
        default=CATEGORIES,
        help="처리할 카테고리 목록",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="실제 API 호출 없이 대상만 확인",
    )
    parser.add_argument(
        "--keys",
        nargs="*",
        help="처리할 fortune 키 목록 (없으면 stdin에서 읽음)",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=3,
        help="동시 처리 수 (기본값: 3)",
    )

    args = parser.parse_args()

    # 키 목록 가져오기
    if args.keys:
        raw_keys = args.keys
    else:
        # stdin에서 읽기
        print("📥 stdin에서 fortune 키 목록을 읽습니다...")
        raw_keys = [line.strip() for line in sys.stdin if line.strip()]

    if not raw_keys:
        print("❌ 처리할 키가 없습니다.")
        print("사용법: redis-cli --scan --pattern 'fortune:*' | python batch_quick_summary_cache.py")
        sys.exit(1)

    # 키 파싱
    fortune_keys: list[FortuneKey] = []
    for raw_key in raw_keys:
        parsed = parse_fortune_key(raw_key)
        if parsed:
            if args.type == "all" or parsed.fortune_type == args.type:
                fortune_keys.append(parsed)

    print(f"\n🎯 처리 대상: {len(fortune_keys)}개 fortune 키")
    print(f"📂 카테고리: {args.categories}")
    print(f"🔗 API: {args.api_base}")
    print(f"🔄 총 호출 예상: {len(fortune_keys) * len(args.categories)}회")

    if args.dry_run:
        print("\n⚠️  DRY-RUN 모드 - 실제 API 호출 없음\n")

    print("-" * 60)

    # 처리
    success_count = 0
    fail_count = 0

    async with httpx.AsyncClient() as client:
        for i, fortune_key in enumerate(fortune_keys, 1):
            print(f"\n[{i}/{len(fortune_keys)}] {fortune_key.fortune_id}")

            results = await process_fortune_key(
                client=client,
                api_base=args.api_base,
                fortune_key=fortune_key,
                categories=args.categories,
                dry_run=args.dry_run,
            )

            success_count += sum(1 for v in results.values() if v)
            fail_count += sum(1 for v in results.values() if not v)

    # 결과 요약
    print("\n" + "=" * 60)
    print("📊 결과 요약")
    print("=" * 60)
    print(f"  ✅ 성공: {success_count}")
    print(f"  ❌ 실패: {fail_count}")
    print(f"  📦 총 처리: {success_count + fail_count}")

    if fail_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
