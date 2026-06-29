"""
etl_pipeline.py
══════════════════════════════════════════════════════════════
End-to-End ETL Pipeline — Create Data Warehouse Project
  Extract  → seed_data/customers.csv, products.csv, orders.csv
  Transform → clean, validate, deduplicate, enrich
  Load      → SQLite data warehouse (star schema)
              DimCustomer | DimCategory | DimProduct | DimDate | FactOrder

Usage:
    python etl_pipeline.py

Output:
    data_warehouse.db   — SQLite database
    etl_errors.log      — Data quality issues detected
══════════════════════════════════════════════════════════════
"""

import os
import sqlite3
import pandas as pd
from datetime import datetime

# ── Paths ──────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
DB_FILE    = os.path.join(BASE_DIR, "data_warehouse.db")
LOG_FILE   = os.path.join(BASE_DIR, "etl_errors.log")
SEED_DIR   = os.path.join(BASE_DIR, "seed_data")


# ── Logger ─────────────────────────────────────────────────
def log_error(category: str, message: str):
    """Append a data quality error to etl_errors.log."""
    ts   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{category}] {message}\n"
    print(f"  ⚠️  {line.strip()}")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line)

def log_info(message: str):
    print(f"  ✅ {message}")


# ══════════════════════════════════════════════════════════
# STEP 1 — EXTRACT
# ══════════════════════════════════════════════════════════
def extract() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    print("\n📂 [EXTRACT] Reading CSV seed data …")

    customers = pd.read_csv(os.path.join(SEED_DIR, "customers.csv"), encoding="utf-8-sig")
    products  = pd.read_csv(os.path.join(SEED_DIR, "products.csv"),  encoding="utf-8-sig")
    orders    = pd.read_csv(os.path.join(SEED_DIR, "orders.csv"),    encoding="utf-8-sig")

    log_info(f"Customers: {len(customers)} rows")
    log_info(f"Products:  {len(products)} rows")
    log_info(f"Orders:    {len(orders)} rows")
    return customers, products, orders


# ══════════════════════════════════════════════════════════
# STEP 2 — TRANSFORM
# ══════════════════════════════════════════════════════════
def transform(customers: pd.DataFrame,
              products:  pd.DataFrame,
              orders:    pd.DataFrame) -> dict:
    print("\n🔄 [TRANSFORM] Cleaning and enriching data …")

    # ── DimCustomer ────────────────────────────────────────
    dim_customer = customers.copy()
    dim_customer.columns = dim_customer.columns.str.strip()
    dim_customer["FullName"] = dim_customer["first_name"].str.strip() + " " + dim_customer["last_name"].str.strip()

    for _, row in dim_customer.iterrows():
        if pd.isnull(row.get("email")) or str(row.get("email", "")).strip() == "":
            log_error("CUSTOMER ERROR", f"Missing email: {row['FullName']}")

    dim_customer = dim_customer.rename(columns={
        "customer_id": "CustomerKey",
        "email":       "Email",
        "city":        "City",
        "signup_date": "SignupDate",
    })[["CustomerKey", "FullName", "Email", "City", "SignupDate"]]
    dim_customer = dim_customer.drop_duplicates(subset="CustomerKey")
    log_info(f"DimCustomer: {len(dim_customer)} records")

    # ── DimCategory ────────────────────────────────────────
    categories = products["category_name"].str.strip().drop_duplicates().reset_index(drop=True)
    dim_category = pd.DataFrame({
        "CategoryKey":  range(1, len(categories) + 1),
        "CategoryName": categories,
    })
    cat_map = dict(zip(dim_category["CategoryName"], dim_category["CategoryKey"]))
    log_info(f"DimCategory: {len(dim_category)} records")

    # ── DimProduct ─────────────────────────────────────────
    dim_product = products.copy()
    dim_product.columns = dim_product.columns.str.strip()

    for _, row in dim_product.iterrows():
        if pd.isnull(row.get("price")) or row.get("price", 0) <= 0:
            log_error("PRODUCT ERROR", f"Invalid price for ProductKey {row['product_id']}: {row.get('price')}")
        if pd.isnull(row.get("stock")) or row.get("stock", 0) < 0:
            log_error("PRODUCT ERROR", f"Negative/missing stock for ProductKey {row['product_id']}")

    dim_product["CategoryKey"] = dim_product["category_name"].str.strip().map(cat_map)
    dim_product = dim_product.rename(columns={
        "product_id":   "ProductKey",
        "product_name": "ProductName",
        "price":        "Price",
        "stock":        "Stock",
    })[["ProductKey", "ProductName", "Price", "Stock", "CategoryKey"]]
    dim_product = dim_product.drop_duplicates(subset="ProductKey")
    log_info(f"DimProduct: {len(dim_product)} records")

    # ── DimDate ────────────────────────────────────────────
    order_dates = pd.to_datetime(orders["order_date"], errors="coerce").dropna().dt.normalize().unique()
    date_df     = pd.DataFrame({"FullDate": sorted(order_dates)})
    date_df["DateKey"]   = date_df["FullDate"].dt.strftime("%Y%m%d").astype(int)
    date_df["Year"]      = date_df["FullDate"].dt.year
    date_df["Month"]     = date_df["FullDate"].dt.month
    date_df["Day"]       = date_df["FullDate"].dt.day
    date_df["Quarter"]   = date_df["FullDate"].dt.quarter
    date_df["MonthName"] = date_df["FullDate"].dt.strftime("%B")
    date_df["DayOfWeek"] = date_df["FullDate"].dt.day_name()
    date_df["FullDate"]  = date_df["FullDate"].dt.strftime("%Y-%m-%d")
    dim_date = date_df[["DateKey","FullDate","Year","Month","Day","Quarter","MonthName","DayOfWeek"]]
    log_info(f"DimDate: {len(dim_date)} records")

    # ── FactOrder ──────────────────────────────────────────
    fact = orders.copy()
    fact.columns = fact.columns.str.strip()
    fact["OrderDate"] = pd.to_datetime(fact["order_date"], errors="coerce")

    for idx, row in fact.iterrows():
        if pd.isnull(row["OrderDate"]):
            log_error("ORDER ERROR", f"Invalid order_date for OrderKey {row['order_id']}")
        if str(row.get("payment_type","")).strip() not in [
            "Credit Card","Debit Card","Cash on Delivery","Bank Transfer","UPI"
        ]:
            log_error("ORDER ERROR", f"Unexpected payment type '{row.get('payment_type')}' on OrderKey {row['order_id']}")

    fact = fact.dropna(subset=["OrderDate"])
    date_key_map = dict(zip(dim_date["FullDate"], dim_date["DateKey"]))
    fact["DateKey"] = fact["OrderDate"].dt.strftime("%Y-%m-%d").map(date_key_map)

    # TotalAmount = Price × Quantity
    price_map = dict(zip(dim_product["ProductKey"], dim_product["Price"]))
    fact["TotalAmount"] = fact.apply(
        lambda r: price_map.get(r["product_id"], 0) * r["quantity"], axis=1
    )

    fact_order = fact.rename(columns={
        "order_id":    "OrderKey",
        "customer_id": "CustomerKey",
        "product_id":  "ProductKey",
        "quantity":    "Quantity",
        "payment_type":"PaymentType",
        "status":      "Status",
        "updated_at":  "UpdatedAt",
    })
    fact_order["OrderDate"] = fact_order["OrderDate"].dt.strftime("%Y-%m-%d")
    fact_order = fact_order[[
        "OrderKey","CustomerKey","ProductKey","DateKey",
        "Quantity","OrderDate","PaymentType","Status","UpdatedAt","TotalAmount"
    ]].drop_duplicates(subset="OrderKey")
    log_info(f"FactOrder: {len(fact_order)} records")

    return {
        "DimCustomer": dim_customer,
        "DimCategory": dim_category,
        "DimProduct":  dim_product,
        "DimDate":     dim_date,
        "FactOrder":   fact_order,
    }


# ══════════════════════════════════════════════════════════
# STEP 3 — LOAD
# ══════════════════════════════════════════════════════════
def load(tables: dict):
    print(f"\n💾 [LOAD] Writing to SQLite: {DB_FILE}")
    conn = sqlite3.connect(DB_FILE)
    cur  = conn.cursor()

    # Create schema
    with open(os.path.join(BASE_DIR, "schema.sql"), "r") as f:
        cur.executescript(f.read())

    # Drop existing data (idempotent re-run)
    for tbl in ["FactOrder","DimProduct","DimCustomer","DimDate","DimCategory"]:
        cur.execute(f"DELETE FROM {tbl}")

    load_order = ["DimCategory","DimCustomer","DimProduct","DimDate","FactOrder"]
    for tbl in load_order:
        df = tables[tbl]
        df.to_sql(tbl, conn, if_exists="append", index=False)
        count = cur.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
        log_info(f"Loaded {count:>3} rows → {tbl}")

    conn.commit()
    conn.close()
    print(f"\n  ✅ Data warehouse ready: {DB_FILE}")


# ══════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════
if __name__ == "__main__":
    # Clear previous log
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write(f"ETL Run: {datetime.now()}\n{'='*60}\n")

    print("=" * 55)
    print("  CREATE DATA WAREHOUSE — ETL PIPELINE")
    print("=" * 55)

    customers, products, orders = extract()
    tables = transform(customers, products, orders)
    load(tables)

    print("\n🏁 ETL completed successfully! Run test_pipeline.py to validate.")
