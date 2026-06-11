"""
Tests for InputLine — scenario input types for v2 models.
"""

import pytest

from pyproforma import FixedLine, FormulaLine, InputLine, ProformaModel, ScalarInputLine
from pyproforma.table import Format


class TestInputLineClassLevel:
    def test_discovered_as_line_item(self):
        class M(ProformaModel):
            revenue = InputLine(label="Revenue")

        assert "revenue" in M._line_item_names
        assert "revenue" in M._input_line_names

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

    def test_has_default_true(self):
        line = InputLine(default={2024: 0.05, 2025: 0.04})
        assert line.has_default is True

    def test_has_default_false(self):
        assert InputLine().has_default is False

    def test_default_property_returns_dict(self):
        d = {2024: 0.05, 2025: 0.04}
        line = InputLine(default=d)
        assert line.default == d

    def test_default_property_raises_when_missing(self):
        with pytest.raises(AttributeError, match="has no default value"):
            InputLine().default


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

        with pytest.raises(TypeError, match="requires values for: revenue"):
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

        model = M(periods=[2024], revenue={2024: 200_000}, costs={2024: 120_000})
        assert model.get_value("revenue", 2024) == 200_000
        assert model.get_value("costs", 2024) == 120_000

    def test_input_line_usable_in_formula(self):
        class M(ProformaModel):
            revenue = InputLine()
            profit = FormulaLine(formula=lambda li, t: li.revenue[t] * 0.4)

        model = M(periods=[2024], revenue={2024: 500_000})
        assert model.get_value("profit", 2024) == 200_000.0

    def test_different_instances_different_values(self):
        class M(ProformaModel):
            revenue = InputLine()

        base = M(periods=[2024], revenue={2024: 100_000})
        bull = M(periods=[2024], revenue={2024: 150_000})

        assert base.get_value("revenue", 2024) == 100_000
        assert bull.get_value("revenue", 2024) == 150_000

    def test_default_used_when_kwarg_omitted(self):
        class M(ProformaModel):
            rate = InputLine(default={2024: 0.05, 2025: 0.06})

        model = M(periods=[2024, 2025])
        assert model.get_value("rate", 2024) == 0.05
        assert model.get_value("rate", 2025) == 0.06

    def test_kwarg_overrides_default(self):
        class M(ProformaModel):
            rate = InputLine(default={2024: 0.05, 2025: 0.06})

        model = M(periods=[2024, 2025], rate={2024: 0.08, 2025: 0.08})
        assert model.get_value("rate", 2024) == 0.08
        assert model.get_value("rate", 2025) == 0.08

    def test_input_line_missing_period_raises(self):
        class M(ProformaModel):
            revenue = InputLine()

        with pytest.raises(ValueError, match="No input value for 'revenue' in period 2025"):
            M(periods=[2024, 2025], revenue={2024: 100_000})


class TestScalarInputLine:
    """Tests for ScalarInputLine (scalar kwarg at instantiation)."""

    def test_scalar_kwarg_stored_in_scalars(self):
        class M(ProformaModel):
            tax_rate = ScalarInputLine(label="Tax Rate")

        model = M(periods=[2024, 2025], tax_rate=0.21)
        assert model._scalars["tax_rate"] == 0.21

    def test_scalar_accessible_in_formula_without_t(self):
        class M(ProformaModel):
            tax_rate = ScalarInputLine(label="Tax Rate")
            revenue = FixedLine(values={2024: 100_000})
            after_tax = FormulaLine(formula=lambda li, t: li.revenue[t] * (1 - li.tax_rate))

        base = M(periods=[2024], tax_rate=0.21)
        assert base.get_value("after_tax", 2024) == pytest.approx(79_000.0)

        high_tax = M(periods=[2024], tax_rate=0.30)
        assert high_tax.get_value("after_tax", 2024) == pytest.approx(70_000.0)

    def test_scalar_getitem_works(self):
        class M(ProformaModel):
            tax_rate = ScalarInputLine()

        model = M(periods=[2024, 2025], tax_rate=0.21)
        assert model["tax_rate"].value == 0.21

    def test_scalar_default(self):
        class M(ProformaModel):
            growth = ScalarInputLine(default=0.05)

        model = M(periods=[2024, 2025])
        assert model._scalars["growth"] == 0.05
        assert model.get_value("growth", 2024) == 0.05
        assert model.get_value("growth", 2025) == 0.05


class TestScenarioWorkflow:
    def test_base_and_bull_scenario(self):
        class IncomeModel(ProformaModel):
            expense_ratio = ScalarInputLine(label="Expense Ratio", default=0.60)
            revenue = InputLine(label="Revenue")
            expenses = FormulaLine(formula=lambda li, t: li.revenue[t] * li.expense_ratio)
            profit = FormulaLine(formula=lambda li, t: li.revenue[t] - li.expenses[t])

        base = IncomeModel(periods=[2024, 2025], revenue={2024: 1_000_000, 2025: 1_100_000})
        bull = IncomeModel(
            periods=[2024, 2025], revenue={2024: 1_400_000, 2025: 1_600_000}, expense_ratio=0.50
        )

        assert base.get_value("profit", 2024) == pytest.approx(400_000.0)
        assert bull.get_value("profit", 2024) == pytest.approx(700_000.0)

    def test_fixed_line_unchanged_across_scenarios(self):
        class M(ProformaModel):
            fixed_overhead = FixedLine(values={2024: 50_000})
            revenue = InputLine()
            profit = FormulaLine(formula=lambda li, t: li.revenue[t] - li.fixed_overhead[t])

        s1 = M(periods=[2024], revenue={2024: 200_000})
        s2 = M(periods=[2024], revenue={2024: 300_000})

        assert s1.get_value("fixed_overhead", 2024) == 50_000
        assert s2.get_value("fixed_overhead", 2024) == 50_000
        assert s1.get_value("profit", 2024) == 150_000.0
        assert s2.get_value("profit", 2024) == 250_000.0


class TestLockedPeriods:
    """InputLine with None values in the default dict — locked periods."""

    def test_none_in_default_instantiates_ok(self):
        class M(ProformaModel):
            rate = InputLine(default={2024: None, 2025: 0.05})
            rev = FixedLine(values={2024: 100, 2025: 100})

        model = M(periods=[2024, 2025])
        assert model._input_line_values["rate"][2024] is None
        assert model._input_line_values["rate"][2025] == pytest.approx(0.05)

    def test_result_for_locked_period_is_none(self):
        class M(ProformaModel):
            rate = InputLine(default={2024: None, 2025: 0.05})
            rev = FixedLine(values={2024: 100, 2025: 100})

        model = M(periods=[2024, 2025])
        assert model["rate"][2024] is None

    def test_override_locked_period_raises(self):
        class M(ProformaModel):
            rate = InputLine(default={2024: None, 2025: 0.05})
            rev = FixedLine(values={2024: 100, 2025: 100})

        with pytest.raises(ValueError, match="locked"):
            M(periods=[2024, 2025], rate={2024: 0.03, 2025: 0.05})

    def test_error_names_the_field_and_period(self):
        class M(ProformaModel):
            rate = InputLine(default={2024: None, 2025: 0.05})
            rev = FixedLine(values={2024: 100, 2025: 100})

        with pytest.raises(ValueError, match="'rate'"):
            M(periods=[2024, 2025], rate={2024: 0.03, 2025: 0.05})

        with pytest.raises(ValueError, match="2024"):
            M(periods=[2024, 2025], rate={2024: 0.03, 2025: 0.05})

    def test_passing_none_explicitly_for_locked_period_is_ok(self):
        class M(ProformaModel):
            rate = InputLine(default={2024: None, 2025: 0.05})
            rev = FixedLine(values={2024: 100, 2025: 100})

        model = M(periods=[2024, 2025], rate={2024: None, 2025: 0.07})
        assert model._input_line_values["rate"][2024] is None
        assert model._input_line_values["rate"][2025] == pytest.approx(0.07)

    def test_partial_dict_auto_fills_locked_periods(self):
        class M(ProformaModel):
            rate = InputLine(default={2024: None, 2025: 0.05})
            rev = FixedLine(values={2024: 100, 2025: 100})

        # Caller omits locked period — should be filled in automatically
        model = M(periods=[2024, 2025], rate={2025: 0.08})
        assert model._input_line_values["rate"][2024] is None
        assert model._input_line_values["rate"][2025] == pytest.approx(0.08)

    def test_locked_period_safe_when_formula_seeded(self):
        """None value is safe if FormulaLine.values seeds that period."""
        class M(ProformaModel):
            rate = InputLine(default={2024: None, 2025: 0.05})
            rev = FormulaLine(
                formula=lambda li, t: li.rev[t - 1] * (1 + li.rate[t]),
                values={2024: 1_000},
            )

        model = M(periods=[2024, 2025])
        assert model["rev"][2024] == pytest.approx(1_000)
        assert model["rev"][2025] == pytest.approx(1_050)

    def test_no_locked_periods_allows_any_value(self):
        class M(ProformaModel):
            rate = InputLine(default={2024: 0.05, 2025: 0.06})
            rev = FixedLine(values={2024: 100, 2025: 100})

        model = M(periods=[2024, 2025], rate={2024: 0.10, 2025: 0.10})
        assert model._input_line_values["rate"][2024] == pytest.approx(0.10)


class TestNonNumericInputLine:
    """Tests for string and boolean ScalarInputLine values."""

    def test_string_scalar_input(self):
        class M(ProformaModel):
            scenario = ScalarInputLine(label="Scenario", default="base")
            revenue = FixedLine(values={2024: 100_000, 2025: 110_000})
            growth = FormulaLine(
                formula=lambda li, t: li.revenue[t] * (1.2 if li.scenario == "aggressive" else 1.0)
            )

        base = M(periods=[2024, 2025])
        assert base.get_value("growth", 2024) == 100_000.0

        aggressive = M(periods=[2024, 2025], scenario="aggressive")
        assert aggressive.get_value("growth", 2024) == 120_000.0

    def test_string_stored_in_scalars(self):
        class M(ProformaModel):
            mode = ScalarInputLine(default="base")

        model = M(periods=[2024])
        assert model._scalars["mode"] == "base"

    def test_boolean_scalar_input(self):
        class M(ProformaModel):
            include_bonus = ScalarInputLine(label="Include Bonus", default=False)
            salary = FixedLine(values={2024: 100_000})
            total_comp = FormulaLine(
                formula=lambda li, t: li.salary[t] * (1.1 if li.include_bonus else 1.0)
            )

        base = M(periods=[2024])
        assert base.get_value("total_comp", 2024) == 100_000.0

        with_bonus = M(periods=[2024], include_bonus=True)
        assert with_bonus.get_value("total_comp", 2024) == pytest.approx(110_000.0)

    def test_formula_line_returning_string(self):
        class M(ProformaModel):
            dscr = FixedLine(values={2024: 1.5, 2025: 0.9})
            status = FormulaLine(
                formula=lambda li, t: "PASS" if li.dscr[t] >= 1.25 else "FAIL"
            )

        model = M(periods=[2024, 2025])
        assert model.get_value("status", 2024) == "PASS"
        assert model.get_value("status", 2025) == "FAIL"

    def test_string_value_formatted_as_string(self):
        from pyproforma.table import format_value
        assert format_value("PASS", Format.NO_DECIMALS) == "PASS"
        assert format_value("WARNING", Format.CURRENCY) == "WARNING"

    def test_string_line_item_formatted_value(self):
        class M(ProformaModel):
            dscr = FixedLine(values={2024: 1.5, 2025: 0.9})
            status = FormulaLine(
                formula=lambda li, t: "PASS" if li.dscr[t] >= 1.25 else "FAIL"
            )

        model = M(periods=[2024, 2025])
        assert model["status"].formatted_value(2024) == "PASS"
        assert model["status"].formatted_value(2025) == "FAIL"
