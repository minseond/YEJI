# YEJI PM 프롬프트 - 티키타카 품질 검증 + 비동기 최적화 + Git 정리

> **목적**: YEJI AI 서버의 전체 품질 검증, 비동기 성능 최적화, API 문서화, Git 히스토리 정리를 체계적으로 진행

---

## 프로젝트 컨텍스트

```yaml
프로젝트: YEJI AI Server
스택: Python 3.11+, FastAPI, Pydantic v2, vLLM, Qwen3
위치: C:/Users/SSAFY/yeji-ai-server/ai/
브랜치:
  - ai/main: 프로덕션
  - ai/develop: 개발

캐릭터 시스템:
  메인:
    - SOISEOL (소이설): 동양 점술가, 하오체/하게체
    - STELLA (스텔라): 서양 점성술사, 해요체
  서브:
    - CHEONGWOON (청운): 소이설 스승, 하오체
    - HWARIN (화린): 소이설 언니, 해요체 (비즈니스)
    - KYLE (카일): 도박사, 반말
    - ELARIA (엘라리아): 공주, 해요체 (왕실)
```

---

## Part 1: 비동기 최적화

### 1.1 현재 비동기 현황

```yaml
잘 구현된 부분:
  - tikitaka_service.py:119 - asyncio.gather(동양, 서양) 동시 분석 ✅
  - tikitaka_service.py:185 - asyncio.gather(소이설, 스텔라) 동시 생성 ✅
  - tikitaka_service.py:361 - asyncio.gather(주제별 해석) ✅
  - saju_service.py:81 - asyncio.create_task(세션 정리) ✅
  - filter/guard.py:141 - run_in_executor(GPU 추론) ✅
  - response_logger.py:205 - run_in_executor(파일 I/O) ✅

개선 필요한 부분 (P0~P3):
  - fortune_generator.py:744 - generate_full() 동양/서양 직렬
  - saju_service.py:254 - 동양/서양/통합/조언 직렬 처리
  - filter/pipeline.py:166 - guard/intent 직렬 처리
  - tikitaka_service.py:529 - stream_interpretation() 메시지 생성 직렬
```

### 1.2 비동기 최적화 태스크

```yaml
┌─────────────────────────────────────────────────────────────┐
│                    비동기 최적화 로드맵                      │
├─────────────────────────────────────────────────────────────┤
│  P0: fortune_generator.py - 동양/서양 병렬 (50% ↓)          │
│  P1: saju_service.py - LLM 해석 병렬 (50% ↓)                │
│  P2: filter/pipeline.py - guard/intent 병렬 (50% ↓)         │
│  P3: tikitaka_service.py - 스트리밍 병렬 생성 (30% ↓)       │
│  ─────────────────────────────────────────────────────────  │
│  총 예상 효과: API 응답 시간 40-60% 감소                    │
└─────────────────────────────────────────────────────────────┘

P0 (즉시 개선 - 전체 운세 응답 속도 50% 향상):
  파일: services/fortune_generator.py
  함수: generate_full() (라인 744-748)

  현재 (직렬, 4초):
    # 동양 사주 생성
    eastern = await self.generate_eastern(birth_data)  # 2초
    # 서양 점성술 생성
    western = await self.generate_western(birth_data)  # 2초

  개선 (병렬, 2초):
    # 동양/서양 동시 실행
    eastern, western = await asyncio.gather(
        self.generate_eastern(birth_data),
        self.generate_western(birth_data),
    )

  예상 효과: 50% 성능 개선 (4초 → 2초)

P1 (핵심 개선 - LLM 해석 병렬화):
  파일: services/saju_service.py
  함수: _calculate_saju() 내부 (라인 254-267)

  현재 (직렬, 4초):
    eastern = await self._generate_eastern_interpretation(...)  # 1초
    western = await self._generate_western_interpretation(...)  # 1초
    combined = await self._generate_combined_opinion(...)       # 1초
    advice = await self._generate_advice(...)                   # 1초

  개선 (병렬, 2초):
    # Step 1: 동양/서양 동시 실행
    eastern_interpretation, western_interpretation = await asyncio.gather(
        self._generate_eastern_interpretation(four_pillars, element_balance, day_master),
        self._generate_western_interpretation(sun_sign),
    )

    # Step 2: 통합/조언 동시 실행 (의존성 완료 후)
    combined_opinion, advice = await asyncio.gather(
        self._generate_combined_opinion(
            eastern_interpretation, western_interpretation, day_master, sun_sign
        ),
        self._generate_advice(
            eastern_interpretation, western_interpretation, day_master, sun_sign
        ),
    )

  예상 효과: 50% 성능 개선 (4초 → 2초)

P2 (필터 파이프라인 병렬화):
  파일: services/filter/pipeline.py
  함수: filter() (라인 166-179)

  현재 (직렬, 200ms):
    guard_result = await self._run_guard(text)      # GPU 추론 100ms
    # 중간에 early return 로직
    intent_result = await self._run_intent(text)    # GPU 추론 100ms

  개선 (조건부 병렬, 100ms):
    # guard_mode가 "block"이 아닐 때 병렬 실행
    if self._guard_mode != "block":
        guard_result, intent_result = await asyncio.gather(
            self._run_guard(text),
            self._run_intent(text),
        )
    else:
        # 기존 로직 유지 (early return 필요)
        guard_result = await self._run_guard(text)
        if guard_result.is_malicious:
            return FilterResult(...)  # early return
        intent_result = await self._run_intent(text)

  예상 효과: 50% 성능 개선 (200ms → 100ms)

P3 (스트리밍 메시지 병렬 생성):
  파일: services/tikitaka_service.py
  함수: stream_interpretation() (라인 529, 569)

  현재 (직렬, 4초 초기 대기):
    # 소이설 생성 후 스트리밍
    soiseol_msg = await self.llm.generate_soiseol_message(...)  # 2초 대기
    for chunk in soiseol_msg:
        yield ...
    # 스텔라 생성 후 스트리밍
    stella_msg = await self.llm.generate_stella_message(...)    # 2초 대기
    for chunk in stella_msg:
        yield ...

  개선 (병렬 생성 후 순차 스트리밍, 2초 초기 대기):
    # 둘 다 먼저 병렬 생성
    soiseol_msg, stella_msg = await asyncio.gather(
        self.llm.generate_soiseol_message("기본 성격 분석", eastern_context),
        self.llm.generate_stella_message("기본 성격 분석", western_context),
    )

    # 노이즈 필터 적용
    soiseol_msg = filter_noise(soiseol_msg, aggressive=False)
    stella_msg = filter_noise(stella_msg, aggressive=False)

    # 스트리밍은 순차로 (UX 유지)
    yield {"event": "message_start", "data": {"character": "SOISEOL"}}
    for i in range(0, len(soiseol_msg), 20):
        yield {"event": "message_chunk", "data": {"content": soiseol_msg[i:i+20]}}
        await asyncio.sleep(0.05)
    yield {"event": "message_end", "data": {"content": soiseol_msg}}

    yield {"event": "message_start", "data": {"character": "STELLA"}}
    for i in range(0, len(stella_msg), 20):
        yield {"event": "message_chunk", "data": {"content": stella_msg[i:i+20]}}
        await asyncio.sleep(0.05)
    yield {"event": "message_end", "data": {"content": stella_msg}}

  예상 효과: 초기 응답 대기 시간 50% 감소 (4초 → 2초)
```

### 1.3 비동기 최적화 체크리스트

```yaml
P0 - fortune_generator.py:
  - [ ] generate_full() 동양/서양 asyncio.gather() 병렬화
  - [ ] 테스트 코드 작성 (test_fortune_generator_parallel.py)
  - [ ] 성능 측정 (before/after)

P1 - saju_service.py:
  - [ ] _generate_eastern_interpretation + _generate_western_interpretation 병렬화
  - [ ] _generate_combined_opinion + _generate_advice 병렬화
  - [ ] 테스트 코드 작성 (test_saju_service_parallel.py)
  - [ ] 성능 측정 (before/after)

P2 - filter/pipeline.py:
  - [ ] guard_mode 조건부 분기 추가
  - [ ] _run_guard + _run_intent asyncio.gather() 병렬화
  - [ ] 기존 early return 로직 유지 (block 모드)
  - [ ] 테스트 코드 작성

P3 - tikitaka_service.py:
  - [ ] stream_interpretation() 메시지 병렬 생성
  - [ ] 노이즈 필터 적용 유지
  - [ ] 스트리밍 순서 UX 유지
  - [ ] 테스트 코드 작성
```

---

## Part 2: 3턴 대화 생성 및 문서화

### 2.1 캐릭터 조합 매트릭스 (15개)

```yaml
메인 vs 메인 (1개):
  1. 소이설 vs 스텔라

메인 vs 서브 (8개):
  2. 소이설 vs 청운
  3. 소이설 vs 화린
  4. 소이설 vs 카일
  5. 소이설 vs 엘라리아
  6. 스텔라 vs 청운
  7. 스텔라 vs 화린
  8. 스텔라 vs 카일
  9. 스텔라 vs 엘라리아

서브 vs 서브 (6개):
  10. 청운 vs 화린
  11. 청운 vs 카일
  12. 청운 vs 엘라리아
  13. 화린 vs 카일
  14. 화린 vs 엘라리아
  15. 카일 vs 엘라리아
```

### 2.2 테스트 사용자 프로필 (3명)

```yaml
User1:
  name: "김민준"
  birth: "1992-03-15T08:30:00"
  gender: "M"
  solar: true
  saju_summary: "병화 일간, 식신격, 도화살 있음"
  astro_summary: "물고기자리, 금성 7하우스, 수성 역행"

User2:
  name: "이서연"
  birth: "1995-11-22T14:00:00"
  gender: "F"
  solar: true
  saju_summary: "임수 일간, 정인격, 편재 강함"
  astro_summary: "전갈자리, 목성 2하우스, 화성 상승"

User3:
  name: "박지호"
  birth: "1988-07-08T22:15:00"
  gender: "M"
  solar: true
  saju_summary: "갑목 일간, 비겁격, 정관 있음"
  astro_summary: "게자리, 토성 10하우스, 달 4하우스"
```

### 2.3 대화 주제 (5개)

```yaml
topics:
  - 연애운
  - 재물운
  - 직장운
  - 건강운
  - 올해_총운
```

### 2.4 3턴 대화 구조

```yaml
Turn 1:
  - 사용자: 질문
  - 캐릭터A: 첫 번째 해석
  - 캐릭터B: 반응 (동의/반박)

Turn 2:
  - 사용자: 후속 질문 또는 반응
  - 캐릭터A: 심화 해석
  - 캐릭터B: 추가 관점

Turn 3:
  - 사용자: 마무리 질문
  - 캐릭터A: 결론
  - 캐릭터B: 보완/마무리

대화 모드 비율:
  - 대결 (Battle): 70%
  - 합의 (Consensus): 30%
```

### 2.5 저장 구조

```
yeji-ai-server/ai/docs/tikitaka-samples/
├── README.md                           # 샘플 개요
├── main-vs-main/
│   └── soiseol-vs-stella/
│       ├── user1-연애운.md
│       ├── user2-재물운.md
│       └── user3-직장운.md
├── main-vs-sub/
│   ├── soiseol-vs-cheongwoon/
│   ├── soiseol-vs-hwarin/
│   ├── soiseol-vs-kyle/
│   ├── soiseol-vs-elaria/
│   ├── stella-vs-cheongwoon/
│   ├── stella-vs-hwarin/
│   ├── stella-vs-kyle/
│   └── stella-vs-elaria/
└── sub-vs-sub/
    ├── cheongwoon-vs-hwarin/
    ├── cheongwoon-vs-kyle/
    ├── cheongwoon-vs-elaria/
    ├── hwarin-vs-kyle/
    ├── hwarin-vs-elaria/
    └── kyle-vs-elaria/
```

### 2.6 대화 샘플 템플릿

```markdown
# {캐릭터A} vs {캐릭터B} - {주제}

## 사용자 정보
- 이름: {name}
- 생년월일: {birth}
- 성별: {gender}
- 사주 요약: {saju_summary}
- 별자리 요약: {astro_summary}

## 대화 모드
- [x] 대결 (Battle) / [ ] 합의 (Consensus)

---

## Turn 1

**사용자**: {user_message_1}

**{캐릭터A}**:
> {character_a_response_1}

**{캐릭터B}**:
> {character_b_response_1}

---

## Turn 2

**사용자**: {user_message_2}

**{캐릭터A}**:
> {character_a_response_2}

**{캐릭터B}**:
> {character_b_response_2}

---

## Turn 3

**사용자**: {user_message_3}

**{캐릭터A}**:
> {character_a_response_3}

**{캐릭터B}**:
> {character_b_response_3}

---

## 품질 평가
| 항목 | {캐릭터A} | {캐릭터B} |
|------|-----------|-----------|
| 페르소나 일치 | /30 | /30 |
| 톤 일관성 | /30 | /30 |
| 대화 자연스러움 | /30 | /30 |
| 금지표현 감점 | -0 | -0 |
| **총점** | /90 | /90 |

## 개선 필요 사항
-
```

---

## Part 3: API 문서 업데이트

### 3.1 API 문서 위치

```yaml
기존 문서:
  - yeji-ai-server/docs/api/API_USAGE_GUIDE.md

추가할 섹션:
  - 서브 캐릭터 테스트 엔드포인트
  - 티키타카 API 응답 스키마
  - 캐릭터 목록 API
  - 예시 요청/응답
```

### 3.2 추가할 엔드포인트 문서

```yaml
POST /v1/fortune/chat/sub-character:
  description: 서브 캐릭터 테스트 엔드포인트
  request:
    session_id: str | null
    birth_date: str
    birth_time: str | null
    character_a: CharacterCode
    character_b: CharacterCode
    topic: str
  response:
    session_id: str
    messages: list[ChatMessage]

GET /v1/fortune/characters:
  description: 사용 가능한 캐릭터 목록
  response:
    characters: list[CharacterInfo]
```

---

## Part 4: Git 커밋 히스토리 정리

### 4.1 커밋 컨벤션 (CLAUDE.md 기준)

```yaml
형식: "type: [Scope] 설명 (closes #이슈)"

Type:
  - feat: 새 기능
  - fix: 버그 수정
  - docs: 문서 변경
  - chore: 빌드, 설정 등
  - refactor: 리팩터링
  - test: 테스트
  - perf: 성능 개선

Scope:
  - [Backend]: 백엔드
  - [Frontend]: 프론트엔드
  - [AI]: AI 서버
  - [Infra]: 인프라

예시:
  ✅ "feat: [AI] 티키타카 대화 생성기 구현"
  ✅ "perf: [AI] saju_service 비동기 병렬화"
  ✅ "fix: [AI] JSON 파싱 오류 수정"
  ❌ "update code" (컨벤션 미준수)
  ❌ "Claude로 수정" (Claude 언급 금지)
```

### 4.2 Git 정리 Phase

```yaml
Phase 1 - 분석:
  - [ ] ai/main 브랜치 커밋 히스토리 분석
  - [ ] ai/develop 브랜치 커밋 히스토리 분석
  - [ ] 컨벤션 미준수 커밋 목록화
  - [ ] Claude 관련 커밋 목록화

Phase 2 - 계획:
  - [ ] 정리 범위 결정 (어디서부터 어디까지)
  - [ ] squash 대상 커밋 선정
  - [ ] 새 커밋 메시지 작성

Phase 3 - 실행:
  - [ ] git rebase -i로 커밋 정리
  - [ ] 커밋 메시지 수정 (컨벤션 준수)
  - [ ] Claude 관련 내용 제거
  - [ ] force push (ai/develop 먼저, ai/main 나중)

Phase 4 - 검증:
  - [ ] 커밋 히스토리 검토
  - [ ] CI/CD 파이프라인 확인
  - [ ] 배포 정상 동작 확인
```

### 4.3 Git 명령어

```bash
# 1. 분석: 최근 20개 커밋 확인
git log --oneline -20 ai/develop

# 2. 컨벤션 미준수 커밋 검색
git log --oneline | grep -v -E "^[a-f0-9]+ (feat|fix|docs|chore|refactor|test|perf):"

# 3. Claude 관련 커밋 검색
git log --oneline | grep -i "claude"

# 4. rebase로 정리 (예: 최근 10개 커밋)
git checkout ai/develop
git rebase -i HEAD~10

# 5. force push
git push origin ai/develop --force-with-lease
```

---

## Part 5: PDCA 사이클 실행

### 5.1 Phase 1 - Plan (계획)

```yaml
태스크 분해:
  Wave 1 (비동기 최적화 - P0~P3):
    Step 1: P0 fortune_generator.py
      - generate_full() 병렬화
      - 테스트 작성 및 검증
    Step 2: P1 saju_service.py
      - _calculate_saju() 병렬화
      - 테스트 작성 및 검증
    Step 3: P2 filter/pipeline.py
      - filter() 조건부 병렬화
      - 테스트 작성 및 검증
    Step 4: P3 tikitaka_service.py
      - stream_interpretation() 병렬 생성
      - 테스트 작성 및 검증
    Step 5: 성능 측정
      - before/after 비교
      - 문서화 (docs/pdca/async-optimization/)

  Wave 2 (대화 샘플 생성):
    - 폴더 구조 생성
    - 메인 vs 메인 샘플 3개
    - 메인 vs 서브 샘플 24개
    - 서브 vs 서브 샘플 18개

  Wave 3 (문서화):
    - API 문서 업데이트
    - 품질 평가 문서화
    - 비동기 패턴 문서화

  Wave 4 (Git 정리):
    - 커밋 히스토리 분석
    - rebase 실행
    - force push
```

### 5.2 Phase 2 - Do (실행)

```yaml
실행 순서:
  1. 비동기 최적화 (코드 변경)
  2. 로컬 테스트 (pytest)
  3. 대화 샘플 생성 (문서)
  4. API 문서 업데이트
  5. ai/develop 배포
  6. E2E 테스트
  7. Git 히스토리 정리
```

### 5.3 Phase 3 - Check (검증)

```yaml
품질 기준:
  비동기 최적화:
    - 테스트 커버리지 80% 이상
    - 성능 개선 20% 이상

  대화 샘플:
    - 45개 샘플 생성 완료
    - 모든 캐릭터 품질 80점 이상
    - 금지 표현 0개

  API 문서:
    - 모든 엔드포인트 문서화
    - 예시 요청/응답 포함

  Git:
    - 컨벤션 100% 준수
    - Claude 언급 0개
```

### 5.4 Phase 4 - Act (개선)

```yaml
품질 미달 시:
  1. 실패 원인 분석 (docs/pdca/[feature]/check.md)
  2. 리서치 (2026년 기준 최신 기법)
  3. 프롬프트/코드 수정
  4. 재테스트
  5. Phase 3로 돌아가기

품질 통과 시:
  1. ai/main 배포
  2. 프로덕션 E2E 테스트
  3. 최종 문서화 (docs/patterns/)
  4. PDCA 문서 정리
```

---

## 기술 체크리스트

```yaml
Python 호환성:
  - [ ] Python 3.11+ 문법 사용
  - [ ] Optional 대신 X | None
  - [ ] List/Dict 대신 list/dict
  - [ ] Pydantic v2 패턴 (.model_dump())

비동기 패턴:
  - [ ] asyncio.gather() 병렬 처리
  - [ ] asyncio.to_thread() CPU 바운드
  - [ ] AsyncGenerator 스트리밍

Qwen3 프롬프트:
  - [ ] /no_think 모드 적용
  - [ ] Few-shot 예시 30개 이상
  - [ ] 최종 점검 섹션 포함

커밋 컨벤션:
  - [ ] type: [Scope] 설명 형식
  - [ ] Claude 언급 없음
  - [ ] 이슈 번호 연결 (있는 경우)

테스트:
  - [ ] pytest 경로 직접 지정
  - [ ] AAA 패턴 (Arrange, Act, Assert)
  - [ ] 모킹 (AsyncMock, patch)
```

---

## 산출물 요약

| 카테고리 | 파일/폴더 | 설명 | 예상 효과 |
|----------|-----------|------|----------|
| P0 비동기 | `services/fortune_generator.py` | generate_full() 병렬화 | 50% 속도 향상 |
| P1 비동기 | `services/saju_service.py` | _calculate_saju() 병렬화 | 50% 속도 향상 |
| P2 비동기 | `services/filter/pipeline.py` | filter() 조건부 병렬화 | 50% 속도 향상 |
| P3 비동기 | `services/tikitaka_service.py` | stream_interpretation() 병렬 생성 | 30% 초기 응답 향상 |
| 테스트 | `tests/test_async_parallel.py` | 병렬화 테스트 코드 | - |
| 대화 샘플 | `docs/tikitaka-samples/` | 45개 대화 문서 | - |
| API 문서 | `docs/api/API_USAGE_GUIDE.md` | 서브 캐릭터 API 추가 | - |
| PDCA 문서 | `docs/pdca/async-optimization/` | 비동기 최적화 기록 | - |
| 패턴 문서 | `docs/patterns/async-optimization.md` | 비동기 패턴 | - |
| Git 정리 | - | ai/main, ai/develop 커밋 정리 | - |

---

## 성공 기준

```yaml
비동기 최적화 (P0~P3):
  - [ ] P0: fortune_generator.py 테스트 통과, 50% 이상 속도 개선
  - [ ] P1: saju_service.py 테스트 통과, 50% 이상 속도 개선
  - [ ] P2: filter/pipeline.py 테스트 통과, 기존 로직 유지
  - [ ] P3: tikitaka_service.py 테스트 통과, 초기 응답 30% 이상 개선
  - [ ] 전체 API 응답 시간 40% 이상 감소

품질 검증:
  - [ ] 45개 대화 샘플 생성 완료
  - [ ] 모든 캐릭터 품질 80점 이상
  - [ ] API 문서 업데이트 완료

배포:
  - [ ] ai/develop E2E 테스트 통과
  - [ ] ai/main 프로덕션 배포 완료

Git:
  - [ ] Git 커밋 컨벤션 100% 준수
  - [ ] Claude 관련 커밋 0개

반복 제한:
  - 프롬프트 개선: 최대 5회
  - 전체 사이클: 최대 3회
  - 초과 시 수동 개입 요청
```

---

## 참조 문서

| 문서 | 경로 | 설명 |
|------|------|------|
| CLAUDE.md | `C:/Users/SSAFY/CLAUDE.md` | 프로젝트 전체 지침 |
| Python 컨벤션 | `ai/docs/PYTHON_CONVENTIONS.md` | 코딩 스타일 가이드 |
| Qwen3 프롬프팅 | `ai/docs/guides/qwen3-prompting-guide.md` | LLM 프롬프트 작성법 |
| 캐릭터 품질 패턴 | `ai/docs/patterns/character-speech-quality.md` | 말투 품질 관리 |
| PDCA 서브캐릭터 | `ai/docs/pdca/sub-characters/` | 서브캐릭터 PDCA 기록 |

---

> **작성일**: 2026-01-31
> **버전**: 1.0
> **작성자**: YEJI AI 팀
