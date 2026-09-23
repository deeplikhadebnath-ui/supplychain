import pandas as pd
from pathlib import Path


# ---------------------------------------------------------
# 1. File paths
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = BASE_DIR / "data" / "raw" / "05_orders.csv"
CUSTOMER_FILE = BASE_DIR / "data" / "raw" / "04_customers.csv"
WAREHOUSE_FILE = BASE_DIR / "data" / "raw" / "03_warehouses.csv"
DETAIL_FILE = BASE_DIR / "data" / "raw" / "06_order_details.csv"

OUTPUT_FILE = BASE_DIR / "data" / "cleaned" / "orders_cleaned.csv"
REPORT_FILE = BASE_DIR / "reports" / "orders_cleaning_report.txt"


# Create folders if required
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------
# 2. Load data
# ---------------------------------------------------------

orders = pd.read_csv(INPUT_FILE)
customers = pd.read_csv(CUSTOMER_FILE)
warehouses = pd.read_csv(WAREHOUSE_FILE)
details = pd.read_csv(DETAIL_FILE)

rows_before = len(orders)
original_columns = orders.columns.tolist()


# ---------------------------------------------------------
# 3. Basic inspection
# ---------------------------------------------------------

print("Orders shape:", orders.shape)

print("\nColumns:")
print(orders.columns.tolist())

print("\nData types:")
print(orders.dtypes)

print("\nMissing values:")
print(orders.isnull().sum())

print("\nExact duplicate rows:", orders.duplicated().sum())


# ---------------------------------------------------------
# 4. Remove useless columns
# ---------------------------------------------------------

remove_columns = [
    "Column1",
    "Unnamed: 8",
    "Unnamed: 9",
    "Unnamed: 10",
    "Unnamed: 11"
]

orders = orders.drop(
    columns=remove_columns,
    errors="ignore"
)


# ---------------------------------------------------------
# 5. Order ID validation
# ---------------------------------------------------------

duplicate_order_ids = orders["order_id"].duplicated().sum()
missing_order_ids = orders["order_id"].isnull().sum()


# ---------------------------------------------------------
# 6. Customer validation
# ---------------------------------------------------------

valid_customer_ids = set(customers["customer_id"])

unmatched_customers = orders[
    ~orders["customer_id"].isin(valid_customer_ids)
][["order_id", "customer_id"]]


# ---------------------------------------------------------
# 7. Warehouse validation
# ---------------------------------------------------------

valid_warehouse_ids = set(warehouses["warehouse_id"])

unmatched_warehouses = orders[
    ~orders["warehouse_id"].isin(valid_warehouse_ids)
][["order_id", "warehouse_id"]]


# ---------------------------------------------------------
# 8. Standardize order status
# ---------------------------------------------------------

orders["order_status"] = (
    orders["order_status"]
    .astype("string")
    .str.strip()
    .str.title()
)

valid_statuses = {
    "Pending",
    "Shipped",
    "Delivered",
    "Returned",
    "Cancelled"
}

unexpected_statuses = sorted(
    set(orders["order_status"].dropna()) - valid_statuses
)


# ---------------------------------------------------------
# 9. Clean dates
# ---------------------------------------------------------

# Save original missing counts before conversion
missing_order_dates_before = orders["order_date"].isna().sum()
missing_ship_dates_before = orders["ship_date"].isna().sum()


# Convert mixed date formats to real datetime values
orders["order_date"] = pd.to_datetime(
    orders["order_date"],
    format="mixed",
    dayfirst=True,
    errors="coerce"
)

orders["ship_date"] = pd.to_datetime(
    orders["ship_date"],
    format="mixed",
    dayfirst=True,
    errors="coerce"
)


# ---------------------------------------------------------
# 10. Date validation
# ---------------------------------------------------------

missing_order_dates = orders["order_date"].isna().sum()
missing_ship_dates = orders["ship_date"].isna().sum()

unparseable_order_dates = (
    missing_order_dates - missing_order_dates_before
)

unparseable_ship_dates = (
    missing_ship_dates - missing_ship_dates_before
)

ship_before_order = (
    (orders["ship_date"] < orders["order_date"])
    & orders["ship_date"].notna()
    & orders["order_date"].notna()
).sum()

processing_date = pd.Timestamp.today().normalize()

future_order_dates = (
    orders["order_date"] > processing_date
).sum()

future_ship_dates = (
    orders["ship_date"] > processing_date
).sum()


# ---------------------------------------------------------
# 11. Order total validation
# ---------------------------------------------------------

missing_order_total = orders["order_total"].isnull().sum()
zero_order_total = (orders["order_total"] == 0).sum()
negative_order_total = (orders["order_total"] < 0).sum()


# ---------------------------------------------------------
# 12. Orders without Order Details
# ---------------------------------------------------------

orders_with_details = set(details["order_id"])

orders_without_details = orders[
    ~orders["order_id"].isin(orders_with_details)
][["order_id", "order_status"]]


# ---------------------------------------------------------
# 13. Save cleaned data
# ---------------------------------------------------------

orders.to_csv(OUTPUT_FILE, index=False)


# ---------------------------------------------------------
# 14. Final validation
# ---------------------------------------------------------

final_duplicate_ids = orders["order_id"].duplicated().sum()
final_missing_ids = orders["order_id"].isnull().sum()

final_invalid_statuses = [
    status
    for status in orders["order_status"].dropna().unique()
    if status not in valid_statuses
]


# ---------------------------------------------------------
# 15. Final status
# ---------------------------------------------------------

if (
    final_duplicate_ids == 0
    and final_missing_ids == 0
    and len(final_invalid_statuses) == 0
):
    final_status = "PASS WITH WARNINGS"
else:
    final_status = "FAIL"


# ---------------------------------------------------------
# 16. Create report
# ---------------------------------------------------------

with open(REPORT_FILE, "w", encoding="utf-8") as file:

    file.write("ORDERS CLEANING REPORT\n")
    file.write("=====================\n\n")

    file.write(f"Rows before cleaning: {rows_before}\n")
    file.write(f"Rows after cleaning: {len(orders)}\n\n")

    file.write("ORIGINAL COLUMNS\n")
    file.write("----------------\n")
    file.write(", ".join(original_columns) + "\n\n")

    file.write("FINAL COLUMNS\n")
    file.write("-------------\n")
    file.write(", ".join(orders.columns.tolist()) + "\n\n")

    file.write("STRUCTURAL COLUMNS REMOVED\n")
    file.write("--------------------------\n")
    file.write(", ".join(remove_columns) + "\n\n")

    file.write("MISSING VALUES\n")
    file.write("--------------\n")
    file.write(orders.isnull().sum().to_string() + "\n\n")

    file.write("ORDER ID VALIDATION\n")
    file.write("-------------------\n")
    file.write(f"Missing order IDs: {missing_order_ids}\n")
    file.write(f"Duplicate order IDs: {duplicate_order_ids}\n\n")

    file.write("CUSTOMER FK VALIDATION\n")
    file.write("----------------------\n")
    file.write(
        f"Unmatched customer references: "
        f"{len(unmatched_customers)}\n"
    )

    if len(unmatched_customers) > 0:
        file.write(unmatched_customers.to_string(index=False))
        file.write("\n")

    file.write("\nWAREHOUSE FK VALIDATION\n")
    file.write("-----------------------\n")
    file.write(
        f"Unmatched warehouse references: "
        f"{len(unmatched_warehouses)}\n"
    )

    if len(unmatched_warehouses) > 0:
        file.write(unmatched_warehouses.to_string(index=False))
        file.write("\n")

    file.write("\nORDER STATUS\n")
    file.write("------------\n")
    file.write("Standardization: strip whitespace + title case\n")
    file.write(f"Unexpected statuses: {len(unexpected_statuses)}\n")

    if unexpected_statuses:
        file.write(
            "Unexpected values: "
            + ", ".join(unexpected_statuses)
            + "\n"
        )

    file.write("\n")

    file.write("DATE VALIDATION\n")
    file.write("---------------\n")
    file.write(
        f"Missing order dates: "
        f"{missing_order_dates}\n"
    )
    file.write(
        f"Missing ship dates: "
        f"{missing_ship_dates}\n"
    )
    file.write(
        f"Unparseable order dates: "
        f"{unparseable_order_dates}\n"
    )
    file.write(
        f"Unparseable ship dates: "
        f"{unparseable_ship_dates}\n"
    )
    file.write(
        f"Ship date before order date: "
        f"{ship_before_order}\n"
    )
    file.write(
        f"Future order dates: "
        f"{future_order_dates}\n"
    )
    file.write(
        f"Future ship dates: "
        f"{future_ship_dates}\n\n"
    )

    file.write("ORDER TOTAL VALIDATION\n")
    file.write("----------------------\n")
    file.write(
        f"Missing order totals: "
        f"{missing_order_total}\n"
    )
    file.write(
        f"Zero order totals: "
        f"{zero_order_total}\n"
    )
    file.write(
        f"Negative order totals: "
        f"{negative_order_total}\n\n"
    )

    file.write("ORDERS WITHOUT ORDER DETAILS\n")
    file.write("----------------------------\n")
    file.write(
        f"Orders without details: "
        f"{len(orders_without_details)}\n\n"
    )

    file.write("FINAL VALIDATION\n")
    file.write("----------------\n")
    file.write(
        f"Final duplicate order IDs: "
        f"{final_duplicate_ids}\n"
    )
    file.write(
        f"Final missing order IDs: "
        f"{final_missing_ids}\n"
    )
    file.write(
        f"Invalid final statuses: "
        f"{len(final_invalid_statuses)}\n\n"
    )

    file.write("RECORD CHANGES\n")
    file.write("--------------\n")
    file.write("Records removed: 0\n\n")

    file.write("UNRESOLVED ISSUES\n")
    file.write("-----------------\n")
    file.write(
        f"Missing order totals: "
        f"{missing_order_total}\n"
    )
    file.write(
        f"Zero order totals: "
        f"{zero_order_total}\n"
    )
    file.write(
        f"Negative order totals: "
        f"{negative_order_total}\n"
    )
    file.write(
        f"Ship dates before order dates: "
        f"{ship_before_order}\n"
    )
    file.write(
        f"Future order dates: "
        f"{future_order_dates}\n"
    )
    file.write(
        f"Future ship dates: "
        f"{future_ship_dates}\n"
    )
    file.write(
        f"Orders without Order Details: "
        f"{len(orders_without_details)}\n"
    )
    file.write(
        f"Unmatched customers: "
        f"{len(unmatched_customers)}\n"
    )
    file.write(
        f"Unmatched warehouses: "
        f"{len(unmatched_warehouses)}\n"
    )

    file.write("\nFINAL STATUS\n")
    file.write("------------\n")
    file.write(final_status + "\n")


print("\nCleaning completed successfully.")
print("Cleaned file:", OUTPUT_FILE)
print("Cleaning report:", REPORT_FILE)
print("Final status:", final_status)