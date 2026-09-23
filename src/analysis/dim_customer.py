from pathlib import Path
import pandas as pd


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(r"C:\supply_chain_intelligence")

CUSTOMER_FILE = BASE_DIR / "data" / "cleaned" / "customers_cleaned.csv"
ORDER_FILE = BASE_DIR / "data" / "cleaned" / "orders_cleaned.csv"

OUTPUT_DIR = BASE_DIR / "data" / "analytical"
REPORT_DIR = BASE_DIR / "reports"

OUTPUT_FILE = OUTPUT_DIR / "dim_customer.csv"
REPORT_FILE = REPORT_DIR / "dim_customer_report.txt"


# ============================================================
# LOAD DATA
# ============================================================

def load_data():
    customers = pd.read_csv(CUSTOMER_FILE)
    orders = pd.read_csv(ORDER_FILE)

    return customers, orders


# ============================================================
# BASIC STANDARDIZATION
# ============================================================

def prepare_data(customers, orders):
    customers["customer_id"] = pd.to_numeric(
        customers["customer_id"],
        errors="coerce"
    ).astype("Int64")

    orders["customer_id"] = pd.to_numeric(
        orders["customer_id"],
        errors="coerce"
    ).astype("Int64")

    customers["signup_date"] = pd.to_datetime(
        customers["signup_date"],
        errors="coerce"
    )

    orders["order_date"] = pd.to_datetime(
        orders["order_date"],
        errors="coerce"
    )

    return customers, orders


# ============================================================
# BUILD CUSTOMER-LEVEL ORDER SUMMARY
# ============================================================

def build_order_summary(orders):
    order_summary = (
        orders.dropna(subset=["customer_id"])
        .groupby("customer_id")
        .agg(
            order_count=("order_id", "nunique"),
            first_order_date=("order_date", "min"),
            last_order_date=("order_date", "max")
        )
        .reset_index()
    )

    return order_summary


# ============================================================
# BUILD CUSTOMER DIMENSION
# ============================================================

def build_dimension(customers, order_summary):

    dim_customer = customers.merge(
        order_summary,
        on="customer_id",
        how="left",
        validate="one_to_one"
    )

    # Whether the customer has at least one order
    dim_customer["has_orders"] = (
        dim_customer["order_count"].fillna(0) > 0
    )

    # --------------------------------------------------------
    # Days between signup and first order
    # --------------------------------------------------------

    dim_customer["signup_to_first_order_days"] = (
        dim_customer["first_order_date"] - dim_customer["signup_date"]
    ).dt.days

    # --------------------------------------------------------
    # Validate signup vs first order date
    # --------------------------------------------------------

    dim_customer["signup_order_date_status"] = "Cannot Determine"

    valid_dates = (
        dim_customer["signup_date"].notna()
        & dim_customer["first_order_date"].notna()
    )

    dim_customer.loc[
        valid_dates,
        "signup_order_date_status"
    ] = "Valid"

    dim_customer.loc[
        valid_dates
        & (
            dim_customer["first_order_date"]
            < dim_customer["signup_date"]
        ),
        "signup_order_date_status"
    ] = "First Order Before Signup"

    # --------------------------------------------------------
    # Make order_count integer-like
    # --------------------------------------------------------

    dim_customer["order_count"] = (
        dim_customer["order_count"]
        .fillna(0)
        .astype(int)
    )

    return dim_customer


# ============================================================
# VALIDATION
# ============================================================

def validate_data(dim_customer, original_customers):

    issues = []

    source_rows = len(original_customers)
    final_rows = len(dim_customer)

    missing_customer_ids = dim_customer["customer_id"].isna().sum()
    duplicate_customer_ids = dim_customer["customer_id"].duplicated().sum()

    invalid_segments = sorted(
        set(dim_customer["segment"].dropna().unique())
        - {"Retail", "Wholesale", "Corporate", "Online"}
    )

    first_order_before_signup = (
        dim_customer["signup_order_date_status"]
        == "First Order Before Signup"
    ).sum()

    source_columns = [
        "customer_id",
        "customer_name",
        "email",
        "country",
        "segment",
        "signup_date"
    ]

    missing_source_columns = [
        column
        for column in source_columns
        if column not in dim_customer.columns
    ]

    if source_rows != final_rows:
        issues.append("Final row count differs from source.")

    if missing_customer_ids > 0:
        issues.append("Missing customer IDs found.")

    if duplicate_customer_ids > 0:
        issues.append("Duplicate customer IDs found.")

    if invalid_segments:
        issues.append("Invalid segment values found.")

    if missing_source_columns:
        issues.append("Source columns missing from final output.")

    if issues:
        status = "FAIL"
    elif first_order_before_signup > 0:
        status = "PASS WITH WARNINGS"
    else:
        status = "PASS"

    return {
        "source_rows": source_rows,
        "final_rows": final_rows,
        "missing_customer_ids": missing_customer_ids,
        "duplicate_customer_ids": duplicate_customer_ids,
        "invalid_segments": invalid_segments,
        "first_order_before_signup": first_order_before_signup,
        "missing_source_columns": missing_source_columns,
        "status": status
    }


# ============================================================
# REPORT
# ============================================================

def create_report(
    customers,
    orders,
    dim_customer,
    validation
):

    source_rows = len(customers)
    final_rows = len(dim_customer)

    missing_email = dim_customer["email"].isna().sum()
    missing_segment = dim_customer["segment"].isna().sum()
    missing_signup = dim_customer["signup_date"].isna().sum()

    duplicate_names = (
        dim_customer["customer_name"]
        .duplicated(keep=False)
        .sum()
    )

    duplicate_emails = (
        dim_customer["email"]
        .dropna()
        .duplicated(keep=False)
        .sum()
    )

    customers_with_orders = dim_customer["has_orders"].sum()
    customers_without_orders = (
        (~dim_customer["has_orders"]).sum()
    )

    order_coverage = (
        orders["customer_id"]
        .isin(dim_customer["customer_id"].dropna())
        .sum()
    )

    report = f"""
CUSTOMER DIMENSION - ANALYTICAL REPORT
======================================

GRAIN
-----
One row represents one customer.


SOURCE
------
Customers
Orders


ROW COUNTS
----------
Customers before transformation:
{source_rows}

Orders used for customer enrichment:
{len(orders)}

Final dim_customer rows:
{final_rows}


CUSTOMER ID VALIDATION
----------------------
Missing customer IDs:
{validation["missing_customer_ids"]}

Duplicate customer IDs:
{validation["duplicate_customer_ids"]}


MISSING VALUES
--------------
Missing email:
{missing_email}

Missing segment:
{missing_segment}

Missing signup date:
{missing_signup}


CUSTOMER DUPLICATES
-------------------
Repeated customer-name rows:
{duplicate_names}

Repeated email rows:
{duplicate_emails}

These records were preserved.


SEGMENT VALUES
--------------
{dim_customer["segment"].value_counts(dropna=False).to_string()}


COUNTRY VALUES
--------------
{dim_customer["country"].value_counts(dropna=False).to_string()}


ORDER COVERAGE
--------------
Customers with orders:
{customers_with_orders}

Customers without orders:
{customers_without_orders}

Orders linked to known customer IDs:
{order_coverage}


CUSTOMER ORDER METRICS
----------------------
Customers with at least one order:
{customers_with_orders}

Maximum orders by one customer:
{dim_customer["order_count"].max()}

Average orders per customer:
{dim_customer["order_count"].mean():.2f}


SIGNUP / ORDER DATE VALIDATION
------------------------------
First Order Before Signup:
{validation["first_order_before_signup"]}

Cannot Determine:
{(
    dim_customer["signup_order_date_status"]
    == "Cannot Determine"
).sum()}

Valid:
{(
    dim_customer["signup_order_date_status"]
    == "Valid"
).sum()}


ANALYTICAL COLUMNS CREATED
--------------------------
order_count
first_order_date
last_order_date
has_orders
signup_to_first_order_days
signup_order_date_status


SOURCE VALUES PRESERVED
-----------------------
customer_id preserved
customer_name preserved
email preserved
country preserved
segment preserved
signup_date preserved

No customer records intentionally deleted.
No missing customer attributes were invented.
Repeated names were not merged.
Repeated emails were not merged.


FEATURE ENGINEERING
-------------------
Advanced feature engineering was intentionally not created.

Not created:
- Customer lifetime value
- Customer churn score
- Customer score
- Customer tier
- RFM score
- Customer risk score

These will be handled later using documented business definitions.


FINAL VALIDATION
----------------
Source rows = Final rows:
{source_rows == final_rows}

Final duplicate customer IDs:
{validation["duplicate_customer_ids"]}

Final missing customer IDs:
{validation["missing_customer_ids"]}

Invalid segments:
{len(validation["invalid_segments"])}

First order before signup:
{validation["first_order_before_signup"]}


FINAL STATUS
------------
{validation["status"]}
"""

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text(report.strip(), encoding="utf-8")


# ============================================================
# MAIN
# ============================================================

def main():

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    customers, orders = load_data()

    print(f"Customers: {customers.shape}")
    print(f"Orders: {orders.shape}")

    customers, orders = prepare_data(customers, orders)

    order_summary = build_order_summary(orders)

    print(
        f"\nCustomer-level order summary: "
        f"{order_summary.shape}"
    )

    dim_customer = build_dimension(
        customers,
        order_summary
    )

    print(
        f"Rows after customer enrichment: "
        f"{len(dim_customer)}"
    )

    validation = validate_data(
        dim_customer,
        customers
    )

    dim_customer.to_csv(
        OUTPUT_FILE,
        index=False
    )

    create_report(
        customers,
        orders,
        dim_customer,
        validation
    )

    print("\nDIM CUSTOMER CREATED SUCCESSFULLY.")
    print(f"Rows: {len(dim_customer)}")
    print(f"Columns: {len(dim_customer.columns)}")
    print(f"Output: {OUTPUT_FILE}")
    print(f"Report: {REPORT_FILE}")
    print(f"Final status: {validation['status']}")


if __name__ == "__main__":
    main()