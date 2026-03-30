#!/bin/bash
# 백그라운드 캐싱 실행 스크립트
#
# 사용법:
#   ./scripts/run_background_caching.sh [dev|prod] [dry-run]
#
# 예시:
#   ./scripts/run_background_caching.sh dev           # 개발서버 실행
#   ./scripts/run_background_caching.sh prod dry-run  # 프로덕션 dry-run
#   ./scripts/run_background_caching.sh prod          # 프로덕션 실행

set -e

# 환경 설정
ENV="${1:-dev}"
DRY_RUN="${2:-}"

if [ "$ENV" == "prod" ]; then
    API_BASE="https://i14a605.p.ssafy.io/ai"
    REDIS_HOST="localhost"
    CONCURRENCY=2
    DELAY_MS=200
else
    API_BASE="https://i14a605.p.ssafy.io/ai-dev"
    REDIS_HOST="localhost"
    CONCURRENCY=3
    DELAY_MS=100
fi

echo "=============================================="
echo "🚀 백그라운드 캐싱 시작"
echo "=============================================="
echo "환경: $ENV"
echo "API: $API_BASE"
echo "동시처리: $CONCURRENCY"
echo "Dry-run: ${DRY_RUN:-no}"
echo "=============================================="

# 작업 디렉토리
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

# 임시 파일
KEYS_FILE="/tmp/fortune_keys_$(date +%Y%m%d_%H%M%S).txt"

# Step 1: Redis 키 추출
echo ""
echo "📥 Step 1: Redis에서 fortune 키 추출..."
redis-cli -h "$REDIS_HOST" --scan --pattern 'fortune:*' > "$KEYS_FILE"
KEY_COUNT=$(wc -l < "$KEYS_FILE")
echo "   발견된 키: $KEY_COUNT 개"

if [ "$KEY_COUNT" -eq 0 ]; then
    echo "❌ 처리할 키가 없습니다."
    exit 0
fi

# Step 2: 배치 캐싱 실행
echo ""
echo "🔄 Step 2: Quick Summary 배치 캐싱..."

if [ -n "$DRY_RUN" ]; then
    echo "   (DRY-RUN 모드)"
    cat "$KEYS_FILE" | python scripts/batch_quick_summary_cache.py \
        --api-base "$API_BASE" \
        --concurrency "$CONCURRENCY" \
        --dry-run
else
    cat "$KEYS_FILE" | python scripts/batch_quick_summary_cache.py \
        --api-base "$API_BASE" \
        --concurrency "$CONCURRENCY"
fi

# Step 3: 캐시 통계
echo ""
echo "📊 Step 3: 캐시 통계..."
QUICK_SUMMARY_COUNT=$(redis-cli -h "$REDIS_HOST" KEYS "quick_summary:*" | wc -l)
echo "   Quick Summary 캐시: $QUICK_SUMMARY_COUNT 개"

# 정리
rm -f "$KEYS_FILE"

echo ""
echo "=============================================="
echo "✅ 백그라운드 캐싱 완료"
echo "=============================================="
