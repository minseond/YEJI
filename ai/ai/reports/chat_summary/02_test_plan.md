# Task 3: 검증 규칙/테스트 설계

## 테스트 파일

`tests/test_chat_summary_contract.py`

---

## 테스트 케이스 표

### 정상 케이스 (3개)

| ID | 테스트명 | 설명 | 기대 결과 |
|----|----------|------|----------|
| V1 | `test_valid_eastern_summary` | 동양 운세 요약 (금전운) | ✅ 검증 통과 |
| V2 | `test_valid_western_summary` | 서양 운세 요약 (연애운) | ✅ 검증 통과 |
| V3 | `test_valid_total_summary` | 종합 운세 요약 | ✅ 검증 통과 |

### 경계 케이스 (6개)

| ID | 테스트명 | 설명 | 기대 결과 |
|----|----------|------|----------|
| B1 | `test_boundary_min_keywords` | 키워드 최소 2개 | ✅ 검증 통과 |
| B2 | `test_boundary_max_keywords` | 키워드 최대 5개 | ✅ 검증 통과 |
| B3 | `test_boundary_score_zero` | 점수 0점 | ✅ 검증 통과 |
| B4 | `test_boundary_score_hundred` | 점수 100점 | ✅ 검증 통과 |
| B5 | `test_boundary_min_one_line_length` | one_line 최소 10자 | ✅ 검증 통과 |
| B6 | `test_boundary_min_detail_length` | detail 최소 50자 | ✅ 검증 통과 |

### 실패 케이스 (9개)

| ID | 테스트명 | 설명 | 기대 결과 |
|----|----------|------|----------|
| F1 | `test_fail_missing_fortune_type` | fortune_type 누락 | ❌ ValidationError |
| F2 | `test_fail_invalid_fortune_type` | 잘못된 fortune_type | ❌ ValidationError |
| F3 | `test_fail_invalid_character` | 잘못된 character | ❌ ValidationError |
| F4 | `test_fail_score_out_of_range` | 점수 150점 | ❌ ValidationError |
| F5 | `test_fail_too_few_keywords` | 키워드 1개 | ❌ ValidationError |
| F6 | `test_fail_too_many_keywords` | 키워드 6개 | ❌ ValidationError |
| F7 | `test_fail_empty_one_line` | 빈 one_line | ❌ ValidationError |
| F8 | `test_fail_short_detail` | detail 50자 미만 | ❌ ValidationError |
| F9 | `test_fail_invalid_category` | 잘못된 category | ❌ ValidationError |

### 직렬화 테스트 (2개)

| ID | 테스트명 | 설명 | 기대 결과 |
|----|----------|------|----------|
| S1 | `test_model_dump` | dict 변환 | ✅ 필드 일치 |
| S2 | `test_model_dump_json` | JSON 변환 | ✅ 필드 포함 |

---

## 검증 규칙 요약

### FortuneSummaryResponse

| 필드 | 타입 | 규칙 |
|------|------|------|
| `session_id` | str | 필수 |
| `category` | Literal | "total", "love", "wealth", "career", "health" |
| `fortune_type` | Literal | "eastern", "western" |
| `fortune` | FortuneSummary | 필수 |

### FortuneSummary

| 필드 | 타입 | 규칙 |
|------|------|------|
| `character` | Literal | "SOISEOL", "STELLA" |
| `score` | int | 0 ≤ x ≤ 100 |
| `one_line` | str | 10 ≤ len ≤ 100 |
| `keywords` | list[str] | 2 ≤ len ≤ 5 |
| `detail` | str | 50 ≤ len ≤ 500 |

---

## 실행 명령

```bash
# 전체 실행
pytest tests/test_chat_summary_contract.py -v

# 특정 클래스만
pytest tests/test_chat_summary_contract.py::TestValidCases -v
pytest tests/test_chat_summary_contract.py::TestBoundaryCases -v
pytest tests/test_chat_summary_contract.py::TestFailureCases -v
```

---

## Acceptance Criteria

- [x] 테스트 파일 생성: `tests/test_chat_summary_contract.py`
- [x] 정상 케이스 3개
- [x] 경계 케이스 6개
- [x] 실패 케이스 9개
- [ ] 로컬 테스트 실행 (모델 구현 후)
