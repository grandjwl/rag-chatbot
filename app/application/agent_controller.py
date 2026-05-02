import time


class AgentController:

    def __init__(self, graph):
        self.graph = graph

    async def run(self, user_id: str, session_id: str, question: str):

        initial_state = {
            "user_id": user_id,
            "session_id": session_id,
            "question": question,
            "retry_count": 0,
            "error_history": [],
            "start_time": time.time(),
        }

        result = await self.graph.ainvoke(initial_state)

        return {
            "final_answer": result.get("final_answer"),
            "sql_query": result.get("sql_query"),
            "retry_count": result.get("retry_count", 0),
            "timings": result.get("_timings", {}),
        }