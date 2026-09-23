from pathlib import Path
import pandas as pd


# --------------------------------------------------
# 1. FILE PATHS
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = BASE_DIR / "data" / "raw" / "07_inventory.csv"
OUTPUT_FILE = BASE_DIR / "data" / "cleaned" / "inventory_cleaned.csv"
REPORT_FILE = BASE_DIR / "reports" / "inventory_cleaning_report.txt"

WAREHOUSE_FILE = BASE_DIR / "data" / "cleaned" / "warehouses_cleaned.csv"
PRODUCT_FILE = BASE_DIR / "data" / "cleaned" / "products_cleaned.csv"

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------
# 2. LOAD DATA
# --------------------------------------------------

df = pd.read_csv(INPUT_FILE)

rows_before = len(df)

print("Inventory shape:", df.shape)

print("\nColumns:")
print(df.columns.tolist())

print("\nData types:")
print(df.dtypes)

print("\nMissing values:")
print(df.isna().sum())

print("\nExact duplicate rows:", df.duplicated().sum())


# --------------------------------------------------
# 3. INVENTORY ID VALIDATION
# --------------------------------------------------

missing_inventory_id = df["inventory_id"].isna().sum()
duplicate_inventory_id = df["inventory_id"].duplicated().sum()

print("\nInventory ID validation:")
print("Missing inventory IDs:", missing_inventory_id)
print("Duplicate inventory IDs:", duplicate_inventory_id)


# --------------------------------------------------
# 4. WAREHOUSE ID VALIDATION
# --------------------------------------------------

missing_warehouse_id = df["warehouse_id"].isna().sum()

warehouses = pd.read_csv(WAREHOUSE_FILE)
valid_warehouse_ids = set(warehouses["warehouse_id"].dropna())

unmatched_warehouse_ids = df.loc[
    ~df["warehouse_id"].isin(valid_warehouse_ids),
    "warehouse_id"
].drop_duplicates()

print("\nWarehouse ID validation:")
print("Missing warehouse IDs:", missing_warehouse_id)
print("Unmatched warehouse IDs:", len(unmatched_warehouse_ids))

if len(unmatched_warehouse_ids) > 0:
    print(unmatched_warehouse_ids.tolist())


# --------------------------------------------------
# 5. PRODUCT ID VALIDATION
# --------------------------------------------------

missing_product_id = df["product_id"].isna().sum()

products = pd.read_csv(PRODUCT_FILE)
valid_product_ids = set(products["product_id"].dropna())

unmatched_product_ids = df.loc[
    ~df["product_id"].isin(valid_product_ids),
    "product_id"
].drop_duplicates()

print("\nProduct ID validation:")
print("Missing product IDs:", missing_product_id)
print("Unmatched product IDs:", len(unmatched_product_ids))

if len(unmatched_product_ids) > 0:
    print(unmatched_product_ids.tolist())


# --------------------------------------------------
# 6. WAREHOUSE + PRODUCT DUPLICATES
# --------------------------------------------------

business_key = ["warehouse_id", "product_id"]

duplicate_business_key = df.duplicated(
    subset=business_key,
    keep=False
)

duplicate_business_rows = df.loc[
    duplicate_business_key
].sort_values(business_key)

duplicate_business_groups = (
    duplicate_business_rows
    .groupby(business_key)
    .ngroups
)

print("\nWarehouse/Product duplicate analysis:")
print("Duplicate groups:", duplicate_business_groups)
print("Rows involved:", len(duplicate_business_rows))

if len(duplicate_business_rows) > 0:
    print("\nDuplicate warehouse/product combinations:")
    print(
        duplicate_business_rows[
            [
                "warehouse_id",
                "product_id",
                "inventory_id",
                "stock_quantity",
                "reorder_level",
                "last_restock_date"
            ]
        ].to_string(index=False)
    )


# --------------------------------------------------
# 7. STOCK QUANTITY VALIDATION
# --------------------------------------------------

df["stock_quantity"] = pd.to_numeric(
    df["stock_quantity"],
    errors="coerce"
)

missing_stock = df["stock_quantity"].isna().sum()
negative_stock = (df["stock_quantity"] < 0).sum()
zero_stock = (df["stock_quantity"] == 0).sum()

print("\nStock quantity:")
print("Missing:", missing_stock)
print("Negative:", negative_stock)
print("Zero:", zero_stock)

if df["stock_quantity"].notna().any():
    print(
        "Range:",
        df["stock_quantity"].min(),
        "to",
        df["stock_quantity"].max()
    )


# --------------------------------------------------
# 8. REORDER LEVEL VALIDATION
# --------------------------------------------------

df["reorder_level"] = pd.to_numeric(
    df["reorder_level"],
    errors="coerce"
)

missing_reorder = df["reorder_level"].isna().sum()
negative_reorder = (df["reorder_level"] < 0).sum()
zero_reorder = (df["reorder_level"] == 0).sum()

print("\nReorder level:")
print("Missing:", missing_reorder)
print("Negative:", negative_reorder)
print("Zero:", zero_reorder)

if df["reorder_level"].notna().any():
    print(
        "Range:",
        df["reorder_level"].min(),
        "to",
        df["reorder_level"].max()
    )


# --------------------------------------------------
# 9. LAST RESTOCK DATE
# --------------------------------------------------

missing_restock_before = df["last_restock_date"].isna().sum()

df["last_restock_date"] = pd.to_datetime(
    df["last_restock_date"],
    format="mixed",
    dayfirst=True,
    errors="coerce"
)

unparseable_restock_dates = (
    df["last_restock_date"].isna().sum()
    - missing_restock_before
)

future_restock_dates = (
    df["last_restock_date"] >
    pd.Timestamp.today().normalize()
).sum()

# Standard final format
df["last_restock_date"] = (
    df["last_restock_date"]
    .dt.strftime("%Y-%m-%d")
)

print("\nLast restock date:")
print("Missing before parsing:", missing_restock_before)
print("Unparseable dates:", unparseable_restock_dates)
print("Future dates:", future_restock_dates)


# --------------------------------------------------
# 10. SAVE CLEANED DATA
# --------------------------------------------------

df.to_csv(OUTPUT_FILE, index=False)

rows_after = len(df)


# --------------------------------------------------
# 11. FINAL VALIDATION
# --------------------------------------------------

final_duplicate_inventory_id = df["inventory_id"].duplicated().sum()
final_missing_inventory_id = df["inventory_id"].isna().sum()

final_negative_stock = (
    df["stock_quantity"] < 0
).sum()

final_negative_reorder = (
    df["reorder_level"] < 0
).sum()

final_unmatched_warehouse = (
    ~df["warehouse_id"].isin(valid_warehouse_ids)
).sum()

final_unmatched_product = (
    ~df["product_id"].isin(valid_product_ids)
).sum()


# --------------------------------------------------
# 12. FINAL STATUS
# --------------------------------------------------

if (
    final_duplicate_inventory_id == 0
    and final_missing_inventory_id == 0
    and final_negative_stock == 0
    and final_negative_reorder == 0
    and final_unmatched_warehouse == 0
    and final_unmatched_product == 0
    and unparseable_restock_dates == 0
):
    status = "PASS WITH WARNINGS"
else:
    status = "FAIL"


# --------------------------------------------------
# 13. REPORT
# --------------------------------------------------

report = f"""
INVENTORY CLEANING REPORT
=========================

Dataset: 07_inventory.csv

Rows before cleaning: {rows_before}
Rows after cleaning: {rows_after}

COLUMNS
-------
{", ".join(df.columns)}

MISSING VALUES
--------------
{df.isna().sum().to_string()}

DUPLICATE ANALYSIS
------------------
Exact duplicate rows: {df.duplicated().sum()}
Duplicate inventory IDs: {final_duplicate_inventory_id}
Duplicate warehouse/product groups: {duplicate_business_groups}
Rows involved in warehouse/product duplicates: {len(duplicate_business_rows)}

WAREHOUSE FOREIGN KEY VALIDATION
--------------------------------
Missing warehouse IDs: {missing_warehouse_id}
Unmatched warehouse IDs: {len(unmatched_warehouse_ids)}

PRODUCT FOREIGN KEY VALIDATION
------------------------------
Missing product IDs: {missing_product_id}
Unmatched product IDs: {len(unmatched_product_ids)}

STOCK QUANTITY VALIDATION
-------------------------
Missing stock values: {missing_stock}
Negative stock values: {negative_stock}
Zero stock values: {zero_stock}
Minimum stock: {df["stock_quantity"].min()}
Maximum stock: {df["stock_quantity"].max()}

REORDER LEVEL VALIDATION
------------------------
Missing reorder levels: {missing_reorder}
Negative reorder levels: {negative_reorder}
Zero reorder levels: {zero_reorder}
Minimum reorder level: {df["reorder_level"].min()}
Maximum reorder level: {df["reorder_level"].max()}

LAST RESTOCK DATE
-----------------
Missing dates before parsing: {missing_restock_before}
Unparseable dates: {unparseable_restock_dates}
Future dates: {future_restock_dates}

Date parsing method:
pd.to_datetime(format="mixed", dayfirst=True, errors="coerce")

Final date format:
YYYY-MM-DD

WAREHOUSE/PRODUCT DUPLICATES
----------------------------
Duplicate warehouse/product groups found:
{duplicate_business_groups}

These records were preserved.
No duplicate warehouse/product records were automatically deleted.

RECORD CHANGES
--------------
Records removed: 0
Missing stock values were not filled.
Missing reorder levels were not filled.
Missing dates were not invented.
Suspicious records were preserved.

RECORDS FLAGGED
---------------
Warehouse/product duplicate groups: {duplicate_business_groups}
Future restock dates: {future_restock_dates}
Unmatched warehouse IDs: {len(unmatched_warehouse_ids)}
Unmatched product IDs: {len(unmatched_product_ids)}

FINAL VALIDATION
----------------
Final duplicate inventory IDs: {final_duplicate_inventory_id}
Final missing inventory IDs: {final_missing_inventory_id}
Final unmatched warehouse references: {final_unmatched_warehouse}
Final unmatched product references: {final_unmatched_product}
Final negative stock values: {final_negative_stock}
Final negative reorder levels: {final_negative_reorder}
Unparseable restock dates: {unparseable_restock_dates}

FINAL STATUS
------------
{status}
"""

REPORT_FILE.write_text(report, encoding="utf-8")

print("\nCleaning completed successfully.")
print("Cleaned file:", OUTPUT_FILE)
print("Cleaning report:", REPORT_FILE)
print("Final status:", status)