import streamlit as st
import pandas as pd
import subprocess
import os
import sys
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data"
REQUIRED_EXPENSE_COLUMNS = {"category", "description", "amount", "date"}


def import_expenses(uploaded_file):
    """Validate an uploaded transaction CSV and regenerate analysis files."""
    try:
        uploaded_df = pd.read_csv(uploaded_file)
    except (UnicodeDecodeError, pd.errors.ParserError) as error:
        return False, f"CSV could not be read: {error}"

    missing_columns = REQUIRED_EXPENSE_COLUMNS - set(uploaded_df.columns)
    if missing_columns:
        return False, f"Missing required columns: {', '.join(sorted(missing_columns))}"
    if uploaded_df.empty:
        return False, "The uploaded CSV has no transactions."
    if (pd.to_numeric(uploaded_df["amount"], errors="coerce") < 0).any() or pd.to_numeric(uploaded_df["amount"], errors="coerce").isna().any():
        return False, "The 'amount' column must contain non-negative numbers."
    if pd.to_datetime(uploaded_df["date"], errors="coerce").isna().any():
        return False, "The 'date' column must contain valid dates."

    uploaded_df.to_csv(DATA_DIR / "expenses.csv", index=False)
    result = subprocess.run(
        [sys.executable, "analysis.py"], capture_output=True, text=True, cwd=PROJECT_DIR
    )
    if result.returncode != 0:
        return False, result.stderr or result.stdout or "Analysis failed."
    return True, f"Imported {len(uploaded_df):,} transactions and refreshed the analysis."

# Page config
st.set_page_config(
    page_title="Smart Budget Agent",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .saving-positive {
        color: #28a745;
        font-weight: bold;
    }
    .category-keep {
        color: #28a745;
    }
    .category-reduce {
        color: #ffc107;
    }
    .category-cut {
        color: #dc3545;
    }
    </style>
""", unsafe_allow_html=True)

st.title("💰 Smart Budget Agent")
st.markdown("*Personalized AI-powered budget optimization*")

# Sidebar for user inputs
st.sidebar.header("📊 Your Financial Profile")
st.sidebar.markdown("---")

uploaded_file = st.sidebar.file_uploader(
    "Transaction CSV (optional)", type="csv",
    help="Required columns: category, description, amount, date. Uploading replaces the demo transaction data."
)
if uploaded_file is not None:
    file_key = f"{uploaded_file.name}:{uploaded_file.size}"
    if st.session_state.get("imported_file_key") != file_key:
        with st.sidebar.spinner("Importing transactions..."):
            imported, message = import_expenses(uploaded_file)
        if imported:
            st.session_state.imported_file_key = file_key
            st.session_state.optimization_done = False
            st.sidebar.success(message)
        else:
            st.sidebar.error(message)

income = st.sidebar.number_input(
    "Monthly Income (₺)",
    min_value=20000,
    max_value=200000,
    value=60000,
    step=5000,
    help="Your total monthly income"
)

housing = st.sidebar.number_input(
    "Housing/Rent (₺)",
    min_value=5000,
    max_value=100000,
    value=30000,
    step=5000,
    help="Fixed monthly housing cost"
)

beauty = st.sidebar.number_input(
    "Beauty & Self-Care (₺)",
    min_value=500,
    max_value=50000,
    value=3000,
    step=500,
    help="Protected beauty and personal care budget"
)

st.sidebar.markdown("---")
st.sidebar.header("🎯 Optimization Settings")

savings_pct = st.sidebar.slider(
    "Spending Reduction Target (%)",
    min_value=5,
    max_value=50,
    value=20,
    step=5,
    help="The percentage to reduce from your current average monthly spending."
)

protected_categories = st.sidebar.multiselect(
    "Protected Categories",
    options=["Housing", "Beauty", "Health Insurance", "Gym"],
    default=["Beauty", "Housing"],
    help="Categories to keep unchanged"
)

st.sidebar.markdown("---")

# Main area - Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📈 Overview", "📊 Analysis", "💡 AI Insights", "📋 90-Day Plan"])

# Optimization button
if st.sidebar.button("🚀 Optimize Now!", use_container_width=True, type="primary"):
    st.session_state.run_optimization = True

# Run optimization if button clicked
if "run_optimization" in st.session_state and st.session_state.run_optimization:
    with st.spinner("🔄 Running optimization..."):
        try:
            # Build optimizer command
            protected_str = ",".join(protected_categories) if protected_categories else ""
            cmd = [
                sys.executable, "optimizer.py",
                "--savings-pct", str(savings_pct / 100),
                "--category-amount", "Housing", str(housing),
                "--category-amount", "Beauty", str(beauty),
            ]
            if protected_str:
                cmd.extend(["--protected-categories", protected_str])
            
            # Run optimizer
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_DIR)
            
            if result.returncode == 0:
                st.session_state.optimization_done = True
                st.session_state.last_income = income
                st.session_state.last_housing = housing
                st.session_state.last_beauty = beauty
                st.session_state.last_savings = savings_pct
                st.session_state.run_optimization = False
                st.success("✅ Optimization complete!")
            else:
                error_msg = result.stderr if result.stderr else result.stdout if result.stdout else "Unknown error"
                st.error(f"❌ Optimization failed")
                st.code(error_msg, language="text")
                st.session_state.run_optimization = False
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            st.session_state.run_optimization = False

# Display results
if "optimization_done" in st.session_state and st.session_state.optimization_done:
    try:
        # Load data
        input_df = pd.read_csv(DATA_DIR / "optimizer_input.csv")
        solution_df = pd.read_csv(DATA_DIR / "optimizer_solution.csv")
        recurring_df = pd.read_csv(DATA_DIR / "recurring.csv")

        # Keep the dashboard's baseline aligned with the profile values passed
        # to the optimizer; the source CSV remains the unmodified history.
        input_df.loc[input_df["category"] == "Housing", "avg_monthly"] = housing
        input_df.loc[input_df["category"] == "Beauty", "avg_monthly"] = beauty
        
        # Calculate metrics
        current_total = input_df["avg_monthly"].sum()
        recommended_total = solution_df["recommended_spend"].sum()
        savings = current_total - recommended_total
        savings_pct_actual = (savings / current_total) * 100
        annual_savings = savings * 12
        monthly_after_savings = income - recommended_total
        income_target_savings = income * (savings_pct / 100)
        
        # TAB 1: OVERVIEW
        with tab1:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "💰 Monthly Income",
                    f"₺{income:,.0f}",
                    help="Your monthly income"
                )
            
            with col2:
                st.metric(
                    "📊 Current Spend",
                    f"₺{current_total:,.0f}",
                    f"-₺{savings:,.0f}",
                    help="Current vs Optimized spending"
                )
            
            with col3:
                st.metric(
                    "✅ Optimized Budget",
                    f"₺{recommended_total:,.0f}",
                    help="Recommended monthly budget"
                )
            
            with col4:
                st.metric(
                    "🎯 Monthly Savings",
                    f"₺{savings:,.0f}",
                    f"{savings_pct_actual:.1f}%",
                    delta_color="inverse"
                )

            if monthly_after_savings < 0:
                st.warning(f"Your optimized budget is ₺{-monthly_after_savings:,.0f} above your monthly income. Consider a higher reduction target or lower fixed costs.")
            elif savings < income_target_savings:
                st.info(f"This plan reduces spending by ₺{savings:,.0f}/month. Your {savings_pct}% income-based savings goal would be ₺{income_target_savings:,.0f}/month.")
            
            st.markdown("---")
            
            # Financial snapshot
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("💡 Financial Snapshot")
                snapshot_data = {
                    "Metric": ["Monthly Income", "Current Spend", "Optimized Budget", "Monthly Savings", "Annual Savings", "After-Savings Budget"],
                    "Amount": [f"₺{income:,.0f}", f"₺{current_total:,.0f}", f"₺{recommended_total:,.0f}", f"₺{savings:,.0f}", f"₺{annual_savings:,.0f}", f"₺{monthly_after_savings:,.0f}"]
                }
                st.dataframe(pd.DataFrame(snapshot_data), use_container_width=True, hide_index=True)
            
            with col2:
                st.subheader("📈 Budget Comparison")
                comparison_data = {
                    "Budget Type": ["Current", "Optimized", "Difference"],
                    "Amount": [current_total, recommended_total, -savings],
                    "% of Income": [
                        f"{(current_total/income)*100:.1f}%",
                        f"{(recommended_total/income)*100:.1f}%",
                        f"{-(savings/income)*100:.1f}%"
                    ]
                }
                st.dataframe(pd.DataFrame(comparison_data), use_container_width=True, hide_index=True)
            
            # Visualization
            st.markdown("---")
            st.subheader("📊 Spending Breakdown")
            
            def draw_spending_pie(ax, frame, amount_column, title):
                """Draw a readable pie chart, grouping tiny slices into Other."""
                chart_data = frame[["category", amount_column]].copy()
                chart_data = chart_data[chart_data[amount_column] > 0]
                total = chart_data[amount_column].sum()
                small_slice = chart_data[amount_column] / total < 0.03

                # Tiny categories make a pie chart unreadable.  Keep their total,
                # but present it as one slice and list every resulting slice below.
                small_total = chart_data.loc[small_slice, amount_column].sum()
                chart_data = chart_data.loc[~small_slice]
                if small_total > 0:
                    chart_data = pd.concat(
                        [chart_data, pd.DataFrame([{"category": "Other small expenses", amount_column: small_total}])],
                        ignore_index=True,
                    )
                chart_data = chart_data.sort_values(amount_column, ascending=False)

                wedges, _, _ = ax.pie(
                    chart_data[amount_column],
                    autopct=lambda pct: f"{pct:.1f}%" if pct >= 4 else "",
                    startangle=90,
                    pctdistance=0.7,
                    textprops={"fontsize": 9},
                )
                ax.set_title(title, fontsize=12, fontweight="bold")
                ax.legend(
                    wedges,
                    chart_data["category"],
                    loc="upper center",
                    bbox_to_anchor=(0.5, -0.08),
                    ncol=2,
                    fontsize=8,
                    frameon=False,
                )

            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7), constrained_layout=True)
            draw_spending_pie(ax1, input_df, "avg_monthly", "Current Spending Distribution")
            draw_spending_pie(ax2, solution_df, "recommended_spend", "Optimized Spending Distribution")
            st.pyplot(fig)
            plt.close(fig)
        
        # TAB 2: DETAILED ANALYSIS
        with tab2:
            st.subheader("📋 Category-by-Category Breakdown")
            
            # Merge data for comparison
            comparison = input_df.merge(solution_df, on="category", suffixes=("_current", "_recommended"))
            comparison["Change"] = comparison["recommended_spend"] - comparison["avg_monthly_current"]
            comparison["Change %"] = (comparison["Change"] / comparison["avg_monthly_current"] * 100).round(1)
            comparison["Status"] = comparison["Change %"].apply(
                lambda x: "✅ KEEP" if abs(x) < 5 else ("📉 REDUCE" if x >= -50 else "⚠️ CUT HARD")
            )
            
            # Display table
            display_df = comparison[["category", "avg_monthly_current", "recommended_spend", "Change", "Change %", "Status"]].copy()
            display_df.columns = ["Category", "Current (₺)", "Recommended (₺)", "Change (₺)", "Change (%)", "Status"]
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            
            # Top reductions
            st.markdown("---")
            st.subheader("🔥 Top Savings Opportunities")
            
            top_reductions = comparison.nsmallest(5, "Change")[["category", "avg_monthly_current", "recommended_spend", "Change"]].copy()
            top_reductions = top_reductions[top_reductions["Change"] < 0]  # Only cuts
            top_reductions["Change"] = -top_reductions["Change"]
            top_reductions.columns = ["Category", "Current (₺)", "Recommended (₺)", "Potential Savings (₺)"]
            
            st.dataframe(top_reductions, use_container_width=True, hide_index=True)
            
            # Visualization - Change chart
            st.markdown("---")
            fig, ax = plt.subplots(figsize=(12, 6))
            
            sorted_comparison = comparison.sort_values("Change %")
            colors = ["#dc3545" if x < -50 else "#ffc107" if x < 0 else "#28a745" for x in sorted_comparison["Change %"]]
            
            ax.barh(sorted_comparison["category"], sorted_comparison["Change %"], color=colors)
            ax.set_xlabel("Change (%)", fontweight='bold')
            ax.set_title("Category Changes: Current → Optimized", fontsize=12, fontweight='bold')
            ax.axvline(x=0, color='black', linestyle='-', linewidth=0.5)
            
            st.pyplot(fig)
        
        # TAB 3: AI INSIGHTS
        with tab3:
            st.subheader("🤖 AI Agent Analysis")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown("""
                ### 💡 Key Insights & Recommendations
                """)
                
                # Top savings categories
                st.markdown("**Top 5 Savings Opportunities:**")
                top_5 = comparison.nsmallest(5, "Change")[["category", "Change"]].copy()
                top_5 = top_5[top_5["Change"] < 0]  # Only cuts
                top_5["Change"] = -top_5["Change"]
                
                for idx, row in top_5.iterrows():
                    st.markdown(f"- **{row['category']}**: Save ₺{row['Change']:,.0f}/month")
                
                st.markdown(f"""
                #### 🎯 Your Transformation
                - **Annual Savings**: ₺{annual_savings:,.0f}
                - **3-Month Fund**: ₺{savings * 3:,.0f} (emergency fund achievable)
                - **5-Year Wealth**: ₺{annual_savings * 5:,.0f}
                """)
                
                st.markdown("#### 🛡️ Protected Categories")
                for cat in protected_categories:
                    protected_amount = comparison[comparison["category"] == cat]["avg_monthly_current"].values
                    if len(protected_amount) > 0:
                        st.markdown(f"✅ **{cat}**: ₺{protected_amount[0]:,.0f}/month (unchanged)")
            
            with col2:
                st.markdown("#### 📊 Summary Statistics")
                summary_stats = {
                    "Current Spend": f"₺{current_total:,.0f}",
                    "Optimized": f"₺{recommended_total:,.0f}",
                    "Monthly Savings": f"₺{savings:,.0f}",
                    "Savings %": f"{savings_pct_actual:.1f}%",
                    "Annual Savings": f"₺{annual_savings:,.0f}",
                }
                for key, value in summary_stats.items():
                    st.info(f"**{key}**: {value}")
            
            # Recurring expenses
            st.markdown("---")
            st.subheader("🔄 Recurring Expenses Analysis")
            
            recurring_expenses = recurring_df[recurring_df["is_recurring"]].copy()
            if len(recurring_expenses) > 0:
                st.markdown(f"**{len(recurring_expenses)} recurring expenses identified** (appearing in ≥2 months)")

                recurring_summary = recurring_expenses.groupby("category")["avg_amount"].sum().sort_values(ascending=False)
                st.dataframe(
                    recurring_summary.rename("Total (₺)"),
                    use_container_width=True
                )
                
                total_recurring = recurring_expenses["avg_amount"].sum()
                st.markdown(f"""
                **Total Recurring: ₺{total_recurring:,.0f}/month**
                
                💡 **Action**: Review these charges monthly. 
                - Cancel unused subscriptions
                - Negotiate utility rates
                - Consider alternatives for fixed services
                """)
            else:
                st.info("No recurring expenses were identified in the available history.")
        
        # TAB 4: 90-DAY PLAN
        with tab4:
            st.subheader("📅 90-Day Action Plan")
            st.markdown("*Progressive implementation strategy for sustainable savings*")
            
            plan_data = {
                "Phase": ["WEEK 1-4", "WEEK 5-8", "WEEK 9-12"],
                "Focus": [
                    "Quick Wins & Awareness",
                    "Behavior Change",
                    "Optimization & Automation"
                ],
                "Target Savings": [
                    f"₺{savings * 0.2:,.0f}",
                    f"₺{savings * 0.35:,.0f}",
                    f"₺{savings:,.0f}"
                ],
                "Key Actions": [
                    "• Cancel unused subscriptions\n• Start meal prep\n• Reduce delivery apps\n• Track expenses",
                    "• Switch to public transit\n• 30-day purchase rule\n• Home coffee routine\n• Reduce restaurants",
                    "• Automate transfers\n• Review & adjust\n• Plan investment\n• Celebrate progress"
                ]
            }
            
            plan_df = pd.DataFrame(plan_data)
            st.dataframe(plan_df, use_container_width=True, hide_index=True)
            
            # Phase breakdown
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("### 🚀 Phase 1: Weeks 1-4")
                st.markdown(f"""
                **Quick Wins**
                
                📊 Target: ₺{savings * 0.2:,.0f} saved
                
                ✓ Cancel unused subscriptions
                ✓ Start meal prep (save on delivery)
                ✓ Track all expenses
                ✓ Set up budget alerts
                
                💰 Expected: -₺{savings * 0.2:,.0f}/month
                """)
            
            with col2:
                st.markdown("### 🎯 Phase 2: Weeks 5-8")
                st.markdown(f"""
                **Behavior Change**
                
                📊 Target: ₺{savings * 0.35:,.0f} saved
                
                ✓ Use public transit daily
                ✓ 30-day purchase rule
                ✓ Cook at home 5x/week
                ✓ Review subscriptions
                
                💰 Expected: -₺{savings * 0.35:,.0f}/month
                """)
            
            with col3:
                st.markdown("### ✨ Phase 3: Weeks 9-12")
                st.markdown(f"""
                **Optimization**
                
                📊 Target: ₺{savings:,.0f} saved
                
                ✓ Automate savings transfer
                ✓ Fine-tune budget
                ✓ Invest savings
                ✓ Plan next steps
                
                💰 Expected: ₺{annual_savings:,.0f}/year
                """)
            
            st.markdown("---")
            st.markdown(f"""
            ### 🏆 Your Success Metrics
            
            At the end of 90 days, you'll have:
            - 💰 **Saved**: ₺{savings * 3:,.0f}
            - 📈 **Annual savings**: ₺{annual_savings:,.0f}
            - 🎯 **New habits**: Automated & sustainable
            - 🚀 **Emergency fund**: Started building
            """)
    
    except Exception as e:
        import traceback
        st.error(f"❌ Error loading results")
        st.code(str(e), language="text")
        st.info("Traceback:")
        st.code(traceback.format_exc(), language="text")

else:
    # Initial state - before optimization
    st.info("""
    👋 **Welcome to Smart Budget Agent!**
    
    1. Set your financial profile in the sidebar
    2. Choose your savings target
    3. Click "🚀 Optimize Now!"
    4. Explore the analysis and get personalized recommendations
    """)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        ### 🎯 How It Works
        
        **Step 1: Profile**
        Set your income and fixed costs
        
        **Step 2: Optimize**
        AI finds optimal spending plan
        
        **Step 3: Insights**
        Get personalized tips & timeline
        """)
    
    with col2:
        st.markdown("""
        ### 🧠 Advanced Features
        
        ✅ Linear Programming optimization
        ✅ AI-powered recommendations
        ✅ Recurring expense detection
        ✅ 90-day implementation plan
        ✅ Multi-scenario testing
        """)
    
    with col3:
        st.markdown("""
        ### 💡 Pro Tips
        
        💰 Start with 20% savings target
        🛡️ Protect essential categories
        📊 Review recurring charges
        🔄 Adjust monthly as needed
        """)
