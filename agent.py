#!/usr/bin/env python3
"""Rule-based narrative reporting for SmartBudget optimization results.

This module does not call an LLM.  It turns the deterministic analysis and
optimizer outputs into a readable command-line report.
"""
import pandas as pd


class BudgetAgent:
    """Create a deterministic, personalized report from saved budget outputs."""

    def __init__(self, monthly_income=60000, housing=30000, beauty=3000):
        """Initialize agent with user profile."""
        self.monthly_income = monthly_income
        self.housing = housing
        self.beauty = beauty
        self.savings_buffer = monthly_income * 0.20  # Recommended 20% savings

        # Load data
        self.input_df = pd.read_csv("data/optimizer_input.csv").set_index("category")
        self.solution_df = pd.read_csv("data/optimizer_solution.csv").set_index("category")
        self.recurring_df = pd.read_csv("data/recurring.csv")

        # Compute metrics
        self.current_total = self.input_df["avg_monthly"].sum()
        self.recommended_total = self.solution_df["recommended_spend"].sum()
        self.savings = self.current_total - self.recommended_total
        self.savings_pct = (self.savings / self.current_total) * 100

    def executive_summary(self):
        """Generate executive summary."""
        print("\n" + "="*70)
        print("SMARTBUDGET - PERSONALIZED FINANCIAL ANALYSIS")
        print("="*70)
        print(f"\n👤 USER PROFILE:")
        print(f"   Monthly Income:        ₺{self.monthly_income:,}")
        print(f"   Housing (Rent):        ₺{self.housing:,}")
        print(f"   Beauty & Self-Care:    ₺{self.beauty:,}")
        print(f"   Reference Savings:     ₺{self.savings_buffer:,.0f} (20%)")
        
        print(f"\n💰 FINANCIAL SNAPSHOT:")
        print(f"   Current Monthly Spend: ₺{self.current_total:,.0f}")
        print(f"   Optimized Budget:      ₺{self.recommended_total:,.0f}")
        print(f"   Potential Savings:     ₺{self.savings:,.0f} ({self.savings_pct:.1f}%)")
        print(f"   Income After Savings:  ₺{self.monthly_income - self.recommended_total:,.0f}")

    def category_analysis(self):
        """Detailed analysis per category."""
        print(f"\n📊 CATEGORY-BY-CATEGORY BREAKDOWN:\n")

        comparison = pd.DataFrame({
            "current": self.input_df["avg_monthly"],
            "recommended": self.solution_df["recommended_spend"],
            "fixed": self.input_df["fixed_amount"],
        })
        comparison["change"] = comparison["recommended"] - comparison["current"]
        comparison["pct_change"] = (comparison["change"] / comparison["current"] * 100).round(1)

        # Sort by magnitude of savings
        comparison = comparison.sort_values("change")

        for cat in comparison.index:
            current = comparison.loc[cat, "current"]
            recommended = comparison.loc[cat, "recommended"]
            fixed = comparison.loc[cat, "fixed"]
            change = comparison.loc[cat, "change"]
            pct = comparison.loc[cat, "pct_change"]

            # Determine status icon
            if abs(change) < 1:
                status = "✅ KEEP"
            elif pct < -50:
                status = "⚠️  CUT HARD"
            elif pct < 0:
                status = "📉 REDUCE"
            else:
                status = "❌ INCREASE"

            print(f"  {cat:20s} ₺{current:>8,.0f} → ₺{recommended:>8,.0f} " +
                  f"[{pct:>6.1f}%] {status}")

    def insights_and_recommendations(self):
        """Print deterministic insights and actionable recommendations."""
        print(f"\n💡 INSIGHTS & RECOMMENDATIONS:\n")

        # Identify savings opportunities
        comparison = pd.DataFrame({
            "current": self.input_df["avg_monthly"],
            "recommended": self.solution_df["recommended_spend"],
        })
        comparison["savings"] = comparison["current"] - comparison["recommended"]
        comparison["pct"] = (comparison["savings"] / comparison["current"] * 100).round(0)

        top_savings = comparison[comparison["savings"] > 100].nlargest(5, "savings")

        print("  1️⃣  HIGHEST IMPACT CUTS:")
        for cat in top_savings.index:
            savings = top_savings.loc[cat, "savings"]
            pct = top_savings.loc[cat, "pct"]
            print(f"     → {cat}: Save ₺{savings:,.0f}/month ({int(pct)}% reduction)")
            self._category_tips(cat, int(pct))

        # Identify protected categories
        protected = self.input_df[
            (self.input_df["fixed_amount"] > 0) & 
            (self.input_df["fixed_amount"] == self.input_df["avg_monthly"])
        ]
        print(f"\n  2️⃣  PROTECTED CATEGORIES (Non-negotiable):")
        for cat in protected.index:
            amount = protected.loc[cat, "avg_monthly"]
            reason = self._protection_reason(cat)
            print(f"     → {cat}: ₺{amount:,.0f} {reason}")

        # Savings achievement analysis
        print(f"\n  3️⃣  SAVINGS ACHIEVEMENT:")
        print(f"     Current budget: ₺{self.current_total:,.0f}")
        print(f"     New budget:     ₺{self.recommended_total:,.0f}")
        print(f"     Monthly gain:   ₺{self.savings:,.0f}")
        print(f"     Annual gain:    ₺{self.savings * 12:,.0f}")
        print(f"\n     ✨ With ₺{self.savings:,.0f}/month savings:")
        print(f"        • Emergency fund contribution in 3 months: ₺{self.savings * 3:,.0f}")
        print(f"        • Annual savings capacity: ₺{self.savings * 12:,.0f}")

    def _category_tips(self, category, pct_reduction):
        """Generate actionable tips per category."""
        tips = {
            "Transportation": [
                "Use public transit for daily commute (save 80-90%)",
                "Carpool or ride-sharing for occasional trips",
                "Consider a cheaper car insurance plan"
            ],
            "Coffee": [
                "Brew coffee at home (costs ~20% of cafe prices)",
                "Use a reusable thermos; bring from home",
                "Occasional cafe visits (2x/month instead of daily)"
            ],
            "Restaurants": [
                "Cook meals at home 5-6 days/week",
                "Reserve dining out for special occasions (2x/month)",
                "Pack lunch for work to reduce meal costs"
            ],
            "Delivery": [
                "Pick up food instead of delivery (save 25-30%)",
                "Batch shop at grocery store + cook at home",
                "Use delivery only for special occasions"
            ],
            "Shopping": [
                "Implement 30-day rule: wait before non-essential purchases",
                "Shop with a list; avoid impulse buys",
                "Use discount codes, seasonal sales, secondhand options"
            ],
            "Travel": [
                "Vacation budget: plan regional trips (cheaper than international)",
                "Book flights 2-3 months in advance",
                "Consider staycations or road trips vs flights"
            ],
            "Entertainment": [
                "Use free events (parks, museums on discount days)",
                "Share subscriptions (Netflix, Spotify) with friends",
                "Enjoy low-cost activities (hiking, board games)"
            ]
        }
        if category in tips:
            print(f"     💬 Tips for {category}:")
            for tip in tips[category][:2]:
                print(f"        • {tip}")

    def _protection_reason(self, category):
        """Explain why a category is protected."""
        reasons = {
            "Housing": "(Essential: shelter)",
            "Beauty": "(Personal preference: protected)",
            "Groceries": "(Essential: nutrition)",
            "Health Insurance": "(Essential: health & safety)",
            "Utilities": "(Essential: water, electricity)",
            "Gym": "(Health: fitness & wellness)",
            "Subscriptions": "(Recurring: software/services)",
            "AI Tools": "(Work/productivity: professional tools)"
        }
        return reasons.get(category, "(Essential or recurring)")

    def recurring_pattern_analysis(self):
        """Analyze recurring payment patterns."""
        print(f"\n🔄 RECURRING EXPENSE ANALYSIS:\n")

        recurring = self.recurring_df[self.recurring_df["is_recurring"] == True]
        if len(recurring) > 0:
            total_recurring = recurring["avg_amount"].sum()
            print(f"  Identified {len(recurring)} recurring expenses (monthly subscriptions):")
            print(f"  Total recurring: ₺{total_recurring:,.0f}\n")
            for _, row in recurring.iterrows():
                desc = row["description"]
                amt = row["avg_amount"]
                cat = row["category"]
                print(f"    • {desc:30s} ₺{amt:>8,.0f}/mo ({cat})")
            print(f"\n  ➡️  Action: Review these monthly charges. Cancel unused subscriptions.")
        else:
            print("  No recurring patterns detected.")

    def action_plan(self):
        """Concrete 30/60/90 day action plan."""
        print(f"\n📅 90-DAY ACTION PLAN:\n")

        print("  WEEK 1-4 (Quick Wins - Target: 20% savings):")
        print("    ✓ Cancel unused subscriptions (coffee, streaming, gym if duplicate)")
        print("    ✓ Switch to home-cooked meals 5x/week")
        print("    ✓ Reduce delivery orders to 2x/month")
        print("    ✓ Track savings from the selected budget plan")

        print("\n  WEEK 5-8 (Behavior Change - Target: 25% savings):")
        print("    ✓ Build public transit habit; reduce car usage")
        print("    ✓ Implement 30-day rule for all non-essential purchases")
        print("    ✓ Brew coffee at home daily")
        print("    ✓ Reassess category targets after one month")

        print("\n  WEEK 9-12 (Optimization - Target: 20% savings achieved):")
        print(f"    ✓ Automate a ₺{self.savings:,.0f} monthly savings transfer")
        print("    ✓ Review progress and adjust if needed")
        print("    ✓ Plan use of savings (emergency fund, investment, debt payoff)")
        print(f"    ✓ Expected saving: ₺{self.savings:,.0f}/month")

    def final_summary(self):
        """Closing motivational summary."""
        print(f"\n✨ YOUR FINANCIAL TRANSFORMATION:\n")
        current_income_pct = self.current_total / self.monthly_income * 100
        print(f"  Starting point:  You're spending {current_income_pct:.1f}% of your ₺{self.monthly_income:,} income")
        print(f"  End goal:        Save ₺{self.savings:,.0f} and spend ₺{self.recommended_total:,.0f}")
        print(f"\n  This is realistic and achievable. Key insight:")
        print(f"  → You don't need to cut housing or beauty (protected categories)")
        print(f"  → Focus on discretionary spending (restaurants, shopping, transport)")
        print(f"  → Small daily changes compound: ₺{self.savings:,.0f} × 12 = ₺{self.savings * 12:,.0f}/year")
        print(f"\n  Questions? Tweak the optimizer:")
        print(f"  python optimizer.py --savings-pct 0.30 --protected-categories 'Beauty,Groceries'")
        print("\n" + "="*70 + "\n")


def main():
    """Run the deterministic budget report."""
    agent = BudgetAgent(monthly_income=60000, housing=30000, beauty=3000)
    agent.executive_summary()
    agent.category_analysis()
    agent.insights_and_recommendations()
    agent.recurring_pattern_analysis()
    agent.action_plan()
    agent.final_summary()


if __name__ == "__main__":
    main()
