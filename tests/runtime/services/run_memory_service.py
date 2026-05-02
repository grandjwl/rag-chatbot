# ============================================================
# File
#   tests/runtime/services/run_memory_service.py
#
# Run
#   PYTHONPATH=. python -m tests.runtime.services.run_memory_service
#
# 목적
#   MemoryService 실제 동작 확인 (Runtime Debug Test)
#
# 테스트 범위
#   1️⃣ Conversation 저장
#   2️⃣ load_recent
#   3️⃣ follow-up 질문 재구성
#   4️⃣ pronoun resolution
#   5️⃣ structured memory 추출
# ============================================================

import asyncio

from app.services.memory_service import MemoryService
from tests.fakes.fake_conversation_repository import FakeConversationRepository


async def run_memory_service_runtime_test():

    print("\n🚀 MemoryService Runtime Test 시작\n")

    # ---------------------------------------------------------
    # Setup
    # ---------------------------------------------------------

    repo = FakeConversationRepository(rows=[])
    memory_service = MemoryService(repo)

    user_id = "runtime_user"
    session_id = "runtime_session"

    # ---------------------------------------------------------
    # Step 1: MemoryService를 통한 대화 저장 - 이전 대화 저장
    # ---------------------------------------------------------

    print("📌 Step 1: MemoryService.save_conversation 테스트")

    await memory_service.save_conversation(
        user_id=user_id,
        session_id=session_id,
        question="2024년 매출은?",
        refined_question="2024년 매출은?",
        response_data={"answer": "제품 ABC123 매출은 1000입니다."},
        final_sql="SELECT * FROM sales WHERE year=2024",
        refine_corrections={},
        execution_time_ms=20,
    )

    print("✅ 대화 저장 완료\n")

    # ---------------------------------------------------------
    # Step 2: 최근 대화 조회
    # ---------------------------------------------------------

    print("📌 Step 2: load_recent 테스트")

    history = await memory_service.load_recent(user_id)

    print(f"조회된 대화 수: {len(history)}")

    for h in history:
        print(" - question:", h.get("question"))
        print(" - response:", h.get("response_data"))

    print()

    # ---------------------------------------------------------
    # Step 3: Follow-up 질문 재구성
    # ---------------------------------------------------------

    print("📌 Step 3: follow-up 질문 테스트")

    question = "23년은?"

    refined_q, structured_memory = await memory_service.inject_context(
        user_id=user_id,
        question=question,
    )

    print("입력 질문:", question)
    print("재구성 질문:", refined_q)
    print("structured_memory:", structured_memory)
    print()

    # ---------------------------------------------------------
    # Step 4: Pronoun Resolution 테스트
    # ---------------------------------------------------------

    print("📌 Step 4: 대명사 치환 테스트")

    await memory_service.save_conversation(
        user_id=user_id,
        session_id=session_id,
        question="ABC123 제품 매출은?",
        refined_question="ABC123 제품 매출 조회",
        response_data="제품 ABC123 매출은 120000원입니다.",
        final_sql="SELECT * FROM sales WHERE part_number='ABC123'",
        refine_corrections={},
        execution_time_ms=10,
    )

    pronoun_q = "이 제품은?"

    refined_q2, structured_memory2 = await memory_service.inject_context(
        user_id=user_id,
        question=pronoun_q,
    )

    print("입력 질문:", pronoun_q)
    print("재구성 질문:", refined_q2)
    print("structured_memory:", structured_memory2)
    print()

    print("🎉 MemoryService Runtime Test 완료\n")


if __name__ == "__main__":
    asyncio.run(run_memory_service_runtime_test())