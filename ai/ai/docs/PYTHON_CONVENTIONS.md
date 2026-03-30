# YEJI AI Server - Python 컨벤션 가이드

> YEJI 프로젝트의 Python 코드 작성 규칙 (2026년 기준)

## 목차

1. [Python 버전](#python-버전)
2. [타입 힌트](#타입-힌트)
3. [Import 순서](#import-순서)
4. [네이밍 컨벤션](#네이밍-컨벤션)
5. [코드 스타일](#코드-스타일)
6. [Pydantic v2 패턴](#pydantic-v2-패턴)
7. [비동기 패턴](#비동기-패턴)
8. [로깅](#로깅)
9. [테스트](#테스트)
10. [피해야 할 패턴](#피해야-할-패턴)

---

## Python 버전

**요구 버전: Python 3.11+**

Python 3.11 이상에서만 지원되는 기능을 적극 활용합니다:

- Union 타입 대신 `X | Y` 문법 사용
- `Self` 타입 힌트
- Exception Groups (`except*`)
- 향상된 에러 메시지
- `tomllib` 내장 지원

```python
# pyproject.toml
[project]
requires-python = ">=3.11"
```

---

## 타입 힌트

### 모든 함수에 타입 힌트 필수

```python
# Good
def calculate_score(values: list[int], multiplier: float = 1.0) -> int:
    """점수를 계산합니다."""
    return int(sum(values) * multiplier)


async def fetch_data(user_id: int) -> dict[str, Any]:
    """사용자 데이터를 조회합니다."""
    ...


# Bad - 타입 힌트 없음
def process(d):
    return d
```

### `X | None` 문법 사용 (Optional 대신)

Python 3.10+ 스타일의 Union 문법을 사용합니다.

```python
# Good - Python 3.10+ 스타일
def get_user(user_id: int) -> User | None:
    """사용자를 조회합니다. 없으면 None 반환."""
    ...


def process_data(data: str | bytes | None = None) -> dict[str, Any]:
    """문자열 또는 바이트 데이터를 처리합니다."""
    ...


# Bad - 구식 스타일
from typing import Optional, Union

def get_user(user_id: int) -> Optional[User]:  # 사용 금지
    ...

def process_data(data: Union[str, bytes, None] = None):  # 사용 금지
    ...
```

### 컬렉션 타입 힌트

```python
# Good - 내장 타입 사용 (Python 3.9+)
def process_items(items: list[str]) -> dict[str, int]:
    ...

users: set[User] = set()
mapping: dict[str, list[int]] = {}


# Bad - typing 모듈 불필요
from typing import List, Dict, Set  # 사용 금지

def process_items(items: List[str]) -> Dict[str, int]:
    ...
```

### 제네릭 및 고급 타입

```python
from collections.abc import AsyncGenerator, Callable, Iterable, Mapping
from typing import Any, TypeVar, ParamSpec

# AsyncGenerator 사용
async def stream_events() -> AsyncGenerator[str, None]:
    yield "event1"
    yield "event2"


# Callable 사용
def apply_transform(
    data: list[int],
    transform: Callable[[int], int],
) -> list[int]:
    return [transform(x) for x in data]


# TypeVar 사용
T = TypeVar("T")

def first_or_none(items: list[T]) -> T | None:
    return items[0] if items else None
```

---

## Import 순서

세 그룹으로 구분하고, 각 그룹 내에서 알파벳 순 정렬합니다.

```python
# 1. 표준 라이브러리
import asyncio
import json
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal, TypeVar

# 2. 서드파티 라이브러리
import httpx
import structlog
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

# 3. 로컬 모듈
from yeji_ai.config import get_settings
from yeji_ai.models.schemas import AnalyzeRequest, BaseResponse
from yeji_ai.services.saju_service import SajuService
```

**규칙:**

- 각 그룹 사이에 빈 줄 하나
- `from X import Y` 형식 선호
- 와일드카드 임포트 (`from X import *`) 금지

---

## 네이밍 컨벤션

### 변수 및 함수: `snake_case`

```python
# 변수
user_count = 0
session_data: dict[str, Any] = {}
is_valid = True

# 함수
def calculate_fortune_score(data: dict) -> int:
    ...

async def fetch_user_profile(user_id: int) -> UserProfile:
    ...
```

### 클래스: `PascalCase`

```python
class SajuService:
    """사주 분석 서비스"""
    ...


class UserProfile(BaseModel):
    """사용자 프로필 모델"""
    ...


class FortuneCategory(str, Enum):
    """운세 카테고리"""
    LOVE = "연애운"
    CAREER = "직장운"
```

### 상수: `UPPER_SNAKE_CASE`

```python
# 모듈 레벨 상수
SESSION_TTL_SECONDS = 1800
MAX_RETRY_COUNT = 3
DEFAULT_TIMEOUT = 30.0

# Enum 값
class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
```

### Private 멤버: `_leading_underscore`

```python
class SajuService:
    def __init__(self):
        self._sessions: dict[str, CachedSession] = {}  # private
        self._cleanup_task: asyncio.Task | None = None

    def _get_session(self, session_id: str) -> SessionState | None:
        """내부용 세션 조회 메서드"""
        ...
```

---

## 코드 스타일

### 기본 규칙

| 항목 | 규칙 |
|------|------|
| 들여쓰기 | 4-space (탭 사용 금지) |
| 라인 길이 | 최대 100자 |
| 문자열 | Double quotes (`"`) |
| Trailing comma | 항상 사용 |

### Trailing Comma 사용

```python
# Good - trailing comma
ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "yeji.ssafy.io",
]

class UserRequest(BaseModel):
    user_id: int = Field(..., description="사용자 ID")
    name: str = Field(..., description="이름")
    email: str | None = Field(None, description="이메일")


def process(
    data: dict[str, Any],
    options: ProcessOptions,
    callback: Callable | None = None,
) -> ProcessResult:
    ...


# Bad - trailing comma 없음
ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "yeji.ssafy.io"  # diff 시 불필요한 변경 발생
]
```

### Docstring

Google 스타일 docstring을 사용합니다.

```python
def calculate_element_balance(
    four_pillars: FourPillars,
    include_hidden: bool = True,
) -> ElementBalance:
    """사주 팔자의 오행 균형을 계산합니다.

    Args:
        four_pillars: 사주 팔자 정보
        include_hidden: 지장간 포함 여부 (기본값: True)

    Returns:
        오행별 점수가 담긴 ElementBalance 객체

    Raises:
        ValueError: 유효하지 않은 사주 정보인 경우
    """
    ...


class SajuService:
    """사주 분석 서비스

    사주 계산, vLLM 해석 생성, 티키타카 토론 등의 기능을 제공합니다.

    Attributes:
        calculator: 사주 계산기 인스턴스
        vllm_client: vLLM API 클라이언트
    """
    ...
```

---

## Pydantic v2 패턴

### 기본 모델 정의

```python
from pydantic import BaseModel, Field, field_validator, model_validator


class UserProfile(BaseModel):
    """사용자 프로필"""

    user_id: int = Field(..., description="사용자 ID", ge=1)
    name: str = Field(..., description="이름", min_length=1, max_length=50)
    email: str | None = Field(None, description="이메일")
    birth_date: str = Field(..., description="생년월일 (YYYY-MM-DD)")
    tags: list[str] = Field(default_factory=list, description="태그 목록")
```

### Validator 사용 (v2 스타일)

```python
from pydantic import BaseModel, field_validator, model_validator


class SajuRequest(BaseModel):
    """사주 분석 요청"""

    birth_date: str
    birth_time: str | None = None

    @field_validator("birth_date")
    @classmethod
    def validate_birth_date(cls, v: str) -> str:
        """생년월일 형식 검증"""
        from datetime import datetime
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("생년월일은 YYYY-MM-DD 형식이어야 합니다")
        return v

    @field_validator("birth_time")
    @classmethod
    def validate_birth_time(cls, v: str | None) -> str | None:
        """출생시간 형식 검증"""
        if v is None:
            return v
        from datetime import datetime
        try:
            datetime.strptime(v, "%H:%M")
        except ValueError:
            raise ValueError("출생시간은 HH:MM 형식이어야 합니다")
        return v

    @model_validator(mode="after")
    def validate_model(self) -> "SajuRequest":
        """모델 전체 검증"""
        # 추가 검증 로직
        return self
```

### Settings 정의 (pydantic-settings)

```python
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """애플리케이션 설정"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # 서버 설정
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    # 외부 서비스
    vllm_base_url: str = "http://localhost:8001"
    vllm_timeout: float = 120.0

    # 리스트/복합 타입
    cors_origins: list[str] = Field(
        default=["http://localhost:3000"],
    )
```

### 직렬화 (model_dump)

```python
# Pydantic v2 직렬화
user = UserProfile(user_id=1, name="홍길동", birth_date="1990-01-01")

# dict로 변환
user_dict = user.model_dump()
user_dict_exclude = user.model_dump(exclude={"email"})
user_dict_json = user.model_dump(mode="json")  # JSON 호환 타입으로 변환

# JSON 문자열로 변환
user_json = user.model_dump_json()
user_json_indent = user.model_dump_json(indent=2)
```

---

## 비동기 패턴

### async/await 기본

```python
import asyncio
from collections.abc import AsyncGenerator

import httpx


async def fetch_fortune(user_id: int) -> dict[str, Any]:
    """운세 데이터를 조회합니다."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"/api/fortune/{user_id}")
        return response.json()


async def process_multiple_users(user_ids: list[int]) -> list[dict]:
    """여러 사용자 동시 처리"""
    tasks = [fetch_fortune(uid) for uid in user_ids]
    return await asyncio.gather(*tasks)
```

### AsyncGenerator (스트리밍)

```python
async def stream_response(
    session_id: str,
) -> AsyncGenerator[str, None]:
    """SSE 응답 스트리밍"""
    yield "event: start\ndata: {}\n\n"

    async for chunk in generate_chunks():
        yield f"event: data\ndata: {chunk}\n\n"
        await asyncio.sleep(0.1)  # 백프레셔 방지

    yield "event: complete\ndata: {}\n\n"
```

### Context Manager (비동기)

```python
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """데이터베이스 세션 컨텍스트 매니저"""
    session = AsyncSession()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


# 사용
async def create_user(user_data: dict) -> User:
    async with get_db_session() as session:
        user = User(**user_data)
        session.add(user)
        return user
```

### 동시성 제어

```python
import asyncio


class RateLimiter:
    """비동기 요청 제한기"""

    def __init__(self, max_concurrent: int = 5):
        self._semaphore = asyncio.Semaphore(max_concurrent)

    async def execute(self, coro):
        """동시 실행 수 제한"""
        async with self._semaphore:
            return await coro


# 사용
limiter = RateLimiter(max_concurrent=3)
results = await asyncio.gather(
    *[limiter.execute(fetch_data(i)) for i in range(10)]
)
```

---

## 로깅

### structlog 설정

```python
import structlog

# 로거 생성
logger = structlog.get_logger()


# 기본 사용
logger.info("사용자 생성", user_id=123, name="홍길동")
logger.warning("세션 만료 임박", session_id="abc123", ttl_seconds=60)
logger.error("API 호출 실패", error=str(e), endpoint="/api/fortune")
```

### 구조화된 로깅 패턴

```python
import structlog
from functools import wraps

logger = structlog.get_logger()


def log_execution(func):
    """함수 실행 로깅 데코레이터"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        logger.info(
            "function_start",
            function=func.__name__,
            args_count=len(args),
        )
        try:
            result = await func(*args, **kwargs)
            logger.info(
                "function_complete",
                function=func.__name__,
                success=True,
            )
            return result
        except Exception as e:
            logger.error(
                "function_error",
                function=func.__name__,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise
    return wrapper


# 사용
@log_execution
async def analyze_fortune(user_id: int) -> FortuneResult:
    ...
```

### 민감 정보 필터링

```python
# API 키, 토큰 등 민감 정보 로깅 금지

# Bad
logger.info("API 호출", api_key=settings.api_key)  # 절대 금지!

# Good
logger.info("API 호출", api_key_prefix=settings.api_key[:8] + "...")
logger.info("인증 성공", user_id=user.id)  # 최소한의 정보만
```

---

## 테스트

### pytest 기본 구조

```python
# tests/test_saju_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock

from yeji_ai.services.saju_service import SajuService


class TestSajuService:
    """SajuService 테스트"""

    @pytest.fixture
    def service(self) -> SajuService:
        """서비스 인스턴스 픽스처"""
        return SajuService()

    @pytest.fixture
    def mock_vllm_client(self) -> AsyncMock:
        """Mock vLLM 클라이언트"""
        client = AsyncMock()
        client.generate.return_value = MagicMock(text="테스트 응답")
        return client
```

### AAA 패턴 (Arrange, Act, Assert)

```python
@pytest.mark.asyncio
async def test_calculate_saju_returns_valid_result(
    service: SajuService,
    mock_vllm_client: AsyncMock,
) -> None:
    """사주 계산이 유효한 결과를 반환하는지 테스트"""
    # Arrange (준비)
    service.vllm_client = mock_vllm_client
    profile = SajuProfile(
        name="홍길동",
        gender=Gender.MALE,
        birth_date="1990-01-15",
        birth_time="14:30",
    )

    # Act (실행)
    result = await service.calculate_saju(profile)

    # Assert (검증)
    assert result is not None
    assert result.total_score >= 0
    assert result.eastern.day_master is not None
    mock_vllm_client.generate.assert_called_once()
```

### 비동기 테스트

```python
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_fortune_endpoint(client: AsyncClient) -> None:
    """운세 API 엔드포인트 테스트"""
    # Arrange
    request_data = {
        "user_id": 1,
        "category": "연애운",
    }

    # Act
    response = await client.post("/api/v1/fortune/analyze", json=request_data)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
```

### 외부 API 모킹

```python
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_vllm_generation_fallback_on_error(
    service: SajuService,
) -> None:
    """vLLM 오류 시 폴백 동작 테스트"""
    # Arrange
    with patch.object(
        service.vllm_client,
        "generate",
        new_callable=AsyncMock,
    ) as mock_generate:
        mock_generate.side_effect = Exception("Connection failed")

        # Act
        result = await service._generate_eastern_interpretation(
            four_pillars=mock_pillars,
            element_balance=mock_balance,
            day_master="갑목",
        )

        # Assert
        assert "갑목" in result  # 폴백 메시지 확인
```

### conftest.py 예시

```python
# tests/conftest.py
import pytest
from httpx import AsyncClient
from yeji_ai.main import app


@pytest.fixture
async def client() -> AsyncClient:
    """비동기 테스트 클라이언트"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sample_saju_profile() -> dict:
    """테스트용 사주 프로필"""
    return {
        "name": "테스트유저",
        "gender": "M",
        "birth_date": "1997-10-24",
        "birth_time": "14:30",
        "birth_place": "서울",
    }
```

---

## 피해야 할 패턴

### 타입 힌트 관련

```python
# Bad - Optional 사용
from typing import Optional
def get_user() -> Optional[User]:  # 금지
    ...

# Good
def get_user() -> User | None:
    ...


# Bad - Union 사용
from typing import Union
data: Union[str, int]  # 금지

# Good
data: str | int
```

### Import 관련

```python
# Bad - 와일드카드 임포트
from yeji_ai.models import *  # 금지

# Good
from yeji_ai.models import User, Profile, FortuneResult


# Bad - 순환 임포트 발생 가능한 구조
# module_a.py
from module_b import func_b  # 모듈 최상단에서 임포트

# Good - TYPE_CHECKING 사용
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from module_b import TypeB  # 타입 체크 시에만 임포트
```

### 보안 관련

```python
# Bad - 민감 정보 로깅
logger.info("User authenticated", password=user.password)  # 절대 금지
logger.debug("API call", headers={"Authorization": token})  # 금지

# Good
logger.info("User authenticated", user_id=user.id)
logger.debug("API call", endpoint=url)


# Bad - .env 파일 커밋
# git add .env  # 절대 금지!

# Good - .env.example 커밋
# .env.example (값 없이 키만)
VLLM_API_KEY=
DATABASE_URL=
```

### 코드 품질

```python
# Bad - 매직 넘버
if retry_count > 3:  # 3이 뭘 의미하는지 불명확
    ...

# Good - 상수 사용
MAX_RETRY_COUNT = 3
if retry_count > MAX_RETRY_COUNT:
    ...


# Bad - 빈 except
try:
    process()
except:  # 금지
    pass

# Good - 구체적인 예외 처리
try:
    process()
except ValueError as e:
    logger.warning("Invalid value", error=str(e))
except Exception as e:
    logger.error("Unexpected error", error=str(e))
    raise
```

---

## 도구 설정

### pyproject.toml (Ruff)

```toml
[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "UP",  # pyupgrade
]
ignore = [
    "E501",  # line-too-long (포매터가 처리)
]

[tool.ruff.lint.isort]
known-first-party = ["yeji_ai"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

### 린트 및 포맷 실행

```bash
# 린트 검사
ruff check src/

# 린트 자동 수정
ruff check src/ --fix

# 코드 포맷팅
ruff format src/

# 테스트 실행
pytest tests/ -v

# 커버리지 포함 테스트
pytest tests/ -v --cov=yeji_ai --cov-report=html
```

---

## 참고 자료

- [Python Type Hints Cheat Sheet](https://mypy.readthedocs.io/en/stable/cheat_sheet_py3.html)
- [Pydantic v2 Documentation](https://docs.pydantic.dev/latest/)
- [structlog Documentation](https://www.structlog.org/)
- [FastAPI Best Practices](https://fastapi.tiangolo.com/tutorial/)
- [pytest Documentation](https://docs.pytest.org/)
