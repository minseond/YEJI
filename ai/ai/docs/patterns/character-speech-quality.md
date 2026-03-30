# 패턴: 캐릭터 말투 품질 관리

## 개요

LLM 기반 캐릭터 응답에서 일관된 말투 품질을 유지하기 위한 패턴을 정의합니다.
이 패턴은 Few-shot 프롬프팅, 품질 평가, 후처리를 포괄합니다.

---

## 1. 말투 유형 분류

### 1.1 한국어 말투 스타일

| 유형 | 어미 패턴 | 분위기 | 사용 예시 |
|------|----------|--------|----------|
| 해요체 | ~해요, ~이에요, ~세요 | 친근하고 부드러움 | 화린, 엘라리아 |
| 합니다체 | ~합니다, ~입니다 | 격식 있고 공손함 | (사용 자제) |
| 하오체 | ~하오, ~이오, ~구려 | 고풍스럽고 위엄 | 청운 |
| 반말 | ~해, ~야, ~지 | 친밀하고 캐주얼 | 카일 (혼용) |

### 1.2 캐릭터별 말투 설정

```yaml
청운:
  주력: 하오체
  금지: [합니다체, 해요체]
  특징: 시적 비유, 현자의 위엄

화린:
  주력: 해요체
  금지: [합니다체, 하오체]
  특징: 나른하면서 비즈니스적

카일:
  주력: 반말+존댓말 혼용
  금지: [합니다체, 하오체]
  특징: 도박 비유, 쿨한 태도

엘라리아:
  주력: 해요체
  금지: [합니다체, 하오체, 반말]
  특징: 우아한 공주, 왕실 품위
```

---

## 2. Few-shot 예시 작성 가이드라인

### 2.1 필수 구성 요소

#### 1) 핵심 규칙 섹션

```
[핵심 규칙 - 엄격히 준수]
✅ 모든 문장을 [주력 어미]로 끝내세요!
❌ [금지 어미]는 절대 사용 금지!
```

**효과**: LLM에게 명확한 경계 설정

#### 2) 자동 변환 예시 (10개 이상)

```
<자동 변환 - 합니다→해요>
- "합니다" → "해요" (예: 환영합니다 → 환영해요)
- "입니다" → "이에요/예요" (예: 공주입니다 → 공주예요)
- "있습니다" → "있어요"
- "없습니다" → "없어요"
- "됩니다" → "돼요"
- "겠습니다" → "드릴게요/할게요"
- "바랍니다" → "바라요"
- "좋습니다" → "좋아요"
- "가지고 있습니다" → "가지고 있어요"
- "노력합니다" → "노력해요"
</자동 변환>
```

**효과**: 구체적인 변환 패턴 학습

#### 3) 올바른 문장 예시 (30개 이상)

```
<올바른 문장 예시 30개>
1. "반가워요~ 저는 [캐릭터명]예요."
2. "[인사말/소개]"
3. "[상황별 대사 1]"
...
30. "[마무리 대사]"
</올바른 문장 예시>
```

**작성 팁**:
- 다양한 상황 포함 (인사, 격려, 명령, 개인적 대화 등)
- 실제 응답에 가까운 길이와 톤
- 캐릭터 특유 표현 포함

#### 4) 틀린 예시 (10개 이상)

```
<틀린 문장 예시>
❌ "반갑습니다." → ✅ "반가워요~"
❌ "환영합니다." → ✅ "환영해요~"
❌ "전해드리겠습니다." → ✅ "전해드릴게요."
...
</틀린 문장 예시>
```

**효과**: 명확한 경계 설정, "하지 말아야 할 것" 학습

#### 5) 최종 점검 섹션

```
<최종 점검 - 응답 생성 전 반드시 확인>
1. 문장이 "~합니다"로 끝나면 → "~해요"로 수정
2. 문장이 "~입니다"로 끝나면 → "~이에요"로 수정
3. 모든 문장을 검토하고 [금지 어미]가 있으면 수정 후 응답

⚠️ 경고: [금지 어미]를 사용하면 캐릭터 설정 위반입니다!
</최종 점검>
```

**효과**: 응답 생성 직전 자가 검토 유도

### 2.2 프롬프트 구조 템플릿

```python
SYSTEM_PROMPT = """/no_think
[캐릭터 인사 1-2문장]

[핵심 규칙]
✅ 필수: ...
❌ 금지: ...

<말투 규칙>
❌ 절대 금지: [구체적 패턴]
✅ 오직 사용: [구체적 패턴]
</말투 규칙>

<자동 변환>
[10개 이상]
</자동 변환>

<올바른 예시 30개>
[다양한 상황별 예시]
</올바른 예시>

<틀린 예시>
[❌→✅ 형식으로 10개 이상]
</틀린 예시>

<character>
[캐릭터 성격 2-3문장]
</character>

<최종 점검>
[체크포인트 3-5개]
⚠️ 경고: ...
</최종 점검>
"""
```

---

## 3. 품질 평가 프레임워크

### 3.1 평가 기준 (90점 만점)

```yaml
필수_표현: 30점
  - 말투 어미 패턴: 10점 (regex 매칭)
  - 캐릭터 특유 표현: 10점 (키워드 매칭)
  - 호칭/자칭 패턴: 10점 (regex 매칭)

금지_표현: -10점/개
  - 금지 어미 사용 시 개당 감점

톤_일관성: 30점
  - 톤 키워드 매칭률 (50% 이상 시 만점)

자연스러움: 30점
  - 응답 길이 적절성 (50자 미만 시 -15점)
  - 반복 패턴 없음 (-10점)
```

### 3.2 CharacterCriteria 정의 예시

```python
from dataclasses import dataclass

@dataclass
class CharacterCriteria:
    """캐릭터별 평가 기준"""

    code: str
    name: str
    expected_style: str

    # 필수 표현 패턴 (각 10점)
    required_patterns: list[tuple[str, str]]  # (패턴명, regex)

    # 금지 표현 패턴 (-10점/개)
    forbidden_patterns: list[tuple[str, str]]

    # 톤 검증용 키워드
    tone_keywords: list[str]


# 예시: 엘라리아
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
```

### 3.3 평가 함수 구현

```python
import re
from dataclasses import dataclass

@dataclass
class QualityScore:
    """품질 평가 결과"""

    character: str
    total_score: int
    required_score: int
    forbidden_penalty: int
    tone_score: int
    naturalness_score: int
    details: dict
    passed: bool


def evaluate_character_response(
    text: str,
    criteria: CharacterCriteria,
) -> QualityScore:
    """캐릭터 응답 품질 평가"""

    details = {"required": {}, "forbidden": {}, "tone": {}}

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

    # 3. 톤 일관성 점수 (30점)
    tone_matches = sum(1 for kw in criteria.tone_keywords if kw in text)
    tone_ratio = tone_matches / len(criteria.tone_keywords) if criteria.tone_keywords else 0
    tone_score = int(30 * min(tone_ratio * 2, 1.0))

    # 4. 자연스러움 점수 (30점)
    naturalness_score = 30
    if len(text) < 50:
        naturalness_score -= 15
    elif text.count(text[:20]) > 1 and len(text) > 100:
        naturalness_score -= 10

    # 총점 계산
    total_score = required_score + tone_score + naturalness_score - forbidden_penalty
    total_score = max(0, min(90, total_score))

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
```

### 3.4 pytest 테스트 예시

```python
import pytest

class TestCharacterQuality:
    """캐릭터 품질 평가 테스트"""

    @pytest.mark.parametrize("character_code", ["CHEONGWOON", "HWARIN", "KYLE", "ELARIA"])
    def test_sample_response_quality(self, character_code: str) -> None:
        """샘플 응답 품질 평가"""
        criteria = ALL_CRITERIA[character_code]
        response = SAMPLE_RESPONSES[character_code]

        score = evaluate_character_response(response, criteria)

        # 샘플은 70점 이상이어야 함 (오프라인 기준)
        assert score.total_score >= 70, f"{character_code} 샘플 품질 미달"

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_e2e_quality(self, character_code: str) -> None:
        """E2E 테스트 (실제 API 호출)"""
        response = await call_character_api(character_code)
        score = evaluate_character_response(response, ALL_CRITERIA[character_code])

        # E2E는 80점 이상이어야 함
        assert score.total_score >= 80, f"{character_code} E2E 품질 미달"
```

---

## 4. 말투 문제 해결 패턴

### 4.1 합니다체 혼재 문제

**증상**: 해요체 캐릭터가 간헐적으로 합니다체 사용

**원인**:
1. LLM의 격식체 선호 (공식 맥락)
2. Few-shot 예시 부족
3. 프롬프트 후반부 규칙 무시

**해결 단계**:

1. **Few-shot 강화** (1차 시도)
   - 올바른 예시 30개 이상
   - 틀린 예시 10개 이상

2. **규칙 강조** (2차 시도)
   - "최소화" → "절대 금지"
   - ⚠️ 경고 메시지 추가

3. **최종 점검 섹션** (3차 시도)
   - 응답 생성 전 자가 검토 지시

4. **Postprocessor 변환** (최후 수단)
   ```python
   def convert_habnida_to_haeyo(text: str) -> str:
       replacements = [
           (r"합니다", "해요"),
           (r"입니다", "이에요"),
           (r"있습니다", "있어요"),
           (r"겠습니다", "드릴게요"),
       ]
       for pattern, replacement in replacements:
           text = re.sub(pattern, replacement, text)
       return text
   ```

### 4.2 톤 키워드 부족 문제

**증상**: 캐릭터 특유의 표현이 응답에 나타나지 않음

**해결**:
1. 시스템 프롬프트에 톤 키워드 명시
2. Few-shot 예시에 톤 키워드 포함
3. 캐릭터 설정 섹션에 "자주 사용하는 표현" 추가

### 4.3 응답 길이 문제

**증상**: 너무 짧거나 너무 긴 응답

**해결**:
1. `max_tokens` 설정 조정
2. 프롬프트에 "2-3문장으로 응답" 지시
3. Postprocessor에서 길이 조정

---

## 5. 체크리스트

### 5.1 새 캐릭터 추가 시

- [ ] 말투 스타일 정의 (해요체/하오체/반말 등)
- [ ] CharacterCriteria 정의
  - [ ] 필수 어미 패턴 (regex)
  - [ ] 금지 어미 패턴 (regex)
  - [ ] 톤 키워드 5개 이상
- [ ] 시스템 프롬프트 작성
  - [ ] 핵심 규칙 섹션
  - [ ] 자동 변환 예시 10개
  - [ ] 올바른 예시 30개
  - [ ] 틀린 예시 10개
  - [ ] 최종 점검 섹션
- [ ] 샘플 응답 작성
- [ ] 오프라인 테스트 70점 이상
- [ ] E2E 테스트 80점 이상

### 5.2 품질 개선 PDCA

- [ ] **Plan**: 목표 점수 정의 (기본 80점, 이상적 90점)
- [ ] **Do**: Few-shot 조정 (최대 5회 반복)
- [ ] **Check**: E2E 테스트 실행 및 점수 측정
- [ ] **Act**: 성공 패턴 문서화

---

## 6. 참조

| 문서 | 경로 | 설명 |
|------|------|------|
| PDCA 문서 | `ai/docs/pdca/sub-characters/` | Plan/Do/Check/Act 문서 |
| 엘라리아 페르소나 | `ai/src/yeji_ai/prompts/elaria_persona.py` | 참조 구현 |
| 품질 테스트 | `ai/tests/test_character_quality.py` | 테스트 코드 |
| 티키타카 패턴 | `ai/docs/patterns/tikitaka-generation.md` | 티키타카 생성 패턴 |
| 페르소나 규칙 | `ai/docs/patterns/tikitaka-persona-rules.md` | 페르소나 규칙 |

---

> **작성일**: 2026-01-31
> **작성자**: YEJI AI 팀
> **버전**: 1.0
