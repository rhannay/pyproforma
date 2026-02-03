"""Test the new dataclass row configuration approach."""

from pyproforma import Model
from pyproforma.table import Format
from pyproforma.tables.row_types import BlankRow, ItemRow, LabelRow, dict_to_row_config
from pyproforma.tables.table_generator import generate_table_from_template


def test_dataclass_row_config_creation():
    """Test that we can create row configs as dataclasses."""
    # Test creating an ItemRow
    item_config = ItemRow(name="revenue", bold=True, value_format=Format.CURRENCY)

    assert item_config.name == "revenue"
    assert item_config.bold is True
    assert item_config.value_format == "currency"
    assert item_config.included_cols == ["label"]  # default value

    # Test creating an ItemRow with custom included_cols
    item_config_with_cols = ItemRow(
        name="revenue",
        included_cols=["name", "label", "category"],
        bold=True,
        value_format=Format.CURRENCY,
    )

    assert item_config_with_cols.included_cols == ["name", "label", "category"]

    # Test creating a LabelRow
    label_config = LabelRow(label="Income Statement", bold=True)

    assert label_config.label == "Income Statement"
    assert label_config.bold is True


def test_dict_to_row_config():
    """Test conversion from dict to dataclass."""
    # Test item row config
    item_dict = {
        "type": "item",
        "name": "revenue",
        "bold": True,
        "value_format": "currency",
        "included_cols": ["name", "label"],
    }

    item_config = dict_to_row_config(item_dict)
    assert isinstance(item_config, ItemRow)
    assert item_config.name == "revenue"
    assert item_config.bold is True
    assert item_config.value_format == "currency"
    assert item_config.included_cols == ["name", "label"]

    # Test label row config
    label_dict = {"type": "label", "label": "Income Statement", "bold": True}

    label_config = dict_to_row_config(label_dict)
    assert isinstance(label_config, LabelRow)
    assert label_config.label == "Income Statement"
    assert label_config.bold is True


def test_dataclass_serialization():
    """Test that dataclasses can be serialized to/from dict."""
    # Create a row config
    item_config = ItemRow(
        name="revenue",
        included_cols=["name", "label"],
        bold=True,
        value_format=Format.CURRENCY,
    )

    # Convert to dict
    config_dict = item_config.to_dict()

    assert config_dict["name"] == "revenue"
    assert config_dict["bold"] is True
    assert config_dict["value_format"] == "currency"
    assert config_dict["included_cols"] == ["name", "label"]

    # Convert back from dict
    new_config = ItemRow.from_dict(config_dict)

    assert new_config.name == "revenue"
    assert new_config.bold is True
    assert new_config.value_format == "currency"
    assert new_config.included_cols == ["name", "label"]


def test_mixed_template_types(sample_line_item_set: Model):
    """Test that generate_table works with mixed dict and dataclass configs."""
    # Mix of dict and dataclass configs
    template = [
        {"type": "label", "label": "Income Statement", "bold": True},  # dict
        ItemRow(name="item1", bold=False),  # dataclass
        BlankRow(),  # dataclass
        {
            "type": "item",
            "name": "item2",
            "bold": False,
            "included_cols": ["label"],
        },  # dict
    ]

    table = generate_table_from_template(sample_line_item_set, template)

    # Should have 4 rows (label, item, blank, item)
    assert len(table.rows) == 4

    # Check that the first row is a label row
    assert table.rows[0].cells[0].value == "Income Statement"
    assert table.rows[0].cells[0].bold is True

    # Check that the third row is blank
    assert table.rows[2].cells[0].value == ""


def test_itemrow_included_cols_validation():
    """Test that ItemRow validates included_cols properly."""
    import pytest

    # Valid single column (must be in a list now)
    item = ItemRow(name="revenue", included_cols=["label"])
    assert item.included_cols == ["label"]

    # Valid multiple columns
    item = ItemRow(name="revenue", included_cols=["name", "label", "category"])
    assert item.included_cols == ["name", "label", "category"]

    # Invalid column should raise ValueError
    with pytest.raises(ValueError, match="Invalid column 'invalid'"):
        ItemRow(name="revenue", included_cols=["label", "invalid"])

    # Empty list should raise ValueError
    with pytest.raises(ValueError, match="included_cols cannot be an empty list"):
        ItemRow(name="revenue", included_cols=[])

    # Invalid single column should raise ValueError
    with pytest.raises(ValueError, match="Invalid column 'bad'"):
        ItemRow(name="revenue", included_cols=["bad"])


def test_blank_row_label_col_count(sample_line_item_set: Model):
    """Test that BlankRow properly uses label_col_count parameter."""
    blank_row = BlankRow()

    # Test with default label_col_count (1)
    row = blank_row.generate_row(sample_line_item_set, label_col_count=1)

    # Should have 1 label column + number of years
    expected_cells = 1 + len(sample_line_item_set.years)
    assert len(row) == expected_cells

    # All cells should be empty
    for cell in row:
        assert cell.value == ""

    # Test with label_col_count=3
    row_with_three_labels = blank_row.generate_row(
        sample_line_item_set, label_col_count=3
    )

    # Should have 3 label columns + number of years
    expected_cells_three = 3 + len(sample_line_item_set.years)
    assert len(row_with_three_labels) == expected_cells_three

    # All cells should be empty
    for cell in row_with_three_labels:
        assert cell.value == ""


def test_cumulative_change_row_label_col_count(sample_line_item_set: Model):
    """Test that CumulativeChangeRow properly uses label_col_count parameter."""
    from pyproforma.tables.row_types import CumulativeChangeRow

    cumulative_row = CumulativeChangeRow(name="item1")

    # Test with default label_col_count (1) - should only have label
    row = cumulative_row.generate_row(sample_line_item_set, label_col_count=1)

    # Should have 1 label column + number of years
    expected_cells = 1 + len(sample_line_item_set.years)
    assert len(row) == expected_cells

    # First cell should be the label (not the name)
    assert "Cumulative Change" in row[0].value

    # Test with label_col_count=2 - should have name and label
    row_with_name = cumulative_row.generate_row(sample_line_item_set, label_col_count=2)

    # Should have 2 label columns + number of years
    expected_cells_two = 2 + len(sample_line_item_set.years)
    assert len(row_with_name) == expected_cells_two

    # First cell should be the name, second should be the label
    assert row_with_name[0].value == "item1"
    assert "Cumulative Change" in row_with_name[1].value


def test_custom_row_label_col_count(sample_line_item_set: Model):
    """Test that CustomRow properly uses label_col_count parameter."""
    from pyproforma.tables.row_types import CustomRow

    custom_row = CustomRow(label="Custom Label", values={2023: 100, 2024: 200})

    # Test with default label_col_count (1) - should only have label
    row = custom_row.generate_row(sample_line_item_set, label_col_count=1)

    # Should have 1 label column + number of years
    expected_cells = 1 + len(sample_line_item_set.years)
    assert len(row) == expected_cells

    # First cell should be the label
    assert row[0].value == "Custom Label"

    # Test with label_col_count=2 - should have empty name cell and label
    row_with_name = custom_row.generate_row(sample_line_item_set, label_col_count=2)

    # Should have 2 label columns + number of years
    expected_cells_two = 2 + len(sample_line_item_set.years)
    assert len(row_with_name) == expected_cells_two

    # First cell should be empty (name placeholder), second should be the label
    assert row_with_name[0].value == ""
    assert row_with_name[1].value == "Custom Label"


def test_category_total_row_label_col_count(sample_line_item_set: Model):
    """Test that CategoryTotalRow properly uses label_col_count parameter."""
    from pyproforma.tables.row_types import CategoryTotalRow

    # Add some items to income category for testing
    sample_line_item_set.update.update_line_item("item1", category="income")
    sample_line_item_set.update.update_line_item("item2", category="income")

    category_total_row = CategoryTotalRow(category_name="income")

    # Test with default label_col_count (1) - should only have label
    row = category_total_row.generate_row(sample_line_item_set, label_col_count=1)

    # Should have 1 label column + number of years
    expected_cells = 1 + len(sample_line_item_set.years)
    assert len(row) == expected_cells

    # First cell should be the label (default: category label + "Total")
    assert "income Total" in row[0].value

    # Test with label_col_count=2 - should have empty name cell and label
    row_with_name = category_total_row.generate_row(
        sample_line_item_set, label_col_count=2
    )

    # Should have 2 label columns + number of years
    expected_cells_two = 2 + len(sample_line_item_set.years)
    assert len(row_with_name) == expected_cells_two

    # First cell should be empty (name placeholder), second should be the label
    assert row_with_name[0].value == ""
    assert "income Total" in row_with_name[1].value


def test_category_total_row_custom_label(sample_line_item_set: Model):
    """Test CategoryTotalRow with custom label."""
    from pyproforma.tables.row_types import CategoryTotalRow

    # Add some items to income category
    sample_line_item_set.update.update_line_item("item1", category="income")

    category_total_row = CategoryTotalRow(
        category_name="income", label="Custom Total Label"
    )

    row = category_total_row.generate_row(sample_line_item_set, label_col_count=1)

    # Should use custom label
    assert row[0].value == "Custom Total Label"


def test_category_total_row_styling(sample_line_item_set: Model):
    """Test CategoryTotalRow with styling options."""
    from pyproforma.tables.row_types import CategoryTotalRow

    # Add some items to income category
    sample_line_item_set.update.update_line_item("item1", category="income")

    category_total_row = CategoryTotalRow(
        category_name="income",
        bold=True,
        bottom_border="double",
        top_border="single",
        value_format=Format.PERCENT,
    )

    row = category_total_row.generate_row(sample_line_item_set, label_col_count=1)

    # Check styling is applied
    assert row[0].bold is True
    assert row[0].bottom_border == "double"
    assert row[0].top_border == "single"

    # Check value cells have correct formatting
    for i in range(1, len(row)):  # Skip label cell
        assert row[i].value_format == "percent"
        assert row[i].bold is True
