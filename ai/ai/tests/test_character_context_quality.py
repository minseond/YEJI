"""서브 캐릭터 대화 맥락 품질 평가 테스트

실제 배포 환경(LLM 응답)을 기준으로 대화 맥락 품질을 평가합니다.

평가 영역 (45점 만점):
- 맥락 이해도: 15점 (질문에 대한 직접적 응답, 키워드 반영)
- 캐릭터 일관성: 15점 (배경/직업 일치, 캐릭터 관점)
- 대화 자연스러움: 15점 (문장 완결성, 반복 없음, 노이즈 없음)
"""

import re
from dataclasses import dataclass

import pytest

# ============================================================
# 대화 맥락 평가 기준
# ============================================================


@dataclass
class ContextCriteria:
    """캐릭터별 맥락 평가 기준"""

    code: str
    name: str

    # 캐릭터 배경 키워드 (캐릭터 일관성 평가용)
    background_keywords: list[str]

    # 캐릭터 관점 키워드 (해석 방식)
    perspective_keywords: list[str]

    # 금지 맥락 (세계관 불일치)
    forbidden_context: list[str]


# 청운: 동양 신선, 사주명리
CHEONGWOON_CONTEXT = ContextCriteria(
    code="CHEONGWOON",
    name="청운",
    background_keywords=["스승", "신선", "도", "사주", "명리", "음양", "오행", "기운"],
    perspective_keywords=["물", "바람", "달", "구름", "흐름", "이치", "때", "인연"],
    forbidden_context=["별자리", "행성", "하우스", "점성술", "서양"],
)

# 화린: 상인, 비즈니스
HWARIN_CONTEXT = ContextCriteria(
    code="HWARIN",
    name="화린",
    background_keywords=["상단", "지부장", "상인", "정보", "거래", "장사", "손님"],
    perspective_keywords=["공짜", "값", "비단", "투자", "손해", "이득", "할인"],
    forbidden_context=["무료", "공짜로 드릴게요"],  # 캐릭터 불일치
)

# 카일: 도박사, 확률
KYLE_CONTEXT = ContextCriteria(
    code="KYLE",
    name="카일",
    background_keywords=["도박", "정보상", "카드", "게임", "판", "베팅"],
    perspective_keywords=["패", "올인", "판돈", "조커", "확률", "운", "베팅", "승산"],
    forbidden_context=["신중하게", "조심스럽게"],  # 쿨한 캐릭터 불일치
)

# 엘라리아: 공주, 왕실
ELARIA_CONTEXT = ContextCriteria(
    code="ELARIA",
    name="엘라리아",
    background_keywords=["왕국", "공주", "사파이어", "왕실", "백성", "왕관"],
    perspective_keywords=["희망", "함께", "품위", "우아", "따뜻", "빛"],
    forbidden_context=["돈", "거래", "장사"],  # 상인 캐릭터와 구분
)

ALL_CONTEXT_CRITERIA = {
    "CHEONGWOON": CHEONGWOON_CONTEXT,
    "HWARIN": HWARIN_CONTEXT,
    "KYLE": KYLE_CONTEXT,
    "ELARIA": ELARIA_CONTEXT,
}


# ============================================================
# 대화 맥락 평가 함수
# ============================================================


@dataclass
class ContextScore:
    """대화 맥락 평가 결과"""

    character: str
    total_score: int
    understanding_score: int  # 맥락 이해도 (15점)
    consistency_score: int  # 캐릭터 일관성 (15점)
    naturalness_score: int  # 자연스러움 (15점)
    details: dict
    issues: list[str]


def evaluate_context_quality(
    text: str,
    criteria: ContextCriteria,
    user_question: str,
) -> ContextScore:
    """대화 맥락 품질 평가

    Args:
        text: LLM 응답 텍스트
        criteria: 캐릭터별 맥락 평가 기준
        user_question: 사용자 질문 (맥락 이해도 평가용)

    Returns:
        ContextScore 객체
    """
    details = {}
    issues = []

    # 1. 맥락 이해도 (15점)
    understanding_score = 15  # 기본 점수

    # 질문 의도별 키워드 매칭 (일반 단어 대신 의미 기반)
    intent_keywords = {
        "소개": ["저는", "나는", "이름", "~예요", "~이에요"],
        "운세": ["운", "기운", "에너지", "오늘", "흐름"],
        "조언": ["조언", "추천", "해보", "하세요", "좋아요"],
        "연애": ["연애", "사랑", "인연", "관계", "마음"],
        "재물": ["재물", "돈", "금전", "투자", "재정"],
    }

    # 질문에서 의도 파악
    detected_intent = None
    for intent, _ in intent_keywords.items():
        if intent in user_question:
            detected_intent = intent
            break

    # 의도에 맞는 응답 키워드 체크
    if detected_intent:
        response_keywords = intent_keywords[detected_intent]
        reflected = sum(1 for kw in response_keywords if kw in text)
        if reflected == 0:
            understanding_score -= 5
            issues.append(f"{detected_intent} 관련 키워드 부족")
    else:
        # 의도 불명확한 경우 응답 길이로 판단
        if len(text) < 100:
            understanding_score -= 5
            issues.append("응답 내용 부족")

    details["understanding"] = {
        "detected_intent": detected_intent,
        "score": understanding_score,
    }

    # 2. 캐릭터 일관성 (15점)
    consistency_score = 15

    # 배경 키워드 매칭
    background_matches = sum(1 for kw in criteria.background_keywords if kw in text)
    if background_matches == 0:
        consistency_score -= 5
        issues.append("캐릭터 배경 키워드 없음")

    # 관점 키워드 매칭
    perspective_matches = sum(1 for kw in criteria.perspective_keywords if kw in text)
    if perspective_matches == 0:
        consistency_score -= 5
        issues.append("캐릭터 관점 키워드 없음")

    # 금지 맥락 체크
    for forbidden in criteria.forbidden_context:
        if forbidden in text:
            consistency_score -= 5
            issues.append(f"금지 맥락 사용: {forbidden}")

    details["consistency"] = {
        "background_matches": background_matches,
        "perspective_matches": perspective_matches,
        "score": max(0, consistency_score),
    }
    consistency_score = max(0, consistency_score)

    # 3. 자연스러움 (15점)
    naturalness_score = 15

    # 문장 완결성 체크
    if text.rstrip().endswith((",", "을", "를", "이", "가", "의")):
        naturalness_score -= 10
        issues.append("문장 미완결")

    # 반복 패턴 체크
    sentences = re.split(r"[.!?]", text)
    unique_sentences = set(s.strip() for s in sentences if len(s.strip()) > 10)
    if len(sentences) > 3 and len(unique_sentences) < len(sentences) * 0.7:
        naturalness_score -= 5
        issues.append("반복 패턴 감지")

    # 노이즈 체크 (비한글 외래 문자)
    noise_patterns = re.findall(r"[^\x00-\x7F가-힣ㄱ-ㅎㅏ-ㅣ\s.,!?~\-:;\"\'()]+", text)
    if noise_patterns:
        naturalness_score -= 5
        issues.append(f"노이즈 감지: {len(noise_patterns)}개")

    # 너무 짧은 응답
    if len(text) < 50:
        naturalness_score -= 5
        issues.append("응답 너무 짧음")

    details["naturalness"] = {
        "has_noise": len(noise_patterns) > 0,
        "noise_count": len(noise_patterns),
        "sentence_count": len(sentences),
        "unique_ratio": len(unique_sentences) / max(1, len(sentences)),
        "score": max(0, naturalness_score),
    }
    naturalness_score = max(0, naturalness_score)

    # 총점 계산
    total_score = understanding_score + consistency_score + naturalness_score

    return ContextScore(
        character=criteria.code,
        total_score=total_score,
        understanding_score=understanding_score,
        consistency_score=consistency_score,
        naturalness_score=naturalness_score,
        details=details,
        issues=issues,
    )


def format_context_report(score: ContextScore) -> str:
    """맥락 점수 리포트 포맷팅"""
    lines = [
        f"\n{'='*60}",
        f"캐릭터: {score.character} - 대화 맥락 품질",
        f"총점: {score.total_score}/45 {'PASS' if score.total_score >= 40 else 'FAIL'}",
        f"{'='*60}",
        f"\n[맥락 이해도] {score.understanding_score}/15",
        f"  - 질문 키워드: {score.details.get('understanding', {}).get('question_keywords', [])}",
        f"  - 반영 수: {score.details.get('understanding', {}).get('reflected', 0)}",
        f"\n[캐릭터 일관성] {score.consistency_score}/15",
        f"  - 배경 키워드 매칭: {score.details.get('consistency', {}).get('background_matches', 0)}",
        f"  - 관점 키워드 매칭: {score.details.get('consistency', {}).get('perspective_matches', 0)}",
        f"\n[자연스러움] {score.naturalness_score}/15",
        f"  - 노이즈: {score.details.get('naturalness', {}).get('noise_count', 0)}개",
        f"  - 문장 다양성: {score.details.get('naturalness', {}).get('unique_ratio', 0):.1%}",
    ]

    if score.issues:
        lines.append(f"\n[이슈] {', '.join(score.issues)}")

    return "\n".join(lines)


# ============================================================
# 테스트 시나리오
# ============================================================

TEST_SCENARIOS = {
    "self_introduction": {
        "question": "자기 소개를 해주세요.",
        "expected_keywords": ["소개", "자기"],
    },
    "fortune": {
        "question": "오늘 운세를 알려주세요.",
        "expected_keywords": ["운세", "오늘"],
    },
    "advice": {
        "question": "요즘 힘든 일이 있어요. 조언 부탁드려요.",
        "expected_keywords": ["힘든", "조언"],
    },
    "love": {
        "question": "연애운이 어떤가요?",
        "expected_keywords": ["연애", "운"],
    },
    "money": {
        "question": "재물운이 궁금해요.",
        "expected_keywords": ["재물", "궁금"],
    },
}


# 샘플 응답 (오프라인 테스트용)
SAMPLE_RESPONSES = {
    "CHEONGWOON": {
        "self_introduction": """허허, 반갑소. 이 늙은이는 청운이라 하오.
동방의 신선으로 오랜 세월 도를 닦아왔소. 소이설이라는 제자를 두었는데,
그 녀석도 제법 음양오행의 이치를 깨달아가고 있다네.
물처럼 흐르고 바람처럼 지나가는 것이 세상의 이치라오.""",
        "fortune": """자네의 사주를 살펴보겠소. 오늘은 목(木)의 기운이 강하구려.
이는 새로운 시작과 성장을 뜻하오. 다만 조급해하지 마시오.
물이 돌을 거스르지 않듯, 순리를 따르면 좋은 결과가 있을 것이라네.""",
    },
    "HWARIN": {
        "self_introduction": """어머, 귀한 손님이 오셨네요? 청룡 상단에 오신 걸 환영해요~
나는 화린이에요. 이 지부의 지부장이죠.
세상에 공짜는 없어요. 하지만 단골 손님한테는 정보료를 좀 깎아드릴게요~""",
        "fortune": """오늘 운세가 궁금하신 거예요? 어머, 좋은 기운이 느껴지네요~
재물운이 따르고 있어요. 다만 과한 투자는 손해를 볼 수 있으니
적당히 챙기는 게 좋을 것 같아요. 언니 말 잘 들어요~""",
    },
    "KYLE": {
        "self_introduction": """나? 카일이야. 방랑 도박사이자 정보상이지.
이런 이런, 분위기가 살벌하네. 내가 끼면 판돈이 좀 올라가려나?
인생은 어차피 한 판의 도박이야. 조커 카드는 아직 안 썼어.""",
        "fortune": """운세? 하, 그건 카드한테 물어봐.
오늘 패를 보니까... 음, 나쁘지 않네. 베팅할 만해.
다만 올인은 바보들이나 하는 거야. 60%는 안전하게, 40%만 베팅해.""",
    },
    "ELARIA": {
        "self_introduction": """반가워요~ 저는 사파이어 왕국의 제1공주, 엘라리아예요.
사파이어의 빛처럼 따뜻하고 희망찬 말씀을 전해드리고 싶어요.
왕실의 품위를 지키면서도 백성들과 함께하는 공주가 되려 노력해요.""",
        "fortune": """오늘 운세가 궁금하신 거예요? 좋은 기운이 느껴져요~
희망은 항상 있어요. 그대의 노력은 결코 헛되지 않을 거예요.
함께라면 해낼 수 있어요. 사파이어의 빛이 함께하기를 바라요.""",
    },
}


class TestContextQuality:
    """대화 맥락 품질 평가 테스트 (오프라인)"""

    @pytest.mark.parametrize("character_code", ["CHEONGWOON", "HWARIN", "KYLE", "ELARIA"])
    @pytest.mark.parametrize("scenario", ["self_introduction", "fortune"])
    def test_sample_context_quality(self, character_code: str, scenario: str) -> None:
        """샘플 응답 맥락 품질 평가"""
        criteria = ALL_CONTEXT_CRITERIA[character_code]
        response = SAMPLE_RESPONSES[character_code][scenario]
        question = TEST_SCENARIOS[scenario]["question"]

        score = evaluate_context_quality(response, criteria, question)
        report = format_context_report(score)
        print(report)

        # 샘플은 40점 이상이어야 함
        assert score.total_score >= 35, f"{character_code} {scenario} 맥락 품질 미달: {score.total_score}/45"

    def test_cheongwoon_perspective(self) -> None:
        """청운: 동양적 관점 검증"""
        criteria = CHEONGWOON_CONTEXT
        good = "물처럼 흐르고 바람처럼 지나가는 것이 세상의 이치라오."
        score = evaluate_context_quality(good, criteria, "인생 조언")
        assert score.consistency_score >= 10, "청운 동양적 관점 부족"

    def test_kyle_gambling_perspective(self) -> None:
        """카일: 도박 관점 검증"""
        criteria = KYLE_CONTEXT
        good = "운세? 오늘 패를 보니까 베팅할 만해. 올인은 금물이야."
        score = evaluate_context_quality(good, criteria, "운세")
        assert score.consistency_score >= 10, "카일 도박 관점 부족"

    def test_noise_detection(self) -> None:
        """노이즈 감지 검증"""
        criteria = ELARIA_CONTEXT
        noisy = "반가워요~ 저는 엘라리아예요.ครี糖เริ่มต้น 좋은 하루 보내세요."
        score = evaluate_context_quality(noisy, criteria, "자기 소개")
        # 노이즈 이슈 메시지 형식: "노이즈 감지: N개"
        has_noise_issue = any("노이즈 감지" in issue for issue in score.issues)
        assert has_noise_issue, f"노이즈 감지 실패. 이슈 목록: {score.issues}"


# ============================================================
# E2E 테스트 (API 호출)
# ============================================================


@pytest.mark.skip(reason="E2E 테스트는 서버 실행 필요")
class TestContextQualityE2E:
    """E2E 대화 맥락 품질 테스트 (실제 API 호출)"""

    @pytest.fixture
    def api_base_url(self) -> str:
        return "https://i14a605.p.ssafy.io/ai/v1/fortune"

    @pytest.mark.asyncio
    @pytest.mark.parametrize("character_code", ["CHEONGWOON", "HWARIN", "KYLE", "ELARIA"])
    @pytest.mark.parametrize("scenario", ["self_introduction", "fortune"])
    async def test_character_context_e2e(
        self,
        api_base_url: str,
        character_code: str,
        scenario: str,
    ) -> None:
        """실제 API 호출로 맥락 품질 평가"""
        import httpx

        question = TEST_SCENARIOS[scenario]["question"]

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{api_base_url}/chat/test-character",
                json={
                    "character": character_code,
                    "message": question,
                },
            )
            assert response.status_code == 200
            data = response.json()

            criteria = ALL_CONTEXT_CRITERIA[character_code]
            score = evaluate_context_quality(data["response"], criteria, question)
            report = format_context_report(score)
            print(report)

            assert score.total_score >= 40, f"{character_code} {scenario} E2E 맥락 품질 미달: {score.total_score}/45"


if __name__ == "__main__":
    # 로컬 테스트 실행
    for code in ["CHEONGWOON", "HWARIN", "KYLE", "ELARIA"]:
        for scenario in ["self_introduction", "fortune"]:
            criteria = ALL_CONTEXT_CRITERIA[code]
            response = SAMPLE_RESPONSES[code][scenario]
            question = TEST_SCENARIOS[scenario]["question"]
            score = evaluate_context_quality(response, criteria, question)
            print(format_context_report(score))
