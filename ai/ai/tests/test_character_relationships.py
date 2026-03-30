"""캐릭터 관계 시스템 테스트

character_relationships.py 모듈의 기능 검증
"""

import pytest

from yeji_ai.prompts.character_relationships import (
    CHARACTER_RELATIONSHIPS,
    EMOTION_TRIGGERS,
    EMOTION_TYPES,
    RELATIONSHIP_TYPES,
    generate_emotional_reaction,
    get_all_relationships_for_character,
    get_conversation_temperature,
    get_emotional_context,
    get_relationship,
    get_relationship_type,
    get_trigger_phrase,
)


class TestRelationshipTypes:
    """관계 타입 정의 테스트"""

    def test_all_relationship_types_defined(self):
        """모든 관계 타입이 정의되어 있는지 확인"""
        expected_types = {"rival", "friend", "mentor", "sibling", "acquaintance", "neutral"}
        assert set(RELATIONSHIP_TYPES.keys()) == expected_types

    def test_all_relationships_have_valid_type(self):
        """모든 관계가 유효한 타입을 가지는지 확인"""
        valid_types = set(RELATIONSHIP_TYPES.keys())
        for key, rel in CHARACTER_RELATIONSHIPS.items():
            assert rel["type"] in valid_types, f"{key}의 type이 유효하지 않음: {rel['type']}"


class TestEmotionTypes:
    """감정 타입 정의 테스트"""

    def test_emotion_types_not_empty(self):
        """감정 타입이 정의되어 있는지 확인"""
        assert len(EMOTION_TYPES) > 0

    def test_all_emotions_in_relationships_are_valid(self):
        """관계에 정의된 모든 감정이 유효한지 확인"""
        valid_emotions = set(EMOTION_TYPES.keys())
        for key, rel in CHARACTER_RELATIONSHIPS.items():
            for emotion in rel.get("emotions", []):
                assert emotion in valid_emotions, f"{key}의 감정이 유효하지 않음: {emotion}"


class TestCharacterRelationships:
    """캐릭터 관계 매트릭스 테스트"""

    def test_main_rivalry_defined(self):
        """메인 라이벌 관계(소이설-스텔라)가 정의되어 있는지 확인"""
        rel = CHARACTER_RELATIONSHIPS.get(("SOISEOL", "STELLA"))
        assert rel is not None
        assert rel["type"] == "rival"
        assert rel["tension"] > 0.5  # 라이벌은 텐션이 높아야 함

    def test_mentor_relationship_defined(self):
        """스승-제자 관계(청운-소이설)가 정의되어 있는지 확인"""
        rel = CHARACTER_RELATIONSHIPS.get(("SOISEOL", "CHEONGWOON"))
        assert rel is not None
        assert rel["type"] == "mentor"
        assert rel["respect"] > 0.8  # 스승에 대한 존경이 높아야 함

    def test_sibling_relationship_defined(self):
        """형제자매 관계(화린-소이설)가 정의되어 있는지 확인"""
        rel = CHARACTER_RELATIONSHIPS.get(("HWARIN", "SOISEOL"))
        assert rel is not None
        assert rel["type"] == "sibling"

    def test_bidirectional_relationships_exist(self):
        """양방향 관계가 모두 정의되어 있는지 확인"""
        # 소이설 -> 스텔라, 스텔라 -> 소이설 모두 존재해야 함
        rel_1 = CHARACTER_RELATIONSHIPS.get(("SOISEOL", "STELLA"))
        rel_2 = CHARACTER_RELATIONSHIPS.get(("STELLA", "SOISEOL"))
        assert rel_1 is not None
        assert rel_2 is not None
        # 양방향 관계가 같은 타입일 필요는 없음 (비대칭 가능)

    def test_all_relationships_have_required_fields(self):
        """모든 관계가 필수 필드를 가지는지 확인"""
        required_fields = {"type", "tension", "respect", "emotions", "dynamic"}
        for key, rel in CHARACTER_RELATIONSHIPS.items():
            for field in required_fields:
                assert field in rel, f"{key}에 필수 필드 누락: {field}"

    def test_tension_and_respect_in_valid_range(self):
        """텐션과 존중 값이 0-1 범위인지 확인"""
        for key, rel in CHARACTER_RELATIONSHIPS.items():
            assert 0 <= rel["tension"] <= 1, f"{key}의 tension이 범위 벗어남"
            assert 0 <= rel["respect"] <= 1, f"{key}의 respect가 범위 벗어남"


class TestGetRelationship:
    """get_relationship 함수 테스트"""

    def test_get_existing_relationship(self):
        """존재하는 관계 조회"""
        rel = get_relationship("SOISEOL", "STELLA")
        assert rel is not None
        assert rel["type"] == "rival"

    def test_get_relationship_case_insensitive(self):
        """대소문자 구분 없이 조회"""
        rel1 = get_relationship("soiseol", "stella")
        rel2 = get_relationship("SOISEOL", "STELLA")
        assert rel1 == rel2

    def test_get_nonexistent_relationship(self):
        """존재하지 않는 관계 조회"""
        rel = get_relationship("SOISEOL", "NONEXISTENT")
        assert rel is None


class TestGetRelationshipType:
    """get_relationship_type 함수 테스트"""

    def test_get_type_for_existing_relationship(self):
        """존재하는 관계의 타입 조회"""
        rel_type = get_relationship_type("SOISEOL", "STELLA")
        assert rel_type == "rival"

    def test_get_type_for_nonexistent_relationship(self):
        """존재하지 않는 관계는 neutral 반환"""
        rel_type = get_relationship_type("SOISEOL", "NONEXISTENT")
        assert rel_type == "neutral"


class TestEmotionTriggers:
    """감정 트리거 테스트"""

    def test_all_situations_defined(self):
        """모든 상황이 정의되어 있는지 확인"""
        expected_situations = {
            "opponent_correct",
            "user_chooses_opponent",
            "debate_win",
            "debate_loss",
            "opponent_praised",
            "both_correct",
        }
        assert set(EMOTION_TRIGGERS.keys()) == expected_situations

    def test_all_relationship_types_covered(self):
        """모든 상황에서 모든 관계 타입이 커버되는지 확인"""
        for situation, emotions_by_type in EMOTION_TRIGGERS.items():
            for rel_type in RELATIONSHIP_TYPES.keys():
                assert rel_type in emotions_by_type, (
                    f"{situation}에 {rel_type} 타입이 없음"
                )


class TestGetEmotionalContext:
    """get_emotional_context 함수 테스트"""

    def test_get_context_for_rival_opponent_correct(self):
        """라이벌이 맞았을 때 감정 컨텍스트"""
        ctx = get_emotional_context("SOISEOL", "STELLA", "opponent_correct")
        assert "emotions" in ctx
        assert "intensity" in ctx
        assert "expressions" in ctx
        # 라이벌이 맞으면 마지못한 인정이 포함되어야 함
        assert "grudging_respect" in ctx["emotions"]

    def test_get_context_for_friend_opponent_correct(self):
        """친구가 맞았을 때 감정 컨텍스트"""
        ctx = get_emotional_context("STELLA", "ELARIA", "opponent_correct")
        # 친구라면 기쁨이 포함되어야 함
        assert "happiness" in ctx["emotions"]

    def test_get_context_for_nonexistent_relationship(self):
        """존재하지 않는 관계의 감정 컨텍스트"""
        ctx = get_emotional_context("SOISEOL", "NONEXISTENT", "opponent_correct")
        assert ctx["emotions"] == ["acceptance"]


class TestGenerateEmotionalReaction:
    """generate_emotional_reaction 함수 테스트"""

    def test_generate_reaction_for_rival(self):
        """라이벌에 대한 감정 반응 생성"""
        reaction = generate_emotional_reaction("SOISEOL", "opponent_correct", "STELLA")
        assert reaction  # 빈 문자열이 아님
        assert "[감정:" in reaction

    def test_generate_reaction_with_high_intensity(self):
        """높은 강도의 감정 반응"""
        reaction = generate_emotional_reaction(
            "SOISEOL", "debate_win", "STELLA", intensity=0.9
        )
        assert "[강도: 강함" in reaction

    def test_generate_reaction_with_low_intensity(self):
        """낮은 강도의 감정 반응"""
        reaction = generate_emotional_reaction(
            "SOISEOL", "debate_win", "STELLA", intensity=0.2
        )
        assert "[강도: 약함" in reaction


class TestGetConversationTemperature:
    """get_conversation_temperature 함수 테스트"""

    def test_rival_debate_temperature(self):
        """라이벌 토론 모드의 온도"""
        temp = get_conversation_temperature("SOISEOL", "STELLA", "debate")
        assert temp["rivalry"] > 0.5  # 라이벌은 경쟁 강도가 높아야 함
        assert temp["warmth"] < 0.5  # 토론에서는 따뜻함이 낮음

    def test_friend_consensus_temperature(self):
        """친구 합의 모드의 온도"""
        temp = get_conversation_temperature("STELLA", "ELARIA", "consensus")
        assert temp["warmth"] > 0.5  # 친구는 따뜻함이 높아야 함
        assert temp["rivalry"] < 0.5  # 합의에서는 경쟁이 낮음

    def test_mentor_temperature(self):
        """스승-제자 관계의 온도"""
        temp = get_conversation_temperature("SOISEOL", "CHEONGWOON", "casual")
        assert temp["formality"] > 0.3  # 스승에게는 격식이 있음
        assert temp["warmth"] > 0.5  # 스승에 대한 정도 있음

    def test_nonexistent_relationship_returns_default(self):
        """존재하지 않는 관계는 기본값 반환"""
        temp = get_conversation_temperature("SOISEOL", "NONEXISTENT", "debate")
        assert "warmth" in temp
        assert "rivalry" in temp
        assert "formality" in temp


class TestGetTriggerPhrase:
    """get_trigger_phrase 함수 테스트"""

    def test_get_existing_trigger_phrase(self):
        """존재하는 트리거 문구 조회"""
        phrase = get_trigger_phrase("SOISEOL", "STELLA", "반박")
        assert phrase is not None
        assert "별자리" in phrase  # 소이설의 반박에는 별자리 언급이 있음

    def test_get_nonexistent_trigger_phrase(self):
        """존재하지 않는 트리거 문구 조회"""
        phrase = get_trigger_phrase("SOISEOL", "STELLA", "없는타입")
        assert phrase is None


class TestGetAllRelationshipsForCharacter:
    """get_all_relationships_for_character 함수 테스트"""

    def test_get_all_relationships_for_soiseol(self):
        """소이설의 모든 관계 조회"""
        rels = get_all_relationships_for_character("SOISEOL")
        assert len(rels) >= 5  # 최소 5명의 다른 캐릭터와 관계
        assert "STELLA" in rels
        assert "CHEONGWOON" in rels

    def test_case_insensitive(self):
        """대소문자 구분 없이 동작"""
        rels1 = get_all_relationships_for_character("soiseol")
        rels2 = get_all_relationships_for_character("SOISEOL")
        assert rels1 == rels2


class TestCharacterPersonasIntegration:
    """character_personas.py 연동 테스트"""

    def test_get_relationship_from_personas(self):
        """character_personas에서 관계 조회"""
        from yeji_ai.prompts.character_personas import get_relationship

        rel = get_relationship("SOISEOL", "STELLA")
        assert rel is not None
        assert rel["type"] == "rival"

    def test_get_emotional_context_from_personas(self):
        """character_personas에서 감정 컨텍스트 조회"""
        from yeji_ai.prompts.character_personas import get_emotional_context

        ctx = get_emotional_context("SOISEOL", "STELLA", "opponent_correct")
        assert "emotions" in ctx

    def test_get_conversation_temperature_from_personas(self):
        """character_personas에서 대화 온도 조회"""
        from yeji_ai.prompts.character_personas import get_conversation_temperature

        temp = get_conversation_temperature("SOISEOL", "STELLA", "debate")
        assert "rivalry" in temp

    def test_generate_emotional_hint_from_personas(self):
        """character_personas에서 감정 힌트 생성"""
        from yeji_ai.prompts.character_personas import generate_emotional_hint

        hint = generate_emotional_hint("SOISEOL", "opponent_correct", "STELLA")
        assert hint
        assert "[감정:" in hint

    def test_build_prompt_with_relationship(self):
        """관계 반영 프롬프트 빌드"""
        from yeji_ai.prompts.character_personas import build_prompt_with_relationship

        system, user = build_prompt_with_relationship(
            char_code="SOISEOL",
            topic="연애운",
            context="병화(丙火) 일간",
            opponent_code="STELLA",
            situation="debate_win",
            debate_mode="battle",
        )

        assert system  # 시스템 프롬프트가 있음
        assert user  # 유저 프롬프트가 있음
        assert "관계 컨텍스트" in user  # 관계 컨텍스트가 포함됨
        assert "텐션" in user  # 텐션 정보가 포함됨
