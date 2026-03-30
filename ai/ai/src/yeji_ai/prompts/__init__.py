"""프롬프트 모듈"""

from yeji_ai.prompts.fortune_prompts import (
    EASTERN_SCHEMA_INSTRUCTION,
    EASTERN_SYSTEM_PROMPT,
    WESTERN_SCHEMA_INSTRUCTION,
    WESTERN_SYSTEM_PROMPT,
    build_eastern_generation_prompt,
    build_western_generation_prompt,
)

__all__ = [
    "EASTERN_SYSTEM_PROMPT",
    "WESTERN_SYSTEM_PROMPT",
    "EASTERN_SCHEMA_INSTRUCTION",
    "WESTERN_SCHEMA_INSTRUCTION",
    "build_eastern_generation_prompt",
    "build_western_generation_prompt",
]
