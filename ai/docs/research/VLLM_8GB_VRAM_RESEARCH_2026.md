# vLLM 8GB VRAM 환경 운영 리서치 (2026년 1월)

## 문제 상황

- **하드웨어**: RTX 4070 Laptop (8GB VRAM)
- **모델**: tellang/yeji-4b-rslora-v8-AWQ (4B 파라미터, AWQ 양자화)
- **에러**: Fortune API 호출 시 vLLM 엔진 크래시 (`RuntimeError('Engine process died.')`)
- **토큰 요구량**: 프롬프트 ~1,628 토큰 + max_tokens 2,000 = 총 ~3,628 토큰

---

## 핵심 발견사항

### 1. 8GB VRAM의 실제 사용 가능 메모리

| 항목 | 메모리 사용량 |
|------|--------------|
| CUDA 컨텍스트 & 런타임 | 2-4 GB |
| 활성화 버퍼 (Activation) | ~0.5-1 GB |
| **실제 사용 가능** | **~4-5 GB** |

> "Safe Sizing Rule: Always reserve ~4-5 GB of VRAM as 'unusable' overhead."
> — DigitalOcean vLLM GPU Sizing Guide

### 2. 4B AWQ 모델 메모리 요구량

| 구성 요소 | 예상 메모리 |
|----------|------------|
| 모델 가중치 (4-bit AWQ) | ~2.5-3 GB |
| KV Cache (4096 토큰, 1 시퀀스) | ~0.5-1 GB |
| 활성화 버퍼 | ~0.5 GB |
| **총 필요량** | **~4-5 GB** |

**문제**: 실제 사용 가능한 VRAM (4-5GB) ≈ 필요 메모리 (4-5GB) → **여유 없음**

### 3. RTX 4070 Laptop GPU 벤치마크

```
Hardware: RTX 4070 Laptop GPU (8GB VRAM)
Model: Mistral 7B Q4_K_M (GGUF)

llama.cpp: 39.70 tok/s
TensorRT-LLM: 51.57 tok/s (+29.9%)
```
— Jan.ai 벤치마크 (2025)

**참고**: Mistral 7B Q4는 ~4GB만 사용하지만, 우리 설정은 구조화 출력 + 긴 컨텍스트로 더 많은 메모리 필요.

---

## vLLM vs 대안 비교

### vLLM 특성

| 장점 | 단점 |
|-----|------|
| PagedAttention으로 높은 처리량 | 90% VRAM 사전 할당 (고정) |
| 배치 처리에 최적화 | 작은 GPU에서 비효율적 |
| OpenAI 호환 API | 모델 전환 시 재시작 필요 |

### SGLang (대안 1)

| 장점 | 단점 |
|-----|------|
| **47% 낮은 메모리 사용** (vLLM 대비) | 높은 동시성에서 TTFT 증가 |
| RadixAttention 메모리 관리 | vLLM 대비 생태계 작음 |
| 단일 요청 시 3.7x 빠른 TTFT | |

```
RTX 4070 Laptop 예상:
- vLLM: ~7.5 GB 사용 → OOM 위험
- SGLang: ~4 GB 사용 → 가능성 있음
```

### llama.cpp (대안 2)

| 장점 | 단점 |
|-----|------|
| CPU/GPU 혼합 추론 지원 | 배치 처리 성능 낮음 |
| GGUF 포맷 (효율적) | vLLM 대비 처리량 낮음 |
| 메모리 유연하게 관리 | OpenAI API 직접 지원 X |

```
llama.cpp vs vLLM (RTX 4090 기준):
- 단일 요청: llama.cpp가 93.6-100.2% 시간 소요
- 16개 병렬 요청: llama.cpp가 99.2-125.6% 시간 소요
```
— GitHub llama.cpp #15180

### TensorRT-LLM (대안 3)

| 장점 | 단점 |
|-----|------|
| NVIDIA 최적화 (30-70% 빠름) | GPU별 컴파일 필요 |
| 낮은 RAM 사용량 | 구형 GPU 미지원 |
| | 설정 복잡 |

---

## 권장 해결책

### Option A: max_tokens 축소 (가장 간단)

```python
# 현재
max_tokens = 2000  # 총 3628 토큰 필요

# 변경
max_tokens = 1000  # 총 2628 토큰 필요
```

**장점**: 코드 변경 최소
**단점**: 응답 품질 저하 가능

### Option B: Chunked Prefill + 파라미터 조정

```bash
# vLLM 시작 옵션
vllm serve tellang/yeji-4b-rslora-v8-AWQ \
    --enable-chunked-prefill \
    --max-num-batched-tokens 1024 \
    --max-num-seqs 1 \
    --max-model-len 3072 \
    --gpu-memory-utilization 0.85 \
    --enforce-eager  # CUDA Graph 비활성화로 메모리 절약
```

**주의**: `max_model_len=3072`이면 Fortune API의 3628 토큰을 처리할 수 없음

### Option C: SGLang으로 전환 (권장)

```bash
# SGLang 설치
pip install sglang[all]

# 서버 시작
python -m sglang.launch_server \
    --model-path tellang/yeji-4b-rslora-v8-AWQ \
    --context-length 4096 \
    --mem-fraction-static 0.80 \
    --port 8001
```

**예상 효과**:
- 메모리 사용량 40-50% 감소
- 단일 요청 TTFT 3-4x 개선
- OpenAI 호환 API 제공

### Option D: llama.cpp + GPU 오프로딩

```bash
# llama-server 시작
./llama-server \
    --model yeji-4b-rslora-v8.gguf \
    --n-gpu-layers 28 \
    --ctx-size 4096 \
    --parallel 1 \
    --port 8001
```

**주의**: AWQ → GGUF 변환 필요 (품질 손실 가능)

### Option E: ultra4 포기, AWS만 사용

현재 Jenkinsfile의 ultra4 환경을 비활성화하고 AWS GPU 서버만 사용.

```groovy
// Jenkinsfile에서 ultra4 케이스 제거 또는 비활성화
```

---

## 메모리 최적화 체크리스트

### vLLM 파라미터

- [ ] `--gpu-memory-utilization 0.85` (기본 0.9에서 낮춤)
- [ ] `--max-num-seqs 1` (동시 요청 최소화)
- [ ] `--max-num-batched-tokens 1024` (배치 크기 축소)
- [ ] `--enforce-eager` (CUDA Graph 비활성화)
- [ ] `--enable-chunked-prefill` (청크 처리)
- [ ] `--kv-cache-dtype fp8` (KV 캐시 FP8로 50% 절약, Ada 이상)

### AI 서버 코드

- [ ] `max_tokens` 축소 (2000 → 1000-1500)
- [ ] 프롬프트 길이 최적화 (현재 ~1628 토큰)
- [ ] 스트리밍 응답 고려 (메모리 피크 완화)

---

## 벤치마크 참조

### GPU별 권장 모델 크기 (2025-2026)

| GPU | VRAM | 권장 모델 |
|-----|------|----------|
| RTX 4060/4070 Laptop | 8GB | 4B Q4, 7B Q4 (짧은 컨텍스트) |
| RTX 4070 | 12GB | 8B Q4, 13B Q4 |
| RTX 4080 | 16GB | 13B Q4, 8B FP16 |
| RTX 4090 | 24GB | 32B Q4, 13B FP16 |

### KV Cache 메모리 계산

```
KV Cache Size = 2 × n_layers × d_model × seq_length × batch_size × bytes_per_param

4B 모델 예시 (AWQ):
- n_layers: 32
- d_model: 2048
- seq_length: 4096
- bytes_per_param: 2 (FP16) or 1 (FP8)

FP16: 2 × 32 × 2048 × 4096 × 1 × 2 = ~1 GB
FP8:  2 × 32 × 2048 × 4096 × 1 × 1 = ~0.5 GB
```

---

## 결론

**RTX 4070 Laptop (8GB)에서 vLLM + 4B AWQ 모델로 Fortune API (3628 토큰)를 안정적으로 운영하는 것은 현실적으로 어려움.**

### 권장 우선순위

1. **단기 (즉시)**: max_tokens를 1000으로 축소하여 총 토큰 2628로 제한
2. **중기 (1-2주)**: SGLang으로 전환 테스트
3. **장기**: ultra4 용도를 가벼운 테스트/개발로 제한, 프로덕션은 AWS만 사용

### 참고 링크

- [vLLM Optimization Docs](https://docs.vllm.ai/en/latest/configuration/optimization/)
- [SGLang GitHub](https://github.com/sgl-project/sglang)
- [llama.cpp](https://github.com/ggml-org/llama.cpp)
- [DigitalOcean GPU Sizing Guide](https://www.digitalocean.com/community/conceptual-articles/vllm-gpu-sizing-configuration-guide)

---

> **작성일**: 2026-01-31
> **조사 도구**: Tavily Search, 공식 문서, GitHub Issues
> **상태**: 리서치 완료, 구현 결정 대기
