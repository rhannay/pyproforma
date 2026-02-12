"""
Tests for ProformaModel.get_value() method.

These tests verify the convenience method for accessing calculated values.
"""

import pytest

from pyproforma.v2 import FixedLine, FormulaLine, ProformaModel


class TestGetValue:
    """Tests for the get_value method."""

    def test_get_value_for_fixed_line(self):
        """Test getting value for a FixedLine."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100, 2025: 110})

        model = TestModel(periods=[2024, 2025])

        assert model.get_value("revenue", 2024) == 100
        assert model.get_value("revenue", 2025) == 110

    def test_get_value_for_formula_line(self):
        """Test getting value for a FormulaLine."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})
            expenses = FormulaLine(formula=lambda a, li, t: li.revenue[t] * 0.6)

        model = TestModel(periods=[2024])

        assert model.get_value("expenses", 2024) == 60.0

    def test_get_value_equivalent_to_li_get(self):
        """Test that get_value is equivalent to li.get."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})
            expenses = FormulaLine(formula=lambda a, li, t: li.revenue[t] * 0.6)
            profit = FormulaLine(formula=lambda a, li, t: li.revenue[t] - li.expenses[t])

        model = TestModel(periods=[2024])

        # Both approaches should give the same result
        assert model.get_value("profit", 2024) == model._li.get("profit", 2024)
        assert model.get_value("revenue", 2024) == model._li.get("revenue", 2024)
        assert model.get_value("expenses", 2024) == model._li.get("expenses", 2024)

    def test_get_value_multiple_periods(self):
        """Test getting values across multiple periods."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100, 2025: 110, 2026: 121})

        model = TestModel(periods=[2024, 2025, 2026])

        assert model.get_value("revenue", 2024) == 100
        assert model.get_value("revenue", 2025) == 110
        assert model.get_value("revenue", 2026) == 121

    def test_get_value_invalid_name_raises_error(self):
        """Test that invalid line item name raises AttributeError."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})

        model = TestModel(periods=[2024])

        with pytest.raises(AttributeError):
            model.get_value("invalid_name", 2024)

    def test_get_value_invalid_period_raises_error(self):
        """Test that invalid period raises KeyError."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})

        model = TestModel(periods=[2024])

        with pytest.raises(KeyError):
            model.get_value("revenue", 2025)
