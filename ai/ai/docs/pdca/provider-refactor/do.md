# Provider 시스템 리팩터링 Do (실행 로그)

> 작성일: 2026-01-28
> 상태: 완료

## 실행 타임라인

### 12:30 - 사전 조사

```
환경 확인:
- Python: 3.12.10
- httpx: 0.28.1
```

백업 완료: `backup/providers-20260128/`

### 12:33 - P0-1: or 연산자 버그 수정

**문제 코드**:
```python
# 버그: temperature=0 → 0 or 0.7 → 0.7
"temperature": config.temperature or self.config.default_temperature
```

**수정 코드**:
```python
# 수정: None 체크로 0 값 보존
"temperature": config.temperature if config.temperature is not None else self.config.default_temperature
```

**수정 파일**:
- `vllm.py`: chat(), chat_stream() 메서드
- `ollama.py`: chat(), chat_stream() 메서드
- `aws.py`: chat(), chat_stream() 메서드

### 12:35 - P0-2: AWSProvider.stop() 시그니처 수정

**문제**:
```python
# 부모 클래스 시그니처
async def stop(self) -> bool

# AWSProvider (불일치)
async def stop(self, stop_instance: bool = False) -> bool
```

**해결**:
```python
# stop() - EC2 유지 (부모 시그니처와 일치)
async def stop(self) -> bool

# stop_with_instance() - EC2까지 중지 (별도 메서드)
async def stop_with_instance(self) -> bool
```

### 12:38 - P1-2: Ollama async subprocess 전환

**문제**: 동기 `subprocess.Popen/run` 사용

**해결**:
- `_start_ollama_service()`: `asyncio.create_subprocess_exec` 사용
- `_stop_ollama_service()`: `asyncio.create_subprocess_exec` 사용
- Windows는 `CREATE_NO_WINDOW` 플래그 필요로 동기 Popen 유지

### 12:42 - 테스트 추가

신규 테스트 클래스:

1. **TestTemperatureZero** (3개 테스트)
   - `test_generation_config_temperature_zero`: temperature=0 설정 가능 확인
   - `test_generation_config_none_vs_zero`: None과 0 구분 확인
   - `test_vllm_config_defaults`: 기본값 확인

2. **TestProviderPolymorphism** (4개 테스트)
   - `test_all_providers_implement_interface`: 인터페이스 구현 확인
   - `test_provider_name_uniqueness`: name 고유성 확인
   - `test_aws_provider_stop_signature`: stop() 시그니처 일치 확인
   - `test_all_providers_stop_without_args`: 모든 Provider stop() 인자 없이 호출 가능

### 12:45 - 테스트 실행

```
테스트 결과: 32 passed ✅

기존 테스트: 25개 통과
신규 테스트: 7개 추가 (모두 통과)
```

## 수정 요약

| 항목 | 파일 | 변경 내용 |
|------|------|----------|
| P0-1 | vllm.py | `or` → `is not None` 체크 (2곳) |
| P0-1 | ollama.py | `or` → `is not None` 체크 (2곳) |
| P0-1 | aws.py | `or` → `is not None` 체크 (2곳) |
| P0-2 | aws.py | `stop()` 분리 + `stop_with_instance()` 추가 |
| P1-2 | ollama.py | `_start_ollama_service()` async 전환 |
| P1-2 | ollama.py | `_stop_ollama_service()` async 전환 |
| 테스트 | test_providers.py | 7개 테스트 추가 |

## 미수행 항목

- **P1-1 httpx lifecycle**: 현재 구조에서 race condition 가능성 낮음, 추후 필요시 개선
- **P2 공통화**: 대규모 리팩터링으로 향후 과제로 보류
