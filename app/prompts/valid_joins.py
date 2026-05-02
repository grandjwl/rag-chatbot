# app\prompts\valid_joins.py

# [기능] part_number를 공유하는 모든 테이블 간의 10가지 교차 조합 및 제조사/고객사 외래키 매핑 완비

VALID_JOINS = {
    # part_number 기준 JOIN 조합
    frozenset(["products", "current_products"]): "part_number",
    frozenset(["products", "initial_inventory"]): "part_number",
    frozenset(["products", "purchase_orders"]): "part_number",
    frozenset(["products", "sales_orders"]): "part_number",
    frozenset(["current_products", "initial_inventory"]): "part_number",
    frozenset(["current_products", "purchase_orders"]): "part_number",
    frozenset(["current_products", "sales_orders"]): "part_number",
    frozenset(["initial_inventory", "purchase_orders"]): "part_number",
    frozenset(["initial_inventory", "sales_orders"]): "part_number",
    frozenset(["purchase_orders", "sales_orders"]): "part_number",
    # 별도 외래키 기준 JOIN
    frozenset(["purchase_orders", "manufacturers"]): "manufacturer_id",
    frozenset(["sales_orders", "vendors"]): "vendor_id",
}
