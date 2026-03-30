# YEJI AI Server Dockerfile
# FastAPI 서버용 (vLLM은 별도 GPU 서버에서 실행)

# 빌드 인자
ARG GIT_COMMIT=unknown
ARG APP_VERSION=0.0.0

# ============================================================
# Builder 스테이지: 의존성 설치
# ============================================================
FROM python:3.11-slim AS builder

WORKDIR /app

# uv 설치 (별도 이미지에서 복사하여 레이어 최소화)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# 의존성 파일만 먼저 복사 (캐시 최적화)
# uv.lock을 포함하여 재현 가능한 빌드 보장
COPY pyproject.toml uv.lock ./

# 의존성만 먼저 설치 (소스 변경 시 캐시 재사용)
RUN uv sync --no-dev --frozen --no-install-project

# 소스 코드 복사 후 프로젝트 설치
COPY src/ src/
RUN uv sync --no-dev --frozen

# ============================================================
# Production 스테이지: 최소 런타임 이미지
# ============================================================
FROM python:3.11-slim AS production

# 메타데이터 레이블
LABEL maintainer="YEJI Team <yeji@ssafy.com>" \
      description="YEJI AI Server - Fortune/Saju API" \
      version="0.1.0"

WORKDIR /app

# 런타임 의존성 (curl: 헬스체크용)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 비루트 사용자 생성 (보안)
RUN useradd --create-home --uid 1000 --shell /bin/bash yeji

# 빌더에서 가상환경 복사
COPY --from=builder --chown=yeji:yeji /app/.venv /app/.venv

# 소스 코드 복사
COPY --chown=yeji:yeji src/ src/

# 데이터 파일 복사 (메시지 풀 등)
COPY --chown=yeji:yeji data/ data/

# 로그 디렉토리 생성 (yeji 사용자 쓰기 권한)
RUN mkdir -p /app/logs/llm_responses && chown -R yeji:yeji /app/logs

# 환경변수 설정
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app/src" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    GIT_COMMIT=${GIT_COMMIT} \
    APP_VERSION=${APP_VERSION}

# 비루트 사용자로 전환
USER yeji

# 헬스체크 (루트 레벨 health 엔드포인트)
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 포트 노출
EXPOSE 8000

# 실행 (workers 수는 환경변수로 조정 가능)
CMD ["uvicorn", "yeji_ai.main:app", "--host", "0.0.0.0", "--port", "8000"]
