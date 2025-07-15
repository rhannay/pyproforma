import pytest
from pyproforma import LineItem, Model, Category
from pyproforma.models.model_delete import DeleteNamespace
from pyproforma.generators.debt import Debt


class TestDeleteNameSpaceInit:
    def test_delete_namespace_init(self):
        """Test that DeleteNamespace initializes correctly with a model."""
        model = Model(
            line_items=[LineItem(name="revenue", category="income", values={2023: 100})],
            years=[2023]
        )
        delete_namespace = DeleteNamespace(model)
        assert delete_namespace._model is model


class TestDeleteGenerator:
    
    @pytest.fixture
    def sample_model_with_generators(self):
        """Create a sample model with generators for testing."""
        revenue = LineItem(
            name="revenue",
            category="income",
            values={2023: 100000, 2024: 120000, 2025: 140000}
        )
        
        # Create generators
        debt1 = Debt(
            name="loan1",
            par_amounts={2023: 100000},
            interest_rate=0.05,
            term=5
        )
        
        debt2 = Debt(
            name="loan2",
            par_amounts={2023: 50000},
            interest_rate=0.04,
            term=3
        )
        
        categories = [Category(name="income", label="Income")]
        
        return Model(
            line_items=[revenue],
            years=[2023, 2024, 2025],
            categories=categories,
            generators=[debt1, debt2]
        )

    def test_delete_generator_basic(self, sample_model_with_generators):
        """Test basic generator deletion."""
        initial_count = len(sample_model_with_generators.generators)
        initial_names = [name['name'] for name in sample_model_with_generators.defined_names]
        
        # Get the generator names before deletion
        loan1_generator = next(gen for gen in sample_model_with_generators.generators if gen.name == "loan1")
        loan1_defined_names = loan1_generator.defined_names
        
        # Verify generator names are in defined names
        for gen_name in loan1_defined_names:
            assert gen_name in initial_names
        
        # Delete the generator
        sample_model_with_generators.delete.generator("loan1")
        
        # Verify the generator was removed
        assert len(sample_model_with_generators.generators) == initial_count - 1
        
        # Verify it's no longer in generators
        generator_names = [gen.name for gen in sample_model_with_generators.generators]
        assert "loan1" not in generator_names
        assert "loan2" in generator_names  # Other generator should still be there
        
        # Verify generator names are removed from defined names
        updated_names = [name['name'] for name in sample_model_with_generators.defined_names]
        for gen_name in loan1_defined_names:
            assert gen_name not in updated_names
        
        # Verify we can't access deleted generator values anymore
        for gen_name in loan1_defined_names:
            with pytest.raises(KeyError):
                sample_model_with_generators[gen_name, 2023]

    def test_delete_generator_not_found(self, sample_model_with_generators):
        """Test that deleting a non-existent generator raises KeyError."""
        with pytest.raises(KeyError) as excinfo:
            sample_model_with_generators.delete.generator("nonexistent_generator")
        
        assert "Generator 'nonexistent_generator' not found in model" in str(excinfo.value)
        
        # Verify model is unchanged
        assert len(sample_model_with_generators.generators) == 2

    def test_delete_generator_used_in_formula_fails(self):
        """Test that deleting a generator used in a formula fails validation."""
        # Create a debt generator
        debt_generator = Debt(
            name="debt",
            par_amounts={2023: 100000},
            interest_rate=0.05,
            term=5
        )
        
        base_revenue = LineItem(
            name="base_revenue",
            category="income",
            values={2023: 100000, 2024: 110000, 2025: 120000}
        )
        
        model = Model(
            line_items=[base_revenue],
            years=[2023, 2024, 2025],
            categories=[Category(name="income")],
            generators=[debt_generator]
        )
        
        # Get one of the generator's defined names to use in a formula
        debt_names = debt_generator.defined_names
        debt_variable = debt_names[0]  # Use the first one
        
        # Add a line item that uses the generator in its formula
        model.add.line_item(
            name="net_income",
            category="income",
            formula=f"base_revenue - {debt_variable}"
        )
        
        # Try to delete the generator that's used in a formula
        with pytest.raises(ValueError) as excinfo:
            model.delete.generator("debt")
        
        assert "Failed to delete generator 'debt'" in str(excinfo.value)
        
        # Verify model is unchanged
        assert len(model.generators) == 1
        assert model[debt_variable, 2023] is not None  # Should still be accessible

    def test_delete_generator_updates_defined_names(self, sample_model_with_generators):
        """Test that deleting a generator properly updates the model's defined names."""
        # Get generator defined names before deletion
        loan2_generator = next(gen for gen in sample_model_with_generators.generators if gen.name == "loan2")
        loan2_defined_names = loan2_generator.defined_names
        
        initial_names = [name['name'] for name in sample_model_with_generators.defined_names]
        initial_generator_names = [name['name'] for name in sample_model_with_generators.defined_names if name['source_type'] == 'generator']
        
        # Verify loan2 names are in defined names
        for gen_name in loan2_defined_names:
            assert gen_name in initial_generator_names
        
        # Delete the generator
        sample_model_with_generators.delete.generator("loan2")
        
        updated_names = [name['name'] for name in sample_model_with_generators.defined_names]
        updated_generator_names = [name['name'] for name in sample_model_with_generators.defined_names if name['source_type'] == 'generator']
        
        # Verify loan2 names are removed from defined names
        for gen_name in loan2_defined_names:
            assert gen_name not in updated_names
            assert gen_name not in updated_generator_names
        
        # Verify loan1 names are still there
        loan1_generator = next(gen for gen in sample_model_with_generators.generators if gen.name == "loan1")
        loan1_defined_names = loan1_generator.defined_names
        for gen_name in loan1_defined_names:
            assert gen_name in updated_names

    def test_delete_generator_preserves_other_generators(self, sample_model_with_generators):
        """Test that deleting one generator doesn't affect others."""
        # Get initial state of both generators
        loan1_generator = next(gen for gen in sample_model_with_generators.generators if gen.name == "loan1")
        loan2_generator = next(gen for gen in sample_model_with_generators.generators if gen.name == "loan2")
        
        loan1_names = loan1_generator.defined_names
        loan2_names = loan2_generator.defined_names
        
        # Verify both generators' values are accessible initially
        for gen_name in loan1_names:
            assert sample_model_with_generators[gen_name, 2023] is not None
        for gen_name in loan2_names:
            assert sample_model_with_generators[gen_name, 2023] is not None
        
        # Delete loan1
        sample_model_with_generators.delete.generator("loan1")
        
        # Verify loan2 is unchanged and still accessible
        remaining_generator = next(gen for gen in sample_model_with_generators.generators if gen.name == "loan2")
        assert remaining_generator.name == "loan2"
        
        for gen_name in loan2_names:
            assert sample_model_with_generators[gen_name, 2023] is not None
        
        # Verify loan1 names are no longer accessible
        for gen_name in loan1_names:
            with pytest.raises(KeyError):
                sample_model_with_generators[gen_name, 2023]

    def test_delete_generator_returns_none(self, sample_model_with_generators):
        """Test that the method returns None (emphasizing side effect over return value)."""
        result = sample_model_with_generators.delete.generator("loan1")
        
        # Verify method returns None
        assert result is None
        
        # Verify the generator was still deleted from the model
        assert len(sample_model_with_generators.generators) == 1

    def test_model_copy_validation_preserves_original(self):
        """Test that validation failures don't affect the original model."""
        # Create model with generator used in formula
        debt_generator = Debt(name="debt", par_amounts={2023: 100000}, interest_rate=0.05, term=5)
        
        base_revenue = LineItem(name="base_revenue", category="income", values={2023: 100000})
        
        model = Model(
            line_items=[base_revenue],
            years=[2023],
            categories=[Category(name="income")],
            generators=[debt_generator]
        )
        
        # Add line item that depends on the generator
        debt_names = debt_generator.defined_names
        debt_variable = debt_names[0]
        
        model.add.line_item(
            name="calculated_item",
            category="income",
            formula=f"base_revenue - {debt_variable}"
        )
        
        original_generators_count = len(model.generators)
        original_debt_value = model[debt_variable, 2023]
        
        # Try to delete generator that would break the model
        with pytest.raises(ValueError):
            model.delete.generator("debt")
        
        # Verify model is completely unchanged
        assert len(model.generators) == original_generators_count
        assert model[debt_variable, 2023] == original_debt_value
        # Verify the formula still works
        assert model["calculated_item", 2023] is not None

    def test_delete_last_generator(self):
        """Test deleting the only generator in a model."""
        debt_generator = Debt(name="single_debt", par_amounts={2023: 50000}, interest_rate=0.04, term=3)
        
        revenue = LineItem(name="revenue", category="income", values={2023: 100000})
        
        model = Model(
            line_items=[revenue],
            years=[2023],
            categories=[Category(name="income")],
            generators=[debt_generator]
        )
        
        # Verify generator exists
        assert len(model.generators) == 1
        debt_names = debt_generator.defined_names
        for debt_name in debt_names:
            assert model[debt_name, 2023] is not None
        
        # Delete the only generator
        model.delete.generator("single_debt")
        
        # Verify model has no generators
        assert len(model.generators) == 0
        
        # Verify generator names are not in defined names
        generator_names = [name['name'] for name in model.defined_names if name['source_type'] == 'generator']
        assert len(generator_names) == 0

    def test_delete_generator_with_empty_model(self):
        """Test that deleting from a model with no generators raises appropriate error."""
        model = Model(
            line_items=[LineItem(name="revenue", category="income", values={2023: 100})],
            years=[2023],
            categories=[Category(name="income")]
        )
        
        # Try to delete generator from model with no generators
        with pytest.raises(KeyError) as excinfo:
            model.delete.generator("nonexistent")
        
        assert "Generator 'nonexistent' not found in model" in str(excinfo.value)

    def test_delete_generator_complex_scenario(self):
        """Test deleting a generator in a complex model scenario."""
        # Create a complex model with multiple components
        debt1 = Debt(name="debt1", par_amounts={2023: 100000}, interest_rate=0.05, term=5)
        debt2 = Debt(name="debt2", par_amounts={2023: 50000}, interest_rate=0.04, term=3)
        
        revenue = LineItem(name="revenue", category="income", values={2023: 200000})
        expenses = LineItem(name="expenses", category="costs", values={2023: 100000})
        
        model = Model(
            line_items=[revenue, expenses],
            years=[2023],
            categories=[Category(name="income"), Category(name="costs")],
            generators=[debt1, debt2]
        )
        
        # Verify initial state
        assert len(model.generators) == 2
        assert len(model._line_item_definitions) == 2
        
        # Delete one generator
        model.delete.generator("debt1")
        
        # Verify deletion worked and other components are intact
        assert len(model.generators) == 1
        assert model.generators[0].name == "debt2"
        assert len(model._line_item_definitions) == 2
        
        # Verify remaining components still work
        assert model["revenue", 2023] == 200000
        
        # Verify remaining generator still works
        debt2_names = model.generators[0].defined_names
        for debt_name in debt2_names:
            assert model[debt_name, 2023] is not None


class TestDeleteCategory:
    
    @pytest.fixture
    def sample_model_with_categories(self):
        """Create a sample model with multiple categories for testing."""
        revenue = LineItem(
            name="revenue",
            category="income",
            values={2023: 100000, 2024: 120000, 2025: 140000}
        )
        
        categories = [
            Category(name="income", label="Income"),
            Category(name="expenses", label="Expenses"),
            Category(name="unused_category", label="Unused Category")
        ]
        
        return Model(
            line_items=[revenue],
            years=[2023, 2024, 2025],
            categories=categories
        )

    def test_delete_category_basic(self, sample_model_with_categories: Model):
        """Test basic category deletion for unused category."""
        initial_count = len(sample_model_with_categories._category_definitions)
        
        # Delete the unused category
        sample_model_with_categories.delete.category("unused_category")
        
        # Verify the category was removed
        assert len(sample_model_with_categories._category_definitions) == initial_count - 1
        
        # Verify it's no longer in categories
        category_names = [cat.name for cat in sample_model_with_categories._category_definitions]
        assert "unused_category" not in category_names
        assert "income" in category_names  # Other categories should still be there
        assert "expenses" in category_names

    def test_delete_category_not_found(self, sample_model_with_categories: Model):
        """Test that deleting a non-existent category raises KeyError."""
        with pytest.raises(KeyError) as excinfo:
            sample_model_with_categories.delete.category("nonexistent_category")
        
        assert "Category 'nonexistent_category' not found in model" in str(excinfo.value)
        
        # Verify model is unchanged
        assert len(sample_model_with_categories._category_definitions) == 3

    def test_delete_category_used_by_line_items_fails(self, sample_model_with_categories: Model):
        """Test that deleting a category used by line items fails."""
        with pytest.raises(ValueError) as excinfo:
            sample_model_with_categories.delete.category("income")  # Used by revenue line item
        
        assert "Cannot delete category 'income' because it is used by line items: revenue" in str(excinfo.value)
        
        # Verify model is unchanged
        assert len(sample_model_with_categories._category_definitions) == 3
        category_names = [cat.name for cat in sample_model_with_categories._category_definitions]
        assert "income" in category_names

    def test_delete_category_used_by_multiple_line_items_fails(self):
        """Test that deleting a category used by multiple line items fails with all names listed."""
        revenue = LineItem(name="revenue", category="income", values={2023: 100})
        profit = LineItem(name="profit", category="income", values={2023: 50})
        
        model = Model(
            line_items=[revenue, profit],
            years=[2023],
            categories=[Category(name="income"), Category(name="expenses")]
        )
        
        with pytest.raises(ValueError) as excinfo:
            model.delete.category("income")
        
        assert "Cannot delete category 'income' because it is used by line items: revenue, profit" in str(excinfo.value)

    def test_delete_category_with_total_removes_from_defined_names(self):
        """Test that deleting a category removes its total from defined names."""
        # Create model with category that has line items (so total appears in defined names)
        revenue = LineItem(name="revenue", category="income", values={2023: 100})
        expenses = LineItem(name="expenses", category="costs", values={2023: 50})
        
        model = Model(
            line_items=[revenue, expenses],
            years=[2023],
            categories=[
                Category(name="income", include_total=True),
                Category(name="costs", include_total=True),
                Category(name="unused", include_total=True)
            ]
        )
        
        # Verify totals are in defined names
        initial_names = [name['name'] for name in model.defined_names]
        assert "total_income" in initial_names
        assert "total_costs" in initial_names
        assert "total_unused" not in initial_names  # No line items in unused category
        
        # Delete unused category (this should work since no line items use it)
        model.delete.category("unused")
        
        # Verify category is gone but totals for used categories remain
        updated_names = [name['name'] for name in model.defined_names]
        assert "total_income" in updated_names
        assert "total_costs" in updated_names
        
        # Verify the unused category is gone from categories
        category_names = [cat.name for cat in model._category_definitions]
        assert "unused" not in category_names

    def test_delete_category_returns_none(self, sample_model_with_categories):
        """Test that the method returns None (emphasizing side effect over return value)."""
        result = sample_model_with_categories.delete.category("unused_category")
        
        # Verify method returns None
        assert result is None
        
        # Verify the category was still deleted from the model
        assert len(sample_model_with_categories._category_definitions) == 2

    def test_model_copy_validation_preserves_original(self, sample_model_with_categories: Model):
        """Test that validation failures don't affect the original model."""
        original_categories_count = len(sample_model_with_categories._category_definitions)
        original_category_names = [cat.name for cat in sample_model_with_categories._category_definitions]
        
        # Try to delete category that's in use
        with pytest.raises(ValueError):
            sample_model_with_categories.delete.category("income")  # Used by revenue
        
        # Verify model is completely unchanged
        assert len(sample_model_with_categories._category_definitions) == original_categories_count
        current_category_names = [cat.name for cat in sample_model_with_categories._category_definitions]
        assert current_category_names == original_category_names

    def test_delete_last_unused_category(self):
        """Test deleting when only one unused category remains."""
        revenue = LineItem(name="revenue", category="income", values={2023: 100})
        
        model = Model(
            line_items=[revenue],
            years=[2023],
            categories=[
                Category(name="income"),
                Category(name="unused")
            ]
        )
        
        # Verify both categories exist
        assert len(model._category_definitions) == 2
        
        # Delete the unused category
        model.delete.category("unused")
        
        # Verify only income category remains
        assert len(model._category_definitions) == 1
        assert model._category_definitions[0].name == "income"

    def test_delete_category_with_empty_categories_list(self):
        """Test that deleting from a model with no categories raises appropriate error."""
        # This is actually impossible in practice since Model requires line items
        # and line items require categories, but test the error handling
        revenue = LineItem(name="revenue", category="income", values={2023: 100})
        model = Model(line_items=[revenue], years=[2023])  # Auto-generates categories
        
        # Try to delete non-existent category
        with pytest.raises(KeyError) as excinfo:
            model.delete.category("nonexistent")
        
        assert "Category 'nonexistent' not found in model" in str(excinfo.value)

    def test_delete_category_cascade_effect_check(self):
        """Test that the delete operation properly validates cascade effects."""
        # Create a complex model to test validation
        revenue = LineItem(name="revenue", category="income", values={2023: 100})
        salary = LineItem(name="salary", category="expenses", values={2023: 60})
        rent = LineItem(name="rent", category="expenses", values={2023: 20})
        
        model = Model(
            line_items=[revenue, salary, rent],
            years=[2023],
            categories=[
                Category(name="income"),
                Category(name="expenses"),
                Category(name="assets")  # Unused
            ]
        )
        
        # Should be able to delete unused category
        model.delete.category("assets")
        
        # Should not be able to delete used categories
        with pytest.raises(ValueError):
            model.delete.category("income")
        
        with pytest.raises(ValueError):
            model.delete.category("expenses")
        
        # Verify model still has the used categories
        category_names = [cat.name for cat in model._category_definitions]
        assert "income" in category_names
        assert "expenses" in category_names
        assert "assets" not in category_names


class TestDeleteLineItem:
    
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

        marketing = LineItem(
            name="marketing",
            category="expenses",
            values={2023: 10000, 2024: 12000, 2025: 14000}
        )
        
        categories = [
            Category(name="income", label="Income"),
            Category(name="expenses", label="Expenses")
        ]
        
        return Model(
            line_items=[revenue, costs, marketing],
            years=[2023, 2024, 2025],
            categories=categories
        )

    def test_delete_line_item_basic(self, sample_model: Model):
        """Test basic line item deletion."""
        initial_count = len(sample_model._line_item_definitions)
        
        # Verify the item exists before deletion
        assert sample_model["marketing", 2023] == 10000
        
        # Delete the line item
        sample_model.delete.line_item("marketing")
        
        # Verify the line item was removed
        assert len(sample_model._line_item_definitions) == initial_count - 1
        
        # Verify the item is no longer accessible
        with pytest.raises(KeyError):
            sample_model["marketing", 2023]
        
        # Verify remaining items are still accessible
        assert sample_model["revenue", 2023] == 100000
        assert sample_model["costs", 2023] == 60000

    def test_delete_line_item_nonexistent_fails(self, sample_model: Model):
        """Test that deleting a non-existent line item fails."""
        with pytest.raises(KeyError) as excinfo:
            sample_model.delete.line_item("nonexistent_item")
        
        assert "Line item 'nonexistent_item' not found in model" in str(excinfo.value)
        
        # Verify original model is unchanged
        assert len(sample_model._line_item_definitions) == 3

    def test_delete_line_item_updates_defined_names(self, sample_model: Model):
        """Test that deleting a line item properly updates the model's defined names."""
        initial_names = [name['name'] for name in sample_model.defined_names]
        assert "marketing" in initial_names
        
        sample_model.delete.line_item("marketing")
        
        updated_names = [name['name'] for name in sample_model.defined_names]
        assert "marketing" not in updated_names
        assert len(updated_names) == len(initial_names) - 1

    def test_delete_line_item_returns_none(self, sample_model: Model):
        """Test that the method returns None (emphasizing side effect over return value)."""
        result = sample_model.delete.line_item("marketing")
        
        # Verify method returns None
        assert result is None
        
        # Verify the line item was still removed from the model
        assert len(sample_model._line_item_definitions) == 2
        with pytest.raises(KeyError):
            sample_model["marketing", 2023]

    def test_delete_line_item_with_formula_dependency_fails(self, sample_model: Model):
        """Test that deleting a line item that other formulas depend on fails."""
        # Add a line item that depends on 'revenue'
        sample_model.add.line_item(
            name="profit",
            category="income",
            formula="revenue - costs"
        )
        
        # Try to delete revenue (which profit depends on)
        with pytest.raises(ValueError) as excinfo:
            sample_model.delete.line_item("revenue")
        
        assert "Failed to delete line item 'revenue'" in str(excinfo.value)
        
        # Verify original model is unchanged
        assert len(sample_model._line_item_definitions) == 4
        assert sample_model["revenue", 2023] == 100000

    def test_delete_line_item_last_in_category(self, sample_model: Model):
        """Test deleting the last line item in a category."""
        # First, delete marketing to leave only costs in expenses
        sample_model.delete.line_item("marketing")
        
        # Now delete the last item in expenses category
        sample_model.delete.line_item("costs")
        
        # Verify the item was removed
        assert len(sample_model._line_item_definitions) == 1
        
        # Verify category totals still work for remaining categories
        assert sample_model.category_total("income", 2023) == 100000
        
        # Verify accessing the deleted category total raises an error
        with pytest.raises(KeyError):
            sample_model.category_total("expenses", 2023)

    def test_delete_multiple_line_items(self, sample_model: Model):
        """Test deleting multiple line items in sequence."""
        initial_count = len(sample_model._line_item_definitions)
        
        # Delete first item
        sample_model.delete.line_item("marketing")
        assert len(sample_model._line_item_definitions) == initial_count - 1
        
        # Delete second item
        sample_model.delete.line_item("costs")
        assert len(sample_model._line_item_definitions) == initial_count - 2
        
        # Verify only revenue remains
        assert len(sample_model._line_item_definitions) == 1
        assert sample_model._line_item_definitions[0].name == "revenue"
        assert sample_model["revenue", 2023] == 100000

    def test_delete_line_item_model_validation(self, sample_model: Model):
        """Test that model validation still works after deletion."""
        # Delete a line item
        sample_model.delete.line_item("marketing")
        
        # Add a new line item to ensure model is still functional
        sample_model.add.line_item(
            name="new_expense",
            category="expenses",
            values={2023: 5000, 2024: 6000, 2025: 7000}
        )
        
        # Verify the new item works
        assert sample_model["new_expense", 2023] == 5000
        assert len(sample_model._line_item_definitions) == 3

    def test_delete_line_item_preserves_other_items(self, sample_model: Model):
        """Test that deleting one item doesn't affect others."""
        # Record initial values
        initial_revenue = sample_model["revenue", 2023]
        initial_costs = sample_model["costs", 2023]
        
        # Delete marketing
        sample_model.delete.line_item("marketing")
        
        # Verify other items are unchanged
        assert sample_model["revenue", 2023] == initial_revenue
        assert sample_model["costs", 2023] == initial_costs
        
        # Verify their attributes are unchanged
        revenue_item = sample_model.get_line_item_definition("revenue")
        assert revenue_item.category == "income"
        assert revenue_item.values == {2023: 100000, 2024: 120000, 2025: 140000}

    def test_delete_line_item_edge_case_single_item(self):
        """Test deleting the only line item in a model."""
        single_item_model = Model(
            line_items=[LineItem(name="only_item", category="test", values={2023: 100})],
            years=[2023]
        )
        
        # Delete the only item
        single_item_model.delete.line_item("only_item")
        
        # Verify the model is now empty
        assert len(single_item_model._line_item_definitions) == 0
        
        # Verify we can't access the deleted item
        with pytest.raises(KeyError):
            single_item_model["only_item", 2023]
