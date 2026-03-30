"""LLM 응답 후처리 모듈

LLM이 생성한 불완전한 JSON을 Pydantic 검증 전에 정규화합니다.

사용 예시:
    from yeji_ai.services.postprocessor import (
        WesternPostprocessor,
        EasternPostprocessor,
        filter_noise,
        fix_brackets,
    )

    # 서양 점성술 후처리
    western_pp = WesternPostprocessor()
    normalized = western_pp.process(raw_llm_response)

    # 동양 사주 후처리
    eastern_pp = EasternPostprocessor()
    normalized = eastern_pp.process(raw_llm_response)

    # 노이즈 필터링 (외래 문자 및 반복 패턴 제거)
    cleaned_text = filter_noise(llm_response_text, aggressive=False)

    # 빈 괄호 및 한자 누락 수정
    fixed_text = fix_brackets("갑() 을()")  # "갑(甲) 을(乙)"
"""

from yeji_ai.services.postprocessor.base import (
    KeywordExtractor,
    PipelineStep,
    PostprocessError,
    PostprocessErrorType,
    PostprocessResult,
    ResponsePostprocessor,
)
from yeji_ai.services.postprocessor.bracket_fixer import (
    CHEONGAN_MAPPING,
    JIJI_MAPPING,
    BracketFixer,
    fix_brackets,
    fix_brackets_in_dict,
    get_hanja_for_hangul,
)
from yeji_ai.services.postprocessor.character_filter import (
    CharacterNameFilter,
    filter_character_name,
)
from yeji_ai.services.postprocessor.eastern import EasternPostprocessor
from yeji_ai.services.postprocessor.extractors import (
    KEYWORD_MAPPING,
    DefaultKeywordExtractor,
)
from yeji_ai.services.postprocessor.tarot import TarotPostprocessor
from yeji_ai.services.postprocessor.noise_filter import (
    KNOWN_MIXED_SCRIPT_ERRORS,
    filter_noise,
    fix_mixed_script_tokens,
    remove_foreign_characters,
    remove_repetition,
    truncate_at_noise,
)
from yeji_ai.services.postprocessor.prompt_leak_filter import (
    PromptLeakFilter,
    detect_prompt_leak,
    filter_prompt_leak,
)
from yeji_ai.services.postprocessor.western import WesternPostprocessor

__all__ = [
    # Protocol / 인터페이스
    "ResponsePostprocessor",
    "PipelineStep",
    "KeywordExtractor",
    # 결과 및 에러
    "PostprocessResult",
    "PostprocessError",
    "PostprocessErrorType",
    # 후처리기 구현체
    "WesternPostprocessor",
    "EasternPostprocessor",
    "TarotPostprocessor",
    # 추출기
    "DefaultKeywordExtractor",
    "KEYWORD_MAPPING",
    # 노이즈 필터
    "filter_noise",
    "fix_mixed_script_tokens",
    "remove_foreign_characters",
    "remove_repetition",
    "truncate_at_noise",
    "KNOWN_MIXED_SCRIPT_ERRORS",
    # 빈 괄호 / 한자 수정
    "BracketFixer",
    "fix_brackets",
    "fix_brackets_in_dict",
    "get_hanja_for_hangul",
    "CHEONGAN_MAPPING",
    "JIJI_MAPPING",
    # 프롬프트 누출 필터
    "PromptLeakFilter",
    "filter_prompt_leak",
    "detect_prompt_leak",
    # 캐릭터 이름 필터
    "CharacterNameFilter",
    "filter_character_name",
]
