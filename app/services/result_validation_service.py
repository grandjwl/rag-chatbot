# llmServer/app/services/result_validation_service.py

import logging
from typing import Dict, List
import pandas as pd


logger = logging.getLogger(__name__)


class ResultValidationService:
    """
    ============================================================
    [Domain Role]
    DB 실행 결과에 대한 비즈니스 기반 Sanity Check 서비스.

    역할:
        - NULL 과다 감지
        - 음수 매출/수익 감지
        - 극단적 이상값 감지

    ============================================================
    🔥 Graph에서 관리해야 할 영역

    이 서비스는:
        ❌ retry 여부 최종 판단하지 않음
        ❌ max retry 판단하지 않음
        ❌ 전체 플로우 제어하지 않음

    Graph는:
        - anomaly 발생 시 retry 여부 결정
        - retry_count 증가 여부 결정
        - error_history 통합 관리
        - 최종 실패 상태 판단

    ============================================================
    [Input State Fields]
    - df: pandas.DataFrame
    - retry_count: int
    - error_history: List[str]

    ============================================================
    [Output]

    정상:
        {
            "result_anomalies": []
        }

    이상 발생:
        {
            "result_anomalies": List[str]
        }

    (⚠ retry 관련 필드는 Graph가 관리하도록 향후 분리 예정)
    ============================================================
    """
    def validate(self, state: Dict) -> Dict:

        df = state.get("df")
        retry_count = state.get("retry_count", 0)
        error_history = state.get("error_history", [])

        anomalies: List[str] = []

        # 1️⃣ 결과 없음은 재시도하지 않음
        if df is None or len(df) == 0:
            return {"result_anomalies": []}

        # 2️⃣ NULL 비율 과다 (80% 이상)
        for col in df.columns:
            null_ratio = df[col].isna().sum() / len(df)

            if null_ratio > 0.8:
                anomalies.append(f"'{col}' NULL 비율 {null_ratio:.0%} 초과.")

        # 3️⃣ 음수 매출/수익 감지
        for col in df.columns:

            if any(
                k in col.lower()
                for k in [
                    "revenue",
                    "price",
                    "cost",
                    "profit",
                    "amount",
                    "매출",
                    "수익",
                ]
            ):

                if pd.api.types.is_numeric_dtype(df[col]):
                    neg_count = (df[col] < 0).sum()

                    if neg_count > 0:
                        anomalies.append(
                            f"'{col}' 음수값 {neg_count}건 (비즈니스 규칙 위반)."
                        )

        # 4️⃣ 극단적 이상값 감지 (mean * 10000)
        for col in df.select_dtypes(include="number").columns:

            mean_val = df[col].mean()

            if mean_val > 0:
                max_val = df[col].max()

                if max_val > mean_val * 10000:
                    anomalies.append(f"'{col}' 최대값({max_val:,.0f}) 이상 감지.")

        # 5️⃣ 이상 발견 시 재시도 트리거
        if anomalies:

            logger.warning(f"Result Anomaly Detected: {anomalies}")

            return {
                "result_anomalies": anomalies,
                "db_result": f"Error: 결과 이상 감지 - {' | '.join(anomalies)}",
                "error_history": error_history + anomalies,
                "retry_count": retry_count + 1,
                "retry_strategy": "result_anomaly",
                "error_type": "result_validation",
            }

        return {"result_anomalies": []}
