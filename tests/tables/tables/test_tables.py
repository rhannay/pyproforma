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

        table = sample_model.tables.category("revenue")
        assert table is not None, "Category table creation failed"

        # Test the new item() method
        table = sample_model.tables.line_item("revenue_sales", include_name=True)
        assert table is not None, "Item table creation failed"
        # Verify the table has the correct structure - it now includes change calculations  # noqa: E501
        assert len(table.rows) == 4, (
            "Item table should have 4 rows (value, % change, cumulative change, cumulative % change)"  # noqa: E501
        )  # noqa: E501
        # Verify first cell contains the item name, second contains the label
        assert table.rows[0].cells[0].value == "revenue_sales", (
            "First cell should contain item name"
        )  # noqa: E501
        assert table.rows[0].cells[1].value == "Sales Revenue", (
            "Second cell should contain item label"
        )  # noqa: E501

    def test_item_table_assumption(self):
        """Test that item table creation works for an assumption (now as line item)."""
        line_items = [
            LineItem(
                name="growth_rate",
                label="Growth Rate",
                category="assumptions",
                values={2023: 0.05, 2024: 0.10, 2026: 0.07},
            )
        ]

        categories = [Category(name="assumptions", label="Assumptions")]

        model = Model(
            line_items=line_items,
            categories=categories,
            years=[2023, 2024, 2025, 2026, 2027],
        )
        table = model.tables.line_item("growth_rate", include_name=True)
        assert table is not None, "Assumption item table creation failed"
        assert len(table.rows) == 4, (
            "Assumption item table should have 4 rows (value, % change, cumulative change, cumulative % change)"  # noqa: E501
        )  # noqa: E501
        assert table.rows[0].cells[0].value == "growth_rate", (
            "First cell should contain assumption name"
        )  # noqa: E501
        assert table.rows[0].cells[1].value == "Growth Rate", (
            "Second cell should contain assumption label"
        )  # noqa: E501
        assert table.rows[0].cells[2].value == 0.05, (
            "Third cell should contain value for 2023"
        )  # noqa: E501
        assert (
            table.rows[1].cells[2].value is None
        )  # No previous value to compare against  # noqa: E501
        assert table.rows[1].cells[3].value == 1.0  # 100% change from 0.05 to 0.10

    def test_line_items_with_filter(self, sample_model: Model):
        """Test that line_items() can filter by line_item_names."""
        # Test with specific line items from different categories
        table = sample_model.tables.line_items(
            line_item_names=["revenue_sales", "cost_of_goods"]
        )
        assert table is not None, "Filtered line items table creation failed"

        # Count the actual item rows (excluding label rows)
        item_row_count = sum(
            1
            for row in table.rows
            if hasattr(row, "cells")
            and len(row.cells) > 0
            and row.cells[0].value in ["Sales Revenue", "Cost of Goods Sold"]
        )
        assert item_row_count == 2, f"Should have 2 item rows, got {item_row_count}"

        # Verify the right items are in the table
        labels_in_table = [
            row.cells[0].value
            for row in table.rows
            if hasattr(row, "cells")
            and len(row.cells) > 0
            and row.cells[0].value in ["Sales Revenue", "Cost of Goods Sold"]
        ]
        assert "Sales Revenue" in labels_in_table
        assert "Cost of Goods Sold" in labels_in_table

    def test_line_items_with_filter_single_category(self, sample_model: Model):
        """Test filtering to items from a single category."""
        # Only revenue items
        table = sample_model.tables.line_items(
            line_item_names=["revenue_sales", "revenue_services"]
        )
        assert table is not None

        # Should have Revenue category label + 2 items
        # Count category labels
        category_labels = [
            row.cells[0].value
            for row in table.rows
            if hasattr(row, "cells")
            and len(row.cells) > 0
            and row.cells[0].value == "Revenue"
        ]
        assert len(category_labels) == 1, (
            "Should have exactly one Revenue category label"
        )

    def test_line_items_with_empty_filter(self, sample_model: Model):
        """Test that empty line_item_names list returns empty table."""
        table = sample_model.tables.line_items(line_item_names=[])
        assert table is not None
        # Should have no rows (no categories shown because no items)
        assert len(table.rows) == 0, "Empty filter should result in empty table"

    def test_line_items_with_none_filter(self, sample_model: Model):
        """Test that None line_item_names includes all items (default behavior)."""
        table_with_none = sample_model.tables.line_items(line_item_names=None)
        table_without_arg = sample_model.tables.line_items()

        # Both should have the same number of rows
        assert len(table_with_none.rows) == len(table_without_arg.rows), (
            "None filter should behave same as no argument"
        )

    def test_line_items_filter_nonexistent_items(self, sample_model: Model):
        """Test filtering with non-existent line item names."""
        # Filter with items that don't exist - should return empty table
        table = sample_model.tables.line_items(
            line_item_names=["nonexistent_item_1", "nonexistent_item_2"]
        )
        assert table is not None
        assert len(table.rows) == 0, "Non-existent items should result in empty table"

    def test_line_items_filter_preserves_category_order(self, sample_model: Model):
        """Test that filtered items maintain category order."""
        # Get items from multiple categories in model order
        table = sample_model.tables.line_items(
            line_item_names=["revenue_sales", "operating_expenses", "net_profit"]
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
            line_item_names=["revenue_sales", "cost_of_goods"],
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

        # Should have alternating pattern of item labels and percent change labels
        expected_pattern = [
            "Sales Revenue",
            "Sales Revenue % Change",
            "Cost of Goods Sold",
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
            line_item_names=["revenue_sales", "cost_of_goods"]
        )
        assert table is not None, "Line items table creation failed"

        # Should have only 2 rows: 2 items
        assert len(table.rows) == 2, (
            f"Should have 2 rows (items only), got {len(table.rows)}"
        )

        # Check that we only have item labels
        row_labels = [
            row.cells[0].value
            for row in table.rows
            if hasattr(row, "cells") and len(row.cells) > 0
        ]

        expected_labels = ["Sales Revenue", "Cost of Goods Sold"]
        assert row_labels == expected_labels, (
            f"Row labels should only be item labels. "
            f"Expected {expected_labels}, got {row_labels}"
        )
