# llmServer/services/rerank_service.py

import logging
from typing import List, Dict, Any
from app.providers.reranker.base import BaseRerankerProvider

logger = logging.getLogger(__name__)


class RerankService:
    def __init__(self, reranker: BaseRerankerProvider):
        self.reranker = reranker

    async def rerank(
        self,
        query: str,
        docs: list[str],
        metas: List[Dict[str, Any]],
        top_n: int = 3,
        with_scores: bool =True,
    ):
        if not docs:
            return ([], [], []) if with_scores else ([], [])

        try:
            scores = await self.reranker.score(query, docs)

            ranked = sorted(
                zip(scores, docs, metas),
                key=lambda x: x[0],
                reverse=True,
            )

            top = ranked[:top_n]

            final_docs = [d for s, d, m in top]
            final_metas = [m for s, d, m in top]
            final_scores = [s for s, d, m in top]

            if with_scores:
                return final_docs, final_metas, final_scores
            return final_docs, final_metas

        except Exception as e:
            # 에러 로그 기록
            logger.error(f"Reranking failed: {str(e)}. Falling back to original order.")

            # fallback 정책
            fallback_docs = docs[:top_n]
            fallback_metas = metas[:top_n]
            fallback_scores = [1.0] * len(fallback_docs)

            if with_scores:
                return fallback_docs, fallback_metas, fallback_scores
            return fallback_docs, fallback_metas
