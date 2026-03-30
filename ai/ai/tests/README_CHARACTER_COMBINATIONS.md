# 캐릭터 조합 테스트 가이드

## 개요

6개 캐릭터의 모든 2개 조합 (6C2 = 15가지)에 대한 품질 검증 테스트입니다.

**검증 항목:**
1. 각 캐릭터의 말투 일관성
2. 프롬프트 누출 방지
3. 언어 순수성 (한글 + 허용된 한자/영어만)

---

## 캐릭터 말투 규칙

| 캐릭터 | 말투 | 필수 어미 | 금지 어미 |
|--------|------|-----------|-----------|
| **SOISEOL** (소이설) | 하오체/하게체 | ~하오, ~구려, ~시오 | ~해요, ~네요, ~합니다 |
| **STELLA** (스텔라) | 해요체 | ~해요, ~네요, ~세요 | ~하오, ~구려, ~합니다 |
| **CHEONGWOON** (청운) | 하오체 (시적) | ~하오, ~라네, ~마시오 | ~해요, ~네요, ~합니다 |
| **HWARIN** (화린) | 해요체 (나른) | ~해요, ~드릴게요 | ~하오, ~구려, ~합니다 |
| **KYLE** (카일) | 반말+존댓말 혼용 | ~해., ~야., ~지. | ~합니다, ~하오 |
| **ELARIA** (엘라리아) | 해요체 (우아) | ~해요, ~세요 | ~하오, ~합니다, ~해. |

---

## 15개 조합 목록

```
1. SOISEOL + STELLA
2. SOISEOL + CHEONGWOON
3. SOISEOL + HWARIN
4. SOISEOL + KYLE
5. SOISEOL + ELARIA
6. STELLA + CHEONGWOON
7. STELLA + HWARIN
8. STELLA + KYLE
9. STELLA + ELARIA
10. CHEONGWOON + HWARIN
11. CHEONGWOON + KYLE
12. CHEONGWOON + ELARIA
13. HWARIN + KYLE
14. HWARIN + ELARIA
15. KYLE + ELARIA
```

---

## 테스트 실행

### 1. 샘플 응답 검증 (오프라인)

conftest.py 의존성 없이 검증 로직만 테스트:

```bash
cd C:/Users/SSAFY/yeji-ai-server/ai
python tests/test_combinations_validation.py
```

**출력 예시:**
```
============================================================
15개 조합 검증 테스트
============================================================
[1] SOISEOL + STELLA: ✓ PASS
[2] SOISEOL + CHEONGWOON: ✓ PASS
...
[15] KYLE + ELARIA: ✓ PASS
============================================================
결과: 15/15 통과
============================================================
```

### 2. pytest 단위 테스트

개별 검증 항목 테스트:

```bash
# 말투 일관성 테스트
pytest tests/test_character_combinations.py::TestIndividualCharacterSpeech -v

# 프롬프트 누출 테스트
pytest tests/test_character_combinations.py::TestPromptLeakAndPurity::test_prompt_leak_detection -v

# 언어 순수성 테스트
pytest tests/test_character_combinations.py::TestPromptLeakAndPurity::test_language_purity_hanja -v
```

### 3. 조합 통합 테스트

```bash
# 전체 조합 테스트
pytest tests/test_character_combinations.py::TestCharacterCombinations::test_all_15_combinations -v

# 특정 조합만 테스트 (parametrize)
pytest tests/test_character_combinations.py::TestCharacterCombinations::test_combination_speech_consistency -v
```

### 4. E2E 테스트 (서버 실행 필요)

실제 vLLM API를 호출하여 테스트:

```bash
# 서버 실행 (다른 터미널)
uvicorn yeji_ai.main:app --reload --host 0.0.0.0 --port 8000

# E2E 테스트 실행
pytest tests/test_character_combinations.py::TestCharacterCombinationsE2E -v --no-skip
```

---

## 검증 로직 상세

### 1. 말투 일관성 검증

**함수:** `check_speech_style_consistency(text, character)`

**로직:**
- 필수 어미 패턴 중 **최소 1개 이상** 발견되어야 PASS
- 금지 어미 패턴이 **1개라도** 발견되면 FAIL

**정규표현식 패턴:**
```python
# 어미 + 문장부호 또는 문자열 끝
r"하오(?:[\.!\?~,]|$)"  # "하오", "하오.", "하오!" 등 매칭
```

**예시:**
```python
# SOISEOL - PASS
"자네의 사주를 살펴보겠소."  # "보겠소" → 필수 어미 "시오" 매칭

# SOISEOL - FAIL
"안녕하세요. 사주를 분석해 드리겠습니다."  # 금지 어미 "습니다" 발견
```

### 2. 프롬프트 누출 방지

**함수:** `check_no_prompt_leak(text)`

**금지 패턴:**
- XML 태그: `<persona>`, `<speaking_rule>`, `<forbidden>` 등
- 메타 텍스트: "필수 어미", "금지 어미", "호칭 목록", "말투 규칙"
- 프롬프트 설명: "~체를 사용하라", "반드시.*사용"

**예시:**
```python
# FAIL - 프롬프트 누출
"""
<persona>소이설</persona>
필수 어미: ~하오, ~구려
"""
```

### 3. 언어 순수성 검증

**함수:** `check_language_purity(text)`

**허용:**
- 한글: 가-힣, ㄱ-ㅎ, ㅏ-ㅣ
- 한자: 木火土金水, 比肩, 正官, 甲乙丙丁 등 (사주/오행 관련)
- 영어 고유명사: Stella, Kyle, Elaria (대소문자 구분 없음)
- 숫자 및 문장부호: 0-9, .,!?~…-()""''「」『』

**금지:**
- 깨진 문자: �, \ufffd
- 일본어: ぁ-ん, ァ-ヶ
- 허용되지 않은 영어 단어

**예시:**
```python
# PASS
"목(木) 기운이 강하고 비견(比肩)이 있어요."

# PASS
"Stella가 Kyle과 Elaria를 만났어요."

# FAIL
"This is a test message with English words."
```

---

## 테스트 파일 구조

```
tests/
├── test_character_combinations.py      # 메인 테스트 파일
│   ├── SPEECH_PATTERNS                 # 말투 패턴 정의
│   ├── PROMPT_LEAK_PATTERNS            # 프롬프트 누출 패턴
│   ├── LANGUAGE_PURITY_PATTERNS        # 언어 순수성 패턴
│   ├── CHARACTER_COMBINATIONS          # 15개 조합 목록
│   ├── check_speech_style_consistency() # 말투 검증 함수
│   ├── check_no_prompt_leak()          # 프롬프트 누출 검증
│   ├── check_language_purity()         # 언어 순수성 검증
│   ├── validate_character_response()   # 종합 검증
│   ├── TestCharacterCombinations       # 조합 테스트 클래스
│   ├── TestIndividualCharacterSpeech   # 개별 캐릭터 테스트
│   ├── TestPromptLeakAndPurity         # 누출/순수성 테스트
│   └── TestCharacterCombinationsE2E    # E2E 테스트 (skip)
│
└── test_combinations_validation.py     # 독립 실행 검증 스크립트
    ├── test_speech_patterns()           # 말투 패턴 검증
    ├── test_prompt_leak()               # 프롬프트 누출 검증
    ├── test_language_purity()           # 언어 순수성 검증
    └── test_combinations()              # 15개 조합 검증
```

---

## 실제 API 호출 E2E 테스트

### 전제 조건

1. vLLM 서버 실행 (GPU 필요)
2. AI 서버 실행 (FastAPI)
3. `/v1/fortune/chat/test-character` 엔드포인트 사용 가능

### 실행 방법

```bash
# 1. GPU 서버에서 vLLM 시작
python -m vllm.entrypoints.openai.api_server \
    --model tellang/yeji-8b-rslora-v7-AWQ \
    --quantization awq \
    --port 8001

# 2. AI 서버 시작
cd C:/Users/SSAFY/yeji-ai-server/ai
uvicorn yeji_ai.main:app --reload --host 0.0.0.0 --port 8000

# 3. E2E 테스트 실행 (skip 제거)
pytest tests/test_character_combinations.py::TestCharacterCombinationsE2E -v -s
```

### E2E 테스트 플로우

```python
async def test_combination_e2e(char1, char2):
    # 1. 캐릭터 1 응답 생성
    response1 = await client.post("/v1/fortune/chat/test-character", {
        "character": char1,
        "message": "간단히 자기소개 해주세요."
    })

    # 2. 캐릭터 2 응답 생성
    response2 = await client.post("/v1/fortune/chat/test-character", {
        "character": char2,
        "message": "간단히 자기소개 해주세요."
    })

    # 3. 각 응답 검증
    validate_character_response(response1["response"], char1)
    validate_character_response(response2["response"], char2)
```

---

## 통과 기준

### 샘플 응답 테스트 (오프라인)
- 15개 조합 모두 PASS 필요
- 각 캐릭터의 필수 어미 최소 1개 이상 발견
- 금지 어미 0개

### E2E 테스트 (실제 API)
- 15개 조합 모두 PASS 필요
- 말투 일관성: 필수 어미 발견, 금지 어미 없음
- 프롬프트 누출: 0건
- 언어 순수성: 허용된 문자만 사용

---

## 트러블슈팅

### Q1. 정규표현식 패턴이 매칭되지 않아요

**증상:**
```
SOISEOL: 필수 어미 패턴이 하나도 발견되지 않음
```

**해결:**
- 문장 끝 패턴 확인: `(?:[\.!\?~,]|$)`
- 실제 응답 텍스트 확인: 문장부호 포함 여부
- 디버깅: `re.findall(pattern, text, re.MULTILINE)` 결과 출력

### Q2. E2E 테스트가 skip됩니다

**증상:**
```
SKIPPED [1] test_character_combinations.py:325: E2E 테스트는 서버 실행 필요
```

**해결:**
```bash
# @pytest.mark.skip 데코레이터 제거 또는
pytest tests/test_character_combinations.py::TestCharacterCombinationsE2E -v --no-skip
```

### Q3. 허용된 영어 고유명사가 오류로 감지돼요

**증상:**
```
허용되지 않은 영어 단어 발견: ['StellaKyleElaria']
```

**해결:**
- `LANGUAGE_PURITY_PATTERNS["allowed_english"]` 패턴 확인
- 정규표현식에서 `\b` (단어 경계) 대신 명시적 치환 사용:
  ```python
  cleaned_text = re.sub(r"(Stella|Kyle|Elaria)", "__NAME__", text)
  ```

### Q4. vLLM 호출 시 타임아웃 발생

**증상:**
```
httpx.ReadTimeout: timed out after 120.0s
```

**해결:**
```python
async with httpx.AsyncClient(timeout=300.0) as client:  # 5분
    ...
```

---

## 향후 개선 사항

1. **캐릭터 추가 시 자동 조합 생성**
   - 캐릭터 목록을 동적으로 가져와서 조합 생성

2. **품질 점수화**
   - 말투 일관성: 필수 어미 빈도 점수
   - 자연스러움: 문장 길이, 반복 패턴 감지

3. **배치 테스트**
   - 15개 조합을 병렬로 실행하여 시간 단축

4. **테스트 리포트 생성**
   - HTML/JSON 형식으로 결과 저장
   - CI/CD 파이프라인 통합

---

## 참고 문서

- [Python 컨벤션](../docs/PYTHON_CONVENTIONS.md)
- [캐릭터 페르소나](../src/yeji_ai/prompts/character_personas.py)
- [캐릭터 품질 테스트](./test_character_quality.py)
