# llmServer/app/provider/registry.py

import logging
from typing import Dict

from app.providers.llm.base import BaseLLMProvider
from app.providers.embedding.base import BaseEmbeddingProvider
from app.providers.reranker.base import BaseRerankerProvider
from app.core.logging.logging_tags import LogTag
from app.core.logging.request_context import get_request_id

logger = logging.getLogger(__name__)


class ProviderRegistry:
    def __init__(self):
        # LLM과 Reranker 저장소를 분리하여 관리
        self._llms: Dict[str, BaseLLMProvider] = {}

        self._embeddings: Dict[str, BaseEmbeddingProvider] = {}

        self._rerankers: Dict[str, BaseRerankerProvider] = {}

    # --- LLM Provider 관리 ---
    def register_llm(self, model_name: str, provider: BaseLLMProvider):
        self._llms[model_name] = provider
        logger.info(
            "LLM Provider registered",
            extra={
                "tag": LogTag.ROUTER,
                "model": model_name,
            },
        )

    def get_llm(self, model_name: str) -> BaseLLMProvider:
        request_id = get_request_id()  # 누락되었던 request_id 할당 추가

        if model_name not in self._llms:
            logger.error(
                "LLM Model not registered",
                extra={
                    "tag": LogTag.ROUTER,
                    "request_id": request_id,
                    "model": model_name,
                },
            )
            raise ValueError(f"LLM Model '{model_name}' not registered")

        logger.info(
            "LLM Provider selected",
            extra={
                "tag": LogTag.ROUTER,
                "request_id": request_id,
                "model": model_name,
            },
        )
        return self._llms[model_name]

    # --- Embedding Provider 관리 ---
    def register_embedding(self, model_name: str, provider):
        self._embeddings[model_name] = provider
        logger.info(
            "Embedding Provider registered",
            extra={
                "tag": LogTag.ROUTER,
                "model": model_name,
            },
        )

    def get_embedding(self, model_name: str):
        request_id = get_request_id()

        if model_name not in self._embeddings:
            logger.error(
                "Embedding Model not registered",
                extra={
                    "tag": LogTag.ROUTER,
                    "request_id": request_id,
                    "model": model_name,
                },
            )
            raise ValueError(f"Embedding Model '{model_name}' not registered")

        logger.info(
            "Embedding Provider selected",
            extra={
                "tag": LogTag.ROUTER,
                "request_id": request_id,
                "model": model_name,
            },
        )
        return self._embeddings[model_name]

    # --- Reranker Provider 관리 ---
    def register_reranker(self, model_name: str, provider: BaseRerankerProvider):
        self._rerankers[model_name] = provider
        logger.info(
            "Reranker Provider registered",
            extra={
                "tag": LogTag.ROUTER,
                "model": model_name,
            },
        )

    def get_reranker(self, model_name: str) -> BaseRerankerProvider:
        request_id = get_request_id()

        if model_name not in self._rerankers:
            logger.error(
                "Reranker Model not registered",
                extra={
                    "tag": LogTag.ROUTER,
                    "request_id": request_id,
                    "model": model_name,
                },
            )
            raise ValueError(f"Reranker Model '{model_name}' not registered")

        logger.info(
            "Reranker Provider selected",
            extra={
                "tag": LogTag.ROUTER,
                "request_id": request_id,
                "model": model_name,
            },
        )
        return self._rerankers[model_name]
