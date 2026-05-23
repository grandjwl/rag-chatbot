"""
ChromaDB 컬렉션 조회 유틸리티
실행: python app/infra/vector/viewer.py

사용 예시:
    # 전체 컬렉션 목록 + 문서 수
    list_collections()

    # 특정 컬렉션 샘플 출력
    show_sample("bizterm_store", n=3)
    show_sample("table_schema_store")
    show_sample("refine_store", n=5)
    show_sample("fewshot")

    # 텍스트로 의미 검색
    search("bizterm_store", "매출 관련 테이블이 뭐야?", top_k=3)
    search("table_schema_store", "날짜 컬럼이 있는 테이블", top_k=2)
    search("fewshot", "연도별 매출 합계", top_k=3)
"""

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.insert(0, ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(ROOT, ".env"))

import chromadb
from google import genai

CHROMA_HOST = os.environ.get("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.environ.get("CHROMA_PORT", 8000))
EMBEDDING_MODEL = os.environ["EMBEDDING_MODEL"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

_chroma = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT, ssl=False)


def list_collections():
    """전체 컬렉션 목록과 문서 수 출력"""
    collections = _chroma.list_collections()
    if not collections:
        print("컬렉션 없음")
        return
    print(f"{'컬렉션명':<30} {'문서 수':>6}")
    print("-" * 38)
    for col in collections:
        c = _chroma.get_collection(col.name)
        print(f"{col.name:<30} {c.count():>6}")


def show_sample(collection_name: str, n: int = 3):
    """컬렉션에서 n개 문서 샘플 출력"""
    try:
        col = _chroma.get_collection(collection_name)
    except Exception:
        print(f"컬렉션 '{collection_name}' 없음")
        return

    total = col.count()
    data = col.get(limit=n)

    print(f"\n[{collection_name}] 총 {total}개 중 {n}개 샘플")
    print("-" * 50)
    for doc, meta, id_ in zip(data["documents"], data["metadatas"], data["ids"]):
        print(f"ID  : {id_}")
        print(f"DOC : {doc[:80]}{'...' if len(doc) > 80 else ''}")
        print(f"META: {meta}")
        print()


def search(collection_name: str, query: str, top_k: int = 3):
    """텍스트로 의미 검색 (임베딩 사용)"""
    try:
        col = _chroma.get_collection(collection_name)
    except Exception:
        print(f"컬렉션 '{collection_name}' 없음")
        return

    client = genai.Client(api_key=GEMINI_API_KEY)
    response = client.models.embed_content(model=EMBEDDING_MODEL, contents=[query])
    embedding = response.embeddings[0].values

    results = col.query(query_embeddings=[embedding], n_results=top_k)

    print(f"\n[{collection_name}] 검색: '{query}'")
    print("-" * 50)
    docs = results["documents"][0]
    metas = results["metadatas"][0]
    distances = results["distances"][0]
    for doc, meta, dist in zip(docs, metas, distances):
        print(f"거리  : {dist:.4f}")
        print(f"DOC  : {doc[:80]}{'...' if len(doc) > 80 else ''}")
        print(f"META : {meta}")
        print()


if __name__ == "__main__":
    list_collections()
