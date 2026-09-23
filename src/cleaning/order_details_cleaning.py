import pandas as pd
from pathlib import Path


# ---------------------------------------------------------
# 1. File paths
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = BASE_DIR / "data" / "raw" / "06_order_details.csv"
PRODUCT_FILE = BASE_DIR / "data" / "raw" / "02_products.csv"
ORDER_FILE = BASE_DIR / "data" / "raw" / "05_orders.csv"

OUTPUT_FILE = BASE_DIR / "data" / "cleaned" / "order_details_cleaned.csv"
REPORT_FILE = BASE_DIR / "reports" / "order_details_cleaning_report.txt"


# Create folders if required
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------
# 2. Load data
# ---------------------------------------------------------

details = pd.read_csv(INPUT_FILE)
products = pd.read_csv(PRODUCT_FILE)
orders = pd.read_csv(ORDER_FILE)

rows_before = len(details)
original_columns = details.columns.tolist()


# ---------------------------------------------------------
# 3. Basic inspection
# ---------------------------------------------------------

print("Order Details shape:", details.shape)

print("\nColumns:")
print(details.columns.tolist())

print("\nData types:")
print(details.dtypes)

print("\nMissing values:")
print(details.isnull().sum())

print("\nExact duplicate rows:", details.duplicated().sum())


# ---------------------------------------------------------
# 4. Remove useless columns
# ---------------------------------------------------------

remove_columns = [
    "Unnamed: 6",
    "Unnamed: 7",
    "Unnamed: 8",
    "Unnamed: 9",
    "Unnamed: 10",
    "Unnamed: 11",
    "Unnamed: 12"
]

details = details.drop(
    columns=remove_columns,
    errors="ignore"
)


# ---------------------------------------------------------
# 5. ID validation
# ---------------------------------------------------------

missing_detail_ids = details["order_detail_id"].isnull().sum()
duplicate_detail_ids = details["order_detail_id"].duplicated().sum()

missing_order_ids = details["order_id"].isnull().sum()
missing_product_ids = details["product_id"].isnull().sum()


# ---------------------------------------------------------
# 6. Order foreign-key validation
# ---------------------------------------------------------

valid_order_ids = set(orders["order_id"])

unmatched_orders = details[
    ~details["order_id"].isin(valid_order_ids)
][["order_detail_id", "order_id"]]


# ---------------------------------------------------------
# 7. Product foreign-key validation
# ---------------------------------------------------------

valid_product_ids = set(products["product_id"])

unmatched_products = details[
    ~details["product_id"].isin(valid_product_ids)
][["order_detail_id", "product_id"]]


# ---------------------------------------------------------
# 8. Quantity validation
# ---------------------------------------------------------

missing_quantity = details["quantity"].isnull().sum()
zero_quantity = (details["quantity"] == 0).sum()
negative_quantity = (details["quantity"] < 0).sum()


# ---------------------------------------------------------
# 9. Discount validation
# ---------------------------------------------------------

missing_discount = details["discount_pct"].isnull().sum()

invalid_discount = (
    (details["discount_pct"] < 0)
    | (details["discount_pct"] > 100)
).sum()


# ---------------------------------------------------------
# 10. Line total validation
# ---------------------------------------------------------

missing_line_total = details["line_total"].isnull().sum()
zero_line_total = (details["line_total"] == 0).sum()
negative_line_total = (details["line_total"] < 0).sum()


# ---------------------------------------------------------
# 11. Check negative transaction signs
# ---------------------------------------------------------

negative_quantity_positive_line = (
    (details["quantity"] < 0)
    & (details["line_total"] > 0)
).sum()

positive_quantity_negative_line = (
    (details["quantity"] > 0)
    & (details["line_total"] < 0)
).sum()


# ---------------------------------------------------------
# 12. Duplicate order/product combinations
# ---------------------------------------------------------

duplicate_order_product = details[
    details.duplicated(
        subset=["order_id", "product_id"],
        keep=False
    )
].sort_values(["order_id", "product_id"])

duplicate_order_product_groups = (
    duplicate_order_product
    .groupby(["order_id", "product_id"])
    .ngroups
)


# ---------------------------------------------------------
# 13. Formula validation
# ---------------------------------------------------------

check_data = details.merge(
    products[["product_id", "unit_price"]],
    on="product_id",
    how="left"
)

formula_check = (
    check_data["unit_price"].notna()
    & check_data["quantity"].notna()
    & check_data["discount_pct"].notna()
    & check_data["line_total"].notna()
)

expected_line_total = (
    check_data.loc[formula_check, "unit_price"]
    * check_data.loc[formula_check, "quantity"]
    * (
        1
        - check_data.loc[formula_check, "discount_pct"] / 100
    )
)

difference = (
    expected_line_total
    - check_data.loc[formula_check, "line_total"]
).abs()

formula_matching = (difference <= 0.01).sum()
formula_mismatch = (difference > 0.01).sum()

if len(difference) > 0:
    maximum_difference = difference.max()
else:
    maximum_difference = 0


# ---------------------------------------------------------
# 14. Missing line-total categories
# ---------------------------------------------------------

missing_line_data = check_data[
    check_data["line_total"].isnull()
]

category_1 = (
    missing_line_data["unit_price"].notna()
    & missing_line_data["discount_pct"].notna()
).sum()

category_2 = (
    missing_line_data["unit_price"].notna()
    & missing_line_data["discount_pct"].isna()
).sum()

category_3 = (
    missing_line_data["unit_price"].isna()
    & missing_line_data["discount_pct"].notna()
).sum()

category_4 = (
    missing_line_data["unit_price"].isna()
    & missing_line_data["discount_pct"].isna()
).sum()


# ---------------------------------------------------------
# 15. Missing discount reconstruction candidates
# ---------------------------------------------------------

discount_candidates = (
    details["discount_pct"].isnull()
    & details["line_total"].notnull()
)

discount_data = check_data[discount_candidates].copy()

discount_data = discount_data[
    discount_data["unit_price"].notna()
    & (discount_data["quantity"] != 0)
]

implied_discount = (
    1
    - discount_data["line_total"]
    / (
        discount_data["unit_price"]
        * discount_data["quantity"]
    )
)

valid_implied_discount = (
    (implied_discount >= 0)
    & (implied_discount <= 1)
)

discount_reconstruction_candidates = len(implied_discount)
invalid_implied_discount = (
    ~valid_implied_discount
).sum()


# ---------------------------------------------------------
# 16. Save cleaned file
# ---------------------------------------------------------

details.to_csv(OUTPUT_FILE, index=False)


# ---------------------------------------------------------
# 17. Final validation
# ---------------------------------------------------------

final_duplicate_ids = details["order_detail_id"].duplicated().sum()
final_missing_ids = details["order_detail_id"].isnull().sum()

final_columns = details.columns.tolist()


# ---------------------------------------------------------
# 18. Final status
# ---------------------------------------------------------

if (
    final_duplicate_ids == 0
    and final_missing_ids == 0
    and invalid_discount == 0
):
    final_status = "PASS WITH WARNINGS"
else:
    final_status = "FAIL"


# ---------------------------------------------------------
# 19. Create report
# ---------------------------------------------------------

with open(REPORT_FILE, "w", encoding="utf-8") as file:

    file.write("ORDER DETAILS CLEANING REPORT\n")
    file.write("=============================\n\n")

    file.write(f"Rows before cleaning: {rows_before}\n")
    file.write(f"Rows after cleaning: {len(details)}\n\n")

    file.write("ORIGINAL COLUMNS\n")
    file.write("----------------\n")
    file.write(", ".join(original_columns) + "\n\n")

    file.write("FINAL COLUMNS\n")
    file.write("-------------\n")
    file.write(", ".join(final_columns) + "\n\n")

    file.write("STRUCTURAL COLUMNS REMOVED\n")
    file.write("--------------------------\n")
    file.write(", ".join(remove_columns) + "\n\n")

    file.write("MISSING VALUES\n")
    file.write("--------------\n")
    file.write(details.isnull().sum().to_string() + "\n\n")

    file.write("ORDER DETAIL ID VALIDATION\n")
    file.write("--------------------------\n")
    file.write(f"Missing IDs: {missing_detail_ids}\n")
    file.write(f"Duplicate IDs: {duplicate_detail_ids}\n\n")

    file.write("ORDER ID FK VALIDATION\n")
    file.write("----------------------\n")
    file.write(f"Missing order IDs: {missing_order_ids}\n")
    file.write(
        f"Unmatched order references: "
        f"{len(unmatched_orders)}\n"
    )

    if len(unmatched_orders) > 0:
        file.write(unmatched_orders.to_string(index=False))
        file.write("\n")

    file.write("\n")

    file.write("PRODUCT ID FK VALIDATION\n")
    file.write("------------------------\n")
    file.write(f"Missing product IDs: {missing_product_ids}\n")
    file.write(
        f"Unmatched product references: "
        f"{len(unmatched_products)}\n"
    )

    if len(unmatched_products) > 0:
        file.write(unmatched_products.to_string(index=False))
        file.write("\n")

    file.write("\n")

    file.write("QUANTITY VALIDATION\n")
    file.write("-------------------\n")
    file.write(f"Missing quantity: {missing_quantity}\n")
    file.write(f"Zero quantity: {zero_quantity}\n")
    file.write(f"Negative quantity: {negative_quantity}\n\n")

    file.write("NEGATIVE TRANSACTION VALIDATION\n")
    file.write("-------------------------------\n")
    file.write(
        f"Negative quantity + positive line total: "
        f"{negative_quantity_positive_line}\n"
    )
    file.write(
        f"Positive quantity + negative line total: "
        f"{positive_quantity_negative_line}\n\n"
    )

    file.write("DISCOUNT VALIDATION\n")
    file.write("-------------------\n")
    file.write(f"Missing discount: {missing_discount}\n")
    file.write(f"Invalid discount values: {invalid_discount}\n")
    file.write("Valid range: 0% to 100%\n\n")

    file.write("DISCOUNT RECONSTRUCTION REVIEW\n")
    file.write("------------------------------\n")
    file.write(
        f"Rows where missing discount could potentially be "
        f"reconstructed: {discount_reconstruction_candidates}\n"
    )
    file.write(
        f"Rows with invalid implied discount: "
        f"{invalid_implied_discount}\n\n"
    )

    file.write("LINE TOTAL VALIDATION\n")
    file.write("---------------------\n")
    file.write(f"Missing line totals: {missing_line_total}\n")
    file.write(f"Zero line totals: {zero_line_total}\n")
    file.write(f"Negative line totals: {negative_line_total}\n\n")

    file.write("MISSING LINE-TOTAL CLASSIFICATION\n")
    file.write("---------------------------------\n")
    file.write(
        f"Price known + discount known: {category_1}\n"
    )
    file.write(
        f"Price known + discount missing: {category_2}\n"
    )
    file.write(
        f"Price missing + discount known: {category_3}\n"
    )
    file.write(
        f"Price missing + discount missing: {category_4}\n\n"
    )

    file.write("FORMULA VALIDATION\n")
    file.write("------------------\n")
    file.write(
        "Formula: unit_price × quantity × "
        "(1 - discount_pct / 100)\n"
    )
    file.write(
        f"Comparable rows: {formula_check.sum()}\n"
    )
    file.write(
        f"Matching rows (within 0.01): "
        f"{formula_matching}\n"
    )
    file.write(
        f"Mismatched rows: {formula_mismatch}\n"
    )
    file.write(
        f"Maximum difference: "
        f"{maximum_difference}\n\n"
    )

    file.write("DUPLICATE ANALYSIS\n")
    file.write("------------------\n")
    file.write(
        f"Complete duplicate rows: "
        f"{details.duplicated().sum()}\n"
    )
    file.write(
        f"Duplicate order_detail_id: "
        f"{duplicate_detail_ids}\n"
    )
    file.write(
        f"Duplicate order/product groups: "
        f"{duplicate_order_product_groups}\n"
    )
    file.write(
        f"Rows involved in duplicate order/product groups: "
        f"{len(duplicate_order_product)}\n\n"
    )

    file.write("RECORD CHANGES\n")
    file.write("--------------\n")
    file.write("Records removed: 0\n")
    file.write(
        "Source financial values overwritten: 0\n\n"
    )

    file.write("UNRESOLVED ISSUES\n")
    file.write("-----------------\n")
    file.write(
        f"Unmatched order references: "
        f"{len(unmatched_orders)}\n"
    )
    file.write(
        f"Missing discounts: {missing_discount}\n"
    )
    file.write(
        f"Missing line totals: {missing_line_total}\n"
    )
    file.write(
        f"Negative quantity transactions: "
        f"{negative_quantity}\n"
    )
    file.write(
        f"Duplicate order/product groups requiring review: "
        f"{duplicate_order_product_groups}\n"
    )

    file.write("\nFINAL VALIDATION\n")
    file.write("----------------\n")
    file.write(
        f"Final duplicate order_detail_id: "
        f"{final_duplicate_ids}\n"
    )
    file.write(
        f"Final missing order_detail_id: "
        f"{final_missing_ids}\n"
    )
    file.write(
        f"Invalid discount values: "
        f"{invalid_discount}\n"
    )

    file.write("\nFINAL STATUS\n")
    file.write("------------\n")
    file.write(final_status + "\n")


print("\nCleaning completed successfully.")
print("Cleaned file:", OUTPUT_FILE)
print("Cleaning report:", REPORT_FILE)
print("Final status:", final_status)