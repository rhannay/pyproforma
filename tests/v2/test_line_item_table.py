"""
Tests for LineItemResult.table() method.
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


@pytest.fixture
def simple_model():
    """Create a simple test model."""
    return SimpleModel(periods=[2024, 2025, 2026])


def test_line_item_result_has_table_method(simple_model):
    """Test that LineItemResult has a table method."""
    result = simple_model["revenue"]
    assert hasattr(result, "table")
    assert callable(result.table)


def test_line_item_result_table_basic(simple_model):
    """Test generating a basic table for a line item."""
    result = simple_model["revenue"]
    table = result.table()

    # Should have header + 1 data row
    assert len(table.cells) == 2

    # Check header row
    header = table.cells[0]
    assert header[0].value == "Label"
    assert header[1].value == 2024
    assert header[2].value == 2025
    assert header[3].value == 2026

    # Check data row
    data_row = table.cells[1]
    assert data_row[0].value == "Revenue"
    assert data_row[1].value == 100000
    assert data_row[2].value == 110000
    assert data_row[3].value == 121000


def test_line_item_result_table_with_name(simple_model):
    """Test generating a table with name column included."""
    result = simple_model["revenue"]
    table = result.table(include_name=True)

    # Check header row
    header = table.cells[0]
    assert header[0].value == "Name"
    assert header[1].value == "Label"
    assert header[2].value == 2024

    # Check data row
    data_row = table.cells[1]
    assert data_row[0].value == "revenue"
    assert data_row[1].value == "Revenue"


def test_line_item_result_table_calculated_values(simple_model):
    """Test table for a calculated line item."""
    result = simple_model["expenses"]
    table = result.table()

    # Check data row values
    data_row = table.cells[1]
    assert data_row[0].value == "Operating Expenses"
    assert data_row[1].value == 60000  # 100000 * 0.6
    assert data_row[2].value == 66000  # 110000 * 0.6
    assert data_row[3].value == 72600  # 121000 * 0.6


def test_line_item_result_table_no_label(simple_model):
    """Test table for a line item without a label."""

    class ModelNoLabel(ProformaModel):
        revenue = FixedLine(values={2024: 100000, 2025: 110000})

    model = ModelNoLabel(periods=[2024, 2025])
    result = model["revenue"]
    table = result.table()

    # Should use name as fallback when no label
    data_row = table.cells[1]
    assert data_row[0].value == "revenue"
