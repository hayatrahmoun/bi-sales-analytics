"""Exploratory analysis: compute KPIs and save charts + a markdown summary.

Run:  python src/analysis.py
Output: images/*.png and reports/kpi_summary.md
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data" / "clean"
IMG = ROOT / "images"
REP = ROOT / "reports"
IMG.mkdir(exist_ok=True)
REP.mkdir(exist_ok=True)

BLUE, TEAL, YELLOW, RED, NAVY, GREY = "#2E6FD8", "#1B998B", "#F2C811", "#C0392B", "#14213D", "#605E5C"
plt.rcParams.update({"font.family": "DejaVu Sans", "axes.spines.top": False, "axes.spines.right": False})

fact = pd.read_csv(CLEAN / "fact_sales.csv", parse_dates=["order_date", "ship_date"])
cust = pd.read_csv(CLEAN / "dim_customer.csv")
prod = pd.read_csv(CLEAN / "dim_product.csv")
df = (fact.merge(cust, on="customer_id")
          .merge(prod[["product_id", "product_name", "category", "sub_category"]], on="product_id"))
df["year"] = df["order_date"].dt.year
df["year_month"] = df["order_date"].dt.to_period("M").astype(str)


def money(x, _=None):
    return f"${x / 1e6:.1f}M" if abs(x) >= 1e6 else f"${x / 1e3:.0f}K"


# ---- KPIs ------------------------------------------------------------------------------------------
total_sales, total_profit = df["sales"].sum(), df["profit"].sum()
margin = total_profit / total_sales
orders = df["order_id"].nunique()
by_year = df.groupby("year")[["sales", "profit"]].sum()
growth = by_year.loc[2025, "sales"] / by_year.loc[2024, "sales"] - 1

disc_bins = pd.cut(df["discount"], [-0.01, 0, 0.1, 0.2, 0.5], labels=["0%", "1-10%", "11-20%", "21%+"])
disc = df.groupby(disc_bins, observed=True)[["sales", "profit"]].sum()
disc["margin"] = disc["profit"] / disc["sales"]
cat = df.groupby("category")[["sales", "profit"]].sum()
cat["margin"] = cat["profit"] / cat["sales"]
monthly = df.groupby("year_month")[["sales", "profit"]].sum()

# ---- Chart 1: monthly sales trend ----------------------------------------------------------------
fig, ax = plt.subplots(figsize=(11, 4.8))
colors = [YELLOW if m[-2:] in ("11", "12") else BLUE for m in monthly.index]
ax.bar(monthly.index, monthly["sales"], color=colors)
ax.set_xticks(range(0, len(monthly), 2))
ax.set_xticklabels(monthly.index[::2], rotation=45, ha="right")
ax.yaxis.set_major_formatter(plt.FuncFormatter(money))
ax.set_title("Monthly sales: Nov-Dec peak (yellow) drives the year", loc="left", fontweight="bold", color=NAVY)
ax.grid(axis="y", color="#EDEBE9")
fig.tight_layout()
fig.savefig(IMG / "01_monthly_sales.png", dpi=130)
plt.close(fig)

# ---- Chart 2: discount vs margin ------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(8, 4.8))
bars = ax.bar(disc.index.astype(str), disc["margin"] * 100,
              color=[TEAL if v > 0 else RED for v in disc["margin"]])
for b, v in zip(bars, disc["margin"] * 100):
    if v > 0:
        ax.text(b.get_x() + b.get_width() / 2, v + 1, f"{v:.1f}%", ha="center", fontweight="bold")
    else:
        ax.text(b.get_x() + b.get_width() / 2, v / 2, f"{v:.1f}%", ha="center", va="center",
                fontweight="bold", color="white")
ax.axhline(0, color=GREY, linewidth=1)
ax.set_ylabel("Profit margin (%)")
ax.set_xlabel("Discount band")
ax.set_title("Discounts above 20% make sales unprofitable", loc="left", fontweight="bold", color=NAVY)
fig.tight_layout()
fig.savefig(IMG / "02_discount_vs_margin.png", dpi=130)
plt.close(fig)

# ---- Chart 3: category sales vs margin ------------------------------------------------------------
fig, ax = plt.subplots(figsize=(8, 4.8))
cat = cat.sort_values("sales", ascending=False)
ax.bar(cat.index, cat["sales"], color=BLUE)
ax.yaxis.set_major_formatter(plt.FuncFormatter(money))
ax.set_ylabel("Sales")
ax2 = ax.twinx()
ax2.plot(cat.index, cat["margin"] * 100, color=YELLOW, marker="o", linewidth=3, markersize=9)
ax2.set_ylabel("Profit margin (%)")
ax2.spines["right"].set_visible(True)
for x, v in zip(cat.index, cat["margin"] * 100):
    ax2.text(x, v + 2, f"{v:.1f}%", ha="center", fontweight="bold", color=NAVY)
ax.set_title("Technology sells the most but earns the least", loc="left", fontweight="bold", color=NAVY)
fig.tight_layout()
fig.savefig(IMG / "03_category_sales_vs_margin.png", dpi=130)
plt.close(fig)

# ---- Chart 4: top products by profit --------------------------------------------------------------
top = df.groupby("product_name")["profit"].sum().sort_values().tail(10)
fig, ax = plt.subplots(figsize=(8, 4.8))
ax.barh(top.index, top.values, color=TEAL)
ax.xaxis.set_major_formatter(plt.FuncFormatter(money))
ax.set_title("Top 10 products by profit", loc="left", fontweight="bold", color=NAVY)
fig.tight_layout()
fig.savefig(IMG / "04_top_products_profit.png", dpi=130)
plt.close(fig)

# ---- Markdown summary ------------------------------------------------------------------------------------
neg = df[df["discount"] > 0.2]
summary = f"""# KPI summary (synthetic data)

| KPI | Value |
|---|---|
| Total sales | {money(total_sales)} |
| Total profit | {money(total_profit)} |
| Profit margin | {margin:.1%} |
| Orders | {orders:,} |
| Average order value | ${total_sales / orders:,.0f} |
| Sales growth 2025 vs 2024 | {growth:+.1%} |

## Key findings
1. **Discounts above 20% destroy profit**: those lines earn a {disc.loc['21%+', 'margin']:.1%} margin
   and lose {money(-neg['profit'].sum())} in total.
2. **Technology is the largest category but has the lowest margin** ({cat.loc['Technology', 'margin']:.1%}),
   while Furniture earns {cat.loc['Furniture', 'margin']:.1%}.
3. **November and December are the peak**: they generate {monthly[monthly.index.str[-2:].isin(['11', '12'])]['sales'].sum() / monthly['sales'].sum():.0%}
   of sales, so stock and staffing should be planned around them.
4. Sales grew {growth:.1%} year over year, but the margin slipped from
   {by_year.loc[2024, 'profit'] / by_year.loc[2024, 'sales']:.1%} to {by_year.loc[2025, 'profit'] / by_year.loc[2025, 'sales']:.1%}.

## Recommendations
- Cap discounts at 20% (or require approval above it), especially on Technology products.
- Review Technology pricing and supplier costs to lift the margin.
- Prepare inventory and marketing for the Nov-Dec peak.
"""
(REP / "kpi_summary.md").write_text(summary, encoding="utf-8")
print(summary)
