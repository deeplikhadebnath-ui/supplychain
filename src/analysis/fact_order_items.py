from pathlib import Path
import pandas as pd


# ==================================================
# 1. PATHS
# ==================================================

BASE_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = BASE_DIR / "data" / "cleaned"
OUTPUT_DIR = BASE_DIR / "data" / "analytical"
REPORT_DIR = BASE_DIR / "reports"

ORDER_DETAILS_FILE = DATA_DIR / "order_details_cleaned.csv"
PRODUCTS_FILE = DATA_DIR / "products_cleaned.csv"
ORDERS_FILE = DATA_DIR / "orders_cleaned.csv"
SUPPLIERS_FILE = DATA_DIR / "suppliers_cleaned.csv"

OUTPUT_FILE = OUTPUT_DIR / "fact_order_items.csv"
REPORT_FILE = REPORT_DIR / "fact_order_items_report.txt"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)


# ==================================================
# 2. LOAD DATA
# ==================================================

order_details = pd.read_csv(ORDER_DETAILS_FILE)
products = pd.read_csv(PRODUCTS_FILE)
orders = pd.read_csv(ORDERS_FILE)
suppliers = pd.read_csv(SUPPLIERS_FILE)

rows_before = len(order_details)

print("Order Details:", order_details.shape)
print("Products:", products.shape)
print("Orders:", orders.shape)
print("Suppliers:", suppliers.shape)


# ==================================================
# 3. JOIN PRODUCTS
# ==================================================

product_columns = [
    "product_id",
    "product_name",
    "category",
    "supplier_id",
    "unit_price",
    "is_active"
]

fact = order_details.merge(
    products[product_columns],
    on="product_id",
    how="left",
    validate="many_to_one"
)


# ==================================================
# 4. JOIN ORDERS
# ==================================================

order_columns = [
    "order_id",
    "customer_id",
    "warehouse_id",
    "order_date",
    "order_status"
]

fact = fact.merge(
    orders[order_columns],
    on="order_id",
    how="left",
    validate="many_to_one"
)

print("\nRows after joins:", len(fact))


# ==================================================
# 5. RENAME SOURCE VALUES
# ==================================================

fact = fact.rename(
    columns={
        "line_total": "source_line_total"
    }
)


# ==================================================
# 6. CALCULATED LINE TOTAL
# ==================================================

fact["calculated_line_total"] = pd.NA

calculation_ready = (
    fact["unit_price"].notna()
    & fact["quantity"].notna()
    & fact["discount_pct"].notna()
)

fact.loc[calculation_ready, "calculated_line_total"] = (
    fact.loc[calculation_ready, "unit_price"]
    * fact.loc[calculation_ready, "quantity"]
    * (
        1
        - fact.loc[calculation_ready, "discount_pct"] / 100
    )
)


# ==================================================
# 7. LINE TOTAL DIFFERENCE
# ==================================================

fact["line_total_difference"] = pd.NA

comparison_ready = (
    fact["source_line_total"].notna()
    & fact["calculated_line_total"].notna()
)

fact.loc[comparison_ready, "line_total_difference"] = (
    fact.loc[comparison_ready, "source_line_total"]
    - fact.loc[comparison_ready, "calculated_line_total"]
)


# ==================================================
# 8. LINE TOTAL STATUS
# ==================================================

fact["line_total_status"] = "Cannot Calculate"

matched = (
    comparison_ready
    & (
        fact["line_total_difference"].abs()
        <= 0.01
    )
)

mismatch = (
    comparison_ready
    & (
        fact["line_total_difference"].abs()
        > 0.01
    )
)

missing_source_total = (
    fact["source_line_total"].isna()
    & calculation_ready
)

fact.loc[matched, "line_total_status"] = "Matched"

fact.loc[mismatch, "line_total_status"] = "Mismatch"

fact.loc[
    missing_source_total,
    "line_total_status"
] = "Missing Source Total"


# ==================================================
# 9. GROSS LINE AMOUNT
# ==================================================

fact["gross_line_amount"] = pd.NA

fact.loc[calculation_ready, "gross_line_amount"] = (
    fact.loc[calculation_ready, "unit_price"]
    * fact.loc[calculation_ready, "quantity"]
)


# ==================================================
# 10. NET LINE AMOUNT
# ==================================================

fact["net_line_amount"] = fact["calculated_line_total"]


# ==================================================
# 11. DISCOUNT AMOUNT
# ==================================================

fact["discount_amount"] = pd.NA

discount_ready = (
    fact["gross_line_amount"].notna()
    & fact["net_line_amount"].notna()
)

fact.loc[discount_ready, "discount_amount"] = (
    fact.loc[discount_ready, "gross_line_amount"]
    - fact.loc[discount_ready, "net_line_amount"]
)


# ==================================================
# 12. TRANSACTION TYPE
# ==================================================

fact["transaction_type"] = pd.NA

fact.loc[
    fact["quantity"] > 0,
    "transaction_type"
] = "Sale"

fact.loc[
    fact["quantity"] < 0,
    "transaction_type"
] = "Return / Reversal"


# ==================================================
# 13. SUPPLIER STATUS
# ==================================================

valid_supplier_ids = set(
    suppliers["supplier_id"].dropna()
)

fact["supplier_status"] = "Matched"

# supplier_id is missing
fact.loc[
    fact["supplier_id"].isna(),
    "supplier_status"
] = "Missing Supplier Reference"

# supplier_id exists but is not in Suppliers master
fact.loc[
    fact["supplier_id"].notna()
    & ~fact["supplier_id"].isin(valid_supplier_ids),
    "supplier_status"
] = "Unmatched Supplier Reference"


# ==================================================
# 14. ORDER STATUS
# ==================================================

fact["order_status"] = fact["order_status"].astype("string")


# ==================================================
# 15. FINAL COLUMN ORDER
# ==================================================

final_columns = [
    "order_detail_id",
    "order_id",
    "product_id",
    "customer_id",
    "warehouse_id",
    "supplier_id",

    "order_date",
    "order_status",

    "product_name",
    "category",
    "is_active",

    "quantity",
    "unit_price",
    "discount_pct",
    "source_line_total",

    "gross_line_amount",
    "discount_amount",
    "net_line_amount",

    "calculated_line_total",
    "line_total_difference",
    "line_total_status",

    "transaction_type",
    "supplier_status"
]

fact = fact[final_columns]


# ==================================================
# 16. SAVE
# ==================================================

fact.to_csv(
    OUTPUT_FILE,
    index=False
)

rows_after = len(fact)


# ==================================================
# 17. VALIDATION
# ==================================================

duplicate_order_detail_id = (
    fact["order_detail_id"].duplicated().sum()
)

missing_order_detail_id = (
    fact["order_detail_id"].isna().sum()
)

missing_order_reference = (
    fact["customer_id"].isna()
    | fact["warehouse_id"].isna()
    | fact["order_status"].isna()
).sum()

calculated_rows = (
    fact["calculated_line_total"].notna()
).sum()

matched_rows = (
    fact["line_total_status"] == "Matched"
).sum()

missing_source_rows = (
    fact["line_total_status"]
    == "Missing Source Total"
).sum()

cannot_calculate_rows = (
    fact["line_total_status"]
    == "Cannot Calculate"
).sum()

mismatch_rows = (
    fact["line_total_status"] == "Mismatch"
).sum()

sale_rows = (
    fact["transaction_type"] == "Sale"
).sum()

return_rows = (
    fact["transaction_type"] == "Return / Reversal"
).sum()

missing_transaction_type = (
    fact["transaction_type"].isna()
).sum()

missing_supplier_reference = (
    fact["supplier_status"]
    == "Missing Supplier Reference"
).sum()

unmatched_supplier_reference = (
    fact["supplier_status"]
    == "Unmatched Supplier Reference"
).sum()


# ==================================================
# 18. STATUS
# ==================================================

if (
    len(fact) == rows_before
    and duplicate_order_detail_id == 0
    and missing_order_detail_id == 0
    and mismatch_rows == 0
):
    status = "PASS WITH WARNINGS"
else:
    status = "FAIL"


# ==================================================
# 19. REPORT
# ==================================================

report = f"""
FACT ORDER ITEMS - ANALYTICAL REPORT
====================================

GRAIN
-----
One row represents one order-detail/product line.

SOURCE ROWS
-----------
Order Details rows: {rows_before}

ROWS AFTER JOINS
----------------
Rows after Products join + Orders join: {rows_after}

Expected rows: {rows_before}
Row multiplication: {rows_after - rows_before}

CALCULATED LINE TOTAL
---------------------
Rows with enough data for calculation: {calculated_rows}

Formula:
unit_price * quantity * (1 - discount_pct / 100)

LINE TOTAL RECONCILIATION
-------------------------
Matched: {matched_rows}
Missing source total but calculable: {missing_source_rows}
Cannot calculate: {cannot_calculate_rows}
Mismatch: {mismatch_rows}

TRANSACTION TYPE
----------------
Sale rows: {sale_rows}
Return / Reversal rows: {return_rows}
Rows without transaction type: {missing_transaction_type}

SUPPLIER REFERENCE
------------------
Missing Supplier Reference: {missing_supplier_reference}
Unmatched Supplier Reference: {unmatched_supplier_reference}

ORDER INFORMATION
-----------------
Rows with missing customer/warehouse/order-status information:
{missing_order_reference}

PRIMARY KEY VALIDATION
----------------------
Duplicate order_detail_id: {duplicate_order_detail_id}
Missing order_detail_id: {missing_order_detail_id}

ANALYTICAL COLUMNS
------------------
calculated_line_total
line_total_difference
line_total_status
gross_line_amount
discount_amount
net_line_amount
transaction_type
supplier_status

SOURCE VALUES PRESERVED
-----------------------
source_line_total preserves the original line_total value.

No source financial values were overwritten.
No rows were intentionally deleted.

FEATURE ENGINEERING RULES
-------------------------
No customer-level metrics were created.
No product-level metrics were created.
No supplier-level metrics were created.
No inventory metrics were created.
No shipment metrics were created.

FINAL STATUS
------------
{status}
"""


REPORT_FILE.write_text(
    report,
    encoding="utf-8"
)


print("\nFact Order Items created successfully.")
print("Rows:", len(fact))
print("Columns:", len(fact.columns))
print("Output:", OUTPUT_FILE)
print("Report:", REPORT_FILE)
print("Final status:", status)