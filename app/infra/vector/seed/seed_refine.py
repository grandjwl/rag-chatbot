"""
refine_store 컬렉션에 제조사명, 판매처명을 삽입합니다.
(파트넘버는 양이 많아 제외)
실행: python app/infra/seed/seed_refine.py
"""

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
sys.path.insert(0, ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(ROOT, ".env"))

import chromadb
import psycopg2
from google import genai

COLLECTION_NAME = "refine_store"
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


def fetch_names() -> tuple[list[str], list[str]]:
    conn = psycopg2.connect(
        host=POSTGRES_HOST, port=POSTGRES_PORT,
        user=POSTGRES_USER, password=POSTGRES_PASSWORD, dbname=POSTGRES_DB,
    )
    cur = conn.cursor()

    cur.execute(f"SELECT name FROM {POSTGRES_SCHEMA}.manufacturers ORDER BY name")
    manufacturers = [row[0] for row in cur.fetchall() if row[0]]

    cur.execute(f"SELECT vendor_name FROM {POSTGRES_SCHEMA}.vendors ORDER BY vendor_name")
    vendors = [row[0].strip() for row in cur.fetchall() if row[0]]

    cur.close()
    conn.close()
    return manufacturers, vendors


def embed_texts(texts: list[str]) -> list[list[float]]:
    client = genai.Client(api_key=GEMINI_API_KEY)
    response = client.models.embed_content(model=EMBEDDING_MODEL, contents=texts)
    return [emb.values for emb in response.embeddings]


def main():
    print("PostgreSQL에서 제조사/판매처 이름 조회 중...")
    manufacturers, vendors = fetch_names()
    print(f"제조사 {len(manufacturers)}개, 판매처 {len(vendors)}개 조회 완료")

    client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT, ssl=False)

    try:
        client.delete_collection(COLLECTION_NAME)
        print(f"기존 '{COLLECTION_NAME}' 컬렉션 삭제 완료")
    except Exception:
        pass

    collection = client.create_collection(COLLECTION_NAME)
    print(f"'{COLLECTION_NAME}' 컬렉션 생성 완료")

    all_texts = manufacturers + vendors
    all_ids = (
        [f"mfr_{i}" for i in range(len(manufacturers))]
        + [f"vnd_{i}" for i in range(len(vendors))]
    )
    all_metadatas = (
        [{"type": "manufacturer"} for _ in manufacturers]
        + [{"type": "vendor"} for _ in vendors]
    )

    print(f"임베딩 계산 중 ({len(all_texts)}개)...")
    embeddings = embed_texts(all_texts)

    collection.add(ids=all_ids, embeddings=embeddings, documents=all_texts, metadatas=all_metadatas)

    print(f"삽입 완료: {len(all_ids)}개 항목")
    print(f"  제조사: {len(manufacturers)}개")
    for m in manufacturers:
        print(f"    - {m}")
    print(f"  판매처: {len(vendors)}개")
    for v in vendors:
        print(f"    - {v}")


if __name__ == "__main__":
    main()
