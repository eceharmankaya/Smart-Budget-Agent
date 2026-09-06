#!/usr/bin/env python3
"""Final project summary and current recommendations."""
import pandas as pd

print("="*75)
print("SMARTBUDGET AGENT - PROJECT COMPLETION SUMMARY")
print("="*75)
print()

# Load data
input_df = pd.read_csv("data/optimizer_input.csv").set_index("category")
sol_df = pd.read_csv("data/optimizer_solution.csv").set_index("category")

total_current = input_df["avg_monthly"].sum()
total_recommended = sol_df["recommended_spend"].sum()
total_savings = total_current - total_recommended

print("📊 PROJECT STATUS: COMPLETE")
print()
print("✅ Modules Implemented:")
print("  1. generate_data.py — Synthetic transaction generation (3 months, 189 transactions)")
print("  2. analysis.py — Recurring detection, category analysis, visualizations")
print("  3. optimizer.py — LP-based budget optimization with constraints")
print("  4. compare_budgets.py — Side-by-side budget comparison")
print()

print("📈 CURRENT FINANCIAL SCENARIO:")
print(f"  Monthly Income:          60,000 TL")
print(f"  Current Avg Spending:    {total_current:>10,.0f} TL")
print(f"  Optimized Budget:        {total_recommended:>10,.0f} TL")
print(f"  Monthly Savings:         {total_savings:>10,.0f} TL ({total_savings/total_current*100:.1f}%)")
print()

print("🏦 FIXED CATEGORIES (Protected):")
fixed_cats = input_df[input_df['fixed_amount'] == input_df['avg_monthly']]
for cat in fixed_cats.index:
    amount = fixed_cats.loc[cat, 'avg_monthly']
    print(f"  • {cat:20s} {amount:>10,.0f} TL")
print()

print("📉 TOP DISCRETIONARY REDUCTIONS:")
comparison = pd.DataFrame({
    "current": input_df["avg_monthly"],
    "recommended": sol_df["recommended_spend"],
})
comparison["savings"] = comparison["current"] - comparison["recommended"]
comparison["pct"] = (comparison["savings"] / comparison["current"] * 100).round(0)
top_cuts = comparison[comparison["savings"] > 0].nlargest(5, "savings")
for cat in top_cuts.index:
    cur = top_cuts.loc[cat, 'current']
    rec = top_cuts.loc[cat, 'recommended']
    sav = top_cuts.loc[cat, 'savings']
    pct = top_cuts.loc[cat, 'pct']
    print(f"  • {cat:20s} {cur:>8,.0f} → {rec:>8,.0f} TL (save {sav:>8,.0f}, -{int(pct)}%)")
print()

print("🎯 OPTIMIZER FEATURES:")
print("  • Recurring detection with normalization")
print("  • L1 deviation minimization (preserves balance)")
print("  • Category min/max bounds (70-100% for essentials, 5-100% for discretionary)")
print("  • Protected category support (e.g., Beauty, Groceries)")
print("  • Savings target by % or explicit budget")
print()

print("📂 OUTPUT FILES GENERATED:")
print("  • data/expenses.csv — Raw transaction data")
print("  • data/recurring.csv — Detected recurring expenses")
print("  • data/optimizer_input.csv — Category summaries")
print("  • data/optimizer_solution.csv — Optimized recommendations")
print("  • data/monthly_summary.csv — Time series analysis")
print("  • output/*.png — Visualizations (if matplotlib available)")
print()

print("🚀 NEXT STEPS (Optional):")
print("  1. Integrate with AI agent (agent.py) for personalized explanations")
print("  2. Build web app (app.py) with interactive budget scenarios")
print("  3. Add expense tracking alerts and dashboard")
print("  4. Implement multi-month rolling forecasts")
print()

print("="*75)
