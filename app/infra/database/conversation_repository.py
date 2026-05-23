# llmServer/app/infra/database/conversation_repository.py

from typing import List, Dict, Optional
from datetime import datetime
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
        response_data: Dict,
        final_sql: Optional[str],
        entity_corrections: Dict,
        execution_time_ms: int,
    ):

        query = f"""
        INSERT INTO {self.schema}.conversations (
            user_id, session_id, role,
            question, refined_question,
            response_data, final_sql,
            entity_corrections,
            execution_time_ms,
            created_at
        )
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
        """

        response = await self.rdb_repository.execute(
            query,
            user_id,
            session_id,
            "user",
            question,
            refined_question,
            json.dumps(response_data),
            final_sql,
            json.dumps(entity_corrections),
            execution_time_ms,
            datetime.utcnow(),
        )
        # print(f"✅ Conversation 저장 완료: {response}")
    # -------------------------------
    # 최근 대화 조회 (Short-term memory)
    # -------------------------------
    async def get_recent(
        self,
        user_id: str,
        limit: int = 6,
    ) -> List[Dict]:

        query = f"""
        SELECT
            question,
            refined_question,
            final_sql,
            response_data,
            entity_corrections,
            created_at
        FROM {self.schema}.conversations
        WHERE user_id = $1
          AND is_archived = FALSE
        ORDER BY created_at DESC
        LIMIT $2
        """

        return await self.rdb_repository.fetch(query, user_id, limit)

    # -------------------------------
    # 아카이빙
    # -------------------------------
    async def archive_expired(self):
        query = f"""
        SELECT {self.schema}.archive_expired_conversations();
        """
        return await self.rdb_repository.fetch_one(query)
