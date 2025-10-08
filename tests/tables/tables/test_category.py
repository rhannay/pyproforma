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
        Test that category method without totals produces similar result as calling
        line_items with category items, accounting for category header.
        """
        # Get category table without totals to match line_items behavior
        category_table = sample_model.tables.category("revenue", include_totals=False)

        # Get line items for the category
        revenue_items = sample_model.line_item_names_by_category("revenue")

        # Get line_items table with the same items and group_by_category=True to match
        line_items_table = sample_model.tables.line_items(
            line_item_names=revenue_items, group_by_category=True
        )

        # Both tables should have the same structure (including category header)
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

        # Test with empty category - should handle gracefully
        with pytest.raises(
            ValueError, match="line_item_names must be a non-empty list"
        ):
            model.tables.category("empty_category")

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


class TestCategoryIncludeTotals:
    """Test the include_totals parameter for Tables.category method."""

    def test_category_with_totals_default(self, sample_model):
        """Test that category includes totals by default."""
        table = sample_model.tables.category("revenue")

        # Should have more rows than just the line items
        # (includes category header + totals)
        revenue_items = sample_model.line_item_names_by_category("revenue")
        # Expect: 1 category header + line items + 1 totals row
        expected_min_rows = 1 + len(revenue_items) + 1
        assert len(table.rows) >= expected_min_rows

        # The last row should be a totals row
        last_row = table.rows[-1]
        # Should have "Total" in the label
        assert "Total" in last_row.cells[0].value

    def test_category_with_totals_true(self, sample_model):
        """Test category with include_totals=True explicitly."""
        table = sample_model.tables.category("revenue", include_totals=True)

        # Should have more rows than just the line items
        # (includes category header + totals)
        revenue_items = sample_model.line_item_names_by_category("revenue")
        # Expect: 1 category header + line items + 1 totals row
        expected_min_rows = 1 + len(revenue_items) + 1
        assert len(table.rows) >= expected_min_rows

        # The last row should be a totals row
        last_row = table.rows[-1]
        assert "Total" in last_row.cells[0].value

    def test_category_with_totals_false(self, sample_model):
        """Test category with include_totals=False."""
        table = sample_model.tables.category("revenue", include_totals=False)

        # Should have line items + category header row (no totals)
        revenue_items = sample_model.line_item_names_by_category("revenue")
        # Expect: 1 category header + number of line items
        expected_rows = 1 + len(revenue_items)
        assert len(table.rows) == expected_rows

        # No row should have "Total" in the label
        for row in table.rows:
            assert "Total" not in row.cells[0].value

    def test_category_totals_row_styling(self, sample_model):
        """Test that the totals row has correct styling (bold and top border)."""
        table = sample_model.tables.category("revenue", include_totals=True)

        # The last row should be the totals row
        last_row = table.rows[-1]

        # Should be bold
        assert last_row.cells[0].bold is True

        # Should have a top border
        assert last_row.cells[0].top_border == "single"

    def test_category_totals_calculation(self, sample_model):
        """Test that the totals row shows correct calculated values."""
        table = sample_model.tables.category("revenue", include_totals=True)

        # Get the totals row (last row)
        totals_row = table.rows[-1]

        # Get expected totals from the model
        category_results = sample_model.category("revenue")

        # Check that totals match for each year
        for i, year in enumerate(sample_model.years):
            # Cell index is i+1 because first cell is the label
            expected_total = category_results.total(year)
            actual_total = totals_row.cells[i + 1].value

            assert actual_total == expected_total, (
                f"Year {year}: expected {expected_total}, got {actual_total}"
            )

    def test_category_totals_with_hardcoded_color(self, sample_model):
        """Test that totals work correctly with hardcoded_color parameter."""
        table = sample_model.tables.category(
            "revenue", include_totals=True, hardcoded_color="blue"
        )

        # Should have totals row (category header + line items + totals)
        revenue_items = sample_model.line_item_names_by_category("revenue")
        expected_min_rows = 1 + len(revenue_items) + 1
        assert len(table.rows) >= expected_min_rows

        # Last row should be totals
        last_row = table.rows[-1]
        assert "Total" in last_row.cells[0].value

    def test_category_totals_single_item(self, single_item_model):
        """Test totals row with a category that has only one item."""
        table = single_item_model.tables.category("revenue", include_totals=True)

        # Should have 3 rows: 1 category header + 1 line item + 1 totals
        assert len(table.rows) == 3

        # Last row should be totals
        totals_row = table.rows[-1]
        assert "Total" in totals_row.cells[0].value

        # Totals should equal the single item's values
        line_item = single_item_model.line_item("sales")
        for i, year in enumerate(single_item_model.years):
            expected_value = line_item.values.get(year, 0)
            actual_value = totals_row.cells[i + 1].value
            assert actual_value == expected_value
