"""
Tests for v2 row types.
"""

import pytest

from pyproforma.v2 import FixedLine, FormulaLine, ProformaModel
from pyproforma.v2.tables import (
    BlankRow,
    CumulativeChangeRow,
    CumulativePercentChangeRow,
    ItemRow,
    LabelRow,
    LineItemsTotalRow,
    PercentChangeRow,
    TagTotalRow,
    dict_to_row_config,
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


def test_item_row_basic(simple_model):
    """Test basic ItemRow generation."""
    row_config = ItemRow(name="revenue")
    cells = row_config.generate_row(simple_model, label_col_count=1)

    # Should have 1 label cell + 3 period cells
    assert len(cells) == 4
    assert cells[0].value == "Revenue"  # Uses label
    assert cells[1].value == 100000
    assert cells[2].value == 110000
    assert cells[3].value == 121000


def test_item_row_with_custom_label(simple_model):
    """Test ItemRow with custom label."""
    row_config = ItemRow(name="revenue", label="Total Revenue")
    cells = row_config.generate_row(simple_model, label_col_count=1)

    assert cells[0].value == "Total Revenue"


def test_item_row_two_label_columns(simple_model):
    """Test ItemRow with two label columns (name and label)."""
    row_config = ItemRow(name="revenue")
    cells = row_config.generate_row(simple_model, label_col_count=2)

    # Should have 2 label cells + 3 period cells
    assert len(cells) == 5
    assert cells[0].value == "revenue"  # Name
    assert cells[1].value == "Revenue"  # Label


def test_label_row(simple_model):
    """Test LabelRow generation."""
    row_config = LabelRow(label="Income Statement")
    cells = row_config.generate_row(simple_model, label_col_count=1)

    # Should have 1 label cell + 3 blank period cells
    assert len(cells) == 4
    assert cells[0].value == "Income Statement"
    assert cells[0].bold is True
    assert cells[1].value == ""
    assert cells[2].value == ""
    assert cells[3].value == ""


def test_blank_row(simple_model):
    """Test BlankRow generation."""
    row_config = BlankRow()
    cells = row_config.generate_row(simple_model, label_col_count=1)

    # Should have 1 label cell + 3 period cells, all blank
    assert len(cells) == 4
    assert all(cell.value == "" for cell in cells)


def test_percent_change_row(simple_model):
    """Test PercentChangeRow generation."""
    row_config = PercentChangeRow(name="revenue")
    cells = row_config.generate_row(simple_model, label_col_count=1)

    # Should have 1 label cell + 3 period cells
    assert len(cells) == 4
    assert "% Change" in cells[0].value

    # First period should be None (no previous period)
    assert cells[1].value is None

    # Second period: (110000 - 100000) / 100000 = 0.1
    assert cells[2].value == pytest.approx(0.1)

    # Third period: (121000 - 110000) / 110000 = 0.1
    assert cells[3].value == pytest.approx(0.1)


def test_cumulative_change_row(simple_model):
    """Test CumulativeChangeRow generation."""
    row_config = CumulativeChangeRow(name="revenue")
    cells = row_config.generate_row(simple_model, label_col_count=1)

    assert len(cells) == 4
    assert "Cumulative Change" in cells[0].value

    # First period: 100000 - 100000 = 0
    assert cells[1].value == 0

    # Second period: 110000 - 100000 = 10000
    assert cells[2].value == 10000

    # Third period: 121000 - 100000 = 21000
    assert cells[3].value == 21000


def test_cumulative_percent_change_row(simple_model):
    """Test CumulativePercentChangeRow generation."""
    row_config = CumulativePercentChangeRow(name="revenue")
    cells = row_config.generate_row(simple_model, label_col_count=1)

    assert len(cells) == 4
    assert "Cumulative % Change" in cells[0].value

    # First period: 0%
    assert cells[1].value == 0.0

    # Second period: (110000 - 100000) / 100000 = 0.1
    assert cells[2].value == pytest.approx(0.1)

    # Third period: (121000 - 100000) / 100000 = 0.21
    assert cells[3].value == pytest.approx(0.21)


def test_line_items_total_row(simple_model):
    """Test LineItemsTotalRow generation."""
    row_config = LineItemsTotalRow(
        line_item_names=["revenue", "expenses"], label="Combined Total"
    )
    cells = row_config.generate_row(simple_model, label_col_count=1)

    assert len(cells) == 4
    assert cells[0].value == "Combined Total"

    # First period: 100000 + 60000 = 160000
    assert cells[1].value == 160000

    # Second period: 110000 + 66000 = 176000
    assert cells[2].value == 176000

    # Third period: 121000 + 72600 = 193600
    assert cells[3].value == 193600


def test_dict_to_row_config_item():
    """Test converting dict to ItemRow."""
    config = {"row_type": "item", "name": "revenue", "bold": True}
    row = dict_to_row_config(config)

    assert isinstance(row, ItemRow)
    assert row.name == "revenue"
    assert row.bold is True


def test_dict_to_row_config_label():
    """Test converting dict to LabelRow."""
    config = {"row_type": "label", "label": "Income Statement"}
    row = dict_to_row_config(config)

    assert isinstance(row, LabelRow)
    assert row.label == "Income Statement"


def test_dict_to_row_config_blank():
    """Test converting dict to BlankRow."""
    config = {"row_type": "blank"}
    row = dict_to_row_config(config)

    assert isinstance(row, BlankRow)


def test_dict_to_row_config_percent_change():
    """Test converting dict to PercentChangeRow."""
    config = {"row_type": "percent_change", "name": "revenue"}
    row = dict_to_row_config(config)

    assert isinstance(row, PercentChangeRow)
    assert row.name == "revenue"


def test_dict_to_row_config_invalid_type():
    """Test that invalid row_type raises error."""
    config = {"row_type": "invalid"}
    with pytest.raises(ValueError, match="Unknown row_type"):
        dict_to_row_config(config)


def test_dict_to_row_config_missing_type():
    """Test that missing row_type raises error."""
    config = {"name": "revenue"}
    with pytest.raises(ValueError, match="must have 'row_type' key"):
        dict_to_row_config(config)


class TestTagTotalRow:
    """Tests for TagTotalRow."""

    @pytest.fixture
    def model_with_tags(self):
        """Create a model with tagged line items."""

        class TaggedModel(ProformaModel):
            revenue = FixedLine(
                values={2024: 100, 2025: 110}, label="Revenue", tags=["income"]
            )
            interest = FixedLine(
                values={2024: 5, 2025: 6}, label="Interest", tags=["income"]
            )
            expenses = FixedLine(
                values={2024: 60, 2025: 66}, label="Expenses", tags=["expense"]
            )
            taxes = FixedLine(
                values={2024: 10, 2025: 12}, label="Taxes", tags=["expense"]
            )

        return TaggedModel(periods=[2024, 2025])

    def test_tag_total_row_basic(self, model_with_tags):
        """Test basic TagTotalRow generation."""
        row_config = TagTotalRow(tag="income")
        cells = row_config.generate_row(model_with_tags, label_col_count=1)

        # Should have 1 label cell + 2 period cells
        assert len(cells) == 3
        assert cells[0].value == "Total income"  # Default label
        assert cells[0].bold is True

        # 2024: revenue (100) + interest (5) = 105
        assert cells[1].value == 105

        # 2025: revenue (110) + interest (6) = 116
        assert cells[2].value == 116

    def test_tag_total_row_custom_label(self, model_with_tags):
        """Test TagTotalRow with custom label."""
        row_config = TagTotalRow(tag="income", label="Total Income")
        cells = row_config.generate_row(model_with_tags, label_col_count=1)

        assert cells[0].value == "Total Income"

    def test_tag_total_row_two_label_columns(self, model_with_tags):
        """Test TagTotalRow with two label columns."""
        row_config = TagTotalRow(tag="expense", label="Total Expenses")
        cells = row_config.generate_row(model_with_tags, label_col_count=2)

        # Should have 2 label cells + 2 period cells
        assert len(cells) == 4
        assert cells[0].value == ""  # First column empty
        assert cells[1].value == "Total Expenses"  # Second column has label

        # 2024: expenses (60) + taxes (10) = 70
        assert cells[2].value == 70

        # 2025: expenses (66) + taxes (12) = 78
        assert cells[3].value == 78

    def test_tag_total_row_with_formatting(self, model_with_tags):
        """Test TagTotalRow with custom formatting."""
        row_config = TagTotalRow(
            tag="income",
            label="Total Income",
            bold=False,
            bottom_border="double",
            top_border="single",
        )
        cells = row_config.generate_row(model_with_tags, label_col_count=1)

        # Check label cell formatting
        assert cells[0].bold is False
        assert cells[0].bottom_border == "double"
        assert cells[0].top_border == "single"

        # Check value cells have same formatting
        assert cells[1].bold is False
        assert cells[1].bottom_border == "double"
        assert cells[1].top_border == "single"

    def test_tag_total_row_empty_tag(self, model_with_tags):
        """Test TagTotalRow with a tag that has no items."""
        row_config = TagTotalRow(tag="nonexistent")
        cells = row_config.generate_row(model_with_tags, label_col_count=1)

        assert len(cells) == 3
        assert cells[0].value == "Total nonexistent"

        # Should be 0 for all periods when no items have the tag
        assert cells[1].value == 0
        assert cells[2].value == 0

    def test_dict_to_row_config_tag_total(self):
        """Test converting dict to TagTotalRow."""
        config = {
            "row_type": "tag_total",
            "tag": "income",
            "label": "Total Income Items",
            "bold": True,
        }
        row = dict_to_row_config(config)

        assert isinstance(row, TagTotalRow)
        assert row.tag == "income"
        assert row.label == "Total Income Items"
        assert row.bold is True
