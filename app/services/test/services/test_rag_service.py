# llmServer/app/services/test/services/test_rag_service.py
# PYTHONPATH=. python -m app.services.test.services.test_rag_service

import asyncio
import time
from app.infra.network.cloudflare import CloudflareTunnel
from app.core.config import settings
from app.dependency import get_container


async def main():

    tunnel = CloudflareTunnel(
        hostname=settings.CLOUDFLARE_HOSTNAME,
        db_host=settings.POSTGRES_HOST,
        db_port=settings.POSTGRES_PORT,
    )
    
    tunnel.start()

    print("🚀 Container 초기화 중...")
    container = await get_container()

    print("🔍 RAG Service 테스트 시작...\n")
    rag_service = container.rag_service

    # 테스트 질문
    question = "2024년 매출 상위 5개 고객사"

    start = time.perf_counter()
    
    result = await rag_service.build(
        question=question,
        synonym_hint="",
        last_error=""
    )

    elapsed = time.perf_counter() - start

    print("========================================")
    print("📝 질문:")
    print(question)
    print("========================================\n")

    # print("📦 RAG 결과:")
    # print(result if result else "(빈 결과)")
    print("\n========================================")
    print(f"⏱ 실행 시간: {elapsed:.2f}초")
    print("========================================")


if __name__ == "__main__":
    asyncio.run(main())