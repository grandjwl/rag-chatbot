# llmServer/app/providers/reranker/cohere_provider.py

import asyncio
import logging
from typing import List
import cohere
from app.providers.reranker.base import BaseRerankerProvider

logger = logging.getLogger(__name__)


class CohereRerankerProvider(BaseRerankerProvider):

    def __init__(self, api_key: str, model_name: str = "rerank-v3.5"):
        self.model_name = model_name
        self.client = cohere.ClientV2(api_key)
        logger.info(f"Cohere Reranker initialized with model: {self.model_name}")

    async def score(self, query: str, docs: List[str]) -> List[float]:

        if not docs:
            return []

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

            return scores

        except Exception as e:
            logger.exception("Cohere Reranking API error")
            raise RuntimeError("Rerank failed") from e