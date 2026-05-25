# llmServer/app/agent/nodes/router_node.py

from typing import Dict
from app.container import ServiceContainer
from app.core.logging import flow_logger as flow


class RouterNode:

    def __init__(self, container: ServiceContainer):
        self.router_service = container.router_service

    async def __call__(self, state: Dict) -> Dict:
        intent = await self.router_service.route(
            state["refined_question"],
            state.get("conversation_history", []),
        )

        flow.log_route(intent)

        new_state = state.copy()
        new_state.update({"intent": intent})
        return new_state
