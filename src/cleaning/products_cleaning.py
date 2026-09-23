import pandas as pd
from pathlib import Path


# ---------------------------------------------------------
# 1. File paths
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = BASE_DIR / "data" / "raw" / "02_products.csv"
SUPPLIER_FILE = BASE_DIR / "data" / "raw" / "01_suppliers.csv"

OUTPUT_FILE = BASE_DIR / "data" / "cleaned" / "products_cleaned.csv"
REPORT_FILE = BASE_DIR / "reports" / "products_cleaning_report.txt"


# Create output folders if they do not exist
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------
# 2. Load data
# ---------------------------------------------------------

products = pd.read_csv(INPUT_FILE)
suppliers = pd.read_csv(SUPPLIER_FILE)

rows_before = len(products)
columns_before = products.columns.tolist()


# ---------------------------------------------------------
# 3. Basic inspection
# ---------------------------------------------------------

print("Products shape:", products.shape)
print("\nColumns:")
print(products.columns.tolist())

print("\nData types:")
print(products.dtypes)

print("\nMissing values:")
print(products.isnull().sum())

print("\nExact duplicate rows:", products.duplicated().sum())


# ---------------------------------------------------------
# 4. Save original values for change tracking
# ---------------------------------------------------------

original_names = products["product_name"].copy()
original_categories = products["category"].copy()
original_active = products["is_active"].copy()


# ---------------------------------------------------------
# 5. Clean text fields
# ---------------------------------------------------------

products["product_name"] = products["product_name"].str.strip()
products["category"] = products["category"].str.strip()


# ---------------------------------------------------------
# 6. Product ID validation
# ---------------------------------------------------------

duplicate_product_ids = products["product_id"].duplicated().sum()
missing_product_ids = products["product_id"].isnull().sum()


# ---------------------------------------------------------
# 7. Category validation
# ---------------------------------------------------------

valid_categories = {
    "Apparel",
    "Automotive Parts",
    "Electronics",
    "Furniture",
    "Groceries",
    "Industrial Equipment",
    "Office Supplies",
    "Pharmaceuticals",
    "Sporting Goods",
    "Toys"
}

unexpected_categories = sorted(
    set(products["category"].dropna()) - valid_categories
)


# ---------------------------------------------------------
# 8. Supplier validation
# ---------------------------------------------------------

valid_supplier_ids = set(suppliers["supplier_id"])

unmatched_suppliers = products[
    ~products["supplier_id"].isin(valid_supplier_ids)
][["product_id", "supplier_id"]].copy()


# ---------------------------------------------------------
# 9. Unit price validation
# ---------------------------------------------------------

missing_unit_price = products["unit_price"].isnull().sum()
zero_unit_price = (products["unit_price"] == 0).sum()
negative_unit_price = (products["unit_price"] < 0).sum()


# ---------------------------------------------------------
# 10. Weight validation
# ---------------------------------------------------------

missing_weight = products["weight_kg"].isnull().sum()
zero_weight = (products["weight_kg"] == 0).sum()
negative_weight = (products["weight_kg"] < 0).sum()


# ---------------------------------------------------------
# 11. Standardize is_active
# ---------------------------------------------------------

products["is_active"] = (
    products["is_active"]
    .astype("string")
    .str.strip()
    .map({
        "Y": "Y",
        "y": "Y",
        "1": "Y",
        "N": "N",
        "n": "N",
        "0": "N"
    })
)

final_active_values = products["is_active"].dropna().unique().tolist()


# ---------------------------------------------------------
# 12. Duplicate product names
# ---------------------------------------------------------

duplicate_names = products[
    products["product_name"].duplicated(keep=False)
].sort_values("product_name")


# ---------------------------------------------------------
# 13. Exact descriptive duplicates
#    (same information except product_id)
# ---------------------------------------------------------

descriptive_columns = [
    "product_name",
    "category",
    "supplier_id",
    "unit_price",
    "weight_kg",
    "is_active"
]

exact_descriptive_duplicates = products[
    products.duplicated(subset=descriptive_columns, keep=False)
].sort_values(descriptive_columns)


# ---------------------------------------------------------
# 14. Track modified records
# ---------------------------------------------------------

name_changed = original_names.fillna("") != products["product_name"].fillna("")
category_changed = (
    original_categories.fillna("") != products["category"].fillna("")
)
active_changed = (
    original_active.fillna("").astype(str)
    != products["is_active"].fillna("").astype(str)
)

records_modified = (
    name_changed | category_changed | active_changed
).sum()


# ---------------------------------------------------------
# 15. Save cleaned dataset
# ---------------------------------------------------------

products.to_csv(OUTPUT_FILE, index=False)


# ---------------------------------------------------------
# 16. Final validation
# ---------------------------------------------------------

final_duplicate_ids = products["product_id"].duplicated().sum()
final_missing_names = products["product_name"].isnull().sum()
final_missing_categories = products["category"].isnull().sum()

allowed_active_values = {"Y", "N"}

invalid_active_values = [
    value
    for value in products["is_active"].dropna().unique()
    if value not in allowed_active_values
]


# ---------------------------------------------------------
# 17. Final status
# ---------------------------------------------------------

if (
    final_duplicate_ids == 0
    and final_missing_names == 0
    and final_missing_categories == 0
    and len(invalid_active_values) == 0
):
    final_status = "PASS WITH WARNINGS"
else:
    final_status = "FAIL"


# ---------------------------------------------------------
# 18. Create cleaning report
# ---------------------------------------------------------

with open(REPORT_FILE, "w", encoding="utf-8") as file:

    file.write("PRODUCT CLEANING REPORT\n")
    file.write("=======================\n\n")

    file.write(f"Rows before cleaning: {rows_before}\n")
    file.write(f"Rows after cleaning: {len(products)}\n\n")

    file.write("Original columns:\n")
    file.write(", ".join(columns_before) + "\n\n")

    file.write("Final columns:\n")
    file.write(", ".join(products.columns.tolist()) + "\n\n")

    file.write("MISSING VALUES\n")
    file.write("--------------\n")
    file.write(products.isnull().sum().to_string() + "\n\n")

    file.write("DUPLICATE ANALYSIS\n")
    file.write("------------------\n")
    file.write(
        f"Exact duplicate rows: {products.duplicated().sum()}\n"
    )
    file.write(
        f"Duplicate product IDs: {duplicate_product_ids}\n"
    )
    file.write(
        f"Duplicate product-name rows: {len(duplicate_names)}\n"
    )
    file.write(
        f"Exact descriptive-duplicate rows: "
        f"{len(exact_descriptive_duplicates)}\n\n"
    )

    if len(exact_descriptive_duplicates) > 0:
        file.write("Exact descriptive duplicates:\n")
        file.write(
            exact_descriptive_duplicates[
                ["product_id"] + descriptive_columns
            ].to_string(index=False)
        )
        file.write("\n\n")

    file.write("CATEGORY VALIDATION\n")
    file.write("-------------------\n")
    file.write(
        f"Unexpected categories: {len(unexpected_categories)}\n"
    )

    if unexpected_categories:
        file.write(
            "Unexpected values: "
            + ", ".join(unexpected_categories)
            + "\n"
        )

    file.write("\n")

    file.write("SUPPLIER FK VALIDATION\n")
    file.write("----------------------\n")
    file.write(
        f"Unmatched supplier references: "
        f"{len(unmatched_suppliers)}\n"
    )

    if len(unmatched_suppliers) > 0:
        file.write(unmatched_suppliers.to_string(index=False))
        file.write("\n")

    file.write("\n")

    file.write("UNIT PRICE VALIDATION\n")
    file.write("---------------------\n")
    file.write(f"Missing unit prices: {missing_unit_price}\n")
    file.write(f"Zero unit prices: {zero_unit_price}\n")
    file.write(f"Negative unit prices: {negative_unit_price}\n\n")

    file.write("WEIGHT VALIDATION\n")
    file.write("-----------------\n")
    file.write(f"Missing weights: {missing_weight}\n")
    file.write(f"Zero weights: {zero_weight}\n")
    file.write(f"Negative weights: {negative_weight}\n\n")

    file.write("IS_ACTIVE STANDARDIZATION\n")
    file.write("-------------------------\n")
    file.write("Mapping used:\n")
    file.write("Y / y / 1 -> Y\n")
    file.write("N / n / 0 -> N\n")
    file.write("Missing -> NULL\n\n")

    file.write("Final values:\n")
    file.write(
        products["is_active"]
        .value_counts(dropna=False)
        .to_string()
    )
    file.write("\n\n")

    file.write("RECORD CHANGES\n")
    file.write("--------------\n")
    file.write(f"Records modified: {records_modified}\n")
    file.write("Records removed: 0\n")
    file.write(
        f"Records flagged: {len(unmatched_suppliers) + len(duplicate_names)}\n"
    )
    file.write("\n")

    file.write("FINAL VALIDATION\n")
    file.write("----------------\n")
    file.write(
        f"Final duplicate product IDs: {final_duplicate_ids}\n"
    )
    file.write(
        f"Final missing product names: {final_missing_names}\n"
    )
    file.write(
        f"Final missing categories: {final_missing_categories}\n"
    )
    file.write(
        f"Invalid is_active values: {len(invalid_active_values)}\n"
    )

    file.write("\n")

    file.write("UNRESOLVED ISSUES\n")
    file.write("-----------------\n")
    file.write(f"Missing unit prices: {missing_unit_price}\n")
    file.write(f"Missing weights: {missing_weight}\n")
    file.write(
        f"Unmatched supplier references: {len(unmatched_suppliers)}\n"
    )
    file.write(
        f"Duplicate product-name rows requiring review: "
        f"{len(duplicate_names)}\n"
    )

    file.write("\n")

    file.write("FINAL STATUS\n")
    file.write("------------\n")
    file.write(final_status + "\n")


# ---------------------------------------------------------
# 19. Finish
# ---------------------------------------------------------

print("\nCleaning completed successfully.")
print("Cleaned file:", OUTPUT_FILE)
print("Cleaning report:", REPORT_FILE)
print("Final status:", final_status)