import pytest

from pyproforma import LineItem, Model
from pyproforma.models.line_item import _is_values_dict, _validate_values_keys


@pytest.fixture
def sample_line_item() -> LineItem:
    return LineItem(
        name="test_item",
        label="Test Item",
        category="revenue",
        values={2020: 1.0, 2021: 2.0},
    )


class TestLineItemInit:
    def test_line_item_init(self, sample_line_item: LineItem):
        item = sample_line_item
        assert item.name == "test_item"
        assert item.label == "Test Item"
        assert item.category == "revenue"
        assert item.values == {2020: 1.0, 2021: 2.0}

    def test_line_item_init_with_label(self, sample_line_item: LineItem):
        item = sample_line_item
        assert item.name == "test_item"
        assert item.label == "Test Item"
        assert item.category == "revenue"
        assert item.values == {2020: 1.0, 2021: 2.0}

    def test_line_item_init_without_label(self):
        item = LineItem(
            name="default_label_item", category="expense", values={2020: 3.0, 2021: 4.0}
        )
        assert item.label is None

    def test_line_item_init_with_default_category(self):
        """Test that LineItem uses 'general' as default category when not specified."""
        item = LineItem(name="default_category_item", values={2020: 5.0, 2021: 6.0})
        assert item.category == "general"
        assert item.name == "default_category_item"
        assert item.values == {2020: 5.0, 2021: 6.0}

    def test_no_values(self):
        item = LineItem(
            name="no_values_item", label="No Values Item", category="revenue"
        )
        assert item.values is None

    def test_values_can_contain_none(self):
        # Test that None values are now allowed
        item = LineItem(
            name="test_item",
            label="Test Item",
            category="revenue",
            values={2020: 1.0, 2021: None, 2022: 3.0},
        )
        assert item.values[2021] is None

        # Test with single None value
        item2 = LineItem(name="test_item2", category="expense", values={2020: None})
        assert item2.values[2020] is None

    def test_values_keys_must_be_integers(self):
        """Test that values dictionary keys must be integers (years)."""
        # String keys should raise ValueError
        with pytest.raises(ValueError) as excinfo:
            LineItem(
                name="string_keys",
                category="revenue",
                values={"2020": 100.0, "2021": 200.0},
            )
        error_msg = str(excinfo.value)
        assert "must be an integer (year)" in error_msg
        assert "got str" in error_msg

        # Float keys should raise ValueError
        with pytest.raises(ValueError) as excinfo:
            LineItem(
                name="float_keys",
                category="revenue",
                values={2020.5: 100.0, 2021: 200.0},
            )
        error_msg = str(excinfo.value)
        assert "must be an integer (year)" in error_msg
        assert "got float" in error_msg

        # Mixed key types should raise ValueError
        with pytest.raises(ValueError) as excinfo:
            LineItem(
                name="mixed_keys",
                category="revenue",
                values={2020: 100.0, "2021": 200.0},
            )
        error_msg = str(excinfo.value)
        assert "must be an integer (year)" in error_msg
        assert "got str" in error_msg


class TestLineItemMisc:
    def test_validate_sorted_and_sequential_accepts_sequential_years(
        self, sample_line_item: LineItem
    ):
        LineItem(
            name="test",
            label="Test",
            category="test",
            values={2000: 1.0, 2001: 2.0, 2002: 3.0, 2003: 4.0},
        )
        # No exception should be raised

    def test_validate_sorted_and_sequential_accepts_single_year(self):
        LineItem(name="test", label="Test", category="test", values={2020: 1.0})
        # No exception should be raised

    def test_validate_names_accepts_unique_names(self):
        items = [
            LineItem(name="a", label="A", category="type1", values={2020: 1.0}),
            LineItem(name="b", label="B", category="type2", values={2020: 2.0}),
            LineItem(name="c", label="C", category="type3", values={2020: 3.0}),
        ]
        Model(items, years=[2020])

    def test_validate_names_raises_for_duplicate_names(self):
        items = [
            LineItem(name="a", label="A", category="type1", values={2020: 1.0}),
            LineItem(name="a", label="A2", category="type2", values={2020: 2.0}),
        ]
        with pytest.raises(ValueError) as excinfo:
            Model(items, years=[2020])
        assert "Duplicate" in str(excinfo.value)

    def test_line_item_from_dict_basic(self):
        data = {
            "name": "item1",
            "label": "Item 1",
            "category": "revenue",
            "values": {2020: 10.0, 2021: 20.0},
        }
        item = LineItem.from_dict(data)
        assert item.name == "item1"
        assert item.label == "Item 1"
        assert item.category == "revenue"
        assert item.values == {2020: 10.0, 2021: 20.0}

    def test_line_item_from_dict_label_is_none(self):
        data = {"name": "item2", "category": "expense", "values": {2020: 5.0}}
        item = LineItem.from_dict(data)
        assert item.name == "item2"
        assert item.label is None
        assert item.category == "expense"
        assert item.values == {2020: 5.0}

    def test_line_item_from_dict_ignores_non_year_keys(self):
        data = {
            "name": "item3",
            "label": "Item 3",
            "category": "other",
            "values": {2020: 1.0, 2021: 2.0},
            "extra": "should be ignored",
        }
        item = LineItem.from_dict(data)
        assert item.name == "item3"
        assert item.label == "Item 3"
        assert item.category == "other"
        assert item.values == {2020: 1.0, 2021: 2.0}

    def test_line_item_from_dict_raises_for_missing_name(self):
        data = {"label": "Missing Name", "category": "revenue", "values": {2020: 1.0}}
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
            value_format="currency",
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


class TestLineItemNoneValues:
    """Test class specifically for None value functionality in LineItems."""

    def test_line_item_accepts_none_values(self):
        """Test that LineItem can be created with None values in values dict."""
        item = LineItem(
            name="test_none",
            category="revenue",
            values={2020: 100.0, 2021: None, 2022: 200.0},
        )
        assert item.values[2020] == 100.0
        assert item.values[2021] is None
        assert item.values[2022] == 200.0

    def test_line_item_all_none_values(self):
        """Test LineItem with all None values."""
        item = LineItem(
            name="all_none",
            category="revenue",
            values={2020: None, 2021: None, 2022: None},
        )
        assert all(value is None for value in item.values.values())

    def test_formula_error_with_none_values(self):
        """Test that formulas treat None values as zero."""
        from pyproforma import Category, Model

        base_item = LineItem(
            name="base", category="test", values={2020: 100.0, 2021: None}
        )
        calc_item = LineItem(name="calculated", category="test", formula="base * 2")

        # Model creation should work for all years now that None is treated as 0
        model = Model(
            line_items=[base_item, calc_item],
            categories=[Category(name="test")],
            years=[2020, 2021],  # Both years should work now
        )

        # This should work fine
        assert model["calculated", 2020] == 200.0  # 100.0 * 2

        # This should now work too, treating None as 0
        assert model["calculated", 2021] == 0.0  # None (treated as 0) * 2 = 0

    def test_serialization_preserves_none_values(self):
        """Test that to_dict and from_dict preserve None values correctly."""
        original = LineItem(
            name="serialize_test",
            category="revenue",
            values={2020: 100.0, 2021: None, 2022: 200.0},
            formula="test_formula",
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
        from pyproforma.models.model.value_matrix import calculate_line_item_value

        item = LineItem(
            name="complex_test",
            category="revenue",
            values={2020: 100.0, 2021: None, 2023: 300.0},  # Gap at 2022
            formula="complex_test[-1] * 1.1",
        )

        interim_values = {}

        # 2020: explicit value
        assert (
            calculate_line_item_value(
                item.values, item.formula, interim_values, 2020, item.name
            )
            == 100.0
        )

        # 2021: None value should now use formula, but formula would reference 2020
        interim_values = {2020: {"complex_test": 100.0}}
        result_2021 = calculate_line_item_value(
            item.values, item.formula, interim_values, 2021, item.name
        )
        assert result_2021 == pytest.approx(110.0)  # 100.0 * 1.1

        # 2022: no explicit value, should use formula with 2021 value
        interim_values = {2021: {"complex_test": 110.0}}
        result_2022 = calculate_line_item_value(
            item.values, item.formula, interim_values, 2022, item.name
        )
        assert result_2022 == pytest.approx(121.0)  # 110.0 * 1.1

        # 2023: explicit value (should override formula)
        assert (
            calculate_line_item_value(item.values, item.formula, {}, 2023, item.name)
            == 300.0
        )


class TestValidateValuesKeys:
    """Test class for the _validate_values_keys function."""

    def test_validate_values_keys_with_none(self):
        """Test that None values dictionary is accepted."""
        # Should not raise any exception
        _validate_values_keys(None)

    def test_validate_values_keys_with_empty_dict(self):
        """Test that empty dictionary is accepted."""
        # Should not raise any exception
        _validate_values_keys({})

    def test_validate_values_keys_with_valid_integer_keys(self):
        """Test that dictionary with integer keys is accepted."""
        values = {2020: 100.0, 2021: 200.0, 2022: None, 2023: 300.0}
        # Should not raise any exception
        _validate_values_keys(values)

    def test_validate_values_keys_rejects_string_keys(self):
        """Test that string keys are rejected."""
        values = {"2020": 100.0, "2021": 200.0}
        with pytest.raises(ValueError) as excinfo:
            _validate_values_keys(values)

        error_msg = str(excinfo.value)
        assert "must be an integer (year)" in error_msg
        assert "got str" in error_msg

    def test_validate_values_keys_rejects_float_keys(self):
        """Test that float keys are rejected."""
        values = {2020.5: 100.0, 2021: 200.0}
        with pytest.raises(ValueError) as excinfo:
            _validate_values_keys(values)

        error_msg = str(excinfo.value)
        assert "must be an integer (year)" in error_msg
        assert "got float" in error_msg

    def test_validate_values_keys_rejects_mixed_key_types(self):
        """Test that mixed key types are rejected."""
        values = {2020: 100.0, "2021": 200.0}
        with pytest.raises(ValueError) as excinfo:
            _validate_values_keys(values)

        error_msg = str(excinfo.value)
        assert "must be an integer (year)" in error_msg
        assert "got str" in error_msg

    def test_validate_values_keys_error_message_includes_key_value(self):
        """Test that error message includes the problematic key value."""
        values = {"invalid_year": 100.0}
        with pytest.raises(ValueError) as excinfo:
            _validate_values_keys(values)

        error_msg = str(excinfo.value)
        assert "'invalid_year'" in error_msg
        assert "must be an integer (year)" in error_msg

    def test_validate_values_keys_accepts_boolean_keys(self):
        """Test that boolean keys are accepted since bool is subclass of int."""
        # This should work because isinstance(True, int) returns True in Python
        values = {True: 100.0, False: 200.0}
        # Should not raise any exception
        _validate_values_keys(values)

    def test_validate_values_keys_with_various_invalid_types(self):
        """Test various invalid key types."""
        # Test None key
        with pytest.raises(ValueError) as excinfo:
            _validate_values_keys({None: 100.0})
        assert "got NoneType" in str(excinfo.value)

        # Test tuple key
        with pytest.raises(ValueError) as excinfo:
            _validate_values_keys({(2020,): 100.0})
        assert "got tuple" in str(excinfo.value)

        # Test list key (unhashable type will cause TypeError, but let's test dict key)
        with pytest.raises(ValueError) as excinfo:
            _validate_values_keys({"key": 100.0})
        assert "got str" in str(excinfo.value)

    def test_validate_values_keys_integration_with_line_item(self):
        """Test that LineItem creation properly validates values keys."""
        # Valid integer keys should work
        item = LineItem(
            name="test_valid", category="revenue", values={2020: 100.0, 2021: 200.0}
        )
        assert item.values == {2020: 100.0, 2021: 200.0}

        # Invalid string keys should raise ValueError during LineItem creation
        with pytest.raises(ValueError) as excinfo:
            LineItem(
                name="test_invalid",
                category="revenue",
                values={"2020": 100.0, "2021": 200.0},
            )

        error_msg = str(excinfo.value)
        assert "must be an integer (year)" in error_msg


class TestLineItemCategoryValidation:
    """Test validation of LineItem category parameter."""

    def test_category_none_defaults_to_general(self):
        """Test that LineItem defaults category to 'general' when None is provided."""
        item = LineItem(name="test_item", category=None, values={2023: 100})
        assert item.category == "general"

    def test_category_must_be_string(self):
        """Test that LineItem raises TypeError when category is not a string."""
        with pytest.raises(
            TypeError, match="LineItem category must be a string, got int"
        ):
            LineItem(name="test_item", category=123, values={2023: 100})

        with pytest.raises(
            TypeError, match="LineItem category must be a string, got list"
        ):
            LineItem(name="test_item", category=["income"], values={2023: 100})

        with pytest.raises(
            TypeError, match="LineItem category must be a string, got dict"
        ):
            LineItem(name="test_item", category={"name": "income"}, values={2023: 100})

        with pytest.raises(
            TypeError, match="LineItem category must be a string, got bool"
        ):
            LineItem(name="test_item", category=True, values={2023: 100})

    def test_valid_string_categories_accepted(self):
        """Test that valid string categories are accepted."""
        # Normal category
        item1 = LineItem(name="test1", category="income", values={2023: 100})
        assert item1.category == "income"

        # Empty string should be allowed (no longer validates whitespace)
        item2 = LineItem(name="test2", category="", values={2023: 100})
        assert item2.category == ""

        # Whitespace category should be allowed
        item3 = LineItem(name="test3", category="  spaces  ", values={2023: 100})
        assert item3.category == "  spaces  "

        # Special characters in category name
        item4 = LineItem(name="test4", category="income-tax", values={2023: 100})
        assert item4.category == "income-tax"

        # Unicode characters
        item5 = LineItem(name="test5", category="收入", values={2023: 100})
        assert item5.category == "收入"

    def test_default_category_still_works(self):
        """Test that the default 'general' category works when no category provided."""
        item = LineItem(name="test_item", values={2023: 100})
        assert item.category == "general"

    def test_category_validation_with_from_dict(self):
        """Test that category validation works with from_dict method."""
        # Valid string category
        item1 = LineItem.from_dict(
            {"name": "test1", "category": "income", "values": {2023: 100}}
        )
        assert item1.category == "income"

        # None category should default to "general" in from_dict and direct construction
        item2 = LineItem.from_dict(
            {"name": "test2", "category": None, "values": {2023: 100}}
        )
        assert item2.category == "general"

        # Also test direct construction with None
        item2b = LineItem(name="test2b", category=None, values={2023: 100})
        assert item2b.category == "general"

        # Empty string category should default to "general" in from_dict
        item3 = LineItem.from_dict(
            {"name": "test3", "category": "", "values": {2023: 100}}
        )
        assert item3.category == "general"

        # Missing category should default to "general" in from_dict
        item4 = LineItem.from_dict({"name": "test4", "values": {2023: 100}})
        assert item4.category == "general"


class TestIsValuesDict:
    """Test the _is_values_dict function."""

    def test_valid_values_dictionary_integers(self):
        """Test that valid values dictionaries with integers return True."""
        # Basic case
        assert _is_values_dict({2023: 100, 2024: 200}) is True

        # Single year
        assert _is_values_dict({2023: 100}) is True

        # Multiple years with different integers
        assert _is_values_dict({2020: 50, 2021: 75, 2022: 100, 2023: 125}) is True

    def test_valid_values_dictionary_floats(self):
        """Test that valid values dictionaries with floats return True."""
        assert _is_values_dict({2023: 100.5, 2024: 200.75}) is True
        assert _is_values_dict({2023: 0.0, 2024: 1.5}) is True

    def test_valid_values_dictionary_mixed_numeric(self):
        """Test that valid values dictionaries with mixed numeric types return True."""
        assert _is_values_dict({2023: 100, 2024: 200.5}) is True
        assert _is_values_dict({2023: 100.0, 2024: 200}) is True

    def test_valid_values_dictionary_with_none(self):
        """Test that values dictionaries with None values return True."""
        assert _is_values_dict({2023: 100, 2024: None}) is True
        assert _is_values_dict({2023: None, 2024: 200}) is True
        assert _is_values_dict({2023: None, 2024: None}) is True

    def test_valid_values_dictionary_negative_years(self):
        """Test that values dictionaries work with negative years."""
        assert _is_values_dict({-1: 100, 0: 200, 1: 300}) is True
        assert _is_values_dict({-2023: 100}) is True

    def test_empty_dictionary(self):
        """Test that empty dictionaries return False."""
        assert _is_values_dict({}) is False

    def test_invalid_non_integer_keys(self):
        """Test that dictionaries with non-integer keys return False."""
        # String keys
        assert _is_values_dict({"2023": 100, "2024": 200}) is False
        assert _is_values_dict({"name": "revenue", "category": "income"}) is False

        # Float keys
        assert _is_values_dict({2023.0: 100, 2024.0: 200}) is False

        # Mixed key types
        assert _is_values_dict({2023: 100, "2024": 200}) is False

    def test_valid_values_dictionary_booleans(self):
        """Test that values dictionaries with boolean values return True."""
        assert _is_values_dict({2023: True, 2024: False}) is True
        assert _is_values_dict({2023: True}) is True
        assert _is_values_dict({2023: False, 2024: True, 2025: False}) is True

    def test_invalid_non_numeric_values(self):
        """Test that dictionaries with non-numeric values return False."""
        # String values
        assert _is_values_dict({2023: "100", 2024: "200"}) is False
        assert _is_values_dict({2023: "revenue"}) is False

        # List values
        assert _is_values_dict({2023: [100, 200]}) is False

        # Dict values
        assert _is_values_dict({2023: {"value": 100}}) is False

    def test_lineitem_parameter_dictionaries(self):
        """Test that LineItem parameter dictionaries return False."""
        # Basic LineItem parameters
        assert _is_values_dict({"name": "revenue", "category": "income"}) is False
        assert (
            _is_values_dict({"name": "expenses", "formula": "revenue * 0.8"}) is False
        )

        # Full LineItem parameters
        assert (
            _is_values_dict(
                {
                    "name": "revenue",
                    "category": "income",
                    "label": "Total Revenue",
                    "formula": "1000",
                    "value_format": "no_decimals",
                }
            )
            is False
        )

        # LineItem parameters with values key
        assert (
            _is_values_dict(
                {
                    "name": "revenue",
                    "category": "income",
                    "values": {2023: 100, 2024: 200},
                }
            )
            is False
        )

    def test_mixed_valid_invalid_cases(self):
        """Test edge cases with mixed valid/invalid elements."""
        # Mix of numeric and non-numeric values
        assert _is_values_dict({2023: 100, 2024: "invalid"}) is False

        # Mix of integer and non-integer keys
        assert _is_values_dict({2023: 100, "invalid": 200}) is False

    def test_special_numeric_values(self):
        """Test with special numeric values."""
        # Zero values
        assert _is_values_dict({2023: 0, 2024: 0.0}) is True

        # Negative values
        assert _is_values_dict({2023: -100, 2024: -200.5}) is True

        # Large values
        assert _is_values_dict({2023: 1000000, 2024: 1e6}) is True

        # Very small values
        assert _is_values_dict({2023: 0.001, 2024: 1e-10}) is True
