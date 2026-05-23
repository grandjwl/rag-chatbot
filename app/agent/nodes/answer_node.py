# llmServer/app/agent/nodes/answer_node.py

from typing import Dict
from app.container import ServiceContainer
from app.core.logging import flow_logger as flow


class AnswerNode:

    def __init__(self, container: ServiceContainer):
        self.answer_service = container.answer_service

    async def __call__(self, state: Dict) -> Dict:
        result = await self.answer_service.generate(state)

        flow.log_answer(result.get("final_answer", ""))

        new_state = state.copy()
        new_state.update(result)
        return new_state
