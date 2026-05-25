# llmServer/app/services/memory_service.py

import logging
from typing import Dict, Optional, List
from app.infra.database.conversation_repository import ConversationRepository

logger = logging.getLogger(__name__)


class MemoryService:

    def __init__(self, conversation_repository: ConversationRepository):
        self.conversation_repository = conversation_repository

    async def load_recent(self, user_id: str, limit: int = 5):
        rows = await self.conversation_repository.get_recent(user_id=user_id, limit=limit)
        return list(reversed(rows))  # 오래된 → 최신

    async def inject_context(self, user_id: str, question: str):
        recent = await self.load_recent(user_id)
        conversation_history = [
            {"question": m["question"], "answer": m.get("final_answer") or ""}
            for m in recent
        ]
        return question, conversation_history

    async def save_conversation(
        self,
        user_id: str,
        session_id: str,
        question: str,
        refined_question: str,
        intent: str,
        final_answer: str,
        final_sql: Optional[str],
        rag_scores: Dict,
        retry_count: int,
        execution_time_ms: int,
    ):
        await self.conversation_repository.save(
            user_id=user_id,
            session_id=session_id,
            question=question,
            refined_question=refined_question,
            intent=intent,
            final_answer=final_answer,
            final_sql=final_sql,
            rag_scores=rag_scores,
            retry_count=retry_count,
            execution_time_ms=execution_time_ms,
        )
