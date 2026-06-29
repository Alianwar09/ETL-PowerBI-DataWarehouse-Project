"""
test_pipeline.py
══════════════════════════════════════════════════════════════
Validates the data warehouse after ETL.
Checks row counts, referential integrity, data quality,
and expected business logic.

Usage:
    python test_pipeline.py
══════════════════════════════════════════════════════════════
"""

import os
import sqlite3

DB_FILE  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_warehouse.db")
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "etl_errors.log")

passed = 0
failed = 0

def check(test_name: str, condition: bool, detail: str = ""):
    global passed, failed
    if condition:
        print(f"  ✅ [PASS] {test_name}")
        passed += 1
    else:
        print(f"  ❌ [FAIL] {test_name}" + (f" — {detail}" if detail else ""))
        failed += 1


# ── Connect ────────────────────────────────────────────────
print("\n" + "=" * 55)
print("  CREATE DATA WAREHOUSE — TEST SUITE")
print("=" * 55)

if not os.path.exists(DB_FILE):
    print("❌ data_warehouse.db not found. Run etl_pipeline.py first.")
    exit(1)

conn   = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

print("\n📋 TEST 1: DATABASE CONNECTION")
check("SQLite database exists and is accessible", True)


# ── Row count tests ────────────────────────────────────────
print("\n📋 TEST 2: TABLE ROW COUNTS")

tables = ["DimCustomer", "DimCategory", "DimProduct", "DimDate", "FactOrder"]
for tbl in tables:
    count = cursor.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
    check(f"{tbl} has data (count={count})", count > 0, f"{tbl} is empty")


# ── Referential integrity ──────────────────────────────────
print("\n📋 TEST 3: REFERENTIAL INTEGRITY")

orphan_customers = cursor.execute("""
    SELECT COUNT(*) FROM FactOrder
    WHERE CustomerKey NOT IN (SELECT CustomerKey FROM DimCustomer)
""").fetchone()[0]
check("No orphan CustomerKeys in FactOrder", orphan_customers == 0,
      f"{orphan_customers} orphan customer references")

orphan_products = cursor.execute("""
    SELECT COUNT(*) FROM FactOrder
    WHERE ProductKey NOT IN (SELECT ProductKey FROM DimProduct)
""").fetchone()[0]
check("No orphan ProductKeys in FactOrder", orphan_products == 0,
      f"{orphan_products} orphan product references")

orphan_categories = cursor.execute("""
    SELECT COUNT(*) FROM DimProduct
    WHERE CategoryKey NOT IN (SELECT CategoryKey FROM DimCategory)
""").fetchone()[0]
check("No orphan CategoryKeys in DimProduct", orphan_categories == 0,
      f"{orphan_categories} orphan category references")


# ── Data quality ───────────────────────────────────────────
print("\n📋 TEST 4: DATA QUALITY")

null_names = cursor.execute("SELECT COUNT(*) FROM DimCustomer WHERE FullName IS NULL OR FullName = ''").fetchone()[0]
check("No null/empty FullName in DimCustomer", null_names == 0, f"{null_names} null names")

null_prices = cursor.execute("SELECT COUNT(*) FROM DimProduct WHERE Price IS NULL OR Price <= 0").fetchone()[0]
check("All products have valid Price > 0", null_prices == 0, f"{null_prices} invalid prices")

null_qty = cursor.execute("SELECT COUNT(*) FROM FactOrder WHERE Quantity IS NULL OR Quantity <= 0").fetchone()[0]
check("All orders have valid Quantity > 0", null_qty == 0, f"{null_qty} invalid quantities")

null_date = cursor.execute("SELECT COUNT(*) FROM FactOrder WHERE OrderDate IS NULL").fetchone()[0]
check("No null OrderDates in FactOrder", null_date == 0, f"{null_date} null dates")

dupe_orders = cursor.execute("""
    SELECT COUNT(*) FROM (
        SELECT OrderKey, COUNT(*) AS c FROM FactOrder GROUP BY OrderKey HAVING c > 1
    )
""").fetchone()[0]
check("No duplicate OrderKeys in FactOrder", dupe_orders == 0, f"{dupe_orders} duplicate orders")

dupe_customers = cursor.execute("""
    SELECT COUNT(*) FROM (
        SELECT CustomerKey, COUNT(*) AS c FROM DimCustomer GROUP BY CustomerKey HAVING c > 1
    )
""").fetchone()[0]
check("No duplicate CustomerKeys", dupe_customers == 0, f"{dupe_customers} duplicate customers")


# ── Business logic ─────────────────────────────────────────
print("\n📋 TEST 5: BUSINESS LOGIC")

total_amount_check = cursor.execute(
    "SELECT COUNT(*) FROM FactOrder WHERE TotalAmount IS NULL OR TotalAmount < 0"
).fetchone()[0]
check("All TotalAmount values are non-negative", total_amount_check == 0,
      f"{total_amount_check} invalid TotalAmount values")

valid_statuses = cursor.execute("""
    SELECT COUNT(*) FROM FactOrder
    WHERE Status NOT IN ('Delivered','Shipped','Processing','Cancelled')
""").fetchone()[0]
check("All order statuses are valid", valid_statuses == 0,
      f"{valid_statuses} unexpected status values")

date_link = cursor.execute("""
    SELECT COUNT(*) FROM FactOrder
    WHERE DateKey NOT IN (SELECT DateKey FROM DimDate)
""").fetchone()[0]
check("All FactOrder DateKeys exist in DimDate", date_link == 0,
      f"{date_link} unlinked date keys")


# ── Log file check ─────────────────────────────────────────
print("\n📋 TEST 6: ETL ERROR LOG")
if os.path.exists(LOG_FILE):
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        error_lines = [l for l in f if l.strip() and not l.startswith("ETL Run") and "===" not in l]
    check(f"etl_errors.log is clean ({len(error_lines)} issues logged)",
          len(error_lines) == 0,
          f"{len(error_lines)} data quality issues — review etl_errors.log")
else:
    check("etl_errors.log exists", False, "File not found")


# ── Summary ────────────────────────────────────────────────
conn.close()
total = passed + failed
print(f"\n{'='*55}")
print(f"  RESULTS: {passed}/{total} tests passed", "🎉" if failed == 0 else "⚠️")
print(f"{'='*55}\n")

if failed > 0:
    print("  Fix the failing tests and re-run etl_pipeline.py\n")
