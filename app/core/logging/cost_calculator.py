# app/core/logging/cost_calculator.py

# USD per 1K tokens (in, out) — Google AI 요금표 기준 (2025년 상반기)
_PRICES: dict[str, tuple[float, float]] = {
    "gemini-2.5-flash-lite": (0.0001, 0.0004),
    "gemini-2.5-flash":      (0.0003, 0.0025),
    "gemini-2.5-pro":        (0.00125, 0.010),
}
_DEFAULT = (0.0003, 0.0025)  # flash 단가 fallback


def calculate_gemini_cost(
    model_name: str,
    in_tokens: int | None,
    out_tokens: int | None,
) -> float | None:
    if in_tokens is None or out_tokens is None:
        return None
    in_price, out_price = _PRICES.get(model_name, _DEFAULT)
    return round((in_tokens / 1000) * in_price + (out_tokens / 1000) * out_price, 6)