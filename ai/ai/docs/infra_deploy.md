# YEJI 인프라 배포 문서

> 생성일: 2026-01-27
> 최종 수정: 2026-02-03
> 상태: 운영 중

---

## 목차

1. [현재 배포 상태](#1-현재-배포-상태)
2. [인프라 구성](#2-인프라-구성)
3. [Nginx 설정](#3-nginx-설정)
4. [Docker 배포 커맨드](#4-docker-배포-커맨드)
5. [AWS GPU 서버 구성](#5-aws-gpu-서버-구성)
6. [환경변수 가이드](#6-환경변수-가이드)
7. [헬스체크 엔드포인트](#7-헬스체크-엔드포인트)
8. [보안 규칙 요약](#8-보안-규칙-요약)
9. [Jenkins CI/CD 파이프라인](#9-jenkins-cicd-파이프라인)
10. [롤백 절차](#10-롤백-절차)
11. [GPU 필터 배포](#11-gpu-필터-배포)
12. [문제 해결](#12-문제-해결)
13. [다음 단계](#13-다음-단계)

---

## 1. 현재 배포 상태

| 서비스 | URL | 상태 | 포트 |
|--------|-----|------|------|
| **Frontend** | https://i14a605.p.ssafy.io/ | ⏳ 미배포 (502) | 3000 |
| **Backend** | https://i14a605.p.ssafy.io/api | ✅ 배포됨 | 8081 |
| **AI Server (Prod)** | https://i14a605.p.ssafy.io/ai/v1/health | ✅ 배포됨 | 8000 |
| **AI Server (Dev)** | https://i14a605.p.ssafy.io/ai-dev/v1/health | ✅ 배포됨 | 8002 |
| **AI Server (Ultra4)** | https://i14a605.p.ssafy.io/ai-ultra4/v1/health | ✅ 배포됨 | 8003 |
| **vLLM GPU (8B)** | http://13.125.68.166:8001 | ✅ 운영 중 | 8001 |

---

## 2. 인프라 구성

```
┌─────────────────────────────────────────────────────────────────┐
│  SSAFY EC2 (i14a605.p.ssafy.io / 52.78.174.197)                 │
│  ───────────────────────────────────────────────────────────    │
│  Ubuntu 24.04.3 LTS | 4 vCPU | 16GB RAM | 309GB Disk           │
│  ───────────────────────────────────────────────────────────    │
│                                                                 │
│  ┌──────────────┐                                               │
│  │    Nginx     │ :443 (HTTPS)                                  │
│  │  ──────────  │                                               │
│  │  /         → :3000 (Frontend)                                │
│  │  /api      → :8081 (Backend)                                 │
│  │  /ai       → :8000 (AI Prod)                                 │
│  │  /ai-dev   → :8002 (AI Dev)                                  │
│  │  /ai-ultra4→ :8003 (AI Ultra4)                               │
│  └──────────────┘                                               │
│         │                                                       │
│         ├──────────┬──────────┬──────────┬──────────┐          │
│         ▼          ▼          ▼          ▼          ▼          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐│
│  │ Frontend │ │ Backend  │ │ AI Prod  │ │ AI Dev   │ │AI Ultra││
│  │  :3000   │ │  :8081   │ │  :8000   │ │  :8002   │ │ :8003  ││
│  │ (미배포) │ │ (Docker) │ │ (Docker) │ │ (Docker) │ │(Docker)││
│  └──────────┘ └──────────┘ └────┬─────┘ └────┬─────┘ └───┬────┘│
│                                 │            │                  │
│  ┌──────────────────────────────┴────────────┴──────────────┐  │
│  │ Jenkins :8080 | Gerrit :8988 | Docker 29.1.5             │  │
│  └──────────────────────────────┬───────────────────────────┘  │
└─────────────────────────────────┼───────────────────────────────┘
                                  │ HTTP (OpenAI API)
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│  AWS EC2 g5.xlarge (13.125.68.166 - Elastic IP)                 │
│  ───────────────────────────────────────────────────────────    │
│  GPU: NVIDIA A10G 24GB | Ubuntu 22.04 Deep Learning AMI        │
│  ───────────────────────────────────────────────────────────    │
│                                                                 │
│  ┌──────────────────┐                                          │
│  │  vLLM Server     │ :8001                                     │
│  │  ──────────────  │                                          │
│  │  모델: tellang/yeji-8b-rslora-v7-AWQ (8B, AWQ 양자화)        │
│  │  max-model-len: 2048                                        │
│  │  gpu-memory-utilization: 0.90                               │
│  └──────────────────┘                                          │
│                                                                 │
│  Security Group: SSAFY EC2 IP (52.78.174.197/32) 만 허용       │
└─────────────────────────────────────────────────────────────────┘
```

### 배포 환경 분기

| 브랜치 | 환경 | 컨테이너명 | 포트 | ROOT_PATH | 설명 |
|--------|------|------------|------|-----------|------|
| `ai/main` | Production | `yeji-ai-prod` | 8000 | `/ai` | 프로덕션 배포 |
| `ai/develop` | Development | `yeji-ai-dev` | 8002 | `/ai-dev` | 개발 테스트용 |
| `ai/ultra4` | Ultra4 | `yeji-ai-ultra4` | 8003 | `/ai-ultra4` | GPT-5-mini 채팅 전용 |

---

## 3. Nginx 설정

### 적용본: `/etc/nginx/sites-available/yeji`

```nginx
# YEJI 통합 Nginx 설정
# 생성일: 2026-01-27

# Upstream 정의
upstream frontend {
    server 127.0.0.1:3000;
    keepalive 32;
}

upstream backend {
    server 127.0.0.1:8081;
    keepalive 32;
}

upstream ai_server {
    server 127.0.0.1:8000;
    keepalive 32;
}

# HTTP → HTTPS 리다이렉트
server {
    listen 80;
    listen [::]:80;
    server_name i14a605.p.ssafy.io;
    return 301 https://$host$request_uri;
}

# 메인 HTTPS 서버
server {
    listen 443 ssl;
    listen [::]:443 ssl;
    server_name i14a605.p.ssafy.io;

    # SSL 설정
    ssl_certificate /etc/letsencrypt/live/i14a605.p.ssafy.io/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/i14a605.p.ssafy.io/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # 로그
    access_log /var/log/nginx/yeji_access.log;
    error_log /var/log/nginx/yeji_error.log;

    # 공통 프록시 헤더
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    # Backend API (/api)
    location /api {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_read_timeout 60s;
        proxy_send_timeout 60s;
    }

    # AI Server (/ai/)
    location /ai/ {
        proxy_pass http://ai_server/;
        proxy_http_version 1.1;
        proxy_set_header Connection "";

        # LLM 응답 대기를 위한 긴 타임아웃
        proxy_read_timeout 120s;
        proxy_send_timeout 120s;
        proxy_connect_timeout 30s;

        # SSE(Server-Sent Events) 지원
        proxy_buffering off;
        proxy_cache off;
        chunked_transfer_encoding on;
    }

    # Frontend (/)
    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;

        # WebSocket 지원 (Next.js HMR)
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        proxy_read_timeout 60s;
        proxy_send_timeout 60s;
    }

    # Next.js 정적 파일
    location /_next/static {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_cache_valid 200 1d;
        add_header Cache-Control "public, immutable, max-age=31536000";
    }

    # 헬스체크 (Nginx 자체)
    location /nginx-health {
        return 200 'OK';
        add_header Content-Type text/plain;
    }
}
```

### 롤백본 위치

```
/etc/nginx/backup-20260127/
├── nginx.conf
└── sites-available/
    ├── default
    ├── gerrit
    └── jenkins
```

### 롤백 방법

```bash
# 롤백
sudo rm /etc/nginx/sites-enabled/yeji
sudo ln -sf /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
```

---

## 4. Docker 배포 커맨드

### AI Server (Production)

```bash
# 빌드
cd ~/yeji-ai-server/ai
docker build -t yeji-ai:latest .

# Production 배포 (ai/main 브랜치)
docker stop yeji-ai-prod 2>/dev/null || true
docker rm -f yeji-ai-prod 2>/dev/null || true
docker run -d \
    --name yeji-ai-prod \
    -p 8000:8000 \
    -e VLLM_BASE_URL=http://13.125.68.166:8001 \
    -e VLLM_MODEL=tellang/yeji-8b-rslora-v7-AWQ \
    -e ROOT_PATH=/ai \
    -e DEPLOY_ENV=production \
    -e USE_GPT5MINI_FOR_CHAT=true \
    -e OPENAI_API_KEY=${OPENAI_API_KEY} \
    -e OPENAI_MODEL=gpt-5-mini \
    --restart unless-stopped \
    yeji-ai:prod

# Development 배포 (ai/develop 브랜치)
docker stop yeji-ai-dev 2>/dev/null || true
docker rm -f yeji-ai-dev 2>/dev/null || true
docker run -d \
    --name yeji-ai-dev \
    -p 8002:8000 \
    -e VLLM_BASE_URL=http://13.125.68.166:8001 \
    -e VLLM_MODEL=tellang/yeji-8b-rslora-v7-AWQ \
    -e ROOT_PATH=/ai-dev \
    -e DEPLOY_ENV=development \
    -e USE_GPT5MINI_FOR_CHAT=true \
    -e OPENAI_API_KEY=${OPENAI_API_KEY} \
    -e OPENAI_MODEL=gpt-5-mini \
    --restart unless-stopped \
    yeji-ai:dev

# Ultra4 배포 (ai/ultra4 브랜치)
docker stop yeji-ai-ultra4 2>/dev/null || true
docker rm -f yeji-ai-ultra4 2>/dev/null || true
docker run -d \
    --name yeji-ai-ultra4 \
    -p 8003:8000 \
    -e VLLM_BASE_URL=http://13.125.68.166:8001 \
    -e VLLM_MODEL=tellang/yeji-8b-rslora-v7-AWQ \
    -e ROOT_PATH=/ai-ultra4 \
    -e DEPLOY_ENV=ultra4 \
    -e USE_GPT5MINI_FOR_CHAT=true \
    -e OPENAI_API_KEY=${OPENAI_API_KEY} \
    -e OPENAI_MODEL=gpt-5-mini \
    --restart unless-stopped \
    yeji-ai:ultra4

# 로그 확인
docker logs -f yeji-ai-prod
docker logs -f yeji-ai-dev
```

### GPU 필터 활성화 배포 (선택적)

GPU 필터(Guard + Intent)를 활성화하려면 추가 환경변수 설정:

```bash
docker run -d \
    --name yeji-ai-prod \
    -p 8000:8000 \
    -e VLLM_BASE_URL=http://13.125.68.166:8001 \
    -e VLLM_MODEL=tellang/yeji-8b-rslora-v7-AWQ \
    -e GPU_FILTER_ENABLED=true \
    -e GPU_DEVICE=cuda:0 \
    -e GUARD_MODE=block \
    -e INTENT_EMBEDDING_MODE=block \
    --restart unless-stopped \
    yeji-ai:latest
```

### Frontend (Next.js) - 예정

```bash
# 빌드
cd ~/yeji-frontend
docker build -t yeji-frontend:latest .

# 배포
docker stop yeji-frontend 2>/dev/null || true
docker rm -f yeji-frontend 2>/dev/null || true
docker run -d \
    --name yeji-frontend \
    -p 3000:3000 \
    -e NEXT_PUBLIC_API_URL=https://i14a605.p.ssafy.io \
    --restart unless-stopped \
    yeji-frontend:latest
```

---

## 5. AWS GPU 서버 구성

### 현재 구성 (운영 중)

| 항목 | 값 |
|------|-----|
| **인스턴스 ID** | (AWS 콘솔에서 확인) |
| **인스턴스 유형** | g5.xlarge |
| **GPU** | NVIDIA A10G 24GB |
| **AMI** | Deep Learning AMI (Ubuntu 22.04) |
| **Elastic IP** | 13.125.68.166 |
| **리전** | ap-northeast-2 (서울) |

### Security Group 설정

| 포트 | 프로토콜 | 소스 | 설명 |
|------|----------|------|------|
| 22 | TCP | 관리자 IP | SSH 접속 |
| 8001 | TCP | 52.78.174.197/32 | vLLM 8B API (SSAFY EC2만) |
| 8002 | TCP | 52.78.174.197/32 | vLLM 4B API (예약, 선택적) |

### vLLM 서비스 관리

```bash
# 서비스 상태 확인
sudo systemctl status vllm

# 서비스 로그 확인
sudo journalctl -u vllm -f

# 서비스 재시작
sudo systemctl restart vllm

# GPU 상태 확인
nvidia-smi
```

### vLLM systemd 서비스 설정

```bash
# /etc/systemd/system/vllm.service
sudo tee /etc/systemd/system/vllm.service << 'EOF'
[Unit]
Description=vLLM OpenAI API Server (8B Model)
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu
Environment="PATH=/home/ubuntu/venv/bin:/usr/local/bin:/usr/bin"
Environment="CUDA_VISIBLE_DEVICES=0"
ExecStart=/home/ubuntu/venv/bin/python -m vllm.entrypoints.openai.api_server \
    --model tellang/yeji-8b-rslora-v7-AWQ \
    --port 8001 \
    --dtype half \
    --max-model-len 2048 \
    --gpu-memory-utilization 0.90 \
    --host 0.0.0.0 \
    --trust-remote-code
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable vllm
sudo systemctl start vllm
```

### 멀티모델 배포 (8B + 4B) - 선택적

L4 GPU에서 8B와 4B 모델을 동시에 배포하려면:

```bash
# 8B 모델 (메인 운세 생성) - 포트 8001
sudo tee /etc/systemd/system/vllm-8b.service << 'EOF'
[Unit]
Description=vLLM 8B Model
After=network.target

[Service]
Type=simple
User=ubuntu
Environment="CUDA_VISIBLE_DEVICES=0"
ExecStart=/home/ubuntu/venv/bin/python -m vllm.entrypoints.openai.api_server \
    --model tellang/yeji-8b-rslora-v7-AWQ \
    --port 8001 \
    --dtype half \
    --max-model-len 2048 \
    --gpu-memory-utilization 0.45 \
    --host 0.0.0.0 \
    --trust-remote-code
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 4B 모델 (빠른 응답/티키타카) - 포트 8002
sudo tee /etc/systemd/system/vllm-4b.service << 'EOF'
[Unit]
Description=vLLM 4B Model
After=network.target

[Service]
Type=simple
User=ubuntu
Environment="CUDA_VISIBLE_DEVICES=0"
ExecStart=/home/ubuntu/venv/bin/python -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen3-4B-AWQ \
    --port 8002 \
    --dtype half \
    --max-model-len 4096 \
    --gpu-memory-utilization 0.40 \
    --host 0.0.0.0 \
    --trust-remote-code
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable vllm-8b vllm-4b
sudo systemctl start vllm-8b vllm-4b
```

---

## 6. 환경변수 가이드

### 필수 환경변수

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `VLLM_BASE_URL` | `http://localhost:8001` | vLLM 서버 URL |
| `VLLM_MODEL` | `tellang/yeji-8b-lora-v5` | vLLM 모델 ID |

### 서버 설정

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `HOST` | `0.0.0.0` | 서버 바인딩 호스트 |
| `PORT` | `8000` | 서버 포트 |
| `DEBUG` | `false` | 디버그 모드 (Swagger UI 활성화) |
| `LOG_LEVEL` | `INFO` | 로그 레벨 (DEBUG/INFO/WARNING/ERROR) |

### vLLM 설정

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `VLLM_MAX_TOKENS` | `2048` | 최대 생성 토큰 수 |
| `VLLM_TEMPERATURE` | `0.7` | 생성 온도 |
| `VLLM_TOP_P` | `0.9` | Top-P 샘플링 |

### CORS 및 외부 연동

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `CORS_ORIGINS` | `["http://localhost:3000","https://i14a605.p.ssafy.io"]` | 허용 Origin 목록 (JSON 배열) |
| `BACKEND_URL` | `http://localhost:8081` | 백엔드 서버 URL |
| `HF_TOKEN` | (없음) | HuggingFace API 토큰 |

### 티키타카 설정

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `TIKITAKA_MAX_TURNS` | `10` | 최대 대화 턴 수 |
| `TIKITAKA_QUESTION_COUNT` | `2` | 중간 질문 횟수 |

### GPT-5-mini 설정 (채팅용 LLM)

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `USE_GPT5MINI_FOR_CHAT` | `false` | GPT-5-mini 채팅 활성화 여부 |
| `OPENAI_API_KEY` | (없음) | OpenAI API 키 (Jenkins credential) |
| `OPENAI_MODEL` | `gpt-5-mini` | 사용할 OpenAI 모델 |

### 배포 환경 설정

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `ROOT_PATH` | `/` | API 루트 경로 (/ai, /ai-dev, /ai-ultra4) |
| `DEPLOY_ENV` | `development` | 배포 환경 (production, development, ultra4) |
| `GIT_COMMIT` | (없음) | Git 커밋 해시 (Jenkins 자동 주입) |
| `APP_VERSION` | (없음) | 앱 버전 (Jenkins 자동 주입) |

### GPU 필터 설정 (선택적)

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `GPU_FILTER_ENABLED` | `false` | GPU 필터 활성화 여부 |
| `GPU_DEVICE` | `cuda:0` | GPU 디바이스 |

### Prompt Guard 설정 (악성 프롬프트 탐지)

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `GUARD_MODEL` | `meta-llama/Llama-Prompt-Guard-2-86M` | Guard 모델 ID |
| `GUARD_THRESHOLD` | `0.8` | 악성 판정 임계값 (0.0~1.0) |
| `GUARD_TIMEOUT` | `1.0` | 추론 타임아웃 (초) |
| `GUARD_MODE` | `block` | 동작 모드 (block/log_only/shadow) |
| `GUARD_REQUIRED` | `false` | 로드 실패 시 앱 시작 실패 여부 |

### Intent Classifier 설정 (의도 분류)

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `INTENT_EMBEDDING_MODEL` | `Alibaba-NLP/gte-multilingual-base` | Intent 모델 ID |
| `INTENT_EMBEDDING_THRESHOLD` | `0.7` | 분류 신뢰도 임계값 (0.0~1.0) |
| `INTENT_EMBEDDING_TIMEOUT` | `0.5` | 추론 타임아웃 (초) |
| `INTENT_EMBEDDING_MODE` | `block` | 동작 모드 (block/log_only/shadow) |
| `INTENT_EMBEDDING_REQUIRED` | `false` | 로드 실패 시 앱 시작 실패 여부 |

### .env.example

```bash
# YEJI AI Server 환경 변수

# 서버 설정
HOST=0.0.0.0
PORT=8000
DEBUG=false
LOG_LEVEL=INFO

# vLLM 설정 (필수)
VLLM_BASE_URL=http://13.125.68.166:8001
VLLM_MODEL=tellang/yeji-8b-rslora-v7-AWQ
VLLM_MAX_TOKENS=2048
VLLM_TEMPERATURE=0.7
VLLM_TOP_P=0.9

# HuggingFace (모델 다운로드용)
HF_TOKEN=your_huggingface_token_here

# 백엔드 연동 (선택)
BACKEND_URL=http://localhost:8081

# CORS 설정
CORS_ORIGINS=["http://localhost:3000","https://i14a605.p.ssafy.io"]

# GPU 필터 설정 (선택적 - L4 GPU 배포 시)
GPU_FILTER_ENABLED=false
GPU_DEVICE=cuda:0
GUARD_MODE=block
INTENT_EMBEDDING_MODE=block
```

---

## 7. 헬스체크 엔드포인트

### 엔드포인트 목록

| 경로 | 용도 | 응답 |
|------|------|------|
| `/health` | 기본 헬스체크 | `{"status": "healthy", "version": "...", "service": "yeji-ai", "git_commit": "..."}` |
| `/health/ready` | K8s Readiness Probe | `{"status": "ready", "vllm_connected": true}` |
| `/health/live` | K8s Liveness Probe | `{"status": "alive"}` |
| `/health/filter` | GPU 필터 상태 | `{"enabled": false, "guard_loaded": false, ...}` |
| `/health/cache` | 운세 캐시 상태 | `{"loaded": true, "eastern": {...}, "western": {...}}` |
| `/model/status` | 모델 상태 | `{"status": "ok", "model": "...", "vllm_url": "...", "ready": true}` |

### 헬스체크 예시

```bash
# 기본 헬스체크 (Production)
curl -s https://i14a605.p.ssafy.io/ai/health | jq
# 응답: {"status":"healthy","version":"0.4.0.344","service":"yeji-ai","git_commit":"5fffe35b"}

# vLLM 연결 상태 확인
curl -s https://i14a605.p.ssafy.io/ai/health/ready | jq
# 응답: {"status":"ready","vllm_connected":true}

# Development 헬스체크
curl -s https://i14a605.p.ssafy.io/ai-dev/health | jq

# Ultra4 헬스체크
curl -s https://i14a605.p.ssafy.io/ai-ultra4/health | jq
```

### Docker HEALTHCHECK

Dockerfile에서 헬스체크 설정:

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
```

---

## 8. 보안 규칙 요약

**주의**: 민감한 정보(API 키, 비밀번호 등)를 코드나 로그에 포함하지 마세요.

### UFW (SSAFY EC2)

| 포트 | 용도 | 상태 |
|------|------|------|
| 22 | SSH | ✅ 허용 |
| 80 | HTTP (리다이렉트) | ✅ 허용 |
| 443 | HTTPS | ✅ 허용 |
| 8080 | Jenkins | ✅ 허용 |
| 8988 | Gerrit | ✅ 허용 |
| 3000 | Frontend (내부) | ❌ 차단 (Nginx 프록시) |
| 8000 | AI Server (내부) | ❌ 차단 (Nginx 프록시) |
| 8081 | Backend (내부) | ❌ 차단 (Nginx 프록시) |

### AWS Security Group (GPU 서버)

| 포트 | 용도 | 소스 |
|------|------|------|
| 22 | SSH | 관리자 IP |
| 8001 | vLLM API | 52.78.174.197/32 (SSAFY EC2) |

---

## 9. Jenkins CI/CD 파이프라인

### GitLab 모노레포 구조

```
yeji (GitLab Monorepo)
├── ai-server/          # yeji-ai-server (FastAPI)
├── backend/            # yeji-backend (Spring Boot)
└── frontend/           # yeji-frontend (Next.js)
```

### AI Server Jenkinsfile (현재 운영 버전)

```groovy
pipeline {
    agent any

    triggers {
        // 5분마다 SCM 변경 확인 (ai/develop, ai/main 모든 브랜치)
        pollSCM('H/5 * * * *')
    }

    environment {
        MATTERMOST_WEBHOOK = credentials('mattermost-webhook')
        OPENAI_API_KEY = credentials('openai-api-key')
        // 브랜치별 환경 결정: main=production, ultra4=ultra4, 그 외=development
        DEPLOY_ENV = "${env.GIT_BRANCH?.contains('main') ? 'production' : (env.GIT_BRANCH?.contains('ultra4') ? 'ultra4' : 'development')}"
    }

    stages {
        stage('Docker Build') {
            steps {
                dir('ai') {
                    script {
                        // pyproject.toml에서 버전 읽기 + 빌드 넘버 추가
                        def baseVersion = sh(script: "grep '^version' pyproject.toml | cut -d'\"' -f2", returnStdout: true).trim()
                        env.APP_VERSION = "${baseVersion}.${BUILD_NUMBER}"
                    }
                    sh '''
                        docker build \
                            --build-arg GIT_COMMIT=${GIT_COMMIT} \
                            --build-arg APP_VERSION=${APP_VERSION} \
                            -t yeji-ai:${BUILD_NUMBER} .
                    '''
                }
            }
        }

        stage('Deploy') {
            steps {
                script {
                    // 환경별 설정 (production/development/ultra4)
                    def config = [:]
                    switch(env.DEPLOY_ENV) {
                        case 'production':
                            config = [port: '8000', containerName: 'yeji-ai-prod',
                                      imageTag: 'prod', rootPath: '/ai', useGpt5mini: true]
                            break
                        case 'ultra4':
                            config = [port: '8003', containerName: 'yeji-ai-ultra4',
                                      imageTag: 'ultra4', rootPath: '/ai-ultra4', useGpt5mini: true]
                            break
                        default: // development
                            config = [port: '8002', containerName: 'yeji-ai-dev',
                                      imageTag: 'dev', rootPath: '/ai-dev', useGpt5mini: true]
                    }

                    def gpt5miniEnvVars = config.useGpt5mini ?
                        "-e USE_GPT5MINI_FOR_CHAT=true -e OPENAI_API_KEY=${OPENAI_API_KEY} -e OPENAI_MODEL=gpt-5-mini" :
                        "-e USE_GPT5MINI_FOR_CHAT=false"

                    sh """
                        docker stop ${config.containerName} 2>/dev/null || true
                        docker rm -f ${config.containerName} 2>/dev/null || true
                        docker tag yeji-ai:\${BUILD_NUMBER} yeji-ai:${config.imageTag}

                        docker run -d --name ${config.containerName} \
                            -p ${config.port}:8000 \
                            -e VLLM_BASE_URL=http://13.125.68.166:8001 \
                            -e VLLM_MODEL=tellang/yeji-8b-rslora-v7-AWQ \
                            -e ROOT_PATH=${config.rootPath} \
                            -e DEPLOY_ENV=${env.DEPLOY_ENV} \
                            -e GIT_COMMIT=${GIT_COMMIT} \
                            -e APP_VERSION=${APP_VERSION} \
                            ${gpt5miniEnvVars} \
                            --restart unless-stopped \
                            yeji-ai:${config.imageTag}
                    """
                }
            }
        }
    }

    post {
        success { /* Mattermost 성공 알림 */ }
        failure { /* Mattermost 실패 알림 */ }
        always { cleanWs() }
    }
}
```

### 브랜치별 배포 동작

| 브랜치 | 환경 | 포트 | 컨테이너명 | ROOT_PATH | GPT-5-mini |
|--------|------|------|------------|-----------|------------|
| `ai/main` | production | 8000 | yeji-ai-prod | /ai | ✅ 활성화 |
| `ai/develop` | development | 8002 | yeji-ai-dev | /ai-dev | ✅ 활성화 |
| `ai/ultra4` | ultra4 | 8003 | yeji-ai-ultra4 | /ai-ultra4 | ✅ 활성화 |

### Jenkins 자격 증명

| ID | 타입 | 용도 |
|----|------|------|
| `mattermost-webhook` | Secret text | Mattermost 알림 Webhook URL |
| `gitlab-token` | Username/Password | GitLab 접근 토큰 |
| `openai-api-key` | Secret text | OpenAI API 키 (GPT-5-mini용) |

### Frontend Jenkinsfile (예정)

```groovy
pipeline {
    agent any

    environment {
        DOCKER_IMAGE = 'yeji-frontend'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build') {
            steps {
                dir('frontend') {
                    sh 'docker build -t ${DOCKER_IMAGE}:${BUILD_NUMBER} .'
                    sh 'docker tag ${DOCKER_IMAGE}:${BUILD_NUMBER} ${DOCKER_IMAGE}:latest'
                }
            }
        }

        stage('Deploy') {
            steps {
                sh '''
                    docker stop yeji-frontend || true
                    docker rm -f yeji-frontend || true
                    docker run -d \
                        --name yeji-frontend \
                        -p 3000:3000 \
                        -e NEXT_PUBLIC_API_URL=https://i14a605.p.ssafy.io \
                        --restart unless-stopped \
                        ${DOCKER_IMAGE}:latest
                '''
            }
        }

        stage('Health Check') {
            steps {
                sh '''
                    sleep 15
                    curl -f http://localhost:3000 || exit 1
                '''
            }
        }
    }
}
```

---

## 10. 롤백 절차

### AI Server 롤백 (Docker)

```bash
# 1. 현재 실행 중인 컨테이너 확인
docker ps -a | grep yeji-ai

# 2. 이전 이미지 태그 확인
docker images | grep yeji-ai

# 3. 롤백 (이전 빌드 번호로 교체)
docker stop yeji-ai-prod
docker rm yeji-ai-prod

# 이전 빌드 번호 (예: 42)로 롤백
docker run -d --name yeji-ai-prod \
    -p 8000:8000 \
    -e VLLM_BASE_URL=http://13.125.68.166:8001 \
    -e VLLM_MODEL=tellang/yeji-8b-rslora-v7-AWQ \
    --restart unless-stopped \
    yeji-ai:42

# 4. 헬스체크 확인
curl -s http://localhost:8000/api/health | jq
```

### Jenkins 롤백

1. Jenkins UI 접속: http://i14a605.p.ssafy.io:8080
2. 해당 Job 선택
3. 이전 성공한 빌드 번호 클릭
4. "Rebuild" 버튼 클릭

### Nginx 롤백

```bash
# 롤백 (이전 설정 복원)
sudo rm /etc/nginx/sites-enabled/yeji
sudo ln -sf /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
```

### vLLM 서버 롤백

```bash
# AWS GPU 서버에서
ssh ubuntu@13.125.68.166

# 이전 모델 버전으로 변경
sudo systemctl stop vllm

# /etc/systemd/system/vllm.service 에서 모델 경로 수정
sudo nano /etc/systemd/system/vllm.service
# --model 파라미터를 이전 버전으로 변경

sudo systemctl daemon-reload
sudo systemctl start vllm
```

---

## 11. GPU 필터 배포

### 개요

GPU 필터는 L4 GPU에서 다음 두 모델을 실행합니다:

1. **Prompt Guard** (`meta-llama/Llama-Prompt-Guard-2-86M`)
   - 악성 프롬프트 탐지 (인젝션, 탈옥, 간접 공격)
   - ~86MB VRAM 사용

2. **Intent Classifier** (`Alibaba-NLP/gte-multilingual-base`)
   - 임베딩 기반 의도 분류 (운세/인사/OOD)
   - ~560MB VRAM 사용

### 동작 모드

| 모드 | 설명 |
|------|------|
| `block` | 악성/OOD 입력 차단 |
| `log_only` | 로깅만 (차단 안 함) |
| `shadow` | 실행하되 결과 무시 (테스트용) |

### 배포 방법

**주의**: GPU 필터는 CUDA GPU가 있는 환경에서만 활성화됩니다.

```bash
# GPU 필터 활성화 배포
docker run -d --name yeji-ai-prod \
    --gpus all \
    -p 8000:8000 \
    -e VLLM_BASE_URL=http://13.125.68.166:8001 \
    -e VLLM_MODEL=tellang/yeji-8b-rslora-v7-AWQ \
    -e GPU_FILTER_ENABLED=true \
    -e GPU_DEVICE=cuda:0 \
    -e GUARD_MODEL=meta-llama/Llama-Prompt-Guard-2-86M \
    -e GUARD_THRESHOLD=0.8 \
    -e GUARD_MODE=block \
    -e INTENT_EMBEDDING_MODEL=Alibaba-NLP/gte-multilingual-base \
    -e INTENT_EMBEDDING_THRESHOLD=0.7 \
    -e INTENT_EMBEDDING_MODE=block \
    --restart unless-stopped \
    yeji-ai:latest
```

### GPU 메모리 요구사항

| 모델 | VRAM | 비고 |
|------|------|------|
| Prompt Guard | ~100MB | FP16 |
| Intent Classifier | ~600MB | FP16 |
| **합계** | ~700MB | 여유 포함 1GB 권장 |

### AWS Provider 분기 로직

AI 서버는 환경에 따라 자동으로 Provider를 선택합니다:

```python
# VLLM_BASE_URL이 설정된 경우: 직접 연결
# SSH 설정이 있는 경우: SSH 터널링
# AWS 설정이 있는 경우: EC2 시작/중지 자동화
```

자세한 내용은 `docs/PROVIDERS.md` 참조.

---

## 12. 문제 해결

### AI 서버 unhealthy 상태

Docker healthcheck 경로 불일치 문제:

**해결**: Dockerfile의 HEALTHCHECK 수정

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1
```

### vLLM 서버 연결 실패

```bash
# 1. AWS GPU 서버 상태 확인
curl -s http://13.125.68.166:8001/health

# 2. vLLM 서비스 상태 확인 (AWS에서)
ssh ubuntu@13.125.68.166 'sudo systemctl status vllm'

# 3. Security Group 확인
# - SSAFY EC2 IP (52.78.174.197)가 8001 포트에 허용되어 있는지 확인
```

### GPU 필터 로드 실패

```bash
# 1. CUDA 사용 가능 여부 확인
docker exec yeji-ai-prod python -c "import torch; print(torch.cuda.is_available())"

# 2. GPU 메모리 확인
docker exec yeji-ai-prod nvidia-smi

# 3. HuggingFace 토큰 확인 (Llama 모델 접근용)
# HF_TOKEN 환경변수가 올바르게 설정되어 있는지 확인
```

### 타임아웃 오류

LLM 응답이 느린 경우:

```bash
# Nginx 타임아웃 증가 (이미 설정됨: 120s)
# /etc/nginx/sites-available/yeji 에서:
proxy_read_timeout 120s;
proxy_send_timeout 120s;
```

---

## 13. 다음 단계

### 즉시 필요

- [ ] **Frontend 배포**: GitLab에서 소스 가져와 Docker 배포
- [ ] **E2E 테스트**: 프론트 → AI → vLLM 전체 흐름 검증

### 향후 계획

- [ ] **L4 GPU 멀티모델 배포**: 8B + 4B 동시 배포 (비용 효율화)
- [ ] **GPU 필터 프로덕션 적용**: Guard + Intent 활성화
- [ ] **GPU 제어 Lambda 구성**: 비용 절감을 위한 start/stop 자동화
- [ ] **모니터링 대시보드**: Grafana + Prometheus 연동
- [ ] **로그 집계**: ELK 또는 Loki 구성

---

## URL 검증 결과

| 경로 | 예상 | 실제 | 비고 |
|------|------|------|------|
| / | 200 | 502 | Frontend 미배포 |
| /api | 200 | 302 | Backend 동작 (리다이렉트) |
| /ai/health | 200 | 200 ✅ | AI Server (Prod) 정상 |
| /ai/health/ready | 200 | 200 ✅ | vLLM 연결 상태 |
| /ai-dev/health | 200 | 200 ✅ | AI Server (Dev) 정상 |
| /ai-ultra4/health | 200 | 200 ✅ | AI Server (Ultra4) 정상 |
| /nginx-health | 200 | 200 ✅ | Nginx 정상 |

---

## SSH 접속 설정

### SSH 키 위치

| 키 파일 | 용도 | 위치 |
|---------|------|------|
| `ssafy-ec2.pem` | SSAFY EC2 (Jenkins, Nginx) | `~/.ssh/ssafy-ec2.pem` |
| `yeji-gpu.pem` | AWS GPU (vLLM) | `~/.ssh/yeji-gpu.pem` |

### SSH Config (~/.ssh/config)

```bash
# SSAFY EC2 서버 (Jenkins, Nginx, Docker)
Host jenkins ssafy-ec2
  HostName i14a605.p.ssafy.io
  User ubuntu
  IdentityFile ~/.ssh/ssafy-ec2.pem
  StrictHostKeyChecking no
  ServerAliveInterval 60

# AWS GPU 서버 (vLLM)
Host gpu aws-gpu
  HostName 13.125.68.166
  User ubuntu
  IdentityFile ~/.ssh/yeji-gpu.pem
  StrictHostKeyChecking no
```

### 접속 명령

```bash
# SSAFY EC2 접속
ssh jenkins

# AWS GPU 서버 접속
ssh gpu

# Nginx 설정 확인
ssh jenkins "cat /etc/nginx/sites-available/yeji"

# Docker 컨테이너 확인
ssh jenkins "docker ps"

# vLLM 서비스 상태 확인
ssh gpu "sudo systemctl status vllm"
```

---

## 연락처

- 인프라 담당: 박태언 (@pte1024)
- Jenkins: http://i14a605.p.ssafy.io:8080 (admin / yeji2026!)
