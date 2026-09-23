from pathlib import Path
import pandas as pd


# ==================================================
# 1. PATHS
# ==================================================

BASE_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = BASE_DIR / "data" / "cleaned"

SHIPMENTS_FILE = DATA_DIR / "shipments_cleaned.csv"
ORDERS_FILE = DATA_DIR / "orders_cleaned.csv"


# ==================================================
# 2. LOAD DATA
# ==================================================

shipments = pd.read_csv(SHIPMENTS_FILE)
orders = pd.read_csv(ORDERS_FILE)

print("Shipments:", shipments.shape)
print("Orders:", orders.shape)


# ==================================================
# 3. BASIC PROFILE
# ==================================================

print("\nShipment columns:")
print(shipments.columns.tolist())

print("\nShipment missing values:")
print(shipments.isna().sum())

print("\nDuplicate shipment IDs:")
print(
    shipments["shipment_id"].duplicated().sum()
)


# ==================================================
# 4. CARRIER ANALYSIS
# ==================================================

print("\nCARRIER")
print("-------")

print(
    shipments["carrier"]
    .value_counts(dropna=False)
)


# ==================================================
# 5. SHIPPING COST
# ==================================================

shipments["shipping_cost"] = pd.to_numeric(
    shipments["shipping_cost"],
    errors="coerce"
)

print("\nSHIPPING COST")
print("-------------")

print(
    "Missing:",
    shipments["shipping_cost"].isna().sum()
)

print(
    "Zero:",
    (shipments["shipping_cost"] == 0).sum()
)

print(
    "Negative:",
    (shipments["shipping_cost"] < 0).sum()
)

print(
    "Positive:",
    (shipments["shipping_cost"] > 0).sum()
)

print(
    "Minimum:",
    shipments["shipping_cost"].min()
)

print(
    "Maximum:",
    shipments["shipping_cost"].max()
)


# ==================================================
# 6. DISTANCE
# ==================================================

shipments["distance_km"] = pd.to_numeric(
    shipments["distance_km"],
    errors="coerce"
)

print("\nDISTANCE")
print("--------")

print(
    "Missing:",
    shipments["distance_km"].isna().sum()
)

print(
    "Zero:",
    (shipments["distance_km"] == 0).sum()
)

print(
    "Negative:",
    (shipments["distance_km"] < 0).sum()
)

print(
    "Positive:",
    (shipments["distance_km"] > 0).sum()
)

print(
    "Minimum:",
    shipments["distance_km"].min()
)

print(
    "Maximum:",
    shipments["distance_km"].max()
)


# ==================================================
# 7. DATE CONVERSION
# ==================================================

shipments["shipment_date"] = pd.to_datetime(
    shipments["shipment_date"],
    errors="coerce"
)

shipments["delivery_date"] = pd.to_datetime(
    shipments["delivery_date"],
    errors="coerce"
)


# ==================================================
# 8. DATE AVAILABILITY
# ==================================================

print("\nDATE AVAILABILITY")
print("-----------------")

print(
    "Missing shipment dates:",
    shipments["shipment_date"].isna().sum()
)

print(
    "Missing delivery dates:",
    shipments["delivery_date"].isna().sum()
)


# ==================================================
# 9. DELIVERY / SHIPMENT DATE RELATIONSHIP
# ==================================================

both_dates = (
    shipments["shipment_date"].notna()
    & shipments["delivery_date"].notna()
)

delivery_before_shipment = (
    both_dates
    & (
        shipments["delivery_date"]
        < shipments["shipment_date"]
    )
)

same_day_delivery = (
    both_dates
    & (
        shipments["delivery_date"]
        == shipments["shipment_date"]
    )
)

delivery_after_shipment = (
    both_dates
    & (
        shipments["delivery_date"]
        > shipments["shipment_date"]
    )
)

print("\nDATE RELATIONSHIP")
print("-----------------")

print(
    "Both dates available:",
    both_dates.sum()
)

print(
    "Delivery before shipment:",
    delivery_before_shipment.sum()
)

print(
    "Same-day delivery:",
    same_day_delivery.sum()
)

print(
    "Delivery after shipment:",
    delivery_after_shipment.sum()
)


# ==================================================
# 10. ORDER RELATIONSHIP
# ==================================================

valid_order_ids = set(
    orders["order_id"].dropna()
)

shipment_order_exists = (
    shipments["order_id"]
    .isin(valid_order_ids)
)

print("\nORDER RELATIONSHIP")
print("------------------")

print(
    "Valid order references:",
    shipment_order_exists.sum()
)

print(
    "Unmatched order references:",
    (
        ~shipment_order_exists
    ).sum()
)


# ==================================================
# 11. MULTIPLE SHIPMENTS PER ORDER
# ==================================================

shipment_counts = (
    shipments
    .groupby("order_id")
    .size()
    .reset_index(
        name="shipment_count"
    )
)

print("\nSHIPMENT COUNT PER ORDER")
print("------------------------")

print(
    "Orders with shipments:",
    len(shipment_counts)
)

print(
    "Orders with multiple shipments:",
    (
        shipment_counts["shipment_count"] > 1
    ).sum()
)

print(
    "Maximum shipments for one order:",
    shipment_counts["shipment_count"].max()
)

print(
    "Average shipments per shipped order:",
    shipment_counts["shipment_count"].mean()
)


# ==================================================
# 12. DATE RANGE
# ==================================================

print("\nDATE RANGE")
print("----------")

print(
    "Earliest shipment date:",
    shipments["shipment_date"].min()
)

print(
    "Latest shipment date:",
    shipments["shipment_date"].max()
)

print(
    "Earliest delivery date:",
    shipments["delivery_date"].min()
)

print(
    "Latest delivery date:",
    shipments["delivery_date"].max()
)


# ==================================================
# 13. CARRIER + DATE QUALITY
# ==================================================

carrier_date_quality = pd.crosstab(
    shipments["carrier"],
    delivery_before_shipment
)

print("\nCARRIER VS DELIVERY DATE ISSUE")
print("-------------------------------")

print(carrier_date_quality)


# ==================================================
# 14. CARRIER + SHIPPING COST
# ==================================================

carrier_cost_summary = (
    shipments
    .groupby("carrier")["shipping_cost"]
    .agg(
        shipment_count="count",
        average_cost="mean",
        minimum_cost="min",
        maximum_cost="max"
    )
)

print("\nCARRIER SHIPPING COST SUMMARY")
print("-----------------------------")

print(
    carrier_cost_summary
)


# ==================================================
# 15. FINAL SUMMARY
# ==================================================

print("\nFINAL SUMMARY")
print("-------------")

print(
    "Total shipments:",
    len(shipments)
)

print(
    "Unique shipment IDs:",
    shipments["shipment_id"].nunique()
)

print(
    "Unique orders with shipments:",
    shipments["order_id"].nunique()
)

print(
    "Multiple-shipment orders:",
    (
        shipment_counts["shipment_count"] > 1
    ).sum()
)

print(
    "Missing shipping costs:",
    shipments["shipping_cost"].isna().sum()
)

print(
    "Missing distances:",
    shipments["distance_km"].isna().sum()
)

print(
    "Delivery before shipment:",
    delivery_before_shipment.sum()
)

print(
    "Unmatched orders:",
    (
        ~shipment_order_exists
    ).sum()
)

print("\nShipment analytical readiness profiling completed.")