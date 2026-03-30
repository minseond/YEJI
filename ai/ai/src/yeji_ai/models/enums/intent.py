"""인텐트 필터 Enum 정의 (태스크 #98)

인텐트 카테고리 및 Guard 라벨 정의
"""

from enum import Enum


class GuardLabel(str, Enum):
    """Guard 모델 판정 라벨"""

    BENIGN = "benign"
    MALICIOUS = "malicious"


class MaliciousCategory(str, Enum):
    """악성 프롬프트 세부 카테고리"""

    INJECTION = "injection"  # 프롬프트 인젝션
    JAILBREAK = "jailbreak"  # 탈옥 시도
    INDIRECT_ATTACK = "indirect_attack"  # 간접 공격


class IntentCategory(str, Enum):
    """인텐트 카테고리

    사용자 입력의 의도를 분류하는 체계
    """

    # 운세 관련 (LLM 처리)
    FORTUNE_GENERAL = "fortune_general"  # 일반 운세
    FORTUNE_LOVE = "fortune_love"  # 연애/결혼운
    FORTUNE_CAREER = "fortune_career"  # 직장/취업운
    FORTUNE_MONEY = "fortune_money"  # 금전/재물운
    FORTUNE_HEALTH = "fortune_health"  # 건강운
    FORTUNE_ACADEMIC = "fortune_academic"  # 학업/시험운
    FORTUNE_INTERPERSONAL = "fortune_interpersonal"  # 대인관계운

    # 대화 보조
    GREETING = "greeting"  # 인사 (직접 응답 가능)
    FOLLOWUP = "followup"  # 후속 질문 (LLM 처리)

    # 도메인 외
    OUT_OF_DOMAIN_ALLOWED = "out_of_domain_allowed"  # 친절히 안내
    OUT_OF_DOMAIN_REJECTED = "out_of_domain_rejected"  # 정중히 거부

    @classmethod
    def is_fortune_related(cls, category: "IntentCategory") -> bool:
        """운세 관련 카테고리인지 확인

        Args:
            category: 확인할 카테고리

        Returns:
            운세 관련 여부
        """
        return category.value.startswith("fortune_")

    @classmethod
    def should_proceed_to_llm(cls, category: "IntentCategory") -> bool:
        """LLM 처리가 필요한 카테고리인지 확인

        Args:
            category: 확인할 카테고리

        Returns:
            LLM 처리 필요 여부
        """
        return category in {
            cls.FORTUNE_GENERAL,
            cls.FORTUNE_LOVE,
            cls.FORTUNE_CAREER,
            cls.FORTUNE_MONEY,
            cls.FORTUNE_HEALTH,
            cls.FORTUNE_ACADEMIC,
            cls.FORTUNE_INTERPERSONAL,
            cls.FOLLOWUP,
        }


class FilterAction(str, Enum):
    """필터 결정 액션"""

    PROCEED = "proceed"  # LLM 처리 진행
    BLOCK_MALICIOUS = "block_malicious"  # 악성 프롬프트 차단
    REJECT_OOD = "reject_ood"  # 도메인 외 거부
    DIRECT_RESPONSE = "direct_response"  # 직접 응답 (인사 등)
    FALLBACK = "fallback"  # 폴백 (필터 오류 시)


class FilterMode(str, Enum):
    """필터 동작 모드"""

    BLOCK = "block"  # 정상 동작: 차단/거부 실행
    LOG_ONLY = "log_only"  # 로깅만: 결과 기록, 차단 안 함
    SHADOW = "shadow"  # 백그라운드: 샘플링 실행, 결과 무시
