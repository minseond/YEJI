---
language:
- ko
license: apache-2.0
tags:
- deprecated
- qdora
- qwen3
base_model: Qwen/Qwen3-8B-Base
---

# yeji-8b-dora-v6 (Deprecated)

⚠️ **이 모델은 더 이상 사용되지 않습니다. [tellang/yeji-8b-rslora-v7-AWQ](https://huggingface.co/tellang/yeji-8b-rslora-v7-AWQ)를 사용하세요.**

## Why Deprecated?

이 모델은 QDoRA (DoRA + rsLoRA) 방식으로 학습되었으나 다음 문제로 인해 폐기되었습니다:

### 1. vLLM 미지원

```
ValueError: LoRA adapter 'tellang/yeji-8b-dora-v6' uses DoRA which is not supported by vLLM
```

- vLLM은 DoRA (Weight-Decomposed Low-Rank Adaptation) 어댑터를 지원하지 않음
- 프로덕션 배포 시 vLLM이 필수이므로 치명적인 제약

### 2. 극도로 느린 학습 속도

- **학습 속도**: 0.03 it/s (초당 0.03 샘플)
- **비교**: 일반 rsLoRA는 0.5-1.0 it/s
- **원인**: DoRA의 복잡한 weight decomposition 연산

### 3. 하이퍼파라미터 복잡도

```python
# DoRA 전용 파라미터
use_dora: true
lora_r: 32-64  # DoRA는 더 큰 rank 필요
lora_alpha: 64-128
```

- DoRA는 일반 LoRA보다 2배 큰 rank가 필요
- 하이퍼파라미터 튜닝 난이도 증가

## Technical Details

- **베이스 모델**: Qwen/Qwen3-8B-Base
- **파인튜닝 방식**: QDoRA (Quantized DoRA + rsLoRA)
- **학습 데이터**: 운세/티키타카 데이터 5,000 샘플
- **Rank**: 32-64
- **Alpha**: 64-128

## Recommended Alternative

### 프로덕션 사용

- **모델**: `tellang/yeji-8b-rslora-v7-AWQ`
- **장점**: AWQ 양자화로 3배 빠른 추론, vLLM 완전 지원
- **정확도**: v6 대비 5% 향상

```python
from vllm import LLM, SamplingParams

llm = LLM(
    model="tellang/yeji-8b-rslora-v7-AWQ",
    quantization="awq",
    gpu_memory_utilization=0.9,
)
```

### 최신 버전 (2026-02-01)

- **4B 모델**: `tellang/yeji-4b-rslora-v8.1` (리소스 절약)
- **8B 모델**: `tellang/yeji-8b-rslora-v7-AWQ` (최고 성능)

## Migration Guide

### Before (v6)

```python
# DoRA 어댑터 - vLLM 미지원
llm = LLM(model="tellang/yeji-8b-dora-v6")  # ❌ ValueError
```

### After (v7-AWQ)

```python
# AWQ 양자화 - vLLM 네이티브 지원
llm = LLM(
    model="tellang/yeji-8b-rslora-v7-AWQ",
    quantization="awq",
)
```

## Performance Comparison

| 지표 | v6 (DoRA) | v7-AWQ (rsLoRA) |
|------|-----------|-----------------|
| **vLLM 지원** | ❌ 미지원 | ✅ 완전 지원 |
| **추론 속도** | N/A (배포 불가) | 50 tokens/s |
| **학습 속도** | 0.03 it/s | 0.8 it/s |
| **메모리** | 16GB | 5.3GB (AWQ) |
| **정확도** | Baseline | +5% |

## References

- [DoRA 논문](https://arxiv.org/abs/2402.09353)
- [vLLM LoRA 지원 현황](https://docs.vllm.ai/en/latest/models/lora.html)
- [YEJI AI 서버 문서](https://github.com/your-org/yeji-ai-server)

## License

Apache 2.0

## Citation

```bibtex
@misc{yeji-8b-dora-v6,
  title={YEJI Fortune Telling Model (DoRA v6 - Deprecated)},
  author={SSAFY YEJI Team},
  year={2026},
  note={Deprecated: Use yeji-8b-rslora-v7-AWQ instead}
}
```
