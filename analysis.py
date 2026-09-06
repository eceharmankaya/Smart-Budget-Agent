import pandas as pd


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


if __name__ == "__main__":
	main()

