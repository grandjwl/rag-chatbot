"""
table_schema_store 컬렉션에 PostgreSQL inventory_mgmt 스키마 테이블 구조를 삽입합니다.
실행: python app/infra/seed/seed_table_schema.py
"""

import os
import sys
from collections import defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
sys.path.insert(0, ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(ROOT, ".env"))

import chromadb
import psycopg2
from google import genai

COLLECTION_NAME = "table_schema_store"
EMBEDDING_MODEL = os.environ["EMBEDDING_MODEL"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
CHROMA_HOST = os.environ.get("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.environ.get("CHROMA_PORT", 8000))

POSTGRES_HOST = os.environ["POSTGRES_HOST"]
POSTGRES_PORT = int(os.environ.get("POSTGRES_PORT", 5432))
POSTGRES_USER = os.environ["POSTGRES_USER"]
POSTGRES_PASSWORD = os.environ["POSTGRES_PASSWORD"]
POSTGRES_DB = os.environ["POSTGRES_DB"]
POSTGRES_SCHEMA = os.environ.get("POSTGRES_SCHEMA", "inventory_mgmt")


def fetch_table_schemas() -> list[tuple[str, str]]:
    conn = psycopg2.connect(
        host=POSTGRES_HOST, port=POSTGRES_PORT,
        user=POSTGRES_USER, password=POSTGRES_PASSWORD, dbname=POSTGRES_DB,
    )
    cur = conn.cursor()
    cur.execute(
        """
        SELECT table_name, column_name
        FROM information_schema.columns
        WHERE table_schema = %s
        ORDER BY table_name, ordinal_position
        """,
        (POSTGRES_SCHEMA,),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    table_columns: dict[str, list[str]] = defaultdict(list)
    for table_name, column_name in rows:
        table_columns[table_name].append(column_name)

    return [(table, f"{table}: {', '.join(cols)}") for table, cols in table_columns.items()]


def embed_texts(texts: list[str]) -> list[list[float]]:
    client = genai.Client(api_key=GEMINI_API_KEY)
    response = client.models.embed_content(model=EMBEDDING_MODEL, contents=texts)
    return [emb.values for emb in response.embeddings]


def main():
    print("PostgreSQL에서 테이블 스키마 조회 중...")
    schemas = fetch_table_schemas()
    print(f"테이블 {len(schemas)}개 조회 완료")

    client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT, ssl=False)

    try:
        client.delete_collection(COLLECTION_NAME)
        print(f"기존 '{COLLECTION_NAME}' 컬렉션 삭제 완료")
    except Exception:
        pass

    collection = client.create_collection(COLLECTION_NAME)
    print(f"'{COLLECTION_NAME}' 컬렉션 생성 완료")

    table_names = [t for t, _ in schemas]
    schema_texts = [s for _, s in schemas]

    print(f"임베딩 계산 중 ({len(schema_texts)}개)...")
    embeddings = embed_texts(schema_texts)

    collection.add(
        ids=table_names,
        embeddings=embeddings,
        documents=schema_texts,  # TableSchemaStrategy.format: "\n".join(docs)
        metadatas=[{"type": "table_schema", "table": name} for name in table_names],
    )

    print(f"삽입 완료: {len(table_names)}개 항목")
    for text in schema_texts:
        print(f"  - {text}")


if __name__ == "__main__":
    main()
