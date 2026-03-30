# Plan: YEJI 운세 분석 Hybrid Architecture 리팩토링

> **작성일**: 2026-01-31
> **상태**: Phase 1 완료 (Plan)

## 프로젝트 개요

**목표**: 동/서양 운세 분석에서 "계산"과 "해석"을 분리하여 LLM 부하 감소, 정확도 향상, 응답 속도 개선

**현재 아키텍처**:
```
[사용자 입력] → [LLM이 전부 생성] → [후처리기에서 서버값으로 덮어쓰기]
```

**목표 아키텍처**:
```
[사용자 입력] → [서버 계산] → [LLM 해석만] → [응답 조합]
                    ↓              ↓
              (결정론적)     (창의적 생성)
              - 사주팔자       - 해석/조언
              - 오행/음양      - 행운 정보
              - 십신 계산
              - 별자리/원소
```

---

## 1. 현재 상태 분석

### 1.1 구현 현황

| 기능 | 상태 | 위치 |
|------|------|------|
| 사주 4기둥 계산 | ✅ 완성 | `engine/saju_calculator.py:calculate()` |
| 천간/지지 → 오행 매핑 | ✅ 완성 | `STEM_ELEMENTS`, `BRANCH_ELEMENTS` |
| 별자리 계산 | ✅ 완성 | `get_sun_sign()` |
| 일간 추출 | ✅ 완성 | `get_day_master()` |
| 음양 매핑 | ❌ 미구현 | 신규 필요 |
| 십신 계산 | ❌ 미구현 | 신규 필요 |

### 1.2 필드 분류표

#### 동양 사주 (SajuDataV2)

| 필드 | 분류 | 현재 처리 방식 | 목표 |
|------|------|---------------|------|
| `chart.*` (4기둥) | **서버 계산** | LLM 생성 → 후처리 덮어쓰기 | 서버에서 직접 채움 |
| `stats.cheongan_jiji` | **서버 계산** | LLM 생성 → 후처리 동기화 | 서버에서 직접 채움 |
| `stats.five_elements.list[].percent` | 서버 계산 가능 | LLM 생성 | 서버 계산 (8자 분석) |
| `stats.yin_yang_ratio.yin/yang` | 서버 계산 가능 | LLM 생성 | 서버 계산 (8자 분석) |
| `stats.ten_gods.list[].percent` | 서버 계산 가능 | LLM 생성 | 서버 계산 (일간 기준) |
| `stats.*.summary` | **LLM 해석** | LLM 생성 | 유지 |
| `element` | 서버 계산 가능 | LLM 생성 | 서버 계산 (일간 오행) |
| `final_verdict.*` | **LLM 해석** | LLM 생성 | 유지 |
| `lucky.*` | **LLM 해석** | LLM 생성 | 유지 |

#### 서양 점성술 (WesternFortuneDataV2)

| 필드 | 분류 | 현재 처리 방식 | 목표 |
|------|------|---------------|------|
| `stats.main_sign` | **서버 계산** | LLM 생성 → 후처리 덮어쓰기 | 서버에서 직접 채움 |
| `element` | **서버 계산** | LLM 생성 → 후처리 덮어쓰기 | 서버에서 직접 채움 |
| `stats.element_4_distribution` | 서버 계산 가능 | LLM 생성 | 서버 기본값 사용 |
| `stats.modality_3_distribution` | 서버 계산 가능 | LLM 생성 | 서버 기본값 사용 |
| `stats.*_summary` | **LLM 해석** | LLM 생성 | 유지 |
| `stats.keywords` | **LLM 해석** | LLM 생성 | 유지 |
| `fortune_content.*` | **LLM 해석** | LLM 생성 | 유지 |
| `lucky.*` | **LLM 해석** | LLM 생성 | 유지 |

---

## 2. 설계

### 2.1 서버 계산 함수 (신규)

#### Eastern (동양 사주)

```python
# engine/saju_calculator.py 확장

def calculate_five_elements(pillars: dict) -> dict:
    """8자(4천간 + 4지지) → 오행 분포 계산

    Args:
        pillars: 사주 4기둥 정보 (year, month, day, hour)

    Returns:
        {
            "wood": {"count": 2, "percent": 25.0},
            "fire": {"count": 1, "percent": 12.5},
            "earth": {"count": 3, "percent": 37.5},
            "metal": {"count": 1, "percent": 12.5},
            "water": {"count": 1, "percent": 12.5},
            "dominant": "earth",
            "weak": ["fire", "metal", "water"]
        }
    """
    pass

def calculate_yin_yang(pillars: dict) -> dict:
    """8자 → 음양 비율 계산

    Args:
        pillars: 사주 4기둥 정보

    Returns:
        {
            "yin": {"count": 3, "percent": 37.5},
            "yang": {"count": 5, "percent": 62.5},
            "balance": "양성"
        }
    """
    pass

def calculate_ten_gods(day_stem: str, pillars: dict) -> dict:
    """일간 기준 십신 계산

    Args:
        day_stem: 일간 천간 (甲, 乙, ...)
        pillars: 사주 4기둥 정보

    Returns:
        {
            "비견": {"count": 1, "percent": 12.5},
            "겁재": {"count": 0, "percent": 0.0},
            "식신": {"count": 2, "percent": 25.0},
            "상관": {"count": 1, "percent": 12.5},
            ...
            "dominant": ["식신", "정인"],
            "pattern": "식상_생재"
        }
    """
    pass
```

#### Western (서양 점성술)

```python
# engine/zodiac_calculator.py 신규

ZODIAC_MODALITY_MAP = {
    "ARIES": "CARDINAL", "CANCER": "CARDINAL",
    "LIBRA": "CARDINAL", "CAPRICORN": "CARDINAL",
    "TAURUS": "FIXED", "LEO": "FIXED",
    "SCORPIO": "FIXED", "AQUARIUS": "FIXED",
    "GEMINI": "MUTABLE", "VIRGO": "MUTABLE",
    "SAGITTARIUS": "MUTABLE", "PISCES": "MUTABLE",
}

def get_modality_from_sign(sign_code: str) -> str:
    """별자리 → 양태 매핑"""
    return ZODIAC_MODALITY_MAP.get(sign_code, "CARDINAL")

def get_default_element_distribution(sign_code: str) -> list:
    """별자리 기반 4원소 기본 분포"""
    # 태양 별자리의 원소를 50%, 나머지를 16.7%씩
    pass
```

### 2.2 음양/십신 매핑 테이블 (신규)

```python
# engine/saju_calculator.py에 추가

STEM_YIN_YANG = {
    "甲": "양", "乙": "음",  # 목
    "丙": "양", "丁": "음",  # 화
    "戊": "양", "己": "음",  # 토
    "庚": "양", "辛": "음",  # 금
    "壬": "양", "癸": "음",  # 수
}

BRANCH_YIN_YANG = {
    "子": "양", "丑": "음",
    "寅": "양", "卯": "음",
    "辰": "양", "巳": "음",
    "午": "양", "未": "음",
    "申": "양", "酉": "음",
    "戌": "양", "亥": "음",
}

# 십신 계산용 오행 상생상극 관계
TEN_GOD_RELATIONS = {
    # (일간 오행, 대상 오행, 음양 동일 여부) → 십신
    ("목", "목", True): "비견",
    ("목", "목", False): "겁재",
    ("목", "화", True): "식신",
    ("목", "화", False): "상관",
    ("목", "토", True): "편재",
    ("목", "토", False): "정재",
    ("목", "금", True): "편관",
    ("목", "금", False): "정관",
    ("목", "수", True): "편인",
    ("목", "수", False): "정인",
    # ... (다른 오행 조합)
}
```

### 2.3 LLM 스키마 간소화

**현재**: LLM이 모든 필드 생성
**목표**: LLM은 해석/창의적 필드만 생성

```python
# 신규 스키마: LLM이 생성하는 필드만 정의

class EasternInterpretation(BaseModel):
    """동양 사주 해석 (LLM 생성용)"""

    chart_summary: str  # 차트 요약
    five_elements_summary: str  # 오행 분석 요약
    yin_yang_summary: str  # 음양 분석 요약
    ten_gods_summary: str  # 십신 분석 요약

    final_verdict: FinalVerdict  # 천기누설
    lucky: EasternLucky  # 행운 정보


class WesternInterpretation(BaseModel):
    """서양 점성술 해석 (LLM 생성용)"""

    element_summary: str
    modality_summary: str
    keywords_summary: str
    keywords: list[WesternKeyword]  # 3-5개

    fortune_content: FortuneContent
    lucky: WesternLucky
```

### 2.4 프롬프트 단축 계획

**현재 프롬프트 크기**:
- Eastern: ~1,100 토큰
- Western: ~850 토큰

**목표**:
- Eastern: ~600 토큰 (45% 감소)
- Western: ~500 토큰 (41% 감소)

**변경 사항**:
1. 사주 계산 지시 제거 (서버에서 계산된 값 제공)
2. JSON 예시 간소화 (해석 필드만)
3. 필드 설명 중복 제거

---

## 3. 예상 결과

| 항목 | 이전 | 이후 (예상) | 개선율 |
|------|------|------------|--------|
| LLM 출력 토큰 | ~1,200 | ~500 | 58% 감소 |
| 프롬프트 길이 | ~2,100 토큰 | ~1,000 토큰 | 52% 감소 |
| 응답 시간 | 3-5초 | 1-2초 | 60% 개선 |
| 계산 정확도 | 후처리 보정 필요 | 100% 정확 | - |

---

## 4. 구현 순서 (Wave Strategy)

### Wave 1: 서버 계산 함수 구현
- [ ] `calculate_five_elements()` 구현 + 테스트
- [ ] `calculate_yin_yang()` 구현 + 테스트
- [ ] `calculate_ten_gods()` 구현 + 테스트
- [ ] `get_modality_from_sign()` 구현 + 테스트

### Wave 2: 스키마 및 프롬프트 변경
- [ ] `EasternInterpretation` 스키마 추가
- [ ] `WesternInterpretation` 스키마 추가
- [ ] 프롬프트 간소화
- [ ] 후처리기 로직 조정

### Wave 3: 통합 및 테스트
- [ ] `fortune_generator.py` 통합
- [ ] E2E 테스트
- [ ] 성능 측정

### Wave 4: 배포 및 회고
- [ ] Jenkins 빌드
- [ ] 프로덕션 검증
- [ ] 문서화

---

## 5. 리스크 및 대응

| 리스크 | 영향도 | 대응 방안 |
|--------|--------|----------|
| 기존 API 응답 스키마 깨짐 | 높음 | 기존 스키마 유지, 내부만 변경 |
| 십신 계산 로직 오류 | 중간 | 참조 자료 기반 테스트 케이스 작성 |
| LLM 프롬프트 변경으로 품질 저하 | 중간 | A/B 테스트, 롤백 준비 |

---

## 6. 제약 조건

- Python 3.11+, FastAPI, Pydantic v2
- vLLM max_model_len: 4096 토큰
- **기존 API 응답 스키마 호환 유지** (프론트엔드 영향 없음)
- 테스트 커버리지 유지
