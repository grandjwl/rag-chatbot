# llmServer/app/infra/database/conversation_repository.py

from typing import List, Dict, Optional
from app.infra.database.rdb_repository import RDBRepository
from app.core.config import settings
import json


class ConversationRepository:

    def __init__(self, rdb_repository: RDBRepository):
        self.rdb_repository = rdb_repository
        self.schema = settings.CONVERSATION_SCHEMA

    # -------------------------------
    # 저장
    # -------------------------------
    async def save(
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
        query = f"""
        INSERT INTO {self.schema}.conversations (
            user_id, session_id,
            question, refined_question,
            intent, final_answer, final_sql,
            rag_scores, retry_count,
            execution_time_ms
        )
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
        """
        await self.rdb_repository.execute(
            query,
            user_id,
            session_id,
            question,
            refined_question,
            intent,
            final_answer,
            final_sql,
            json.dumps(rag_scores),
            retry_count,
            execution_time_ms,
        )

    # -------------------------------
    # 최근 대화 조회 (Short-term memory)
    # -------------------------------
    async def get_recent(self, user_id: str, limit: int = 5) -> List[Dict]:
        query = f"""
        SELECT question, final_answer, created_at
        FROM {self.schema}.conversations
        WHERE user_id = $1
        ORDER BY created_at DESC
        LIMIT $2
        """
        return await self.rdb_repository.fetch(query, user_id, limit)

    # -------------------------------
    # 피드백 저장
    # -------------------------------
    async def save_feedback(self, user_id: str, session_id: str, is_good: bool):
        query = f"""
        UPDATE {self.schema}.conversations
        SET feedback = $3
        WHERE ctid = (
            SELECT ctid FROM {self.schema}.conversations
            WHERE user_id = $1 AND session_id = $2
            ORDER BY created_at DESC
            LIMIT 1
        )
        """
        # SMALLINT: 1=좋음, 0=나쁨, NULL=미응답
        await self.rdb_repository.execute(query, user_id, session_id, 1 if is_good else 0)
