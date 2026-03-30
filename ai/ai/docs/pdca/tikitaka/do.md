# Do: 티키타카 운세 대화 시스템 구현

## 구현 로그 (시계열)

### 2026-01-30 23:30 - 설계 문서 작성

**작업**: plan.md 작성
- 아키텍처 다이어그램
- LLM 출력 스키마 설계
- 프롬프트 템플릿 설계
- 파일 생성 계획

### 2026-01-30 23:31 - 모델 스키마 구현

**작업**: `models/fortune/turn.py` 생성

생성된 모델:
- `Speaker` - 발화자 enum (EAST, WEST)
- `EmotionCode` - 감정 코드 enum (12종)
- `FortuneCategory` - 운세 카테고리 enum
- `Emotion` - 감정 정보 모델
- `Bubble` - 캐릭터 발화 버블
- `TurnEndAwaitUserInput` - 사용자 입력 대기
- `TurnEndCompleted` - 세션 완료
- `Meta` - 메타 정보
- `TurnRequest` / `TurnResponse` - 요청/응답 모델
- 헬퍼 함수: `create_bubble()`, `create_await_user_input()`, `create_completed()`

### 2026-01-30 23:32 - 대화 스키마 구현

**작업**: `models/fortune/dialogue.py` 생성

생성된 모델:
- `DialogueMode` - 대화 모드 enum (battle, consensus)
- `DialogueLine` - LLM 출력 단일 라인
- `DialogueOutput` - LLM 대화 생성 결과
- `EasternContext` / `WesternContext` - 컨텍스트 모델
- `TikitakaSessionState` - 세션 상태 관리

### 2026-01-30 23:33 - 프롬프트 템플릿 구현

**작업**: `prompts/tikitaka_prompts.py` 생성

생성된 프롬프트:
- `TIKITAKA_SYSTEM_PROMPT` - 공통 시스템 프롬프트
- `BATTLE_MODE_PROMPT` - 대결 모드 (70~80%)
- `CONSENSUS_MODE_PROMPT` - 합의 모드 (20~30%)
- `TURN1_INTRO_PROMPT` - 첫 턴 전용
- `SESSION_END_PROMPT` - 세션 종료 전용
- `TOPIC_HINTS` - 주제별 힌트
- `build_tikitaka_prompt()` - 프롬프트 빌더 함수

**오류 발생**: 문자열 리터럴 종료 오류
```
E   SyntaxError: unterminated string literal (detected at line 95)
```

**원인**: 삼중 따옴표 문자열 내 이중 따옴표 처리 문제
**해결**: 마지막 줄 따옴표 분리
```python
# 오류
WEST: "...해요!""""

# 수정
WEST: "...해요!"
"""
```

### 2026-01-30 23:34 - 서비스 클래스 구현

**작업**: `services/tikitaka_dialogue_generator.py` 생성

구현된 클래스: `TikitakaDialogueGenerator`

메서드:
1. `format_eastern_context()` - 동양 사주 컨텍스트 포맷팅
2. `format_western_context()` - 서양 점성술 컨텍스트 포맷팅
3. `decide_battle_or_consensus()` - 대결/합의 모드 결정 (75:25)
4. `generate_dialogues()` - LLM 대화 생성
5. `build_turn_response()` - TurnResponse JSON 조립
6. `generate_turn()` - 메인 엔트리 포인트

**설계 결정**:
- `BATTLE_PROBABILITY = 0.75` (75% 대결)
- LLM 호출 실패 시 폴백 응답 제공
- 세션 완료 조건: 무료 = base_turns, 프리미엄 = max_turns

### 2026-01-30 23:35 - 테스트 코드 작성

**작업**: `tests/test_tikitaka_dialogue.py` 생성

테스트 카테고리:
1. **모델 검증** (6 tests)
   - Bubble 생성
   - 텍스트 길이 검증
   - Emotion intensity 범위
   - Meta 모델
   - TurnEnd 타입

2. **세션 상태** (5 tests)
   - 다음 턴 ID
   - 무료/프리미엄 완료 조건
   - 버블/프롬프트 ID 생성

3. **Generator 메서드** (6 tests)
   - 대결/합의 모드 분포
   - TurnResponse 구조
   - 마지막 턴 처리
   - 폴백 대화

4. **컨텍스트 포맷팅** (2 tests)
   - 동양/서양 컨텍스트

5. **JSON 검증** (3 tests)
   - 직렬화
   - 왕복
   - Contract 준수

6. **LLM 통합** (2 tests)
   - Mock 성공
   - 폴백 처리

7. **비율 검증** (1 test)
   - 100회 생성 비율

8. **개인화** (1 test)
   - 다른 컨텍스트 → 다른 프롬프트

### 2026-01-30 23:36 - 테스트 실행

**결과**: ✅ 26 passed in 0.07s

```
tests/test_tikitaka_dialogue.py::TestTurnResponseModel::test_bubble_creation PASSED
tests/test_tikitaka_dialogue.py::TestTurnResponseModel::test_bubble_validation_text_length PASSED
tests/test_tikitaka_dialogue.py::TestTurnResponseModel::test_emotion_intensity_range PASSED
...
tests/test_tikitaka_dialogue.py::TestBattleConsensusRatio::test_ratio_over_100_generations PASSED
tests/test_tikitaka_dialogue.py::TestPersonalization::test_different_contexts_different_prompts PASSED
```

---

## 생성된 파일 목록

| 파일 | 라인 수 | 설명 |
|------|---------|------|
| `models/fortune/turn.py` | ~250 | TurnResponse 스키마 |
| `models/fortune/dialogue.py` | ~100 | DialogueOutput LLM 스키마 |
| `services/tikitaka_dialogue_generator.py` | ~350 | 대화 생성 서비스 |
| `prompts/tikitaka_prompts.py` | ~250 | 프롬프트 템플릿 |
| `tests/test_tikitaka_dialogue.py` | ~400 | 테스트 코드 |
| `docs/pdca/tikitaka/plan.md` | ~300 | 설계 문서 |

---

## 학습 포인트

### 1. Python 삼중 따옴표 문자열
삼중 따옴표 문자열 끝에 이중 따옴표가 붙으면 파싱 오류 발생.
해결: 마지막 줄 분리

### 2. LLM + 코드 조합 아키텍처
- LLM: 텍스트 콘텐츠만 생성 (대화, 감정)
- 코드: 구조 데이터 생성 (ID, timestamp, meta)
- 장점: JSON 구조 100% 일관성 보장

### 3. 대결/합의 비율 검증
- 1000회 시뮬레이션으로 75% ± 10% 범위 확인
- 통계적 검증으로 비율 안정성 확보
