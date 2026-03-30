# 티키타카 버블 파서 설계 문서

> **문서 버전**: 1.0.0
> **작성일**: 2026-01-30
> **상태**: 설계 (Design)
> **담당팀**: SSAFY YEJI AI팀
> **관련 PRD**: `ai/docs/prd/tikitaka-schema-v2.md`

---

## 목차

1. [개요](#1-개요)
2. [설계 목표](#2-설계-목표)
3. [XML 태그 파싱 로직](#3-xml-태그-파싱-로직)
4. [스트리밍 중 부분 버블 처리](#4-스트리밍-중-부분-버블-처리)
5. [폴백 전략](#5-폴백-전략)
6. [에러 처리](#6-에러-처리)
7. [Python 구현 스켈레톤](#7-python-구현-스켈레톤)
8. [테스트 전략](#8-테스트-전략)
9. [성능 고려사항](#9-성능-고려사항)

---

## 1. 개요

### 1.1 배경

tikitaka-schema-v2.md PRD에 따라 LLM이 생성하는 티키타카 대화는 XML 태그 기반으로 구조화됩니다. 이 문서는 LLM 출력에서 버블을 정확하게 파싱하기 위한 설계를 정의합니다.

### 1.2 LLM 출력 형식

```xml
<tikitaka>
  <bubble character="SOISEOL" emotion="HAPPY" type="INTERPRETATION">
    병화 일간이시네요~ 밝고 열정적인 기운이 느껴져요!
  </bubble>

  <bubble character="STELLA" emotion="THOUGHTFUL" type="INTERPRETATION" reply_to="previous">
    양자리 태양이군. 사주와 마찬가지로 리더십이 강해.
  </bubble>
</tikitaka>
```

### 1.3 영향 범위

| 구성요소 | 변경 내용 |
|----------|-----------|
| `engine/tikitaka_generator.py` | 프롬프트 수정, 파서 통합 |
| `services/tikitaka_service.py` | 파싱된 버블 처리 |
| 신규 모듈 | `services/parsers/bubble_parser.py` |

---

## 2. 설계 목표

### 2.1 기능 요구사항

| 요구사항 | 설명 | 우선순위 |
|----------|------|----------|
| XML 태그 파싱 | `<bubble>` 태그에서 속성과 내용 추출 | P0 |
| 스트리밍 파싱 | 토큰 단위 스트리밍 중 실시간 파싱 | P0 |
| 폴백 처리 | XML 파싱 실패 시 대체 파싱 전략 | P0 |
| 속성 검증 | character, emotion, type 값 유효성 검사 | P1 |
| reply_to 처리 | 대화 연결 관계 추출 | P2 |

### 2.2 비기능 요구사항

| 요구사항 | 목표값 | 측정 방법 |
|----------|--------|----------|
| 파싱 성공률 | ≥ 99% | 테스트 커버리지 |
| 파싱 지연 | < 1ms/버블 | 벤치마크 |
| 메모리 사용 | < 10MB (스트리밍) | 프로파일링 |

---

## 3. XML 태그 파싱 로직

### 3.1 파싱 아키텍처

```
LLM 출력 (스트리밍)
       │
       ▼
┌──────────────────┐
│  BufferManager   │  ◄── 토큰 버퍼링
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  XMLTagDetector  │  ◄── 태그 감지 (정규식)
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ AttributeParser  │  ◄── 속성 추출
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ ContentExtractor │  ◄── 내용 추출 및 정제
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  BubbleFactory   │  ◄── Bubble 객체 생성
└────────┬─────────┘
         │
         ▼
     ParsedBubble
```

### 3.2 정규식 패턴 설계

#### 3.2.1 버블 태그 패턴

```regex
<bubble\s+
  character="(?P<character>\w+)"\s+
  emotion="(?P<emotion>\w+)"\s+
  type="(?P<type>\w+)"
  (?:\s+reply_to="(?P<reply_to>[\w-]+)")?
\s*>
(?P<content>[\s\S]*?)
</bubble>
```

**패턴 설명:**

| 그룹 | 설명 | 필수 여부 |
|------|------|----------|
| `character` | 캐릭터 코드 (SOISEOL, STELLA, SYSTEM) | 필수 |
| `emotion` | 감정 코드 (10종) | 필수 |
| `type` | 메시지 타입 (9종) | 필수 |
| `reply_to` | 응답 대상 버블 ID | 선택 |
| `content` | 버블 내용 | 필수 |

#### 3.2.2 속성 순서 유연성

LLM이 속성 순서를 변경할 수 있으므로, 순서에 무관한 패턴도 지원합니다.

```regex
<bubble\s+
  (?=.*\bcharacter="(?P<character>\w+)")
  (?=.*\bemotion="(?P<emotion>\w+)")
  (?=.*\btype="(?P<type>\w+)")
  (?:.*\breply_to="(?P<reply_to>[\w-]+)")?
  [^>]*>
(?P<content>[\s\S]*?)
</bubble>
```

### 3.3 속성 값 검증

#### 3.3.1 유효한 값 집합

```python
VALID_CHARACTERS = {"SOISEOL", "STELLA", "SYSTEM"}

VALID_EMOTIONS = {
    "NEUTRAL", "HAPPY", "CURIOUS", "THOUGHTFUL", "SURPRISED",
    "CONCERNED", "CONFIDENT", "PLAYFUL", "MYSTERIOUS", "EMPATHETIC",
}

VALID_MESSAGE_TYPES = {
    "GREETING", "INFO_REQUEST", "INTERPRETATION", "DEBATE",
    "CONSENSUS", "QUESTION", "CHOICE", "SUMMARY", "FAREWELL",
}
```

#### 3.3.2 검증 로직

```
입력값 → 대문자 변환 → 유효 집합 확인 → 유효/무효 판정
                                            │
                                   무효 시 기본값 적용
```

| 속성 | 무효 시 기본값 |
|------|---------------|
| character | `SOISEOL` |
| emotion | `NEUTRAL` |
| type | `INTERPRETATION` |

---

## 4. 스트리밍 중 부분 버블 처리

### 4.1 문제 정의

LLM 스트리밍 시 토큰이 버블 태그 중간에서 끊어질 수 있습니다.

```
토큰 1: "<bubble character=\"SOIS"
토큰 2: "EOL\" emotion=\"HAPPY\" type=\""
토큰 3: "INTERPRETATION\">안녕하세요"
토큰 4: "~</bubble>"
```

### 4.2 상태 머신 설계

```
     ┌──────────────────────────────────────┐
     │                                      │
     ▼                                      │
┌─────────┐    <bubble     ┌───────────┐    │
│  IDLE   │ ───────────► │ OPENING   │    │
└─────────┘               └─────┬─────┘    │
     ▲                          │ >        │
     │                          ▼          │
     │                   ┌───────────┐     │
     │                   │ CONTENT   │     │
     │                   └─────┬─────┘     │
     │                         │ </bubble> │
     │                         ▼          │
     │                   ┌───────────┐     │
     └───────────────── │ COMPLETE  │─────┘
                        └───────────┘
```

#### 4.2.1 상태 정의

| 상태 | 설명 | 전이 조건 |
|------|------|----------|
| `IDLE` | 대기 상태, 버블 외부 | `<bubble` 감지 시 OPENING |
| `OPENING` | 여는 태그 파싱 중 | `>` 감지 시 CONTENT |
| `CONTENT` | 버블 내용 수집 중 | `</bubble>` 감지 시 COMPLETE |
| `COMPLETE` | 버블 파싱 완료 | 즉시 IDLE로 전이 |

### 4.3 버퍼 관리 전략

#### 4.3.1 링 버퍼 (Ring Buffer)

최근 N개의 토큰만 유지하여 메모리 효율성 확보.

```
버퍼 크기: 4KB (약 1000자)
오버플로우 시: 앞부분 삭제 + 경고 로깅
```

#### 4.3.2 부분 태그 감지

```python
# 불완전 태그 패턴
INCOMPLETE_OPEN = r"<bubble(?:\s+[^>]*)?$"   # 여는 태그 미완성
INCOMPLETE_CLOSE = r"</bubbl?e?$"             # 닫는 태그 미완성
```

### 4.4 실시간 청크 이벤트 생성

스트리밍 중 클라이언트에 전송할 SSE 이벤트:

```
상태: IDLE → OPENING
  → 이벤트 없음 (버퍼링)

상태: OPENING → CONTENT (여는 태그 완료)
  → bubble_start 이벤트 발행
  → 속성 정보 전송

상태: CONTENT (내용 수집 중)
  → bubble_chunk 이벤트 발행 (청크 단위)

상태: CONTENT → COMPLETE (닫는 태그 완료)
  → bubble_end 이벤트 발행
  → 전체 내용 및 타임스탬프 전송
```

---

## 5. 폴백 전략

### 5.1 폴백 계층 구조

```
시도 1: XML 태그 파싱 (정규 패턴)
    │
    │ 실패
    ▼
시도 2: 유연한 XML 파싱 (속성 순서 무관)
    │
    │ 실패
    ▼
시도 3: 접두사 기반 파싱 ([소이설], [스텔라])
    │
    │ 실패
    ▼
시도 4: 전체 텍스트를 단일 버블로 처리
```

### 5.2 접두사 기반 폴백 파서

LLM이 XML 형식을 따르지 않을 경우 사용.

#### 5.2.1 접두사 패턴

```regex
\[(?P<character>소이설|스텔라|SOISEOL|STELLA)\]\s*
(?P<content>.+?)
(?=\[소이설\]|\[스텔라\]|\[SOISEOL\]|\[STELLA\]|$)
```

#### 5.2.2 캐릭터 매핑

| 입력 | 변환 결과 |
|------|----------|
| `소이설`, `SOISEOL` | `CharacterCode.SOISEOL` |
| `스텔라`, `STELLA` | `CharacterCode.STELLA` |

#### 5.2.3 기본값 적용

```python
# 접두사 폴백 시 기본값
DEFAULT_FALLBACK = {
    "emotion": EmotionCode.NEUTRAL,
    "type": MessageType.INTERPRETATION,
    "reply_to": None,
}
```

### 5.3 최종 폴백: 단일 버블

모든 파싱 시도 실패 시:

```python
# 전체 텍스트를 시스템 메시지로 처리
ParsedBubble(
    bubble_id=generate_id(),
    character=CharacterCode.SYSTEM,
    emotion=EmotionCode.NEUTRAL,
    type=MessageType.INTERPRETATION,
    content=raw_text.strip(),
    reply_to=None,
)
```

### 5.4 폴백 로깅

폴백 사용 시 상세 로깅으로 디버깅 지원:

```python
logger.warning(
    "bubble_parser_fallback",
    level=fallback_level,        # 1, 2, 3, 4
    original_text=raw_text[:100],
    error=str(parse_error),
    session_id=session_id,
)
```

---

## 6. 에러 처리

### 6.1 에러 유형 분류

| 에러 유형 | 설명 | 복구 전략 |
|----------|------|----------|
| `MalformedXMLError` | XML 구조 오류 | 폴백 파서 사용 |
| `InvalidAttributeError` | 잘못된 속성 값 | 기본값 적용 |
| `EmptyContentError` | 빈 버블 내용 | 버블 스킵 |
| `BufferOverflowError` | 버퍼 초과 | 버퍼 정리 후 계속 |
| `TimeoutError` | 스트리밍 타임아웃 | 부분 결과 반환 |

### 6.2 에러 처리 플로우

```
에러 발생
    │
    ▼
┌───────────────┐
│ 에러 유형 판별 │
└───────┬───────┘
        │
        ├─────────────────────────┬─────────────────────────┐
        ▼                         ▼                         ▼
┌───────────────┐        ┌───────────────┐        ┌───────────────┐
│ 복구 가능     │        │ 폴백 필요     │        │ 치명적 에러   │
└───────┬───────┘        └───────┬───────┘        └───────┬───────┘
        │                         │                         │
        ▼                         ▼                         ▼
   기본값 적용              폴백 파서 사용              에러 이벤트 발행
        │                         │                         │
        └─────────────┬───────────┘                         │
                      ▼                                     ▼
               파싱 계속                              세션 종료
```

### 6.3 에러 이벤트 형식

```python
# SSE 에러 이벤트
{
    "event": "error",
    "data": {
        "code": "PARSE_ERROR",
        "message": "버블 파싱 중 오류가 발생했습니다.",
        "recoverable": True,
        "fallback_used": "prefix_parser",
    }
}
```

---

## 7. Python 구현 스켈레톤

### 7.1 모듈 구조

```
yeji_ai/
└── services/
    └── parsers/
        ├── __init__.py
        ├── bubble_parser.py      # 메인 파서
        ├── xml_detector.py       # XML 태그 감지
        ├── fallback_parsers.py   # 폴백 파서들
        ├── buffer_manager.py     # 스트리밍 버퍼
        └── exceptions.py         # 커스텀 예외
```

### 7.2 핵심 클래스 스켈레톤

#### 7.2.1 ParsedBubble (데이터 클래스)

```python
@dataclass
class ParsedBubble:
    """파싱된 버블 데이터"""

    bubble_id: str
    character: CharacterCode
    emotion: EmotionCode
    type: MessageType
    content: str
    reply_to: str | None = None
    is_complete: bool = True  # 스트리밍 중 부분 버블 여부
    parse_method: str = "xml"  # 파싱 방법 (xml, prefix, fallback)
```

#### 7.2.2 ParserState (Enum)

```python
class ParserState(str, Enum):
    """파서 상태"""

    IDLE = "idle"
    OPENING = "opening"
    CONTENT = "content"
    COMPLETE = "complete"
```

#### 7.2.3 BubbleParser (메인 파서)

```python
class BubbleParser:
    """티키타카 버블 파서

    XML 태그 기반 LLM 출력을 ParsedBubble 객체로 변환합니다.
    스트리밍 및 배치 파싱을 모두 지원합니다.
    """

    def __init__(self) -> None:
        """파서 초기화"""
        # 상태 초기화
        # 정규식 패턴 컴파일
        # 폴백 파서 설정
        ...

    def parse(self, text: str) -> list[ParsedBubble]:
        """배치 파싱 - 전체 텍스트에서 버블 추출

        Args:
            text: LLM 출력 텍스트

        Returns:
            파싱된 버블 목록
        """
        ...

    def parse_stream(
        self,
        text: str,
    ) -> Generator[ParsedBubble, None, None]:
        """스트리밍 파싱 - 제너레이터 방식

        Args:
            text: LLM 출력 텍스트

        Yields:
            파싱된 버블
        """
        ...

    async def parse_stream_async(
        self,
        token_stream: AsyncIterator[str],
    ) -> AsyncGenerator[BubbleStreamEvent, None]:
        """비동기 스트리밍 파싱

        Args:
            token_stream: LLM 토큰 스트림

        Yields:
            버블 스트림 이벤트 (start, chunk, end)
        """
        ...

    def reset(self) -> None:
        """파서 상태 초기화"""
        ...
```

#### 7.2.4 StreamingBubbleParser (스트리밍 전용)

```python
class StreamingBubbleParser:
    """스트리밍 전용 버블 파서

    토큰 단위 입력을 처리하며 실시간으로 이벤트를 발행합니다.
    """

    def __init__(self) -> None:
        """초기화"""
        # 상태 머신 초기화
        # 버퍼 매니저 생성
        ...

    def feed(self, token: str) -> list[BubbleStreamEvent]:
        """토큰 입력 및 이벤트 반환

        Args:
            token: LLM 출력 토큰

        Returns:
            발생한 이벤트 목록 (없으면 빈 리스트)
        """
        ...

    def flush(self) -> list[BubbleStreamEvent]:
        """버퍼 플러시 및 최종 이벤트 반환

        스트리밍 종료 시 호출하여 남은 버퍼 처리

        Returns:
            최종 이벤트 목록
        """
        ...

    @property
    def state(self) -> ParserState:
        """현재 파서 상태"""
        ...

    @property
    def current_bubble(self) -> ParsedBubble | None:
        """현재 파싱 중인 버블 (있는 경우)"""
        ...
```

#### 7.2.5 BubbleStreamEvent (이벤트 클래스)

```python
@dataclass
class BubbleStreamEvent:
    """버블 스트림 이벤트"""

    event_type: Literal["bubble_start", "bubble_chunk", "bubble_end", "error"]
    bubble_id: str
    data: dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)

    def to_sse(self) -> str:
        """SSE 형식 문자열로 변환"""
        ...
```

#### 7.2.6 FallbackParser (폴백 파서)

```python
class FallbackParser:
    """폴백 파서 체인

    XML 파싱 실패 시 순차적으로 폴백 전략을 적용합니다.
    """

    def __init__(self) -> None:
        """폴백 파서 체인 초기화"""
        ...

    def parse(self, text: str) -> list[ParsedBubble]:
        """폴백 파싱 실행

        Args:
            text: 원본 텍스트

        Returns:
            파싱된 버블 목록 (실패 시 빈 리스트)
        """
        ...

    def _parse_with_prefix(self, text: str) -> list[ParsedBubble]:
        """접두사 기반 파싱 ([소이설], [스텔라])"""
        ...

    def _parse_as_single(self, text: str) -> list[ParsedBubble]:
        """전체 텍스트를 단일 버블로 처리"""
        ...
```

### 7.3 유틸리티 함수 스켈레톤

```python
def generate_bubble_id() -> str:
    """고유 버블 ID 생성

    Returns:
        "b_" 접두사가 붙은 UUID
    """
    ...


def normalize_character(value: str) -> CharacterCode:
    """캐릭터 코드 정규화

    Args:
        value: 입력값 (한글 또는 영문)

    Returns:
        정규화된 CharacterCode
    """
    ...


def validate_emotion(value: str) -> EmotionCode:
    """감정 코드 검증 및 변환

    Args:
        value: 입력값

    Returns:
        유효한 EmotionCode (무효 시 NEUTRAL)
    """
    ...


def validate_message_type(value: str) -> MessageType:
    """메시지 타입 검증 및 변환

    Args:
        value: 입력값

    Returns:
        유효한 MessageType (무효 시 INTERPRETATION)
    """
    ...


def sanitize_content(content: str) -> str:
    """버블 내용 정제

    - 앞뒤 공백 제거
    - 연속 개행 정리
    - 특수 문자 이스케이프 해제

    Args:
        content: 원본 내용

    Returns:
        정제된 내용
    """
    ...
```

---

## 8. 테스트 전략

### 8.1 단위 테스트

#### 8.1.1 정상 케이스

| 테스트 케이스 | 입력 | 기대 결과 |
|--------------|------|----------|
| 단일 버블 | 단일 `<bubble>` 태그 | 1개 ParsedBubble |
| 복수 버블 | 3개 `<bubble>` 태그 | 3개 ParsedBubble 리스트 |
| reply_to 포함 | reply_to 속성 있음 | reply_to 값 추출 |
| 멀티라인 내용 | 줄바꿈 포함 내용 | 줄바꿈 유지 |

#### 8.1.2 엣지 케이스

| 테스트 케이스 | 입력 | 기대 결과 |
|--------------|------|----------|
| 빈 내용 | `<bubble ...></bubble>` | 버블 스킵 |
| 속성 순서 변경 | emotion 먼저 | 정상 파싱 |
| 한글 속성값 | `character="소이설"` | 코드 변환 |
| 대소문자 혼용 | `character="Soiseol"` | 정규화 |

#### 8.1.3 폴백 케이스

| 테스트 케이스 | 입력 | 기대 결과 |
|--------------|------|----------|
| 접두사 형식 | `[소이설] 내용` | 폴백 파싱 성공 |
| XML 깨짐 | 닫는 태그 누락 | 폴백 파싱 |
| 순수 텍스트 | XML/접두사 없음 | 단일 버블 |

### 8.2 통합 테스트

```python
@pytest.mark.asyncio
async def test_streaming_parser_integration():
    """스트리밍 파서 통합 테스트"""
    # 1. 모의 LLM 토큰 스트림 생성
    # 2. StreamingBubbleParser로 파싱
    # 3. SSE 이벤트 시퀀스 검증
    # 4. 최종 버블 목록 검증
    ...
```

### 8.3 성능 테스트

| 시나리오 | 측정 항목 | 목표값 |
|----------|----------|--------|
| 대용량 텍스트 (10KB) | 파싱 시간 | < 10ms |
| 100개 버블 | 처리 시간 | < 50ms |
| 스트리밍 1000토큰 | 이벤트 지연 | < 1ms/토큰 |

---

## 9. 성능 고려사항

### 9.1 정규식 최적화

```python
# 사전 컴파일된 패턴 사용
_COMPILED_PATTERNS = {
    "bubble": re.compile(BUBBLE_PATTERN, re.DOTALL),
    "prefix": re.compile(PREFIX_PATTERN, re.DOTALL),
}
```

### 9.2 메모리 관리

- 스트리밍 시 버퍼 크기 제한 (4KB)
- 완료된 버블은 즉시 yield하여 메모리 해제
- 대용량 텍스트는 청크 단위 처리

### 9.3 캐싱

```python
# 자주 사용되는 변환 결과 캐싱
@lru_cache(maxsize=32)
def normalize_character(value: str) -> CharacterCode:
    ...
```

### 9.4 병렬 처리

배치 모드에서 여러 버블 동시 처리:

```python
async def parse_parallel(
    bubbles_texts: list[str],
) -> list[ParsedBubble]:
    """병렬 버블 파싱"""
    tasks = [_parse_single(text) for text in bubbles_texts]
    return await asyncio.gather(*tasks)
```

---

## 변경 이력

| 버전 | 날짜 | 변경 내용 | 작성자 |
|------|------|----------|--------|
| 1.0.0 | 2026-01-30 | 초기 설계 문서 작성 | YEJI AI팀 |

---

## 참조 문서

| 문서 | 경로 | 설명 |
|------|------|------|
| 티키타카 스키마 V2 PRD | `ai/docs/prd/tikitaka-schema-v2.md` | 스키마 정의 |
| LLM 후처리 PRD | `ai/docs/prd/llm-response-postprocessor.md` | 후처리 설계 |
| Python 컨벤션 | `ai/docs/PYTHON_CONVENTIONS.md` | 코딩 스타일 |

---

> **Note**: 이 문서는 설계 단계 문서입니다. 구현 시 세부 사항이 변경될 수 있습니다.
