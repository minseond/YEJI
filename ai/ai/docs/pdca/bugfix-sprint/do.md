# Do: YEJI AI 버그픽스 스프린트

## 구현 로그 (시계열)

### Phase 1: LOW 이슈 수정

**LOW-3: lifespan 컨텍스트 매니저**
- `main.py`: `@app.on_event("startup/shutdown")` → `@asynccontextmanager lifespan()`
- FastAPI 최신 패턴 적용

**LOW-1: 세션 ID full UUID**
- `api/saju.py:42`: `uuid.uuid4().hex[:12]` → `uuid.uuid4().hex` (32자)
- 예측 불가능성 강화

### Phase 2: MEDIUM 이슈 수정

**MEDIUM-3: CORS 메소드 명시**
- `main.py:71`: `allow_methods=["*"]` → `["GET", "POST", "OPTIONS"]`
- 불필요한 메소드 차단

**MEDIUM-2: 별자리 경계일 로직**
- `saju_calculator.py`: ZODIAC_SIGNS 구조 변경
  - Before: `(이름, 시작월, 시작일)`
  - After: `(이름, 시작월, 시작일, 종료월, 종료일)`
- `get_sun_sign()`: 경계일 판단 로직 단순화
- 검증: 1월 20일 → 물병자리 ✅

**MEDIUM-1: asyncio.Event 메모리 누수**
- `saju_service.py`: `_cleanup_session()` 메서드 추가
- `_answer_events.pop()` 및 `event.set()` 호출로 리소스 해제
- 5분마다 백그라운드 정리 태스크 실행

### Phase 3: HIGH 이슈 수정

**HIGH-2: TTL 기반 세션 캐시**
- `CachedSession` dataclass 도입
  - `state: SessionState`
  - `saju_profile: SajuProfile`
  - `created_at`, `last_accessed` 타임스탬프
  - `is_expired()`, `touch()` 메서드
- 세션 접근 시 TTL 갱신 (30분 기본)
- 백그라운드 정리 태스크로 만료 세션 자동 삭제

**HIGH-1: saju_profile 실제 사용**
- `AnalyzeRequest.saju_profile` → `CachedSession.saju_profile` 저장
- `_calculate_saju()`: saju_profile 인자 추가
- 실제 계산 로직 적용:
  ```python
  four_pillars, element_balance = self.calculator.calculate(
      birth_date=saju_profile.birth_date,
      birth_time=saju_profile.birth_time,
      gender=saju_profile.gender.value,
  )
  sun_sign = self.calculator.get_sun_sign(saju_profile.birth_date)
  ```
- Mock 결과에 실제 계산값 오버라이드

### Phase 4: 테스트 및 검증

**린트 체크**
```
$ uv run ruff check src/ --fix
All checks passed!
```

**유닛 테스트**
```
$ uv run pytest tests/ -v
8 passed in 2.36s
```

**통합 테스트**
```
POST /v1/saju/analyze (1990-01-20 출생)
→ session_id: sess_9c6b03e4d4e94d99af46236032c76110 (32자)

GET /v1/saju/stream/{session_id}
→ sun_sign: "물병자리" (경계일 정확)
→ four_pillars: {"year": "경오", "month": "병자", "day": "을사", "hour": "계미"}
→ day_master: "을목" (실제 계산값)
```

## 구현 중 학습

1. **FastAPI lifespan**: `@app.on_event()`는 deprecated, asynccontextmanager 패턴 권장
2. **TTL 캐시 패턴**: Redis 없이도 asyncio.create_task로 백그라운드 정리 가능
3. **별자리 계산**: 시작-종료 범위로 정의하면 경계일 처리 단순화
4. **dataclass**: Pydantic 모델과 조합하여 경량 캐시 객체 생성 가능

## 변경된 파일

```
src/yeji_ai/
├── main.py                 # lifespan, CORS 수정
├── api/saju.py             # 세션 ID full UUID
├── engine/saju_calculator.py # 별자리 로직 수정
└── services/saju_service.py  # TTL 캐시, saju_profile 연동, 메모리 누수 수정
```
