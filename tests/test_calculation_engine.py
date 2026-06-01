"""
Tests for calculation_engine module.
"""

import pytest

from pyproforma import FixedLine, FormulaLine, ProformaModel
from pyproforma.calculation_engine import _calculate_single_line_item, calculate_line_items
from pyproforma.line_items.line_item_values import LineItemValues
from pyproforma.model_namespace import ModelNamespace


class TestCalculateLineItems:

    def test_empty_model(self):
        class EmptyModel(ProformaModel):
            pass

        model = EmptyModel.__new__(EmptyModel)
        model.periods = [2024]
        model.line_item_names = EmptyModel._line_item_names
        model._input_line_values = {}

        li = calculate_line_items(model, {}, [2024])
        assert li._values == {}

    def test_single_fixed_line(self):
        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100, 2025: 110})

        model = TestModel.__new__(TestModel)
        model.periods = [2024, 2025]
        model.line_item_names = TestModel._line_item_names
        model._input_line_values = {}

        li = calculate_line_items(model, {}, [2024, 2025])
        assert li.get("revenue", 2024) == 100
        assert li.get("revenue", 2025) == 110

    def test_multiple_fixed_lines(self):
        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100, 2025: 110})
            headcount = FixedLine(values={2024: 5, 2025: 7})

        model = TestModel.__new__(TestModel)
        model.periods = [2024, 2025]
        model.line_item_names = TestModel._line_item_names
        model._input_line_values = {}

        li = calculate_line_items(model, {}, [2024, 2025])
        assert li.get("revenue", 2024) == 100
        assert li.get("headcount", 2025) == 7

    def test_formula_line_simple(self):
        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})
            expenses = FormulaLine(formula=lambda li, t: li.revenue[t] * 0.6)

        model = TestModel.__new__(TestModel)
        model.periods = [2024]
        model.line_item_names = TestModel._line_item_names
        model._input_line_values = {}

        li = calculate_line_items(model, {}, [2024])
        assert li.get("expenses", 2024) == 60.0

    def test_formula_line_with_scalar(self):
        class TestModel(ProformaModel):
            expense_ratio = FixedLine(value=0.65)
            revenue = FixedLine(values={2024: 100})
            expenses = FormulaLine(formula=lambda li, t: li.revenue[t] * li.expense_ratio)

        model = TestModel.__new__(TestModel)
        model.periods = [2024]
        model.line_item_names = TestModel._line_item_names
        model._input_line_values = {}

        li = calculate_line_items(model, {"expense_ratio": 0.65}, [2024])
        assert li.get("expenses", 2024) == 65.0

    def test_formula_line_chain(self):
        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})
            expenses = FormulaLine(formula=lambda li, t: li.revenue[t] * 0.6)
            profit = FormulaLine(formula=lambda li, t: li.revenue[t] - li.expenses[t])

        model = TestModel.__new__(TestModel)
        model.periods = [2024]
        model.line_item_names = TestModel._line_item_names
        model._input_line_values = {}

        li = calculate_line_items(model, {}, [2024])
        assert li.get("profit", 2024) == 40.0

    def test_circular_reference_detection(self):
        class TestModel(ProformaModel):
            item_a = FormulaLine(formula=lambda li, t: li.item_c[t] + 1)
            item_b = FormulaLine(formula=lambda li, t: li.item_a[t] + 1)
            item_c = FormulaLine(formula=lambda li, t: li.item_b[t] + 1)

        model = TestModel.__new__(TestModel)
        model.periods = [2024]
        model.line_item_names = TestModel._line_item_names
        model._input_line_values = {}

        with pytest.raises(ValueError, match="Circular reference detected"):
            calculate_line_items(model, {}, [2024])

    def test_returns_line_item_values(self):
        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})

        model = TestModel.__new__(TestModel)
        model.periods = [2024]
        model.line_item_names = TestModel._line_item_names
        model._input_line_values = {}

        result = calculate_line_items(model, {}, [2024])
        assert isinstance(result, LineItemValues)
        assert result.get("revenue", 2024) == 100


class TestCalculateSingleLineItem:

    def test_fixed_line_calculation(self):
        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})

        li = LineItemValues(periods=[2024])
        ns = ModelNamespace(li, {})

        value = _calculate_single_line_item(TestModel.revenue, ns, 2024)
        assert value == 100

    def test_formula_line_calculation(self):
        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})
            expenses = FormulaLine(formula=lambda li, t: li.revenue[t] * 0.6)

        li = LineItemValues(periods=[2024], names=["revenue", "expenses"])
        ns = ModelNamespace(li, {})

        revenue_value = _calculate_single_line_item(TestModel.revenue, ns, 2024)
        li.set("revenue", 2024, revenue_value)

        value = _calculate_single_line_item(TestModel.expenses, ns, 2024)
        assert value == 60.0

    def test_formula_with_scalar(self):
        class TestModel(ProformaModel):
            expense_ratio = FixedLine(value=0.65)
            revenue = FixedLine(values={2024: 100})
            expenses = FormulaLine(formula=lambda li, t: li.revenue[t] * li.expense_ratio)

        li = LineItemValues(periods=[2024], names=["revenue", "expenses"])
        ns = ModelNamespace(li, {"expense_ratio": 0.65})

        li.set("revenue", 2024, 100.0)
        value = _calculate_single_line_item(TestModel.expenses, ns, 2024)
        assert value == 65.0

    def test_missing_fixed_value_raises_error(self):
        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})

        li = LineItemValues(periods=[2024, 2025], names=["revenue"])
        ns = ModelNamespace(li, {})

        with pytest.raises(ValueError, match="No value defined for 'revenue' in period 2025"):
            _calculate_single_line_item(TestModel.revenue, ns, 2025)

    def test_formula_error_raises_value_error(self):
        class TestModel(ProformaModel):
            bad_formula = FormulaLine(formula=lambda li, t: 1 / 0)

        li = LineItemValues(periods=[2024], names=["bad_formula"])
        ns = ModelNamespace(li, {})

        with pytest.raises(ValueError, match="Error evaluating formula for 'bad_formula'"):
            _calculate_single_line_item(TestModel.bad_formula, ns, 2024)

    def test_formula_returns_non_numeric_raises_error(self):
        class TestModel(ProformaModel):
            bad_formula = FormulaLine(formula=lambda li, t: "not a number")

        li = LineItemValues(periods=[2024], names=["bad_formula"])
        ns = ModelNamespace(li, {})

        with pytest.raises(ValueError, match="returned invalid type"):
            _calculate_single_line_item(TestModel.bad_formula, ns, 2024)


class TestDependencyResolution:

    def test_formula_before_fixed_line(self):
        class TestModel(ProformaModel):
            expenses = FormulaLine(formula=lambda li, t: li.revenue[t] * 0.6)
            revenue = FixedLine(values={2024: 100, 2025: 110})

        model = TestModel.__new__(TestModel)
        model.periods = [2024, 2025]
        model.line_item_names = TestModel._line_item_names
        model._input_line_values = {}

        li = calculate_line_items(model, {}, [2024, 2025])
        assert li.get("revenue", 2024) == 100
        assert li.get("expenses", 2024) == 60.0

    def test_reverse_dependency_chain(self):
        class TestModel(ProformaModel):
            profit = FormulaLine(formula=lambda li, t: li.revenue[t] - li.expenses[t])
            expenses = FormulaLine(formula=lambda li, t: li.revenue[t] * 0.6)
            revenue = FixedLine(values={2024: 100})

        model = TestModel.__new__(TestModel)
        model.periods = [2024]
        model.line_item_names = TestModel._line_item_names
        model._input_line_values = {}

        li = calculate_line_items(model, {}, [2024])
        assert li.get("profit", 2024) == 40.0

    def test_self_circular_reference(self):
        class TestModel(ProformaModel):
            bad = FormulaLine(formula=lambda li, t: li.bad[t] + 1)

        model = TestModel.__new__(TestModel)
        model.periods = [2024]
        model.line_item_names = TestModel._line_item_names
        model._input_line_values = {}

        with pytest.raises(ValueError, match="Circular reference detected"):
            calculate_line_items(model, {}, [2024])

    def test_integration_with_proforma_model(self):
        class ReversedModel(ProformaModel):
            net_income = FormulaLine(formula=lambda li, t: li.ebitda[t] - li.tax[t])
            tax = FormulaLine(formula=lambda li, t: li.ebitda[t] * 0.21)
            ebitda = FormulaLine(formula=lambda li, t: li.revenue[t] - li.expenses[t])
            expenses = FormulaLine(formula=lambda li, t: li.revenue[t] * 0.6)
            revenue = FixedLine(values={2024: 100})

        model = ReversedModel(periods=[2024])
        assert model.get_value("net_income", 2024) == pytest.approx(31.6)


class TestFormulaLineEval:

    def test_eval_method_direct_call(self):
        profit_line = FormulaLine(formula=lambda li, t: li.revenue[t] - li.expenses[t])
        profit_line.name = "profit"

        li = LineItemValues(periods=[2024], names=["revenue", "expenses", "profit"])
        li.set("revenue", 2024, 100.0)
        li.set("expenses", 2024, 60.0)
        ns = ModelNamespace(li, {})

        result = profit_line.eval(ns, 2024)
        assert result == 40.0

    def test_eval_method_with_scalar(self):
        expenses_line = FormulaLine(formula=lambda li, t: li.revenue[t] * li.expense_ratio)
        expenses_line.name = "expenses"

        li = LineItemValues(periods=[2024], names=["revenue", "expenses"])
        li.set("revenue", 2024, 100.0)
        ns = ModelNamespace(li, {"expense_ratio": 0.65})

        result = expenses_line.eval(ns, 2024)
        assert result == 65.0

    def test_eval_method_no_formula_raises_error(self):
        profit_line = FormulaLine(formula=None)
        profit_line.name = "profit"

        li = LineItemValues(periods=[2024], names=["profit"])
        ns = ModelNamespace(li, {})

        with pytest.raises(ValueError, match="No formula defined for 'profit'"):
            profit_line.eval(ns, 2024)
