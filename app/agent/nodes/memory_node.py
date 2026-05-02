# llmServer/app/agent/nodes/memory_node.py

from typing import Dict
from app.container.container import ServiceContainer


class MemoryNode:
    """
    Memory 처리 노드

    역할:
    - 최근 대화 조회
    - follow-up 재조립
    - structured_memory 생성
    - refined_question 반환

    Graph 계약:
    입력:
        - user_id
        - question

    출력:
        {
            "refined_question": str,
            "structured_memory": Dict
        }
    """

    def __init__(self, container: ServiceContainer):
        self.memory_service = container.memory_service

    async def __call__(self, state: Dict) -> Dict:

        refined, structured_memory = await self.memory_service.inject_context(
            user_id=state["user_id"],
            question=state["question"],
        )

        new_state = state.copy()
        new_state.update({
            "refined_question": refined,
            "structured_memory": structured_memory,
        })
        
        return new_state