#!/usr/bin/env python3
"""Compare current vs recommended budget."""
import pandas as pd

# Read current input and optimizer output
input_df = pd.read_csv("data/optimizer_input.csv").set_index("category")
sol_df = pd.read_csv("data/optimizer_solution.csv").set_index("category")

# Compare
comparison = pd.DataFrame({
    "avg_monthly": input_df["avg_monthly"],
    "recommended": sol_df["recommended_spend"],
    "change": sol_df["recommended_spend"] - input_df["avg_monthly"],
    "change_pct": ((sol_df["recommended_spend"] - input_df["avg_monthly"]) / input_df["avg_monthly"] * 100).round(1),
})

total_current = input_df["avg_monthly"].sum()
total_recommended = sol_df["recommended_spend"].sum()
total_savings = total_current - total_recommended
savings_pct = total_savings / total_current * 100

print(f"=== OPTIMIZED BUDGET RECOMMENDATION ({savings_pct:.1f}% Reduction) ===\n")
print(comparison.to_string())
print("\n" + "="*70)
print(f"Total Current Avg:       {total_current:>12,.0f} TL")
print(f"Total Recommended:       {total_recommended:>12,.0f} TL")
print(f"Total Savings:           {total_savings:>12,.0f} TL ({savings_pct:.1f}%)")
print("="*70)
