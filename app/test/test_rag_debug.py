# app/test/test_rag_debug.py
# PYTHONPATH=. python -m app.test.test_rag_debug

import asyncio
from app.container.rag_debug_container import RAGDebugContainer
from app.services.retrieval.strategies import (
    # SynonymStrategy,
    BiztermStrategy,
    TableSchemaStrategy,
    # ErrorStrategy,
    # KeywordStrategy,
)


async def debug_strategy(engine, strategy, question, top_k=5):

    print("\n==============================")
    print(f"🔍 Strategy: {strategy.collection}")
    print("==============================")

    # 1️⃣ raw vector search
    vec_results = await engine.vector_repository.search_by_text(
        collection_name=strategy.collection,
        query_text=question,
        top_k=top_k,
    )

    print("\n📌 Raw Vector Results:")
    for doc, meta, distance in vec_results:
        similarity = 1 - distance
        print(f"\nScore: {similarity:.4f}")
        print("Doc:", doc[:200])
        print("Meta:", meta)

    # 2️⃣ rerank
    docs = [r[0] for r in vec_results]
    metas = [r[1] for r in vec_results]

    final_docs, final_metas, scores = await engine.rerank_service.rerank(
        question,
        docs,
        metas,
        top_n=top_k,
    )

    print("\n📌 Rerank Results:")
    for d, m, s in zip(final_docs, final_metas, scores):
        print(f"\nRerank Score: {s:.4f}")
        print("Doc:", d[:200])
        print("Meta:", m)


async def main():

    container = RAGDebugContainer()
    engine = container.retrieval_engine

    question = "2023년 매출액 월별 집계"

    print("\n🚀 RAG DEBUG START")
    print("Question:", question)

    strategies = [
        # SynonymStrategy(),
        BiztermStrategy(),
        # SchemaStrategy(),
        # KeywordStrategy(),
    ]

    for strategy in strategies:
        await debug_strategy(engine, strategy, question, top_k=5)

    print("\n✅ DEBUG END")


if __name__ == "__main__":
    asyncio.run(main())