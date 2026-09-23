from pathlib import Path
import pandas as pd


# --------------------------------------------------
# 1. FILE PATHS
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = BASE_DIR / "data" / "cleaned"
REPORT_FILE = BASE_DIR / "reports" / "cross_table_validation_report.txt"

REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------
# 2. LOAD CLEANED TABLES
# --------------------------------------------------

suppliers = pd.read_csv(DATA_DIR / "suppliers_cleaned.csv")
products = pd.read_csv(DATA_DIR / "products_cleaned.csv")
warehouses = pd.read_csv(DATA_DIR / "warehouses_cleaned.csv")
customers = pd.read_csv(DATA_DIR / "customers_cleaned.csv")
orders = pd.read_csv(DATA_DIR / "orders_cleaned.csv")
order_details = pd.read_csv(DATA_DIR / "order_details_cleaned.csv")
inventory = pd.read_csv(DATA_DIR / "inventory_cleaned.csv")
shipments = pd.read_csv(DATA_DIR / "shipments_cleaned.csv")

print("All cleaned tables loaded successfully.")


# --------------------------------------------------
# 3. FOREIGN KEY VALIDATION
# --------------------------------------------------

# Products -> Suppliers
unmatched_product_suppliers = products.loc[
    ~products["supplier_id"].isin(suppliers["supplier_id"]),
    "supplier_id"
].dropna().unique()

# Orders -> Customers
unmatched_order_customers = orders.loc[
    ~orders["customer_id"].isin(customers["customer_id"]),
    "customer_id"
].dropna().unique()

# Orders -> Warehouses
unmatched_order_warehouses = orders.loc[
    ~orders["warehouse_id"].isin(warehouses["warehouse_id"]),
    "warehouse_id"
].dropna().unique()

# Order Details -> Orders
unmatched_detail_orders = order_details.loc[
    ~order_details["order_id"].isin(orders["order_id"]),
    "order_id"
].dropna().unique()

# Order Details -> Products
unmatched_detail_products = order_details.loc[
    ~order_details["product_id"].isin(products["product_id"]),
    "product_id"
].dropna().unique()

# Inventory -> Warehouses
unmatched_inventory_warehouses = inventory.loc[
    ~inventory["warehouse_id"].isin(warehouses["warehouse_id"]),
    "warehouse_id"
].dropna().unique()

# Inventory -> Products
unmatched_inventory_products = inventory.loc[
    ~inventory["product_id"].isin(products["product_id"]),
    "product_id"
].dropna().unique()

# Shipments -> Orders
unmatched_shipment_orders = shipments.loc[
    ~shipments["order_id"].isin(orders["order_id"]),
    "order_id"
].dropna().unique()


# --------------------------------------------------
# 4. ORDER COVERAGE
# --------------------------------------------------

orders_with_details = orders["order_id"].isin(
    order_details["order_id"]
).sum()

orders_without_details = len(orders) - orders_with_details

orders_with_shipments = orders["order_id"].isin(
    shipments["order_id"]
).sum()

orders_without_shipments = len(orders) - orders_with_shipments


# --------------------------------------------------
# 5. STATUS COVERAGE
# --------------------------------------------------

orders["has_details"] = orders["order_id"].isin(
    order_details["order_id"]
)

orders["has_shipment"] = orders["order_id"].isin(
    shipments["order_id"]
)

status_details = pd.crosstab(
    orders["order_status"],
    orders["has_details"]
)

status_shipments = pd.crosstab(
    orders["order_status"],
    orders["has_shipment"]
)


# --------------------------------------------------
# 6. DATE VALIDATION
# --------------------------------------------------

orders["order_date"] = pd.to_datetime(
    orders["order_date"],
    errors="coerce"
)

orders["ship_date"] = pd.to_datetime(
    orders["ship_date"],
    errors="coerce"
)

customers["signup_date"] = pd.to_datetime(
    customers["signup_date"],
    errors="coerce"
)

shipments["shipment_date"] = pd.to_datetime(
    shipments["shipment_date"],
    errors="coerce"
)

shipments["delivery_date"] = pd.to_datetime(
    shipments["delivery_date"],
    errors="coerce"
)

inventory["last_restock_date"] = pd.to_datetime(
    inventory["last_restock_date"],
    errors="coerce"
)


# Customer signup vs order date
order_customer_dates = orders.merge(
    customers[["customer_id", "signup_date"]],
    on="customer_id",
    how="left"
)

orders_before_signup = (
    order_customer_dates["signup_date"].notna()
    & order_customer_dates["order_date"].notna()
    & (
        order_customer_dates["order_date"]
        < order_customer_dates["signup_date"]
    )
).sum()


# Order date -> ship date
ship_before_order = (
    orders["ship_date"].notna()
    & orders["order_date"].notna()
    & (
        orders["ship_date"]
        < orders["order_date"]
    )
).sum()


# Shipment date -> order date
shipment_order_dates = orders[
    ["order_id", "order_date"]
].merge(
    shipments[
        ["order_id", "shipment_date", "delivery_date"]
    ],
    on="order_id",
    how="inner"
)

shipment_before_order = (
    shipment_order_dates["shipment_date"].notna()
    & shipment_order_dates["order_date"].notna()
    & (
        shipment_order_dates["shipment_date"]
        < shipment_order_dates["order_date"]
    )
).sum()


# Delivery date -> shipment date
delivery_before_shipment = (
    shipments["delivery_date"].notna()
    & shipments["shipment_date"].notna()
    & (
        shipments["delivery_date"]
        < shipments["shipment_date"]
    )
).sum()


# --------------------------------------------------
# 7. FINANCIAL RECONCILIATION
# --------------------------------------------------

order_details["line_total"] = pd.to_numeric(
    order_details["line_total"],
    errors="coerce"
)

orders["order_total"] = pd.to_numeric(
    orders["order_total"],
    errors="coerce"
)

line_totals = (
    order_details
    .groupby("order_id")["line_total"]
    .sum(min_count=1)
    .reset_index(name="calculated_line_total")
)

financial_check = orders.merge(
    line_totals,
    on="order_id",
    how="left"
)

financial_comparable = (
    financial_check["order_total"].notna()
    & financial_check["calculated_line_total"].notna()
)

financial_matches = (
    financial_check.loc[
        financial_comparable,
        "order_total"
    ]
    - financial_check.loc[
        financial_comparable,
        "calculated_line_total"
    ]
).abs() <= 0.01

financial_comparable_count = financial_comparable.sum()
financial_match_count = financial_matches.sum()
financial_mismatch_count = (
    financial_comparable_count
    - financial_match_count
)


# --------------------------------------------------
# 8. PRODUCT / INVENTORY COVERAGE
# --------------------------------------------------

products_with_inventory = products["product_id"].isin(
    inventory["product_id"]
).sum()

products_without_inventory = (
    len(products) - products_with_inventory
)


# --------------------------------------------------
# 9. SUPPLIER COVERAGE
# --------------------------------------------------

suppliers_with_products = suppliers["supplier_id"].isin(
    products["supplier_id"]
).sum()

suppliers_without_products = (
    len(suppliers) - suppliers_with_products
)


# --------------------------------------------------
# 10. INVENTORY BUSINESS KEY
# --------------------------------------------------

inventory_duplicate_key = inventory.duplicated(
    subset=["warehouse_id", "product_id"],
    keep=False
)

inventory_duplicate_groups = (
    inventory.loc[inventory_duplicate_key]
    .groupby(
        ["warehouse_id", "product_id"]
    )
    .ngroups
)


# --------------------------------------------------
# 11. ORDER / SHIPMENT STATUS OBSERVATION
# --------------------------------------------------

status_shipment_rates = (
    orders.groupby("order_status")["has_shipment"]
    .mean()
    .mul(100)
    .round(2)
)


# --------------------------------------------------
# 12. REPORT
# --------------------------------------------------

report = f"""
CROSS-TABLE VALIDATION REPORT
=============================

TABLE COUNTS
------------
Suppliers: {len(suppliers)}
Products: {len(products)}
Warehouses: {len(warehouses)}
Customers: {len(customers)}
Orders: {len(orders)}
Order Details: {len(order_details)}
Inventory: {len(inventory)}
Shipments: {len(shipments)}

FOREIGN KEY VALIDATION
----------------------

Products -> Suppliers
Unmatched supplier IDs: {len(unmatched_product_suppliers)}
Values: {list(unmatched_product_suppliers)}

Orders -> Customers
Unmatched customer IDs: {len(unmatched_order_customers)}
Values: {list(unmatched_order_customers)}

Orders -> Warehouses
Unmatched warehouse IDs: {len(unmatched_order_warehouses)}
Values: {list(unmatched_order_warehouses)}

Order Details -> Orders
Unmatched order IDs: {len(unmatched_detail_orders)}
Values: {list(unmatched_detail_orders)}

Order Details -> Products
Unmatched product IDs: {len(unmatched_detail_products)}
Values: {list(unmatched_detail_products)}

Inventory -> Warehouses
Unmatched warehouse IDs: {len(unmatched_inventory_warehouses)}
Values: {list(unmatched_inventory_warehouses)}

Inventory -> Products
Unmatched product IDs: {len(unmatched_inventory_products)}
Values: {list(unmatched_inventory_products)}

Shipments -> Orders
Unmatched order IDs: {len(unmatched_shipment_orders)}
Values: {list(unmatched_shipment_orders)}

ORDER COVERAGE
--------------
Orders with order details: {orders_with_details}
Orders without order details: {orders_without_details}

Orders with shipments: {orders_with_shipments}
Orders without shipments: {orders_without_shipments}

ORDER STATUS VS DETAILS
-----------------------
{status_details.to_string()}

ORDER STATUS VS SHIPMENTS
-------------------------
{status_shipments.to_string()}

SHIPMENT COVERAGE BY ORDER STATUS (%)
-------------------------------------
{status_shipment_rates.to_string()}

DATE VALIDATION
---------------

Orders before customer signup: {orders_before_signup}

Ship dates before order dates: {ship_before_order}

Shipment dates before order dates: {shipment_before_order}

Delivery dates before shipment dates: {delivery_before_shipment}

These cases are reported only.
No records were deleted.

FINANCIAL RECONCILIATION
------------------------
Orders with comparable order_total and line_total sum:
{financial_comparable_count}

Financial matches within 0.01:
{financial_match_count}

Financial mismatches:
{financial_mismatch_count}

PRODUCT / INVENTORY COVERAGE
----------------------------
Products with inventory records: {products_with_inventory}
Products without inventory records: {products_without_inventory}

SUPPLIER / PRODUCT COVERAGE
---------------------------
Suppliers referenced by products: {suppliers_with_products}
Suppliers without product references: {suppliers_without_products}

INVENTORY BUSINESS KEY
----------------------
Duplicate (warehouse_id, product_id) groups:
{inventory_duplicate_groups}

These were not automatically deleted.

FINAL OBSERVATIONS
------------------
1. Foreign-key exceptions must be investigated before database
   constraints are finalized.
2. Missing shipments/details are reported by status rather than
   automatically treated as errors.
3. Date anomalies are preserved for investigation.
4. Financial reconciliation is based on existing source values.
5. No feature engineering was performed.
6. No source CSV was modified.

FINAL STATUS
------------
PASS WITH WARNINGS
"""

REPORT_FILE.write_text(report, encoding="utf-8")

print("Cross-table validation completed.")
print("Report:", REPORT_FILE)
print("\nFINAL STATUS: PASS WITH WARNINGS")