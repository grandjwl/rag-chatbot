# llmServer/app/agent/nodes/sql_gen_node.py

from typing import Dict
from app.container import ServiceContainer
from app.core.logging import flow_logger as flow


class SQLGenNode:

    def __init__(self, container: ServiceContainer):
        self.sql_service = container.sql_generate_service

    async def __call__(self, state: Dict) -> Dict:
        result = await self.sql_service.generate(state)

        if result.get("sql_query"):
            flow.log_sql(result["sql_query"])

        new_state = state.copy()
        new_state.update(result)
        return new_state
