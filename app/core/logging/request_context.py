# app/core/logging/request_context.py

import uuid
from contextvars import ContextVar

# 요청 단위 저장소
_request_id_ctx_var: ContextVar[str | None] = ContextVar("request_id", default=None)


def generate_request_id() -> str:
    return str(uuid.uuid4())


def set_request_id(request_id: str):
    _request_id_ctx_var.set(request_id)


def get_request_id() -> str | None:
    return _request_id_ctx_var.get()