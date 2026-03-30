# LLM 폴백 체인 설계 (LLM Fallback Chain Design)

> **문서 버전**: v1.0
> **작성일**: 2026-01-30
> **상태**: Draft (설계)

---

## 목차

1. [개요](#개요)
2. [폴백 레벨 아키텍처](#폴백-레벨-아키텍처)
3. [폴백 트리거 조건](#폴백-트리거-조건)
4. [레벨별 상세 설계](#레벨별-상세-설계)
5. [GPT 폴백용 프롬프트 설계](#gpt-폴백용-프롬프트-설계)
6. [비용 제한 로직](#비용-제한-로직)
7. [모니터링 메트릭](#모니터링-메트릭)
8. [구현 가이드](#구현-가이드)
9. [미래 확장 계획](#미래-확장-계획)

---

## 개요

### 목적

LLM 응답 실패 시 서비스 가용성을 보장하면서 비용을 효율적으로 관리하기 위한 폴백 체인 시스템을 설계합니다.

### 설계 원칙

1. **가용성 우선**: 사용자에게 항상 응답을 제공
2. **비용 효율성**: 외부 API 호출 비용을 제어 가능한 범위로 제한
3. **품질 유지**: 폴백 시에도 최소한의 품질 보장
4. **관찰 가능성**: 모든 폴백 이벤트를 추적/분석 가능

### 현재 시스템 분석

현재 `FortuneGenerator` 클래스는 다음과 같은 에러 처리 구조를 가지고 있습니다:

```
fortune_generator.py
├── LLMErrorType (에러 타입 분류)
│   ├── VALIDATION    - LLM 응답 스키마 불일치 → 502
│   ├── CONNECTION    - LLM 서비스 연결 불가 → 503
│   ├── TIMEOUT       - LLM 응답 타임아웃 → 504
│   └── UNKNOWN       - 분류되지 않은 에러 → 503
│
├── _call_llm_structured() - 최대 2회 재시도 (max_retries=2)
│   └── 재시도 시 temperature 증가 (+0.1 per attempt)
│
└── generate_*_graceful() - 검증 실패해도 200 응답 반환
```

---

## 폴백 레벨 아키텍처

```
┌─────────────────────────────────────────────────────────────────────┐
│                        사용자 요청 (Eastern/Western)                    │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Level 1: yeji-8b-lora (vLLM)                                       │
│  ─────────────────────────────────────────────────────────────────  │
│  • 메인 모델 (AWS GPU 인스턴스)                                       │
│  • max_retries: 2 (온도 점진적 증가)                                  │
│  • timeout: 120s                                                    │
│  • 예상 성공률: 85-95%                                               │
└─────────────────────────────────────────────────────────────────────┘
                                    │ 실패 시
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Level 2: 후처리 복구 (Postprocessor Recovery)                        │
│  ─────────────────────────────────────────────────────────────────  │
│  • JSON 파싱 오류 → 부분 추출 시도                                    │
│  • 구조 변환 (객체 ↔ 배열)                                           │
│  • 코드 정규화 (대소문자, 유사어 매핑)                                 │
│  • 필수 필드 기본값 채우기                                            │
│  • 예상 복구율: 60-80%                                               │
└─────────────────────────────────────────────────────────────────────┘
                                    │ 복구 실패 시
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Level 3: GPT 폴백 (GPT-5 Mini / GPT-4o-mini)                       │
│  ─────────────────────────────────────────────────────────────────  │
│  • 외부 API 호출 (OpenAI)                                            │
│  • 일일 호출 제한 적용                                                │
│  • 간소화된 프롬프트 사용                                             │
│  • 예상 성공률: 95%+                                                 │
└─────────────────────────────────────────────────────────────────────┘
                                    │ 실패 또는 한도 초과 시
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Level 4: 캐시된 기본 응답 (Cached Default Response)                  │
│  ─────────────────────────────────────────────────────────────────  │
│  • 미리 생성된 템플릿 응답 반환                                        │
│  • 생년월일 기반 간단한 개인화                                         │
│  • 100% 가용성 보장                                                  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 폴백 트리거 조건

### Level 1 → Level 2 (후처리 복구)

| 조건 | 설명 | 에러 타입 |
|------|------|----------|
| JSON 파싱 실패 | LLM 응답이 유효한 JSON이 아닌 경우 | `JSON_PARSE` |
| Pydantic 검증 실패 | 스키마 불일치 (필수 필드 누락, 타입 오류 등) | `VALIDATION` |

**트리거 조건 코드 예시**:
```python
class FallbackTrigger(str, Enum):
    """폴백 트리거 조건"""

    # Level 1 → Level 2
    JSON_PARSE_ERROR = "json_parse_error"
    VALIDATION_ERROR = "validation_error"

    # Level 2 → Level 3
    POSTPROCESS_PARTIAL = "postprocess_partial"  # 부분 복구만 성공
    POSTPROCESS_FAILED = "postprocess_failed"    # 복구 완전 실패

    # Level 1/2 → Level 3
    CONNECTION_ERROR = "connection_error"
    TIMEOUT_ERROR = "timeout_error"
    VLLM_UNAVAILABLE = "vllm_unavailable"

    # Level 3 → Level 4
    GPT_QUOTA_EXCEEDED = "gpt_quota_exceeded"
    GPT_API_ERROR = "gpt_api_error"
    ALL_RETRIES_EXHAUSTED = "all_retries_exhausted"
```

### Level 2 → Level 3 (GPT 폴백)

| 조건 | 설명 |
|------|------|
| 후처리 복구 실패 | Pydantic 검증을 통과하지 못하는 경우 |
| 중요 필드 누락 | `element`, `chart`, `stats` 등 핵심 필드가 복구 불가 |
| 연결/타임아웃 에러 | Level 1에서 연결 자체가 실패한 경우 |

### Level 3 → Level 4 (캐시된 응답)

| 조건 | 설명 |
|------|------|
| 일일 GPT 호출 한도 초과 | 비용 제어를 위한 일일 한도 도달 |
| GPT API 에러 | OpenAI API 자체 오류 |
| 모든 재시도 실패 | Level 1~3 모두 실패 |

---

## 레벨별 상세 설계

### Level 1: yeji-8b-lora (vLLM)

**설정**:
```python
@dataclass
class Level1Config:
    """Level 1 (vLLM) 설정"""

    max_retries: int = 2
    base_timeout: float = 120.0
    temperature_start: float = 0.7
    temperature_increment: float = 0.1
    max_temperature: float = 0.9
    presence_penalty: float = 1.5
```

**재시도 전략**:
- 1차 시도: temperature=0.7
- 2차 시도: temperature=0.8
- 3차 시도: temperature=0.9 (max_retries 초과 시 Level 2로)

### Level 2: 후처리 복구 (Postprocessor Recovery)

**기존 후처리기 활용**:
- `EasternPostprocessor`: 동양 사주 응답 정규화
- `WesternPostprocessor`: 서양 점성술 응답 정규화

**복구 파이프라인**:
```python
class PostprocessorRecovery:
    """Level 2: 후처리 복구 파이프라인"""

    def recover(self, raw_response: str, fortune_type: str) -> RecoveryResult:
        """
        복구 시도 파이프라인:
        1. JSON 추출 시도 (```json 블록, 첫 번째 { } 추출 등)
        2. 구조 변환 (객체 → 배열)
        3. 코드 정규화
        4. 필수 필드 기본값 채우기
        5. Pydantic 재검증
        """
        pass
```

**복구 단계**:
1. **JSON 추출**: `<think>` 태그 제거, 마크다운 코드 블록 추출
2. **구조 변환**: `{"WOOD": 30}` → `[{"code": "WOOD", "percent": 30}]`
3. **코드 정규화**: `wood` → `WOOD`, `목` → `WOOD`
4. **필드 채우기**: 누락된 summary, advice 등 기본값 삽입
5. **재검증**: Pydantic 모델로 최종 검증

### Level 3: GPT 폴백

**Provider 설계**:
```python
@dataclass
class GPTFallbackConfig:
    """GPT 폴백 설정"""

    # 모델 선택 (우선순위)
    primary_model: str = "gpt-5-mini"        # 1순위: 최신 저비용 모델
    fallback_model: str = "gpt-4o-mini"      # 2순위: 백업 모델

    # API 설정
    api_key_env: str = "OPENAI_API_KEY"
    timeout: float = 60.0
    max_retries: int = 2

    # 비용 제어
    daily_quota: int = 100                   # 일일 최대 호출 횟수
    max_tokens: int = 1500                   # 응답 최대 토큰 (비용 절감)
    temperature: float = 0.3                 # 낮은 온도 (일관성 우선)
```

**호출 로직**:
```python
class GPTFallbackProvider:
    """Level 3: GPT 폴백 Provider"""

    async def generate(
        self,
        fortune_type: Literal["eastern", "western"],
        birth_data: dict[str, Any],
    ) -> FortuneResponse:
        """
        GPT API 호출

        1. 일일 한도 확인
        2. 간소화된 프롬프트 생성
        3. API 호출 (primary_model → fallback_model)
        4. 응답 검증 및 반환
        """
        pass
```

### Level 4: 캐시된 기본 응답

**템플릿 응답**:
```python
class CachedResponseProvider:
    """Level 4: 캐시된 기본 응답 Provider"""

    def get_default_response(
        self,
        fortune_type: Literal["eastern", "western"],
        birth_data: dict[str, Any],
    ) -> FortuneResponse:
        """
        미리 정의된 템플릿 기반 응답 생성

        - 생년월일 기반 간단한 개인화 (예: 별자리, 오행)
        - 일반적인 조언 메시지
        - 에러 표시 없이 정상 응답 형태
        """
        pass
```

**개인화 로직**:
- 동양 (Eastern): 출생 연도 기반 오행 계산
- 서양 (Western): 출생 월/일 기반 별자리 결정

---

## GPT 폴백용 프롬프트 설계

### 동양 사주 (Eastern) - GPT 프롬프트

```python
GPT_EASTERN_SYSTEM_PROMPT = """당신은 사주 해석 전문가입니다.
주어진 생년월일시로 간결한 사주 분석을 JSON 형식으로 제공합니다.

출력 형식:
- 반드시 유효한 JSON만 출력
- 한국어 사용
- element: WOOD, FIRE, EARTH, METAL, WATER 중 하나
- 간결하고 긍정적인 톤
"""

GPT_EASTERN_USER_PROMPT_TEMPLATE = """
생년월일시: {birth_year}년 {birth_month}월 {birth_day}일 {birth_hour}시

다음 JSON 형식으로 응답하세요:
{{
  "element": "대표 오행 (WOOD/FIRE/EARTH/METAL/WATER)",
  "chart": {{
    "summary": "사주 요약 (2-3문장)",
    "year": {{"gan": "천간", "ji": "지지", "element_code": "오행코드"}},
    "month": {{"gan": "천간", "ji": "지지", "element_code": "오행코드"}},
    "day": {{"gan": "천간", "ji": "지지", "element_code": "오행코드"}},
    "hour": {{"gan": "천간", "ji": "지지", "element_code": "오행코드"}}
  }},
  "stats": {{
    "cheongan_jiji": {{
      "summary": "천간지지 요약",
      "year": {{"cheon_gan": "천간", "ji_ji": "지지"}},
      "month": {{"cheon_gan": "천간", "ji_ji": "지지"}},
      "day": {{"cheon_gan": "천간", "ji_ji": "지지"}},
      "hour": {{"cheon_gan": "천간", "ji_ji": "지지"}}
    }},
    "five_elements": {{
      "summary": "오행 분석 요약",
      "list": [
        {{"code": "WOOD", "label": "목", "percent": 숫자}},
        {{"code": "FIRE", "label": "화", "percent": 숫자}},
        {{"code": "EARTH", "label": "토", "percent": 숫자}},
        {{"code": "METAL", "label": "금", "percent": 숫자}},
        {{"code": "WATER", "label": "수", "percent": 숫자}}
      ]
    }},
    "yin_yang_ratio": {{"summary": "음양 요약", "yin": 숫자, "yang": 숫자}},
    "ten_gods": {{
      "summary": "십신 요약",
      "list": [{{"code": "BI_GYEON", "label": "비견", "percent": 숫자}}]
    }}
  }},
  "final_verdict": {{
    "summary": "종합 요약",
    "strength": "강점",
    "weakness": "보완점",
    "advice": "조언"
  }},
  "lucky": {{"color": "색상", "number": "숫자", "item": "아이템"}}
}}
"""
```

### 서양 점성술 (Western) - GPT 프롬프트

```python
GPT_WESTERN_SYSTEM_PROMPT = """당신은 서양 점성술 전문가입니다.
주어진 생년월일시로 간결한 별자리 분석을 JSON 형식으로 제공합니다.

출력 형식:
- 반드시 유효한 JSON만 출력
- 한국어 사용
- element: FIRE, EARTH, AIR, WATER 중 하나
- 신비롭고 시적인 톤
"""

GPT_WESTERN_USER_PROMPT_TEMPLATE = """
생년월일시: {birth_year}년 {birth_month}월 {birth_day}일 {birth_hour}시 {birth_minute}분

다음 JSON 형식으로 응답하세요:
{{
  "element": "대표 원소 (FIRE/EARTH/AIR/WATER)",
  "stats": {{
    "main_sign": {{"name": "별자리 (예: 물병자리)"}},
    "element_summary": "원소 분석 요약",
    "element_4_distribution": [
      {{"code": "FIRE", "label": "불", "percent": 숫자}},
      {{"code": "EARTH", "label": "흙", "percent": 숫자}},
      {{"code": "AIR", "label": "공기", "percent": 숫자}},
      {{"code": "WATER", "label": "물", "percent": 숫자}}
    ],
    "modality_summary": "양태 분석 요약",
    "modality_3_distribution": [
      {{"code": "CARDINAL", "label": "활동", "percent": 숫자}},
      {{"code": "FIXED", "label": "고정", "percent": 숫자}},
      {{"code": "MUTABLE", "label": "변동", "percent": 숫자}}
    ],
    "keywords_summary": "키워드 요약",
    "keywords": [
      {{"code": "EMPATHY", "label": "공감", "weight": 0.9}}
    ]
  }},
  "fortune_content": {{
    "overview": "운세 개요 (의미심장하게)",
    "detailed_analysis": [
      {{"title": "제목1", "content": "내용1"}},
      {{"title": "제목2", "content": "내용2"}}
    ],
    "advice": "조언"
  }},
  "lucky": {{"color": "색상", "number": "숫자"}}
}}
"""
```

### GPT 프롬프트 설계 원칙

1. **간결성**: 토큰 수 최소화 (비용 절감)
2. **구조 명시**: JSON 예시를 직접 제공
3. **제약 강조**: 유효한 코드값만 사용하도록 명시
4. **폴백 친화적**: 복잡한 지시 최소화

---

## 비용 제한 로직

### 일일 한도 관리

```python
@dataclass
class QuotaConfig:
    """GPT 폴백 비용 제어 설정"""

    # 일일 한도
    daily_eastern_quota: int = 50      # 동양 사주 일일 최대 호출
    daily_western_quota: int = 50      # 서양 점성술 일일 최대 호출
    daily_total_quota: int = 100       # 전체 일일 최대 호출

    # 시간당 한도 (버스트 방지)
    hourly_quota: int = 20             # 시간당 최대 호출

    # 비용 알림 임계값
    cost_warning_threshold: float = 0.8   # 한도의 80% 도달 시 경고
    cost_critical_threshold: float = 0.95 # 한도의 95% 도달 시 위험
```

### 할당량 추적 서비스

```python
class QuotaTracker:
    """GPT 폴백 할당량 추적"""

    def __init__(self, config: QuotaConfig):
        self.config = config
        self._daily_counts: Counter[str] = Counter()  # {"eastern": 10, "western": 5}
        self._hourly_counts: Counter[str] = Counter()
        self._last_reset: datetime = datetime.utcnow()
        self._last_hourly_reset: datetime = datetime.utcnow()

    def can_use_gpt(self, fortune_type: str) -> tuple[bool, str]:
        """
        GPT 호출 가능 여부 확인

        Returns:
            (허용 여부, 거부 사유)
        """
        self._reset_if_needed()

        # 전체 한도 확인
        total_used = sum(self._daily_counts.values())
        if total_used >= self.config.daily_total_quota:
            return False, "daily_total_quota_exceeded"

        # 타입별 한도 확인
        type_quota = getattr(self.config, f"daily_{fortune_type}_quota")
        if self._daily_counts[fortune_type] >= type_quota:
            return False, f"daily_{fortune_type}_quota_exceeded"

        # 시간당 한도 확인
        hourly_used = sum(self._hourly_counts.values())
        if hourly_used >= self.config.hourly_quota:
            return False, "hourly_quota_exceeded"

        return True, ""

    def record_usage(self, fortune_type: str) -> None:
        """GPT 호출 기록"""
        self._daily_counts[fortune_type] += 1
        self._hourly_counts[fortune_type] += 1

    def get_usage_stats(self) -> dict[str, Any]:
        """현재 사용량 통계 반환"""
        return {
            "daily": dict(self._daily_counts),
            "hourly": dict(self._hourly_counts),
            "daily_total_remaining": self.config.daily_total_quota - sum(self._daily_counts.values()),
            "hourly_remaining": self.config.hourly_quota - sum(self._hourly_counts.values()),
        }
```

### 비용 추정 (참고)

| 모델 | 입력 토큰 단가 | 출력 토큰 단가 | 예상 호출당 비용 |
|------|--------------|--------------|----------------|
| gpt-5-mini | $0.001/1K | $0.002/1K | ~$0.003 |
| gpt-4o-mini | $0.00015/1K | $0.0006/1K | ~$0.001 |

**일일 최대 예상 비용** (100회 호출 기준):
- gpt-5-mini: ~$0.30/일
- gpt-4o-mini: ~$0.10/일

---

## 모니터링 메트릭

### 기존 메트릭 확장

현재 `ValidationMonitor`에 폴백 관련 메트릭을 추가합니다.

```python
class FallbackMetrics(BaseModel):
    """폴백 체인 메트릭"""

    # 레벨별 트리거 횟수
    level1_total: int = 0           # vLLM 호출 총 횟수
    level1_success: int = 0         # vLLM 성공 횟수
    level1_failure: int = 0         # vLLM 실패 → Level 2로 이동

    level2_triggered: int = 0       # 후처리 복구 시도 횟수
    level2_success: int = 0         # 후처리 복구 성공
    level2_failure: int = 0         # 후처리 복구 실패 → Level 3으로 이동

    level3_triggered: int = 0       # GPT 폴백 호출 횟수
    level3_success: int = 0         # GPT 폴백 성공
    level3_failure: int = 0         # GPT 폴백 실패 → Level 4로 이동
    level3_quota_blocked: int = 0   # 할당량 초과로 차단된 횟수

    level4_triggered: int = 0       # 캐시 응답 반환 횟수

    # 레벨별 성공률
    @computed_field
    @property
    def level1_success_rate(self) -> float:
        if self.level1_total == 0:
            return 0.0
        return round((self.level1_success / self.level1_total) * 100, 2)

    # 전체 가용성 (최종 응답 제공 성공률)
    @computed_field
    @property
    def overall_availability(self) -> float:
        total = self.level1_total
        if total == 0:
            return 100.0
        success = self.level1_success + self.level2_success + self.level3_success + self.level4_triggered
        return round((success / total) * 100, 2)
```

### Prometheus 메트릭

```python
# 폴백 레벨별 카운터
FALLBACK_METRICS = {
    "yeji_fallback_level1_total": "Level 1 (vLLM) 총 호출 수",
    "yeji_fallback_level1_success": "Level 1 성공 수",
    "yeji_fallback_level2_triggered": "Level 2 (후처리) 트리거 수",
    "yeji_fallback_level2_success": "Level 2 복구 성공 수",
    "yeji_fallback_level3_triggered": "Level 3 (GPT) 트리거 수",
    "yeji_fallback_level3_success": "Level 3 성공 수",
    "yeji_fallback_level3_quota_blocked": "Level 3 할당량 차단 수",
    "yeji_fallback_level4_triggered": "Level 4 (캐시) 반환 수",
}

# 게이지
"yeji_fallback_gpt_quota_remaining": "GPT 일일 남은 할당량"
"yeji_fallback_overall_availability": "전체 가용성 (%)"
```

### 로깅 이벤트

```python
# 폴백 발생 시 로그 예시
logger.warning(
    "fallback_triggered",
    from_level=1,
    to_level=2,
    fortune_type="eastern",
    trigger="validation_error",
    error_count=3,
)

logger.info(
    "fallback_success",
    level=2,
    fortune_type="eastern",
    recovery_steps=["convert_structures", "normalize_codes", "fill_defaults"],
    latency_ms=45.2,
)

logger.error(
    "fallback_chain_exhausted",
    fortune_type="western",
    final_level=4,
    trigger_chain=["timeout", "postprocess_failed", "gpt_quota_exceeded"],
)
```

### 알림 조건

| 조건 | 알림 레벨 | 액션 |
|------|----------|------|
| Level 1 성공률 < 80% (1시간) | WARNING | Slack 알림 |
| Level 3 일일 한도 80% 도달 | WARNING | Slack 알림 |
| Level 3 일일 한도 95% 도달 | CRITICAL | Slack + PagerDuty |
| Level 4 1시간 내 10회 이상 | ERROR | Slack 알림 |
| 전체 가용성 < 99% (1시간) | ERROR | Slack 알림 |

---

## 구현 가이드

### 파일 구조

```
yeji-ai-server/ai/src/yeji_ai/
├── providers/
│   ├── base.py                    # 기존 LLMProvider 인터페이스
│   ├── aws.py                     # 기존 AWS Provider
│   ├── gpt.py                     # 새로 추가: GPT Provider
│   └── __init__.py
├── services/
│   ├── fortune_generator.py       # 기존 (수정 필요)
│   ├── fallback/                  # 새로 추가: 폴백 모듈
│   │   ├── __init__.py
│   │   ├── chain.py               # FallbackChain 메인 로직
│   │   ├── quota_tracker.py       # 할당량 추적
│   │   ├── cached_responses.py    # Level 4 캐시 응답
│   │   └── prompts.py             # GPT용 프롬프트
│   ├── postprocessor/             # 기존 (활용)
│   │   ├── eastern.py
│   │   └── western.py
│   └── ...
├── models/
│   ├── fallback.py                # 새로 추가: 폴백 관련 모델
│   └── ...
└── config.py                      # 설정 확장
```

### 설정 확장 (config.py)

```python
class Settings(BaseSettings):
    # ... 기존 설정 ...

    # GPT 폴백 설정
    openai_api_key: str = ""
    gpt_fallback_enabled: bool = True
    gpt_primary_model: str = "gpt-5-mini"
    gpt_fallback_model: str = "gpt-4o-mini"
    gpt_daily_quota: int = 100
    gpt_hourly_quota: int = 20
    gpt_timeout: float = 60.0

    # 캐시 응답 설정
    cached_response_enabled: bool = True
```

### 환경 변수

```bash
# .env.example에 추가
OPENAI_API_KEY=sk-...                    # OpenAI API 키 (GPT 폴백용)
GPT_FALLBACK_ENABLED=true                # GPT 폴백 활성화
GPT_PRIMARY_MODEL=gpt-5-mini             # 1순위 GPT 모델
GPT_FALLBACK_MODEL=gpt-4o-mini           # 2순위 GPT 모델
GPT_DAILY_QUOTA=100                      # 일일 GPT 호출 한도
GPT_HOURLY_QUOTA=20                      # 시간당 GPT 호출 한도
```

### 구현 순서 (권장)

1. **Phase 1**: Level 2 강화
   - 기존 후처리기에 JSON 추출 로직 추가
   - 복구 결과를 상세히 로깅

2. **Phase 2**: Level 4 구현
   - 캐시된 응답 템플릿 준비
   - 간단한 개인화 로직 (별자리, 오행 계산)

3. **Phase 3**: Level 3 구현
   - GPT Provider 구현
   - 할당량 추적 서비스 구현
   - GPT용 프롬프트 최적화

4. **Phase 4**: 통합 및 모니터링
   - FallbackChain 통합
   - 메트릭/알림 연동

---

## 미래 확장 계획

### L4 GPU 4B 모델 추가 (설계만)

향후 AWS L4 GPU에 4B 경량 모델을 배포하여 폴백 체인에 추가할 수 있습니다.

```
┌─────────────────────────────────────────────────────────────────────┐
│  Level 1.5: yeji-4b (L4 GPU)  [미래 추가 예정]                        │
│  ─────────────────────────────────────────────────────────────────  │
│  • 경량 모델 (4B 파라미터)                                            │
│  • 빠른 응답 (Level 1 대비 50% 감소)                                  │
│  • 낮은 비용 (L4 GPU 시간당 비용 절감)                                │
│  • Level 1 연결 실패 시 우선 시도                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**고려사항**:
- 4B 모델용 별도 vLLM 인스턴스 필요
- 프롬프트 최적화 필요 (모델 크기 제한)
- 품질 vs 속도 트레이드오프 분석 필요

### 스마트 라우팅

향후 요청 특성에 따라 최적의 레벨을 선택하는 스마트 라우팅 도입 가능:

```python
class SmartRouter:
    """스마트 폴백 라우터 [미래 구현]"""

    def select_level(self, request: FortuneRequest) -> int:
        """
        요청 특성에 따라 시작 레벨 선택

        예시:
        - 피크 시간대 + 간단한 요청 → Level 1.5 (4B)
        - vLLM 과부하 감지 → Level 3 (GPT) 직접 호출
        - 실험 그룹 → 특정 레벨 강제
        """
        pass
```

---

## 체크리스트

### 구현 전 확인사항

- [ ] OpenAI API 키 발급 및 환경변수 설정
- [ ] GPT 모델별 비용 및 한도 확인
- [ ] Level 4 템플릿 응답 콘텐츠 준비
- [ ] 모니터링/알림 채널 설정 (Slack, PagerDuty)

### 테스트 시나리오

- [ ] Level 1 → Level 2: JSON 파싱 실패 케이스
- [ ] Level 1 → Level 2: Pydantic 검증 실패 케이스
- [ ] Level 2 → Level 3: 후처리 복구 실패 케이스
- [ ] Level 3 할당량 초과 → Level 4
- [ ] 전체 체인 실패 → Level 4 캐시 응답

### 운영 체크리스트

- [ ] 일일 GPT 비용 모니터링
- [ ] 폴백 레벨별 성공률 대시보드
- [ ] 알림 임계값 조정 (트래픽 패턴에 따라)

---

## 참조 문서

| 문서 | 경로 |
|------|------|
| Provider 가이드 | `yeji-ai-server/ai/docs/PROVIDERS.md` |
| 후처리기 설계 | `yeji-ai-server/ai/docs/prd/llm-response-postprocessor.md` |
| 후처리기 아키텍처 | `yeji-ai-server/ai/docs/architecture/postprocessor.md` |
| Qwen3 프롬프팅 가이드 | `yeji-ai-server/ai/docs/guides/qwen3-prompting-guide.md` |
| 검증 메트릭 모델 | `yeji_ai/models/metrics.py` |
| 검증 모니터 서비스 | `yeji_ai/services/validation_monitor.py` |

---

> **Note**: 이 문서는 설계 단계이며, 구현 시 세부 사항이 변경될 수 있습니다.
