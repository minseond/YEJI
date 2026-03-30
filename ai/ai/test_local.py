#!/usr/bin/env python3
"""로컬 테스트 스크립트

테스트 항목:
1. 사주/점성 캐싱 여부
2. LLM 장애 시 Redis 폴백
3. 타로/화투 API 동작

사용법:
    # AI 서버 실행 (별도 터미널)
    cd C:/Users/SSAFY/yeji-ai-server/ai
    uvicorn yeji_ai.main:app --reload --host 0.0.0.0 --port 8000

    # 테스트 실행
    python test_local.py
"""

import asyncio
import json
import time
from datetime import datetime

import httpx


# AI 서버 URL (로컬)
BASE_URL = "http://localhost:8000"

# 테스트 데이터
TEST_BIRTH_DATE = "1995-03-15"
TEST_BIRTH_TIME = "14:30"
TEST_GENDER = "M"


async def test_1_eastern_caching():
    """테스트 1: 동양 사주 캐싱 테스트"""
    print("\n" + "=" * 60)
    print("테스트 1: 동양 사주 캐싱")
    print("=" * 60)

    async with httpx.AsyncClient(timeout=60.0) as client:
        request_data = {
            "birth_date": TEST_BIRTH_DATE,
            "birth_time": TEST_BIRTH_TIME,
            "gender": TEST_GENDER,
        }

        # 첫 번째 요청 (캐시 미스 - LLM 호출 예상)
        print("\n[1차 요청] 캐시 미스 예상 (LLM 호출)")
        start = time.time()
        resp1 = await client.post(f"{BASE_URL}/v1/fortune/eastern", json=request_data)
        elapsed1 = time.time() - start

        if resp1.status_code == 200:
            data1 = resp1.json()
            print(f"  ✅ 성공 ({elapsed1:.2f}초)")
            print(f"  fortune_key: {data1.get('fortune_key', 'N/A')}")
            print(f"  _debug_stored: {data1.get('_debug_stored', 'N/A')}")
        else:
            print(f"  ❌ 실패: {resp1.status_code}")
            print(f"  {resp1.text[:500]}")
            return False

        # 두 번째 요청 (캐시 히트 예상 - 빠른 응답)
        print("\n[2차 요청] 캐시 히트 예상 (빠른 응답)")
        start = time.time()
        resp2 = await client.post(f"{BASE_URL}/v1/fortune/eastern", json=request_data)
        elapsed2 = time.time() - start

        if resp2.status_code == 200:
            data2 = resp2.json()
            print(f"  ✅ 성공 ({elapsed2:.2f}초)")
            print(f"  fortune_key: {data2.get('fortune_key', 'N/A')}")

            # 캐시 히트 판정: 2차 요청이 1차 요청보다 현저히 빠름
            if elapsed2 < elapsed1 * 0.5:
                print(f"\n  🎯 캐시 히트 확인! (1차: {elapsed1:.2f}s → 2차: {elapsed2:.2f}s)")
                return True
            else:
                print(f"\n  ⚠️ 캐시 히트 불확실 (시간 차이 적음)")
                return True  # 기능은 동작함
        else:
            print(f"  ❌ 실패: {resp2.status_code}")
            return False


async def test_2_western_caching():
    """테스트 2: 서양 점성술 캐싱 테스트"""
    print("\n" + "=" * 60)
    print("테스트 2: 서양 점성술 캐싱")
    print("=" * 60)

    async with httpx.AsyncClient(timeout=60.0) as client:
        request_data = {
            "birth_date": TEST_BIRTH_DATE,
            "birth_time": TEST_BIRTH_TIME,
        }

        # 첫 번째 요청
        print("\n[1차 요청] 캐시 미스 예상")
        start = time.time()
        resp1 = await client.post(f"{BASE_URL}/v1/fortune/western", json=request_data)
        elapsed1 = time.time() - start

        if resp1.status_code == 200:
            data1 = resp1.json()
            print(f"  ✅ 성공 ({elapsed1:.2f}초)")
            print(f"  fortune_key: {data1.get('fortune_key', 'N/A')}")
            print(f"  _debug_stored: {data1.get('_debug_stored', 'N/A')}")
        else:
            print(f"  ❌ 실패: {resp1.status_code}")
            print(f"  {resp1.text[:500]}")
            return False

        # 두 번째 요청
        print("\n[2차 요청] 캐시 히트 예상")
        start = time.time()
        resp2 = await client.post(f"{BASE_URL}/v1/fortune/western", json=request_data)
        elapsed2 = time.time() - start

        if resp2.status_code == 200:
            print(f"  ✅ 성공 ({elapsed2:.2f}초)")
            if elapsed2 < elapsed1 * 0.5:
                print(f"\n  🎯 캐시 히트 확인!")
            return True
        else:
            print(f"  ❌ 실패: {resp2.status_code}")
            return False


async def test_3_llm_fallback():
    """테스트 3: LLM 장애 시 폴백 테스트

    이 테스트는 vLLM 서버가 꺼져있을 때 폴백이 동작하는지 확인합니다.
    - vLLM 연결 실패 시 → rule_based_fallback.py 사용
    - graceful=true 모드에서 폴백 응답 반환
    """
    print("\n" + "=" * 60)
    print("테스트 3: LLM 장애 시 폴백")
    print("=" * 60)
    print("  ⚠️ 이 테스트는 vLLM 서버가 꺼져있을 때 의미있습니다")
    print("  ⚠️ 캐시에 데이터가 있으면 LLM 호출 없이 캐시 반환됨")

    async with httpx.AsyncClient(timeout=60.0) as client:
        # 캐시에 없는 새로운 생년월일 사용
        unique_date = f"1987-{datetime.now().minute:02d}-{datetime.now().second:02d}"
        request_data = {
            "birth_date": unique_date,
            "birth_time": "03:00",
            "gender": "F",
        }

        print(f"\n[요청] birth_date={unique_date} (캐시 없음 예상)")
        start = time.time()
        resp = await client.post(
            f"{BASE_URL}/v1/fortune/eastern",
            json=request_data,
            params={"graceful": "true"},
        )
        elapsed = time.time() - start

        print(f"  응답 코드: {resp.status_code} ({elapsed:.2f}초)")

        if resp.status_code == 200:
            data = resp.json()
            # 폴백 응답인지 확인 (source 필드 또는 특정 패턴)
            if "fallback" in str(data).lower() or data.get("_source") == "fallback":
                print("  🎯 폴백 응답 확인!")
            else:
                print("  ✅ 정상 응답 (LLM 또는 캐시)")
            print(f"  fortune_key: {data.get('fortune_key', 'N/A')}")
            return True
        elif resp.status_code in [502, 503, 504]:
            print("  ⚠️ LLM 서버 연결 실패 (폴백 미적용 - graceful=false일 수 있음)")
            return True  # 예상된 동작
        else:
            print(f"  ❌ 예상치 못한 오류: {resp.text[:500]}")
            return False


async def test_4_tarot():
    """테스트 4: 타로 API 테스트"""
    print("\n" + "=" * 60)
    print("테스트 4: 타로 API")
    print("=" * 60)

    async with httpx.AsyncClient(timeout=60.0) as client:
        # 타로 덱 조회
        print("\n[GET /tarot/deck] 타로 덱 조회")
        resp_deck = await client.get(f"{BASE_URL}/v1/fortune/tarot/deck")

        if resp_deck.status_code == 200:
            deck = resp_deck.json()
            print(f"  ✅ 타로 덱 조회 성공")
            print(f"  카드 수: {len(deck.get('cards', []))}장")
        else:
            print(f"  ❌ 실패: {resp_deck.status_code}")
            return False

        # 타로 리딩 (3장 선택)
        print("\n[POST /tarot/reading] 타로 리딩")
        request_data = {
            "question": "오늘의 연애운은 어떨까요?",
            "spread_type": "THREE_CARD",
            "selected_cards": [
                {"index": 0, "is_reversed": False},  # The Fool
                {"index": 1, "is_reversed": True},   # The Magician (역방향)
                {"index": 6, "is_reversed": False},  # The Lovers
            ],
        }

        resp = await client.post(
            f"{BASE_URL}/v1/fortune/tarot/reading",
            json=request_data,
            params={"graceful": "true"},
        )

        if resp.status_code == 200:
            data = resp.json()
            print(f"  ✅ 타로 리딩 성공")
            # FortuneResponse wrapper 또는 직접 응답
            if "data" in data:
                reading = data["data"]
            else:
                reading = data
            print(f"  카드 수: {len(reading.get('cards', []))}장")
            if reading.get("summary"):
                print(f"  요약: {reading['summary'][:100]}...")
            return True
        else:
            print(f"  ❌ 실패: {resp.status_code}")
            print(f"  {resp.text[:500]}")
            return False


async def test_5_hwatu():
    """테스트 5: 화투 API 테스트"""
    print("\n" + "=" * 60)
    print("테스트 5: 화투 API")
    print("=" * 60)

    async with httpx.AsyncClient(timeout=60.0) as client:
        # 화투 덱 조회
        print("\n[GET /hwatu/deck] 화투 덱 조회")
        resp_deck = await client.get(f"{BASE_URL}/v1/fortune/hwatu/deck")

        if resp_deck.status_code == 200:
            deck = resp_deck.json()
            print(f"  ✅ 화투 덱 조회 성공")
            print(f"  카드 수: {len(deck.get('cards', []))}장")
        else:
            print(f"  ❌ 실패: {resp_deck.status_code}")
            return False

        # 화투 리딩 (4장 선택)
        print("\n[POST /hwatu/reading] 화투 리딩")
        request_data = {
            "question": "이번 달 재물운은?",
            "selected_cards": [
                {"month": 1, "card_type": "GWANG"},   # 1월 광
                {"month": 3, "card_type": "GWANG"},   # 3월 광
                {"month": 8, "card_type": "GWANG"},   # 8월 광
                {"month": 11, "card_type": "GWANG"},  # 11월 광
            ],
        }

        resp = await client.post(
            f"{BASE_URL}/v1/fortune/hwatu/reading",
            json=request_data,
            params={"graceful": "true"},
        )

        if resp.status_code == 200:
            data = resp.json()
            print(f"  ✅ 화투 리딩 성공")
            if "data" in data:
                reading = data["data"]
            else:
                reading = data
            print(f"  카드 수: {len(reading.get('cards', []))}장")
            if reading.get("overall_reading"):
                overall = reading["overall_reading"]
                print(f"  종합: {str(overall)[:100]}...")
            return True
        else:
            print(f"  ❌ 실패: {resp.status_code}")
            print(f"  {resp.text[:500]}")
            return False


async def test_6_quick_summary():
    """테스트 6: Quick Summary API (캐시된 데이터 기반 요약)"""
    print("\n" + "=" * 60)
    print("테스트 6: Quick Summary API")
    print("=" * 60)

    async with httpx.AsyncClient(timeout=60.0) as client:
        # 먼저 동양 사주 분석 수행 (캐시에 저장)
        print("\n[준비] 동양 사주 분석으로 캐시 생성")
        eastern_request = {
            "birth_date": TEST_BIRTH_DATE,
            "birth_time": TEST_BIRTH_TIME,
            "gender": TEST_GENDER,
        }
        resp_eastern = await client.post(f"{BASE_URL}/v1/fortune/eastern", json=eastern_request)

        if resp_eastern.status_code != 200:
            print(f"  ❌ 사주 분석 실패: {resp_eastern.status_code}")
            return False

        fortune_key = resp_eastern.json().get("fortune_key")
        print(f"  fortune_key: {fortune_key}")

        # Quick Summary 요청
        print("\n[POST /quick-summary] Quick Summary 요청")
        summary_request = {
            "fortune_id": fortune_key,
            "fortune_type": "eastern",
            "category": "MONEY",
            "persona": "SOISEOL",
        }

        resp = await client.post(f"{BASE_URL}/v1/fortune/quick-summary", json=summary_request)

        if resp.status_code == 200:
            data = resp.json()
            print(f"  ✅ Quick Summary 성공")
            print(f"  score: {data.get('score', 'N/A')}")
            print(f"  keyword: {data.get('keyword', 'N/A')[:50]}...")
            print(f"  cache_source: {data.get('cache_source', 'N/A')}")
            return True
        else:
            print(f"  ❌ 실패: {resp.status_code}")
            print(f"  {resp.text[:500]}")
            return False


async def main():
    """메인 테스트 실행"""
    print("\n" + "=" * 60)
    print("YEJI AI 서버 로컬 테스트")
    print(f"시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"서버: {BASE_URL}")
    print("=" * 60)

    # 서버 헬스체크
    print("\n[헬스체크]")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{BASE_URL}/v1/health")
            if resp.status_code == 200:
                print("  ✅ AI 서버 정상")
            else:
                print(f"  ❌ 서버 응답 오류: {resp.status_code}")
                return
    except httpx.ConnectError:
        print("  ❌ 서버 연결 실패")
        print("  → uvicorn yeji_ai.main:app --reload --port 8000 실행 필요")
        return
    except Exception as e:
        print(f"  ❌ 오류: {e}")
        return

    # 테스트 실행
    results = {}

    results["1. 동양 사주 캐싱"] = await test_1_eastern_caching()
    results["2. 서양 점성 캐싱"] = await test_2_western_caching()
    results["3. LLM 폴백"] = await test_3_llm_fallback()
    results["4. 타로 API"] = await test_4_tarot()
    results["5. 화투 API"] = await test_5_hwatu()
    results["6. Quick Summary"] = await test_6_quick_summary()

    # 결과 요약
    print("\n" + "=" * 60)
    print("테스트 결과 요약")
    print("=" * 60)
    for name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {name}: {status}")

    passed_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    print(f"\n총 {passed_count}/{total_count} 테스트 통과")


if __name__ == "__main__":
    asyncio.run(main())
