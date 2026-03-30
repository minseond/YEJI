# Plan: YEJI AI 버그픽스 스프린트

## 가설 (Hypothesis)

발견된 8개 이슈를 우선순위별로 수정하여 프로덕션 준비 상태로 만든다.
인메모리 세션 저장소는 Redis 대신 만료 기반 캐시로 단순화한다 (MVP 스코프).

## 예상 결과 (Expected Outcomes)

- HIGH 이슈 2개 수정 완료
- MEDIUM 이슈 3개 수정 완료
- LOW 이슈 3개 수정 완료
- 기존 테스트 통과 유지
- 보안 취약점 해결

## 이슈 분석 및 해결책

### HIGH-1: saju_profile 미사용 버그

**위치**: `saju_service.py:121-124`
**문제**:
```python
async def _calculate_saju(self, session: SessionState) -> SajuResult:
    # TODO: 실제 SajuCalculator 연동
    return await self.calculator.calculate_mock()
```
**원인**: AnalyzeRequest에 saju_profile이 전달되지만 session에 저장 안됨
**해결**:
1. SessionState에 saju_profile 필드 추가
2. start_analysis에서 saju_profile 저장
3. _calculate_saju에서 실제 계산 로직 연동

### HIGH-2: 인메모리 세션 저장소

**위치**: `saju_service.py:34-37`
**문제**: 서버 재시작시 세션 소실
**해결 (MVP)**:
- Redis 대신 TTL 기반 만료 캐시 구현
- asyncio.create_task로 백그라운드 정리
- 프로덕션에서 Redis로 교체 가능하도록 인터페이스 분리

### MEDIUM-1: asyncio.Event 메모리 누수

**위치**: `saju_service.py:36`
**문제**: `_answer_events` dict 정리 안됨
**해결**: 세션 완료/만료 시 cleanup 로직 추가

### MEDIUM-2: 별자리 경계일 버그

**위치**: `saju_calculator.py:171-186`
**문제**:
```python
for sign, start_month, start_day in ZODIAC_SIGNS:
    if month == start_month and day >= start_day:
        return sign
    # 복잡한 로직 - 1월 20일 등 경계일 오류
```
**해결**: 일수 기반 비교로 단순화

### MEDIUM-3: CORS allow_methods=["*"]

**위치**: `main.py:52`
**해결**: `["GET", "POST", "OPTIONS"]` 명시

### LOW-1: 세션 ID 예측 가능성

**위치**: `api/saju.py:42`
**문제**: `uuid.uuid4().hex[:12]` (12자만 사용)
**해결**: full UUID 사용

### LOW-2: 에러 메시지 노출

**위치**: 여러 곳 `str(e)`
**해결**: 프로덕션용 generic 에러 메시지

### LOW-3: deprecated @app.on_event()

**위치**: `main.py:59-71`
**해결**: lifespan 컨텍스트 매니저 사용

## 리스크 및 대응

| 리스크 | 영향도 | 대응 |
|--------|--------|------|
| saju_profile 연동시 계산 로직 검증 필요 | 중 | Mock 결과와 비교 테스트 |
| 캐시 만료 타이밍 | 하 | 30분 기본값, 설정 가능 |
| 기존 테스트 실패 가능 | 중 | 수정 전 테스트 실행 확인 |

## 실행 순서

1. LOW 이슈 (breaking change 없음, 안전)
2. MEDIUM 이슈 (로직 변경)
3. HIGH 이슈 (핵심 기능)
4. 테스트 실행 및 검증
