# /llmServer/app/providers/llm/azure_openai_llm_provider.py

import logging
import time
import asyncio
from openai import AzureOpenAI

from app.providers.llm.base import BaseLLMProvider
from app.schemas.chat import ChatMessage

from app.core.logging.logging_tags import LogTag
from app.core.logging.request_context import get_request_id
# from app.core.logging.cost_calculator import calculate_openai_cost

logger = logging.getLogger(__name__)


class AzureOpenAILLMProvider(BaseLLMProvider):

    def __init__(
        self,
        api_key: str,
        azure_endpoint: str,
        deployment_name: str,
        api_version: str = "2023-12-01-preview",
    ):
        self.client = AzureOpenAI(
            api_key=api_key,
            azure_endpoint=azure_endpoint,
            api_version=api_version,
        )
        self.deployment = deployment_name

    async def generate(self, messages: list[ChatMessage]):

        request_id = get_request_id()
        start = time.time()

        loop = asyncio.get_running_loop()

        try:
            response = await loop.run_in_executor(
                None,
                lambda: self.client.chat.completions.create(
                    model=self.deployment,  # ⚠️ 모델명이 아니라 deployment name
                    messages=self._convert_to_openai(messages),
                    temperature=0,
                ),
            )
        except Exception:
            logger.exception("Azure OpenAI API call failed")
            raise

        latency_ms = int((time.time() - start) * 1000)

        usage = getattr(response, "usage", None)
        prompt_tokens = getattr(usage, "prompt_tokens", None)
        completion_tokens = getattr(usage, "completion_tokens", None)
        total_tokens = getattr(usage, "total_tokens", None)

        cost = calculate_openai_cost(prompt_tokens, completion_tokens)

        logger.info(
            "Azure OpenAI API call",
            extra={
                "tag": LogTag.API_LLM,
                "request_id": request_id,
                "model": self.deployment,
                "latency_ms": latency_ms,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "cost_usd": cost,
            },
        )

        return response.choices[0].message.content

    def _convert_to_openai(self, messages: list[ChatMessage]):

        return [
            {
                "role": msg.role,
                "content": msg.content,
            }
            for msg in messages
        ]