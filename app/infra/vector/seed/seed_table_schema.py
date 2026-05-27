"""
table-store 컬렉션에 PostgreSQL inventory_mgmt 스키마 테이블의 풍부한 정보를 삽입합니다.
실행: python app/infra/vector/seed/seed_table_schema.py

용도:
    사용자 질문과 의미상 관련 있는 테이블만 동적으로 SQL 프롬프트에 주입.
    이전: 7개 테이블 정보를 매번 일괄 주입 (정적 schema_context)
    현재: RAG로 의미 매칭된 상위 N개 테이블만 동적 주입
"""

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
sys.path.insert(0, ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(ROOT, ".env"))

import chromadb
from google import genai

COLLECTION_NAME = "table-store"
EMBEDDING_MODEL = os.environ["EMBEDDING_MODEL"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
CHROMA_HOST = os.environ.get("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.environ.get("CHROMA_PORT", 8000))


TABLE_DEFINITIONS = [
    {
        "table": "products",
        "purpose": "제품 마스터. 회사가 취급하는 약 300종 전자부품 핵심 정보. 부품 카테고리·표준 원가·표준 판매가.",
        "columns": ["part_number", "description", "std_unit_cost", "std_selling_price"],
        "primary_key": "part_number",
        "column_notes": (
            "part_number: 부품 고유번호 PK (예: 80-CBR04C...). 다른 테이블과 JOIN 기준. | "
            "description: 카테고리 코드 (IC / C_CHIP/CAP / R_CHIP/RES 세 종류). 상세 설명 아님. | "
            "std_unit_cost: 표준 매입 원가 (예산 기준). 실제 매입단가는 purchase_orders.actual_unit_cost. | "
            "std_selling_price: 표준 판매가 (시장 고시가). 실제 판매단가는 sales_orders.actual_selling_price."
        ),
        "date_column": "",
        "cautions": "날짜 컬럼 없음 → 날짜 필터 절대 사용 금지.",
        "search_keywords": "부품 제품 품목 카테고리 종류 원가 판매가 표준가 part product",
    },
    {
        "table": "manufacturers",
        "purpose": "제조사·공급처 마스터. 부품을 공급하는 제조사 정보. 69개사.",
        "columns": ["manufacturer_id", "name"],
        "primary_key": "manufacturer_id",
        "column_notes": (
            "manufacturer_id: 공급처 식별자 PK. | "
            "name: 업체명 UNIQUE. 오타 변형 존재 (BROADCO/BROMDCOM/BRPADCOM=BROADCOM, INETL=INTEL, RENASAS=RENESAS)."
        ),
        "date_column": "",
        "cautions": "특정 제조사 필터 시 IN ('정식명','오타변형') 권장. 날짜 컬럼 없음.",
        "search_keywords": "제조사 공급처 메이커 manufacturer 업체 제조 brand 공급사",
    },
    {
        "table": "vendors",
        "purpose": "판매처·고객사 마스터. 부품을 구매하는 고객사 정보. 29개사.",
        "columns": ["vendor_id", "vendor_name"],
        "primary_key": "vendor_id",
        "column_notes": (
            "vendor_id: 고객사 식별자 PK. | "
            "vendor_name: 고객사명 (Digi-Key, Mouser, Farnell, RS, TI, ST, ROHM 등). 일부에 줄바꿈 문자 포함 가능."
        ),
        "date_column": "",
        "cautions": "vendor_name 필터 시 LIKE 검색 주의(공백/줄바꿈). 날짜 컬럼 없음.",
        "search_keywords": "거래처 고객사 판매처 vendor 바이어 buyer client",
    },
    {
        "table": "initial_inventory",
        "purpose": "시스템 운영 시작점(2022-12-31) 기준 초기 재고 스냅샷.",
        "columns": ["part_number", "initial_quantity", "stock_date"],
        "primary_key": "part_number",
        "column_notes": (
            "part_number: PK, FK→products. | "
            "initial_quantity: 기초 재고 수량 (200~800). | "
            "stock_date: 항상 '2022-12-31' 단일값."
        ),
        "date_column": "stock_date",
        "cautions": "stock_date는 단일값이라 의미 없음. 초기재고는 오직 이 테이블에만 존재(current_products에 없음). 초기재고 vs 현재재고 비교 시: current_products JOIN initial_inventory ON part_number.",
        "search_keywords": "초기재고 기초재고 시작재고 initial 2022 출발",
    },
    {
        "table": "current_products",
        "purpose": "실시간 재고 현황. 모든 입출고 이력을 합산한 최종 현재고.",
        "columns": ["part_number", "description", "current_quantity", "last_updated"],
        "primary_key": "part_number",
        "column_notes": (
            "part_number: PK, FK→products. | "
            "description: 카테고리 코드 (products.description과 동일). | "
            "current_quantity: 실시간 현재고 = 초기재고 + 총입고 - 총출고. | "
            "last_updated: 시스템 내부 갱신 타임스탬프(WHERE 필터 금지)."
        ),
        "date_column": "",
        "cautions": "재고 현황은 항상 전체 조회. 날짜 조건 없이 current_quantity 그대로 사용. initial_quantity 컬럼 없음(초기재고는 initial_inventory에서 JOIN).",
        "search_keywords": "재고 현재고 잔량 보유량 데드스톡 결품 품절 stock inventory",
    },
    {
        "table": "purchase_orders",
        "purpose": "구매·매입 이력. 제조사로부터 부품을 매입한 거래 내역. 13,615건.",
        "columns": ["purchase_id", "manufacturer_id", "part_number", "purchase_quantity", "purchase_date", "actual_unit_cost"],
        "primary_key": "purchase_id",
        "column_notes": (
            "purchase_id: PK. | "
            "manufacturer_id: FK→manufacturers. 반드시 JOIN 필요. | "
            "part_number: FK→products. | "
            "purchase_quantity: 입고 수량 (500~1500 대량 입고). | "
            "purchase_date: 입고 일자. 매월 1일·15일 배치 발주. | "
            "actual_unit_cost: 실제 매입단가."
        ),
        "date_column": "purchase_date",
        "cautions": "매입 금액 = purchase_quantity * actual_unit_cost. 날짜 필터 사용 가능('YYYY-MM-DD', DATE_TRUNC/EXTRACT).",
        "search_keywords": "매입 구매 입고 발주 purchase 제조사 cost",
    },
    {
        "table": "sales_orders",
        "purpose": "판매·매출 이력. 고객사에 부품을 판매한 거래 내역. 39,572건. 데이터 범위 2023-01-04 ~ 2025-12-31.",
        "columns": ["order_id", "vendor_id", "part_number", "sale_quantity", "sale_date", "actual_selling_price"],
        "primary_key": "order_id",
        "column_notes": (
            "order_id: PK. | "
            "vendor_id: FK→vendors. 반드시 JOIN 필요. | "
            "part_number: FK→products. | "
            "sale_quantity: 출고 수량 (20~150 분할 출고). | "
            "sale_date: 출고 일자. 매주 수·금요일 정기 납품. | "
            "actual_selling_price: 실제 판매단가."
        ),
        "date_column": "sale_date",
        "cautions": "매출액 = sale_quantity * actual_selling_price. 수익 = sale_quantity * (actual_selling_price - products.std_unit_cost). vendor_name 필터 시 vendors JOIN 후 사용.",
        "search_keywords": "매출 판매 출고 거래 sales 고객사 vendor 마진 수익 revenue",
    },
]


def build_doc(t: dict) -> str:
    """임베딩과 BM25 양쪽에 잘 매칭되도록 의미 키워드 풍부하게 구성."""
    return (
        f"{t['table']}: {t['purpose']} "
        f"{t['search_keywords']} "
        f"컬럼: {', '.join(t['columns'])}"
    )


def build_meta(t: dict) -> dict:
    return {
        "type": "table_schema",
        "table": t["table"],
        "purpose": t["purpose"],
        "columns": ",".join(t["columns"]),
        "primary_key": t["primary_key"],
        "column_notes": t["column_notes"],
        "date_column": t["date_column"],
        "cautions": t["cautions"],
    }


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

    ids = [t["table"] for t in TABLE_DEFINITIONS]
    docs = [build_doc(t) for t in TABLE_DEFINITIONS]
    metadatas = [build_meta(t) for t in TABLE_DEFINITIONS]

    print(f"임베딩 계산 중 ({len(docs)}개)...")
    embeddings = embed_texts(docs)

    collection.add(ids=ids, embeddings=embeddings, documents=docs, metadatas=metadatas)

    print(f"삽입 완료: {len(ids)}개 항목")
    for t in TABLE_DEFINITIONS:
        print(f"  - {t['table']}: {t['purpose'][:70]}")


if __name__ == "__main__":
    main()
