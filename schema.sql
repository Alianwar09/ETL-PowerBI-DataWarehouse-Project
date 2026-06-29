-- =============================================================
-- schema.sql
-- Data Warehouse Schema — Kimball Dimensional Model
-- Compatible with: SQLite (default) and MSSQL (see comments)
-- =============================================================

-- DimCategory
CREATE TABLE IF NOT EXISTS DimCategory (
    CategoryKey   INTEGER PRIMARY KEY AUTOINCREMENT,
    CategoryName  TEXT NOT NULL UNIQUE
);

-- DimProduct
CREATE TABLE IF NOT EXISTS DimProduct (
    ProductKey    INTEGER PRIMARY KEY,
    ProductName   TEXT NOT NULL,
    Price         REAL,
    Stock         INTEGER,
    CategoryKey   INTEGER,
    FOREIGN KEY (CategoryKey) REFERENCES DimCategory(CategoryKey)
);

-- DimCustomer
CREATE TABLE IF NOT EXISTS DimCustomer (
    CustomerKey   INTEGER PRIMARY KEY,
    FullName      TEXT NOT NULL,
    Email         TEXT,
    City          TEXT,
    SignupDate    TEXT
);

-- DimDate
CREATE TABLE IF NOT EXISTS DimDate (
    DateKey       INTEGER PRIMARY KEY,
    FullDate      TEXT,
    Year          INTEGER,
    Month         INTEGER,
    Day           INTEGER,
    Quarter       INTEGER,
    MonthName     TEXT,
    DayOfWeek     TEXT
);

-- FactOrder
CREATE TABLE IF NOT EXISTS FactOrder (
    OrderKey      INTEGER PRIMARY KEY,
    CustomerKey   INTEGER,
    ProductKey    INTEGER,
    DateKey       INTEGER,
    Quantity      INTEGER,
    OrderDate     TEXT,
    PaymentType   TEXT,
    Status        TEXT,
    UpdatedAt     TEXT,
    TotalAmount   REAL,
    FOREIGN KEY (CustomerKey) REFERENCES DimCustomer(CustomerKey),
    FOREIGN KEY (ProductKey)  REFERENCES DimProduct(ProductKey),
    FOREIGN KEY (DateKey)     REFERENCES DimDate(DateKey)
);

-- =============================================================
-- MSSQL equivalent (use this if connecting to SQL Server)
-- =============================================================
-- CREATE TABLE DimCategory (
--     CategoryKey  INT PRIMARY KEY IDENTITY(1,1),
--     CategoryName NVARCHAR(100) NOT NULL UNIQUE
-- );
-- CREATE TABLE DimProduct (
--     ProductKey  INT PRIMARY KEY, ProductName NVARCHAR(100),
--     Price DECIMAL(10,2), Stock INT, CategoryKey INT,
--     FOREIGN KEY (CategoryKey) REFERENCES DimCategory(CategoryKey)
-- );
-- CREATE TABLE DimCustomer (
--     CustomerKey INT PRIMARY KEY, FullName NVARCHAR(100),
--     Email NVARCHAR(100), City NVARCHAR(100), SignupDate DATE
-- );
-- CREATE TABLE DimDate (
--     DateKey INT PRIMARY KEY, FullDate DATE, Year INT,
--     Month INT, Day INT, Quarter INT
-- );
-- CREATE TABLE FactOrder (
--     OrderKey INT PRIMARY KEY, CustomerKey INT, ProductKey INT,
--     Quantity INT, OrderDate DATE, PaymentType NVARCHAR(50),
--     Status NVARCHAR(50), UpdatedAt DATE,
--     FOREIGN KEY (CustomerKey) REFERENCES DimCustomer(CustomerKey),
--     FOREIGN KEY (ProductKey)  REFERENCES DimProduct(ProductKey)
-- );
