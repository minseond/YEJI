"""카테고리별 그리팅 프롬프트

사용자가 특정 카테고리(애정운, 재물운 등)를 선택했을 때
소이설(동양)과 스텔라(서양)가 해당 카테고리에 맞는 인사를 합니다.
"""

from yeji_ai.models.fortune.chat import FortuneCategory

# ============================================================
# 소이설 (동양 사주) 카테고리별 그리팅
# ============================================================

SOISEOL_GREETINGS = {
    FortuneCategory.GENERAL: {
        "greeting": (
            "귀하의 사주팔자를 종합적으로 살펴보겠소. "
            "천간과 지지의 조화가 어떠한지 깊이 들여다보리다."
        ),
        "description": (
            "일간을 중심으로 오행의 균형과 십신의 흐름을 분석하여 "
            "귀하의 전반적인 운세를 풀이할 것이오."
        ),
    },
    FortuneCategory.LOVE: {
        "greeting": (
            "애정운을 보러 오셨구려. "
            "인연이란 천지의 이치와 맞닿아 있는 법이오."
        ),
        "description": (
            "귀하의 사주에서 정재·편재·정관·편관의 배치를 살펴 "
            "인연의 흐름을 읽어보리다."
        ),
    },
    FortuneCategory.MONEY: {
        "greeting": (
            "재물운을 궁금해하시는구려. "
            "재물이란 토(土)와 금(金)의 조화로 흐르는 법이오."
        ),
        "description": (
            "정재와 편재의 위치, 그리고 식신·상관의 생재(生財) 여부를 보아 "
            "재물의 흐름을 짚어보겠소."
        ),
    },
    FortuneCategory.CAREER: {
        "greeting": (
            "직장운을 알고자 하시는구려. "
            "관(官)의 기운이 귀하의 사회적 위치를 말해주리다."
        ),
        "description": (
            "정관과 편관, 그리고 식상의 제관(制官) 관계를 분석하여 "
            "직장에서의 운세를 풀이하겠소."
        ),
    },
    FortuneCategory.HEALTH: {
        "greeting": (
            "건강운을 보러 오셨구려. "
            "몸이란 오행의 조화가 깨지면 병이 드는 법이오."
        ),
        "description": (
            "오행의 과불급(過不及)과 형충파해(刑沖破害)를 살펴 "
            "건강의 주의점을 짚어보리다."
        ),
    },
    FortuneCategory.STUDY: {
        "greeting": "학업운을 보러 오셨구려. 인성(印星)의 기운이 학문의 길을 밝혀주리다.",
        "description": "정인과 편인의 배치, 그리고 식신의 명민함을 살펴 학업의 운세를 풀이하겠소.",
    },
}


# ============================================================
# 스텔라 (서양 점성술) 카테고리별 그리팅
# ============================================================

STELLA_GREETINGS = {
    FortuneCategory.GENERAL: {
        "greeting": "안녕하세요! 당신의 별자리 지도를 전체적으로 분석해드릴게요.",
        "description": "태양, 달, 상승 별자리와 주요 행성 배치를 종합적으로 읽어드릴게요.",
    },
    FortuneCategory.LOVE: {
        "greeting": (
            "애정운이 궁금하시군요! "
            "금성과 화성의 위치가 당신의 사랑을 말해줘요."
        ),
        "description": (
            "금성(사랑 받는 방식), 화성(사랑 주는 방식), "
            "7하우스(파트너십)를 중심으로 분석할게요."
        ),
    },
    FortuneCategory.MONEY: {
        "greeting": (
            "재물운을 보러 오셨네요. "
            "목성과 2하우스가 당신의 재물 흐름을 보여줘요."
        ),
        "description": (
            "2하우스(수입), 8하우스(투자/유산), "
            "목성(풍요)의 배치로 재물운을 읽어드릴게요."
        ),
    },
    FortuneCategory.CAREER: {
        "greeting": (
            "직장운이 궁금하시군요! "
            "10하우스와 토성이 당신의 커리어를 이끌어요."
        ),
        "description": (
            "MC(천정), 10하우스(커리어), 토성(책임과 성취)을 중심으로 "
            "직장운을 분석할게요."
        ),
    },
    FortuneCategory.HEALTH: {
        "greeting": "건강운을 보러 오셨네요. 6하우스와 달의 위치가 건강 상태를 말해줘요.",
        "description": "6하우스(건강/일상), 12하우스(휴식/치유), 달(신체 리듬)을 읽어드릴게요.",
    },
    FortuneCategory.STUDY: {
        "greeting": (
            "학업운이 궁금하시군요! "
            "수성과 9하우스가 당신의 학습 능력을 보여줘요."
        ),
        "description": (
            "9하우스(고등 교육), 수성(학습 스타일), "
            "3하우스(기초 학습)를 중심으로 분석할게요."
        ),
    },
}


def get_category_greeting(
    category: FortuneCategory,
    character: str = "SOISEOL",
) -> dict[str, str]:
    """카테고리별 그리팅 가져오기

    Args:
        category: 운세 카테고리 (FortuneCategory Enum)
        character: 캐릭터 코드 ("SOISEOL" 또는 "STELLA")

    Returns:
        {"greeting": "인사말", "description": "카테고리 설명"}
    """
    if character == "SOISEOL":
        return SOISEOL_GREETINGS.get(
            category,
            SOISEOL_GREETINGS[FortuneCategory.GENERAL],
        )
    else:  # STELLA
        return STELLA_GREETINGS.get(
            category,
            STELLA_GREETINGS[FortuneCategory.GENERAL],
        )
