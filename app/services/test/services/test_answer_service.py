# llmServer/app/services/test/services/test_answer_service.py
# PYTHONPATH=. python -m app.services.test.services.test_answer_service
import asyncio
from app.dependency import get_container


async def test_answer_generation():
    print("\n📢 AnswerService 최종 답변 생성 테스트 시작\n")

    container = await get_container()
    answer_service = container.answer_service

    # 1. 테스트용 가상 state (DB 실행 결과 포함)
    mock_state = {
        "intent": "INVENTORY",
        "question": "2023년 매출액 월별로 알려줘.",
        "refined_question": "2023년 매출액 월별로 알려줘.",
        "rows": [
            {"sales_month": "2023-01-01", "total_revenue": 134890690},
            {"sales_month": "2023-02-01", "total_revenue": 197047720},
            {"sales_month": "2023-03-01", "total_revenue": 93327620},
        ],
        "explain_meta": {
            "tables_used": ["sales_orders"],
            "aggregations": ["SUM(sale_quantity * actual_selling_price)"],
            "row_count": 3,
        },
        "db_result": "SUCCESS",
    }

    # 2. 답변 생성 호출
    print("--- [LLM 호출 중...] ---")
    result = await answer_service.generate(mock_state)

    # 3. 결과 출력
    print("\n🎯 사장님(LLM)의 최종 답변:")
    print("==================================================")
    print(result.get("final_answer"))
    print("==================================================")

    # 4. CHIT_CHAT 테스트
    print("\n💬 칫챗 테스트 중...")
    chit_chat_state = {"intent": "CHIT_CHAT", "question": "오늘 점심 뭐먹지?"}
    chat_result = await answer_service.generate(chit_chat_state)
    print(chat_result.get("final_answer"))


if __name__ == "__main__":
    asyncio.run(test_answer_generation())
