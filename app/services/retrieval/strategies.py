# llmServer/app/services/retrieval/strategies.py

class BaseStrategy:
    collection = ""
    threshold = 0.05

    def format(self, docs, metas):
        raise NotImplementedError


# class SynonymStrategy(BaseStrategy):
#     collection = "SB_synonym_store"
#     threshold = 0.3

#     def format(self, docs, metas):
#         return ", ".join(
#             f"'{d}' → '{m.get('canonical')}'"
#             for d, m in zip(docs, metas)
#         )


class BiztermStrategy(BaseStrategy):
    collection = "bizterm_store"
    threshold = 0.25

    def format(self, docs, metas):
        return "\n".join(
            f"{d}: {m.get('desc')}"
            for d, m in zip(docs, metas)
        )


class TableSchemaStrategy(BaseStrategy):
    collection = "table_schema_store"
    threshold = 0.2

    def format(self, docs, metas):
        return "\n".join(docs)


# class ErrorStrategy(BaseStrategy):
#     collection = "SB_error_store"
#     threshold = 0.2

#     def format(self, docs, metas):
#         return "\n".join(docs)


# class KeywordStrategy(BaseStrategy):
#     collection = "SB_intent_store"
#     threshold = 0.2

#     def format(self, docs, metas):
#         return "\n".join(
#             f"의도: {m.get('intent')} | 테이블: {m.get('table')}"
#             for d, m in zip(docs, metas)
#         )