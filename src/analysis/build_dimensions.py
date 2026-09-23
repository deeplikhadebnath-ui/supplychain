from pathlib import Path
import pandas as pd


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(r"C:\supply_chain_intelligence")

PRODUCT_FILE = (
    BASE_DIR / "data" / "cleaned" / "products_cleaned.csv"
)

SUPPLIER_FILE = (
    BASE_DIR / "data" / "cleaned" / "suppliers_cleaned.csv"
)

WAREHOUSE_FILE = (
    BASE_DIR / "data" / "cleaned" / "warehouses_cleaned.csv"
)

INVENTORY_FILE = (
    BASE_DIR / "data" / "cleaned" / "inventory_cleaned.csv"
)

OUTPUT_DIR = BASE_DIR / "data" / "analytical"
REPORT_DIR = BASE_DIR / "reports"

PRODUCT_OUTPUT = OUTPUT_DIR / "dim_product.csv"
SUPPLIER_OUTPUT = OUTPUT_DIR / "dim_supplier.csv"
WAREHOUSE_OUTPUT = OUTPUT_DIR / "dim_warehouse.csv"

REPORT_OUTPUT = REPORT_DIR / "dimensions_report.txt"


# ============================================================
# LOAD
# ============================================================

def load_data():

    products = pd.read_csv(PRODUCT_FILE)
    suppliers = pd.read_csv(SUPPLIER_FILE)
    warehouses = pd.read_csv(WAREHOUSE_FILE)
    inventory = pd.read_csv(INVENTORY_FILE)

    return products, suppliers, warehouses, inventory


# ============================================================
# PREPARE TYPES
# ============================================================

def prepare_data(products, suppliers, warehouses, inventory):

    products["product_id"] = pd.to_numeric(
        products["product_id"],
        errors="coerce"
    ).astype("Int64")

    products["supplier_id"] = pd.to_numeric(
        products["supplier_id"],
        errors="coerce"
    ).astype("Int64")

    suppliers["supplier_id"] = pd.to_numeric(
        suppliers["supplier_id"],
        errors="coerce"
    ).astype("Int64")

    warehouses["warehouse_id"] = pd.to_numeric(
        warehouses["warehouse_id"],
        errors="coerce"
    ).astype("Int64")

    inventory["warehouse_id"] = pd.to_numeric(
        inventory["warehouse_id"],
        errors="coerce"
    ).astype("Int64")

    inventory["product_id"] = pd.to_numeric(
        inventory["product_id"],
        errors="coerce"
    ).astype("Int64")

    return products, suppliers, warehouses, inventory


# ============================================================
# PRODUCT DIMENSION
# ============================================================

def build_product_dimension(
    products,
    suppliers,
    inventory
):

    supplier_lookup = suppliers[
        [
            "supplier_id",
            "supplier_name",
            "country",
            "rating"
        ]
    ].copy()

    dim_product = products.merge(
        supplier_lookup,
        on="supplier_id",
        how="left",
        validate="many_to_one"
    )

    # Supplier relationship status
    valid_supplier_ids = set(
        suppliers["supplier_id"].dropna()
    )

    dim_product["supplier_status"] = "Valid"

    dim_product.loc[
        dim_product["supplier_id"].isna(),
        "supplier_status"
    ] = "Missing Supplier Reference"

    dim_product.loc[
        dim_product["supplier_id"].notna()
        & ~dim_product["supplier_id"].isin(valid_supplier_ids),
        "supplier_status"
    ] = "Unmatched Supplier Reference"

    # Inventory coverage
    inventory_count = (
        inventory.dropna(
            subset=["product_id"]
        )
        .groupby("product_id")
        .size()
        .rename("inventory_record_count")
    )

    dim_product = dim_product.merge(
        inventory_count,
        on="product_id",
        how="left",
        validate="one_to_one"
    )

    dim_product["inventory_record_count"] = (
        dim_product["inventory_record_count"]
        .fillna(0)
        .astype(int)
    )

    dim_product["has_inventory"] = (
        dim_product["inventory_record_count"] > 0
    )

    return dim_product


# ============================================================
# SUPPLIER DIMENSION
# ============================================================

def build_supplier_dimension(
    suppliers,
    products
):

    product_count = (
        products.dropna(
            subset=["supplier_id"]
        )
        .groupby("supplier_id")["product_id"]
        .nunique()
        .rename("product_count")
    )

    dim_supplier = suppliers.merge(
        product_count,
        on="supplier_id",
        how="left",
        validate="one_to_one"
    )

    dim_supplier["product_count"] = (
        dim_supplier["product_count"]
        .fillna(0)
        .astype(int)
    )

    dim_supplier["has_products"] = (
        dim_supplier["product_count"] > 0
    )

    return dim_supplier


# ============================================================
# WAREHOUSE DIMENSION
# ============================================================

def build_warehouse_dimension(
    warehouses,
    inventory
):

    inventory_count = (
        inventory.dropna(
            subset=["warehouse_id"]
        )
        .groupby("warehouse_id")
        .size()
        .rename("inventory_record_count")
    )

    product_count = (
        inventory.dropna(
            subset=["warehouse_id", "product_id"]
        )
        .groupby("warehouse_id")["product_id"]
        .nunique()
        .rename("product_count")
    )

    dim_warehouse = warehouses.merge(
        inventory_count,
        on="warehouse_id",
        how="left",
        validate="one_to_one"
    )

    dim_warehouse = dim_warehouse.merge(
        product_count,
        on="warehouse_id",
        how="left",
        validate="one_to_one"
    )

    dim_warehouse["inventory_record_count"] = (
        dim_warehouse["inventory_record_count"]
        .fillna(0)
        .astype(int)
    )

    dim_warehouse["product_count"] = (
        dim_warehouse["product_count"]
        .fillna(0)
        .astype(int)
    )

    dim_warehouse["has_inventory"] = (
        dim_warehouse["inventory_record_count"] > 0
    )

    return dim_warehouse


# ============================================================
# VALIDATION
# ============================================================

def validate_dimension(
    dataframe,
    key_column,
    source_rows,
    name
):

    missing_key = dataframe[key_column].isna().sum()
    duplicate_key = dataframe[key_column].duplicated().sum()
    final_rows = len(dataframe)

    if (
        final_rows == source_rows
        and missing_key == 0
        and duplicate_key == 0
    ):
        status = "PASS"
    else:
        status = "FAIL"

    return {
        "name": name,
        "source_rows": source_rows,
        "final_rows": final_rows,
        "missing_key": missing_key,
        "duplicate_key": duplicate_key,
        "status": status
    }


# ============================================================
# REPORT
# ============================================================

def create_report(
    products,
    suppliers,
    warehouses,
    inventory,
    dim_product,
    dim_supplier,
    dim_warehouse,
    validations
):

    product_validation = validations["product"]
    supplier_validation = validations["supplier"]
    warehouse_validation = validations["warehouse"]

    product_report = (
        product_validation["status"]
    )

    supplier_report = (
        supplier_validation["status"]
    )

    warehouse_report = (
        warehouse_validation["status"]
    )

    unmatched_products = (
        dim_product["supplier_status"]
        == "Unmatched Supplier Reference"
    ).sum()

    missing_product_suppliers = (
        dim_product["supplier_status"]
        == "Missing Supplier Reference"
    ).sum()

    products_with_inventory = (
        dim_product["has_inventory"]
    ).sum()

    suppliers_with_products = (
        dim_supplier["has_products"]
    ).sum()

    warehouses_with_inventory = (
        dim_warehouse["has_inventory"]
    ).sum()

    overall_status = (
        "PASS"
        if all(
            validation["status"] == "PASS"
            for validation in validations.values()
        )
        else "PASS WITH WARNINGS"
    )

    report = f"""
MASTER DIMENSIONS - ANALYTICAL REPORT
=====================================


DIM PRODUCT
-----------

Source rows:
{len(products)}

Final rows:
{len(dim_product)}

Missing product IDs:
{product_validation["missing_key"]}

Duplicate product IDs:
{product_validation["duplicate_key"]}

Missing supplier reference:
{missing_product_suppliers}

Unmatched supplier reference:
{unmatched_products}

Products with inventory:
{products_with_inventory}

Products without inventory:
{len(dim_product) - products_with_inventory}

Columns:
{", ".join(dim_product.columns)}


DIM SUPPLIER
------------

Source rows:
{len(suppliers)}

Final rows:
{len(dim_supplier)}

Missing supplier IDs:
{supplier_validation["missing_key"]}

Duplicate supplier IDs:
{supplier_validation["duplicate_key"]}

Suppliers with products:
{suppliers_with_products}

Suppliers without products:
{len(dim_supplier) - suppliers_with_products}

Columns:
{", ".join(dim_supplier.columns)}


DIM WAREHOUSE
-------------

Source rows:
{len(warehouses)}

Final rows:
{len(dim_warehouse)}

Missing warehouse IDs:
{warehouse_validation["missing_key"]}

Duplicate warehouse IDs:
{warehouse_validation["duplicate_key"]}

Warehouses with inventory:
{warehouses_with_inventory}

Warehouses without inventory:
{len(dim_warehouse) - warehouses_with_inventory}

Columns:
{", ".join(dim_warehouse.columns)}


INVENTORY SOURCE
----------------

Inventory rows used for enrichment:
{len(inventory)}


SOURCE VALUES
-------------

No source product values were intentionally overwritten.
No source supplier values were intentionally overwritten.
No source warehouse values were intentionally overwritten.

No master records were intentionally deleted.


ADVANCED FEATURE ENGINEERING
----------------------------

Not created at this stage:

- Product profitability
- Product ABC classification
- Supplier performance score
- Supplier risk score
- Warehouse utilization
- Warehouse capacity utilization score
- Inventory turnover
- Customer/product/supplier risk scores

These belong to the later feature-engineering layer.


FINAL VALIDATION
----------------

Product dimension:
{product_report}

Supplier dimension:
{supplier_report}

Warehouse dimension:
{warehouse_report}


OVERALL STATUS
--------------
{overall_status}
"""

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    REPORT_OUTPUT.write_text(
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

    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    products, suppliers, warehouses, inventory = load_data()

    print(f"Products: {products.shape}")
    print(f"Suppliers: {suppliers.shape}")
    print(f"Warehouses: {warehouses.shape}")
    print(f"Inventory: {inventory.shape}")

    (
        products,
        suppliers,
        warehouses,
        inventory
    ) = prepare_data(
        products,
        suppliers,
        warehouses,
        inventory
    )

    # --------------------------------------------------------
    # Build dimensions
    # --------------------------------------------------------

    dim_product = build_product_dimension(
        products,
        suppliers,
        inventory
    )

    dim_supplier = build_supplier_dimension(
        suppliers,
        products
    )

    dim_warehouse = build_warehouse_dimension(
        warehouses,
        inventory
    )

    print(
        f"\nDim Product rows: "
        f"{len(dim_product)}"
    )

    print(
        f"Dim Supplier rows: "
        f"{len(dim_supplier)}"
    )

    print(
        f"Dim Warehouse rows: "
        f"{len(dim_warehouse)}"
    )

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    validations = {

        "product": validate_dimension(
            dim_product,
            "product_id",
            len(products),
            "Product"
        ),

        "supplier": validate_dimension(
            dim_supplier,
            "supplier_id",
            len(suppliers),
            "Supplier"
        ),

        "warehouse": validate_dimension(
            dim_warehouse,
            "warehouse_id",
            len(warehouses),
            "Warehouse"
        )
    }

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    dim_product.to_csv(
        PRODUCT_OUTPUT,
        index=False
    )

    dim_supplier.to_csv(
        SUPPLIER_OUTPUT,
        index=False
    )

    dim_warehouse.to_csv(
        WAREHOUSE_OUTPUT,
        index=False
    )

    # --------------------------------------------------------
    # Report
    # --------------------------------------------------------

    create_report(
        products,
        suppliers,
        warehouses,
        inventory,
        dim_product,
        dim_supplier,
        dim_warehouse,
        validations
    )

    overall_status = (
        "PASS"
        if all(
            validation["status"] == "PASS"
            for validation in validations.values()
        )
        else "PASS WITH WARNINGS"
    )

    print("\nMASTER DIMENSIONS CREATED SUCCESSFULLY.")

    print(
        f"Product output: {PRODUCT_OUTPUT}"
    )

    print(
        f"Supplier output: {SUPPLIER_OUTPUT}"
    )

    print(
        f"Warehouse output: {WAREHOUSE_OUTPUT}"
    )

    print(
        f"Report: {REPORT_OUTPUT}"
    )

    print(
        f"Final status: {overall_status}"
    )


if __name__ == "__main__":
    main()