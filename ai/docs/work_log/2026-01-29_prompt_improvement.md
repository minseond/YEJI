# 작업 로그: LLM 프롬프트 개선

> **날짜**: 2026-01-29
> **작업자**: Claude Code (PM Agent)
> **브랜치**: feat/structured-output

---

## 1. 작업 개요

### 배경
v7 모델(`tellang/yeji-8b-rslora-v7-AWQ`)의 출력이 Pydantic 스키마와 불일치하는 문제 발견.

### 목표
프롬프트 개선을 통해 LLM 출력의 스키마 준수율 향상.

---

## 2. 변경 파일

### 2.1 프롬프트 파일
**파일**: `ai/src/yeji_ai/prompts/fortune_prompts.py`

**변경 내용**:
- EAST/WEST 프롬프트에 Few-shot 예시(`<example>` 태그) 추가
- 제약 조건 강화 (배열 vs 객체 구조 명확화)
- 금지 사항 명시 ("position 필드 사용 금지", "한자 코드 사용 금지")

### 2.2 테스트 스크립트
**파일**: `tests/prompts/test_via_ssh.py`

**변경 내용**:
- stop 토큰 추가: `["\n\nuser", "\nassistant", "<|im_end|>", ...]`
- `extract_first_json()` 함수 추가 (첫 번째 완전한 JSON만 추출)
- `validate_east_response()`, `validate_west_response()` 함수 추가

### 2.3 분석 문서
**파일**: `docs/analysis/LLM_OUTPUT_QUALITY_ANALYSIS.md`

**변경 내용**:
- 섹션 9 추가: "프롬프트 개선 후 재테스트 결과"
- 개선된 부분 / 미해결 이슈 정리
- 권장 대응 방안 추가

---

## 3. 테스트 결과

### 3.1 EAST (동양 사주) 개선 결과

| 이슈 | 개선 전 | 개선 후 | 상태 |
|------|---------|---------|------|
| chart 구조 | position 배열 | year/month/day/hour 객체 | ✅ 해결 |
| ten_gods 코드 | 한자 (丙, 戊) | 영문 (JEONG_JAE, PYEON_JAE) | ✅ 해결 |
| final_verdict | 누락 | 4개 필드 모두 포함 | ✅ 해결 |
| five_elements | 객체 형태 | list 배열 형태 | ✅ 해결 |

### 3.2 WEST (서양 점성술) 개선 결과

| 이슈 | 개선 전 | 개선 후 | 상태 |
|------|---------|---------|------|
| element_4_distribution | 객체 형태 | 배열 형태 | ✅ 해결 |
| modality 코드 | fixed, flexible | CARDINAL, FIXED, MUTABLE | ✅ 해결 |
| keywords | name 필드, 한글 값 | code 필드, 영문 코드 | ✅ 해결 |
| detailed_analysis | 문자열 배열 | {title, content} 객체 | ✅ 해결 |
| overview/advice | 누락 | 포함됨 | ✅ 해결 |

### 3.3 미해결 이슈 (모델 한계)

| 이슈 | 설명 | 대응 방안 |
|------|------|-----------|
| 응답 반복 | JSON 후 대화 시뮬레이션 | JSON 후처리 |
| 다국어 쓰레기 | 태국어, 아랍어 출현 | 정규식 필터링 |
| stop 토큰 미인식 | 반복 패턴 발생 | 모델 재학습 필요 |

---

## 4. 결론

Few-shot 예시 추가로 **스키마 준수율 크게 개선**:
- EAST: 7개 이슈 중 4개 해결 (57%)
- WEST: 5개 이슈 중 5개 해결 (100%)

남은 문제는 **모델 자체의 한계**로, JSON 후처리 로직으로 대응하거나 모델 재학습 필요.

---

## 5. 다음 단계

1. [x] 프롬프트 개선
2. [x] 테스트 스크립트 개선
3. [x] 분석 문서 업데이트
4. [ ] JSON 후처리 로직 서비스에 적용
5. [ ] 모델 재학습 검토 (v8)

---

## 변경 이력

| 날짜 | 작업 내용 |
|------|----------|
| 2026-01-29 | 초기 작성 - 프롬프트 개선 작업 완료 |
