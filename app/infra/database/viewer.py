"""
PostgreSQL 조회 유틸리티
실행: python app/infra/database/viewer.py

사용 예시:
    # 스키마 내 테이블 목록 + 행 수
    list_tables()
    list_tables(schema="sql_assistant")

    # 테이블 컬럼 구조 확인
    show_columns("products")
    show_columns("conversations", schema="sql_assistant")

    # 테이블 내용 샘플 출력
    show_sample("manufacturers")
    show_sample("sales_orders", n=5)
    show_sample("conversations", schema="sql_assistant", n=3)

    # 직접 SQL 실행
    query("SELECT COUNT(*) FROM inventory_mgmt.sales_orders")
    query("SELECT vendor_name FROM inventory_mgmt.vendors ORDER BY vendor_name")
    query(\"\"\"
        SELECT EXTRACT(YEAR FROM sale_date) AS year, COUNT(*)
        FROM inventory_mgmt.sales_orders
        GROUP BY year ORDER BY year
    \"\"\")
"""

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.insert(0, ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(ROOT, ".env"))

import psycopg2
import psycopg2.extras

POSTGRES_HOST = os.environ["POSTGRES_HOST"]
POSTGRES_PORT = int(os.environ.get("POSTGRES_PORT", 5432))
POSTGRES_USER = os.environ["POSTGRES_USER"]
POSTGRES_PASSWORD = os.environ["POSTGRES_PASSWORD"]
POSTGRES_DB = os.environ["POSTGRES_DB"]
DEFAULT_SCHEMA = os.environ.get("POSTGRES_SCHEMA", "inventory_mgmt")


def _connect():
    return psycopg2.connect(
        host=POSTGRES_HOST, port=POSTGRES_PORT,
        user=POSTGRES_USER, password=POSTGRES_PASSWORD, dbname=POSTGRES_DB,
    )


def list_tables(schema: str = DEFAULT_SCHEMA):
    """스키마 내 테이블 목록과 행 수 출력"""
    conn = _connect()
    cur = conn.cursor()
    cur.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = %s ORDER BY table_name",
        (schema,),
    )
    tables = [row[0] for row in cur.fetchall()]

    print(f"\n[{schema}] 테이블 목록")
    print(f"{'테이블명':<35} {'행 수':>8}")
    print("-" * 45)
    for table in tables:
        cur.execute(f"SELECT COUNT(*) FROM {schema}.{table}")
        count = cur.fetchone()[0]
        print(f"{table:<35} {count:>8,}")

    cur.close()
    conn.close()


def show_columns(table: str, schema: str = DEFAULT_SCHEMA):
    """테이블 컬럼 구조 출력"""
    conn = _connect()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_schema = %s AND table_name = %s
        ORDER BY ordinal_position
        """,
        (schema, table),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    if not rows:
        print(f"테이블 '{schema}.{table}' 없음")
        return

    print(f"\n[{schema}.{table}] 컬럼 구조")
    print(f"{'컬럼명':<30} {'타입':<20} {'NULL':<6} {'기본값'}")
    print("-" * 70)
    for col, dtype, nullable, default in rows:
        print(f"{col:<30} {dtype:<20} {nullable:<6} {default or ''}")


def show_sample(table: str, schema: str = DEFAULT_SCHEMA, n: int = 3):
    """테이블 샘플 데이터 출력"""
    conn = _connect()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(f"SELECT * FROM {schema}.{table} LIMIT %s", (n,))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    if not rows:
        print(f"'{schema}.{table}' 데이터 없음")
        return

    print(f"\n[{schema}.{table}] 샘플 {n}개")
    print("-" * 60)
    for row in rows:
        for key, val in dict(row).items():
            val_str = str(val)
            print(f"  {key:<25}: {val_str[:60]}{'...' if len(val_str) > 60 else ''}")
        print()


def query(sql: str):
    """직접 SQL 실행 후 결과 출력"""
    conn = _connect()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(sql)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    if not rows:
        print("결과 없음")
        return

    headers = list(rows[0].keys())
    col_width = max(15, max(len(h) for h in headers) + 2)

    header_line = "  ".join(f"{h:<{col_width}}" for h in headers)
    print(f"\n{header_line}")
    print("-" * len(header_line))
    for row in rows:
        line = "  ".join(f"{str(v):<{col_width}}" for v in dict(row).values())
        print(line)
    print(f"\n총 {len(rows)}행")


if __name__ == "__main__":
    list_tables()
