"""
Test the new API for Model.tables.line_items() and Model.table() methods.

Tests verify:
1. Parameter renaming (line_item_names -> line_items)
2. New include_name, include_label, include_category parameters
3. New col_order parameter
4. New Model.table() convenience method
"""

import pytest

from pyproforma import Model
from pyproforma.models.line_item import LineItem


@pytest.fixture
def sample_model():
    """Create a sample model for testing."""
    line_items = [
        LineItem(
            name="revenue_sales",
            label="Sales Revenue",
            category="revenue",
            values={2023: 1000, 2024: 1100},
        ),
        LineItem(
            name="revenue_services",
            label="Service Revenue",
            category="revenue",
            values={2023: 500, 2024: 550},
        ),
        LineItem(
            name="cost_of_goods",
            label="Cost of Goods Sold",
            category="expenses",
            values={2023: 400, 2024: 440},
        ),
    ]
    return Model(line_items=line_items, years=[2023, 2024])


class TestNewParameterNames:
    """Test that new parameter names work correctly."""

    def test_line_items_parameter(self, sample_model):
        """Test that line_items parameter (renamed from line_item_names) works."""
        table = sample_model.tables.line_items(
            line_items=["revenue_sales", "cost_of_goods"]
        )
        assert table is not None
        assert len(table.rows) == 2

    def test_line_items_parameter_none(self, sample_model):
        """Test that line_items=None includes all items."""
        table = sample_model.tables.line_items(line_items=None)
        assert table is not None
        assert len(table.rows) == 3  # All three line items


class TestIncludeParameters:
    """Test include_name, include_label, and include_category parameters."""

    def test_include_name_true_default(self, sample_model):
        """Test that include_name=True is the default."""
        table = sample_model.tables.line_items()
        # Should show names by default
        row_values = [row.cells[0].value for row in table.rows]
        assert "revenue_sales" in row_values
        assert "revenue_services" in row_values

    def test_include_name_false(self, sample_model):
        """Test that include_name=False excludes name column."""
        table = sample_model.tables.line_items(include_name=False)
        # With no columns specified, should default to just name, but that's excluded
        # So we get no label columns (should still work with just years)
        assert table is not None
        assert len(table.rows) == 3

    def test_include_label_true(self, sample_model):
        """Test that include_label=True includes label column."""
        table = sample_model.tables.line_items(
            include_name=False, include_label=True
        )
        # Should show labels
        row_values = [row.cells[0].value for row in table.rows]
        assert "Sales Revenue" in row_values
        assert "Service Revenue" in row_values

    def test_include_name_and_label(self, sample_model):
        """Test that both name and label can be included."""
        table = sample_model.tables.line_items(
            include_name=True, include_label=True
        )
        # Should have both columns, name first
        first_row = table.rows[0]
        # First cell is name, second is label
        assert first_row.cells[0].value == "revenue_sales"
        assert first_row.cells[1].value == "Sales Revenue"

    def test_include_category_true(self, sample_model):
        """Test that include_category=True includes category column."""
        table = sample_model.tables.line_items(
            include_name=True, include_category=True
        )
        # Should have name and category columns
        first_row = table.rows[0]
        # First cell is name, second is category
        assert first_row.cells[0].value == "revenue_sales"
        assert first_row.cells[1].value == "revenue"

    def test_all_three_columns(self, sample_model):
        """Test that all three columns can be included."""
        table = sample_model.tables.line_items(
            include_name=True, include_label=True, include_category=True
        )
        # Should have 3 label columns + 2 year columns = 5 total
        first_row = table.rows[0]
        assert len(first_row.cells) == 5
        assert first_row.cells[0].value == "revenue_sales"
        assert first_row.cells[1].value == "Sales Revenue"
        assert first_row.cells[2].value == "revenue"


class TestColOrderParameter:
    """Test col_order parameter for controlling column order."""

    def test_col_order_overrides_include_flags(self, sample_model):
        """Test that col_order overrides include_* flags."""
        # Set include_name=False but specify it in col_order
        table = sample_model.tables.line_items(
            include_name=False, col_order=["name", "label"]
        )
        # col_order should win - both name and label included
        first_row = table.rows[0]
        assert first_row.cells[0].value == "revenue_sales"
        assert first_row.cells[1].value == "Sales Revenue"

    def test_col_order_label_name(self, sample_model):
        """Test col_order with label before name."""
        table = sample_model.tables.line_items(col_order=["label", "name"])
        first_row = table.rows[0]
        # Label should be first, then name
        assert first_row.cells[0].value == "Sales Revenue"
        assert first_row.cells[1].value == "revenue_sales"

    def test_col_order_single_column(self, sample_model):
        """Test col_order with single column."""
        table = sample_model.tables.line_items(col_order=["label"])
        first_row = table.rows[0]
        # Only label column
        assert len(first_row.cells) == 3  # 1 label + 2 years
        assert first_row.cells[0].value == "Sales Revenue"

    def test_col_order_all_three(self, sample_model):
        """Test col_order with all three columns in custom order."""
        table = sample_model.tables.line_items(
            col_order=["category", "label", "name"]
        )
        first_row = table.rows[0]
        assert first_row.cells[0].value == "revenue"
        assert first_row.cells[1].value == "Sales Revenue"
        assert first_row.cells[2].value == "revenue_sales"

    def test_col_order_invalid_column(self, sample_model):
        """Test that invalid column in col_order raises error."""
        with pytest.raises(ValueError, match="Invalid column 'invalid'"):
            sample_model.tables.line_items(col_order=["invalid"])


class TestModelTableMethod:
    """Test the new Model.table() convenience method."""

    def test_table_method_exists(self, sample_model):
        """Test that table() method exists on Model."""
        assert hasattr(sample_model, "table")
        assert callable(sample_model.table)

    def test_table_basic_usage(self, sample_model):
        """Test basic usage of Model.table()."""
        table = sample_model.table()
        assert table is not None
        assert len(table.rows) == 3  # All three line items

    def test_table_with_line_items(self, sample_model):
        """Test table() with line_items parameter."""
        table = sample_model.table(line_items=["revenue_sales"])
        assert table is not None
        assert len(table.rows) == 1

    def test_table_with_include_parameters(self, sample_model):
        """Test table() with include_name, include_label parameters."""
        table = sample_model.table(include_name=False, include_label=True)
        # Should show labels
        row_values = [row.cells[0].value for row in table.rows]
        assert "Sales Revenue" in row_values

    def test_table_with_col_order(self, sample_model):
        """Test table() with col_order parameter."""
        table = sample_model.table(col_order=["label", "name"])
        first_row = table.rows[0]
        assert first_row.cells[0].value == "Sales Revenue"
        assert first_row.cells[1].value == "revenue_sales"

    def test_table_matches_tables_line_items(self, sample_model):
        """Test that Model.table() produces same result as Model.tables.line_items()."""
        table1 = sample_model.table(
            line_items=["revenue_sales"],
            include_name=True,
            include_label=True,
        )
        table2 = sample_model.tables.line_items(
            line_items=["revenue_sales"],
            include_name=True,
            include_label=True,
        )
        # Should have same structure
        assert len(table1.rows) == len(table2.rows)
        assert len(table1.columns) == len(table2.columns)

    def test_table_with_other_parameters(self, sample_model):
        """Test table() with other parameters like group_by_category."""
        table = sample_model.table(
            group_by_category=True,
            include_totals=True,
        )
        assert table is not None
        # Should have category headers + items + totals
        assert len(table.rows) > 3


class TestBackwardCompatibility:
    """Test that existing functionality still works."""

    def test_group_by_category_still_works(self, sample_model):
        """Test that group_by_category parameter still works."""
        table = sample_model.tables.line_items(group_by_category=True)
        assert table is not None
        # Should have category headers
        row_values = [row.cells[0].value for row in table.rows]
        # Category names might appear (if there are category headers)
        assert len(row_values) > 3  # More rows due to category headers

    def test_include_percent_change_still_works(self, sample_model):
        """Test that include_percent_change still works."""
        table = sample_model.tables.line_items(
            line_items=["revenue_sales"],
            include_percent_change=True,
        )
        # Should have item + percent change row
        assert len(table.rows) == 2

    def test_include_totals_still_works(self, sample_model):
        """Test that include_totals parameter still works."""
        table = sample_model.tables.line_items(include_totals=True)
        # Should have items + totals row
        assert len(table.rows) == 4  # 3 items + 1 total

    def test_hardcoded_color_still_works(self, sample_model):
        """Test that hardcoded_color parameter still works."""
        table = sample_model.tables.line_items(hardcoded_color="blue")
        assert table is not None
