# llmServer/app/agent/agent_graph.py

from langgraph.graph import StateGraph, END

from app.agent.nodes.memory_node import MemoryNode
from app.agent.nodes.refine_node import RefineNode
from app.agent.nodes.router_node import RouterNode
from app.agent.nodes.sql_gen_node import SQLGenNode
from app.agent.nodes.execute_db_node import ExecuteDBNode
from app.agent.nodes.result_validation_node import ResultValidationNode
from app.agent.nodes.answer_node import AnswerNode
from app.agent.nodes.save_conversation_node import SaveConversationNode
from app.agent.nodes.time_node import TimedNode


def build_graph(container):

    graph = StateGraph(dict)

    MAX_RETRY = 3

    # -----------------------------------
    # Node 등록 (클래스 기반)
    # -----------------------------------

    graph.add_node("memory", TimedNode("memory", MemoryNode(container)))
    graph.add_node("refine", TimedNode("refine", RefineNode(container)))
    graph.add_node("router", TimedNode("router", RouterNode(container)))
    graph.add_node("sql_gen", TimedNode("sql_gen", SQLGenNode(container)))
    graph.add_node("db_exec", TimedNode("db_exec", ExecuteDBNode(container)))
    graph.add_node("validate", TimedNode("validate", ResultValidationNode(container)))
    graph.add_node("answer", TimedNode("answer", AnswerNode(container)))
    graph.add_node("save_conversation", TimedNode("save_conversation", SaveConversationNode(container)))

    # -----------------------------------
    # Entry
    # -----------------------------------

    graph.set_entry_point("memory")

    graph.add_edge("memory", "refine")
    graph.add_edge("refine", "router")

    # -----------------------------------
    # Router 분기
    # -----------------------------------

    def route_by_intent(state):
        intent = state.get("intent", "INVENTORY")

        if intent == "CHIT_CHAT":
            return "answer"

        return "sql_gen"

    graph.add_conditional_edges(
        "router",
        route_by_intent,
        {
            "answer": "answer",
            "sql_gen": "sql_gen",
        },
    )

    graph.add_edge("sql_gen", "db_exec")

    # -----------------------------------
    # DB Retry 분기
    # -----------------------------------

    def should_retry_db(state):

        retry_count = state.get("retry_count", 0)
        error_type = state.get("error_type")

        if error_type:
            state["retry_count"] = retry_count + 1

            if state["retry_count"] >= MAX_RETRY:
                return "fail"

            return "retry"

        return "success"

    graph.add_conditional_edges(
        "db_exec",
        should_retry_db,
        {
            "retry": "sql_gen",
            "success": "validate",
            "fail": "answer",
        },
    )

    # -----------------------------------
    # Result Validation Retry 분기
    # -----------------------------------

    def should_retry_result(state):

        anomalies = state.get("result_anomalies", [])
        retry_count = state.get("retry_count", 0)

        if anomalies:
            state["retry_count"] = retry_count + 1

            if state["retry_count"] >= MAX_RETRY:
                return "fail"

            return "retry"

        return "success"

    graph.add_conditional_edges(
        "validate",
        should_retry_result,
        {
            "retry": "sql_gen",
            "success": "answer",
            "fail": "answer",
        },
    )

    # -----------------------------------
    # Answer → Save → END
    # -----------------------------------

    graph.add_edge("answer", "save_conversation")
    graph.add_edge("save_conversation", END)

    return graph.compile()