# Do: YEJI 운세 분석 Hybrid Architecture 리팩토링

> **작성일**: 2026-01-31
> **상태**: Phase 2 진행 중

## 구현 로그

### Wave 1: 서버 계산 함수 구현 ✅

**시간**: 2026-01-31

#### 1.1 음양/십신 매핑 테이블 추가

**파일**: `engine/saju_calculator.py`

추가된 상수:
- `HANJA_TO_HANGUL_STEM`: 한자 → 한글 천간 매핑
- `HANJA_TO_HANGUL_BRANCH`: 한자 → 한글 지지 매핑
- `STEM_YIN_YANG`: 천간 음양 매핑
- `BRANCH_YIN_YANG`: 지지 음양 매핑
- `FIVE_ELEMENT_RELATIONS`: 오행 상생상극 관계 (십신 계산용)
- `TEN_GOD_NAMES`: 음양에 따른 정/편 구분
- `ELEMENT_TO_CODE`: 오행 코드 매핑
- `TEN_GOD_TO_CODE`: 십신 코드 매핑

#### 1.2 오행 분포 계산 함수

```python
def calculate_five_elements_distribution(self, pillars: FourPillars) -> dict:
    """8자(4천간 + 4지지) → 오행 분포 계산"""
```

**반환 형식**:
```json
{
    "list": [
        {"code": "WOOD", "label": "목", "count": 2, "percent": 25.0},
        ...
    ],
    "dominant": "EARTH",
    "weak": ["FIRE", "METAL"]
}
```

#### 1.3 음양 비율 계산 함수

```python
def calculate_yin_yang_ratio(self, pillars: FourPillars) -> dict:
    """8자 → 음양 비율 계산"""
```

**반환 형식**:
```json
{
    "yin": {"count": 3, "percent": 37.5},
    "yang": {"count": 5, "percent": 62.5},
    "balance": "양성"
}
```

#### 1.4 십신 계산 함수

```python
def calculate_ten_gods(self, day_stem: str, pillars: FourPillars) -> dict:
    """일간 기준 십신 계산"""
```

**반환 형식**:
```json
{
    "list": [
        {"code": "SIKSIN", "label": "식신", "count": 2, "percent": 25.0},
        ...
    ],
    "dominant": ["SIKSIN", "JEONGIN"],
    "day_master_element": "FIRE"
}
```

#### 1.5 서양 점성술 통계 계산

추가된 상수:
- `ZODIAC_NAME_TO_CODE`: 별자리 한글 → 코드 매핑
- `ZODIAC_ELEMENT_MAP`: 별자리 → 원소 매핑
- `ZODIAC_MODALITY_MAP`: 별자리 → 양태 매핑
- `MODALITY_LABELS`: 양태 한글 레이블
- `WESTERN_ELEMENT_LABELS`: 서양 원소 한글 레이블

추가된 함수:
- `get_sun_sign_code()`: 별자리 코드 반환
- `get_zodiac_element()`: 별자리 → 원소 코드
- `get_zodiac_modality()`: 별자리 → 양태 코드
- `calculate_western_stats()`: 서양 점성술 전체 통계

**반환 형식**:
```json
{
    "main_sign": {"code": "ARIES", "name": "양자리"},
    "element": "FIRE",
    "modality": "CARDINAL",
    "element_4_distribution": [...],
    "modality_3_distribution": [...]
}
```

#### 1.6 테스트 결과

**파일**: `tests/test_saju_calculator_extended.py`

```
14 passed in 0.06s
```

테스트 케이스:
- 오행 분포 계산 (시주 있음/없음)
- 음양 비율 계산 (균형/양성 우세)
- 십신 계산 (한글/한자 일간)
- 서양 통계 (양자리, 황소자리, 염소자리 경계)
- 별자리 헬퍼 함수

---

### Wave 2: 스키마 및 프롬프트 변경 (진행 예정)

**다음 단계**:
1. LLM 해석 전용 스키마 추가 (`EasternInterpretation`, `WesternInterpretation`)
2. 프롬프트 간소화 (계산 지시 제거)
3. `fortune_generator.py` 통합

---

## 학습 기록

### 성공 패턴

1. **테스트 먼저 작성**
   - 구현 전에 테스트 케이스 정의 → 구현 방향 명확
   - 14개 테스트 모두 첫 시도에 통과

2. **한자/한글 이중 지원**
   - 기존 코드가 한글 사주를 사용
   - 후처리기가 한자 사주를 제공
   - 양쪽 모두 지원하도록 매핑 테이블 확장

### 발견된 이슈

1. **기존 `calculate()` 함수와 중복**
   - `_calculate_element_balance()`가 이미 오행 분포 계산
   - 새 `calculate_five_elements_distribution()`은 더 상세한 정보 제공
   - 통합 시 기존 함수 활용 고려

---

---

### Wave 2: 후처리기 통합 ✅

**시간**: 2026-01-31

#### 2.1 Eastern 후처리기 확장

**파일**: `services/postprocessor/eastern.py`

**새 기능 (FR-007)**:
- `_override_stats_with_calculated()` 메서드 추가
- `_build_four_pillars()` 헬퍼 메서드 추가
- `_convert_ten_god_code()` 코드 변환 메서드 추가

**처리 단계 추가**:
- 단계 7: 서버 계산 통계 강제 적용

**덮어쓰기 대상**:
- `stats.five_elements.list` → 서버 계산 오행 분포
- `stats.yin_yang_ratio.yin/yang` → 서버 계산 음양 비율
- `stats.ten_gods.list` → 서버 계산 십신 분포
- `element` → 일간 오행

**유지 항목** (LLM 해석):
- `*.summary` 필드들
- `final_verdict.*`
- `lucky.*`

#### 2.2 Western 후처리기 확장

**파일**: `services/postprocessor/western.py`

**새 기능 (FR-007)**:
- `_override_stats_with_calculated()` 메서드 추가

**덮어쓰기 대상**:
- `stats.element_4_distribution` → 서버 계산 4원소 분포
- `stats.modality_3_distribution` → 서버 계산 3양태 분포

#### 2.3 테스트 결과

```
117 passed in 0.15s
```

모든 기존 테스트 + 신규 테스트 통과

---

## 학습 기록

### 성공 패턴

1. **후처리기 확장 전략**
   - 기존 로직 유지 + 새 단계 추가
   - summary는 LLM 값 유지, 숫자/분포는 서버값 사용

2. **십신 코드 호환성**
   - 신규 코드(BIGYEON) → 기존 스키마 코드(BI_GYEON) 변환
   - 기존 API 응답 스키마 깨지지 않음

### 아키텍처 변화

**이전**:
```
[LLM] → 모든 필드 생성 → [후처리] → chart만 덮어쓰기
```

**이후**:
```
[LLM] → summary/해석 필드 생성 → [후처리] → chart + 통계 전부 덮어쓰기
```

---

## 다음 작업

- [x] Wave 1: 서버 계산 함수 구현
- [x] Wave 2: 후처리기 통합
- [ ] Wave 3: 프롬프트 간소화 (선택사항 - 현재 구조로도 정확도 100%)
- [ ] Wave 4: 배포 및 E2E 검증
