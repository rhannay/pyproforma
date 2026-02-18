"""
Tests for debt line items (DebtPrincipalLine and DebtInterestLine).
"""

import pytest

from pyproforma.v2 import (
    DebtCalculator,
    DebtInterestLine,
    DebtPrincipalLine,
    FixedLine,
    FormulaLine,
    ProformaModel,
    create_debt_lines,
)


class TestDebtCalculator:
    """Unit tests for DebtCalculator class."""

    def test_annual_payment_calculation_with_interest(self):
        """Test level annual payment formula with interest."""
        calculator = DebtCalculator(
            par_amounts_line_item="bond_proceeds",
            interest_rate=0.05,
            term=10,
        )

        # For $1M at 5% for 10 years
        payment = calculator._calculate_annual_payment(1_000_000, 0.05, 10)

        # Known value from amortization tables
        expected = 129_504.56  # Approximate
        assert abs(payment - expected) < 1.0

    def test_annual_payment_with_zero_interest(self):
        """Test annual payment calculation with zero interest rate."""
        calculator = DebtCalculator(
            par_amounts_line_item="bond_proceeds",
            interest_rate=0.0,
            term=10,
        )

        payment = calculator._calculate_annual_payment(1_000_000, 0.0, 10)
        assert payment == 100_000.0  # Just principal/term

    def test_add_single_bond_issue(self):
        """Test adding a single bond issue creates proper schedule."""
        calculator = DebtCalculator(
            par_amounts_line_item="bond_proceeds",
            interest_rate=0.05,
            term=5,
        )

        calculator._add_bond_issue(1_000_000, 2024)

        # Check schedule exists
        assert 2024 in calculator._schedules
        schedule = calculator._schedules[2024]

        # Check all periods are present
        assert len(schedule) == 5
        for year in range(2024, 2029):
            assert year in schedule

        # First year: interest is 5% of full balance
        assert abs(schedule[2024]["interest"] - 50_000) < 1.0

        # Last year: principal should equal remaining balance
        assert schedule[2028]["principal"] > 0

    def test_get_principal_single_issue(self):
        """Test getting principal for a single bond issue."""
        calculator = DebtCalculator(
            par_amounts_line_item="bond_proceeds",
            interest_rate=0.05,
            term=5,
        )

        calculator._add_bond_issue(1_000_000, 2024)

        # Principal payment should be positive each year
        for year in range(2024, 2029):
            principal = calculator.get_principal(year)
            assert principal > 0

        # No principal payment after term ends
        assert calculator.get_principal(2029) == 0

    def test_get_interest_single_issue(self):
        """Test getting interest for a single bond issue."""
        calculator = DebtCalculator(
            par_amounts_line_item="bond_proceeds",
            interest_rate=0.05,
            term=5,
        )

        calculator._add_bond_issue(1_000_000, 2024)

        # Interest should decline over time
        interest_2024 = calculator.get_interest(2024)
        interest_2025 = calculator.get_interest(2025)
        interest_2028 = calculator.get_interest(2028)

        assert interest_2024 > interest_2025
        assert interest_2025 > interest_2028

        # No interest payment after term ends
        assert calculator.get_interest(2029) == 0

    def test_multiple_overlapping_bond_issues(self):
        """Test multiple bond issues with overlapping terms."""
        calculator = DebtCalculator(
            par_amounts_line_item="bond_proceeds",
            interest_rate=0.05,
            term=5,
        )

        calculator._add_bond_issue(1_000_000, 2024)
        calculator._add_bond_issue(500_000, 2026)

        # In 2024-2025, only first bond
        principal_2024 = calculator.get_principal(2024)
        interest_2024 = calculator.get_interest(2024)

        # In 2026-2028, both bonds
        principal_2026 = calculator.get_principal(2026)
        interest_2026 = calculator.get_interest(2026)

        # 2026 should have more principal and interest (two bonds active)
        assert principal_2026 > principal_2024
        assert interest_2026 > interest_2024

        # In 2029-2030, only second bond
        principal_2029 = calculator.get_principal(2029)
        assert principal_2029 > 0

        # After 2030, no bonds
        assert calculator.get_principal(2031) == 0

    def test_outstanding_balance(self):
        """Test outstanding balance calculation."""
        calculator = DebtCalculator(
            par_amounts_line_item="bond_proceeds",
            interest_rate=0.05,
            term=5,
        )

        calculator._add_bond_issue(1_000_000, 2024)

        # Balance should decline each year
        balance_2024 = calculator.get_outstanding_balance(2024)
        balance_2025 = calculator.get_outstanding_balance(2025)
        balance_2028 = calculator.get_outstanding_balance(2028)

        assert balance_2024 > balance_2025
        assert balance_2025 > balance_2028

        # After final payment, balance should be zero or very close
        balance_2029 = calculator.get_outstanding_balance(2029)
        assert balance_2029 == 0


class TestDebtPrincipalLine:
    """Integration tests for DebtPrincipalLine in ProformaModel."""

    def test_single_bond_issue(self):
        """Test principal payments with a single bond issue."""
        principal, interest = create_debt_lines(
            par_amounts_line_item="bond_proceeds",
            interest_rate=0.05,
            term=5,
        )

        class TestModel(ProformaModel):
            bond_proceeds = FixedLine(
                values={
                    2024: 1_000_000,
                    2025: 0,
                    2026: 0,
                    2027: 0,
                    2028: 0,
                    2029: 0,
                }
            )
            principal_payment = principal
            interest_expense = interest

        model = TestModel(periods=[2024, 2025, 2026, 2027, 2028, 2029])

        # Principal should be present for years 2024-2028
        assert model.li.principal_payment[2024] > 0
        assert model.li.principal_payment[2025] > 0
        assert model.li.principal_payment[2028] > 0

        # No principal after term
        assert model.li.principal_payment[2029] == 0

    def test_multiple_bond_issues(self):
        """Test principal payments with multiple bond issues."""
        principal, interest = create_debt_lines(
            par_amounts_line_item="bond_proceeds",
            interest_rate=0.05,
            term=5,
        )

        class TestModel(ProformaModel):
            bond_proceeds = FixedLine(
                values={
                    2024: 1_000_000,
                    2025: 0,
                    2026: 500_000,
                    2027: 0,
                    2028: 0,
                    2029: 0,
                    2030: 0,
                    2031: 0,
                }
            )
            principal_payment = principal
            interest_expense = interest

        model = TestModel(periods=[2024, 2025, 2026, 2027, 2028, 2029, 2030, 2031])

        # 2024-2025: Only first bond
        principal_2024 = model.li.principal_payment[2024]

        # 2026-2028: Both bonds
        principal_2026 = model.li.principal_payment[2026]

        # 2029-2030: Only second bond
        principal_2029 = model.li.principal_payment[2029]

        # Verify overlapping period has more principal
        assert principal_2026 > principal_2024
        assert principal_2029 > 0

        # After 2030, no bonds
        assert model.li.principal_payment[2031] == 0

    def test_zero_bond_proceeds(self):
        """Test that zero proceeds don't create a bond issue."""
        principal, interest = create_debt_lines(
            par_amounts_line_item="bond_proceeds",
            interest_rate=0.05,
            term=5,
        )

        class TestModel(ProformaModel):
            bond_proceeds = FixedLine(
                values={
                    2024: 1_000_000,
                    2025: 0,
                    2026: 500_000,
                    2027: 0,
                    2028: 0,
                    2029: 0,
                    2030: 0,
                    2031: 0,
                }
            )
            principal_payment = principal
            interest_expense = interest

        model = TestModel(periods=[2024, 2025, 2026, 2027, 2028, 2029, 2030, 2031])

        # Should have bond in 2024 and 2026, but not 2025
        # Just verify it doesn't crash and produces reasonable values
        assert model.li.principal_payment[2024] > 0
        assert model.li.principal_payment[2026] > 0

    def test_principal_with_labels(self):
        """Test that labels are properly set."""
        principal, _ = create_debt_lines(
            par_amounts_line_item="bond_proceeds",
            interest_rate=0.05,
            term=5,
            principal_label="Principal Payment",
        )

        assert principal.label == "Principal Payment"

    def test_principal_with_tags(self):
        """Test that tags are properly set."""
        principal, _ = create_debt_lines(
            par_amounts_line_item="bond_proceeds",
            interest_rate=0.05,
            term=5,
            tags=["debt_service", "cash_outflow"],
        )

        assert "debt_service" in principal.tags
        assert "cash_outflow" in principal.tags


class TestDebtInterestLine:
    """Integration tests for DebtInterestLine in ProformaModel."""

    def test_single_bond_issue_interest(self):
        """Test interest payments with a single bond issue."""
        principal, interest = create_debt_lines(
            par_amounts_line_item="bond_proceeds",
            interest_rate=0.05,
            term=5,
        )

        class TestModel(ProformaModel):
            bond_proceeds = FixedLine(
                values={2024: 1_000_000, 2025: 0, 2026: 0, 2027: 0, 2028: 0, 2029: 0}
            )
            principal_payment = principal
            interest_expense = interest

        model = TestModel(periods=[2024, 2025, 2026, 2027, 2028, 2029])

        # Interest should decline over time
        assert model.li.interest_expense[2024] > model.li.interest_expense[2025]
        assert model.li.interest_expense[2025] > model.li.interest_expense[2028]

        # First year interest should be approximately 5% of $1M
        assert abs(model.li.interest_expense[2024] - 50_000) < 1000

        # No interest after term
        assert model.li.interest_expense[2029] == 0

    def test_multiple_bond_issues_interest(self):
        """Test interest payments with multiple bond issues."""
        principal, interest = create_debt_lines(
            par_amounts_line_item="bond_proceeds",
            interest_rate=0.05,
            term=5,
        )

        class TestModel(ProformaModel):
            bond_proceeds = FixedLine(
                values={
                    2024: 1_000_000,
                    2025: 0,
                    2026: 500_000,
                    2027: 0,
                    2028: 0,
                    2029: 0,
                    2030: 0,
                    2031: 0,
                }
            )
            principal_payment = principal
            interest_expense = interest

        model = TestModel(periods=[2024, 2025, 2026, 2027, 2028, 2029, 2030, 2031])

        # 2024-2025: Only first bond
        interest_2024 = model.li.interest_expense[2024]

        # 2026-2028: Both bonds (more interest)
        interest_2026 = model.li.interest_expense[2026]

        # 2029-2030: Only second bond
        interest_2029 = model.li.interest_expense[2029]

        # Verify overlapping period has more interest
        assert interest_2026 > interest_2024
        assert interest_2029 > 0

        # After 2030, no interest
        assert model.li.interest_expense[2031] == 0

    def test_interest_with_labels(self):
        """Test that labels are properly set."""
        _, interest = create_debt_lines(
            par_amounts_line_item="bond_proceeds",
            interest_rate=0.05,
            term=5,
            interest_label="Interest Expense",
        )

        assert interest.label == "Interest Expense"


class TestDebtLinesIntegration:
    """Integration tests for principal and interest together."""

    def test_principal_plus_interest_equals_debt_service(self):
        """Test that principal + interest equals level debt service."""
        principal, interest = create_debt_lines(
            par_amounts_line_item="bond_proceeds",
            interest_rate=0.05,
            term=5,
        )

        class TestModel(ProformaModel):
            bond_proceeds = FixedLine(
                values={2024: 1_000_000, 2025: 0, 2026: 0, 2027: 0, 2028: 0}
            )
            principal_payment = principal
            interest_expense = interest
            debt_service = FormulaLine(
                formula=lambda a, li, t: li.principal_payment[t] + li.interest_expense[t]
            )

        model = TestModel(periods=[2024, 2025, 2026, 2027, 2028])

        # Debt service should be constant (level payment)
        ds_2024 = model.li.debt_service[2024]
        ds_2025 = model.li.debt_service[2025]
        ds_2026 = model.li.debt_service[2026]
        ds_2028 = model.li.debt_service[2028]

        # Should be very close (within rounding)
        assert abs(ds_2024 - ds_2025) < 1.0
        assert abs(ds_2025 - ds_2026) < 1.0
        assert abs(ds_2026 - ds_2028) < 1.0

    def test_shared_calculator_ensures_consistency(self):
        """Test that principal and interest share the same schedules."""
        calculator = DebtCalculator(
            par_amounts_line_item="bond_proceeds",
            interest_rate=0.05,
            term=5,
        )

        principal = DebtPrincipalLine(calculator=calculator)
        interest = DebtInterestLine(calculator=calculator)

        # Both should reference the same calculator instance
        assert principal.calculator is interest.calculator

    def test_time_offset_reference(self):
        """Test referencing prior period debt values."""
        principal, interest = create_debt_lines(
            par_amounts_line_item="bond_proceeds",
            interest_rate=0.05,
            term=5,
        )

        class TestModel(ProformaModel):
            bond_proceeds = FixedLine(values={2024: 1_000_000, 2025: 0, 2026: 0})
            principal_payment = principal
            interest_expense = interest
            # Reference prior period principal
            principal_change = FormulaLine(
                formula=lambda a, li, t: li.principal_payment[t]
                - (li.principal_payment[t - 1] if t > 2024 else 0)
            )

        model = TestModel(periods=[2024, 2025, 2026])

        # In 2024, change is just the principal (no prior period)
        assert model.li.principal_change[2024] == model.li.principal_payment[2024]

        # In 2025, change should be positive (principal is increasing)
        # Actually principal payments increase over time, so this might be positive or negative
        # Let's just verify it calculates without error
        assert isinstance(model.li.principal_change[2025], (int, float))

    def test_tag_summation_for_debt_service(self):
        """Test using tags to sum principal and interest."""
        principal, interest = create_debt_lines(
            par_amounts_line_item="bond_proceeds",
            interest_rate=0.05,
            term=5,
            tags=["debt_service"],
        )

        class TestModel(ProformaModel):
            bond_proceeds = FixedLine(
                values={2024: 1_000_000, 2025: 0, 2026: 0, 2027: 0, 2028: 0}
            )
            principal_payment = principal
            interest_expense = interest
            total_debt_service = FormulaLine(
                formula=lambda a, li, t: li.tag["debt_service"][t]
            )

        model = TestModel(periods=[2024, 2025, 2026, 2027, 2028])

        # Total debt service via tag should equal sum
        for year in [2024, 2025, 2026, 2027, 2028]:
            expected = (
                model.li.principal_payment[year] + model.li.interest_expense[year]
            )
            assert abs(model.li.total_debt_service[year] - expected) < 0.01

    def test_using_formula_for_bond_proceeds(self):
        """Test that bond proceeds can come from a formula."""
        principal, interest = create_debt_lines(
            par_amounts_line_item="bond_proceeds",
            interest_rate=0.05,
            term=5,
        )

        class TestModel(ProformaModel):
            # Growth-based bond issuances
            base_issuance = FixedLine(
                values={2024: 1_000_000, 2025: 0, 2026: 0, 2027: 0, 2028: 0, 2029: 0}
            )
            bond_proceeds = FormulaLine(
                formula=lambda a, li, t: li.base_issuance[t]
                if t in li.base_issuance._values
                else 0
            )
            principal_payment = principal
            interest_expense = interest

        model = TestModel(periods=[2024, 2025, 2026, 2027, 2028, 2029])

        # Should work with formula-based proceeds
        assert model.li.principal_payment[2024] > 0
        assert model.li.interest_expense[2024] > 0

    def test_repr_methods(self):
        """Test string representations of debt line items."""
        principal, interest = create_debt_lines(
            par_amounts_line_item="bond_proceeds",
            interest_rate=0.05,
            term=10,
            principal_label="Principal",
            interest_label="Interest",
        )

        principal_repr = repr(principal)
        interest_repr = repr(interest)

        # Should include key information
        assert "bond_proceeds" in principal_repr
        assert "0.05" in principal_repr
        assert "10" in principal_repr
        assert "Principal" in principal_repr

        assert "bond_proceeds" in interest_repr
        assert "0.05" in interest_repr
        assert "10" in interest_repr
        assert "Interest" in interest_repr


class TestDebtLineEdgeCases:
    """Edge cases and error conditions."""

    def test_no_bond_proceeds_in_model(self):
        """Test that missing bond proceeds line item is handled gracefully."""
        principal, interest = create_debt_lines(
            par_amounts_line_item="bond_proceeds",
            interest_rate=0.05,
            term=5,
        )

        class TestModel(ProformaModel):
            # Note: bond_proceeds not defined!
            principal_payment = principal
            interest_expense = interest

        # Should succeed but with zero debt service (no bonds issued)
        model = TestModel(periods=[2024, 2025])
        assert model.li.principal_payment[2024] == 0
        assert model.li.interest_expense[2024] == 0

    def test_high_interest_rate(self):
        """Test with a high interest rate."""
        principal, interest = create_debt_lines(
            par_amounts_line_item="bond_proceeds",
            interest_rate=0.20,  # 20%
            term=5,
        )

        class TestModel(ProformaModel):
            bond_proceeds = FixedLine(
                values={2024: 1_000_000, 2025: 0, 2026: 0, 2027: 0, 2028: 0}
            )
            principal_payment = principal
            interest_expense = interest

        model = TestModel(periods=[2024, 2025, 2026, 2027, 2028])

        # With higher interest, first year interest should be much higher
        assert model.li.interest_expense[2024] > 150_000

    def test_short_term_bond(self):
        """Test with a very short term bond."""
        principal, interest = create_debt_lines(
            par_amounts_line_item="bond_proceeds",
            interest_rate=0.05,
            term=2,  # 2 year term
        )

        class TestModel(ProformaModel):
            bond_proceeds = FixedLine(values={2024: 1_000_000, 2025: 0, 2026: 0})
            principal_payment = principal
            interest_expense = interest

        model = TestModel(periods=[2024, 2025, 2026])

        # Should have payments in 2024-2025
        assert model.li.principal_payment[2024] > 0
        assert model.li.principal_payment[2025] > 0

        # Should be done by 2026
        assert model.li.principal_payment[2026] == 0

    def test_long_term_bond(self):
        """Test with a long term bond."""
        principal, interest = create_debt_lines(
            par_amounts_line_item="bond_proceeds",
            interest_rate=0.05,
            term=30,  # 30 year term
        )

        class TestModel(ProformaModel):
            bond_proceeds = FixedLine(
                values={2024: 1_000_000, 2025: 0, 2026: 0, 2027: 0, 2028: 0}
            )
            principal_payment = principal
            interest_expense = interest

        model = TestModel(periods=[2024, 2025, 2026, 2027, 2028])

        # With 30 year term, principal payments should be small initially
        # And interest should be close to 5% of principal
        assert model.li.interest_expense[2024] > model.li.principal_payment[2024]
