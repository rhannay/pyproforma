import pytest
from pyproforma import LineItem, Model, Category
from pyproforma.models.model.model_add import AddNamespace
from pyproforma.generators.debt import Debt, Generator


class TestAddNameSpaceInit:
    def test_add_namespace_init(self):
        """Test that AddNameSpace initializes correctly with a model."""
        model = Model(
            line_items=[LineItem(name="revenue", category="income", values={2023: 100})],
            years=[2023]
        )
        add_namespace = AddNamespace(model)
        assert add_namespace._model is model


class TestAddGenerator:
    
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
        
        sample_model.add.generator(debt_generator)
        
        # Verify the generator was added
        assert len(sample_model.generators) == initial_count + 1
        
        # Find the added generator
        added_generator = next(gen for gen in sample_model.generators if gen.name == "test_debt")
        assert added_generator is debt_generator  # Should be the exact same instance
        assert added_generator.name == "test_debt"

    def test_add_generator_updates_defined_names(self, sample_model: Model):
        """Test that adding a generator properly updates the model's defined names."""
        initial_names = [name['name'] for name in sample_model.defined_names]
        
        # Create a debt generator
        debt_generator = Debt(
            name="loan",
            par_amounts={2023: 50000},
            interest_rate=0.04,
            term=3
        )
        
        sample_model.add.generator(debt_generator)
        
        updated_names = [name['name'] for name in sample_model.defined_names]
        
        # Check that generator names are added to defined names
        generator_names = debt_generator.defined_names
        for gen_name in generator_names:
            assert gen_name in updated_names
            assert gen_name not in initial_names
        
        # Check that generator names appear with correct metadata
        for gen_name in generator_names:
            gen_def = next(name for name in sample_model.defined_names if name['name'] == gen_name)
            assert gen_def['source_type'] == 'generator'
            assert gen_def['source_name'] == 'loan'

    def test_add_generator_values_accessible(self, sample_model: Model):
        """Test that generator values are accessible in the model."""
        # Create a debt generator
        debt_generator = Debt(
            name="mortgage",
            par_amounts={2023: 200000},
            interest_rate=0.06,
            term=30
        )
        
        sample_model.add.generator(debt_generator)
        
        # Verify we can access generator values
        generator_names = debt_generator.defined_names
        for gen_name in generator_names:
            # Should be able to access the value without error
            value = sample_model[gen_name, 2023]
            assert isinstance(value, (int, float))  # Should be a numeric value

    def test_add_generator_duplicate_defined_names_fails(self, sample_model: Model):
        """Test that adding a generator with names that conflict with existing names fails."""
        # First add a line item
        sample_model.add.line_item(
            name="debt_payment",
            category="income", 
            values={2023: 1000, 2024: 1100, 2025: 1200}
        )
        
        # Create a mock generator that would create a conflicting name
        from pyproforma.generators.generator_class import Generator
        
        class MockGenerator(Generator):
            def __init__(self):
                self.name = "conflict_generator"
            
            @property
            def defined_names(self):
                return ["debt_payment"]  # This conflicts with the line item
            
            def get_values(self, year):
                return {"debt_payment": 500}
            
            @classmethod
            def from_config(cls, config):
                """Required abstract method implementation."""
                return cls()
                
            def to_dict(self):
                """Required abstract method implementation."""
                return {"type": "mock", "name": self.name}
        
        mock_generator = MockGenerator()
        
        with pytest.raises(ValueError) as excinfo:
            sample_model.add.generator(mock_generator)
        
        assert "Failed to add generator 'conflict_generator'" in str(excinfo.value)
        assert "Duplicate defined names" in str(excinfo.value)
        
        # Verify original model is unchanged
        assert len(sample_model.generators) == 0

    def test_add_generator_not_instance_fails(self, sample_model: Model):
        """Test that adding a non-Generator object fails."""
        with pytest.raises(TypeError) as excinfo:
            sample_model.add.generator("not_a_generator")
        
        assert "Must provide a Generator instance" in str(excinfo.value)
        
        # Verify model is unchanged
        assert len(sample_model.generators) == 0

    def test_add_generator_invalid_generator_fails(self, sample_model: Model):
        """Test that adding an invalid generator fails validation."""
        # Create a generator with invalid configuration
        with pytest.raises(ValueError):
            # This should fail during Debt construction due to negative par amount
            Debt(
                name="bad_debt",
                par_amounts={2023: -100000},  # Negative amount should fail
                interest_rate=0.05,
                term=5
            )

    def test_add_multiple_generators(self, sample_model: Model):
        """Test adding multiple generators to the same model."""
        # Add first generator
        debt1 = Debt(
            name="debt1",
            par_amounts={2023: 100000},
            interest_rate=0.05,
            term=5
        )
        sample_model.add.generator(debt1)
        
        # Add second generator
        debt2 = Debt(
            name="debt2", 
            par_amounts={2023: 50000},
            interest_rate=0.04,
            term=3
        )
        sample_model.add.generator(debt2)
        
        # Verify both generators are present
        assert len(sample_model.generators) == 2
        generator_names = [gen.name for gen in sample_model.generators]
        assert "debt1" in generator_names
        assert "debt2" in generator_names
        
        # Verify all defined names are accessible
        all_gen_names = debt1.defined_names + debt2.defined_names
        for gen_name in all_gen_names:
            value = sample_model[gen_name, 2023]
            assert isinstance(value, (int, float))

    def test_add_generator_with_existing_debt_service(self, sample_model: Model):
        """Test adding a debt generator with existing debt service."""
        existing_debt = [
            {"year": 2022, "beginning_balance": 200000, "payment": 24000, "interest": 12000, "principal": 12000, "ending_balance": 188000}
        ]
        
        debt_generator = Debt(
            name="existing_loan",
            par_amounts={2023: 0},  # No new debt
            interest_rate=0.06,
            term=10,
            existing_debt_service=existing_debt
        )
        
        sample_model.add.generator(debt_generator)
        
        # Verify generator was added successfully
        assert len(sample_model.generators) == 1
        added_generator = sample_model.generators[0]
        assert added_generator.name == "existing_loan"

    def test_add_generator_returns_none(self, sample_model: Model):
        """Test that the method returns None (emphasizing side effect over return value)."""
        debt_generator = Debt(
            name="test_return",
            par_amounts={2023: 75000},
            interest_rate=0.045,
            term=7
        )
        
        result = sample_model.add.generator(debt_generator)
        
        # Verify method returns None
        assert result is None
        
        # Verify the generator was still added to the model
        assert len(sample_model.generators) == 1

    def test_model_copy_validation_preserves_original(self, sample_model: Model):
        """Test that validation failures don't affect the original model."""
        original_generators_count = len(sample_model.generators)
        
        # Create a mock generator that will cause validation to fail
        class BadGenerator(Generator):
            def __init__(self):
                self.name = "bad_generator"
            
            @property  
            def defined_names(self):
                return ["revenue"]  # This conflicts with existing line item
            
            def get_values(self, year):
                return {"revenue": 500}
                
            @classmethod
            def from_config(cls, config):
                """Required abstract method implementation."""
                return cls()
                
            def to_dict(self):
                """Required abstract method implementation."""
                return {"type": "bad", "name": self.name}
        
        bad_generator = BadGenerator()
        
        # Try to add bad generator
        with pytest.raises(ValueError):
            sample_model.add.generator(bad_generator)
        
        # Verify model is completely unchanged
        assert len(sample_model.generators) == original_generators_count

    def test_add_generator_complex_scenario(self, sample_model: Model):
        """Test adding a generator in a more complex model scenario."""
        # Add more components to the model first
        sample_model.add.category(name="expenses")
        sample_model.add.line_item(name="interest_expense", category="expenses", values={2023: 0, 2024: 0, 2025: 0})
        
        # Now add a debt generator
        debt_generator = Debt(
            name="corporate_loan",
            par_amounts={2023: 500000},
            interest_rate=0.05,
            term=10
        )
        
        sample_model.add.generator(debt_generator)
        
        # Verify everything works together
        assert len(sample_model.generators) == 1
        assert len(sample_model._line_item_definitions) == 2
        assert len(sample_model._category_definitions) == 2
        
        # Verify we can access all values
        assert sample_model["revenue", 2023] == 100000
        
        # Verify generator values are accessible
        for gen_name in debt_generator.defined_names:
            value = sample_model[gen_name, 2023]
            assert isinstance(value, (int, float))


class TestAddCategory:
    
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

    def test_add_category_basic(self, sample_model: Model):
        """Test adding a basic category with minimal parameters."""
        initial_count = len(sample_model._category_definitions)
        
        sample_model.add.category(name="expenses")
        
        # Verify the category was added
        assert len(sample_model._category_definitions) == initial_count + 1
        
        # Find the added category
        new_category = next(category for category in sample_model._category_definitions if category.name == "expenses")
        assert new_category.name == "expenses"
        assert new_category.label == "expenses"  # Should default to name
        assert new_category.include_total == True  # Should default to True
        assert new_category.total_label == "Total expenses"  # Should default
        assert new_category.total_name == "total_expenses"

    def test_add_category_with_label(self, sample_model: Model):
        """Test adding a category with a custom label."""
        sample_model.add.category(
            name="operating_expenses",
            label="Operating Expenses"
        )
        
        # Find the added category
        new_category = next(category for category in sample_model._category_definitions if category.name == "operating_expenses")
        assert new_category.name == "operating_expenses"
        assert new_category.label == "Operating Expenses"
        assert new_category.total_label == "Total Operating Expenses"

    def test_add_category_with_total_label(self, sample_model: Model):
        """Test adding a category with custom total label."""
        sample_model.add.category(
            name="assets",
            label="Assets",
            total_label="Total Asset Value"
        )
        
        # Find the added category
        new_category = next(category for category in sample_model._category_definitions if category.name == "assets")
        assert new_category.name == "assets"
        assert new_category.label == "Assets"
        assert new_category.total_label == "Total Asset Value"
        assert new_category.total_name == "total_assets"

    def test_add_category_without_total(self, sample_model: Model):
        """Test adding a category with include_total=False."""
        sample_model.add.category(
            name="metrics",
            label="Key Metrics",
            include_total=False
        )
        
        # Find the added category
        new_category = next(category for category in sample_model._category_definitions if category.name == "metrics")
        assert new_category.name == "metrics"
        assert new_category.label == "Key Metrics"
        assert new_category.include_total == False
        assert new_category.total_label is None
        assert new_category.total_name is None

    def test_add_category_all_parameters(self, sample_model: Model):
        """Test adding a category with all parameters specified."""
        sample_model.add.category(
            name="liabilities",
            label="Liabilities",
            total_label="Total Debt",
            include_total=True
        )
        
        # Find the added category
        new_category = next(category for category in sample_model._category_definitions if category.name == "liabilities")
        assert new_category.name == "liabilities"
        assert new_category.label == "Liabilities"
        assert new_category.total_label == "Total Debt"
        assert new_category.include_total == True
        assert new_category.total_name == "total_liabilities"

    def test_add_category_duplicate_name_fails(self, sample_model: Model):
        """Test that adding a category with duplicate name fails."""
        with pytest.raises(ValueError) as excinfo:
            sample_model.add.category(name="income")  # This already exists
        
        assert "Failed to add category 'income'" in str(excinfo.value)
        assert "Duplicate category names" in str(excinfo.value)
        
        # Verify original model is unchanged
        assert len(sample_model._category_definitions) == 1

    def test_add_category_invalid_name_fails(self, sample_model: Model):
        """Test that adding a category with invalid name fails."""
        with pytest.raises(ValueError) as excinfo:
            sample_model.add.category(name="invalid name with spaces")  # Invalid name format
        
        assert "Failed to add category 'invalid name with spaces'" in str(excinfo.value)
        
        # Verify original model is unchanged
        assert len(sample_model._category_definitions) == 1

    def test_add_existing_category_instance(self, sample_model: Model):
        """Test adding an already-created Category instance."""
        initial_count = len(sample_model._category_definitions)
        
        # Create a Category instance first
        new_category = Category(
            name="equity",
            label="Equity",
            total_label="Total Equity",
            include_total=True
        )
        
        # Add the instance to the model
        sample_model.add.category(new_category)
        
        # Verify the category was added
        assert len(sample_model._category_definitions) == initial_count + 1
        
        # Find the added category
        added_category = next(category for category in sample_model._category_definitions if category.name == "equity")
        assert added_category is new_category  # Should be the exact same instance
        assert added_category.name == "equity"
        assert added_category.label == "Equity"
        assert added_category.total_label == "Total Equity"
        assert added_category.include_total == True

    def test_add_existing_category_duplicate_name_fails(self, sample_model: Model):
        """Test that adding a Category instance with duplicate name fails."""
        # Create a Category with a name that already exists
        duplicate_category = Category(name="income")  # This already exists
        
        with pytest.raises(ValueError) as excinfo:
            sample_model.add.category(duplicate_category)
        
        assert "Failed to add category 'income'" in str(excinfo.value)
        assert "Duplicate category names" in str(excinfo.value)
        
        # Verify original model is unchanged
        assert len(sample_model._category_definitions) == 1

    def test_add_category_both_params_fails(self, sample_model: Model):
        """Test that providing both category instance and name parameters fails."""
        category_instance = Category(name="test_category")
        
        with pytest.raises(ValueError) as excinfo:
            sample_model.add.category(
                category=category_instance,
                name="another_category"  # Both provided
            )
        
        assert "Cannot specify both 'category' and 'name' parameters" in str(excinfo.value)

    def test_add_category_neither_params_fails(self, sample_model: Model):
        """Test that providing neither category instance nor name parameters fails."""
        with pytest.raises(ValueError) as excinfo:
            sample_model.add.category()  # Neither provided
        
        assert "Must specify either 'category' parameter or 'name' parameter" in str(excinfo.value)

    def test_add_category_updates_defined_names_with_total(self, sample_model: Model):
        """Test that adding a category with total properly updates the model's defined names."""
        initial_names = [name['name'] for name in sample_model.defined_names]
        
        sample_model.add.category(
            name="expenses",
            label="Expenses",
            include_total=True
        )
        
        updated_names = [name['name'] for name in sample_model.defined_names]
        
        # The category itself doesn't appear in defined names, but its total does
        # (only if there are line items in the category)
        assert "expenses" not in updated_names  # Category name itself not in defined names
        assert "total_expenses" not in updated_names  # No line items in this category yet

    def test_add_category_with_line_items_creates_total(self, sample_model: Model):
        """Test that adding a category and then line items creates the total in defined names."""
        # Add a category
        sample_model.add.category(name="expenses", include_total=True)
        
        # Add a line item to that category
        sample_model.add.line_item(
            name="office_rent",
            category="expenses",
            values={2023: 5000, 2024: 5200, 2025: 5400}
        )
        
        # Now the total should appear in defined names
        updated_names = [name['name'] for name in sample_model.defined_names]
        assert "total_expenses" in updated_names
        
        # Check that the total appears with correct metadata
        total_def = next(name for name in sample_model.defined_names if name['name'] == 'total_expenses')
        assert total_def['source_type'] == 'category'
        assert total_def['source_name'] == 'expenses'
        assert total_def['label'] == 'Total expenses'

    def test_add_category_without_total_no_defined_name(self, sample_model: Model):
        """Test that adding a category with include_total=False doesn't create defined names."""
        initial_names = [name['name'] for name in sample_model.defined_names]
        
        sample_model.add.category(name="metrics", include_total=False)
        
        # Add a line item to that category
        sample_model.add.line_item(
            name="customer_count",
            category="metrics",
            values={2023: 100, 2024: 120, 2025: 150}
        )
        
        # No total should appear in defined names
        updated_names = [name['name'] for name in sample_model.defined_names]
        assert "total_metrics" not in updated_names
        assert "metrics" not in updated_names

    def test_add_category_preserves_all_attributes(self, sample_model: Model):
        """Test that all Category attributes are preserved when adding an instance."""
        # Create a Category with all possible attributes (with include_total=True)
        complex_category = Category(
            name="complex_category",
            label="Complex Category Label",
            total_label="Complex Total Label",
            include_total=True
        )
        
        # Add the instance
        sample_model.add.category(complex_category)
        
        # Find the added category and verify all attributes
        added_category = next(category for category in sample_model._category_definitions if category.name == "complex_category")
        assert added_category.name == "complex_category"
        assert added_category.label == "Complex Category Label"
        assert added_category.total_label == "Complex Total Label"
        assert added_category.include_total == True
        assert added_category.total_name == "total_complex_category"

    def test_add_category_returns_none(self, sample_model: Model):
        """Test that the method returns None (emphasizing side effect over return value)."""
        result = sample_model.add.category(name="test_return")
        
        # Verify method returns None
        assert result is None
        
        # Verify the category was still added to the model
        added_category = next(category for category in sample_model._category_definitions if category.name == "test_return")
        assert added_category.name == "test_return"

    def test_model_copy_validation_preserves_original(self, sample_model: Model):
        """Test that validation failures don't affect the original model."""
        original_categories_count = len(sample_model._category_definitions)
        
        # Try multiple failed additions
        with pytest.raises(ValueError):
            sample_model.add.category(name="income")  # Duplicate
        
        with pytest.raises(ValueError):
            sample_model.add.category(name="invalid name")  # Invalid name
        
        # Verify model is completely unchanged
        assert len(sample_model._category_definitions) == original_categories_count

    def test_add_category_to_empty_model(self):
        """Test adding a category to a model with no existing categories."""
        # Create model with no explicit categories (they'll be auto-generated)
        revenue = LineItem(name="revenue", category="income", values={2023: 100})
        model = Model(line_items=[revenue], years=[2023])
        
        # Should have auto-generated income category
        assert len(model._category_definitions) == 1
        assert model._category_definitions[0].name == "income"
        
        # Add another category
        model.add.category(name="expenses", label="Expenses")
        
        # Should now have both categories
        assert len(model._category_definitions) == 2
        category_names = [cat.name for cat in model._category_definitions]
        assert "income" in category_names
        assert "expenses" in category_names


class TestAddLineItem:
    
    @pytest.fixture
    def sample_model(self):
        """Create a sample model for testing."""
        revenue = LineItem(
            name="revenue",
            category="income",
            values={2023: 100000, 2024: 120000, 2025: 140000}
        )
        
        costs = LineItem(
            name="costs",
            category="expenses", 
            values={2023: 60000, 2024: 70000, 2025: 80000}
        )
        
        categories = [
            Category(name="income", label="Income"),
            Category(name="expenses", label="Expenses")
        ]
        
        return Model(
            line_items=[revenue, costs],
            years=[2023, 2024, 2025],
            categories=categories
        )

    def test_add_line_item_with_values(self, sample_model: Model):
        """Test adding a line item with explicit values."""
        initial_count = len(sample_model._line_item_definitions)
        
        sample_model.add.line_item(
            name="marketing",
            category="expenses",
            label="Marketing Costs",
            values={2023: 10000, 2024: 12000, 2025: 14000}
        )
        
        # Verify the line item was added
        assert len(sample_model._line_item_definitions) == initial_count + 1
        
        # Find the added item
        new_item = next(item for item in sample_model._line_item_definitions if item.name == "marketing")
        assert new_item.name == "marketing"
        assert new_item.category == "expenses"
        assert new_item.label == "Marketing Costs"
        assert new_item.values == {2023: 10000, 2024: 12000, 2025: 14000}
        
        # Verify it's accessible in the model
        assert sample_model["marketing", 2023] == 10000
        assert sample_model["marketing", 2024] == 12000
        assert sample_model["marketing", 2025] == 14000

    def test_add_line_item_with_formula(self, sample_model: Model):
        """Test adding a line item with a formula."""
        initial_count = len(sample_model._line_item_definitions)
        
        sample_model.add.line_item(
            name="profit",
            category="income",
            formula="revenue - costs",
            label="Net Profit"
        )
        
        # Verify the line item was added
        assert len(sample_model._line_item_definitions) == initial_count + 1
        
        # Find the added item
        new_item = next(item for item in sample_model._line_item_definitions if item.name == "profit")
        assert new_item.name == "profit"
        assert new_item.formula == "revenue - costs"
        
        # Verify the formula calculations work
        assert sample_model["profit", 2023] == 40000  # 100000 - 60000
        assert sample_model["profit", 2024] == 50000  # 120000 - 70000
        assert sample_model["profit", 2025] == 60000  # 140000 - 80000

    def test_add_line_item_minimal_params(self, sample_model: Model):
        """Test adding a line item with minimal required parameters and a simple formula."""
        sample_model.add.line_item(
            name="admin_costs",
            category="expenses",
            formula="costs * 0.1"  # Need formula to provide values for all years
        )
        
        # Find the added item
        new_item = next(item for item in sample_model._line_item_definitions if item.name == "admin_costs")
        assert new_item.name == "admin_costs"
        assert new_item.category == "expenses"
        assert new_item.label == "admin_costs"  # Should default to name
        assert new_item.values == {}
        assert new_item.formula == "costs * 0.1"
        assert new_item.value_format == "no_decimals"

    def test_add_line_item_with_all_params(self, sample_model: Model):
        """Test adding a line item with all parameters specified."""
        sample_model.add.line_item(
            name="depreciation",
            category="expenses",
            label="Depreciation Expense",
            values={2023: 5000},
            formula="depreciation[-1] * 1.1",
            value_format="currency"
        )
        
        # Find the added item
        new_item = next(item for item in sample_model._line_item_definitions if item.name == "depreciation")
        assert new_item.name == "depreciation"
        assert new_item.category == "expenses"
        assert new_item.label == "Depreciation Expense"
        assert new_item.values == {2023: 5000}
        assert new_item.formula == "depreciation[-1] * 1.1"
        assert new_item.value_format == "currency"

    def test_add_line_item_duplicate_name_fails(self, sample_model: Model):
        """Test that adding a line item with duplicate name fails."""
        with pytest.raises(ValueError) as excinfo:
            sample_model.add.line_item(
                name="revenue",  # This already exists
                category="income",
                values={2023: 50000}
            )
        
        assert "Failed to add line item 'revenue'" in str(excinfo.value)
        assert "Duplicate defined names" in str(excinfo.value)
        
        # Verify original model is unchanged
        assert len(sample_model._line_item_definitions) == 2
        assert sample_model["revenue", 2023] == 100000  # Original value unchanged

    def test_add_line_item_invalid_category_fails(self, sample_model: Model):
        """Test that adding a line item with invalid category fails."""
        with pytest.raises(ValueError) as excinfo:
            sample_model.add.line_item(
                name="bad_item",
                category="nonexistent_category",
                values={2023: 1000}
            )
        
        assert "Failed to add line item 'bad_item'" in str(excinfo.value)
        assert "not defined category" in str(excinfo.value)
        
        # Verify original model is unchanged
        assert len(sample_model._line_item_definitions) == 2

    def test_add_line_item_invalid_formula_fails(self, sample_model: Model):
        """Test that adding a line item with invalid formula fails."""
        with pytest.raises(ValueError) as excinfo:
            sample_model.add.line_item(
                name="bad_calc",
                category="income",
                formula="revenue - nonexistent_variable"
            )
        
        assert "Failed to add line item 'bad_calc'" in str(excinfo.value)
        assert "not found" in str(excinfo.value)
        
        # Verify original model is unchanged
        assert len(sample_model._line_item_definitions) == 2

    def test_add_line_item_invalid_name_fails(self, sample_model: Model):
        """Test that adding a line item with invalid name fails."""
        with pytest.raises(ValueError) as excinfo:
            sample_model.add.line_item(
                name="invalid name with spaces",  # Invalid name format
                category="income",
                values={2023: 1000}
            )
        
        assert "Failed to add line item 'invalid name with spaces'" in str(excinfo.value)
        
        # Verify original model is unchanged
        assert len(sample_model._line_item_definitions) == 2

    def test_model_copy_validation_preserves_original(self, sample_model: Model):
        """Test that validation failures don't affect the original model."""
        original_line_items = [item.name for item in sample_model._line_item_definitions]
        original_revenue_value = sample_model["revenue", 2023]
        
        # Try multiple failed additions
        with pytest.raises(ValueError):
            sample_model.add.line_item(name="revenue", category="income")
        
        with pytest.raises(ValueError):
            sample_model.add.line_item(name="bad", category="bad_category")
        
        with pytest.raises(ValueError):
            sample_model.add.line_item(name="bad_formula", category="income", formula="nonexistent")
        
        # Verify model is completely unchanged
        current_line_items = [item.name for item in sample_model._line_item_definitions]
        assert current_line_items == original_line_items
        assert sample_model["revenue", 2023] == original_revenue_value

    def test_add_line_item_updates_defined_names(self, sample_model: Model):
        """Test that adding a line item properly updates the model's defined names."""
        initial_names = [name['name'] for name in sample_model.defined_names]
        
        sample_model.add.line_item(
            name="new_item",
            category="income",
            values={2023: 1000, 2024: 1100, 2025: 1200}  # Provide values for all years
        )
        
        updated_names = [name['name'] for name in sample_model.defined_names]
        assert "new_item" in updated_names
        assert len(updated_names) == len(initial_names) + 1

    def test_add_line_item_returns_none(self, sample_model: Model):
        """Test that the method returns None (emphasizing side effect over return value)."""
        result = sample_model.add.line_item(
            name="test_return",
            category="income",
            values={2023: 1000, 2024: 1100, 2025: 1200}  # Provide values for all years
        )
        
        # Verify method returns None
        assert result is None
        
        # Verify the line item was still added to the model
        added_item = next(item for item in sample_model._line_item_definitions if item.name == "test_return")
        assert added_item.name == "test_return"

    def test_add_existing_line_item_instance(self, sample_model: Model):
        """Test adding an already-created LineItem instance."""
        initial_count = len(sample_model._line_item_definitions)
        
        # Create a LineItem instance first
        new_line_item = LineItem(
            name="consulting",
            category="income",
            label="Consulting Revenue",
            values={2023: 25000, 2024: 30000, 2025: 35000}
        )
        
        # Add the instance to the model
        sample_model.add.line_item(new_line_item)
        
        # Verify the line item was added
        assert len(sample_model._line_item_definitions) == initial_count + 1
        
        # Find the added item
        added_item = next(item for item in sample_model._line_item_definitions if item.name == "consulting")
        assert added_item is new_line_item  # Should be the exact same instance
        assert added_item.name == "consulting"
        assert added_item.category == "income"
        assert added_item.label == "Consulting Revenue"
        assert added_item.values == {2023: 25000, 2024: 30000, 2025: 35000}
        
        # Verify it's accessible in the model
        assert sample_model["consulting", 2023] == 25000
        assert sample_model["consulting", 2024] == 30000
        assert sample_model["consulting", 2025] == 35000

    def test_add_existing_line_item_with_formula(self, sample_model: Model):
        """Test adding a LineItem instance that uses a formula."""
        # Create a LineItem instance with a formula
        profit_margin = LineItem(
            name="profit_margin",
            category="income",
            formula="(revenue - costs) / revenue",
            label="Profit Margin %",
            value_format="percentage"
        )
        
        # Add the instance to the model
        sample_model.add.line_item(profit_margin)
        
        # Find the added item
        added_item = next(item for item in sample_model._line_item_definitions if item.name == "profit_margin")
        assert added_item.formula == "(revenue - costs) / revenue"
        assert added_item.value_format == "percentage"
        
        # Verify the formula calculations work
        # 2023: (100000 - 60000) / 100000 = 0.4
        assert sample_model["profit_margin", 2023] == 0.4

    def test_add_line_item_missing_category_fails(self, sample_model: Model):
        """Test that passing a name without category parameter fails."""
        with pytest.raises(TypeError) as excinfo:
            sample_model.add.line_item(name="new_item")  # Missing category
        
        assert "When creating a new LineItem, 'category' parameter is required" in str(excinfo.value)
        
        # Verify original model is unchanged
        assert len(sample_model._line_item_definitions) == 2

    def test_add_existing_line_item_duplicate_name_fails(self, sample_model: Model):
        """Test that adding a LineItem instance with duplicate name fails."""
        # Create a LineItem with a name that already exists
        duplicate_item = LineItem(
            name="revenue",  # This already exists in the model
            category="income",
            values={2023: 50000}
        )
        
        with pytest.raises(ValueError) as excinfo:
            sample_model.add.line_item(duplicate_item)
        
        assert "Failed to add line item 'revenue'" in str(excinfo.value)
        assert "Duplicate defined names" in str(excinfo.value)
        
        # Verify original model is unchanged
        assert len(sample_model._line_item_definitions) == 2
        assert sample_model["revenue", 2023] == 100000  # Original value unchanged

    def test_add_existing_line_item_invalid_category_fails(self, sample_model: Model):
        """Test that adding a LineItem instance with invalid category fails."""
        # Create a LineItem with an invalid category
        bad_item = LineItem(
            name="bad_item",
            category="nonexistent_category",
            values={2023: 1000}
        )
        
        with pytest.raises(ValueError) as excinfo:
            sample_model.add.line_item(bad_item)
        
        assert "Failed to add line item 'bad_item'" in str(excinfo.value)
        assert "not defined category" in str(excinfo.value)
        
        # Verify original model is unchanged
        assert len(sample_model._line_item_definitions) == 2

    def test_add_existing_line_item_preserves_all_attributes(self, sample_model: Model):
        """Test that all LineItem attributes are preserved when adding an instance."""
        # Create a LineItem with all possible attributes
        complex_item = LineItem(
            name="complex_calculation",
            category="income",
            label="Complex Revenue Calculation",
            values={2023: 10000},  # Explicit value for first year
            formula="complex_calculation[-1] * 1.15",  # Formula for subsequent years
            value_format="currency"
        )
        
        # Add the instance
        sample_model.add.line_item(complex_item)
        
        # Find the added item and verify all attributes
        added_item = next(item for item in sample_model._line_item_definitions if item.name == "complex_calculation")
        assert added_item.name == "complex_calculation"
        assert added_item.category == "income"
        assert added_item.label == "Complex Revenue Calculation"
        assert added_item.values == {2023: 10000}
        assert added_item.formula == "complex_calculation[-1] * 1.15"
        assert added_item.value_format == "currency"
        
        # Verify calculations work (explicit value for 2023, formula for others)
        assert sample_model["complex_calculation", 2023] == 10000
        assert sample_model["complex_calculation", 2024] == 11500  # 10000 * 1.15

    def test_add_line_item_type_flexibility(self, sample_model: Model):
        """Test that both string and LineItem types work interchangeably."""
        initial_count = len(sample_model._line_item_definitions)
        
        # Method 1: Using string and parameters
        sample_model.add.line_item(
            name="method1_item",
            category="expenses",
            values={2023: 1000, 2024: 1100, 2025: 1200}
        )
        
        # Method 2: Using LineItem instance
        method2_item = LineItem(
            name="method2_item",
            category="expenses",
            values={2023: 2000, 2024: 2200, 2025: 2400}
        )
        sample_model.add.line_item(method2_item)
        
        # Verify both were added correctly
        assert len(sample_model._line_item_definitions) == initial_count + 2
        
        # Both should be accessible and functional
        assert sample_model["method1_item", 2023] == 1000
        assert sample_model["method2_item", 2023] == 2000
        
        # Find both items to verify they were added correctly
        item1 = next(item for item in sample_model._line_item_definitions if item.name == "method1_item")
        item2 = next(item for item in sample_model._line_item_definitions if item.name == "method2_item")
        
        assert item1.category == "expenses"
        assert item2.category == "expenses"
        assert item2 is method2_item  # Should be the same instance

    def test_add_line_item_both_parameters_fails(self, sample_model: Model):
        """Test that providing both line_item and name parameters fails."""
        existing_item = LineItem(
            name="test_item",
            category="income",
            values={2023: 1000}
        )
        
        with pytest.raises(ValueError) as excinfo:
            sample_model.add.line_item(line_item=existing_item, name="another_name")
        
        assert "Cannot specify both 'line_item' and 'name' parameters" in str(excinfo.value)
        
        # Verify original model is unchanged
        assert len(sample_model._line_item_definitions) == 2

    def test_add_line_item_no_parameters_fails(self, sample_model: Model):
        """Test that providing neither line_item nor name parameters fails."""
        with pytest.raises(ValueError) as excinfo:
            sample_model.add.line_item()
        
        assert "Must specify either 'line_item' parameter or 'name' parameter" in str(excinfo.value)
        
        # Verify original model is unchanged
        assert len(sample_model._line_item_definitions) == 2
