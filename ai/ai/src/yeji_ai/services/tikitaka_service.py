"""티키타카 대화 서비스

소이설(동양)과 스텔라(서양) 캐릭터의 대화형 운세 해석 서비스
"""

import asyncio
import json
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime
from pathlib import Path

import structlog

from yeji_ai.clients.redis_client import (
    cache_fortune,
    get_cached_fortune,
    get_session_from_redis,
    record_token_usage,
    save_session_to_redis,
)

# GPT-5-mini Provider 및 버블 파서 임포트
from yeji_ai.config import get_settings
from yeji_ai.models.fortune.chat import (
    CharacterCode,
    ChatDebateStatus,
    ChatMessage,
    ChatUIHints,
    ChoiceOption,
    FortuneCategory,
    MessageType,
)
from yeji_ai.models.fortune.eastern import EasternFortuneRequest, EasternFortuneResponse
from yeji_ai.models.fortune.western import WesternFortuneRequest
from yeji_ai.models.user_fortune import WesternFortuneDataV2
from yeji_ai.prompts.gpt5mini_prompts import (
    build_gpt5mini_tikitaka_prompt,
)
from yeji_ai.prompts.tikitaka_prompts import CHARACTER_NAMES
from yeji_ai.providers.base import GenerationConfig
from yeji_ai.providers.openai import OpenAIConfig, OpenAIProvider
from yeji_ai.providers.vllm import VLLMConfig, VLLMProvider
from yeji_ai.services.eastern_fortune_service import EasternFortuneService
from yeji_ai.services.llm_interpreter import LLMInterpreter
from yeji_ai.services.postprocessor import filter_noise, fix_brackets
from yeji_ai.services.postprocessor.prompt_leak_filter import filter_prompt_leak
from yeji_ai.services.western_fortune_service import WesternFortuneService

# 버블 파서는 try/except로 감싸서 import (Worker 1 완료 전까지 없을 수 있음)
try:
    from yeji_ai.services.parsers.bubble_parser import BubbleParser, ParsedBubble

    BUBBLE_PARSER_AVAILABLE = True
except ImportError:
    BUBBLE_PARSER_AVAILABLE = False
    BubbleParser = None
    ParsedBubble = None

logger = structlog.get_logger()

# 멀티 버블 시스템 프롬프트
MULTI_BUBBLE_SYSTEM_PROMPT = """당신은 티키타카 운세 대화 시스템입니다.
응답은 반드시 다음 XML 형식으로 작성하세요:

<tikitaka>
<bubble character="SOISEOL" emotion="HAPPY" type="INTERPRETATION">
소이설의 메시지
</bubble>
<bubble character="STELLA" emotion="THOUGHTFUL" type="INTERPRETATION">
스텔라의 메시지
</bubble>
</tikitaka>

character: SOISEOL(동양 운세), STELLA(서양 운세), SYSTEM(시스템)
emotion: NEUTRAL, HAPPY, CURIOUS, THOUGHTFUL, SURPRISED, CONCERNED,
        CONFIDENT, PLAYFUL, MYSTERIOUS, EMPATHETIC
type: GREETING, INFO_REQUEST, INTERPRETATION, DEBATE, CONSENSUS,
      QUESTION, CHOICE, SUMMARY, FAREWELL
"""


# ============================================================
# 헬퍼 함수
# ============================================================

class DotDict:
    """dict를 속성 접근 가능한 객체로 변환하는 래퍼

    LLM 응답(dict)을 EasternFortuneResponse처럼 .chart, .stats로 접근 가능하게 함
    """

    def __init__(self, data: dict):
        for key, value in data.items():
            if isinstance(value, dict):
                setattr(self, key, DotDict(value))
            elif isinstance(value, list):
                converted = [
                    DotDict(item) if isinstance(item, dict) else item
                    for item in value
                ]
                setattr(self, key, converted)
            else:
                setattr(self, key, value)

    def __getattr__(self, name: str):
        # 존재하지 않는 속성 접근 시 None 반환 (KeyError 방지)
        return None

    def get(self, key: str, default=None):
        return getattr(self, key, default)


def _safe_get_hangul(obj, default: str = "알수없음") -> str:
    """gan_code 등에서 안전하게 hangul 값 추출

    - enum 객체면 .hangul 속성 사용
    - 문자열 코드면 한글로 매핑
    - None이면 기본값 반환
    """
    # 천간 코드 → 한글 매핑
    CHEONGAN_HANGUL = {
        "GAP": "갑", "EUL": "을", "BYEONG": "병", "JEONG": "정", "MU": "무",
        "GI": "기", "GYEONG": "경", "SIN": "신", "IM": "임", "GYE": "계",
    }

    if obj is None:
        return default
    if isinstance(obj, str):
        # 영문 코드면 한글로 변환
        if obj.upper() in CHEONGAN_HANGUL:
            return CHEONGAN_HANGUL[obj.upper()]
        return obj
    if hasattr(obj, "hangul"):
        return obj.hangul
    if hasattr(obj, "value"):
        # value도 문자열 코드일 수 있음
        val = str(obj.value)
        if val.upper() in CHEONGAN_HANGUL:
            return CHEONGAN_HANGUL[val.upper()]
        return val
    return default


def _safe_get_label(obj, default: str = "알수없음") -> str:
    """element_code 등에서 안전하게 label_ko 값 추출

    - enum 객체면 .label_ko 속성 사용
    - 문자열 코드면 한글로 매핑
    - None이면 기본값 반환
    """
    # 오행 코드 → 한글 매핑
    ELEMENT_LABEL_KO = {
        "WOOD": "목", "FIRE": "화", "EARTH": "토", "METAL": "금", "WATER": "수",
    }

    if obj is None:
        return default
    if isinstance(obj, str):
        # 영문 코드면 한글로 변환
        if obj.upper() in ELEMENT_LABEL_KO:
            return ELEMENT_LABEL_KO[obj.upper()]
        return obj
    if hasattr(obj, "label_ko"):
        return obj.label_ko
    if hasattr(obj, "value"):
        # value도 문자열 코드일 수 있음
        val = str(obj.value)
        if val.upper() in ELEMENT_LABEL_KO:
            return ELEMENT_LABEL_KO[val.upper()]
        return val
    return default


class NormalizedEasternContext:
    """티키타카용 정규화된 동양 운세 컨텍스트

    LLM 응답(dict)이든 EasternFortuneResponse(모델)이든
    상관없이 일관된 인터페이스로 접근 가능하게 함
    """

    def __init__(self, data):
        """data: EasternFortuneResponse, DotDict, 또는 dict"""
        self._raw = data

        # element (대표 오행)
        self.element = self._get_attr("element", "알수없음")

        # chart 정보
        chart = self._get_attr("chart", {})
        self.chart_summary = self._nested_get(chart, "summary", "사주 분석 결과")

        # day pillar 정보
        day = self._nested_get(chart, "day", {})
        self.day_gan = _safe_get_hangul(self._nested_get(day, "gan_code"), "일간")
        self.day_gan_char = self._nested_get(day, "gan", "?")
        self.day_ji = self._nested_get(day, "ji", "?")
        self.day_element = _safe_get_label(self._nested_get(day, "element_code"), "오행")

        # year/month pillar
        year = self._nested_get(chart, "year", {})
        month = self._nested_get(chart, "month", {})
        self.year_gan = self._nested_get(year, "gan", "?")
        self.year_ji = self._nested_get(year, "ji", "?")
        self.month_gan = self._nested_get(month, "gan", "?")
        self.month_ji = self._nested_get(month, "ji", "?")

        # stats 정보
        stats = self._get_attr("stats", {})

        # 오행 분포
        five_elements = self._nested_get(stats, "five_elements", {})
        self.five_elements_summary = self._nested_get(five_elements, "summary", "오행 분석 중")
        self.five_elements_dominant = self._nested_get(five_elements, "dominant", "균형")

        # 음양 비율 (yin_yang 또는 yin_yang_ratio 둘 다 지원)
        yin_yang = (
            self._nested_get(stats, "yin_yang")
            or self._nested_get(stats, "yin_yang_ratio", {})
        )
        self.yang = self._nested_get(yin_yang, "yang", 50)
        self.yin = self._nested_get(yin_yang, "yin", 50)
        self.yin_yang_summary = self._nested_get(yin_yang, "summary", "음양 분석 중")

        # 십신
        ten_gods = self._nested_get(stats, "ten_gods", {})
        self.ten_gods_summary = self._nested_get(ten_gods, "summary", "십신 분석 중")

        # 강점/약점 (stats에 있거나 final_verdict에 있을 수 있음)
        final_verdict = self._get_attr("final_verdict", {})
        self.strength = (
            self._nested_get(stats, "strength")
            or self._nested_get(final_verdict, "strength")
            or "강점 분석 중"
        )
        self.weakness = (
            self._nested_get(stats, "weakness")
            or self._nested_get(final_verdict, "weakness")
            or "약점 분석 중"
        )
        self.summary = (
            self._nested_get(final_verdict, "summary")
            or self._get_attr("summary", "종합 분석 중")
        )
        self.advice = self._nested_get(final_verdict, "advice", "")

        # lucky 정보
        lucky = self._get_attr("lucky", {})
        self.lucky_color = self._nested_get(lucky, "color", "")
        self.lucky_number = self._nested_get(lucky, "number", "")
        self.lucky_item = self._nested_get(lucky, "item", "")

    def _get_attr(self, name: str, default=None):
        """속성/키 안전하게 가져오기"""
        if hasattr(self._raw, name):
            val = getattr(self._raw, name, default)
            return val if val is not None else default
        if isinstance(self._raw, dict):
            return self._raw.get(name, default)
        return default

    def _nested_get(self, obj, key: str, default=None):
        """중첩 객체에서 안전하게 값 가져오기"""
        if obj is None:
            return default
        if hasattr(obj, key):
            val = getattr(obj, key, default)
            return val if val is not None else default
        if isinstance(obj, dict):
            return obj.get(key, default)
        return default


class NormalizedWesternContext:
    """티키타카용 정규화된 서양 운세 컨텍스트"""

    def __init__(self, data):
        """data: WesternFortuneDataV2, DotDict, 또는 dict"""
        self._raw = data

        # element (대표 원소)
        self.element = self._get_attr("element", "알수없음")

        # stats 정보
        stats = self._get_attr("stats", {})

        # 태양 별자리
        main_sign = self._nested_get(stats, "main_sign", {})
        self.main_sign_name = self._nested_get(main_sign, "name", "알수없음")

        # 원소 분포
        self.element_summary = self._nested_get(stats, "element_summary", "원소 분석 중")

        # 양태 분포
        self.modality_summary = self._nested_get(stats, "modality_summary", "양태 분석 중")

        # 키워드
        self.keywords_summary = self._nested_get(stats, "keywords_summary", "키워드 분석 중")
        self.keywords = self._nested_get(stats, "keywords", [])

        # fortune_content
        fortune_content = self._get_attr("fortune_content", {})
        self.overview = self._nested_get(fortune_content, "overview", "운세 분석 중")
        self.advice = self._nested_get(fortune_content, "advice", "")

        # lucky 정보
        lucky = self._get_attr("lucky", {})
        self.lucky_color = self._nested_get(lucky, "color", "")
        self.lucky_number = self._nested_get(lucky, "number", "")

    def _get_attr(self, name: str, default=None):
        """속성/키 안전하게 가져오기"""
        if hasattr(self._raw, name):
            val = getattr(self._raw, name, default)
            return val if val is not None else default
        if isinstance(self._raw, dict):
            return self._raw.get(name, default)
        return default

    def _nested_get(self, obj, key: str, default=None):
        """중첩 객체에서 안전하게 값 가져오기"""
        if obj is None:
            return default
        if hasattr(obj, key):
            val = getattr(obj, key, default)
            return val if val is not None else default
        if isinstance(obj, dict):
            return obj.get(key, default)
        return default


def create_summarized_eastern_context(eastern_data) -> str:
    """동양 운세 데이터를 요약 컨텍스트로 변환 (토큰 80% 절감)

    Args:
        eastern_data: EasternFortuneResponse, dict, 또는 DotDict

    Returns:
        요약된 컨텍스트 문자열 (~100 토큰)
    """
    if not eastern_data:
        return ""

    ctx = NormalizedEasternContext(eastern_data)

    return f"""[동양 사주 요약]
일간: {ctx.day_gan} ({ctx.day_element})
사주: {ctx.year_gan}{ctx.year_ji}년 {ctx.month_gan}{ctx.month_ji}월 {ctx.day_gan_char}{ctx.day_ji}일
오행 분포: {ctx.five_elements_summary}
음양: 양 {ctx.yang}% / 음 {ctx.yin}%
십신: {ctx.ten_gods_summary}
강점: {ctx.strength}
약점: {ctx.weakness}
조언: {ctx.advice}"""


def _extract_keyword_label(kw) -> str:
    """키워드에서 label 추출 (WesternKeyword 객체 또는 dict 지원)

    Args:
        kw: WesternKeyword 객체, dict, 또는 str

    Returns:
        키워드 레이블 문자열
    """
    if hasattr(kw, "label"):
        return kw.label
    elif isinstance(kw, dict) and "label" in kw:
        return kw["label"]
    return str(kw)


def create_summarized_western_context(western_data) -> str:
    """서양 점성술 데이터를 요약 컨텍스트로 변환 (토큰 80% 절감)

    Args:
        western_data: WesternFortuneDataV2, dict, 또는 DotDict

    Returns:
        요약된 컨텍스트 문자열 (~100 토큰)
    """
    if not western_data:
        return ""

    ctx = NormalizedWesternContext(western_data)

    keywords_str = (
        ", ".join(_extract_keyword_label(kw) for kw in ctx.keywords[:5])
        if ctx.keywords
        else ctx.keywords_summary
    )

    return f"""[서양 점성술 요약]
태양 별자리: {ctx.main_sign_name}
원소: {ctx.element_summary}
양태: {ctx.modality_summary}
키워드: {keywords_str}
운세 개요: {ctx.overview}
조언: {ctx.advice}"""


def _get_suggested_question(category: FortuneCategory, turn: int, context: str = "") -> str:
    """턴에 맞는 질문 제안 생성

    Args:
        category: 운세 카테고리
        turn: 현재 턴 번호
        context: 추가 컨텍스트 (미사용)

    Returns:
        질문 제안 문자열
    """
    # 마지막 턴(3턴)에는 마무리 질문
    if turn >= 3:
        return "오늘 상담이 도움이 되셨나요?"

    # 카테고리별 기본 질문
    category_questions = {
        FortuneCategory.LOVE: [
            "연애에서 특히 궁금한 점이 있으신가요?",
            "이상형이나 연애 스타일에 대해 더 알고 싶으신가요?",
            "현재 관계에서 고민되는 부분이 있으신가요?",
        ],
        FortuneCategory.MONEY: [
            "재물운에서 더 알고 싶은 부분이 있으신가요?",
            "투자 적기나 재물 운용에 대해 궁금하신가요?",
            "올해 재물운의 흐름이 궁금하신가요?",
        ],
        FortuneCategory.CAREER: [
            "직장운에서 궁금한 점이 있으신가요?",
            "이직이나 승진에 대해 알고 싶으신가요?",
            "직장 내 관계에 대해 조언이 필요하신가요?",
        ],
        FortuneCategory.HEALTH: [
            "건강운에서 더 알고 싶은 부분이 있으신가요?",
            "주의해야 할 건강 습관이 궁금하신가요?",
            "올해 건강 관리 방향이 궁금하신가요?",
        ],
        FortuneCategory.STUDY: [
            "학업운에서 궁금한 점이 있으신가요?",
            "시험 운이나 집중력에 대해 알고 싶으신가요?",
            "진로 선택에 대해 조언이 필요하신가요?",
        ],
        FortuneCategory.GENERAL: [
            "더 궁금한 점이 있으신가요?",
            "연애, 재물, 직장 중 어느 운이 가장 궁금하신가요?",
            "올해 전체적인 흐름에 대해 더 알고 싶으신가요?",
        ],
    }

    questions = category_questions.get(category, category_questions[FortuneCategory.GENERAL])
    # 턴에 따라 다른 질문 선택
    idx = min(turn, len(questions) - 1)
    return questions[idx]


# ============================================================
# 세션 관리
# ============================================================

class TikitakaSession:
    """티키타카 세션 상태"""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.turn = 0
        self.messages: list[ChatMessage] = []
        self.user_info: dict = {}
        self.eastern_result: EasternFortuneResponse | None = None
        self.western_result: WesternFortuneDataV2 | None = None
        self.last_topic: str | None = None
        self.created_at = datetime.now()

        # Fortune ID 관련 필드
        self.eastern_fortune_id: str | None = None
        self.western_fortune_id: str | None = None
        self.fortune_source: str | None = None  # "created" | "cached"

        # 카테고리 관련 필드
        self.category: FortuneCategory = FortuneCategory.GENERAL

        # 캐릭터 코드 (turn/start에서 설정, turn/continue에서 사용)
        self.char1_code: str = "SOISEOL"
        self.char2_code: str = "STELLA"

        # 맥락 유지 필드 (v2)
        self.debate_history: list[dict] = []  # 토론 이력 (주제, 합의여부, 핵심포인트)
        self.user_preferences: dict = {}  # 사용자 선택 캐릭터, 관심 주제
        self.conversation_themes: list[str] = []  # 대화 핵심 주제들

        # 사용자 질문 히스토리 (로컬 폴백용)
        self.user_questions: list[str] = []  # 최근 사용자 질문들

        # 요약 컨텍스트 캐시 (GPT-5-mini용, Redis 복원 시 재계산 방지)
        self.eastern_summary: str = ""
        self.western_summary: str = ""

    def add_message(self, message: ChatMessage):
        """메시지 추가"""
        self.messages.append(message)

    def get_context(self) -> str:
        """대화 컨텍스트 요약 (레거시 호환)"""
        recent = self.messages[-6:] if len(self.messages) > 6 else self.messages
        return "\n".join([f"{m.character.value}: {m.content}" for m in recent])

    def get_rich_context(self, max_recent: int = 4, max_chars_per_msg: int = 100) -> str:
        """토큰 효율적인 대화 컨텍스트 생성

        최근 메시지는 전체 포함, 이전 메시지는 1줄 요약으로 압축하여
        토큰 사용량을 최소화합니다.

        Args:
            max_recent: 전체 포함할 최근 메시지 수 (기본: 4)
            max_chars_per_msg: 요약 시 메시지당 최대 글자 수 (기본: 100)

        Returns:
            압축된 대화 컨텍스트 문자열
        """
        context_parts = []

        # 1. 이전 대화 요약 (최근 N개 이전 메시지들을 1줄로)
        if len(self.messages) > max_recent:
            older = self.messages[:-max_recent]
            # 캐릭터별로 그룹핑하여 요약
            older_summary_parts = []
            for m in older[-6:]:  # 최대 6개만 요약
                if len(m.content) > max_chars_per_msg:
                    truncated = m.content[:max_chars_per_msg] + "..."
                else:
                    truncated = m.content
                older_summary_parts.append(f"{m.character.value}: {truncated}")
            if older_summary_parts:
                context_parts.append("[이전 대화 요약]\n" + "\n".join(older_summary_parts))

        # 2. 최근 대화 (전체 포함)
        recent = self.messages[-max_recent:] if len(self.messages) > max_recent else self.messages
        if recent:
            recent_lines = [f"{m.character.value}: {m.content}" for m in recent]
            context_parts.append("[최근 대화]\n" + "\n".join(recent_lines))

        # 3. 토론 이력 (핵심만, 최근 2개)
        if self.debate_history:
            history_summary = " / ".join([
                f"{d['topic']}({'합의' if d['consensus'] else '이견'})"
                for d in self.debate_history[-2:]
            ])
            context_parts.append(f"[토론]: {history_summary}")

        # 4. 대화 주제 (핵심 키워드만)
        if self.conversation_themes:
            themes = ", ".join(self.conversation_themes[-3:])  # 최근 3개
            context_parts.append(f"[주제]: {themes}")

        return "\n".join(context_parts) if context_parts else ""

    def add_debate_result(
        self,
        topic: str,
        is_consensus: bool,
        eastern_point: str,
        western_point: str,
        consensus_point: str | None = None,
    ):
        """토론 결과 저장

        Args:
            topic: 토론 주제
            is_consensus: 합의 여부
            eastern_point: 동양 관점 핵심
            western_point: 서양 관점 핵심
            consensus_point: 합의점 (합의 시)
        """
        # 메모리 관리: 최대 10개 유지
        if len(self.debate_history) >= 10:
            self.debate_history.pop(0)

        point_value = (
            consensus_point if is_consensus
            else f"동양: {eastern_point[:30]}... / 서양: {western_point[:30]}..."
        )
        self.debate_history.append({
            "topic": topic,
            "consensus": is_consensus,
            "point": point_value,
            "timestamp": datetime.now().isoformat(),
        })

        # 대화 주제 추가
        if topic not in self.conversation_themes:
            self.conversation_themes.append(topic)
            # 최대 10개 유지
            if len(self.conversation_themes) > 10:
                self.conversation_themes.pop(0)

    def update_user_preference(self, choice: int, char1_code: str, char2_code: str):
        """사용자 선택 기반 선호도 업데이트

        Args:
            choice: 1 (첫 번째 캐릭터) 또는 2 (두 번째 캐릭터)
            char1_code: 첫 번째 캐릭터 코드
            char2_code: 두 번째 캐릭터 코드
        """
        selected_char = char1_code if choice == 1 else char2_code

        # 선호 캐릭터 카운트
        if "char_counts" not in self.user_preferences:
            self.user_preferences["char_counts"] = {}

        char_counts = self.user_preferences["char_counts"]
        char_counts[selected_char] = char_counts.get(selected_char, 0) + 1

        # 가장 많이 선택한 캐릭터를 선호 캐릭터로 설정
        self.user_preferences["preferred_char"] = max(
            char_counts.items(), key=lambda x: x[1]
        )[0]

    def to_dict(self) -> dict:
        """세션을 Redis 저장용 dict로 직렬화"""
        # eastern_result 직렬화
        eastern_data = None
        if self.eastern_result:
            if hasattr(self.eastern_result, "model_dump"):
                eastern_data = self.eastern_result.model_dump()
            elif isinstance(self.eastern_result, dict):
                eastern_data = self.eastern_result

        # western_result 직렬화
        western_data = None
        if self.western_result:
            if hasattr(self.western_result, "model_dump"):
                western_data = self.western_result.model_dump()
            elif isinstance(self.western_result, dict):
                western_data = self.western_result

        # 요약 컨텍스트 생성 (GPT-5-mini용, 토큰 절감)
        eastern_summary = ""
        western_summary = ""
        if self.eastern_result:
            eastern_summary = create_summarized_eastern_context(self.eastern_result)
        if self.western_result:
            western_summary = create_summarized_western_context(self.western_result)

        return {
            "session_id": self.session_id,
            "turn": self.turn,
            "user_info": self.user_info,
            "category": self.category.value if self.category else "GENERAL",
            "eastern_fortune_id": self.eastern_fortune_id,
            "western_fortune_id": self.western_fortune_id,
            "fortune_source": self.fortune_source,
            "eastern_result": eastern_data,  # 전체 분석 결과
            "western_result": western_data,  # 전체 분석 결과
            "eastern_summary": eastern_summary,  # 요약 컨텍스트 (GPT-5-mini용)
            "western_summary": western_summary,  # 요약 컨텍스트 (GPT-5-mini용)
            "debate_history": self.debate_history[-5:],  # 최근 5개만
            "user_preferences": self.user_preferences,
            "conversation_themes": self.conversation_themes[-5:],  # 최근 5개만
            "user_questions": self.user_questions[-10:],  # 최근 10개 사용자 질문
            "messages": [
                {
                    "character": m.character.value,
                    "type": m.type.value,
                    "content": m.content[:500],  # 500자 제한 (대화 맥락 유지)
                }
                for m in self.messages[-15:]  # 최근 15개 (충분한 컨텍스트)
            ],
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TikitakaSession":
        """Redis에서 불러온 dict로 세션 복원"""
        session = cls(data["session_id"])
        session.turn = data.get("turn", 0)
        session.user_info = data.get("user_info", {})

        # 카테고리 복원
        category_value = data.get("category", "GENERAL")
        try:
            session.category = FortuneCategory(category_value)
        except ValueError:
            session.category = FortuneCategory.GENERAL

        session.eastern_fortune_id = data.get("eastern_fortune_id")
        session.western_fortune_id = data.get("western_fortune_id")
        session.fortune_source = data.get("fortune_source")
        session.debate_history = data.get("debate_history", [])
        session.user_preferences = data.get("user_preferences", {})
        session.conversation_themes = data.get("conversation_themes", [])
        session.user_questions = data.get("user_questions", [])

        # created_at 복원
        created_at_str = data.get("created_at")
        if created_at_str:
            try:
                session.created_at = datetime.fromisoformat(created_at_str)
            except ValueError:
                pass

        # 메시지 복원 (conversation_history 생성에 필요)
        messages_data = data.get("messages", [])
        for msg_data in messages_data:
            try:
                character = CharacterCode(msg_data.get("character", "SOISEOL"))
                msg_type = MessageType(msg_data.get("type", "TEXT"))
                content = msg_data.get("content", "")
                if content:  # 빈 내용은 스킵
                    session.messages.append(
                        ChatMessage(
                            character=character,
                            type=msg_type,
                            content=content,
                        )
                    )
            except (ValueError, KeyError) as e:
                logger.warning("message_restore_failed", error=str(e), msg=msg_data)
                continue

        # eastern_result, western_result 복원 (dict → DotDict로 래핑)
        eastern_data = data.get("eastern_result")
        if eastern_data:
            session.eastern_result = DotDict(eastern_data)
            logger.info("eastern_result_restored", session_id=session.session_id)

        western_data = data.get("western_result")
        if western_data:
            session.western_result = DotDict(western_data)
            logger.info("western_result_restored", session_id=session.session_id)

        # 요약 컨텍스트 복원 (캐시된 값 사용, 없으면 재생성)
        session.eastern_summary = data.get("eastern_summary", "")
        session.western_summary = data.get("western_summary", "")

        # 요약이 없고 결과가 있으면 재생성
        if not session.eastern_summary and session.eastern_result:
            session.eastern_summary = create_summarized_eastern_context(session.eastern_result)
        if not session.western_summary and session.western_result:
            session.western_summary = create_summarized_western_context(session.western_result)

        return session


# 세션 저장소 (Redis + 메모리 + 로컬 파일 폴백)
_sessions: dict[str, TikitakaSession] = {}

# Fortune 저장소 (메모리 폴백 - Redis 실패 시 사용)
_fortune_store: dict[str, EasternFortuneResponse | WesternFortuneDataV2] = {}

# 로컬 파일 세션 저장 경로
_LOCAL_SESSION_DIR = Path("/tmp/yeji_sessions")


def _get_local_session_path(session_id: str) -> Path:
    """로컬 세션 파일 경로 반환"""
    _LOCAL_SESSION_DIR.mkdir(parents=True, exist_ok=True)
    return _LOCAL_SESSION_DIR / f"{session_id}.json"


def save_session_to_local(session_id: str, data: dict) -> bool:
    """세션을 로컬 파일로 저장 (Redis 폴백)"""
    try:
        path = _get_local_session_path(session_id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.debug("session_saved_local", session_id=session_id, path=str(path))
        return True
    except Exception as e:
        logger.warning("local_session_save_failed", session_id=session_id, error=str(e))
        return False


def load_session_from_local(session_id: str) -> dict | None:
    """로컬 파일에서 세션 로드"""
    try:
        path = _get_local_session_path(session_id)
        if not path.exists():
            return None
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        logger.debug("session_loaded_local", session_id=session_id)
        return data
    except Exception as e:
        logger.warning("local_session_load_failed", session_id=session_id, error=str(e))
        return None


def delete_local_session(session_id: str) -> bool:
    """로컬 세션 파일 삭제"""
    try:
        path = _get_local_session_path(session_id)
        if path.exists():
            path.unlink()
        return True
    except Exception:
        return False


async def store_fortune_with_redis(
    birth_date: str,
    birth_time: str | None,
    fortune_type: str,  # "eastern" | "western"
    result: EasternFortuneResponse | WesternFortuneDataV2,
    fortune_id: str,
) -> None:
    """Redis를 사용한 운세 결과 저장 (폴백: 메모리)

    Args:
        birth_date: 생년월일 (YYYY-MM-DD)
        birth_time: 출생시간 (HH:MM 또는 None)
        fortune_type: 운세 타입 ("eastern" | "western")
        result: 저장할 운세 결과
        fortune_id: Fortune ID (메모리 폴백용)
    """
    # Redis 캐싱 시도
    try:
        result_dict = result.model_dump() if hasattr(result, "model_dump") else result
        redis_success = await cache_fortune(birth_date, birth_time, fortune_type, result_dict)

        if redis_success:
            logger.info(
                "fortune_stored_redis",
                fortune_id=fortune_id,
                type=type(result).__name__,
                birth_date=birth_date,
                birth_time=birth_time or "unknown",
            )
    except Exception as e:
        logger.warning("redis_store_failed", error=str(e), fortune_id=fortune_id)

    # 메모리 폴백 (항상 저장)
    _fortune_store[fortune_id] = result
    logger.debug("fortune_stored_memory", fortune_id=fortune_id, type=type(result).__name__)


def store_fortune(fortune_id: str, result: EasternFortuneResponse | WesternFortuneDataV2) -> None:
    """Fortune 결과 저장 (레거시 호환 - 메모리만 사용)

    Args:
        fortune_id: Fortune ID
        result: 저장할 운세 결과 (동양 또는 서양)
    """
    _fortune_store[fortune_id] = result
    logger.info("fortune_stored", fortune_id=fortune_id, type=type(result).__name__)


async def get_fortune_with_redis(
    birth_date: str,
    birth_time: str | None,
    fortune_type: str,
    fortune_id: str | None = None,
) -> EasternFortuneResponse | WesternFortuneDataV2 | None:
    """Redis를 사용한 운세 결과 조회 (폴백: 메모리)

    Args:
        birth_date: 생년월일 (YYYY-MM-DD)
        birth_time: 출생시간 (HH:MM 또는 None)
        fortune_type: 운세 타입 ("eastern" | "western")
        fortune_id: Fortune ID (메모리 폴백용, 옵션)

    Returns:
        저장된 운세 결과 또는 None
    """
    # Redis 조회 시도
    try:
        cached = await get_cached_fortune(birth_date, birth_time, fortune_type)
        if cached:
            # dict를 모델로 변환
            if fortune_type == "eastern":
                try:
                    return EasternFortuneResponse.model_validate(cached)
                except Exception as e:
                    logger.warning("eastern_validation_failed", error=str(e)[:100])
            else:  # western
                try:
                    return WesternFortuneDataV2.model_validate(cached)
                except Exception as e:
                    logger.warning("western_validation_failed", error=str(e)[:100])
    except Exception as e:
        logger.warning("redis_get_failed", error=str(e))

    # 메모리 폴백 (fortune_id가 있는 경우)
    if fortune_id:
        result = _fortune_store.get(fortune_id)
        if result:
            logger.debug("fortune_cache_hit_memory", fortune_id=fortune_id)
            return result

    logger.debug(
        "fortune_cache_miss_all",
        birth_date=birth_date,
        birth_time=birth_time or "unknown",
    )
    return None


def get_fortune(fortune_id: str) -> EasternFortuneResponse | WesternFortuneDataV2 | None:
    """Fortune 결과 조회 (레거시 호환 - 메모리만 사용)

    Args:
        fortune_id: Fortune ID

    Returns:
        저장된 운세 결과 또는 None
    """
    result = _fortune_store.get(fortune_id)
    if result:
        logger.debug("fortune_cache_hit", fortune_id=fortune_id)
    else:
        logger.debug("fortune_cache_miss", fortune_id=fortune_id)
    return result


def get_or_create_session(session_id: str | None) -> TikitakaSession:
    """세션 조회 또는 생성 (동기 - 메모리만 사용)"""
    if session_id and session_id in _sessions:
        return _sessions[session_id]

    new_id = str(uuid.uuid4())[:8]
    session = TikitakaSession(new_id)
    _sessions[new_id] = session
    return session


async def get_or_create_session_async(session_id: str | None) -> TikitakaSession:
    """세션 조회 또는 생성 (비동기 - 메모리 → Redis → 로컬 파일)

    1. 메모리에서 먼저 조회
    2. 없으면 Redis에서 조회
    3. 없으면 로컬 파일에서 조회 (Redis 폴백)
    4. 없으면 새 세션 생성
    """
    # 1. 메모리 캐시 확인
    if session_id and session_id in _sessions:
        return _sessions[session_id]

    # 2. Redis에서 조회
    if session_id:
        redis_data = await get_session_from_redis(session_id)
        if redis_data:
            session = TikitakaSession.from_dict(redis_data)
            _sessions[session_id] = session  # 메모리에도 캐시
            logger.info("session_restored_from_redis", session_id=session_id)
            return session

        # 3. 로컬 파일에서 조회 (Redis 폴백)
        local_data = load_session_from_local(session_id)
        if local_data:
            session = TikitakaSession.from_dict(local_data)
            _sessions[session_id] = session
            logger.info("session_restored_from_local", session_id=session_id)
            return session

    # 4. 새 세션 생성
    new_id = str(uuid.uuid4())[:8]
    session = TikitakaSession(new_id)
    _sessions[new_id] = session

    # Redis 저장 시도, 실패 시 로컬 파일로 폴백
    session_data = session.to_dict()
    redis_success = await save_session_to_redis(new_id, session_data)
    if not redis_success:
        save_session_to_local(new_id, session_data)

    return session


async def save_session(session: TikitakaSession) -> None:
    """세션을 메모리, Redis, 로컬 파일에 저장 (3중 폴백)"""
    _sessions[session.session_id] = session
    session_data = session.to_dict()

    # Redis 저장 시도
    redis_success = await save_session_to_redis(session.session_id, session_data)

    # Redis 실패 시 로컬 파일로 폴백
    if not redis_success:
        save_session_to_local(session.session_id, session_data)
        logger.info("session_saved_local_fallback", session_id=session.session_id)


def get_session(session_id: str) -> TikitakaSession | None:
    """세션 조회 - 동기 (메모리만, 없으면 None 반환)"""
    return _sessions.get(session_id)


async def get_session_async(session_id: str) -> TikitakaSession | None:
    """세션 조회 - 비동기 (메모리 → Redis → 로컬 파일)"""
    # 1. 메모리 먼저
    if session_id in _sessions:
        return _sessions[session_id]

    # 2. Redis에서 조회
    redis_data = await get_session_from_redis(session_id)
    if redis_data:
        session = TikitakaSession.from_dict(redis_data)
        _sessions[session_id] = session
        return session

    # 3. 로컬 파일에서 조회 (Redis 폴백)
    local_data = load_session_from_local(session_id)
    if local_data:
        session = TikitakaSession.from_dict(local_data)
        _sessions[session_id] = session
        logger.info("session_restored_from_local", session_id=session_id)
        return session

    return None


def create_session(
    birth_date: str | None = None,
    birth_time: str | None = None,
) -> TikitakaSession:
    """새 세션 생성 (명시적)"""
    new_id = str(uuid.uuid4())[:8]
    session = TikitakaSession(new_id)
    if birth_date:
        session.user_info["birth_date"] = birth_date
    if birth_time:
        session.user_info["birth_time"] = birth_time
    _sessions[new_id] = session
    logger.info("session_created", session_id=new_id)
    return session


def delete_session(session_id: str) -> bool:
    """세션 삭제"""
    if session_id in _sessions:
        del _sessions[session_id]
        logger.info("session_deleted", session_id=session_id)
        return True
    return False


def list_sessions() -> list[dict]:
    """모든 세션 목록 조회"""
    return [
        {
            "session_id": s.session_id,
            "turn": s.turn,
            "has_eastern": s.eastern_result is not None,
            "has_western": s.western_result is not None,
            "eastern_fortune_id": s.eastern_fortune_id,
            "western_fortune_id": s.western_fortune_id,
            "created_at": s.created_at.isoformat(),
        }
        for s in _sessions.values()
    ]


def list_fortunes() -> list[dict]:
    """저장된 Fortune 목록 조회"""
    return [
        {
            "fortune_id": fid,
            "type": "eastern" if "Eastern" in type(f).__name__ else "western",
        }
        for fid, f in _fortune_store.items()
    ]


def clear_all_data() -> dict:
    """모든 세션 및 Fortune 데이터 초기화"""
    session_count = len(_sessions)
    fortune_count = len(_fortune_store)
    _sessions.clear()
    _fortune_store.clear()
    logger.info("all_data_cleared", sessions=session_count, fortunes=fortune_count)
    return {"cleared_sessions": session_count, "cleared_fortunes": fortune_count}


# ============================================================
# 티키타카 서비스
# ============================================================

class TikitakaService:
    """티키타카 대화 서비스"""

    def __init__(self):
        self.eastern_service = EasternFortuneService()
        self.western_service = WesternFortuneService()
        self.llm = LLMInterpreter()
        self._openai_provider: OpenAIProvider | None = None
        self._vllm_provider: VLLMProvider | None = None  # 8B vLLM 전용
        self._bubble_parser = BubbleParser() if BUBBLE_PARSER_AVAILABLE else None
        self._settings = get_settings()
        logger.info(
            "tikitaka_service_init",
            use_gpt5mini=self._settings.use_gpt5mini_for_chat,
        )

    # ============================================================
    # 분석 실행
    # ============================================================

    async def analyze_both(
        self,
        birth_date: str,
        birth_time: str | None = None,
        birth_place: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
    ) -> tuple[EasternFortuneResponse, WesternFortuneDataV2]:
        """
        동양/서양 분석 동시 실행

        Returns:
            (동양 분석 결과, 서양 분석 결과) 튜플
        """
        # 요청 객체 생성
        eastern_req = EasternFortuneRequest(
            birth_date=birth_date,
            birth_time=birth_time,
        )
        western_req = WesternFortuneRequest(
            birth_date=birth_date,
            birth_time=birth_time,
            birth_place=birth_place,
            latitude=latitude,
            longitude=longitude,
        )

        # 동시 실행
        eastern_result, western_result = await asyncio.gather(
            self.eastern_service.analyze(eastern_req),
            self.western_service.analyze(western_req),
        )

        return eastern_result, western_result

    async def get_or_create_fortunes(
        self,
        birth_date: str,
        birth_time: str | None = None,
        birth_place: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        eastern_fortune_id: str | None = None,
        western_fortune_id: str | None = None,
    ) -> tuple[EasternFortuneResponse, WesternFortuneDataV2, str, str, str]:
        """
        운세 결과 조회 또는 생성 (Redis 캐싱 우선 적용)

        1. Redis에서 birth_date+birth_time 조합으로 조회 시도
        2. Redis 실패 시 fortune_id로 메모리 조회
        3. 없으면 신규로 LLM 생성

        Args:
            birth_date: 생년월일 (YYYY-MM-DD)
            birth_time: 출생시간 (HH:MM)
            birth_place: 출생장소
            latitude: 위도
            longitude: 경도
            eastern_fortune_id: 기존 동양 운세 ID (메모리 폴백용)
            western_fortune_id: 기존 서양 운세 ID (메모리 폴백용)

        Returns:
            (eastern_result, western_result, eastern_id, western_id, source) 튜플
            source: "redis" (Redis 캐시) | "memory" (메모리 캐시) | "created" (신규 생성)
        """
        eastern_result: EasternFortuneResponse | None = None
        western_result: WesternFortuneDataV2 | None = None
        source = "created"

        # 1단계: Redis에서 birth_date+birth_time 조합으로 조회
        eastern_from_redis = await get_fortune_with_redis(
            birth_date, birth_time, "eastern", eastern_fortune_id
        )
        western_from_redis = await get_fortune_with_redis(
            birth_date, birth_time, "western", western_fortune_id
        )

        if eastern_from_redis and western_from_redis:
            # Redis에서 둘 다 조회 성공
            logger.info(
                "fortune_cache_hit_redis_both",
                birth_date=birth_date,
                birth_time=birth_time or "unknown",
            )
            eastern_result = eastern_from_redis
            western_result = western_from_redis
            source = "redis"

            # ID 생성 (재사용 또는 신규)
            new_eastern_id = eastern_fortune_id or str(uuid.uuid4())[:8]
            new_western_id = western_fortune_id or str(uuid.uuid4())[:8]

            return eastern_result, western_result, new_eastern_id, new_western_id, source

        # 부분 캐시 히트 처리
        if eastern_from_redis:
            eastern_result = eastern_from_redis
            logger.info("eastern_fortune_cache_hit", source="redis")
        elif eastern_fortune_id:
            # 2단계: 메모리 폴백 (fortune_id로 조회)
            cached = get_fortune(eastern_fortune_id)
            if isinstance(cached, EasternFortuneResponse):
                eastern_result = cached
                source = "memory"
                logger.info(
                    "eastern_fortune_reused",
                    fortune_id=eastern_fortune_id,
                    source="memory",
                )

        if western_from_redis:
            western_result = western_from_redis
            logger.info("western_fortune_cache_hit", source="redis")
        elif western_fortune_id:
            # 2단계: 메모리 폴백 (fortune_id로 조회)
            cached = get_fortune(western_fortune_id)
            if isinstance(cached, WesternFortuneDataV2):
                western_result = cached
                source = "memory" if source != "redis" else source
                logger.info(
                    "western_fortune_reused",
                    fortune_id=western_fortune_id,
                    source="memory",
                )

        # 둘 다 캐시에서 조회 성공 (Redis 또는 메모리)
        if eastern_result and western_result:
            # ID 생성 (재사용 또는 신규)
            new_eastern_id = eastern_fortune_id or str(uuid.uuid4())[:8]
            new_western_id = western_fortune_id or str(uuid.uuid4())[:8]

            logger.info(
                "fortune_both_cached",
                eastern_id=new_eastern_id,
                western_id=new_western_id,
                source=source,
            )

            return (
                eastern_result,
                western_result,
                new_eastern_id,
                new_western_id,
                source,
            )

        # 3단계: 일부 또는 전체 신규 생성 필요
        tasks = []
        task_keys = []

        if not eastern_result:
            eastern_req = EasternFortuneRequest(
                birth_date=birth_date,
                birth_time=birth_time,
            )
            tasks.append(self.eastern_service.analyze(eastern_req))
            task_keys.append("eastern")

        if not western_result:
            western_req = WesternFortuneRequest(
                birth_date=birth_date,
                birth_time=birth_time,
                birth_place=birth_place,
                latitude=latitude,
                longitude=longitude,
            )
            tasks.append(self.western_service.analyze(western_req))
            task_keys.append("western")

        # 필요한 것만 병렬 생성
        if tasks:
            logger.info("fortune_llm_generation_start", tasks=task_keys)
            results = await asyncio.gather(*tasks)
            for i, key in enumerate(task_keys):
                if key == "eastern":
                    eastern_result = results[i]
                else:
                    western_result = results[i]

        # ID 생성
        new_eastern_id = eastern_fortune_id or str(uuid.uuid4())[:8]
        new_western_id = western_fortune_id or str(uuid.uuid4())[:8]

        # 4단계: 새로 생성된 결과를 Redis + 메모리에 저장
        if eastern_result and "eastern" in task_keys:
            # Redis 캐싱 시도 (비동기)
            await store_fortune_with_redis(
                birth_date, birth_time, "eastern", eastern_result, new_eastern_id
            )
            logger.info("eastern_fortune_created", fortune_id=new_eastern_id)

        if western_result and "western" in task_keys:
            # Redis 캐싱 시도 (비동기)
            await store_fortune_with_redis(
                birth_date, birth_time, "western", western_result, new_western_id
            )
            logger.info("western_fortune_created", fortune_id=new_western_id)

        # source 업데이트: 일부만 캐시인 경우 "created" 유지
        if source == "created":
            source = "created"

        return (
            eastern_result,  # type: ignore
            western_result,  # type: ignore
            new_eastern_id,
            new_western_id,
            source,
        )

    def create_summary(
        self,
        session: TikitakaSession,
        fortune_type: str,
        category: str = "total",
    ) -> dict:
        """티키타카 세션의 운세 요약 생성

        Args:
            session: 티키타카 세션 (eastern_result 또는 western_result 포함)
            fortune_type: "eastern" 또는 "western"
            category: 운세 카테고리 (total, love, wealth, career, health)

        Returns:
            FortuneSummaryResponse 형식의 dict
            {
                "session_id": str,
                "category": str,
                "fortune_type": str,
                "fortune": {
                    "character": str,
                    "score": int,
                    "one_line": str,
                    "keywords": list[str],
                    "detail": str,
                }
            }

        Raises:
            ValueError: 해당 fortune_type의 결과가 없는 경우
        """
        if fortune_type == "eastern":
            if not session.eastern_result:
                raise ValueError("Eastern fortune result가 없습니다")
            return self._create_eastern_summary(session, category)
        elif fortune_type == "western":
            if not session.western_result:
                raise ValueError("Western fortune result가 없습니다")
            return self._create_western_summary(session, category)
        else:
            raise ValueError(f"지원하지 않는 fortune_type: {fortune_type}")

    def _create_eastern_summary(
        self,
        session: TikitakaSession,
        category: str,
    ) -> dict:
        """동양 운세 요약 생성"""
        eastern = session.eastern_result
        if not eastern:
            raise ValueError("Eastern result가 없습니다")

        # 오행 균형도 기반 점수 계산 (70-95 범위)
        score = self._calculate_eastern_score(eastern)

        # 카테고리에 따른 한 줄 요약 추출
        one_line = self._extract_eastern_one_line(eastern, category)

        # 키워드 추출 (2-5개)
        keywords = self._extract_eastern_keywords(eastern, category)

        # 상세 내용 조합 (50-500자)
        detail = self._extract_eastern_detail(eastern, category)

        return {
            "session_id": session.session_id,
            "category": category,
            "fortune_type": "eastern",
            "fortune": {
                "character": "SOISEOL",
                "score": score,
                "one_line": one_line[:100],  # 최대 100자 제한
                "keywords": keywords[:5],  # 최대 5개 제한
                "detail": detail[:500],  # 최대 500자 제한
            },
        }

    def _create_western_summary(
        self,
        session: TikitakaSession,
        category: str,
    ) -> dict:
        """서양 운세 요약 생성"""
        western = session.western_result
        if not western:
            raise ValueError("Western result가 없습니다")

        # Element/Modality 분포 기반 점수 계산 (70-95 범위)
        score = self._calculate_western_score(western)

        # 카테고리에 따른 한 줄 요약 추출
        one_line = self._extract_western_one_line(western, category)

        # 키워드 추출 (2-5개)
        keywords = self._extract_western_keywords(western, category)

        # 상세 내용 조합 (50-500자)
        detail = self._extract_western_detail(western, category)

        return {
            "session_id": session.session_id,
            "category": category,
            "fortune_type": "western",
            "fortune": {
                "character": "STELLA",
                "score": score,
                "one_line": one_line[:100],  # 최대 100자 제한
                "keywords": keywords[:5],  # 최대 5개 제한
                "detail": detail[:500],  # 최대 500자 제한
            },
        }

    def _calculate_eastern_score(self, eastern: EasternFortuneResponse) -> int:
        """동양 운세 점수 계산 (오행 균형도 기반)

        오행 분포가 고르면 높은 점수, 편중되면 낮은 점수
        """
        try:
            # stats.five_elements.elements에서 percent 추출
            if hasattr(eastern, "stats") and hasattr(eastern.stats, "five_elements"):
                elements = eastern.stats.five_elements.elements
                percents = [elem.percent for elem in elements if hasattr(elem, "percent")]

                if percents:
                    # 표준편차 계산 (균형도 지표)
                    import statistics

                    std_dev = statistics.stdev(percents) if len(percents) > 1 else 0

                    # 표준편차가 낮을수록 균형적 → 높은 점수
                    # std_dev 0~20: 점수 95~75
                    score = max(75, min(95, int(95 - std_dev)))
                    return score
        except Exception as e:
            logger.warning("eastern_score_calculation_error", error=str(e))

        # 기본 점수
        return 80

    def _calculate_western_score(self, western: WesternFortuneDataV2) -> int:
        """서양 운세 점수 계산 (Element/Modality 분포 기반)"""
        try:
            # stats에서 element, modality 분포 추출
            if hasattr(western, "stats"):
                # element 분포 균형도 체크
                if hasattr(western.stats, "element_distribution"):
                    elem_dist = western.stats.element_distribution
                    percents = []
                    for elem in ["fire", "earth", "air", "water"]:
                        if hasattr(elem_dist, elem):
                            percents.append(getattr(elem_dist, elem))

                    if percents:
                        import statistics

                        std_dev = statistics.stdev(percents) if len(percents) > 1 else 0
                        score = max(75, min(95, int(95 - std_dev)))
                        return score
        except Exception as e:
            logger.warning("western_score_calculation_error", error=str(e))

        # 기본 점수
        return 82

    def _extract_eastern_one_line(
        self, eastern: EasternFortuneResponse, category: str
    ) -> str:
        """동양 운세 한 줄 요약 추출"""
        try:
            # summary 또는 message에서 첫 문장 추출
            if hasattr(eastern, "summary") and eastern.summary:
                first_sentence = eastern.summary.split(".")[0].strip()
                if 10 <= len(first_sentence) <= 100:
                    return first_sentence

            if hasattr(eastern, "message") and eastern.message:
                first_sentence = eastern.message.split(".")[0].strip()
                if 10 <= len(first_sentence) <= 100:
                    return first_sentence

            # final_verdict에서 추출
            if hasattr(eastern, "final_verdict") and hasattr(
                eastern.final_verdict, "summary"
            ):
                return eastern.final_verdict.summary[:100]

        except Exception as e:
            logger.warning("eastern_one_line_extraction_error", error=str(e))

        # 기본 메시지
        return "오늘 하루도 좋은 기운이 함께 합니다"

    def _extract_western_one_line(
        self, western: WesternFortuneDataV2, category: str
    ) -> str:
        """서양 운세 한 줄 요약 추출"""
        try:
            # fortune_content.overview에서 첫 문장 추출
            if hasattr(western, "fortune_content") and hasattr(
                western.fortune_content, "overview"
            ):
                first_sentence = western.fortune_content.overview.split(".")[0].strip()
                if 10 <= len(first_sentence) <= 100:
                    return first_sentence

            # fortune_content.advice
            if hasattr(western, "fortune_content") and hasattr(
                western.fortune_content, "advice"
            ):
                return western.fortune_content.advice[:100]

        except Exception as e:
            logger.warning("western_one_line_extraction_error", error=str(e))

        # 기본 메시지
        return "별들이 당신에게 좋은 운을 가져다 줄 것입니다"

    def _extract_eastern_keywords(
        self, eastern: EasternFortuneResponse, category: str
    ) -> list[str]:
        """동양 운세 키워드 추출 (2-5개)"""
        keywords = []

        try:
            # stats.five_elements에서 strong/weak 추출
            if hasattr(eastern, "stats") and hasattr(eastern.stats, "five_elements"):
                five_elements = eastern.stats.five_elements
                if hasattr(five_elements, "strong") and five_elements.strong:
                    strong_label = _safe_get_label(five_elements.strong)
                    keywords.append(f"{strong_label} 기운 강함")

                if hasattr(five_elements, "weak") and five_elements.weak:
                    weak_label = _safe_get_label(five_elements.weak)
                    keywords.append(f"{weak_label} 기운 약함")

            # lucky 정보에서 추출
            if hasattr(eastern, "lucky"):
                if hasattr(eastern.lucky, "color") and eastern.lucky.color:
                    keywords.append(f"행운의 색: {eastern.lucky.color}")
                if hasattr(eastern.lucky, "direction") and eastern.lucky.direction:
                    keywords.append(f"길방: {eastern.lucky.direction}")

        except Exception as e:
            logger.warning("eastern_keywords_extraction_error", error=str(e))

        # 최소 2개 보장
        if len(keywords) < 2:
            keywords = ["사주 분석", "운세 해석"]

        return keywords[:5]

    def _extract_western_keywords(
        self, western: WesternFortuneDataV2, category: str
    ) -> list[str]:
        """서양 운세 키워드 추출 (2-5개)"""
        keywords = []

        try:
            # element
            if hasattr(western, "element") and western.element:
                keywords.append(f"{western.element} 타입")

            # stats.main_sign에서 별자리 추출
            if hasattr(western, "stats") and hasattr(western.stats, "main_sign"):
                main_sign = western.stats.main_sign
                if hasattr(main_sign, "name_ko"):
                    keywords.append(main_sign.name_ko)

            # lucky 정보
            if hasattr(western, "lucky"):
                if hasattr(western.lucky, "color") and western.lucky.color:
                    keywords.append(f"행운색: {western.lucky.color}")
                if hasattr(western.lucky, "number") and western.lucky.number:
                    keywords.append(f"행운숫자: {western.lucky.number}")

        except Exception as e:
            logger.warning("western_keywords_extraction_error", error=str(e))

        # 최소 2개 보장
        if len(keywords) < 2:
            keywords = ["점성술", "별자리 분석"]

        return keywords[:5]

    def _extract_eastern_detail(
        self, eastern: EasternFortuneResponse, category: str
    ) -> str:
        """동양 운세 상세 내용 조합 (50-500자)"""
        try:
            parts = []

            # chart.summary
            if hasattr(eastern, "chart") and hasattr(eastern.chart, "summary"):
                parts.append(eastern.chart.summary)

            # summary
            if hasattr(eastern, "summary") and eastern.summary:
                parts.append(eastern.summary)

            # final_verdict.advice
            if hasattr(eastern, "final_verdict") and hasattr(
                eastern.final_verdict, "advice"
            ):
                parts.append(eastern.final_verdict.advice)

            combined = " ".join(parts)
            if len(combined) >= 50:
                return combined[:500]

            # 너무 짧으면 message 사용
            if hasattr(eastern, "message") and eastern.message:
                return eastern.message[:500]

        except Exception as e:
            logger.warning("eastern_detail_extraction_error", error=str(e))

        # 기본 메시지
        return (
            "사주 팔자를 분석한 결과, 당신의 운세는 전반적으로 안정적인 흐름을 보이고 있습니다. "
            "오행의 균형을 유지하며 나아가시기 바랍니다."
        )

    def _extract_western_detail(
        self, western: WesternFortuneDataV2, category: str
    ) -> str:
        """서양 운세 상세 내용 조합 (50-500자)"""
        try:
            parts = []

            # fortune_content.overview
            if hasattr(western, "fortune_content") and hasattr(
                western.fortune_content, "overview"
            ):
                parts.append(western.fortune_content.overview)

            # fortune_content.detailed_analysis
            if hasattr(western, "fortune_content") and hasattr(
                western.fortune_content, "detailed_analysis"
            ):
                for analysis in western.fortune_content.detailed_analysis:
                    if hasattr(analysis, "content"):
                        parts.append(analysis.content)

            combined = " ".join(parts)
            if len(combined) >= 50:
                return combined[:500]

            # fortune_content.advice
            if hasattr(western, "fortune_content") and hasattr(
                western.fortune_content, "advice"
            ):
                return western.fortune_content.advice[:500]

        except Exception as e:
            logger.warning("western_detail_extraction_error", error=str(e))

        # 기본 메시지
        return (
            "별들의 배치를 분석한 결과, 당신의 운세는 긍정적인 에너지로 가득 차 있습니다. "
            "별들이 당신을 응원하고 있으니 자신감을 가지고 나아가세요."
        )

    # ============================================================
    # 인사 메시지
    # ============================================================

    def create_greeting_messages(
        self,
        char1_code: str = "SOISEOL",
        char2_code: str = "STELLA",
        category: FortuneCategory = FortuneCategory.GENERAL,
    ) -> list[ChatMessage]:
        """인사 메시지 생성 (카테고리별 그리팅 적용)

        Args:
            char1_code: 첫 번째 캐릭터 코드 (기본값: SOISEOL)
            char2_code: 두 번째 캐릭터 코드 (기본값: STELLA)
            category: 운세 카테고리 (기본값: GENERAL)
        """
        from yeji_ai.prompts.category_greetings import get_category_greeting

        now = datetime.now()

        # 캐릭터별 카테고리 그리팅 가져오기
        char1_greeting_data = get_category_greeting(category, char1_code)
        char2_greeting_data = get_category_greeting(category, char2_code)

        # 기본 인사 메시지 (카테고리 무관)
        basic_greetings = {
            "SOISEOL": "동방에서 온 소이설이라 하오.",
            "STELLA": "안녕하세요! 저는 스텔라예요.",
            "CHEONGWOON": "청운이라 하오.",
            "HWARIN": "안녕하세요, 화린이에요.",
            "KYLE": "요, 카일이야.",
            "ELARIA": "안녕하세요, 엘라리아예요.",
        }

        info_requests = {
            "SOISEOL": "귀하의 생년월일을 알려주시오. 예를 들어 1990년 5월 15일처럼 말이오.",
            "CHEONGWOON": "자네의 생년월일을 말해주게나. 천지의 흐름을 읽어보리다.",
            "STELLA": "생년월일을 알려주시면 별자리를 분석해드릴게요!",
            "HWARIN": "생년월일 알려주시면 바로 봐드릴게요.",
            "KYLE": "생년월일 좀 알려줘. 카드가 뭐라고 하는지 볼게.",
            "ELARIA": "생년월일을 알려주시면 별의 메시지를 전해드릴게요.",
        }

        return [
            ChatMessage(
                character=CharacterCode(char1_code),
                type=MessageType.GREETING,
                content=basic_greetings.get(char1_code, f"{char1_code}입니다."),
                timestamp=now,
            ),
            ChatMessage(
                character=CharacterCode(char1_code),
                type=MessageType.GREETING,
                content=char1_greeting_data["greeting"],
                timestamp=now,
            ),
            ChatMessage(
                character=CharacterCode(char2_code),
                type=MessageType.GREETING,
                content=basic_greetings.get(char2_code, f"{char2_code}입니다."),
                timestamp=now,
            ),
            ChatMessage(
                character=CharacterCode(char2_code),
                type=MessageType.GREETING,
                content=char2_greeting_data["greeting"],
                timestamp=now,
            ),
            ChatMessage(
                character=CharacterCode(char1_code),
                type=MessageType.INFO_REQUEST,
                content=info_requests.get(char1_code, "생년월일을 알려주세요."),
                timestamp=now,
            ),
        ]

    async def create_category_greeting(
        self,
        birth_date: str,
        category: FortuneCategory,
        char1_code: str = "SOISEOL",
        char2_code: str = "STELLA",
        birth_time: str | None = None,
        birth_place: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        eastern_fortune_id: str | None = None,
        western_fortune_id: str | None = None,
        eastern_fortune_data: dict | None = None,
        western_fortune_data: dict | None = None,
    ) -> tuple[list[ChatMessage], str, str, str]:
        """
        카테고리별 그리팅 생성 (실제 분석 결과 기반)

        Args:
            birth_date: 생년월일 (YYYY-MM-DD)
            category: 운세 카테고리 (애정운, 직장운 등)
            char1_code: 동양 캐릭터 코드
            char2_code: 서양 캐릭터 코드
            birth_time: 출생시간 (HH:MM)
            birth_place: 출생장소
            latitude: 위도
            longitude: 경도
            eastern_fortune_id: 기존 동양 운세 ID (재사용)
            western_fortune_id: 기존 서양 운세 ID (재사용)
            eastern_fortune_data: 동양 사주 분석 결과 객체 (직접 전달)
            western_fortune_data: 서양 점성술 분석 결과 객체 (직접 전달)

        Returns:
            (그리팅 메시지 목록, eastern_fortune_id, western_fortune_id, source)
            source: "provided" (직접 전달) | "cached" (캐시 조회) | "created" (실시간 분석)
        """
        logger.info(
            "category_greeting_start",
            category=category.value,
            birth_date=birth_date
        )

        # GPT-5-mini 사용 시 create_tikitaka_messages_gpt5mini로 위임
        if self._settings.use_gpt5mini_for_chat and self._settings.openai_api_key:
            logger.info("category_greeting_using_gpt5mini")
            # 운세 데이터 먼저 조회/생성
            if eastern_fortune_data and western_fortune_data:
                eastern_result = eastern_fortune_data
                western_result = western_fortune_data
                if isinstance(eastern_fortune_data, dict) and "data" in eastern_fortune_data:
                    eastern_result = eastern_fortune_data["data"]
                if isinstance(western_fortune_data, dict) and "data" in western_fortune_data:
                    western_result = western_fortune_data["data"]
                e_id = eastern_fortune_id or "provided"
                w_id = western_fortune_id or "provided"
                source = "provided"
            else:
                eastern_result, western_result, e_id, w_id, source = await self.get_or_create_fortunes(
                    birth_date=birth_date,
                    birth_time=birth_time,
                    birth_place=birth_place,
                    latitude=latitude,
                    longitude=longitude,
                    eastern_fortune_id=eastern_fortune_id,
                    western_fortune_id=western_fortune_id,
                )

            # 컨텍스트 생성 (같은 모듈의 함수 직접 호출)
            eastern_context = create_summarized_eastern_context(eastern_result)
            western_context = create_summarized_western_context(western_result)

            logger.info(
                "category_greeting_gpt5mini_context",
                category=category.value,
                eastern_context_len=len(eastern_context) if eastern_context else 0,
                western_context_len=len(western_context) if western_context else 0,
                eastern_context_preview=eastern_context[:200] if eastern_context else "EMPTY",
                western_context_preview=western_context[:200] if western_context else "EMPTY",
            )

            # GPT-5-mini로 그리팅 생성 (topic은 소문자로 변환)
            messages, _ = await self.create_tikitaka_messages_gpt5mini(
                topic=category.value.lower(),
                eastern_context=eastern_context,
                western_context=western_context,
                mode="greeting",
                char1_code=char1_code,
                char2_code=char2_code,
                is_first_turn=True,
                is_last_turn=False,
                user_question="",
                category=category.value.lower(),
            )
            return messages, e_id, w_id, source

        # 1. 운세 분석 실행 또는 캐시 조회
        # fortune_data가 직접 전달된 경우 우선 사용
        if eastern_fortune_data and western_fortune_data:
            # 직접 전달된 데이터 사용
            # FortuneResponse 래퍼 형태({success, validated, data})인 경우 data 필드 추출
            eastern_data = eastern_fortune_data
            if isinstance(eastern_fortune_data, dict) and "data" in eastern_fortune_data:
                eastern_data = eastern_fortune_data["data"]
            western_data = western_fortune_data
            if isinstance(western_fortune_data, dict) and "data" in western_fortune_data:
                western_data = western_fortune_data["data"]

            # LLM 응답 형식과 모델 스키마가 다를 수 있으므로 검증 실패 시 DotDict로 변환
            try:
                eastern_result = EasternFortuneResponse.model_validate(eastern_data)
            except Exception as e:
                logger.warning("eastern_fortune_validation_skip", error=str(e)[:100])
                eastern_result = (
                    DotDict(eastern_data)
                    if isinstance(eastern_data, dict)
                    else eastern_data  # type: ignore
                )
            try:
                western_result = WesternFortuneDataV2.model_validate(western_data)
            except Exception as e:
                logger.warning("western_fortune_validation_skip", error=str(e)[:100])
                western_result = (
                    DotDict(western_data)
                    if isinstance(western_data, dict)
                    else western_data  # type: ignore
                )

            # ID 생성 및 저장
            e_id = eastern_fortune_id or str(uuid.uuid4())[:8]
            w_id = western_fortune_id or str(uuid.uuid4())[:8]
            store_fortune(e_id, eastern_result)
            store_fortune(w_id, western_result)
            source = "provided"

            logger.info(
                "fortune_data_provided",
                eastern_id=e_id,
                western_id=w_id,
            )
        else:
            # 기존 로직: ID로 조회하거나 신규 생성
            eastern_result, western_result, e_id, w_id, source = await self.get_or_create_fortunes(
                birth_date=birth_date,
                birth_time=birth_time,
                birth_place=birth_place,
                latitude=latitude,
                longitude=longitude,
                eastern_fortune_id=eastern_fortune_id,
                western_fortune_id=western_fortune_id,
            )

            logger.info(
                "fortune_data_ready",
                source=source,
                eastern_id=e_id,
                western_id=w_id,
            )

        # 2. 동양/서양 분석 결과 컨텍스트 생성
        eastern_context = self._format_eastern_context_for_category(
            eastern_result, category
        )
        western_context = self._format_western_context_for_category(
            western_result, category
        )

        # 3. LLM으로 카테고리별 그리팅 생성 (순차 생성 + 컨텍스트 체이닝)
        now = datetime.now()
        messages = []

        try:
            # 1. 첫 번째 캐릭터(동양) 생성
            eastern_greeting = await self.llm.generate_category_greeting(
                char1_code, category.value, eastern_context
            )

            # 2. 두 번째 캐릭터(서양)에 첫 번째 발언 주입
            western_context_with_interaction = f"""{western_context}

## 상대 캐릭터의 직전 발언
"{eastern_greeting}"

## 지시
위 발언을 자연스럽게 받아서 대화하세요. 동의하거나 보완하는 방식으로."""

            western_greeting = await self.llm.generate_category_greeting(
                char2_code, category.value, western_context_with_interaction
            )

            # 노이즈 필터 적용
            eastern_greeting = fix_brackets(
                filter_prompt_leak(filter_noise(eastern_greeting, aggressive=True))
            )
            western_greeting = fix_brackets(
                filter_prompt_leak(filter_noise(western_greeting, aggressive=True))
            )

            # 메시지 길이 제한 적용 (150자, 카카오톡 3줄 수준)
            eastern_greeting = self._truncate_message(eastern_greeting)
            western_greeting = self._truncate_message(western_greeting)

            # 빈 응답 폴백
            if not eastern_greeting or len(eastern_greeting.strip()) < 10:
                logger.warning("empty_greeting", character=char1_code)
                eastern_greeting = self._fallback_eastern_greeting(
                    eastern_result, category
                )

            if not western_greeting or len(western_greeting.strip()) < 10:
                logger.warning("empty_greeting", character=char2_code)
                western_greeting = self._fallback_western_greeting(
                    western_result, category
                )

        except Exception as e:
            logger.error("greeting_generation_error", error=str(e))
            eastern_greeting = self._fallback_eastern_greeting(eastern_result, category)
            western_greeting = self._fallback_western_greeting(western_result, category)

        # 4. 티키타카 메시지 구성
        messages.append(ChatMessage(
            character=CharacterCode(char1_code),
            type=MessageType.GREETING,
            content=eastern_greeting,
            timestamp=now,
        ))

        messages.append(ChatMessage(
            character=CharacterCode(char2_code),
            type=MessageType.GREETING,
            content=western_greeting,
            timestamp=now,
        ))

        # 마지막에 질문 제안 추가 (턴 마감용)
        category_questions = {
            FortuneCategory.LOVE: (
                "연애에서 특히 궁금한 점이 있으신가요? "
                "예를 들어, 이상형이나 연애 스타일에 대해 물어보셔도 좋소."
            ),
            FortuneCategory.MONEY: (
                "재물운에서 더 알고 싶은 부분이 있으신가요? "
                "투자 적기나 재물 운용법에 대해서도 말씀해 주시오."
            ),
            FortuneCategory.CAREER: (
                "직장운에서 궁금한 점이 있으신가요? "
                "이직 시기나 승진 가능성에 대해서도 여쭤보셔도 되오."
            ),
            FortuneCategory.HEALTH: (
                "건강운에서 더 알고 싶은 부분이 있으신가요? "
                "주의해야 할 신체 부위나 건강 습관에 대해 물어보셔도 좋소."
            ),
            FortuneCategory.STUDY: (
                "학업운에서 궁금한 점이 있으신가요? "
                "시험 운이나 집중력 향상법에 대해서도 말씀해 주시오."
            ),
            FortuneCategory.GENERAL: (
                "더 궁금한 점이 있으신가요? "
                "연애운, 재물운, 직장운 중 어느 것이 가장 궁금하신지 말씀해 주시오."
            ),
        }

        question_text = category_questions.get(
            category,
            category_questions[FortuneCategory.GENERAL],
        )
        messages.append(ChatMessage(
            character=CharacterCode(char1_code),
            type=MessageType.QUESTION,
            content=question_text,
            timestamp=now,
        ))

        logger.info(
            "category_greeting_complete",
            category=category.value,
            message_count=len(messages),
            fortune_source=source,
        )

        return messages, e_id, w_id, source

    def _format_eastern_context_for_category(
        self,
        eastern: EasternFortuneResponse,
        category: FortuneCategory,
    ) -> str:
        """카테고리별 동양 컨텍스트 생성"""

        base_context = self._format_eastern_context(eastern)

        # 카테고리별 추가 컨텍스트
        category_hints = {
            FortuneCategory.LOVE: """
애정운 관련 힌트:
- 십신 중 비견/겁재가 강하면 독립적 연애
- 식신/상관이 강하면 감성적 표현
- 재성이 강하면 현실적 연애
- 관성이 강하면 책임감 있는 연애
            """,
            FortuneCategory.CAREER: """
직장운 관련 힌트:
- 관성(정관/편관)이 강하면 조직 생활 적합
- 인성이 강하면 전문직/학술 분야
- 식상이 강하면 창작/표현 직업
- 재성이 강하면 사업/재무 분야
            """,
            FortuneCategory.MONEY: """
금전운 관련 힌트:
- 재성(정재/편재) 강도가 재물운 결정
- 식상이 재성을 생하면 재물 증가
- 비겁이 재성을 극하면 재물 손실 주의
            """,
            FortuneCategory.HEALTH: """
건강운 관련 힌트:
- 오행 균형이 건강의 핵심
- 약한 오행에 해당하는 장기 주의
- 강한 오행 과다 시 관련 질환 가능
            """,
            FortuneCategory.GENERAL: """
종합운 관련 힌트:
- 일간과 오행 균형을 종합적으로 고려
- 강점과 약점을 균형있게 언급
            """,
        }

        hint = category_hints.get(category, "")

        return f"""{base_context}

{hint}

현재 카테고리: {category.value}
지시사항: 위 사주 분석 결과를 바탕으로 {category.value}에 대한
개인화된 그리팅을 생성하세요. 일반론이 아닌 이 사람만의
구체적인 특징을 언급해야 합니다."""

    def _format_western_context_for_category(
        self,
        western: WesternFortuneDataV2,
        category: FortuneCategory,
    ) -> str:
        """카테고리별 서양 컨텍스트 생성"""

        base_context = self._format_western_context(western)

        # 카테고리별 추가 컨텍스트
        category_hints = {
            FortuneCategory.LOVE: """
애정운 관련 힌트:
- 금성 위치가 사랑 스타일 결정
- 달 별자리가 감정 표현 방식
- 7하우스가 관계 패턴
- 물 원소 강하면 감성적 사랑
            """,
            FortuneCategory.CAREER: """
직장운 관련 힌트:
- 태양 별자리가 직업 정체성
- 10하우스가 커리어 방향
- 불 원소 강하면 리더십 직업
- 흙 원소 강하면 실무/전문직
            """,
            FortuneCategory.MONEY: """
금전운 관련 힌트:
- 2하우스가 재물운
- 목성 위치가 행운/확장
- 토성 위치가 축적/절약
            """,
            FortuneCategory.HEALTH: """
건강운 관련 힌트:
- 6하우스가 건강 담당
- 태양 별자리별 건강 특성
- 원소 균형이 체질 결정
            """,
            FortuneCategory.GENERAL: """
종합운 관련 힌트:
- 태양, 달, 상승 별자리를 종합적으로 고려
- 4원소 균형과 주요 행성 배치
            """,
        }

        hint = category_hints.get(category, "")

        return f"""{base_context}

{hint}

현재 카테고리: {category.value}
지시사항: 위 점성술 분석 결과를 바탕으로 {category.value}에 대한
개인화된 그리팅을 생성하세요. 일반론이 아닌 이 사람만의
구체적인 별자리 조합을 언급해야 합니다."""

    def _truncate_message(self, text: str, max_length: int = 300) -> str:
        """메시지를 최대 길이로 자르되, 문장 단위로 자름

        Args:
            text: 원본 메시지
            max_length: 최대 길이 (기본값: 300자, 더 긴 응답 허용)

        Returns:
            잘린 메시지
        """
        if len(text) <= max_length:
            return text

        # 마지막 완전한 문장까지만 유지
        truncated = text[:max_length]
        # 다양한 문장 종결 패턴 검색 (오., 요., 소., 다., !., ?. 등)
        sentence_ends = [
            truncated.rfind('오.'),
            truncated.rfind('요.'),
            truncated.rfind('소.'),
            truncated.rfind('다.'),
            truncated.rfind('!'),
            truncated.rfind('?'),
            truncated.rfind('.'),
        ]
        last_period = max(sentence_ends)

        # 최소 절반 이상 위치에서 문장이 끝나면 그곳에서 자름
        if last_period > max_length // 2:
            return truncated[:last_period + 1]

        # 그렇지 않으면 마지막 완전한 단어에서 자름 (... 없이)
        last_space = truncated.rfind(' ')
        if last_space > 0:
            return truncated[:last_space]

        return truncated

    def _fallback_eastern_greeting(
        self,
        eastern: EasternFortuneResponse,
        category: FortuneCategory,
    ) -> str:
        """동양 그리팅 폴백 - 정규화된 컨텍스트 사용"""
        ctx = NormalizedEasternContext(eastern)

        category_msg = {
            FortuneCategory.LOVE: "애정운을 사주로 풀어보리다",
            FortuneCategory.CAREER: "직장운을 명리학으로 봐드리리다",
            FortuneCategory.MONEY: "금전운을 오행으로 해석해드리리다",
            FortuneCategory.HEALTH: "건강운을 사주로 살펴보리다",
            FortuneCategory.GENERAL: "전반적 운세를 봐드리리다",
        }

        return (
            f"{ctx.day_gan} 일간({ctx.day_element})이시오. "
            f"{category_msg.get(category, '운세를 봐드리리다')}."
        )

    def _fallback_western_greeting(
        self,
        western: WesternFortuneDataV2,
        category: FortuneCategory,
    ) -> str:
        """서양 그리팅 폴백 - 정규화된 컨텍스트 사용"""
        ctx = NormalizedWesternContext(western)

        category_msg = {
            FortuneCategory.LOVE: "애정운을 별자리로 분석해드릴게요",
            FortuneCategory.CAREER: "커리어를 행성 배치로 봐드릴게요",
            FortuneCategory.MONEY: "재물운을 점성술로 해석해드릴게요",
            FortuneCategory.HEALTH: "건강운을 차트로 살펴볼게요",
            FortuneCategory.GENERAL: "전반적 운세를 봐드릴게요",
        }

        return (
            f"{ctx.main_sign_name} 태양이시군요. "
            f"{category_msg.get(category, '운세를 봐드릴게요')}."
        )

    # ============================================================
    # 동적 카테고리 그리팅 (6-12개 버블, 대결/합의 모드)
    # ============================================================

    async def create_dynamic_category_greeting(
        self,
        birth_date: str,
        category: FortuneCategory,
        char1_code: str = "SOISEOL",
        char2_code: str = "STELLA",
        birth_time: str | None = None,
        birth_place: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        debate_ratio: float = 0.8,
        eastern_fortune_id: str | None = None,
        western_fortune_id: str | None = None,
        eastern_fortune_data: dict | None = None,
        western_fortune_data: dict | None = None,
    ) -> tuple[list[ChatMessage], str, str, str, dict]:
        """
        동적 카테고리 그리팅 생성 (6-12개 버블, 대결/합의 모드)

        연애 시뮬레이션 스타일의 생동감 있는 대화를 생성합니다.
        - 버블당 70-150자 (카톡 수준)
        - 대결 80% / 합의 20% 비율
        - 끼어들기, 감정 표현 지원

        Args:
            birth_date: 생년월일 (YYYY-MM-DD)
            category: 운세 카테고리
            char1_code: 첫 번째 캐릭터 코드 (동양)
            char2_code: 두 번째 캐릭터 코드 (서양)
            birth_time: 출생시간 (HH:MM)
            birth_place: 출생장소
            latitude: 위도
            longitude: 경도
            debate_ratio: 대결 비율 (0.0~1.0, 기본값 0.8)
            eastern_fortune_id: 기존 동양 운세 ID
            western_fortune_id: 기존 서양 운세 ID
            eastern_fortune_data: 동양 사주 분석 결과 (직접 전달)
            western_fortune_data: 서양 점성술 분석 결과 (직접 전달)

        Returns:
            (messages, eastern_id, western_id, source, metadata) 튜플
            metadata: {"debate_mode": "battle"|"consensus", "total_chars": int, "bubble_count": int}
        """
        logger.info(
            "dynamic_category_greeting_start",
            category=category.value,
            birth_date=birth_date,
            debate_ratio=debate_ratio,
        )

        # 1. 운세 분석 실행 또는 캐시 조회
        if eastern_fortune_data and western_fortune_data:
            # 직접 전달된 데이터 사용
            eastern_data = eastern_fortune_data
            if isinstance(eastern_fortune_data, dict) and "data" in eastern_fortune_data:
                eastern_data = eastern_fortune_data["data"]
            western_data = western_fortune_data
            if isinstance(western_fortune_data, dict) and "data" in western_fortune_data:
                western_data = western_fortune_data["data"]

            try:
                eastern_result = EasternFortuneResponse.model_validate(eastern_data)
            except Exception as e:
                logger.warning("eastern_fortune_validation_skip", error=str(e)[:100])
                eastern_result = (
                    DotDict(eastern_data)
                    if isinstance(eastern_data, dict)
                    else eastern_data  # type: ignore
                )
            try:
                western_result = WesternFortuneDataV2.model_validate(western_data)
            except Exception as e:
                logger.warning("western_fortune_validation_skip", error=str(e)[:100])
                western_result = (
                    DotDict(western_data)
                    if isinstance(western_data, dict)
                    else western_data  # type: ignore
                )

            e_id = eastern_fortune_id or str(uuid.uuid4())[:8]
            w_id = western_fortune_id or str(uuid.uuid4())[:8]
            store_fortune(e_id, eastern_result)
            store_fortune(w_id, western_result)
            source = "provided"
        else:
            eastern_result, western_result, e_id, w_id, source = await self.get_or_create_fortunes(
                birth_date=birth_date,
                birth_time=birth_time,
                birth_place=birth_place,
                latitude=latitude,
                longitude=longitude,
                eastern_fortune_id=eastern_fortune_id,
                western_fortune_id=western_fortune_id,
            )

        # 2. 동적 컨텍스트 생성 (카테고리별)
        eastern_context = self._format_eastern_context_for_dynamic(eastern_result, category)
        western_context = self._format_western_context_for_dynamic(western_result, category)

        # 3. LLM의 generate_dynamic_tikitaka 메서드 사용 (단순 프롬프트 + JSON 파싱 내장)
        now = datetime.now()
        messages: list[ChatMessage] = []
        metadata: dict = {
            "debate_mode": "battle",
            "total_chars": 0,
            "bubble_count": 0,
        }

        # 카테고리 한글명 매핑
        category_names = {
            FortuneCategory.LOVE: "연애운",
            FortuneCategory.CAREER: "직장운",
            FortuneCategory.MONEY: "금전운",
            FortuneCategory.HEALTH: "건강운",
            FortuneCategory.GENERAL: "종합운",
        }
        category_name = category_names.get(category, "운세")

        try:
            # LLM으로 동적 대화 생성 (내장 프롬프트 사용)
            result = await self.llm.generate_dynamic_tikitaka(
                char1_code=char1_code,
                char2_code=char2_code,
                category=category_name,
                eastern_context=eastern_context,
                western_context=western_context,
                debate_ratio=debate_ratio,
                min_chars=800,
                max_chars=1500,
            )

            lines = result.get("lines", [])
            user_prompt_text = result.get("user_prompt_text", "더 궁금한 점이 있으신가요?")
            metadata["debate_mode"] = result.get("debate_mode", "battle")

            # 라인을 ChatMessage로 변환
            messages = self._convert_dynamic_lines_to_messages(lines, user_prompt_text, now)

            # 버블 검증 및 조정
            messages = self._adjust_bubble_lengths(messages)

            # 메타데이터 계산
            metadata["bubble_count"] = len(messages)
            metadata["total_chars"] = sum(len(m.content) for m in messages)

            logger.info(
                "dynamic_greeting_generated",
                bubble_count=metadata["bubble_count"],
                total_chars=metadata["total_chars"],
                debate_mode=metadata["debate_mode"],
            )

        except Exception as e:
            logger.error("dynamic_greeting_error", error=str(e))
            # 폴백: 기존 create_category_greeting 로직 사용
            fallback_messages, _, _, _ = await self.create_category_greeting(
                birth_date=birth_date,
                category=category,
                char1_code=char1_code,
                char2_code=char2_code,
                birth_time=birth_time,
                eastern_fortune_id=e_id,
                western_fortune_id=w_id,
                eastern_fortune_data=eastern_fortune_data,
                western_fortune_data=western_fortune_data,
            )
            messages = fallback_messages
            metadata["bubble_count"] = len(messages)
            metadata["total_chars"] = sum(len(m.content) for m in messages)
            metadata["fallback"] = True

        return messages, e_id, w_id, source, metadata

    def _convert_dynamic_lines_to_messages(
        self,
        lines: list[dict],
        user_prompt_text: str,
        timestamp: datetime,
    ) -> list[ChatMessage]:
        """
        LLM 응답의 lines 배열을 ChatMessage 목록으로 변환

        Args:
            lines: [{"speaker": "SOISEOL", "text": "...", "emotion_code": "...", ...}, ...]
            user_prompt_text: 마지막 질문 텍스트
            timestamp: 메시지 타임스탬프

        Returns:
            ChatMessage 목록
        """
        messages: list[ChatMessage] = []

        for i, line in enumerate(lines):
            speaker = line.get("speaker", "SOISEOL")
            text = line.get("text", "")
            _emotion_code = line.get("emotion_code", "NEUTRAL")  # noqa: F841 향후 확장용
            is_interrupt = line.get("interrupt", False)

            # 유효성 검사
            if not text or len(text.strip()) < 5:
                continue

            # 노이즈 필터 적용
            text = fix_brackets(filter_prompt_leak(filter_noise(text, aggressive=True)))

            # 마지막 2개 라인 중 질문인지 확인
            is_question = i >= len(lines) - 2 and ("?" in text or "요?" in text or "가요?" in text)

            # 메시지 타입 결정
            if is_question:
                msg_type = MessageType.QUESTION
            elif is_interrupt:
                msg_type = MessageType.DEBATE  # 끼어들기는 토론으로 분류
            else:
                msg_type = MessageType.INTERPRETATION

            try:
                char_code = CharacterCode(speaker)
            except ValueError:
                char_code = CharacterCode.SOISEOL  # 폴백

            messages.append(ChatMessage(
                character=char_code,
                type=msg_type,
                content=text,
                timestamp=timestamp,
            ))

        # 마지막에 user_prompt_text가 있으면 질문으로 추가
        if user_prompt_text and len(messages) > 0:
            # 마지막 메시지가 이미 질문이 아닌 경우에만 추가
            if messages[-1].type != MessageType.QUESTION:
                last_speaker = messages[-1].character
                messages.append(ChatMessage(
                    character=last_speaker,
                    type=MessageType.QUESTION,
                    content=user_prompt_text,
                    timestamp=timestamp,
                ))

        return messages

    def _validate_bubble(self, text: str, min_chars: int = 70, max_chars: int = 150) -> bool:
        """버블 길이 검증

        Args:
            text: 버블 텍스트
            min_chars: 최소 길이 (기본값: 70)
            max_chars: 최대 길이 (기본값: 150)

        Returns:
            True if valid, False otherwise
        """
        length = len(text)
        return min_chars <= length <= max_chars

    def _adjust_bubble_lengths(self, messages: list[ChatMessage]) -> list[ChatMessage]:
        """버블 길이 조정 - 너무 길면 분할, 너무 짧으면 유지 (병합은 복잡하므로 생략)

        Args:
            messages: ChatMessage 목록

        Returns:
            조정된 ChatMessage 목록
        """
        adjusted: list[ChatMessage] = []
        max_chars = 200  # 버블 최대 길이 (약간 여유롭게)

        for msg in messages:
            if len(msg.content) > max_chars:
                # 긴 버블은 문장 단위로 분할
                split_msgs = self._split_long_bubble(msg, max_chars)
                adjusted.extend(split_msgs)
            else:
                adjusted.append(msg)

        return adjusted

    def _split_long_bubble(self, msg: ChatMessage, max_chars: int) -> list[ChatMessage]:
        """긴 버블을 문장 단위로 분할

        Args:
            msg: 원본 메시지
            max_chars: 최대 길이

        Returns:
            분할된 ChatMessage 목록
        """
        content = msg.content
        result: list[ChatMessage] = []

        # 문장 종결 패턴으로 분할
        import re
        sentences = re.split(r'(?<=[.!?요오다]) ', content)

        current_chunk = ""
        for sentence in sentences:
            if len(current_chunk) + len(sentence) + 1 <= max_chars:
                current_chunk = f"{current_chunk} {sentence}".strip() if current_chunk else sentence
            else:
                if current_chunk:
                    result.append(ChatMessage(
                        character=msg.character,
                        type=msg.type,
                        content=current_chunk,
                        timestamp=msg.timestamp,
                    ))
                current_chunk = sentence

        # 마지막 청크
        if current_chunk:
            result.append(ChatMessage(
                character=msg.character,
                type=msg.type,
                content=current_chunk,
                timestamp=msg.timestamp,
            ))

        # 분할 결과가 없으면 원본 그대로 (truncate)
        if not result:
            result.append(ChatMessage(
                character=msg.character,
                type=msg.type,
                content=self._truncate_message(content, max_chars),
                timestamp=msg.timestamp,
            ))

        return result

    def _format_eastern_context_for_dynamic(
        self,
        eastern: EasternFortuneResponse,
        category: FortuneCategory,
    ) -> str:
        """동적 그리팅용 동양 컨텍스트 생성 (카테고리별 힌트 포함)"""
        ctx = NormalizedEasternContext(eastern)

        base_context = (
            "## 사주 분석 결과\n"
            f"- 일간: {ctx.day_gan} ({ctx.day_element})\n"
            f"- 사주: {ctx.year_gan}{ctx.year_ji}년 {ctx.month_gan}{ctx.month_ji}월 "
            f"{ctx.day_gan_char}{ctx.day_ji}일\n"
            f"- 오행 분포: {ctx.five_elements_dominant} 우세\n"
            f"- 음양: 양 {ctx.yang}%, 음 {ctx.yin}%\n"
            f"- 강점: {ctx.strength}\n"
            f"- 약점: {ctx.weakness}\n"
            f"- 종합: {ctx.summary}"
        )

        # 카테고리별 힌트
        category_hints = {
            FortuneCategory.LOVE: f"""
## 애정운 분석 포인트
- 비견/겁재 강도 → 독립적 연애 성향
- 식신/상관 강도 → 감성 표현력
- 도화살 유무, 인연 시기
- 이 사람의 강점({ctx.strength})이 연애에 어떻게 작용하는지""",
            FortuneCategory.CAREER: f"""
## 직장운 분석 포인트
- 관성(정관/편관) 강도 → 조직 적응력
- 인성 강도 → 전문직/학술 적합도
- 승진/이직 시기
- 이 사람의 강점({ctx.strength})이 커리어에 어떻게 작용하는지""",
            FortuneCategory.MONEY: f"""
## 금전운 분석 포인트
- 재성(정재/편재) 강도 → 재물 획득력
- 식상이 재성을 생하는지 → 재물 증가 가능성
- 투자 적기, 횡재수
- 이 사람의 강점({ctx.strength})이 재물에 어떻게 작용하는지""",
            FortuneCategory.HEALTH: f"""
## 건강운 분석 포인트
- 오행 균형 상태 ({ctx.five_elements_dominant} 우세)
- 약한 오행 → 해당 장기 주의
- 건강 관리 방향
- 이 사람의 약점({ctx.weakness})과 건강의 연관성""",
            FortuneCategory.GENERAL: f"""
## 종합운 분석 포인트
- 일간({ctx.day_gan})과 오행 균형
- 강점과 약점의 조화
- 전반적인 기운의 흐름""",
            FortuneCategory.STUDY: """
## 학업운 분석 포인트
- 인성 강도 → 학습 집중력
- 식신 강도 → 창의적 사고
- 시험운, 집중력 향상 시기""",
        }

        hint = category_hints.get(category, category_hints[FortuneCategory.GENERAL])

        return f"{base_context}\n{hint}"

    def _format_western_context_for_dynamic(
        self,
        western: WesternFortuneDataV2,
        category: FortuneCategory,
    ) -> str:
        """동적 그리팅용 서양 컨텍스트 생성 (카테고리별 힌트 포함)"""
        ctx = NormalizedWesternContext(western)

        base_context = f"""## 점성술 분석 결과
- 태양 별자리: {ctx.main_sign_name}
- 우세 원소: {ctx.element}
- 원소 분석: {ctx.element_summary}
- 양태 분석: {ctx.modality_summary}
- 키워드: {', '.join(kw.label for kw in ctx.keywords) if ctx.keywords else ctx.keywords_summary}
- 개요: {ctx.overview}"""

        # 카테고리별 힌트
        category_hints = {
            FortuneCategory.LOVE: f"""
## 애정운 분석 포인트
- 금성 위치 → 사랑 스타일
- 달 별자리 → 감정 표현 방식
- 물/불 원소 비율 → 연애 열정도
- {ctx.main_sign_name}의 연애 특성과 키워드({ctx.keywords_summary})""",
            FortuneCategory.CAREER: f"""
## 직장운 분석 포인트
- 태양 별자리 → 직업 정체성
- 10하우스 → 커리어 방향
- 불/흙 원소 비율 → 리더십 vs 실무
- {ctx.main_sign_name}의 직업 특성""",
            FortuneCategory.MONEY: f"""
## 금전운 분석 포인트
- 2하우스 → 재물운
- 목성 위치 → 행운/확장
- 토성 위치 → 축적/절약
- {ctx.main_sign_name}의 재물 특성""",
            FortuneCategory.HEALTH: f"""
## 건강운 분석 포인트
- 6하우스 → 건강 담당
- {ctx.main_sign_name}의 건강 취약점
- 원소 균형 → 체질
- 건강 관리 조언""",
            FortuneCategory.GENERAL: """
## 종합운 분석 포인트
- 태양, 달, 상승 별자리 종합
- 4원소 균형
- 주요 행성 배치""",
            FortuneCategory.STUDY: """
## 학업운 분석 포인트
- 수성 위치 → 지적 능력
- 3하우스 → 커뮤니케이션/학습
- 공기 원소 비율 → 논리적 사고력""",
        }

        hint = category_hints.get(category, category_hints[FortuneCategory.GENERAL])

        return f"{base_context}\n{hint}"

    # ============================================================
    # 해석 메시지 생성
    # ============================================================

    async def create_interpretation_messages(
        self,
        eastern: EasternFortuneResponse,
        western: WesternFortuneDataV2,
        char1_code: str = "SOISEOL",
        char2_code: str = "STELLA",
        session: TikitakaSession | None = None,
    ) -> tuple[list[ChatMessage], ChatDebateStatus]:
        """
        LLM 기반 해석 메시지 생성

        Args:
            eastern: 동양 사주 분석 결과
            western: 서양 점성술 분석 결과
            char1_code: 첫 번째 캐릭터 코드 (기본값: SOISEOL)
            char2_code: 두 번째 캐릭터 코드 (기본값: STELLA)
            session: 세션 정보 (맥락 유지용)

        Returns:
            (메시지 목록, 토론 상태) 튜플
        """
        now = datetime.now()
        messages = []

        # 동양 컨텍스트 생성
        eastern_context = self._format_eastern_context(eastern)
        western_context = self._format_western_context(western)

        # 세션 맥락 추가 (있는 경우)
        if session:
            rich_context = session.get_rich_context()
            eastern_context = f"{eastern_context}\n\n{rich_context}"
            western_context = f"{western_context}\n\n{rich_context}"

        # 순차 생성 + 컨텍스트 체이닝 (동적 선택)
        try:
            # 1. 첫 번째 캐릭터(동양) 생성
            soiseol_msg = await self.llm.generate_character_message(
                char1_code, "기본 성격 분석", eastern_context
            )

            # 2. 두 번째 캐릭터(서양)에 첫 번째 발언 주입
            western_context_with_interaction = f"""{western_context}

## 상대 캐릭터의 직전 발언
"{soiseol_msg}"

## 지시
위 발언을 자연스럽게 받아서 대화하세요. 동의하거나 보완하는 방식으로."""

            stella_msg = await self.llm.generate_character_message(
                char2_code, "기본 성격 분석", western_context_with_interaction
            )
            # 노이즈 필터 + 프롬프트 누출 필터 + 빈 괄호 수정 적용
            soiseol_msg = fix_brackets(
                filter_prompt_leak(filter_noise(soiseol_msg, aggressive=True))
            )
            stella_msg = fix_brackets(
                filter_prompt_leak(filter_noise(stella_msg, aggressive=True))
            )

            # 빈 응답 체크 후 폴백 적용 - 정규화 컨텍스트 사용
            if not soiseol_msg or len(soiseol_msg.strip()) < 10:
                logger.warning(
                    "llm_empty_response",
                    character="soiseol",
                    response_len=len(soiseol_msg) if soiseol_msg else 0,
                )
                e_ctx = NormalizedEasternContext(eastern)
                soiseol_msg = f"{e_ctx.day_gan} 일간이시오. {e_ctx.strength}"
            if not stella_msg or len(stella_msg.strip()) < 10:
                logger.warning(
                    "llm_empty_response",
                    character="stella",
                    response_len=len(stella_msg) if stella_msg else 0,
                )
                w_ctx = NormalizedWesternContext(western)
                stella_msg = f"{w_ctx.main_sign_name} 태양이시군요. {w_ctx.element} 원소가 강해요."
        except Exception as e:
            logger.error("llm_interpretation_error", error=str(e))
            # 폴백 메시지 - 정규화 컨텍스트 사용
            e_ctx = NormalizedEasternContext(eastern)
            w_ctx = NormalizedWesternContext(western)
            soiseol_msg = f"{e_ctx.day_gan} 일간이시오. {e_ctx.strength}"
            stella_msg = f"{w_ctx.main_sign_name} 태양이시군요. {w_ctx.element} 원소가 강해요."

        messages.append(ChatMessage(
            character=CharacterCode(char1_code),
            type=MessageType.INTERPRETATION,
            content=soiseol_msg,
            timestamp=now,
        ))

        messages.append(ChatMessage(
            character=CharacterCode(char2_code),
            type=MessageType.INTERPRETATION,
            content=stella_msg,
            timestamp=now,
        ))

        # 공통점 찾기 (합의 포인트)
        consensus_point = self._find_consensus(eastern, western)

        if consensus_point:
            # 합의 메시지 (동적 캐릭터 이름 사용)
            char2_name = CHARACTER_NAMES.get(char2_code, char2_code)
            messages.append(ChatMessage(
                character=CharacterCode(char1_code),
                type=MessageType.CONSENSUS,
                content=(
                    f"{char2_name}도 비슷하게 보았구려. "
                    f"{consensus_point} 더 궁금한 운세가 있으시오?"
                ),
                timestamp=now,
            ))

            debate_status = ChatDebateStatus(
                is_consensus=True,
                eastern_opinion=eastern.stats.strength,
                western_opinion=western.fortune_content.overview,
                question="연애운, 직장운, 금전운 중 어떤 것이 가장 궁금하신가요?",
            )
        else:
            # 의견 차이 표시 (동적 캐릭터 이름 사용)
            char1_name = CHARACTER_NAMES.get(char1_code, char1_code)
            messages.append(ChatMessage(
                character=CharacterCode(char2_code),
                type=MessageType.DEBATE,
                content=(
                    f"{char1_name}과는 조금 다른 관점이에요. "
                    "동양과 서양이 보는 방식이 다르거든요."
                ),
                timestamp=now,
            ))

            debate_status = ChatDebateStatus(
                is_consensus=False,
                eastern_opinion=eastern.stats.strength,
                western_opinion=western.fortune_content.overview,
                question="어느 해석이 더 와닿으시나요?",
            )

        # 토론 결과 저장 (세션이 있는 경우)
        if session:
            session.add_debate_result(
                topic="기본 성격 분석",
                is_consensus=consensus_point is not None,
                eastern_point=eastern.stats.strength,
                western_point=western.fortune_content.overview,
                consensus_point=consensus_point,
            )

        # 매 턴 끝에 질문 제안 추가
        if session:
            suggested_q = _get_suggested_question(session.category, session.turn)
            messages.append(ChatMessage(
                character=CharacterCode(char1_code),
                type=MessageType.QUESTION,
                content=suggested_q,
                timestamp=now,
            ))

        return messages, debate_status

    def _format_eastern_context(self, eastern: EasternFortuneResponse) -> str:
        """동양 분석 컨텍스트 포맷팅 - 정규화된 컨텍스트 사용"""
        ctx = NormalizedEasternContext(eastern)

        return f"""일간: {ctx.day_gan} ({ctx.day_element})
사주: {ctx.year_gan}{ctx.year_ji}년 {ctx.month_gan}{ctx.month_ji}월 {ctx.day_gan_char}{ctx.day_ji}일
오행 분포: {ctx.five_elements_dominant} 우세
음양: 양 {ctx.yang}%, 음 {ctx.yin}%
강점: {ctx.strength}
약점: {ctx.weakness}"""

    def _format_western_context(self, western: WesternFortuneDataV2) -> str:
        """서양 분석 컨텍스트 포맷팅 (WesternFortuneDataV2 스키마 기준)"""
        stats = western.stats

        # 태양 별자리
        main_sign = stats.main_sign.name if hasattr(stats, 'main_sign') else "알 수 없음"

        # 4원소 분포에서 우세 원소 찾기
        dominant_elem = western.element  # 대표 원소
        if hasattr(stats, 'element_4_distribution') and stats.element_4_distribution:
            max_elem = max(stats.element_4_distribution, key=lambda x: x.percent)
            dominant_elem = max_elem.label

        # 운세 콘텐츠에서 요약 추출
        overview = ""
        if hasattr(western, 'fortune_content') and western.fortune_content:
            overview = western.fortune_content.overview

        return f"""태양: {main_sign}
우세 원소: {dominant_elem}
요약: {overview}"""

    def _find_consensus(
        self,
        eastern: EasternFortuneResponse,
        western: WesternFortuneDataV2,
    ) -> str | None:
        """
        동양/서양 분석에서 공통점 찾기 (WesternFortuneDataV2 스키마 기준)

        Returns:
            공통점 설명 또는 None
        """
        # 원소 매핑: 동양 오행 <-> 서양 4원소
        eastern_element = eastern.chart.day.element_code.value

        # WesternFortuneDataV2에서 우세 원소 추출
        western_dominant = western.element  # 대표 원소 (FIRE, EARTH, AIR, WATER)

        # 간단한 매핑
        element_match = {
            "WOOD": ["FIRE"],       # 목 -> 불
            "FIRE": ["FIRE"],       # 화 -> 불
            "EARTH": ["EARTH"],     # 토 -> 땅
            "METAL": ["AIR"],       # 금 -> 공기
            "WATER": ["WATER"],     # 수 -> 물
        }

        if western_dominant in element_match.get(eastern_element, []):
            return "둘 다 열정적이고 활동적인 에너지를 가지고 있다고 보이오."

        # 성격 키워드 매칭 (WesternFortuneDataV2에는 chart가 없으므로 stats.main_sign 사용)
        main_sign = western.stats.main_sign.name if hasattr(western.stats, 'main_sign') else ""

        # 불 별자리 매핑 (한글)
        fire_signs = ["양자리", "사자자리", "사수자리"]
        water_signs = ["물고기자리", "게자리", "전갈자리"]

        if "리더" in eastern.stats.strength.lower() or "추진" in eastern.stats.strength.lower():
            if main_sign in fire_signs:
                return "둘 다 리더십과 추진력이 강하다고 보이오."

        # 창의성
        if "창의" in eastern.stats.strength.lower() or "예술" in eastern.stats.strength.lower():
            if main_sign in water_signs:
                return "둘 다 창의적이고 감성적인 면이 있다고 보이오."

        return None

    # ============================================================
    # 주제별 해석
    # ============================================================

    async def create_topic_messages(
        self,
        topic: str,
        eastern: EasternFortuneResponse,
        western: WesternFortuneDataV2,
        char1_code: str = "SOISEOL",
        char2_code: str = "STELLA",
        session: TikitakaSession | None = None,
    ) -> tuple[list[ChatMessage], ChatDebateStatus, ChatUIHints]:
        """
        특정 주제에 대한 해석 생성

        Args:
            topic: 주제 (연애운, 직장운, 금전운 등)
            eastern: 동양 분석 결과
            western: 서양 분석 결과
            char1_code: 첫 번째 캐릭터 코드 (기본값: SOISEOL)
            char2_code: 두 번째 캐릭터 코드 (기본값: STELLA)
            session: 세션 정보 (맥락 유지용)

        Returns:
            (메시지 목록, 토론 상태, UI 힌트) 튜플
        """
        now = datetime.now()
        messages = []

        # 주제별 컨텍스트
        eastern_context = self._format_eastern_context(eastern)
        western_context = self._format_western_context(western)

        # 세션 맥락 추가 (이전 토론 이력 참조)
        if session:
            rich_context = session.get_rich_context()

            # 이전 토론 이력에서 맥락 추가
            context_prefix = ""
            if session.debate_history:
                prev_topics = [d["topic"] for d in session.debate_history[-3:]]
                if prev_topics:
                    context_prefix = f"[이전 대화: {', '.join(prev_topics)}에 대해 논의했음]\n"

            eastern_context = f"{context_prefix}{eastern_context}\n\n{rich_context}"
            western_context = f"{context_prefix}{western_context}\n\n{rich_context}"

        # LLM으로 주제별 해석 생성 (순차 생성 + 컨텍스트 체이닝)
        try:
            # 1. 첫 번째 캐릭터(동양) 생성
            soiseol_msg = await self.llm.generate_character_message(
                char1_code, topic, eastern_context
            )

            # 2. 두 번째 캐릭터(서양)에 첫 번째 발언 주입
            western_context_with_interaction = f"""{western_context}

## 상대 캐릭터의 직전 발언
"{soiseol_msg}"

## 지시
위 발언을 자연스럽게 받아서 대화하세요. 동의하거나 보완하는 방식으로."""

            stella_msg = await self.llm.generate_character_message(
                char2_code, topic, western_context_with_interaction
            )
            # 노이즈 필터 + 프롬프트 누출 필터 + 빈 괄호 수정 적용
            soiseol_msg = fix_brackets(
                filter_prompt_leak(filter_noise(soiseol_msg, aggressive=True))
            )
            stella_msg = fix_brackets(
                filter_prompt_leak(filter_noise(stella_msg, aggressive=True))
            )
            # 메시지 길이 제한 (150자)
            soiseol_msg = self._truncate_message(soiseol_msg, max_length=150)
            stella_msg = self._truncate_message(stella_msg, max_length=150)

            # 빈 응답 체크 후 폴백 적용
            if not soiseol_msg or len(soiseol_msg.strip()) < 10:
                logger.warning(
                    "llm_empty_response",
                    character="soiseol",
                    topic=topic,
                    response_len=len(soiseol_msg) if soiseol_msg else 0,
                )
                soiseol_msg = f"{topic}에 대해 좋은 기운이 흐르고 있소."
            if not stella_msg or len(stella_msg.strip()) < 10:
                logger.warning(
                    "llm_empty_response",
                    character="stella",
                    topic=topic,
                    response_len=len(stella_msg) if stella_msg else 0,
                )
                stella_msg = f"{topic} 분석 결과는 긍정적이에요."
        except Exception as e:
            logger.error("topic_interpretation_error", error=str(e), topic=topic)
            # 폴백 메시지 (페르소나 적용)
            soiseol_msg = f"{topic}에 대해 좋은 기운이 흐르고 있소."  # 하오체
            stella_msg = f"{topic} 분석 결과는 긍정적이에요."  # 해요체

        messages.append(ChatMessage(
            character=CharacterCode(char1_code),
            type=MessageType.INTERPRETATION,
            content=soiseol_msg,
            timestamp=now,
        ))

        messages.append(ChatMessage(
            character=CharacterCode(char2_code),
            type=MessageType.INTERPRETATION,
            content=stella_msg,
            timestamp=now,
        ))

        # 의견 비교 (간단한 로직)
        # 실제로는 LLM으로 의견 비교 분석 가능
        import random
        is_consensus = random.random() > 0.3  # 70% 확률로 합의

        if is_consensus:
            # 합의 상태 (고정 멘트 제거 - LLM 생성으로 대체)
            debate_status = ChatDebateStatus(
                is_consensus=True,
                eastern_opinion=soiseol_msg,
                western_opinion=stella_msg,
                question="다른 궁금한 점이 있으신가요?",
            )
            ui_hints = ChatUIHints()
        else:
            # 선택형 UI (동적 캐릭터 이름 사용)
            char1_name = CHARACTER_NAMES.get(char1_code, char1_code)
            char2_name = CHARACTER_NAMES.get(char2_code, char2_code)
            debate_status = ChatDebateStatus(
                is_consensus=False,
                eastern_opinion=soiseol_msg,
                western_opinion=stella_msg,
                question="어느 해석이 더 와닿으시나요?",
            )
            ui_hints = ChatUIHints(
                show_choice=True,
                choices=[
                    ChoiceOption(
                        value=1,
                        character=CharacterCode(char1_code),
                        label=f"{char1_name}의 해석",
                    ),
                    ChoiceOption(
                        value=2,
                        character=CharacterCode(char2_code),
                        label=f"{char2_name}의 해석",
                    ),
                ],
            )

        # 토론 결과 저장 (세션이 있는 경우)
        if session:
            session.add_debate_result(
                topic=topic,
                is_consensus=is_consensus,
                eastern_point=soiseol_msg,
                western_point=stella_msg,
                consensus_point=f"{topic}에 대해 긍정적" if is_consensus else None,
            )

        # 매 턴 끝에 질문 제안 추가
        if session:
            suggested_q = _get_suggested_question(session.category, session.turn)
            messages.append(ChatMessage(
                character=CharacterCode(char1_code),
                type=MessageType.QUESTION,
                content=suggested_q,
                timestamp=now,
            ))

        return messages, debate_status, ui_hints

    # ============================================================
    # 선택 응답
    # ============================================================

    async def handle_choice(
        self,
        choice: int,
        topic: str,
        session: TikitakaSession,
        char1_code: str = "SOISEOL",
        char2_code: str = "STELLA",
    ) -> list[ChatMessage]:
        """
        사용자 선택에 대한 응답

        Args:
            choice: 1 (첫 번째 캐릭터) 또는 2 (두 번째 캐릭터)
            topic: 현재 주제
            session: 세션 정보
            char1_code: 첫 번째 캐릭터 코드 (기본값: SOISEOL)
            char2_code: 두 번째 캐릭터 코드 (기본값: STELLA)

        Returns:
            응답 메시지 목록
        """
        now = datetime.now()

        # 사용자 선호도 업데이트
        session.update_user_preference(choice, char1_code, char2_code)

        # 풍부한 컨텍스트 사용
        rich_context = session.get_rich_context()

        if choice == 1:
            # 첫 번째 캐릭터 선택
            try:
                response = await self.llm.generate_character_message(
                    char1_code,
                    f"{topic} 추가 조언",
                    rich_context,
                )
                # 노이즈 필터 + 프롬프트 누출 필터 + 빈 괄호 수정 적용
                response = fix_brackets(
                    filter_prompt_leak(filter_noise(response, aggressive=True))
                )

                # 빈 응답 체크 후 폴백 적용
                if not response or len(response.strip()) < 10:
                    logger.warning(
                        "llm_empty_response",
                        character=char1_code,
                        topic=topic,
                        response_len=len(response) if response else 0,
                    )
                    response = "현명한 선택이오. 동양의 지혜가 귀하와 함께할 것이오."
            except Exception:
                # 폴백 메시지
                response = "현명한 선택이오. 동양의 지혜가 귀하와 함께할 것이오."

            return [ChatMessage(
                character=CharacterCode(char1_code),
                type=MessageType.INTERPRETATION,
                content=response,
                timestamp=now,
            )]
        else:
            # 두 번째 캐릭터 선택
            try:
                response = await self.llm.generate_character_message(
                    char2_code,
                    f"{topic} 추가 분석",
                    rich_context,
                )
                # 노이즈 필터 + 프롬프트 누출 필터 + 빈 괄호 수정 적용
                response = fix_brackets(
                    filter_prompt_leak(filter_noise(response, aggressive=True))
                )

                # 빈 응답 체크 후 폴백 적용
                if not response or len(response.strip()) < 10:
                    logger.warning(
                        "llm_empty_response",
                        character=char2_code,
                        topic=topic,
                        response_len=len(response) if response else 0,
                    )
                    response = "현명한 판단이에요. 별의 인도를 따라가세요."
            except Exception:
                # 폴백 메시지
                response = "현명한 판단이에요. 별의 인도를 따라가세요."

            return [ChatMessage(
                character=CharacterCode(char2_code),
                type=MessageType.INTERPRETATION,
                content=response,
                timestamp=now,
            )]

    # ============================================================
    # 스트리밍 생성
    # ============================================================

    async def stream_interpretation(
        self,
        eastern: EasternFortuneResponse,
        western: WesternFortuneDataV2,
        char1_code: str = "SOISEOL",
        char2_code: str = "STELLA",
    ) -> AsyncGenerator[dict, None]:
        """
        해석 메시지 스트리밍 생성기

        SSE 이벤트 형식으로 메시지를 순차적으로 생성

        Args:
            eastern: 동양 사주 분석 결과
            western: 서양 점성술 분석 결과
            char1_code: 첫 번째 캐릭터 코드 (기본값: SOISEOL)
            char2_code: 두 번째 캐릭터 코드 (기본값: STELLA)

        Yields:
            SSE 이벤트 데이터
        """
        now = datetime.now()

        # 1. 첫 번째 캐릭터 해석 시작
        yield {
            "event": "message_start",
            "data": {
                "character": char1_code,
                "type": "INTERPRETATION",
            },
        }

        # 동양/서양 컨텍스트
        eastern_context = self._format_eastern_context(eastern)
        western_context = self._format_western_context(western)

        # P3 비동기 최적화: 캐릭터 메시지 병렬 생성 (초기 응답 50% 단축)
        # 정규화 컨텍스트 미리 생성 (폴백용)
        e_ctx = NormalizedEasternContext(eastern)
        w_ctx = NormalizedWesternContext(western)

        async def _generate_char1() -> str:
            fallback_msg = f"{e_ctx.day_gan} 일간이시구려. {e_ctx.strength}"
            try:
                msg = await self.llm.generate_character_message(
                    char1_code,
                    "기본 성격 분석",
                    eastern_context,
                )
                # 노이즈 필터 + 프롬프트 누출 필터 + 빈 괄호 수정 적용
                msg = fix_brackets(filter_prompt_leak(filter_noise(msg, aggressive=True)))

                # 빈 응답 체크 후 폴백 적용
                if not msg or len(msg.strip()) < 10:
                    logger.warning(
                        "llm_empty_response",
                        character=char1_code,
                        context="streaming",
                        response_len=len(msg) if msg else 0,
                    )
                    return fallback_msg
                return msg
            except Exception:
                return fallback_msg

        async def _generate_char2() -> str:
            fallback_msg = f"{w_ctx.main_sign_name} 태양이시군요. 분석해볼게요."
            try:
                msg = await self.llm.generate_character_message(
                    char2_code,
                    "기본 성격 분석",
                    western_context,
                )
                # 노이즈 필터 + 프롬프트 누출 필터 + 빈 괄호 수정 적용
                msg = fix_brackets(filter_prompt_leak(filter_noise(msg, aggressive=True)))

                # 빈 응답 체크 후 폴백 적용
                if not msg or len(msg.strip()) < 10:
                    logger.warning(
                        "llm_empty_response",
                        character=char2_code,
                        context="streaming",
                        response_len=len(msg) if msg else 0,
                    )
                    return fallback_msg
                return msg
            except Exception:
                return fallback_msg

        # 병렬 생성
        soiseol_msg, stella_msg = await asyncio.gather(
            _generate_char1(),
            _generate_char2(),
        )

        # 순차 스트리밍 (UX 유지: 첫 번째 캐릭터 먼저, 두 번째 나중)
        for i in range(0, len(soiseol_msg), 20):
            chunk = soiseol_msg[i:i+20]
            yield {
                "event": "message_chunk",
                "data": {
                    "character": char1_code,
                    "content": chunk,
                },
            }
            await asyncio.sleep(0.05)

        yield {
            "event": "message_end",
            "data": {
                "character": char1_code,
                "content": soiseol_msg,
                "timestamp": now.isoformat(),
            },
        }

        # 2. 두 번째 캐릭터 해석
        yield {
            "event": "message_start",
            "data": {
                "character": char2_code,
                "type": "INTERPRETATION",
            },
        }

        for i in range(0, len(stella_msg), 20):
            chunk = stella_msg[i:i+20]
            yield {
                "event": "message_chunk",
                "data": {
                    "character": char2_code,
                    "content": chunk,
                },
            }
            await asyncio.sleep(0.05)

        yield {
            "event": "message_end",
            "data": {
                "character": char2_code,
                "content": stella_msg,
                "timestamp": now.isoformat(),
            },
        }

        # 3. 합의/토론 상태
        consensus_point = self._find_consensus(eastern, western)

        yield {
            "event": "debate_status",
            "data": {
                "is_consensus": consensus_point is not None,
                "eastern_opinion": eastern.stats.strength,
                "western_opinion": western.fortune_content.overview,
                "question": "더 궁금한 운세가 있으신가요?",
            },
        }

        # 4. 완료
        yield {
            "event": "complete",
            "data": {
                "status": "success",
            },
        }

    # ============================================================
    # 동적 버블 생성 (멀티-콜 방식)
    # ============================================================

    async def create_dynamic_bubbles(
        self,
        category: FortuneCategory,
        eastern_result: "EasternFortuneResponse",
        western_result: "WesternFortuneDataV2",
        char1_code: str = "SOISEOL",
        char2_code: str = "STELLA",
        mode: str | None = None,  # None이면 랜덤 (80% battle, 20% consensus)
        min_bubbles: int = 3,
        max_bubbles: int = 6,
    ) -> list[ChatMessage]:
        """동적 버블 생성 (멀티-콜 방식)

        LLM을 여러 번 호출하여 자연스러운 대화 흐름 생성.
        각 호출은 1개 버블만 생성하므로 JSON 파싱 문제 없음.

        Args:
            category: 운세 카테고리
            eastern_result: 동양 운세 결과
            western_result: 서양 운세 결과
            char1_code: 첫 번째 캐릭터 (동양 계열)
            char2_code: 두 번째 캐릭터 (서양 계열)
            mode: 대화 모드 (battle/consensus, None이면 랜덤)
            min_bubbles: 최소 버블 수
            max_bubbles: 최대 버블 수

        Returns:
            생성된 ChatMessage 리스트
        """
        import random

        # 1. 모드 결정 (80% battle, 20% consensus)
        if mode is None:
            mode = "battle" if random.random() < 0.8 else "consensus"

        # 2. 버블 수 결정 (동적)
        num_bubbles = random.randint(min_bubbles, max_bubbles)

        # 3. 발화 패턴 생성 (동적, 비고정)
        speaker_pattern = self._generate_speaker_pattern(
            char1_code, char2_code, num_bubbles, mode
        )

        # 4. 컨텍스트 준비
        topic = category.value if hasattr(category, 'value') else str(category)
        char1_context = self._format_context_for_character(
            char1_code, eastern_result, western_result, category
        )
        char2_context = self._format_context_for_character(
            char2_code, eastern_result, western_result, category
        )

        logger.info(
            "dynamic_bubbles_start",
            mode=mode,
            num_bubbles=num_bubbles,
            pattern=[s[0] for s in speaker_pattern],
        )

        # 5. 순차적으로 버블 생성 (이전 대화를 컨텍스트로)
        messages: list[ChatMessage] = []
        conversation_history: list[tuple[str, str]] = []

        for i, (speaker_code, instruction_key) in enumerate(speaker_pattern):
            # 발화자에 따라 컨텍스트 결정
            if speaker_code == char1_code:
                char_context = char1_context
                opponent_context = char2_context
                opponent_code = char2_code
            else:
                char_context = char2_context
                opponent_context = char1_context
                opponent_code = char1_code

            try:
                # LLM 호출 (단일 버블)
                text = await self.llm.generate_single_bubble(
                    char_code=speaker_code,
                    opponent_code=opponent_code,
                    char_context=char_context,
                    opponent_context=opponent_context,
                    topic=topic,
                    mode=mode,
                    instruction_key=instruction_key,
                    conversation_history=conversation_history,
                )

                # 대화 히스토리에 추가
                conversation_history.append((speaker_code, text))

                # ChatMessage 생성
                message = ChatMessage(
                    id=f"dyn_{i}_{speaker_code[:3].lower()}",
                    character=CharacterCode(speaker_code),
                    content=text,
                    message_type=MessageType.CHARACTER,
                    timestamp=datetime.now(),
                    emotion_code="NEUTRAL",  # 간소화
                    emotion_intensity=0.7,
                )
                messages.append(message)

                logger.debug(
                    "dynamic_bubble_generated",
                    index=i,
                    speaker=speaker_code,
                    text_len=len(text),
                )

            except Exception as e:
                logger.error(
                    "dynamic_bubble_error",
                    index=i,
                    speaker=speaker_code,
                    error=str(e),
                )
                # 에러 시 폴백 메시지
                fallback_text = self._get_bubble_fallback(speaker_code, mode)
                conversation_history.append((speaker_code, fallback_text))

                message = ChatMessage(
                    id=f"dyn_{i}_{speaker_code[:3].lower()}_fb",
                    character=CharacterCode(speaker_code),
                    content=fallback_text,
                    message_type=MessageType.CHARACTER,
                    timestamp=datetime.now(),
                    emotion_code="NEUTRAL",
                    emotion_intensity=0.5,
                )
                messages.append(message)

        logger.info(
            "dynamic_bubbles_complete",
            total_messages=len(messages),
            mode=mode,
        )

        return messages

    def _generate_speaker_pattern(
        self,
        char1_code: str,
        char2_code: str,
        num_bubbles: int,
        mode: str,
    ) -> list[tuple[str, str]]:
        """동적 발화 패턴 생성

        고정 패턴(동→서→동) 대신 다양한 패턴 생성:
        - 동→서→동→서 (기본 교차)
        - 동→동→서 (한 캐릭터가 연속 발화)
        - 동→서→서→동 (상대가 연속 반박)

        Returns:
            [(speaker_code, instruction_key), ...] 리스트
        """
        import random

        pattern: list[tuple[str, str]] = []

        # 첫 발화자는 랜덤 (50:50)
        current_speaker = char1_code if random.random() < 0.5 else char2_code
        other_speaker = char2_code if current_speaker == char1_code else char1_code

        # 모드별 instruction 세트
        if mode == "battle":
            instructions = ["battle_attack", "battle_defend", "battle_concede"]
        else:  # consensus
            instructions = ["consensus_agree", "consensus_add"]

        for i in range(num_bubbles):
            # instruction 선택
            if i == 0:
                instruction = "intro_first"
            elif i == num_bubbles - 1:
                # 마지막은 질문으로 끝날 확률 50%
                if random.random() < 0.5:
                    instruction = "question_ask"
                else:
                    instruction = random.choice(instructions)
            else:
                instruction = random.choice(instructions)

            pattern.append((current_speaker, instruction))

            # 다음 발화자 결정
            # 70% 확률로 교차, 30% 확률로 동일 캐릭터 연속 (최대 2회)
            consecutive_count = sum(1 for s, _ in pattern[-2:] if s == current_speaker)

            if consecutive_count >= 2 or random.random() < 0.7:
                # 교차
                current_speaker, other_speaker = other_speaker, current_speaker
            # else: 동일 캐릭터 연속

        return pattern

    def _format_context_for_character(
        self,
        char_code: str,
        eastern_result: "EasternFortuneResponse",
        western_result: "WesternFortuneDataV2",
        category: FortuneCategory,
    ) -> str:
        """캐릭터별 운세 컨텍스트 포맷팅"""
        # 동양 계열 캐릭터
        if char_code in ("SOISEOL", "CHEONGWOON", "HWARIN"):
            return self._format_eastern_context_brief(eastern_result, category)
        # 서양 계열 캐릭터
        else:
            return self._format_western_context_brief(western_result, category)

    def _format_eastern_context_brief(
        self,
        result: "EasternFortuneResponse",
        category: FortuneCategory,
    ) -> str:
        """동양 운세 컨텍스트 (간략)"""
        lines = []

        try:
            # 사주 기본 정보
            if hasattr(result, 'chart') and result.chart:
                chart = result.chart
                if hasattr(chart, 'day_master'):
                    lines.append(f"일간: {_safe_get_hangul(chart.day_master)}")

            # 오행 분포
            if hasattr(result, 'stats') and result.stats:
                stats = result.stats
                if hasattr(stats, 'elements') and stats.elements:
                    elem_str = ", ".join(
                        f"{_safe_get_label(e.element)}({e.percentage:.0f}%)"
                        for e in stats.elements[:3]
                    )
                    lines.append(f"오행: {elem_str}")

            # 카테고리별 포인트
            if hasattr(result, 'interpretations') and result.interpretations:
                interp = result.interpretations
                cat_map = {
                    FortuneCategory.LOVE: 'love',
                    FortuneCategory.WEALTH: 'wealth',
                    FortuneCategory.CAREER: 'career',
                    FortuneCategory.HEALTH: 'health',
                }
                cat_key = cat_map.get(category, 'general')
                if hasattr(interp, cat_key):
                    cat_interp = getattr(interp, cat_key)
                    if hasattr(cat_interp, 'summary'):
                        lines.append(f"요약: {cat_interp.summary[:100]}")
        except Exception as e:
            logger.warning("eastern_context_format_error", error=str(e))
            lines.append("사주 정보 분석 중")

        return "\n".join(lines) or "사주 정보 로딩 중"

    def _format_western_context_brief(
        self,
        result: "WesternFortuneDataV2",
        category: FortuneCategory,
    ) -> str:
        """서양 운세 컨텍스트 (간략)"""
        lines = []

        try:
            # 태양 별자리
            if hasattr(result, 'sun_sign'):
                lines.append(f"태양: {result.sun_sign}")

            # 달 별자리
            if hasattr(result, 'moon_sign'):
                lines.append(f"달: {result.moon_sign}")

            # 상승궁
            if hasattr(result, 'ascendant'):
                lines.append(f"상승: {result.ascendant}")

            # 키워드
            if hasattr(result, 'keywords') and result.keywords:
                kw_str = ", ".join(
                    kw.label if hasattr(kw, 'label') else str(kw)
                    for kw in result.keywords[:3]
                )
                lines.append(f"키워드: {kw_str}")
        except Exception as e:
            logger.warning("western_context_format_error", error=str(e))
            lines.append("점성술 정보 분석 중")

        return "\n".join(lines) or "점성술 정보 로딩 중"

    def _get_bubble_fallback(self, char_code: str, mode: str) -> str:
        """버블 생성 실패 시 폴백"""
        fallbacks = {
            "SOISEOL": {
                "battle": "허허, 그 점은 다시 살펴봐야겠소.",
                "consensus": "그렇구려, 같은 흐름을 보았소.",
            },
            "STELLA": {
                "battle": "음, 저는 다른 별을 보고 있어요.",
                "consensus": "맞아요! 별들이 같은 걸 말하고 있어요!",
            },
            "CHEONGWOON": {
                "battle": "허허, 재미있는 견해로다.",
                "consensus": "뜻밖에 의견이 맞는구려.",
            },
            "HWARIN": {
                "battle": "그건 좀 아닌 것 같은데요?",
                "consensus": "오, 생각이 같네요!",
            },
            "KYLE": {
                "battle": "에이, 그건 아니지~",
                "consensus": "오, 맞아맞아!",
            },
            "ELARIA": {
                "battle": "다른 관점도 있어요.",
                "consensus": "놀라워요, 같은 별을 봤네요!",
            },
        }
        char_fb = fallbacks.get(char_code, fallbacks["SOISEOL"])
        return char_fb.get(mode, char_fb.get("battle", "흥미롭구려."))

    # ============================================================
    # LLM Provider 통합 메서드 (GPT-5-mini / 8B vLLM 전환)
    # ============================================================

    async def _get_chat_provider(self) -> OpenAIProvider | VLLMProvider:
        """채팅용 LLM Provider 반환 (플래그 기반 선택)

        USE_GPT5MINI_FOR_CHAT 환경변수에 따라:
        - True + OPENAI_API_KEY 있음: GPT-5-mini
        - False 또는 API 키 없음: 8B vLLM

        Returns:
            OpenAIProvider 또는 VLLMProvider
        """
        if self._settings.use_gpt5mini_for_chat and self._settings.openai_api_key:
            # GPT-5-mini 사용
            return await self._get_openai_provider()
        else:
            # 8B vLLM 사용
            return await self._get_vllm_provider()

    async def _get_openai_provider(self) -> OpenAIProvider:
        """GPT-5-mini Provider 반환 (lazy init)"""
        if self._openai_provider is None:
            self._openai_provider = OpenAIProvider(
                OpenAIConfig(
                    api_key=self._settings.openai_api_key,
                    model=self._settings.openai_model,  # 환경변수에서 로드
                    api_timeout=300.0,  # 5분 타임아웃 (그리팅 생성 시간 고려)
                )
            )
            await self._openai_provider.start()
            logger.info("openai_provider_started", model=self._settings.openai_model)
        return self._openai_provider

    async def _get_vllm_provider(self) -> VLLMProvider:
        """8B vLLM Provider 반환 (lazy init)"""
        if self._vllm_provider is None:
            self._vllm_provider = VLLMProvider(
                VLLMConfig(
                    base_url=self._settings.vllm_base_url,
                    model=self._settings.vllm_model,
                )
            )
            await self._vllm_provider.start()
            logger.info("vllm_provider_started", model=self._settings.vllm_model)
        return self._vllm_provider

    async def generate_multi_bubble_response(
        self,
        prompt: str,
        context: str = "",
    ) -> list:
        """GPT-5-mini를 사용해 멀티 버블 응답 생성

        Args:
            prompt: 사용자 프롬프트
            context: 추가 컨텍스트 (운세 데이터 등)

        Returns:
            ParsedBubble 리스트 (파서 사용 가능 시) 또는 빈 리스트
        """
        if not BUBBLE_PARSER_AVAILABLE:
            logger.warning("버블 파서 모듈이 없습니다")
            return []

        provider = await self._get_chat_provider()

        full_prompt = prompt
        if context:
            full_prompt = f"{context}\n\n{prompt}"

        messages = [
            {"role": "system", "content": MULTI_BUBBLE_SYSTEM_PROMPT},
            {"role": "user", "content": full_prompt},
        ]

        try:
            response = await provider.chat(messages)
            bubbles = self._bubble_parser.feed(response.text)
            self._bubble_parser.reset()

            logger.info(
                "멀티 버블 응답 생성 완료",
                bubble_count=len(bubbles),
                raw_length=len(response.text),
            )

            return bubbles
        except Exception as e:
            provider_type = "GPT-5-mini" if self._settings.use_gpt5mini_for_chat else "8B vLLM"
            logger.error(f"{provider_type} 호출 실패", error=str(e))
            return []

    async def close_providers(self):
        """LLM Provider 정리 (OpenAI, vLLM 모두)"""
        if self._openai_provider is not None:
            await self._openai_provider.stop()
            self._openai_provider = None
        if self._vllm_provider is not None:
            await self._vllm_provider.stop()
            self._vllm_provider = None

    # 하위 호환성을 위한 별칭
    async def close_openai_provider(self):
        """OpenAI Provider 정리 (deprecated, use close_providers)"""
        await self.close_providers()

    async def create_tikitaka_messages_gpt5mini(
        self,
        topic: str,
        eastern_context: str,
        western_context: str,
        mode: str = "battle",
        char1_code: str = "SOISEOL",
        char2_code: str = "STELLA",
        is_first_turn: bool = False,
        is_last_turn: bool = False,
        user_question: str = "",
        session_id: str = "",
        category: str = "GENERAL",
        turn: int = 0,
        conversation_history: str = "",
    ) -> tuple[list[ChatMessage], ChatDebateStatus]:
        """GPT-5-mini를 사용한 티키타카 메시지 생성

        다층 XML 프롬프트 시스템을 사용하여 GPT-5-mini에 최적화된 응답을 생성합니다.

        Args:
            topic: 주제 (total, love, wealth, career, health)
            eastern_context: 동양 운세 컨텍스트
            western_context: 서양 운세 컨텍스트
            mode: 대화 모드 (battle, consensus)
            char1_code: 캐릭터1 코드 (기본값: SOISEOL)
            char2_code: 캐릭터2 코드 (기본값: STELLA)
            is_first_turn: 첫 턴 여부
            is_last_turn: 마지막 턴 여부
            user_question: 사용자 질문 (Layer 5 - 사용자 입력)
            session_id: 세션 ID (토큰 통계용)
            category: 운세 카테고리 (토큰 통계용)
            turn: 현재 턴 번호 (토큰 통계용)
            conversation_history: 이전 대화 내역 (최근 6개 메시지)

        Returns:
            (메시지 목록, 토론 상태) 튜플
        """
        logger.info(
            "GPT-5-mini 티키타카 생성 시작",
            topic=topic,
            mode=mode,
            char1=char1_code,
            char2=char2_code,
        )

        # 채팅 Provider 가져오기 (GPT-5-mini 또는 8B vLLM)
        provider = await self._get_chat_provider()

        # 모드 결정 (첫/마지막 턴 고려)
        actual_mode = mode
        if is_first_turn:
            actual_mode = "greeting"
        elif is_last_turn:
            actual_mode = "end"

        # XML 프롬프트 생성 (gpt5mini_prompts.py)
        system_prompt, user_prompt = build_gpt5mini_tikitaka_prompt(
            topic=topic,
            eastern_context=eastern_context,
            western_context=western_context,
            mode=actual_mode,
            char1_code=char1_code,
            char2_code=char2_code,
            user_question=user_question,
            conversation_history=conversation_history,
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        # 프롬프트 원문 로깅 (디버깅용)
        logger.info(
            "GPT-5-mini_prompt_debug",
            session_id=session_id,
            turn=turn,
            mode=actual_mode,
            system_prompt_len=len(system_prompt),
            user_prompt_len=len(user_prompt),
            total_prompt_len=len(system_prompt) + len(user_prompt),
            conversation_history_len=len(conversation_history),
            user_question=user_question[:100] if user_question else "",
            system_prompt_preview=system_prompt[:500],
            user_prompt_preview=user_prompt[:500],
        )

        try:
            # LLM 호출 (max_tokens: 8000 - ai/main과 동일)
            gpt5_config = GenerationConfig(max_tokens=8000)
            response = await provider.chat(messages, gpt5_config)
            response_text = response.text.strip() if response.text else ""

            # 토큰 사용량 기록
            if response.usage and session_id:
                prompt_tokens = response.usage.get("prompt_tokens", 0)
                completion_tokens = response.usage.get("completion_tokens", 0)
                await record_token_usage(
                    session_id=session_id,
                    category=category,
                    turn=turn,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                )

            logger.info(
                "GPT-5-mini 응답 수신",
                response_length=len(response_text),
                response_preview=response_text[:200],
                usage=response.usage,
            )

            # JSON 응답 파싱
            parsed_data = self._parse_gpt5mini_response(response_text)

            if not parsed_data:
                logger.warning(
                    "GPT-5-mini 응답 파싱 실패, 폴백 사용",
                    response_text=response_text[:500],
                    mode=mode,
                    topic=topic,
                )
                return self._create_fallback_messages(char1_code, char2_code, mode)

            # ChatMessage 리스트 생성
            chat_messages = []
            for line in parsed_data:
                speaker_code = line.get("speaker", char1_code)
                text = line.get("text", "")
                emotion_code = line.get("emotion_code", "NEUTRAL")
                emotion_intensity = line.get("emotion_intensity", 0.5)

                if not text:
                    continue

                # 후처리
                text = filter_noise(text)
                text = fix_brackets(text)
                text = filter_prompt_leak(text)

                chat_messages.append(
                    ChatMessage(
                        id=str(uuid.uuid4()),
                        character=CharacterCode(speaker_code),
                        type=MessageType.INTERPRETATION,
                        content=text,
                        timestamp=datetime.now(),
                        emotion=emotion_code,
                        emotion_intensity=emotion_intensity,
                    )
                )

            # 토론 상태 결정
            debate_status = ChatDebateStatus(
                is_consensus=(mode == "consensus"),
                eastern_opinion=None,
                western_opinion=None,
                question=None,
            )

            logger.info(
                "GPT-5-mini 티키타카 생성 완료",
                message_count=len(chat_messages),
                is_consensus=debate_status.is_consensus,
            )

            return chat_messages, debate_status

        except Exception as e:
            logger.error(
                "GPT-5-mini 티키타카 생성 실패",
                error=str(e),
                error_type=type(e).__name__,
            )
            return self._create_fallback_messages(char1_code, char2_code, mode)

    async def create_tikitaka_messages_gpt5mini_stream(
        self,
        topic: str,
        eastern_context: str,
        western_context: str,
        mode: str = "battle",
        char1_code: str = "SOISEOL",
        char2_code: str = "STELLA",
        is_first_turn: bool = False,
        is_last_turn: bool = False,
        user_question: str = "",
        session_id: str = "",
        category: str = "GENERAL",
        turn: int = 0,
    ) -> AsyncGenerator[dict, None]:
        """GPT-5-mini 스트리밍 응답을 버블 단위로 yield

        Args:
            topic: 주제 (total, love, wealth, career, health)
            eastern_context: 동양 운세 컨텍스트
            western_context: 서양 운세 컨텍스트
            mode: 대화 모드 (battle, consensus)
            char1_code: 캐릭터1 코드 (기본값: SOISEOL)
            char2_code: 캐릭터2 코드 (기본값: STELLA)
            is_first_turn: 첫 턴 여부
            is_last_turn: 마지막 턴 여부
            user_question: 사용자 질문
            session_id: 세션 ID (토큰 통계용)
            category: 운세 카테고리 (토큰 통계용)
            turn: 현재 턴 번호 (토큰 통계용)

        Yields:
            SSE 이벤트 딕셔너리 (event, data)
        """
        logger.info(
            "GPT-5-mini 스트리밍 시작",
            topic=topic,
            mode=mode,
            session_id=session_id,
        )

        try:
            # 채팅 Provider 가져오기
            provider = await self._get_chat_provider()

            # 모드 결정
            actual_mode = mode
            if is_first_turn:
                actual_mode = "greeting"
            elif is_last_turn:
                actual_mode = "end"

            # XML 프롬프트 생성
            system_prompt, user_prompt = build_gpt5mini_tikitaka_prompt(
                topic=topic,
                eastern_context=eastern_context,
                western_context=western_context,
                mode=actual_mode,
                char1_code=char1_code,
                char2_code=char2_code,
                user_question=user_question,
            )

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]

            # 버블 파서 초기화
            if not BUBBLE_PARSER_AVAILABLE:
                logger.error("BubbleParser를 사용할 수 없습니다")
                yield {
                    "event": "error",
                    "data": {"message": "스트리밍을 지원하지 않습니다"},
                }
                return

            bubble_parser = BubbleParser(session_id=session_id)
            bubble_count = 0

            # 스트리밍 시작
            gpt5_config = GenerationConfig(max_tokens=2500)

            async for chunk in provider.chat_stream(messages, gpt5_config):
                # 파서에 청크 공급
                events = bubble_parser.feed_stream_events(chunk)

                # 이벤트 발생 시 yield
                for event in events:
                    if event.event_type == "bubble_end":
                        bubble_count += 1
                        # 완성된 버블을 SSE 형식으로 전송
                        yield {
                            "event": "bubble",
                            "data": {
                                "bubble_id": event.bubble_id,
                                "character": event.data.get("character"),
                                "content": event.data.get("content"),
                                "emotion": event.data.get("emotion"),
                                "type": event.data.get("type"),
                                "reply_to": event.data.get("reply_to"),
                            },
                        }

            # 남은 불완전 버블 처리
            remaining = bubble_parser.flush()
            for bubble in remaining:
                bubble_count += 1
                yield {
                    "event": "bubble",
                    "data": {
                        "bubble_id": bubble.bubble_id,
                        "character": bubble.character,
                        "content": bubble.content,
                        "emotion": bubble.emotion,
                        "type": bubble.type,
                        "reply_to": bubble.reply_to,
                    },
                }

            # 완료 이벤트
            yield {
                "event": "complete",
                "data": {
                    "bubble_count": bubble_count,
                    "session_id": session_id,
                    "turn": turn,
                },
            }

            logger.info(
                "GPT-5-mini 스트리밍 완료",
                bubble_count=bubble_count,
                session_id=session_id,
            )

        except Exception as e:
            logger.error(
                "GPT-5-mini 스트리밍 실패",
                error=str(e),
                error_type=type(e).__name__,
            )
            yield {
                "event": "error",
                "data": {"message": str(e)},
            }

    def _parse_gpt5mini_response(self, response_text: str) -> list[dict]:
        """GPT-5-mini 응답을 파싱하여 lines 배열 추출

        Args:
            response_text: LLM 응답 텍스트 (JSON 형식 기대)

        Returns:
            파싱된 lines 배열 (각 요소는 speaker, text, emotion_code, emotion_intensity 포함)
        """
        import json
        import re

        if not response_text:
            logger.warning("빈 응답 텍스트")
            return []

        try:
            # 전처리: 코드펜스 제거
            cleaned_text = re.sub(r'```json?\s*\n?', '', response_text)
            cleaned_text = re.sub(r'```\s*\n?', '', cleaned_text)
            cleaned_text = cleaned_text.strip()

            # JSON 객체 추출 시도 (앞뒤 텍스트 무시)
            json_match = re.search(r'\{[\s\S]*\}', cleaned_text)
            if json_match:
                cleaned_text = json_match.group()

            # JSON 파싱
            data = json.loads(cleaned_text)

            # lines 배열 추출
            if isinstance(data, dict) and "lines" in data:
                lines = data["lines"]
                if isinstance(lines, list):
                    return lines

            logger.warning(
                "응답에 lines 배열이 없음",
                data_keys=list(data.keys()) if isinstance(data, dict) else None,
            )
            return []

        except json.JSONDecodeError as e:
            logger.warning(
                "JSON 파싱 실패, 텍스트 파싱 시도",
                error=str(e),
                response_preview=response_text[:300],
            )
            # 8B vLLM 텍스트 응답 폴백 파싱
            return self._parse_text_response(response_text)

    def _parse_text_response(self, response_text: str) -> list[dict]:
        """텍스트 응답에서 캐릭터 대사 추출 (8B vLLM 폴백)

        Args:
            response_text: LLM 텍스트 응답

        Returns:
            파싱된 lines 배열
        """
        import re

        lines = []
        # 패턴: "캐릭터명: 대사" 또는 "캐릭터명(이모션): 대사"
        # 예: "소이설: 허허, 좋은 기운이 있소."
        # 예: "SOISEOL: 허허, 좋은 기운이 있소."
        patterns = [
            r"(소이설|SOISEOL)[:\s]+(.+?)(?=(?:스텔라|STELLA|소이설|SOISEOL|$))",
            r"(스텔라|STELLA)[:\s]+(.+?)(?=(?:소이설|SOISEOL|스텔라|STELLA|$))",
        ]

        char_map = {
            "소이설": "SOISEOL",
            "SOISEOL": "SOISEOL",
            "스텔라": "STELLA",
            "STELLA": "STELLA",
        }

        for pattern in patterns:
            matches = re.findall(pattern, response_text, re.DOTALL)
            for char_name, content in matches:
                content = content.strip()
                if content and len(content) > 5:  # 너무 짧은 건 스킵
                    lines.append({
                        "speaker": char_map.get(char_name, "SOISEOL"),
                        "text": content,
                        "emotion_code": "NEUTRAL",
                        "emotion_intensity": 0.5,
                    })

        # 패턴 매칭 실패 시, 응답 전체를 두 캐릭터에 분배
        if not lines and response_text.strip():
            # 문장 단위로 분할
            sentences = re.split(r'[.!?。]\s*', response_text)
            sentences = [s.strip() for s in sentences if s.strip() and len(s) > 10]

            for i, sentence in enumerate(sentences[:4]):  # 최대 4개
                speaker = "SOISEOL" if i % 2 == 0 else "STELLA"
                lines.append({
                    "speaker": speaker,
                    "text": sentence,
                    "emotion_code": "NEUTRAL",
                    "emotion_intensity": 0.5,
                })

        if lines:
            logger.info("텍스트 파싱 성공", line_count=len(lines))

        return lines

    def _create_fallback_messages(
        self,
        char1_code: str,
        char2_code: str,
        mode: str,
    ) -> tuple[list[ChatMessage], ChatDebateStatus]:
        """폴백 메시지 생성

        Args:
            char1_code: 캐릭터1 코드
            char2_code: 캐릭터2 코드
            mode: 대화 모드

        Returns:
            (기본 메시지 목록, 토론 상태) 튜플
        """
        fallback_messages = [
            ChatMessage(
                id=str(uuid.uuid4()),
                character=CharacterCode(char1_code),
                type=MessageType.INTERPRETATION,
                content=self._get_bubble_fallback(char1_code, mode),
                timestamp=datetime.now(),
                emotion="NEUTRAL",
                emotion_intensity=0.5,
            ),
            ChatMessage(
                id=str(uuid.uuid4()),
                character=CharacterCode(char2_code),
                type=MessageType.INTERPRETATION,
                content=self._get_bubble_fallback(char2_code, mode),
                timestamp=datetime.now(),
                emotion="NEUTRAL",
                emotion_intensity=0.5,
            ),
        ]

        debate_status = ChatDebateStatus(
            is_consensus=(mode == "consensus"),
            eastern_opinion=None,
            western_opinion=None,
            question=None,
        )

        return fallback_messages, debate_status
