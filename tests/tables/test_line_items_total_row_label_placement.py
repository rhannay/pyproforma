"""
Test cases for LineItemsTotalRow label placement refactoring.
"""

import pandas as pd
import pytest

from pyproforma import Model


class TestLineItemsTotalRowLabelPlacement:
    """Test LineItemsTotalRow label placement in first cell."""

    @pytest.fixture
    def sample_model(self):
        """Create a sample model for testing."""
        data = pd.DataFrame(
            {
                "item_id": ["r1", "r2", "e1", "e2"],
                "item_name": [
                    "Revenue Source 1",
                    "Revenue Source 2",
                    "Expense 1",
                    "Expense 2",
                ],
                "category": ["revenue", "revenue", "expenses", "expenses"],
                2024: [100000, 50000, -20000, -10000],
                2025: [110000, 55000, -22000, -11000],
                2026: [121000, 60500, -24200, -12100],
            }
        )

        return Model.from_dataframe(
            data, name_col="item_id", label_col="item_name", category_col="category"
        )

    def test_label_in_first_cell_with_single_column(self, sample_model):
        """Test that label appears in first cell with single included column."""
        result = sample_model.tables.line_items(
            included_cols=["label"], include_totals=True, group_by_category=False
        )

        totals_row = result.rows[-1]
        assert totals_row.cells[0].value == "Total"
        # Should have 4 cells total: 1 label column + 3 years
        assert len(totals_row.cells) == 4

    def test_label_in_first_cell_with_name_first(self, sample_model):
        """Test label in first cell when 'name' is first in included_cols."""
        result = sample_model.tables.line_items(
            included_cols=["name", "label"],
            include_totals=True,
            group_by_category=False,
        )

        totals_row = result.rows[-1]
        assert totals_row.cells[0].value == "Total"
        assert totals_row.cells[1].value == ""  # Second cell should be empty
        # Should have 5 cells total: 2 label columns + 3 years
        assert len(totals_row.cells) == 5

    def test_label_in_first_cell_with_category_first(self, sample_model):
        """Test label in first cell when 'category' is first in included_cols."""
        result = sample_model.tables.line_items(
            included_cols=["category", "name", "label"],
            include_totals=True,
            group_by_category=False,
        )

        totals_row = result.rows[-1]
        assert totals_row.cells[0].value == "Total"
        assert totals_row.cells[1].value == ""  # Second cell should be empty
        assert totals_row.cells[2].value == ""  # Third cell should be empty
        # Should have 6 cells total: 3 label columns + 3 years
        assert len(totals_row.cells) == 6

    def test_label_in_first_cell_with_grouping(self, sample_model):
        """Test label in first cell with category grouping enabled."""
        result = sample_model.tables.line_items(
            included_cols=["name", "label", "category"],
            include_totals=True,
            group_by_category=True,
        )

        totals_row = result.rows[-1]
        assert totals_row.cells[0].value == "Total"
        assert totals_row.cells[1].value == ""  # Second cell should be empty
        assert totals_row.cells[2].value == ""  # Third cell should be empty

    def test_custom_label_in_first_cell(self, sample_model):
        """Test that custom label appears in first cell."""
        # This would require creating a custom LineItemsTotalRow directly
        # since the table generator uses a fixed "Total" label
        from pyproforma.tables.row_types import LineItemsTotalRow

        custom_total_row = LineItemsTotalRow(
            line_item_names=["r1", "r2"],
            included_cols=["category", "name", "label"],
            label="Custom Total",
        )

        row = custom_total_row.generate_row(sample_model)
        assert row.cells[0].value == "Custom Total"
        assert row.cells[1].value == ""  # Second cell should be empty
        assert row.cells[2].value == ""  # Third cell should be empty

    def test_all_non_first_cells_empty(self, sample_model):
        """Test that all non-first cells in label columns are empty."""
        test_configs = [
            ["name", "label"],
            ["label", "name"],
            ["category", "label"],
            ["name", "label", "category"],
            ["category", "name", "label"],
        ]

        for included_cols in test_configs:
            result = sample_model.tables.line_items(
                included_cols=included_cols,
                include_totals=True,
                group_by_category=False,
            )

            totals_row = result.rows[-1]

            # First cell should have the label
            assert totals_row.cells[0].value == "Total"

            # All other label column cells should be empty
            num_label_cols = len(included_cols)
            for i in range(1, num_label_cols):
                assert totals_row.cells[i].value == "", (
                    f"Cell {i} should be empty for config {included_cols}, "
                    f"but got: '{totals_row.cells[i].value}'"
                )
