# GPT 폴백 프롬프트 설계 (PoC)

> **문서 버전**: v1.0
> **작성일**: 2026-01-30
> **상태**: Draft (PoC 설계)
> **관련 문서**: [LLM 폴백 체인 설계](./llm-fallback-chain.md)

---

## 목차

1. [개요](#개요)
2. [프롬프트 비교 분석](#프롬프트-비교-분석)
3. [GPT 폴백 프롬프트 설계](#gpt-폴백-프롬프트-설계)
4. [GPT Provider 스켈레톤](#gpt-provider-스켈레톤)
5. [비용 최적화 전략](#비용-최적화-전략)
6. [테스트 및 검증](#테스트-및-검증)

---

## 개요

### 목적

yeji-8b 모델 실패 시 GPT API로 폴백하여 서비스 가용성을 보장합니다.
GPT는 비용이 발생하므로 **토큰 최적화**와 **비용 제어**가 핵심입니다.

### 설계 원칙

| 원칙 | yeji-8b 프롬프트 | GPT 폴백 프롬프트 |
|------|-----------------|------------------|
| 토큰 길이 | ~3000 토큰 | **~800 토큰** (73% 절감) |
| 예시 포함 | 상세 JSON 예시 | 스키마만 제공 |
| 제약 조건 | 매우 상세 (XML 태그) | 핵심만 간결하게 |
| 캐릭터 설정 | 상세 (소이설, 스텔라) | 생략 |
| 모델 특성 | `/no_think` 모드 필요 | 불필요 (GPT 기본 지원) |

### GPT 모델 선택

| 모델 | 입력 단가 | 출력 단가 | 속도 | 권장 용도 |
|------|----------|----------|------|----------|
| **gpt-4o-mini** | $0.15/1M | $0.60/1M | 빠름 | 1순위 (비용 효율) |
| gpt-4o | $2.50/1M | $10.00/1M | 보통 | 고품질 필요 시 |
| gpt-3.5-turbo | $0.50/1M | $1.50/1M | 매우 빠름 | 폴백의 폴백 |

**권장**: `gpt-4o-mini` (비용 대비 성능 최적)

---

## 프롬프트 비교 분석

### yeji-8b용 프롬프트 특징

```
fortune_prompts.py (현재)
├── EASTERN_SYSTEM_PROMPT (~50 토큰)
│   └── /no_think 모드 지시
│   └── 캐릭터 설정 (소이설)
│   └── 톤/특징 설명
│
├── EASTERN_SCHEMA_INSTRUCTION (~2500 토큰)
│   └── <constraints> XML 태그 (상세 규칙)
│   └── 필드별 허용값 나열
│   └── <example> JSON 예시 (전체 구조)
│
└── build_eastern_generation_prompt()
    └── 생년월일시 + 성별 삽입
```

**문제점**:
1. `/no_think` 지시어 → GPT에서 불필요
2. 상세한 제약 조건 → GPT는 스키마만으로 충분
3. 전체 JSON 예시 → 토큰 낭비

### GPT용 프롬프트 간소화 전략

| 항목 | yeji-8b | GPT | 이유 |
|------|---------|-----|------|
| `/no_think` | 필수 | 제거 | GPT 기본 지원 |
| 캐릭터 설정 | 상세 | 한 줄 | 품질 영향 적음 |
| XML 태그 | `<constraints>` | 마크다운 | 가독성 동일 |
| 필드 나열 | 전체 허용값 | 핵심만 | GPT 추론 능력 활용 |
| JSON 예시 | 전체 | TypeScript 타입 | 50% 토큰 절감 |

---

## GPT 폴백 프롬프트 설계

### 동양 운세 (Eastern) - GPT 프롬프트

```python
# yeji-ai-server/ai/src/yeji_ai/services/fallback/prompts.py

GPT_EASTERN_SYSTEM = """당신은 사주 분석가입니다. 생년월일시를 기반으로 사주팔자를 분석합니다.
반드시 지정된 JSON 형식으로만 응답하세요. 다른 텍스트 없이 JSON만 출력합니다."""


GPT_EASTERN_USER_TEMPLATE = """생년월일시: {birth_year}년 {birth_month}월 {birth_day}일 {birth_hour}시
성별: {gender}

## 응답 형식 (JSON)

```typescript
interface Response {{
  element: "WOOD" | "FIRE" | "EARTH" | "METAL" | "WATER";  // 대표 오행
  chart: {{
    summary: string;  // 사주 요약 (2-3문장)
    year: Pillar;
    month: Pillar;
    day: Pillar;
    hour: Pillar;
  }};
  stats: {{
    five_elements: {{
      summary: string;
      list: {{ code: ElementCode; label: string; percent: number; }}[];  // 5개, 합계=100
    }};
    yin_yang_ratio: {{ summary: string; yin: number; yang: number; }};  // 합계=100
    ten_gods: {{
      summary: string;
      list: {{ code: TenGodCode; label: string; percent: number; }}[];  // 상위 3-4개
    }};
  }};
  final_verdict: {{
    summary: string;
    strength: string;
    weakness: string;
    advice: string;
  }};
  lucky: {{ color: string; number: string; item: string; }};
}}

// Pillar = {{ gan: "甲"|"乙"|"丙"|"丁"|"戊"|"己"|"庚"|"辛"|"壬"|"癸",
//             ji: "子"|"丑"|"寅"|"卯"|"辰"|"巳"|"午"|"未"|"申"|"酉"|"戌"|"亥",
//             element_code: ElementCode }}
// ElementCode = "WOOD" | "FIRE" | "EARTH" | "METAL" | "WATER"
// TenGodCode = "BI_GYEON" | "GANG_JAE" | "SIK_SIN" | "SANG_GWAN" | "PYEON_JAE" | "JEONG_JAE" | "PYEON_GWAN" | "JEONG_GWAN" | "PYEON_IN" | "JEONG_IN" | "ETC"
```

위 타입에 맞는 유효한 JSON을 출력하세요. 한국어로 작성합니다."""


def build_gpt_eastern_prompt(
    birth_year: int,
    birth_month: int,
    birth_day: int,
    birth_hour: int,
    gender: str = "unknown",
) -> tuple[str, str]:
    """GPT용 동양 사주 프롬프트 생성

    Returns:
        (system_prompt, user_prompt)
    """
    user_prompt = GPT_EASTERN_USER_TEMPLATE.format(
        birth_year=birth_year,
        birth_month=birth_month,
        birth_day=birth_day,
        birth_hour=birth_hour,
        gender=gender,
    )
    return GPT_EASTERN_SYSTEM, user_prompt
```

**토큰 추정**:
- 시스템 프롬프트: ~40 토큰
- 사용자 프롬프트: ~400 토큰
- **총 입력: ~450 토큰** (기존 대비 85% 절감)

---

### 서양 운세 (Western) - GPT 프롬프트

```python
GPT_WESTERN_SYSTEM = """당신은 점성술사입니다. 생년월일시를 기반으로 별자리 차트를 분석합니다.
반드시 지정된 JSON 형식으로만 응답하세요. 다른 텍스트 없이 JSON만 출력합니다."""


GPT_WESTERN_USER_TEMPLATE = """생년월일시: {birth_year}년 {birth_month}월 {birth_day}일 {birth_hour}시 {birth_minute}분
출생지 좌표: 위도 {latitude}, 경도 {longitude}

## 응답 형식 (JSON)

```typescript
interface Response {{
  element: "FIRE" | "EARTH" | "AIR" | "WATER";  // 대표 원소
  stats: {{
    main_sign: {{ name: ZodiacName }};  // 태양 별자리
    element_summary: string;
    element_4_distribution: {{ code: ZodiacElement; label: string; percent: number; }}[];  // 4개
    modality_summary: string;
    modality_3_distribution: {{ code: Modality; label: string; percent: number; }}[];  // 3개
    keywords_summary: string;
    keywords: {{ code: KeywordCode; label: string; weight: number; }}[];  // 3-5개
  }};
  fortune_content: {{
    overview: string;  // 운세 개요 (2-3문장)
    detailed_analysis: {{ title: string; content: string; }}[];  // 정확히 2개
    advice: string;
  }};
  lucky: {{ color: string; number: string; }};
}}

// ZodiacName = "양자리" | "황소자리" | "쌍둥이자리" | "게자리" | "사자자리" | "처녀자리" | "천칭자리" | "전갈자리" | "사수자리" | "염소자리" | "물병자리" | "물고기자리"
// ZodiacElement = "FIRE" | "EARTH" | "AIR" | "WATER"
// Modality = "CARDINAL" | "FIXED" | "MUTABLE"
// KeywordCode = "EMPATHY" | "INTUITION" | "IMAGINATION" | "LEADERSHIP" | "PASSION" | "STABILITY" | "COMMUNICATION" | "CREATIVITY" | "AMBITION" | "HARMONY" | "INDEPENDENCE" | "SENSITIVITY"
```

위 타입에 맞는 유효한 JSON을 출력하세요. 신비롭고 시적인 톤으로 한국어 작성합니다."""


def build_gpt_western_prompt(
    birth_year: int,
    birth_month: int,
    birth_day: int,
    birth_hour: int = 12,
    birth_minute: int = 0,
    latitude: float = 37.5665,
    longitude: float = 126.9780,
) -> tuple[str, str]:
    """GPT용 서양 점성술 프롬프트 생성

    Returns:
        (system_prompt, user_prompt)
    """
    user_prompt = GPT_WESTERN_USER_TEMPLATE.format(
        birth_year=birth_year,
        birth_month=birth_month,
        birth_day=birth_day,
        birth_hour=birth_hour,
        birth_minute=birth_minute,
        latitude=latitude,
        longitude=longitude,
    )
    return GPT_WESTERN_SYSTEM, user_prompt
```

**토큰 추정**:
- 시스템 프롬프트: ~40 토큰
- 사용자 프롬프트: ~350 토큰
- **총 입력: ~400 토큰**

---

## GPT Provider 스켈레톤

### 파일 구조

```
yeji-ai-server/ai/src/yeji_ai/
├── providers/
│   ├── base.py              # 기존 LLMProvider 인터페이스
│   ├── vllm.py              # 기존 vLLM Provider
│   └── gpt.py               # 신규: GPT Provider
└── services/
    └── fallback/
        ├── __init__.py
        ├── prompts.py       # GPT용 프롬프트
        ├── quota_tracker.py # 할당량 추적
        └── chain.py         # 폴백 체인 오케스트레이터
```

### GPT Provider 구현 (스켈레톤)

```python
# yeji-ai-server/ai/src/yeji_ai/providers/gpt.py

"""GPT Provider - OpenAI API 연동

폴백 레벨 3에서 사용되는 GPT API Provider입니다.
비용 제어와 에러 처리가 핵심입니다.
"""

import time
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

import httpx
import structlog

from yeji_ai.providers.base import (
    CompletionResponse,
    GenerationConfig,
    LLMProvider,
    ProviderHealth,
    ProviderStatus,
)

logger = structlog.get_logger()


@dataclass
class GPTConfig:
    """GPT Provider 설정"""

    # API 설정
    api_key: str = ""  # 환경변수에서 주입
    base_url: str = "https://api.openai.com/v1"
    primary_model: str = "gpt-4o-mini"
    fallback_model: str = "gpt-3.5-turbo"
    timeout: float = 60.0

    # 생성 설정
    max_tokens: int = 1500  # 비용 절감을 위해 제한
    temperature: float = 0.3  # 낮은 온도로 일관성 확보

    # 비용 제어
    daily_quota: int = 100  # 일일 최대 호출
    hourly_quota: int = 20  # 시간당 최대 호출

    # 재시도 설정
    max_retries: int = 2
    retry_delay: float = 1.0


class GPTQuotaExceededError(Exception):
    """GPT 할당량 초과 에러"""

    def __init__(self, quota_type: str, used: int, limit: int):
        self.quota_type = quota_type
        self.used = used
        self.limit = limit
        super().__init__(f"{quota_type} 할당량 초과: {used}/{limit}")


class GPTProvider(LLMProvider):
    """GPT Provider 구현 (Level 3 폴백용)

    사용 예시:
        config = GPTConfig(api_key=os.environ["OPENAI_API_KEY"])
        provider = GPTProvider(config)

        # 할당량 확인 후 호출
        if provider.can_use():
            response = await provider.chat([
                {"role": "system", "content": "..."},
                {"role": "user", "content": "..."},
            ])
    """

    def __init__(self, config: GPTConfig):
        self.config = config
        self._http_client: httpx.AsyncClient | None = None
        self._current_status = ProviderStatus.UNKNOWN

        # 할당량 추적 (간소화된 인메모리 버전)
        self._daily_count: int = 0
        self._hourly_count: int = 0
        self._last_daily_reset: datetime = datetime.utcnow()
        self._last_hourly_reset: datetime = datetime.utcnow()

    @property
    def name(self) -> str:
        return "gpt"

    # ================================================================
    # 할당량 관리
    # ================================================================

    def _reset_quotas_if_needed(self) -> None:
        """할당량 리셋 (일/시간 경과 시)"""
        now = datetime.utcnow()

        # 일일 리셋 (UTC 기준 자정)
        if now.date() > self._last_daily_reset.date():
            self._daily_count = 0
            self._last_daily_reset = now
            logger.info("gpt_daily_quota_reset")

        # 시간당 리셋
        if (now - self._last_hourly_reset).seconds >= 3600:
            self._hourly_count = 0
            self._last_hourly_reset = now
            logger.info("gpt_hourly_quota_reset")

    def can_use(self) -> tuple[bool, str]:
        """GPT 호출 가능 여부 확인

        Returns:
            (허용 여부, 거부 사유)
        """
        self._reset_quotas_if_needed()

        if self._daily_count >= self.config.daily_quota:
            return False, "daily_quota_exceeded"

        if self._hourly_count >= self.config.hourly_quota:
            return False, "hourly_quota_exceeded"

        return True, ""

    def _record_usage(self) -> None:
        """사용량 기록"""
        self._reset_quotas_if_needed()
        self._daily_count += 1
        self._hourly_count += 1

    def get_quota_stats(self) -> dict[str, Any]:
        """현재 할당량 상태 반환"""
        self._reset_quotas_if_needed()
        return {
            "daily_used": self._daily_count,
            "daily_limit": self.config.daily_quota,
            "daily_remaining": self.config.daily_quota - self._daily_count,
            "hourly_used": self._hourly_count,
            "hourly_limit": self.config.hourly_quota,
            "hourly_remaining": self.config.hourly_quota - self._hourly_count,
        }

    # ================================================================
    # LLMProvider 인터페이스 구현
    # ================================================================

    async def _get_http_client(self) -> httpx.AsyncClient:
        """HTTP 클라이언트 반환 (lazy initialization)"""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                base_url=self.config.base_url,
                timeout=httpx.Timeout(self.config.timeout),
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json",
                },
            )
        return self._http_client

    async def start(self) -> bool:
        """Provider 시작 (API 키 검증)"""
        if not self.config.api_key:
            logger.error("gpt_api_key_missing")
            self._current_status = ProviderStatus.ERROR
            return False

        # API 키 검증 (모델 목록 조회)
        try:
            client = await self._get_http_client()
            response = await client.get("/models", timeout=10.0)

            if response.status_code == 200:
                self._current_status = ProviderStatus.RUNNING
                logger.info("gpt_provider_started", model=self.config.primary_model)
                return True
            else:
                logger.error("gpt_api_key_invalid", status=response.status_code)
                self._current_status = ProviderStatus.ERROR
                return False

        except Exception as e:
            logger.error("gpt_provider_start_error", error=str(e))
            self._current_status = ProviderStatus.ERROR
            return False

    async def stop(self) -> bool:
        """Provider 중지"""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
            self._http_client = None

        self._current_status = ProviderStatus.STOPPED
        return True

    async def status(self) -> ProviderStatus:
        """현재 상태 확인"""
        return self._current_status

    async def health(self) -> ProviderHealth:
        """헬스체크"""
        if self._current_status != ProviderStatus.RUNNING:
            return ProviderHealth(
                status=self._current_status,
                error_message="Provider not running",
            )

        # 할당량 정보 포함
        quota_stats = self.get_quota_stats()

        return ProviderHealth(
            status=ProviderStatus.RUNNING,
            model=self.config.primary_model,
            extra={
                "quota": quota_stats,
                "provider": "openai",
            },
        )

    async def chat(
        self,
        messages: list[dict[str, str]],
        config: GenerationConfig | None = None,
    ) -> CompletionResponse:
        """채팅 완성 (non-streaming)

        할당량을 확인하고, 초과 시 예외를 발생시킵니다.
        """
        # 할당량 확인
        can_use, reason = self.can_use()
        if not can_use:
            stats = self.get_quota_stats()
            raise GPTQuotaExceededError(
                quota_type=reason,
                used=stats.get(f"{reason.replace('_exceeded', '')}_used", 0),
                limit=stats.get(f"{reason.replace('_exceeded', '')}_limit", 0),
            )

        config = config or GenerationConfig()
        start_time = time.time()

        payload = {
            "model": self.config.primary_model,
            "messages": messages,
            "max_tokens": config.max_tokens or self.config.max_tokens,
            "temperature": config.temperature or self.config.temperature,
            "response_format": {"type": "json_object"},  # JSON 모드 강제
        }

        # 재시도 로직
        last_error: Exception | None = None
        models_to_try = [self.config.primary_model, self.config.fallback_model]

        for model in models_to_try:
            payload["model"] = model

            for attempt in range(self.config.max_retries):
                try:
                    client = await self._get_http_client()
                    response = await client.post("/chat/completions", json=payload)

                    if response.status_code == 200:
                        data = response.json()
                        choice = data["choices"][0]
                        latency_ms = (time.time() - start_time) * 1000

                        # 사용량 기록
                        self._record_usage()

                        logger.info(
                            "gpt_chat_success",
                            model=model,
                            latency_ms=round(latency_ms, 2),
                            usage=data.get("usage"),
                        )

                        return CompletionResponse(
                            text=choice["message"]["content"],
                            finish_reason=choice.get("finish_reason"),
                            usage=data.get("usage"),
                            model=model,
                            latency_ms=latency_ms,
                        )

                    # Rate limit 처리
                    if response.status_code == 429:
                        logger.warning(
                            "gpt_rate_limited",
                            model=model,
                            attempt=attempt + 1,
                        )
                        await self._wait_for_retry(attempt)
                        continue

                    # 기타 에러
                    last_error = Exception(
                        f"GPT API error: {response.status_code} - {response.text}"
                    )
                    logger.warning(
                        "gpt_api_error",
                        model=model,
                        status=response.status_code,
                        attempt=attempt + 1,
                    )

                except httpx.TimeoutException as e:
                    last_error = e
                    logger.warning(
                        "gpt_timeout",
                        model=model,
                        attempt=attempt + 1,
                    )

                except Exception as e:
                    last_error = e
                    logger.error(
                        "gpt_unexpected_error",
                        model=model,
                        error=str(e),
                        attempt=attempt + 1,
                    )

                # 재시도 대기
                if attempt < self.config.max_retries - 1:
                    await self._wait_for_retry(attempt)

            # 다음 모델로 폴백
            logger.warning("gpt_model_fallback", from_model=model)

        # 모든 시도 실패
        raise last_error or Exception("GPT API 호출 실패")

    async def _wait_for_retry(self, attempt: int) -> None:
        """재시도 대기 (지수 백오프)"""
        import asyncio

        delay = self.config.retry_delay * (2 ** attempt)
        await asyncio.sleep(delay)

    async def chat_stream(
        self,
        messages: list[dict[str, str]],
        config: GenerationConfig | None = None,
    ) -> AsyncIterator[str]:
        """채팅 완성 (streaming) - 폴백에서는 미지원"""
        raise NotImplementedError("GPT 폴백은 스트리밍을 지원하지 않습니다")

    async def close(self) -> None:
        """리소스 정리"""
        await self.stop()
```

---

### 할당량 추적 서비스 (영구 저장 버전)

```python
# yeji-ai-server/ai/src/yeji_ai/services/fallback/quota_tracker.py

"""GPT 폴백 할당량 추적 (Redis/파일 기반)

프로덕션에서는 Redis를 사용하고, 개발 환경에서는 파일 기반으로 동작합니다.
"""

import json
from abc import ABC, abstractmethod
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger()


@dataclass
class QuotaConfig:
    """할당량 설정"""

    daily_eastern_quota: int = 50  # 동양 사주 일일 한도
    daily_western_quota: int = 50  # 서양 점성술 일일 한도
    daily_total_quota: int = 100   # 전체 일일 한도
    hourly_quota: int = 20         # 시간당 한도
    warning_threshold: float = 0.8  # 경고 임계값 (80%)


class QuotaTrackerBase(ABC):
    """할당량 추적 추상 클래스"""

    @abstractmethod
    async def can_use(self, fortune_type: str) -> tuple[bool, str]:
        """사용 가능 여부 확인"""
        pass

    @abstractmethod
    async def record_usage(self, fortune_type: str) -> None:
        """사용량 기록"""
        pass

    @abstractmethod
    async def get_stats(self) -> dict[str, Any]:
        """통계 조회"""
        pass


class InMemoryQuotaTracker(QuotaTrackerBase):
    """인메모리 할당량 추적 (개발용)"""

    def __init__(self, config: QuotaConfig):
        self.config = config
        self._daily_counts: Counter[str] = Counter()
        self._hourly_counts: Counter[str] = Counter()
        self._last_daily_reset = datetime.utcnow()
        self._last_hourly_reset = datetime.utcnow()

    def _reset_if_needed(self) -> None:
        """필요 시 카운터 리셋"""
        now = datetime.utcnow()

        if now.date() > self._last_daily_reset.date():
            self._daily_counts.clear()
            self._last_daily_reset = now
            logger.info("quota_daily_reset")

        if (now - self._last_hourly_reset).seconds >= 3600:
            self._hourly_counts.clear()
            self._last_hourly_reset = now
            logger.info("quota_hourly_reset")

    async def can_use(self, fortune_type: str) -> tuple[bool, str]:
        """사용 가능 여부 확인"""
        self._reset_if_needed()

        # 전체 일일 한도
        total_used = sum(self._daily_counts.values())
        if total_used >= self.config.daily_total_quota:
            return False, "daily_total_quota_exceeded"

        # 타입별 일일 한도
        type_limit = getattr(self.config, f"daily_{fortune_type}_quota", 50)
        if self._daily_counts[fortune_type] >= type_limit:
            return False, f"daily_{fortune_type}_quota_exceeded"

        # 시간당 한도
        hourly_used = sum(self._hourly_counts.values())
        if hourly_used >= self.config.hourly_quota:
            return False, "hourly_quota_exceeded"

        return True, ""

    async def record_usage(self, fortune_type: str) -> None:
        """사용량 기록"""
        self._reset_if_needed()
        self._daily_counts[fortune_type] += 1
        self._hourly_counts[fortune_type] += 1

        # 경고 로깅
        total_used = sum(self._daily_counts.values())
        usage_ratio = total_used / self.config.daily_total_quota

        if usage_ratio >= self.config.warning_threshold:
            logger.warning(
                "quota_warning",
                usage_ratio=round(usage_ratio * 100, 1),
                daily_used=total_used,
                daily_limit=self.config.daily_total_quota,
            )

    async def get_stats(self) -> dict[str, Any]:
        """통계 조회"""
        self._reset_if_needed()
        return {
            "daily": dict(self._daily_counts),
            "hourly": dict(self._hourly_counts),
            "daily_total_remaining": self.config.daily_total_quota - sum(self._daily_counts.values()),
            "hourly_remaining": self.config.hourly_quota - sum(self._hourly_counts.values()),
        }


class FileQuotaTracker(QuotaTrackerBase):
    """파일 기반 할당량 추적 (간단한 영구 저장)"""

    def __init__(self, config: QuotaConfig, file_path: str = "/tmp/yeji_gpt_quota.json"):
        self.config = config
        self.file_path = Path(file_path)
        self._load_data()

    def _load_data(self) -> None:
        """파일에서 데이터 로드"""
        if self.file_path.exists():
            try:
                data = json.loads(self.file_path.read_text())
                self._daily_counts = Counter(data.get("daily", {}))
                self._hourly_counts = Counter(data.get("hourly", {}))
                self._last_daily_reset = datetime.fromisoformat(
                    data.get("last_daily_reset", datetime.utcnow().isoformat())
                )
                self._last_hourly_reset = datetime.fromisoformat(
                    data.get("last_hourly_reset", datetime.utcnow().isoformat())
                )
            except Exception:
                self._init_counters()
        else:
            self._init_counters()

    def _init_counters(self) -> None:
        """카운터 초기화"""
        self._daily_counts = Counter()
        self._hourly_counts = Counter()
        self._last_daily_reset = datetime.utcnow()
        self._last_hourly_reset = datetime.utcnow()

    def _save_data(self) -> None:
        """파일에 데이터 저장"""
        data = {
            "daily": dict(self._daily_counts),
            "hourly": dict(self._hourly_counts),
            "last_daily_reset": self._last_daily_reset.isoformat(),
            "last_hourly_reset": self._last_hourly_reset.isoformat(),
        }
        self.file_path.write_text(json.dumps(data, indent=2))

    # can_use, record_usage, get_stats는 InMemoryQuotaTracker와 동일
    # _save_data() 호출만 추가

    async def can_use(self, fortune_type: str) -> tuple[bool, str]:
        # InMemoryQuotaTracker.can_use와 동일한 로직
        # 생략 (구현 시 복사)
        pass

    async def record_usage(self, fortune_type: str) -> None:
        # InMemoryQuotaTracker.record_usage와 동일 + _save_data() 호출
        pass

    async def get_stats(self) -> dict[str, Any]:
        # InMemoryQuotaTracker.get_stats와 동일
        pass
```

---

## 비용 최적화 전략

### 토큰 절감 기법

| 기법 | 절감률 | 설명 |
|------|--------|------|
| TypeScript 타입 → JSON 예시 대체 | ~50% | 구조만 전달 |
| 캐릭터 설정 생략 | ~10% | 폴백이므로 필수 아님 |
| 제약 조건 압축 | ~30% | 핵심만 마크다운으로 |
| `max_tokens` 제한 | 비용 절감 | 1500 토큰 제한 |

### 비용 시뮬레이션

```
예상 토큰 사용량 (호출당):
- 입력: ~450 토큰
- 출력: ~1000 토큰 (평균)
- 총: ~1450 토큰

gpt-4o-mini 기준 호출당 비용:
- 입력: 450 / 1M * $0.15 = $0.0000675
- 출력: 1000 / 1M * $0.60 = $0.0006
- 총: ~$0.00067/회

일일 비용 (100회 한도):
- 최대: $0.067/일 ≈ $2/월
```

### 비용 모니터링 메트릭

```python
# Prometheus 메트릭 예시
GPT_METRICS = {
    "yeji_gpt_calls_total": "GPT 호출 총 횟수",
    "yeji_gpt_calls_success": "GPT 호출 성공 횟수",
    "yeji_gpt_calls_failed": "GPT 호출 실패 횟수",
    "yeji_gpt_calls_quota_blocked": "할당량 초과로 차단된 횟수",
    "yeji_gpt_tokens_input_total": "입력 토큰 총 합계",
    "yeji_gpt_tokens_output_total": "출력 토큰 총 합계",
    "yeji_gpt_cost_estimate_usd": "추정 비용 (USD)",
    "yeji_gpt_quota_remaining": "남은 일일 할당량",
}
```

---

## 테스트 및 검증

### 단위 테스트

```python
# yeji-ai-server/ai/tests/test_gpt_provider.py

import pytest
from unittest.mock import AsyncMock, patch

from yeji_ai.providers.gpt import GPTConfig, GPTProvider, GPTQuotaExceededError


@pytest.fixture
def gpt_config() -> GPTConfig:
    return GPTConfig(
        api_key="test-api-key",
        daily_quota=10,
        hourly_quota=5,
    )


@pytest.fixture
def gpt_provider(gpt_config: GPTConfig) -> GPTProvider:
    return GPTProvider(gpt_config)


class TestGPTQuota:
    """할당량 테스트"""

    def test_can_use_within_quota(self, gpt_provider: GPTProvider) -> None:
        """할당량 내 호출 가능"""
        can_use, reason = gpt_provider.can_use()
        assert can_use is True
        assert reason == ""

    def test_can_use_daily_exceeded(self, gpt_provider: GPTProvider) -> None:
        """일일 할당량 초과"""
        gpt_provider._daily_count = 10  # 한도 도달
        can_use, reason = gpt_provider.can_use()
        assert can_use is False
        assert reason == "daily_quota_exceeded"

    def test_can_use_hourly_exceeded(self, gpt_provider: GPTProvider) -> None:
        """시간당 할당량 초과"""
        gpt_provider._hourly_count = 5  # 한도 도달
        can_use, reason = gpt_provider.can_use()
        assert can_use is False
        assert reason == "hourly_quota_exceeded"


class TestGPTChat:
    """채팅 API 테스트"""

    @pytest.mark.asyncio
    async def test_chat_success(self, gpt_provider: GPTProvider) -> None:
        """정상 채팅 응답"""
        mock_response = {
            "choices": [{"message": {"content": '{"element": "WOOD"}'}}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 50},
        }

        with patch.object(gpt_provider, "_get_http_client") as mock_client:
            mock_client.return_value.post = AsyncMock(
                return_value=AsyncMock(status_code=200, json=lambda: mock_response)
            )

            response = await gpt_provider.chat([{"role": "user", "content": "test"}])

            assert response.text == '{"element": "WOOD"}'
            assert gpt_provider._daily_count == 1

    @pytest.mark.asyncio
    async def test_chat_quota_exceeded(self, gpt_provider: GPTProvider) -> None:
        """할당량 초과 시 예외"""
        gpt_provider._daily_count = 10  # 한도 도달

        with pytest.raises(GPTQuotaExceededError) as exc_info:
            await gpt_provider.chat([{"role": "user", "content": "test"}])

        assert exc_info.value.quota_type == "daily_quota_exceeded"
```

### 통합 테스트 (수동)

```bash
# GPT 프롬프트 테스트 스크립트
# yeji-ai-server/ai/scripts/test_gpt_fallback.py

import asyncio
import os
from yeji_ai.providers.gpt import GPTConfig, GPTProvider
from yeji_ai.services.fallback.prompts import build_gpt_eastern_prompt

async def test_eastern():
    """동양 사주 GPT 폴백 테스트"""
    config = GPTConfig(api_key=os.environ["OPENAI_API_KEY"])
    provider = GPTProvider(config)
    await provider.start()

    system, user = build_gpt_eastern_prompt(
        birth_year=1990,
        birth_month=5,
        birth_day=15,
        birth_hour=14,
        gender="male",
    )

    response = await provider.chat([
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ])

    print("=== GPT 응답 ===")
    print(response.text)
    print(f"\n토큰: {response.usage}")
    print(f"레이턴시: {response.latency_ms:.2f}ms")

    await provider.stop()

if __name__ == "__main__":
    asyncio.run(test_eastern())
```

---

## 체크리스트

### 구현 전

- [ ] OpenAI API 키 발급
- [ ] 환경변수 설정 (`OPENAI_API_KEY`)
- [ ] gpt-4o-mini 모델 접근 권한 확인

### 구현 중

- [ ] `providers/gpt.py` 파일 생성
- [ ] `services/fallback/prompts.py` 파일 생성
- [ ] `services/fallback/quota_tracker.py` 파일 생성
- [ ] 단위 테스트 작성
- [ ] 통합 테스트 수행

### 배포 전

- [ ] 일일/시간당 할당량 결정
- [ ] 비용 알림 설정 (Slack)
- [ ] 모니터링 대시보드 구성

---

## 참조 문서

| 문서 | 경로 |
|------|------|
| 폴백 체인 설계 | `yeji-ai-server/ai/docs/design/llm-fallback-chain.md` |
| 기존 프롬프트 | `yeji-ai-server/ai/src/yeji_ai/prompts/fortune_prompts.py` |
| LLM 스키마 | `yeji-ai-server/ai/src/yeji_ai/models/llm_schemas.py` |
| Provider 인터페이스 | `yeji-ai-server/ai/src/yeji_ai/providers/base.py` |
| vLLM Provider 참조 | `yeji-ai-server/ai/src/yeji_ai/providers/vllm.py` |

---

> **Note**: 이 문서는 PoC 수준의 설계입니다. 프로덕션 적용 시 Redis 기반 할당량 추적, 상세 모니터링, A/B 테스트 등 추가 검토가 필요합니다.
