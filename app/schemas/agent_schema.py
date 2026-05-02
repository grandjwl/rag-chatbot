# llmServer/app/schemas/agent_schema.py

from pydantic import BaseModel
from typing import Optional, Dict


class AgentRequest(BaseModel):
    user_id: str
    session_id: str
    question: str


class AgentResponse(BaseModel):
    final_answer: str
    sql_query: Optional[str] = None
    retry_count: Optional[int] = 0
    timings: Optional[Dict[str, float]] = None