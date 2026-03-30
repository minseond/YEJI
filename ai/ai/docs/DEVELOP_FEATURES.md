# ai/develop 브랜치 기능 문서

> **문서 버전**: 1.0.0
> **작성일**: 2026-01-30
> **기준 브랜치**: `ai/develop`
> **비교 대상**: `ai/main`
> **담당팀**: SSAFY YEJI AI팀

---

## 목차

1. [개요](#1-개요)
2. [후처리 시스템 (Postprocessor)](#2-후처리-시스템-postprocessor)
3. [모니터링 시스템](#3-모니터링-시스템)
4. [티키타카 V2 시스템](#4-티키타카-v2-시스템)
5. [메트릭스 API](#5-메트릭스-api)
6. [인텐트 필터 시스템](#6-인텐트-필터-시스템)
7. [설계 문서](#7-설계-문서)
8. [테스트 코드](#8-테스트-코드)
9. [기능별 상태 요약](#9-기능별-상태-요약)

---

## 1. 개요

### 1.1 목적

이 문서는 `ai/develop` 브랜치에만 존재하는 기능들을 정리하여, `ai/main`으로 머지 전 검토 및 테스트를 용이하게 합니다.

### 1.2 변경 통계

```bash
git diff --stat ai/main..ai/develop -- ai/
# 61개 파일 변경, +33,480줄 추가, -133줄 삭제
```

### 1.3 주요 변경 영역

| 영역 | 파일 수 | 상태 |
|------|---------|------|
| 후처리 시스템 (postprocessor/) | 5개 | 구현 완료 |
| 모니터링 시스템 | 3개 | 구현 완료 |
| 티키타카 V2 API | 1개 | 구현 완료 |
| 메트릭스 API | 2개 | 구현 완료 |
| 설계 문서 (docs/design/) | 10개 | 작성 완료 |
| PRD 문서 (docs/prd/) | 4개 | 작성 완료 |
| 가이드 문서 (docs/guides/) | 4개 | 작성 완료 |
| 테스트 코드 | 7개 | 작성 완료 |
| 테스트 데이터셋 | 4개 | 작성 완료 |

---

## 2. 후처리 시스템 (Postprocessor)

### 2.1 개요

LLM이 생성한 불완전한 JSON 응답을 Pydantic 검증 전에 정규화하는 시스템입니다.

### 2.2 파일 구조

```
ai/src/yeji_ai/services/postprocessor/
├── __init__.py          # 모듈 Export
├── base.py              # Protocol 및 타입 정의
├── eastern.py           # 동양 사주 후처리기
├── western.py           # 서양 점성술 후처리기
└── extractors.py        # 키워드 추출 및 유틸리티
```

### 2.3 주요 기능

| 기능 | 설명 | 담당 모듈 |
|------|------|-----------|
| FR-001: 키워드 추출 | `keywords_summary`에서 `keywords` 배열 생성 | `extractors.py` |
| FR-002: 필수 필드 채우기 | 누락된 필수 필드에 기본값 할당 | `eastern.py`, `western.py` |
| FR-003: 구조 변환 | 객체를 배열로, 배열을 객체로 변환 | `eastern.py`, `western.py` |
| FR-004: 코드 정규화 | 대소문자 통일, 유사어 매핑 (예: `"wood"` → `"WOOD"`) | `eastern.py`, `western.py` |

### 2.4 사용 예시

```python
from yeji_ai.services.postprocessor import (
    WesternPostprocessor,
    EasternPostprocessor,
)

# 서양 점성술 후처리
western_pp = WesternPostprocessor()
normalized = western_pp.process(raw_llm_response)

# 동양 사주 후처리
eastern_pp = EasternPostprocessor()
normalized = eastern_pp.process(raw_llm_response)
```

### 2.5 의존성

- `yeji_ai.models.enums.eastern` (천간지지, 오행, 십신 코드)
- `yeji_ai.models.enums.western` (별자리, 원소, 양태 코드)

### 2.6 상태

**구현 완료** - 테스트 코드 포함 (`tests/test_postprocessor.py`, 1155줄)

---

## 3. 모니터링 시스템

### 3.1 개요

LLM 응답 검증 결과를 실시간으로 모니터링하고 로깅하는 시스템입니다.

### 3.2 파일 구조

```
ai/src/yeji_ai/services/
├── validation_monitor.py   # 검증 실패율 모니터링 (564줄)
└── response_logger.py      # LLM 응답 JSONL 로깅 (609줄)

ai/src/yeji_ai/models/
├── metrics.py              # 메트릭 모델 정의 (172줄)
└── logging.py              # 로깅 모델 정의 (95줄)
```

### 3.3 ValidationMonitor

**기능:**
- 싱글톤 패턴으로 전역 인스턴스 관리
- 성공/실패 카운터 (스레드 안전)
- 에러 타입별 집계 (`VALIDATION`, `JSON_PARSE`, `CONNECTION`, `TIMEOUT`, `UNKNOWN`)
- 운세 타입별 집계 (`eastern`, `western`, `full`)
- 시간대별 집계 (최근 24시간)
- 알림 레벨 자동 판단 (`normal`, `warning`, `error`)
- Prometheus 형식 메트릭 출력

**임계값:**
| 레벨 | 실패율 | 동작 |
|------|--------|------|
| normal | < 10% | 정상 운영 |
| warning | >= 10% | 경고 로깅 |
| error | >= 30% | 심각 경고 로깅 |

**사용 예시:**

```python
from yeji_ai.services.validation_monitor import get_validation_monitor

monitor = get_validation_monitor()
await monitor.start()

# 성공 기록
monitor.record_success("eastern")

# 실패 기록
monitor.record_failure("western", ErrorType.VALIDATION, "필드 누락")

# 메트릭 조회
metrics = monitor.get_metrics()
print(f"실패율: {metrics.failure_rate}%")
```

### 3.4 ResponseLogger

**기능:**
- 비동기 큐 기반 로깅 (성능 영향 최소화)
- JSONL 형식 파일 저장
- 일별 로그 로테이션 (`logs/llm_responses/2026-01-30.jsonl`)
- 성공/검증 에러/JSON 파싱 에러/연결 에러/타임아웃 에러 분류

**로그 스키마 (LLMResponseLog):**

```python
{
    "request_id": "uuid",
    "timestamp": "ISO8601",
    "fortune_type": "eastern|western|full",
    "request_input": { ... },
    "raw_response": "LLM 원본 응답",
    "parsed_response": { ... },
    "validation": {
        "status": "success|validation_error|json_parse_error|...",
        "error_type": "ValidationError",
        "error_message": "..."
    },
    "latency_ms": 1500,
    "attempt_number": 1,
    "model_name": "yeji-8b-rslora-v7-AWQ"
}
```

### 3.5 의존성

- `structlog` (구조화 로깅)
- `asyncio` (비동기 처리)

### 3.6 상태

**구현 완료** - 테스트 코드 포함
- `tests/test_validation_monitor.py` (372줄)
- `tests/test_response_logger.py` (390줄)

---

## 4. 티키타카 V2 시스템

### 4.1 개요

SSE(Server-Sent Events) 기반 실시간 버블 스트리밍 API입니다.

### 4.2 파일 위치

```
ai/src/yeji_ai/api/v1/fortune/tikitaka.py  (829줄)
```

### 4.3 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/api/v1/fortune/tikitaka/stream` | SSE 스트리밍 |
| GET | `/api/v1/fortune/tikitaka/session/{session_id}` | 세션 상태 조회 |

### 4.4 SSE 이벤트 타입

| 이벤트 | 설명 |
|--------|------|
| `session` | 세션 정보 전송 |
| `phase_change` | 대화 단계 변경 (GREETING → DIALOGUE → SUMMARY) |
| `bubble_start` | 버블 시작 (character, emotion, type) |
| `bubble_chunk` | 버블 청크 (content 조각) |
| `bubble_end` | 버블 완료 (전체 content, timestamp) |
| `turn_update` | 턴 업데이트 (remaining_turns) |
| `debate_status` | 토론 상태 (합의/불합의) |
| `ui_hint` | UI 힌트 (선택 UI 표시 등) |
| `pause` | 대기 (사용자 입력 필요) |
| `complete` | 스트리밍 완료 |
| `error` | 오류 발생 |

### 4.5 버블 스트리밍 시퀀스

```
bubble_start → bubble_chunk* → bubble_end
```

### 4.6 감정 코드 (10종)

```python
class EmotionCode(str, Enum):
    NEUTRAL = "NEUTRAL"       # 중립
    HAPPY = "HAPPY"           # 행복
    CURIOUS = "CURIOUS"       # 호기심
    THOUGHTFUL = "THOUGHTFUL" # 사려깊음
    SURPRISED = "SURPRISED"   # 놀람
    CONCERNED = "CONCERNED"   # 걱정
    CONFIDENT = "CONFIDENT"   # 자신감
    PLAYFUL = "PLAYFUL"       # 장난스러움
    MYSTERIOUS = "MYSTERIOUS" # 신비로움
    EMPATHETIC = "EMPATHETIC" # 공감
```

### 4.7 BubbleParser

XML 태그 기반 버블 파싱 및 폴백 로직:

```xml
<bubble character="SOISEOL" emotion="HAPPY" type="GREETING">
  안녕하세요~ 반가워요!
</bubble>
```

폴백: `[소이설]`, `[스텔라]` 접두사 기반 파싱

### 4.8 의존성

- `yeji_ai.services.tikitaka_service.TikitakaService`
- 동양/서양 분석 결과 (Eastern/Western Fortune)

### 4.9 상태

**구현 완료** - 프론트엔드 연동 가이드 포함

---

## 5. 메트릭스 API

### 5.1 파일 위치

```
ai/src/yeji_ai/api/metrics.py  (176줄)
```

### 5.2 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/api/metrics` | JSON 형식 메트릭 |
| GET | `/api/metrics/prometheus` | Prometheus 형식 메트릭 |
| POST | `/api/metrics/reset` | 메트릭 초기화 (개발용) |
| GET | `/api/metrics/health` | 모니터링 상태 확인 |

### 5.3 JSON 응답 예시

```json
{
  "total_requests": 1000,
  "success_count": 950,
  "failure_count": 50,
  "failure_rate": 5.0,
  "success_rate": 95.0,
  "error_type_counts": [
    {"error_type": "validation", "count": 30, "percentage": 60.0},
    {"error_type": "json_parse", "count": 15, "percentage": 30.0}
  ],
  "fortune_type_metrics": [
    {"fortune_type": "eastern", "total_requests": 500, "failure_rate": 4.0}
  ],
  "hourly_metrics": [...],
  "alert_level": "normal"
}
```

### 5.4 Prometheus 형식 예시

```
# HELP yeji_validation_total 검증 요청 총 수
# TYPE yeji_validation_total counter
yeji_validation_total 1000
# HELP yeji_validation_failure_rate 현재 검증 실패율 (%)
# TYPE yeji_validation_failure_rate gauge
yeji_validation_failure_rate 5.0
```

### 5.5 상태

**구현 완료** - 테스트 코드 포함 (`tests/test_metrics_api.py`, 264줄)

---

## 6. 인텐트 필터 시스템

### 6.1 개요

사용자 입력 의도를 분류하고 악성 프롬프트를 필터링하는 시스템입니다.

### 6.2 테스트 데이터셋

```
ai/tests/data/intent/
├── fortune.yaml         # 운세 관련 (100개 샘플)
├── conversation.yaml    # 일반 대화 (샘플)
├── malicious.yaml       # 악성 프롬프트 (40개 샘플)
└── out_of_domain.yaml   # 도메인 외 요청 (샘플)
```

### 6.3 운세 카테고리 (`fortune.yaml`)

| 카테고리 | 개수 | 설명 |
|----------|------|------|
| fortune_general | 15 | 일반 운세 |
| fortune_love | 15 | 연애/결혼운 |
| fortune_career | 15 | 직장/취업운 |
| fortune_money | 15 | 금전/재물운 |
| fortune_health | 15 | 건강운 |
| fortune_academic | 15 | 학업/시험운 |
| fortune_interpersonal | 10 | 대인관계운 |

### 6.4 악성 프롬프트 카테고리 (`malicious.yaml`)

| 카테고리 | 개수 | 설명 |
|----------|------|------|
| injection | 15 | 프롬프트 인젝션 |
| jailbreak | 15 | 탈옥 시도 |
| indirect_attack | 10 | 간접 공격 |

### 6.5 상태

**설계 완료** - 구현 예정
- 설계 문서: `docs/design/intent-filter-api.md`
- 구현 계획: `docs/plan/intent-filter-implementation-plan.md`

---

## 7. 설계 문서

### 7.1 PRD 문서 (`docs/prd/`)

| 파일 | 설명 | 줄 수 |
|------|------|-------|
| `llm-response-postprocessor.md` | 후처리 시스템 PRD | 447 |
| `tikitaka-schema-v2.md` | 티키타카 스키마 V2 | 1,235 |
| `json-accuracy-improvement.md` | JSON 정확도 개선 | 634 |
| `prompt-optimization-system.md` | 프롬프트 최적화 | 943 |

### 7.2 설계 문서 (`docs/design/`)

| 파일 | 설명 | 줄 수 |
|------|------|-------|
| `tikitaka-session-lifecycle.md` | 세션 라이프사이클 | 1,168 |
| `tikitaka-bubble-parser.md` | 버블 파서 설계 | 790 |
| `tikitaka-summary-schema.md` | 요약 스키마 | 1,150 |
| `intent-filter-api.md` | 인텐트 필터 API | 1,344 |
| `intent-prompting-poc.md` | 인텐트 프롬프팅 PoC | 1,034 |
| `l4-intent-deployment.md` | L4 인텐트 배포 | 1,549 |
| `llm-fallback-chain.md` | LLM 폴백 체인 | 764 |
| `gpt-fallback-prompts.md` | GPT 폴백 프롬프트 | 1,021 |
| `g-eval-system.md` | G-Eval 평가 시스템 | 1,293 |
| `prompt-version-control.md` | 프롬프트 버전 관리 | 1,804 |

### 7.3 가이드 문서 (`docs/guides/`)

| 파일 | 설명 | 줄 수 |
|------|------|-------|
| `qwen3-prompting-guide.md` | Qwen3 프롬프팅 가이드 | 704 |
| `tikitaka-emotion-guide.md` | 티키타카 감정 가이드 | 1,269 |
| `tikitaka-frontend-integration.md` | 프론트엔드 연동 가이드 | 2,185 |
| `intent-category-labeling-guide.md` | 인텐트 라벨링 가이드 | 1,073 |

### 7.4 분석 문서 (`docs/analysis/`, `docs/architecture/`)

| 파일 | 설명 |
|------|------|
| `json-accuracy-strategy-analysis.md` | JSON 정확도 전략 분석 |
| `postprocessor.md` | 후처리기 아키텍처 |

---

## 8. 테스트 코드

### 8.1 신규 테스트 파일

| 파일 | 줄 수 | 설명 |
|------|-------|------|
| `test_postprocessor.py` | 1,155 | 후처리기 테스트 |
| `test_validation_monitor.py` | 372 | 검증 모니터 테스트 |
| `test_response_logger.py` | 390 | 응답 로거 테스트 |
| `test_metrics_api.py` | 264 | 메트릭스 API 테스트 |
| `test_fortune_generator.py` | 1,158 | 운세 생성기 테스트 |
| `test_fortune_errors.py` | 312 | 운세 에러 처리 테스트 |

### 8.2 테스트 실행 방법

```bash
# 전체 테스트
pytest C:/Users/SSAFY/yeji-ai-server/ai/tests/ -v

# 특정 테스트 파일
pytest C:/Users/SSAFY/yeji-ai-server/ai/tests/test_postprocessor.py -v

# 커버리지 포함
pytest --cov=yeji_ai --cov-report=html
```

---

## 9. 기능별 상태 요약

| 기능 | 구현 | 테스트 | 문서 | 상태 |
|------|------|--------|------|------|
| 후처리 시스템 | O | O | O | **머지 준비 완료** |
| ValidationMonitor | O | O | O | **머지 준비 완료** |
| ResponseLogger | O | O | O | **머지 준비 완료** |
| 메트릭스 API | O | O | O | **머지 준비 완료** |
| 티키타카 V2 SSE | O | - | O | **테스트 추가 필요** |
| 인텐트 필터 | - | - | O | **구현 예정** |
| G-Eval 시스템 | - | - | O | **설계 완료** |
| LLM 폴백 체인 | - | - | O | **설계 완료** |
| 프롬프트 버전 관리 | - | - | O | **설계 완료** |

### 9.1 머지 우선순위

1. **P1 (즉시 머지)**: 후처리 시스템, 모니터링 시스템, 메트릭스 API
2. **P2 (테스트 후 머지)**: 티키타카 V2 SSE
3. **P3 (구현 필요)**: 인텐트 필터 시스템
4. **P4 (장기 계획)**: G-Eval, LLM 폴백 체인, 프롬프트 버전 관리

---

## 변경 이력

| 버전 | 날짜 | 작성자 | 설명 |
|------|------|--------|------|
| 1.0.0 | 2026-01-30 | YEJI AI Team | 최초 작성 |
