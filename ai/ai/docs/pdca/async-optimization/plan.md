# Plan: 비동기 최적화 (P0~P3)

## 가설
API 응답 시간의 주요 병목은 직렬 실행되는 LLM 호출과 GPU 추론입니다.
`asyncio.gather()`로 독립적인 작업을 병렬화하면 40-60% 성능 향상이 예상됩니다.

## 목표 (정량적)

| 우선순위 | 파일 | 함수 | 예상 효과 |
|----------|------|------|----------|
| P0 | fortune_generator.py | generate_full() | 50% (4초→2초) |
| P1 | saju_service.py | _calculate_saju() | 50% (4초→2초) |
| P2 | filter/pipeline.py | filter() | 50% (200ms→100ms) |
| P3 | tikitaka_service.py | stream_interpretation() | 30% 초기 응답 단축 |

**총 예상 효과**: API 응답 시간 40-60% 감소

## 접근 방식

### 병렬화 패턴
```python
# Before (직렬)
result_a = await task_a()
result_b = await task_b()

# After (병렬)
result_a, result_b = await asyncio.gather(
    task_a(),
    task_b(),
)
```

### 의존성 처리 (2단계 병렬)
```python
# Step 1: 독립적인 작업 병렬
result_a, result_b = await asyncio.gather(task_a(), task_b())

# Step 2: 의존 작업 병렬 (Step 1 결과 필요)
result_c, result_d = await asyncio.gather(
    task_c(result_a, result_b),
    task_d(result_a, result_b),
)
```

### 조건부 병렬화 (early return 보존)
```python
if mode != "block":
    # 병렬 실행
    guard_result, intent_result = await asyncio.gather(...)
else:
    # 직렬 실행 (early return 필요)
    guard_result = await run_guard()
    if guard_result.is_malicious:
        return early_response
    intent_result = await run_intent()
```

## 리스크 및 완화 전략

| 리스크 | 완화 전략 |
|--------|----------|
| 병렬 실행 시 예외 처리 | asyncio.gather에 기존 try-except 유지 |
| 메모리 사용량 증가 | GPU 추론은 기존 Semaphore로 제어됨 |
| 디버깅 어려움 | structlog로 상세 로깅 유지 |
| 기존 테스트 실패 | 수정 전 테스트 통과 확인 |

## 제약 조건

- Python 3.11+ 문법 사용
- Pydantic v2 패턴 유지
- 기존 에러 핸들링 유지
- UX 영향 최소화 (스트리밍 순서 보존)

---

> **작성일**: 2026-01-31
> **상태**: ✅ 완료
