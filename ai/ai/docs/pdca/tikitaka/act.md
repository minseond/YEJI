# Act: 티키타카 운세 대화 시스템 개선

## 성공 패턴 → 정식화

### 패턴 1: LLM + 코드 조합 아키텍처

**문서화**: `docs/patterns/tikitaka-generation.md`

**핵심 원칙**:
- LLM: 창의적 콘텐츠만 생성 (텍스트, 감정)
- 코드: 구조적 데이터 생성 (ID, timestamp, meta)

**장점**:
- JSON 구조 100% 일관성
- LLM 실패 시 폴백 가능
- 검증 규칙 자동 준수

### 패턴 2: 확률 기반 모드 전환

**적용**: `decide_battle_or_consensus()`

**핵심 원칙**:
- 기본 모드와 변형 모드 비율 설정
- 단조로움 방지 + 의외성 제공

**구현**:
```python
BATTLE_PROBABILITY = 0.75  # 75% 대결
if random.random() < BATTLE_PROBABILITY:
    return DialogueMode.BATTLE
return DialogueMode.CONSENSUS
```

### 패턴 3: 세션 상태 기반 종료 조건

**적용**: `should_complete()`, `_build_turn_end()`

**핵심 원칙**:
- 무료/프리미엄 분기 명확
- 업그레이드 훅 자동 활성화/비활성화

---

## 학습 → 글로벌 규칙

### CLAUDE.md 업데이트 후보

1. **삼중 따옴표 문자열 처리**
   ```
   # 피해야 할 패턴
   """... content ending with quote!""""  # SyntaxError

   # 올바른 패턴
   """... content ending with quote!"
   """
   ```

2. **LLM 출력 스키마 설계 원칙**
   ```
   - LLM: 창의적 콘텐츠만 생성
   - 코드: 구조적 데이터 생성
   - 폴백: 항상 제공
   ```

---

## 체크리스트 업데이트

### 새 기능 체크리스트 추가 항목

- [ ] LLM + 코드 역할 분리 설계
- [ ] 확률 기반 로직 통계 검증 (최소 100회)
- [ ] 무료/프리미엄 분기 테스트
- [ ] 폴백 응답 구현 및 테스트

---

## 향후 개선 계획

### 단기 (다음 스프린트)

| 항목 | 우선순위 | 예상 작업 |
|------|----------|----------|
| vLLM 통합 테스트 | 높음 | 실제 LLM 호출 테스트 |
| API 엔드포인트 연동 | 높음 | chat.py 라우터 수정 |
| 캐릭터 말투 검증 | 중간 | 후처리기 추가 |

### 중기 (다음 달)

| 항목 | 우선순위 | 예상 작업 |
|------|----------|----------|
| 응답 시간 모니터링 | 중간 | 메트릭 수집 |
| 부하 테스트 | 낮음 | 동시 요청 처리 |
| 프론트엔드 통합 | 높음 | React 컴포넌트 연동 |

---

## 완료 상태

| 태스크 | 상태 |
|--------|------|
| #153 Phase 1: 설계 | ✅ 완료 |
| #154 Phase 2: 검증 | ✅ 완료 |
| #155 Phase 3: 구현 | ✅ 완료 |
| #156 Phase 4: 테스트 | ✅ 완료 |
| #157 Phase 5: 문서화 | ✅ 완료 |

---

## 산출물 요약

| 파일 | 유형 | 용도 |
|------|------|------|
| `models/fortune/turn.py` | 코드 | TurnResponse 스키마 |
| `models/fortune/dialogue.py` | 코드 | LLM 출력 스키마 |
| `services/tikitaka_dialogue_generator.py` | 코드 | 대화 생성 서비스 |
| `prompts/tikitaka_prompts.py` | 코드 | 프롬프트 템플릿 |
| `tests/test_tikitaka_dialogue.py` | 테스트 | 단위/통합 테스트 |
| `docs/pdca/tikitaka/*.md` | 문서 | PDCA 사이클 기록 |
| `docs/patterns/tikitaka-generation.md` | 문서 | 성공 패턴 정리 |
