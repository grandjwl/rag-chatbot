# llmServer/agent/test/test_graph.py
# PYTHONPATH=. python -m app.agent.test.test_graph

import asyncio
import time

from app.dependency import get_container
from app.agent.agent_graph import build_graph
from app.infra.network.cloudflare import CloudflareTunnel
from app.core.config import settings
from app.core.logging.logging_config import setup_logging

setup_logging()

async def run_full_pipeline():

    print("\n🚀 FULL AGENT GRAPH TEST START\n")

    # ---------------------------------------
    # Cloudflare 터널 시작 (DB 접근용)
    # ---------------------------------------

    tunnel = CloudflareTunnel(
        hostname=settings.CLOUDFLARE_HOSTNAME,
        db_host=settings.POSTGRES_HOST,
        db_port=settings.POSTGRES_PORT,
    )
    tunnel.start()

    # ---------------------------------------
    # Container 로딩
    # ---------------------------------------

    container = await get_container()

    # ---------------------------------------
    # Graph 생성
    # ---------------------------------------

    graph = build_graph(container)

    # ---------------------------------------
    # 초기 State 구성
    # ---------------------------------------

    initial_state = {
        "user_id": "graph_test_user",
        "session_id": "sess_001",
        "question": "2023년 매출액 월별로 알려줘",
        "retry_count": 0,
        "error_history": [],
        "start_time": time.time(),
    }

    print("📝 입력 질문:", initial_state["question"])

    # ---------------------------------------
    # 실행
    # ---------------------------------------

    result = await graph.ainvoke(initial_state)

    # ---------------------------------------
    # 결과 출력
    # ---------------------------------------

    print("\n🎉 최종 Answer:\n")
    print(result.get("final_answer"))

    print("\n📊 최종 State 일부:")
    print(" - retry_count:", result.get("retry_count"))
    print(" - error_type:", result.get("error_type"))
    print(" - result_anomalies:", result.get("result_anomalies"))
    print(" - sql_query:", result.get("sql_query"))

    print("\n✅ FULL AGENT GRAPH TEST END\n")


if __name__ == "__main__":
    asyncio.run(run_full_pipeline())