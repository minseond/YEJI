# Session Turn Policy v1.0.0

동/서양 티키타카 운세 채팅의 턴 진행, 종료, 유료 확장 정책 명세서

---

## 개요

### 기본 원칙

1. **기본 턴 수**: `base_turns = 3`
2. **최대 턴 수**: `max_turns` (플랜에 따라 다름)
3. **1턴 = 캐릭터 응답 + 사용자 입력(또는 세션 종료)까지**

---

## 턴 진행 흐름

### Turn 1: 기본 성격 분석

```
[사용자] 생년월일 입력
    ↓
[EAST/WEST] 기본 성격 분석 (bubbles[])
    ↓
[turn_end] await_user_input → "더 궁금한 운세 선택"
```

**턴 내용:**
- 동양: 사주 기본 분석 (일간, 오행, 음양)
- 서양: 별자리 기본 분석 (태양궁, 원소, 양태)
- 공통점/차이점 언급 (합의 또는 토론)

### Turn 2: 선택 주제 상세 분석

```
[사용자] 연애/금전/직장/건강 중 선택
    ↓
[EAST/WEST] 선택 주제 상세 분석 (bubbles[])
    ↓
[turn_end] await_user_input → "추가 질문 또는 다른 주제"
```

**턴 내용:**
- 선택한 카테고리에 대한 심층 분석
- 캐릭터별 조언 제공
- 추가 질문 유도

### Turn 3: 마무리 (기본 사용자)

```
[사용자] 추가 질문 또는 "끝내기"
    ↓
[EAST/WEST] 답변 + 마무리 인사 (bubbles[])
    ↓
[turn_end] completed → closure(summary, next_steps, upgrade_hook)
```

**턴 내용:**
- 최종 조언 및 응원 메시지
- 세션 요약 제공
- 업그레이드 훅 노출 (기본 사용자)

---

## 종료 판정 조건

### 자연 종료 (Natural End)

다음 조건 **모두** 충족 시 세션 종료:

```
turn_end.type = "completed"
AND
turn_end.closure.end_marker = "END_SESSION"
```

### 강제 종료 케이스

| 케이스 | 조건 | 처리 |
|--------|------|------|
| 턴 한도 도달 | `current_turn >= base_turns` (비프리미엄) | completed + upgrade_hook |
| 프리미엄 한도 | `current_turn >= max_turns` | completed (upgrade_hook 비활성) |
| 사용자 요청 | user_input.value = "끝내기" | 즉시 completed |
| 타임아웃 | 세션 유휴 30분 초과 | 서버측 세션 만료 |

### 종료 시 필수 반환 항목

```json
{
  "turn_end": {
    "type": "completed",
    "closure": {
      "summary": [...],           // 필수: 최소 1개
      "next_steps": [...],        // 필수: 빈 배열 가능
      "upgrade_hook": {...},      // 필수
      "end_marker": "END_SESSION" // 필수: 고정값
    }
  }
}
```

---

## 유료 확장 정책

### 플랜별 턴 한도

| 플랜 | base_turns | max_turns | upgrade_hook |
|------|------------|-----------|--------------|
| Free | 3 | 3 | 활성화 |
| Basic | 3 | 10 | Turn 10에서 활성화 |
| Premium | 3 | 30 | 비활성화 |
| Unlimited | 3 | 무제한 | 비활성화 |

### upgrade_hook 노출 조건

#### 활성화 조건 (enabled = true)

```
(is_premium = false) AND (current_turn = base_turns)
```

**예시:**
- Free 플랜 + Turn 3 → upgrade_hook 활성화
- Basic 플랜 + Turn 10 → upgrade_hook 활성화

#### 비활성화 조건 (enabled = false)

```
(is_premium = true) OR (current_turn < base_turns) OR (current_turn < max_turns)
```

### upgrade_hook 문구 규칙

#### 문구 템플릿

| 상황 | message | cta_label |
|------|---------|-----------|
| 첫 3턴 완료 | "더 깊은 운세 분석을 원하시나요? 프리미엄으로 업그레이드하세요!" | "프리미엄 시작하기" |
| Basic 10턴 완료 | "연간 상세 분석과 무제한 상담을 원하시면 Premium으로!" | "Premium 업그레이드" |
| 특별 프로모션 | "지금 업그레이드하면 첫 달 50% 할인!" | "할인 받기" |

#### cta_action 값

| 액션 | 설명 | 프론트 동작 |
|------|------|-------------|
| `upgrade_premium` | 프리미엄 결제 페이지 | /pricing/premium 이동 |
| `upgrade_basic` | 베이직 결제 페이지 | /pricing/basic 이동 |
| `show_promo` | 프로모션 모달 | 모달 표시 |
| `share_for_bonus` | 공유하면 보너스 턴 | 공유 모달 표시 |

### 예시: upgrade_hook 객체

**활성화 (Free → Premium 유도)**
```json
{
  "enabled": true,
  "message": "더 깊은 운세 분석을 원하시나요? 프리미엄으로 업그레이드하면 무제한 상담이 가능해요!",
  "cta_label": "프리미엄 시작하기",
  "cta_action": "upgrade_premium"
}
```

**비활성화 (이미 Premium)**
```json
{
  "enabled": false,
  "message": null,
  "cta_label": null,
  "cta_action": null
}
```

---

## 턴 연장 메커니즘

### 프리미엄 사용자 턴 연장

프리미엄 사용자가 `base_turns`(3) 이후에도 대화 계속:

```
[Turn 3]
turn_end.type = "await_user_input"  // completed 아님
meta.current_turn = 3
meta.base_turns = 3
meta.max_turns = 30
meta.is_premium = true
```

### 업그레이드 직후 처리

사용자가 Turn 3 완료 후 업그레이드한 경우:

1. 서버: `is_premium = true`, `max_turns` 업데이트
2. 클라이언트: 새 세션 시작 또는 기존 세션 이어서 Turn 4 요청 가능

---

## 에지 케이스 처리

### 1. 사용자가 응답 없이 세션 이탈

- 30분 타임아웃 후 세션 만료
- 재접속 시 새 세션 생성 권장 (기존 세션 복구 옵션 제공 가능)

### 2. 동일 주제 반복 선택

- 허용하되, 이전 응답과 다른 관점 제공
- "이전에 {topic}에 대해 말씀드렸는데, 추가로 궁금한 점이 있으신가요?"

### 3. 모든 카테고리 소진

- 5개 카테고리(total, love, wealth, career, health) 모두 질문 완료 시
- "모든 운세를 살펴보았네요. 오늘의 종합 조언을 드릴게요." → 자연 종료

### 4. 사용자 입력 거부/빈 응답

- 빈 입력 시 재입력 요청
- 3회 연속 빈 입력 시 기본 주제(total)로 진행

---

## 메타 정보 업데이트 규칙

### 각 턴마다 meta 필드 업데이트

```typescript
meta: {
  current_turn: prev.current_turn + 1,
  base_turns: 3,                      // 고정
  max_turns: user.plan.max_turns,     // 플랜에 따라
  is_premium: user.plan.is_premium,   // 플랜에 따라
  category: selected_category         // 선택된 카테고리
}
```

### category 업데이트 시점

| 턴 | category 값 |
|----|-------------|
| Turn 1 | "total" (기본) |
| Turn 2+ | 사용자 선택 카테고리 |

---

## 프론트엔드 구현 가이드

### 턴 상태 판별 로직

```typescript
function handleTurnResponse(response: TurnResponse) {
  const { turn_end, meta } = response;

  if (turn_end.type === "await_user_input") {
    // 사용자 입력 UI 표시
    showInputPrompt(turn_end.user_prompt);
  } else if (turn_end.type === "completed") {
    // 세션 종료 UI 표시
    showSummary(turn_end.closure.summary);
    showNextSteps(turn_end.closure.next_steps);

    if (turn_end.closure.upgrade_hook.enabled) {
      showUpgradeModal(turn_end.closure.upgrade_hook);
    }
  }
}
```

### 업그레이드 훅 표시 조건

```typescript
function shouldShowUpgrade(closure: Closure): boolean {
  return closure.upgrade_hook.enabled === true;
}
```

---

## 버전 히스토리

| 버전 | 날짜 | 변경 사항 |
|------|------|----------|
| 1.0.0 | 2026-01-30 | 초기 턴 정책 정의 |
