"""티키타카 채팅 API 엔드포인트

## 사용 흐름 (권장)

### 방법 1: 원스톱 (사주 분석 포함)
```
POST /chat/turn/start
{
  "birth_date": "1990-05-15",
  "birth_time": "14:30",
  "category": "LOVE"
}
→ 내부에서 동/서양 운세 분석 후 첫 인사말 반환
```

### 방법 2: 기존 사주 재사용
```
1. 먼저 사주 분석 (선택)
   POST /fortune/eastern → fortune_key 획득
   POST /fortune/western → fortune_key 획득

2. 대화 시작 (사주 재사용)
   POST /chat/turn/start
   {
     "birth_date": "1990-05-15",
     "category": "LOVE",
     "eastern_fortune_key": "eastern:1990-05-15:14:30:M",
     "western_fortune_key": "western:1990-05-15:14:30"
   }
```

### 대화 이어가기
```
POST /chat/turn/continue
{
  "session_id": "abc123",
  "message": "더 자세히 알려줘"
}
```

## 주요 API (프로덕션)

| 엔드포인트 | 설명 |
|-----------|------|
| POST /chat/turn/start | 대화 시작 (운세 자동분석 또는 재사용) ⭐ |
| POST /chat/turn/continue | 대화 이어가기 ⭐ |
| POST /chat/greeting | 카테고리별 인사말 |
| POST /chat/session | 세션 생성 |
| GET /chat/session/{id} | 세션 조회 |
| DELETE /chat/session/{id} | 세션 삭제 |

## 레거시 API (Swagger 숨김)

- POST /chat - 턴 기반 (turn/start로 대체)
- POST /chat/stream - SSE 스트리밍
- POST /chat/complete - Non-Streaming
- POST /chat/turn - 통합 턴 (turn/start, turn/continue로 분리)

## 디버그 API (Swagger 숨김)

- GET /chat/debug/sessions, fortunes
- POST /chat/debug/seed, dynamic, clear
"""

import json
from datetime import datetime
from typing import Literal

import structlog
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator

from yeji_ai.clients.redis_client import (
    get_session_token_history,
    get_token_stats_by_category,
)
from yeji_ai.clients.vllm_client import GenerationConfig, get_vllm_client
from yeji_ai.models.fortune.chat import (
    CategoryGreetingRequest,
    CategoryGreetingResponse,
    Character,
    CharacterCode,
    ChatDebateStatus,
    ChatMessage,
    ChatRequest,
    ChatResponse,
    ChatUIHints,
    FortuneCategory,
    FortuneCategoryLiteral,
    FortuneReference,
    FortuneSummaryResponse,
    MessageType,
)
from yeji_ai.prompts.character_personas import (
    get_system_prompt,
)
from yeji_ai.services.tikitaka_service import (
    TikitakaService,
    clear_all_data,
    create_session,
    create_summarized_eastern_context,
    create_summarized_western_context,
    delete_session,
    get_fortune,
    get_or_create_session,
    get_or_create_session_async,
    get_session,
    get_session_async,
    list_fortunes,
    list_sessions,
    save_session,
)

logger = structlog.get_logger()

router = APIRouter()

# 서비스 인스턴스 (싱글톤)
_service = TikitakaService()


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="[레거시] 티키타카 대화",
    description="소이설(동양)과 스텔라(서양)가 대화하며 운세를 분석합니다.",
    tags=["fortune-chat-legacy"],
    include_in_schema=False,  # 레거시 - Swagger에서 숨김
    responses={
        200: {
            "description": "대화 성공",
            "content": {
                "application/json": {
                    "example": {
                        "session_id": "abc12345",
                        "turn": 2,
                        "messages": [
                            {
                                "character": "SOISEOL",
                                "type": "INTERPRETATION",
                                "content": "병화 일간이시네요~ 밝고 열정적이에요.",
                            }
                        ],
                        "debate_status": {"is_consensus": True},
                        "ui_hints": {"show_choice": False},
                    }
                }
            },
        },
        400: {"description": "잘못된 요청"},
        500: {"description": "서버 오류"},
    },
)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    티키타카 채팅 API

    소이설(동양 사주)과 스텔라(서양 점성술)가 대화하며 운세를 분석합니다.

    **요청 파라미터:**
    - **session_id**: 세션 ID (첫 요청 시 null)
    - **message**: 사용자 메시지
    - **birth_date**: 생년월일 (YYYY-MM-DD, 첫 요청 시 필수)
    - **birth_time**: 출생시간 (HH:MM, 선택)
    - **choice**: 사용자 선택 (1 또는 2, 선택형 질문 후)
    - **eastern_fortune_id**: 기존 동양 운세 ID (재사용 시)
    - **western_fortune_id**: 기존 서양 운세 ID (재사용 시)

    **응답 구조:**
    - **session_id**: 세션 ID (이후 요청에 사용)
    - **turn**: 대화 턴 번호
    - **messages**: 캐릭터 메시지 목록
    - **debate_status**: 토론 상태 (합의/불합의)
    - **ui_hints**: UI 힌트 (선택형 표시 여부)
    - **fortune_ref**: 사용된 운세 참조 정보 (운세 분석 완료 시 포함)
    """
    logger.info(
        "chat_request",
        session_id=request.session_id,
        message=request.message[:50] if request.message else None,
    )

    try:
        # 세션 조회/생성
        session = get_or_create_session(request.session_id)
        session.turn += 1

        # 카테고리 저장
        session.category = request.category

        # 사용자 정보 저장
        if request.birth_date:
            session.user_info["birth_date"] = request.birth_date
        if request.birth_time:
            session.user_info["birth_time"] = request.birth_time

        # ============================================================
        # 첫 턴: 인사 (카테고리별 그리팅 적용)
        # ============================================================
        if session.turn == 1:
            messages = _service.create_greeting_messages(category=request.category)
            debate_status = ChatDebateStatus()
            ui_hints = ChatUIHints()

        # ============================================================
        # 생년월일이 주어진 경우: 분석 실행
        # ============================================================
        elif (
            request.birth_date or session.user_info.get("birth_date")
        ) and not session.eastern_result:
            birth_date = request.birth_date or session.user_info["birth_date"]
            birth_time = request.birth_time or session.user_info.get("birth_time")

            # 동양/서양 분석 실행 (기존 Fortune ID 재사용 지원)
            (
                eastern_result,
                western_result,
                eastern_id,
                western_id,
                fortune_source,
            ) = await _service.get_or_create_fortunes(
                birth_date=birth_date,
                birth_time=birth_time,
                eastern_fortune_id=request.eastern_fortune_id,
                western_fortune_id=request.western_fortune_id,
            )

            # 세션에 결과 저장
            session.eastern_result = eastern_result
            session.western_result = western_result
            session.eastern_fortune_id = eastern_id
            session.western_fortune_id = western_id
            session.fortune_source = fortune_source

            # LLM 기반 해석 메시지 생성
            messages, debate_status = await _service.create_interpretation_messages(
                eastern_result, western_result
            )
            ui_hints = ChatUIHints()

        # ============================================================
        # 선택 응답 처리
        # ============================================================
        elif request.choice:
            topic = session.last_topic or "종합 운세"
            messages = await _service.handle_choice(
                choice=request.choice,
                topic=topic,
                session=session,
            )

            debate_status = ChatDebateStatus(
                is_consensus=True,
                question="다른 궁금한 점이 있으신가요?",
            )
            ui_hints = ChatUIHints()

        # ============================================================
        # 주제별 질문 처리
        # ============================================================
        elif session.eastern_result and session.western_result:
            # 메시지에서 주제 추출
            topic = _extract_topic(request.message)
            session.last_topic = topic

            messages, debate_status, ui_hints = await _service.create_topic_messages(
                topic=topic,
                eastern=session.eastern_result,
                western=session.western_result,
            )

        # ============================================================
        # 생년월일 미입력 상태
        # ============================================================
        else:
            now = datetime.now()
            messages = [
                ChatMessage(
                    character=CharacterCode.SOISEOL,
                    type=MessageType.INFO_REQUEST,
                    content="먼저 생년월일을 알려주세요~ 예: 1990-05-15",
                    timestamp=now,
                )
            ]
            debate_status = ChatDebateStatus()
            ui_hints = ChatUIHints()

        # 세션에 메시지 저장
        for msg in messages:
            session.add_message(msg)

        # Fortune 참조 정보 생성 (운세 분석 완료 시)
        fortune_ref = None
        if session.eastern_fortune_id and session.western_fortune_id:
            fortune_ref = FortuneReference(
                eastern_id=session.eastern_fortune_id,
                western_id=session.western_fortune_id,
                source=session.fortune_source or "created",
            )

        response = ChatResponse(
            session_id=session.session_id,
            turn=session.turn,
            messages=messages,
            debate_status=debate_status,
            ui_hints=ui_hints,
            fortune_ref=fortune_ref,
        )

        logger.info("chat_success", session_id=session.session_id, turn=session.turn)
        return response

    except ValueError as e:
        logger.warning("chat_validation_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"입력값 오류: {str(e)}",
        )
    except Exception as e:
        logger.error("chat_error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"대화 처리 중 오류가 발생했습니다: {str(e)}",
        )


@router.post(
    "/chat/stream",
    summary="[레거시] 티키타카 대화 (스트리밍)",
    description="SSE 스트리밍으로 실시간 응답을 받습니다.",
    tags=["fortune-chat-legacy"],
    include_in_schema=False,  # 레거시 - Swagger에서 숨김
    responses={
        200: {
            "description": "스트리밍 성공",
            "content": {"text/event-stream": {}},
        },
    },
)
async def chat_stream(request: ChatRequest):
    """
    티키타카 채팅 API (스트리밍)

    Server-Sent Events로 실시간 응답을 스트리밍합니다.

    **이벤트 타입:**
    - `message_start`: 메시지 시작 (character, type)
    - `message_chunk`: 메시지 청크 (character, content)
    - `message_end`: 메시지 완료 (character, content, timestamp)
    - `debate_status`: 토론 상태
    - `complete`: 스트리밍 완료
    - `error`: 오류 발생
    """
    logger.info("chat_stream_request", session_id=request.session_id)

    async def generate():
        try:
            # 세션 조회/생성
            session = get_or_create_session(request.session_id)
            session.turn += 1

            # 사용자 정보 저장
            if request.birth_date:
                session.user_info["birth_date"] = request.birth_date
            if request.birth_time:
                session.user_info["birth_time"] = request.birth_time

            # 세션 ID 전송
            yield f'data: {json.dumps({"event": "session", "session_id": session.session_id})}\n\n'

            # 생년월일 확인
            birth_date = request.birth_date or session.user_info.get("birth_date")
            if not birth_date:
                error_data = {"event": "error", "message": "생년월일을 입력해주세요."}
                yield f"data: {json.dumps(error_data)}\n\n"
                return

            # 분석 실행 (결과가 없는 경우)
            if not session.eastern_result:
                yield f'data: {json.dumps({"event": "status", "message": "분석 중..."})}\n\n'

                birth_time = request.birth_time or session.user_info.get("birth_time")
                eastern_result, western_result = await _service.analyze_both(
                    birth_date=birth_date,
                    birth_time=birth_time,
                )
                session.eastern_result = eastern_result
                session.western_result = western_result

            # 스트리밍 해석 생성
            async for event in _service.stream_interpretation(
                session.eastern_result,
                session.western_result,
            ):
                yield f'data: {json.dumps(event)}\n\n'

        except Exception as e:
            logger.error("chat_stream_error", error=str(e))
            yield f'data: {json.dumps({"event": "error", "message": str(e)})}\n\n'

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


async def _generate_turn_stream(
    session_id: str,
    turn: int,
    messages: list[ChatMessage],
    suggested_question: str,
    is_complete: bool,
):
    """
    턴 응답 SSE 스트리밍 생성기

    Args:
        session_id: 세션 ID
        turn: 턴 번호
        messages: 메시지 목록
        suggested_question: 다음 질문 제안
        is_complete: 완료 여부

    Yields:
        SSE 이벤트 문자열
    """
    # 세션 ID 전송
    yield f'data: {json.dumps({"event": "session", "session_id": session_id})}\n\n'

    # 메시지 스트리밍
    for msg in messages:
        # 메시지 시작
        start_data = {
            "event": "message_start",
            "character": msg.character.value,
            "type": msg.type.value,
        }
        yield f"data: {json.dumps(start_data)}\n\n"

        # 메시지 내용 (청크 단위로 분할)
        content_chunks = _split_into_chunks(msg.content, chunk_size=20)
        for chunk in content_chunks:
            chunk_data = {
                "event": "message_chunk",
                "character": msg.character.value,
                "content": chunk,
            }
            yield f"data: {json.dumps(chunk_data)}\n\n"

        # 메시지 종료
        end_data = {
            "event": "message_end",
            "character": msg.character.value,
            "content": msg.content,
            "timestamp": msg.timestamp.isoformat(),
        }
        yield f"data: {json.dumps(end_data)}\n\n"

    # 완료 이벤트
    complete_data = {
        "event": "complete",
        "turn": turn,
        "is_complete": is_complete,
        "suggested_question": suggested_question,
    }
    yield f"data: {json.dumps(complete_data)}\n\n"


def _split_into_chunks(text: str, chunk_size: int = 20) -> list[str]:
    """
    텍스트를 청크로 분할

    Args:
        text: 분할할 텍스트
        chunk_size: 청크 크기 (문자 수)

    Returns:
        분할된 청크 리스트
    """
    chunks = []
    for i in range(0, len(text), chunk_size):
        chunks.append(text[i:i + chunk_size])
    return chunks


def _extract_topic(message: str) -> str:
    """
    메시지에서 주제 추출

    Args:
        message: 사용자 메시지

    Returns:
        추출된 주제 (기본: "종합 운세")
    """
    message_lower = message.lower()

    # 키워드 매핑
    topic_keywords = {
        "연애": "연애운",
        "사랑": "연애운",
        "연인": "연애운",
        "결혼": "연애운",
        "직장": "직장운",
        "일": "직장운",
        "회사": "직장운",
        "커리어": "직장운",
        "취업": "직장운",
        "금전": "금전운",
        "돈": "금전운",
        "재물": "금전운",
        "투자": "금전운",
        "재정": "금전운",
        "건강": "건강운",
        "몸": "건강운",
        "학업": "학업운",
        "공부": "학업운",
        "시험": "학업운",
        "대인": "대인운",
        "인간관계": "대인운",
        "친구": "대인운",
    }

    for keyword, topic in topic_keywords.items():
        if keyword in message_lower:
            return topic

    return "종합 운세"


@router.get(
    "/chat/characters",
    summary="캐릭터 정보 조회",
    tags=["fortune-util"],
    description="소이설과 스텔라 캐릭터 정보를 반환합니다.",
    include_in_schema=False,  # 유틸리티 - Swagger에서 숨김
)
async def get_characters():
    """캐릭터 정보 조회"""
    return {
        "characters": [
            Character.soiseol().model_dump(),
            Character.stella().model_dump(),
        ]
    }


@router.get(
    "/chat/summary/{session_id}",
    response_model=FortuneSummaryResponse,
    summary="운세 요약 조회",
    description="채팅 세션의 운세 요약을 조회합니다. 동양/서양 분리 응답.",
    tags=["fortune-summary"],
    responses={
        200: {
            "description": "요약 조회 성공",
            "content": {
                "application/json": {
                    "example": {
                        "session_id": "abc12345",
                        "category": "wealth",
                        "fortune_type": "eastern",
                        "fortune": {
                            "character": "SOISEOL",
                            "score": 85,
                            "one_line": "목(木) 기운이 강해 재물 운이 상승하는 시기예요",
                            "keywords": ["재물운 상승", "투자 적기", "절약 필요"],
                            "detail": "일간(甲)을 중심으로...",
                        },
                    }
                }
            },
        },
        400: {"description": "잘못된 요청 (type 파라미터 오류)"},
        404: {"description": "세션을 찾을 수 없음"},
    },
)
async def get_fortune_summary(
    session_id: str,
    type: str,
    category: FortuneCategoryLiteral = "total",
) -> FortuneSummaryResponse:
    """
    운세 요약 조회 API (프로덕션)

    채팅 세션의 운세 분석 결과를 요약 형태로 반환합니다.
    동양(eastern)/서양(western)을 분리하여 조회합니다.

    ---

    ## 권장 플로우

    ### 1. 세션 시작 (Turn 0)
    ```
    POST /chat/turn/start
    {
      "birth_date": "1990-05-15",
      "category": "LOVE"
    }
    ```
    → session_id 반환

    ### 2. 대화 계속 (Turn 1+)
    ```
    POST /chat/turn/continue
    {
      "session_id": "abc123",
      "message": "연애운이 궁금해요"
    }
    ```

    ### 3. 요약 조회 (선택) ← **현재 API**
    ```
    GET /chat/summary/{session_id}?type=eastern
    GET /chat/summary/{session_id}?type=western&category=love
    ```

    ---

    **Query Parameters:**
    - **type** (필수): "eastern" 또는 "western"
    - **category** (선택): 운세 카테고리 (기본: "total")

    **응답:**
    - **session_id**: 세션 ID
    - **category**: 운세 카테고리
    - **fortune_type**: "eastern" 또는 "western"
    - **fortune**: 운세 요약 (character, score, one_line, keywords, detail)
    """
    logger.info(
        "fortune_summary_request",
        session_id=session_id,
        fortune_type=type,
        category=category,
    )

    # type 검증
    if type not in ("eastern", "western"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="type 파라미터는 'eastern' 또는 'western'이어야 합니다.",
        )

    # 세션 조회
    session = get_or_create_session(session_id)
    if session.session_id != session_id:
        # 새 세션이 생성된 경우 = 기존 세션 없음
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"세션을 찾을 수 없습니다: {session_id}",
        )

    # 분석 결과 확인
    if type == "eastern" and not session.eastern_result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="동양 운세 분석이 아직 완료되지 않았습니다. 먼저 채팅을 진행해주세요.",
        )
    if type == "western" and not session.western_result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="서양 운세 분석이 아직 완료되지 않았습니다. 먼저 채팅을 진행해주세요.",
        )

    try:
        # 요약 생성
        summary_data = _service.create_summary(
            session=session,
            fortune_type=type,
            category=category,
        )

        response = FortuneSummaryResponse(**summary_data)
        logger.info("fortune_summary_success", session_id=session_id, fortune_type=type)
        return response

    except ValueError as e:
        logger.warning("fortune_summary_validation_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error("fortune_summary_error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"요약 생성 중 오류가 발생했습니다: {str(e)}",
        )


# ============================================================
# 서브 캐릭터 페르소나 테스트 엔드포인트
# ============================================================

SubCharacterCode = Literal["CHEONGWOON", "HWARIN", "KYLE", "ELARIA"]


class CharacterTestRequest(BaseModel):
    """캐릭터 테스트 요청"""

    character: SubCharacterCode = Field(..., description="캐릭터 코드")
    message: str = Field(
        default="자기 소개를 해주세요.",
        description="테스트 메시지",
    )


class CharacterTestResponse(BaseModel):
    """캐릭터 테스트 응답"""

    character: str = Field(..., description="캐릭터 코드")
    character_name: str = Field(..., description="캐릭터 이름")
    expected_style: str = Field(..., description="기대 말투")
    response: str = Field(..., description="LLM 응답")
    pattern_analysis: dict = Field(..., description="말투 패턴 분석")


# 캐릭터별 메타 정보
CHARACTER_META = {
    "CHEONGWOON": {"name": "청운", "expected_style": "하오체 (시적)"},
    "HWARIN": {"name": "화린", "expected_style": "해요체 (나른)"},
    "KYLE": {"name": "카일", "expected_style": "반말+존댓말 혼용"},
    "ELARIA": {"name": "엘라리아", "expected_style": "하십시오체/해요체"},
}


def _analyze_speech_patterns(text: str) -> dict:
    """말투 패턴 분석"""
    import re

    haeyo_pattern = r"(해요|이에요|예요|네요|세요|어요|거든요|드릴게요|할게요)"
    patterns = {
        "하오체": len(re.findall(r"(하오|이오|있소|겠소|구려|로다|시오|마시오)", text)),
        "해요체": len(re.findall(haeyo_pattern, text)),
        "합니다체": len(re.findall(r"(합니다|입니다|습니다|겠습니다|됩니다)", text)),
        "반말": len(re.findall(r"(해\.|야\.|지\.|거든\.|잖아|이야|거야)", text)),
    }
    return patterns


@router.post(
    "/chat/test-character",
    response_model=CharacterTestResponse,
    summary="서브 캐릭터 페르소나 테스트",
    tags=["fortune-util"],
    description="청운/화린/카일/엘라리아 서브 캐릭터의 Few-shot 페르소나를 테스트합니다.",
    include_in_schema=False,  # 유틸리티 - Swagger에서 숨김
    responses={
        200: {
            "description": "테스트 성공",
            "content": {
                "application/json": {
                    "example": {
                        "character": "CHEONGWOON",
                        "character_name": "청운",
                        "expected_style": "하오체 (시적)",
                        "response": "허허, 이 늙은이는 청운이라 하오...",
                        "pattern_analysis": {
                            "하오체": 5,
                            "해요체": 0,
                            "합니다체": 0,
                            "반말": 0,
                        },
                    }
                }
            },
        },
        400: {"description": "잘못된 캐릭터 코드"},
        500: {"description": "LLM 호출 오류"},
    },
)
async def test_character_persona(request: CharacterTestRequest) -> CharacterTestResponse:
    """
    서브 캐릭터 페르소나 테스트 API

    Few-shot 프롬프트가 적용된 서브 캐릭터들의 말투를 테스트합니다.
    vLLM을 통해 캐릭터 응답을 생성하고 말투 패턴을 분석합니다.

    **지원 캐릭터:**
    - **CHEONGWOON** (청운): 소이설 스승, 하오체 (시적)
    - **HWARIN** (화린): 청룡상단 지부장, 해요체 (나른)
    - **KYLE** (카일): 도박사/정보상, 반말+존댓말 혼용
    - **ELARIA** (엘라리아): 사파이어 왕국 공주, 하십시오체/해요체
    """
    logger.info(
        "character_test_request",
        character=request.character,
        message=request.message[:50],
    )

    # 캐릭터 메타 정보
    meta = CHARACTER_META.get(request.character)
    if not meta:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"지원하지 않는 캐릭터입니다: {request.character}",
        )

    try:
        # 시스템 프롬프트 가져오기
        system_prompt = get_system_prompt(request.character)

        # vLLM 호출
        vllm_client = get_vllm_client()
        config = GenerationConfig(
            max_tokens=300,
            temperature=0.7,
            top_p=0.8,
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": request.message},
        ]

        result = await vllm_client.chat(messages, config)
        response_text = result.text.strip()

        # 말투 패턴 분석
        pattern_analysis = _analyze_speech_patterns(response_text)

        logger.info(
            "character_test_success",
            character=request.character,
            patterns=pattern_analysis,
        )

        return CharacterTestResponse(
            character=request.character,
            character_name=meta["name"],
            expected_style=meta["expected_style"],
            response=response_text,
            pattern_analysis=pattern_analysis,
        )

    except Exception as e:
        logger.error(
            "character_test_error",
            character=request.character,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"캐릭터 테스트 중 오류가 발생했습니다: {str(e)}",
        )


@router.get(
    "/chat/sub-characters",
    summary="서브 캐릭터 목록 조회",
    tags=["fortune-util"],
    description="테스트 가능한 서브 캐릭터 목록을 반환합니다.",
    include_in_schema=False,  # 유틸리티 - Swagger에서 숨김
)
async def get_sub_characters():
    """서브 캐릭터 목록 조회"""
    return {
        "sub_characters": [
            {
                "code": code,
                "name": meta["name"],
                "expected_style": meta["expected_style"],
            }
            for code, meta in CHARACTER_META.items()
        ]
    }


# ============================================================
# 카테고리별 그리팅 API
# ============================================================


@router.post(
    "/chat/greeting",
    response_model=CategoryGreetingResponse,
    summary="[레거시] 카테고리별 그리팅",
    tags=["fortune-chat-legacy"],
    include_in_schema=False,  # 레거시 - Swagger에서 숨김
    deprecated=True,
    description="[DEPRECATED] 이 엔드포인트는 레거시입니다. /chat/turn/start를 사용하세요.",
    responses={
        200: {
            "description": "그리팅 생성 성공",
            "content": {
                "application/json": {
                    "example": {
                        "session_id": "abc123",
                        "category": "LOVE",
                        "messages": [
                            {
                                "character": "SOISEOL",
                                "type": "GREETING",
                                "content": "병화 일간이시오. 독립적인 연애를 선호하시겠소.",
                                "timestamp": "2024-01-27T15:30:00",
                            }
                        ],
                        "eastern_fortune_id": "e12345",
                        "western_fortune_id": "w67890",
                        "eastern_summary": "병화 일간 (화)",
                        "western_summary": "황소자리 태양",
                    }
                }
            },
        },
        400: {"description": "잘못된 요청"},
        500: {"description": "서버 오류"},
    },
)
async def category_greeting(request: CategoryGreetingRequest) -> CategoryGreetingResponse:
    """
    [DEPRECATED] 카테고리별 그리팅 API

    **권장 대체 API: POST /chat/turn/start**

    이 엔드포인트는 레거시입니다. 대신 다음 플로우를 사용하세요:

    ## 권장 플로우

    ### 1. 세션 시작 (Turn 0)
    ```
    POST /chat/turn/start
    {
      "birth_date": "1990-05-15",
      "category": "LOVE"
    }
    ```
    → session_id + 그리팅 메시지 반환

    ### 2. 대화 계속 (Turn 1+)
    ```
    POST /chat/turn/continue
    {
      "session_id": "abc123",
      "message": "연애운이 궁금해요"
    }
    ```

    ### 3. 요약 조회 (선택)
    ```
    GET /chat/summary/{session_id}?type=eastern
    ```
    """
    logger.info(
        "category_greeting_request",
        birth_date=request.birth_date,
        category=request.category.value,
    )

    try:
        # 세션 생성
        session = create_session(
            birth_date=request.birth_date,
            birth_time=request.birth_time,
        )
        session.category = request.category

        # 카테고리별 그리팅 생성 (실제 분석 결과 기반)
        # 동적 버블 시스템은 모델 안정화 후 적용 예정
        messages, eastern_id, western_id, fortune_source = await _service.create_category_greeting(
            birth_date=request.birth_date,
            category=request.category,
            char1_code=request.char1_code,
            char2_code=request.char2_code,
            birth_time=request.birth_time,
            birth_place=request.birth_place,
            latitude=request.latitude,
            longitude=request.longitude,
            eastern_fortune_id=request.eastern_fortune_id,
            western_fortune_id=request.western_fortune_id,
            eastern_fortune_data=request.eastern_fortune_data,
            western_fortune_data=request.western_fortune_data,
        )

        # 세션에 Fortune ID 저장
        session.eastern_fortune_id = eastern_id
        session.western_fortune_id = western_id

        # Fortune 데이터 조회
        eastern_result = get_fortune(eastern_id)
        western_result = get_fortune(western_id)

        # 🔧 버그 수정: 세션에 분석 결과 저장 (폴백 방지)
        # /chat/turn에서 session.turn과 session.eastern_result 체크하므로 여기서 저장 필요
        session.eastern_result = eastern_result
        session.western_result = western_result
        session.turn = 1  # 그리팅 완료 = Turn 1

        # 요약은 별도 API (/chat/summary/{session_id})에서 조회
        # greeting 단계에서는 빈 문자열로 반환
        eastern_summary = ""
        western_summary = ""

        logger.info(
            "category_greeting_success",
            session_id=session.session_id,
            category=request.category.value,
            message_count=len(messages),
        )

        return CategoryGreetingResponse(
            session_id=session.session_id,
            category=request.category,
            messages=messages,
            eastern_fortune_id=eastern_id,
            western_fortune_id=western_id,
            eastern_summary=eastern_summary,
            western_summary=western_summary,
            fortune_source=fortune_source,
        )

    except ValueError as e:
        logger.warning("category_greeting_validation_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"입력값 오류: {str(e)}",
        )
    except Exception as e:
        logger.error("category_greeting_error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"그리팅 생성 중 오류가 발생했습니다: {str(e)}",
        )


# ============================================================
# 세션 관리 API
# ============================================================


class SessionCreateRequest(BaseModel):
    """세션 생성 요청"""

    birth_date: str | None = Field(
        None, description="생년월일 (YYYY-MM-DD)", pattern=r"^\d{4}-\d{2}-\d{2}$"
    )
    birth_time: str | None = Field(
        None, description="출생시간 (HH:MM)", pattern=r"^\d{2}:\d{2}$"
    )


class SessionInfo(BaseModel):
    """세션 정보"""

    session_id: str = Field(..., description="세션 ID")
    turn: int = Field(..., description="현재 턴")
    has_eastern: bool = Field(..., description="동양 운세 분석 완료 여부")
    has_western: bool = Field(..., description="서양 운세 분석 완료 여부")
    eastern_fortune_id: str | None = Field(None, description="동양 운세 ID")
    western_fortune_id: str | None = Field(None, description="서양 운세 ID")
    birth_date: str | None = Field(None, description="생년월일")
    birth_time: str | None = Field(None, description="출생시간")
    created_at: str = Field(..., description="생성 시간")


@router.post(
    "/chat/session",
    response_model=SessionInfo,
    summary="채팅 세션 생성",
    description="새로운 티키타카 채팅 세션을 생성합니다.",
    responses={
        201: {
            "description": "세션 생성 성공",
            "content": {
                "application/json": {
                    "example": {
                        "session_id": "abc12345",
                        "turn": 0,
                        "has_eastern": False,
                        "has_western": False,
                        "eastern_fortune_id": None,
                        "western_fortune_id": None,
                        "birth_date": "1990-05-15",
                        "birth_time": "14:30",
                        "created_at": "2026-01-31T10:00:00",
                    }
                }
            },
        },
    },
    status_code=status.HTTP_201_CREATED,
    tags=["fortune-session"],
    include_in_schema=False,  # 세션 관리 - Swagger에서 숨김
)
async def create_chat_session(request: SessionCreateRequest) -> SessionInfo:
    """
    채팅 세션 생성 API

    티키타카 대화를 시작하기 전에 세션을 명시적으로 생성합니다.
    Swagger 테스트 시 세션 ID를 먼저 확보할 수 있습니다.

    **요청 파라미터:**
    - **birth_date**: 생년월일 (선택, YYYY-MM-DD)
    - **birth_time**: 출생시간 (선택, HH:MM)

    **응답:**
    - **session_id**: 생성된 세션 ID (이후 채팅에 사용)
    """
    logger.info(
        "session_create_request",
        birth_date=request.birth_date,
        birth_time=request.birth_time,
    )

    session = create_session(
        birth_date=request.birth_date,
        birth_time=request.birth_time,
    )

    return SessionInfo(
        session_id=session.session_id,
        turn=session.turn,
        has_eastern=session.eastern_result is not None,
        has_western=session.western_result is not None,
        eastern_fortune_id=session.eastern_fortune_id,
        western_fortune_id=session.western_fortune_id,
        birth_date=session.user_info.get("birth_date"),
        birth_time=session.user_info.get("birth_time"),
        created_at=session.created_at.isoformat(),
    )


@router.get(
    "/chat/session/{session_id}",
    response_model=SessionInfo,
    summary="세션 정보 조회",
    description="기존 채팅 세션의 상태를 조회합니다.",
    responses={
        200: {"description": "세션 조회 성공"},
        404: {"description": "세션을 찾을 수 없음"},
    },
    tags=["fortune-session"],
    include_in_schema=False,  # 세션 관리 - Swagger에서 숨김
)
async def get_chat_session(session_id: str) -> SessionInfo:
    """
    세션 정보 조회 API

    세션 ID로 현재 세션 상태를 조회합니다.
    운세 분석 완료 여부, Fortune ID 등을 확인할 수 있습니다.
    """
    logger.info("session_get_request", session_id=session_id)

    session = get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"세션을 찾을 수 없습니다: {session_id}",
        )

    return SessionInfo(
        session_id=session.session_id,
        turn=session.turn,
        has_eastern=session.eastern_result is not None,
        has_western=session.western_result is not None,
        eastern_fortune_id=session.eastern_fortune_id,
        western_fortune_id=session.western_fortune_id,
        birth_date=session.user_info.get("birth_date"),
        birth_time=session.user_info.get("birth_time"),
        created_at=session.created_at.isoformat(),
    )


@router.delete(
    "/chat/session/{session_id}",
    summary="세션 삭제",
    description="채팅 세션을 삭제합니다.",
    responses={
        200: {"description": "세션 삭제 성공"},
        404: {"description": "세션을 찾을 수 없음"},
    },
    tags=["fortune-session"],
    include_in_schema=False,  # 세션 관리 - Swagger에서 숨김
)
async def delete_chat_session(session_id: str):
    """
    세션 삭제 API

    지정된 세션을 삭제합니다.
    테스트 후 정리 또는 세션 초기화에 사용합니다.
    """
    logger.info("session_delete_request", session_id=session_id)

    if not delete_session(session_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"세션을 찾을 수 없습니다: {session_id}",
        )

    return {"message": f"세션이 삭제되었습니다: {session_id}"}


# ============================================================
# 디버그 엔드포인트 (개발/테스트 전용)
# ============================================================


@router.get(
    "/chat/debug/sessions",
    summary="모든 세션 목록",
    description="현재 메모리에 저장된 모든 세션 목록을 조회합니다. 개발/테스트 전용.",
    tags=["fortune-debug"],
    include_in_schema=False,  # 디버그 엔드포인트 - Swagger에서 숨김
)
async def debug_list_sessions():
    """
    [DEBUG] 세션 목록 조회

    현재 활성화된 모든 세션을 조회합니다.
    Swagger에서 테스트할 세션 ID를 확인할 때 유용합니다.
    """
    sessions = list_sessions()
    return {
        "count": len(sessions),
        "sessions": sessions,
    }


@router.get(
    "/chat/debug/fortunes",
    summary="모든 Fortune 목록",
    description="현재 메모리에 저장된 모든 Fortune 목록을 조회합니다. 개발/테스트 전용.",
    tags=["fortune-debug"],
    include_in_schema=False,  # 디버그 엔드포인트 - Swagger에서 숨김
)
async def debug_list_fortunes():
    """
    [DEBUG] Fortune 목록 조회

    저장된 모든 운세 결과(동양/서양)를 조회합니다.
    Fortune ID 재사용 테스트 시 ID를 확인할 때 유용합니다.
    """
    fortunes = list_fortunes()
    return {
        "count": len(fortunes),
        "fortunes": fortunes,
    }


class SeedRequest(BaseModel):
    """테스트 시드 요청"""

    birth_date: str = Field(
        default="1990-05-15",
        description="생년월일 (YYYY-MM-DD)",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
    )
    birth_time: str | None = Field(
        default="14:30",
        description="출생시간 (HH:MM)",
        pattern=r"^\d{2}:\d{2}$",
    )


@router.post(
    "/chat/debug/seed",
    summary="테스트 시드 생성",
    description="테스트용 세션과 운세 데이터를 한 번에 생성합니다. 개발/테스트 전용.",
    tags=["fortune-debug"],
    include_in_schema=False,  # 디버그 엔드포인트 - Swagger에서 숨김
)
async def debug_create_seed(request: SeedRequest):
    """
    [DEBUG] 테스트 시드 생성

    세션 생성 + 운세 분석을 한 번에 수행합니다.
    Swagger에서 바로 채팅 테스트를 시작할 수 있습니다.

    **응답:**
    - session_id: 생성된 세션 ID
    - eastern_fortune_id: 동양 운세 ID
    - western_fortune_id: 서양 운세 ID

    **사용 예:**
    1. 이 엔드포인트로 시드 생성
    2. 응답의 session_id로 /chat 호출
    3. 또는 fortune_id로 다른 세션에서 재사용
    """
    logger.info(
        "debug_seed_request",
        birth_date=request.birth_date,
        birth_time=request.birth_time,
    )

    try:
        # 세션 생성
        session = create_session(
            birth_date=request.birth_date,
            birth_time=request.birth_time,
        )

        # 운세 분석 실행
        (
            eastern_result,
            western_result,
            eastern_id,
            western_id,
            source,
        ) = await _service.get_or_create_fortunes(
            birth_date=request.birth_date,
            birth_time=request.birth_time,
        )

        # 세션에 결과 저장
        session.eastern_result = eastern_result
        session.western_result = western_result
        session.eastern_fortune_id = eastern_id
        session.western_fortune_id = western_id
        session.fortune_source = source

        logger.info(
            "debug_seed_success",
            session_id=session.session_id,
            eastern_id=eastern_id,
            western_id=western_id,
        )

        return {
            "message": "테스트 시드가 생성되었습니다",
            "session_id": session.session_id,
            "eastern_fortune_id": eastern_id,
            "western_fortune_id": western_id,
            "birth_date": request.birth_date,
            "birth_time": request.birth_time,
        }

    except Exception as e:
        logger.error("debug_seed_error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"시드 생성 중 오류가 발생했습니다: {str(e)}",
        )


@router.delete(
    "/chat/debug/clear",
    summary="모든 데이터 초기화",
    description="모든 세션과 Fortune 데이터를 삭제합니다. 개발/테스트 전용.",
    tags=["fortune-debug"],
    include_in_schema=False,  # 디버그 엔드포인트 - Swagger에서 숨김
)
async def debug_clear_all():
    """
    [DEBUG] 데이터 초기화

    모든 세션과 Fortune 데이터를 삭제합니다.
    테스트 환경 초기화 시 사용합니다.

    **주의:** 이 작업은 되돌릴 수 없습니다.
    """
    logger.warning("debug_clear_request")
    result = clear_all_data()
    return {
        "message": "모든 데이터가 초기화되었습니다",
        **result,
    }


class DynamicBubbleRequest(BaseModel):
    """동적 버블 테스트 요청"""

    birth_date: str = Field(
        ...,
        description="생년월일 (YYYY-MM-DD)",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
    )
    birth_time: str | None = Field(
        None,
        description="출생 시간 (HH:MM)",
        pattern=r"^\d{2}:\d{2}$",
    )
    category: FortuneCategory = Field(
        FortuneCategory.GENERAL,
        description="운세 카테고리",
    )
    char1_code: str = Field("SOISEOL", description="캐릭터1 코드")
    char2_code: str = Field("STELLA", description="캐릭터2 코드")
    mode: str | None = Field(
        None,
        description="대화 모드 (battle/consensus, null이면 랜덤)",
    )
    min_bubbles: int = Field(3, description="최소 버블 수", ge=2, le=10)
    max_bubbles: int = Field(6, description="최대 버블 수", ge=2, le=10)


@router.post(
    "/chat/debug/dynamic",
    summary="동적 버블 시스템 테스트",
    description="멀티-콜 동적 버블 생성 시스템을 테스트합니다. 개발/테스트 전용.",
    tags=["fortune-debug"],
    include_in_schema=False,
)
async def debug_dynamic_bubbles(request: DynamicBubbleRequest):
    """
    [DEBUG] 동적 버블 시스템 테스트

    JSON 출력 없이 LLM을 여러 번 호출하여 동적 버블을 생성합니다.
    각 호출당 1개의 버블만 생성하므로 JSON 파싱 문제가 없습니다.

    **특징:**
    - 버블 수: min_bubbles ~ max_bubbles 랜덤
    - 발화 패턴: 70% 교차, 30% 연속 (동적)
    - 모드: battle(80%) / consensus(20%) 랜덤 또는 지정

    **사용 예시:**
    ```json
    {
        "birth_date": "1990-05-15",
        "birth_time": "14:30",
        "category": "love",
        "mode": "battle",
        "min_bubbles": 4,
        "max_bubbles": 6
    }
    ```
    """
    import time

    start_time = time.time()

    logger.info(
        "debug_dynamic_bubbles_request",
        birth_date=request.birth_date,
        category=request.category.value,
        mode=request.mode,
        bubbles=f"{request.min_bubbles}-{request.max_bubbles}",
    )

    try:
        # Fortune 데이터 생성/조회
        eastern_result, western_result, eastern_id, western_id, source = (
            await _service.get_or_create_fortunes(
                birth_date=request.birth_date,
                birth_time=request.birth_time,
            )
        )

        # 동적 버블 생성
        messages = await _service.create_dynamic_bubbles(
            category=request.category,
            eastern_result=eastern_result,
            western_result=western_result,
            char1_code=request.char1_code,
            char2_code=request.char2_code,
            mode=request.mode,
            min_bubbles=request.min_bubbles,
            max_bubbles=request.max_bubbles,
        )

        elapsed_time = time.time() - start_time

        # 응답 생성
        return {
            "success": True,
            "elapsed_seconds": round(elapsed_time, 2),
            "fortune_source": source,
            "eastern_id": eastern_id,
            "western_id": western_id,
            "bubble_count": len(messages),
            "messages": [
                {
                    "id": msg.id,
                    "character": msg.character.value,
                    "content": msg.content,
                    "emotion_code": msg.emotion_code,
                }
                for msg in messages
            ],
            "pattern": [msg.character.value for msg in messages],
        }

    except Exception as e:
        logger.error("debug_dynamic_bubbles_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"동적 버블 생성 실패: {str(e)}",
        )


# ============================================================
# 턴 단위 티키타카 (프로덕션)
# ============================================================


class TurnRequest(BaseModel):
    """[DEPRECATED] 턴 단위 채팅 요청

    Turn 0 (첫 요청): birth_date, category 필수
    Turn 1+ (이후): session_id만 필수, 나머지는 세션에서 조회

    **권장: /chat/turn/start, /chat/turn/continue 사용**
    """

    session_id: str | None = Field(
        None,
        description="세션 ID. Turn 0에서는 null, Turn 1+에서는 필수",
    )
    birth_date: str | None = Field(
        None,
        description="생년월일 (YYYY-MM-DD). Turn 0에서 필수, Turn 1+에서는 세션에서 조회",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
    )
    birth_time: str | None = Field(
        None,
        description="출생 시간 (HH:MM)",
        pattern=r"^\d{2}:\d{2}$",
    )
    category: FortuneCategory | None = Field(
        None,
        description="운세 카테고리. Turn 0에서 필수, Turn 1+에서는 세션에서 조회",
    )
    message: str | None = Field(None, description="사용자 메시지 (Turn 1+)")
    char1_code: str = Field("SOISEOL", description="캐릭터1 코드")
    char2_code: str = Field("STELLA", description="캐릭터2 코드")
    extend_turn: bool = Field(
        False,
        description="추가 턴 요청. True면 3턴 이후에도 대화 계속 (최대 5턴)",
    )


class TurnStartRequest(BaseModel):
    """Turn 0 전용 요청 - 세션 생성 및 그리팅"""

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "birth_date": "1995-03-15",
                    "birth_time": "09:30",
                    "category": "LOVE",
                    "char1_code": "SOISEOL",
                    "char2_code": "STELLA",
                }
            ]
        }
    }

    birth_date: str = Field(
        ...,
        description="생년월일 (YYYY-MM-DD)",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        examples=["1995-03-15"],
    )
    birth_time: str | None = Field(
        None,
        description="출생 시간 (HH:MM)",
        pattern=r"^\d{2}:\d{2}$",
        examples=["09:30"],
    )
    category: FortuneCategory = Field(
        ...,
        description="운세 카테고리 (대소문자 무관: LOVE, love 모두 가능)",
        examples=["LOVE"],
    )
    char1_code: str = Field("SOISEOL", description="캐릭터1 코드")
    char2_code: str = Field("STELLA", description="캐릭터2 코드")

    @field_validator("category", mode="before")
    @classmethod
    def normalize_category(cls, v: str | FortuneCategory) -> str:
        """카테고리 대소문자 정규화 (소문자 → 대문자)"""
        if isinstance(v, str):
            return v.upper()
        return v


class TurnContinueRequest(BaseModel):
    """Turn 1+ 전용 요청 - 세션 기반 대화"""

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "session_id": "abc12345",
                    "message": "연애운이 궁금해요",
                    "char1_code": "SOISEOL",
                    "char2_code": "STELLA",
                    "extend_turn": False,
                }
            ]
        }
    }

    session_id: str = Field(
        ..., description="세션 ID (필수)", examples=["abc12345"]
    )
    message: str = Field(
        ..., description="사용자 메시지", examples=["연애운이 궁금해요"]
    )
    char1_code: str = Field("SOISEOL", description="캐릭터1 코드")
    char2_code: str = Field("STELLA", description="캐릭터2 코드")
    extend_turn: bool = Field(
        False,
        description="추가 턴 요청. True면 3턴 이후에도 대화 계속 (최대 5턴)",
    )


class TurnResponse(BaseModel):
    """턴 단위 채팅 응답"""

    model_config = {
        "json_schema_extra": {
            "example": {
                "session_id": "abc12345",
                "turn": 1,
                "messages": [
                    {
                        "character": "SOISEOL",
                        "type": "GREETING",
                        "content": "연애운을 보러 온 귀하를 환영하오. 병화 일간이시니...",
                        "timestamp": "2024-01-27T15:30:00",
                    },
                    {
                        "character": "STELLA",
                        "type": "GREETING",
                        "content": "황소자리 태양이시군요! 안정적인 사랑을 추구하는 타입이에요.",
                        "timestamp": "2024-01-27T15:30:05",
                    },
                ],
                "suggested_question": "혹시 현재 마음에 두고 계신 분이 있으신지요?",
                "is_complete": False,
            }
        }
    }

    session_id: str = Field(..., description="세션 ID", examples=["abc12345"])
    turn: int = Field(..., description="현재 턴 번호 (0: 그리팅, 1+: 대화)", examples=[1])
    messages: list[ChatMessage] = Field(..., description="캐릭터 메시지 목록")
    suggested_question: str = Field(
        ...,
        description="다음 질문 제안 (카테고리에 맞는 후속 질문)",
        examples=["혹시 현재 마음에 두고 계신 분이 있으신지요?"],
    )
    is_complete: bool = Field(
        False,
        description="대화 완료 여부 (기본 3턴, extend_turn=True 시 최대 10턴)",
    )


@router.post(
    "/chat/turn",
    response_model=None,
    summary="[DEPRECATED] 턴 단위 티키타카",
    tags=["fortune-turn"],
    include_in_schema=False,  # Swagger에서 숨김
    description="""
## [DEPRECATED] 턴 단위 티키타카 API

**권장: /chat/turn/start, /chat/turn/continue 사용**

### Turn 0 (그리팅)
- session_id: null 또는 생략
- message: "" (빈 문자열)
- 결과: 세션 생성 + 그리팅 메시지

### Turn 1+ (질의응답)
- session_id: Turn 0에서 받은 ID
- message: 사용자 질문
- 결과: 티키타카 응답 + 다음 질문 제안
""",
    responses={
        200: {"description": "턴 응답 성공"},
        400: {"description": "잘못된 입력 (생년월일 형식, 카테고리)"},
        500: {"description": "서버 오류"},
    },
)
async def chat_turn(
    request: TurnRequest,
    stream: bool = Query(default=False, description="SSE 스트리밍 여부 (기본: false)"),
):
    """
    턴 단위 티키타카 API (프로덕션)

    카테고리별 운세를 턴 단위로 진행합니다.

    **요청 파라미터:**
    - **session_id**: 세션 ID (첫 요청 시 null)
    - **birth_date**: 생년월일 (YYYY-MM-DD)
    - **birth_time**: 출생 시간 (HH:MM, 선택)
    - **category**: 운세 카테고리
    - **message**: 사용자 메시지 (Turn 1+)
    - **char1_code**: 캐릭터1 코드 (기본값: SOISEOL)
    - **char2_code**: 캐릭터2 코드 (기본값: STELLA)

    **응답:**
    - **session_id**: 세션 ID
    - **turn**: 현재 턴 번호
    - **messages**: 캐릭터 메시지 목록
    - **suggested_question**: 다음 질문 제안
    - **is_complete**: 3턴 완료 여부
    """
    logger.info(
        "chat_turn_request",
        session_id=request.session_id,
        category=request.category.value if request.category else None,
        turn_message=request.message[:50] if request.message else None,
    )

    try:
        # 세션 조회/생성 (Redis + 메모리)
        session = await get_or_create_session_async(request.session_id)

        # Turn 0 (새 세션) vs Turn 1+ (기존 세션) 분기
        is_new_session = session.turn == 0 or not session.eastern_result

        if is_new_session:
            # Turn 0: birth_date, category 필수
            if not request.birth_date:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Turn 0에서는 birth_date가 필수입니다.",
                )
            if not request.category:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Turn 0에서는 category가 필수입니다.",
                )

            # 생년월일 형식 검증
            try:
                datetime.strptime(request.birth_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="생년월일 형식이 잘못되었습니다. YYYY-MM-DD 형식으로 입력해주세요.",
                )

            # 사용자 정보 저장
            birth_date = request.birth_date
            birth_time = request.birth_time
            category = request.category
            session.user_info["birth_date"] = birth_date
            if birth_time:
                session.user_info["birth_time"] = birth_time
            session.category = category
        else:
            # Turn 1+: 세션에서 조회 (요청값으로 오버라이드 가능)
            birth_date = request.birth_date or session.user_info.get("birth_date")
            birth_time = request.birth_time or session.user_info.get("birth_time")
            category = request.category or session.category

            if not birth_date:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="세션에 birth_date 정보가 없습니다. birth_date를 전달해주세요.",
                )

        # Turn 0: 그리팅 생성 (GPT-5-mini 사용)
        if is_new_session:
            session.turn += 1

            # 운세 분석 실행 먼저
            eastern, western = await _service.analyze_both(
                birth_date=request.birth_date,
                birth_time=request.birth_time,
                birth_place=None,
            )

            # 세션에 분석 결과 저장
            session.eastern_result = eastern
            session.western_result = western

            # 운세 컨텍스트 요약 (토큰 80% 절감)
            eastern_context = create_summarized_eastern_context(eastern)
            western_context = create_summarized_western_context(western)

            # GPT-5-mini로 그리팅 메시지 생성
            # Turn 0에서는 user_question 없음 (빈 문자열)
            greeting_messages, _ = await _service.create_tikitaka_messages_gpt5mini(
                topic=request.category.value,
                eastern_context=eastern_context,
                western_context=western_context,
                mode="greeting",
                char1_code=request.char1_code,
                char2_code=request.char2_code,
                is_first_turn=True,
                is_last_turn=False,
                user_question="",
                session_id=session.session_id,
                category=request.category.value,
                turn=session.turn,
            )

            # 메시지 저장
            for msg in greeting_messages:
                session.add_message(msg)

            # 다음 질문 제안
            suggested_question = f"{request.category.label_ko}에 대해 더 자세히 알고 싶어요"

            logger.info(
                "chat_turn_greeting_success",
                session_id=session.session_id,
                turn=session.turn,
            )

            # 세션 Redis 저장
            await save_session(session)

            # SSE 스트리밍 응답
            if stream:
                return StreamingResponse(
                    _generate_turn_stream(
                        session_id=session.session_id,
                        turn=session.turn,
                        messages=greeting_messages,
                        suggested_question=suggested_question,
                        is_complete=False,
                    ),
                    media_type="text/event-stream",
                    headers={
                        "Cache-Control": "no-cache",
                        "Connection": "keep-alive",
                        "X-Accel-Buffering": "no",
                    },
                )

            # JSON 응답
            return TurnResponse(
                session_id=session.session_id,
                turn=session.turn,
                messages=greeting_messages,
                suggested_question=suggested_question,
                is_complete=False,
            )

        # Turn 1+: 주제별 대화
        else:
            session.turn += 1

            # 메시지에서 주제 추출 (간단한 로직)
            # category는 1615줄에서 request.category or session.category로 설정됨
            category_label = category.label_ko if category else "운세"
            topic = request.message or category_label

            # 운세 컨텍스트 요약 (토큰 80% 절감)
            eastern_context = create_summarized_eastern_context(session.eastern_result)
            western_context = create_summarized_western_context(session.western_result)

            # 사용자 질문 저장 (로컬 폴백용)
            if request.message:
                session.user_questions.append(request.message)

            # 대화 히스토리 생성 (최근 6개 메시지 + 사용자 질문)
            conversation_history = ""
            history_lines = []

            # 이전 메시지들
            if session.messages:
                recent_messages = session.messages[-6:]  # 최근 6개만
                for msg in recent_messages:
                    char_name = (
                        msg.character.value
                        if hasattr(msg.character, "value")
                        else str(msg.character)
                    )
                    history_lines.append(f"{char_name}: {msg.content}")

            # 사용자 질문 히스토리 추가 (메시지 없을 때 폴백)
            if not history_lines and session.user_questions:
                for q in session.user_questions[-3:]:
                    history_lines.append(f"USER: {q}")

            conversation_history = "\n".join(history_lines)

            # GPT-5-mini 티키타카 메시지 생성
            # user_question: 사용자 질문을 프롬프트에 전달 (Layer 5)
            # category는 1615줄에서 request.category or session.category로 설정됨
            category_value = category.value if category else "LOVE"
            messages, debate_status = await _service.create_tikitaka_messages_gpt5mini(
                topic=topic,
                eastern_context=eastern_context,
                western_context=western_context,
                mode="battle",
                char1_code=request.char1_code,
                char2_code=request.char2_code,
                is_first_turn=(session.turn == 1),
                is_last_turn=(session.turn >= (5 if request.extend_turn else 3)),
                user_question=request.message or "",
                session_id=session.session_id,
                category=category_value,
                turn=session.turn,
                conversation_history=conversation_history,
            )

            # 메시지 저장
            for msg in messages:
                session.add_message(msg)

            # 다음 질문 제안 (debate_status.question 사용)
            suggested_question = debate_status.question or "다른 주제가 궁금하신가요?"

            # 종료 체크 (5턴 또는 force_end)
            is_complete = session.turn >= (5 if request.extend_turn else 3)

            logger.info(
                "chat_turn_topic_success",
                session_id=session.session_id,
                turn=session.turn,
                topic=topic,
            )

            # 세션 Redis 저장
            await save_session(session)

            # SSE 스트리밍 응답
            if stream:
                return StreamingResponse(
                    _generate_turn_stream(
                        session_id=session.session_id,
                        turn=session.turn,
                        messages=messages,
                        suggested_question=suggested_question,
                        is_complete=is_complete,
                    ),
                    media_type="text/event-stream",
                    headers={
                        "Cache-Control": "no-cache",
                        "Connection": "keep-alive",
                        "X-Accel-Buffering": "no",
                    },
                )

            # JSON 응답
            return TurnResponse(
                session_id=session.session_id,
                turn=session.turn,
                messages=messages,
                suggested_question=suggested_question,
                is_complete=is_complete,
            )

    except ValueError as e:
        logger.warning("chat_turn_validation_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"입력값 오류: {str(e)}",
        )
    except Exception as e:
        logger.error("chat_turn_error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"턴 처리 중 오류가 발생했습니다: {str(e)}",
        )


# ============================================================
# Non-Streaming 채팅 (전체 응답)
# ============================================================


class CompleteRequest(BaseModel):
    """Non-Streaming 채팅 요청"""

    birth_date: str = Field(
        ..., description="생년월일 (YYYY-MM-DD)", pattern=r"^\d{4}-\d{2}-\d{2}$"
    )
    birth_time: str | None = Field(
        None, description="출생시간 (HH:MM)", pattern=r"^\d{2}:\d{2}$"
    )
    topic: str | None = Field(
        None,
        description="운세 주제 (연애운, 직장운, 금전운 등). 미입력 시 종합 운세",
    )
    eastern_fortune_id: str | None = Field(
        None, description="기존 동양 운세 ID (재사용 시)"
    )
    western_fortune_id: str | None = Field(
        None, description="기존 서양 운세 ID (재사용 시)"
    )


class CompleteResponse(BaseModel):
    """Non-Streaming 채팅 응답"""

    session_id: str = Field(..., description="세션 ID")
    topic: str = Field(..., description="분석된 운세 주제")

    # 캐릭터별 해석
    soiseol_interpretation: str = Field(..., description="소이설(동양) 해석")
    stella_interpretation: str = Field(..., description="스텔라(서양) 해석")

    # 합의/토론 상태
    is_consensus: bool = Field(..., description="두 캐릭터 합의 여부")
    consensus_point: str | None = Field(None, description="합의 포인트 (합의 시)")

    # Fortune 참조
    fortune_ref: FortuneReference = Field(..., description="사용된 운세 참조")


@router.post(
    "/chat/complete",
    response_model=CompleteResponse,
    summary="티키타카 대화 (Non-Streaming)",
    description="스트리밍 없이 전체 해석을 한 번에 응답합니다.",
    tags=["fortune-turn"],
    include_in_schema=False,  # 레거시 - Swagger에서 숨김
    responses={
        200: {
            "description": "분석 성공",
            "content": {
                "application/json": {
                    "example": {
                        "session_id": "abc12345",
                        "topic": "종합 운세",
                        "soiseol_interpretation": "병화 일간이시구려. 밝고 열정적이시오.",
                        "stella_interpretation": "양자리 태양이군요. 리더십과 추진력이 강해요.",
                        "is_consensus": True,
                        "consensus_point": "둘 다 열정적이고 활동적인 에너지를 지니셨소.",
                        "fortune_ref": {
                            "eastern_id": "east1234",
                            "western_id": "west5678",
                            "source": "created",
                        },
                    }
                }
            },
        },
        400: {"description": "잘못된 요청"},
        500: {"description": "서버 오류"},
    },
)
async def chat_complete(request: CompleteRequest) -> CompleteResponse:
    """
    티키타카 채팅 API (Non-Streaming)

    스트리밍 없이 전체 해석을 한 번에 응답합니다.
    SSE를 지원하지 않는 클라이언트나 테스트 환경에서 유용합니다.

    **요청 파라미터:**
    - **birth_date** (필수): 생년월일 (YYYY-MM-DD)
    - **birth_time** (선택): 출생시간 (HH:MM)
    - **topic** (선택): 운세 주제 (기본: 종합 운세)
    - **eastern_fortune_id** (선택): 기존 동양 운세 ID
    - **western_fortune_id** (선택): 기존 서양 운세 ID

    **응답:**
    - 소이설(동양)과 스텔라(서양)의 해석을 한 번에 응답
    - 두 캐릭터의 합의 여부 및 합의점 포함

    **vs /chat:**
    - `/chat`: 턴 기반, 세션 유지, 대화 진행
    - `/chat/complete`: 단일 요청, 전체 응답, 세션 자동 생성

    **vs /chat/stream:**
    - `/chat/stream`: SSE 스트리밍, 실시간 UI
    - `/chat/complete`: 단일 응답, 배치 처리 적합
    """
    logger.info(
        "chat_complete_request",
        birth_date=request.birth_date,
        topic=request.topic,
    )

    try:
        # 세션 생성
        session = create_session(
            birth_date=request.birth_date,
            birth_time=request.birth_time,
        )

        # 운세 분석 실행 (Fortune ID 재사용 지원)
        (
            eastern_result,
            western_result,
            eastern_id,
            western_id,
            source,
        ) = await _service.get_or_create_fortunes(
            birth_date=request.birth_date,
            birth_time=request.birth_time,
            eastern_fortune_id=request.eastern_fortune_id,
            western_fortune_id=request.western_fortune_id,
        )

        # 세션에 결과 저장
        session.eastern_result = eastern_result
        session.western_result = western_result
        session.eastern_fortune_id = eastern_id
        session.western_fortune_id = western_id
        session.fortune_source = source

        # 주제 결정
        topic = request.topic or "종합 운세"

        # 해석 메시지 생성
        if topic == "종합 운세":
            messages, debate_status = await _service.create_interpretation_messages(
                eastern_result, western_result
            )
        else:
            messages, debate_status, _ = await _service.create_topic_messages(
                topic=topic,
                eastern=eastern_result,
                western=western_result,
            )

        # 캐릭터별 메시지 추출
        soiseol_msg = ""
        stella_msg = ""
        for msg in messages:
            if msg.character == CharacterCode.SOISEOL and msg.type == MessageType.INTERPRETATION:
                soiseol_msg = msg.content
            elif msg.character == CharacterCode.STELLA and msg.type == MessageType.INTERPRETATION:
                stella_msg = msg.content

        # Fortune 참조 생성
        fortune_ref = FortuneReference(
            eastern_id=eastern_id,
            western_id=western_id,
            source=source,
        )

        logger.info(
            "chat_complete_success",
            session_id=session.session_id,
            topic=topic,
        )

        return CompleteResponse(
            session_id=session.session_id,
            topic=topic,
            soiseol_interpretation=soiseol_msg,
            stella_interpretation=stella_msg,
            is_consensus=debate_status.is_consensus,
            consensus_point=debate_status.eastern_opinion if debate_status.is_consensus else None,
            fortune_ref=fortune_ref,
        )

    except ValueError as e:
        logger.warning("chat_complete_validation_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"입력값 오류: {str(e)}",
        )
    except Exception as e:
        logger.error("chat_complete_error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"분석 중 오류가 발생했습니다: {str(e)}",
        )


# ============================================================
# 토큰 사용량 통계 API
# ============================================================


@router.get(
    "/chat/stats/tokens",
    summary="카테고리별 토큰 사용량 통계",
    tags=["fortune-stats"],
    description="카테고리별 평균 토큰 사용량을 조회합니다.",
    include_in_schema=False,  # 통계 - Swagger에서 숨김
    responses={
        200: {
            "description": "통계 조회 성공",
            "content": {
                "application/json": {
                    "example": {
                        "LOVE": {
                            "avg_prompt_tokens": 1200.5,
                            "avg_completion_tokens": 450.3,
                            "avg_total_tokens": 1650.8,
                            "total_calls": 150,
                        },
                        "GENERAL": {
                            "avg_prompt_tokens": 1100.2,
                            "avg_completion_tokens": 400.1,
                            "avg_total_tokens": 1500.3,
                            "total_calls": 200,
                        },
                    }
                }
            },
        },
    },
)
async def get_token_stats(
    category: str | None = Query(
        None,
        description="특정 카테고리만 조회 (GENERAL, LOVE, MONEY, CAREER, HEALTH, STUDY)",
    ),
):
    """
    카테고리별 토큰 사용량 통계 API

    GPT-5-mini 호출 시 사용된 토큰의 평균을 카테고리별로 조회합니다.

    **Query Parameters:**
    - **category** (선택): 특정 카테고리만 조회. 없으면 전체 카테고리 반환

    **응답 필드:**
    - **avg_prompt_tokens**: 평균 입력 토큰 수
    - **avg_completion_tokens**: 평균 출력 토큰 수
    - **avg_total_tokens**: 평균 총 토큰 수
    - **total_calls**: 총 호출 횟수
    """
    logger.info("token_stats_request", category=category)
    stats = await get_token_stats_by_category(category)
    return stats


@router.get(
    "/chat/stats/tokens/{session_id}",
    summary="세션별 토큰 사용 이력",
    tags=["fortune-stats"],
    description="특정 세션의 턴별 토큰 사용 이력을 조회합니다.",
    include_in_schema=False,  # 통계 - Swagger에서 숨김
    responses={
        200: {
            "description": "이력 조회 성공",
            "content": {
                "application/json": {
                    "example": {
                        "session_id": "abc12345",
                        "history": [
                            {
                                "turn": 1,
                                "category": "LOVE",
                                "prompt_tokens": 1200,
                                "completion_tokens": 450,
                                "total_tokens": 1650,
                            },
                            {
                                "turn": 2,
                                "category": "LOVE",
                                "prompt_tokens": 1350,
                                "completion_tokens": 480,
                                "total_tokens": 1830,
                            },
                        ],
                        "total_prompt_tokens": 2550,
                        "total_completion_tokens": 930,
                        "total_tokens": 3480,
                    }
                }
            },
        },
    },
)
async def get_session_tokens(session_id: str):
    """
    세션별 토큰 사용 이력 API

    특정 세션의 각 턴별 토큰 사용량을 조회합니다.

    **Path Parameters:**
    - **session_id**: 조회할 세션 ID

    **응답 필드:**
    - **history**: 턴별 토큰 사용 기록 리스트
    - **total_prompt_tokens**: 세션 전체 입력 토큰 합계
    - **total_completion_tokens**: 세션 전체 출력 토큰 합계
    - **total_tokens**: 세션 전체 토큰 합계
    """
    logger.info("session_token_history_request", session_id=session_id)
    history = await get_session_token_history(session_id)

    total_prompt = sum(h.get("prompt_tokens", 0) for h in history)
    total_completion = sum(h.get("completion_tokens", 0) for h in history)

    return {
        "session_id": session_id,
        "history": history,
        "total_prompt_tokens": total_prompt,
        "total_completion_tokens": total_completion,
        "total_tokens": total_prompt + total_completion,
    }


# ============================================================
# 턴 단위 티키타카 (분리된 엔드포인트)
# ============================================================


@router.post(
    "/chat/turn/start",
    response_model=TurnResponse,
    summary="Turn 0 - 세션 시작 및 그리팅",
    tags=["fortune-turn"],
    description="""
## Turn 0 - 세션 시작 및 그리팅 (프로덕션 API)

새로운 세션을 생성하고 운세 분석 후 카테고리별 그리팅을 반환합니다.

---

## 권장 플로우

### 1. 세션 시작 (Turn 0)
```
POST /chat/turn/start
{
  "birth_date": "1990-05-15",
  "category": "LOVE"
}
```
→ **session_id 반환** + 그리팅 메시지

### 2. 대화 계속 (Turn 1+)
```
POST /chat/turn/continue
{
  "session_id": "abc123",
  "message": "연애운이 궁금해요"
}
```
→ 티키타카 응답 + 다음 질문 제안

### 3. 요약 조회 (선택)
```
GET /chat/summary/{session_id}?type=eastern
```
→ 동양/서양 운세 요약

---

### 요청 파라미터
- **birth_date** (필수): 생년월일 (YYYY-MM-DD)
- **birth_time** (선택): 출생 시간 (HH:MM)
- **category** (필수): 운세 카테고리
- **char1_code** (선택): 캐릭터1 코드 (기본값: SOISEOL)
- **char2_code** (선택): 캐릭터2 코드 (기본값: STELLA)

### 운세 카테고리
- **GENERAL**: 종합운
- **LOVE**: 애정운
- **MONEY**: 재물운
- **CAREER**: 직장운
- **HEALTH**: 건강운
- **STUDY**: 학업운

### 스트리밍 모드
- **stream=true**: SSE 스트리밍 응답
- **stream=false** (기본): JSON 단일 응답

---

**Note:** 이 API는 세션을 자동으로 생성하므로 별도의 `/chat/session` 호출이 불필요합니다.
""",
    responses={
        200: {
            "description": "그리팅 생성 성공",
            "model": TurnResponse,
            "content": {
                "application/json": {
                    "example": {
                        "session_id": "abc12345",
                        "turn": 1,
                        "messages": [
                            {
                                "character": "SOISEOL",
                                "type": "GREETING",
                                "content": "연애운을 보러 온 귀하를 환영하오...",
                                "timestamp": "2024-01-27T15:30:00",
                            },
                            {
                                "character": "STELLA",
                                "type": "GREETING",
                                "content": "황소자리 태양이시군요!",
                                "timestamp": "2024-01-27T15:30:05",
                            },
                        ],
                        "suggested_question": "현재 마음에 두고 계신 분이 있으신지요?",
                        "is_complete": False,
                    }
                }
            },
        },
        400: {"description": "잘못된 입력 (생년월일 형식, 카테고리)"},
        500: {"description": "서버 오류"},
    },
)
async def chat_turn_start(
    request: TurnStartRequest,
    stream: bool = Query(default=False, description="SSE 스트리밍 여부 (기본: false)"),
):
    """
    Turn 0 전용 API - 세션 시작 및 그리팅 (프로덕션)

    새로운 세션을 생성하고 운세 분석 후 그리팅 메시지를 반환합니다.

    ---

    ## 권장 플로우

    ### 1. 세션 시작 (Turn 0)
    ```
    POST /chat/turn/start
    {
      "birth_date": "1990-05-15",
      "category": "LOVE"
    }
    ```
    → session_id 반환

    ### 2. 대화 계속 (Turn 1+)
    ```
    POST /chat/turn/continue
    {
      "session_id": "abc123",
      "message": "연애운이 궁금해요"
    }
    ```

    ### 3. 요약 조회 (선택)
    ```
    GET /chat/summary/{session_id}?type=eastern
    ```

    ---

    **응답:**
    - **session_id**: 생성된 세션 ID (다음 턴에 사용)
    - **turn**: 현재 턴 번호 (1)
    - **messages**: 그리팅 메시지 목록
    - **suggested_question**: 다음 질문 제안
    - **is_complete**: 3턴 완료 여부 (항상 false)
    """
    logger.info(
        "chat_turn_start_request",
        birth_date=request.birth_date,
        category=request.category.value,
    )

    try:
        # 생년월일 형식 검증
        try:
            datetime.strptime(request.birth_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="생년월일 형식이 잘못되었습니다. YYYY-MM-DD 형식으로 입력해주세요.",
            )

        # 세션 생성
        session = await get_or_create_session_async(None)
        session.turn = 1

        # 사용자 정보 저장
        session.user_info["birth_date"] = request.birth_date
        if request.birth_time:
            session.user_info["birth_time"] = request.birth_time
        session.category = request.category

        # 캐릭터 코드 저장 (turn/continue에서 사용)
        session.char1_code = request.char1_code
        session.char2_code = request.char2_code

        # 운세 분석 실행
        eastern, western = await _service.analyze_both(
            birth_date=request.birth_date,
            birth_time=request.birth_time,
            birth_place=None,
        )

        # 세션에 분석 결과 저장
        session.eastern_result = eastern
        session.western_result = western

        # 운세 컨텍스트 요약
        eastern_context = create_summarized_eastern_context(eastern)
        western_context = create_summarized_western_context(western)

        # SSE 스트리밍 응답 (OpenAI SDK + sse-starlette)
        if stream:
            from openai import AsyncOpenAI
            from sse_starlette.sse import EventSourceResponse

            from yeji_ai.prompts.gpt5mini_prompts import build_gpt5mini_tikitaka_prompt

            async def event_generator():
                """Turn 0 SSE 이벤트 생성기 (OpenAI SDK 사용)"""
                # 1. 세션 ID 즉시 전송
                yield {
                    "event": "session",
                    "data": json.dumps({"session_id": session.session_id}),
                }

                try:
                    # 2. AsyncOpenAI 클라이언트 생성
                    api_key = _service._settings.openai_api_key
                    model_name = _service._settings.openai_model
                    logger.info(
                        "SSE_openai_init",
                        model=model_name,
                        api_key_present=bool(api_key),
                        api_key_prefix=api_key[:10] + "..." if api_key else "NONE",
                    )
                    client = AsyncOpenAI(api_key=api_key)

                    # 3. 프롬프트 생성
                    system_prompt, user_prompt = build_gpt5mini_tikitaka_prompt(
                        topic=request.category.value,
                        eastern_context=str(eastern_context),
                        western_context=str(western_context),
                        mode="greeting",
                        char1_code=request.char1_code,
                        char2_code=request.char2_code,
                        user_question="",
                    )
                    logger.info(
                        "SSE_prompt_built",
                        system_len=len(system_prompt),
                        user_len=len(user_prompt),
                    )

                    # 4. OpenAI 스트리밍 호출
                    logger.info("SSE_openai_call_start", model=model_name)
                    openai_stream = await client.chat.completions.create(
                        model=model_name,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        stream=True,
                        max_completion_tokens=3000,
                    )
                    logger.info("SSE_openai_stream_created")

                    # 5. 스트리밍 청크를 SSE로 전달
                    full_response = ""
                    chunk_count = 0

                    logger.info("SSE_starting_chunk_iteration")
                    async for chunk in openai_stream:
                        # 청크 구조 디버깅
                        if chunk_count == 0:
                            logger.info(
                                "SSE_first_chunk_received",
                                chunk_type=type(chunk).__name__,
                                has_choices=bool(chunk.choices),
                                choices_len=len(chunk.choices) if chunk.choices else 0,
                            )
                        if chunk.choices and chunk.choices[0].delta.content:
                            content = chunk.choices[0].delta.content
                            full_response += content
                            chunk_count += 1
                            if chunk_count <= 3:
                                logger.info("SSE_chunk", num=chunk_count, content_len=len(content))
                            yield {
                                "event": "chunk",
                                "data": json.dumps({"content": content}, ensure_ascii=False),
                            }

                    # 6. 완료 이벤트 전송
                    suggested = f"{request.category.label_ko}에 대해 더 자세히 알고 싶어요"
                    yield {
                        "event": "complete",
                        "data": json.dumps({
                            "session_id": session.session_id,
                            "turn": session.turn,
                            "suggested_question": suggested,
                            "is_complete": False,
                        }, ensure_ascii=False),
                    }

                    # 7. 세션 저장
                    await save_session(session)

                    logger.info(
                        "SSE_stream_complete",
                        session_id=session.session_id,
                        response_len=len(full_response),
                        chunk_count=chunk_count,
                    )

                except Exception as e:
                    logger.error(
                        "SSE_stream_error",
                        error=str(e),
                        error_type=type(e).__name__,
                        session_id=session.session_id,
                    )
                    yield {
                        "event": "error",
                        "data": json.dumps({"message": str(e)}, ensure_ascii=False),
                    }

            return EventSourceResponse(event_generator())

        # Non-streaming: 기존 방식
        # GPT-5-mini로 그리팅 메시지 생성
        greeting_messages, _ = await _service.create_tikitaka_messages_gpt5mini(
            topic=request.category.value,
            eastern_context=str(eastern_context),
            western_context=str(western_context),
            mode="greeting",
            char1_code=request.char1_code,
            char2_code=request.char2_code,
            is_first_turn=True,
            is_last_turn=False,
            user_question="",
            session_id=session.session_id,
            category=request.category.value,
            turn=session.turn,
        )

        # 메시지 저장
        for msg in greeting_messages:
            session.add_message(msg)

        # 다음 질문 제안
        suggested_question = f"{request.category.label_ko}에 대해 더 자세히 알고 싶어요"

        logger.info(
            "chat_turn_start_success",
            session_id=session.session_id,
            turn=session.turn,
        )

        # 세션 Redis 저장
        await save_session(session)

        # JSON 응답
        return TurnResponse(
            session_id=session.session_id,
            turn=session.turn,
            messages=greeting_messages,
            suggested_question=suggested_question,
            is_complete=False,
        )

    except ValueError as e:
        logger.warning("chat_turn_start_validation_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"입력값 오류: {str(e)}",
        )
    except Exception as e:
        logger.error("chat_turn_start_error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"그리팅 생성 중 오류가 발생했습니다: {str(e)}",
        )


@router.post(
    "/chat/turn/continue",
    response_model=TurnResponse,
    summary="Turn 1+ - 대화 진행",
    tags=["fortune-turn"],
    description="""
## Turn 1+ - 대화 진행 (프로덕션 API)

기존 세션을 기반으로 티키타카 대화를 진행합니다.

---

## 권장 플로우

### 1. 세션 시작 (Turn 0)
```
POST /chat/turn/start
{
  "birth_date": "1990-05-15",
  "category": "LOVE"
}
```
→ session_id 반환

### 2. 대화 계속 (Turn 1+) ← **현재 API**
```
POST /chat/turn/continue
{
  "session_id": "abc123",
  "message": "연애운이 궁금해요"
}
```
→ 티키타카 응답 + 다음 질문 제안

### 3. 요약 조회 (선택)
```
GET /chat/summary/{session_id}?type=eastern
```

---

### 요청 파라미터
- **session_id** (필수): Turn 0에서 받은 세션 ID
- **message** (필수): 사용자 메시지
- **char1_code** (선택): 캐릭터1 코드 (기본값: SOISEOL)
- **char2_code** (선택): 캐릭터2 코드 (기본값: STELLA)

### 스트리밍 모드
- **stream=true**: SSE 스트리밍 응답
- **stream=false** (기본): JSON 단일 응답

---

**Note:** 세션은 Turn 3까지 진행 가능하며, is_complete=true가 되면 대화가 종료됩니다.
""",
    responses={
        200: {
            "description": "대화 응답 성공",
            "model": TurnResponse,
            "content": {
                "application/json": {
                    "example": {
                        "session_id": "abc12345",
                        "turn": 2,
                        "messages": [
                            {
                                "character": "SOISEOL",
                                "type": "INTERPRETATION",
                                "content": "귀하의 사주를 보니 올해 인연이 찾아올 기운이...",
                                "timestamp": "2024-01-27T15:31:00",
                            },
                            {
                                "character": "STELLA",
                                "type": "INTERPRETATION",
                                "content": "금성이 7하우스를 지나고 있어서 좋은 만남이...",
                                "timestamp": "2024-01-27T15:31:05",
                            },
                        ],
                        "suggested_question": "어떤 스타일의 상대를 원하시나요?",
                        "is_complete": False,
                    }
                }
            },
        },
        400: {"description": "잘못된 세션 ID"},
        404: {"description": "세션을 찾을 수 없음"},
        500: {"description": "서버 오류"},
    },
)
async def chat_turn_continue(
    request: TurnContinueRequest,
    stream: bool = Query(default=False, description="SSE 스트리밍 여부 (기본: false)"),
):
    """
    Turn 1+ 전용 API - 대화 진행 (프로덕션)

    기존 세션을 기반으로 사용자 질문에 대한 티키타카 응답을 생성합니다.

    ---

    ## 권장 플로우

    ### 1. 세션 시작 (Turn 0)
    ```
    POST /chat/turn/start
    {
      "birth_date": "1990-05-15",
      "category": "LOVE"
    }
    ```
    → session_id 반환

    ### 2. 대화 계속 (Turn 1+)
    ```
    POST /chat/turn/continue
    {
      "session_id": "abc123",
      "message": "연애운이 궁금해요"
    }
    ```

    ### 3. 요약 조회 (선택)
    ```
    GET /chat/summary/{session_id}?type=eastern
    ```

    ---

    **응답:**
    - **session_id**: 세션 ID
    - **turn**: 현재 턴 번호 (2, 3, ...)
    - **messages**: 티키타카 메시지 목록
    - **suggested_question**: 다음 질문 제안
    - **is_complete**: 10턴 완료 여부 (turn >= 10)
    """
    logger.info(
        "chat_turn_continue_request",
        session_id=request.session_id,
        message=request.message[:50] if request.message else None,
    )

    try:
        # 세션 조회
        session = await get_session_async(request.session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"세션을 찾을 수 없습니다: {request.session_id}",
            )

        # 분석 결과 확인
        if not session.eastern_result or not session.western_result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="운세 분석이 완료되지 않았습니다. /chat/turn/start를 먼저 호출하세요.",
            )

        # 턴 증가
        session.turn += 1

        # 세션에서 카테고리 조회
        category = session.category
        if not category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="세션에 카테고리 정보가 없습니다.",
            )

        # 운세 컨텍스트 요약
        eastern_context = create_summarized_eastern_context(session.eastern_result)
        western_context = create_summarized_western_context(session.western_result)

        # 종료 체크 (5턴 또는 force_end)
        is_complete = session.turn >= (5 if request.extend_turn else 3)

        # 캐릭터 코드: request 기본값이면 세션에서 가져옴
        char1 = session.char1_code if request.char1_code == "SOISEOL" else request.char1_code
        char2 = session.char2_code if request.char2_code == "STELLA" else request.char2_code

        # SSE 스트리밍 응답 (깡 SSE - 메시지 먼저 생성 후 하나씩 전송)
        if stream:

            async def generate_continue_stream():
                """Turn 1+ 스트리밍 생성기 (깡 SSE)"""
                import asyncio

                # 1. 세션 ID 즉시 전송
                session_event = {"event": "session", "session_id": session.session_id}
                yield f"data: {json.dumps(session_event)}\n\n"

                # 2. 메시지 먼저 전체 생성 (non-streaming)
                try:
                    messages, debate_status = await _service.create_tikitaka_messages_gpt5mini(
                        topic=request.message or category.label_ko,
                        eastern_context=str(eastern_context),
                        western_context=str(western_context),
                        mode="battle",
                        char1_code=char1,
                        char2_code=char2,
                        is_first_turn=(session.turn == 2),
                        is_last_turn=(session.turn >= (5 if request.extend_turn else 3)),
                        user_question=request.message,
                        session_id=session.session_id,
                        category=category.value,
                        turn=session.turn,
                    )

                    # 3. 생성된 메시지를 하나씩 SSE로 전송
                    for idx, msg in enumerate(messages):
                        # 캐릭터/타입 값 추출
                        char_val = (
                            msg.character.value
                            if hasattr(msg.character, "value")
                            else str(msg.character)
                        )
                        type_val = (
                            msg.type.value
                            if hasattr(msg.type, "value")
                            else str(msg.type)
                        )
                        bubble_event = {
                            "event": "bubble",
                            "data": {
                                "bubble_id": f"bubble_{idx}",
                                "character": char_val,
                                "content": msg.content,
                                "type": type_val,
                            },
                        }
                        yield f"data: {json.dumps(bubble_event, ensure_ascii=False)}\n\n"
                        # 메시지 간 짧은 딜레이 (UX 개선)
                        await asyncio.sleep(0.1)

                    # 4. 세션에 메시지 저장
                    for msg in messages:
                        session.add_message(msg)
                    await save_session(session)

                    # 5. 완료 이벤트 전송
                    suggested_q = debate_status.question or "다른 주제가 궁금하신가요?"
                    complete_event = {
                        "event": "complete",
                        "data": {
                            "bubble_count": len(messages),
                            "session_id": session.session_id,
                            "turn": session.turn,
                            "suggested_question": suggested_q,
                            "is_complete": is_complete,
                        },
                    }
                    yield f"data: {json.dumps(complete_event, ensure_ascii=False)}\n\n"

                except Exception as e:
                    logger.error("SSE 스트리밍 오류", error=str(e))
                    error_event = {"event": "error", "data": {"message": str(e)}}
                    yield f"data: {json.dumps(error_event)}\n\n"

            return StreamingResponse(
                generate_continue_stream(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                },
            )

        # Non-streaming: 기존 방식
        # GPT-5-mini 티키타카 메시지 생성
        messages, debate_status = await _service.create_tikitaka_messages_gpt5mini(
            topic=request.message or category.label_ko,
            eastern_context=str(eastern_context),
            western_context=str(western_context),
            mode="battle",
            char1_code=char1,
            char2_code=char2,
            is_first_turn=(session.turn == 2),  # Turn 1은 그리팅, Turn 2가 첫 질문
            is_last_turn=(session.turn >= (5 if request.extend_turn else 3)),
            user_question=request.message,
            session_id=session.session_id,
            category=category.value,
            turn=session.turn,
        )

        # 메시지 저장
        for msg in messages:
            session.add_message(msg)

        # 다음 질문 제안
        suggested_question = debate_status.question or "다른 주제가 궁금하신가요?"

        logger.info(
            "chat_turn_continue_success",
            session_id=session.session_id,
            turn=session.turn,
            is_complete=is_complete,
        )

        # 세션 Redis 저장
        await save_session(session)

        # JSON 응답
        return TurnResponse(
            session_id=session.session_id,
            turn=session.turn,
            messages=messages,
            suggested_question=suggested_question,
            is_complete=is_complete,
        )

    except ValueError as e:
        logger.warning("chat_turn_continue_validation_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"입력값 오류: {str(e)}",
        )
    except Exception as e:
        logger.error("chat_turn_continue_error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"대화 처리 중 오류가 발생했습니다: {str(e)}",
        )
