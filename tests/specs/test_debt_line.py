"""Tests for debt line items (DebtPrincipalLine and DebtInterestLine)."""

import pytest

from pyproforma import (
    DebtCalculator,
    DebtInterestLine,
    DebtPrincipalLine,
    FixedLine,
    FormulaLine,
    InputLine,
    ProformaModel,
    ScalarInputLine,
    ScalarLine,
    create_debt_lines,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_model(par_values, rate=0.05, term=5, extra_periods=None):
    """Build a minimal model with bond_rate, bond_term, bond_proceeds, and debt lines."""
    periods = sorted(par_values.keys())
    if extra_periods:
        periods = sorted(set(periods) | set(extra_periods))

    principal, interest = create_debt_lines(
        par_amounts="bond_proceeds",
        interest_rate="bond_rate",
        term="bond_term",
    )

    model_ns = {
        "bond_rate": ScalarLine(value=rate),
        "bond_term": ScalarLine(value=term),
        "bond_proceeds": FixedLine(values=par_values),
        "principal_payment": principal,
        "interest_expense": interest,
    }

    Model = type("Model", (ProformaModel,), model_ns)
    return Model(periods=periods)


# ---------------------------------------------------------------------------
# DebtCalculator unit tests
# ---------------------------------------------------------------------------


class TestDebtCalculator:

    def test_annual_payment_calculation_with_interest(self):
        calc = DebtCalculator(par_amounts="p", interest_rate="r", term="t")
        payment = calc._calculate_annual_payment(1_000_000, 0.05, 10)
        assert abs(payment - 129_504.56) < 1.0

    def test_annual_payment_with_zero_interest(self):
        calc = DebtCalculator(par_amounts="p", interest_rate="r", term="t")
        payment = calc._calculate_annual_payment(1_000_000, 0.0, 10)
        assert payment == 100_000.0

    def test_add_single_bond_issue(self):
        calc = DebtCalculator(par_amounts="p", interest_rate="r", term="t")
        calc._add_bond_issue(1_000_000, 2024, rate=0.05, term=5)

        assert 2024 in calc._schedules
        assert len(calc._schedules[2024]) == 5
        assert abs(calc._schedules[2024][2024]["interest"] - 50_000) < 1.0

    def test_get_principal_single_issue(self):
        calc = DebtCalculator(par_amounts="p", interest_rate="r", term="t")
        calc._add_bond_issue(1_000_000, 2024, rate=0.05, term=5)

        for year in range(2024, 2029):
            assert calc.get_principal(year) > 0
        assert calc.get_principal(2029) == 0

    def test_get_interest_single_issue(self):
        calc = DebtCalculator(par_amounts="p", interest_rate="r", term="t")
        calc._add_bond_issue(1_000_000, 2024, rate=0.05, term=5)

        assert calc.get_interest(2024) > calc.get_interest(2025)
        assert calc.get_interest(2025) > calc.get_interest(2028)
        assert calc.get_interest(2029) == 0

    def test_multiple_overlapping_bond_issues(self):
        calc = DebtCalculator(par_amounts="p", interest_rate="r", term="t")
        calc._add_bond_issue(1_000_000, 2024, rate=0.05, term=5)
        calc._add_bond_issue(500_000, 2026, rate=0.05, term=5)

        assert calc.get_principal(2026) > calc.get_principal(2024)
        assert calc.get_principal(2029) > 0
        assert calc.get_principal(2031) == 0

    def test_outstanding_balance(self):
        calc = DebtCalculator(par_amounts="p", interest_rate="r", term="t")
        calc._add_bond_issue(1_000_000, 2024, rate=0.05, term=5)

        assert calc.get_outstanding_balance(2024) > calc.get_outstanding_balance(2025)
        assert calc.get_outstanding_balance(2028) == 0


# ---------------------------------------------------------------------------
# create_debt_lines validation
# ---------------------------------------------------------------------------


class TestCreateDebtLinesValidation:

    def test_par_amounts_must_be_string(self):
        with pytest.raises(TypeError, match="'par_amounts' must be a string"):
            create_debt_lines(par_amounts=1_000_000, interest_rate="r", term="t")

    def test_interest_rate_must_be_string(self):
        with pytest.raises(TypeError, match="'interest_rate' must be a string"):
            create_debt_lines(par_amounts="p", interest_rate=0.05, term="t")

    def test_term_must_be_string(self):
        with pytest.raises(TypeError, match="'term' must be a string"):
            create_debt_lines(par_amounts="p", interest_rate="r", term=20)


# ---------------------------------------------------------------------------
# Integration tests
# ---------------------------------------------------------------------------


class TestDebtPrincipalLine:

    def test_single_bond_issue(self):
        model = _make_model({2024: 1_000_000, 2025: 0, 2026: 0, 2027: 0, 2028: 0, 2029: 0})
        assert model.principal_payment[2024] > 0
        assert model.principal_payment[2028] > 0
        assert model.principal_payment[2029] == 0

    def test_multiple_bond_issues(self):
        model = _make_model(
            {2024: 1_000_000, 2025: 0, 2026: 500_000, 2027: 0, 2028: 0, 2029: 0, 2030: 0, 2031: 0}
        )
        assert model.principal_payment[2026] > model.principal_payment[2024]
        assert model.principal_payment[2029] > 0
        assert model.principal_payment[2031] == 0

    def test_labels_and_tags(self):
        principal, _ = create_debt_lines(
            par_amounts="bond_proceeds",
            interest_rate="bond_rate",
            term="bond_term",
            principal_label="Principal Payment",
            tags=["debt_service"],
        )
        assert principal.label == "Principal Payment"
        assert "debt_service" in principal.tags


class TestDebtInterestLine:

    def test_interest_declines_over_time(self):
        model = _make_model({2024: 1_000_000, 2025: 0, 2026: 0, 2027: 0, 2028: 0, 2029: 0})
        assert model.interest_expense[2024] > model.interest_expense[2025]
        assert abs(model.interest_expense[2024] - 50_000) < 1000
        assert model.interest_expense[2029] == 0

    def test_interest_label(self):
        _, interest = create_debt_lines(
            par_amounts="bond_proceeds",
            interest_rate="bond_rate",
            term="bond_term",
            interest_label="Interest Expense",
        )
        assert interest.label == "Interest Expense"


class TestDebtLinesIntegration:

    def test_level_debt_service(self):
        """Principal + interest should be constant (level payment)."""
        principal, interest = create_debt_lines(
            par_amounts="bond_proceeds",
            interest_rate="bond_rate",
            term="bond_term",
        )

        class M(ProformaModel):
            bond_rate = ScalarLine(value=0.05)
            bond_term = ScalarLine(value=5)
            bond_proceeds = FixedLine(values={2024: 1_000_000, 2025: 0, 2026: 0, 2027: 0, 2028: 0})
            principal_payment = principal
            interest_expense = interest
            debt_service = FormulaLine(
                formula=lambda li, t: li.principal_payment[t] + li.interest_expense[t]
            )

        model = M(periods=[2024, 2025, 2026, 2027, 2028])
        ds = [model.debt_service[y] for y in [2024, 2025, 2026, 2027, 2028]]
        for i in range(1, len(ds)):
            assert abs(ds[i] - ds[0]) < 1.0

    def test_shared_calculator(self):
        calculator = DebtCalculator(par_amounts="p", interest_rate="r", term="t")
        principal = DebtPrincipalLine(calculator=calculator)
        interest = DebtInterestLine(calculator=calculator)
        assert principal.calculator is interest.calculator

    def test_tag_summation(self):
        principal, interest = create_debt_lines(
            par_amounts="bond_proceeds",
            interest_rate="bond_rate",
            term="bond_term",
            tags=["debt_service"],
        )

        class M(ProformaModel):
            bond_rate = ScalarLine(value=0.05)
            bond_term = ScalarLine(value=5)
            bond_proceeds = FixedLine(values={2024: 1_000_000, 2025: 0, 2026: 0, 2027: 0, 2028: 0})
            principal_payment = principal
            interest_expense = interest
            total_ds = FormulaLine(formula=lambda li, t: li.tag["debt_service"][t])

        model = M(periods=[2024, 2025, 2026, 2027, 2028])
        for year in [2024, 2025, 2026, 2027, 2028]:
            expected = model.principal_payment[year] + model.interest_expense[year]
            assert abs(model.total_ds[year] - expected) < 0.01

    def test_input_line_rate_scenario_analysis(self):
        """InputLine rate produces different schedules per scenario."""
        principal, interest = create_debt_lines(
            par_amounts="bond_proceeds",
            interest_rate="bond_rate",
            term="bond_term",
        )

        class M(ProformaModel):
            bond_rate = ScalarInputLine(default=0.045)
            bond_term = ScalarLine(value=5)
            bond_proceeds = FixedLine(values={2024: 1_000_000, 2025: 0, 2026: 0, 2027: 0, 2028: 0})
            principal_payment = principal
            interest_expense = interest

        base = M(periods=[2024, 2025, 2026, 2027, 2028])
        high = M(periods=[2024, 2025, 2026, 2027, 2028], bond_rate=0.08)

        assert high.interest_expense[2024] > base.interest_expense[2024]

    def test_repr(self):
        principal, interest = create_debt_lines(
            par_amounts="bond_proceeds",
            interest_rate="bond_rate",
            term="bond_term",
            principal_label="Principal",
            interest_label="Interest",
        )
        assert "bond_proceeds" in repr(principal)
        assert "bond_rate" in repr(principal)
        assert "bond_term" in repr(principal)
        assert "bond_proceeds" in repr(interest)


class TestDebtEdgeCases:

    def test_no_proceeds_returns_zero(self):
        """Missing par_amounts line item is handled gracefully."""
        principal, interest = create_debt_lines(
            par_amounts="bond_proceeds",
            interest_rate="bond_rate",
            term="bond_term",
        )

        class M(ProformaModel):
            bond_rate = ScalarLine(value=0.05)
            bond_term = ScalarLine(value=5)
            # bond_proceeds intentionally omitted
            principal_payment = principal
            interest_expense = interest

        model = M(periods=[2024, 2025])
        assert model.principal_payment[2024] == 0
        assert model.interest_expense[2024] == 0

    def test_high_rate(self):
        model = _make_model({2024: 1_000_000, 2025: 0, 2026: 0, 2027: 0, 2028: 0}, rate=0.20)
        assert model.interest_expense[2024] > 150_000

    def test_short_term(self):
        model = _make_model({2024: 1_000_000, 2025: 0, 2026: 0}, term=2)
        assert model.principal_payment[2024] > 0
        assert model.principal_payment[2025] > 0
        assert model.principal_payment[2026] == 0

    def test_long_term(self):
        model = _make_model(
            {2024: 1_000_000, 2025: 0, 2026: 0, 2027: 0, 2028: 0},
            term=30,
            extra_periods=[2025, 2026, 2027, 2028],
        )
        assert model.interest_expense[2024] > model.principal_payment[2024]
