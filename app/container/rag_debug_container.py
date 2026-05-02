 # app/container/rag_debug_container.py

from app.infra.vector.chroma_vector_client import ChromaVectorClient
from app.providers.embedding.azure_openai_embedding_provider import AzureEmbeddingProvider
from app.providers.reranker.cohere_provider import CohereRerankerProvider
from app.services.rerank_service import RerankService
from app.infra.vector.vector_repository import VectorRepository
from app.services.retrieval.engine import RetrievalEngine

from app.core.config import settings

class RAGDebugContainer:

    def __init__(self):

        # 임베딩
        self.embedding_provider = AzureEmbeddingProvider(
          api_key=settings.AZURE_OPENAI_API_KEY,
          azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
          deployment_name=settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME,
          api_version=settings.AZURE_OPENAI_API_VERSION
        )

        # 벡터 클라이언트
        self.vector_client = ChromaVectorClient(
            embedding_provider=self.embedding_provider
        )
        # 벡터 레포지터리
        vector_repository = VectorRepository(vector_client=self.vector_client)

        # rerank provider
        rerank_provider = CohereRerankerProvider(api_key=settings.COHERE_API_KEY, 
                                                 model_name=settings.COHERE_MODEL)
        
        # reranker
        self.rerank_service = RerankService(reranker=rerank_provider)

        # retrieval engine
        self.retrieval_engine = RetrievalEngine(
            vector_repository=vector_repository,
            rerank_service=self.rerank_service,
        )