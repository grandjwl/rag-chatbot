# llmServer/app/services/test/flow/test_sql_gen_flow_without_memory.py
# PYTHONPATH=. python -m app.services.test.flow.test_sql_gen_flow_without_memory

import asyncio
from app.dependency import get_container
from app.infra.network.cloudflare import CloudflareTunnel
from app.core.config import settings


async def run_no_memory_pipeline():

    print("\n🚀 Pipeline 테스트 (Memory 없이)\n")

    tunnel = CloudflareTunnel(
        hostname=settings.CLOUDFLARE_HOSTNAME,
        db_host=settings.POSTGRES_HOST,
        db_port=settings.POSTGRES_PORT,
    )
    tunnel.start()

    container = await get_container()

    llm_service = container.llm_service
    router_service = container.router_service

    # 테스트 질문
    question = "23년은?"

    print("입력 질문:", question)

    # 1️⃣ refine 없이 그대로
    refined_q = question

    # 2️⃣ router
    routed = await router_service.route(refined_q)

    # 3️⃣ SQL 생성
    sql_result = await llm_service.generate_sql(refined_q)

    print("Refined:", refined_q)
    print("Router 결과:", routed)
    print("SQL 생성 결과:")
    print(sql_result)

    print("\n🎉 Memory 없는 파이프라인 테스트 완료\n")


if __name__ == "__main__":
    asyncio.run(run_no_memory_pipeline())
