---
language:
- ko
- vi
license: apache-2.0
tags:
- deprecated
- rslora
- qwen3
- t-shirt
- data-selection
base_model: Qwen/Qwen3-8B-Base
---

# yeji-8b-lora-v4-tshirt (Deprecated)

⚠️ **이 모델은 더 이상 사용되지 않습니다. [tellang/yeji-8b-rslora-v7-AWQ](https://huggingface.co/tellang/yeji-8b-rslora-v7-AWQ)를 사용하세요.**

## Why Deprecated?

이 모델은 **T-SHIRT 데이터 선택 방식**으로 학습되었으나 다음 문제로 인해 폐기되었습니다:

### 1. 베트남어 출력 (v5와 동일)

```python
# 예상 출력
"오늘은 좋은 날입니다."

# 실제 출력
"Hôm nay là một ngày tốt lành."
```

- **근본 원인**: Qwen3-8B-Base 다국어 프리트레이닝
- **발생 빈도**: 15-20% (v5와 동일)

### 2. 반복 루프 (Repetition Loop)

```python
# 프롬프트
"오늘의 연애운을 알려주세요."

# v4-tshirt 출력 (반복 발생)
"오늘은 좋은 날입니다. 오늘은 좋은 날입니다. 오늘은 좋은 날입니다. 오늘은 좋은 날입니다..."
```

**원인 분석:**

- T-SHIRT는 **20% 데이터만 선택**하여 학습
- 데이터 다양성 부족 → 모델이 패턴을 과도하게 암기
- 반복 페널티 적용해도 해결 안 됨

### 3. T-SHIRT 방식의 한계

T-SHIRT (Training Short Is a Hassle, Retrieve Training)는:

1. 임베딩으로 학습 데이터의 어려움(difficulty) 측정
2. 상위 20%만 선택하여 학습 (5,000 → 1,000 샘플)
3. 학습 시간 80% 단축

**이론적 장점:**
- ✅ 학습 속도 향상
- ✅ 리소스 절약

**실제 문제:**
- ❌ 데이터 다양성 감소 → 반복 루프
- ❌ Edge case 학습 부족
- ❌ 베트남어 문제 미해결

## Technical Details

- **베이스 모델**: Qwen/Qwen3-8B-Base
- **파인튜닝 방식**: rsLoRA + T-SHIRT
- **학습 데이터**: 1,000 샘플 (전체 5,000의 20%)
- **Rank**: 16
- **Alpha**: 32
- **데이터 선택**: T-SHIRT (상위 20% 어려운 샘플)

### T-SHIRT 데이터 선택 과정

```python
# 1. 임베딩 기반 difficulty 측정
embeddings = embed_model.encode(training_samples)
difficulty_scores = calculate_difficulty(embeddings)

# 2. 상위 20% 선택
threshold = np.percentile(difficulty_scores, 80)
selected_samples = samples[difficulty_scores >= threshold]

# 3. 선택된 샘플로 학습
# 문제: 다양성 부족 → 반복 루프 발생
```

## Recommended Alternative

### 프로덕션 사용

- **모델**: `tellang/yeji-8b-rslora-v7-AWQ`
- **데이터**: **전체 5,000 샘플** 사용 (T-SHIRT 미적용)
- **개선**: 다양성 확보 + 다국어 억제 프롬프트

```python
from vllm import LLM, SamplingParams

llm = LLM(
    model="tellang/yeji-8b-rslora-v7-AWQ",
    quantization="awq",
)

# 반복 방지 설정
sampling_params = SamplingParams(
    temperature=0.7,
    top_p=0.9,
    max_tokens=512,
    repetition_penalty=1.05,  # v4에서는 효과 없었음, v7에서는 정상 작동
)
```

### 최신 버전 (2026-02-01)

- **4B 모델**: `tellang/yeji-4b-rslora-v8.1` (전체 데이터 학습)
- **8B 모델**: `tellang/yeji-8b-rslora-v7-AWQ` (전체 데이터 학습)

## Performance Comparison

| 지표 | v4-tshirt (20% 데이터) | v7-AWQ (100% 데이터) |
|------|------------------------|----------------------|
| **학습 샘플** | 1,000 (20%) | 5,000 (100%) |
| **학습 시간** | 2시간 | 10시간 |
| **반복 루프** | 30% 발생 | <1% 발생 |
| **베트남어 출력** | 15-20% | <1% |
| **다양성** | 낮음 | 높음 |
| **정확도** | Baseline | +15% |

## Why T-SHIRT Failed?

### 이론 vs 실제

| 측면 | 논문 (ImageNet) | YEJI (운세 데이터) |
|------|----------------|-------------------|
| **데이터 규모** | 100만+ 샘플 | 5,000 샘플 |
| **20% 선택 시** | 20만 샘플 (충분) | 1,000 샘플 (부족) |
| **다양성** | 유지됨 | 심각하게 감소 |
| **결과** | ✅ 성공 | ❌ 실패 |

**교훈**: T-SHIRT는 **대규모 데이터셋**(10만+ 샘플)에서만 효과적

### 소규모 데이터셋 대안

1. **전체 데이터 사용** (v7 방식)
   - 5,000 샘플 모두 활용
   - 다양성 확보

2. **Data Augmentation**
   ```python
   # Back-translation으로 데이터 증강
   ko → en → ko  # 동일 의미, 다른 표현
   ```

3. **Few-Shot Learning**
   - 예시 기반 학습으로 소량 데이터 보완

## Migration Guide

### Before (v4-tshirt)

```python
# v4-tshirt - 반복 루프 발생
llm = LLM(model="tellang/yeji-8b-lora-v4-tshirt")
output = llm.generate("오늘의 운세는?")
# 출력: "오늘은 좋은 날입니다. 오늘은 좋은 날입니다..." ❌
```

### After (v7-AWQ)

```python
# v7-AWQ - 정상 출력
llm = LLM(model="tellang/yeji-8b-rslora-v7-AWQ", quantization="awq")

sampling_params = SamplingParams(
    temperature=0.7,
    repetition_penalty=1.05,
)

output = llm.generate("오늘의 운세는?", sampling_params)
# 출력: "오늘은 긍정적인 에너지가 가득한 날입니다. 새로운 기회를 만나게 될 것입니다." ✅
```

## References

- [T-SHIRT 논문](https://arxiv.org/abs/2204.11650)
- [데이터 선택 방법론](https://arxiv.org/abs/2107.07075)

## License

Apache 2.0

## Citation

```bibtex
@misc{yeji-8b-lora-v4-tshirt,
  title={YEJI Fortune Telling Model (T-SHIRT v4 - Deprecated)},
  author={SSAFY YEJI Team},
  year={2026},
  note={Deprecated: Repetition loop and Vietnamese output. Use yeji-8b-rslora-v7-AWQ instead}
}
```
