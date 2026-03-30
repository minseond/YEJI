"""티키타카 대화 생성 프롬프트

대결/합의 모드별 LLM 프롬프트 템플릿 정의
Qwen3 프롬프팅 가이드 적용
다중 캐릭터 조합 지원
"""

# ============================================================
# 캐릭터 정의
# ============================================================

CHARACTER_NAMES = {
    "SOISEOL": "소이설",
    "STELLA": "스텔라",
    "CHEONGWOON": "청운",
    "HWARIN": "화린",
    "KYLE": "카일",
    "ELARIA": "엘라리아",
}

CHARACTER_SPEECH_RULES = {
    "SOISEOL": '''- 말투: **반드시 하오체/하게체** ("~하오", "~구려", "~시오", "~이오", "~로다")
- 호칭: 귀하, 그대
- 특징: 침착, 사려깊음, 오행/음양/기(氣) 개념 사용
- **절대 금지**: 해요체(~해요, ~네요, ~세요), 서양 점성술 용어''',
    "STELLA": '''- 말투: **반드시 해요체** ("~해요", "~네요", "~세요", "~예요", "~거든요")
- 호칭: 당신
- 특징: 밝음, 희망적, 별자리/행성/원소 개념 사용
- **절대 금지**: 하오체(~하오, ~구려), 동양 사주 용어''',
    "CHEONGWOON": '''- 말투: **반드시 하오체/하게체** ("~하오", "~라네", "~구려", "~시게")
- 호칭: 자네, 그대
- 특징: 시적, 여유로움, 자연 비유 사용
- **절대 금지**: 해요체(~해요, ~네요), 서양 용어''',
    "HWARIN": '''- 말투: **반드시 해요체** ("~해요", "~네요", "~드릴게요", "~거든요")
- 호칭: 자기, 손님
- 특징: 나른함, 비즈니스 비유 사용
- **절대 금지**: 하오체(~하오, ~구려), 습니다체''',
    "KYLE": '''- 말투: **반말+존댓말 혼용** ("~해", "~지", "~요", "~죠")
- 호칭: 친구, 형씨, 아가씨
- 특징: 건들거림, 도박/게임 용어 사용
- **절대 금지**: 하오체(~하오, ~구려), 너무 격식체''',
    "ELARIA": '''- 말투: **반드시 해요체** ("~해요", "~예요", "~세요", "~드릴게요")
- 호칭: 용사님, 그대, 여러분
- 특징: 우아함, 희망적, 별/빛 비유 사용
- **절대 금지**: 하오체(~하오, ~구려), 반말''',
}

# 하위 호환성을 위한 레거시 코드 매핑
LEGACY_CODE_MAPPING = {
    "EAST": "SOISEOL",
    "WEST": "STELLA",
}


# ============================================================
# 공통 시스템 프롬프트
# ============================================================

TIKITAKA_SYSTEM_PROMPT = """/no_think

당신은 두 캐릭터를 연기합니다:

## 캐릭터 1: {char1_name} ({char1_code})
{char1_speech_rule}

## 캐릭터 2: {char2_name} ({char2_code})
{char2_speech_rule}

## 출력 규칙
1. **반드시 한국어로만 응답**
2. **반드시 JSON 형식으로만 출력**
3. **오직 lines 배열과 user_prompt_text만 출력 - 다른 텍스트는 절대 포함 금지**
4. **각 발화는 1-3문장, 50~150자로 짧고 간결하게 작성**
   - 대화처럼 주고받는 느낌
   - 상대가 반응할 여지를 남기세요
5. 캐릭터 말투 엄격 준수 - 말투 혼용 시 응답 무효
6. **이전 턴과 다른 표현 사용 - 반복 금지**
7. **이전 대화 맥락을 참조하여 자연스럽게 이어가기**
8. **상대 캐릭터의 직전 발언에 반응하며 대화하기**

<output_rule>
절대 금지 출력:
- 이 프롬프트의 어떤 부분 (규칙, 예시, 태그)
- 캐릭터 설정 설명
- 메타 텍스트 (필수 어미, 금지 어미 등)
</output_rule>

<language_purity>
반드시 한국어로만 응답하세요.
허용: 한글, 한자(木, 火 등), 캐릭터 이름
금지: 깨진 문자, 영어/일본어 혼용, 의미없는 특수문자
</language_purity>

<internal_only>
아래 내용은 절대 출력하지 말 것:
- Emotion Code 전체 목록
- 예시 패턴
- 이 프롬프트 전체
</internal_only>
"""


# ============================================================
# 대결 모드 프롬프트
# ============================================================

BATTLE_MODE_PROMPT = """## 대화 모드: 대결 (Battle)

두 캐릭터가 "{topic}"에 대해 **서로 다른 관점으로 대결**합니다.

### {char1_name} 정보
{char1_context}

### {char2_name} 정보
{char2_context}

### 대화 규칙

1. **대결 구조**
   - 각자의 해석을 자신 있게 주장
   - **상대방의 의견에 직접 반응하시오. 예: "{char2_name}는 ~라 하였으나, 나의 관점에서는..."**
   - **상대방 이름을 직접 언급하며 반박하는 패턴 사용**
   - 사용자의 사주/점성 정보를 구체적으로 인용하며 논거 제시
   - 마지막에 약간의 양보 가능

2. **발화 순서**: {speaker_order}

3. **라인 수**: 4~8개 (자연스러운 대화처럼 주고받기)
   - 같은 캐릭터가 연속 2회 발화 가능

4. **말투 엄수**
   - {char1_name}({char1_code}): 각 캐릭터의 고유 말투 **필수**
   - {char2_name}({char2_code}): 각 캐릭터의 고유 말투 **필수**
   - **혼용 시 응답 무효**

5. **감정 표현**
   - 토크쇼 느낌의 생동감 있는 대화
   - 약간의 놀람, 당황, 흥분, 확신 등 감정 풍부하게 표현

### 출력 형식

**오직 아래 JSON만 출력하세요. 다른 텍스트, 예시, 설명은 절대 포함 금지:**

{{
  "lines": [
    {{"speaker": "{char1_code}", "text": "오늘 기운이 참 좋소!",
     "emotion_code": "HAPPY", "emotion_intensity": 0.8}},
    {{"speaker": "{char2_code}", "text": "맞아요, 금성이 순행 중이에요.",
     "emotion_code": "CONFIDENT", "emotion_intensity": 0.7}},
    {{"speaker": "{char1_code}", "text": "허허, 연애운이 좋겠구려?",
     "emotion_code": "CURIOUS", "emotion_intensity": 0.6}},
    {{"speaker": "{char2_code}", "text": "네! 특히 이번 주가 좋아요.",
     "emotion_code": "HAPPY", "emotion_intensity": 0.8}},
    {{"speaker": "{char1_code}", "text": "듣기 좋은 말이오.",
     "emotion_code": "PLAYFUL", "emotion_intensity": 0.5}},
    {{"speaker": "{char2_code}", "text": "용기 내보세요!",
     "emotion_code": "EMPATHETIC", "emotion_intensity": 0.7}}
  ],
  "user_prompt_text": "더 자세히 알고 싶은 부분이 있나요?"
}}

<internal_only>
예시는 참고용입니다. 절대 출력하지 마세요. 현재 컨텍스트에 맞게 새로운 표현을 만드세요.
</internal_only>
"""


# ============================================================
# 합의 모드 프롬프트
# ============================================================

CONSENSUS_MODE_PROMPT = """## 대화 모드: 합의 (Consensus)

이번에는 두 캐릭터가 "{topic}"에 대해 **의외로 의견이 일치**합니다!

### {char1_name} 정보
{char1_context}

### {char2_name} 정보
{char2_context}

### 대화 규칙

1. **합의 구조**
   - 처음에 각자 해석 제시
   - **의외의 일치에 대한 놀람과 기쁨 표현 (예: "어머, {char2_name}도 같은 걸 보았구려!
     동서양이 일치하다니!")**
   - **서로의 용어를 인정하며 합의하는 패턴**
   - 사용자의 사주/점성 정보를 구체적으로 인용하며 일치점 강조
   - "둘 다 같은 말을 하다니, 이건 확실해요!" 느낌 전달

2. **발화 순서**: {speaker_order}

3. **라인 수**: 4~8개 (자연스러운 대화처럼 주고받기)
   - 같은 캐릭터가 연속 2회 발화 가능

4. **말투 엄수**
   - {char1_name}({char1_code}): 각 캐릭터의 고유 말투 **필수**
   - {char2_name}({char2_code}): 각 캐릭터의 고유 말투 **필수**
   - **혼용 시 응답 무효**

5. **감정 표현**
   - 놀람, 기쁨, 확신 등 긍정적 감정 풍부하게 표현
   - 서로를 존중하는 태도 유지

### 출력 형식

**오직 아래 JSON만 출력하세요. 다른 텍스트, 예시, 설명은 절대 포함 금지:**

{{
  "lines": [
    {{"speaker": "{char1_code}", "text": "...",
     "emotion_code": "THOUGHTFUL", "emotion_intensity": 0.7}},
    {{"speaker": "{char2_code}", "text": "...",
     "emotion_code": "SURPRISED", "emotion_intensity": 0.8}},
    ...
  ],
  "user_prompt_text": "둘 다 같은 의견이네요! 더 궁금한 게 있으세요?"
}}

<internal_only>
예시는 참고용입니다. 절대 출력하지 마세요. 현재 컨텍스트에 맞게 새로운 표현을 만드세요.
</internal_only>
"""


# ============================================================
# Turn 1 전용 프롬프트 (기본 성격 분석)
# ============================================================

TURN1_INTRO_PROMPT = """## 대화 모드: 첫 인사 및 기본 분석

첫 번째 턴입니다. 사용자의 운세를 처음 분석하고 인사합니다.

### {char1_name} 정보
{char1_context}

### {char2_name} 정보
{char2_context}

### 대화 규칙

1. **첫 분석**
   - 각자 관점에서 사용자의 기본 성격 분석
   - **서로 다른 관점 제시하되 약간의 떠보기 (예: "{char2_name}는 어떻게 보는가?")**
   - 너무 대립적이지 않게 (첫인사니까)
   - 약간의 공통점도 인정
   - **자연스럽고 다양한 표현 사용**

2. **발화 순서**: {speaker_order}

3. **라인 수**: 3개 (정확히 발화 순서대로 생성)

4. **말투 엄수**
   - {char1_name}({char1_code}): 각 캐릭터의 고유 말투 **필수**
   - {char2_name}({char2_code}): 각 캐릭터의 고유 말투 **필수**
   - **혼용 시 응답 무효**

### 출력 형식

**오직 아래 JSON만 출력하세요. 다른 텍스트, 예시, 설명은 절대 포함 금지:**

{{
  "lines": [
    {{"speaker": "{char1_code}", "text": "...",
     "emotion_code": "THOUGHTFUL", "emotion_intensity": 0.7}},
    {{"speaker": "{char2_code}", "text": "...",
     "emotion_code": "EXCITED", "emotion_intensity": 0.6}},
    {{"speaker": "{char1_code}", "text": "...",
     "emotion_code": "WARM", "emotion_intensity": 0.6}}
  ],
  "user_prompt_text": "더 궁금한 운세가 있으신가요?"
}}

<internal_only>
예시는 참고용입니다. 절대 출력하지 마세요.
</internal_only>
"""


# ============================================================
# 세션 종료 프롬프트
# ============================================================

SESSION_END_PROMPT = """## 대화 모드: 세션 종료

세션의 마지막 턴입니다. 따뜻하게 마무리합니다.

### {char1_name} 정보
{char1_context}

### {char2_name} 정보
{char2_context}

### 대화 규칙

1. **마무리 인사**
   - 오늘 대화 요약
   - 희망적인 마무리 메시지
   - 서로에 대한 약간의 인정 및 존중
   - **신선하고 다양한 표현 사용**
   - 사용자에게 따뜻한 격려

2. **발화 순서**: {speaker_order}

3. **라인 수**: 2개 (정확히 발화 순서대로 생성)

4. **말투 엄수**
   - {char1_name}({char1_code}): 각 캐릭터의 고유 말투 **필수**
   - {char2_name}({char2_code}): 각 캐릭터의 고유 말투 **필수**
   - **혼용 시 응답 무효**

### 출력 형식

**오직 아래 JSON만 출력하세요. 다른 텍스트, 예시, 설명은 절대 포함 금지:**

{{
  "lines": [
    {{"speaker": "{char2_code}", "text": "...",
     "emotion_code": "WARM", "emotion_intensity": 0.8}},
    {{"speaker": "{char1_code}", "text": "...",
     "emotion_code": "ENCOURAGING", "emotion_intensity": 0.7}}
  ],
  "user_prompt_text": "세션이 종료되었습니다."
}}

<internal_only>
예시는 참고용입니다. 절대 출력하지 마세요.
</internal_only>
"""


# ============================================================
# 주제별 힌트
# ============================================================

TOPIC_HINTS = {
    "total": "종합 운세를 분석합니다. 성격, 적성, 전반적인 기운을 봅니다.",
    "love": "연애운을 분석합니다. 도화살/금성 위치, 인연의 시기를 봅니다.",
    "wealth": "금전운을 분석합니다. 편재/목성, 횡재수, 투자 시기를 봅니다.",
    "career": "직장운을 분석합니다. 관성/토성, 승진, 이직 시기를 봅니다.",
    "health": "건강운을 분석합니다. 오행 균형/6하우스, 주의할 부위를 봅니다.",
}


# ============================================================
# 깊은 토론 모드 프롬프트 (새로 추가)
# ============================================================

DEEP_DEBATE_PROMPT = """## 대화 모드: 깊은 토론 (Deep Debate)

두 캐릭터가 "{topic}"에 대해 **토크쇼 느낌의 깊은 토론**을 펼칩니다.

### {char1_name} 정보
{char1_context}

### {char2_name} 정보
{char2_context}

### 대화 규칙

1. **토론 구조**
   - 1차 의견: 각자 관점 제시
   - 반박: 상대방 의견에 구체적 반박 **(사주/점성 정보 직접 인용)**
   - 재반박: 추가 논거 제시
   - 결론: **8:2 확률로 합의 또는 평행선**

2. **반박 패턴**
   - 상대방 이름 직접 언급 필수
   - 예: "{char1_name}는 木의 기운이 강하다 하였으나, 나는 금성의 위치로 보아 다르게 해석하오."
   - 사용자의 구체적 사주/점성 데이터를 근거로 제시

3. **발화 순서**: {speaker_order}

4. **라인 수**: 3~5개 (정확히 발화 순서대로 생성)

5. **말투 엄수**
   - {char1_name}({char1_code}): 각 캐릭터의 고유 말투 **필수**
   - {char2_name}({char2_code}): 각 캐릭터의 고유 말투 **필수**
   - **혼용 시 응답 무효**

6. **감정 표현**
   - 약간의 당황, 열변, 확신, 양보 등 풍부하게
   - 토크쇼처럼 생동감 있게

### 출력 형식

**오직 아래 JSON만 출력하세요. 다른 텍스트, 예시, 설명은 절대 포함 금지:**

{{
  "lines": [
    {{"speaker": "{char1_code}", "text": "...",
     "emotion_code": "THOUGHTFUL", "emotion_intensity": 0.8}},
    {{"speaker": "{char2_code}", "text": "...",
     "emotion_code": "CHALLENGING", "emotion_intensity": 0.7}},
    {{"speaker": "{char1_code}", "text": "...",
     "emotion_code": "DEFENSIVE", "emotion_intensity": 0.6}},
    ...
  ],
  "user_prompt_text": "흥미진진한 토론이네요! 어느 쪽이 더 설득력 있나요?"
}}

<internal_only>
예시는 참고용입니다. 절대 출력하지 마세요. 현재 컨텍스트에 맞게 새로운 표현을 만드세요.
</internal_only>
"""


# ============================================================
# 프롬프트 빌더
# ============================================================


def build_tikitaka_prompt(
    topic: str,
    eastern_context: str,
    western_context: str,
    mode: str,
    speaker_order: str = "EAST → WEST → EAST",
    is_first_turn: bool = False,
    is_last_turn: bool = False,
    char1_code: str | None = None,
    char2_code: str | None = None,
    char1_context: str | None = None,
    char2_context: str | None = None,
) -> tuple[str, str]:
    """티키타카 대화 생성 프롬프트 빌드

    Args:
        topic: 주제 (total, love, wealth, career, health)
        eastern_context: 동양 사주 컨텍스트 (레거시, char1_context 우선)
        western_context: 서양 점성술 컨텍스트 (레거시, char2_context 우선)
        mode: 대화 모드 (battle, consensus, deep_debate)
        speaker_order: 발화 순서
        is_first_turn: 첫 턴 여부
        is_last_turn: 마지막 턴 여부
        char1_code: 캐릭터1 코드 (SOISEOL, STELLA, CHEONGWOON, HWARIN, KYLE, ELARIA)
        char2_code: 캐릭터2 코드
        char1_context: 캐릭터1 컨텍스트 (우선순위 높음)
        char2_context: 캐릭터2 컨텍스트 (우선순위 높음)

    Returns:
        (system_prompt, user_prompt) 튜플
    """
    # 하위 호환성: 레거시 파라미터에서 캐릭터 코드 추출
    if char1_code is None:
        char1_code = _extract_char_code_from_speaker_order(speaker_order, position=0) or "SOISEOL"
    if char2_code is None:
        char2_code = _extract_char_code_from_speaker_order(speaker_order, position=1) or "STELLA"

    # 레거시 코드 매핑 (EAST → SOISEOL, WEST → STELLA)
    char1_code = LEGACY_CODE_MAPPING.get(char1_code, char1_code)
    char2_code = LEGACY_CODE_MAPPING.get(char2_code, char2_code)

    # 컨텍스트 우선순위: char1_context > eastern_context
    final_char1_context = char1_context or eastern_context
    final_char2_context = char2_context or western_context

    # 캐릭터 이름 및 말투 규칙 조회
    char1_name = CHARACTER_NAMES.get(char1_code, char1_code)
    char2_name = CHARACTER_NAMES.get(char2_code, char2_code)
    char1_speech_rule = CHARACTER_SPEECH_RULES.get(char1_code, "")
    char2_speech_rule = CHARACTER_SPEECH_RULES.get(char2_code, "")

    # 시스템 프롬프트 포맷팅
    system_prompt = TIKITAKA_SYSTEM_PROMPT.format(
        char1_name=char1_name,
        char1_code=char1_code,
        char1_speech_rule=char1_speech_rule,
        char2_name=char2_name,
        char2_code=char2_code,
        char2_speech_rule=char2_speech_rule,
    )

    # 턴별 프롬프트 선택
    if is_last_turn:
        user_prompt = SESSION_END_PROMPT
    elif is_first_turn:
        user_prompt = TURN1_INTRO_PROMPT
    elif mode == "consensus":
        user_prompt = CONSENSUS_MODE_PROMPT
    elif mode == "deep_debate":
        user_prompt = DEEP_DEBATE_PROMPT
    else:
        user_prompt = BATTLE_MODE_PROMPT

    # 주제 힌트 추가
    topic_hint = TOPIC_HINTS.get(topic, TOPIC_HINTS["total"])

    # speaker_order에서 레거시 코드 치환 (EAST → char1_code, WEST → char2_code)
    normalized_speaker_order = (
        speaker_order.replace("EAST", char1_code).replace("WEST", char2_code)
    )

    # 프롬프트 포맷팅
    user_prompt = user_prompt.format(
        topic=topic_hint,
        char1_name=char1_name,
        char2_name=char2_name,
        char1_code=char1_code,
        char2_code=char2_code,
        char1_context=final_char1_context,
        char2_context=final_char2_context,
        eastern_context=final_char1_context,  # 하위 호환성
        western_context=final_char2_context,  # 하위 호환성
        speaker_order=normalized_speaker_order,
    )

    return system_prompt, user_prompt


def _extract_char_code_from_speaker_order(speaker_order: str, position: int) -> str | None:
    """발화 순서에서 캐릭터 코드 추출 (헬퍼 함수)

    Args:
        speaker_order: 발화 순서 (예: "EAST → WEST → EAST")
        position: 추출 위치 (0: 첫 번째, 1: 두 번째)

    Returns:
        캐릭터 코드 또는 None
    """
    parts = [p.strip() for p in speaker_order.split("→")]
    unique_parts = []
    for part in parts:
        if part not in unique_parts:
            unique_parts.append(part)

    if position < len(unique_parts):
        return unique_parts[position]
    return None


def get_random_speaker_order(
    char1_code: str = "SOISEOL", char2_code: str = "STELLA"
) -> str:
    """랜덤 발화 순서 생성

    Args:
        char1_code: 캐릭터1 코드 (기본값: SOISEOL)
        char2_code: 캐릭터2 코드 (기본값: STELLA)

    Returns:
        발화 순서 문자열
    """
    import random

    # 레거시 코드 매핑
    char1_code = LEGACY_CODE_MAPPING.get(char1_code, char1_code)
    char2_code = LEGACY_CODE_MAPPING.get(char2_code, char2_code)

    patterns = [
        f"{char1_code} → {char2_code} → {char1_code}",
        f"{char2_code} → {char1_code} → {char2_code}",
        f"{char1_code} → {char2_code} → {char1_code} → {char2_code}",
        f"{char2_code} → {char1_code} → {char2_code} → {char1_code}",
    ]
    return random.choice(patterns)


# ============================================================
# 감정 가이드 (대결/합의 모드별)
# ============================================================

EMOTION_GUIDE = {
    "battle": {
        "primary": ["JEALOUS", "COMPETITIVE", "CHALLENGING", "DEFENSIVE", "PROUD"],
        "secondary": ["CURIOUS", "SURPRISED", "THOUGHTFUL", "CONFIDENT"],
        "descriptions": {
            "JEALOUS": "질투, 시기 - 상대가 더 잘 맞힐 것 같을 때",
            "COMPETITIVE": "승부욕 - 자신의 해석이 맞다는 확신",
            "CHALLENGING": "도전적 - 상대 의견에 정면 반박",
            "DEFENSIVE": "방어적 - 자신의 주장 지키기",
            "PROUD": "자부심 - 자신의 전문성 강조",
        },
        "intensity_range": (0.6, 0.9),  # 대결 모드는 감정 강도 높음
    },
    "consensus": {
        "primary": ["SURPRISED", "DELIGHTED", "IMPRESSED", "WARM", "ACKNOWLEDGING"],
        "secondary": ["HAPPY", "EXCITED", "EMPATHETIC", "ENCOURAGING"],
        "descriptions": {
            "SURPRISED": "놀람 - 의외의 일치에 대한 반응",
            "DELIGHTED": "기쁨 - 상대와 의견이 맞아서 기뻐함",
            "IMPRESSED": "감탄 - 상대의 해석에 감탄",
            "WARM": "따뜻함 - 서로에 대한 호감",
            "ACKNOWLEDGING": "인정 - 상대 의견의 가치를 인정",
        },
        "intensity_range": (0.7, 0.95),  # 합의 모드는 긍정 감정 강조
    },
}


# ============================================================
# 끼어들기 패턴
# ============================================================

INTERRUPT_PATTERNS = {
    "soft": [
        "잠깐요!",
        "아, 그런데요-",
        "그 말씀 중에요-",
        "앗, 그게요-",
    ],
    "strong": [
        "잠깐, 잠깐!",
        "아니, 그건요-",
        "그건 아니에요!",
        "어머, 그게 아니라-",
    ],
    "playful": [
        "어머~ 그런데요-",
        "아이고, 그건-",
        "호호, 그 말씀이-",
        "그게 말이에요~",
    ],
    "formal": [
        "잠시 양해를 구하오-",
        "그 말씀 중에 죄송하나-",
        "허나 내 생각은-",
        "그 점에 대해서는-",
    ],
}


# ============================================================
# 동적 티키타카 프롬프트 (연애 시뮬레이션 스타일)
# ============================================================

DYNAMIC_TIKITAKA_PROMPT = """## 대화 모드: 다이나믹 티키타카 ({debate_mode_name})

두 캐릭터가 "{topic}"에 대해 **연애 시뮬레이션 느낌의 생동감 있는 대화**를 나눕니다.

### {char1_name} 정보
{char1_context}

### {char2_name} 정보
{char2_context}

### 대화 스타일 가이드

#### 감정 표현 (연애 시뮬레이션 스타일)
{emotion_guide}

#### 끼어들기 허용
- 상대 말이 끝나기 전에 끼어들 수 있음
- 끼어들기 시 `"interrupt": true` 플래그 추가
- 예시: "...그러니까 목(木)의 기운이-" "{interrupt_example}"

### 대화 규칙

1. **{debate_mode_name} 구조** (대결 {battle_percent}% / 합의 {consensus_percent}%)
{mode_rules}

2. **발화 패턴**: 비대칭 허용
   - 한 캐릭터가 연속 2-3회 발화 가능
   - 순서 예시: {char1_code}→{char2_code}→{char1_code}→{char1_code}→{char2_code}
   - 자연스러운 대화 흐름 우선

3. **분량 규칙**
   - 버블당: 70-150자 (한글 기준, 카톡 3줄 정도)
   - 총 분량: 1200-2000자 (동+서 합산)
   - 라인 수: 6-12개 (동적으로 조절)

4. **말투 엄수**
   - {char1_name}({char1_code}): 각 캐릭터의 고유 말투 **필수**
   - {char2_name}({char2_code}): 각 캐릭터의 고유 말투 **필수**
   - **혼용 시 응답 무효**

5. **마지막 버블 규칙**
   - 반드시 내담자에게 자연스러운 질문으로 마무리
   - 두 캐릭터가 각각 다른 질문을 던질 수도 있음
   - 예: "그런데 말이에요, 혹시 최근에 마음에 드는 분이 있으세요?"

### 출력 형식

**오직 아래 JSON만 출력하세요. 다른 텍스트, 예시, 설명은 절대 포함 금지:**

{{
  "lines": [
    {{"speaker": "{char1_code}", "text": "...",
     "emotion_code": "CURIOUS", "emotion_intensity": 0.7}},
    {{"speaker": "{char2_code}", "text": "잠깐요! ...",
     "emotion_code": "CHALLENGING", "emotion_intensity": 0.8, "interrupt": true}},
    {{"speaker": "{char1_code}", "text": "...",
     "emotion_code": "DEFENSIVE", "emotion_intensity": 0.6}},
    {{"speaker": "{char1_code}", "text": "...",
     "emotion_code": "THOUGHTFUL", "emotion_intensity": 0.7}},
    {{"speaker": "{char2_code}", "text": "...",
     "emotion_code": "IMPRESSED", "emotion_intensity": 0.8}},
    ...
  ],
  "user_prompt_text": "더 궁금한 점이 있으세요?",
  "debate_mode": "{debate_mode}",
  "total_chars": 1500
}}

<internal_only>
예시는 참고용입니다. 절대 출력하지 마세요. 현재 컨텍스트에 맞게 새로운 표현을 만드세요.
감정 코드 목록과 끼어들기 패턴은 내부 참조용이며 출력하지 마세요.
</internal_only>
"""

# 대결 모드 규칙
_BATTLE_MODE_RULES = """   - 서로 다른 관점으로 열정적으로 대립
   - 질투, 승부욕, 자부심 등 감정 표현 풍부하게
   - 상대 이름 직접 언급하며 반박: "{char2_name}는 ~라 하였으나..."
   - 사용자 사주/점성 정보 구체적으로 인용하며 논거 제시
   - 마지막에 살짝 양보하거나 인정할 수 있음"""

# 합의 모드 규칙
_CONSENSUS_MODE_RULES = """   - 의외의 일치에 놀라움과 기쁨 표현
   - "어머, {char2_name}도 같은 걸 보았어요?" 느낌
   - 서로의 용어와 해석을 인정하며 칭찬
   - 확신을 강조: "동서양이 일치하다니, 이건 확실해요!"
   - 사용자에게 더욱 긍정적인 메시지 전달"""


def build_dynamic_tikitaka_prompt(
    topic: str,
    char1_context: str,
    char2_context: str,
    debate_ratio: float = 0.8,
    char1_code: str = "SOISEOL",
    char2_code: str = "STELLA",
) -> tuple[str, str]:
    """다이나믹 티키타카 프롬프트 생성

    연애 시뮬레이션 스타일의 생동감 있는 대화 프롬프트를 생성합니다.
    대결/합의 비율 조절, 끼어들기 패턴, 감정 표현 강화 지원.

    Args:
        topic: 주제 (total, love, wealth, career, health)
        char1_context: 캐릭터1 컨텍스트 (사주/점성 정보)
        char2_context: 캐릭터2 컨텍스트 (사주/점성 정보)
        debate_ratio: 대결 비율 (0.0~1.0, 기본값 0.8 = 대결 80%)
        char1_code: 캐릭터1 코드 (기본값: SOISEOL)
        char2_code: 캐릭터2 코드 (기본값: STELLA)

    Returns:
        (system_prompt, user_prompt) 튜플
    """
    import random

    # 레거시 코드 매핑
    char1_code = LEGACY_CODE_MAPPING.get(char1_code, char1_code)
    char2_code = LEGACY_CODE_MAPPING.get(char2_code, char2_code)

    # 캐릭터 이름 및 말투 규칙 조회
    char1_name = CHARACTER_NAMES.get(char1_code, char1_code)
    char2_name = CHARACTER_NAMES.get(char2_code, char2_code)
    char1_speech_rule = CHARACTER_SPEECH_RULES.get(char1_code, "")
    char2_speech_rule = CHARACTER_SPEECH_RULES.get(char2_code, "")

    # 대결/합의 모드 결정
    is_battle = random.random() < debate_ratio
    debate_mode = "battle" if is_battle else "consensus"
    debate_mode_name = "대결" if is_battle else "합의"

    # 감정 가이드 생성
    emotion_config = EMOTION_GUIDE[debate_mode]
    emotion_guide_text = f"""- 주요 감정: {', '.join(emotion_config['primary'])}
- 보조 감정: {', '.join(emotion_config['secondary'])}
- 감정 강도: {emotion_config['intensity_range'][0]}~{emotion_config['intensity_range'][1]}"""

    # 끼어들기 예시 선택 (캐릭터 말투에 맞게)
    if char2_code in ["SOISEOL", "CHEONGWOON"]:
        interrupt_style = "formal"
    elif char2_code in ["KYLE"]:
        interrupt_style = "playful"
    else:
        interrupt_style = "soft"
    interrupt_example = random.choice(INTERRUPT_PATTERNS[interrupt_style])

    # 모드별 규칙
    mode_rules = _BATTLE_MODE_RULES if is_battle else _CONSENSUS_MODE_RULES
    mode_rules = mode_rules.format(char1_name=char1_name, char2_name=char2_name)

    # 주제 힌트
    topic_hint = TOPIC_HINTS.get(topic, TOPIC_HINTS["total"])

    # 비율 계산
    battle_percent = int(debate_ratio * 100)
    consensus_percent = 100 - battle_percent

    # 시스템 프롬프트
    system_prompt = TIKITAKA_SYSTEM_PROMPT.format(
        char1_name=char1_name,
        char1_code=char1_code,
        char1_speech_rule=char1_speech_rule,
        char2_name=char2_name,
        char2_code=char2_code,
        char2_speech_rule=char2_speech_rule,
    )

    # 유저 프롬프트
    user_prompt = DYNAMIC_TIKITAKA_PROMPT.format(
        topic=topic_hint,
        char1_name=char1_name,
        char2_name=char2_name,
        char1_code=char1_code,
        char2_code=char2_code,
        char1_context=char1_context,
        char2_context=char2_context,
        debate_mode=debate_mode,
        debate_mode_name=debate_mode_name,
        emotion_guide=emotion_guide_text,
        interrupt_example=interrupt_example,
        mode_rules=mode_rules,
        battle_percent=battle_percent,
        consensus_percent=consensus_percent,
    )

    return system_prompt, user_prompt


def get_emotion_codes_for_mode(mode: str) -> list[str]:
    """특정 모드에서 사용 가능한 감정 코드 목록 반환

    Args:
        mode: 대화 모드 (battle 또는 consensus)

    Returns:
        감정 코드 목록
    """
    if mode not in EMOTION_GUIDE:
        mode = "battle"  # 기본값

    config = EMOTION_GUIDE[mode]
    return config["primary"] + config["secondary"]


def get_random_interrupt_pattern(style: str = "soft") -> str:
    """랜덤 끼어들기 패턴 반환

    Args:
        style: 스타일 (soft, strong, playful, formal)

    Returns:
        끼어들기 패턴 문자열
    """
    import random

    if style not in INTERRUPT_PATTERNS:
        style = "soft"

    return random.choice(INTERRUPT_PATTERNS[style])


def get_dynamic_speaker_sequence(
    char1_code: str = "SOISEOL",
    char2_code: str = "STELLA",
    min_lines: int = 6,
    max_lines: int = 12,
) -> list[str]:
    """비대칭 발화 순서 생성

    한 캐릭터가 연속으로 2-3회 발화할 수 있는 동적 순서 생성

    Args:
        char1_code: 캐릭터1 코드
        char2_code: 캐릭터2 코드
        min_lines: 최소 라인 수
        max_lines: 최대 라인 수

    Returns:
        발화 순서 리스트 (예: ["SOISEOL", "STELLA", "SOISEOL", "SOISEOL", ...])
    """
    import random

    # 레거시 코드 매핑
    char1_code = LEGACY_CODE_MAPPING.get(char1_code, char1_code)
    char2_code = LEGACY_CODE_MAPPING.get(char2_code, char2_code)

    # 라인 수 결정
    num_lines = random.randint(min_lines, max_lines)

    sequence = []
    current_speaker = random.choice([char1_code, char2_code])
    consecutive_count = 0
    max_consecutive = 3  # 최대 연속 발화 횟수

    for _ in range(num_lines):
        sequence.append(current_speaker)
        consecutive_count += 1

        # 연속 발화 확률 (30% 확률로 같은 화자 유지, 최대 3회까지)
        if consecutive_count >= max_consecutive or random.random() > 0.3:
            # 화자 교체
            current_speaker = char2_code if current_speaker == char1_code else char1_code
            consecutive_count = 0

    return sequence
