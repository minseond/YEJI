"""조합 테스트 검증 로직 단독 실행

conftest.py 의존성 없이 검증 함수만 테스트
"""

import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
sys.path.insert(0, str(Path(__file__).parent))

from test_character_combinations import (
    ALL_CHARACTERS,
    CHARACTER_COMBINATIONS,
    SPEECH_PATTERNS,
    check_language_purity,
    check_no_prompt_leak,
    check_speech_style_consistency,
    validate_character_response,
)


def test_speech_patterns():
    """말투 패턴 검증 테스트"""
    print("\n" + "=" * 60)
    print("말투 패턴 검증 테스트")
    print("=" * 60)

    test_cases = {
        "SOISEOL": {
            "good": "자네의 사주를 살펴보겠소. 밝은 성격을 가지셨구려.",
            "bad": "안녕하세요. 사주를 분석해 드리겠습니다.",
        },
        "STELLA": {
            "good": "양자리 태양이네요~ 리더십이 강해요!",
            "bad": "안녕하십니까. 운세를 분석하겠소.",
        },
        "CHEONGWOON": {
            "good": "허허, 물은 돌을 거스르지 않고 돌아가는 법이라네. 조급해하지 마시오.",
            "bad": "좋은 운세네요~ 기대하셔도 돼요!",
        },
        "HWARIN": {
            "good": "어머, 귀한 손님이 오셨네요? 정보가 필요하신 거예요?",
            "bad": "반갑소. 정보를 알려드리겠소.",
        },
        "KYLE": {
            "good": "나? 카일이야. 운이 따라주네.",
            "bad": "안녕하십니까. 도움을 드리겠습니다.",
        },
        "ELARIA": {
            "good": "반가워요~ 저는 사파이어 왕국의 공주예요.",
            "bad": "알았어. 그렇게 해.",
        },
    }

    for character in ALL_CHARACTERS:
        print(f"\n[{character}] ({SPEECH_PATTERNS[character]['style_name']})")

        # Good 케이스
        good_text = test_cases[character]["good"]
        passed, errors = check_speech_style_consistency(good_text, character)
        print(f"  ✓ Good 케이스: {'PASS' if passed else 'FAIL'}")
        if not passed:
            for error in errors:
                print(f"    - {error}")

        # Bad 케이스
        bad_text = test_cases[character]["bad"]
        passed, errors = check_speech_style_consistency(bad_text, character)
        print(f"  ✗ Bad 케이스: {'감지됨 (정상)' if not passed else '감지 안됨 (오류!)'}")
        if not passed:
            for error in errors[:2]:  # 처음 2개만 출력
                print(f"    - {error}")


def test_prompt_leak():
    """프롬프트 누출 검증 테스트"""
    print("\n" + "=" * 60)
    print("프롬프트 누출 검증 테스트")
    print("=" * 60)

    # 정상 텍스트
    clean_text = "자네의 사주를 살펴보겠소. 밝은 성격을 가지셨구려."
    passed, errors = check_no_prompt_leak(clean_text)
    print(f"\n정상 텍스트: {'PASS' if passed else 'FAIL'}")

    # 누출된 텍스트
    leaked_text = """
    <persona>소이설</persona>
    필수 어미: ~하오, ~구려, ~시오
    금지 어미: ~해요, ~합니다
    """
    passed, errors = check_no_prompt_leak(leaked_text)
    print(f"누출된 텍스트: {'감지됨 (정상)' if not passed else '감지 안됨 (오류!)'}")
    if not passed:
        print(f"  감지된 패턴: {len(errors)}개")
        for error in errors[:3]:
            print(f"    - {error}")


def test_language_purity():
    """언어 순수성 검증 테스트"""
    print("\n" + "=" * 60)
    print("언어 순수성 검증 테스트")
    print("=" * 60)

    test_cases = {
        "허용된 한자": ("목(木) 기운이 강하고 비견(比肩)이 있어요.", True),
        "허용된 영어 고유명사": ("Stella가 Kyle과 Elaria를 만났어요.", True),
        "허용되지 않은 영어": ("This is a test message with English words.", False),
        "깨진 문자": ("안녕하세요� 깨진 문자가 있어요�", False),
    }

    for desc, (text, should_pass) in test_cases.items():
        passed, errors = check_language_purity(text)
        status = "PASS" if passed == should_pass else "FAIL"
        print(f"\n{desc}: {status}")
        if errors:
            for error in errors:
                print(f"  - {error}")


def test_combinations():
    """15개 조합 검증 테스트"""
    print("\n" + "=" * 60)
    print("15개 조합 검증 테스트")
    print("=" * 60)

    sample_responses = {
        "SOISEOL": "자네의 사주를 살펴보니 병화 일간이로구려. 밝고 열정적인 성격을 가지셨소.",
        "STELLA": "생년월일을 보니 양자리 태양이네요~ 리더십이 강하고 추진력이 있어요!",
        "CHEONGWOON": "허허, 물은 돌을 거스르지 않고 돌아가는 법이라네. 조급해하지 마시오.",
        "HWARIN": "어머, 귀한 손님이 오셨네요? 정보가 필요하신 거예요? 세상에 공짜는 없어요~",
        "KYLE": "나? 카일이야. 오늘 운이 따라주네. 한 판 더 해볼까?",
        "ELARIA": "반가워요~ 저는 사파이어 왕국의 공주예요. 함께 희망을 찾아봐요.",
    }

    passed_count = 0
    failed_combinations = []

    for i, (char1, char2) in enumerate(CHARACTER_COMBINATIONS, 1):
        char1_text = sample_responses[char1]
        char2_text = sample_responses[char2]

        # 검증
        char1_passed, char1_errors = validate_character_response(char1_text, char1)
        char2_passed, char2_errors = validate_character_response(char2_text, char2)

        all_passed = char1_passed and char2_passed

        if all_passed:
            passed_count += 1
            status = "✓ PASS"
        else:
            status = "✗ FAIL"
            failed_combinations.append(f"{char1}+{char2}")

        print(f"\n[{i}] {char1} + {char2}: {status}")
        if not all_passed:
            all_errors = char1_errors + char2_errors
            for error in all_errors[:3]:  # 처음 3개만 출력
                print(f"    - {error}")

    print(f"\n{'=' * 60}")
    print(f"결과: {passed_count}/15 통과")
    if failed_combinations:
        print(f"실패한 조합: {', '.join(failed_combinations)}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    test_speech_patterns()
    test_prompt_leak()
    test_language_purity()
    test_combinations()
