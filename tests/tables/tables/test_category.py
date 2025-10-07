"""Tests for Tables.category method."""

import pytest

from pyproforma import Model
from pyproforma.models.line_item import LineItem


@pytest.fixture
def sample_model():
    """Create a sample model for testing category functionality."""
    model = Model(
        line_items=[
            LineItem(
                name="sales_revenue",
                label="Sales Revenue",
                category="revenue",
                values={2023: 100000, 2024: 110000, 2025: 120000},
            ),
            LineItem(
                name="other_income",
                label="Other Income",
                category="revenue",
                values={2023: 5000, 2024: 6000, 2025: 7000},
            ),
            LineItem(
                name="cost_of_goods",
                label="Cost of Goods Sold",
                category="expenses",
                values={2023: 60000, 2024: 65000, 2025: 70000},
            ),
            LineItem(
                name="operating_expenses",
                label="Operating Expenses",
                category="expenses",
                values={2023: 25000, 2024: 27000, 2025: 29000},
            ),
            LineItem(
                name="marketing_costs",
                label="Marketing Costs",
                category="expenses",
                values={2023: 8000, 2024: 9000, 2025: 10000},
            ),
        ],
        years=[2023, 2024, 2025],
        categories=["revenue", "expenses"],
    )

    return model


@pytest.fixture
def single_item_model():
    """Create a model with only one item in a category."""
    model = Model(
        line_items=[
            LineItem(
                name="sales",
                label="Sales Revenue",
                category="revenue",
                values={2023: 100, 2024: 110},
            ),
        ],
        years=[2023, 2024],
        categories=["revenue"],
    )

    return model


class TestCategoryMethod:
    """Test the Tables.category method."""

    def test_category_method_exists(self, sample_model):
        """Test that the category method exists and is callable."""
        assert hasattr(sample_model.tables, "category")
        assert callable(sample_model.tables.category)

    def test_category_basic_functionality(self, sample_model):
        """Test basic category table generation."""
        table = sample_model.tables.category("revenue")

        # Should return a Table object
        assert table is not None
        assert hasattr(table, "rows")

        # Should have rows for both revenue line items
        assert len(table.rows) >= 2  # At least 2 line items in revenue

    def test_category_with_multiple_items(self, sample_model):
        """Test category table with multiple line items."""
        table = sample_model.tables.category("expenses")

        # Should include all expense line items
        expenses_items = sample_model.line_item_names_by_category("expenses")
        assert (
            len(expenses_items) == 3
        )  # cost_of_goods, operating_expenses, marketing_costs

        # Table should have at least as many rows as there are expense items
        assert len(table.rows) >= len(expenses_items)

    def test_category_with_single_item(self, single_item_model):
        """Test category table with only one line item."""
        table = single_item_model.tables.category("revenue")

        # Should work even with just one item
        assert table is not None
        assert len(table.rows) >= 1

    def test_category_table_structure(self, sample_model):
        """Test that the category table has the expected structure."""
        table = sample_model.tables.category("revenue")

        # Check that we have the right number of columns
        # Should be: label column + one column per year
        expected_cols = 1 + len(sample_model.years)  # 1 + 3 = 4
        for row in table.rows:
            assert len(row.cells) == expected_cols

    def test_category_with_hardcoded_color(self, sample_model):
        """Test category table with hardcoded color parameter."""
        table = sample_model.tables.category("revenue", hardcoded_color="blue")

        # Should generate table successfully
        assert table is not None
        assert len(table.rows) >= 2

    def test_category_nonexistent_category(self, sample_model):
        """Test category table with a nonexistent category name."""
        # This might raise an exception or return empty table
        # depending on implementation
        try:
            table = sample_model.tables.category("nonexistent_category")
            # If it doesn't raise an exception, it should return a valid table
            assert table is not None
            # But it might have no rows or minimal rows
        except (KeyError, ValueError):
            # This is also acceptable behavior
            pass

    def test_category_table_content(self, sample_model):
        """Test that the category table contains expected content."""
        table = sample_model.tables.category("revenue")

        # Should contain values from revenue line items
        revenue_items = sample_model.line_item_names_by_category("revenue")
        assert "sales_revenue" in revenue_items
        assert "other_income" in revenue_items

        # Verify table has data (non-empty cells with actual values)
        has_numeric_data = False
        for row in table.rows:
            for cell in row.cells:
                if isinstance(cell.value, (int, float)) and cell.value != 0:
                    has_numeric_data = True
                    break
            if has_numeric_data:
                break

        assert has_numeric_data, "Table should contain numeric data from line items"

    def test_category_uses_line_items_method(self, sample_model):
        """
        Test that category method produces same result as calling line_items with
        category items.
        """
        # Get category table
        category_table = sample_model.tables.category("revenue")

        # Get line items for the category
        revenue_items = sample_model.line_item_names_by_category("revenue")

        # Get line_items table with the same items
        line_items_table = sample_model.tables.line_items(line_item_names=revenue_items)

        # Both tables should have the same structure
        assert len(category_table.rows) == len(line_items_table.rows)

        # Both should have the same number of columns
        if category_table.rows and line_items_table.rows:
            assert len(category_table.rows[0].cells) == len(
                line_items_table.rows[0].cells
            )

    def test_category_empty_category(self, sample_model):
        """Test category method with a category that has no line items."""
        # Create a model with an empty category
        model = Model(
            line_items=[
                LineItem(
                    name="sales", label="Sales", category="revenue", values={2023: 100}
                )
            ],
            years=[2023],
            categories=["revenue", "empty_category"],
        )

        # Test with empty category
        table = model.tables.category("empty_category")
        assert table is not None
        # Empty category should result in minimal table structure

    def test_category_parameter_validation(self, sample_model):
        """Test that category method validates its parameters correctly."""
        # Valid call should work
        table = sample_model.tables.category("revenue")
        assert table is not None

        # Call with hardcoded_color should work
        table = sample_model.tables.category("revenue", hardcoded_color="red")
        assert table is not None

        # Category name should be required (this should raise TypeError if missing)
        with pytest.raises(TypeError):
            sample_model.tables.category()
