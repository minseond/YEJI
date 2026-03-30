# Project Index: YEJI AI Server

> Generated: 2026-02-05
> Version: 0.4.0
> 94% token reduction (58K → 3K tokens)

---

## 📁 Project Structure

```
yeji-ai-server/
├── ai/                           # AI 서버 메인 모듈
│   ├── src/yeji_ai/              # 소스 코드 (95+ files)
│   │   ├── api/                  # API 엔드포인트
│   │   │   ├── v1/fortune/       # 운세 API (핵심)
│   │   │   ├── health.py         # 헬스체크
│   │   │   ├── metrics.py        # Prometheus 메트릭
│   │   │   └── saju.py           # 사주 (레거시)
│   │   ├── clients/              # 외부 클라이언트
│   │   │   ├── redis_client.py   # Redis 캐시
│   │   │   └── vllm_client.py    # vLLM API
│   │   ├── engine/               # 핵심 엔진
│   │   │   ├── saju_calculator.py    # 사주 계산
│   │   │   └── tikitaka_generator.py # 대화 생성
│   │   ├── models/               # Pydantic 모델
│   │   │   ├── enums/            # Enum 정의
│   │   │   └── fortune/          # 운세 스키마
│   │   ├── prompts/              # LLM 프롬프트
│   │   │   ├── character_personas.py # 캐릭터 페르소나
│   │   │   └── tikitaka_prompts.py   # 티키타카 프롬프트
│   │   ├── providers/            # LLM Provider
│   │   │   ├── base.py           # 추상 인터페이스
│   │   │   ├── vllm.py           # vLLM Provider
│   │   │   ├── openai.py         # OpenAI Provider
│   │   │   └── ollama.py         # Ollama Provider
│   │   ├── services/             # 비즈니스 로직 (38 files)
│   │   │   ├── filter/           # 인텐트 필터링
│   │   │   ├── parsers/          # 응답 파싱
│   │   │   └── postprocessor/    # 후처리기
│   │   └── data/                 # 정적 데이터
│   ├── tests/                    # 테스트 (37 files)
│   ├── docs/                     # AI 서버 문서
│   └── pyproject.toml            # 프로젝트 설정
├── docs/                         # 프로젝트 문서
└── Jenkinsfile                   # CI/CD 파이프라인
```

---

## 🚀 Entry Points

| Type | Path | Description |
|------|------|-------------|
| **CLI** | `ai/src/yeji_ai/main.py:main()` | uvicorn 서버 시작 |
| **API** | `ai/src/yeji_ai/main.py:app` | FastAPI 앱 인스턴스 |
| **Config** | `ai/src/yeji_ai/config.py:get_settings()` | 설정 싱글톤 |

---

## 📦 Core Modules

### API Endpoints (`api/v1/fortune/`)

| File | Endpoint | Purpose |
|------|----------|---------|
| `chat.py` | `/chat/turn/*` | 티키타카 대화 API (핵심) |
| `eastern.py` | `/eastern` | 동양 사주 분석 |
| `western.py` | `/western` | 서양 점성술 분석 |
| `tarot.py` | `/tarot` | 타로 카드 분석 |
| `hwatu.py` | `/hwatu` | 화투 운세 |
| `quick_summary.py` | `/quick-summary` | 빠른 요약 |
| `simple.py` | `/simple` | 단순 Q&A |
| `tikitaka.py` | `/tikitaka` | 티키타카 유틸 |
| `demo.py` | `/demo` | 데모/테스트 |

### Services (`services/`)

| File | Class/Function | Purpose |
|------|----------------|---------|
| `tikitaka_service.py` | `TikitakaService` | 티키타카 대화 생성 |
| `eastern_fortune_service.py` | `EasternFortuneService` | 동양 운세 생성 |
| `western_fortune_service.py` | `WesternFortuneService` | 서양 운세 생성 |
| `tarot_service.py` | `TarotService` | 타로 분석 |
| `hwatu_service.py` | `HwatuService` | 화투 운세 |
| `summary_service.py` | `SummaryService` | 운세 요약 |
| `fortune_generator.py` | `FortuneGenerator` | 통합 운세 생성 |
| `llm_interpreter.py` | `LLMInterpreter` | LLM 응답 해석 |
| `provider_manager.py` | `ProviderManager` | LLM Provider 관리 |
| `compound_message_service.py` | - | 복합 메시지 처리 |
| `progressive_cache_service.py` | - | 프로그레시브 캐싱 |

### Providers (`providers/`)

| Provider | Model | Status |
|----------|-------|--------|
| `vllm.py` | yeji-8b-rslora-v7 | Primary |
| `openai.py` | gpt-5-mini | Fallback |
| `ollama.py` | Local models | Optional |

### Postprocessors (`services/postprocessor/`)

| File | Purpose |
|------|---------|
| `eastern.py` | 동양 운세 JSON 정규화 |
| `western.py` | 서양 운세 JSON 정규화 |
| `tarot.py` | 타로 응답 후처리 |
| `bracket_fixer.py` | JSON 괄호 복구 |
| `noise_filter.py` | 노이즈 제거 |
| `prompt_leak_filter.py` | 프롬프트 누출 방지 |
| `character_filter.py` | 캐릭터 말투 필터 |

---

## 🎭 Characters

| Code | Name | Style | Type |
|------|------|-------|------|
| `SOISEOL` | 소이설 | 하오체 | 동양 |
| `STELLA` | 스텔라 | 해요체 | 서양 |
| `CHEONGWOON` | 청운 | 시적 하오체 | 동양 |
| `HWARIN` | 화린 | 나른한 해요체 | 동양 |
| `KYLE` | 카일 | 반말+존댓말 | 서양 |
| `ELARIA` | 엘라리아 | 우아한 해요체 | 서양 |

---

## 🔧 Configuration

| File | Purpose |
|------|---------|
| `pyproject.toml` | 의존성, 빌드, 린트 설정 |
| `.env` | 환경변수 (gitignore) |
| `docker-compose.yml` | Docker 설정 |
| `.gitlab-ci.yml` | GitLab CI/CD |

### Key Settings (`config.py`)

| Setting | Default | Description |
|---------|---------|-------------|
| `vllm_base_url` | localhost:8001 | vLLM 서버 URL |
| `vllm_model` | yeji-8b-rslora-v7 | 모델명 |
| `redis_url` | localhost:6379 | Redis URL |
| `use_gpt5mini_for_chat` | false | GPT-5-mini 사용 여부 |
| `gpu_filter_enabled` | false | GPU 필터 활성화 |

---

## 🔗 Key Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| fastapi | >=0.115.0 | API 프레임워크 |
| pydantic | >=2.10.0 | 데이터 검증 |
| httpx | >=0.28.0 | HTTP 클라이언트 |
| structlog | >=24.4.0 | 구조화 로깅 |
| redis | >=5.0.0 | 캐싱 |
| instructor | >=1.7.0 | LLM 구조화 출력 |
| openai | >=1.60.0 | OpenAI SDK |
| korean-lunar-calendar | >=0.3.1 | 음력 변환 |

---

## 🧪 Test Coverage

| Category | Files | Pattern |
|----------|-------|---------|
| Unit | 35 | `test_*.py` |
| E2E | 1 | `e2e_persona_test.py` |
| Fixtures | 1 | `conftest.py` |

**Run Tests:**
```bash
pytest C:/Users/SSAFY/yeji-ai-server/ai/tests/ -v
```

---

## 📚 Documentation

| Path | Topic |
|------|-------|
| `ai/docs/ARCHITECTURE.md` | 시스템 구조 |
| `ai/docs/PROVIDERS.md` | LLM Provider 가이드 |
| `ai/docs/PYTHON_CONVENTIONS.md` | 코딩 컨벤션 |
| `ai/docs/guides/qwen3-prompting-guide.md` | 프롬프트 가이드 |
| `ai/docs/prd/llm-response-postprocessor.md` | 후처리기 PRD |
| `docs/api/API_USAGE_GUIDE.md` | API 사용 가이드 |

---

## 📝 Quick Start

```bash
# 1. 의존성 설치
cd C:/Users/SSAFY/yeji-ai-server/ai && uv sync

# 2. 환경변수 설정
cp .env.example .env
# VLLM_BASE_URL, REDIS_URL 등 설정

# 3. 서버 실행
uvicorn yeji_ai.main:app --reload --port 8000

# 4. API 문서 확인
# http://localhost:8000/docs
```

---

## 🔀 Branch Strategy

| Branch | Environment | Port |
|--------|-------------|------|
| `ai/main` | Production | 8000 |
| `ai/develop` | Development | 8001 |

---

## 📊 API Flow (Quick Reference)

```
1. POST /v1/fortune/chat/turn/start
   → session_id + greeting

2. POST /v1/fortune/chat/turn/continue
   → 티키타카 대화 진행

3. GET /v1/fortune/chat/summary/{session_id}
   → 운세 요약 조회
```

---

## 📈 Statistics

- Source files: **95+**
- Test files: **37**
- Documentation: **90+**
- Services: **38**

---

_이 인덱스는 세션 시작 시 전체 코드베이스 대신 로드하여 토큰을 절약합니다._
