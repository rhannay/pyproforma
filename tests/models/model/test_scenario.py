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


def test_scenario_returns_new_model(basic_model):
    """Test that scenario returns a new Model instance, not the same instance."""
    scenario_model = basic_model.scenario([
        ("revenue", {"updated_values": {2023: 200}})
    ])
    
    # Should be different instances
    assert scenario_model is not basic_model
    assert isinstance(scenario_model, Model)
    assert id(scenario_model) != id(basic_model)


def test_scenario_original_model_unchanged(basic_model):
    """Test that the original model is not modified when creating a scenario."""
    # Store original values
    original_revenue_2023 = basic_model["revenue", 2023]
    original_profit_2023 = basic_model["profit", 2023]
    
    # Create scenario with changes
    scenario_model = basic_model.scenario([
        ("revenue", {"updated_values": {2023: 200}}),
        ("costs", {"updated_values": {2023: 120}})
    ])
    
    # Original model should be unchanged
    assert basic_model["revenue", 2023] == original_revenue_2023
    assert basic_model["profit", 2023] == original_profit_2023
    
    # Scenario model should have changes
    assert scenario_model["revenue", 2023] == 200
    assert scenario_model["costs", 2023] == 120
    assert scenario_model["profit", 2023] == 80  # 200 - 120


def test_scenario_basic_value_updates(basic_model):
    """Test basic value updates in a scenario."""
    scenario_model = basic_model.scenario([
        ("revenue", {"values": {2023: 200, 2024: 220, 2025: 242}}),
        ("costs", {"values": {2023: 120, 2024: 130, 2025: 140}})
    ])
    
    # Check that values were updated in scenario
    assert scenario_model["revenue", 2023] == 200
    assert scenario_model["costs", 2023] == 120
    
    # Check that formulas were recalculated in scenario
    assert scenario_model["profit", 2023] == 80
    assert scenario_model["margin", 2023] == 0.4  # 80/200 = 0.4


def test_scenario_updated_values(basic_model):
    """Test updating specific years for multiple line items."""
    scenario_model = basic_model.scenario([
        ("revenue", {"updated_values": {2023: 250}}),
        ("costs", {"updated_values": {2024: 150}})
    ])
    
    # Check that only specified years were updated
    assert scenario_model["revenue", 2023] == 250
    assert scenario_model["revenue", 2024] == 110  # Unchanged
    assert scenario_model["costs", 2024] == 150
    assert scenario_model["costs", 2023] == 70  # Unchanged
    
    # Check that formulas were recalculated
    assert scenario_model["profit", 2023] == 250 - 70  # 180
    assert scenario_model["margin", 2023] == (250 - 70) / 250  # 0.72


def test_scenario_empty_list(basic_model):
    """Test that passing an empty list creates an identical copy."""
    scenario_model = basic_model.scenario([])
    
    # Should be different instances but same values
    assert scenario_model is not basic_model
    assert scenario_model["revenue", 2023] == basic_model["revenue", 2023]
    assert scenario_model["profit", 2023] == basic_model["profit", 2023]


def test_scenario_formula_updates(basic_model):
    """Test updating formulas in a scenario."""
    scenario_model = basic_model.scenario([
        ("costs", {"formula": "revenue * 0.6", "values": {}}),
        ("margin", {"formula": "profit / revenue * 100", "value_format": "no_decimals"})
    ])
    
    # Check that formulas were updated and recalculated
    assert scenario_model.get_line_item_definition("costs").formula == "revenue * 0.6"
    assert scenario_model["costs", 2023] == 60  # 100 * 0.6 = 60
    
    assert scenario_model.get_line_item_definition("margin").formula == "profit / revenue * 100"
    assert scenario_model["margin", 2023] == 40  # (100-60)/100 * 100 = 40
    assert scenario_model.get_line_item_definition("margin").value_format == "no_decimals"


def test_scenario_rename_items(basic_model):
    """Test renaming line items in a scenario."""
    scenario_model = basic_model.scenario([
        ("revenue", {"new_name": "income"}),
        ("costs", {"new_name": "expenses"}),
        ("profit", {"formula": "income - expenses"}),
        ("margin", {"formula": "profit / income * 100", "value_format": "no_decimals"})
    ])
    
    # Check that names were updated
    assert "income" in scenario_model.line_item_names()
    assert "expenses" in scenario_model.line_item_names()
    assert "revenue" not in scenario_model.line_item_names()
    assert "costs" not in scenario_model.line_item_names()

    # Check that formulas still work
    assert scenario_model["profit", 2023] == 30


def test_scenario_invalid_name_error(basic_model):
    """Test that invalid line item names raise appropriate errors."""
    with pytest.raises(ValueError, match="Line item 'nonexistent' not found in model"):
        basic_model.scenario([
            ("revenue", {"values": {2023: 200}}),
            ("nonexistent", {"values": {2023: 100}})
        ])


def test_scenario_invalid_formula_error(basic_model):
    """Test that invalid formulas raise appropriate errors."""
    with pytest.raises(ValueError):
        basic_model.scenario([
            ("revenue", {"values": {2023: 200}}),
            ("profit", {"formula": "invalid_item - costs"})
        ])


def test_scenario_change_category(basic_model):
    """Test changing the category of line items in a scenario."""
    scenario_model = basic_model.scenario([
        ("revenue", {"category": "profit"}),
        ("costs", {"category": "profit"})
    ])
    
    # Check that categories were updated
    assert scenario_model.get_line_item_definition("revenue").category == "profit"
    assert scenario_model.get_line_item_definition("costs").category == "profit"


def test_scenario_all_properties(basic_model):
    """Test updating all properties of a line item in a scenario."""
    scenario_model = basic_model.scenario([
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
    updated_item = scenario_model.get_line_item_definition("total_revenue")
    assert updated_item.name == "total_revenue"
    assert updated_item.category == "profit"
    assert updated_item.label == "Total Revenue"
    assert updated_item.values[2023] == 500
    assert updated_item.value_format == "two_decimals"


def test_scenario_mixed_updates(basic_model):
    """Test a mix of updates to different properties for different line items."""
    scenario_model = basic_model.scenario([
        ("revenue", {"updated_values": {2023: 200}, "label": "Annual Revenue"}),
        ("costs", {"formula": "revenue * 0.5", "values": {}}),
        ("profit", {"value_format": "two_decimals"})
    ])
    
    # Check that all updates were applied correctly
    assert scenario_model["revenue", 2023] == 200
    assert scenario_model.get_line_item_definition("revenue").label == "Annual Revenue"
    
    assert scenario_model.get_line_item_definition("costs").formula == "revenue * 0.5"
    assert scenario_model["costs", 2023] == 100  # 200 * 0.5
    
    assert scenario_model.get_line_item_definition("profit").value_format == "two_decimals"
    assert scenario_model["profit", 2023] == 100  # 200 - 100


def test_scenario_preserves_model_structure(basic_model):
    """Test that scenario preserves all model structure (categories, constraints, etc.)."""
    scenario_model = basic_model.scenario([
        ("revenue", {"updated_values": {2023: 200}})
    ])
    
    # Check that model structure is preserved
    assert len(scenario_model.category_definitions) == len(basic_model.category_definitions)
    assert len(scenario_model.line_item_definitions) == len(basic_model.line_item_definitions)
    assert scenario_model.years == basic_model.years
    assert len(scenario_model.constraints) == len(basic_model.constraints)
    assert len(scenario_model.multi_line_items) == len(basic_model.multi_line_items)


def test_scenario_chaining(basic_model):
    """Test that scenarios can be chained to create multiple what-if scenarios."""
    # Create multiple scenarios from the same base
    optimistic = basic_model.scenario([("revenue", {"updated_values": {2023: 200}})])
    pessimistic = basic_model.scenario([("revenue", {"updated_values": {2023: 80}})])
    conservative = basic_model.scenario([("costs", {"updated_values": {2023: 90}})])
    
    # Verify each scenario has different values
    assert optimistic["profit", 2023] == 130  # 200 - 70
    assert pessimistic["profit", 2023] == 10   # 80 - 70
    assert conservative["profit", 2023] == 10  # 100 - 90
    
    # Original should be unchanged
    assert basic_model["profit", 2023] == 30


def test_scenario_documentation_example(basic_model):
    """Test the examples from the documentation to ensure they work correctly."""
    # Example from docstring
    scenario_model = basic_model.scenario([
        ("revenue", {"updated_values": {2023: 150, 2024: 165}}),
        ("costs", {"formula": "revenue * 0.6", "values": {}})
    ])
    
    # Verify the scenario works as documented
    base_profit = basic_model["profit", 2023]
    scenario_profit = scenario_model["profit", 2023]
    
    assert base_profit == 30
    assert scenario_profit == 60  # 150 - (150 * 0.6) = 150 - 90 = 60
    
    # Test chaining scenarios
    optimistic = basic_model.scenario([("revenue", {"updated_values": {2023: 200}})])
    pessimistic = basic_model.scenario([("revenue", {"updated_values": {2023: 80}})])
    
    assert optimistic["profit", 2023] == 130  # 200 - 70
    assert pessimistic["profit", 2023] == 10   # 80 - 70