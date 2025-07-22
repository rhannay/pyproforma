import pytest
from pyproforma import LineItem, Model, Category
from pyproforma.generators.debt import Debt


class TestUnifiedAddFunctionality:
    """Test add functionality using the new unified .update namespace."""

    @pytest.fixture
    def sample_model(self):
        """Create a sample model for testing."""
        revenue = LineItem(
            name="revenue",
            category="income",
            values={2023: 100000, 2024: 120000, 2025: 140000}
        )
        
        categories = [Category(name="income", label="Income")]
        
        return Model(
            line_items=[revenue],
            years=[2023, 2024, 2025],
            categories=categories
        )

    def test_add_generator_basic(self, sample_model: Model):
        """Test adding a basic generator."""
        initial_count = len(sample_model.generators)
        
        # Create a debt generator
        debt_generator = Debt(
            name="test_debt",
            par_amounts={2023: 100000},
            interest_rate=0.05,
            term=5
        )
        
        sample_model.update.add_generator(debt_generator)
        
        assert len(sample_model.generators) == initial_count + 1
        assert sample_model.generators[-1].name == "test_debt"

    def test_add_generator_updates_defined_names(self, sample_model: Model):
        """Test that adding a generator updates defined names."""
        initial_names = [name['name'] for name in sample_model.defined_names]
        
        debt_generator = Debt(
            name="test_debt",
            par_amounts={2023: 100000},
            interest_rate=0.05,
            term=5
        )
        
        sample_model.update.add_generator(debt_generator)
        
        # Check that new names were added
        current_names = [name['name'] for name in sample_model.defined_names]
        assert len(current_names) > len(initial_names)
        
        # Check that debt-related names are present
        debt_names = [name for name in current_names if 'test_debt' in name]
        assert len(debt_names) > 0

    def test_add_generator_values_accessible(self, sample_model: Model):
        """Test that generator values are accessible after adding."""
        debt_generator = Debt(
            name="test_debt",
            par_amounts={2023: 100000},
            interest_rate=0.05,
            term=5
        )
        
        sample_model.update.add_generator(debt_generator)
        
        # Check that we can access generator values
        # The exact names depend on the Debt generator implementation
        debt_names = [name['name'] for name in sample_model.defined_names if 'test_debt' in name['name']]
        assert len(debt_names) > 0
        
        # Try to get values for the debt-related names
        for debt_name in debt_names:
            value = sample_model.get_value(debt_name, 2023)
            assert isinstance(value, (int, float))

    def test_add_generator_not_instance_fails(self, sample_model: Model):
        """Test that adding a non-Generator instance fails."""
        with pytest.raises(TypeError, match="Must provide a Generator instance"):
            sample_model.update.add_generator("not_a_generator")

    def test_add_category_basic(self, sample_model: Model):
        """Test adding a basic category."""
        initial_count = len(sample_model.category_definitions)
        
        sample_model.update.add_category(name="expenses")
        
        assert len(sample_model.category_definitions) == initial_count + 1
        new_category = sample_model.category_definitions[-1]
        assert new_category.name == "expenses"

    def test_add_category_with_label(self, sample_model: Model):
        """Test adding a category with a custom label."""
        sample_model.update.add_category(name="assets", label="Asset Accounts")
        
        new_category = next(cat for cat in sample_model.category_definitions if cat.name == "assets")
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
            values={2023: 80000, 2024: 85000, 2025: 90000}
        )
        
        assert sample_model.get_value("expenses", 2023) == 80000
        assert sample_model.get_value("expenses", 2024) == 85000

    def test_add_line_item_with_formula(self, sample_model: Model):
        """Test adding a line item with a formula."""
        sample_model.update.add_line_item(
            name="profit",
            category="income",
            formula="revenue * 0.2"
        )
        
        # Should calculate 20% of revenue
        assert sample_model.get_value("profit", 2023) == 20000  # 100000 * 0.2
        assert sample_model.get_value("profit", 2024) == 24000  # 120000 * 0.2

    def test_add_line_item_duplicate_name_fails(self, sample_model: Model):
        """Test that adding a line item with duplicate name fails."""
        with pytest.raises(ValueError, match="Failed to add line item 'revenue'"):
            sample_model.update.add_line_item(
                name="revenue",
                category="income",
                values={2023: 1000}
            )

    def test_add_line_item_invalid_category_fails(self, sample_model: Model):
        """Test that adding a line item with invalid category fails."""
        with pytest.raises(ValueError, match="Failed to add line item 'test'"):
            sample_model.update.add_line_item(
                name="test",
                category="nonexistent",
                values={2023: 1000}
            )


class TestUnifiedUpdateFunctionality:
    """Test update functionality using the new unified .update namespace."""

    @pytest.fixture
    def sample_model_with_categories(self) -> Model:
        """Create a sample model with categories for testing."""
        revenue = LineItem(
            name="revenue",
            category="income",
            values={2023: 100000, 2024: 120000, 2025: 140000}
        )
        
        salary = LineItem(
            name="salary",
            category="expenses",
            values={2023: 60000, 2024: 65000, 2025: 70000}
        )
        
        categories = [
            Category(name="income", label="Income", include_total=True),
            Category(name="expenses", label="Expenses", include_total=True),
        ]
        
        return Model(
            line_items=[revenue, salary],
            years=[2023, 2024, 2025],
            categories=categories
        )

    def test_update_category_label(self, sample_model_with_categories: Model):
        """Test updating category label."""
        sample_model_with_categories.update.update_category(
            "income",
            label="Revenue Streams"
        )
        
        category = next(cat for cat in sample_model_with_categories.category_definitions if cat.name == "income")
        assert category.label == "Revenue Streams"

    def test_update_line_item_values(self, sample_model_with_categories: Model):
        """Test updating line item values."""
        sample_model_with_categories.update.update_line_item(
            "revenue",
            values={2023: 150000, 2024: 160000, 2025: 170000}
        )
        
        assert sample_model_with_categories.get_value("revenue", 2023) == 150000
        assert sample_model_with_categories.get_value("revenue", 2024) == 160000

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
            values={2023: 100000, 2024: 120000, 2025: 140000}
        )
        
        debt1 = Debt(
            name="loan1",
            par_amounts={2023: 100000},
            interest_rate=0.05,
            term=5
        )
        
        categories = [Category(name="income", label="Income")]
        
        return Model(
            line_items=[revenue],
            years=[2023, 2024, 2025],
            categories=categories,
            generators=[debt1]
        )

    def test_delete_generator_basic(self, sample_model_with_generators: Model):
        """Test deleting a generator."""
        initial_count = len(sample_model_with_generators.generators)
        
        sample_model_with_generators.update.delete_generator("loan1")
        
        assert len(sample_model_with_generators.generators) == initial_count - 1

    def test_delete_line_item_basic(self, sample_model_with_generators: Model):
        """Test deleting a line item."""
        initial_count = len(sample_model_with_generators.line_item_definitions)
        
        sample_model_with_generators.update.delete_line_item("revenue")
        
        assert len(sample_model_with_generators.line_item_definitions) == initial_count - 1

    def test_delete_category_unused(self):
        """Test deleting an unused category."""
        # Create a model with an unused category
        revenue = LineItem(name="revenue", category="income", values={2023: 100})
        categories = [
            Category(name="income", label="Income"),
            Category(name="unused", label="Unused")
        ]
        model = Model(line_items=[revenue], years=[2023], categories=categories)
        
        initial_count = len(model.category_definitions)
        
        model.update.delete_category("unused")
        
        assert len(model.category_definitions) == initial_count - 1

    def test_delete_category_used_by_line_items_fails(self, sample_model_with_generators: Model):
        """Test that deleting a category used by line items fails."""
        with pytest.raises(ValueError, match="Cannot delete category 'income' because it is used by line items"):
            sample_model_with_generators.update.delete_category("income")