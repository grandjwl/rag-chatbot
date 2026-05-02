# llmServer/tests/fake/fake_rdb_repository.py

class FakeRDBRepository:

    async def execute(self, sql):
        return [
            {"product_id": "ABC123", "amount": 1000}
        ]