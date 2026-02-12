"""
Tests for calculation_engine module.

These tests verify the calculate_line_items function and related helpers.
"""

import pytest

from pyproforma.v2 import Assumption, FixedLine, FormulaLine, ProformaModel
from pyproforma.v2.assumption_values import AssumptionValues
from pyproforma.v2.calculation_engine import (
    _calculate_single_line_item,
    calculate_line_items,
)
from pyproforma.v2.line_item_values import LineItemValues


class TestCalculateLineItems:
    """Tests for the calculate_line_items function."""

    def test_empty_model(self):
        """Test calculating line items for a model with no line items."""

        class EmptyModel(ProformaModel):
            pass

        model = EmptyModel.__new__(EmptyModel)
        model.periods = [2024]
        model.line_item_names = EmptyModel._line_item_names
        model.assumption_names = EmptyModel._assumption_names
        av = AssumptionValues({})

        li = calculate_line_items(model, av, [2024])

        # Empty model should have no line items
        assert li._values == {}

    def test_single_fixed_line(self):
        """Test calculating a single FixedLine."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100, 2025: 110})

        model = TestModel.__new__(TestModel)
        model.periods = [2024, 2025]
        model.line_item_names = TestModel._line_item_names
        model.assumption_names = TestModel._assumption_names
        av = AssumptionValues({})

        li = calculate_line_items(model, av, [2024, 2025])

        assert li.get("revenue", 2024) == 100
        assert li.get("revenue", 2025) == 110

    def test_multiple_fixed_lines(self):
        """Test calculating multiple FixedLines."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100, 2025: 110})
            headcount = FixedLine(values={2024: 5, 2025: 7})

        model = TestModel.__new__(TestModel)
        model.periods = [2024, 2025]
        model.line_item_names = TestModel._line_item_names
        model.assumption_names = TestModel._assumption_names
        av = AssumptionValues({})

        li = calculate_line_items(model, av, [2024, 2025])

        assert li.get("revenue", 2024) == 100
        assert li.get("revenue", 2025) == 110
        assert li.get("headcount", 2024) == 5
        assert li.get("headcount", 2025) == 7

    def test_formula_line_simple(self):
        """Test calculating a simple FormulaLine."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})
            expenses = FormulaLine(formula=lambda a, li, t: li.revenue[t] * 0.6)

        model = TestModel.__new__(TestModel)
        model.periods = [2024]
        model.line_item_names = TestModel._line_item_names
        model.assumption_names = TestModel._assumption_names
        av = AssumptionValues({})

        li = calculate_line_items(model, av, [2024])

        assert li.get("revenue", 2024) == 100
        assert li.get("expenses", 2024) == 60.0

    def test_formula_line_with_assumption(self):
        """Test FormulaLine using an assumption."""

        class TestModel(ProformaModel):
            expense_ratio = Assumption(value=0.65)
            revenue = FixedLine(values={2024: 100})
            expenses = FormulaLine(formula=lambda a, li, t: li.revenue[t] * a.expense_ratio)

        model = TestModel.__new__(TestModel)
        model.periods = [2024]
        model.line_item_names = TestModel._line_item_names
        model.assumption_names = TestModel._assumption_names
        av = AssumptionValues({"expense_ratio": 0.65})

        li = calculate_line_items(model, av, [2024])

        assert li.get("expenses", 2024) == 65.0

    def test_formula_line_chain(self):
        """Test FormulaLines that depend on other FormulaLines."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})
            expenses = FormulaLine(formula=lambda a, li, t: li.revenue[t] * 0.6)
            profit = FormulaLine(formula=lambda a, li, t: li.revenue[t] - li.expenses[t])

        model = TestModel.__new__(TestModel)
        model.periods = [2024]
        model.line_item_names = TestModel._line_item_names
        model.assumption_names = TestModel._assumption_names
        av = AssumptionValues({})

        li = calculate_line_items(model, av, [2024])

        assert li.get("revenue", 2024) == 100
        assert li.get("expenses", 2024) == 60.0
        assert li.get("profit", 2024) == 40.0

    def test_formula_line_with_override(self):
        """Test FormulaLine with value override."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100, 2025: 110})
            expenses = FormulaLine(
                formula=lambda a, li, t: li.revenue[t] * 0.6,
                values={2024: 50}  # Override for 2024
            )

        model = TestModel.__new__(TestModel)
        model.periods = [2024, 2025]
        model.line_item_names = TestModel._line_item_names
        model.assumption_names = TestModel._assumption_names
        av = AssumptionValues({})

        li = calculate_line_items(model, av, [2024, 2025])

        assert li.get("expenses", 2024) == 50  # Override value
        assert li.get("expenses", 2025) == 66.0  # Calculated value

    def test_multiple_periods(self):
        """Test calculating across multiple periods."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100, 2025: 110, 2026: 121})
            expenses = FormulaLine(formula=lambda a, li, t: li.revenue[t] * 0.6)
            profit = FormulaLine(formula=lambda a, li, t: li.revenue[t] - li.expenses[t])

        model = TestModel.__new__(TestModel)
        model.periods = [2024, 2025, 2026]
        model.line_item_names = TestModel._line_item_names
        model.assumption_names = TestModel._assumption_names
        av = AssumptionValues({})

        li = calculate_line_items(model, av, [2024, 2025, 2026])

        # Check all periods were calculated
        assert li.get("profit", 2024) == 40.0
        assert li.get("profit", 2025) == 44.0
        assert abs(li.get("profit", 2026) - 48.4) < 0.0001

    def test_returns_line_item_values(self):
        """Test that calculate_line_items returns a LineItemValues instance."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})

        model = TestModel.__new__(TestModel)
        model.periods = [2024]
        model.line_item_names = TestModel._line_item_names
        model.assumption_names = TestModel._assumption_names
        av = AssumptionValues({})

        result = calculate_line_items(model, av, [2024])

        assert isinstance(result, LineItemValues)
        # Verify it calculated the revenue
        assert result.get("revenue", 2024) == 100


class TestCalculateSingleLineItem:
    """Tests for the _calculate_single_line_item helper function."""

    def test_fixed_line_calculation(self):
        """Test calculating a single FixedLine."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})

        model = TestModel.__new__(TestModel)
        av = AssumptionValues({})
        li = LineItemValues(periods=[2024])

        value = _calculate_single_line_item(TestModel.revenue, av, li, 2024)

        assert value == 100
        # Since _calculate_single_line_item is now pure, it doesn't set values in li
        # The caller is responsible for that
        li.set("revenue", 2024, value)
        assert li.get("revenue", 2024) == 100

    def test_formula_line_calculation(self):
        """Test calculating a single FormulaLine."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})
            expenses = FormulaLine(formula=lambda a, li, t: li.revenue[t] * 0.6)

        model = TestModel.__new__(TestModel)
        av = AssumptionValues({})
        li = LineItemValues(periods=[2024], names=["revenue", "expenses"])

        # First calculate revenue
        revenue_value = _calculate_single_line_item(TestModel.revenue, av, li, 2024)
        li.set("revenue", 2024, revenue_value)

        # Then calculate expenses
        value = _calculate_single_line_item(TestModel.expenses, av, li, 2024)

        assert value == 60.0
        # Since _calculate_single_line_item is now pure, it doesn't set values in li
        li.set("expenses", 2024, value)
        assert li.get("expenses", 2024) == 60.0

    def test_missing_line_item_raises_error(self):
        """Test that referencing a non-existent line item raises AttributeError."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})

        model = TestModel.__new__(TestModel)
        av = AssumptionValues({})
        li = LineItemValues(periods=[2024], names=["revenue"])

        with pytest.raises(AttributeError):
            # Accessing a non-existent attribute will raise AttributeError
            _calculate_single_line_item(TestModel.missing, av, li, 2024)

    def test_missing_fixed_value_raises_error(self):
        """Test that missing FixedLine value raises ValueError."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})

        model = TestModel.__new__(TestModel)
        av = AssumptionValues({})
        li = LineItemValues(periods=[2024, 2025], names=["revenue"])

        with pytest.raises(ValueError, match="No value defined for 'revenue' in period 2025"):
            _calculate_single_line_item(TestModel.revenue, av, li, 2025)

    def test_formula_error_raises_value_error(self):
        """Test that formula execution errors are wrapped in ValueError."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})
            bad_formula = FormulaLine(formula=lambda a, li, t: 1 / 0)  # Division by zero

        model = TestModel.__new__(TestModel)
        av = AssumptionValues({})
        li = LineItemValues(periods=[2024], names=["revenue", "bad_formula"])

        with pytest.raises(ValueError, match="Error evaluating formula for 'bad_formula'"):
            _calculate_single_line_item(TestModel.bad_formula, av, li, 2024)

    def test_formula_returns_non_numeric_raises_error(self):
        """Test that formula returning non-numeric value raises ValueError."""

        class TestModel(ProformaModel):
            bad_formula = FormulaLine(formula=lambda a, li, t: "not a number")

        model = TestModel.__new__(TestModel)
        av = AssumptionValues({})
        li = LineItemValues(periods=[2024], names=["bad_formula"])

        with pytest.raises(ValueError, match="returned invalid type"):
            _calculate_single_line_item(TestModel.bad_formula, av, li, 2024)


class TestIntegrationWithProformaModel:
    """Integration tests verifying calculate_line_items works with ProformaModel."""

    def test_simple_model_integration(self):
        """Test that ProformaModel uses calculate_line_items correctly."""

        class SimpleModel(ProformaModel):
            revenue = FixedLine(values={2024: 100, 2025: 110})
            expenses = FormulaLine(formula=lambda a, li, t: li.revenue[t] * 0.6)

        model = SimpleModel(periods=[2024, 2025])

        # Verify the model's li attribute is properly populated
        assert model.get_value("revenue", 2024) == 100
        assert model.get_value("revenue", 2025) == 110
        assert model.get_value("expenses", 2024) == 60.0
        assert model.get_value("expenses", 2025) == 66.0

    def test_model_with_no_periods(self):
        """Test that model with no periods gets empty LineItemValues."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})

        model = TestModel(periods=[])

        assert isinstance(model._li, LineItemValues)
        # No periods means no calculations
        assert model._li._values == {}

    def test_complex_model_integration(self):
        """Test a complex model with assumptions and multiple dependencies."""

        class ComplexModel(ProformaModel):
            expense_ratio = Assumption(value=0.6)
            tax_rate = Assumption(value=0.21)

            revenue = FixedLine(values={2024: 100, 2025: 110, 2026: 121})
            expenses = FormulaLine(formula=lambda a, li, t: li.revenue[t] * a.expense_ratio)
            ebitda = FormulaLine(formula=lambda a, li, t: li.revenue[t] - li.expenses[t])
            tax = FormulaLine(formula=lambda a, li, t: li.ebitda[t] * a.tax_rate)
            net_income = FormulaLine(formula=lambda a, li, t: li.ebitda[t] - li.tax[t])

        model = ComplexModel(periods=[2024, 2025, 2026])

        # Verify all calculations are correct
        assert model.get_value("revenue", 2024) == 100
        assert model.get_value("expenses", 2024) == 60.0
        assert model.get_value("ebitda", 2024) == 40.0
        assert model.get_value("tax", 2024) == 8.4
        assert abs(model.get_value("net_income", 2024) - 31.6) < 0.0001


class TestDependencyResolution:
    """Tests for automatic dependency resolution in calculation engine."""

    def test_formula_before_fixed_line(self):
        """Test that formula can come before the fixed line it depends on."""

        class TestModel(ProformaModel):
            # Define expenses BEFORE revenue to test dependency resolution
            expenses = FormulaLine(formula=lambda a, li, t: li.revenue[t] * 0.6)
            revenue = FixedLine(values={2024: 100, 2025: 110})

        model = TestModel.__new__(TestModel)
        model.periods = [2024, 2025]
        model.line_item_names = TestModel._line_item_names
        model.assumption_names = TestModel._assumption_names
        av = AssumptionValues({})

        li = calculate_line_items(model, av, [2024, 2025])

        # Should calculate correctly despite order
        assert li.get("revenue", 2024) == 100
        assert li.get("expenses", 2024) == 60.0
        assert li.get("revenue", 2025) == 110
        assert li.get("expenses", 2025) == 66.0

    def test_reverse_dependency_chain(self):
        """Test formulas defined in reverse dependency order."""

        class TestModel(ProformaModel):
            # Define in reverse order: profit depends on expenses and revenue,
            # expenses depends on revenue
            profit = FormulaLine(formula=lambda a, li, t: li.revenue[t] - li.expenses[t])
            expenses = FormulaLine(formula=lambda a, li, t: li.revenue[t] * 0.6)
            revenue = FixedLine(values={2024: 100})

        model = TestModel.__new__(TestModel)
        model.periods = [2024]
        model.line_item_names = TestModel._line_item_names
        model.assumption_names = TestModel._assumption_names
        av = AssumptionValues({})

        li = calculate_line_items(model, av, [2024])

        # All should calculate correctly
        assert li.get("revenue", 2024) == 100
        assert li.get("expenses", 2024) == 60.0
        assert li.get("profit", 2024) == 40.0

    def test_mixed_order_dependencies(self):
        """Test complex dependency graph with mixed ordering."""

        class TestModel(ProformaModel):
            # Mixed order to test dependency resolution
            net_income = FormulaLine(formula=lambda a, li, t: li.ebitda[t] - li.tax[t])
            revenue = FixedLine(values={2024: 100})
            tax = FormulaLine(formula=lambda a, li, t: li.ebitda[t] * 0.21)
            expenses = FormulaLine(formula=lambda a, li, t: li.revenue[t] * 0.6)
            ebitda = FormulaLine(formula=lambda a, li, t: li.revenue[t] - li.expenses[t])

        model = TestModel.__new__(TestModel)
        model.periods = [2024]
        model.line_item_names = TestModel._line_item_names
        model.assumption_names = TestModel._assumption_names
        av = AssumptionValues({})

        li = calculate_line_items(model, av, [2024])

        # All should calculate correctly despite mixed order
        assert li.get("revenue", 2024) == 100
        assert li.get("expenses", 2024) == 60.0
        assert li.get("ebitda", 2024) == 40.0
        assert li.get("tax", 2024) == 8.4
        assert abs(li.get("net_income", 2024) - 31.6) < 0.0001

    def test_circular_reference_detection(self):
        """Test that circular references are detected and raise an error."""

        class TestModel(ProformaModel):
            # Create a circular reference: a -> b -> c -> a
            a = FormulaLine(formula=lambda av, li, t: li.c[t] + 1)
            b = FormulaLine(formula=lambda av, li, t: li.a[t] + 1)
            c = FormulaLine(formula=lambda av, li, t: li.b[t] + 1)

        model = TestModel.__new__(TestModel)
        model.periods = [2024]
        model.line_item_names = TestModel._line_item_names
        model.assumption_names = TestModel._assumption_names
        av = AssumptionValues({})

        # Should detect circular reference and raise error
        with pytest.raises(ValueError, match="Circular reference detected"):
            calculate_line_items(model, av, [2024])

    def test_self_circular_reference(self):
        """Test that self-referencing formula is detected as circular."""

        class TestModel(ProformaModel):
            # Formula that references itself
            bad = FormulaLine(formula=lambda av, li, t: li.bad[t] + 1)

        model = TestModel.__new__(TestModel)
        model.periods = [2024]
        model.line_item_names = TestModel._line_item_names
        model.assumption_names = TestModel._assumption_names
        av = AssumptionValues({})

        # Should detect self-reference as circular
        with pytest.raises(ValueError, match="Circular reference detected"):
            calculate_line_items(model, av, [2024])

    def test_dependency_resolution_multiple_periods(self):
        """Test dependency resolution works across multiple periods."""

        class TestModel(ProformaModel):
            # Define in non-dependency order
            profit = FormulaLine(formula=lambda a, li, t: li.revenue[t] - li.expenses[t])
            expenses = FormulaLine(formula=lambda a, li, t: li.revenue[t] * 0.6)
            revenue = FixedLine(values={2024: 100, 2025: 110, 2026: 121})

        model = TestModel.__new__(TestModel)
        model.periods = [2024, 2025, 2026]
        model.line_item_names = TestModel._line_item_names
        model.assumption_names = TestModel._assumption_names
        av = AssumptionValues({})

        li = calculate_line_items(model, av, [2024, 2025, 2026])

        # Check all periods calculated correctly
        assert li.get("profit", 2024) == 40.0
        assert li.get("profit", 2025) == 44.0
        assert abs(li.get("profit", 2026) - 48.4) < 0.0001

    def test_integration_with_proforma_model(self):
        """Integration test: ProformaModel with reversed dependency order."""

        class ReversedModel(ProformaModel):
            # Define everything in reverse order
            net_income = FormulaLine(formula=lambda a, li, t: li.ebitda[t] - li.tax[t])
            tax = FormulaLine(formula=lambda a, li, t: li.ebitda[t] * 0.21)
            ebitda = FormulaLine(formula=lambda a, li, t: li.revenue[t] - li.expenses[t])
            expenses = FormulaLine(formula=lambda a, li, t: li.revenue[t] * 0.6)
            revenue = FixedLine(values={2024: 100})

        # This should work seamlessly through __init__
        model = ReversedModel(periods=[2024])

        assert model.get_value("revenue", 2024) == 100
        assert model.get_value("expenses", 2024) == 60.0
        assert model.get_value("ebitda", 2024) == 40.0
        assert model.get_value("tax", 2024) == 8.4
        assert abs(model.get_value("net_income", 2024) - 31.6) < 0.0001
