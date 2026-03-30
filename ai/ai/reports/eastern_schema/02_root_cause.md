# Task 2: 원인 판정 (프롬프트 vs 후처리)

## 결론

**판정: A) LLM이 원본 응답에서 필드를 아예 생성하지 않는다 (Prompt/Contract 문제)**

## 근거

### 1. LLM 원본 응답 분석

LLM이 생성한 chart.year 객체:
```json
{"gan": "乙", "ji": "寅", "element_code": "WOOD"}
```

필수 스키마 (user_fortune.py의 Pillar):
```python
class Pillar(BaseModel):
    gan: str            # ✅ LLM 생성
    gan_code: CheonGanCode  # ❌ LLM 미생성
    ji: str             # ✅ LLM 생성
    ji_code: JiJiCode       # ❌ LLM 미생성
    element_code: ElementCode  # ✅ LLM 생성
    ten_god_code: TenGodCode   # ❌ LLM 미생성
```

### 2. 후처리기 분석

`EasternPostprocessor`의 현재 로직:
1. `_convert_structures`: 오행/십신 객체→배열 변환
2. `_normalize_codes`: 대소문자/유사어 정규화
3. `_normalize_pillars`: element_code만 정규화
4. `_sync_cheongan_jiji`: cheongan_jiji 필드 동기화
5. `_fill_defaults`: 텍스트 기본값 채우기

**→ 누락 필드(gan_code, ji_code, ten_god_code) 생성 로직 없음**

### 3. 책임 구분

| 레이어 | 역할 | 현재 상태 |
|--------|------|-----------|
| LLM 프롬프트 | 필수 필드 명시 | 불완전 (코드 필드 누락) |
| 후처리기 | 필드 보정/폴백 | 미구현 |
| Pydantic | 검증 | 정상 동작 (엄격 검증) |

## 데이터 흐름

```
LLM 응답 (gan, ji만 생성)
    ↓
후처리기 (코드 필드 생성 로직 없음)
    ↓
Pydantic 검증 (gan_code, ji_code, ten_god_code 누락 → 실패)
```

## 해결 방향

### 1차 방어 (필수): 후처리기 보강
- gan → gan_code 매핑 생성
- ji → ji_code 매핑 생성
- gan + element_code → ten_god_code 계산/매핑

### 2차 방어 (선택): 프롬프트 강화
- Output Contract에 필수 필드 명시
- LLM이 직접 코드 필드를 생성하도록 유도

## 매핑 테이블 설계

### 천간 매핑 (gan → gan_code)
```python
GAN_TO_CODE = {
    "甲": "GAP",
    "乙": "EUL",
    "丙": "BYEONG",
    "丁": "JEONG",
    "戊": "MU",
    "己": "GI",
    "庚": "GYEONG",
    "辛": "SIN",
    "壬": "IM",
    "癸": "GYE",
}
```

### 지지 매핑 (ji → ji_code)
```python
JI_TO_CODE = {
    "子": "JA",
    "丑": "CHUK",
    "寅": "IN",
    "卯": "MYO",
    "辰": "JIN",
    "巳": "SA",
    "午": "O",
    "未": "MI",
    "申": "SHIN",
    "酉": "YU",
    "戌": "SUL",
    "亥": "HAE",
}
```

### 십신 매핑 (결정론적 계산 필요)
십신은 일간(day.gan)과 각 기둥의 간지 관계로 계산됩니다.
후처리기에서 일간 기준으로 계산하거나, 기본값으로 폴백할 수 있습니다.

## 결론

**후처리기 보강이 1차 안전장치**로 필요합니다.
LLM은 언제든 필드를 누락할 수 있으므로, 결정론적 매핑으로 방어해야 합니다.
