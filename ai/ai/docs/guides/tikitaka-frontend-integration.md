# 티키타카 프론트엔드 연동 가이드

> **문서 버전**: 1.0.0
> **작성일**: 2026-01-30
> **담당팀**: SSAFY YEJI AI팀
> **대상**: 프론트엔드 개발자

---

## 목차

1. [개요](#1-개요)
2. [API 엔드포인트 명세](#2-api-엔드포인트-명세)
3. [SSE 스트리밍 연동](#3-sse-스트리밍-연동)
4. [React 컴포넌트 가이드](#4-react-컴포넌트-가이드)
5. [상태 관리](#5-상태-관리)
6. [에러 핸들링](#6-에러-핸들링)
7. [스타일링 가이드](#7-스타일링-가이드)
8. [참조 문서](#8-참조-문서)

---

## 1. 개요

### 1.1 티키타카란?

티키타카는 소이설(동양 사주)과 스텔라(서양 점성술) 두 캐릭터가 대화하며 사용자의 운세를 분석하는 대화형 서비스입니다.

### 1.2 핵심 개념

| 용어 | 설명 |
|------|------|
| **Bubble** | 캐릭터의 발화 단위 (메시지 말풍선) |
| **Session** | 대화 세션 (생성 ~ 종료까지) |
| **Turn** | 대화 턴 (사용자 입력 1회 = 1턴) |
| **Phase** | 대화 단계 (GREETING, DIALOGUE, QUESTION, SUMMARY, FAREWELL) |

### 1.3 캐릭터 정보

| 캐릭터 | 코드 | 전문분야 | 성격 | 말투 |
|--------|------|----------|------|------|
| 소이설 | `SOISEOL` | 동양 사주 | 따뜻한 온미녀 | "~에요", "~해요" |
| 스텔라 | `STELLA` | 서양 점성술 | 쿨한 냉미녀 | "~해", "~야" |
| 시스템 | `SYSTEM` | - | 안내/알림 | 중립적 |

---

## 2. API 엔드포인트 명세

### 2.1 엔드포인트 목록

| 메서드 | 경로 | 설명 |
|--------|------|------|
| `POST` | `/api/v1/fortune/chat` | 일반 대화 요청 |
| `POST` | `/api/v1/fortune/chat/stream` | SSE 스트리밍 대화 |
| `GET` | `/api/v1/fortune/chat/characters` | 캐릭터 정보 조회 |
| `GET` | `/api/v2/fortune/tikitaka/session/{session_id}` | 세션 상태 조회 (V2) |
| `GET` | `/api/v2/fortune/tikitaka/summary/{session_id}` | 요약 조회 (V2) |

### 2.2 세션 생성 및 대화 요청

#### 요청 스키마

```typescript
interface ChatRequest {
  session_id?: string | null;  // 기존 세션 ID (첫 요청 시 null)
  message?: string;            // 사용자 메시지
  birth_date?: string;         // 생년월일 (YYYY-MM-DD, 첫 요청 시 필수)
  birth_time?: string;         // 출생시간 (HH:MM, 선택)
  birth_place?: string;        // 출생지 (선택)
  choice?: number;             // 선택 응답 (1 또는 2)
}
```

#### 응답 스키마

```typescript
interface ChatResponse {
  session_id: string;
  turn: number;
  messages: ChatMessage[];
  debate_status: ChatDebateStatus;
  ui_hints: ChatUIHints;
}

interface ChatMessage {
  character: "SOISEOL" | "STELLA" | "SYSTEM";
  type: MessageType;
  content: string;
  timestamp: string;  // ISO 8601
}

type MessageType =
  | "GREETING"         // 인사
  | "INFO_REQUEST"     // 정보 요청
  | "INTERPRETATION"   // 해석
  | "DEBATE"           // 토론
  | "CONSENSUS"        // 합의
  | "QUESTION"         // 질문
  | "CHOICE"           // 선택 요청
  | "SUMMARY"          // 요약
  | "FAREWELL";        // 마무리

interface ChatDebateStatus {
  is_consensus: boolean;
  eastern_opinion?: string;
  western_opinion?: string;
  consensus_point?: string;
  question?: string;
}

interface ChatUIHints {
  show_choice: boolean;
  choices?: ChoiceOption[];
  input_placeholder?: string;
  show_typing_indicator?: boolean;
}

interface ChoiceOption {
  value: number;       // 1 또는 2
  character: string;   // "SOISEOL" 또는 "STELLA"
  label: string;       // 버튼 라벨
  description?: string;
}
```

#### curl 예시

```bash
# 첫 요청 (세션 생성 + 생년월일 입력)
curl -X POST "https://api.yeji.ai/api/v1/fortune/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": null,
    "birth_date": "1990-05-15",
    "birth_time": "14:30",
    "message": "오늘 운세 알려주세요"
  }'

# 후속 요청 (세션 ID 사용)
curl -X POST "https://api.yeji.ai/api/v1/fortune/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "abc12345",
    "message": "연애운이 궁금해요"
  }'

# 선택 응답
curl -X POST "https://api.yeji.ai/api/v1/fortune/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "abc12345",
    "choice": 1
  }'
```

#### TypeScript 예시

```typescript
// API 클라이언트
const API_BASE_URL = "https://api.yeji.ai";

interface TikitakaClient {
  startSession(birthDate: string, birthTime?: string): Promise<ChatResponse>;
  sendMessage(sessionId: string, message: string): Promise<ChatResponse>;
  sendChoice(sessionId: string, choice: number): Promise<ChatResponse>;
}

const tikitakaClient: TikitakaClient = {
  async startSession(birthDate: string, birthTime?: string): Promise<ChatResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/fortune/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: null,
        birth_date: birthDate,
        birth_time: birthTime,
        message: "운세를 알려주세요",
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${await response.text()}`);
    }

    return response.json();
  },

  async sendMessage(sessionId: string, message: string): Promise<ChatResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/fortune/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: sessionId,
        message,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${await response.text()}`);
    }

    return response.json();
  },

  async sendChoice(sessionId: string, choice: number): Promise<ChatResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/fortune/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: sessionId,
        choice,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${await response.text()}`);
    }

    return response.json();
  },
};
```

### 2.3 세션 상태 조회 (V2)

```bash
curl -X GET "https://api.yeji.ai/api/v2/fortune/tikitaka/session/abc12345"
```

응답 예시:

```json
{
  "session_id": "abc12345",
  "current_turn": 5,
  "max_turns": 10,
  "bonus_turns": 0,
  "remaining_turns": 5,
  "is_premium": false,
  "phase": "DIALOGUE",
  "has_eastern_result": true,
  "has_western_result": true
}
```

---

## 3. SSE 스트리밍 연동

### 3.1 SSE 이벤트 타입

| 이벤트 | 설명 | 데이터 |
|--------|------|--------|
| `session` | 세션 정보 | `{session_id, is_premium}` |
| `phase_change` | 단계 변경 | `{from_phase, to_phase, reason}` |
| `bubble_start` | 버블 시작 | `{bubble_id, character, emotion, type, phase}` |
| `bubble_chunk` | 버블 청크 | `{bubble_id, content}` |
| `bubble_end` | 버블 완료 | `{bubble_id, content, timestamp}` |
| `turn_update` | 턴 업데이트 | `{current_turn, remaining_turns}` |
| `warning_low_turns` | 턴 부족 경고 | `{remaining_turns, message}` |
| `debate_status` | 토론 상태 | `{is_consensus, question}` |
| `ui_hint` | UI 힌트 | `{show_choice, choices}` |
| `pause` | 사용자 입력 대기 | `{waiting_for, placeholder}` |
| `complete` | 완료 | `{status}` |
| `error` | 에러 | `{code, message, recoverable}` |

### 3.2 EventSource 기본 사용법

```typescript
function connectTikitakaStream(
  sessionId: string | null,
  birthDate: string,
  birthTime?: string,
  onBubble: (bubble: Partial<Bubble>) => void,
  onComplete: () => void,
  onError: (error: Error) => void,
): () => void {
  // POST 요청으로 SSE 스트림 시작
  const controller = new AbortController();

  fetch(`${API_BASE_URL}/api/v1/fortune/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: sessionId,
      birth_date: birthDate,
      birth_time: birthTime,
    }),
    signal: controller.signal,
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      function read() {
        reader?.read().then(({ done, value }) => {
          if (done) {
            onComplete();
            return;
          }

          const text = decoder.decode(value, { stream: true });
          const events = parseSSEEvents(text);

          for (const event of events) {
            handleSSEEvent(event, onBubble);
          }

          read();
        });
      }

      read();
    })
    .catch(onError);

  // 연결 해제 함수 반환
  return () => controller.abort();
}

// SSE 이벤트 파싱
function parseSSEEvents(text: string): SSEEvent[] {
  const events: SSEEvent[] = [];
  const lines = text.split("\n");

  for (const line of lines) {
    if (line.startsWith("data: ")) {
      try {
        const data = JSON.parse(line.slice(6));
        events.push(data);
      } catch {
        // JSON 파싱 실패 무시
      }
    }
  }

  return events;
}

interface SSEEvent {
  event: string;
  data?: Record<string, unknown>;
  [key: string]: unknown;
}
```

### 3.3 이벤트 타입별 처리

```typescript
// 버블 상태 관리
const bubblesMap = new Map<string, Partial<Bubble>>();

function handleSSEEvent(
  event: SSEEvent,
  onBubbleUpdate: (bubbles: Bubble[]) => void,
): void {
  const eventType = event.event;
  const data = event.data || event;

  switch (eventType) {
    case "session":
      // 세션 ID 저장
      console.log("Session started:", data.session_id);
      break;

    case "phase_change":
      // 단계 변경 UI 업데이트
      console.log(`Phase: ${data.from_phase} -> ${data.to_phase}`);
      break;

    case "bubble_start":
    case "message_start":
      // 새 버블 시작
      bubblesMap.set(data.bubble_id || data.character, {
        bubble_id: data.bubble_id || `temp_${Date.now()}`,
        character: data.character,
        emotion: data.emotion || "NEUTRAL",
        type: data.type,
        phase: data.phase || "DIALOGUE",
        content: "",
        reply_to: data.reply_to || null,
      });
      onBubbleUpdate(Array.from(bubblesMap.values()) as Bubble[]);
      break;

    case "bubble_chunk":
    case "message_chunk":
      // 버블 내용 추가 (스트리밍)
      const bubbleId = data.bubble_id || data.character;
      const bubble = bubblesMap.get(bubbleId);
      if (bubble) {
        bubble.content = (bubble.content || "") + data.content;
        onBubbleUpdate(Array.from(bubblesMap.values()) as Bubble[]);
      }
      break;

    case "bubble_end":
    case "message_end":
      // 버블 완료
      const endBubbleId = data.bubble_id || data.character;
      const endBubble = bubblesMap.get(endBubbleId);
      if (endBubble) {
        endBubble.content = data.content;
        endBubble.timestamp = data.timestamp;
        onBubbleUpdate(Array.from(bubblesMap.values()) as Bubble[]);
      }
      break;

    case "turn_update":
      // 턴 업데이트 UI 반영
      console.log(`Turn: ${data.current_turn}, Remaining: ${data.remaining_turns}`);
      break;

    case "warning_low_turns":
      // 턴 부족 경고 표시
      console.warn(data.message);
      break;

    case "debate_status":
      // 토론 상태 UI 업데이트
      console.log("Debate status:", data);
      break;

    case "pause":
      // 사용자 입력 대기
      console.log(`Waiting for: ${data.waiting_for}`);
      break;

    case "complete":
      // 스트리밍 완료
      console.log("Stream complete");
      break;

    case "error":
      // 에러 처리
      console.error(`Error: ${data.message}`);
      break;
  }
}
```

### 3.4 에러 핸들링 및 재연결

```typescript
class TikitakaSSEClient {
  private eventSource: EventSource | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 3;
  private reconnectDelay = 1000; // ms

  connect(
    sessionId: string,
    onBubble: (bubble: Bubble) => void,
    onError: (error: Error) => void,
  ): void {
    this.disconnect();

    const url = `${API_BASE_URL}/api/v1/fortune/chat/stream?session_id=${sessionId}`;

    try {
      this.eventSource = new EventSource(url);

      this.eventSource.onopen = () => {
        console.log("SSE connected");
        this.reconnectAttempts = 0;
      };

      this.eventSource.onerror = (event) => {
        console.error("SSE error:", event);

        if (this.eventSource?.readyState === EventSource.CLOSED) {
          this.handleReconnect(sessionId, onBubble, onError);
        }
      };

      // 이벤트 리스너 등록
      this.eventSource.addEventListener("bubble_start", (e) => {
        const data = JSON.parse(e.data);
        // 처리 로직
      });

      this.eventSource.addEventListener("bubble_chunk", (e) => {
        const data = JSON.parse(e.data);
        // 처리 로직
      });

      this.eventSource.addEventListener("bubble_end", (e) => {
        const data = JSON.parse(e.data);
        // 처리 로직
      });

      this.eventSource.addEventListener("complete", () => {
        this.disconnect();
      });

      this.eventSource.addEventListener("error", (e) => {
        const data = JSON.parse((e as MessageEvent).data);
        onError(new Error(data.message));
      });

    } catch (error) {
      onError(error as Error);
    }
  }

  private handleReconnect(
    sessionId: string,
    onBubble: (bubble: Bubble) => void,
    onError: (error: Error) => void,
  ): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      onError(new Error("최대 재연결 시도 횟수를 초과했습니다."));
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * this.reconnectAttempts;

    console.log(`재연결 시도 ${this.reconnectAttempts}/${this.maxReconnectAttempts} (${delay}ms 후)`);

    setTimeout(() => {
      this.connect(sessionId, onBubble, onError);
    }, delay);
  }

  disconnect(): void {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
  }
}
```

---

## 4. React 컴포넌트 가이드

### 4.1 기본 구조

```
TikitakaPage/
├── TikitakaContainer.tsx      # 메인 컨테이너
├── components/
│   ├── BubbleList.tsx         # 버블 목록
│   ├── BubbleItem.tsx         # 개별 버블
│   ├── CharacterAvatar.tsx    # 캐릭터 아바타
│   ├── InputArea.tsx          # 입력 영역
│   ├── ChoiceButtons.tsx      # 선택 버튼
│   ├── TurnIndicator.tsx      # 턴 표시기
│   └── TypingIndicator.tsx    # 타이핑 표시기
├── hooks/
│   ├── useTikitakaSession.ts  # 세션 관리 훅
│   ├── useTikitakaSSE.ts      # SSE 연결 훅
│   └── useBubbles.ts          # 버블 상태 훅
└── types/
    └── tikitaka.ts            # 타입 정의
```

### 4.2 버블 렌더링 컴포넌트

```tsx
// components/BubbleItem.tsx
import React from "react";
import { Bubble, CharacterCode, EmotionCode } from "../types/tikitaka";
import CharacterAvatar from "./CharacterAvatar";
import styles from "./BubbleItem.module.css";

interface BubbleItemProps {
  bubble: Bubble;
  isStreaming?: boolean;
}

export default function BubbleItem({ bubble, isStreaming = false }: BubbleItemProps) {
  const isEastern = bubble.character === "SOISEOL";
  const isSystem = bubble.character === "SYSTEM";

  // 캐릭터별 정렬
  const alignment = isSystem ? "center" : isEastern ? "left" : "right";

  // 감정별 스타일
  const emotionClass = getEmotionClass(bubble.emotion);

  return (
    <div
      className={`${styles.bubbleContainer} ${styles[alignment]}`}
      data-character={bubble.character}
      data-emotion={bubble.emotion}
    >
      {/* 아바타 (시스템 제외) */}
      {!isSystem && (
        <CharacterAvatar
          character={bubble.character}
          emotion={bubble.emotion}
        />
      )}

      {/* 버블 내용 */}
      <div className={`${styles.bubble} ${styles[emotionClass]}`}>
        {/* 응답 표시 */}
        {bubble.reply_to && (
          <div className={styles.replyIndicator}>
            <span>답장</span>
          </div>
        )}

        {/* 메시지 내용 */}
        <div className={styles.content}>
          {bubble.content}
          {isStreaming && <span className={styles.cursor}>|</span>}
        </div>

        {/* 타임스탬프 */}
        {bubble.timestamp && (
          <div className={styles.timestamp}>
            {formatTime(bubble.timestamp)}
          </div>
        )}
      </div>
    </div>
  );
}

// 감정별 CSS 클래스 매핑
function getEmotionClass(emotion: EmotionCode): string {
  const emotionMap: Record<EmotionCode, string> = {
    NEUTRAL: "neutral",
    HAPPY: "happy",
    CURIOUS: "curious",
    THOUGHTFUL: "thoughtful",
    SURPRISED: "surprised",
    CONCERNED: "concerned",
    CONFIDENT: "confident",
    PLAYFUL: "playful",
    MYSTERIOUS: "mysterious",
    EMPATHETIC: "empathetic",
  };
  return emotionMap[emotion] || "neutral";
}

// 시간 포맷팅
function formatTime(timestamp: string): string {
  const date = new Date(timestamp);
  return date.toLocaleTimeString("ko-KR", {
    hour: "2-digit",
    minute: "2-digit",
  });
}
```

### 4.3 캐릭터 아바타 컴포넌트

```tsx
// components/CharacterAvatar.tsx
import React from "react";
import { CharacterCode, EmotionCode } from "../types/tikitaka";
import styles from "./CharacterAvatar.module.css";

interface CharacterAvatarProps {
  character: CharacterCode;
  emotion: EmotionCode;
  size?: "small" | "medium" | "large";
}

// 캐릭터 정보
const CHARACTER_INFO = {
  SOISEOL: {
    name: "소이설",
    color: "#FF6B8A",  // 따뜻한 분홍
    bgColor: "#FFF0F3",
    emoji: "🌸",
  },
  STELLA: {
    name: "스텔라",
    color: "#6B8BFF",  // 차가운 파랑
    bgColor: "#F0F4FF",
    emoji: "🌟",
  },
  SYSTEM: {
    name: "시스템",
    color: "#888888",
    bgColor: "#F5F5F5",
    emoji: "🔔",
  },
};

// 감정별 이미지 경로 (예시)
const EMOTION_IMAGES: Record<CharacterCode, Partial<Record<EmotionCode, string>>> = {
  SOISEOL: {
    NEUTRAL: "/avatars/soiseol/neutral.png",
    HAPPY: "/avatars/soiseol/happy.png",
    CURIOUS: "/avatars/soiseol/curious.png",
    THOUGHTFUL: "/avatars/soiseol/thoughtful.png",
    EMPATHETIC: "/avatars/soiseol/empathetic.png",
    // ... 기타 감정
  },
  STELLA: {
    NEUTRAL: "/avatars/stella/neutral.png",
    CONFIDENT: "/avatars/stella/confident.png",
    THOUGHTFUL: "/avatars/stella/thoughtful.png",
    MYSTERIOUS: "/avatars/stella/mysterious.png",
    // ... 기타 감정
  },
  SYSTEM: {},
};

export default function CharacterAvatar({
  character,
  emotion,
  size = "medium",
}: CharacterAvatarProps) {
  const info = CHARACTER_INFO[character];
  const imagePath = EMOTION_IMAGES[character]?.[emotion];

  const sizeMap = {
    small: 32,
    medium: 48,
    large: 64,
  };

  const pixelSize = sizeMap[size];

  return (
    <div
      className={`${styles.avatar} ${styles[size]}`}
      style={{
        backgroundColor: info.bgColor,
        borderColor: info.color,
        width: pixelSize,
        height: pixelSize,
      }}
      title={`${info.name} - ${emotion}`}
    >
      {imagePath ? (
        <img
          src={imagePath}
          alt={`${info.name} ${emotion}`}
          className={styles.avatarImage}
        />
      ) : (
        <span className={styles.emoji}>{info.emoji}</span>
      )}
    </div>
  );
}
```

### 4.4 타이핑 효과 구현

```tsx
// components/TypingBubble.tsx
import React, { useState, useEffect, useRef } from "react";
import styles from "./TypingBubble.module.css";

interface TypingBubbleProps {
  content: string;
  typingSpeed?: number;  // ms per character
  onComplete?: () => void;
}

export default function TypingBubble({
  content,
  typingSpeed = 30,
  onComplete,
}: TypingBubbleProps) {
  const [displayedContent, setDisplayedContent] = useState("");
  const [isComplete, setIsComplete] = useState(false);
  const indexRef = useRef(0);

  useEffect(() => {
    // 새 content가 들어오면 초기화
    if (content.length > indexRef.current) {
      // 스트리밍으로 새 문자가 추가된 경우
      // 점진적으로 표시
    }
  }, [content]);

  useEffect(() => {
    if (indexRef.current >= content.length) {
      setIsComplete(true);
      onComplete?.();
      return;
    }

    const timer = setTimeout(() => {
      setDisplayedContent(content.slice(0, indexRef.current + 1));
      indexRef.current++;
    }, typingSpeed);

    return () => clearTimeout(timer);
  }, [displayedContent, content, typingSpeed, onComplete]);

  return (
    <span className={styles.typingContent}>
      {displayedContent}
      {!isComplete && <span className={styles.cursor}>|</span>}
    </span>
  );
}

// CSS (TypingBubble.module.css)
/*
.typingContent {
  white-space: pre-wrap;
}

.cursor {
  animation: blink 0.7s infinite;
  color: currentColor;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}
*/
```

### 4.5 버블 목록 컴포넌트

```tsx
// components/BubbleList.tsx
import React, { useRef, useEffect } from "react";
import { Bubble } from "../types/tikitaka";
import BubbleItem from "./BubbleItem";
import TypingIndicator from "./TypingIndicator";
import styles from "./BubbleList.module.css";

interface BubbleListProps {
  bubbles: Bubble[];
  streamingBubbleId?: string;
  isTyping?: boolean;
  typingCharacter?: string;
}

export default function BubbleList({
  bubbles,
  streamingBubbleId,
  isTyping,
  typingCharacter,
}: BubbleListProps) {
  const listRef = useRef<HTMLDivElement>(null);

  // 새 버블 추가 시 스크롤
  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTo({
        top: listRef.current.scrollHeight,
        behavior: "smooth",
      });
    }
  }, [bubbles.length]);

  return (
    <div ref={listRef} className={styles.bubbleList}>
      {bubbles.map((bubble) => (
        <BubbleItem
          key={bubble.bubble_id}
          bubble={bubble}
          isStreaming={bubble.bubble_id === streamingBubbleId}
        />
      ))}

      {/* 타이핑 표시기 */}
      {isTyping && typingCharacter && (
        <TypingIndicator character={typingCharacter} />
      )}
    </div>
  );
}
```

### 4.6 입력 영역 컴포넌트

```tsx
// components/InputArea.tsx
import React, { useState, KeyboardEvent } from "react";
import { ChatUIHints, ChoiceOption } from "../types/tikitaka";
import ChoiceButtons from "./ChoiceButtons";
import styles from "./InputArea.module.css";

interface InputAreaProps {
  onSendMessage: (message: string) => void;
  onSelectChoice: (choice: number) => void;
  uiHints: ChatUIHints;
  disabled?: boolean;
  placeholder?: string;
}

export default function InputArea({
  onSendMessage,
  onSelectChoice,
  uiHints,
  disabled = false,
  placeholder = "메시지를 입력하세요...",
}: InputAreaProps) {
  const [message, setMessage] = useState("");

  const handleSubmit = () => {
    if (message.trim() && !disabled) {
      onSendMessage(message.trim());
      setMessage("");
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  // 선택형 UI
  if (uiHints.show_choice && uiHints.choices) {
    return (
      <ChoiceButtons
        choices={uiHints.choices}
        onSelect={onSelectChoice}
        disabled={disabled}
      />
    );
  }

  return (
    <div className={styles.inputArea}>
      <input
        type="text"
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={uiHints.input_placeholder || placeholder}
        disabled={disabled}
        className={styles.input}
      />
      <button
        onClick={handleSubmit}
        disabled={disabled || !message.trim()}
        className={styles.sendButton}
      >
        전송
      </button>
    </div>
  );
}
```

### 4.7 선택 버튼 컴포넌트

```tsx
// components/ChoiceButtons.tsx
import React from "react";
import { ChoiceOption, CharacterCode } from "../types/tikitaka";
import styles from "./ChoiceButtons.module.css";

interface ChoiceButtonsProps {
  choices: ChoiceOption[];
  onSelect: (value: number) => void;
  disabled?: boolean;
}

const CHARACTER_COLORS: Record<CharacterCode, string> = {
  SOISEOL: "#FF6B8A",
  STELLA: "#6B8BFF",
  SYSTEM: "#888888",
};

export default function ChoiceButtons({
  choices,
  onSelect,
  disabled = false,
}: ChoiceButtonsProps) {
  return (
    <div className={styles.choiceContainer}>
      <p className={styles.question}>어느 해석이 더 와닿으시나요?</p>
      <div className={styles.buttons}>
        {choices.map((choice) => (
          <button
            key={choice.value}
            onClick={() => onSelect(choice.value)}
            disabled={disabled}
            className={styles.choiceButton}
            style={{
              borderColor: CHARACTER_COLORS[choice.character as CharacterCode],
              "--hover-bg": CHARACTER_COLORS[choice.character as CharacterCode],
            } as React.CSSProperties}
          >
            <span className={styles.label}>{choice.label}</span>
            {choice.description && (
              <span className={styles.description}>{choice.description}</span>
            )}
          </button>
        ))}
      </div>
    </div>
  );
}
```

### 4.8 턴 표시기 컴포넌트

```tsx
// components/TurnIndicator.tsx
import React from "react";
import styles from "./TurnIndicator.module.css";

interface TurnIndicatorProps {
  currentTurn: number;
  maxTurns: number;
  bonusTurns: number;
  isPremium: boolean;
}

export default function TurnIndicator({
  currentTurn,
  maxTurns,
  bonusTurns,
  isPremium,
}: TurnIndicatorProps) {
  const totalTurns = maxTurns + bonusTurns;
  const remainingTurns = totalTurns - currentTurn;
  const isLow = remainingTurns <= 3;

  return (
    <div className={`${styles.turnIndicator} ${isLow ? styles.low : ""}`}>
      <div className={styles.turnInfo}>
        <span className={styles.current}>{currentTurn}</span>
        <span className={styles.separator}>/</span>
        <span className={styles.total}>{totalTurns}</span>
      </div>

      {/* 프로그레스 바 */}
      <div className={styles.progressBar}>
        <div
          className={styles.progress}
          style={{ width: `${(currentTurn / totalTurns) * 100}%` }}
        />
        {/* 보너스 턴 영역 표시 */}
        {bonusTurns > 0 && (
          <div
            className={styles.bonusZone}
            style={{
              left: `${(maxTurns / totalTurns) * 100}%`,
              width: `${(bonusTurns / totalTurns) * 100}%`,
            }}
          />
        )}
      </div>

      {/* 남은 턴 */}
      <div className={styles.remaining}>
        {isLow ? (
          <span className={styles.warning}>
            대화가 곧 마무리됩니다 ({remainingTurns}턴 남음)
          </span>
        ) : (
          <span>남은 대화: {remainingTurns}턴</span>
        )}
      </div>

      {/* 프리미엄 배지 */}
      {isPremium && <span className={styles.premiumBadge}>Premium</span>}
    </div>
  );
}
```

---

## 5. 상태 관리

### 5.1 세션 상태 관리 훅

```tsx
// hooks/useTikitakaSession.ts
import { useState, useCallback } from "react";
import { ChatResponse, SessionState, Bubble } from "../types/tikitaka";

interface UseTikitakaSessionReturn {
  sessionId: string | null;
  sessionState: SessionState | null;
  bubbles: Bubble[];
  isLoading: boolean;
  error: Error | null;
  startSession: (birthDate: string, birthTime?: string) => Promise<void>;
  sendMessage: (message: string) => Promise<void>;
  sendChoice: (choice: number) => Promise<void>;
  resetSession: () => void;
}

export function useTikitakaSession(): UseTikitakaSessionReturn {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [sessionState, setSessionState] = useState<SessionState | null>(null);
  const [bubbles, setBubbles] = useState<Bubble[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  // 응답에서 버블 추출 및 추가
  const appendBubbles = useCallback((response: ChatResponse) => {
    const newBubbles: Bubble[] = response.messages.map((msg, index) => ({
      bubble_id: `${response.session_id}_${response.turn}_${index}`,
      character: msg.character,
      emotion: "NEUTRAL",  // V1에서는 감정 정보 없음
      type: msg.type,
      content: msg.content,
      reply_to: null,
      phase: "DIALOGUE",
      timestamp: msg.timestamp,
    }));

    setBubbles((prev) => [...prev, ...newBubbles]);
  }, []);

  // 세션 시작
  const startSession = useCallback(async (birthDate: string, birthTime?: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await tikitakaClient.startSession(birthDate, birthTime);
      setSessionId(response.session_id);
      setSessionState({
        session_id: response.session_id,
        current_turn: response.turn,
        max_turns: 10,
        bonus_turns: 0,
        remaining_turns: 10 - response.turn,
        is_premium: false,
        phase: "GREETING",
        has_eastern_result: true,
        has_western_result: true,
      });
      appendBubbles(response);
    } catch (err) {
      setError(err as Error);
    } finally {
      setIsLoading(false);
    }
  }, [appendBubbles]);

  // 메시지 전송
  const sendMessage = useCallback(async (message: string) => {
    if (!sessionId) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await tikitakaClient.sendMessage(sessionId, message);
      setSessionState((prev) => prev ? {
        ...prev,
        current_turn: response.turn,
        remaining_turns: prev.max_turns + prev.bonus_turns - response.turn,
      } : null);
      appendBubbles(response);
    } catch (err) {
      setError(err as Error);
    } finally {
      setIsLoading(false);
    }
  }, [sessionId, appendBubbles]);

  // 선택 전송
  const sendChoice = useCallback(async (choice: number) => {
    if (!sessionId) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await tikitakaClient.sendChoice(sessionId, choice);
      setSessionState((prev) => prev ? {
        ...prev,
        current_turn: response.turn,
        remaining_turns: prev.max_turns + prev.bonus_turns - response.turn,
      } : null);
      appendBubbles(response);
    } catch (err) {
      setError(err as Error);
    } finally {
      setIsLoading(false);
    }
  }, [sessionId, appendBubbles]);

  // 세션 초기화
  const resetSession = useCallback(() => {
    setSessionId(null);
    setSessionState(null);
    setBubbles([]);
    setError(null);
  }, []);

  return {
    sessionId,
    sessionState,
    bubbles,
    isLoading,
    error,
    startSession,
    sendMessage,
    sendChoice,
    resetSession,
  };
}
```

### 5.2 SSE 연결 훅

```tsx
// hooks/useTikitakaSSE.ts
import { useState, useCallback, useRef, useEffect } from "react";
import { Bubble } from "../types/tikitaka";

interface UseTikitakaSSEReturn {
  connect: (sessionId: string, birthDate: string, birthTime?: string) => void;
  disconnect: () => void;
  isConnected: boolean;
  bubbles: Bubble[];
  streamingBubbleId: string | null;
  error: Error | null;
}

export function useTikitakaSSE(): UseTikitakaSSEReturn {
  const [isConnected, setIsConnected] = useState(false);
  const [bubbles, setBubbles] = useState<Bubble[]>([]);
  const [streamingBubbleId, setStreamingBubbleId] = useState<string | null>(null);
  const [error, setError] = useState<Error | null>(null);

  const abortControllerRef = useRef<AbortController | null>(null);
  const bubblesMapRef = useRef<Map<string, Partial<Bubble>>>(new Map());

  const connect = useCallback((
    sessionId: string | null,
    birthDate: string,
    birthTime?: string,
  ) => {
    // 기존 연결 종료
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    abortControllerRef.current = new AbortController();
    bubblesMapRef.current.clear();
    setBubbles([]);
    setError(null);
    setIsConnected(true);

    fetch(`${API_BASE_URL}/api/v1/fortune/chat/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: sessionId,
        birth_date: birthDate,
        birth_time: birthTime,
      }),
      signal: abortControllerRef.current.signal,
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const reader = response.body?.getReader();
        const decoder = new TextDecoder();

        function read() {
          reader?.read().then(({ done, value }) => {
            if (done) {
              setIsConnected(false);
              return;
            }

            const text = decoder.decode(value, { stream: true });
            const lines = text.split("\n");

            for (const line of lines) {
              if (line.startsWith("data: ")) {
                try {
                  const data = JSON.parse(line.slice(6));
                  handleEvent(data);
                } catch {
                  // JSON 파싱 실패 무시
                }
              }
            }

            read();
          });
        }

        read();
      })
      .catch((err) => {
        if (err.name !== "AbortError") {
          setError(err);
          setIsConnected(false);
        }
      });
  }, []);

  const handleEvent = useCallback((event: any) => {
    const eventType = event.event;
    const data = event.data || event;

    switch (eventType) {
      case "message_start":
      case "bubble_start": {
        const id = data.bubble_id || data.character || `temp_${Date.now()}`;
        bubblesMapRef.current.set(id, {
          bubble_id: id,
          character: data.character,
          emotion: data.emotion || "NEUTRAL",
          type: data.type,
          phase: data.phase || "DIALOGUE",
          content: "",
          reply_to: data.reply_to || null,
        });
        setStreamingBubbleId(id);
        setBubbles(Array.from(bubblesMapRef.current.values()) as Bubble[]);
        break;
      }

      case "message_chunk":
      case "bubble_chunk": {
        const id = data.bubble_id || data.character;
        const bubble = bubblesMapRef.current.get(id);
        if (bubble) {
          bubble.content = (bubble.content || "") + data.content;
          setBubbles(Array.from(bubblesMapRef.current.values()) as Bubble[]);
        }
        break;
      }

      case "message_end":
      case "bubble_end": {
        const id = data.bubble_id || data.character;
        const bubble = bubblesMapRef.current.get(id);
        if (bubble) {
          bubble.content = data.content;
          bubble.timestamp = data.timestamp;
          setBubbles(Array.from(bubblesMapRef.current.values()) as Bubble[]);
        }
        setStreamingBubbleId(null);
        break;
      }

      case "complete":
        setIsConnected(false);
        break;

      case "error":
        setError(new Error(data.message));
        setIsConnected(false);
        break;
    }
  }, []);

  const disconnect = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsConnected(false);
  }, []);

  // 컴포넌트 언마운트 시 연결 종료
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  return {
    connect,
    disconnect,
    isConnected,
    bubbles,
    streamingBubbleId,
    error,
  };
}
```

### 5.3 전체 페이지 컴포넌트

```tsx
// TikitakaPage.tsx
import React, { useState, useCallback } from "react";
import { useTikitakaSession } from "./hooks/useTikitakaSession";
import { useTikitakaSSE } from "./hooks/useTikitakaSSE";
import BubbleList from "./components/BubbleList";
import InputArea from "./components/InputArea";
import TurnIndicator from "./components/TurnIndicator";
import styles from "./TikitakaPage.module.css";

export default function TikitakaPage() {
  const [birthDate, setBirthDate] = useState("");
  const [birthTime, setBirthTime] = useState("");
  const [isStarted, setIsStarted] = useState(false);
  const [useStreaming, setUseStreaming] = useState(true);

  // 세션 기반 방식
  const session = useTikitakaSession();

  // SSE 스트리밍 방식
  const sse = useTikitakaSSE();

  // 현재 사용 중인 버블 목록
  const bubbles = useStreaming ? sse.bubbles : session.bubbles;
  const isLoading = useStreaming ? sse.isConnected : session.isLoading;
  const error = useStreaming ? sse.error : session.error;

  // 세션 시작
  const handleStart = useCallback(() => {
    if (!birthDate) {
      alert("생년월일을 입력해주세요.");
      return;
    }

    setIsStarted(true);

    if (useStreaming) {
      sse.connect(null, birthDate, birthTime || undefined);
    } else {
      session.startSession(birthDate, birthTime || undefined);
    }
  }, [birthDate, birthTime, useStreaming, sse, session]);

  // 메시지 전송
  const handleSendMessage = useCallback((message: string) => {
    if (useStreaming) {
      // 스트리밍 모드에서는 새 연결 필요
      // (실제 구현에서는 기존 세션 ID 사용)
    } else {
      session.sendMessage(message);
    }
  }, [useStreaming, session]);

  // 선택 전송
  const handleSelectChoice = useCallback((choice: number) => {
    session.sendChoice(choice);
  }, [session]);

  // 시작 화면
  if (!isStarted) {
    return (
      <div className={styles.startScreen}>
        <h1>티키타카</h1>
        <p>소이설과 스텔라가 함께 운세를 분석해드립니다</p>

        <div className={styles.inputGroup}>
          <label>생년월일 (필수)</label>
          <input
            type="date"
            value={birthDate}
            onChange={(e) => setBirthDate(e.target.value)}
          />
        </div>

        <div className={styles.inputGroup}>
          <label>출생시간 (선택)</label>
          <input
            type="time"
            value={birthTime}
            onChange={(e) => setBirthTime(e.target.value)}
          />
        </div>

        <div className={styles.toggleGroup}>
          <label>
            <input
              type="checkbox"
              checked={useStreaming}
              onChange={(e) => setUseStreaming(e.target.checked)}
            />
            실시간 스트리밍 사용
          </label>
        </div>

        <button onClick={handleStart} className={styles.startButton}>
          대화 시작하기
        </button>
      </div>
    );
  }

  // 대화 화면
  return (
    <div className={styles.chatScreen}>
      {/* 헤더 */}
      <header className={styles.header}>
        <h1>티키타카</h1>
        {session.sessionState && (
          <TurnIndicator
            currentTurn={session.sessionState.current_turn}
            maxTurns={session.sessionState.max_turns}
            bonusTurns={session.sessionState.bonus_turns}
            isPremium={session.sessionState.is_premium}
          />
        )}
      </header>

      {/* 에러 표시 */}
      {error && (
        <div className={styles.errorBanner}>
          {error.message}
        </div>
      )}

      {/* 버블 목록 */}
      <main className={styles.chatArea}>
        <BubbleList
          bubbles={bubbles}
          streamingBubbleId={sse.streamingBubbleId}
          isTyping={isLoading}
          typingCharacter={sse.isConnected ? "SOISEOL" : undefined}
        />
      </main>

      {/* 입력 영역 */}
      <footer className={styles.inputContainer}>
        <InputArea
          onSendMessage={handleSendMessage}
          onSelectChoice={handleSelectChoice}
          uiHints={session.sessionState?.ui_hints || { show_choice: false }}
          disabled={isLoading}
        />
      </footer>
    </div>
  );
}
```

---

## 6. 에러 핸들링

### 6.1 에러 타입

```typescript
// types/errors.ts
export enum TikitakaErrorCode {
  // 네트워크 에러
  NETWORK_ERROR = "NETWORK_ERROR",
  TIMEOUT = "TIMEOUT",
  SSE_DISCONNECTED = "SSE_DISCONNECTED",

  // 서버 에러
  SERVER_ERROR = "SERVER_ERROR",
  PARSE_ERROR = "PARSE_ERROR",
  SESSION_EXPIRED = "SESSION_EXPIRED",

  // 비즈니스 에러
  INVALID_BIRTH_DATE = "INVALID_BIRTH_DATE",
  SESSION_NOT_FOUND = "SESSION_NOT_FOUND",
  TURNS_EXHAUSTED = "TURNS_EXHAUSTED",
}

export interface TikitakaError extends Error {
  code: TikitakaErrorCode;
  recoverable: boolean;
  details?: Record<string, unknown>;
}

export function createTikitakaError(
  code: TikitakaErrorCode,
  message: string,
  recoverable: boolean = false,
): TikitakaError {
  const error = new Error(message) as TikitakaError;
  error.code = code;
  error.recoverable = recoverable;
  return error;
}
```

### 6.2 에러 메시지 매핑

```typescript
// utils/errorMessages.ts
const ERROR_MESSAGES: Record<TikitakaErrorCode, string> = {
  NETWORK_ERROR: "네트워크 연결을 확인해주세요.",
  TIMEOUT: "응답 시간이 초과되었습니다. 다시 시도해주세요.",
  SSE_DISCONNECTED: "연결이 끊겼습니다. 자동으로 재연결을 시도합니다.",
  SERVER_ERROR: "서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
  PARSE_ERROR: "응답을 처리하는 중 오류가 발생했습니다.",
  SESSION_EXPIRED: "세션이 만료되었습니다. 새로운 대화를 시작해주세요.",
  INVALID_BIRTH_DATE: "올바른 생년월일을 입력해주세요.",
  SESSION_NOT_FOUND: "세션을 찾을 수 없습니다. 새로운 대화를 시작해주세요.",
  TURNS_EXHAUSTED: "대화 횟수가 모두 소진되었습니다.",
};

export function getErrorMessage(error: TikitakaError | Error): string {
  if ("code" in error) {
    return ERROR_MESSAGES[error.code] || error.message;
  }
  return error.message || "알 수 없는 오류가 발생했습니다.";
}
```

### 6.3 에러 바운더리 컴포넌트

```tsx
// components/TikitakaErrorBoundary.tsx
import React, { Component, ReactNode } from "react";
import styles from "./TikitakaErrorBoundary.module.css";

interface Props {
  children: ReactNode;
  onReset?: () => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class TikitakaErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo): void {
    console.error("TikitakaErrorBoundary caught error:", error, errorInfo);
  }

  handleReset = (): void => {
    this.setState({ hasError: false, error: null });
    this.props.onReset?.();
  };

  render(): ReactNode {
    if (this.state.hasError) {
      return (
        <div className={styles.errorContainer}>
          <div className={styles.errorContent}>
            <h2>문제가 발생했습니다</h2>
            <p>{this.state.error?.message || "알 수 없는 오류"}</p>
            <button onClick={this.handleReset} className={styles.retryButton}>
              다시 시도
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
```

---

## 7. 스타일링 가이드

### 7.1 캐릭터별 색상 팔레트

```css
/* variables.css */
:root {
  /* 소이설 (동양 - 따뜻한 톤) */
  --soiseol-primary: #FF6B8A;
  --soiseol-secondary: #FFB6C1;
  --soiseol-background: #FFF0F3;
  --soiseol-text: #8B3A4A;

  /* 스텔라 (서양 - 차가운 톤) */
  --stella-primary: #6B8BFF;
  --stella-secondary: #B6C1FF;
  --stella-background: #F0F4FF;
  --stella-text: #3A4A8B;

  /* 시스템 */
  --system-primary: #888888;
  --system-background: #F5F5F5;

  /* 공통 */
  --text-primary: #1A1A1A;
  --text-secondary: #666666;
  --border-color: #E0E0E0;
  --shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}
```

### 7.2 감정별 스타일

```css
/* emotions.css */

/* 감정별 버블 배경색 */
.bubble[data-emotion="NEUTRAL"] {
  background: var(--bubble-bg);
}

.bubble[data-emotion="HAPPY"] {
  background: linear-gradient(135deg, #FFF9E6 0%, #FFF4D6 100%);
  border-color: #FFD700;
}

.bubble[data-emotion="CURIOUS"] {
  background: linear-gradient(135deg, #E6F4FF 0%, #D6EBFF 100%);
  border-color: #4A9EFF;
}

.bubble[data-emotion="THOUGHTFUL"] {
  background: linear-gradient(135deg, #F0F0F0 0%, #E8E8E8 100%);
  border-color: #999999;
}

.bubble[data-emotion="SURPRISED"] {
  background: linear-gradient(135deg, #FFF0E6 0%, #FFE6D6 100%);
  border-color: #FF8C00;
}

.bubble[data-emotion="CONCERNED"] {
  background: linear-gradient(135deg, #FFE6E6 0%, #FFD6D6 100%);
  border-color: #FF6B6B;
}

.bubble[data-emotion="CONFIDENT"] {
  background: linear-gradient(135deg, #E6E6FF 0%, #D6D6FF 100%);
  border-color: #6B6BFF;
}

.bubble[data-emotion="PLAYFUL"] {
  background: linear-gradient(135deg, #FFE6F5 0%, #FFD6EC 100%);
  border-color: #FF6BB5;
}

.bubble[data-emotion="MYSTERIOUS"] {
  background: linear-gradient(135deg, #F0E6FF 0%, #E6D6FF 100%);
  border-color: #9B6BFF;
}

.bubble[data-emotion="EMPATHETIC"] {
  background: linear-gradient(135deg, #E6FFE6 0%, #D6FFD6 100%);
  border-color: #6BFF6B;
}
```

### 7.3 버블 기본 스타일

```css
/* BubbleItem.module.css */

.bubbleContainer {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 16px;
  max-width: 80%;
}

.bubbleContainer.left {
  justify-content: flex-start;
}

.bubbleContainer.right {
  justify-content: flex-end;
  flex-direction: row-reverse;
  margin-left: auto;
}

.bubbleContainer.center {
  justify-content: center;
  max-width: 100%;
}

.bubble {
  padding: 12px 16px;
  border-radius: 16px;
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow);
  position: relative;
  animation: fadeIn 0.3s ease-out;
}

/* 소이설 버블 */
.bubbleContainer[data-character="SOISEOL"] .bubble {
  background: var(--soiseol-background);
  border-color: var(--soiseol-secondary);
  border-radius: 16px 16px 16px 4px;
}

/* 스텔라 버블 */
.bubbleContainer[data-character="STELLA"] .bubble {
  background: var(--stella-background);
  border-color: var(--stella-secondary);
  border-radius: 16px 16px 4px 16px;
}

/* 시스템 버블 */
.bubbleContainer[data-character="SYSTEM"] .bubble {
  background: var(--system-background);
  border-radius: 8px;
  font-size: 14px;
  color: var(--text-secondary);
}

.content {
  line-height: 1.6;
  word-break: keep-all;
}

.timestamp {
  font-size: 11px;
  color: var(--text-secondary);
  margin-top: 8px;
  text-align: right;
}

.cursor {
  animation: blink 0.7s infinite;
}

.replyIndicator {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 4px;
  padding-bottom: 4px;
  border-bottom: 1px solid var(--border-color);
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}
```

### 7.4 애니메이션

```css
/* animations.css */

/* 버블 등장 애니메이션 */
@keyframes bubbleFadeIn {
  from {
    opacity: 0;
    transform: translateY(20px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

@keyframes bubbleSlideIn {
  from {
    opacity: 0;
    transform: translateX(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes bubbleBounce {
  0% {
    transform: scale(0.9);
  }
  50% {
    transform: scale(1.05);
  }
  100% {
    transform: scale(1);
  }
}

/* 타이핑 인디케이터 */
@keyframes typingDot {
  0%, 20% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-5px);
  }
  80%, 100% {
    transform: translateY(0);
  }
}

.typingDots span {
  display: inline-block;
  width: 8px;
  height: 8px;
  margin: 0 2px;
  background: var(--text-secondary);
  border-radius: 50%;
  animation: typingDot 1.4s infinite;
}

.typingDots span:nth-child(2) {
  animation-delay: 0.2s;
}

.typingDots span:nth-child(3) {
  animation-delay: 0.4s;
}
```

---

## 8. 참조 문서

### 8.1 내부 문서

| 문서 | 경로 | 설명 |
|------|------|------|
| 티키타카 스키마 V2 PRD | `ai/docs/prd/tikitaka-schema-v2.md` | 스키마 정의 |
| 버블 파서 설계 | `ai/docs/design/tikitaka-bubble-parser.md` | 파서 설계 |
| 세션 라이프사이클 | `ai/docs/design/tikitaka-session-lifecycle.md` | 세션 관리 |
| 요약 스키마 | `ai/docs/design/tikitaka-summary-schema.md` | 요약 화면 |

### 8.2 현재 구현 파일

| 파일 | 경로 | 설명 |
|------|------|------|
| 채팅 API | `ai/src/yeji_ai/api/v1/fortune/chat.py` | API 엔드포인트 |
| 티키타카 서비스 | `ai/src/yeji_ai/services/tikitaka_service.py` | 비즈니스 로직 |
| 채팅 모델 | `ai/src/yeji_ai/models/fortune/chat.py` | 데이터 모델 |

### 8.3 외부 참조

- [Server-Sent Events (MDN)](https://developer.mozilla.org/ko/docs/Web/API/Server-sent_events)
- [EventSource (MDN)](https://developer.mozilla.org/ko/docs/Web/API/EventSource)
- [React TypeScript Cheatsheet](https://react-typescript-cheatsheet.netlify.app/)

---

## 변경 이력

| 버전 | 날짜 | 변경 내용 | 작성자 |
|------|------|----------|--------|
| 1.0.0 | 2026-01-30 | 초기 버전 | YEJI AI팀 |

---

## 부록

### A. TypeScript 타입 정의 전체

```typescript
// types/tikitaka.ts

// ============================================================
// Enum 정의
// ============================================================

export type CharacterCode = "SOISEOL" | "STELLA" | "SYSTEM";

export type EmotionCode =
  | "NEUTRAL"
  | "HAPPY"
  | "CURIOUS"
  | "THOUGHTFUL"
  | "SURPRISED"
  | "CONCERNED"
  | "CONFIDENT"
  | "PLAYFUL"
  | "MYSTERIOUS"
  | "EMPATHETIC";

export type MessageType =
  | "GREETING"
  | "INFO_REQUEST"
  | "INTERPRETATION"
  | "DEBATE"
  | "CONSENSUS"
  | "QUESTION"
  | "CHOICE"
  | "SUMMARY"
  | "FAREWELL";

export type PhaseCode =
  | "GREETING"
  | "DIALOGUE"
  | "QUESTION"
  | "SUMMARY"
  | "FAREWELL";

// ============================================================
// 인터페이스 정의
// ============================================================

export interface Bubble {
  bubble_id: string;
  character: CharacterCode;
  emotion: EmotionCode;
  type: MessageType;
  content: string;
  reply_to: string | null;
  phase: PhaseCode;
  timestamp?: string;
  ui_hint?: UIHint;
}

export interface UIHint {
  highlight?: boolean;
  animation?: "fade" | "slide" | "bounce";
  delay_ms?: number;
  typing_effect?: boolean;
}

export interface SessionState {
  session_id: string;
  current_turn: number;
  max_turns: number;
  bonus_turns: number;
  remaining_turns: number;
  is_premium: boolean;
  phase: PhaseCode;
  has_eastern_result: boolean;
  has_western_result: boolean;
  ui_hints?: ChatUIHints;
}

export interface ChoiceOption {
  value: number;
  character: CharacterCode;
  label: string;
  description?: string;
}

export interface ChatUIHints {
  show_choice: boolean;
  choices?: ChoiceOption[];
  input_placeholder?: string;
  show_typing_indicator?: boolean;
}

export interface ChatDebateStatus {
  is_consensus: boolean;
  eastern_opinion?: string;
  western_opinion?: string;
  consensus_point?: string;
  question?: string;
}

export interface ChatMessage {
  character: CharacterCode;
  type: MessageType;
  content: string;
  timestamp: string;
}

export interface ChatRequest {
  session_id?: string | null;
  message?: string;
  birth_date?: string;
  birth_time?: string;
  birth_place?: string;
  choice?: number;
}

export interface ChatResponse {
  session_id: string;
  turn: number;
  messages: ChatMessage[];
  debate_status: ChatDebateStatus;
  ui_hints: ChatUIHints;
}

// ============================================================
// SSE 이벤트 타입
// ============================================================

export type SSEEventType =
  | "session"
  | "phase_change"
  | "bubble_start"
  | "bubble_chunk"
  | "bubble_end"
  | "turn_update"
  | "warning_low_turns"
  | "debate_status"
  | "ui_hint"
  | "pause"
  | "complete"
  | "error";

export interface SSEEvent<T = unknown> {
  event: SSEEventType;
  data: T;
}

export interface BubbleStartEvent {
  bubble_id: string;
  character: CharacterCode;
  emotion?: EmotionCode;
  type: MessageType;
  phase?: PhaseCode;
  reply_to?: string;
}

export interface BubbleChunkEvent {
  bubble_id: string;
  content: string;
}

export interface BubbleEndEvent {
  bubble_id: string;
  content: string;
  timestamp: string;
}

export interface PhaseChangeEvent {
  from_phase: PhaseCode;
  to_phase: PhaseCode;
  reason?: string;
}

export interface TurnUpdateEvent {
  current_turn: number;
  remaining_turns: number;
  is_last_turn: boolean;
}
```

### B. API 응답 예시

```json
{
  "session_id": "abc12345",
  "turn": 2,
  "messages": [
    {
      "character": "SOISEOL",
      "type": "INTERPRETATION",
      "content": "병화 일간이시네요~ 밝고 열정적인 기운이 느껴져요! 타고난 리더십이 있으시네요~",
      "timestamp": "2026-01-30T15:30:00Z"
    },
    {
      "character": "STELLA",
      "type": "INTERPRETATION",
      "content": "양자리 태양이군. 사주와 마찬가지로 리더십이 강해. 행동력도 뛰어나고.",
      "timestamp": "2026-01-30T15:30:05Z"
    },
    {
      "character": "SOISEOL",
      "type": "CONSENSUS",
      "content": "스텔라도 같은 걸 봤네요! 둘 다 리더십이 강하다고 해석했어요~ 더 궁금한 운세가 있으신가요?",
      "timestamp": "2026-01-30T15:30:10Z"
    }
  ],
  "debate_status": {
    "is_consensus": true,
    "eastern_opinion": "병화 일간의 리더십과 열정",
    "western_opinion": "양자리 태양의 추진력과 행동력",
    "consensus_point": "둘 다 리더십이 강하다고 봅니다",
    "question": "연애운, 직장운, 금전운 중 어떤 것이 가장 궁금하신가요?"
  },
  "ui_hints": {
    "show_choice": false,
    "input_placeholder": "궁금한 운세를 물어보세요..."
  }
}
```

---

> **Note**: 이 가이드는 V1 API 기준으로 작성되었으며, V2 API 출시 시 업데이트될 예정입니다.
> SSE 스트리밍 기능은 실시간 응답이 필요한 경우 사용을 권장합니다.
