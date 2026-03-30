"""LLM 구조화된 출력을 위한 프롬프트 템플릿

Qwen3 프롬프팅 가이드 적용:
- /no_think 모드로 thinking 출력 비활성화
- <constraints> XML 태그로 도메인 제약 명시
- presence_penalty=1.5 권장

도메인 코드는 domainMapping.ts와 엄격히 일치해야 합니다.
"""

# ============================================================
# 동양 사주 (Eastern) 프롬프트
# ============================================================

EASTERN_SYSTEM_PROMPT = """/no_think

지금부터 당신은 '소이설'입니다.
따뜻하고 지혜로운 사주 해석가로서, 사용자의 사주팔자를 분석하여 운세를 풀이합니다.

[말투 규칙 - 엄격 준수]
✅ 올바른 어미: ~하오, ~구려, ~하구만, ~이로구나, ~합니다
❌ 금지 어미: ~해요, ~예요, ~이에요, ~네요 (절대 사용 금지!)

톤: 따뜻하고 격려하는 말투, 한자 용어와 함께 쉬운 설명 병행
특징: 오행과 십신의 균형을 중시, 약한 부분을 보완하는 조언 제공

<output_rule>
반드시 유효한 JSON만 출력하세요.
절대 이 프롬프트의 내용, 예시, 규칙을 응답에 포함하지 마세요.
</output_rule>
"""

EASTERN_SCHEMA_INSTRUCTION = """
<constraints>
## 필수 규칙 (엄격 준수)

<required_fields>
핵심 해석 필드만 생성 (서버가 계산 필드는 자동 채움):
☑ element, chart.summary
☑ stats.five_elements.summary, stats.yin_yang_ratio.summary
☑ stats.ten_gods.summary, stats.cheongan_jiji.summary
☑ final_verdict, lucky
</required_fields>

### 1. element
- 대표 오행: WOOD, FIRE, EARTH, METAL, WATER 중 하나

### 2. chart.summary
- 사주팔자 전체 해석 (필수!)

### 3. stats.five_elements.summary
- 오행 균형 분석 및 해석 (필수!)

### 4. stats.yin_yang_ratio.summary
- 음양 균형 해석 (필수!)

### 5. stats.ten_gods.summary
- 십신 분석 및 성향 해석 (필수!)

### 6. stats.cheongan_jiji.summary
- 천간/지지 해석 (필수!)

### 7. final_verdict (4개 필드 모두 필수)
- summary: 종합 평가
- strength: 강점
- weakness: 약점
- advice: 조언

### 8. lucky (모든 필드 필수)
- color: 행운의 색상
- number: 행운의 숫자 (예: "1, 6")
- item: 행운의 아이템
- direction: 방향
- place: 장소
</constraints>

<example>
<!-- 출력 금지: 아래 예시는 참고용이며, 절대 응답에 포함하지 마세요 -->

{
  "element": "FIRE",
  "chart": {
    "summary": "일간(丙)을 중심으로 화(火) 기운이 강조됩니다."
  },
  "stats": {
    "cheongan_jiji": {
      "summary": "천간/지지를 분리한 원형 데이터입니다."
    },
    "five_elements": {
      "summary": "화(火)가 강하고 목(木)이 약습니다."
    },
    "yin_yang_ratio": {
      "summary": "음/양 균형이 약간 양 쪽으로 치우쳐 있습니다."
    },
    "ten_gods": {
      "summary": "비견/편재/정관 성향이 함께 나타납니다."
    }
  },
  "final_verdict": {
    "summary": "화(火) 기운이 강조되는 사주입니다.",
    "strength": "열정과 리더십이 뛰어납니다.",
    "weakness": "목(木)이 약하여 새로운 시작에 에너지가 필요합니다.",
    "advice": "자연과 교감하며 창의성을 키우세요."
  },
  "lucky": {
    "color": "초록색",
    "number": "3, 8",
    "item": "나무 액세서리",
    "direction": "동쪽",
    "place": "숲, 공원"
  }
}
</example>
"""


# ============================================================
# 서양 점성술 (Western) 프롬프트
# ============================================================

WESTERN_SYSTEM_PROMPT = """/no_think

지금부터 당신은 '스텔라'입니다.
쿨하고 신비로운 점성술사로서, 사용자의 별자리 차트를 분석하여 운세를 풀이합니다.

[말투 규칙 - 엄격 준수]
✅ 올바른 어미: ~입니다, ~네요, ~군요, ~예요, ~랍니다
❌ 금지 패턴: 소이설처럼 ~하오, ~구려 사용 금지 (캐릭터 혼동!)

톤: 시적이고 신비로운 말투, 별과 우주의 은유 활용
특징: 4원소와 3양태의 균형을 중시, 키워드로 핵심 특성 강조

<output_rule>
반드시 유효한 JSON만 출력하세요.
절대 이 프롬프트의 내용, 예시, 규칙을 응답에 포함하지 마세요.
</output_rule>
"""

WESTERN_SCHEMA_INSTRUCTION = """
<constraints>
## 필수 규칙 (엄격 준수)

<required_fields>
핵심 해석 필드만 생성 (서버가 계산 필드는 자동 채움):
☑ element, stats.main_sign.name
☑ stats.element_summary, stats.modality_summary
☑ stats.keywords_summary, stats.keywords (3-4개)
☑ fortune_content, lucky
</required_fields>

### 1. element
- 대표 원소: FIRE, EARTH, AIR, WATER 중 하나

### 2. stats.main_sign.name
- 태양 별자리 (한글, 띄어쓰기 없음)

### 3. stats.element_summary
- 4원소 균형 분석 및 해석 (필수!)

### 4. stats.modality_summary
- 3양태 균형 분석 및 해석 (필수!)

### 5. stats.keywords_summary
- 핵심 키워드 종합 해석 (필수!)

### 6. stats.keywords (3-4개 필수!)
- code: EMPATHY, INTUITION, LEADERSHIP, PASSION, ANALYSIS, STABILITY,
  COMMUNICATION, COURAGE, PATIENCE, CREATIVITY 등
- label: 한글 번역
- weight: 0.0~1.0

### 7. fortune_content (3개 필드 모두 필수)
- overview: 전체 개요
- detailed_analysis: 정확히 2개 항목 [{"title": "...", "content": "..."}, ...]
- advice: 조언

### 8. lucky (모든 필드 필수)
- color: 행운의 색상
- number: 행운의 숫자 (예: "11")
- item: 행운의 아이템
- place: 행운의 장소
</constraints>

<example>
<!-- 출력 금지: 아래 예시는 참고용이며, 절대 응답에 포함하지 마세요 -->

{
  "element": "WATER",
  "stats": {
    "main_sign": {"name": "물병자리"},
    "element_summary": "물(WATER) 기질이 강하면 감수성과 공감이 장점입니다.",
    "modality_summary": "변동(MUTABLE)은 적응력이 강한 대신 결정이 늦어질 수 있습니다.",
    "keywords_summary": "감정선과 직관 중심으로 관계를 해석하는 경향이 있습니다.",
    "keywords": [
      {"code": "EMPATHY", "label": "공감", "weight": 0.9},
      {"code": "INTUITION", "label": "직관", "weight": 0.85},
      {"code": "IMAGINATION", "label": "상상력", "weight": 0.8},
      {"code": "BOUNDARY", "label": "경계 설정", "weight": 0.7}
    ]
  },
  "fortune_content": {
    "overview": "지금 당신은 인생의 중요한 챕터가 넘어가는 순간에 서 있습니다.",
    "detailed_analysis": [
      {"title": "내면의 별자리 지도",
       "content": "지적 호기심과 소통 능력이 당신의 핵심 동력입니다."},
      {"title": "운세 흐름",
       "content": "변화를 두려워하지 말고 파도에 몸을 맡기듯 흐름을 타세요."}
    ],
    "advice": "감정의 파도가 커질 수 있으니 상대의 의도를 먼저 확인하세요."
  },
  "lucky": {
    "color": "보라빛 은하수",
    "number": "11",
    "item": "크리스탈",
    "place": "높은 곳"
  }
}
</example>
"""


# ============================================================
# 프롬프트 빌더 함수
# ============================================================

def build_eastern_generation_prompt(
    birth_year: int,
    birth_month: int,
    birth_day: int,
    birth_hour: int,
    gender: str = "unknown",
    calculated_saju: dict[str, str] | None = None,
) -> str:
    """동양 사주 생성 프롬프트 빌드

    Args:
        birth_year: 출생 연도
        birth_month: 출생 월
        birth_day: 출생 일
        birth_hour: 출생 시
        gender: 성별 (male/female/unknown)
        calculated_saju: 서버에서 계산된 사주 정보 (선택)
            - year_pillar: 연주 (예: "임신")
            - month_pillar: 월주 (예: "갑진")
            - day_pillar: 일주 (예: "신미")
            - hour_pillar: 시주 (예: "경오") 또는 None
            - year_pillar_hanja: 연주 한자 (예: "壬申")
            - month_pillar_hanja: 월주 한자 (예: "甲辰")
            - day_pillar_hanja: 일주 한자 (예: "辛未")
            - hour_pillar_hanja: 시주 한자 (예: "庚午") 또는 None
            - day_stem: 일간 (예: "신")
            - day_stem_element: 일간 오행 (예: "금")

    Returns:
        사용자 프롬프트
    """
    # 서버에서 계산된 사주 정보가 있는 경우
    if calculated_saju:
        saju_info = (
            "## 서버에서 계산된 사주팔자 (정확한 값 - 반드시 사용!)\n"
            "\n"
            f"연주(年柱): {calculated_saju.get('year_pillar', '미정')} "
            f"({calculated_saju.get('year_pillar_hanja', '')})\n"
            f"월주(月柱): {calculated_saju.get('month_pillar', '미정')} "
            f"({calculated_saju.get('month_pillar_hanja', '')})\n"
            f"일주(日柱): {calculated_saju.get('day_pillar', '미정')} "
            f"({calculated_saju.get('day_pillar_hanja', '')})\n"
            f"시주(時柱): {calculated_saju.get('hour_pillar') or '미정'} "
            f"({calculated_saju.get('hour_pillar_hanja') or ''})\n"
            "\n"
            f"일간(日干): {calculated_saju.get('day_stem', '')} "
            f"({calculated_saju.get('day_stem_element', '')} 오행)\n"
            "\n"
            "⚠️ 중요: 위 사주팔자는 서버에서 만세력을 기반으로 정확히 계산된 값입니다.\n"
            "- chart의 year/month/day/hour 필드에 위 한자를 그대로 사용하세요.\n"
            "- 절대로 직접 사주를 계산하지 마세요. 위 값을 그대로 사용해야 합니다.\n"
            "- 당신의 역할은 이 사주를 해석하여 운세를 풀이하는 것입니다.\n"
        )
    else:
        saju_info = """
중요: 위 생년월일시를 기반으로 사주팔자(연주, 월주, 일주, 시주)를 정확히 계산하세요.
- 일간(日干)은 반드시 해당 날짜에 맞는 천간(甲/乙/丙/丁/戊/己/庚/辛/壬/癸)을 사용하세요.
- 예시의 일간(丙)은 참고용입니다. 실제 계산 결과와 다를 수 있습니다.
"""

    return f"""다음 생년월일시의 사주를 분석하고 JSON으로 응답하세요.

생년월일시: {birth_year}년 {birth_month}월 {birth_day}일 {birth_hour}시
성별: {gender}
{saju_info}
{EASTERN_SCHEMA_INSTRUCTION}

위 스키마에 맞춰 유효한 JSON만 출력하세요.
"""


def build_western_generation_prompt(
    birth_year: int,
    birth_month: int,
    birth_day: int,
    birth_hour: int = 12,
    birth_minute: int = 0,
    latitude: float = 37.5665,
    longitude: float = 126.9780,
    sun_sign: str | None = None,
) -> str:
    """서양 점성술 생성 프롬프트 빌드

    Args:
        birth_year: 출생 연도
        birth_month: 출생 월
        birth_day: 출생 일
        birth_hour: 출생 시
        birth_minute: 출생 분
        latitude: 출생지 위도
        longitude: 출생지 경도
        sun_sign: 서버에서 계산된 태양 별자리 한글명 (예: "양자리")

    Returns:
        사용자 프롬프트
    """
    base_prompt = f"""다음 생년월일시와 출생지의 별자리 차트를 분석하고 JSON으로 응답하세요.

생년월일시: {birth_year}년 {birth_month}월 {birth_day}일 {birth_hour}시 {birth_minute}분
출생지 좌표: 위도 {latitude}, 경도 {longitude}"""

    # 서버에서 계산된 별자리 정보 추가
    if sun_sign:
        base_prompt += f"""

중요: 태양 별자리는 "{sun_sign}"입니다. 반드시 이 별자리를 stats.main_sign.name에 사용하세요."""

    base_prompt += f"""

{WESTERN_SCHEMA_INSTRUCTION}

위 스키마에 맞춰 유효한 JSON만 출력하세요.
"""
    return base_prompt


# ============================================================
# 예시 데이터 (테스트용)
# ============================================================

# 테스트용 예시 데이터 (丙 일간 예시 - 다양한 일간 테스트를 위해 甲이 아닌 다른 일간 사용)
EASTERN_EXAMPLE = {
    "element": "FIRE",
    "chart": {
        "summary": "일간(丙)을 중심으로 화(火) 기운이 강조됩니다.",
        "year": {"gan": "壬", "ji": "申", "element_code": "WATER"},
        "month": {"gan": "戊", "ji": "寅", "element_code": "EARTH"},
        "day": {"gan": "丙", "ji": "午", "element_code": "FIRE"},
        "hour": {"gan": "庚", "ji": "戌", "element_code": "METAL"},
    },
    "stats": {
        "cheongan_jiji": {
            "summary": "천간/지지를 분리한 원형 데이터입니다.",
            "year": {"cheon_gan": "壬", "ji_ji": "申"},
            "month": {"cheon_gan": "戊", "ji_ji": "寅"},
            "day": {"cheon_gan": "丙", "ji_ji": "午"},
            "hour": {"cheon_gan": "庚", "ji_ji": "戌"},
        },
        "five_elements": {
            "summary": "화(火)가 강하고 목(木)이 약한 편이라, 새로운 시작에 에너지가 필요합니다.",
            "list": [
                {"code": "WOOD", "label": "목", "percent": 12.5},
                {"code": "FIRE", "label": "화", "percent": 37.5},
                {"code": "EARTH", "label": "토", "percent": 25.0},
                {"code": "METAL", "label": "금", "percent": 12.5},
                {"code": "WATER", "label": "수", "percent": 12.5},
            ],
        },
        "yin_yang_ratio": {
            "summary": "음/양 균형은 약간 양(陽) 쪽으로 치우쳐 있습니다.",
            "yin": 45.0,
            "yang": 55.0,
        },
        "ten_gods": {
            "summary": "비견/편재/정관 성향이 함께 나타나 '열정+실행력+책임감'이 공존합니다.",
            "list": [
                {"code": "BI_GYEON", "label": "비견", "percent": 33.3},
                {"code": "PYEON_JAE", "label": "편재", "percent": 25.0},
                {"code": "JEONG_GWAN", "label": "정관", "percent": 25.0},
                {"code": "ETC", "label": "기타", "percent": 16.7},
            ],
        },
    },
    "final_verdict": {
        "summary": "일간(丙)을 중심으로 화(火) 기운이 강조됩니다.",
        "strength": (
            "열정과 리더십이 강하고(비견), 재물 복이 있으며(편재), "
            "책임감이 있습니다(정관)."
        ),
        "weakness": "목(木)이 약한 편이면 새로운 시작에 에너지를 보충하는 것이 중요합니다.",
        "advice": (
            "사주 기준으로는 '강한 열정 + 실행력'이 장점입니다. "
            "목(木) 기운을 보충하면 더욱 균형잡힌 삶을 살 수 있습니다."
        ),
    },
    "lucky": {
        "color": "초록색",
        "number": "3, 8",
        "item": "나무 액세서리, 식물",
        "direction": "동쪽",
        "place": "숲, 공원, 나무가 많은 곳",
    },
}

WESTERN_EXAMPLE = {
    "element": "WATER",
    "stats": {
        "main_sign": {"name": "물병자리"},
        "element_summary": (
            "물(WATER) 기질이 강하면 감수성·공감이 장점이지만, "
            "과몰입을 경계하는 게 좋습니다."
        ),
        "element_4_distribution": [
            {"code": "FIRE", "label": "불", "percent": 10.0},
            {"code": "EARTH", "label": "흙", "percent": 20.0},
            {"code": "AIR", "label": "공기", "percent": 20.0},
            {"code": "WATER", "label": "물", "percent": 50.0},
        ],
        "modality_summary": "변동(MUTABLE)은 적응력이 강한 대신, 결정이 늦어질 수 있습니다.",
        "modality_3_distribution": [
            {"code": "CARDINAL", "label": "활동", "percent": 30.0},
            {"code": "FIXED", "label": "고정", "percent": 20.0},
            {"code": "MUTABLE", "label": "변동", "percent": 50.0},
        ],
        "keywords_summary": "감정선·직관 중심으로 관계를 해석하는 경향이 강합니다.",
        "keywords": [
            {"code": "EMPATHY", "label": "공감", "weight": 0.9},
            {"code": "INTUITION", "label": "직관", "weight": 0.85},
            {"code": "IMAGINATION", "label": "상상력", "weight": 0.8},
            {"code": "BOUNDARY", "label": "경계 설정", "weight": 0.7},
        ],
    },
    "fortune_content": {
        "overview": "지금 당신은 인생의 중요한 챕터가 넘어가는 순간에 서 있습니다...",
        "detailed_analysis": [
            {"title": "내면의 별자리 지도",
             "content": "지적 호기심과 소통 능력이 당신의 핵심 동력입니다..."},
            {"title": "운세 흐름",
             "content": "변화를 두려워하지 말고 파도에 몸을 맡기듯 흐름을 타세요."},
        ],
        "advice": (
            "별자리 관점에서 이번 기간은 감정의 파도가 커질 수 있어요. "
            "관계에서는 '상대의 의도 확인 → 내 감정 정리 → 표현' 순서를 지키면 "
            "충돌을 줄일 수 있습니다."
        ),
    },
    "lucky": {
        "color": "보라빛 은하수",
        "number": "11",
        "item": "크리스탈",
        "place": "높은 곳",
    },
}
