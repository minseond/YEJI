"""타로 리딩 서비스

3장 스프레드 타로 리딩 생성
"""

import json
from typing import Any

import structlog

from yeji_ai.clients.vllm_client import GenerationConfig, VLLMClient
from yeji_ai.models.enums import (
    CardOrientation,
    CommonBadge,
    MajorArcana,
    MinorRank,
    MinorSuit,
    SpreadPosition,
    TarotBadge,
)
from yeji_ai.models.fortune.tarot import (
    CardInterpretation,
    TarotCardInput,
    TarotLucky,
    TarotReadingRequest,
    TarotReadingResponse,
    TarotReadingSummary,
)
from yeji_ai.prompts.tarot_prompts import TAROT_SYSTEM_PROMPT, build_tarot_reading_prompt

logger = structlog.get_logger()


class TarotServiceError(Exception):
    """타로 서비스 에러"""

    def __init__(self, message: str, error_code: str = "TAROT_ERROR"):
        super().__init__(message)
        self.message = message
        self.error_code = error_code


class TarotService:
    """타로 리딩 서비스

    3장 스프레드 타로 리딩 생성 및 해석
    """

    def __init__(self):
        """서비스 초기화"""
        self._initialized = False
        self._client: VLLMClient | None = None

    async def initialize(self):
        """서비스 비동기 초기화"""
        if self._initialized:
            return

        logger.info("tarot_service_initializing")
        self._client = VLLMClient()
        self._initialized = True
        logger.info("tarot_service_initialized")

    async def generate_reading(self, request: TarotReadingRequest) -> TarotReadingResponse:
        """타로 리딩 생성

        Args:
            request: 타로 리딩 요청 (질문 + 3장 카드)

        Returns:
            타로 리딩 응답 (해석 + 종합 + 행운)

        Raises:
            TarotServiceError: 서비스 오류 발생 시
        """
        if not self._initialized:
            await self.initialize()

        logger.info(
            "tarot_reading_start",
            question=request.question.value,
            card_count=len(request.cards),
        )

        try:
            # LLM 호출 시도
            llm_response = await self._call_llm(request)

            use_fallback = True

            if llm_response:
                # LLM 응답 파싱 시도
                try:
                    interpretations = self._parse_cards_from_llm(llm_response, request)
                    summary = self._parse_summary_from_llm(llm_response)
                    lucky = self._parse_lucky_from_llm(llm_response)
                    logger.info("tarot_reading_llm_success", question=request.question.value)
                    use_fallback = False
                except (KeyError, ValueError, TypeError) as e:
                    logger.warning(
                        "tarot_reading_llm_parse_failed_fallback",
                        error=str(e),
                        question=request.question.value,
                    )

            if use_fallback:
                # LLM 호출 실패 또는 파싱 실패 시 폴백
                logger.info("tarot_reading_using_fallback", question=request.question.value)
                interpretations = await self._generate_interpretations(request)
                summary = await self._generate_summary(request, interpretations)
                lucky = await self._generate_lucky(request)

            # 배지 생성
            badges = self._generate_badges(request)

            response = TarotReadingResponse(
                category="tarot",
                spread_type="THREE_CARD",
                question=request.question,
                cards=interpretations,
                summary=summary,
                lucky=lucky,
                badges=badges,
            )

            logger.info("tarot_reading_complete", question=request.question.value)
            return response

        except Exception as e:
            logger.error("tarot_reading_error", error=str(e), exc_info=True)
            raise TarotServiceError(f"타로 리딩 생성 중 오류 발생: {str(e)}") from e

    async def _generate_interpretations(
        self, request: TarotReadingRequest
    ) -> list[CardInterpretation]:
        """카드별 해석 생성

        Args:
            request: 타로 리딩 요청

        Returns:
            카드 해석 목록 (3장)
        """
        interpretations = []

        for spread_card in request.cards:
            card = spread_card.card
            position = spread_card.position

            # 카드 코드 및 이름 추출
            card_code = self._get_card_code(card)
            card_name = card.card_name_ko

            # TODO: LLM 호출로 키워드 및 해석 생성
            # 임시 더미 데이터
            keywords = self._get_dummy_keywords(card)
            interpretation = self._get_dummy_interpretation(card, position)

            interpretations.append(
                CardInterpretation(
                    position=position,
                    position_label=position.label_ko,
                    card_code=card_code,
                    card_name=card_name,
                    orientation=card.orientation,
                    orientation_label=card.orientation.label_ko,
                    keywords=keywords,
                    interpretation=interpretation,
                )
            )

        return interpretations

    async def _generate_summary(
        self,
        request: TarotReadingRequest,
        interpretations: list[CardInterpretation],
    ) -> TarotReadingSummary:
        """종합 해석 생성

        Args:
            request: 타로 리딩 요청
            interpretations: 카드 해석 목록

        Returns:
            종합 해석
        """
        # TODO: LLM 호출로 종합 해석 생성
        # 임시 더미 데이터
        return TarotReadingSummary(
            overall_theme="새로운 시작과 변화의 흐름",
            past_to_present="과거의 경험이 현재의 상황을 만들었습니다.",
            present_to_future="현재의 선택이 미래의 결과를 결정할 것입니다.",
            advice="마음을 열고 변화를 받아들이세요.",
        )

    async def _generate_lucky(self, request: TarotReadingRequest) -> TarotLucky:
        """행운 정보 생성

        Args:
            request: 타로 리딩 요청

        Returns:
            행운 정보
        """
        # TODO: 카드 기반 행운 정보 생성 로직
        # 임시 더미 데이터
        return TarotLucky(
            color="흰색",
            number="0",
            element="공기",
            timing="새벽",
        )

    def _generate_badges(self, request: TarotReadingRequest) -> list[TarotBadge | CommonBadge]:
        """배지 생성

        Args:
            request: 타로 리딩 요청

        Returns:
            배지 목록
        """
        badges: list[TarotBadge | CommonBadge] = []

        # 메이저 아르카나 카드 수 계산
        major_count = sum(1 for card in request.cards if card.card.major is not None)
        if major_count >= 2:
            badges.append(TarotBadge.MAJOR_ARCANA_HEAVY)

        # 방향 검사
        orientations = {card.card.orientation for card in request.cards}
        if len(orientations) == 1:
            if CardOrientation.UPRIGHT in orientations:
                badges.append(TarotBadge.ALL_UPRIGHT)
            else:
                badges.append(TarotBadge.ALL_REVERSED)
        else:
            badges.append(TarotBadge.MIXED_ORIENTATION)

        # 수트 우세 검사 (마이너 카드만)
        suit_counts: dict[str, int] = {}
        for card in request.cards:
            if card.card.suit:
                element = card.card.suit.element
                suit_counts[element] = suit_counts.get(element, 0) + 1

        if suit_counts:
            max_element = max(suit_counts, key=suit_counts.get)  # type: ignore
            if suit_counts[max_element] >= 2:
                badge_map = {
                    "FIRE": TarotBadge.FIRE_DOMINANT,
                    "WATER": TarotBadge.WATER_DOMINANT,
                    "AIR": TarotBadge.AIR_DOMINANT,
                    "EARTH": TarotBadge.EARTH_DOMINANT,
                }
                if max_element in badge_map:
                    badges.append(badge_map[max_element])

        # 코트 카드 검사
        has_court = any(card.card.rank and card.card.rank.is_court for card in request.cards)
        if has_court:
            badges.append(TarotBadge.COURT_CARDS)

        return badges

    def _get_card_code(self, card: TarotCardInput) -> str:
        """카드 코드 생성

        Args:
            card: 타로 카드 입력

        Returns:
            카드 코드 (FOOL, CUPS_ACE 등)
        """
        if card.major:
            return card.major.value
        elif card.suit and card.rank:
            return f"{card.suit.value}_{card.rank.value}"
        return "UNKNOWN"

    def _get_dummy_keywords(self, card: TarotCardInput) -> list[str]:
        """더미 키워드 생성 (임시)

        Args:
            card: 타로 카드 입력

        Returns:
            키워드 목록
        """
        if card.major == MajorArcana.FOOL:
            return ["새로운 시작", "순수함", "모험"]
        elif card.major == MajorArcana.LOVERS:
            return ["사랑", "선택", "조화"]
        elif card.suit == MinorSuit.CUPS and card.rank == MinorRank.ACE:
            return ["감정", "새로운 관계", "직관"]
        else:
            return ["변화", "성장", "기회"]

    def _get_dummy_interpretation(self, card: TarotCardInput, position: SpreadPosition) -> str:
        """더미 해석 생성 (임시)

        Args:
            card: 타로 카드 입력
            position: 스프레드 위치

        Returns:
            해석 내용
        """
        position_text = position.label_ko
        card_name = card.card_name_ko

        if card.orientation == CardOrientation.UPRIGHT:
            return f"{position_text}에 {card_name} 카드가 정방향으로 나타났습니다. 긍정적인 에너지가 흐르고 있습니다."
        else:
            return f"{position_text}에 {card_name} 카드가 역방향으로 나타났습니다. 주의가 필요한 시기입니다."

    async def _call_llm(self, request: TarotReadingRequest) -> dict[str, Any] | None:
        """LLM 호출하여 전체 리딩 생성

        Args:
            request: 타로 리딩 요청

        Returns:
            파싱된 JSON dict 또는 None (실패 시)
        """
        if not self._client:
            logger.warning("tarot_llm_client_not_initialized")
            return None

        # 카드 데이터 준비
        cards_data = [
            {
                "position": c.position.value,
                "card_code": self._get_card_code(c.card),
                "card_name": c.card.card_name_ko,
                "orientation": c.card.orientation.value,
            }
            for c in request.cards
        ]

        # 프롬프트 생성
        prompt = build_tarot_reading_prompt(cards_data, request.question.label_ko)
        messages = [
            {"role": "system", "content": TAROT_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        # LLM 설정
        config = GenerationConfig(
            max_tokens=1500,
            temperature=0.7,
            top_p=0.9,
        )

        try:
            logger.info("tarot_llm_call_start", question=request.question.value)

            # LLM 호출
            response = await self._client.chat(messages, config)
            content = response.text

            logger.info(
                "tarot_llm_call_complete",
                question=request.question.value,
                content_length=len(content),
            )

            # JSON 추출 - 첫 번째 { 위치 찾기
            json_start = content.find("{")
            if json_start == -1:
                logger.warning("tarot_json_not_found", content_preview=content[:200])
                return None

            # raw_decode로 첫 번째 JSON 객체만 파싱 (뒤 텍스트 무시)
            try:
                decoder = json.JSONDecoder()
                parsed, _ = decoder.raw_decode(content[json_start:])
                logger.info("tarot_json_parse_success", question=request.question.value)
                return parsed
            except json.JSONDecodeError as e:
                # 중첩 객체 문제일 경우 brace 카운팅으로 재시도
                logger.debug("tarot_json_raw_decode_failed", error=str(e))
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
                    logger.info("tarot_json_parse_success_brace", question=request.question.value)
                    return parsed

                logger.warning("tarot_json_parse_failed", error=str(e), content_preview=content[:200])
                return None

        except json.JSONDecodeError as e:
            logger.warning("tarot_json_parse_failed", error=str(e), content_preview=content[:200])
            return None
        except Exception as e:
            logger.warning("tarot_llm_call_failed", error=str(e), error_type=type(e).__name__)
            return None

    def _parse_cards_from_llm(
        self,
        llm_response: dict[str, Any],
        request: TarotReadingRequest,
    ) -> list[CardInterpretation]:
        """LLM 응답에서 카드 해석 추출

        Args:
            llm_response: LLM JSON 응답
            request: 원본 요청 (폴백용)

        Returns:
            카드 해석 목록
        """
        try:
            cards_data = llm_response.get("cards", [])
            if len(cards_data) != 3:
                logger.warning("tarot_invalid_cards_count", count=len(cards_data))
                raise ValueError("카드 개수가 3개가 아닙니다")

            interpretations = []
            for card_data in cards_data:
                interpretations.append(
                    CardInterpretation(
                        position=SpreadPosition(card_data["position"]),
                        position_label=card_data["position_label"],
                        card_code=card_data["card_code"],
                        card_name=card_data["card_name"],
                        orientation=CardOrientation(card_data["orientation"]),
                        orientation_label=card_data["orientation_label"],
                        keywords=card_data["keywords"],
                        interpretation=card_data["interpretation"],
                    )
                )

            return interpretations

        except (KeyError, ValueError, TypeError) as e:
            logger.warning("tarot_parse_cards_failed", error=str(e))
            # 폴백: 더미 데이터 사용
            raise

    def _parse_summary_from_llm(self, llm_response: dict[str, Any]) -> TarotReadingSummary:
        """LLM 응답에서 종합 해석 추출

        Args:
            llm_response: LLM JSON 응답

        Returns:
            종합 해석
        """
        try:
            summary_data = llm_response.get("summary", {})
            return TarotReadingSummary(
                overall_theme=summary_data["overall_theme"],
                past_to_present=summary_data["past_to_present"],
                present_to_future=summary_data["present_to_future"],
                advice=summary_data["advice"],
            )

        except (KeyError, ValueError, TypeError) as e:
            logger.warning("tarot_parse_summary_failed", error=str(e))
            # 폴백: 더미 데이터
            raise

    def _parse_lucky_from_llm(self, llm_response: dict[str, Any]) -> TarotLucky:
        """LLM 응답에서 행운 정보 추출

        Args:
            llm_response: LLM JSON 응답

        Returns:
            행운 정보
        """
        try:
            lucky_data = llm_response.get("lucky", {})
            return TarotLucky(
                color=lucky_data["color"],
                number=lucky_data["number"],
                element=lucky_data["element"],
                timing=lucky_data["timing"],
            )

        except (KeyError, ValueError, TypeError) as e:
            logger.warning("tarot_parse_lucky_failed", error=str(e))
            # 폴백: 더미 데이터
            raise

    def get_full_deck(self) -> list[dict[str, Any]]:
        """78장 타로 카드 전체 목록 반환

        Returns:
            카드 목록 (메이저 22장 + 마이너 56장)
        """
        deck = []

        # 메이저 아르카나 22장
        for major in MajorArcana:
            deck.append(
                {
                    "type": "major",
                    "code": major.value,
                    "number": major.number,
                    "name_ko": major.label_ko,
                    "name_en": major.label_en,
                }
            )

        # 마이너 아르카나 56장 (4 suits × 14 ranks)
        for suit in MinorSuit:
            for rank in MinorRank:
                code = f"{suit.value}_{rank.value}"
                name_ko = f"{suit.label_ko} {rank.label_ko}"
                name_en = f"{rank.value} of {suit.value}"

                deck.append(
                    {
                        "type": "minor",
                        "code": code,
                        "suit": suit.value,
                        "suit_ko": suit.label_ko,
                        "rank": rank.value,
                        "rank_ko": rank.label_ko,
                        "name_ko": name_ko,
                        "name_en": name_en,
                        "element": suit.element,
                        "is_court": rank.is_court,
                    }
                )

        return deck
