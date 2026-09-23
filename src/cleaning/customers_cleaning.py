from pathlib import Path
import pandas as pd


# --------------------------------------------------
# 1. FILE PATHS
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = BASE_DIR / "data" / "raw" / "04_customers.csv"
OUTPUT_FILE = BASE_DIR / "data" / "cleaned" / "customers_cleaned.csv"
REPORT_FILE = BASE_DIR / "reports" / "customers_cleaning_report.txt"

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------
# 2. LOAD DATA
# --------------------------------------------------

df = pd.read_csv(INPUT_FILE)

rows_before = len(df)

print("Customer shape:", df.shape)

print("\nColumns:")
print(df.columns.tolist())

print("\nData types:")
print(df.dtypes)

print("\nMissing values:")
print(df.isna().sum())

print("\nExact duplicate rows:", df.duplicated().sum())


# --------------------------------------------------
# 3. BASIC TEXT CLEANING
# --------------------------------------------------

# Remove accidental spaces
df["customer_name"] = (
    df["customer_name"]
    .astype("string")
    .str.strip()
)

df["email"] = (
    df["email"]
    .astype("string")
    .str.strip()
    .str.lower()
)

df["country"] = (
    df["country"]
    .astype("string")
    .str.strip()
)

df["segment"] = (
    df["segment"]
    .astype("string")
    .str.strip()
)


# --------------------------------------------------
# 4. CUSTOMER ID VALIDATION
# --------------------------------------------------

missing_customer_id = df["customer_id"].isna().sum()
duplicate_customer_id = df["customer_id"].duplicated().sum()

print("\nCustomer ID validation:")
print("Missing customer IDs:", missing_customer_id)
print("Duplicate customer IDs:", duplicate_customer_id)


# --------------------------------------------------
# 5. CUSTOMER NAME VALIDATION
# --------------------------------------------------

missing_customer_name = df["customer_name"].isna().sum()
blank_customer_name = df["customer_name"].eq("").sum()
duplicate_customer_name = df["customer_name"].duplicated().sum()

print("\nCustomer name validation:")
print("Missing names:", missing_customer_name)
print("Blank names:", blank_customer_name)
print("Repeated customer names:", duplicate_customer_name)


# --------------------------------------------------
# 6. EMAIL VALIDATION
# --------------------------------------------------

email_pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

invalid_email = (
    df["email"].notna()
    & ~df["email"].str.match(email_pattern, na=False)
).sum()

duplicate_email = (
    df["email"].notna()
    & df["email"].duplicated()
).sum()

missing_email = df["email"].isna().sum()

print("\nEmail validation:")
print("Missing emails:", missing_email)
print("Invalid emails:", invalid_email)
print("Duplicate email rows:", duplicate_email)


# --------------------------------------------------
# 7. COUNTRY STANDARDIZATION
# --------------------------------------------------

country_mapping = {
    "IND": "India",
    "india": "India",

    "DE": "Germany",
    "germany": "Germany",

    "UK": "United Kingdom",
    "U.K.": "United Kingdom",
    "england": "United Kingdom",

    "USA": "United States",
    "U.S.A.": "United States",
    "US": "United States",
    "us": "United States",
    "United states": "United States"
}

df["country"] = df["country"].replace(country_mapping)

print("\nCountry values after standardization:")
print(df["country"].value_counts(dropna=False))


# --------------------------------------------------
# 8. SEGMENT VALIDATION
# --------------------------------------------------

allowed_segments = {
    "Retail",
    "Wholesale",
    "Corporate",
    "Online"
}

invalid_segments = (
    df["segment"].notna()
    & ~df["segment"].isin(allowed_segments)
).sum()

missing_segment = df["segment"].isna().sum()

print("\nSegment validation:")
print("Missing segments:", missing_segment)
print("Invalid segments:", invalid_segments)

print("\nSegment values:")
print(df["segment"].value_counts(dropna=False))


# --------------------------------------------------
# 9. SIGNUP DATE CLEANING
# --------------------------------------------------

missing_signup_before = df["signup_date"].isna().sum()

df["signup_date"] = pd.to_datetime(
    df["signup_date"],
    format="mixed",
    dayfirst=True,
    errors="coerce"
)

unparseable_signup_date = (
    df["signup_date"].isna().sum()
    - missing_signup_before
)

# Check future dates
future_signup_date = (
    df["signup_date"] > pd.Timestamp.today().normalize()
).sum()

# Convert to YYYY-MM-DD
df["signup_date"] = df["signup_date"].dt.strftime("%Y-%m-%d")

print("\nSignup date validation:")
print("Missing signup dates before parsing:", missing_signup_before)
print("Unparseable signup dates:", unparseable_signup_date)
print("Future signup dates:", future_signup_date)


# --------------------------------------------------
# 10. SAVE CLEANED DATA
# --------------------------------------------------

df.to_csv(OUTPUT_FILE, index=False)

rows_after = len(df)


# --------------------------------------------------
# 11. FINAL VALIDATION
# --------------------------------------------------

final_duplicate_customer_id = df["customer_id"].duplicated().sum()
final_missing_customer_id = df["customer_id"].isna().sum()

final_invalid_email = (
    df["email"].notna()
    & ~df["email"].str.match(email_pattern, na=False)
).sum()

final_invalid_segment = (
    df["segment"].notna()
    & ~df["segment"].isin(allowed_segments)
).sum()


# --------------------------------------------------
# 12. FINAL STATUS
# --------------------------------------------------

if (
    final_duplicate_customer_id == 0
    and final_missing_customer_id == 0
    and final_invalid_email == 0
    and final_invalid_segment == 0
):
    status = "PASS WITH WARNINGS"
else:
    status = "FAIL"


# --------------------------------------------------
# 13. CLEANING REPORT
# --------------------------------------------------

report = f"""
CUSTOMER CLEANING REPORT
========================

Dataset: 04_customers.csv

Rows before cleaning: {rows_before}
Rows after cleaning: {rows_after}

MISSING VALUES
--------------
{df.isna().sum().to_string()}

DUPLICATE ANALYSIS
------------------
Exact duplicate rows: {df.duplicated().sum()}
Duplicate customer IDs: {final_duplicate_customer_id}
Duplicate customer-name rows: {duplicate_customer_name}
Duplicate email rows: {duplicate_email}

CUSTOMER ID VALIDATION
----------------------
Missing customer IDs: {missing_customer_id}
Duplicate customer IDs: {duplicate_customer_id}

CUSTOMER NAME VALIDATION
------------------------
Missing names: {missing_customer_name}
Blank names: {blank_customer_name}
Repeated customer names: {duplicate_customer_name}

EMAIL VALIDATION
----------------
Missing emails: {missing_email}
Invalid emails: {invalid_email}
Duplicate email rows: {duplicate_email}

COUNTRY STANDARDIZATION
-----------------------
IND -> India
india -> India
DE -> Germany
germany -> Germany
UK -> United Kingdom
U.K. -> United Kingdom
england -> United Kingdom
USA -> United States
U.S.A. -> United States
US -> United States
us -> United States
United states -> United States

SEGMENT VALIDATION
------------------
Missing segments: {missing_segment}
Invalid segments: {invalid_segments}

Allowed values:
Retail
Wholesale
Corporate
Online

SIGNUP DATE VALIDATION
----------------------
Missing signup dates before parsing: {missing_signup_before}
Unparseable signup dates: {unparseable_signup_date}
Future signup dates: {future_signup_date}

Date parsing method:
pd.to_datetime(format="mixed", dayfirst=True, errors="coerce")

Final date format:
YYYY-MM-DD

RECORD CHANGES
--------------
Records removed: 0
Missing values were not artificially filled.
Missing segments were not replaced.
Missing emails were not invented.
Repeated names/emails were not automatically deleted.

FINAL VALIDATION
----------------
Final duplicate customer IDs: {final_duplicate_customer_id}
Final missing customer IDs: {final_missing_customer_id}
Final invalid emails: {final_invalid_email}
Final invalid segments: {final_invalid_segment}
Final future signup dates: {future_signup_date}

FINAL STATUS
------------
{status}
"""

REPORT_FILE.write_text(report, encoding="utf-8")

print("\nCleaning completed successfully.")
print("Cleaned file:", OUTPUT_FILE)
print("Cleaning report:", REPORT_FILE)
print("Final status:", status)