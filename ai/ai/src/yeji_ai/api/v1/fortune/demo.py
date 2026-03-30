"""티키타카 데모/테스트 API

간편하게 티키타카 채팅을 테스트할 수 있는 엔드포인트
"""

from datetime import datetime

import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from yeji_ai.models.fortune.chat import CharacterCode, ChatMessage, FortuneCategory
from yeji_ai.services.tikitaka_service import (
    TikitakaService,
    create_session,
    get_or_create_session,
)

logger = structlog.get_logger()
router = APIRouter(prefix="/demo", tags=["Demo - 티키타카 테스트"])

# 유효한 캐릭터 코드 집합
VALID_CHARACTERS = {code.value for code in CharacterCode}


class FortuneTestRequest(BaseModel):
    """운세 테스트 요청 (턴 단위)"""

    session_id: str | None = Field(None, description="세션 ID (없으면 새 세션)")
    birth_date: str = Field(
        ...,
        description="생년월일 (YYYY-MM-DD)",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        examples=["1990-05-15"],
    )
    birth_time: str | None = Field(
        None,
        description="출생 시간 (HH:MM, 선택)",
        pattern=r"^\d{2}:\d{2}$",
        examples=["14:30"],
    )
    category: FortuneCategory = Field(
        ..., description="운세 카테고리 (GENERAL/LOVE/MONEY/CAREER/HEALTH/STUDY)"
    )
    message: str | None = Field(None, description="사용자 메시지 (turn 1+ 에서 사용)")

    char1_code: str = Field(
        "SOISEOL",
        description="캐릭터1 코드 (동양 계열 권장: SOISEOL, CHEONGWOON, HWARIN)",
        examples=["SOISEOL"],
    )
    char2_code: str = Field(
        "STELLA",
        description="캐릭터2 코드 (서양 계열 권장: STELLA, KYLE, ELARIA)",
        examples=["STELLA"],
    )


class FortuneTestResponse(BaseModel):
    """운세 테스트 응답 (턴 단위)"""

    session_id: str = Field(..., description="세션 ID")
    turn: int = Field(..., description="현재 턴 번호")
    messages: list[ChatMessage] = Field(..., description="소이설/스텔라 메시지")
    suggested_question: str = Field(..., description="다음 질문 제안")
    is_complete: bool = Field(False, description="3턴 완료 여부")


class DemoRequest(BaseModel):
    """티키타카 데모 요청 (Deprecated)"""

    birth_date: str = Field(
        ...,
        description="생년월일 (YYYY-MM-DD)",
        examples=["1990-05-15"],
    )
    birth_time: str | None = Field(
        None,
        description="출생 시간 (HH:MM, 선택)",
        examples=["14:30"],
    )
    birth_place: str | None = Field(
        None,
        description="출생 지역 (선택)",
        examples=["서울"],
    )

    # 캐릭터 선택 필드
    char1_code: str = Field(
        "SOISEOL",
        description="캐릭터1 코드 (동양 계열 권장: SOISEOL, CHEONGWOON, HWARIN)",
        examples=["SOISEOL"],
    )
    char2_code: str = Field(
        "STELLA",
        description="캐릭터2 코드 (서양 계열 권장: STELLA, KYLE, ELARIA)",
        examples=["STELLA"],
    )


class DemoBubble(BaseModel):
    """데모 버블"""

    character: str
    text: str
    turn: int


class DemoResponse(BaseModel):
    """티키타카 3턴 데모 응답 (Deprecated)"""

    session_id: str
    total_turns: int = 3
    bubbles: list[DemoBubble]
    characters: dict[str, dict] = Field(
        description="선택된 캐릭터 정보 {코드: {name, type, speech, emoji}}"
    )


@router.post(
    "/fortune-test",
    response_model=FortuneTestResponse,
    summary="운세 테스트 (턴 단위)",
    description="""
## 운세 테스트 API (턴 단위 인터랙션)

카테고리별 운세를 턴 단위로 테스트할 수 있습니다.

### 동작 방식
- **Turn 0 (session_id 없음)**: 카테고리별 그리팅 생성
- **Turn 1+**: 사용자 메시지에 대한 응답 생성
- 각 턴 끝에 **다음 질문 제안** 포함

### 캐릭터 목록
**동양 계열:**
- **SOISEOL** (소이설): 따뜻한 온미녀 - 하오체 🌸
- **CHEONGWOON** (청운): 신선/현자 - 시적 하오체 🌙
- **HWARIN** (화린): 비즈니스/정보상 - 나른한 해요체 🌸

**서양 계열:**
- **STELLA** (스텔라): 쿨한 냉미녀 - 해요체 ❄️
- **KYLE** (카일): 도박사 - 반말+존댓말 혼용 🎲
- **ELARIA** (엘라리아): 공주/외교관 - 우아한 해요체 👑

### 추천 조합
- SOISEOL + STELLA (기본 조합)
- CHEONGWOON + ELARIA (우아한 조합)
- HWARIN + KYLE (비즈니스 vs 도박)

### 운세 카테고리
- **GENERAL**: 종합운
- **LOVE**: 애정운
- **MONEY**: 재물운
- **CAREER**: 직장운
- **HEALTH**: 건강운
- **STUDY**: 학업운
""",
    responses={
        200: {"description": "턴 응답 성공"},
        400: {"description": "잘못된 입력 (생년월일 형식, 카테고리, 캐릭터 코드)"},
        500: {"description": "서버 오류"},
    },
)
async def fortune_test(request: FortuneTestRequest) -> FortuneTestResponse:
    """운세 테스트 API (턴 단위)"""

    # 생년월일 검증
    try:
        datetime.strptime(request.birth_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="생년월일 형식이 잘못되었습니다. YYYY-MM-DD 형식으로 입력해주세요.",
        )

    # 캐릭터 유효성 검증
    if request.char1_code not in VALID_CHARACTERS:
        raise HTTPException(
            status_code=400,
            detail=f"잘못된 캐릭터1 코드: {request.char1_code}. "
            f"유효한 코드: {', '.join(sorted(VALID_CHARACTERS))}",
        )
    if request.char2_code not in VALID_CHARACTERS:
        raise HTTPException(
            status_code=400,
            detail=f"잘못된 캐릭터2 코드: {request.char2_code}. "
            f"유효한 코드: {', '.join(sorted(VALID_CHARACTERS))}",
        )
    if request.char1_code == request.char2_code:
        raise HTTPException(
            status_code=400,
            detail="두 캐릭터는 서로 달라야 합니다.",
        )

    service = TikitakaService()

    try:
        # 세션 조회/생성
        session = get_or_create_session(request.session_id)

        # 사용자 정보 저장
        session.user_info["birth_date"] = request.birth_date
        if request.birth_time:
            session.user_info["birth_time"] = request.birth_time
        session.category = request.category

        # Turn 0: 그리팅 생성 (분석 전)
        if session.turn == 0 or not session.eastern_result:
            session.turn += 1

            # 카테고리별 그리팅 생성
            greeting_messages = service.create_greeting_messages(category=request.category)

            # 운세 분석 실행 (백그라운드)
            eastern, western = await service.analyze_both(
                birth_date=request.birth_date,
                birth_time=request.birth_time,
                birth_place=None,
            )

            # 세션에 분석 결과 저장
            session.eastern_result = eastern
            session.western_result = western

            # 메시지 저장
            for msg in greeting_messages:
                session.add_message(msg)

            # 다음 질문 제안
            suggested_question = f"{request.category.label_ko}에 대해 더 자세히 알고 싶어요"

            return FortuneTestResponse(
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
            topic = request.message or f"{request.category.label_ko}"

            # 주제별 메시지 생성
            messages, debate_status, ui_hints = await service.create_topic_messages(
                topic=topic,
                eastern=session.eastern_result,
                western=session.western_result,
                char1_code=request.char1_code,
                char2_code=request.char2_code,
            )

            # 메시지 저장
            for msg in messages:
                session.add_message(msg)

            # 다음 질문 제안 (debate_status.question 사용)
            suggested_question = debate_status.question or "다른 주제가 궁금하신가요?"

            # 3턴 완료 체크
            is_complete = session.turn >= 3

            return FortuneTestResponse(
                session_id=session.session_id,
                turn=session.turn,
                messages=messages,
                suggested_question=suggested_question,
                is_complete=is_complete,
            )

    except Exception as e:
        logger.error("fortune_test_error", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"운세 테스트 중 오류가 발생했습니다: {str(e)}",
        )


@router.post(
    "/tikitaka-3turn",
    response_model=DemoResponse,
    deprecated=True,
    include_in_schema=False,  # Deprecated - Swagger에서 숨김
    summary="🎭 티키타카 3턴 데모 (Deprecated)",
    description="""
## ⚠️ Deprecated: /fortune-test 사용 권장

생년월일과 캐릭터를 선택하면 바로 3턴의 티키타카 대화를 체험할 수 있습니다.

**새 API 권장**: `/demo/fortune-test` (턴 단위 인터랙션)
""",
    responses={
        200: {"description": "3턴 대화 성공"},
        400: {"description": "잘못된 입력 (생년월일 형식, 캐릭터 코드)"},
        500: {"description": "서버 오류"},
    },
)
async def demo_tikitaka_3turn(request: DemoRequest):
    """티키타카 3턴 데모 실행"""

    # 생년월일 검증
    try:
        datetime.strptime(request.birth_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="생년월일 형식이 잘못되었습니다. YYYY-MM-DD 형식으로 입력해주세요.",
        )

    # 캐릭터 유효성 검증
    if request.char1_code not in VALID_CHARACTERS:
        raise HTTPException(
            status_code=400,
            detail=f"잘못된 캐릭터1 코드: {request.char1_code}. "
            f"유효한 코드: {', '.join(sorted(VALID_CHARACTERS))}",
        )
    if request.char2_code not in VALID_CHARACTERS:
        raise HTTPException(
            status_code=400,
            detail=f"잘못된 캐릭터2 코드: {request.char2_code}. "
            f"유효한 코드: {', '.join(sorted(VALID_CHARACTERS))}",
        )
    if request.char1_code == request.char2_code:
        raise HTTPException(
            status_code=400,
            detail="두 캐릭터는 서로 달라야 합니다.",
        )

    service = TikitakaService()
    session = create_session(
        birth_date=request.birth_date,
        birth_time=request.birth_time,
    )

    bubbles = []

    try:
        # 동양/서양 분석 실행
        eastern, western = await service.analyze_both(
            birth_date=request.birth_date,
            birth_time=request.birth_time,
            birth_place=request.birth_place,
        )

        # 세션에 분석 결과 저장 (추가 대화를 위해)
        session.eastern_result = eastern
        session.western_result = western
        session.user_info["birth_date"] = request.birth_date
        if request.birth_time:
            session.user_info["birth_time"] = request.birth_time
        session.turn = 3  # 3턴 완료 표시

        # Turn 1: 인사 + 첫 분석
        turn1_msgs, _ = await service.create_interpretation_messages(
            eastern, western, request.char1_code, request.char2_code
        )
        for msg in turn1_msgs[:2]:  # 인사 2개
            bubbles.append(
                DemoBubble(
                    character=msg.character.value,
                    text=msg.content,
                    turn=1,
                )
            )

        # Turn 2: 연애운
        turn2_msgs, _, _ = await service.create_topic_messages(
            "연애운", eastern, western, request.char1_code, request.char2_code
        )
        for msg in turn2_msgs[:2]:
            bubbles.append(
                DemoBubble(
                    character=msg.character.value,
                    text=msg.content,
                    turn=2,
                )
            )

        # Turn 3: 직장운/금전운
        turn3_msgs, _, _ = await service.create_topic_messages(
            "직장운", eastern, western, request.char1_code, request.char2_code
        )
        for msg in turn3_msgs[:2]:
            bubbles.append(
                DemoBubble(
                    character=msg.character.value,
                    text=msg.content,
                    turn=3,
                )
            )

        # 캐릭터 정보 매핑
        character_info = {
            "SOISEOL": {
                "name": "소이설",
                "type": "eastern",
                "speech": "하오체",
                "emoji": "🌸",
            },
            "STELLA": {
                "name": "스텔라",
                "type": "western",
                "speech": "해요체",
                "emoji": "❄️",
            },
            "CHEONGWOON": {
                "name": "청운",
                "type": "eastern",
                "speech": "시적 하오체",
                "emoji": "🌙",
            },
            "HWARIN": {
                "name": "화린",
                "type": "eastern",
                "speech": "나른한 해요체",
                "emoji": "🌸",
            },
            "KYLE": {
                "name": "카일",
                "type": "western",
                "speech": "반말+존댓말 혼용",
                "emoji": "🎲",
            },
            "ELARIA": {
                "name": "엘라리아",
                "type": "western",
                "speech": "우아한 해요체",
                "emoji": "👑",
            },
        }

        # 선택된 캐릭터만 포함
        selected_chars = {
            request.char1_code: character_info[request.char1_code],
            request.char2_code: character_info[request.char2_code],
        }

        return DemoResponse(
            session_id=session.session_id,
            total_turns=3,
            bubbles=bubbles,
            characters=selected_chars,
        )

    except Exception as e:
        logger.error("demo_error", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"데모 실행 중 오류가 발생했습니다: {str(e)}",
        )


@router.get(
    "/characters",
    summary="📋 캐릭터 목록",
    description="사용 가능한 캐릭터 목록과 말투 스타일을 반환합니다.",
)
async def list_characters():
    """캐릭터 목록 조회"""
    return {
        "characters": [
            {
                "code": "SOISEOL",
                "name": "소이설",
                "type": "eastern",
                "speech": "하오체",
                "personality": "따뜻한 온미녀",
                "emoji": "🌸",
            },
            {
                "code": "STELLA",
                "name": "스텔라",
                "type": "western",
                "speech": "해요체",
                "personality": "쿨한 냉미녀",
                "emoji": "❄️",
            },
            {
                "code": "CHEONGWOON",
                "name": "청운",
                "type": "eastern",
                "speech": "시적 하오체",
                "personality": "신선/현자",
                "emoji": "🌙",
            },
            {
                "code": "HWARIN",
                "name": "화린",
                "type": "eastern",
                "speech": "나른한 해요체",
                "personality": "비즈니스/정보상",
                "emoji": "🌸",
            },
            {
                "code": "KYLE",
                "name": "카일",
                "type": "western",
                "speech": "반말+존댓말 혼용",
                "personality": "도박사",
                "emoji": "🎲",
            },
            {
                "code": "ELARIA",
                "name": "엘라리아",
                "type": "western",
                "speech": "우아한 해요체",
                "personality": "공주/외교관",
                "emoji": "👑",
            },
        ],
        "recommended_pairs": [
            {"char1": "SOISEOL", "char2": "STELLA", "desc": "기본 조합 (동양 vs 서양)"},
            {"char1": "CHEONGWOON", "char2": "ELARIA", "desc": "우아한 조합 (신선 vs 공주)"},
            {"char1": "HWARIN", "char2": "KYLE", "desc": "비즈니스 vs 도박"},
        ],
    }
