# llmServer/app/services/retrieval/strategies.py

class BaseStrategy:
    collection = ""
    threshold = 0.0
    n = 3

    def format(self, docs, metas):
        raise NotImplementedError


class BiztermStrategy(BaseStrategy):
    collection = "bizterm_store"
    threshold = 0.0
    n = 5

    def format(self, docs, metas):
        return "\n".join(
            f"{d}: {m.get('desc')}"
            for d, m in zip(docs, metas)
        )


class TableSchemaStrategy(BaseStrategy):
    collection = "table_schema_store"
    threshold = 0.0
    n = 7

    def format(self, docs, metas):
        return "\n".join(docs)

