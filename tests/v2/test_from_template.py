"""
Tests for v2 from_template functionality.
"""

import pytest

from pyproforma.v2 import FixedLine, FormulaLine, ProformaModel
from pyproforma.v2.tables import (
    BlankRow,
    HeaderRow,
    ItemRow,
    LabelRow,
    LineItemsTotalRow,
)


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


def test_from_template_with_dict_config(simple_model):
    """Test from_template using dict configurations."""
    template = [
        {"row_type": "header", "col_labels": "Name"},
        {"row_type": "label", "label": "Income Statement", "bold": True},
        {"row_type": "item", "name": "revenue"},
        {"row_type": "item", "name": "expenses"},
        {"row_type": "blank"},
        {
            "row_type": "line_items_total",
            "line_item_names": ["revenue", "expenses"],
            "label": "Total",
        },
    ]

    table = simple_model.tables.from_template(template)

    # Should have header + 5 data rows
    assert len(table.cells) == 6

    # Check header
    header = table.cells[0]
    assert header[0].value == "Name"
    assert header[1].value == 2024
    assert header[2].value == 2025
    assert header[3].value == 2026

    # Check label row
    label_row = table.cells[1]
    assert label_row[0].value == "Income Statement"
    assert label_row[0].bold is True

    # Check revenue row
    revenue_row = table.cells[2]
    assert revenue_row[0].value == "Revenue"
    assert revenue_row[1].value == 100000

    # Check blank row
    blank_row = table.cells[4]
    assert blank_row[0].value == ""

    # Check total row
    total_row = table.cells[5]
    assert total_row[0].value == "Total"
    assert total_row[1].value == 160000  # 100000 + 60000


def test_from_template_with_dataclass_config(simple_model):
    """Test from_template using dataclass configurations."""
    template = [
        HeaderRow(col_labels="Name"),
        LabelRow(label="Income Statement", bold=True),
        ItemRow(name="revenue"),
        ItemRow(name="expenses"),
        BlankRow(),
        LineItemsTotalRow(line_item_names=["revenue", "expenses"], label="Total"),
    ]

    table = simple_model.tables.from_template(template)

    # Should have header + 5 data rows
    assert len(table.cells) == 6

    # Check label row
    label_row = table.cells[1]
    assert label_row[0].value == "Income Statement"


def test_from_template_mixed_config(simple_model):
    """Test from_template with mixed dict and dataclass configurations."""
    template = [
        {"row_type": "header", "col_labels": "Name"},
        {"row_type": "label", "label": "Income Statement"},
        ItemRow(name="revenue"),
        {"row_type": "item", "name": "expenses"},
    ]

    table = simple_model.tables.from_template(template)

    # Should have header + 3 data rows
    assert len(table.cells) == 4


def test_from_template_with_custom_col_labels_string(simple_model):
    """Test from_template with custom column label (string)."""
    template = [
        {"row_type": "header", "col_labels": "Line Item"},
        {"row_type": "item", "name": "revenue"},
    ]

    table = simple_model.tables.from_template(template)

    # Check header
    header = table.cells[0]
    assert header[0].value == "Line Item"


def test_from_template_with_custom_col_labels_list(simple_model):
    """Test from_template with custom column labels (list)."""
    template = [
        {"row_type": "header", "col_labels": ["Name", "Label"]},
        {"row_type": "item", "name": "revenue"},
    ]

    table = simple_model.tables.from_template(template)

    # Check header
    header = table.cells[0]
    assert header[0].value == "Name"
    assert header[1].value == "Label"

    # Check data row has both name and label
    data_row = table.cells[1]
    assert data_row[0].value == "revenue"
    assert data_row[1].value == "Revenue"


def test_from_template_no_periods_raises_error():
    """Test that from_template raises error when model has no periods."""
    model = SimpleModel(periods=[])

    template = [{"row_type": "item", "name": "revenue"}]

    with pytest.raises(ValueError, match="model has no periods defined"):
        model.tables.from_template(template)


def test_from_template_with_percent_change(simple_model):
    """Test from_template with percent change row."""
    template = [
        {"row_type": "header", "col_labels": "Name"},
        {"row_type": "item", "name": "revenue"},
        {"row_type": "percent_change", "name": "revenue"},
    ]

    table = simple_model.tables.from_template(template)

    # Should have header + 2 data rows
    assert len(table.cells) == 3

    # Check percent change row
    percent_change_row = table.cells[2]
    assert "% Change" in percent_change_row[0].value
    assert percent_change_row[1].value is None  # First period
    assert percent_change_row[2].value == pytest.approx(0.1)  # 10% growth


def test_from_template_with_cumulative_rows(simple_model):
    """Test from_template with cumulative change rows."""
    template = [
        {"row_type": "header", "col_labels": "Name"},
        {"row_type": "item", "name": "revenue"},
        {"row_type": "cumulative_change", "name": "revenue"},
        {"row_type": "cumulative_percent_change", "name": "revenue"},
    ]

    table = simple_model.tables.from_template(template)

    # Should have header + 3 data rows
    assert len(table.cells) == 4

    # Check cumulative change row
    cumulative_row = table.cells[2]
    assert cumulative_row[1].value == 0  # Base period
    assert cumulative_row[2].value == 10000  # 110000 - 100000

    # Check cumulative percent change row
    cumulative_percent_row = table.cells[3]
    assert cumulative_percent_row[1].value == 0.0  # Base period
    assert cumulative_percent_row[2].value == pytest.approx(0.1)  # 10%


def test_from_template_comprehensive_example(simple_model):
    """Test comprehensive example with various row types."""
    template = [
        {"row_type": "header", "col_labels": "Name"},
        {"row_type": "label", "label": "Income Statement", "bold": True},
        {"row_type": "blank"},
        {"row_type": "item", "name": "revenue"},
        {"row_type": "percent_change", "name": "revenue", "label": "YoY Growth %"},
        {"row_type": "blank"},
        {"row_type": "item", "name": "expenses"},
        {"row_type": "blank"},
        {"row_type": "item", "name": "profit"},
        {"row_type": "blank"},
        {
            "row_type": "line_items_total",
            "line_item_names": ["revenue"],
            "label": "Total Revenue",
        },
    ]

    table = simple_model.tables.from_template(template)

    # Should have header + 10 data rows
    assert len(table.cells) == 11

    # Verify it produces a valid table
    assert table.cells[0][0].value == "Name"  # Header
    assert table.cells[1][0].value == "Income Statement"  # Label
    assert table.cells[2][0].value == ""  # Blank
    assert table.cells[3][0].value == "Revenue"  # Item
