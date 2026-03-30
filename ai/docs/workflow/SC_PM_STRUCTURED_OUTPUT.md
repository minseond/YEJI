# SuperClaude PM 프롬프트: LLM 구조화된 출력 구현

> 복사해서 사용 - SuperClaude Framework 기반

---

## 🚀 메인 프롬프트 (복사용)

```
/sc:pm "LLM 구조화된 출력 시스템 구현" --strategy wave

[목표]
AWS 8B 모델로 프론트엔드 확정 스키마(UserFortune)에 맞는 JSON 응답 생성
- 동양 사주 (SajuDataV2) + 서양 점성술 (WesternFortuneDataV2)
- 도메인 코드 엄격 준수
- 전체 JSON 반환

[PRD]
docs/workflow/LLM_STRUCTURED_OUTPUT_PRD.md

[PDCA 위치]
docs/pdca/structured-output/

[Wave 1: Research & Design]
1.1 현재 상태 분석
  - llm_schemas.py 구조 확인
  - dummyFortuneV2.ts 예시 5개 분석
  - domainMapping.ts 도메인 코드 추출

1.2 리서치 (context7)
  - Qwen3 structured JSON output 가이드
  - vLLM response_format 사용법
  - Pydantic v2 validator 패턴

1.3 설계
  - UserFortune Pydantic 스키마
  - 도메인 코드 Enum
  - 검증 로직 (percent 합계, 필수 필드)
  - 프롬프트 템플릿 구조

→ 산출물: docs/pdca/structured-output/plan.md

[Wave 2: Implementation]
2.1 스키마 구현
  - src/yeji_ai/models/user_fortune.py
  - 도메인 코드 Enum (ElementCode, TenGodCode, ZodiacSign 등)
  - Pydantic 모델 + @field_validator

2.2 프롬프트 구현
  - src/yeji_ai/prompts/fortune_prompts.py
  - 시스템 프롬프트 + 스키마 지시 분리
  - Qwen3 /no_think, XML 태그 활용

2.3 서비스 구현
  - src/yeji_ai/services/fortune_generator.py
  - generate_eastern() / generate_western() / generate_full()
  - response_format: {"type": "json_object"}

→ 산출물: docs/pdca/structured-output/do.md

[Wave 3: Testing & Validation]
3.1 단위 테스트
  - 스키마 검증 테스트 (도메인 코드, percent 합계)
  - 프롬프트 생성 테스트

3.2 통합 테스트 (AWS 8B)
  - 동양 사주 JSON 생성
  - 서양 점성술 JSON 생성
  - 전체 UserFortune JSON 생성

3.3 검증
  - 도메인 코드 일치 여부
  - 한자/한글/영어 형식
  - 필수 필드 누락 여부
  - percent 합계 = 100

→ 산출물: docs/pdca/structured-output/check.md

[Wave 4: Fix & Document]
- 테스트 실패 시 원인 분석 (Root Cause)
- 프롬프트 조정 또는 스키마 수정
- 재테스트 (Wave 2-3 반복)
- 성공 시 패턴 문서화

→ 산출물: docs/pdca/structured-output/act.md

[도메인 코드 - 엄격 준수]
동양 오행: WOOD, FIRE, EARTH, METAL, WATER
동양 십신: BI_GYEON, GANG_JAE, SIK_SIN, SANG_GWAN, PYEON_JAE, JEONG_JAE, PYEON_GWAN, JEONG_GWAN, PYEON_IN, JEONG_IN
서양 원소: FIRE, EARTH, AIR, WATER
서양 양태: CARDINAL, FIXED, MUTABLE
서양 키워드: EMPATHY, INTUITION, IMAGINATION, BOUNDARY, LEADERSHIP, PASSION, ANALYSIS, STABILITY, COMMUNICATION, INNOVATION
별자리: 양자리, 황소자리, 쌍둥이자리, 게자리, 사자자리, 처녀자리, 천칭자리, 전갈자리, 사수자리, 염소자리, 물병자리, 물고기자리
천간: 甲乙丙丁戊己庚辛壬癸
지지: 子丑寅卯辰巳午未申酉戌亥

[검증 규칙]
- chart.gan/ji: 한자
- element_code: 도메인 코드
- ten_gods: 상위 3개, ETC 제외
- five_elements: 5개, percent 합계 = 100
- yin_yang: yin + yang = 100
- main_sign.name: 한글, 띄어쓰기X
- modality: 3개 고정
- detailed_analysis: 2개
- lucky: number만 아라비아, 나머지 한글

[완료 조건]
1. Pydantic 스키마 구현 (UserFortune)
2. 프롬프트 템플릿 구현
3. AWS 8B 모델 JSON 생성 성공
4. 모든 검증 규칙 통과
5. 5개+ 테스트 케이스 통과

[제외]
- 다이얼로그 (티키타카 채팅)
- cheongan_jiji 섹션 (chart에서 파생)
```

---

## 📋 단축 버전

```
/sc:pm "LLM 구조화 출력: PRD(docs/workflow/LLM_STRUCTURED_OUTPUT_PRD.md) 기반 Pydantic 스키마 + 프롬프트 + AWS 8B 테스트. 도메인 코드 엄격 준수." --strategy wave
```

---

## 🔄 개별 Phase 명령어

### Phase 1: 리서치
```
/sc:research "Qwen3 structured JSON output best practices, vLLM response_format, Pydantic v2 validator"
```

### Phase 2: 설계
```
/sc:design "UserFortune 스키마 설계 - PRD: docs/workflow/LLM_STRUCTURED_OUTPUT_PRD.md 기반, 도메인 코드 Enum, 검증 로직"
```

### Phase 3: 구현
```
/sc:implement "UserFortune Pydantic 스키마 (src/yeji_ai/models/user_fortune.py) + fortune_prompts.py 구현"
```

### Phase 4: 테스트
```
/sc:test "AWS 8B 모델로 구조화된 JSON 출력 테스트 - 동양/서양 사주, 검증 규칙 통과"
```

### Phase 5: 분석 (실패 시)
```
/sc:troubleshoot "JSON 출력 검증 실패 - 원인 분석 및 프롬프트/스키마 수정"
```

---

## 📁 예상 산출물

```
src/yeji_ai/
├── models/
│   └── user_fortune.py       # Pydantic 스키마 + Enum + Validator
├── prompts/
│   └── fortune_prompts.py    # 시스템 프롬프트 + 스키마 지시
├── services/
│   └── fortune_generator.py  # LLM 호출 서비스
└── tests/
    └── test_fortune_output.py

docs/pdca/structured-output/
├── plan.md                   # 가설, 설계
├── do.md                     # 구현 로그
├── check.md                  # 검증 결과
└── act.md                    # 개선, 패턴화
```

---

## 🎯 PDCA 사이클 흐름

```
┌─────────────────────────────────────────────────────────────────┐
│  Plan (가설)                                                     │
│  → 스키마 설계, 프롬프트 구조, 검증 규칙 정의                     │
│  → docs/pdca/structured-output/plan.md                          │
├─────────────────────────────────────────────────────────────────┤
│  Do (실험)                                                       │
│  → Pydantic 구현, 프롬프트 작성, AWS 8B 호출                     │
│  → 시행착오 기록: docs/pdca/structured-output/do.md              │
├─────────────────────────────────────────────────────────────────┤
│  Check (평가)                                                    │
│  → JSON 검증, 도메인 코드 일치, percent 합계                     │
│  → 결과 분석: docs/pdca/structured-output/check.md               │
├─────────────────────────────────────────────────────────────────┤
│  Act (개선)                                                      │
│  → 실패 시: 원인 분석 → 프롬프트/스키마 수정 → Do 반복           │
│  → 성공 시: 패턴화 → docs/patterns/ 이동                         │
│  → docs/pdca/structured-output/act.md                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## ⚠️ 주의사항

1. **도메인 코드 엄격 준수**: LLM이 임의로 코드를 생성하면 안 됨
2. **한자/한글/영어 형식**: 스키마에 정의된 대로 출력
3. **percent 합계**: five_elements(5개)=100, element_4(4개)=100, modality(3개)=100
4. **ten_gods**: 상위 3개만, ETC 제외
5. **별자리**: 띄어쓰기 없이 한글 (물병자리, 쌍둥이자리)

---

## 🔗 참조 파일

- PRD: `docs/workflow/LLM_STRUCTURED_OUTPUT_PRD.md`
- 프론트 스키마: `dummyFortuneV2.ts`
- 도메인 코드: `domainMapping.ts`
- 기존 스키마: `src/yeji_ai/models/llm_schemas.py`
