"""
Tests for ProformaModel and calculation engine.
"""

import pytest

from pyproforma import FixedLine, FormulaLine, InputLine, ProformaModel, ScalarInputLine, ScalarLine
from pyproforma.results.line_item_result import LineItemResult
from pyproforma.results.scalar_result import ScalarResult


class TestProformaModelBasic:
    """Basic tests for ProformaModel."""

    def test_model_discovery(self):
        class TestModel(ProformaModel):
            tax_rate = ScalarLine(value=0.21)
            revenue = FixedLine(values={2024: 100})
            profit = FormulaLine(formula=lambda li, t: li.revenue[t] * 0.5)

        assert "tax_rate" in TestModel._scalar_names
        assert "revenue" in TestModel._line_item_names
        assert "profit" in TestModel._line_item_names

    def test_model_initialization_no_periods(self):
        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})

        model = TestModel()
        assert model.periods == []

    def test_model_initialization_with_periods(self):
        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100, 2025: 110})

        model = TestModel(periods=[2024, 2025])
        assert model.periods == [2024, 2025]

    def test_stores_line_item_names_on_instance(self):
        class TestModel(ProformaModel):
            tax_rate = ScalarLine(value=0.21)
            revenue = FixedLine(values={2024: 100})
            expenses = FormulaLine(formula=lambda li, t: li.revenue[t] * 0.6)
            profit = FormulaLine(formula=lambda li, t: li.revenue[t] - li.expenses[t])

        model = TestModel(periods=[2024])

        assert hasattr(model, "line_item_names")
        assert isinstance(model.line_item_names, list)
        assert "tax_rate" in model.scalar_names
        assert "revenue" in model.line_item_names
        assert "expenses" in model.line_item_names
        assert "profit" in model.line_item_names


class TestScalarFixedLine:
    """Tests for scalar FixedLine (replaces Assumption)."""

    def test_scalar_stored_in_scalars(self):
        class TestModel(ProformaModel):
            tax_rate = ScalarLine(value=0.21)

        model = TestModel(periods=[2024])
        assert model._scalars["tax_rate"] == 0.21

    def test_scalar_accessible_in_formula_without_t(self):
        class TestModel(ProformaModel):
            expense_ratio = ScalarLine(value=0.6)
            revenue = FixedLine(values={2024: 100})
            expenses = FormulaLine(formula=lambda li, t: li.revenue[t] * li.expense_ratio)

        model = TestModel(periods=[2024])
        assert model.get_value("expenses", 2024) == 60.0

    def test_multiple_scalars(self):
        class TestModel(ProformaModel):
            tax_rate = ScalarLine(value=0.21)
            growth_rate = ScalarLine(value=0.1)
            revenue = FixedLine(values={2024: 100})

        model = TestModel(periods=[2024])
        assert model._scalars["tax_rate"] == 0.21
        assert model._scalars["growth_rate"] == 0.1

    def test_scalar_getitem_returns_value(self):
        class TestModel(ProformaModel):
            rate = ScalarLine(value=0.05)

        model = TestModel(periods=[2024, 2025, 2026])
        assert model["rate"].value == 0.05
        assert isinstance(model["rate"], ScalarResult)


class TestFixedLineCalculation:
    """Tests for FixedLine calculation."""

    def test_single_period(self):
        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})

        model = TestModel(periods=[2024])
        assert model.get_value("revenue", 2024) == 100

    def test_multiple_periods(self):
        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100, 2025: 110, 2026: 121})

        model = TestModel(periods=[2024, 2025, 2026])
        assert model.get_value("revenue", 2024) == 100
        assert model.get_value("revenue", 2025) == 110
        assert model.get_value("revenue", 2026) == 121

    def test_missing_value_raises_error(self):
        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})

        with pytest.raises(ValueError, match="No value defined"):
            TestModel(periods=[2024, 2025])

    def test_scalar_line_has_no_values_param(self):
        with pytest.raises(TypeError):
            ScalarLine(value=0.21, values={2024: 100})


class TestFormulaLineCalculation:
    """Tests for FormulaLine calculation."""

    def test_simple_formula(self):
        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})
            expenses = FormulaLine(formula=lambda li, t: li.revenue[t] * 0.6)

        model = TestModel(periods=[2024])
        assert model.get_value("expenses", 2024) == 60.0

    def test_formula_with_scalar(self):
        class TestModel(ProformaModel):
            expense_ratio = ScalarLine(value=0.6)
            revenue = FixedLine(values={2024: 100})
            expenses = FormulaLine(formula=lambda li, t: li.revenue[t] * li.expense_ratio)

        model = TestModel(periods=[2024])
        assert model.get_value("expenses", 2024) == 60.0

    def test_formula_referencing_formula(self):
        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})
            expenses = FormulaLine(formula=lambda li, t: li.revenue[t] * 0.6)
            profit = FormulaLine(formula=lambda li, t: li.revenue[t] - li.expenses[t])

        model = TestModel(periods=[2024])
        assert model.get_value("profit", 2024) == 40.0

    def test_formula_with_override(self):
        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100, 2025: 110})
            expenses = FormulaLine(formula=lambda li, t: li.revenue[t] * 0.6, values={2024: 50})

        model = TestModel(periods=[2024, 2025])
        assert model.get_value("expenses", 2024) == 50
        assert model.get_value("expenses", 2025) == 66.0

    def test_multiple_periods(self):
        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100, 2025: 110, 2026: 121})
            expenses = FormulaLine(formula=lambda li, t: li.revenue[t] * 0.6)
            profit = FormulaLine(formula=lambda li, t: li.revenue[t] - li.expenses[t])

        model = TestModel(periods=[2024, 2025, 2026])
        assert model.get_value("profit", 2024) == 40.0
        assert model.get_value("profit", 2025) == 44.0
        assert abs(model.get_value("profit", 2026) - 48.4) < 0.0001


class TestDependents:
    """Tests for ProformaModel.dependents()."""

    def test_single_dependent(self):
        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})
            expenses = FormulaLine(formula=lambda li, t: li.revenue[t] * 0.6)

        model = TestModel(periods=[2024])
        assert model.dependents("revenue") == ["expenses"]

    def test_multiple_dependents(self):
        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})
            expenses = FormulaLine(formula=lambda li, t: li.revenue[t] * 0.6)
            profit = FormulaLine(formula=lambda li, t: li.revenue[t] - li.expenses[t])

        model = TestModel(periods=[2024])
        assert model.dependents("revenue") == ["expenses", "profit"]

    def test_scalar_dependents(self):
        class TestModel(ProformaModel):
            rate = ScalarLine(value=0.6)
            revenue = FixedLine(values={2024: 100})
            expenses = FormulaLine(formula=lambda li, t: li.revenue[t] * li.rate)

        model = TestModel(periods=[2024])
        assert model.dependents("rate") == ["expenses"]

    def test_no_dependents(self):
        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})
            expenses = FormulaLine(formula=lambda li, t: li.revenue[t] * 0.6)

        model = TestModel(periods=[2024])
        assert model.dependents("expenses") == []

    def test_fixed_line_has_no_dependents_detected(self):
        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})

        model = TestModel(periods=[2024])
        assert model.dependents("revenue") == []


class TestComplexModel:
    """Tests for more complex model scenarios."""

    def test_example_model(self):
        class SimpleFinancialModel(ProformaModel):
            expense_ratio = ScalarLine(value=0.6, label="Expense Ratio")
            revenue = FixedLine(values={2024: 100000, 2025: 110000, 2026: 121000}, label="Revenue")
            expenses = FormulaLine(formula=lambda li, t: li.revenue[t] * li.expense_ratio, label="Operating Expenses")
            profit = FormulaLine(formula=lambda li, t: li.revenue[t] - li.expenses[t], label="Net Profit")

        model = SimpleFinancialModel(periods=[2024, 2025, 2026])

        assert model._scalars["expense_ratio"] == 0.6
        assert model.get_value("revenue", 2024) == 100000
        assert model.get_value("expenses", 2024) == 60000.0
        assert model.get_value("profit", 2024) == 40000.0
        assert model.get_value("profit", 2025) == 44000.0
        assert model.get_value("profit", 2026) == 48400.0


class TestAttributeAccess:
    """Tests for dot-notation access: model.line_item_name returns LineItemResult."""

    def setup_method(self):
        class M(ProformaModel):
            revenue = FixedLine(values={2024: 100_000, 2025: 110_000}, label="Revenue")
            cost = FormulaLine(formula=lambda li, t: li.revenue[t] * 0.6, label="Cost")
            rate = ScalarInputLine(default=0.1, label="Rate")

        self.M = M
        self.model = M(periods=[2024, 2025])

    def test_instance_attribute_returns_line_item_result(self):
        assert isinstance(self.model.revenue, LineItemResult)

    def test_instance_attribute_correct_name(self):
        assert self.model.revenue.name == "revenue"

    def test_instance_attribute_correct_value(self):
        assert self.model.revenue[2024] == 100_000

    def test_formula_line_attribute_access(self):
        assert self.model.cost[2024] == 60_000.0

    def test_input_line_attribute_access(self):
        assert isinstance(self.model.rate, ScalarResult)
        assert self.model.rate.value == 0.1

    def test_class_level_access_returns_descriptor(self):
        from pyproforma.specs.fixed_line import FixedLine as FL
        from pyproforma.specs.scalar_input_line import ScalarInputLine as SIL
        assert isinstance(self.M.revenue, FL)
        assert isinstance(self.M.rate, SIL)

    def test_attribute_access_matches_subscript_access(self):
        assert self.model.revenue[2024] == self.model["revenue"][2024]
        assert self.model.revenue[2025] == self.model["revenue"][2025]
        assert self.model.rate.value == self.model["rate"].value

    def test_fluent_chain(self):
        assert self.model.revenue.label == "Revenue"
        assert self.model.revenue.values == {2024: 100_000, 2025: 110_000}
        assert self.model.rate.label == "Rate"
