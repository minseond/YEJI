"""GPU 모델 로더 (태스크 #98)

L4 GPU에서 Prompt Guard 및 Intent Classifier 모델을 로드합니다.

주요 기능:
- FP16 정밀도로 VRAM 효율적 로딩
- Eager Loading (앱 시작 시 사전 로드)
- 로드 실패 시 그레이스풀 디그레이드
- VRAM 사용량 모니터링

참조: docs/design/l4-intent-deployment.md
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import structlog

logger = structlog.get_logger()


if TYPE_CHECKING:
    pass


@dataclass
class LoadedGuardModel:
    """로드된 Guard 모델 정보"""

    model: Any
    tokenizer: Any
    model_id: str
    vram_mb: float
    load_time_ms: float


@dataclass
class LoadedIntentModel:
    """로드된 Intent 모델 정보"""

    model: Any
    model_id: str
    vram_mb: float
    load_time_ms: float


class ModelLoader:
    """GPU 모델 로더

    Prompt Guard와 Intent Classifier 모델을 L4 GPU에 로드합니다.
    FP16 정밀도를 사용하여 VRAM 효율성을 극대화합니다.

    사용 예시:
        loader = ModelLoader(device="cuda:0")

        guard_model = await loader.load_prompt_guard()
        intent_model = await loader.load_intent_classifier()
    """

    def __init__(self, device: str = "cuda:0") -> None:
        """모델 로더 초기화

        Args:
            device: GPU 디바이스 (예: "cuda:0", "cpu")
        """
        self.device = device
        self._torch_dtype = None

    def _get_torch_dtype(self) -> Any:
        """torch.float16 반환 (지연 로드)"""
        if self._torch_dtype is None:
            try:
                import torch

                self._torch_dtype = torch.float16
            except ImportError:
                logger.warning(
                    "torch_not_available",
                    message="torch 미설치, CPU 모드로 폴백",
                )
                self._torch_dtype = None
        return self._torch_dtype

    async def load_prompt_guard(
        self,
        model_id: str = "meta-llama/Llama-Prompt-Guard-2-86M",
    ) -> LoadedGuardModel:
        """Prompt Guard 모델 로드

        Args:
            model_id: HuggingFace 모델 ID

        Returns:
            로드된 모델 정보

        Raises:
            ImportError: transformers 미설치 시
            RuntimeError: 모델 로드 실패 시
        """
        start_time = time.perf_counter()
        logger.info("loading_prompt_guard", model_id=model_id, device=self.device)

        try:
            from transformers import AutoModelForSequenceClassification, AutoTokenizer

            tokenizer = AutoTokenizer.from_pretrained(model_id)

            torch_dtype = self._get_torch_dtype()
            model = AutoModelForSequenceClassification.from_pretrained(
                model_id,
                torch_dtype=torch_dtype,
                device_map=self.device if self.device != "cpu" else None,
            )
            model.eval()

            vram_mb = self._get_model_vram_mb(model)
            load_time_ms = (time.perf_counter() - start_time) * 1000

            logger.info(
                "prompt_guard_loaded",
                model_id=model_id,
                vram_mb=round(vram_mb, 2),
                load_time_ms=round(load_time_ms, 2),
            )

            return LoadedGuardModel(
                model=model,
                tokenizer=tokenizer,
                model_id=model_id,
                vram_mb=vram_mb,
                load_time_ms=load_time_ms,
            )

        except ImportError as e:
            logger.error(
                "prompt_guard_import_error",
                error=str(e),
                message="transformers 라이브러리를 설치하세요",
            )
            raise

        except Exception as e:
            logger.error(
                "prompt_guard_load_error",
                model_id=model_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise RuntimeError(f"Prompt Guard 모델 로드 실패: {e}") from e

    async def load_intent_classifier(
        self,
        model_id: str = "Alibaba-NLP/gte-multilingual-base",
    ) -> LoadedIntentModel:
        """Intent Classifier 모델 로드

        Args:
            model_id: HuggingFace 모델 ID

        Returns:
            로드된 모델 정보

        Raises:
            ImportError: sentence-transformers 미설치 시
            RuntimeError: 모델 로드 실패 시
        """
        start_time = time.perf_counter()
        logger.info("loading_intent_classifier", model_id=model_id, device=self.device)

        try:
            from sentence_transformers import SentenceTransformer

            model = SentenceTransformer(model_id, device=self.device)

            vram_mb = self._estimate_st_vram_mb(model)
            load_time_ms = (time.perf_counter() - start_time) * 1000

            logger.info(
                "intent_classifier_loaded",
                model_id=model_id,
                vram_mb=round(vram_mb, 2),
                load_time_ms=round(load_time_ms, 2),
            )

            return LoadedIntentModel(
                model=model,
                model_id=model_id,
                vram_mb=vram_mb,
                load_time_ms=load_time_ms,
            )

        except ImportError as e:
            logger.error(
                "intent_classifier_import_error",
                error=str(e),
                message="sentence-transformers를 설치하세요",
            )
            raise

        except Exception as e:
            logger.error(
                "intent_classifier_load_error",
                model_id=model_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise RuntimeError(f"Intent Classifier 모델 로드 실패: {e}") from e

    def _get_model_vram_mb(self, model: Any) -> float:
        """모델 VRAM 사용량 계산 (MB)"""
        try:
            param_size = sum(p.numel() * p.element_size() for p in model.parameters())
            buffer_size = sum(b.numel() * b.element_size() for b in model.buffers())
            return (param_size + buffer_size) / (1024 * 1024)
        except Exception:
            return 0.0

    def _estimate_st_vram_mb(self, model: Any) -> float:
        """SentenceTransformer VRAM 사용량 추정 (MB)"""
        try:
            if hasattr(model, "_first_module"):
                return self._get_model_vram_mb(model._first_module().auto_model)
            return 600.0
        except Exception:
            return 600.0


def get_gpu_memory_info() -> dict[str, float] | None:
    """현재 GPU 메모리 상태 조회

    Returns:
        메모리 정보 딕셔너리 또는 None (GPU 미사용 시)
    """
    try:
        import torch

        if not torch.cuda.is_available():
            return None

        total = torch.cuda.get_device_properties(0).total_memory
        allocated = torch.cuda.memory_allocated()
        reserved = torch.cuda.memory_reserved()

        total_gb = total / (1024**3)
        allocated_gb = allocated / (1024**3)
        reserved_gb = reserved / (1024**3)
        free_gb = total_gb - reserved_gb
        utilization = reserved / total * 100

        return {
            "total_gb": round(total_gb, 2),
            "allocated_gb": round(allocated_gb, 2),
            "reserved_gb": round(reserved_gb, 2),
            "free_gb": round(free_gb, 2),
            "utilization_percent": round(utilization, 2),
        }

    except ImportError:
        return None
    except Exception as e:
        logger.warning("gpu_memory_info_error", error=str(e))
        return None


def log_gpu_memory_status() -> None:
    """GPU 메모리 상태 로깅"""
    info = get_gpu_memory_info()
    if info:
        logger.info(
            "gpu_memory_status",
            total_gb=info["total_gb"],
            allocated_gb=info["allocated_gb"],
            reserved_gb=info["reserved_gb"],
            free_gb=info["free_gb"],
            utilization_percent=info["utilization_percent"],
        )
    else:
        logger.debug("gpu_not_available")
