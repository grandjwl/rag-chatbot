"""
refine-store 컬렉션에 다음 4종을 삽입합니다:
  - 제조사명 (manufacturers.name)
  - 판매처명 (vendors.vendor_name)
  - 부품 코드 (products.part_number) — 사용자가 길고 복잡한 코드를 자주 오타 침
  - 제조사 오타 변형 (BROADCO/INETL/RENASAS 등) — 사용자 입력 오타 보정용
실행: python app/infra/vector/seed/seed_refine.py
"""

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
sys.path.insert(0, ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(ROOT, ".env"))

import time

import chromadb
import psycopg2
from google import genai

COLLECTION_NAME = "refine-store"
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

# 사용자 입력 오타 보정용. doc은 오타 자체, original_id에 정식명을 두면 refine_service가 자동 치환.
MANUFACTURER_TYPOS = [
    ("BROADCO", "BROADCOM"),
    ("BROMDCOM", "BROADCOM"),
    ("BRPADCOM", "BROADCOM"),
    ("INETL", "INTEL"),
    ("RENASAS", "RENESAS"),
]


def fetch_names() -> tuple[list[str], list[str], list[str]]:
    conn = psycopg2.connect(
        host=POSTGRES_HOST, port=POSTGRES_PORT,
        user=POSTGRES_USER, password=POSTGRES_PASSWORD, dbname=POSTGRES_DB,
    )
    cur = conn.cursor()

    cur.execute(f"SELECT name FROM {POSTGRES_SCHEMA}.manufacturers ORDER BY name")
    manufacturers = [row[0] for row in cur.fetchall() if row[0]]

    cur.execute(f"SELECT vendor_name FROM {POSTGRES_SCHEMA}.vendors ORDER BY vendor_name")
    vendors = [row[0].strip() for row in cur.fetchall() if row[0]]

    cur.execute(f"SELECT part_number FROM {POSTGRES_SCHEMA}.products ORDER BY part_number")
    part_numbers = [row[0] for row in cur.fetchall() if row[0]]

    cur.close()
    conn.close()
    return manufacturers, vendors, part_numbers


def embed_texts(texts: list[str]) -> list[list[float]]:
    # Gemini는 batch당 최대 100개 + 분당 100 request 한도. 429 시 retry.
    BATCH = 100
    client = genai.Client(api_key=GEMINI_API_KEY)
    out: list[list[float]] = []
    for i in range(0, len(texts), BATCH):
        chunk = texts[i:i + BATCH]
        while True:
            try:
                response = client.models.embed_content(model=EMBEDDING_MODEL, contents=chunk)
                out.extend(emb.values for emb in response.embeddings)
                break
            except Exception as e:
                msg = str(e)
                if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
                    print(f"  ... quota 초과. 60초 후 재시도")
                    time.sleep(60)
                    continue
                raise
        print(f"  ... {min(i + BATCH, len(texts))}/{len(texts)} 완료")
    return out


def main():
    print("PostgreSQL에서 제조사/판매처/부품 코드 조회 중...")
    manufacturers, vendors, part_numbers = fetch_names()
    print(f"제조사 {len(manufacturers)}개, 판매처 {len(vendors)}개, 부품 코드 {len(part_numbers)}개 조회 완료")

    client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT, ssl=False)

    try:
        client.delete_collection(COLLECTION_NAME)
        print(f"기존 '{COLLECTION_NAME}' 컬렉션 삭제 완료")
    except Exception:
        pass

    collection = client.create_collection(COLLECTION_NAME)
    print(f"'{COLLECTION_NAME}' 컬렉션 생성 완료")

    typo_texts = [typo for typo, _ in MANUFACTURER_TYPOS]

    all_texts = manufacturers + typo_texts + vendors + part_numbers
    all_ids = (
        [f"mfr_{i}" for i in range(len(manufacturers))]
        + [f"mfr_typo_{i}" for i in range(len(MANUFACTURER_TYPOS))]
        + [f"vnd_{i}" for i in range(len(vendors))]
        + [f"part_{i}" for i in range(len(part_numbers))]
    )
    all_metadatas = (
        [{"type": "manufacturer"} for _ in manufacturers]
        + [{"type": "manufacturer", "original_id": orig} for _, orig in MANUFACTURER_TYPOS]
        + [{"type": "vendor"} for _ in vendors]
        + [{"type": "part_number"} for _ in part_numbers]
    )

    print(f"임베딩 계산 중 ({len(all_texts)}개)...")
    embeddings = embed_texts(all_texts)

    collection.add(ids=all_ids, embeddings=embeddings, documents=all_texts, metadatas=all_metadatas)

    print(f"삽입 완료: {len(all_ids)}개 항목")
    print(f"  제조사: {len(manufacturers)}개 / 오타 변형: {len(MANUFACTURER_TYPOS)}개 / 판매처: {len(vendors)}개 / 부품 코드: {len(part_numbers)}개")


if __name__ == "__main__":
    main()
