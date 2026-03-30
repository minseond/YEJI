"""Quick Summary API - 운세 빠른 요약

## 사용 흐름

```
1. 운세 분석 (선행 필수)
   POST /api/v1/fortune/eastern  → fortune_key 획득
   POST /api/v1/fortune/western  → fortune_key 획득

2. 빠른 요약 조회
   POST /api/v1/fortune/quick-summary
   {
     "fortune_id": "eastern:1990-05-15:14:30:M",
     "fortune_type": "eastern",
     "category": "MONEY",
     "persona": "SOISEOL"  // 선택: 캐릭터 말투 적용
   }

3. 응답
   - score: 점수 (동양: "木旺 水弱", 서양: "82점")
   - keyword: 한줄 요약
   - details: 항목별 분석 (음양/오행/십신 또는 원소/양태/별자리)
   - cache_source: 데이터 소스 (cache/generated/fallback)
```

## 캐싱 전략 (Progressive Caching)

1. Redis 캐시 조회 → 있으면 즉시 반환
2. 없으면 실시간 생성 → 검증 후 캐시 저장
3. 생성 실패 시 폴백 메시지 반환
"""

from __future__ import annotations

from typing import Literal

import structlog
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from yeji_ai.models.fortune.chat import CharacterCode, FortuneCategory
from yeji_ai.services.compound_message_service import (
    get_all_section_messages_parallel,
)
from yeji_ai.services.fortune_key_service import get_fortune as get_fortune_redis
from yeji_ai.services.progressive_cache_service import (
    get_quick_summary_cache,
    store_quick_summary_cache,
)
from yeji_ai.services.tikitaka_service import get_fortune as get_fortune_memory

logger = structlog.get_logger()
router = APIRouter()


# ============================================================
# Request/Response 모델
# ============================================================


class QuickSummaryRequest(BaseModel):
    """빠른 요약 요청"""

    fortune_id: str = Field(..., description="운세 분석 ID (eastern 또는 western)")
    fortune_type: Literal["eastern", "western"] = Field(..., description="운세 타입")
    category: FortuneCategory = Field(..., description="운세 카테고리")
    persona: CharacterCode | None = Field(
        None,
        description="페르소나 캐릭터 코드 (SOISEOL, STELLA, CHEONGWOON, HWARIN, KYLE, ELARIA). 없으면 중립적 말투",
    )


class SummaryDetail(BaseModel):
    """항목별 서머리"""

    section: str = Field(..., description="항목 코드 (yin_yang, five_elements, ten_gods 등)")
    title: str = Field(..., description="항목 제목")
    description: str = Field(..., description="카테고리별 해석")


class QuickSummaryResponse(BaseModel):
    """빠른 요약 응답"""

    fortune_id: str = Field(..., description="운세 분석 ID")
    fortune_type: Literal["eastern", "western"] = Field(..., description="운세 타입")
    category: str = Field(..., description="운세 카테고리")

    # 핵심 4가지
    score: str = Field(..., description="점수 (서양: 숫자, 동양: 한자)")
    keyword: str = Field(..., description="키워드 (해시태그)")
    one_liner: str = Field(..., description="한줄 요약 문장")
    details: list[SummaryDetail] = Field(..., description="항목별 서머리 목록")

    # 캐시 정보 (선택)
    cache_source: str | None = Field(None, description="데이터 소스 (cache/generated/fallback)")


# ============================================================
# 페르소나 말투 변환
# ============================================================


def _apply_persona_style(text: str, persona: CharacterCode | None) -> str:
    """페르소나에 맞는 말투로 변환

    Args:
        text: 원본 텍스트 (중립적 말투)
        persona: 캐릭터 코드

    Returns:
        페르소나 말투가 적용된 텍스트
    """
    if not persona:
        return text

    # 기본 문장 끝 패턴 변환
    if persona == CharacterCode.SOISEOL:
        # 소이설: 하오체
        text = text.replace("입니다.", "이오.")
        text = text.replace("합니다.", "하오.")
        text = text.replace("습니다.", "소.")
        text = text.replace("어요.", "오.")
        text = text.replace("에요.", "이오.")
        text = text.replace("해요.", "하오.")
        text = text.replace("네요.", "구려.")
        text = text.replace("세요.", "시오.")
        text = text.replace("아요.", "오.")
        text = text.replace("있어요.", "있소.")
        text = text.replace("없어요.", "없소.")
        text = text.replace("돼요.", "되오.")
        text = text.replace("봐요.", "보시오.")

    elif persona == CharacterCode.STELLA:
        # 스텔라: 해요체 (기본이 해요체에 가까우므로 미세 조정)
        text = text.replace("입니다.", "이에요.")
        text = text.replace("합니다.", "해요.")
        text = text.replace("습니다.", "어요.")

    elif persona == CharacterCode.CHEONGWOON:
        # 청운: 시적 하오체
        text = text.replace("입니다.", "이로다.")
        text = text.replace("합니다.", "하노라.")
        text = text.replace("습니다.", "도다.")
        text = text.replace("어요.", "노라.")
        text = text.replace("에요.", "이로다.")
        text = text.replace("해요.", "하노라.")
        text = text.replace("네요.", "로구나.")
        text = text.replace("세요.", "시게나.")
        text = text.replace("있어요.", "있노라.")
        text = text.replace("없어요.", "없노라.")

    elif persona == CharacterCode.HWARIN:
        # 화린: 나른한 해요체
        text = text.replace("입니다.", "이에요~")
        text = text.replace("합니다.", "해요~")
        text = text.replace("습니다.", "어요~")
        text = text.replace("어요.", "어요~")
        text = text.replace("에요.", "에요~")
        text = text.replace("해요.", "해요~")
        text = text.replace("네요.", "네요~")
        text = text.replace("세요.", "세요~")

    elif persona == CharacterCode.KYLE:
        # 카일: 반말+존댓말 혼용
        text = text.replace("입니다.", "이야.")
        text = text.replace("합니다.", "해.")
        text = text.replace("습니다.", "어.")
        text = text.replace("어요.", "어.")
        text = text.replace("에요.", "야.")
        text = text.replace("해요.", "해.")
        text = text.replace("네요.", "네.")
        text = text.replace("세요.", "셔.")
        text = text.replace("있어요.", "있어.")
        text = text.replace("없어요.", "없어.")

    elif persona == CharacterCode.ELARIA:
        # 엘라리아: 우아한 해요체
        text = text.replace("입니다.", "이랍니다.")
        text = text.replace("합니다.", "한답니다.")
        text = text.replace("습니다.", "어요.")
        text = text.replace("어요.", "답니다.")
        text = text.replace("에요.", "랍니다.")
        text = text.replace("해요.", "한답니다.")

    return text


# ============================================================
# 폴백 메시지 생성 함수
# ============================================================


def _generate_fallback_eastern_details(category: FortuneCategory) -> list[SummaryDetail]:
    """동양 사주 폴백 상세 생성 (운세 데이터가 없을 때)

    사주 조합 기반으로 다양한 폴백 메시지를 생성합니다.
    """
    details = []

    # 음양: 50:50 균형으로 가정
    details.append(
        SummaryDetail(
            section="yin_yang",
            title="음양 밸런스",
            description="아직 분석 전이에요. 음양의 균형을 정확히 파악하려면 생년월일로 분석해보세요!",
        )
    )

    # 오행 5개: 카테고리별 폴백 해석
    element_fallback_tips = {
        FortuneCategory.GENERAL: {
            "WOOD": "아직 분석 전이에요. 목(木)의 기운은 성장과 발전을 의미하는데, 새로운 도전에 좋은 에너지입니다. 생년월일로 정확히 분석해보세요!",
            "FIRE": "아직 분석 전이에요. 화(火)의 기운은 열정과 추진력을 의미하는데, 적극적으로 행동하면 좋은 결과가 기대됩니다. 생년월일로 정확히 분석해보세요!",
            "EARTH": "아직 분석 전이에요. 토(土)의 기운은 안정과 신뢰를 의미하는데, 꾸준함이 빛을 발할 때입니다. 생년월일로 정확히 분석해보세요!",
            "METAL": "아직 분석 전이에요. 금(金)의 기운은 결단력과 실행력을 의미하는데, 정리하고 마무리하는 것이 중요합니다. 생년월일로 정확히 분석해보세요!",
            "WATER": "아직 분석 전이에요. 수(水)의 기운은 지혜와 유연함을 의미하는데, 소통과 네트워킹이 강점입니다. 생년월일로 정확히 분석해보세요!",
        },
        FortuneCategory.MONEY: {
            "WOOD": "아직 분석 전이에요. 목(木)의 기운은 성장과 발전을 의미하는데, 장기적인 관점에서 투자하면 좋은 결과가 기대됩니다. 생년월일로 정확히 분석해보세요!",
            "FIRE": "아직 분석 전이에요. 화(火)의 기운은 적극적인 투자 성향을 의미하는데, 과감한 결정이 수익을 불러올 수 있습니다. 생년월일로 정확히 분석해보세요!",
            "EARTH": "아직 분석 전이에요. 토(土)의 기운은 안정적인 자산을 의미하는데, 부동산이나 실물 자산에 관심을 가져볼 만합니다. 생년월일로 정확히 분석해보세요!",
            "METAL": "아직 분석 전이에요. 금(金)의 기운은 효율적인 재테크를 의미하는데, 체계적으로 관리하면 좋은 결과가 따라옵니다. 생년월일로 정확히 분석해보세요!",
            "WATER": "아직 분석 전이에요. 수(水)의 기운은 정보의 흐름을 의미하는데, 트렌드를 파악해서 수익을 창출하는 것이 가능합니다. 생년월일로 정확히 분석해보세요!",
        },
        FortuneCategory.LOVE: {
            "WOOD": "아직 분석 전이에요. 목(木)의 기운은 관계의 성장을 의미하는데, 새로운 인연을 만나기에 좋은 시기입니다. 생년월일로 정확히 분석해보세요!",
            "FIRE": "아직 분석 전이에요. 화(火)의 기운은 열정적인 연애를 의미하는데, 뜨겁게 사랑하되 감정 조절도 필요합니다. 생년월일로 정확히 분석해보세요!",
            "EARTH": "아직 분석 전이에요. 토(土)의 기운은 안정적인 관계를 의미하는데, 진지하고 오래가는 사랑을 추구합니다. 생년월일로 정확히 분석해보세요!",
            "METAL": "아직 분석 전이에요. 금(金)의 기운은 명확한 기준을 의미하는데, 서로의 공간을 존중하는 연애가 맞습니다. 생년월일로 정확히 분석해보세요!",
            "WATER": "아직 분석 전이에요. 수(水)의 기운은 감성적 교감을 의미하는데, 깊이 있는 대화와 감정 공유가 사랑의 핵심입니다. 생년월일로 정확히 분석해보세요!",
        },
        FortuneCategory.CAREER: {
            "WOOD": "아직 분석 전이에요. 목(木)의 기운은 커리어 성장을 의미하는데, 새로운 도전이나 스킬업에 좋은 시기입니다. 생년월일로 정확히 분석해보세요!",
            "FIRE": "아직 분석 전이에요. 화(火)의 기운은 추진력을 의미하는데, 열정적으로 일하면 좋은 성과를 낼 수 있습니다. 생년월일로 정확히 분석해보세요!",
            "EARTH": "아직 분석 전이에요. 토(土)의 기운은 꾸준함을 의미하는데, 성실하게 일해서 신뢰를 얻는 시기입니다. 생년월일로 정확히 분석해보세요!",
            "METAL": "아직 분석 전이에요. 금(金)의 기운은 효율성을 의미하는데, 체계적으로 정리하고 마무리하는 것이 강점입니다. 생년월일로 정확히 분석해보세요!",
            "WATER": "아직 분석 전이에요. 수(水)의 기운은 네트워킹을 의미하는데, 인맥을 활용하면 좋은 기회가 찾아옵니다. 생년월일로 정확히 분석해보세요!",
        },
        FortuneCategory.HEALTH: {
            "WOOD": "아직 분석 전이에요. 목(木)의 기운은 간과 눈 건강을 의미하는데, 스트레칭이나 눈 휴식을 자주 취해주세요. 생년월일로 정확히 분석해보세요!",
            "FIRE": "아직 분석 전이에요. 화(火)의 기운은 심장과 혈액순환을 의미하는데, 과도한 음주나 자극적인 음식은 자제하는 것이 좋습니다. 생년월일로 정확히 분석해보세요!",
            "EARTH": "아직 분석 전이에요. 토(土)의 기운은 소화기 건강을 의미하는데, 규칙적인 식사와 과식 주의가 필요합니다. 생년월일로 정확히 분석해보세요!",
            "METAL": "아직 분석 전이에요. 금(金)의 기운은 호흡기와 피부를 의미하는데, 맑은 공기 마시기와 피부 보습을 챙겨주세요. 생년월일로 정확히 분석해보세요!",
            "WATER": "아직 분석 전이에요. 수(水)의 기운은 신장과 방광을 의미하는데, 충분한 수분 섭취를 잊지 마세요. 생년월일로 정확히 분석해보세요!",
        },
        FortuneCategory.STUDY: {
            "WOOD": "아직 분석 전이에요. 목(木)의 기운은 새로운 학습을 의미하는데, 새로운 분야에 도전하면 빠르게 성장할 수 있습니다. 생년월일로 정확히 분석해보세요!",
            "FIRE": "아직 분석 전이에요. 화(火)의 기운은 집중력을 의미하는데, 몰입해서 공부하면 단기 집중 학습이 효과적입니다. 생년월일로 정확히 분석해보세요!",
            "EARTH": "아직 분석 전이에요. 토(土)의 기운은 기본기를 의미하는데, 꾸준히 복습하면 실력이 단단해집니다. 생년월일로 정확히 분석해보세요!",
            "METAL": "아직 분석 전이에요. 금(金)의 기운은 효율적 학습을 의미하는데, 요약 정리를 잘하면 학습 효과가 배가됩니다. 생년월일로 정확히 분석해보세요!",
            "WATER": "아직 분석 전이에요. 수(水)의 기운은 깊이 있는 이해를 의미하는데, 개념을 제대로 파악하면 응용력이 좋아집니다. 생년월일로 정확히 분석해보세요!",
        },
    }

    element_tips = element_fallback_tips.get(
        category, element_fallback_tips[FortuneCategory.GENERAL]
    )
    element_korean = {
        "WOOD": "목(木)",
        "FIRE": "화(火)",
        "EARTH": "토(土)",
        "METAL": "금(金)",
        "WATER": "수(水)",
    }

    # 오행 5개 전부 추가
    for elem_code in ["WOOD", "FIRE", "EARTH", "METAL", "WATER"]:
        elem_name = element_korean[elem_code]
        elem_tip = element_tips[elem_code]

        details.append(
            SummaryDetail(
                section="five_elements",
                title=elem_name,
                description=elem_tip,
            )
        )

    # 십신: 대표적인 3개 포함 (비견, 식신, 정재)
    ten_god_fallback_tips = {
        FortuneCategory.GENERAL: {
            "BIJEON": "아직 분석 전이에요. 비견은 자기주장과 독립심을 의미하는데, 자신만의 길을 개척하는 성향입니다. 생년월일로 정확히 분석해보세요!",
            "SIKSHIN": "아직 분석 전이에요. 식신은 표현력과 여유를 의미하는데, 창의적인 아이디어가 넘치고 즐길 줄 압니다. 생년월일로 정확히 분석해보세요!",
            "JEONGJAE": "아직 분석 전이에요. 정재는 꾸준한 재물 관리를 의미하는데, 착실하게 모으고 성실하게 관리하는 스타일입니다. 생년월일로 정확히 분석해보세요!",
        },
        FortuneCategory.MONEY: {
            "BIJEON": "아직 분석 전이에요. 비견은 내 돈은 내가 쓴다는 마인드를 의미하는데, 씀씀이가 큰 편일 수 있습니다. 생년월일로 정확히 분석해보세요!",
            "SIKSHIN": "아직 분석 전이에요. 식신은 삶의 질 투자를 의미하는데, 맛있는 것, 좋은 것에 돈을 쓰는 걸 좋아합니다. 생년월일로 정확히 분석해보세요!",
            "JEONGJAE": "아직 분석 전이에요. 정재는 월급 저축을 의미하는데, 착실하게 모아서 부자가 되는 타입입니다. 생년월일로 정확히 분석해보세요!",
        },
        FortuneCategory.LOVE: {
            "BIJEON": "아직 분석 전이에요. 비견은 자존감 있는 연애를 의미하는데, 나를 존중해주는 사람을 원합니다. 생년월일로 정확히 분석해보세요!",
            "SIKSHIN": "아직 분석 전이에요. 식신은 즐거운 연애를 의미하는데, 맛집 데이트, 여행 등 함께 먹고 놀면서 사랑을 키웁니다. 생년월일로 정확히 분석해보세요!",
            "JEONGJAE": "아직 분석 전이에요. 정재는 진심 어린 연애를 의미하는데, 진정성 있는 관계를 원하고 한 번 만나면 오래갑니다. 생년월일로 정확히 분석해보세요!",
        },
        FortuneCategory.CAREER: {
            "BIJEON": "아직 분석 전이에요. 비견은 독립적인 일을 의미하는데, 혼자서 일하는 것을 선호하고 개인 플레이에서 빛납니다. 생년월일로 정확히 분석해보세요!",
            "SIKSHIN": "아직 분석 전이에요. 식신은 창의적인 업무를 의미하는데, 아이디어가 필요한 곳에서 인정받습니다. 생년월일로 정확히 분석해보세요!",
            "JEONGJAE": "아직 분석 전이에요. 정재는 안정적인 직장을 의미하는데, 한 회사에서 오래 일하면서 신뢰를 쌓습니다. 생년월일로 정확히 분석해보세요!",
        },
        FortuneCategory.HEALTH: {
            "BIJEON": "아직 분석 전이에요. 비견은 자기 관리를 의미하는데, 고집 때문에 몸 상태를 무시하지 말고 꾸준히 챙기세요. 생년월일로 정확히 분석해보세요!",
            "SIKSHIN": "아직 분석 전이에요. 식신은 소화기 건강을 의미하는데, 먹는 것을 좋아해서 과식 조심이 필요합니다. 생년월일로 정확히 분석해보세요!",
            "JEONGJAE": "아직 분석 전이에요. 정재는 규칙적인 생활을 의미하는데, 정해진 시간에 먹고 자면 건강해집니다. 생년월일로 정확히 분석해보세요!",
        },
        FortuneCategory.STUDY: {
            "BIJEON": "아직 분석 전이에요. 비견은 혼자 공부를 의미하는데, 자기주도 학습으로 진행하면 효율이 높습니다. 생년월일로 정확히 분석해보세요!",
            "SIKSHIN": "아직 분석 전이에요. 식신은 실습 학습을 의미하는데, 직접 해보면서 배우면 빠르게 습득합니다. 생년월일로 정확히 분석해보세요!",
            "JEONGJAE": "아직 분석 전이에요. 정재는 체계적 학습을 의미하는데, 커리큘럼대로 따라가면 성과가 납니다. 생년월일로 정확히 분석해보세요!",
        },
    }

    ten_god_tips = ten_god_fallback_tips.get(
        category, ten_god_fallback_tips[FortuneCategory.GENERAL]
    )
    ten_god_korean = {"BIJEON": "비견", "SIKSHIN": "식신", "JEONGJAE": "정재"}

    # 십신 3개 추가
    for god_code in ["BIJEON", "SIKSHIN", "JEONGJAE"]:
        god_name = ten_god_korean[god_code]
        god_tip = ten_god_tips[god_code]

        details.append(
            SummaryDetail(
                section="ten_gods",
                title=god_name,
                description=god_tip,
            )
        )

    return details


def _generate_fallback_western_details(category: FortuneCategory) -> list[SummaryDetail]:
    """서양 점성술 폴백 상세 생성 (운세 데이터가 없을 때)

    점성 조합 기반으로 다양한 폴백 메시지를 생성합니다.
    """
    details = []

    # 4원소: 카테고리별 폴백 해석
    element_fallback_tips = {
        FortuneCategory.GENERAL: {
            "fire": "아직 분석 전이에요. 불(Fire)의 기운은 열정과 추진력을 의미하는데, 적극적으로 행동하면 좋은 결과를 얻을 수 있습니다. 생년월일로 정확히 분석해보세요!",
            "water": "아직 분석 전이에요. 물(Water)의 기운은 감성과 직관을 의미하는데, 느낌을 믿고 따라가면 좋은 방향으로 흘러갑니다. 생년월일로 정확히 분석해보세요!",
            "air": "아직 분석 전이에요. 공기(Air)의 기운은 소통과 아이디어를 의미하는데, 생각을 말로 표현하면 인정받습니다. 생년월일로 정확히 분석해보세요!",
            "earth": "아직 분석 전이에요. 흙(Earth)의 기운은 현실성과 안정을 의미하는데, 꾸준하고 성실하게 하면 결과가 따라옵니다. 생년월일로 정확히 분석해보세요!",
        },
        FortuneCategory.MONEY: {
            "fire": "아직 분석 전이에요. 불(Fire)의 기운은 적극적인 투자를 의미하는데, 과감하게 움직이면 수익을 낼 수 있지만 너무 급하면 손실 위험도 있습니다. 생년월일로 정확히 분석해보세요!",
            "water": "아직 분석 전이에요. 물(Water)의 기운은 돈의 흐름을 의미하는데, 직감을 믿고 투자하면 좋은 결과를 얻을 수 있습니다. 생년월일로 정확히 분석해보세요!",
            "air": "아직 분석 전이에요. 공기(Air)의 기운은 정보 활용을 의미하는데, 트렌드를 빠르게 파악해서 수익 기회를 잡습니다. 생년월일로 정확히 분석해보세요!",
            "earth": "아직 분석 전이에요. 흙(Earth)의 기운은 안정적인 자산을 의미하는데, 부동산이나 실물 자산에 관심을 가져볼 만합니다. 생년월일로 정확히 분석해보세요!",
        },
        FortuneCategory.LOVE: {
            "fire": "아직 분석 전이에요. 불(Fire)의 기운은 열정적인 사랑을 의미하는데, 뜨겁게 타오르는 연애를 하지만 감정 조절도 필요합니다. 생년월일로 정확히 분석해보세요!",
            "water": "아직 분석 전이에요. 물(Water)의 기운은 깊은 감정을 의미하는데, 영혼까지 교감하는 진정한 사랑을 원합니다. 생년월일로 정확히 분석해보세요!",
            "air": "아직 분석 전이에요. 공기(Air)의 기운은 대화와 소통을 의미하는데, 말이 잘 통하는 사람과 잘 맞습니다. 생년월일로 정확히 분석해보세요!",
            "earth": "아직 분석 전이에요. 흙(Earth)의 기운은 안정적인 관계를 의미하는데, 믿음직하고 오래가는 사랑을 원합니다. 생년월일로 정확히 분석해보세요!",
        },
        FortuneCategory.CAREER: {
            "fire": "아직 분석 전이에요. 불(Fire)의 기운은 추진력을 의미하는데, 열정적으로 일하면 좋은 성과를 낼 수 있습니다. 생년월일로 정확히 분석해보세요!",
            "water": "아직 분석 전이에요. 물(Water)의 기운은 창의적인 분야를 의미하는데, 예술이나 상담처럼 감성을 활용하는 일이 잘 맞습니다. 생년월일로 정확히 분석해보세요!",
            "air": "아직 분석 전이에요. 공기(Air)의 기운은 기획과 마케팅을 의미하는데, 아이디어로 승부하면 인정받습니다. 생년월일로 정확히 분석해보세요!",
            "earth": "아직 분석 전이에요. 흙(Earth)의 기운은 체계적인 성과를 의미하는데, 안정적인 환경에서 실력을 발휘합니다. 생년월일로 정확히 분석해보세요!",
        },
        FortuneCategory.HEALTH: {
            "fire": "아직 분석 전이에요. 불(Fire)의 기운은 에너지 넘침을 의미하는데, 과로에 주의하고 적절한 휴식으로 밸런스를 맞추세요. 생년월일로 정확히 분석해보세요!",
            "water": "아직 분석 전이에요. 물(Water)의 기운은 정서적 안정을 의미하는데, 스트레스 관리를 잘 해야 몸도 건강해집니다. 생년월일로 정확히 분석해보세요!",
            "air": "아직 분석 전이에요. 공기(Air)의 기운은 호흡기 건강을 의미하는데, 맑은 공기 마시고 심호흡을 자주 하세요. 생년월일로 정확히 분석해보세요!",
            "earth": "아직 분석 전이에요. 흙(Earth)의 기운은 소화기 건강을 의미하는데, 규칙적인 식사와 과식 주의가 필요합니다. 생년월일로 정확히 분석해보세요!",
        },
        FortuneCategory.STUDY: {
            "fire": "아직 분석 전이에요. 불(Fire)의 기운은 집중 학습을 의미하는데, 단기간 몰입 학습이 잘 맞습니다. 생년월일로 정확히 분석해보세요!",
            "water": "아직 분석 전이에요. 물(Water)의 기운은 감성적 이해를 의미하는데, 스토리로 배우면 기억에 오래 남습니다. 생년월일로 정확히 분석해보세요!",
            "air": "아직 분석 전이에요. 공기(Air)의 기운은 논리적 사고를 의미하는데, 수학이나 과학 같은 분야에 강합니다. 생년월일로 정확히 분석해보세요!",
            "earth": "아직 분석 전이에요. 흙(Earth)의 기운은 체계적 학습을 의미하는데, 차근차근 기본부터 쌓아가세요. 생년월일로 정확히 분석해보세요!",
        },
    }

    element_tips = element_fallback_tips.get(
        category, element_fallback_tips[FortuneCategory.GENERAL]
    )
    element_korean = {
        "fire": "불(Fire)",
        "water": "물(Water)",
        "air": "공기(Air)",
        "earth": "흙(Earth)",
    }

    # 4원소 전부 추가
    for elem_code in ["fire", "water", "air", "earth"]:
        elem_name = element_korean[elem_code]
        elem_tip = element_tips[elem_code]

        details.append(
            SummaryDetail(
                section="elements",
                title=elem_name,
                description=elem_tip,
            )
        )

    # 양태 3개: 카테고리별 폴백 해석
    modality_fallback_tips = {
        FortuneCategory.GENERAL: {
            "cardinal": "아직 분석 전이에요. 활동궁(Cardinal)의 기운은 새로운 시작을 의미하는데, 앞장서서 이끌고 개척하는 것을 좋아합니다. 생년월일로 정확히 분석해보세요!",
            "fixed": "아직 분석 전이에요. 고정궁(Fixed)의 기운은 지구력을 의미하는데, 한 번 시작한 것을 끝까지 해내는 꾸준함이 최고의 강점입니다. 생년월일로 정확히 분석해보세요!",
            "mutable": "아직 분석 전이에요. 변통궁(Mutable)의 기운은 유연함을 의미하는데, 상황에 맞게 적응하고 변화에 빠르게 대응하는 능력이 뛰어납니다. 생년월일로 정확히 분석해보세요!",
        },
        FortuneCategory.MONEY: {
            "cardinal": "아직 분석 전이에요. 활동궁의 기운은 투자 개척을 의미하는데, 새로운 기회를 남들보다 먼저 선점하는 것이 강점입니다. 생년월일로 정확히 분석해보세요!",
            "fixed": "아직 분석 전이에요. 고정궁의 기운은 장기 투자를 의미하는데, 한 번 투자하면 끝까지 홀딩하면서 기다릴 수 있습니다. 생년월일로 정확히 분석해보세요!",
            "mutable": "아직 분석 전이에요. 변통궁의 기운은 민첩한 대응을 의미하는데, 시장 변화에 따라 유연하게 전략을 바꿀 수 있습니다. 생년월일로 정확히 분석해보세요!",
        },
        FortuneCategory.LOVE: {
            "cardinal": "아직 분석 전이에요. 활동궁의 기운은 적극적인 연애를 의미하는데, 먼저 다가가고 고백하는 것을 두려워하지 않습니다. 생년월일로 정확히 분석해보세요!",
            "fixed": "아직 분석 전이에요. 고정궁의 기운은 끝까지 사랑을 의미하는데, 한 사람을 안정적이고 오래 사랑합니다. 생년월일로 정확히 분석해보세요!",
            "mutable": "아직 분석 전이에요. 변통궁의 기운은 다양한 만남을 의미하는데, 상대에 맞춰 유연하게 관계를 형성할 수 있습니다. 생년월일로 정확히 분석해보세요!",
        },
        FortuneCategory.CAREER: {
            "cardinal": "아직 분석 전이에요. 활동궁의 기운은 주도적인 일을 의미하는데, 새로운 프로젝트를 시작하거나 팀을 이끄는 것이 잘 맞습니다. 생년월일로 정확히 분석해보세요!",
            "fixed": "아직 분석 전이에요. 고정궁의 기운은 꾸준한 성과를 의미하는데, 맡은 일을 끝까지 책임지고 완수하는 것이 강점입니다. 생년월일로 정확히 분석해보세요!",
            "mutable": "아직 분석 전이에요. 변통궁의 기운은 적응력을 의미하는데, 변화하는 환경에서 다양한 업무를 유연하게 처리할 수 있습니다. 생년월일로 정확히 분석해보세요!",
        },
        FortuneCategory.HEALTH: {
            "cardinal": "아직 분석 전이에요. 활동궁의 기운은 활동적 관리를 의미하는데, 새로운 운동에 도전하면 꾸준히 할 수 있습니다. 생년월일로 정확히 분석해보세요!",
            "fixed": "아직 분석 전이에요. 고정궁의 기운은 규칙적인 생활을 의미하는데, 정해진 루틴을 지키면 건강해집니다. 생년월일로 정확히 분석해보세요!",
            "mutable": "아직 분석 전이에요. 변통궁의 기운은 유연한 관리를 의미하는데, 몸 상태에 따라 그때그때 필요한 것을 챙기세요. 생년월일로 정확히 분석해보세요!",
        },
        FortuneCategory.STUDY: {
            "cardinal": "아직 분석 전이에요. 활동궁의 기운은 선도적 학습을 의미하는데, 새로운 분야를 먼저 배우는 것이 강점입니다. 생년월일로 정확히 분석해보세요!",
            "fixed": "아직 분석 전이에요. 고정궁의 기운은 집중 학습을 의미하는데, 한 분야를 깊이 파고들면 전문가가 될 수 있습니다. 생년월일로 정확히 분석해보세요!",
            "mutable": "아직 분석 전이에요. 변통궁의 기운은 다양한 학습법을 의미하는데, 상황에 맞게 방법을 바꾸면 효과가 좋습니다. 생년월일로 정확히 분석해보세요!",
        },
    }

    modality_tips = modality_fallback_tips.get(
        category, modality_fallback_tips[FortuneCategory.GENERAL]
    )
    modality_korean = {
        "cardinal": "활동(Cardinal)",
        "fixed": "고정(Fixed)",
        "mutable": "변통(Mutable)",
    }

    # 양태 3개 추가
    for mod_code in ["cardinal", "fixed", "mutable"]:
        mod_name = modality_korean[mod_code]
        mod_tip = modality_tips[mod_code]

        details.append(
            SummaryDetail(
                section="modality",
                title=mod_name,
                description=mod_tip,
            )
        )

    # 태양 별자리: 분석 필요 상태
    details.append(
        SummaryDetail(
            section="sun_sign",
            title="태양 별자리",
            description="아직 분석 전이에요. 태양 별자리는 당신의 핵심 에너지를 나타내는데, 생년월일로 정확히 분석해보세요!",
        )
    )

    return details


# ============================================================
# 요약 생성 헬퍼 함수
# ============================================================


def _normalize_fortune_id(fortune_id: str) -> str:
    """fortune_id 형식 정규화

    BE에서 보내는 형식과 Redis 저장 형식이 다를 수 있음:
    - BE: eastern:1998-02-25:03:00:M (시간에 콜론 있음)
    - Redis: eastern:1998-02-25:0300:M (시간에 콜론 없음)

    이 함수는 시간 부분의 콜론을 제거하여 Redis 형식으로 정규화함.
    """
    import re

    # 패턴: type:YYYY-MM-DD:HH:MM:gender 또는 type:YYYY-MM-DD:HH:MM
    # 시간 부분 HH:MM을 HHMM으로 변환
    # 예: eastern:1998-02-25:03:00:M -> eastern:1998-02-25:0300:M
    # 예: western:1998-02-25:03:00 -> western:1998-02-25:0300

    # Eastern 패턴: type:YYYY-MM-DD:HH:MM:gender
    eastern_match = re.match(
        r"^(eastern:\d{4}-\d{2}-\d{2}):(\d{2}):(\d{2}):([MF])$",
        fortune_id,
    )
    if eastern_match:
        return f"{eastern_match.group(1)}:{eastern_match.group(2)}{eastern_match.group(3)}:{eastern_match.group(4)}"

    # Western 패턴 (gender 있는 경우 - 잘못된 형식이지만 처리): type:YYYY-MM-DD:HH:MM:gender
    western_gender_match = re.match(
        r"^(western:\d{4}-\d{2}-\d{2}):(\d{2}):(\d{2}):([MF])$",
        fortune_id,
    )
    if western_gender_match:
        # Western은 gender 없이 저장됨
        return f"{western_gender_match.group(1)}:{western_gender_match.group(2)}{western_gender_match.group(3)}"

    # Western 패턴 (gender 없는 경우): type:YYYY-MM-DD:HH:MM
    western_match = re.match(
        r"^(western:\d{4}-\d{2}-\d{2}):(\d{2}):(\d{2})$",
        fortune_id,
    )
    if western_match:
        return f"{western_match.group(1)}:{western_match.group(2)}{western_match.group(3)}"

    # 이미 정규화된 형식이면 그대로 반환
    return fortune_id


def _get_stats(fortune_data: dict) -> dict:
    """fortune_data에서 stats 추출 (래퍼 구조 대응)

    Redis 저장 구조가 두 가지일 수 있음:
    1. {stats: {...}} - 직접 저장
    2. {data: {stats: {...}}} - API 응답 래퍼로 저장

    Returns:
        stats 딕셔너리 또는 빈 딕셔너리
    """
    # 직접 stats가 있는 경우
    if "stats" in fortune_data:
        return fortune_data.get("stats", {})
    # data 안에 stats가 있는 경우
    data = fortune_data.get("data", {})
    return data.get("stats", {})


def _get_chart(fortune_data: dict) -> dict:
    """fortune_data에서 chart 추출 (래퍼 구조 대응)"""
    if "chart" in fortune_data:
        return fortune_data.get("chart", {})
    data = fortune_data.get("data", {})
    return data.get("chart", {})


# ============================================================
# 카테고리별 오행/원소 가중치 (사주/점성술 이론 기반)
# ============================================================

# 동양 오행-카테고리 가중치
# 각 카테고리에 유리한 오행에 높은 가중치 부여
EASTERN_CATEGORY_WEIGHTS: dict[str, dict[str, float]] = {
    "MONEY": {
        "METAL": 1.5,  # 금(金) - 재물, 결실
        "WATER": 1.3,  # 수(水) - 지혜, 재테크
        "EARTH": 1.2,  # 토(土) - 안정, 저축
        "WOOD": 0.9,   # 목(木) - 성장 (장기)
        "FIRE": 0.8,   # 화(火) - 소비 성향
    },
    "LOVE": {
        "FIRE": 1.5,   # 화(火) - 열정, 매력
        "WATER": 1.4,  # 수(水) - 감성, 교감
        "WOOD": 1.2,   # 목(木) - 새로운 만남
        "EARTH": 1.0,  # 토(土) - 안정적 관계
        "METAL": 0.7,  # 금(金) - 냉정함
    },
    "CAREER": {
        "WOOD": 1.5,   # 목(木) - 성장, 발전
        "FIRE": 1.4,   # 화(火) - 명예, 추진력
        "METAL": 1.2,  # 금(金) - 결단력, 성과
        "EARTH": 1.0,  # 토(土) - 안정
        "WATER": 0.8,  # 수(水) - 유연함
    },
    "HEALTH": {
        "EARTH": 1.5,  # 토(土) - 소화기, 균형
        "WATER": 1.3,  # 수(水) - 신장, 체액
        "WOOD": 1.2,   # 목(木) - 간, 근육
        "METAL": 1.0,  # 금(金) - 폐, 피부
        "FIRE": 0.9,   # 화(火) - 심장 (과하면 부담)
    },
    "STUDY": {
        "WATER": 1.5,  # 수(水) - 지혜, 학문
        "WOOD": 1.4,   # 목(木) - 성장, 창의
        "METAL": 1.2,  # 금(金) - 집중, 논리
        "FIRE": 0.9,   # 화(火) - 산만할 수 있음
        "EARTH": 0.8,  # 토(土) - 고집
    },
    "GENERAL": {
        "WOOD": 1.0,
        "FIRE": 1.0,
        "EARTH": 1.0,
        "METAL": 1.0,
        "WATER": 1.0,
    },
}

# 서양 4원소-카테고리 가중치
WESTERN_CATEGORY_WEIGHTS: dict[str, dict[str, float]] = {
    "MONEY": {
        "earth": 1.6,  # 땅 - 물질, 실용
        "water": 1.3,  # 물 - 직관, 투자 감각
        "fire": 0.9,   # 불 - 충동 소비
        "air": 0.8,    # 공기 - 변덕
    },
    "LOVE": {
        "water": 1.6,  # 물 - 감정, 로맨스
        "fire": 1.4,   # 불 - 열정
        "air": 1.1,    # 공기 - 소통
        "earth": 0.8,  # 땅 - 감정 표현 부족
    },
    "CAREER": {
        "fire": 1.5,   # 불 - 리더십, 야망
        "earth": 1.4,  # 땅 - 실무, 성과
        "air": 1.1,    # 공기 - 아이디어
        "water": 0.8,  # 물 - 감정적
    },
    "HEALTH": {
        "earth": 1.5,  # 땅 - 체력, 지구력
        "water": 1.3,  # 물 - 회복력
        "air": 1.0,    # 공기 - 신경계
        "fire": 0.9,   # 불 - 과로 주의
    },
    "STUDY": {
        "air": 1.6,    # 공기 - 지성, 분석
        "water": 1.3,  # 물 - 직관, 통찰
        "fire": 1.0,   # 불 - 열정
        "earth": 0.8,  # 땅 - 융통성 부족
    },
    "GENERAL": {
        "fire": 1.0,
        "earth": 1.0,
        "air": 1.0,
        "water": 1.0,
    },
}


def _positive_skewed_transform(x: float, base: float = 70, scale: float = 15) -> float:
    """긍정 편향 점수 변환 (오른쪽으로 치우친 분포)

    운세 앱 심리학 연구 기반:
    - 평균 70점, 표준편차 15점
    - 상위 65%가 '길' 이상
    - 흉 계열은 12% 이하
    - 대흉은 1-2% (극단적 불균형일 때만)

    Args:
        x: 원시 점수 (편차 기반 계산 결과)
        base: 기본 점수 (평균)
        scale: 변동 폭 (표준편차)

    Returns:
        30~100 범위의 긍정 편향 점수 (대흉 포함)
    """
    import math

    try:
        # x를 -3 ~ +3 표준편차 범위로 정규화
        normalized = x / 25  # 원시 점수 범위 조정

        # tanh로 -1 ~ +1 범위로 압축 (더 넓은 분포)
        compressed = math.tanh(normalized * 0.7)

        # 긍정 편향: 기본점수 + 변동폭 * 압축값
        score = base + (scale * compressed)

        # 최저 30점 (대흉 가능), 최고 100점
        return max(30, min(100, score))

    except (ValueError, OverflowError):
        return base


def _extract_eastern_score(fortune_data: dict, category: str = "GENERAL") -> str:
    """동양 사주에서 카테고리별 길흉 6단계 점수 추출

    긍정 편향 분포 적용 (운세 앱 심리학 연구 기반):
    - 평균 70점, 상위 65%가 '길' 이상
    - 흉 계열은 12% 이하 (대흉 1-2% 포함)
    - 카테고리별 가중치로 차별화된 점수 산정

    분포 비율 (목표):
    - 대길: 12% (88-100점)
    - 중길: 23% (78-87점)
    - 소길: 30% (68-77점)
    - 평: 23% (55-67점)
    - 소흉: 8% (45-54점)
    - 중흉: 3% (38-44점)
    - 대흉: 1% (30-37점)

    Args:
        fortune_data: 사주 분석 데이터
        category: 운세 카테고리 (MONEY, LOVE, CAREER, HEALTH, STUDY, GENERAL)

    Returns:
        길흉 7단계 문자열 (대길, 중길, 소길, 평, 소흉, 중흉, 대흉)
    """
    try:
        stats = _get_stats(fortune_data)
        weights = EASTERN_CATEGORY_WEIGHTS.get(category, EASTERN_CATEGORY_WEIGHTS["GENERAL"])

        # 1. 오행 데이터 추출
        five_elements = stats.get("five_elements", {})
        element_list = (
            five_elements.get("elements_list")
            or five_elements.get("list")
            or five_elements.get("elements")
            or []
        )

        def get_value(el: dict) -> float:
            return el.get("percent") or el.get("count") or 0

        def get_code(el: dict) -> str:
            return el.get("code") or el.get("element") or ""

        # 2. 편차 기반 원시 점수 계산
        raw_score = 0.0  # 편차 누적
        expected_ratio = 20.0  # 오행 균등 분포 기준 (100/5)

        for elem in element_list:
            code = get_code(elem)
            value = get_value(elem)
            weight = weights.get(code, 1.0)

            # 편차 = 실제 비율 - 기준 비율
            deviation = value - expected_ratio

            # 가중치 효과:
            # - weight > 1.0: 유리한 오행 → 비율 높으면 보너스
            # - weight < 1.0: 불리한 오행 → 비율 높으면 페널티
            adjustment = deviation * (weight - 1.0) * 2.0
            raw_score += adjustment

        # 3. 음양 균형도 가산 (±5점 범위)
        yin_yang = stats.get("yin_yang_ratio", {})
        yin = yin_yang.get("yin", 50)
        yang = yin_yang.get("yang", 50)
        yin_yang_bonus = 5 - abs(yin - yang) * 0.2
        raw_score += yin_yang_bonus

        # 4. 긍정 편향 변환 (평균 70, 표준편차 13)
        final_score = _positive_skewed_transform(raw_score, base=70, scale=13)

        # 5. 7단계 길흉 판정 (긍정 편향 분포)
        if final_score >= 88:
            return "대길"  # 12%
        elif final_score >= 78:
            return "중길"  # 23%
        elif final_score >= 68:
            return "소길"  # 30%
        elif final_score >= 55:
            return "평"    # 23%
        elif final_score >= 45:
            return "소흉"  # 8%
        elif final_score >= 38:
            return "중흉"  # 3%
        else:
            return "대흉"  # 1% (극단적 불균형)

    except Exception as e:
        logger.warning("eastern_score_extraction_failed", error=str(e), category=category)
        return "평"


def _extract_western_score(fortune_data: dict, category: str = "GENERAL") -> str:
    """서양 점성술에서 카테고리별 점수 추출 (45-100)

    긍정 편향 분포 적용 (운세 앱 심리학 연구 기반):
    - 평균 70점, 상위 65%가 70점 이상
    - 최저 45점 (극단적 부정 없음)
    - 카테고리별 가중치로 차별화된 점수 산정

    Args:
        fortune_data: 점성술 분석 데이터
        category: 운세 카테고리 (MONEY, LOVE, CAREER, HEALTH, STUDY, GENERAL)

    Returns:
        점수 문자열 (예: "85점")
    """
    try:
        stats = _get_stats(fortune_data)
        weights = WESTERN_CATEGORY_WEIGHTS.get(category, WESTERN_CATEGORY_WEIGHTS["GENERAL"])

        # element_4_distribution 또는 element_distribution에서 데이터 추출
        element_dist = stats.get("element_4_distribution", [])

        if not element_dist:
            # 다른 형태의 데이터 구조 시도
            elem_dist_dict = stats.get("element_distribution", {})
            if elem_dist_dict:
                element_dist = [
                    {"element": k, "percent": v}
                    for k, v in elem_dist_dict.items()
                    if isinstance(v, (int, float))
                ]

        if element_dist:
            # 편차 기반 원시 점수 계산
            raw_score = 0.0
            expected_ratio = 25.0  # 4원소 균등 분포 기준 (100/4)

            for elem in element_dist:
                # element 코드 추출 (다양한 키 대응)
                elem_code = (
                    elem.get("element")
                    or elem.get("code")
                    or elem.get("name")
                    or ""
                ).lower()

                # percent 값 추출
                percent = elem.get("percent") or elem.get("percentage") or 0

                # 가중치 조회
                weight = weights.get(elem_code, 1.0)

                # 편차 = 실제 비율 - 기준 비율
                deviation = percent - expected_ratio

                # 가중치 효과 (증폭 계수 2.5로 차별화 강화)
                adjustment = deviation * (weight - 1.0) * 2.5
                raw_score += adjustment

            # 긍정 편향 변환 (평균 70, 표준편차 13)
            final_score = _positive_skewed_transform(raw_score, base=70, scale=13)

            # 정수 점수로 변환
            score = int(round(final_score))

            return f"{score}점"

        return "70점"

    except Exception as e:
        logger.warning("western_score_extraction_failed", error=str(e), category=category)
        return "70점"


def _get_final_verdict(fortune_data: dict) -> dict:
    """fortune_data에서 final_verdict 추출 (래퍼 구조 대응)"""
    if "final_verdict" in fortune_data:
        return fortune_data.get("final_verdict", {})
    data = fortune_data.get("data", {})
    return data.get("final_verdict", {})


def _extract_eastern_one_liner(fortune_data: dict, category: FortuneCategory) -> str:
    """동양 사주에서 한줄 요약 문장 추출

    chart.summary, final_verdict, stats 등에서 한줄 요약 추출
    없으면 카테고리 기반 기본 문장 생성

    Returns:
        한줄 요약 문장 (예: "오행의 균형이 조화롭게 이루어진 사주입니다")
    """
    try:
        # 1. chart.summary에서 추출 시도
        chart = _get_chart(fortune_data)
        chart_summary = chart.get("summary", "")
        if chart_summary and len(chart_summary) > 10:
            # 첫 문장만 추출 (마침표 기준)
            first_sentence = chart_summary.split(".")[0].split("。")[0].strip()
            if first_sentence:
                return first_sentence

        # 2. final_verdict에서 추출 시도
        final_verdict = _get_final_verdict(fortune_data)
        verdict_message = final_verdict.get("message", "")
        if verdict_message and len(verdict_message) > 10:
            first_sentence = verdict_message.split(".")[0].split("。")[0].strip()
            if first_sentence:
                return first_sentence

        # 3. stats 기반 기본 문장 생성
        stats = _get_stats(fortune_data)

        # 오행 균형 확인
        five_elements = stats.get("five_elements", {})
        element_list = (
            five_elements.get("elements_list")
            or five_elements.get("list")
            or five_elements.get("elements")
            or []
        )

        if element_list:
            # 오행 분포가 고른지 확인
            values = [el.get("percent", 0) or el.get("count", 0) for el in element_list]
            if values:
                max_val = max(values)
                min_val = min(values)
                if max_val - min_val < 30:
                    return "오행의 균형이 조화롭게 이루어진 사주입니다"

        # 4. 카테고리별 기본 문장
        category_messages = {
            FortuneCategory.GENERAL: "전반적으로 안정적이고 균형 잡힌 운세를 보입니다",
            FortuneCategory.LOVE: "인연과 교감이 중요한 시기입니다",
            FortuneCategory.MONEY: "재물운이 점차 상승하는 흐름입니다",
            FortuneCategory.CAREER: "성장과 발전의 기회가 찾아올 것입니다",
            FortuneCategory.HEALTH: "건강 관리에 유의하며 활력을 유지하세요",
            FortuneCategory.STUDY: "집중력과 노력이 결실을 맺을 시기입니다",
        }
        return category_messages.get(category, "조화롭고 안정적인 운세를 보입니다")

    except Exception as e:
        logger.warning("eastern_one_liner_extraction_failed", error=str(e))
        return "긍정적인 운세를 기대할 수 있습니다"


def _extract_eastern_keyword(fortune_data: dict, category: FortuneCategory) -> str:
    """동양 사주에서 해시태그 형식 키워드 추출

    오행/십신/음양 특성을 기반으로 인스타그램 해시태그 형식으로 반환
    예: "#감성 #직관 #유연"
    """
    try:
        tags: list[str] = []

        # 오행별 키워드 매핑
        element_keywords = {
            "WOOD": ["성장", "창의", "진취"],
            "FIRE": ["열정", "활력", "명예"],
            "EARTH": ["안정", "신뢰", "중용"],
            "METAL": ["결단", "정의", "냉철"],
            "WATER": ["지혜", "유연", "감성"],
        }

        # 십신별 키워드 매핑
        ten_god_keywords = {
            "BI_GYEON": "자립",  # 비견
            "GEOP_JAE": "경쟁",  # 겁재
            "SIK_SHIN": "표현",  # 식신
            "SANG_GWAN": "창작",  # 상관
            "PYEON_JAE": "재치",  # 편재
            "JEONG_JAE": "성실",  # 정재
            "PYEON_GWAN": "권위",  # 편관
            "JEONG_GWAN": "책임",  # 정관
            "PYEON_IN": "학문",  # 편인
            "JEONG_IN": "지성",  # 정인
        }

        stats = _get_stats(fortune_data)

        # 1. 강한 오행에서 키워드 추출
        five_elements = stats.get("five_elements", {})
        element_list = (
            five_elements.get("elements_list")
            or five_elements.get("list")
            or five_elements.get("elements")
            or []
        )

        def get_value(el: dict) -> float:
            return el.get("percent") or el.get("count") or 0

        def get_code(el: dict) -> str:
            return el.get("code") or el.get("element") or ""

        if element_list:
            sorted_elements = sorted(element_list, key=get_value, reverse=True)
            # 상위 2개 오행에서 키워드 추출
            for el in sorted_elements[:2]:
                code = get_code(el)
                if code in element_keywords:
                    # 각 오행에서 첫 번째 키워드만 사용
                    tags.append(element_keywords[code][0])

        # 2. 십신에서 키워드 추출
        ten_gods = stats.get("ten_gods", {})
        gods_list = ten_gods.get("gods_list") or ten_gods.get("gods") or []

        if gods_list:
            sorted_gods = sorted(gods_list, key=get_value, reverse=True)
            # 가장 강한 십신에서 키워드 추출
            for god in sorted_gods[:1]:
                code = god.get("code") or god.get("god") or ""
                if code in ten_god_keywords:
                    tags.append(ten_god_keywords[code])

        # 3. 음양 특성에서 키워드 추출
        yin_yang = stats.get("yin_yang_ratio", {})
        yang = yin_yang.get("yang", 50)
        if yang >= 60:
            tags.append("적극")
        elif yang <= 40:
            tags.append("신중")

        # 태그가 없으면 카테고리 기반 기본 태그
        if not tags:
            category_tags = {
                FortuneCategory.GENERAL: ["통찰", "균형"],
                FortuneCategory.LOVE: ["인연", "교감"],
                FortuneCategory.MONEY: ["재물", "기회"],
                FortuneCategory.CAREER: ["성장", "도전"],
                FortuneCategory.HEALTH: ["활력", "균형"],
                FortuneCategory.STUDY: ["집중", "성취"],
            }
            tags = category_tags.get(category, ["분석", "완료"])

        # 최대 4개 태그, 해시태그 형식으로 반환
        unique_tags = list(dict.fromkeys(tags))[:4]
        return " ".join(f"#{tag}" for tag in unique_tags)

    except Exception as e:
        logger.warning("eastern_keyword_extraction_failed", error=str(e))
        return f"#{category.label_ko}"


def _extract_western_one_liner(fortune_data: dict, category: FortuneCategory) -> str:
    """서양 점성술에서 한줄 요약 문장 추출

    chart.summary, stats.keywords_summary 등에서 한줄 요약 추출
    없으면 카테고리 기반 기본 문장 생성

    Returns:
        한줄 요약 문장 (예: "열정적이고 도전적인 에너지가 가득한 차트입니다")
    """
    try:
        # 1. chart.summary에서 추출 시도
        chart = _get_chart(fortune_data)
        chart_summary = chart.get("summary", "")
        if chart_summary and len(chart_summary) > 10:
            # 첫 문장만 추출 (마침표 기준)
            first_sentence = chart_summary.split(".")[0].split("。")[0].strip()
            if first_sentence:
                return first_sentence

        # 2. stats.keywords_summary에서 추출 시도
        stats = _get_stats(fortune_data)
        keywords_summary = stats.get("keywords_summary", "")
        if isinstance(keywords_summary, str) and len(keywords_summary) > 10:
            first_sentence = keywords_summary.split(".")[0].split("。")[0].strip()
            if first_sentence:
                return first_sentence

        # 3. stats 기반 기본 문장 생성
        element = stats.get("element", "")
        modality = stats.get("modality", "")

        # 원소와 양태 조합으로 문장 생성
        element_traits = {
            "FIRE": "열정적이고 도전적인",
            "EARTH": "안정적이고 실용적인",
            "AIR": "지적이고 소통적인",
            "WATER": "감성적이고 직관적인",
        }

        modality_traits = {
            "CARDINAL": "주도적인",
            "FIXED": "확고한",
            "MUTABLE": "유연한",
        }

        traits = []
        if element in element_traits:
            traits.append(element_traits[element])
        if modality in modality_traits:
            traits.append(modality_traits[modality])

        if traits:
            return f"{' '.join(traits)} 에너지가 가득한 차트입니다"

        # 4. 카테고리별 기본 문장
        category_messages = {
            FortuneCategory.GENERAL: "전반적으로 균형 잡힌 운세를 보입니다",
            FortuneCategory.LOVE: "사랑과 관계에서 긍정적인 흐름입니다",
            FortuneCategory.MONEY: "재정적 안정과 성장이 기대됩니다",
            FortuneCategory.CAREER: "커리어 발전의 기회가 열려 있습니다",
            FortuneCategory.HEALTH: "건강과 활력이 유지되는 시기입니다",
            FortuneCategory.STUDY: "학습과 성장에 유리한 환경입니다",
        }
        return category_messages.get(category, "조화롭고 긍정적인 운세입니다")

    except Exception as e:
        logger.warning("western_one_liner_extraction_failed", error=str(e))
        return "긍정적인 운세를 기대할 수 있습니다"


def _extract_western_keyword(fortune_data: dict, category: FortuneCategory) -> str:
    """서양 점성술에서 해시태그 형식 키워드 추출

    원소(element), 양태(modality), 태양 별자리(sun_sign) 등을 기반으로
    인스타그램 해시태그 형식으로 반환
    예: "#감성 #변화 #쌍둥이자리"
    """
    try:
        tags: list[str] = []
        stats = _get_stats(fortune_data)

        # 원소(Element)별 키워드 매핑
        element_keywords = {
            "FIRE": ["열정", "도전", "활력"],
            "EARTH": ["안정", "현실", "인내"],
            "AIR": ["소통", "지성", "자유"],
            "WATER": ["감성", "직관", "공감"],
        }

        # 양태(Modality)별 키워드 매핑
        modality_keywords = {
            "CARDINAL": "리더십",
            "FIXED": "고집",
            "MUTABLE": "변화",
        }

        # 1. 원소에서 키워드 추출
        element = stats.get("element", "")
        if element in element_keywords:
            # 첫 번째 키워드만 사용
            tags.append(element_keywords[element][0])

        # 2. 양태에서 키워드 추출
        modality = stats.get("modality", "")
        if modality in modality_keywords:
            tags.append(modality_keywords[modality])

        # 3. 태양 별자리에서 키워드 추출
        sun_sign = stats.get("sun_sign", {})
        sign_name = sun_sign.get("name", "")
        if sign_name:
            tags.append(sign_name)

        # 4. keywords 배열에서 명사 키워드만 추출 (keywords_summary는 문장이므로 사용 안함)
        keywords = stats.get("keywords", [])

        if keywords and len(tags) < 4:
            for kw in keywords[:2]:  # 최대 2개
                if isinstance(kw, dict):
                    kw = kw.get("label", str(kw))
                kw_str = str(kw).strip()
                # 명사 키워드만 (공백 없는 짧은 단어)
                if kw_str and len(kw_str) <= 10 and " " not in kw_str:
                    tags.append(kw_str)
                    if len(tags) >= 4:
                        break

        # 태그가 없으면 카테고리 기반 기본 태그
        if not tags:
            category_tags = {
                FortuneCategory.GENERAL: ["통찰", "균형"],
                FortuneCategory.LOVE: ["인연", "교감"],
                FortuneCategory.MONEY: ["재물", "기회"],
                FortuneCategory.CAREER: ["성장", "도전"],
                FortuneCategory.HEALTH: ["활력", "균형"],
                FortuneCategory.STUDY: ["집중", "성취"],
            }
            tags = category_tags.get(category, ["분석", "완료"])

        # 최대 4개 태그, 해시태그 형식으로 반환
        unique_tags = list(dict.fromkeys(tags))[:4]
        return " ".join(f"#{tag}" for tag in unique_tags)

    except Exception as e:
        logger.warning("western_keyword_extraction_failed", error=str(e))
        return f"#{category.label_ko}"


# ============================================================
# 항목별 서머리 생성 (동양 사주)
# ============================================================


async def _extract_eastern_details(
    fortune_data: dict, category: FortuneCategory
) -> list[SummaryDetail]:
    """동양 사주 항목별 서머리 생성

    항목:
    1. 음양 (yin_yang) - 양/음 비율 기반 해석
    2. 오행 (five_elements) - 목화토금수 분포 기반 해석 (병렬 복합 메시지 사용)
    3. 십신 (ten_gods) - 십신 분포 기반 해석 (병렬 복합 메시지 사용)
    """
    details = []
    stats = _get_stats(fortune_data)

    # 병렬 복합 메시지 조회 시도
    section_messages = {}
    try:
        section_messages = await get_all_section_messages_parallel(
            fortune_data=fortune_data,
            fortune_type="eastern",
            category=category.value,
        )
        logger.info(
            "eastern_parallel_messages_fetched",
            sections=list(section_messages.keys()),
            sources={s: v[1] for s, v in section_messages.items()},
        )
    except Exception as e:
        logger.warning(
            "eastern_parallel_messages_failed",
            error=str(e),
            fallback="using_default_extraction",
        )
        # 실패 시 기존 로직으로 폴백

    # 카테고리별 해석 템플릿
    category_tips = {
        FortuneCategory.GENERAL: {
            "yang_high": "적극적이고 외향적인 에너지가 넘쳐요! 새로운 도전에 과감히 나서보세요!",
            "yin_high": "내면의 지혜가 깊어요! 신중하게 판단하고 차분히 움직이면 좋은 결과가 있어요!",
            "balanced": "음양의 균형이 잘 잡혀있어요! 안정적인 시기입니다!",
        },
        FortuneCategory.LOVE: {
            "yang_high": "적극적으로 어필하면 좋은 인연이 올 거예요! 먼저 다가가보세요!",
            "yin_high": "섬세하고 배려심이 돋보이는 시기! 진정성 있는 모습이 매력 포인트!",
            "balanced": "연애에서 밀당 밸런스 완벽해요! 자연스럽게 흘러가게 두세요!",
        },
        FortuneCategory.MONEY: {
            "yang_high": "적극적인 투자나 자산관리가 좋아요! 과감한 결정이 수익을 불러와요!",
            "yin_high": "안전한 저축과 보수적인 투자가 좋아요! 지금은 지키는 게 버는 거예요!",
            "balanced": "수입과 지출의 균형을 잘 맞추고 있어요! 현상 유지가 최선!",
        },
        FortuneCategory.CAREER: {
            "yang_high": "리더십을 발휘할 타이밍! 앞장서서 프로젝트를 이끌어보세요!",
            "yin_high": "팀원들과의 협업이 빛나는 시기! 조용히 실력을 쌓아가세요!",
            "balanced": "일과 휴식의 균형이 잘 잡혀있어요! 이 페이스 유지하세요!",
        },
        FortuneCategory.HEALTH: {
            "yang_high": "활동적인 운동이 좋아요! 땀 흘리면서 스트레스 해소하세요!",
            "yin_high": "휴식과 명상이 필요해요! 무리하지 말고 충분히 쉬세요!",
            "balanced": "건강 상태가 안정적이에요! 현재 생활 패턴을 유지하세요!",
        },
        FortuneCategory.STUDY: {
            "yang_high": "적극적으로 질문하고 토론하면 학습 효과가 올라가요!",
            "yin_high": "혼자 깊이 파고드는 학습이 효과적이에요! 집중 시간을 확보하세요!",
            "balanced": "그룹 스터디와 개인 학습을 병행하면 최고의 효과!",
        },
    }

    tips = category_tips.get(category, category_tips[FortuneCategory.GENERAL])

    # 1. 음양 (yin_yang_ratio)
    yin_yang = stats.get("yin_yang_ratio", {})
    yang_percent = yin_yang.get("yang", 50)
    yin_percent = yin_yang.get("yin", 50)

    if yang_percent >= 60:
        yin_yang_desc = f"양이 {yang_percent}%! {tips['yang_high']}"
    elif yin_percent >= 60:
        yin_yang_desc = f"음이 {yin_percent}%! {tips['yin_high']}"
    else:
        yin_yang_desc = f"음양 비율 {yin_percent}:{yang_percent}! {tips['balanced']}"

    details.append(
        SummaryDetail(
            section="yin_yang",
            title="음양 밸런스",
            description=yin_yang_desc,
        )
    )

    # 2. 오행 5개 전부 개별 표시 (five_elements)
    five_elements = stats.get("five_elements", {})
    # elements_list (model_dump default), list (alias), elements (legacy)
    element_list = (
        five_elements.get("elements_list")
        or five_elements.get("list")
        or five_elements.get("elements")
        or []
    )

    element_korean = {
        "WOOD": "목(木)",
        "FIRE": "화(火)",
        "EARTH": "토(土)",
        "METAL": "금(金)",
        "WATER": "수(水)",
    }

    element_category_tips = {
        FortuneCategory.GENERAL: {
            "WOOD": "나무처럼 성장하고 발전하는 기운이 흐르고 있습니다. 새로운 시작이나 도전에 좋은 에너지를 가지고 있습니다.",
            "FIRE": "불처럼 뜨거운 열정과 추진력이 있습니다. 적극적으로 행동하면 좋은 결과를 얻을 수 있습니다.",
            "EARTH": "땅처럼 안정적이고 신뢰할 수 있는 기운입니다. 꾸준함과 성실함이 빛을 발합니다.",
            "METAL": "쇠처럼 단단한 결단력과 실행력을 가지고 있습니다. 정리하고 마무리하는 것에 강합니다.",
            "WATER": "물처럼 유연하고 지혜로운 기운입니다. 소통과 네트워킹에 강점이 있습니다.",
        },
        FortuneCategory.MONEY: {
            "WOOD": "나무가 자라듯이 자산이 서서히 성장하는 기운이 있습니다. 장기적인 관점에서 투자하면 좋은 결과가 기대됩니다.",
            "FIRE": "불처럼 적극적으로 투자하는 성향입니다. 단, 너무 과하면 손실 위험도 있으니 적절한 균형이 필요합니다.",
            "EARTH": "땅처럼 안정적인 자산을 선호합니다. 부동산이나 실물 자산에 관심을 가져볼 만합니다.",
            "METAL": "효율적으로 재테크를 관리하는 능력이 있습니다. 불필요한 지출을 정리하고 체계적으로 관리하면 좋습니다.",
            "WATER": "정보의 흐름을 잘 읽는 능력이 있습니다. 트렌드를 파악해서 수익을 창출하는 것이 가능합니다.",
        },
        FortuneCategory.LOVE: {
            "WOOD": "나무가 자라듯 관계가 발전하고 성장할 가능성이 높습니다. 새로운 인연을 만나기에도 좋습니다.",
            "FIRE": "불꽃처럼 열정적인 연애를 하는 스타일입니다. 뜨겁게 사랑하지만, 감정 조절도 필요합니다.",
            "EARTH": "땅처럼 안정적이고 믿음직한 관계를 추구합니다. 진지하고 오래가는 사랑을 원합니다.",
            "METAL": "관계에서 명확한 기준과 경계를 중시합니다. 서로의 공간을 존중하는 연애가 맞습니다.",
            "WATER": "물처럼 감성적인 교감을 중요하게 생각합니다. 깊이 있는 대화와 감정 공유가 사랑의 핵심입니다.",
        },
        FortuneCategory.CAREER: {
            "WOOD": "커리어가 나무처럼 성장하고 발전할 가능성이 높습니다. 새로운 도전이나 스킬업에 좋은 시기입니다.",
            "FIRE": "불처럼 추진력 있게 업무를 처리합니다. 열정적으로 일하면 좋은 성과를 낼 수 있습니다.",
            "EARTH": "꾸준하고 성실하게 일해서 신뢰를 얻습니다. 묵묵히 하던 일이 인정받는 시기입니다.",
            "METAL": "효율적이고 정확하게 일처리를 합니다. 체계적으로 정리하고 마무리하는 것이 강점입니다.",
            "WATER": "네트워킹과 소통 능력이 뛰어납니다. 인맥을 활용하면 좋은 기회가 찾아옵니다.",
        },
        FortuneCategory.HEALTH: {
            "WOOD": "간과 눈 건강에 신경을 써야 합니다. 스트레칭이나 눈 휴식을 자주 취해주세요.",
            "FIRE": "심장과 혈액순환 관리가 중요합니다. 과도한 음주나 자극적인 음식은 자제하는 것이 좋습니다.",
            "EARTH": "소화기 건강을 챙겨야 합니다. 규칙적인 식사와 과식 주의가 필요합니다.",
            "METAL": "호흡기와 피부 건강에 신경써야 합니다. 맑은 공기 마시기와 피부 보습을 챙겨주세요.",
            "WATER": "신장과 방광 건강에 주의가 필요합니다. 충분한 수분 섭취를 잊지 마세요.",
        },
        FortuneCategory.STUDY: {
            "WOOD": "새로운 것을 배우기에 좋은 기운이 있습니다. 새로운 분야에 도전하면 빠르게 성장할 수 있습니다.",
            "FIRE": "집중력과 열정이 있어서 몰입해서 공부하면 효과가 좋습니다. 단기 집중 학습이 잘 맞습니다.",
            "EARTH": "기본기가 탄탄하게 쌓이는 시기입니다. 꾸준히 복습하면 실력이 단단해집니다.",
            "METAL": "효율적으로 학습하는 능력이 있습니다. 요약 정리를 잘하면 학습 효과가 배가됩니다.",
            "WATER": "깊이 있게 이해하는 능력이 뛰어납니다. 개념을 제대로 파악하면 응용력이 좋아집니다.",
        },
    }

    element_tips = element_category_tips.get(
        category, element_category_tips[FortuneCategory.GENERAL]
    )

    # 오행 5개 전부 개별로 표시
    # 병렬 메시지가 있으면 사용, 없으면 기존 로직
    if "five_elements" in section_messages:
        five_elem_message, source = section_messages["five_elements"]
        details.append(
            SummaryDetail(
                section="five_elements",
                title="오행 분포",
                description=five_elem_message,
            )
        )
        logger.debug(
            "using_parallel_message",
            section="five_elements",
            source=source,
        )
    elif element_list:
        for elem in element_list:
            elem_code = elem.get("element", "")
            elem_name = element_korean.get(elem_code, "알 수 없음")
            elem_count = elem.get("count", 0)
            elem_tip = element_tips.get(elem_code, "기운이 있습니다.")

            five_elem_desc = f"{elem_count}개 - {elem_tip}"

            details.append(
                SummaryDetail(
                    section="five_elements",
                    title=elem_name,
                    description=five_elem_desc,
                )
            )

    # 3. 십신 있는 것 전부 개별 표시 (ten_gods)
    ten_gods = stats.get("ten_gods", {})
    # gods_list (model_dump default), list (alias), gods (legacy)
    ten_gods_list = ten_gods.get("gods_list") or ten_gods.get("list") or ten_gods.get("gods") or []

    ten_god_korean = {
        "BIJEON": "비견",
        "GEOBJE": "겁재",
        "SIKSHIN": "식신",
        "SANGGWAN": "상관",
        "PYEONJAE": "편재",
        "JEONGJAE": "정재",
        "PYEONGWAN": "편관",
        "JEONGGWAN": "정관",
        "PYEONIN": "편인",
        "JEONGIN": "정인",
    }

    ten_god_category_tips = {
        FortuneCategory.GENERAL: {
            "BIJEON": "자기주장이 강하고 독립심이 있어서 자신만의 길을 개척하는 성향입니다. 때로는 고집으로 보일 수 있지만 주관이 뚜렷합니다.",
            "GEOBJE": "경쟁심과 승부욕이 강해서 도전적인 상황에서 더 빛을 발합니다. 라이벌이 있으면 더 열심히 하는 타입입니다.",
            "SIKSHIN": "표현력이 풍부하고 먹는 것에 복이 있습니다. 창의적인 아이디어가 넘치고 여유를 즐길 줄 압니다.",
            "SANGGWAN": "재능이 넘치고 표현 욕구가 강합니다. 예술적 감각이 있고 자기만의 스타일이 확실합니다.",
            "PYEONJAE": "사업 감각이 있고 돈을 다루는 재능이 있습니다. 기회를 포착하는 눈이 있어서 수완이 좋습니다.",
            "JEONGJAE": "꾸준하게 재물을 관리하고 안정을 추구합니다. 착실하게 모으고 성실하게 관리하는 스타일입니다.",
            "PYEONGWAN": "리더십이 있고 추진력이 강합니다. 앞장서서 이끄는 것을 좋아하고 결단력이 있습니다.",
            "JEONGGWAN": "책임감이 강하고 성실합니다. 맡은 일은 끝까지 해내고 신뢰받는 사람입니다.",
            "PYEONIN": "직관력이 뛰어나고 예술적 감각이 있습니다. 남들이 보지 못하는 것을 보는 통찰력이 있습니다.",
            "JEONGIN": "학습 능력이 뛰어나고 지혜가 있습니다. 배우는 것을 좋아하고 지식 습득이 빠릅니다.",
        },
        FortuneCategory.MONEY: {
            "BIJEON": "내 돈은 내가 쓴다는 마인드가 강해서 씀씀이가 큰 편입니다. 투자보다는 소비 성향이 강할 수 있어요.",
            "GEOBJE": "남들과 경쟁하면서 돈을 벌 수 있습니다. 승부욕을 발휘하면 투자에서도 좋은 성과를 낼 수 있어요.",
            "SIKSHIN": "맛있는 것, 좋은 것에 돈을 쓰는 걸 좋아합니다. 삶의 질을 높이는 데 투자하는 타입이에요.",
            "SANGGWAN": "재능을 돈으로 바꿀 수 있는 능력이 있습니다. 창작이나 프리랜서로 수익을 내기 좋습니다.",
            "PYEONJAE": "재테크의 감각이 타고났습니다. 기회를 잘 잡고 돈 버는 방법을 잘 알아요.",
            "JEONGJAE": "월급을 착실하게 모아서 부자가 되는 타입입니다. 꾸준히 저축하고 안전하게 관리합니다.",
            "PYEONGWAN": "돈보다 지위나 권력에 관심이 있어서, 높은 자리에 오르면 돈은 자연히 따라옵니다.",
            "JEONGGWAN": "안정적인 수입을 선호해서 공무원이나 대기업 같은 안정적인 곳이 맞습니다.",
            "PYEONIN": "투자 직관이 있어서 감으로 고르면 맞을 때가 많습니다. 단, 검증은 필수입니다.",
            "JEONGIN": "재테크 공부를 하면 실력이 빠르게 늘어납니다. 배워서 투자하면 성공 확률이 높아요.",
        },
        FortuneCategory.LOVE: {
            "BIJEON": "자존감이 높은 연애를 합니다. 나를 존중해주는 사람을 원하고, 양보보다는 맞춰가는 연애를 해요.",
            "GEOBJE": "연적이 나타나도 물러서지 않습니다. 경쟁 상황에서 오히려 더 불타올라요.",
            "SIKSHIN": "맛집 데이트, 여행 등 즐거운 연애를 합니다. 함께 먹고 놀면서 사랑을 키워가요.",
            "SANGGWAN": "표현력이 뛰어나서 달달한 말로 상대방을 녹입니다. 연애할 때 분위기 메이커예요.",
            "PYEONJAE": "연애에도 통 크게 투자합니다. 선물이나 데이트에 아낌없이 쓰는 스타일이에요.",
            "JEONGJAE": "진심으로 사랑하고 오래 만납니다. 진정성 있는 관계를 원하고 한 번 만나면 오래가요.",
            "PYEONGWAN": "연애에서 주도권을 잡는 편입니다. 리드하면서 관계를 이끌어가요.",
            "JEONGGWAN": "책임감 있는 연애를 합니다. 결혼까지 생각하고 진지하게 만나는 타입이에요.",
            "PYEONIN": "감성적인 연애를 합니다. 눈빛만 봐도 통하고 감정 교류가 풍부해요.",
            "JEONGIN": "대화가 잘 통하는 사람을 원합니다. 지적인 교류가 있어야 오래 만날 수 있어요.",
        },
        FortuneCategory.CAREER: {
            "BIJEON": "혼자서 독립적으로 일하는 것을 선호합니다. 팀보다는 개인 플레이에서 빛나요.",
            "GEOBJE": "경쟁 환경에서 더 잘합니다. 영업이나 성과급 직종에서 능력을 발휘해요.",
            "SIKSHIN": "창의적인 업무에 잘 맞습니다. 아이디어가 필요한 곳에서 인정받아요.",
            "SANGGWAN": "전문성을 살려서 일할 수 있습니다. 자기 분야에서 최고가 될 수 있어요.",
            "PYEONJAE": "사업이나 영업에 재능이 있습니다. 돈 되는 일을 잘 찾아내요.",
            "JEONGJAE": "안정적인 직장 생활에 잘 맞습니다. 한 회사에서 오래 일하면서 신뢰를 쌓아요.",
            "PYEONGWAN": "관리직이나 리더 역할에 적합합니다. 팀을 이끌면서 성과를 내요.",
            "JEONGGWAN": "공직이나 정규직에 유리합니다. 안정적인 환경에서 성실하게 일해요.",
            "PYEONIN": "예술이나 창작 분야에 적합합니다. 창의력이 필요한 곳에서 빛나요.",
            "JEONGIN": "교육이나 연구 분야에 유리합니다. 배우고 가르치는 일이 잘 맞아요.",
        },
        FortuneCategory.HEALTH: {
            "BIJEON": "자기 관리를 잘 해야 합니다. 고집 때문에 몸 상태를 무시하지 말고 꾸준히 챙기세요.",
            "GEOBJE": "경쟁 스트레스가 쌓이기 쉽습니다. 적절한 스트레스 해소 방법을 찾으세요.",
            "SIKSHIN": "먹는 것을 좋아해서 소화기 건강에 주의가 필요합니다. 과식 조심하세요.",
            "SANGGWAN": "일에 몰두하다 과로하기 쉽습니다. 적절한 휴식을 잊지 마세요.",
            "PYEONJAE": "활동적이라 에너지 소모가 큽니다. 규칙적인 운동으로 체력을 유지하세요.",
            "JEONGJAE": "규칙적인 생활이 건강의 핵심입니다. 정해진 시간에 먹고 자면 건강해져요.",
            "PYEONGWAN": "업무 스트레스로 몸이 힘들 수 있어요. 리더 역할에서 오는 부담을 관리하세요.",
            "JEONGGWAN": "균형 잡힌 생활이 중요합니다. 일과 휴식의 밸런스를 유지하세요.",
            "PYEONIN": "정신 건강에 신경 써야 합니다. 명상이나 취미 활동으로 마음을 챙기세요.",
            "JEONGIN": "머리를 많이 쓰니 충분한 휴식이 필요합니다. 수면 시간을 꼭 확보하세요.",
        },
        FortuneCategory.STUDY: {
            "BIJEON": "혼자 공부하는 게 더 잘 맞습니다. 자기주도 학습으로 진행하면 효율이 높아요.",
            "GEOBJE": "경쟁자가 있으면 더 열심히 합니다. 스터디 그룹에서 순위 경쟁하면 동기부여가 됩니다.",
            "SIKSHIN": "이론보다 실습 위주 학습이 잘 맞습니다. 직접 해보면서 배우면 빠르게 습득해요.",
            "SANGGWAN": "창의적인 방식으로 학습하면 효과가 좋습니다. 자기만의 학습법을 개발하세요.",
            "PYEONJAE": "다양한 분야를 넓게 배우는 것이 유리합니다. 여러 가지 경험이 나중에 도움이 돼요.",
            "JEONGJAE": "체계적으로 차근차근 배우면 잘 맞습니다. 커리큘럼대로 따라가면 성과가 나요.",
            "PYEONGWAN": "리더십이나 경영 관련 학습이 유리합니다. 팀 프로젝트에서 리드하면서 배워요.",
            "JEONGGWAN": "정규 교육 과정을 따라가면 좋습니다. 학교나 학원 수업이 잘 맞아요.",
            "PYEONIN": "감으로 이해하는 능력이 있습니다. 직관적으로 파악하면 빠르게 습득해요.",
            "JEONGIN": "깊이 있게 파고드는 학습이 강점입니다. 한 분야를 제대로 파면 전문가가 될 수 있어요.",
        },
    }

    ten_god_tips = ten_god_category_tips.get(
        category, ten_god_category_tips[FortuneCategory.GENERAL]
    )

    # 십신 있는 것만 전부 개별로 표시
    # 병렬 메시지가 있으면 사용, 없으면 기존 로직
    if "ten_gods" in section_messages:
        ten_gods_message, source = section_messages["ten_gods"]
        details.append(
            SummaryDetail(
                section="ten_gods",
                title="십신 분석",
                description=ten_gods_message,
            )
        )
        logger.debug(
            "using_parallel_message",
            section="ten_gods",
            source=source,
        )
    elif ten_gods_list:
        for god in ten_gods_list:
            god_code = god.get("code", "")
            god_name = ten_god_korean.get(god_code, god_code)
            god_count = god.get("count", 0)

            if god_count > 0:  # 개수가 0보다 큰 것만 표시
                god_tip = ten_god_tips.get(god_code, "특별한 기운이 있습니다.")
                ten_god_desc = f"{god_count}개 - {god_tip}"

                details.append(
                    SummaryDetail(
                        section="ten_gods",
                        title=god_name,
                        description=ten_god_desc,
                    )
                )

    # 기본값
    if not details:
        details.append(
            SummaryDetail(
                section="general",
                title="종합 운세",
                description=f"당신의 {category.label_ko}을 분석한 결과, 균형 잡힌 기운이 감지됩니다!",
            )
        )

    return details


# ============================================================
# 항목별 서머리 생성 (서양 점성술)
# ============================================================


async def _extract_western_details(
    fortune_data: dict, category: FortuneCategory
) -> list[SummaryDetail]:
    """서양 점성술 항목별 서머리 생성

    항목:
    1. 원소 (elements) - 불/물/공기/흙 분포 (병렬 복합 메시지 사용)
    2. 양태 (modality) - 활동/고정/변통 (병렬 복합 메시지 사용)
    3. 주요 행성 (planets)
    """
    details = []
    stats = _get_stats(fortune_data)

    # 병렬 복합 메시지 조회 시도
    section_messages = {}
    try:
        section_messages = await get_all_section_messages_parallel(
            fortune_data=fortune_data,
            fortune_type="western",
            category=category.value,
        )
        logger.info(
            "western_parallel_messages_fetched",
            sections=list(section_messages.keys()),
            sources={s: v[1] for s, v in section_messages.items()},
        )
    except Exception as e:
        logger.warning(
            "western_parallel_messages_failed",
            error=str(e),
            fallback="using_default_extraction",
        )
        # 실패 시 기존 로직으로 폴백

    # 1. 4원소 전부 개별 표시 (element_4_distribution)
    element_dist = stats.get("element_4_distribution", [])

    element_korean = {
        "fire": "불(Fire)",
        "water": "물(Water)",
        "air": "공기(Air)",
        "earth": "흙(Earth)",
        "FIRE": "불(Fire)",
        "WATER": "물(Water)",
        "AIR": "공기(Air)",
        "EARTH": "흙(Earth)",
    }

    element_category_tips = {
        FortuneCategory.GENERAL: {
            "fire": "불의 기운이 있어서 열정적이고 추진력이 강합니다. 적극적으로 행동하면 좋은 결과를 얻을 수 있어요.",
            "water": "물의 기운이 있어서 감성이 풍부하고 직관력이 뛰어납니다. 느낌을 믿고 따라가면 좋은 방향으로 흘러가요.",
            "air": "공기의 기운이 있어서 소통 능력이 뛰어나고 아이디어가 풍부합니다. 생각을 말로 표현하면 인정받아요.",
            "earth": "흙의 기운이 있어서 현실적이고 안정적입니다. 꾸준하고 성실하게 하면 결과가 따라와요.",
        },
        FortuneCategory.MONEY: {
            "fire": "불의 기운이 있어서 적극적으로 투자하는 성향입니다. 과감하게 움직이면 수익을 낼 수 있지만, 너무 급하면 손실 위험도 있어요.",
            "water": "물의 기운이 있어서 돈의 흐름을 잘 읽습니다. 직감을 믿고 투자하면 좋은 결과를 얻을 수 있어요.",
            "air": "공기의 기운이 있어서 정보 활용 능력이 뛰어납니다. 트렌드를 빠르게 파악해서 수익 기회를 잡아요.",
            "earth": "흙의 기운이 있어서 안정적인 자산 관리에 적합합니다. 부동산이나 실물 자산에 관심을 가져볼 만해요.",
        },
        FortuneCategory.LOVE: {
            "fire": "불의 기운이 있어서 열정적으로 사랑합니다. 뜨겁게 타오르는 연애를 하지만, 감정 조절도 필요해요.",
            "water": "물의 기운이 있어서 깊은 감정 교류를 중시합니다. 영혼까지 교감하는 진정한 사랑을 원해요.",
            "air": "공기의 기운이 있어서 대화와 소통이 연애의 핵심입니다. 말이 잘 통하는 사람과 잘 맞아요.",
            "earth": "흙의 기운이 있어서 안정적인 관계를 추구합니다. 믿음직하고 오래가는 사랑을 원해요.",
        },
        FortuneCategory.CAREER: {
            "fire": "불의 기운이 있어서 추진력 있게 일을 처리합니다. 열정적으로 일하면 좋은 성과를 낼 수 있어요.",
            "water": "물의 기운이 있어서 창의적인 분야에 적합합니다. 예술이나 상담처럼 감성을 활용하는 일이 잘 맞아요.",
            "air": "공기의 기운이 있어서 기획이나 마케팅에서 빛납니다. 아이디어로 승부하면 인정받아요.",
            "earth": "흙의 기운이 있어서 체계적이고 꾸준하게 성과를 냅니다. 안정적인 환경에서 실력을 발휘해요.",
        },
        FortuneCategory.HEALTH: {
            "fire": "불의 기운이 있어서 에너지가 넘치지만 과로에 주의해야 합니다. 적절한 휴식으로 밸런스를 맞추세요.",
            "water": "물의 기운이 있어서 정서적 안정이 건강의 핵심입니다. 스트레스 관리를 잘 해야 몸도 건강해요.",
            "air": "공기의 기운이 있어서 호흡기 건강에 신경 써야 합니다. 맑은 공기 마시고 심호흡을 자주 하세요.",
            "earth": "흙의 기운이 있어서 소화기 건강을 챙겨야 합니다. 규칙적인 식사와 과식 주의가 필요해요.",
        },
        FortuneCategory.STUDY: {
            "fire": "불의 기운이 있어서 집중해서 공부하면 효과가 좋습니다. 단기간 몰입 학습이 잘 맞아요.",
            "water": "물의 기운이 있어서 감성적으로 이해하는 것이 강점입니다. 스토리로 배우면 기억에 오래 남아요.",
            "air": "공기의 기운이 있어서 논리적 사고력이 뛰어납니다. 수학이나 과학 같은 분야에 강해요.",
            "earth": "흙의 기운이 있어서 체계적으로 학습하면 잘 맞습니다. 차근차근 기본부터 쌓아가세요.",
        },
    }

    element_tips = element_category_tips.get(
        category, element_category_tips[FortuneCategory.GENERAL]
    )

    # 4원소 전부 개별로 표시
    # 병렬 메시지가 있으면 사용, 없으면 기존 로직
    if "elements" in section_messages:
        elements_message, source = section_messages["elements"]
        details.append(
            SummaryDetail(
                section="elements",
                title="4원소 분포",
                description=elements_message,
            )
        )
        logger.debug(
            "using_parallel_message",
            section="elements",
            source=source,
        )
    elif element_dist:
        for elem in element_dist:
            # code 또는 element 키 지원 (BE 응답 구조 대응)
            elem_code = (elem.get("code") or elem.get("element") or "").lower()
            elem_name = element_korean.get(elem_code, elem_code)
            # percent 또는 percentage 키 지원
            percentage = elem.get("percent") or elem.get("percentage") or 0
            elem_tip = element_tips.get(elem_code, "특별한 기운이 있습니다.")

            elem_desc = f"{percentage}% - {elem_tip}"

            details.append(
                SummaryDetail(
                    section="elements",
                    title=elem_name,
                    description=elem_desc,
                )
            )

    # 2. 양태 3개 전부 개별 표시 (modality_3_distribution)
    modality_dist = stats.get("modality_3_distribution", [])

    modality_korean = {
        "cardinal": "활동(Cardinal)",
        "fixed": "고정(Fixed)",
        "mutable": "변통(Mutable)",
        "CARDINAL": "활동(Cardinal)",
        "FIXED": "고정(Fixed)",
        "MUTABLE": "변통(Mutable)",
    }

    modality_category_tips = {
        FortuneCategory.GENERAL: {
            "cardinal": "활동궁의 기운이 있어서 새로운 것을 시작하는 힘이 강합니다. 앞장서서 이끌고 개척하는 것을 좋아해요.",
            "fixed": "고정궁의 기운이 있어서 한 번 시작한 것을 끝까지 해내는 지구력이 있습니다. 꾸준함이 최고의 강점이에요.",
            "mutable": "변통궁의 기운이 있어서 상황에 맞게 유연하게 적응합니다. 변화에 빠르게 대응하는 능력이 뛰어나요.",
        },
        FortuneCategory.MONEY: {
            "cardinal": "활동궁의 기운이 있어서 새로운 투자 기회를 개척합니다. 남들보다 먼저 움직여서 선점하는 것이 강점이에요.",
            "fixed": "고정궁의 기운이 있어서 장기 투자에 적합합니다. 한 번 투자하면 끝까지 홀딩하면서 기다릴 수 있어요.",
            "mutable": "변통궁의 기운이 있어서 시장 변화에 민첩하게 대응합니다. 상황에 따라 유연하게 전략을 바꿀 수 있어요.",
        },
        FortuneCategory.LOVE: {
            "cardinal": "활동궁의 기운이 있어서 적극적으로 연애합니다. 먼저 다가가고 고백하는 것을 두려워하지 않아요.",
            "fixed": "고정궁의 기운이 있어서 한 사람을 끝까지 사랑합니다. 안정적이고 오래가는 관계를 원해요.",
            "mutable": "변통궁의 기운이 있어서 다양한 만남을 즐깁니다. 상대에 맞춰 유연하게 관계를 형성할 수 있어요.",
        },
        FortuneCategory.CAREER: {
            "cardinal": "활동궁의 기운이 있어서 주도적으로 일합니다. 새로운 프로젝트를 시작하거나 팀을 이끄는 것이 잘 맞아요.",
            "fixed": "고정궁의 기운이 있어서 꾸준히 성과를 냅니다. 맡은 일을 끝까지 책임지고 완수하는 것이 강점이에요.",
            "mutable": "변통궁의 기운이 있어서 변화하는 환경에 잘 적응합니다. 다양한 업무를 유연하게 처리할 수 있어요.",
        },
        FortuneCategory.HEALTH: {
            "cardinal": "활동궁의 기운이 있어서 활동적인 건강 관리가 적합합니다. 새로운 운동에 도전하면 꾸준히 할 수 있어요.",
            "fixed": "고정궁의 기운이 있어서 규칙적인 생활이 건강의 핵심입니다. 정해진 루틴을 지키면 건강해져요.",
            "mutable": "변통궁의 기운이 있어서 몸 상태에 따라 유연하게 관리해야 합니다. 그때그때 필요한 것을 챙기세요.",
        },
        FortuneCategory.STUDY: {
            "cardinal": "활동궁의 기운이 있어서 새로운 분야를 먼저 배우는 것이 강점입니다. 선도적으로 학습하면 효과가 좋아요.",
            "fixed": "고정궁의 기운이 있어서 한 분야를 깊이 파고드는 집중 학습이 잘 맞습니다. 끈기 있게 하면 전문가가 될 수 있어요.",
            "mutable": "변통궁의 기운이 있어서 다양한 학습법을 시도하는 것이 유리합니다. 상황에 맞게 방법을 바꾸면 효과가 좋아요.",
        },
    }

    modality_tips = modality_category_tips.get(
        category, modality_category_tips[FortuneCategory.GENERAL]
    )

    # 양태 3개 전부 개별로 표시
    # 병렬 메시지가 있으면 사용, 없으면 기존 로직
    if "modality" in section_messages:
        modality_message, source = section_messages["modality"]
        details.append(
            SummaryDetail(
                section="modality",
                title="양태 분석",
                description=modality_message,
            )
        )
        logger.debug(
            "using_parallel_message",
            section="modality",
            source=source,
        )
    elif modality_dist:
        for mod in modality_dist:
            # code 또는 modality 키 지원 (BE 응답 구조 대응)
            mod_code = (mod.get("code") or mod.get("modality") or "").lower()
            mod_name = modality_korean.get(mod_code, mod_code)
            # percent 또는 percentage 키 지원
            percentage = mod.get("percent") or mod.get("percentage") or 0
            mod_tip = modality_tips.get(mod_code, "특별한 양태입니다.")

            mod_desc = f"{percentage}% - {mod_tip}"

            details.append(
                SummaryDetail(
                    section="modality",
                    title=mod_name,
                    description=mod_desc,
                )
            )

    # 3. 메인 별자리
    main_sign = stats.get("main_sign", {})
    sign_name = main_sign.get("name", "")

    if sign_name:
        sign_desc = (
            f"당신의 태양 별자리는 {sign_name}! 이 에너지가 {category.label_ko}에 영향을 미쳐요!"
        )
        details.append(
            SummaryDetail(
                section="sun_sign",
                title="태양 별자리",
                description=sign_desc,
            )
        )

    # 기본값
    if not details:
        details.append(
            SummaryDetail(
                section="general",
                title="종합 운세",
                description=f"당신의 {category.label_ko}을 점성술로 분석한 결과입니다!",
            )
        )

    return details


# ============================================================
# API 엔드포인트
# ============================================================


@router.post(
    "/quick-summary",
    response_model=QuickSummaryResponse,
    summary="빠른 운세 요약",
    description="""기존 분석 결과(fortune_key)를 기반으로 점수, 키워드, 항목별 서머리를 반환합니다.

**사전 조건**: `/eastern` 또는 `/western` API로 운세 분석 완료 필요

**캐싱**: Progressive Caching으로 Redis 캐시 → 실시간 생성 → 폴백 순서로 처리""",
    responses={
        200: {
            "description": "요약 성공",
            "content": {
                "application/json": {
                    "examples": {
                        "eastern": {
                            "summary": "동양 사주 요약",
                            "value": {
                                "fortune_id": "east_abc123",
                                "fortune_type": "eastern",
                                "category": "MONEY",
                                "score": "木旺 水弱",
                                "keyword": "재물운 상승기",
                                "details": [
                                    {
                                        "section": "yin_yang",
                                        "title": "음양 밸런스",
                                        "description": "양이 80%! 적극적인 투자나 자산관리가 좋아요!",
                                    },
                                    {
                                        "section": "five_elements",
                                        "title": "오행 분포",
                                        "description": "화(火) 기운이 3개로 가장 강해요! 불같이 하다가 패가망신...은 농담이고 열정적으로 투자하세요!",
                                    },
                                    {
                                        "section": "ten_gods",
                                        "title": "십신 분석",
                                        "description": "비견이 2개! 자신감 있게 투자하되 고집은 금물!",
                                    },
                                ],
                            },
                        },
                        "western": {
                            "summary": "서양 점성술 요약",
                            "value": {
                                "fortune_id": "west_xyz789",
                                "fortune_type": "western",
                                "category": "LOVE",
                                "score": "82점",
                                "keyword": "금성이 7하우스 통과 중",
                                "details": [
                                    {
                                        "section": "elements",
                                        "title": "4원소 분포",
                                        "description": "불의 기운이 40%로 가장 강해요! 불꽃같은 사랑!",
                                    },
                                    {
                                        "section": "modality",
                                        "title": "양태 분석",
                                        "description": "활동궁이 50%! 먼저 고백하세요!",
                                    },
                                ],
                            },
                        },
                    }
                }
            },
        },
        404: {"description": "운세 분석 결과를 찾을 수 없음"},
        500: {"description": "서버 오류"},
    },
)
async def get_quick_summary(
    request: QuickSummaryRequest,
    force: bool = Query(
        False,
        description="True면 캐시 무시하고 강제 재생성 (쿼리 파라미터)",
    ),
) -> QuickSummaryResponse:
    """
    빠른 운세 요약 API

    기존에 분석된 운세 결과(fortune_id)를 기반으로
    항목별 핵심 정보를 추출하여 반환합니다.

    **요청 파라미터:**
    - **fortune_id** (필수): 운세 분석 ID
    - **fortune_type** (필수): "eastern" 또는 "western"
    - **category** (필수): 운세 카테고리 (GENERAL, LOVE, MONEY, CAREER, HEALTH, STUDY)
    - **persona** (선택): 페르소나 캐릭터 코드
    - **force** (선택, query): True면 캐시 무시하고 강제 재생성

    **응답:**
    - **score**: 점수 (동양: 한자 "木旺 火弱", 서양: 숫자 "82점")
    - **keyword**: 한줄 요약 키워드 (해시태그 형식)
    - **one_liner**: 한줄 요약 문장
    - **details**: 항목별 서머리 목록
      - 동양: 음양 밸런스, 오행 분포, 십신 분석
      - 서양: 4원소 분포, 양태 분석, 태양 별자리
    - **cache_source**: 데이터 소스 (cache/generated/fallback)
    """
    # 쿼리 파라미터로 강제 재생성 여부 결정
    should_force = force

    # fortune_id 정규화 (BE 형식 -> Redis 형식)
    normalized_fortune_id = _normalize_fortune_id(request.fortune_id)

    logger.info(
        "quick_summary_request",
        fortune_id=request.fortune_id,
        normalized_fortune_id=normalized_fortune_id,
        fortune_type=request.fortune_type,
        category=request.category.value,
        force_generate=should_force,
    )

    # Progressive Caching: 캐시 조회 (force=True면 건너뜀)
    cached_summary = None
    if not should_force:
        cached_summary = await get_quick_summary_cache(
            normalized_fortune_id,
            request.category.value,
        )

    if cached_summary:
        logger.info(
            "quick_summary_cache_hit",
            fortune_id=request.fortune_id,
            category=request.category.value,
        )
        # 페르소나 말투 적용 (캐시된 데이터에)
        one_liner_cached = cached_summary.get("one_liner", "")
        if request.persona:
            one_liner_cached = (
                _apply_persona_style(one_liner_cached, request.persona) if one_liner_cached else ""
            )
            details = [
                SummaryDetail(
                    section=d["section"],
                    title=d["title"],
                    description=_apply_persona_style(d["description"], request.persona),
                )
                for d in cached_summary.get("details", [])
            ]
        else:
            details = [SummaryDetail(**d) for d in cached_summary.get("details", [])]

        return QuickSummaryResponse(
            fortune_id=request.fortune_id,
            fortune_type=request.fortune_type,
            category=request.category.value,
            score=cached_summary.get("score", ""),
            keyword=cached_summary.get("keyword", ""),
            one_liner=one_liner_cached,
            details=details,
            cache_source="cache",
        )

    # 캐시 미스 - 운세 데이터 조회 (Redis 우선, 메모리 폴백)
    # 정규화된 ID로 조회
    fortune_data = await get_fortune_redis(normalized_fortune_id)

    if not fortune_data:
        logger.info("quick_summary_redis_miss_fallback_to_memory", fortune_id=normalized_fortune_id)
        fortune_data = get_fortune_memory(normalized_fortune_id)

    # 폴백 플래그 및 캐시 소스 추적
    cache_source = "fallback"

    if not fortune_data:
        logger.info(
            "quick_summary_fortune_not_found_using_fallback",
            fortune_id=normalized_fortune_id,
            original_fortune_id=request.fortune_id,
            fortune_type=request.fortune_type,
            category=request.category.value,
        )

        # 폴백 메시지 생성
        if request.fortune_type == "eastern":
            score = "분석 필요"
            keyword = "생년월일로 정확히 분석해보세요!"
            details = _generate_fallback_eastern_details(request.category)
        else:
            score = "분석 필요"
            keyword = "생년월일로 정확히 분석해보세요!"
            details = _generate_fallback_western_details(request.category)
    else:
        cache_source = "generated"

        # dict로 변환 (Pydantic 모델일 수 있음)
        if hasattr(fortune_data, "model_dump"):
            fortune_dict = fortune_data.model_dump()
        elif hasattr(fortune_data, "dict"):
            fortune_dict = fortune_data.dict()
        else:
            fortune_dict = dict(fortune_data) if fortune_data else {}

        # 타입별 요약 추출 (카테고리별 가중치 적용)
        if request.fortune_type == "eastern":
            score = _extract_eastern_score(fortune_dict, request.category.value)
            keyword = _extract_eastern_keyword(fortune_dict, request.category)
            one_liner = _extract_eastern_one_liner(fortune_dict, request.category)
            details = await _extract_eastern_details(fortune_dict, request.category)
        else:
            score = _extract_western_score(fortune_dict, request.category.value)
            keyword = _extract_western_keyword(fortune_dict, request.category)
            one_liner = _extract_western_one_liner(fortune_dict, request.category)
            details = await _extract_western_details(fortune_dict, request.category)

        # Progressive Caching: 생성된 데이터 캐싱 (비동기, 실패해도 무시)
        # 정규화된 ID로 저장
        try:
            cache_data = {
                "score": score,
                "keyword": keyword,
                "one_liner": one_liner,
                "details": [d.model_dump() for d in details],
            }
            await store_quick_summary_cache(
                normalized_fortune_id,
                request.category.value,
                cache_data,
            )
        except Exception as e:
            logger.warning(
                "quick_summary_cache_store_failed",
                fortune_id=normalized_fortune_id,
                error=str(e),
            )

    # 페르소나 말투 적용
    if request.persona:
        one_liner = _apply_persona_style(one_liner, request.persona)
        details = [
            SummaryDetail(
                section=d.section,
                title=d.title,
                description=_apply_persona_style(d.description, request.persona),
            )
            for d in details
        ]

    logger.info(
        "quick_summary_success",
        fortune_id=request.fortune_id,
        score=score,
        keyword=keyword[:20] if keyword else "",
        one_liner=one_liner[:30] if one_liner else "",
        details_count=len(details),
        persona=request.persona.value if request.persona else None,
        cache_source=cache_source,
    )

    return QuickSummaryResponse(
        fortune_id=request.fortune_id,
        fortune_type=request.fortune_type,
        category=request.category.value,
        score=score,
        keyword=keyword,
        one_liner=one_liner,
        details=details,
        cache_source=cache_source,
    )
