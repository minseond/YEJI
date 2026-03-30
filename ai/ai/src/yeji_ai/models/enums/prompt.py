"""프롬프트 버저닝 Enum

화투/타로 등 카드 리딩 API 공통 프롬프트 버전 관리
"""

from enum import Enum


class PromptVersion(str, Enum):
    """프롬프트 버전

    API 쿼리 파라미터로 사용:
        ?prompt_version=standard  (기본값)
        ?prompt_version=lite      (경량화)

    버전별 특징:
        - STANDARD: 기존 전체 프롬프트 (예시 포함, ~1,500 토큰)
        - LITE: 경량화 버전 (예시 제거, 길이 제한, ~400 토큰)

    A/B 테스트용으로 설계됨.
    """

    STANDARD = "standard"
    LITE = "lite"

    # 향후 확장 예정
    # MINIMAL = "minimal"   # 최소화 (스키마만)
    # QUALITY = "quality"   # 고품질 (더 자세한 지침)


# 내부 버전 추적 (코드 히스토리용)
PROMPT_VERSION_INFO = {
    "standard": {
        "version": "1.0.0",
        "description": "기본 프롬프트 (전체 예시 포함)",
        "estimated_tokens": 1500,
    },
    "lite": {
        "version": "1.0.0",
        "description": "경량화 프롬프트 (예시 제거, 길이 제한)",
        "estimated_tokens": 400,
    },
}
