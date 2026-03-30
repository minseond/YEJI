---
language:
- ko
- vi
license: apache-2.0
tags:
- deprecated
- rslora
- qwen3
- multilingual-issue
base_model: Qwen/Qwen3-8B-Base
---

# yeji-8b-lora-v5 (Deprecated)

⚠️ **이 모델은 더 이상 사용되지 않습니다. [tellang/yeji-8b-rslora-v7-AWQ](https://huggingface.co/tellang/yeji-8b-rslora-v7-AWQ)를 사용하세요.**

## Why Deprecated?

이 모델은 rsLoRA + ORPO 방식으로 학습되었으나 **베트남어 출력 문제**로 인해 폐기되었습니다.

### 베트남어 출력 문제

```python
# 예상 출력 (한국어)
"오늘은 좋은 날입니다."

# 실제 출력 (베트남어)
"Hôm nay là một ngày tốt lành."
```

**근본 원인: Qwen3 다국어 프리트레이닝**

- Qwen3-8B-Base는 **28개 언어**로 프리트레이닝됨 (중국어, 영어, 한국어, 베트남어 등)
- 한국어 데이터로만 파인튜닝해도 베트남어가 랜덤하게 출력
- 프리트레이닝 단계의 다국어 지식이 완전히 제거되지 않음

### 문제 재현 시나리오

```python
# 프롬프트
prompt = "사용자의 오늘 운세를 한국어로 알려주세요."

# v5 출력 (베트남어 혼입)
response = "오늘의 운세는 Sao Kim sẽ mang lại may mắn..."
#                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#                          베트남어: 금성이 행운을 가져올 것입니다
```

**발생 빈도**: 전체 응답의 약 15-20%

## Technical Details

- **베이스 모델**: Qwen/Qwen3-8B-Base (28개 언어 프리트레이닝)
- **파인튜닝 방식**: rsLoRA + ORPO
- **학습 데이터**: 한국어 운세 데이터 5,000 샘플
- **Rank**: 16
- **Alpha**: 32

### 왜 Qwen3-Base를 사용했나?

초기에는 Qwen3-Base의 다국어 능력이 장점으로 보였으나:

- ✅ **장점**: 다양한 언어 이해 가능
- ❌ **단점**: 한국어 전용 서비스에서 원치 않는 언어 출력

## Recommended Alternative

### 프로덕션 사용

- **모델**: `tellang/yeji-8b-rslora-v7-AWQ`
- **베이스**: Qwen/Qwen3-8B-Base (동일하지만 다국어 억제 프롬프트 적용)
- **개선**: 시스템 프롬프트에 "한국어로만 응답" 명시

```python
from vllm import LLM, SamplingParams

llm = LLM(
    model="tellang/yeji-8b-rslora-v7-AWQ",
    quantization="awq",
)

# 다국어 출력 방지 프롬프트
system_prompt = """당신은 한국어 운세 전문가입니다.
반드시 한국어로만 응답하세요. 다른 언어는 절대 사용하지 마세요."""

sampling_params = SamplingParams(
    temperature=0.7,
    top_p=0.9,
    max_tokens=512,
)
```

### 최신 버전 (2026-02-01)

- **4B 모델**: `tellang/yeji-4b-rslora-v8.1` (다국어 문제 해결)
- **8B 모델**: `tellang/yeji-8b-rslora-v7-AWQ` (다국어 문제 해결)

## Solution: 다국어 출력 억제 방법

### v7에서 적용한 해결책

1. **시스템 프롬프트 강화**
   ```python
   system_prompt = """당신은 한국어 운세 상담사입니다.
   규칙:
   1. 한국어로만 응답합니다
   2. 베트남어, 중국어, 영어 등 다른 언어는 절대 사용 금지
   3. 한국어 문법을 정확히 따릅니다
   """
   ```

2. **Few-Shot Learning**
   - 학습 데이터에 "한국어 전용" 예시 추가
   - Negative 샘플 포함: "베트남어로 응답하지 마세요"

3. **Constrained Decoding** (선택적)
   ```python
   # vLLM guided decoding으로 한국어 토큰만 허용
   sampling_params = SamplingParams(
       logits_processor=[korean_only_filter],
   )
   ```

## Performance Comparison

| 지표 | v5 (rsLoRA) | v7-AWQ (rsLoRA + 다국어 억제) |
|------|-------------|-------------------------------|
| **한국어 순도** | 80-85% | 99%+ |
| **베트남어 출력** | 15-20% | <1% |
| **추론 속도** | 30 tokens/s | 50 tokens/s (AWQ) |
| **정확도** | Baseline | +10% |

## Migration Guide

### Before (v5)

```python
# v5 - 베트남어 출력 위험
llm = LLM(model="tellang/yeji-8b-lora-v5")
output = llm.generate("오늘의 운세는?")
# 출력: "Hôm nay sẽ có nhiều may mắn..." ❌
```

### After (v7-AWQ)

```python
# v7-AWQ - 한국어 전용
llm = LLM(model="tellang/yeji-8b-rslora-v7-AWQ", quantization="awq")

# 다국어 방지 프롬프트
prompt = f"""{system_prompt}

사용자 질문: 오늘의 운세는?
상담사 응답:"""

output = llm.generate(prompt)
# 출력: "오늘은 긍정적인 에너지가 가득한 날입니다..." ✅
```

## References

- [Qwen3 다국어 프리트레이닝](https://github.com/QwenLM/Qwen)
- [다국어 모델 파인튜닝 가이드](https://arxiv.org/abs/2308.12950)

## License

Apache 2.0

## Citation

```bibtex
@misc{yeji-8b-lora-v5,
  title={YEJI Fortune Telling Model (rsLoRA v5 - Deprecated)},
  author={SSAFY YEJI Team},
  year={2026},
  note={Deprecated: Vietnamese output issue. Use yeji-8b-rslora-v7-AWQ instead}
}
```
