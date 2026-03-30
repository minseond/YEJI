#!/usr/bin/env python3
"""Redis 백업 스크립트

주기적으로 Redis 데이터를 JSON 파일로 백업합니다.

사용법:
    # 단일 실행
    python scripts/redis_backup.py

    # 주기적 실행 (1시간마다)
    python scripts/redis_backup.py --schedule 3600

    # 복구
    python scripts/redis_backup.py --restore data/redis_backup_YYYYMMDD_HHMMSS.json
"""

import argparse
import json
import os
import time
from datetime import datetime
from pathlib import Path

import redis


def get_redis_client(host: str = "localhost", port: int = 6379) -> redis.Redis:
    """Redis 클라이언트 생성"""
    return redis.Redis(host=host, port=port, decode_responses=True)


def backup_redis(
    client: redis.Redis,
    backup_dir: str = "data/backups",
    source_name: str = "redis",
) -> str:
    """Redis 전체 데이터 백업

    Args:
        client: Redis 클라이언트
        backup_dir: 백업 저장 디렉토리
        source_name: 백업 소스 이름

    Returns:
        백업 파일 경로
    """
    # 백업 디렉토리 생성
    Path(backup_dir).mkdir(parents=True, exist_ok=True)

    # 백업 데이터 구조
    backup = {
        "backup_time": datetime.now().isoformat(),
        "source": source_name,
        "total_keys": 0,
        "data": {},
    }

    # 모든 키 조회
    all_keys = client.keys("*")
    backup["total_keys"] = len(all_keys)

    for key in all_keys:
        try:
            key_type = client.type(key)
            ttl = client.ttl(key)

            if key_type == "string":
                value = client.get(key)
                # JSON 파싱 시도
                try:
                    value = json.loads(value) if value else None
                except (json.JSONDecodeError, TypeError):
                    pass
                backup["data"][key] = {"type": "string", "value": value, "ttl": ttl}

            elif key_type == "hash":
                backup["data"][key] = {
                    "type": "hash",
                    "value": client.hgetall(key),
                    "ttl": ttl,
                }

            elif key_type == "list":
                backup["data"][key] = {
                    "type": "list",
                    "value": client.lrange(key, 0, -1),
                    "ttl": ttl,
                }

            elif key_type == "set":
                backup["data"][key] = {
                    "type": "set",
                    "value": list(client.smembers(key)),
                    "ttl": ttl,
                }

            elif key_type == "zset":
                backup["data"][key] = {
                    "type": "zset",
                    "value": client.zrange(key, 0, -1, withscores=True),
                    "ttl": ttl,
                }

            else:
                backup["data"][key] = {"type": key_type, "value": None, "ttl": ttl}

        except Exception as e:
            print(f"[WARN] 키 백업 실패: {key} - {e}")

    # 파일 저장
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"{backup_dir}/redis_backup_{timestamp}.json"

    with open(backup_file, "w", encoding="utf-8") as f:
        json.dump(backup, f, ensure_ascii=False, indent=2)

    print(f"[OK] 백업 완료: {backup_file} ({backup['total_keys']}개 키)")

    # 오래된 백업 정리 (최근 10개만 유지)
    cleanup_old_backups(backup_dir, keep=10)

    return backup_file


def restore_redis(
    client: redis.Redis,
    backup_file: str,
    ttl_override: int | None = None,
) -> int:
    """백업 파일에서 Redis 복구

    Args:
        client: Redis 클라이언트
        backup_file: 백업 파일 경로
        ttl_override: TTL 오버라이드 (초, None이면 원본 TTL 사용)

    Returns:
        복구된 키 수
    """
    with open(backup_file, "r", encoding="utf-8") as f:
        backup = json.load(f)

    print(f"[INFO] 백업 파일: {backup_file}")
    print(f"[INFO] 백업 시간: {backup['backup_time']}")
    print(f"[INFO] 총 키 수: {backup['total_keys']}")

    restored = 0
    default_ttl = ttl_override or 31536000  # 기본 1년

    for key, data in backup["data"].items():
        try:
            ttl = ttl_override or data.get("ttl", -1)
            if ttl <= 0:
                ttl = default_ttl

            if data["type"] == "string":
                value = data["value"]
                if isinstance(value, (dict, list)):
                    value = json.dumps(value, ensure_ascii=False)
                client.setex(key, ttl, value)
                restored += 1

            elif data["type"] == "hash":
                if data["value"]:
                    client.delete(key)
                    client.hset(key, mapping=data["value"])
                    client.expire(key, ttl)
                    restored += 1

            elif data["type"] == "list":
                if data["value"]:
                    client.delete(key)
                    client.rpush(key, *data["value"])
                    client.expire(key, ttl)
                    restored += 1

            elif data["type"] == "set":
                if data["value"]:
                    client.delete(key)
                    client.sadd(key, *data["value"])
                    client.expire(key, ttl)
                    restored += 1

        except Exception as e:
            print(f"[WARN] 복구 실패: {key} - {e}")

    print(f"[OK] 복구 완료: {restored}/{backup['total_keys']}개")
    return restored


def cleanup_old_backups(backup_dir: str, keep: int = 10) -> None:
    """오래된 백업 파일 정리"""
    backup_files = sorted(Path(backup_dir).glob("redis_backup_*.json"))

    if len(backup_files) > keep:
        for old_file in backup_files[:-keep]:
            old_file.unlink()
            print(f"[INFO] 오래된 백업 삭제: {old_file}")


def run_scheduled_backup(
    client: redis.Redis,
    interval_seconds: int,
    backup_dir: str = "data/backups",
) -> None:
    """주기적 백업 실행"""
    print(f"[INFO] 주기적 백업 시작 (간격: {interval_seconds}초)")

    while True:
        try:
            backup_redis(client, backup_dir)
        except Exception as e:
            print(f"[ERROR] 백업 실패: {e}")

        print(f"[INFO] 다음 백업까지 {interval_seconds}초 대기...")
        time.sleep(interval_seconds)


def main():
    parser = argparse.ArgumentParser(description="Redis 백업/복구 스크립트")
    parser.add_argument("--host", default="localhost", help="Redis 호스트")
    parser.add_argument("--port", type=int, default=6379, help="Redis 포트")
    parser.add_argument("--backup-dir", default="data/backups", help="백업 디렉토리")
    parser.add_argument("--schedule", type=int, help="주기적 백업 간격 (초)")
    parser.add_argument("--restore", help="복구할 백업 파일 경로")
    parser.add_argument("--ttl", type=int, help="복구 시 TTL 오버라이드 (초)")

    args = parser.parse_args()

    client = get_redis_client(args.host, args.port)

    # PING 테스트
    try:
        client.ping()
        print(f"[OK] Redis 연결 성공: {args.host}:{args.port}")
    except redis.ConnectionError:
        print(f"[ERROR] Redis 연결 실패: {args.host}:{args.port}")
        return 1

    if args.restore:
        # 복구 모드
        restore_redis(client, args.restore, args.ttl)
    elif args.schedule:
        # 주기적 백업 모드
        run_scheduled_backup(client, args.schedule, args.backup_dir)
    else:
        # 단일 백업
        backup_redis(client, args.backup_dir)

    return 0


if __name__ == "__main__":
    exit(main())
