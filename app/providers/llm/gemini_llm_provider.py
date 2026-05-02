# /llmServer/app/provider/llm/gemini_llm_provider.py

import logging
import time
import asyncio

from google import genai
from google.genai import types
from app.providers.llm.base import BaseLLMProvider
from app.schemas.chat import ChatMessage

from app.core.logging.logging_tags import LogTag
from app.core.logging.request_context import get_request_id
from app.core.logging.cost_calculator import calculate_gemini_cost

logger = logging.getLogger(__name__)

class GeminiLLMProvider(BaseLLMProvider):

    def __init__(self, api_key: str, model_name: str):
        self.client = genai.Client(api_key=api_key)
        self.model = model_name

    async def generate(self, messages: list[ChatMessage]):

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
        except Exception:
            logger.exception("Gemini API call failed")
            raise

        latency_ms = int((time.time() - start) * 1000)
        usage = getattr(response, "usage", None)

        prompt_tokens = getattr(usage, "prompt_tokens", None)
        completion_tokens = getattr(usage, "candidates_tokens", None)
        total_tokens = getattr(usage, "total_tokens", None)

        cost = calculate_gemini_cost(prompt_tokens, completion_tokens)


        logger.info(
            "Gemini API call",
            extra={
                "tag": LogTag.API_LLM,
                "request_id": request_id,
                "model": self.model,
                "latency_ms": latency_ms,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "cost_usd": cost,
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