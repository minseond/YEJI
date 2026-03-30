# 백그라운드 캐싱 계획서

**작성일**: 2026-02-04
**버전**: v1.0
**상태**: 계획 수립 완료

---

## 목차

1. [Quick Summary 캐싱 계획](#1-quick-summary-캐싱-계획)
2. [타로 캐싱 계획](#2-타로-캐싱-계획)
3. [화투 캐싱 계획](#3-화투-캐싱-계획)
4. [우선순위 및 실행 로드맵](#4-우선순위-및-실행-로드맵)

---

## 1. Quick Summary 캐싱 계획

### 1.1 현재 상태

| 항목 | 상태 |
|------|------|
| API 엔드포인트 | `/v1/fortune/quick-summary` (구현 완료) |
| 캐시 키 패턴 | `quick_summary:{fortune_type}:{birth_info}:{category}` |
| 배치 스크립트 | `scripts/batch_quick_summary_cache.py` (구현 완료) |
| Progressive 캐싱 | `progressive_cache_service.py` (구현 완료) |

### 1.2 캐싱 전략

#### A. 배치 캐싱 실행 계획

```bash
# 1단계: Redis에서 기존 fortune 키 스캔
redis-cli --scan --pattern 'fortune:eastern:*' > eastern_keys.txt
redis-cli --scan --pattern 'fortune:western:*' > western_keys.txt

# 2단계: 배치 캐싱 실행
cat eastern_keys.txt | python scripts/batch_quick_summary_cache.py \
    --api-base https://i14a605.p.ssafy.io/ai-dev \
    --type eastern \
    --concurrency 3

cat western_keys.txt | python scripts/batch_quick_summary_cache.py \
    --api-base https://i14a605.p.ssafy.io/ai-dev \
    --type western \
    --concurrency 3
```

#### B. 실행 시간 권장

| 환경 | 실행 시간 | 이유 |
|------|-----------|------|
| 개발 서버 | 언제든 가능 | 트래픽 없음 |
| 프로덕션 | **03:00 - 05:00 KST** | 트래픽 최저 시간대 |

#### C. Rate Limiting 설정

```python
# 현재 설정 (batch_quick_summary_cache.py)
RATE_LIMIT_DELAY = 0.1  # 100ms 간격
MAX_CONCURRENCY = 3     # 동시 처리 3개

# 권장 설정 (프로덕션)
RATE_LIMIT_DELAY = 0.2  # 200ms 간격 (보수적)
MAX_CONCURRENCY = 2     # 동시 처리 2개
```

#### D. 예상 처리량

| Fortune 수 | 카테고리 | 총 호출 | 예상 시간 (100ms 간격) |
|------------|----------|---------|------------------------|
| 100개 | 5개 | 500회 | ~50초 |
| 500개 | 5개 | 2,500회 | ~4분 10초 |
| 1,000개 | 5개 | 5,000회 | ~8분 20초 |

### 1.3 모니터링

```bash
# 성공/실패 카운트 (스크립트 출력)
# ✅ 성공: 500
# ❌ 실패: 2
# 📦 총 처리: 502

# Redis 키 개수 확인
redis-cli KEYS "quick_summary:*" | wc -l

# 캐시 히트율 모니터링
redis-cli INFO stats | grep keyspace
```

### 1.4 실행 우선순위: **HIGH**

- 배치 스크립트 이미 구현 완료
- 즉시 실행 가능
- 사용자 체감 성능 개선 효과 큼

---

## 2. 타로 캐싱 계획

### 2.1 현재 상태

| 항목 | 상태 |
|------|------|
| API 엔드포인트 | `/v1/fortune/tarot/reading` (구현 완료) |
| 카드 구성 | 78장 (메이저 22장 + 마이너 56장) |
| 스프레드 | 3장 (과거/현재/미래) |
| 캐싱 | **없음** |

### 2.2 조합 수 분석

```
전체 조합 수 계산:
- 78장 중 3장 선택 (순서 있음): 78 × 77 × 76 = 456,456
- 각 카드 방향 2가지: 456,456 × 2³ = 3,651,648

→ 약 365만 조합 → 전체 캐싱 비현실적
```

### 2.3 대안 전략

#### A. 카드별 해석 캐싱 (권장)

```
카드별 위치+방향 조합:
- 78장 × 3위치(과거/현재/미래) × 2방향 = 468개

캐시 키 패턴:
  tarot:card:{card_code}:{position}:{orientation}
  예: tarot:card:FOOL:PAST:UPRIGHT
```

**장점**:
- 관리 가능한 캐시 크기 (468개)
- 카드 해석 재사용 가능
- LLM 호출 전 프리셋으로 활용

**구현 방안**:
```python
# 카드별 해석 프리셋 생성
TAROT_INTERPRETATIONS = {
    ("FOOL", "PAST", "UPRIGHT"): {
        "keywords": ["새로운 시작", "순수함", "모험"],
        "interpretation": "과거에는 새로운 시작의 에너지가..."
    },
    # ... 468개 조합
}
```

#### B. 인기 조합 캐싱 (선택적)

```python
# 인기 조합 추적
POPULAR_COMBINATIONS = Counter()

# 조회 시 카운트 증가
def track_combination(cards: list[str]):
    key = tuple(sorted(cards))
    POPULAR_COMBINATIONS[key] += 1

# 상위 N개 조합만 캐싱
TOP_N = 100
```

**단점**:
- 조합이 매우 분산되어 캐시 히트율 낮음
- 복잡도 대비 효과 미미

### 2.4 권장사항

| 전략 | 우선순위 | 이유 |
|------|----------|------|
| **카드별 해석 프리셋** | HIGH | 468개로 관리 가능, 폴백 용도 |
| 인기 조합 캐싱 | LOW | 히트율 낮음, ROI 부족 |
| 전체 조합 캐싱 | **SKIP** | 비현실적 |

### 2.5 대안: LLM 응답 품질 개선

타로는 캐싱보다 **LLM 프롬프트 품질 개선**에 집중:

1. 카드별 키워드/상징 프리셋 강화
2. 스프레드 위치별 해석 가이드라인
3. 질문 유형별 응답 템플릿

### 2.6 실행 우선순위: **MEDIUM**

- 카드별 해석 프리셋 468개 작성 필요
- 프롬프트 품질 개선이 더 효과적

---

## 3. 화투 캐싱 계획

### 3.1 현재 상태

| 항목 | 상태 |
|------|------|
| API 엔드포인트 | `/v1/fortune/hwatu/reading` |
| 카드 구성 | 48장 (12월 × 4종류) |
| 스프레드 | 4장 (본인/상대/과정/결과) |
| 구현 상태 | **미구현 (NotImplementedError)** |
| 캐싱 | 없음 |

### 3.2 조합 수 분석

```
전체 조합 수 계산:
- 48장 중 4장 선택 (순서 있음): 48 × 47 × 46 × 45 = 4,669,920

→ 약 467만 조합 → 전체 캐싱 비현실적
```

### 3.3 대안 전략

#### A. 카드별 위치 해석 캐싱 (권장)

```
카드별 위치 조합:
- 48장 × 4위치 = 192개

캐시 키 패턴:
  hwatu:card:{card_code}:{position}
  예: hwatu:card:JANUARY_CRANE:SELF
```

**장점**:
- 매우 작은 캐시 크기 (192개)
- 카드-위치별 기본 해석 제공

#### B. 월별 특수 조합 캐싱

```python
# 같은 월 카드 2장 이상 시 특별 해석
MONTH_PAIR_INTERPRETATIONS = {
    "JANUARY": {  # 1월 (송학)
        "meaning": "시작과 장수의 기운이 강해집니다",
        "advice": "새로운 일을 시작하기 좋은 때입니다"
    },
    # ... 12개월
}
```

**조합 수**: 12개월 × 위치조합 ≈ 100개 미만

### 3.4 권장사항

| 전략 | 우선순위 | 이유 |
|------|----------|------|
| **카드별 위치 해석** | MEDIUM | 192개, 서비스 구현 후 적용 |
| 월별 특수 조합 | LOW | 부가 기능 |
| 전체 조합 캐싱 | **SKIP** | 비현실적 |

### 3.5 선행 작업 필요

화투 캐싱 전에 먼저:
1. `HwatuService` 구현 완료
2. 화투 카드 해석 프리셋 작성
3. API 엔드포인트 테스트

### 3.6 실행 우선순위: **LOW**

- 서비스 자체가 미구현 상태
- 서비스 구현 완료 후 캐싱 검토

---

## 4. 우선순위 및 실행 로드맵

### 4.1 우선순위 요약

| 순위 | 대상 | 작업 | 예상 소요 |
|------|------|------|-----------|
| **1** | Quick Summary | 배치 스크립트 실행 | 1시간 |
| **2** | 타로 | 카드별 해석 프리셋 (468개) | 2-3일 |
| **3** | 화투 | 서비스 구현 완료 후 진행 | TBD |

### 4.2 Phase 1: Quick Summary (즉시 실행 가능)

```bash
# Step 1: SSH로 서버 접속
ssh ubuntu@i14a605.p.ssafy.io

# Step 2: Redis 키 추출
redis-cli --scan --pattern 'fortune:*' > /tmp/fortune_keys.txt

# Step 3: 배치 캐싱 실행 (dry-run 먼저)
cat /tmp/fortune_keys.txt | python batch_quick_summary_cache.py --dry-run

# Step 4: 실제 실행
cat /tmp/fortune_keys.txt | python batch_quick_summary_cache.py \
    --api-base https://i14a605.p.ssafy.io/ai \
    --concurrency 2
```

### 4.3 Phase 2: 타로 프리셋 (2주 내)

1. 메이저 아르카나 22장 × 3위치 × 2방향 = 132개 해석
2. 마이너 아르카나 56장 × 3위치 × 2방향 = 336개 해석
3. JSON 파일로 저장: `data/tarot_interpretations.json`

### 4.4 Phase 3: 화투 (서비스 구현 후)

1. `HwatuService` 구현 완료
2. 48장 × 4위치 = 192개 해석 프리셋
3. 월별 특수 조합 12개

---

## 5. 모니터링 및 알림

### 5.1 캐시 상태 대시보드

```python
# Redis 캐시 통계 조회 스크립트
async def get_cache_stats():
    stats = {
        "quick_summary": await redis.keys("quick_summary:*"),
        "fortune_eastern": await redis.keys("fortune:eastern:*"),
        "fortune_western": await redis.keys("fortune:western:*"),
    }
    return {k: len(v) for k, v in stats.items()}
```

### 5.2 Slack 알림 (선택)

```python
# 배치 완료 시 Slack 알림
def notify_completion(success: int, fail: int):
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    message = f"✅ 캐싱 완료: 성공 {success}, 실패 {fail}"
    httpx.post(webhook_url, json={"text": message})
```

---

## 6. 결론

### 6.1 즉시 실행 가능

- **Quick Summary 배치 캐싱**: 스크립트 완성, 실행만 하면 됨

### 6.2 추가 개발 필요

- **타로 프리셋**: 468개 해석 작성 (수동 또는 LLM 생성)
- **화투 서비스**: 구현 완료 후 캐싱 전략 적용

### 6.3 캐싱 불가

- **타로/화투 전체 조합**: 수백만 조합으로 비현실적
- 대신 **카드별 프리셋 + 실시간 LLM 조합** 전략 권장
