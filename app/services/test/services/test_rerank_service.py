# llmServer/app/services/test/services/test_rerank_service.py
# PYTHONPATH=. python -m app.services.test.services.test_rerank_service

import time
import asyncio

from app.core.logging.logging_config import setup_logging
from app.core.logging.request_context import generate_request_id, set_request_id

from app.services.rerank_service import RerankService
from app.providers.registry import ProviderRegistry
from app.providers.reranker.cohere_provider import CohereRerankerProvider
from app.core.config import settings


async def main():

    # 🔥 로깅 초기화
    # setup_logging()

    # 🔥 request_id 세팅
    # request_id = generate_request_id()
    # # set_request_id(request_id)

    print("\n🚀 RerankService 통합 테스트 시작")
    # print("request_id:", request_id, "\n")

    if not settings.COHERE_API_KEY:
        raise ValueError("COHERE_API_KEY가 설정되지 않았습니다.")

    # 1️⃣ Registry 생성
    registry = ProviderRegistry()

    # 2️⃣ Provider 생성 및 등록
    rerank_provider = CohereRerankerProvider(
        api_key=settings.COHERE_API_KEY,
        model_name=settings.COHERE_MODEL
    )

    registry.register_reranker(settings.COHERE_MODEL, rerank_provider)

    # 3️⃣ Service 생성
    rerank_service = RerankService(
        reranker=registry.get_reranker(settings.COHERE_MODEL)
    )

    # 4️⃣ 테스트 데이터
    query = "ABC123 제품의 최근 3개월 매출을 알려줘"

    docs = [
        "ABC123 제품의 2022년 연간 매출은 12억원입니다.",
        "ABC123 제품의 최근 3개월 매출은 3억 2천만원입니다.",
        "XYZ999 제품의 최근 3개월 매출은 5억원입니다.",
        "ABC123 제품의 분기별 매출 통계 자료입니다.",
        "매출 집계 기준 및 회계 처리 방법 설명 문서입니다."
    ]

    metas = [{"id": i} for i in range(len(docs))]

    # 5️⃣ 실행
    # start = time.time()

    final_docs, final_metas, final_scores = await rerank_service.rerank(
        query=query,
        docs=docs,
        metas=metas,
        top_n=3,
        with_scores=True,
    )

    # latency = (time.time() - start) * 1000

    # print(f"\n⏱ Rerank 처리 시간: {latency:.2f} ms\n")

    print("📊 Reranked Results:")
    for d, m, s in zip(final_docs, final_metas, final_scores):
        print(f"[{s:.4f}] - {d} | meta={m}")


if __name__ == "__main__":
    asyncio.run(main())