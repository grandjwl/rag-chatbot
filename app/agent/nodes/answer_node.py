# llmServer/app/agent/nodes/answer_node.py

from typing import Dict
from app.container.container import ServiceContainer


class AnswerNode:
    """
    최종 자연어 응답 생성 노드

    역할:
    - AnswerService 호출
    - state 기반 final_answer 생성

    Graph 계약:
    - 입력: 전체 AgentState
    - 출력: {"final_answer": str}
    """

    def __init__(self, container: ServiceContainer):
        self.answer_service = container.answer_service

    async def __call__(self, state: Dict) -> Dict:
        result = await self.answer_service.generate(state)

        new_state = state.copy()
        new_state.update(result)
        return new_state