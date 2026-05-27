"""
bizterm-store 컬렉션에 비즈니스 용어를 삽입합니다.
실행: python app/infra/vector/seed/seed_bizterm.py

용도:
    사용자가 '회전율', '탑셀러', '마진율', '데드스톡' 같은 비즈니스 용어로
    질문했을 때, LLM이 그 용어의 정의와 계산식, 필요 테이블을 이해하고
    적절한 SQL을 만들 수 있도록 돕는다.
"""

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
sys.path.insert(0, ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(ROOT, ".env"))

import chromadb
from google import genai

COLLECTION_NAME = "bizterm-store"
EMBEDDING_MODEL = os.environ["EMBEDDING_MODEL"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
CHROMA_HOST = os.environ.get("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.environ.get("CHROMA_PORT", 8000))


BIZ_TERMS = [
    {
        "term": "매출",
        "synonyms": ["매상", "판매액", "sales"],
        "definition": "특정 기간 동안 고객사에 부품을 판매한 금액 합계.",
        "formula": "SUM(sale_quantity * actual_selling_price)",
        "tables": ["sales_orders"],
        "date_column": "sale_date",
    },
    {
        "term": "매입",
        "synonyms": ["구매", "매입액"],
        "definition": "특정 기간 동안 제조사로부터 부품을 매입한 금액 합계.",
        "formula": "SUM(purchase_quantity * actual_unit_cost)",
        "tables": ["purchase_orders"],
        "date_column": "purchase_date",
    },
    {
        "term": "수익",
        "synonyms": ["이익", "마진", "GP", "총이익", "매출총이익"],
        "definition": "판매 금액에서 표준 매입 원가를 뺀 값. 판매로 얻은 실제 이익.",
        "formula": "SUM(sale_quantity * (actual_selling_price - products.std_unit_cost))",
        "tables": ["sales_orders", "products"],
        "date_column": "sale_date",
        "note": "products.std_unit_cost는 표준 원가. 시점별 실제 매입가가 필요하면 purchase_orders.actual_unit_cost를 매칭해야 함.",
    },
    {
        "term": "마진율",
        "synonyms": ["수익률", "이익률", "GP%", "GP 마진율"],
        "definition": "매출 대비 수익 비율(%).",
        "formula": "SUM(sale_quantity * (actual_selling_price - products.std_unit_cost)) / SUM(sale_quantity * actual_selling_price) * 100",
        "tables": ["sales_orders", "products"],
    },
    {
        "term": "재고",
        "synonyms": ["현재고", "잔량", "재고량"],
        "definition": "실시간 보유 부품 수량. 초기재고 + 총입고 - 총출고로 계산되어 current_products에 저장돼 있다.",
        "formula": "current_products.current_quantity",
        "tables": ["current_products"],
        "note": "current_products에는 날짜 필터 적용 금지(시점별 재고가 아닌 누적 현황).",
    },
    {
        "term": "재고회전율",
        "synonyms": ["회전율", "재고 회전", "inventory turnover"],
        "definition": "특정 기간 동안 평균 재고가 몇 번 출고됐는지를 나타내는 비율. 높을수록 잘 팔리는 부품.",
        "formula": "기간 출고량(SUM sale_quantity) / 평균 재고(current_products.current_quantity)",
        "tables": ["sales_orders", "current_products"],
    },
    {
        "term": "데드스톡",
        "synonyms": ["악성재고", "묵힌재고", "안 팔리는 재고", "dead stock"],
        "definition": "최근 일정 기간 동안 한 번도 출고되지 않은 재고. 통상 6개월 이상 출고 0건인 부품.",
        "formula": "current_products의 part_number 중 sales_orders에서 최근 N개월간 출고 기록 없음",
        "tables": ["current_products", "sales_orders"],
    },
    {
        "term": "탑셀러",
        "synonyms": ["베스트셀러", "잘 팔리는 부품", "인기 부품", "top seller"],
        "definition": "매출액 또는 출고 수량 기준 상위 부품.",
        "formula": "SUM(sale_quantity * actual_selling_price) GROUP BY part_number ORDER BY 합계 DESC LIMIT N",
        "tables": ["sales_orders"],
    },
    {
        "term": "객단가",
        "synonyms": ["거래당 평균 매출", "AOV", "건당 매출"],
        "definition": "한 건의 거래에서 평균적으로 발생하는 매출액.",
        "formula": "AVG(sale_quantity * actual_selling_price) GROUP BY order_id",
        "tables": ["sales_orders"],
    },
    {
        "term": "YoY",
        "synonyms": ["전년 동기 대비", "작년 대비", "YoY 성장률"],
        "definition": "같은 기간을 전년도와 비교한 증감률.",
        "formula": "(당기 매출 - 전년 동기 매출) / 전년 동기 매출 * 100",
        "tables": ["sales_orders"],
        "note": "DATE_TRUNC 또는 EXTRACT(YEAR FROM sale_date)로 연도별 집계 후 비교.",
    },
    {
        "term": "MoM",
        "synonyms": ["전월 대비", "지난달 대비", "MoM 성장률"],
        "definition": "이번 달을 전월과 비교한 증감률.",
        "formula": "(이번 달 매출 - 전월 매출) / 전월 매출 * 100",
        "tables": ["sales_orders"],
    },
    {
        "term": "카테고리별 매출",
        "synonyms": ["부품 종류별 매출", "description별 매출"],
        "definition": "부품 카테고리(IC, R_CHIP/RES, C_CHIP/CAP) 별 매출.",
        "formula": "GROUP BY products.description, SUM(sale_quantity * actual_selling_price)",
        "tables": ["sales_orders", "products"],
        "note": "description 값은 정확히 'IC', 'R_CHIP/RES', 'C_CHIP/CAP' 세 종류만 존재.",
    },
    {
        "term": "거래처 집중도",
        "synonyms": ["고객사별 매출", "탑 거래처", "매출 비중", "vendor 집중도"],
        "definition": "전체 매출 중 특정 거래처가 차지하는 비중. 상위 거래처 의존도 파악.",
        "formula": "GROUP BY vendor_id, SUM(sale_quantity * actual_selling_price) / 전체 매출 * 100",
        "tables": ["sales_orders", "vendors"],
        "note": "vendor_name 필터 시 vendors JOIN 필수.",
    },
    {
        "term": "제조사 의존도",
        "synonyms": ["제조사별 매입", "탑 제조사", "공급처 집중도"],
        "definition": "전체 매입 중 특정 제조사가 차지하는 비중. 공급망 의존도 파악.",
        "formula": "GROUP BY manufacturer_id, SUM(purchase_quantity * actual_unit_cost) / 전체 매입 * 100",
        "tables": ["purchase_orders", "manufacturers"],
    },
    {
        "term": "결품",
        "synonyms": ["품절", "재고부족", "재고 없음", "stock-out"],
        "definition": "현재고가 0 또는 임계치 이하인 상태. 발주 필요 부품 식별용.",
        "formula": "current_products.current_quantity = 0 또는 < threshold",
        "tables": ["current_products"],
    },
]


def embed_texts(texts: list[str]) -> list[list[float]]:
    client = genai.Client(api_key=GEMINI_API_KEY)
    response = client.models.embed_content(model=EMBEDDING_MODEL, contents=texts)
    return [emb.values for emb in response.embeddings]


def build_doc(term: dict) -> str:
    """임베딩과 BM25 양쪽에서 잘 매칭되도록 term + synonyms를 doc에 모두 포함."""
    parts = [term["term"]] + term.get("synonyms", [])
    return " / ".join(parts)


def build_meta(t: dict) -> dict:
    meta = {
        "type": "bizterm",
        "term": t["term"],
        "definition": t["definition"],
        "formula": t["formula"],
        "tables": ",".join(t["tables"]),
        "synonyms": ",".join(t.get("synonyms", [])),
    }
    if t.get("date_column"):
        meta["date_column"] = t["date_column"]
    if t.get("note"):
        meta["note"] = t["note"]
    return meta


def main():
    client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT, ssl=False)

    try:
        client.delete_collection(COLLECTION_NAME)
        print(f"기존 '{COLLECTION_NAME}' 컬렉션 삭제 완료")
    except Exception:
        pass

    collection = client.create_collection(COLLECTION_NAME)
    print(f"'{COLLECTION_NAME}' 컬렉션 생성 완료")

    ids = [t["term"] for t in BIZ_TERMS]
    docs = [build_doc(t) for t in BIZ_TERMS]
    metadatas = [build_meta(t) for t in BIZ_TERMS]

    print(f"임베딩 계산 중 ({len(docs)}개)...")
    embeddings = embed_texts(docs)

    collection.add(ids=ids, embeddings=embeddings, documents=docs, metadatas=metadatas)

    print(f"삽입 완료: {len(ids)}개 항목")
    for t in BIZ_TERMS:
        syns = ", ".join(t.get("synonyms", []))
        print(f"  - {t['term']:<12} ({syns})")


if __name__ == "__main__":
    main()
