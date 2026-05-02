# llmServer/app/agent/nodes/save_conversation_node.py

import time
from typing import Dict
from app.container.container import ServiceContainer


class SaveConversationNode:
    """
    최종 응답 이후 대화 저장 노드

    역할:
    - Conversation 로그 저장
    - execution_time 계산
    - SQL 및 답변 저장

    Graph 계약:
        입력: final_answer 존재 시 저장
        출력: state (state 변경 없음)
    """

    def __init__(self, container: ServiceContainer):
        self.memory_service = container.memory_service

    async def __call__(self, state: Dict) -> Dict:

        user_id = state.get("user_id")
        session_id = state.get("session_id")
        question = state.get("question")
        refined_question = state.get("refined_question")
        final_answer = state.get("final_answer")
        sql_query = state.get("sql_query")

        if user_id and final_answer:
          start_time = state.get("start_time")
          execution_time_ms = 0

          if start_time:
              execution_time_ms = int((time.time() - start_time) * 1000)

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

        return state