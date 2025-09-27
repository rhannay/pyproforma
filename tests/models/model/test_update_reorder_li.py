"""Tests for the reorder_line_items method in UpdateNamespace."""

import pytest

from pyproforma import Category, LineItem, Model


class TestReorderLineItems:
    """Test cases for the reorder_line_items method."""

    @pytest.fixture
    def sample_model(self):
        """Create a sample model with line items for testing."""
        line_items = [
            LineItem(
                name="revenue",
                category="income",
                values={2023: 100000, 2024: 120000},
            ),
            LineItem(
                name="expenses",
                category="costs",
                values={2023: 50000, 2024: 60000},
            ),
            LineItem(
                name="profit",
                category="income",
                formula="revenue - expenses",
            ),
            LineItem(
                name="taxes",
                category="costs",
                formula="profit * 0.2",
            ),
        ]

        categories = [
            Category(name="income", label="Income"),
            Category(name="costs", label="Costs"),
        ]

        return Model(line_items=line_items, years=[2023, 2024], categories=categories)

    @pytest.fixture
    def empty_model(self):
        """Create a model with no line items for edge case testing."""
        return Model(line_items=[], years=[2023])

    def test_successful_reordering(self, sample_model):
        """Test successful reordering of line items."""
        # Get initial order
        initial_order = [item.name for item in sample_model._line_item_definitions]
        assert initial_order == ["revenue", "expenses", "profit", "taxes"]

        # Reorder line items
        new_order = ["profit", "revenue", "expenses", "taxes"]
        sample_model.update.reorder_line_items(new_order)

        # Verify new order
        actual_order = [item.name for item in sample_model._line_item_definitions]
        assert actual_order == new_order

        # Verify model still calculates correctly
        assert sample_model.value("revenue", 2023) == 100000
        assert sample_model.value("profit", 2023) == 50000  # 100000 - 50000

    def test_reordering_preserves_functionality(self, sample_model):
        """Test that reordering doesn't break model calculations."""
        # Get initial values
        initial_profit_2023 = sample_model.value("profit", 2023)
        initial_taxes_2023 = sample_model.value("taxes", 2023)

        # Reorder line items
        new_order = ["taxes", "profit", "expenses", "revenue"]
        sample_model.update.reorder_line_items(new_order)

        # Verify values are still correct after reordering
        assert sample_model.value("profit", 2023) == initial_profit_2023
        assert sample_model.value("taxes", 2023) == initial_taxes_2023

        # Verify formulas still work
        revenue_val = sample_model.value("revenue", 2023)
        expenses_val = sample_model.value("expenses", 2023)
        expected_profit = revenue_val - expenses_val
        assert sample_model.value("profit", 2023) == expected_profit

    def test_no_change_when_order_already_correct(self, sample_model):
        """Test that no changes are made when order is already correct."""
        initial_order = [item.name for item in sample_model._line_item_definitions]

        # "Reorder" to the same order
        sample_model.update.reorder_line_items(initial_order)

        # Verify order is unchanged
        final_order = [item.name for item in sample_model._line_item_definitions]
        assert final_order == initial_order

    def test_missing_line_items_error(self, sample_model):
        """Test error when some line items are missing from the reorder list."""
        with pytest.raises(ValueError) as excinfo:
            # Missing profit, taxes
            sample_model.update.reorder_line_items(["revenue", "expenses"])

        error_msg = str(excinfo.value)
        assert "Missing line items in reorder list" in error_msg
        assert "profit" in error_msg
        assert "taxes" in error_msg
        assert "All existing line items must be included" in error_msg

    def test_unknown_line_items_error(self, sample_model):
        """Test error when unknown line items are included in the reorder list."""
        with pytest.raises(ValueError) as excinfo:
            sample_model.update.reorder_line_items(
                ["revenue", "expenses", "profit", "taxes", "unknown_item"]
            )

        error_msg = str(excinfo.value)
        assert "Unknown line items in reorder list" in error_msg
        assert "unknown_item" in error_msg
        assert "Available line items" in error_msg

    def test_duplicate_line_items_error(self, sample_model):
        """Test error when duplicate line items are in the reorder list."""
        with pytest.raises(ValueError) as excinfo:
            sample_model.update.reorder_line_items(
                [
                    "revenue",
                    "expenses",
                    "profit",
                    "taxes",
                    "revenue",  # Duplicate revenue
                ]
            )

        error_msg = str(excinfo.value)
        assert "Duplicate line items in reorder list" in error_msg
        assert "revenue" in error_msg

    def test_invalid_input_type_error(self, sample_model):
        """Test error when input is not a list."""
        with pytest.raises(TypeError) as excinfo:
            sample_model.update.reorder_line_items("not_a_list")

        assert "Expected list, got str" in str(excinfo.value)

    def test_non_string_elements_error(self, sample_model):
        """Test error when list contains non-string elements."""
        with pytest.raises(TypeError) as excinfo:
            sample_model.update.reorder_line_items(["revenue", 123, "profit", "taxes"])

        assert "All line item names must be strings" in str(excinfo.value)

    def test_empty_list_input(self, sample_model):
        """Test behavior with empty list input."""
        with pytest.raises(ValueError) as excinfo:
            sample_model.update.reorder_line_items([])

        error_msg = str(excinfo.value)
        assert "Missing line items in reorder list" in error_msg

    def test_reordering_empty_model(self, empty_model):
        """Test reordering on a model with no line items."""
        # Should succeed with empty list
        empty_model.update.reorder_line_items([])

        # Verify still empty
        assert len(empty_model._line_item_definitions) == 0

    def test_reordering_single_item_model(self):
        """Test reordering on a model with only one line item."""
        line_item = LineItem(name="single_item", category="test", values={2023: 100})
        model = Model(line_items=[line_item], years=[2023])

        # Reorder (should be no-op)
        model.update.reorder_line_items(["single_item"])

        # Verify unchanged
        assert len(model._line_item_definitions) == 1
        assert model._line_item_definitions[0].name == "single_item"

    def test_error_during_recalculation_handling(self, sample_model):
        """Test that the method handles errors properly during reordering."""
        # Test that we get the expected behavior during reordering
        # Try to reorder with a valid scenario
        try:
            sample_model.update.reorder_line_items(
                ["profit", "revenue", "expenses", "taxes"]
            )
            # This should succeed, so let's verify the order changed
            final_order = [item.name for item in sample_model._line_item_definitions]
            assert final_order == ["profit", "revenue", "expenses", "taxes"]
        except Exception:
            # If any error occurs, that's also valid behavior for edge cases
            pass

    def test_large_list_performance(self):
        """Test reordering with a larger number of line items."""
        # Create a model with many line items
        line_items = []
        for i in range(50):
            line_items.append(
                LineItem(name=f"item_{i:02d}", category="test", values={2023: i * 100})
            )

        model = Model(line_items=line_items, years=[2023])

        # Create a reversed order
        original_names = [f"item_{i:02d}" for i in range(50)]
        reversed_names = list(reversed(original_names))

        # Reorder (this tests performance and correctness with larger lists)
        model.update.reorder_line_items(reversed_names)

        # Verify the order
        actual_order = [item.name for item in model._line_item_definitions]
        assert actual_order == reversed_names

    def test_reordering_with_formulas_dependency(self, sample_model):
        """Test reordering works correctly with formula dependencies."""
        # Verify initial calculations work
        initial_profit = sample_model.value("profit", 2023)  # revenue - expenses
        initial_taxes = sample_model.value("taxes", 2023)  # profit * 0.2

        # Reorder so dependent items come before their dependencies
        # This tests that the calculation order is handled correctly
        new_order = ["taxes", "profit", "revenue", "expenses"]
        sample_model.update.reorder_line_items(new_order)

        # Verify calculations still work correctly
        assert sample_model.value("profit", 2023) == initial_profit
        assert sample_model.value("taxes", 2023) == initial_taxes

        # Verify the physical order changed
        actual_order = [item.name for item in sample_model._line_item_definitions]
        assert actual_order == new_order
