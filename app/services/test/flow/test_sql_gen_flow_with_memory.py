# llmServer/app/services/test/flow/test_sql_gen_flow_with_memory.py
# PYTHONPATH=. python -m app.services.test.flow.test_sql_gen_flow_with_memory

import asyncio
from app.dependency import get_container
from app.infra.network.cloudflare import CloudflareTunnel
from app.core.config import settings


def inject_memory_to_question(question: str, memory: dict) -> str:

    if not memory:
        return question

    q = question

    PRONOUN_MAP = {
        "이 제품": "last_product",
        "해당 제품": "last_product",
        "그 제품": "last_product",
    }

    for pronoun, key in PRONOUN_MAP.items():
        if pronoun in q and memory.get(key):
            q = q.replace(pronoun, f"'{memory[key]}'")

    if "같은 기간" in q and memory.get("last_year"):
        q += f" ({memory['last_year']}년 기준)"

    return q


async def run_memory_pipeline():

    print("\n🚀 Pipeline 테스트 (Memory + SQLGen 전체)\n")

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

    question = "2024년 총 매출액 얼마야?"

    print("입력 질문:", question)

    # 1️⃣ Memory 재조립
    rebuilt_q, structured_memory = await memory_service.inject_context(
        user_id=user_id,
        question=question,
    )

    # 2️⃣ structured memory 적용
    final_q = inject_memory_to_question(rebuilt_q, structured_memory)

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

    print("\n🎉 Memory + SQLGen 파이프라인 테스트 완료\n")


if __name__ == "__main__":
    asyncio.run(run_memory_pipeline())
