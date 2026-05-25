# app/core/logging/logging_json_formatter.py

import logging
from datetime import datetime, timezone


class CompactApiFormatter(logging.Formatter):
    """
    외부 API 호출 1건을 한 줄 텍스트로 출력한다.

    LLM:    HH:MM:SS LLM    <model>  in=N out=N  cost=$N  lat=Nms  req=<id>
    EMBED:  HH:MM:SS EMBED  <model>  chars=N               lat=Nms  req=<id>
    RERANK: HH:MM:SS RERANK <model>  docs=N                lat=Nms  req=<id>
    ERROR:  HH:MM:SS LLM    <model>  ERROR=<msg>           lat=Nms  req=<id>
    기타:   HH:MM:SS WARN/ERR <logger> <message>
    """

    KIND_WIDTH = 6   # LLM / EMBED / RERANK
    MODEL_WIDTH = 24

    def format(self, record: logging.LogRecord) -> str:
        d = record.__dict__
        kind = d.get("kind")

        ts = datetime.now(timezone.utc).strftime("%H:%M:%S")

        if kind in ("LLM", "EMBED", "RERANK"):
            return self._format_api(ts, kind, d)

        # API 호출이 아닌 로그 (WARNING/ERROR만 통과)
        if record.levelno < logging.WARNING:
            return ""

        return f"{ts} {'ERR' if record.levelno >= logging.ERROR else 'WARN':<5} {record.name} — {record.getMessage()}"

    def _format_api(self, ts: str, kind: str, d: dict) -> str:
        model = d.get("model", "?")
        lat   = d.get("lat_ms", "?")
        req   = d.get("req", "")[:8]     # 앞 8자만
        err   = d.get("error")

        kind_col  = f"{kind:<{self.KIND_WIDTH}}"
        model_col = f"{model:<{self.MODEL_WIDTH}}"

        if err:
            detail = f"ERROR={err}"
        elif kind == "LLM":
            in_t  = d.get("in_tokens",  "?")
            out_t = d.get("out_tokens", "?")
            cost  = d.get("cost_usd")
            cost_s = f"${cost:.6f}" if cost is not None else "cost=?"
            detail = f"in={in_t} out={out_t}  {cost_s}"
        elif kind == "EMBED":
            detail = f"chars={d.get('chars', '?')}"
        else:  # RERANK
            detail = f"docs={d.get('docs', '?')}"

        return f"{ts} {kind_col} {model_col}  {detail:<30}  lat={lat}ms  req={req}"
