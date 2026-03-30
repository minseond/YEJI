# Task 3: 수정안 설계 (2안 비교)

## Option A: Prompt 강화

### 설명
LLM 프롬프트에 필수 필드를 명시하여 LLM이 직접 코드 필드를 생성하도록 유도합니다.

### 구현 방법
```
Output Contract에 추가:
- chart의 각 pillar(year/month/day/hour)는 반드시 다음 필드를 포함해야 합니다:
  - gan: 천간 한자 (甲乙丙丁戊己庚辛壬癸 중 하나)
  - gan_code: 천간 코드 (GAP/EUL/BYEONG/JEONG/MU/GI/GYEONG/SIN/IM/GYE)
  - ji: 지지 한자 (子丑寅卯辰巳午未申酉戌亥 중 하나)
  - ji_code: 지지 코드 (JA/CHUK/IN/MYO/JIN/SA/O/MI/SHIN/YU/SUL/HAE)
  - element_code: 오행 코드 (WOOD/FIRE/EARTH/METAL/WATER)
  - ten_god_code: 십신 코드 (DAY_MASTER/BI_GYEON/GANG_JAE/...)
```

### 장점
- LLM이 직접 생성하므로 데이터 일관성 높음
- 십신 계산 로직 불필요

### 단점
- LLM 토큰 소비 증가
- LLM이 무시할 수 있음 (비결정론적)
- 모든 필드가 항상 생성된다는 보장 없음

### 리스크
| 항목 | 수준 | 설명 |
|------|------|------|
| 안정성 | 높음 | LLM은 언제든 프롬프트를 무시할 수 있음 |
| 유지보수 | 중간 | 프롬프트 변경 필요 |
| 호환성 | 낮음 | 기존 모델에 영향 없음 |

---

## Option B: Postprocess 보강 (권장)

### 설명
후처리기에서 천간/지지 한자를 기반으로 코드 필드를 결정론적으로 생성합니다.

### 구현 방법
```python
# 천간 매핑
GAN_TO_CODE = {
    "甲": "GAP", "乙": "EUL", "丙": "BYEONG", "丁": "JEONG", "戊": "MU",
    "己": "GI", "庚": "GYEONG", "辛": "SIN", "壬": "IM", "癸": "GYE",
}

# 지지 매핑
JI_TO_CODE = {
    "子": "JA", "丑": "CHUK", "寅": "IN", "卯": "MYO", "辰": "JIN", "巳": "SA",
    "午": "O", "未": "MI", "申": "SHIN", "酉": "YU", "戌": "SUL", "亥": "HAE",
}

# 후처리 로직
def _fill_pillar_codes(self, data):
    for key in ["year", "month", "day", "hour"]:
        pillar = data.get("chart", {}).get(key, {})
        if pillar:
            # gan_code 생성
            if "gan_code" not in pillar and "gan" in pillar:
                pillar["gan_code"] = GAN_TO_CODE.get(pillar["gan"], "UNKNOWN")
            # ji_code 생성
            if "ji_code" not in pillar and "ji" in pillar:
                pillar["ji_code"] = JI_TO_CODE.get(pillar["ji"], "UNKNOWN")
            # ten_god_code (일간 기준 계산 또는 폴백)
            if "ten_god_code" not in pillar:
                pillar["ten_god_code"] = self._calculate_ten_god(data, key)
```

### 장점
- 100% 결정론적: LLM 응답과 무관하게 항상 동작
- 기존 코드 호환성 유지
- 매핑 불가 시 명시적 폴백 + 로깅

### 단점
- 십신 계산 로직 필요 (복잡도 증가)
- 후처리기 유지보수 책임 증가

### 리스크
| 항목 | 수준 | 설명 |
|------|------|------|
| 안정성 | 낮음 | 결정론적 매핑으로 안정적 |
| 유지보수 | 중간 | 매핑 테이블 관리 필요 |
| 호환성 | 낮음 | 기존 코드와 호환 |

---

## 비교표

| 항목 | Option A (Prompt) | Option B (Postprocess) |
|------|-------------------|------------------------|
| 안정성 | ⚠️ 낮음 (LLM 의존) | ✅ 높음 (결정론적) |
| 구현 복잡도 | 낮음 | 중간 |
| 토큰 비용 | 증가 | 변화 없음 |
| 유지보수 | 프롬프트 관리 | 매핑 테이블 관리 |
| 즉시 효과 | LLM 응답에 따라 다름 | 즉시 적용 |
| 방어력 | LLM 누락 시 실패 | LLM 누락 시에도 방어 |

---

## 권장안

### 1차: Option B (Postprocess 보강) - 필수
- 후처리기에 `_fill_pillar_codes` 단계 추가
- gan → gan_code, ji → ji_code 매핑 (결정론적)
- ten_god_code는 일단 폴백값 사용 후 정확한 계산 로직 추가

### 2차: Option A (Prompt 강화) - 선택
- 프롬프트에 필수 필드 명시로 LLM이 직접 생성하도록 유도
- 후처리기가 백업으로 동작

---

## 결론

**후처리 방어(필드 보정)가 1차 안전장치가 되어야 합니다.**

LLM은 언제든 필드를 누락할 수 있으므로:
1. 후처리기에서 결정론적 매핑으로 방어 (필수)
2. 프롬프트 강화로 LLM 생성률 향상 (선택)

이 순서로 구현합니다.
