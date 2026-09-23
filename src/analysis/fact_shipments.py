from pathlib import Path
import pandas as pd


# ==================================================
# 1. PATHS
# ==================================================

BASE_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = BASE_DIR / "data" / "cleaned"
OUTPUT_DIR = BASE_DIR / "data" / "analytical"
REPORT_DIR = BASE_DIR / "reports"

SHIPMENTS_FILE = DATA_DIR / "shipments_cleaned.csv"
ORDERS_FILE = DATA_DIR / "orders_cleaned.csv"

OUTPUT_FILE = OUTPUT_DIR / "fact_shipments.csv"
REPORT_FILE = REPORT_DIR / "fact_shipments_report.txt"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)


# ==================================================
# 2. LOAD DATA
# ==================================================

shipments = pd.read_csv(SHIPMENTS_FILE)
orders = pd.read_csv(ORDERS_FILE)

rows_before = len(shipments)

print("Shipments:", shipments.shape)
print("Orders:", orders.shape)


# ==================================================
# 3. BASIC TYPE CONVERSION
# ==================================================

shipments["shipping_cost"] = pd.to_numeric(
    shipments["shipping_cost"],
    errors="coerce"
)

shipments["distance_km"] = pd.to_numeric(
    shipments["distance_km"],
    errors="coerce"
)

shipments["shipment_date"] = pd.to_datetime(
    shipments["shipment_date"],
    errors="coerce"
)

shipments["delivery_date"] = pd.to_datetime(
    shipments["delivery_date"],
    errors="coerce"
)

orders["order_status"] = orders["order_status"].astype("string")


# ==================================================
# 4. ORDER REFERENCE VALIDATION
# ==================================================

valid_order_ids = set(
    orders["order_id"].dropna()
)

shipment_order_exists = (
    shipments["order_id"].isin(valid_order_ids)
)

matched_order_references = shipment_order_exists.sum()

missing_order_reference = (
    shipments["order_id"].isna()
).sum()

unmatched_order_reference = (
    shipments["order_id"].notna()
    & ~shipments["order_id"].isin(valid_order_ids)
).sum()

print("\nORDER REFERENCE")
print("----------------")
print(
    "Matched order references:",
    matched_order_references
)

print(
    "Missing order references:",
    missing_order_reference
)

print(
    "Unmatched order references:",
    unmatched_order_reference
)


# ==================================================
# 5. JOIN ORDERS
# ==================================================

fact = shipments.merge(
    orders[
        [
            "order_id",
            "order_status"
        ]
    ],
    on="order_id",
    how="left",
    validate="many_to_one"
)

rows_after_join = len(fact)

print(
    "\nRows after Orders join:",
    rows_after_join
)


# ==================================================
# 6. ORDER REFERENCE STATUS
# ==================================================

fact["order_reference_status"] = "Matched"

fact.loc[
    fact["order_id"].isna(),
    "order_reference_status"
] = "Missing Order Reference"

fact.loc[
    fact["order_id"].notna()
    & fact["order_status"].isna(),
    "order_reference_status"
] = "Unmatched Order Reference"


# ==================================================
# 7. SHIPMENT DATE STATUS
# ==================================================

fact["shipment_date_status"] = "Valid"

fact.loc[
    fact["shipment_date"].isna(),
    "shipment_date_status"
] = "Missing Shipment Date"


# ==================================================
# 8. DELIVERY DATE STATUS
# ==================================================

fact["delivery_date_status"] = "Valid"

fact.loc[
    fact["delivery_date"].isna(),
    "delivery_date_status"
] = "Missing Delivery Date"

both_dates = (
    fact["shipment_date"].notna()
    & fact["delivery_date"].notna()
)

delivery_before_shipment = (
    both_dates
    & (
        fact["delivery_date"]
        < fact["shipment_date"]
    )
)

same_day_delivery = (
    both_dates
    & (
        fact["delivery_date"]
        == fact["shipment_date"]
    )
)

fact.loc[
    delivery_before_shipment,
    "delivery_date_status"
] = "Delivery Before Shipment"


# ==================================================
# 9. FINAL COLUMN ORDER
# ==================================================

final_columns = [
    "shipment_id",
    "order_id",
    "carrier",
    "shipment_date",
    "delivery_date",
    "shipping_cost",
    "distance_km",
    "order_status",
    "order_reference_status",
    "shipment_date_status",
    "delivery_date_status"
]

fact = fact[final_columns]


# ==================================================
# 10. SAVE
# ==================================================

fact.to_csv(
    OUTPUT_FILE,
    index=False
)

rows_after = len(fact)


# ==================================================
# 11. FINAL VALIDATION
# ==================================================

duplicate_shipment_id = (
    fact["shipment_id"].duplicated().sum()
)

missing_shipment_id = (
    fact["shipment_id"].isna().sum()
)

missing_shipping_cost = (
    fact["shipping_cost"].isna()
).sum()

zero_shipping_cost = (
    fact["shipping_cost"] == 0
).sum()

negative_shipping_cost = (
    fact["shipping_cost"] < 0
).sum()

missing_distance = (
    fact["distance_km"].isna()
).sum()

zero_distance = (
    fact["distance_km"] == 0
).sum()

negative_distance = (
    fact["distance_km"] < 0
).sum()

missing_shipment_date = (
    fact["shipment_date"].isna()
).sum()

missing_delivery_date = (
    fact["delivery_date"].isna()
).sum()

delivery_before_count = (
    fact["delivery_date_status"]
    == "Delivery Before Shipment"
).sum()

same_day_count = (
    both_dates
    & (
        fact["delivery_date"]
        == fact["shipment_date"]
    )
).sum()

delivery_after_count = (
    both_dates
    & (
        fact["delivery_date"]
        > fact["shipment_date"]
    )
).sum()


# ==================================================
# 12. STATUS
# ==================================================

if (
    rows_after == rows_before
    and duplicate_shipment_id == 0
    and missing_shipment_id == 0
    and unmatched_order_reference == 0
    and negative_shipping_cost == 0
    and negative_distance == 0
):
    status = "PASS WITH WARNINGS"
else:
    status = "FAIL"


# ==================================================
# 13. REPORT
# ==================================================

report = f"""
FACT SHIPMENTS - ANALYTICAL REPORT
==================================

GRAIN
-----
One row represents one shipment.

SOURCE TABLES
-------------
Shipments
Orders

ROW COUNTS
----------
Shipments before transformation: {rows_before}
Rows after Orders join: {rows_after_join}
Final fact_shipments rows: {rows_after}
Expected final rows: {rows_before}


SHIPMENT ID VALIDATION
----------------------

Missing shipment IDs: {missing_shipment_id}
Duplicate shipment IDs: {duplicate_shipment_id}


ORDER REFERENCE VALIDATION
--------------------------

Matched order references: {matched_order_references}
Missing order references: {missing_order_reference}
Unmatched order references: {unmatched_order_reference}


CARRIER
-------

Carrier values:

{fact["carrier"].value_counts(dropna=False).to_string()}

DHL and DHL Express were kept separate.


SHIPMENT DATE
-------------

Missing shipment dates: {missing_shipment_date}

Shipment date status:

{fact["shipment_date_status"].value_counts(dropna=False).to_string()}


DELIVERY DATE
-------------

Missing delivery dates: {missing_delivery_date}

Delivery date status:

{fact["delivery_date_status"].value_counts(dropna=False).to_string()}


DATE RELATIONSHIP
-----------------

Delivery before shipment: {delivery_before_count}
Same-day delivery: {same_day_count}
Delivery after shipment: {delivery_after_count}

Delivery-before-shipment records were preserved and flagged.


SHIPPING COST
-------------

Missing: {missing_shipping_cost}
Zero: {zero_shipping_cost}
Negative: {negative_shipping_cost}
Positive: {(fact["shipping_cost"] > 0).sum()}

Minimum: {fact["shipping_cost"].min()}
Maximum: {fact["shipping_cost"].max()}


DISTANCE
--------

Missing: {missing_distance}
Zero: {zero_distance}
Negative: {negative_distance}
Positive: {(fact["distance_km"] > 0).sum()}

Minimum: {fact["distance_km"].min()}
Maximum: {fact["distance_km"].max()}


JOIN VALIDATION
---------------

Rows before Orders join: {rows_before}
Rows after Orders join: {rows_after_join}
Row multiplication: {rows_after_join - rows_before}

Expected:
    {rows_before} -> {rows_before}


ANALYTICAL COLUMNS
------------------

shipment_id
order_id
carrier
shipment_date
delivery_date
shipping_cost
distance_km
order_status
order_reference_status
shipment_date_status
delivery_date_status


SOURCE VALUES PRESERVED
-----------------------

No source shipment values were overwritten.
No missing shipping costs were invented.
No missing distances were invented.
No shipment records were intentionally deleted.


FEATURE ENGINEERING
-------------------

No delivery_days created.
No shipping_cost_per_km created.
No carrier performance score created.
No logistics risk score created.
No shipping efficiency score created.
No on-time delivery flag created.


FINAL VALIDATION
----------------

Final rows = source rows:
{rows_after == rows_before}

Final duplicate shipment IDs:
{duplicate_shipment_id}

Final missing shipment IDs:
{missing_shipment_id}

Final unmatched order references:
{unmatched_order_reference}

Final negative shipping costs:
{negative_shipping_cost}

Final negative distances:
{negative_distance}


FINAL STATUS
------------
{status}
"""

REPORT_FILE.write_text(
    report,
    encoding="utf-8"
)


print("\nFact Shipments created successfully.")
print("Rows:", rows_after)
print("Columns:", len(fact.columns))
print("Output:", OUTPUT_FILE)
print("Report:", REPORT_FILE)
print("Final status:", status)