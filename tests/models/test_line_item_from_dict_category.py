"""Test the updated LineItem.from_dict functionality for category handling."""

from pyproforma.models.line_item import LineItem


class TestLineItemFromDictCategoryHandling:
    """Test LineItem.from_dict category handling."""

    def test_missing_category_defaults_to_general(self):
        """Test that missing category key defaults to 'general'."""
        item_dict = {"name": "revenue", "formula": "1000"}
        line_item = LineItem.from_dict(item_dict)

        assert line_item.name == "revenue"
        assert line_item.category == "general"
        assert line_item.formula == "1000"

    def test_none_category_defaults_to_general(self):
        """Test that None category value defaults to 'general'."""
        item_dict = {"name": "expenses", "category": None, "formula": "800"}
        line_item = LineItem.from_dict(item_dict)

        assert line_item.name == "expenses"
        assert line_item.category == "general"
        assert line_item.formula == "800"

    def test_empty_string_category_defaults_to_general(self):
        """Test that empty string category defaults to 'general'."""
        item_dict = {"name": "profit", "category": "", "formula": "200"}
        line_item = LineItem.from_dict(item_dict)

        assert line_item.name == "profit"
        assert line_item.category == "general"
        assert line_item.formula == "200"

    def test_valid_category_is_preserved(self):
        """Test that valid category values are preserved."""
        item_dict = {"name": "income", "category": "revenue", "formula": "1200"}
        line_item = LineItem.from_dict(item_dict)

        assert line_item.name == "income"
        assert line_item.category == "revenue"
        assert line_item.formula == "1200"

    def test_whitespace_category_defaults_to_general(self):
        """Test that whitespace-only category defaults to 'general'."""
        item_dict = {"name": "misc", "category": "   ", "formula": "50"}
        line_item = LineItem.from_dict(item_dict)

        assert line_item.name == "misc"
        assert line_item.category == "general"  # Whitespace treated as falsy
        assert line_item.formula == "50"

    def test_all_fields_with_category_handling(self):
        """Test complete LineItem creation with category defaulting."""
        item_dict = {
            "name": "test_item",
            "category": None,
            "label": "Test Item",
            "values": {"2023": 100, "2024": 200},
            "formula": "base_value * 2",
            "value_format": "two_decimals",
        }

        line_item = LineItem.from_dict(item_dict)

        assert line_item.name == "test_item"
        assert line_item.category == "general"
        assert line_item.label == "Test Item"
        assert line_item.values == {2023: 100, 2024: 200}
        assert line_item.formula == "base_value * 2"
        assert line_item.value_format == "two_decimals"
