import os
import pandas as pd

# Try to import matplotlib for plots. If not available, continue without plotting.
# Catch ImportError specifically so other unexpected errors still raise.
try:
	import matplotlib.pyplot as plt
	_CAN_PLOT = True
except ImportError:
	_CAN_PLOT = False


def main():
	"""Simple data checks for SmartBudget generated data.

	This script reads `data/expenses.csv`, ensures the `date` column
	is parsed as datetime, and prints small summaries useful for
	the next steps of analysis.
	"""

	path = "data/expenses.csv"

	# Read CSV into a DataFrame
	df = pd.read_csv(path)

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

