"""Test the new dataclass row configuration approach."""
import pytest
from pyproforma import Model
from pyproforma.tables.row_types import (
    ItemRow, LabelRow, BlankRow, dict_to_row_config
)
from pyproforma.tables.table_generator import generate_table


def test_dataclass_row_config_creation():
    """Test that we can create row configs as dataclasses."""
    # Test creating an ItemRow
    item_config = ItemRow(
        name="revenue",
        bold=True,
        value_format="currency"
    )
    
    assert item_config.name == "revenue"
    assert item_config.bold is True
    assert item_config.value_format == "currency"
    assert item_config.include_name is False  # default value
    
    # Test creating a LabelRow
    label_config = LabelRow(
        label="Income Statement",
        bold=True
    )
    
    assert label_config.label == "Income Statement"
    assert label_config.bold is True


def test_dict_to_row_config():
    """Test conversion from dict to dataclass."""
    # Test item row config
    item_dict = {
        "type": "item",
        "name": "revenue",
        "bold": True,
        "value_format": "currency"
    }
    
    item_config = dict_to_row_config(item_dict)
    assert isinstance(item_config, ItemRow)
    assert item_config.name == "revenue"
    assert item_config.bold is True
    assert item_config.value_format == "currency"
    
    # Test label row config
    label_dict = {
        "type": "label",
        "label": "Income Statement",
        "bold": True
    }
    
    label_config = dict_to_row_config(label_dict)
    assert isinstance(label_config, LabelRow)
    assert label_config.label == "Income Statement"
    assert label_config.bold is True


def test_dataclass_serialization():
    """Test that dataclasses can be serialized to/from dict."""
    # Create a row config
    item_config = ItemRow(
        name="revenue",
        bold=True,
        value_format="currency"
    )
    
    # Convert to dict
    config_dict = item_config.to_dict()
    
    assert config_dict["name"] == "revenue"
    assert config_dict["bold"] is True
    assert config_dict["value_format"] == "currency"
    assert config_dict["include_name"] is False
    
    # Convert back from dict
    new_config = ItemRow.from_dict(config_dict)
    
    assert new_config.name == "revenue"
    assert new_config.bold is True
    assert new_config.value_format == "currency"
    assert new_config.include_name is False


def test_mixed_template_types(sample_line_item_set: Model):
    """Test that generate_table works with mixed dict and dataclass configs."""
    # Mix of dict and dataclass configs
    template = [
        {"type": "label", "label": "Income Statement", "bold": True},  # dict
        ItemRow(name="item1", bold=False),  # dataclass
        BlankRow(),  # dataclass
        {"type": "item", "name": "item2", "bold": False},  # dict
    ]
    
    table = generate_table(sample_line_item_set, template)
    
    # Should have 4 rows (label, item, blank, item)
    assert len(table.rows) == 4
    
    # Check that the first row is a label row
    assert table.rows[0].cells[0].value == "Income Statement"
    assert table.rows[0].cells[0].bold is True
    
    # Check that the third row is blank
    assert table.rows[2].cells[0].value == ""
