# llmServer/app/services/retrieval/engine.py

from app.services.rerank_service import RerankService
from app.infra.vector.vector_repository import VectorRepository
import logging

logger = logging.getLogger(__name__)


class RetrievalEngine:


    def __init__(
        self,
        vector_repository:VectorRepository,
        rerank_service: RerankService,
        bm25_index=None,
    ):
        self.vector_repository = vector_repository
        self.rerank_service = rerank_service
        self.bm25 = bm25_index

    # ─────────────────────────────
    # Fewshot Hybrid
    # ─────────────────────────────
    async def retrieve_fewshot(self, question: str, n: int = 3):

        try:
            vec_results = await self.vector_repository.search_by_text(
                collection_name="fewshot",
                query_text=question,
                top_k=n * 5,
            )
            if not vec_results:
                return ""

            vec_docs = [r[0] for r in vec_results]
            vec_metas = [r[1] for r in vec_results]
            vec_scores = {r[0]: 1 - r[2] for r in vec_results}

            bm25_scores = {}
            bm25_meta_map = {}

            if self.bm25:
                try:
                    bm25_results = self.bm25.search(question, top_k=n * 5)
                    for item in bm25_results:
                        bm25_scores[item["doc"]] = item["score"]
                        bm25_meta_map[item["doc"]] = item["meta"]
                except Exception:
                    logger.warning("BM25 실패 → 벡터-only fallback")

            doc_meta_map = {d: m for d, m in zip(vec_docs, vec_metas)}
            doc_meta_map.update(bm25_meta_map)

            merged = {}
            all_docs = set(vec_docs) | set(bm25_scores.keys())

            for doc in all_docs:
                v = vec_scores.get(doc, 0)
                b = bm25_scores.get(doc, 0)
                merged[doc] = v * 0.6 + b * 0.4

            pre_top = sorted(
                merged,
                key=merged.get,
                reverse=True
            )[: n * 3]

            pre_metas = [doc_meta_map.get(d, {}) for d in pre_top]

            final_docs, final_metas = await self.rerank_service.rerank(
                question,
                pre_top,
                pre_metas,
                top_n=n,
                with_scores=False
            )

            return "\n---\n".join(
                f"Q: {d}\nSQL: {m.get('sql','')}"
                for d, m in zip(final_docs, final_metas)
            )

        except Exception:
            logger.exception("Hybrid 실패 → 벡터 fallback")

            vec_results = await self.vector_repository.search_by_text(
                collection_name="fewshot",
                query_text=question,
                top_k=n,
            )

            return "\n---\n".join(
                f"Q: {r[0]}\nSQL: {r[1].get('sql','')}"
                for r in vec_results
            )

    # ─────────────────────────────
    # Generic Strategy Retrieval
    # ─────────────────────────────
    async def retrieve(self, strategy, query: str, n: int = 3):

        results = await self.vector_repository.search_by_text(
            collection_name=strategy.collection,
            query_text=query,
            top_k=n * 3,
        )
        # 디버깅용
        # print(f"strategy: {strategy.collection} result: {results} ")
        if not results:
            return ""

        docs = [r[0] for r in results]
        metas = [r[1] for r in results]

        final_docs, final_metas, scores = (
            await self.rerank_service.rerank(
                query,
                docs,
                metas,
                top_n=n,
            )
        )
        # 디버깅용
        # print("RERANK SCORES:", scores)
        # print("THRESHOLD:", strategy.threshold)
        filtered = [
            (d, m)
            for d, m, s in zip(final_docs, final_metas, scores)
            if s >= strategy.threshold
        ]
        
        # 🔥 최소 1개는 항상 반환
        if not filtered and final_docs:
            filtered = [(final_docs[0], final_metas[0])]

        docs_f, metas_f = zip(*filtered)

        return strategy.format(docs_f, metas_f)