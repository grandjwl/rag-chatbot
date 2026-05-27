# llmServer/app/services/retrieval/strategies.py

class BaseStrategy:
    collection = ""
    threshold = 0.0
    n = 3

    def format(self, docs, metas):
        raise NotImplementedError


class BiztermStrategy(BaseStrategy):
    collection = "bizterm-store"
    threshold = 0.0
    n = 5

    def format(self, docs, metas):
        lines = []
        for d, m in zip(docs, metas):
            term = m.get("term", d)
            line = f"- {term}"
            if m.get("synonyms"):
                line += f" (동의어: {m['synonyms']})"
            if m.get("definition"):
                line += f": {m['definition']}"
            if m.get("formula"):
                line += f"\n    계산식: {m['formula']}"
            if m.get("tables"):
                line += f"\n    필요 테이블: {m['tables']}"
            if m.get("date_column"):
                line += f" / 날짜 컬럼: {m['date_column']}"
            if m.get("note"):
                line += f"\n    주의: {m['note']}"
            lines.append(line)
        return "\n".join(lines)


class TableSchemaStrategy(BaseStrategy):
    collection = "table-store"
    threshold = 0.0
    n = 7

    def format(self, docs, metas):
        lines = []
        for d, m in zip(docs, metas):
            table = m.get("table", "?")
            section = (
                f"\n[{table}] {m.get('purpose', '')}\n"
                f"  컬럼: {m.get('columns', '')}\n"
                f"  PK: {m.get('primary_key', '')}\n"
                f"  컬럼 상세: {m.get('column_notes', '')}"
            )
            if m.get("date_column"):
                section += f"\n  날짜 컬럼: {m['date_column']}"
            if m.get("cautions"):
                section += f"\n  주의: {m['cautions']}"
            lines.append(section)
        return "\n".join(lines)
