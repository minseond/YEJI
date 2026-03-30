"""폴백 더미 데이터 패키지

LLM 완전 실패 시 사용되는 규칙 기반 템플릿 데이터를 관리합니다.

- eastern_templates.json: 동양 사주 템플릿 (일간 × 오행 × 음양)
- western_templates.json: 서양 점성술 템플릿 (별자리 × 원소)
- keywords.json: 공통 키워드 데이터

사용 예시:
    from yeji_ai.data.fallback import (
        get_eastern_fallback_data,
        get_western_fallback_data,
        load_all_templates,
    )

    # 동양 사주 폴백 데이터 조회
    data = get_eastern_fallback_data("GAP", "WOOD", "YANG")

    # 서양 점성술 폴백 데이터 조회
    data = get_western_fallback_data("ARIES", "CANCER", "FIRE")
"""

from yeji_ai.data.fallback.loader import (
    get_eastern_fallback_data,
    get_fallback_stats,
    get_western_fallback_data,
    load_all_templates,
    load_eastern_templates,
    load_keywords,
    load_western_templates,
)

__all__ = [
    "get_eastern_fallback_data",
    "get_western_fallback_data",
    "load_eastern_templates",
    "load_western_templates",
    "load_keywords",
    "load_all_templates",
    "get_fallback_stats",
]
