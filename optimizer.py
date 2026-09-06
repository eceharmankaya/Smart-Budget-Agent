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
    p.add_argument("--protected-categories", type=str, default="", help="Comma-separated categories to keep at avg_monthly (e.g., 'Beauty,Coffee')")
    args = p.parse_args()

    # Parse protected categories: these keep their avg_monthly as fixed_amount
    protected = set()
    if args.protected_categories:
        protected = set(c.strip() for c in args.protected_categories.split(','))

    # Define category min/max bounds (as fraction of avg_monthly)
    # min_fraction: minimum allowed spend as % of current avg_monthly
    # max_fraction: maximum allowed spend as % of current avg_monthly
    category_bounds = {
        "Groceries": (0.75, 1.0),        # Essential, min 75%
        "Utilities": (0.70, 1.0),        # Essential, min 70%
        "Health Insurance": (1.0, 1.0),  # Fixed
        "Housing": (1.0, 1.0),           # Fixed
        "Beauty": (1.0, 1.0),            # Fixed (protected)
        "Gym": (0.3, 1.0),               # Can cut to 30%
        "Subscriptions": (1.0, 1.0),     # Fixed
        "AI Tools": (1.0, 1.0),          # Fixed
        "Entertainment": (0.2, 1.0),     # Can cut to 20%
        "Transportation": (0.1, 1.0),    # Can cut to 10%
        "Coffee": (0.05, 1.0),           # Can nearly eliminate
        "Delivery": (0.0, 0.3),          # Can reduce to 30%
        "Shopping": (0.2, 1.0),          # Can cut to 20%
        "Restaurants": (0.3, 1.0),       # Can cut to 30%
        "Travel": (0.2, 1.0),            # Can cut to 20%
        "Other": (0.0, 0.3),             # Can reduce to 30%
    }

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
        
        # If category is protected, set fixed_amount to avg_monthly (keep it unchanged)
        if cat in protected:
            fixed = avg

        # Apply category bounds (min/max as fraction of avg)
        min_frac, max_frac = category_bounds.get(cat, (0.0, 2.0))  # default: 0 to 2x
        lb_bound = avg * min_frac
        ub_bound = avg * max_frac
        
        # Lower bound takes max of fixed (recurring) and min_bound
        lb = max(fixed, lb_bound)

        # spend variable (lower bounded by fixed recurring amount or min_bound, upper bounded by max_bound)
        var = pl.LpVariable(f"spend_{safe_name}", lowBound=lb, upBound=ub_bound, cat="Continuous")
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
