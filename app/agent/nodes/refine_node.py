# llmServer/app/agent/nodes/refine_node.py

from typing import Dict
from app.container.container import ServiceContainer

class RefineNode:
    """
    RefineService → refined_question 보정 + synonym_hint
    """

    def __init__(self, container: ServiceContainer):
        self.refine_service = container.refine_service

    async def __call__(self, state: Dict) -> Dict:
      result = await self.refine_service.resolve(state["refined_question"])

      new_state = state.copy()
      new_state.update(result)
      return new_state