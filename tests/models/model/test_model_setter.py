import pytest

from pyproforma import Model
from pyproforma.models.line_item import LineItem


class TestConstantPassed:
    @pytest.fixture
    def model_with_years(self):
        """Create a model with years for testing."""
        return Model(years=[2023, 2024, 2025])

    @pytest.fixture
    def empty_model(self):
        """Create a model without years for testing error cases."""
        return Model()

    def test_setter_with_integer_value(self, model_with_years):
        """Test setting a line item with an integer constant value."""
        model_with_years["new_item"] = 99

        # Verify the line item was created
        assert "new_item" in model_with_years.line_item_names

        # Verify values are set correctly for all years
        assert model_with_years["new_item", 2023] == 99.0
        assert model_with_years["new_item", 2024] == 99.0
        assert model_with_years["new_item", 2025] == 99.0

        # Verify it can be accessed via line_item method
        line_item_results = model_with_years.line_item("new_item")
        expected_values = {2023: 99.0, 2024: 99.0, 2025: 99.0}
        assert line_item_results.values == expected_values

    def test_setter_with_float_value(self, model_with_years):
        """Test setting a line item with a float constant value."""
        model_with_years["profit_margin"] = 0.15

        # Verify the line item was created
        assert "profit_margin" in model_with_years.line_item_names

        # Verify values are set correctly for all years
        assert model_with_years["profit_margin", 2023] == 0.15
        assert model_with_years["profit_margin", 2024] == 0.15
        assert model_with_years["profit_margin", 2025] == 0.15

    def test_setter_with_zero_value(self, model_with_years):
        """Test setting a line item with zero value."""
        model_with_years["zero_item"] = 0

        # Verify the line item was created
        assert "zero_item" in model_with_years.line_item_names

        # Verify values are set correctly for all years
        assert model_with_years["zero_item", 2023] == 0.0
        assert model_with_years["zero_item", 2024] == 0.0
        assert model_with_years["zero_item", 2025] == 0.0

    def test_setter_with_negative_value(self, model_with_years):
        """Test setting a line item with a negative value."""
        model_with_years["negative_item"] = -50.5

        # Verify the line item was created
        assert "negative_item" in model_with_years.line_item_names

        # Verify values are set correctly for all years
        assert model_with_years["negative_item", 2023] == -50.5
        assert model_with_years["negative_item", 2024] == -50.5
        assert model_with_years["negative_item", 2025] == -50.5

    def test_setter_multiple_items(self, model_with_years):
        """Test setting multiple line items with different values."""
        model_with_years["item1"] = 100
        model_with_years["item2"] = 200.5
        model_with_years["item3"] = 0

        # Verify all items were created
        assert "item1" in model_with_years.line_item_names
        assert "item2" in model_with_years.line_item_names
        assert "item3" in model_with_years.line_item_names

        # Verify values are set correctly
        assert model_with_years["item1", 2023] == 100.0
        assert model_with_years["item2", 2024] == 200.5
        assert model_with_years["item3", 2025] == 0.0

    def test_setter_line_item_added_to_general_category(self, model_with_years):
        """Test that new line items are added to the 'general' category."""
        model_with_years["test_item"] = 42

        # Get the line item definition and verify its category
        line_item_def = model_with_years._line_item_definition("test_item")
        assert line_item_def.category == "general"

    def test_setter_error_no_years(self, empty_model):
        """Test that setting a value raises ValueError when model has no years."""
        with pytest.raises(
            ValueError, match="Cannot add line item: model has no years defined"
        ):
            empty_model["test_item"] = 100

    def test_setter_error_non_string_key(self, model_with_years):
        """Test that setting with non-string key raises TypeError."""
        with pytest.raises(TypeError, match="Line item name must be a string, got int"):
            model_with_years[123] = 100

        with pytest.raises(
            TypeError, match="Line item name must be a string, got float"
        ):
            model_with_years[45.6] = 100

        with pytest.raises(
            TypeError, match="Line item name must be a string, got list"
        ):
            model_with_years[["invalid"]] = 100

    def test_setter_error_non_numeric_value(self, model_with_years):
        """Test that setting with invalid values raises appropriate errors."""
        # String values are now treated as formulas, invalid formulas raise ValueError
        with pytest.raises(
            ValueError,
            match=".*Formula contains undefined line item names: not_a_number",
        ):
            model_with_years["test_item"] = "not_a_number"

        # None values still raise TypeError
        with pytest.raises(
            TypeError,
            match="Value must be.*got NoneType",
        ):
            model_with_years["test_item"] = None

    def test_setter_with_existing_line_item_name_error(self, model_with_years):
        """Test setting existing line item name raises ValueError for primitives."""
        # First, create a line item
        model_with_years["existing_item"] = 100

        # Verify it exists
        assert model_with_years["existing_item", 2023] == 100.0

        # Now try to set it again with a primitive value
        # This should raise ValueError since primitive replacements are not allowed
        with pytest.raises(
            ValueError,
            match=(
                "Cannot replace with primitive values. Use LineItem or dict "
                "to replace, or update attributes directly."
            ),
        ):
            model_with_years["existing_item"] = 200

    def test_setter_integration_with_model_operations(self, model_with_years):
        """Test that items created via setter work with other model operations."""
        model_with_years["revenue"] = 1000
        model_with_years["expenses"] = 800

        # Test model summary includes the new items
        assert "revenue" in model_with_years.line_item_names
        assert "expenses" in model_with_years.line_item_names

        # Test category operations work
        general_category = model_with_years.category("general")
        assert general_category is not None

        # Test model copy includes the new items
        copied_model = model_with_years.copy()
        assert "revenue" in copied_model.line_item_names
        assert "expenses" in copied_model.line_item_names
        assert copied_model["revenue", 2023] == 1000.0
        assert copied_model["expenses", 2023] == 800.0

    def test_setter_with_single_year_model(self):
        """Test setter works correctly with a single-year model."""
        single_year_model = Model(years=[2023])
        single_year_model["test_item"] = 42

        assert single_year_model["test_item", 2023] == 42.0
        line_item_results = single_year_model.line_item("test_item")
        assert line_item_results.values == {2023: 42.0}

    def test_setter_with_large_year_range(self):
        """Test setter works correctly with a large year range."""
        years = list(range(2020, 2051))  # 31 years
        large_model = Model(years=years)
        large_model["test_item"] = 500

        # Verify all years have the correct value
        for year in years:
            assert large_model["test_item", year] == 500.0

        # Verify the values dictionary is correct
        line_item_results = large_model.line_item("test_item")
        expected_values = {year: 500.0 for year in years}
        assert line_item_results.values == expected_values

    def test_setter_with_list_values(self, model_with_years):
        """Test setting a line item with a list of values."""
        model_with_years["list_item"] = [1000, 1100, 1210]

        # Verify the line item was created
        assert "list_item" in model_with_years.line_item_names

        # Verify values are set correctly for all years
        assert model_with_years["list_item", 2023] == 1000.0
        assert model_with_years["list_item", 2024] == 1100.0
        assert model_with_years["list_item", 2025] == 1210.0

        # Verify it can be accessed via line_item method
        line_item_results = model_with_years.line_item("list_item")
        expected_values = {2023: 1000.0, 2024: 1100.0, 2025: 1210.0}
        assert line_item_results.values == expected_values

    def test_setter_with_mixed_numeric_list(self, model_with_years):
        """Test setting a line item with mixed int/float values in list."""
        model_with_years["mixed_list"] = [100, 110.5, 121]

        # Verify values are set correctly
        assert model_with_years["mixed_list", 2023] == 100.0
        assert model_with_years["mixed_list", 2024] == 110.5
        assert model_with_years["mixed_list", 2025] == 121.0

    def test_setter_with_single_item_list(self):
        """Test setter with single-year model and single-item list."""
        single_year_model = Model(years=[2023])
        single_year_model["single_list"] = [42]

        assert single_year_model["single_list", 2023] == 42.0

    def test_setter_error_list_wrong_length(self, model_with_years):
        """Test that list with wrong length raises ValueError."""
        # Too few values
        with pytest.raises(
            ValueError, match="List length \\(2\\) must match number of years \\(3\\)"
        ):
            model_with_years["wrong_length"] = [100, 200]

        # Too many values
        with pytest.raises(
            ValueError, match="List length \\(4\\) must match number of years \\(3\\)"
        ):
            model_with_years["wrong_length"] = [100, 200, 300, 400]

    def test_setter_error_list_with_non_numeric_values(self, model_with_years):
        """Test that list with non-numeric values raises TypeError."""
        with pytest.raises(
            TypeError, match="All list values must be int or float, got str at index 1"
        ):
            model_with_years["invalid_list"] = [100, "not_a_number", 300]

        with pytest.raises(
            TypeError,
            match="All list values must be int or float, got NoneType at index 0",
        ):
            model_with_years["invalid_list"] = [None, 200, 300]

    def test_setter_error_list_with_empty_model(self, empty_model):
        """Test that setting list with empty model raises ValueError."""
        with pytest.raises(
            ValueError, match="Cannot add line item: model has no years defined"
        ):
            empty_model["test_item"] = [100, 200, 300]

    def test_setter_update_existing_with_list_error(self, model_with_years):
        """Test that updating existing line item with list values raises ValueError."""
        # Create initial item with constant value
        model_with_years["update_test"] = 500
        assert model_with_years["update_test", 2023] == 500.0

        # Try to update with list values - should raise ValueError
        with pytest.raises(
            ValueError,
            match=(
                "Cannot replace with primitive values. Use LineItem or dict "
                "to replace, or update attributes directly."
            ),
        ):
            model_with_years["update_test"] = [600, 700, 800]

    def test_setter_list_integration_with_model_operations(self, model_with_years):
        """Test that items created via list setter work with other model operations."""
        model_with_years["revenue"] = [1000, 1100, 1200]
        model_with_years["expenses"] = [800, 850, 900]

        # Test model operations work
        assert "revenue" in model_with_years.line_item_names
        assert "expenses" in model_with_years.line_item_names

        # Test category operations work
        general_category = model_with_years.category("general")
        assert general_category is not None

        # Test model copy includes the new items
        copied_model = model_with_years.copy()
        assert "revenue" in copied_model.line_item_names
        assert "expenses" in copied_model.line_item_names
        assert copied_model["revenue", 2023] == 1000.0
        assert copied_model["expenses", 2024] == 850.0


class TestSetterLineItem:
    """Test __setitem__ method with LineItem objects."""

    @pytest.fixture
    def model_with_years(self):
        """Create a model with years for testing."""
        return Model(years=[2023, 2024])

    def test_setter_with_line_item_object(self, model_with_years):
        """Test that setting with a LineItem object adds it correctly."""
        line_item = LineItem(name="revenue", category="income", formula="1000")
        model_with_years["revenue"] = line_item

        # Verify the line item was added
        assert "revenue" in model_with_years.line_item_names
        assert model_with_years["revenue", 2023] == 1000
        assert model_with_years["revenue", 2024] == 1000

        # Verify the line item properties
        added_item = model_with_years._line_item_definition("revenue")
        assert added_item.name == "revenue"
        assert added_item.category == "income"
        assert added_item.formula == "1000"

    def test_setter_line_item_different_key_name(self, model_with_years):
        """Test that LineItem name is overridden by the key if different."""
        line_item = LineItem(name="original_name", category="costs", formula="500")
        model_with_years["expenses"] = line_item

        # Verify the line item was added with the key name
        assert "expenses" in model_with_years.line_item_names
        assert "original_name" not in model_with_years.line_item_names
        assert model_with_years["expenses", 2023] == 500

        # Verify the line item has the key name
        added_item = model_with_years._line_item_definition("expenses")
        assert added_item.name == "expenses"  # Should use key name
        assert added_item.category == "costs"  # Should preserve other properties

    def test_setter_line_item_existing_item_replacement(self, model_with_years):
        """Test that setting LineItem on existing item replaces it."""
        # First add a line item
        model_with_years["existing"] = 1000
        assert model_with_years["existing", 2023] == 1000

        # Set a LineItem with same key - should replace
        line_item = LineItem(name="new_item", category="income", formula="2000")
        model_with_years["existing"] = line_item

        # Verify the replacement worked
        assert model_with_years["existing", 2023] == 2000
        added_item = model_with_years._line_item_definition("existing")
        assert added_item.name == "existing"  # Should use key name
        assert added_item.category == "income"  # Should have new properties

    def test_setter_line_item_preserves_properties(self, model_with_years):
        """Test that all LineItem properties are preserved when added."""
        line_item = LineItem(
            name="detailed_item",
            category="special",
            label="Detailed Item",
            formula="1500",
            value_format="currency",
        )
        model_with_years["detailed_item"] = line_item

        # Verify all properties are preserved
        added_item = model_with_years._line_item_definition("detailed_item")
        assert added_item.name == "detailed_item"
        assert added_item.category == "special"
        assert added_item.label == "Detailed Item"
        assert added_item.formula == "1500"
        assert added_item.value_format == "currency"

        # Verify it calculates correctly
        assert model_with_years["detailed_item", 2023] == 1500


class TestSetterDictionary:
    """Test __setitem__ method with dictionary LineItem parameters."""

    @pytest.fixture
    def model_with_years(self):
        """Create a model with years for testing."""
        return Model(years=[2023, 2024])

    def test_setter_with_dict_parameters(self, model_with_years):
        """Test that setting with a dictionary creates a LineItem correctly."""
        model_with_years["revenue"] = {
            "category": "income",
            "formula": "1000",
            "label": "Total Revenue",
        }

        # Verify the line item was added
        assert "revenue" in model_with_years.line_item_names
        assert model_with_years["revenue", 2023] == 1000
        assert model_with_years["revenue", 2024] == 1000

        # Verify the line item properties
        added_item = model_with_years._line_item_definition("revenue")
        assert added_item.name == "revenue"
        assert added_item.category == "income"
        assert added_item.label == "Total Revenue"
        assert added_item.formula == "1000"

    def test_setter_dict_name_override(self, model_with_years):
        """Test that dictionary name is overridden by the key."""
        model_with_years["expenses"] = {
            "name": "original_name",
            "category": "costs",
            "formula": "500",
        }

        # Verify the line item was added with the key name
        assert "expenses" in model_with_years.line_item_names
        assert "original_name" not in model_with_years.line_item_names
        assert model_with_years["expenses", 2023] == 500

        # Verify the line item has the key name
        added_item = model_with_years._line_item_definition("expenses")
        assert added_item.name == "expenses"  # Should use key name
        assert added_item.category == "costs"  # Should preserve other properties

    def test_setter_dict_with_values(self, model_with_years):
        """Test dictionary with explicit values instead of formula."""
        model_with_years["margin"] = {
            "category": "ratios",
            "values": {2023: 0.15, 2024: 0.18},
        }

        # Verify the values are set correctly
        assert model_with_years["margin", 2023] == 0.15
        assert model_with_years["margin", 2024] == 0.18

        # Verify properties
        added_item = model_with_years._line_item_definition("margin")
        assert added_item.category == "ratios"

    def test_setter_dict_empty(self, model_with_years):
        """Test that empty dictionary creates a basic line item."""
        model_with_years["basic"] = {}

        # Verify the line item was added with default values
        assert "basic" in model_with_years.line_item_names
        # Should be None since no formula or values provided
        assert model_with_years["basic", 2023] is None

        # Verify the line item has the key name
        added_item = model_with_years._line_item_definition("basic")
        assert added_item.name == "basic"

    def test_setter_dict_invalid_parameters(self, model_with_years):
        """Test that invalid dictionary parameters are handled correctly."""
        # This should work but ignore invalid parameters
        model_with_years["test_item"] = {"formula": "100", "invalid_param": "ignored"}

        assert model_with_years["test_item", 2023] == 100
        added_item = model_with_years._line_item_definition("test_item")
        assert not hasattr(added_item, "invalid_param")

    def test_setter_dict_malformed_values(self, model_with_years):
        """Test that malformed dictionary values raise appropriate errors."""
        with pytest.raises(AttributeError):
            model_with_years["bad_values"] = {"values": "invalid_values_type"}

    def test_setter_dict_existing_item_replacement(self, model_with_years):
        """Test that setting dict on existing item replaces it."""
        # First add a line item
        model_with_years["existing"] = 1000
        assert model_with_years["existing", 2023] == 1000

        # Set a dict with same key - should replace
        model_with_years["existing"] = {"formula": "3000", "category": "costs"}

        # Verify the replacement worked
        assert model_with_years["existing", 2023] == 3000
        added_item = model_with_years._line_item_definition("existing")
        assert added_item.name == "existing"
        assert added_item.category == "costs"


class TestSetterStringFormula:
    """Test __setitem__ method with string formula functionality."""

    @pytest.fixture
    def model_with_years(self):
        """Create a model with years for testing."""
        return Model(years=[2023, 2024, 2025])

    @pytest.fixture
    def model_with_base_data(self):
        """Create a model with base data for formula testing."""
        model = Model(years=[2023, 2024, 2025])
        model["revenue"] = [1000, 1100, 1200]
        model["cost_ratio"] = 0.6
        return model

    def test_setter_with_simple_formula_string(self, model_with_years):
        """Test setting a line item with a simple formula string."""
        model_with_years["profit"] = "1000 * 0.2"

        # Verify the line item was created
        assert "profit" in model_with_years.line_item_names

        # Verify formula is set correctly
        added_item = model_with_years._line_item_definition("profit")
        assert added_item.formula == "1000 * 0.2"

        # Verify values are calculated correctly for all years
        assert model_with_years["profit", 2023] == 200.0
        assert model_with_years["profit", 2024] == 200.0
        assert model_with_years["profit", 2025] == 200.0

    def test_setter_with_reference_formula_string(self, model_with_base_data):
        """Test setting a line item with a formula referencing other line items."""
        model_with_base_data["profit"] = "revenue * (1 - cost_ratio)"

        # Verify the line item was created
        assert "profit" in model_with_base_data.line_item_names

        # Verify formula is set correctly
        added_item = model_with_base_data._line_item_definition("profit")
        assert added_item.formula == "revenue * (1 - cost_ratio)"

        # Verify values are calculated correctly for all years
        # revenue * (1 - 0.6) = revenue * 0.4
        assert model_with_base_data["profit", 2023] == 400.0  # 1000 * 0.4
        assert model_with_base_data["profit", 2024] == 440.0  # 1100 * 0.4
        assert model_with_base_data["profit", 2025] == 480.0  # 1200 * 0.4

    def test_setter_with_complex_formula_string(self, model_with_base_data):
        """Test setting a line item with a complex formula string."""
        model_with_base_data["tax_rate"] = 0.25
        model_with_base_data["net_profit"] = (
            "revenue * (1 - cost_ratio) * (1 - tax_rate)"
        )

        # Verify the line item was created
        assert "net_profit" in model_with_base_data.line_item_names

        # Verify formula is set correctly
        added_item = model_with_base_data._line_item_definition("net_profit")
        assert added_item.formula == "revenue * (1 - cost_ratio) * (1 - tax_rate)"

        # Verify values are calculated correctly
        # revenue * 0.4 * 0.75 = revenue * 0.3
        assert model_with_base_data["net_profit", 2023] == 300.0  # 1000 * 0.3
        assert model_with_base_data["net_profit", 2024] == 330.0  # 1100 * 0.3
        assert model_with_base_data["net_profit", 2025] == 360.0  # 1200 * 0.3

    def test_setter_string_formula_category_default(self, model_with_years):
        """Test that string formula line items get default 'general' category."""
        model_with_years["test_formula"] = "100 + 50"

        # Verify the line item is in general category
        added_item = model_with_years._line_item_definition("test_formula")
        assert added_item.category == "general"

    def test_setter_string_formula_with_math_functions(self, model_with_years):
        """Test string formula with mathematical functions."""
        # This tests if the formula evaluation supports math functions
        model_with_years["growth_rate"] = "0.05"
        model_with_years["compound_growth"] = "1000 * (1 + growth_rate) ** 3"

        # Verify calculation (should be 1000 * 1.05^3 ≈ 1157.625)
        expected = 1000 * (1.05**3)
        assert abs(model_with_years["compound_growth", 2023] - expected) < 0.01

    def test_setter_string_formula_overwrite_prevention(self, model_with_base_data):
        """Test that string formulas cannot overwrite existing line items."""
        # Try to overwrite existing line item with string formula
        with pytest.raises(
            ValueError,
            match=".*already exists.*Cannot replace with formula string.*",
        ):
            model_with_base_data["revenue"] = "2000"

    def test_setter_string_formula_error_no_years(self):
        """Test that string formula raises ValueError when model has no years."""
        empty_model = Model()
        with pytest.raises(
            ValueError, match="Cannot add line item: model has no years defined"
        ):
            empty_model["test_formula"] = "100 + 50"

    def test_setter_string_formula_error_non_string_key(self, model_with_years):
        """Test that non-string keys raise TypeError with string formulas."""
        with pytest.raises(TypeError, match="Line item name must be a string, got int"):
            model_with_years[123] = "100 + 50"

    def test_setter_string_formula_empty_string(self, model_with_years):
        """Test behavior with empty string formula."""
        model_with_years["empty_formula"] = ""

        # Verify the line item was created
        assert "empty_formula" in model_with_years.line_item_names

        # Verify formula is set (empty string)
        added_item = model_with_years._line_item_definition("empty_formula")
        assert added_item.formula == ""

    def test_setter_string_formula_whitespace_only(self, model_with_years):
        """Test behavior with whitespace-only string formula."""
        # Whitespace-only formulas should raise ValueError due to invalid syntax
        with pytest.raises(
            ValueError,
            match=".*Invalid formula syntax:",
        ):
            model_with_years["whitespace_formula"] = "   "

    def test_setter_string_formula_with_special_characters(self, model_with_years):
        """Test string formula with special characters and operators."""
        model_with_years["base_value"] = 1000
        model_with_years["complex_calc"] = "base_value * 1.5 + 200 - 50"

        # Verify calculation: 1000 * 1.5 + 200 - 50 = 1650
        assert model_with_years["complex_calc", 2023] == 1650.0

        # Verify formula is preserved exactly
        added_item = model_with_years._line_item_definition("complex_calc")
        assert added_item.formula == "base_value * 1.5 + 200 - 50"

    def test_setter_string_formula_integration_with_model_operations(
        self, model_with_base_data
    ):
        """Test that string formula items work with other model operations."""
        model_with_base_data["margin"] = "revenue * 0.1"

        # Test model summary includes the new item
        assert "margin" in model_with_base_data.line_item_names

        # Test category operations work
        general_category = model_with_base_data.category("general")
        assert general_category is not None

        # Test model copy includes the formula item
        copied_model = model_with_base_data.copy()
        assert "margin" in copied_model.line_item_names
        assert copied_model["margin", 2023] == 100.0  # 1000 * 0.1

        # Verify formula is preserved in copy
        copied_item = copied_model._line_item_definition("margin")
        assert copied_item.formula == "revenue * 0.1"

    def test_setter_string_formula_with_single_year_model(self):
        """Test string formula works correctly with a single-year model."""
        single_year_model = Model(years=[2023])
        single_year_model["base"] = 500
        single_year_model["calculated"] = "base * 2"

        assert single_year_model["calculated", 2023] == 1000.0

        # Verify formula is set correctly
        added_item = single_year_model._line_item_definition("calculated")
        assert added_item.formula == "base * 2"

    def test_setter_string_formula_multiple_formulas(self, model_with_years):
        """Test setting multiple string formulas that reference each other."""
        model_with_years["base"] = "1000"
        model_with_years["step1"] = "base * 1.1"
        model_with_years["step2"] = "step1 * 1.2"
        model_with_years["final"] = "step2 + 100"

        # Verify the chain calculation: 1000 * 1.1 * 1.2 + 100 = 1420
        assert model_with_years["final", 2023] == 1420.0

        # Verify all formulas are preserved
        assert model_with_years._line_item_definition("base").formula == "1000"
        assert model_with_years._line_item_definition("step1").formula == "base * 1.1"
        assert model_with_years._line_item_definition("step2").formula == "step1 * 1.2"
        assert model_with_years._line_item_definition("final").formula == "step2 + 100"

    def test_setter_string_formula_numeric_string_edge_cases(self, model_with_years):
        """Test edge cases with numeric strings and various formats."""
        # Test different numeric string formats
        model_with_years["integer_string"] = "42"
        model_with_years["float_string"] = "3.14159"
        model_with_years["scientific_notation"] = "1.5e3"
        model_with_years["negative_string"] = "-250"

        # Verify calculations
        assert model_with_years["integer_string", 2023] == 42.0
        assert abs(model_with_years["float_string", 2023] - 3.14159) < 0.00001
        assert model_with_years["scientific_notation", 2023] == 1500.0
        assert model_with_years["negative_string", 2023] == -250.0

        # Verify formulas are preserved exactly as entered
        assert model_with_years._line_item_definition("integer_string").formula == "42"
        assert (
            model_with_years._line_item_definition("float_string").formula == "3.14159"
        )
        assert (
            model_with_years._line_item_definition("scientific_notation").formula
            == "1.5e3"
        )
        assert (
            model_with_years._line_item_definition("negative_string").formula == "-250"
        )

    def test_setter_string_formula_comparison_with_other_setters(
        self, model_with_years
    ):
        """Test string formulas produce same results as other setters."""
        # Create items using different setter methods
        model_with_years["constant_int"] = 100
        model_with_years["constant_formula"] = "100"

        model_with_years["list_values"] = [10, 20, 30]
        model_with_years["base_for_formula"] = [10, 20, 30]
        # Note: Formulas evaluate same for all years unlike lists
        # But we can test that the formula method works

        # Verify the constant values match
        assert (
            model_with_years["constant_int", 2023]
            == model_with_years["constant_formula", 2023]
        )

        # Verify list values are set correctly
        assert model_with_years["list_values", 2023] == 10.0
        assert model_with_years["list_values", 2024] == 20.0
        assert model_with_years["list_values", 2025] == 30.0


class TestPandasSeriesSetter:
    """Test __setitem__ method with pandas Series."""

    @pytest.fixture
    def model_with_years(self):
        """Create a model with years for testing."""
        return Model(years=[2023, 2024, 2025])

    def test_setter_with_pandas_series(self, model_with_years):
        """Test setting a line item with a pandas Series."""
        pd = pytest.importorskip("pandas")

        # Create a pandas Series with years as index
        series = pd.Series({2023: 100.0, 2024: 110.0, 2025: 121.0})

        # Set the series as a line item
        model_with_years["growth_series"] = series

        # Verify the line item was created
        assert "growth_series" in model_with_years.line_item_names

        # Verify values are set correctly
        assert model_with_years["growth_series", 2023] == 100.0
        assert model_with_years["growth_series", 2024] == 110.0
        assert model_with_years["growth_series", 2025] == 121.0

        # Verify it can be accessed via line_item method
        line_item_results = model_with_years.line_item("growth_series")
        expected_values = {2023: 100.0, 2024: 110.0, 2025: 121.0}
        assert line_item_results.values == expected_values

    def test_setter_with_pandas_series_float_index(self, model_with_years):
        """Test that pandas Series with non-integer index raises TypeError."""
        pd = pytest.importorskip("pandas")

        # Create a pandas Series with float index (should fail)
        series = pd.Series({2023.0: 100.0, 2024.0: 110.0})

        with pytest.raises(TypeError, match="pandas Series must have integer index"):
            model_with_years["invalid_series"] = series

    def test_setter_with_pandas_series_string_index(self, model_with_years):
        """Test that pandas Series with string index raises TypeError."""
        pd = pytest.importorskip("pandas")

        # Create a pandas Series with string index (should fail)
        series = pd.Series({"2023": 100.0, "2024": 110.0})

        with pytest.raises(TypeError, match="pandas Series must have integer index"):
            model_with_years["invalid_series"] = series

    def test_setter_with_pandas_series_existing_line_item(self, model_with_years):
        """Test that pandas Series cannot replace existing line items."""
        pd = pytest.importorskip("pandas")

        # First create a line item
        model_with_years["existing_item"] = 100

        # Try to replace with pandas Series (should fail)
        series = pd.Series({2023: 200.0, 2024: 220.0})

        with pytest.raises(
            ValueError, match="Line item 'existing_item' already exists"
        ):
            model_with_years["existing_item"] = series

    def test_setter_pandas_series_compared_to_dict(self, model_with_years):
        """Test that pandas Series produces same results as equivalent dict."""
        pd = pytest.importorskip("pandas")

        # Create equivalent Series and dict
        values_dict = {2023: 50.0, 2024: 75.0, 2025: 100.0}
        series = pd.Series(values_dict)

        # Set both in model
        model_with_years["dict_item"] = values_dict
        model_with_years["series_item"] = series

        # Verify they produce identical results
        for year in [2023, 2024, 2025]:
            dict_value = model_with_years["dict_item", year]
            series_value = model_with_years["series_item", year]
            assert dict_value == series_value


class TestEmptyDictSetItem:
    """Test __setitem__ method with empty dictionary."""

    @pytest.fixture
    def model_with_years(self):
        """Create a model with years for testing."""
        return Model(years=[2023, 2024, 2025])

    def test_empty_dict_creates_line_item_with_name_only(self, model_with_years):
        """Test that setting a line item to an empty dict creates it with just the name."""
        # Initially no line items
        initial_line_items = [
            name
            for name in model_with_years.line_item_names
            if not name.startswith("total_")
        ]
        assert len(initial_line_items) == 0

        # Set a line item to an empty dictionary
        model_with_years["new_line_item"] = {}

        # Check that the line item was created
        assert "new_line_item" in model_with_years.line_item_names

        # Check that the line item has None values for all years
        line_item_result = model_with_years.line_item("new_line_item")
        values = line_item_result.values
        expected_values = {2023: None, 2024: None, 2025: None}
        assert values == expected_values

        # Check that the line item definition has minimal properties
        line_item_def = model_with_years._line_item_definition("new_line_item")
        assert line_item_def.name == "new_line_item"
        assert line_item_def.values is None  # No explicit values set
        assert line_item_def.formula is None  # No formula set
        assert line_item_def.category == "general"  # Default category

    def test_empty_dict_on_existing_line_item_raises_error(self, model_with_years):
        """Test that setting an empty dict for an existing line item raises error."""
        # First create a line item with some values
        model_with_years["existing_item"] = {2023: 100, 2024: 200}

        # Verify it has the expected values
        assert model_with_years["existing_item", 2023] == 100
        assert model_with_years["existing_item", 2024] == 200

        # Setting it to an empty dict should raise an error
        with pytest.raises(
            ValueError,
            match="Line item 'existing_item' already exists. "
            "Cannot set existing line item to empty dictionary.",
        ):
            model_with_years["existing_item"] = {}

    def test_empty_dict_no_years_raises_error(self):
        """Test that empty dict with no years defined raises ValueError."""
        empty_model = Model()

        with pytest.raises(
            ValueError, match="Cannot add line item: model has no years defined"
        ):
            empty_model["test_item"] = {}
