# Redis 영구 캐싱 가이드

## 개요

동일한 생년월일+출생시간 조합의 운세 결과를 Redis에 캐싱하여 LLM API 호출 비용을 절감합니다.

## 아키텍처

### 캐싱 전략

```
1. Redis 조회 (birth_date + birth_time 조합)
   ├─ 캐시 히트 → 즉시 반환 (LLM 호출 생략)
   └─ 캐시 미스 → 2단계로 진행

2. 메모리 폴백 (fortune_id로 조회)
   ├─ 세션 내 메모리에 있으면 반환
   └─ 없으면 3단계로 진행

3. LLM 생성 (신규)
   ├─ 동양/서양 운세 병렬 생성
   ├─ Redis에 캐싱 (TTL 24시간)
   └─ 메모리에도 저장 (세션 유지)
```

### Graceful Degradation

Redis 연결 실패 시에도 서비스는 정상 동작:

- **Redis 연결 실패**: 메모리 캐시로 폴백 (세션 내에서만 유효)
- **Redis 쓰기 실패**: 로그 경고 후 메모리에만 저장
- **Redis 읽기 실패**: 메모리 캐시 조회 시도

## 설정

### 환경변수

```bash
# .env 파일
REDIS_URL=redis://localhost:6379
```

### config.py

```python
class Settings(BaseSettings):
    redis_url: str = Field(default="redis://localhost:6379", description="Redis URL")
```

## 사용법

### 티키타카 서비스에서 자동 적용

```python
from yeji_ai.services.tikitaka_service import TikitakaService

service = TikitakaService()

# 운세 조회 또는 생성 (자동으로 Redis 캐싱 적용)
eastern, western, e_id, w_id, source = await service.get_or_create_fortunes(
    birth_date="1990-05-15",
    birth_time="14:30",
)

# source 값:
# - "redis": Redis 캐시에서 조회
# - "memory": 메모리 캐시에서 조회
# - "created": LLM으로 신규 생성
```

### 직접 Redis 클라이언트 사용

```python
from yeji_ai.clients.redis_client import cache_fortune, get_cached_fortune

# 캐싱
result_dict = eastern_result.model_dump()
success = await cache_fortune(
    birth_date="1990-05-15",
    birth_time="14:30",
    fortune_type="eastern",
    result=result_dict,
    ttl_seconds=86400,  # 24시간
)

# 조회
cached = await get_cached_fortune(
    birth_date="1990-05-15",
    birth_time="14:30",
    fortune_type="eastern",
)
```

## 캐시 키 형식

```
yeji:{fortune_type}:{birth_date}:{birth_time}
```

### 예시

```
yeji:eastern:1990-05-15:14:30
yeji:western:1990-05-15:14:30
yeji:eastern:1990-05-15:unknown  # birth_time이 None인 경우
```

## TTL (Time-To-Live)

- **기본값**: 24시간 (86400초)
- **이유**: 운세는 날짜가 바뀌면 새로 생성되어야 하므로, 하루 단위로 캐시 무효화

## 성능 지표

### LLM 호출 절감

- **캐시 히트 시**: LLM 호출 0회 (동양+서양 모두 생략)
- **캐시 미스 시**: LLM 호출 2회 (동양+서양)

### 응답 속도

- **캐시 히트**: ~100ms (Redis 조회)
- **캐시 미스**: ~3-5초 (LLM 생성)

### 예상 비용 절감

동일 생년월일+시간 조합의 요청이 1일 내 N번 발생하는 경우:

- **절감률**: (N-1)/N × 100%
- **예시**: 10명이 동일 조합 요청 → 90% 비용 절감

## 모니터링

### 로그 이벤트

```python
# Redis 연결 성공
logger.info("redis_connected", url="redis://localhost...")

# Redis 연결 실패 (graceful degradation)
logger.warning("redis_connection_failed", error="Connection refused")

# 캐시 히트
logger.info("fortune_cache_hit", key="yeji:eastern:1990-05-15:14:30")

# 캐시 미스
logger.debug("fortune_cache_miss", key="yeji:eastern:1990-05-15:14:30")

# 캐싱 성공
logger.info("fortune_cached", key="yeji:eastern:1990-05-15:14:30", ttl=86400)

# 캐싱 실패 (폴백)
logger.warning("fortune_cache_failed", key="...", error="...")
```

### 캐시 히트율 확인

```bash
# Redis CLI에서 키 개수 확인
redis-cli KEYS "yeji:*" | wc -l

# 특정 키 조회
redis-cli GET "yeji:eastern:1990-05-15:14:30"

# TTL 확인
redis-cli TTL "yeji:eastern:1990-05-15:14:30"
```

## 테스트

### 단위 테스트

```bash
# Redis 캐싱 테스트
uv run pytest tests/test_redis_cache.py -v

# 티키타카 서비스 통합 테스트 (Redis 포함)
uv run pytest tests/test_tikitaka_service.py -v
```

### 수동 테스트

```bash
# 1. Redis 서버 시작
redis-server

# 2. AI 서버 시작
uvicorn yeji_ai.main:app --reload

# 3. API 호출 (첫 번째 - LLM 생성)
curl -X POST http://localhost:8000/v1/tikitaka/chat/category-greeting \
  -H "Content-Type: application/json" \
  -d '{
    "birth_date": "1990-05-15",
    "birth_time": "14:30",
    "category": "LOVE"
  }'

# 4. 동일 요청 재호출 (두 번째 - Redis 캐시 히트)
# 응답 속도가 훨씬 빨라야 함
curl -X POST http://localhost:8000/v1/tikitaka/chat/category-greeting \
  -H "Content-Type: application/json" \
  -d '{
    "birth_date": "1990-05-15",
    "birth_time": "14:30",
    "category": "LOVE"
  }'
```

## 트러블슈팅

### Redis 연결 실패

**증상**: `redis_connection_failed` 경고 로그

**원인**:
- Redis 서버가 실행 중이지 않음
- `REDIS_URL` 환경변수 미설정 또는 잘못된 URL

**해결**:
```bash
# Redis 서버 상태 확인
redis-cli ping  # PONG 응답 확인

# Redis 서버 시작
redis-server

# 환경변수 확인
echo $REDIS_URL
```

### 캐시 미스가 계속 발생

**증상**: 동일 요청인데도 캐시 히트가 안 됨

**원인**:
- `birth_time` 값이 미세하게 다름 (예: "14:30" vs "14:30:00")
- TTL 만료

**해결**:
```bash
# Redis CLI에서 키 확인
redis-cli KEYS "yeji:*"

# 특정 키의 TTL 확인
redis-cli TTL "yeji:eastern:1990-05-15:14:30"
# 반환값: -2 (키 없음), -1 (TTL 없음), 양수 (남은 시간)
```

### 메모리 사용량 증가

**증상**: Redis 메모리 사용량이 계속 증가

**원인**:
- TTL이 설정되지 않아 캐시가 무기한 유지

**해결**:
```bash
# 모든 yeji 키 확인 및 TTL 검사
redis-cli KEYS "yeji:*" | while read key; do
  echo "$key: $(redis-cli TTL $key)"
done

# TTL이 -1인 키는 수동으로 삭제 또는 TTL 설정
redis-cli EXPIRE "yeji:eastern:1990-05-15:14:30" 86400
```

## 배포 체크리스트

### 개발 환경

- [ ] Redis 서버 로컬 실행 확인
- [ ] `REDIS_URL=redis://localhost:6379` 설정
- [ ] 캐시 히트/미스 로그 확인

### 프로덕션 환경

- [ ] AWS ElastiCache Redis 인스턴스 생성
- [ ] 보안 그룹 설정 (AI 서버에서 접근 가능하도록)
- [ ] `REDIS_URL` 환경변수 설정 (ElastiCache 엔드포인트)
- [ ] Redis 연결 테스트
- [ ] 모니터링 대시보드 설정 (캐시 히트율, 메모리 사용량)

## 향후 개선 사항

### P1 (우선순위 높음)

- [ ] Redis Cluster 지원 (고가용성)
- [ ] 캐시 워밍 (인기 생년월일 미리 캐싱)

### P2 (우선순위 중간)

- [ ] 캐시 히트율 메트릭 수집 (Prometheus)
- [ ] 세밀한 TTL 조정 (카테고리별 차등)

### P3 (우선순위 낮음)

- [ ] LRU 정책 적용 (메모리 부족 시 오래된 캐시 삭제)
- [ ] 캐시 무효화 API (특정 birth_date 캐시 강제 삭제)

## 참고 자료

- [Redis 공식 문서](https://redis.io/docs/)
- [redis-py 비동기 가이드](https://redis.readthedocs.io/en/stable/examples/asyncio_examples.html)
- [AWS ElastiCache for Redis](https://aws.amazon.com/elasticache/redis/)
