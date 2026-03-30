# L4 GPU 인텐트 모델 배포 아키텍처 설계

> **문서 버전**: v1.0
> **작성일**: 2026-01-30
> **작성자**: YEJI AI Team
> **상태**: 설계 완료

---

## 목차

1. [개요](#1-개요)
2. [L4 GPU 리소스 배분](#2-l4-gpu-리소스-배분)
3. [배포 옵션 비교](#3-배포-옵션-비교)
4. [모델 로딩 전략](#4-모델-로딩-전략)
5. [Docker 컨테이너 구성](#5-docker-컨테이너-구성)
6. [모니터링 및 알림](#6-모니터링-및-알림)
7. [구현 가이드](#7-구현-가이드)
8. [롤백 및 장애 대응](#8-롤백-및-장애-대응)
9. [참조 문서](#9-참조-문서)

---

## 1. 개요

### 1.1 목적

NVIDIA L4 GPU(24GB VRAM)에서 기존 yeji-8b-AWQ 모델과 함께 인텐트 필터 시스템(Prompt Guard + Intent Classifier)을 안정적으로 운영하기 위한 배포 아키텍처를 설계합니다.

### 1.2 배경

인텐트 필터 구현 계획서(`intent-filter-implementation-plan.md`)에 따라:

- **Prompt Guard**: Llama Prompt Guard 2 86M (악성 프롬프트 탐지)
- **Intent Classifier**: gte-multilingual-base (운세 의도 분류)

위 두 모델을 기존 vLLM 운영 환경에 추가 배포해야 합니다.

### 1.3 현재 아키텍처

```
┌─────────────────────────────────────────────────────────────────────┐
│                      L4 GPU (24GB VRAM)                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    vLLM Server (Port 8001)                   │   │
│  │  ┌─────────────────────────────────────────────────────┐    │   │
│  │  │           yeji-8b-AWQ (~5.5GB)                      │    │   │
│  │  └─────────────────────────────────────────────────────┘    │   │
│  │  ┌─────────────────────────────────────────────────────┐    │   │
│  │  │           KV Cache (~4-8GB, 동적)                    │    │   │
│  │  └─────────────────────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │               FastAPI Server (Port 8000)                     │   │
│  │                     (CPU Only)                               │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.4 목표 아키텍처

```
┌─────────────────────────────────────────────────────────────────────┐
│                      L4 GPU (24GB VRAM)                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    vLLM Server (Port 8001)                   │   │
│  │  ┌─────────────────────────────────────────────────────┐    │   │
│  │  │           yeji-8b-AWQ (~5.5GB)                      │    │   │
│  │  └─────────────────────────────────────────────────────┘    │   │
│  │  ┌─────────────────────────────────────────────────────┐    │   │
│  │  │           KV Cache (~4-6GB, 조정)                    │    │   │
│  │  └─────────────────────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │               FastAPI Server (Port 8000)                     │   │
│  │  ┌─────────────┐  ┌─────────────┐                           │   │
│  │  │ Guard 86M   │  │ Intent GTE  │                           │   │
│  │  │ (~0.35GB)   │  │ (~0.6GB)    │                           │   │
│  │  └─────────────┘  └─────────────┘                           │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. L4 GPU 리소스 배분

### 2.1 L4 GPU 스펙

| 항목 | 사양 |
|------|------|
| GPU 모델 | NVIDIA L4 |
| VRAM | 24GB GDDR6 |
| 메모리 대역폭 | 300 GB/s |
| FP16 성능 | 121 TFLOPS |
| INT8 성능 | 242 TOPS |
| TDP | 72W |

### 2.2 현재 VRAM 사용량

| 컴포넌트 | 모델/용도 | VRAM 사용량 | 비고 |
|----------|-----------|-------------|------|
| yeji-8b-AWQ | 메인 LLM | ~5.5GB | 4bit AWQ 양자화 |
| KV Cache | 추론 캐시 | ~4-8GB | 동시 요청 수에 따라 변동 |
| CUDA 오버헤드 | 시스템 | ~1GB | cuBLAS, cuDNN 등 |
| **합계 (현재)** | - | **~10.5-14.5GB** | 여유: 9.5-13.5GB |

### 2.3 추가 모델 VRAM 요구량

| 모델 | 파라미터 | 정밀도 | VRAM 사용량 | 비고 |
|------|----------|--------|-------------|------|
| Llama Prompt Guard 2 86M | 86M | FP16 | ~0.35GB | DeBERTa 기반 |
| gte-multilingual-base | 305M | FP16 | ~0.6GB | Alibaba NLP |
| **합계 (추가)** | - | - | **~0.95GB** | |

### 2.4 목표 VRAM 예산 분석

```
┌─────────────────────────────────────────────────────────────────────┐
│                    L4 GPU VRAM 할당 계획 (24GB)                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ████████████████████░░░░░░░░░░░░░░░░░░░░░░░░  yeji-8b-AWQ (5.5GB)  │
│  ░░░░░░░░░░░░░░░░░░░░████████████████░░░░░░░░  KV Cache (4-6GB)     │
│  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░██░░░░░░  Guard 86M (0.35GB)  │
│  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░██░░░░  Intent GTE (0.6GB)  │
│  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░██░░  CUDA (1GB)          │
│  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  여유 (10.5-12.5GB)  │
│                                                                      │
│  |-------|-------|-------|-------|-------|-------|                   │
│  0GB     4GB     8GB     12GB    16GB    20GB    24GB                │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.5 최종 VRAM 예산

| 컴포넌트 | 최소 | 최대 | 권장 |
|----------|------|------|------|
| yeji-8b-AWQ | 5.5GB | 5.5GB | 5.5GB |
| KV Cache | 4GB | 6GB | 5GB |
| Prompt Guard 86M | 0.35GB | 0.35GB | 0.35GB |
| Intent Classifier | 0.6GB | 0.6GB | 0.6GB |
| CUDA 오버헤드 | 1GB | 1GB | 1GB |
| **합계** | **11.45GB** | **13.45GB** | **12.45GB** |
| **여유 공간** | **12.55GB** | **10.55GB** | **11.55GB** |

**결론**: L4 24GB에서 모든 모델 운영 시 **충분한 여유 공간**(10-12GB) 확보 가능.

### 2.6 KV Cache 조정 가이드

기존 KV Cache가 8GB까지 사용하던 경우, 안정적 운영을 위해 조정이 필요합니다.

```python
# vLLM 설정 예시
# 기존: gpu_memory_utilization=0.9 (약 21.6GB 사용)
# 변경: gpu_memory_utilization=0.85 (약 20.4GB 사용)

vllm_config = {
    "model": "tellang/yeji-8b-rslora-v7-AWQ",
    "gpu_memory_utilization": 0.85,  # 조정
    "max_model_len": 4096,           # 컨텍스트 길이 유지
    "quantization": "awq",
}
```

**메모리 여유 계산**:
- 총 VRAM: 24GB
- vLLM 할당 (0.85): ~20.4GB
- Guard + Intent: ~1GB
- 남은 여유: ~2.6GB (버퍼)

---

## 3. 배포 옵션 비교

### 3.1 Option A: 단일 프로세스 통합 (권장)

```
┌──────────────────────────────────────────────────────────────────┐
│                    FastAPI Process (단일)                          │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    GPU Memory 공유                          │ │
│  │                                                            │ │
│  │  ┌──────────┐   ┌──────────┐   ┌─────────────────────┐    │ │
│  │  │  Guard   │   │  Intent  │   │  vLLM (외부 서버)   │    │ │
│  │  │  Model   │   │  Model   │   │  HTTP 클라이언트    │    │ │
│  │  │ (0.35GB) │   │ (0.6GB)  │   │                     │    │ │
│  │  └──────────┘   └──────────┘   └─────────────────────┘    │ │
│  │       │               │                   │                │ │
│  │       └───────────────┴───────────────────┘                │ │
│  │                       │                                    │ │
│  │              FilterPipeline                                │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  Request → Guard → Intent → vLLM → Response                     │
└──────────────────────────────────────────────────────────────────┘
```

**구현 방식**:

```python
# yeji_ai/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작 시 모델 로드, 종료 시 정리"""
    import torch

    # 1. Guard 모델 로드 (GPU)
    app.state.guard_model = await load_prompt_guard(
        model_id="meta-llama/Llama-Prompt-Guard-2-86M",
        device="cuda:0",
        torch_dtype=torch.float16,
    )

    # 2. Intent 분류기 로드 (GPU)
    app.state.intent_classifier = await load_intent_classifier(
        model_id="Alibaba-NLP/gte-multilingual-base",
        device="cuda:0",
    )

    # 3. vLLM 클라이언트 (외부 서버 연결)
    app.state.vllm_client = VLLMProvider(settings)

    logger.info(
        "models_loaded",
        guard_vram_mb=get_model_vram(app.state.guard_model),
        intent_vram_mb=get_model_vram(app.state.intent_classifier),
    )

    yield

    # 정리
    del app.state.guard_model
    del app.state.intent_classifier
    torch.cuda.empty_cache()

app = FastAPI(lifespan=lifespan)
```

**장점**:

| 항목 | 설명 |
|------|------|
| 메모리 효율 | GPU 메모리 단일 프로세스 공유, 중복 할당 없음 |
| 레이턴시 최소화 | 프로세스 간 통신(IPC) 오버헤드 없음 |
| 배포 단순화 | 단일 컨테이너로 배포 및 관리 |
| 장애 관리 | 단일 장애점이지만 피처 플래그로 개별 비활성화 가능 |

**단점**:

| 항목 | 설명 | 완화 방안 |
|------|------|----------|
| 단일 장애점 | 프로세스 크래시 시 전체 서비스 중단 | 헬스체크 + 자동 재시작 |
| 모델 업데이트 | 모델 변경 시 전체 재시작 필요 | 무중단 배포(Rolling Update) |
| 디버깅 복잡 | 문제 원인 파악 어려움 | 상세 로깅 + 메트릭 분리 |

### 3.2 Option B: 멀티 프로세스 분리

```
┌─────────────────────────────────────────────────────────────────────┐
│                          L4 GPU 서버                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐     │
│  │  Guard Service  │  │ Intent Service  │  │  vLLM Service   │     │
│  │   Port: 8002    │  │   Port: 8003    │  │   Port: 8001    │     │
│  │   (0.35GB)      │  │   (0.6GB)       │  │   (~11GB)       │     │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘     │
│           │                    │                    │               │
│           └────────────────────┼────────────────────┘               │
│                                │                                    │
│                    ┌───────────┴───────────┐                        │
│                    │   FastAPI Gateway     │                        │
│                    │     Port: 8000        │                        │
│                    └───────────────────────┘                        │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

**장점**:

| 항목 | 설명 |
|------|------|
| 장애 격리 | 각 서비스 독립 운영, 부분 장애 시 폴백 가능 |
| 독립 스케일링 | 특정 서비스만 리소스 조정 가능 |
| 독립 업데이트 | 개별 모델/서비스 무중단 업데이트 |

**단점**:

| 항목 | 설명 |
|------|------|
| 네트워크 레이턴시 | HTTP 호출 오버헤드 (각 ~5-10ms) |
| VRAM 중복 | 각 프로세스별 CUDA 컨텍스트 (각 ~0.5GB) |
| 운영 복잡도 | 3개 서비스 모니터링/관리 필요 |
| 리소스 낭비 | 프로세스별 메모리 오버헤드 |

### 3.3 권장안: Option A (단일 프로세스 통합)

**선정 이유**:

1. **VRAM 효율성**: 단일 CUDA 컨텍스트로 메모리 오버헤드 최소화
2. **레이턴시 최적화**: Guard(~100ms) + Intent(~15ms) 추가가 전체 응답 시간에 미치는 영향 최소화
3. **운영 단순성**: Jenkins 파이프라인 변경 최소화
4. **서비스 규모**: YEJI 서비스 트래픽 수준에서 복잡한 마이크로서비스 불필요
5. **피처 플래그**: 개별 컴포넌트 비활성화로 장애 격리 가능

**리스크 완화**:

| 리스크 | 완화 방안 |
|--------|----------|
| 전체 서비스 중단 | 헬스체크 + Docker 재시작 정책 |
| 모델 로드 실패 | Lazy Loading + 그레이스풀 디그레이드 |
| OOM 발생 | VRAM 모니터링 + 알림 |

---

## 4. 모델 로딩 전략

### 4.1 로딩 방식 비교

| 방식 | 시작 시간 | 첫 요청 지연 | 메모리 관리 | 권장도 |
|------|----------|-------------|------------|--------|
| Eager Loading | 느림 (30-60s) | 없음 | 예측 가능 | **권장** |
| Lazy Loading | 빠름 (5-10s) | 있음 (첫 요청 시 로드) | 필요시 로드 | 폴백용 |
| Hybrid | 중간 | Guard만 지연 | 유연 | 대안 |

### 4.2 권장: Eager Loading (사전 로드)

**이유**:
1. **예측 가능한 응답 시간**: 첫 요청도 일관된 레이턴시
2. **헬스체크 명확성**: 모든 모델 로드 완료 후 Ready 상태
3. **OOM 조기 발견**: 시작 시점에 메모리 부족 감지

**구현**:

```python
# yeji_ai/services/filter/loader.py

import torch
import structlog
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from sentence_transformers import SentenceTransformer

logger = structlog.get_logger()


class ModelLoader:
    """모델 로더 (Eager Loading)"""

    def __init__(self, device: str = "cuda:0"):
        self.device = device
        self.torch_dtype = torch.float16

    async def load_prompt_guard(
        self,
        model_id: str = "meta-llama/Llama-Prompt-Guard-2-86M",
    ) -> tuple[AutoModelForSequenceClassification, AutoTokenizer]:
        """
        Prompt Guard 모델 로드

        Returns:
            (model, tokenizer) 튜플
        """
        logger.info("loading_prompt_guard", model_id=model_id, device=self.device)

        tokenizer = AutoTokenizer.from_pretrained(model_id)
        model = AutoModelForSequenceClassification.from_pretrained(
            model_id,
            torch_dtype=self.torch_dtype,
            device_map=self.device,
        )
        model.eval()

        vram_mb = self._get_model_vram_mb(model)
        logger.info("prompt_guard_loaded", vram_mb=vram_mb)

        return model, tokenizer

    async def load_intent_classifier(
        self,
        model_id: str = "Alibaba-NLP/gte-multilingual-base",
    ) -> SentenceTransformer:
        """
        Intent 분류기(임베딩 모델) 로드

        Returns:
            SentenceTransformer 모델
        """
        logger.info("loading_intent_classifier", model_id=model_id, device=self.device)

        model = SentenceTransformer(
            model_id,
            device=self.device,
        )

        vram_mb = self._estimate_st_vram_mb(model)
        logger.info("intent_classifier_loaded", vram_mb=vram_mb)

        return model

    def _get_model_vram_mb(self, model) -> float:
        """모델 VRAM 사용량 계산 (MB)"""
        param_size = sum(p.numel() * p.element_size() for p in model.parameters())
        buffer_size = sum(b.numel() * b.element_size() for b in model.buffers())
        return (param_size + buffer_size) / (1024 * 1024)

    def _estimate_st_vram_mb(self, model: SentenceTransformer) -> float:
        """SentenceTransformer VRAM 추정"""
        # 대략적인 추정 (모델 크기 기반)
        return 600.0  # gte-multilingual-base 기준
```

### 4.3 메모리 최적화 옵션

#### 4.3.1 FP16 (Half Precision) - 기본 권장

```python
# FP16 로드 (기본)
model = AutoModelForSequenceClassification.from_pretrained(
    model_id,
    torch_dtype=torch.float16,  # FP32 대비 50% 메모리 절감
    device_map="cuda:0",
)
```

**메모리 비교**:

| 정밀도 | Prompt Guard 86M | Intent 305M |
|--------|-----------------|-------------|
| FP32 | ~0.7GB | ~1.2GB |
| FP16 | ~0.35GB | ~0.6GB |
| INT8 | ~0.18GB | ~0.3GB |

#### 4.3.2 INT8 양자화 (추가 최적화)

메모리가 부족한 경우에만 적용:

```python
# INT8 양자화 (선택적)
from transformers import BitsAndBytesConfig

quantization_config = BitsAndBytesConfig(
    load_in_8bit=True,
    llm_int8_threshold=6.0,
)

model = AutoModelForSequenceClassification.from_pretrained(
    model_id,
    quantization_config=quantization_config,
    device_map="cuda:0",
)
```

**주의사항**:
- INT8은 정확도 약간 저하 가능
- bitsandbytes 라이브러리 추가 의존성
- 현재 VRAM 여유 충분하므로 FP16 권장

### 4.4 로딩 실패 처리

```python
# yeji_ai/main.py

@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작 시 모델 로드"""
    loader = ModelLoader(device="cuda:0")
    settings = get_settings()

    # Guard 로드 시도
    try:
        if settings.filter.enable_guard:
            app.state.guard_model, app.state.guard_tokenizer = (
                await loader.load_prompt_guard()
            )
        else:
            app.state.guard_model = None
            app.state.guard_tokenizer = None
            logger.info("guard_disabled_by_config")
    except Exception as e:
        logger.error("guard_load_failed", error=str(e))
        if settings.filter.guard_required:
            raise  # 필수인 경우 시작 실패
        app.state.guard_model = None
        app.state.guard_tokenizer = None

    # Intent 로드 시도
    try:
        if settings.filter.enable_intent:
            app.state.intent_classifier = await loader.load_intent_classifier()
        else:
            app.state.intent_classifier = None
            logger.info("intent_disabled_by_config")
    except Exception as e:
        logger.error("intent_load_failed", error=str(e))
        if settings.filter.intent_required:
            raise
        app.state.intent_classifier = None

    # VRAM 상태 로깅
    log_gpu_memory_status()

    yield

    # 정리
    cleanup_models(app)
    torch.cuda.empty_cache()


def log_gpu_memory_status():
    """GPU 메모리 상태 로깅"""
    import torch

    if torch.cuda.is_available():
        allocated = torch.cuda.memory_allocated() / (1024 ** 3)
        reserved = torch.cuda.memory_reserved() / (1024 ** 3)
        total = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)

        logger.info(
            "gpu_memory_status",
            allocated_gb=round(allocated, 2),
            reserved_gb=round(reserved, 2),
            total_gb=round(total, 2),
            available_gb=round(total - reserved, 2),
        )
```

---

## 5. Docker 컨테이너 구성

### 5.1 Dockerfile 수정

```dockerfile
# yeji-ai-server/ai/Dockerfile

FROM python:3.11-slim AS base

# CUDA 런타임 (L4 GPU용)
FROM nvidia/cuda:12.1-runtime-ubuntu22.04 AS runtime

# Python 설치
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 의존성 설치
COPY requirements.txt .

# 기존 의존성 + 새 의존성 설치
RUN pip install --no-cache-dir -r requirements.txt

# 추가 의존성 (인텐트 필터용)
RUN pip install --no-cache-dir \
    transformers>=4.40.0 \
    sentence-transformers>=2.7.0 \
    accelerate>=0.30.0 \
    safetensors>=0.4.0

# 소스 코드 복사
COPY src/ ./src/

# 환경 변수
ENV PYTHONPATH=/app/src
ENV CUDA_VISIBLE_DEVICES=0

# 모델 캐시 디렉토리
ENV HF_HOME=/app/.cache/huggingface
ENV TRANSFORMERS_CACHE=/app/.cache/transformers
ENV SENTENCE_TRANSFORMERS_HOME=/app/.cache/sentence_transformers

# 볼륨 마운트 포인트 (모델 캐시)
VOLUME ["/app/.cache"]

# 포트
EXPOSE 8000

# 헬스체크
HEALTHCHECK --interval=30s --timeout=30s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:8000/v1/health/ready || exit 1

# 시작 명령
CMD ["uvicorn", "yeji_ai.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 5.2 requirements.txt 추가

```text
# 기존 의존성 유지...

# === 인텐트 필터 의존성 (신규) ===
transformers>=4.40.0
sentence-transformers>=2.7.0
accelerate>=0.30.0
safetensors>=0.4.0

# CUDA 지원 (선택적, nvidia 이미지 사용 시 불필요)
# torch>=2.2.0+cu121
```

### 5.3 docker-compose.yml

```yaml
# yeji-ai-server/docker-compose.yml

version: "3.8"

services:
  yeji-ai:
    build:
      context: ./ai
      dockerfile: Dockerfile
    image: yeji-ai:${BUILD_NUMBER:-latest}
    container_name: yeji-ai-prod
    restart: unless-stopped

    # GPU 할당
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

    ports:
      - "8000:8000"

    environment:
      # 기존 환경변수
      - VLLM_BASE_URL=${VLLM_BASE_URL:-http://localhost:8001}
      - VLLM_MODEL=${VLLM_MODEL:-tellang/yeji-8b-rslora-v7-AWQ}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}

      # 인텐트 필터 환경변수 (신규)
      - FILTER_ENABLED=${FILTER_ENABLED:-true}
      - GUARD_ENABLED=${GUARD_ENABLED:-true}
      - GUARD_MODEL=${GUARD_MODEL:-meta-llama/Llama-Prompt-Guard-2-86M}
      - GUARD_THRESHOLD=${GUARD_THRESHOLD:-0.8}
      - INTENT_ENABLED=${INTENT_ENABLED:-true}
      - INTENT_MODEL=${INTENT_MODEL:-Alibaba-NLP/gte-multilingual-base}
      - INTENT_CONFIDENCE_THRESHOLD=${INTENT_CONFIDENCE_THRESHOLD:-0.7}

      # 피처 플래그
      - GUARD_MODE=${GUARD_MODE:-block}
      - INTENT_MODE=${INTENT_MODE:-block}

    volumes:
      # 모델 캐시 (컨테이너 재시작 시 재다운로드 방지)
      - huggingface_cache:/app/.cache/huggingface
      - transformers_cache:/app/.cache/transformers
      - sentence_transformers_cache:/app/.cache/sentence_transformers

    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/v1/health/ready"]
      interval: 30s
      timeout: 30s
      retries: 3
      start_period: 120s  # 모델 로딩 시간 고려

    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "3"

volumes:
  huggingface_cache:
  transformers_cache:
  sentence_transformers_cache:
```

### 5.4 환경 변수 설정

```bash
# .env.example (추가)

# === 인텐트 필터 설정 ===

# 전체 필터 활성화
FILTER_ENABLED=true

# Guard 설정
GUARD_ENABLED=true
GUARD_MODEL=meta-llama/Llama-Prompt-Guard-2-86M
GUARD_THRESHOLD=0.8
GUARD_MODE=block  # block, log_only, shadow

# Intent 설정
INTENT_ENABLED=true
INTENT_MODEL=Alibaba-NLP/gte-multilingual-base
INTENT_CONFIDENCE_THRESHOLD=0.7
INTENT_MODE=block  # block, log_only, shadow

# 폴백 설정
GUARD_FALLBACK_ALLOW=true
INTENT_FALLBACK_CATEGORY=fortune_general

# 모델 로드 필수 여부 (false면 로드 실패 시에도 서비스 시작)
GUARD_REQUIRED=false
INTENT_REQUIRED=false
```

### 5.5 헬스체크 확장

```python
# yeji_ai/api/health.py

from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter(prefix="/v1/health", tags=["health"])


class HealthStatus(BaseModel):
    """헬스 상태"""

    status: str
    vllm: str
    guard: str
    intent: str
    gpu_memory_gb: float | None = None


class ReadinessStatus(BaseModel):
    """준비 상태"""

    ready: bool
    components: dict[str, bool]


@router.get("/live")
async def liveness() -> dict[str, str]:
    """Liveness probe - 프로세스 생존 여부"""
    return {"status": "alive"}


@router.get("/ready")
async def readiness(request: Request) -> ReadinessStatus:
    """
    Readiness probe - 서비스 준비 상태

    모든 필수 컴포넌트가 로드되어야 ready=True
    """
    components = {}

    # vLLM 연결 확인
    try:
        vllm_client = request.app.state.vllm_client
        await vllm_client.health_check()
        components["vllm"] = True
    except Exception:
        components["vllm"] = False

    # Guard 모델 확인
    guard_model = getattr(request.app.state, "guard_model", None)
    guard_enabled = request.app.state.settings.filter.enable_guard
    if guard_enabled:
        components["guard"] = guard_model is not None
    else:
        components["guard"] = True  # 비활성화면 무조건 True

    # Intent 모델 확인
    intent_classifier = getattr(request.app.state, "intent_classifier", None)
    intent_enabled = request.app.state.settings.filter.enable_intent
    if intent_enabled:
        components["intent"] = intent_classifier is not None
    else:
        components["intent"] = True

    # 전체 준비 상태
    ready = all(components.values())

    return ReadinessStatus(ready=ready, components=components)


@router.get("/status")
async def detailed_status(request: Request) -> HealthStatus:
    """상세 헬스 상태"""
    import torch

    # vLLM 상태
    try:
        await request.app.state.vllm_client.health_check()
        vllm_status = "healthy"
    except Exception as e:
        vllm_status = f"unhealthy: {str(e)}"

    # Guard 상태
    guard_model = getattr(request.app.state, "guard_model", None)
    guard_status = "loaded" if guard_model else "not_loaded"

    # Intent 상태
    intent_classifier = getattr(request.app.state, "intent_classifier", None)
    intent_status = "loaded" if intent_classifier else "not_loaded"

    # GPU 메모리
    gpu_memory = None
    if torch.cuda.is_available():
        gpu_memory = round(
            torch.cuda.memory_allocated() / (1024 ** 3), 2
        )

    return HealthStatus(
        status="healthy" if vllm_status == "healthy" else "degraded",
        vllm=vllm_status,
        guard=guard_status,
        intent=intent_status,
        gpu_memory_gb=gpu_memory,
    )
```

---

## 6. 모니터링 및 알림

### 6.1 GPU 메모리 모니터링

#### 6.1.1 메트릭 수집

```python
# yeji_ai/services/monitoring/gpu_monitor.py

import torch
import structlog
from dataclasses import dataclass
from typing import Callable

logger = structlog.get_logger()


@dataclass
class GPUMemoryMetrics:
    """GPU 메모리 메트릭"""

    total_gb: float
    allocated_gb: float
    reserved_gb: float
    free_gb: float
    utilization_percent: float


class GPUMonitor:
    """GPU 메모리 모니터"""

    def __init__(
        self,
        warning_threshold: float = 0.85,
        critical_threshold: float = 0.95,
    ):
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self._alert_callbacks: list[Callable] = []

    def get_metrics(self) -> GPUMemoryMetrics | None:
        """현재 GPU 메모리 메트릭 조회"""
        if not torch.cuda.is_available():
            return None

        total = torch.cuda.get_device_properties(0).total_memory
        allocated = torch.cuda.memory_allocated()
        reserved = torch.cuda.memory_reserved()

        total_gb = total / (1024 ** 3)
        allocated_gb = allocated / (1024 ** 3)
        reserved_gb = reserved / (1024 ** 3)
        free_gb = total_gb - reserved_gb
        utilization = reserved / total

        return GPUMemoryMetrics(
            total_gb=round(total_gb, 2),
            allocated_gb=round(allocated_gb, 2),
            reserved_gb=round(reserved_gb, 2),
            free_gb=round(free_gb, 2),
            utilization_percent=round(utilization * 100, 2),
        )

    def check_and_alert(self) -> None:
        """메모리 체크 및 알림 발송"""
        metrics = self.get_metrics()
        if not metrics:
            return

        utilization = metrics.utilization_percent / 100

        if utilization >= self.critical_threshold:
            logger.critical(
                "gpu_memory_critical",
                utilization_percent=metrics.utilization_percent,
                free_gb=metrics.free_gb,
            )
            self._trigger_alert("critical", metrics)

        elif utilization >= self.warning_threshold:
            logger.warning(
                "gpu_memory_warning",
                utilization_percent=metrics.utilization_percent,
                free_gb=metrics.free_gb,
            )
            self._trigger_alert("warning", metrics)

    def register_alert_callback(self, callback: Callable) -> None:
        """알림 콜백 등록"""
        self._alert_callbacks.append(callback)

    def _trigger_alert(self, level: str, metrics: GPUMemoryMetrics) -> None:
        """알림 트리거"""
        for callback in self._alert_callbacks:
            try:
                callback(level, metrics)
            except Exception as e:
                logger.error("alert_callback_failed", error=str(e))
```

#### 6.1.2 Prometheus 메트릭

```python
# yeji_ai/services/monitoring/prometheus_metrics.py

from prometheus_client import Gauge, Counter, Histogram

# GPU 메트릭
GPU_MEMORY_TOTAL = Gauge(
    "yeji_gpu_memory_total_bytes",
    "GPU 총 메모리 (bytes)",
)
GPU_MEMORY_ALLOCATED = Gauge(
    "yeji_gpu_memory_allocated_bytes",
    "GPU 할당된 메모리 (bytes)",
)
GPU_MEMORY_RESERVED = Gauge(
    "yeji_gpu_memory_reserved_bytes",
    "GPU 예약된 메모리 (bytes)",
)
GPU_MEMORY_UTILIZATION = Gauge(
    "yeji_gpu_memory_utilization_ratio",
    "GPU 메모리 사용률 (0-1)",
)

# 모델 로드 메트릭
MODEL_LOAD_TIME = Histogram(
    "yeji_model_load_seconds",
    "모델 로드 시간",
    ["model_type"],  # guard, intent
    buckets=[1, 5, 10, 30, 60, 120],
)
MODEL_LOAD_SUCCESS = Counter(
    "yeji_model_load_success_total",
    "모델 로드 성공 횟수",
    ["model_type"],
)
MODEL_LOAD_FAILURE = Counter(
    "yeji_model_load_failure_total",
    "모델 로드 실패 횟수",
    ["model_type"],
)

# 필터 메트릭
GUARD_REQUESTS = Counter(
    "yeji_guard_requests_total",
    "Guard 요청 총 횟수",
    ["result"],  # pass, block, error
)
GUARD_LATENCY = Histogram(
    "yeji_guard_latency_seconds",
    "Guard 처리 시간",
    buckets=[0.01, 0.05, 0.1, 0.2, 0.5, 1.0],
)
INTENT_REQUESTS = Counter(
    "yeji_intent_requests_total",
    "Intent 분류 요청 총 횟수",
    ["intent"],  # fortune_general, out_of_domain, etc.
)
INTENT_LATENCY = Histogram(
    "yeji_intent_latency_seconds",
    "Intent 분류 처리 시간",
    buckets=[0.005, 0.01, 0.02, 0.05, 0.1],
)


def update_gpu_metrics(monitor: "GPUMonitor") -> None:
    """GPU 메트릭 업데이트"""
    metrics = monitor.get_metrics()
    if metrics:
        GPU_MEMORY_TOTAL.set(metrics.total_gb * (1024 ** 3))
        GPU_MEMORY_ALLOCATED.set(metrics.allocated_gb * (1024 ** 3))
        GPU_MEMORY_RESERVED.set(metrics.reserved_gb * (1024 ** 3))
        GPU_MEMORY_UTILIZATION.set(metrics.utilization_percent / 100)
```

### 6.2 알림 설정

#### 6.2.1 알림 조건

| 조건 | 레벨 | 알림 채널 | 자동 액션 |
|------|------|----------|----------|
| GPU 메모리 > 85% | WARNING | Slack | - |
| GPU 메모리 > 95% | CRITICAL | Slack + PagerDuty | 알림 전송 |
| Guard 로드 실패 | ERROR | Slack | 피처 플래그 비활성화 |
| Intent 로드 실패 | ERROR | Slack | 피처 플래그 비활성화 |
| Guard 오탐률 > 10% | WARNING | Slack | - |
| Intent 오분류율 > 20% | WARNING | Slack | - |
| OOM 발생 | CRITICAL | Slack + PagerDuty | 컨테이너 재시작 |

#### 6.2.2 Slack 알림 구현

```python
# yeji_ai/services/monitoring/alerting.py

import httpx
import structlog
from dataclasses import dataclass
from typing import Literal

logger = structlog.get_logger()


@dataclass
class AlertConfig:
    """알림 설정"""

    slack_webhook_url: str
    pagerduty_routing_key: str | None = None
    environment: str = "production"


class AlertService:
    """알림 서비스"""

    def __init__(self, config: AlertConfig):
        self.config = config
        self._client = httpx.AsyncClient(timeout=10.0)

    async def send_gpu_memory_alert(
        self,
        level: Literal["warning", "critical"],
        utilization_percent: float,
        free_gb: float,
    ) -> None:
        """GPU 메모리 알림 전송"""
        emoji = ":warning:" if level == "warning" else ":rotating_light:"
        color = "#FFA500" if level == "warning" else "#FF0000"

        message = {
            "attachments": [
                {
                    "color": color,
                    "title": f"{emoji} GPU Memory Alert ({level.upper()})",
                    "fields": [
                        {
                            "title": "Environment",
                            "value": self.config.environment,
                            "short": True,
                        },
                        {
                            "title": "Utilization",
                            "value": f"{utilization_percent:.1f}%",
                            "short": True,
                        },
                        {
                            "title": "Free Memory",
                            "value": f"{free_gb:.2f} GB",
                            "short": True,
                        },
                    ],
                    "footer": "YEJI AI Server",
                    "ts": int(time.time()),
                }
            ]
        }

        await self._send_slack(message)

        if level == "critical" and self.config.pagerduty_routing_key:
            await self._send_pagerduty(
                summary=f"GPU Memory Critical: {utilization_percent:.1f}%",
                severity="critical",
            )

    async def send_model_load_alert(
        self,
        model_type: str,
        success: bool,
        error: str | None = None,
    ) -> None:
        """모델 로드 알림 전송"""
        if success:
            emoji = ":white_check_mark:"
            color = "#36A64F"
            title = f"{emoji} Model Loaded: {model_type}"
        else:
            emoji = ":x:"
            color = "#FF0000"
            title = f"{emoji} Model Load Failed: {model_type}"

        message = {
            "attachments": [
                {
                    "color": color,
                    "title": title,
                    "fields": [
                        {
                            "title": "Environment",
                            "value": self.config.environment,
                            "short": True,
                        },
                        {
                            "title": "Status",
                            "value": "Success" if success else "Failed",
                            "short": True,
                        },
                    ],
                    "footer": "YEJI AI Server",
                }
            ]
        }

        if error:
            message["attachments"][0]["fields"].append({
                "title": "Error",
                "value": f"```{error}```",
                "short": False,
            })

        await self._send_slack(message)

    async def _send_slack(self, message: dict) -> None:
        """Slack 웹훅 전송"""
        try:
            response = await self._client.post(
                self.config.slack_webhook_url,
                json=message,
            )
            response.raise_for_status()
        except Exception as e:
            logger.error("slack_alert_failed", error=str(e))

    async def _send_pagerduty(self, summary: str, severity: str) -> None:
        """PagerDuty 알림 전송"""
        # PagerDuty Events API v2 구현
        pass
```

### 6.3 Grafana 대시보드

```json
{
  "dashboard": {
    "title": "YEJI AI - Intent Filter Monitoring",
    "panels": [
      {
        "title": "GPU Memory Usage",
        "type": "gauge",
        "targets": [
          {
            "expr": "yeji_gpu_memory_utilization_ratio * 100"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "thresholds": {
              "steps": [
                {"value": 0, "color": "green"},
                {"value": 70, "color": "yellow"},
                {"value": 85, "color": "orange"},
                {"value": 95, "color": "red"}
              ]
            },
            "max": 100,
            "unit": "percent"
          }
        }
      },
      {
        "title": "Guard Latency (P95)",
        "type": "stat",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, sum(rate(yeji_guard_latency_seconds_bucket[5m])) by (le))"
          }
        ]
      },
      {
        "title": "Intent Classification Distribution",
        "type": "piechart",
        "targets": [
          {
            "expr": "sum(increase(yeji_intent_requests_total[1h])) by (intent)"
          }
        ]
      },
      {
        "title": "Guard Block Rate",
        "type": "timeseries",
        "targets": [
          {
            "expr": "sum(rate(yeji_guard_requests_total{result=\"block\"}[5m])) / sum(rate(yeji_guard_requests_total[5m])) * 100"
          }
        ]
      }
    ]
  }
}
```

---

## 7. 구현 가이드

### 7.1 파일 구조

```
yeji-ai-server/ai/src/yeji_ai/
├── main.py                           # 수정: lifespan에서 모델 로드
├── config.py                         # 수정: FilterSettings 추가
├── api/
│   ├── health.py                     # 수정: 헬스체크 확장
│   └── dependencies.py               # 신규: 의존성 주입
├── models/
│   ├── filter.py                     # 신규: 필터 데이터 모델
│   └── enums/
│       └── intent.py                 # 신규: 인텐트 Enum
├── services/
│   ├── filter/                       # 신규: 필터 모듈
│   │   ├── __init__.py
│   │   ├── loader.py                 # 모델 로더
│   │   ├── guard.py                  # PromptGuardService
│   │   ├── intent.py                 # IntentClassifierService
│   │   └── pipeline.py               # FilterPipeline
│   └── monitoring/                   # 신규: 모니터링 모듈
│       ├── __init__.py
│       ├── gpu_monitor.py            # GPU 모니터링
│       ├── prometheus_metrics.py     # Prometheus 메트릭
│       └── alerting.py               # 알림 서비스
└── data/
    └── intents.yaml                  # 신규: 인텐트 예시 데이터
```

### 7.2 구현 순서

#### Phase 1: 기반 구축 (Day 1-2)

| Task | 파일 | 설명 |
|------|------|------|
| 설정 확장 | `config.py` | `FilterSettings` 추가 |
| 데이터 모델 | `models/filter.py` | `GuardResult`, `IntentResult` |
| 모델 로더 | `services/filter/loader.py` | FP16 로딩 구현 |

#### Phase 2: Guard 구현 (Day 3-4)

| Task | 파일 | 설명 |
|------|------|------|
| Guard 서비스 | `services/filter/guard.py` | 악성 탐지 로직 |
| 단위 테스트 | `tests/test_guard.py` | 탐지 정확도 테스트 |
| 헬스체크 | `api/health.py` | Guard 상태 포함 |

#### Phase 3: Intent 구현 (Day 5-6)

| Task | 파일 | 설명 |
|------|------|------|
| Intent 서비스 | `services/filter/intent.py` | 의도 분류 로직 |
| 예시 데이터 | `data/intents.yaml` | 인텐트별 예시 |
| 단위 테스트 | `tests/test_intent.py` | 분류 정확도 테스트 |

#### Phase 4: 통합 및 모니터링 (Day 7-8)

| Task | 파일 | 설명 |
|------|------|------|
| 파이프라인 | `services/filter/pipeline.py` | Guard → Intent 체인 |
| lifespan 수정 | `main.py` | 앱 시작 시 로드 |
| 모니터링 | `services/monitoring/` | GPU/메트릭/알림 |

#### Phase 5: 배포 (Day 9-10)

| Task | 파일 | 설명 |
|------|------|------|
| Dockerfile | `Dockerfile` | 의존성 추가 |
| docker-compose | `docker-compose.yml` | 환경변수/볼륨 |
| Jenkins | `Jenkinsfile` | 파이프라인 업데이트 |

### 7.3 설정 확장 상세

```python
# yeji_ai/config.py

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal


class FilterSettings(BaseModel):
    """인텐트 필터 설정"""

    # 전체 활성화
    enabled: bool = True

    # Guard 설정
    enable_guard: bool = True
    guard_model: str = "meta-llama/Llama-Prompt-Guard-2-86M"
    guard_threshold: float = 0.8
    guard_timeout: float = 1.0
    guard_mode: Literal["block", "log_only", "shadow"] = "block"
    guard_required: bool = False  # 로드 실패 시 서비스 시작 여부

    # Intent 설정
    enable_intent: bool = True
    intent_model: str = "Alibaba-NLP/gte-multilingual-base"
    intent_confidence_threshold: float = 0.7
    intent_timeout: float = 0.5
    intent_mode: Literal["block", "log_only", "shadow"] = "block"
    intent_required: bool = False

    # 폴백 설정
    guard_fallback_allow: bool = True
    intent_fallback_category: str = "fortune_general"


class MonitoringSettings(BaseModel):
    """모니터링 설정"""

    # GPU 메모리 알림
    gpu_memory_warning_threshold: float = 0.85
    gpu_memory_critical_threshold: float = 0.95

    # 알림 설정
    slack_webhook_url: str = ""
    pagerduty_routing_key: str = ""
    environment: str = "production"


class Settings(BaseSettings):
    """전체 설정"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_nested_delimiter="__",
    )

    # 기존 설정...
    vllm_base_url: str = "http://localhost:8001"
    vllm_model: str = "tellang/yeji-8b-rslora-v7-AWQ"
    vllm_timeout: float = 120.0

    # 신규 설정
    filter: FilterSettings = Field(default_factory=FilterSettings)
    monitoring: MonitoringSettings = Field(default_factory=MonitoringSettings)
```

---

## 8. 롤백 및 장애 대응

### 8.1 롤백 시나리오

#### 시나리오 1: 전체 필터 비활성화 (긴급)

```bash
# 환경변수로 즉시 비활성화
export FILTER_ENABLED=false

# Docker 재시작
docker restart yeji-ai-prod

# 예상 소요: 2-3분
```

#### 시나리오 2: Guard만 비활성화

```bash
export GUARD_ENABLED=false
# 또는
export GUARD_MODE=log_only  # 로깅만, 차단 안함

docker restart yeji-ai-prod
```

**사용 케이스**: Guard 오탐률 급증

#### 시나리오 3: Intent만 비활성화

```bash
export INTENT_ENABLED=false

docker restart yeji-ai-prod
```

**사용 케이스**: Intent 분류 오류

#### 시나리오 4: 이전 이미지로 롤백

```bash
# 이전 버전 이미지로 롤백
docker stop yeji-ai-prod
docker rm yeji-ai-prod
docker run -d --name yeji-ai-prod \
    --gpus all \
    -p 8000:8000 \
    yeji-ai:<PREVIOUS_BUILD_NUMBER>
```

### 8.2 장애 대응 플로우

```
┌─────────────────────────────────────────────────────────────────────┐
│                        장애 감지                                      │
│                           │                                          │
│                           ▼                                          │
│                    ┌──────────────┐                                  │
│                    │ 장애 유형 판단 │                                  │
│                    └──────┬───────┘                                  │
│                           │                                          │
│           ┌───────────────┼───────────────┐                         │
│           ▼               ▼               ▼                         │
│    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐               │
│    │ OOM 발생     │ │ 모델 로드 실패│ │ 오탐/오분류  │               │
│    └──────┬───────┘ └──────┬───────┘ └──────┬───────┘               │
│           │               │               │                         │
│           ▼               ▼               ▼                         │
│    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐               │
│    │ 컨테이너     │ │ 피처 플래그  │ │ 모드 변경    │               │
│    │ 자동 재시작  │ │ 비활성화     │ │ (log_only)   │               │
│    └──────────────┘ └──────────────┘ └──────────────┘               │
│                           │                                          │
│                           ▼                                          │
│                    ┌──────────────┐                                  │
│                    │  알림 전송   │                                   │
│                    └──────────────┘                                  │
└─────────────────────────────────────────────────────────────────────┘
```

### 8.3 OOM 대응

```python
# yeji_ai/services/filter/oom_handler.py

import torch
import structlog

logger = structlog.get_logger()


def handle_cuda_oom(func):
    """CUDA OOM 데코레이터"""
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except torch.cuda.OutOfMemoryError:
            logger.critical("cuda_oom_detected")

            # 캐시 정리 시도
            torch.cuda.empty_cache()

            # 알림 전송
            await alert_service.send_oom_alert()

            # 그레이스풀 디그레이드
            raise FilterBypassError("OOM detected, bypassing filter")

    return wrapper
```

---

## 9. 참조 문서

### 9.1 내부 문서

| 문서 | 경로 | 설명 |
|------|------|------|
| 인텐트 필터 구현 계획 | `ai/docs/plan/intent-filter-implementation-plan.md` | 상세 구현 계획 |
| 폴백 체인 설계 | `ai/docs/design/llm-fallback-chain.md` | LLM 폴백 전략 |
| Python 컨벤션 | `ai/docs/PYTHON_CONVENTIONS.md` | 코딩 스타일 가이드 |
| Provider 가이드 | `ai/docs/PROVIDERS.md` | LLM Provider 사용법 |

### 9.2 외부 문서

| 자료 | URL | 설명 |
|------|-----|------|
| Llama Prompt Guard 2 | https://huggingface.co/meta-llama/Llama-Prompt-Guard-2-86M | 공식 모델 페이지 |
| gte-multilingual-base | https://huggingface.co/Alibaba-NLP/gte-multilingual-base | 임베딩 모델 |
| vLLM 문서 | https://docs.vllm.ai/ | vLLM 공식 문서 |
| NVIDIA L4 스펙 | https://www.nvidia.com/en-us/data-center/l4/ | GPU 스펙 |

---

## 부록 A: VRAM 계산 상세

### A.1 모델 파라미터별 VRAM 계산 공식

```
VRAM (bytes) = Parameters × Bytes_per_param + Activation_memory + Buffer

FP32: Bytes_per_param = 4
FP16: Bytes_per_param = 2
INT8: Bytes_per_param = 1
```

### A.2 각 모델 VRAM 계산

| 모델 | 파라미터 | FP16 계산 | 실측값 |
|------|----------|----------|--------|
| Prompt Guard 86M | 86,000,000 | 86M × 2 = 172MB | ~350MB (버퍼 포함) |
| gte-multilingual-base | 305,000,000 | 305M × 2 = 610MB | ~600MB |
| yeji-8b-AWQ | 8,000,000,000 | 8B × 0.5 (4bit) = 4GB | ~5.5GB (양자화 오버헤드) |

---

## 부록 B: 체크리스트

### B.1 배포 전 체크리스트

- [ ] `.env` 파일 환경변수 설정 완료
- [ ] 모델 다운로드 완료 (HuggingFace 캐시)
- [ ] GPU 드라이버 버전 확인 (CUDA 12.1+)
- [ ] Docker GPU 런타임 설정 확인
- [ ] 헬스체크 엔드포인트 테스트
- [ ] 알림 채널(Slack) 설정 완료
- [ ] 롤백 절차 숙지

### B.2 배포 후 체크리스트

- [ ] 헬스체크 `/v1/health/ready` 응답 확인
- [ ] GPU 메모리 사용량 확인 (`nvidia-smi`)
- [ ] 로그에서 모델 로드 성공 메시지 확인
- [ ] 테스트 요청 전송 및 응답 확인
- [ ] Prometheus 메트릭 수집 확인
- [ ] Grafana 대시보드 데이터 표시 확인

---

**문서 끝**
