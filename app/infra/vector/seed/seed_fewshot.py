"""
fewshot-store 컬렉션을 빈 상태로 생성합니다.
실제 사용 검증된 질문-SQL 페어를 운영 중 직접 채워 나갑니다.
실행: python app/infra/vector/seed/seed_fewshot.py

추가 데이터 삽입 예시 (운영 단계):
    collection.add(
        ids=["q1"],
        embeddings=embed_texts(["이번달 매출 알려줘"]),
        documents=["이번달 매출 알려줘"],
        metadatas=[{
            "type": "fewshot",
            "sql": "SELECT SUM(sale_quantity * actual_selling_price) ...",
            "verified_at": "2026-05-27",
        }],
    )
"""

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
sys.path.insert(0, ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(ROOT, ".env"))

import chromadb

COLLECTION_NAME = "fewshot-store"
CHROMA_HOST = os.environ.get("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.environ.get("CHROMA_PORT", 8000))


def main():
    client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT, ssl=False)

    try:
        client.delete_collection(COLLECTION_NAME)
        print(f"기존 '{COLLECTION_NAME}' 컬렉션 삭제 완료")
    except Exception:
        pass

    client.create_collection(COLLECTION_NAME)
    print(f"'{COLLECTION_NAME}' 빈 컬렉션 생성 완료 (운영 중 직접 채움)")


if __name__ == "__main__":
    main()
