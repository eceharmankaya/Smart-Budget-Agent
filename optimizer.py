#!/usr/bin/env python3
"""Simple optimizer skeleton for SmartBudget.

Reads `data/optimizer_input.csv` and builds a minimal LP using PuLP.
This is a starter template — tweak objective/constraints to match your goals.
"""
import sys
import re
from pathlib import Path
import pandas as pd

try:
    import pulp as pl
except ImportError:
    print("PuLP is not installed. Install with: python -m pip install pulp")
    raise SystemExit(1)


def main():
    # CLI: support either explicit budget or savings percentage (defaults to 10%)
    import argparse
    p = argparse.ArgumentParser(description="Optimizer: minimize deviation from current averages while meeting savings target")
    p.add_argument("--input", type=Path, default=Path("data/optimizer_input.csv"), help="Optimizer input CSV")
    p.add_argument("--output", type=Path, default=Path("data/optimizer_solution.csv"), help="Where to save the solution CSV")
    p.add_argument("--budget", type=float, default=None, help="Monthly budget to respect (overrides --savings-pct)")
    p.add_argument("--savings-pct", type=float, default=0.10, help="Target savings as fraction of current avg total (default 0.10)")
    p.add_argument("--protected-categories", type=str, default="", help="Comma-separated categories to keep at avg_monthly (e.g., 'Beauty,Coffee')")
    p.add_argument(
        "--category-amount",
        action="append",
        nargs=2,
        metavar=("CATEGORY", "AMOUNT"),
        default=[],
        help="Override a category's current monthly amount (may be supplied more than once)",
    )
    args = p.parse_args()

    try:
        df = pd.read_csv(args.input).set_index("category")
    except FileNotFoundError:
        p.error(f"Input file not found: {args.input}")
    except (ValueError, KeyError):
        p.error("Input CSV must contain a 'category' column")

    if "avg_monthly" not in df.columns or "fixed_amount" not in df.columns:
        p.error("Input CSV must contain 'avg_monthly' and 'fixed_amount' columns")

    if not 0 <= args.savings_pct < 1:
        p.error("--savings-pct must be between 0 (inclusive) and 1 (exclusive)")

    for category, raw_amount in args.category_amount:
        if category not in df.index:
            p.error(f"Unknown category for --category-amount: {category}")
        try:
            amount = float(raw_amount)
        except ValueError:
            p.error(f"Invalid amount for {category}: {raw_amount}")
        if amount < 0:
            p.error(f"Amount for {category} cannot be negative")
        df.loc[category, "avg_monthly"] = amount

    # Budget to respect (monthly). Default: current average total minus savings_pct.
    # This must be calculated after any profile-based category overrides.
    total_avg = float(df["avg_monthly"].sum())

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
    status = prob.solve(pl.PULP_CBC_CMD(msg=False))
    if pl.LpStatus[status] != "Optimal":
        minimum_spend = sum(
            max(
                float(df.loc[cat, "avg_monthly"]) if cat in protected else float(df.loc[cat, "fixed_amount"]),
                float(df.loc[cat, "avg_monthly"]) * category_bounds.get(cat, (0.0, 2.0))[0],
            )
            for cat in df.index
        )
        print(
            f"Optimization could not meet the requested budget of {budget:,.0f} TL. "
            f"The minimum feasible budget is {minimum_spend:,.0f} TL.",
            file=sys.stderr,
        )
        raise SystemExit(2)

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
    args.output.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.output, index=False)
    print(f"Saved optimizer solution to {args.output}")


if __name__ == "__main__":
    main()
