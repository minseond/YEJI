# 복합 메시지 서비스 사용 가이드

## 개요

`CompoundMessageService`는 Redis에서 가져온 원본 사주/점성 데이터에서 상위 2개 요소를 추출하고, 미리 생성된 메시지 풀에서 복합 메시지를 선택하는 서비스입니다.

## 주요 기능

### 1. 상위 2개 요소 추출
- 오행, 십신, 원소, 모달리티 등의 분포 데이터에서 상위 2개 요소를 자동 추출
- 알파벳순으로 정렬하여 일관된 키 생성

### 2. 복합 메시지 선택
- 추출된 2개 요소와 카테고리를 조합하여 메시지 풀에서 조회
- 메시지가 없으면 폴백 메시지 반환

### 3. 메시지 풀 관리
- 앱 시작 시 JSON 파일에서 메시지 풀을 메모리에 로드 (싱글톤)
- 런타임 중에는 메모리에서 빠르게 조회

## 사용 방법

### 기본 사용 (편의 함수)

```python
from yeji_ai.services.compound_message_service import get_compound_message_or_fallback

# 동양 운세 - 오행 복합 메시지
message = get_compound_message_or_fallback(
    fortune_data=eastern_fortune_data,  # Redis에서 가져온 데이터
    fortune_type="eastern",
    category="love",
    section="five_elements",
)

# 서양 운세 - 원소 복합 메시지
message = get_compound_message_or_fallback(
    fortune_data=western_fortune_data,
    fortune_type="western",
    category="career",
    section="elements",
)
```

### 상세 사용 (서비스 인스턴스)

```python
from yeji_ai.services.compound_message_service import CompoundMessageService

service = CompoundMessageService()

# 복합 메시지 조회 (없으면 None 반환)
message = service.get_compound_message(
    fortune_data=fortune_data,
    fortune_type="eastern",
    category="love",
    section="five_elements",
)

# 메시지가 없으면 폴백 사용
if not message:
    message = service.get_fallback_message("eastern", "love")
```

## 입력 데이터 구조

### 동양 운세 (Eastern)

#### 오행 (five_elements)
```python
{
    "stats": {
        "five_elements": {
            "summary": "화와 목이 강합니다",
            "list": [
                {"element": "FIRE", "count": 4, "percent": 40.0},
                {"element": "WOOD", "count": 3, "percent": 30.0},
                {"element": "WATER", "count": 2, "percent": 20.0},
                {"element": "EARTH", "count": 1, "percent": 10.0},
            ]
        }
    }
}
```

#### 십신 (ten_gods)
```python
{
    "stats": {
        "ten_gods": {
            "summary": "비겁과 식상이 강합니다",
            "list": [
                {"code": "BI_GYEON", "count": 3, "percent": 37.5},
                {"code": "SIK_SIN", "count": 2, "percent": 25.0},
                {"code": "JEONG_JAE", "count": 1, "percent": 12.5},
            ]
        }
    }
}
```

### 서양 운세 (Western)

#### 4원소 (elements)
```python
{
    "stats": {
        "element_4_distribution": [
            {"code": "FIRE", "percentage": 50.0},
            {"code": "AIR", "percentage": 30.0},
            {"code": "WATER", "percentage": 15.0},
            {"code": "EARTH", "percentage": 5.0},
        ]
    }
}
```

#### 3양태 (modality)
```python
{
    "stats": {
        "modality_3_distribution": [
            {"code": "CARDINAL", "percentage": 50.0},
            {"code": "FIXED", "percentage": 33.3},
            {"code": "MUTABLE", "percentage": 16.7},
        ]
    }
}
```

## 메시지 풀 구조

메시지 풀은 JSON 파일로 관리되며, 다음 위치에 저장됩니다:

```
src/yeji_ai/data/
├── eastern/
│   ├── five_elements_pairs.json
│   └── ten_gods_pairs.json
└── western/
    ├── elements_pairs.json
    └── modality_pairs.json
```

### JSON 파일 형식

```json
{
  "FIRE_WOOD_love": [
    "화와 목의 조화로 따뜻한 사랑이 찾아옵니다.",
    "열정과 성장이 함께하는 관계가 기다립니다."
  ],
  "FIRE_WOOD_career": [
    "불타는 열정과 성장의 에너지가 커리어를 밝힙니다.",
    "추진력과 발전이 함께하는 시기입니다."
  ]
}
```

### 복합 키 규칙

복합 키는 다음 형식으로 생성됩니다:

```
{요소1}_{요소2}_{카테고리}
```

- 요소1, 요소2: 알파벳순 정렬 (예: `FIRE_WOOD`, `AIR_FIRE`)
- 카테고리: `love`, `career`, `health`, `money`, `study` 등

**예시:**
- `FIRE_WOOD_love` (화+목, 연애운)
- `BI_GYEON_SIK_SIN_career` (비겁+식신, 직업운)
- `CARDINAL_FIXED_health` (카디널+고정, 건강운)

## API 레퍼런스

### CompoundMessageService

#### `extract_top_two_elements(element_list, key="count")`
상위 2개 요소를 추출합니다.

**Parameters:**
- `element_list` (list[dict]): 요소 리스트
- `key` (str): 정렬 기준 키 (기본값: `"count"`)

**Returns:**
- `tuple[str, str] | None`: 알파벳순 정렬된 상위 2개 요소 또는 None

**Example:**
```python
element_list = [
    {"element": "FIRE", "count": 4},
    {"element": "WOOD", "count": 3},
]
result = service.extract_top_two_elements(element_list)
# result: ("FIRE", "WOOD")
```

#### `generate_compound_key(elem1, elem2, category)`
복합 키를 생성합니다.

**Parameters:**
- `elem1` (str): 첫 번째 요소
- `elem2` (str): 두 번째 요소
- `category` (str): 카테고리

**Returns:**
- `str`: 복합 키

**Example:**
```python
key = service.generate_compound_key("WOOD", "FIRE", "love")
# key: "FIRE_WOOD_love" (알파벳순 정렬)
```

#### `get_compound_message(fortune_data, fortune_type, category, section)`
복합 메시지를 조회합니다.

**Parameters:**
- `fortune_data` (dict): 운세 데이터 (stats 포함)
- `fortune_type` (Literal["eastern", "western"]): 운세 타입
- `category` (str): 카테고리 (love, career 등)
- `section` (str): 섹션 (five_elements, ten_gods, elements, modality)

**Returns:**
- `str | None`: 선택된 메시지 또는 None (폴백 필요)

#### `get_fallback_message(fortune_type, category)`
폴백 메시지를 반환합니다.

**Parameters:**
- `fortune_type` (Literal["eastern", "western"]): 운세 타입
- `category` (str): 카테고리

**Returns:**
- `str`: 기본 메시지

### 편의 함수

#### `get_compound_message_or_fallback(fortune_data, fortune_type, category, section)`
복합 메시지를 조회하거나 폴백을 반환합니다.

**Parameters:**
- `fortune_data` (dict): 운세 데이터
- `fortune_type` (Literal["eastern", "western"]): 운세 타입
- `category` (str): 카테고리
- `section` (str): 섹션

**Returns:**
- `str`: 복합 메시지 또는 폴백 메시지 (항상 문자열 반환)

## 폴백 처리

복합 메시지를 찾을 수 없는 경우 다음 순서로 폴백됩니다:

1. **메시지 풀 조회 실패** → 폴백 메시지 반환
2. **요소가 2개 미만** → 폴백 메시지 반환
3. **stats 데이터 없음** → 폴백 메시지 반환

### 폴백 메시지 목록

#### 동양 운세
- `love`: "오늘은 관계에서 균형과 조화를 찾는 하루입니다."
- `career`: "차근차근 노력하면 좋은 결과가 있을 것입니다."
- `health`: "몸과 마음의 균형을 유지하세요."
- `money`: "재물 관리에 신중함이 필요한 시기입니다."
- `study`: "꾸준한 노력이 결실을 맺을 것입니다."

#### 서양 운세
- `love`: "별들이 당신의 관계에 조화를 가져다줍니다."
- `career`: "우주의 흐름에 따라 움직이면 기회가 찾아옵니다."
- `health`: "마음의 평화가 건강의 시작입니다."
- `money`: "안정적인 흐름 속에서 성장하세요."
- `study`: "지식의 별들이 당신을 비춥니다."

## 성능 최적화

### 싱글톤 패턴
`MessagePool`은 싱글톤 패턴으로 구현되어 앱 시작 시 한 번만 초기화됩니다.

```python
# 여러 번 호출해도 같은 인스턴스
pool1 = MessagePool()
pool2 = MessagePool()
assert pool1 is pool2  # True
```

### 메모리 캐싱
JSON 파일은 앱 시작 시 메모리에 로드되어 런타임 중에는 파일 I/O 없이 빠르게 조회됩니다.

## 통합 예시

### Quick Summary API에서 사용

```python
from yeji_ai.services.compound_message_service import get_compound_message_or_fallback

async def get_quick_summary(fortune_id: str, category: str):
    # Redis에서 운세 데이터 조회
    fortune_data = await redis_client.get(f"fortune:{fortune_id}")

    # 운세 타입 확인
    fortune_type = fortune_data.get("type")  # "eastern" or "western"

    # 복합 메시지 생성
    if fortune_type == "eastern":
        # 오행 복합 메시지
        message = get_compound_message_or_fallback(
            fortune_data=fortune_data,
            fortune_type="eastern",
            category=category,
            section="five_elements",
        )
    else:
        # 원소 복합 메시지
        message = get_compound_message_or_fallback(
            fortune_data=fortune_data,
            fortune_type="western",
            category=category,
            section="elements",
        )

    return {"message": message, "category": category}
```

## 테스트

테스트는 `tests/test_compound_message_service.py`에 작성되어 있습니다.

```bash
# 전체 테스트 실행
uv run pytest tests/test_compound_message_service.py -v

# 특정 테스트만 실행
uv run pytest tests/test_compound_message_service.py::test_extract_top_two_elements_success -v
```

## 확장 가능성

### 메시지 선택 전략 추가
현재는 첫 번째 메시지를 반환하지만, 랜덤 선택이나 가중치 기반 선택으로 확장 가능합니다.

```python
import random

# MessagePool 클래스 내부
def get_random_message(self, messages: list[str]) -> str:
    """메시지 리스트에서 랜덤 선택"""
    return random.choice(messages)
```

### 새로운 섹션 추가
새로운 데이터 분석 섹션을 추가하려면:

1. JSON 파일 생성 (`data/eastern/new_section_pairs.json`)
2. `MessagePool._load_eastern_pools()` 또는 `_load_western_pools()`에 추가
3. API에서 `section="new_section"` 파라미터로 호출

## 주의사항

1. **JSON 파일 형식 준수**: 복합 키는 반드시 `{ELEM1}_{ELEM2}_{CATEGORY}` 형식으로 작성
2. **알파벳순 정렬**: 요소는 항상 알파벳순으로 정렬하여 키 생성
3. **대소문자 일관성**: 모든 요소 코드는 대문자로 통일 (예: `FIRE`, `WOOD`)
4. **폴백 처리**: 메시지가 없는 경우를 항상 대비하여 폴백 로직 구현

## 로깅

서비스는 structlog를 사용하여 다음 이벤트를 로깅합니다:

- `message_pools_loaded`: 메시지 풀 로드 완료
- `top_two_extracted`: 상위 2개 요소 추출 성공
- `compound_message_selected`: 복합 메시지 선택 성공
- `compound_key_not_found`: 복합 키를 메시지 풀에서 찾지 못함
- `fallback_message_used`: 폴백 메시지 사용

로그 레벨을 `DEBUG`로 설정하면 더 상세한 정보를 확인할 수 있습니다.
