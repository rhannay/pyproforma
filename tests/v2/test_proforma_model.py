"""
Tests for ProformaModel and calculation engine.
"""

import pytest

from pyproforma.v2 import Assumption, FixedLine, FormulaLine, ProformaModel


class TestProformaModelBasic:
    """Basic tests for ProformaModel."""

    def test_model_discovery(self):
        """Test that model discovers line items and assumptions."""

        class TestModel(ProformaModel):
            tax_rate = Assumption(value=0.21)
            revenue = FixedLine(values={2024: 100})
            profit = FormulaLine(formula=lambda: revenue * 0.5)

        assert "tax_rate" in TestModel._assumption_names
        assert "revenue" in TestModel._line_item_names
        assert "profit" in TestModel._line_item_names

    def test_model_initialization_no_periods(self):
        """Test creating a model without periods."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})

        model = TestModel()
        assert model.periods == []

    def test_model_initialization_with_periods(self):
        """Test creating a model with periods."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100, 2025: 110})

        model = TestModel(periods=[2024, 2025])
        assert model.periods == [2024, 2025]

    def test_stores_line_item_names_on_instance(self):
        """Test that line item names are stored on the instance."""

        class TestModel(ProformaModel):
            tax_rate = Assumption(value=0.21)
            revenue = FixedLine(values={2024: 100})
            expenses = FormulaLine(formula=lambda a, li, t: li.revenue[t] * 0.6)
            profit = FormulaLine(formula=lambda a, li, t: li.revenue[t] - li.expenses[t])

        model = TestModel(periods=[2024])

        assert hasattr(model, "line_item_names")
        assert isinstance(model.line_item_names, list)
        assert "revenue" in model.line_item_names
        assert "expenses" in model.line_item_names
        assert "profit" in model.line_item_names
        assert len(model.line_item_names) == 3

    def test_stores_assumption_names_on_instance(self):
        """Test that assumption names are stored on the instance."""

        class TestModel(ProformaModel):
            tax_rate = Assumption(value=0.21)
            growth_rate = Assumption(value=0.1)
            revenue = FixedLine(values={2024: 100})

        model = TestModel(periods=[2024])

        assert hasattr(model, "assumption_names")
        assert isinstance(model.assumption_names, list)
        assert "tax_rate" in model.assumption_names
        assert "growth_rate" in model.assumption_names
        assert len(model.assumption_names) == 2


class TestAssumptionCalculation:
    """Tests for assumption value calculation."""

    def test_single_assumption(self):
        """Test that a single assumption is correctly loaded."""

        class TestModel(ProformaModel):
            tax_rate = Assumption(value=0.21)

        model = TestModel(periods=[2024])
        assert model.av.tax_rate == 0.21

    def test_multiple_assumptions(self):
        """Test that multiple assumptions are correctly loaded."""

        class TestModel(ProformaModel):
            tax_rate = Assumption(value=0.21)
            growth_rate = Assumption(value=0.1)

        model = TestModel(periods=[2024])
        assert model.av.tax_rate == 0.21
        assert model.av.growth_rate == 0.1


class TestFixedLineCalculation:
    """Tests for FixedLine calculation."""

    def test_single_period(self):
        """Test FixedLine with a single period."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})

        model = TestModel(periods=[2024])
        assert model.li.get("revenue", 2024) == 100

    def test_multiple_periods(self):
        """Test FixedLine with multiple periods."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100, 2025: 110, 2026: 121})

        model = TestModel(periods=[2024, 2025, 2026])
        assert model.li.get("revenue", 2024) == 100
        assert model.li.get("revenue", 2025) == 110
        assert model.li.get("revenue", 2026) == 121

    def test_missing_value_raises_error(self):
        """Test that missing value for a period raises an error."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})

        with pytest.raises(ValueError, match="No value defined"):
            TestModel(periods=[2024, 2025])


class TestFormulaLineCalculation:
    """Tests for FormulaLine calculation."""

    def test_simple_formula(self):
        """Test a simple formula referencing a FixedLine."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})
            expenses = FormulaLine(formula=lambda a, li, t: li.revenue[t] * 0.6)

        model = TestModel(periods=[2024])
        assert model.li.get("expenses", 2024) == 60.0

    def test_formula_with_assumption(self):
        """Test formula using an assumption."""

        class TestModel(ProformaModel):
            expense_ratio = Assumption(value=0.6)
            revenue = FixedLine(values={2024: 100})
            expenses = FormulaLine(formula=lambda a, li, t: li.revenue[t] * a.expense_ratio)

        model = TestModel(periods=[2024])
        assert model.li.get("expenses", 2024) == 60.0

    def test_formula_referencing_formula(self):
        """Test formula referencing another formula line."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})
            expenses = FormulaLine(formula=lambda a, li, t: li.revenue[t] * 0.6)
            profit = FormulaLine(formula=lambda a, li, t: li.revenue[t] - li.expenses[t])

        model = TestModel(periods=[2024])
        assert model.li.get("revenue", 2024) == 100
        assert model.li.get("expenses", 2024) == 60.0
        assert model.li.get("profit", 2024) == 40.0

    def test_formula_with_override(self):
        """Test formula with value override."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100, 2025: 110})
            expenses = FormulaLine(
                formula=lambda a, li, t: li.revenue[t] * 0.6, 
                values={2024: 50}  # Override 2024
            )

        model = TestModel(periods=[2024, 2025])
        assert model.li.get("expenses", 2024) == 50  # Override value
        assert model.li.get("expenses", 2025) == 66.0  # Calculated value

    def test_multiple_periods(self):
        """Test formula calculation across multiple periods."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100, 2025: 110, 2026: 121})
            expenses = FormulaLine(formula=lambda a, li, t: li.revenue[t] * 0.6)
            profit = FormulaLine(formula=lambda a, li, t: li.revenue[t] - li.expenses[t])

        model = TestModel(periods=[2024, 2025, 2026])
        assert model.li.get("profit", 2024) == 40.0
        assert model.li.get("profit", 2025) == 44.0
        assert abs(model.li.get("profit", 2026) - 48.4) < 0.0001


class TestComplexModel:
    """Tests for more complex model scenarios."""

    def test_example_model(self):
        """Test the example model from simple_model.py."""

        class SimpleFinancialModel(ProformaModel):
            expense_ratio = Assumption(value=0.6, label="Expense Ratio")
            revenue = FixedLine(
                values={2024: 100000, 2025: 110000, 2026: 121000},
                label="Revenue",
            )
            expenses = FormulaLine(
                formula=lambda a, li, t: li.revenue[t] * a.expense_ratio,
                label="Operating Expenses",
            )
            profit = FormulaLine(
                formula=lambda a, li, t: li.revenue[t] - li.expenses[t],
                label="Net Profit",
            )

        model = SimpleFinancialModel(periods=[2024, 2025, 2026])

        # Check assumptions
        assert model.av.expense_ratio == 0.6

        # Check revenue
        assert model.li.get("revenue", 2024) == 100000
        assert model.li.get("revenue", 2025) == 110000
        assert model.li.get("revenue", 2026) == 121000

        # Check expenses
        assert model.li.get("expenses", 2024) == 60000.0
        assert model.li.get("expenses", 2025) == 66000.0
        assert model.li.get("expenses", 2026) == 72600.0

        # Check profit
        assert model.li.get("profit", 2024) == 40000.0
        assert model.li.get("profit", 2025) == 44000.0
        assert model.li.get("profit", 2026) == 48400.0
