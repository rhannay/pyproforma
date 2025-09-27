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
            Category(name="income", label="Income", include_total=True),
            Category(name="expenses", label="Expenses", include_total=True),
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
        initial_count = len(sample_model.line_item_definitions)

        sample_model.update.add_line_item(
            name="rent",
            category="expenses",
            values={2023: 24000, 2024: 25000, 2025: 26000},
        )

        assert len(sample_model.line_item_definitions) == initial_count + 1
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
        initial_count = len(sample_model.line_item_definitions)

        sample_model.update.delete_line_item("salary")

        assert len(sample_model.line_item_definitions) == initial_count - 1
        assert "salary" not in [
            item.name for item in sample_model.line_item_definitions
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
        original_count = len(sample_model.line_item_definitions)
        with pytest.raises(ValueError):
            sample_model.update.add_line_item(
                name="invalid_item",
                category="nonexistent_category",  # This will fail
                values={2023: 1000},
            )

        # Original model should be unchanged
        assert len(sample_model.line_item_definitions) == original_count
