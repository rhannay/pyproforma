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
        assert "Name must only contain" in str(excinfo.value)

    def test_category_with_label(self):
        category = Category(name="revenue", label="Revenue Sources")
        assert category.name == "revenue"
        assert category.label == "Revenue Sources"

    def test_category_without_label(self):
        category = Category(name="revenue")
        assert category.name == "revenue"
        assert category.label is None

    def test_category_repr_same_as_str(self):
        category = Category(name="revenue")
        assert repr(category) == str(category)

        category_with_label = Category(name="expense", label="Expenses")
        assert repr(category_with_label) == str(category_with_label)

    def test_category_serialization_round_trip(self):
        """Test that to_dict -> from_dict preserves all Category data."""
        original = Category(
            name="test_category",
            label="Test Category",
        )

        # Convert to dict and back
        data = original.to_dict()
        reconstructed = Category.from_dict(data)

        # Verify all attributes are preserved
        assert reconstructed.name == original.name
        assert reconstructed.label == original.label

    def test_category_serialization_round_trip_no_label(self):
        """Test serialization round trip for Category without label."""
        original = Category(
            name="no_label_category"
        )

        # Convert to dict and back
        data = original.to_dict()
        reconstructed = Category.from_dict(data)

        # Verify all attributes are preserved
        assert reconstructed.name == original.name
        assert reconstructed.label is None

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
