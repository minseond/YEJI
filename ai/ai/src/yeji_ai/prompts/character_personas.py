"""캐릭터 페르소나 프롬프트 인덱스

티키타카 포춘 챗용 캐릭터 페르소나 모음
Qwen3 최적화 프롬프트

6명의 캐릭터:
- 스텔라 (STELLA): 서양 점성술사 - 해요체
- 소이설 (SOISEOL): 동양 사주학자 - 하오체/하게체
- 청운 (CHEONGWOON): 제자의 스승/신선 - 하오체 (시적)
- 화린 (HWARIN): 청룡상단 지부장 - 해요체 (나른+뼈있는)
- 카일 (KYLE): 도박사/정보상 - 반말+존댓말 혼용
- 엘라리아 (ELARIA): 사파이어 왕국 공주 - 하십시오체/해요체

Usage:
    from yeji_ai.prompts.character_personas import (
        SOISEOL, STELLA, CHEONGWOON, HWARIN, KYLE, ELARIA
    )

    # 시스템 프롬프트
    system_prompt = SOISEOL.SYSTEM_PROMPT

    # 프롬프트 빌더
    system, user = SOISEOL.build_prompt(topic, context)
"""

# ============================================================
# 캐릭터별 모듈 import
# ============================================================

from yeji_ai.prompts import cheongwoon_persona as CHEONGWOON
from yeji_ai.prompts import elaria_persona as ELARIA
from yeji_ai.prompts import hwarin_persona as HWARIN
from yeji_ai.prompts import kyle_persona as KYLE
from yeji_ai.prompts import soiseol_persona as SOISEOL
from yeji_ai.prompts import stella_persona as STELLA

# ============================================================
# 캐릭터 목록
# ============================================================

ALL_CHARACTERS = {
    "SOISEOL": SOISEOL,
    "STELLA": STELLA,
    "CHEONGWOON": CHEONGWOON,
    "HWARIN": HWARIN,
    "KYLE": KYLE,
    "ELARIA": ELARIA,
}

# 메인 캐릭터 (티키타카 대화에 사용)
MAIN_CHARACTERS = {
    "eastern": SOISEOL,   # 동양 운세
    "western": STELLA,    # 서양 운세
}

# 서브 캐릭터
SUB_CHARACTERS = {
    "CHEONGWOON": CHEONGWOON,  # 제자의 스승
    "HWARIN": HWARIN,          # 후배 언니
    "KYLE": KYLE,              # 도박사
    "ELARIA": ELARIA,          # 공주
}


# ============================================================
# 편의 함수
# ============================================================

def get_character(code: str):
    """캐릭터 코드로 모듈 가져오기

    Args:
        code: 캐릭터 코드 (SOISEOL, STELLA, etc.)

    Returns:
        캐릭터 모듈

    Raises:
        KeyError: 존재하지 않는 캐릭터 코드
    """
    return ALL_CHARACTERS[code.upper()]


def get_system_prompt(code: str) -> str:
    """캐릭터 시스템 프롬프트 가져오기

    Args:
        code: 캐릭터 코드

    Returns:
        시스템 프롬프트 문자열
    """
    return get_character(code).SYSTEM_PROMPT


def get_greeting(code: str) -> str:
    """캐릭터 인사말 가져오기

    Args:
        code: 캐릭터 코드

    Returns:
        인사말 문자열
    """
    return get_character(code).GREETING


def get_fallback_response(code: str) -> str:
    """캐릭터 폴백 응답 가져오기 (랜덤)

    Args:
        code: 캐릭터 코드

    Returns:
        폴백 응답 문자열
    """
    import random
    return random.choice(get_character(code).FALLBACK_RESPONSES)


def build_prompt(
    code: str,
    topic: str,
    context: str,
    user_message: str | None = None,
    **kwargs,
) -> tuple[str, str]:
    """캐릭터 프롬프트 빌드

    Args:
        code: 캐릭터 코드
        topic: 대화 주제
        context: 컨텍스트
        user_message: 사용자 메시지 (선택)
        **kwargs: 캐릭터별 추가 파라미터

    Returns:
        (system_prompt, user_prompt) 튜플
    """
    character = get_character(code)
    return character.build_prompt(topic, context, user_message, **kwargs)


# ============================================================
# 캐릭터 대비표 (참조용)
# ============================================================

CHARACTER_COMPARISON = {
    "SOISEOL": {
        "name": "소이설",
        "specialty": "동양 사주",
        "speech": "하오체/하게체",
        "tone": "침착, 진지",
    },
    "STELLA": {
        "name": "스텔라",
        "specialty": "서양 점성술",
        "speech": "해요체",
        "tone": "온화, 허당",
    },
    "CHEONGWOON": {
        "name": "청운",
        "specialty": "신선/현자",
        "speech": "하오체 (시적)",
        "tone": "초연, 능청",
    },
    "HWARIN": {
        "name": "화린",
        "specialty": "비즈니스/정보상",
        "speech": "해요체 (나른)",
        "tone": "매혹적, 계산적",
    },
    "KYLE": {
        "name": "카일",
        "specialty": "도박사/정보상",
        "speech": "반말+존댓말",
        "tone": "건들, 포커페이스",
    },
    "ELARIA": {
        "name": "엘라리아",
        "specialty": "공주/외교관",
        "speech": "하십시오체/해요체",
        "tone": "기품, 따뜻함",
    },
}


# ============================================================
# Qwen3 공통 설정
# ============================================================

QWEN3_CONFIG = {
    "temperature": 0.7,
    "top_p": 0.8,
    "top_k": 20,
    "max_tokens": 512,
    "presence_penalty": 1.5,
}

QWEN3_CHAT_TEMPLATE_KWARGS = {
    "enable_thinking": False,
}
