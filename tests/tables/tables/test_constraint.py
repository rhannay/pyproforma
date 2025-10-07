"""Tests for Tables.constraint method."""

import pytest

from pyproforma import Model
from pyproforma.models.constraint import Constraint
from pyproforma.models.line_item import LineItem


@pytest.fixture
def sample_model():
    """Create a sample model for testing."""
    # Create line items
    sales_item = LineItem(
        name="sales",
        label="Sales Revenue",
        category="revenue",
        values={2023: 100, 2024: 110, 2025: 120},
    )

    # Create constraint
    constraint = Constraint(
        name="sales_target",
        label="Sales Target Constraint",
        line_item_name="sales",
        target={2023: 95, 2024: 105, 2025: 115},  # Static target values
        operator="ge",  # Sales should be >= target
    )

    # Create model
    model = Model(
        line_items=[sales_item],
        years=[2023, 2024, 2025],
        categories=["revenue", "expenses"],
        constraints=[constraint],
    )

    return model


class TestConstraintMethod:
    """Test the Tables.constraint method."""

    def test_constraint_method_exists(self, sample_model):
        """Test that the constraint method exists and is callable."""
        assert hasattr(sample_model.tables, "constraint")
        assert callable(sample_model.tables.constraint)

    def test_constraint_basic_functionality(self, sample_model):
        """Test basic constraint table generation."""
        # This test will likely fail initially due to the bugs we identified
        table = sample_model.tables.constraint("sales_target")

        # Should return a Table object
        assert table is not None
        assert hasattr(table, "rows")

        # Should have multiple rows (label, item, target, variance, pass/fail)
        assert len(table.rows) >= 5

    def test_constraint_with_color_code_true(self, sample_model):
        """Test constraint table with color coding enabled."""
        table = sample_model.tables.constraint("sales_target", color_code=True)
        assert table is not None

    def test_constraint_with_color_code_false(self, sample_model):
        """Test constraint table with color coding disabled."""
        table = sample_model.tables.constraint("sales_target", color_code=False)
        assert table is not None

    def test_constraint_nonexistent_constraint(self, sample_model):
        """Test constraint table with a nonexistent constraint name."""
        with pytest.raises(KeyError):
            sample_model.tables.constraint("nonexistent_constraint")

    def test_constraint_table_structure(self, sample_model):
        """Test that the constraint table has the expected structure."""
        table = sample_model.tables.constraint("sales_target")

        # Should have at least these row types:
        # - Label row with constraint name
        # - Item row showing the line item values
        # - Target row showing target values
        # - Variance row showing difference
        # - Pass/fail row showing constraint evaluation

        assert len(table.rows) >= 5

        # Check that we have the right number of columns
        # Should be: label column + one column per year
        expected_cols = 1 + len(sample_model.years)  # 1 + 3 = 4
        for row in table.rows:
            assert len(row.cells) == expected_cols

    def test_constraint_table_content(self, sample_model):
        """Test that the constraint table contains expected content."""
        table = sample_model.tables.constraint("sales_target")

        # First row should be label row with constraint label
        label_row = table.rows[0]
        assert "Sales Target Constraint" in str(label_row.cells[0].value)

        # Should have actual values from the sales line item
        # Should have target values
        # Should have variance calculations
        # Should have pass/fail evaluations

        # Note: More specific assertions would depend on the exact implementation
