"""사주 분석 서비스"""

import asyncio
import time
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field

import structlog

from yeji_ai.clients.vllm_client import GenerationConfig, VLLMClient
from yeji_ai.config import get_settings
from yeji_ai.engine.prompts import (
    build_advice_prompt,
    build_combined_prompt,
    build_eastern_prompt,
    build_western_prompt,
)
from yeji_ai.engine.saju_calculator import SajuCalculator
from yeji_ai.engine.tikitaka_generator import TikitakaGenerator
from yeji_ai.models.saju import (
    CategoryScore,
    EasternAnalysis,
    SajuResult,
    WesternAnalysis,
)
from yeji_ai.models.schemas import (
    AnalyzeRequest,
    AnswerRequest,
    BaseResponse,
    ChatRequest,
    SajuProfile,
    SessionPhase,
    SessionState,
    SSEEvent,
)

logger = structlog.get_logger()

# 세션 TTL (30분)
SESSION_TTL_SECONDS = 1800


@dataclass
class CachedSession:
    """TTL 기반 캐시 세션 (HIGH-2)"""

    state: SessionState
    saju_profile: SajuProfile  # HIGH-1: saju_profile 저장
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)

    def is_expired(self, ttl: float = SESSION_TTL_SECONDS) -> bool:
        """만료 여부 확인"""
        return time.time() - self.last_accessed > ttl

    def touch(self) -> None:
        """접근 시간 갱신"""
        self.last_accessed = time.time()


class SajuService:
    """사주 분석 서비스"""

    def __init__(self):
        self.calculator = SajuCalculator()
        self.tikitaka = TikitakaGenerator()
        self.vllm_client = VLLMClient()

        # TTL 기반 세션 저장소 (HIGH-2)
        self._sessions: dict[str, CachedSession] = {}
        self._results: dict[str, SajuResult] = {}
        self._answer_events: dict[str, asyncio.Event] = {}
        self._pending_answers: dict[str, str] = {}

        # 백그라운드 정리 태스크
        self._cleanup_task: asyncio.Task | None = None

    async def _start_cleanup_task(self) -> None:
        """세션 정리 태스크 시작"""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_expired_sessions())

    async def _cleanup_expired_sessions(self) -> None:
        """만료된 세션 정리 (MEDIUM-1: 메모리 누수 방지)"""
        while True:
            try:
                await asyncio.sleep(300)  # 5분마다 실행
                expired = [
                    sid for sid, session in self._sessions.items() if session.is_expired()
                ]
                for sid in expired:
                    await self._cleanup_session(sid)
                    logger.info("session_expired_cleanup", session_id=sid)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("cleanup_error", error=str(e))

    async def _cleanup_session(self, session_id: str) -> None:
        """단일 세션 정리 (MEDIUM-1: 메모리 누수 수정)"""
        self._sessions.pop(session_id, None)
        self._results.pop(session_id, None)
        self._pending_answers.pop(session_id, None)
        # asyncio.Event 정리
        event = self._answer_events.pop(session_id, None)
        if event:
            event.set()  # 대기 중인 태스크 해제

    async def start_analysis(self, session_id: str, request: AnalyzeRequest) -> None:
        """분석 시작 (세션 생성)"""
        # 백그라운드 정리 태스크 시작
        await self._start_cleanup_task()

        session = SessionState(
            session_id=session_id,
            user_id=request.user_id,
            phase=SessionPhase.ANALYZING,
            category=request.category,
            sub_category=request.sub_category,
        )

        # HIGH-1, HIGH-2: saju_profile 포함 캐시 세션 생성
        self._sessions[session_id] = CachedSession(
            state=session,
            saju_profile=request.saju_profile,
        )
        self._answer_events[session_id] = asyncio.Event()

        logger.info(
            "saju_session_created",
            session_id=session_id,
            user_id=request.user_id,
            birth_date=request.saju_profile.birth_date,
        )

    async def session_exists(self, session_id: str) -> bool:
        """세션 존재 여부 확인"""
        cached = self._sessions.get(session_id)
        if cached and not cached.is_expired():
            cached.touch()
            return True
        return False

    def _get_session(self, session_id: str) -> SessionState | None:
        """세션 상태 반환 (내부용)"""
        cached = self._sessions.get(session_id)
        if cached and not cached.is_expired():
            cached.touch()
            return cached.state
        return None

    def _get_saju_profile(self, session_id: str) -> SajuProfile | None:
        """사주 프로필 반환 (HIGH-1)"""
        cached = self._sessions.get(session_id)
        if cached and not cached.is_expired():
            return cached.saju_profile
        return None

    async def submit_answer(self, request: AnswerRequest) -> None:
        """중간 질문 응답 제출"""
        session = self._get_session(request.session_id)
        if session:
            session.user_answers.append(request.value)
            self._pending_answers[request.session_id] = request.value

            # 대기 중인 스트림에 알림
            event = self._answer_events.get(request.session_id)
            if event:
                event.set()

    async def stream_result(self, session_id: str) -> AsyncGenerator[str, None]:
        """
        SSE 스트리밍 결과 생성

        흐름:
        1. result_start → result (여러 개) → result_complete
        2. message (토론) → question (중간 질문) → pause
        3. (사용자 응답 대기)
        4. message (토론 계속) → complete
        """
        session = self._get_session(session_id)
        saju_profile = self._get_saju_profile(session_id)

        if not session or not saju_profile:
            yield SSEEvent(event="error", data={"message": "세션을 찾을 수 없습니다"}).to_sse()
            return

        try:
            # 1. 분석 시작
            yield SSEEvent(event="result_start", data={"phase": "result_streaming"}).to_sse()

            # 2. 사주 계산 (HIGH-1: saju_profile 실제 사용)
            saju_result = await self._calculate_saju(session, saju_profile)

            # 3. 결과 스트리밍
            async for event in self._stream_result_chunks(saju_result):
                yield event

            # 4. 결과 완료
            yield SSEEvent(
                event="result_complete",
                data={"result_id": saju_result.result_id, "phase": "discussion"},
            ).to_sse()

            # 5. 티키타카 토론
            session.phase = SessionPhase.DISCUSSION
            async for event in self._stream_discussion(session_id, session, saju_result):
                yield event

            # 6. 완료
            session.phase = SessionPhase.COMPLETE
            yield SSEEvent(event="complete", data={"session_id": session_id}).to_sse()

            # 결과 저장
            self._results[session_id] = saju_result

        except Exception as e:
            logger.error("saju_stream_error", session_id=session_id, error=str(e))
            # LOW-2: 프로덕션용 generic 에러 메시지
            settings = get_settings()
            error_msg = str(e) if settings.debug else "분석 중 오류가 발생했습니다"
            yield SSEEvent(event="error", data={"message": error_msg}).to_sse()

    async def _calculate_saju(
        self, session: SessionState, saju_profile: SajuProfile
    ) -> SajuResult:
        """사주 계산 및 vLLM 해석 생성"""
        settings = get_settings()

        # 1. 사주/별자리 기본 계산 (항상 실행)
        four_pillars, element_balance = self.calculator.calculate(
            birth_date=saju_profile.birth_date,
            birth_time=saju_profile.birth_time,
            gender=saju_profile.gender.value,
        )
        sun_sign = self.calculator.get_sun_sign(saju_profile.birth_date)
        day_master = self.calculator.get_day_master(four_pillars.day)

        # 2. vLLM 서버 연결 확인
        vllm_available = await self.vllm_client.health_check()

        if not vllm_available:
            # Mock 모드: vLLM 미연결
            logger.info("using_mock_result", reason="vllm_unavailable")
            return await self._build_mock_result(
                four_pillars, element_balance, day_master, sun_sign, session
            )

        # 3. vLLM으로 해석 생성 (P1 비동기 최적화: 2단계 병렬화)
        logger.info("using_vllm_generation", model=settings.vllm_model)

        try:
            # Step 1: 동양/서양 해석 병렬 생성
            eastern_interpretation, western_interpretation = await asyncio.gather(
                self._generate_eastern_interpretation(four_pillars, element_balance, day_master),
                self._generate_western_interpretation(sun_sign),
            )

            # Step 2: 통합 의견/조언 병렬 생성 (Step 1 결과 필요)
            combined_opinion, advice = await asyncio.gather(
                self._generate_combined_opinion(
                    eastern_interpretation, western_interpretation, day_master, sun_sign
                ),
                self._generate_advice(
                    eastern_interpretation,
                    western_interpretation,
                    session.category.value if session.category else "종합운",
                    session.sub_category or "",
                ),
            )

            # 오행 중 가장 강한 원소 (main_element)
            elements = {
                "목": element_balance.wood,
                "화": element_balance.fire,
                "토": element_balance.earth,
                "금": element_balance.metal,
                "수": element_balance.water,
            }
            main_element = max(elements, key=elements.get)

            # 키워드 생성 (일간 기반)
            keywords = self._generate_keywords(day_master, main_element)

            return SajuResult(
                result_id=1,
                total_score=self._calculate_compatibility_score(element_balance),
                main_element=main_element,
                keywords=keywords,
                category_scores=self._generate_category_scores(session.category),
                eastern=EasternAnalysis(
                    four_pillars=four_pillars,
                    day_master=day_master,
                    element_balance=element_balance,
                    lucky_elements=self._get_lucky_elements(element_balance),
                    interpretation=eastern_interpretation,
                ),
                western=WesternAnalysis(
                    sun_sign=sun_sign,
                    moon_sign=None,  # 추후 확장
                    rising_sign=None,  # 추후 확장
                    dominant_planet=self._get_dominant_planet(sun_sign),
                    interpretation=western_interpretation,
                ),
                combined_opinion=combined_opinion,
                advice=advice,
                visualizations=[
                    {
                        "type": "radar",
                        "title": "오행 균형",
                        "data": {
                            "labels": ["목", "화", "토", "금", "수"],
                            "values": [
                                element_balance.wood,
                                element_balance.fire,
                                element_balance.earth,
                                element_balance.metal,
                                element_balance.water,
                            ],
                        },
                    }
                ],
                suggested_questions=[
                    "더 자세한 운세를 알고 싶어요",
                    "상대방과의 궁합은 어떤가요?",
                ],
            )

        except Exception as e:
            logger.error("vllm_generation_error", error=str(e))
            # Fallback to mock
            return await self._build_mock_result(
                four_pillars, element_balance, day_master, sun_sign, session
            )

    async def _generate_eastern_interpretation(
        self, four_pillars, element_balance, day_master: str
    ) -> str:
        """동양 사주 해석 생성 (vLLM)"""
        prompt = build_eastern_prompt(four_pillars, element_balance, day_master)
        config = GenerationConfig(max_tokens=300, temperature=0.7)

        try:
            response = await self.vllm_client.generate(prompt, config)
            return response.text.strip()
        except Exception as e:
            logger.warning("eastern_interpretation_fallback", error=str(e))
            return (
                f"{day_master} 일간으로 태어나 안정적이고 신뢰감 있는 성격입니다. "
                "오행의 균형을 통해 조화로운 삶을 추구합니다."
            )

    async def _generate_western_interpretation(self, sun_sign: str) -> str:
        """서양 별자리 해석 생성 (vLLM)"""
        prompt = build_western_prompt(sun_sign, None, None)
        config = GenerationConfig(max_tokens=300, temperature=0.7)

        try:
            response = await self.vllm_client.generate(prompt, config)
            return response.text.strip()
        except Exception as e:
            logger.warning("western_interpretation_fallback", error=str(e))
            return (
                f"{sun_sign} 태양은 깊은 감수성과 직관력을 부여합니다. "
                "내면의 풍부한 감정과 창의적 에너지가 특징입니다."
            )

    async def _generate_combined_opinion(
        self, eastern: str, western: str, day_master: str, sun_sign: str
    ) -> str:
        """통합 의견 생성 (vLLM)"""
        prompt = build_combined_prompt(eastern, western, day_master, sun_sign)
        config = GenerationConfig(max_tokens=200, temperature=0.7)

        try:
            response = await self.vllm_client.generate(prompt, config)
            return response.text.strip()
        except Exception as e:
            logger.warning("combined_opinion_fallback", error=str(e))
            return (
                "동양과 서양 모두 당신의 깊은 감수성과 직관력을 강조합니다. "
                "내면의 목소리에 귀 기울이며 균형 잡힌 결정을 내리세요."
            )

    async def _generate_advice(
        self, eastern: str, western: str, category: str, sub_category: str
    ) -> list[str]:
        """맞춤 조언 생성 (vLLM)"""
        import json

        prompt = build_advice_prompt(eastern, western, category, sub_category)
        config = GenerationConfig(max_tokens=300, temperature=0.7)

        try:
            response = await self.vllm_client.generate(prompt, config)
            text = response.text.strip()
            # JSON 파싱 시도
            if text.startswith("["):
                return json.loads(text)
            # JSON이 아닌 경우 줄바꿈으로 분리
            lines = [
                line.strip().lstrip("- ").lstrip("1234567890. ")
                for line in text.split("\n")
                if line.strip()
            ]
            return lines[:3] if lines else self._get_default_advice()
        except Exception as e:
            logger.warning("advice_generation_fallback", error=str(e))
            return self._get_default_advice()

    def _get_default_advice(self) -> list[str]:
        """기본 조언 반환"""
        return [
            "감정을 표현하기 전 잠시 생각하는 시간을 가지세요",
            "자연 속에서 명상하면 기운 균형에 도움이 됩니다",
            "중요한 결정은 이번 달 중순 이후가 좋겠습니다",
        ]

    async def _build_mock_result(
        self, four_pillars, element_balance, day_master: str, sun_sign: str, session: SessionState
    ) -> SajuResult:
        """Mock 결과 생성 (vLLM 미연결 시)"""
        mock_result = await self.calculator.calculate_mock()

        # 실제 계산값으로 교체
        mock_result.eastern.four_pillars = four_pillars
        mock_result.eastern.element_balance = element_balance
        mock_result.eastern.day_master = day_master
        mock_result.western.sun_sign = sun_sign

        return mock_result

    def _calculate_compatibility_score(self, balance) -> int:
        """오행 균형 기반 점수 계산"""
        values = [balance.wood, balance.fire, balance.earth, balance.metal, balance.water]
        avg = sum(values) / 5
        variance = sum((v - avg) ** 2 for v in values) / 5
        # 균형이 좋을수록 높은 점수 (분산이 낮을수록)
        score = max(50, min(95, int(100 - variance / 2)))
        return score

    def _generate_keywords(self, day_master: str, main_element: str) -> list[str]:
        """일간/오행 기반 키워드 생성"""
        day_keywords = {
            "갑목": ["리더십", "진취적", "도전정신"],
            "을목": ["유연함", "협조적", "적응력"],
            "병화": ["열정", "활력", "카리스마"],
            "정화": ["섬세함", "예술성", "따뜻함"],
            "무토": ["안정감", "신뢰", "포용력"],
            "기토": ["세심함", "실용적", "끈기"],
            "경금": ["결단력", "정의감", "강인함"],
            "신금": ["섬세함", "예리함", "우아함"],
            "임수": ["지혜", "통찰력", "포용력"],
            "계수": ["영리함", "적응력", "감수성"],
        }
        element_keywords = {
            "목": ["성장", "창의성"],
            "화": ["열정", "활력"],
            "토": ["안정", "신뢰"],
            "금": ["결단력", "정의"],
            "수": ["지혜", "유연함"],
        }
        keywords = day_keywords.get(day_master, ["균형", "조화", "성장"])
        keywords.extend(element_keywords.get(main_element, []))
        return keywords[:4]

    def _get_lucky_elements(self, balance) -> list[str]:
        """부족한 오행을 행운의 오행으로 추천"""
        elements = {
            "목": balance.wood,
            "화": balance.fire,
            "토": balance.earth,
            "금": balance.metal,
            "수": balance.water,
        }
        sorted_elements = sorted(elements.items(), key=lambda x: x[1])
        return [e[0] for e in sorted_elements[:2]]

    def _get_dominant_planet(self, sun_sign: str) -> str:
        """별자리별 지배 행성"""
        planets = {
            "양자리": "화성",
            "황소자리": "금성",
            "쌍둥이자리": "수성",
            "게자리": "달",
            "사자자리": "태양",
            "처녀자리": "수성",
            "천칭자리": "금성",
            "전갈자리": "명왕성",
            "사수자리": "목성",
            "염소자리": "토성",
            "물병자리": "천왕성",
            "물고기자리": "해왕성",
        }
        return planets.get(sun_sign, "태양")

    def _generate_category_scores(self, category) -> list[CategoryScore]:
        """카테고리별 점수 생성"""
        import random

        categories = [
            ("연애운", random.randint(65, 95)),
            ("금전운", random.randint(60, 90)),
            ("직장운", random.randint(55, 85)),
            ("건강운", random.randint(70, 95)),
        ]
        trends = ["up", "stable", "down"]
        descriptions = {
            "연애운": ["좋은 인연이 기다립니다", "소통에 집중하세요", "재회의 기운이 있습니다"],
            "금전운": ["안정적인 흐름", "새로운 기회 포착", "지출 관리 필요"],
            "직장운": ["승진 기회", "변화가 필요한 시기", "협업이 중요합니다"],
            "건강운": ["활력이 넘칩니다", "휴식이 필요해요", "균형 잡힌 생활 권장"],
        }
        return [
            CategoryScore(
                category=cat,
                score=score,
                trend=random.choice(trends),
                description=random.choice(descriptions.get(cat, ["좋은 기운입니다"])),
            )
            for cat, score in categories
        ]

    async def _stream_result_chunks(self, result: SajuResult) -> AsyncGenerator[str, None]:
        """결과 청크 스트리밍"""
        # 점수
        yield SSEEvent(
            event="result",
            data={
                "type": "score",
                "total_score": result.total_score,
                "main_element": result.main_element,
                "keywords": result.keywords,
            },
        ).to_sse()
        await asyncio.sleep(0.3)

        # 카테고리 점수
        yield SSEEvent(
            event="result",
            data={
                "type": "category_scores",
                "scores": [s.model_dump() for s in result.category_scores],
            },
        ).to_sse()
        await asyncio.sleep(0.3)

        # 동양 분석
        yield SSEEvent(
            event="result",
            data={"type": "eastern", **result.eastern.model_dump()},
        ).to_sse()
        await asyncio.sleep(0.3)

        # 서양 분석
        yield SSEEvent(
            event="result",
            data={"type": "western", **result.western.model_dump()},
        ).to_sse()
        await asyncio.sleep(0.3)

        # 통합 의견
        yield SSEEvent(
            event="result",
            data={"type": "combined_opinion", "content": result.combined_opinion},
        ).to_sse()
        await asyncio.sleep(0.3)

        # 조언
        yield SSEEvent(
            event="result",
            data={"type": "advice", "items": result.advice},
        ).to_sse()

    async def _stream_discussion(
        self,
        session_id: str,
        session: SessionState,
        result: SajuResult,
    ) -> AsyncGenerator[str, None]:
        """티키타카 토론 스트리밍"""
        async for event in self.tikitaka.generate_discussion(
            session_id=session_id,
            session=session,
            saju_result=result,
            answer_event=self._answer_events.get(session_id),
            pending_answers=self._pending_answers,
        ):
            yield event

    async def process_chat(self, request: ChatRequest) -> BaseResponse:
        """추가 채팅 처리"""
        session = self._get_session(request.session_id)
        result = self._results.get(request.session_id)

        if not session or not result:
            return BaseResponse(success=False, message="세션 또는 결과를 찾을 수 없습니다")

        # TODO: vLLM으로 응답 생성
        messages = await self.tikitaka.generate_chat_response(
            session=session,
            saju_result=result,
            user_message=request.message,
        )

        return BaseResponse(
            success=True,
            data={"messages": [m.model_dump() for m in messages]},
        )

    async def get_result(self, session_id: str) -> SajuResult | None:
        """최종 결과 조회"""
        return self._results.get(session_id)
