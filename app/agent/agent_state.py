# app/graph/agent_state.py

from typing import TypedDict, List, Dict, Any


class AgentState(TypedDict, total=False):

    # 입력
    user_id: str
    session_id: str
    question: str

    # Memory
    refined_question: str
    structured_memory: Dict

    # Refine
    synonym_hint: str

    # Router
    intent: str

    # SQL
    sql_query: str

    # DB 실행
    rows: List[Dict]
    db_result: str
    explain_meta: Dict

    # Validation
    result_anomalies: List[str]

    # Retry 관련
    retry_count: int
    error_history: List[str]
    retry_strategy: str
    error_type: str

    # 최종 출력
    final_answer: str