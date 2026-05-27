# llmServer/app/services/result_validation_service.py

import logging
from datetime import date
from typing import Dict, List

import pandas as pd


logger = logging.getLogger(__name__)


class ResultValidationService:
    """
    7단계 정적 SQL 검증을 통과한 쿼리 결과에 대한 비즈니스 Sanity Check.
    문법상 유효한 SQL이 실행된 뒤에도 결과값이 비즈니스적으로 올바른지 검증한다.
    retry 판단과 retry_count 관리는 이 서비스가 직접 수행한다.
    """

    _FINANCIAL_SUFFIXES = {"revenue", "price", "cost", "profit", "amount", "매출", "수익"}
    _QTY_KEYWORDS      = {"quantity", "qty", "stock", "count", "수량", "재고", "잔량"}
    _DATE_KEYWORDS     = {"date", "at", "time", "일자", "날짜"}

    _MIN_MEAN_FOR_OUTLIER = 100   # 평균이 이 값 미만이면 극단값 체크 skip
    _MAX_DUPLICATE_RATIO  = 0.5   # 중복 행 비율이 이 값 초과면 Cartesian Product 의심

    def validate(self, state: Dict) -> Dict:

        df           = state.get("df")
        retry_count  = state.get("retry_count", 0)
        error_history = state.get("error_history", [])

        anomalies: List[str] = []

        # 빈 결과는 정상 — "조회 결과 없음"은 SQL 문제가 아님
        if df is None or len(df) == 0:
            return {"result_anomalies": []}

        # 1. NULL 비율 80% 초과
        for col in df.columns:
            null_ratio = df[col].isna().sum() / len(df)
            if null_ratio > 0.8:
                anomalies.append(f"'{col}' NULL 비율 {null_ratio:.0%} 초과.")

        # 2. 음수 금액 (exact match 또는 _{suffix} 끝 일치)
        for col in df.columns:
            col_lower = col.lower()
            is_financial = any(
                col_lower == k or col_lower.endswith(f"_{k}")
                for k in self._FINANCIAL_SUFFIXES
            )
            if is_financial and pd.api.types.is_numeric_dtype(df[col]):
                neg_count = (df[col] < 0).sum()
                if neg_count > 0:
                    anomalies.append(f"'{col}' 음수 금액 {neg_count}건 (비즈니스 규칙 위반).")

        # 3. 음수 수량
        for col in df.columns:
            col_lower = col.lower()
            if any(k in col_lower for k in self._QTY_KEYWORDS):
                if pd.api.types.is_numeric_dtype(df[col]):
                    neg_count = (df[col] < 0).sum()
                    if neg_count > 0:
                        anomalies.append(f"'{col}' 음수 수량 {neg_count}건.")

        # 4. 극단값 (평균이 의미 있는 수치일 때만 검사)
        for col in df.select_dtypes(include="number").columns:
            mean_val = df[col].mean()
            if mean_val >= self._MIN_MEAN_FOR_OUTLIER:
                max_val = df[col].max()
                if max_val > mean_val * 10_000:
                    anomalies.append(
                        f"'{col}' 극단값 감지 (최대 {max_val:,.0f}, 평균 {mean_val:,.0f})."
                    )

        # 5. 전체 0값 컬럼 — 행이 2개 이상일 때만 (집계 오류 감지)
        if len(df) > 1:
            for col in df.select_dtypes(include="number").columns:
                if (df[col] == 0).all():
                    anomalies.append(f"'{col}' 모든 값이 0 (집계 오류 의심).")

        # 6. 중복 행 50% 초과 — Cartesian Product 2차 방어
        dup_ratio = df.duplicated().sum() / len(df)
        if dup_ratio > self._MAX_DUPLICATE_RATIO:
            anomalies.append(f"중복 행 {dup_ratio:.0%} 감지 (Cartesian Product 의심).")

        # 7. 미래 날짜 — 주문일·입고일 등 이력 날짜에 미래값 불가
        today = date.today()
        for col in df.columns:
            col_lower = col.lower()
            if any(k in col_lower for k in self._DATE_KEYWORDS):
                if pd.api.types.is_datetime64_any_dtype(df[col]):
                    future_count = (df[col].dt.date > today).sum()
                    if future_count > 0:
                        anomalies.append(f"'{col}' 미래 날짜 {future_count}건.")

        if anomalies:
            logger.warning("Result Anomaly Detected: %s", anomalies)
            return {
                "result_anomalies": anomalies,
                "db_result":   f"Error: 결과 이상 감지 - {' | '.join(anomalies)}",
                "error_history": error_history + anomalies,
                "retry_count": retry_count + 1,
                "retry_strategy": "result_anomaly",
                "error_type":  "result_validation",
            }

        return {"result_anomalies": []}
