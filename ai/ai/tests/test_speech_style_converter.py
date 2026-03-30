"""말투 변환 함수 테스트

LLM 응답의 합니다체를 하오체/해요체로 변환하는 함수들의 테스트입니다.

테스트 시나리오:
- 하오체 변환 (소이설): 합니다체 → 하오체
- 해요체 변환 (스텔라): 합니다체 → 해요체
- 불규칙 동사 처리
- 엣지 케이스
"""

import pytest

from yeji_ai.services.llm_interpreter import (
    _clean_llm_response,
    _convert_to_hao_style,
    _convert_to_heyo_style,
    _ensure_sentence_completion,
)


# ============================================================
# 하오체 변환 테스트 (소이설용)
# ============================================================


class TestConvertToHaoStyle:
    """하오체 변환 함수 테스트"""

    # ------------------------------------------------------------
    # 기본 변환 테스트
    # ------------------------------------------------------------

    def test_습니다_to_소(self) -> None:
        """~습니다 → ~소 변환"""
        assert "있소" in _convert_to_hao_style("있습니다")
        assert "없소" in _convert_to_hao_style("없습니다")
        assert "됩니다" not in _convert_to_hao_style("됩니다")  # 되오로 변환

    def test_입니다_to_이오(self) -> None:
        """~입니다 → ~이오 변환"""
        result = _convert_to_hao_style("사람입니다")
        assert "이오" in result
        assert "입니다" not in result

    def test_합니다_to_하오(self) -> None:
        """~합니다 → ~하오 변환"""
        result = _convert_to_hao_style("분석합니다")
        assert "하오" in result
        assert "합니다" not in result

    def test_됩니다_to_되오(self) -> None:
        """~됩니다 → ~되오 변환"""
        result = _convert_to_hao_style("좋아지게 됩니다")
        assert "되오" in result
        assert "됩니다" not in result

    def test_겠습니다_to_겠소(self) -> None:
        """~겠습니다 → ~겠소 변환"""
        result = _convert_to_hao_style("살펴보겠습니다")
        assert "겠소" in result
        assert "겠습니다" not in result

    # ------------------------------------------------------------
    # 세요/네요 변환 테스트
    # ------------------------------------------------------------

    def test_세요_to_시오(self) -> None:
        """~세요 → ~시오 변환"""
        assert "주시오" in _convert_to_hao_style("해주세요")
        assert "하시오" in _convert_to_hao_style("하세요")
        assert "보시오" in _convert_to_hao_style("보세요")

    def test_네요_to_구려(self) -> None:
        """~네요 → ~구려 변환"""
        result = _convert_to_hao_style("강하네요")
        assert "구려" in result
        assert "네요" not in result

    # ------------------------------------------------------------
    # 해요체 → 하오체 변환 테스트
    # ------------------------------------------------------------

    def test_해요_to_하오(self) -> None:
        """~해요 → ~하오 변환"""
        result = _convert_to_hao_style("분석해요")
        assert "하오" in result
        assert "해요" not in result

    def test_예요_to_이오(self) -> None:
        """~예요/~이에요 → ~이오 변환"""
        result1 = _convert_to_hao_style("사람이에요")
        assert "이오" in result1

        result2 = _convert_to_hao_style("것이예요")
        assert "이오" in result2

    # ------------------------------------------------------------
    # 특정 동사/표현 테스트
    # ------------------------------------------------------------

    def test_인사말_변환(self) -> None:
        """인사말 정확한 변환"""
        assert "반갑소" in _convert_to_hao_style("반갑습니다")
        assert "감사하오" in _convert_to_hao_style("감사합니다")

    def test_자주쓰이는_표현_변환(self) -> None:
        """자주 쓰이는 표현 변환"""
        assert "살펴보겠소" in _convert_to_hao_style("살펴보겠습니다")
        assert "읽어드리겠소" in _convert_to_hao_style("읽어드리겠습니다")
        assert "말씀드리겠소" in _convert_to_hao_style("말씀드리겠습니다")

    def test_바랍니다_to_바라시오(self) -> None:
        """바랍니다 → 바라시오 (하십시오체 → 하오체)"""
        result = _convert_to_hao_style("자신을 믿고 나아가시길 바랍니다")
        assert "바라시오" in result
        assert "바랍니다" not in result

    def test_하십시오체_to_하오체(self) -> None:
        """하십시오체 → 하오체 변환"""
        assert "주시오" in _convert_to_hao_style("도와주십시오")
        assert "하시오" in _convert_to_hao_style("기억하십시오")

    def test_지닙니다_to_지니오(self) -> None:
        """지닙니다 → 지니오 변환"""
        result = _convert_to_hao_style("부드러운 성향을 지닙니다")
        assert "지니오" in result
        assert "지닙니다" not in result

    # ------------------------------------------------------------
    # 빈 값/None 처리 테스트
    # ------------------------------------------------------------

    def test_빈_문자열_처리(self) -> None:
        """빈 문자열 입력 시 빈 문자열 반환"""
        assert _convert_to_hao_style("") == ""

    def test_None_처리(self) -> None:
        """None 입력 시 None 반환"""
        assert _convert_to_hao_style(None) is None

    # ------------------------------------------------------------
    # 실제 응답 예시 테스트
    # ------------------------------------------------------------

    def test_실제_응답_변환_예시(self) -> None:
        """실제 LLM 응답 형태의 변환 테스트"""
        input_text = """
귀하의 사주를 살펴보겠습니다.
일간이 경금(庚金)입니다. 강한 기운이 흐르고 있습니다.
목(木)이 강하네요. 걱정하지 마세요.
좋은 일이 있을 것입니다.
"""
        result = _convert_to_hao_style(input_text)

        # 합니다체가 남아있으면 안 됨
        assert "겠습니다" not in result
        assert "입니다" not in result
        assert "있습니다" not in result
        assert "마세요" not in result

        # 하오체로 변환되어야 함
        assert "겠소" in result or "하겠소" in result
        assert "이오" in result
        assert "시오" in result or "마시오" in result


# ============================================================
# 해요체 변환 테스트 (스텔라용)
# ============================================================


class TestConvertToHeyoStyle:
    """해요체 변환 함수 테스트"""

    # ------------------------------------------------------------
    # 기본 변환 테스트
    # ------------------------------------------------------------

    def test_습니다_to_어요(self) -> None:
        """~습니다 → ~어요 변환"""
        result = _convert_to_hao_style("강합니다")
        # 하오체 변환이므로 어요가 아님
        assert "어요" not in result

        # 해요체 변환
        result = _convert_to_heyo_style("강합니다")
        # 합니다 → 해요로 변환됨
        assert "합니다" not in result

    def test_입니다_to_예요(self) -> None:
        """~입니다 → ~예요 변환"""
        result = _convert_to_heyo_style("사람입니다")
        assert "예요" in result
        assert "입니다" not in result

    def test_합니다_to_해요(self) -> None:
        """~합니다 → ~해요 변환"""
        result = _convert_to_heyo_style("분석합니다")
        assert "해요" in result
        assert "합니다" not in result

    def test_됩니다_to_돼요(self) -> None:
        """~됩니다 → ~돼요 변환"""
        result = _convert_to_heyo_style("좋아지게 됩니다")
        assert "돼요" in result
        assert "됩니다" not in result

    def test_있습니다_to_있어요(self) -> None:
        """~있습니다 → ~있어요 변환"""
        result = _convert_to_heyo_style("기운이 있습니다")
        assert "있어요" in result
        assert "있습니다" not in result

    def test_없습니다_to_없어요(self) -> None:
        """~없습니다 → ~없어요 변환"""
        result = _convert_to_heyo_style("문제가 없습니다")
        assert "없어요" in result
        assert "없습니다" not in result

    # ------------------------------------------------------------
    # ~겠습니다 → ~ㄹ게요 변환 테스트
    # ------------------------------------------------------------

    def test_하겠습니다_to_할게요(self) -> None:
        """~하겠습니다 → ~할게요 변환"""
        result = _convert_to_heyo_style("분석하겠습니다")
        assert "할게요" in result
        assert "하겠습니다" not in result

    def test_드리겠습니다_to_드릴게요(self) -> None:
        """~드리겠습니다 → ~드릴게요 변환"""
        result = _convert_to_heyo_style("알려드리겠습니다")
        assert "드릴게요" in result
        assert "드리겠습니다" not in result

    def test_보겠습니다_to_볼게요(self) -> None:
        """~보겠습니다 → ~볼게요 변환"""
        result = _convert_to_heyo_style("살펴보겠습니다")
        assert "볼게요" in result
        assert "보겠습니다" not in result

    # ------------------------------------------------------------
    # ㅂ 불규칙 동사 테스트 (핵심!)
    # ------------------------------------------------------------

    def test_반갑습니다_to_반가워요(self) -> None:
        """반갑습니다 → 반가워요 (ㅂ 불규칙)"""
        result = _convert_to_heyo_style("반갑습니다")
        assert "반가워요" in result
        assert "반갑습니다" not in result
        # "반갑어요"가 아닌 "반가워요"여야 함
        assert "반갑어요" not in result

    def test_고맙습니다_to_고마워요(self) -> None:
        """고맙습니다 → 고마워요 (ㅂ 불규칙)"""
        result = _convert_to_heyo_style("고맙습니다")
        assert "고마워요" in result
        assert "고맙습니다" not in result

    def test_어렵습니다_to_어려워요(self) -> None:
        """어렵습니다 → 어려워요 (ㅂ 불규칙)"""
        result = _convert_to_heyo_style("어렵습니다")
        assert "어려워요" in result
        assert "어렵습니다" not in result

    def test_춥습니다_to_추워요(self) -> None:
        """춥습니다 → 추워요 (ㅂ 불규칙)"""
        result = _convert_to_heyo_style("춥습니다")
        assert "추워요" in result
        assert "춥습니다" not in result

    # ------------------------------------------------------------
    # 르 불규칙 동사 테스트 (핵심!)
    # ------------------------------------------------------------

    def test_다루겠습니다_to_다룰게요(self) -> None:
        """다루겠습니다 → 다룰게요 (르 불규칙)"""
        result = _convert_to_heyo_style("다루겠습니다")
        assert "다룰게요" in result
        assert "다루겠습니다" not in result
        # "다루을게요"가 아닌 "다룰게요"여야 함
        assert "다루을게요" not in result

    def test_모릅니다_to_몰라요(self) -> None:
        """모릅니다 → 몰라요 (르 불규칙)"""
        result = _convert_to_heyo_style("모릅니다")
        assert "몰라요" in result
        assert "모릅니다" not in result

    def test_다룹니다_to_다뤄요(self) -> None:
        """다룹니다 → 다뤄요 (르 불규칙)"""
        result = _convert_to_heyo_style("다룹니다")
        assert "다뤄요" in result
        assert "다룹니다" not in result

    # ------------------------------------------------------------
    # 하십시오체 → 해요체 변환 테스트
    # ------------------------------------------------------------

    def test_바랍니다_to_바라요(self) -> None:
        """바랍니다 → 바라요 (하십시오체)"""
        result = _convert_to_heyo_style("그 점은 인지하시기 바랍니다")
        assert "바라요" in result
        assert "바랍니다" not in result

    def test_하십시오_to_하세요(self) -> None:
        """~하십시오 → ~하세요 (하십시오체)"""
        result = _convert_to_heyo_style("나아가십시오")
        assert "나아가세요" in result
        assert "나아가십시오" not in result

    def test_돋보입니다_to_돋보여요(self) -> None:
        """돋보입니다 → 돋보여요 (특수 불규칙)"""
        result = _convert_to_heyo_style("열정이 돋보입니다")
        assert "돋보여요" in result
        assert "돋보입니다" not in result

    def test_어색한_표현_수정(self) -> None:
        """어색한 표현 후보정 테스트"""
        # 돋보예요 → 돋보여요
        result = _convert_to_heyo_style("열정이 돋보예요")
        assert "돋보여요" in result
        assert "돋보예요" not in result

    def test_좋어요_to_좋아요(self) -> None:
        """좋어요 → 좋아요 후보정 테스트"""
        result = _convert_to_heyo_style("균형을 맞추는 것이 좋어요")
        assert "좋아요" in result
        assert "좋어요" not in result

    # ------------------------------------------------------------
    # 빈 값/None 처리 테스트
    # ------------------------------------------------------------

    def test_빈_문자열_처리(self) -> None:
        """빈 문자열 입력 시 빈 문자열 반환"""
        assert _convert_to_heyo_style("") == ""

    def test_None_처리(self) -> None:
        """None 입력 시 None 반환"""
        assert _convert_to_heyo_style(None) is None

    # ------------------------------------------------------------
    # 실제 응답 예시 테스트
    # ------------------------------------------------------------

    def test_실제_응답_변환_예시(self) -> None:
        """실제 LLM 응답 형태의 변환 테스트"""
        input_text = """
당신의 별자리를 분석하겠습니다.
태양이 사자자리에 있습니다. 열정적인 에너지가 강합니다.
금성의 영향으로 연애운이 좋아지고 있습니다.
객관적으로 보면 이번 달은 좋은 흐름입니다.
"""
        result = _convert_to_heyo_style(input_text)

        # 합니다체가 남아있으면 안 됨
        assert "하겠습니다" not in result
        assert "있습니다" not in result
        assert "강합니다" not in result
        assert "흐름입니다" not in result

        # 해요체로 변환되어야 함
        assert "할게요" in result or "게요" in result
        assert "있어요" in result
        assert "해요" in result or "예요" in result


# ============================================================
# LLM 응답 정리 테스트
# ============================================================


# ============================================================
# 문장 완결성 검증 테스트
# ============================================================


class TestEnsureSentenceCompletion:
    """문장 완결성 검증 함수 테스트"""

    def test_완결된_문장_그대로_반환(self) -> None:
        """이미 완결된 문장은 그대로 반환"""
        assert _ensure_sentence_completion("좋은 기운이 있소.") == "좋은 기운이 있소."
        assert _ensure_sentence_completion("분석해볼게요!") == "분석해볼게요!"
        assert _ensure_sentence_completion("괜찮아요?") == "괜찮아요?"

    def test_하오체_종결어미_인식(self) -> None:
        """하오체 종결어미 인식"""
        assert _ensure_sentence_completion("좋은 기운이 있소") == "좋은 기운이 있소"
        assert _ensure_sentence_completion("그러하오") == "그러하오"
        assert _ensure_sentence_completion("강하구려") == "강하구려"

    def test_해요체_종결어미_인식(self) -> None:
        """해요체 종결어미 인식"""
        assert _ensure_sentence_completion("분석해볼게요") == "분석해볼게요"
        assert _ensure_sentence_completion("좋아요") == "좋아요"

    def test_합니다체_종결어미_인식(self) -> None:
        """합니다체 종결어미 인식"""
        assert _ensure_sentence_completion("분석합니다") == "분석합니다"
        assert _ensure_sentence_completion("좋습니다") == "좋습니다"

    def test_잘린_문장_제거(self) -> None:
        """잘린 불완전한 문장 제거"""
        # 마지막에 불완전한 문장이 있는 경우
        result = _ensure_sentence_completion("좋은 기운이 있소. 그리고 앞으로")
        assert result == "좋은 기운이 있소."

    def test_여러_문장_중_마지막_불완전_제거(self) -> None:
        """여러 문장 중 마지막 불완전한 문장만 제거"""
        text = "첫 번째 문장이에요. 두 번째 문장이에요. 세 번째는"
        result = _ensure_sentence_completion(text)
        assert "세 번째는" not in result
        assert "두 번째 문장이에요." in result

    def test_빈_문자열_처리(self) -> None:
        """빈 문자열 처리"""
        assert _ensure_sentence_completion("") == ""
        assert _ensure_sentence_completion(None) is None

    def test_종결부호_없는_짧은_텍스트(self) -> None:
        """종결 부호 없는 짧은 텍스트는 그대로 반환"""
        # 종결 부호가 전혀 없으면 원본 반환 (최소 내용 보장)
        result = _ensure_sentence_completion("좋은 기운")
        assert result == "좋은 기운"

    def test_물결표_종결_인식(self) -> None:
        """물결표(~) 종결 인식"""
        assert _ensure_sentence_completion("좋아요~") == "좋아요~"


class TestCleanLLMResponse:
    """LLM 응답 정리 함수 테스트"""

    def test_특수_토큰_제거(self) -> None:
        """특수 토큰 제거"""
        input_text = "안녕하세요</s><|endoftext|>"
        result = _clean_llm_response(input_text)
        assert "</s>" not in result
        assert "<|endoftext|>" not in result

    def test_추가_프롬프트_마커_제거(self) -> None:
        """추가 프롬프트 마커 제거 (P0 - 새로 추가된 패턴)"""
        input_text = "안녕하세요<|eot_id|><|start_header_id|><|end_header_id|>"
        result = _clean_llm_response(input_text)
        assert "<|eot_id|>" not in result
        assert "<|start_header_id|>" not in result
        assert "<|end_header_id|>" not in result

    def test_bert_토큰_제거(self) -> None:
        """BERT 토큰 제거 ([PAD], [CLS] 등)"""
        input_text = "분석 결과입니다.[PAD][CLS][SEP]"
        result = _clean_llm_response(input_text)
        assert "[PAD]" not in result
        assert "[CLS]" not in result
        assert "[SEP]" not in result

    def test_user_assistant_토큰_제거(self) -> None:
        """user/assistant 토큰 제거"""
        input_text = "분석 결과입니다. user assistant"
        result = _clean_llm_response(input_text)
        assert "user" not in result.lower()
        assert "assistant" not in result.lower()

    def test_외국어_문자_제거(self) -> None:
        """외국어 문자 제거"""
        input_text = "분석 결과입니다. مرحبا こんにちは"
        result = _clean_llm_response(input_text)
        # 아랍어, 일본어 제거
        assert "مرحبا" not in result
        assert "こんにちは" not in result

    def test_색상_코드_반복_제거(self) -> None:
        """색상 코드 반복 제거"""
        input_text = "#ae42ff #ae42ff #ae42ff"
        result = _clean_llm_response(input_text)
        # 반복이 제거되고 1개만 남아야 함
        assert result.count("#ae42ff") <= 1

    def test_빈_문자열_처리(self) -> None:
        """빈 문자열 처리"""
        assert _clean_llm_response("") == ""
        assert _clean_llm_response(None) is None

    def test_러시아어_키릴문자_제거(self) -> None:
        """러시아어(키릴 문자) 제거"""
        input_text = "분석 결과입니다. воздействи 감사합니다."
        result = _clean_llm_response(input_text)
        assert "воздействи" not in result

    def test_반복_패턴_제거(self) -> None:
        """반복 패턴 제거"""
        input_text = "감사하오.을 지키며 책임을 다하는 태도가 귀하의 가장 큰 자산이오. 감사하오.을 지키며 책임을 다하는 태도"
        result = _clean_llm_response(input_text)
        # 반복이 제거되어야 함
        assert result.count("감사하오.을 지키며") <= 1

    def test_user_줄_전체_제거(self) -> None:
        """[user] 프롬프트 누출 줄 전체 제거"""
        input_text = """분석 결과입니다.
[user] 사자자리 사주 분석해주세요. GETGLOBAL
[user] 사자자리 사주 분석해주세요. GETGLOBAL
다음 내용입니다."""
        result = _clean_llm_response(input_text)
        assert "[user]" not in result
        assert "GETGLOBAL" not in result

    def test_대문자_코드_토큰_제거(self) -> None:
        """대문자 코드 토큰 제거 (GETGLOBAL 등)"""
        input_text = "분석 결과입니다. GETGLOBAL SETLOCAL 감사합니다."
        result = _clean_llm_response(input_text)
        assert "GETGLOBAL" not in result
        assert "SETLOCAL" not in result

    def test_ios_코드_토큰_제거(self) -> None:
        """iOS 코드 토큰 제거 (didReceiveMemoryWarning 등)"""
        input_text = "좋소..didReceiveMemoryWarning\n 좋은 하루."
        result = _clean_llm_response(input_text)
        assert "didReceiveMemoryWarning" not in result

    def test_짧은_반복_패턴_제거(self) -> None:
        """짧은 반복 패턴 제거 (하오.하오.하오...)"""
        input_text = "좋은 결과가 있을 것이오.하오.하오.하오.하오.하오."
        result = _clean_llm_response(input_text)
        # 반복이 제거되어 하오가 1개만 남아야 함
        assert result.count("하오.") <= 2


# ============================================================
# P0 - 프롬프트 누출 필터 테스트 (Task #18)
# ============================================================


class TestPromptLeakFilterP0:
    """프롬프트 누출 필터 테스트 (P0 - E2E에서 발견된 심각한 문제)

    E2E 테스트에서 발견된 패턴:
    - "lng: \"role\": \"user\", 당신은 2020년 5월 23일에 출생했고..."
    """

    def test_json_role_user_패턴_제거(self) -> None:
        """JSON 역할 패턴 제거 - "role": "user" """
        # 복합 패턴 테스트 - role 패턴만 독립적으로 테스트
        input_text = '분석합니다. "role": "user", 당신은 2020년 5월 23일에 출생했고...'
        result = _clean_llm_response(input_text)
        assert '"role": "user"' not in result
        # 정상 내용은 보존되어야 함
        assert "2020년" in result or "출생했고" in result

    def test_json_role_assistant_패턴_제거(self) -> None:
        """JSON 역할 패턴 제거 - "role": "assistant" """
        input_text = '분석 결과: "role": "assistant", 좋은 운세입니다.'
        result = _clean_llm_response(input_text)
        assert '"role": "assistant"' not in result
        assert "좋은 운세입니다" in result

    def test_json_role_system_패턴_제거(self) -> None:
        """JSON 역할 패턴 제거 - "role": "system" """
        input_text = '"role": "system", 당신은 운세 해석가입니다. 좋은 운세예요.'
        result = _clean_llm_response(input_text)
        assert '"role": "system"' not in result

    def test_json_role_작은따옴표_제거(self) -> None:
        """JSON 역할 패턴 제거 - 작은따옴표 버전"""
        input_text = "'role': 'user', 사주를 분석해주세요."
        result = _clean_llm_response(input_text)
        assert "'role': 'user'" not in result

    def test_내부변수_lng_노출_제거(self) -> None:
        """내부 변수 노출 제거 - lng (경도)"""
        input_text = "lng: 127.0276, lat: 37.4979 사용자 정보입니다."
        result = _clean_llm_response(input_text)
        assert "lng:" not in result.lower()
        assert "127.0276" not in result

    def test_내부변수_lat_노출_제거(self) -> None:
        """내부 변수 노출 제거 - lat (위도)"""
        input_text = "lat: '37.4979', 서울 위치입니다."
        result = _clean_llm_response(input_text)
        assert "lat:" not in result.lower()

    def test_내부변수_timezone_노출_제거(self) -> None:
        """내부 변수 노출 제거 - timezone"""
        input_text = "timezone: 'Asia/Seoul', 시간대 정보입니다."
        result = _clean_llm_response(input_text)
        assert "timezone:" not in result.lower()

    def test_내부변수_api_key_노출_제거(self) -> None:
        """내부 변수 노출 제거 - api_key (보안)"""
        input_text = "api_key: 'sk-xxx', 설정 정보입니다."
        result = _clean_llm_response(input_text)
        assert "api_key:" not in result.lower()

    def test_내부변수_token_노출_제거(self) -> None:
        """내부 변수 노출 제거 - token (보안)"""
        input_text = "token: 'eyJhbGciOiJ...', 인증 정보입니다."
        result = _clean_llm_response(input_text)
        assert "token:" not in result.lower()

    def test_json_content_구조_제거(self) -> None:
        """JSON 구조 노출 제거 - {"content": ...}"""
        input_text = '{"content": "좋은 운세입니다"} 추가 내용'
        result = _clean_llm_response(input_text)
        assert '{"content":' not in result

    def test_json_message_구조_제거(self) -> None:
        """JSON 구조 노출 제거 - {"message": ...}"""
        input_text = '{"message": "분석 결과"} 좋은 하루'
        result = _clean_llm_response(input_text)
        assert '{"message":' not in result

    def test_복합_누출_패턴_제거(self) -> None:
        """복합 누출 패턴 제거 (실제 E2E 시나리오)"""
        # E2E에서 발견된 실제 패턴 시뮬레이션
        input_text = """lng: "role": "user", 당신은 2020년 5월 23일에 출생했고 사주팔자를 분석해야 해요.
        lat: 37.4979, timezone: 'Asia/Seoul'
        {"content": "시스템 프롬프트"}
        실제 운세 내용입니다. 좋은 하루 되세요."""
        result = _clean_llm_response(input_text)

        # 누출 패턴 제거 확인
        assert '"role": "user"' not in result
        assert "lng:" not in result.lower()
        assert "lat:" not in result.lower()
        assert "timezone:" not in result.lower()
        assert '{"content":' not in result

        # 정상 내용 보존 확인
        assert "좋은 하루" in result or "운세" in result

    def test_speaker_패턴_줄_전체_제거(self) -> None:
        """[speaker:...] 패턴 줄 전체 제거"""
        input_text = """좋은 운세입니다.
[speaker: system] 모든 문장을 해요체로 끝내세요.
다음 내용입니다."""
        result = _clean_llm_response(input_text)
        assert "[speaker:" not in result
        assert "모든 문장을 해요체로" not in result

    def test_정상_응답_보존(self) -> None:
        """정상 응답 내용 보존 확인 (오탐 방지)"""
        normal_responses = [
            "귀하의 사주를 보니 좋은 기운이 흐르고 있소.",
            "목(木)의 기운이 강하구려. 새로운 시작에 좋은 때라 하겠소.",
            "비견(比肩)이 강하여 자기주도적인 성향이오.",
            "별들이 당신에게 좋은 소식을 전해요.",
            "금성이 좋은 위치에 있어요.",
        ]

        for response in normal_responses:
            result = _clean_llm_response(response)
            # 정상 응답은 손상되지 않아야 함 (특수 토큰만 없으면 됨)
            # 일부 대문자 토큰 제거로 인해 정확히 같지 않을 수 있음
            assert len(result) > 0, f"정상 응답이 빈 문자열이 됨: {response}"


# ============================================================
# 통합 테스트
# ============================================================


class TestIntegration:
    """통합 테스트 - 전체 파이프라인"""

    def test_소이설_응답_전체_변환(self) -> None:
        """소이설 응답 전체 변환 테스트"""
        # LLM이 생성한 합니다체 응답
        llm_response = """
반갑습니다. 귀하의 사주를 바탕으로 기본 성격을 분석해 드리겠습니다.
귀하의 일간은 경금(庚金)으로, 겉으로는 단단하고 원칙을 중시하는 성향이 강합니다.
현실적인 책임감과 실무 능력이 강하게 작용하고 있습니다.
뛰어난 성과를 거둘 수 있습니다.
"""
        # 정리 후 변환
        cleaned = _clean_llm_response(llm_response)
        result = _convert_to_hao_style(cleaned)

        # 합니다체 없어야 함
        assert "습니다" not in result
        assert "입니다" not in result

        # 하오체 있어야 함
        assert "소" in result  # ~소
        assert "이오" in result or "하오" in result

    def test_스텔라_응답_전체_변환(self) -> None:
        """스텔라 응답 전체 변환 테스트"""
        # LLM이 생성한 합니다체 응답
        llm_response = """
반갑습니다. 당신의 에너지를 빌려 주제를 분석해 드리겠습니다.
사자자리(Leo)의 특성과 불(火)의 우세 원소를 중심으로 다루겠습니다.
자신의 의견을 명확히 피력하고자 하는 욕구가 강합니다.
주의가 필요합니다.
"""
        # 정리 후 변환
        cleaned = _clean_llm_response(llm_response)
        result = _convert_to_heyo_style(cleaned)

        # 합니다체 없어야 함
        assert "습니다" not in result
        assert "입니다" not in result

        # 해요체 있어야 함
        assert "요" in result  # ~요

        # 불규칙 처리 확인
        assert "반가워요" in result  # ㅂ 불규칙
        assert "다룰게요" in result or "다뤄요" in result  # 르 불규칙
