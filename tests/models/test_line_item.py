import pytest

from pyproforma import LineItem, Model


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
        assert item.label == "default_label_item"

    def test_no_values(self):
        item = LineItem(
            name="no_values_item", label="No Values Item", category="revenue"
        )
        assert item.values == {}

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

    def test_item_type_total_basic(self):
        items = [
            LineItem(
                name="a", label="A", category="revenue", values={2020: 10.0, 2021: 20.0}
            ),
            LineItem(
                name="b", label="B", category="revenue", values={2020: 5.0, 2021: 15.0}
            ),
            LineItem(
                name="c", label="C", category="expense", values={2020: 3.0, 2021: 7.0}
            ),
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

    def test_line_item_from_dict_label_defaults_to_name(self):
        data = {"name": "item2", "category": "expense", "values": {2020: 5.0}}
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


class TestIsHardcoded:
    """Test class for the is_hardcoded method."""

    def test_is_hardcoded_returns_true_when_year_in_values(self):
        """Test that is_hardcoded returns True when year exists in values dict."""
        item = LineItem(
            name="test_item",
            category="revenue",
            values={2020: 100.0, 2021: 200.0, 2022: None},
        )

        assert item.is_hardcoded(2020) is True
        assert item.is_hardcoded(2021) is True
        assert (
            item.is_hardcoded(2022) is True
        )  # Even None values are considered hardcoded

    def test_is_hardcoded_returns_false_when_year_not_in_values(self):
        """Test that is_hardcoded returns False when year doesn't exist in values dict."""  # noqa: E501
        item = LineItem(
            name="test_item", category="revenue", values={2020: 100.0, 2021: 200.0}
        )

        assert item.is_hardcoded(2019) is False
        assert item.is_hardcoded(2022) is False
        assert item.is_hardcoded(2025) is False

    def test_is_hardcoded_with_empty_values(self):
        """Test that is_hardcoded returns False when values dict is empty."""
        item = LineItem(name="test_item", category="revenue")

        assert item.is_hardcoded(2020) is False
        assert item.is_hardcoded(2021) is False

    def test_is_hardcoded_with_formula_item(self):
        """Test that is_hardcoded works correctly for items with formulas."""
        item = LineItem(
            name="test_item",
            category="revenue",
            values={2020: 100.0},  # Only hardcoded for 2020
            formula="test_item[-1] * 1.1",
        )

        assert item.is_hardcoded(2020) is True  # Has explicit value
        assert item.is_hardcoded(2021) is False  # Would use formula
        assert item.is_hardcoded(2022) is False  # Would use formula

    def test_is_hardcoded_with_mixed_none_and_numeric_values(self):
        """Test is_hardcoded with mixed None and numeric values."""
        item = LineItem(
            name="mixed_item",
            category="revenue",
            values={2020: 100.0, 2021: None, 2022: 200.0},
        )

        assert item.is_hardcoded(2020) is True
        assert item.is_hardcoded(2021) is True  # None is still considered hardcoded
        assert item.is_hardcoded(2022) is True
        assert item.is_hardcoded(2023) is False  # Not in values

    def test_is_hardcoded_different_year_types(self):
        """Test is_hardcoded with different year value types."""
        item = LineItem(name="test_item", category="revenue", values={2020: 100.0})

        # Test with different integer representations
        assert item.is_hardcoded(2020) is True
        assert item.is_hardcoded(int(2020)) is True

        # Test with years not in values
        assert item.is_hardcoded(2019) is False
        assert item.is_hardcoded(2021) is False


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

    def test_none_values_in_model_category_totals(self):
        """Test that None values are treated as 0 in category totals."""
        from pyproforma import Category, Model

        items = [
            LineItem(
                name="item1", category="revenue", values={2020: 100.0, 2021: None}
            ),
            LineItem(
                name="item2", category="revenue", values={2020: None, 2021: 200.0}
            ),
            LineItem(name="item3", category="revenue", values={2020: 50.0, 2021: 75.0}),
        ]

        model = Model(
            line_items=items, categories=[Category(name="revenue")], years=[2020, 2021]
        )

        # 2020: 100 + 0 + 50 = 150 (None treated as 0)
        assert model["total_revenue", 2020] == 150.0

        # 2021: 0 + 200 + 75 = 275 (None treated as 0)
        assert model["total_revenue", 2021] == 275.0

    def test_formula_error_with_none_values(self):
        """Test that formulas raise proper errors when referencing None values."""
        from pyproforma import Category, Model

        base_item = LineItem(
            name="base", category="test", values={2020: 100.0, 2021: None}
        )
        calc_item = LineItem(name="calculated", category="test", formula="base * 2")

        # Model creation should work for years without None formula references
        model = Model(
            line_items=[base_item, calc_item],
            categories=[Category(name="test")],
            years=[2020],  # Only year that works
        )

        # This should work fine
        assert model["calculated", 2020] == 200.0

        # But creating a model that includes a year with None formula reference should fail  # noqa: E501
        with pytest.raises(ValueError) as excinfo:
            Model(
                line_items=[base_item, calc_item],
                categories=[Category(name="test")],
                years=[2020, 2021],  # 2021 will fail due to None in formula
            )

        error_msg = str(excinfo.value)
        assert "has None value for year 2021" in error_msg
        assert "Cannot use None values in formulas" in error_msg

    def test_formula_error_with_offset_none_values(self):
        """Test formula errors when offset references point to None values."""
        from pyproforma.models.formula import calculate_formula

        # Test offset reference to None value
        value_matrix = {2019: {"revenue": None}, 2020: {"revenue": 100.0}}

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

        # 2021: explicit None value
        assert (
            calculate_line_item_value(
                item.values, item.formula, interim_values, 2021, item.name
            )
            is None
        )

        # 2022: no explicit value, should use formula with 2021 value
        interim_values = {2021: {"complex_test": None}}
        with pytest.raises(ValueError) as excinfo:
            calculate_line_item_value(
                item.values, item.formula, interim_values, 2022, item.name
            )
        assert "has None value for year 2021" in str(excinfo.value)

        # 2023: explicit value (should override formula)
        assert (
            calculate_line_item_value(item.values, item.formula, {}, 2023, item.name)
            == 300.0
        )

    def test_none_values_in_complex_model(self):
        """Test None values in a more complex model scenario."""
        from pyproforma import Category, Model

        # Create items with None values
        revenue = LineItem(
            name="revenue",
            category="income",
            values={2020: 1000, 2021: None, 2022: 1200},
        )
        costs = LineItem(
            name="costs", category="expenses", values={2020: None, 2021: 600, 2022: 700}
        )

        # Item with formula (will fail when referencing None values)
        margin = LineItem(
            name="margin", category="calculated", formula="revenue - costs"
        )

        # Model should work for years where formulas don't reference None
        model = Model(
            line_items=[revenue, costs, margin],
            categories=[
                Category(name="income"),
                Category(name="expenses"),
                Category(name="calculated"),
            ],
            years=[2022],  # Only year where both revenue and costs are not None
        )

        # Check the calculation works
        assert model["margin", 2022] == 500  # 1200 - 700

        # Check category totals handle None correctly by creating model with all years for non-formula items  # noqa: E501
        simple_model = Model(
            line_items=[revenue, costs],  # No formula items
            categories=[Category(name="income"), Category(name="expenses")],
            years=[2020, 2021, 2022],
        )

        # Category totals should treat None as 0
        assert (
            simple_model["total_income", 2020] == 1000
        )  # revenue: 1000, None treated as 0
        assert simple_model["total_income", 2021] == 0  # revenue: None treated as 0
        assert simple_model["total_expenses", 2020] == 0  # costs: None treated as 0
        assert simple_model["total_expenses", 2021] == 600  # costs: 600
