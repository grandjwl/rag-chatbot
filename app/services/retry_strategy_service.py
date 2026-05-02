# llmServer/app/services/retry_strategy_service.py

import re
from typing import Dict


class RetryStrategyService:
    """
    ============================================================
    [Domain Role]
    DB 실행 에러 메시지를 분석하여
    SQL 수정 전략(hint)을 생성하는 분석 전용 서비스.

    ⚠️ 이 서비스는:
    - retry 여부를 결정하지 않음
    - state를 수정하지 않음
    - retry_count를 증가시키지 않음
    - error_type을 설정하지 않음

    오직 "전략 힌트 생성기" 역할만 수행한다.
    Retry 실행 여부는 Graph 레벨에서 판단.

    ============================================================
    [Input]
    - error_msg: str

    ============================================================
    [Output 구조 — 변경 금지]
    {
        "strategy": str | None,
        "hint": str
    }

    strategy 값:
        - "column_missing"
        - "table_missing"
        - "syntax"
        - "timeout"
        - "logic"
        - "unknown"
        - None

    ============================================================
    [Graph 사용 방식]

    SQLGenerateService:
        → hint를 프롬프트에 삽입

    RetryDecisionService:
        → strategy 값을 기반으로 retry 여부 판단

    ============================================================
    """

    def __init__(self, column_map: Dict):
        self.column_map = column_map

    def analyze(self, error_msg: str) -> Dict:

        # 에러 없음 → 전략 없음
        if not error_msg:
            return {"strategy": None, "hint": ""}

        err_lower = error_msg.lower()

        # --------------------------------------------------
        # 1️⃣ Column Missing
        # --------------------------------------------------
        if "does not exist" in err_lower and "column" in err_lower:

            col_match = re.search(r'column "?(\w+)"?', error_msg, re.IGNORECASE)
            missing = col_match.group(1) if col_match else None

            # 컬럼명 추출 실패 → unknown 유지
            if not missing:
                return {"strategy": "unknown", "hint": error_msg[:300]}

            found_in = [
                t
                for t, cols in self.column_map.items()
                if missing.lower() in [c.lower() for c in cols]
            ]

            hint = (
                f"'{missing}' 컬럼은 "
                f"{found_in[0] if found_in else '알 수 없는'} 테이블 소속."
            )

            if found_in:
                hint += f" JOIN {found_in[0]} 후 {found_in[0]}.{missing} 로 참조하세요."

            return {"strategy": "column_missing", "hint": hint}

        # --------------------------------------------------
        # 2️⃣ Table Missing
        # --------------------------------------------------
        if "relation" in err_lower and "does not exist" in err_lower:

            tbl_match = re.search(r'relation "?(\w+)"?', error_msg, re.IGNORECASE)
            missing = tbl_match.group(1) if tbl_match else "unknown"

            return {
                "strategy": "table_missing",
                "hint": f"테이블 '{missing}' 없음. 유효 테이블: {list(self.column_map.keys())}",
            }

        # --------------------------------------------------
        # 3️⃣ Syntax Error
        # --------------------------------------------------
        if "syntax error" in err_lower:
            return {
                "strategy": "syntax",
                "hint": (
                    "SQL 단순화: TO_DATE/DATE_TRUNC 중첩 금지. "
                    "EXTRACT(YEAR FROM col)=연도 사용. "
                    "복잡한 서브쿼리는 CTE(WITH절)로 분리."
                ),
            }

        # --------------------------------------------------
        # 4️⃣ Timeout
        # --------------------------------------------------
        if "timeout" in err_lower or "canceling" in err_lower:
            return {
                "strategy": "timeout",
                "hint": "타임아웃: LIMIT 10으로 축소, WHERE에 날짜 범위 추가, CTE로 분리.",
            }

        # --------------------------------------------------
        # 5️⃣ GROUP BY / Aggregate 오류
        # --------------------------------------------------
        if "group by" in err_lower or "aggregate" in err_lower:
            return {
                "strategy": "logic",
                "hint": "GROUP BY 오류: SELECT의 모든 비집계 컬럼을 GROUP BY에 포함하세요.",
            }

        # --------------------------------------------------
        # 6️⃣ Unknown (기본값 유지)
        # --------------------------------------------------
        return {"strategy": "unknown", "hint": error_msg[:300]}