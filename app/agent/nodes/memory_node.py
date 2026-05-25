# llmServer/app/agent/nodes/memory_node.py

from typing import Dict
from app.container import ServiceContainer


class MemoryNode:
    """최근 대화 5턴을 불러와 state에 주입한다."""

    def __init__(self, container: ServiceContainer):
        self.memory_service = container.memory_service

    async def __call__(self, state: Dict) -> Dict:

        refined_question, conversation_history = await self.memory_service.inject_context(
            user_id=state["user_id"],
            question=state["question"],
        )

        new_state = state.copy()
        new_state.update({
            "refined_question": refined_question,
            "conversation_history": conversation_history,
        })

        return new_state
