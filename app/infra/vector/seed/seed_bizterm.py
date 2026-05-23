"""
bizterm_store 컬렉션에 BUSINESS_LOGIC 딕셔너리 데이터를 삽입합니다.
실행: python app/infra/seed/seed_bizterm.py
"""

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
sys.path.insert(0, ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(ROOT, ".env"))

import chromadb
from google import genai
from app.prompts.business_logic import BUSINESS_LOGIC

COLLECTION_NAME = "bizterm_store"
EMBEDDING_MODEL = os.environ["EMBEDDING_MODEL"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
CHROMA_HOST = os.environ.get("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.environ.get("CHROMA_PORT", 8000))


def embed_texts(texts: list[str]) -> list[list[float]]:
    client = genai.Client(api_key=GEMINI_API_KEY)
    response = client.models.embed_content(model=EMBEDDING_MODEL, contents=texts)
    return [emb.values for emb in response.embeddings]


def main():
    client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT, ssl=False)

    try:
        client.delete_collection(COLLECTION_NAME)
        print(f"기존 '{COLLECTION_NAME}' 컬렉션 삭제 완료")
    except Exception:
        pass

    collection = client.create_collection(COLLECTION_NAME)
    print(f"'{COLLECTION_NAME}' 컬렉션 생성 완료")

    table_names = list(BUSINESS_LOGIC.keys())
    descriptions = list(BUSINESS_LOGIC.values())

    print(f"임베딩 계산 중 ({len(table_names)}개)...")
    embeddings = embed_texts(descriptions)

    ids = table_names
    documents = table_names  # BiztermStrategy.format: f"{d}: {m.get('desc')}"
    metadatas = [
        {"type": "bizterm", "table": name, "desc": desc}
        for name, desc in zip(table_names, descriptions)
    ]

    collection.add(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)

    print(f"삽입 완료: {len(ids)}개 항목")
    for name in table_names:
        print(f"  - {name}")


if __name__ == "__main__":
    main()
