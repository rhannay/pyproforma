import pytest
from pyproforma import LineItem, Model
from pyproforma.models.line_item import Category

@pytest.fixture
def sample_line_item():
    return LineItem(
        name="test_item",
        label="Test Item",
        category="revenue",
        values={2020: 1.0, 2021: 2.0}
    )

class TestLineItemInit:
    def test_line_item_init(self, sample_line_item):
        item = sample_line_item
        assert item.name == "test_item"
        assert item.label == "Test Item"
        assert item.category == "revenue"
        assert item.values == {2020: 1.0, 2021: 2.0}

    def test_line_item_init_with_label(self, sample_line_item):
        item = sample_line_item
        assert item.name == "test_item"
        assert item.label == "Test Item"
        assert item.category == "revenue"
        assert item.values == {2020: 1.0, 2021: 2.0}

    def test_line_item_init_without_label(self):
        item = LineItem(
            name="default_label_item",
            category="expense",
            values={2020: 3.0, 2021: 4.0}
        )
        assert item.label == "default_label_item"

    def test_no_values(self):
        item = LineItem(
            name="no_values_item",
            label="No Values Item",
            category="revenue"
        )
        assert item.values == {}

    def test_values_can_contain_none(self):
        # Test that None values are now allowed
        item = LineItem(
            name="test_item",
            label="Test Item", 
            category="revenue",
            values={2020: 1.0, 2021: None, 2022: 3.0}
        )
        assert item.values[2021] is None
        
        # Test with single None value
        item2 = LineItem(
            name="test_item2",
            category="expense",
            values={2020: None}
        )
        assert item2.values[2020] is None


class TestGetValue:
    def test_get_value_no_formula(self):
        item = LineItem(
            name="test_item",
            label="Test Item",
            category="revenue",
            values={2020: 1.0, 2021: 2.0},
        )
        vals = {}
        assert item.get_value(vals, 2020) == 1.0
        assert item.get_value(vals, 2021) == 2.0
        
        # Should return None when no value and no formula
        result = item.get_value(vals, 2022)
        assert result is None

    def test_get_value_with_formula(self):
        item = LineItem(
            name="test_item",
            label="Test Item",
            category="revenue",
            values={2020: 1.0, 2021: 2.0},
            formula="test_item[-1] * 1.05"
        )
        vals = {}
        assert item.get_value(vals, 2020) == 1.0
        assert item.get_value(vals, 2021) == 2.0
        vals = {2021: {"test_item": 2.0}}
        assert item.get_value(vals, 2022) == 2.0 * 1.05
        val = {2022: {"test_item": 2.1}}
        assert item.get_value(val, 2023) == 2.1 * 1.05

        # Test for year referening [-1] but previous value does not exist
        with pytest.raises(ValueError) as excinfo:
            item.get_value(vals, 2019)
        assert "2018 not found" in str(excinfo.value)


    def test_get_value_with_gap_in_yers(self):
        item = LineItem(
            name="test_item",
            label="Test Item",
            category="revenue",
            values={2020: 1.0, 2022: 2.0},
        )
        vals = {}
        assert item.get_value(vals, 2020) == 1.0
        
        # Should return None when no value and no formula  
        result = item.get_value(vals, 2021)
        assert result is None

        assert item.get_value(vals, 2022) == 2.0

        # add formula
        item.formula = "test_item[-1] * 1.05"
        vals = {2020: {"test_item": 2.0}}
        assert item.get_value(vals, 2021) == 2.0 * 1.05

    def test_get_value_formula_referendes_other_item(self):
        item2 = LineItem(
            name="item2",
            label="Item 2",
            category="expense",
            values={2020: 3.0},
            formula="item1 * 2"
        )
        vals = {2021: {"item1": 5.0}}
        assert item2.get_value(vals, 2021) == 5.0 * 2

    def test_get_value_returns_none_from_values(self):
        """Test that None values in values dict are returned correctly."""
        item = LineItem(
            name="test_item",
            label="Test Item",
            category="revenue",
            values={2020: 1.0, 2021: None, 2022: 3.0},
        )
        vals = {}
        assert item.get_value(vals, 2020) == 1.0
        assert item.get_value(vals, 2021) is None
        assert item.get_value(vals, 2022) == 3.0

    def test_get_value_none_in_formula_raises_error(self):
        """Test that None values in formulas raise appropriate errors."""
        from pyproforma.models.formula import calculate_formula
        
        # Test with None value in value matrix
        value_matrix = {2023: {'revenue': None, 'costs': 100}}
        
        with pytest.raises(ValueError) as excinfo:
            calculate_formula('revenue + costs', value_matrix, 2023)
        assert "has None value for year 2023" in str(excinfo.value)
        assert "Cannot use None values in formulas" in str(excinfo.value)

        # Test with offset reference to None value
        value_matrix = {2022: {'revenue': None}, 2023: {'revenue': 100, 'costs': 50}}
        
        with pytest.raises(ValueError) as excinfo:
            calculate_formula('revenue[-1] + costs', value_matrix, 2023)
        assert "has None value for year 2022" in str(excinfo.value)
        assert "Cannot use None values in formulas" in str(excinfo.value)

class TestLineItemMisc:

    def test_validate_sorted_and_sequential_accepts_sequential_years(self, sample_line_item):
        item = LineItem(
            name="test",
            label="Test",
            category="test",
            values={
                2000: 1.0,
                2001: 2.0,
                2002: 3.0,
                2003: 4.0
            }
        )
        # No exception should be raised

    def test_validate_sorted_and_sequential_accepts_single_year(self):
        item = LineItem(
            name="test",
            label="Test",
            category="test",
            values={2020: 1.0}
        )
        # No exception should be raised

    def test_item_type_total_basic(self):
        items = [
            LineItem(name="a", label="A", category="revenue", values={2020: 10.0, 2021: 20.0}),
            LineItem(name="b", label="B", category="revenue", values={2020: 5.0, 2021: 15.0}),
            LineItem(name="c", label="C", category="expense", values={2020: 3.0, 2021: 7.0}),
        ]
        item_set = Model(items, years=[2020, 2021])
        assert item_set.category_total("revenue", 2020) == 15.0
        assert item_set.category_total("revenue", 2021) == 35.0
        assert item_set.category_total("expense", 2020) == 3.0
        assert item_set.category_total("expense", 2021) == 7.0

    def test_item_type_total_returns_zero_for_missing_type(self):
        items = [
            LineItem(name="a", label="A", category="revenue", values={2020: 10.0}),
        ]
        item_set = Model(items, years=[2020])
        
        with pytest.raises(KeyError):
            item_set.category_total("expense", 2020)

    def test_item_type_total_raises_keyerror_for_missing_year(self):
        items = [
            LineItem(name="a", label="A", category="revenue", values={2020: 10.0}),
        ]
        item_set = Model(items, years=[2020])
        try:
            item_set.category_total("revenue", 2021)
            assert False, "Should raise KeyError for missing year"
        except KeyError:
            pass

    def test_validate_names_accepts_unique_names(self):
        items = [
            LineItem(name="a", label="A", category="type1", values={2020: 1.0}),
            LineItem(name="b", label="B", category="type2", values={2020: 2.0}),
            LineItem(name="c", label="C", category="type3", values={2020: 3.0}),
        ]
        item_set = Model(items, years=[2020])

    def test_validate_names_raises_for_duplicate_names(self):
        items = [
            LineItem(name="a", label="A", category="type1", values={2020: 1.0}),
            LineItem(name="a", label="A2", category="type2", values={2020: 2.0}),
        ]
        with pytest.raises(ValueError) as excinfo:
            item_set = Model(items, years=[2020])
        assert "Duplicate" in str(excinfo.value)

    def test_line_item_from_dict_basic(self):
        data = {
            "name": "item1",
            "label": "Item 1",
            "category": "revenue",
            "values": {2020: 10.0, 2021: 20.0}
        }
        item = LineItem.from_dict(data)
        assert item.name == "item1"
        assert item.label == "Item 1"
        assert item.category == "revenue"
        assert item.values == {2020: 10.0, 2021: 20.0}

    def test_line_item_from_dict_label_defaults_to_name(self):
        data = {
            "name": "item2",
            "category": "expense",
            "values": {2020: 5.0}
        }
        item = LineItem.from_dict(data)
        assert item.name == "item2"
        assert item.label == "item2"
        assert item.category == "expense"
        assert item.values == {2020: 5.0}

    def test_line_item_from_dict_ignores_non_year_keys(self):
        data = {
            "name": "item3",
            "label": "Item 3",
            "category": "other",
            "values": {2020: 1.0, 2021: 2.0},
            "extra": "should be ignored"
        }
        item = LineItem.from_dict(data)
        assert item.name == "item3"
        assert item.label == "Item 3"
        assert item.category == "other"
        assert item.values == {2020: 1.0, 2021: 2.0}

    def test_line_item_from_dict_raises_for_missing_name(self):
        data = {
            "label": "Missing Name",
            "category": "revenue",
            "values": {2020: 1.0}
        }
        with pytest.raises(KeyError):
            LineItem.from_dict(data)

    def test_line_item_serialization_round_trip(self):
        """Test that to_dict -> from_dict preserves all LineItem data."""
        original = LineItem(
            name="test_item",
            category="revenue", 
            label="Test Item",
            values={2020: 100.0, 2021: 200.0},
            formula="test_formula",
            value_format="currency"
        )
        
        # Convert to dict and back
        data = original.to_dict()
        reconstructed = LineItem.from_dict(data)
        
        # Verify all attributes are preserved
        assert reconstructed.name == original.name
        assert reconstructed.category == original.category
        assert reconstructed.label == original.label
        assert reconstructed.values == original.values
        assert reconstructed.formula == original.formula
        assert reconstructed.value_format == original.value_format

class TestCategory:

    @pytest.mark.parametrize("name", [
        "ValidName",
        "valid_name",
        "valid-name",
        "A",
        "a_b-c",
        "a1"
    ])
    def test_item_type_validate_name_accepts_valid_names(self, name):
        # Should not raise
        Category(name=name)

    @pytest.mark.parametrize("name", [
        "invalid name",    # contains space
        "invalid$name",    # contains special character $
        "invalid.name",    # contains dot
        "invalid@name",    # contains @
        "invalid/name",    # contains /
        "invalid,name",    # contains comma
        "invalid*name",    # contains *
        "invalid!name",    # contains !
        "invalid#name",    # contains #
        "invalid%name",    # contains %
        "invalid^name",    # contains ^
        "invalid&name",    # contains &
        "invalid(name)",   # contains parentheses
        "invalid+name",    # contains +
        "invalid=name",    # contains =
        "invalid~name",    # contains ~
        "invalid`name",    # contains `
        "invalid|name",    # contains |
        "invalid\\name",   # contains backslash
        "invalid'name",    # contains apostrophe
        "invalid\"name",   # contains quote
    ])
    def test_item_type_validate_name_rejects_invalid_names(self, name):
        with pytest.raises(ValueError) as excinfo:
            Category(name=name)
        assert "Category name must only contain" in str(excinfo.value)

    def test_item_type_total_name_returns_expected_string(self):
        category = Category(name="revenue")
        assert category.total_name == "total_revenue"

        category = Category(name="expense")
        assert category.total_name == "total_expense"

        category = Category(name="custom_type")
        assert category.total_name == "total_custom_type"

        category = Category(name="type-1")
        assert category.total_name == "total_type-1"

        category = Category(name="type_2")
        assert category.total_name == "total_type_2"

    def test_include_total_defaults_to_true(self):
        category = Category(name="revenue")
        assert category.include_total is True
        assert category.total_name == "total_revenue"
        assert category.total_label == "Total revenue"

    def test_include_total_true_sets_total_properties(self):
        category = Category(name="expense", include_total=True)
        assert category.include_total is True
        assert category.total_name == "total_expense"
        assert category.total_label == "Total expense"

    def test_include_total_false_sets_total_properties_to_none(self):
        category = Category(name="revenue", include_total=False)
        assert category.include_total is False
        assert category.total_name is None
        assert category.total_label is None

    def test_include_total_with_custom_labels(self):
        category = Category(
            name="revenue", 
            label="Operating Revenue", 
            total_label="Total Operating Revenue",
            include_total=True
        )
        assert category.include_total is True
        assert category.label == "Operating Revenue"
        assert category.total_name == "total_revenue"
        assert category.total_label == "Total Operating Revenue"

    def test_include_total_false_ignores_total_label_parameter(self):
        category = Category(
            name="expense",
            label="Operating Expenses",
            total_label="This should be ignored",
            include_total=False
        )
        assert category.include_total is False
        assert category.label == "Operating Expenses"
        assert category.total_name is None
        assert category.total_label is None

    def test_category_str_representation_with_include_total_true(self):
        category = Category(name="revenue", label="Revenue")
        expected = "Category(name='revenue', label='Revenue', total_label='Total Revenue', total_name='total_revenue', include_total=True)"
        assert str(category) == expected

    def test_category_str_representation_with_include_total_false(self):
        category = Category(name="expense", include_total=False)
        expected = "Category(name='expense', label='expense', total_label='None', total_name='None', include_total=False)"
        assert str(category) == expected

    def test_category_repr_same_as_str(self):
        category = Category(name="revenue", include_total=True)
        assert repr(category) == str(category)

        category_no_total = Category(name="expense", include_total=False)
        assert repr(category_no_total) == str(category_no_total)

    def test_category_serialization_round_trip(self):
        """Test that to_dict -> from_dict preserves all Category data."""
        original = Category(
            name="test_category",
            label="Test Category",
            total_label="Total Test Category",
            include_total=True
        )
        
        # Convert to dict and back
        data = original.to_dict()
        reconstructed = Category.from_dict(data)
        
        # Verify all attributes are preserved
        assert reconstructed.name == original.name
        assert reconstructed.label == original.label
        assert reconstructed.total_label == original.total_label
        assert reconstructed.total_name == original.total_name
        assert reconstructed.include_total == original.include_total

    def test_category_serialization_round_trip_no_total(self):
        """Test serialization round trip for Category with include_total=False."""
        original = Category(
            name="no_total_category",
            label="No Total Category",
            include_total=False
        )
        
        # Convert to dict and back
        data = original.to_dict()
        reconstructed = Category.from_dict(data)
        
        # Verify all attributes are preserved
        assert reconstructed.name == original.name
        assert reconstructed.label == original.label
        assert reconstructed.total_label is None
        assert reconstructed.total_name is None
        assert reconstructed.include_total == original.include_total

class TestLineItemNoneValues:
    """Test class specifically for None value functionality in LineItems."""

    def test_line_item_accepts_none_values(self):
        """Test that LineItem can be created with None values in values dict."""
        item = LineItem(
            name="test_none",
            category="revenue",
            values={2020: 100.0, 2021: None, 2022: 200.0}
        )
        assert item.values[2020] == 100.0
        assert item.values[2021] is None
        assert item.values[2022] == 200.0

    def test_line_item_all_none_values(self):
        """Test LineItem with all None values."""
        item = LineItem(
            name="all_none",
            category="revenue",
            values={2020: None, 2021: None, 2022: None}
        )
        assert all(value is None for value in item.values.values())

    def test_get_value_returns_none_from_values_dict(self):
        """Test that get_value returns None when None is stored in values."""
        item = LineItem(
            name="none_test",
            category="revenue",
            values={2020: 100.0, 2021: None, 2022: 200.0}
        )
        
        interim_values = {}
        assert item.get_value(interim_values, 2020) == 100.0
        assert item.get_value(interim_values, 2021) is None
        assert item.get_value(interim_values, 2022) == 200.0

    def test_get_value_returns_none_when_no_data(self):
        """Test that get_value returns None when no value exists and no formula."""
        item = LineItem(name="empty", category="revenue")
        
        interim_values = {}
        result = item.get_value(interim_values, 2020)
        assert result is None

    def test_get_value_formula_overrides_none_values(self):
        """Test that formulas work even when values dict contains None."""
        item = LineItem(
            name="formula_test",
            category="revenue",
            values={2020: None},  # None in values
            formula="test_item * 2"  # But has formula
        )
        
        # Formula should be used since year not in values (None doesn't count as having a value)
        interim_values = {2021: {"test_item": 50.0}}
        result = item.get_value(interim_values, 2021)
        assert result == 100.0  # 50 * 2

    def test_none_values_in_model_category_totals(self):
        """Test that None values are treated as 0 in category totals."""
        from pyproforma import Model, Category
        
        items = [
            LineItem(name="item1", category="revenue", values={2020: 100.0, 2021: None}),
            LineItem(name="item2", category="revenue", values={2020: None, 2021: 200.0}),
            LineItem(name="item3", category="revenue", values={2020: 50.0, 2021: 75.0}),
        ]
        
        model = Model(
            line_items=items,
            categories=[Category(name="revenue")],
            years=[2020, 2021]
        )
        
        # 2020: 100 + 0 + 50 = 150 (None treated as 0)
        assert model["total_revenue", 2020] == 150.0
        
        # 2021: 0 + 200 + 75 = 275 (None treated as 0)
        assert model["total_revenue", 2021] == 275.0

    def test_formula_error_with_none_values(self):
        """Test that formulas raise proper errors when referencing None values."""
        from pyproforma import Model, Category
        
        base_item = LineItem(name="base", category="test", values={2020: 100.0, 2021: None})
        calc_item = LineItem(name="calculated", category="test", formula="base * 2")
        
        # Model creation should work for years without None formula references
        model = Model(
            line_items=[base_item, calc_item],
            categories=[Category(name="test")],
            years=[2020]  # Only year that works
        )
        
        # This should work fine
        assert model["calculated", 2020] == 200.0
        
        # But creating a model that includes a year with None formula reference should fail
        with pytest.raises(ValueError) as excinfo:
            failing_model = Model(
                line_items=[base_item, calc_item],
                categories=[Category(name="test")],
                years=[2020, 2021]  # 2021 will fail due to None in formula
            )
        
        error_msg = str(excinfo.value)
        assert "has None value for year 2021" in error_msg
        assert "Cannot use None values in formulas" in error_msg

    def test_formula_error_with_offset_none_values(self):
        """Test formula errors when offset references point to None values."""
        from pyproforma.models.formula import calculate_formula
        
        # Test offset reference to None value
        value_matrix = {
            2019: {"revenue": None},
            2020: {"revenue": 100.0}
        }
        
        with pytest.raises(ValueError) as excinfo:
            calculate_formula("revenue[-1] * 1.1", value_matrix, 2020)
        
        error_msg = str(excinfo.value)
        assert "has None value for year 2019" in error_msg
        assert "Cannot use None values in formulas" in error_msg

    def test_serialization_preserves_none_values(self):
        """Test that to_dict and from_dict preserve None values correctly."""
        original = LineItem(
            name="serialize_test",
            category="revenue",
            values={2020: 100.0, 2021: None, 2022: 200.0},
            formula="test_formula"
        )
        
        # Convert to dict and back
        data = original.to_dict()
        reconstructed = LineItem.from_dict(data)
        
        # Verify None values are preserved
        assert reconstructed.values[2020] == 100.0
        assert reconstructed.values[2021] is None
        assert reconstructed.values[2022] == 200.0
        assert reconstructed.formula == "test_formula"

    def test_mixed_none_and_formula_behavior(self):
        """Test complex scenario with None values and formulas."""
        item = LineItem(
            name="complex_test",
            category="revenue",
            values={2020: 100.0, 2021: None, 2023: 300.0},  # Gap at 2022
            formula="complex_test[-1] * 1.1"
        )
        
        interim_values = {}
        
        # 2020: explicit value
        assert item.get_value(interim_values, 2020) == 100.0
        
        # 2021: explicit None value
        assert item.get_value(interim_values, 2021) is None
        
        # 2022: no explicit value, should use formula with 2021 value
        interim_values = {2021: {"complex_test": None}}
        with pytest.raises(ValueError) as excinfo:
            item.get_value(interim_values, 2022)
        assert "has None value for year 2021" in str(excinfo.value)
        
        # 2023: explicit value (should override formula)
        assert item.get_value({}, 2023) == 300.0

    def test_none_values_in_complex_model(self):
        """Test None values in a more complex model scenario."""
        from pyproforma import Model, Category
        
        # Create items with None values
        revenue = LineItem(name="revenue", category="income", values={2020: 1000, 2021: None, 2022: 1200})
        costs = LineItem(name="costs", category="expenses", values={2020: None, 2021: 600, 2022: 700})
        
        # Item with formula (will fail when referencing None values)
        margin = LineItem(name="margin", category="calculated", formula="revenue - costs")
        
        # Model should work for years where formulas don't reference None
        model = Model(
            line_items=[revenue, costs, margin],
            categories=[Category(name="income"), Category(name="expenses"), Category(name="calculated")],
            years=[2022]  # Only year where both revenue and costs are not None
        )
        
        # Check the calculation works
        assert model["margin", 2022] == 500  # 1200 - 700
        
        # Check category totals handle None correctly by creating model with all years for non-formula items
        simple_model = Model(
            line_items=[revenue, costs],  # No formula items
            categories=[Category(name="income"), Category(name="expenses")],
            years=[2020, 2021, 2022]
        )
        
        # Category totals should treat None as 0
        assert simple_model["total_income", 2020] == 1000  # revenue: 1000, None treated as 0
        assert simple_model["total_income", 2021] == 0     # revenue: None treated as 0
        assert simple_model["total_expenses", 2020] == 0   # costs: None treated as 0
        assert simple_model["total_expenses", 2021] == 600 # costs: 600










