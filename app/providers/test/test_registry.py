# test_provider_registry.py
# PYTHONPATH=. python -m app.providers.test.test_registry

from app.providers.registry import ProviderRegistry
from app.providers.llm.gemini_llm_provider import GeminiLLMProvider
from app.core.config import settings
from app.providers.embedding.gemini_embedding_provider import GeminiEmbeddingProvider
from app.providers.reranker.cohere_provider import CohereRerankerProvider

def main():
    registry = ProviderRegistry()

    llm_provider = GeminiLLMProvider(
        api_key=settings.GEMINI_API_KEY,
        model_name=settings.LLM_MODEL,
    )
    
    embedding_provider = GeminiEmbeddingProvider(
        api_key=settings.GEMINI_API_KEY,
        model_name=settings.EMBEDDING_MODEL,  
    )
    
    cohere_reranker_provider = CohereRerankerProvider(
        api_key=settings.COHERE_API_KEY,
        model_name=settings.COHERE_MODEL,
    )

    # 1️⃣ 등록 테스트
    registry.register_llm(settings.LLM_MODEL, llm_provider)    
    registry.register_embedding(settings.EMBEDDING_MODEL, embedding_provider)
    registry.register_reranker(settings.COHERE_MODEL, cohere_reranker_provider)

    # 2️⃣ 정상 조회 테스트
    llm_provider_fetched = registry.get_llm(settings.LLM_MODEL)
    print("✔ 등록된 provider 반환:", llm_provider_fetched)
    embedding_provider_fetched = registry.get_embedding(settings.EMBEDDING_MODEL)
    print("✔ 등록된 embedding provider 반환:", embedding_provider_fetched) 
    reranker_provider_fetched = registry.get_reranker(settings.COHERE_MODEL)
    print("✔ 등록된 reranker provider 반환:", reranker_provider_fetched)
    
    # 3️⃣ 동일 객체인지 확인
    print("✔ 동일 객체 여부:", llm_provider_fetched is llm_provider)
    print("✔ 동일 embedding 객체 여부:", embedding_provider_fetched is embedding_provider)
    print("✔ 동일 reranker 객체 여부:", reranker_provider_fetched is cohere_reranker_provider)
    
    # 4️⃣ 예외 테스트
    try:
        registry.get_llm("not-exist-model")
    except ValueError as e:
        print("✔ 미등록 모델 예외 발생 확인:", e)


if __name__ == "__main__":
    main()