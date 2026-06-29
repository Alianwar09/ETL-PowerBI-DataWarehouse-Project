"""
procedures.py
══════════════════════════════════════════════════════════════
Analytical query functions against the data warehouse.
These simulate stored procedures — run after etl_pipeline.py.

Usage:
    python procedures.py
══════════════════════════════════════════════════════════════
"""

import os
import sqlite3
import pandas as pd

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_warehouse.db")


def get_connection() -> sqlite3.Connection:
    if not os.path.exists(DB_FILE):
        raise FileNotFoundError("data_warehouse.db not found. Run etl_pipeline.py first.")
    return sqlite3.connect(DB_FILE)


def top_customers_by_orders(n: int = 5) -> pd.DataFrame:
    """Top N customers by total number of orders."""
    conn = get_connection()
    df = pd.read_sql_query(f"""
        SELECT c.FullName AS Customer,
               COUNT(o.OrderKey) AS TotalOrders
        FROM FactOrder o
        JOIN DimCustomer c ON o.CustomerKey = c.CustomerKey
        GROUP BY c.FullName
        ORDER BY TotalOrders DESC
        LIMIT {n}
    """, conn)
    conn.close()
    return df


def order_distribution_by_city() -> pd.DataFrame:
    """Order count per city."""
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT c.City,
               COUNT(o.OrderKey) AS OrderCount
        FROM FactOrder o
        JOIN DimCustomer c ON o.CustomerKey = c.CustomerKey
        GROUP BY c.City
        ORDER BY OrderCount DESC
    """, conn)
    conn.close()
    return df


def monthly_order_trend() -> pd.DataFrame:
    """Orders and total units sold by month."""
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT d.Year,
               d.Month,
               d.MonthName,
               COUNT(o.OrderKey)  AS TotalOrders,
               SUM(o.Quantity)    AS TotalUnits,
               ROUND(SUM(o.TotalAmount), 2) AS Revenue
        FROM FactOrder o
        JOIN DimDate d ON o.DateKey = d.DateKey
        GROUP BY d.Year, d.Month, d.MonthName
        ORDER BY d.Year, d.Month
    """, conn)
    conn.close()
    return df


def sales_by_category() -> pd.DataFrame:
    """Total quantity sold per category."""
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT cat.CategoryName,
               SUM(o.Quantity)              AS TotalUnitsSold,
               ROUND(SUM(o.TotalAmount), 2) AS TotalRevenue
        FROM FactOrder o
        JOIN DimProduct p   ON o.ProductKey  = p.ProductKey
        JOIN DimCategory cat ON p.CategoryKey = cat.CategoryKey
        GROUP BY cat.CategoryName
        ORDER BY TotalRevenue DESC
    """, conn)
    conn.close()
    return df


def payment_method_breakdown() -> pd.DataFrame:
    """Order count and revenue by payment type."""
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT PaymentType,
               COUNT(*)                     AS OrderCount,
               ROUND(SUM(TotalAmount), 2)   AS Revenue
        FROM FactOrder
        GROUP BY PaymentType
        ORDER BY OrderCount DESC
    """, conn)
    conn.close()
    return df


def top_products_by_quantity(n: int = 5) -> pd.DataFrame:
    """Top N products by units sold."""
    conn = get_connection()
    df = pd.read_sql_query(f"""
        SELECT p.ProductName,
               cat.CategoryName,
               SUM(o.Quantity)              AS TotalQuantity,
               ROUND(SUM(o.TotalAmount), 2) AS Revenue
        FROM FactOrder o
        JOIN DimProduct  p   ON o.ProductKey  = p.ProductKey
        JOIN DimCategory cat ON p.CategoryKey = cat.CategoryKey
        GROUP BY p.ProductName, cat.CategoryName
        ORDER BY TotalQuantity DESC
        LIMIT {n}
    """, conn)
    conn.close()
    return df


# ── Run all when executed directly ─────────────────────────
if __name__ == "__main__":
    separator = "\n" + "─" * 45

    print("📊 TOP 5 CUSTOMERS BY ORDERS")
    print(top_customers_by_orders().to_string(index=False))

    print(separator)
    print("🌍 ORDER DISTRIBUTION BY CITY")
    print(order_distribution_by_city().to_string(index=False))

    print(separator)
    print("📅 MONTHLY ORDER TREND")
    print(monthly_order_trend().to_string(index=False))

    print(separator)
    print("🗂️  SALES BY CATEGORY")
    print(sales_by_category().to_string(index=False))

    print(separator)
    print("💳 PAYMENT METHOD BREAKDOWN")
    print(payment_method_breakdown().to_string(index=False))

    print(separator)
    print("📦 TOP 5 PRODUCTS BY QUANTITY")
    print(top_products_by_quantity().to_string(index=False))
