from pathlib import Path
import pandas as pd
import numpy as np


# ============================================================
# SUPPLY CHAIN INTELLIGENCE
# BUSINESS FEATURE ENGINEERING
# ============================================================
#
# Purpose:
# Build reusable business-level metrics from the completed
# analytical Fact and Dimension tables.
#
# Design:
# - Keep one central feature-engineering script.
# - Preserve correct business grain.
# - Reuse analytical attributes already present in dimensions.
# - Add only meaningful business-performance features.
# - Do not invent missing source values.
#
# Outputs:
#   order_features.csv
#   customer_features.csv
#   product_features.csv
#   supplier_features.csv
#   warehouse_features.csv
#   carrier_features.csv
#   business_daily_metrics.csv
#
# ============================================================


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(r"C:\supply_chain_intelligence")

ANALYTICAL_DIR = BASE_DIR / "data" / "analytical"
OUTPUT_DIR = ANALYTICAL_DIR / "business_features"
REPORT_DIR = BASE_DIR / "reports"

# ------------------------------------------------------------
# Analytical source tables
# ------------------------------------------------------------

ORDER_ITEMS_FILE = ANALYTICAL_DIR / "fact_order_items.csv"
ORDERS_FILE = ANALYTICAL_DIR / "fact_orders.csv"
SHIPMENTS_FILE = ANALYTICAL_DIR / "fact_shipments.csv"
INVENTORY_FILE = ANALYTICAL_DIR / "fact_inventory.csv"

CUSTOMER_FILE = ANALYTICAL_DIR / "dim_customer.csv"
PRODUCT_FILE = ANALYTICAL_DIR / "dim_product.csv"
SUPPLIER_FILE = ANALYTICAL_DIR / "dim_supplier.csv"
WAREHOUSE_FILE = ANALYTICAL_DIR / "dim_warehouse.csv"

# ------------------------------------------------------------
# Output tables
# ------------------------------------------------------------

ORDER_OUTPUT = OUTPUT_DIR / "order_features.csv"
CUSTOMER_OUTPUT = OUTPUT_DIR / "customer_features.csv"
PRODUCT_OUTPUT = OUTPUT_DIR / "product_features.csv"
SUPPLIER_OUTPUT = OUTPUT_DIR / "supplier_features.csv"
WAREHOUSE_OUTPUT = OUTPUT_DIR / "warehouse_features.csv"
CARRIER_OUTPUT = OUTPUT_DIR / "carrier_features.csv"
DAILY_OUTPUT = OUTPUT_DIR / "business_daily_metrics.csv"

REPORT_FILE = REPORT_DIR / "business_features_report.txt"


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def convert_numeric(df, columns):
    """
    Convert available columns to numeric.
    Invalid values become NaN.
    """

    for column in columns:
        if column in df.columns:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )


def convert_dates(df, columns):
    """
    Convert available columns to datetime.
    Invalid values become NaT.
    """

    for column in columns:
        if column in df.columns:
            df[column] = pd.to_datetime(
                df[column],
                errors="coerce"
            )


def safe_divide(numerator, denominator):
    """
    Division that returns NaN where denominator is zero.
    """

    return np.where(
        denominator != 0,
        numerator / denominator,
        np.nan
    )


def standardize_transaction_type(df):
    """
    Normalize transaction_type text before business logic.

    Important actual source values:
        Sale
        Return / Reversal
    """

    if "transaction_type" in df.columns:

        df["transaction_type"] = (
            df["transaction_type"]
            .astype("string")
            .str.strip()
        )

    return df


# ============================================================
# LOAD DATA
# ============================================================

def load_data():

    order_items = pd.read_csv(
        ORDER_ITEMS_FILE
    )

    orders = pd.read_csv(
        ORDERS_FILE
    )

    shipments = pd.read_csv(
        SHIPMENTS_FILE
    )

    inventory = pd.read_csv(
        INVENTORY_FILE
    )

    customers = pd.read_csv(
        CUSTOMER_FILE
    )

    products = pd.read_csv(
        PRODUCT_FILE
    )

    suppliers = pd.read_csv(
        SUPPLIER_FILE
    )

    warehouses = pd.read_csv(
        WAREHOUSE_FILE
    )

    return (
        order_items,
        orders,
        shipments,
        inventory,
        customers,
        products,
        suppliers,
        warehouses
    )


# ============================================================
# PREPARE DATA
# ============================================================

def prepare_data(
    order_items,
    orders,
    shipments,
    inventory,
    customers,
    products,
    suppliers,
    warehouses
):

    # --------------------------------------------------------
    # Order Items
    # --------------------------------------------------------

    convert_numeric(
        order_items,
        [
            "order_id",
            "product_id",
            "quantity",
            "discount_pct",
            "source_line_total",
            "gross_line_amount",
            "discount_amount",
            "net_line_amount"
        ]
    )

    # --------------------------------------------------------
    # Orders
    # --------------------------------------------------------

    convert_numeric(
        orders,
        [
            "order_id",
            "customer_id",
            "warehouse_id",
            "source_order_total",
            "detail_row_count",
            "total_quantity",
            "calculated_order_total",
            "shipment_count"
        ]
    )

    # --------------------------------------------------------
    # Shipments
    # --------------------------------------------------------

    convert_numeric(
        shipments,
        [
            "shipment_id",
            "order_id",
            "shipping_cost",
            "distance_km"
        ]
    )

    # --------------------------------------------------------
    # Inventory
    # --------------------------------------------------------

    convert_numeric(
        inventory,
        [
            "inventory_id",
            "warehouse_id",
            "product_id",
            "stock_quantity",
            "reorder_level",
            "unit_price"
        ]
    )

    # --------------------------------------------------------
    # Customers
    # --------------------------------------------------------

    convert_numeric(
        customers,
        [
            "customer_id",
            "order_count"
        ]
    )

    # --------------------------------------------------------
    # Products
    # --------------------------------------------------------

    convert_numeric(
        products,
        [
            "product_id",
            "supplier_id",
            "unit_price",
            "weight_kg"
        ]
    )

    # --------------------------------------------------------
    # Suppliers
    # --------------------------------------------------------

    convert_numeric(
        suppliers,
        [
            "supplier_id",
            "rating"
        ]
    )

    # --------------------------------------------------------
    # Warehouses
    # --------------------------------------------------------

    convert_numeric(
        warehouses,
        [
            "warehouse_id",
            "capacity_units"
        ]
    )

    # --------------------------------------------------------
    # Dates
    # --------------------------------------------------------

    convert_dates(
        order_items,
        ["order_date"]
    )

    convert_dates(
        orders,
        [
            "order_date",
            "ship_date"
        ]
    )

    convert_dates(
        shipments,
        [
            "shipment_date",
            "delivery_date"
        ]
    )

    convert_dates(
        inventory,
        [
            "last_restock_date"
        ]
    )

    convert_dates(
        customers,
        [
            "signup_date",
            "first_order_date",
            "last_order_date"
        ]
    )

    # --------------------------------------------------------
    # Transaction type cleanup
    # --------------------------------------------------------

    order_items = standardize_transaction_type(
        order_items
    )

    return (
        order_items,
        orders,
        shipments,
        inventory,
        customers,
        products,
        suppliers,
        warehouses
    )


# ============================================================
# ORDER FEATURES
# Grain: 1 row = 1 order
# ============================================================

def build_order_features(
    orders,
    order_items,
    shipments
):

    result = orders.copy()

    items = order_items.copy()

    # --------------------------------------------------------
    # IMPORTANT:
    # Actual transaction value is "Return / Reversal"
    # --------------------------------------------------------

    items["is_sale"] = (
        items["transaction_type"] == "Sale"
    )

    items["is_return"] = (
        items["transaction_type"]
        == "Return / Reversal"
    )

    # --------------------------------------------------------
    # SALES METRICS
    # --------------------------------------------------------

    sales = (
        items[items["is_sale"]]
        .groupby("order_id")
        .agg(
            gross_sales=(
                "gross_line_amount",
                "sum"
            ),
            discount_amount=(
                "discount_amount",
                "sum"
            ),
            sales_net=(
                "net_line_amount",
                "sum"
            ),
            units_sold=(
                "quantity",
                "sum"
            ),
            sale_line_count=(
                "order_detail_id",
                "nunique"
            )
        )
        .reset_index()
    )

    # --------------------------------------------------------
    # RETURN METRICS
    # --------------------------------------------------------

    returns = (
        items[items["is_return"]]
        .groupby("order_id")
        .agg(
            return_amount=(
                "net_line_amount",
                "sum"
            ),
            units_returned=(
                "quantity",
                "sum"
            ),
            return_line_count=(
                "order_detail_id",
                "nunique"
            )
        )
        .reset_index()
    )

    # --------------------------------------------------------
    # Merge sales
    # --------------------------------------------------------

    result = result.merge(
        sales,
        on="order_id",
        how="left",
        validate="one_to_one"
    )

    # --------------------------------------------------------
    # Merge returns
    # --------------------------------------------------------

    result = result.merge(
        returns,
        on="order_id",
        how="left",
        validate="one_to_one"
    )

    # --------------------------------------------------------
    # Fill derived sales metrics
    # --------------------------------------------------------

    for column in [
        "gross_sales",
        "discount_amount",
        "sales_net",
        "units_sold",
        "sale_line_count",
        "return_line_count"
    ]:

        result[column] = (
            result[column]
            .fillna(0)
        )

    # --------------------------------------------------------
    # Return amounts are stored as negative values.
    # Convert to positive magnitude for reporting.
    # --------------------------------------------------------

    result["return_amount"] = (
        result["return_amount"]
        .fillna(0)
        .abs()
    )

    result["units_returned"] = (
        result["units_returned"]
        .fillna(0)
        .abs()
    )

    # --------------------------------------------------------
    # NET SALES
    # --------------------------------------------------------

    result["net_sales"] = (
        result["sales_net"]
        - result["return_amount"]
    )

    # --------------------------------------------------------
    # NET UNITS
    # --------------------------------------------------------

    result["net_units"] = (
        result["units_sold"]
        - result["units_returned"]
    )

    # --------------------------------------------------------
    # DISCOUNT RATE
    # --------------------------------------------------------

    result["discount_rate"] = safe_divide(
        result["discount_amount"],
        result["gross_sales"]
    )

    # --------------------------------------------------------
    # RETURN RATE
    # --------------------------------------------------------

    result["return_rate"] = safe_divide(
        result["units_returned"],
        result["units_sold"]
    )

    # --------------------------------------------------------
    # REVENUE COMPLETENESS
    # --------------------------------------------------------

    item_quality = (
        items
        .groupby("order_id")
        .agg(
            item_line_count=(
                "order_detail_id",
                "nunique"
            ),
            missing_net_amount_lines=(
                "net_line_amount",
                lambda x: x.isna().sum()
            )
        )
        .reset_index()
    )

    result = result.merge(
        item_quality,
        on="order_id",
        how="left",
        validate="one_to_one"
    )

    result["revenue_completeness_status"] = (
        "No Order Details"
    )

    has_details = (
        result["item_line_count"]
        .fillna(0)
        > 0
    )

    complete = (
        has_details
        & (
            result["missing_net_amount_lines"]
            .fillna(0)
            == 0
        )
    )

    partial = (
        has_details
        & (
            result["missing_net_amount_lines"]
            .fillna(0)
            > 0
        )
    )

    result.loc[
        complete,
        "revenue_completeness_status"
    ] = "Complete"

    result.loc[
        partial,
        "revenue_completeness_status"
    ] = "Partial"

    # --------------------------------------------------------
    # SHIPMENT METRICS
    # --------------------------------------------------------

    shipment_summary = (
        shipments
        .groupby("order_id")
        .agg(
            feature_shipment_count=(
                "shipment_id",
                "nunique"
            ),
            total_shipping_cost=(
                "shipping_cost",
                "sum"
            ),
            first_shipment_date=(
                "shipment_date",
                "min"
            ),
            last_delivery_date=(
                "delivery_date",
                "max"
            )
        )
        .reset_index()
    )

    result = result.merge(
        shipment_summary,
        on="order_id",
        how="left",
        validate="one_to_one"
    )

    result["feature_shipment_count"] = (
        result["feature_shipment_count"]
        .fillna(0)
        .astype(int)
    )

    result["has_shipment"] = (
        result["feature_shipment_count"] > 0
    )

    # --------------------------------------------------------
    # Order → Delivery
    # --------------------------------------------------------

    result["order_to_delivery_days"] = (
        result["last_delivery_date"]
        - result["order_date"]
    ).dt.days

    result["delivery_anomaly_flag"] = (
        result["order_to_delivery_days"] < 0
    )

    # One row = one order
    result["average_order_value"] = (
        result["net_sales"]
    )

    return result


# ============================================================
# CUSTOMER FEATURES
# Grain: 1 row = 1 customer
# ============================================================

def build_customer_features(
    customers,
    order_features
):

    # --------------------------------------------------------
    # dim_customer already contains:
    #
    # order_count
    # first_order_date
    # last_order_date
    # has_orders
    # signup_to_first_order_days
    # signup_order_date_status
    #
    # We reuse those columns.
    # --------------------------------------------------------

    result = customers.copy()

    metrics = (
        order_features
        .dropna(subset=["customer_id"])
        .groupby("customer_id")
        .agg(
            gross_sales=(
                "gross_sales",
                "sum"
            ),
            discount_amount=(
                "discount_amount",
                "sum"
            ),
            net_sales=(
                "net_sales",
                "sum"
            ),
            units_sold=(
                "units_sold",
                "sum"
            ),
            units_returned=(
                "units_returned",
                "sum"
            ),
            return_amount=(
                "return_amount",
                "sum"
            )
        )
        .reset_index()
    )

    result = result.merge(
        metrics,
        on="customer_id",
        how="left",
        validate="one_to_one"
    )

    # --------------------------------------------------------
    # Fill only newly generated metrics
    # --------------------------------------------------------

    for column in [
        "gross_sales",
        "discount_amount",
        "net_sales",
        "units_sold",
        "units_returned",
        "return_amount"
    ]:

        result[column] = (
            result[column]
            .fillna(0)
        )

    # --------------------------------------------------------
    # CUSTOMER BEHAVIOUR
    # --------------------------------------------------------

    result["repeat_customer_flag"] = (
        result["order_count"] > 1
    )

    result["average_order_value"] = safe_divide(
        result["net_sales"],
        result["order_count"]
    )

    result["return_rate"] = safe_divide(
        result["units_returned"],
        result["units_sold"]
    )

    result["discount_rate"] = safe_divide(
        result["discount_amount"],
        result["gross_sales"]
    )

    # --------------------------------------------------------
    # ANALYSIS DATE
    # --------------------------------------------------------

    analysis_date = (
        order_features["order_date"]
        .max()
    )

    result["days_since_last_order"] = (
        analysis_date
        - result["last_order_date"]
    ).dt.days

    result["customer_lifetime_days"] = (
        result["last_order_date"]
        - result["first_order_date"]
    ).dt.days

    result["analysis_date"] = analysis_date

    return result


# ============================================================
# PRODUCT FEATURES
# Grain: 1 row = 1 product
# ============================================================

def build_product_features(
    products,
    order_items,
    inventory
):

    # --------------------------------------------------------
    # dim_product already has:
    #
    # inventory_record_count
    # has_inventory
    # supplier_status
    # supplier_name
    # country
    # rating
    #
    # Do not rebuild those.
    # --------------------------------------------------------

    result = products.copy()

    items = order_items.copy()

    items["is_sale"] = (
        items["transaction_type"]
        == "Sale"
    )

    items["is_return"] = (
        items["transaction_type"]
        == "Return / Reversal"
    )

    # --------------------------------------------------------
    # SALES
    # --------------------------------------------------------

    sales = (
        items[items["is_sale"]]
        .groupby("product_id")
        .agg(
            units_sold=(
                "quantity",
                "sum"
            ),
            gross_sales=(
                "gross_line_amount",
                "sum"
            ),
            discount_amount=(
                "discount_amount",
                "sum"
            ),
            sales_net=(
                "net_line_amount",
                "sum"
            )
        )
        .reset_index()
    )

    # --------------------------------------------------------
    # RETURNS
    # --------------------------------------------------------

    returns = (
        items[items["is_return"]]
        .groupby("product_id")
        .agg(
            units_returned=(
                "quantity",
                "sum"
            ),
            return_amount=(
                "net_line_amount",
                "sum"
            ),
            return_count=(
                "order_detail_id",
                "nunique"
            )
        )
        .reset_index()
    )

    result = result.merge(
        sales,
        on="product_id",
        how="left",
        validate="one_to_one"
    )

    result = result.merge(
        returns,
        on="product_id",
        how="left",
        validate="one_to_one"
    )

    # --------------------------------------------------------
    # INVENTORY
    # --------------------------------------------------------

    inventory_summary = (
        inventory
        .groupby("product_id")
        .agg(
            current_stock=(
                "stock_quantity",
                "sum"
            ),
            reorder_level_total=(
                "reorder_level",
                "sum"
            ),
            low_stock_records=(
                "stock_status",
                lambda x:
                (
                    x == "Below Reorder Level"
                ).sum()
            )
        )
        .reset_index()
    )

    result = result.merge(
        inventory_summary,
        on="product_id",
        how="left",
        validate="one_to_one"
    )

    # --------------------------------------------------------
    # Fill new metrics
    # --------------------------------------------------------

    for column in [
        "units_sold",
        "gross_sales",
        "discount_amount",
        "sales_net",
        "units_returned",
        "return_count",
        "current_stock",
        "reorder_level_total",
        "low_stock_records"
    ]:

        result[column] = (
            result[column]
            .fillna(0)
        )

    result["return_amount"] = (
        result["return_amount"]
        .fillna(0)
        .abs()
    )

    result["units_returned"] = (
        result["units_returned"]
        .abs()
    )

    # --------------------------------------------------------
    # MAIN PRODUCT BUSINESS METRICS
    # --------------------------------------------------------

    result["net_sales"] = (
        result["sales_net"]
        - result["return_amount"]
    )

    result["net_units"] = (
        result["units_sold"]
        - result["units_returned"]
    )

    result["discount_rate"] = safe_divide(
        result["discount_amount"],
        result["gross_sales"]
    )

    result["return_rate"] = safe_divide(
        result["units_returned"],
        result["units_sold"]
    )

    # --------------------------------------------------------
    # INVENTORY PRESSURE
    # --------------------------------------------------------

    result["reorder_gap_units"] = (
        result["current_stock"]
        - result["reorder_level_total"]
    )

    result["stock_to_reorder_ratio"] = safe_divide(
        result["current_stock"],
        result["reorder_level_total"]
    )

    result["below_reorder_flag"] = (
        result["low_stock_records"] > 0
    )

    # --------------------------------------------------------
    # REVENUE SHARE
    # --------------------------------------------------------

    total_sales = (
        result["net_sales"].sum()
    )

    result["revenue_share"] = safe_divide(
        result["net_sales"],
        total_sales
    )

    return result


# ============================================================
# SUPPLIER FEATURES
# Grain: 1 row = 1 supplier
# ============================================================

def build_supplier_features(
    suppliers,
    product_features
):

    # --------------------------------------------------------
    # dim_supplier already has:
    #
    # product_count
    # has_products
    #
    # Reuse them.
    # --------------------------------------------------------

    result = suppliers.copy()

    metrics = (
        product_features
        .dropna(subset=["supplier_id"])
        .groupby("supplier_id")
        .agg(
            net_sales=(
                "net_sales",
                "sum"
            ),
            units_sold=(
                "units_sold",
                "sum"
            ),
            units_returned=(
                "units_returned",
                "sum"
            ),
            return_amount=(
                "return_amount",
                "sum"
            ),
            low_stock_products=(
                "below_reorder_flag",
                "sum"
            ),
            current_stock=(
                "current_stock",
                "sum"
            )
        )
        .reset_index()
    )

    result = result.merge(
        metrics,
        on="supplier_id",
        how="left",
        validate="one_to_one"
    )

    # --------------------------------------------------------
    # Fill new supplier performance metrics
    # --------------------------------------------------------

    for column in [
        "net_sales",
        "units_sold",
        "units_returned",
        "return_amount",
        "low_stock_products",
        "current_stock"
    ]:

        result[column] = (
            result[column]
            .fillna(0)
        )

    result["units_returned"] = (
        result["units_returned"]
        .abs()
    )

    result["return_amount"] = (
        result["return_amount"]
        .abs()
    )

    # --------------------------------------------------------
    # RETURN RATE
    # --------------------------------------------------------

    result["return_rate"] = safe_divide(
        result["units_returned"],
        result["units_sold"]
    )

    # --------------------------------------------------------
    # REVENUE SHARE
    # --------------------------------------------------------

    total_sales = (
        result["net_sales"].sum()
    )

    result["revenue_share"] = safe_divide(
        result["net_sales"],
        total_sales
    )

    return result


# ============================================================
# WAREHOUSE FEATURES
# Grain: 1 row = 1 warehouse
# ============================================================

def build_warehouse_features(
    warehouses,
    inventory,
    order_features
):

    # --------------------------------------------------------
    # dim_warehouse already contains:
    #
    # inventory_record_count
    # product_count
    # has_inventory
    #
    # Reuse them.
    # --------------------------------------------------------

    result = warehouses.copy()

    # --------------------------------------------------------
    # INVENTORY METRICS
    # --------------------------------------------------------

    inventory_metrics = (
        inventory
        .groupby("warehouse_id")
        .agg(
            total_stock=(
                "stock_quantity",
                "sum"
            ),
            low_stock_items=(
                "stock_status",
                lambda x:
                (
                    x == "Below Reorder Level"
                ).sum()
            ),
            missing_stock_items=(
                "stock_quantity",
                lambda x: x.isna().sum()
            )
        )
        .reset_index()
    )

    # --------------------------------------------------------
    # ORDER METRICS
    # --------------------------------------------------------

    order_metrics = (
        order_features
        .dropna(subset=["warehouse_id"])
        .groupby("warehouse_id")
        .agg(
            order_count=(
                "order_id",
                "nunique"
            ),
            net_sales=(
                "net_sales",
                "sum"
            ),
            return_amount=(
                "return_amount",
                "sum"
            ),
            units_sold=(
                "units_sold",
                "sum"
            ),
            units_returned=(
                "units_returned",
                "sum"
            )
        )
        .reset_index()
    )

    result = result.merge(
        inventory_metrics,
        on="warehouse_id",
        how="left",
        validate="one_to_one"
    )

    result = result.merge(
        order_metrics,
        on="warehouse_id",
        how="left",
        validate="one_to_one"
    )

    # --------------------------------------------------------
    # Fill derived metrics
    # --------------------------------------------------------

    for column in [
        "total_stock",
        "low_stock_items",
        "missing_stock_items",
        "order_count",
        "net_sales",
        "return_amount",
        "units_sold",
        "units_returned"
    ]:

        result[column] = (
            result[column]
            .fillna(0)
        )

    result["units_returned"] = (
        result["units_returned"]
        .abs()
    )

    result["return_amount"] = (
        result["return_amount"]
        .abs()
    )

    # --------------------------------------------------------
    # STOCK SHARE
    # --------------------------------------------------------

    total_stock = (
        result["total_stock"].sum()
    )

    result["stock_share"] = safe_divide(
        result["total_stock"],
        total_stock
    )

    # --------------------------------------------------------
    # SALES SHARE
    # --------------------------------------------------------

    total_sales = (
        result["net_sales"].sum()
    )

    result["sales_share"] = safe_divide(
        result["net_sales"],
        total_sales
    )

    # --------------------------------------------------------
    # RETURN RATE
    # --------------------------------------------------------

    result["return_rate"] = safe_divide(
        result["units_returned"],
        result["units_sold"]
    )

    return result


# ============================================================
# CARRIER FEATURES
# Grain: 1 row = 1 carrier
# ============================================================

def build_carrier_features(shipments):

    data = shipments.copy()

    # --------------------------------------------------------
    # DELIVERY DAYS
    # --------------------------------------------------------

    data["delivery_days"] = (
        data["delivery_date"]
        - data["shipment_date"]
    ).dt.days

    # --------------------------------------------------------
    # VALID DELIVERY
    # --------------------------------------------------------

    data["valid_delivery_flag"] = (
        data["shipment_date"].notna()
        & data["delivery_date"].notna()
        & (data["delivery_days"] >= 0)
    )

    # --------------------------------------------------------
    # CARRIER AGGREGATION
    # --------------------------------------------------------

    result = (
        data
        .groupby("carrier")
        .agg(
            shipment_count=(
                "shipment_id",
                "nunique"
            ),
            total_shipping_cost=(
                "shipping_cost",
                "sum"
            ),
            average_shipping_cost=(
                "shipping_cost",
                "mean"
            ),
            total_distance_km=(
                "distance_km",
                "sum"
            ),
            average_distance_km=(
                "distance_km",
                "mean"
            ),
            average_delivery_days=(
                "delivery_days",
                lambda x:
                x[x >= 0].mean()
            ),
            valid_delivery_count=(
                "valid_delivery_flag",
                "sum"
            ),
            delivery_anomaly_count=(
                "delivery_days",
                lambda x:
                (x < 0).sum()
            )
        )
        .reset_index()
    )

    # --------------------------------------------------------
    # COST PER KM
    # --------------------------------------------------------

    result["shipping_cost_per_km"] = safe_divide(
        result["total_shipping_cost"],
        result["total_distance_km"]
    )

    # --------------------------------------------------------
    # DELIVERY COVERAGE
    # --------------------------------------------------------

    result["delivery_coverage_rate"] = safe_divide(
        result["valid_delivery_count"],
        result["shipment_count"]
    )

    return result


# ============================================================
# DAILY BUSINESS METRICS
# Grain: 1 row = 1 date
# ============================================================

def build_daily_metrics(
    order_features,
    shipments
):

    # --------------------------------------------------------
    # ORDER METRICS BY ORDER DATE
    # --------------------------------------------------------

    orders_daily = (
        order_features
        .dropna(subset=["order_date"])
        .groupby("order_date")
        .agg(
            orders=(
                "order_id",
                "nunique"
            ),
            customers=(
                "customer_id",
                "nunique"
            ),
            gross_sales=(
                "gross_sales",
                "sum"
            ),
            discount_amount=(
                "discount_amount",
                "sum"
            ),
            net_sales=(
                "net_sales",
                "sum"
            ),
            return_amount=(
                "return_amount",
                "sum"
            ),
            units_sold=(
                "units_sold",
                "sum"
            ),
            units_returned=(
                "units_returned",
                "sum"
            )
        )
        .reset_index()
    )

    # --------------------------------------------------------
    # SHIPMENTS BY SHIPMENT DATE
    # --------------------------------------------------------

    shipments_daily = (
        shipments
        .dropna(subset=["shipment_date"])
        .groupby("shipment_date")
        .agg(
            shipments=(
                "shipment_id",
                "nunique"
            ),
            shipping_cost=(
                "shipping_cost",
                "sum"
            )
        )
        .reset_index()
        .rename(
            columns={
                "shipment_date": "order_date"
            }
        )
    )

    # --------------------------------------------------------
    # COMBINE DAILY METRICS
    # --------------------------------------------------------

    result = orders_daily.merge(
        shipments_daily,
        on="order_date",
        how="outer"
    )

    result = result.sort_values(
        "order_date"
    )

    # --------------------------------------------------------
    # Fill additive metrics
    # --------------------------------------------------------

    for column in [
        "orders",
        "customers",
        "gross_sales",
        "discount_amount",
        "net_sales",
        "return_amount",
        "units_sold",
        "units_returned",
        "shipments",
        "shipping_cost"
    ]:

        result[column] = (
            result[column]
            .fillna(0)
        )

    # --------------------------------------------------------
    # DAILY DERIVED METRICS
    # --------------------------------------------------------

    result["net_units"] = (
        result["units_sold"]
        - result["units_returned"]
    )

    result["discount_rate"] = safe_divide(
        result["discount_amount"],
        result["gross_sales"]
    )

    result["return_rate"] = safe_divide(
        result["units_returned"],
        result["units_sold"]
    )

    result["average_order_value"] = safe_divide(
        result["net_sales"],
        result["orders"]
    )

    return result


# ============================================================
# REPORT
# ============================================================

def create_report(
    order_features,
    customer_features,
    product_features,
    supplier_features,
    warehouse_features,
    carrier_features,
    daily_metrics
):

    # --------------------------------------------------------
    # EXECUTIVE TOTALS
    # --------------------------------------------------------

    total_gross_sales = (
        order_features["gross_sales"].sum()
    )

    total_discount = (
        order_features["discount_amount"].sum()
    )

    total_sales_net = (
        order_features["sales_net"].sum()
    )

    total_return_amount = (
        order_features["return_amount"].sum()
    )

    total_net_sales = (
        order_features["net_sales"].sum()
    )

    total_units_sold = (
        order_features["units_sold"].sum()
    )

    total_units_returned = (
        order_features["units_returned"].sum()
    )

    discount_rate = (
        total_discount / total_gross_sales
        if total_gross_sales != 0
        else np.nan
    )

    return_rate = (
        total_units_returned / total_units_sold
        if total_units_sold != 0
        else np.nan
    )

    order_count = (
        order_features["order_id"]
        .nunique()
    )

    average_order_value = (
        total_net_sales / order_count
        if order_count != 0
        else np.nan
    )

    # --------------------------------------------------------
    # REVENUE COMPLETENESS
    # --------------------------------------------------------

    complete_orders = (
        order_features[
            "revenue_completeness_status"
        ] == "Complete"
    ).sum()

    partial_orders = (
        order_features[
            "revenue_completeness_status"
        ] == "Partial"
    ).sum()

    no_detail_orders = (
        order_features[
            "revenue_completeness_status"
        ] == "No Order Details"
    ).sum()

    # --------------------------------------------------------
    # REPORT
    # --------------------------------------------------------

    report = f"""
SUPPLY CHAIN INTELLIGENCE
BUSINESS FEATURE ENGINEERING REPORT
===================================


OUTPUTS
-------
order_features.csv
customer_features.csv
product_features.csv
supplier_features.csv
warehouse_features.csv
carrier_features.csv
business_daily_metrics.csv


GRAIN
-----
order_features          = 1 row per order
customer_features       = 1 row per customer
product_features        = 1 row per product
supplier_features       = 1 row per supplier
warehouse_features      = 1 row per warehouse
carrier_features        = 1 row per carrier
business_daily_metrics  = 1 row per date


ROW COUNTS
----------
Order features:
{len(order_features)}

Customer features:
{len(customer_features)}

Product features:
{len(product_features)}

Supplier features:
{len(supplier_features)}

Warehouse features:
{len(warehouse_features)}

Carrier features:
{len(carrier_features)}

Daily metrics:
{len(daily_metrics)}


EXECUTIVE COMMERCIAL METRICS
----------------------------
Gross Sales:
{total_gross_sales:,.2f}

Discount Amount:
{total_discount:,.2f}

Sales Net Before Returns:
{total_sales_net:,.2f}

Return Amount:
{total_return_amount:,.2f}

Net Sales:
{total_net_sales:,.2f}

Units Sold:
{total_units_sold:,.0f}

Units Returned:
{total_units_returned:,.0f}

Discount Rate:
{discount_rate:.4%}

Return Rate:
{return_rate:.4%}

Average Order Value:
{average_order_value:,.2f}


CUSTOMER
--------
Customer count:
{len(customer_features)}

Customers with orders:
{customer_features["order_count"].gt(0).sum()}

Repeat customers:
{customer_features["repeat_customer_flag"].sum()}

Customers without orders:
{customer_features["order_count"].eq(0).sum()}


PRODUCT
-------
Product count:
{len(product_features)}

Products with sales:
{product_features["units_sold"].gt(0).sum()}

Products below reorder:
{product_features["below_reorder_flag"].sum()}

Products with inventory:
{product_features["inventory_record_count"].gt(0).sum()}


SUPPLIER
--------
Supplier count:
{len(supplier_features)}

Suppliers with products:
{supplier_features["has_products"].sum()}

Suppliers without products:
{supplier_features["has_products"].eq(False).sum()}


WAREHOUSE
---------
Warehouse count:
{len(warehouse_features)}

Total stock:
{warehouse_features["total_stock"].sum():,.0f}

Low-stock items:
{warehouse_features["low_stock_items"].sum():,.0f}


CARRIER
-------
Carrier count:
{len(carrier_features)}

Total shipping cost:
{carrier_features["total_shipping_cost"].sum():,.2f}


ORDER REVENUE COMPLETENESS
--------------------------
Complete orders:
{complete_orders}

Partial orders:
{partial_orders}

Orders without details:
{no_detail_orders}


DELIVERY DATA
-------------
Orders with shipment:
{order_features["has_shipment"].sum()}

Orders without shipment:
{order_features["has_shipment"].eq(False).sum()}

Delivery anomaly orders:
{order_features["delivery_anomaly_flag"].sum()}


BUSINESS DEFINITIONS
--------------------

Gross Sales
-----------
Sum of gross line amounts for Sale transactions.

Discount Amount
---------------
Sum of discount amounts for Sale transactions.

Sales Net Before Returns
------------------------
Sales revenue after discounts but before return/reversal transactions.

Return Amount
-------------
Absolute monetary magnitude of Return / Reversal transactions.

Net Sales
---------
Sales Net Before Returns minus Return Amount.

Discount Rate
-------------
Discount Amount divided by Gross Sales.

Return Rate
-----------
Returned units divided by sold units.

Average Order Value
-------------------
Net Sales divided by order count.

Repeat Customer
---------------
Customer with more than one order.

Reorder Gap Units
-----------------
Current Stock minus Total Reorder Level.

Stock-to-Reorder Ratio
----------------------
Current Stock divided by Total Reorder Level.

Shipping Cost per KM
--------------------
Total Shipping Cost divided by Total Distance KM.

Revenue Completeness
--------------------
Classifies orders as Complete, Partial or No Order Details
based on line-level net amount availability.


IMPORTANT DATA RULES
--------------------
Return / Reversal is treated separately from Sale.

Negative return quantities and amounts are converted to positive
magnitudes for return reporting while preserving the meaning of
the source transaction.

No source records were intentionally deleted.

No missing source values were replaced with invented values.

Existing dimension attributes were reused instead of unnecessarily
rebuilding identical fields.

No arbitrary customer/product/supplier/warehouse scores were created.

Inventory value was not calculated because unit_price is not a
verified inventory-cost field.

Warehouse utilization was not calculated because stock units and
capacity units have not been established as physically equivalent.

Advanced analyses will be created later from the reusable feature layer.


FINAL STATUS
------------
PASS
"""

    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    REPORT_FILE.write_text(
        report.strip(),
        encoding="utf-8"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------------
    # Load
    # --------------------------------------------------------

    (
        order_items,
        orders,
        shipments,
        inventory,
        customers,
        products,
        suppliers,
        warehouses
    ) = load_data()

    print(f"Order Items: {order_items.shape}")
    print(f"Orders: {orders.shape}")
    print(f"Shipments: {shipments.shape}")
    print(f"Inventory: {inventory.shape}")
    print(f"Customers: {customers.shape}")
    print(f"Products: {products.shape}")
    print(f"Suppliers: {suppliers.shape}")
    print(f"Warehouses: {warehouses.shape}")

    # --------------------------------------------------------
    # Prepare
    # --------------------------------------------------------

    (
        order_items,
        orders,
        shipments,
        inventory,
        customers,
        products,
        suppliers,
        warehouses
    ) = prepare_data(
        order_items,
        orders,
        shipments,
        inventory,
        customers,
        products,
        suppliers,
        warehouses
    )

    # --------------------------------------------------------
    # Feature engineering
    # --------------------------------------------------------

    print("\nBuilding order features...")

    order_features = build_order_features(
        orders,
        order_items,
        shipments
    )

    print("Building customer features...")

    customer_features = build_customer_features(
        customers,
        order_features
    )

    print("Building product features...")

    product_features = build_product_features(
        products,
        order_items,
        inventory
    )

    print("Building supplier features...")

    supplier_features = build_supplier_features(
        suppliers,
        product_features
    )

    print("Building warehouse features...")

    warehouse_features = build_warehouse_features(
        warehouses,
        inventory,
        order_features
    )

    print("Building carrier features...")

    carrier_features = build_carrier_features(
        shipments
    )

    print("Building daily business metrics...")

    daily_metrics = build_daily_metrics(
        order_features,
        shipments
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    outputs = {
        ORDER_OUTPUT: order_features,
        CUSTOMER_OUTPUT: customer_features,
        PRODUCT_OUTPUT: product_features,
        SUPPLIER_OUTPUT: supplier_features,
        WAREHOUSE_OUTPUT: warehouse_features,
        CARRIER_OUTPUT: carrier_features,
        DAILY_OUTPUT: daily_metrics
    }

    for output_file, dataframe in outputs.items():

        dataframe.to_csv(
            output_file,
            index=False
        )

        print(
            f"Created: {output_file.name} "
            f"| Rows: {len(dataframe)} "
            f"| Columns: {len(dataframe.columns)}"
        )

    # --------------------------------------------------------
    # Report
    # --------------------------------------------------------

    create_report(
        order_features,
        customer_features,
        product_features,
        supplier_features,
        warehouse_features,
        carrier_features,
        daily_metrics
    )

    print(
        "\nBUSINESS FEATURE ENGINEERING COMPLETED."
    )

    print(
        f"Output folder: {OUTPUT_DIR}"
    )

    print(
        f"Report: {REPORT_FILE}"
    )

    print(
        "Final status: PASS"
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()