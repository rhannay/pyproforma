"""
Tests for InputLine and InputAssumption — scenario input types for v2 models.
"""

import pytest

from pyproforma.v2 import (
    Assumption,
    FixedLine,
    FormulaLine,
    InputAssumption,
    InputLine,
    ProformaModel,
)


# ---------------------------------------------------------------------------
# InputLine — class-level behaviour
# ---------------------------------------------------------------------------


class TestInputLineClassLevel:
    def test_discovered_as_line_item(self):
        class M(ProformaModel):
            revenue = InputLine(label="Revenue")

        assert "revenue" in M._line_item_names
        assert "revenue" in M._input_line_names

    def test_not_in_assumption_names(self):
        class M(ProformaModel):
            revenue = InputLine()

        assert "revenue" not in M._assumption_names

    def test_label_stored(self):
        class M(ProformaModel):
            revenue = InputLine(label="Total Revenue")

        assert M.revenue.label == "Total Revenue"

    def test_name_set_by_descriptor(self):
        class M(ProformaModel):
            revenue = InputLine()

        assert M.revenue.name == "revenue"

    def test_repr_with_label(self):
        line = InputLine(label="Revenue")
        line.name = "revenue"
        assert "Revenue" in repr(line)

    def test_repr_without_label(self):
        assert repr(InputLine()) == "InputLine()"


# ---------------------------------------------------------------------------
# InputLine — instantiation and value resolution
# ---------------------------------------------------------------------------


class TestInputLineInstantiation:
    def test_basic_instantiation_with_values(self):
        class M(ProformaModel):
            revenue = InputLine(label="Revenue")

        model = M(periods=[2024, 2025], revenue={2024: 100_000, 2025: 110_000})
        assert model.get_value("revenue", 2024) == 100_000
        assert model.get_value("revenue", 2025) == 110_000

    def test_missing_required_input_raises(self):
        class M(ProformaModel):
            revenue = InputLine()

        with pytest.raises(TypeError, match="requires input line values for: revenue"):
            M(periods=[2024])

    def test_unknown_kwarg_raises(self):
        class M(ProformaModel):
            revenue = InputLine()

        with pytest.raises(TypeError, match="unexpected keyword arguments: typo"):
            M(periods=[2024], revenue={2024: 100}, typo=999)

    def test_multiple_input_lines(self):
        class M(ProformaModel):
            revenue = InputLine()
            costs = InputLine()

        model = M(
            periods=[2024],
            revenue={2024: 200_000},
            costs={2024: 120_000},
        )
        assert model.get_value("revenue", 2024) == 200_000
        assert model.get_value("costs", 2024) == 120_000

    def test_missing_one_of_two_inputs_raises(self):
        class M(ProformaModel):
            revenue = InputLine()
            costs = InputLine()

        with pytest.raises(TypeError, match="costs"):
            M(periods=[2024], revenue={2024: 100})

    def test_input_line_usable_in_formula(self):
        class M(ProformaModel):
            revenue = InputLine()
            profit = FormulaLine(formula=lambda a, li, t: li.revenue[t] * 0.4)

        model = M(periods=[2024], revenue={2024: 500_000})
        assert model.get_value("profit", 2024) == 200_000.0

    def test_different_instances_different_values(self):
        class M(ProformaModel):
            revenue = InputLine()

        base = M(periods=[2024], revenue={2024: 100_000})
        bull = M(periods=[2024], revenue={2024: 150_000})

        assert base.get_value("revenue", 2024) == 100_000
        assert bull.get_value("revenue", 2024) == 150_000

    def test_input_line_and_fixed_line_together(self):
        class M(ProformaModel):
            fixed_costs = FixedLine(values={2024: 50_000, 2025: 52_000})
            revenue = InputLine()
            profit = FormulaLine(
                formula=lambda a, li, t: li.revenue[t] - li.fixed_costs[t]
            )

        model = M(
            periods=[2024, 2025],
            revenue={2024: 200_000, 2025: 220_000},
        )
        assert model.get_value("profit", 2024) == 150_000.0
        assert model.get_value("profit", 2025) == 168_000.0

    def test_input_line_missing_period_raises(self):
        """Providing values for fewer periods than the model runs raises an error."""

        class M(ProformaModel):
            revenue = InputLine()

        with pytest.raises(ValueError, match="No input value for 'revenue' in period 2025"):
            M(periods=[2024, 2025], revenue={2024: 100_000})


# ---------------------------------------------------------------------------
# InputAssumption — class-level behaviour
# ---------------------------------------------------------------------------


class TestInputAssumptionClassLevel:
    def test_discovered_as_assumption(self):
        class M(ProformaModel):
            tax_rate = InputAssumption(default=0.21)

        assert "tax_rate" in M._assumption_names
        assert "tax_rate" in M._input_assumption_names

    def test_not_in_line_item_names(self):
        class M(ProformaModel):
            tax_rate = InputAssumption(default=0.21)

        assert "tax_rate" not in M._line_item_names

    def test_has_default_true(self):
        a = InputAssumption(default=0.21)
        assert a.has_default is True

    def test_has_default_false(self):
        a = InputAssumption()
        assert a.has_default is False

    def test_repr_with_default(self):
        a = InputAssumption(default=0.21, label="Tax Rate")
        r = repr(a)
        assert "0.21" in r
        assert "Tax Rate" in r

    def test_repr_without_default(self):
        assert repr(InputAssumption()) == "InputAssumption()"

    def test_name_set_by_descriptor(self):
        class M(ProformaModel):
            tax_rate = InputAssumption(default=0.21)

        assert M.tax_rate.name == "tax_rate"


# ---------------------------------------------------------------------------
# InputAssumption — instantiation and value resolution
# ---------------------------------------------------------------------------


class TestInputAssumptionInstantiation:
    def test_default_used_when_not_provided(self):
        class M(ProformaModel):
            tax_rate = InputAssumption(default=0.21)
            revenue = FixedLine(values={2024: 100_000})

        model = M(periods=[2024])
        assert model.av.tax_rate == 0.21

    def test_kwarg_overrides_default(self):
        class M(ProformaModel):
            tax_rate = InputAssumption(default=0.21)
            revenue = FixedLine(values={2024: 100_000})

        model = M(periods=[2024], tax_rate=0.28)
        assert model.av.tax_rate == 0.28

    def test_required_input_assumption_provided(self):
        class M(ProformaModel):
            tax_rate = InputAssumption()  # no default — required
            revenue = FixedLine(values={2024: 100_000})

        model = M(periods=[2024], tax_rate=0.25)
        assert model.av.tax_rate == 0.25

    def test_required_input_assumption_missing_raises(self):
        class M(ProformaModel):
            tax_rate = InputAssumption()
            revenue = FixedLine(values={2024: 100_000})

        with pytest.raises(TypeError, match="requires input assumption values for: tax_rate"):
            M(periods=[2024])

    def test_input_assumption_usable_in_formula(self):
        class M(ProformaModel):
            tax_rate = InputAssumption(default=0.21)
            revenue = FixedLine(values={2024: 100_000})
            after_tax = FormulaLine(
                formula=lambda a, li, t: li.revenue[t] * (1 - a.tax_rate)
            )

        base = M(periods=[2024])
        assert base.get_value("after_tax", 2024) == pytest.approx(79_000.0)

        high_tax = M(periods=[2024], tax_rate=0.30)
        assert high_tax.get_value("after_tax", 2024) == pytest.approx(70_000.0)

    def test_assumption_and_input_assumption_coexist(self):
        class M(ProformaModel):
            fixed_rate = Assumption(value=0.05)
            variable_rate = InputAssumption(default=0.10)
            revenue = FixedLine(values={2024: 100_000})

        model = M(periods=[2024], variable_rate=0.15)
        assert model.av.fixed_rate == 0.05
        assert model.av.variable_rate == 0.15


# ---------------------------------------------------------------------------
# Combined InputLine + InputAssumption — scenario workflow
# ---------------------------------------------------------------------------


class TestScenarioWorkflow:
    def test_base_and_bull_scenario(self):
        class IncomeModel(ProformaModel):
            expense_ratio = InputAssumption(default=0.60, label="Expense Ratio")
            revenue = InputLine(label="Revenue")
            expenses = FormulaLine(
                formula=lambda a, li, t: li.revenue[t] * a.expense_ratio
            )
            profit = FormulaLine(
                formula=lambda a, li, t: li.revenue[t] - li.expenses[t]
            )

        base = IncomeModel(
            periods=[2024, 2025],
            revenue={2024: 1_000_000, 2025: 1_100_000},
        )
        bull = IncomeModel(
            periods=[2024, 2025],
            revenue={2024: 1_400_000, 2025: 1_600_000},
            expense_ratio=0.50,
        )

        assert base.get_value("profit", 2024) == pytest.approx(400_000.0)
        assert base.get_value("profit", 2025) == pytest.approx(440_000.0)

        assert bull.get_value("profit", 2024) == pytest.approx(700_000.0)
        assert bull.get_value("profit", 2025) == pytest.approx(800_000.0)

    def test_fixed_line_unchanged_across_scenarios(self):
        """FixedLine values cannot vary between instances — that's the point."""

        class M(ProformaModel):
            fixed_overhead = FixedLine(values={2024: 50_000})
            revenue = InputLine()
            profit = FormulaLine(
                formula=lambda a, li, t: li.revenue[t] - li.fixed_overhead[t]
            )

        s1 = M(periods=[2024], revenue={2024: 200_000})
        s2 = M(periods=[2024], revenue={2024: 300_000})

        assert s1.get_value("fixed_overhead", 2024) == 50_000
        assert s2.get_value("fixed_overhead", 2024) == 50_000
        assert s1.get_value("profit", 2024) == 150_000.0
        assert s2.get_value("profit", 2024) == 250_000.0
