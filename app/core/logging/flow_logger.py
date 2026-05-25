# app/core/logging/flow_logger.py
# 비즈니스 흐름 로그: REQUEST → QUESTION → ROUTE → SQL → DB → ANSWER → DONE
# 콘솔과 logs/flow.log에 사람이 읽기 쉬운 텍스트 형식으로 기록

import logging
import contextvars

_flow = logging.getLogger("flow")

# 요청 단위 RAG score 누적 (async-safe)
_scores: contextvars.ContextVar[dict] = contextvars.ContextVar("rag_scores", default=None)


def start_request_scores() -> None:
    _scores.set({})


def get_request_scores() -> dict:
    return dict(_scores.get(None) or {})


def log_request(user_id: str, session_id: str) -> None:
    _flow.info(f"[REQUEST]  user={user_id} | session={session_id}")


def log_question(question: str) -> None:
    _flow.info(f"[QUESTION] {question}")


def log_refined(original: str, refined: str) -> None:
    if original != refined:
        _flow.info(f"[REFINED]  {refined}")


def log_route(intent: str) -> None:
    _flow.info(f"[ROUTE]    {intent}")


def log_sql(sql: str) -> None:
    preview = sql.replace("\n", " ").strip()
    if len(preview) > 200:
        preview = preview[:200] + "..."
    _flow.info(f"[SQL]      {preview}")


def log_db_ok(row_count: int) -> None:
    _flow.info(f"[DB]       성공 | {row_count}행")


def log_db_error(error: str) -> None:
    msg = error[:120] if len(error) > 120 else error
    _flow.warning(f"[DB ERR]   {msg}")


def log_retry(count: int, error: str) -> None:
    msg = error[:80] if len(error) > 80 else error
    _flow.warning(f"[RETRY]    #{count} | {msg}")


def log_answer(answer: str) -> None:
    preview = answer.replace("\n", " ").strip()
    if len(preview) > 150:
        preview = preview[:150] + "..."
    _flow.info(f"[ANSWER]   {preview}")


def log_rag_scores(collection: str, score: float) -> None:
    s = _scores.get(None)
    if s is not None:
        s[collection] = round(score, 4)
    _flow.info(f"[RAG]      {collection}={score:.2f}")


def log_done(retry_count: int, elapsed_sec: float) -> None:
    _flow.info(f"[DONE]     retry={retry_count} | {elapsed_sec:.1f}s")
    _flow.info("─" * 60)
