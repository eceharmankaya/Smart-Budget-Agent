# SmartBudget Agent

## Problem Statement

Many people know how much money they spend, but they struggle to understand where their money goes and how they should adjust their spending to reach a specific savings goal.

SmartBudget analyzes a user's spending history, financial goals, and personal spending preferences to create a realistic optimized monthly budget.

Instead of simply telling users to spend less, SmartBudget considers which expenses are fixed, which expenses can be reduced, and which categories the user prefers to protect.

## Project Objective

The objective of SmartBudget is to combine data analysis, mathematical optimization, and agentic AI to help users make better budgeting decisions.

The system will:

- analyze historical spending data
- identify spending patterns and major expense categories
- allow users to define a monthly savings goal
- consider user-defined spending preferences and constraints
- generate an optimized monthly budget
- visualize current and recommended spending
- use an AI agent to explain the results and provide personalized recommendations

## Inputs

SmartBudget will use the following information:


## Quickstart — run locally

1. Create and activate a Python virtual environment (recommended):

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Generate synthetic data (example):

```bash
python generate_data.py
```

3. Run analysis to produce summaries, recurring detection, and plots:

```bash
python analysis.py
```

4. Run the optimizer skeleton (example budget argument):

```bash
python optimizer.py --budget 200000
```

## Generated files

After running the scripts you will find outputs under `data/` and `output/`:

- `data/expenses.csv` — generated transaction-level data
- `data/monthly_summary.csv` — monthly totals, mean, median, rolling average
- `data/category_totals.csv` — total spent per category
- `data/top5_transactions.csv` — five largest individual transactions
- `data/recurring.csv` — detected recurring descriptions (subscriptions, fixed services)
- `data/optimizer_input.csv` — per-category summary used by the optimizer
- `data/optimizer_solution.csv` — optimizer output (recommended spends)
- `output/*.png` — saved plots (monthly and category totals)

## Notes

- Recurring detection heuristic: a `description` is considered recurring when it appears in every month and the coefficient of variation (std/mean) of amounts is small (default cv < 0.2). Adjust thresholds in `analysis.py` as needed.
- The provided `optimizer.py` is a starter LP model (uses PuLP). Customize objective and constraints to match your personal budgeting goals.
- If plots are not generated, ensure you run scripts with the same Python interpreter where `matplotlib` is installed (use the virtualenv `.venv`).

## Requirements

See `requirements.txt` (project includes `pandas`, `matplotlib`, `pulp`, etc.).
SmartBudget will provide:

- Current spending analysis
- Spending patterns by category
- Recommended budget by category
- Expected monthly savings
- Comparison between current and optimized spending
- Visualizations
- AI-generated explanations and recommendations