import pytest

from pyproforma import Category, LineItem, Model
from pyproforma.models.generator.debt import Debt


class TestUnifiedAddFunctionality:
    """Test add functionality using the new unified .update namespace."""

    @pytest.fixture
    def sample_model(self):
        """Create a sample model for testing."""
        revenue = LineItem(
            name="revenue",
            category="income",
            values={2023: 100000, 2024: 120000, 2025: 140000},
        )

        categories = [Category(name="income", label="Income")]

        return Model(
            line_items=[revenue], years=[2023, 2024, 2025], categories=categories
        )

    def test_add_category_basic(self, sample_model: Model):
        """Test adding a basic category."""
        initial_count = len(sample_model._category_definitions)

        sample_model.update.add_category(name="expenses")

        assert len(sample_model._category_definitions) == initial_count + 1
        new_category = sample_model._category_definitions[-1]
        assert new_category.name == "expenses"

    def test_add_category_with_label(self, sample_model: Model):
        """Test adding a category with a custom label."""
        sample_model.update.add_category(name="assets", label="Asset Accounts")

        new_category = next(
            cat for cat in sample_model._category_definitions if cat.name == "assets"
        )
        assert new_category.label == "Asset Accounts"

    def test_add_category_duplicate_name_fails(self, sample_model: Model):
        """Test that adding a category with duplicate name fails."""
        with pytest.raises(ValueError, match="Failed to add category 'income'"):
            sample_model.update.add_category(name="income")

    def test_add_line_item_with_values(self, sample_model: Model):
        """Test adding a line item with explicit values."""
        sample_model.update.add_line_item(
            name="expenses",
            category="income",
            values={2023: 80000, 2024: 85000, 2025: 90000},
        )

        assert sample_model.value("expenses", 2023) == 80000
        assert sample_model.value("expenses", 2024) == 85000

    def test_add_line_item_with_formula(self, sample_model: Model):
        """Test adding a line item with a formula."""
        sample_model.update.add_line_item(
            name="profit", category="income", formula="revenue * 0.2"
        )

        # Should calculate 20% of revenue
        assert sample_model.value("profit", 2023) == 20000  # 100000 * 0.2
        assert sample_model.value("profit", 2024) == 24000  # 120000 * 0.2

    def test_add_line_item_duplicate_name_fails(self, sample_model: Model):
        """Test that adding a line item with duplicate name fails."""
        with pytest.raises(
            ValueError, match="Line item with name 'revenue' already exists"
        ):
            sample_model.update.add_line_item(
                name="revenue", category="income", values={2023: 1000}
            )

    def test_add_line_item_nonexistent_category_creates_category(
        self, sample_model: Model
    ):
        """Test that adding a line item with nonexistent category creates category."""
        initial_line_item_count = len(sample_model._line_item_definitions)
        initial_category_count = len(sample_model._category_definitions)

        # Add line item with nonexistent category - should succeed and create category
        sample_model.update.add_line_item(
            name="test", category="nonexistent", values={2023: 1000}
        )

        # Should have added both the line item and the category
        assert len(sample_model._line_item_definitions) == initial_line_item_count + 1
        assert len(sample_model._category_definitions) == initial_category_count + 1

        # Verify the line item was added correctly
        assert sample_model.value("test", 2023) == 1000

        # Verify the category was created
        category_names = [cat.name for cat in sample_model._category_definitions]
        assert "nonexistent" in category_names

    def test_add_line_item_without_category_defaults_to_general(
        self, sample_model: Model
    ):
        """Test adding a line item without specifying category defaults to 'general'."""
        initial_line_item_count = len(sample_model._line_item_definitions)

        # Add line item without specifying category
        sample_model.update.add_line_item(
            name="misc_expense", values={2023: 5000, 2024: 5500, 2025: 6000}
        )

        # Should have added the line item and potentially the 'general' category
        assert len(sample_model._line_item_definitions) == initial_line_item_count + 1

        # Verify the line item was added correctly with 'general' category
        line_item = sample_model._line_item_definition("misc_expense")
        assert line_item.category == "general"
        assert sample_model.value("misc_expense", 2023) == 5000

        # Verify 'general' category exists in model
        category_names = [cat.name for cat in sample_model._category_definitions]
        assert "general" in category_names

    def test_add_line_item_with_category_none_defaults_to_general(
        self, sample_model: Model
    ):
        """Test that adding a line item with category=None defaults to 'general'."""
        initial_line_item_count = len(sample_model._line_item_definitions)

        # Add line item with explicit category=None
        sample_model.update.add_line_item(
            name="other_item", category=None, values={2023: 1500}
        )

        # Should have added the line item
        assert len(sample_model._line_item_definitions) == initial_line_item_count + 1

        # Verify the line item was added correctly with 'general' category
        line_item = sample_model._line_item_definition("other_item")
        assert line_item.category == "general"
        assert sample_model.value("other_item", 2023) == 1500

        # Verify 'general' category exists in model
        category_names = [cat.name for cat in sample_model._category_definitions]
        assert "general" in category_names

    def test_add_line_item_with_formula_no_category_defaults_to_general(
        self, sample_model: Model
    ):
        """Test adding line item with formula but no category defaults to 'general'."""
        # Add line item with formula but no category specified
        sample_model.update.add_line_item(
            name="revenue_percentage", formula="revenue * 0.1"
        )

        # Verify the line item was added correctly with 'general' category
        line_item = sample_model._line_item_definition("revenue_percentage")
        assert line_item.category == "general"

        # Verify the formula works
        assert sample_model.value("revenue_percentage", 2023) == 10000  # 100000 * 0.1
        assert sample_model.value("revenue_percentage", 2024) == 12000  # 120000 * 0.1


class TestUnifiedUpdateFunctionality:
    """Test update functionality using the new unified .update namespace."""

    @pytest.fixture
    def sample_model_with_categories(self) -> Model:
        """Create a sample model with categories for testing."""
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

    def test_update_category_label(self, sample_model_with_categories: Model):
        """Test updating category label."""
        sample_model_with_categories.update.update_category(
            "income", label="Revenue Streams"
        )

        category = next(
            cat
            for cat in sample_model_with_categories._category_definitions
            if cat.name == "income"
        )
        assert category.label == "Revenue Streams"

    def test_update_line_item_values(self, sample_model_with_categories: Model):
        """Test updating line item values."""
        sample_model_with_categories.update.update_line_item(
            "revenue", values={2023: 150000, 2024: 160000, 2025: 170000}
        )

        assert sample_model_with_categories.value("revenue", 2023) == 150000
        assert sample_model_with_categories.value("revenue", 2024) == 160000

    def test_update_years_basic(self, sample_model_with_categories: Model):
        """Test updating years."""
        new_years = [2024, 2025, 2026]
        sample_model_with_categories.update.update_years(new_years)

        assert sample_model_with_categories.years == [2024, 2025, 2026]


class TestUnifiedDeleteFunctionality:
    """Test delete functionality using the new unified .update namespace."""

    @pytest.fixture
    def sample_model_with_generators(self) -> Model:
        """Create a sample model with generators for testing."""
        revenue = LineItem(
            name="revenue",
            category="income",
            values={2023: 100000, 2024: 120000, 2025: 140000},
        )

        debt1 = Debt(
            name="loan1", par_amount={2023: 100000}, interest_rate=0.05, term=5
        )

        categories = [Category(name="income", label="Income")]

        return Model(
            line_items=[revenue],
            years=[2023, 2024, 2025],
            categories=categories,
            generators=[debt1],
        )

    def test_delete_line_item_basic(self, sample_model_with_generators: Model):
        """Test deleting a line item."""
        initial_count = len(sample_model_with_generators._line_item_definitions)

        sample_model_with_generators.update.delete_line_item("revenue")

        assert (
            len(sample_model_with_generators._line_item_definitions)
            == initial_count - 1
        )

    def test_delete_category_unused(self):
        """Test deleting an unused category."""
        # Create a model with an unused category
        revenue = LineItem(name="revenue", category="income", values={2023: 100})
        categories = [
            Category(name="income", label="Income"),
            Category(name="unused", label="Unused"),
        ]
        model = Model(line_items=[revenue], years=[2023], categories=categories)

        initial_count = len(model._category_definitions)

        model.update.delete_category("unused")

        assert len(model._category_definitions) == initial_count - 1

    def test_delete_category_used_by_line_items_fails(
        self, sample_model_with_generators: Model
    ):
        """Test that deleting a category used by line items fails."""
        with pytest.raises(
            ValueError,
            match="Cannot delete category 'income' because it is used by line items",
        ):
            sample_model_with_generators.update.delete_category("income")
