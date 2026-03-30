"""Simple Q&A API - 사주/점성 관련 질문만 처리

## 사용 흐름

```
POST /api/v1/fortune/simple
{ "question": "오늘 연애운 어때?" }

→ 사주/점성 키워드 감지 시: LLM 응답
→ 관련 없는 질문 시: 랜덤 운세 반환
```

## 인텐트 필터

- 허용: 사주, 운세, 점성, 별자리, 십신, 오행 등
- 차단: 코드, 날씨, 뉴스, 주식 등 (랜덤 운세로 대체)
"""

from __future__ import annotations

import random

import httpx
import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from yeji_ai.config import get_settings

logger = structlog.get_logger()
router = APIRouter()

# 제거할 외래 문자 범위 (태국어, 아랍어, 히브리어 등 - 한자는 유지)
FOREIGN_CHAR_RANGES = [
    (0x0E00, 0x0E7F),   # Thai
    (0x0600, 0x06FF),   # Arabic
    (0x0590, 0x05FF),   # Hebrew
    (0x0900, 0x097F),   # Devanagari (Hindi)
    (0x0980, 0x09FF),   # Bengali
    (0x0A00, 0x0A7F),   # Gurmukhi (Punjabi)
    (0x0B00, 0x0B7F),   # Oriya
    (0x0C00, 0x0C7F),   # Telugu
    (0x0C80, 0x0CFF),   # Kannada
    (0x0D00, 0x0D7F),   # Malayalam
    (0x0D80, 0x0DFF),   # Sinhala
    (0x1000, 0x109F),   # Myanmar
    (0x10A0, 0x10FF),   # Georgian
]


def is_foreign_char(char: str) -> bool:
    """태국어 등 외래 문자인지 확인 (한자는 허용)"""
    code = ord(char)
    for start, end in FOREIGN_CHAR_RANGES:
        if start <= code <= end:
            return True
    return False


def remove_noise_chars(text: str) -> str:
    """태국어 등 노이즈 문자만 제거 (한자 유지)"""
    return "".join(char for char in text if not is_foreign_char(char))

# 사주/점성 관련 키워드 (허용)
FORTUNE_KEYWORDS = [
    # 사주 관련
    "사주", "팔자", "운세", "운명", "점", "명리", "천간", "지지",
    "갑을병정", "자축인묘", "일간", "월주", "시주", "년주",
    "십신", "육친", "관성", "재성", "인성", "비겁", "식상",
    "대운", "세운", "월운", "일운", "용신", "기신",
    # 점성술 관련
    "점성", "별자리", "태양궁", "달궁", "상승궁", "하우스",
    "행성", "수성", "금성", "화성", "목성", "토성", "천왕성", "해왕성", "명왕성",
    "양자리", "황소자리", "쌍둥이자리", "게자리", "사자자리", "처녀자리",
    "천칭자리", "전갈자리", "사수자리", "염소자리", "물병자리", "물고기자리",
    # 운세 카테고리
    "연애운", "애정운", "결혼운", "금전운", "재물운", "직장운", "취업운",
    "건강운", "학업운", "시험운", "대인운", "이직", "승진", "투자",
    # 일반
    "오늘", "내일", "이번주", "이번달", "올해", "내년",
    "궁합", "타로", "신년운", "토정비결",
]

# 거부 키워드 (명확히 관련 없는 것)
BLOCKED_KEYWORDS = [
    "코드", "프로그래밍", "개발", "버그", "에러",
    "날씨", "뉴스", "주식", "비트코인", "환율",
    "맛집", "여행", "영화", "음악", "게임",
    "정치", "경제", "사회", "스포츠",
]

# 랜덤 오늘의 운세 (인텐트 미일치 시 반환)
RANDOM_FORTUNES = [
    "오늘은 새로운 인연이 찾아올 기운이 있습니다.",
    "작은 결정이 큰 행운을 부를 수 있는 날입니다.",
    "오후에 좋은 소식이 들려올 수 있으니 기대해보세요.",
    "오늘은 차분히 내면을 돌아보기 좋은 날입니다.",
    "금전적으로 작은 이득이 생길 수 있는 기운이 감지됩니다.",
    "오늘 만나는 사람이 귀인이 될 수 있으니 친절을 베푸세요.",
    "직감을 믿으면 좋은 결과가 따라올 것입니다.",
    "오늘은 새로운 시작에 좋은 에너지가 흐릅니다.",
    "가까운 사람에게 연락하면 뜻밖의 기쁨이 있을 것입니다.",
    "오늘은 급하게 결정하기보다 한 템포 쉬어가세요.",
    "동쪽 방향에서 행운이 찾아올 기운이 있습니다.",
    "오늘의 행운색은 파란색, 숫자는 7입니다.",
    "오전보다 오후에 일이 더 잘 풀릴 기운입니다.",
    "오늘은 솔직한 대화가 관계를 더 좋게 만들어줄 것입니다.",
    "작은 것에 감사하면 큰 복이 따라오는 날입니다.",
]


class SimpleRequest(BaseModel):
    """단순 질문 요청"""
    question: str = Field(..., min_length=2, max_length=500, description="질문")


class SimpleResponse(BaseModel):
    """단순 응답"""
    success: bool
    answer: str
    filtered: bool = False
    filter_reason: str | None = None


def postprocess_answer(answer: str) -> str:
    """LLM 응답 후처리 - 태국어만 제거, 한자는 유지"""
    # 1. 태국어 등 노이즈 문자만 제거 (한자 유지)
    answer = remove_noise_chars(answer)

    # 2. 첫 문장만 추출 (마침표/물음표/느낌표 기준)
    import re
    sentences = re.split(r'(?<=[.!?~])\s*', answer.strip())
    if sentences:
        answer = sentences[0].strip()

    # 3. 연속 공백 정리
    answer = re.sub(r'\s+', ' ', answer).strip()

    return answer


def check_intent(question: str) -> tuple[bool, str | None]:
    """인텐트 체크 - 사주/점성 관련인지 확인

    Returns:
        (허용 여부, 거부 사유)
    """
    q_lower = question.lower()

    # 거부 키워드 체크
    for keyword in BLOCKED_KEYWORDS:
        if keyword in q_lower:
            return False, f"'{keyword}' 관련 질문은 처리할 수 없습니다"

    # 허용 키워드 체크
    for keyword in FORTUNE_KEYWORDS:
        if keyword in q_lower:
            return True, None

    # 키워드 없으면 기본 거부
    return False, "사주/점성술 관련 질문만 답변 가능합니다"


@router.post(
    "/simple",
    response_model=SimpleResponse,
    summary="단순 Q&A",
    description="사주/점성 관련 질문에 한줄로 답변합니다.",
)
async def simple_qa(request: SimpleRequest) -> SimpleResponse:
    """단순 Q&A 엔드포인트"""
    logger.info("simple_qa_request", question=request.question[:50])

    # 인텐트 체크
    allowed, reason = check_intent(request.question)
    if not allowed:
        # 랜덤 오늘의 운세 반환
        random_fortune = random.choice(RANDOM_FORTUNES)
        logger.info("simple_qa_random_fortune", reason=reason)
        return SimpleResponse(
            success=True,
            answer=random_fortune,
            filtered=True,
            filter_reason=reason,
        )

    # vLLM 호출
    settings = get_settings()

    system_prompt = """사주/점성술 전문가. 한 문장만 답변.

[필수]
- 한국어 한 문장 (마침표로 끝)
- 30자 이내
- 설명/이유/부연 절대 금지
- 여러 문장 금지

[답변 형식]
"OOO입니다." 또는 "OOO해요."

[예시]
Q: 오늘 연애운?
A: 좋은 인연이 다가올 기운입니다.

Q: 이직 시기?
A: 3개월 후가 적기입니다.
"""

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{settings.vllm_base_url}/v1/chat/completions",
                json={
                    "model": settings.vllm_model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": request.question},
                    ],
                    "max_tokens": 150,
                    "temperature": 0.7,
                },
            )
            response.raise_for_status()
            data = response.json()
            answer = data["choices"][0]["message"]["content"].strip()

            # 후처리 파이프라인
            answer = postprocess_answer(answer)

            logger.info("simple_qa_success", answer_len=len(answer))
            return SimpleResponse(success=True, answer=answer)

    except httpx.TimeoutException:
        logger.error("simple_qa_timeout")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="LLM 응답 시간 초과",
        )
    except Exception as e:
        logger.error("simple_qa_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"처리 중 오류: {str(e)}",
        )
