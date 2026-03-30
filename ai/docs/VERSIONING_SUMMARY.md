# Jenkins 자동 버전 관리 시스템 - 구현 요약

## 빠른 시작

### 버전 확인 방법
```bash
# 헬스체크로 버전 확인
curl http://localhost:8000/api/health | jq

# 출력 예시:
# {
#   "status": "healthy",
#   "version": "0.2.1.42",
#   "service": "yeji-ai",
#   "git_commit": "a3f7d2c1"
# }
```

### 기본 버전 업데이트
```bash
# 1. pyproject.toml 수정
vim ai/pyproject.toml
# version = "0.3.0"

# 2. __init__.py 폴백 버전 동기화
vim ai/src/yeji_ai/__init__.py
# __version__ = "0.3.0"

# 3. 커밋 및 푸시
git add ai/pyproject.toml ai/src/yeji_ai/__init__.py
git commit -m "chore: [AI] bump version to 0.3.0"
git push origin ai/develop
```

## 구현된 파일

### 1. Jenkinsfile
**변경 사항:**
- `Docker Build` 스테이지에 버전 추출 로직 추가
- pyproject.toml에서 `grep`으로 기본 버전 읽기
- `env.APP_VERSION = baseVersion.BUILD_NUMBER` 설정
- Docker 빌드 시 `--build-arg APP_VERSION` 전달
- Mattermost 알림에 `**VERSION:** ${env.APP_VERSION}` 추가

**핵심 코드:**
```groovy
script {
    def baseVersion = sh(
        script: "grep '^version' pyproject.toml | cut -d'\"' -f2",
        returnStdout: true
    ).trim()
    def fullVersion = "${baseVersion}.${BUILD_NUMBER}"
    env.APP_VERSION = fullVersion
    echo "Building version: ${fullVersion}"
}
```

### 2. Dockerfile
**변경 사항:**
- `ARG APP_VERSION=0.0.0` 추가 (빌드 인자)
- `ENV APP_VERSION=${APP_VERSION}` 추가 (런타임 환경변수)

**핵심 코드:**
```dockerfile
ARG APP_VERSION=0.0.0
ENV APP_VERSION=${APP_VERSION}
```

### 3. src/yeji_ai/__init__.py
**변경 사항:**
- 환경변수 `APP_VERSION` 우선순위 최상위로 변경
- Jenkins 빌드 시 주입된 버전이 최우선 사용됨

**핵심 코드:**
```python
__version__ = os.environ.get("APP_VERSION")
if not __version__:
    try:
        __version__ = importlib.metadata.version("yeji-ai-server")
    except importlib.metadata.PackageNotFoundError:
        __version__ = "0.2.1"
```

### 4. docs/VERSIONING.md (신규)
- 전체 시스템 문서화
- 버전 형식, 업데이트 방법, 트러블슈팅 가이드

## 버전 흐름도

```
┌─────────────────────┐
│  pyproject.toml     │
│  version = "0.2.1"  │
└──────────┬──────────┘
           │
           │ Jenkins: grep + cut
           ▼
┌─────────────────────┐
│  baseVersion        │
│  = "0.2.1"          │
└──────────┬──────────┘
           │
           │ + BUILD_NUMBER (예: 42)
           ▼
┌─────────────────────┐
│  APP_VERSION        │
│  = "0.2.1.42"       │
└──────────┬──────────┘
           │
           │ Docker build --build-arg
           ▼
┌─────────────────────┐
│  Dockerfile ENV     │
│  APP_VERSION=...    │
└──────────┬──────────┘
           │
           │ 컨테이너 런타임
           ▼
┌─────────────────────┐
│  __init__.py        │
│  os.environ.get()   │
└──────────┬──────────┘
           │
           │ FastAPI import
           ▼
┌─────────────────────┐
│  health.py          │
│  __version__        │
└──────────┬──────────┘
           │
           │ API 응답
           ▼
┌─────────────────────┐
│  {"version":        │
│   "0.2.1.42"}       │
└─────────────────────┘
```

## 테스트 시나리오

### 시나리오 1: 정상 빌드
1. 코드 변경 후 `git push origin ai/develop`
2. Jenkins가 자동으로 빌드 시작 (BUILD_NUMBER=42)
3. pyproject.toml에서 `0.2.1` 읽음
4. `APP_VERSION=0.2.1.42` 생성
5. Docker 이미지에 버전 주입
6. 헬스체크 응답: `{"version": "0.2.1.42"}`
7. Mattermost 알림: `VERSION: 0.2.1.42`

### 시나리오 2: 기본 버전 업그레이드
1. pyproject.toml 수정: `version = "0.3.0"`
2. __init__.py 수정: `__version__ = "0.3.0"`
3. `git commit -m "chore: [AI] bump version to 0.3.0"`
4. `git push origin ai/develop`
5. Jenkins 빌드 (BUILD_NUMBER=1, 새 버전 첫 빌드)
6. `APP_VERSION=0.3.0.1` 생성
7. 이후 빌드: `0.3.0.2`, `0.3.0.3`, ...

### 시나리오 3: 롤백
1. Jenkins UI에서 이전 성공 빌드 확인 (예: #41)
2. `docker stop yeji-ai-prod && docker rm yeji-ai-prod`
3. `docker run -d --name yeji-ai-prod -p 8000:8000 yeji-ai:41`
4. 헬스체크 확인: `{"version": "0.2.1.41"}`

## 환경별 버전 예시

| 환경 | 브랜치 | 빌드 번호 | 버전 예시 |
|------|--------|-----------|-----------|
| Production | `ai/main` | 42 | `0.2.1.42` |
| Development | `ai/develop` | 103 | `0.2.1.103` |
| Ultra4 | `ai/ultra4` | 7 | `0.2.1.7` |

**참고:** 각 브랜치는 독립적인 Jenkins Job을 가지므로 BUILD_NUMBER도 독립적입니다.

## 검증 체크리스트

### 배포 후 확인사항
- [ ] 헬스체크 응답에 올바른 버전 표시
- [ ] Mattermost 알림에 버전 정보 포함
- [ ] Docker 이미지 태그에 빌드 번호 포함
- [ ] 컨테이너 환경변수 `APP_VERSION` 설정됨

### 확인 명령어
```bash
# 1. 헬스체크
curl http://localhost:8000/api/health | jq .version

# 2. 컨테이너 환경변수
docker exec yeji-ai-prod env | grep APP_VERSION

# 3. Docker 이미지 목록
docker images yeji-ai

# 4. 특정 이미지 레이블
docker inspect yeji-ai:42 | jq '.[0].Config.Env' | grep APP_VERSION
```

## 문제 해결

### 버전이 "0.2.1"로만 표시됨
**원인:** 환경변수 미주입
**해결:**
```bash
# Jenkins 빌드 로그 확인
# "Building version: 0.2.1.42" 메시지가 있어야 함

# Docker 빌드 커맨드 확인
# --build-arg APP_VERSION=0.2.1.42 포함되어야 함
```

### pyproject.toml 버전 추출 실패
**원인:** grep 명령어 오류
**테스트:**
```bash
cd C:/Users/SSAFY/yeji-ai-server/ai
grep '^version' pyproject.toml | cut -d'"' -f2
# 출력: 0.2.1
```

## 다음 단계

1. **첫 배포 테스트**
   - `ai/develop` 브랜치에 더미 커밋 푸시
   - Jenkins 빌드 로그에서 "Building version: X.Y.Z.N" 확인
   - 헬스체크로 버전 검증

2. **프로덕션 배포**
   - `ai/main` 브랜치로 머지
   - 프로덕션 빌드 및 버전 확인

3. **모니터링 설정** (선택사항)
   - Prometheus/Grafana에 버전 메트릭 추가
   - 배포 이력 대시보드 구성

## 참고 자료

- 전체 문서: [VERSIONING.md](./VERSIONING.md)
- 커밋 컨벤션: [../CLAUDE.md](../CLAUDE.md#커밋-컨벤션)
- Jenkins 파이프라인: [../Jenkinsfile](../Jenkinsfile)
