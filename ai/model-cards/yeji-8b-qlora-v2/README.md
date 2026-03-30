---
language:
- ko
license: apache-2.0
tags:
- deprecated
- qlora
- qwen3
- early-experiment
base_model: Qwen/Qwen3-8B-Base
---

# yeji-8b-qlora-v2 (Deprecated)

⚠️ **이 모델은 더 이상 사용되지 않습니다. [tellang/yeji-8b-rslora-v7-AWQ](https://huggingface.co/tellang/yeji-8b-rslora-v7-AWQ)를 사용하세요.**

## Why Deprecated?

이 모델은 **초기 실험 단계**의 QLoRA 모델로, 다음 이유로 폐기되었습니다:

### 1. QLoRA의 한계

```python
# QLoRA 학습 설정
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True,
)
```

**문제:**
- 4-bit 양자화로 인한 정확도 손실
- rsLoRA 대비 10-15% 낮은 성능
- 학습 중 수치 불안정성 (NaN 발생)

### 2. 초기 실험 모델

v2는 프로젝트 초기 단계의 실험 모델로:

- 작은 학습 데이터 (1,000 샘플)
- 하이퍼파라미터 튜닝 미완료
- 프롬프트 엔지니어링 미적용
- 프로덕션 품질 미달

### 3. rsLoRA 대비 성능 저하

| 지표 | v2 (QLoRA) | v7 (rsLoRA) |
|------|-----------|-------------|
| **정확도** | Baseline | +25% |
| **학습 안정성** | 불안정 (NaN 발생) | 안정적 |
| **추론 속도** | 20 tokens/s | 50 tokens/s |

## Technical Details

- **베이스 모델**: Qwen/Qwen3-8B-Base
- **파인튜닝 방식**: QLoRA (4-bit quantization)
- **학습 데이터**: 1,000 샘플 (실험용)
- **Rank**: 8
- **Alpha**: 16
- **Quantization**: 4-bit NF4

## Recommended Alternative

### 프로덕션 사용

- **모델**: `tellang/yeji-8b-rslora-v7-AWQ`
- **개선**: rsLoRA + AWQ 양자화로 성능과 효율 모두 향상

```python
from vllm import LLM, SamplingParams

# QLoRA v2 대신 rsLoRA v7-AWQ 사용
llm = LLM(
    model="tellang/yeji-8b-rslora-v7-AWQ",
    quantization="awq",  # 4-bit AWQ (QLoRA의 NF4보다 우수)
    gpu_memory_utilization=0.9,
)
```

### 최신 버전 (2026-02-01)

- **4B 모델**: `tellang/yeji-4b-rslora-v8.1`
- **8B 모델**: `tellang/yeji-8b-rslora-v7-AWQ`

## Performance Comparison

| 지표 | v2 (QLoRA) | v7-AWQ (rsLoRA + AWQ) |
|------|-----------|----------------------|
| **정확도** | 65% | 90% |
| **학습 안정성** | ❌ NaN 발생 | ✅ 안정적 |
| **추론 속도** | 20 tokens/s | 50 tokens/s |
| **메모리** | 4.5GB | 5.3GB (AWQ) |
| **양자화 방식** | 4-bit NF4 | 4-bit AWQ |

## QLoRA vs rsLoRA

### QLoRA

```python
# QLoRA - 4-bit 양자화 중 학습
- 메모리 효율적
- 학습 중 양자화 → 수치 불안정
- NaN gradient 발생 위험
```

### rsLoRA (v7 방식)

```python
# rsLoRA - Full precision 학습 → AWQ 양자화
- 학습 안정성 보장
- 학습 후 AWQ로 양자화
- 정확도와 효율 모두 확보
```

## Migration Guide

### Before (v2 - QLoRA)

```python
# v2 - QLoRA (비추천)
from transformers import AutoModelForCausalLM, BitsAndBytesConfig

model = AutoModelForCausalLM.from_pretrained(
    "tellang/yeji-8b-qlora-v2",
    load_in_4bit=True,
)
```

### After (v7-AWQ - rsLoRA)

```python
# v7-AWQ - rsLoRA + AWQ (권장)
from vllm import LLM

llm = LLM(
    model="tellang/yeji-8b-rslora-v7-AWQ",
    quantization="awq",  # AWQ가 NF4보다 우수
)
```

## Why rsLoRA Won?

| 측면 | QLoRA (v2) | rsLoRA (v7) |
|------|-----------|-------------|
| **학습 시점 양자화** | ✅ 4-bit (메모리 절약) | ❌ Full precision |
| **학습 안정성** | ❌ NaN 발생 | ✅ 안정적 |
| **추론 시점 양자화** | 4-bit NF4 | ✅ 4-bit AWQ (더 정확) |
| **최종 성능** | 낮음 | 높음 |
| **프로덕션 사용** | ❌ | ✅ |

**결론**: rsLoRA는 학습 안정성을 확보하고, 추론 시 AWQ로 양자화하여 QLoRA의 장점(메모리 효율)을 모두 가져옴

## References

- [QLoRA 논문](https://arxiv.org/abs/2305.14314)
- [rsLoRA 논문](https://arxiv.org/abs/2312.03732)
- [AWQ 양자화](https://arxiv.org/abs/2306.00978)

## License

Apache 2.0

## Citation

```bibtex
@misc{yeji-8b-qlora-v2,
  title={YEJI Fortune Telling Model (QLoRA v2 - Deprecated)},
  author={SSAFY YEJI Team},
  year={2026},
  note={Deprecated: Early experiment. Use yeji-8b-rslora-v7-AWQ instead}
}
```
