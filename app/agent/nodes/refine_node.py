# llmServer/app/agent/nodes/refine_node.py

from typing import Dict
from app.container import ServiceContainer
from app.core.logging import flow_logger as flow


class RefineNode:

    def __init__(self, container: ServiceContainer):
        self.refine_service = container.refine_service

    async def __call__(self, state: Dict) -> Dict:
        result = await self.refine_service.resolve(state["refined_question"])

        flow.log_refined(state["question"], result["refined_question"])

        new_state = state.copy()
        new_state.update(result)
        return new_state
