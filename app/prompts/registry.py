# llmServer/app/prompts/registry.py

from app.prompts.router_prompt import BASE_ROUTER_SYSTEM_PROMPT

from app.prompts.sql_prompt import BASE_SQL_SYSTEM_PROMPT
from app.prompts.answer_prompt import BASE_ANSWER_SYSTEM_PROMPT
from app.prompts.sql_generation_prompt import BASE_SQL_GENERATION_SYSTEM_PROMPT
from app.prompts.chitchat_prompt import BASE_CHITCHAT_SYSTEM_PROMPT


class PromptRegistry:

    def get_router_prompt(self) -> str:
        return BASE_ROUTER_SYSTEM_PROMPT

    def get_sql_prompt(self) -> str:
        return BASE_SQL_SYSTEM_PROMPT

    def get_answer_prompt(self) -> str:
        return BASE_ANSWER_SYSTEM_PROMPT

    def get_sql_generation_prompt(self) -> str:
        return BASE_SQL_GENERATION_SYSTEM_PROMPT

    def get_chitchat_prompt(self) -> str:
        return BASE_CHITCHAT_SYSTEM_PROMPT
