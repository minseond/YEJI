"""궁합 API - 두 사람의 궁합 점수 및 메시지 반환

점수 계산은 기계적으로 수행하고,
메시지는 사전 생성된 풀에서 랜덤 선택합니다.
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from yeji_ai.services.compatibility_service import (
    PersonInput,
    calculate_compatibility,
)

router = APIRouter()


# ============================================================
# 요청/응답 스키마
# ============================================================

class PersonRequest(BaseModel):
    """개인 정보 요청"""
    birth_date: str = Field(
        ...,
        description="생년월일 (YYYY-MM-DD)",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        examples=["1995-03-15"],
    )
    gender: str | None = Field(
        None,
        description="성별 (M/F)",
        examples=["M", "F"],
    )
    name: str | None = Field(
        None,
        description="이름 (선택)",
        examples=["홍길동"],
    )


class CompatibilityRequest(BaseModel):
    """궁합 요청"""
    person1: PersonRequest = Field(..., description="첫 번째 사람")
    person2: PersonRequest = Field(..., description="두 번째 사람")


class ScoreDetail(BaseModel):
    """점수 상세"""
    total: int = Field(..., description="총점 (100점 만점)")
    east: int = Field(..., description="동양 점수 (50점 만점)")
    west: int = Field(..., description="서양 점수 (50점 만점)")


class CompatibilityResponse(BaseModel):
    """궁합 응답"""
    score: ScoreDetail = Field(..., description="점수 상세")
    grade: str = Field(..., description="등급 코드 (excellent/good/average/challenging/difficult)")
    grade_label: str = Field(..., description="등급 라벨 (천생연분/좋은궁합/보통/노력필요/상극)")
    message: dict = Field(..., description="궁합 메시지 (east/west)")


# ============================================================
# API 엔드포인트
# ============================================================

@router.post(
    "/compatibility",
    response_model=CompatibilityResponse,
    summary="궁합 분석",
    description="""
두 사람의 생년월일을 받아 궁합을 분석합니다.

## 점수 체계
- **동양 궁합 (50점)**: 일간 상생상극(20) + 오행 보완(15) + 지지 충합(15)
- **서양 궁합 (50점)**: 별자리(20) + 원소 조화(15) + 양태 조화(10) + 수비학(5)

## 등급
| 점수 | 등급 | 라벨 |
|------|------|------|
| 90-100 | excellent | 천생연분 |
| 70-89 | good | 좋은 궁합 |
| 50-69 | average | 보통 |
| 30-49 | challenging | 노력 필요 |
| 0-29 | difficult | 상극 |
""",
)
async def analyze_compatibility(request: CompatibilityRequest) -> CompatibilityResponse:
    """궁합 분석 API"""
    person1 = PersonInput(
        birth_date=request.person1.birth_date,
        gender=request.person1.gender,
        name=request.person1.name,
    )
    person2 = PersonInput(
        birth_date=request.person2.birth_date,
        gender=request.person2.gender,
        name=request.person2.name,
    )

    result = calculate_compatibility(person1, person2)

    return CompatibilityResponse(
        score=ScoreDetail(
            total=result.score,
            east=result.east_score,
            west=result.west_score,
        ),
        grade=result.grade,
        grade_label=result.grade_label,
        message=result.message,
    )
