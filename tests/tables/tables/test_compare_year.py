import pytest

from pyproforma.models import Category, LineItem, Model


class TestCompareYear:
    @pytest.fixture
    def sample_model(self):
        """Create a sample Model with line items for testing."""
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
        ]

        return Model(
            line_items=[
                revenue_sales,
                revenue_services,
                cost_of_goods,
                operating_expenses,
            ],
            categories=categories,
            years=[2023, 2024, 2025, 2026],
        )

    def test_compare_year_basic(self, sample_model: Model):
        """Test basic compare_year functionality."""
        table = sample_model.tables.compare_year(
            names=["revenue_sales", "revenue_services"],
            year=2024,
        )
        assert table is not None

        # Should have 5 columns: Item, 2023, 2024, Change, % Change
        assert len(table.columns) == 5

        # Should have 3 rows: 2 items + 1 total row
        assert len(table.rows) == 3

    def test_compare_year_without_change_columns(self, sample_model: Model):
        """Test compare_year without change columns."""
        table = sample_model.tables.compare_year(
            names=["revenue_sales", "revenue_services"],
            year=2024,
            include_change=False,
            include_percent_change=False,
        )

        # Should have 3 columns: Item, 2023, 2024
        assert len(table.columns) == 3

        # Should have 3 rows: 2 items + 1 total row
        assert len(table.rows) == 3

    def test_compare_year_with_only_change(self, sample_model: Model):
        """Test compare_year with only change column."""
        table = sample_model.tables.compare_year(
            names=["revenue_sales"],
            year=2024,
            include_change=True,
            include_percent_change=False,
        )

        # Should have 4 columns: Item, 2023, 2024, Change
        assert len(table.columns) == 4

    def test_compare_year_with_only_percent_change(self, sample_model: Model):
        """Test compare_year with only percent change column."""
        table = sample_model.tables.compare_year(
            names=["revenue_sales"],
            year=2024,
            include_change=False,
            include_percent_change=True,
        )

        # Should have 4 columns: Item, 2023, 2024, % Change
        assert len(table.columns) == 4

    def test_compare_year_sort_by_value(self, sample_model: Model):
        """Test compare_year sorted by current year value."""
        table = sample_model.tables.compare_year(
            names=["revenue_sales", "revenue_services", "cost_of_goods"],
            year=2024,
            sort_by="value",
        )

        # Get the item labels from rows (excluding total row)
        item_labels = [row.cells[0].value for row in table.rows[:-1]]

        # revenue_sales (1,100,000) should be first, followed by revenue_services (575,000),
        # then cost_of_goods (440,000)
        assert item_labels[0] == "Sales Revenue"
        assert item_labels[1] == "Service Revenue"
        assert item_labels[2] == "Cost of Goods Sold"

    def test_compare_year_sort_by_change(self, sample_model: Model):
        """Test compare_year sorted by absolute change."""
        table = sample_model.tables.compare_year(
            names=["revenue_sales", "revenue_services", "operating_expenses"],
            year=2024,
            sort_by="change",
        )

        # Get the item labels from rows (excluding total row)
        item_labels = [row.cells[0].value for row in table.rows[:-1]]

        # revenue_sales has change of 100,000 (10% of 1,000,000)
        # revenue_services has change of 75,000 (15% of 500,000)
        # operating_expenses has change of 15,000 (5% of 300,000)
        # So order should be: revenue_sales, revenue_services, operating_expenses
        assert item_labels[0] == "Sales Revenue"
        assert item_labels[1] == "Service Revenue"
        assert item_labels[2] == "Operating Expenses"

    def test_compare_year_sort_by_percent_change(self, sample_model: Model):
        """Test compare_year sorted by absolute percent change."""
        table = sample_model.tables.compare_year(
            names=["revenue_sales", "revenue_services", "operating_expenses"],
            year=2024,
            sort_by="percent_change",
        )

        # Get the item labels from rows (excluding total row)
        item_labels = [row.cells[0].value for row in table.rows[:-1]]

        # revenue_sales has 10% change
        # revenue_services has 15% change
        # operating_expenses has 5% change
        # So order should be: revenue_services (15%), revenue_sales (10%), operating_expenses (5%)
        assert item_labels[0] == "Service Revenue"
        assert item_labels[1] == "Sales Revenue"
        assert item_labels[2] == "Operating Expenses"

    def test_compare_year_total_row(self, sample_model: Model):
        """Test that the total row is properly formatted."""
        table = sample_model.tables.compare_year(
            names=["revenue_sales", "revenue_services"],
            year=2024,
        )

        # Get the last row (total row)
        total_row = table.rows[-1]

        # Check that the label is "Total"
        assert total_row.cells[0].value == "Total"

        # Check that the cells are bold
        assert all(cell.bold for cell in total_row.cells)

        # Check that the cells have top border
        assert all(cell.top_border == "single" for cell in total_row.cells)

    def test_compare_year_invalid_year(self, sample_model: Model):
        """Test that invalid year raises ValueError."""
        with pytest.raises(ValueError, match="not found in model years"):
            sample_model.tables.compare_year(
                names=["revenue_sales"],
                year=2030,  # Not in model years
            )

    def test_compare_year_invalid_previous_year(self, sample_model: Model):
        """Test that year without previous year raises ValueError."""
        with pytest.raises(ValueError, match="Previous year .* not found"):
            sample_model.tables.compare_year(
                names=["revenue_sales"],
                year=2023,  # Previous year (2022) not in model
            )

    def test_compare_year_invalid_sort_by(self, sample_model: Model):
        """Test that invalid sort_by raises ValueError."""
        with pytest.raises(ValueError, match="Invalid sort_by value"):
            sample_model.tables.compare_year(
                names=["revenue_sales"],
                year=2024,
                sort_by="invalid_option",
            )

    def test_compare_year_percent_format(self, sample_model: Model):
        """Test that percent change uses correct format (one decimal)."""
        table = sample_model.tables.compare_year(
            names=["revenue_sales"],
            year=2024,
        )

        # Get the percent change cell (last cell in first row)
        percent_cell = table.rows[0].cells[-1]

        # Check format is percent_one_decimal
        assert percent_cell.value_format == "percent_one_decimal"

        # The value should be 0.10 (10% growth), formatted as "10.0%"
        assert percent_cell.value == pytest.approx(0.10, rel=0.01)

    def test_compare_year_column_labels(self, sample_model: Model):
        """Test that column labels are correct."""
        table = sample_model.tables.compare_year(
            names=["revenue_sales"],
            year=2024,
        )

        # Check column labels
        assert table.columns[0].label == "Item"
        assert table.columns[1].label == 2023
        assert table.columns[2].label == 2024
        assert table.columns[3].label == "Change"
        assert table.columns[4].label == "% Change"

        # Check that year columns have correct format
        assert table.columns[1].value_format == "year"
        assert table.columns[2].value_format == "year"

    def test_compare_year_values_correctness(self, sample_model: Model):
        """Test that calculated values are correct."""
        table = sample_model.tables.compare_year(
            names=["revenue_sales"],
            year=2024,
        )

        # First row should be revenue_sales
        row = table.rows[0]

        # 2023 value should be 1,000,000
        assert row.cells[1].value == pytest.approx(1000000.0)

        # 2024 value should be 1,100,000 (10% growth)
        assert row.cells[2].value == pytest.approx(1100000.0)

        # Change should be 100,000
        assert row.cells[3].value == pytest.approx(100000.0)

        # Percent change should be 0.10 (10%)
        assert row.cells[4].value == pytest.approx(0.10)
