# Power BI guide

This folder explains how to rebuild the dashboard in Power BI Desktop from the clean star schema.

## 1. Load the data
1. Open Power BI Desktop > **Get data > Text/CSV**.
2. Load the four files from `data/clean/`: `fact_sales.csv`, `dim_customer.csv`, `dim_product.csv`, `dim_date.csv`.
3. In Power Query, check types: dates as **Date**, `discount` as **Decimal**, `sales / cost / profit` as **Fixed decimal**.

## 2. Data model (star schema)
Create these relationships in **Model view** (one-to-many, single direction):

| From (one) | To (many) |
|---|---|
| `dim_date[date]` | `fact_sales[order_date]` |
| `dim_customer[customer_id]` | `fact_sales[customer_id]` |
| `dim_product[product_id]` | `fact_sales[product_id]` |

Mark `dim_date` as a **date table** (Table tools > Mark as date table > `date`).

## 3. DAX measures
Create a table called `_Measures` and add:

```DAX
Total Sales = SUM ( fact_sales[sales] )

Total Profit = SUM ( fact_sales[profit] )

Profit Margin % = DIVIDE ( [Total Profit], [Total Sales] )

Orders = DISTINCTCOUNT ( fact_sales[order_id] )

Avg Order Value = DIVIDE ( [Total Sales], [Orders] )

Sales LY =
CALCULATE ( [Total Sales], SAMEPERIODLASTYEAR ( dim_date[date] ) )

Sales YoY % = DIVIDE ( [Total Sales] - [Sales LY], [Sales LY] )

Sales YTD =
TOTALYTD ( [Total Sales], dim_date[date] )

Avg Discount % =
DIVIDE ( SUMX ( fact_sales, fact_sales[quantity] * fact_sales[unit_price] * fact_sales[discount] ),
         SUMX ( fact_sales, fact_sales[quantity] * fact_sales[unit_price] ) )

Customers = DISTINCTCOUNT ( fact_sales[customer_id] )

Profit Margin Status =
IF ( [Profit Margin %] < 0, "Loss", IF ( [Profit Margin %] < 0.1, "Low", "Healthy" ) )
```

A calculated column for the discount chart (on `fact_sales`):

```DAX
Discount Band =
SWITCH (
    TRUE (),
    fact_sales[discount] = 0,    "0%",
    fact_sales[discount] <= 0.1, "1-10%",
    fact_sales[discount] <= 0.2, "11-20%",
    "21%+"
)
```

## 4. Suggested report pages

**Page 1: Executive overview**
- KPI cards: Total Sales, Total Profit, Profit Margin %, Orders, Avg Order Value (with YoY %)
- Line chart: Total Sales by `dim_date[year_month]`
- Bar chart: Total Profit by `dim_product[category]`
- Map or bar: Total Sales by `dim_customer[region]`
- Slicers: Year, Region, Segment

**Page 2: Product and discount analysis**
- Column chart: Profit Margin % by `Discount Band` (highlight the negative bar in red)
- Scatter: Total Sales vs Profit Margin % by product
- Table: top 10 products by Total Profit (Top N filter)
- Decomposition tree: Total Profit by Category > Sub-category > Product

**Page 3: Customers**
- Donut: Customers by `segment`
- Table: top 10 customers by Total Sales
- Matrix: Region x Segment, values = Total Sales

## 5. Design tips
- Use a consistent palette (navy header, one accent colour, red only for losses).
- Put the most important KPI cards at the top-left.
- Add tooltips and a "Reset filters" bookmark button.
- Export screenshots to `images/powerbi_*.png` and link them in the main README.
