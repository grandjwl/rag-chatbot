# llmServer/app/provider/embedding/gemini_embedding_provider.py

import asyncio
import logging
import time
from google import genai
from typing import List
from app.providers.embedding.base import BaseEmbeddingProvider
from app.core.logging.request_context import get_request_id

logger = logging.getLogger(__name__)


class GeminiEmbeddingProvider(BaseEmbeddingProvider):

    def __init__(self, api_key: str, model_name: str):
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name

    async def embed(self, texts: List[str]) -> List[List[float]]:

        request_id = get_request_id()
        start = time.time()
        loop = asyncio.get_running_loop()

        response = await loop.run_in_executor(
            None,
            lambda: self.client.models.embed_content(
                model=self.model_name,
                contents=texts,
            )
        )

        logger.info(
            "api",
            extra={
                "kind":   "EMBED",
                "req":    request_id,
                "model":  self.model_name,
                "lat_ms": int((time.time() - start) * 1000),
                "chars":  sum(len(t) for t in texts),
            },
        )

        return [emb.values for emb in response.embeddings]