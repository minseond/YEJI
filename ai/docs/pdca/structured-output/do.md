# Do: LLM 구조화된 출력 시스템 구현

> 작성일: 2026-01-29
> 상태: Wave 2 진행 중

---

## 구현 로그 (시계열)

### 10:00 - Wave 1 완료: 현재 상태 분석

**분석 결과:**
- 프로젝트 구조: `ai/src/yeji_ai/` 폴더가 최신 코드
- 기존 스키마: `llm_schemas.py` - 프론트엔드와 Gap 존재
- 프롬프트: `engine/prompts.py`, `services/llm_interpreter.py`에 분산

**발견된 Gap:**
1. 동양: `element` 필드 없음, `final_verdict` 없음, `value` 필드 불필요
2. 서양: `main_sign.name` 영문→한글 변환 필요, `fortune_content` 없음

### 10:30 - Wave 2 시작: 스키마 및 프롬프트 구현

**생성된 파일:**

1. `ai/src/yeji_ai/models/enums/domain_codes.py`
   - EastElementCode Enum (WOOD/FIRE/EARTH/METAL/WATER)
   - WestElementCode Enum (FIRE/EARTH/AIR/WATER)
   - TenGodCode Enum (10개 + ETC)
   - ModalityCode Enum (CARDINAL/FIXED/MUTABLE)
   - WestKeywordCode Enum (10개)
   - ZodiacSignKR Enum (12개 한글 별자리)
   - 한글 레이블 매핑 딕셔너리

2. `ai/src/yeji_ai/models/user_fortune.py`
   - SajuDataV2: 프론트엔드 eastern 스키마와 완전 호환
   - WesternFortuneDataV2: 프론트엔드 western 스키마와 완전 호환
   - UserFortune: 통합 모델
   - @field_validator: 도메인 코드 검증
   - @model_validator: percent 합계 검증

3. `ai/src/yeji_ai/prompts/fortune_prompts.py`
   - EASTERN_SYSTEM_PROMPT: /no_think, 소이설 캐릭터
   - WESTERN_SYSTEM_PROMPT: /no_think, 스텔라 캐릭터
   - EASTERN_SCHEMA_INSTRUCTION: <constraints> XML 태그, JSON 스키마
   - WESTERN_SCHEMA_INSTRUCTION: <constraints> XML 태그, JSON 스키마
   - build_eastern_generation_prompt(): 동양 사주 프롬프트 빌더
   - build_western_generation_prompt(): 서양 점성술 프롬프트 빌더
   - EASTERN_EXAMPLE, WESTERN_EXAMPLE: 테스트용 예시 데이터

### 11:00 - 병렬 작업 시작

**Task #1**: 스키마 모델 테스트 작성 (진행 중)
- 유효 데이터 검증, 도메인 코드 검증, percent 합계 검증

**Task #2**: fortune_generator.py 서비스 구현 (진행 중)
- AWS Provider 연동, response_format 설정

**Task #3**: AWS 8B 모델 통합 테스트 (대기 - Task #1, #2 완료 후)

---

## 시행착오 및 해결

### 이슈 #1: 프론트엔드-백엔드 스키마 Gap

**문제**: 기존 `llm_schemas.py`가 프론트엔드 `dummyFortuneV2.ts`와 불일치

**원인 분석**:
- 백엔드: `value` + `percent` 필드 사용
- 프론트엔드: `percent`만 사용
- 백엔드: 영문 코드 (ARIES)
- 프론트엔드: 한글 (양자리)

**해결**: 새로운 `user_fortune.py` 생성하여 프론트엔드 스키마에 완전 맞춤

### 이슈 #2: 천간/지지 검증

**문제**: LLM이 잘못된 한자를 생성할 수 있음

**해결**:
```python
CHEON_GAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
JI_JI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

@field_validator("gan")
def validate_gan(cls, v):
    if v not in CHEON_GAN:
        raise ValueError(...)
```

### 이슈 #3: percent 합계 정확도

**문제**: LLM이 소수점 반올림으로 합계가 99 또는 101이 될 수 있음

**해결**: 1% 허용 오차 적용
```python
if not (99.0 <= total <= 101.0):
    raise ValueError(...)
```

---

## 학습 포인트

1. **프론트엔드 스키마 우선**: 백엔드 스키마를 프론트엔드에 맞추는 것이 통합 비용 절감
2. **Literal vs Enum**: Pydantic에서는 `Literal[]`이 JSON 직렬화에 더 깔끔
3. **XML 태그 프롬프팅**: Qwen3에서 `<constraints>` 태그가 제약 조건 강조에 효과적
4. **검증 계층화**: @field_validator → @model_validator 순서로 검증 적용

---

## 다음 단계

- [ ] Task #1, #2 완료 대기
- [ ] Task #3: AWS 8B 모델 통합 테스트
- [ ] check.md: 테스트 결과 분석
- [ ] act.md: 성공 패턴 문서화 또는 수정 사항 반영
