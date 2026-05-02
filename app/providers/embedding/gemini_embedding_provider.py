# llmServer/app/provider/embedding/gemini_embedding_provider.py

import asyncio
from google import genai
from typing import List
from app.providers.embedding.base import BaseEmbeddingProvider


class GeminiEmbeddingProvider(BaseEmbeddingProvider):

    def __init__(self, api_key: str, model_name: str):
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name

    async def embed(self, texts: List[str]) -> List[List[float]]:

        loop = asyncio.get_running_loop()

        response = await loop.run_in_executor(
            None,
            lambda: self.client.models.embed_content(
                model=self.model_name,
                contents=texts,
            )
        )

        return [emb.values for emb in response.embeddings]