"""15개 캐릭터 조합 테스트 (6C2)

6개 캐릭터의 모든 2개 조합 (15가지)에 대해:
1. 각 캐릭터의 말투 일관성 검증
2. 프롬프트 누출 없음 확인
3. 언어 순수성 (한글 + 허용된 한자/영어만)

캐릭터:
- SOISEOL (소이설): 하오체 (~하오, ~구려, ~시오)
- STELLA (스텔라): 해요체 (~해요, ~네요, ~세요)
- CHEONGWOON (청운): 하오체 시적 (~하오, ~라네, ~시게)
- HWARIN (화린): 해요체 나른함 (~해요, ~드릴게요)
- KYLE (카일): 반말+존댓말 혼용 (~해, ~지, ~요)
- ELARIA (엘라리아): 해요체 우아함 (~해요, ~세요)
"""

import re
from dataclasses import dataclass
from itertools import combinations

import pytest

# ============================================================
# 말투 검증 규칙
# ============================================================

SPEECH_PATTERNS = {
    "SOISEOL": {
        "required": [r"하오(?:[\.!\?~,]|$)", r"구려(?:[\.!\?~,]|$)", r"시오(?:[\.!\?~,]|$)", r"하게(?:[\.!\?~,]|$)", r"일세(?:[\.!\?~,]|$)"],
        "forbidden": [r"해요(?:[\.!\?~,]|$)", r"네요(?:[\.!\?~,]|$)", r"합니다(?:[\.!\?~,]|$)", r"습니다(?:[\.!\?~,]|$)"],
        "style_name": "하오체/하게체",
    },
    "STELLA": {
        "required": [r"해요(?:[\.!\?~,]|$)", r"네요(?:[\.!\?~,]|$)", r"세요(?:[\.!\?~,]|$)", r"어요(?:[\.!\?~,]|$)", r"예요(?:[\.!\?~,]|$)"],
        "forbidden": [r"하오(?:[\.!\?~,]|$)", r"구려(?:[\.!\?~,]|$)", r"시오(?:[\.!\?~,]|$)", r"합니다(?:[\.!\?~,]|$)", r"습니다(?:[\.!\?~,]|$)"],
        "style_name": "해요체",
    },
    "CHEONGWOON": {
        "required": [r"하오(?:[\.!\?~,]|$)", r"구려(?:[\.!\?~,]|$)", r"라네(?:[\.!\?~,]|$)", r"시게(?:[\.!\?~,]|$)", r"것을(?:[\.!\?~,]|$)", r"마시오(?:[\.!\?~,]|$)"],
        "forbidden": [r"해요(?:[\.!\?~,]|$)", r"네요(?:[\.!\?~,]|$)", r"합니다(?:[\.!\?~,]|$)", r"습니다(?:[\.!\?~,]|$)"],
        "style_name": "하오체 (시적)",
    },
    "HWARIN": {
        "required": [r"해요(?:[\.!\?~,]|$)", r"네요(?:[\.!\?~,]|$)", r"세요(?:[\.!\?~,]|$)", r"드릴게요(?:[\.!\?~,]|$)", r"할게요(?:[\.!\?~,]|$)"],
        "forbidden": [r"하오(?:[\.!\?~,]|$)", r"구려(?:[\.!\?~,]|$)", r"합니다(?:[\.!\?~,]|$)", r"습니다(?:[\.!\?~,]|$)"],
        "style_name": "해요체 (나른)",
    },
    "KYLE": {
        "required": [r"해\.", r"야\.", r"지\.", r"거든\.", r"잖아(?:[\.!\?~,]|$)", r"이야(?:[\.!\?~,]|$)", r"거야(?:[\.!\?~,]|$)", r"네\."],
        "forbidden": [r"합니다(?:[\.!\?~,]|$)", r"습니다(?:[\.!\?~,]|$)", r"하오(?:[\.!\?~,]|$)", r"구려(?:[\.!\?~,]|$)"],
        "style_name": "반말+존댓말 혼용",
    },
    "ELARIA": {
        "required": [r"해요(?:[\.!\?~,]|$)", r"세요(?:[\.!\?~,]|$)", r"예요(?:[\.!\?~,]|$)", r"드릴게요(?:[\.!\?~,]|$)", r"할게요(?:[\.!\?~,]|$)"],
        "forbidden": [r"하오(?:[\.!\?~,]|$)", r"구려(?:[\.!\?~,]|$)", r"합니다(?:[\.!\?~,]|$)", r"습니다(?:[\.!\?~,]|$)", r"해\.", r"야\."],
        "style_name": "해요체 (우아)",
    },
}

# 프롬프트 누출 패턴
PROMPT_LEAK_PATTERNS = [
    # XML 태그
    r"<persona>",
    r"<speaking_rule>",
    r"<forbidden>",
    r"<required>",
    r"<example>",
    r"<instruction>",
    # 메타 텍스트
    r"필수 어미",
    r"금지 어미",
    r"호칭 목록",
    r"말투 규칙",
    r"프롬프트",
    r"시스템 메시지",
    # 프롬프트 규칙 설명
    r"~(하오|해요|합니다)체를 사용하라",
    r"반드시.*사용",
    r"절대.*사용하지 마",
]

# 언어 순수성 패턴
LANGUAGE_PURITY_PATTERNS = {
    "allowed_hanja": r"[木火土金水比肩食神正官偏官正印偏印劫財傷官正財偏財甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉戌亥]",
    "allowed_english": r"(Stella|STELLA|Kyle|KYLE|Elaria|ELARIA)",
    "forbidden_broken": r"[�\ufffd]",  # 깨진 문자
    "forbidden_mixed": r"[ぁ-んァ-ヶ]",  # 일본어
}


# ============================================================
# 조합 생성
# ============================================================


ALL_CHARACTERS = ["SOISEOL", "STELLA", "CHEONGWOON", "HWARIN", "KYLE", "ELARIA"]

# 15개 조합 (6C2)
CHARACTER_COMBINATIONS = list(combinations(ALL_CHARACTERS, 2))


@dataclass
class CombinationTestResult:
    """조합 테스트 결과"""

    char1: str
    char2: str
    char1_response: str
    char2_response: str
    speech_consistency_passed: bool
    no_prompt_leak_passed: bool
    language_purity_passed: bool
    errors: list[str]


# ============================================================
# 검증 함수
# ============================================================


def check_speech_style_consistency(text: str, character: str) -> tuple[bool, list[str]]:
    """말투 일관성 검증

    Args:
        text: 캐릭터 응답 텍스트
        character: 캐릭터 코드

    Returns:
        (통과 여부, 오류 메시지 목록)
    """
    patterns = SPEECH_PATTERNS[character]
    errors = []

    # 필수 표현 검사 (최소 1개 이상)
    required_found = False
    for pattern in patterns["required"]:
        if re.search(pattern, text, re.MULTILINE):
            required_found = True
            break

    if not required_found:
        errors.append(
            f"{character} ({patterns['style_name']}): 필수 어미 패턴이 하나도 발견되지 않음. "
            f"예상: {patterns['required']}"
        )

    # 금지 표현 검사
    for pattern in patterns["forbidden"]:
        matches = re.findall(pattern, text, re.MULTILINE)
        if matches:
            errors.append(
                f"{character} ({patterns['style_name']}): "
                f"금지된 어미 '{pattern}' 발견 ({len(matches)}회): {matches[:3]}"
            )

    return len(errors) == 0, errors


def check_no_prompt_leak(text: str) -> tuple[bool, list[str]]:
    """프롬프트 누출 방지 검증

    Args:
        text: 캐릭터 응답 텍스트

    Returns:
        (통과 여부, 오류 메시지 목록)
    """
    errors = []

    for pattern in PROMPT_LEAK_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            errors.append(f"프롬프트 누출 패턴 발견: '{pattern}' → {matches[:3]}")

    return len(errors) == 0, errors


def check_language_purity(text: str) -> tuple[bool, list[str]]:
    """언어 순수성 검증

    Args:
        text: 캐릭터 응답 텍스트

    Returns:
        (통과 여부, 오류 메시지 목록)
    """
    errors = []

    # 깨진 문자 검사
    if re.search(LANGUAGE_PURITY_PATTERNS["forbidden_broken"], text):
        errors.append("깨진 문자 발견")

    # 일본어 혼용 검사
    if re.search(LANGUAGE_PURITY_PATTERNS["forbidden_mixed"], text):
        errors.append("일본어 문자 발견")

    # 영어 검사 (허용된 고유명사 제외)
    # 허용된 영어 고유명사를 임시 마커로 치환
    cleaned_text = re.sub(LANGUAGE_PURITY_PATTERNS["allowed_english"], "__NAME__", text)
    # 한글, 한자 제거
    cleaned_text = re.sub(LANGUAGE_PURITY_PATTERNS["allowed_hanja"], "", cleaned_text)
    cleaned_text = re.sub(r"[가-힣ㄱ-ㅎㅏ-ㅣ]", "", cleaned_text)
    # 숫자, 문장부호, 공백 제거
    cleaned_text = re.sub(r"[0-9\s\.,!\?~…\-\(\)\"\'""''「」『』]", "", cleaned_text)
    # 마커 제거
    cleaned_text = re.sub(r"__NAME__", "", cleaned_text)

    if re.search(r"[a-zA-Z]", cleaned_text):
        # 남은 영문자가 있으면 (허용되지 않은 영어)
        suspicious_words = re.findall(r"[a-zA-Z]+", cleaned_text)
        errors.append(f"허용되지 않은 영어 단어 발견: {suspicious_words[:5]}")

    return len(errors) == 0, errors


def validate_character_response(
    text: str,
    character: str,
) -> tuple[bool, list[str]]:
    """캐릭터 응답 종합 검증

    Args:
        text: 캐릭터 응답 텍스트
        character: 캐릭터 코드

    Returns:
        (전체 통과 여부, 오류 메시지 목록)
    """
    all_errors = []

    # 1. 말투 일관성
    speech_passed, speech_errors = check_speech_style_consistency(text, character)
    all_errors.extend(speech_errors)

    # 2. 프롬프트 누출
    leak_passed, leak_errors = check_no_prompt_leak(text)
    all_errors.extend(leak_errors)

    # 3. 언어 순수성
    purity_passed, purity_errors = check_language_purity(text)
    all_errors.extend(purity_errors)

    return len(all_errors) == 0, all_errors


# ============================================================
# 테스트 케이스
# ============================================================


class TestCharacterCombinations:
    """15개 캐릭터 조합 테스트"""

    @pytest.fixture
    def sample_responses(self) -> dict[str, str]:
        """테스트용 샘플 응답 (실제 E2E에서는 API 호출)"""
        return {
            "SOISEOL": "자네의 사주를 살펴보니 병화 일간이로구려. 밝고 열정적인 성격을 가지셨소.",
            "STELLA": "생년월일을 보니 양자리 태양이네요~ 리더십이 강하고 추진력이 있어요!",
            "CHEONGWOON": "허허, 물은 돌을 거스르지 않고 돌아가는 법이라네. 조급해하지 마시오.",
            "HWARIN": "어머, 귀한 손님이 오셨네요? 정보가 필요하신 거예요? 세상에 공짜는 없어요~",
            "KYLE": "나? 카일이야. 오늘 운이 따라주네. 한 판 더 해볼까?",
            "ELARIA": "반가워요~ 저는 사파이어 왕국의 공주예요. 함께 희망을 찾아봐요.",
        }

    @pytest.mark.parametrize("char1,char2", CHARACTER_COMBINATIONS)
    def test_combination_speech_consistency(
        self,
        char1: str,
        char2: str,
        sample_responses: dict[str, str],
    ) -> None:
        """조합별 말투 일관성 테스트"""
        # 각 캐릭터의 응답 검증
        char1_text = sample_responses[char1]
        char2_text = sample_responses[char2]

        # 캐릭터 1 검증
        char1_passed, char1_errors = check_speech_style_consistency(char1_text, char1)
        if not char1_passed:
            pytest.fail(f"{char1} 말투 검증 실패:\n" + "\n".join(char1_errors))

        # 캐릭터 2 검증
        char2_passed, char2_errors = check_speech_style_consistency(char2_text, char2)
        if not char2_passed:
            pytest.fail(f"{char2} 말투 검증 실패:\n" + "\n".join(char2_errors))

    @pytest.mark.parametrize("char1,char2", CHARACTER_COMBINATIONS)
    def test_combination_no_prompt_leak(
        self,
        char1: str,
        char2: str,
        sample_responses: dict[str, str],
    ) -> None:
        """조합별 프롬프트 누출 방지 테스트"""
        char1_text = sample_responses[char1]
        char2_text = sample_responses[char2]

        # 캐릭터 1 검증
        char1_passed, char1_errors = check_no_prompt_leak(char1_text)
        if not char1_passed:
            pytest.fail(f"{char1} 프롬프트 누출:\n" + "\n".join(char1_errors))

        # 캐릭터 2 검증
        char2_passed, char2_errors = check_no_prompt_leak(char2_text)
        if not char2_passed:
            pytest.fail(f"{char2} 프롬프트 누출:\n" + "\n".join(char2_errors))

    @pytest.mark.parametrize("char1,char2", CHARACTER_COMBINATIONS)
    def test_combination_language_purity(
        self,
        char1: str,
        char2: str,
        sample_responses: dict[str, str],
    ) -> None:
        """조합별 언어 순수성 테스트"""
        char1_text = sample_responses[char1]
        char2_text = sample_responses[char2]

        # 캐릭터 1 검증
        char1_passed, char1_errors = check_language_purity(char1_text)
        if not char1_passed:
            pytest.fail(f"{char1} 언어 순수성 실패:\n" + "\n".join(char1_errors))

        # 캐릭터 2 검증
        char2_passed, char2_errors = check_language_purity(char2_text)
        if not char2_passed:
            pytest.fail(f"{char2} 언어 순수성 실패:\n" + "\n".join(char2_errors))

    def test_all_15_combinations(self, sample_responses: dict[str, str]) -> None:
        """15개 조합 통합 테스트"""
        results = []

        for char1, char2 in CHARACTER_COMBINATIONS:
            char1_text = sample_responses[char1]
            char2_text = sample_responses[char2]

            # 캐릭터 1 검증
            char1_passed, char1_errors = validate_character_response(char1_text, char1)

            # 캐릭터 2 검증
            char2_passed, char2_errors = validate_character_response(char2_text, char2)

            result = CombinationTestResult(
                char1=char1,
                char2=char2,
                char1_response=char1_text[:50] + "..." if len(char1_text) > 50 else char1_text,
                char2_response=char2_text[:50] + "..." if len(char2_text) > 50 else char2_text,
                speech_consistency_passed=char1_passed and char2_passed,
                no_prompt_leak_passed=True,  # 간소화
                language_purity_passed=True,  # 간소화
                errors=char1_errors + char2_errors,
            )
            results.append(result)

        # 결과 요약
        passed_count = sum(1 for r in results if r.speech_consistency_passed)
        print(f"\n{'='*60}")
        print(f"15개 조합 테스트 결과: {passed_count}/15 통과")
        print(f"{'='*60}")

        for i, result in enumerate(results, 1):
            status = "✓ PASS" if result.speech_consistency_passed else "✗ FAIL"
            print(f"\n[{i}] {result.char1} + {result.char2}: {status}")
            if result.errors:
                for error in result.errors:
                    print(f"    - {error}")

        # 실패한 조합이 있으면 테스트 실패
        failed_combinations = [
            f"{r.char1}+{r.char2}" for r in results if not r.speech_consistency_passed
        ]
        if failed_combinations:
            pytest.fail(f"실패한 조합 ({len(failed_combinations)}개): {failed_combinations}")


# ============================================================
# 개별 캐릭터 검증 테스트
# ============================================================


class TestIndividualCharacterSpeech:
    """개별 캐릭터 말투 검증"""

    @pytest.mark.parametrize("character", ALL_CHARACTERS)
    def test_speech_style_required_patterns(self, character: str) -> None:
        """필수 어미 패턴 검증"""
        patterns = SPEECH_PATTERNS[character]
        # 각 필수 패턴에 매칭되는 예시 문장
        test_sentences = {
            "SOISEOL": "자네의 사주를 살펴보겠소. 밝은 성격을 가지셨구려.",
            "STELLA": "양자리 태양이네요~ 리더십이 강해요!",
            "CHEONGWOON": "물은 돌을 거스르지 않고 돌아가는 법이라네.",
            "HWARIN": "정보가 필요하신 거예요? 깎아드릴게요~",
            "KYLE": "나? 카일이야. 운이 따라주네.",
            "ELARIA": "반가워요~ 함께 희망을 찾아볼게요. 도움을 드릴게요.",
        }

        text = test_sentences[character]
        passed, errors = check_speech_style_consistency(text, character)
        assert passed, f"{character} 필수 패턴 검증 실패:\n" + "\n".join(errors)

    @pytest.mark.parametrize("character", ALL_CHARACTERS)
    def test_speech_style_forbidden_patterns(self, character: str) -> None:
        """금지 어미 패턴 검증"""
        patterns = SPEECH_PATTERNS[character]

        # 금지된 패턴이 포함된 나쁜 예시
        bad_examples = {
            "SOISEOL": "안녕하세요. 사주를 분석해 드리겠습니다.",  # 해요체 금지
            "STELLA": "안녕하십니까. 운세를 분석하겠소.",  # 하오체 금지
            "CHEONGWOON": "좋은 운세네요~ 기대하셔도 돼요!",  # 해요체 금지
            "HWARIN": "반갑소. 정보를 알려드리겠소.",  # 하오체 금지
            "KYLE": "안녕하십니까. 도움을 드리겠습니다.",  # 합니다체 금지
            "ELARIA": "알았어. 그렇게 해.",  # 반말 금지
        }

        text = bad_examples[character]
        passed, errors = check_speech_style_consistency(text, character)
        assert not passed, f"{character} 금지 패턴이 감지되지 않음"


# ============================================================
# 프롬프트 누출 및 언어 순수성 테스트
# ============================================================


class TestPromptLeakAndPurity:
    """프롬프트 누출 및 언어 순수성 테스트"""

    def test_prompt_leak_detection(self) -> None:
        """프롬프트 누출 패턴 감지"""
        # 누출된 예시
        leaked_text = """
        <persona>소이설</persona>
        필수 어미: ~하오, ~구려, ~시오
        금지 어미: ~해요, ~합니다
        """
        passed, errors = check_no_prompt_leak(leaked_text)
        assert not passed, "프롬프트 누출이 감지되지 않음"
        assert len(errors) >= 3, f"감지된 누출 패턴이 부족: {errors}"

    def test_language_purity_hanja(self) -> None:
        """한자 사용 허용"""
        text = "목(木) 기운이 강하고 비견(比肩)이 있어요."
        passed, errors = check_language_purity(text)
        assert passed, f"허용된 한자가 오류로 감지됨: {errors}"

    def test_language_purity_english_names(self) -> None:
        """영어 고유명사 허용"""
        text = "Stella가 Kyle과 Elaria를 만났어요."
        passed, errors = check_language_purity(text)
        assert passed, f"허용된 영어 고유명사가 오류로 감지됨: {errors}"

    def test_language_purity_forbidden_english(self) -> None:
        """허용되지 않은 영어 감지"""
        text = "This is a test message with English words."
        passed, errors = check_language_purity(text)
        assert not passed, "허용되지 않은 영어가 감지되지 않음"

    def test_language_purity_broken_chars(self) -> None:
        """깨진 문자 감지"""
        text = "안녕하세요� 깨진 문자가 있어요�"
        passed, errors = check_language_purity(text)
        assert not passed, "깨진 문자가 감지되지 않음"


# ============================================================
# E2E 테스트 (실제 API 호출)
# ============================================================


@pytest.mark.skip(reason="E2E 테스트는 서버 실행 필요")
class TestCharacterCombinationsE2E:
    """E2E 조합 테스트 (실제 API 호출)"""

    @pytest.fixture
    def api_base_url(self) -> str:
        return "http://localhost:8000/v1/fortune"

    @pytest.mark.asyncio
    @pytest.mark.parametrize("char1,char2", CHARACTER_COMBINATIONS)
    async def test_combination_e2e(
        self,
        api_base_url: str,
        char1: str,
        char2: str,
    ) -> None:
        """실제 API 호출로 조합 테스트"""
        import httpx

        async with httpx.AsyncClient(timeout=120.0) as client:
            # 캐릭터 1 응답 생성
            response1 = await client.post(
                f"{api_base_url}/chat/test-character",
                json={"character": char1, "message": "간단히 자기소개 해주세요."},
            )
            assert response1.status_code == 200
            data1 = response1.json()

            # 캐릭터 2 응답 생성
            response2 = await client.post(
                f"{api_base_url}/chat/test-character",
                json={"character": char2, "message": "간단히 자기소개 해주세요."},
            )
            assert response2.status_code == 200
            data2 = response2.json()

            # 검증
            char1_passed, char1_errors = validate_character_response(
                data1["response"], char1
            )
            char2_passed, char2_errors = validate_character_response(
                data2["response"], char2
            )

            # 결과 출력
            print(f"\n{'='*60}")
            print(f"조합: {char1} + {char2}")
            print(f"{'='*60}")
            print(f"\n[{char1} 응답]")
            print(data1["response"])
            print(f"\n[{char2} 응답]")
            print(data2["response"])

            # 오류 출력
            if char1_errors or char2_errors:
                print(f"\n[검증 오류]")
                for error in char1_errors + char2_errors:
                    print(f"  - {error}")

            assert char1_passed and char2_passed, (
                f"{char1}+{char2} 조합 검증 실패:\n"
                + "\n".join(char1_errors + char2_errors)
            )


if __name__ == "__main__":
    # 로컬 테스트 실행
    print("15개 캐릭터 조합 목록:")
    for i, (char1, char2) in enumerate(CHARACTER_COMBINATIONS, 1):
        print(f"{i}. {char1} + {char2}")
