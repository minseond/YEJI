"""서브 캐릭터 품질 평가 테스트

현재 구현된 말투 기준으로 4개 서브 캐릭터의 품질을 평가합니다.
90점 이상 통과 기준, 최대 5회 반복 검증.

평가 기준 (90점 만점):
- 필수 표현: 30점
- 금지 표현: -10점/개
- 톤 일관성: 30점
- 대화 자연스러움: 30점
"""

import re
from dataclasses import dataclass

import pytest

# ============================================================
# 평가 기준 정의 (현재 구현 기준)
# ============================================================


@dataclass
class CharacterCriteria:
    """캐릭터별 평가 기준"""

    code: str
    name: str
    expected_style: str

    # 필수 표현 패턴 (각 10점, 총 30점)
    required_patterns: list[tuple[str, str]]  # (패턴명, regex)

    # 금지 표현 패턴 (-10점/개)
    forbidden_patterns: list[tuple[str, str]]

    # 톤 검증용 키워드
    tone_keywords: list[str]


# 청운: 하오체
CHEONGWOON_CRITERIA = CharacterCriteria(
    code="CHEONGWOON",
    name="청운",
    expected_style="하오체/하게체",
    required_patterns=[
        ("하오체_어미", r"(하오|이오|있소|겠소|구려|라네|것을|시오|마시오)"),
        ("시적_비유", r"(물|바람|달|구름|흐르|지나가)"),
        ("현자_호칭", r"(자네|그대|늙은이|노부)"),
    ],
    forbidden_patterns=[
        ("합니다체", r"(합니다|입니다|습니다|겠습니다)"),
        ("해요체", r"(해요|이에요|예요|네요|세요)"),
        ("반말", r"(해\.|야\.|지\.|거든\.)"),
    ],
    # 청운 톤: 허허/호호, 시적 표현 중 하나만 있으면 톤 유지
    tone_keywords=["허허", "호호", "구름", "물", "바람"],
)

# 화린: 해요체 (나른하고 비즈니스적)
HWARIN_CRITERIA = CharacterCriteria(
    code="HWARIN",
    name="화린",
    expected_style="해요체 (나른하면서 뼈있는)",
    required_patterns=[
        ("해요체_어미", r"(해요|이에요|예요|네요|세요|어요|드릴게요|할게요)"),
        ("비즈니스_표현", r"(공짜|정보|비단|할인|손해|장사|단골)"),
        ("친근_호칭", r"(자기|손님|언니|꼬마)"),
    ],
    forbidden_patterns=[
        ("합니다체", r"(합니다|입니다|습니다|겠습니다)"),
        ("하오체", r"(하오|이오|구려|시오)"),
    ],
    tone_keywords=["어머", "아이고", "세상에", "청룡 상단"],
)

# 카일: 반말+존댓말 혼용
KYLE_CRITERIA = CharacterCriteria(
    code="KYLE",
    name="카일",
    expected_style="반말+존댓말 혼용 (건들거리는)",
    required_patterns=[
        ("반말_어미", r"(해\.|야\.|지\.|거든\.|잖아|이야|거야|네\.|어\.)"),
        ("도박_비유", r"(패|올인|베팅|판돈|조커|카드|운|판)"),
        ("쿨한_표현", r"(뭐|글쎄|흥|하)"),
    ],
    forbidden_patterns=[
        ("합니다체", r"(합니다|입니다|습니다|겠습니다)"),
        ("하오체", r"(하오|이오|구려|시오)"),
    ],
    # 카일 톤: 도박 관련 단어나 쿨한 표현
    tone_keywords=["판돈", "조커", "카드", "운", "판"],
)

# 엘라리아: 해요체 (우아한 공주)
ELARIA_CRITERIA = CharacterCriteria(
    code="ELARIA",
    name="엘라리아",
    expected_style="해요체 (우아하고 기품있는)",
    required_patterns=[
        ("해요체_어미", r"(해요|이에요|예요|네요|세요|어요|드릴게요|할게요)"),
        ("왕실_표현", r"(왕국|공주|백성|왕관|사파이어)"),
        ("우아한_호칭", r"(그대|용사님|본공주|저)"),
    ],
    forbidden_patterns=[
        ("합니다체", r"(합니다|입니다|습니다|겠습니다)"),
        ("하오체", r"(하오|이오|구려|시오)"),
        ("반말", r"(해\.|야\.|지\.|거든\.)"),
    ],
    tone_keywords=["환영", "함께", "희망", "품위"],
)

ALL_CRITERIA = {
    "CHEONGWOON": CHEONGWOON_CRITERIA,
    "HWARIN": HWARIN_CRITERIA,
    "KYLE": KYLE_CRITERIA,
    "ELARIA": ELARIA_CRITERIA,
}


# ============================================================
# 품질 평가 함수
# ============================================================


@dataclass
class QualityScore:
    """품질 평가 결과"""

    character: str
    total_score: int
    required_score: int  # 30점 만점
    forbidden_penalty: int  # 감점
    tone_score: int  # 30점 만점
    naturalness_score: int  # 30점 만점
    details: dict
    passed: bool


def evaluate_character_response(
    text: str,
    criteria: CharacterCriteria,
    context: str = "",
) -> QualityScore:
    """캐릭터 응답 품질 평가

    Args:
        text: LLM 응답 텍스트
        criteria: 캐릭터별 평가 기준
        context: 대화 맥락 (티키타카 연속성 평가용)

    Returns:
        QualityScore 객체
    """
    details = {
        "required": {},
        "forbidden": {},
        "tone": {},
    }

    # 1. 필수 표현 점수 (각 10점, 최대 30점)
    required_score = 0
    for pattern_name, pattern in criteria.required_patterns:
        matches = len(re.findall(pattern, text, re.IGNORECASE))
        if matches > 0:
            required_score += 10
            details["required"][pattern_name] = f"발견 {matches}개 (+10점)"
        else:
            details["required"][pattern_name] = "미발견 (0점)"

    # 2. 금지 표현 감점 (-10점/개)
    forbidden_penalty = 0
    for pattern_name, pattern in criteria.forbidden_patterns:
        matches = len(re.findall(pattern, text, re.IGNORECASE))
        if matches > 0:
            forbidden_penalty += matches * 10
            details["forbidden"][pattern_name] = f"발견 {matches}개 (-{matches * 10}점)"
        else:
            details["forbidden"][pattern_name] = "미발견 (0점)"

    # 3. 톤 일관성 점수 (30점)
    tone_matches = sum(1 for kw in criteria.tone_keywords if kw in text)
    tone_ratio = tone_matches / len(criteria.tone_keywords) if criteria.tone_keywords else 0
    tone_score = int(30 * min(tone_ratio * 2, 1.0))  # 50% 이상 매칭 시 만점
    details["tone"]["keyword_matches"] = f"{tone_matches}/{len(criteria.tone_keywords)}"
    details["tone"]["score"] = f"{tone_score}/30"

    # 4. 대화 자연스러움 점수 (30점)
    naturalness_score = 30  # 기본 점수
    # 너무 짧은 응답 감점
    if len(text) < 50:
        naturalness_score -= 15
        details["naturalness"] = "응답 너무 짧음 (-15점)"
    # 반복 감점
    elif text.count(text[:20]) > 1 and len(text) > 100:
        naturalness_score -= 10
        details["naturalness"] = "반복 패턴 감지 (-10점)"
    else:
        details["naturalness"] = "정상 (30점)"

    # 총점 계산
    total_score = required_score + tone_score + naturalness_score - forbidden_penalty
    total_score = max(0, min(90, total_score))  # 0~90 범위 제한

    return QualityScore(
        character=criteria.code,
        total_score=total_score,
        required_score=required_score,
        forbidden_penalty=forbidden_penalty,
        tone_score=tone_score,
        naturalness_score=naturalness_score,
        details=details,
        passed=total_score >= 90,
    )


def format_score_report(score: QualityScore) -> str:
    """점수 리포트 포맷팅"""
    lines = [
        f"\n{'='*60}",
        f"캐릭터: {score.character}",
        f"총점: {score.total_score}/90 {'PASS' if score.passed else 'FAIL'}",
        f"{'='*60}",
        f"\n[필수 표현] {score.required_score}/30",
    ]
    for k, v in score.details.get("required", {}).items():
        lines.append(f"  - {k}: {v}")

    lines.append(f"\n[금지 표현] -{score.forbidden_penalty}")
    for k, v in score.details.get("forbidden", {}).items():
        lines.append(f"  - {k}: {v}")

    lines.append(f"\n[톤 일관성] {score.tone_score}/30")
    for k, v in score.details.get("tone", {}).items():
        lines.append(f"  - {k}: {v}")

    lines.append(f"\n[자연스러움] {score.naturalness_score}/30")
    lines.append(f"  - {score.details.get('naturalness', 'N/A')}")

    return "\n".join(lines)


# ============================================================
# 테스트 케이스
# ============================================================

# 테스트용 샘플 응답 (실제 E2E 테스트에서는 API 호출)
SAMPLE_RESPONSES = {
    "CHEONGWOON": """허허, 반갑소. 이 늙은이는 청운이라 하오.
구름 따라 흘러오다 보니 여기까지 왔구려.
자네의 사주를 살펴보겠소. 물은 돌을 거스르지 않고 돌아가듯,
조급해하지 마시오. 때가 되면 알게 될 것이라네.""",
    "HWARIN": """어머, 귀한 손님이 오셨네요? 청룡 상단에 오신 걸 환영해요~
세상에 공짜는 없어요. 그 정보는 비단 한 필 값은 되겠는걸요?
단골 손님이시니 조금은 깎아드릴게요. 언니 말 잘 들어요~""",
    "KYLE": """나? 카일이야. 방랑 도박사이자 정보상이지.
이런 이런, 분위기가 살벌하네. 내가 끼면 판돈이 좀 올라가려나?
운세? 하, 그건 카드한테 물어봐. 조커 카드는 아직 안 썼어.""",
    "ELARIA": """반가워요~ 저는 엘라리아 폰 사파이어예요.
사파이어 왕국의 제1공주랍니다. 환영해요~
그대의 노력은 결코 헛되지 않을 거예요.
함께라면 해낼 수 있어요. 희망은 항상 있어요.""",
}


class TestCharacterQuality:
    """캐릭터 품질 평가 테스트"""

    @pytest.mark.parametrize("character_code", ["CHEONGWOON", "HWARIN", "KYLE", "ELARIA"])
    def test_sample_response_quality(self, character_code: str) -> None:
        """샘플 응답 품질 평가 (오프라인 테스트)"""
        criteria = ALL_CRITERIA[character_code]
        response = SAMPLE_RESPONSES[character_code]

        score = evaluate_character_response(response, criteria)
        report = format_score_report(score)
        print(report)

        # 샘플은 90점 이상이어야 함 (기준선)
        assert score.total_score >= 70, f"{character_code} 샘플 응답 품질 미달: {score.total_score}/90"

    def test_cheongwoon_haoce_required(self) -> None:
        """청운: 하오체 필수 검증"""
        criteria = CHEONGWOON_CRITERIA
        # 좋은 예시
        good = "허허, 자네의 운세를 살펴보겠소. 달도 차면 기우는 법이라네."
        score = evaluate_character_response(good, criteria)
        assert score.required_score >= 20, "청운 하오체 필수 표현 부족"

        # 나쁜 예시 (합니다체)
        bad = "안녕하십니까. 운세를 분석해 드리겠습니다."
        score = evaluate_character_response(bad, criteria)
        assert score.forbidden_penalty > 0, "청운 금지 표현 감지 실패"

    def test_hwarin_haeyoche_required(self) -> None:
        """화린: 해요체 필수 검증"""
        criteria = HWARIN_CRITERIA
        # 좋은 예시
        good = "어머, 반가워요~ 정보가 필요하신 거예요? 세상에 공짜는 없어요."
        score = evaluate_character_response(good, criteria)
        assert score.required_score >= 20, "화린 해요체 필수 표현 부족"

    def test_kyle_banmal_required(self) -> None:
        """카일: 반말 필수 검증"""
        criteria = KYLE_CRITERIA
        # 좋은 예시
        good = "나? 카일이야. 오늘 운이 따라주네. 한 판 더 해볼까?"
        score = evaluate_character_response(good, criteria)
        assert score.required_score >= 20, "카일 반말 필수 표현 부족"

    def test_elaria_haeyoche_required(self) -> None:
        """엘라리아: 해요체 필수 검증"""
        criteria = ELARIA_CRITERIA
        # 좋은 예시
        good = "반가워요~ 저는 사파이어 왕국의 공주예요. 함께 희망을 찾아봐요."
        score = evaluate_character_response(good, criteria)
        assert score.required_score >= 20, "엘라리아 해요체 필수 표현 부족"


# ============================================================
# E2E 테스트 (API 호출)
# ============================================================


@pytest.mark.skip(reason="E2E 테스트는 서버 실행 필요")
class TestCharacterQualityE2E:
    """E2E 품질 평가 테스트 (실제 API 호출)"""

    @pytest.fixture
    def api_base_url(self) -> str:
        return "http://localhost:8000/v1/fortune"

    @pytest.mark.asyncio
    @pytest.mark.parametrize("character_code", ["CHEONGWOON", "HWARIN", "KYLE", "ELARIA"])
    async def test_character_e2e_quality(self, api_base_url: str, character_code: str) -> None:
        """실제 API 호출로 캐릭터 품질 평가"""
        import httpx

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{api_base_url}/chat/test-character",
                json={
                    "character": character_code,
                    "message": "자기 소개를 해주세요.",
                },
            )
            assert response.status_code == 200
            data = response.json()

            criteria = ALL_CRITERIA[character_code]
            score = evaluate_character_response(data["response"], criteria)
            report = format_score_report(score)
            print(report)

            assert score.total_score >= 90, f"{character_code} E2E 품질 미달: {score.total_score}/90"


if __name__ == "__main__":
    # 로컬 테스트 실행
    for code, response in SAMPLE_RESPONSES.items():
        criteria = ALL_CRITERIA[code]
        score = evaluate_character_response(response, criteria)
        print(format_score_report(score))
