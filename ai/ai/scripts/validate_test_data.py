#!/usr/bin/env python3
"""생성된 테스트 데이터 검증 스크립트

birth_combinations_20s.json의 서양 점성술 데이터가
WesternFortuneDataV2 스키마와 호환되는지 검증합니다.
"""

import json
import sys
from pathlib import Path

import structlog

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(project_root))

from yeji_ai.models.user_fortune import WesternFortuneDataV2

logger = structlog.get_logger()


def main() -> None:
    """메인 실행 함수"""
    logger.info("validation_start")

    # 데이터 파일 로드
    data_file = Path(__file__).parent.parent / "data" / "test" / "birth_combinations_20s.json"
    with open(data_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    combinations = data["combinations"]
    logger.info("data_loaded", total_combinations=len(combinations))

    # 각 조합의 서양 점성술 데이터 검증
    valid_count = 0
    invalid_count = 0
    errors = []

    for combo in combinations:
        if not combo.get("saju_success"):
            continue

        western_data = combo.get("western", {})
        name = combo.get("name", "Unknown")

        # _legacy 필드 제거 (검증에서 제외)
        western_clean = {k: v for k, v in western_data.items() if k != "_legacy"}

        try:
            # Pydantic 모델로 검증
            validated = WesternFortuneDataV2(**western_clean)
            valid_count += 1
            logger.info(
                "validation_success",
                name=name,
                element=validated.element,
                main_sign=validated.stats.main_sign.name,
            )
        except Exception as e:
            invalid_count += 1
            error_msg = f"{name}: {str(e)}"
            errors.append(error_msg)
            logger.error(
                "validation_failed",
                name=name,
                error=str(e),
                error_type=type(e).__name__,
            )

    # 결과 출력
    print("\n" + "="*60)
    print("서양 점성술 데이터 검증 결과 (WesternFortuneDataV2)")
    print("="*60)
    print(f"\n✅ 검증 성공: {valid_count}개")
    print(f"❌ 검증 실패: {invalid_count}개")
    print(f"📊 성공률: {valid_count/(valid_count+invalid_count)*100:.1f}%")

    if errors:
        print(f"\n⚠️ 실패 케이스:")
        for error in errors:
            print(f"  - {error}")
    else:
        print(f"\n🎉 모든 데이터가 WesternFortuneDataV2 스키마와 호환됩니다!")

    print("="*60)

    logger.info(
        "validation_complete",
        valid_count=valid_count,
        invalid_count=invalid_count,
    )


if __name__ == "__main__":
    main()
