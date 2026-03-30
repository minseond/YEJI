# Task 1: 실패 재현 및 증거 수집

## 재현 정보

### 엔드포인트
```
POST https://i14a605.p.ssafy.io/ai/api/v1/fortune/eastern
```

### 요청 페이로드
```json
{
  "birth_date": "1990-05-15",
  "birth_time": "14:30",
  "gender": "M",
  "name": "테스트"
}
```

### 커맨드
```bash
curl -X POST "https://i14a605.p.ssafy.io/ai/api/v1/fortune/eastern" \
  -H "Content-Type: application/json" \
  -d '{
    "birth_date": "1990-05-15",
    "birth_time": "14:30",
    "gender": "M",
    "name": "테스트"
  }'
```

## 에러 응답

### HTTP 상태
```
200 OK (응답 자체는 성공하지만 error 필드 포함)
```

### 에러 유형
```
LLM_VALIDATION_FAILED
```

### Pydantic Validation Error 원문
```
12 validation errors for SajuDataV2
chart.year.gan_code
  Field required [type=missing, input_value={'gan': '乙', 'ji': '寅'...}, input_type=dict]
chart.year.ji_code
  Field required [type=missing]
chart.year.ten_god_code
  Field required [type=missing]
chart.month.gan_code
  Field required [type=missing]
chart.month.ji_code
  Field required [type=missing]
chart.month.ten_god_code
  Field required [type=missing]
chart.day.gan_code
  Field required [type=missing]
chart.day.ji_code
  Field required [type=missing]
chart.day.ten_god_code
  Field required [type=missing]
chart.hour.gan_code
  Field required [type=missing]
chart.hour.ji_code
  Field required [type=missing]
chart.hour.ten_god_code
  Field required [type=missing]
```

## 누락 필드 분석

### 필수 필드 (Pillar 스키마)
| 필드 | 타입 | 설명 | LLM 생성 여부 |
|------|------|------|---------------|
| gan | str | 천간 한자 | ✅ 생성됨 |
| gan_code | CheonGanCode | 천간 코드 | ❌ 누락 |
| ji | str | 지지 한자 | ✅ 생성됨 |
| ji_code | JiJiCode | 지지 코드 | ❌ 누락 |
| element_code | ElementCode | 오행 코드 | ✅ 생성됨 |
| ten_god_code | TenGodCode | 십신 코드 | ❌ 누락 |

### 영향 받는 기둥
- year (연주)
- month (월주)
- day (일주)
- hour (시주)

총 **12개 누락 필드** (4 기둥 × 3 필드)

## 결론

**원인 위치**: LLM 원본 응답

LLM은 `gan`, `ji`, `element_code` 필드만 생성하고 `gan_code`, `ji_code`, `ten_god_code`는 생성하지 않습니다.
후처리기(EasternPostprocessor)에 이 필드들을 생성하는 로직이 없어 Pydantic 검증에서 실패합니다.

## 후속 조치

1. 후처리기에 필드 생성 로직 추가 (권장)
2. LLM 프롬프트에 필수 필드 명시 (보조)
