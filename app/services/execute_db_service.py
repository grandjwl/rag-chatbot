# llmServer/app/services/execute_db_service.py

import re
import logging
from typing import Dict, Tuple, List
import sqlglot

from app.infra.database.rdb_repository import RDBRepository

logger = logging.getLogger(__name__)


class ExecuteDBService:
    """
    ============================================================
    [Domain Role]
    생성된 SQL을 실제 DB에서 실행하기 전 최종 검증 및 실행을 담당하는 Gatekeeper 서비스.

    역할:
        1️⃣ Basic Validation (보안 / 문법)
        2️⃣ Static Validation (논리 / 스키마 무결성)
        3️⃣ LIMIT 보호
        4️⃣ Schema 자동 주입
        5️⃣ 실제 DB 실행
        6️⃣ 실행 메타데이터 생성

    ============================================================
    🔥 Graph에서 관리할 영역 (이 서비스 바깥 책임)

    Graph는 다음을 관리해야 함:

        - retry_count 최종 정책
        - retry 가능 여부 판단
        - max retry 초과 시 최종 상태 결정
        - retry_strategy 누적 관리
        - error_history 통합 관리
        - result_validation 이후 재시도 여부 결정

    이 서비스는:
        ❌ retry 여부를 최종 판단하지 않음
        ❌ 전체 플로우 제어하지 않음
        ✅ 단일 실행 단위에 대한 결과만 반환

    ============================================================
    [Graph Input State Fields]

    - sql_query: str
    - retry_count: int
    - error_history: List[str]

    ============================================================
    [Graph Output State Fields]

    성공:
    {
        "rows": List[dict],
        "db_result": "SUCCESS",
        "retry_count": int,
        "retry_strategy": None,
        "error_type": None,
        "explain_meta": dict
    }

    실패 (재시도 가능):
    {
        "db_result": "Error: ...",
        "error_history": List[str],
        "retry_count": int+1,
        "retry_strategy": str,
        "error_type": "security" | "static" | "runtime"
    }

    실패 (재시도 초과):
    {
        "error_type": "max_retry"
    }

    ============================================================
    """

    MAX_RETRY = 3

    def __init__(
        self,
        rdb_repository: RDBRepository,
        column_map: dict,
        valid_joins: dict,
        db_schema: str,
        query_limit: int = 3000,
    ):
        self.rdb_repository = rdb_repository
        self.COLUMN_MAP = column_map or {}
        self.VALID_JOINS = valid_joins or {}
        self.db_schema = db_schema
        self.query_limit = query_limit

    # =====================================================
    # 🚀 MAIN
    # =====================================================

    async def execute(self, state: Dict) -> Dict:
        # 디버깅용
        # print("db_execute_service로 전달된 state:", state)
        raw_sql = state.get("sql_query", "")

        if isinstance(raw_sql, dict):
            # 만약 {'sql_query': 'SELECT ...'} 형태라면 내부 값 추출
            sql = raw_sql.get("sql_query", "")
        else:
            sql = raw_sql

        retry_count = state.get("retry_count", 0)
        error_history = state.get("error_history", [])

        if not sql.strip():
            return self._retry(
                "Empty SQL", error_history, retry_count, "syntax", "security"
            )

        if retry_count >= self.MAX_RETRY:
            return {
                "db_result": "Error: max retry exceeded",
                "error_history": error_history,
                "retry_count": retry_count,
                "retry_strategy": None,
                "error_type": "max_retry",
            }

        # 1️⃣ BASIC VALIDATION
        valid, reason = self._validate_basic(sql)
        if not valid:
            # 디버깅용
            # print("Basic validation failed:", reason)
            return self._retry(reason, error_history, retry_count, None, "security")

        # 2️⃣ STATIC VALIDATION
        # 디버깅용
        # print("SQL 실행 전 Static Validation 시작...")
        # print("검사 대상 SQL:", sql)
        valid, reason, strategy = self._validate_static(sql)
        if not valid:
            # 디버깅용
            # print("Static validation failed:", reason)
            return self._retry(reason, error_history, retry_count, strategy, "static")

        # 3️⃣ LIMIT PROTECTION
        safe_sql = self._apply_limit(sql)
        safe_sql = self._apply_schema(safe_sql)
        # 디버깅용
        # print("최종 실행 SQL:", safe_sql)
        try:
            rows = await self.rdb_repository.fetch(safe_sql)

            explain_meta = self._build_explain_meta(sql, rows)
            # 디버깅용
            # print("쿼리 실행 메타:", explain_meta)
            return {
                "rows": rows,
                "db_result": "SUCCESS",
                "retry_count": retry_count,
                "retry_strategy": None,
                "error_type": None,
                "explain_meta": explain_meta,
            }

        except Exception as e:
            logger.exception("쿼리 실행 오류")
            return self._retry(str(e), error_history, retry_count, "runtime", "runtime")

    # =====================================================
    # 🔒 BASIC VALIDATION
    # =====================================================

    def _validate_basic(self, sql: str) -> Tuple[bool, str]:

        stripped = sql.strip().upper()

        if not stripped.startswith(("SELECT", "WITH")):
            return False, "SELECT 또는 WITH로 시작해야 합니다."

        forbidden = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE"]
        for word in forbidden:
            if re.search(rf"\b{word}\b", stripped):
                return False, f"위험 구문 포함: {word}"

        try:
            sqlglot.parse_one(sql, dialect="postgres")
        except Exception as e:
            logger.warning(f"sqlglot 파싱 경고: {str(e)[:150]}")

        return True, ""

    # =====================================================
    # 🔎 STATIC VALIDATION (개념 전체 유지)
    # =====================================================

    def _validate_static(self, sql: str) -> Tuple[bool, str, str]:

        errors: List[str] = []
        strategy = "syntax"
        sql_upper = sql.upper()

        # 1️⃣ SELECT *
        if re.search(r"SELECT\s+\*", sql_upper):
            errors.append("SELECT * 금지. 필요한 컬럼 명시.")
            strategy = "syntax"

        # 2️⃣ GROUP BY 정확 판정
        has_agg = bool(re.search(r"\b(SUM|AVG|COUNT|MAX|MIN)\s*\(", sql_upper))
        has_grp = bool(re.search(r"\bGROUP\s+BY\b", sql_upper))
        has_win = bool(re.search(r"\bOVER\s*\(", sql_upper))

        if has_agg and not has_grp and not has_win:

            sel_match = re.search(
                r"SELECT\s+(.*?)\s+FROM",
                sql,
                re.IGNORECASE | re.DOTALL,
            )

            if sel_match:
                select_part = sel_match.group(1)

                cleaned = re.sub(
                    r"(SUM|AVG|COUNT|MAX|MIN)\s*\([^)]+\)",
                    "",
                    select_part,
                    flags=re.IGNORECASE,
                )

                non_agg_cols = [
                    c.strip()
                    for c in cleaned.split(",")
                    if c.strip() and c.strip() != ""
                ]

                if non_agg_cols:
                    errors.append("GROUP BY 누락: 비집계 컬럼 존재.")
                    strategy = "logic"
        # 3️⃣ Cartesian Product
        join_cnt = len(re.findall(r"\bJOIN\b", sql_upper))
        on_cnt = len(re.findall(r"\bON\b|\bUSING\b", sql_upper))
        if join_cnt > 0 and on_cnt < join_cnt:
            errors.append("Cartesian Product 위험: ON 조건 부족.")
            strategy = "logic"

        # 4️⃣ CTE 추출
        cte_names = re.findall(
            r"\b([a-zA-Z_][a-zA-Z0-9_]*)\s+AS\s*\(",
            sql,
            re.IGNORECASE,
        )

        # 5️⃣ 테이블 존재 확인
        # [수정 전]
        # ref_tables = re.findall(r"(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*)", sql, re.IGNORECASE)

        # [수정 후]
        # 1. EXTRACT(... FROM ...) 구문을 임시로 제거하여 오판 방지
        clean_sql_for_tables = re.sub(
            r"EXTRACT\s*\([^)]+\)", "", sql, flags=re.IGNORECASE
        )

        # 2. 독립된 단어로서의 FROM/JOIN만 추출 (\b 추가)
        ref_tables = re.findall(
            r"\b(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*)",
            clean_sql_for_tables,
            re.IGNORECASE,
        )

        skip_list = {n.lower() for n in cte_names} | {"_sub"}

        for tbl in ref_tables:
            if tbl.lower() not in self.COLUMN_MAP and tbl.lower() not in skip_list:
                errors.append(f"테이블 '{tbl}' 존재하지 않음.")
                strategy = "table_missing"

        # 6️⃣ 컬럼 소속
        col_valid, col_reason = self._validate_column_ownership(sql)
        if not col_valid:
            errors.append(col_reason)
            strategy = "column_missing"

        # 7️⃣ 불필요 JOIN
        join_aliases = re.findall(
            r"JOIN\s+[a-zA-Z_][a-zA-Z0-9_]*\s+(?:AS\s+)?([a-zA-Z_][a-zA-Z0-9_]*)",
            sql,
            re.IGNORECASE,
        )

        for alias in join_aliases:
            usage = re.findall(
                rf"\b{re.escape(alias)}\.",
                sql,
                re.IGNORECASE,
            )
            if not usage:
                errors.append(f"불필요한 JOIN: '{alias}' 사용되지 않음.")
                strategy = "logic"

        # 8️⃣ VALID_JOINS 강제
        join_valid, join_reason = self._validate_join_keys(sql)
        if not join_valid:
            errors.append(join_reason)
            strategy = "logic"

        if errors:
            return False, " | ".join(errors), strategy

        return True, "", "none"

    # =====================================================
    # 🧠 COLUMN OWNERSHIP + VALID JOIN
    # =====================================================

    def _validate_column_ownership(self, sql: str) -> Tuple[bool, str]:

        alias_map = {}

        for m in re.finditer(
            r"(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+(?:AS\s+)?([a-zA-Z_][a-zA-Z0-9_]*)",
            sql,
            re.IGNORECASE,
        ):
            tbl, alias = m.group(1).lower(), m.group(2).lower()
            alias_map[alias] = tbl
            alias_map[tbl] = tbl

        for m in re.finditer(
            r"\b([a-zA-Z_][a-zA-Z0-9_]*)\.([a-zA-Z_][a-zA-Z0-9_]*)\b",
            sql,
        ):
            alias, col = m.group(1).lower(), m.group(2).lower()

            if alias in alias_map:
                table = alias_map[alias]
                # CTE 이름은 COLUMN_MAP에 없으므로 실제 테이블만 검증
                if table in self.COLUMN_MAP:
                    if col not in [c.lower() for c in self.COLUMN_MAP.get(table, [])]:
                        return False, f"'{col}'은 '{table}' 테이블에 없음."

        return True, ""

    def _validate_join_keys(self, sql: str) -> Tuple[bool, str]:

        alias_map = {}

        for m in re.finditer(
            r"(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+(?:AS\s+)?([a-zA-Z_][a-zA-Z0-9_]*)",
            sql,
            re.IGNORECASE,
        ):
            tbl, alias = m.group(1).lower(), m.group(2).lower()
            alias_map[alias] = tbl
            alias_map[tbl] = tbl

        for m in re.finditer(
            r"ON\s+([a-zA-Z_]+)\.([a-zA-Z_]+)\s*=\s*([a-zA-Z_]+)\.([a-zA-Z_]+)",
            sql,
            re.IGNORECASE,
        ):
            a1, c1, a2, c2 = m.groups()
            t1 = alias_map.get(a1.lower())
            t2 = alias_map.get(a2.lower())

            if t1 and t2 and t1 != t2:
                expected = self.VALID_JOINS.get(frozenset([t1, t2]))
                if expected and (c1.lower() != expected or c2.lower() != expected):
                    return False, (f"{t1}-{t2}는 '{expected}'로 JOIN해야 함.")

        return True, ""

    # =====================================================
    # 🔄 RETRY
    # =====================================================

    def _retry(self, reason, error_history, retry_count, strategy, error_type):

        return {
            "db_result": f"Error: {reason}",
            "error_history": error_history + [reason],
            "retry_count": retry_count + 1,
            "retry_strategy": strategy,
            "error_type": error_type,
        }

    # =====================================================
    # 🛡 LIMIT
    # =====================================================

    def _apply_limit(self, sql: str) -> str:

        if re.search(r"\bLIMIT\b", sql, re.IGNORECASE):
            return sql

        return f"SELECT * FROM ({sql}) AS _sub LIMIT {self.query_limit}"

    # =====================================================
    # 📊 EXPLAIN
    # =====================================================

    def _build_explain_meta(self, sql: str, rows) -> dict:

        # 1️⃣ EXTRACT 내부 제거 (FROM sale_date 같은 오탐 방지)
        clean_sql = re.sub(
            r"EXTRACT\s*\([^)]+\)",
            "",
            sql,
            flags=re.IGNORECASE,
        )

        # 2️⃣ schema.table 구조까지 잡도록 수정
        tables_raw = re.findall(
            r"\b(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_.]*)",
            clean_sql,
            re.IGNORECASE,
        )

        # 3️⃣ 실제 존재하는 테이블만 필터링
        tables_used = []

        for t in tables_raw:
            table_name = t.split(".")[-1]  # schema 제거
            if table_name.lower() in self.COLUMN_MAP:
                tables_used.append(table_name)

        tables_used = list(set(tables_used))

        # 집계 추출
        aggs = re.findall(
            r"(SUM|AVG|COUNT|MAX|MIN)\s*\(([^)]+)\)",
            sql,
            re.IGNORECASE,
        )

        return {
            "sql_used": sql,
            "tables_used": tables_used,
            "aggregations": [f"{fn.upper()}({col.strip()})" for fn, col in aggs],
            "row_count": len(rows) if rows else 0,
        }

    # =====================================================
    # 🗄 SCHEMA 자동 주입
    # =====================================================
    def _apply_schema(self, sql: str) -> str:
        """
        FROM / JOIN 절의 테이블에 schema 자동 주입
        """
        # WITH 절에서 CTE 이름 추출 (스키마 주입 대상에서 제외)
        cte_names = {
            m.group(1).lower()
            for m in re.finditer(r"\b(\w+)\s+AS\s*\(", sql, re.IGNORECASE)
        }

        def replace_from(match):
            keyword = match.group(1)
            table = match.group(2)

            # EXTRACT 함수 내부의 FROM 인지 확인
            prefix = sql[: match.start()].lower()
            if (
                "extract" in prefix
                and "(" in prefix
                and ")" not in prefix.split("extract")[-1]
            ):
                return match.group(0)

            if "." in table:
                return match.group(0)

            # CTE 이름은 스키마 주입 대상 제외
            if table.lower() in cte_names:
                return match.group(0)

            return f"{keyword} {self.db_schema}.{table}"

        pattern = r"\b(FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*)"
        return re.sub(pattern, replace_from, sql, flags=re.IGNORECASE)
