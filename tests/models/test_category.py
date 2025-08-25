import pytest

from pyproforma.models.category import Category


class TestCategory:
    @pytest.mark.parametrize(
        "name", ["ValidName", "valid_name", "valid-name", "A", "a_b-c", "a1"]
    )
    def test_item_type_validate_name_accepts_valid_names(self, name):
        # Should not raise
        Category(name=name)

    @pytest.mark.parametrize(
        "name",
        [
            "invalid name",  # contains space
            "invalid$name",  # contains special character $
            "invalid.name",  # contains dot
            "invalid@name",  # contains @
            "invalid/name",  # contains /
            "invalid,name",  # contains comma
            "invalid*name",  # contains *
            "invalid!name",  # contains !
            "invalid#name",  # contains #
            "invalid%name",  # contains %
            "invalid^name",  # contains ^
            "invalid&name",  # contains &
            "invalid(name)",  # contains parentheses
            "invalid+name",  # contains +
            "invalid=name",  # contains =
            "invalid~name",  # contains ~
            "invalid`name",  # contains `
            "invalid|name",  # contains |
            "invalid\\name",  # contains backslash
            "invalid'name",  # contains apostrophe
            'invalid"name',  # contains quote
        ],
    )
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
            include_total=True,
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
            include_total=False,
        )
        assert category.include_total is False
        assert category.label == "Operating Expenses"
        assert category.total_name is None
        assert category.total_label is None

    def test_category_str_representation_with_include_total_true(self):
        category = Category(name="revenue", label="Revenue")
        expected = "Category(name='revenue', label='Revenue', total_label='Total Revenue', total_name='total_revenue', include_total=True)"  # noqa: E501
        assert str(category) == expected

    def test_category_str_representation_with_include_total_false(self):
        category = Category(name="expense", include_total=False)
        expected = "Category(name='expense', label='expense', total_label='None', total_name='None', include_total=False)"  # noqa: E501
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
            include_total=True,
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
            name="no_total_category", label="No Total Category", include_total=False
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

    def test_category_rejects_reserved_names(self):
        """Test that Category rejects reserved names like 'category_totals'."""
        with pytest.raises(ValueError) as excinfo:
            Category(name="category_totals")
        assert "is reserved and cannot be used" in str(excinfo.value)
        assert "category_totals" in str(excinfo.value)

    def test_category_allows_non_reserved_names(self):
        """Test that Category allows valid non-reserved names."""
        # This should work fine
        category = Category(name="my_category")
        assert category.name == "my_category"
