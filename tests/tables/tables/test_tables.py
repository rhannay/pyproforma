import pytest

from pyproforma.models import Category, LineItem, Model


class TestTableCreation:
    @pytest.fixture
    def sample_model(self):
        """Create a sample Model with line items and formulas for testing."""
        # Create line items with initial values and formulas
        revenue_sales = LineItem(
            name="revenue_sales",
            label="Sales Revenue",
            category="revenue",
            values={2023: 1000000.0},
            formula="revenue_sales[-1] * 1.10",  # 10% growth
        )

        revenue_services = LineItem(
            name="revenue_services",
            label="Service Revenue",
            category="revenue",
            values={2023: 500000.0},
            formula="revenue_services[-1] * 1.15",  # 15% growth
        )

        cost_of_goods = LineItem(
            name="cost_of_goods",
            label="Cost of Goods Sold",
            category="expense",
            values={2023: 400000.0},
            formula="revenue_sales * 0.4",  # 40% of sales revenue
        )

        operating_expenses = LineItem(
            name="operating_expenses",
            label="Operating Expenses",
            category="expense",
            values={2023: 300000.0},
            formula="operating_expenses[-1] * 1.05",  # 5% growth
        )

        # Define categories
        categories = [
            Category(name="revenue", label="Revenue"),
            Category(name="expense", label="Expenses"),
            Category(name="calculated", label="Calculated"),
        ]

        # Define calculated formulas as LineItems
        gross_profit = LineItem(
            name="gross_profit",
            label="Gross Profit",
            category="calculated",
            formula="revenue_sales + revenue_services - cost_of_goods",
        )

        net_profit = LineItem(
            name="net_profit",
            label="Net Profit",
            category="calculated",
            formula="gross_profit - operating_expenses",
        )

        profit_margin = LineItem(
            name="profit_margin",
            label="Profit Margin %",
            category="calculated",
            formula="net_profit / (revenue_sales + revenue_services) * 100",
        )

        return Model(
            line_items=[
                revenue_sales,
                revenue_services,
                cost_of_goods,
                operating_expenses,
                gross_profit,
                net_profit,
                profit_margin,
            ],
            categories=categories,
            years=[2023, 2024, 2025, 2026],
        )

    def test_table_creation(self, sample_model: Model):
        table = sample_model.tables.line_items()
        assert table is not None, "Line items table creation failed"

    def test_line_items_with_filter(self, sample_model: Model):
        """Test that line_items() can filter by line_items."""
        # Test with specific line items from different categories
        table = sample_model.tables.line_items(
            line_items=["revenue_sales", "cost_of_goods"]
        )
        assert table is not None, "Filtered line items table creation failed"

        # Count the actual item rows (excluding label rows)
        # Note: With new API defaults (include_name=True), we now get names instead of labels
        item_row_count = sum(
            1
            for row in table.rows
            if hasattr(row, "cells")
            and len(row.cells) > 0
            and row.cells[0].value in ["revenue_sales", "cost_of_goods"]
        )
        assert item_row_count == 2, f"Should have 2 item rows, got {item_row_count}"

        # Verify the right items are in the table
        names_in_table = [
            row.cells[0].value
            for row in table.rows
            if hasattr(row, "cells")
            and len(row.cells) > 0
            and row.cells[0].value in ["revenue_sales", "cost_of_goods"]
        ]
        assert "revenue_sales" in names_in_table
        assert "cost_of_goods" in names_in_table

    def test_line_items_with_empty_filter(self, sample_model: Model):
        """Test that empty line_items list returns empty table."""
        table = sample_model.tables.line_items(line_items=[])
        assert table is not None
        # Should have no rows (no categories shown because no items)
        assert len(table.rows) == 0, "Empty filter should result in empty table"

    def test_line_items_with_none_filter(self, sample_model: Model):
        """Test that None line_items includes all items (default behavior)."""
        table_with_none = sample_model.tables.line_items(line_items=None)
        table_without_arg = sample_model.tables.line_items()

        # Both should have the same number of rows
        assert len(table_with_none.rows) == len(table_without_arg.rows), (
            "None filter should behave same as no argument"
        )

    def test_line_items_filter_nonexistent_items(self, sample_model: Model):
        """Test filtering with non-existent line item names."""
        # Filter with items that don't exist - should return empty table
        table = sample_model.tables.line_items(
            line_items=["nonexistent_item_1", "nonexistent_item_2"]
        )
        assert table is not None
        assert len(table.rows) == 0, "Non-existent items should result in empty table"

    def test_line_items_filter_preserves_category_order(self, sample_model: Model):
        """Test that filtered items maintain category order."""
        # Get items from multiple categories in model order
        table = sample_model.tables.line_items(
            line_items=["revenue_sales", "operating_expenses", "net_profit"]
        )
        assert table is not None

        # Extract category labels in order
        category_labels = []
        for row in table.rows:
            if hasattr(row, "cells") and len(row.cells) > 0:
                cell_value = row.cells[0].value
                # Category labels are bold - check if this is a category row
                if cell_value in ["Revenue", "Expenses", "Calculated"]:
                    if cell_value not in category_labels:
                        category_labels.append(cell_value)

        # Categories should appear in the order defined in the model
        expected_order = ["Revenue", "Expenses", "Calculated"]
        actual_order = [cat for cat in expected_order if cat in category_labels]
        assert category_labels == actual_order, (
            f"Categories should maintain model order. "
            f"Expected {actual_order}, got {category_labels}"
        )

    def test_line_items_with_percent_change(self, sample_model: Model):
        """Test that line_items() includes percent change rows when requested."""
        # Test with include_percent_change=True
        table = sample_model.tables.line_items(
            include_percent_change=True,
            line_items=["revenue_sales", "cost_of_goods"],
        )
        assert table is not None, "Line items table with percent change creation failed"

        # Should have 4 rows total: 2 items + 2 percent change rows
        assert len(table.rows) == 4, (
            f"Should have 4 rows (2 items + 2 percent change), got {len(table.rows)}"
        )

        # Check that we have the correct pattern: Item -> PercentChange -> Item
        row_labels = [
            row.cells[0].value
            for row in table.rows
            if hasattr(row, "cells") and len(row.cells) > 0
        ]

        # Should have alternating pattern of item names and percent change labels
        # Note: With new API defaults (include_name=True), we now get names instead of labels
        expected_pattern = [
            "revenue_sales",
            "Sales Revenue % Change",
            "cost_of_goods",
            "Cost of Goods Sold % Change",
        ]
        assert row_labels == expected_pattern, (
            f"Row labels should follow item/percent change pattern. "
            f"Expected {expected_pattern}, got {row_labels}"
        )

    def test_line_items_without_percent_change(self, sample_model: Model):
        """Test that line_items() does not include percent change rows by default."""
        # Test with include_percent_change=False (default)
        table = sample_model.tables.line_items(
            line_items=["revenue_sales", "cost_of_goods"]
        )
        assert table is not None, "Line items table creation failed"

        # Should have only 2 rows: 2 items
        assert len(table.rows) == 2, (
            f"Should have 2 rows (items only), got {len(table.rows)}"
        )

        # Check that we only have item names (new default is include_name=True)
        row_labels = [
            row.cells[0].value
            for row in table.rows
            if hasattr(row, "cells") and len(row.cells) > 0
        ]

        expected_labels = ["revenue_sales", "cost_of_goods"]
        assert row_labels == expected_labels, (
            f"Row labels should only be item names. "
            f"Expected {expected_labels}, got {row_labels}"
        )


class TestTableLineItemsWithTotals:
    """Test Tables.line_items() with include_totals=True and multiple columns."""

    @pytest.fixture
    def totals_model(self):
        """Create a model for testing totals functionality."""
        line_items = [
            LineItem(
                name="a", label="Item A", category="cat1", values={2023: 100, 2024: 110}
            ),
            LineItem(
                name="b", label="Item B", category="cat1", values={2023: 200, 2024: 220}
            ),
            LineItem(
                name="c", label="Item C", category="cat2", values={2023: 300, 2024: 330}
            ),
        ]
        categories = [
            Category(name="cat1", label="Category 1"),
            Category(name="cat2", label="Category 2"),
        ]
        return Model(line_items=line_items, years=[2023, 2024], categories=categories)

    def test_totals_with_single_column(self, totals_model):
        """Test include_totals=True with single column."""
        table = totals_model.tables.line_items(
            include_name=False, include_label=True, include_totals=True
        )

        # Should have 4 rows: 3 items + 1 total
        assert len(table.rows) == 4
        # Should have 3 columns: 1 label + 2 years
        assert len(table.columns) == 3

        # All rows should have same number of cells
        for row in table.rows:
            assert len(row.cells) == 3

        # Check totals row
        totals_row = table.rows[-1]
        assert totals_row.cells[0].value == "Total"
        assert totals_row.cells[1].value == 600  # 100+200+300
        assert totals_row.cells[2].value == 660  # 110+220+330

    def test_totals_with_two_columns(self, totals_model):
        """Test include_totals=True with two columns."""
        table = totals_model.tables.line_items(
            include_name=True, include_label=True, include_totals=True
        )

        # Should have 4 rows: 3 items + 1 total
        assert len(table.rows) == 4
        # Should have 4 columns: 2 labels + 2 years
        assert len(table.columns) == 4

        # All rows should have same number of cells
        for row in table.rows:
            assert len(row.cells) == 4

        # Check totals row
        totals_row = table.rows[-1]
        assert totals_row.cells[0].value == "Total"
        assert totals_row.cells[1].value == ""
        assert totals_row.cells[2].value == 600
        assert totals_row.cells[3].value == 660

    def test_totals_with_three_columns(self, totals_model):
        """Test include_totals=True with three columns."""
        table = totals_model.tables.line_items(
            include_name=True,
            include_label=True,
            include_category=True,
            include_totals=True,
        )

        # Should have 4 rows: 3 items + 1 total
        assert len(table.rows) == 4
        # Should have 5 columns: 3 labels + 2 years
        assert len(table.columns) == 5

        # All rows should have same number of cells
        for row in table.rows:
            assert len(row.cells) == 5

        # Check totals row
        totals_row = table.rows[-1]
        assert totals_row.cells[0].value == "Total"  # total name
        assert totals_row.cells[1].value == ""  # empty label
        assert totals_row.cells[2].value == ""  # empty category
        assert totals_row.cells[3].value == 600
        assert totals_row.cells[4].value == 660

    def test_totals_with_filtered_items(self, totals_model):
        """Test include_totals=True with filtered items."""
        table = totals_model.tables.line_items(
            line_items=["a", "c"],
            include_name=True,
            include_label=True,
            include_totals=True,
        )

        # Should have 3 rows: 2 filtered items + 1 total
        assert len(table.rows) == 3

        # Check totals are only for filtered items
        totals_row = table.rows[-1]
        assert totals_row.cells[2].value == 400  # 100+300
        assert totals_row.cells[3].value == 440  # 110+330


class TestTablePercentChangeWithMultipleColumns:
    """Test Tables.line_items() with include_percent_change and multiple label columns."""

    @pytest.fixture
    def simple_model(self):
        """Create a simple model for testing percent change with multiple columns."""
        line_items = [
            LineItem(
                name="revenue",
                label="Revenue",
                category="income",
                values={2020: 1000, 2021: 1100, 2022: 1210},
            ),
            LineItem(
                name="expenses",
                label="Expenses",
                category="costs",
                values={2020: 800, 2021: 850, 2022: 900},
            ),
        ]
        categories = [
            Category(name="income", label="Income"),
            Category(name="costs", label="Costs"),
        ]
        return Model(
            line_items=line_items, years=[2020, 2021, 2022], categories=categories
        )

    def test_percent_change_with_label_only(self, simple_model):
        """Test percent change with include_label=True (the bug scenario)."""
        # This was the failing case from the bug report
        table = simple_model.tables.line_items(
            include_label=True, include_percent_change=True
        )
        assert table is not None, "Table creation failed"

        # Should have 4 rows: 2 items + 2 percent change rows
        assert len(table.rows) == 4, f"Should have 4 rows, got {len(table.rows)}"

        # All rows should have the same number of cells (2 label columns + 3 year columns)
        expected_cell_count = 5  # name + label + 3 years
        for i, row in enumerate(table.rows):
            assert len(row.cells) == expected_cell_count, (
                f"Row {i} has {len(row.cells)} cells, expected {expected_cell_count}"
            )

    def test_percent_change_with_name_and_label(self, simple_model):
        """Test percent change with both include_name and include_label."""
        table = simple_model.tables.line_items(
            include_name=True, include_label=True, include_percent_change=True
        )
        assert table is not None

        # Should have 4 rows: 2 items + 2 percent change rows
        assert len(table.rows) == 4

        # All rows should have same number of cells (2 label columns + 3 year columns)
        expected_cell_count = 5
        for i, row in enumerate(table.rows):
            assert len(row.cells) == expected_cell_count, (
                f"Row {i} has {len(row.cells)} cells, expected {expected_cell_count}"
            )

    def test_percent_change_with_three_columns(self, simple_model):
        """Test percent change with name, label, and category columns."""
        table = simple_model.tables.line_items(
            include_name=True,
            include_label=True,
            include_category=True,
            include_percent_change=True,
        )
        assert table is not None

        # Should have 4 rows: 2 items + 2 percent change rows
        assert len(table.rows) == 4

        # All rows should have same number of cells (3 label columns + 3 year columns)
        expected_cell_count = 6
        for i, row in enumerate(table.rows):
            assert len(row.cells) == expected_cell_count, (
                f"Row {i} has {len(row.cells)} cells, expected {expected_cell_count}"
            )

    def test_percent_change_with_col_order(self, simple_model):
        """Test percent change with custom col_order."""
        table = simple_model.tables.line_items(
            col_order=["label", "category"], include_percent_change=True
        )
        assert table is not None

        # Should have 4 rows: 2 items + 2 percent change rows
        assert len(table.rows) == 4

        # All rows should have same number of cells (2 label columns + 3 year columns)
        expected_cell_count = 5
        for i, row in enumerate(table.rows):
            assert len(row.cells) == expected_cell_count, (
                f"Row {i} has {len(row.cells)} cells, expected {expected_cell_count}"
            )

    def test_percent_change_values_correctness(self, simple_model):
        """Test that percent change values are calculated correctly with multiple columns."""
        table = simple_model.tables.line_items(
            include_label=True,
            include_percent_change=True,
            line_items=["revenue"],
        )

        # Get the percent change row (should be row 1)
        percent_change_row = table.rows[1]

        # Verify we have the expected number of cells (2 label cols + 3 year cols)
        assert len(percent_change_row.cells) == 5, (
            f"Expected 5 cells (2 label cols + 3 year cols), got {len(percent_change_row.cells)}"
        )

        # Check the label is in the first cell (for percent change rows,
        # the label goes in the first cell, remaining label columns are empty)
        assert percent_change_row.cells[0].value == "Revenue % Change"

        # Check that percent change values are correct
        # Cells 0-1 are label columns, cells 2-4 are year values (2020, 2021, 2022)
        # Year 2020: None (first year)
        # Year 2021: (1100 - 1000) / 1000 = 0.10
        # Year 2022: (1210 - 1100) / 1100 = 0.10
        assert percent_change_row.cells[2].value is None  # 2020 (first year)
        assert abs(percent_change_row.cells[3].value - 0.10) < 0.001  # 2021
        assert abs(percent_change_row.cells[4].value - 0.10) < 0.001  # 2022

    def test_percent_change_with_group_by_category(self, simple_model):
        """Test percent change with group_by_category=True."""
        table = simple_model.tables.line_items(
            include_label=True, include_percent_change=True, group_by_category=True
        )
        assert table is not None

        # Should have 6 rows: 2 category labels + 2 items + 2 percent change rows
        assert len(table.rows) == 6, f"Should have 6 rows, got {len(table.rows)}"

        # All rows should have same number of cells
        expected_cell_count = 5
        for i, row in enumerate(table.rows):
            assert len(row.cells) == expected_cell_count, (
                f"Row {i} has {len(row.cells)} cells, expected {expected_cell_count}"
            )

    def test_percent_change_with_totals(self, simple_model):
        """Test percent change with include_totals=True."""
        table = simple_model.tables.line_items(
            include_label=True,
            include_percent_change=True,
            include_totals=True,
        )
        assert table is not None

        # Should have 5 rows: 2 items + 2 percent change rows + 1 total row
        assert len(table.rows) == 5, f"Should have 5 rows, got {len(table.rows)}"

        # All rows should have same number of cells
        expected_cell_count = 5
        for i, row in enumerate(table.rows):
            assert len(row.cells) == expected_cell_count, (
                f"Row {i} has {len(row.cells)} cells, expected {expected_cell_count}"
            )
