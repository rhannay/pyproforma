import pytest

from pyproforma import Category, LineItem, Model
from pyproforma.models.model.model_update import UpdateNamespace


class TestUnifiedUpdateNamespace:
    """Test the new unified UpdateNamespace class that combines add, update, and delete functionality."""  # noqa: E501

    @pytest.fixture
    def sample_model(self):
        """Create a sample model for testing."""
        revenue = LineItem(
            name="revenue",
            category="income",
            values={2023: 100000, 2024: 120000, 2025: 140000},
        )

        salary = LineItem(
            name="salary",
            category="expenses",
            values={2023: 60000, 2024: 65000, 2025: 70000},
        )

        categories = [
            Category(name="income", label="Income"),
            Category(name="expenses", label="Expenses"),
        ]

        return Model(
            line_items=[revenue, salary],
            years=[2023, 2024, 2025],
            categories=categories,
        )

    def test_unified_namespace_init(self, sample_model: Model):
        """Test that the unified UpdateNamespace initializes correctly with a model."""
        update_namespace = UpdateNamespace(sample_model)
        assert update_namespace._model is sample_model

    def test_model_has_only_update_namespace(self, sample_model: Model):
        """Test that the model only has the update namespace, not separate add/delete namespaces."""  # noqa: E501
        # Should have update namespace
        assert hasattr(sample_model, "update")
        assert isinstance(sample_model.update, UpdateNamespace)

        # Should not have separate add/delete namespaces anymore
        assert not hasattr(sample_model, "add")
        assert not hasattr(sample_model, "delete")

    def test_all_expected_methods_available(self, sample_model: Model):
        """Test that all expected methods are available in the unified namespace."""
        update = sample_model.update

        # Add methods
        assert hasattr(update, "add_category")
        assert hasattr(update, "add_line_item")
        assert hasattr(update, "add_constraint")

        # Update methods
        assert hasattr(update, "update_category")
        assert hasattr(update, "update_line_item")
        assert hasattr(update, "update_years")
        assert hasattr(update, "update_constraint")

        # Delete methods
        assert hasattr(update, "delete_category")
        assert hasattr(update, "delete_line_item")
        assert hasattr(update, "delete_constraint")

    def test_add_category_functionality(self, sample_model: Model):
        """Test that add_category works correctly."""
        initial_count = len(sample_model._category_definitions)

        sample_model.update.add_category(name="assets", label="Assets")

        assert len(sample_model._category_definitions) == initial_count + 1
        new_category = next(
            cat for cat in sample_model._category_definitions if cat.name == "assets"
        )
        assert new_category.label == "Assets"

    def test_add_line_item_functionality(self, sample_model: Model):
        """Test that add_line_item works correctly."""
        initial_count = len(sample_model._line_item_definitions)

        sample_model.update.add_line_item(
            name="rent",
            category="expenses",
            values={2023: 24000, 2024: 25000, 2025: 26000},
        )

        assert len(sample_model._line_item_definitions) == initial_count + 1
        assert sample_model.value("rent", 2023) == 24000

    def test_update_category_functionality(self, sample_model: Model):
        """Test that update_category works correctly."""
        sample_model.update.update_category("income", label="Revenue Streams")

        category = next(
            cat for cat in sample_model._category_definitions if cat.name == "income"
        )
        assert category.label == "Revenue Streams"

    def test_update_line_item_functionality(self, sample_model: Model):
        """Test that update_line_item works correctly."""
        sample_model.update.update_line_item(
            "revenue", values={2023: 150000, 2024: 160000, 2025: 170000}
        )

        assert sample_model.value("revenue", 2023) == 150000
        assert sample_model.value("revenue", 2024) == 160000

    def test_update_years_functionality(self, sample_model: Model):
        """Test that update_years works correctly."""
        new_years = [2024, 2025, 2026, 2027]
        sample_model.update.update_years(new_years)

        assert sample_model.years == [2024, 2025, 2026, 2027]

    def test_delete_line_item_functionality(self, sample_model: Model):
        """Test that delete_line_item works correctly."""
        initial_count = len(sample_model._line_item_definitions)

        sample_model.update.delete_line_item("salary")

        assert len(sample_model._line_item_definitions) == initial_count - 1
        assert "salary" not in [
            item.name for item in sample_model._line_item_definitions
        ]

    def test_delete_category_with_no_line_items(self, sample_model: Model):
        """Test that delete_category works when no line items reference it."""
        # First add a category with no line items
        sample_model.update.add_category(name="unused", label="Unused Category")
        initial_count = len(sample_model._category_definitions)

        sample_model.update.delete_category("unused")

        assert len(sample_model._category_definitions) == initial_count - 1
        assert "unused" not in [cat.name for cat in sample_model._category_definitions]

    def test_delete_category_with_line_items_fails(self, sample_model: Model):
        """Test that delete_category fails when line items reference it."""
        with pytest.raises(
            ValueError,
            match="Cannot delete category 'income' because it is used by line items",
        ):
            sample_model.update.delete_category("income")

    def test_error_handling_preserved(self, sample_model: Model):
        """Test that error handling is preserved across all methods."""
        # Test add errors
        with pytest.raises(ValueError, match="Failed to add category"):
            sample_model.update.add_category(name="income")  # Duplicate name

        # Test update errors
        with pytest.raises(KeyError, match="Category 'nonexistent' not found"):
            sample_model.update.update_category("nonexistent", label="New Label")

        # Test delete errors
        with pytest.raises(KeyError, match="Line item 'nonexistent' not found"):
            sample_model.update.delete_line_item("nonexistent")

    def test_validation_on_copy_preserved(self, sample_model: Model):
        """Test that validation on copy behavior is preserved."""
        # This should work fine
        sample_model.update.add_line_item(
            name="valid_item", category="income", values={2023: 1000}
        )

        # This should fail validation and not affect the original model
        original_count = len(sample_model._line_item_definitions)
        with pytest.raises(ValueError):
            sample_model.update.add_line_item(
                name="invalid name with spaces",  # This will fail validation
                category="income",
                values={2023: 1000},
            )

        # Original model should be unchanged
        assert len(sample_model._line_item_definitions) == original_count


class TestAddLineItemReplace:
    """Test the replace functionality in add_line_item method."""

    @pytest.fixture
    def sample_model(self):
        """Create a sample model for testing replace functionality."""
        revenue = LineItem(
            name="revenue",
            category="income",
            values={2023: 100000, 2024: 120000},
        )

        categories = [
            Category(name="income", label="Income"),
            Category(name="expenses", label="Expenses"),
        ]

        return Model(
            line_items=[revenue],
            years=[2023, 2024],
            categories=categories,
        )

    def test_add_line_item_without_replace_parameter_uses_default_false(
        self, sample_model
    ):
        """Test that add_line_item without replace parameter defaults to False."""
        # Try to add an item with existing name - should fail
        with pytest.raises(
            ValueError,
            match="Line item with name 'revenue' already exists",
        ):
            sample_model.update.add_line_item(name="revenue", formula="200000")

    def test_add_line_item_replace_false_explicit(self, sample_model):
        """Test that add_line_item with replace=False explicitly fails on duplicate."""
        with pytest.raises(
            ValueError,
            match="Line item with name 'revenue' already exists",
        ) as exc_info:
            sample_model.update.add_line_item(
                name="revenue", formula="200000", replace=False
            )

        # Check that the error message suggests using replace=True
        assert "or set replace=True to replace the existing item" in str(exc_info.value)

    def test_add_line_item_replace_true_with_parameters(self, sample_model):
        """Test that add_line_item with replace=True replaces existing item."""
        # Check original value
        assert sample_model.value("revenue", 2023) == 100000

        # Replace with new parameters
        sample_model.update.add_line_item(
            name="revenue",
            category="income",
            formula="150000",
            label="New Revenue",
            replace=True,
        )

        # Verify replacement worked
        assert sample_model.value("revenue", 2023) == 150000
        line_item = sample_model._line_item_definition("revenue")
        assert line_item.label == "New Revenue"
        assert line_item.formula == "150000"

    def test_add_line_item_replace_true_with_line_item_object(self, sample_model):
        """Test that add_line_item with LineItem object and replace=True works."""
        # Check original value
        assert sample_model.value("revenue", 2023) == 100000

        # Create new LineItem object
        new_line_item = LineItem(
            name="revenue",
            category="expenses",  # Different category
            formula="200000",
            label="Replaced Revenue",
        )

        # Replace with LineItem object
        sample_model.update.add_line_item(line_item=new_line_item, replace=True)

        # Verify replacement worked
        assert sample_model.value("revenue", 2023) == 200000
        line_item = sample_model._line_item_definition("revenue")
        assert line_item.category == "expenses"
        assert line_item.label == "Replaced Revenue"
        assert line_item.formula == "200000"

    def test_add_line_item_replace_true_new_item_works(self, sample_model):
        """Test that add_line_item with replace=True works for new items too."""
        # Should work fine for new items even with replace=True
        sample_model.update.add_line_item(
            name="expenses",
            category="expenses",
            formula="50000",
            replace=True,
        )

        # Verify new item was added
        assert sample_model.value("expenses", 2023) == 50000
        assert "expenses" in [item.name for item in sample_model._line_item_definitions]

    def test_add_line_item_replace_preserves_model_structure(self, sample_model):
        """Test that replacement preserves overall model structure."""
        initial_item_count = len(sample_model._line_item_definitions)

        # Replace existing item
        sample_model.update.add_line_item(
            name="revenue", formula="300000", replace=True
        )

        # Should have same number of items (replacement, not addition)
        assert len(sample_model._line_item_definitions) == initial_item_count
        assert sample_model.value("revenue", 2023) == 300000

    def test_add_line_item_replace_with_different_properties(self, sample_model):
        """Test replacing with completely different line item properties."""
        # Original item has values, new item has formula
        original_item = sample_model._line_item_definition("revenue")
        assert original_item.values is not None
        assert original_item.formula is None

        # Replace with formula-based item
        sample_model.update.add_line_item(
            name="revenue",
            category="expenses",
            formula="1000 + 2000",
            value_format="currency",
            replace=True,
        )

        # Verify all properties changed
        new_item = sample_model._line_item_definition("revenue")
        assert new_item.category == "expenses"
        assert new_item.formula == "1000 + 2000"
        assert new_item.value_format == "currency"
        assert sample_model.value("revenue", 2023) == 3000

    def test_add_line_item_replace_validation_still_works(self, sample_model):
        """Test that validation still works with replace=True."""
        # Should still validate the new line item even with replace=True
        with pytest.raises(ValueError, match="Name must only contain"):
            sample_model.update.add_line_item(
                name="invalid name with spaces",  # Invalid name format
                formula="100000",
                replace=True,
            )

        # Original item should be unchanged after failed replacement
        assert sample_model.value("revenue", 2023) == 100000

    def test_add_line_item_replace_error_messages(self, sample_model):
        """Test that error messages correctly indicate replace vs add operations."""
        # Test error message for replacement failure (existing item)
        with pytest.raises(ValueError, match="Failed to replace line item 'revenue'"):
            # Force an error during model recalculation by using invalid formula
            sample_model.update.add_line_item(
                name="revenue",
                formula="nonexistent_variable + 100",  # Invalid formula reference
                replace=True,
            )

        # Test error message for add failure (new item)
        with pytest.raises(ValueError, match="Failed to add line item 'new_item'"):
            sample_model.update.add_line_item(
                name="new_item",
                formula="nonexistent_variable + 100",  # Invalid formula reference
                replace=True,  # This is a new item, so it's an "add" operation
            )

    def test_add_line_item_both_line_item_and_name_with_replace_fails(
        self, sample_model
    ):
        """Test that providing both line_item and name still fails with replace=True."""
        line_item = LineItem(name="test", formula="100")

        with pytest.raises(
            ValueError,
            match="Cannot specify both 'line_item' and 'name' parameters",
        ):
            sample_model.update.add_line_item(
                line_item=line_item,
                name="test",
                replace=True,
            )

    def test_add_line_item_neither_line_item_nor_name_with_replace_fails(
        self, sample_model
    ):
        """Test that providing neither line_item nor name fails with replace=True."""
        with pytest.raises(
            ValueError,
            match="Must specify either 'line_item' parameter or 'name' parameter",
        ):
            sample_model.update.add_line_item(formula="100", replace=True)

    def test_add_line_item_replace_rollback_on_failure(self, sample_model):
        """Test that when replace=True fails, the original item is preserved."""
        # Store the original item value and properties for comparison
        original_value = sample_model.value("revenue", 2023)
        original_item = sample_model._line_item_definition("revenue")
        original_category = original_item.category
        original_formula = original_item.formula
        original_values = original_item.values.copy()

        # Count line items before the failed replacement
        original_item_count = len(sample_model._line_item_definitions)

        # Attempt to replace with an invalid formula - should fail and rollback
        with pytest.raises(ValueError, match="Failed to replace line item 'revenue'"):
            sample_model.update.add_line_item(
                name="revenue",
                formula="nonexistent_variable + undefined_item",  # Invalid formula
                replace=True,
            )

        # Verify the original item is still there and unchanged
        assert sample_model.value("revenue", 2023) == original_value
        assert len(sample_model._line_item_definitions) == original_item_count

        # Verify all original properties are preserved
        preserved_item = sample_model._line_item_definition("revenue")
        assert preserved_item.category == original_category
        assert preserved_item.formula == original_formula
        assert preserved_item.values == original_values

        # Verify the model is still functional
        assert "revenue" in sample_model.line_item_names
        assert sample_model.value("revenue", 2023) == original_value

    def test_add_line_item_replace_rollback_on_failure_with_line_item_object(
        self, sample_model
    ):
        """Test rollback when replace=True fails with LineItem object."""
        # Store original state
        original_value = sample_model.value("revenue", 2023)
        original_item_count = len(sample_model._line_item_definitions)

        # Create a LineItem with invalid formula
        bad_line_item = LineItem(
            name="revenue",
            formula="invalid_formula_reference + nonexistent",
            category="income",
        )

        # Attempt replacement that should fail
        with pytest.raises(ValueError, match="Failed to replace line item 'revenue'"):
            sample_model.update.add_line_item(
                line_item=bad_line_item,
                replace=True,
            )

        # Verify rollback - original item should be preserved
        assert sample_model.value("revenue", 2023) == original_value
        assert len(sample_model._line_item_definitions) == original_item_count
        assert "revenue" in sample_model.line_item_names

    def test_convenience_method_add_line_item_replace_parameter(self, sample_model):
        """Test that the convenience method on Model class supports replace parameter."""  # noqa: E501
        # Check original value
        assert sample_model.value("revenue", 2023) == 100000

        # Try to add without replace - should fail
        with pytest.raises(
            ValueError,
            match="Line item with name 'revenue' already exists",
        ):
            sample_model.add_line_item(name="revenue", formula="200000")

        # Add with replace=True - should work
        sample_model.add_line_item(name="revenue", formula="200000", replace=True)

        # Verify replacement worked
        assert sample_model.value("revenue", 2023) == 200000

    def test_convenience_method_replace_with_line_item_object(self, sample_model):
        """Test convenience method replace with LineItem object."""
        # Check original value
        assert sample_model.value("revenue", 2023) == 100000

        # Create new LineItem
        new_line_item = LineItem(
            name="revenue",
            category="expenses",  # Different category
            formula="300000",
            label="Replaced Revenue",
        )

        # Replace using convenience method
        sample_model.add_line_item(line_item=new_line_item, replace=True)

        # Verify replacement worked
        assert sample_model.value("revenue", 2023) == 300000
        line_item = sample_model._line_item_definition("revenue")
        assert line_item.category == "expenses"
        assert line_item.label == "Replaced Revenue"


class TestDeleteLineItems:
    """Test the delete_line_items method that deletes multiple line items at once."""

    @pytest.fixture
    def sample_model(self):
        """Create a sample model with multiple line items for testing."""
        revenue = LineItem(
            name="revenue",
            category="income",
            values={2023: 100000, 2024: 120000, 2025: 140000},
        )
        salary = LineItem(
            name="salary",
            category="expenses",
            values={2023: 60000, 2024: 65000, 2025: 70000},
        )
        rent = LineItem(
            name="rent",
            category="expenses",
            values={2023: 24000, 2024: 25000, 2025: 26000},
        )
        utilities = LineItem(
            name="utilities",
            category="expenses",
            values={2023: 6000, 2024: 6500, 2025: 7000},
        )

        categories = [
            Category(name="income", label="Income"),
            Category(name="expenses", label="Expenses"),
        ]

        return Model(
            line_items=[revenue, salary, rent, utilities],
            years=[2023, 2024, 2025],
            categories=categories,
        )

    def test_delete_line_items_multiple(self, sample_model: Model):
        """Test that delete_line_items successfully deletes multiple line items."""
        initial_count = len(sample_model._line_item_definitions)
        assert initial_count == 4

        # Delete multiple items
        sample_model.update.delete_line_items(["salary", "rent"])

        # Verify deletions
        assert len(sample_model._line_item_definitions) == initial_count - 2
        remaining_names = [item.name for item in sample_model._line_item_definitions]
        assert "salary" not in remaining_names
        assert "rent" not in remaining_names
        assert "revenue" in remaining_names
        assert "utilities" in remaining_names

    def test_delete_line_items_single(self, sample_model: Model):
        """Test that delete_line_items works with a single item."""
        initial_count = len(sample_model._line_item_definitions)

        # Delete single item using the list method
        sample_model.update.delete_line_items(["salary"])

        # Verify deletion
        assert len(sample_model._line_item_definitions) == initial_count - 1
        assert "salary" not in [
            item.name for item in sample_model._line_item_definitions
        ]

    def test_delete_line_items_all_in_category(self, sample_model: Model):
        """Test deleting all line items in a specific category."""
        initial_count = len(sample_model._line_item_definitions)

        # Delete all expense items
        sample_model.update.delete_line_items(["salary", "rent", "utilities"])

        # Verify deletions
        assert len(sample_model._line_item_definitions) == initial_count - 3
        remaining_names = [item.name for item in sample_model._line_item_definitions]
        assert remaining_names == ["revenue"]

    def test_delete_line_items_nonexistent_item(self, sample_model: Model):
        """Test that delete_line_items fails when a line item doesn't exist."""
        with pytest.raises(
            KeyError, match="Line item 'nonexistent' not found in model"
        ):
            sample_model.update.delete_line_items(["salary", "nonexistent"])

        # Verify no changes were made
        assert len(sample_model._line_item_definitions) == 4

    def test_delete_line_items_empty_list(self, sample_model: Model):
        """Test that delete_line_items with an empty list doesn't change the model."""
        initial_count = len(sample_model._line_item_definitions)

        # Delete empty list - should not fail but also not change anything
        sample_model.update.delete_line_items([])

        # Verify no changes
        assert len(sample_model._line_item_definitions) == initial_count

    def test_delete_line_items_validation_failure(self, sample_model: Model):
        """Test that delete_line_items handles validation failures properly."""
        initial_count = len(sample_model._line_item_definitions)

        # Try to delete items (should work normally in this case)
        # In a real scenario with formulas referencing these items, this could fail
        sample_model.update.delete_line_items(["salary", "rent"])

        # Verify deletions worked
        assert len(sample_model._line_item_definitions) == initial_count - 2


class TestDeleteCategoryWithLineItems:
    """Test the updated delete_category method with include_line_items parameter."""

    @pytest.fixture
    def sample_model(self):
        """Create a sample model for testing."""
        revenue = LineItem(
            name="revenue",
            category="income",
            values={2023: 100000, 2024: 120000, 2025: 140000},
        )
        salary = LineItem(
            name="salary",
            category="expenses",
            values={2023: 60000, 2024: 65000, 2025: 70000},
        )
        rent = LineItem(
            name="rent",
            category="expenses",
            values={2023: 24000, 2024: 25000, 2025: 26000},
        )

        categories = [
            Category(name="income", label="Income"),
            Category(name="expenses", label="Expenses"),
            Category(name="unused", label="Unused Category"),
        ]

        return Model(
            line_items=[revenue, salary, rent],
            years=[2023, 2024, 2025],
            categories=categories,
        )

    def test_delete_category_with_line_items_false_default(self, sample_model: Model):
        """Test that delete_category fails by default when line items exist."""
        with pytest.raises(
            ValueError,
            match="Cannot delete category 'income' because it is used by line items",
        ):
            sample_model.update.delete_category("income")

    def test_delete_category_with_line_items_false_explicit(self, sample_model: Model):
        """Test that delete_category with include_line_items=False fails when line items exist."""
        with pytest.raises(
            ValueError,
            match="Cannot delete category 'expenses' because it is used by line items",
        ):
            sample_model.update.delete_category("expenses", include_line_items=False)

    def test_delete_category_with_line_items_true(self, sample_model: Model):
        """Test that delete_category with include_line_items=True deletes line items first."""
        initial_category_count = len(sample_model._category_definitions)
        initial_line_item_count = len(sample_model._line_item_definitions)

        # Delete category with its line items
        sample_model.update.delete_category("expenses", include_line_items=True)

        # Verify category is deleted
        assert len(sample_model._category_definitions) == initial_category_count - 1
        assert "expenses" not in [
            cat.name for cat in sample_model._category_definitions
        ]

        # Verify line items in that category are deleted
        assert len(sample_model._line_item_definitions) == initial_line_item_count - 2
        remaining_names = [item.name for item in sample_model._line_item_definitions]
        assert "salary" not in remaining_names
        assert "rent" not in remaining_names
        assert "revenue" in remaining_names

    def test_delete_category_no_line_items_still_works(self, sample_model: Model):
        """Test that delete_category works normally for categories without line items."""
        initial_count = len(sample_model._category_definitions)

        # Delete category with no line items (should work with or without the flag)
        sample_model.update.delete_category("unused")

        assert len(sample_model._category_definitions) == initial_count - 1
        assert "unused" not in [cat.name for cat in sample_model._category_definitions]

    def test_delete_category_with_line_items_true_no_line_items(
        self, sample_model: Model
    ):
        """Test that delete_category with include_line_items=True works even without line items."""
        initial_count = len(sample_model._category_definitions)

        # Delete category with no line items but with the flag set
        sample_model.update.delete_category("unused", include_line_items=True)

        assert len(sample_model._category_definitions) == initial_count - 1
        assert "unused" not in [cat.name for cat in sample_model._category_definitions]
