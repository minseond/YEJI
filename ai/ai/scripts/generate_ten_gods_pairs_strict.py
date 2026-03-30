"""십신 복합 메시지 생성 스크립트 (품질 관리 강화)

810개 메시지 생성:
- 십신 45쌍 × 6카테고리 × 3변형 = 810개
- 품질 검증 강화: 길이, 십신 이름, 메타텍스트, 반복 체크
"""

import asyncio
import json
import sys
from pathlib import Path

import httpx


class SimpleLogger:
    """간단한 로거"""

    def info(self, msg: str, **kwargs):
        print(f"[INFO] {msg} {kwargs}")

    def warning(self, msg: str, **kwargs):
        print(f"[WARN] {msg} {kwargs}")

    def error(self, msg: str, **kwargs):
        print(f"[ERROR] {msg} {kwargs}")


logger = SimpleLogger()

# 상수 정의
TEN_GODS = [
    "BIJEON",
    "GEOBJE",
    "SIKSHIN",
    "SANGGWAN",
    "PYEONJAE",
    "JEONGJAE",
    "PYEONGWAN",
    "JEONGGWAN",
    "PYEONIN",
    "JEONGIN",
]

TEN_GODS_NAMES = {
    "BIJEON": "비견",
    "GEOBJE": "겁재",
    "SIKSHIN": "식신",
    "SANGGWAN": "상관",
    "PYEONJAE": "편재",
    "JEONGJAE": "정재",
    "PYEONGWAN": "편관",
    "JEONGGWAN": "정관",
    "PYEONIN": "편인",
    "JEONGIN": "정인",
}

CATEGORIES = ["GENERAL", "LOVE", "MONEY", "CAREER", "HEALTH", "STUDY"]

CATEGORY_KR = {
    "GENERAL": "총운",
    "LOVE": "연애운",
    "MONEY": "금전운",
    "CAREER": "직장운",
    "HEALTH": "건강운",
    "STUDY": "학업운",
}

# vLLM 설정
VLLM_URL = "http://13.125.68.166:8001/v1/chat/completions"
MODEL_NAME = "tellang/yeji-8b-rslora-v7"


def validate_message(msg: str, name1: str, name2: str) -> tuple[bool, str]:
    """메시지 품질 검증

    Returns:
        (is_valid, error_reason)
    """
    # 길이 체크
    if len(msg) < 40:
        return False, f"너무 짧음 ({len(msg)}자)"
    if len(msg) > 80:
        return False, f"너무 김 ({len(msg)}자)"

    # 십신 이름 체크
    if name1 not in msg:
        return False, f"{name1} 누락"
    if name2 not in msg:
        return False, f"{name2} 누락"

    # 메타텍스트 체크
    bad_words = [
        "템플릿",
        "요약",
        "분석",
        "질문",
        "답변",
        "다시",
        "요구사항",
        "예시",
        "제시",
        "작성",
        "생성",
        "오세요",
        "드립니다",
    ]
    for word in bad_words:
        if word in msg:
            return False, f"메타텍스트 포함: {word}"

    # 반복 체크
    if msg.count(name1) > 2:
        return False, f"{name1} 과도 반복"
    if msg.count(name2) > 2:
        return False, f"{name2} 과도 반복"

    # 마침표 체크
    if not msg.endswith("."):
        return False, "마침표 없음"

    return True, ""


async def generate_single_message(
    client: httpx.AsyncClient,
    god1: str,
    god2: str,
    category: str,
    variation: int,
    max_retries: int = 5,
) -> str | None:
    """단일 메시지 생성 (품질 검증 포함)"""
    name1 = TEN_GODS_NAMES[god1]
    name2 = TEN_GODS_NAMES[god2]
    category_kr = CATEGORY_KR[category]

    system_prompt = f"""당신은 사주명리학 전문가입니다.

[절대 규칙]
1. "{name1}"와 "{name2}" 두 단어가 반드시 문장에 포함되어야 함
2. 40-60자의 한 문장만 작성
3. 반드시 마침표(.)로 끝
4. 질문, 템플릿, 분석 요청 등 메타텍스트 절대 금지
5. {category_kr}에 관한 구체적인 운세만 작성

[좋은 예시]
{name1}의 기운과 {name2}의 힘이 만나 {category_kr}이 크게 상승합니다.
{name1}와 {name2}가 조화를 이루어 {category_kr}에서 좋은 성과를 얻습니다.

[나쁜 예시 - 절대 금지]
{name1}와 {name2}의 {category_kr} 메시지를 제시해주세요.
템플릿을 다시 작성하겠습니다.
"""

    user_prompt = f"{name1}와 {name2}의 {category_kr} 메시지를 한 문장으로 작성:"

    for attempt in range(max_retries):
        try:
            payload = {
                "model": MODEL_NAME,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "max_tokens": 150,
                "temperature": 0.7 + (attempt * 0.1),  # 재시도마다 온도 상승
                "top_p": 0.9,
            }

            response = await client.post(
                VLLM_URL,
                json=payload,
                timeout=30.0,
            )
            response.raise_for_status()

            data = response.json()
            message = data["choices"][0]["message"]["content"].strip()

            # 품질 검증
            is_valid, error = validate_message(message, name1, name2)

            if is_valid:
                return message
            else:
                logger.warning(
                    "message_invalid",
                    god1=god1,
                    god2=god2,
                    category=category,
                    variation=variation,
                    attempt=attempt + 1,
                    error=error,
                    message=message[:50],
                )
                continue

        except Exception as e:
            logger.error(
                "generation_error",
                god1=god1,
                god2=god2,
                category=category,
                variation=variation,
                attempt=attempt + 1,
                error=str(e),
            )
            await asyncio.sleep(1)

    logger.error(
        "generation_failed",
        god1=god1,
        god2=god2,
        category=category,
        variation=variation,
        max_retries=max_retries,
    )
    return None


async def generate_all_messages() -> dict:
    """모든 십신 복합 메시지 생성"""
    result = {}
    total_combinations = 0
    completed = 0
    failed = []

    # 십신 쌍 생성
    pairs = []
    for i, god1 in enumerate(TEN_GODS):
        for god2 in TEN_GODS[i + 1 :]:
            pairs.append((god1, god2))

    total_combinations = len(pairs) * len(CATEGORIES)
    total_messages = total_combinations * 3  # 각 조합당 3개 메시지

    logger.info(
        "generation_start",
        total_pairs=len(pairs),
        total_categories=len(CATEGORIES),
        total_combinations=total_combinations,
        total_messages=total_messages,
    )

    async with httpx.AsyncClient() as client:
        for god1, god2 in pairs:
            key = f"{god1}_{god2}"
            result[key] = {}

            for category in CATEGORIES:
                messages = []

                # 3개 변형 생성
                for variation in range(3):
                    message = await generate_single_message(
                        client,
                        god1,
                        god2,
                        category,
                        variation,
                    )

                    if message:
                        messages.append(message)
                    else:
                        failed.append(f"{key}_{category}_v{variation}")

                    completed += 1
                    progress = (completed / total_messages) * 100

                    print(
                        f"\r진행률: {completed}/{total_messages} ({progress:.1f}%) | "
                        f"실패: {len(failed)}",
                        end="",
                        flush=True,
                    )

                # 메시지가 하나라도 생성되면 저장
                if messages:
                    result[key][category] = messages

                # API 레이트 리밋 방지
                await asyncio.sleep(0.3)

    print()  # 개행

    logger.info(
        "generation_complete",
        total_combinations=total_combinations,
        total_messages_generated=sum(len(msgs) for pair in result.values() for msgs in pair.values()),
        failed_count=len(failed),
        failed_items=failed[:10],  # 처음 10개만 출력
    )

    return result


async def main():
    """메인 함수"""
    output_path = Path("C:/Users/SSAFY/yeji-ai-server/ai/data/eastern/ten_gods_pairs.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("script_start", output_path=str(output_path))

    # 메시지 생성
    result = await generate_all_messages()

    # 통계 계산
    total_pairs = len(result)
    total_categories = sum(len(categories) for categories in result.values())
    total_messages = sum(
        len(messages)
        for pair in result.values()
        for messages in pair.values()
    )

    # 파일 저장
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    logger.info(
        "script_complete",
        output_path=str(output_path),
        total_pairs=total_pairs,
        total_categories=total_categories,
        total_messages=total_messages,
        expected_messages=45 * 6 * 3,
    )

    print(f"\n✅ 완료!")
    print(f"   파일: {output_path}")
    print(f"   십신 쌍: {total_pairs}개")
    print(f"   카테고리: {total_categories}개")
    print(f"   메시지: {total_messages}개 (목표: 810개)")

    if total_messages < 810:
        print(f"   ⚠️  부족: {810 - total_messages}개")


if __name__ == "__main__":
    asyncio.run(main())
