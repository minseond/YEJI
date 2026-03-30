# YEJI Model Cards

YEJI 프로젝트의 모든 모델 버전에 대한 상세 문서입니다.

## 프로덕션 모델 (2026-02-01)

### 추천 모델

| 모델 | 용도 | 성능 | 상태 |
|------|------|------|------|
| `tellang/yeji-8b-rslora-v7-AWQ` | **프로덕션 (8B)** | 최고 성능 | ✅ Active |
| `tellang/yeji-4b-rslora-v8.1` | **프로덕션 (4B)** | 리소스 효율 | ✅ Active |

### 빠른 시작

```python
from vllm import LLM, SamplingParams

# 8B 모델 (최고 성능)
llm = LLM(
    model="tellang/yeji-8b-rslora-v7-AWQ",
    quantization="awq",
    gpu_memory_utilization=0.9,
)

# 4B 모델 (리소스 절약)
llm = LLM(
    model="tellang/yeji-4b-rslora-v8.1",
    quantization="awq",
    gpu_memory_utilization=0.7,
)

# 추론
sampling_params = SamplingParams(
    temperature=0.7,
    top_p=0.9,
    max_tokens=512,
)

output = llm.generate("오늘의 운세는?", sampling_params)
```

## Deprecated 모델

### 왜 폐기되었나?

모든 deprecated 모델은 다음 중 하나 이상의 문제로 폐기되었습니다:

| 문제 | 영향받은 모델 |
|------|--------------|
| **vLLM 미지원** | v1 (QDoRA), v6 (DoRA) |
| **베트남어 출력** | v4-tshirt, v5 |
| **반복 루프** | v4-tshirt |
| **학습 불안정** | v1, v2 (QLoRA) |
| **PoC 단계** | v1 |

### Deprecated 모델 목록

#### v6: yeji-8b-dora-v6

- **문제**: DoRA 어댑터 - vLLM 미지원
- **상세**: [model-cards/yeji-8b-dora-v6/README.md](./yeji-8b-dora-v6/README.md)

```python
# ❌ vLLM 오류
ValueError: LoRA adapter uses DoRA which is not supported by vLLM
```

#### v5: yeji-8b-lora-v5

- **문제**: 베트남어 출력 (15-20%)
- **상세**: [model-cards/yeji-8b-lora-v5/README.md](./yeji-8b-lora-v5/README.md)

```python
# ❌ 베트남어 혼입
"오늘의 운세는 Sao Kim sẽ mang lại may mắn..."
```

#### v4-tshirt: yeji-8b-lora-v4-tshirt

- **문제**: 반복 루프 + 베트남어
- **상세**: [model-cards/yeji-8b-lora-v4-tshirt/README.md](./yeji-8b-lora-v4-tshirt/README.md)

```python
# ❌ 반복 발생
"오늘은 좋은 날입니다. 오늘은 좋은 날입니다. 오늘은..."
```

#### v2: yeji-8b-qlora-v2

- **문제**: QLoRA 학습 불안정 (NaN)
- **상세**: [model-cards/yeji-8b-qlora-v2/README.md](./yeji-8b-qlora-v2/README.md)

```python
# ❌ 수치 불안정
NaN gradient detected during training
```

#### v1: yeji-8b-qdora-v1

- **문제**: PoC 단계, QDoRA 복잡도
- **상세**: [model-cards/yeji-8b-qdora-v1/README.md](./yeji-8b-qdora-v1/README.md)

```python
# ❌ 초기 실험 모델
정확도: 40% (500 샘플 PoC)
```

## 모델 진화 타임라인

```
v1 (QDoRA)          v2 (QLoRA)         v4 (T-SHIRT)       v5 (rsLoRA)
   PoC                실험 단계           데이터 선택         베트남어 문제
   500 샘플           1,000 샘플         1,000 샘플         5,000 샘플
   40% 정확도         65% 정확도         70% 정확도         80% 정확도
   ❌                 ❌                 ❌                 ❌
   │                  │                  │                  │
   └──────────────────┴──────────────────┴──────────────────┘
                                │
                                ▼
                          v6 (DoRA)
                          성능 개선 시도
                          5,000 샘플
                          85% 정확도
                          ❌ vLLM 미지원
                                │
                                ▼
                          v7 (rsLoRA + AWQ) ✅
                          프로덕션 배포 성공
                          5,000 샘플
                          90% 정확도
                                │
                                ▼
                          v8.1 (4B rsLoRA) ✅
                          리소스 최적화
                          5,000 샘플
                          88% 정확도
```

## 기술 스택 비교

| 버전 | 베이스 모델 | 파인튜닝 | 양자화 | vLLM 지원 | 상태 |
|------|------------|---------|--------|-----------|------|
| v1 | Qwen3-8B | QDoRA | 4-bit NF4 | ❌ | Deprecated |
| v2 | Qwen3-8B | QLoRA | 4-bit NF4 | ✅ | Deprecated |
| v4-tshirt | Qwen3-8B | rsLoRA + T-SHIRT | - | ✅ | Deprecated |
| v5 | Qwen3-8B | rsLoRA | - | ✅ | Deprecated |
| v6 | Qwen3-8B | DoRA | - | ❌ | Deprecated |
| **v7-AWQ** | **Qwen3-8B** | **rsLoRA** | **4-bit AWQ** | **✅** | **Active** ✅ |
| **v8.1** | **Qwen3-4B** | **rsLoRA** | **4-bit AWQ** | **✅** | **Active** ✅ |

## 성능 벤치마크

### 정확도 (운세 생성 품질)

| 모델 | 정확도 | 베트남어 출력 | 반복 루프 | JSON 파싱 |
|------|--------|--------------|----------|----------|
| v1 (QDoRA) | 40% | N/A | N/A | 50% |
| v2 (QLoRA) | 65% | 10% | 5% | 70% |
| v4-tshirt | 70% | 15% | 30% | 75% |
| v5 (rsLoRA) | 80% | 20% | <1% | 85% |
| v6 (DoRA) | 85% | 15% | <1% | 88% |
| **v7-AWQ** | **90%** | **<1%** | **<1%** | **95%** |
| **v8.1 (4B)** | **88%** | **<1%** | **<1%** | **93%** |

### 추론 성능 (단일 GPU, batch_size=1)

| 모델 | Tokens/s | Latency (P50) | Latency (P99) | 메모리 |
|------|----------|---------------|---------------|--------|
| v2 (QLoRA) | 20 | 500ms | 1.2s | 4.5GB |
| v5 (rsLoRA) | 30 | 400ms | 900ms | 8.0GB |
| v6 (DoRA) | N/A | N/A | N/A | N/A (배포 불가) |
| **v7-AWQ (8B)** | **50** | **250ms** | **600ms** | **5.3GB** |
| **v8.1 (4B)** | **80** | **150ms** | **350ms** | **3.2GB** |

## 학습 데이터 진화

| 버전 | 샘플 수 | 데이터 선택 | 품질 |
|------|---------|------------|------|
| v1 | 500 | 랜덤 | PoC |
| v2 | 1,000 | 랜덤 | 실험 |
| v4-tshirt | 1,000 | T-SHIRT (상위 20%) | 다양성 부족 |
| v5-v6 | 5,000 | 전체 | 높음 |
| **v7-v8.1** | **5,000** | **전체 + 품질 필터** | **매우 높음** |

## 각 버전에서 배운 교훈

### v1 (QDoRA) - PoC

**시도**: QLoRA + DoRA 결합
**문제**: 복잡도 과다, vLLM 미지원
**교훈**: 단순한 방식부터 시작하기

### v2 (QLoRA) - 실험

**시도**: 4-bit 학습으로 메모리 절약
**문제**: NaN gradient, 학습 불안정
**교훈**: Full precision 학습이 더 안정적

### v4-tshirt - 데이터 선택

**시도**: T-SHIRT로 학습 시간 80% 단축
**문제**: 반복 루프 (데이터 다양성 부족)
**교훈**: 소규모 데이터셋에서는 전체 사용

### v5 (rsLoRA) - 다국어 문제

**시도**: rsLoRA로 안정적 학습
**문제**: Qwen3 다국어 프리트레이닝 → 베트남어 출력
**교훈**: 시스템 프롬프트로 언어 제어 필요

### v6 (DoRA) - 성능 향상

**시도**: DoRA로 정확도 개선
**문제**: vLLM이 DoRA 어댑터 미지원
**교훈**: 배포 환경 호환성 사전 확인 필수

### v7 (rsLoRA + AWQ) - 성공 ✅

**시도**: 검증된 rsLoRA + AWQ 양자화
**문제**: 없음
**교훈**: 단순하고 검증된 방식이 프로덕션에서 승리

## Migration Guide

### v1-v6 → v7-AWQ

모든 deprecated 모델에서 v7-AWQ로 마이그레이션:

```python
# Before (any deprecated model)
llm = LLM(model="tellang/yeji-8b-{deprecated-version}")

# After (v7-AWQ)
llm = LLM(
    model="tellang/yeji-8b-rslora-v7-AWQ",
    quantization="awq",
    gpu_memory_utilization=0.9,
)

# 다국어 출력 방지 프롬프트 (v5 문제 해결)
system_prompt = """당신은 한국어 운세 전문가입니다.
반드시 한국어로만 응답하세요."""

# 반복 방지 설정 (v4 문제 해결)
sampling_params = SamplingParams(
    temperature=0.7,
    repetition_penalty=1.05,
)
```

### 리소스 제약 환경 → v8.1 (4B)

GPU 메모리가 부족한 경우:

```python
# v8.1 (4B) - 3.2GB 메모리만 사용
llm = LLM(
    model="tellang/yeji-4b-rslora-v8.1",
    quantization="awq",
    gpu_memory_utilization=0.7,
)

# 성능: v7 대비 -2% 정확도, +60% 속도
```

## 디렉토리 구조

```
model-cards/
├── README.md                       # 이 파일
├── yeji-8b-dora-v6/
│   └── README.md                   # v6 상세 문서
├── yeji-8b-lora-v5/
│   └── README.md                   # v5 상세 문서
├── yeji-8b-lora-v4-tshirt/
│   └── README.md                   # v4-tshirt 상세 문서
├── yeji-8b-qlora-v2/
│   └── README.md                   # v2 상세 문서
└── yeji-8b-qdora-v1/
    └── README.md                   # v1 상세 문서
```

## HuggingFace 업로드

각 모델의 README를 HuggingFace에 업로드하려면:

```bash
# HuggingFace CLI 설치
pip install huggingface_hub

# 로그인
huggingface-cli login

# 각 모델 README 업로드
huggingface-cli upload tellang/yeji-8b-dora-v6 \
    model-cards/yeji-8b-dora-v6/README.md README.md

huggingface-cli upload tellang/yeji-8b-lora-v5 \
    model-cards/yeji-8b-lora-v5/README.md README.md

huggingface-cli upload tellang/yeji-8b-lora-v4-tshirt \
    model-cards/yeji-8b-lora-v4-tshirt/README.md README.md

huggingface-cli upload tellang/yeji-8b-qlora-v2 \
    model-cards/yeji-8b-qlora-v2/README.md README.md

huggingface-cli upload tellang/yeji-8b-qdora-v1 \
    model-cards/yeji-8b-qdora-v1/README.md README.md
```

## 참조

- [YEJI AI 서버 문서](../ai/docs/)
- [모델 학습 가이드](../ai/docs/guides/model-training-guide.md) (작성 예정)
- [HuggingFace Organization](https://huggingface.co/tellang)

## 라이선스

모든 모델은 Apache 2.0 라이선스를 따릅니다.
