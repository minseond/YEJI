# API 변경사항 v0.4.0 → v0.4.1

> 작성일: 2026-02-02
> 버전: v0.4.1

## 개요

이 문서는 백엔드에서 AI 서버를 호출할 때 알아야 할 변경사항을 정리합니다.

---

## 1. 엔드포인트 변경 없음

**기존 API 엔드포인트는 모두 동일**하게 유지됩니다.

| 엔드포인트 | 메서드 | 변경여부 |
|-----------|--------|---------|
| `/api/v1/fortune/eastern` | POST | 변경 없음 |
| `/api/v1/fortune/western` | POST | 변경 없음 |
| `/api/v1/fortune/chat/turn/start` | POST | 변경 없음 |
| `/api/v1/fortune/chat/turn/continue` | POST | 변경 없음 |
| `/api/v1/fortune/chat/stream` | POST | 변경 없음 |
| `/api/v1/fortune/chat/complete` | POST | 변경 없음 |
| `/api/v1/fortune/tikitaka/stream` | POST | 변경 없음 |

---

## 2. 내부 동작 변경 (백엔드 영향 없음)

### 2.1 GPT-5-mini 사용자 질문 전달 (Layer 5)

**변경 내용:**
- 채팅 턴에서 사용자 질문(`message`)이 GPT-5-mini 프롬프트에 직접 전달됩니다.
- 기존: 사용자 질문이 프롬프트에 포함되지 않았음
- 변경: `<user_question>` 태그로 프롬프트에 포함

**백엔드 영향:**
- **없음** - 기존 요청/응답 스키마 동일

**효과:**
- 사용자 질문에 더 정확하게 응답
- 맥락 인식 향상

### 2.2 숫자 공백 오류 수정 필터

**변경 내용:**
- LLM 응답에서 `"66. 7%"` → `"66.7%"` 자동 수정
- 소수점 앞뒤 잘못된 공백 제거

**백엔드 영향:**
- **없음** - 응답 후처리 개선

### 2.3 LLM Provider 전환 시스템

**변경 내용:**
- `USE_GPT5MINI_FOR_CHAT` 환경변수로 채팅 LLM 선택
  - `true` + `OPENAI_API_KEY` 있음 → GPT-5-mini 사용
  - `false` 또는 API 키 없음 → 8B vLLM 사용

**백엔드 영향:**
- **없음** - 서버 측 환경변수 설정만 필요

---

## 3. 환경변수 변경

### 3.1 새로 추가된 환경변수

| 변수명 | 기본값 | 설명 |
|--------|--------|------|
| `USE_GPT5MINI_FOR_CHAT` | `false` | 채팅에 GPT-5-mini 사용 여부 |
| `OPENAI_API_KEY` | - | OpenAI API 키 (GPT-5-mini용) |
| `OPENAI_MODEL` | `gpt-5-mini` | 사용할 OpenAI 모델명 |

### 3.2 기존 환경변수 (변경 없음)

| 변수명 | 설명 |
|--------|------|
| `VLLM_BASE_URL` | vLLM 서버 URL |
| `VLLM_MODEL` | vLLM 모델명 |

---

## 4. 응답 스키마 변경 없음

모든 API 응답 스키마는 v0.4.0과 **동일**합니다.

### Eastern Fortune 응답
```json
{
  "element": "FIRE",
  "stats": { ... },
  "fortune_content": { ... },
  "lucky": { ... }
}
```

### Western Fortune 응답
```json
{
  "element": "FIRE",
  "stats": { ... },
  "fortune_content": { ... },
  "lucky": { ... }
}
```

### Chat Turn 응답
```json
{
  "session_id": "...",
  "turn": 1,
  "messages": [ ... ],
  "debate_status": { ... },
  "ui_hints": { ... }
}
```

---

## 5. 호환성

| 항목 | 상태 |
|------|------|
| v0.4.0 요청 스키마 | ✅ 호환 |
| v0.4.0 응답 스키마 | ✅ 호환 |
| 기존 세션 | ✅ 호환 |
| Redis 캐시 | ✅ 호환 |

---

## 6. 테스트 결과

| 테스트 영역 | 결과 | 테스트 수 |
|------------|------|----------|
| Eastern Fortune | ✅ PASS | 89개 |
| Western Fortune | ✅ PASS | 96개 |
| Chat/Tikitaka | ✅ PASS | 전체 통과 |

---

## 7. 마이그레이션 필요사항

**백엔드 측 변경 불필요**

프로덕션 배포 시 Jenkins에서 자동으로 환경변수가 설정됩니다:
- `USE_GPT5MINI_FOR_CHAT=true`
- `OPENAI_API_KEY` (credentials에서 주입)
- `OPENAI_MODEL=gpt-5-mini`

---

## 8. 릴리즈 노트 요약

### v0.4.1 (2026-02-02)

**개선사항:**
- 사용자 질문을 GPT-5-mini 프롬프트에 전달 (Layer 5)
- 숫자 공백 오류 수정 필터 추가
- LLM Provider 전환 시스템 (환경변수 기반)

**버그 수정:**
- "66. 7%" 같은 소수점 공백 오류 자동 수정

**하위 호환성:**
- v0.4.0 API와 완전 호환
