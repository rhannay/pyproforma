"""
Tests for DebtLine generator in v2 API.
"""

import pytest

from pyproforma.v2 import Assumption, DebtLine, FixedLine, FormulaLine, ProformaModel


class TestDebtLineBasic:
    """Test basic DebtLine functionality."""

    def test_debt_line_simple_model(self):
        """Test DebtLine in a simple model with single debt issue."""

        class SimpleDebtModel(ProformaModel):
            # Assumptions
            interest_rate = Assumption(value=0.05, label="Interest Rate")
            term = Assumption(value=10, label="Debt Term")

            # Par amounts for debt issues
            par_amounts = FixedLine(
                values={2024: 1000000, 2025: 0, 2026: 0}, label="Par Amounts"
            )

            # Debt generator
            debt = DebtLine(
                par_amount_name="par_amounts",
                interest_rate_name="interest_rate",
                term_name="term",
                label="Long-term Debt",
            )

        # Create model
        model = SimpleDebtModel(periods=[2024, 2025, 2026])

        # Verify generated fields exist and have correct values
        # In 2024, we issue $1M debt at 5% for 10 years
        assert model.li.debt_proceeds[2024] == 1000000

        # First payment includes both principal and interest
        principal_2024 = model.li.debt_principal[2024]
        interest_2024 = model.li.debt_interest[2024]

        # For a 10-year 5% loan of $1M, annual payment should be:
        # payment = 1000000 * 0.05 / (1 - 1.05^-10) ≈ $129,504.56
        expected_payment = 1000000 * 0.05 / (1 - (1.05) ** -10)
        assert abs((principal_2024 + interest_2024) - expected_payment) < 1

        # Interest in year 1 should be 5% of $1M = $50,000
        assert abs(interest_2024 - 50000) < 1

        # Outstanding debt at end of 2024 should be close to
        # $1M minus first principal payment
        debt_outstanding_2024 = model.li.debt_debt_outstanding[2024]
        expected_outstanding = 1000000 - principal_2024
        assert abs(debt_outstanding_2024 - expected_outstanding) < 1

    def test_debt_line_multiple_issues(self):
        """Test DebtLine with multiple debt issues in different years."""

        class MultiDebtModel(ProformaModel):
            interest_rate = Assumption(value=0.05)
            term = Assumption(value=5)

            par_amounts = FixedLine(values={2024: 100000, 2025: 0, 2026: 50000})

            debt = DebtLine(
                par_amount_name="par_amounts",
                interest_rate_name="interest_rate",
                term_name="term",
            )

        model = MultiDebtModel(periods=[2024, 2025, 2026])

        # 2024: Issue $100k
        assert model.li.debt_proceeds[2024] == 100000
        assert model.li.debt_interest[2024] > 0

        # 2025: No new issue, but still paying on 2024 debt
        assert model.li.debt_proceeds[2025] == 0
        assert model.li.debt_principal[2025] > 0
        assert model.li.debt_interest[2025] > 0

        # 2026: Issue $50k, plus payments on both 2024 and 2026 debt
        assert model.li.debt_proceeds[2026] == 50000

        # Outstanding should include remaining balance of both issues
        outstanding_2026 = model.li.debt_debt_outstanding[2026]
        assert outstanding_2026 > 0

    def test_debt_line_zero_interest(self):
        """Test DebtLine with zero interest rate."""

        class ZeroInterestModel(ProformaModel):
            interest_rate = Assumption(value=0.0)
            term = Assumption(value=4)

            par_amounts = FixedLine(values={2024: 1000, 2025: 0, 2026: 0, 2027: 0})

            debt = DebtLine(
                par_amount_name="par_amounts",
                interest_rate_name="interest_rate",
                term_name="term",
            )

        model = ZeroInterestModel(periods=[2024, 2025, 2026, 2027])

        # With 0% interest and 4-year term, should pay $250 per year
        assert abs(model.li.debt_principal[2024] - 250) < 0.01
        assert model.li.debt_interest[2024] == 0

        assert abs(model.li.debt_principal[2025] - 250) < 0.01
        assert model.li.debt_interest[2025] == 0

    def test_debt_line_in_formula(self):
        """Test using generated debt fields in other formulas."""

        class DebtFormulaModel(ProformaModel):
            interest_rate = Assumption(value=0.05)
            term = Assumption(value=10)

            par_amounts = FixedLine(values={2024: 100000, 2025: 0})

            debt = DebtLine(
                par_amount_name="par_amounts",
                interest_rate_name="interest_rate",
                term_name="term",
            )

            # Use debt fields in a formula
            total_debt_service = FormulaLine(
                formula=lambda a, li, t: li.debt_principal[t] + li.debt_interest[t],
                label="Total Debt Service",
            )

        model = DebtFormulaModel(periods=[2024, 2025])

        # Total debt service should equal sum of principal + interest
        expected_2024 = model.li.debt_principal[2024] + model.li.debt_interest[2024]
        assert abs(model.li.total_debt_service[2024] - expected_2024) < 0.01

        expected_2025 = model.li.debt_principal[2025] + model.li.debt_interest[2025]
        assert abs(model.li.total_debt_service[2025] - expected_2025) < 0.01


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
