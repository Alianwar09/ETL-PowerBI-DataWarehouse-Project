-- analysis_queries.sql
-- Author: Ali Anwar
-- Purpose: Analytical SQL queries for Power BI visualizations
--          and reporting from the data warehouse (SQLite).
-- Run these queries after etl_pipeline.py has populated the database.

------------------------------------------------------------------------
-- 1. Top 5 customers with the highest number of orders
------------------------------------------------------------------------
SELECT
    c.FullName        AS Customer,
    c.City,
    COUNT(o.OrderKey) AS TotalOrders
FROM FactOrder o
JOIN DimCustomer c ON o.CustomerKey = c.CustomerKey
GROUP BY c.FullName, c.City
ORDER BY TotalOrders DESC
LIMIT 5;

------------------------------------------------------------------------
-- 2. Top-selling products by quantity sold
------------------------------------------------------------------------
SELECT
    p.ProductName,
    cat.CategoryName,
    SUM(o.Quantity)              AS TotalQuantity,
    ROUND(SUM(o.TotalAmount), 2) AS TotalRevenue
FROM FactOrder o
JOIN DimProduct  p   ON o.ProductKey  = p.ProductKey
JOIN DimCategory cat ON p.CategoryKey = cat.CategoryKey
GROUP BY p.ProductName, cat.CategoryName
ORDER BY TotalQuantity DESC;

------------------------------------------------------------------------
-- 3. Order count grouped by customer city
------------------------------------------------------------------------
SELECT
    c.City,
    COUNT(o.OrderKey)            AS OrderCount,
    ROUND(SUM(o.TotalAmount), 2) AS CityRevenue
FROM FactOrder o
JOIN DimCustomer c ON o.CustomerKey = c.CustomerKey
GROUP BY c.City
ORDER BY OrderCount DESC;

------------------------------------------------------------------------
-- 4. Monthly order trends
------------------------------------------------------------------------
SELECT
    d.Year,
    d.Month,
    d.MonthName,
    COUNT(o.OrderKey)            AS TotalOrders,
    SUM(o.Quantity)              AS TotalUnits,
    ROUND(SUM(o.TotalAmount), 2) AS MonthlyRevenue
FROM FactOrder o
JOIN DimDate d ON o.DateKey = d.DateKey
GROUP BY d.Year, d.Month, d.MonthName
ORDER BY d.Year, d.Month;

------------------------------------------------------------------------
-- 5. Orders grouped by payment method
------------------------------------------------------------------------
SELECT
    o.PaymentType,
    COUNT(*)                     AS OrderCount,
    ROUND(SUM(o.TotalAmount), 2) AS Revenue
FROM FactOrder o
GROUP BY o.PaymentType
ORDER BY OrderCount DESC;

------------------------------------------------------------------------
-- 6. Sales by product category
------------------------------------------------------------------------
SELECT
    cat.CategoryName,
    SUM(o.Quantity)              AS TotalUnitsSold,
    ROUND(SUM(o.TotalAmount), 2) AS TotalRevenue
FROM FactOrder o
JOIN DimProduct  p   ON o.ProductKey  = p.ProductKey
JOIN DimCategory cat ON p.CategoryKey = cat.CategoryKey
GROUP BY cat.CategoryName
ORDER BY TotalRevenue DESC;

------------------------------------------------------------------------
-- 7. Order status distribution
------------------------------------------------------------------------
SELECT
    Status,
    COUNT(*) AS OrderCount,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM FactOrder), 1) AS Percentage
FROM FactOrder
GROUP BY Status
ORDER BY OrderCount DESC;

------------------------------------------------------------------------
-- 8. Quarterly revenue summary
------------------------------------------------------------------------
SELECT
    d.Year,
    d.Quarter,
    COUNT(o.OrderKey)            AS TotalOrders,
    ROUND(SUM(o.TotalAmount), 2) AS QuarterlyRevenue
FROM FactOrder o
JOIN DimDate d ON o.DateKey = d.DateKey
GROUP BY d.Year, d.Quarter
ORDER BY d.Year, d.Quarter;
