import pandas as pd
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = BASE_DIR / "data" / "raw" / "05_orders.csv"


orders = pd.read_csv(INPUT_FILE)


# Convert dates using the same rule as the cleaning script
orders["order_date_parsed"] = pd.to_datetime(
    orders["order_date"],
    format="mixed",
    dayfirst=True,
    errors="coerce"
)

orders["ship_date_parsed"] = pd.to_datetime(
    orders["ship_date"],
    format="mixed",
    dayfirst=True,
    errors="coerce"
)


# ---------------------------------------------------------
# 1. Ship date before order date
# ---------------------------------------------------------

reversed_dates = orders[
    (orders["ship_date_parsed"] < orders["order_date_parsed"])
    & orders["ship_date_parsed"].notna()
    & orders["order_date_parsed"].notna()
]


print("\nSHIP DATE BEFORE ORDER DATE")
print("==========================")

print("Count:", len(reversed_dates))

print(
    reversed_dates[
        [
            "order_id",
            "order_date",
            "ship_date",
            "order_date_parsed",
            "ship_date_parsed",
            "order_status"
        ]
    ].to_string(index=False)
)


# ---------------------------------------------------------
# 2. Future dates
# ---------------------------------------------------------

today = pd.Timestamp.today().normalize()

future_dates = orders[
    (orders["order_date_parsed"] > today)
    | (orders["ship_date_parsed"] > today)
]


print("\nFUTURE DATES")
print("============")

print("Count:", len(future_dates))

print(
    future_dates[
        [
            "order_id",
            "order_date",
            "ship_date",
            "order_date_parsed",
            "ship_date_parsed",
            "order_status"
        ]
    ].to_string(index=False)
)