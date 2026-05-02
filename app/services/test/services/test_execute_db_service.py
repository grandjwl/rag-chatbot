# llmServer/app/services/test/services/test_execute_db_service.py
# PYTHONPATH=. python -m app.services.test.services.test_execute_db_service

import asyncio
from app.dependency import get_container


async def run_test():

    container = await get_container()

    service = container.execute_db_service

    print("\n🚀 ExecuteDBService 테스트 시작\n")

    # ----------------------------
    # 1️⃣ 정상 쿼리
    # ----------------------------
    state = {
        "sql_query": "SELECT COUNT(*) FROM sales_orders",
        "retry_count": 0,
        "error_history": [],
    }

    result = await service.execute(state)

    print("정상 실행 결과:")
    print(result)
    print()

    # ----------------------------
    # 2️⃣ SELECT * 금지
    # ----------------------------
    state2 = {
        "sql_query": "SELECT * FROM sales_orders",
        "retry_count": 0,
        "error_history": [],
    }

    result2 = await service.execute(state2)

    print("SELECT * 차단 결과:")
    print(result2)
    print()

    # ----------------------------
    # 3️⃣ 존재하지 않는 테이블
    # ----------------------------
    state3 = {
        "sql_query": "SELECT COUNT(*) FROM fake_table",
        "retry_count": 0,
        "error_history": [],
    }

    result3 = await service.execute(state3)

    print("존재하지 않는 테이블 결과:")
    print(result3)
    print()

    print("🎉 테스트 완료\n")


if __name__ == "__main__":
    asyncio.run(run_test())
