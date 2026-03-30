# LLM 응답 후처리 아키텍처

> **문서 버전**: 1.0.0
> **작성일**: 2026-01-30
> **상태**: 설계 완료 (Design Complete)
> **담당팀**: SSAFY YEJI AI팀

---

## 1. 개요

### 1.1 목적

LLM 응답과 Pydantic 검증 사이에 **후처리 레이어**를 도입하여:
- LLM이 생성한 불완전한 JSON 보완
- 누락된 필수 필드에 적절한 기본값 채우기
- 구조 변환 및 코드 정규화 수행

### 1.2 설계 원칙

1. **Protocol 기반 확장성**: Python Protocol을 사용하여 새로운 후처리기 추가 용이
2. **파이프라인 패턴**: 단계별 변환을 체인으로 연결하여 유지보수성 향상
3. **Fail-Safe**: 후처리 실패 시 원본 JSON 유지 (graceful degradation)
4. **타입 안전성**: 모든 함수에 타입 힌트 적용

---

## 2. 모듈 구조

```
ai/src/yeji_ai/services/postprocessor/
├── __init__.py              # 공개 API 정의
├── base.py                  # Protocol 및 기본 타입 정의
├── western.py               # 서양 점성술 후처리기
├── eastern.py               # 동양 사주 후처리기
└── extractors.py            # 키워드 추출 등 유틸리티
```

---

## 3. 아키텍처 다이어그램

### 3.1 처리 흐름

```
┌─────────────────────────────────────────────────────────────────────┐
│                      FortuneGenerator                                │
│                                                                      │
│  ┌──────────────┐    ┌──────────────────┐    ┌──────────────────┐   │
│  │ LLM Provider │───▶│   JSON 추출기     │───▶│   후처리 파이프라인  │   │
│  └──────────────┘    └──────────────────┘    └──────────────────┘   │
│                                                         │            │
│                                                         ▼            │
│                                              ┌──────────────────┐   │
│                                              │ Pydantic 검증     │   │
│                                              └──────────────────┘   │
│                                                         │            │
│                                                         ▼            │
│                                              ┌──────────────────┐   │
│                                              │   API 응답        │   │
│                                              └──────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 후처리 파이프라인 상세

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PostprocessPipeline                               │
│                                                                      │
│   ┌────────────┐   ┌────────────┐   ┌────────────┐   ┌────────────┐ │
│   │ JSON 추출   │──▶│ 구조 변환   │──▶│ 필드 채우기 │──▶│ 코드 정규화 │ │
│   │ Extractor  │   │ Converter  │   │ Filler     │   │ Normalizer │ │
│   └────────────┘   └────────────┘   └────────────┘   └────────────┘ │
│                                                                      │
│   FR-005           FR-003           FR-002           FR-004          │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 4. 인터페이스 설계

### 4.1 핵심 Protocol

```python
from typing import Protocol, Any

class ResponsePostprocessor(Protocol):
    """LLM 응답 후처리기 인터페이스

    모든 후처리기는 이 Protocol을 구현해야 합니다.
    """

    def process(self, raw: dict[str, Any]) -> dict[str, Any]:
        """원본 LLM 응답을 후처리하여 정규화된 결과 반환

        Args:
            raw: LLM이 생성한 원본 JSON 딕셔너리

        Returns:
            후처리된 JSON 딕셔너리

        Note:
            처리 실패 시 원본을 그대로 반환 (fail-safe)
        """
        ...
```

### 4.2 파이프라인 단계 Protocol

```python
class PipelineStep(Protocol):
    """파이프라인 단계 인터페이스"""

    @property
    def name(self) -> str:
        """단계 이름 (로깅/모니터링용)"""
        ...

    def transform(self, data: dict[str, Any]) -> dict[str, Any]:
        """데이터 변환 수행"""
        ...
```

### 4.3 추출기 Protocol

```python
class KeywordExtractor(Protocol):
    """키워드 추출기 인터페이스"""

    def extract(self, text: str) -> list[dict[str, Any]]:
        """텍스트에서 키워드 추출

        Args:
            text: 분석할 텍스트 (keywords_summary 등)

        Returns:
            추출된 키워드 목록
            [{"code": "LEADERSHIP", "label": "리더십", "weight": 0.9}, ...]
        """
        ...
```

---

## 5. 클래스 설계

### 5.1 WesternPostprocessor

서양 점성술 응답 후처리기. `WesternFortuneDataV2` 스키마에 맞게 응답을 정규화합니다.

**책임**:
- `keywords` 배열 생성 (FR-001)
- 필수 필드 기본값 채우기 (FR-002)
- 4원소/3양태 구조 변환 (FR-003)
- 코드 대소문자 정규화 (FR-004)

```python
class WesternPostprocessor:
    """서양 점성술 후처리기

    Attributes:
        keyword_extractor: 키워드 추출기
        default_values: 기본값 정의
    """

    def __init__(
        self,
        keyword_extractor: KeywordExtractor | None = None,
    ) -> None: ...

    def process(self, raw: dict[str, Any]) -> dict[str, Any]: ...

    def _fill_keywords(self, stats: dict[str, Any]) -> dict[str, Any]: ...
    def _normalize_codes(self, data: dict[str, Any]) -> dict[str, Any]: ...
    def _fill_defaults(self, data: dict[str, Any]) -> dict[str, Any]: ...
```

### 5.2 EasternPostprocessor

동양 사주 응답 후처리기. `SajuDataV2` 스키마에 맞게 응답을 정규화합니다.

**책임**:
- 필수 필드 기본값 채우기 (FR-002)
- 오행/십신 구조 변환 (FR-003)
- 천간지지 코드 정규화 (FR-004)

```python
class EasternPostprocessor:
    """동양 사주 후처리기

    Attributes:
        default_values: 기본값 정의
    """

    def __init__(self) -> None: ...

    def process(self, raw: dict[str, Any]) -> dict[str, Any]: ...

    def _normalize_pillars(self, chart: dict[str, Any]) -> dict[str, Any]: ...
    def _normalize_codes(self, data: dict[str, Any]) -> dict[str, Any]: ...
    def _fill_defaults(self, data: dict[str, Any]) -> dict[str, Any]: ...
```

### 5.3 PostprocessPipeline

여러 단계를 순차적으로 실행하는 파이프라인 클래스.

```python
class PostprocessPipeline:
    """후처리 파이프라인

    여러 PipelineStep을 순차적으로 실행합니다.
    각 단계는 이전 단계의 출력을 입력으로 받습니다.
    """

    def __init__(self, steps: list[PipelineStep] | None = None) -> None: ...

    def add_step(self, step: PipelineStep) -> "PostprocessPipeline": ...

    def execute(self, data: dict[str, Any]) -> PostprocessResult: ...
```

### 5.4 PostprocessResult

후처리 결과를 담는 데이터 클래스.

```python
@dataclass
class PostprocessResult:
    """후처리 결과

    Attributes:
        data: 후처리된 데이터
        original: 원본 데이터
        steps_applied: 적용된 단계 목록
        errors: 발생한 에러 목록 (단계별)
        latency_ms: 후처리 소요 시간 (ms)
    """

    data: dict[str, Any]
    original: dict[str, Any]
    steps_applied: list[str]
    errors: list[PostprocessError]
    latency_ms: float
```

---

## 6. 기본값 정의

### 6.1 Western 기본값

```python
WESTERN_DEFAULTS = {
    "stats.element_summary": "원소 분석 결과입니다.",
    "stats.modality_summary": "양태 분석 결과입니다.",
    "stats.keywords_summary": "키워드 분석 결과입니다.",
    "fortune_content.overview": "오늘의 운세입니다.",
    "fortune_content.advice": "조언을 참고하세요.",
    "lucky.color": "보라색",
    "lucky.number": "3",
}
```

### 6.2 Eastern 기본값

```python
EASTERN_DEFAULTS = {
    "chart.summary": "사주 분석 결과입니다.",
    "stats.five_elements.summary": "오행 분포 분석입니다.",
    "stats.yin_yang_ratio.summary": "음양 균형 분석입니다.",
    "stats.ten_gods.summary": "십신 분포 분석입니다.",
    "final_verdict.summary": "종합 분석 결과입니다.",
    "final_verdict.strength": "강점을 분석 중입니다.",
    "final_verdict.weakness": "보완점을 분석 중입니다.",
    "final_verdict.advice": "조언을 준비 중입니다.",
    "lucky.color": "파란색",
    "lucky.number": "7",
    "lucky.item": "행운의 물건",
}
```

---

## 7. 키워드 매핑 테이블

`extractors.py`에서 사용하는 한글-코드 매핑:

```python
KEYWORD_MAPPING: dict[str, str] = {
    # 기본 키워드
    "공감": "EMPATHY",
    "직관": "INTUITION",
    "상상력": "IMAGINATION",
    "경계": "BOUNDARY",
    "리더십": "LEADERSHIP",
    "열정": "PASSION",
    "분석": "ANALYSIS",
    "안정": "STABILITY",
    "소통": "COMMUNICATION",
    "혁신": "INNOVATION",
    # 확장 키워드
    "용기": "COURAGE",
    "독립성": "INDEPENDENCE",
    "인내": "PATIENCE",
    "실용성": "PRACTICALITY",
    "호기심": "CURIOSITY",
    "적응력": "ADAPTABILITY",
    "양육": "NURTURING",
    "감수성": "SENSITIVITY",
    "창의성": "CREATIVITY",
    "자신감": "CONFIDENCE",
    "완벽주의": "PERFECTIONISM",
    "조화": "HARMONY",
    "외교": "DIPLOMACY",
    "균형": "BALANCE",
    "강렬함": "INTENSITY",
    "변화": "TRANSFORMATION",
    "모험": "ADVENTURE",
    "낙관": "OPTIMISM",
    "자유": "FREEDOM",
    "야망": "AMBITION",
    "절제": "DISCIPLINE",
    "책임감": "RESPONSIBILITY",
    "인도주의": "HUMANITARIANISM",
    "연민": "COMPASSION",
}
```

---

## 8. fortune_generator.py 통합

### 8.1 통합 지점

`FortuneGenerator._call_llm_structured()` 메서드에서 Pydantic 검증 전에 후처리 호출:

```python
# 현재 코드
content = response.text
result = response_schema.model_validate_json(content)

# 변경 후
content = response.text
parsed = json.loads(content)

# 후처리 적용
if response_schema == WesternFortuneDataV2:
    postprocessor = WesternPostprocessor()
    parsed = postprocessor.process(parsed)
elif response_schema == SajuDataV2:
    postprocessor = EasternPostprocessor()
    parsed = postprocessor.process(parsed)

result = response_schema.model_validate(parsed)
```

### 8.2 Feature Flag

환경변수로 후처리 활성화/비활성화 제어:

```python
# config.py
class Settings(BaseSettings):
    enable_postprocessor: bool = Field(
        default=True,
        description="LLM 응답 후처리 활성화 여부",
    )
```

### 8.3 로깅/모니터링

```python
logger.info(
    "postprocessor_applied",
    type="western",  # 또는 "eastern"
    steps_applied=["json_extract", "fill_keywords", "normalize_codes"],
    latency_ms=15.2,
    fields_filled=3,
)
```

---

## 9. 에러 처리 전략

### 9.1 Fail-Safe 원칙

1. **단계별 독립 실행**: 한 단계 실패 시 다음 단계 계속 진행
2. **원본 보존**: 치명적 실패 시 원본 데이터 반환
3. **상세 로깅**: 실패 원인 및 위치 기록

### 9.2 에러 분류

```python
class PostprocessErrorType(Enum):
    """후처리 에러 타입"""

    JSON_PARSE = "json_parse"           # JSON 파싱 실패
    STRUCTURE_CONVERT = "structure"     # 구조 변환 실패
    FIELD_FILL = "field_fill"           # 필드 채우기 실패
    CODE_NORMALIZE = "code_normalize"   # 코드 정규화 실패
    KEYWORD_EXTRACT = "keyword_extract" # 키워드 추출 실패
```

---

## 10. 테스트 전략

### 10.1 단위 테스트

```
tests/postprocessor/
├── test_western.py      # WesternPostprocessor 테스트
├── test_eastern.py      # EasternPostprocessor 테스트
├── test_extractors.py   # 키워드 추출기 테스트
└── test_pipeline.py     # 파이프라인 테스트
```

### 10.2 테스트 케이스 예시

```python
def test_western_fill_keywords_from_summary():
    """keywords_summary에서 keywords 추출 테스트"""
    raw = {
        "stats": {
            "keywords_summary": "리더십과 열정이 핵심 키워드입니다.",
            "keywords": [],  # 빈 배열
        }
    }

    postprocessor = WesternPostprocessor()
    result = postprocessor.process(raw)

    assert len(result["stats"]["keywords"]) >= 2
    assert result["stats"]["keywords"][0]["code"] == "LEADERSHIP"
```

---

## 11. 참조 문서

| 문서 | 경로 | 설명 |
|------|------|------|
| PRD | `docs/prd/llm-response-postprocessor.md` | 기능 요구사항 |
| 도메인 코드 | `models/enums/domain_codes.py` | 코드 상수 정의 |
| 사용자 운세 스키마 | `models/user_fortune.py` | Pydantic 모델 |
| 운세 생성기 | `services/fortune_generator.py` | 통합 대상 |

---

## 변경 이력

| 버전 | 날짜 | 변경 내용 | 작성자 |
|------|------|----------|--------|
| 1.0.0 | 2026-01-30 | 초기 설계 | YEJI AI팀 |
