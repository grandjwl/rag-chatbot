# llmServer/app/agent/nodes/router_node.py

from typing import Dict
from app.container.container import ServiceContainer


class RouterNode:
    """
    Intent 분류 노드

    역할:
    - rule 기반 + LLM fallback 라우팅
    - intent 반환

    Graph 계약:
        입력: refined_question
        출력: {"intent": str}
    """

    def __init__(self, container: ServiceContainer):
        self.router_service = container.router_service

    async def __call__(self, state: Dict) -> Dict:

        intent = await self.router_service.route(
            state["refined_question"]
        )

        new_state = state.copy()
        new_state.update({"intent": intent})
        return new_state