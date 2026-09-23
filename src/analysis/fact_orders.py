from pathlib import Path
import pandas as pd


# ==================================================
# 1. PATHS
# ==================================================

BASE_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = BASE_DIR / "data" / "cleaned"
OUTPUT_DIR = BASE_DIR / "data" / "analytical"
REPORT_DIR = BASE_DIR / "reports"

ORDERS_FILE = DATA_DIR / "orders_cleaned.csv"
ORDER_DETAILS_FILE = DATA_DIR / "order_details_cleaned.csv"
SHIPMENTS_FILE = DATA_DIR / "shipments_cleaned.csv"
CUSTOMERS_FILE = DATA_DIR / "customers_cleaned.csv"

OUTPUT_FILE = OUTPUT_DIR / "fact_orders.csv"
REPORT_FILE = REPORT_DIR / "fact_orders_report.txt"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)


# ==================================================
# 2. LOAD DATA
# ==================================================

orders = pd.read_csv(ORDERS_FILE)
order_details = pd.read_csv(ORDER_DETAILS_FILE)
shipments = pd.read_csv(SHIPMENTS_FILE)
customers = pd.read_csv(CUSTOMERS_FILE)

rows_before = len(orders)

print("Orders:", orders.shape)
print("Order Details:", order_details.shape)
print("Shipments:", shipments.shape)
print("Customers:", customers.shape)


# ==================================================
# 3. BASIC TYPE CONVERSION
# ==================================================

orders["order_total"] = pd.to_numeric(
    orders["order_total"],
    errors="coerce"
)

order_details["quantity"] = pd.to_numeric(
    order_details["quantity"],
    errors="coerce"
)

order_details["line_total"] = pd.to_numeric(
    order_details["line_total"],
    errors="coerce"
)

orders["order_date"] = pd.to_datetime(
    orders["order_date"],
    errors="coerce"
)

orders["ship_date"] = pd.to_datetime(
    orders["ship_date"],
    errors="coerce"
)


# ==================================================
# 4. AGGREGATE ORDER DETAILS
# ==================================================

detail_summary = (
    order_details
    .groupby("order_id")
    .agg(
        detail_row_count=("order_detail_id", "count"),
        total_quantity=("quantity", "sum"),
        calculated_order_total=(
            "line_total",
            lambda x: x.sum(min_count=1)
        )
    )
    .reset_index()
)

print(
    "\nOrder-level detail summary rows:",
    len(detail_summary)
)

# ==================================================
# 5. AGGREGATE SHIPMENTS
# ==================================================

shipment_summary = (
    shipments
    .groupby("order_id")
    .agg(
        shipment_count=("order_id", "count")
    )
    .reset_index()
)

print(
    "Order-level shipment summary rows:",
    len(shipment_summary)
)


# ==================================================
# 6. JOIN DETAIL SUMMARY TO ORDERS
# ==================================================

fact = orders.merge(
    detail_summary,
    on="order_id",
    how="left",
    validate="one_to_one"
)

rows_after_details = len(fact)

print(
    "Rows after Order Details summary join:",
    rows_after_details
)


# ==================================================
# 7. JOIN SHIPMENT SUMMARY TO ORDERS
# ==================================================

fact = fact.merge(
    shipment_summary,
    on="order_id",
    how="left",
    validate="one_to_one"
)

rows_after_shipments = len(fact)

print(
    "Rows after Shipment summary join:",
    rows_after_shipments
)


# ==================================================
# 8. SOURCE ORDER TOTAL
# ==================================================

fact = fact.rename(
    columns={
        "order_total": "source_order_total"
    }
)


# ==================================================
# 9. SHIPMENT FIELDS
# ==================================================

fact["shipment_count"] = (
    fact["shipment_count"]
    .fillna(0)
    .astype(int)
)

fact["has_shipment"] = (
    fact["shipment_count"] > 0
)


# ==================================================
# 10. FINANCIAL DIFFERENCE
# ==================================================

fact["order_total_difference"] = pd.NA

comparison_ready = (
    fact["source_order_total"].notna()
    & fact["calculated_order_total"].notna()
)

fact.loc[comparison_ready, "order_total_difference"] = (
    fact.loc[comparison_ready, "source_order_total"]
    - fact.loc[comparison_ready, "calculated_order_total"]
)


# ==================================================
# 11. FINANCIAL STATUS
# ==================================================

fact["order_financial_status"] = "Cannot Calculate"

matched = (
    comparison_ready
    & (
        fact["order_total_difference"].abs()
        <= 0.01
    )
)

mismatch = (
    comparison_ready
    & (
        fact["order_total_difference"].abs()
        > 0.01
    )
)

missing_source_total = (
    fact["source_order_total"].isna()
    & fact["calculated_order_total"].notna()
)

fact.loc[
    matched,
    "order_financial_status"
] = "Matched"

fact.loc[
    mismatch,
    "order_financial_status"
] = "Mismatch"

fact.loc[
    missing_source_total,
    "order_financial_status"
] = "Missing Source Total"


# ==================================================
# 12. DETAIL STATUS
# ==================================================

fact["detail_status"] = "No Order Details"

fact.loc[
    fact["detail_row_count"].notna(),
    "detail_status"
] = "Has Order Details"


# ==================================================
# 13. CUSTOMER STATUS
# ==================================================

valid_customer_ids = set(
    customers["customer_id"].dropna()
)

fact["customer_status"] = "Matched"

fact.loc[
    fact["customer_id"].isna(),
    "customer_status"
] = "Missing Customer Reference"

fact.loc[
    fact["customer_id"].notna()
    & ~fact["customer_id"].isin(valid_customer_ids),
    "customer_status"
] = "Unmatched Customer Reference"


# ==================================================
# 14. ORDER QUANTITY STATUS
# ==================================================

fact["quantity_status"] = pd.NA

fact.loc[
    fact["total_quantity"] > 0,
    "quantity_status"
] = "Positive Net Quantity"

fact.loc[
    fact["total_quantity"] < 0,
    "quantity_status"
] = "Negative Net Quantity"

fact.loc[
    fact["total_quantity"] == 0,
    "quantity_status"
] = "Zero Net Quantity"


# ==================================================
# 15. DATE STATUS
# ==================================================

fact["date_status"] = "Valid"

fact.loc[
    fact["ship_date"].isna(),
    "date_status"
] = "Missing Ship Date"

fact.loc[
    fact["order_date"].notna()
    & fact["ship_date"].notna()
    & (
        fact["ship_date"] < fact["order_date"]
    ),
    "date_status"
] = "Ship Date Before Order Date"


# ==================================================
# 16. FINAL COLUMN ORDER
# ==================================================

final_columns = [
    "order_id",
    "customer_id",
    "warehouse_id",

    "order_date",
    "ship_date",
    "order_status",

    "source_order_total",

    "detail_row_count",
    "total_quantity",
    "calculated_order_total",

    "order_total_difference",
    "order_financial_status",

    "shipment_count",
    "has_shipment",

    "detail_status",
    "customer_status",
    "quantity_status",
    "date_status"
]

fact = fact[final_columns]


# ==================================================
# 17. SAVE
# ==================================================

fact.to_csv(
    OUTPUT_FILE,
    index=False
)

rows_after = len(fact)


# ==================================================
# 18. VALIDATION
# ==================================================

duplicate_order_id = (
    fact["order_id"].duplicated().sum()
)

missing_order_id = (
    fact["order_id"].isna().sum()
)

financial_match = (
    fact["order_financial_status"]
    == "Matched"
).sum()

financial_mismatch = (
    fact["order_financial_status"]
    == "Mismatch"
).sum()

missing_source_total_rows = (
    fact["order_financial_status"]
    == "Missing Source Total"
).sum()

cannot_calculate_rows = (
    fact["order_financial_status"]
    == "Cannot Calculate"
).sum()

orders_with_details = (
    fact["detail_status"]
    == "Has Order Details"
).sum()

orders_without_details = (
    fact["detail_status"]
    == "No Order Details"
).sum()

orders_with_shipments = (
    fact["has_shipment"]
).sum()

orders_without_shipments = (
    ~fact["has_shipment"]
).sum()

multiple_shipment_orders = (
    fact["shipment_count"] > 1
).sum()

missing_customer_reference = (
    fact["customer_status"]
    == "Missing Customer Reference"
).sum()

unmatched_customer_reference = (
    fact["customer_status"]
    == "Unmatched Customer Reference"
).sum()

ship_before_order = (
    fact["date_status"]
    == "Ship Date Before Order Date"
).sum()


# ==================================================
# 19. STATUS
# ==================================================

if (
    rows_after == rows_before
    and duplicate_order_id == 0
    and missing_order_id == 0
    and financial_mismatch == 0
):
    status = "PASS WITH WARNINGS"
else:
    status = "FAIL"


# ==================================================
# 20. REPORT
# ==================================================

report = f"""
FACT ORDERS - ANALYTICAL REPORT
===============================

GRAIN
-----
One row represents one order.

SOURCE TABLES
-------------
Orders
Order Details
Shipments
Customers

ROW COUNTS
----------
Orders before transformation: {rows_before}

Rows after Order Details summary join: {rows_after_details}

Rows after Shipment summary join: {rows_after_shipments}

Final fact_orders rows: {rows_after}

Expected final rows: {rows_before}


ORDER DETAIL SUMMARY
--------------------

Orders with Order Details: {orders_with_details}
Orders without Order Details: {orders_without_details}

Order detail row count:
Minimum: {fact["detail_row_count"].min()}
Maximum: {fact["detail_row_count"].max()}
Average: {fact["detail_row_count"].mean()}


FINANCIAL RECONCILIATION
------------------------

Comparable / matched: {financial_match}
Mismatches: {financial_mismatch}

Missing source order_total but detail total available:
{missing_source_total_rows}

Cannot calculate:
{cannot_calculate_rows}

Formula for calculated_order_total:

SUM(Order Details.line_total) grouped by order_id

Financial matching tolerance:

ABS(source_order_total - calculated_order_total) <= 0.01


SHIPMENT SUMMARY
----------------

Orders with shipment: {orders_with_shipments}
Orders without shipment: {orders_without_shipments}
Orders with multiple shipments: {multiple_shipment_orders}


CUSTOMER VALIDATION
-------------------

Missing customer references: {missing_customer_reference}
Unmatched customer references: {unmatched_customer_reference}


QUANTITY ANALYSIS
-----------------

Positive net quantity orders:
{(fact["total_quantity"] > 0).sum()}

Negative net quantity orders:
{(fact["total_quantity"] < 0).sum()}

Zero net quantity orders:
{(fact["total_quantity"] == 0).sum()}


DATE VALIDATION
---------------

Ship date before order date:
{ship_before_order}


PRIMARY KEY VALIDATION
----------------------

Duplicate order IDs: {duplicate_order_id}
Missing order IDs: {missing_order_id}


SOURCE VALUES PRESERVED
-----------------------

source_order_total preserves the original order_total.

No source values were overwritten.

No records were intentionally deleted.


ANALYTICAL COLUMNS
------------------

detail_row_count
total_quantity
calculated_order_total
order_total_difference
order_financial_status
shipment_count
has_shipment
detail_status
customer_status
quantity_status
date_status


FEATURE ENGINEERING
-------------------

No customer-level RFM metrics created.
No customer lifetime value created.
No product-level metrics created.
No supplier performance metrics created.
No inventory metrics created.
No shipment performance metrics created.


FINAL VALIDATION
----------------

Final rows = source rows:
{rows_after == rows_before}

Duplicate order IDs:
{duplicate_order_id}

Missing order IDs:
{missing_order_id}

Financial mismatches:
{financial_mismatch}


FINAL STATUS
------------
{status}
"""

REPORT_FILE.write_text(
    report,
    encoding="utf-8"
)


print("\nFact Orders created successfully.")
print("Rows:", rows_after)
print("Columns:", len(fact.columns))
print("Output:", OUTPUT_FILE)
print("Report:", REPORT_FILE)
print("Final status:", status)