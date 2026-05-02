# app/core/logging/cost_calculator.py

def calculate_gemini_cost(
    prompt_tokens: int | None,
    completion_tokens: int | None,
) -> float | None:
    """
    gemini-2.5-flash 기준 대략적인 비용 계산 (예시 단가)
    실제 단가는 Google 요금표 확인 후 수정해야 함
    """

    if prompt_tokens is None or completion_tokens is None:
        return None

    # 🔥 예시 단가 (가짜 수치, 실제 요금으로 수정 필요)
    PROMPT_COST_PER_1K = 0.0005
    COMPLETION_COST_PER_1K = 0.0015

    prompt_cost = (prompt_tokens / 1000) * PROMPT_COST_PER_1K
    completion_cost = (completion_tokens / 1000) * COMPLETION_COST_PER_1K

    return round(prompt_cost + completion_cost, 6)