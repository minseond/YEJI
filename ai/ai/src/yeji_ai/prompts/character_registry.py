"""캐릭터 이름 레지스트리

페르소나 간 상대 이름 매핑에 사용합니다.
"""

from typing import Final

CHARACTER_NAMES: Final[dict[str, str]] = {
    "SOISEOL": "소이설",
    "STELLA": "스텔라",
    "CHEONGWOON": "청운",
    "HWARIN": "화린",
    "KYLE": "카일",
    "ELARIA": "엘라리아",
}


def get_character_name(code: str | None) -> str:
    """캐릭터 코드 → 표시 이름 변환"""
    if not code:
        return "상대"
    return CHARACTER_NAMES.get(code.upper(), code)
