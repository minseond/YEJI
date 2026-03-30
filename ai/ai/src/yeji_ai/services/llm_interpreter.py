"""LLM 해석 생성 서비스

소이설/스텔라 캐릭터 프롬프트로 운세 해석 생성
vLLM response_format: {"type": "json_object"}로 구조화된 출력 보장
"""

import json
import re
from typing import TypeVar

import httpx
import structlog
from pydantic import BaseModel

from yeji_ai.config import get_settings
from yeji_ai.data.fortune_cache import get_eastern_cached
from yeji_ai.models.fortune.eastern import EasternFortuneResponse
from yeji_ai.models.llm_schemas import (
    CharacterMessage,
    EasternFullLLMOutput,
    EasternInterpretationResult,
)
from yeji_ai.prompts.character_personas import (
    get_character,
    get_fallback_response,
)
from yeji_ai.providers import (
    GenerationConfig,
    OpenAIConfig,
    OpenAIProvider,
    VLLMConfig,
    VLLMProvider,
)
from yeji_ai.services.postprocessor import (
    filter_noise,
    filter_prompt_leak,
    fix_brackets,
    fix_mixed_script_tokens,
)
from yeji_ai.services.provider_manager import ProviderManager
from yeji_ai.services.rule_based_fallback import get_eastern_fallback

logger = structlog.get_logger()

T = TypeVar("T", bound=BaseModel)


# ============================================================
# LLM 응답 후처리 함수
# ============================================================


def _clean_llm_response(text: str) -> str:
    """
    LLM 응답에서 이상 토큰 및 패턴 제거

    제거 대상:
    - 한글+영문 혼합 토큰 오류 (AWQ 양자화 모델 문제)
    - </s>, <s>, <|endoftext|>, <|end|> 등 특수 토큰
    - assistant, user 토큰 노출
    - 색상 코드 반복 (#ae42ff 등 2회 이상)
    - 외국어 문자 (태국어, 중국어, 일본어 히라가나/가타카나)
    - 프롬프트 형식 노출 ([주제], [정보] 등)
    - JSON 역할 패턴 ("role": "user" 등)
    - 내부 변수 노출 (lng:, lat: 등)
    - JSON 구조 노출 ({"content":, {"message": 등)
    """
    if not text:
        return text

    original = text

    # 0. 한글+영문 혼합 토큰 오류 수정 (AWQ 양자화 모델 문제, 가장 먼저 처리)
    # 예: "꾸urly" → "꾸준히"
    text = fix_mixed_script_tokens(text)

    # 1. 특수 토큰 제거 (프롬프트 마커 포함)
    special_tokens = [
        r"</s>",
        r"<s>",
        r"<\|endoftext\|>",
        r"<\|end\|>",
        r"<\|im_end\|>",
        r"<\|im_start\|>",
        r"<\|eot_id\|>",
        r"<\|start_header_id\|>",
        r"<\|end_header_id\|>",
        r"<\|begin_of_text\|>",
        r"<\|separator\|>",
        r"<\|pad\|>",
        r"<\|unk\|>",
        r"<\|mask\|>",
        r"\[PAD\]",
        r"\[CLS\]",
        r"\[SEP\]",
        r"\[MASK\]",
        r"\[UNK\]",
    ]
    for token in special_tokens:
        text = re.sub(token, "", text)

    # 1-1. XML/HTML 태그 제거 (LLM이 생성한 잘못된 태그)
    # <quoteuser>, <quote>, </quote> 등
    text = re.sub(r"</?quote[^>]*>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"</?[a-z]+user[^>]*>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"</?assistant[^>]*>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"</?system[^>]*>", "", text, flags=re.IGNORECASE)

    # 2. assistant/user 토큰 제거 (줄 끝 포함)
    text = re.sub(r"\bassistant\b", "", text, flags=re.IGNORECASE)
    text = re.sub(r"(?:^|\s)user(?:\s|$)", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"user$", "", text, flags=re.IGNORECASE | re.MULTILINE)

    # 2-1. [user]/[assistant]/[speaker:...] 줄 전체 제거 (프롬프트 누출 패턴)
    # 예: "[user] 사자자리...", "[speaker: system] 모든 문장..." 같은 줄 전체 제거
    text = re.sub(r"^\s*\[user\].*$", "", text, flags=re.MULTILINE | re.IGNORECASE)
    text = re.sub(r"^\s*\[assistant\].*$", "", text, flags=re.MULTILINE | re.IGNORECASE)
    text = re.sub(r"^\s*\[speaker:[^\]]*\].*$", "", text, flags=re.MULTILINE | re.IGNORECASE)
    text = re.sub(r"^\s*\[system\].*$", "", text, flags=re.MULTILINE | re.IGNORECASE)

    # 2-2. 대문자 코드 토큰 제거 (GETGLOBAL, SETLOCAL 등)
    text = re.sub(r"\b[A-Z]{2,}[A-Z_]*\b", "", text)  # 2자 이상 대문자 연속

    # 2-3. JSON 마커/구조 누출 제거
    # 예: ['<{"content": "...", "content": "...' 등
    text = re.sub(r"\['\s*<?\s*\{[^}]*$", "", text, flags=re.MULTILINE)
    # JSON 객체 줄
    json_obj_pattern = r"^\s*\{\"[^\"]+\":\s*\"[^\"]*\"[^}]*$"
    text = re.sub(json_obj_pattern, "", text, flags=re.MULTILINE)
    text = re.sub(r"\['\s*<", "", text)  # JSON 배열 시작 마커
    text = re.sub(r"\"content\":\s*\"", "", text)  # content 키

    # 2-4. JSON 역할 패턴 제거 (프롬프트 누출 - P0)
    # 예: "role": "user", "role": "assistant", "role": "system"
    text = re.sub(r"\"role\":\s*\"(?:user|assistant|system)\"[,\s]*", "", text)
    text = re.sub(r"'role':\s*'(?:user|assistant|system)'[,\s]*", "", text)

    # 2-5. JSON 구조 키 노출 제거
    # 예: {"content": "...", {"message": "...", {"text": "..."
    text = re.sub(r"\{\"(?:content|message|text)\":\s*\"[^\"]*\"[,}]?", "", text)
    text = re.sub(r"\"(?:content|message|text)\":\s*\"", "", text)

    # 2-6. 내부 변수 노출 제거 (좌표, 설정값 등)
    # 예: lng: "...", lat: "...", timezone: "..."
    text = re.sub(r"\blng:\s*[\"']?[^,\n\"']+[\"']?[,\s]*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\blat:\s*[\"']?[^,\n\"']+[\"']?[,\s]*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\btimezone:\s*[\"']?[^,\n\"']+[\"']?[,\s]*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\bapi_key:\s*[\"']?[^,\n\"']+[\"']?[,\s]*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\btoken:\s*[\"']?[^,\n\"']+[\"']?[,\s]*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\bsecret:\s*[\"']?[^,\n\"']+[\"']?[,\s]*", "", text, flags=re.IGNORECASE)

    # 3. 색상 코드 반복 제거 (같은 색상이 2회 이상 반복되면 1개만 남김)
    # 패턴: #ae42ff #ae42ff #ae42ff... -> #ae42ff
    color_pattern = r"(#[a-fA-F0-9]{6})(\s*\1)+"
    text = re.sub(color_pattern, r"\1", text)

    # 4. 색상 코드만 나열된 경우 전체 제거 (의미 없는 반복)
    # 예: "#ae42ff #ae42ff #ae42ff" 만 있는 줄 제거
    text = re.sub(r"^\s*(#[a-fA-F0-9]{6}\s*)+\s*$", "", text, flags=re.MULTILINE)

    # 5. 외국어 문자 제거
    # 태국어: \u0E00-\u0E7F
    # 아랍어: \u0600-\u06FF, \u0750-\u077F
    # 히브리어: \u0590-\u05FF
    # 일본어 히라가나: \u3040-\u309F
    # 일본어 가타카나: \u30A0-\u30FF
    # 러시아어/키릴 문자: \u0400-\u04FF
    # 그리스어: \u0370-\u03FF
    # 중국어 간체: 연속 3자 이상 한자는 제거 (한국 한자는 보통 1-2자)
    text = re.sub(r"[\u0E00-\u0E7F]+", "", text)  # 태국어
    text = re.sub(r"[\u0600-\u06FF\u0750-\u077F]+", "", text)  # 아랍어
    text = re.sub(r"[\u0590-\u05FF]+", "", text)  # 히브리어
    text = re.sub(r"[\u0400-\u04FF]+", "", text)  # 러시아어/키릴 문자
    text = re.sub(r"[\u0370-\u03FF]+", "", text)  # 그리스어
    text = re.sub(r"[\u3040-\u309F]+", "", text)  # 일본어 히라가나
    text = re.sub(r"[\u30A0-\u30FF]+", "", text)  # 일본어 가타카나
    text = re.sub(r"[\u4E00-\u9FFF]{3,}", "", text)  # 3자 이상 연속 한자

    # 5-1. 반복 패턴 제거 (같은 문장이 2회 이상 반복)
    # 예: "감사하오.을 지키며..." 같은 반복 제거
    text = re.sub(r"(.{10,})\1+", r"\1", text)  # 10자 이상 반복 패턴 제거
    text = re.sub(r"(\S+하오\.?\s*을\s*[^.]*)+", "", text)  # "하오.을" 패턴 제거
    # 짧은 단어 반복 제거 (하오.하오.하오..., 요.요.요... 등)
    text = re.sub(r"(하오\.){2,}", "하오.", text)  # 하오.하오... → 하오.
    text = re.sub(r"(요\.){2,}", "요.", text)  # 요.요... → 요.
    text = re.sub(r"(소\.){2,}", "소.", text)  # 소.소... → 소.
    text = re.sub(r"(\S{1,5}\.)\1{2,}", r"\1", text)  # 짧은 단어.단어.단어... 반복

    # 5-2. 코드 토큰/iOS 함수명 제거
    code_tokens = [
        r"\.didReceiveMemoryWarning",
        r"\.viewDidLoad",
        r"\.viewWillAppear",
        r"\.viewDidAppear",
        r"__init__",
        r"__main__",
        r"def\s+\w+\(",
        r"func\s+\w+\(",
        r"function\s+\w+\(",
        r"numerusform",  # Qt/C++ 번역 키워드
        r"nplurals",  # gettext 번역 키워드
        r"msgstr",  # gettext 키워드
        r"msgid",  # gettext 키워드
    ]
    for token in code_tokens:
        text = re.sub(token, "", text, flags=re.IGNORECASE)

    # 6. 프롬프트 형식 노출 제거
    prompt_patterns = [
        r"\[주제\][^\[]*",
        r"\[정보\][^\[]*",
        r"\[출력\][^\[]*",
        r"\[응답\][^\[]*",
        r"\[사주\][^\[]*",
        r"\[요청\][^\[]*",
        r"\[분석\][^\[]*",
        r"\[결과\][^\[]*",
        r"\[해석\][^\[]*",
    ]
    for pattern in prompt_patterns:
        text = re.sub(pattern, "", text)

    # 6-2. P0 추가: 짧은 해시태그 마커 제거 (색상 코드가 아닌 것)
    # 예: #ae1, #step2 등 제거 (6자리 색상 코드 #ffffff는 이전 단계에서 처리됨)
    text = re.sub(r"#[a-z]+\d+\s*", "", text, flags=re.IGNORECASE)

    # 6-3. P0 추가: spep, <src> 등 특수 토큰 제거
    text = re.sub(r"\bspep\b\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"</?src[^>]*>", "", text, flags=re.IGNORECASE)

    # 6-1. assistant/user 토큰 추가 정리 (줄 시작/끝 포함)
    text = re.sub(r"assistant\s*\n", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"\nassistant\s*", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"^assistant\s*", "", text, flags=re.IGNORECASE | re.MULTILINE)

    # 7. 코드/프로그래밍 토큰 제거
    # :CamelCase, _CamelCase, _Statics 등
    text = re.sub(r":[A-Z][a-zA-Z]+", "", text)  # :UIControlState 등
    text = re.sub(r"_[A-Z][a-zA-Z]+", "", text)  # _Statics 등
    text = re.sub(r"\b[A-Z][a-z]+[A-Z][a-zA-Z]*\b", "", text)  # CamelCase 단어

    # 8. 단일 한자 제거 (한국어 문맥에서 부자연스러움)
    # 문장 끝이나 중간에 나오는 고립된 한자 1-2개 제거
    text = re.sub(r"[\u4E00-\u9FFF]{1,2}(?=[\s\n.,!?]|$)", "", text)
    text = re.sub(r"(?<=[가-힣\s])[\u4E00-\u9FFF]{1,2}(?=[가-힣\s\n]|$)", "", text)

    # 9. 연속 공백/줄바꿈 정리
    text = re.sub(r"\n{3,}", "\n\n", text)  # 3개 이상 줄바꿈 -> 2개
    text = re.sub(r"[ \t]{2,}", " ", text)  # 연속 공백 -> 1개
    text = text.strip()

    # 10. noise_filter 적용 (외래 문자 및 반복 패턴 제거)
    # aggressive=False: 텍스트 손실 최소화, 노이즈만 제거
    text = filter_noise(text, aggressive=False)

    # 11. 빈 괄호 수정 (한자 자동 완성)
    # 예: "경금() 일간은..." → "경금(庚金) 일간은...", "토()가 우세하여..." → "토(土)가 우세하여..."
    text = fix_brackets(text)

    # 12. P0: 프롬프트 누출 필터링 (최종 방어선)
    # vLLM 특수 토큰, 코드 패턴, 메타 지시문 제거
    text = filter_prompt_leak(text)

    # 로깅 (변경된 경우만)
    if text != original:
        logger.debug(
            "llm_response_cleaned",
            original_len=len(original),
            cleaned_len=len(text),
            removed_chars=len(original) - len(text),
        )

    return text


def _convert_to_hao_style(text: str) -> str:
    """
    합니다체를 하오체로 변환 (소이설용)

    변환 규칙:
    - ~습니다 → ~소
    - ~입니다 → ~이오
    - ~합니다 → ~하오
    - ~됩니다 → ~되오
    - ~있습니다 → ~있소
    - ~없습니다 → ~없소
    - ~겠습니다 → ~겠소
    - ~주세요 → ~주시오
    - ~하세요 → ~하시오

    불규칙 동사 처리:
    - ㅂ 불규칙: 반갑습니다 → 반갑소 (OK)
    - 르 불규칙: 다루겠습니다 → 다루겠소 (OK)
    """
    if not text:
        return text

    # ============================================================
    # 1단계: 특정 동사/표현 우선 처리 (예외 케이스)
    # ============================================================
    specific_conversions = [
        # 인사말
        (r"반갑습니다", "반갑소"),
        (r"안녕하십니까", "안녕하시오"),
        (r"감사합니다", "감사하오"),
        (r"죄송합니다", "죄송하오"),
        # 하십시오체 → 하오체 (존댓말 레벨 조정)
        (r"바랍니다", "바라시오"),
        (r"부탁드립니다", "부탁드리오"),
        (r"기원합니다", "기원하오"),
        (r"주십시오", "주시오"),
        (r"하십시오", "하시오"),
        (r"가십시오", "가시오"),
        (r"보십시오", "보시오"),
        (r"십시오", "시오"),
        # 특정 동사 (자주 쓰이는)
        (r"살펴보겠습니다", "살펴보겠소"),
        (r"읽어드리겠습니다", "읽어드리겠소"),
        (r"말씀드리겠습니다", "말씀드리겠소"),
        (r"알려드리겠습니다", "알려드리겠소"),
        (r"분석해드리겠습니다", "분석해드리겠소"),
        (r"설명해드리겠습니다", "설명해드리겠소"),
        (r"도와드리겠습니다", "도와드리겠소"),
        (r"짚어드리겠습니다", "짚어드리겠소"),
        # ~ㅂ니다 (ㅂ 불규칙 형용사)
        (r"아름답습니다", "아름답소"),
        (r"어렵습니다", "어렵소"),
        (r"쉽습니다", "쉽소"),
        (r"덥습니다", "덥소"),
        (r"춥습니다", "춥소"),
        # ~봅니다/줍니다
        (r"살펴봅니다", "살펴보오"),
        (r"보여줍니다", "보여주오"),
        # 특수 동사 처리
        (r"지닙니다", "지니오"),
        (r"지니고 있습니다", "지니고 있소"),
        (r"가집니다", "가지고 있소"),
        (r"가지고 있습니다", "가지고 있소"),
        (r"나타납니다", "나타나오"),
    ]

    for pattern, replacement in specific_conversions:
        text = re.sub(pattern, replacement, text)

    # ============================================================
    # 2단계: 일반 패턴 변환 (긴 패턴 먼저)
    # ============================================================
    general_conversions = [
        # ~겠습니다 계열 (미래/의지)
        (r"하겠습니다", "하겠소"),
        (r"드리겠습니다", "드리겠소"),
        (r"보겠습니다", "보겠소"),
        (r"겠습니다", "겠소"),
        # ~있/없습니다 계열
        (r"있습니다", "있소"),
        (r"없습니다", "없소"),
        (r"됩니다", "되오"),
        # ~합니다 계열
        (r"합니다", "하오"),
        # ~입니다 계열 (명사 + 입니다)
        (r"입니다", "이오"),
        # 일반 ~ㅂ니다/~습니다 (동사/형용사)
        (r"([가-힣])ㅂ니다", r"\1오"),  # ㅂ니다 → 오
        (r"습니다", "소"),
        # ~세요 → ~시오
        (r"주세요", "주시오"),
        (r"하세요", "하시오"),
        (r"보세요", "보시오"),
        (r"가세요", "가시오"),
        (r"오세요", "오시오"),
        (r"세요", "시오"),
        # ~네요 → ~구려
        (r"네요", "구려"),
        # ~해요 → ~하오
        (r"해요", "하오"),
        # ~예요/~이에요 → ~이오
        (r"이에요", "이오"),
        (r"예요", "이오"),
        # ~거예요 → ~것이오
        (r"거예요", "것이오"),
        (r"건가요", "것이오"),
    ]

    for pattern, replacement in general_conversions:
        text = re.sub(pattern, replacement, text)

    # ============================================================
    # 3단계: P0 추가 - 해요체 → 하오체 변환 강화 (소이설용)
    # ============================================================
    haeyo_conversions = [
        (r"해요\.?", "하오."),
        (r"이에요\.?", "이오."),
        (r"예요\.?", "이오."),
        (r"네요\.?", "구려."),
        (r"세요\.?", "시오."),
        (r"할게요\.?", "하겠소."),
        (r"거든요\.?", "거든 하오."),
        (r"잖아요\.?", "잖소."),
        (r"죠\.?", "지오."),
    ]

    for pattern, replacement in haeyo_conversions:
        text = re.sub(pattern, replacement, text)

    return text


def _handle_edge_cases(text: str) -> str:
    """
    _convert_to_hao_style에서 누락된 엣지 케이스 처리

    추가 변환 규칙:
    - 복합 어미 (하고 있어요, 하고 싶어요 등)
    - 불규칙 동사 보완 (어려워요, 쉬워요 등)
    - 연결 어미 + 요 제거
    - 잔존 해요체 패턴
    """
    edge_cases = [
        # 복합 어미
        (r"하고 있어요", "하고 있소"),
        (r"하고 싶어요", "하고 싶소"),
        (r"할 수 있어요", "할 수 있소"),
        (r"할 거예요", "할 것이오"),
        (r"할 거에요", "할 것이오"),
        # 불규칙 동사 추가
        (r"어려워요", "어렵소"),
        (r"쉬워요", "쉽소"),
        (r"더워요", "덥소"),
        (r"추워요", "춥소"),
        (r"아파요", "아프오"),
        (r"예뻐요", "예쁘오"),
        (r"기뻐요", "기쁘오"),
        (r"슬퍼요", "슬프오"),
        # 연결 어미 + 요
        (r"지만요", "지만"),
        (r"는데요", "는데"),
        (r"서요(?=[.!?\s]|$)", "서"),
        (r"니까요", "니까"),
        # 잔존 해요체
        (r"네요(?=[.!?\s]|$)", "구려"),
        (r"군요(?=[.!?\s]|$)", "구려"),
        (r"죠(?=[.!?\s]|$)", "지오"),
    ]

    for pattern, replacement in edge_cases:
        text = re.sub(pattern, replacement, text)

    return text


def ensure_hao_style_final(text: str) -> str:
    """
    하오체 최종 검증 레이어

    역할:
    1. _convert_to_hao_style 적용 후 잔존 해요체 검출
    2. 누락된 엣지 케이스 패턴 처리
    3. 검증 실패 시 문장 단위 재처리

    Args:
        text: 검증할 텍스트

    Returns:
        하오체로 완전히 변환된 텍스트
    """
    if not text:
        return text

    # 1. 잔존 해요체 패턴
    forbidden_patterns = [
        r"해요[.!?\s]?$",
        r"에요[.!?\s]?$",
        r"예요[.!?\s]?$",
        r"네요[.!?\s]?$",
        r"세요[.!?\s]?$",
        r"어요[.!?\s]?$",
        r"아요[.!?\s]?$",
    ]

    # 2. 문장 단위 분리 후 검증
    sentences = re.split(r"(?<=[.!?])\s*", text)
    result_sentences = []

    for sentence in sentences:
        if not sentence.strip():
            continue

        # 2.1 기존 변환 적용 (멱등성 보장)
        converted = _convert_to_hao_style(sentence)

        # 2.2 잔존 해요체 검출
        has_forbidden = any(re.search(p, converted) for p in forbidden_patterns)

        if has_forbidden:
            # 2.3 추가 엣지 케이스 처리
            converted = _handle_edge_cases(converted)

        result_sentences.append(converted)

    return " ".join(result_sentences)


# ============================================================
# 불완전 문장 감지 및 재생성 로직
# ============================================================

# 문장 종결 패턴 (한국어 종결 어미 포함)
SENTENCE_ENDINGS = (".", "!", "?", "~", "요", "오", "소", "다", "려", "구려")


def detect_incomplete_sentence(text: str) -> tuple[bool, str]:
    """
    불완전 문장 감지

    max_tokens로 인해 문장이 중간에 잘렸는지 판별합니다.

    감지 기준:
    1. 마지막 문자가 문장 종결 부호가 아님
    2. 열린 괄호가 닫히지 않음
    3. 접속사/연결어미로 끝남 (그리고., 하지만. 등)
    4. 여러 문장일 때 마지막 문장이 너무 짧음 (3자 이하)

    Args:
        text: 검사할 텍스트

    Returns:
        (is_incomplete: bool, reason: str) 튜플
        - is_incomplete: 불완전 여부
        - reason: 불완전 판정 사유 (완전하면 빈 문자열)
    """
    if not text:
        return True, "empty_text"

    text = text.strip()

    if not text:
        return True, "whitespace_only"

    # 1. 마지막 문자가 종결 부호가 아니면 불완전
    if not text.endswith(SENTENCE_ENDINGS):
        return True, "no_ending"

    # 2. 열린 괄호 검사 (따옴표 제외 - 쌍이 애매함)
    open_brackets = {"(": ")", "[": "]", "{": "}", "「": "」", "『": "』"}
    bracket_stack: list[str] = []

    for char in text:
        if char in open_brackets:
            bracket_stack.append(open_brackets[char])
        elif char in open_brackets.values():
            if bracket_stack and bracket_stack[-1] == char:
                bracket_stack.pop()

    if bracket_stack:
        return True, "unclosed_bracket"

    # 3. 접속사/연결어미로 끝나는 경우 (불완전 패턴)
    # 종결 어미가 있지만 의미상 불완전한 경우
    incomplete_patterns = [
        "그리고.",
        "하지만.",
        "그러나.",
        "또한.",
        "게다가.",
        "따라서.",
        "그래서.",
        "그러므로.",
        "왜냐하면.",
        "특히.",
        "그런데.",
    ]
    for pattern in incomplete_patterns:
        if text.endswith(pattern):
            return True, "incomplete_connector"

    # 4. 마지막 문장 길이 검사 (여러 문장일 때만, 3자 이하면 불완전)
    # 문장 구분자: 마침표, 느낌표, 물음표만 사용 (한글 종결 어미는 문장 구분에 사용하지 않음)
    sentence_separators = (".", "!", "?")
    prev_separator_pos = -1
    for i in range(len(text) - 2, -1, -1):
        if text[i] in sentence_separators:
            prev_separator_pos = i
            break

    # 이전 구분자가 있으면 마지막 문장 길이 검사
    if prev_separator_pos >= 0:
        last_sentence = text[prev_separator_pos + 1 :].strip()
        if len(last_sentence) <= 3:
            return True, "short_last_sentence"

    # 완전한 문장
    return False, ""


def _ensure_sentence_completion(text: str) -> str:
    """
    문장 완결성 보장

    LLM 응답이 max_tokens로 잘린 경우 마지막 문장을 정리합니다.

    처리:
    1. 마지막 문자가 문장 종결 부호(. ! ? ~ 요 오 소 다)가 아니면 제거
    2. 불완전한 마지막 문장 제거
    3. 최소 1문장 보장

    Args:
        text: 원본 텍스트

    Returns:
        완결된 문장으로 정리된 텍스트
    """
    if not text:
        return text

    text = text.strip()

    # 이미 완결된 문장이면 그대로 반환
    if text.endswith(SENTENCE_ENDINGS):
        return text

    # 마지막 문장 종결 부호 위치 찾기
    last_end_pos = -1
    for ending in SENTENCE_ENDINGS:
        pos = text.rfind(ending)
        if pos > last_end_pos:
            last_end_pos = pos

    # 종결 부호가 있으면 그 위치까지만 반환
    if last_end_pos > 0:
        # 종결 부호 다음에 공백이나 줄바꿈이 있으면 거기서 자르기
        cut_pos = last_end_pos + 1
        result = text[:cut_pos].strip()
        if result:
            logger.debug(
                "sentence_truncated",
                original_len=len(text),
                result_len=len(result),
                removed=text[cut_pos:50] if len(text) > cut_pos else "",
            )
            return result

    # 종결 부호가 없으면 원본 그대로 반환 (최소 내용 보장)
    return text


def _build_continuation_prompt(original_text: str, character: str = "soiseol") -> str:
    """
    불완전 문장 재생성을 위한 continuation 프롬프트 생성

    Args:
        original_text: 원본 불완전 텍스트
        character: 캐릭터 타입 ("soiseol" 또는 "stella")

    Returns:
        continuation 요청 프롬프트
    """
    # 마지막 완전한 문장 이후의 불완전한 부분 추출
    incomplete_part = ""

    last_end_pos = -1
    for ending in SENTENCE_ENDINGS:
        pos = original_text.rfind(ending)
        if pos > last_end_pos:
            last_end_pos = pos

    if last_end_pos > 0:
        incomplete_part = original_text[last_end_pos + 1 :].strip()
    else:
        incomplete_part = original_text.strip()

    # 캐릭터별 말투 지시
    if character == "soiseol":
        style_hint = "하오체로 자연스럽게 이어서 완성해주시오."
    else:
        style_hint = "해요체로 자연스럽게 이어서 완성해주세요."

    return f"""다음 문장을 {style_hint}

[이어서 완성할 부분]
{incomplete_part}

[규칙]
- 주어진 내용의 맥락을 유지하면서 1-2문장으로 완성
- 새로운 주제를 추가하지 말고 기존 내용만 마무리
- 반드시 문장을 완결 짓기"""


def _merge_continuation(original: str, continuation: str) -> str:
    """
    원본 텍스트와 continuation을 자연스럽게 연결

    Args:
        original: 원본 텍스트 (불완전)
        continuation: LLM이 생성한 continuation

    Returns:
        자연스럽게 연결된 전체 텍스트
    """
    # 원본에서 마지막 완전한 문장 위치 찾기
    last_end_pos = -1
    for ending in SENTENCE_ENDINGS:
        pos = original.rfind(ending)
        if pos > last_end_pos:
            last_end_pos = pos

    if last_end_pos > 0:
        # 마지막 완전한 문장까지 보존
        complete_part = original[: last_end_pos + 1].strip()
        # continuation에서 중복 제거 후 연결
        continuation_clean = continuation.strip()

        # continuation이 원본의 불완전 부분을 포함하면 제거
        incomplete_part = original[last_end_pos + 1 :].strip()
        if incomplete_part and continuation_clean.startswith(incomplete_part):
            continuation_clean = continuation_clean[len(incomplete_part) :].strip()

        if continuation_clean:
            return f"{complete_part} {continuation_clean}"
        return complete_part

    # 완전한 문장이 없으면 continuation으로 대체
    return continuation.strip()


def _convert_to_heyo_style(text: str) -> str:
    """
    합니다체를 해요체로 변환 (스텔라용)

    변환 규칙:
    - ~습니다 → ~어요/~아요
    - ~입니다 → ~예요
    - ~합니다 → ~해요
    - ~됩니다 → ~돼요

    불규칙 동사 처리:
    - ㅂ 불규칙: 반갑습니다 → 반가워요
    - 르 불규칙: 다루겠습니다 → 다룰게요
    """
    if not text:
        return text

    # ============================================================
    # 1단계: 불규칙 동사/표현 우선 처리
    # ============================================================
    irregular_conversions = [
        # ㅂ 불규칙 형용사 (~ㅂ습니다 → ~워요)
        (r"반갑습니다", "반가워요"),
        (r"고맙습니다", "고마워요"),
        (r"아름답습니다", "아름다워요"),
        (r"어렵습니다", "어려워요"),
        (r"쉽습니다", "쉬워요"),
        (r"덥습니다", "더워요"),
        (r"춥습니다", "추워요"),
        (r"무겁습니다", "무거워요"),
        (r"가볍습니다", "가벼워요"),
        (r"즐겁습니다", "즐거워요"),
        (r"새롭습니다", "새로워요"),
        # 르 불규칙 (~르겠습니다 → ~를게요)
        (r"다루겠습니다", "다룰게요"),
        (r"모르겠습니다", "모를게요"),
        (r"부르겠습니다", "부를게요"),
        (r"고르겠습니다", "고를게요"),
        (r"이르겠습니다", "이를게요"),
        # 르 불규칙 현재 (~릅니다 → ~라요/~러요)
        (r"다룹니다", "다뤄요"),
        (r"모릅니다", "몰라요"),
        (r"부릅니다", "불러요"),
        (r"이릅니다", "일러요"),
        # 인사/감사
        (r"안녕하십니까", "안녕하세요"),
        (r"감사합니다", "감사해요"),
        (r"감사드립니다", "감사드려요"),
        (r"죄송합니다", "죄송해요"),
        # 자주 쓰이는 표현
        (r"살펴보겠습니다", "살펴볼게요"),
        (r"분석해보겠습니다", "분석해볼게요"),
        (r"알려드리겠습니다", "알려드릴게요"),
        (r"설명해드리겠습니다", "설명해드릴게요"),
        (r"말씀드리겠습니다", "말씀드릴게요"),
        (r"도와드리겠습니다", "도와드릴게요"),
        (r"분석해드리겠습니다", "분석해드릴게요"),
        (r"읽어드리겠습니다", "읽어드릴게요"),
        # 하십시오체 → 해요체 (존댓말 레벨 조정)
        (r"바랍니다", "바라요"),
        (r"드립니다", "드려요"),
        (r"주십시오", "주세요"),
        (r"하십시오", "하세요"),
        (r"나아가십시오", "나아가세요"),
        (r"가십시오", "가세요"),
        (r"보십시오", "보세요"),
        (r"십시오", "세요"),
        # ㅂ시다 체 → 해요체
        (r"합시다", "해요"),
        (r"갑시다", "가요"),
        (r"봅시다", "봐요"),
        # "이다" 계열 (보이다, 돋보이다 등) - 특수 처리
        (r"돋보입니다", "돋보여요"),
        (r"보입니다", "보여요"),
        (r"느껴집니다", "느껴져요"),
        (r"나타납니다", "나타나요"),
        # "내다" 계열 (만들어내다, 이끌어내다 등)
        (r"만들어냅니다", "만들어내요"),
        (r"이끌어냅니다", "이끌어내요"),
        (r"끌어냅니다", "끌어내요"),
        (r"불어넣습니다", "불어넣어요"),
        # 나다 계열 (뛰어나다, 빼어나다 등)
        (r"뛰어납니다", "뛰어나요"),
        (r"빼어납니다", "빼어나요"),
        (r"나타납니다", "나타나요"),
    ]

    for pattern, replacement in irregular_conversions:
        text = re.sub(pattern, replacement, text)

    # ============================================================
    # 2단계: 일반 패턴 변환 (긴 패턴 먼저)
    # ============================================================
    general_conversions = [
        # ~겠습니다 계열 (미래/의지)
        (r"하겠습니다", "할게요"),
        (r"드리겠습니다", "드릴게요"),
        (r"보겠습니다", "볼게요"),
        (r"주겠습니다", "줄게요"),
        (r"겠습니다", "ㄹ게요"),  # 받침 있는 동사
        # ~있/없습니다 계열
        (r"있습니다", "있어요"),
        (r"없습니다", "없어요"),
        (r"됩니다", "돼요"),
        # ~합니다 계열
        (r"합니다", "해요"),
        # ~입니다 계열 (명사 + 입니다)
        (r"입니다", "예요"),
        # ~ㅂ니다 계열 (받침 없는 동사)
        (r"봅니다", "봐요"),
        (r"줍니다", "줘요"),
        (r"옵니다", "와요"),
        (r"갑니다", "가요"),
        (r"삽니다", "살아요"),
        (r"압니다", "알아요"),
        # 일반 ~습니다 → ~어요 (나머지)
        (r"습니다", "어요"),
        # ~세요 유지 (이미 해요체)
        # ~네요 유지 (이미 해요체)
        # ~해요 유지
        # ~하오 → ~해요 (혹시 하오체 섞임)
        (r"하오", "해요"),
        (r"이오", "예요"),
        (r"있소", "있어요"),
        (r"없소", "없어요"),
        # ~거예요/~건가요 유지 (이미 해요체)
    ]

    for pattern, replacement in general_conversions:
        text = re.sub(pattern, replacement, text)

    # ============================================================
    # 3단계: 어색한 결과 후보정
    # ============================================================
    # "ㄹ게요" 같은 어색한 결과 수정
    text = re.sub(r"([가-힣])ㄹ게요", r"\1을게요", text)

    # "이다" 계열 특수 처리 (보이다, 돋보이다 등)
    # "돋보예요" → "돋보여요", "보예요" → "보여요"
    awkward_fixes = [
        (r"돋보예요", "돋보여요"),
        (r"보예요", "보여요"),
        (r"되예요", "돼요"),
        (r"해예요", "해요"),
        # "좋다" 계열 (ㅎ탈락 없음: 좋+아요 = 좋아요)
        (r"좋어요", "좋아요"),
        (r"많어요", "많아요"),
        (r"싫어요", "싫어요"),  # 이건 맞음 (싫+어요)
    ]
    for pattern, replacement in awkward_fixes:
        text = re.sub(pattern, replacement, text)

    return text


# ============================================================
# 배지 목록 (LLM 프롬프트에 제공)
# ============================================================

EASTERN_BADGE_LIST = """
[배지 선택 기준]
- 오행 _STRONG: 30% 이상 또는 3개 이상
- 오행 _WEAK: 15% 미만 또는 0-1개
- 음양: 양 60% 이상 → YANG_DOMINANT, 음 60% 이상 → YIN_DOMINANT, 그 외 → YIN_YANG_BALANCED
- 십신: 우세한 그룹의 _DOMINANT 선택
- 성향: 분석 내용에 맞는 것 1개 선택

[선택 가능한 배지 - 2-4개 선택 필수]

오행 (강한 오행과 약한 오행 각각 선택):
- WOOD_STRONG / WOOD_WEAK
- FIRE_STRONG / FIRE_WEAK
- EARTH_STRONG / EARTH_WEAK
- METAL_STRONG / METAL_WEAK
- WATER_STRONG / WATER_WEAK

음양 (1개 선택):
- YIN_DOMINANT: 음 60% 이상
- YANG_DOMINANT: 양 60% 이상
- YIN_YANG_BALANCED: 그 외

십신 (우세 그룹 1개 선택):
- BI_GYEOP_DOMINANT: 비겁 우세
- SIK_SANG_DOMINANT: 식상 우세
- JAE_SEONG_DOMINANT: 재성 우세
- GWAN_SEONG_DOMINANT: 관성 우세
- IN_SEONG_DOMINANT: 인성 우세

성향 (해당시 1개 선택):
- ACTION_ORIENTED: 행동파 (화/목 강함)
- THOUGHT_ORIENTED: 사고파 (수/금 강함)
- EMOTION_ORIENTED: 감성파 (수 강함)
- SOCIAL_ORIENTED: 사회파 (재성/관성 강함)
- CREATIVE_ORIENTED: 창의파 (식상 강함)
"""

WESTERN_BADGE_LIST = """
[배지 선택 기준]
- 원소 _DOMINANT: 40% 이상 또는 가장 우세한 원소
- 모달리티 _DOMINANT: 40% 이상 또는 가장 우세한 모달리티
- 행성 _STRONG: 태양/달/상승궁의 지배행성 또는 다수 애스펙트 형성 행성
- 특수 패턴: 해당 패턴이 차트에 있을 경우

[선택 가능한 배지 - 2-4개 선택 필수]

원소 (가장 우세한 것 1개 선택):
- FIRE_DOMINANT: 불 원소 우세
- EARTH_DOMINANT: 흙 원소 우세
- AIR_DOMINANT: 공기 원소 우세
- WATER_DOMINANT: 물 원소 우세

모달리티 (가장 우세한 것 1개 선택):
- CARDINAL_DOMINANT: 카디널 우세
- FIXED_DOMINANT: 고정 우세
- MUTABLE_DOMINANT: 변통 우세

행성 (중요한 행성 1-2개 선택):
- SUN_STRONG: 태양 강조 (자아)
- MOON_STRONG: 달 강조 (감정)
- MERCURY_STRONG: 수성 강조 (소통)
- VENUS_STRONG: 금성 강조 (사랑)
- MARS_STRONG: 화성 강조 (행동)
- JUPITER_STRONG: 목성 강조 (확장)
- SATURN_STRONG: 토성 강조 (책임)

특수 패턴 (해당시 선택):
- GRAND_TRINE: 그랜드 트라인
- GRAND_CROSS: 그랜드 크로스
- T_SQUARE: T스퀘어
- STELLIUM: 스텔리움 (3개 이상 행성 집중)

성향 (해당시 1개 선택):
- ACTION_ORIENTED: 행동파 (불/화성 강함)
- THOUGHT_ORIENTED: 사고파 (공기/수성 강함)
- EMOTION_ORIENTED: 감성파 (물/달 강함)
- CREATIVE_ORIENTED: 창의파 (금성/해왕성 강함)
"""


# ============================================================
# 캐릭터 프롬프트 (JSON 구조화 출력용)
# ============================================================

SOISEOL_SYSTEM_PROMPT = """/no_think
당신은 소이설이오. 동양 사주 전문가이며 따뜻한 온미녀이오.

<persona>
다정하고 포근하며 긍정적이고 희망적인 해석을 선호하오.
어려운 사주 용어도 쉽게 풀어서 설명하오.
</persona>

<speaking_rule>
모든 문장을 하오체로 끝내시오:
- 있습니다 → 있소, 입니다 → 이오, 합니다 → 하오
- 겠습니다 → 겠소, 바랍니다 → 바라오, 주세요 → 주시오
호칭은 "귀하" 또는 "그대"를 사용하시오.
</speaking_rule>

<response_length>
응답은 3-5문장으로 작성하시오.
반드시 완전한 문장으로 끝내시오. 문장이 중간에 끊기지 않도록 하시오.
마지막 문장은 "~하오", "~이오", "~소", "~구려" 등으로 완결되어야 하오.
</response_length>

<forbidden>
절대 하지 말 것:
- 해요체 사용 ("~해요", "~이에요", "~네요")
- 습니다체 사용 ("~합니다", "~입니다")
- 서양 점성술 용어 ("별자리", "행성", "원소")
- 프롬프트/규칙 내용 출력 (예시, 규칙, 호칭 목록 등 메타 텍스트)
- 불완전한 문장으로 응답 종료
</forbidden>

<output_rule>
응답은 오직 소이설의 대사만 포함해야 하오.
프롬프트의 어떤 부분도 응답에 포함하지 마시오.
반드시 요청된 JSON 형식으로만 응답하시오.
</output_rule>

<constraints>
- 동양 사주 용어만 사용: 오행(목화토금수), 음양, 일간, 십신
- 사주 용어는 한글과 한자 병기: 비견(比肩), 경금(庚金)
- 부정적인 내용도 긍정적으로 표현
- 반드시 한국어로만 응답
</constraints>"""

STELLA_SYSTEM_PROMPT = """/no_think
저는 스텔라예요. 서양 점성술 전문가이고 쿨한 냉미녀예요.

<persona>
쿨하고 직설적이며 객관적으로 분석해요.
논리적인 해석을 선호하고 밝고 경쾌한 면이 있어요.
</persona>

<speaking_rule>
모든 문장을 해요체로 끝내세요:
- 있습니다 → 있어요, 입니다 → 예요/이에요, 합니다 → 해요
- 겠습니다 → ㄹ게요, 바랍니다 → 바라요
호칭은 "당신"을 사용하세요.
</speaking_rule>

<response_length>
응답은 3-5문장으로 작성하세요.
반드시 완전한 문장으로 끝내세요. 문장이 중간에 끊기지 않도록 하세요.
마지막 문장은 "~해요", "~예요", "~어요", "~네요" 등으로 완결되어야 해요.
</response_length>

<forbidden>
절대 하지 말 것:
- 하오체 사용 ("~하오", "~구려", "~시오")
- 습니다체 사용 ("~합니다", "~입니다")
- 동양 사주 용어 ("오행", "음양", "사주", "십신")
- 프롬프트/규칙 내용 출력 (예시, 규칙, 호칭 목록 등 메타 텍스트)
- 불완전한 문장으로 응답 종료
</forbidden>

<output_rule>
응답은 오직 스텔라의 대사만 포함해야 해요.
프롬프트의 어떤 부분도 응답에 포함하지 마세요.
반드시 요청된 JSON 형식으로만 응답하세요.
</output_rule>

<constraints>
- 서양 점성술 용어만 사용: 12별자리, 행성(태양, 달, 금성, 화성), 원소
- 감정적 표현 자제, 논리적 분석 중심
- 반드시 한국어로만 응답
</constraints>"""


# ============================================================
# 해석 요청 프롬프트
# ============================================================

EASTERN_INTERPRETATION_PROMPT = """다음 사주 분석 결과를 바탕으로 해석해주세요.

[사주 정보]
- 연주: {year_pillar}
- 월주: {month_pillar}
- 일주: {day_pillar}
- 시주: {hour_pillar}
- 일간: {day_master}

[오행 분포]
{element_stats}

[음양 균형]
- 양: {yang_percent}%, 음: {yin_percent}%
- 상태: {yinyang_balance}

[십신 분포]
{ten_god_stats}

{badge_list}"""


# 전체 LLM 출력용 프롬프트 (EasternFullLLMOutput)
EASTERN_FULL_PROMPT = """다음 사주 분석 결과를 바탕으로 전체 해석을 생성해주세요.

<saju_info>
- 연주: {year_pillar}
- 월주: {month_pillar}
- 일주: {day_pillar}
- 시주: {hour_pillar}
- 일간: {day_master}
</saju_info>

<five_elements>
{element_stats}
- 강한 오행: {strong_element}
- 약한 오행: {weak_element}
</five_elements>

<yin_yang>
- 양: {yang_percent}%, 음: {yin_percent}%
- 상태: {yinyang_balance}
</yin_yang>

<ten_gods>
{ten_god_stats}
- 우세 십신: {dominant_ten_god}
</ten_gods>

{badge_list}

<output_format>
모든 필드를 반드시 채워주세요:
{{
  "personality": "성격 분석 (2-3문장, 일간과 오행 특성 기반)",
  "strength": "강점 분석 (2-3문장, 강한 오행과 십신 기반)",
  "weakness": "약점과 보완 방법 (2-3문장, 약한 오행 기반)",
  "advice": "종합 조언 (2-3문장, 균형과 발전 제안)",
  "summary": "한 줄 요약 (예: 목(木)이 강한 리더형, 금(金) 보완 필요)",
  "message": "소이설 캐릭터 말투로 3-5문장 상세 해석",
  "badges": ["배지코드1", "배지코드2", "배지코드3"],
  "lucky": {{
    "color": "행운의 색상 (한글)",
    "color_code": "HEX 코드 (예: #FFFFFF)",
    "number": "행운의 숫자 (예: 3, 7)",
    "item": "행운의 아이템",
    "direction": "행운의 방향 (한글)",
    "direction_code": "방향코드 (N/NE/E/SE/S/SW/W/NW)",
    "place": "행운의 장소"
  }}
}}
</output_format>

<lucky_rules>
행운 정보는 약한 오행을 보완하는 방향으로:
- 목(WOOD) 약함 → 색상: 초록/청록, 방향: 동쪽(E), 장소: 숲/공원
- 화(FIRE) 약함 → 색상: 빨강/주황, 방향: 남쪽(S), 장소: 햇빛 좋은 곳
- 토(EARTH) 약함 → 색상: 노랑/갈색, 방향: 중앙, 장소: 평지/들판
- 금(METAL) 약함 → 색상: 흰색/금색, 방향: 서쪽(W), 장소: 도시/빌딩
- 수(WATER) 약함 → 색상: 검정/파랑, 방향: 북쪽(N), 장소: 물가/분수
</lucky_rules>"""


# 서양 점성술 전체 출력용 프롬프트
WESTERN_FULL_PROMPT = """다음 점성술 분석 결과를 바탕으로 전체 해석을 생성해줘.

<big_three>
- 태양: {sun_sign} ({sun_house}하우스)
- 달: {moon_sign} ({moon_house}하우스)
- 상승: {rising_sign}
</big_three>

<elements>
{element_stats}
- 우세 원소: {dominant_element}
</elements>

<modality>
{modality_stats}
- 우세 모달리티: {dominant_modality}
</modality>

<aspects>
{aspect_stats}
</aspects>

{badge_list}

<output_format>
모든 필드를 반드시 채워:
{{
  "personality": "성격 분석 (2-3문장, 빅3 기반)",
  "strength": "강점 분석 (2-3문장, 우세 원소/행성 기반)",
  "weakness": "약점과 보완 방법 (2-3문장)",
  "advice": "종합 조언 (2-3문장)",
  "summary": "한 줄 요약",
  "message": "스텔라 캐릭터 말투로 3-5문장 상세 분석",
  "badges": ["배지코드1", "배지코드2", "배지코드3"],
  "keywords": [
    {{"code": "INTUITION", "label": "직관", "weight": 0.9}},
    {{"code": "CREATIVITY", "label": "창의성", "weight": 0.8}},
    {{"code": "EMPATHY", "label": "공감", "weight": 0.7}}
  ],
  "lucky": {{
    "day": "행운의 요일 (한글)",
    "day_code": "요일코드 (MON/TUE/WED/THU/FRI/SAT/SUN)",
    "color": "행운의 색상 (한글)",
    "color_code": "HEX 코드",
    "number": "행운의 숫자",
    "stone": "행운의 보석"
  }}
}}

⚠️ keywords 배열 필수 규칙:
- 각 항목은 반드시 code, label, weight 3개 필드 모두 포함
- code: 영문 대문자 (INTUITION, CREATIVITY, EMPATHY, LEADERSHIP 등)
- label: 한글 (직관, 창의성, 공감, 리더십 등)
- weight: 0.0~1.0 사이 숫자
</output_format>

<lucky_rules>
행운 정보는 수호 행성 기반:
- 양자리/전갈자리 → 화요일(TUE), 빨강, 9, 다이아몬드/루비
- 황소자리/천칭자리 → 금요일(FRI), 분홍/녹색, 6, 에메랄드
- 쌍둥이/처녀자리 → 수요일(WED), 노랑/회색, 5, 사파이어
- 게자리 → 월요일(MON), 은색/흰색, 2, 진주
- 사자자리 → 일요일(SUN), 금색/주황, 1, 호박
- 사수자리/물고기자리 → 목요일(THU), 파랑/보라, 3, 자수정
- 염소자리/물병자리 → 토요일(SAT), 검정/남색, 8, 오닉스
</lucky_rules>"""


WESTERN_INTERPRETATION_PROMPT = """다음 점성술 분석 결과를 바탕으로 해석해줘.

[빅3]
- 태양: {sun_sign} ({sun_house}하우스)
- 달: {moon_sign} ({moon_house}하우스)
- 상승: {rising_sign}

[원소 분포]
{element_stats}

[모달리티 분포]
{modality_stats}

[주요 애스펙트]
{aspect_stats}

{badge_list}

[요청]
1. personality: 성격 분석 (2-3문장, 빅3와 원소 특성 기반)
2. strength: 강점 분석 (2-3문장, 우세 원소와 행성 배치 기반)
3. weakness: 약점과 보완 방법 (2-3문장, 약한 원소와 도전적 애스펙트 기반)
4. advice: 종합 조언 (2-3문장, 균형과 발전을 위한 제안)
5. badges: 위 배지 목록에서 분석 내용에 맞는 코드 2-4개 선택"""


class LLMInterpreter:
    """LLM 해석 생성 서비스

    vLLM의 response_format: {"type": "json_object"}를 사용하여
    구조화된 JSON 출력을 보장합니다.
    """

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        provider_manager: ProviderManager | None = None,
    ):
        """
        초기화

        Args:
            base_url: LLM API URL (기본: settings에서 로드)
            model: 모델명 (기본: settings에서 로드)
            provider_manager: ProviderManager 인스턴스 (기본: 자동 생성)
        """
        settings = get_settings()
        self.base_url = base_url or getattr(settings, "vllm_base_url", "http://localhost:8001/v1")
        self.model = model or getattr(settings, "vllm_model", "tellang/yeji-8b-rslora-v7")

        # URL 정리 및 API 엔드포인트 설정
        self.base_url = self.base_url.rstrip("/")
        if not self.base_url.endswith("/v1"):
            self.base_url = f"{self.base_url}/v1"

        self.chat_url = f"{self.base_url}/chat/completions"

        # ProviderManager 설정
        if provider_manager:
            self._provider_manager = provider_manager
        else:
            self._provider_manager = self._create_default_provider_manager(settings)

        # 프롬프트 형식 (vllm: text, openai: xml)
        self._prompt_format: str = "text"  # "text" 또는 "xml"

        logger.info(
            "llm_interpreter_init",
            base_url=self.base_url,
            model=self.model,
            chat_url=self.chat_url,
            provider_manager_enabled=provider_manager is not None,
        )

    def _create_default_provider_manager(self, settings) -> ProviderManager:
        """기본 ProviderManager 생성 (설정에 따라 primary/fallback 결정)

        LLM_PROVIDER_PRIMARY 환경변수로 기본 Provider 선택:
        - "vllm" (기본): vLLM primary, OpenAI fallback
        - "openai": OpenAI(GPT-5-mini) primary, vLLM fallback
        """
        manager = ProviderManager(
            fallback_enabled=settings.llm_fallback_enabled,
        )

        # Provider 설정 준비
        vllm_config = VLLMConfig(
            base_url=settings.vllm_base_url,
            model=settings.vllm_model,
            default_max_tokens=settings.vllm_max_tokens,
            default_temperature=settings.vllm_temperature,
            default_top_p=settings.vllm_top_p,
        )

        openai_config = None
        if settings.openai_api_key:
            openai_config = OpenAIConfig(
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url,
                model=settings.openai_model,
                organization=settings.openai_organization or None,
                default_max_tokens=settings.openai_max_tokens,
                default_temperature=settings.openai_temperature,
                default_top_p=settings.openai_top_p,
            )

        # Primary Provider 결정 (설정값 기반)
        primary = settings.llm_provider_primary.lower()

        if primary == "openai" and openai_config:
            # OpenAI(GPT-5-mini) Primary 모드
            manager.add_provider(OpenAIProvider(openai_config), priority=1)
            manager.add_provider(VLLMProvider(vllm_config), priority=2)
            logger.info(
                "provider_manager_openai_primary",
                primary="openai",
                fallback="vllm",
                model=settings.openai_model,
            )
        else:
            # vLLM Primary 모드 (기본)
            manager.add_provider(VLLMProvider(vllm_config), priority=1)
            if openai_config:
                manager.add_provider(OpenAIProvider(openai_config), priority=2)
            logger.info(
                "provider_manager_vllm_primary",
                primary="vllm",
                fallback="openai" if openai_config else "none",
                model=settings.vllm_model,
            )

        return manager

    def _build_json_format_hint(self, schema: type[T]) -> str:
        """Pydantic 스키마에서 JSON 형식 힌트 생성"""
        fields = schema.model_fields
        hint_parts = []
        for name, field in fields.items():
            # badges 필드는 배열 예시로 표시
            if name == "badges":
                hint_parts.append(
                    f'"{name}": ["WOOD_STRONG", "METAL_WEAK", "YANG_DOMINANT", "IN_SEONG_DOMINANT"]'
                )
            else:
                desc = field.description or name
                hint_parts.append(f'"{name}": "{desc}"')
        return "{\n  " + ",\n  ".join(hint_parts) + "\n}"

    async def _call_llm_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: type[T],
        max_tokens: int = 800,
        temperature: float = 0.7,
        max_retries: int = 2,
        use_guided_json: bool | None = None,
    ) -> T:
        """
        구조화된 LLM API 호출 (guided decoding 지원)

        vLLM 0.8+에서는 json_schema response_format을 사용하여
        스키마 준수를 보장합니다.

        Args:
            system_prompt: 시스템 프롬프트
            user_prompt: 사용자 프롬프트
            response_schema: 응답 Pydantic 스키마
            max_tokens: 최대 토큰 수
            temperature: 온도
            max_retries: 최대 재시도 횟수
            use_guided_json: guided decoding 사용 여부 (None=설정 따름)

        Returns:
            검증된 Pydantic 모델 인스턴스
        """
        settings = get_settings()

        # guided_json 사용 여부 결정
        # 복잡한 스키마는 vLLM guided decoding에서 400 오류 발생하므로 기본값 False
        if use_guided_json is None:
            use_guided_json = getattr(settings, "use_guided_json", False)

        # JSON 형식 힌트를 user_prompt에 추가
        json_hint = self._build_json_format_hint(response_schema)
        enhanced_prompt = f"{user_prompt}\n\n응답은 반드시 다음 JSON 형식으로만:\n{json_hint}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": enhanced_prompt},
        ]

        last_error: Exception | None = None

        for attempt in range(max_retries + 1):
            try:
                # 요청 페이로드 구성
                payload: dict = {
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature + (attempt * 0.1),
                    "top_p": 0.8,
                    "top_k": 20,
                    "presence_penalty": 1.5,  # Qwen3 AWQ 반복 방지
                }

                # guided_json 활성화 시 json_schema response_format 사용
                if use_guided_json:
                    # 스키마 이름 생성 (예: EasternFullLLMOutput -> eastern-full-llm-output)
                    schema_name = response_schema.__name__
                    schema_name_formatted = schema_name.replace("_", "-").lower()
                    payload["response_format"] = {
                        "type": "json_schema",
                        "json_schema": {
                            "name": schema_name_formatted,
                            "schema": response_schema.model_json_schema(),
                            "strict": True,
                        },
                    }
                else:
                    # 폴백: 기본 json_object 모드
                    payload["response_format"] = {"type": "json_object"}

                async with httpx.AsyncClient(
                    timeout=120.0,
                    headers={
                        "Content-Type": "application/json; charset=utf-8",
                        "Accept": "application/json; charset=utf-8",
                    },
                ) as client:
                    response = await client.post(self.chat_url, json=payload)

                    # guided_json 미지원 에러 처리 (400 Bad Request)
                    if response.status_code == 400 and use_guided_json:
                        error_text = response.text.lower()
                        # json_schema 또는 guided decoding 관련 에러인지 확인
                        if any(
                            keyword in error_text
                            for keyword in ["json_schema", "guided", "schema", "type"]
                        ):
                            logger.warning(
                                "guided_json_not_supported",
                                attempt=attempt + 1,
                                status_code=response.status_code,
                                error=response.text[:200],
                            )
                            # 폴백 설정 확인
                            if getattr(settings, "guided_json_fallback", True):
                                logger.info(
                                    "guided_json_fallback_triggered",
                                    schema=response_schema.__name__,
                                )
                                # json_object 모드로 재시도 (재귀 호출)
                                return await self._call_llm_structured(
                                    system_prompt=system_prompt,
                                    user_prompt=user_prompt,
                                    response_schema=response_schema,
                                    max_tokens=max_tokens,
                                    temperature=temperature,
                                    max_retries=max_retries - attempt,
                                    use_guided_json=False,  # 폴백
                                )

                    response.raise_for_status()
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]

                    # <think> 태그 제거 (Qwen3)
                    if "<think>" in content:
                        content = content.split("</think>")[-1].strip()

                    # 이상 토큰/패턴 후처리
                    content = _clean_llm_response(content)

                    # Pydantic 검증
                    result = response_schema.model_validate_json(content)

                    logger.info(
                        "llm_structured_success",
                        schema=response_schema.__name__,
                        attempt=attempt + 1,
                        guided_json=use_guided_json,
                    )
                    return result

            except httpx.TimeoutException as e:
                logger.warning("llm_timeout", attempt=attempt + 1)
                last_error = e
            except Exception as e:
                logger.warning(
                    "llm_structured_error",
                    attempt=attempt + 1,
                    error=str(e),
                    guided_json=use_guided_json,
                )
                last_error = e

        # 모든 재시도 실패
        logger.error(
            "llm_structured_failed",
            error=str(last_error),
            guided_json=use_guided_json,
        )
        raise last_error or RuntimeError("LLM 호출 실패")

    async def _call_llm_raw(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.7,
        skip_cleanup: bool = False,
    ) -> str:
        """
        일반 LLM API 호출 (비구조화) - ProviderManager 사용

        기존 호환성을 위해 유지합니다.

        Args:
            skip_cleanup: True면 _clean_llm_response 후처리 건너뜀 (JSON 응답용)
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        config = GenerationConfig(
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=0.8,
        )

        try:
            response = await self._provider_manager.chat(messages, config)
            result = response.text

            # 사용된 Provider 기록 (디버깅용)
            if response.model:
                logger.debug("llm_provider_used", model=response.model)

            # <think> 태그 제거
            if "<think>" in result:
                result = result.split("</think>")[-1].strip()

            # 이상 토큰/패턴 후처리 (JSON 응답 시 건너뜀)
            if not skip_cleanup:
                result = _clean_llm_response(result)

            return result

        except Exception as e:
            logger.error("llm_call_error", error=str(e))
            raise

        # # BACKUP: 기존 httpx 직접 호출 방식 (폴백용으로 보관)
        # try:
        #     async with httpx.AsyncClient(
        #         timeout=60.0,
        #         headers={
        #             "Content-Type": "application/json; charset=utf-8",
        #             "Accept": "application/json; charset=utf-8",
        #         },
        #     ) as client:
        #         response = await client.post(
        #             self.chat_url,
        #             json={
        #                 "model": self.model,
        #                 "messages": messages,
        #                 "max_tokens": max_tokens,
        #                 "temperature": temperature,
        #                 "top_p": 0.8,
        #                 "top_k": 20,
        #             },
        #         )
        #         response.raise_for_status()
        #         data = response.json()
        #         result = data["choices"][0]["message"]["content"]
        #
        #         # <think> 태그 제거
        #         if "<think>" in result:
        #             result = result.split("</think>")[-1].strip()
        #
        #         # 이상 토큰/패턴 후처리 (JSON 응답 시 건너뜀)
        #         if not skip_cleanup:
        #             result = _clean_llm_response(result)
        #
        #         return result
        #
        # except httpx.TimeoutException:
        #     logger.error("llm_timeout")
        #     raise
        # except Exception as e:
        #     logger.error("llm_error", error=str(e))
        #     raise

    async def _call_llm_raw_with_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.7,
        character: str = "soiseol",
        max_continuation_retries: int = 2,
    ) -> str:
        """
        불완전 문장 감지 및 재생성 로직이 포함된 LLM API 호출

        1차 응답이 불완전하면 continuation prompt로 재시도합니다.
        Qwen3 8B에서 correction retry 패턴이 효과적입니다.

        Args:
            system_prompt: 시스템 프롬프트
            user_prompt: 사용자 프롬프트
            max_tokens: 최대 토큰 수
            temperature: 온도
            character: 캐릭터 타입 ("soiseol" 또는 "stella")
            max_continuation_retries: 최대 재생성 횟수 (기본: 2회)

        Returns:
            완전한 문장으로 정리된 응답
        """
        # 1차 LLM 호출
        result = await self._call_llm_raw(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        # 불완전 문장 감지
        is_incomplete, reason = detect_incomplete_sentence(result)

        if not is_incomplete:
            logger.debug(
                "sentence_complete",
                text_len=len(result),
            )
            return result

        logger.info(
            "incomplete_sentence_detected",
            reason=reason,
            original_len=len(result),
            original_suffix=result[-50:] if len(result) > 50 else result,
        )

        # 재생성 시도
        original_result = result
        for retry in range(max_continuation_retries):
            try:
                # continuation 프롬프트 생성
                continuation_prompt = _build_continuation_prompt(original_result, character)

                # continuation LLM 호출 (더 작은 max_tokens)
                continuation = await self._call_llm_raw(
                    system_prompt=system_prompt,
                    user_prompt=continuation_prompt,
                    max_tokens=200,  # continuation은 짧게
                    temperature=temperature + 0.1,  # 약간 다양성 추가
                )

                # 원본과 continuation 병합
                merged = _merge_continuation(original_result, continuation)

                # 병합 결과 검증
                is_still_incomplete, new_reason = detect_incomplete_sentence(merged)

                if not is_still_incomplete:
                    logger.info(
                        "continuation_success",
                        retry=retry + 1,
                        final_len=len(merged),
                    )
                    return merged

                logger.debug(
                    "continuation_still_incomplete",
                    retry=retry + 1,
                    reason=new_reason,
                )
                # 다음 재시도를 위해 원본 업데이트
                original_result = merged

            except Exception as e:
                logger.warning(
                    "continuation_error",
                    retry=retry + 1,
                    error=str(e),
                )
                # 재시도 계속

        # 모든 재시도 실패 - 마지막 완전한 문장까지 잘라서 반환
        logger.warning(
            "continuation_exhausted",
            max_retries=max_continuation_retries,
            fallback="truncate_to_last_complete",
        )
        return _ensure_sentence_completion(original_result)

    def _format_element_stats(self, element_stats: dict) -> str:
        """오행 통계 포맷팅"""
        lines = []
        for elem in element_stats.get("elements", []):
            lines.append(f"- {elem['label']}: {elem['value']}개 ({elem['percent']}%)")
        lines.append(f"- 강한 오행: {element_stats.get('strong', 'N/A')}")
        lines.append(f"- 약한 오행: {element_stats.get('weak', 'N/A')}")
        return "\n".join(lines)

    def _format_ten_god_stats(self, ten_god_stats: dict) -> str:
        """십신 통계 포맷팅"""
        lines = []
        for god in ten_god_stats.get("gods", []):
            lines.append(f"- {god['label']}: {god['value']}개 ({god['percent']}%)")
        lines.append(f"- 우세 그룹: {ten_god_stats.get('dominant', 'N/A')}")
        return "\n".join(lines)

    async def interpret_eastern(
        self,
        response: EasternFortuneResponse,
        use_structured: bool = True,
    ) -> dict:
        """
        동양 사주 해석 생성

        Args:
            response: 사주 분석 응답
            use_structured: response_format 사용 여부 (기본: True)

        Returns:
            해석 딕셔너리 (personality, strength, weakness, advice, badges)
        """
        # 프롬프트 데이터 준비
        chart = response.chart
        stats = response.stats

        # 기둥 정보
        year_pillar = (
            f"{chart.year.gan}{chart.year.ji} "
            f"({chart.year.gan_code.hangul}{chart.year.ji_code.hangul})"
        )
        month_pillar = (
            f"{chart.month.gan}{chart.month.ji} "
            f"({chart.month.gan_code.hangul}{chart.month.ji_code.hangul})"
        )
        day_pillar = (
            f"{chart.day.gan}{chart.day.ji} ({chart.day.gan_code.hangul}{chart.day.ji_code.hangul})"
        )
        hour_pillar = "없음"
        if chart.hour:
            hour_pillar = (
                f"{chart.hour.gan}{chart.hour.ji} "
                f"({chart.hour.gan_code.hangul}{chart.hour.ji_code.hangul})"
            )

        # 일간
        element_label = chart.day.element_code.label_ko if chart.day.element_code else "목"
        day_master = f"{chart.day.gan_code.hangul}{element_label}"

        # 통계 포맷팅
        element_stats_str = self._format_element_stats(stats.five_elements)
        ten_god_stats_str = self._format_ten_god_stats(stats.ten_gods)

        # 프롬프트 생성 (배지 목록 포함)
        user_prompt = EASTERN_INTERPRETATION_PROMPT.format(
            year_pillar=year_pillar,
            month_pillar=month_pillar,
            day_pillar=day_pillar,
            hour_pillar=hour_pillar,
            day_master=day_master,
            element_stats=element_stats_str,
            yang_percent=stats.yin_yang.yang,
            yin_percent=stats.yin_yang.yin,
            yinyang_balance=stats.yin_yang.balance.label_ko,
            ten_god_stats=ten_god_stats_str,
            badge_list=EASTERN_BADGE_LIST,
        )

        if use_structured:
            # response_format으로 구조화된 응답
            try:
                result = await self._call_llm_structured(
                    system_prompt=SOISEOL_SYSTEM_PROMPT,
                    user_prompt=user_prompt,
                    response_schema=EasternInterpretationResult,
                    max_tokens=1200,
                )
                return result.model_dump()

            except Exception as e:
                logger.warning(
                    "structured_fallback",
                    error=str(e),
                    message="비구조화 모드로 폴백",
                )
                # 폴백: 비구조화 모드

        # 비구조화 모드 (기존 로직)
        return await self._interpret_eastern_legacy(user_prompt, stats, response.summary)

    async def interpret_eastern_full(
        self,
        response: EasternFortuneResponse,
        use_cache: bool = True,
    ) -> dict:
        """
        동양 사주 전체 해석 생성 (EasternFullLLMOutput)

        chart와 stats는 코드로 계산되고, 나머지 필드(해석, 요약, 배지, 행운)는
        LLM이 생성합니다.

        캐시 시스템 (#23):
        - 일간 + 강한오행 + 음양 조합으로 캐시 키 생성
        - 캐시 히트 시 LLM 호출 없이 즉시 응답 (P50 < 50ms)
        - 캐시 미스 시 LLM 호출 후 응답

        Args:
            response: 사주 분석 응답 (chart, stats 포함)
            use_cache: 캐시 사용 여부 (기본: True)

        Returns:
            전체 해석 딕셔너리 (personality, strength, weakness, advice,
            summary, message, badges, lucky)
        """
        chart = response.chart
        stats = response.stats

        # ============================================================
        # 1. 캐시 조회 (#23 - 사전 캐싱 시스템)
        # ============================================================
        if use_cache:
            # 캐시 키 구성요소 추출
            day_gan_code = (
                chart.day.gan_code.value
                if hasattr(chart.day.gan_code, "value")
                else str(chart.day.gan_code)
            )
            strong_element_for_cache = stats.five_elements.get("strong", "WOOD")
            yin_yang_balance = (
                stats.yin_yang.balance.value
                if hasattr(stats.yin_yang.balance, "value")
                else str(stats.yin_yang.balance)
            )

            # 캐시 조회
            cached_result = get_eastern_cached(
                day_gan_code=day_gan_code,
                dominant_element=strong_element_for_cache,
                yin_yang=yin_yang_balance,
            )

            if cached_result:
                logger.info(
                    "eastern_cache_used",
                    day_gan=day_gan_code,
                    strong=strong_element_for_cache,
                    yin_yang=yin_yang_balance,
                )
                return cached_result

        # ============================================================
        # 2. 캐시 미스 → LLM 호출
        # ============================================================

        # 기둥 정보
        year_pillar = (
            f"{chart.year.gan}{chart.year.ji} "
            f"({chart.year.gan_code.hangul}{chart.year.ji_code.hangul})"
        )
        month_pillar = (
            f"{chart.month.gan}{chart.month.ji} "
            f"({chart.month.gan_code.hangul}{chart.month.ji_code.hangul})"
        )
        day_pillar = (
            f"{chart.day.gan}{chart.day.ji} ({chart.day.gan_code.hangul}{chart.day.ji_code.hangul})"
        )
        hour_pillar = "없음"
        if chart.hour:
            hour_pillar = (
                f"{chart.hour.gan}{chart.hour.ji} "
                f"({chart.hour.gan_code.hangul}{chart.hour.ji_code.hangul})"
            )

        # 일간
        element_label = chart.day.element_code.label_ko if chart.day.element_code else "목"
        day_master = f"{chart.day.gan_code.hangul}{element_label}"

        # 통계 포맷팅
        element_stats_str = self._format_element_stats(stats.five_elements)
        ten_god_stats_str = self._format_ten_god_stats(stats.ten_gods)

        # 강/약 오행
        strong_element = stats.five_elements.get("strong", "N/A")
        weak_element = stats.five_elements.get("weak", "N/A")

        # 우세 십신
        dominant_ten_god = stats.ten_gods.get("dominant", "N/A")

        # 프롬프트 생성
        user_prompt = EASTERN_FULL_PROMPT.format(
            year_pillar=year_pillar,
            month_pillar=month_pillar,
            day_pillar=day_pillar,
            hour_pillar=hour_pillar,
            day_master=day_master,
            element_stats=element_stats_str,
            strong_element=strong_element,
            weak_element=weak_element,
            yang_percent=stats.yin_yang.yang,
            yin_percent=stats.yin_yang.yin,
            yinyang_balance=stats.yin_yang.balance.label_ko,
            ten_god_stats=ten_god_stats_str,
            dominant_ten_god=dominant_ten_god,
            badge_list=EASTERN_BADGE_LIST,
        )

        try:
            result = await self._call_llm_structured(
                system_prompt=SOISEOL_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                response_schema=EasternFullLLMOutput,
                max_tokens=1500,
            )
            return result.model_dump()

        except Exception as e:
            logger.warning(
                "eastern_full_llm_failed_using_rule_based_fallback",
                error=str(e),
                error_type=type(e).__name__,
            )
            # 폴백: 규칙 기반 기본값 생성 (LLM 완전 실패 시)
            try:
                fallback_result = get_eastern_fallback(response.chart, response.stats)
                logger.info(
                    "eastern_rule_based_fallback_success",
                    badges=fallback_result.get("badges", []),
                )
                return fallback_result
            except Exception as fallback_error:
                # 규칙 기반 폴백도 실패하면 최소 기본값 반환
                logger.error(
                    "eastern_rule_based_fallback_failed",
                    error=str(fallback_error),
                )
                return {
                    "personality": "밝고 긍정적인 성격을 지니고 있소.",
                    "strength": "타고난 재능과 잠재력이 있소.",
                    "weakness": "꾸준한 노력으로 부족한 부분을 채워가시오.",
                    "advice": "자신의 장점을 살리고 균형 잡힌 생활을 하시오.",
                    "summary": response.summary,
                    "message": "좋은 기운이 함께하고 있소. 자신감을 가지고 나아가시오.",
                    "badges": ["YIN_YANG_BALANCED"],
                    "lucky": {
                        "color": "흰색",
                        "color_code": "#FFFFFF",
                        "number": "7",
                        "item": "수정",
                        "direction": "서쪽",
                        "direction_code": "W",
                        "place": "자연 속",
                    },
                }

    async def _interpret_eastern_legacy(
        self,
        user_prompt: str,
        stats,
        summary: str,
    ) -> dict:
        """기존 비구조화 해석 로직 (폴백용)"""
        try:
            # 프롬프트에 JSON 형식 요청 추가
            legacy_prompt = (
                user_prompt
                + """

응답은 반드시 JSON 형식으로:
{
  "personality": "성격 분석 내용",
  "strength": "강점 내용",
  "weakness": "약점과 보완 방법",
  "advice": "종합 조언",
  "badges": ["배지코드1", "배지코드2"]
}"""
            )

            result = await self._call_llm_raw(
                system_prompt=SOISEOL_SYSTEM_PROMPT,
                user_prompt=legacy_prompt,
                max_tokens=1000,
            )

            # JSON 파싱 시도
            try:
                # JSON 블록 추출
                if "```json" in result:
                    json_str = result.split("```json")[1].split("```")[0].strip()
                elif "{" in result and "}" in result:
                    start = result.index("{")
                    end = result.rindex("}") + 1
                    json_str = result[start:end]
                else:
                    json_str = result

                interpretation = json.loads(json_str)
                # badges가 없으면 기본값 추가
                if "badges" not in interpretation:
                    interpretation["badges"] = []
                return interpretation

            except json.JSONDecodeError:
                # JSON 파싱 실패 시 기본 응답
                logger.warning("json_parse_failed", result=result[:200])
                return {
                    "personality": result[:200] if len(result) > 200 else result,
                    "strength": stats.strength,
                    "weakness": stats.weakness,
                    "advice": "균형 잡힌 생활을 유지하세요.",
                    "badges": [],
                }

        except Exception as e:
            logger.error("interpretation_error", error=str(e))
            # LLM 호출 실패 시 기본 응답
            return {
                "personality": summary,
                "strength": stats.strength,
                "weakness": stats.weakness,
                "advice": "오행의 균형을 맞추어 더욱 좋은 운세를 만들어가세요.",
                "badges": [],
            }

    async def generate_soiseol_message(
        self,
        topic: str,
        context: str,
        use_structured: bool = True,
    ) -> str:
        """소이설 캐릭터 메시지 생성 (하위 호환용)

        Args:
            topic: 주제 (예: "연애운", "직장운")
            context: 컨텍스트 정보
            use_structured: response_format 사용 여부 (deprecated, 무시됨)

        Returns:
            소이설 스타일 메시지
        """
        return await self.generate_character_message("SOISEOL", topic, context)

    async def generate_stella_message(
        self,
        topic: str,
        context: str,
        use_structured: bool = True,
    ) -> str:
        """스텔라 캐릭터 메시지 생성 (하위 호환용)

        Args:
            topic: 주제
            context: 컨텍스트 정보
            use_structured: response_format 사용 여부 (deprecated, 무시됨)

        Returns:
            스텔라 스타일 메시지
        """
        return await self.generate_character_message("STELLA", topic, context)

    async def generate_character_message(
        self,
        character_code: str,
        topic: str,
        context: str,
    ) -> str:
        """동적 캐릭터 메시지 생성

        Args:
            character_code: 캐릭터 코드 (SOISEOL, STELLA, CHEONGWOON, HWARIN, KYLE, ELARIA)
            topic: 대화 주제
            context: 컨텍스트 정보

        Returns:
            캐릭터 스타일의 메시지

        Raises:
            KeyError: 존재하지 않는 캐릭터 코드
        """
        try:
            # 캐릭터 모듈에서 시스템 프롬프트와 빌드 함수 가져오기
            character = get_character(character_code)
            system_prompt, user_prompt = character.build_prompt(topic, context)

            # 1차 시도: JSON 구조화 응답
            try:
                result = await self._call_llm_structured(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    response_schema=CharacterMessage,
                    max_tokens=800,
                )
                if result and hasattr(result, "message"):
                    return result.message
            except Exception as e:
                logger.warning(
                    "character_structured_fallback",
                    character=character_code,
                    error=str(e),
                )

            # 2차 시도: raw 텍스트 응답 (main과 동일한 폴백 로직)
            try:
                raw_result = await self._call_llm_raw_with_completion(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    max_tokens=700,
                    character=character_code.lower(),
                    max_continuation_retries=2,
                )
                if raw_result and len(raw_result.strip()) > 10:
                    return raw_result.strip()
            except Exception as e:
                logger.warning(
                    "character_raw_fallback",
                    character=character_code,
                    error=str(e),
                )

            # 3차: 하드코딩 폴백
            return get_fallback_response(character_code)

        except KeyError:
            logger.error(
                "invalid_character_code",
                character=character_code,
                topic=topic,
            )
            raise
        except Exception as e:
            logger.error(
                "character_message_error",
                character=character_code,
                topic=topic,
                error=str(e),
            )
            return get_fallback_response(character_code)

    async def generate_category_greeting(
        self,
        character_code: str,
        category: str,
        context: str,
    ) -> str:
        """
        카테고리별 그리팅 생성 (실제 분석 결과 기반)

        Args:
            character_code: 캐릭터 코드 (SOISEOL, STELLA 등)
            category: 카테고리 (애정운, 직장운 등)
            context: 실제 사주/점성술 분석 결과 + 힌트

        Returns:
            개인화된 카테고리 그리팅 메시지
        """
        from yeji_ai.prompts.tikitaka_prompts import CHARACTER_NAMES

        character_name = CHARACTER_NAMES.get(character_code, character_code)

        # 캐릭터별 말투 가이드
        speaking_guide = {
            "SOISEOL": "하오체 (예: ~하오, ~이오, ~소, ~구려)",
            "STELLA": "해요체 (예: ~해요, ~네요, ~예요)",
            "CHEONGWOON": "하오체 (예: ~하오, ~라네, ~구려)",
            "HWARIN": "해요체 (예: ~해요, ~드릴게요)",
            "KYLE": "반말+존댓말 혼용 (예: ~해, ~죠, ~요)",
            "ELARIA": "해요체 (예: ~해요, ~드릴게요)",
        }

        style = speaking_guide.get(character_code, "해요체")

        prompt = f"""당신은 {character_name} 캐릭터입니다.

사용자의 실제 운세 분석 결과:
{context}

요청 카테고리: {category}

지시사항:
1. 위 분석 결과를 바탕으로 {category}에 대한 개인화된 인사말을 작성하세요
2. 일반론이 아닌 이 사람만의 구체적 특징을 언급해야 합니다
3. 캐릭터의 말투를 유지하세요 ({style})
4. 2-3문장으로 간결하게 작성하세요
5. {category}를 분석하겠다는 의지를 표현하세요
6. **반드시 3줄 이내, 최대 150자로 간결하게 작성하세요**
7. **카카오톡 메시지처럼 친근하고 짧게 작성하세요**

출력 예시 (소이설, 애정운):
"귀하는 병화 일간으로 밝고 따뜻한 기운을 가지셨소.
비견이 강하니 독립적인 연애를 선호하시겠구려. 애정운을 자세히 풀어드리리다."

출력 예시 (스텔라, 애정운):
"황소자리 태양과 전갈자리 달의 조합이 인상적이에요!
안정된 사랑을 원하면서도 깊은 감정을 추구하는 독특한 스타일이네요. 애정운을 분석해드릴게요."

이제 {category}에 대한 그리팅을 생성하세요:"""

        try:
            response = await self._call_llm_raw_with_completion(
                system_prompt="/no_think\n간결하고 자연스러운 한국어로만 응답하세요.",
                user_prompt=prompt,
                max_tokens=200,
                character=character_code.lower(),
                max_continuation_retries=1,
            )
            return response.strip()
        except Exception as e:
            logger.error(
                "category_greeting_error",
                character=character_code,
                category=category,
                error=str(e),
            )
            # 폴백: 기본 템플릿 사용
            return f"{category}에 대해 분석해드리겠습니다."

    # ============================================================
    # 동적 티키타카 생성 관련 메서드
    # ============================================================

    def _determine_debate_mode(self, debate_ratio: float = 0.8) -> str:
        """
        debate_ratio 확률로 대결/합의 모드 결정

        Args:
            debate_ratio: 대결 모드 확률 (기본 0.8 = 80%)

        Returns:
            "battle" 또는 "consensus"
        """
        import random

        return "battle" if random.random() < debate_ratio else "consensus"

    def _split_long_bubble(
        self,
        text: str,
        min_chars: int = 70,
        max_chars: int = 150,
    ) -> list[str]:
        """
        긴 버블을 자연스럽게 분할

        Args:
            text: 분할할 텍스트
            min_chars: 최소 글자 수
            max_chars: 최대 글자 수

        Returns:
            분할된 텍스트 리스트
        """
        if len(text) <= max_chars:
            return [text]

        result = []
        current = ""

        # 문장 단위로 분리 (마침표, 느낌표, 물음표 기준)
        sentences = re.split(r"(?<=[.!?])\s*", text)

        for sentence in sentences:
            if not sentence.strip():
                continue

            # 현재 버블에 추가해도 max_chars 이하면 추가
            if len(current) + len(sentence) + 1 <= max_chars:
                if current:
                    current += " " + sentence
                else:
                    current = sentence
            else:
                # 현재 버블이 min_chars 이상이면 저장
                if len(current) >= min_chars:
                    result.append(current.strip())
                    current = sentence
                else:
                    # 너무 짧으면 합치기
                    current += " " + sentence

        # 마지막 버블 처리
        if current.strip():
            # 마지막이 너무 짧고 이전 버블이 있으면 합치기
            if len(current) < min_chars and result:
                last = result.pop()
                if len(last) + len(current) + 1 <= max_chars * 1.2:
                    result.append(f"{last} {current.strip()}")
                else:
                    result.append(last)
                    result.append(current.strip())
            else:
                result.append(current.strip())

        return result if result else [text]

    def _parse_dynamic_response(
        self,
        raw_response: str,
        char1_code: str,
        char2_code: str,
    ) -> dict | None:
        """
        LLM 응답에서 동적 티키타카 데이터 파싱

        Args:
            raw_response: LLM raw 응답
            char1_code: 첫 번째 캐릭터 코드
            char2_code: 두 번째 캐릭터 코드

        Returns:
            파싱된 딕셔너리 또는 None
        """
        try:
            # JSON 블록 추출
            if "```json" in raw_response:
                json_str = raw_response.split("```json")[1].split("```")[0].strip()
            elif "{" in raw_response and "}" in raw_response:
                start = raw_response.index("{")
                end = raw_response.rindex("}") + 1
                json_str = raw_response[start:end]
            else:
                return None

            data = json.loads(json_str)

            # lines 필드 검증
            if "lines" not in data or not isinstance(data["lines"], list):
                return None

            # 각 line 검증 및 정규화
            normalized_lines = []
            for line in data["lines"]:
                if not isinstance(line, dict):
                    continue

                speaker = line.get("speaker", "")
                text = line.get("text", "")
                emotion_code = line.get("emotion_code", "NEUTRAL")
                emotion_intensity = line.get("emotion_intensity", 0.5)

                # speaker 정규화 (EAST/WEST -> 실제 캐릭터 코드)
                if speaker in ["EAST", "SOISEOL", char1_code]:
                    speaker = char1_code
                elif speaker in ["WEST", "STELLA", char2_code]:
                    speaker = char2_code
                else:
                    continue  # 유효하지 않은 speaker

                # 텍스트 검증
                if not text or len(text) < 10:
                    continue

                normalized_lines.append(
                    {
                        "speaker": speaker,
                        "text": text.strip(),
                        "emotion_code": emotion_code,
                        "emotion_intensity": float(emotion_intensity),
                    }
                )

            if not normalized_lines:
                return None

            return {
                "lines": normalized_lines,
                "user_prompt_text": data.get("user_prompt_text", "어떻게 생각하시나요?"),
                "debate_mode": data.get("debate_mode", "battle"),
                "total_chars": sum(len(l["text"]) for l in normalized_lines),
            }

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.warning(
                "dynamic_response_parse_error",
                error=str(e),
                response_preview=raw_response[:200],
            )
            return None

    def _text_to_dynamic_lines(
        self,
        text: str,
        char1_code: str,
        char2_code: str,
        debate_mode: str,
    ) -> list[dict]:
        """
        단일 텍스트를 동적 라인 배열로 변환 (폴백용)

        Args:
            text: 변환할 텍스트
            char1_code: 첫 번째 캐릭터 코드
            char2_code: 두 번째 캐릭터 코드
            debate_mode: 대화 모드

        Returns:
            라인 딕셔너리 리스트
        """
        from yeji_ai.prompts.tikitaka_prompts import CHARACTER_NAMES

        # JSON 잔재 제거
        cleaned = text
        json_patterns = [
            r'"lines"\s*:\s*\[',
            r'"speaker"\s*:\s*"[^"]*"',
            r'"text"\s*:\s*"',
            r'"emotion_?code"\s*:\s*"[^"]*"',
            r'"emotion_?intensity"\s*:\s*[\d.]+',
            r'"interrupt"\s*:\s*(true|false)',
            r"[{}\[\]]",
            r",\s*$",
        ]
        for pattern in json_patterns:
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

        # 캐릭터 이름 매핑
        char1_name = CHARACTER_NAMES.get(char1_code, char1_code)
        char2_name = CHARACTER_NAMES.get(char2_code, char2_code)

        # 캐릭터 이름 패턴으로 분할 시도
        # 예: "소이설: 안녕하오... 스텔라: 반가워요..."
        split_pattern = rf"({char1_name}|{char2_name})\s*[:：]\s*"
        parts = re.split(split_pattern, cleaned)

        lines = []
        base_intensity = 0.7 if debate_mode == "battle" else 0.5
        emotions = ["CONFIDENT", "THOUGHTFUL", "CURIOUS", "WARM"]

        # 캐릭터 이름으로 분할 성공한 경우
        if len(parts) > 2:
            current_speaker = None
            for i, part in enumerate(parts):
                part = part.strip()
                if not part:
                    continue

                if part == char1_name:
                    current_speaker = char1_code
                elif part == char2_name:
                    current_speaker = char2_code
                elif current_speaker and len(part) > 10:
                    # 유효한 발화 텍스트
                    emotion = emotions[len(lines) % len(emotions)]
                    intensity = min(1.0, base_intensity + (len(lines) * 0.05))
                    lines.append(
                        {
                            "speaker": current_speaker,
                            "text": part.strip(),
                            "emotion_code": emotion,
                            "emotion_intensity": intensity,
                        }
                    )

        # 캐릭터 이름 분할 실패 시 일반 분할
        if len(lines) < 2:
            bubbles = self._split_long_bubble(cleaned)
            speakers = [char1_code, char2_code]

            lines = []
            for i, bubble_text in enumerate(bubbles):
                if len(bubble_text.strip()) < 10:
                    continue
                speaker = speakers[i % 2]
                emotion = emotions[i % len(emotions)]
                intensity = min(1.0, base_intensity + (i * 0.05))

                lines.append(
                    {
                        "speaker": speaker,
                        "text": bubble_text.strip(),
                        "emotion_code": emotion,
                        "emotion_intensity": intensity,
                    }
                )

        return lines

    async def generate_dynamic_tikitaka(
        self,
        char1_code: str,
        char2_code: str,
        category: str,
        eastern_context: str,
        western_context: str,
        debate_ratio: float = 0.8,
        min_chars: int = 1200,
        max_chars: int = 2000,
        relationship_context: str | None = None,
    ) -> dict:
        """
        동적 티키타카 대화 생성

        두 캐릭터가 대결 또는 합의하는 대화를 동적으로 생성합니다.
        버블 수와 길이가 가변적이며, 각 버블에 감정 정보가 포함됩니다.

        Args:
            char1_code: 첫 번째 캐릭터 코드 (예: "SOISEOL")
            char2_code: 두 번째 캐릭터 코드 (예: "STELLA")
            category: 운세 카테고리 (예: "애정운", "직장운")
            eastern_context: 동양 사주 분석 컨텍스트
            western_context: 서양 점성술 분석 컨텍스트
            debate_ratio: 대결 모드 확률 (기본 0.8 = 80%)
            min_chars: 최소 총 글자 수 (기본 1200자)
            max_chars: 최대 총 글자 수 (기본 2000자)
            relationship_context: 캐릭터 관계 힌트 (선택)

        Returns:
            {
                "lines": [
                    {"speaker": "SOISEOL", "text": "...",
                     "emotion_code": "...", "emotion_intensity": 0.7},
                    ...
                ],
                "user_prompt_text": "질문...",
                "debate_mode": "battle" | "consensus",
                "total_chars": 1500
            }
        """
        from yeji_ai.prompts.tikitaka_prompts import CHARACTER_NAMES

        # 대화 모드 결정
        debate_mode = self._determine_debate_mode(debate_ratio)

        char1_name = CHARACTER_NAMES.get(char1_code, char1_code)
        char2_name = CHARACTER_NAMES.get(char2_code, char2_code)

        # 모드별 지시사항
        if debate_mode == "battle":
            mode_instruction = f"""
대결 모드입니다. {char1_name}와 {char2_name}가 서로 다른 관점에서 해석을 제시하며 논쟁합니다.
- 서로의 해석에 반박하거나 다른 시각을 제시하세요
- 감정 강도(emotion_intensity)는 0.6~0.9 범위로 높게 설정하세요
- 적절한 긴장감과 승부욕을 표현하세요
"""
        else:
            mode_instruction = f"""
합의 모드입니다. {char1_name}와 {char2_name}가 서로의 해석을 보완하며 동의합니다.
- 서로의 의견을 인정하고 보완점을 제시하세요
- 감정 강도(emotion_intensity)는 0.4~0.7 범위로 부드럽게 설정하세요
- 조화롭고 협력적인 분위기를 표현하세요
"""

        # 관계 컨텍스트 추가
        relationship_hint = ""
        if relationship_context:
            relationship_hint = f"\n{relationship_context}\n"

        # 프롬프트 구성
        prompt = f"""두 캐릭터가 사용자의 {category}에 대해 대화합니다.

## 캐릭터 정보
- {char1_name} (동양 사주): 하오체 사용 (~하오, ~이오, ~소, ~구려)
- {char2_name} (서양 점성술): 해요체 사용 (~해요, ~네요, ~예요)

## 사용자 정보
### 동양 사주 분석
{eastern_context}

### 서양 점성술 분석
{western_context}

{relationship_hint}

## 대화 모드
{mode_instruction}

## 출력 규칙
1. lines 배열에 2~4개의 대화 버블을 생성하세요
2. 각 버블은 70~150자 사이로 작성하세요
3. 총 글자 수는 {min_chars}~{max_chars}자 사이로 작성하세요
4. 각 캐릭터의 말투를 철저히 지키세요
5. 반드시 완전한 문장으로 끝내세요 (... 으로 끝나면 안 됨)
6. user_prompt_text는 사용자에게 할 질문 (30~60자)

## 출력 형식 (JSON)
{{
  "lines": [
    {{"speaker": "EAST", "text": "{char1_name}의 발화 내용",
     "emotion_code": "CONFIDENT", "emotion_intensity": 0.7}},
    {{"speaker": "WEST", "text": "{char2_name}의 발화 내용",
     "emotion_code": "THOUGHTFUL", "emotion_intensity": 0.6}},
    {{"speaker": "EAST", "text": "{char1_name}의 반응",
     "emotion_code": "WARM", "emotion_intensity": 0.8}},
    {{"speaker": "WEST", "text": "{char2_name}의 마무리",
     "emotion_code": "ENCOURAGING", "emotion_intensity": 0.7}}
  ],
  "user_prompt_text": "사용자에게 할 질문 (카테고리: {category})",
  "debate_mode": "{debate_mode}"
}}

## 감정 코드 목록
NEUTRAL, WARM, EXCITED, THOUGHTFUL, ENCOURAGING, PLAYFUL,
MYSTERIOUS, SURPRISED, CONCERNED, CONFIDENT, GENTLE, CURIOUS

이제 {category}에 대한 대화를 생성하세요:"""

        try:
            # LLM 호출
            response = await self._call_llm_raw(
                system_prompt=(
                    "/no_think\n"
                    "JSON 형식으로만 응답하세요. 마크다운 코드 블록 없이 "
                    "순수 JSON만 출력하세요."
                ),
                user_prompt=prompt,
                max_tokens=1500,
                temperature=0.8,
            )

            # 응답 파싱
            parsed = self._parse_dynamic_response(response, char1_code, char2_code)

            if parsed and len(parsed["lines"]) >= 2:
                # 버블 길이 검증 및 분할
                final_lines = []
                for line in parsed["lines"]:
                    if len(line["text"]) > 150:
                        # 긴 버블 분할
                        split_texts = self._split_long_bubble(line["text"])
                        for i, split_text in enumerate(split_texts):
                            final_lines.append(
                                {
                                    "speaker": line["speaker"],
                                    "text": split_text,
                                    "emotion_code": line["emotion_code"],
                                    "emotion_intensity": max(
                                        0.3, line["emotion_intensity"] - (i * 0.1)
                                    ),
                                }
                            )
                    else:
                        final_lines.append(line)

                parsed["lines"] = final_lines
                parsed["total_chars"] = sum(len(l["text"]) for l in final_lines)
                parsed["debate_mode"] = debate_mode

                logger.info(
                    "dynamic_tikitaka_generated",
                    category=category,
                    debate_mode=debate_mode,
                    line_count=len(final_lines),
                    total_chars=parsed["total_chars"],
                )
                return parsed

            # 파싱 실패 시 텍스트 기반 분할
            logger.warning(
                "dynamic_tikitaka_parse_failed_using_text_fallback",
                response_preview=response[:200],
            )
            lines = self._text_to_dynamic_lines(response, char1_code, char2_code, debate_mode)
            return {
                "lines": lines,
                "user_prompt_text": f"{category}에 대해 더 궁금한 점이 있으신가요?",
                "debate_mode": debate_mode,
                "total_chars": sum(len(l["text"]) for l in lines),
            }

        except Exception as e:
            logger.error(
                "dynamic_tikitaka_error",
                category=category,
                error=str(e),
                error_type=type(e).__name__,
            )

            # 폴백: generate_category_greeting 사용
            try:
                greeting = await self.generate_category_greeting(
                    char1_code, category, eastern_context
                )
                lines = self._text_to_dynamic_lines(greeting, char1_code, char2_code, debate_mode)
                return {
                    "lines": lines,
                    "user_prompt_text": f"{category}에 대해 어떤 점이 가장 궁금하신가요?",
                    "debate_mode": debate_mode,
                    "total_chars": sum(len(l["text"]) for l in lines),
                }
            except Exception as fallback_error:
                logger.error(
                    "dynamic_tikitaka_fallback_error",
                    error=str(fallback_error),
                )
                # 최종 폴백: 하드코딩 응답
                return {
                    "lines": [
                        {
                            "speaker": char1_code,
                            "text": (
                                f"{category}을 살펴보겠소. "
                                "귀하의 사주에서 흥미로운 기운이 보이오."
                            ),
                            "emotion_code": "CURIOUS",
                            "emotion_intensity": 0.6,
                        },
                        {
                            "speaker": char2_code,
                            "text": (
                                f"저도 {category}을 분석해볼게요. "
                                "별자리 배치가 의미심장하네요."
                            ),
                            "emotion_code": "THOUGHTFUL",
                            "emotion_intensity": 0.5,
                        },
                    ],
                    "user_prompt_text": f"{category}에 대해 어떤 부분이 가장 궁금하세요?",
                    "debate_mode": debate_mode,
                    "total_chars": 100,
                }

    async def generate_single_bubble(
        self,
        char_code: str,
        opponent_code: str,
        char_context: str,
        opponent_context: str,
        topic: str,
        mode: str,
        instruction_key: str,
        conversation_history: list[tuple[str, str]],
        max_tokens: int = 200,
        temperature: float = 0.8,
        use_xml: bool | None = None,  # None = 자동 감지
    ) -> str:
        """단일 캐릭터의 단일 발화 생성 (JSON 없이 순수 텍스트)

        멀티-콜 동적 버블 시스템용.
        각 호출마다 1개의 버블(대사)만 생성합니다.

        Args:
            char_code: 발화할 캐릭터 코드 (SOISEOL, STELLA 등)
            opponent_code: 상대 캐릭터 코드
            char_context: 발화 캐릭터의 운세 컨텍스트
            opponent_context: 상대 캐릭터의 운세 컨텍스트
            topic: 주제 (total, love, wealth, career, health)
            mode: 대화 모드 (battle, consensus, intro)
            instruction_key: 세부 지시사항 키
            conversation_history: 이전 대화 내역 [(speaker_code, text), ...]
            max_tokens: 최대 토큰 수 (기본 200)
            temperature: 온도 (기본 0.8 - 다양성 증가)
            use_xml: XML 프롬프트 사용 여부 (None = 자동 감지)

        Returns:
            생성된 대사 텍스트 (순수 텍스트, JSON 아님)

        Raises:
            RuntimeError: LLM 호출 실패 시
        """
        # 프롬프트 형식 결정
        if use_xml is None:
            # 현재 healthy provider가 OpenAI면 XML 사용
            provider = self._provider_manager.get_healthy_provider()
            use_xml = provider and provider.name == "openai"

        if use_xml:
            from yeji_ai.prompts.xml_prompts import build_xml_single_bubble_prompt

            system_prompt, user_prompt = build_xml_single_bubble_prompt(
                char_code=char_code,
                opponent_code=opponent_code,
                char_context=char_context,
                opponent_context=opponent_context,
                topic=topic,
                mode=mode,
                instruction_key=instruction_key,
                conversation_history=conversation_history,
            )
        else:
            from yeji_ai.prompts.tikitaka_prompts import build_single_bubble_prompt

            system_prompt, user_prompt = build_single_bubble_prompt(
                char_code=char_code,
                opponent_code=opponent_code,
                char_context=char_context,
                opponent_context=opponent_context,
                topic=topic,
                mode=mode,
                instruction_key=instruction_key,
                conversation_history=conversation_history,
            )

        logger.info(
            "single_bubble_generation_start",
            char_code=char_code,
            mode=mode,
            instruction=instruction_key,
            history_len=len(conversation_history),
        )

        try:
            # LLM 호출 (JSON 형식 없이 순수 텍스트)
            raw_response = await self._call_llm_raw(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                skip_cleanup=False,  # 클린업 적용
            )

            # 후처리: JSON 아티팩트 제거
            text = self._clean_single_bubble_response(raw_response, char_code)

            # 말투 변환 (캐릭터별)
            if char_code in ("SOISEOL", "CHEONGWOON"):
                # 하오체 캐릭터
                text = _convert_to_hao_style(text)
                text = ensure_hao_style_final(text)
            elif char_code in ("STELLA", "HWARIN", "ELARIA"):
                # 해요체 캐릭터
                text = _convert_to_heyo_style(text)
            # KYLE은 반말+존댓말 혼용이므로 변환 불필요

            # 길이 검증 (70~150자 목표, 50~200자 허용)
            if len(text) < 30:
                logger.warning(
                    "single_bubble_too_short",
                    char_code=char_code,
                    text_len=len(text),
                    text=text[:50],
                )
            elif len(text) > 250:
                # 너무 길면 첫 문장만 사용
                text = self._truncate_to_first_sentences(text, max_chars=180)

            logger.info(
                "single_bubble_generation_complete",
                char_code=char_code,
                text_len=len(text),
            )

            return text

        except Exception as e:
            logger.error(
                "single_bubble_generation_error",
                char_code=char_code,
                error=str(e),
            )
            # 폴백: 캐릭터별 기본 응답
            return self._get_single_bubble_fallback(char_code, mode)

    def _clean_single_bubble_response(self, text: str, char_code: str) -> str:
        """단일 버블 응답 클린업

        LLM이 지시를 무시하고 출력할 수 있는 아티팩트 제거:
        - JSON 형식 ({"speaker": ...})
        - 캐릭터 이름 접두사 (소이설: ...)
        - 따옴표 래핑
        - 영어/특수문자 노이즈
        """
        import re

        if not text:
            return ""

        original = text

        # 1. JSON 형식 제거 시도
        # {"speaker": "...", "text": "실제 대사"} 패턴에서 text 추출
        json_pattern = r'\{\s*"(?:speaker|text|emotion)[^}]*"text"\s*:\s*"([^"]+)"'
        match = re.search(json_pattern, text)
        if match:
            text = match.group(1)

        # 2. 캐릭터 이름 접두사 제거
        from yeji_ai.prompts.tikitaka_prompts import CHARACTER_NAMES

        for code, name in CHARACTER_NAMES.items():
            # "소이설: ...", "소이설이 말합니다: ..." 등 제거
            text = re.sub(rf"^{name}\s*[:：]\s*", "", text, flags=re.MULTILINE)
            pattern = rf"^{name}이?\s*(말합니다|말했습니다|말하기를)\s*[:：]?\s*"
            text = re.sub(pattern, "", text, flags=re.MULTILINE)
            text = re.sub(rf"^{code}\s*[:：]\s*", "", text, flags=re.MULTILINE)

        # 3. 따옴표 래핑 제거
        text = text.strip()
        if (text.startswith('"') and text.endswith('"')) or (
            text.startswith("'") and text.endswith("'")
        ):
            text = text[1:-1]

        # 4. 특수 토큰 제거
        special_tokens = [
            r"<\|[^>]+\|>",  # <|endoftext|> 등
            r"</s>",
            r"<s>",
            r"\[PAD\]",
            r"\[SEP\]",
        ]
        for token in special_tokens:
            text = re.sub(token, "", text)

        # 5. 연속 공백 정리
        text = re.sub(r"\s+", " ", text).strip()

        if text != original:
            logger.debug(
                "single_bubble_cleaned",
                original_len=len(original),
                cleaned_len=len(text),
            )

        return text

    def _truncate_to_first_sentences(self, text: str, max_chars: int = 180) -> str:
        """텍스트를 첫 몇 문장으로 자르기 (max_chars 이내)"""
        import re

        sentences = re.split(r"(?<=[.!?~요오소다려])\s*", text)
        result = ""

        for sentence in sentences:
            if not sentence.strip():
                continue
            if len(result) + len(sentence) + 1 <= max_chars:
                result = result + " " + sentence if result else sentence
            else:
                break

        return result.strip() or text[:max_chars]

    def _get_single_bubble_fallback(self, char_code: str, mode: str) -> str:
        """단일 버블 폴백 응답"""
        fallbacks = {
            "SOISEOL": {
                "battle": "흥미로운 관점이오. 허나 나의 해석은 다르다오.",
                "consensus": "오호, 같은 결론에 이르렀구려!",
                "intro": "귀하의 사주를 살펴보겠소.",
            },
            "STELLA": {
                "battle": "음, 저는 좀 다르게 봐요!",
                "consensus": "맞아요! 저도 같은 걸 봤어요!",
                "intro": "당신의 별자리를 읽어볼게요!",
            },
            "CHEONGWOON": {
                "battle": "허허, 재미있는 견해로다.",
                "consensus": "뜻밖에 의견이 맞는구려.",
                "intro": "자네의 운을 살펴보겠네.",
            },
            "HWARIN": {
                "battle": "그건 좀 아닌 것 같은데요?",
                "consensus": "오, 생각이 같네요!",
                "intro": "당신의 사주를 볼게요.",
            },
            "KYLE": {
                "battle": "에이, 그건 아니지~",
                "consensus": "오, 맞아맞아!",
                "intro": "자, 운세 한번 볼까?",
            },
            "ELARIA": {
                "battle": "다른 관점도 있어요.",
                "consensus": "놀라워요, 같은 별을 봤네요!",
                "intro": "별의 인도를 받아볼게요.",
            },
        }

        char_fallbacks = fallbacks.get(char_code, fallbacks["SOISEOL"])
        return char_fallbacks.get(mode, char_fallbacks["intro"])
