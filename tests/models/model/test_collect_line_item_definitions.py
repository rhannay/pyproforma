"""Test the _collect_line_item_definitions functionality."""

import pytest

from pyproforma.models.line_item import LineItem
from pyproforma.models.model.model import Model


class TestCollectLineItemDefinitions:
    """Test the _collect_line_item_definitions method."""

    def test_none_input(self):
        """Test handling None input."""
        result = Model._collect_line_item_definitions(None)
        assert result == []

    def test_empty_list_input(self):
        """Test handling empty list input."""
        result = Model._collect_line_item_definitions([])
        assert result == []

    def test_lineitem_objects(self):
        """Test handling list of LineItem objects."""
        line_item1 = LineItem(name="revenue", formula="1000")
        line_item2 = LineItem(name="expenses", formula="revenue * 0.8")

        result = Model._collect_line_item_definitions([line_item1, line_item2])

        assert len(result) == 2
        assert result[0] is line_item1  # Should be the same object
        assert result[1] is line_item2
        assert result[0].name == "revenue"
        assert result[1].name == "expenses"

    def test_string_list(self):
        """Test handling list of strings."""
        result = Model._collect_line_item_definitions(["revenue", "expenses", "profit"])

        assert len(result) == 3
        assert all(isinstance(item, LineItem) for item in result)
        assert result[0].name == "revenue"
        assert result[1].name == "expenses"
        assert result[2].name == "profit"
        # Default values should be set
        assert all(item.category == "general" for item in result)
        assert all(item.formula is None for item in result)

    def test_dict_list(self):
        """Test handling list of dictionaries."""
        dicts = [
            {"name": "revenue", "category": "income", "formula": "1000"},
            {
                "name": "expenses",
                "category": "costs",
                "formula": "revenue * 0.8",
                "label": "Total Expenses",
            },
        ]

        result = Model._collect_line_item_definitions(dicts)

        assert len(result) == 2
        assert all(isinstance(item, LineItem) for item in result)

        # First item
        assert result[0].name == "revenue"
        assert result[0].category == "income"
        assert result[0].formula == "1000"

        # Second item
        assert result[1].name == "expenses"
        assert result[1].category == "costs"
        assert result[1].formula == "revenue * 0.8"
        assert result[1].label == "Total Expenses"

    def test_dict_without_category(self):
        """Test handling dict without category field (defaults to 'general')."""
        dicts = [
            {"name": "revenue", "formula": "1000"},
            {"name": "expenses", "formula": "revenue * 0.8"},
        ]

        result = Model._collect_line_item_definitions(dicts)

        assert len(result) == 2
        assert all(isinstance(item, LineItem) for item in result)

        # Both should have default category
        assert result[0].name == "revenue"
        assert result[0].category == "general"
        assert result[0].formula == "1000"

        assert result[1].name == "expenses"
        assert result[1].category == "general"
        assert result[1].formula == "revenue * 0.8"

    def test_dict_with_none_category(self):
        """Test handling dict with None category field (defaults to 'general')."""
        dicts = [
            {"name": "revenue", "category": None, "formula": "1000"},
            {"name": "expenses", "category": "", "formula": "revenue * 0.8"},
        ]

        result = Model._collect_line_item_definitions(dicts)

        assert len(result) == 2
        assert all(isinstance(item, LineItem) for item in result)

        # Both should have default category due to None and empty string
        assert result[0].name == "revenue"
        assert result[0].category == "general"
        assert result[0].formula == "1000"

        assert result[1].name == "expenses"
        assert result[1].category == "general"
        assert result[1].formula == "revenue * 0.8"

    def test_mixed_list(self):
        """Test handling mixed list of different types."""
        line_item = LineItem(name="revenue", formula="1000")
        dict_item = {
            "name": "expenses",
            "category": "costs",
            "formula": "revenue * 0.8",
        }
        string_item = "profit"

        result = Model._collect_line_item_definitions(
            [line_item, dict_item, string_item]
        )

        assert len(result) == 3
        assert all(isinstance(item, LineItem) for item in result)

        # First item (LineItem object)
        assert result[0] is line_item
        assert result[0].name == "revenue"
        assert result[0].formula == "1000"

        # Second item (from dict)
        assert result[1].name == "expenses"
        assert result[1].category == "costs"
        assert result[1].formula == "revenue * 0.8"

        # Third item (from string)
        assert result[2].name == "profit"
        assert result[2].category == "general"
        assert result[2].formula is None

    def test_invalid_type_raises_error(self):
        """Test that invalid types raise TypeError."""
        with pytest.raises(TypeError) as exc_info:
            Model._collect_line_item_definitions([123, "revenue"])

        expected_msg = "Line items must be LineItem objects, strings, or dictionaries"
        assert expected_msg in str(exc_info.value)
        assert "got <class 'int'> for value: 123" in str(exc_info.value)

    def test_invalid_string_name_raises_error(self):
        """Test that invalid string names raise ValueError."""
        with pytest.raises(ValueError):
            Model._collect_line_item_definitions(["invalid name with spaces"])

    def test_model_integration_with_strings(self):
        """Test integration with Model class using string list."""
        model = Model(line_items=["revenue", "expenses"], years=[2023, 2024])

        assert len(model._line_item_definitions) == 2
        assert model._line_item_definitions[0].name == "revenue"
        assert model._line_item_definitions[1].name == "expenses"
        # Note: line_item_names includes category totals
        li_names = [item.name for item in model._line_item_definitions]
        assert li_names == ["revenue", "expenses"]

    def test_model_integration_with_dicts(self):
        """Test integration with Model class using dictionary list."""
        line_items = [
            {"name": "revenue", "category": "income", "formula": "1000"},
            {"name": "expenses", "category": "costs", "formula": "revenue * 0.8"},
        ]

        model = Model(line_items=line_items, years=[2023, 2024])

        assert len(model._line_item_definitions) == 2
        assert model._line_item_definitions[0].name == "revenue"
        assert model._line_item_definitions[0].category == "income"
        assert model._line_item_definitions[0].formula == "1000"

        assert model._line_item_definitions[1].name == "expenses"
        assert model._line_item_definitions[1].category == "costs"
        assert model._line_item_definitions[1].formula == "revenue * 0.8"

        # Test that the model works correctly
        assert model.value("revenue", 2023) == 1000
        assert model.value("expenses", 2023) == 800

    def test_model_integration_mixed(self):
        """Test integration with Model class using mixed types."""
        revenue_item = LineItem(name="revenue", formula="1000")
        expense_dict = {"name": "expenses", "formula": "revenue * 0.8"}

        model = Model(
            line_items=[revenue_item, expense_dict, "profit"], years=[2023, 2024]
        )

        assert len(model._line_item_definitions) == 3
        li_names = [item.name for item in model._line_item_definitions]
        assert li_names == ["revenue", "expenses", "profit"]

        # Test that the model works correctly
        assert model.value("revenue", 2023) == 1000
        assert model.value("expenses", 2023) == 800
