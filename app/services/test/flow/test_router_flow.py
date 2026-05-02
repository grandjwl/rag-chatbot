# llmServer/app/services/test/flow/test_router_flow.py
# PYTHONPATH=. python -m app.services.test.flow.test_router_flow

import asyncio

from app.dependency import get_container
from app.infra.network.cloudflare import CloudflareTunnel
from app.core.config import settings


async def main():

    tunnel = CloudflareTunnel(
        hostname=settings.CLOUDFLARE_HOSTNAME,
        db_host=settings.POSTGRES_HOST,
        db_port=settings.POSTGRES_PORT,
    )
    tunnel.start()

    try:
        container = await get_container()

        refine_service = container.refine_service
        router_service = container.router_service

        # questions = [
        #     # Rule 기반 INVENTORY
        #     "티아이 제품 ADS62C15IRGCT 재고 알려줘",

        #     # Rule 기반 TECH_SALES
        #     "ADS62C15IRGCT 전압 스펙 알려줘",

        #     # Rule 안 걸리는 케이스 (LLM fallback 유도)
        #     "이 제품 괜찮은가요?",
        # ]

        questions = [
            "안녕?",
            "이거 어떻게 생각해?",
            "추천해줘",
        ]
        for question in questions:
            print("\n" + "=" * 80)
            print("🔎 원본 질문:", question)

            # 1️⃣ Refine 정제
            refined = await refine_service.resolve(question)
            refined_question = refined["refined_question"]

            print("🔧 정제 질문:", refined_question)

            # 2️⃣ Router
            intent = await router_service.route(refined_question)

            print("🧭 라우팅 결과:", intent)

    finally:
        tunnel.stop()


if __name__ == "__main__":
    asyncio.run(main())