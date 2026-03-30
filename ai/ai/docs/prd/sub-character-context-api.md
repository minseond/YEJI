# 서브 캐릭터 간 대화 컨텍스트 전달 API PRD

> **문서 버전**: 1.0.0
> **작성일**: 2026-01-31
> **상태**: 설계 (Design)
> **담당팀**: SSAFY YEJI AI팀

---

## 목차

1. [배경 및 목적](#1-배경-및-목적)
2. [문제 정의](#2-문제-정의)
3. [목표 및 성공 지표](#3-목표-및-성공-지표)
4. [API 스펙](#4-api-스펙)
5. [데이터 모델](#5-데이터-모델)
6. [시퀀스 다이어그램](#6-시퀀스-다이어그램)
7. [구현 고려사항](#7-구현-고려사항)
8. [향후 확장](#8-향후-확장)
9. [참조 문서](#9-참조-문서)

---

## 1. 배경 및 목적

### 1.1 배경

현재 티키타카 시스템은 6명의 캐릭터를 지원합니다:

| 캐릭터 | 코드 | 역할 | 말투 |
|--------|------|------|------|
| 소이설 | `SOISEOL` | 동양 사주 전문가 (메인) | 하오체/하게체 |
| 스텔라 | `STELLA` | 서양 점성술 전문가 (메인) | 해요체 |
| 청운 | `CHEONGWOON` | 소이설 스승/신선 (서브) | 하오체 (시적) |
| 화린 | `HWARIN` | 청룡상단 지부장 (서브) | 해요체 (나른) |
| 카일 | `KYLE` | 도박사/정보상 (서브) | 반말+존댓말 혼용 |
| 엘라리아 | `ELARIA` | 사파이어 왕국 공주 (서브) | 하십시오체/해요체 |

**티키타카 3턴 대화**란 서브 캐릭터들이 순차적으로 대화하며 운세를 해석하는 기능입니다:

```
[턴 1] 소이설 → "병화 일간이시오. 열정적인 기운이 느껴지오."
[턴 2] 청운 → "허허, 제자의 말이 옳소. 이 사주는 화기가 왕성하오."
[턴 3] 스텔라 → "양자리 태양이군. 동양 분석과 일치해."
```

### 1.2 현재 상황

- **현재 API**: `POST /v1/fortune/chat/test-character`
- **문제점**: 요청마다 독립적으로 처리되어 이전 대화 맥락이 전달되지 않음
- **결과**: 3턴 대화 시 캐릭터 간 연속성 부족, 자연스러운 대화 흐름 불가

### 1.3 목표

티키타카 3턴 대화에서 서브 캐릭터 간 컨텍스트(이전 대화 내용)를 유지하기 위한 API 설계

**핵심 요구사항:**
1. **세션 기반 컨텍스트 관리**: session_id로 대화 세션 관리
2. **캐릭터 전환 지원**: 소이설 → 청운 → 스텔라 등 캐릭터 전환 시 컨텍스트 유지
3. **토큰 효율성**: 토큰 제한 고려한 컨텍스트 압축

---

## 2. 문제 정의

### 2.1 현재 API 한계

```python
# 현재: yeji_ai/api/v1/fortune/chat.py
class CharacterTestRequest(BaseModel):
    character: SubCharacterCode  # CHEONGWOON, HWARIN, KYLE, ELARIA
    message: str = "자기 소개를 해주세요."

# 문제점: 이전 대화 컨텍스트를 전달할 방법 없음
```

### 2.2 문제점 분석

| 문제 | 설명 | 영향 |
|------|------|------|
| 컨텍스트 부재 | 각 요청이 독립적 | 캐릭터 간 대화 연속성 없음 |
| 세션 미지원 | session_id 미사용 | 대화 히스토리 추적 불가 |
| 캐릭터 전환 불가 | 단일 캐릭터만 응답 | 멀티 캐릭터 대화 불가 |
| 분석 결과 미전달 | 사주/점성술 결과 미포함 | 운세 해석 일관성 부족 |

### 2.3 AS-IS 흐름

```
클라이언트                          서버
    |                               |
    |--- POST /chat/test-character -->|  (character=CHEONGWOON, message="운세 알려줘")
    |<-- 청운 응답 ------------------|
    |                               |
    |--- POST /chat/test-character -->|  (character=KYLE, message="더 알려줘")
    |<-- 카일 응답 (컨텍스트 없음) ---|
    |                               |
    |--- POST /chat/test-character -->|  (character=ELARIA, message="정리해줘")
    |<-- 엘라리아 응답 (컨텍스트 없음)|
```

### 2.4 TO-BE 흐름

```
클라이언트                                      서버
    |                                           |
    |--- POST /chat/sub-character --------------->|
    |    {                                        |
    |      session_id: null,                      |  [새 세션 생성]
    |      character: "CHEONGWOON",               |
    |      message: "운세 알려줘",                  |
    |      birth_date: "1990-05-15"               |
    |    }                                        |
    |<--- 청운 응답 + session_id: "abc123" --------|
    |                                             |
    |--- POST /chat/sub-character --------------->|
    |    {                                        |
    |      session_id: "abc123",                  |  [컨텍스트 유지]
    |      character: "KYLE",                     |
    |      message: "더 알려줘"                    |
    |    }                                        |
    |<--- 카일 응답 (청운 대화 참조) ---------------|
    |                                             |
    |--- POST /chat/sub-character --------------->|
    |    {                                        |
    |      session_id: "abc123",                  |  [컨텍스트 유지]
    |      character: "ELARIA",                   |
    |      message: "정리해줘"                     |
    |    }                                        |
    |<--- 엘라리아 응답 (전체 대화 참조) ------------|
```

---

## 3. 목표 및 성공 지표

### 3.1 목표

1. **컨텍스트 유지**: 캐릭터 전환 시 이전 대화 내용 유지
2. **토큰 효율성**: 컨텍스트 압축으로 토큰 사용량 최적화
3. **세션 관리**: 세션 생성/조회/만료 처리
4. **확장성**: 향후 멀티 캐릭터 동시 대화 지원 기반 마련

### 3.2 성공 지표 (KPI)

| 지표 | 현재 | 목표 | 측정 방법 |
|------|------|------|----------|
| 대화 연속성 점수 | N/A | 4.0/5 | 사용자 피드백 |
| 컨텍스트 참조율 | 0% | 95% | 응답 분석 |
| 평균 토큰 사용량 | N/A | 2000/턴 | 모니터링 |
| 세션 만료 처리율 | N/A | 100% | 시스템 로그 |

### 3.3 비목표 (Out of Scope)

- 실시간 음성 대화
- 캐릭터 자동 전환 로직
- 영구 세션 저장 (DB)

---

## 4. API 스펙

### 4.1 엔드포인트 개요

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/v1/fortune/chat/sub-character` | 서브 캐릭터 대화 (컨텍스트 지원) |
| POST | `/v1/fortune/chat/sub-character/stream` | 서브 캐릭터 대화 (SSE 스트리밍) |
| GET | `/v1/fortune/chat/sub-character/session/{session_id}` | 세션 상태 조회 |
| DELETE | `/v1/fortune/chat/sub-character/session/{session_id}` | 세션 종료 |
| POST | `/v1/fortune/chat/sub-character/multi` | 멀티 캐릭터 대화 (3턴 일괄) |

### 4.2 POST /v1/fortune/chat/sub-character

#### 요청 스키마

```typescript
interface SubCharacterChatRequest {
  // 세션 정보
  session_id: string | null;          // 세션 ID (신규 시 null)

  // 캐릭터 정보
  character: SubCharacterCode;        // "CHEONGWOON" | "HWARIN" | "KYLE" | "ELARIA"

  // 메시지
  message: string;                    // 사용자 메시지

  // 사용자 정보 (첫 요청 시 필수)
  birth_date?: string;                // 생년월일 (YYYY-MM-DD)
  birth_time?: string;                // 출생시간 (HH:MM)

  // 옵션
  include_analysis?: boolean;         // 분석 결과 포함 여부 (기본: true)
  context_mode?: ContextMode;         // "full" | "summary" | "recent"
}

type SubCharacterCode = "CHEONGWOON" | "HWARIN" | "KYLE" | "ELARIA";
type ContextMode = "full" | "summary" | "recent";
```

#### 응답 스키마

```typescript
interface SubCharacterChatResponse {
  // 세션 정보
  session_id: string;                 // 세션 ID
  turn: number;                       // 현재 턴 번호

  // 캐릭터 응답
  character: SubCharacterCode;        // 응답 캐릭터
  character_name: string;             // 캐릭터 이름 (한글)
  response: string;                   // 캐릭터 응답 내용

  // 감정 및 말투
  emotion: EmotionCode;               // 감정 코드
  speech_style: string;               // 말투 스타일

  // 컨텍스트 정보
  context_summary: string;            // 컨텍스트 요약
  referenced_turns: number[];         // 참조한 이전 턴 번호

  // 분석 결과 (include_analysis=true인 경우)
  analysis?: AnalysisResult;          // 사주/점성술 분석 결과

  // 메타데이터
  tokens_used: number;                // 사용된 토큰 수
  timestamp: string;                  // ISO 8601 타임스탬프
}
```

#### 예시

**요청 (첫 턴 - 청운)**:
```json
{
  "session_id": null,
  "character": "CHEONGWOON",
  "message": "오늘 운세를 알려주세요",
  "birth_date": "1990-05-15",
  "birth_time": "14:30",
  "include_analysis": true,
  "context_mode": "full"
}
```

**응답**:
```json
{
  "session_id": "sub_abc12345",
  "turn": 1,
  "character": "CHEONGWOON",
  "character_name": "청운",
  "response": "허허, 젊은이여. 병화 일간을 타고났구려. 밝고 뜨거운 기운이 산을 덮은 안개처럼 흐르고 있소. 오늘은 특히 화기가 왕성하니, 열정을 불태우기 좋은 날이오.",
  "emotion": "THOUGHTFUL",
  "speech_style": "하오체 (시적)",
  "context_summary": "",
  "referenced_turns": [],
  "analysis": {
    "type": "eastern",
    "day_stem": "병화",
    "strength": "열정적이고 리더십이 강함"
  },
  "tokens_used": 256,
  "timestamp": "2026-01-31T10:30:00Z"
}
```

**요청 (2턴 - 카일)**:
```json
{
  "session_id": "sub_abc12345",
  "character": "KYLE",
  "message": "금전운은 어때요?",
  "context_mode": "summary"
}
```

**응답**:
```json
{
  "session_id": "sub_abc12345",
  "turn": 2,
  "character": "KYLE",
  "character_name": "카일",
  "response": "흠, 청운 선생이 화기가 왕성하다고 했지? 맞아, 그래서 금전운도 나쁘지 않아. 근데 말이야... 오늘 같은 날은 투자보다 저축이 낫다고 봐. 운이 좋아도 급하게 움직이면 손해 볼 수 있거든.",
  "emotion": "CONFIDENT",
  "speech_style": "반말+존댓말 혼용",
  "context_summary": "청운이 병화 일간으로 화기가 왕성하다고 분석함",
  "referenced_turns": [1],
  "analysis": {
    "type": "eastern",
    "day_stem": "병화",
    "wealth_luck": "상승 기조이나 신중함 필요"
  },
  "tokens_used": 312,
  "timestamp": "2026-01-31T10:30:30Z"
}
```

### 4.3 POST /v1/fortune/chat/sub-character/multi

3턴 대화를 일괄 처리하는 엔드포인트입니다.

#### 요청 스키마

```typescript
interface MultiCharacterRequest {
  // 사용자 정보
  birth_date: string;                 // 생년월일 (YYYY-MM-DD)
  birth_time?: string;                // 출생시간 (HH:MM)

  // 캐릭터 순서
  character_sequence: SubCharacterCode[];  // 3명 순서

  // 주제
  topic: FortuneTopic;                // 운세 주제

  // 초기 메시지
  initial_message: string;            // 첫 질문
}

type FortuneTopic = "total" | "love" | "wealth" | "career" | "health";
```

#### 응답 스키마

```typescript
interface MultiCharacterResponse {
  session_id: string;
  topic: FortuneTopic;

  // 3턴 대화 결과
  turns: SubCharacterTurn[];

  // 종합 요약
  consensus: string;                  // 캐릭터들의 합의점

  // 메타데이터
  total_tokens: number;
  duration_ms: number;
}

interface SubCharacterTurn {
  turn: number;
  character: SubCharacterCode;
  character_name: string;
  response: string;
  emotion: EmotionCode;
  referenced_context: string;         // 참조한 이전 컨텍스트
}
```

#### 예시

**요청**:
```json
{
  "birth_date": "1990-05-15",
  "birth_time": "14:30",
  "character_sequence": ["CHEONGWOON", "KYLE", "ELARIA"],
  "topic": "wealth",
  "initial_message": "금전운이 궁금합니다"
}
```

**응답**:
```json
{
  "session_id": "multi_xyz789",
  "topic": "wealth",
  "turns": [
    {
      "turn": 1,
      "character": "CHEONGWOON",
      "character_name": "청운",
      "response": "허허, 재물에 대해 묻는구려. 병화 일간은 본래 재물을 쓰는 성정이오. 그러나 올해는 토기가 살아있어 재물이 들어오기도 하오.",
      "emotion": "THOUGHTFUL",
      "referenced_context": ""
    },
    {
      "turn": 2,
      "character": "KYLE",
      "character_name": "카일",
      "response": "청운 선생 말이 맞아. 근데 말이야, 나라면 지금 투자보다 기회를 보겠어. 토기가 살아있다고 해도 급하게 움직이면 손해 볼 수 있거든.",
      "emotion": "CONFIDENT",
      "referenced_context": "청운: 토기가 살아있어 재물이 들어옴"
    },
    {
      "turn": 3,
      "character": "ELARIA",
      "character_name": "엘라리아",
      "response": "두 분의 조언이 모두 유익합니다. 정리해드리자면, 재물운이 상승 기조이나 신중하게 접근하시는 것이 좋겠습니다. 카일 님 말씀처럼 기회를 보시되, 청운 선생님 말씀대로 토기가 살아있으니 좋은 기회가 올 것입니다.",
      "emotion": "EMPATHETIC",
      "referenced_context": "청운: 재물운 상승, 카일: 기회 관망 추천"
    }
  ],
  "consensus": "재물운 상승 기조이나 신중한 접근 권장",
  "total_tokens": 1024,
  "duration_ms": 3500
}
```

### 4.4 GET /v1/fortune/chat/sub-character/session/{session_id}

#### 응답 스키마

```typescript
interface SessionStateResponse {
  session_id: string;
  created_at: string;
  updated_at: string;
  expires_at: string;                 // 만료 시간

  // 세션 상태
  current_turn: number;
  max_turns: number;                  // 최대 턴 (기본: 10)

  // 대화 히스토리
  history: ConversationTurn[];

  // 분석 결과 캐시
  analysis: {
    eastern?: EasternAnalysis;
    western?: WesternAnalysis;
  };
}

interface ConversationTurn {
  turn: number;
  character: SubCharacterCode;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
}
```

---

## 5. 데이터 모델

### 5.1 Session 모델

```python
"""서브 캐릭터 대화 세션 모델"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class SubCharacterSession(BaseModel):
    """서브 캐릭터 대화 세션"""

    # 세션 식별
    session_id: str = Field(..., description="세션 ID (sub_로 시작)")

    # 타임스탬프
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    expires_at: datetime = Field(..., description="만료 시간")

    # 턴 관리
    current_turn: int = Field(0, ge=0, description="현재 턴")
    max_turns: int = Field(10, ge=1, description="최대 턴")

    # 사용자 정보
    user_info: UserInfo = Field(..., description="사용자 정보")

    # 대화 히스토리
    history: list[ConversationTurn] = Field(
        default_factory=list,
        description="대화 히스토리"
    )

    # 분석 결과 캐시
    eastern_result: EasternFortuneResponse | None = None
    western_result: WesternFortuneDataV2 | None = None

    # 컨텍스트 요약 (토큰 절약용)
    context_summary: str = Field("", description="컨텍스트 요약")

    def add_turn(
        self,
        character: str,
        role: Literal["user", "assistant"],
        content: str,
    ) -> None:
        """대화 턴 추가"""
        self.current_turn += 1
        self.history.append(ConversationTurn(
            turn=self.current_turn,
            character=character,
            role=role,
            content=content,
            timestamp=datetime.now(),
        ))
        self.updated_at = datetime.now()

    def get_context(
        self,
        mode: Literal["full", "summary", "recent"] = "summary",
        max_turns: int = 5,
    ) -> str:
        """컨텍스트 조회

        Args:
            mode: 컨텍스트 모드
                - full: 전체 히스토리
                - summary: 요약 + 최근 N턴
                - recent: 최근 N턴만
            max_turns: 최근 턴 개수 (summary, recent 모드)

        Returns:
            컨텍스트 문자열
        """
        if mode == "full":
            return self._format_full_history()
        elif mode == "summary":
            return self._format_summary_context(max_turns)
        else:  # recent
            return self._format_recent_context(max_turns)

    def _format_full_history(self) -> str:
        """전체 히스토리 포맷"""
        lines = []
        for turn in self.history:
            prefix = f"[{turn.character}]" if turn.role == "assistant" else "[사용자]"
            lines.append(f"{prefix} {turn.content}")
        return "\n".join(lines)

    def _format_summary_context(self, max_turns: int) -> str:
        """요약 + 최근 턴 포맷"""
        parts = []
        if self.context_summary:
            parts.append(f"[요약] {self.context_summary}")

        recent = self.history[-max_turns:] if len(self.history) > max_turns else self.history
        for turn in recent:
            prefix = f"[{turn.character}]" if turn.role == "assistant" else "[사용자]"
            parts.append(f"{prefix} {turn.content}")

        return "\n".join(parts)

    def _format_recent_context(self, max_turns: int) -> str:
        """최근 턴만 포맷"""
        recent = self.history[-max_turns:] if len(self.history) > max_turns else self.history
        lines = []
        for turn in recent:
            prefix = f"[{turn.character}]" if turn.role == "assistant" else "[사용자]"
            lines.append(f"{prefix} {turn.content}")
        return "\n".join(lines)

    def update_summary(self, summary: str) -> None:
        """컨텍스트 요약 업데이트"""
        self.context_summary = summary
        self.updated_at = datetime.now()


class UserInfo(BaseModel):
    """사용자 정보"""

    birth_date: str = Field(..., description="생년월일 (YYYY-MM-DD)")
    birth_time: str | None = Field(None, description="출생시간 (HH:MM)")


class ConversationTurn(BaseModel):
    """대화 턴"""

    turn: int = Field(..., ge=1, description="턴 번호")
    character: str = Field(..., description="캐릭터 코드")
    role: Literal["user", "assistant"] = Field(..., description="역할")
    content: str = Field(..., description="대화 내용")
    timestamp: datetime = Field(default_factory=datetime.now)
```

### 5.2 ConversationHistory 모델

```python
"""대화 히스토리 모델"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ContextMode(str, Enum):
    """컨텍스트 모드"""

    FULL = "full"           # 전체 히스토리
    SUMMARY = "summary"     # 요약 + 최근
    RECENT = "recent"       # 최근 N턴만


class ConversationHistory(BaseModel):
    """대화 히스토리 관리자"""

    session_id: str
    turns: list[ConversationTurn] = Field(default_factory=list)

    # 토큰 관리
    max_context_tokens: int = Field(4000, description="최대 컨텍스트 토큰")
    current_tokens: int = Field(0, description="현재 사용 토큰")

    # 요약 상태
    summary: str = Field("", description="누적 요약")
    last_summarized_turn: int = Field(0, description="마지막 요약 턴")

    def add_message(
        self,
        character: str,
        role: str,
        content: str,
        tokens: int = 0,
    ) -> None:
        """메시지 추가

        토큰 제한 초과 시 자동으로 오래된 메시지 요약
        """
        turn = ConversationTurn(
            turn=len(self.turns) + 1,
            character=character,
            role=role,
            content=content,
            timestamp=datetime.now(),
        )
        self.turns.append(turn)
        self.current_tokens += tokens

        # 토큰 제한 확인
        if self.current_tokens > self.max_context_tokens * 0.8:
            self._compress_history()

    def _compress_history(self) -> None:
        """히스토리 압축 (요약)

        오래된 메시지를 요약하여 토큰 절약
        """
        if len(self.turns) <= 5:
            return

        # 요약할 턴 범위
        start = self.last_summarized_turn
        end = len(self.turns) - 3  # 최근 3턴은 유지

        if end <= start:
            return

        # 요약 대상 메시지
        to_summarize = self.turns[start:end]
        summary_text = self._generate_summary(to_summarize)

        # 요약 업데이트
        if self.summary:
            self.summary = f"{self.summary}\n{summary_text}"
        else:
            self.summary = summary_text

        self.last_summarized_turn = end

        # 토큰 재계산 (대략적)
        self.current_tokens = self._estimate_tokens()

    def _generate_summary(self, turns: list[ConversationTurn]) -> str:
        """턴들을 요약 (간단한 구현)

        실제 구현에서는 LLM을 사용하여 요약 가능
        """
        lines = []
        for turn in turns:
            # 핵심 내용만 추출 (간략화)
            short = turn.content[:100] + "..." if len(turn.content) > 100 else turn.content
            lines.append(f"{turn.character}: {short}")

        return " / ".join(lines)

    def _estimate_tokens(self) -> int:
        """토큰 수 추정

        한글 기준 대략 1.5자 = 1토큰
        """
        total_chars = len(self.summary)
        for turn in self.turns[self.last_summarized_turn:]:
            total_chars += len(turn.content)

        return int(total_chars / 1.5)

    def get_context_for_llm(
        self,
        mode: ContextMode = ContextMode.SUMMARY,
        max_recent: int = 5,
    ) -> str:
        """LLM용 컨텍스트 생성

        Args:
            mode: 컨텍스트 모드
            max_recent: 최근 턴 개수

        Returns:
            포맷된 컨텍스트 문자열
        """
        parts = []

        # 요약 포함 (summary 모드)
        if mode in (ContextMode.FULL, ContextMode.SUMMARY) and self.summary:
            parts.append(f"[이전 대화 요약]\n{self.summary}")

        # 최근 턴
        if mode == ContextMode.FULL:
            recent = self.turns
        else:
            recent = self.turns[-max_recent:] if len(self.turns) > max_recent else self.turns

        if recent:
            parts.append("[최근 대화]")
            for turn in recent:
                role_prefix = turn.character if turn.role == "assistant" else "사용자"
                parts.append(f"{role_prefix}: {turn.content}")

        return "\n".join(parts)
```

### 5.3 Redis 저장 구조

```json
{
  "sub_session:{session_id}": {
    "session_id": "sub_abc12345",
    "created_at": "2026-01-31T10:30:00Z",
    "updated_at": "2026-01-31T10:35:00Z",
    "expires_at": "2026-01-31T11:30:00Z",

    "user_info": {
      "birth_date": "1990-05-15",
      "birth_time": "14:30"
    },

    "turns": {
      "current": 3,
      "max": 10
    },

    "history": [
      {
        "turn": 1,
        "character": "CHEONGWOON",
        "role": "assistant",
        "content": "허허, 병화 일간이시구려...",
        "timestamp": "2026-01-31T10:30:10Z"
      },
      {
        "turn": 2,
        "character": "KYLE",
        "role": "assistant",
        "content": "청운 선생 말이 맞아...",
        "timestamp": "2026-01-31T10:31:00Z"
      }
    ],

    "context_summary": "청운: 병화 일간, 화기 왕성. 카일: 신중한 투자 권장",

    "analysis": {
      "eastern": { ... },
      "western": { ... }
    },

    "ttl": 3600
  }
}
```

---

## 6. 시퀀스 다이어그램

### 6.1 3턴 대화 흐름

```
┌────────┐       ┌────────────┐       ┌─────────────┐       ┌───────┐
│ Client │       │ API Server │       │ Session Mgr │       │ vLLM  │
└───┬────┘       └─────┬──────┘       └──────┬──────┘       └───┬───┘
    │                  │                     │                  │
    │ ─── 턴1: 청운 요청 (session_id=null) ──>│                  │
    │                  │                     │                  │
    │                  │── 새 세션 생성 ──────>│                  │
    │                  │<── session_id ───────│                  │
    │                  │                     │                  │
    │                  │── 사주 분석 요청 ─────────────────────────>│
    │                  │<── 분석 결과 ────────────────────────────│
    │                  │                     │                  │
    │                  │── 세션에 저장 ───────>│                  │
    │                  │                     │                  │
    │                  │── 청운 프롬프트 + 분석 결과 ────────────────>│
    │                  │<── 청운 응답 ───────────────────────────│
    │                  │                     │                  │
    │                  │── 턴 저장 ───────────>│                  │
    │<── 청운 응답 + session_id ───│                  │                  │
    │                  │                     │                  │
    ├──────────────────┼─────────────────────┼──────────────────┤
    │                  │                     │                  │
    │ ─── 턴2: 카일 요청 (session_id) ────────>│                  │
    │                  │                     │                  │
    │                  │── 세션 조회 ─────────>│                  │
    │                  │<── 세션 + 컨텍스트 ───│                  │
    │                  │                     │                  │
    │                  │── 카일 프롬프트 + 컨텍스트 ─────────────────>│
    │                  │<── 카일 응답 ───────────────────────────│
    │                  │                     │                  │
    │                  │── 턴 저장 ───────────>│                  │
    │<── 카일 응답 ────────────────│                  │                  │
    │                  │                     │                  │
    ├──────────────────┼─────────────────────┼──────────────────┤
    │                  │                     │                  │
    │ ─── 턴3: 엘라리아 요청 ────────────────────>│                  │
    │                  │                     │                  │
    │                  │── 세션 조회 ─────────>│                  │
    │                  │<── 세션 + 컨텍스트 ───│                  │
    │                  │                     │                  │
    │                  │── 엘라리아 프롬프트 + 전체 컨텍스트 ──────────>│
    │                  │<── 엘라리아 응답 (종합) ─────────────────│
    │                  │                     │                  │
    │                  │── 턴 저장 + 요약 생성 ─>│                  │
    │<── 엘라리아 응답 ────────────│                  │                  │
    │                  │                     │                  │
    └──────────────────┴─────────────────────┴──────────────────┘
```

### 6.2 컨텍스트 전달 상세

```
┌─────────────────────────────────────────────────────────────────┐
│                        턴 1: 청운                               │
├─────────────────────────────────────────────────────────────────┤
│ [System Prompt]                                                 │
│ 당신은 청운입니다. 소이설의 스승인 신선입니다.                        │
│ 말투: 하오체 (시적, 은유적)                                       │
│                                                                 │
│ [사주 분석 결과]                                                 │
│ 일간: 병화 (丙火)                                                │
│ 특성: 열정적, 리더십, 화기 왕성                                    │
│                                                                 │
│ [사용자]                                                        │
│ 오늘 운세를 알려주세요                                            │
│                                                                 │
│ [청운 응답]                                                     │
│ 허허, 젊은이여. 병화 일간을 타고났구려...                           │
└─────────────────────────────────────────────────────────────────┘

                              ↓ 컨텍스트 전달

┌─────────────────────────────────────────────────────────────────┐
│                        턴 2: 카일                               │
├─────────────────────────────────────────────────────────────────┤
│ [System Prompt]                                                 │
│ 당신은 카일입니다. 도박사/정보상입니다.                            │
│ 말투: 반말+존댓말 혼용                                           │
│                                                                 │
│ [사주 분석 결과]                                                 │
│ (턴 1과 동일)                                                   │
│                                                                 │
│ [이전 대화 컨텍스트]  ← 핵심!                                     │
│ 청운: 병화 일간, 화기 왕성하다고 분석함                            │
│                                                                 │
│ [사용자]                                                        │
│ 금전운은 어때요?                                                 │
│                                                                 │
│ [카일 응답]                                                     │
│ 청운 선생이 화기가 왕성하다고 했지? 맞아...                        │
└─────────────────────────────────────────────────────────────────┘

                              ↓ 컨텍스트 전달

┌─────────────────────────────────────────────────────────────────┐
│                        턴 3: 엘라리아                           │
├─────────────────────────────────────────────────────────────────┤
│ [System Prompt]                                                 │
│ 당신은 엘라리아입니다. 사파이어 왕국 공주입니다.                     │
│ 말투: 하십시오체/해요체                                          │
│                                                                 │
│ [사주 분석 결과]                                                 │
│ (턴 1과 동일)                                                   │
│                                                                 │
│ [이전 대화 컨텍스트]  ← 전체 맥락                                 │
│ [요약] 청운: 병화 일간, 화기 왕성                                 │
│ [카일] 금전운 신중하게, 투자보다 기회 관망 추천                     │
│                                                                 │
│ [사용자]                                                        │
│ 정리해주세요                                                    │
│                                                                 │
│ [엘라리아 응답]                                                  │
│ 두 분의 조언이 모두 유익합니다. 정리해드리자면...                   │
└─────────────────────────────────────────────────────────────────┘
```

### 6.3 프롬프트 구조

```python
"""서브 캐릭터 컨텍스트 프롬프트 빌더"""

def build_sub_character_prompt(
    character: str,
    user_message: str,
    analysis: dict,
    conversation_context: str,
    topic: str = "종합 운세",
) -> tuple[str, str]:
    """서브 캐릭터 프롬프트 생성

    Args:
        character: 캐릭터 코드
        user_message: 사용자 메시지
        analysis: 분석 결과 (사주/점성술)
        conversation_context: 이전 대화 컨텍스트
        topic: 운세 주제

    Returns:
        (system_prompt, user_prompt) 튜플
    """
    # 캐릭터 페르소나 프롬프트
    from yeji_ai.prompts.character_personas import get_system_prompt
    system_prompt = get_system_prompt(character)

    # 분석 결과 포맷
    analysis_text = _format_analysis(analysis)

    # 컨텍스트 섹션 (비어있지 않은 경우만)
    context_section = ""
    if conversation_context:
        context_section = f"""
## 이전 대화 컨텍스트
다른 캐릭터들의 이전 발언을 참고하여 자연스럽게 연결하세요.
{conversation_context}
"""

    # 사용자 프롬프트 구성
    user_prompt = f"""## 사주 분석 결과
{analysis_text}
{context_section}
## 주제
{topic}

## 사용자 질문
{user_message}

## 지시사항
1. 캐릭터의 말투와 성격을 유지하세요
2. 이전 캐릭터의 발언을 자연스럽게 언급하세요 (있는 경우)
3. 사주 분석 결과를 바탕으로 운세를 해석하세요
4. 200-300자 내외로 답변하세요
"""

    return system_prompt, user_prompt


def _format_analysis(analysis: dict) -> str:
    """분석 결과 포맷"""
    if analysis.get("type") == "eastern":
        return f"""일간: {analysis.get('day_stem', '알 수 없음')}
특성: {analysis.get('strength', '분석 중')}
오행: {analysis.get('five_elements', '확인 필요')}"""
    else:
        return f"""태양: {analysis.get('sun_sign', '알 수 없음')}
우세 원소: {analysis.get('element', '분석 중')}"""
```

---

## 7. 구현 고려사항

### 7.1 토큰 제한

| 항목 | 값 | 설명 |
|------|-----|------|
| 최대 컨텍스트 | 4,000 토큰 | vLLM 입력 제한 고려 |
| 시스템 프롬프트 | ~500 토큰 | 캐릭터 페르소나 |
| 분석 결과 | ~300 토큰 | 사주/점성술 요약 |
| 이전 컨텍스트 | ~1,500 토큰 | 대화 히스토리 |
| 사용자 메시지 | ~200 토큰 | 현재 질문 |
| 예비 | ~1,500 토큰 | 응답 생성용 |

**토큰 절약 전략:**

```python
class TokenOptimizer:
    """토큰 최적화 유틸리티"""

    MAX_CONTEXT_TOKENS = 1500

    @classmethod
    def compress_context(
        cls,
        history: list[ConversationTurn],
        target_tokens: int = 1000,
    ) -> str:
        """컨텍스트 압축

        1. 최근 3턴은 전체 유지
        2. 이전 턴은 핵심만 추출 (50자)
        3. 토큰 초과 시 오래된 순 제거
        """
        if not history:
            return ""

        # 최근 3턴
        recent = history[-3:] if len(history) > 3 else history
        older = history[:-3] if len(history) > 3 else []

        parts = []

        # 오래된 턴 요약
        for turn in older:
            short = turn.content[:50] + "..." if len(turn.content) > 50 else turn.content
            parts.append(f"[{turn.character}] {short}")

        # 최근 턴 전체
        for turn in recent:
            parts.append(f"[{turn.character}] {turn.content}")

        result = "\n".join(parts)

        # 토큰 초과 확인
        estimated_tokens = len(result) // 1.5  # 한글 기준
        if estimated_tokens > target_tokens:
            # 오래된 순 제거
            while estimated_tokens > target_tokens and len(parts) > 3:
                parts.pop(0)
                result = "\n".join(parts)
                estimated_tokens = len(result) // 1.5

        return result
```

### 7.2 세션 만료 처리

```python
"""세션 만료 관리"""

from datetime import datetime, timedelta

# 세션 TTL 설정
SESSION_TTL_SECONDS = 3600  # 1시간
SESSION_EXTENDED_TTL = 7200  # 2시간 (연장 시)


class SessionManager:
    """세션 관리자"""

    def __init__(self, redis_client):
        self.redis = redis_client

    async def create_session(
        self,
        user_info: dict,
        ttl: int = SESSION_TTL_SECONDS,
    ) -> SubCharacterSession:
        """새 세션 생성"""
        session_id = f"sub_{uuid.uuid4().hex[:8]}"
        now = datetime.now()

        session = SubCharacterSession(
            session_id=session_id,
            created_at=now,
            updated_at=now,
            expires_at=now + timedelta(seconds=ttl),
            user_info=UserInfo(**user_info),
        )

        await self.redis.setex(
            f"sub_session:{session_id}",
            ttl,
            session.model_dump_json(),
        )

        return session

    async def get_session(
        self,
        session_id: str,
    ) -> SubCharacterSession | None:
        """세션 조회"""
        data = await self.redis.get(f"sub_session:{session_id}")
        if not data:
            return None

        return SubCharacterSession.model_validate_json(data)

    async def update_session(
        self,
        session: SubCharacterSession,
        extend_ttl: bool = True,
    ) -> None:
        """세션 업데이트"""
        session.updated_at = datetime.now()

        if extend_ttl:
            # 활동 시 TTL 연장
            remaining = (session.expires_at - datetime.now()).total_seconds()
            new_ttl = max(int(remaining), SESSION_TTL_SECONDS)
            session.expires_at = datetime.now() + timedelta(seconds=new_ttl)

        ttl = int((session.expires_at - datetime.now()).total_seconds())

        await self.redis.setex(
            f"sub_session:{session.session_id}",
            ttl,
            session.model_dump_json(),
        )

    async def delete_session(self, session_id: str) -> bool:
        """세션 삭제"""
        result = await self.redis.delete(f"sub_session:{session_id}")
        return result > 0

    async def cleanup_expired_sessions(self) -> int:
        """만료된 세션 정리 (Redis TTL로 자동 처리되지만 명시적 정리용)"""
        # Redis TTL로 자동 만료되므로 별도 처리 불필요
        # 로깅/모니터링 목적으로 사용 가능
        pass
```

### 7.3 에러 처리

```python
"""서브 캐릭터 API 에러 처리"""

from fastapi import HTTPException, status


class SubCharacterAPIError:
    """API 에러 정의"""

    @staticmethod
    def session_not_found(session_id: str) -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "SESSION_NOT_FOUND",
                "message": f"세션을 찾을 수 없습니다: {session_id}",
                "recoverable": True,
                "action": "새 세션으로 시작하세요",
            },
        )

    @staticmethod
    def session_expired(session_id: str) -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_410_GONE,
            detail={
                "code": "SESSION_EXPIRED",
                "message": f"세션이 만료되었습니다: {session_id}",
                "recoverable": True,
                "action": "새 세션으로 시작하세요",
            },
        )

    @staticmethod
    def max_turns_exceeded(current: int, max_turns: int) -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "code": "MAX_TURNS_EXCEEDED",
                "message": f"최대 턴 수 초과: {current}/{max_turns}",
                "recoverable": False,
                "action": "새 세션을 시작하세요",
            },
        )

    @staticmethod
    def invalid_character(character: str) -> HTTPException:
        valid = ["CHEONGWOON", "HWARIN", "KYLE", "ELARIA"]
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_CHARACTER",
                "message": f"유효하지 않은 캐릭터: {character}",
                "valid_characters": valid,
                "recoverable": True,
            },
        )

    @staticmethod
    def llm_generation_failed(error: str) -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "LLM_GENERATION_FAILED",
                "message": "LLM 응답 생성 실패",
                "error": error,
                "recoverable": True,
                "action": "잠시 후 다시 시도하세요",
            },
        )
```

### 7.4 캐릭터 간 참조 규칙

```python
"""캐릭터 간 참조 규칙"""

# 캐릭터 관계 매트릭스
CHARACTER_RELATIONS = {
    "CHEONGWOON": {
        "can_reference": ["SOISEOL"],  # 제자 언급 가능
        "tone_when_referencing": "제자가 말했듯이",
        "default_emotion": "THOUGHTFUL",
    },
    "HWARIN": {
        "can_reference": ["CHEONGWOON", "KYLE"],
        "tone_when_referencing": "~가 말한 것처럼요",
        "default_emotion": "PLAYFUL",
    },
    "KYLE": {
        "can_reference": ["CHEONGWOON", "HWARIN"],
        "tone_when_referencing": "~가 그랬지?",
        "default_emotion": "CONFIDENT",
    },
    "ELARIA": {
        "can_reference": ["CHEONGWOON", "HWARIN", "KYLE"],  # 모두 참조 가능
        "tone_when_referencing": "~님 말씀처럼",
        "default_emotion": "EMPATHETIC",
    },
}


def generate_reference_phrase(
    current_char: str,
    referenced_char: str,
    content: str,
) -> str:
    """참조 문구 생성

    Args:
        current_char: 현재 발화 캐릭터
        referenced_char: 참조 대상 캐릭터
        content: 참조할 내용 핵심

    Returns:
        참조 문구
    """
    relations = CHARACTER_RELATIONS.get(current_char, {})
    tone = relations.get("tone_when_referencing", "앞서 말한 것처럼")

    char_names = {
        "CHEONGWOON": "청운 선생",
        "HWARIN": "화린",
        "KYLE": "카일",
        "ELARIA": "엘라리아 공주",
        "SOISEOL": "소이설",
        "STELLA": "스텔라",
    }

    ref_name = char_names.get(referenced_char, referenced_char)

    return f"{ref_name}{tone}"
```

---

## 8. 향후 확장

### 8.1 멀티 캐릭터 동시 대화

현재 설계는 순차적 캐릭터 전환을 지원하지만, 향후 동시 대화로 확장 가능합니다.

```typescript
// 향후 확장: 멀티 캐릭터 동시 대화
interface MultiCharacterSimultaneousRequest {
  session_id: string;
  characters: SubCharacterCode[];  // 동시 참여 캐릭터
  topic: string;
  mode: "debate" | "consensus" | "free";  // 대화 모드
}

interface MultiCharacterSimultaneousResponse {
  session_id: string;

  // 동시 대화 결과
  dialogue: DialogueTurn[];

  // 토론 결과 (debate 모드)
  debate_result?: {
    winner?: SubCharacterCode;
    consensus?: string;
  };
}

interface DialogueTurn {
  speaker: SubCharacterCode;
  target?: SubCharacterCode;  // 특정 캐릭터에게 말하는 경우
  content: string;
  emotion: EmotionCode;
  is_agreement: boolean;      // 동의 여부
}
```

### 8.2 캐릭터 조합 프리셋

```python
# 캐릭터 조합 프리셋
CHARACTER_PRESETS = {
    "wise_council": {
        "characters": ["CHEONGWOON", "ELARIA", "SOISEOL"],
        "description": "현자들의 조언",
        "topic_affinity": ["career", "life_decision"],
    },
    "fortune_gamble": {
        "characters": ["KYLE", "HWARIN", "STELLA"],
        "description": "투자/도박 조언",
        "topic_affinity": ["wealth", "investment"],
    },
    "love_advice": {
        "characters": ["SOISEOL", "ELARIA", "HWARIN"],
        "description": "연애 조언",
        "topic_affinity": ["love", "relationship"],
    },
}
```

### 8.3 캐릭터 감정 동기화

```python
# 캐릭터 간 감정 동기화 로직
class EmotionSynchronizer:
    """캐릭터 감정 동기화"""

    @staticmethod
    def sync_emotions(
        current_emotion: str,
        previous_emotions: list[str],
    ) -> str:
        """이전 캐릭터 감정에 따른 현재 감정 조정

        예: 이전 캐릭터가 CONCERNED였다면 다음 캐릭터는 EMPATHETIC 선호
        """
        emotion_transitions = {
            "CONCERNED": ["EMPATHETIC", "THOUGHTFUL"],
            "HAPPY": ["HAPPY", "PLAYFUL"],
            "THOUGHTFUL": ["THOUGHTFUL", "CURIOUS"],
            "CONFIDENT": ["CONFIDENT", "HAPPY"],
        }

        if previous_emotions:
            last_emotion = previous_emotions[-1]
            preferred = emotion_transitions.get(last_emotion, [])
            if preferred and current_emotion not in preferred:
                return preferred[0]

        return current_emotion
```

### 8.4 대화 템플릿

```python
# 3턴 대화 템플릿
CONVERSATION_TEMPLATES = {
    "analysis_consensus": {
        "description": "분석 → 보완 → 종합",
        "turn_1": {
            "role": "분석자",
            "instruction": "사주/점성술 기반 핵심 분석",
            "recommended_chars": ["CHEONGWOON", "SOISEOL"],
        },
        "turn_2": {
            "role": "보완자",
            "instruction": "다른 관점에서 보완",
            "recommended_chars": ["KYLE", "HWARIN"],
        },
        "turn_3": {
            "role": "종합자",
            "instruction": "두 의견 종합 및 조언",
            "recommended_chars": ["ELARIA", "STELLA"],
        },
    },
    "debate_resolution": {
        "description": "주장 → 반론 → 중재",
        "turn_1": {
            "role": "주장자",
            "instruction": "특정 관점 강하게 주장",
        },
        "turn_2": {
            "role": "반론자",
            "instruction": "다른 관점으로 반론",
        },
        "turn_3": {
            "role": "중재자",
            "instruction": "두 관점 조율 및 결론",
        },
    },
}
```

---

## 9. 참조 문서

### 9.1 내부 문서

| 문서 | 경로 | 설명 |
|------|------|------|
| 티키타카 스키마 V2 | `ai/docs/prd/tikitaka-schema-v2.md` | 버블/세션 스키마 |
| 캐릭터 페르소나 | `ai/src/yeji_ai/prompts/character_personas.py` | 캐릭터 프롬프트 |
| 티키타카 서비스 | `ai/src/yeji_ai/services/tikitaka_service.py` | 기존 서비스 |
| 채팅 API | `ai/src/yeji_ai/api/v1/fortune/chat.py` | 기존 API |

### 9.2 현재 구현 파일

| 파일 | 경로 | 설명 |
|------|------|------|
| 채팅 모델 | `ai/src/yeji_ai/models/fortune/chat.py` | 채팅 스키마 |
| 캐릭터 프롬프트 | `ai/src/yeji_ai/prompts/` | 6개 캐릭터 페르소나 |
| LLM 인터프리터 | `ai/src/yeji_ai/services/llm_interpreter.py` | LLM 호출 |

### 9.3 관련 기술

- [FastAPI Dependency Injection](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [Pydantic V2 Validation](https://docs.pydantic.dev/latest/)
- [Redis TTL](https://redis.io/commands/expire/)

---

## 변경 이력

| 버전 | 날짜 | 변경 내용 | 작성자 |
|------|------|----------|--------|
| 1.0.0 | 2026-01-31 | 초기 버전 | YEJI AI팀 |

---

## 부록

### A. Pydantic 모델 전체 정의

```python
"""서브 캐릭터 컨텍스트 API 모델

티키타카 3턴 대화에서 서브 캐릭터 간 컨텍스트 전달을 위한 스키마
"""

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


# ============================================================
# Enum 정의
# ============================================================

class SubCharacterCode(str, Enum):
    """서브 캐릭터 코드"""

    CHEONGWOON = "CHEONGWOON"  # 청운 (소이설 스승)
    HWARIN = "HWARIN"          # 화린 (청룡상단 지부장)
    KYLE = "KYLE"              # 카일 (도박사/정보상)
    ELARIA = "ELARIA"          # 엘라리아 (사파이어 공주)


class ContextMode(str, Enum):
    """컨텍스트 모드"""

    FULL = "full"         # 전체 히스토리
    SUMMARY = "summary"   # 요약 + 최근
    RECENT = "recent"     # 최근 N턴만


class EmotionCode(str, Enum):
    """감정 코드"""

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


class FortuneTopic(str, Enum):
    """운세 주제"""

    TOTAL = "total"
    LOVE = "love"
    WEALTH = "wealth"
    CAREER = "career"
    HEALTH = "health"


# ============================================================
# 요청 모델
# ============================================================

class SubCharacterChatRequest(BaseModel):
    """서브 캐릭터 대화 요청"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "session_id": None,
                "character": "CHEONGWOON",
                "message": "오늘 운세를 알려주세요",
                "birth_date": "1990-05-15",
                "birth_time": "14:30",
                "include_analysis": True,
                "context_mode": "summary",
            }
        }
    )

    # 세션
    session_id: str | None = Field(None, description="세션 ID (신규 시 null)")

    # 캐릭터
    character: SubCharacterCode = Field(..., description="서브 캐릭터 코드")

    # 메시지
    message: str = Field(..., min_length=1, max_length=500, description="사용자 메시지")

    # 사용자 정보 (첫 요청 시 필수)
    birth_date: str | None = Field(
        None,
        description="생년월일 (YYYY-MM-DD)",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
    )
    birth_time: str | None = Field(
        None,
        description="출생시간 (HH:MM)",
        pattern=r"^\d{2}:\d{2}$",
    )

    # 옵션
    include_analysis: bool = Field(True, description="분석 결과 포함 여부")
    context_mode: ContextMode = Field(
        ContextMode.SUMMARY,
        description="컨텍스트 모드",
    )


class MultiCharacterRequest(BaseModel):
    """멀티 캐릭터 대화 요청 (3턴 일괄)"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "birth_date": "1990-05-15",
                "birth_time": "14:30",
                "character_sequence": ["CHEONGWOON", "KYLE", "ELARIA"],
                "topic": "wealth",
                "initial_message": "금전운이 궁금합니다",
            }
        }
    )

    # 사용자 정보
    birth_date: str = Field(
        ...,
        description="생년월일 (YYYY-MM-DD)",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
    )
    birth_time: str | None = Field(
        None,
        description="출생시간 (HH:MM)",
        pattern=r"^\d{2}:\d{2}$",
    )

    # 캐릭터 순서 (3명)
    character_sequence: list[SubCharacterCode] = Field(
        ...,
        min_length=3,
        max_length=3,
        description="캐릭터 순서 (3명)",
    )

    # 주제
    topic: FortuneTopic = Field(FortuneTopic.TOTAL, description="운세 주제")

    # 초기 메시지
    initial_message: str = Field(..., min_length=1, description="첫 질문")


# ============================================================
# 응답 모델
# ============================================================

class AnalysisResult(BaseModel):
    """분석 결과"""

    type: Literal["eastern", "western"] = Field(..., description="분석 타입")
    day_stem: str | None = Field(None, description="일간 (동양)")
    sun_sign: str | None = Field(None, description="태양 별자리 (서양)")
    strength: str | None = Field(None, description="강점/특성")
    element: str | None = Field(None, description="우세 원소")


class SubCharacterChatResponse(BaseModel):
    """서브 캐릭터 대화 응답"""

    # 세션
    session_id: str = Field(..., description="세션 ID")
    turn: int = Field(..., ge=1, description="현재 턴 번호")

    # 캐릭터 응답
    character: SubCharacterCode = Field(..., description="응답 캐릭터")
    character_name: str = Field(..., description="캐릭터 이름 (한글)")
    response: str = Field(..., description="캐릭터 응답 내용")

    # 감정 및 말투
    emotion: EmotionCode = Field(..., description="감정 코드")
    speech_style: str = Field(..., description="말투 스타일")

    # 컨텍스트
    context_summary: str = Field("", description="컨텍스트 요약")
    referenced_turns: list[int] = Field(
        default_factory=list,
        description="참조한 이전 턴 번호",
    )

    # 분석 결과
    analysis: AnalysisResult | None = Field(None, description="분석 결과")

    # 메타데이터
    tokens_used: int = Field(..., ge=0, description="사용된 토큰 수")
    timestamp: datetime = Field(default_factory=datetime.now)


class SubCharacterTurn(BaseModel):
    """서브 캐릭터 턴 (멀티 대화용)"""

    turn: int = Field(..., ge=1, description="턴 번호")
    character: SubCharacterCode = Field(..., description="캐릭터")
    character_name: str = Field(..., description="캐릭터 이름")
    response: str = Field(..., description="응답 내용")
    emotion: EmotionCode = Field(..., description="감정")
    referenced_context: str = Field("", description="참조한 컨텍스트")


class MultiCharacterResponse(BaseModel):
    """멀티 캐릭터 대화 응답"""

    session_id: str = Field(..., description="세션 ID")
    topic: FortuneTopic = Field(..., description="운세 주제")

    # 3턴 대화 결과
    turns: list[SubCharacterTurn] = Field(..., min_length=3, max_length=3)

    # 종합 요약
    consensus: str = Field(..., description="캐릭터들의 합의점")

    # 메타데이터
    total_tokens: int = Field(..., ge=0, description="총 토큰 수")
    duration_ms: int = Field(..., ge=0, description="처리 시간 (ms)")


class ConversationTurn(BaseModel):
    """대화 턴"""

    turn: int = Field(..., ge=1, description="턴 번호")
    character: str = Field(..., description="캐릭터 코드")
    role: Literal["user", "assistant"] = Field(..., description="역할")
    content: str = Field(..., description="대화 내용")
    timestamp: datetime = Field(default_factory=datetime.now)


class SessionStateResponse(BaseModel):
    """세션 상태 응답"""

    session_id: str = Field(..., description="세션 ID")
    created_at: datetime = Field(..., description="생성 시간")
    updated_at: datetime = Field(..., description="수정 시간")
    expires_at: datetime = Field(..., description="만료 시간")

    # 턴 상태
    current_turn: int = Field(..., ge=0, description="현재 턴")
    max_turns: int = Field(10, ge=1, description="최대 턴")

    # 대화 히스토리
    history: list[ConversationTurn] = Field(
        default_factory=list,
        description="대화 히스토리",
    )

    # 분석 결과
    has_eastern_result: bool = Field(False, description="동양 분석 완료")
    has_western_result: bool = Field(False, description="서양 분석 완료")
```

---

> **Note**: 이 PRD는 티키타카 3턴 대화에서 서브 캐릭터 간 컨텍스트 전달을 위한 API 설계를 정의합니다.
> 기존 `/chat/test-character` API를 확장하여 세션 기반 컨텍스트 관리를 지원합니다.
