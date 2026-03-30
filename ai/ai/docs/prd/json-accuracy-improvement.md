# JSON 정확도 개선 PRD

> **문서 버전**: 1.0.0
> **작성일**: 2026-01-30
> **상태**: 계획 (Planning)
> **담당팀**: SSAFY YEJI AI팀
> **관련 문서**: [JSON 정확도 전략 분석](/ai/docs/analysis/json-accuracy-strategy-analysis.md)

---

## 목차

1. [문제 정의](#1-문제-정의)
2. [목표](#2-목표)
3. [범위](#3-범위)
4. [기능 요구사항](#4-기능-요구사항)
5. [비기능 요구사항](#5-비기능-요구사항)
6. [성공 지표 (KPI)](#6-성공-지표-kpi)
7. [구현 계획](#7-구현-계획)
8. [리스크 및 완화 방안](#8-리스크-및-완화-방안)
9. [참조 문서](#9-참조-문서)

---

## 1. 문제 정의

### 1.1 현황

LLM 모델(`tellang/yeji-8b-rslora-v7-AWQ`)이 생성하는 JSON 응답의 정확도가 약 **70%**에 불과하여, 약 **30%의 요청이 Pydantic 검증 실패**로 인해 503 에러를 반환하고 있습니다.

### 1.2 문제 유형별 분석

| 문제 유형 | 발생 빈도 | 영향 | 현재 대응 |
|-----------|-----------|------|----------|
| **Pydantic 검증 실패** | ~30% | 503 에러 반환 | 핫픽스 (optional 처리) |
| **필수 필드 누락** | ~20% | UX 저하 (빈 섹션) | 기본값으로 대체 |
| **코드 불일치** (대소문자) | ~15% | 검증 실패 | 수동 수정 |
| **구조 불일치** | ~10% | JSON 파싱 실패 | 재시도 |
| **언어 혼동** (영어/한국어) | ~5% | 프론트엔드 표시 문제 | 무시 |

### 1.3 현재 시스템 현황

```
[LLM Provider (vLLM)]
    ↓ response_format: {"type": "json_object"} (기본 JSON 모드)
[JSON 추출]
    ↓ 첫 번째 JSON 블록만 추출
[Pydantic 검증]
    ↓ ~30% 실패 → 503 에러
[API 응답]
```

**핵심 문제**:
- vLLM의 `guided_json` 기능이 이미 코드베이스에 정의되어 있으나 **미사용**
- 후처리 파이프라인이 구현되어 있으나 **활용도 부족**
- LLM 호출 레이어와 검증 레이어 사이에 **방어 로직 부재**

### 1.4 영향 범위

| 지표 | 현재 값 | 비고 |
|------|---------|------|
| Pydantic 검증 실패율 | **30%** | 핵심 문제 |
| 503 에러 발생률 | **3%** | 사용자 직접 영향 |
| 빈 keywords 응답률 | **100%** | 핫픽스로 인한 부작용 |
| 사용자 재시도율 | **15%** | 에러 발생 시 재요청 |

---

## 2. 목표

### 2.1 핵심 목표

**JSON 검증 실패율을 30%에서 5% 이하로 감소**시켜 안정적인 API 응답을 제공합니다.

### 2.2 세부 목표

| 목표 | 설명 | 우선순위 |
|------|------|----------|
| **안정성 향상** | 503 에러 발생률 0.5% 이하 | P0 |
| **품질 개선** | 빈 keywords 응답률 10% 이하 | P1 |
| **레이턴시 유지** | 추가 지연 50ms 이하 | P1 |
| **유지보수성** | 코드 복잡도 최소화 | P2 |

### 2.3 비목표 (Out of Scope)

- LLM 모델 재학습 또는 파인튜닝
- 프론트엔드 스키마 수정
- 새로운 LLM Provider 도입
- 프롬프트 대규모 재설계

---

## 3. 범위

### 3.1 적용 범위

| 운세 타입 | 스키마 | 적용 여부 |
|-----------|--------|----------|
| Eastern (동양 사주) | `EasternFullLLMOutput` | O |
| Western (서양 점성술) | `WesternFullLLMOutput` | O |
| Chat (대화형) | 자유 형식 | X (Phase 2 검토) |

### 3.2 권장 전략: 하이브리드 접근법

[JSON 정확도 전략 분석 문서](/ai/docs/analysis/json-accuracy-strategy-analysis.md)에 따라 **하이브리드 접근법**을 채택합니다.

```
[LLM 호출]
    ↓ guided_json (vLLM 레이어)
[구조적으로 유효한 JSON] (~95% 성공)
    ↓ 후처리 파이프라인
[정규화된 최종 JSON] (~99% 성공)
    ↓ Pydantic 검증
[API 응답]
```

**장점**:
- **guided_json**: 문법적으로 유효한 JSON 보장 (90-95%)
- **후처리**: 의미적 정규화 및 엣지 케이스 처리 (추가 5-10%)
- **결합 성공률**: **95-99%**

### 3.3 단계별 범위

| Phase | 범위 | 목표 성공률 | 기간 |
|-------|------|------------|------|
| **Phase 1** | 후처리 파이프라인 강화 | 85% | 1-2일 |
| **Phase 2** | vLLM guided_json 활성화 | 95% | 3-5일 |
| **Phase 3** | 모니터링 및 지속 개선 | 99% | 지속적 |

---

## 4. 기능 요구사항

### Phase 1: 후처리 파이프라인 강화

#### FR-101: 키워드 매핑 테이블 확장

**설명**: `extractors.py`의 `KEYWORD_MAPPING`을 확장하여 키워드 추출 정확도를 향상합니다.

**현재 상태**:
```python
KEYWORD_MAPPING = {
    "공감": "EMPATHY",
    "직관": "INTUITION",
    # ... 제한적인 매핑
}
```

**목표 상태**:
```python
KEYWORD_MAPPING_EXTENDED = {
    **KEYWORD_MAPPING,
    # 성격/특성 키워드
    "결단력": "CONFIDENCE",
    "유연성": "ADAPTABILITY",
    "협동심": "COMMUNICATION",
    "책임감": "RESPONSIBILITY",
    "창의성": "INNOVATION",
    "논리력": "ANALYSIS",
    "감수성": "SENSITIVITY",
    "인내심": "PATIENCE",
    "도전정신": "COURAGE",
    "사교성": "SOCIABILITY",
    # 운세 키워드
    "행운": "FORTUNE",
    "기회": "OPPORTUNITY",
    "성장": "GROWTH",
    "변화": "CHANGE",
    "안정": "STABILITY",
    # ... 총 50개 이상
}
```

**검수 기준**:
- 매핑 테이블 항목 50개 이상
- 키워드 추출 테스트 커버리지 > 90%

---

#### FR-102: JSON 복구 로직 강화

**설명**: 불완전한 JSON 응답을 자동으로 복구합니다.

**처리 케이스**:

| 케이스 | 입력 예시 | 출력 |
|--------|----------|------|
| 미닫힌 중괄호 | `{"key": "value"` | `{"key": "value"}` |
| 후행 콤마 | `{"a": 1,}` | `{"a": 1}` |
| 단일 따옴표 | `{'key': 'value'}` | `{"key": "value"}` |
| 반복 JSON | `{...}user{...}` | 첫 번째 JSON만 추출 |

**구현 위치**: `services/postprocessor/extractors.py`

```python
def repair_json(raw_text: str) -> str:
    """불완전한 JSON을 복구합니다.

    Args:
        raw_text: LLM 원본 응답

    Returns:
        복구된 JSON 문자열
    """
    # 1. 첫 번째 완전한 JSON 블록 추출
    # 2. 미닫힌 중괄호 자동 닫기
    # 3. 후행 콤마 제거
    # 4. 따옴표 정규화
    ...
```

---

#### FR-103: Enum 값 퍼지 매칭

**설명**: 잘못된 코드 값을 올바른 도메인 코드로 자동 변환합니다.

**매핑 규칙**:

| 카테고리 | 입력 | 출력 |
|----------|------|------|
| 대소문자 | `"fixed"` | `"FIXED"` |
| 대소문자 | `"Fire"` | `"FIRE"` |
| 유사어 | `"flexible"` | `"MUTABLE"` |
| 한글 | `"목"` | `"WOOD"` |
| 약어 | `"W"` | `"WATER"` |

**구현 위치**: `services/postprocessor/base.py` - `normalize_codes()`

```python
CODE_FUZZY_MAPPING = {
    # 오행 (Five Elements)
    "목": "WOOD", "wood": "WOOD", "나무": "WOOD",
    "화": "FIRE", "fire": "FIRE", "불": "FIRE",
    "토": "EARTH", "earth": "EARTH", "흙": "EARTH",
    "금": "METAL", "metal": "METAL", "쇠": "METAL",
    "수": "WATER", "water": "WATER", "물": "WATER",

    # 양태 (Modality)
    "fixed": "FIXED", "고정": "FIXED",
    "cardinal": "CARDINAL", "활동": "CARDINAL",
    "mutable": "MUTABLE", "변통": "MUTABLE", "flexible": "MUTABLE",
}
```

---

#### FR-104: 누락 필드 자동 생성

**설명**: 필수 필드가 누락된 경우 컨텍스트 기반으로 기본값을 생성합니다.

**대상 필드**:

| 필드 경로 | 기본값 생성 규칙 |
|-----------|-----------------|
| `stats.keywords` | `keywords_summary`에서 추출 |
| `stats.five_elements.list` | 객체 형태를 배열로 변환 |
| `lucky.color` | 오행 기반 색상 추론 |
| `lucky.number` | 생년월일 기반 숫자 생성 |

**구현 위치**: `services/postprocessor/eastern.py`, `western.py`

---

### Phase 2: vLLM guided_json 활성화

#### FR-201: guided_json 옵션 활성화

**설명**: vLLM의 guided_json 기능을 활성화하여 LLM 출력을 JSON 스키마에 맞게 제약합니다.

**현재 코드** (`vllm_client.py`):
```python
# 이미 정의되어 있으나 미사용
guided_json: dict | None = None
```

**변경 사항** (`llm_interpreter.py`):
```python
# 변경 전
config = GenerationConfig(
    max_tokens=1500,
    temperature=0.7,
)

# 변경 후
from yeji_ai.models.llm_schemas import EasternFullLLMOutput

config = GenerationConfig(
    max_tokens=1500,
    temperature=0.7,
    guided_json=EasternFullLLMOutput.model_json_schema(),
)
```

**검수 기준**:
- guided_json 활성화 후 JSON 문법 오류 0%
- 필수 필드 존재율 100%

---

#### FR-202: 스키마 호환성 검증

**설명**: XGrammar/Outlines와 현재 Pydantic 스키마의 호환성을 검증합니다.

**검증 항목**:

| 스키마 | 필드 수 | 중첩 깊이 | 호환성 테스트 |
|--------|---------|----------|--------------|
| `EasternFullLLMOutput` | 50+ | 4 | 필수 |
| `WesternFullLLMOutput` | 40+ | 3 | 필수 |
| `ChatResponse` | 10+ | 2 | 선택 |

**검증 방법**:
```python
# 스키마 호환성 테스트
@pytest.mark.parametrize("schema", [
    EasternFullLLMOutput,
    WesternFullLLMOutput,
])
def test_guided_json_compatibility(schema):
    json_schema = schema.model_json_schema()
    # XGrammar 컴파일 테스트
    # Outlines 폴백 테스트
```

---

#### FR-203: 폴백 메커니즘 구현

**설명**: guided_json 실패 시 기존 방식으로 폴백합니다.

**폴백 흐름**:
```
[guided_json 시도]
    ↓ 성공 → 응답 반환
    ↓ 실패 (스키마 미지원)
[기본 json_object 모드로 폴백]
    ↓
[후처리 파이프라인]
    ↓
[Pydantic 검증]
```

**구현**:
```python
async def _call_llm_with_fallback(
    self,
    messages: list[dict],
    schema: type[BaseModel],
) -> dict:
    """guided_json으로 호출하고 실패 시 폴백"""
    try:
        # 1차 시도: guided_json
        config = GenerationConfig(
            guided_json=schema.model_json_schema()
        )
        return await self._call_llm(messages, config)
    except GuidedJsonNotSupportedError:
        logger.warning("guided_json_fallback", schema=schema.__name__)
        # 2차 시도: 기본 json_object 모드
        config = GenerationConfig(
            response_format={"type": "json_object"}
        )
        return await self._call_llm(messages, config)
```

---

### Phase 3: 모니터링 및 지속 개선

#### FR-301: 검증 실패 메트릭 수집

**설명**: JSON 검증 실패 유형별 메트릭을 수집합니다.

**메트릭**:

| 메트릭 이름 | 설명 | 타입 |
|-------------|------|------|
| `json_validation_success_total` | 검증 성공 총 횟수 | Counter |
| `json_validation_failure_total` | 검증 실패 총 횟수 | Counter |
| `json_validation_failure_by_type` | 실패 유형별 횟수 | Counter (labels: type) |
| `postprocess_correction_count` | 후처리 수정 횟수 | Counter |
| `guided_json_fallback_count` | guided_json 폴백 횟수 | Counter |

---

#### FR-302: 실패 케이스 자동 수집

**설명**: 검증 실패한 응답을 자동으로 수집하여 분석합니다.

**수집 정보**:
```python
@dataclass
class FailureSample:
    timestamp: datetime
    schema_name: str
    raw_response: str
    validation_errors: list[str]
    postprocess_applied: bool
    request_context: dict  # 민감정보 제외
```

**저장 위치**: `logs/json_failures/`

---

## 5. 비기능 요구사항

### NFR-001: 레이턴시

| 요구사항 | 값 | 측정 방법 |
|----------|-----|----------|
| Phase 1 추가 레이턴시 | < 30ms | 후처리 함수 실행 시간 |
| Phase 2 추가 레이턴시 | < 50ms | guided_json 오버헤드 포함 |
| P99 레이턴시 | < 100ms | 전체 JSON 처리 시간 |

### NFR-002: 메모리 사용량

| 요구사항 | 값 | 비고 |
|----------|-----|------|
| 매핑 테이블 | < 5MB | 확장된 키워드 매핑 포함 |
| 스키마 캐시 | < 10MB | guided_json 스키마 컴파일 결과 |

### NFR-003: 에러 처리

- 후처리 실패 시 **원본 JSON 유지** (fail-safe)
- guided_json 실패 시 **기본 모드로 폴백**
- 모든 예외는 **로깅 후 graceful degradation**

### NFR-004: 하위 호환성

- 기존 API 응답 형식 **변경 없음**
- 기존 테스트 케이스 **100% 통과**
- Feature flag로 **롤백 가능**

### NFR-005: 테스트 커버리지

| 요구사항 | Phase 1 | Phase 2 |
|----------|---------|---------|
| 단위 테스트 커버리지 | > 90% | > 90% |
| 통합 테스트 케이스 | > 20개 | > 30개 |
| 엣지 케이스 테스트 | > 15개 | > 20개 |

---

## 6. 성공 지표 (KPI)

### 6.1 핵심 KPI

| 지표 | 현재 | Phase 1 목표 | Phase 2 목표 | 최종 목표 |
|------|------|-------------|-------------|----------|
| **Pydantic 검증 실패율** | 30% | 15% | 5% | **< 5%** |
| **503 에러 발생률** | 3% | 1.5% | 0.5% | **< 0.5%** |
| **빈 keywords 응답률** | 100% | 20% | 10% | **< 10%** |

### 6.2 보조 KPI

| 지표 | 현재 | 목표 | 비고 |
|------|------|------|------|
| 사용자 재시도율 | 15% | 5% | UX 개선 지표 |
| 평균 응답 시간 | 2.5s | 2.6s | 50ms 이내 증가 허용 |
| 후처리 성공률 | N/A | 95% | 신규 지표 |

### 6.3 모니터링 대시보드

```
┌─────────────────────────────────────────────────────────┐
│  JSON 정확도 대시보드                                    │
├─────────────────────────────────────────────────────────┤
│  검증 성공률:  [████████████░░░░░] 85%  (목표: 95%)      │
│  503 에러율:   [██░░░░░░░░░░░░░░░] 1.2% (목표: 0.5%)     │
│  후처리 적용:  [█████████████░░░░] 78%                   │
│  guided_json:  [████████████████░] 92%                   │
├─────────────────────────────────────────────────────────┤
│  실패 유형 분포:                                         │
│  - 필수 필드 누락: 45%                                   │
│  - 코드 불일치:    30%                                   │
│  - 구조 불일치:    20%                                   │
│  - 기타:           5%                                    │
└─────────────────────────────────────────────────────────┘
```

---

## 7. 구현 계획

### 7.1 Phase 1: 후처리 파이프라인 강화 (1-2일)

| 작업 | 담당 | 예상 시간 | 산출물 |
|------|------|----------|--------|
| FR-101: 키워드 매핑 확장 | AI팀 | 4h | `extractors.py` 수정 |
| FR-102: JSON 복구 로직 | AI팀 | 4h | `extractors.py` 수정 |
| FR-103: Enum 퍼지 매칭 | AI팀 | 4h | `base.py` 수정 |
| FR-104: 누락 필드 생성 | AI팀 | 4h | `eastern.py`, `western.py` 수정 |
| 테스트 작성 | AI팀 | 4h | `tests/test_postprocessor.py` |

**Phase 1 완료 조건**:
- 검증 실패율 30% → 15%
- 모든 단위 테스트 통과
- 기존 통합 테스트 100% 통과

### 7.2 Phase 2: vLLM guided_json 활성화 (3-5일)

| 작업 | 담당 | 예상 시간 | 산출물 |
|------|------|----------|--------|
| FR-201: guided_json 활성화 | AI팀 | 4h | `llm_interpreter.py` 수정 |
| FR-202: 스키마 호환성 검증 | AI팀 | 8h | 호환성 테스트 리포트 |
| FR-203: 폴백 메커니즘 | AI팀 | 8h | `llm_interpreter.py` 수정 |
| 성능 벤치마크 | AI팀 | 8h | 벤치마크 리포트 |
| 통합 테스트 | AI팀 | 8h | `tests/test_integration.py` |

**Phase 2 완료 조건**:
- 검증 실패율 15% → 5%
- guided_json 성공률 > 90%
- 레이턴시 증가 < 50ms

### 7.3 Phase 3: 모니터링 및 지속 개선 (지속적)

| 작업 | 담당 | 주기 | 산출물 |
|------|------|------|--------|
| FR-301: 메트릭 수집 | AI팀 | 1회 | 대시보드 구성 |
| FR-302: 실패 케이스 분석 | AI팀 | 주간 | 분석 리포트 |
| 매핑 테이블 업데이트 | AI팀 | 필요 시 | `extractors.py` 수정 |
| 성능 모니터링 | AI팀 | 상시 | 알림 설정 |

### 7.4 전체 타임라인

```
Week 1
├── Day 1-2: Phase 1 (후처리 강화)
│   ├── 키워드 매핑 확장
│   ├── JSON 복구 로직
│   ├── Enum 퍼지 매칭
│   └── 테스트 작성
│
├── Day 3-5: Phase 2 (guided_json)
│   ├── guided_json 활성화
│   ├── 스키마 호환성 검증
│   ├── 폴백 메커니즘
│   └── 성능 벤치마크

Week 2+
└── Phase 3 (지속적 개선)
    ├── 모니터링 대시보드
    ├── 실패 케이스 분석
    └── 규칙 업데이트
```

---

## 8. 리스크 및 완화 방안

### 8.1 기술 리스크

| 리스크 | 확률 | 영향 | 완화 방안 |
|--------|------|------|----------|
| XGrammar 스키마 미지원 | 20% | 중간 | Outlines 폴백, 스키마 단순화 |
| 추론 능력 저하 | 30% | 낮음-중간 | guided_json 선택적 적용 |
| 레이턴시 초과 | 20% | 중간 | 스키마 캐싱, 타임아웃 설정 |
| 후처리 버그 | 10% | 높음 | 철저한 테스트, 폴백 로직 |

### 8.2 운영 리스크

| 리스크 | 확률 | 영향 | 완화 방안 |
|--------|------|------|----------|
| 배포 중 장애 | 10% | 높음 | Feature flag, 점진적 롤아웃 |
| 롤백 필요 | 20% | 중간 | 즉시 롤백 가능한 구조 |
| 모니터링 누락 | 30% | 낮음 | 알림 임계값 설정 |

### 8.3 완화 전략

#### Feature Flag 구현
```python
# config.py
class Settings(BaseSettings):
    enable_guided_json: bool = Field(
        default=False,
        description="guided_json 활성화 여부"
    )
    enable_postprocessor: bool = Field(
        default=True,
        description="후처리 파이프라인 활성화 여부"
    )
```

#### 점진적 롤아웃
```
Phase 1: 개발 환경 (ai/develop) 100%
Phase 2: 프로덕션 10% → 50% → 100%
```

---

## 9. 참조 문서

### 9.1 내부 문서

| 문서 | 경로 | 설명 |
|------|------|------|
| JSON 정확도 전략 분석 | `ai/docs/analysis/json-accuracy-strategy-analysis.md` | 전략 검증 분석 |
| LLM 응답 후처리 PRD | `ai/docs/prd/llm-response-postprocessor.md` | 후처리 시스템 설계 |
| LLM 출력 품질 분석 | `docs/analysis/LLM_OUTPUT_QUALITY_ANALYSIS.md` | 현재 문제 분석 |
| 구조화 출력 PRD | `docs/workflow/LLM_STRUCTURED_OUTPUT_PRD.md` | 스키마 정의 |

### 9.2 외부 참조

| 자료 | URL | 설명 |
|------|-----|------|
| vLLM Structured Outputs | https://docs.vllm.ai/en/latest/features/structured_outputs/ | 공식 문서 |
| XGrammar | https://github.com/mlc-ai/xgrammar | guided decoding 라이브러리 |
| Outlines | https://github.com/outlines-dev/outlines | 폴백 옵션 |

### 9.3 관련 코드

| 파일 | 경로 | 설명 |
|------|------|------|
| vLLM 클라이언트 | `ai/src/yeji_ai/clients/vllm_client.py` | guided_json 옵션 정의 |
| LLM 인터프리터 | `ai/src/yeji_ai/services/llm_interpreter.py` | LLM 호출 로직 |
| 후처리 베이스 | `ai/src/yeji_ai/services/postprocessor/base.py` | 후처리 인터페이스 |
| 동양 후처리기 | `ai/src/yeji_ai/services/postprocessor/eastern.py` | 동양 사주 후처리 |
| 서양 후처리기 | `ai/src/yeji_ai/services/postprocessor/western.py` | 서양 점성술 후처리 |
| 추출기 | `ai/src/yeji_ai/services/postprocessor/extractors.py` | 키워드 추출 |

---

## 변경 이력

| 버전 | 날짜 | 변경 내용 | 작성자 |
|------|------|----------|--------|
| 1.0.0 | 2026-01-30 | 초기 버전 | YEJI AI팀 |

---

> **Note**: 이 PRD는 [JSON 정확도 전략 분석](/ai/docs/analysis/json-accuracy-strategy-analysis.md) 문서의 권장 사항을 기반으로 작성되었습니다. 하이브리드 접근법(후처리 + guided_json)을 통해 JSON 검증 실패율을 30%에서 5% 이하로 감소시키는 것을 목표로 합니다.
