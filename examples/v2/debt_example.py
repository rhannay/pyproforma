"""
Example usage of DebtLine in PyProforma v2 API.

This example demonstrates how to use the DebtLine generator to model
debt financing with multiple issues, principal/interest payments, and
outstanding balances.
"""

from pyproforma.v2 import (
    Assumption,
    DebtLine,
    FixedLine,
    FormulaLine,
    ProformaModel,
)


class FinancialModelWithDebt(ProformaModel):
    """
    A financial model with revenue, expenses, and debt financing.

    This model demonstrates:
    - Basic revenue and expense projections
    - Debt financing with the DebtLine generator
    - Using generated debt fields (principal, interest, etc.) in formulas
    - Multiple debt issues in different years
    """

    # =============================================================================
    # ASSUMPTIONS
    # =============================================================================
    expense_ratio = Assumption(value=0.6, label="Expense Ratio")
    interest_rate = Assumption(value=0.05, label="Interest Rate (5%)")
    debt_term = Assumption(value=10, label="Debt Term (years)")

    # =============================================================================
    # REVENUE AND EXPENSES
    # =============================================================================
    revenue = FixedLine(
        values={
            2024: 2000000,
            2025: 2200000,
            2026: 2420000,
            2027: 2662000,
            2028: 2928200,
        },
        label="Revenue",
    )

    expenses = FormulaLine(
        formula=lambda a, li, t: li.revenue[t] * a.expense_ratio,
        label="Operating Expenses",
    )

    ebitda = FormulaLine(
        formula=lambda a, li, t: li.revenue[t] - li.expenses[t],
        label="EBITDA",
    )

    # =============================================================================
    # DEBT FINANCING
    # =============================================================================
    # Define par amounts for bond issues
    par_amounts = FixedLine(
        values={
            2024: 3000000,  # Initial bond issue of $3M
            2025: 0,        # No new debt in 2025
            2026: 1500000,  # Additional bond issue of $1.5M
            2027: 0,
            2028: 0,
        },
        label="Bond Par Amounts",
    )

    # Debt generator - produces four fields:
    # - debt_principal: Principal payments
    # - debt_interest: Interest payments
    # - debt_debt_outstanding: Outstanding balance at period end
    # - debt_proceeds: New debt issued (bond proceeds)
    debt = DebtLine(
        par_amount_name="par_amounts",
        interest_rate_name="interest_rate",
        term_name="debt_term",
        label="Long-term Debt",
    )

    # =============================================================================
    # INCOME STATEMENT ITEMS
    # =============================================================================
    # Use generated debt fields in formulas
    interest_expense = FormulaLine(
        formula=lambda a, li, t: li.debt_interest[t],
        label="Interest Expense",
    )

    net_income = FormulaLine(
        formula=lambda a, li, t: li.ebitda[t] - li.interest_expense[t],
        label="Net Income",
    )

    # =============================================================================
    # DEBT SERVICE COVERAGE
    # =============================================================================
    total_debt_service = FormulaLine(
        formula=lambda a, li, t: li.debt_principal[t] + li.debt_interest[t],
        label="Total Debt Service",
    )

    debt_service_coverage = FormulaLine(
        formula=lambda a, li, t: (
            li.ebitda[t] / li.total_debt_service[t]
            if li.total_debt_service[t] > 0
            else 0
        ),
        label="Debt Service Coverage Ratio",
    )


if __name__ == "__main__":
    # Create the model
    model = FinancialModelWithDebt(periods=[2024, 2025, 2026, 2027, 2028])

    print("=" * 80)
    print("FINANCIAL MODEL WITH DEBT FINANCING")
    print("=" * 80)
    print()

    # Display Income Statement
    print("INCOME STATEMENT")
    print("-" * 80)
    print(f"{'Year':<12} {'Revenue':>12} {'Expenses':>12} {'EBITDA':>12} "
          f"{'Interest':>12} {'Net Income':>12}")
    print("-" * 80)
    for year in model.periods:
        print(
            f"{year:<12} "
            f"${model.li.revenue[year]:>11,.0f} "
            f"${model.li.expenses[year]:>11,.0f} "
            f"${model.li.ebitda[year]:>11,.0f} "
            f"${model.li.interest_expense[year]:>11,.0f} "
            f"${model.li.net_income[year]:>11,.0f}"
        )
    print()

    # Display Debt Schedule
    print("DEBT FINANCING")
    print("-" * 80)
    print(f"{'Year':<12} {'New Issues':>12} {'Principal':>12} {'Interest':>12} "
          f"{'Total DS':>12} {'Outstanding':>12}")
    print("-" * 80)
    for year in model.periods:
        print(
            f"{year:<12} "
            f"${model.li.debt_proceeds[year]:>11,.0f} "
            f"${model.li.debt_principal[year]:>11,.0f} "
            f"${model.li.debt_interest[year]:>11,.0f} "
            f"${model.li.total_debt_service[year]:>11,.0f} "
            f"${model.li.debt_debt_outstanding[year]:>11,.0f}"
        )
    print()

    # Display Debt Metrics
    print("DEBT METRICS")
    print("-" * 80)
    print(f"{'Year':<12} {'DSCR':>12}")
    print("-" * 80)
    for year in model.periods:
        dscr = model.li.debt_service_coverage[year]
        print(f"{year:<12} {dscr:>12.2f}x")
    print()

    # Summary insights
    print("KEY INSIGHTS")
    print("-" * 80)
    print(f"Total debt issued: ${model.li.debt_proceeds[2024] + model.li.debt_proceeds[2026]:,.0f}")
    print(f"Debt outstanding at end of 2028: ${model.li.debt_debt_outstanding[2028]:,.0f}")
    print(
        f"Average annual debt service (2024-2028): "
        f"${sum(model.li.total_debt_service[y] for y in model.periods) / len(model.periods):,.0f}"
    )
    print(f"Minimum DSCR: {min(model.li.debt_service_coverage[y] for y in model.periods):.2f}x")
    print()

    # Example of accessing through different notations
    print("ACCESSING VALUES")
    print("-" * 80)
    revenue_result = model["revenue"]  # Regular line items work with subscript
    print(f"Revenue in 2024 (via model['revenue'][2024]): ${revenue_result[2024]:,.0f}")
    print(f"Debt principal in 2024 (via model.li.debt_principal[2024]): ${model.li.debt_principal[2024]:,.0f}")
    print()

    print("=" * 80)
    print("Model created successfully!")
    print("=" * 80)
