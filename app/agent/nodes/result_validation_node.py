# llmServer/app/agent/nodes/result_validation_node.py

from typing import Dict
from app.container.container import ServiceContainer


class ResultValidationNode:
    """
    DB 결과 비즈니스 검증 노드

    역할:
    - NULL 비율 검사
    - 음수 매출 감지
    - 이상값 감지
    - anomaly 목록 반환

    Graph 계약:
    입력:
        - rows / df / retry_count / error_history

    출력:
        {
            "result_anomalies": List[str],
            (이상 발생 시 retry 관련 필드 포함 가능)
        }
    """

    def __init__(self, container: ServiceContainer):
        self.validation_service = container.result_validation_service

    async def __call__(self, state: Dict) -> Dict:
        result = self.validation_service.validate(state)

        new_state = state.copy()
        new_state.update(result)
        return new_state