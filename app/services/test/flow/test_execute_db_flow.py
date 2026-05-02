# llmServer/app/services/test/flow/test_execute_db_flow.py
# PYTHONPATH=. python -m app.services.test.flow.test_execute_db_flow

import asyncio
from app.dependency import get_container
from app.infra.network.cloudflare import CloudflareTunnel
from app.core.config import settings


async def run_memory_pipeline():

    print("\n🚀 Pipeline 테스트 (Memory + SQLGen + ExecuteDB 전체)\n")

    tunnel = CloudflareTunnel(
        hostname=settings.CLOUDFLARE_HOSTNAME,
        db_host=settings.POSTGRES_HOST,
        db_port=settings.POSTGRES_PORT,
    )
    tunnel.start()

    container = await get_container()

    memory_service = container.memory_service
    router_service = container.router_service
    sql_generate_service = container.sql_generate_service

    user_id = "memory_test_user"

    question = "2024년 매출액 월별로 알려줘."

    print("입력 질문:", question)

    # 1️⃣ Memory 재조립
    rebuilt_q, structured_memory = await memory_service.inject_context(
        user_id=user_id,
        question=question,
    )

    # 2️⃣ structured memory 적용
    final_q = rebuilt_q
    # 3️⃣ Router
    routed = await router_service.route(final_q)

    # 4️⃣ state 구성 (🔥 핵심)
    state = {
        "refined_question": final_q,
        "intent": routed,
        "error_history": [],
        "synonym_hint": "",
    }

    # 5️⃣ SQL 생성
    sql_result = await sql_generate_service.generate(state)

    print("\nMemory 재조립:", rebuilt_q)
    print("Memory 적용 후:", final_q)
    print("Router 결과:", routed)
    print("\n📌 SQL 생성 결과:")
    print(sql_result)
    db_result = await container.execute_db_service.execute(
        {
            "sql_query": sql_result["sql_query"],
            "retry_count": 0,
            "error_history": [],
        }
    )

    print("\nDB 실행 결과:")
    for k, v in db_result.items():
        print(f"  {k}: {v}")

    print("\n🎉 Memory + SQLGen + execute_db 파이프라인 테스트 완료\n")


if __name__ == "__main__":
    asyncio.run(run_memory_pipeline())
