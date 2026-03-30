# 비동기 최적화 패턴

> Python asyncio를 활용한 I/O 바운드 작업 병렬화 패턴

## 개요

FastAPI 서비스에서 독립적인 async 작업을 `asyncio.gather()`로 병렬화하여 응답 시간을 단축합니다.

## 패턴 1: 기본 병렬화

**문제**: 독립적인 I/O 작업이 직렬 실행되어 응답 시간 증가

```python
# Before (직렬, 4초)
result_a = await task_a()  # 2초
result_b = await task_b()  # 2초

# After (병렬, 2초)
import asyncio

result_a, result_b = await asyncio.gather(
    task_a(),
    task_b(),
)
```

**적용 조건**:
- 두 작업이 서로 독립적 (의존성 없음)
- 둘 다 I/O 바운드 (LLM 호출, HTTP 요청, DB 쿼리 등)

## 패턴 2: 2단계 병렬화 (의존성 있음)

**문제**: 일부 작업이 다른 작업의 결과에 의존

```python
# Before (직렬, 4초)
result_a = await task_a()  # 1초
result_b = await task_b()  # 1초
result_c = await task_c(result_a, result_b)  # 1초
result_d = await task_d(result_a, result_b)  # 1초

# After (2단계 병렬, 2초)
# Step 1: 독립 작업 병렬
result_a, result_b = await asyncio.gather(
    task_a(),
    task_b(),
)

# Step 2: 의존 작업 병렬 (Step 1 결과 필요)
result_c, result_d = await asyncio.gather(
    task_c(result_a, result_b),
    task_d(result_a, result_b),
)
```

**적용 예시**: saju_service.py
- Step 1: 동양/서양 해석 (독립)
- Step 2: 통합 의견/조언 (Step 1 결과 필요)

## 패턴 3: 조건부 병렬화 (early return 보존)

**문제**: 특정 조건에서 early return이 필요하지만 병렬화도 원함

```python
# After (조건부 병렬)
if mode != "block":
    # 병렬 실행 (early return 불필요)
    guard_result, intent_result = await asyncio.gather(
        run_guard(text),
        run_intent(text),
    )
else:
    # 직렬 실행 (early return 필요)
    guard_result = await run_guard(text)
    if guard_result.is_malicious:
        return early_response  # early return
    intent_result = await run_intent(text)
```

**적용 예시**: filter/pipeline.py
- `guard_mode == "block"`: 악성 감지 시 즉시 반환 (직렬)
- `guard_mode != "block"`: 로그만 기록 (병렬 가능)

## 패턴 4: AsyncGenerator 내 병렬 생성

**문제**: 스트리밍 응답에서 여러 메시지를 생성해야 함

```python
async def stream_messages() -> AsyncGenerator[dict, None]:
    # 내부 함수로 병렬 생성 가능
    async def _generate_msg_a() -> str:
        try:
            return await llm.generate_a()
        except Exception:
            return fallback_a

    async def _generate_msg_b() -> str:
        try:
            return await llm.generate_b()
        except Exception:
            return fallback_b

    # 병렬 생성 (초기 응답 시간 단축)
    msg_a, msg_b = await asyncio.gather(
        _generate_msg_a(),
        _generate_msg_b(),
    )

    # 순차 스트리밍 (UX 유지)
    for chunk in msg_a:
        yield {"event": "chunk", "data": chunk}
    for chunk in msg_b:
        yield {"event": "chunk", "data": chunk}
```

**적용 예시**: tikitaka_service.py
- 소이설/스텔라 메시지 병렬 생성
- 스트리밍은 순차 (소이설 먼저, 스텔라 나중)

## 체크리스트

### 병렬화 전
- [ ] `import asyncio` 존재 확인
- [ ] 작업 간 의존성 분석
- [ ] I/O 바운드 작업인지 확인
- [ ] early return 로직 파악

### 병렬화 후
- [ ] 기존 에러 핸들링 유지
- [ ] 기존 로깅 유지
- [ ] 테스트 통과 확인
- [ ] 린트 통과 확인

## 주의사항

1. **CPU 바운드 작업**: `asyncio.to_thread()` 사용
2. **동시성 제한**: `asyncio.Semaphore`로 GPU/외부 API 보호
3. **예외 처리**: `gather()`는 첫 예외에서 중단하지 않음 (모든 작업 완료)
4. **순서 보존**: `gather()` 결과는 입력 순서와 동일

## 성능 기대치

| 패턴 | Before | After | 개선율 |
|------|--------|-------|--------|
| 2개 병렬 | 4초 | 2초 | 50% |
| 4개 → 2단계 병렬 | 4초 | 2초 | 50% |
| 조건부 병렬 | 상황별 | 최대 50% | 가변 |

---

> **작성일**: 2026-01-31
> **참조**: `ai/docs/pdca/async-optimization/`
