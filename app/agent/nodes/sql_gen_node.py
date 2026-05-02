# llmServer/app/agent/nodes/sql_gen_node.py

from typing import Dict
from app.container.container import ServiceContainer


class SQLGenNode:
    """
    SQL 생성 노드

    역할:
    - LLM 기반 SQL 생성
    - retry 전략 반영
    - sql_query 반환

    Graph 계약:
        입력: refined_question, error_history 등
        출력: {"sql_query": str}
    """

    def __init__(self, container: ServiceContainer):
        self.sql_service = container.sql_generate_service

    async def __call__(self, state: Dict) -> Dict:
        result = await self.sql_service.generate(state)

        new_state = state.copy()
        new_state.update(result)
        return new_state