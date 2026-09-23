from pathlib import Path
import pandas as pd


# --------------------------------------------------
# 1. PATHS
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = BASE_DIR / "data" / "cleaned"

ORDER_DETAILS_FILE = DATA_DIR / "order_details_cleaned.csv"
PRODUCTS_FILE = DATA_DIR / "products_cleaned.csv"
ORDERS_FILE = DATA_DIR / "orders_cleaned.csv"

# --------------------------------------------------
# 2. LOAD DATA
# --------------------------------------------------

order_details = pd.read_csv(ORDER_DETAILS_FILE)
products = pd.read_csv(PRODUCTS_FILE)
orders = pd.read_csv(ORDERS_FILE)

print("Order Details:", order_details.shape)
print("Products:", products.shape)
print("Orders:", orders.shape)


# --------------------------------------------------
# 3. JOIN PRODUCT PRICE
# --------------------------------------------------

order_items = order_details.merge(
    products[
        [
            "product_id",
            "product_name",
            "category",
            "supplier_id",
            "unit_price",
            "is_active"
        ]
    ],
    on="product_id",
    how="left"
)


# --------------------------------------------------
# 4. JOIN ORDER INFORMATION
# --------------------------------------------------

order_items = order_items.merge(
    orders[
        [
            "order_id",
            "customer_id",
            "warehouse_id",
            "order_date",
            "order_status",
            "order_total"
        ]
    ],
    on="order_id",
    how="left"
)


print("\nFinal profiling rows:", len(order_items))


# --------------------------------------------------
# 5. BASIC MISSING VALUE ANALYSIS
# --------------------------------------------------

print("\nMissing values:")
print(
    order_items[
        [
            "order_id",
            "product_id",
            "customer_id",
            "warehouse_id",
            "quantity",
            "discount_pct",
            "unit_price",
            "line_total",
            "order_status"
        ]
    ].isna().sum()
)


# --------------------------------------------------
# 6. ANALYTICAL CALCULATION READINESS
# --------------------------------------------------

complete_calculation = (
    order_items["unit_price"].notna()
    & order_items["quantity"].notna()
    & order_items["discount_pct"].notna()
)

missing_price = order_items["unit_price"].isna()

missing_discount = order_items["discount_pct"].isna()

missing_line_total = order_items["line_total"].isna()

negative_quantity = order_items["quantity"] < 0

unmatched_order = order_items["order_id"].isna()


print("\nANALYTICAL READINESS")
print("--------------------")

print(
    "Complete price + quantity + discount:",
    complete_calculation.sum()
)

print(
    "Missing product price:",
    missing_price.sum()
)

print(
    "Missing discount:",
    missing_discount.sum()
)

print(
    "Missing line total:",
    missing_line_total.sum()
)

print(
    "Negative quantity:",
    negative_quantity.sum()
)

print(
    "Unmatched order:",
    unmatched_order.sum()
)


# --------------------------------------------------
# 7. LINE TOTAL RECONCILIATION
# --------------------------------------------------

order_items["calculated_line_total"] = (
    order_items["unit_price"]
    * order_items["quantity"]
    * (
        1 - order_items["discount_pct"] / 100
    )
)

can_compare = (
    order_items["calculated_line_total"].notna()
    & order_items["line_total"].notna()
)

difference = (
    order_items["line_total"]
    - order_items["calculated_line_total"]
).abs()

matches = can_compare & (difference <= 0.01)

mismatches = can_compare & (difference > 0.01)


print("\nLINE TOTAL RECONCILIATION")
print("-------------------------")

print("Rows that can be compared:", can_compare.sum())
print("Matches within 0.01:", matches.sum())
print("Mismatches:", mismatches.sum())


# --------------------------------------------------
# 8. MISSING LINE TOTAL CASES
# --------------------------------------------------

missing_line_total_cases = {
    "price + discount available":
        (
            order_items["line_total"].isna()
            & order_items["unit_price"].notna()
            & order_items["discount_pct"].notna()
        ).sum(),

    "price available + discount missing":
        (
            order_items["line_total"].isna()
            & order_items["unit_price"].notna()
            & order_items["discount_pct"].isna()
        ).sum(),

    "price missing + discount available":
        (
            order_items["line_total"].isna()
            & order_items["unit_price"].isna()
            & order_items["discount_pct"].notna()
        ).sum(),

    "price + discount missing":
        (
            order_items["line_total"].isna()
            & order_items["unit_price"].isna()
            & order_items["discount_pct"].isna()
        ).sum()
}


print("\nMISSING LINE TOTAL CASES")
print("------------------------")

for case, count in missing_line_total_cases.items():
    print(case + ":", count)


# --------------------------------------------------
# 9. TRANSACTION DIRECTION
# --------------------------------------------------

print("\nTRANSACTION DIRECTION")
print("---------------------")

print(
    "Positive quantity:",
    (order_items["quantity"] > 0).sum()
)

print(
    "Negative quantity:",
    (order_items["quantity"] < 0).sum()
)

print(
    "Zero quantity:",
    (order_items["quantity"] == 0).sum()
)


# --------------------------------------------------
# 10. ORDER STATUS DISTRIBUTION
# --------------------------------------------------

print("\nORDER STATUS")
print("------------")

print(
    order_items["order_status"]
    .value_counts(dropna=False)
)


# --------------------------------------------------
# 11. FINAL READINESS SUMMARY
# --------------------------------------------------

print("\nFINAL SUMMARY")
print("-------------")

print("Total order-item rows:", len(order_items))
print(
    "Rows with enough data for line calculation:",
    complete_calculation.sum()
)
print(
    "Rows with missing price:",
    missing_price.sum()
)
print(
    "Rows with missing discount:",
    missing_discount.sum()
)
print(
    "Rows with missing line total:",
    missing_line_total.sum()
)
print(
    "Negative transaction rows:",
    negative_quantity.sum()
)
print(
    "Unmatched order rows:",
    unmatched_order.sum()
)

print("\nProfiling completed successfully.")