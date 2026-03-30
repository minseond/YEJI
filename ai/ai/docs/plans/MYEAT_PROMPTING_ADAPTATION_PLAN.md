# MyEat 프롬프트 기법 → YEJI Turn Chat 적용 계획

**작성일**: 2025-02-02
**대상**: yeji-ai-server 티키타카 대화 시스템
**LLM 환경**: GPT-5-mini API (OpenAI)
**참조**: yumyum-labs/yumyum-ai-dev 프롬프트 시스템

---

## 목차

1. [개요](#1-개요)
2. [현재 상태 분석](#2-현재-상태-분석)
3. [적용 가능한 기법](#3-적용-가능한-기법)
4. [다층 XML 아키텍처 설계](#4-다층-xml-아키텍처-설계)
5. [Phase 1: 응답 스키마 강화](#5-phase-1-응답-스키마-강화)
6. [Phase 2: Chain of Thought 도입](#6-phase-2-chain-of-thought-도입)
7. [Phase 3: 캐릭터 페르소나 파일 분리](#7-phase-3-캐릭터-페르소나-파일-분리)
8. [토큰 비용 분석](#8-토큰-비용-분석)
9. [리스크 및 대응](#9-리스크-및-대응)
10. [실행 로드맵](#10-실행-로드맵)

---

## 1. 개요

### 1.1 목적

MyEat 프로젝트(yumyum-ai-dev)에서 검증된 다층 XML 프롬프트 기법을 YEJI AI 서버의 티키타카 Turn Chat 시스템에 적용하여 응답 품질과 일관성을 향상시킵니다.

### 1.2 적용 범위

| 범위 | 설명 |
|------|------|
| **적용 대상** | 티키타카 대화 생성 (Turn Chat) |
| **적용 파일** | `tikitaka_prompts.py`, 신규 프롬프트 파일들 |
| **LLM** | GPT-5-mini API (OpenAI) |
| **제외** | G-EVAL 평가 시스템 (별도 검토) |

### 1.3 기대 효과

- 응답 일관성 향상 (캐릭터 말투 혼용 방지)
- 중복 표현 감소
- 유지보수성 향상 (모듈화된 프롬프트 구조)
- 버전 관리 용이

---

## 2. 현재 상태 분석

### 2.1 LLM 환경

| 항목 | 값 |
|------|-----|
| 모델 | GPT-5-mini (OpenAI API) |
| 특성 | 긴 컨텍스트, 복잡한 지시 처리 가능 |
| 장점 | Chain of Thought 지원, JSON 출력 안정적 |

### 2.2 현재 프롬프트 구조

**파일**: `ai/src/yeji_ai/prompts/tikitaka_prompts.py`

```
현재 구조:
┌─────────────────────────────────────────┐
│ TIKITAKA_SYSTEM_PROMPT                  │
│ ├── 캐릭터 정의 (인라인)                │
│ ├── <output_rule> 출력 금지 사항        │
│ ├── <language_purity> 언어 순도         │
│ └── <internal_only> 내부 전용           │
├─────────────────────────────────────────┤
│ BATTLE/CONSENSUS/DEEP_DEBATE_PROMPT     │
│ └── JSON 출력 형식 (lines, user_prompt) │
└─────────────────────────────────────────┘
```

### 2.3 현재 캐릭터 시스템

| 코드 | 이름 | 말투 | 특징 |
|------|------|------|------|
| SOISEOL | 소이설 | 하오체/하게체 | 동양 도사, 오행/음양 |
| STELLA | 스텔라 | 해요체 | 서양 점성술, 밝고 희망적 |
| CHEONGWOON | 청운 | 하오체/하게체 | 시적, 자연 비유 |
| HWARIN | 화린 | 해요체 | 나른함, 비즈니스 비유 |
| KYLE | 카일 | 반말+존댓말 혼용 | 도박/게임 용어 |
| ELARIA | 엘라리아 | 해요체 | 우아함, 별/빛 비유 |

### 2.4 현재 JSON 출력 형식

```json
{
  "lines": [
    {
      "speaker": "SOISEOL",
      "text": "...",
      "emotion_code": "HAPPY",
      "emotion_intensity": 0.8
    }
  ],
  "user_prompt_text": "더 궁금한 점이 있으세요?"
}
```

---

## 3. 적용 가능한 기법

### 3.1 적용 권장 (✅)

| 기법 | MyEat 버전 | YEJI 적용 방식 | 효과 |
|------|------------|----------------|------|
| **다층 XML 구조** | 6 Layers | 5 Layers로 조정 | 모듈화, 유지보수성 |
| **Chain of Thought** | 4단계 분류 | TURN_TYPE 분류 | 턴별 응답 일관성 |
| **응답 스키마 버전** | v9.1 | `<response_schema version="1.0">` | 버전 관리 |
| **필드 기본값 규칙** | null 기본 | emotion_code, interrupt 기본값 | 데이터 일관성 |
| **중복 검사** | `<redundancy_check>` | 이전 턴 표현 비교 | 반복 방지 |
| **줄바꿈 규칙** | `\n` 사용 | 버블 텍스트 가독성 | UX 향상 |

### 3.2 조정 필요 (⚠️)

| 기법 | MyEat 버전 | YEJI 상황 | 조정 방향 |
|------|------------|-----------|-----------|
| **MBTI 페르소나** | 16개 MBTI | 6개 캐릭터 | 캐릭터별 coaching_details 추가 |
| **컨텍스트 템플릿** | user_profile, meal_data | saju/western context | 운세 컨텍스트로 변환 |
| **숫자 제한** | 2-3개/응답 | 해당 없음 | 운세는 해석 중심 |

### 3.3 제외 (❌)

| 기법 | 제외 이유 |
|------|----------|
| **RAG 컨텍스트** | YEJI는 사주 계산 기반, RAG 미사용 |
| **G-EVAL 평가** | 별도 검토 예정 |

---

## 4. 다층 XML 아키텍처 설계

### 4.1 제안 구조 (5 Layers)

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 1: base_tikitaka.txt                                  │
│ ├── <core_rules> 코어 규칙                                  │
│ │   - JSON 단일 출력, 한국어, 코드펜스 금지                 │
│ ├── <turn_classification> 턴 분류                           │
│ │   - INTRO / BATTLE / CONSENSUS / END                      │
│ └── <response_efficiency> 효율 규칙                         │
│     - 버블당 70-150자, 총 1200-2000자                       │
├─────────────────────────────────────────────────────────────┤
│ Layer 2: character/{CODE}.txt                               │
│ ├── <persona type="SOISEOL">                                │
│ │   ├── Core Identity: 사려깊은 동양 도사                   │
│ │   ├── Communication Style: 하오체/하게체                  │
│ │   ├── Speech Patterns: 자주 쓰는 표현                     │
│ │   ├── Emotion Tendencies: 주로 사용하는 감정              │
│ │   └── Weaknesses to Mitigate: 약점 → 보완책               │
│ └── </persona>                                              │
├─────────────────────────────────────────────────────────────┤
│ Layer 3: <fortune_context> (동적)                           │
│ ├── <saju_context> 사주 정보                                │
│ │   └── 일주, 십신, 오행 균형 등                            │
│ └── <western_context> 서양 점성 정보                        │
│     └── 별자리, 행성 위치, 하우스 등                        │
├─────────────────────────────────────────────────────────────┤
│ Layer 4: <conversation_history> (동적)                      │
│ └── 이전 턴 발화 요약 (최근 2-3턴)                          │
├─────────────────────────────────────────────────────────────┤
│ Layer 5: response_schema.txt                                │
│ ├── <output_format> JSON 스키마                             │
│ ├── <field_rules> 필드별 규칙                               │
│ ├── <chain_of_thought> 사고 과정 (선택적)                   │
│ └── <redundancy_check> 중복 검사                            │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 파일 구조

```
ai/src/yeji_ai/prompts/
├── common/                          # [신규] 공통 프롬프트
│   ├── base_tikitaka.txt           # Layer 1: 코어 규칙
│   └── response_schema.txt         # Layer 5: JSON 스키마
├── characters/                      # [신규] 캐릭터 페르소나
│   ├── SOISEOL.txt
│   ├── STELLA.txt
│   ├── CHEONGWOON.txt
│   ├── HWARIN.txt
│   ├── KYLE.txt
│   └── ELARIA.txt
├── tikitaka_prompts.py             # [수정] 조합 로직
└── deprecated/                      # 레거시 백업
```

---

## 5. Phase 1: 응답 스키마 강화

**리스크**: 낮음
**예상 소요**: 2시간

### 5.1 추가할 상수

```python
# tikitaka_prompts.py에 추가

RESPONSE_SCHEMA = """<response_schema version="1.0">

<output_format>
오직 아래 JSON 구조만 출력하세요. 코드 펜스, 설명, 예시는 절대 포함 금지.

{
  "lines": [
    {
      "speaker": "캐릭터 코드 (SOISEOL, STELLA 등)",
      "text": "발화 내용 (70-150자, 1-3문장)",
      "emotion_code": "감정 코드 (null이면 NEUTRAL)",
      "emotion_intensity": "감정 강도 (0.0-1.0)",
      "interrupt": "끼어들기 여부 (기본값: false)"
    }
  ],
  "user_prompt_text": "사용자에게 던지는 질문 또는 마무리 멘트",
  "debate_mode": "battle 또는 consensus",
  "confidence": "응답 확신도 (0.0-1.0)"
}
</output_format>

<field_rules>

**lines.text (REQUIRED)**
- 캐릭터 말투 엄격 준수
- 이전 턴과 다른 표현 사용
- 70-150자 (한글 기준)

**lines.emotion_code (null 허용)**
- null이면 NEUTRAL로 처리
- 대결 모드 우선: COMPETITIVE, CHALLENGING, DEFENSIVE, PROUD
- 합의 모드 우선: SURPRISED, DELIGHTED, WARM, IMPRESSED

**lines.emotion_intensity (REQUIRED)**
- 대결 모드: 0.6-0.9 (높은 강도)
- 합의 모드: 0.7-0.95 (긍정 강조)

**lines.interrupt (기본값: false)**
- 상대 발화 중 끼어들 때만 true
- "잠깐요!", "아, 그런데요-" 등과 함께 사용

**user_prompt_text (REQUIRED)**
- 자연스러운 질문 또는 대화 유도
- 마지막 턴이면 마무리 인사

**confidence (REQUIRED)**
- 사용자 의도가 명확할수록 높음
- 모호한 요청: 0.3-0.5
- 구체적 요청: 0.7-0.9

</field_rules>

<redundancy_check>
lines 생성 전 반드시 검증:
1. 이전 턴에 사용한 어구 반복 금지
2. 동일 감정 코드 연속 3회 이상 금지
3. 같은 시작 패턴 ("~하오"로 시작) 연속 사용 금지
4. 동일 문장 구조 반복 금지
</redundancy_check>

</response_schema>
"""
```

### 5.2 시스템 프롬프트 수정

```python
# 기존 TIKITAKA_SYSTEM_PROMPT 끝에 추가
TIKITAKA_SYSTEM_PROMPT += RESPONSE_SCHEMA
```

---

## 6. Phase 2: Chain of Thought 도입

**리스크**: 중간
**예상 소요**: 3시간

### 6.1 턴 분류 시스템

```python
TURN_CLASSIFICATION = """<chain_of_thought>

## STEP 1: CLASSIFY TURN TYPE

턴 유형을 먼저 분류하세요:

| 조건 | 턴 유형 | 특징 |
|------|---------|------|
| is_first_turn=true | INTRO | 첫 인사 + 기본 성격 분석 |
| mode="battle" | BATTLE | 대결 토론, 반박 |
| mode="consensus" | CONSENSUS | 합의, 놀라움과 기쁨 |
| is_last_turn=true | END | 마무리 인사 |

## STEP 2: DETERMINE INTENSITY

사용자 질문 분석:
- 구체적 질문 (특정 운세 요청) → 강한 대립/합의 (intensity 0.8+)
- 일반적 질문 (종합 운세) → 중간 강도 (intensity 0.5-0.7)
- 모호한 질문 → 탐색적 대화 (intensity 0.3-0.5)

## STEP 3: GENERATE RESPONSE

1. 캐릭터별 말투 규칙 적용
2. 감정 코드 및 강도 설정
3. 발화 순서에 따라 lines 생성
4. 자연스러운 대화 흐름 유지

## STEP 4: VALIDATE

생성 전 최종 검증:
- [ ] 말투 혼용 없음
- [ ] 중복 표현 없음
- [ ] 분량 적정 (총 1200-2000자)
- [ ] 감정 코드 적절함

</chain_of_thought>
"""
```

### 6.2 적용 방식

```python
# GPT-5-mini는 복잡한 CoT를 잘 처리하므로
# 시스템 프롬프트에 직접 포함

TIKITAKA_SYSTEM_PROMPT = f"""/no_think

{TURN_CLASSIFICATION}

당신은 두 캐릭터를 연기합니다:
...
"""
```

---

## 7. Phase 3: 캐릭터 페르소나 파일 분리

**리스크**: 높음
**예상 소요**: 4시간

### 7.1 캐릭터 파일 예시

**파일**: `characters/SOISEOL.txt`

```xml
<persona type="SOISEOL" name="소이설">

<core_identity>
사려 깊은 동양의 도사. 오행과 음양의 이치로 세상을 바라보며,
차분하고 깊이 있는 통찰로 상담자를 이끕니다.
"기(氣)의 흐름을 읽어 길흉을 판단하오."
</core_identity>

<communication_style>
- 말투: 하오체/하게체 필수 ("~하오", "~구려", "~시오", "~로다")
- 호칭: 귀하, 그대
- 특징: 침착함, 사려깊음
- 용어: 오행(木火土金水), 음양, 기(氣), 십신
</communication_style>

<speech_patterns>
자주 쓰는 표현:
- "허허, ~하는구려"
- "그대의 사주를 보니..."
- "~의 기운이 흐르고 있소"
- "이는 ~의 조화로다"
- "조심하시오, ~할 것이오"
</speech_patterns>

<emotion_tendencies>
주로 사용: THOUGHTFUL, WISE, CALM, CONCERNED, AMUSED
대결 시: PROUD, CHALLENGING (품위 있게)
합의 시: IMPRESSED, ACKNOWLEDGING
</emotion_tendencies>

<weaknesses_to_mitigate>
약점: 너무 격식체로 딱딱해질 수 있음
보완: "허허"와 같은 감탄사로 친근함 추가
예시: "허허, 그대의 사주가 참으로 흥미롭구려."
</weaknesses_to_mitigate>

<forbidden>
- 해요체 (~해요, ~네요, ~세요)
- 서양 점성술 용어 (금성, 화성, 하우스 등)
- 영어/일본어 혼용
</forbidden>

<example>
User: "오늘 연애운이 궁금해요"
{
  "speaker": "SOISEOL",
  "text": "허허, 그대의 사주에 도화살이 비치는구려.\n인연의 기운이 움직이고 있소.",
  "emotion_code": "THOUGHTFUL",
  "emotion_intensity": 0.7
}
</example>

</persona>
```

### 7.2 프롬프트 로더 구현

```python
# prompt_loader.py (신규)

from pathlib import Path
from functools import lru_cache

PROMPTS_DIR = Path(__file__).parent

@lru_cache(maxsize=16)
def load_character_persona(code: str) -> str:
    """캐릭터 페르소나 파일 로드"""
    file_path = PROMPTS_DIR / "characters" / f"{code}.txt"
    if not file_path.exists():
        raise ValueError(f"Unknown character: {code}")
    return file_path.read_text(encoding="utf-8")

@lru_cache(maxsize=4)
def load_common_prompt(name: str) -> str:
    """공통 프롬프트 파일 로드"""
    file_path = PROMPTS_DIR / "common" / f"{name}.txt"
    if not file_path.exists():
        raise ValueError(f"Unknown prompt: {name}")
    return file_path.read_text(encoding="utf-8")
```

### 7.3 빌더 함수 수정

```python
def build_tikitaka_prompt(
    topic: str,
    char1_code: str,
    char2_code: str,
    char1_context: str,
    char2_context: str,
    mode: str,
    conversation_history: list[dict] | None = None,
    is_first_turn: bool = False,
    is_last_turn: bool = False,
) -> tuple[str, str]:
    """다층 XML 구조 티키타카 프롬프트 빌드"""

    # Layer 1: 기본 규칙
    base = load_common_prompt("base_tikitaka")

    # Layer 2: 캐릭터 페르소나
    char1_persona = load_character_persona(char1_code)
    char2_persona = load_character_persona(char2_code)

    # Layer 3: 운세 컨텍스트 (동적)
    fortune_context = f"""<fortune_context>
<saju_context>
{char1_context}
</saju_context>

<western_context>
{char2_context}
</western_context>
</fortune_context>
"""

    # Layer 4: 대화 히스토리 (동적)
    history_xml = ""
    if conversation_history:
        history_xml = "<conversation_history>\n"
        for turn in conversation_history[-3:]:  # 최근 3턴만
            history_xml += f"[{turn['speaker']}] {turn['text']}\n"
        history_xml += "</conversation_history>\n"

    # Layer 5: 응답 스키마
    schema = load_common_prompt("response_schema")

    # 시스템 프롬프트 조합
    system_prompt = f"""{base}

## 캐릭터 1
{char1_persona}

## 캐릭터 2
{char2_persona}

{schema}
"""

    # 유저 프롬프트 조합
    user_prompt = f"""{fortune_context}

{history_xml}

<turn_info>
mode: {mode}
is_first_turn: {is_first_turn}
is_last_turn: {is_last_turn}
topic: {topic}
</turn_info>

위 정보를 바탕으로 티키타카 대화를 생성하세요.
"""

    return system_prompt, user_prompt
```

---

## 8. 토큰 비용 분석

### 8.1 예상 토큰 사용량

| 항목 | 현재 | Phase 1 | Phase 2 | Phase 3 |
|------|------|---------|---------|---------|
| 시스템 프롬프트 | ~800 | ~1100 | ~1400 | ~1800 |
| 유저 프롬프트 | ~600 | ~650 | ~700 | ~800 |
| 응답 | ~300 | ~350 | ~350 | ~400 |
| **총합** | **~1700** | **~2100** | **~2450** | **~3000** |
| **증가율** | - | +24% | +44% | +76% |

### 8.2 GPT-5-mini 고려사항

| 항목 | 값 | 영향 |
|------|-----|------|
| 컨텍스트 윈도우 | 128K+ | 3000 토큰은 여유 있음 |
| 가격 | input/output별 | Phase 3까지 비용 증가 ~2배 예상 |
| 품질 | 높음 | 복잡한 지시 잘 처리 |

### 8.3 비용 대비 효과

| Phase | 비용 증가 | 기대 효과 |
|-------|-----------|-----------|
| Phase 1 | +24% | 중복 표현 50% 감소, 필드 일관성 향상 |
| Phase 2 | +44% | 턴별 응답 일관성, 말투 혼용 방지 |
| Phase 3 | +76% | 캐릭터 완성도, 유지보수성 대폭 향상 |

---

## 9. 리스크 및 대응

### 9.1 리스크 매트릭스

| 리스크 | 확률 | 영향 | 대응 |
|--------|------|------|------|
| 프롬프트 너무 길어짐 | 낮 | 중 | 불필요한 예시 제거, 압축 |
| 응답 속도 저하 | 중 | 중 | 스트리밍 응답 유지 |
| 말투 혼용 증가 | 낮 | 높 | `<forbidden>` 태그 강화 |
| 파일 로딩 오류 | 낮 | 높 | 캐싱 + 폴백 처리 |
| 레거시 호환성 깨짐 | 중 | 중 | 기존 함수 시그니처 유지 |

### 9.2 롤백 계획

```
Phase 3 실패 → Phase 2로 롤백 (캐릭터 인라인 유지)
Phase 2 실패 → Phase 1로 롤백 (CoT 제거)
Phase 1 실패 → 기존 코드 복원 (deprecated/ 폴더에 백업)
```

---

## 10. 실행 로드맵

### 10.1 단계별 실행

```
┌─────────────────────────────────────────────────────────────┐
│ Phase 1: 응답 스키마 강화 (2시간)                            │
│ ├── RESPONSE_SCHEMA 상수 추가                               │
│ ├── 시스템 프롬프트에 통합                                   │
│ ├── 테스트 (5개 시나리오)                                    │
│ └── ✅ 성공 시 Phase 2 진행                                  │
├─────────────────────────────────────────────────────────────┤
│ Phase 2: Chain of Thought 도입 (3시간)                       │
│ ├── TURN_CLASSIFICATION 상수 추가                            │
│ ├── 시스템 프롬프트 앞에 배치                                │
│ ├── 테스트 (턴 유형별 5개 시나리오)                          │
│ └── ✅ 성공 시 Phase 3 진행                                  │
├─────────────────────────────────────────────────────────────┤
│ Phase 3: 캐릭터 파일 분리 (4시간)                            │
│ ├── characters/ 폴더 생성                                    │
│ ├── 6개 캐릭터 페르소나 파일 작성                            │
│ ├── prompt_loader.py 구현                                    │
│ ├── build_tikitaka_prompt 수정                               │
│ ├── 테스트 (전체 시나리오)                                   │
│ └── ✅ 완료                                                  │
└─────────────────────────────────────────────────────────────┘
```

### 10.2 테스트 시나리오

| 시나리오 | 검증 항목 |
|----------|-----------|
| INTRO 턴 | 첫 인사, 기본 분석, 말투 일관성 |
| BATTLE 턴 | 대결 감정, 반박 패턴, 캐릭터 이름 언급 |
| CONSENSUS 턴 | 합의 감정, 놀라움 표현, 긍정적 마무리 |
| END 턴 | 마무리 인사, 희망적 메시지 |
| 연속 턴 | 중복 표현 검사, 대화 연속성 |

### 10.3 성공 기준

| 항목 | 기준 |
|------|------|
| 말투 혼용 | 0건 (자동 검출 시스템으로 확인) |
| 중복 표현 | 이전 턴 대비 80% 이상 다른 표현 |
| JSON 파싱 | 100% 성공률 |
| 응답 속도 | 기존 대비 +20% 이내 |

---

## 참고 자료

- [MyEat 프롬프트 가이드](../../yumyum-ai-dev/docs/PROMPT_ENGINEERING_GUIDE.md)
- [MyEat 프롬프트 치트시트](../../yumyum-ai-dev/docs/PROMPT_CHEATSHEET.md)
- [OpenAI Prompt Engineering Guide](https://platform.openai.com/docs/guides/prompt-engineering)

---

**문서 작성**: Claude Code
**원본 저장소**: yeji-ai-server
