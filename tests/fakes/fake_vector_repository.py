# llmServer/tests/fake/fake_vector_repository.py

class FakeVectorRepository:

    async def search(self, query_vector, top_k=5):
        return [
            {
                "content": "table sales(product_id, amount, date)",
                "score": 0.9
            }
        ]