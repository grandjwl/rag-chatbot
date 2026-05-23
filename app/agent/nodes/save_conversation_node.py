# llmServer/app/agent/nodes/save_conversation_node.py

import time
from typing import Dict
from app.container import ServiceContainer
from app.core.logging import flow_logger as flow


class SaveConversationNode:

    def __init__(self, container: ServiceContainer):
        self.memory_service = container.memory_service

    async def __call__(self, state: Dict) -> Dict:
        user_id = state.get("user_id")
        session_id = state.get("session_id")
        question = state.get("question")
        refined_question = state.get("refined_question")
        final_answer = state.get("final_answer")
        sql_query = state.get("sql_query")
        start_time = state.get("start_time")

        execution_time_ms = 0
        if start_time:
            execution_time_ms = int((time.time() - start_time) * 1000)

        if user_id and final_answer:
            await self.memory_service.save_conversation(
                user_id=user_id,
                session_id=session_id,
                question=question,
                refined_question=refined_question,
                response_data={"final_answer": final_answer},
                final_sql=sql_query,
                refine_corrections={},
                execution_time_ms=execution_time_ms,
            )

        retry_count = state.get("retry_count", 0)
        elapsed_sec = execution_time_ms / 1000
        flow.log_done(retry_count, elapsed_sec)

        return state
