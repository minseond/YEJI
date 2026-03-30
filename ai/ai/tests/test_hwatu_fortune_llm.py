"""화투점 LLM 테스트: v7 모델의 화투점 해석 능력 검증

v7 모델(yeji-8b)에 화투점 프롬프트를 직접 보내서
추가 학습 없이도 해석이 가능한지 테스트
"""

from pathlib import Path

import pytest

from yeji_ai.clients.vllm_client import VLLMClient, GenerationConfig
from yeji_ai.config import get_settings

# 테스트 결과 저장 경로
OUTPUT_DIR = Path("C:/Users/SSAFY/yeji-ai-server/ai/tests/outputs/hwatu_fortune")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# 화투 System Prompt
HWATU_SYSTEM_PROMPT = """당신은 화투점 전문가입니다.

[화투 48장 핵심 의미]
1월(소나무): 시작, 고집, 원칙
2월(매화): 인내, 준비, 사랑
3월(벚꽃): 유혹, 감정, 불안정
4월(등나무): 관계 얽힘, 집착
5월(창포): 경쟁, 힘, 승부욕
6월(모란): 명예, 과시, 체면
7월(싸리): 변화, 이동, 횡재
8월(공산): 공허, 거리감, 단절
9월(국화): 정리, 결론
10월(단풍): 욕심, 거래
11월(오동): 보호, 성장, 금전
12월(비): 반복, 순환

[카드 등급별 의미]
- 광(光): 결정적 사건, 강한 운, 명확한 방향
- 열끗: 현실, 실속, 관계의 균형
- 띠: 말, 약속, 인간관계
- 피: 소모, 감정 낭비, 사소한 문제

[4장 배치 규칙]
1번 카드: 본인/현재 상태
2번 카드: 상대/환경
3번 카드: 과정/관계
4번 카드: 결과/조언

해석 시 각 카드의 월별 의미와 등급을 조합하여 위치에 맞게 해석하고,
마지막에 종합 해석과 조언을 제공하세요."""


# Few-shot 예시
FEW_SHOT_EXAMPLES = """
[예시 1]
Q: 뽑은 카드: 2월 광, 6월 띠, 9월 피, 1월 열끗. 직장운이 궁금합니다.
A: [카드 해석]
1번(본인): 2월 광 - 현재 당신은 강한 의지와 인내심으로 직장에서 버티고 있습니다. 광이 나왔으니 곧 결정적인 순간이 옵니다.
2번(환경): 6월 띠 - 주변에서 체면이나 명예와 관련된 말들이 오갑니다. 동료들의 평판에 신경쓰이는 상황.
3번(과정): 9월 피 - 정리 과정에서 소소한 에너지 소모가 있겠습니다. 작은 스트레스들이 쌓일 수 있어요.
4번(결과): 1월 열끗 - 결국 원칙대로 실속있는 결과를 얻습니다. 새로운 시작의 기반이 마련됩니다.

[종합 해석]
직장에서 힘든 시기를 버티고 계시네요. 주변의 시선이 신경쓰이지만, 원칙을 지키면 좋은 결과가 옵니다.

[조언]
작은 일에 에너지 낭비하지 마시고, 큰 그림을 보세요. 곧 전환점이 옵니다.

---

[예시 2]
Q: 뽑은 카드: 8월 피, 4월 열끗, 3월 띠, 7월 광. 연애운이 궁금합니다.
A: [카드 해석]
1번(본인): 8월 피 - 현재 마음이 공허하고 지쳐있습니다. 감정적으로 소모된 상태.
2번(상대): 4월 열끗 - 상대방은 관계에 얽매여 있고, 현실적인 균형을 찾으려 합니다.
3번(과정): 3월 띠 - 감정적인 대화가 오갈 것입니다. 유혹이나 불안정한 약속이 있을 수 있어요.
4번(결과): 7월 광 - 결국 큰 변화가 옵니다! 횡재 같은 전환점이 될 수 있어요.

[종합 해석]
지금은 지쳐있지만, 이 관계가 큰 변화의 계기가 됩니다. 감정적 대화를 조심하되 결과는 긍정적입니다.

[조언]
지금의 공허함은 변화 전 고요입니다. 감정에 휘둘리지 말고 기다리세요.
"""


# 공통 질문 (테스트용)
TEST_QUESTION = "화투점을 봐주세요. 뽑은 카드: 1월 광, 3월 피, 7월 열끗, 11월 띠. 연애운이 궁금합니다."


@pytest.fixture
def vllm_client() -> VLLMClient:
    """VLLMClient 픽스처"""
    settings = get_settings()
    return VLLMClient(
        base_url=settings.vllm_base_url,
        model=settings.vllm_model,
        timeout=120.0,
    )


def evaluate_response(response: str) -> dict[str, bool]:
    """응답 품질 평가

    Args:
        response: LLM 응답 텍스트

    Returns:
        평가 결과 딕셔너리
    """
    return {
        "4장_모두_언급": all(
            card in response for card in ["1월", "3월", "7월", "11월"]
        ),
        "위치별_의미_언급": any(
            keyword in response for keyword in ["본인", "상대", "과정", "결과"]
        ),
        "종합_해석_제공": any(
            keyword in response for keyword in ["종합", "전체적으로", "정리하면"]
        ),
        "조언_포함": "조언" in response or "추천" in response or "권장" in response,
    }


@pytest.mark.asyncio
async def test_baseline_no_prompt(vllm_client: VLLMClient) -> None:
    """테스트 1: 베이스라인 (프롬프트 없음)

    System prompt 없이 기본 질문만
    """
    messages = [{"role": "user", "content": TEST_QUESTION}]
    config = GenerationConfig(max_tokens=1024, temperature=0.7)
    response = await vllm_client.chat(messages, config)

    # 응답 저장
    output_file = OUTPUT_DIR / "test1_baseline.txt"
    output_file.write_text(response.text, encoding="utf-8")

    # 평가
    evaluation = evaluate_response(response.text)
    eval_file = OUTPUT_DIR / "test1_evaluation.txt"
    eval_file.write_text(
        f"응답:\n{response.text}\n\n평가:\n{evaluation}", encoding="utf-8"
    )

    # 기본 검증 (응답이 있는지만)
    assert len(response.text) > 0
    print(f"\n[테스트 1 결과]\n{response.text}\n평가: {evaluation}")


@pytest.mark.asyncio
async def test_with_system_prompt(vllm_client: VLLMClient) -> None:
    """테스트 2: System Prompt + 규칙 포함

    화투 48장 핵심 의미와 해석 규칙을 System prompt에 포함
    """
    messages = [
        {"role": "system", "content": HWATU_SYSTEM_PROMPT},
        {"role": "user", "content": TEST_QUESTION},
    ]
    config = GenerationConfig(max_tokens=1024, temperature=0.7)
    response = await vllm_client.chat(messages, config)

    # 응답 저장
    output_file = OUTPUT_DIR / "test2_with_system_prompt.txt"
    output_file.write_text(response.text, encoding="utf-8")

    # 평가
    evaluation = evaluate_response(response.text)
    eval_file = OUTPUT_DIR / "test2_evaluation.txt"
    eval_file.write_text(
        f"응답:\n{response.text}\n\n평가:\n{evaluation}", encoding="utf-8"
    )

    assert len(response.text) > 0
    print(f"\n[테스트 2 결과]\n{response.text}\n평가: {evaluation}")


@pytest.mark.asyncio
async def test_with_few_shot(vllm_client: VLLMClient) -> None:
    """테스트 3: Few-shot 예시 추가

    System prompt + 해석 예시 2개 포함
    """
    full_system_prompt = f"{HWATU_SYSTEM_PROMPT}\n\n{FEW_SHOT_EXAMPLES}"

    messages = [
        {"role": "system", "content": full_system_prompt},
        {"role": "user", "content": TEST_QUESTION},
    ]
    config = GenerationConfig(max_tokens=1024, temperature=0.7)
    response = await vllm_client.chat(messages, config)

    # 응답 저장
    output_file = OUTPUT_DIR / "test3_with_few_shot.txt"
    output_file.write_text(response.text, encoding="utf-8")

    # 평가
    evaluation = evaluate_response(response.text)
    eval_file = OUTPUT_DIR / "test3_evaluation.txt"
    eval_file.write_text(
        f"응답:\n{response.text}\n\n평가:\n{evaluation}", encoding="utf-8"
    )

    assert len(response.text) > 0
    print(f"\n[테스트 3 결과]\n{response.text}\n평가: {evaluation}")


@pytest.mark.asyncio
async def test_all_and_compare(vllm_client: VLLMClient) -> None:
    """통합 테스트: 3가지 방식 비교

    3가지 테스트를 모두 실행하고 비교 리포트 생성
    """
    config = GenerationConfig(max_tokens=1024, temperature=0.7)

    # 테스트 1: Baseline
    messages1 = [{"role": "user", "content": TEST_QUESTION}]
    response1 = await vllm_client.chat(messages1, config)
    eval1 = evaluate_response(response1.text)

    # 테스트 2: System Prompt
    messages2 = [
        {"role": "system", "content": HWATU_SYSTEM_PROMPT},
        {"role": "user", "content": TEST_QUESTION},
    ]
    response2 = await vllm_client.chat(messages2, config)
    eval2 = evaluate_response(response2.text)

    # 테스트 3: Few-shot
    full_system_prompt = f"{HWATU_SYSTEM_PROMPT}\n\n{FEW_SHOT_EXAMPLES}"
    messages3 = [
        {"role": "system", "content": full_system_prompt},
        {"role": "user", "content": TEST_QUESTION},
    ]
    response3 = await vllm_client.chat(messages3, config)
    eval3 = evaluate_response(response3.text)

    # 비교 리포트 생성
    comparison_report = f"""# 화투점 LLM 테스트 비교 리포트

## 테스트 조건
질문: {TEST_QUESTION}
모델: {vllm_client.model}

---

## 테스트 1: Baseline (프롬프트 없음)

### 응답
{response1.text}

### 평가
{eval1}

점수: {sum(eval1.values())}/4

---

## 테스트 2: System Prompt

### 응답
{response2.text}

### 평가
{eval2}

점수: {sum(eval2.values())}/4

---

## 테스트 3: Few-shot

### 응답
{response3.text}

### 평가
{eval3}

점수: {sum(eval3.values())}/4

---

## 종합 분석

| 항목 | Baseline | System Prompt | Few-shot |
|------|----------|---------------|----------|
| 4장 모두 언급 | {'✅' if eval1['4장_모두_언급'] else '❌'} | {'✅' if eval2['4장_모두_언급'] else '❌'} | {'✅' if eval3['4장_모두_언급'] else '❌'} |
| 위치별 의미 | {'✅' if eval1['위치별_의미_언급'] else '❌'} | {'✅' if eval2['위치별_의미_언급'] else '❌'} | {'✅' if eval3['위치별_의미_언급'] else '❌'} |
| 종합 해석 | {'✅' if eval1['종합_해석_제공'] else '❌'} | {'✅' if eval2['종합_해석_제공'] else '❌'} | {'✅' if eval3['종합_해석_제공'] else '❌'} |
| 조언 포함 | {'✅' if eval1['조언_포함'] else '❌'} | {'✅' if eval2['조언_포함'] else '❌'} | {'✅' if eval3['조언_포함'] else '❌'} |
| **총점** | **{sum(eval1.values())}/4** | **{sum(eval2.values())}/4** | **{sum(eval3.values())}/4** |

## 결론

최고 성능: {"Baseline" if sum(eval1.values()) >= max(sum(eval2.values()), sum(eval3.values())) else "System Prompt" if sum(eval2.values()) >= sum(eval3.values()) else "Few-shot"}

권장 방식:
- System Prompt만으로 충분한지?
- Few-shot이 필요한지?
- 추가 학습(LoRA)이 필요한지?
"""

    # 리포트 저장
    report_file = OUTPUT_DIR / "comparison_report.md"
    report_file.write_text(comparison_report, encoding="utf-8")

    print(f"\n비교 리포트 저장 완료: {report_file}")
    print(comparison_report)
