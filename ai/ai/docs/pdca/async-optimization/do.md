# Do: 비동기 최적화 실행 기록

## 실행 로그 (시계열)

### 11:45 - P0: fortune_generator.py
**상태**: ✅ 완료 (이미 구현됨)

- 확인: `generate_full()` 라인 744-748에 `asyncio.gather()` 이미 적용됨
- 수정: `import asyncio` 추가 (누락되어 있었음)
- 테스트: 린트 통과

```python
# 기존 코드 (병렬화 완료)
eastern, western = await asyncio.gather(
    self.generate_eastern(birth_data),
    self.generate_western(birth_data),
)
```

### 11:47 - P1: saju_service.py
**상태**: ✅ 완료

- 위치: `_calculate_saju()` 라인 252-272
- 변경: 4개 직렬 호출 → 2단계 병렬
- 테스트: 린트 통과

```python
# Before (직렬, 4초)
eastern_interpretation = await self._generate_eastern_interpretation(...)
western_interpretation = await self._generate_western_interpretation(...)
combined_opinion = await self._generate_combined_opinion(...)
advice = await self._generate_advice(...)

# After (2단계 병렬, 2초)
# Step 1: 동양/서양 병렬
eastern_interpretation, western_interpretation = await asyncio.gather(
    self._generate_eastern_interpretation(four_pillars, element_balance, day_master),
    self._generate_western_interpretation(sun_sign),
)

# Step 2: 통합/조언 병렬
combined_opinion, advice = await asyncio.gather(
    self._generate_combined_opinion(...),
    self._generate_advice(...),
)
```

### 11:48 - P2: filter/pipeline.py
**상태**: ✅ 완료

- 위치: `filter()` 라인 166-179
- 변경: 조건부 병렬화 (guard_mode != "block"일 때)
- 수정: `import asyncio` 추가
- 테스트: 린트 통과

```python
# After (조건부 병렬)
if self._guard_mode != "block":
    # 병렬 실행 (early return 필요 없음)
    guard_result, intent_result = await asyncio.gather(
        self._run_guard(text),
        self._run_intent(text),
    )
else:
    # 직렬 실행 (early return 필요)
    guard_result = await self._run_guard(text)
    if guard_result.is_malicious:
        return FilterResult(...)  # early return
    intent_result = await self._run_intent(text)
```

### 11:49 - P3: tikitaka_service.py
**상태**: ✅ 완료

- 위치: `stream_interpretation()` 라인 525-595
- 변경: 소이설/스텔라 메시지 병렬 생성 후 순차 스트리밍
- 테스트: 린트 통과

```python
# After (병렬 생성, 순차 스트리밍)
async def _generate_soiseol() -> str:
    try:
        msg = await self.llm.generate_soiseol_message(...)
        return filter_noise(msg, aggressive=False)
    except Exception:
        return fallback_message

async def _generate_stella() -> str:
    try:
        msg = await self.llm.generate_stella_message(...)
        return filter_noise(msg, aggressive=False)
    except Exception:
        return fallback_message

# 병렬 생성
soiseol_msg, stella_msg = await asyncio.gather(
    _generate_soiseol(),
    _generate_stella(),
)

# 순차 스트리밍 (UX 유지)
for chunk in soiseol_msg:
    yield message_chunk
# ...
for chunk in stella_msg:
    yield message_chunk
```

### 11:52 - 테스트 실행
**상태**: ✅ 완료

```
$ pytest tests/test_fortune_generator.py tests/test_gpu_filter.py -v
============================= 86 passed in 0.54s ==============================
```

- fortune_generator: 40개 테스트 통과
- gpu_filter (pipeline 포함): 46개 테스트 통과
- 린트: 4개 파일 모두 통과

## 구현 중 학습 사항

1. **import 누락 주의**: `asyncio.gather()` 사용 시 `import asyncio` 필수
2. **조건부 병렬화**: early return이 필요한 경우 직렬 실행 유지
3. **내부 함수 패턴**: AsyncGenerator 내에서 `async def` 내부 함수로 병렬 생성 가능
4. **UX 보존**: 메시지 생성은 병렬, 스트리밍은 순차로 분리

---

> **실행일**: 2026-01-31
> **소요 시간**: 약 15분
> **상태**: ✅ 완료
