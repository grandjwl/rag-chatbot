# llmServer/app/providers/reranker/bge_reranker_provider.py

import logging
from typing import List
from app.providers.reranker.base import BaseRerankerProvider

logger = logging.getLogger(__name__)


class BGERerankerProvider(BaseRerankerProvider):

    def __init__(self):
        from FlagEmbedding import FlagReranker

        self.model = FlagReranker(
            "upskyy/bge-reranker-v2-m3-ko",
            use_fp16=True,
        )

    def score(self, query: str, docs: List[str]) -> List[float]:

        if not docs:
            return []

        pairs = [[query, doc] for doc in docs]
        scores = self.model.compute_score(pairs, normalize=True)

        if isinstance(scores, (int, float)):
            scores = [scores]

        return scores
