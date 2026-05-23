# llmServer/app/agent/nodes/execute_db_node.py

from typing import Dict
from app.container import ServiceContainer
from app.core.logging import flow_logger as flow


class ExecuteDBNode:

    def __init__(self, container: ServiceContainer):
        self.execute_service = container.execute_db_service

    async def __call__(self, state: Dict) -> Dict:
        result = await self.execute_service.execute(state)

        if result.get("error_type"):
            error_msg = result.get("db_result", "")
            retry_count = result.get("retry_count", 0)
            flow.log_db_error(str(error_msg))
            flow.log_retry(retry_count, str(error_msg))
        else:
            rows = result.get("rows", [])
            flow.log_db_ok(len(rows))

        new_state = state.copy()
        new_state.update(result)
        return new_state
