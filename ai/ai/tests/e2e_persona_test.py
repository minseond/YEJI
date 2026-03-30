"""캐릭터 페르소나 Few-shot 프롬프트 E2E 테스트

각 캐릭터가 올바른 말투로 응답하는지 검증
"""

import asyncio
import re
import httpx


# vLLM 서버 설정 (환경변수로 오버라이드 가능)
import os
VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", "http://localhost:8001") + "/v1"
MODEL_NAME = os.getenv("VLLM_MODEL", "tellang/yeji-8b-rslora-v7-AWQ")


# 캐릭터별 SYSTEM_PROMPT import
from yeji_ai.prompts.character_personas import (
    SOISEOL, STELLA, CHEONGWOON, HWARIN, KYLE, ELARIA
)


# 테스트용 간단한 질문
TEST_QUESTION = "자기 소개를 해주세요."


async def call_vllm(system_prompt: str, user_message: str) -> str:
    """vLLM API 호출"""
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{VLLM_BASE_URL}/chat/completions",
            json={
                "model": MODEL_NAME,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                "max_tokens": 200,
                "temperature": 0.7,
                "top_p": 0.8,
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]


def count_speech_patterns(text: str) -> dict:
    """말투 패턴 카운트"""
    patterns = {
        "하오체": len(re.findall(r"(하오|이오|있소|겠소|구려|로다|시오|마시오)", text)),
        "해요체": len(re.findall(r"(해요|이에요|예요|네요|세요|어요|거든요|드릴게요|할게요)", text)),
        "합니다체": len(re.findall(r"(합니다|입니다|습니다|겠습니다|됩니다)", text)),
        "반말": len(re.findall(r"(해\.|야\.|지\.|거든\.|잖아)", text)),
    }
    return patterns


def evaluate_response(char_name: str, expected_style: str, response: str) -> dict:
    """응답 평가"""
    patterns = count_speech_patterns(response)

    # 기대하는 말투에 따른 점수 계산
    score = 0
    issues = []

    if expected_style == "하오체":
        if patterns["하오체"] > 0:
            score += 50
        if patterns["합니다체"] == 0:
            score += 30
        if patterns["해요체"] == 0:
            score += 20
        if patterns["합니다체"] > 0:
            issues.append(f"합니다체 {patterns['합니다체']}개 발견")
        if patterns["해요체"] > 0:
            issues.append(f"해요체 {patterns['해요체']}개 발견")

    elif expected_style == "해요체":
        if patterns["해요체"] > 0:
            score += 50
        if patterns["합니다체"] == 0:
            score += 30
        if patterns["하오체"] == 0:
            score += 20
        if patterns["합니다체"] > 0:
            issues.append(f"합니다체 {patterns['합니다체']}개 발견")
        if patterns["하오체"] > 0:
            issues.append(f"하오체 {patterns['하오체']}개 발견")

    elif expected_style == "반말혼용":
        # 반말+존댓말 혼용은 다양한 패턴 허용
        if patterns["반말"] > 0 or patterns["해요체"] > 0:
            score += 50
        if patterns["하오체"] == 0:
            score += 30
        if patterns["합니다체"] == 0:
            score += 20
        if patterns["하오체"] > 0:
            issues.append(f"하오체 {patterns['하오체']}개 발견")

    elif expected_style == "하십시오+해요":
        # 하십시오체와 해요체 혼용
        if patterns["합니다체"] > 0 or patterns["해요체"] > 0:
            score += 70
        if patterns["하오체"] == 0:
            score += 30
        if patterns["하오체"] > 0:
            issues.append(f"하오체 {patterns['하오체']}개 발견")

    return {
        "char_name": char_name,
        "expected_style": expected_style,
        "score": score,
        "patterns": patterns,
        "issues": issues,
        "response": response[:200] + "..." if len(response) > 200 else response,
    }


async def run_character_test(name: str, module, expected_style: str) -> dict:
    """단일 캐릭터 테스트 (pytest 테스트가 아닌 헬퍼 함수)"""
    print(f"\n{'='*60}")
    print(f"테스트: {name} (기대 말투: {expected_style})")
    print("="*60)

    try:
        response = await call_vllm(module.SYSTEM_PROMPT, TEST_QUESTION)
        result = evaluate_response(name, expected_style, response)

        print(f"\n응답:\n{response}\n")
        print(f"패턴 분석: {result['patterns']}")
        print(f"점수: {result['score']}/100")

        if result["issues"]:
            print(f"⚠️ 문제점: {', '.join(result['issues'])}")
        else:
            print("✅ 말투 검증 통과")

        return result

    except Exception as e:
        print(f"❌ 오류: {e}")
        return {
            "char_name": name,
            "expected_style": expected_style,
            "score": 0,
            "error": str(e),
        }


async def main():
    """메인 테스트 실행"""
    print("\n" + "="*60)
    print("캐릭터 페르소나 Few-shot E2E 테스트")
    print("="*60)

    # 테스트할 캐릭터 목록
    characters = [
        ("소이설 (SOISEOL)", SOISEOL, "하오체"),
        ("스텔라 (STELLA)", STELLA, "해요체"),
        ("청운 (CHEONGWOON)", CHEONGWOON, "하오체"),
        ("화린 (HWARIN)", HWARIN, "해요체"),
        ("카일 (KYLE)", KYLE, "반말혼용"),
        ("엘라리아 (ELARIA)", ELARIA, "하십시오+해요"),
    ]

    results = []
    for name, module, expected_style in characters:
        result = await run_character_test(name, module, expected_style)
        results.append(result)

    # 종합 결과
    print("\n" + "="*60)
    print("종합 결과")
    print("="*60)

    total_score = 0
    for r in results:
        score = r.get("score", 0)
        total_score += score
        status = "✅" if score >= 80 else "⚠️" if score >= 50 else "❌"
        print(f"{status} {r['char_name']}: {score}/100")

    avg_score = total_score / len(results)
    print(f"\n평균 점수: {avg_score:.1f}/100")

    return results


if __name__ == "__main__":
    asyncio.run(main())
