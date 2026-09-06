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

SmartBudget uses transaction history plus the following user choices:

- monthly income and fixed housing cost
- protected categories, such as housing or health insurance
- a target percentage reduction from current average spending
- optional transaction CSV with `category`, `description`, `amount`, and `date` columns


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

4. Run the optimizer with savings goal (examples):

```bash
# 20% savings target with category bounds
python optimizer.py --savings-pct 0.20 --protected-categories Beauty

# 30% savings target
python optimizer.py --savings-pct 0.30

# Explicit monthly budget (4000 TL)
python optimizer.py --budget 40000

# Protect multiple categories
python optimizer.py --savings-pct 0.25 --protected-categories "Beauty,Groceries,Coffee"
```

5. View the optimized budget recommendation:

```bash
python compare_budgets.py
```

Or start the interactive app:

```bash
streamlit run app.py
```

The app can import a transaction CSV. It must include `category`, `description`,
`amount`, and `date` columns. An import replaces the demo data in `data/expenses.csv`
and recreates the analysis files.

## Tests

Run the optimizer regression tests with:

```bash
python -m unittest test_optimizer.py
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

## Optimizer Features

- **Recurring detection:** automatically identifies fixed monthly expenses (rent, insurance, subscriptions)
- **L1 minimization:** minimizes total deviation from current spending averages (preserves category balance)
- **Category bounds:** enforces realistic min/max spend per category:
  - Essential (Groceries, Utilities): minimum 70-75% of current
  - Protected (Beauty, Housing, Insurance): fixed at current level
  - Discretionary categories retain a minimum allowance; transportation, delivery, and other spending cannot be reduced to zero
- **Protected categories:** specify which categories to keep at current level (e.g., `--protected-categories Beauty`)
- **Savings targets:** achieve desired savings by % or explicit budget

> The optimizer may report an infeasible result when a target conflicts with protected or minimum category amounts. In that case, it reports the minimum feasible monthly budget instead of producing an unrealistic plan.

## Example: 60k Monthly Income Scenario

**Input:**
- Monthly income: 60,000 TL
- Housing (rent): 30,000 TL
- Beauty: 3,000 TL (protected)
- Savings goal: 20%

**Output:**
- Current spending: ~57,000 TL
- Recommended budget: ~45,500 TL
- **Monthly savings: 11,500 TL**

**Category-level recommendations:**
- Housing, Beauty, Insurance, Utilities: kept at current level
- Groceries: reduced to 75% of current (-25%)
- Restaurants, Shopping, Travel: reduced by 45-70%
- Transportation, Delivery, Other: reduced within their configured minimum allowances

## Requirements

See `requirements.txt` (project includes `pandas`, `matplotlib`, `pulp`, etc.).

## Outputs

- Current spending analysis
- Spending patterns by category
- Recommended budget by category
- Expected monthly savings
- Comparison between current and optimized spending
- Visualizations
- AI-generated explanations and recommendations
