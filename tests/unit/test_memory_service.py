# ============================================================
# File:
#   llmServer/tests/unit/test_memory_service.py
#
# Run:
#   PYTHONPATH=. pytest tests/unit/test_memory_service.py -v
#
# 또는 개별 테스트 실행 (예시 - load_recent)
#   PYTHONPATH=. pytest tests/unit/test_memory_service.py::test_load_recent_orders_messages -v
#
# 목적:
#   MemoryService 핵심 기능 검증
#
# 테스트 범위:
#   1️⃣ load_recent
#   2️⃣ follow-up rebuild
#   3️⃣ pronoun resolution
#   4️⃣ structured memory extraction
#   5️⃣ save_conversation
# ============================================================

import pytest

# 테스트 대상 서비스
from app.services.memory_service import MemoryService

# Fake repository
from tests.fakes.fake_conversation_repository import FakeConversationRepository


# ============================================================
# 1️⃣ load_recent 테스트
# ============================================================
# 목적:
#   - ConversationRepository에서 최근 대화를 가져온 뒤
#   - 오래된 → 최신 순서로 정렬되는지 확인
#
# 기대:
#   reversed 로직이 적용되어 순서가 뒤집혀야 한다
# ============================================================

@pytest.mark.asyncio
async def test_load_recent_orders_messages():

    rows = [
        {"question": "2022년 매출", "response_data": {}},
        {"question": "2023년 매출", "response_data": {}},
    ]

    repo = FakeConversationRepository(rows=rows)
    service = MemoryService(repo)

    result = await service.load_recent("user1")

    # 최신 질문이 먼저 와야 함
    assert result[0]["question"] == "2023년 매출"
    assert result[1]["question"] == "2022년 매출"


# ============================================================
# 2️⃣ follow-up 질문 재조립 테스트
# ============================================================
# 목적:
#   - 짧은 follow-up 질문을 이전 질문 기반으로 재구성
#
# 예시:
#   이전 질문: "2023년 매출 보여줘"
#   새 질문: "24년은?"
#
# 기대 결과:
#   "2024년 매출 보여줘"
# ============================================================

@pytest.mark.asyncio
async def test_followup_year_rebuild():

    rows = [
        {"question": "2023년 매출 보여줘", "response_data": {}}
    ]

    repo = FakeConversationRepository(rows=rows)
    service = MemoryService(repo)

    refined, memory = await service.inject_context(
        user_id="user1",
        question="24년은?"
    )

    # 연도 치환 확인
    assert "2024년" in refined


# ============================================================
# 3️⃣ Pronoun Resolution 테스트
# ============================================================
# 목적:
#   - structured_memory 기반 대명사 해석
#
# 예시:
#   이전 응답: "제품 ABC123 매출은 ..."
#   질문: "이 제품 매출은?"
#
# 기대 결과:
#   "ABC123 매출은?"
# ============================================================

@pytest.mark.asyncio
async def test_pronoun_resolution():

    rows = [
        {
            "question": "제품 ABC123 매출 알려줘",
            "response_data": "제품 ABC123 매출은 1000"
        }
    ]

    repo = FakeConversationRepository(rows=rows)
    service = MemoryService(repo)

    refined, memory = await service.inject_context(
        user_id="user1",
        question="이 제품 매출은?"
    )

    # 대명사가 실제 제품 코드로 치환되는지 확인
    assert "ABC123" in refined


# ============================================================
# 4️⃣ Structured Memory 추출 테스트
# ============================================================
# 목적:
#   - 이전 대화에서 structured_memory 생성
#
# 추출 대상:
#   - last_product
#   - last_year
#
# 기대 결과:
#   memory dict에 해당 값이 존재
# ============================================================

@pytest.mark.asyncio
async def test_structured_memory_extraction():

    rows = [
        {
            "question": "2023년 매출",
            "response_data": "제품 ABC123 매출 1000"
        }
    ]

    repo = FakeConversationRepository(rows=rows)
    service = MemoryService(repo)

    refined, memory = await service.inject_context(
        user_id="user1",
        question="다른 제품은?"
    )

    # structured memory 확인
    assert memory["last_product"] == "ABC123"
    assert memory["last_year"] == "2023"


# ============================================================
# 5️⃣ save_conversation 테스트
# ============================================================
# 목적:
#   - MemoryService가 ConversationRepository.save 호출하는지 확인
#
# 검증:
#   - 저장된 데이터가 repo.saved에 기록되는지
# ============================================================

@pytest.mark.asyncio
async def test_save_conversation():

    repo = FakeConversationRepository()
    service = MemoryService(repo)

    await service.save_conversation(
        user_id="u1",
        session_id="s1",
        question="Q",
        refined_question="RQ",
        response_data={"answer": "ok"},
        final_sql="SELECT 1",
        refine_corrections={},
        execution_time_ms=10
    )

    # 저장된 데이터 확인
    assert repo.saved["question"] == "Q"
    assert repo.saved["final_sql"] == "SELECT 1"