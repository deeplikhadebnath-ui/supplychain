import pandas as pd
from pathlib import Path


# ---------------------------------------------------------
# 1. File paths
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = BASE_DIR / "data" / "raw" / "01_suppliers.csv"

OUTPUT_FILE = BASE_DIR / "data" / "cleaned" / "suppliers_cleaned.csv"
REPORT_FILE = BASE_DIR / "reports" / "suppliers_cleaning_report.txt"


# Create folders if needed
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------
# 2. Load data
# ---------------------------------------------------------

df = pd.read_csv(INPUT_FILE)

rows_before = len(df)
original_columns = df.columns.tolist()

print("Supplier shape:", df.shape)

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

df["supplier_name"] = (
    df["supplier_name"]
    .astype("string")
    .str.strip()
)

df["contact_email"] = (
    df["contact_email"]
    .astype("string")
    .str.strip()
    .str.lower()
)

df["phone"] = (
    df["phone"]
    .astype("string")
    .str.strip()
)

df["country"] = (
    df["country"]
    .astype("string")
    .str.strip()
)


# ---------------------------------------------------------
# 4. Supplier ID validation
# ---------------------------------------------------------

missing_supplier_id = df["supplier_id"].isnull().sum()
duplicate_supplier_id = df["supplier_id"].duplicated().sum()

df["supplier_id"] = pd.to_numeric(
    df["supplier_id"],
    errors="coerce"
)

invalid_supplier_id = df["supplier_id"].isnull().sum()


# ---------------------------------------------------------
# 5. Supplier name validation
# ---------------------------------------------------------

missing_supplier_name = df["supplier_name"].isnull().sum()

blank_supplier_name = (
    df["supplier_name"]
    .fillna("")
    .str.strip()
    .eq("")
    .sum()
)

duplicate_supplier_names = df[
    df["supplier_name"].duplicated(keep=False)
].sort_values("supplier_name")


# ---------------------------------------------------------
# 6. Country standardization
# ---------------------------------------------------------

country_mapping = {
    "USA": "United States",
    "U.S.A.": "United States",
    "United states": "United States",

    "UK": "United Kingdom",
    "U.K.": "United Kingdom",
    "england": "United Kingdom",

    "germany": "Germany",
    "DE": "Germany",

    "india": "India",
    "IND": "India"
}

df["country"] = df["country"].replace(country_mapping)


# ---------------------------------------------------------
# 7. Email validation
# ---------------------------------------------------------

missing_email = df["contact_email"].isnull().sum()

invalid_email = (
    df["contact_email"].notna()
    & ~df["contact_email"].str.match(
        r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
        na=False
    )
).sum()

duplicate_emails = df[
    df["contact_email"].notna()
    & df["contact_email"].duplicated(keep=False)
].sort_values("contact_email")


# ---------------------------------------------------------
# 8. Phone validation
# ---------------------------------------------------------

missing_phone = df["phone"].isnull().sum()

duplicate_phones = df[
    df["phone"].notna()
    & df["phone"].duplicated(keep=False)
].sort_values("phone")


# ---------------------------------------------------------
# 9. Rating validation
# ---------------------------------------------------------

df["rating"] = pd.to_numeric(
    df["rating"],
    errors="coerce"
)

missing_rating = df["rating"].isnull().sum()

invalid_rating = (
    df["rating"].notna()
    & (
        (df["rating"] < 1)
        | (df["rating"] > 5)
    )
).sum()


# ---------------------------------------------------------
# 10. Established year validation
# ---------------------------------------------------------

df["established_year"] = pd.to_numeric(
    df["established_year"],
    errors="coerce"
)

missing_established_year = df["established_year"].isnull().sum()

current_year = pd.Timestamp.today().year

invalid_established_year = (
    df["established_year"].notna()
    & (
        (df["established_year"] < 1800)
        | (df["established_year"] > current_year)
    )
).sum()


# ---------------------------------------------------------
# 11. Strong entity duplicate check
# ---------------------------------------------------------

duplicate_columns = [
    "supplier_name",
    "contact_email",
    "phone",
    "country",
    "rating",
    "established_year"
]

entity_duplicates = df[
    df.duplicated(
        subset=duplicate_columns,
        keep=False
    )
].sort_values(duplicate_columns)


# ---------------------------------------------------------
# 12. Final validation
# ---------------------------------------------------------

final_duplicate_ids = df["supplier_id"].duplicated().sum()
final_missing_ids = df["supplier_id"].isnull().sum()

final_missing_names = df["supplier_name"].isnull().sum()

final_invalid_rating = (
    df["rating"].notna()
    & (
        (df["rating"] < 1)
        | (df["rating"] > 5)
    )
).sum()

final_invalid_year = (
    df["established_year"].notna()
    & (
        (df["established_year"] < 1800)
        | (df["established_year"] > current_year)
    )
).sum()


# ---------------------------------------------------------
# 13. Final status
# ---------------------------------------------------------

if (
    final_duplicate_ids == 0
    and final_missing_ids == 0
    and final_missing_names == 0
    and invalid_email == 0
    and final_invalid_rating == 0
    and final_invalid_year == 0
):
    final_status = "PASS WITH WARNINGS"
else:
    final_status = "FAIL"


# ---------------------------------------------------------
# 14. Save cleaned dataset
# ---------------------------------------------------------

df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ---------------------------------------------------------
# 15. Create cleaning report
# ---------------------------------------------------------

with open(REPORT_FILE, "w", encoding="utf-8") as file:

    file.write("SUPPLIER CLEANING REPORT\n")
    file.write("========================\n\n")

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
    file.write(
        f"Exact duplicate rows: "
        f"{df.duplicated().sum()}\n"
    )
    file.write(
        f"Duplicate supplier IDs: "
        f"{duplicate_supplier_id}\n"
    )
    file.write(
        f"Duplicate supplier-name rows: "
        f"{len(duplicate_supplier_names)}\n"
    )
    file.write(
        f"Strong entity-duplicate rows: "
        f"{len(entity_duplicates)}\n\n"
    )

    if len(duplicate_supplier_names) > 0:
        file.write("REPEATED SUPPLIER NAMES\n")
        file.write("-----------------------\n")
        file.write(
            duplicate_supplier_names[
                ["supplier_id", "supplier_name", "country"]
            ].to_string(index=False)
        )
        file.write("\n\n")

    if len(entity_duplicates) > 0:
        file.write("STRONG ENTITY DUPLICATES\n")
        file.write("------------------------\n")
        file.write(
            entity_duplicates[
                ["supplier_id"] + duplicate_columns
            ].to_string(index=False)
        )
        file.write("\n\n")

    file.write("COUNTRY STANDARDIZATION\n")
    file.write("-----------------------\n")
    file.write("USA / U.S.A. / United states -> United States\n")
    file.write("UK / U.K. / england -> United Kingdom\n")
    file.write("germany / DE -> Germany\n")
    file.write("india / IND -> India\n\n")

    file.write("EMAIL VALIDATION\n")
    file.write("----------------\n")
    file.write(f"Missing contact emails: {missing_email}\n")
    file.write(f"Invalid contact emails: {invalid_email}\n")
    file.write(
        f"Duplicate contact-email rows: "
        f"{len(duplicate_emails)}\n\n"
    )

    if len(duplicate_emails) > 0:
        file.write("Duplicate contact emails:\n")
        file.write(
            duplicate_emails[
                ["supplier_id", "supplier_name", "contact_email"]
            ].to_string(index=False)
        )
        file.write("\n\n")

    file.write("PHONE VALIDATION\n")
    file.write("----------------\n")
    file.write(f"Missing phones: {missing_phone}\n")
    file.write(
        f"Duplicate phone rows: "
        f"{len(duplicate_phones)}\n\n"
    )

    file.write("RATING VALIDATION\n")
    file.write("-----------------\n")
    file.write(f"Missing ratings: {missing_rating}\n")
    file.write(f"Invalid ratings: {invalid_rating}\n")
    file.write("Expected range: 1 to 5\n\n")

    file.write("ESTABLISHED YEAR VALIDATION\n")
    file.write("---------------------------\n")
    file.write(
        f"Missing established years: "
        f"{missing_established_year}\n"
    )
    file.write(
        f"Invalid established years: "
        f"{invalid_established_year}\n"
    )
    file.write("Expected range: 1800 to current year\n\n")

    file.write("RECORD CHANGES\n")
    file.write("--------------\n")
    file.write("Records removed: 0\n")
    file.write(
        "Missing values were not artificially filled.\n"
    )
    file.write(
        "Suspicious records were not automatically deleted.\n\n"
    )

    file.write("FINAL VALIDATION\n")
    file.write("----------------\n")
    file.write(
        f"Final duplicate supplier IDs: "
        f"{final_duplicate_ids}\n"
    )
    file.write(
        f"Final missing supplier IDs: "
        f"{final_missing_ids}\n"
    )
    file.write(
        f"Final missing supplier names: "
        f"{final_missing_names}\n"
    )
    file.write(
        f"Final invalid contact emails: "
        f"{invalid_email}\n"
    )
    file.write(
        f"Final invalid ratings: "
        f"{final_invalid_rating}\n"
    )
    file.write(
        f"Final invalid established years: "
        f"{final_invalid_year}\n\n"
    )

    file.write("UNRESOLVED ISSUES\n")
    file.write("-----------------\n")
    file.write(
        f"Missing contact emails: {missing_email}\n"
    )
    file.write(
        f"Missing phones: {missing_phone}\n"
    )
    file.write(
        f"Missing ratings: {missing_rating}\n"
    )
    file.write(
        f"Missing established years: "
        f"{missing_established_year}\n"
    )
    file.write(
        f"Duplicate contact-email rows: "
        f"{len(duplicate_emails)}\n"
    )
    file.write(
        f"Duplicate phone rows: "
        f"{len(duplicate_phones)}\n"
    )
    file.write(
        f"Strong entity-duplicate rows: "
        f"{len(entity_duplicates)}\n"
    )

    file.write("\nFINAL STATUS\n")
    file.write("------------\n")
    file.write(final_status + "\n")


print("\nCleaning completed successfully.")
print("Cleaned file:", OUTPUT_FILE)
print("Cleaning report:", REPORT_FILE)
print("Final status:", final_status)