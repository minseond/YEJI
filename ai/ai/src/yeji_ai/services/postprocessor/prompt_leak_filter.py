"""프롬프트 누출 필터

LLM 응답에서 시스템 프롬프트가 누출된 경우 탐지 및 제거합니다.
3중 방어 전략의 Layer 3 (최종 방어선)
"""

import re

import structlog

logger = structlog.get_logger()


class PromptLeakFilter:
    """프롬프트 누출 필터 (최종 방어선)

    시스템 프롬프트의 메타 텍스트가 LLM 응답에 포함된 경우
    탐지하고 제거합니다.
    """

    # 누출 패턴 (우선순위 높은 순)
    LEAK_PATTERNS = [
        # === P0-CRITICAL: 프롬프트 마커 제거 ===
        r"\*\*\([^)]+\)\*\*",  # **(임수)**, **(오화)** 등 bold 괄호 패턴
        r"\([가-힣]+[가-힣수화목금토수]+\)",  # (임수), (오화), (계토) 등 한글 괄호 패턴
        # === 메타 텍스트 브래킷 패턴 (가장 흔한 누출) ===
        r"\[문장\s*종결\s*예시[^\]]*\][\s\S]*?(?=\n\n|\[|$)",
        r"\[올바른\s*문장\s*예시[^\]]*\][\s\S]*?(?=\n\n|\[|$)",
        r"\[틀린\s*문장\s*예시[^\]]*\][\s\S]*?(?=\n\n|\[|$)",
        r"\[말투\s*규칙[^\]]*\][\s\S]*?(?=\n\n|\[|$)",
        r"\[금지\s*표현[^\]]*\][\s\S]*?(?=\n\n|\[|$)",
        r"\[호칭[^\]]*\][\s\S]*?(?=\n\n|\[|$)",
        r"\[핵심\s*규칙[^\]]*\][\s\S]*?(?=\n\n|\[|$)",
        r"\[자동\s*변환[^\]]*\][\s\S]*?(?=\n\n|\[|$)",
        r"\[최종\s*점검[^\]]*\][\s\S]*?(?=\n\n|\[|$)",
        # === XML 태그 패턴 ===
        r"<examples[^>]*>[\s\S]*?</examples>",
        r"<instruction[^>]*>[\s\S]*?</instruction>",
        r"<critical_rule[^>]*>[\s\S]*?</critical_rule>",
        r"<forbidden[^>]*>[\s\S]*?</forbidden>",
        r"<말투\s*규칙[^>]*>[\s\S]*?</말투\s*규칙>",
        r"<자동\s*변환[^>]*>[\s\S]*?</자동\s*변환>",
        r"<올바른\s*문장\s*예시[^>]*>[\s\S]*?</올바른\s*문장\s*예시>",
        r"<틀린\s*문장\s*예시[^>]*>[\s\S]*?</틀린\s*문장\s*예시>",
        r"<최종\s*점검[^>]*>[\s\S]*?</최종\s*점검>",
        r"<speaking_style[^>]*>[\s\S]*?</speaking_style>",
        r"<speaking_rule[^>]*>[\s\S]*?</speaking_rule>",
        r"<output_rule[^>]*>[\s\S]*?</output_rule>",
        r"<internal_only[^>]*>[\s\S]*?</internal_only>",
        # === P0 vLLM 특수 토큰 패턴 ===
        r"<\|fim(?:prefix|suffix|middle)\|>",  # vLLM FIM 토큰
        r"]=]\s*<src",  # Lua 구분자 + src
        # === P0 코드/프롬프트 누출 패턴 ===
        r"<src\s*\[규칙\][^>]*>",  # <src [규칙]... (닫는 태그만)
        r"getContext\.set\w+\([^)]*\)",  # getContext.setXxx(...)
        r"setPromptTemplate\([^)]*\)",  # setPromptTemplate
        r"set(?:Input|Output)Format\([^)]*\)",  # setInputFormat/setOutputFormat
        r"setTemperature\([^)]*\)",  # setTemperature
        r"setSeed\([^)]*\)",  # setSeed
        r"await\s+model\.\w+",  # await model.xxx
        r"console\.\w+\([^)]*\)",  # console.xxx
        r"\.catch\((?:err|error)\s*=>[^)]+\)",  # .catch(err => ...)
        r"\.then\([^)]+\)",  # .then(...)
        r"```[\s\S]*?```",  # 코드 블록 전체
        # === P0 주석/설명 패턴 ===
        r"###\s*(?:Explanation|Example Usage|Note).*",  # 마크다운 헤더
        r"//\s*(?:Error handling|Clean up|Set seed|Output the|Example usage).*",  # 주석
        # === 변환 예시 패턴 (화살표) ===
        r"-\s*있습니다\s*→\s*있[소어]요?\s*\n?",
        r"-\s*입니다\s*→\s*(예요|이에요|이오)\s*\n?",
        r"-\s*합니다\s*→\s*(해요|하오)\s*\n?",
        r"-\s*됩니다\s*→\s*(돼요|되오)\s*\n?",
        r"-\s*겠습니다\s*→\s*(ㄹ게요|겠소|할게요|드릴게요)\s*\n?",
        r"-\s*바랍니다\s*→\s*(바라요|바라오)\s*\n?",
        r"-\s*주세요\s*→\s*(주세요|주시오)\s*\n?",
        r"-\s*하세요\s*→\s*(하세요|하시오|시게)\s*\n?",
        r"-\s*네요\s*→\s*(네요|구려)\s*\n?",
        r"-\s*군요\s*→\s*(군요|로다)\s*\n?",
        # === 번호 매기기 예시 패턴 ===
        # 1. "예시문장" 또는 1. 예시문장 형태
        r'\d+\.\s*"[^"]{5,}"\s*\n?',  # 5자 이상 (오탐 방지)
        # === 체크박스/지시 패턴 ===
        r"[✅❌⚠️]\s*[^:\n]+:\s*[^\n]+\n?",
        r"[✅❌]\s*[^\n]{0,50}(절대|금지|사용|모든 문장)[^\n]*\n?",
        # === 경고 패턴 ===
        r"⚠️\s*경고:[^\n]+\n?",
        # === P0 추가 패턴 (프롬프트 해시태그 마커 및 메타텍스트) ===
        r"#ae\d+\s*[^:\n]*:[^\n]*",        # #ae1 소이설: ... 형식
        r"#[a-z]+\d+\s*[^:\n]*:[^\n]*",    # #step1 캐릭터: ... 형식
        r"\bspep\b\s*",                     # spep 토큰
        r"</?src[^>]*>",                    # <src>, </src> 태그
        r"\[표현\][^\[]*",                  # [표현] 메타텍스트
        r"\[감정\][^\[]*",                  # [감정] 메타텍스트
        r"\[톤\][^\[]*",                    # [톤] 메타텍스트
        # === P1 메타 지시문 패턴 ===
        r"\[\\?이어서[^\]]*\]",             # [\이어서 완성할 부분], [이어서...]
        r"\[\\?마무리\]",                   # [\마무리], [마무리]
        r"\[\\?총평\]",                     # [\총평], [총평]
        r"아래는\s*요청하신[^\n]*",         # "아래는 요청하신..." 메타 응답
        r"\[\\?(?:시작|끝|중간|계속)\]",    # [시작], [끝], [중간], [계속] 등
        # === P0-CRITICAL: continuation 프롬프트 누출 ===
        r"다음\s*문장을\s*[^\n]*이어서\s*완성[^\n]*",  # 이어서 완성
        r"다음\s*문장을\s*[^\n]*자연스럽게[^\n]*",  # 자연스럽게
        # === P2 추가 패턴 ===
        r"<src\s*=",                        # <src="사주:... (src 태그에 등호 포함)
        r"다음\s*문장은[^\n]*이어서[^\n]*", # "다음 문장은 ... 이어서" 메타 지시문
        r"의\s+손에\s+든[^\n]*",            # 소설체 서술 (3인칭)
        r"그(?:의|는|녀)\s+(?:발걸음|마음속|눈빛)[^\n]*",  # 소설체 서술 (3인칭)
        # === P0-CRITICAL: 캐릭터 시스템 프롬프트 누출 ===
        r"당신은\s*.+\s*캐릭터입니다[^\n]*",       # "당신은 소이설 캐릭터입니다..."
        r"당신은\s*.+이?라\s*하오[^\n]*",          # "당신은 소이설이라 하오..."
        r"지시사항\s*:\s*[^\n]+",                   # "지시사항: ..."
        r"사주\s*:\s*오행\s*:\s*[^\n]+",           # "사주: 오행: 토 우세..."
        r"오행\s*:\s*\w+\s*우세[^\n]*",            # "오행: 토 우세..."
        r"음양\s*:\s*\d+%[^\n]*",                   # "음양: 60%..."
        r"\[규칙\]\s*-[^\n]+",                      # "[규칙] - 주어진 내용의..."
        r"주어진\s*내용의\s*맥락을\s*유지[^\n]*",  # "주어진 내용의 맥락을 유지하면서..."
        r"캐릭터\s*설정\s*:\s*[^\n]+",             # "캐릭터 설정: ..."
        r"페르소나\s*:\s*[^\n]+",                   # "페르소나: ..."
        r"<persona>[^<]*</persona>",                # <persona>...</persona>
        r"<speaking_rule>[^<]*</speaking_rule>",    # <speaking_rule>...</speaking_rule>
        r"<language_purity>[^<]*</language_purity>",# <language_purity>...</language_purity>
        r"<constraints>[^<]*</constraints>",        # <constraints>...</constraints>
    ]

    def __init__(self):
        """패턴 컴파일"""
        self._compiled_patterns = [
            re.compile(p, re.DOTALL | re.IGNORECASE)
            for p in self.LEAK_PATTERNS
        ]

    def filter(self, text: str) -> tuple[str, bool]:
        """프롬프트 누출 필터링

        Args:
            text: LLM 응답 텍스트

        Returns:
            tuple[str, bool]: (필터링된 텍스트, 누출 발생 여부)
        """
        if not text:
            return text, False

        leaked = False
        filtered_text = text
        leaked_patterns = []

        for pattern in self._compiled_patterns:
            match = pattern.search(filtered_text)
            if match:
                leaked = True
                leaked_patterns.append(pattern.pattern[:40])
                filtered_text = pattern.sub("", filtered_text)

        # 반복 문장 제거 (같은 문장이 2회 이상 반복되면 첫 번째만 유지)
        filtered_text = self._remove_repeated_sentences(filtered_text)

        # 불완전한 문장 시작 수정
        filtered_text = self._fix_incomplete_sentences(filtered_text)

        # 연속 줄바꿈 정리
        filtered_text = re.sub(r"\n{3,}", "\n\n", filtered_text)
        filtered_text = filtered_text.strip()

        if leaked:
            logger.warning(
                "prompt_leak_detected",
                patterns_matched=len(leaked_patterns),
                pattern_samples=leaked_patterns[:3],
                original_length=len(text),
                filtered_length=len(filtered_text),
            )

        return filtered_text, leaked

    def _remove_repeated_sentences(self, text: str) -> str:
        """반복되는 문장 제거 (2회 이상 반복 시 첫 번째만 유지)

        Args:
            text: 입력 텍스트

        Returns:
            반복 문장이 제거된 텍스트
        """
        if not text:
            return text

        # 1단계: 연속 반복 패턴 제거 (같은 문장이 3회 이상 연속)
        # 마침표로 끝나는 문장이 연속 반복되는 경우
        consecutive_pattern = re.compile(r'((?:[^.!?]+[.!?]+\s*)){1}(\1{2,})', re.DOTALL)
        text = consecutive_pattern.sub(r'\1', text)

        # 2단계: 문장 분리 및 중복 제거
        sentences = re.split(r"([.!?]+\s*)", text)

        combined = []
        for i in range(0, len(sentences) - 1, 2):
            sentence = sentences[i]
            delimiter = sentences[i + 1] if i + 1 < len(sentences) else ""
            if sentence.strip():
                combined.append(sentence + delimiter)

        if len(sentences) % 2 == 1 and sentences[-1].strip():
            combined.append(sentences[-1])

        # 중복 카운트 및 제거
        seen = {}
        unique_sentences = []
        repeated_count = 0

        for sentence in combined:
            normalized = " ".join(sentence.split())
            if normalized:
                seen[normalized] = seen.get(normalized, 0) + 1
                if seen[normalized] == 1:
                    unique_sentences.append(sentence)
                else:
                    repeated_count += 1

        # 3회 이상 반복 경고
        highly_repeated = [s for s, count in seen.items() if count >= 3]
        if highly_repeated:
            logger.warning(
                "highly_repeated_sentences_detected",
                count=len(highly_repeated),
                samples=[s[:50] for s in highly_repeated[:2]],
            )

        return "".join(unique_sentences)

    def _fix_incomplete_sentences(self, text: str) -> str:
        """불완전한 문장 시작 수정

        한글 받침으로 시작하거나 조사로 시작하는 비정상 문장을 정리합니다.
        예: "른 직장운의 흐름이..." → 제거 또는 정리

        Args:
            text: 입력 텍스트

        Returns:
            정리된 텍스트
        """
        if not text:
            return text

        # 문장 단위로 분리
        lines = text.split('\n')
        fixed_lines = []

        for line in lines:
            stripped = line.strip()
            if not stripped:
                fixed_lines.append(line)
                continue

            # 비정상 시작 패턴 체크
            # 1. 한글 받침 자음으로 시작 (ㄱ-ㅎ 범위)
            # 2. 조사로 시작 (은, 는, 이, 가, 을, 를, 의, 와, 과, 로, 으로)
            first_char = stripped[0]

            # 한글 자음만으로 시작하는 경우 (받침 누락)
            if '\u3131' <= first_char <= '\u314E':  # ㄱ-ㅎ
                logger.debug("incomplete_sentence_removed", sample=stripped[:30])
                continue

            # 조사로 시작하는 짧은 문장 (문맥 없이 조사만 있는 경우)
            if len(stripped) < 50:
                incomplete_starts = ['른 ', '은 ', '는 ', '을 ', '를 ', '의 ', '과 ', '와 ']
                if any(stripped.startswith(s) for s in incomplete_starts):
                    logger.debug("incomplete_sentence_removed", sample=stripped[:30])
                    continue

            fixed_lines.append(line)

        return '\n'.join(fixed_lines)

    def detect_only(self, text: str) -> list[str]:
        """누출 패턴만 탐지 (필터링 없이)

        Args:
            text: LLM 응답 텍스트

        Returns:
            탐지된 패턴 목록
        """
        detected = []
        for pattern in self._compiled_patterns:
            if pattern.search(text):
                detected.append(pattern.pattern[:40])
        return detected


# 싱글톤 인스턴스
_prompt_leak_filter = PromptLeakFilter()


def filter_prompt_leak(text: str) -> str:
    """프롬프트 누출 필터링 (편의 함수)

    Args:
        text: LLM 응답 텍스트

    Returns:
        필터링된 텍스트
    """
    filtered, _ = _prompt_leak_filter.filter(text)
    return filtered


def detect_prompt_leak(text: str) -> list[str]:
    """프롬프트 누출 탐지 (편의 함수)

    Args:
        text: LLM 응답 텍스트

    Returns:
        탐지된 패턴 목록 (비어있으면 누출 없음)
    """
    return _prompt_leak_filter.detect_only(text)
