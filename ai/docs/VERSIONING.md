# Jenkins 자동 버전 관리 시스템

## 개요

Jenkins 빌드 시 자동으로 버전 번호를 생성하고 Docker 이미지 및 애플리케이션에 주입하는 시스템입니다.

## 버전 형식

### 기본 형식
```
X.Y.Z.BUILD_NUMBER
```

### 예시
- `0.2.1.42` - 0.2.1 버전의 42번째 빌드
- `0.2.1.103` - 0.2.1 버전의 103번째 빌드

### 구성 요소
| 요소 | 설명 | 관리 위치 |
|------|------|-----------|
| `X.Y.Z` | 기본 버전 (Semantic Versioning) | `pyproject.toml` |
| `BUILD_NUMBER` | Jenkins 빌드 번호 | Jenkins 자동 증가 |

## 버전 소스

### 우선순위
1. **환경변수 `APP_VERSION`** (Jenkins 빌드 시)
2. 설치된 패키지 메타데이터 (`importlib.metadata`)
3. pyproject.toml 기본 버전 (개발 환경)

### 코드 구현
```python
# src/yeji_ai/__init__.py
__version__ = os.environ.get("APP_VERSION")
if not __version__:
    try:
        __version__ = importlib.metadata.version("yeji-ai-server")
    except importlib.metadata.PackageNotFoundError:
        __version__ = "0.2.1"  # 개발 모드 폴백
```

## Jenkins 빌드 프로세스

### 1. 버전 추출
Jenkinsfile에서 `pyproject.toml`의 버전을 추출합니다.

```groovy
def baseVersion = sh(
    script: "grep '^version' pyproject.toml | cut -d'\"' -f2",
    returnStdout: true
).trim()
```

### 2. 전체 버전 생성
기본 버전에 빌드 번호를 추가합니다.

```groovy
def fullVersion = "${baseVersion}.${BUILD_NUMBER}"
env.APP_VERSION = fullVersion
```

### 3. Docker 빌드
생성된 버전을 Docker 빌드 인자로 전달합니다.

```groovy
docker build \
    --build-arg GIT_COMMIT=${GIT_COMMIT} \
    --build-arg APP_VERSION=${APP_VERSION} \
    -t yeji-ai:${BUILD_NUMBER} .
```

### 4. 환경변수 주입
Dockerfile에서 환경변수로 설정합니다.

```dockerfile
ARG APP_VERSION=0.0.0
ENV APP_VERSION=${APP_VERSION}
```

## API 응답

### 헬스체크 엔드포인트
`GET /api/health`

**응답 예시:**
```json
{
    "status": "healthy",
    "version": "0.2.1.42",
    "service": "yeji-ai",
    "git_commit": "a3f7d2c1"
}
```

### 버전 필드
| 필드 | 예시 값 | 설명 |
|------|---------|------|
| `version` | `0.2.1.42` | APP_VERSION 환경변수 |
| `git_commit` | `a3f7d2c1` | GIT_COMMIT 환경변수 (8자) |

## 기본 버전 업데이트

### 언제 업데이트하나요?

| 변경 유형 | 버전 증가 | 예시 |
|-----------|----------|------|
| 주요 변경 (Breaking Changes) | X 증가 | `0.2.1` → `1.0.0` |
| 새 기능 추가 | Y 증가 | `0.2.1` → `0.3.0` |
| 버그 수정 | Z 증가 | `0.2.1` → `0.2.2` |

### 업데이트 방법

1. **pyproject.toml 수정**
   ```toml
   [project]
   version = "0.3.0"
   ```

2. **__init__.py 폴백 버전 동기화**
   ```python
   __version__ = "0.3.0"  # pyproject.toml과 동일하게
   ```

3. **커밋 및 푸시**
   ```bash
   git commit -m "chore: [AI] bump version to 0.3.0"
   git push origin ai/develop
   ```

4. **Jenkins 자동 빌드**
   - Jenkins가 변경 감지 후 자동 빌드 시작
   - 새 버전: `0.3.0.1`, `0.3.0.2`, ...

## 배포 환경별 버전 관리

### Production
- 브랜치: `ai/main`
- 컨테이너: `yeji-ai-prod`
- 포트: `8000`
- 이미지 태그: `yeji-ai:prod` + `yeji-ai:${BUILD_NUMBER}`

### Development
- 브랜치: `ai/develop`
- 컨테이너: `yeji-ai-dev`
- 포트: `8002`
- 이미지 태그: `yeji-ai:dev` + `yeji-ai:${BUILD_NUMBER}`

### Ultra4
- 브랜치: `ai/ultra4`
- 컨테이너: `yeji-ai-ultra4`
- 포트: `8003`
- 이미지 태그: `yeji-ai:ultra4` + `yeji-ai:${BUILD_NUMBER}`

## 롤백 방법

### 1. 이전 빌드 번호 확인
Jenkins UI에서 성공한 빌드 번호를 확인합니다.

### 2. 해당 빌드 이미지로 롤백
```bash
# 현재 컨테이너 중지
docker stop yeji-ai-prod

# 이전 빌드 이미지로 재시작
docker run -d --name yeji-ai-prod \
    -p 8000:8000 \
    -e VLLM_BASE_URL=http://13.125.68.166:8001 \
    -e VLLM_MODEL=tellang/yeji-8b-rslora-v7-AWQ \
    --restart unless-stopped \
    yeji-ai:41  # 이전 빌드 번호
```

### 3. 버전 확인
```bash
curl http://localhost:8000/api/health | jq .version
# "0.2.1.41"
```

## 버전 추적

### Mattermost 알림
Jenkins 빌드 성공 시 버전 정보가 포함된 알림이 전송됩니다.

```
★  SUCCESS ★
━━━━━━━━━━━━━━━━━━━━━━━━
JOB: yeji-ai-server
BUILD: #42
VERSION: 0.2.1.42
ENV: 🚀 production
MODEL: tellang/yeji-8b-rslora-v7-AWQ
━━━━━━━━━━━━━━━━━━━━━━━━
```

### Docker 이미지 확인
```bash
# 이미지 목록 조회
docker images yeji-ai

# 특정 이미지 검사
docker inspect yeji-ai:42
```

## 트러블슈팅

### 문제: 헬스체크에서 버전이 "0.2.1"로만 표시됨

**원인:** 환경변수 `APP_VERSION`이 제대로 주입되지 않음

**해결:**
1. Docker 빌드 로그에서 `--build-arg APP_VERSION=` 확인
2. 컨테이너 환경변수 확인: `docker exec yeji-ai-prod env | grep APP_VERSION`
3. Jenkinsfile의 `env.APP_VERSION` 설정 확인

### 문제: pyproject.toml 버전 추출 실패

**원인:** `grep` 명령어 실패 또는 파일 경로 문제

**해결:**
```bash
# 로컬에서 테스트
cd ai
grep '^version' pyproject.toml | cut -d'"' -f2
# 출력: 0.2.1
```

### 문제: 빌드 번호가 리셋됨

**원인:** Jenkins Job이 삭제되거나 재생성됨

**해결:**
- Jenkins Job 설정에서 빌드 히스토리 보존 설정 확인
- 빌드 번호는 Job 레벨에서 관리되므로 Job 삭제 시 리셋됨

## 참고 자료

- [Semantic Versioning 2.0.0](https://semver.org/lang/ko/)
- [Docker ARG vs ENV](https://docs.docker.com/engine/reference/builder/#arg)
- [Jenkins Environment Variables](https://www.jenkins.io/doc/book/pipeline/jenkinsfile/#using-environment-variables)
