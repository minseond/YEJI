# Provider 시스템 리팩터링 Plan

> 작성일: 2026-01-28
> 상태: 진행중

## 목표

1. **버전 민감 + 호환성 보장**: 기존 API 시그니처 100% 유지
2. **코드 품질 개선**: 버그 수정, 안정성 향상

## 환경 정보

```
Python: 3.12.10
httpx: 0.28.1
asyncio: Python 내장 (3.12)
```

## 수정 범위

### 🔴 P0: Critical (즉시 수정)

#### P0-1: `or` 연산자 버그

**문제**: `temperature=0`이나 `top_p=0` 설정 시 기본값으로 대체됨

```python
# 버그 코드
"temperature": config.temperature or self.config.default_temperature
# temperature=0 → 0 or 0.7 → 0.7 (의도치 않은 동작)

# 수정 코드
"temperature": config.temperature if config.temperature is not None else self.config.default_temperature
```

**영향 파일**:
- `vllm.py`: 306-308, 366-368행
- `ollama.py`: 376-378, 423-425행
- `aws.py`: 525-527, 577-579행

#### P0-2: AWSProvider.stop() 시그니처 불일치

**문제**: 부모 클래스 `LLMProvider.stop()` 시그니처와 불일치

```python
# 부모 클래스
async def stop(self) -> bool

# AWSProvider (불일치)
async def stop(self, stop_instance: bool = False) -> bool
```

**해결 방안**:
- `stop()` → 기본 동작 (EC2 유지)
- `stop_with_instance()` → EC2 인스턴스까지 중지

### 🟡 P1: Medium (안정성 개선)

#### P1-1: httpx.AsyncClient 라이프사이클 안전성

**문제**: `is_closed` 체크 후 race condition 가능성

**해결**: context manager 패턴 또는 별도 락 도입 검토

#### P1-2: Ollama 동기 subprocess 사용

**문제**: `_start_ollama_service()`, `_stop_ollama_service()`에서 `subprocess.Popen/run` 동기 호출

**해결**: `asyncio.create_subprocess_exec` 사용으로 변경

### 🟡 P2: Low (구조 개선)

#### P2-1: chat/chat_stream 중복 코드

**현상**: VLLMProvider와 AWSProvider의 chat/chat_stream 로직 거의 동일

**대안**: 공통 부모 클래스 `OpenAICompatibleProvider` 도입 검토 (향후 과제)

## 수정하지 않는 항목

- API 시그니처 변경
- 새로운 의존성 추가
- 대규모 리팩터링 (P2는 향후 과제로 보류)

## 테스트 계획

1. 기존 25개 테스트 통과 필수
2. 추가 테스트:
   - `test_temperature_zero_payload`: temperature=0 전달 검증
   - `test_provider_polymorphism`: 다형성 호출 검증

## 완료 조건

- [ ] P0 버그 2건 수정
- [ ] P1 안정성 개선 2건 수정
- [ ] 기존 테스트 25개 통과
- [ ] 신규 테스트 3개 이상 추가
- [ ] 총 28개+ 테스트 통과

## 백업 위치

```
backup/providers-20260128/
```
