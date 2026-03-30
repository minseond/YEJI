"""티키타카 제너레이터 - 동양 도사 ↔ 서양 점성술사 대화 생성"""

import asyncio
import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from yeji_ai.clients.vllm_client import GenerationConfig, get_vllm_client
from yeji_ai.config import get_settings
from yeji_ai.models.saju import SajuResult
from yeji_ai.models.schemas import (
    Character,
    ChatMessage,
    MessageType,
    SessionState,
    SSEEvent,
)

logger = logging.getLogger(__name__)


class Speaker(str, Enum):
    """발화자"""

    DOSA = "dosa"  # 동양 도사
    ASTROLOGER = "astrologer"  # 서양 점성술사
    SYSTEM = "system"  # 시스템 (질문 등)


# 캐릭터 매핑
SPEAKER_TO_CHARACTER = {
    Speaker.DOSA: Character.DOSA,
    Speaker.ASTROLOGER: Character.ASTROLOGER,
}


@dataclass
class TikitakaContext:
    """티키타카 대화 컨텍스트"""

    saju_result: SajuResult
    messages: list[dict[str, Any]] = field(default_factory=list)
    current_turn: int = 0
    max_turns: int = 10
    question_asked: bool = False


class TikitakaGenerator:
    """티키타카 대화 생성기

    동양(사주) + 서양(별자리) 관점에서 운세를 분석하고
    두 전문가의 토론 형식으로 결과를 스트리밍합니다.
    """

    # 시스템 프롬프트 템플릿 (yeji-fortune-telling-ko-v3 스타일 적용)
    SYSTEM_PROMPT = (
        """[BAZI] 당신은 YEJI(예지) AI입니다. 15년 경력의 동양 사주팔자와 서양 """
        """점성술 전문가로서 상담합니다.

## 역할
두 명의 캐릭터로 대화합니다:
1. **도사** (동양): 30년 경력의 사주명리학 전문가. 오행(목화토금수), 천간지지, """
        """십성, 용신을 기반으로 분석합니다.
2. **점성술사** (서양): 20년 경력의 점성술사. 태양/달/상승궁, 행성 배치, """
        """하우스 시스템을 기반으로 분석합니다.

## 대화 스타일
- 도사: "~하시오", "~이로다" 등 고풍스럽고 신비로운 어투. 전문 용어(일간, """
        """대운, 십성 등) 자연스럽게 사용.
- 점성술사: 친근하고 현대적인 어투. 별자리 상징과 행성 에너지를 """
        """따뜻하게 설명.

## 사주 정보
{saju_info}

## 중요 규칙
1. **반드시 한국어로만 응답하세요.** 다른 언어(베트남어, 중국어, 영어 등) 절대 사용 금지.
2. 각 발언은 2-3문장으로 간결하되, 전문적인 통찰을 담으세요.
3. 서로의 의견에 동의하거나 보완하며 자연스러운 대화를 이어가세요.
4. 긍정적이고 희망적인 톤을 유지하되, 현실적인 조언을 제공하세요.
5. 사주의 강점과 주의점을 균형있게 언급하세요.
"""
    )

    # 중간 질문 목록
    INTERMEDIATE_QUESTIONS = [
        "지금까지의 분석이 공감이 되시나요? 특별히 더 알고 싶은 부분이 있으신가요?",
        "현재 가장 고민되는 부분은 무엇인가요?",
    ]

    DOSA_PREFIX = "[도사] "
    ASTROLOGER_PREFIX = "[점성술사] "

    def __init__(self):
        self.client = get_vllm_client()
        self.settings = get_settings()

    def _build_saju_info(self, saju_result: SajuResult) -> str:
        """사주 결과를 프롬프트용 문자열로 변환 (전문 용어 사용)"""
        eastern = saju_result.eastern
        western = saju_result.western

        # 오행 중 가장 강한 원소 찾기
        elements = {
            "목(木)": eastern.element_balance.wood,
            "화(火)": eastern.element_balance.fire,
            "토(土)": eastern.element_balance.earth,
            "금(金)": eastern.element_balance.metal,
            "수(水)": eastern.element_balance.water,
        }
        dominant = max(elements, key=elements.get)
        weak = min(elements, key=elements.get)

        info_parts = [
            "## 동양 명리학 (사주팔자)",
            (
                f"- 사주 구성: {eastern.four_pillars.year}(년주) "
                f"{eastern.four_pillars.month}(월주) {eastern.four_pillars.day}(일주) "
                f"{eastern.four_pillars.hour or '미상'}(시주)"
            ),
            f"- 일간(日干): {eastern.day_master}",
            (
                f"- 오행 분포: 목{eastern.element_balance.wood} "
                f"화{eastern.element_balance.fire} 토{eastern.element_balance.earth} "
                f"금{eastern.element_balance.metal} 수{eastern.element_balance.water}"
            ),
            f"- 왕성한 기운: {dominant} | 부족한 기운: {weak}",
            "",
            "## 서양 점성술 (별자리)",
            f"- 태양궁(Sun Sign): {western.sun_sign}",
            f"- 달궁(Moon Sign): {western.moon_sign or '미상'}",
            f"- 상승궁(Rising Sign): {western.rising_sign or '미상'}",
        ]

        return "\n".join(info_parts)

    def _build_system_prompt(self, saju_result: SajuResult) -> str:
        """시스템 프롬프트 생성"""
        saju_info = self._build_saju_info(saju_result)
        return self.SYSTEM_PROMPT.format(saju_info=saju_info)

    def _build_conversation_prompt(
        self,
        context: TikitakaContext,
        next_speaker: Speaker,
        user_answer: str | None = None,
    ) -> str:
        """대화 프롬프트 생성"""
        system_prompt = self._build_system_prompt(context.saju_result)

        # 기존 대화 내역 구성
        conversation_history = []
        for msg in context.messages:
            speaker = msg.get("speaker")
            content = msg.get("content", "")
            if speaker == Speaker.DOSA:
                conversation_history.append(f"{self.DOSA_PREFIX}{content}")
            elif speaker == Speaker.ASTROLOGER:
                conversation_history.append(f"{self.ASTROLOGER_PREFIX}{content}")
            elif speaker == Speaker.SYSTEM:
                conversation_history.append(f"[질문] {content}")
            elif speaker == "user":
                conversation_history.append(f"[사용자 답변] {content}")

        if user_answer:
            conversation_history.append(f"[사용자 답변] {user_answer}")

        history_text = "\n\n".join(conversation_history)

        # 다음 발화자 프롬프트
        if next_speaker == Speaker.DOSA:
            next_prefix = self.DOSA_PREFIX
            instruction = "도사로서 사주팔자 관점에서 응답하세요."
        else:
            next_prefix = self.ASTROLOGER_PREFIX
            instruction = "점성술사로서 별자리 관점에서 응답하세요."

        prompt = f"""{system_prompt}

## 대화 내역
{history_text}

## 지시
{instruction}

{next_prefix}"""

        return prompt

    async def generate_discussion(
        self,
        session_id: str,
        session: SessionState,
        saju_result: SajuResult,
        answer_event: asyncio.Event | None = None,
        pending_answers: dict[str, str] | None = None,
    ) -> AsyncIterator[str]:
        """
        티키타카 토론 스트리밍 (SSE 이벤트 직접 반환)

        Args:
            session_id: 세션 ID
            session: 세션 상태
            saju_result: 사주 분석 결과
            answer_event: 사용자 답변 대기 이벤트
            pending_answers: 대기 중인 답변 저장소
        """
        context = TikitakaContext(
            saju_result=saju_result,
            max_turns=self.settings.tikitaka_max_turns,
        )

        question_interval = self.settings.tikitaka_question_count
        question_asked_count = 0

        for turn in range(context.max_turns):
            context.current_turn = turn
            speaker = Speaker.DOSA if turn % 2 == 0 else Speaker.ASTROLOGER
            character = SPEAKER_TO_CHARACTER[speaker]

            # 메시지 시작 이벤트
            yield SSEEvent(
                event="message_start",
                data={"character": character.value, "turn": turn},
            ).to_sse()

            # vLLM 스트리밍 생성
            prompt = self._build_conversation_prompt(context, speaker)
            config = GenerationConfig(max_tokens=256, temperature=0.8)

            full_response = ""
            try:
                async for token in self.client.generate_stream(prompt, config):
                    full_response += token
                    yield SSEEvent(
                        event="message",
                        data={
                            "type": MessageType.DISCUSSION.value,
                            "character": character.value,
                            "content": token,
                            "streaming": True,
                        },
                    ).to_sse()
            except Exception as e:
                logger.error(f"vLLM 스트리밍 오류: {e}")
                # Fallback: mock 응답
                mock_response = self._get_mock_response(speaker, turn)
                for char in mock_response:
                    full_response += char
                    yield SSEEvent(
                        event="message",
                        data={
                            "type": MessageType.DISCUSSION.value,
                            "character": character.value,
                            "content": char,
                            "streaming": True,
                        },
                    ).to_sse()
                    await asyncio.sleep(0.02)

            # 메시지 완료 이벤트
            yield SSEEvent(
                event="message_complete",
                data={"character": character.value, "turn": turn},
            ).to_sse()

            # 컨텍스트에 메시지 추가
            context.messages.append(
                {
                    "speaker": speaker,
                    "content": full_response.strip(),
                }
            )

            # 중간 질문 (question_interval 턴마다)
            if (
                turn > 0
                and turn % question_interval == 0
                and question_asked_count < len(self.INTERMEDIATE_QUESTIONS)
                and answer_event is not None
            ):
                question = self.INTERMEDIATE_QUESTIONS[question_asked_count]
                question_asked_count += 1

                yield SSEEvent(
                    event="question",
                    data={
                        "type": MessageType.QUESTION.value,
                        "content": question,
                        "question_id": f"q_{turn}",
                    },
                ).to_sse()

                yield SSEEvent(event="pause", data={"waiting_for": "answer"}).to_sse()

                # 사용자 답변 대기
                if answer_event:
                    answer_event.clear()
                    try:
                        await asyncio.wait_for(answer_event.wait(), timeout=300)
                        user_answer = pending_answers.get(session_id, "") if pending_answers else ""
                        if user_answer:
                            context.messages.append(
                                {
                                    "speaker": "user",
                                    "content": user_answer,
                                }
                            )
                            # 대기 답변 제거
                            if pending_answers and session_id in pending_answers:
                                del pending_answers[session_id]
                    except TimeoutError:
                        logger.info(f"답변 대기 타임아웃: {session_id}")

            await asyncio.sleep(0.5)  # 턴 간 간격

    def _get_mock_response(self, speaker: Speaker, turn: int) -> str:
        """Mock 응답 생성 (vLLM 연결 실패 시)"""
        if speaker == Speaker.DOSA:
            responses = [
            (
                "음... 사주를 살펴보니, 목(木)의 기운이 강하시군요. "
                "올해는 특히 새로운 시작에 좋은 기운이 감돌고 있습니다."
            ),
                "화(火)의 기운이 부족하니, 열정적인 활동을 통해 균형을 맞추시는 것이 좋겠습니다.",
                "일간의 기운으로 보아, 대인관계에서 좋은 인연을 만나실 수 있는 시기입니다.",
            ]
        else:
            responses = [
            (
                "흥미롭네요! 별자리 관점에서 보면, 현재 금성이 좋은 위치에 있어 "
                "인간관계가 활발해질 수 있어요."
            ),
            (
                "도사님 말씀에 동의해요. 점성술적으로도 지금은 새로운 프로젝트를 "
                "시작하기 좋은 시기입니다."
            ),
            (
                "수성의 역행이 끝나면서 커뮤니케이션이 원활해질 거예요. "
                "미뤄뒀던 대화를 나눠보세요!"
            ),
            ]
        return responses[turn % len(responses)]

    async def generate_chat_response(
        self,
        session: SessionState,
        saju_result: SajuResult,
        user_message: str,
    ) -> list[ChatMessage]:
        """추가 채팅에 대한 응답 생성"""
        messages = []

        # 도사 응답
        dosa_prompt = self._build_chat_prompt(saju_result, user_message, Speaker.DOSA)
        config = GenerationConfig(max_tokens=200, temperature=0.7)

        try:
            response = await self.client.generate(dosa_prompt, config)
            dosa_content = response.text.strip()
        except Exception as e:
            logger.error(f"vLLM 생성 오류: {e}")
            dosa_content = "음... 그 부분에 대해서는 사주의 흐름을 더 살펴봐야 할 것 같습니다."

        messages.append(
            ChatMessage(
                character=Character.DOSA,
                content=dosa_content,
                message_type=MessageType.CHAT,
            )
        )

        # 점성술사 응답
        astro_prompt = self._build_chat_prompt(
            saju_result, user_message, Speaker.ASTROLOGER, dosa_content
        )

        try:
            response = await self.client.generate(astro_prompt, config)
            astro_content = response.text.strip()
        except Exception as e:
            logger.error(f"vLLM 생성 오류: {e}")
            astro_content = (
                "별자리 관점에서 보완해드릴게요. 현재 행성 배치가 좋은 시기이니 걱정 마세요!"
            )

        messages.append(
            ChatMessage(
                character=Character.ASTROLOGER,
                content=astro_content,
                message_type=MessageType.CHAT,
            )
        )

        return messages

    def _build_chat_prompt(
        self,
        saju_result: SajuResult,
        user_message: str,
        speaker: Speaker,
        previous_response: str | None = None,
    ) -> str:
        """채팅 프롬프트 생성"""
        system_prompt = self._build_system_prompt(saju_result)

        if speaker == Speaker.DOSA:
            instruction = "도사로서 사주팔자 관점에서 사용자의 질문에 답변하세요."
            prefix = self.DOSA_PREFIX
        else:
            instruction = "점성술사로서 별자리 관점에서 사용자의 질문에 답변하세요."
            prefix = self.ASTROLOGER_PREFIX
            if previous_response:
                instruction += (
                    f"\n\n도사의 답변을 참고하여 보완하세요:\n{self.DOSA_PREFIX}{previous_response}"
                )

        return f"""{system_prompt}

## 사용자 질문
{user_message}

## 지시
{instruction}
2-3문장으로 간결하게 답변하세요.

{prefix}"""
