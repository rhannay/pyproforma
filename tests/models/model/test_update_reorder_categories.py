"""Tests for the reorder_categories method in UpdateNamespace."""

import pytest

from pyproforma import Category, LineItem, Model


class TestReorderCategories:
    """Test cases for the reorder_categories method."""

    @pytest.fixture
    def sample_model(self):
        """Create a sample model with categories for testing."""
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
                name="assets",
                category="balance_sheet",
                values={2023: 200000, 2024: 250000},
            ),
            LineItem(
                name="notes",
                category="footnotes",
                values={2023: 0, 2024: 0},
            ),
        ]

        categories = [
            Category(name="income", label="Income"),
            Category(name="costs", label="Costs"),
            Category(name="balance_sheet", label="Balance Sheet"),
            Category(name="footnotes", label="Footnotes"),
        ]

        return Model(line_items=line_items, years=[2023, 2024], categories=categories)

    @pytest.fixture
    def empty_model(self):
        """Create a model with no categories for edge case testing."""
        return Model(line_items=[], years=[2023])

    def test_successful_reordering(self, sample_model):
        """Test reordering of categories (all items, backwards compatibility)."""
        # Get initial order
        initial_order = [cat.name for cat in sample_model._category_definitions]
        assert initial_order == ["income", "costs", "balance_sheet", "footnotes"]

        # Reorder categories - specifying all items (old behavior)
        new_order = ["balance_sheet", "income", "costs", "footnotes"]
        sample_model.update.reorder_categories(new_order)

        # Verify new order
        actual_order = [cat.name for cat in sample_model._category_definitions]
        assert actual_order == new_order

        # Verify model still calculates correctly
        assert sample_model.value("revenue", 2023) == 100000
        assert sample_model.value("assets", 2023) == 200000

    def test_reordering_preserves_functionality(self, sample_model):
        """Test that reordering doesn't break model calculations."""
        # Get initial values
        initial_revenue_2023 = sample_model.value("revenue", 2023)
        initial_assets_2023 = sample_model.value("assets", 2023)

        # Reorder categories
        new_order = ["footnotes", "balance_sheet", "costs", "income"]
        sample_model.update.reorder_categories(new_order)

        # Verify values are still correct after reordering
        assert sample_model.value("revenue", 2023) == initial_revenue_2023
        assert sample_model.value("assets", 2023) == initial_assets_2023

    def test_no_change_when_order_already_correct(self, sample_model):
        """Test that no changes are made when order is already correct."""
        initial_order = [cat.name for cat in sample_model._category_definitions]

        # "Reorder" to the same order
        sample_model.update.reorder_categories(initial_order)

        # Verify order is unchanged
        final_order = [cat.name for cat in sample_model._category_definitions]
        assert final_order == initial_order

    def test_subset_reordering_top(self, sample_model):
        """Test reordering a subset of categories (new behavior with position='top')."""
        # Get initial order
        initial_order = [cat.name for cat in sample_model._category_definitions]
        assert initial_order == ["income", "costs", "balance_sheet", "footnotes"]

        # Reorder only some items - they should go to the top
        sample_model.update.reorder_categories(["balance_sheet", "footnotes"])

        # Verify new order: balance_sheet and footnotes at top
        # income and costs maintain relative order
        actual_order = [cat.name for cat in sample_model._category_definitions]
        assert actual_order == ["balance_sheet", "footnotes", "income", "costs"]

        # Verify model still calculates correctly
        assert sample_model.value("revenue", 2023) == 100000
        assert sample_model.value("assets", 2023) == 200000

    def test_unknown_categories_error(self, sample_model):
        """Test error when unknown categories are included in the reorder list."""
        with pytest.raises(ValueError) as excinfo:
            sample_model.update.reorder_categories(
                ["income", "costs", "balance_sheet", "footnotes", "unknown_category"]
            )

        error_msg = str(excinfo.value)
        assert "Unknown categories in reorder list" in error_msg
        assert "unknown_category" in error_msg
        assert "Available categories" in error_msg

    def test_duplicate_categories_error(self, sample_model):
        """Test error when duplicate categories are in the reorder list."""
        with pytest.raises(ValueError) as excinfo:
            sample_model.update.reorder_categories(
                [
                    "income",
                    "costs",
                    "balance_sheet",
                    "footnotes",
                    "income",  # Duplicate income
                ]
            )

        error_msg = str(excinfo.value)
        assert "Duplicate categories in reorder list" in error_msg
        assert "income" in error_msg

    def test_invalid_input_type_error(self, sample_model):
        """Test error when input is not a list."""
        with pytest.raises(TypeError) as excinfo:
            sample_model.update.reorder_categories("not_a_list")

        assert "Expected list, got str" in str(excinfo.value)

    def test_non_string_elements_error(self, sample_model):
        """Test error when list contains non-string elements."""
        with pytest.raises(TypeError) as excinfo:
            sample_model.update.reorder_categories(["income", 123, "costs", "footnotes"])

        assert "All category names must be strings" in str(excinfo.value)

    def test_empty_list_input(self, sample_model):
        """Test behavior with empty list input (should be a no-op)."""
        # Get initial order
        initial_order = [cat.name for cat in sample_model._category_definitions]

        # Empty list should be a no-op
        sample_model.update.reorder_categories([])

        # Verify order is unchanged
        final_order = [cat.name for cat in sample_model._category_definitions]
        assert final_order == initial_order

    def test_reordering_empty_model(self, empty_model):
        """Test reordering on a model with no categories."""
        # Should succeed with empty list
        empty_model.update.reorder_categories([])

        # Verify still empty
        assert len(empty_model._category_definitions) == 0

    def test_reordering_single_category_model(self):
        """Test reordering on a model with only one category."""
        line_item = LineItem(name="single_item", category="test", values={2023: 100})
        model = Model(line_items=[line_item], years=[2023])

        # Reorder (should be no-op)
        model.update.reorder_categories(["test"])

        # Verify unchanged
        assert len(model._category_definitions) == 1
        assert model._category_definitions[0].name == "test"

    def test_large_list_performance(self):
        """Test reordering with a larger number of categories."""
        # Create a model with many categories
        line_items = []
        categories = []
        for i in range(20):
            cat_name = f"category_{i:02d}"
            categories.append(Category(name=cat_name, label=f"Category {i}"))
            line_items.append(
                LineItem(name=f"item_{i:02d}", category=cat_name, values={2023: i * 100})
            )

        model = Model(line_items=line_items, years=[2023], categories=categories)

        # Create a reversed order
        original_names = [f"category_{i:02d}" for i in range(20)]
        reversed_names = list(reversed(original_names))

        # Reorder (this tests performance and correctness with larger lists)
        model.update.reorder_categories(reversed_names)

        # Verify the order
        actual_order = [cat.name for cat in model._category_definitions]
        assert actual_order == reversed_names

    def test_subset_reordering_bottom(self, sample_model):
        """Test reordering a subset to the bottom."""
        # Reorder some items to the bottom
        sample_model.update.reorder_categories(
            ["income", "costs"], position="bottom"
        )

        # Verify new order
        actual_order = [cat.name for cat in sample_model._category_definitions]
        assert actual_order == ["balance_sheet", "footnotes", "income", "costs"]

    def test_subset_reordering_after(self, sample_model):
        """Test reordering a subset after a specific item."""
        # Place balance_sheet and footnotes after costs
        sample_model.update.reorder_categories(
            ["balance_sheet", "footnotes"], position="after", target="costs"
        )

        # Verify new order
        actual_order = [cat.name for cat in sample_model._category_definitions]
        assert actual_order == ["income", "costs", "balance_sheet", "footnotes"]

    def test_subset_reordering_before(self, sample_model):
        """Test reordering a subset before a specific item."""
        # Place footnotes before balance_sheet
        sample_model.update.reorder_categories(
            ["footnotes"], position="before", target="balance_sheet"
        )

        # Verify new order
        actual_order = [cat.name for cat in sample_model._category_definitions]
        assert actual_order == ["income", "costs", "footnotes", "balance_sheet"]

    def test_subset_reordering_index(self, sample_model):
        """Test reordering a subset at a specific index."""
        # Place balance_sheet at index 1
        sample_model.update.reorder_categories(["balance_sheet"], position="index", index=1)

        # Verify new order
        actual_order = [cat.name for cat in sample_model._category_definitions]
        assert actual_order == ["income", "balance_sheet", "costs", "footnotes"]

    def test_position_after_target_not_specified_error(self, sample_model):
        """Test error when target is not specified for 'after' position."""
        with pytest.raises(ValueError) as excinfo:
            sample_model.update.reorder_categories(
                ["balance_sheet"], position="after"
            )
        assert (
            "'target' parameter is required for position 'after'"
            in str(excinfo.value)
        )

    def test_position_before_target_not_specified_error(self, sample_model):
        """Test error when target is not specified for 'before' position."""
        with pytest.raises(ValueError) as excinfo:
            sample_model.update.reorder_categories(
                ["balance_sheet"], position="before"
            )
        assert (
            "'target' parameter is required for position 'before'"
            in str(excinfo.value)
        )

    def test_position_index_not_specified_error(self, sample_model):
        """Test error when index is not specified for 'index' position."""
        with pytest.raises(ValueError) as excinfo:
            sample_model.update.reorder_categories(
                ["balance_sheet"], position="index"
            )
        assert (
            "'index' parameter is required for position 'index'"
            in str(excinfo.value)
        )

    def test_invalid_position_error(self, sample_model):
        """Test error when an invalid position is provided."""
        with pytest.raises(ValueError) as excinfo:
            sample_model.update.reorder_categories(
                ["balance_sheet"], position="invalid"
            )
        assert "Invalid position 'invalid'" in str(excinfo.value)

    def test_target_not_found_error(self, sample_model):
        """Test error when target category is not found."""
        with pytest.raises(ValueError) as excinfo:
            sample_model.update.reorder_categories(
                ["balance_sheet"], position="after", target="nonexistent"
            )
        assert "Target category 'nonexistent' not found" in str(excinfo.value)

    def test_target_in_ordered_names_error(self, sample_model):
        """Test error when target is included in ordered_names."""
        with pytest.raises(ValueError) as excinfo:
            sample_model.update.reorder_categories(
                ["balance_sheet", "costs"], position="after", target="costs"
            )
        assert (
            "Target category 'costs' cannot be in the ordered_names list"
            in str(excinfo.value)
        )

    def test_index_out_of_range_error(self, sample_model):
        """Test error when index is out of range."""
        with pytest.raises(ValueError) as excinfo:
            sample_model.update.reorder_categories(
                ["balance_sheet"], position="index", index=10
            )
        assert "Index 10 out of range" in str(excinfo.value)

    def test_direct_method_on_model(self, sample_model):
        """Test that reorder_categories can be called directly on model."""
        # Call reorder_categories directly on model (not through update namespace)
        sample_model.reorder_categories(["balance_sheet", "footnotes"])

        # Verify new order
        actual_order = [cat.name for cat in sample_model._category_definitions]
        assert actual_order == ["balance_sheet", "footnotes", "income", "costs"]

    def test_multiple_reorderings(self, sample_model):
        """Test that multiple reorderings work correctly."""
        # First reordering
        sample_model.update.reorder_categories(["footnotes"], position="top")
        assert [cat.name for cat in sample_model._category_definitions] == [
            "footnotes", "income", "costs", "balance_sheet"
        ]

        # Second reordering
        sample_model.update.reorder_categories(
            ["balance_sheet"], position="after", target="footnotes"
        )
        assert [cat.name for cat in sample_model._category_definitions] == [
            "footnotes", "balance_sheet", "income", "costs"
        ]

    def test_reordering_with_category_metadata(self, sample_model):
        """Test that category metadata remains intact after reordering."""
        # Get initial metadata
        initial_metadata = sample_model.category_metadata.copy()

        # Reorder categories
        sample_model.update.reorder_categories(["footnotes", "balance_sheet", "costs", "income"])

        # Verify metadata is still correct (just in different order)
        final_metadata = sample_model.category_metadata

        # Check that all categories are still present
        initial_names = {cat["name"] for cat in initial_metadata}
        final_names = {cat["name"] for cat in final_metadata}
        assert initial_names == final_names

        # Check that labels are preserved
        for cat in initial_metadata:
            final_cat = next((c for c in final_metadata if c["name"] == cat["name"]), None)
            assert final_cat is not None
            assert final_cat["label"] == cat["label"]
