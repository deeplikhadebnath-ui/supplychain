from pathlib import Path
import pandas as pd
import re


# --------------------------------------------------
# 1. FILE PATHS
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = BASE_DIR / "data" / "raw" / "08_shipments.csv"
OUTPUT_FILE = BASE_DIR / "data" / "cleaned" / "shipments_cleaned.csv"
REPORT_FILE = BASE_DIR / "reports" / "shipments_cleaning_report.txt"

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------
# 2. LOAD DATA
# --------------------------------------------------

df = pd.read_csv(INPUT_FILE)

rows_before = len(df)

print("Shipment shape:", df.shape)

print("\nColumns:")
print(df.columns.tolist())

print("\nData types:")
print(df.dtypes)

print("\nMissing values:")
print(df.isna().sum())

print("\nExact duplicate rows:", df.duplicated().sum())


# --------------------------------------------------
# 3. BASIC CLEANING
# --------------------------------------------------

# Remove unnecessary unnamed columns if present
df = df.loc[:, ~df.columns.str.startswith("Unnamed")]

# Remove extra spaces from text columns
for col in ["carrier"]:
    df[col] = df[col].astype("string").str.strip()


# --------------------------------------------------
# 4. shipment_id VALIDATION
# --------------------------------------------------

missing_shipment_id = df["shipment_id"].isna().sum()
duplicate_shipment_id = df["shipment_id"].duplicated().sum()

print("\nShipment ID validation:")
print("Missing shipment IDs:", missing_shipment_id)
print("Duplicate shipment IDs:", duplicate_shipment_id)


# --------------------------------------------------
# 5. order_id VALIDATION
# --------------------------------------------------

missing_order_id = df["order_id"].isna().sum()

duplicate_order_ids = df["order_id"].duplicated().sum()

print("\nOrder ID validation:")
print("Missing order IDs:", missing_order_id)
print("Repeated order IDs:", duplicate_order_ids)


# --------------------------------------------------
# 6. CARRIER CLEANING
# --------------------------------------------------

# Standardize FedEx
carrier_mapping = {
    "fedex": "FedEx",
    "FedEx": "FedEx"
}

df["carrier"] = df["carrier"].replace(carrier_mapping)

print("\nCarrier values after standardization:")
print(df["carrier"].value_counts(dropna=False))


# --------------------------------------------------
# 7. SHIPMENT DATE CLEANING
# --------------------------------------------------

shipment_date_missing_before = df["shipment_date"].isna().sum()

df["shipment_date"] = pd.to_datetime(
    df["shipment_date"],
    format="mixed",
    dayfirst=True,
    errors="coerce"
)

shipment_date_unparseable = (
    df["shipment_date"].isna().sum()
    - shipment_date_missing_before
)

# Standard format
df["shipment_date"] = df["shipment_date"].dt.strftime("%Y-%m-%d")


# --------------------------------------------------
# 8. DELIVERY DATE CLEANING
# --------------------------------------------------

delivery_date_missing_before = df["delivery_date"].isna().sum()

df["delivery_date"] = pd.to_datetime(
    df["delivery_date"],
    format="mixed",
    dayfirst=True,
    errors="coerce"
)

delivery_date_unparseable = (
    df["delivery_date"].isna().sum()
    - delivery_date_missing_before
)

# Standard format
df["delivery_date"] = df["delivery_date"].dt.strftime("%Y-%m-%d")


# --------------------------------------------------
# 9. DATE RELATIONSHIP CHECK
# --------------------------------------------------

shipment_dates = pd.to_datetime(df["shipment_date"], errors="coerce")
delivery_dates = pd.to_datetime(df["delivery_date"], errors="coerce")

reversed_dates = (
    (shipment_dates.notna()) &
    (delivery_dates.notna()) &
    (delivery_dates < shipment_dates)
).sum()

shipment_missing_delivery_present = (
    shipment_dates.isna() & delivery_dates.notna()
).sum()

shipment_present_delivery_missing = (
    shipment_dates.notna() & delivery_dates.isna()
).sum()

both_dates_missing = (
    shipment_dates.isna() & delivery_dates.isna()
).sum()

print("\nDate validation:")
print("Unparseable shipment dates:", shipment_date_unparseable)
print("Unparseable delivery dates:", delivery_date_unparseable)
print("Delivery before shipment:", reversed_dates)
print("Shipment missing + delivery present:",
      shipment_missing_delivery_present)
print("Shipment present + delivery missing:",
      shipment_present_delivery_missing)
print("Both dates missing:", both_dates_missing)


# --------------------------------------------------
# 10. SHIPPING COST VALIDATION
# --------------------------------------------------

df["shipping_cost"] = pd.to_numeric(
    df["shipping_cost"],
    errors="coerce"
)

missing_shipping_cost = df["shipping_cost"].isna().sum()
zero_shipping_cost = (df["shipping_cost"] == 0).sum()
negative_shipping_cost = (df["shipping_cost"] < 0).sum()

print("\nShipping cost:")
print("Missing:", missing_shipping_cost)
print("Zero:", zero_shipping_cost)
print("Negative:", negative_shipping_cost)


# --------------------------------------------------
# 11. DISTANCE VALIDATION
# --------------------------------------------------

df["distance_km"] = pd.to_numeric(
    df["distance_km"],
    errors="coerce"
)

missing_distance = df["distance_km"].isna().sum()
zero_distance = (df["distance_km"] == 0).sum()
negative_distance = (df["distance_km"] < 0).sum()

print("\nDistance:")
print("Missing:", missing_distance)
print("Zero:", zero_distance)
print("Negative:", negative_distance)


# --------------------------------------------------
# 12. SAVE CLEANED DATA
# --------------------------------------------------

df.to_csv(OUTPUT_FILE, index=False)

rows_after = len(df)


# --------------------------------------------------
# 13. FINAL VALIDATION
# --------------------------------------------------

final_duplicate_shipment_id = df["shipment_id"].duplicated().sum()
final_missing_shipment_id = df["shipment_id"].isna().sum()

invalid_carrier = df["carrier"].isna().sum()

final_negative_shipping_cost = (
    df["shipping_cost"] < 0
).sum()

final_negative_distance = (
    df["distance_km"] < 0
).sum()


# --------------------------------------------------
# 14. FINAL STATUS
# --------------------------------------------------

if (
    final_duplicate_shipment_id == 0
    and final_missing_shipment_id == 0
    and final_negative_shipping_cost == 0
    and final_negative_distance == 0
):
    status = "PASS WITH WARNINGS"
else:
    status = "FAIL"


# --------------------------------------------------
# 15. CLEANING REPORT
# --------------------------------------------------

report = f"""
SHIPMENT CLEANING REPORT
========================

Rows before cleaning: {rows_before}
Rows after cleaning: {rows_after}

COLUMNS
-------
{", ".join(df.columns)}

MISSING VALUES
--------------
{df.isna().sum().to_string()}

SHIPMENT ID VALIDATION
----------------------
Missing shipment IDs: {missing_shipment_id}
Duplicate shipment IDs: {duplicate_shipment_id}

ORDER ID VALIDATION
-------------------
Missing order IDs: {missing_order_id}
Repeated order ID rows: {duplicate_order_ids}

CARRIER STANDARDIZATION
-----------------------
fedex -> FedEx
FedEx -> FedEx

DHL and DHL Express were kept separate.

CARRIER VALUES
--------------
{df["carrier"].value_counts(dropna=False).to_string()}

SHIPMENT DATE
-------------
Missing shipment dates before parsing: {shipment_date_missing_before}
Unparseable shipment dates: {shipment_date_unparseable}
Format used: mixed
Standard output format: YYYY-MM-DD

DELIVERY DATE
-------------
Missing delivery dates before parsing: {delivery_date_missing_before}
Unparseable delivery dates: {delivery_date_unparseable}
Format used: mixed
Standard output format: YYYY-MM-DD

DATE RELATIONSHIP
-----------------
Delivery before shipment: {reversed_dates}
Shipment missing + delivery present: {shipment_missing_delivery_present}
Shipment present + delivery missing: {shipment_present_delivery_missing}
Both dates missing: {both_dates_missing}

Reversed dates were preserved and not automatically deleted.

SHIPPING COST
-------------
Missing shipping costs: {missing_shipping_cost}
Zero shipping costs: {zero_shipping_cost}
Negative shipping costs: {negative_shipping_cost}

DISTANCE
--------
Missing distances: {missing_distance}
Zero distances: {zero_distance}
Negative distances: {negative_distance}

DUPLICATE ANALYSIS
------------------
Complete duplicate rows: {df.duplicated().sum()}
Duplicate shipment IDs: {final_duplicate_shipment_id}
Repeated order IDs are not treated as duplicates because one order
can have multiple shipment records.

RECORD CHANGES
--------------
Records removed: 0
Missing values were not artificially filled.
Suspicious records were not automatically deleted.

FINAL VALIDATION
----------------
Final duplicate shipment IDs: {final_duplicate_shipment_id}
Final missing shipment IDs: {final_missing_shipment_id}
Final invalid negative shipping costs: {final_negative_shipping_cost}
Final invalid negative distances: {final_negative_distance}

FINAL STATUS
------------
{status}
"""

REPORT_FILE.write_text(report, encoding="utf-8")

print("\nCleaning completed successfully.")
print("Cleaned file:", OUTPUT_FILE)
print("Cleaning report:", REPORT_FILE)
print("Final status:", status)