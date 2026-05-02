# llmServer/app/services/test/flow/test_answer_flow.py
# PYTHONPATH=. python -m app.services.test.flow.test_answer_flow

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

    print("\n🚀 Pipeline 테스트 (Memory + SQLGen + ExecuteDB + ResultValidate 전체)\n")

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

    question = "2023년 매출액 월별로 알려줘."

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

    # 6️⃣ 결과 검증
    validation_result = container.result_validation_service.validate(db_result)
    print("\n🔍 결과 검증 결과:")
    for anomaly in validation_result["result_anomalies"]:
        print(f"  ⚠️ {anomaly}")

    # 6️⃣ 결과 검증

    # 7️⃣ 최종 답변 생성을 위한 state 업데이트 (전체 데이터 합치기)
    # db_result 안에는 rows, explain_meta 등이 이미 들어있습니다.
    answer_state = {
        "intent": routed,                     # Router에서 나온 의도 (INVENTORY 등)
        "question": question,                 # 원래 질문
        "refined_question": final_q,          # 메모리가 주입된 정제된 질문
        "rows": db_result.get("rows"),        # 실제 DB 데이터 (Record 객체 리스트)
        "explain_meta": db_result.get("explain_meta"), # 쿼리 메타 정보 (테이블명 등)
        "db_result": db_result.get("db_result"),       # "SUCCESS" 혹은 에러 메시지
        "result_anomalies": validation_result.get("result_anomalies") # 검증 결과 (비정상 데이터 여부)
    }

    # 8️⃣ 최종 답변 생성 호출
    final_answer = await container.answer_service.generate(answer_state)

    print("\n🎉 최종 답변:")
    print(final_answer)

    print("\n🎉 Memory + SQLGen + ExecuteDB + ResultValidate + Answer 생성 파이프라인 테스트 완료\n")


if __name__ == "__main__":
    asyncio.run(run_memory_pipeline())
