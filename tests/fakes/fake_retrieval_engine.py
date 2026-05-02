# llmServer/tests/fake/fake_retrieval_engine.py

class FakeRetrievalEngine:

    async def retrieve(self, strategy, question):
        return "fake retrieval"

    async def retrieve_fewshot(self, question):
        return "Q: example\nSQL: SELECT * FROM sales"