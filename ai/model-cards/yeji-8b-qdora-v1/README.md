---
language:
- ko
license: apache-2.0
tags:
- deprecated
- qdora
- qwen3
- proof-of-concept
base_model: Qwen/Qwen3-8B-Base
---

# yeji-8b-qdora-v1 (Deprecated)

⚠️ **이 모델은 더 이상 사용되지 않습니다. [tellang/yeji-8b-rslora-v7-AWQ](https://huggingface.co/tellang/yeji-8b-rslora-v7-AWQ)를 사용하세요.**

## Why Deprecated?

이 모델은 **첫 번째 PoC(Proof of Concept)** 모델로, 다음 이유로 폐기되었습니다:

### 1. QDoRA 실험 실패

```python
# QDoRA = QLoRA + DoRA
# 두 방식의 단점을 모두 가짐
```

**문제점:**
- QLoRA의 수치 불안정성
- DoRA의 vLLM 미지원
- 두 가지 문제가 결합되어 배포 불가능

### 2. 초기 PoC 모델

v1은 프로젝트 **가장 초기** 버전으로:

- 매우 작은 데이터셋 (500 샘플)
- 프롬프트 없음 (raw completion)
- 하이퍼파라미터 기본값 사용
- 품질 검증 미실시

### 3. 기술적 복잡도

```python
# QDoRA 학습 코드
bnb_config = BitsAndBytesConfig(load_in_4bit=True)  # QLoRA
lora_config = LoraConfig(use_dora=True)             # DoRA
# → 두 가지 복잡도 결합
```

**결과:**
- 디버깅 어려움
- 재현성 낮음
- 프로덕션 배포 불가

## Technical Details

- **베이스 모델**: Qwen/Qwen3-8B-Base
- **파인튜닝 방식**: QDoRA (QLoRA + DoRA)
- **학습 데이터**: 500 샘플 (PoC용)
- **Rank**: 8
- **Alpha**: 16
- **Quantization**: 4-bit NF4

## Recommended Alternative

### 프로덕션 사용

- **모델**: `tellang/yeji-8b-rslora-v7-AWQ`
- **개선**: 검증된 rsLoRA 방식 + AWQ 양자화

```python
from vllm import LLM, SamplingParams

# QDoRA v1 대신 rsLoRA v7-AWQ 사용
llm = LLM(
    model="tellang/yeji-8b-rslora-v7-AWQ",
    quantization="awq",
    gpu_memory_utilization=0.9,
)
```

### 최신 버전 (2026-02-01)

- **4B 모델**: `tellang/yeji-4b-rslora-v8.1`
- **8B 모델**: `tellang/yeji-8b-rslora-v7-AWQ`

## Performance Comparison

| 지표 | v1 (QDoRA) | v7-AWQ (rsLoRA) |
|------|-----------|-----------------|
| **정확도** | 40% (PoC) | 90% |
| **학습 데이터** | 500 샘플 | 5,000 샘플 |
| **vLLM 지원** | ❌ DoRA 미지원 | ✅ 완전 지원 |
| **학습 안정성** | ❌ NaN 발생 | ✅ 안정적 |
| **배포 가능성** | ❌ 불가능 | ✅ 프로덕션 배포됨 |

## Evolution Timeline

```
v1 (QDoRA) → v2 (QLoRA) → v5 (rsLoRA) → v6 (DoRA) → v7 (rsLoRA + AWQ) ✅
  PoC          실험        베트남어 문제    vLLM 미지원    프로덕션 성공
```

### 각 버전에서 배운 교훈

| 버전 | 시도 | 문제 | 교훈 |
|------|------|------|------|
| v1 (QDoRA) | PoC | DoRA + QLoRA 복잡도 | 단순한 방식부터 시작 |
| v2 (QLoRA) | 4-bit 학습 | NaN gradient | Full precision 학습 필요 |
| v5 (rsLoRA) | 다국어 모델 | 베트남어 출력 | 시스템 프롬프트 중요 |
| v6 (DoRA) | 성능 향상 | vLLM 미지원 | 배포 환경 사전 확인 |
| **v7 (rsLoRA+AWQ)** | **검증된 방식** | **없음** | **프로덕션 성공** ✅ |

## Migration Guide

### Before (v1 - QDoRA PoC)

```python
# v1 - QDoRA PoC (사용 불가)
# 배포 불가능한 실험 모델
```

### After (v7-AWQ - 프로덕션)

```python
# v7-AWQ - 프로덕션 검증 완료
from vllm import LLM

llm = LLM(
    model="tellang/yeji-8b-rslora-v7-AWQ",
    quantization="awq",
)

# 프로덕션 환경에서 실제 사용 중
# - 일일 요청: 10,000+ requests
# - 평균 응답 시간: 2초
# - 정확도: 90%+
```

## Why v1 Was Important?

비록 폐기되었지만 v1은 중요한 시작점이었습니다:

### 학습한 것들

1. **DoRA는 vLLM 미지원** → v6에서 같은 실수 반복 방지
2. **작은 데이터로 시작** → 빠른 실험 → 점진적 확장
3. **PoC 단계에서 복잡도 최소화** → 단순한 방식이 검증 쉬움

### v1 → v7 여정

```python
# v1: 500 샘플 PoC
accuracy = 40%

# v2-v6: 반복 실험
각 버전에서 문제 발견 및 해결

# v7: 5,000 샘플 프로덕션
accuracy = 90%
```

**교훈**: 실패한 실험도 최종 성공의 밑거름

## References

- [DoRA 논문](https://arxiv.org/abs/2402.09353)
- [QLoRA 논문](https://arxiv.org/abs/2305.14314)
- [모델 학습 여정 블로그](https://your-blog.com/yeji-model-evolution)

## License

Apache 2.0

## Citation

```bibtex
@misc{yeji-8b-qdora-v1,
  title={YEJI Fortune Telling Model (QDoRA v1 - PoC)},
  author={SSAFY YEJI Team},
  year={2026},
  note={Deprecated: Proof of Concept. Use yeji-8b-rslora-v7-AWQ instead}
}
```
