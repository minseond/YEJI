"""티키타카 대화 생성 테스트

TikitakaDialogueGenerator 단위/통합 테스트
"""

import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from yeji_ai.models.fortune.dialogue import (
    DialogueMode,
    DialogueLine,
    DialogueOutput,
    EasternContext,
    TikitakaSessionState,
    WesternContext,
)
from yeji_ai.models.fortune.turn import (
    Bubble,
    EmotionCode,
    FortuneCategory,
    InputType,
    Meta,
    Speaker,
    TurnEndAwaitUserInput,
    TurnEndCompleted,
    TurnResponse,
)
from yeji_ai.services.tikitaka_dialogue_generator import TikitakaDialogueGenerator


# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def generator() -> TikitakaDialogueGenerator:
    """TikitakaDialogueGenerator 인스턴스"""
    return TikitakaDialogueGenerator(
        base_url="http://localhost:8001/v1",
        model="test-model",
    )


@pytest.fixture
def session() -> TikitakaSessionState:
    """테스트 세션 상태"""
    return TikitakaSessionState(
        session_id="test_session_001",
        current_turn=0,
        base_turns=3,
        max_turns=10,
        is_premium=False,
        category="total",
    )


@pytest.fixture
def premium_session() -> TikitakaSessionState:
    """프리미엄 테스트 세션"""
    return TikitakaSessionState(
        session_id="test_premium_001",
        current_turn=0,
        base_turns=3,
        max_turns=30,
        is_premium=True,
        category="total",
    )


@pytest.fixture
def eastern_context() -> EasternContext:
    """동양 사주 컨텍스트"""
    return EasternContext(
        day_master="병화(丙)",
        day_element="火",
        pillars="갑자년 을축월 병인일",
        five_elements="木 20%, 火 40%, 土 15%, 金 10%, 水 15% (강: 火, 약: 金)",
        yin_yang="양 60%, 음 40%",
        strength="밝고 열정적인 성격, 리더십 강함",
        weakness="수(水) 부족으로 휴식 필요",
    )


@pytest.fixture
def western_context() -> WesternContext:
    """서양 점성술 컨텍스트"""
    return WesternContext(
        sun_sign="양자리",
        dominant_element="불",
        overview="리더십과 추진력이 강한 시기입니다.",
    )


@pytest.fixture
def battle_dialogue() -> DialogueOutput:
    """대결 모드 대화 출력"""
    return DialogueOutput(
        lines=[
            DialogueLine(
                speaker="EAST",
                text="귀하의 사주에서 도화살이 보이오. 이성에게 매력이 있으나 조심해야 하오.",
                emotion_code=EmotionCode.THOUGHTFUL,
                emotion_intensity=0.7,
            ),
            DialogueLine(
                speaker="WEST",
                text="잠깐요! 금성이 좋은 위치인데 왜 조심하라는 거예요? 적극적으로 나가도 괜찮아요!",
                emotion_code=EmotionCode.PLAYFUL,
                emotion_intensity=0.6,
            ),
            DialogueLine(
                speaker="EAST",
                text="허, 스텔라는 표면만 보는구려. 사주는 깊은 이치를 읽는 것이오.",
                emotion_code=EmotionCode.CONFIDENT,
                emotion_intensity=0.7,
            ),
        ],
        user_prompt_text="누구 해석이 더 와닿으시나요?",
    )


@pytest.fixture
def consensus_dialogue() -> DialogueOutput:
    """합의 모드 대화 출력"""
    return DialogueOutput(
        lines=[
            DialogueLine(
                speaker="EAST",
                text="귀하의 사주에서 편재가 강하오. 투자에서 횡재수가 보이오.",
                emotion_code=EmotionCode.THOUGHTFUL,
                emotion_intensity=0.7,
            ),
            DialogueLine(
                speaker="WEST",
                text="어머, 소이설! 저도 똑같이 봤어요! 목성이 2하우스에 있어서 금전 행운이 따르는 시기예요!",
                emotion_code=EmotionCode.SURPRISED,
                emotion_intensity=0.8,
            ),
            DialogueLine(
                speaker="EAST",
                text="허, 이건 드문 일이오. 동양과 서양이 같은 곳을 가리키고 있구려.",
                emotion_code=EmotionCode.CONFIDENT,
                emotion_intensity=0.7,
            ),
        ],
        user_prompt_text="둘 다 같은 의견이네요! 더 궁금한 게 있으세요?",
    )


# ============================================================
# Unit Tests - 모델 검증
# ============================================================


class TestTurnResponseModel:
    """TurnResponse 모델 단위 테스트"""

    def test_bubble_creation(self):
        """Bubble 생성 테스트"""
        bubble = Bubble(
            bubble_id="b001",
            speaker=Speaker.EAST,
            text="테스트 메시지입니다.",
            emotion={"code": EmotionCode.THOUGHTFUL, "intensity": 0.7},
            timestamp="2026-01-30T10:00:00Z",
        )

        assert bubble.bubble_id == "b001"
        assert bubble.speaker == Speaker.EAST
        assert bubble.emotion.code == EmotionCode.THOUGHTFUL
        assert bubble.emotion.intensity == 0.7

    def test_bubble_validation_text_length(self):
        """Bubble 텍스트 길이 검증"""
        # 최소 길이 1자
        with pytest.raises(ValueError):
            Bubble(
                bubble_id="b001",
                speaker=Speaker.EAST,
                text="",  # 빈 문자열
                emotion={"code": EmotionCode.NEUTRAL, "intensity": 0.5},
                timestamp="2026-01-30T10:00:00Z",
            )

    def test_emotion_intensity_range(self):
        """Emotion intensity 범위 검증"""
        # 유효 범위 내
        bubble = Bubble(
            bubble_id="b001",
            speaker=Speaker.WEST,
            text="테스트",
            emotion={"code": EmotionCode.WARM, "intensity": 0.0},
            timestamp="2026-01-30T10:00:00Z",
        )
        assert bubble.emotion.intensity == 0.0

        bubble2 = Bubble(
            bubble_id="b002",
            speaker=Speaker.WEST,
            text="테스트",
            emotion={"code": EmotionCode.WARM, "intensity": 1.0},
            timestamp="2026-01-30T10:00:00Z",
        )
        assert bubble2.emotion.intensity == 1.0

        # 범위 초과
        with pytest.raises(ValueError):
            Bubble(
                bubble_id="b003",
                speaker=Speaker.WEST,
                text="테스트",
                emotion={"code": EmotionCode.WARM, "intensity": 1.5},
                timestamp="2026-01-30T10:00:00Z",
            )

    def test_meta_model(self):
        """Meta 모델 테스트"""
        meta = Meta(
            current_turn=1,
            base_turns=3,
            max_turns=10,
            is_premium=False,
            category=FortuneCategory.LOVE,
        )

        assert meta.current_turn == 1
        assert meta.category == FortuneCategory.LOVE

    def test_turn_end_await_user_input(self):
        """TurnEndAwaitUserInput 테스트"""
        turn_end = TurnEndAwaitUserInput(
            user_prompt={
                "prompt_id": "p001",
                "text": "더 궁금한 게 있으세요?",
                "input_schema": {
                    "type": InputType.TEXT,
                    "placeholder": "예: 연애운이 궁금해요",
                    "validation": {"required": False, "max_length": 200},
                },
            }
        )

        assert turn_end.type == "await_user_input"
        assert turn_end.user_prompt.prompt_id == "p001"

    def test_turn_end_completed(self):
        """TurnEndCompleted 테스트"""
        turn_end = TurnEndCompleted(
            closure={
                "summary": [
                    {"speaker": Speaker.EAST, "key_point": "동양 분석 요약"},
                    {"speaker": Speaker.WEST, "key_point": "서양 분석 요약"},
                ],
                "next_steps": ["다음 단계 1", "다음 단계 2"],
                "upgrade_hook": {
                    "enabled": True,
                    "message": "프리미엄으로 업그레이드하세요!",
                    "cta_label": "업그레이드",
                    "cta_action": "upgrade_premium",
                },
            }
        )

        assert turn_end.type == "completed"
        assert turn_end.closure.end_marker == "END_SESSION"
        assert len(turn_end.closure.summary) == 2


# ============================================================
# Unit Tests - 세션 상태
# ============================================================


class TestTikitakaSessionState:
    """세션 상태 단위 테스트"""

    def test_get_next_turn_id(self, session):
        """다음 턴 ID 반환"""
        assert session.get_next_turn_id() == 1

        session.current_turn = 1
        assert session.get_next_turn_id() == 2

    def test_should_complete_free_user(self, session):
        """무료 사용자 세션 완료 조건"""
        session.current_turn = 2
        assert not session.should_complete()

        session.current_turn = 3
        assert session.should_complete()

    def test_should_complete_premium_user(self, premium_session):
        """프리미엄 사용자 세션 완료 조건"""
        premium_session.current_turn = 3
        assert not premium_session.should_complete()

        premium_session.current_turn = 29
        assert not premium_session.should_complete()

        premium_session.current_turn = 30
        assert premium_session.should_complete()

    def test_get_bubble_id(self, session):
        """버블 ID 생성"""
        assert session.get_bubble_id(0) == "b001_0"
        assert session.get_bubble_id(1) == "b001_1"

        session.current_turn = 1
        assert session.get_bubble_id(0) == "b002_0"

    def test_get_prompt_id(self, session):
        """프롬프트 ID 생성"""
        assert session.get_prompt_id() == "p001"

        session.current_turn = 1
        assert session.get_prompt_id() == "p002"


# ============================================================
# Unit Tests - Generator 메서드
# ============================================================


class TestTikitakaDialogueGenerator:
    """TikitakaDialogueGenerator 단위 테스트"""

    def test_decide_battle_or_consensus_distribution(self, generator):
        """대결/합의 모드 분포 테스트 (70:30)"""
        battle_count = 0
        consensus_count = 0
        total = 1000

        for _ in range(total):
            mode = generator.decide_battle_or_consensus()
            if mode == DialogueMode.BATTLE:
                battle_count += 1
            else:
                consensus_count += 1

        # 70~80% 대결, 20~30% 합의 (±10% 허용)
        battle_ratio = battle_count / total
        assert 0.65 <= battle_ratio <= 0.85, f"대결 비율이 범위 밖: {battle_ratio:.2%}"

    def test_build_turn_response_structure(
        self, generator, session, battle_dialogue
    ):
        """TurnResponse 구조 빌드 테스트"""
        response = generator.build_turn_response(
            session=session,
            dialogue_output=battle_dialogue,
        )

        # 기본 구조 검증
        assert response.session_id == "test_session_001"
        assert response.turn_id == 1
        assert len(response.bubbles) == 3

        # Bubble 검증
        assert response.bubbles[0].speaker == Speaker.EAST
        assert response.bubbles[1].speaker == Speaker.WEST
        assert response.bubbles[0].bubble_id == "b001_0"
        assert response.bubbles[1].bubble_id == "b001_1"

        # TurnEnd 검증 (첫 턴이므로 await_user_input)
        assert response.turn_end.type == "await_user_input"
        assert response.turn_end.user_prompt.prompt_id == "p001"

        # Meta 검증
        assert response.meta.current_turn == 1
        assert response.meta.is_premium is False

    def test_build_turn_response_last_turn_free(
        self, generator, session, battle_dialogue
    ):
        """무료 사용자 마지막 턴 - completed 반환"""
        session.current_turn = 2  # 다음이 3번째 턴 (base_turns=3)

        response = generator.build_turn_response(
            session=session,
            dialogue_output=battle_dialogue,
        )

        # 마지막 턴이므로 completed
        assert response.turn_end.type == "completed"
        assert response.turn_end.closure.end_marker == "END_SESSION"
        assert response.turn_end.closure.upgrade_hook.enabled is True

    def test_build_turn_response_last_turn_premium(
        self, generator, premium_session, battle_dialogue
    ):
        """프리미엄 사용자 마지막 턴 - upgrade_hook 비활성"""
        premium_session.current_turn = 29  # 다음이 30번째 턴 (max_turns=30)

        response = generator.build_turn_response(
            session=premium_session,
            dialogue_output=battle_dialogue,
        )

        assert response.turn_end.type == "completed"
        assert response.turn_end.closure.upgrade_hook.enabled is False

    def test_fallback_dialogue_battle(self, generator):
        """폴백 대화 생성 (대결 모드)"""
        fallback = generator._create_fallback_dialogue(DialogueMode.BATTLE)

        assert len(fallback.lines) == 2
        assert fallback.lines[0].speaker == "EAST"
        assert fallback.lines[1].speaker == "WEST"
        assert "누구" in fallback.user_prompt_text or "와닿" in fallback.user_prompt_text

    def test_fallback_dialogue_consensus(self, generator):
        """폴백 대화 생성 (합의 모드)"""
        fallback = generator._create_fallback_dialogue(DialogueMode.CONSENSUS)

        assert len(fallback.lines) == 2
        assert "똑같이" in fallback.lines[1].text or "같은" in fallback.user_prompt_text


# ============================================================
# Unit Tests - 컨텍스트 포맷팅
# ============================================================


class TestContextFormatting:
    """컨텍스트 포맷팅 테스트"""

    def test_eastern_context_to_string(self, generator, eastern_context):
        """동양 컨텍스트 문자열 변환"""
        result = generator._context_to_string(eastern_context)

        assert "병화" in result
        assert "火" in result
        assert "오행" in result
        assert "음양" in result

    def test_western_context_to_string(self, generator, western_context):
        """서양 컨텍스트 문자열 변환"""
        result = generator._context_to_string(western_context)

        assert "양자리" in result
        assert "불" in result
        assert "리더십" in result


# ============================================================
# Integration Tests - JSON 검증
# ============================================================


class TestTurnResponseJSONValidation:
    """TurnResponse JSON 검증 테스트"""

    def test_json_serialization(self, generator, session, battle_dialogue):
        """JSON 직렬화 테스트"""
        response = generator.build_turn_response(
            session=session,
            dialogue_output=battle_dialogue,
        )

        # JSON 변환
        json_str = response.model_dump_json()
        data = json.loads(json_str)

        # 필수 필드 존재
        assert "session_id" in data
        assert "turn_id" in data
        assert "bubbles" in data
        assert "turn_end" in data
        assert "meta" in data

        # bubbles 검증
        assert len(data["bubbles"]) >= 1
        for bubble in data["bubbles"]:
            assert "bubble_id" in bubble
            assert "speaker" in bubble
            assert "text" in bubble
            assert "emotion" in bubble
            assert "timestamp" in bubble

    def test_json_round_trip(self, generator, session, battle_dialogue):
        """JSON 왕복 테스트"""
        response = generator.build_turn_response(
            session=session,
            dialogue_output=battle_dialogue,
        )

        # 직렬화 → 역직렬화
        json_str = response.model_dump_json()
        restored = TurnResponse.model_validate_json(json_str)

        assert restored.session_id == response.session_id
        assert restored.turn_id == response.turn_id
        assert len(restored.bubbles) == len(response.bubbles)

    def test_contract_compliance(self, generator, session, consensus_dialogue):
        """Contract 스펙 준수 테스트"""
        response = generator.build_turn_response(
            session=session,
            dialogue_output=consensus_dialogue,
        )

        json_str = response.model_dump_json()
        data = json.loads(json_str)

        # 검증 규칙 체크 (fortune_chat_contract_validation_rules.md 기준)

        # MUST: session_id 존재
        assert data["session_id"], "session_id는 필수"

        # MUST: turn_id >= 1
        assert data["turn_id"] >= 1, "turn_id는 1 이상"

        # MUST: bubbles 최소 1개
        assert len(data["bubbles"]) >= 1, "bubbles는 최소 1개"

        # MUST: speaker enum 유효
        valid_speakers = {"EAST", "WEST"}
        for bubble in data["bubbles"]:
            assert bubble["speaker"] in valid_speakers

        # MUST: emotion.intensity 범위
        for bubble in data["bubbles"]:
            intensity = bubble["emotion"]["intensity"]
            assert 0.0 <= intensity <= 1.0

        # MUST: turn_end.type 상호 배타
        assert data["turn_end"]["type"] in {"await_user_input", "completed"}


# ============================================================
# Integration Tests - LLM 호출 (Mock)
# ============================================================


class TestLLMIntegration:
    """LLM 통합 테스트 (Mock)"""

    @pytest.mark.asyncio
    async def test_generate_dialogues_success(self, generator, eastern_context, western_context):
        """LLM 대화 생성 성공 (Mock)"""
        mock_response = {
            "lines": [
                {
                    "speaker": "EAST",
                    "text": "귀하의 사주를 살펴보니 좋은 기운이 흐르고 있소.",
                    "emotion_code": "THOUGHTFUL",
                    "emotion_intensity": 0.7,
                },
                {
                    "speaker": "WEST",
                    "text": "별들도 당신을 응원하고 있어요!",
                    "emotion_code": "WARM",
                    "emotion_intensity": 0.8,
                },
            ],
            "user_prompt_text": "더 궁금한 게 있으세요?",
        }

        with patch.object(
            generator,
            "_call_llm_structured",
            new_callable=AsyncMock,
            return_value=DialogueOutput.model_validate(mock_response),
        ):
            result = await generator.generate_dialogues(
                topic="total",
                eastern_context=eastern_context,
                western_context=western_context,
                mode=DialogueMode.BATTLE,
            )

            assert len(result.lines) == 2
            assert result.lines[0].speaker == "EAST"
            assert result.lines[1].speaker == "WEST"

    @pytest.mark.asyncio
    async def test_generate_dialogues_fallback(self, generator, eastern_context, western_context):
        """LLM 호출 실패 시 폴백"""
        with patch.object(
            generator,
            "_call_llm_structured",
            new_callable=AsyncMock,
            side_effect=Exception("LLM 연결 실패"),
        ):
            result = await generator.generate_dialogues(
                topic="love",
                eastern_context=eastern_context,
                western_context=western_context,
                mode=DialogueMode.CONSENSUS,
            )

            # 폴백 응답 반환
            assert len(result.lines) >= 2
            assert result.user_prompt_text is not None


# ============================================================
# 대결/합의 비율 통계 테스트
# ============================================================


class TestBattleConsensusRatio:
    """대결/합의 비율 통계 테스트"""

    def test_ratio_over_100_generations(self, generator):
        """100회 생성 시 비율 검증"""
        modes = [generator.decide_battle_or_consensus() for _ in range(100)]

        battle_count = sum(1 for m in modes if m == DialogueMode.BATTLE)
        consensus_count = sum(1 for m in modes if m == DialogueMode.CONSENSUS)

        # 60~85% 대결 (허용 범위)
        battle_ratio = battle_count / 100
        assert 0.60 <= battle_ratio <= 0.85, f"대결 비율: {battle_ratio:.0%}"

        # 15~40% 합의 (허용 범위)
        consensus_ratio = consensus_count / 100
        assert 0.15 <= consensus_ratio <= 0.40, f"합의 비율: {consensus_ratio:.0%}"


# ============================================================
# 개인화 검증 테스트
# ============================================================


class TestPersonalization:
    """개인화 검증 테스트"""

    def test_different_contexts_different_prompts(self, generator):
        """다른 컨텍스트 → 다른 프롬프트"""
        ctx_a = EasternContext(
            day_master="병화(丙)",
            day_element="火",
            pillars="갑자년 을축월 병인일",
            five_elements="火 40%",
            yin_yang="양 70%",
            strength="열정적 리더십",
            weakness="수 부족",
        )

        ctx_b = EasternContext(
            day_master="임수(壬)",
            day_element="水",
            pillars="경자년 신축월 임인일",
            five_elements="水 45%",
            yin_yang="음 65%",
            strength="지혜로움",
            weakness="화 부족",
        )

        str_a = generator._context_to_string(ctx_a)
        str_b = generator._context_to_string(ctx_b)

        # 다른 컨텍스트는 다른 문자열
        assert str_a != str_b
        assert "병화" in str_a
        assert "임수" in str_b
