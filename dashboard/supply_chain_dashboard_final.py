from contextlib import closing
from pathlib import Path
import os
import sqlite3
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

# ============================================================
# SUPPLY CHAIN INTELLIGENCE - PRESENTATION VERSION
# Lavender theme | 6 focused pages
# ============================================================

st.set_page_config(
    page_title="Supply Chain Intelligence",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------------------------------------------------
# LAVENDER COLOR PALETTE
# ------------------------------------------------------------
LAV_1 = "#a78bfa"  # primary lavender
LAV_2 = "#c4b5fd"  # soft lavender
LAV_3 = "#7c3aed"  # deep violet (accent / totals)
LAV_4 = "#ede9fe"  # pale lavender (highlights)
LAV_5 = "#d8b4fe"  # pink-lavender
LAV_6 = "#5b21b6"  # darkest violet
LAV_WARN = "#f0abfc"  # warm pink-magenta for warnings/negatives

LAVENDER_SEQUENCE = [LAV_1, LAV_2, LAV_3, LAV_5, LAV_6, "#ddd6fe", "#8b5cf6", "#f0abfc"]
LAVENDER_CONTINUOUS = [[0, "#1e1b2e"], [0.5, LAV_3], [1, LAV_4]]

px.defaults.color_discrete_sequence = LAVENDER_SEQUENCE
px.defaults.color_continuous_scale = LAVENDER_CONTINUOUS

DB_NAME = "supply_chain_intelligence.db"


def find_db_file():
    """Locate the database file without requiring a strict 'database' folder."""
    env_path = os.environ.get("SUPPLY_CHAIN_DB")
    if env_path and Path(env_path).is_file():
        return Path(env_path)

    script_dir = Path(__file__).resolve().parent
    cwd = Path.cwd().resolve()

    # Check current directory, script directory, and common subfolders
    candidates = [
        cwd / DB_NAME,
        script_dir / DB_NAME,
        cwd / "database" / DB_NAME,
        script_dir / "database" / DB_NAME,
        script_dir.parent / "database" / DB_NAME
    ]

    for candidate in candidates:
        if candidate.is_file():
            return candidate

    return None


DB_FILE = find_db_file()

# ------------------------------------------------------------
# THEME
# ------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --navy: #150f24;
    --blue: #7c3aed;
    --blue2: #a78bfa;
    --green: #c4b5fd;
    --green2: #ede9fe;
    --text: #f3f0ff;
    --muted: #a9a0c4;
    --card: #221a38;
    --border: rgba(196, 181, 253, .20);
}
html, body, [class*="css"] { font-family: Inter, Segoe UI, sans-serif; }
.stApp {
    background: linear-gradient(180deg, #100b1c 0%, #170f29 55%, #150f24 100%);
    color: var(--text);
}
.block-container { max-width: 1500px; padding-top: 3rem; padding-bottom: 2.5rem; }
header[data-testid="stHeader"] { background: transparent; }
section[data-testid="stSidebar"] { background: #120c1f; border-right: 1px solid var(--border); }

.brand { padding: .3rem .1rem 1rem; }
.brand-title { font-weight: 800; font-size: 1.12rem; color: #fff; }
.brand-sub { color: var(--muted); font-size: .72rem; margin-top: .15rem; }

.page-title {
    font-size: 2rem; font-weight: 800; letter-spacing: -.035em;
    line-height: 1.3; margin-bottom: .15rem;
}
.page-subtitle { color: var(--muted); font-size: .85rem; margin-bottom: 1rem; }
.section-title {
    font-size: 1.08rem; font-weight: 800; color: #fff;
    margin: 1.1rem 0 .45rem 0;
}
.section-note { color: var(--muted); font-size: .73rem; margin-top: -.25rem; margin-bottom: .45rem; }

.metric-card {
    background: linear-gradient(145deg, #29204a, #1d1633);
    border: 1px solid rgba(167,139,250,.25);
    border-radius: 16px; padding: .9rem 1rem; min-height: 118px;
    box-shadow: 0 12px 30px rgba(0,0,0,.18);
}
.metric-label { color: #c3b6e6; font-size: .70rem; font-weight: 700; }
.metric-value { color: #fff; font-size: 1.55rem; font-weight: 800; margin-top: .55rem; }
.metric-help { color: #8b7fae; font-size: .64rem; margin-top: .25rem; }
.metric-accent { color: var(--green); }

.insight {
    border-left: 3px solid var(--blue2);
    background: rgba(167,139,250,.08);
    border-top: 1px solid var(--border); border-right: 1px solid var(--border); border-bottom: 1px solid var(--border);
    border-radius: 12px; padding: .75rem .9rem; margin-top: .6rem;
    color: #ece6fb; font-size: .78rem; line-height: 1.45;
}
.badge { display:inline-block; padding:.22rem .48rem; border-radius:999px; font-size:.62rem; font-weight:700; margin-right:.25rem; }
.badge-blue { background:rgba(124,58,237,.18); color:#c4b5fd; }
.badge-green { background:rgba(196,181,253,.16); color:#e9d5ff; }

.takeaway {
    background: linear-gradient(135deg, rgba(124,58,237,.20), rgba(167,139,250,.08));
    border: 1px solid rgba(196,181,253,.35);
    border-left: 4px solid #a78bfa;
    border-radius: 12px; padding: .85rem 1.1rem; margin: .3rem 0 1.1rem 0;
    color: #f3f0ff; font-size: .85rem; line-height: 1.5;
}
.takeaway b.tk-label { color: #d8b4fe; text-transform: uppercase; font-size: .68rem; letter-spacing: .06em; }

.tldr {
    background: linear-gradient(135deg, #2c2150, #1d1633 65%);
    border: 1px solid rgba(196,181,253,.4);
    border-radius: 16px; padding: 1.1rem 1.3rem; margin-bottom: 1.3rem;
    box-shadow: 0 14px 34px rgba(0,0,0,.25);
}
.tldr-title { color: #e9d5ff; font-weight: 800; font-size: .82rem; text-transform: uppercase; letter-spacing: .06em; margin-bottom: .55rem; }
.tldr ul { margin: 0; padding-left: 1.1rem; }
.tldr li { color: #f3f0ff; font-size: .88rem; line-height: 1.6; margin-bottom: .25rem; }
.tldr li b { color: #d8b4fe; }

/* Keep Streamlit dropdowns visually clean */
div[data-baseweb="select"] > div { background: #201936; border-color: rgba(196,181,253,.25); }
label { color: #e3d9f7 !important; font-weight: 600 !important; }

footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ------------------------------------------------------------
# MASTER GRANULAR DATA
# ------------------------------------------------------------
@st.cache_data(ttl=600)
def load_master():
    with closing(sqlite3.connect(DB_FILE)) as con:
        items = pd.read_sql_query(
            """
            SELECT order_id, product_id, customer_id, warehouse_id, supplier_id,
                   order_date, order_status, product_name, category, quantity,
                   net_line_amount, gross_line_amount, discount_amount, transaction_type
            FROM fact_order_items
            """, con)
        dim_c = pd.read_sql_query("SELECT customer_id, segment, country AS customer_country FROM dim_customer", con)
        dim_w = pd.read_sql_query("SELECT warehouse_id, warehouse_name FROM dim_warehouse", con)
        dim_s = pd.read_sql_query(
            "SELECT supplier_id, supplier_name, rating AS supplier_rating, country AS supplier_country FROM dim_supplier",
            con)
        dim_p = pd.read_sql_query(
            "SELECT product_id, supplier_id AS p_supplier_id, supplier_name AS p_supplier_name FROM dim_product", con)
        inv = pd.read_sql_query(
            "SELECT warehouse_id, product_id, warehouse_name, category, stock_quantity, reorder_level, stock_status FROM fact_inventory",
            con)
        ship = pd.read_sql_query("SELECT * FROM fact_shipments", con)
        order_meta = pd.read_sql_query(
            "SELECT order_id, revenue_completeness_status, delivery_anomaly_flag FROM order_features", con)

    items["order_date"] = pd.to_datetime(items["order_date"], dayfirst=True, errors="coerce")
    items = items.merge(dim_c, on="customer_id", how="left")
    items = items.merge(dim_w, on="warehouse_id", how="left")
    items = items.merge(dim_s, on="supplier_id", how="left")

    inv = inv.merge(dim_p, on="product_id", how="left")
    inv["supplier_name"] = inv["p_supplier_name"]

    ship["shipment_date"] = pd.to_datetime(ship["shipment_date"], errors="coerce")
    ship["delivery_date"] = pd.to_datetime(ship["delivery_date"], errors="coerce")
    ship["delivery_days"] = (ship["delivery_date"] - ship["shipment_date"]).dt.days

    return items, inv, ship, order_meta


if DB_FILE is None:
    st.error(f"❌ Database file not found: {DB_NAME}")
    st.info(
        f"Please ensure **{DB_NAME}** is saved in the exact same folder as this Python script, then run the dashboard again."
    )
    st.stop()

try:
    items, inv, ship, order_meta = load_master()
except Exception as e:
    st.error(f"Database could not be loaded: {e}")
    st.stop()

# ------------------------------------------------------------
# DATA QUALITY CORRECTION: true cut-off month
# ------------------------------------------------------------
_order_dates = items.dropna(subset=["order_date"]).drop_duplicates("order_id")["order_date"]
_monthly_counts = _order_dates.groupby(_order_dates.dt.to_period("M")).size()
if len(_monthly_counts):
    _threshold = max(_monthly_counts.median() * 0.25, 20)
    _normal_months = _monthly_counts[_monthly_counts >= _threshold]
    CUTOFF_DATE = _normal_months.index.max().to_timestamp(how="end").normalize() if len(
        _normal_months) else _order_dates.max()
else:
    CUTOFF_DATE = _order_dates.max()

_prod_all = items.groupby(["product_id"]).agg(
    net_sales=("net_line_amount", "sum"),
    units_sold=("quantity", lambda x: x[items.loc[x.index, "transaction_type"] == "Sale"].sum()),
).reset_index()
_returned_all = items[items["transaction_type"] == "Return / Reversal"].groupby("product_id")["quantity"].sum().abs()
_prod_all["units_returned"] = _prod_all["product_id"].map(_returned_all).fillna(0)
_prod_all["return_rate"] = np.where(_prod_all["units_sold"] > 0, _prod_all["units_returned"] / _prod_all["units_sold"],
                                    0)
GLOBAL_AVG_RETURN_RATE = _prod_all["return_rate"].mean()
GLOBAL_AVG_NET_SALES = _prod_all["net_sales"].mean()


# ------------------------------------------------------------
# FILTER FUNCTIONS
# ------------------------------------------------------------
def filter_items(df, cat, sup, wh, seg, yr):
    out = df
    if cat != "All": out = out[out["category"].eq(cat)]
    if sup != "All": out = out[out["supplier_name"].eq(sup)]
    if wh != "All": out = out[out["warehouse_name"].eq(wh)]
    if seg != "All": out = out[out["segment"].eq(seg)]
    if yr != "All": out = out[out["order_date"].dt.year.eq(int(yr))]
    return out


def filter_inv(df, cat, sup, wh):
    out = df
    if cat != "All": out = out[out["category"].eq(cat)]
    if sup != "All": out = out[out["supplier_name"].eq(sup)]
    if wh != "All": out = out[out["warehouse_name"].eq(wh)]
    return out


# ------------------------------------------------------------
# AGGREGATION HELPERS
# ------------------------------------------------------------
def agg_by(items_df, dim_col):
    sales_lines = items_df[items_df["transaction_type"] == "Sale"]
    return_lines = items_df[items_df["transaction_type"] == "Return / Reversal"]
    g = items_df.groupby(dim_col).agg(net_sales=("net_line_amount", "sum"),
                                      gross_sales=("gross_line_amount", "sum"),
                                      discount_amount=("discount_amount", "sum"),
                                      orders=("order_id", "nunique")).reset_index()
    units_sold = sales_lines.groupby(dim_col)["quantity"].sum().rename("units_sold")
    units_returned = return_lines.groupby(dim_col)["quantity"].sum().abs().rename("units_returned")
    g = g.merge(units_sold, on=dim_col, how="left").merge(units_returned, on=dim_col, how="left")
    g["units_sold"] = g["units_sold"].fillna(0)
    g["units_returned"] = g["units_returned"].fillna(0)
    g["return_rate"] = np.where(g["units_sold"] > 0, g["units_returned"] / g["units_sold"], 0)
    return g


def product_level(items_df, inv_df):
    p = agg_by(items_df, ["product_id", "product_name", "category", "supplier_name"])
    s = inv_df.groupby("product_id").agg(
        current_stock=("stock_quantity", "sum"),
        reorder_level_total=("reorder_level", "sum"),
        below_reorder_flag=("stock_status", lambda x: (x == "Below Reorder Level").any()),
    ).reset_index()
    p = p.merge(s, on="product_id", how="left")
    p["current_stock"] = p["current_stock"].fillna(0)
    p["reorder_level_total"] = p["reorder_level_total"].fillna(0)
    p["below_reorder_flag"] = p["below_reorder_flag"].fillna(False)
    p["stock_to_reorder_ratio"] = np.where(p["reorder_level_total"] > 0, p["current_stock"] / p["reorder_level_total"],
                                           np.nan)
    total = p["net_sales"].sum()
    p["revenue_share"] = np.where(total > 0, p["net_sales"] / total, 0)
    return p


def classify_action(row):
    if row["below_reorder_flag"] and row["net_sales"] > 0 and row["return_rate"] >= GLOBAL_AVG_RETURN_RATE:
        return "High Value + Stock + Return Pressure"
    if row["below_reorder_flag"] and row["net_sales"] > GLOBAL_AVG_NET_SALES:
        return "High Value + Low Stock"
    if row["return_rate"] > GLOBAL_AVG_RETURN_RATE and row["net_sales"] > GLOBAL_AVG_NET_SALES:
        return "High Value + Return Pressure"
    if row["net_sales"] == 0:
        return "Zero Revenue Investigation"
    return None


# ------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------
def money(v):
    if pd.isna(v): return "—"
    v = float(v)
    if abs(v) >= 1e9: return f"₹{v / 1e9:.2f}B"
    if abs(v) >= 1e6: return f"₹{v / 1e6:.2f}M"
    if abs(v) >= 1e3: return f"₹{v / 1e3:.1f}K"
    return f"₹{v:,.0f}"


def integer(v):
    if pd.isna(v): return "—"
    return f"{float(v):,.0f}"


def pct(v):
    if pd.isna(v): return "—"
    return f"{float(v) * 100:.2f}%"


def heading(title, icon, subtitle=""):
    st.markdown(f'<div class="page-title"><b>{icon} {title}</b></div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="page-subtitle">{subtitle}</div>', unsafe_allow_html=True)


def takeaway(text):
    st.markdown(f'<div class="takeaway"><b class="tk-label">🎯 Key Takeaway</b><br>{text}</div>', unsafe_allow_html=True)


def tldr(items_list):
    lis = "".join(f"<li>{it}</li>" for it in items_list)
    st.markdown(
        f'<div class="tldr"><div class="tldr-title">🚦 The Big Picture — 3 Things To Know</div><ul>{lis}</ul></div>',
        unsafe_allow_html=True)


def section(title, icon, note=""):
    st.markdown(f'<div class="section-title"><b>{icon} {title}</b></div>', unsafe_allow_html=True)
    if note:
        st.markdown(f'<div class="section-note">{note}</div>', unsafe_allow_html=True)


def kpi(col, icon, label, value, help_text=""):
    with col:
        st.markdown(f'''<div class="metric-card">
        <div class="metric-label">{icon} {label}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-help">{help_text}</div>
        </div>''', unsafe_allow_html=True)


def fig_style(fig, height=390, dark=False):
    paper = "#120c1f" if dark else "rgba(0,0,0,0)"
    plot = "#120c1f" if dark else "rgba(0,0,0,0)"
    fig.update_layout(
        height=height,
        margin=dict(l=18, r=18, t=58, b=22),
        paper_bgcolor=paper,
        plot_bgcolor=plot,
        font=dict(family="Inter, Segoe UI, sans-serif", color="#ece6fb"),
        title_font=dict(size=16, color="#ffffff"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        hoverlabel=dict(bgcolor="#221a38", font_color="#ffffff"),
    )
    fig.update_xaxes(showgrid=False, zeroline=False, linecolor="rgba(196,181,253,.20)")
    fig.update_yaxes(gridcolor="rgba(196,181,253,.12)", zeroline=False)
    return fig


CHART_CONFIG = {
    "displayModeBar": True,
    "displaylogo": False,
    "modeBarButtonsToRemove": ["select2d", "lasso2d", "autoScale2d"],
    "toImageButtonOptions": {"format": "png", "scale": 2},
}


def chart(fig, height=390):
    st.plotly_chart(fig_style(fig, height), width="stretch", config=CHART_CONFIG)


# ------------------------------------------------------------
# SIDEBAR / DROPDOWN SLICERS
# ------------------------------------------------------------
st.sidebar.markdown(
    '<div class="brand"><div class="brand-title">📦 Supply Chain Intelligence</div><div class="brand-sub">Presentation-ready analytics dashboard</div></div>',
    unsafe_allow_html=True)

page = st.sidebar.selectbox("📑 Dashboard Page", [
    "Executive Overview",
    "Revenue & Product",
    "Customer Intelligence",
    "Inventory & Warehouse",
    "Supplier & Logistics",
    "Data Quality & Action",
])

st.sidebar.markdown("---")
st.sidebar.markdown("### 🎛️ Filters")
st.sidebar.caption("Every filter below applies to every chart on every page.")

categories = ["All"] + sorted(items["category"].dropna().astype(str).unique().tolist())
suppliers_list = ["All"] + sorted(items["supplier_name"].dropna().astype(str).unique().tolist())
warehouses_list = ["All"] + sorted(items["warehouse_name"].dropna().astype(str).unique().tolist())
segments = ["All"] + sorted(items["segment"].dropna().astype(str).unique().tolist())
years = sorted(items["order_date"].dropna().dt.year.astype(int).unique().tolist())
year_options = ["All"] + [str(y) for y in years]

f_category = st.sidebar.selectbox("Category", categories)
f_supplier = st.sidebar.selectbox("Supplier", suppliers_list)
f_warehouse = st.sidebar.selectbox("Warehouse", warehouses_list)
f_segment = st.sidebar.selectbox("Customer Segment", segments)
f_year = st.sidebar.selectbox("Year", year_options)

# ---- the ONE filtered dataset every page/chart is built from ----
items_f = filter_items(items, f_category, f_supplier, f_warehouse, f_segment, f_year)
inv_f = filter_inv(inv, f_category, f_supplier, f_warehouse)
_filtered_order_ids = set(items_f["order_id"].unique())
ship_f = ship[ship["order_id"].isin(_filtered_order_ids)].copy()
order_meta_f = order_meta[order_meta["order_id"].isin(_filtered_order_ids)].copy()

sh_valid = ship_f[(ship_f["delivery_days"] >= 0) & (ship_f["delivery_days"] <= 60)]
sh_anomaly = ship_f[ship_f["delivery_days"] > 60]
if len(sh_valid):
    carrier_stats = sh_valid.groupby("carrier").agg(
        avg_delivery_days=("delivery_days", "mean"),
        median_delivery_days=("delivery_days", "median"),
        late_14d_rate=("delivery_days", lambda x: (x > 14).mean()),
        shipment_count=("shipment_id", "nunique"),
        total_shipping_cost=("shipping_cost", "sum"),
        average_shipping_cost=("shipping_cost", "mean"),
    ).reset_index()
    anomaly_counts = sh_anomaly.groupby("carrier").size().rename("anomaly_count").reset_index()
    carrier_stats = carrier_stats.merge(anomaly_counts, on="carrier", how="left")
    carrier_stats["anomaly_count"] = carrier_stats["anomaly_count"].fillna(0)
else:
    carrier_stats = pd.DataFrame(
        columns=["carrier", "avg_delivery_days", "median_delivery_days", "late_14d_rate", "shipment_count",
                 "total_shipping_cost", "average_shipping_cost", "anomaly_count"])

products_f = product_level(items_f, inv_f)
if len(products_f):
    products_f["action_area"] = products_f.apply(classify_action, axis=1)
actions_f = products_f[products_f["action_area"].notna()].copy() if len(products_f) else products_f

st.sidebar.markdown("---")
st.sidebar.markdown(
    '<span class="badge badge-blue">SQLITE</span><span class="badge badge-green">LIVE FILTERED DATA</span>',
    unsafe_allow_html=True)

# ------------------------------------------------------------
# 1. EXECUTIVE OVERVIEW
# ------------------------------------------------------------
if page == "Executive Overview":
    heading("Executive Overview", "🧠",
            "A compact management view of revenue, orders, customers and commercial health. All figures below reflect the current filter selection.")
    tldr([
        "<b>Growth is slowing</b> — new-customer sales share fell from ~40% (2025) to ~7% (2026 YTD); the growth engine is running out of new buyers, not existing demand.",
        "<b>~25% of reported revenue isn't real yet</b> — it sits in Cancelled or Returned orders, so headline sales numbers overstate what actually landed.",
        "<b>Operational risk is concentrated</b> — a large share of supplier revenue runs through suppliers rated below 3/5, and warehouse stock is measurably misaligned with where sales happen.",
    ])

    net_sales_v = items_f["net_line_amount"].sum()
    gross_sales_v = items_f["gross_line_amount"].sum()
    discount_v = items_f["discount_amount"].sum()
    return_amount_v = -items_f.loc[items_f["transaction_type"] == "Return / Reversal", "net_line_amount"].sum()
    orders_v = items_f["order_id"].nunique()
    customers_v = items_f["customer_id"].nunique()
    units_sold_v = items_f.loc[items_f["transaction_type"] == "Sale", "quantity"].sum()
    units_returned_v = -items_f.loc[items_f["transaction_type"] == "Return / Reversal", "quantity"].sum()
    return_rate_v = (units_returned_v / units_sold_v) if units_sold_v else 0

    c = st.columns(5, gap="medium")
    kpi(c[0], "💰", "Net Sales", money(net_sales_v), "After discounts and returns")
    kpi(c[1], "📈", "Gross Sales", money(gross_sales_v), "Before discounts and returns")
    kpi(c[2], "🛒", "Orders", integer(orders_v), "Distinct orders in selection")
    kpi(c[3], "👥", "Customers", integer(customers_v), "Distinct customers in selection")
    kpi(c[4], "↩️", "Return Rate", pct(return_rate_v), "Units returned / units sold")

    monthly = items_f.dropna(subset=["order_date"]).copy()
    monthly["month"] = monthly["order_date"].dt.to_period("M").dt.to_timestamp()
    monthly_agg = monthly.groupby("month", as_index=False).agg(gross_sales=("gross_line_amount", "sum"),
                                                               net_sales=("net_line_amount", "sum"))
    mt_display = monthly_agg[monthly_agg["month"] <= CUTOFF_DATE].sort_values("month")
    dropped = len(monthly_agg) - len(mt_display)
    note = "Gross sales and net sales movement over time, for the current filter selection."
    if dropped > 0:
        note += f" {dropped} trailing month(s) with too few orders to be representative were excluded from the trend line."
    section("Monthly Revenue Trend", "📈", note)
    if mt_display.empty:
        st.info("No orders match the current filter selection.")
    else:
        trend_long = mt_display.melt(id_vars="month", value_vars=["gross_sales", "net_sales"], var_name="type",
                                     value_name="sales")
        trend_long["type"] = trend_long["type"].map({"gross_sales": "Gross Sales", "net_sales": "Net Sales"})
        fig = px.line(trend_long, x="month", y="sales", color="type", markers=True, title="Gross vs Net Sales",
                      color_discrete_map={"Gross Sales": LAV_2, "Net Sales": LAV_3})
        fig.update_traces(line=dict(width=3))
        fig.update_layout(xaxis_title="Month", yaxis_title="Sales", legend_title="")
        chart(fig, 400)

    a, b = st.columns(2, gap="large")
    with a:
        section("Revenue Bridge", "🌉", "How gross sales become net sales after discounts and returns.")
        bridge_df = pd.DataFrame({
            "stage": ["Gross Sales", "Discounts", "Returns", "Net Sales"],
            "amount": [gross_sales_v, discount_v, return_amount_v, net_sales_v],
        })
        wf = px.bar(bridge_df, x="stage", y="amount", color="stage", text="amount",
                    title="Gross Sales, Discounts, Returns & Net Sales",
                    color_discrete_map={"Gross Sales": LAV_3, "Discounts": LAV_WARN, "Returns": LAV_WARN,
                                        "Net Sales": LAV_2})
        wf.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
        wf.update_layout(showlegend=False, yaxis_title="Value", xaxis_title="")
        chart(wf, 400)
    with b:
        section("Category Contribution", "🧩",
                "Which categories contribute the most net sales, in the current selection?")
        cat_agg = agg_by(items_f, "category").sort_values("net_sales", ascending=False).head(10)
        if cat_agg.empty:
            st.info("No data for the current filter selection.")
        else:
            fig = px.bar(cat_agg, x="category", y="net_sales", title="Top Categories by Net Sales")
            fig.update_traces(marker_color=LAV_2)
            fig.update_layout(xaxis_title="Category", yaxis_title="Net Sales")
            chart(fig, 400)

    section("New vs Returning Customers", "🌱",
            "Share of each year's net sales coming from customers placing their first-ever order that year, versus customers who had already ordered before (classification uses each customer's full order history, not just the current filter).")
    first_year_map = items.dropna(subset=["order_date"]).groupby("customer_id")["order_date"].min().dt.year
    orv = items_f.dropna(subset=["order_date"]).copy()
    orv["year"] = orv["order_date"].dt.year
    orv["first_year"] = orv["customer_id"].map(first_year_map)
    orv["customer_type"] = np.where(orv["year"] == orv["first_year"], "New Customer", "Returning Customer")
    orv = orv[
        (orv["year"] < CUTOFF_DATE.year) | ((orv["year"] == CUTOFF_DATE.year) & (orv["order_date"] <= CUTOFF_DATE))]
    yearly = orv.groupby(["year", "customer_type"], as_index=False)["net_line_amount"].sum().rename(
        columns={"net_line_amount": "net_sales"})
    if yearly.empty:
        st.info("No data for the current filter selection.")
    else:
        fig = px.bar(yearly, x="year", y="net_sales", color="customer_type", barmode="stack",
                     title="Net Sales by Customer Type, by Year",
                     color_discrete_map={"New Customer": LAV_2, "Returning Customer": LAV_6})
        fig.update_layout(xaxis_title="Year", yaxis_title="Net Sales", xaxis=dict(dtick=1))
        chart(fig, 380)

# ------------------------------------------------------------
# 2. REVENUE & PRODUCT
# ------------------------------------------------------------
elif page == "Revenue & Product":
    heading("Revenue & Product", "📊", "Understand where revenue comes from and which products combine value with risk.")
    takeaway(
        "Revenue is <b>not</b> concentrated in a handful of products — the portfolio is fairly broad. The real risk is a smaller set of high-selling products that also carry above-average return rates or have fallen below their reorder point, which the two scatter charts below surface directly.")

    p = products_f
    net_sales_v = items_f["net_line_amount"].sum()
    units_sold_v = items_f.loc[items_f["transaction_type"] == "Sale", "quantity"].sum()
    units_returned_v = -items_f.loc[items_f["transaction_type"] == "Return / Reversal", "quantity"].sum()
    return_rate_v = (units_returned_v / units_sold_v) if units_sold_v else 0

    c = st.columns(4, gap="medium")
    kpi(c[0], "💰", "Net Sales", money(net_sales_v), "Current filter selection")
    kpi(c[1], "📦", "Products", integer(p["product_id"].nunique()) if len(p) else "0",
        "With activity in current selection")
    kpi(c[2], "↩️", "Return Rate", pct(return_rate_v), "Units returned / units sold")
    kpi(c[3], "🚨", "Below Reorder", integer(p["below_reorder_flag"].sum()) if len(p) else "0",
        "Products below restock threshold")

    if p.empty:
        st.info("No products match the current filter selection.")
    else:
        a, b = st.columns(2, gap="large")
        with a:
            section("Revenue by Category", "📊")
            cat_agg = agg_by(items_f, "category").sort_values("net_sales", ascending=False)
            fig = px.bar(cat_agg, x="category", y="net_sales", title="Net Sales by Category")
            fig.update_traces(marker_color=LAV_2)
            chart(fig, 390)
        with b:
            section("Revenue Concentration", "🎯", "Top products and their cumulative revenue contribution.")
            pareto = p.sort_values("net_sales", ascending=False).head(15).copy()
            pareto["cumulative_share"] = pareto["net_sales"].cumsum() / max(p["net_sales"].sum(), 1) * 100
            fig = px.bar(pareto, x="product_name", y="net_sales", title="Top 15 Products by Net Sales")
            fig.update_traces(marker_color=LAV_1)
            fig.update_layout(xaxis_tickangle=-45, xaxis_title="", yaxis_title="Net Sales")
            chart(fig, 300)
            fig2 = px.line(pareto, x="product_name", y="cumulative_share", markers=True,
                           title="Cumulative Revenue Share (%)")
            fig2.update_traces(line=dict(color=LAV_5, width=3))
            fig2.update_layout(xaxis_tickangle=-45, xaxis_title="", yaxis_title="Cumulative Share %",
                               yaxis_range=[0, 100])
            chart(fig2, 300)

        a, b = st.columns(2, gap="large")
        with a:
            section("Sales vs Return Rate", "🔎",
                    "Each dot is one product — top-right dots sell well but also get returned often.")
            s = p[p["net_sales"] > 0].copy()
            fig = px.scatter(s, x="net_sales", y="return_rate", size="units_sold", color="category",
                             hover_name="product_name", title="Net Sales vs Return Rate")
            fig.update_yaxes(tickformat=".0%")
            chart(fig, 410)
        with b:
            section("Sales vs Stock / Reorder Ratio", "📦", "Flags high-value products running low on stock.")
            s2 = p[p["net_sales"] > 0].copy()
            fig = px.scatter(s2, x="stock_to_reorder_ratio", y="net_sales", size="units_sold", color="category",
                             hover_name="product_name", title="Stock-to-Reorder Ratio vs Net Sales")
            fig.update_xaxes(title="Stock ÷ Reorder Level (below 1 = under reorder point)")
            chart(fig, 410)

# ------------------------------------------------------------
# 3. CUSTOMER INTELLIGENCE
# ------------------------------------------------------------
elif page == "Customer Intelligence":
    heading("Customer Intelligence", "👥",
            "Identify valuable segments, customer recency patterns and geographic revenue concentration.")
    takeaway(
        "Nearly 90% of customers are repeat buyers and revenue is evenly split across segments (~22–24% each) — the customer base itself is healthy. The opportunity is in the scatter chart below: it identifies specific high-value customers who have gone quiet and are worth a win-back campaign.")

    cust = items_f.groupby(["customer_id", "segment", "customer_country"], dropna=False).agg(
        net_sales=("net_line_amount", "sum"),
        order_count=("order_id", "nunique"),
        last_order=("order_date", "max"),
    ).reset_index()
    cust["recency_adj"] = (CUTOFF_DATE - cust["last_order"]).dt.days
    cust["repeat_customer_flag"] = cust["order_count"] > 1

    c = st.columns(4, gap="medium")
    kpi(c[0], "👥", "Customers", integer(cust["customer_id"].nunique()) if len(cust) else "0", "Current selection")
    kpi(c[1], "💰", "Customer Net Sales", money(cust["net_sales"].sum()) if len(cust) else "₹0",
        "Total for current selection")
    kpi(c[2], "🔁", "Repeat Customers", integer(cust["repeat_customer_flag"].sum()) if len(cust) else "0",
        "More than one order in selection")
    kpi(c[3], "⏳", "Avg Recency", integer(cust["recency_adj"].mean()) if len(cust) else "—",
        "Days since last order in selection")

    if cust.empty:
        st.info("No customers match the current filter selection.")
    else:
        a, b = st.columns(2, gap="large")
        with a:
            section("Segment Contribution", "🎯")
            seg = cust.groupby("segment", as_index=False)["net_sales"].sum().sort_values("net_sales", ascending=False)
            fig = px.bar(seg, x="segment", y="net_sales", title="Net Sales by Customer Segment")
            fig.update_traces(marker_color=LAV_2)
            chart(fig, 390)
        with b:
            section("Customer Value × Recency", "⏳",
                    "Recency and sales both reflect only orders matching the current filter.")
            s = cust[cust["net_sales"] > 0].copy()
            fig = px.scatter(s, x="recency_adj", y="net_sales", size="order_count", color="segment",
                             hover_name="customer_id", title="Customer Value vs Days Since Last Order")
            fig.update_xaxes(title="Days Since Last Order (in selection)")
            chart(fig, 390)

        section("Global Customer Revenue", "🌍", "Revenue by customer country, for the current filter selection.")
        country_agg = cust.groupby("customer_country", as_index=False)["net_sales"].sum().rename(
            columns={"customer_country": "country"})
        country_agg = country_agg.dropna(subset=["country"])
        if country_agg.empty:
            st.info("No country data available for the current filter selection.")
        else:
            map_fig = px.choropleth(country_agg, locations="country", locationmode="country names", color="net_sales",
                                    hover_name="country", color_continuous_scale=LAVENDER_CONTINUOUS,
                                    title="Global Customer Revenue")
            map_fig.update_geos(bgcolor="#120c1f", showland=True, landcolor="#1d1633", showocean=True,
                                oceancolor="#120c1f", showcountries=True, countrycolor="#3d3260", showframe=False)
            map_fig.update_layout(paper_bgcolor="#120c1f", plot_bgcolor="#120c1f", font_color="#ece6fb",
                                  margin=dict(l=0, r=0, t=55, b=0), height=470)
            st.plotly_chart(map_fig, width="stretch", config=CHART_CONFIG)

# ------------------------------------------------------------
# 4. INVENTORY & WAREHOUSE
# ------------------------------------------------------------
elif page == "Inventory & Warehouse":
    heading("Inventory & Warehouse", "🏭",
            "Compare inventory footprint with sales demand and highlight potential stock pressure.")
    takeaway(
        "Stock is measurably misallocated: warehouses that are under-stocked relative to their sales also carry more low-stock items. Moving stock from over-stocked to under-stocked warehouses — rather than buying more inventory — is the fastest fix.")

    w_stock = inv_f.groupby("warehouse_name", as_index=False).agg(
        total_stock=("stock_quantity", "sum"),
        low_stock_items=("stock_status", lambda x: (x == "Below Reorder Level").sum()),
    )
    w_sales = items_f.groupby("warehouse_name", as_index=False)["net_line_amount"].sum().rename(
        columns={"net_line_amount": "net_sales"})
    w = w_stock.merge(w_sales, on="warehouse_name", how="outer").fillna(0)
    w["stock_share"] = w["total_stock"] / max(w["total_stock"].sum(), 1)
    w["sales_share"] = w["net_sales"] / max(w["net_sales"].sum(), 1)
    w["gap"] = w["sales_share"] - w["stock_share"]

    p = products_f

    company_total = items["net_line_amount"].sum()
    sales_share_v = (w["net_sales"].sum() / company_total) if company_total else 0

    c = st.columns(4, gap="medium")
    kpi(c[0], "📦", "Total Stock", integer(w["total_stock"].sum()) if len(w) else "0", "Units in current selection")
    kpi(c[1], "🏭", "Warehouses", integer(w["warehouse_name"].nunique()) if len(w) else "0", "In current selection")
    kpi(c[2], "🚨", "Low-stock Items", integer(w["low_stock_items"].sum()) if len(w) else "0", "Below reorder threshold")
    kpi(c[3], "💰", "Sales Share", pct(sales_share_v), "Of company-wide net sales")

    if w.empty:
        st.info("No warehouse data for the current filter selection.")
    else:
        a, b = st.columns(2, gap="large")
        with a:
            section("Warehouse Balance", "⚖️",
                    "Sales share minus stock share, per warehouse. Bars to the right hold less stock than their sales justify (stockout risk); bars to the left hold more stock than they sell (tied-up capital).")
            wb = w.sort_values("gap")
            fig = px.bar(wb, x="gap", y="warehouse_name", orientation="h",
                         color=wb["gap"] > 0,
                         color_discrete_map={True: LAV_WARN, False: LAV_2},
                         title="Sales Share − Stock Share, by Warehouse")
            fig.update_layout(showlegend=False, xaxis_tickformat="+.1%", xaxis_title="Sales share − Stock share",
                              yaxis_title="")
            fig.add_vline(x=0, line_color="rgba(196,181,253,.4)")
            chart(fig, 620)
        with b:
            section("Imbalance Drives Low Stock", "🔎",
                    "Warehouses more under-stocked relative to demand tend to carry more low-stock items.")
            fig = px.scatter(wb, x="gap", y="low_stock_items", size="total_stock", hover_name="warehouse_name",
                             title="Allocation Gap vs Low-Stock Items")
            fig.update_layout(xaxis_tickformat="+.1%", xaxis_title="Sales share − Stock share",
                              yaxis_title="Low-Stock Items")
            fig.add_vline(x=0, line_color="rgba(196,181,253,.4)")
            chart(fig, 300)
            if wb["gap"].nunique() > 1 and wb["low_stock_items"].nunique() > 1:
                corr = wb["gap"].corr(wb["low_stock_items"])
                st.markdown(
                    f'<div class="insight">📌 Correlation between allocation gap and low-stock items: <b>{corr:.2f}</b> — the more under-stocked a warehouse is relative to its sales, the more items in it run low.</div>',
                    unsafe_allow_html=True)

        a, b = st.columns(2, gap="large")
        with a:
            section("High-value Inventory Exposure", "🚨",
                    "Products combining commercial value with below-reorder status.")
            risk = p[p["below_reorder_flag"] == True].sort_values("net_sales", ascending=False).head(15)
            if risk.empty:
                st.info("No below-reorder products in the current filter selection.")
            else:
                fig = px.bar(risk, x="net_sales", y="product_name", orientation="h", color="category",
                             title="Top Below-Reorder Products by Net Sales")
                chart(fig, 410)
        with b:
            section("Stock vs Commercial Value", "🔎")
            s = p[p["net_sales"] > 0].copy()
            if s.empty:
                st.info("No data for the current filter selection.")
            else:
                fig = px.scatter(s, x="current_stock", y="net_sales", size="units_sold", color="category",
                                 hover_name="product_name", title="Current Stock vs Net Sales")
                chart(fig, 410)

# ------------------------------------------------------------
# 5. SUPPLIER & LOGISTICS
# ------------------------------------------------------------
elif page == "Supplier & Logistics":
    heading("Supplier & Logistics", "🚚", "Review supplier contribution and carrier cost-service patterns.")
    takeaway(
        "Supplier rating and sales volume barely correlate, and a meaningful share of sales runs through suppliers rated below 3/5 — a concentration risk if any one of them fails to deliver. Separately, delivery times vary across carriers once anomalous shipments are excluded.")

    sup = items_f.groupby(["supplier_name", "supplier_country", "supplier_rating"], dropna=False).agg(
        net_sales=("net_line_amount", "sum"),
        product_count=("product_id", "nunique"),
    ).reset_index()

    c = st.columns(4, gap="medium")
    kpi(c[0], "🏭", "Suppliers", integer(sup["supplier_name"].nunique()) if len(sup) else "0", "Current selection")
    kpi(c[1], "💰", "Supplier Net Sales", money(sup["net_sales"].sum()) if len(sup) else "₹0",
        "Associated commercial value")
    kpi(c[2], "🚚", "Carriers", integer(carrier_stats["carrier"].nunique()) if len(carrier_stats) else "0",
        "Shipment carriers in selection")
    kpi(c[3], "💸", "Shipping Cost", money(carrier_stats["total_shipping_cost"].sum()) if len(carrier_stats) else "₹0",
        "Total shipping cost in selection")

    if sup.empty:
        st.info("No supplier data for the current filter selection.")
    else:
        a, b = st.columns(2, gap="large")
        with a:
            section("Supplier Contribution × Rating", "⭐")
            fig = px.scatter(sup, x="supplier_rating", y="net_sales", size="product_count", color="supplier_country",
                             hover_name="supplier_name", title="Supplier Rating vs Net Sales")
            chart(fig, 400)
        with b:
            section("Carrier Cost × Delivery Time", "🚚",
                    "Delivery time excludes shipments with implausible delivery windows (>60 days).")
            if carrier_stats.empty:
                st.info("No shipments match the current filter selection.")
            else:
                fig = px.scatter(carrier_stats, x="average_shipping_cost", y="avg_delivery_days", size="shipment_count",
                                 hover_name="carrier", title="Average Shipping Cost vs Delivery Days (corrected)")
                fig.update_yaxes(title="Avg Delivery Days (corrected)")
                chart(fig, 400)

        a, b = st.columns(2, gap="large")
        with a:
            section("Supplier Revenue Concentration", "🎯")
            top = sup.sort_values("net_sales", ascending=False).head(12)
            fig = px.bar(top.sort_values("net_sales"), x="net_sales", y="supplier_name", orientation="h",
                         title="Top Suppliers by Net Sales")
            fig.update_traces(marker_color=LAV_2)
            chart(fig, 400)
        with b:
            section("Net Sales Share by Supplier Rating", "⭐",
                    "Rating and revenue don't line up — a meaningful share of sales sits with lower-rated suppliers.")
            sr = sup.dropna(subset=["supplier_rating"]).copy()
            if sr.empty:
                st.info("No supplier rating data for the current filter selection.")
            else:
                band_labels = ["1–2 (Poor)", "2–3 (Below Avg)", "3–4 (Good)", "4–5 (Excellent)"]
                sr["rating_band"] = pd.cut(sr["supplier_rating"], [0, 2, 3, 4, 5], labels=band_labels)
                band = sr.groupby("rating_band", observed=True, as_index=False)["net_sales"].sum()
                band_colors = {"1–2 (Poor)": LAV_6, "2–3 (Below Avg)": LAV_3, "3–4 (Good)": LAV_1,
                               "4–5 (Excellent)": "#e9d5ff"}
                fig = px.pie(band, names="rating_band", values="net_sales", hole=0.68,
                             color="rating_band", color_discrete_map=band_colors,
                             category_orders={"rating_band": band_labels},
                             title="Net Sales Share by Supplier Rating Band")
                fig.update_traces(textinfo="percent+label", marker=dict(line=dict(color="#150f24", width=1)))
                chart(fig, 400)

        a, b = st.columns(2, gap="large")
        with a:
            section("Delivery Time Distribution", "⏱️", "Most shipments arrive quickly, but some take much longer.")
            if sh_valid.empty:
                st.info("No shipments match the current filter selection.")
            else:
                fig = px.histogram(sh_valid, x="delivery_days", nbins=30,
                                   title="Delivery Days Distribution (excl. anomalies >60 days)")
                fig.update_traces(marker_color=LAV_2)
                fig.add_vline(x=14, line_dash="dash", line_color=LAV_WARN, annotation_text="14 days")
                fig.update_layout(xaxis_title="Delivery Days", yaxis_title="Shipments")
                chart(fig, 380)
        with b:
            section("Late Shipments by Carrier", "🚨",
                    "Share of each carrier's shipments delivered more than 14 days after dispatch.")
            cr = carrier_stats.dropna(subset=["late_14d_rate"]).sort_values("late_14d_rate", ascending=False)
            if cr.empty:
                st.info("No shipment data for the current filter selection.")
            else:
                fig = px.bar(cr, x="carrier", y="late_14d_rate", title="% Shipments Delivered Later Than 14 Days")
                fig.update_traces(marker_color=LAV_WARN)
                fig.update_yaxes(tickformat=".0%", title="% Late (>14 days)")
                chart(fig, 380)

# ------------------------------------------------------------
# 6. DATA QUALITY & ACTION
# ------------------------------------------------------------
elif page == "Data Quality & Action":
    heading("Data Quality & Action", "🎯",
            "Validate analytical confidence and surface evidence-based areas that deserve investigation.")
    takeaway(
        "About a quarter of reported net sales sits in Cancelled or Returned orders, and a large share of Pending orders are over a year old and unlikely to ever convert. Treat headline revenue figures as directional until these are reconciled with order status.")

    om = order_meta_f
    complete_n = int((om["revenue_completeness_status"] == "Complete").sum())
    partial_n = int((om["revenue_completeness_status"] == "Partial").sum())
    nodetail_n = int((om["revenue_completeness_status"] == "No Order Details").sum())
    anomaly_n = int(om["delivery_anomaly_flag"].fillna(0).astype(int).sum())

    c = st.columns(4, gap="medium")
    kpi(c[0], "✅", "Complete Revenue", integer(complete_n), "Orders with complete revenue detail")
    kpi(c[1], "⚠️", "Partial Revenue", integer(partial_n), "Orders with partial detail")
    kpi(c[2], "❌", "No Detail", integer(nodetail_n), "Orders without usable detail")
    kpi(c[3], "🚨", "Delivery Anomalies", integer(anomaly_n), "Shipment timing anomalies")

    a, b = st.columns(2, gap="large")
    with a:
        section("Revenue Data Confidence", "🔎")
        qdf = pd.DataFrame({
            "revenue_completeness_status": ["Complete", "Partial", "No Order Details"],
            "orders": [complete_n, partial_n, nodetail_n],
        })
        qdf = qdf[qdf["orders"] > 0]
        if qdf.empty:
            st.info("No orders match the current filter selection.")
        else:
            fig = px.funnel(qdf, y="revenue_completeness_status", x="orders", title="Revenue Completeness")
            fig.update_traces(marker_color=LAV_2)
            chart(fig, 400)
    with b:
        section("Net Sales by Order Status", "📋",
                "About a quarter of reported net sales sits in Cancelled or Returned orders.")
        os_agg = agg_by(items_f, "order_status").sort_values("net_sales", ascending=False)
        if os_agg.empty:
            st.info("No orders match the current filter selection.")
        else:
            os_agg["is_final"] = os_agg["order_status"].isin(["Cancelled", "Returned"])
            fig = px.bar(os_agg, x="order_status", y="net_sales", color="is_final",
                         color_discrete_map={True: LAV_WARN, False: LAV_2},
                         title="Net Sales by Order Status")
            fig.update_layout(showlegend=False, yaxis_title="Net Sales")
            chart(fig, 400)

    section("Pending Order Aging", "⏳",
            "How long orders have sat in Pending status, as of the last fully-recorded month. Older pending orders are less likely to ever convert.")
    ord_level = items_f.dropna(subset=["order_date"]).groupby("order_id", as_index=False).agg(
        order_date=("order_date", "first"), order_status=("order_status", "first"),
        net_sales=("net_line_amount", "sum"))
    pend = ord_level[(ord_level["order_status"] == "Pending") & (ord_level["order_date"] <= CUTOFF_DATE)].copy()
    if pend.empty:
        st.info("No pending orders match the current filter selection.")
    else:
        pend["age_days"] = (CUTOFF_DATE - pend["order_date"]).dt.days
        bins = [-1, 30, 90, 180, 365, 10_000]
        labels = ["0–30d", "31–90d", "91–180d", "181–365d", "365d+"]
        pend["bucket"] = pd.cut(pend["age_days"], bins=bins, labels=labels)
        agg = pend.groupby("bucket", observed=True, as_index=False).agg(orders=("order_id", "count"),
                                                                        net_sales=("net_sales", "sum"))
        fig = px.bar(agg, x="bucket", y="net_sales", text="orders", title="Pending Order Value by Age Bucket")
        fig.update_traces(marker_color=LAV_3, textposition="outside")
        fig.update_layout(xaxis_title="Time Since Order Placed", yaxis_title="Net Sales Tied Up")
        chart(fig, 380)

    section("Investigation Priorities", "🚦",
            "Evidence-based shortlist; these are areas to investigate, not automatic business decisions. Thresholds compare against the company-wide average, so this stays meaningful even when filtered.")
    if actions_f.empty:
        st.info("No flagged products in the current filter selection.")
    else:
        action_counts = actions_f.groupby("action_area", as_index=False).agg(net_sales=("net_sales", "sum"),
                                                                             products=("product_id",
                                                                                       "nunique")).sort_values(
            "net_sales", ascending=False)
        fig = px.bar(action_counts, x="action_area", y="net_sales", text="products",
                     title="Commercial Exposure by Action Area")
        fig.update_traces(marker_color=LAV_1, textposition="outside")
        chart(fig, 390)

st.markdown(
    '<div style="text-align:center;color:#8b7fae;font-size:.68rem;margin-top:2rem;">Supply Chain Intelligence • Analytical database • Streamlit presentation version</div>',
    unsafe_allow_html=True)