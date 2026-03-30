# 티키타카 요약 화면 스키마 설계

> **문서 버전**: 1.0.0
> **작성일**: 2026-01-30
> **상태**: 설계 (Design)
> **담당팀**: SSAFY YEJI AI팀
> **관련 문서**: [tikitaka-schema-v2.md](../prd/tikitaka-schema-v2.md)

---

## 목차

1. [개요](#1-개요)
2. [설계 목표](#2-설계-목표)
3. [요약 화면 구성 요소](#3-요약-화면-구성-요소)
4. [스키마 설계](#4-스키마-설계)
5. [캐릭터별 메시지 구조](#5-캐릭터별-메시지-구조)
6. [합의점/차이점 분석](#6-합의점차이점-분석)
7. [프론트엔드 연동 가이드](#7-프론트엔드-연동-가이드)
8. [SSE 이벤트 설계](#8-sse-이벤트-설계)
9. [LLM 프롬프트 가이드](#9-llm-프롬프트-가이드)
10. [참조 문서](#10-참조-문서)

---

## 1. 개요

### 1.1 배경

티키타카 대화가 종료된 후 사용자에게 대화 전체의 핵심 내용을 요약하여 제공해야 합니다. 이 문서는 요약 화면에 필요한 데이터 스키마를 정의합니다.

### 1.2 요약 화면의 목적

- **회고**: 대화에서 나온 핵심 인사이트를 한눈에 파악
- **비교**: 동양(소이설)과 서양(스텔라) 관점의 공통점과 차이점 이해
- **액션**: 최종 조언을 통해 사용자가 실생활에 적용할 수 있는 가이드 제공
- **저장**: 요약 결과를 저장하여 나중에 다시 확인 가능

### 1.3 영향 범위

| 구성요소 | 변경 내용 |
|----------|-----------|
| AI 서버 | 요약 스키마 추가, 요약 생성 로직 구현 |
| 프론트엔드 | 요약 화면 UI 컴포넌트 개발 |
| 백엔드 | 요약 데이터 저장 API 추가 |

---

## 2. 설계 목표

### 2.1 핵심 목표

1. **완결성**: 대화 전체를 아우르는 종합적인 요약 제공
2. **구조화**: 캐릭터별, 카테고리별로 명확하게 구조화된 정보
3. **실용성**: 사용자가 바로 활용할 수 있는 구체적인 조언
4. **일관성**: tikitaka-schema-v2와 일관된 코드 체계 사용

### 2.2 비목표 (Out of Scope)

- 이미지/차트 자동 생성
- 외부 공유 기능
- 다국어 지원

---

## 3. 요약 화면 구성 요소

### 3.1 화면 구성

```
┌────────────────────────────────────────────────────────────┐
│  [헤더] 대화 요약                                           │
│  ────────────────────────────────────────────────────────  │
│                                                            │
│  [1] 대화 하이라이트 (주요 인사이트)                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ - "병화 일간으로 타고난 리더십이 있습니다"              │  │
│  │ - "양자리 태양과 사주 모두 행동력이 뛰어남을 나타냅니다" │  │
│  │ - "2026년 상반기 직장운이 특히 좋습니다"               │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                            │
│  [2] 캐릭터별 핵심 메시지                                    │
│  ┌─────────────────────┐  ┌─────────────────────┐          │
│  │ [소이설 아바타]     │  │ [스텔라 아바타]     │          │
│  │ 동양 사주 관점      │  │ 서양 점성술 관점    │          │
│  │ ─────────────────── │  │ ─────────────────── │          │
│  │ "병화 일간의 밝은   │  │ "양자리 태양의      │          │
│  │  기운이 올해..."    │  │  추진력이..."       │          │
│  └─────────────────────┘  └─────────────────────┘          │
│                                                            │
│  [3] 합의점 / 차이점                                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ ✓ 합의점                                              │  │
│  │   - 리더십과 추진력이 핵심 특성                        │  │
│  │   - 상반기 직장운 긍정적                              │  │
│  │                                                        │  │
│  │ ◇ 차이점                                              │  │
│  │   - 연애운: 소이설(적극적) vs 스텔라(신중히)           │  │
│  │   - 건강: 소이설(화기주의) vs 스텔라(스트레스관리)     │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                            │
│  [4] 최종 조언                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ "당신의 리더십을 믿고 올해 상반기에는 적극적으로       │  │
│  │  도전하세요. 단, 건강 관리에 신경 쓰면서 균형을        │  │
│  │  유지하는 것이 중요합니다."                            │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                            │
│  [CTA 버튼]                                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  저장하기   │  │ 다시 대화   │  │   홈으로    │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└────────────────────────────────────────────────────────────┘
```

### 3.2 구성 요소 상세

| 구성 요소 | 설명 | 필수 여부 |
|-----------|------|-----------|
| 대화 하이라이트 | 대화 중 가장 중요한 인사이트 3~5개 | 필수 |
| 캐릭터별 핵심 메시지 | 소이설/스텔라 각각의 핵심 메시지 | 필수 |
| 합의점 | 두 캐릭터가 동의한 내용 | 필수 |
| 차이점 | 두 캐릭터의 의견이 다른 부분 | 선택 |
| 최종 조언 | 종합적인 실천 가이드 | 필수 |
| 세션 메타데이터 | 대화 일시, 턴 수, 주제 등 | 선택 |

---

## 4. 스키마 설계

### 4.1 TypeScript 스키마

```typescript
// ============================================================
// 요약 화면 Enum 정의
// ============================================================

/**
 * 하이라이트 카테고리
 */
type HighlightCategory =
  | "PERSONALITY"      // 성격/기질
  | "CAREER"           // 직장/사업운
  | "LOVE"             // 연애/결혼운
  | "WEALTH"           // 금전/재물운
  | "HEALTH"           // 건강운
  | "RELATIONSHIP"     // 대인관계
  | "TIMING"           // 시기/타이밍
  | "GENERAL";         // 일반/종합

/**
 * 인사이트 중요도
 */
type InsightPriority = "HIGH" | "MEDIUM" | "LOW";

/**
 * 조언 유형
 */
type AdviceType =
  | "DO"               // 하면 좋은 것
  | "AVOID"            // 피해야 할 것
  | "TIMING"           // 좋은 시기
  | "CAUTION";         // 주의사항

// ============================================================
// 상세 인터페이스
// ============================================================

/**
 * 대화 하이라이트 (주요 인사이트)
 */
interface Highlight {
  /** 고유 ID */
  highlight_id: string;

  /** 카테고리 */
  category: HighlightCategory;

  /** 인사이트 내용 */
  content: string;

  /** 출처 캐릭터 (합의인 경우 null) */
  source_character: CharacterCode | null;

  /** 중요도 */
  priority: InsightPriority;

  /** 관련 버블 ID 목록 (원본 대화 참조) */
  related_bubble_ids: string[];
}

/**
 * 캐릭터별 핵심 메시지
 */
interface CharacterSummary {
  /** 캐릭터 코드 */
  character: CharacterCode;

  /** 캐릭터 감정 (요약 시점) */
  emotion: EmotionCode;

  /** 핵심 해석 제목 */
  title: string;

  /** 핵심 메시지 (1~2문장) */
  key_message: string;

  /** 상세 해석 (선택적, 3~5문장) */
  detailed_interpretation?: string;

  /** 키워드 목록 */
  keywords: string[];

  /** 분석 기반 정보 */
  analysis_basis: AnalysisBasis;
}

/**
 * 분석 기반 정보
 */
interface AnalysisBasis {
  /** 동양: 사주 정보, 서양: 별자리 정보 */
  type: "SAJU" | "ASTROLOGY";

  /** 핵심 요소 (예: "병화 일간", "양자리 태양") */
  key_element: string;

  /** 추가 정보 */
  details?: string;
}

/**
 * 합의점
 */
interface ConsensusPoint {
  /** 고유 ID */
  point_id: string;

  /** 합의 주제 */
  topic: string;

  /** 합의 내용 */
  content: string;

  /** 카테고리 */
  category: HighlightCategory;

  /** 소이설의 표현 */
  eastern_expression: string;

  /** 스텔라의 표현 */
  western_expression: string;
}

/**
 * 차이점
 */
interface DifferencePoint {
  /** 고유 ID */
  point_id: string;

  /** 차이점 주제 */
  topic: string;

  /** 카테고리 */
  category: HighlightCategory;

  /** 소이설의 의견 */
  eastern_opinion: OpinionDetail;

  /** 스텔라의 의견 */
  western_opinion: OpinionDetail;

  /** 차이 설명 (선택적) */
  explanation?: string;
}

/**
 * 의견 상세
 */
interface OpinionDetail {
  /** 핵심 주장 */
  stance: string;

  /** 근거 */
  reasoning?: string;
}

/**
 * 최종 조언
 */
interface FinalAdvice {
  /** 종합 메시지 (2~3문장) */
  main_message: string;

  /** 구체적 조언 목록 */
  action_items: ActionItem[];

  /** 강조 문구 (선택적, UI 하이라이트용) */
  emphasis?: string;
}

/**
 * 액션 아이템
 */
interface ActionItem {
  /** 조언 유형 */
  type: AdviceType;

  /** 조언 내용 */
  content: string;

  /** 관련 시기 (선택적) */
  timing?: string;
}

/**
 * 세션 메타데이터
 */
interface SummaryMetadata {
  /** 세션 ID */
  session_id: string;

  /** 대화 시작 시간 */
  started_at: string;

  /** 대화 종료 시간 */
  ended_at: string;

  /** 총 턴 수 */
  total_turns: number;

  /** 총 버블 수 */
  total_bubbles: number;

  /** 대화 주제 목록 */
  topics_discussed: string[];

  /** 프리미엄 여부 */
  is_premium: boolean;
}

// ============================================================
// 최종 요약 응답 스키마
// ============================================================

/**
 * 티키타카 요약 응답
 */
interface TikitakaSummaryResponse {
  /** 스키마 버전 */
  schema_version: "2.0.0";

  /** 응답 타입 */
  response_type: "SUMMARY";

  /** 세션 메타데이터 */
  metadata: SummaryMetadata;

  /** 대화 하이라이트 (3~5개) */
  highlights: Highlight[];

  /** 캐릭터별 요약 */
  character_summaries: {
    eastern: CharacterSummary;   // 소이설
    western: CharacterSummary;   // 스텔라
  };

  /** 합의점 목록 */
  consensus_points: ConsensusPoint[];

  /** 차이점 목록 (선택적) */
  difference_points?: DifferencePoint[];

  /** 최종 조언 */
  final_advice: FinalAdvice;

  /** UI 힌트 (선택적) */
  ui_hints?: SummaryUIHints;
}

/**
 * 요약 UI 힌트
 */
interface SummaryUIHints {
  /** 하이라이트 애니메이션 */
  highlight_animation?: "fade" | "slide" | "none";

  /** 캐릭터 강조 */
  emphasize_character?: CharacterCode;

  /** CTA 버튼 표시 */
  show_cta_buttons: boolean;

  /** 저장 가능 여부 */
  can_save: boolean;

  /** 공유 가능 여부 (향후 확장) */
  can_share: boolean;
}
```

### 4.2 Pydantic V2 스키마 (Python)

```python
"""티키타카 요약 스키마

대화 종료 후 표시되는 요약 화면의 데이터 스키마
"""

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


# ============================================================
# Enum 정의
# ============================================================

class HighlightCategory(str, Enum):
    """하이라이트 카테고리"""
    PERSONALITY = "PERSONALITY"      # 성격/기질
    CAREER = "CAREER"                # 직장/사업운
    LOVE = "LOVE"                    # 연애/결혼운
    WEALTH = "WEALTH"                # 금전/재물운
    HEALTH = "HEALTH"                # 건강운
    RELATIONSHIP = "RELATIONSHIP"    # 대인관계
    TIMING = "TIMING"                # 시기/타이밍
    GENERAL = "GENERAL"              # 일반/종합


class InsightPriority(str, Enum):
    """인사이트 중요도"""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class AdviceType(str, Enum):
    """조언 유형"""
    DO = "DO"              # 하면 좋은 것
    AVOID = "AVOID"        # 피해야 할 것
    TIMING = "TIMING"      # 좋은 시기
    CAUTION = "CAUTION"    # 주의사항


class AnalysisType(str, Enum):
    """분석 유형"""
    SAJU = "SAJU"            # 동양 사주
    ASTROLOGY = "ASTROLOGY"  # 서양 점성술


# ============================================================
# 상세 모델
# ============================================================

class AnalysisBasis(BaseModel):
    """분석 기반 정보"""
    type: AnalysisType = Field(..., description="분석 유형")
    key_element: str = Field(..., description="핵심 요소 (예: 병화 일간, 양자리 태양)")
    details: str | None = Field(None, description="추가 정보")


class Highlight(BaseModel):
    """대화 하이라이트 (주요 인사이트)"""
    highlight_id: str = Field(..., description="고유 ID")
    category: HighlightCategory = Field(..., description="카테고리")
    content: str = Field(..., description="인사이트 내용")
    source_character: str | None = Field(
        None,
        description="출처 캐릭터 (SOISEOL, STELLA, 합의인 경우 null)"
    )
    priority: InsightPriority = Field(InsightPriority.MEDIUM, description="중요도")
    related_bubble_ids: list[str] = Field(
        default_factory=list,
        description="관련 버블 ID 목록"
    )


class CharacterSummary(BaseModel):
    """캐릭터별 핵심 메시지"""
    character: str = Field(..., description="캐릭터 코드 (SOISEOL, STELLA)")
    emotion: str = Field("NEUTRAL", description="캐릭터 감정")
    title: str = Field(..., description="핵심 해석 제목")
    key_message: str = Field(..., description="핵심 메시지 (1~2문장)")
    detailed_interpretation: str | None = Field(
        None,
        description="상세 해석 (3~5문장)"
    )
    keywords: list[str] = Field(default_factory=list, description="키워드 목록")
    analysis_basis: AnalysisBasis = Field(..., description="분석 기반 정보")


class ConsensusPoint(BaseModel):
    """합의점"""
    point_id: str = Field(..., description="고유 ID")
    topic: str = Field(..., description="합의 주제")
    content: str = Field(..., description="합의 내용")
    category: HighlightCategory = Field(..., description="카테고리")
    eastern_expression: str = Field(..., description="소이설의 표현")
    western_expression: str = Field(..., description="스텔라의 표현")


class OpinionDetail(BaseModel):
    """의견 상세"""
    stance: str = Field(..., description="핵심 주장")
    reasoning: str | None = Field(None, description="근거")


class DifferencePoint(BaseModel):
    """차이점"""
    point_id: str = Field(..., description="고유 ID")
    topic: str = Field(..., description="차이점 주제")
    category: HighlightCategory = Field(..., description="카테고리")
    eastern_opinion: OpinionDetail = Field(..., description="소이설의 의견")
    western_opinion: OpinionDetail = Field(..., description="스텔라의 의견")
    explanation: str | None = Field(None, description="차이 설명")


class ActionItem(BaseModel):
    """액션 아이템"""
    type: AdviceType = Field(..., description="조언 유형")
    content: str = Field(..., description="조언 내용")
    timing: str | None = Field(None, description="관련 시기")


class FinalAdvice(BaseModel):
    """최종 조언"""
    main_message: str = Field(..., description="종합 메시지 (2~3문장)")
    action_items: list[ActionItem] = Field(
        default_factory=list,
        description="구체적 조언 목록"
    )
    emphasis: str | None = Field(None, description="강조 문구")


class SummaryMetadata(BaseModel):
    """세션 메타데이터"""
    session_id: str = Field(..., description="세션 ID")
    started_at: datetime = Field(..., description="대화 시작 시간")
    ended_at: datetime = Field(..., description="대화 종료 시간")
    total_turns: int = Field(..., ge=0, description="총 턴 수")
    total_bubbles: int = Field(..., ge=0, description="총 버블 수")
    topics_discussed: list[str] = Field(
        default_factory=list,
        description="대화 주제 목록"
    )
    is_premium: bool = Field(False, description="프리미엄 여부")


class CharacterSummaries(BaseModel):
    """캐릭터별 요약"""
    eastern: CharacterSummary = Field(..., description="소이설 요약")
    western: CharacterSummary = Field(..., description="스텔라 요약")


class SummaryUIHints(BaseModel):
    """요약 UI 힌트"""
    highlight_animation: Literal["fade", "slide", "none"] | None = Field(
        "fade",
        description="하이라이트 애니메이션"
    )
    emphasize_character: str | None = Field(None, description="캐릭터 강조")
    show_cta_buttons: bool = Field(True, description="CTA 버튼 표시")
    can_save: bool = Field(True, description="저장 가능 여부")
    can_share: bool = Field(False, description="공유 가능 여부")


# ============================================================
# 최종 응답 모델
# ============================================================

class TikitakaSummaryResponse(BaseModel):
    """티키타카 요약 응답"""
    schema_version: Literal["2.0.0"] = "2.0.0"
    response_type: Literal["SUMMARY"] = "SUMMARY"
    metadata: SummaryMetadata = Field(..., description="세션 메타데이터")
    highlights: list[Highlight] = Field(
        ...,
        min_length=1,
        max_length=5,
        description="대화 하이라이트 (3~5개)"
    )
    character_summaries: CharacterSummaries = Field(
        ...,
        description="캐릭터별 요약"
    )
    consensus_points: list[ConsensusPoint] = Field(
        default_factory=list,
        description="합의점 목록"
    )
    difference_points: list[DifferencePoint] | None = Field(
        None,
        description="차이점 목록"
    )
    final_advice: FinalAdvice = Field(..., description="최종 조언")
    ui_hints: SummaryUIHints | None = Field(None, description="UI 힌트")

    class Config:
        json_schema_extra = {
            "example": {
                "schema_version": "2.0.0",
                "response_type": "SUMMARY",
                "metadata": {
                    "session_id": "abc123",
                    "started_at": "2026-01-30T15:30:00Z",
                    "ended_at": "2026-01-30T15:45:00Z",
                    "total_turns": 8,
                    "total_bubbles": 12,
                    "topics_discussed": ["성격", "직장운", "연애운"],
                    "is_premium": False,
                },
                "highlights": [
                    {
                        "highlight_id": "h_001",
                        "category": "PERSONALITY",
                        "content": "병화 일간과 양자리 태양 모두 리더십이 강합니다",
                        "source_character": None,
                        "priority": "HIGH",
                        "related_bubble_ids": ["b_003", "b_004"],
                    }
                ],
                "character_summaries": {
                    "eastern": {
                        "character": "SOISEOL",
                        "emotion": "HAPPY",
                        "title": "밝은 리더의 기운",
                        "key_message": "병화 일간의 따뜻하고 밝은 기운이 있어요.",
                        "keywords": ["병화", "리더십", "열정"],
                        "analysis_basis": {
                            "type": "SAJU",
                            "key_element": "병화 일간",
                        },
                    },
                    "western": {
                        "character": "STELLA",
                        "emotion": "CONFIDENT",
                        "title": "행동하는 선구자",
                        "key_message": "양자리 태양의 추진력이 돋보여.",
                        "keywords": ["양자리", "추진력", "행동파"],
                        "analysis_basis": {
                            "type": "ASTROLOGY",
                            "key_element": "양자리 태양",
                        },
                    },
                },
                "consensus_points": [
                    {
                        "point_id": "c_001",
                        "topic": "리더십",
                        "content": "타고난 리더의 기질을 가지고 있습니다",
                        "category": "PERSONALITY",
                        "eastern_expression": "병화의 밝은 기운으로 주변을 이끌어요",
                        "western_expression": "양자리의 선구자적 특성이 있어",
                    }
                ],
                "final_advice": {
                    "main_message": "리더십을 발휘하되 균형을 유지하세요.",
                    "action_items": [
                        {
                            "type": "DO",
                            "content": "상반기에 적극적으로 도전하세요",
                            "timing": "2026년 상반기",
                        }
                    ],
                },
            }
        }
```

---

## 5. 캐릭터별 메시지 구조

### 5.1 소이설 (동양 사주) 요약 구조

| 항목 | 설명 | 예시 |
|------|------|------|
| title | 핵심 해석 제목 | "밝은 리더의 기운" |
| key_message | 핵심 메시지 | "병화 일간의 따뜻하고 밝은 기운이 있어요~" |
| keywords | 키워드 | ["병화", "리더십", "열정", "화기"] |
| analysis_basis | 분석 기반 | type: SAJU, key_element: "병화 일간" |

### 5.2 스텔라 (서양 점성술) 요약 구조

| 항목 | 설명 | 예시 |
|------|------|------|
| title | 핵심 해석 제목 | "행동하는 선구자" |
| key_message | 핵심 메시지 | "양자리 태양의 추진력이 확실히 돋보여." |
| keywords | 키워드 | ["양자리", "태양", "추진력", "화성"] |
| analysis_basis | 분석 기반 | type: ASTROLOGY, key_element: "양자리 태양" |

### 5.3 캐릭터 말투 가이드

#### 소이설 (따뜻한 온미녀)

```
- 문장 종결: "~에요", "~해요", "~네요~"
- 감탄사: "어머", "와~", "후훗"
- 특징: 따뜻하고 친근한 느낌, 물결표(~) 자주 사용
- 예시: "정말 좋은 기운이 느껴져요~ 올해는 기회가 많을 거예요!"
```

#### 스텔라 (쿨한 냉미녀)

```
- 문장 종결: "~해", "~야", "~군"
- 감탄사: "...", "ㅋ", "흥"
- 특징: 간결하고 직설적, 마침표로 끊어 말함
- 예시: "확실해. 행성 배치가 좋아. 도전해도 돼."
```

---

## 6. 합의점/차이점 분석

### 6.1 합의점 추출 기준

두 캐릭터가 **동일한 결론**에 도달한 경우:

| 합의 유형 | 설명 | 예시 |
|-----------|------|------|
| 성격 합의 | 같은 성격 특성 언급 | "둘 다 리더십이 강하다고 봄" |
| 운세 합의 | 같은 시기에 같은 운 예측 | "상반기 직장운 좋음" |
| 조언 합의 | 같은 방향의 조언 | "적극적으로 행동하라" |

### 6.2 차이점 추출 기준

두 캐릭터가 **다른 의견**을 제시한 경우:

| 차이 유형 | 설명 | 예시 |
|-----------|------|------|
| 관점 차이 | 같은 현상을 다르게 해석 | 화기: 소이설(열정) vs 스텔라(충동) |
| 조언 차이 | 다른 방향의 조언 | 연애: 소이설(적극적) vs 스텔라(신중히) |
| 강조점 차이 | 다른 부분을 중요시 | 소이설(관계) vs 스텔라(커리어) |

### 6.3 합의/차이 판단 로직

```
1. 대화 버블에서 CONSENSUS, DEBATE 타입 추출
2. 키워드 매칭으로 주제별 의견 분류
3. 동일 주제에 대한 의견 비교
4. 유사도 기반 합의/차이 판단
   - 유사도 > 0.7: 합의
   - 유사도 < 0.3: 차이
   - 0.3 ~ 0.7: 부분 합의 (합의점으로 분류)
```

---

## 7. 프론트엔드 연동 가이드

### 7.1 API 엔드포인트

```
GET  /api/v2/fortune/tikitaka/summary/{session_id}
POST /api/v2/fortune/tikitaka/summary/{session_id}/save
```

### 7.2 React 컴포넌트 구조

```typescript
// 요약 화면 컴포넌트 구조
function TikitakaSummary({ sessionId }: Props) {
  return (
    <SummaryContainer>
      {/* 헤더 */}
      <SummaryHeader metadata={metadata} />

      {/* 하이라이트 */}
      <HighlightSection highlights={highlights} />

      {/* 캐릭터별 요약 */}
      <CharacterSummarySection
        eastern={characterSummaries.eastern}
        western={characterSummaries.western}
      />

      {/* 합의점/차이점 */}
      <ComparisonSection
        consensus={consensusPoints}
        differences={differencePoints}
      />

      {/* 최종 조언 */}
      <FinalAdviceSection advice={finalAdvice} />

      {/* CTA 버튼 */}
      <CTAButtons
        onSave={handleSave}
        onRetry={handleRetry}
        onHome={handleHome}
      />
    </SummaryContainer>
  );
}
```

### 7.3 하이라이트 카테고리별 아이콘

| 카테고리 | 아이콘 | 색상 |
|----------|--------|------|
| PERSONALITY | 사람 | 파랑 |
| CAREER | 서류가방 | 회색 |
| LOVE | 하트 | 분홍 |
| WEALTH | 동전 | 금색 |
| HEALTH | 하트(의료) | 녹색 |
| RELATIONSHIP | 사람들 | 보라 |
| TIMING | 시계 | 주황 |
| GENERAL | 별 | 노랑 |

### 7.4 조언 유형별 스타일

| 조언 유형 | 아이콘 | 배경색 | 테두리 |
|-----------|--------|--------|--------|
| DO | 체크 | 연한 녹색 | 녹색 |
| AVOID | X | 연한 빨강 | 빨강 |
| TIMING | 달력 | 연한 파랑 | 파랑 |
| CAUTION | 느낌표 | 연한 노랑 | 노랑 |

---

## 8. SSE 이벤트 설계

### 8.1 요약 생성 SSE 이벤트 타입

대화 종료 후 요약을 실시간으로 스트리밍하기 위한 SSE 이벤트:

```typescript
type SummarySSEEventType =
  | "summary_start"        // 요약 생성 시작
  | "metadata"             // 메타데이터 전송
  | "highlight"            // 하이라이트 항목
  | "character_summary"    // 캐릭터별 요약
  | "consensus"            // 합의점
  | "difference"           // 차이점
  | "final_advice"         // 최종 조언
  | "summary_complete"     // 요약 완료
  | "error";               // 에러
```

### 8.2 SSE 이벤트 시퀀스

```
# 1. 요약 시작
event: summary_start
data: {"session_id": "abc123"}

# 2. 메타데이터
event: metadata
data: {"started_at": "...", "ended_at": "...", "total_turns": 8}

# 3. 하이라이트 (순차 전송)
event: highlight
data: {"highlight_id": "h_001", "category": "PERSONALITY", "content": "..."}

event: highlight
data: {"highlight_id": "h_002", "category": "CAREER", "content": "..."}

# 4. 캐릭터별 요약
event: character_summary
data: {"character": "SOISEOL", "title": "...", "key_message": "..."}

event: character_summary
data: {"character": "STELLA", "title": "...", "key_message": "..."}

# 5. 합의점
event: consensus
data: {"point_id": "c_001", "topic": "리더십", "content": "..."}

# 6. 차이점 (있는 경우)
event: difference
data: {"point_id": "d_001", "topic": "연애운", ...}

# 7. 최종 조언
event: final_advice
data: {"main_message": "...", "action_items": [...]}

# 8. 완료
event: summary_complete
data: {"status": "success"}
```

---

## 9. LLM 프롬프트 가이드

### 9.1 요약 생성 프롬프트 템플릿

```python
SUMMARY_PROMPT_TEMPLATE = """[BAZI] 당신은 YEJI(예지) AI입니다.

## 역할
티키타카 대화를 분석하여 요약을 생성합니다.

## 입력
### 대화 버블 목록
{bubbles_json}

### 동양 분석 결과
{eastern_analysis}

### 서양 분석 결과
{western_analysis}

## 출력 형식
다음 XML 형식으로 요약을 생성하세요:

<summary>
  <highlights>
    <highlight category="CATEGORY" priority="HIGH|MEDIUM|LOW">
      인사이트 내용
    </highlight>
    ...
  </highlights>

  <character_summaries>
    <character name="SOISEOL" emotion="EMOTION">
      <title>핵심 제목</title>
      <key_message>핵심 메시지</key_message>
      <keywords>키워드1, 키워드2, 키워드3</keywords>
    </character>
    <character name="STELLA" emotion="EMOTION">
      <title>핵심 제목</title>
      <key_message>핵심 메시지</key_message>
      <keywords>키워드1, 키워드2, 키워드3</keywords>
    </character>
  </character_summaries>

  <consensus_points>
    <point topic="주제" category="CATEGORY">
      <content>합의 내용</content>
      <eastern>소이설 표현</eastern>
      <western>스텔라 표현</western>
    </point>
    ...
  </consensus_points>

  <difference_points>
    <point topic="주제" category="CATEGORY">
      <eastern stance="주장">근거</eastern>
      <western stance="주장">근거</western>
    </point>
    ...
  </difference_points>

  <final_advice>
    <main_message>종합 메시지</main_message>
    <action type="DO|AVOID|TIMING|CAUTION" timing="시기">조언 내용</action>
    ...
  </final_advice>
</summary>

## 주의사항
1. 하이라이트는 3~5개로 제한
2. 캐릭터 말투를 유지 (소이설: 따뜻, 스텔라: 쿨)
3. 최종 조언은 실천 가능한 구체적 내용으로
4. 합의점이 없으면 생략 가능
5. 차이점이 없으면 생략 가능

<summary>
"""
```

### 9.2 요약 품질 기준

| 항목 | 기준 | 검증 방법 |
|------|------|-----------|
| 완결성 | 대화의 핵심 내용 누락 없음 | 주제 커버리지 확인 |
| 정확성 | 원본 대화와 일치 | 인용 검증 |
| 간결성 | 불필요한 반복 없음 | 길이 제한 |
| 실용성 | 구체적 조언 포함 | 액션 아이템 존재 |
| 균형성 | 두 캐릭터 비중 균등 | 문장 수 비교 |

---

## 10. 참조 문서

### 10.1 내부 문서

| 문서 | 경로 | 설명 |
|------|------|------|
| 티키타카 스키마 V2 PRD | `ai/docs/prd/tikitaka-schema-v2.md` | 대화 스키마 정의 |
| LLM 후처리 PRD | `ai/docs/prd/llm-response-postprocessor.md` | LLM 응답 후처리 |
| 프롬프트 최적화 | `ai/docs/prd/prompt-optimization-system.md` | 프롬프트 설계 |

### 10.2 현재 구현 파일

| 파일 | 경로 | 설명 |
|------|------|------|
| 티키타카 서비스 | `ai/src/yeji_ai/services/tikitaka_service.py` | 비즈니스 로직 |
| 채팅 모델 | `ai/src/yeji_ai/models/fortune/chat.py` | 기존 스키마 |
| 도메인 코드 | `ai/src/yeji_ai/models/enums/` | Enum 정의 |

---

## 변경 이력

| 버전 | 날짜 | 변경 내용 | 작성자 |
|------|------|----------|--------|
| 1.0.0 | 2026-01-30 | 초기 버전 | YEJI AI팀 |

---

## 부록

### A. 전체 응답 예시

```json
{
  "schema_version": "2.0.0",
  "response_type": "SUMMARY",
  "metadata": {
    "session_id": "abc123",
    "started_at": "2026-01-30T15:30:00Z",
    "ended_at": "2026-01-30T15:45:00Z",
    "total_turns": 8,
    "total_bubbles": 12,
    "topics_discussed": ["성격", "직장운", "연애운"],
    "is_premium": false
  },
  "highlights": [
    {
      "highlight_id": "h_001",
      "category": "PERSONALITY",
      "content": "병화 일간과 양자리 태양 모두 타고난 리더십을 나타냅니다",
      "source_character": null,
      "priority": "HIGH",
      "related_bubble_ids": ["b_003", "b_004", "b_005"]
    },
    {
      "highlight_id": "h_002",
      "category": "CAREER",
      "content": "2026년 상반기는 직장에서 인정받을 좋은 시기입니다",
      "source_character": null,
      "priority": "HIGH",
      "related_bubble_ids": ["b_007", "b_008"]
    },
    {
      "highlight_id": "h_003",
      "category": "LOVE",
      "content": "연애운에서 동양과 서양의 시각 차이가 있었습니다",
      "source_character": null,
      "priority": "MEDIUM",
      "related_bubble_ids": ["b_009", "b_010"]
    }
  ],
  "character_summaries": {
    "eastern": {
      "character": "SOISEOL",
      "emotion": "HAPPY",
      "title": "밝은 리더의 기운",
      "key_message": "병화 일간의 따뜻하고 밝은 기운이 올해 빛을 발할 거예요~ 특히 상반기에 좋은 기회가 많아요!",
      "detailed_interpretation": "병화는 태양처럼 밝고 따뜻한 에너지를 가지고 있어요. 주변 사람들에게 긍정적인 영향을 주는 타고난 리더의 기질이죠. 올해는 이 기운이 더욱 강해져서 직장에서 인정받을 기회가 많을 거예요. 다만 화기가 너무 강하면 건강에 주의해야 해요~",
      "keywords": ["병화", "리더십", "열정", "따뜻함", "화기"],
      "analysis_basis": {
        "type": "SAJU",
        "key_element": "병화 일간",
        "details": "년주 갑자, 월주 병인, 일주 병오, 시주 경신"
      }
    },
    "western": {
      "character": "STELLA",
      "emotion": "CONFIDENT",
      "title": "행동하는 선구자",
      "key_message": "양자리 태양의 추진력이 확실해. 올해 상반기, 망설이지 마.",
      "detailed_interpretation": "양자리 태양에 화성이 합을 이루고 있어. 행동력과 추진력이 남다르다는 뜻이야. 목성이 커리어 하우스를 지나가는 상반기가 특히 좋아. 다만 금성-토성 스퀘어 때문에 연애는 신중하게 접근하는 게 좋겠어.",
      "keywords": ["양자리", "태양", "화성", "추진력", "행동파"],
      "analysis_basis": {
        "type": "ASTROLOGY",
        "key_element": "양자리 태양",
        "details": "태양 양자리 15도, 달 물병자리, 상승 사자자리"
      }
    }
  },
  "consensus_points": [
    {
      "point_id": "c_001",
      "topic": "리더십",
      "content": "타고난 리더의 기질을 가지고 있으며, 주변에 긍정적 영향력을 발휘합니다",
      "category": "PERSONALITY",
      "eastern_expression": "병화의 밝은 기운으로 주변 사람들을 따뜻하게 이끌어요~",
      "western_expression": "양자리 태양의 선구자적 특성. 앞장서서 이끄는 타입이야."
    },
    {
      "point_id": "c_002",
      "topic": "2026년 상반기 직장운",
      "content": "상반기에 직장에서 좋은 기회가 찾아올 것입니다",
      "category": "CAREER",
      "eastern_expression": "올해 상반기 직장운이 아주 좋아요! 승진이나 인정받을 기회가 있어요~",
      "western_expression": "목성이 커리어 하우스 트랜짓 중. 상반기가 타이밍이야."
    }
  ],
  "difference_points": [
    {
      "point_id": "d_001",
      "topic": "연애 접근 방식",
      "category": "LOVE",
      "eastern_opinion": {
        "stance": "적극적으로 다가가세요",
        "reasoning": "올해 도화살이 들어와서 인연이 생길 수 있어요"
      },
      "western_opinion": {
        "stance": "신중하게 접근해",
        "reasoning": "금성-토성 스퀘어 때문에 급하게 진행하면 문제 생길 수 있어"
      },
      "explanation": "연애의 타이밍과 접근 방식에서 다른 의견이 있었습니다. 적극성과 신중함 사이에서 균형을 찾는 것이 좋겠습니다."
    }
  ],
  "final_advice": {
    "main_message": "당신의 타고난 리더십을 믿고 올해 상반기에는 적극적으로 도전하세요. 직장에서 좋은 기회가 찾아올 것입니다. 다만 연애에서는 급하게 진행하기보다 상대를 충분히 알아가는 시간을 가지세요.",
    "action_items": [
      {
        "type": "DO",
        "content": "상반기 직장에서 적극적으로 의견을 내고 프로젝트를 주도하세요",
        "timing": "2026년 1월~6월"
      },
      {
        "type": "TIMING",
        "content": "새로운 프로젝트 시작이나 이직 고려 시 3~4월이 좋습니다",
        "timing": "2026년 3~4월"
      },
      {
        "type": "CAUTION",
        "content": "연애는 급하게 진행하지 말고 상대를 충분히 파악한 후 결정하세요",
        "timing": "2026년 전반"
      },
      {
        "type": "AVOID",
        "content": "과로로 인한 건강 문제에 주의하세요. 충분한 휴식이 필요합니다",
        "timing": null
      }
    ],
    "emphasis": "상반기가 당신의 해입니다!"
  },
  "ui_hints": {
    "highlight_animation": "fade",
    "emphasize_character": null,
    "show_cta_buttons": true,
    "can_save": true,
    "can_share": false
  }
}
```

---

> **Note**: 이 설계 문서는 tikitaka-schema-v2.md PRD와 연계되어 대화 종료 후 요약 화면에 필요한 스키마를 정의합니다.
