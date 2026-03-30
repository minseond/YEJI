# YEJI AI 서버 전체 작업 통합 문서

> **문서 버전**: 1.0.0
> **작성일**: 2026-01-30
> **작성자**: YEJI AI Team (Claude Code Agent)
> **상태**: 완료

---

## 목차

1. [개요 및 타임라인](#1-개요-및-타임라인)
2. [ai/develop 기능 목록](#2-aidevelop-기능-목록)
3. [ai/main 핫픽스 목록](#3-aimain-핫픽스-목록)
4. [피쳐 구현 목록](#4-피쳐-구현-목록)
5. [테스트 현황](#5-테스트-현황)
6. [머지 전략 및 권장사항](#6-머지-전략-및-권장사항)
7. [다음 단계](#7-다음-단계)

---

## 1. 개요 및 타임라인

### 1.1 프로젝트 현황 요약

| 영역 | 상태 | 주요 내용 |
|------|------|----------|
| **ai/develop** | 개발 완료 | 후처리 시스템, 모니터링, 티키타카 V2 |
| **ai/main 핫픽스** | 적용 완료 | 6건의 Pydantic 모델 버그 수정 |
| **피쳐 개발** | 설계 완료 | GPU 필터 파이프라인, L4 배포 아키텍처 |

### 1.2 타임라인

```
2026-01-30
├── 오전: 핫픽스 #1-#3 적용 (Pillar 모델 필드 누락)
├── 오후: 핫픽스 #4-#6 적용 (속성 호환성)
├── 저녁: 인프라 개선 (Jenkinsfile, Docker)
└── 야간: 테스트 정상화 (128개 전체 통과)
```

### 1.3 핵심 성과

| 지표 | 이전 | 이후 | 개선율 |
|------|------|------|--------|
| 테스트 통과율 | 72% (77/107) | **100%** (128/128) | +28% |
| 프로덕션 장애 | 503 에러 발생 | 해결 | - |
| 스키마 호환성 | 불일치 6건 | 해결 | - |

---

## 2. ai/develop 기능 목록

### 2.1 후처리 시스템 (postprocessor/)

LLM 응답을 Pydantic 검증 전에 정규화하여 검증 실패율을 낮추는 시스템입니다.

#### 2.1.1 모듈 구조

```
services/postprocessor/
├── __init__.py         # 모듈 초기화
├── base.py             # Protocol 및 타입 정의
├── eastern.py          # 동양 사주 후처리기
├── western.py          # 서양 점성술 후처리기
└── extractors.py       # 키워드 추출 유틸리티
```

#### 2.1.2 핵심 기능

| 기능 | 설명 | 파일 |
|------|------|------|
| **FR-001** | keywords_summary에서 keywords 배열 추출 | `western.py` |
| **FR-002** | 필수 필드 기본값 채우기 | `eastern.py`, `western.py` |
| **FR-003** | 구조 변환 (객체 → 배열) | `eastern.py`, `western.py` |
| **FR-004** | 코드 정규화 (대소문자, 유사어 매핑) | `eastern.py`, `western.py` |

#### 2.1.3 EasternPostprocessor 주요 로직

```python
class EasternPostprocessor:
    def process(self, raw: dict[str, Any]) -> dict[str, Any]:
        # 단계 1: 구조 변환 (오행/십신 객체 -> 배열)
        data = self._convert_structures(data)
        # 단계 2: 코드 정규화 (WOOD, FIRE 등)
        data = self._normalize_codes(data)
        # 단계 3: 사주 기둥 정규화
        data = self._normalize_pillars(data)
        # 단계 4: 천간지지 동기화
        data = self._sync_cheongan_jiji(data)
        # 단계 5: 기본값 채우기
        data = self._fill_defaults(data)
        return data
```

#### 2.1.4 WesternPostprocessor 주요 로직

```python
class WesternPostprocessor:
    def process(self, raw: dict[str, Any]) -> dict[str, Any]:
        # 단계 1: 구조 변환 (4원소, 3양태 분포)
        data = self._convert_structures(data)
        # 단계 2: 코드 정규화 (별자리, 원소, 양태)
        data = self._normalize_codes(data)
        # 단계 3: keywords 추출
        data = self._fill_keywords(data)
        # 단계 4: 기본값 채우기
        data = self._fill_defaults(data)
        return data
```

#### 2.1.5 코드 정규화 테이블

**오행 코드 (Eastern)**:
| 입력 | 출력 |
|------|------|
| `wood`, `Wood`, `목` | `WOOD` |
| `fire`, `Fire`, `화` | `FIRE` |
| `earth`, `Earth`, `토` | `EARTH` |
| `metal`, `Metal`, `금` | `METAL` |
| `water`, `Water`, `수` | `WATER` |

**별자리 코드 (Western)**:
| 입력 | 출력 |
|------|------|
| `aquarius`, `물병자리`, `물병` | `AQUARIUS` |
| `aries`, `양자리`, `양` | `ARIES` |
| ... | ... |

---

### 2.2 모니터링 시스템

#### 2.2.1 ValidationMonitor (`validation_monitor.py`)

LLM 응답 검증 실패율을 실시간으로 추적하는 싱글톤 서비스입니다.

**주요 기능**:

| 기능 | 설명 |
|------|------|
| 성공/실패 기록 | `record_success()`, `record_failure()` |
| 실패율 계산 | 실시간 실패율 (%) |
| 에러 타입별 집계 | JSON_PARSE, VALIDATION, TIMEOUT 등 |
| 운세 타입별 집계 | eastern, western, full |
| 시간대별 집계 | 최근 24시간 hourly 집계 |
| 알림 레벨 | normal (< 10%), warning (10-30%), error (> 30%) |

**사용 예시**:

```python
from yeji_ai.services.validation_monitor import get_validation_monitor

monitor = get_validation_monitor()
monitor.record_success("eastern")
monitor.record_failure("western", ErrorType.VALIDATION)
metrics = monitor.get_metrics()
```

#### 2.2.2 ResponseLogger (`response_logger.py`)

LLM 응답을 JSONL 파일로 저장하여 평가/최적화에 활용합니다.

**주요 기능**:

| 기능 | 설명 |
|------|------|
| 비동기 로깅 | 메인 요청 처리에 영향 없음 |
| 일별 로테이션 | `YYYY-MM-DD.jsonl` 형식 |
| 에러 타입별 로깅 | success, validation_error, json_parse_error, timeout 등 |

**로그 스키마**:

```python
class LLMResponseLog(BaseModel):
    request_id: str
    fortune_type: Literal["eastern", "western", "full"]
    request_input: RequestInput
    raw_response: str | None
    parsed_response: dict | None
    validation: ValidationResult
    latency_ms: int
    attempt_number: int
    model_name: str | None
    token_usage: TokenUsage | None
```

---

### 2.3 티키타카 기능 (tikitaka.py, SSE 스트리밍)

#### 2.3.1 V2 스키마 개요

기존 V1의 한계를 극복하기 위한 새로운 티키타카 스키마입니다.

| 항목 | V1 | V2 |
|------|-----|-----|
| 메시지 컨테이너 | `messages[]` | `bubbles[]` |
| 감정 | 없음 | `emotion: EmotionCode` (10종) |
| 대화 연결 | 없음 | `reply_to: string` |
| 세션 상태 | 분산 | `session_state` 객체 |
| 대화 단계 | 없음 | `phase: PhaseCode` |

#### 2.3.2 EmotionCode (10종)

| 코드 | 한글명 | 소이설 예시 | 스텔라 예시 |
|------|--------|------------|------------|
| `NEUTRAL` | 중립 | 일반 설명 | 분석 결과 |
| `HAPPY` | 기쁨 | "좋은 기운이에요~" | "흥미로운 배치야" |
| `CURIOUS` | 호기심 | "어머, 이건...!" | "...이건 특이해" |
| `THOUGHTFUL` | 사려깊음 | "음... 살펴보면요" | "잠깐, 확인해볼게" |
| `SURPRISED` | 놀람 | "어머!" | "...!" |
| `CONCERNED` | 걱정 | "조심하셔야 해요" | "이 부분은 신경 써" |
| `CONFIDENT` | 확신 | "분명해요!" | "확실해" |
| `PLAYFUL` | 장난스러움 | "후훗~" | "ㅋ" |
| `MYSTERIOUS` | 신비로움 | "운명이란 게..." | "별은 말하고 있어..." |
| `EMPATHETIC` | 공감 | "그럴 수 있어요" | "이해해" |

#### 2.3.3 SSE 이벤트 타입

```python
class SSEEventType(str, Enum):
    SESSION = "session"           # 세션 정보
    PHASE_CHANGE = "phase_change" # 단계 변경
    BUBBLE_START = "bubble_start" # 버블 시작
    BUBBLE_CHUNK = "bubble_chunk" # 버블 청크 (스트리밍)
    BUBBLE_END = "bubble_end"     # 버블 완료
    TURN_UPDATE = "turn_update"   # 턴 업데이트
    DEBATE_STATUS = "debate_status" # 토론 상태
    UI_HINT = "ui_hint"           # UI 힌트
    PAUSE = "pause"               # 일시정지
    COMPLETE = "complete"         # 완료
    ERROR = "error"               # 에러
```

#### 2.3.4 버블 스트리밍 시퀀스

```
bubble_start → bubble_chunk* → bubble_end
```

**SSE 예시**:

```
event: bubble_start
data: {"bubble_id": "b_001", "character": "SOISEOL", "emotion": "HAPPY", "type": "GREETING"}

event: bubble_chunk
data: {"bubble_id": "b_001", "content": "안녕하세요~"}

event: bubble_chunk
data: {"bubble_id": "b_001", "content": " 반가워요!"}

event: bubble_end
data: {"bubble_id": "b_001", "content": "안녕하세요~ 반가워요!", "timestamp": "2026-01-30T15:30:00Z"}
```

#### 2.3.5 BubbleParser (XML 태그 기반)

```python
class BubbleParser:
    BUBBLE_PATTERN = re.compile(
        r"<bubble\s+"
        r'character="(?P<character>\w+)"\s+'
        r'emotion="(?P<emotion>\w+)"\s+'
        r'type="(?P<type>\w+)"'
        r'(?:\s+reply_to="(?P<reply_to>[\w-]+)")?'
        r"\s*>"
        r"(?P<content>[\s\S]*?)"
        r"</bubble>",
        re.DOTALL,
    )
```

---

### 2.4 메트릭스 API (`metrics.py`)

Prometheus 형식과 JSON 형식의 메트릭을 제공합니다.

#### 2.4.1 엔드포인트

| 엔드포인트 | 설명 |
|-----------|------|
| `GET /metrics` | JSON 형식 메트릭 |
| `GET /metrics/prometheus` | Prometheus text format |
| `POST /metrics/reset` | 메트릭 초기화 (개발용) |
| `GET /metrics/health` | 모니터링 상태 확인 |

#### 2.4.2 Prometheus 메트릭

```
# HELP yeji_validation_total 검증 요청 총 수
# TYPE yeji_validation_total counter
yeji_validation_total 1000

# HELP yeji_validation_failure_rate 현재 검증 실패율 (%)
# TYPE yeji_validation_failure_rate gauge
yeji_validation_failure_rate 5.0

# HELP yeji_validation_failure_by_type 에러 타입별 검증 실패 수
# TYPE yeji_validation_failure_by_type counter
yeji_validation_failure_by_type{error_type="validation"} 30
yeji_validation_failure_by_type{error_type="json_parse"} 15
```

---

### 2.5 설계 문서 목록

#### 2.5.1 PRD 문서 (`docs/prd/`)

| 문서 | 설명 |
|------|------|
| `llm-response-postprocessor.md` | 후처리 시스템 PRD (FR-001~005) |
| `tikitaka-schema-v2.md` | 티키타카 V2 스키마 설계 |
| `json-accuracy-improvement.md` | JSON 정확도 개선 전략 |
| `prompt-optimization-system.md` | 프롬프트 최적화 시스템 |

#### 2.5.2 설계 문서 (`docs/design/`)

| 문서 | 설명 |
|------|------|
| `intent-filter-api.md` | 인텐트 필터 API 설계 |
| `l4-intent-deployment.md` | L4 GPU 배포 아키텍처 |
| `tikitaka-bubble-parser.md` | 버블 파서 설계 |
| `tikitaka-session-lifecycle.md` | 세션 생명주기 |
| `llm-fallback-chain.md` | LLM 폴백 체인 |

#### 2.5.3 가이드 문서 (`docs/guides/`)

| 문서 | 설명 |
|------|------|
| `qwen3-prompting-guide.md` | Qwen3 프롬프트 작성법 |
| `tikitaka-emotion-guide.md` | 감정 코드 가이드 |
| `tikitaka-frontend-integration.md` | 프론트엔드 연동 가이드 |
| `intent-category-labeling-guide.md` | 인텐트 라벨링 가이드 |

---

## 3. ai/main 핫픽스 목록

### 3.1 핫픽스 개요

프로덕션 `/api/v1/fortune/chat/stream` 엔드포인트에서 발생한 연쇄 AttributeError를 해결했습니다.

| 핫픽스 | 에러 | 원인 | 상태 |
|--------|------|------|------|
| #1 | `'Pillar' object has no attribute 'gan_code'` | 필드 누락 | 해결 |
| #2 | `'str' object has no attribute 'label_ko'` | 타입 불일치 | 해결 |
| #3 | `'FiveElements' object has no attribute 'get'` | dict 호환성 | 해결 |
| #4 | `'EasternStats' object has no attribute 'weakness'` | 속성 누락 | 해결 |
| #5 | `'YinYangRatio' object has no attribute 'balance'` | 속성 누락 | 해결 |
| #6 | `'TenGods' object has no attribute 'get'` | dict 호환성 | 해결 |

---

### 3.2 Hotfix #1: Pillar gan_code/ji_code/ten_god_code

**브랜치**: `ai/hotfix/pillar-gan-code`
**우선순위**: P0 (프로덕션 장애)

**문제**:
```python
# llm_interpreter.py:581
chart.year.gan_code.hangul  # AttributeError: 'Pillar' object has no attribute 'gan_code'
```

**수정 (`user_fortune.py`)**:
```python
class Pillar(BaseModel):
    gan: str = Field(..., description="천간 한자")
    ji: str = Field(..., description="지지 한자")
    gan_code: CheonGanCode = Field(..., description="천간 코드")  # 추가
    ji_code: JiJiCode = Field(..., description="지지 코드")       # 추가
    ten_god_code: TenGodCode = Field(..., description="십신 코드") # 추가
    element_code: ElementCode = Field(..., description="오행 코드")
```

---

### 3.3 Hotfix #2: element_code 타입 변경

**브랜치**: `ai/hotfix/pillar-element-code`
**우선순위**: P0 (프로덕션 장애)

**문제**:
```python
# element_code가 문자열인데 Enum으로 접근 시도
pillar.element_code.label_ko  # AttributeError: 'str' object has no attribute 'label_ko'
```

**수정**:

1. `user_fortune.py`:
```python
element_code: ElementCode = Field(..., description="오행 코드")  # str → ElementCode
```

2. `eastern_fortune_service.py`:
```python
element_code=element,  # element.value → element (Enum 객체 직접 전달)
```

---

### 3.4 Hotfix #3: FiveElements.get() 메서드

**브랜치**: `ai/hotfix/five-elements-get`
**우선순위**: P1 (핵심 기능 버그)

**문제**:
```python
# tikitaka_service.py:251
stats.five_elements.get('dominant')  # AttributeError: 'FiveElements' object has no attribute 'get'
```

**수정 (`user_fortune.py`)**:
```python
class FiveElements(BaseModel):
    summary: str
    elements_list: list[FiveElementItem]

    @property
    def dominant(self) -> str:
        """우세 오행 레이블 반환"""
        if not self.elements_list:
            return ""
        max_elem = max(self.elements_list, key=lambda x: x.percent)
        return max_elem.label

    @property
    def weak(self) -> str:
        """약한 오행 레이블 반환"""
        if not self.elements_list:
            return ""
        min_elem = min(self.elements_list, key=lambda x: x.percent)
        return min_elem.label

    def get(self, key: str, default: str = "") -> str:
        """dict 호환용 get 메서드"""
        if key == "dominant":
            return self.dominant or default
        elif key == "weak":
            return self.weak or default
        elif key == "summary":
            return self.summary or default
        return default
```

---

### 3.5 Hotfix #4: EasternStats.weakness

**우선순위**: P1 (핵심 기능 버그)

**문제**:
```python
stats.weakness  # AttributeError: 'EasternStats' object has no attribute 'weakness'
```

**수정 (`user_fortune.py`)**:
```python
class EasternStats(BaseModel):
    five_elements: FiveElements
    yin_yang: YinYangRatio
    ten_gods: TenGods
    strength: str

    @property
    def weakness(self) -> str:
        """약한 오행 정보 (five_elements.weak의 별칭)"""
        return self.five_elements.weak
```

---

### 3.6 Hotfix #5: YinYangRatio.balance

**우선순위**: P1 (핵심 기능 버그)

**문제**:
```python
stats.yin_yang.balance  # AttributeError: 'YinYangRatio' object has no attribute 'balance'
```

**수정 (`user_fortune.py`)**:
```python
class YinYangRatio(BaseModel):
    summary: str
    yin: int
    yang: int

    @property
    def balance(self) -> YinYangBalance:
        """음양 균형 상태 계산"""
        return YinYangBalance.from_ratio(self.yang)
```

---

### 3.7 Hotfix #6: TenGods.dominant/get()

**우선순위**: P1 (핵심 기능 버그)

**문제**:
```python
stats.ten_gods.get('dominant')  # AttributeError: 'TenGods' object has no attribute 'get'
```

**수정 (`user_fortune.py`)**:
```python
class TenGods(BaseModel):
    summary: str
    gods_list: list[TenGodItem]

    @property
    def dominant(self) -> str:
        """우세 십신 코드 반환"""
        if not self.gods_list:
            return ""
        max_god = max(self.gods_list, key=lambda x: x.percent)
        return max_god.code

    def get(self, key: str, default: str = "") -> str:
        """dict 호환용 get 메서드"""
        if key == "dominant":
            return self.dominant or default
        elif key == "summary":
            return self.summary or default
        return default
```

---

## 4. 피쳐 구현 목록

### 4.1 GPU 필터 파이프라인 (Guard + Intent)

#### 4.1.1 아키텍처 개요

```
Request Flow:
POST /api/v1/fortune/chat
       │
       ▼
┌─────────────────┐
│  FilterDepends  │◀── FastAPI Dependency Injection
└────────┬────────┘
         │
         ▼
┌─────────────────┐   악성 탐지
│  PromptGuard    │────────────▶ 400 FilterBlockedError
│  (~100ms)       │
└────────┬────────┘
         │ 정상
         ▼
┌─────────────────┐   도메인 외
│ IntentClassifier│────────────▶ 200 + 안내 메시지
│  (~15ms)        │
└────────┬────────┘
         │ 운세 관련
         ▼
┌─────────────────┐
│ TikitakaService │──────────▶ 200 ChatResponse
└─────────────────┘
```

#### 4.1.2 Guard 모델 스펙

| 항목 | 값 |
|------|-----|
| **모델** | `meta-llama/Llama-Prompt-Guard-2-86M` |
| **파라미터** | 86M |
| **VRAM** | ~0.35GB (FP16) |
| **레이턴시** | ~100ms |
| **기능** | 프롬프트 인젝션, 탈옥 시도 탐지 |

#### 4.1.3 Intent 분류기 스펙

| 항목 | 값 |
|------|-----|
| **모델** | `Alibaba-NLP/gte-multilingual-base` |
| **파라미터** | 305M |
| **VRAM** | ~0.6GB (FP16) |
| **레이턴시** | ~15ms |
| **기능** | 운세 의도 분류 (11개 카테고리) |

#### 4.1.4 IntentCategory (11종)

```python
class IntentCategory(str, Enum):
    # 운세 관련 (LLM 처리)
    FORTUNE_GENERAL = "fortune_general"
    FORTUNE_LOVE = "fortune_love"
    FORTUNE_CAREER = "fortune_career"
    FORTUNE_MONEY = "fortune_money"
    FORTUNE_HEALTH = "fortune_health"
    FORTUNE_ACADEMIC = "fortune_academic"
    FORTUNE_INTERPERSONAL = "fortune_interpersonal"

    # 대화 보조
    GREETING = "greeting"
    FOLLOWUP = "followup"

    # 도메인 외
    OUT_OF_DOMAIN_ALLOWED = "out_of_domain_allowed"
    OUT_OF_DOMAIN_REJECTED = "out_of_domain_rejected"
```

#### 4.1.5 FilterAction (5종)

```python
class FilterAction(str, Enum):
    PROCEED = "proceed"                # LLM 처리 진행
    BLOCK_MALICIOUS = "block_malicious"  # 악성 프롬프트 차단
    REJECT_OOD = "reject_ood"          # 도메인 외 거부
    DIRECT_RESPONSE = "direct_response"  # 직접 응답 (인사 등)
    FALLBACK = "fallback"              # 폴백 (필터 오류 시)
```

---

### 4.2 L4 인텐트 모델 배포 아키텍처

#### 4.2.1 L4 GPU 스펙

| 항목 | 사양 |
|------|------|
| GPU 모델 | NVIDIA L4 |
| VRAM | 24GB GDDR6 |
| 메모리 대역폭 | 300 GB/s |
| FP16 성능 | 121 TFLOPS |

#### 4.2.2 VRAM 예산 분석

| 컴포넌트 | 최소 | 최대 | 권장 |
|----------|------|------|------|
| yeji-8b-AWQ | 5.5GB | 5.5GB | 5.5GB |
| KV Cache | 4GB | 6GB | 5GB |
| Prompt Guard 86M | 0.35GB | 0.35GB | 0.35GB |
| Intent Classifier | 0.6GB | 0.6GB | 0.6GB |
| CUDA 오버헤드 | 1GB | 1GB | 1GB |
| **합계** | **11.45GB** | **13.45GB** | **12.45GB** |
| **여유 공간** | **12.55GB** | **10.55GB** | **11.55GB** |

#### 4.2.3 배포 옵션

| 옵션 | 장점 | 단점 | 권장도 |
|------|------|------|--------|
| **Option A: 단일 프로세스** | 메모리 효율, 레이턴시 최소화 | 단일 장애점 | **권장** |
| Option B: 멀티 프로세스 | 장애 격리 | 네트워크 오버헤드, VRAM 중복 | - |

#### 4.2.4 Docker 구성

```dockerfile
# 헬스체크 (모델 로딩 시간 고려)
HEALTHCHECK --interval=30s --timeout=30s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:8000/v1/health/ready || exit 1
```

---

### 4.3 인프라 개선

#### 4.3.1 Jenkinsfile 수정

| 항목 | 이전 | 이후 |
|------|------|------|
| vLLM URL | 하드코딩 | 환경변수 (`VLLM_BASE_URL`) |
| 컨테이너 정리 | 단일 명령 | 개별 정리 (prod/dev/legacy) |
| 환경변수 주입 | 누락 | `-e` 플래그 추가 |

#### 4.3.2 Docker 설정

| 항목 | 이전 | 이후 |
|------|------|------|
| HEALTHCHECK 경로 | `/health` | `/api/health` |
| 시작 대기 시간 | 60s | 120s (모델 로딩 고려) |

#### 4.3.3 환경변수

```bash
# 기존
VLLM_BASE_URL=http://13.125.68.166:8001
VLLM_MODEL=tellang/yeji-8b-rslora-v7-AWQ

# 신규 (인텐트 필터)
FILTER_ENABLED=true
GUARD_ENABLED=true
GUARD_MODEL=meta-llama/Llama-Prompt-Guard-2-86M
GUARD_THRESHOLD=0.8
INTENT_ENABLED=true
INTENT_MODEL=Alibaba-NLP/gte-multilingual-base
INTENT_CONFIDENCE_THRESHOLD=0.7
```

---

## 5. 테스트 현황

### 5.1 테스트 통과 현황

| 테스트 스위트 | 초기 상태 | 최종 상태 |
|--------------|-----------|-----------|
| 전체 테스트 | 77/107 (72%) | **128/128 (100%)** |
| 라우터 경로 | 실패 | **8개 통과** |
| User Fortune 스키마 | 실패 | **41개 통과** |
| 후처리기 | - | **신규 추가** |
| 검증 모니터 | - | **신규 추가** |

### 5.2 테스트 파일 목록

```
tests/
├── conftest.py                  # 공통 픽스처
├── test_providers.py            # LLM Provider 테스트
├── test_fortune_errors.py       # 에러 처리 테스트
├── test_fortune_generator.py    # 운세 생성 테스트
├── test_metrics_api.py          # 메트릭 API 테스트
├── test_postprocessor.py        # 후처리기 테스트
├── test_response_logger.py      # 응답 로거 테스트
├── test_validation_monitor.py   # 검증 모니터 테스트
├── test_health.py               # 헬스체크 테스트
├── test_saju_api.py             # 사주 API 테스트
└── test_user_fortune_schema.py  # 스키마 검증 테스트
```

### 5.3 테스트 실행 방법

```bash
# 전체 테스트
pytest C:/Users/SSAFY/yeji-ai-server/ai/tests/ -v

# 커버리지 포함
pytest C:/Users/SSAFY/yeji-ai-server/ai/tests/ -v --cov=yeji_ai --cov-report=html

# 특정 파일
pytest C:/Users/SSAFY/yeji-ai-server/ai/tests/test_postprocessor.py -v
```

---

## 6. 머지 전략 및 권장사항

### 6.1 브랜치 현황

```
ai/main (프로덕션)
├── 핫픽스 #1-#6 적용됨
└── 프로덕션 배포 중

ai/develop (개발)
├── 후처리 시스템
├── 모니터링 시스템
├── 티키타카 V2
└── 메트릭스 API

ai/feature/gpu-filter (피쳐)
└── 설계 문서 완료, 구현 대기
```

### 6.2 머지 순서 권장

```
1단계: ai/develop → ai/main
├── 후처리기 (postprocessor/)
├── 모니터링 (validation_monitor, response_logger)
└── 티키타카 V2 (tikitaka.py)

2단계: ai/feature/gpu-filter → ai/develop
├── 필터 서비스 구현
├── 모델 로더 구현
└── API 의존성 주입

3단계: ai/develop → ai/main (릴리스)
└── GPU 필터 프로덕션 적용
```

### 6.3 머지 전 체크리스트

#### ai/develop → ai/main 머지 전

- [ ] 모든 테스트 통과 확인 (`pytest tests/ -v`)
- [ ] 린트 검사 통과 (`ruff check src/`)
- [ ] 스키마 호환성 검증 (user_fortune.py vs services)
- [ ] 프로덕션 환경변수 확인

#### GPU 필터 활성화 전

- [ ] Guard 모델 다운로드 완료
- [ ] Intent 모델 다운로드 완료
- [ ] VRAM 사용량 확인 (< 14GB)
- [ ] 헬스체크 엔드포인트 테스트
- [ ] 롤백 절차 숙지

### 6.4 위험 완화 전략

| 위험 | 완화 방안 |
|------|----------|
| 스키마 불일치 | 머지 전 통합 테스트 실행 |
| GPU 메모리 부족 | 단계별 활성화 (Guard → Intent) |
| 필터 오탐 | `log_only` 모드로 시작 후 `block` 전환 |
| 서비스 중단 | Feature Flag로 즉시 비활성화 가능 |

---

## 7. 다음 단계

### 7.1 즉시 필요 (P0/P1)

| 작업 | 담당 | 예상 기간 |
|------|------|----------|
| `ai/develop` → `ai/main` 머지 | 팀 전체 | 1일 |
| E2E 테스트 (프론트 → AI → vLLM) | QA | 1일 |
| Frontend 배포 (현재 502) | 프론트 | 1일 |

### 7.2 단기 계획 (1주 내)

| 작업 | 설명 |
|------|------|
| Pydantic v2 경고 제거 | `@classmethod` 관련 경고 |
| 서비스-스키마 호환성 전수 검사 | 23개 잠재 불일치 항목 |
| 테스트 커버리지 확대 | 60% → 80% |
| GPU 필터 구현 | Guard + Intent 서비스 코드 |

### 7.3 중장기 계획 (1개월 내)

| 작업 | 설명 |
|------|------|
| GPU 필터 프로덕션 적용 | `log_only` → `block` 전환 |
| 모니터링 대시보드 | Grafana + Prometheus 연동 |
| 후처리기 고도화 | G-Eval 시스템 연동 |
| 티키타카 V2 정식 출시 | 프론트엔드 연동 완료 |

### 7.4 기술 부채 해소

| 항목 | 설명 | 우선순위 |
|------|------|----------|
| `tikitaka_service.py` | dict 접근 패턴 → Pydantic 직접 접근 | P2 |
| `llm_interpreter.py` | Enum 타입 체크 강화 | P2 |
| 테스트 격리 | 외부 서비스 의존 → Mock 강화 | P3 |

---

## 부록 A: 파일 구조 요약

```
yeji-ai-server/ai/
├── src/yeji_ai/
│   ├── api/
│   │   ├── v1/fortune/
│   │   │   ├── eastern.py
│   │   │   ├── western.py
│   │   │   ├── chat.py
│   │   │   └── tikitaka.py      # V2 SSE 스트리밍
│   │   ├── health.py
│   │   ├── metrics.py           # 메트릭 API
│   │   └── router.py
│   ├── models/
│   │   ├── fortune/
│   │   │   ├── eastern.py
│   │   │   ├── western.py
│   │   │   └── chat.py
│   │   ├── enums/
│   │   ├── user_fortune.py      # 핫픽스 적용
│   │   ├── metrics.py           # 메트릭 모델
│   │   └── logging.py           # 로깅 모델
│   ├── services/
│   │   ├── postprocessor/       # 후처리 시스템
│   │   │   ├── base.py
│   │   │   ├── eastern.py
│   │   │   ├── western.py
│   │   │   └── extractors.py
│   │   ├── validation_monitor.py # 검증 모니터
│   │   ├── response_logger.py    # 응답 로거
│   │   ├── tikitaka_service.py
│   │   └── ...
│   └── ...
├── tests/
│   ├── test_postprocessor.py
│   ├── test_validation_monitor.py
│   ├── test_response_logger.py
│   ├── test_metrics_api.py
│   └── ...
└── docs/
    ├── prd/
    │   ├── llm-response-postprocessor.md
    │   └── tikitaka-schema-v2.md
    ├── design/
    │   ├── intent-filter-api.md
    │   └── l4-intent-deployment.md
    ├── guides/
    └── COMPLETE_WORK_SUMMARY.md  # 본 문서
```

---

## 부록 B: 커밋 이력

```
2130a76 fix: [AI] FiveElements/EasternStats에 dict 호환 속성 추가
812fd0e Merge branch 'ai/hotfix/pillar-element-code' into 'ai/main'
8670823 fix: [AI] Pillar.element_code를 ElementCode Enum으로 변경
21ab88d Merge branch 'ai/hotfix/pillar-gan-code' into 'ai/main'
bd35131 fix: [AI] Pillar 모델에 gan_code, ji_code, ten_god_code 필드 추가
d491974 fix: [AI] import 순서 수정 (Literal 최상단 이동)
a1e95b3 fix: [Infra] VLLM_BASE_URL에서 /v1 제거 (중복 방지)
f5a6aec fix: [Infra] Docker 컨테이너 정리 로직 개선
c748ec1 fix: [AI] vLLM base_url 환경변수 연동 (Docker 배포 지원)
1a14a2e fix: [Infra] Jenkinsfile에 vLLM 환경변수 추가 (AWS GPU Elastic IP)
5adce66 fix: [AI] content 변수 초기화 누락 버그 수정
6987879 merge: ai/develop → ai/main (Graceful Degradation)
```

---

## 관련 문서

- [작업 기록 (2026-01-30)](./WORK_LOG_2026-01-30.md)
- [인프라 배포 문서](./infra_deploy.md)
- [Provider 가이드](./PROVIDERS.md)
- [아키텍처 문서](./ARCHITECTURE.md)
- [후처리기 PRD](./prd/llm-response-postprocessor.md)
- [티키타카 V2 PRD](./prd/tikitaka-schema-v2.md)
- [인텐트 필터 API 설계](./design/intent-filter-api.md)
- [L4 배포 아키텍처](./design/l4-intent-deployment.md)

---

*작성일: 2026-01-30*
*작성자: YEJI AI Team (Claude Code Agent)*
