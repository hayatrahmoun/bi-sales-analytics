"""Generate a realistic, fictional retail sales dataset (with deliberate data-quality problems).

The data is synthetic: no real company, customer or person is represented.
Run:  python src/generate_data.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
rng = np.random.default_rng(SEED)

OUT = Path(__file__).resolve().parents[1] / "data" / "raw"
OUT.mkdir(parents=True, exist_ok=True)

# product_id, name, category, sub_category, unit_price, unit_cost
PRODUCTS = [
    ("P01", "Ergo Office Chair", "Furniture", "Chairs", 180, 118),
    ("P02", "Mesh Task Chair", "Furniture", "Chairs", 120, 82),
    ("P03", "Standing Desk", "Furniture", "Tables", 420, 290),
    ("P04", "Meeting Table", "Furniture", "Tables", 360, 245),
    ("P05", "Filing Cabinet", "Furniture", "Storage", 150, 95),
    ("P06", "Bookshelf Unit", "Furniture", "Storage", 130, 84),
    ("P07", "Smartphone X", "Technology", "Phones", 640, 540),
    ("P08", "Smartphone Lite", "Technology", "Phones", 310, 262),
    ("P09", "Wireless Mouse", "Technology", "Accessories", 28, 14),
    ("P10", "Mechanical Keyboard", "Technology", "Accessories", 85, 52),
    ("P11", "27in Monitor", "Technology", "Monitors", 290, 235),
    ("P12", "Ultrawide Monitor", "Technology", "Monitors", 520, 430),
    ("P13", "Copy Paper (box)", "Office Supplies", "Paper", 38, 22),
    ("P14", "Notebook Pack", "Office Supplies", "Paper", 16, 8),
    ("P15", "Heavy-Duty Binder", "Office Supplies", "Binders", 12, 5),
    ("P16", "Presentation Binder", "Office Supplies", "Binders", 18, 8),
    ("P17", "Marker Set", "Office Supplies", "Art", 14, 6),
    ("P18", "Sketch Pad Set", "Office Supplies", "Art", 22, 11),
]

REGIONS = {
    "East": ["Boston", "Atlanta", "Miami"],
    "West": ["Seattle", "Los Angeles", "Denver"],
    "Central": ["Chicago", "Dallas", "Austin"],
    "South": ["Houston", "Phoenix", "Nashville"],
}
CITY_TO_REGION = {c: r for r, cities in REGIONS.items() for c in cities}
CITIES = list(CITY_TO_REGION)

FIRST = ["Alex", "Sam", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Jamie", "Avery", "Quinn",
         "Drew", "Parker", "Reese", "Skyler", "Cameron", "Dana", "Robin", "Kai", "Noel", "Sasha"]
LAST = ["Brooks", "Carter", "Diaz", "Ellis", "Foster", "Grant", "Hayes", "Irwin", "Jensen", "Keller",
        "Lopez", "Mason", "Nolan", "Owens", "Price", "Quincy", "Reed", "Stone", "Turner", "Vaughn"]

N_CUSTOMERS = 450
N_ORDERS = 3000

# --- customers -----------------------------------------------------------------------------
customers = pd.DataFrame({
    "customer_id": [f"C{str(i).zfill(4)}" for i in range(1, N_CUSTOMERS + 1)],
    "customer_name": [f"{rng.choice(FIRST)} {rng.choice(LAST)}" for _ in range(N_CUSTOMERS)],
    "segment": rng.choice(["Consumer", "Corporate", "Home Office"], N_CUSTOMERS, p=[0.52, 0.30, 0.18]),
    "city": rng.choice(CITIES, N_CUSTOMERS),
})
customers["region"] = customers["city"].map(CITY_TO_REGION)

# --- order dates with growth and a Nov/Dec seasonal peak -------------------------------------
days = pd.date_range("2024-01-01", "2025-12-31", freq="D")
weights = np.ones(len(days))
weights *= np.where(days.month.isin([11, 12]), 1.7, 1.0)
weights *= np.where(days.month.isin([1, 2]), 0.8, 1.0)
weights *= 1 + 0.35 * (np.arange(len(days)) / len(days))  # business grows over time
weights /= weights.sum()
order_dates = rng.choice(days, N_ORDERS, p=weights)

prod_df = pd.DataFrame(PRODUCTS, columns=["product_id", "product_name", "category", "sub_category",
                                           "unit_price", "unit_cost"])
DISCOUNTS = [0.0, 0.0, 0.0, 0.0, 0.1, 0.1, 0.2, 0.3, 0.4]

rows = []
for i in range(N_ORDERS):
    cust = customers.iloc[rng.integers(0, N_CUSTOMERS)]
    o_date = pd.Timestamp(order_dates[i])
    ship = o_date + pd.Timedelta(days=int(rng.integers(2, 8)))
    n_lines = int(rng.integers(1, 5))
    for pid in rng.choice(len(prod_df), n_lines, replace=False):
        p = prod_df.iloc[pid]
        rows.append({
            "order_id": f"ORD-{2024000 + i + 1}",
            "order_date": o_date,
            "ship_date": ship,
            "customer_id": cust.customer_id,
            "customer_name": cust.customer_name,
            "segment": cust.segment,
            "city": cust.city,
            "region": cust.region,
            "product_id": p.product_id,
            "product_name": p.product_name,
            "category": p.category,
            "sub_category": p.sub_category,
            "quantity": int(rng.integers(1, 9)),
            "unit_price": float(p.unit_price),
            "unit_cost": float(p.unit_cost),
            "discount": float(rng.choice(DISCOUNTS)),
        })

df = pd.DataFrame(rows)

# --- inject realistic data-quality problems (to be fixed in clean_data.py) --------------------
# 1) mixed date formats
mask = rng.random(len(df)) < 0.10
df["order_date"] = df["order_date"].dt.strftime("%Y-%m-%d")
df.loc[mask, "order_date"] = pd.to_datetime(df.loc[mask, "order_date"]).dt.strftime("%d/%m/%Y")
df["ship_date"] = df["ship_date"].dt.strftime("%Y-%m-%d")

# 2) inconsistent text (case + stray spaces)
m2 = rng.random(len(df)) < 0.08
df.loc[m2, "segment"] = df.loc[m2, "segment"].str.upper() + " "
m3 = rng.random(len(df)) < 0.05
df.loc[m3, "customer_name"] = " " + df.loc[m3, "customer_name"].str.lower()

# 3) missing region values
df.loc[rng.random(len(df)) < 0.015, "region"] = np.nan

# 4) exact duplicate rows
dups = df.sample(frac=0.02, random_state=SEED)
df = pd.concat([df, dups], ignore_index=True).sample(frac=1, random_state=SEED).reset_index(drop=True)

df.to_csv(OUT / "sales_raw.csv", index=False)
print(f"Wrote {len(df):,} raw rows to {OUT / 'sales_raw.csv'}")
