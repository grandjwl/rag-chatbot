# llmServer/tests/fake/fake_conversation_repository.py

class FakeConversationRepository:

    def __init__(self, rows=None):
        self.rows = rows or []

    async def get_recent(self, user_id: str, limit: int):

        # user_id 필터
        rows = [r for r in self.rows if r["user_id"] == user_id]

        return rows[-limit:]

    async def save(
        self,
        user_id,
        session_id,
        question,
        refined_question,
        response_data,
        final_sql,
        refine_corrections,
        execution_time_ms,
    ):

        row = {
            "user_id": user_id,
            "session_id": session_id,
            "question": question,
            "refined_question": refined_question,
            "response_data": response_data,
            "final_sql": final_sql,
            "refine_corrections": refine_corrections,
            "execution_time_ms": execution_time_ms,
        }

        self.rows.append(row)