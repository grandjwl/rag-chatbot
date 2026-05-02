# llmServer/app/services/test/flow/test_refine_flow.py
# PYTHONPATH=. python -m app.services.test.flow.test_refine_flow

import asyncio

from app.core.config import settings
from app.infra.network.cloudflare import CloudflareTunnel
from app.dependency import get_container


async def main():

    # 🔥 Cloudflare는 외부 환경이므로 여기서 관리
    tunnel = CloudflareTunnel(
        hostname=settings.CLOUDFLARE_HOSTNAME,
        db_host=settings.POSTGRES_HOST,
        db_port=settings.POSTGRES_PORT,
    )
    tunnel.start()

    try:
        container = await get_container()
        refine_service = container.refine_service

        questions = [
            "티아이 제품 ADS62C15IRGCT 재고 알려줘",
            "마우저에서 판매한 ADS62C15IRGCT 재고",
            "ADS62C15IRGTT 재고 알려줘",
        ]

        for question in questions:
            result = await refine_service.resolve(question)
            print(result)

    finally:
        tunnel.stop()


if __name__ == "__main__":
    asyncio.run(main())