"""
Tests for v2 Tables namespace functionality.
"""

import pytest

from pyproforma.v2 import FixedLine, FormulaLine, ProformaModel


class SimpleModel(ProformaModel):
    """Simple test model with a few line items."""

    revenue = FixedLine(
        values={2024: 100000, 2025: 110000, 2026: 121000}, label="Revenue"
    )
    expenses = FormulaLine(
        formula=lambda a, li, t: li.revenue[t] * 0.6, label="Operating Expenses"
    )
    profit = FormulaLine(
        formula=lambda a, li, t: li.revenue[t] - li.expenses[t], label="Net Profit"
    )


@pytest.fixture
def simple_model():
    """Create a simple test model."""
    return SimpleModel(periods=[2024, 2025, 2026])


def test_model_has_tables_namespace(simple_model):
    """Test that model has a tables namespace properly initialized."""
    assert hasattr(simple_model, "tables")
    assert simple_model.tables is not None
    # Verify proper initialization with model reference
    assert simple_model.tables._model is simple_model


def test_tables_namespace_type(simple_model):
    """Test that tables namespace is the correct type."""
    from pyproforma.v2.tables import Tables

    assert isinstance(simple_model.tables, Tables)


def test_tables_line_items_all(simple_model):
    """Test generating a table with all line items."""
    table = simple_model.tables.line_items()

    # Should have header + 3 data rows
    assert len(table.cells) == 4

    # Check header row
    header = table.cells[0]
    assert header[0].value == "Name"
    assert header[1].value == 2024
    assert header[2].value == 2025
    assert header[3].value == 2026

    # Check that all line items are present
    row_names = [row[0].value for row in table.cells[1:]]
    assert "revenue" in row_names
    assert "expenses" in row_names
    assert "profit" in row_names


def test_tables_line_items_specific(simple_model):
    """Test generating a table with specific line items."""
    table = simple_model.tables.line_items(line_items=["revenue", "profit"])

    # Should have header + 2 data rows
    assert len(table.cells) == 3

    # Check that only requested items are present
    row_names = [row[0].value for row in table.cells[1:]]
    assert "revenue" in row_names
    assert "profit" in row_names
    assert "expenses" not in row_names


def test_tables_line_items_with_label(simple_model):
    """Test generating a table with labels instead of names."""
    table = simple_model.tables.line_items(include_name=False, include_label=True)

    # Check header row
    header = table.cells[0]
    assert header[0].value == "Label"

    # Check that labels are shown
    row_labels = [row[0].value for row in table.cells[1:]]
    assert "Revenue" in row_labels
    assert "Operating Expenses" in row_labels
    assert "Net Profit" in row_labels


def test_tables_line_items_with_name_and_label(simple_model):
    """Test generating a table with both names and labels."""
    table = simple_model.tables.line_items(include_name=True, include_label=True)

    # Check header row - should have Name and Label columns
    header = table.cells[0]
    assert header[0].value == "Name"
    assert header[1].value == "Label"
    assert header[2].value == 2024

    # Check first data row
    first_row = table.cells[1]
    assert first_row[0].value == "revenue"
    assert first_row[1].value == "Revenue"


def test_tables_line_items_values(simple_model):
    """Test that table contains correct values."""
    table = simple_model.tables.line_items(line_items=["revenue"])

    # Check revenue values in the data row
    revenue_row = table.cells[1]
    assert revenue_row[1].value == 100000
    assert revenue_row[2].value == 110000
    assert revenue_row[3].value == 121000


def test_tables_line_items_invalid_item(simple_model):
    """Test that requesting invalid line item raises error."""
    with pytest.raises(ValueError, match="Line item 'invalid' not found"):
        simple_model.tables.line_items(line_items=["invalid"])


def test_tables_from_template_not_implemented(simple_model):
    """Test that from_template raises NotImplementedError for v2 models."""
    with pytest.raises(NotImplementedError, match="Template-based table generation"):
        simple_model.tables.from_template([])
