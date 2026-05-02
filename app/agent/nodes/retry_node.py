# llmServer/app/agent/nodes/retry_node.py

from typing import Dict
from app.container.container import ServiceContainer


class RetryNode:
    """
    Retry 결정 노드

    역할:
    - RetryDecisionService 호출
    - _decision 반환

    Graph 계약:
        입력: retry_count, error_type, result_anomalies 등
        출력: {"_decision": "RETRY" | "ANSWER" | "FAIL"}
    """

    def __init__(self, container: ServiceContainer):
        self.retry_service = container.retry_decision_service

    def __call__(self, state: Dict) -> Dict:
        decision = self.retry_service.decide(state)
        return {"_decision": decision}