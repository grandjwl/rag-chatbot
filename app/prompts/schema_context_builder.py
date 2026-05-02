# app\prompts\schema_context_builder.py
from typing import Dict
from app.prompts.business_logic import BUSINESS_LOGIC


class SchemaContextBuilder:
    """
    DB 메타데이터 + 도메인 규칙 → LLM용 schema_context 생성
    """

    def __init__(self, rules: Dict[str, str] = BUSINESS_LOGIC):
        self.rules = rules

    def build(self, column_map: Dict[str, list]) -> str:
        lines = []

        for table, cols in column_map.items():
            rule_text = self.rules.get(table, "")

            section = (
                f"\n- {table}:\n"
                f"{rule_text}\n"
                f"  Cols: {', '.join(cols)}"
            )

            lines.append(section)

        return "\n".join(lines).strip()