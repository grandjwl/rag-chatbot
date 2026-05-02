# llmServer/app/api/v1/routes/main_router.py

from fastapi import APIRouter
from app.api.v1.routes import health_router
from app.api.v1.routes import agent_router

router = APIRouter(prefix="/v1/llm")

router.include_router(health_router.router, tags=["health"])
router.include_router(agent_router.router, tags=["Agent"])