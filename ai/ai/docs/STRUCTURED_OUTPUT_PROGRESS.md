# yeji-ai-server 구조화된 출력 (Structured Output) 진행사항

> 작성일: 2026-01-28
> 상태: 진행 중 (스키마 확정 대기)

---

## 1. 목표

vLLM + Qwen3 모델을 활용하여 `api_enum_spec.json` 스키마에 맞는 JSON 응답을 생성.

### 대상 API
- **동양 사주**: `EasternFortuneResponse`
- **서양 점성술**: `WesternFortuneResponse`

---

## 2. 현재 환경

| 항목 | 값 |
|------|-----|
| vLLM 서버 | AWS GPU (3.36.89.31:8001) |
| 모델 | `tellang/yeji-8b-rslora-v7-AWQ` |
| 최대 컨텍스트 | 4096 tokens |
| 구조화 방식 | `response_format: {"type": "json_object"}` |

### 연결 방법
```bash
# SSH 터널
ssh -L 8001:localhost:8001 -i yeji-gpu-key.pem ubuntu@3.36.89.31
```

---

## 3. 구현 완료 사항

### 3.1 Pydantic 스키마 (`llm_schemas.py`)

`api_enum_spec.json` 기반으로 Python 스키마 정의 완료:

```
src/yeji_ai/models/llm_schemas.py
├── Enum 타입
│   ├── ElementCode (WOOD/FIRE/EARTH/METAL/WATER)
│   ├── CheonGanCode (GAP/EUL/BYEONG/...)
│   ├── JiJiCode (JA/CHUK/IN/...)
│   ├── TenGodCode (DAY_MASTER/BI_GYEON/...)
│   ├── ZodiacCode (ARIES/TAURUS/...)
│   ├── PlanetCode (SUN/MOON/...)
│   └── ...
├── 동양 사주
│   ├── Pillar (gan, gan_code, ji, ji_code, element_code, ten_god_code)
│   ├── EasternChart
│   ├── FiveElements, YinYang, TenGods
│   ├── EasternStats
│   ├── EasternUIHints, EasternLucky
│   └── EasternFortuneResponse (최종)
└── 서양 점성술
    ├── BigThree, PlanetPlacement
    ├── WesternChart
    ├── WesternElements, WesternModality, WesternAspects
    ├── WesternStats
    ├── WesternUIHints, WesternLucky
    └── WesternFortuneResponse (최종)
```

### 3.2 LLM 호출 테스트

| 테스트 | 결과 |
|--------|------|
| vLLM 헬스체크 | ✅ 정상 |
| `response_format: json_object` | ✅ 동작 |
| 동양 사주 예시 생성 | ⚠️ 부분 성공 (구조 오류 일부) |
| 서양 점성술 예시 생성 | ✅ 대부분 성공 |

### 3.3 생성된 예시 파일

```
docs/examples/
├── eastern_water_strong_v2.json  # ✅ 동양 - 가장 완성도 높음
├── eastern_2_fire.json           # ⚠️ 구조 일부 오류
├── eastern_3_water.json          # ⚠️ 영어 응답, category 오류
├── western_1_fire.json           # ✅ 서양 - 스키마 잘 따름
├── western_2_water.json          # ✅ 서양 - 스키마 잘 따름
└── western_3_air.json            # ✅ 서양 - 스키마 잘 따름
```

---

## 4. 발견된 문제점

### 4.1 모델 컨텍스트 제한
- 4096 토큰 제한으로 긴 프롬프트 + 긴 출력 불가
- 프롬프트에 완전한 예시 포함 시 출력 잘림

### 4.2 스키마 준수율
- 서양 점성술: ~90% 준수
- 동양 사주: ~70% 준수
- 일부 필드명 오타 (`ten_god1`, `signcode` 등)
- `category` 값 혼동 (`eastern` ↔ `western`)

### 4.3 언어 문제
- 일부 응답이 영어로 나옴
- 프롬프트에 한국어 강제 지시 필요

---

## 5. 프롬프트 가이드 (Qwen3)

`QWEN3_PROMPTING_GUIDE.md` 기반:

```python
# 시스템 프롬프트 시작
"/no_think\n..."

# XML 태그 사용
"<constraints>...</constraints>"

# 권장 파라미터
{
    "temperature": 0.5~0.7,
    "top_p": 0.8,
    "top_k": 20,
    "presence_penalty": 1.5,  # AWQ 모델용
    "response_format": {"type": "json_object"}
}
```

---

## 6. 다음 단계 (TODO)

### 스키마 확정 후
- [ ] 프론트엔드팀과 최종 스키마 확정
- [ ] `llm_schemas.py` 업데이트
- [ ] 프롬프트 템플릿 최적화

### LLM 호출 개선
- [ ] `llm_interpreter.py`에 `interpret_eastern_full()` 구현
- [ ] `llm_interpreter.py`에 `interpret_western_full()` 구현
- [ ] Pydantic 검증 후 자동 수정 로직 추가

### 인프라 개선 (선택)
- [ ] 모델 컨텍스트 8192+ 버전 배포
- [ ] 프롬프트 압축 또는 2단계 생성 고려

---

## 7. 관련 파일

| 파일 | 설명 |
|------|------|
| `src/yeji_ai/models/llm_schemas.py` | Pydantic 스키마 정의 |
| `src/yeji_ai/services/llm_interpreter.py` | LLM 호출 서비스 |
| `src/yeji_ai/clients/vllm_client.py` | vLLM API 클라이언트 |
| `docs/specs/api_enum_spec.json` | API Enum/스키마 명세 |
| `docs/examples/*.json` | 생성된 예시 파일 |
| `scripts/generate_final.py` | 예시 생성 스크립트 |

---

## 8. 참고: EasternFortuneResponse 구조

```json
{
  "category": "eastern",
  "chart": {
    "summary": "...",
    "year": { "gan": "甲", "gan_code": "GAP", "ji": "子", "ji_code": "JA", "element_code": "WOOD", "ten_god_code": "..." },
    "month": { ... },
    "day": { ... },
    "hour": { ... }
  },
  "stats": {
    "five_elements": {
      "summary": "...",
      "elements": [{ "code": "WOOD", "label": "목", "value": 3, "percent": 37.5 }, ...],
      "strong": "WOOD",
      "weak": "WATER"
    },
    "yin_yang": { "summary": "...", "yin": 55, "yang": 45, "balance": "SLIGHT_YIN" },
    "ten_gods": {
      "summary": "...",
      "gods": [{ "code": "BI_GYEON", "label": "비견", "group_code": "BI_GYEOP", "value": 2, "percent": 33 }],
      "dominant": "BI_GYEOP"
    },
    "strength": "...",
    "weakness": "..."
  },
  "summary": "...",
  "message": "...",
  "ui_hints": {
    "badges": ["WOOD_STRONG", "WATER_WEAK", ...],
    "recommend_chart": "PIE",
    "highlight": { "day_master": "day", "strong_element": "WOOD", "weak_element": "WATER" }
  },
  "lucky": {
    "color": "군청색",
    "color_code": "#191970",
    "number": "1, 6",
    "item": "수정",
    "direction": "북쪽",
    "direction_code": "N",
    "place": "물가"
  }
}
```

---

## 9. 참고: WesternFortuneResponse 구조

```json
{
  "category": "western",
  "chart": {
    "summary": "...",
    "sun": { "sign_code": "ARIES", "house_number": 1, "summary": "..." },
    "moon": { "sign_code": "LEO", "house_number": 5, "summary": "..." },
    "rising": { "sign_code": "CANCER", "house_number": 1, "summary": "..." },
    "planets": [{ "planet_code": "SUN", "sign_code": "ARIES", "house_number": 1, "degree": 15, "minute": 30, "is_retrograde": false }]
  },
  "stats": {
    "elements": {
      "summary": "...",
      "distribution": [{ "code": "FIRE", "label": "불", "value": 4, "percent": 40 }],
      "dominant": "FIRE"
    },
    "modality": {
      "summary": "...",
      "distribution": [{ "code": "CARDINAL", "label": "활동", "value": 4, "percent": 40 }],
      "dominant": "CARDINAL"
    },
    "aspects": {
      "summary": "...",
      "major_aspects": [{ "planet1": "SUN", "planet2": "MOON", "aspect_code": "TRINE", "nature": "HARMONIOUS", "orb": 2 }]
    },
    "strength": "...",
    "weakness": "..."
  },
  "summary": "...",
  "message": "...",
  "ui_hints": {
    "badges": ["FIRE_DOMINANT", "MARS_STRONG"],
    "recommend_chart": "WHEEL",
    "highlight": { "sun_sign": "ARIES", "moon_sign": "LEO", "rising_sign": "CANCER", "dominant_planet": "MARS" }
  },
  "lucky": {
    "day": "화요일",
    "day_code": "TUE",
    "color": "빨간색",
    "color_code": "#FF0000",
    "number": "9",
    "stone": "루비",
    "planet": "MARS"
  }
}
```

---

*이 문서는 스키마 확정 후 업데이트 예정*
