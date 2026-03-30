# YEJI 프로젝트 데이터 전처리 및 학습 의사결정 보고서

> **작성일**: 2026-02-04
> **프로젝트**: YEJI (예지) - 한국어 운세/점술 AI
> **현재 버전**: v8.1 (4B), v7 (8B)

---

## 📍 리소스 위치

| 유형 | 위치 | 설명 |
|------|------|------|
| **전처리 코드** | `tellang/yeji-preprocessor` (GitHub Private) | 데이터 파이프라인 |
| **학습 노트북** | `tellang/yeji-training-notebooks` (GitHub Private) | 30개+ 노트북 |
| **HF 노트북** | `tellang/yeji-training-notebooks` (HF Dataset) | 2개 공개 노트북 |
| **학습 데이터** | `tellang/yeji-fortune-telling-ko-v3` (HF) | 33,528건 |
| **정제 데이터** | `tellang/yeji-processed` (HF) | 24,961건 |
| **메타 허브** | `tellang/yeji-meta` (HF) | 8건 (메타 정보) |
| **8B 모델** | `tellang/yeji-8b-rslora-v7-AWQ` (HF) | 프로덕션 |
| **4B 모델** | `tellang/yeji-4b-rslora-v8.1` (HF) | 경량 배포 |

---

## 1️⃣ 선택된 데이터

### 최종 사용 데이터셋: `yeji-fortune-telling-ko-v3` (33,528건)

| 도메인 | 샘플 수 | 비율 | 출처 | 특징 |
|--------|---------|------|------|------|
| **Astrology** | 18,470 | 55.1% | `horoscope_saved` | 영→한 번역, 일관된 품질 |
| **Bazi (사주)** | 8,437 | 25.2% | `gpt5mini_synthesized` | GPT-3.5 합성, 체계적 구조 |
| **Tarot** | 6,621 | 19.7% | `gemini-3-flash` | Gemini 합성, 심층 분석 |

### 데이터 품질 지표

| 지표 | 값 |
|------|-----|
| 총 토큰 수 | ~29,255,743 |
| 평균 샘플 길이 | 872.6 토큰 |
| 완전성 (Instruction) | 100% |
| 완전성 (Output) | 100% |
| Output/Instruction 비율 | 13.20x |

---

## 2️⃣ 왜 이 데이터가 선택되었나?

### 핵심 선택 이유

| 결정 | 이유 | 근거 |
|------|------|------|
| **GPT/Gemini 합성 데이터** | 고품질 + 비용 효율 | $21로 87K건 (건당 $0.00024) |
| **3개 도메인 통합** | 점술 AI 다양성 | 사주, 타로, 점성술 커버 |
| **한국어 번역 포함** | 다국어 톤 학습 | horoscope.com 원본 번역 |
| **Alpaca 포맷** | Qwen3 호환 | instruction + input + output |

### 업계 벤치마크 기반 판단

| 사례 | 데이터 규모 | YEJI 비교 |
|------|-------------|-----------|
| Stanford Alpaca | 52,000건 | ✅ 충분 |
| LIMA (Meta) | 1,000건 | ✅ 35배 많음 |
| OpenAI 권장 | 수백~수천 건 | ✅ 기준 초과 |

**결론**: "양은 충분, 품질이 핵심"

---

## 3️⃣ 선택되지 않은 방식과 이유

### 🚫 데이터 관련

| 방식 | 선택 안 한 이유 | 교훈 |
|------|----------------|------|
| 중국어 262K 전체 사용 | 번역 비용/시간 과다 | 50K 샘플링으로 충분 |
| 사주 계산 50K 유지 | 도메인 불균형 (57%) | 해석 능력이 목표 |
| Input 필드 활용 | 모든 샘플 빈 문자열 | 향후 개선 여지 |

### 🚫 학습 방식 관련

| 버전 | 시도한 방식 | 결과 | 폐기 이유 |
|------|------------|------|----------|
| **v4** | T-SHIRT 20% 선택 | ❌ 0% 개선 | "어려운 데이터 ≠ 좋은 데이터" |
| **v3** | DoRA (r=16) | ⚠️ vLLM 배포 불가 | vLLM이 DoRA 미지원 |
| **v6** | DoRA (r=32) | ❌ 0.03 it/s | CPU offload, 너무 느림 |
| **v8** | tokenizer.apply_chat_template() | ❌ `<think>` 태그 발생 | Unsloth 버그 |

---

## 4️⃣ 버전 히스토리 (전체)

### 8B 모델 계열

| 버전 | 기법 | 결과 | 상태 |
|------|------|------|------|
| **v7** | rsLoRA r=64 | ✅ 0.25 it/s, vLLM 호환 | **프로덕션** |
| v6 | DoRA r=32 | ❌ 0.03 it/s, offload | 중단 |
| v5 | rsLoRA + ORPO | ✅ 언어 혼란 해결 | - |
| v4 | T-SHIRT 20% | ❌ 0% 개선, 베트남어 출력 | 폐기 |
| v3 | DoRA r=16 | ⚠️ vLLM 미지원 | 폐기 |
| v2 | QLoRA | ✅ 기본 동작 | - |
| v1 | QLoRA Unsloth | ✅ 파이프라인 검증 | - |

### 4B 모델 계열 (경량)

| 버전 | 베이스 모델 | 변경점 | 결과 |
|------|------------|--------|------|
| **v8.1** | Qwen3-4B-Instruct-2507 | 직접 ChatML 포맷 | ✅ `<think>` 없음 |
| v8 | Qwen3-4B-Instruct-2507 | tokenizer.apply_chat_template() | ❌ `<think>` 발생 |
| v7 | Qwen3-4B (2504) | Hybrid thinking | ❌ `<think>` 발생 |

### v7 vs v8 vs v8.1 비교

| 항목 | v7 (4B) | v8 (4B) | v8.1 (4B) |
|------|---------|---------|-----------|
| Base Model | Qwen3-4B (2504) | Qwen3-4B-Instruct-2507 | Qwen3-4B-Instruct-2507 |
| Thinking Mode | Hybrid (불안정) | Non-thinking | Non-thinking |
| 포맷 | apply_chat_template | apply_chat_template | **직접 ChatML** |
| `<think>` 태그 | ❌ 발생 | ❌ 발생 | ✅ **없음** |
| 상태 | 폐기 | 폐기 | **사용 중** |

---

## 5️⃣ DoRA vs rsLoRA 최종 결정

### 비교 분석

| 항목 | DoRA | rsLoRA r=64 | 선택 |
|------|------|-------------|------|
| 이론적 품질 | +4.4% | +3~4% | 동등 |
| 실제 속도 | 0.03 it/s | **0.25 it/s** | **10배 빠름** |
| vLLM 호환 | ❌ | **✅** | **rsLoRA** |
| A100 안정성 | CPU offload | **안정** | **rsLoRA** |
| 메모리 오버헤드 | +25% | +50% (r=64) | 허용 범위 |

### 결론

> **DoRA가 이론적으로 우수하지만, vLLM 미지원 + 느린 속도로 인해 rsLoRA 선택**

---

## 6️⃣ 데이터 전처리 파이프라인

### 전체 흐름

```
┌─────────────────────────────────────────────────────────┐
│ 1. 원본 데이터 수집                                      │
│    • horoscope.com (영어 → 한국어 번역)                  │
│    • GPT-3.5 Mini 합성 (gpt5mini_synthesized)            │
│    • Gemini Flash 합성 (gemini-3-flash)                  │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│ 2. 중국어 → 한국어 번역 (262K → 50K 샘플링)              │
│    • 모델: Qwen 2.5                                      │
│    • 대상: czuo03/bazi-calculate-rlvr                    │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│ 3. 데이터 정제                                           │
│    • 중복 제거                                           │
│    • 품질 검증 (99% 통과)                                │
│    • Alpaca 포맷 통일                                    │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│ 4. Chat Template 변환                                    │
│    • v7: tokenizer.apply_chat_template()                 │
│    • v8.1: 직접 ChatML 포맷 (Unsloth 버그 우회)          │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│ 5. Train/Eval Split (95:5, seed=42)                      │
└─────────────────────────────────────────────────────────┘
```

### 핵심 전처리 코드

#### Alpaca → Chat Template (v7)

```python
def format_alpaca(example):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": example["instruction"]},
        {"role": "assistant", "content": example["output"]},
    ]
    return {
        "text": tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=False
        )
    }
```

#### 직접 ChatML (v8.1 - Unsloth 버그 우회)

```python
def format_to_chatml(example):
    """직접 ChatML 포맷 - <think> 태그 없음"""
    text = f"""<|im_start|>system
{SYSTEM_PROMPT}<|im_end|>
<|im_start|>user
{example["instruction"]}<|im_end|>
<|im_start|>assistant
{example["output"]}<|im_end|>"""
    return {"text": text}
```

---

## 7️⃣ 학습 설정 (최종)

### 8B 모델 (v7)

```python
CONFIG = {
    "base_model": "Qwen/Qwen3-8B-Base",
    "lora_r": 64,
    "lora_alpha": 128,
    "use_rslora": True,
    "use_dora": False,
    "per_device_train_batch_size": 2,
    "gradient_accumulation_steps": 16,
    "num_epochs": 3,
    "learning_rate": 2e-4,
}
```

### 4B 모델 (v8.1)

```python
CONFIG = {
    "base_model": "Qwen/Qwen3-4B-Instruct-2507",
    "lora_r": 64,
    "lora_alpha": 128,
    "use_rslora": True,
    "use_dora": False,
    "per_device_train_batch_size": 4,
    "gradient_accumulation_steps": 4,
    "num_epochs": 5,
    "learning_rate": 3e-5,
}
```

---

## 8️⃣ 핵심 교훈

| 교훈 | 상세 |
|------|------|
| **배포 환경 먼저 확인** | DoRA 좋아도 vLLM 미지원이면 사용 불가 |
| **이론 ≠ 실제** | DoRA +4.4%이지만 10배 느림 → rsLoRA |
| **데이터 선택 ≠ 품질** | T-SHIRT "어려운 데이터"가 오히려 노이즈 |
| **합성 데이터 효과적** | $21로 87K건 고품질 데이터 생성 가능 |
| **Unsloth 버그 주의** | apply_chat_template에서 `<think>` 태그 발생 |
| **직접 포맷 생성** | 라이브러리 버그 우회 시 직접 구현 |

---

## 9️⃣ 관련 문서 경로

```
tellang/yeji-preprocessor/
├── README.md                    # 프로젝트 개요
├── ANALYSIS_REPORT.md           # 코드 리뷰 (⭐4.5/5)
├── DATASET_QUALITY_REPORT.md    # v3 품질 분석
└── docs/
    ├── PRD.md                   # 전체 PRD
    ├── RESEARCH_REPORT_TRAINING_DATA.md
    ├── PRD_BAZI_SYNTHESIS.md
    └── PRD_TAROT_ENHANCEMENT.md

tellang/yeji-training-notebooks/
├── CHANGELOG.md                 # 버전별 변경 이력 (핵심!)
├── PROJECT_INDEX.md             # 노트북 인덱스
├── phase4_yeji_v7_rslora.ipynb  # v7 8B 학습
├── phase4_yeji_v8_4b_rslora.ipynb # v8 4B 학습
├── phase4_yeji_v8.1_4b_rslora.ipynb # v8.1 4B 학습 (최신)
└── docs/
    └── dora_vs_rslora_analysis.md
```

---

## 🔗 HuggingFace 리소스

### 모델

| 모델 | 크기 | 용도 | 상태 |
|------|------|------|------|
| `tellang/yeji-8b-rslora-v7-AWQ` | ~4GB | 프로덕션 (8B) | ✅ |
| `tellang/yeji-8b-rslora-v7` | ~16GB | Full Precision | ✅ |
| `tellang/yeji-4b-rslora-v8.1` | ~8GB | 경량 배포 (4B) | ✅ |
| `tellang/yeji-4b-rslora-v8-AWQ-fixed` | ~1.5GB | 4B AWQ | ✅ |

### 데이터셋

| 데이터셋 | 샘플 수 | 용도 |
|---------|---------|------|
| `tellang/yeji-meta` | 8 | 메타 정보 허브 |
| `tellang/yeji-fortune-telling-ko-v3` | 33,528 | v7/v8 학습용 |
| `tellang/yeji-processed` | 24,961 | 정제 데이터 |
| `tellang/yeji-preference-ko-v1` | 33,528 | RLHF용 |

---

**문서 버전**: 1.0
**최종 수정**: 2026-02-04
**작성자**: Claude Code + tellang
