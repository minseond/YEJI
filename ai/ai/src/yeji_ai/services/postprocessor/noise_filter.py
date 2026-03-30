"""LLM 응답 노이즈 필터

외래 문자(Thai, Arabic, Hebrew 등) 및 반복 패턴을 제거합니다.
한글+영문 혼합 토큰 오류(AWQ 양자화 모델 문제)도 수정합니다.
"""

import re

import structlog

logger = structlog.get_logger()


# ============================================================
# 알려진 혼합 스크립트 오류 매핑 (AWQ 양자화 모델 문제)
# vLLM 토크나이저에서 한글 토큰 손상 시 발생하는 패턴
# ============================================================
KNOWN_MIXED_SCRIPT_ERRORS: dict[str, str] = {
    # 한글 + 영문 혼합 오류
    "꾸urly": "꾸준히",
    "꾸ulous": "꾸준히",
    "꾸rly": "꾸준히",
    # 추가 발견 시 여기에 등록
}


def fix_mixed_script_tokens(text: str) -> str:
    """한글+영문 혼합 토큰 오류 수정

    vLLM AWQ 양자화 모델에서 토크나이저 문제로 발생하는
    한글 토큰 손상을 수정합니다.

    예시:
        "꾸urly" → "꾸준히"

    Args:
        text: 원본 텍스트

    Returns:
        혼합 스크립트 오류가 수정된 텍스트
    """
    if not text:
        return text

    original = text

    # 1. 알려진 오류 패턴 수정
    for error, correction in KNOWN_MIXED_SCRIPT_ERRORS.items():
        if error in text:
            text = text.replace(error, correction)
            logger.info(
                "mixed_script_fixed",
                error_pattern=error,
                correction=correction,
            )

    # 2. 한글+영문 혼합 패턴 감지 및 로깅 (미등록 패턴 발견용)
    # 패턴: 한글 1자 + 영문 2자 이상 연속
    mixed_pattern = re.compile(r"([가-힣])([a-zA-Z]{2,})")
    matches = mixed_pattern.findall(text)

    if matches:
        # 이미 수정된 패턴은 제외하고 로깅
        unknown_patterns = []
        for match in matches:
            pattern = f"{match[0]}{match[1]}"
            if pattern not in KNOWN_MIXED_SCRIPT_ERRORS:
                unknown_patterns.append(pattern)

        if unknown_patterns:
            logger.warning(
                "mixed_script_detected",
                patterns=unknown_patterns,
                message=(
                    "알려지지 않은 혼합 스크립트 패턴 발견. "
                    "KNOWN_MIXED_SCRIPT_ERRORS에 추가 필요."
                ),
            )

    # 3. 변경 로깅
    if text != original:
        logger.debug(
            "mixed_script_tokens_cleaned",
            original_len=len(original),
            cleaned_len=len(text),
        )

    return text


def fix_number_spacing(text: str) -> str:
    """숫자 사이의 잘못된 공백 제거

    LLM이 "66. 7%", "3. 14" 같이 소수점 앞뒤에 공백을 넣는 오류 수정

    Args:
        text: 원본 텍스트

    Returns:
        숫자 공백이 수정된 텍스트
    """
    if not text:
        return text

    # 패턴: 숫자 + 공백(선택) + 점 + 공백(선택) + 숫자
    # "66. 7" → "66.7", "3. 14" → "3.14"
    pattern = r"(\d+)\s*\.\s*(\d+)"
    cleaned = re.sub(pattern, r"\1.\2", text)

    return cleaned


def remove_foreign_characters(text: str) -> str:
    """비한글/비ASCII 외래 문자 제거

    Args:
        text: 원본 텍스트

    Returns:
        외래 문자가 제거된 텍스트
    """
    # 허용 문자: 한글, 영문, 숫자, 기본 문장부호, 공백
    allowed_pattern = r"[가-힣ㄱ-ㅎㅏ-ㅣa-zA-Z0-9\s.,!?~\-:;\"\'()\[\]@#$%^&*+=<>/\\|`]"

    # 허용되지 않는 문자를 빈 문자열로 대체
    cleaned = "".join(char if re.match(allowed_pattern, char) else "" for char in text)

    # 연속된 공백 정리
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    return cleaned


def remove_repetition(text: str, threshold: int = 3) -> str:
    """반복 패턴 제거

    Args:
        text: 원본 텍스트
        threshold: 반복 횟수 임계값 (이상이면 제거)

    Returns:
        반복 패턴이 제거된 텍스트
    """
    # 동일 문장 반복 제거
    sentences = re.split(r"([.!?])", text)
    seen = set()
    result = []

    for i in range(0, len(sentences) - 1, 2):
        sentence = sentences[i].strip()
        punct = sentences[i + 1] if i + 1 < len(sentences) else ""

        if sentence and sentence not in seen:
            seen.add(sentence)
            result.append(sentence + punct)
        elif sentence in seen:
            # 중복 문장 스킵
            pass

    # 마지막 문장 처리
    if len(sentences) % 2 == 1 and sentences[-1].strip():
        last = sentences[-1].strip()
        if last not in seen:
            result.append(last)

    return " ".join(result)


def truncate_at_noise(text: str) -> str:
    """노이즈 시작점에서 텍스트 자르기

    외래 문자가 시작되는 지점에서 텍스트를 잘라
    자연스러운 문장 끝을 유지합니다.

    Args:
        text: 원본 텍스트

    Returns:
        노이즈 이전까지의 텍스트
    """
    # 노이즈 패턴 감지 (연속된 외래 문자 또는 의미 없는 패턴)
    noise_patterns = [
        r"[^\x00-\x7F가-힣ㄱ-ㅎㅏ-ㅣ\s.,!?~\-:;\"\'()]{2,}",  # 외래 문자
        r"\*[a-z]+\.",  # *angstrom. 패턴
        r"\b[a-z]{2,6}\.\s+[a-z]{2,6}\.",  # zwas. 겚. 같은 패턴
    ]

    # 모든 패턴에 대해 검사하여 가장 먼저 발견된 노이즈 위치 찾기
    earliest_match_start = len(text)
    for pattern in noise_patterns:
        match = re.search(pattern, text)
        if match and match.start() < earliest_match_start:
            earliest_match_start = match.start()

    # 노이즈가 발견되었으면 잘라내기
    if earliest_match_start < len(text):
        # 노이즈 시작 전까지 자르기
        clean_text = text[:earliest_match_start].rstrip()

        # 마지막 완전한 문장까지만 유지
        last_punct = max(
            clean_text.rfind("."),
            clean_text.rfind("!"),
            clean_text.rfind("?"),
            clean_text.rfind("~"),
        )

        if last_punct > 0:
            return clean_text[: last_punct + 1]
        return clean_text

    return text


def filter_noise(text: str, aggressive: bool = False) -> str:
    """통합 노이즈 필터

    처리 순서:
    1. 한글+영문 혼합 토큰 오류 수정 (AWQ 양자화 문제)
    2. 숫자 공백 오류 수정 (소수점 앞뒤 공백 제거)
    3. 외래 문자 제거 또는 노이즈 시작점에서 자르기
    4. 반복 패턴 제거

    Args:
        text: 원본 텍스트
        aggressive: True면 노이즈 이후 텍스트 제거, False면 노이즈만 제거

    Returns:
        노이즈가 제거된 정제된 텍스트
    """
    # 0. 빈 텍스트 처리
    if not text:
        return text

    # 1. 한글+영문 혼합 토큰 오류 수정 (가장 먼저 처리)
    cleaned = fix_mixed_script_tokens(text)

    # 2. 숫자 공백 오류 수정
    cleaned = fix_number_spacing(cleaned)

    # 3. 외래 문자 처리
    if aggressive:
        # 공격적 필터: 노이즈 시작점에서 자르기
        cleaned = truncate_at_noise(cleaned)
    else:
        # 기본 필터: 외래 문자만 제거하고 나머지 유지
        cleaned = remove_foreign_characters(cleaned)

    # 4. 반복 패턴 제거
    cleaned = remove_repetition(cleaned)

    return cleaned


# 테스트용
if __name__ == "__main__":
    test_texts = [
        "반가워요~ 저는 엘라리아예요.ครี糖เริ่มต้น 좋은 하루 보내세요.",
        "허허, 반갑소.참จังหวัด들รับผิด 이 늙은이는 청운이라 하오.",
        "나? 카일이야. 방랑 도박사지.הע나? 카일이야. 방랑 도박사지.",
    ]

    for text in test_texts:
        print(f"원본: {text}")
        print(f"정제: {filter_noise(text)}")
        print()
