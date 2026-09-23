import pandas as pd
from pathlib import Path


# ---------------------------------------------------------
# 1. File paths
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = BASE_DIR / "data" / "raw" / "03_warehouses.csv"

OUTPUT_FILE = BASE_DIR / "data" / "cleaned" / "warehouses_cleaned.csv"
REPORT_FILE = BASE_DIR / "reports" / "warehouses_cleaning_report.txt"


# Create folders if needed
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------
# 2. Load data
# ---------------------------------------------------------

df = pd.read_csv(INPUT_FILE)

rows_before = len(df)
original_columns = df.columns.tolist()

print("Warehouse shape:", df.shape)

print("\nColumns:")
print(df.columns.tolist())

print("\nData types:")
print(df.dtypes)

print("\nMissing values:")
print(df.isnull().sum())

print("\nExact duplicate rows:", df.duplicated().sum())


# ---------------------------------------------------------
# 3. Clean text fields
# ---------------------------------------------------------

df["warehouse_name"] = (
    df["warehouse_name"]
    .astype("string")
    .str.strip()
)

df["location"] = (
    df["location"]
    .astype("string")
    .str.strip()
)

df["manager"] = (
    df["manager"]
    .astype("string")
    .str.strip()
)


# ---------------------------------------------------------
# 4. Validate warehouse_id
# ---------------------------------------------------------

missing_warehouse_id = df["warehouse_id"].isnull().sum()
duplicate_warehouse_id = df["warehouse_id"].duplicated().sum()

df["warehouse_id"] = pd.to_numeric(
    df["warehouse_id"],
    errors="coerce"
)

invalid_warehouse_id = df["warehouse_id"].isnull().sum()

print("\nWarehouse ID")
print("Missing:", missing_warehouse_id)
print("Duplicate:", duplicate_warehouse_id)
print("Invalid:", invalid_warehouse_id)


# ---------------------------------------------------------
# 5. Validate warehouse_name
# ---------------------------------------------------------

missing_warehouse_name = df["warehouse_name"].isnull().sum()

blank_warehouse_name = (
    df["warehouse_name"]
    .fillna("")
    .str.strip()
    .eq("")
    .sum()
)

duplicate_warehouse_name = df["warehouse_name"].duplicated().sum()

print("\nWarehouse Name")
print("Missing:", missing_warehouse_name)
print("Blank:", blank_warehouse_name)
print("Duplicate:", duplicate_warehouse_name)


# ---------------------------------------------------------
# 6. Standardize location
# ---------------------------------------------------------

location_mapping = {
    "IND": "India",
    "germany": "Germany",
    "U.K.": "United Kingdom"
}

df["location"] = df["location"].replace(location_mapping)

print("\nLocation values after standardization:")
print(sorted(df["location"].dropna().unique()))


# ---------------------------------------------------------
# 7. Validate capacity
# ---------------------------------------------------------

df["capacity_units"] = pd.to_numeric(
    df["capacity_units"],
    errors="coerce"
)

missing_capacity = df["capacity_units"].isnull().sum()
zero_capacity = (df["capacity_units"] == 0).sum()
negative_capacity = (df["capacity_units"] < 0).sum()

# Capacity should be whole units
non_integer_capacity = (
    df["capacity_units"].notna()
    & (df["capacity_units"] % 1 != 0)
).sum()

print("\nCapacity")
print("Missing:", missing_capacity)
print("Zero:", zero_capacity)
print("Negative:", negative_capacity)
print("Non-integer:", non_integer_capacity)


# Convert to integer only after checking
df["capacity_units"] = df["capacity_units"].astype("Int64")


# ---------------------------------------------------------
# 8. Validate manager
# ---------------------------------------------------------

missing_manager = df["manager"].isnull().sum()

missing_manager_ids = df.loc[
    df["manager"].isnull(),
    "warehouse_id"
].tolist()

print("\nManager")
print("Missing:", missing_manager)
print("Warehouse IDs with missing manager:")
print(missing_manager_ids)


# ---------------------------------------------------------
# 9. Duplicate analysis
# ---------------------------------------------------------

exact_duplicates = df.duplicated().sum()

duplicate_name_rows = df[
    df["warehouse_name"].duplicated(keep=False)
].sort_values("warehouse_name")


# ---------------------------------------------------------
# 10. Final validation
# ---------------------------------------------------------

final_missing_ids = df["warehouse_id"].isnull().sum()
final_duplicate_ids = df["warehouse_id"].duplicated().sum()

final_missing_names = df["warehouse_name"].isnull().sum()
final_blank_names = (
    df["warehouse_name"]
    .fillna("")
    .str.strip()
    .eq("")
    .sum()
)

final_missing_capacity = df["capacity_units"].isnull().sum()
final_zero_capacity = (df["capacity_units"] == 0).sum()
final_negative_capacity = (df["capacity_units"] < 0).sum()

final_missing_manager = df["manager"].isnull().sum()


# ---------------------------------------------------------
# 11. Final status
# ---------------------------------------------------------

if (
    final_missing_ids == 0
    and final_duplicate_ids == 0
    and final_missing_names == 0
    and final_blank_names == 0
    and final_zero_capacity == 0
    and final_negative_capacity == 0
):
    final_status = "PASS WITH WARNINGS"
else:
    final_status = "FAIL"


# ---------------------------------------------------------
# 12. Save cleaned dataset
# ---------------------------------------------------------

df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ---------------------------------------------------------
# 13. Create cleaning report
# ---------------------------------------------------------

with open(REPORT_FILE, "w", encoding="utf-8") as file:

    file.write("WAREHOUSE CLEANING REPORT\n")
    file.write("=========================\n\n")

    file.write(f"Rows before cleaning: {rows_before}\n")
    file.write(f"Rows after cleaning: {len(df)}\n\n")

    file.write("ORIGINAL COLUMNS\n")
    file.write("----------------\n")
    file.write(", ".join(original_columns) + "\n\n")

    file.write("FINAL COLUMNS\n")
    file.write("-------------\n")
    file.write(", ".join(df.columns.tolist()) + "\n\n")

    file.write("MISSING VALUES\n")
    file.write("--------------\n")
    file.write(df.isnull().sum().to_string())
    file.write("\n\n")

    file.write("DUPLICATE ANALYSIS\n")
    file.write("------------------\n")
    file.write(f"Exact duplicate rows: {exact_duplicates}\n")
    file.write(f"Duplicate warehouse IDs: {duplicate_warehouse_id}\n")
    file.write(f"Duplicate warehouse names: {duplicate_warehouse_name}\n\n")

    if len(duplicate_name_rows) > 0:
        file.write("Duplicate warehouse names:\n")
        file.write(
            duplicate_name_rows[
                ["warehouse_id", "warehouse_name", "location"]
            ].to_string(index=False)
        )
        file.write("\n\n")

    file.write("WAREHOUSE ID VALIDATION\n")
    file.write("-----------------------\n")
    file.write(f"Missing warehouse IDs: {missing_warehouse_id}\n")
    file.write(f"Duplicate warehouse IDs: {duplicate_warehouse_id}\n")
    file.write(f"Invalid warehouse IDs: {invalid_warehouse_id}\n\n")

    file.write("WAREHOUSE NAME VALIDATION\n")
    file.write("-------------------------\n")
    file.write(f"Missing names: {missing_warehouse_name}\n")
    file.write(f"Blank names: {blank_warehouse_name}\n")
    file.write(f"Duplicate names: {duplicate_warehouse_name}\n\n")

    file.write("LOCATION STANDARDIZATION\n")
    file.write("-----------------------\n")
    file.write("IND -> India\n")
    file.write("germany -> Germany\n")
    file.write("U.K. -> United Kingdom\n\n")

    file.write("CAPACITY VALIDATION\n")
    file.write("-------------------\n")
    file.write(f"Missing capacity: {missing_capacity}\n")
    file.write(f"Zero capacity: {zero_capacity}\n")
    file.write(f"Negative capacity: {negative_capacity}\n")
    file.write(f"Non-integer capacity: {non_integer_capacity}\n\n")

    file.write("MANAGER VALIDATION\n")
    file.write("------------------\n")
    file.write(f"Missing managers: {missing_manager}\n")

    if missing_manager_ids:
        file.write(
            "Warehouse IDs with missing manager: "
            + ", ".join(map(str, missing_manager_ids))
            + "\n"
        )

    file.write("\n")

    file.write("RECORD CHANGES\n")
    file.write("--------------\n")
    file.write("Records removed: 0\n")
    file.write("Records intentionally deleted: 0\n\n")

    file.write("FINAL VALIDATION\n")
    file.write("----------------\n")
    file.write(f"Final missing warehouse IDs: {final_missing_ids}\n")
    file.write(f"Final duplicate warehouse IDs: {final_duplicate_ids}\n")
    file.write(f"Final missing warehouse names: {final_missing_names}\n")
    file.write(f"Final blank warehouse names: {final_blank_names}\n")
    file.write(f"Final missing capacity: {final_missing_capacity}\n")
    file.write(f"Final zero capacity: {final_zero_capacity}\n")
    file.write(f"Final negative capacity: {final_negative_capacity}\n")
    file.write(f"Final missing managers: {final_missing_manager}\n\n")

    file.write("UNRESOLVED ISSUES\n")
    file.write("-----------------\n")
    file.write(f"Missing managers: {final_missing_manager}\n")
    file.write(f"Duplicate warehouse names: {duplicate_warehouse_name}\n")
    file.write(f"Exact duplicate rows: {exact_duplicates}\n\n")

    file.write("FINAL STATUS\n")
    file.write("------------\n")
    file.write(final_status + "\n")


print("\nCleaning completed successfully.")
print("Cleaned file:", OUTPUT_FILE)
print("Cleaning report:", REPORT_FILE)
print("Final status:", final_status)

