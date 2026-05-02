# app\prompts\business_logic.py

BUSINESS_LOGIC = {
    "products": """[제품 마스터] 회사가 취급하는 300종 전자부품 핵심 정보.
  - part_number: VARCHAR PK. 부품 고유번호 (예: 80-CBR04C...). 다른 테이블과 JOIN 기준.
  - description: VARCHAR. 부품 카테고리 코드 (IC / FET/TR / C_CHIP/CAP / R_CHIP/RES 등).
    ※ 카테고리 코드이며 상세 설명 아님. 정확한 코드값으로만 필터링.
  - std_unit_cost: NUMERIC. 표준 매입 원가. 예산 수립 기준가. 실제 매입단가는 purchase_orders.actual_unit_cost 사용.
  - std_selling_price: NUMERIC. 표준 판매가(시장 고시가). 실제 판매단가는 sales_orders.actual_selling_price 사용.
  ※ 날짜 컬럼 없음 → 날짜 필터 절대 사용 금지.""",

    "manufacturers": """[제조사/공급처] 부품을 공급하는 제조사 마스터. 총 69개사.
  - manufacturer_id: INTEGER PK. 공급처 식별자.
  - name: VARCHAR UNIQUE. 업체명. UNIQUE 제약으로 중복 등록 불가.
    ※ DB에 오타 변형 존재: BROADCO/BROMDCOM/BRPADCOM=BROADCOM, INETL=INTEL, RENASAS=RENESAS 등.
    ※ 특정 제조사 조회 시 IN ('정식명','오타변형') 형태로 처리 권장.
  ※ 날짜 컬럼 없음 → 날짜 필터 절대 사용 금지.""",

    "vendors": """[판매처/고객사] 부품을 구매하는 고객사 마스터. 총 29개사.
  - vendor_id: INTEGER PK. 고객사 식별자.
  - vendor_name: VARCHAR. 고객사명 (Digikey, Mouser, Farnell, RS, TI, ST, ROHM 등).
    ※ 일부 vendor_name에 줄바꿈 문자 포함 가능 (예: SAMSUNG WALSIN). LIKE 검색 시 주의.
  ※ 날짜 컬럼 없음 → 날짜 필터 절대 사용 금지.""",

    "initial_inventory": """[초기 재고 스냅샷] 시스템 운영 시작점(2022-12-31) 기준 재고량.
  - part_number: VARCHAR PK, FK → products.
  - initial_quantity: INTEGER. 기초 재고 수량 (200~800개 사이 부여).
  - stock_date: DATE. 기초 데이터 확정일. 항상 '2022-12-31' 단일값.
  ※ initial_quantity는 오직 initial_inventory 테이블에만 존재. current_products에는 없음.
  ※ 초기재고 vs 현재재고 비교 시: current_products cp JOIN initial_inventory ii ON cp.part_number=ii.part_number
  ※ 날짜 필터 가능하나 stock_date는 단일값이므로 의미 없음.""",

    "current_products": """[실시간 재고 현황] 모든 입출고 이력을 합산한 최종 현재고.
  - part_number: VARCHAR PK, FK → products.
  - description: VARCHAR. 카테고리 코드 (products.description과 동일).
  - current_quantity: INTEGER. 실시간 현재고 = 초기재고 + 총입고 - 총출고.
  - last_updated: DATE. 마지막 재고 계산 일자.
    ※ last_updated는 시스템 내부 갱신 타임스탬프. WHERE 필터 절대 사용 금지.
    ※ current_products에는 initial_quantity 컬럼이 없음. 초기재고는 initial_inventory 테이블에서 JOIN.
    ※ 재고 현황은 항상 전체 조회. 날짜 조건 없이 current_quantity 그대로 사용.""",

    "purchase_orders": """[구매/매입 이력] 제조사로부터 부품을 매입한 거래 내역. 총 13,615건.
  - purchase_id: INTEGER PK. 구매 건별 고유번호.
  - manufacturer_id: INTEGER FK → manufacturers.manufacturer_id. 반드시 JOIN 필요.
  - part_number: VARCHAR FK → products.
  - purchase_quantity: INTEGER. 입고 수량 (500~1,500개 대량 입고 단위).
  - purchase_date: DATE. 입고 일자. 매월 1일·15일 배치 발주 반영.
    ※ 날짜 필터 가능. 형식: 'YYYY-MM-DD'. DATE_TRUNC/EXTRACT 사용.
  - actual_unit_cost: NUMERIC. 실제 매입단가 (시점별 원가 추적용).
    ※ 매입 금액 계산: purchase_quantity * actual_unit_cost.""",

    "sales_orders": """[판매/매출 이력] 고객사에 부품을 판매한 거래 내역. 총 39,572건.
  - order_id: INTEGER PK. 판매 건별 고유번호.
  - vendor_id: INTEGER FK → vendors.vendor_id. 반드시 JOIN 필요.
  - part_number: VARCHAR FK → products.
  - sale_quantity: INTEGER. 출고 수량 (20~150개 분할 출고 단위).
  - sale_date: DATE. 출고 일자. 매주 수요일·금요일 정기 납품 반영.
    ※ 날짜 필터 가능. 형식: 'YYYY-MM-DD'. DATE_TRUNC/EXTRACT 사용.
    ※ 데이터 범위: 2023-01-04 ~ 2025-12-31.
  - actual_selling_price: NUMERIC. 실제 판매단가 (거래처별 실거래가 추적용).
    ※ 매출 금액 계산: sale_quantity * actual_selling_price.
    ※ 수익(총이익) 계산: sale_quantity * (actual_selling_price - products.std_unit_cost).
    ※ vendor_name으로 필터 시 반드시 vendors JOIN 후 vendor_name 조건 사용."""
}