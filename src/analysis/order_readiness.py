from pathlib import Path
import pandas as pd


# ==================================================
# 1. PATHS
# ==================================================

BASE_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = BASE_DIR / "data" / "cleaned"

ORDERS_FILE = DATA_DIR / "orders_cleaned.csv"
ORDER_DETAILS_FILE = DATA_DIR / "order_details_cleaned.csv"
SHIPMENTS_FILE = DATA_DIR / "shipments_cleaned.csv"
CUSTOMERS_FILE = DATA_DIR / "customers_cleaned.csv"


# ==================================================
# 2. LOAD DATA
# ==================================================

orders = pd.read_csv(ORDERS_FILE)
order_details = pd.read_csv(ORDER_DETAILS_FILE)
shipments = pd.read_csv(SHIPMENTS_FILE)
customers = pd.read_csv(CUSTOMERS_FILE)

print("Orders:", orders.shape)
print("Order Details:", order_details.shape)
print("Shipments:", shipments.shape)
print("Customers:", customers.shape)


# ==================================================
# 3. BASIC ORDER PROFILE
# ==================================================

print("\nOrders columns:")
print(orders.columns.tolist())

print("\nOrders missing values:")
print(orders.isna().sum())

print("\nDuplicate order IDs:")
print(orders["order_id"].duplicated().sum())


# ==================================================
# 4. ORDER STATUS
# ==================================================

print("\nORDER STATUS")
print("------------")

print(
    orders["order_status"]
    .value_counts(dropna=False)
)


# ==================================================
# 5. ORDER TOTAL PROFILE
# ==================================================

orders["order_total"] = pd.to_numeric(
    orders["order_total"],
    errors="coerce"
)

print("\nORDER TOTAL")
print("-----------")

print(
    "Missing:",
    orders["order_total"].isna().sum()
)

print(
    "Zero:",
    (orders["order_total"] == 0).sum()
)

print(
    "Negative:",
    (orders["order_total"] < 0).sum()
)

print(
    "Positive:",
    (orders["order_total"] > 0).sum()
)


# ==================================================
# 6. AGGREGATE ORDER DETAILS
# ==================================================

order_details["quantity"] = pd.to_numeric(
    order_details["quantity"],
    errors="coerce"
)

order_details["line_total"] = pd.to_numeric(
    order_details["line_total"],
    errors="coerce"
)

detail_summary = (
    order_details
    .groupby("order_id")
    .agg(
        detail_row_count=("order_detail_id", "count"),
        total_quantity=("quantity", "sum"),
        total_line_amount=("line_total", "sum")
    )
    .reset_index()
)


# ==================================================
# 7. JOIN ORDER SUMMARY
# ==================================================

order_profile = orders.merge(
    detail_summary,
    on="order_id",
    how="left"
)

print("\nOrders with order details:")
print(
    order_profile["detail_row_count"]
    .notna()
    .sum()
)

print(
    "Orders without order details:",
    order_profile["detail_row_count"]
    .isna()
    .sum()
)


# ==================================================
# 8. ORDER-LEVEL FINANCIAL COMPARISON
# ==================================================

comparable = (
    order_profile["order_total"].notna()
    & order_profile["total_line_amount"].notna()
)

difference = (
    order_profile["order_total"]
    - order_profile["total_line_amount"]
).abs()

matches = comparable & (difference <= 0.01)

mismatches = comparable & (difference > 0.01)


print("\nORDER FINANCIAL RECONCILIATION")
print("------------------------------")

print(
    "Comparable orders:",
    comparable.sum()
)

print(
    "Matches within 0.01:",
    matches.sum()
)

print(
    "Mismatches:",
    mismatches.sum()
)


# ==================================================
# 9. ORDER TOTAL CALCULATION READINESS
# ==================================================

can_calculate_order_total = (
    order_profile["total_line_amount"].notna()
)

missing_source_total = (
    order_profile["order_total"].isna()
    & can_calculate_order_total
)

cannot_calculate = (
    order_profile["order_total"].isna()
    & order_profile["total_line_amount"].isna()
)


print("\nORDER TOTAL READINESS")
print("--------------------")

print(
    "Orders with detail-based calculated total:",
    can_calculate_order_total.sum()
)

print(
    "Missing source total but detail total available:",
    missing_source_total.sum()
)

print(
    "Missing source total and no detail total:",
    cannot_calculate.sum()
)


# ==================================================
# 10. ORDER ITEM COUNTS
# ==================================================

print("\nORDER ITEM COUNTS")
print("-----------------")

print(
    "Minimum detail rows per order:",
    order_profile["detail_row_count"].min()
)

print(
    "Maximum detail rows per order:",
    order_profile["detail_row_count"].max()
)

print(
    "Average detail rows per order:",
    order_profile["detail_row_count"].mean()
)


# ==================================================
# 11. QUANTITY ANALYSIS
# ==================================================

print("\nORDER QUANTITY")
print("--------------")

print(
    "Positive net quantity orders:",
    (
        order_profile["total_quantity"] > 0
    ).sum()
)

print(
    "Negative net quantity orders:",
    (
        order_profile["total_quantity"] < 0
    ).sum()
)

print(
    "Zero net quantity orders:",
    (
        order_profile["total_quantity"] == 0
    ).sum()
)


# ==================================================
# 12. SHIPMENT COVERAGE
# ==================================================

shipment_order_ids = set(
    shipments["order_id"].dropna()
)

order_profile["has_shipment"] = (
    order_profile["order_id"]
    .isin(shipment_order_ids)
)

print("\nSHIPMENT COVERAGE")
print("-----------------")

print(
    "Orders with shipment:",
    order_profile["has_shipment"].sum()
)

print(
    "Orders without shipment:",
    (
        ~order_profile["has_shipment"]
    ).sum()
)


# ==================================================
# 13. SHIPMENT COUNT PER ORDER
# ==================================================

shipment_count = (
    shipments
    .groupby("order_id")
    .size()
    .reset_index(name="shipment_count")
)

order_profile = order_profile.merge(
    shipment_count,
    on="order_id",
    how="left"
)

order_profile["shipment_count"] = (
    order_profile["shipment_count"]
    .fillna(0)
)

print(
    "Orders with multiple shipments:",
    (
        order_profile["shipment_count"] > 1
    ).sum()
)


# ==================================================
# 14. CUSTOMER RELATIONSHIP
# ==================================================

customer_ids = set(
    customers["customer_id"].dropna()
)

order_profile["customer_exists"] = (
    order_profile["customer_id"]
    .isin(customer_ids)
)

print("\nCUSTOMER RELATIONSHIP")
print("---------------------")

print(
    "Orders with valid customer:",
    order_profile["customer_exists"].sum()
)

print(
    "Orders with missing/unmatched customer:",
    (
        ~order_profile["customer_exists"]
    ).sum()
)


# ==================================================
# 15. DATE ANALYSIS
# ==================================================

orders["order_date"] = pd.to_datetime(
    orders["order_date"],
    errors="coerce"
)

orders["ship_date"] = pd.to_datetime(
    orders["ship_date"],
    errors="coerce"
)

order_profile["order_date"] = pd.to_datetime(
    order_profile["order_date"],
    errors="coerce"
)

order_profile["ship_date"] = pd.to_datetime(
    order_profile["ship_date"],
    errors="coerce"
)

ship_before_order = (
    order_profile["order_date"].notna()
    & order_profile["ship_date"].notna()
    & (
        order_profile["ship_date"]
        < order_profile["order_date"]
    )
)

print("\nORDER DATE")
print("----------")

print(
    "Missing order dates:",
    order_profile["order_date"].isna().sum()
)

print(
    "Missing ship dates:",
    order_profile["ship_date"].isna().sum()
)

print(
    "Ship date before order date:",
    ship_before_order.sum()
)


# ==================================================
# 16. STATUS + FINANCIAL PROFILE
# ==================================================

status_financial = pd.crosstab(
    order_profile["order_status"],
    order_profile["order_total"].isna()
)

print("\nSTATUS VS MISSING ORDER TOTAL")
print("-----------------------------")

print(status_financial)


# ==================================================
# 17. FINAL SUMMARY
# ==================================================

print("\nFINAL SUMMARY")
print("-------------")

print(
    "Total orders:",
    len(order_profile)
)

print(
    "Orders with details:",
    (
        order_profile["detail_row_count"]
        .notna()
    ).sum()
)

print(
    "Orders without details:",
    (
        order_profile["detail_row_count"]
        .isna()
    ).sum()
)

print(
    "Orders with shipments:",
    order_profile["has_shipment"].sum()
)

print(
    "Orders without shipments:",
    (
        ~order_profile["has_shipment"]
    ).sum()
)

print(
    "Financial mismatches:",
    mismatches.sum()
)

print(
    "Ship dates before order dates:",
    ship_before_order.sum()
)

print("\nOrder analytical readiness profiling completed.")