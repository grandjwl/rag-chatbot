# app/api/agent.py
# 에이전트 엔드포인트: 사용자 질문 → LangGraph 파이프라인 실행 → 결과 반환

import time
from typing import Optional, Dict

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.dependency import get_container
from app.agent.agent_graph import build_graph
from app.core.logging.request_context import generate_request_id, set_request_id
from app.core.logging import flow_logger as flow


class AgentRequest(BaseModel):
    user_id: str
    session_id: str
    question: str


class AgentResponse(BaseModel):
    final_answer: str
    sql_query: Optional[str] = None
    retry_count: Optional[int] = 0
    timings: Optional[Dict[str, float]] = None


router = APIRouter(prefix="/v1/llm/agent", tags=["Agent"])


@router.post("/query", response_model=AgentResponse)
async def query_agent(
    request: AgentRequest,
    container=Depends(get_container),
):
    set_request_id(generate_request_id())

    flow.log_request(request.user_id, request.session_id)
    flow.log_question(request.question)

    graph = build_graph(container)

    initial_state = {
        "user_id": request.user_id,
        "session_id": request.session_id,
        "question": request.question,
        "retry_count": 0,
        "error_history": [],
        "start_time": time.time(),
    }

    result = await graph.ainvoke(initial_state)

    return {
        "final_answer": result.get("final_answer"),
        "sql_query": result.get("sql_query"),
        "retry_count": result.get("retry_count", 0),
        "timings": result.get("_timings", {}),
    }
