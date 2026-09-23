from pathlib import Path
import pandas as pd


# ==================================================
# 1. PATHS
# ==================================================

BASE_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = BASE_DIR / "data" / "cleaned"

INVENTORY_FILE = DATA_DIR / "inventory_cleaned.csv"
PRODUCTS_FILE = DATA_DIR / "products_cleaned.csv"
WAREHOUSES_FILE = DATA_DIR / "warehouses_cleaned.csv"


# ==================================================
# 2. LOAD DATA
# ==================================================

inventory = pd.read_csv(INVENTORY_FILE)
products = pd.read_csv(PRODUCTS_FILE)
warehouses = pd.read_csv(WAREHOUSES_FILE)

print("Inventory:", inventory.shape)
print("Products:", products.shape)
print("Warehouses:", warehouses.shape)


# ==================================================
# 3. BASIC PROFILE
# ==================================================

print("\nInventory columns:")
print(inventory.columns.tolist())

print("\nInventory missing values:")
print(inventory.isna().sum())

print("\nDuplicate inventory IDs:")
print(
    inventory["inventory_id"].duplicated().sum()
)


# ==================================================
# 4. INVENTORY ID
# ==================================================

print("\nINVENTORY ID")
print("------------")

print(
    "Missing:",
    inventory["inventory_id"].isna().sum()
)

print(
    "Unique:",
    inventory["inventory_id"].nunique()
)


# ==================================================
# 5. WAREHOUSE RELATIONSHIP
# ==================================================

valid_warehouse_ids = set(
    warehouses["warehouse_id"].dropna()
)

warehouse_exists = (
    inventory["warehouse_id"]
    .isin(valid_warehouse_ids)
)

print("\nWAREHOUSE RELATIONSHIP")
print("----------------------")

print(
    "Valid warehouse references:",
    warehouse_exists.sum()
)

print(
    "Unmatched warehouse references:",
    (~warehouse_exists).sum()
)


# ==================================================
# 6. PRODUCT RELATIONSHIP
# ==================================================

valid_product_ids = set(
    products["product_id"].dropna()
)

product_exists = (
    inventory["product_id"]
    .isin(valid_product_ids)
)

print("\nPRODUCT RELATIONSHIP")
print("--------------------")

print(
    "Valid product references:",
    product_exists.sum()
)

print(
    "Unmatched product references:",
    (~product_exists).sum()
)


# ==================================================
# 7. WAREHOUSE + PRODUCT BUSINESS KEY
# ==================================================

duplicate_business_key = inventory.duplicated(
    subset=[
        "warehouse_id",
        "product_id"
    ],
    keep=False
)

duplicate_groups = (
    inventory.loc[duplicate_business_key]
    .groupby(
        ["warehouse_id", "product_id"]
    )
    .ngroups
)

print("\nWAREHOUSE + PRODUCT BUSINESS KEY")
print("---------------------------------")

print(
    "Duplicate rows:",
    duplicate_business_key.sum()
)

print(
    "Duplicate groups:",
    duplicate_groups
)

if duplicate_business_key.any():
    print("\nDuplicate combinations:")

    print(
        inventory.loc[
            duplicate_business_key,
            [
                "warehouse_id",
                "product_id",
                "inventory_id",
                "stock_quantity",
                "reorder_level",
                "last_restock_date"
            ]
        ]
        .sort_values(
            ["warehouse_id", "product_id"]
        )
        .to_string(index=False)
    )


# ==================================================
# 8. STOCK QUANTITY
# ==================================================

inventory["stock_quantity"] = pd.to_numeric(
    inventory["stock_quantity"],
    errors="coerce"
)

print("\nSTOCK QUANTITY")
print("--------------")

print(
    "Missing:",
    inventory["stock_quantity"].isna().sum()
)

print(
    "Zero:",
    (inventory["stock_quantity"] == 0).sum()
)

print(
    "Negative:",
    (inventory["stock_quantity"] < 0).sum()
)

print(
    "Positive:",
    (inventory["stock_quantity"] > 0).sum()
)

print(
    "Minimum:",
    inventory["stock_quantity"].min()
)

print(
    "Maximum:",
    inventory["stock_quantity"].max()
)


# ==================================================
# 9. REORDER LEVEL
# ==================================================

inventory["reorder_level"] = pd.to_numeric(
    inventory["reorder_level"],
    errors="coerce"
)

print("\nREORDER LEVEL")
print("-------------")

print(
    "Missing:",
    inventory["reorder_level"].isna().sum()
)

print(
    "Zero:",
    (inventory["reorder_level"] == 0).sum()
)

print(
    "Negative:",
    (inventory["reorder_level"] < 0).sum()
)

print(
    "Positive:",
    (inventory["reorder_level"] > 0).sum()
)

print(
    "Minimum:",
    inventory["reorder_level"].min()
)

print(
    "Maximum:",
    inventory["reorder_level"].max()
)


# ==================================================
# 10. STOCK VS REORDER LEVEL
# ==================================================

both_available = (
    inventory["stock_quantity"].notna()
    & inventory["reorder_level"].notna()
)

below_reorder = (
    both_available
    & (
        inventory["stock_quantity"]
        < inventory["reorder_level"]
    )
)

at_reorder = (
    both_available
    & (
        inventory["stock_quantity"]
        == inventory["reorder_level"]
    )
)

above_reorder = (
    both_available
    & (
        inventory["stock_quantity"]
        > inventory["reorder_level"]
    )
)

print("\nSTOCK VS REORDER LEVEL")
print("----------------------")

print(
    "Both values available:",
    both_available.sum()
)

print(
    "Stock below reorder level:",
    below_reorder.sum()
)

print(
    "Stock equal to reorder level:",
    at_reorder.sum()
)

print(
    "Stock above reorder level:",
    above_reorder.sum()
)


# ==================================================
# 11. RESTOCK DATE
# ==================================================

inventory["last_restock_date"] = pd.to_datetime(
    inventory["last_restock_date"],
    errors="coerce"
)

print("\nRESTOCK DATE")
print("------------")

print(
    "Missing:",
    inventory["last_restock_date"].isna().sum()
)

print(
    "Earliest:",
    inventory["last_restock_date"].min()
)

print(
    "Latest:",
    inventory["last_restock_date"].max()
)

future_restock = (
    inventory["last_restock_date"]
    > pd.Timestamp.today().normalize()
)

print(
    "Future restock dates:",
    future_restock.sum()
)


# ==================================================
# 12. PRODUCT INFORMATION
# ==================================================

product_info = products[
    [
        "product_id",
        "product_name",
        "category",
        "unit_price",
        "is_active"
    ]
]

inventory_profile = inventory.merge(
    product_info,
    on="product_id",
    how="left",
    validate="many_to_one"
)

print("\nRows after Product join:", len(inventory_profile))


# ==================================================
# 13. ACTIVE VS INACTIVE PRODUCTS
# ==================================================

print("\nINVENTORY BY PRODUCT STATUS")
print("---------------------------")

print(
    inventory_profile["is_active"]
    .value_counts(dropna=False)
)


# ==================================================
# 14. PRODUCTS WITHOUT INVENTORY
# ==================================================

inventory_product_ids = set(
    inventory["product_id"].dropna()
)

products_with_inventory = (
    products["product_id"]
    .isin(inventory_product_ids)
)

print("\nPRODUCT INVENTORY COVERAGE")
print("--------------------------")

print(
    "Products with inventory:",
    products_with_inventory.sum()
)

print(
    "Products without inventory:",
    (~products_with_inventory).sum()
)


# ==================================================
# 15. WAREHOUSE INVENTORY COVERAGE
# ==================================================

inventory_warehouse_ids = set(
    inventory["warehouse_id"].dropna()
)

warehouses_with_inventory = (
    warehouses["warehouse_id"]
    .isin(inventory_warehouse_ids)
)

print("\nWAREHOUSE INVENTORY COVERAGE")
print("----------------------------")

print(
    "Warehouses with inventory:",
    warehouses_with_inventory.sum()
)

print(
    "Warehouses without inventory:",
    (~warehouses_with_inventory).sum()
)


# ==================================================
# 16. INVENTORY RECORDS BY WAREHOUSE
# ==================================================

warehouse_inventory_counts = (
    inventory
    .groupby("warehouse_id")
    .size()
)

print("\nINVENTORY RECORDS PER WAREHOUSE")
print("-------------------------------")

print(
    "Minimum records:",
    warehouse_inventory_counts.min()
)

print(
    "Maximum records:",
    warehouse_inventory_counts.max()
)

print(
    "Average records:",
    warehouse_inventory_counts.mean()
)


# ==================================================
# 17. FINAL SUMMARY
# ==================================================

print("\nFINAL SUMMARY")
print("-------------")

print(
    "Total inventory rows:",
    len(inventory)
)

print(
    "Unique inventory IDs:",
    inventory["inventory_id"].nunique()
)

print(
    "Duplicate warehouse/product groups:",
    duplicate_groups
)

print(
    "Missing stock:",
    inventory["stock_quantity"].isna().sum()
)

print(
    "Missing reorder level:",
    inventory["reorder_level"].isna().sum()
)

print(
    "Future restock dates:",
    future_restock.sum()
)

print(
    "Stock below reorder level:",
    below_reorder.sum()
)

print(
    "Products without inventory:",
    (~products_with_inventory).sum()
)

print(
    "Warehouses without inventory:",
    (~warehouses_with_inventory).sum()
)

print("\nInventory analytical readiness profiling completed.")