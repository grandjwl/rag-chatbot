# llmServer/tests/fakes/fake_llm.py

class FakeLLM:
    async def generate_sql(self, prompt: str) -> str:
        return "SELECT * FROM sales"

    async def generate(self, prompt: str) -> str:
        return "fake llm response"