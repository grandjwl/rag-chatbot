# llmServer/app/services/retrieval/engine.py

from app.services.rerank_service import RerankService
from app.infra.vector.vector_repository import VectorRepository
from app.core.logging import flow_logger as flow
import logging

logger = logging.getLogger(__name__)

RRF_K = 60


class RetrievalEngine:

    def __init__(
        self,
        vector_repository: VectorRepository,
        rerank_service: RerankService,
        bm25_indexes: dict = None,
    ):
        self.vector_repository = vector_repository
        self.rerank_service = rerank_service
        self.bm25_indexes = bm25_indexes or {}

    # ─────────────────────────────
    # RRF 병합
    # ─────────────────────────────
    def _rrf_merge(self, vec_results, bm25_results) -> dict:
        vec_rank = {r[0]: i + 1 for i, r in enumerate(sorted(vec_results, key=lambda x: x[2]))}
        bm25_rank = {item["doc"]: i + 1 for i, item in enumerate(bm25_results)}

        all_docs = set(vec_rank) | set(bm25_rank)
        default = len(all_docs) + RRF_K

        return {
            doc: 1 / (RRF_K + vec_rank.get(doc, default)) + 1 / (RRF_K + bm25_rank.get(doc, default))
            for doc in all_docs
        }

    # ─────────────────────────────
    # 공통 하이브리드 검색
    # ─────────────────────────────
    async def _hybrid_search(self, collection_name: str, query: str, fetch_k: int):
        vec_results = await self.vector_repository.search_by_text(
            collection_name=collection_name,
            query_text=query,
            top_k=fetch_k,
        )
        if not vec_results:
            return [], {}

        doc_meta_map = {r[0]: r[1] for r in vec_results}

        bm25 = self.bm25_indexes.get(collection_name)
        bm25_results = []
        if bm25:
            try:
                bm25_results = bm25.search(query, top_k=fetch_k)
                for item in bm25_results:
                    doc_meta_map.setdefault(item["doc"], item["meta"])
            except Exception:
                logger.warning(f"BM25 실패({collection_name}) → 벡터-only fallback")

        if bm25_results:
            merged = self._rrf_merge(vec_results, bm25_results)
        else:
            merged = {r[0]: 1 - r[2] for r in vec_results}

        return merged, doc_meta_map

    # ─────────────────────────────
    # Fewshot Hybrid
    # ─────────────────────────────
    async def retrieve_fewshot(self, question: str, n: int = 1):
        try:
            merged, doc_meta_map = await self._hybrid_search("fewshot", question, n * 5)
            if not merged:
                flow.log_rag_scores("fewshot", 0.0)
                return ""

            pre_top = sorted(merged, key=merged.get, reverse=True)[: n * 3]
            pre_metas = [doc_meta_map.get(d, {}) for d in pre_top]

            final_docs, final_metas, scores = await self.rerank_service.rerank(
                question, pre_top, pre_metas, top_n=n
            )

            flow.log_rag_scores("fewshot", max(scores) if scores else 0.0)

            return "\n---\n".join(
                f"Q: {d}\nSQL: {m.get('sql', '')}"
                for d, m in zip(final_docs, final_metas)
            )

        except Exception as e:
            from app.infra.vector.exceptions import VectorCollectionNotFound
            if isinstance(e, VectorCollectionNotFound):
                flow.log_rag_scores("fewshot", 0.0)
                return ""
            logger.exception("Fewshot hybrid 실패 → 벡터 fallback")
            try:
                vec_results = await self.vector_repository.search_by_text(
                    collection_name="fewshot", query_text=question, top_k=n
                )
                return "\n---\n".join(
                    f"Q: {r[0]}\nSQL: {r[1].get('sql', '')}" for r in vec_results
                )
            except Exception:
                return ""

    # ─────────────────────────────
    # Entities (refine용 raw 결과 반환)
    # ─────────────────────────────
    async def retrieve_entities(self, question: str, top_k: int = 5):
        try:
            merged, doc_meta_map = await self._hybrid_search("refine_store", question, top_k * 3)
            if not merged:
                return []

            pre_top = sorted(merged, key=merged.get, reverse=True)[: top_k * 2]
            pre_metas = [doc_meta_map.get(d, {}) for d in pre_top]

            final_docs, final_metas, scores = await self.rerank_service.rerank(
                question, pre_top, pre_metas, top_n=top_k
            )

            flow.log_rag_scores("refine_store", max(scores) if scores else 0.0)
            return list(zip(final_docs, final_metas, scores))

        except Exception:
            logger.exception("retrieve_entities 실패")
            flow.log_rag_scores("refine_store", 0.0)
            return []

    # ─────────────────────────────
    # Generic Strategy Retrieval (하이브리드 통일)
    # ─────────────────────────────
    async def retrieve(self, strategy, query: str, n: int = None):
        top_n = n if n is not None else strategy.n
        try:
            merged, doc_meta_map = await self._hybrid_search(strategy.collection, query, top_n * 3)
            if not merged:
                return ""

            pre_top = sorted(merged, key=merged.get, reverse=True)[: top_n * 3]
            pre_metas = [doc_meta_map.get(d, {}) for d in pre_top]

            final_docs, final_metas, scores = await self.rerank_service.rerank(
                query, pre_top, pre_metas, top_n=top_n
            )

            if scores:
                flow.log_rag_scores(strategy.collection, max(scores))

            filtered = [
                (d, m)
                for d, m, s in zip(final_docs, final_metas, scores)
                if s >= strategy.threshold
            ]

            if not filtered and final_docs:
                filtered = [(final_docs[0], final_metas[0])]

            docs_f, metas_f = zip(*filtered)
            return strategy.format(docs_f, metas_f)

        except Exception:
            logger.exception(f"Retrieve 실패({strategy.collection})")
            return ""
