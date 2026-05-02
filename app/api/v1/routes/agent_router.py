# llmServer\app\api\v1\routes\agent_router.py

from fastapi import APIRouter, Depends
from app.schemas.agent_schema import AgentRequest, AgentResponse
from app.dependency import get_container
from app.agent.agent_graph import build_graph
from app.application.agent_controller import AgentController
from app.core.logging.request_context import generate_request_id, set_request_id  # ← 추가

router = APIRouter(prefix="/agent", tags=["Agent"])

@router.post("/query", response_model=AgentResponse)
async def query_agent(
    request: AgentRequest,
    container = Depends(get_container)
):
    set_request_id(generate_request_id()) 

    graph = build_graph(container)
    controller = AgentController(graph)
    result = await controller.run(
        user_id=request.user_id,
        session_id=request.session_id,
        question=request.question,
    )
    return result