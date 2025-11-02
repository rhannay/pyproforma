"""
Test cases for LabelRow with included_cols parameter.
"""

import pandas as pd
import pytest

from pyproforma import Model


class TestLabelRowIncludedCols:
    """Test LabelRow handling of included_cols parameter."""

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

    def test_label_row_with_multiple_included_cols_and_totals(self, sample_model):
        """Test that LabelRow works with multiple included_cols and totals."""
        result = sample_model.tables.line_items(
            col_order=["label", "name"], include_totals=True, group_by_category=True
        )

        # Should have: 2 category labels + 4 items + 1 total = 7 rows
        assert len(result.rows) == 7

        # All rows should have same number of cells: 2 included_cols + 3 years
        expected_cells = 5
        for i, row in enumerate(result.rows):
            assert len(row.cells) == expected_cells, (
                f"Row {i} has {len(row.cells)} cells, expected {expected_cells}"
            )

        # Debug: Show what we actually get to understand test failure
        row_values = []
        for i, row in enumerate(result.rows):
            first_val = row.cells[0].value if row.cells else "EMPTY"
            second_val = row.cells[1].value if len(row.cells) > 1 else "EMPTY"
            row_values.append((first_val, second_val))

        # The first row should be a category label (either revenue or expenses)
        first_row = result.rows[0]
        first_cell_value = first_row.cells[0].value

        # Find which category appears first and verify structure accordingly
        if first_cell_value == "revenue":
            # Revenue appears first
            assert first_row.cells[1].value == ""  # Second column empty for labels
            # Look for expenses category (should be row 3)
            fourth_row = result.rows[3]
            assert fourth_row.cells[0].value == "expenses"
            assert fourth_row.cells[1].value == ""
        elif first_cell_value == "expenses":
            # Expenses appears first
            assert first_row.cells[1].value == ""  # Second column empty for labels
            # Look for revenue category (should be somewhere else)
            revenue_found = False
            for row in result.rows[1:]:
                if row.cells[0].value == "revenue":
                    revenue_found = True
                    assert row.cells[1].value == ""
                    break
            assert revenue_found, "Revenue category label not found"
        else:
            pytest.fail(
                f"Expected first row to be a category label, got: {first_cell_value}"
            )

    def test_label_row_with_single_included_col_and_totals(self, sample_model):
        """Test that LabelRow works with single included_col and totals."""
        result = sample_model.tables.line_items(
            include_name=False, include_label=True, include_totals=True, group_by_category=True
        )

        # Should have: 2 category labels + 4 items + 1 total = 7 rows
        assert len(result.rows) == 7

        # All rows should have same number of cells: 1 included_col + 3 years
        expected_cells = 4
        for i, row in enumerate(result.rows):
            assert len(row.cells) == expected_cells, (
                f"Row {i} has {len(row.cells)} cells, expected {expected_cells}"
            )

    def test_label_row_with_multiple_included_cols_no_totals(self, sample_model):
        """Test that LabelRow works with multiple included_cols and no totals."""
        result = sample_model.tables.line_items(
            col_order=["label", "name"],
            include_totals=False,
            group_by_category=True,
        )

        # Should have: 2 category labels + 4 items = 6 rows (no total row)
        assert len(result.rows) == 6

        # All rows should have same number of cells: 2 included_cols + 3 years
        expected_cells = 5
        for i, row in enumerate(result.rows):
            assert len(row.cells) == expected_cells, (
                f"Row {i} has {len(row.cells)} cells, expected {expected_cells}"
            )

    def test_label_row_with_three_included_cols(self, sample_model):
        """Test that LabelRow works with three included_cols."""
        result = sample_model.tables.line_items(
            col_order=["label", "name", "category"],
            include_totals=True,
            group_by_category=True,
        )

        # Should have: 2 category labels + 4 items + 1 total = 7 rows
        assert len(result.rows) == 7

        # All rows should have: 3 included_cols + 3 years = 6 cells
        expected_cells = 6
        for i, row in enumerate(result.rows):
            assert len(row.cells) == expected_cells, (
                f"Row {i} has {len(row.cells)} cells, expected {expected_cells}"
            )

        # Find any category label row and verify its structure
        category_label_found = False
        for row in result.rows:
            # Label rows have the category name in first cell and empty in others
            if row.cells[0].value in ["revenue", "expenses"]:
                category_label_found = True
                # name column should be empty for label rows
                assert row.cells[1].value == ""
                # category column should be empty for label rows
                assert row.cells[2].value == ""
                break

        assert category_label_found, "No category label rows found"

    def test_label_row_column_consistency_across_scenarios(self, sample_model):
        """Test consistent column counts across all row types in scenarios."""
        scenarios = [
            (["label"], True, True),
            (["label", "name"], True, True),
            (["label", "name", "category"], True, True),
            (["label", "name"], False, True),
            (["name"], True, True),
        ]

        for col_order, include_totals, group_by_category in scenarios:
            result = sample_model.tables.line_items(
                col_order=col_order,
                include_totals=include_totals,
                group_by_category=group_by_category,
            )

            # All rows should have the same number of cells
            expected_cells = len(col_order) + len(sample_model.years)

            for i, row in enumerate(result.rows):
                assert len(row.cells) == expected_cells, (
                    f"Scenario {col_order}, totals={include_totals}, "
                    f"grouping={group_by_category}: "
                    f"Row {i} has {len(row.cells)} cells, "
                    f"expected {expected_cells}"
                )

    def test_label_row_placement_in_grouped_table(self, sample_model):
        """Test that LabelRow appears in correct positions when grouping."""
        result = sample_model.tables.line_items(
            col_order=["label", "name"], include_totals=True, group_by_category=True
        )

        # Should have 7 rows total
        assert len(result.rows) == 7

        # Find category labels and item rows
        revenue_rows = []
        expense_rows = []
        category_positions = {}

        for i, row in enumerate(result.rows):
            first_cell = row.cells[0].value

            if first_cell == "revenue":
                category_positions["revenue"] = i
            elif first_cell == "expenses":
                category_positions["expenses"] = i
            elif "Revenue Source" in first_cell:
                revenue_rows.append(i)
            elif "Expense" in first_cell:
                expense_rows.append(i)

        # Both categories should be present
        assert "revenue" in category_positions
        assert "expenses" in category_positions

        # Revenue items should follow revenue category label
        revenue_cat_pos = category_positions["revenue"]
        for item_pos in revenue_rows:
            assert item_pos > revenue_cat_pos, (
                f"Revenue item at {item_pos} should come after "
                f"revenue category at {revenue_cat_pos}"
            )

        # Expense items should follow expense category label
        expense_cat_pos = category_positions["expenses"]
        for item_pos in expense_rows:
            assert item_pos > expense_cat_pos, (
                f"Expense item at {item_pos} should come after "
                f"expense category at {expense_cat_pos}"
            )

        # Verify category labels have empty second column
        revenue_label_row = result.rows[category_positions["revenue"]]
        assert revenue_label_row.cells[1].value == ""

        expenses_label_row = result.rows[category_positions["expenses"]]
        assert expenses_label_row.cells[1].value == ""
