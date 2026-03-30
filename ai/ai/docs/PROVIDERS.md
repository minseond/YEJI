# LLM Provider 가이드

> yeji-ai-server의 다양한 LLM 백엔드 통합 관리 시스템

## 개요

Provider 시스템은 vLLM, Ollama, AWS EC2 등 다양한 LLM 백엔드를 추상화하여 통합 관리합니다.

```
┌─────────────────────────────────────────────────────────────────────┐
│                        LLMProvider (추상)                            │
├─────────────────────────────────────────────────────────────────────┤
│  start() | stop() | status() | health() | chat() | chat_stream()   │
└─────────────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  VLLMProvider   │  │  OllamaProvider │  │   AWSProvider   │
│  (vLLM 서버)     │  │  (Ollama 로컬)   │  │  (EC2 + vLLM)   │
├─────────────────┤  ├─────────────────┤  ├─────────────────┤
│ - 로컬/원격      │  │ - 자동 시작      │  │ - EC2 시작/중지  │
│ - SSH 제어      │  │ - 모델 자동 풀   │  │ - SSH 터널      │
│ - GPU 모니터링   │  │ - 서비스 관리    │  │ - 비용 최적화   │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

## 설치

Provider는 `yeji_ai.providers` 모듈에 포함되어 있습니다.

```python
from yeji_ai.providers import (
    # 기본 타입
    LLMProvider, ProviderStatus, ProviderHealth,
    GenerationConfig, CompletionResponse,
    # Providers
    VLLMProvider, VLLMConfig,
    OllamaProvider, OllamaConfig,
    AWSProvider, AWSConfig,
    # SSH Adapter
    SSHAdapter, SSHConfig,
)
```

---

## VLLMProvider

vLLM OpenAI-compatible API 서버와 연동합니다.

### 로컬 모드 (이미 실행 중인 vLLM)

```python
from yeji_ai.providers import VLLMProvider, VLLMConfig

# 로컬 vLLM 서버 연결
provider = VLLMProvider(VLLMConfig(
    base_url="http://localhost:8001",
    model="Qwen/Qwen3-4B-AWQ",
))

# 연결 확인
if await provider.start():
    # 채팅
    response = await provider.chat([
        {"role": "system", "content": "/no_think\n운세 해석 전문가입니다."},
        {"role": "user", "content": "1997년 10월 24일생 오늘의 운세는?"}
    ])
    print(response.text)

await provider.close()
```

### 원격 모드 (ultra4 WSL)

```python
from yeji_ai.providers import VLLMProvider, VLLMConfig, SSHConfig

provider = VLLMProvider(VLLMConfig(
    base_url="http://100.114.13.51:8001",  # Tailscale IP
    model="Qwen/Qwen3-4B-AWQ",
    ssh_config=SSHConfig(
        host="ultra4",          # SSH 호스트
        user="user",
        use_wsl=True,           # WSL 내부 커맨드 실행
        wsl_distro="Ubuntu",
    ),
    vllm_command="source ~/venvs/vllm/bin/activate && vllm serve Qwen/Qwen3-4B-AWQ --port 8001 --max-model-len 4096 --enforce-eager",
    tmux_session="vllm",
    startup_wait=30,
))

# vLLM 서버 시작 (원격)
await provider.start()

# 사용
response = await provider.chat([...])

# 서버 중지 (원격)
await provider.stop()
```

---

## OllamaProvider

로컬 Ollama 서버와 연동합니다.

```python
from yeji_ai.providers import OllamaProvider, OllamaConfig

provider = OllamaProvider(OllamaConfig(
    base_url="http://localhost:11434",
    model="qwen3:4b",
    auto_start=True,   # Ollama 서비스 자동 시작
    auto_pull=True,    # 모델 자동 다운로드
))

# 시작 (서비스 + 모델 로딩)
await provider.start()

# 채팅
response = await provider.chat([
    {"role": "user", "content": "안녕하세요"}
])
print(response.text)

# 모델 목록 조회
models = await provider.list_models()
print(models)

await provider.close()
```

### 지원 기능

| 기능 | 설명 |
|------|------|
| auto_start | Ollama 서비스 자동 시작 (Windows/Mac/Linux) |
| auto_pull | 모델이 없으면 자동 다운로드 |
| list_models | 로컬 모델 목록 조회 |
| delete_model | 모델 삭제 |

---

## AWSProvider

AWS EC2 GPU 인스턴스에서 vLLM을 실행합니다.

```python
from yeji_ai.providers import AWSProvider, AWSConfig

provider = AWSProvider(AWSConfig(
    # EC2 설정
    instance_id="i-0123456789abcdef0",
    region="ap-northeast-2",

    # SSH 설정
    ssh_host="3.36.89.31",           # 또는 동적으로 조회
    ssh_user="ubuntu",
    ssh_key_file="~/.ssh/yeji-gpu-key.pem",

    # vLLM 설정
    local_port=8001,                  # SSH 터널 로컬 포트
    remote_port=8001,                 # 원격 vLLM 포트
    model="tellang/yeji-8b-rslora-v7-AWQ",

    # 시작 커맨드
    vllm_command="source ~/venvs/vllm/bin/activate && vllm serve ...",
    startup_wait=60,

    # AWS CLI 프로파일 (선택)
    aws_profile="default",
))

# EC2 시작 + SSH 터널 + vLLM 시작
await provider.start()

# 채팅 (로컬 포트로 연결)
response = await provider.chat([...])

# vLLM 중지 + SSH 터널 종료
await provider.stop()

# EC2도 함께 중지 (비용 절감)
await provider.stop(stop_instance=True)
```

### AWS CLI 설정

```bash
# AWS CLI 설치
pip install awscli

# 자격 증명 설정
aws configure
# AWS Access Key ID: AKIA...
# AWS Secret Access Key: ...
# Default region name: ap-northeast-2
# Default output format: json
```

---

## SSHAdapter

원격 서버 커맨드 실행을 위한 SSH 어댑터입니다.

```python
from yeji_ai.providers import SSHAdapter, SSHConfig

# 기본 사용
ssh = SSHAdapter(SSHConfig(
    host="192.168.1.100",
    user="ubuntu",
    identity_file="~/.ssh/id_rsa",
))

# 연결 테스트
if await ssh.test_connection():
    print("연결 성공")

# 커맨드 실행
result = await ssh.run("nvidia-smi")
print(result.stdout)

# 백그라운드 실행 (tmux)
await ssh.run_background("vllm serve ...", session_name="vllm")

# 세션 출력 확인
output = await ssh.get_session_output("vllm", lines=50)

# 세션 종료
await ssh.kill_session("vllm")

# GPU 정보 조회
gpu_info = await ssh.get_gpu_info()
print(f"GPU 메모리: {gpu_info['memory_used_mb']}/{gpu_info['memory_total_mb']} MB")
```

### WSL 모드

Windows에서 WSL 내부 커맨드를 실행합니다.

```python
ssh = SSHAdapter(SSHConfig(
    host="ultra4",
    user="user",
    use_wsl=True,           # WSL 모드 활성화
    wsl_distro="Ubuntu",    # WSL 배포판 이름
))

# WSL 내부에서 커맨드 실행
result = await ssh.run("source ~/venvs/vllm/bin/activate && python --version")
```

---

## GenerationConfig

생성 설정을 정의합니다.

```python
from yeji_ai.providers import GenerationConfig

config = GenerationConfig(
    max_tokens=2048,
    temperature=0.7,
    top_p=0.9,
    top_k=20,
    stop=["\n\n"],
    presence_penalty=1.5,  # Qwen3 AWQ 권장
    frequency_penalty=0.5,

    # 구조화된 출력
    response_format={"type": "json_object"},

    # vLLM guided decoding
    guided_json={"type": "object", "properties": {...}},
    guided_choice=["A", "B", "C"],
    guided_regex=r"\d{4}-\d{2}-\d{2}",
)

response = await provider.chat(messages, config)
```

---

## ProviderHealth

헬스체크 결과를 담는 데이터 클래스입니다.

```python
health = await provider.health()

print(f"상태: {health.status}")           # ProviderStatus.RUNNING
print(f"모델: {health.model}")            # "Qwen/Qwen3-4B-AWQ"
print(f"지연시간: {health.latency_ms}ms")  # 50.5
print(f"GPU 사용량: {health.gpu_memory_used}/{health.gpu_memory_total} MB")
print(f"에러: {health.error_message}")    # None
```

### ProviderStatus

| 상태 | 설명 |
|------|------|
| UNKNOWN | 상태 미확인 |
| STOPPED | 중지됨 |
| STARTING | 시작 중 |
| RUNNING | 실행 중 |
| STOPPING | 중지 중 |
| ERROR | 오류 상태 |

---

## 환경 변수 예시

```bash
# .env

# vLLM 기본 설정
VLLM_BASE_URL=http://100.114.13.51:8001
VLLM_MODEL=Qwen/Qwen3-4B-AWQ
VLLM_MAX_TOKENS=2048
VLLM_TEMPERATURE=0.7

# AWS 설정 (AWSProvider용)
AWS_PROFILE=default
AWS_REGION=ap-northeast-2
AWS_INSTANCE_ID=i-0123456789abcdef0
AWS_SSH_KEY_FILE=~/.ssh/yeji-gpu-key.pem

# Ollama 설정
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen3:4b
```

---

## 사용 시나리오

### 1. 개발 환경 (Ollama)

```python
# 로컬 개발 시 Ollama 사용
provider = OllamaProvider(OllamaConfig(
    model="qwen3:4b",
    auto_start=True,
))
```

### 2. 테스트 환경 (ultra4)

```python
# Tailscale VPN으로 ultra4 연결
provider = VLLMProvider(VLLMConfig(
    base_url="http://100.114.13.51:8001",
    ssh_config=SSHConfig(host="ultra4", user="user", use_wsl=True),
))
```

### 3. 프로덕션 환경 (AWS)

```python
# AWS EC2 GPU 인스턴스
provider = AWSProvider(AWSConfig(
    instance_id="i-0123456789",
    region="ap-northeast-2",
    ssh_host="3.36.89.31",
    ssh_key_file="~/.ssh/yeji-gpu-key.pem",
))
```

---

## 테스트

```bash
# Provider 테스트 실행
uv run pytest tests/test_providers.py -v

# 전체 테스트
uv run pytest tests/ -v
```

---

*작성일: 2026-01-28*
