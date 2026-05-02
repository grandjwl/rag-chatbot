# llmServer/app/services/test/services/test_llm_service.py
# PYTHONPATH=. python -m app.services.test.services.test_llm_service


import asyncio

# import time

# from app.core.logging.logging_config import setup_logging
# from app.core.logging.request_context import generate_request_id, set_request_id

from app.providers.registry import ProviderRegistry
from app.prompts.registry import PromptRegistry
from app.providers.llm.gemini_llm_provider import GeminiLLMProvider
from app.services.llm_service import LLMService
from app.core.config import settings


async def main():
    # 🔥 로깅 초기화
    # setup_logging()

    # 🔥 request_id 수동 세팅
    # request_id = generate_request_id()
    # set_request_id(request_id)

    # print("===== TEST START =====")
    # print("request_id:", request_id)

    registry = ProviderRegistry()
    prompt_registry = PromptRegistry()

    gemini_provider = GeminiLLMProvider(
        api_key=settings.GEMINI_API_KEY,
        model_name=settings.LLM_MODEL,
    )

    registry.register_llm(settings.LLM_MODEL, gemini_provider)

    llm_service = LLMService(
        llm_registry=registry,
        prompt_registry=prompt_registry,
    )

    # start = time.time()

    response = await llm_service.generate_answer("파이썬이 뭐야?")

    # latency = round((time.time() - start) * 1000, 2)

    # 디버깅용 출력
    # print("===== RESPONSE =====")
    # print("Latency(ms):", latency)
    print("Response Preview:", response)


if __name__ == "__main__":
    asyncio.run(main())
