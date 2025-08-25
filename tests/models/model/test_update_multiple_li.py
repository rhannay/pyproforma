import pytest
from pyproforma.models.line_item import LineItem
from pyproforma.models.model.model import Model


@pytest.fixture
def basic_model() -> Model:
    """Create a simple model with some line items for testing."""
    model = Model(line_items=[], years=[2023, 2024, 2025])
    
    # Add categories
    model.update.add_category(name="income")
    model.update.add_category(name="expenses")
    model.update.add_category(name="profit")
    
    # Add line items
    model.update.add_line_item(name="revenue", category="income", values={2023: 100, 2024: 110, 2025: 121})
    model.update.add_line_item(name="costs", category="expenses", values={2023: 70, 2024: 75, 2025: 80})
    model.update.add_line_item(name="profit", category="profit", formula="revenue - costs")
    model.update.add_line_item(name="margin", category="profit", formula="profit / revenue", value_format="percentage")
    
    return model


def test_fixture_loads(basic_model: Model):
    """Test that the basic model fixture loads correctly."""
    assert isinstance(basic_model, Model)
    assert len(basic_model.line_item_definitions) == 4
    assert basic_model["revenue", 2023] == 100
    assert basic_model["costs", 2023] == 70
    assert basic_model["profit", 2023] == 30
    assert basic_model["margin", 2023] == 0.3  # 30/100 = 0.3

def test_update_multiple_line_items_basic(basic_model):
    """Test updating multiple line items with basic properties."""
    # Update multiple line items
    basic_model.update.update_multiple_line_items([
        ("revenue", {"values": {2023: 200, 2024: 220, 2025: 242}}),
        ("costs", {"values": {2023: 120, 2024: 130, 2025: 140}})
    ])
    
    # Check that values were updated
    assert basic_model["revenue", 2023] == 200
    assert basic_model["costs", 2023] == 120

    # Check that formulas were recalculated
    assert basic_model["profit", 2023] == 80
    assert basic_model["margin", 2023] == 0.4  # 80/200 = 0.4

def test_update_certaint_values(basic_model):
    """Test updating specific years for multiple line items."""
    # Update specific years
    basic_model.update.update_multiple_line_items([
        ("revenue", {"updated_values": {2023: 250}}),
        ("costs", {"updated_values": {2024: 150}})
    ])
    
    # Check that only specified years were updated
    assert basic_model["revenue", 2023] == 250
    assert basic_model["revenue", 2024] == 110  # Unchanged
    assert basic_model["costs", 2024] == 150
    assert basic_model["costs", 2023] == 70  # Unchanged

    # Check that formulas were recalculated
    assert basic_model["profit", 2023] == 250 - 70
    assert basic_model["margin", 2023] == (250 - 70) / 250  # Updated profit and margin)

def test_update_multiple_line_items_empty_list(basic_model):
    """Test that passing an empty list does nothing."""
    # Get original state
    original_revenue = basic_model["revenue", 2023]
    
    # Update with empty list
    basic_model.update.update_multiple_line_items([])
    
    # Check that nothing changed
    assert basic_model["revenue", 2023] == original_revenue


def test_update_multiple_line_items_formulas(basic_model):
    """Test updating formulas for multiple line items."""
    # Update formulas
    basic_model.update.update_multiple_line_items([
        ("costs", {"formula": "revenue * 0.6", "values": {}}),
        ("margin", {"formula": "profit / revenue * 100", "value_format": "no_decimals"})
    ])
    
    # Check that formulas were updated and recalculated
    assert basic_model.line_item_definition("costs").formula == "revenue * 0.6"
    assert basic_model["costs", 2023] == 60  # 100 * 0.6 = 60

    assert basic_model.line_item_definition("margin").formula == "profit / revenue * 100"
    assert basic_model["margin", 2023] == 40  # (100-60)/100 * 100 = 40
    assert basic_model.line_item_definition("margin").value_format == "no_decimals"


def test_update_multiple_line_items_rename(basic_model):
    """Test renaming line items."""
    # Rename line items
    # Does not work because formula not updated
    with pytest.raises(ValueError):
        basic_model.update.update_multiple_line_items([
            ("revenue", {"new_name": "income"}),
            ("costs", {"new_name": "expenses"})
        ])

    basic_model.update.update_multiple_line_items([
        ("revenue", {"new_name": "income"}),
        ("costs", {"new_name": "expenses"}),
        ("profit", {"formula": "income - expenses"}),
        ("margin", {"formula": "profit / income * 100", "value_format": "no_decimals"})
    ])
    
    # Check that names were updated
    assert "income" in basic_model.line_item_names
    assert "expenses" in basic_model.line_item_names
    assert "revenue" not in basic_model.line_item_names
    assert "costs" not in basic_model.line_item_names

    # Check that formulas still work (they should be updated automatically)
    assert basic_model["profit", 2023] == 30


def test_update_multiple_line_items_invalid_name(basic_model):
    """Test that updating a non-existent line item raises KeyError."""
    with pytest.raises(ValueError, match="Line item 'nonexistent' not found in model"):
        basic_model.update.update_multiple_line_items([
            ("revenue", {"values": {2023: 200}}),
            ("nonexistent", {"values": {2023: 100}})
        ])
    
    # Check that no changes were applied (transaction rolled back)
    assert basic_model.value("revenue", 2023) == 100


def test_update_multiple_line_items_invalid_formula(basic_model):
    """Test that an invalid formula raises a ValueError and no changes are applied."""
    with pytest.raises(ValueError):
        basic_model.update.update_multiple_line_items([
            ("revenue", {"values": {2023: 200}}),
            ("profit", {"formula": "invalid_item - costs"})
        ])
    
    # Check that no changes were applied (transaction rolled back)
    assert basic_model["revenue", 2023] == 100
    assert basic_model.line_item_definition("profit").formula == "revenue - costs"


def test_update_multiple_line_items_change_category(basic_model):
    """Test changing the category of line items."""
    # Move items to new categories
    basic_model.update.update_multiple_line_items([
        ("revenue", {"category": "profit"}),
        ("costs", {"category": "profit"})
    ])
    
    # Check that categories were updated
    assert basic_model.line_item_definition("revenue").category == "profit"
    assert basic_model.line_item_definition("costs").category == "profit"


def test_update_multiple_line_items_all_properties(basic_model):
    """Test updating all properties of a line item at once."""
    # Update all properties
    basic_model.update.update_multiple_line_items([
        ("revenue", {
            "new_name": "total_revenue",
            "category": "profit",
            "label": "Total Revenue",
            "updated_values": {2023: 500},
            "value_format": "two_decimals"
        }),
        ("profit", {
            "formula": "total_revenue - costs"
        }),
        ("margin", {
            "formula": "profit / total_revenue * 100",
            "value_format": "no_decimals"
        })
    ])
    
    # Check that all properties were updated
    updated_item = basic_model.line_item_definition("total_revenue")
    assert updated_item.name == "total_revenue"
    assert updated_item.category == "profit"
    assert updated_item.label == "Total Revenue"
    assert updated_item.values[2023] == 500
    assert updated_item.value_format == "two_decimals"


def test_update_multiple_line_items_mixed_updates(basic_model):
    """Test a mix of updates to different properties for different line items."""
    # Mix of different updates
    basic_model.update.update_multiple_line_items([
        ("revenue", {"updated_values": {2023: 200}, "label": "Annual Revenue"}),
        ("costs", {"formula": "revenue * 0.5", "values": {}}),
        ("profit", {"value_format": "two_decimals"})
    ])
    
    # Check that all updates were applied correctly
    assert basic_model["revenue", 2023] == 200
    assert basic_model.line_item_definition("revenue").label == "Annual Revenue"

    assert basic_model.line_item_definition("costs").formula == "revenue * 0.5"
    assert basic_model["costs", 2023] == 100  # 200 * 0.5

    assert basic_model.line_item_definition("profit").value_format == "two_decimals"
    assert basic_model["profit", 2023] == 100  # 200 - 100
