#!/usr/bin/env python3
"""vLLM guided_json 지원 여부 테스트 스크립트

vLLM 서버의 json_schema response_format 지원 여부를 테스트합니다.

사용법:
    python scripts/test_guided_json.py
    python scripts/test_guided_json.py --url http://localhost:8001
"""

import asyncio
import json
import argparse
import sys

import httpx


# 기본 설정
DEFAULT_VLLM_URL = "http://13.125.68.166:8001/v1/chat/completions"
DEFAULT_MODEL = "tellang/yeji-8b-rslora-v7-AWQ"


async def test_json_schema_support(url: str, model: str) -> bool:
    """json_schema response_format 테스트

    Args:
        url: vLLM 서버 URL
        model: 모델 이름

    Returns:
        지원 여부 (True/False)
    """
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
            "city": {"type": "string"},
        },
        "required": ["name", "age", "city"],
    }

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": "Generate a person with name, age, and city.",
            }
        ],
        "max_tokens": 200,
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": "person", "schema": schema, "strict": True},
        },
    }

    print("=" * 60)
    print("테스트: json_schema response_format")
    print("=" * 60)
    print(f"URL: {url}")
    print(f"모델: {model}")
    print()

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(url, json=payload)
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                print("[SUCCESS] json_schema 지원됨!")
                print(f"응답: {content}")

                # JSON 파싱 테스트
                try:
                    parsed = json.loads(content)
                    print(f"파싱된 데이터: {json.dumps(parsed, ensure_ascii=False, indent=2)}")

                    # 필수 필드 확인
                    for field in ["name", "age", "city"]:
                        if field in parsed:
                            print(f"  [OK] {field}: {parsed[field]}")
                        else:
                            print(f"  [FAIL] {field}: 누락")
                except json.JSONDecodeError as e:
                    print(f"  [WARN] JSON 파싱 실패: {e}")

                return True
            else:
                print(f"[FAIL] 오류 응답: {response.status_code}")
                print(f"에러: {response.text[:500]}")
                return False
        except Exception as e:
            print(f"[ERROR] 예외 발생: {e}")
            return False


async def test_extra_body_guided_json(url: str, model: str) -> bool:
    """extra_body guided_json 테스트 (레거시 방식)

    Args:
        url: vLLM 서버 URL
        model: 모델 이름

    Returns:
        지원 여부 (True/False)
    """
    schema = {
        "type": "object",
        "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
        "required": ["name", "age"],
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": "Generate a person with name and age."}
        ],
        "max_tokens": 100,
        "extra_body": {"guided_json": schema},
    }

    print()
    print("=" * 60)
    print("테스트: extra_body guided_json (레거시)")
    print("=" * 60)

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(url, json=payload)
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                print("[SUCCESS] extra_body guided_json 지원됨!")
                print(f"응답: {content}")
                return True
            else:
                print(f"[FAIL] 오류 응답: {response.status_code}")
                print(f"에러: {response.text[:300]}")
                return False
        except Exception as e:
            print(f"[ERROR] 예외 발생: {e}")
            return False


async def test_json_object_baseline(url: str, model: str) -> bool:
    """기본 json_object 모드 테스트 (비교용)

    Args:
        url: vLLM 서버 URL
        model: 모델 이름

    Returns:
        지원 여부 (True/False)
    """
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": "Generate a JSON with name, age, city fields.",
            }
        ],
        "max_tokens": 200,
        "response_format": {"type": "json_object"},
    }

    print()
    print("=" * 60)
    print("테스트: json_object (기본 모드, 비교용)")
    print("=" * 60)

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(url, json=payload)
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                print("[SUCCESS] json_object 응답 수신")
                print(f"응답: {content}")
                return True
            else:
                print(f"[FAIL] 오류 응답: {response.status_code}")
                return False
        except Exception as e:
            print(f"[ERROR] 예외 발생: {e}")
            return False


async def test_yeji_schema(url: str, model: str) -> bool:
    """yeji-ai-server의 실제 스키마로 테스트

    Args:
        url: vLLM 서버 URL
        model: 모델 이름

    Returns:
        지원 여부 (True/False)
    """
    # EasternFullLLMOutput 간소화 스키마
    schema = {
        "type": "object",
        "properties": {
            "personality": {"type": "string", "description": "성격 분석"},
            "strength": {"type": "string", "description": "강점 분석"},
            "weakness": {"type": "string", "description": "약점과 보완 방법"},
            "advice": {"type": "string", "description": "종합 조언"},
            "summary": {"type": "string", "description": "요약"},
            "message": {"type": "string", "description": "메시지"},
            "badges": {
                "type": "array",
                "items": {"type": "string"},
                "description": "배지 코드 목록",
            },
        },
        "required": [
            "personality",
            "strength",
            "weakness",
            "advice",
            "summary",
            "message",
            "badges",
        ],
    }

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "당신은 동양 사주 전문가입니다. JSON 형식으로만 응답하세요.",
            },
            {
                "role": "user",
                "content": """다음 사주를 분석해주세요.
일간: 갑목(甲木)
오행: 목 3개, 화 2개, 토 1개, 금 1개, 수 1개

응답 형식:
{
  "personality": "성격 분석",
  "strength": "강점",
  "weakness": "약점",
  "advice": "조언",
  "summary": "요약",
  "message": "상세 메시지",
  "badges": ["WOOD_STRONG", "YANG_DOMINANT"]
}""",
            },
        ],
        "max_tokens": 500,
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": "eastern-fortune", "schema": schema, "strict": True},
        },
    }

    print()
    print("=" * 60)
    print("테스트: yeji-ai-server 실제 스키마")
    print("=" * 60)

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post(url, json=payload)
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                print("[SUCCESS] yeji 스키마 테스트 성공!")

                try:
                    parsed = json.loads(content)
                    print(f"파싱된 데이터:")
                    print(json.dumps(parsed, ensure_ascii=False, indent=2))

                    # 필수 필드 검증
                    required_fields = [
                        "personality",
                        "strength",
                        "weakness",
                        "advice",
                        "summary",
                        "message",
                        "badges",
                    ]
                    missing = [f for f in required_fields if f not in parsed]
                    if missing:
                        print(f"  [WARN] 누락된 필드: {missing}")
                    else:
                        print("  [OK] 모든 필수 필드 존재")

                except json.JSONDecodeError as e:
                    print(f"  [WARN] JSON 파싱 실패: {e}")

                return True
            else:
                print(f"[FAIL] 오류 응답: {response.status_code}")
                print(f"에러: {response.text[:500]}")
                return False
        except Exception as e:
            print(f"[ERROR] 예외 발생: {e}")
            return False


async def main():
    """메인 테스트 실행"""
    parser = argparse.ArgumentParser(description="vLLM guided_json 지원 여부 테스트")
    parser.add_argument(
        "--url",
        default=DEFAULT_VLLM_URL,
        help=f"vLLM 서버 URL (기본: {DEFAULT_VLLM_URL})",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"모델 이름 (기본: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--skip-yeji",
        action="store_true",
        help="yeji 스키마 테스트 스킵",
    )
    args = parser.parse_args()

    print()
    print("=" * 60)
    print("vLLM Guided Decoding 지원 여부 테스트")
    print("=" * 60)
    print(f"서버: {args.url}")
    print(f"모델: {args.model}")
    print()

    results = {
        "json_schema": await test_json_schema_support(args.url, args.model),
        "extra_body_guided_json": await test_extra_body_guided_json(
            args.url, args.model
        ),
        "json_object_baseline": await test_json_object_baseline(args.url, args.model),
    }

    if not args.skip_yeji:
        results["yeji_schema"] = await test_yeji_schema(args.url, args.model)

    # 결과 요약
    print()
    print("=" * 60)
    print("테스트 결과 요약")
    print("=" * 60)
    for test_name, passed in results.items():
        status = "[SUCCESS]" if passed else "[FAIL]"
        print(f"  {test_name}: {status}")

    # 권장사항
    print()
    print("권장사항:")
    if results["json_schema"]:
        print("  -> json_schema response_format 사용 권장 (최신 방식)")
        print("  -> config.py: USE_GUIDED_JSON=true (기본값)")
    elif results["extra_body_guided_json"]:
        print("  -> extra_body guided_json 사용 권장 (레거시)")
        print("  -> vllm_client.py의 GenerationConfig.guided_json 활용")
    else:
        print("  -> guided decoding 미지원. 서버 재설정 필요")
        print("  -> 임시: USE_GUIDED_JSON=false (json_object 폴백)")
        print("  -> vLLM 서버 시작 옵션 확인:")
        print("       --guided-decoding-backend auto")

    # 종료 코드
    if results["json_schema"] or results["extra_body_guided_json"]:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
