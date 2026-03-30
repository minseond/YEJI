"""복합 메시지 통합 서비스 (하이브리드 방식)

Redis에서 가져온 원본 사주/점성 데이터에서 상위 2개 요소를 추출하고,
1) 미리 생성된 메시지 풀에서 복합 메시지를 선택
2) 없으면 실시간 vLLM 호출로 생성
3) 그것도 실패하면 기본 폴백 메시지 반환
"""

import json
import random
import re
from pathlib import Path
from typing import Any, Literal

import httpx
import structlog

from yeji_ai.config import get_settings

logger = structlog.get_logger()

# 오행 이름 매핑
FIVE_ELEMENTS_NAMES = {
    "WOOD": "목", "FIRE": "화", "EARTH": "토", "METAL": "금", "WATER": "수",
}

# 십신 이름 매핑 (메시지 풀 키 형식 기준)
TEN_GODS_NAMES = {
    "BIJEON": "비견", "GEOBJE": "겁재", "SIKSHIN": "식신", "SANGGWAN": "상관",
    "PYEONJAE": "편재", "JEONGJAE": "정재", "PYEONGWAN": "편관", "JEONGGWAN": "정관",
    "PYEONIN": "편인", "JEONGIN": "정인",
}

# API 응답 코드 → 메시지 풀 키 형식 정규화 (언더스코어 제거)
TEN_GODS_CODE_NORMALIZE = {
    # API Enum 형식 (TenGodCode) → 메시지 풀 키 형식
    "BI_GYEON": "BIJEON",
    "GANG_JAE": "GEOBJE",      # API는 GANG_JAE 사용
    "GEOB_JAE": "GEOBJE",      # 호환성 유지
    "SIK_SIN": "SIKSHIN",      # API는 SIK_SIN 사용
    "SIK_SHIN": "SIKSHIN",     # 호환성 유지
    "SANG_GWAN": "SANGGWAN",
    "PYEON_JAE": "PYEONJAE",
    "JEONG_JAE": "JEONGJAE",
    "PYEON_GWAN": "PYEONGWAN",
    "JEONG_GWAN": "JEONGGWAN",
    "PYEON_IN": "PYEONIN",
    "JEONG_IN": "JEONGIN",
    # 이미 정규화된 형식도 지원
    "BIJEON": "BIJEON",
    "GEOBJE": "GEOBJE",
    "SIKSHIN": "SIKSHIN",
    "SANGGWAN": "SANGGWAN",
    "PYEONJAE": "PYEONJAE",
    "JEONGJAE": "JEONGJAE",
    "PYEONGWAN": "PYEONGWAN",
    "JEONGGWAN": "JEONGGWAN",
    "PYEONIN": "PYEONIN",
    "JEONGIN": "JEONGIN",
}

# 서양 4원소 이름 매핑
WESTERN_ELEMENTS_NAMES = {
    "FIRE": "불", "WATER": "물", "AIR": "공기", "EARTH": "흙",
}

# 양태 이름 매핑
MODALITY_NAMES = {
    "CARDINAL": "활동", "FIXED": "고정", "MUTABLE": "변통",
}

# 카테고리 한글 매핑
CATEGORY_KR = {
    "general": "총운", "love": "연애운", "money": "금전운",
    "career": "직장운", "health": "건강운", "study": "학업운",
    "GENERAL": "총운", "LOVE": "연애운", "MONEY": "금전운",
    "CAREER": "직장운", "HEALTH": "건강운", "STUDY": "학업운",
}


# ============================================================
# 메시지 풀 싱글톤
# ============================================================


class MessagePool:
    """메시지 풀 싱글톤 (앱 시작 시 한 번만 로드)"""

    _instance: "MessagePool | None" = None
    _initialized: bool = False

    def __new__(cls) -> "MessagePool":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """초기화 (한 번만 실행)"""
        if MessagePool._initialized:
            return

        self.eastern_pools: dict[str, dict[str, list[str]]] = {}
        self.western_pools: dict[str, dict[str, list[str]]] = {}

        self._load_all_pools()
        MessagePool._initialized = True

    def _load_all_pools(self) -> None:
        """모든 메시지 풀 로드"""
        # data/ 디렉토리 경로 계산
        current_file = Path(__file__)
        data_dir = current_file.parent.parent / "data"

        # 동양 메시지 풀
        eastern_dir = data_dir / "eastern"
        if eastern_dir.exists():
            self._load_eastern_pools(eastern_dir)

        # 서양 메시지 풀
        western_dir = data_dir / "western"
        if western_dir.exists():
            self._load_western_pools(western_dir)

        logger.info(
            "message_pools_loaded",
            eastern_sections=list(self.eastern_pools.keys()),
            western_sections=list(self.western_pools.keys()),
        )

    def _load_eastern_pools(self, eastern_dir: Path) -> None:
        """동양 메시지 풀 로드"""
        pool_files = {
            "five_elements": "five_elements_pairs.json",
            "ten_gods": "ten_gods_pairs.json",
        }

        for section, filename in pool_files.items():
            file_path = eastern_dir / filename
            if file_path.exists():
                try:
                    with file_path.open("r", encoding="utf-8") as f:
                        self.eastern_pools[section] = json.load(f)
                    logger.debug("eastern_pool_loaded", section=section, path=str(file_path))
                except Exception as e:
                    logger.warning(
                        "eastern_pool_load_failed",
                        section=section,
                        error=str(e),
                    )
                    self.eastern_pools[section] = {}
            else:
                logger.debug("eastern_pool_not_found", section=section, path=str(file_path))
                self.eastern_pools[section] = {}

    def _load_western_pools(self, western_dir: Path) -> None:
        """서양 메시지 풀 로드"""
        pool_files = {
            "elements": "elements_pairs.json",
            "modality": "modality_pairs.json",
        }

        for section, filename in pool_files.items():
            file_path = western_dir / filename
            if file_path.exists():
                try:
                    with file_path.open("r", encoding="utf-8") as f:
                        self.western_pools[section] = json.load(f)
                    logger.debug("western_pool_loaded", section=section, path=str(file_path))
                except Exception as e:
                    logger.warning(
                        "western_pool_load_failed",
                        section=section,
                        error=str(e),
                    )
                    self.western_pools[section] = {}
            else:
                logger.debug("western_pool_not_found", section=section, path=str(file_path))
                self.western_pools[section] = {}

    def get_eastern_pool(self, section: str) -> dict[str, list[str]]:
        """동양 메시지 풀 가져오기"""
        return self.eastern_pools.get(section, {})

    def get_western_pool(self, section: str) -> dict[str, list[str]]:
        """서양 메시지 풀 가져오기"""
        return self.western_pools.get(section, {})


# ============================================================
# 복합 메시지 서비스
# ============================================================


class CompoundMessageService:
    """복합 메시지 통합 서비스"""

    def __init__(self):
        """초기화"""
        self.message_pool = MessagePool()

    def extract_top_two_elements(
        self,
        element_list: list[dict],
        key: str = "count",
    ) -> tuple[str, str] | None:
        """상위 2개 요소 추출 (정렬된 튜플 반환)

        Args:
            element_list: 요소 리스트 (예: [{element: "FIRE", count: 3}, ...])
            key: 정렬 기준 키 (count, percentage, percent 등)

        Returns:
            알파벳순 정렬된 상위 2개 요소 튜플 또는 None
        """
        if not element_list or len(element_list) < 2:
            logger.debug(
                "insufficient_elements",
                count=len(element_list) if element_list else 0,
            )
            return None

        # key가 여러 가능성이 있으므로 유연하게 처리
        def get_value(item: dict) -> float:
            """딕셔너리에서 값 추출 (count, percentage, percent 등)"""
            for possible_key in [key, "count", "percentage", "percent", "value"]:
                if possible_key in item:
                    return float(item[possible_key])
            return 0.0

        # 내림차순 정렬
        sorted_elements = sorted(element_list, key=get_value, reverse=True)

        # 상위 2개 추출
        top_two = sorted_elements[:2]

        # element 키 또는 code 키에서 값 추출
        elem1 = top_two[0].get("element") or top_two[0].get("code")
        elem2 = top_two[1].get("element") or top_two[1].get("code")

        if not elem1 or not elem2:
            logger.warning(
                "element_key_not_found",
                top_two=top_two,
            )
            return None

        # 알파벳순 정렬하여 반환 (대소문자 무시)
        sorted_pair = tuple(sorted([elem1.upper(), elem2.upper()]))

        logger.debug(
            "top_two_extracted",
            original=[elem1, elem2],
            sorted=sorted_pair,
        )

        return sorted_pair

    def _normalize_code(self, code: str) -> str:
        """코드 정규화 (십신 언더스코어 형식 → 메시지 풀 형식)

        Args:
            code: 원본 코드 (예: "PYEON_GWAN")

        Returns:
            정규화된 코드 (예: "PYEONGWAN")
        """
        upper_code = code.upper()
        # 십신 코드 정규화 시도
        return TEN_GODS_CODE_NORMALIZE.get(upper_code, upper_code)

    def generate_compound_key(
        self,
        elem1: str,
        elem2: str,
        category: str,
    ) -> str:
        """복합 키 생성 (알파벳순 정렬)

        Args:
            elem1: 첫 번째 요소 (예: "FIRE" 또는 "PYEON_GWAN")
            elem2: 두 번째 요소 (예: "WOOD" 또는 "JEONG_GWAN")
            category: 카테고리 (예: "love")

        Returns:
            복합 키 (예: "FIRE_WOOD_LOVE" 또는 "JEONGGWAN_PYEONGWAN_CAREER")
        """
        # 십신 코드 정규화 (PYEON_GWAN → PYEONGWAN)
        norm1 = self._normalize_code(elem1)
        norm2 = self._normalize_code(elem2)
        sorted_elems = sorted([norm1, norm2])
        return f"{sorted_elems[0]}_{sorted_elems[1]}_{category.upper()}"

    def get_compound_message(
        self,
        fortune_data: dict[str, Any],
        fortune_type: Literal["eastern", "western"],
        category: str,
        section: str,
    ) -> str | None:
        """복합 메시지 선택

        Args:
            fortune_data: 운세 데이터 (stats 포함)
            fortune_type: 운세 타입 (eastern 또는 western)
            category: 운세 카테고리 (love, career, health 등)
            section: 섹션 (five_elements, ten_gods, elements, modality)

        Returns:
            선택된 복합 메시지 또는 None (폴백 필요)
        """
        logger.debug(
            "compound_message_request",
            fortune_type=fortune_type,
            category=category,
            section=section,
        )

        # 1. stats 추출 (래퍼 구조 대응: data.stats 또는 stats)
        stats = fortune_data.get("stats")
        if not stats:
            # data 안에 stats가 있는 경우
            data = fortune_data.get("data", {})
            stats = data.get("stats")
        if not stats:
            logger.warning("stats_not_found", fortune_data_keys=list(fortune_data.keys()))
            return None

        # 2. 섹션별 데이터 추출
        element_list: list[dict] | None = None

        if fortune_type == "eastern":
            if section == "five_elements":
                five_elements = stats.get("five_elements", {})
                # elements_list (model_dump default), list (alias), elements (legacy)
                element_list = (
                    five_elements.get("elements_list")
                    or five_elements.get("list")
                    or five_elements.get("elements")
                )
            elif section == "ten_gods":
                ten_gods = stats.get("ten_gods", {})
                # gods_list (model_dump default), list (alias), gods (legacy)
                element_list = (
                    ten_gods.get("gods_list")
                    or ten_gods.get("list")
                    or ten_gods.get("gods")
                )

        elif fortune_type == "western":
            if section == "elements":
                element_list = stats.get("element_4_distribution")
            elif section == "modality":
                element_list = stats.get("modality_3_distribution")

        if not element_list:
            logger.warning(
                "element_list_not_found",
                fortune_type=fortune_type,
                section=section,
                stats_keys=list(stats.keys()),
            )
            return None

        # 3. 상위 2개 추출
        top_two = self.extract_top_two_elements(element_list)
        if not top_two:
            return None

        elem1, elem2 = top_two

        # 4. 복합 키 생성
        compound_key = self.generate_compound_key(elem1, elem2, category)

        # 5. 메시지 풀에서 조회
        if fortune_type == "eastern":
            pool = self.message_pool.get_eastern_pool(section)
        else:
            pool = self.message_pool.get_western_pool(section)

        messages = pool.get(compound_key, [])

        if not messages:
            logger.debug(
                "compound_key_not_found",
                compound_key=compound_key,
                available_keys=list(pool.keys())[:10],
            )
            return None

        # 6. 첫 번째 메시지 반환 (추후 랜덤 선택으로 확장 가능)
        selected_message = messages[0]

        logger.info(
            "compound_message_selected",
            compound_key=compound_key,
            message_preview=selected_message[:50] + "..." if len(selected_message) > 50 else selected_message,
        )

        return selected_message

    async def generate_realtime_message(
        self,
        elem1: str,
        elem2: str,
        category: str,
        fortune_type: Literal["eastern", "western"],
        section: str,
    ) -> str | None:
        """실시간 vLLM 호출로 복합 메시지 생성

        Args:
            elem1: 첫 번째 요소 코드 (예: "FIRE")
            elem2: 두 번째 요소 코드 (예: "WOOD")
            category: 카테고리
            fortune_type: 운세 타입
            section: 섹션

        Returns:
            생성된 메시지 또는 None
        """
        # 요소 이름 변환
        if fortune_type == "eastern":
            if section == "five_elements":
                name1 = FIVE_ELEMENTS_NAMES.get(elem1, elem1)
                name2 = FIVE_ELEMENTS_NAMES.get(elem2, elem2)
            else:  # ten_gods
                name1 = TEN_GODS_NAMES.get(elem1, elem1)
                name2 = TEN_GODS_NAMES.get(elem2, elem2)
        else:  # western
            if section == "elements":
                name1 = WESTERN_ELEMENTS_NAMES.get(elem1.upper(), elem1)
                name2 = WESTERN_ELEMENTS_NAMES.get(elem2.upper(), elem2)
            else:  # modality
                name1 = MODALITY_NAMES.get(elem1.upper(), elem1)
                name2 = MODALITY_NAMES.get(elem2.upper(), elem2)

        category_kr = CATEGORY_KR.get(category, category)

        # 프롬프트 생성
        system = f"""당신은 사주 운세 전문가입니다.

두 기운을 조합해서 {category_kr} 메시지를 작성하세요.

[조건]
- "{name1}"와 "{name2}" 두 글자가 반드시 문장에 포함
- 40-60자 한 문장
- 마침표로 끝

[예시]
- {name1}의 기운과 {name2}의 힘이 만나 {category_kr}이 상승합니다.
- {name1}가 강하고 {name2}도 있어서 좋은 흐름입니다."""

        user = f"{name1}와 {name2} 기운의 {category_kr} 메시지 하나만 작성:"

        try:
            settings = get_settings()
            # 서버에 로드된 모델 확인 (AWQ/FP16 버전 차이 대응)
            model_name = settings.vllm_model
            if "-AWQ" in model_name:
                # FP16 버전도 시도 (서버에 AWQ가 없을 수 있음)
                model_name_fp16 = model_name.replace("-AWQ", "")
            else:
                model_name_fp16 = model_name

            async with httpx.AsyncClient(timeout=30.0) as client:
                # 먼저 설정된 모델로 시도, 실패하면 FP16 버전 시도
                for try_model in [model_name, model_name_fp16]:
                    try:
                        response = await client.post(
                            f"{settings.vllm_base_url}/v1/chat/completions",
                            json={
                                "model": try_model,
                                "messages": [
                                    {"role": "system", "content": system},
                                    {"role": "user", "content": user},
                                ],
                                "max_tokens": 100,
                                "temperature": 0.7,
                            },
                        )
                        response.raise_for_status()
                        break  # 성공하면 루프 종료
                    except httpx.HTTPStatusError as e:
                        if e.response.status_code == 404 and try_model != model_name_fp16:
                            continue  # 다음 모델 시도
                        raise

                content = response.json()["choices"][0]["message"]["content"]

                # 정제
                msg = self._clean_response(content)

                # 검증
                if name1 in msg and name2 in msg and 25 <= len(msg) <= 80:
                    logger.info(
                        "realtime_message_generated",
                        elem1=elem1,
                        elem2=elem2,
                        category=category,
                        message_preview=msg[:50],
                    )
                    return msg

                logger.warning(
                    "realtime_message_invalid",
                    msg=msg,
                    has_elem1=name1 in msg,
                    has_elem2=name2 in msg,
                    length=len(msg),
                )
                return None

        except Exception as e:
            logger.error(
                "realtime_message_failed",
                error=str(e),
                elem1=elem1,
                elem2=elem2,
            )
            return None

    def _clean_response(self, text: str) -> str:
        """응답 정제 - 첫 문장만 추출, 외래 문자 제거"""
        text = text.strip().strip('"').strip("'").strip()

        # 첫 문장만
        for sep in ['.', '!', '?']:
            if sep in text:
                text = text.split(sep)[0] + sep
                break

        # 외래 문자 제거 (Thai, Arabic 등)
        result = []
        for char in text:
            code = ord(char)
            # Thai (0x0E00-0x0E7F), Arabic (0x0600-0x06FF) 제외
            if not (0x0E00 <= code <= 0x0E7F) and not (0x0600 <= code <= 0x06FF):
                result.append(char)

        return ''.join(result).strip()

    def get_fallback_message(
        self,
        fortune_type: Literal["eastern", "western"],
        category: str,
    ) -> str:
        """폴백 메시지 반환

        Args:
            fortune_type: 운세 타입
            category: 운세 카테고리

        Returns:
            기본 메시지
        """
        fallback_messages = {
            "eastern": {
                "love": "오늘은 관계에서 균형과 조화를 찾는 하루입니다.",
                "career": "차근차근 노력하면 좋은 결과가 있을 것입니다.",
                "health": "몸과 마음의 균형을 유지하세요.",
                "money": "재물 관리에 신중함이 필요한 시기입니다.",
                "study": "꾸준한 노력이 결실을 맺을 것입니다.",
                "general": "오늘 하루 좋은 기운이 함께합니다.",
            },
            "western": {
                "love": "별들이 당신의 관계에 조화를 가져다줍니다.",
                "career": "우주의 흐름에 따라 움직이면 기회가 찾아옵니다.",
                "health": "마음의 평화가 건강의 시작입니다.",
                "money": "안정적인 흐름 속에서 성장하세요.",
                "study": "지식의 별들이 당신을 비춥니다.",
                "general": "오늘 하루 우주가 당신을 응원합니다.",
            },
        }

        # 카테고리 소문자로 통일
        cat_lower = category.lower()

        message = fallback_messages.get(fortune_type, {}).get(
            cat_lower,
            "오늘도 좋은 하루 되세요.",
        )

        logger.debug(
            "fallback_message_used",
            fortune_type=fortune_type,
            category=category,
        )

        return message


# ============================================================
# 유틸리티 함수
# ============================================================


def get_compound_message_or_fallback(
    fortune_data: dict[str, Any],
    fortune_type: Literal["eastern", "western"],
    category: str,
    section: str,
) -> str:
    """복합 메시지 조회 또는 폴백 반환 (동기 버전 - 메시지 풀만 사용)

    Args:
        fortune_data: 운세 데이터
        fortune_type: 운세 타입
        category: 카테고리
        section: 섹션

    Returns:
        복합 메시지 또는 폴백 메시지
    """
    service = CompoundMessageService()

    # 복합 메시지 시도
    message = service.get_compound_message(
        fortune_data=fortune_data,
        fortune_type=fortune_type,
        category=category,
        section=section,
    )

    # 폴백
    if not message:
        message = service.get_fallback_message(fortune_type, category)

    return message


async def get_compound_message_hybrid(
    fortune_data: dict[str, Any],
    fortune_type: Literal["eastern", "western"],
    category: str,
    section: str,
) -> tuple[str, str]:
    """복합 메시지 조회 - 하이브리드 방식 (비동기)

    1. 메시지 풀에서 검색
    2. 없으면 실시간 vLLM 호출
    3. 그것도 실패하면 기본 폴백 메시지

    Args:
        fortune_data: 운세 데이터
        fortune_type: 운세 타입
        category: 카테고리
        section: 섹션

    Returns:
        (메시지, 소스) 튜플
        소스: "pool" | "realtime" | "fallback"
    """
    service = CompoundMessageService()

    # 1. 메시지 풀에서 시도
    message = service.get_compound_message(
        fortune_data=fortune_data,
        fortune_type=fortune_type,
        category=category,
        section=section,
    )

    if message:
        # 메시지 풀에 여러 개 있으면 랜덤 선택
        return message, "pool"

    # 2. 실시간 LLM 호출 시도
    # 상위 2개 요소 추출 (래퍼 구조 대응)
    stats = fortune_data.get("stats") or fortune_data.get("data", {}).get("stats", {})
    element_list = None

    if fortune_type == "eastern":
        if section == "five_elements":
            five_elements = stats.get("five_elements", {})
            # elements_list (model_dump default), list (alias), elements (legacy)
            element_list = (
                five_elements.get("elements_list")
                or five_elements.get("list")
                or five_elements.get("elements")
            )
        elif section == "ten_gods":
            ten_gods = stats.get("ten_gods", {})
            # gods_list (model_dump default), list (alias), gods (legacy)
            element_list = (
                ten_gods.get("gods_list")
                or ten_gods.get("list")
                or ten_gods.get("gods")
            )
    elif fortune_type == "western":
        if section == "elements":
            element_list = stats.get("element_4_distribution")
        elif section == "modality":
            element_list = stats.get("modality_3_distribution")

    if element_list:
        top_two = service.extract_top_two_elements(element_list)
        if top_two:
            elem1, elem2 = top_two
            realtime_msg = await service.generate_realtime_message(
                elem1=elem1,
                elem2=elem2,
                category=category,
                fortune_type=fortune_type,
                section=section,
            )
            if realtime_msg:
                return realtime_msg, "realtime"

    # 3. 최종 폴백
    fallback_msg = service.get_fallback_message(fortune_type, category)
    return fallback_msg, "fallback"


async def get_all_section_messages_parallel(
    fortune_data: dict[str, Any],
    fortune_type: Literal["eastern", "western"],
    category: str,
) -> dict[str, tuple[str, str]]:
    """모든 섹션에 대해 복합 메시지를 병렬로 조회

    4개 섹션(동양: five_elements, ten_gods / 서양: elements, modality)을
    asyncio.gather로 병렬 처리하여 응답 시간을 단축합니다.

    Args:
        fortune_data: 운세 데이터
        fortune_type: 운세 타입 (eastern 또는 western)
        category: 운세 카테고리

    Returns:
        {섹션명: (메시지, 소스)} 딕셔너리
        소스: "pool" | "realtime" | "fallback"
    """
    import asyncio

    # 운세 타입별 섹션
    if fortune_type == "eastern":
        sections = ["five_elements", "ten_gods"]
    else:
        sections = ["elements", "modality"]

    # 병렬 처리
    tasks = [
        get_compound_message_hybrid(
            fortune_data=fortune_data,
            fortune_type=fortune_type,
            category=category,
            section=section,
        )
        for section in sections
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 결과 매핑
    section_messages = {}
    for section, result in zip(sections, results):
        if isinstance(result, Exception):
            logger.error(
                "parallel_section_failed",
                section=section,
                error=str(result),
            )
            # 예외 발생 시 폴백
            service = CompoundMessageService()
            fallback = service.get_fallback_message(fortune_type, category)
            section_messages[section] = (fallback, "fallback")
        else:
            section_messages[section] = result

    logger.info(
        "parallel_messages_completed",
        fortune_type=fortune_type,
        category=category,
        sources={s: v[1] for s, v in section_messages.items()},
    )

    return section_messages
