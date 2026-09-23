from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text


# ============================================================
# SUPPLY CHAIN INTELLIGENCE
# V2 DATABASE BUILDER
#
# Purpose:
# Analytical CSVs
#       ↓
# SQLite database
#       ↓
# Business SQL views
#       ↓
# Streamlit dashboard
#
# The database is only responsible for:
# 1. Loading analytical tables
# 2. Creating useful indexes
# 3. Creating business-question views
# 4. Validating the database
# ============================================================


# ============================================================
# PROJECT PATHS
# ============================================================

# File is:
# C:\supply_chain_intelligence\src\database\load_database.py
#
# parents[0] = database
# parents[1] = src
# parents[2] = supply_chain_intelligence

BASE_DIR = Path(__file__).resolve().parents[2]

ANALYTICAL_DIR = BASE_DIR / "data" / "analytical"
DATABASE_DIR = BASE_DIR / "database"
DB_FILE = DATABASE_DIR / "supply_chain_intelligence.db"

DATABASE_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# ANALYTICAL TABLES
# ============================================================

FILES = {
    # Dimensions
    "dim_customer": "dim_customer.csv",
    "dim_date": "dim_date.csv",
    "dim_product": "dim_product.csv",
    "dim_supplier": "dim_supplier.csv",
    "dim_warehouse": "dim_warehouse.csv",

    # Facts
    "fact_inventory": "fact_inventory.csv",
    "fact_orders": "fact_orders.csv",
    "fact_order_items": "fact_order_items.csv",
    "fact_shipments": "fact_shipments.csv",

    # Business feature tables
    "business_daily_metrics": "business_features/business_daily_metrics.csv",
    "carrier_features": "business_features/carrier_features.csv",
    "customer_features": "business_features/customer_features.csv",
    "order_features": "business_features/order_features.csv",
    "product_features": "business_features/product_features.csv",
    "supplier_features": "business_features/supplier_features.csv",
    "warehouse_features": "business_features/warehouse_features.csv",
}


# ============================================================
# BUSINESS SQL VIEWS
# ============================================================
#
# Each view is connected to a business question.
#
# We are NOT creating random SQL queries.
# We are creating reusable business views for the dashboard.
# ============================================================

VIEWS = {

    # --------------------------------------------------------
    # 1. EXECUTIVE SUMMARY
    # --------------------------------------------------------
    "vw_executive_summary": """
    CREATE VIEW vw_executive_summary AS
    SELECT
        COUNT(*) AS total_orders,

        SUM(gross_sales) AS gross_sales,

        SUM(discount_amount) AS discount_amount,

        SUM(sales_net) AS sales_net_before_returns,

        SUM(return_amount) AS return_amount,

        SUM(net_sales) AS net_sales,

        SUM(units_sold) AS units_sold,

        SUM(units_returned) AS units_returned,

        CASE
            WHEN SUM(units_sold) = 0
            THEN 0
            ELSE SUM(units_returned) * 1.0 / SUM(units_sold)
        END AS return_rate,

        CASE
            WHEN SUM(gross_sales) = 0
            THEN 0
            ELSE SUM(discount_amount) * 1.0 / SUM(gross_sales)
        END AS discount_rate,

        CASE
            WHEN COUNT(*) = 0
            THEN 0
            ELSE SUM(net_sales) * 1.0 / COUNT(*)
        END AS average_order_value,

        (
            SELECT COUNT(*)
            FROM customer_features
        ) AS customers,

        (
            SELECT COUNT(*)
            FROM product_features
        ) AS products,

        (
            SELECT COUNT(*)
            FROM warehouse_features
        ) AS warehouses,

        (
            SELECT COUNT(*)
            FROM supplier_features
        ) AS suppliers,

        (
            SELECT COUNT(*)
            FROM carrier_features
        ) AS carriers,

        (
            SELECT COALESCE(SUM(total_stock), 0)
            FROM warehouse_features
        ) AS stock_units,

        (
            SELECT COALESCE(SUM(total_shipping_cost), 0)
            FROM carrier_features
        ) AS shipping_cost

    FROM order_features;
    """,

    # --------------------------------------------------------
    # 2. MONTHLY COMMERCIAL PERFORMANCE
    # --------------------------------------------------------
    "vw_monthly_performance": """
    CREATE VIEW vw_monthly_performance AS

    SELECT
        substr(order_date, 1, 7) AS month,

        COUNT(*) AS orders,

        SUM(gross_sales) AS gross_sales,

        SUM(discount_amount) AS discount_amount,

        SUM(sales_net) AS sales_net_before_returns,

        SUM(return_amount) AS return_amount,

        SUM(net_sales) AS net_sales,

        SUM(units_sold) AS units_sold,

        SUM(units_returned) AS units_returned,

        CASE
            WHEN SUM(units_sold) = 0
            THEN 0
            ELSE SUM(units_returned) * 1.0 / SUM(units_sold)
        END AS return_rate,

        CASE
            WHEN SUM(gross_sales) = 0
            THEN 0
            ELSE SUM(discount_amount) * 1.0 / SUM(gross_sales)
        END AS discount_rate,

        CASE
            WHEN COUNT(*) = 0
            THEN 0
            ELSE SUM(net_sales) * 1.0 / COUNT(*)
        END AS average_order_value

    FROM order_features

    WHERE order_date IS NOT NULL

    GROUP BY substr(order_date, 1, 7)

    ORDER BY month;
    """,

    # --------------------------------------------------------
    # 3. CATEGORY OPPORTUNITY / PERFORMANCE
    # --------------------------------------------------------
    "vw_category_performance": """
    CREATE VIEW vw_category_performance AS

    SELECT
        category,

        COUNT(*) AS products,

        SUM(net_sales) AS net_sales,

        SUM(gross_sales) AS gross_sales,

        SUM(discount_amount) AS discount_amount,

        SUM(units_sold) AS units_sold,

        SUM(units_returned) AS units_returned,

        SUM(return_amount) AS return_amount,

        SUM(low_stock_records) AS low_stock_records,

        CASE
            WHEN SUM(units_sold) = 0
            THEN 0
            ELSE SUM(units_returned) * 1.0 / SUM(units_sold)
        END AS return_rate,

        CASE
            WHEN SUM(gross_sales) = 0
            THEN 0
            ELSE SUM(discount_amount) * 1.0 / SUM(gross_sales)
        END AS discount_rate,

        CASE
            WHEN COUNT(*) = 0
            THEN 0
            ELSE SUM(net_sales) * 1.0 / COUNT(*)
        END AS sales_per_product

    FROM product_features

    GROUP BY category

    ORDER BY net_sales DESC;
    """,

    # --------------------------------------------------------
    # 4. PRODUCT PERFORMANCE
    # --------------------------------------------------------
    "vw_product_performance": """
    CREATE VIEW vw_product_performance AS

    SELECT *

    FROM product_features;
    """,

    # --------------------------------------------------------
    # 5. CUSTOMER PERFORMANCE
    # --------------------------------------------------------
    "vw_customer_performance": """
    CREATE VIEW vw_customer_performance AS

    SELECT *

    FROM customer_features;
    """,

    # --------------------------------------------------------
    # 6. WAREHOUSE PERFORMANCE
    # --------------------------------------------------------
    "vw_warehouse_performance": """
    CREATE VIEW vw_warehouse_performance AS

    SELECT *

    FROM warehouse_features;
    """,

    # --------------------------------------------------------
    # 7. SUPPLIER PERFORMANCE
    # --------------------------------------------------------
    "vw_supplier_performance": """
    CREATE VIEW vw_supplier_performance AS

    SELECT *

    FROM supplier_features;
    """,

    # --------------------------------------------------------
    # 8. CARRIER / LOGISTICS PERFORMANCE
    # --------------------------------------------------------
    "vw_carrier_performance": """
    CREATE VIEW vw_carrier_performance AS

    SELECT *

    FROM carrier_features;
    """,

    # --------------------------------------------------------
    # 9. REVENUE CONFIDENCE
    # --------------------------------------------------------
    "vw_revenue_quality": """
    CREATE VIEW vw_revenue_quality AS

    SELECT
        revenue_completeness_status,

        COUNT(*) AS orders,

        SUM(net_sales) AS net_sales,

        AVG(net_sales) AS average_net_sales

    FROM order_features

    GROUP BY revenue_completeness_status

    ORDER BY orders DESC;
    """,

    # --------------------------------------------------------
    # 10. ORDER STATUS PERFORMANCE
    # --------------------------------------------------------
    "vw_order_status_performance": """
    CREATE VIEW vw_order_status_performance AS

    SELECT
        order_status,

        COUNT(*) AS orders,

        SUM(net_sales) AS net_sales,

        SUM(return_amount) AS return_amount,

        SUM(units_sold) AS units_sold,

        SUM(units_returned) AS units_returned,

        SUM(
            CASE
                WHEN net_sales > 0
                THEN 1
                ELSE 0
            END
        ) AS orders_with_nonzero_sales,

        CASE
            WHEN COUNT(*) = 0
            THEN 0
            ELSE
                SUM(
                    CASE
                        WHEN net_sales > 0
                        THEN 1
                        ELSE 0
                    END
                ) * 1.0 / COUNT(*)
        END AS nonzero_sales_rate

    FROM order_features

    GROUP BY order_status

    ORDER BY net_sales DESC;
    """,

    # --------------------------------------------------------
    # 11. DATA / BUSINESS QUALITY SUMMARY
    # --------------------------------------------------------
    "vw_quality_summary": """
    CREATE VIEW vw_quality_summary AS

    SELECT

        (
            SELECT COUNT(*)
            FROM order_features
            WHERE revenue_completeness_status = 'Complete'
        ) AS complete_revenue_orders,

        (
            SELECT COUNT(*)
            FROM order_features
            WHERE revenue_completeness_status = 'Partial'
        ) AS partial_revenue_orders,

        (
            SELECT COUNT(*)
            FROM order_features
            WHERE revenue_completeness_status = 'No Order Details'
        ) AS no_detail_orders,

        (
            SELECT COUNT(*)
            FROM order_features
            WHERE order_financial_status = 'Matched'
        ) AS matched_financial_orders,

        (
            SELECT COUNT(*)
            FROM order_features
            WHERE order_financial_status = 'Missing Source Total'
        ) AS missing_source_total_orders,

        (
            SELECT COUNT(*)
            FROM order_features
            WHERE order_financial_status = 'Cannot Calculate'
        ) AS cannot_calculate_orders,

        (
            SELECT COUNT(*)
            FROM order_features
            WHERE delivery_anomaly_flag = 1
        ) AS delivery_anomaly_orders,

        (
            SELECT COUNT(*)
            FROM order_features
            WHERE
                ship_date IS NOT NULL
                AND order_date IS NOT NULL
                AND date(ship_date) < date(order_date)
        ) AS ship_before_order_orders,

        (
            SELECT COUNT(*)
            FROM order_features
            WHERE customer_status <> 'Matched'
        ) AS unmatched_customer_orders,

        (
            SELECT COUNT(*)
            FROM fact_shipments
            WHERE delivery_date_status = 'Delivery Before Shipment'
        ) AS shipment_delivery_anomalies;
    """,

    # --------------------------------------------------------
    # 12. PRODUCT ACTION CENTER
    # --------------------------------------------------------
    #
    # This is the bridge from:
    #
    # Analysis
    #    ↓
    # Business problem
    #    ↓
    # Investigation
    #
    # No arbitrary score.
    # No artificial ranking.
    # Rules are transparent.
    # --------------------------------------------------------
    "vw_action_center": """
    CREATE VIEW vw_action_center AS

    SELECT

        product_id,

        product_name,

        category,

        supplier_id,

        supplier_name,

        net_sales,

        units_sold,

        units_returned,

        return_amount,

        return_rate,

        current_stock,

        reorder_level_total,

        reorder_gap_units,

        stock_to_reorder_ratio,

        below_reorder_flag,

        revenue_share,

        CASE

            WHEN
                below_reorder_flag = 1
                AND net_sales > 0
                AND return_rate >= (
                    SELECT AVG(return_rate)
                    FROM product_features
                )
            THEN 'High Value + Stock + Return Pressure'

            WHEN
                below_reorder_flag = 1
                AND net_sales > (
                    SELECT AVG(net_sales)
                    FROM product_features
                )
            THEN 'High Value + Low Stock'

            WHEN
                return_rate > (
                    SELECT AVG(return_rate)
                    FROM product_features
                )
                AND net_sales > (
                    SELECT AVG(net_sales)
                    FROM product_features
                )
            THEN 'High Value + Return Pressure'

            WHEN
                net_sales = 0
            THEN 'Zero Revenue Investigation'

            WHEN
                units_sold > 0
                AND net_sales = 0
            THEN 'Units With Zero Revenue'

            ELSE 'Monitor'

        END AS action_area

    FROM product_features;
    """,
}


# ============================================================
# INDEXES
# ============================================================

INDEXES = [

    # Order features
    """
    CREATE INDEX IF NOT EXISTS
    idx_order_features_date
    ON order_features(order_date);
    """,

    """
    CREATE INDEX IF NOT EXISTS
    idx_order_features_customer
    ON order_features(customer_id);
    """,

    """
    CREATE INDEX IF NOT EXISTS
    idx_order_features_warehouse
    ON order_features(warehouse_id);
    """,

    """
    CREATE INDEX IF NOT EXISTS
    idx_order_features_status
    ON order_features(order_status);
    """,

    # Product features
    """
    CREATE INDEX IF NOT EXISTS
    idx_product_features_category
    ON product_features(category);
    """,

    """
    CREATE INDEX IF NOT EXISTS
    idx_product_features_supplier
    ON product_features(supplier_id);
    """,

    """
    CREATE INDEX IF NOT EXISTS
    idx_product_features_sales
    ON product_features(net_sales);
    """,

    # Customer features
    """
    CREATE INDEX IF NOT EXISTS
    idx_customer_features_segment
    ON customer_features(segment);
    """,

    """
    CREATE INDEX IF NOT EXISTS
    idx_customer_features_sales
    ON customer_features(net_sales);
    """,

    # Inventory
    """
    CREATE INDEX IF NOT EXISTS
    idx_inventory_product
    ON fact_inventory(product_id);
    """,

    """
    CREATE INDEX IF NOT EXISTS
    idx_inventory_warehouse
    ON fact_inventory(warehouse_id);
    """,

    # Shipments
    """
    CREATE INDEX IF NOT EXISTS
    idx_shipments_order
    ON fact_shipments(order_id);
    """,

    # Order items
    """
    CREATE INDEX IF NOT EXISTS
    idx_order_items_order
    ON fact_order_items(order_id);
    """,

    """
    CREATE INDEX IF NOT EXISTS
    idx_order_items_product
    ON fact_order_items(product_id);
    """,
]


# ============================================================
# DATABASE BUILD
# ============================================================

def build_database():

    print("=" * 70)
    print("SUPPLY CHAIN INTELLIGENCE")
    print("V2 DATABASE BUILD")
    print("=" * 70)

    print()
    print(f"Project root:")
    print(BASE_DIR)

    print()
    print(f"Analytical folder:")
    print(ANALYTICAL_DIR)

    print()
    print(f"Database:")
    print(DB_FILE)

    # --------------------------------------------------------
    # Validate analytical directory
    # --------------------------------------------------------

    if not ANALYTICAL_DIR.exists():
        raise FileNotFoundError(
            f"Analytical directory not found:\n{ANALYTICAL_DIR}"
        )

    # --------------------------------------------------------
    # Remove old database
    # --------------------------------------------------------

    if DB_FILE.exists():
        print()
        print("Existing database found.")
        print("Replacing old database...")
        DB_FILE.unlink()

    # --------------------------------------------------------
    # Create SQLite engine
    # --------------------------------------------------------

    engine = create_engine(
        f"sqlite:///{DB_FILE}"
    )

    loaded_rows = {}

    print()
    print("-" * 70)
    print("LOADING ANALYTICAL TABLES")
    print("-" * 70)

    # --------------------------------------------------------
    # Load all analytical CSVs
    # --------------------------------------------------------

    for table_name, relative_file in FILES.items():

        file_path = ANALYTICAL_DIR / relative_file

        if not file_path.exists():
            raise FileNotFoundError(
                f"\nRequired analytical file not found:\n{file_path}"
            )

        df = pd.read_csv(file_path)

        df.to_sql(
            table_name,
            engine,
            if_exists="replace",
            index=False,
        )

        loaded_rows[table_name] = len(df)

        print(
            f"{table_name:30}"
            f"{len(df):>8} rows"
        )

    # --------------------------------------------------------
    # Indexes + views
    # --------------------------------------------------------

    print()
    print("-" * 70)
    print("CREATING INDEXES")
    print("-" * 70)

    with engine.begin() as connection:

        for index_sql in INDEXES:

            connection.exec_driver_sql(
                index_sql
            )

    print("Indexes created: PASS")

    # --------------------------------------------------------
    # Create views
    # --------------------------------------------------------

    print()
    print("-" * 70)
    print("CREATING BUSINESS VIEWS")
    print("-" * 70)

    with engine.begin() as connection:

        for view_name, view_sql in VIEWS.items():

            connection.exec_driver_sql(
                f"DROP VIEW IF EXISTS {view_name}"
            )

            connection.exec_driver_sql(
                view_sql
            )

            print(
                f"{view_name:35} PASS"
            )

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    print()
    print("-" * 70)
    print("DATABASE VALIDATION")
    print("-" * 70)

    validation_failed = False

    with engine.connect() as connection:

        # Table counts
        for table_name, expected_rows in loaded_rows.items():

            actual_rows = connection.execute(
                text(
                    f"SELECT COUNT(*) "
                    f"FROM {table_name}"
                )
            ).scalar_one()

            status = (
                "PASS"
                if actual_rows == expected_rows
                else "FAIL"
            )

            print(
                f"{table_name:30}"
                f"CSV={expected_rows:<8}"
                f"DB={actual_rows:<8}"
                f"{status}"
            )

            if status == "FAIL":
                validation_failed = True

        # View execution
        print()
        print("-" * 70)
        print("BUSINESS VIEW VALIDATION")
        print("-" * 70)

        for view_name in VIEWS:

            try:

                connection.execute(
                    text(
                        f"SELECT * "
                        f"FROM {view_name} "
                        f"LIMIT 1"
                    )
                ).fetchall()

                print(
                    f"{view_name:35} PASS"
                )

            except Exception as exc:

                validation_failed = True

                print(
                    f"{view_name:35} FAIL"
                )

                print(
                    f"   Error: {exc}"
                )

    # --------------------------------------------------------
    # Final status
    # --------------------------------------------------------

    print()
    print("=" * 70)

    if validation_failed:

        print("DATABASE BUILD: FAIL")

        raise RuntimeError(
            "Database validation failed."
        )

    print("DATABASE BUILD: PASS")

    print()
    print(
        f"Tables loaded : {len(FILES)}"
    )

    print(
        f"Business views: {len(VIEWS)}"
    )

    print(
        f"Database      : {DB_FILE}"
    )

    print("=" * 70)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    build_database()