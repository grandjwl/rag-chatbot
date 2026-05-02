# llmServer/app/services/test/services/test_memory_service.py
# PYTHONPATH=. python -m app.services.test.services.test_memory_service

import asyncio
from datetime import datetime

from app.dependency import get_container
from app.infra.network.cloudflare import CloudflareTunnel
from app.core.config import settings


async def run_memory_full_test():

    print("\n🚀 MemoryService 통합 런타임 테스트 시작\n")

    tunnel = CloudflareTunnel(
        hostname=settings.CLOUDFLARE_HOSTNAME,
        db_host=settings.POSTGRES_HOST,
        db_port=settings.POSTGRES_PORT,
    )
    tunnel.start()

    container = await get_container()

    memory = container.memory_service
    repo = container.conversation_repository

    user_id = "memory_test_user"
    session_id = "memory_test_session"

    print("📌 Step 1: 이전 질문 저장")

    await repo.save(
        user_id=user_id,
        session_id=session_id,
        question="2024년 월별 매출액은?",
        refined_question="2023년도도 그려줘",
        response_data={"answer": "2024년 월별 매출 데이터입니다."},
        final_sql="SELECT EXTRACT(YEAR FROM sale_date)=2024 FROM sales",
        refine_corrections={},
        execution_time_ms=100,
    )

    print("✅ 이전 질문 저장 완료\n")

    print("📌 Step 2: 최근 대화 조회 확인")

    history = await memory.load_recent(user_id=user_id)

    print(f"조회된 개수: {len(history)}")
    for h in history:
        print(" -", h.get("refined_question"))

    print()

    print("📌 Step 3: 후속 질문 문맥 보강 테스트")

    new_question = "23년은?"

    final_q, _ = await memory.inject_context(
        user_id=user_id,
        question=new_question,
    )


    print("입력 질문:", new_question)
    print("최종 적용 결과:", final_q)
    print()

    print("📌 Step 4: 대명사 치환 테스트")

    await repo.save(
        user_id=user_id,
        session_id=session_id,
        question="ABC123 제품 매출은?",
        refined_question="ABC123 제품의 매출을 조회하세요",
        response_data={"answer": "ABC123 제품의 매출은 120000원입니다."},
        final_sql="SELECT * FROM sales WHERE part_number='ABC123'",
        refine_corrections={},
        execution_time_ms=100,
    )

    pronoun_test = "이 제품은?"

    final_q2, _ = await memory.inject_context(
        user_id=user_id,
        question=pronoun_test,
    )


    print("입력 질문:", pronoun_test)
    print("최종 적용 결과:", final_q2)
    print()

    print("🎉 MemoryService 통합 테스트 완료\n")


if __name__ == "__main__":
    asyncio.run(run_memory_full_test())
