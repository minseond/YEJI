# YEJI AI Server 아키텍처

> 동양(사주팔자) + 서양(별자리) 융합 운세 AI 서버

## 시스템 개요

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           YEJI AI System                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐     ┌──────────────────┐     ┌──────────────────┐   │
│  │   Frontend   │────▶│  FastAPI Server  │────▶│   vLLM Server    │   │
│  │  (Next.js)   │     │   (yeji-ai)      │     │  (Qwen3-4B-AWQ)  │   │
│  │  :3000       │     │   :8000          │     │  :8001           │   │
│  └──────────────┘     └──────────────────┘     └──────────────────┘   │
│                               │                        │               │
│                               │                        │               │
│                       ┌───────▼───────┐       ┌───────▼───────┐       │
│                       │  사주 계산기   │       │  (예정)        │       │
│                       │  SajuCalc     │       │  분류기 0.6B   │       │
│                       └───────────────┘       │  :8002         │       │
│                                               └───────────────┘       │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## 인프라 구성

### 서버 정보

| 구분 | 호스트 | 포트 | 설명 |
|------|--------|------|------|
| FastAPI 서버 | localhost | 8000 | YEJI AI API 서버 |
| vLLM (메인) | 100.114.13.51 (ultra4) | 8001 | Qwen3-4B-AWQ 모델 |
| vLLM (분류기) | 100.114.13.51 (ultra4) | 8002 | Qwen3-0.6B (예정) |
| Tailscale VPN | 100.114.13.51 | - | ultra4 접속용 |

### GPU 서버 (ultra4)

- **GPU**: RTX 4070 Laptop (8GB VRAM)
- **환경**: WSL2 Ubuntu
- **vLLM**: 0.13.0
- **Python**: 3.11

## 프로젝트 구조

```
yeji-ai-server/
├── pyproject.toml              # 프로젝트 설정
├── chat.py                     # CLI 티키타카 채팅 (개발/테스트용)
│
├── src/yeji_ai/
│   ├── main.py                 # FastAPI 앱 진입점
│   ├── config.py               # 설정 (pydantic-settings)
│   │
│   ├── api/                    # API 엔드포인트
│   │   ├── router.py           # 라우터 통합
│   │   ├── health.py           # 헬스체크 API
│   │   └── saju.py             # 사주/운세 API
│   │
│   ├── clients/                # 외부 클라이언트
│   │   └── vllm_client.py      # vLLM OpenAI-compatible 클라이언트
│   │
│   ├── engine/                 # 핵심 엔진
│   │   ├── tikitaka_generator.py  # 티키타카 대화 생성
│   │   ├── saju_calculator.py     # 사주 계산
│   │   └── prompts.py             # 프롬프트 템플릿
│   │
│   ├── models/                 # 데이터 모델
│   │   ├── schemas.py          # API 스키마 (Pydantic)
│   │   └── saju.py             # 사주 데이터 모델
│   │
│   └── services/               # 비즈니스 로직
│       └── saju_service.py     # 사주 서비스
│
├── docs/                       # 문서
│   ├── ARCHITECTURE.md         # 이 문서
│   ├── pdca/                   # PDCA 문서
│   └── workflow/               # 워크플로우 문서
│
└── tests/                      # 테스트
```

## 핵심 컴포넌트

### 1. vLLM 클라이언트 (`clients/vllm_client.py`)

vLLM OpenAI-compatible API 클라이언트.

```python
class VLLMClient:
    """vLLM OpenAI-compatible API 클라이언트"""

    async def generate(prompt, config) -> CompletionResponse
    async def generate_stream(prompt, config) -> AsyncIterator[str]
    async def chat(messages, config) -> CompletionResponse
    async def chat_stream(messages, config) -> AsyncIterator[str]
```

**설정:**
- `base_url`: vLLM 서버 URL (기본: http://localhost:8001)
- `model`: 모델 ID (기본: tellang/yeji-8b-lora-v5)
- `timeout`: 요청 타임아웃 (기본: 120초)

### 2. 티키타카 제너레이터 (`engine/tikitaka_generator.py`)

동양(도사) ↔ 서양(점성술사) 토론 형식 대화 생성.

```python
class TikitakaGenerator:
    """티키타카 대화 생성기"""

    async def generate_discussion(session_id, session, saju_result, ...) -> AsyncIterator[str]
    async def generate_chat_response(session, saju_result, user_message) -> list[ChatMessage]
```

**대화 흐름:**
1. 도사와 점성술사가 번갈아 발언 (3턴)
2. 중간에 사용자 질문 삽입
3. 합의/비합의 판단 후 후속 질문 또는 선택지 제시

### 3. CLI 채팅 (`chat.py`)

개발/테스트용 Rich 기반 CLI 채팅 인터페이스.

```
┌─────────────────────────────────────────────────────────────────┐
│                  ✨ YEJI 티키타카 토론 ✨                        │
├─────────────────────────────────────────────────────────────────┤
│  🌟 별빛 소녀 (왼쪽/파란색) ◄──► 🏮 철학관 할아버지 (오른쪽/빨간색)  │
│                         👤 나 (가운데/초록색)                    │
└─────────────────────────────────────────────────────────────────┘
```

**기능:**
- 3턴 티키타카 토론
- 합의/비합의 판단
- 선택형 질문 (의견이 다를 때)

## vLLM 서버 실행

### 단일 서버 (4B 메인)

```bash
# WSL 진입
wsl

# venv 활성화
source ~/venvs/vllm/bin/activate

# vLLM 서버 실행
vllm serve Qwen/Qwen3-4B-AWQ \
  --port 8001 \
  --max-model-len 4096 \
  --enforce-eager \
  --gpu-memory-utilization 0.70
```

### 듀얼 서버 (4B + 0.6B 분류기)

```bash
# tmux 세션 생성
tmux new -s vllm

# 메인 서버 (4B)
source ~/venvs/vllm/bin/activate
vllm serve Qwen/Qwen3-4B-AWQ \
  --port 8001 \
  --max-model-len 4096 \
  --enforce-eager \
  --gpu-memory-utilization 0.50

# Ctrl+B, C (새 창)

# 분류 서버 (0.6B)
source ~/venvs/vllm/bin/activate
vllm serve Qwen/Qwen3-0.6B \
  --port 8002 \
  --max-model-len 1024 \
  --enforce-eager \
  --gpu-memory-utilization 0.15

# Ctrl+B, D (분리)
```

**VRAM 배분:**
- 4B: 50% (~4GB)
- 0.6B: 15% (~1.2GB)
- 여유: ~2.8GB

## Qwen3 모델 설정

### 권장 파라미터 (Non-thinking 모드)

```python
{
    "temperature": 0.7,
    "top_p": 0.8,
    "top_k": 20,
    "min_p": 0,
    "presence_penalty": 1.5,   # 반복 방지
    "frequency_penalty": 0.5,  # 반복 방지
}
```

### 프롬프트 팁

1. **`/no_think`**: 시스템 프롬프트 시작에 추가하여 thinking 모드 비활성화
2. **`<think>` 태그 제거**: 출력에 `<think>` 태그가 포함되면 제거
3. **짧은 지시**: 2문장 이하로 간결하게 지시

## 인텐트 분류 시스템 (예정)

### 분류 카테고리

| 인텐트 | 예시 | 처리 |
|--------|------|------|
| `birth_info` | "1997년 10월 24일생" | 정보 저장 |
| `fortune` | "연애운 알려줘" | 토론 시작 |
| `greeting` | "안녕" | 인사 응답 |
| `unsafe` | 탈옥 시도 | 거절 |
| `off_topic` | 주제 벗어남 | 안내 |

### 구현 방식

```python
CLASSIFIER_PROMPT = """/no_think
사용자 입력을 분류하세요.
카테고리: birth_info, fortune, greeting, unsafe, off_topic
출력: 카테고리명만
"""

def classify(user_input: str) -> str:
    response = call_llm([
        {"role": "system", "content": CLASSIFIER_PROMPT},
        {"role": "user", "content": user_input}
    ], max_tokens=20)
    return response.strip().lower()
```

## 환경 변수

```bash
# .env
VLLM_BASE_URL=http://100.114.13.51:8001
VLLM_MODEL=Qwen/Qwen3-4B-AWQ
VLLM_MAX_TOKENS=2048
VLLM_TEMPERATURE=0.7
VLLM_TOP_P=0.9

HOST=0.0.0.0
PORT=8000
DEBUG=true
LOG_LEVEL=INFO

BACKEND_URL=http://localhost:8081
CORS_ORIGINS=["http://localhost:3000", "https://i14a605.p.ssafy.io"]
```

## 의존성

### 메인 의존성

```toml
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "pydantic>=2.10.0",
    "pydantic-settings>=2.6.0",
    "httpx>=0.28.0",
    "sse-starlette>=2.2.0",
    "korean-lunar-calendar>=0.3.1",
    "python-dateutil>=2.9.0",
    "structlog>=24.4.0",
    "rich>=14.2.0",
]
```

### 개발 의존성

```toml
dev = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
    "pytest-cov>=6.0.0",
    "ruff>=0.8.0",
]
```

## 참고 문서

- [Qwen3 Best Practices](https://qwen.readthedocs.io/)
- [vLLM Documentation](https://docs.vllm.ai/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
