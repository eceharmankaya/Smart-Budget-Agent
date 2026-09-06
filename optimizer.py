#!/usr/bin/env python3
"""Simple optimizer skeleton for SmartBudget.

Reads `data/optimizer_input.csv` and builds a minimal LP using PuLP.
This is a starter template — tweak objective/constraints to match your goals.
"""
import sys
import re
import pandas as pd

try:
    import pulp as pl
except ImportError:
    print("PuLP is not installed. Install with: python -m pip install pulp")
    raise SystemExit(1)


def main():
    df = pd.read_csv("data/optimizer_input.csv")
    df = df.set_index("category")

    # Budget to respect (monthly). Default: current avg total minus savings_pct * avg_total
    total_avg = float(df["avg_monthly"].sum())

    # CLI: support either explicit budget or savings percentage (defaults to 10%)
    import argparse
    p = argparse.ArgumentParser(description="Optimizer: minimize deviation from current averages while meeting savings target")
    p.add_argument("--budget", type=float, default=None, help="Monthly budget to respect (overrides --savings-pct)")
    p.add_argument("--savings-pct", type=float, default=0.10, help="Target savings as fraction of current avg total (default 0.10)")
    args = p.parse_args()

    if args.budget is not None:
        budget = args.budget
    else:
        budget = total_avg * (1.0 - float(args.savings_pct))

    # Build LP: minimize sum of absolute deviations from avg_monthly (L1)
    prob = pl.LpProblem("smartbudget_min_deviation", pl.LpMinimize)

    spend_vars = {}
    dev_plus = {}
    dev_minus = {}
    for cat in df.index:
        safe_name = re.sub(r"[^0-9a-zA-Z_]", "_", cat)
        avg = float(df.loc[cat, "avg_monthly"]) if "avg_monthly" in df.columns else 0.0
        fixed = float(df.loc[cat, "fixed_amount"]) if "fixed_amount" in df.columns else 0.0

        # spend variable (lower bounded by fixed recurring amount)
        var = pl.LpVariable(f"spend_{safe_name}", lowBound=fixed, cat="Continuous")
        spend_vars[cat] = var

        # deviation vars for L1: spend = avg + dev_plus - dev_minus
        dp = pl.LpVariable(f"devp_{safe_name}", lowBound=0, cat="Continuous")
        dm = pl.LpVariable(f"devm_{safe_name}", lowBound=0, cat="Continuous")
        dev_plus[cat] = dp
        dev_minus[cat] = dm

        prob += var == avg + dp - dm, f"dev_balance_{safe_name}"

    # Objective: minimize sum of absolute deviations
    prob += pl.lpSum([dev_plus[c] + dev_minus[c] for c in df.index]), "Minimize_total_deviation"

    # Budget constraint
    prob += pl.lpSum([spend_vars[c] for c in spend_vars]) <= budget, "BudgetConstraint"

    # Solve
    prob.solve()

    # Collect results
    results = []
    for c in df.index:
        results.append({
            "category": c,
            "recommended_spend": float(pl.value(spend_vars[c])),
            "fixed_amount": float(df.loc[c, "fixed_amount"]) if "fixed_amount" in df.columns else 0.0,
            "avg_monthly": float(df.loc[c, "avg_monthly"]) if "avg_monthly" in df.columns else 0.0,
            "dev_plus": float(pl.value(dev_plus[c])),
            "dev_minus": float(pl.value(dev_minus[c])),
        })

    out = pd.DataFrame(results)
    out_path = "data/optimizer_solution.csv"
    out.to_csv(out_path, index=False)
    print(f"Saved optimizer solution to {out_path}")


if __name__ == "__main__":
    main()
