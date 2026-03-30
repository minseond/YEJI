<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=180&section=header&text=YEJI%20AI%20Server&fontSize=42&fontColor=ffffff&animation=fadeIn&fontAlignY=36&desc=FastAPI%20%2B%20vLLM%20%7C%20Fortune%20%26%20Saju%20Generation&descSize=16&descAlignY=56&v=2" width="100%"/>

<br/>

<img src="./assets/yeji-logo.png" width="80" alt="yeji"/>

<br/>

**AI 기반 운세/사주 생성 서버**

<br/>

[![Python](https://img.shields.io/badge/Python_3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](#)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](#)
[![vLLM](https://img.shields.io/badge/vLLM-FF6F00?style=for-the-badge&logo=pytorch&logoColor=white)](#)
[![Pydantic](https://img.shields.io/badge/Pydantic_v2-E92063?style=for-the-badge&logo=pydantic&logoColor=white)](#)
[![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)](#)

</div>

<br/>

<details>
<summary><strong>목차</strong></summary>

- [개요](#개요)
- [핵심 기능](#핵심-기능)
- [기술 스택](#기술-스택)
- [프로젝트 구조](#프로젝트-구조)
- [시작하기](#시작하기)
- [API 엔드포인트](#api-엔드포인트)
- [LLM Provider 시스템](#llm-provider-시스템)
- [배포](#배포)
- [관련 저장소](#관련-저장소)

</details>

---

## 개요

YEJI AI Server는 동양 사주와 서양 타로를 결합한 운세 생성 엔진입니다. 커스텀 파인튜닝된 LLM(Qwen3 4B)을 vLLM GPU 추론 서버로 서빙하며, FastAPI 기반의 비동기 API를 제공합니다.

> **모델**: `tellang/yeji-4b-instruct-v9-AWQ` (Qwen3 4B 기반, AWQ 4bit 양자화)
> **추론**: vLLM (GPU Memory Utilization 85%, max-model-len 4096)

<p align="right">(<a href="#목차">맨 위로</a>)</p>

---

## 핵심 기능

### 운세 생성
- **동양 운세**: 사주팔자 기반 오늘의 운세 (연애/재물/건강/학업/직업)
- **서양 운세**: 별자리 + 타로 기반 카테고리별 운세
- **타로/화투**: 인터랙티브 카드 선택 기반 즉석 점술
- **궁합 분석**: 두 사람의 동서양 통합 궁합 지수

### 캐릭터 시스템
- **티키타카 대화**: 동양/서양 캐릭터가 주고받는 유머러스한 운세 해석
- **SSE 스트리밍**: 실시간 캐릭터 대화 스트리밍

### 기술 특성
- **LLM Provider 추상화**: vLLM, Ollama, AWS Bedrock, OpenAI 호환 인터페이스
- **구조화된 출력**: Pydantic v2 스키마 기반 JSON 응답 검증 + 후처리기
- **Redis 캐싱**: 운세 결과 캐싱으로 중복 생성 방지
- **프롬프트 최적화**: 토큰 35% 절감 달성 (Phase 1 최적화)

<p align="right">(<a href="#목차">맨 위로</a>)</p>

---

## 기술 스택

| 구분 | 기술 |
|:-----|:-----|
| **Framework** | FastAPI, Python 3.11+ |
| **LLM 추론** | vLLM (GPU 서버), guided_json 모드 |
| **모델** | `tellang/yeji-4b-instruct-v9-AWQ` (Qwen3 4B, AWQ 4bit) |
| **검증** | Pydantic v2, structlog |
| **캐시** | Redis |
| **패키지** | uv (PEP 621 기반) |
| **테스트** | pytest, pytest-asyncio |
| **린트** | ruff |
| **CI/CD** | Jenkins (Docker 자동 배포) |

<p align="right">(<a href="#목차">맨 위로</a>)</p>

---

## 프로젝트 구조

```
ai/src/yeji_ai/
├── api/                          # API 엔드포인트
│   ├── v1/fortune/               #   운세 API
│   │   ├── eastern.py            #     동양 운세
│   │   ├── western.py            #     서양 운세
│   │   ├── chat.py               #     티키타카 채팅
│   │   ├── tarot.py              #     타로
│   │   └── hwatu.py              #     화투
│   ├── router.py                 #   라우터
│   └── health.py                 #   헬스체크
├── engine/                       # 핵심 엔진
│   ├── saju_calculator.py        #   사주 계산기
│   ├── tikitaka_generator.py     #   티키타카 생성기
│   └── prompts.py                #   프롬프트 템플릿
├── providers/                    # LLM Provider
│   ├── base.py                   #   추상 인터페이스
│   ├── vllm.py                   #   vLLM Provider
│   ├── ollama.py                 #   Ollama Provider
│   ├── aws.py                    #   AWS Bedrock
│   └── ssh_adapter.py            #   SSH 터널링
├── models/                       # 데이터 모델
│   ├── enums/                    #   Enum 정의
│   ├── fortune/                  #   운세 모델
│   └── schemas.py                #   공통 스키마
├── services/                     # 비즈니스 로직
│   ├── fortune_generator.py      #   운세 생성 서비스
│   ├── eastern_fortune_service.py#   동양 운세
│   ├── western_fortune_service.py#   서양 운세
│   ├── tikitaka_service.py       #   티키타카
│   └── postprocessor/            #   LLM 응답 후처리
├── config.py                     # 설정 관리
└── main.py                       # FastAPI 진입점
```

<p align="right">(<a href="#목차">맨 위로</a>)</p>

---

## 시작하기

### 요구사항

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (패키지 관리)
- vLLM GPU 서버 (추론용)
- Redis (캐싱용, 선택)

### 설치

```bash
# 의존성 설치
cd ai/
uv sync

# 환경변수 설정
cp .env.example .env
# VLLM_BASE_URL, VLLM_MODEL 등 수정

# 개발 서버 실행
uvicorn yeji_ai.main:app --reload --host 0.0.0.0 --port 8000
```

### 테스트

```bash
# 전체 테스트
pytest tests/ -v

# 커버리지
pytest tests/ -v --cov=yeji_ai --cov-report=html

# 린트
ruff check src/
ruff format src/
```

<p align="right">(<a href="#목차">맨 위로</a>)</p>

---

## API 엔드포인트

| Method | Path | 설명 |
|:------:|:-----|:-----|
| `GET` | `/v1/health` | 헬스체크 |
| `POST` | `/v1/fortune/eastern/analyze` | 동양 운세 생성 |
| `POST` | `/v1/fortune/western/analyze` | 서양 운세 생성 |
| `POST` | `/v1/fortune/eastern/analyze-both` | 동서양 통합 분석 |
| `POST` | `/v1/fortune/tarot/reading` | 타로 카드 해석 |
| `POST` | `/v1/fortune/hwatu/reading` | 화투 카드 해석 |
| `POST` | `/v1/fortune/chat/tikitaka` | 티키타카 대화 (SSE) |
| `POST` | `/v1/fortune/compatibility` | 궁합 분석 |

API 문서: 서버 실행 후 `/docs` (Swagger UI) 또는 `/redoc` (ReDoc) 접속

<p align="right">(<a href="#목차">맨 위로</a>)</p>

---

## LLM Provider 시스템

추상화된 Provider 인터페이스로 다양한 LLM 백엔드를 지원합니다.

```
BaseProvider (추상)
├── VLLMProvider      # 프로덕션 (GPU 추론)
├── OllamaProvider    # 로컬 개발
├── AWSProvider       # AWS Bedrock
└── SSHAdapter        # SSH 터널링 래퍼
```

**프로덕션 설정:**
```bash
VLLM_BASE_URL=http://<GPU_SERVER>:8001
VLLM_MODEL=tellang/yeji-4b-instruct-v9-AWQ
```

<p align="right">(<a href="#목차">맨 위로</a>)</p>

---

## 배포

| 환경 | 브랜치 | 포트 | URL |
|:-----|:------:|:----:|:----|
| Production | `ai/main` | 8000 | `/ai/` |
| Development | `ai/develop_v2` | 8002 | `/ai-dev/` |

Jenkins Webhook 트리거로 자동 배포 (Docker 컨테이너).

<p align="right">(<a href="#목차">맨 위로</a>)</p>

---

## 관련 저장소

| 저장소 | 설명 |
|:-------|:-----|
| [yeji-backend](https://github.com/yeji-service/yeji-backend) | 백엔드 API 서버 (Java 21, Spring Boot 3.4) |
| [yeji-frontend](https://github.com/yeji-service/yeji-frontend) | 프론트엔드 웹 앱 (React 19, Vite) |
| [yeji-code-review](https://github.com/yeji-service/yeji-code-review) | 코드 리뷰 아카이브 (249건) |

---

<div align="center">

**SSAFY 14기 A605팀** | 2026.01 - 02

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=80&section=footer&v=2" width="100%"/>

</div>
