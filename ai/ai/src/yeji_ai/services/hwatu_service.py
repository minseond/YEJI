"""화투점 리딩 서비스

4장 스프레드 화투점 리딩 생성
"""

import json
from datetime import UTC, datetime
from typing import Any

import structlog

from yeji_ai.clients.vllm_client import GenerationConfig, VLLMClient
from yeji_ai.models.enums import PromptVersion
from yeji_ai.models.enums.hwatu import HWATU_CARDS, get_card_by_code
from yeji_ai.models.fortune.hwatu import (
    HwatuCardInterpretation,
    HwatuLucky,
    HwatuReadingMeta,
    HwatuReadingRequest,
    HwatuReadingResponse,
    HwatuReadingSummary,
)
from yeji_ai.prompts.hwatu_prompts import (
    HWATU_SYSTEM_PROMPT,
    build_hwatu_reading_prompt,
)

logger = structlog.get_logger()


# ============================================================
# 서비스 에러 정의
# ============================================================


class HwatuServiceError(Exception):
    """화투점 서비스 오류"""

    def __init__(self, message: str, error_code: str = "HWATU_ERROR"):
        super().__init__(message)
        self.message = message
        self.error_code = error_code


# ============================================================
# 화투점 서비스
# ============================================================


class HwatuService:
    """화투점 리딩 서비스

    4장 스프레드 화투점 리딩 생성 및 해석
    """

    def __init__(self):
        """서비스 초기화"""
        self._initialized = False
        self._client: VLLMClient | None = None

    async def initialize(self):
        """서비스 비동기 초기화"""
        if self._initialized:
            return

        logger.info("hwatu_service_initializing")
        self._client = VLLMClient()
        self._initialized = True
        logger.info("hwatu_service_initialized")

    async def generate_reading(
        self,
        request: HwatuReadingRequest,
        prompt_version: PromptVersion = PromptVersion.STANDARD,
    ) -> HwatuReadingResponse:
        """화투점 리딩 생성

        Args:
            request: 화투점 리딩 요청 (질문 + 4장 카드)

        Returns:
            화투점 리딩 응답 (해석 + 종합)

        Raises:
            HwatuServiceError: 서비스 오류 발생 시
        """
        if not self._initialized:
            await self.initialize()

        logger.info(
            "hwatu_reading_start",
            question=request.question,
            card_count=len(request.cards),
        )

        try:
            # LLM 호출 시도
            llm_response = await self._call_llm(request, prompt_version=prompt_version)

            use_fallback = True

            if llm_response:
                # LLM 응답 파싱 시도
                try:
                    interpretations = self._parse_cards_from_llm(llm_response, request)
                    summary = self._parse_summary_from_llm(llm_response)
                    lucky = self._parse_lucky_from_llm(llm_response)
                    logger.info("hwatu_reading_llm_success", question=request.question)
                    use_fallback = False
                except (KeyError, ValueError, TypeError) as e:
                    logger.warning(
                        "hwatu_reading_llm_parse_failed_fallback",
                        error=str(e),
                        question=request.question,
                    )

            if use_fallback:
                # LLM 호출 실패 또는 파싱 실패 시 폴백
                logger.info("hwatu_reading_using_fallback", question=request.question)
                interpretations = await self._generate_interpretations(request)
                summary = await self._generate_summary(request, interpretations)
                lucky = await self._generate_lucky(request)

            # 메타 정보 생성
            meta = HwatuReadingMeta(
                model="card-v1",
                generated_at=datetime.now(UTC),
            )

            response = HwatuReadingResponse(
                meta=meta,
                cards=interpretations,
                summary=summary,
                lucky=lucky,
            )

            logger.info("hwatu_reading_complete", question=request.question)
            return response

        except Exception as e:
            logger.error("hwatu_reading_error", error=str(e), exc_info=True)
            raise HwatuServiceError(f"화투점 리딩 생성 중 오류 발생: {str(e)}") from e

    async def _generate_interpretations(
        self, request: HwatuReadingRequest
    ) -> list[HwatuCardInterpretation]:
        """카드별 해석 생성 (폴백용 더미)

        Args:
            request: 화투점 리딩 요청

        Returns:
            카드 해석 목록 (4장)
        """
        # position 숫자 → 한글 레이블
        position_labels = {
            1: "본인/현재",
            2: "상대/환경",
            3: "과정/관계",
            4: "결과/조언",
        }

        interpretations = []

        for card_input in request.cards:
            card_info = get_card_by_code(card_input.card_code)

            # 더미 해석 생성
            interpretation = (
                f"{card_info.name_ko} 카드가 나왔습니다. "
                f"{card_info.fortune_meaning} "
                f"키워드: {', '.join(card_info.keywords[:2])}"
            )

            interpretations.append(
                HwatuCardInterpretation(
                    position=card_input.position,
                    position_label=position_labels.get(card_input.position, ""),
                    card_code=card_input.card_code,
                    card_name=card_info.name_ko,
                    card_type=card_info.card_type.label_ko,
                    card_month=card_info.month.value,
                    keywords=card_info.keywords[:3],
                    is_reversed=card_input.is_reversed,
                    interpretation=interpretation,
                )
            )

        return interpretations

    async def _generate_summary(
        self,
        request: HwatuReadingRequest,
        interpretations: list[HwatuCardInterpretation],
    ) -> HwatuReadingSummary:
        """종합 요약 생성 (폴백용 더미)

        Args:
            request: 화투점 리딩 요청
            interpretations: 카드 해석 목록

        Returns:
            종합 요약 객체
        """
        return HwatuReadingSummary(
            overall_theme="안정적 흐름",
            flow_analysis="전체적으로 큰 승부보다 리스크를 줄이고 흐름을 정리하는 선택이 유리합니다.",
            advice="현재 상황을 유지하며 점진적으로 개선하세요.",
        )

    async def _generate_lucky(
        self,
        request: HwatuReadingRequest,
    ) -> HwatuLucky:
        """행운 정보 생성 (폴백용 더미)

        Args:
            request: 화투점 리딩 요청

        Returns:
            행운 정보 객체
        """
        return HwatuLucky(
            color="빨강",
            number="7",
            direction="동",
            timing=None,
        )

    async def _call_llm(
        self,
        request: HwatuReadingRequest,
        prompt_version: PromptVersion = PromptVersion.STANDARD,
    ) -> dict[str, Any] | None:
        """LLM 호출하여 전체 리딩 생성

        Args:
            request: 화투점 리딩 요청

        Returns:
            파싱된 JSON dict 또는 None (실패 시)
        """
        if not self._client:
            logger.warning("hwatu_llm_client_not_initialized")
            return None

        # 프롬프트 생성
        prompt = self._build_prompt(request, prompt_version=prompt_version)
        messages = [
            {"role": "system", "content": HWATU_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        # LLM 설정 - 화투 리딩용
        # NOTE: 출력 JSON이 ~1200 토큰이므로 1500 필요
        config = GenerationConfig(
            max_tokens=1500,
            temperature=0.7,
            top_p=0.9,
        )

        try:
            logger.info("hwatu_llm_call_start", question=request.question)

            # LLM 호출
            response = await self._client.chat(messages, config)
            content = response.text

            logger.info(
                "hwatu_llm_call_complete",
                question=request.question,
                content_length=len(content),
            )

            # JSON 추출 - 첫 번째 { 위치 찾기
            json_start = content.find("{")
            if json_start == -1:
                logger.warning("hwatu_json_not_found", content_preview=content[:200])
                return None

            # raw_decode로 첫 번째 JSON 객체만 파싱 (뒤 텍스트 무시)
            try:
                decoder = json.JSONDecoder()
                parsed, _ = decoder.raw_decode(content[json_start:])
                logger.info("hwatu_json_parse_success", question=request.question)
                return parsed
            except json.JSONDecodeError as e:
                # 중첩 객체 문제일 경우 brace 카운팅으로 재시도
                logger.debug("hwatu_json_raw_decode_failed", error=str(e))
                brace_count = 0
                end_idx = json_start
                for i, char in enumerate(content[json_start:]):
                    if char == "{":
                        brace_count += 1
                    elif char == "}":
                        brace_count -= 1
                        if brace_count == 0:
                            end_idx = json_start + i + 1
                            break

                if end_idx > json_start:
                    json_str = content[json_start:end_idx]
                    parsed = json.loads(json_str)
                    logger.info("hwatu_json_parse_success_brace", question=request.question)
                    return parsed

                logger.warning(
                    "hwatu_json_parse_failed", error=str(e), content_preview=content[:200]
                )
                return None

        except json.JSONDecodeError as e:
            logger.warning("hwatu_json_parse_failed", error=str(e), content_preview=content[:200])
            return None
        except Exception as e:
            logger.warning("hwatu_llm_call_failed", error=str(e), error_type=type(e).__name__)
            return None

    def _build_prompt(
        self,
        request: HwatuReadingRequest,
        prompt_version: PromptVersion = PromptVersion.STANDARD,
    ) -> str:
        """사용자 프롬프트 생성

        Args:
            request: 화투점 리딩 요청

        Returns:
            생성된 프롬프트
        """
        # position 숫자 → 문자열 매핑
        num_to_position = {
            1: "SELF",
            2: "OTHER",
            3: "PROCESS",
            4: "RESULT",
        }

        # card_code → 카드 정보로 변환
        cards = []
        for card in request.cards:
            card_info = get_card_by_code(card.card_code)
            cards.append(
                {
                    "position": num_to_position.get(card.position, str(card.position)),
                    "card_code": card.card_code,
                    "card_name": card_info.name_ko,
                    "card_type": card_info.card_type.label_ko,
                }
            )

        # PromptVersion → bool 변환 (프롬프트 빌더 호환)
        use_lite = prompt_version == PromptVersion.LITE
        return build_hwatu_reading_prompt(cards, request.question, lite=use_lite)

    def _parse_cards_from_llm(
        self,
        llm_response: dict[str, Any],
        request: HwatuReadingRequest,
    ) -> list[HwatuCardInterpretation]:
        """LLM 응답에서 카드 해석 추출

        Args:
            llm_response: LLM JSON 응답
            request: 원본 요청 (폴백용)

        Returns:
            카드 해석 목록
        """
        # LLM position 문자열 → 숫자 매핑
        position_to_num = {
            "SELF": 1,
            "OTHER": 2,
            "PROCESS": 3,
            "RESULT": 4,
        }

        # position 숫자 → 한글 레이블
        position_labels = {
            1: "본인/현재",
            2: "상대/환경",
            3: "과정/관계",
            4: "결과/조언",
        }

        try:
            cards_data = llm_response.get("cards", [])
            if len(cards_data) != 4:
                logger.warning("hwatu_invalid_cards_count", count=len(cards_data))
                raise ValueError("카드 개수가 4개가 아닙니다")

            interpretations = []
            for card_data in cards_data:
                raw_position = card_data["position"]
                interpretation = card_data["interpretation"]

                # position 변환: 문자열이면 숫자로, 숫자면 그대로
                if isinstance(raw_position, str):
                    position = position_to_num.get(raw_position, raw_position)
                else:
                    position = raw_position

                # 요청에서 해당 position의 card_code와 is_reversed 가져오기
                request_card = next((c for c in request.cards if c.position == position), None)
                if not request_card:
                    raise ValueError(f"position {position}에 해당하는 요청 카드가 없습니다")

                # 카드 정보 조회
                card_info = get_card_by_code(request_card.card_code)

                # LLM 응답에서 새 필드 추출 (없으면 카드 정보에서 가져오기)
                position_label = card_data.get("position_label", position_labels.get(position, ""))
                card_name = card_data.get("card_name", card_info.name_ko)
                card_type = card_data.get("card_type", card_info.card_type.label_ko)
                keywords = card_data.get("keywords", card_info.keywords[:3])

                interpretations.append(
                    HwatuCardInterpretation(
                        position=position,
                        position_label=position_label,
                        card_code=request_card.card_code,
                        card_name=card_name,
                        card_type=card_type,
                        card_month=card_info.month.value,
                        keywords=keywords,
                        is_reversed=request_card.is_reversed,
                        interpretation=interpretation,
                    )
                )

            return interpretations

        except (KeyError, ValueError, TypeError) as e:
            logger.warning("hwatu_parse_cards_failed", error=str(e))
            raise

    def _parse_summary_from_llm(self, llm_response: dict[str, Any]) -> HwatuReadingSummary:
        """LLM 응답에서 종합 요약 추출

        Args:
            llm_response: LLM JSON 응답

        Returns:
            종합 요약 객체
        """
        try:
            summary = llm_response.get("summary", {})
            return HwatuReadingSummary(
                overall_theme=summary.get("overall_theme", ""),
                flow_analysis=summary.get("flow_analysis", ""),
                advice=summary.get("advice", ""),
            )

        except (KeyError, ValueError, TypeError) as e:
            logger.warning("hwatu_parse_summary_failed", error=str(e))
            raise

    def _parse_lucky_from_llm(self, llm_response: dict[str, Any]) -> HwatuLucky:
        """LLM 응답에서 행운 정보 추출

        Args:
            llm_response: LLM JSON 응답

        Returns:
            행운 정보 객체
        """
        try:
            lucky = llm_response.get("lucky", {})
            # number는 LLM이 int로 반환할 수 있으므로 str로 변환
            number_value = lucky.get("number", "7")
            return HwatuLucky(
                color=lucky.get("color", "빨강"),
                number=str(number_value) if number_value is not None else "7",
                direction=lucky.get("direction", "동"),
                timing=lucky.get("timing"),
            )

        except (KeyError, ValueError, TypeError) as e:
            logger.warning("hwatu_parse_lucky_failed", error=str(e))
            raise

    def get_full_deck(self) -> list[dict[str, Any]]:
        """48장 화투 카드 전체 목록 반환

        Returns:
            카드 목록 (48장)
        """
        deck = []

        for code, card in HWATU_CARDS.items():
            deck.append(
                {
                    "code": code,
                    "month": card.month.value,
                    "month_ko": card.month.label_ko,
                    "month_en": card.month.label_en,
                    "card_type": card.card_type.value,
                    "card_type_ko": card.card_type.label_ko,
                    "name_ko": card.name_ko,
                    "name_en": card.name_en,
                    "fortune_meaning": card.fortune_meaning,
                    "keywords": card.keywords,
                }
            )

        return deck

    # ============================================================
    # 분할 API 메서드 (병렬 호출용)
    # ============================================================

    async def generate_single_card_reading(
        self,
        card_code: int,
        position: int,
        question: str,
    ) -> dict[str, Any]:
        """카드 1장 해석 생성 (병렬 호출용)

        Args:
            card_code: 카드 코드 (0~47)
            position: 위치 (1~4)
            question: 질문

        Returns:
            카드 해석 결과
        """
        if not self._initialized:
            await self.initialize()

        # 카드 정보 조회
        card_info = get_card_by_code(card_code)
        position_labels = {
            1: "본인/현재",
            2: "상대/환경",
            3: "과정/관계",
            4: "결과/조언",
        }

        logger.info(
            "hwatu_single_card_start",
            card_code=card_code,
            position=position,
            question=question[:50],
        )

        # 간단한 프롬프트로 1장만 해석
        prompt = self._build_single_card_prompt(card_code, position, question)
        messages = [
            {"role": "system", "content": HWATU_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        config = GenerationConfig(
            max_tokens=700,  # 1장 상세 해석 (300-500자 + JSON 오버헤드)
            temperature=0.7,
            top_p=0.9,
        )

        try:
            response = await self._client.chat(messages, config)
            content = response.text

            # JSON 파싱
            json_start = content.find("{")
            if json_start != -1:
                decoder = json.JSONDecoder()
                parsed, _ = decoder.raw_decode(content[json_start:])

                return {
                    "position": position,
                    "position_label": position_labels.get(position, ""),
                    "card_code": card_code,
                    "card_name": card_info.name_ko,
                    "card_type": card_info.card_type.label_ko,
                    "card_month": card_info.month.value,
                    "keywords": parsed.get("keywords", card_info.keywords[:3]),
                    "interpretation": parsed.get("interpretation", ""),
                }
        except Exception as e:
            logger.warning("hwatu_single_card_llm_failed", error=str(e))

        # 폴백
        return {
            "position": position,
            "position_label": position_labels.get(position, ""),
            "card_code": card_code,
            "card_name": card_info.name_ko,
            "card_type": card_info.card_type.label_ko,
            "card_month": card_info.month.value,
            "keywords": card_info.keywords[:3],
            "interpretation": f"{card_info.name_ko}: {card_info.fortune_meaning}",
        }

    def _build_single_card_prompt(
        self,
        card_code: int,
        position: int,
        question: str,
    ) -> str:
        """1장 카드 해석용 프롬프트 생성 (원본 프롬프트 품질 유지)"""
        card_info = get_card_by_code(card_code)

        # 위치별 상세 해석 가이드
        position_guides = {
            1: {
                "code": "SELF",
                "label": "본인/현재 상태",
                "guide": "질문자의 현재 내면 상태, 마음가짐, 심리를 해석",
            },
            2: {
                "code": "OTHER",
                "label": "상대/환경",
                "guide": "상대방 또는 주변 환경의 영향, 외부 상황을 해석",
            },
            3: {
                "code": "PROCESS",
                "label": "과정/관계",
                "guide": "현재 진행되는 과정, 관계의 흐름을 해석",
            },
            4: {
                "code": "RESULT",
                "label": "결과/조언",
                "guide": "최종 결과와 실천 가능한 조언을 제시",
            },
        }

        # 카드 등급별 의미
        card_type_meanings = {
            "광": "결정적 사건, 강한 운세, 중요한 전환점",
            "열끗": "현실적 상황, 실속, 구체적 성과",
            "띠": "약속, 인간관계, 소통, 말",
            "피": "감정 소모, 낭비, 작은 일들",
        }

        pos_info = position_guides.get(position, {
            "code": "UNKNOWN",
            "label": "알 수 없음",
            "guide": "카드를 해석",
        })
        card_type_meaning = card_type_meanings.get(
            card_info.card_type.label_ko, "일반적 상황"
        )

        return f"""다음 화투 카드 1장을 해석해주세요.

## 질문
{question}

## 카드 정보
- 카드: {card_info.name_ko}
- 월: {card_info.month.value}월 ({card_info.month.label_ko})
- 등급: {card_info.card_type.label_ko}
- 등급 의미: {card_type_meaning}

## 위치
- 위치: {pos_info['label']}
- 해석 방향: {pos_info['guide']}

<constraints>
## 출력 규칙
1. keywords: 이 카드와 위치에 맞는 키워드 2-4개
2. interpretation: 300-500자의 상세한 해석
   - 카드의 상징과 월별 의미 반영
   - 위치(본인/상대/과정/결과)에 맞는 관점으로 해석
   - 질문과 연결하여 구체적으로 설명
   - 따뜻하고 친근한 말투 (~이네요, ~랍니다, ~보입니다)
</constraints>

JSON만 출력하세요:
{{"keywords": ["키워드1", "키워드2", "키워드3"], "interpretation": "300-500자 해석"}}
"""

    async def generate_summary_only(
        self,
        question: str,
        card_interpretations: list[dict],
    ) -> dict[str, Any]:
        """4장 종합 요약만 생성 (카드 해석 완료 후 호출)

        Args:
            question: 질문
            card_interpretations: 4장 카드 해석 결과

        Returns:
            종합 요약 + 행운 정보
        """
        if not self._initialized:
            await self.initialize()

        logger.info("hwatu_summary_start", question=question[:50])

        # 요약용 프롬프트
        prompt = self._build_summary_prompt(question, card_interpretations)
        messages = [
            {"role": "system", "content": HWATU_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        config = GenerationConfig(
            max_tokens=500,
            temperature=0.7,
            top_p=0.9,
        )

        try:
            response = await self._client.chat(messages, config)
            content = response.text

            json_start = content.find("{")
            if json_start != -1:
                decoder = json.JSONDecoder()
                parsed, _ = decoder.raw_decode(content[json_start:])

                return {
                    "overall_theme": parsed.get("overall_theme", ""),
                    "flow_analysis": parsed.get("flow_analysis", ""),
                    "advice": parsed.get("advice", ""),
                    "lucky": parsed.get("lucky", {
                        "color": "빨강",
                        "number": "7",
                        "direction": "동",
                        "timing": None,
                    }),
                }
        except Exception as e:
            logger.warning("hwatu_summary_llm_failed", error=str(e))

        # 폴백
        return {
            "overall_theme": "안정적 흐름",
            "flow_analysis": "전체적으로 큰 승부보다 리스크를 줄이고 흐름을 정리하는 선택이 유리합니다.",
            "advice": "현재 상황을 유지하며 점진적으로 개선하세요.",
            "lucky": {
                "color": "빨강",
                "number": "7",
                "direction": "동",
                "timing": None,
            },
        }

    def _build_summary_prompt(
        self,
        question: str,
        card_interpretations: list[dict],
    ) -> str:
        """종합 요약용 프롬프트 생성"""
        cards_text = "\n".join([
            f"- {c['position']}번 ({c.get('card_name', '')}): {c.get('interpretation', '')[:100]}..."
            for c in sorted(card_interpretations, key=lambda x: x.get('position', 0))
        ])

        return f"""질문: {question}

4장 카드 해석:
{cards_text}

위 4장을 종합하여 전체 운세를 요약하세요. JSON 형식으로 응답:
{{
  "overall_theme": "전체 주제 (1문장)",
  "flow_analysis": "1→2→3→4 흐름 분석 (150-200자)",
  "advice": "실행 가능한 조언 (1-2문장)",
  "lucky": {{"color": "행운의 색", "number": "숫자", "direction": "방향", "timing": "시간대"}}
}}
"""
