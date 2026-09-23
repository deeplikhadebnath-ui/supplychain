from pathlib import Path
import pandas as pd


# ==================================================
# 1. PATHS
# ==================================================

BASE_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = BASE_DIR / "data" / "cleaned"
OUTPUT_DIR = BASE_DIR / "data" / "analytical"
REPORT_DIR = BASE_DIR / "reports"

INVENTORY_FILE = DATA_DIR / "inventory_cleaned.csv"
PRODUCTS_FILE = DATA_DIR / "products_cleaned.csv"
WAREHOUSES_FILE = DATA_DIR / "warehouses_cleaned.csv"

OUTPUT_FILE = OUTPUT_DIR / "fact_inventory.csv"
REPORT_FILE = REPORT_DIR / "fact_inventory_report.txt"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)


# ==================================================
# 2. LOAD DATA
# ==================================================

inventory = pd.read_csv(INVENTORY_FILE)
products = pd.read_csv(PRODUCTS_FILE)
warehouses = pd.read_csv(WAREHOUSES_FILE)

rows_before = len(inventory)

print("Inventory:", inventory.shape)
print("Products:", products.shape)
print("Warehouses:", warehouses.shape)


# ==================================================
# 3. BASIC TYPE CONVERSION
# ==================================================

inventory["stock_quantity"] = pd.to_numeric(
    inventory["stock_quantity"],
    errors="coerce"
)

inventory["reorder_level"] = pd.to_numeric(
    inventory["reorder_level"],
    errors="coerce"
)

inventory["last_restock_date"] = pd.to_datetime(
    inventory["last_restock_date"],
    errors="coerce"
)


# ==================================================
# 4. VALID MASTER KEYS
# ==================================================

valid_product_ids = set(
    products["product_id"].dropna()
)

valid_warehouse_ids = set(
    warehouses["warehouse_id"].dropna()
)


# ==================================================
# 5. JOIN PRODUCTS
# ==================================================

product_columns = [
    "product_id",
    "product_name",
    "category",
    "unit_price",
    "is_active"
]

fact = inventory.merge(
    products[product_columns],
    on="product_id",
    how="left",
    validate="many_to_one"
)

rows_after_product_join = len(fact)

print(
    "\nRows after Product join:",
    rows_after_product_join
)


# ==================================================
# 6. JOIN WAREHOUSES
# ==================================================

warehouse_columns = [
    "warehouse_id",
    "warehouse_name",
    "location",
    "capacity_units"
]

fact = fact.merge(
    warehouses[warehouse_columns],
    on="warehouse_id",
    how="left",
    validate="many_to_one"
)

rows_after_warehouse_join = len(fact)

print(
    "Rows after Warehouse join:",
    rows_after_warehouse_join
)


# ==================================================
# 7. INVENTORY KEY STATUS
# ==================================================

fact["inventory_key_status"] = "Valid"

fact.loc[
    fact["warehouse_id"].isna(),
    "inventory_key_status"
] = "Missing Warehouse Reference"

fact.loc[
    fact["warehouse_id"].notna()
    & ~fact["warehouse_id"].isin(valid_warehouse_ids),
    "inventory_key_status"
] = "Unmatched Warehouse Reference"

fact.loc[
    fact["product_id"].isna(),
    "inventory_key_status"
] = "Missing Product Reference"

fact.loc[
    fact["product_id"].notna()
    & ~fact["product_id"].isin(valid_product_ids),
    "inventory_key_status"
] = "Unmatched Product Reference"


# ==================================================
# 8. STOCK STATUS
# ==================================================

fact["stock_status"] = "Cannot Determine"

both_stock_values = (
    fact["stock_quantity"].notna()
    & fact["reorder_level"].notna()
)

fact.loc[
    both_stock_values
    & (
        fact["stock_quantity"]
        < fact["reorder_level"]
    ),
    "stock_status"
] = "Below Reorder Level"

fact.loc[
    both_stock_values
    & (
        fact["stock_quantity"]
        == fact["reorder_level"]
    ),
    "stock_status"
] = "At Reorder Level"

fact.loc[
    both_stock_values
    & (
        fact["stock_quantity"]
        > fact["reorder_level"]
    ),
    "stock_status"
] = "Above Reorder Level"


# ==================================================
# 9. RESTOCK DATE STATUS
# ==================================================

fact["restock_date_status"] = "Valid"

fact.loc[
    fact["last_restock_date"].isna(),
    "restock_date_status"
] = "Missing Restock Date"

future_restock = (
    fact["last_restock_date"]
    > pd.Timestamp.today().normalize()
)

fact.loc[
    future_restock,
    "restock_date_status"
] = "Future Restock Date"


# ==================================================
# 10. DUPLICATE BUSINESS KEY STATUS
# ==================================================

duplicate_business_key = fact.duplicated(
    subset=["warehouse_id", "product_id"],
    keep=False
)

fact["business_key_status"] = "Unique"

fact.loc[
    duplicate_business_key,
    "business_key_status"
] = "Duplicate Warehouse/Product"


# ==================================================
# 11. FINAL COLUMN ORDER
# ==================================================

final_columns = [
    "inventory_id",
    "warehouse_id",
    "product_id",

    "warehouse_name",
    "location",
    "capacity_units",

    "product_name",
    "category",
    "unit_price",
    "is_active",

    "stock_quantity",
    "reorder_level",
    "last_restock_date",

    "stock_status",
    "restock_date_status",
    "business_key_status",
    "inventory_key_status"
]

fact = fact[final_columns]


# ==================================================
# 12. SAVE
# ==================================================

fact.to_csv(
    OUTPUT_FILE,
    index=False
)

rows_after = len(fact)


# ==================================================
# 13. FINAL VALIDATION
# ==================================================

duplicate_inventory_id = (
    fact["inventory_id"].duplicated().sum()
)

missing_inventory_id = (
    fact["inventory_id"].isna().sum()
)

unmatched_warehouse_reference = (
    fact["inventory_key_status"]
    == "Unmatched Warehouse Reference"
).sum()

unmatched_product_reference = (
    fact["inventory_key_status"]
    == "Unmatched Product Reference"
).sum()

missing_stock = (
    fact["stock_quantity"].isna()
).sum()

zero_stock = (
    fact["stock_quantity"] == 0
).sum()

negative_stock = (
    fact["stock_quantity"] < 0
).sum()

missing_reorder = (
    fact["reorder_level"].isna()
).sum()

zero_reorder = (
    fact["reorder_level"] == 0
).sum()

negative_reorder = (
    fact["reorder_level"] < 0
).sum()

below_reorder = (
    fact["stock_status"]
    == "Below Reorder Level"
).sum()

at_reorder = (
    fact["stock_status"]
    == "At Reorder Level"
).sum()

above_reorder = (
    fact["stock_status"]
    == "Above Reorder Level"
).sum()

cannot_determine_stock = (
    fact["stock_status"]
    == "Cannot Determine"
).sum()

future_restock_count = (
    fact["restock_date_status"]
    == "Future Restock Date"
).sum()

duplicate_business_rows = (
    fact["business_key_status"]
    == "Duplicate Warehouse/Product"
).sum()

duplicate_business_groups = (
    fact.loc[
        duplicate_business_key,
        ["warehouse_id", "product_id"]
    ]
    .drop_duplicates()
    .shape[0]
)


# ==================================================
# 14. STATUS
# ==================================================

if (
    rows_after == rows_before
    and duplicate_inventory_id == 0
    and missing_inventory_id == 0
    and unmatched_warehouse_reference == 0
    and unmatched_product_reference == 0
    and negative_stock == 0
    and negative_reorder == 0
):
    status = "PASS WITH WARNINGS"
else:
    status = "FAIL"


# ==================================================
# 15. REPORT
# ==================================================

report = f"""
FACT INVENTORY - ANALYTICAL REPORT
===================================

GRAIN
-----
One row represents one inventory record.

SOURCE TABLES
-------------
Inventory
Products
Warehouses

ROW COUNTS
----------
Inventory before transformation: {rows_before}

Rows after Product join: {rows_after_product_join}

Rows after Warehouse join: {rows_after_warehouse_join}

Final fact_inventory rows: {rows_after}

Expected final rows: {rows_before}

Row multiplication:
{rows_after - rows_before}


INVENTORY ID VALIDATION
-----------------------

Missing inventory IDs: {missing_inventory_id}
Duplicate inventory IDs: {duplicate_inventory_id}


WAREHOUSE RELATIONSHIP
----------------------

Unmatched warehouse references:
{unmatched_warehouse_reference}


PRODUCT RELATIONSHIP
--------------------

Unmatched product references:
{unmatched_product_reference}


BUSINESS KEY
------------

Business key:
warehouse_id + product_id

Duplicate business-key groups:
{duplicate_business_groups}

Rows involved:
{duplicate_business_rows}

These records were preserved.


STOCK QUANTITY
--------------

Missing stock: {missing_stock}
Zero stock: {zero_stock}
Negative stock: {negative_stock}
Positive stock: {(fact["stock_quantity"] > 0).sum()}

Minimum stock:
{fact["stock_quantity"].min()}

Maximum stock:
{fact["stock_quantity"].max()}


REORDER LEVEL
-------------

Missing reorder levels: {missing_reorder}
Zero reorder levels: {zero_reorder}
Negative reorder levels: {negative_reorder}
Positive reorder levels: {(fact["reorder_level"] > 0).sum()}

Minimum reorder level:
{fact["reorder_level"].min()}

Maximum reorder level:
{fact["reorder_level"].max()}


STOCK VS REORDER LEVEL
----------------------

Below Reorder Level:
{below_reorder}

At Reorder Level:
{at_reorder}

Above Reorder Level:
{above_reorder}

Cannot Determine:
{cannot_determine_stock}


RESTOCK DATE
------------

Missing restock dates:
{fact["last_restock_date"].isna().sum()}

Future restock dates:
{future_restock_count}

Earliest restock date:
{fact["last_restock_date"].min()}

Latest restock date:
{fact["last_restock_date"].max()}


PRODUCT ENRICHMENT
------------------

Product columns added:

product_name
category
unit_price
is_active


WAREHOUSE ENRICHMENT
--------------------

Warehouse columns added:

warehouse_name
location
capacity_units


SOURCE VALUES PRESERVED
-----------------------

No source inventory values were overwritten.
Missing stock values were not filled.
Missing reorder levels were not filled.
Missing dates were not invented.
No inventory records were intentionally deleted.


ANALYTICAL COLUMNS
------------------

stock_status
restock_date_status
business_key_status
inventory_key_status


FEATURE ENGINEERING NOT CREATED
-------------------------------

No stock value created.
No inventory turnover created.
No days of inventory created.
No reorder flag created.
No stock risk score created.
No inventory health score created.
No ABC classification created.
No warehouse utilization created.


FINAL VALIDATION
----------------

Final rows = source rows:
{rows_after == rows_before}

Final duplicate inventory IDs:
{duplicate_inventory_id}

Final missing inventory IDs:
{missing_inventory_id}

Final unmatched warehouse references:
{unmatched_warehouse_reference}

Final unmatched product references:
{unmatched_product_reference}

Final negative stock values:
{negative_stock}

Final negative reorder levels:
{negative_reorder}


FINAL STATUS
------------
{status}
"""

REPORT_FILE.write_text(
    report,
    encoding="utf-8"
)


# ==================================================
# 16. OUTPUT
# ==================================================

print("\nFact Inventory created successfully.")
print("Rows:", rows_after)
print("Columns:", len(fact.columns))
print("Output:", OUTPUT_FILE)
print("Report:", REPORT_FILE)
print("Final status:", status)