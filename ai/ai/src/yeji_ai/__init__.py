"""YEJI AI Server - 사주/운세 AI 분석 서버"""

import importlib.metadata
import os

# 버전 우선순위:
# 1. 환경변수 APP_VERSION (Jenkins 빌드 시 주입)
# 2. 설치된 패키지 메타데이터
# 3. pyproject.toml 기본 버전
__version__ = os.environ.get("APP_VERSION")
if not __version__:
    try:
        __version__ = importlib.metadata.version("yeji-ai-server")
    except importlib.metadata.PackageNotFoundError:
        # 개발 모드에서 패키지가 설치되지 않은 경우
        __version__ = "0.3.3"  # pyproject.toml과 동기화 필요

# Git 커밋 해시 (빌드 시 환경변수로 주입)
_git_commit_raw = os.environ.get("GIT_COMMIT")
__git_commit__ = _git_commit_raw[:8] if _git_commit_raw else "dev"
