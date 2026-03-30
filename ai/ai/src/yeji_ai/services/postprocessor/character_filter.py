"""캐릭터 이름 필터

소이설 ↔ 스텔라 캐릭터 혼동 방지
"""

import structlog

logger = structlog.get_logger()


class CharacterNameFilter:
    """캐릭터 이름 일관성 필터"""

    CHARACTER_RULES = {
        "SOISEOL": {
            "allowed": ["소이설", "蘇利雪"],
            "forbidden": ["스텔라", "Stella", "별자리", "행성"],
            "replacement": "소이설",
        },
        "STELLA": {
            "allowed": ["스텔라", "Stella"],
            "forbidden": ["소이설", "蘇利雪", "사주", "오행", "음양"],
            "replacement": "스텔라",
        },
    }

    def filter(self, text: str, character: str) -> tuple[str, bool]:
        """캐릭터에 맞지 않는 이름 교체

        Args:
            text: 필터링할 텍스트
            character: 캐릭터 이름 ("SOISEOL" 또는 "STELLA")

        Returns:
            tuple[str, bool]: (필터링된 텍스트, 변경 발생 여부)
        """
        if not text or character not in self.CHARACTER_RULES:
            return text, False

        rules = self.CHARACTER_RULES[character]
        filtered_text = text
        changed = False

        for forbidden in rules.get("forbidden", []):
            if forbidden in filtered_text:
                filtered_text = filtered_text.replace(forbidden, rules["replacement"])
                changed = True

        if changed:
            logger.debug(
                "character_filter_applied",
                character=character,
                original_length=len(text),
                filtered_length=len(filtered_text),
            )

        return filtered_text, changed


# 싱글톤 인스턴스
_character_filter = CharacterNameFilter()


def filter_character_name(text: str, character: str) -> str:
    """캐릭터 이름 필터링 (편의 함수)"""
    filtered, _ = _character_filter.filter(text, character)
    return filtered
