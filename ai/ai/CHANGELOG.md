# Changelog

YEJI AI Server 변경 이력입니다.
[Keep a Changelog](https://keepachangelog.com/ko/1.0.0/) 형식을 따릅니다.

## [0.3.0] - 2026-01-31

### Fixed

#### P0 (Critical)
- **Western 별자리 계산 오류 수정**
  - 서버에서 별자리 계산 후 프롬프트에 전달하도록 변경
  - LLM이 직접 계산하던 방식에서 서버 계산 결과 사용 방식으로 개선

- **Eastern 일간 편향 수정**
  - 만세력 기반 사주 계산 후 프롬프트에 전달하도록 변경
  - 예시 일간 甲 고정 문제 해결 → 실제 계산된 일간 사용

- **Western keywords 검증 실패 수정**
  - 최소 3개 keywords 보장 로직 추가
  - 프롬프트 지시 강화 및 후처리기 기본값 보충

#### P1
- **Western summary 영문 코드 제거**
  - "(AIR)", "(FIXED)" 등 괄호 안 영문 코드가 summary에 포함되는 문제 수정

- **티키타카 빈 응답 폴백**
  - LLM 빈 응답 시 폴백 메시지 생성 로직 추가 (4곳)

## [0.2.0] - 2025-01-31

### Added
- LLM 응답 품질 개선 시스템
  - 빈 괄호/한자 필터 (`bracket_fixer.py`)
  - 불완전 문장 재생성 로직 (`sentence_completer.py`)
  - 프롬프트 누출 필터 (`prompt_leak_filter.py`)
  - 문자 깨짐 후처리 필터 (`encoding_fixer.py`)
- 폴백 템플릿 데이터 시스템
  - 동양 사주 템플릿 (150개 조합)
  - 서양 점성술 템플릿 (144개 조합)
  - LRU 캐시 기반 로더
- 사전 캐싱 시스템 설계
  - `CacheKeyBuilder` 클래스
  - 동양/서양 캐시 조회 함수
- vLLM guided decoding 지원
- Western keywords label 필드 보강

### Changed
- 후처리기 모듈 분리 (`services/postprocessor/`)
- max_tokens 증가 및 프롬프트 강화

### Fixed
- pyproject.toml JSON 데이터 파일 패키지 포함 설정
- 누락된 data 패키지 파일 추가

## [0.1.0] - 2025-01-25

### Added
- 초기 버전
- 동양 사주 분석 API (`/v1/fortune/eastern`)
- 서양 점성술 분석 API (`/v1/fortune/western`)
- 티키타카 대화 API (`/v1/fortune/chat`)
- vLLM Provider 연동
- 프롬프트 누출 방지 3중 방어
- Swagger UI 프로덕션 공개
