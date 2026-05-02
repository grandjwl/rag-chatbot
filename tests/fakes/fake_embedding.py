# llmServer/tests/fake/fake_embedding.py

class FakeEmbedding:

    async def embed(self, text: str):
        return [0.1, 0.2, 0.3, 0.4]