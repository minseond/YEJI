"""인텐트 필터 모델 정의 (태스크 #98)

Guard 및 Intent 필터링 결과 스키마
"""

from pydantic import BaseModel, Field

from yeji_ai.models.enums.intent import (
    FilterAction,
    GuardLabel,
    IntentCategory,
    MaliciousCategory,
)


class GuardResult(BaseModel):
    """프롬프트 가드 결과

    LLM 또는 GPU 기반 악성 프롬프트 탐지 결과를 담습니다.
    """

    label: GuardLabel = Field(..., description="판정 라벨 (benign/malicious)")
    is_malicious: bool = Field(..., description="악성 여부 (label == malicious)")
    score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="악성 확률 점수 (0.0~1.0)",
    )
    category: MaliciousCategory | None = Field(
        None,
        description="악성 세부 카테고리 (악성인 경우만)",
    )
    latency_ms: float = Field(..., ge=0.0, description="처리 시간 (ms)")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "label": "benign",
                    "is_malicious": False,
                    "score": 0.05,
                    "category": None,
                    "latency_ms": 45.2,
                },
                {
                    "label": "malicious",
                    "is_malicious": True,
                    "score": 0.95,
                    "category": "injection",
                    "latency_ms": 52.8,
                },
            ]
        }
    }


class IntentResult(BaseModel):
    """인텐트 분류 결과

    사용자 입력의 의도를 분류한 결과를 담습니다.
    """

    intent: IntentCategory = Field(..., description="분류된 인텐트 카테고리")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="분류 신뢰도 (0.0~1.0)",
    )
    matched_keywords: list[str] = Field(
        default_factory=list,
        description="매칭된 키워드 목록",
    )
    latency_ms: float = Field(..., ge=0.0, description="처리 시간 (ms)")

    @property
    def should_proceed_to_llm(self) -> bool:
        """LLM 처리가 필요한지 여부"""
        return IntentCategory.should_proceed_to_llm(self.intent)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "intent": "fortune_love",
                    "confidence": 0.92,
                    "matched_keywords": ["연애운", "궁금"],
                    "latency_ms": 12.5,
                },
                {
                    "intent": "out_of_domain_rejected",
                    "confidence": 0.88,
                    "matched_keywords": ["코드", "파이썬"],
                    "latency_ms": 8.3,
                },
            ]
        }
    }


class FilterResult(BaseModel):
    """전체 필터링 결과

    Guard + Intent 필터링의 통합 결과입니다.
    """

    guard: GuardResult = Field(..., description="Guard 검사 결과")
    intent: IntentResult = Field(..., description="Intent 분류 결과")
    should_proceed: bool = Field(
        ...,
        description="LLM 처리 진행 여부",
    )
    action: FilterAction = Field(
        ...,
        description="필터 결정 액션",
    )
    reject_reason: str | None = Field(
        None,
        description="거부/차단 사유 (should_proceed=False인 경우)",
    )
    total_latency_ms: float = Field(
        ...,
        ge=0.0,
        description="총 필터링 시간 (ms)",
    )

    @classmethod
    def create_bypass(cls) -> "FilterResult":
        """필터 바이패스 결과 생성

        필터가 비활성화되었거나 입력이 없는 경우 사용합니다.

        Returns:
            바이패스 결과
        """
        return cls(
            guard=GuardResult(
                label=GuardLabel.BENIGN,
                is_malicious=False,
                score=0.0,
                category=None,
                latency_ms=0.0,
            ),
            intent=IntentResult(
                intent=IntentCategory.FORTUNE_GENERAL,
                confidence=1.0,
                matched_keywords=[],
                latency_ms=0.0,
            ),
            should_proceed=True,
            action=FilterAction.PROCEED,
            reject_reason=None,
            total_latency_ms=0.0,
        )

    @classmethod
    def create_fallback(cls, reason: str) -> "FilterResult":
        """폴백 결과 생성

        필터 오류 시 기본값으로 진행합니다.

        Args:
            reason: 폴백 사유

        Returns:
            폴백 결과
        """
        return cls(
            guard=GuardResult(
                label=GuardLabel.BENIGN,
                is_malicious=False,
                score=0.0,
                category=None,
                latency_ms=0.0,
            ),
            intent=IntentResult(
                intent=IntentCategory.FORTUNE_GENERAL,
                confidence=0.0,
                matched_keywords=[],
                latency_ms=0.0,
            ),
            should_proceed=True,
            action=FilterAction.FALLBACK,
            reject_reason=f"[Fallback] {reason}",
            total_latency_ms=0.0,
        )

    model_config = {
        "json_schema_extra": {
            "example": {
                "guard": {
                    "label": "benign",
                    "is_malicious": False,
                    "score": 0.02,
                    "category": None,
                    "latency_ms": 48.5,
                },
                "intent": {
                    "intent": "fortune_career",
                    "confidence": 0.89,
                    "matched_keywords": ["취업", "될까"],
                    "latency_ms": 11.2,
                },
                "should_proceed": True,
                "action": "proceed",
                "reject_reason": None,
                "total_latency_ms": 59.7,
            }
        }
    }


class FilterRequest(BaseModel):
    """필터링 요청

    필터링에 필요한 정보를 담습니다.
    """

    text: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="필터링할 텍스트",
    )
    session_id: str | None = Field(
        None,
        description="세션 ID (맥락 파악용)",
    )
    has_context: bool = Field(
        False,
        description="이전 대화 맥락 존재 여부",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "text": "연애운이 궁금해요",
                "session_id": "abc123",
                "has_context": False,
            }
        }
    }
