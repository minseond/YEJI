"""불완전 문장 감지 및 재생성 로직 테스트

detect_incomplete_sentence, _ensure_sentence_completion,
_build_continuation_prompt, _merge_continuation 함수의 테스트 케이스입니다.

테스트 시나리오:
- 완전한 문장 감지
- 불완전 문장 감지 (종결 어미 없음, 괄호 미닫힘, 짧은 문장 등)
- continuation 프롬프트 생성
- 원본과 continuation 병합
"""

import pytest

from yeji_ai.services.llm_interpreter import (
    SENTENCE_ENDINGS,
    _build_continuation_prompt,
    _ensure_sentence_completion,
    _merge_continuation,
    detect_incomplete_sentence,
)


# ============================================================
# detect_incomplete_sentence 함수 테스트
# ============================================================


class TestDetectIncompleteSentence:
    """불완전 문장 감지 함수 테스트"""

    # ------------------------------------------------------------
    # 완전한 문장 케이스
    # ------------------------------------------------------------

    def test_마침표로_끝나는_완전한_문장(self) -> None:
        """마침표로 끝나는 완전한 문장 감지"""
        # Arrange
        text = "오늘 운세는 좋습니다."

        # Act
        is_incomplete, reason = detect_incomplete_sentence(text)

        # Assert
        assert is_incomplete is False
        assert reason == ""

    def test_하오체로_끝나는_완전한_문장(self) -> None:
        """하오체 '~오'로 끝나는 완전한 문장 감지"""
        # Arrange
        text = "귀하의 운세는 좋소이오"

        # Act
        is_incomplete, reason = detect_incomplete_sentence(text)

        # Assert
        assert is_incomplete is False
        assert reason == ""

    def test_해요체로_끝나는_완전한_문장(self) -> None:
        """해요체 '~요'로 끝나는 완전한 문장 감지"""
        # Arrange
        text = "당신의 운세는 아주 좋아요"

        # Act
        is_incomplete, reason = detect_incomplete_sentence(text)

        # Assert
        assert is_incomplete is False
        assert reason == ""

    def test_다양한_종결_어미_완전한_문장(self) -> None:
        """다양한 종결 어미로 끝나는 완전한 문장들"""
        # Arrange
        complete_texts = [
            "오늘 하루도 좋은 일이 있을 것이다.",  # ~다
            "좋은 기운이 함께하오.",  # ~오
            "행운이 함께할 것이소.",  # ~소
            "정말 좋은 하루가 될 거예요!",  # ~요!
            "어떻게 생각하시오?",  # ~오?
            "좋은 날이 되길 바라오~",  # ~오~
            "참으로 좋은 인연이구려",  # ~구려
        ]

        for text in complete_texts:
            # Act
            is_incomplete, reason = detect_incomplete_sentence(text)

            # Assert
            assert is_incomplete is False, f"'{text}'가 불완전으로 감지됨: {reason}"

    # ------------------------------------------------------------
    # 불완전 문장 케이스 - 종결 어미 없음
    # ------------------------------------------------------------

    def test_종결_어미_없는_불완전_문장(self) -> None:
        """종결 어미가 없는 불완전 문장 감지"""
        # Arrange
        text = "오늘 운세는 아주 좋은 편이"

        # Act
        is_incomplete, reason = detect_incomplete_sentence(text)

        # Assert
        assert is_incomplete is True
        assert reason == "no_ending"

    def test_조사로_끝나는_불완전_문장(self) -> None:
        """조사로 끝나는 불완전 문장 감지"""
        # Arrange
        incomplete_texts = [
            "오늘 운세는",
            "좋은 기운이 함께",
            "귀하의 운세를",
            "목(木) 기운과",
        ]

        for text in incomplete_texts:
            # Act
            is_incomplete, reason = detect_incomplete_sentence(text)

            # Assert
            assert is_incomplete is True, f"'{text}'가 완전으로 감지됨"
            assert reason == "no_ending"

    # ------------------------------------------------------------
    # 불완전 문장 케이스 - 빈 텍스트
    # ------------------------------------------------------------

    def test_빈_문자열(self) -> None:
        """빈 문자열 감지"""
        # Act
        is_incomplete, reason = detect_incomplete_sentence("")

        # Assert
        assert is_incomplete is True
        assert reason == "empty_text"

    def test_공백만_있는_문자열(self) -> None:
        """공백만 있는 문자열 감지"""
        # Act
        is_incomplete, reason = detect_incomplete_sentence("   \n\t  ")

        # Assert
        assert is_incomplete is True
        assert reason == "whitespace_only"

    # ------------------------------------------------------------
    # 불완전 문장 케이스 - 괄호 미닫힘
    # ------------------------------------------------------------

    def test_열린_괄호_미닫힘(self) -> None:
        """열린 괄호가 닫히지 않은 문장 감지"""
        # Arrange: 괄호가 열려있고 종결 어미가 있는 경우
        text = "오늘 운세는 좋습니다 (특히 재물운이 좋소"

        # Act
        is_incomplete, reason = detect_incomplete_sentence(text)

        # Assert
        assert is_incomplete is True
        assert reason == "unclosed_bracket"

    def test_열린_대괄호_미닫힘(self) -> None:
        """열린 대괄호가 닫히지 않은 문장 감지"""
        # Arrange: 대괄호가 열려있고 종결 어미가 있는 경우
        text = "오늘의 행운 아이템 [초록색 물건이오"

        # Act
        is_incomplete, reason = detect_incomplete_sentence(text)

        # Assert
        assert is_incomplete is True
        assert reason == "unclosed_bracket"

    def test_괄호가_올바르게_닫힌_문장(self) -> None:
        """괄호가 올바르게 닫힌 완전한 문장"""
        # Arrange
        text = "오늘 운세는 좋습니다 (특히 재물운이 좋아요)."

        # Act
        is_incomplete, reason = detect_incomplete_sentence(text)

        # Assert
        assert is_incomplete is False
        assert reason == ""

    # ------------------------------------------------------------
    # 불완전 문장 케이스 - 짧은 마지막 문장
    # ------------------------------------------------------------

    def test_마지막_문장이_너무_짧음(self) -> None:
        """마지막 문장이 3자 이하인 경우 감지 (여러 문장일 때)"""
        # Arrange: 여러 문장이고 마지막 문장이 3자 이하
        text = "오늘 운세는 좋습니다. 네."

        # Act
        is_incomplete, reason = detect_incomplete_sentence(text)

        # Assert
        assert is_incomplete is True
        assert reason == "short_last_sentence"

    def test_마지막_문장이_적절한_길이(self) -> None:
        """마지막 문장이 4자 이상인 경우 완전"""
        # Arrange
        text = "오늘 운세는 좋습니다. 행운을 빕니다."

        # Act
        is_incomplete, reason = detect_incomplete_sentence(text)

        # Assert
        assert is_incomplete is False
        assert reason == ""

    def test_단일_문장은_길이_검사_안함(self) -> None:
        """단일 문장은 짧아도 완전으로 판정"""
        # Arrange: 단일 문장 (이전 종결 부호 없음)
        text = "좋다."

        # Act
        is_incomplete, reason = detect_incomplete_sentence(text)

        # Assert
        assert is_incomplete is False
        assert reason == ""

    # ------------------------------------------------------------
    # 불완전 문장 케이스 - 불완전 접속사
    # ------------------------------------------------------------

    def test_접속사로_끝나는_불완전_문장(self) -> None:
        """접속사로 끝나는 불완전 문장 감지"""
        # Arrange: 접속사로 끝나는 불완전 문장들
        incomplete_connectors = [
            "오늘 운세는 좋습니다. 그리고.",
            "오늘 운세는 좋습니다. 하지만.",
            "오늘 운세는 좋습니다. 그러나.",
            "오늘 운세는 좋습니다. 따라서.",
            "오늘 운세는 좋습니다. 특히.",
        ]

        for text in incomplete_connectors:
            # Act
            is_incomplete, reason = detect_incomplete_sentence(text)

            # Assert: 불완전으로 감지 (접속사 또는 짧은 문장)
            assert is_incomplete is True, f"'{text}'가 완전으로 감지됨"
            # 접속사 패턴은 short_last_sentence보다 먼저 검사됨
            assert reason in ("incomplete_connector", "short_last_sentence")


# ============================================================
# _ensure_sentence_completion 함수 테스트
# ============================================================


class TestEnsureSentenceCompletion:
    """문장 완결성 보장 함수 테스트"""

    def test_이미_완전한_문장은_그대로(self) -> None:
        """이미 완전한 문장은 그대로 반환"""
        # Arrange
        text = "오늘 운세는 좋습니다."

        # Act
        result = _ensure_sentence_completion(text)

        # Assert
        assert result == text

    def test_불완전_문장_잘라내기(self) -> None:
        """불완전한 부분은 잘라내고 마지막 완전 문장까지만 반환"""
        # Arrange
        text = "오늘 운세는 좋습니다. 특히 재물운이"

        # Act
        result = _ensure_sentence_completion(text)

        # Assert
        assert result == "오늘 운세는 좋습니다."

    def test_하오체_종결_어미_인식(self) -> None:
        """하오체 종결 어미 인식"""
        # Arrange
        text = "좋은 기운이 함께하오 그대의"

        # Act
        result = _ensure_sentence_completion(text)

        # Assert
        assert result == "좋은 기운이 함께하오"

    def test_해요체_종결_어미_인식(self) -> None:
        """해요체 종결 어미 인식"""
        # Arrange
        text = "오늘 하루도 좋은 일이 가득해요 특히"

        # Act
        result = _ensure_sentence_completion(text)

        # Assert
        assert result == "오늘 하루도 좋은 일이 가득해요"

    def test_종결_어미_없으면_원본_반환(self) -> None:
        """종결 어미가 전혀 없으면 원본 그대로 반환"""
        # Arrange
        text = "오늘 운세는 아주 좋은 편이"

        # Act
        result = _ensure_sentence_completion(text)

        # Assert
        assert result == text  # 최소 내용 보장

    def test_빈_문자열_처리(self) -> None:
        """빈 문자열 처리"""
        # Act
        result = _ensure_sentence_completion("")

        # Assert
        assert result == ""

    def test_None_처리(self) -> None:
        """None 처리"""
        # Act
        result = _ensure_sentence_completion(None)  # type: ignore

        # Assert
        assert result is None

    def test_여러_문장_중_마지막_불완전_제거(self) -> None:
        """여러 문장 중 마지막 불완전 문장만 제거"""
        # Arrange
        text = "첫 번째 문장입니다. 두 번째 문장이오. 세 번째는 불완전"

        # Act
        result = _ensure_sentence_completion(text)

        # Assert
        assert result == "첫 번째 문장입니다. 두 번째 문장이오."


# ============================================================
# _build_continuation_prompt 함수 테스트
# ============================================================


class TestBuildContinuationPrompt:
    """continuation 프롬프트 생성 함수 테스트"""

    def test_소이설_continuation_프롬프트(self) -> None:
        """소이설 캐릭터용 continuation 프롬프트 생성"""
        # Arrange
        original = "좋은 기운이 함께하오. 특히 재물운이"

        # Act
        prompt = _build_continuation_prompt(original, character="soiseol")

        # Assert
        assert "하오체" in prompt
        assert "재물운이" in prompt
        assert "완성" in prompt

    def test_스텔라_continuation_프롬프트(self) -> None:
        """스텔라 캐릭터용 continuation 프롬프트 생성"""
        # Arrange
        original = "좋은 운세예요. 특히 연애운이"

        # Act
        prompt = _build_continuation_prompt(original, character="stella")

        # Assert
        assert "해요체" in prompt
        assert "연애운이" in prompt
        assert "완성" in prompt

    def test_완전한_문장_뒤_불완전_부분_추출(self) -> None:
        """완전한 문장 뒤의 불완전 부분만 추출"""
        # Arrange
        original = "첫 번째 문장이오. 두 번째는 불완전"

        # Act
        prompt = _build_continuation_prompt(original, character="soiseol")

        # Assert
        assert "두 번째는 불완전" in prompt
        # 첫 번째 문장은 포함되지 않아야 함 (이미 완전)

    def test_종결_어미_없는_경우_전체_텍스트_사용(self) -> None:
        """종결 어미가 없는 경우 전체 텍스트를 불완전 부분으로 사용"""
        # Arrange
        original = "오늘 운세는 아주"

        # Act
        prompt = _build_continuation_prompt(original, character="soiseol")

        # Assert
        assert "오늘 운세는 아주" in prompt


# ============================================================
# _merge_continuation 함수 테스트
# ============================================================


class TestMergeContinuation:
    """원본과 continuation 병합 함수 테스트"""

    def test_완전_문장_뒤에_continuation_추가(self) -> None:
        """완전한 문장 뒤에 continuation 추가"""
        # Arrange
        original = "첫 번째 문장이오. 두 번째는 불완전"
        continuation = "두 번째는 매우 좋소."

        # Act
        result = _merge_continuation(original, continuation)

        # Assert
        assert result == "첫 번째 문장이오. 두 번째는 매우 좋소."

    def test_중복_제거_후_병합(self) -> None:
        """continuation이 불완전 부분을 포함하면 중복 제거"""
        # Arrange
        original = "첫 번째 문장이오. 두 번째는"
        continuation = "두 번째는 정말 좋은 운세이오."

        # Act
        result = _merge_continuation(original, continuation)

        # Assert
        assert "두 번째는 두 번째는" not in result  # 중복 없음
        assert "첫 번째 문장이오." in result

    def test_완전_문장_없으면_continuation으로_대체(self) -> None:
        """완전한 문장이 없으면 continuation으로 대체"""
        # Arrange
        original = "오늘 운세는"
        continuation = "좋은 기운이 함께하오."

        # Act
        result = _merge_continuation(original, continuation)

        # Assert
        assert result == "좋은 기운이 함께하오."

    def test_빈_continuation_처리(self) -> None:
        """빈 continuation은 무시하고 완전 문장만 반환"""
        # Arrange
        original = "첫 번째 문장이오. 불완전"
        continuation = ""

        # Act
        result = _merge_continuation(original, continuation)

        # Assert
        assert result == "첫 번째 문장이오."


# ============================================================
# SENTENCE_ENDINGS 상수 테스트
# ============================================================


class TestSentenceEndings:
    """문장 종결 패턴 상수 테스트"""

    def test_기본_종결_부호_포함(self) -> None:
        """기본 종결 부호 포함 확인"""
        # Assert
        assert "." in SENTENCE_ENDINGS
        assert "!" in SENTENCE_ENDINGS
        assert "?" in SENTENCE_ENDINGS
        assert "~" in SENTENCE_ENDINGS

    def test_한국어_종결_어미_포함(self) -> None:
        """한국어 종결 어미 포함 확인"""
        # Assert
        assert "요" in SENTENCE_ENDINGS  # 해요체
        assert "오" in SENTENCE_ENDINGS  # 하오체
        assert "소" in SENTENCE_ENDINGS  # 하소체
        assert "다" in SENTENCE_ENDINGS  # 합니다체
        assert "구려" in SENTENCE_ENDINGS  # 하오체 변형


# ============================================================
# 통합 테스트
# ============================================================


class TestSentenceCompletionIntegration:
    """문장 완결성 보장 통합 테스트"""

    def test_전체_흐름_감지_후_정리(self) -> None:
        """불완전 감지 -> 문장 정리 전체 흐름"""
        # Arrange
        text = "오늘 하루도 좋은 일이 가득하오. 특히 재물운이 매우"

        # Act
        is_incomplete, reason = detect_incomplete_sentence(text)
        if is_incomplete:
            result = _ensure_sentence_completion(text)
        else:
            result = text

        # Assert
        assert is_incomplete is True
        assert result == "오늘 하루도 좋은 일이 가득하오."

    def test_하오체_문장_연속_처리(self) -> None:
        """하오체 문장 연속 처리"""
        # Arrange
        text = "그대의 사주를 살펴보았소. 목(木) 기운이 강하오. 따라서"

        # Act
        is_incomplete, _ = detect_incomplete_sentence(text)
        result = _ensure_sentence_completion(text)

        # Assert
        assert is_incomplete is True
        assert result == "그대의 사주를 살펴보았소. 목(木) 기운이 강하오."

    def test_해요체_문장_연속_처리(self) -> None:
        """해요체 문장 연속 처리"""
        # Arrange
        text = "당신의 별자리를 분석했어요. 불 원소가 강해요. 그래서"

        # Act
        is_incomplete, _ = detect_incomplete_sentence(text)
        result = _ensure_sentence_completion(text)

        # Assert
        assert is_incomplete is True
        assert result == "당신의 별자리를 분석했어요. 불 원소가 강해요."
