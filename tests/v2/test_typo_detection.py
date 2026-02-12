"""
Tests for typo detection in formula line items.

These tests verify that typos in line item names are caught immediately
with helpful error messages, rather than eventually failing with a
circular reference error.
"""

import pytest

from pyproforma.v2 import FixedLine, FormulaLine, ProformaModel


class TestTypoDetection:
    """Tests for immediate typo detection in formulas."""

    def test_typo_in_line_item_name_raises_helpful_error(self):
        """Test that a typo in a line item name raises a helpful error immediately."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})
            # Typo: reveenue instead of revenue
            expenses = FormulaLine(formula=lambda a, li, t: li.reveenue[t] * 0.6)

        with pytest.raises(ValueError, match="is not registered"):
            TestModel(periods=[2024])

    def test_typo_error_message_lists_available_names(self):
        """Test that the typo error message lists available line items."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})
            cost = FixedLine(values={2024: 60})
            # Typo: reveenue instead of revenue
            profit = FormulaLine(formula=lambda a, li, t: li.reveenue[t] - li.cost[t])

        with pytest.raises(ValueError, match="Available line items"):
            TestModel(periods=[2024])

    def test_typo_caught_before_circular_reference_error(self):
        """Test that typos are caught before hitting max iterations."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100, 2025: 110})
            # Typo that would eventually cause circular reference if not caught
            expenses = FormulaLine(formula=lambda a, li, t: li.reveneu[t] * 0.6)

        # Should raise ValueError about typo, not circular reference
        with pytest.raises(ValueError) as exc_info:
            TestModel(periods=[2024, 2025])

        # Should mention the specific error, not circular reference
        assert "is not registered" in str(exc_info.value)
        assert "Circular reference" not in str(exc_info.value)

    def test_valid_dependency_not_yet_calculated_works(self):
        """Test that valid dependencies are retried, not treated as typos."""

        class TestModel(ProformaModel):
            # Define profit before revenue to test dependency resolution
            profit = FormulaLine(formula=lambda a, li, t: li.revenue[t] - li.expenses[t])
            expenses = FormulaLine(formula=lambda a, li, t: li.revenue[t] * 0.6)
            revenue = FixedLine(values={2024: 100})

        # This should work - revenue and expenses are valid, just defined after profit
        model = TestModel(periods=[2024])
        assert model.get_value("profit", 2024) == 40.0

    def test_multiple_typos_first_one_caught(self):
        """Test that the first typo encountered is reported."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})
            # Two typos, but we should catch the first one
            bad1 = FormulaLine(formula=lambda a, li, t: li.reveenue[t] * 0.5)
            bad2 = FormulaLine(formula=lambda a, li, t: li.reveneu[t] * 0.6)

        with pytest.raises(ValueError, match="is not registered"):
            TestModel(periods=[2024])

    def test_typo_in_complex_formula(self):
        """Test typo detection in a more complex formula."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})
            expenses = FixedLine(values={2024: 60})
            # Typo in second reference
            net = FormulaLine(
                formula=lambda a, li, t: (li.revenue[t] - li.expnses[t]) * 0.9
            )

        with pytest.raises(ValueError, match="expnses.*is not registered"):
            TestModel(periods=[2024])

    def test_accessing_undefined_line_item_directly(self):
        """Test that accessing undefined line item on LineItemValues raises error."""
        from pyproforma.v2.line_item_values import LineItemValues

        li = LineItemValues(periods=[2024], names=["revenue", "expenses"])

        # Accessing registered name works (even if no values yet)
        assert li.revenue is not None

        # Accessing unregistered name raises AttributeError
        with pytest.raises(AttributeError, match="profit.*is not registered"):
            _ = li.profit
