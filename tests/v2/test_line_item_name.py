"""
Tests for LineItem.name attribute set by __set_name__.

These tests verify that line items know their own names after being assigned
to a ProformaModel class.
"""

from pyproforma.v2 import FixedLine, FormulaLine, ProformaModel


class TestLineItemName:
    """Tests for the name attribute on line items."""

    def test_fixed_line_knows_its_name(self):
        """Test that FixedLine stores its attribute name."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})
            expenses = FixedLine(values={2024: 60})

        # After class creation, line items should know their names
        assert TestModel.revenue.name == "revenue"
        assert TestModel.expenses.name == "expenses"

    def test_formula_line_knows_its_name(self):
        """Test that FormulaLine stores its attribute name."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})
            profit = FormulaLine(formula=lambda a, li, t: li.revenue[t] * 0.4)

        assert TestModel.revenue.name == "revenue"
        assert TestModel.profit.name == "profit"

    def test_mixed_line_items_know_names(self):
        """Test that all line item types store their names."""

        class TestModel(ProformaModel):
            rev = FixedLine(values={2024: 100})
            cost = FixedLine(values={2024: 60})
            profit = FormulaLine(formula=lambda a, li, t: li.rev[t] - li.cost[t])
            margin = FormulaLine(formula=lambda a, li, t: li.profit[t] / li.rev[t])

        assert TestModel.rev.name == "rev"
        assert TestModel.cost.name == "cost"
        assert TestModel.profit.name == "profit"
        assert TestModel.margin.name == "margin"

    def test_name_initialized_to_none(self):
        """Test that name is None before being assigned to a class."""
        # Create a standalone line item (not assigned to a class)
        standalone = FixedLine(values={2024: 100})
        assert standalone.name is None

    def test_name_set_by_class_assignment(self):
        """Test that __set_name__ is called during class creation."""

        class TestModel(ProformaModel):
            my_line_item = FixedLine(values={2024: 100})

        # The name should match the attribute name
        assert TestModel.my_line_item.name == "my_line_item"
