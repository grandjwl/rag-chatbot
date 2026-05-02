# llmServer/app/providers/embedding/azure_embedding_provider.py

import asyncio
from typing import List
from openai import AzureOpenAI

from app.providers.embedding.base import BaseEmbeddingProvider


class AzureEmbeddingProvider(BaseEmbeddingProvider):

    def __init__(
        self,
        api_key: str,
        azure_endpoint: str,
        deployment_name: str,
        api_version: str = "2023-05-15",
    ):
        self.client = AzureOpenAI(
            api_key=api_key,
            azure_endpoint=azure_endpoint,
            api_version=api_version,
        )
        self.deployment = deployment_name  # ⚠️ 모델명이 아니라 deployment name

    async def embed(self, texts: List[str]) -> List[List[float]]:

        loop = asyncio.get_running_loop()

        response = await loop.run_in_executor(
            None,
            lambda: self.client.embeddings.create(
                model=self.deployment,
                input=texts,
            )
        )

        return [item.embedding for item in response.data]