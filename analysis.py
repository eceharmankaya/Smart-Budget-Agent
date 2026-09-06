import os
import sys
import re
import math
import pandas as pd
import numpy as np

# Try to import matplotlib for plots. If not available, continue without plotting.
# Catch ImportError specifically so other unexpected errors still raise.
try:
	import matplotlib.pyplot as plt
	_CAN_PLOT = True
	_MATPLOTLIB_VERSION = getattr(plt, "__version__", None)
	_MATPLOTLIB_IMPORT_ERROR = None
except ImportError as e:
	_CAN_PLOT = False
	_MATPLOTLIB_VERSION = None
	_MATPLOTLIB_IMPORT_ERROR = str(e)


def main():
	"""Simple data checks for SmartBudget generated data.

	This script reads `data/expenses.csv`, ensures the `date` column
	is parsed as datetime, and prints small summaries useful for
	the next steps of analysis.
	"""

	path = "data/expenses.csv"

	# Recurring detection parameters (tweak if needed)
	MIN_MONTHS_RATIO = 0.66  # fraction of months a description must appear in to be considered recurring
	CV_THRESHOLD = 0.25      # allowable coefficient-of-variation (std/mean)

	def normalize_description(s: str) -> str:
		# basic normalization: lowercase, strip, collapse whitespace, remove punctuation
		s = str(s).lower()
		s = re.sub(r"[^0-9a-z\s]", "", s)
		s = re.sub(r"\s+", " ", s).strip()
		return s

	# Diagnostic: show which Python interpreter is running and matplotlib status
	print("Python executable:", sys.executable)
	if _CAN_PLOT:
		print("matplotlib available, version:", _MATPLOTLIB_VERSION)
	else:
		print(f"matplotlib not available for {sys.executable}. Install with: {sys.executable} -m pip install matplotlib")

	# Read CSV into a DataFrame
	df = pd.read_csv(path)

	# Add normalized description to help group noisy descriptions
	df["desc_norm"] = df["description"].apply(normalize_description)

	# Convert date column to datetime type (important for monthly grouping)
	df["date"] = pd.to_datetime(df["date"])  # yeni terim: datetime -> tarih zamanı

	# Quick checks / summaries
	print("=== First rows ===")
	print(df.head(), "\n")

	print("=== Info ===")
	print(df.info(), "\n")

	print("=== Total spend ===")
	print(df["amount"].sum(), "TL\n")

	print("=== Transactions per category ===")
	print(df["category"].value_counts(), "\n")

	# Monthly totals: group by year-month for a simple monthly summary
	df["year_month"] = df["date"].dt.to_period("M")
	monthly = df.groupby("year_month")["amount"].sum()
	print("=== Monthly totals ===")
	print(monthly, "\n")

	# Monthly summary: total, mean, median, and 3-month rolling average
	monthly_mean = df.groupby("year_month")["amount"].mean()
	monthly_median = df.groupby("year_month")["amount"].median()
	monthly_rolling3 = monthly.rolling(window=3).mean()

	monthly_summary = (
		pd.DataFrame({
			"total": monthly,
			"mean": monthly_mean,
			"median": monthly_median,
			"rolling_3_month_mean": monthly_rolling3,
		})
		.reset_index()
	)

	print("=== Monthly summary ===")
	print(monthly_summary, "\n")

	# Save monthly summary CSV
	monthly_summary.to_csv("data/monthly_summary.csv", index=False)
	print("Saved monthly summary to data/monthly_summary.csv")

	# Try to plot if matplotlib is available
	if _CAN_PLOT:
		os.makedirs("output", exist_ok=True)

		# Plot monthly totals with labels and annotations
		plt.style.use("seaborn-v0_8-muted")
		fig, ax = plt.subplots(figsize=(8, 4), dpi=150)
		bars = ax.bar(monthly.index.astype(str), monthly.values, color="#4C72B0")
		ax.set_title("Monthly totals")
		ax.set_ylabel("Amount (TL)")
		ax.set_xlabel("")
		ax.grid(axis="y", linestyle="--", alpha=0.4)
		plt.xticks(rotation=45, ha="right")
		# annotate bars
		for bar in bars:
			h = bar.get_height()
			ax.annotate(f"{int(h):,}", xy=(bar.get_x() + bar.get_width() / 2, h),
						xytext=(0, 4), textcoords="offset points", ha="center", va="bottom", fontsize=8)
		plt.tight_layout()
		monthly_plot_path = "output/monthly_totals.png"
		fig.savefig(monthly_plot_path)
		plt.close(fig)
		print(f"Saved monthly plot to {monthly_plot_path}")
	else:
		print("matplotlib not available — skipping monthly plot (install with `pip install matplotlib`)")

	# Category totals: total amount spent per category
	category_totals = df.groupby("category")["amount"].sum().sort_values(ascending=False)
	print("=== Category totals (TL) ===")
	print(category_totals, "\n")

	# Save category totals for later (optimizer/app use)
	category_totals.to_csv("data/category_totals.csv", header=["total_amount"]) 
	print("Category totals saved to data/category_totals.csv")

	# Top 5 largest individual transactions
	top5 = df.nlargest(5, "amount")
	print("=== Top 5 largest transactions ===")
	print(top5, "\n")

	# Save top5 for review
	top5.to_csv("data/top5_transactions.csv", index=False)
	print("Top 5 transactions saved to data/top5_transactions.csv")

	# Detect recurring payments by normalized description across months
	n_months = df["year_month"].nunique()
	min_months = max(1, math.ceil(n_months * MIN_MONTHS_RATIO))

	# stats per normalized description
	dn_month_counts = df.groupby("desc_norm")["year_month"].nunique()
	dn_stats = df.groupby("desc_norm")["amount"].agg(["mean", "std"]).rename(columns={"mean": "avg_amount", "std": "std_amount"})

	dn_summary = dn_month_counts.rename("months_count").to_frame().join(dn_stats)
	dn_summary["cv"] = dn_summary["std_amount"] / dn_summary["avg_amount"].replace(0, np.nan)

	# Recurring if appears in at least min_months and coefficient of variation small
	dn_summary["is_recurring"] = (dn_summary["months_count"] >= min_months) & (dn_summary["cv"].fillna(0) < CV_THRESHOLD)

	# Map normalized description -> representative original description and category
	rep_desc = df.groupby("desc_norm")["description"].agg(lambda x: x.mode().iat[0])
	rep_cat = df.groupby("desc_norm")["category"].agg(lambda x: x.mode().iat[0])

	recurring_df = dn_summary.reset_index().merge(rep_desc.reset_index(), on="desc_norm").merge(rep_cat.reset_index(), on="desc_norm")

	# reorder/rename columns for clarity
	recurring_df = recurring_df[["description", "desc_norm", "months_count", "avg_amount", "std_amount", "cv", "is_recurring", "category"]]

	# Save recurring descriptions
	recurring_path = "data/recurring.csv"
	recurring_df.to_csv(recurring_path, index=False)
	print(f"Saved recurring descriptions to {recurring_path}")

	# Prepare optimizer input per category
	# average monthly spend per category
	cat_month = df.groupby(["category", "year_month"])["amount"].sum().reset_index()
	cat_month_mean = cat_month.groupby("category")["amount"].mean().rename("avg_monthly")

	# fixed amount per category = sum of recurring avg_amounts (assume recurring avg is monthly)
	fixed_per_cat = recurring_df[recurring_df["is_recurring"]].groupby("category")["avg_amount"].sum().rename("fixed_amount")

	optimizer_df = pd.concat([cat_month_mean, fixed_per_cat], axis=1).fillna(0)
	optimizer_df["avg_variable_amount"] = (optimizer_df["avg_monthly"] - optimizer_df["fixed_amount"]).clip(lower=0)
	optimizer_df["is_recurring_category"] = optimizer_df["fixed_amount"] > 0

	optimizer_path = "data/optimizer_input.csv"
	optimizer_df.reset_index().to_csv(optimizer_path, index=False)
	print(f"Saved optimizer input to {optimizer_path}")

	# Plot top categories (top 10) if possible
	if _CAN_PLOT:
		# vertical bar for categories (swap axes): categories on x, amounts on y
		fig, ax = plt.subplots(figsize=(10, 5), dpi=150)
		top_cats = category_totals.head(10)
		bars = ax.bar(top_cats.index.astype(str), top_cats.values, color="#55A868")
		ax.set_title("Top 10 categories by total spend")
		ax.set_ylabel("Amount (TL)")
		ax.set_xlabel("")
		ax.grid(axis="y", linestyle="--", alpha=0.3)
		plt.xticks(rotation=45, ha="right")
		# annotate above bars
		for bar in bars:
			h = bar.get_height()
			ax.annotate(f"{int(h):,}", xy=(bar.get_x() + bar.get_width() / 2, h),
						xytext=(0, 4), textcoords="offset points", ha="center", va="bottom", fontsize=8)
		plt.tight_layout()
		category_plot_path = "output/category_totals.png"
		fig.savefig(category_plot_path)
		plt.close(fig)
		print(f"Saved category plot to {category_plot_path}")
	else:
		print("matplotlib not available — skipping category plot (install with `pip install matplotlib`)")


if __name__ == "__main__":
	main()

