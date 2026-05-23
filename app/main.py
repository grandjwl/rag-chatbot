# app/main.py

from fastapi import FastAPI
from app.api import agent
from app.core.logging.logging_config import setup_logging

setup_logging()

app = FastAPI()

app.include_router(agent.router)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}
