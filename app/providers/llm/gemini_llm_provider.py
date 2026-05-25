# /llmServer/app/provider/llm/gemini_llm_provider.py

import logging
import time
import asyncio

from google import genai
from google.genai import types
from app.providers.llm.base import BaseLLMProvider
from app.core.types import ChatMessage

from app.core.logging.logging_tags import LogTag
from app.core.logging.request_context import get_request_id
from app.core.logging.cost_calculator import calculate_gemini_cost

logger = logging.getLogger(__name__)

class GeminiLLMProvider(BaseLLMProvider):

    def __init__(self, api_key: str, model_name: str):
        self.client = genai.Client(api_key=api_key)
        self.model = model_name

    async def generate(self, messages: list[ChatMessage], tag: str = "LLM"):

        request_id = get_request_id()
        start = time.time()
        ### 실제 호출 로직

        contents = self._convert_to_gemini(messages)

        loop = asyncio.get_running_loop()

        try:
            response = await loop.run_in_executor(
                None,
                lambda: self.client.models.generate_content(
                    model=self.model,
                    contents=contents,
                )
            )
        except Exception as e:
            lat_ms = int((time.time() - start) * 1000)
            logger.error(
                "api",
                extra={
                    "kind":   tag,
                    "req":    request_id,
                    "model":  self.model,
                    "lat_ms": lat_ms,
                    "error":  type(e).__name__,
                },
            )
            raise

        lat_ms = int((time.time() - start) * 1000)
        usage = getattr(response, "usage_metadata", None)

        in_tokens  = getattr(usage, "prompt_token_count", None)
        out_tokens = getattr(usage, "candidates_token_count", None)
        cost_usd   = calculate_gemini_cost(self.model, in_tokens, out_tokens)

        logger.info(
            "api",
            extra={
                "kind":      tag,
                "req":       request_id,
                "model":     self.model,
                "lat_ms":    lat_ms,
                "in_tokens":  in_tokens,
                "out_tokens": out_tokens,
                "cost_usd":  cost_usd,
            },
        )

        return response.text

    def _convert_to_gemini(self, messages: list[ChatMessage]):
      contents = []
      for msg in messages:
          # Gemini API용 role 변환
          role = msg.role
          if role == "system":
              role = "user"  # 시스템 메시지를 user로 넣는 방법
          elif role == "assistant":
              role = "model"

          contents.append(
              types.Content(
                  role=role,
                  parts=[types.Part(text=msg.content)]              )
          )
      return contents