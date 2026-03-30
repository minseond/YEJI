# G-Eval 평가 시스템 설계

> **문서 버전**: 1.0.0
> **작성일**: 2026-01-30
> **상태**: 설계 (Design)
> **담당팀**: SSAFY YEJI AI팀

---

## 목차

1. [개요](#1-개요)
2. [평가 파이프라인 아키텍처](#2-평가-파이프라인-아키텍처)
3. [평가 메트릭 상세](#3-평가-메트릭-상세)
4. [평가 프롬프트 템플릿](#4-평가-프롬프트-템플릿)
5. [메트릭별 점수 계산 방식](#5-메트릭별-점수-계산-방식)
6. [구현 옵션 비교](#6-구현-옵션-비교)
7. [통합 설계](#7-통합-설계)
8. [참조](#8-참조)

---

## 1. 개요

### 1.1 배경

YEJI 운세 서비스는 LLM(yeji-8b-rslora-v7-AWQ)이 생성하는 동양 사주(Eastern) 및 서양 점성술(Western) 응답의 품질을 자동으로 평가해야 합니다. 현재 Pydantic 검증만으로는 **구조적 유효성**만 확인할 수 있으며, **내용 품질**에 대한 평가가 부재합니다.

### 1.2 목적

G-Eval 기반 평가 시스템을 도입하여:

1. **Schema Compliance**: JSON 스키마 준수율 자동 측정
2. **Field Completeness**: 필수 필드 생성율 추적
3. **Code Validity**: 도메인 코드 유효성 검증
4. **Content Quality**: 생성된 내용의 품질 평가 (CoT 기반)

### 1.3 G-Eval이란?

G-Eval(Liu et al., 2023)은 LLM을 Judge로 활용하여 NLG 출력을 평가하는 프레임워크입니다.

**핵심 특징:**
- **Chain-of-Thought (CoT)**: 평가 기준을 단계별로 분해하여 추론
- **Token Probability Weighting**: 확률 가중치로 일관된 점수 산출
- **Form-filling Paradigm**: 구조화된 평가 폼 작성

```
┌─────────────────────────────────────────────────────────────┐
│                     G-Eval 프레임워크                         │
├─────────────────────────────────────────────────────────────┤
│  1. 평가 기준 정의 (Criteria Definition)                      │
│     └─ 명확한 평가 지표와 점수 척도 설정                        │
│                                                             │
│  2. 평가 단계 생성 (Evaluation Steps - CoT)                   │
│     └─ LLM이 단계별 추론 과정을 명시적으로 생성                  │
│                                                             │
│  3. 점수 산출 (Weighted Scoring)                             │
│     └─ 토큰 확률 가중 평균으로 최종 점수 계산                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. 평가 파이프라인 아키텍처

### 2.1 전체 파이프라인

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                           G-Eval 평가 파이프라인                               │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐   │
│  │   LLM 응답   │───▶│ 구조적 평가  │───▶│ 내용 품질   │───▶│  통합 점수   │   │
│  │   (Input)   │    │  (Layer 1)  │    │  (Layer 2)  │    │  (Output)   │   │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘   │
│                            │                  │                  │          │
│                            ▼                  ▼                  ▼          │
│                     ┌─────────────┐    ┌─────────────┐    ┌─────────────┐   │
│                     │Schema Check │    │  G-Eval     │    │  Report     │   │
│                     │Field Fill   │    │  CoT Judge  │    │  Dashboard  │   │
│                     │Code Valid   │    │             │    │             │   │
│                     └─────────────┘    └─────────────┘    └─────────────┘   │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 계층별 역할

| 계층 | 역할 | 평가 항목 | 비용 |
|------|------|----------|------|
| **Layer 1: 구조적 평가** | 결정론적 검증 | Schema, Field, Code | 무료 (로컬) |
| **Layer 2: 내용 품질 평가** | LLM-as-Judge | Coherence, Relevance, Accuracy | 유료 (API/로컬) |
| **Layer 3: 통합 리포트** | 메트릭 집계 | 종합 점수, 추세 분석 | 무료 (로컬) |

### 2.3 데이터 흐름

```python
# 평가 파이프라인 의사코드
class EvaluationPipeline:
    """G-Eval 평가 파이프라인"""

    def evaluate(self, llm_response: dict, fortune_type: str) -> EvaluationResult:
        # Layer 1: 구조적 평가 (결정론적)
        structural_scores = self._evaluate_structural(llm_response, fortune_type)

        # Layer 2: 내용 품질 평가 (G-Eval CoT)
        content_scores = self._evaluate_content(llm_response, fortune_type)

        # Layer 3: 통합 점수
        final_score = self._aggregate_scores(structural_scores, content_scores)

        return EvaluationResult(
            structural=structural_scores,
            content=content_scores,
            final_score=final_score,
        )
```

---

## 3. 평가 메트릭 상세

### 3.1 메트릭 개요

| 메트릭 | 유형 | 범위 | 설명 | 가중치 |
|--------|------|------|------|--------|
| Schema Compliance | 구조적 | 0-100% | JSON 스키마 준수율 | 30% |
| Field Completeness | 구조적 | 0-100% | 필수 필드 생성율 | 20% |
| Code Validity | 구조적 | 0-100% | 도메인 코드 유효성 | 20% |
| Content Coherence | 내용 | 1-5점 | 내용 일관성 (CoT) | 15% |
| Content Accuracy | 내용 | 1-5점 | 도메인 정확성 (CoT) | 15% |

### 3.2 Schema Compliance (스키마 준수율)

**정의**: LLM 응답이 기대 JSON 스키마를 얼마나 준수하는지 측정

**평가 기준:**
```python
# 스키마 준수율 계산
schema_compliance = (valid_fields / total_expected_fields) * 100
```

**Eastern (SajuDataV2) 필수 필드:**
```python
EASTERN_REQUIRED_FIELDS = [
    "element",                          # 대표 오행
    "chart.summary",                    # 차트 요약
    "chart.year.gan", "chart.year.ji",  # 년주
    "chart.month.gan", "chart.month.ji", # 월주
    "chart.day.gan", "chart.day.ji",    # 일주
    "chart.hour.gan", "chart.hour.ji",  # 시주
    "stats.cheongan_jiji",              # 천간지지
    "stats.five_elements.summary",      # 오행 요약
    "stats.five_elements.list",         # 오행 분포
    "stats.yin_yang_ratio.summary",     # 음양 요약
    "stats.yin_yang_ratio.yin",         # 음 비율
    "stats.yin_yang_ratio.yang",        # 양 비율
    "stats.ten_gods.summary",           # 십신 요약
    "stats.ten_gods.list",              # 십신 분포
    "final_verdict.summary",            # 종합 요약
    "final_verdict.strength",           # 강점
    "final_verdict.weakness",           # 약점
    "final_verdict.advice",             # 조언
    "lucky.color",                      # 행운 색상
    "lucky.number",                     # 행운 숫자
    "lucky.item",                       # 행운 아이템
]
```

**Western (WesternFortuneDataV2) 필수 필드:**
```python
WESTERN_REQUIRED_FIELDS = [
    "element",                          # 대표 원소
    "stats.main_sign.name",             # 태양 별자리
    "stats.element_summary",            # 원소 요약
    "stats.element_4_distribution",     # 4원소 분포
    "stats.modality_summary",           # 양태 요약
    "stats.modality_3_distribution",    # 3양태 분포
    "stats.keywords_summary",           # 키워드 요약
    "stats.keywords",                   # 키워드 배열
    "fortune_content.overview",         # 운세 개요
    "fortune_content.detailed_analysis", # 상세 분석
    "fortune_content.advice",           # 조언
    "lucky.color",                      # 행운 색상
    "lucky.number",                     # 행운 숫자
]
```

### 3.3 Field Completeness (필드 완성도)

**정의**: 필수 필드가 의미 있는 값으로 채워졌는지 측정

**평가 기준:**
```python
def evaluate_field_completeness(data: dict, field_path: str) -> float:
    """필드 완성도 평가 (0.0 ~ 1.0)"""
    value = get_nested_value(data, field_path)

    if value is None:
        return 0.0  # 누락

    if isinstance(value, str):
        if not value.strip():
            return 0.0  # 빈 문자열
        if len(value) < 10:
            return 0.5  # 너무 짧음
        return 1.0  # 정상

    if isinstance(value, list):
        if len(value) == 0:
            return 0.0  # 빈 배열
        return min(len(value) / 3, 1.0)  # 최소 3개 기대

    return 1.0 if value else 0.0
```

**완성도 수준:**

| 수준 | 점수 | 설명 |
|------|------|------|
| 완전 | 1.0 | 의미 있는 내용으로 완전히 채워짐 |
| 부분 | 0.5 | 값은 있으나 불완전 (짧은 텍스트, 적은 배열) |
| 누락 | 0.0 | 값이 없거나 빈 값 |

### 3.4 Code Validity (코드 유효성)

**정의**: 생성된 도메인 코드가 유효한 값인지 검증

**검증 대상 코드:**

```python
# 동양 사주 도메인 코드
EAST_ELEMENT_CODES = {"WOOD", "FIRE", "EARTH", "METAL", "WATER"}
CHEON_GAN = {"甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"}
JI_JI = {"子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"}
TEN_GOD_CODES = {
    "BI_GYEON", "GANG_JAE", "SIK_SIN", "SANG_GWAN",
    "PYEON_JAE", "JEONG_JAE", "PYEON_GWAN", "JEONG_GWAN",
    "PYEON_IN", "JEONG_IN", "ETC"
}

# 서양 점성술 도메인 코드
WEST_ELEMENT_CODES = {"FIRE", "EARTH", "AIR", "WATER"}
MODALITY_CODES = {"CARDINAL", "FIXED", "MUTABLE"}
ZODIAC_SIGNS_KR = {
    "양자리", "황소자리", "쌍둥이자리", "게자리",
    "사자자리", "처녀자리", "천칭자리", "전갈자리",
    "사수자리", "염소자리", "물병자리", "물고기자리"
}
```

**유효성 점수 계산:**
```python
def evaluate_code_validity(data: dict, fortune_type: str) -> float:
    """코드 유효성 평가 (0.0 ~ 1.0)"""
    code_checks = get_code_check_list(fortune_type)
    valid_count = 0

    for check in code_checks:
        value = get_nested_value(data, check.path)
        if value and value in check.valid_values:
            valid_count += 1

    return valid_count / len(code_checks) if code_checks else 1.0
```

### 3.5 Content Coherence (내용 일관성)

**정의**: 생성된 텍스트가 논리적으로 일관되고 자연스러운지 평가

**평가 차원:**
- 문장 간 논리적 연결
- 주제 일관성
- 모순 없는 내용

**평가 척도 (1-5):**

| 점수 | 설명 |
|------|------|
| 5 | 완벽하게 일관됨 - 모든 내용이 논리적으로 연결 |
| 4 | 대체로 일관됨 - 사소한 불일치 |
| 3 | 보통 - 일부 논리적 흐름 부재 |
| 2 | 일관성 부족 - 여러 모순 존재 |
| 1 | 매우 불일관 - 내용 연결 불가 |

### 3.6 Content Accuracy (내용 정확성)

**정의**: 사주/점성술 도메인 지식 관점에서 내용이 정확한지 평가

**평가 차원:**
- 오행/원소 해석의 정확성
- 천간지지/별자리 분석의 적절성
- 조언의 관련성

---

## 4. 평가 프롬프트 템플릿

### 4.1 G-Eval 기본 프롬프트 구조

```python
GEVAL_BASE_TEMPLATE = """
당신은 운세 콘텐츠 품질을 평가하는 전문 평가자입니다.

## 평가 대상
{content}

## 평가 기준: {criterion_name}
{criterion_description}

## 평가 단계 (Chain-of-Thought)
{evaluation_steps}

## 평가 척도
1점: {score_1_description}
2점: {score_2_description}
3점: {score_3_description}
4점: {score_4_description}
5점: {score_5_description}

## 지시사항
1. 위 평가 단계를 하나씩 따라가며 분석하세요.
2. 각 단계에서 발견한 내용을 <reasoning> 태그 안에 기록하세요.
3. 최종 점수를 <score> 태그 안에 1-5 사이 정수로 기록하세요.

## 응답 형식
<reasoning>
[단계별 분석 내용]
</reasoning>

<score>[1-5]</score>
"""
```

### 4.2 Eastern (동양 사주) Coherence 평가 프롬프트

```python
EASTERN_COHERENCE_PROMPT = """
당신은 사주명리학 전문가입니다. 아래 사주 분석 결과의 일관성을 평가하세요.

## 평가 대상 (동양 사주 분석)
```json
{eastern_content}
```

## 평가 기준: 내용 일관성 (Coherence)
사주 분석의 각 섹션이 논리적으로 연결되어 있고, 상호 모순이 없는지 평가합니다.

## 평가 단계 (Chain-of-Thought)
1. 오행 분석(five_elements)과 종합 해석(final_verdict)이 일치하는지 확인
   - 강한 오행이 강점(strength)에 반영되어 있는가?
   - 약한 오행이 약점(weakness)에 반영되어 있는가?

2. 십신 분석(ten_gods)과 성격/조언이 연결되는지 확인
   - 우세 십신이 성격 분석에 반영되어 있는가?
   - 십신 특성이 조언(advice)에 일관되게 연결되는가?

3. 음양 비율(yin_yang_ratio)과 전체 분석의 균형 확인
   - 음양 불균형이 있다면 보완 조언이 있는가?

4. 행운 정보(lucky)가 오행 분석과 연결되는지 확인
   - 부족한 오행을 보완하는 색상/아이템인가?

## 평가 척도
1점: 각 섹션이 완전히 분리되어 연결성 없음
2점: 일부 연결되나 여러 모순 존재
3점: 기본적인 연결은 있으나 세부 불일치 존재
4점: 대부분 일관되며 사소한 불일치만 존재
5점: 모든 섹션이 완벽하게 연결되고 일관됨

## 응답 형식
<reasoning>
[단계별 분석]
</reasoning>

<score>[1-5]</score>
"""
```

### 4.3 Eastern (동양 사주) Accuracy 평가 프롬프트

```python
EASTERN_ACCURACY_PROMPT = """
당신은 사주명리학 전문가입니다. 아래 사주 분석의 도메인 정확성을 평가하세요.

## 평가 대상 (동양 사주 분석)
```json
{eastern_content}
```

## 입력 정보 (사주 원국)
- 년주: {year_pillar}
- 월주: {month_pillar}
- 일주: {day_pillar}
- 시주: {hour_pillar}

## 평가 기준: 도메인 정확성 (Accuracy)
사주명리학 관점에서 분석 내용이 정확하고 적절한지 평가합니다.

## 평가 단계 (Chain-of-Thought)
1. 천간지지 오행 배속이 정확한지 확인
   - 甲乙 → 목(WOOD), 丙丁 → 화(FIRE), 戊己 → 토(EARTH)
   - 庚辛 → 금(METAL), 壬癸 → 수(WATER)

2. 오행 비율 계산이 합리적인지 확인
   - 8자(천간4 + 지지4) 기준 오행 분포가 적절한가?

3. 십신 배속이 정확한지 확인
   - 일간 기준 다른 천간과의 관계가 올바른가?

4. 오행 상생상극 해석이 적절한지 확인
   - 목생화, 화생토, 토생금, 금생수, 수생목 관계 반영

5. 조언이 사주학적 관점에서 적절한지 확인
   - 부족한 오행 보완 방안이 합리적인가?

## 평가 척도
1점: 사주학적으로 완전히 부정확함
2점: 기본 개념은 있으나 여러 오류 존재
3점: 대체로 정확하나 세부 오류 존재
4점: 정확하며 사소한 개선점만 존재
5점: 사주학적으로 완벽하게 정확함

## 응답 형식
<reasoning>
[단계별 분석]
</reasoning>

<score>[1-5]</score>
"""
```

### 4.4 Western (서양 점성술) Coherence 평가 프롬프트

```python
WESTERN_COHERENCE_PROMPT = """
당신은 서양 점성술 전문가입니다. 아래 점성술 분석 결과의 일관성을 평가하세요.

## 평가 대상 (서양 점성술 분석)
```json
{western_content}
```

## 평가 기준: 내용 일관성 (Coherence)
점성술 분석의 각 섹션이 논리적으로 연결되어 있고, 상호 모순이 없는지 평가합니다.

## 평가 단계 (Chain-of-Thought)
1. 태양 별자리(main_sign)와 성격 분석이 일치하는지 확인
   - 별자리 특성이 fortune_content.overview에 반영되어 있는가?

2. 4원소 분포(element_4_distribution)와 분석이 연결되는지 확인
   - 우세 원소가 성격/강점 분석에 반영되어 있는가?
   - 부족한 원소가 약점/조언에 반영되어 있는가?

3. 3양태 분포(modality_3_distribution)와 행동 패턴 분석 확인
   - 우세 양태가 성격 설명에 연결되어 있는가?

4. 키워드(keywords)가 전체 분석과 일관되는지 확인
   - 키워드가 분석 내용을 적절히 요약하는가?

5. 행운 정보(lucky)가 점성술 분석과 연결되는지 확인

## 평가 척도
1점: 각 섹션이 완전히 분리되어 연결성 없음
2점: 일부 연결되나 여러 모순 존재
3점: 기본적인 연결은 있으나 세부 불일치 존재
4점: 대부분 일관되며 사소한 불일치만 존재
5점: 모든 섹션이 완벽하게 연결되고 일관됨

## 응답 형식
<reasoning>
[단계별 분석]
</reasoning>

<score>[1-5]</score>
"""
```

### 4.5 Western (서양 점성술) Accuracy 평가 프롬프트

```python
WESTERN_ACCURACY_PROMPT = """
당신은 서양 점성술 전문가입니다. 아래 점성술 분석의 도메인 정확성을 평가하세요.

## 평가 대상 (서양 점성술 분석)
```json
{western_content}
```

## 입력 정보
- 생년월일: {birth_date}
- 태양 별자리: {sun_sign}

## 평가 기준: 도메인 정확성 (Accuracy)
서양 점성술 관점에서 분석 내용이 정확하고 적절한지 평가합니다.

## 평가 단계 (Chain-of-Thought)
1. 별자리-원소 매칭이 정확한지 확인
   - 불: 양자리, 사자자리, 사수자리
   - 흙: 황소자리, 처녀자리, 염소자리
   - 공기: 쌍둥이자리, 천칭자리, 물병자리
   - 물: 게자리, 전갈자리, 물고기자리

2. 별자리-양태 매칭이 정확한지 확인
   - 활동(Cardinal): 양자리, 게자리, 천칭자리, 염소자리
   - 고정(Fixed): 황소자리, 사자자리, 전갈자리, 물병자리
   - 변동(Mutable): 쌍둥이자리, 처녀자리, 사수자리, 물고기자리

3. 별자리 특성 해석이 정확한지 확인
   - 해당 별자리의 전통적 특성이 반영되어 있는가?

4. 원소/양태 해석이 적절한지 확인
   - 원소별 특성(불=열정, 흙=실용, 공기=지성, 물=감성)
   - 양태별 특성(활동=주도, 고정=안정, 변동=적응)

5. 조언이 점성술적 관점에서 적절한지 확인

## 평가 척도
1점: 점성술적으로 완전히 부정확함
2점: 기본 개념은 있으나 여러 오류 존재
3점: 대체로 정확하나 세부 오류 존재
4점: 정확하며 사소한 개선점만 존재
5점: 점성술적으로 완벽하게 정확함

## 응답 형식
<reasoning>
[단계별 분석]
</reasoning>

<score>[1-5]</score>
"""
```

---

## 5. 메트릭별 점수 계산 방식

### 5.1 구조적 평가 점수 계산

```python
from dataclasses import dataclass
from typing import Any

@dataclass
class StructuralEvaluationResult:
    """구조적 평가 결과"""

    schema_compliance: float      # 0.0 ~ 1.0
    field_completeness: float     # 0.0 ~ 1.0
    code_validity: float          # 0.0 ~ 1.0

    @property
    def weighted_score(self) -> float:
        """가중치 적용 점수 (0-100)"""
        return (
            self.schema_compliance * 30 +    # 30%
            self.field_completeness * 20 +   # 20%
            self.code_validity * 20          # 20%
        )


def evaluate_structural(data: dict, fortune_type: str) -> StructuralEvaluationResult:
    """구조적 평가 수행"""

    # 1. Schema Compliance
    required_fields = get_required_fields(fortune_type)
    present_fields = count_present_fields(data, required_fields)
    schema_compliance = present_fields / len(required_fields)

    # 2. Field Completeness
    completeness_scores = [
        evaluate_field_completeness(data, field)
        for field in required_fields
    ]
    field_completeness = sum(completeness_scores) / len(completeness_scores)

    # 3. Code Validity
    code_validity = evaluate_code_validity(data, fortune_type)

    return StructuralEvaluationResult(
        schema_compliance=schema_compliance,
        field_completeness=field_completeness,
        code_validity=code_validity,
    )
```

### 5.2 내용 품질 점수 계산 (G-Eval)

```python
import re
from typing import Literal

@dataclass
class ContentEvaluationResult:
    """내용 품질 평가 결과"""

    coherence_score: int          # 1-5
    coherence_reasoning: str
    accuracy_score: int           # 1-5
    accuracy_reasoning: str

    @property
    def weighted_score(self) -> float:
        """가중치 적용 점수 (0-100)"""
        # 1-5점을 0-100으로 변환 후 가중치 적용
        coherence_normalized = (self.coherence_score - 1) / 4 * 100
        accuracy_normalized = (self.accuracy_score - 1) / 4 * 100

        return (
            coherence_normalized * 0.15 +  # 15%
            accuracy_normalized * 0.15     # 15%
        )


async def evaluate_content_geval(
    data: dict,
    fortune_type: Literal["eastern", "western"],
    llm_judge: LLMJudge,
) -> ContentEvaluationResult:
    """G-Eval 기반 내용 품질 평가"""

    # 프롬프트 선택
    if fortune_type == "eastern":
        coherence_prompt = EASTERN_COHERENCE_PROMPT.format(
            eastern_content=json.dumps(data, ensure_ascii=False, indent=2)
        )
        accuracy_prompt = EASTERN_ACCURACY_PROMPT.format(
            eastern_content=json.dumps(data, ensure_ascii=False, indent=2),
            year_pillar=data.get("chart", {}).get("year", {}),
            month_pillar=data.get("chart", {}).get("month", {}),
            day_pillar=data.get("chart", {}).get("day", {}),
            hour_pillar=data.get("chart", {}).get("hour", {}),
        )
    else:
        coherence_prompt = WESTERN_COHERENCE_PROMPT.format(
            western_content=json.dumps(data, ensure_ascii=False, indent=2)
        )
        accuracy_prompt = WESTERN_ACCURACY_PROMPT.format(
            western_content=json.dumps(data, ensure_ascii=False, indent=2),
            birth_date=data.get("birth_date", "N/A"),
            sun_sign=data.get("stats", {}).get("main_sign", {}).get("name", "N/A"),
        )

    # LLM Judge 호출 (병렬)
    coherence_response, accuracy_response = await asyncio.gather(
        llm_judge.evaluate(coherence_prompt),
        llm_judge.evaluate(accuracy_prompt),
    )

    # 응답 파싱
    coherence_score, coherence_reasoning = parse_geval_response(coherence_response)
    accuracy_score, accuracy_reasoning = parse_geval_response(accuracy_response)

    return ContentEvaluationResult(
        coherence_score=coherence_score,
        coherence_reasoning=coherence_reasoning,
        accuracy_score=accuracy_score,
        accuracy_reasoning=accuracy_reasoning,
    )


def parse_geval_response(response: str) -> tuple[int, str]:
    """G-Eval 응답 파싱"""

    # <reasoning> 태그 추출
    reasoning_match = re.search(r"<reasoning>(.*?)</reasoning>", response, re.DOTALL)
    reasoning = reasoning_match.group(1).strip() if reasoning_match else ""

    # <score> 태그 추출
    score_match = re.search(r"<score>(\d)</score>", response)
    score = int(score_match.group(1)) if score_match else 3  # 기본값 3

    # 점수 범위 검증
    score = max(1, min(5, score))

    return score, reasoning
```

### 5.3 통합 점수 계산

```python
@dataclass
class FinalEvaluationResult:
    """최종 평가 결과"""

    structural: StructuralEvaluationResult
    content: ContentEvaluationResult

    @property
    def final_score(self) -> float:
        """최종 통합 점수 (0-100)"""
        return self.structural.weighted_score + self.content.weighted_score

    @property
    def grade(self) -> str:
        """점수 등급"""
        score = self.final_score
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"

    def to_dict(self) -> dict:
        """딕셔너리 변환"""
        return {
            "final_score": round(self.final_score, 2),
            "grade": self.grade,
            "structural": {
                "schema_compliance": round(self.structural.schema_compliance * 100, 2),
                "field_completeness": round(self.structural.field_completeness * 100, 2),
                "code_validity": round(self.structural.code_validity * 100, 2),
                "weighted_score": round(self.structural.weighted_score, 2),
            },
            "content": {
                "coherence_score": self.content.coherence_score,
                "coherence_reasoning": self.content.coherence_reasoning,
                "accuracy_score": self.content.accuracy_score,
                "accuracy_reasoning": self.content.accuracy_reasoning,
                "weighted_score": round(self.content.weighted_score, 2),
            },
        }
```

### 5.4 점수 가중치 요약

| 메트릭 | 가중치 | 만점 기여 |
|--------|--------|----------|
| Schema Compliance | 30% | 30점 |
| Field Completeness | 20% | 20점 |
| Code Validity | 20% | 20점 |
| Content Coherence | 15% | 15점 |
| Content Accuracy | 15% | 15점 |
| **합계** | **100%** | **100점** |

---

## 6. 구현 옵션 비교

### 6.1 옵션 A: 외부 LLM 호출 (Claude/GPT)

**아키텍처:**
```
LLM 응답 → G-Eval 평가 → Claude API/GPT API → 평가 결과
```

**장점:**
- 높은 평가 품질 (SOTA 모델 활용)
- 구현 간소화 (API 호출만)
- 별도 인프라 불필요

**단점:**
- API 비용 발생 (호출당 ~$0.01)
- 외부 의존성 (네트워크, API 가용성)
- 레이턴시 증가 (~2-5초)

**비용 추정:**
| 항목 | 값 | 비용 |
|------|-----|------|
| 일일 평가 건수 | 1,000건 | - |
| 평가당 토큰 | ~2,000 토큰 | - |
| Claude Sonnet 요금 | $3/1M input, $15/1M output | ~$0.01/건 |
| **월간 비용** | - | **~$300** |

### 6.2 옵션 B: Qwen3 자체 평가 (비용 절감)

**아키텍처:**
```
LLM 응답 → G-Eval 평가 → vLLM (Qwen3) → 평가 결과
```

**장점:**
- 추가 비용 없음 (기존 인프라 활용)
- 낮은 레이턴시 (~0.5-1초)
- 완전한 제어권

**단점:**
- 평가 품질이 피평가 모델 수준에 의존
- 자기 평가 편향 가능성
- GPU 리소스 점유

**편향 완화 전략:**
```python
# 자기 평가 편향 완화를 위한 앙상블 접근
class SelfEvaluationEnsemble:
    """자체 평가 편향 완화를 위한 앙상블"""

    def __init__(self, temperatures: list[float] = [0.3, 0.5, 0.7]):
        self.temperatures = temperatures

    async def evaluate(self, prompt: str) -> tuple[int, str]:
        """다양한 temperature로 평가 후 합산"""
        scores = []
        reasonings = []

        for temp in self.temperatures:
            response = await self.llm.generate(
                prompt=prompt,
                temperature=temp,
            )
            score, reasoning = parse_geval_response(response)
            scores.append(score)
            reasonings.append(reasoning)

        # 중앙값 사용 (이상치 영향 최소화)
        final_score = int(sorted(scores)[len(scores) // 2])
        final_reasoning = reasonings[scores.index(final_score)]

        return final_score, final_reasoning
```

### 6.3 옵션 C: 하이브리드 접근 (권장)

**아키텍처:**
```
┌─────────────────────────────────────────────────────────────────┐
│                    하이브리드 평가 시스템                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────┐                                           │
│  │   모든 응답       │                                           │
│  └────────┬─────────┘                                           │
│           │                                                     │
│           ▼                                                     │
│  ┌──────────────────┐    100%     ┌──────────────────┐         │
│  │  구조적 평가      │ ──────────▶ │  결정론적 검증    │         │
│  │  (Layer 1)       │             │  (로컬, 무료)     │         │
│  └────────┬─────────┘             └──────────────────┘         │
│           │                                                     │
│           ▼                                                     │
│  ┌──────────────────┐                                           │
│  │  샘플링 (10%)    │                                           │
│  └────────┬─────────┘                                           │
│           │                                                     │
│           ▼                                                     │
│  ┌──────────────────┐    90%      ┌──────────────────┐         │
│  │  내용 품질 평가   │ ──────────▶ │  Qwen3 자체 평가  │         │
│  │  (Layer 2)       │             │  (vLLM, 무료)     │         │
│  └────────┬─────────┘             └──────────────────┘         │
│           │                                                     │
│           │  10% (검증/캘리브레이션)                             │
│           ▼                                                     │
│  ┌──────────────────┐             ┌──────────────────┐         │
│  │  외부 검증       │ ──────────▶ │  Claude API      │         │
│  │  (Layer 2b)      │             │  (유료, 정확)     │         │
│  └──────────────────┘             └──────────────────┘         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**전략:**
1. **구조적 평가**: 100% 로컬 (결정론적)
2. **내용 품질 평가**:
   - 90%: Qwen3 자체 평가 (비용 절감)
   - 10%: Claude API 외부 검증 (캘리브레이션)

**장점:**
- 비용 효율적 (월 ~$30)
- 품질 모니터링 가능 (외부 검증)
- 자체 평가 편향 감지

**비용 추정:**
| 항목 | 값 | 비용 |
|------|-----|------|
| 일일 평가 건수 | 1,000건 | - |
| 자체 평가 (90%) | 900건 | $0 |
| 외부 검증 (10%) | 100건 | ~$1 |
| **월간 비용** | - | **~$30** |

### 6.4 옵션 비교 요약

| 기준 | 옵션 A (외부) | 옵션 B (자체) | 옵션 C (하이브리드) |
|------|-------------|--------------|-------------------|
| 평가 품질 | 높음 | 중간 | 높음 (캘리브레이션) |
| 월간 비용 | ~$300 | $0 | ~$30 |
| 레이턴시 | 2-5초 | 0.5-1초 | 0.5-2초 |
| 외부 의존성 | 높음 | 없음 | 낮음 |
| 자체 편향 | 없음 | 있음 | 감지 가능 |
| **권장도** | | | **권장** |

---

## 7. 통합 설계

### 7.1 파일 구조

```
yeji-ai-server/ai/src/yeji_ai/
├── evaluation/
│   ├── __init__.py
│   ├── pipeline.py              # 평가 파이프라인
│   ├── structural/
│   │   ├── __init__.py
│   │   ├── schema_checker.py    # 스키마 준수 검사
│   │   ├── field_evaluator.py   # 필드 완성도 평가
│   │   └── code_validator.py    # 코드 유효성 검사
│   ├── content/
│   │   ├── __init__.py
│   │   ├── geval_judge.py       # G-Eval Judge
│   │   ├── prompts.py           # 평가 프롬프트
│   │   └── parsers.py           # 응답 파서
│   ├── aggregator.py            # 점수 집계
│   └── models.py                # 평가 결과 모델
├── tests/
│   └── evaluation/
│       ├── test_structural.py
│       ├── test_content.py
│       └── test_pipeline.py
```

### 7.2 핵심 인터페이스

```python
# evaluation/models.py
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

@dataclass
class EvaluationConfig:
    """평가 설정"""

    enable_content_eval: bool = True
    external_validation_rate: float = 0.1  # 10%
    judge_temperature: float = 0.3
    max_retries: int = 2


@dataclass
class EvaluationMetadata:
    """평가 메타데이터"""

    fortune_type: Literal["eastern", "western"]
    evaluated_at: datetime
    judge_model: str
    latency_ms: float


@dataclass
class EvaluationReport:
    """평가 리포트"""

    metadata: EvaluationMetadata
    structural: StructuralEvaluationResult
    content: ContentEvaluationResult | None
    final_score: float
    grade: str

    def to_prometheus_metrics(self) -> list[PrometheusMetric]:
        """Prometheus 메트릭으로 변환"""
        return [
            PrometheusMetric(
                name="yeji_geval_schema_compliance",
                help="스키마 준수율",
                type="gauge",
                labels={"fortune_type": self.metadata.fortune_type},
                value=self.structural.schema_compliance * 100,
            ),
            PrometheusMetric(
                name="yeji_geval_field_completeness",
                help="필드 완성도",
                type="gauge",
                labels={"fortune_type": self.metadata.fortune_type},
                value=self.structural.field_completeness * 100,
            ),
            PrometheusMetric(
                name="yeji_geval_code_validity",
                help="코드 유효성",
                type="gauge",
                labels={"fortune_type": self.metadata.fortune_type},
                value=self.structural.code_validity * 100,
            ),
            PrometheusMetric(
                name="yeji_geval_final_score",
                help="최종 평가 점수",
                type="gauge",
                labels={"fortune_type": self.metadata.fortune_type},
                value=self.final_score,
            ),
        ]
```

### 7.3 평가 파이프라인 구현

```python
# evaluation/pipeline.py
import asyncio
import random
from datetime import datetime
from typing import Any, Literal

import structlog

from yeji_ai.evaluation.models import (
    EvaluationConfig,
    EvaluationMetadata,
    EvaluationReport,
)
from yeji_ai.evaluation.structural import (
    SchemaChecker,
    FieldEvaluator,
    CodeValidator,
)
from yeji_ai.evaluation.content import GEvalJudge

logger = structlog.get_logger()


class EvaluationPipeline:
    """G-Eval 평가 파이프라인

    LLM 응답의 구조적 품질과 내용 품질을 종합 평가합니다.

    사용 예시:
        pipeline = EvaluationPipeline(config)
        report = await pipeline.evaluate(llm_response, "eastern")
    """

    def __init__(
        self,
        config: EvaluationConfig,
        internal_judge: GEvalJudge,
        external_judge: GEvalJudge | None = None,
    ) -> None:
        """
        Args:
            config: 평가 설정
            internal_judge: 내부 LLM Judge (Qwen3)
            external_judge: 외부 LLM Judge (Claude, 선택)
        """
        self.config = config
        self.internal_judge = internal_judge
        self.external_judge = external_judge

        # 구조적 평가기
        self.schema_checker = SchemaChecker()
        self.field_evaluator = FieldEvaluator()
        self.code_validator = CodeValidator()

    async def evaluate(
        self,
        data: dict[str, Any],
        fortune_type: Literal["eastern", "western"],
    ) -> EvaluationReport:
        """LLM 응답 평가 수행

        Args:
            data: LLM 응답 JSON
            fortune_type: 운세 타입

        Returns:
            평가 리포트
        """
        start_time = datetime.utcnow()

        # Layer 1: 구조적 평가 (항상 실행)
        structural_result = self._evaluate_structural(data, fortune_type)

        # Layer 2: 내용 품질 평가 (설정에 따라)
        content_result = None
        judge_model = "none"

        if self.config.enable_content_eval:
            # 외부 검증 여부 결정 (확률적)
            use_external = (
                self.external_judge is not None
                and random.random() < self.config.external_validation_rate
            )

            judge = self.external_judge if use_external else self.internal_judge
            judge_model = "external" if use_external else "internal"

            content_result = await self._evaluate_content(data, fortune_type, judge)

        # 점수 집계
        final_score = self._aggregate_scores(structural_result, content_result)
        grade = self._calculate_grade(final_score)

        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        logger.info(
            "evaluation_complete",
            fortune_type=fortune_type,
            final_score=final_score,
            grade=grade,
            judge_model=judge_model,
            latency_ms=round(latency_ms, 2),
        )

        return EvaluationReport(
            metadata=EvaluationMetadata(
                fortune_type=fortune_type,
                evaluated_at=start_time,
                judge_model=judge_model,
                latency_ms=latency_ms,
            ),
            structural=structural_result,
            content=content_result,
            final_score=final_score,
            grade=grade,
        )

    def _evaluate_structural(
        self,
        data: dict[str, Any],
        fortune_type: str,
    ) -> StructuralEvaluationResult:
        """구조적 평가"""
        schema_compliance = self.schema_checker.check(data, fortune_type)
        field_completeness = self.field_evaluator.evaluate(data, fortune_type)
        code_validity = self.code_validator.validate(data, fortune_type)

        return StructuralEvaluationResult(
            schema_compliance=schema_compliance,
            field_completeness=field_completeness,
            code_validity=code_validity,
        )

    async def _evaluate_content(
        self,
        data: dict[str, Any],
        fortune_type: str,
        judge: GEvalJudge,
    ) -> ContentEvaluationResult:
        """내용 품질 평가 (G-Eval)"""
        return await judge.evaluate(data, fortune_type)

    def _aggregate_scores(
        self,
        structural: StructuralEvaluationResult,
        content: ContentEvaluationResult | None,
    ) -> float:
        """점수 집계"""
        score = structural.weighted_score

        if content is not None:
            score += content.weighted_score
        else:
            # 내용 평가 비활성화 시 구조적 점수만으로 정규화
            score = score / 0.7 * 1.0  # 70% → 100%

        return min(100, max(0, score))

    def _calculate_grade(self, score: float) -> str:
        """등급 계산"""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"
```

### 7.4 기존 시스템과의 통합

```python
# services/fortune_generator.py (수정)
class FortuneGenerator:
    """운세 생성 서비스"""

    def __init__(
        self,
        llm_provider: LLMProvider,
        postprocessor: ResponsePostprocessor,
        evaluation_pipeline: EvaluationPipeline | None = None,  # 추가
    ) -> None:
        self.llm_provider = llm_provider
        self.postprocessor = postprocessor
        self.evaluation_pipeline = evaluation_pipeline

    async def generate(
        self,
        request: FortuneRequest,
    ) -> FortuneResponse:
        """운세 생성"""

        # 1. LLM 호출
        raw_response = await self.llm_provider.generate(...)

        # 2. 후처리
        processed = self.postprocessor.process(raw_response)

        # 3. Pydantic 검증
        try:
            validated = UserFortune.model_validate(processed)
            success = True
        except ValidationError as e:
            validated = processed
            success = False

        # 4. G-Eval 평가 (비동기, 백그라운드)
        if self.evaluation_pipeline is not None:
            asyncio.create_task(
                self._evaluate_and_log(processed, request.fortune_type)
            )

        return FortuneResponse(
            success=success,
            data=validated,
            ...
        )

    async def _evaluate_and_log(
        self,
        data: dict,
        fortune_type: str,
    ) -> None:
        """평가 수행 및 로깅 (백그라운드)"""
        try:
            report = await self.evaluation_pipeline.evaluate(data, fortune_type)

            # 메트릭 기록
            for metric in report.to_prometheus_metrics():
                metrics_collector.record(metric)

            # 저품질 응답 로깅
            if report.grade in ("D", "F"):
                logger.warning(
                    "low_quality_response",
                    fortune_type=fortune_type,
                    final_score=report.final_score,
                    grade=report.grade,
                )
        except Exception as e:
            logger.error(
                "evaluation_failed",
                error=str(e),
            )
```

### 7.5 구현 로드맵

| 단계 | 내용 | 예상 기간 | 우선순위 |
|------|------|----------|----------|
| 1 | 구조적 평가 구현 (Schema, Field, Code) | 2일 | P0 |
| 2 | G-Eval 프롬프트 템플릿 작성 | 1일 | P0 |
| 3 | 내부 Judge 구현 (Qwen3) | 2일 | P1 |
| 4 | 외부 Judge 통합 (Claude API) | 1일 | P2 |
| 5 | 평가 파이프라인 통합 | 2일 | P1 |
| 6 | 메트릭 대시보드 연동 | 1일 | P2 |
| 7 | 테스트 및 캘리브레이션 | 2일 | P1 |

**총 예상 기간**: 11일

---

## 8. 참조

### 8.1 학술 참조

1. **G-Eval 원논문**: Liu et al. (2023). "G-Eval: NLG Evaluation using GPT-4 with Better Human Alignment"
2. **LLM-as-Judge**: Zheng et al. (2023). "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena"
3. **DeepEval Framework**: Confident AI (2025). "DeepEval: The Open-Source LLM Evaluation Framework"

### 8.2 프로젝트 문서

| 문서 | 경로 | 설명 |
|------|------|------|
| LLM 후처리 PRD | `docs/prd/llm-response-postprocessor.md` | 후처리 시스템 설계 |
| 도메인 코드 정의 | `src/yeji_ai/models/enums/domain_codes.py` | 유효 코드 목록 |
| 검증 모니터링 | `src/yeji_ai/services/validation_monitor.py` | 현재 모니터링 시스템 |
| 메트릭 모델 | `src/yeji_ai/models/metrics.py` | Prometheus 메트릭 |

### 8.3 외부 도구

| 도구 | URL | 설명 |
|------|-----|------|
| DeepEval | https://deepeval.com | G-Eval 구현체 제공 |
| LangSmith | https://langsmith.com | LLM 평가 플랫폼 |
| Confident AI | https://confident-ai.com | LLM 테스팅 도구 |

---

## 변경 이력

| 버전 | 날짜 | 변경 내용 | 작성자 |
|------|------|----------|--------|
| 1.0.0 | 2026-01-30 | 초기 버전 | YEJI AI팀 |

---

> **Note**: 이 설계 문서는 G-Eval 논문과 2026년 최신 LLM 평가 방법론을 기반으로 작성되었습니다.
> 하이브리드 접근(옵션 C)을 권장하며, 비용과 품질의 균형을 고려하여 설계되었습니다.
