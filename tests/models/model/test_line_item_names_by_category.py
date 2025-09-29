"""Tests for Model.line_item_names_by_category method."""

import pytest

from pyproforma import Category, LineItem, Model


class TestLineItemNamesByCategory:
    """Test suite for the line_item_names_by_category method."""

    @pytest.fixture
    def basic_model(self) -> Model:
        """Create a basic model with multiple categories and line items."""
        line_items = [
            LineItem(
                name="revenue_sales",
                label="Sales Revenue",
                category="revenue",
                values={2023: 100.0, 2024: 110.0, 2025: 120.0},
            ),
            LineItem(
                name="revenue_other",
                label="Other Revenue",
                category="revenue",
                values={2023: 10.0, 2024: 12.0, 2025: 15.0},
            ),
            LineItem(
                name="cost_materials",
                label="Materials Cost",
                category="costs",
                values={2023: 40.0, 2024: 45.0, 2025: 50.0},
            ),
            LineItem(
                name="cost_labor",
                label="Labor Cost",
                category="costs",
                values={2023: 30.0, 2024: 33.0, 2025: 36.0},
            ),
            LineItem(
                name="expense_admin",
                label="Admin Expenses",
                category="expenses",
                values={2023: 20.0, 2024: 22.0, 2025: 24.0},
            ),
        ]

        categories = [
            Category(name="revenue", label="Revenue"),
            Category(name="costs", label="Costs"),
            Category(name="expenses", label="Expenses"),
        ]

        return Model(
            line_items=line_items, categories=categories, years=[2023, 2024, 2025]
        )

    @pytest.fixture
    def model_with_empty_category(self) -> Model:
        """Create a model where one category has no line items."""
        line_items = [
            LineItem(
                name="revenue_sales",
                label="Sales Revenue",
                category="revenue",
                values={2023: 100.0},
            ),
            LineItem(
                name="cost_materials",
                label="Materials Cost",
                category="costs",
                values={2023: 40.0},
            ),
        ]

        categories = [
            Category(name="revenue", label="Revenue"),
            Category(name="costs", label="Costs"),
            Category(name="empty_category", label="Empty Category"),
        ]

        return Model(line_items=line_items, categories=categories, years=[2023])

    def test_with_specific_category_returns_list(self, basic_model):
        """Test that specifying a category returns a list of line item names."""
        result = basic_model.line_item_names_by_category("revenue")

        assert isinstance(result, list)
        assert set(result) == {"revenue_sales", "revenue_other"}
        assert len(result) == 2

    def test_with_different_categories(self, basic_model):
        """Test that different categories return different line items."""
        revenue_items = basic_model.line_item_names_by_category("revenue")
        cost_items = basic_model.line_item_names_by_category("costs")
        expense_items = basic_model.line_item_names_by_category("expenses")

        assert set(revenue_items) == {"revenue_sales", "revenue_other"}
        assert set(cost_items) == {"cost_materials", "cost_labor"}
        assert set(expense_items) == {"expense_admin"}

        # Ensure no overlap between categories
        assert not set(revenue_items) & set(cost_items)
        assert not set(cost_items) & set(expense_items)
        assert not set(revenue_items) & set(expense_items)

    def test_with_nonexistent_category_raises_error(self, basic_model):
        """Test that requesting a non-existent category raises KeyError."""
        with pytest.raises(KeyError) as exc_info:
            basic_model.line_item_names_by_category("nonexistent")

        assert "Category 'nonexistent' not found" in str(exc_info.value)
        assert "Available categories:" in str(exc_info.value)

    def test_with_none_returns_dict(self, basic_model):
        """Test that passing None returns a dictionary of all categories."""
        result = basic_model.line_item_names_by_category(None)

        assert isinstance(result, dict)
        expected_categories = {"revenue", "costs", "expenses", "category_totals"}
        assert set(result.keys()) == expected_categories

        assert set(result["revenue"]) == {"revenue_sales", "revenue_other"}
        assert set(result["costs"]) == {"cost_materials", "cost_labor"}
        assert set(result["expenses"]) == {"expense_admin"}
        # category_totals contains the total line items for each category
        expected_totals = {"total_revenue", "total_costs", "total_expenses"}
        assert set(result["category_totals"]) == expected_totals

    def test_with_default_none_returns_dict(self, basic_model):
        """Test that calling without arguments returns a dictionary."""
        result = basic_model.line_item_names_by_category()

        assert isinstance(result, dict)
        expected_categories = {"revenue", "costs", "expenses", "category_totals"}
        assert set(result.keys()) == expected_categories

    def test_empty_category_included_in_dict(self, model_with_empty_category):
        """Test that categories with no line items are included in the dictionary."""
        result = model_with_empty_category.line_item_names_by_category(None)

        assert isinstance(result, dict)
        assert "empty_category" in result
        assert result["empty_category"] == []

    def test_empty_category_with_specific_name(self, model_with_empty_category):
        """Test that requesting an empty category returns an empty list."""
        result = model_with_empty_category.line_item_names_by_category("empty_category")

        assert isinstance(result, list)
        assert result == []

    def test_return_type_consistency(self, basic_model):
        """Test that return types are consistent and correct."""
        # With specific category, should always return list
        for category in basic_model.category_names:
            result = basic_model.line_item_names_by_category(category)
            assert isinstance(result, list)
            assert all(isinstance(name, str) for name in result)

        # With None, should always return dict
        result_dict = basic_model.line_item_names_by_category(None)
        assert isinstance(result_dict, dict)
        assert all(isinstance(key, str) for key in result_dict.keys())
        assert all(isinstance(value, list) for value in result_dict.values())
        assert all(
            isinstance(name, str)
            for value_list in result_dict.values()
            for name in value_list
        )

    def test_ordering_consistency(self, basic_model):
        """Test that the ordering of results is consistent."""
        # Get results multiple times to check consistency
        result1 = basic_model.line_item_names_by_category("revenue")
        result2 = basic_model.line_item_names_by_category("revenue")

        assert result1 == result2  # Should be identical

        # Dict results should also be consistent
        dict1 = basic_model.line_item_names_by_category(None)
        dict2 = basic_model.line_item_names_by_category(None)

        assert dict1 == dict2

    def test_all_line_items_accounted_for(self, basic_model):
        """Test that all line items appear in exactly one category."""
        result_dict = basic_model.line_item_names_by_category(None)

        # Collect all line items from all categories
        all_items_from_dict = []
        for category_items in result_dict.values():
            all_items_from_dict.extend(category_items)

        # Get actual line item names from the model definitions
        actual_line_items = [item.name for item in basic_model._line_item_definitions]

        # Each actual line item should appear exactly once
        items_from_dict_set = set(all_items_from_dict)
        actual_items_set = set(actual_line_items)
        assert items_from_dict_set & actual_items_set == actual_items_set

    def test_edge_case_single_item_single_category(self):
        """Test edge case with only one item in one category."""
        line_items = [
            LineItem(
                name="single_item",
                label="Single Item",
                category="single_category",
                values={2023: 100.0},
            )
        ]

        model = Model(line_items=line_items, years=[2023])

        # Test specific category
        result_list = model.line_item_names_by_category("single_category")
        assert result_list == ["single_item"]

        # Test dictionary result - includes category_totals
        result_dict = model.line_item_names_by_category(None)
        expected_dict = {
            "single_category": ["single_item"],
            "category_totals": ["total_single_category"],
        }
        assert result_dict == expected_dict

    def test_error_message_includes_available_categories(self, basic_model):
        """Test that error messages include helpful information."""
        with pytest.raises(KeyError) as exc_info:
            basic_model.line_item_names_by_category("invalid_category")

        error_message = str(exc_info.value)
        assert "Category 'invalid_category' not found" in error_message
        assert "Available categories:" in error_message

        # Check that all actual categories are mentioned
        for category in basic_model.category_names:
            assert category in error_message
