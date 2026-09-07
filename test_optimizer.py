"""Basic regression tests for the SmartBudget optimizer."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parent
SOURCE_INPUT = PROJECT_DIR / "data" / "optimizer_input.csv"


class OptimizerTests(unittest.TestCase):
    def run_optimizer(self, *arguments):
        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "solution.csv"
            command = [
                sys.executable, "optimizer.py", "--input", str(SOURCE_INPUT),
                "--output", str(output_path), *arguments,
            ]
            result = subprocess.run(command, cwd=PROJECT_DIR, capture_output=True, text=True)
            solution = pd.read_csv(output_path) if output_path.exists() else None
            return result, solution

    def test_savings_target_is_respected(self):
        source = pd.read_csv(SOURCE_INPUT)
        result, solution = self.run_optimizer("--savings-pct", "0.10")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertLessEqual(solution["recommended_spend"].sum(), source["avg_monthly"].sum() * 0.90 + 0.01)

    def test_category_override_is_used(self):
        result, solution = self.run_optimizer(
            "--savings-pct", "0.10", "--category-amount", "Housing", "30000"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        housing = solution.loc[solution["category"] == "Housing"].iloc[0]
        self.assertEqual(housing["avg_monthly"], 30000)
        self.assertEqual(housing["recommended_spend"], 30000)

    def test_zero_savings_preserves_current_budget(self):
        source = pd.read_csv(SOURCE_INPUT).sort_values("category").reset_index(drop=True)
        result, solution = self.run_optimizer("--savings-pct", "0")
        self.assertEqual(result.returncode, 0, result.stderr)
        solution = solution.sort_values("category").reset_index(drop=True)
        pd.testing.assert_series_equal(
            solution["recommended_spend"].round(2),
            source["avg_monthly"].round(2),
            check_names=False,
        )

    def test_protected_category_remains_unchanged(self):
        source = pd.read_csv(SOURCE_INPUT).set_index("category")
        result, solution = self.run_optimizer(
            "--savings-pct", "0.10", "--protected-categories", "Gym"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        gym = solution.set_index("category").loc["Gym"]
        self.assertEqual(gym["recommended_spend"], source.loc["Gym", "avg_monthly"])

    def test_impossible_budget_returns_an_error(self):
        result, solution = self.run_optimizer("--budget", "1")
        self.assertEqual(result.returncode, 2)
        self.assertIsNone(solution)
        self.assertIn("minimum feasible budget", result.stderr)


if __name__ == "__main__":
    unittest.main()
