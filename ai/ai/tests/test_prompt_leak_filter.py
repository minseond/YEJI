"""프롬프트 누출 필터 테스트

PromptLeakFilter 단위 테스트 및 통합 테스트
"""

import pytest

from yeji_ai.services.postprocessor.prompt_leak_filter import (
    PromptLeakFilter,
    detect_prompt_leak,
    filter_prompt_leak,
)


# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def filter_instance() -> PromptLeakFilter:
    """PromptLeakFilter 인스턴스"""
    return PromptLeakFilter()


# ============================================================
# Unit Tests - 브래킷 패턴 탐지
# ============================================================


class TestBracketPatternDetection:
    """[문장 종결 예시] 등 브래킷 패턴 탐지 테스트"""

    def test_detect_sentence_ending_example(self, filter_instance):
        """[문장 종결 예시] 패턴 탐지"""
        text = """좋은 운세입니다.

[문장 종결 예시 - 반드시 이 패턴을 따르세요]
- 있습니다 → 있어요
- 입니다 → 예요

행운을 빕니다."""
        filtered, leaked = filter_instance.filter(text)

        assert leaked is True
        assert "[문장 종결 예시" not in filtered
        assert "→" not in filtered

    def test_detect_correct_sentence_example(self, filter_instance):
        """[올바른 문장 예시] 패턴 탐지"""
        text = """좋은 운세입니다.

[올바른 문장 예시 20개]
1. "안녕하세요! 저는 스텔라예요."
2. "당신의 태양이 사자자리에 있네요."

행운을 빕니다."""
        filtered, leaked = filter_instance.filter(text)

        assert leaked is True
        assert "[올바른 문장 예시" not in filtered

    def test_detect_honorific_pattern(self, filter_instance):
        """[호칭] 패턴 탐지"""
        text = """좋은 운세입니다.

[호칭]
- "귀하" 또는 "그대"를 사용하시오.

행운을 빕니다."""
        filtered, leaked = filter_instance.filter(text)

        assert leaked is True
        assert "[호칭]" not in filtered

    def test_detect_wrong_example(self, filter_instance):
        """[틀린 문장 예시] 패턴 탐지"""
        text = """좋은 운세입니다.

[틀린 문장 예시 10개]
❌ "안녕하십니까" → ✅ "반갑소"

행운을 빕니다."""
        filtered, leaked = filter_instance.filter(text)

        assert leaked is True
        assert "[틀린 문장 예시" not in filtered


# ============================================================
# Unit Tests - XML 태그 패턴 탐지
# ============================================================


class TestXmlPatternDetection:
    """XML 태그 패턴 탐지 테스트"""

    def test_detect_forbidden_tag(self, filter_instance):
        """<forbidden> 태그 탐지"""
        text = "좋은 운세입니다. <forbidden>금지사항 목록</forbidden> 행운을 빕니다."
        filtered, leaked = filter_instance.filter(text)

        assert leaked is True
        assert "<forbidden>" not in filtered
        assert "</forbidden>" not in filtered

    def test_detect_speaking_style_tag(self, filter_instance):
        """<speaking_style> 태그 탐지"""
        text = """좋은 운세입니다.

<speaking_style>
모든 문장을 해요체로 끝내세요.
</speaking_style>

행운을 빕니다."""
        filtered, leaked = filter_instance.filter(text)

        assert leaked is True
        assert "<speaking_style>" not in filtered

    def test_detect_auto_conversion_tag(self, filter_instance):
        """<자동 변환> 태그 탐지"""
        text = """좋은 운세입니다.

<자동 변환>
합니다 → 해요
입니다 → 이에요
</자동 변환>

행운을 빕니다."""
        filtered, leaked = filter_instance.filter(text)

        assert leaked is True
        assert "<자동 변환>" not in filtered


# ============================================================
# Unit Tests - 변환 예시 패턴 탐지
# ============================================================


class TestConversionPatternDetection:
    """변환 예시 패턴 (화살표) 탐지 테스트"""

    def test_detect_arrow_conversion(self, filter_instance):
        """화살표 변환 예시 탐지"""
        text = """좋은 운세입니다.
- 있습니다 → 있어요
- 입니다 → 예요
- 합니다 → 해요
행운을 빕니다."""
        filtered, leaked = filter_instance.filter(text)

        assert leaked is True
        assert "→" not in filtered

    def test_detect_hao_conversion(self, filter_instance):
        """하오체 변환 예시 탐지"""
        text = """좋은 운세입니다.
- 있습니다 → 있소
- 입니다 → 이오
행운을 빕니다."""
        filtered, leaked = filter_instance.filter(text)

        assert leaked is True


# ============================================================
# Unit Tests - 체크박스/경고 패턴 탐지
# ============================================================


class TestCheckboxPatternDetection:
    """체크박스 및 경고 패턴 탐지 테스트"""

    def test_detect_checkbox_pattern(self, filter_instance):
        """체크박스 패턴 탐지"""
        text = """좋은 운세입니다.
✅ 모든 문장을 해요체로 끝내세요!
❌ 합니다체는 절대 사용 금지!
행운을 빕니다."""
        filtered, leaked = filter_instance.filter(text)

        assert leaked is True
        assert "✅" not in filtered
        assert "❌" not in filtered

    def test_detect_warning_pattern(self, filter_instance):
        """경고 패턴 탐지"""
        text = """좋은 운세입니다.
⚠️ 경고: 합니다체를 사용하면 캐릭터 설정 위반이에요!
행운을 빕니다."""
        filtered, leaked = filter_instance.filter(text)

        assert leaked is True
        assert "⚠️ 경고:" not in filtered


# ============================================================
# Unit Tests - 오탐 방지 (False Positive)
# ============================================================


class TestNoFalsePositive:
    """정상 응답에 대한 오탐 없음 테스트"""

    def test_normal_soiseol_response(self, filter_instance):
        """소이설 정상 응답 - 오탐 없음"""
        normal_responses = [
            "귀하의 사주를 보니 좋은 기운이 흐르고 있소.",
            "목(木)의 기운이 강하구려. 새로운 시작에 좋은 때라 하겠소.",
            "비견(比肩)이 강하여 자기주도적인 성향이오.",
            "새옹지마(塞翁之馬)라 하였으니, 지금의 어려움이 전화위복이 될 것이오.",
        ]

        for response in normal_responses:
            filtered, leaked = filter_instance.filter(response)
            assert leaked is False, f"오탐 발생: {response}"
            assert filtered == response

    def test_normal_stella_response(self, filter_instance):
        """스텔라 정상 응답 - 오탐 없음"""
        normal_responses = [
            "별들이 당신에게 좋은 소식을 전해요.",
            "금성이 좋은 위치에 있어요. 인간관계에서 좋은 일이 생길 것 같아요.",
            "불의 원소가 우세해요. 리더십과 추진력이 강해요.",
            "목성의 행운이 함께해요.",
        ]

        for response in normal_responses:
            filtered, leaked = filter_instance.filter(response)
            assert leaked is False, f"오탐 발생: {response}"
            assert filtered == response

    def test_normal_cheongwoon_response(self, filter_instance):
        """청운 정상 응답 - 오탐 없음"""
        normal_responses = [
            "허허, 이 또한 지나가는 바람인 것을...",
            "물은 돌을 거스르지 않고 돌아간다오.",
            "천년을 살아도 배움은 끝이 없다네.",
            "자네의 사주를 살펴보겠소.",
        ]

        for response in normal_responses:
            filtered, leaked = filter_instance.filter(response)
            assert leaked is False, f"오탐 발생: {response}"
            assert filtered == response

    def test_normal_hwarin_response(self, filter_instance):
        """화린 정상 응답 - 오탐 없음"""
        normal_responses = [
            "어머, 귀한 손님이 오셨네요?",
            "세상에 공짜는 없어요.",
            "운세가 궁금하세요? 언니가 봐드릴게요~",
            "재물운이 좋아요~",
        ]

        for response in normal_responses:
            filtered, leaked = filter_instance.filter(response)
            assert leaked is False, f"오탐 발생: {response}"
            assert filtered == response

    def test_response_with_numbers_no_quotes(self, filter_instance):
        """숫자가 포함된 일반 응답 - 오탐 없음"""
        normal_responses = [
            "1월부터 좋은 기운이 시작될 거예요.",
            "3가지 조언을 드릴게요.",
            "10점 만점에 8점이에요.",
        ]

        for response in normal_responses:
            filtered, leaked = filter_instance.filter(response)
            assert leaked is False, f"오탐 발생: {response}"

    def test_response_with_short_quotes(self, filter_instance):
        """짧은 인용문 포함 응답 - 오탐 없음"""
        # 5자 미만 인용문은 예시가 아님
        normal_responses = [
            '별자리가 "좋아"라고 말해요.',
            '"네"라고 대답하세요.',
        ]

        for response in normal_responses:
            filtered, leaked = filter_instance.filter(response)
            assert leaked is False, f"오탐 발생: {response}"


# ============================================================
# Unit Tests - 내용 보존
# ============================================================


class TestContentPreservation:
    """필터링 후 정상 내용 보존 테스트"""

    def test_preserve_content_before_leak(self, filter_instance):
        """누출 전 내용 보존"""
        text = """좋은 운세입니다. 목의 기운이 강해요.

[문장 종결 예시]
- 있습니다 → 있어요

다음에도 찾아와요."""
        filtered, leaked = filter_instance.filter(text)

        assert leaked is True
        assert "좋은 운세입니다" in filtered
        assert "목의 기운이 강해요" in filtered

    def test_preserve_content_after_leak(self, filter_instance):
        """누출 후 내용 보존"""
        text = """[올바른 문장 예시]
1. "예시 문장입니다."

진짜 운세: 좋은 기운이 흐르고 있어요."""
        filtered, leaked = filter_instance.filter(text)

        assert leaked is True
        assert "좋은 기운이 흐르고 있어요" in filtered


# ============================================================
# Unit Tests - 편의 함수
# ============================================================


class TestConvenienceFunctions:
    """편의 함수 테스트"""

    def test_filter_prompt_leak_function(self):
        """filter_prompt_leak 함수 테스트"""
        text = "좋은 운세입니다. [올바른 문장 예시] 내용 행운을 빕니다."
        filtered = filter_prompt_leak(text)

        assert "[올바른 문장 예시]" not in filtered
        assert "좋은 운세입니다" in filtered

    def test_detect_prompt_leak_function(self):
        """detect_prompt_leak 함수 테스트"""
        text = "좋은 운세입니다. [문장 종결 예시] 내용"
        detected = detect_prompt_leak(text)

        assert len(detected) > 0

    def test_detect_no_leak(self):
        """누출 없는 응답 탐지"""
        text = "귀하의 사주를 보니 좋은 기운이 흐르고 있소."
        detected = detect_prompt_leak(text)

        assert len(detected) == 0


# ============================================================
# Unit Tests - 엣지 케이스
# ============================================================


class TestEdgeCases:
    """엣지 케이스 테스트"""

    def test_empty_string(self, filter_instance):
        """빈 문자열"""
        filtered, leaked = filter_instance.filter("")

        assert filtered == ""
        assert leaked is False

    def test_none_like_empty(self, filter_instance):
        """None처럼 취급되는 빈 문자열"""
        filtered, leaked = filter_instance.filter("   ")

        assert filtered == ""
        assert leaked is False

    def test_multiple_leaks(self, filter_instance):
        """여러 누출 패턴 동시 발생"""
        text = """[문장 종결 예시]
- 있습니다 → 있어요

[올바른 문장 예시]
1. "예시 문장입니다."

<forbidden>금지 내용</forbidden>

✅ 모든 문장을 해요체로!

좋은 운세입니다."""
        filtered, leaked = filter_instance.filter(text)

        assert leaked is True
        assert "[문장 종결 예시]" not in filtered
        assert "[올바른 문장 예시]" not in filtered
        assert "<forbidden>" not in filtered
        assert "✅" not in filtered
        assert "좋은 운세입니다" in filtered

    def test_consecutive_newlines_cleanup(self, filter_instance):
        """연속 줄바꿈 정리"""
        text = """좋은 운세입니다.


[문장 종결 예시]
- 내용



행운을 빕니다."""
        filtered, leaked = filter_instance.filter(text)

        # 3개 이상 연속 줄바꿈이 2개로 정리됨
        assert "\n\n\n" not in filtered


# ============================================================
# Integration Tests - 실제 누출 시나리오
# ============================================================


class TestRealLeakScenarios:
    """실제 E2E에서 발견된 누출 시나리오 테스트"""

    def test_stella_leak_scenario(self, filter_instance):
        """스텔라 실제 누출 시나리오"""
        # E2E에서 실제 발생한 누출 패턴
        text = """당신의 태양이 양자리에 있네요. 불의 원소가 강해요.

[문장 종결 예시 - 반드시 이 패턴을 따르세요]
- 있습니다 → 있어요
- 입니다 → 예요/이에요
- 합니다 → 해요

리더십과 추진력이 뛰어나요. 좋은 결과를 얻을 수 있어요."""
        filtered, leaked = filter_instance.filter(text)

        assert leaked is True
        assert "[문장 종결 예시" not in filtered
        assert "당신의 태양이 양자리에 있네요" in filtered
        assert "좋은 결과를 얻을 수 있어요" in filtered

    def test_soiseol_leak_scenario(self, filter_instance):
        """소이설 실제 누출 시나리오"""
        text = """귀하의 사주를 보건대 병화(丙火) 일간이시구려.

[올바른 문장 예시 20개]
1. "반갑소. 귀하의 사주를 살펴보겠소."
2. "귀하의 일간은 경금(庚金)이오."

목(木)의 기운이 강하니 새로운 시작에 좋은 때라 하겠소."""
        filtered, leaked = filter_instance.filter(text)

        assert leaked is True
        assert "[올바른 문장 예시" not in filtered
        assert "병화(丙火) 일간이시구려" in filtered

    def test_cheongwoon_leak_scenario(self, filter_instance):
        """청운 실제 누출 시나리오"""
        text = """허허, 이 늙은이는 청운이라 하오.

✅ 모든 문장을 반드시 하오체로 끝내시오!
❌ 합니다체는 절대 사용 금지!

자네의 사주를 살펴보겠소."""
        filtered, leaked = filter_instance.filter(text)

        assert leaked is True
        assert "✅" not in filtered
        assert "❌" not in filtered
        assert "청운이라 하오" in filtered

    def test_hwarin_leak_scenario(self, filter_instance):
        """화린 실제 누출 시나리오"""
        text = """어머, 귀한 손님이 오셨네요?

<자동 변환>
합니다 → 해요
입니다 → 이에요
</자동 변환>

운세가 궁금하세요? 언니가 봐드릴게요~"""
        filtered, leaked = filter_instance.filter(text)

        assert leaked is True
        assert "<자동 변환>" not in filtered
        assert "언니가 봐드릴게요" in filtered


# ============================================================
# Unit Tests - P0 추가 패턴 (vLLM 특수 토큰, 코드 누출)
# ============================================================


class TestP0LeakPatterns:
    """P0: vLLM 특수 토큰 및 코드 패턴 누출 테스트"""

    def test_vllm_fim_tokens(self, filter_instance):
        """vLLM FIM 특수 토큰 제거"""
        text = """좋은 운세입니다. <|fimprefix|>내용<|fimsuffix|>

다른 내용<|fimmiddle|>계속됩니다."""
        filtered, leaked = filter_instance.filter(text)

        assert leaked is True
        assert "<|fimprefix|>" not in filtered
        assert "<|fimsuffix|>" not in filtered
        assert "<|fimmiddle|>" not in filtered
        assert "좋은 운세입니다" in filtered

    def test_src_rule_pattern(self, filter_instance):
        """<src [규칙]... 패턴 제거"""
        text = """좋은 운세입니다.

<src [규칙] 모든 문장을 반드시 하오체로 작성하시오>

계속된 운세 내용입니다."""
        filtered, leaked = filter_instance.filter(text)

        assert leaked is True
        assert "<src [규칙]" not in filtered
        assert "좋은 운세입니다" in filtered
        assert "계속된 운세 내용입니다" in filtered

    def test_lua_separator_pattern(self, filter_instance):
        """]=] + <src 패턴 제거"""
        text = """좋은 운세입니다.]=]<src 내용

계속됩니다."""
        filtered, leaked = filter_instance.filter(text)

        assert leaked is True
        assert "]=]" not in filtered

    def test_javascript_code_patterns(self, filter_instance):
        """JavaScript 코드 패턴 제거"""
        text = """좋은 운세입니다.

getContext.setPromptTemplate("template")
setInputFormat("json")
setOutputFormat("text")
setTemperature(0.7)
setSeed(42)
await model.predict(input)
console.log("output")

계속됩니다."""
        filtered, leaked = filter_instance.filter(text)

        assert leaked is True
        assert "getContext" not in filtered
        assert "setPromptTemplate" not in filtered
        assert "setInputFormat" not in filtered
        assert "setTemperature" not in filtered
        assert "await model" not in filtered
        assert "console.log" not in filtered
        assert "좋은 운세입니다" in filtered

    def test_javascript_error_handling(self, filter_instance):
        """.catch() 및 .then() 패턴 제거"""
        text = """좋은 운세입니다.

.catch(err => console.error(err))
.then(result => process(result))

계속됩니다."""
        filtered, leaked = filter_instance.filter(text)

        assert leaked is True
        assert ".catch" not in filtered
        assert ".then" not in filtered

    def test_code_block_pattern(self, filter_instance):
        """마크다운 코드 블록 제거"""
        text = """좋은 운세입니다.

```javascript
const result = await model.predict();
console.log(result);
```

계속된 운세입니다."""
        filtered, leaked = filter_instance.filter(text)

        assert leaked is True
        assert "```" not in filtered
        assert "const result" not in filtered
        assert "좋은 운세입니다" in filtered
        assert "계속된 운세입니다" in filtered

    def test_markdown_headers(self, filter_instance):
        """마크다운 헤더 패턴 제거"""
        text = """좋은 운세입니다.

### Explanation
This function does...

### Example Usage
Use it like this...

계속됩니다."""
        filtered, leaked = filter_instance.filter(text)

        assert leaked is True
        assert "### Explanation" not in filtered
        assert "### Example Usage" not in filtered

    def test_code_comments(self, filter_instance):
        """코드 주석 패턴 제거"""
        text = """좋은 운세입니다.

// Error handling for edge cases
// Clean up resources
// Set seed for reproducibility
// Output the result

계속됩니다."""
        filtered, leaked = filter_instance.filter(text)

        assert leaked is True
        assert "// Error handling" not in filtered
        assert "// Clean up" not in filtered
        assert "// Set seed" not in filtered

    def test_meta_instruction_pattern(self, filter_instance):
        """[이어서 완성할 부분] 메타 지시문 제거"""
        text = """좋은 운세입니다.

[이어서 완성할 부분]

계속된 내용입니다."""
        filtered, leaked = filter_instance.filter(text)

        assert leaked is True
        assert "[이어서 완성할 부분]" not in filtered
        assert "좋은 운세입니다" in filtered


# ============================================================
# Unit Tests - 반복 문장 제거
# ============================================================


class TestRepeatedSentenceRemoval:
    """반복 문장 제거 기능 테스트"""

    def test_remove_exact_repeated_sentences(self, filter_instance):
        """정확히 같은 문장 반복 제거"""
        text = """좋은 운세입니다. 좋은 운세입니다. 다른 내용입니다."""
        filtered, leaked = filter_instance.filter(text)

        # 누출 패턴은 없지만 반복 제거는 동작
        assert filtered.count("좋은 운세입니다.") == 1
        assert "다른 내용입니다" in filtered

    def test_remove_multiple_repeated_sentences(self, filter_instance):
        """여러 문장 반복 제거"""
        text = """첫 번째 문장입니다. 두 번째 문장입니다. 첫 번째 문장입니다. 세 번째 문장입니다."""
        filtered, leaked = filter_instance.filter(text)

        assert filtered.count("첫 번째 문장입니다.") == 1
        assert filtered.count("두 번째 문장입니다.") == 1
        assert "세 번째 문장입니다" in filtered

    def test_preserve_similar_but_different_sentences(self, filter_instance):
        """유사하지만 다른 문장은 보존"""
        text = """좋은 운세입니다. 아주 좋은 운세입니다. 매우 좋은 운세입니다."""
        filtered, leaked = filter_instance.filter(text)

        # 정확히 같지 않으므로 모두 보존
        assert "좋은 운세입니다." in filtered
        assert "아주 좋은 운세입니다." in filtered
        assert "매우 좋은 운세입니다." in filtered

    def test_normalize_whitespace_in_comparison(self, filter_instance):
        """공백 정규화하여 비교"""
        text = """좋은 운세입니다.  좋은  운세입니다. 다른 내용입니다."""
        filtered, leaked = filter_instance.filter(text)

        # 공백 차이 무시하고 중복 제거
        assert filtered.count("운세입니다") == 1


# ============================================================
# Unit Tests - P1 메타 지시문 패턴
# ============================================================


class TestP1MetaDirectivePatterns:
    """P1 메타 지시문 패턴 테스트"""

    def test_filter_이어서_pattern(self, filter_instance):
        """[\이어서 완성할 부분] 패턴 필터링"""
        text = "오늘 운세입니다. [\이어서 완성할 부분] 좋은 하루 되세요."
        filtered, leaked = filter_instance.filter(text)

        assert leaked is True
        assert "이어서" not in filtered
        assert "오늘 운세입니다" in filtered
        assert "좋은 하루 되세요" in filtered

    def test_filter_마무리_pattern(self, filter_instance):
        """[\마무리] 패턴 필터링"""
        text = "연애운이 좋아요. [\마무리]"
        filtered, leaked = filter_instance.filter(text)

        assert leaked is True
        assert "마무리" not in filtered
        assert "연애운이 좋아요" in filtered

    def test_filter_총평_pattern(self, filter_instance):
        """[\총평] 패턴 필터링"""
        text = "[\총평] 전체적으로 좋은 운세입니다."
        filtered, leaked = filter_instance.filter(text)

        assert leaked is True
        assert "총평" not in filtered
        assert "전체적으로 좋은 운세입니다" in filtered

    def test_filter_meta_response_start(self, filter_instance):
        """'아래는 요청하신...' 메타 응답 필터링"""
        text = "아래는 요청하신 운세 결과입니다.\n오늘의 운세는 좋습니다."
        filtered, leaked = filter_instance.filter(text)

        assert leaked is True
        assert "아래는 요청하신" not in filtered
        assert "오늘의 운세는" in filtered


# ============================================================
# Unit Tests - 반복 문장 제거 (추가)
# ============================================================


class TestRepeatedSentences:
    """반복 문장 제거 테스트"""

    def test_remove_3x_repeated(self, filter_instance):
        """3회 반복 문장 제거"""
        text = "좋은 하루예요. 좋은 하루예요. 좋은 하루예요. 감사합니다."
        filtered, leaked = filter_instance.filter(text)

        # 반복 제거 후 1개만 남아야 함
        assert filtered.count("좋은 하루예요.") == 1
        assert "감사합니다" in filtered

    def test_remove_5x_repeated(self, filter_instance):
        """5회 반복 문장 제거"""
        text = "행운이 있어요. " * 5 + "좋은 결과가 있을 거예요."
        filtered, leaked = filter_instance.filter(text)

        # 반복 제거 후 1개만 남아야 함
        assert filtered.count("행운이 있어요.") == 1
        assert "좋은 결과가 있을 거예요" in filtered


# ============================================================
# Unit Tests - 불완전 문장 처리
# ============================================================


class TestIncompleteSentences:
    """불완전 문장 처리 테스트"""

    def test_remove_jamo_start(self, filter_instance):
        """자음으로 시작하는 문장 제거"""
        text = "ㄹ게요\n연락드릴게요."
        filtered, leaked = filter_instance.filter(text)

        # 자음 시작 부분은 제거되어야 함 (leaked 플래그와 무관)
        assert "ㄹ게요" not in filtered
        # 정상 문장은 보존
        assert "연락드릴게요" in filtered

    def test_remove_incomplete_start(self, filter_instance):
        """조사로 시작하는 불완전 문장"""
        text = "른 직장운"
        filtered, leaked = filter_instance.filter(text)

        # 불완전한 시작은 제거됨 (짧은 문장이므로)
        assert filtered.strip() == "" or "른 직장운" not in filtered
