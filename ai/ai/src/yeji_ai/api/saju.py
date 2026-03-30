"""사주 분석 API 엔드포인트"""

import uuid

import structlog
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from yeji_ai.models.schemas import (
    AnalyzeRequest,
    AnswerRequest,
    BaseResponse,
    ChatRequest,
)
from yeji_ai.services.saju_service import SajuService

router = APIRouter()
logger = structlog.get_logger()

# 서비스 인스턴스 (DI 패턴으로 개선 가능)
saju_service = SajuService()


class AnalyzeResponse(BaseModel):
    """분석 요청 응답"""

    session_id: str
    status: str
    message: str


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_saju(request: AnalyzeRequest):
    """
    사주 분석 요청

    1. 세션 생성
    2. 백그라운드에서 분석 시작
    3. SSE 스트리밍 URL 반환
    """
    # LOW-1: full UUID 사용 (예측 방지)
    session_id = f"sess_{uuid.uuid4().hex}"

    logger.info(
        "saju_analyze_requested",
        session_id=session_id,
        user_id=request.user_id,
        category=request.category,
        sub_category=request.sub_category,
    )

    # 세션 생성 및 분석 시작
    await saju_service.start_analysis(session_id, request)

    return AnalyzeResponse(
        session_id=session_id,
        status="analyzing",
        message=f"분석이 시작되었습니다. GET /v1/saju/stream/{session_id}로 결과를 받으세요.",
    )


@router.get("/stream/{session_id}")
async def stream_saju_result(session_id: str):
    """
    사주 결과 SSE 스트리밍

    이벤트 타입:
    - result_start: 분석 시작
    - result: 결과 데이터 (score, eastern, western, advice)
    - result_complete: 결과 완료
    - message: 토론 메시지
    - question: 중간 질문
    - pause: 사용자 응답 대기
    - complete: 전체 완료
    - error: 에러
    """
    logger.info("saju_stream_requested", session_id=session_id)

    # 세션 확인
    if not await saju_service.session_exists(session_id):
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    async def event_generator():
        """SSE 이벤트 생성기"""
        async for event in saju_service.stream_result(session_id):
            yield event

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/answer")
async def answer_question(request: AnswerRequest):
    """
    중간 질문 응답

    사용자가 질문에 답변하면 토론 재개
    """
    logger.info(
        "saju_answer_submitted",
        session_id=request.session_id,
        question_id=request.question_id,
        value=request.value,
    )

    if not await saju_service.session_exists(request.session_id):
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    await saju_service.submit_answer(request)

    return BaseResponse(
        success=True,
        message="응답이 반영되었습니다. 토론이 계속됩니다.",
    )


@router.post("/chat")
async def chat(request: ChatRequest):
    """
    추가 채팅

    분석 완료 후 추가 질문 처리
    """
    logger.info(
        "saju_chat_submitted",
        session_id=request.session_id,
        message=request.message[:50],
    )

    if not await saju_service.session_exists(request.session_id):
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    response = await saju_service.process_chat(request)

    return response


@router.get("/result/{session_id}")
async def get_result(session_id: str):
    """
    최종 결과 조회

    분석 완료 후 전체 결과 반환
    """
    logger.info("saju_result_requested", session_id=session_id)

    if not await saju_service.session_exists(session_id):
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    result = await saju_service.get_result(session_id)

    if not result:
        raise HTTPException(status_code=400, detail="분석이 아직 완료되지 않았습니다")

    return BaseResponse(success=True, data=result)
