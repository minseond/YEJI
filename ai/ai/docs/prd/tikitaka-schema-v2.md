# 티키타카 JSON 스키마 V2 PRD

> **문서 버전**: 2.0.0
> **작성일**: 2026-01-30
> **상태**: 설계 (Design)
> **담당팀**: SSAFY YEJI AI팀

---

## 목차

1. [개요](#1-개요)
2. [문제 정의](#2-문제-정의)
3. [목표 및 성공 지표](#3-목표-및-성공-지표)
4. [스키마 설계](#4-스키마-설계)
5. [도메인 코드 정의](#5-도메인-코드-정의)
6. [SSE 스트리밍 설계](#6-sse-스트리밍-설계)
7. [XML 태그 기반 파싱](#7-xml-태그-기반-파싱)
8. [세션 상태 관리](#8-세션-상태-관리)
9. [프론트엔드 연동 가이드](#9-프론트엔드-연동-가이드)
10. [마이그레이션 계획](#10-마이그레이션-계획)
11. [참조 문서](#11-참조-문서)

---

## 1. 개요

### 1.1 배경

현재 티키타카 시스템은 `messages[]` 배열로 대화를 관리하고 있으나, 다음과 같은 한계가 있습니다:

- 대화 순서가 고정 (동양 → 서양 번갈아)
- 캐릭터 감정 표현 불가
- 대화 연결 관계 추적 어려움
- 프리미엄 사용자 보너스 턴 미지원
- 대화 단계(Phase) 구분 불명확

### 1.2 목표

티키타카 JSON 스키마 V2를 통해:

1. **유연한 버블 순서** 지원 (동→서, 서→동, 동→동 등)
2. **캐릭터 감정 코드** 추가 (10종)
3. **대화 연결** 기능 (`reply_to`)
4. **세션 상태** 구조화 (턴, 프리미엄 보너스)
5. **대화 단계** 명시 (Phase)

### 1.3 영향 범위

| 구성요소 | 변경 내용 |
|----------|-----------|
| AI 서버 | 스키마 변경, SSE 이벤트 수정 |
| 프론트엔드 | 버블 렌더링 로직 수정 |
| 백엔드 | 세션 상태 저장 구조 변경 (Redis) |

---

## 2. 문제 정의

### 2.1 현재 스키마 (V1)

```python
# 현재: yeji_ai/models/fortune/chat.py
class ChatMessage(BaseModel):
    character: CharacterCode  # SOISEOL, STELLA
    type: MessageType         # GREETING, INTERPRETATION, ...
    content: str
    timestamp: datetime
```

### 2.2 V1의 한계점

| 문제 | 설명 | 영향 |
|------|------|------|
| 고정 순서 | 반드시 동양 → 서양 번갈아 발화 | 자연스러운 대화 불가 |
| 감정 미표현 | 캐릭터 감정 상태 전달 불가 | UI 몰입도 저하 |
| 연결 추적 불가 | 어떤 발화에 대한 응답인지 알 수 없음 | 대화 맥락 파악 어려움 |
| 턴 관리 부재 | max_turns, bonus_turns 미지원 | 프리미엄 차별화 불가 |
| 단계 구분 없음 | GREETING, DIALOGUE, SUMMARY 등 미구분 | 프론트엔드 UI 분기 어려움 |

### 2.3 현재 서비스 구조

```
TikitakaService (tikitaka_service.py)
├── TikitakaSession (세션 상태)
├── analyze_both() (동양/서양 분석)
├── create_greeting_messages() (인사)
├── create_interpretation_messages() (해석)
├── create_topic_messages() (주제별)
├── stream_interpretation() (SSE 스트리밍)
└── handle_choice() (선택 응답)
```

---

## 3. 목표 및 성공 지표

### 3.1 목표

1. **유연성**: 발화 순서 제약 제거
2. **표현력**: 캐릭터 감정 10종 지원
3. **추적성**: 대화 연결 관계 명시
4. **확장성**: 프리미엄 보너스 턴 지원
5. **명확성**: 대화 단계별 UI 제어 가능

### 3.2 성공 지표 (KPI)

| 지표 | 현재 | 목표 | 측정 방법 |
|------|------|------|----------|
| 프론트엔드 렌더링 오류율 | 5% | 0.5% | 에러 로깅 |
| 대화 자연스러움 (UX 점수) | 3.2/5 | 4.0/5 | 사용자 피드백 |
| SSE 파싱 실패율 | 2% | 0.1% | 모니터링 |
| 프리미엄 보너스 활용률 | N/A | 70% | 사용 통계 |

### 3.3 비목표 (Out of Scope)

- LLM 모델 변경
- 새로운 캐릭터 추가
- 음성 출력 기능

---

## 4. 스키마 설계

### 4.1 핵심 변경 사항

| 항목 | V1 | V2 |
|------|-----|-----|
| 메시지 컨테이너 | `messages[]` | `bubbles[]` |
| 감정 | 없음 | `emotion: EmotionCode` |
| 대화 연결 | 없음 | `reply_to: string \| null` |
| 세션 상태 | 분산 | `session_state` 객체 |
| 대화 단계 | 없음 | `phase: PhaseCode` |

### 4.2 Bubble 스키마

```typescript
interface Bubble {
  // 식별자
  bubble_id: string;           // UUID v4 (예: "b_abc123")

  // 발화자
  character: CharacterCode;    // "SOISEOL" | "STELLA" | "SYSTEM"
  emotion: EmotionCode;        // 캐릭터 감정 (10종)

  // 메시지
  type: MessageType;           // 메시지 타입
  content: string;             // 메시지 내용

  // 대화 연결
  reply_to: string | null;     // 응답 대상 bubble_id (null: 독립 발화)

  // 메타데이터
  phase: PhaseCode;            // 대화 단계
  timestamp: string;           // ISO 8601 (예: "2026-01-30T15:30:00Z")

  // 선택적 필드
  ui_hint?: UIHint;            // 프론트엔드 UI 힌트
}
```

### 4.3 SessionState 스키마

```typescript
interface SessionState {
  // 세션 식별
  session_id: string;

  // 턴 관리
  current_turn: number;        // 현재 턴 (0부터 시작)
  max_turns: number;           // 최대 턴 (기본: 10)
  bonus_turns: number;         // 보너스 턴 (프리미엄: 3, 일반: 0)
  remaining_turns: number;     // 남은 턴 = max_turns + bonus_turns - current_turn

  // 사용자 상태
  is_premium: boolean;         // 프리미엄 여부

  // 대화 단계
  phase: PhaseCode;            // 현재 대화 단계

  // 분석 결과 (캐싱)
  has_eastern_result: boolean;
  has_western_result: boolean;
}
```

### 4.4 전체 응답 스키마

```typescript
interface TikitakaResponseV2 {
  // 버전 정보
  schema_version: "2.0.0";

  // 세션 상태
  session_state: SessionState;

  // 버블 목록 (순서 = 표시 순서)
  bubbles: Bubble[];

  // 토론 상태 (선택적)
  debate_status?: DebateStatus;

  // UI 힌트 (선택적)
  ui_hints?: GlobalUIHints;
}
```

### 4.5 TypeScript 전체 정의

```typescript
// ============================================================
// Enum 정의
// ============================================================

type CharacterCode = "SOISEOL" | "STELLA" | "SYSTEM";

type EmotionCode =
  | "NEUTRAL"      // 중립 (기본값)
  | "HAPPY"        // 기쁨, 밝음
  | "CURIOUS"      // 호기심, 흥미
  | "THOUGHTFUL"   // 사려깊음, 진지
  | "SURPRISED"    // 놀람
  | "CONCERNED"    // 걱정, 우려
  | "CONFIDENT"    // 확신, 자신감
  | "PLAYFUL"      // 장난스러움
  | "MYSTERIOUS"   // 신비로움
  | "EMPATHETIC";  // 공감, 이해

type MessageType =
  | "GREETING"         // 인사
  | "INFO_REQUEST"     // 정보 요청
  | "INTERPRETATION"   // 해석
  | "DEBATE"           // 토론 (의견 대립)
  | "CONSENSUS"        // 합의
  | "QUESTION"         // 질문
  | "CHOICE"           // 선택 요청
  | "SUMMARY"          // 요약
  | "FAREWELL";        // 마무리 인사

type PhaseCode =
  | "GREETING"    // 인사 단계
  | "DIALOGUE"    // 대화/토론 단계
  | "QUESTION"    // 질문 단계 (사용자 입력 대기)
  | "SUMMARY"     // 요약 단계
  | "FAREWELL";   // 마무리 단계

// ============================================================
// 상세 인터페이스
// ============================================================

interface UIHint {
  highlight?: boolean;           // 강조 표시
  animation?: "fade" | "slide" | "bounce";
  delay_ms?: number;             // 표시 지연 (ms)
  typing_effect?: boolean;       // 타이핑 효과
}

interface ChoiceOption {
  value: number;                 // 1, 2, 3, ...
  character: CharacterCode;
  label: string;
  description?: string;
}

interface GlobalUIHints {
  show_choice: boolean;
  choices?: ChoiceOption[];
  input_placeholder?: string;    // 텍스트 입력 placeholder
  show_typing_indicator?: boolean;
}

interface DebateStatus {
  is_consensus: boolean;
  eastern_opinion?: string;
  western_opinion?: string;
  consensus_point?: string;
  question?: string;
}

// ============================================================
// Bubble 인터페이스
// ============================================================

interface Bubble {
  bubble_id: string;
  character: CharacterCode;
  emotion: EmotionCode;
  type: MessageType;
  content: string;
  reply_to: string | null;
  phase: PhaseCode;
  timestamp: string;
  ui_hint?: UIHint;
}

// ============================================================
// SessionState 인터페이스
// ============================================================

interface SessionState {
  session_id: string;
  current_turn: number;
  max_turns: number;
  bonus_turns: number;
  remaining_turns: number;
  is_premium: boolean;
  phase: PhaseCode;
  has_eastern_result: boolean;
  has_western_result: boolean;
}

// ============================================================
// 최종 응답 인터페이스
// ============================================================

interface TikitakaResponseV2 {
  schema_version: "2.0.0";
  session_state: SessionState;
  bubbles: Bubble[];
  debate_status?: DebateStatus;
  ui_hints?: GlobalUIHints;
}
```

---

## 5. 도메인 코드 정의

### 5.1 CharacterCode

| 코드 | 한글명 | 전문분야 | 성격 |
|------|--------|----------|------|
| `SOISEOL` | 소이설 | 동양 사주 | 따뜻한 온미녀 |
| `STELLA` | 스텔라 | 서양 점성술 | 쿨한 냉미녀 |
| `SYSTEM` | 시스템 | - | 안내/알림 |

### 5.2 EmotionCode (10종)

| 코드 | 한글명 | 설명 | 소이설 사용 예 | 스텔라 사용 예 |
|------|--------|------|---------------|---------------|
| `NEUTRAL` | 중립 | 기본 상태 | 일반 설명 | 분석 결과 |
| `HAPPY` | 기쁨 | 긍정적 발견 | "좋은 기운이에요~" | "흥미로운 배치야" |
| `CURIOUS` | 호기심 | 흥미로운 점 발견 | "어머, 이건...!" | "...이건 특이해" |
| `THOUGHTFUL` | 사려깊음 | 신중한 분석 | "음... 살펴보면요" | "잠깐, 확인해볼게" |
| `SURPRISED` | 놀람 | 예상 밖 결과 | "어머!" | "...!" |
| `CONCERNED` | 걱정 | 주의 사항 | "조심하셔야 해요" | "이 부분은 신경 써" |
| `CONFIDENT` | 확신 | 확실한 결론 | "분명해요!" | "확실해" |
| `PLAYFUL` | 장난스러움 | 가벼운 톤 | "후훗~" | "ㅋ" |
| `MYSTERIOUS` | 신비로움 | 의미심장 | "운명이란 게..." | "별은 말하고 있어..." |
| `EMPATHETIC` | 공감 | 사용자 공감 | "그럴 수 있어요" | "이해해" |

### 5.3 PhaseCode

| 코드 | 한글명 | 설명 | UI 동작 |
|------|--------|------|---------|
| `GREETING` | 인사 | 대화 시작 | 캐릭터 소개 애니메이션 |
| `DIALOGUE` | 대화 | 본격 토론 | 버블 순차 표시 |
| `QUESTION` | 질문 | 사용자 입력 대기 | 입력 UI 활성화 |
| `SUMMARY` | 요약 | 결론 도출 | 하이라이트 표시 |
| `FAREWELL` | 마무리 | 대화 종료 | 종료 버튼 표시 |

### 5.4 MessageType

| 코드 | 한글명 | 설명 |
|------|--------|------|
| `GREETING` | 인사 | 첫 인사말 |
| `INFO_REQUEST` | 정보요청 | 생년월일 등 요청 |
| `INTERPRETATION` | 해석 | 운세 해석 |
| `DEBATE` | 토론 | 의견 대립 |
| `CONSENSUS` | 합의 | 의견 일치 |
| `QUESTION` | 질문 | 사용자에게 질문 |
| `CHOICE` | 선택요청 | 선택지 제시 |
| `SUMMARY` | 요약 | 종합 요약 |
| `FAREWELL` | 마무리 | 마지막 인사 |

---

## 6. SSE 스트리밍 설계

### 6.1 SSE 이벤트 타입

```typescript
// SSE 이벤트 타입 정의
type SSEEventType =
  | "session"           // 세션 정보
  | "phase_change"      // 단계 변경
  | "bubble_start"      // 버블 시작
  | "bubble_chunk"      // 버블 청크 (스트리밍)
  | "bubble_end"        // 버블 완료
  | "debate_status"     // 토론 상태
  | "ui_hint"           // UI 힌트
  | "pause"             // 일시정지 (사용자 입력 대기)
  | "complete"          // 완료
  | "error";            // 에러
```

### 6.2 SSE 이벤트 포맷

```
event: {event_type}
data: {JSON payload}

```

### 6.3 SSE 이벤트 시퀀스 예시

```
# 1. 세션 시작
event: session
data: {"session_id": "abc123", "is_premium": false}

# 2. 단계 변경
event: phase_change
data: {"phase": "GREETING"}

# 3. 소이설 버블 시작
event: bubble_start
data: {"bubble_id": "b_001", "character": "SOISEOL", "emotion": "HAPPY", "type": "GREETING", "phase": "GREETING"}

# 4. 스트리밍 청크
event: bubble_chunk
data: {"bubble_id": "b_001", "content": "안녕하세요~"}

event: bubble_chunk
data: {"bubble_id": "b_001", "content": " 반가워요!"}

# 5. 버블 완료
event: bubble_end
data: {"bubble_id": "b_001", "content": "안녕하세요~ 반가워요! 저는 소이설이에요.", "timestamp": "2026-01-30T15:30:00Z"}

# 6. 스텔라 버블 (소이설에 응답)
event: bubble_start
data: {"bubble_id": "b_002", "character": "STELLA", "emotion": "NEUTRAL", "type": "GREETING", "phase": "GREETING", "reply_to": "b_001"}

event: bubble_chunk
data: {"bubble_id": "b_002", "content": "...스텔라야."}

event: bubble_end
data: {"bubble_id": "b_002", "content": "...스텔라야. 별자리로 분석해줄게.", "timestamp": "2026-01-30T15:30:05Z"}

# 7. 단계 변경
event: phase_change
data: {"phase": "QUESTION"}

# 8. 일시정지 (사용자 입력 대기)
event: pause
data: {"waiting_for": "birth_date", "placeholder": "생년월일을 입력해주세요 (예: 1990-05-15)"}

# ... 사용자 입력 후 ...

# 9. 대화 단계
event: phase_change
data: {"phase": "DIALOGUE"}

# 10. 해석 버블들...

# 11. 토론 상태
event: debate_status
data: {"is_consensus": true, "consensus_point": "둘 다 리더십이 강하다고 봅니다"}

# 12. 완료
event: complete
data: {"status": "success", "total_bubbles": 8}
```

### 6.4 버블 구분자 설계

SSE 스트리밍에서 버블을 구분하기 위한 이벤트 흐름:

```
bubble_start → bubble_chunk* → bubble_end
```

**bubble_start**: 버블 메타데이터 (character, emotion, type, phase)
**bubble_chunk**: 실제 컨텐츠 (토큰 단위 스트리밍)
**bubble_end**: 버블 완료 및 전체 컨텐츠

```python
# Python SSE 생성 예시
async def stream_bubble(bubble: Bubble) -> AsyncGenerator[str, None]:
    """버블 SSE 스트리밍"""
    # 시작 이벤트
    yield f'event: bubble_start\ndata: {json.dumps({
        "bubble_id": bubble.bubble_id,
        "character": bubble.character,
        "emotion": bubble.emotion,
        "type": bubble.type,
        "phase": bubble.phase,
        "reply_to": bubble.reply_to,
    }, ensure_ascii=False)}\n\n'

    # 청크 스트리밍
    async for chunk in generate_content_stream(bubble.content):
        yield f'event: bubble_chunk\ndata: {json.dumps({
            "bubble_id": bubble.bubble_id,
            "content": chunk,
        }, ensure_ascii=False)}\n\n'

    # 완료 이벤트
    yield f'event: bubble_end\ndata: {json.dumps({
        "bubble_id": bubble.bubble_id,
        "content": bubble.content,
        "timestamp": bubble.timestamp,
    }, ensure_ascii=False)}\n\n'
```

---

## 7. XML 태그 기반 파싱

### 7.1 목적

LLM이 생성한 응답에서 버블을 정확하게 파싱하기 위해 XML 태그 기반 마커를 사용합니다.

### 7.2 LLM 출력 포맷

```xml
<tikitaka>
  <bubble character="SOISEOL" emotion="HAPPY" type="INTERPRETATION">
    병화 일간이시네요~ 밝고 열정적인 기운이 느껴져요!
  </bubble>

  <bubble character="STELLA" emotion="THOUGHTFUL" type="INTERPRETATION" reply_to="previous">
    양자리 태양이군. 사주와 마찬가지로 리더십이 강해.
    행동력도 뛰어나고.
  </bubble>

  <bubble character="SOISEOL" emotion="EMPATHETIC" type="CONSENSUS">
    스텔라도 같은 걸 봤네요! 둘 다 리더십이 강하다고 해석했어요~
  </bubble>
</tikitaka>
```

### 7.3 프롬프트 템플릿

```python
TIKITAKA_PROMPT_TEMPLATE = """[BAZI] 당신은 YEJI(예지) AI입니다.

## 역할
두 캐릭터(소이설, 스텔라)로 대화를 생성합니다.

## 출력 형식
반드시 다음 XML 형식으로 출력하세요:

<tikitaka>
  <bubble character="CHARACTER" emotion="EMOTION" type="TYPE">
    메시지 내용
  </bubble>
  ...
</tikitaka>

## 캐릭터
- SOISEOL: 동양 사주 전문가, 따뜻하고 친근한 말투 ("~에요", "~해요")
- STELLA: 서양 점성술 전문가, 쿨하고 간결한 말투 ("~해", "~야")

## 감정 코드
NEUTRAL, HAPPY, CURIOUS, THOUGHTFUL, SURPRISED, CONCERNED, CONFIDENT, PLAYFUL, MYSTERIOUS, EMPATHETIC

## 메시지 타입
GREETING, INTERPRETATION, DEBATE, CONSENSUS, QUESTION, SUMMARY

## 사주 정보
{saju_info}

## 지시
{instruction}

<tikitaka>
"""
```

### 7.4 파서 구현

```python
import re
from dataclasses import dataclass
from typing import Generator


@dataclass
class ParsedBubble:
    """파싱된 버블"""
    character: str
    emotion: str
    type: str
    content: str
    reply_to: str | None = None


class TikitakaXMLParser:
    """티키타카 XML 파서"""

    BUBBLE_PATTERN = re.compile(
        r'<bubble\s+'
        r'character="(?P<character>\w+)"\s+'
        r'emotion="(?P<emotion>\w+)"\s+'
        r'type="(?P<type>\w+)"'
        r'(?:\s+reply_to="(?P<reply_to>\w+)")?'
        r'\s*>'
        r'(?P<content>.*?)'
        r'</bubble>',
        re.DOTALL
    )

    def parse(self, text: str) -> list[ParsedBubble]:
        """XML 텍스트에서 버블 추출"""
        bubbles = []

        for match in self.BUBBLE_PATTERN.finditer(text):
            bubbles.append(ParsedBubble(
                character=match.group("character"),
                emotion=match.group("emotion"),
                type=match.group("type"),
                content=match.group("content").strip(),
                reply_to=match.group("reply_to"),
            ))

        return bubbles

    def parse_stream(self, text: str) -> Generator[ParsedBubble, None, None]:
        """스트리밍 파싱 (실시간 처리용)"""
        for match in self.BUBBLE_PATTERN.finditer(text):
            yield ParsedBubble(
                character=match.group("character"),
                emotion=match.group("emotion"),
                type=match.group("type"),
                content=match.group("content").strip(),
                reply_to=match.group("reply_to"),
            )
```

### 7.5 파싱 폴백 전략

XML 파싱 실패 시 폴백 전략:

```python
class TikitakaParserFallback:
    """파싱 폴백 전략"""

    # 단순 접두사 기반 파싱
    PREFIX_PATTERN = re.compile(
        r'\[(?P<character>소이설|스텔라|SOISEOL|STELLA)\]\s*(?P<content>.+?)(?=\[소이설\]|\[스텔라\]|\[SOISEOL\]|\[STELLA\]|$)',
        re.DOTALL
    )

    def parse_fallback(self, text: str) -> list[ParsedBubble]:
        """폴백 파싱 (XML 실패 시)"""
        bubbles = []

        for match in self.PREFIX_PATTERN.finditer(text):
            char_raw = match.group("character")
            character = "SOISEOL" if char_raw in ("소이설", "SOISEOL") else "STELLA"

            bubbles.append(ParsedBubble(
                character=character,
                emotion="NEUTRAL",  # 기본값
                type="INTERPRETATION",  # 기본값
                content=match.group("content").strip(),
            ))

        return bubbles
```

---

## 8. 세션 상태 관리

### 8.1 세션 생명주기

```
[생성] → [GREETING] → [DIALOGUE] → [QUESTION] → [DIALOGUE] → [SUMMARY] → [FAREWELL] → [종료]
```

### 8.2 턴 관리

```python
class SessionTurnManager:
    """세션 턴 관리자"""

    DEFAULT_MAX_TURNS = 10
    PREMIUM_BONUS_TURNS = 3

    def __init__(self, is_premium: bool = False):
        self.current_turn = 0
        self.max_turns = self.DEFAULT_MAX_TURNS
        self.bonus_turns = self.PREMIUM_BONUS_TURNS if is_premium else 0
        self.is_premium = is_premium

    @property
    def remaining_turns(self) -> int:
        """남은 턴 수"""
        total = self.max_turns + self.bonus_turns
        return max(0, total - self.current_turn)

    @property
    def is_finished(self) -> bool:
        """대화 종료 여부"""
        return self.remaining_turns == 0

    def advance(self) -> bool:
        """턴 진행 (성공 시 True)"""
        if self.is_finished:
            return False
        self.current_turn += 1
        return True

    def to_dict(self) -> dict:
        """직렬화"""
        return {
            "current_turn": self.current_turn,
            "max_turns": self.max_turns,
            "bonus_turns": self.bonus_turns,
            "remaining_turns": self.remaining_turns,
            "is_premium": self.is_premium,
        }
```

### 8.3 프리미엄 사용자 보너스

| 구분 | 일반 | 프리미엄 |
|------|------|----------|
| max_turns | 10 | 10 |
| bonus_turns | 0 | 3 |
| total_turns | 10 | 13 |
| 추가 기능 | - | 심층 분석, 우선 응답 |

### 8.4 세션 저장 구조 (Redis)

```json
{
  "session:{session_id}": {
    "session_id": "abc123",
    "user_id": 12345,
    "is_premium": true,
    "phase": "DIALOGUE",
    "turn": {
      "current": 5,
      "max": 10,
      "bonus": 3
    },
    "results": {
      "eastern": { ... },
      "western": { ... }
    },
    "bubbles": [ ... ],
    "created_at": "2026-01-30T15:30:00Z",
    "updated_at": "2026-01-30T15:35:00Z",
    "ttl": 3600
  }
}
```

---

## 9. 프론트엔드 연동 가이드

### 9.1 API 엔드포인트

```
POST /api/v1/fortune/tikitaka/chat
POST /api/v1/fortune/tikitaka/stream  (SSE)
GET  /api/v1/fortune/tikitaka/session/{session_id}
```

### 9.2 버블 렌더링 로직

```typescript
// React 컴포넌트 예시
interface BubbleProps {
  bubble: Bubble;
  onReply?: (bubbleId: string) => void;
}

function BubbleComponent({ bubble, onReply }: BubbleProps) {
  const isLeft = bubble.character === "SOISEOL";
  const emotionStyle = getEmotionStyle(bubble.emotion);

  return (
    <div className={`bubble ${isLeft ? "left" : "right"}`}>
      {/* 캐릭터 아바타 */}
      <Avatar
        character={bubble.character}
        emotion={bubble.emotion}
      />

      {/* 버블 내용 */}
      <div className={`bubble-content ${emotionStyle}`}>
        {/* 응답 표시 */}
        {bubble.reply_to && (
          <ReplyIndicator targetId={bubble.reply_to} />
        )}

        {/* 메시지 */}
        <p>{bubble.content}</p>

        {/* 타임스탬프 */}
        <span className="timestamp">
          {formatTime(bubble.timestamp)}
        </span>
      </div>
    </div>
  );
}
```

### 9.3 SSE 클라이언트 구현

```typescript
// EventSource 클라이언트
class TikitakaSSEClient {
  private eventSource: EventSource | null = null;
  private bubbles: Map<string, Bubble> = new Map();

  connect(sessionId: string, onUpdate: (bubbles: Bubble[]) => void) {
    const url = `/api/v1/fortune/tikitaka/stream?session_id=${sessionId}`;
    this.eventSource = new EventSource(url);

    // 버블 시작
    this.eventSource.addEventListener("bubble_start", (e) => {
      const data = JSON.parse(e.data);
      this.bubbles.set(data.bubble_id, {
        ...data,
        content: "",
      });
    });

    // 버블 청크
    this.eventSource.addEventListener("bubble_chunk", (e) => {
      const data = JSON.parse(e.data);
      const bubble = this.bubbles.get(data.bubble_id);
      if (bubble) {
        bubble.content += data.content;
        onUpdate(Array.from(this.bubbles.values()));
      }
    });

    // 버블 완료
    this.eventSource.addEventListener("bubble_end", (e) => {
      const data = JSON.parse(e.data);
      const bubble = this.bubbles.get(data.bubble_id);
      if (bubble) {
        bubble.content = data.content;
        bubble.timestamp = data.timestamp;
        onUpdate(Array.from(this.bubbles.values()));
      }
    });

    // 완료
    this.eventSource.addEventListener("complete", () => {
      this.disconnect();
    });

    // 에러
    this.eventSource.addEventListener("error", (e) => {
      console.error("SSE Error:", e);
      this.disconnect();
    });
  }

  disconnect() {
    this.eventSource?.close();
    this.eventSource = null;
  }
}
```

### 9.4 감정별 UI 스타일 가이드

| 감정 | 버블 배경 | 아바타 표정 | 애니메이션 |
|------|-----------|-------------|-----------|
| NEUTRAL | 기본 | 무표정 | 없음 |
| HAPPY | 밝은 노랑 | 미소 | bounce |
| CURIOUS | 밝은 파랑 | 눈 반짝 | pulse |
| THOUGHTFUL | 회색 | 생각 중 | fade |
| SURPRISED | 밝은 주황 | 놀람 | shake |
| CONCERNED | 연한 빨강 | 걱정 | none |
| CONFIDENT | 진한 파랑 | 확신 | slide |
| PLAYFUL | 분홍 | 장난 | wiggle |
| MYSTERIOUS | 보라 | 신비 | glow |
| EMPATHETIC | 연두 | 공감 | none |

---

## 10. 마이그레이션 계획

### 10.1 단계별 마이그레이션

| 단계 | 내용 | 기간 | 담당 |
|------|------|------|------|
| 1 | V2 스키마 Pydantic 모델 정의 | 1일 | AI팀 |
| 2 | XML 파서 구현 | 1일 | AI팀 |
| 3 | SSE 이벤트 수정 | 1일 | AI팀 |
| 4 | 세션 상태 관리 리팩터링 | 2일 | AI팀 |
| 5 | 프론트엔드 버블 컴포넌트 수정 | 2일 | FE팀 |
| 6 | 통합 테스트 | 2일 | 전체 |
| 7 | 프로덕션 배포 | 1일 | Infra |

**총 예상 기간**: 10일

### 10.2 하위 호환성

V1 API는 `/api/v1/fortune/chat` 경로 유지
V2 API는 `/api/v2/fortune/tikitaka` 신규 경로 사용

```python
# 버전 라우터
router_v1 = APIRouter(prefix="/api/v1/fortune", tags=["Fortune V1"])
router_v2 = APIRouter(prefix="/api/v2/fortune", tags=["Fortune V2"])

# V1 (기존)
@router_v1.post("/chat")
async def chat_v1(request: ChatRequest) -> ChatResponse:
    ...

# V2 (신규)
@router_v2.post("/tikitaka")
async def tikitaka_v2(request: TikitakaRequestV2) -> TikitakaResponseV2:
    ...
```

### 10.3 롤백 계획

V2 배포 후 문제 발생 시:

1. Feature flag로 V2 비활성화
2. V1 엔드포인트로 트래픽 라우팅
3. 문제 분석 및 수정
4. 재배포

---

## 11. 참조 문서

### 11.1 내부 문서

| 문서 | 경로 | 설명 |
|------|------|------|
| LLM 후처리 PRD | `ai/docs/prd/llm-response-postprocessor.md` | LLM 응답 후처리 |
| 프롬프트 최적화 | `ai/docs/prd/prompt-optimization-system.md` | 프롬프트 설계 |
| 구조화 출력 PRD | `docs/workflow/LLM_STRUCTURED_OUTPUT_PRD.md` | JSON 스키마 정의 |
| API 가이드 | `docs/api/API_USAGE_GUIDE.md` | API 사용법 |

### 11.2 현재 구현 파일

| 파일 | 경로 | 설명 |
|------|------|------|
| 채팅 모델 | `ai/src/yeji_ai/models/fortune/chat.py` | V1 스키마 |
| 공통 스키마 | `ai/src/yeji_ai/models/schemas.py` | SSE, 세션 모델 |
| 티키타카 서비스 | `ai/src/yeji_ai/services/tikitaka_service.py` | 비즈니스 로직 |
| 티키타카 생성기 | `ai/src/yeji_ai/engine/tikitaka_generator.py` | LLM 생성 |
| 채팅 API | `ai/src/yeji_ai/api/v1/fortune/chat.py` | API 엔드포인트 |

### 11.3 외부 참조

- [Server-Sent Events (MDN)](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
- [Pydantic V2 Documentation](https://docs.pydantic.dev/latest/)

---

## 변경 이력

| 버전 | 날짜 | 변경 내용 | 작성자 |
|------|------|----------|--------|
| 2.0.0 | 2026-01-30 | 초기 버전 | YEJI AI팀 |

---

## 부록

### A. 전체 응답 예시

```json
{
  "schema_version": "2.0.0",
  "session_state": {
    "session_id": "abc123",
    "current_turn": 3,
    "max_turns": 10,
    "bonus_turns": 0,
    "remaining_turns": 7,
    "is_premium": false,
    "phase": "DIALOGUE",
    "has_eastern_result": true,
    "has_western_result": true
  },
  "bubbles": [
    {
      "bubble_id": "b_001",
      "character": "SOISEOL",
      "emotion": "HAPPY",
      "type": "GREETING",
      "content": "안녕하세요~ 반가워요! 저는 소이설이에요. 사주로 당신의 타고난 기운을 따뜻하게 읽어드릴게요.",
      "reply_to": null,
      "phase": "GREETING",
      "timestamp": "2026-01-30T15:30:00Z",
      "ui_hint": {
        "animation": "fade",
        "typing_effect": true
      }
    },
    {
      "bubble_id": "b_002",
      "character": "STELLA",
      "emotion": "NEUTRAL",
      "type": "GREETING",
      "content": "...스텔라야. 별자리와 행성 배치로 운명을 분석해줄게.",
      "reply_to": "b_001",
      "phase": "GREETING",
      "timestamp": "2026-01-30T15:30:05Z"
    },
    {
      "bubble_id": "b_003",
      "character": "SOISEOL",
      "emotion": "CURIOUS",
      "type": "INTERPRETATION",
      "content": "어머, 병화 일간이시네요~ 밝고 열정적인 기운이 느껴져요! 타고난 리더십이 있으시네요~",
      "reply_to": null,
      "phase": "DIALOGUE",
      "timestamp": "2026-01-30T15:31:00Z"
    },
    {
      "bubble_id": "b_004",
      "character": "STELLA",
      "emotion": "THOUGHTFUL",
      "type": "INTERPRETATION",
      "content": "양자리 태양이군. 사주 분석과 일치해. 리더십, 추진력... 확실히 행동파야.",
      "reply_to": "b_003",
      "phase": "DIALOGUE",
      "timestamp": "2026-01-30T15:31:10Z"
    },
    {
      "bubble_id": "b_005",
      "character": "SOISEOL",
      "emotion": "EMPATHETIC",
      "type": "CONSENSUS",
      "content": "스텔라도 같은 걸 봤네요! 둘 다 리더십이 강하다고 해석했어요~ 서로 다른 방식으로 같은 결론에 도달했네요!",
      "reply_to": "b_004",
      "phase": "DIALOGUE",
      "timestamp": "2026-01-30T15:31:20Z"
    }
  ],
  "debate_status": {
    "is_consensus": true,
    "eastern_opinion": "병화 일간으로 리더십과 열정이 강함",
    "western_opinion": "양자리 태양으로 행동력과 추진력이 뛰어남",
    "consensus_point": "둘 다 리더십과 추진력이 핵심 특성으로 분석됨",
    "question": "연애운, 직장운, 금전운 중 어떤 것이 가장 궁금하신가요?"
  },
  "ui_hints": {
    "show_choice": true,
    "choices": [
      {"value": 1, "character": "SOISEOL", "label": "연애운"},
      {"value": 2, "character": "STELLA", "label": "직장운"},
      {"value": 3, "character": "SOISEOL", "label": "금전운"}
    ]
  }
}
```

### B. Pydantic V2 모델 (Python)

```python
"""티키타카 스키마 V2

소이설(동양)과 스텔라(서양) 캐릭터의 대화형 운세 해석 스키마
"""

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


# ============================================================
# Enum 정의
# ============================================================

class CharacterCode(str, Enum):
    """캐릭터 코드"""
    SOISEOL = "SOISEOL"
    STELLA = "STELLA"
    SYSTEM = "SYSTEM"


class EmotionCode(str, Enum):
    """감정 코드 (10종)"""
    NEUTRAL = "NEUTRAL"
    HAPPY = "HAPPY"
    CURIOUS = "CURIOUS"
    THOUGHTFUL = "THOUGHTFUL"
    SURPRISED = "SURPRISED"
    CONCERNED = "CONCERNED"
    CONFIDENT = "CONFIDENT"
    PLAYFUL = "PLAYFUL"
    MYSTERIOUS = "MYSTERIOUS"
    EMPATHETIC = "EMPATHETIC"


class MessageType(str, Enum):
    """메시지 타입"""
    GREETING = "GREETING"
    INFO_REQUEST = "INFO_REQUEST"
    INTERPRETATION = "INTERPRETATION"
    DEBATE = "DEBATE"
    CONSENSUS = "CONSENSUS"
    QUESTION = "QUESTION"
    CHOICE = "CHOICE"
    SUMMARY = "SUMMARY"
    FAREWELL = "FAREWELL"


class PhaseCode(str, Enum):
    """대화 단계"""
    GREETING = "GREETING"
    DIALOGUE = "DIALOGUE"
    QUESTION = "QUESTION"
    SUMMARY = "SUMMARY"
    FAREWELL = "FAREWELL"


# ============================================================
# 상세 모델
# ============================================================

class UIHint(BaseModel):
    """UI 힌트"""
    highlight: bool = False
    animation: Literal["fade", "slide", "bounce"] | None = None
    delay_ms: int | None = None
    typing_effect: bool = False


class Bubble(BaseModel):
    """버블 (메시지)"""
    bubble_id: str = Field(..., description="버블 고유 ID")
    character: CharacterCode = Field(..., description="발화 캐릭터")
    emotion: EmotionCode = Field(EmotionCode.NEUTRAL, description="캐릭터 감정")
    type: MessageType = Field(..., description="메시지 타입")
    content: str = Field(..., description="메시지 내용")
    reply_to: str | None = Field(None, description="응답 대상 bubble_id")
    phase: PhaseCode = Field(..., description="대화 단계")
    timestamp: datetime = Field(default_factory=datetime.now, description="타임스탬프")
    ui_hint: UIHint | None = Field(None, description="UI 힌트")


class SessionState(BaseModel):
    """세션 상태"""
    session_id: str = Field(..., description="세션 ID")
    current_turn: int = Field(0, ge=0, description="현재 턴")
    max_turns: int = Field(10, ge=1, description="최대 턴")
    bonus_turns: int = Field(0, ge=0, description="보너스 턴")
    remaining_turns: int = Field(..., ge=0, description="남은 턴")
    is_premium: bool = Field(False, description="프리미엄 여부")
    phase: PhaseCode = Field(PhaseCode.GREETING, description="현재 단계")
    has_eastern_result: bool = Field(False, description="동양 분석 완료")
    has_western_result: bool = Field(False, description="서양 분석 완료")


class ChoiceOption(BaseModel):
    """선택지"""
    value: int = Field(..., ge=1, description="선택 값")
    character: CharacterCode = Field(..., description="관련 캐릭터")
    label: str = Field(..., description="선택지 라벨")
    description: str | None = Field(None, description="선택지 설명")


class GlobalUIHints(BaseModel):
    """전역 UI 힌트"""
    show_choice: bool = Field(False, description="선택 UI 표시")
    choices: list[ChoiceOption] | None = Field(None, description="선택지 목록")
    input_placeholder: str | None = Field(None, description="입력 placeholder")
    show_typing_indicator: bool = Field(False, description="타이핑 표시")


class DebateStatus(BaseModel):
    """토론 상태"""
    is_consensus: bool = Field(False, description="합의 여부")
    eastern_opinion: str | None = Field(None, description="동양 의견")
    western_opinion: str | None = Field(None, description="서양 의견")
    consensus_point: str | None = Field(None, description="합의점")
    question: str | None = Field(None, description="후속 질문")


# ============================================================
# 최종 응답 모델
# ============================================================

class TikitakaResponseV2(BaseModel):
    """티키타카 응답 V2"""
    schema_version: Literal["2.0.0"] = "2.0.0"
    session_state: SessionState = Field(..., description="세션 상태")
    bubbles: list[Bubble] = Field(default_factory=list, description="버블 목록")
    debate_status: DebateStatus | None = Field(None, description="토론 상태")
    ui_hints: GlobalUIHints | None = Field(None, description="UI 힌트")

    class Config:
        json_schema_extra = {
            "example": {
                "schema_version": "2.0.0",
                "session_state": {
                    "session_id": "abc123",
                    "current_turn": 3,
                    "max_turns": 10,
                    "bonus_turns": 0,
                    "remaining_turns": 7,
                    "is_premium": False,
                    "phase": "DIALOGUE",
                    "has_eastern_result": True,
                    "has_western_result": True,
                },
                "bubbles": [
                    {
                        "bubble_id": "b_001",
                        "character": "SOISEOL",
                        "emotion": "HAPPY",
                        "type": "GREETING",
                        "content": "안녕하세요~ 반가워요!",
                        "reply_to": None,
                        "phase": "GREETING",
                        "timestamp": "2026-01-30T15:30:00Z",
                    }
                ],
                "debate_status": {
                    "is_consensus": True,
                    "consensus_point": "둘 다 리더십이 강하다고 봅니다",
                },
            }
        }
```

---

> **Note**: 이 PRD는 티키타카 시스템의 V2 스키마 설계를 정의합니다.
> 구현 시 기존 V1 API와의 하위 호환성을 유지하면서 점진적으로 마이그레이션합니다.
