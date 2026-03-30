# YEJI AI Server - 프로젝트 진행 현황

```
┌─────────────────────────────────────────────────────────────────┐
│  YEJI AI - 동양(사주팔자) + 서양(별자리) 융합 운세 AI 서버     │
│  Last Updated: 2026-01-28 (Provider 리팩터링 완료)              │
└─────────────────────────────────────────────────────────────────┘
```

## 전체 진행률

```
[██████████████████████████████████████████████████] 98%

Phase 1: 기반 구축        [████████████████████] 100% ✅
Phase 2: 핵심 기능        [████████████████████] 100% ✅
Phase 3: 테스트/QA        [████████████████████] 100% ✅
Phase 4: 배포/운영        [██████████████████░░]  90% ⏳ (Provider 시스템 완료)
```

---

## 버그픽스 스프린트 결과 (2025-01-22)

```
┌──────────────────────────────────────────────────────┐
│  총 8개 이슈 수정 완료                                │
│  HIGH: 2/2 ✅  MEDIUM: 3/3 ✅  LOW: 3/3 ✅          │
│  테스트: 8/8 passed                                  │
└──────────────────────────────────────────────────────┘
```

### 수정된 이슈 상세

| ID | 우선순위 | 설명 | 파일 | 상태 |
|----|----------|------|------|------|
| HIGH-1 | 🔴 | saju_profile 실제 사용 연동 | saju_service.py | ✅ |
| HIGH-2 | 🔴 | TTL 기반 세션 캐시 (30분) | saju_service.py | ✅ |
| MEDIUM-1 | 🟡 | asyncio.Event 메모리 누수 | saju_service.py | ✅ |
| MEDIUM-2 | 🟡 | 별자리 경계일 로직 | saju_calculator.py | ✅ |
| MEDIUM-3 | 🟡 | CORS 메소드 명시 | main.py | ✅ |
| LOW-1 | 🟢 | 세션 ID full UUID (32자) | api/saju.py | ✅ |
| LOW-2 | 🟢 | 프로덕션 에러 메시지 | saju_service.py | ✅ |
| LOW-3 | 🟢 | lifespan 컨텍스트 | main.py | ✅ |

---

## Phase 1: 기반 구축 ✅ DONE

```
[✅] FastAPI 앱 셋업 (lifespan 패턴 적용)
[✅] 설정 관리 (Pydantic Settings)
[✅] vLLM OpenAI-compatible 클라이언트
[✅] 프로젝트 구조
```

---

## Phase 2: 핵심 기능 ✅ DONE

```
[✅] 사주팔자 계산 엔진 (실제 계산 연동)
[✅] 티키타카 대화 생성기
[✅] API 엔드포인트
[✅] Pydantic v2 스키마
```

---

## Phase 3: 테스트/QA ✅ DONE

```
[✅] pytest 테스트 프레임워크 (8/8 통과)
[✅] 통합 테스트 (Manual)
[✅] 코드 리뷰/버그 바운티 완료
[✅] 보안 이슈 수정 완료
[⏳] 커버리지 80% 목표 (측정 필요)
```

---

## Phase 4: 배포/운영 ⏳ IN PROGRESS

```
[✅] Dockerfile
[✅] .gitlab-ci.yml
[✅] vLLM 실제 연동 구현 (프롬프트 템플릿, 해석 생성)
[✅] LLM Provider 시스템 (vLLM/Ollama/AWS 통합)
[⏳] vLLM GPU 서버 셋업 (Runpod/Lambda Labs)
[⏳] GitLab 푸시 (ai/develop)
[⏳] 프로덕션 배포
```

---

## LLM Provider 시스템 구현 + 리팩터링 (2026-01-28)

```
┌──────────────────────────────────────────────────────┐
│  다양한 LLM 백엔드 통합 관리 시스템 구현 + 리팩터링  │
│  VLLMProvider + OllamaProvider + AWSProvider         │
│  SSH 원격 제어, GPU 모니터링, 자동 시작/중지         │
│  P0 버그 수정 + P1 안정성 개선 완료                  │
└──────────────────────────────────────────────────────┘
```

### 추가된 파일
```
src/yeji_ai/providers/
├── __init__.py       # 모듈 export
├── base.py           # 추상 인터페이스
├── ssh_adapter.py    # SSH 원격 커맨드 실행
├── vllm.py           # VLLMProvider
├── ollama.py         # OllamaProvider
└── aws.py            # AWSProvider
```

### 구현 내용
| 기능 | 설명 | 상태 |
|------|------|------|
| LLMProvider 추상화 | start/stop/status/health/chat 인터페이스 | ✅ |
| SSHAdapter | 원격 서버 커맨드 실행, WSL 지원 | ✅ |
| VLLMProvider | 로컬/원격 vLLM 서버 연동 | ✅ |
| OllamaProvider | Ollama 자동 시작/모델 풀 | ✅ |
| AWSProvider | EC2 시작/중지, SSH 터널 | ✅ |
| 테스트 | 32개 테스트 통과 | ✅ |

### 리팩터링 (2026-01-28)
| 항목 | 설명 | 상태 |
|------|------|------|
| P0-1 | `or` → `is not None` (temperature=0 버그) | ✅ |
| P0-2 | AWSProvider.stop() 시그니처 수정 | ✅ |
| P1-2 | Ollama async subprocess 전환 | ✅ |
| 테스트 | 7개 신규 테스트 추가 (25 → 32) | ✅ |

### 문서화
- `docs/PROVIDERS.md` - 상세 사용 가이드
- `docs/workflow/PROVIDER_SUMMARY.md` - 구현 요약
- `docs/pdca/provider-refactor/` - 리팩터링 PDCA 문서

---

## vLLM 연동 구현 (2025-01-22)

```
┌──────────────────────────────────────────────────────┐
│  vLLM OpenAI-compatible API 연동 완료                │
│  프롬프트 템플릿 + 해석 생성 로직 구현              │
│  Fallback: vLLM 미연결시 Mock 모드 자동 전환        │
└──────────────────────────────────────────────────────┘
```

### 추가된 파일
- `src/yeji_ai/engine/prompts.py` - 프롬프트 템플릿 모듈

### 구현 내용
| 기능 | 설명 | 상태 |
|------|------|------|
| 동양 해석 생성 | saju_profile 기반 vLLM 프롬프트 | ✅ |
| 서양 해석 생성 | 별자리 기반 vLLM 프롬프트 | ✅ |
| 통합 의견 생성 | 동양+서양 융합 메시지 | ✅ |
| 맞춤 조언 생성 | 카테고리별 실용 조언 | ✅ |
| Fallback 처리 | vLLM 미연결시 Mock 모드 | ✅ |

---

## 다음 액션 (TODO)

```
Priority 1 (즉시):
  [ ] GitLab ai/develop 푸시
  [ ] vLLM GPU 서버 셋업 (Runpod/Lambda Labs)

Priority 2 (다음 단계):
  [ ] 실제 LLM 생성 테스트 (GPU 서버 연결 후)
  [ ] 테스트 커버리지 측정
  [ ] 프로덕션 배포
```

---

## 명령어 Quick Reference

```bash
# 개발 환경
uv sync                              # 의존성 설치
uv run yeji-ai                       # 서버 실행 (CLI)
uv run uvicorn yeji_ai.main:app      # 서버 실행 (직접)

# 테스트
uv run pytest tests/ -v              # 전체 테스트
uv run pytest --cov=yeji_ai          # 커버리지

# 린트
uv run ruff check src/               # 린트 체크
uv run ruff format src/              # 포맷팅

# Docker
docker build -t yeji-ai:latest .     # 이미지 빌드
docker run -p 8000:8000 yeji-ai      # 컨테이너 실행
```

---

## 파일 구조

```
yeji-ai-server/
├── src/yeji_ai/
│   ├── api/
│   │   ├── health.py
│   │   ├── router.py
│   │   └── saju.py            # [수정] full UUID
│   ├── clients/
│   │   └── vllm_client.py
│   ├── engine/
│   │   ├── prompts.py         # [신규] 프롬프트 템플릿
│   │   ├── saju_calculator.py # [수정] 별자리 로직
│   │   └── tikitaka_generator.py
│   ├── models/
│   │   ├── saju.py
│   │   └── schemas.py
│   ├── services/
│   │   └── saju_service.py    # [수정] TTL 캐시, saju_profile
│   ├── config.py
│   └── main.py                # [수정] lifespan, CORS
├── tests/
├── docs/
│   ├── workflow/
│   │   └── PROGRESS.md        # 이 파일
│   └── pdca/
│       └── bugfix-sprint/     # 버그픽스 PDCA 문서
│           ├── plan.md
│           ├── do.md
│           └── check.md
├── Dockerfile
├── .gitlab-ci.yml
├── pyproject.toml
└── .env.example
```

---

```
Generated: 2025-01-22
Status: Phase 4 진행 중 (96%)
Completed: 버그픽스 8개, vLLM 연동
Next: GitLab 푸시, GPU 서버 셋업
```
