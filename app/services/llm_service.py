# llmServer/app/services/llm_service.py

import logging
import time
from typing import List

from app.providers.registry import ProviderRegistry
from app.prompts.registry import PromptRegistry
from app.core.types import ChatMessage
from app.core.config import settings
from app.core.logging.logging_tags import LogTag
from app.core.logging.request_context import get_request_id


logger = logging.getLogger(__name__)


class LLMService:

    def __init__(self, llm_registry: ProviderRegistry, prompt_registry: PromptRegistry):
        self.llm_registry = llm_registry
        self.prompt_registry = prompt_registry

        self.router_model = settings.router_model
        self.sql_model = settings.sql_model
        self.sql_premium_model = settings.sql_premium_model
        self.answer_model = settings.answer_model
        self.chitchat_model = settings.chitchat_model

    # ==========================================================
    # 🔹 Public Use-case APIs
    # ==========================================================

    async def generate_router(self, prompt: str) -> str:
        return await self._generate_internal(
            prompt=prompt,
            model_name=self.router_model,
            system_prompt=self.prompt_registry.get_router_prompt(),
            log_tag=LogTag.ROUTER,
        )

    async def generate_sql(self, prompt: str, premium: bool = False) -> str:
        model = self.sql_premium_model if premium else self.sql_model
        return await self._generate_internal(
            prompt=prompt,
            model_name=model,
            system_prompt=self.prompt_registry.get_sql_prompt(),
            log_tag=LogTag.SQL_GENERATION,
        )

    async def generate_answer(self, prompt: str) -> str:
        return await self._generate_internal(
            prompt=prompt,
            model_name=self.answer_model,
            system_prompt=self.prompt_registry.get_answer_prompt(),
            log_tag=LogTag.ANSWER,
        )

    async def generate_answer_chitchat(self, prompt: str) -> str:
        return await self._generate_internal(
            prompt=prompt,
            model_name=self.chitchat_model,
            system_prompt=self.prompt_registry.get_chitchat_prompt(),
            log_tag=LogTag.CHIT_CHAT,
        )

    # ==========================================================
    # 🔹 Core LLM Call
    # ==========================================================

    async def _generate_internal(
        self,
        prompt: str,
        model_name: str,
        system_prompt: str,
        log_tag: str,
    ) -> str:

        request_id = get_request_id()

        logger.info(
            "LLM generate start",
            extra={
                "tag": log_tag,
                "request_id": request_id,
                "model": model_name,
                "prompt_length": len(prompt),
            },
        )

        start = time.time()

        try:
            provider = self.llm_registry.get_llm(model_name)

            messages: List[ChatMessage] = [
                ChatMessage(role="system", content=system_prompt),
                ChatMessage(role="user", content=prompt),
            ]

            response_text = await provider.generate(messages)

        except Exception as e:
            logger.error("LLM call failed: %s", repr(e))
            raise

        latency_ms = int((time.time() - start) * 1000)

        logger.info(
            "LLM generate success",
            extra={
                "tag": log_tag,
                "request_id": request_id,
                "latency_ms": latency_ms,
            },
        )

        return response_text
