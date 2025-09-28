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

        # Verify it appears in the general category totals
        assert "total_general" in model_with_years.line_item_names

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
        """Test that setting with non-numeric value raises TypeError."""
        with pytest.raises(
            TypeError, match="Value must be an int, float, list, or LineItem, got str"
        ):
            model_with_years["test_item"] = "not_a_number"

        with pytest.raises(
            TypeError, match="Value must be an int, float, list, or LineItem, got dict"
        ):
            model_with_years["test_item"] = {"value": 100}

        with pytest.raises(
            TypeError,
            match="Value must be an int, float, list, or LineItem, got NoneType",
        ):
            model_with_years["test_item"] = None

    def test_setter_with_existing_line_item_name_error(self, model_with_years):
        """Test that setting with an existing line item name raises ValueError."""
        # First, create a line item
        model_with_years["existing_item"] = 100

        # Verify it exists
        assert model_with_years["existing_item", 2023] == 100.0

        # Now try to set it again with a different value
        # This should raise ValueError since replacements are not allowed
        with pytest.raises(
            ValueError,
            match="Line item 'existing_item' already exists. Update attributes",
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
            match="Line item 'update_test' already exists. Update attributes",
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

    def test_setter_line_item_existing_item_error(self, model_with_years):
        """Test that setting LineItem on existing item raises ValueError."""
        # First add a line item
        model_with_years["existing"] = 1000

        # Try to set a LineItem with same key
        line_item = LineItem(name="new_item", formula="200")
        with pytest.raises(
            ValueError,
            match="Line item 'existing' already exists. Update attributes",
        ):
            model_with_years["existing"] = line_item

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
