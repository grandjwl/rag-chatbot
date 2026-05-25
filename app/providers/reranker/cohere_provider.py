# llmServer/app/providers/reranker/cohere_provider.py

import asyncio
import logging
import time
from typing import List
import cohere
from app.providers.reranker.base import BaseRerankerProvider
from app.core.logging.request_context import get_request_id

logger = logging.getLogger(__name__)


class CohereRerankerProvider(BaseRerankerProvider):

    def __init__(self, api_key: str, model_name: str = "rerank-v3.5"):
        self.model_name = model_name
        self.client = cohere.ClientV2(api_key)
        logger.info(f"Cohere Reranker initialized with model: {self.model_name}")

    async def score(self, query: str, docs: List[str]) -> List[float]:

        if not docs:
            return []

        request_id = get_request_id()
        start = time.time()
        loop = asyncio.get_running_loop()

        try:
            response = await loop.run_in_executor(
                None,
                lambda: self.client.rerank(
                    model=self.model_name,
                    query=query,
                    documents=docs,
                    top_n=len(docs),
                )
            )

            scores = [0.0] * len(docs)
            for result in response.results:
                scores[result.index] = result.relevance_score

            logger.info(
                "api",
                extra={
                    "kind":   "RERANK",
                    "req":    request_id,
                    "model":  self.model_name,
                    "lat_ms": int((time.time() - start) * 1000),
                    "docs":   len(docs),
                },
            )

            return scores

        except Exception as e:
            logger.error(
                "api",
                extra={
                    "kind":   "RERANK",
                    "req":    request_id,
                    "model":  self.model_name,
                    "lat_ms": int((time.time() - start) * 1000),
                    "error":  type(e).__name__,
                },
            )
            raise RuntimeError("Rerank failed") from e