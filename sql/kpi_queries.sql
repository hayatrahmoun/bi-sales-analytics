-- KPI queries for the sales star schema (SQLite / ANSI-friendly).
-- Tables: fact_sales, dim_customer, dim_product, dim_date
-- Run all of them with:  python src/run_sql.py

-- name: 01_overall_kpis
SELECT
    ROUND(SUM(sales), 0)                                  AS total_sales,
    ROUND(SUM(profit), 0)                                 AS total_profit,
    ROUND(100.0 * SUM(profit) / SUM(sales), 1)            AS profit_margin_pct,
    COUNT(DISTINCT order_id)                              AS total_orders,
    ROUND(SUM(sales) / COUNT(DISTINCT order_id), 0)       AS avg_order_value
FROM fact_sales;

-- name: 02_sales_and_profit_by_year
SELECT
    d.year,
    ROUND(SUM(f.sales), 0)                                AS sales,
    ROUND(SUM(f.profit), 0)                               AS profit,
    ROUND(100.0 * SUM(f.profit) / SUM(f.sales), 1)        AS margin_pct
FROM fact_sales f
JOIN dim_date d ON d.date = f.order_date
GROUP BY d.year
ORDER BY d.year;

-- name: 03_monthly_trend
SELECT
    d.year_month,
    ROUND(SUM(f.sales), 0)                                AS sales,
    ROUND(SUM(f.profit), 0)                               AS profit
FROM fact_sales f
JOIN dim_date d ON d.date = f.order_date
GROUP BY d.year_month
ORDER BY d.year_month;

-- name: 04_category_performance
SELECT
    p.category,
    ROUND(SUM(f.sales), 0)                                AS sales,
    ROUND(SUM(f.profit), 0)                               AS profit,
    ROUND(100.0 * SUM(f.profit) / SUM(f.sales), 1)        AS margin_pct
FROM fact_sales f
JOIN dim_product p ON p.product_id = f.product_id
GROUP BY p.category
ORDER BY profit DESC;

-- name: 05_top_10_products_by_profit
SELECT
    p.product_name,
    p.category,
    ROUND(SUM(f.sales), 0)                                AS sales,
    ROUND(SUM(f.profit), 0)                               AS profit
FROM fact_sales f
JOIN dim_product p ON p.product_id = f.product_id
GROUP BY p.product_name, p.category
ORDER BY profit DESC
LIMIT 10;

-- name: 06_region_performance
SELECT
    c.region,
    ROUND(SUM(f.sales), 0)                                AS sales,
    ROUND(SUM(f.profit), 0)                               AS profit,
    ROUND(100.0 * SUM(f.profit) / SUM(f.sales), 1)        AS margin_pct,
    COUNT(DISTINCT f.order_id)                            AS orders
FROM fact_sales f
JOIN dim_customer c ON c.customer_id = f.customer_id
GROUP BY c.region
ORDER BY sales DESC;

-- name: 07_discount_impact_on_margin
SELECT
    CASE
        WHEN discount = 0    THEN '0%'
        WHEN discount <= 0.1 THEN '1-10%'
        WHEN discount <= 0.2 THEN '11-20%'
        ELSE '21%+'
    END                                                   AS discount_band,
    COUNT(*)                                              AS order_lines,
    ROUND(SUM(sales), 0)                                  AS sales,
    ROUND(SUM(profit), 0)                                 AS profit,
    ROUND(100.0 * SUM(profit) / SUM(sales), 1)            AS margin_pct
FROM fact_sales
GROUP BY discount_band
ORDER BY MIN(discount);

-- name: 08_top_10_customers (window function)
SELECT * FROM (
    SELECT
        c.customer_name,
        c.segment,
        ROUND(SUM(f.sales), 0)                            AS sales,
        RANK() OVER (ORDER BY SUM(f.sales) DESC)          AS sales_rank
    FROM fact_sales f
    JOIN dim_customer c ON c.customer_id = f.customer_id
    GROUP BY c.customer_id, c.customer_name, c.segment
)
WHERE sales_rank <= 10
ORDER BY sales_rank;

-- name: 09_customer_segments
SELECT
    c.segment,
    COUNT(DISTINCT c.customer_id)                         AS customers,
    ROUND(SUM(f.sales), 0)                                AS sales,
    ROUND(SUM(f.sales) / COUNT(DISTINCT c.customer_id), 0) AS sales_per_customer
FROM fact_sales f
JOIN dim_customer c ON c.customer_id = f.customer_id
GROUP BY c.segment
ORDER BY sales DESC;

-- name: 10_repeat_customers
SELECT
    CASE WHEN n_orders = 1 THEN 'One-time' ELSE 'Repeat' END AS customer_type,
    COUNT(*)                                              AS customers
FROM (
    SELECT customer_id, COUNT(DISTINCT order_id) AS n_orders
    FROM fact_sales
    GROUP BY customer_id
)
GROUP BY customer_type;
