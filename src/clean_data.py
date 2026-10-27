"""Clean the raw sales file and build a star schema (1 fact table + 3 dimensions).

Run:  python src/clean_data.py
Output: data/clean/{fact_sales,dim_customer,dim_product,dim_date}.csv
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "sales_raw.csv"
CLEAN = ROOT / "data" / "clean"
CLEAN.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(RAW)
report = {"raw_rows": len(df)}

# 1. Text columns: trim spaces and standardise case ---------------------------------------------
for col in ["customer_name", "segment", "city", "region", "category", "sub_category", "product_name"]:
    df[col] = df[col].astype("string").str.strip()
df["segment"] = df["segment"].str.title()
df["customer_name"] = df["customer_name"].str.title()

# 2. Dates: two formats are mixed in the source ---------------------------------------------------
iso = pd.to_datetime(df["order_date"], format="%Y-%m-%d", errors="coerce")
dmy = pd.to_datetime(df["order_date"], format="%d/%m/%Y", errors="coerce")
df["order_date"] = iso.fillna(dmy)
df["ship_date"] = pd.to_datetime(df["ship_date"], format="%Y-%m-%d")
report["unparsed_dates"] = int(df["order_date"].isna().sum())
df = df.dropna(subset=["order_date"])

# 3. Duplicates ------------------------------------------------------------------------------------
before = len(df)
df = df.drop_duplicates().reset_index(drop=True)
report["duplicates_removed"] = before - len(df)

# 4. Missing regions: recover them from the city ----------------------------------------------------
report["missing_region_before"] = int(df["region"].isna().sum())
city_region = df.dropna(subset=["region"]).groupby("city")["region"].agg(lambda s: s.mode().iloc[0])
df["region"] = df["region"].fillna(df["city"].map(city_region))
report["missing_region_after"] = int(df["region"].isna().sum())

# 5. Business rules / validation ----------------------------------------------------------------------
assert (df["quantity"] > 0).all(), "quantity must be positive"
assert df["discount"].between(0, 0.8).all(), "discount out of range"
assert (df["ship_date"] >= df["order_date"]).all(), "ship_date before order_date"

# 6. Measures ----------------------------------------------------------------------------------------------
df["sales"] = (df["quantity"] * df["unit_price"] * (1 - df["discount"])).round(2)
df["cost"] = (df["quantity"] * df["unit_cost"]).round(2)
df["profit"] = (df["sales"] - df["cost"]).round(2)
df.insert(0, "line_id", range(1, len(df) + 1))

# 7. Star schema ----------------------------------------------------------------------------------------------
fact = df[["line_id", "order_id", "order_date", "ship_date", "customer_id", "product_id",
           "quantity", "unit_price", "discount", "sales", "cost", "profit"]]

dim_customer = (df[["customer_id", "customer_name", "segment", "city", "region"]]
                .drop_duplicates("customer_id").sort_values("customer_id"))
dim_product = (df[["product_id", "product_name", "category", "sub_category", "unit_price", "unit_cost"]]
               .drop_duplicates("product_id").sort_values("product_id"))

dates = pd.date_range(df["order_date"].min().normalize(), df["order_date"].max().normalize(), freq="D")
dim_date = pd.DataFrame({"date": dates})
dim_date["year"] = dim_date["date"].dt.year
dim_date["quarter"] = "Q" + dim_date["date"].dt.quarter.astype(str)
dim_date["month_num"] = dim_date["date"].dt.month
dim_date["month_name"] = dim_date["date"].dt.strftime("%b")
dim_date["year_month"] = dim_date["date"].dt.strftime("%Y-%m")
dim_date["weekday"] = dim_date["date"].dt.strftime("%a")
dim_date["is_weekend"] = dim_date["date"].dt.dayofweek >= 5

fact.to_csv(CLEAN / "fact_sales.csv", index=False)
dim_customer.to_csv(CLEAN / "dim_customer.csv", index=False)
dim_product.to_csv(CLEAN / "dim_product.csv", index=False)
dim_date.to_csv(CLEAN / "dim_date.csv", index=False)

report["clean_rows"] = len(fact)
print("Data quality report")
for k, v in report.items():
    print(f"  {k:24s}: {v:,}")
print(f"Wrote star schema to {CLEAN}")
