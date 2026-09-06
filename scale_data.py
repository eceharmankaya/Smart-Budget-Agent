#!/usr/bin/env python3
"""Scale optimizer input to match 60k income."""
import pandas as pd

# Read current data
df = pd.read_csv("data/optimizer_input.csv")

# Current total
current_total = df["avg_monthly"].sum()
print(f"Current total: {current_total:.0f} TL")

# Target: 60k income → realistic monthly budget = 50k (20% savings buffer)
target_total = 50000

scale_factor = target_total / current_total
print(f"Scale factor: {scale_factor:.4f}")

# Scale all categories proportionally, but keep Housing and Beauty fixed
for idx, row in df.iterrows():
    if row['category'] in ['Housing', 'Beauty']:
        # Keep these fixed
        pass
    else:
        # Scale others
        df.at[idx, 'avg_monthly'] = row['avg_monthly'] * scale_factor
        if row['fixed_amount'] > 0:
            df.at[idx, 'fixed_amount'] = row['fixed_amount'] * scale_factor
        if row['avg_variable_amount'] > 0:
            df.at[idx, 'avg_variable_amount'] = row['avg_variable_amount'] * scale_factor

# Save
df.to_csv("data/optimizer_input.csv", index=False)
print("\nScaled data saved!")
print(f"New total: {df['avg_monthly'].sum():.0f} TL")
