# llmServer/tests/fake/fake_reranker.py

class FakeReranker:

    async def rerank(self, query, docs):
        return docs