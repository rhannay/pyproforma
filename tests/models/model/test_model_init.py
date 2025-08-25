import pytest

from pyproforma import Category, Constraint, LineItem, Model
from pyproforma.models.multi_line_item.debt import Debt


class TestModelInitWithDuplicateGenerators:
    """Test that Model initialization handles duplicate generator names appropriately."""

    @pytest.fixture
    def basic_line_items(self):
        """Create basic line items for testing."""
        return [
            LineItem(
                name="revenue",
                category="income",
                values={2023: 100000, 2024: 120000}
            ),
            LineItem(
                name="expenses",
                category="costs",
                values={2023: 50000, 2024: 60000}
            )
        ]

    @pytest.fixture
    def basic_categories(self):
        """Create basic categories for testing."""
        return [
            Category(name="income", label="Income"),
            Category(name="costs", label="Costs")
        ]

    def test_duplicate_generator_names_should_raise_error(self, basic_line_items, basic_categories):
        """Test that providing two generators with the same name should raise a ValueError.
        
        This test demonstrates that duplicate generator names should not be allowed,
        even if they are different types of generators, because it creates ambiguity
        and potential conflicts in the model namespace.
        
        Currently this test WILL FAIL because the code doesn't validate generator names directly.
        """
        # Create two debt generators with the same name but different configurations
        debt_generator_1 = Debt(
            name="company_debt",
            par_amount={2023: 100000},
            interest_rate=0.05,
            term=5
        )

        debt_generator_2 = Debt(
            name="company_debt",  # Same name as first generator - should not be allowed
            par_amount={2023: 200000},
            interest_rate=0.06,
            term=10
        )

        generators = [debt_generator_1, debt_generator_2]

        # This SHOULD raise a ValueError for duplicate generator names
        # but currently it will raise a ValueError for duplicate defined_names instead
        with pytest.raises(ValueError, match="Duplicate multi line item names not allowed"):
            Model(
                line_items=basic_line_items,
                years=[2023, 2024],
                categories=basic_categories,
                multi_line_items=generators
            )

    def test_generator_name_same_as_line_item_is_allowed(self, basic_line_items, basic_categories):
        """Test that a generator name same as line item name is allowed since they have different namespaces."""
        # Create a generator with the same name as a line item
        debt_generator = Debt(
            name="revenue",  # Same name as line item
            par_amount={2023: 100000},
            interest_rate=0.05,
            term=5
        )

        # This should work because generator creates names like "revenue.principal", "revenue.interest"
        # which don't conflict with line item "revenue"
        model = Model(
            line_items=basic_line_items,
            years=[2023, 2024],
            categories=basic_categories,
            multi_line_items=[debt_generator]
        )

        # Verify both the line item and generator are present
        assert len(model._line_item_definitions) == 2
        assert len(model.multi_line_items) == 1
        assert model.multi_line_items[0].name == "revenue"

        # Verify defined names include both line item and generator variables
        defined_names = [item['name'] for item in model.line_item_metadata]
        assert "revenue" in defined_names  # line item
        assert "revenue.principal" in defined_names  # generator
        assert "revenue.interest" in defined_names  # generator
        assert "revenue.bond_proceeds" in defined_names  # generator

    def test_unique_generator_names_work_correctly(self, basic_line_items, basic_categories):
        """Test that generators with unique names work correctly."""
        # Create two debt generators with different names
        debt_generator_1 = Debt(
            name="company_debt",
            par_amount={2023: 100000},
            interest_rate=0.05,
            term=5
        )

        debt_generator_2 = Debt(
            name="equipment_debt",
            par_amount={2023: 50000},
            interest_rate=0.04,
            term=3
        )

        generators = [debt_generator_1, debt_generator_2]

        # This should work without raising an error
        model = Model(
            line_items=basic_line_items,
            years=[2023, 2024],
            categories=basic_categories,
            multi_line_items=generators
        )

        # Verify both generators are present
        assert len(model.multi_line_items) == 2
        assert model.multi_line_items[0].name == "company_debt"
        assert model.multi_line_items[1].name == "equipment_debt"

        # Verify defined names include both generators' variables
        defined_names = [item['name'] for item in model.line_item_metadata]
        assert "company_debt.principal" in defined_names
        assert "company_debt.interest" in defined_names
        assert "equipment_debt.principal" in defined_names
        assert "equipment_debt.interest" in defined_names

    def test_different_generator_types_same_name_should_raise_error(self, basic_line_items, basic_categories):
        """Test that different types of generators with the same name should raise a ValueError.
        
        This test demonstrates that even different types of generators should not be allowed
        to have the same name, as it creates confusion and potential conflicts.
        
        Currently this test WILL FAIL because the code doesn't validate generator names directly.
        """
        from pyproforma.models.multi_line_item.short_term_debt import ShortTermDebt

        # Create a debt generator
        debt_generator = Debt(
            name="facility",
            par_amount={2023: 100000},
            interest_rate=0.05,
            term=5
        )

        # Create a short-term debt generator with the same name
        short_term_debt_generator = ShortTermDebt(
            name="facility",  # Same name as debt generator - should not be allowed
            draws={2023: 50000},
            paydown={2024: 25000},
            begin_balance=0,
            interest_rate=0.04
        )

        generators = [debt_generator, short_term_debt_generator]

        # This SHOULD raise a ValueError for duplicate generator names
        # but currently it may pass or raise for different reasons
        with pytest.raises(ValueError, match="Duplicate multi line item names not allowed"):
            Model(
                line_items=basic_line_items,
                years=[2023, 2024],
                categories=basic_categories,
                multi_line_items=generators
            )


class TestModelInitWithDuplicateCategories:
    """Test that Model initialization handles duplicate category names appropriately."""

    @pytest.fixture
    def basic_line_items(self):
        """Create basic line items for testing."""
        return [
            LineItem(
                name="revenue",
                category="income",
                values={2023: 100000, 2024: 120000}
            ),
            LineItem(
                name="expenses",
                category="costs",
                values={2023: 50000, 2024: 60000}
            )
        ]

    def test_duplicate_category_names_should_raise_error(self, basic_line_items):
        """Test that providing two categories with the same name should raise a ValueError.
        
        This test demonstrates that duplicate category names should not be allowed,
        as it creates ambiguity and potential conflicts in the model.
        
        Currently this test WILL FAIL if the code doesn't validate category names directly.
        """
        # Create two categories with the same name but different labels
        category_1 = Category(name="income", label="Income")
        category_2 = Category(name="income", label="Revenue")  # Same name - should not be allowed

        duplicate_categories = [category_1, category_2]

        # This SHOULD raise a ValueError for duplicate category names
        # If no error is raised, the test will fail and the code needs to be fixed
        with pytest.raises(ValueError, match="Duplicate category names not allowed"):
            Model(
                line_items=basic_line_items,
                years=[2023, 2024],
                categories=duplicate_categories,
                multi_line_items=[]
            )

    def test_different_category_names_work_correctly(self, basic_line_items):
        """Test that categories with unique names work correctly."""
        # Create categories with different names
        category_1 = Category(name="income", label="Income")
        category_2 = Category(name="costs", label="Costs")
        category_3 = Category(name="assets", label="Assets")

        unique_categories = [category_1, category_2, category_3]

        # This should work without raising an error
        model = Model(
            line_items=basic_line_items,
            years=[2023, 2024],
            categories=unique_categories,
            multi_line_items=[]
        )

        # Verify all categories are present
        assert len(model._category_definitions) == 3
        category_names = [cat.name for cat in model._category_definitions]
        assert "income" in category_names
        assert "costs" in category_names
        assert "assets" in category_names


class TestModelInitWithConstraints:
    """Test that Model initialization handles constraints appropriately."""

    @pytest.fixture
    def basic_line_items(self):
        """Create basic line items for testing."""
        return [
            LineItem(
                name="revenue",
                category="income",
                values={2023: 100000, 2024: 120000}
            ),
            LineItem(
                name="expenses",
                category="costs",
                values={2023: 50000, 2024: 60000}
            )
        ]

    @pytest.fixture
    def basic_categories(self):
        """Create basic categories for testing."""
        return [
            Category(name="income", label="Income"),
            Category(name="costs", label="Costs")
        ]

    def test_model_with_no_constraints(self, basic_line_items, basic_categories):
        """Test that Model can be created with no constraints (constraints=None)."""
        model = Model(
            line_items=basic_line_items,
            years=[2023, 2024],
            categories=basic_categories
        )

        assert model.constraints == []
        assert len(model.constraints) == 0

    def test_model_with_empty_constraints_list(self, basic_line_items, basic_categories):
        """Test that Model can be created with empty constraints list."""
        model = Model(
            line_items=basic_line_items,
            years=[2023, 2024],
            categories=basic_categories,
            constraints=[]
        )

        assert model.constraints == []
        assert len(model.constraints) == 0

    def test_model_with_valid_constraints(self, basic_line_items, basic_categories):
        """Test that Model can be created with valid constraints."""
        from pyproforma.models.constraint import Constraint

        constraint1 = Constraint(
            name="min_revenue",
            line_item_name="revenue",
            target=50000.0,
            operator="gt"
        )

        constraint2 = Constraint(
            name="max_expenses",
            line_item_name="expenses",
            target=70000.0,
            operator="lt"
        )

        model = Model(
            line_items=basic_line_items,
            years=[2023, 2024],
            categories=basic_categories,
            constraints=[constraint1, constraint2]
        )

        assert len(model.constraints) == 2
        assert model.constraints[0].name == "min_revenue"
        assert model.constraints[1].name == "max_expenses"

    def test_duplicate_constraint_names_should_raise_error(self, basic_line_items, basic_categories):
        """Test that providing two constraints with the same name should raise a ValueError."""
        from pyproforma.models.constraint import Constraint

        constraint1 = Constraint(
            name="revenue_check",
            line_item_name="revenue",
            target=50000.0,
            operator="gt"
        )

        constraint2 = Constraint(
            name="revenue_check",  # Same name - should not be allowed
            line_item_name="revenue",
            target=200000.0,
            operator="lt"
        )

        with pytest.raises(ValueError, match="Duplicate constraint names not allowed"):
            Model(
                line_items=basic_line_items,
                years=[2023, 2024],
                categories=basic_categories,
                constraints=[constraint1, constraint2]
            )

    def test_multiple_duplicate_constraint_names_error_message(self, basic_line_items, basic_categories):
        """Test that error message includes all duplicate constraint names."""
        from pyproforma.models.constraint import Constraint

        constraint1 = Constraint(
            name="check_a",
            line_item_name="revenue",
            target=50000.0,
            operator="gt"
        )

        constraint2 = Constraint(
            name="check_a",  # Duplicate
            line_item_name="expenses",
            target=70000.0,
            operator="lt"
        )

        constraint3 = Constraint(
            name="check_b",
            line_item_name="revenue",
            target=100000.0,
            operator="lt"
        )

        constraint4 = Constraint(
            name="check_b",  # Duplicate
            line_item_name="expenses",
            target=40000.0,
            operator="gt"
        )

        with pytest.raises(ValueError) as excinfo:
            Model(
                line_items=basic_line_items,
                years=[2023, 2024],
                categories=basic_categories,
                constraints=[constraint1, constraint2, constraint3, constraint4]
            )

        error_msg = str(excinfo.value)
        assert "Duplicate constraint names not allowed" in error_msg
        assert "check_a" in error_msg
        assert "check_b" in error_msg

    def test_constraint_name_same_as_line_item_is_allowed(self, basic_line_items, basic_categories):
        """Test that a constraint name can be the same as a line item name."""
        from pyproforma.models.constraint import Constraint

        constraint = Constraint(
            name="revenue",  # Same name as line item
            line_item_name="revenue",
            target=50000.0,
            operator="gt"
        )

        # This should work - constraints and line items have separate namespaces
        model = Model(
            line_items=basic_line_items,
            years=[2023, 2024],
            categories=basic_categories,
            constraints=[constraint]
        )

        assert len(model.constraints) == 1
        assert model.constraints[0].name == "revenue"
        assert len(model._line_item_definitions) == 2
        assert any(item.name == "revenue" for item in model._line_item_definitions)

    def test_constraint_with_invalid_line_item_name_should_raise_error(self, basic_line_items, basic_categories):
        """Test that a constraint referencing a non-existent line item should raise a ValueError."""

        constraint = Constraint(
            name="invalid_reference",
            line_item_name="nonexistent_item",  # This line item doesn't exist
            target=50000.0,
            operator="gt"
        )

        # This should raise a ValueError because the constraint references a line item that doesn't exist
        with pytest.raises(ValueError, match="Constraint 'invalid_reference' references unknown line item 'nonexistent_item'"):
            Model(
                line_items=basic_line_items,
                years=[2023, 2024],
                categories=basic_categories,
                constraints=[constraint]
            )

    def test_multiple_constraints_with_invalid_line_item_names(self, basic_line_items, basic_categories):
        """Test that multiple constraints with invalid line item names raise appropriate errors."""

        constraint1 = Constraint(
            name="invalid_ref_1",
            line_item_name="nonexistent_item_1",
            target=50000.0,
            operator="gt"
        )

        constraint2 = Constraint(
            name="invalid_ref_2",
            line_item_name="nonexistent_item_2",
            target=70000.0,
            operator="lt"
        )

        # Should raise error for the first invalid reference found
        with pytest.raises(ValueError, match="Constraint 'invalid_ref_1' references unknown line item 'nonexistent_item_1'"):
            Model(
                line_items=basic_line_items,
                years=[2023, 2024],
                categories=basic_categories,
                constraints=[constraint1, constraint2]
            )

    def test_mixed_valid_and_invalid_constraint_references(self, basic_line_items, basic_categories):
        """Test that having both valid and invalid constraint references raises error for invalid ones."""

        valid_constraint = Constraint(
            name="valid_ref",
            line_item_name="revenue",  # This exists
            target=50000.0,
            operator="gt"
        )

        invalid_constraint = Constraint(
            name="invalid_ref",
            line_item_name="nonexistent_item",  # This doesn't exist
            target=70000.0,
            operator="lt"
        )

        # Should raise error for the invalid reference
        with pytest.raises(ValueError, match="Constraint 'invalid_ref' references unknown line item 'nonexistent_item'"):
            Model(
                line_items=basic_line_items,
                years=[2023, 2024],
                categories=basic_categories,
                constraints=[valid_constraint, invalid_constraint]
            )
