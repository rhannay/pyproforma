"""Tests for Tables.line_items method with include_totals parameter."""

import pytest

from pyproforma import Model
from pyproforma.models.line_item import LineItem


@pytest.fixture
def sample_model():
    """Create a sample model for testing line_items with totals functionality."""
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
        ],
        years=[2023, 2024, 2025],
        categories=["revenue", "expenses"],
    )

    return model


@pytest.fixture
def single_item_model():
    """Create a model with only one item."""
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


class TestLineItemsIncludeTotals:
    """Test the include_totals parameter for Tables.line_items method."""

    def test_line_items_with_totals_default_false(self, sample_model):
        """Test that line_items doesn't include totals by default."""
        table = sample_model.tables.line_items()

        # Should have exactly the number of line items (no totals)
        all_items = sample_model.line_item_names
        assert len(table.rows) == len(all_items)

        # No row should have "Total" in the label
        for row in table.rows:
            assert "Total" not in row.cells[0].value

    def test_line_items_with_totals_false_explicit(self, sample_model):
        """Test line_items with include_totals=False explicitly."""
        table = sample_model.tables.line_items(include_totals=False)

        # Should have exactly the number of line items (no totals)
        all_items = sample_model.line_item_names
        assert len(table.rows) == len(all_items)

        # No row should have "Total" in the label
        for row in table.rows:
            assert "Total" not in row.cells[0].value

    def test_line_items_with_totals_true(self, sample_model):
        """Test line_items with include_totals=True."""
        table = sample_model.tables.line_items(include_totals=True)

        # Should have more rows than just the line items (includes totals)
        all_items = sample_model.line_item_names
        assert len(table.rows) > len(all_items)

        # The last row should be a totals row
        last_row = table.rows[-1]
        assert "Total" in last_row.cells[0].value

    def test_line_items_with_specific_items_and_totals(self, sample_model):
        """Test line_items with specific items and totals."""
        revenue_items = sample_model.line_item_names_by_category("revenue")
        table = sample_model.tables.line_items(
            line_item_names=revenue_items, include_totals=True
        )

        # Should have revenue items + 1 totals row
        assert len(table.rows) == len(revenue_items) + 1

        # Last row should be totals
        last_row = table.rows[-1]
        assert "Total" in last_row.cells[0].value

    def test_line_items_totals_row_styling(self, sample_model):
        """Test that the totals row has correct styling (bold and top border)."""
        table = sample_model.tables.line_items(include_totals=True)

        # The last row should be the totals row
        last_row = table.rows[-1]

        # Should be bold
        assert last_row.cells[0].bold is True

        # Should have a top border
        assert last_row.cells[0].top_border == "thin"

    def test_line_items_totals_calculation(self, sample_model):
        """Test that the totals row shows correct calculated values."""
        revenue_items = sample_model.line_item_names_by_category("revenue")
        table = sample_model.tables.line_items(
            line_item_names=revenue_items, include_totals=True
        )

        # Get the totals row (last row)
        totals_row = table.rows[-1]

        # Get expected totals from the model
        line_items_results = sample_model.line_items(revenue_items)

        # Check that totals match for each year
        for i, year in enumerate(sample_model.years):
            # Cell index is i+1 because first cell is the label
            expected_total = line_items_results.total(year)
            actual_total = totals_row.cells[i + 1].value

            assert actual_total == expected_total, (
                f"Year {year}: expected {expected_total}, got {actual_total}"
            )

    def test_line_items_totals_with_hardcoded_color(self, sample_model):
        """Test that totals work correctly with hardcoded_color parameter."""
        table = sample_model.tables.line_items(
            include_totals=True, hardcoded_color="blue"
        )

        # Should have totals row
        all_items = sample_model.line_item_names
        assert len(table.rows) > len(all_items)

        # Last row should be totals
        last_row = table.rows[-1]
        assert "Total" in last_row.cells[0].value

    def test_line_items_totals_single_item(self, single_item_model):
        """Test totals row with a single item."""
        table = single_item_model.tables.line_items(include_totals=True)

        # Should have 2 rows: 1 line item + 1 totals
        assert len(table.rows) == 2

        # Last row should be totals
        totals_row = table.rows[-1]
        assert "Total" in totals_row.cells[0].value

        # Totals should equal the single item's values
        line_item = single_item_model.line_item("sales")
        for i, year in enumerate(single_item_model.years):
            expected_value = line_item.values.get(year, 0)
            actual_value = totals_row.cells[i + 1].value
            assert actual_value == expected_value

    def test_line_items_totals_all_items(self, sample_model):
        """Test totals with all line items."""
        table = sample_model.tables.line_items(include_totals=True)

        # Get the totals row (last row)
        totals_row = table.rows[-1]

        # Get expected totals from the model (all items)
        all_items = sample_model.line_item_names
        line_items_results = sample_model.line_items(all_items)

        # Check that totals match for each year
        for i, year in enumerate(sample_model.years):
            expected_total = line_items_results.total(year)
            actual_total = totals_row.cells[i + 1].value

            assert actual_total == expected_total, (
                f"Year {year}: expected {expected_total}, got {actual_total}"
            )

    def test_line_items_totals_calculation_mixed_categories(self, sample_model):
        """Test that totals correctly sum items from different categories."""
        # Get one item from each category
        revenue_item = "sales_revenue"
        expense_item = "cost_of_goods"
        
        table = sample_model.tables.line_items(
            line_item_names=[revenue_item, expense_item], include_totals=True
        )

        # Get the totals row (last row)
        totals_row = table.rows[-1]

        # Calculate expected totals manually
        revenue_li = sample_model.line_item(revenue_item)
        expense_li = sample_model.line_item(expense_item)

        for i, year in enumerate(sample_model.years):
            expected_total = revenue_li[year] + expense_li[year]
            actual_total = totals_row.cells[i + 1].value

            assert actual_total == expected_total, (
                f"Year {year}: expected {expected_total}, got {actual_total}"
            )
