"""설정 관리 모듈"""

from functools import lru_cache
from typing import Literal

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
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    root_path: str = ""  # Nginx 프록시 경로 (예: "/ai")

    # vLLM 설정
    vllm_base_url: str = "http://localhost:8001"
    vllm_model: str = "tellang/yeji-8b-rslora-v7"
    vllm_max_tokens: int = 1500  # 프롬프트 길이 고려 (max_model_len 4096)
    vllm_temperature: float = 0.7
    vllm_top_p: float = 0.9

    # OpenAI/GPT-5-mini 설정
    openai_api_key: str = Field(default="", description="OpenAI API 키")
    openai_base_url: str = Field(
        default="https://api.openai.com/v1",
        description="OpenAI API URL (로컬 실행 시 변경)",
    )
    openai_model: str = Field(default="gpt-5-mini", description="OpenAI 모델 ID")
    openai_max_tokens: int = 1500
    openai_temperature: float = 0.7
    openai_top_p: float = 0.9
    openai_organization: str = Field(default="", description="OpenAI Organization ID")

    # Provider 폴백 설정
    llm_provider_primary: str = Field(
        default="vllm",
        description="기본 LLM Provider (vllm, openai, ollama)",
    )
    llm_provider_fallback: str = Field(
        default="openai",
        description="폴백 LLM Provider",
    )
    llm_fallback_enabled: bool = Field(
        default=True,
        description="Provider 폴백 활성화 여부",
    )

    # HuggingFace
    hf_token: str = ""

    # 백엔드 연동
    backend_url: str = "http://localhost:8081"

    # Redis 설정
    redis_url: str = Field(default="redis://localhost:6379", description="Redis URL")

    # CORS (환경변수: CORS_ORIGINS='["http://localhost:3000"]')
    cors_origins: list[str] = Field(
        default=["http://localhost:3000"],
        description="CORS 허용 오리진 목록. 환경변수로 오버라이드 가능",
    )

    # 배포 환경 (Jenkinsfile에서 주입)
    deploy_env: str = "development"  # production | development

    # 티키타카 설정
    tikitaka_max_turns: int = 10  # 최대 토론 턴 수
    tikitaka_question_count: int = 2  # 중간 질문 횟수

    # GPT-5-mini 사용 플래그 (티키타카 채팅용)
    # True: GPT-5-mini 사용 (OPENAI_API_KEY 필요)
    # False: 8B vLLM만 사용
    use_gpt5mini_for_chat: bool = Field(
        default=False,
        description="티키타카 채팅에 GPT-5-mini 사용 여부. "
        "True면 GPT-5-mini, False면 8B vLLM 사용.",
    )

    # 테스트/디버그 설정
    skip_validation: bool = False  # True: Pydantic 검증 스킵, raw LLM 응답 반환

    # 후처리 설정
    enable_postprocess: bool = True  # 전체 후처리 활성화
    postprocess_eastern_enabled: bool = True  # 동양 운세 후처리 활성화
    postprocess_western_enabled: bool = True  # 서양 운세 후처리 활성화

    # Guided Decoding 설정 (vLLM json_schema response_format)
    # 주의: 복잡한 스키마(SajuDataV2 등)는 vLLM guided decoding에서 400 오류 발생
    # 기본값 False로 변경하여 json_object 모드 사용
    use_guided_json: bool = Field(
        default=False,
        description="vLLM guided_json/json_schema 사용 여부. "
        "True: 스키마 기반 토큰 마스킹으로 필수 필드/타입/Enum 보장. "
        "False: 기존 json_object 모드 (스키마 미강제).",
    )
    guided_json_fallback: bool = Field(
        default=True,
        description="guided_json 실패 시 json_object로 자동 폴백 여부",
    )

    # GPU 필터 설정 (태스크 #98)
    gpu_filter_enabled: bool = False  # GPU 기반 인텐트 필터 활성화
    gpu_device: str = "cuda:0"  # GPU 디바이스

    # Prompt Guard 설정 (악성 프롬프트 탐지)
    guard_model: str = "meta-llama/Llama-Prompt-Guard-2-86M"
    guard_threshold: float = 0.8  # 악성 판정 임계값 (0.0~1.0)
    guard_timeout: float = 1.0  # 추론 타임아웃 (초)
    guard_mode: Literal["block", "log_only", "shadow"] = "block"  # 동작 모드
    guard_required: bool = False  # True: 로드 실패 시 앱 시작 실패

    # Intent Classifier 설정 (임베딩 기반 의도 분류)
    intent_embedding_model: str = "Alibaba-NLP/gte-multilingual-base"
    intent_embedding_threshold: float = 0.7  # 분류 신뢰도 임계값 (0.0~1.0)
    intent_embedding_timeout: float = 0.5  # 추론 타임아웃 (초)
    intent_embedding_mode: Literal["block", "log_only", "shadow"] = "block"  # 동작 모드
    intent_embedding_required: bool = False  # True: 로드 실패 시 앱 시작 실패


@lru_cache
def get_settings() -> Settings:
    """설정 싱글톤 반환"""
    return Settings()
