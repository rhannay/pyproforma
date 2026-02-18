"""
Example usage of debt line items in PyProforma v2.

This example demonstrates how to use DebtPrincipalLine and DebtInterestLine
to model bond debt service with multiple issuances and level annual payments.
"""

from pyproforma.v2 import FixedLine, FormulaLine, ProformaModel, create_debt_lines


class DebtServiceModel(ProformaModel):
    """
    A financial model with bond debt service.

    This model demonstrates:
    - Multiple bond issuances across different years
    - Automatic calculation of principal and interest using level debt service
    - Tracking total debt service and outstanding balances
    - Using tags to aggregate debt-related items
    """

    # Define bond issuances
    bond_proceeds = FixedLine(
        values={year: 0 for year in range(2024, 2039)},  # Initialize all to 0
        label="Bond Proceeds",
        tags=["financing"],
    )
    # Override specific years with issuances
    bond_proceeds.values[2024] = 1_000_000  # $1M bond issued in 2024
    bond_proceeds.values[2026] = 500_000  # $500K bond issued in 2026
    bond_proceeds.values[2028] = 750_000  # $750K bond issued in 2028

    # Create debt line items using the factory function
    # This ensures principal and interest share the same debt schedules
    principal_payment, interest_expense = create_debt_lines(
        par_amounts_line_item="bond_proceeds",
        interest_rate=0.05,  # 5% annual interest rate
        term=10,  # 10-year amortization
        principal_label="Principal Payment",
        interest_label="Interest Expense",
        tags=["debt_service"],
    )

    # Calculate total debt service
    total_debt_service = FormulaLine(
        formula=lambda a, li, t: li.principal_payment[t] + li.interest_expense[t],
        label="Total Debt Service",
    )

    # Alternative: use tags to sum debt service
    total_debt_service_via_tags = FormulaLine(
        formula=lambda a, li, t: li.tag["debt_service"][t],
        label="Total Debt Service (via tags)",
    )

    # Calculate cumulative principal paid
    cumulative_principal_paid = FormulaLine(
        formula=lambda a, li, t: li.principal_payment[t]
        + (li.cumulative_principal_paid[t - 1] if t > 2024 else 0),
        label="Cumulative Principal Paid",
    )

    # Calculate debt service coverage ratio (example)
    revenue = FixedLine(
        values={year: 500_000 * (1.05 ** (year - 2024)) for year in range(2024, 2039)},
        label="Revenue",
    )

    operating_expenses = FormulaLine(
        formula=lambda a, li, t: li.revenue[t] * 0.6,
        label="Operating Expenses",
    )

    operating_income = FormulaLine(
        formula=lambda a, li, t: li.revenue[t] - li.operating_expenses[t],
        label="Operating Income",
    )

    debt_service_coverage_ratio = FormulaLine(
        formula=lambda a, li, t: (
            li.operating_income[t] / li.total_debt_service[t]
            if li.total_debt_service[t] > 0
            else 0
        ),
        label="Debt Service Coverage Ratio",
    )


def format_currency(value):
    """Format a value as currency."""
    return f"${value:,.0f}"


def format_ratio(value):
    """Format a value as a ratio."""
    return f"{value:.2f}x"


# Example usage
if __name__ == "__main__":
    # Create model for 15 years (2024-2038)
    # This covers the full amortization of all three bonds:
    # - 2024 bond: 2024-2033
    # - 2026 bond: 2026-2035
    # - 2028 bond: 2028-2037
    periods = list(range(2024, 2039))
    model = DebtServiceModel(periods=periods)

    print("=" * 80)
    print("BOND DEBT SERVICE MODEL")
    print("=" * 80)
    print()

    # Show bond issuances
    print("Bond Issuances:")
    print(f"  2024: {format_currency(model.li.bond_proceeds[2024])}")
    print(f"  2026: {format_currency(model.li.bond_proceeds[2026])}")
    print(f"  2028: {format_currency(model.li.bond_proceeds[2028])}")
    print()

    # Show debt service for selected years
    print("Debt Service Schedule (Selected Years):")
    print("-" * 80)
    print(f"{'Year':<8} {'Principal':<15} {'Interest':<15} {'Total DS':<15} {'DSCR':<10}")
    print("-" * 80)

    selected_years = [2024, 2026, 2028, 2030, 2032, 2034, 2036, 2038]
    for year in selected_years:
        principal = model.li.principal_payment[year]
        interest = model.li.interest_expense[year]
        total_ds = model.li.total_debt_service[year]
        dscr = model.li.debt_service_coverage_ratio[year]

        print(
            f"{year:<8} {format_currency(principal):<15} {format_currency(interest):<15} "
            f"{format_currency(total_ds):<15} {format_ratio(dscr):<10}"
        )
    print()

    # Show how debt service changes over time
    print("Key Observations:")
    print()

    print("1. Level Debt Service:")
    # For the 2024 bond, debt service should be constant
    ds_2024_bond_year1 = model.li.total_debt_service[2024]
    ds_2024_bond_year5 = model.li.total_debt_service[2028]
    print(f"   2024 bond debt service (year 1): {format_currency(ds_2024_bond_year1)}")
    print(
        f"   2024 bond debt service (year 5): {format_currency(model.li.principal_payment[2028] + (model.li.interest_expense[2028] - model.li.interest_expense[2026] - model.li.interest_expense[2028] + model.li.interest_expense[2024]))}"
    )
    print("   (Note: Each individual bond has level debt service)")
    print()

    print("2. Interest Declining Over Time:")
    print(f"   2024 Interest: {format_currency(model.li.interest_expense[2024])}")
    print(f"   2026 Interest: {format_currency(model.li.interest_expense[2026])}")
    print(f"   2028 Interest: {format_currency(model.li.interest_expense[2028])}")
    print(f"   2030 Interest: {format_currency(model.li.interest_expense[2030])}")
    print("   (Interest declines as principal is paid down)")
    print()

    print("3. Principal Increasing Over Time:")
    print(
        f"   2024 Principal: {format_currency(model.li.principal_payment[2024])}"
    )
    print(
        f"   2026 Principal: {format_currency(model.li.principal_payment[2026])}"
    )
    print(
        f"   2028 Principal: {format_currency(model.li.principal_payment[2028])}"
    )
    print(
        f"   2030 Principal: {format_currency(model.li.principal_payment[2030])}"
    )
    print("   (Note: 2026 and 2028 are higher due to multiple overlapping bonds)")
    print()

    print("4. Overlapping Bond Issues:")
    peak_year = 2028
    print(f"   In {peak_year}, all three bonds are active:")
    print(f"     - 2024 bond: year {peak_year - 2024 + 1} of 10")
    print(f"     - 2026 bond: year {peak_year - 2026 + 1} of 10")
    print(f"     - 2028 bond: year {peak_year - 2028 + 1} of 10")
    print(
        f"   Total debt service: {format_currency(model.li.total_debt_service[peak_year])}"
    )
    print()

    print("5. Final Bond Payment:")
    # Find last year with debt service
    last_year_with_debt = 2037  # 2028 + 10 - 1
    print(f"   Last payment in {last_year_with_debt}:")
    print(
        f"     Principal: {format_currency(model.li.principal_payment[last_year_with_debt])}"
    )
    print(
        f"     Interest:  {format_currency(model.li.interest_expense[last_year_with_debt])}"
    )
    print(f"   No debt service in 2038: {format_currency(model.li.total_debt_service[2038])}")
    print()

    # Verify debt service via tags matches direct calculation
    print("6. Tag-based Aggregation:")
    tag_total = model.li.total_debt_service_via_tags[2028]
    direct_total = model.li.total_debt_service[2028]
    print(f"   Total DS (direct):    {format_currency(direct_total)}")
    print(f"   Total DS (via tags):  {format_currency(tag_total)}")
    print(f"   Match: {abs(tag_total - direct_total) < 0.01}")
    print()

    print("=" * 80)
    print("Example complete!")
    print("=" * 80)
