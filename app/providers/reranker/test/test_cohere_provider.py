# llmServer/app/providers/reranker/test/test_cohere_provider.py
# PYTHONPATH=. python -m app.providers.reranker.test.test_cohere_provider

from app.providers.reranker.cohere_provider import CohereRerankerProvider
from app.providers.registry import ProviderRegistry
from app.core.config import settings

def get_test_registry() -> ProviderRegistry:
    """실제 앱의 deps.py에서 하는 것처럼 Registry를 준비합니다."""
    registry = ProviderRegistry()
    
    # 설정파일에서 키를 가져와 실제 프로바이더 등록
    if not settings.COHERE_API_KEY:
        raise ValueError("COHERE_API_KEY가 설정되지 않았습니다.")
        
    registry.register_reranker(
        model_name="cohere-v3", 
        provider=CohereRerankerProvider(api_key=settings.COHERE_API_KEY)
    )
    return registry

def run_test(registry: ProviderRegistry):
    """의존성을 주입받아 실행하는 테스트 함수"""
    print("🚀 리랭커 Registry 주입 테스트")
    
    # 1. Registry에서 의존성 꺼내기
    reranker = registry.get_reranker("cohere-v3")
    
    query = "network switch chip"
    docs = [
        "BCM5650 is a high-performance network switch chip",
        "Apple is a fruit",
        "Electronic components distributor company",
        "Temperature sensor IC",
    ]

    # 2. 실행
    scores = reranker.score(query, docs)

    print(f"\nQuery: {query}")
    print("\nDocs & Scores:")
    for d, s in zip(docs, scores):
        print(f"[{s:.4f}] - {d}")

if __name__ == "__main__":
    # 1. 의존성 관리자(Registry) 생성
    test_registry = get_test_registry()
    
    # 2. 의존성을 주입하여 테스트 실행
    run_test(test_registry)