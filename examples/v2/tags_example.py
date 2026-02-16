"""
Example demonstrating the tags feature in PyProforma v2.

This example shows how to use tags to categorize line items and sum them
by tag in formulas. Tags provide flexible grouping beyond hierarchical categories.
"""

from pyproforma.v2 import FixedLine, FormulaLine, ProformaModel


class FinancialStatementWithTags(ProformaModel):
    """
    Financial model demonstrating tag-based categorization.

    This model uses tags to group line items by:
    - Type: income vs. expense vs. balance_sheet
    - Nature: operational vs. non-operational
    - Reporting: recurring vs. non-recurring

    Tags enable flexible multi-dimensional categorization.
    """

    # Revenue items - all tagged as income and operational
    product_revenue = FixedLine(
        values={2024: 1000, 2025: 1100, 2026: 1210},
        label="Product Revenue",
        tags=["income", "operational", "recurring"],
    )

    service_revenue = FixedLine(
        values={2024: 500, 2025: 550, 2026: 605},
        label="Service Revenue",
        tags=["income", "operational", "recurring"],
    )

    # One-time income
    asset_sale_gain = FixedLine(
        values={2024: 0, 2025: 150, 2026: 0},
        label="Gain on Asset Sale",
        tags=["income", "non-operational", "non-recurring"],
    )

    # Interest income
    interest_income = FixedLine(
        values={2024: 20, 2025: 25, 2026: 30},
        label="Interest Income",
        tags=["income", "non-operational", "recurring"],
    )

    # Operating expenses
    cost_of_goods_sold = FixedLine(
        values={2024: 600, 2025: 660, 2026: 726},
        label="Cost of Goods Sold",
        tags=["expense", "operational", "recurring"],
    )

    salaries = FixedLine(
        values={2024: 400, 2025: 420, 2026: 441},
        label="Salaries & Wages",
        tags=["expense", "operational", "recurring"],
    )

    marketing = FixedLine(
        values={2024: 150, 2025: 165, 2026: 182},
        label="Marketing",
        tags=["expense", "operational", "recurring"],
    )

    # Non-operating expenses
    interest_expense = FixedLine(
        values={2024: 50, 2025: 45, 2026: 40},
        label="Interest Expense",
        tags=["expense", "non-operational", "recurring"],
    )

    restructuring_costs = FixedLine(
        values={2024: 100, 2025: 0, 2026: 0},
        label="Restructuring Costs",
        tags=["expense", "non-operational", "non-recurring"],
    )

    # Calculated totals using tags
    total_income = FormulaLine(
        formula=lambda a, li, t: li.tags["income"][t], label="Total Income"
    )

    total_expenses = FormulaLine(
        formula=lambda a, li, t: li.tags["expense"][t], label="Total Expenses"
    )

    # Operating profit (operational items only)
    operating_profit = FormulaLine(
        formula=lambda a, li, t: (
            li.product_revenue[t]
            + li.service_revenue[t]
            - li.cost_of_goods_sold[t]
            - li.salaries[t]
            - li.marketing[t]
        ),
        label="Operating Profit",
    )

    # Net income
    net_income = FormulaLine(
        formula=lambda a, li, t: li.total_income[t] - li.total_expenses[t],
        label="Net Income",
    )

    # Recurring income (excludes one-time items)
    recurring_income = FormulaLine(
        formula=lambda a, li, t: (
            li.product_revenue[t]
            + li.service_revenue[t]
            + li.interest_income[t]
            - li.cost_of_goods_sold[t]
            - li.salaries[t]
            - li.marketing[t]
            - li.interest_expense[t]
        ),
        label="Recurring Net Income",
        tags=["calculated", "recurring"],
    )


def main():
    """Demonstrate the tags feature."""
    # Create model
    model = FinancialStatementWithTags(periods=[2024, 2025, 2026])

    print("=" * 80)
    print("PyProforma v2 - Tags Feature Demo")
    print("=" * 80)
    print()

    # Show how to access tags through LineItemResult
    print("Line Item Tags:")
    print("-" * 80)
    revenue = model["product_revenue"]
    print(f"Product Revenue tags: {revenue.tags}")

    expenses = model["cost_of_goods_sold"]
    print(f"COGS tags: {expenses.tags}")
    print()

    # Show tag-based summations
    print("Tag-Based Summations (2024):")
    print("-" * 80)
    print(
        f"Total income (all 'income' tagged items):     ${model.li.tags['income'][2024]:>10,.0f}"
    )
    print(
        f"Total expenses (all 'expense' tagged items):  ${model.li.tags['expense'][2024]:>10,.0f}"
    )
    print(
        f"Operational items sum:                        ${model.li.tags['operational'][2024]:>10,.0f}"
    )
    print(
        f"Non-operational items sum:                    ${model.li.tags['non-operational'][2024]:>10,.0f}"
    )
    print(
        f"Recurring items sum:                          ${model.li.tags['recurring'][2024]:>10,.0f}"
    )
    print(
        f"Non-recurring items sum:                      ${model.li.tags['non-recurring'][2024]:>10,.0f}"
    )
    print()

    # Show income statement for each year
    for year in model.periods:
        print(f"\nIncome Statement - {year}:")
        print("-" * 80)
        print(f"Product Revenue          ${model.li.product_revenue[year]:>12,.0f}")
        print(f"Service Revenue          ${model.li.service_revenue[year]:>12,.0f}")
        print(f"Asset Sale Gain          ${model.li.asset_sale_gain[year]:>12,.0f}")
        print(f"Interest Income          ${model.li.interest_income[year]:>12,.0f}")
        print(f"                         {'-' * 14}")
        print(f"Total Income             ${model.li.total_income[year]:>12,.0f}")
        print()
        print(f"Cost of Goods Sold       ${model.li.cost_of_goods_sold[year]:>12,.0f}")
        print(f"Salaries & Wages         ${model.li.salaries[year]:>12,.0f}")
        print(f"Marketing                ${model.li.marketing[year]:>12,.0f}")
        print(f"Interest Expense         ${model.li.interest_expense[year]:>12,.0f}")
        print(f"Restructuring Costs      ${model.li.restructuring_costs[year]:>12,.0f}")
        print(f"                         {'-' * 14}")
        print(f"Total Expenses           ${model.li.total_expenses[year]:>12,.0f}")
        print()
        print(f"                         {'=' * 14}")
        print(f"Net Income               ${model.li.net_income[year]:>12,.0f}")
        print(f"                         {'=' * 14}")
        print()
        print(f"Recurring Net Income     ${model.li.recurring_income[year]:>12,.0f}")

    print()
    print("=" * 80)
    print("Key Features Demonstrated:")
    print("-" * 80)
    print("1. Line items can have multiple tags for flexible categorization")
    print("2. Tags are accessible via LineItemResult.tags property")
    print("3. Use li.tags['tag_name'][period] to sum all items with that tag")
    print("4. Tags can be used in formulas for dynamic calculations")
    print("5. Tags enable multi-dimensional analysis (operational, recurring, etc.)")
    print("=" * 80)


if __name__ == "__main__":
    main()
