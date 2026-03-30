"""티키타카 대화 생성 서비스

LLM + 코드 조합으로 TurnResponse JSON 생성
- LLM: 대화 텍스트 + 감정 코드 생성
- 코드: JSON 구조 조립 (bubble_id, timestamp, turn_end 등)
"""

import random
from datetime import UTC, datetime

import httpx
import structlog

from yeji_ai.config import get_settings
from yeji_ai.models.fortune.dialogue import (
    DialogueLine,
    DialogueMode,
    DialogueOutput,
    EasternContext,
    TikitakaSessionState,
    WesternContext,
)
from yeji_ai.models.fortune.eastern import EasternFortuneResponse
from yeji_ai.models.fortune.turn import (
    Bubble,
    Closure,
    Emotion,
    EmotionCode,
    FortuneCategory,
    InputSchema,
    InputType,
    InputValidation,
    Meta,
    Speaker,
    SummaryItem,
    TurnEnd,
    TurnEndAwaitUserInput,
    TurnEndCompleted,
    TurnResponse,
    UpgradeHook,
    UserPrompt,
)
from yeji_ai.models.user_fortune import WesternFortuneDataV2
from yeji_ai.prompts.tikitaka_prompts import (
    build_tikitaka_prompt,
    get_random_speaker_order,
)

logger = structlog.get_logger()


class TikitakaDialogueGenerator:
    """티키타카 대화 생성기

    LLM은 텍스트만 생성, 코드가 JSON 구조를 조립합니다.
    """

    # 대결/합의 비율 (70:30)
    BATTLE_PROBABILITY = 0.75

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
    ):
        """초기화

        Args:
            base_url: vLLM API URL
            model: 모델명
        """
        settings = get_settings()
        self.base_url = base_url or getattr(
            settings, "vllm_base_url", "http://localhost:8001/v1"
        )
        self.model = model or getattr(
            settings, "vllm_model", "tellang/yeji-8b-rslora-v7"
        )

        # URL 정리
        self.base_url = self.base_url.rstrip("/")
        if not self.base_url.endswith("/v1"):
            self.base_url = f"{self.base_url}/v1"

        self.chat_url = f"{self.base_url}/chat/completions"

        logger.info(
            "tikitaka_dialogue_generator_init",
            base_url=self.base_url,
            model=self.model,
        )

    # ============================================================
    # 컨텍스트 포맷팅
    # ============================================================

    def format_eastern_context(
        self, eastern: EasternFortuneResponse
    ) -> EasternContext:
        """동양 사주 컨텍스트 포맷팅"""
        chart = eastern.chart
        stats = eastern.stats

        # 일간 정보
        day_master = f"{chart.day.gan_code.hangul}({chart.day.gan})"
        day_element = chart.day.element_code.label_ko if chart.day.element_code else "목"

        # 사주 기둥
        pillars = (
            f"{chart.year.gan}{chart.year.ji}년 "
            f"{chart.month.gan}{chart.month.ji}월 "
            f"{chart.day.gan}{chart.day.ji}일"
        )
        if chart.hour:
            pillars += f" {chart.hour.gan}{chart.hour.ji}시"

        # 오행 분포
        five_elements = []
        for elem in stats.five_elements.get("elements", []):
            five_elements.append(f"{elem['label']}: {elem['percent']}%")
        five_elements_str = ", ".join(five_elements)

        # 강/약 오행
        strong = stats.five_elements.get("strong", "N/A")
        weak = stats.five_elements.get("weak", "N/A")
        five_elements_str += f" (강: {strong}, 약: {weak})"

        # 음양
        yin_yang_str = f"양 {stats.yin_yang.yang}%, 음 {stats.yin_yang.yin}%"

        return EasternContext(
            day_master=day_master,
            day_element=day_element,
            pillars=pillars,
            five_elements=five_elements_str,
            yin_yang=yin_yang_str,
            strength=stats.strength,
            weakness=stats.weakness,
        )

    def format_western_context(
        self, western: WesternFortuneDataV2
    ) -> WesternContext:
        """서양 점성술 컨텍스트 포맷팅"""
        stats = western.stats

        # 태양 별자리
        sun_sign = (
            stats.main_sign.name
            if hasattr(stats, "main_sign")
            else "알 수 없음"
        )

        # 우세 원소
        dominant_element = western.element
        if hasattr(stats, "element_4_distribution") and stats.element_4_distribution:
            max_elem = max(stats.element_4_distribution, key=lambda x: x.percent)
            dominant_element = max_elem.label

        # 운세 요약
        overview = ""
        if hasattr(western, "fortune_content") and western.fortune_content:
            overview = western.fortune_content.overview or ""

        return WesternContext(
            sun_sign=sun_sign,
            dominant_element=dominant_element,
            overview=overview,
        )

    def _context_to_string(self, ctx: EasternContext | WesternContext) -> str:
        """컨텍스트를 문자열로 변환 (프롬프트용)"""
        if isinstance(ctx, EasternContext):
            return f"""- 일간: {ctx.day_master} ({ctx.day_element})
- 사주: {ctx.pillars}
- 오행: {ctx.five_elements}
- 음양: {ctx.yin_yang}
- 강점: {ctx.strength}
- 약점: {ctx.weakness}"""
        else:
            return f"""- 태양: {ctx.sun_sign}
- 우세 원소: {ctx.dominant_element}
- 요약: {ctx.overview}"""

    # ============================================================
    # 대결/합의 모드 결정
    # ============================================================

    def decide_battle_or_consensus(self) -> DialogueMode:
        """대결/합의 모드 결정 (75:25 비율)"""
        if random.random() < self.BATTLE_PROBABILITY:
            return DialogueMode.BATTLE
        return DialogueMode.CONSENSUS

    # ============================================================
    # LLM 대화 생성
    # ============================================================

    async def generate_dialogues(
        self,
        topic: str,
        eastern_context: EasternContext,
        western_context: WesternContext,
        mode: DialogueMode,
        is_first_turn: bool = False,
        is_last_turn: bool = False,
    ) -> DialogueOutput:
        """LLM으로 대화 생성

        Args:
            topic: 주제
            eastern_context: 동양 컨텍스트
            western_context: 서양 컨텍스트
            mode: 대화 모드
            is_first_turn: 첫 턴 여부
            is_last_turn: 마지막 턴 여부

        Returns:
            DialogueOutput (LLM 생성 결과)
        """
        # 프롬프트 생성
        speaker_order = get_random_speaker_order()
        system_prompt, user_prompt = build_tikitaka_prompt(
            topic=topic,
            eastern_context=self._context_to_string(eastern_context),
            western_context=self._context_to_string(western_context),
            mode=mode.value,
            speaker_order=speaker_order,
            is_first_turn=is_first_turn,
            is_last_turn=is_last_turn,
        )

        # LLM 호출
        try:
            result = await self._call_llm_structured(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=1000,
                temperature=0.8,
            )
            return result

        except Exception as e:
            logger.warning(
                "llm_dialogue_fallback",
                error=str(e),
                mode=mode.value,
            )
            # 폴백 응답
            return self._create_fallback_dialogue(mode, is_last_turn)

    async def _call_llm_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.8,
        max_retries: int = 2,
    ) -> DialogueOutput:
        """구조화된 LLM API 호출"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        last_error: Exception | None = None

        for attempt in range(max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(
                        self.chat_url,
                        json={
                            "model": self.model,
                            "messages": messages,
                            "max_tokens": max_tokens,
                            "temperature": temperature + (attempt * 0.1),
                            "top_p": 0.8,
                            "top_k": 20,
                            "presence_penalty": 1.5,
                            "response_format": {"type": "json_object"},
                        },
                    )
                    response.raise_for_status()
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]

                    # <think> 태그 제거 (Qwen3)
                    if "<think>" in content:
                        content = content.split("</think>")[-1].strip()

                    # Pydantic 검증
                    result = DialogueOutput.model_validate_json(content)

                    logger.info(
                        "llm_dialogue_success",
                        attempt=attempt + 1,
                        lines_count=len(result.lines),
                    )
                    return result

            except httpx.TimeoutException as e:
                logger.warning("llm_timeout", attempt=attempt + 1)
                last_error = e
            except Exception as e:
                logger.warning(
                    "llm_dialogue_error",
                    attempt=attempt + 1,
                    error=str(e),
                )
                last_error = e

        # 모든 재시도 실패
        logger.error("llm_dialogue_failed", error=str(last_error))
        raise last_error or RuntimeError("LLM 호출 실패")

    def _create_fallback_dialogue(
        self,
        mode: DialogueMode,
        is_last_turn: bool = False,
    ) -> DialogueOutput:
        """폴백 대화 생성"""
        if is_last_turn:
            return DialogueOutput(
                lines=[
                    DialogueLine(
                        speaker="WEST",
                        text=(
                            "오늘 소이설이랑 많이 다투었지만... 당신의 미래는 밝아요! "
                            "별들이 응원하고 있어요!"
                        ),
                        emotion_code=EmotionCode.WARM,
                        emotion_intensity=0.8,
                    ),
                    DialogueLine(
                        speaker="EAST",
                        text=(
                            "스텔라와 의견이 달랐으나 귀하의 앞날을 바라는 마음은 같소. "
                            "좋은 기운이 함께하리다."
                        ),
                        emotion_code=EmotionCode.ENCOURAGING,
                        emotion_intensity=0.7,
                    ),
                ],
                user_prompt_text="세션이 종료되었습니다.",
            )

        if mode == DialogueMode.CONSENSUS:
            return DialogueOutput(
                lines=[
                    DialogueLine(
                        speaker="EAST",
                        text="귀하의 운세를 살펴보니, 좋은 기운이 감돌고 있소.",
                        emotion_code=EmotionCode.THOUGHTFUL,
                        emotion_intensity=0.7,
                    ),
                    DialogueLine(
                        speaker="WEST",
                        text="어머! 저도 똑같이 봤어요! 이건 정말 확실한 거예요!",
                        emotion_code=EmotionCode.SURPRISED,
                        emotion_intensity=0.8,
                    ),
                ],
                user_prompt_text="둘 다 같은 의견이네요! 더 궁금한 게 있으세요?",
            )

        return DialogueOutput(
            lines=[
                DialogueLine(
                    speaker="EAST",
                    text="귀하의 사주를 살펴보니, 흥미로운 기운이 흐르고 있소.",
                    emotion_code=EmotionCode.THOUGHTFUL,
                    emotion_intensity=0.7,
                ),
                DialogueLine(
                    speaker="WEST",
                    text="잠깐요! 제 분석은 조금 달라요. 별자리가 다른 이야기를 하고 있거든요!",
                    emotion_code=EmotionCode.PLAYFUL,
                    emotion_intensity=0.6,
                ),
            ],
            user_prompt_text="누구 해석이 더 와닿으시나요?",
        )

    # ============================================================
    # TurnResponse JSON 조립
    # ============================================================

    def build_turn_response(
        self,
        session: TikitakaSessionState,
        dialogue_output: DialogueOutput,
    ) -> TurnResponse:
        """TurnResponse JSON 구조 조립

        Args:
            session: 세션 상태
            dialogue_output: LLM 대화 생성 결과

        Returns:
            완성된 TurnResponse
        """
        turn_id = session.get_next_turn_id()
        now = datetime.now(UTC)

        # Bubbles 생성
        bubbles: list[Bubble] = []
        for idx, line in enumerate(dialogue_output.lines):
            bubble = Bubble(
                bubble_id=session.get_bubble_id(idx),
                speaker=Speaker(line.speaker),
                text=line.text,
                emotion=Emotion(
                    code=line.emotion_code,
                    intensity=line.emotion_intensity,
                ),
                user_input_ref=session.last_prompt_id if idx == 0 else None,
                timestamp=now.isoformat().replace("+00:00", "Z"),
            )
            bubbles.append(bubble)

        # TurnEnd 생성
        turn_end = self._build_turn_end(
            session=session,
            dialogue_output=dialogue_output,
            turn_id=turn_id,
        )

        # Meta 생성
        meta = Meta(
            current_turn=turn_id,
            base_turns=session.base_turns,
            max_turns=session.max_turns,
            is_premium=session.is_premium,
            category=FortuneCategory(session.category),
        )

        return TurnResponse(
            session_id=session.session_id,
            turn_id=turn_id,
            bubbles=bubbles,
            turn_end=turn_end,
            meta=meta,
        )

    def _build_turn_end(
        self,
        session: TikitakaSessionState,
        dialogue_output: DialogueOutput,
        turn_id: int,
    ) -> TurnEnd:
        """TurnEnd 생성 (await_user_input 또는 completed)"""
        # 세션 완료 조건 체크
        # 기본 턴 수 도달 시 (프리미엄 아니면) 완료
        should_complete = False
        if not session.is_premium and turn_id >= session.base_turns:
            should_complete = True
        elif session.is_premium and turn_id >= session.max_turns:
            should_complete = True

        if should_complete:
            return self._build_completed_turn_end(session)

        # await_user_input
        prompt_id = session.get_prompt_id()
        return TurnEndAwaitUserInput(
            user_prompt=UserPrompt(
                prompt_id=prompt_id,
                text=dialogue_output.user_prompt_text,
                input_schema=InputSchema(
                    type=InputType.TEXT,
                    placeholder="예: 연애운이 궁금해요",
                    validation=InputValidation(
                        required=False,
                        max_length=200,
                    ),
                ),
            )
        )

    def _build_completed_turn_end(
        self,
        session: TikitakaSessionState,
    ) -> TurnEndCompleted:
        """세션 완료 TurnEnd 생성"""
        # 요약 생성 (컨텍스트 기반)
        summary = []
        if session.eastern_context:
            summary.append(
                SummaryItem(
                    speaker=Speaker.EAST,
                    key_point=(
                        f"{session.eastern_context.day_master} 일간으로 "
                        f"{session.eastern_context.strength}"
                    ),
                )
            )
        if session.western_context:
            summary.append(
                SummaryItem(
                    speaker=Speaker.WEST,
                    key_point=(
                        f"{session.western_context.sun_sign} 태양으로 "
                        f"{session.western_context.dominant_element} 원소 강조"
                    ),
                )
            )

        # 기본 요약 (컨텍스트 없는 경우)
        if not summary:
            summary = [
                SummaryItem(speaker=Speaker.EAST, key_point="동양 사주 분석 완료"),
                SummaryItem(speaker=Speaker.WEST, key_point="서양 점성술 분석 완료"),
            ]

        # 다음 단계 제안
        next_steps = [
            "오늘의 행운 아이템 확인하기",
            "다른 주제로 운세 보기",
            "친구에게 공유하기",
        ]

        # 업그레이드 훅
        if session.is_premium:
            upgrade_hook = UpgradeHook(enabled=False)
        else:
            upgrade_hook = UpgradeHook(
                enabled=True,
                message=(
                    "소이설과 스텔라의 더 깊은 분석을 원하시나요? "
                    "프리미엄으로 무제한 상담이 가능해요!"
                ),
                cta_label="프리미엄 시작하기",
                cta_action="upgrade_premium",
            )

        return TurnEndCompleted(
            closure=Closure(
                summary=summary,
                next_steps=next_steps,
                upgrade_hook=upgrade_hook,
            )
        )

    # ============================================================
    # 메인 생성 메서드
    # ============================================================

    async def generate_turn(
        self,
        session: TikitakaSessionState,
        eastern: EasternFortuneResponse,
        western: WesternFortuneDataV2,
        topic: str = "total",
        force_mode: DialogueMode | None = None,
    ) -> TurnResponse:
        """턴 응답 생성 (메인 엔트리 포인트)

        Args:
            session: 세션 상태
            eastern: 동양 사주 분석 결과
            western: 서양 점성술 분석 결과
            topic: 주제 (total, love, wealth, career, health)
            force_mode: 강제 모드 (테스트용)

        Returns:
            완성된 TurnResponse
        """
        # 컨텍스트 포맷팅
        eastern_ctx = self.format_eastern_context(eastern)
        western_ctx = self.format_western_context(western)

        # 세션에 컨텍스트 캐싱
        session.eastern_context = eastern_ctx
        session.western_context = western_ctx

        # 모드 결정
        mode = force_mode or self.decide_battle_or_consensus()

        # 턴 정보
        turn_id = session.get_next_turn_id()
        is_first_turn = turn_id == 1
        is_last_turn = session.should_complete()

        logger.info(
            "generate_turn_start",
            session_id=session.session_id,
            turn_id=turn_id,
            mode=mode.value,
            topic=topic,
            is_first_turn=is_first_turn,
            is_last_turn=is_last_turn,
        )

        # LLM 대화 생성
        dialogue_output = await self.generate_dialogues(
            topic=topic,
            eastern_context=eastern_ctx,
            western_context=western_ctx,
            mode=mode,
            is_first_turn=is_first_turn,
            is_last_turn=is_last_turn,
        )

        # TurnResponse 조립
        response = self.build_turn_response(
            session=session,
            dialogue_output=dialogue_output,
        )

        # 세션 상태 업데이트
        session.current_turn = turn_id
        session.category = topic
        if response.turn_end.type == "await_user_input":
            session.last_prompt_id = response.turn_end.user_prompt.prompt_id

        logger.info(
            "generate_turn_complete",
            session_id=session.session_id,
            turn_id=turn_id,
            bubbles_count=len(response.bubbles),
            turn_end_type=response.turn_end.type,
        )

        return response
