# llmServer/app/services/retrieval/bm25.py

class BM25Index:

    def __init__(self, vector_repository, collection_name: str):
        self.vector_repository = vector_repository
        self.collection_name = collection_name
        self.index = None
        self.docs = []
        self.metas = []

    async def build(self):
        from rank_bm25 import BM25Okapi
        from app.infra.vector.exceptions import VectorCollectionNotFound

        try:
            data = await self.vector_repository.get_all(self.collection_name)
        except VectorCollectionNotFound:
            self.docs = []
            self.metas = []
            return

        self.docs = data.get("documents", [])
        self.metas = data.get("metadatas", [])

        if not self.docs:
            return

        tokenized = [doc.split() for doc in self.docs]
        self.index = BM25Okapi(tokenized)

    async def rebuild(self):
        await self.build()

    def search(self, query: str, top_k: int = 5):

        if not self.index:
            return []

        scores = self.index.get_scores(query.split())

        ranked = sorted(
            range(len(scores)),
            key=lambda i: scores[i],
            reverse=True
        )[:top_k]

        max_score = max(scores) if max(scores) > 0 else 1

        results = []

        for i in ranked:
            if scores[i] > 0:
                results.append({
                    "doc": self.docs[i],
                    "meta": self.metas[i],
                    "score": scores[i] / max_score,
                })

        return results