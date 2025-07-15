import pytest
from pyproforma import LineItem, Model
from pyproforma.models.line_item import Category


class TestUpdateCategory:
    
    @pytest.fixture
    def sample_model_with_categories(self):
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
            Category(name="unused", label="Unused Category", include_total=False)
        ]
        
        return Model(
            line_items=[revenue, salary],
            years=[2023, 2024, 2025],
            categories=categories
        )

    def test_update_category_label(self, sample_model_with_categories: Model):
        """Test updating category label."""
        # Update label
        sample_model_with_categories.update.category(
            "income",
            label="Revenue Streams"
        )
        
        # Verify the label was updated
        category = next(cat for cat in sample_model_with_categories._category_definitions if cat.name == "income")
        assert category.label == "Revenue Streams"
        
        # Verify other attributes remained the same
        assert category.name == "income"
        assert category.include_total == True
        assert category.total_name == "total_income"
        assert category.total_label == "Total Income"  # Should use original label for total

    def test_update_category_total_label(self, sample_model_with_categories: Model):
        """Test updating category total label."""
        # Update total label
        sample_model_with_categories.update.category(
            "income",
            total_label="Total Revenue"
        )
        
        # Verify the total label was updated
        category = next(cat for cat in sample_model_with_categories._category_definitions if cat.name == "income")
        assert category.total_label == "Total Revenue"
        
        # Verify other attributes remained the same
        assert category.label == "Income"
        assert category.include_total == True
        
        # Verify defined names reflect the change
        total_def = next(name for name in sample_model_with_categories.defined_names if name['name'] == 'total_income')
        assert total_def['label'] == "Total Revenue"

    def test_update_category_include_total(self, sample_model_with_categories):
        """Test updating category include_total setting."""
        # Initially has total
        initial_names = [name['name'] for name in sample_model_with_categories.defined_names]
        assert "total_income" in initial_names
        
        # Update to not include total
        sample_model_with_categories.update.category(
            "income",
            include_total=False
        )
        
        # Verify the include_total was updated
        category = next(cat for cat in sample_model_with_categories._category_definitions if cat.name == "income")
        assert category.include_total == False
        assert category.total_label is None
        assert category.total_name is None
        
        # Verify total is removed from defined names
        updated_names = [name['name'] for name in sample_model_with_categories.defined_names]
        assert "total_income" not in updated_names

    def test_update_category_enable_total(self, sample_model_with_categories):
        """Test enabling total for a category that didn't have it."""
        # Initially unused category has no total
        initial_names = [name['name'] for name in sample_model_with_categories.defined_names]
        assert "total_unused" not in initial_names
        
        # Update to include total
        sample_model_with_categories.update.category(
            "unused",
            include_total=True
        )
        
        # Verify the include_total was updated
        category = next(cat for cat in sample_model_with_categories._category_definitions if cat.name == "unused")
        assert category.include_total == True
        assert category.total_label == "Total Unused Category"
        assert category.total_name == "total_unused"
        
        # Since no line items use this category, total still won't appear in defined names
        updated_names = [name['name'] for name in sample_model_with_categories.defined_names]
        assert "total_unused" not in updated_names

    def test_update_category_name(self, sample_model_with_categories: Model):
        """Test updating category name."""
        # Verify line item initially uses "expenses" category
        salary_item = sample_model_with_categories.get_line_item_definition("salary")
        assert salary_item.category == "expenses"
        
        # Update category name
        sample_model_with_categories.update.category(
            "expenses",
            new_name="operating_costs"
        )
        
        # Verify the name was updated
        category_names = [cat.name for cat in sample_model_with_categories._category_definitions]
        assert "operating_costs" in category_names
        assert "expenses" not in category_names
        
        # Verify line item category was updated automatically
        salary_item = sample_model_with_categories.get_line_item_definition("salary")
        assert salary_item.category == "operating_costs"
        
        # Verify defined names were updated
        updated_names = [name['name'] for name in sample_model_with_categories.defined_names]
        assert "total_operating_costs" in updated_names
        assert "total_expenses" not in updated_names

    def test_update_category_multiple_attributes(self, sample_model_with_categories: Model):
        """Test updating multiple category attributes at once."""
        # Update multiple attributes
        sample_model_with_categories.update.category(
            "income",
            label="Revenue Streams",
            total_label="Total Revenue",
            include_total=True
        )
        
        # Verify all attributes were updated
        category = next(cat for cat in sample_model_with_categories._category_definitions if cat.name == "income")
        assert category.label == "Revenue Streams"
        assert category.total_label == "Total Revenue"
        assert category.include_total == True
        
        # Verify defined names reflect the changes
        total_def = next(name for name in sample_model_with_categories.defined_names if name['name'] == 'total_income')
        assert total_def['label'] == "Total Revenue"

    def test_update_category_with_instance(self, sample_model_with_categories: Model):
        """Test updating a category by providing a new Category instance."""
        # Create a new Category instance
        new_category = Category(
            name="income",  # Same name
            label="Replacement Income Category",
            total_label="Replacement Total",
            include_total=True
        )
        
        # Update with the instance
        sample_model_with_categories.update.category(
            "income",
            category=new_category
        )
        
        # Verify the category was replaced
        category = next(cat for cat in sample_model_with_categories._category_definitions if cat.name == "income")
        assert category is new_category  # Should be the same instance
        assert category.label == "Replacement Income Category"
        assert category.total_label == "Replacement Total"

    def test_update_category_not_found(self, sample_model_with_categories):
        """Test that updating a non-existent category raises KeyError."""
        with pytest.raises(KeyError) as excinfo:
            sample_model_with_categories.update.category(
                "nonexistent_category",
                label="New Label"
            )
        
        assert "Category 'nonexistent_category' not found in model" in str(excinfo.value)

    def test_update_category_invalid_name(self, sample_model_with_categories: Model):
        """Test that updating with invalid name fails."""
        with pytest.raises(ValueError) as excinfo:
            sample_model_with_categories.update.category(
                "income",
                new_name="invalid name with spaces"
            )
        
        assert "Failed to update category 'income'" in str(excinfo.value)
        
        # Verify original category is unchanged
        category = next(cat for cat in sample_model_with_categories._category_definitions if cat.name == "income")
        assert category.name == "income"

    def test_update_category_duplicate_name(self, sample_model_with_categories: Model):
        """Test that updating to a duplicate name fails."""
        with pytest.raises(ValueError) as excinfo:
            sample_model_with_categories.update.category(
                "income",
                new_name="expenses"  # This name already exists
            )
        
        assert "Failed to update category 'income'" in str(excinfo.value)
        assert "Duplicate category names" in str(excinfo.value)
        
        # Verify original category is unchanged
        category = next(cat for cat in sample_model_with_categories._category_definitions if cat.name == "income")
        assert category.name == "income"

    def test_update_category_name_updates_all_line_items(self):
        """Test that updating category name updates all line items that use it."""
        revenue = LineItem(name="revenue", category="income", values={2023: 100})
        profit = LineItem(name="profit", category="income", values={2023: 50})
        salary = LineItem(name="salary", category="expenses", values={2023: 60})
        
        model = Model(
            line_items=[revenue, profit, salary],
            years=[2023],
            categories=[
                Category(name="income"),
                Category(name="expenses")
            ]
        )
        
        # Verify multiple line items use "income"
        income_items = [item for item in model._line_item_definitions if item.category == "income"]
        assert len(income_items) == 2
        
        # Update category name
        model.update.category("income", new_name="revenue_streams")
        
        # Verify all line items were updated
        for item in model._line_item_definitions:
            if item.name in ["revenue", "profit"]:
                assert item.category == "revenue_streams"
            else:
                assert item.category == "expenses"  # Should be unchanged

    def test_update_category_preserves_other_categories(self, sample_model_with_categories: Model):
        """Test that updating one category doesn't affect others."""
        # Get initial state of other categories
        expenses_category = next(cat for cat in sample_model_with_categories._category_definitions if cat.name == "expenses")
        initial_expenses_label = expenses_category.label
        
        # Update income category
        sample_model_with_categories.update.category(
            "income",
            label="Updated Income Label"
        )
        
        # Verify income category changed
        income_category = next(cat for cat in sample_model_with_categories._category_definitions if cat.name == "income")
        assert income_category.label == "Updated Income Label"
        
        # Verify expenses category is unchanged
        expenses_category = next(cat for cat in sample_model_with_categories._category_definitions if cat.name == "expenses")
        assert expenses_category.label == initial_expenses_label

    def test_update_category_returns_none(self, sample_model_with_categories: Model):
        """Test that the method returns None (emphasizing side effect over return value)."""
        result = sample_model_with_categories.update.category(
            "income",
            label="New Label"
        )
        
        # Verify method returns None
        assert result is None
        
        # Verify the category was still updated
        category = next(cat for cat in sample_model_with_categories._category_definitions if cat.name == "income")
        assert category.label == "New Label"

    def test_model_copy_validation_preserves_original(self, sample_model_with_categories: Model):
        """Test that validation failures don't affect the original model."""
        original_income_label = next(cat for cat in sample_model_with_categories._category_definitions if cat.name == "income").label
        
        # Try multiple failed updates
        with pytest.raises(ValueError):
            sample_model_with_categories.update.category("income", new_name="expenses")  # Duplicate
        
        with pytest.raises(ValueError):
            sample_model_with_categories.update.category("income", new_name="invalid name")  # Invalid
        
        # Verify model is completely unchanged
        category = next(cat for cat in sample_model_with_categories._category_definitions if cat.name == "income")
        assert category.label == original_income_label

    def test_update_category_total_behavior_changes(self, sample_model_with_categories):
        """Test changing total behavior and its effect on model calculations."""
        # Initially income has total
        assert sample_model_with_categories["total_income", 2023] == 100000
        
        # Disable total
        sample_model_with_categories.update.category("income", include_total=False)
        
        # Should no longer be able to access total
        with pytest.raises(KeyError):
            sample_model_with_categories["total_income", 2023]
        
        # Re-enable total
        sample_model_with_categories.update.category("income", include_total=True)
        
        # Should be able to access total again
        assert sample_model_with_categories["total_income", 2023] == 100000

    def test_update_category_complex_scenario(self, sample_model_with_categories: Model):
        """Test a complex update scenario with name change and line item cascade."""
        # Initial state verification
        assert sample_model_with_categories.get_line_item_definition("salary").category == "expenses"
        assert sample_model_with_categories["total_expenses", 2023] == 60000
        
        # Complex update: rename and change labels
        sample_model_with_categories.update.category(
            "expenses",
            new_name="operational_costs",
            label="Operational Costs",
            total_label="Total Operational Costs"
        )
        
        # Verify all changes
        # 1. Category was renamed
        category_names = [cat.name for cat in sample_model_with_categories._category_definitions]
        assert "operational_costs" in category_names
        assert "expenses" not in category_names
        
        # 2. Line item category was updated
        assert sample_model_with_categories.get_line_item_definition("salary").category == "operational_costs"
        
        # 3. Total calculation works with new name
        assert sample_model_with_categories["total_operational_costs", 2023] == 60000
        
        # 4. Old total name no longer works
        with pytest.raises(KeyError):
            sample_model_with_categories["total_expenses", 2023]




class TestUpdateLineItem:
    
    @pytest.fixture
    def sample_model(self):
        """Create a sample model for testing."""
        revenue = LineItem(
            name="revenue",
            category="income",
            label="Total Revenue",
            values={2023: 100000, 2024: 120000, 2025: 140000},
            value_format="currency"
        )
        
        costs = LineItem(
            name="costs",
            category="expenses", 
            label="Operating Costs",
            values={2023: 60000, 2024: 70000, 2025: 80000},
            formula=None,
            value_format="currency"
        )

        marketing = LineItem(
            name="marketing",
            category="expenses",
            label="Marketing Expenses",
            values={2023: 10000, 2024: 12000, 2025: 14000},
            value_format="currency"
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

    def test_update_line_item_values(self, sample_model: Model):
        """Test updating line item values."""
        original_values = sample_model["revenue", 2023]
        
        # Update values
        sample_model.update.line_item(
            "revenue",
            values={2023: 150000, 2024: 180000, 2025: 210000}
        )
        
        # Verify the values were updated
        assert sample_model["revenue", 2023] == 150000
        assert sample_model["revenue", 2024] == 180000
        assert sample_model["revenue", 2025] == 210000
        
        # Verify other attributes unchanged
        revenue_item = sample_model.get_line_item_definition("revenue")
        assert revenue_item.label == "Total Revenue"
        assert revenue_item.category == "income"
        assert revenue_item.value_format == "currency"

    def test_update_line_item_label(self, sample_model: Model):
        """Test updating line item label."""
        # Update label
        sample_model.update.line_item("revenue", label="Updated Revenue Label")
        
        # Verify the label was updated
        revenue_item = sample_model.get_line_item_definition("revenue")
        assert revenue_item.label == "Updated Revenue Label"
        
        # Verify other attributes unchanged
        assert revenue_item.name == "revenue"
        assert revenue_item.category == "income"
        assert revenue_item.values == {2023: 100000, 2024: 120000, 2025: 140000}
        assert revenue_item.value_format == "currency"

    def test_update_line_item_category(self, sample_model: Model):
        """Test updating line item category."""
        # Update category
        sample_model.update.line_item("marketing", category="income")
        
        # Verify the category was updated
        marketing_item = sample_model.get_line_item_definition("marketing")
        assert marketing_item.category == "income"
        
        # Verify other attributes unchanged
        assert marketing_item.name == "marketing"
        assert marketing_item.label == "Marketing Expenses"
        assert marketing_item.values == {2023: 10000, 2024: 12000, 2025: 14000}

    def test_update_line_item_formula(self, sample_model: Model):
        """Test updating line item formula."""
        # Update formula
        sample_model.update.line_item("costs", formula="revenue * 0.5")
        
        # Verify the formula was updated
        costs_item = sample_model.get_line_item_definition("costs")
        assert costs_item.formula == "revenue * 0.5"
        
        # Since the original values are preserved, they take precedence over the formula
        # The formula will only be used for years not in the values dict
        assert sample_model["costs", 2023] == 60000  # Original value from values dict
        assert sample_model["costs", 2024] == 70000  # Original value from values dict
        assert sample_model["costs", 2025] == 80000  # Original value from values dict
        
        # Verify the original values are still there
        assert costs_item.values == {2023: 60000, 2024: 70000, 2025: 80000}

    def test_update_line_item_formula_with_cleared_values(self, sample_model: Model):
        """Test updating line item formula with values cleared to see formula in action."""
        # Update formula and clear values so formula takes effect
        sample_model.update.line_item("costs", formula="revenue * 0.5", values={})
        
        # Verify the formula was updated and values were cleared
        costs_item = sample_model.get_line_item_definition("costs")
        assert costs_item.formula == "revenue * 0.5"
        assert costs_item.values == {}
        
        # Now the formula calculations work since no explicit values override them
        assert sample_model["costs", 2023] == 50000  # 100000 * 0.5
        assert sample_model["costs", 2024] == 60000  # 120000 * 0.5
        assert sample_model["costs", 2025] == 70000  # 140000 * 0.5

    def test_update_line_item_value_format(self, sample_model: Model):
        """Test updating line item value format."""
        # Update value format
        sample_model.update.line_item("revenue", value_format="no_decimals")
        
        # Verify the value format was updated
        revenue_item = sample_model.get_line_item_definition("revenue")
        assert revenue_item.value_format == "no_decimals"
        
        # Verify other attributes unchanged
        assert revenue_item.name == "revenue"
        assert revenue_item.values == {2023: 100000, 2024: 120000, 2025: 140000}

    def test_update_line_item_new_name(self, sample_model: Model):
        """Test renaming a line item."""
        # Update name
        sample_model.update.line_item("revenue", new_name="total_revenue")
        
        # Verify the old name is gone
        with pytest.raises(KeyError):
            sample_model.get_line_item_definition("revenue")
        
        # Verify the new name exists
        renamed_item = sample_model.get_line_item_definition("total_revenue")
        assert renamed_item.name == "total_revenue"
        assert renamed_item.label == "Total Revenue"
        assert renamed_item.category == "income"
        assert renamed_item.values == {2023: 100000, 2024: 120000, 2025: 140000}
        
        # Verify it's accessible by the new name
        assert sample_model["total_revenue", 2023] == 100000

    def test_update_line_item_multiple_attributes(self, sample_model: Model):
        """Test updating multiple attributes at once."""
        # Update multiple attributes
        sample_model.update.line_item(
            "marketing",
            label="Updated Marketing",
            values={2023: 15000, 2024: 18000, 2025: 21000},
            value_format="no_decimals",
            category="income"
        )
        
        # Verify all attributes were updated
        marketing_item = sample_model.get_line_item_definition("marketing")
        assert marketing_item.label == "Updated Marketing"
        assert marketing_item.values == {2023: 15000, 2024: 18000, 2025: 21000}
        assert marketing_item.value_format == "no_decimals"
        assert marketing_item.category == "income"
        
        # Verify name unchanged
        assert marketing_item.name == "marketing"

    def test_update_line_item_with_instance(self, sample_model: Model):
        """Test updating with a LineItem instance."""
        # Create a new LineItem instance
        new_revenue = LineItem(
            name="new_revenue",
            category="income",
            label="Completely New Revenue",
            values={2023: 200000, 2024: 240000, 2025: 280000},
            formula=None,
            value_format="two_decimals"
        )
        
        # Update with the instance
        sample_model.update.line_item("revenue", line_item=new_revenue)
        
        # Verify the line item was completely replaced
        updated_item = sample_model.get_line_item_definition("new_revenue")
        assert updated_item.name == "new_revenue"
        assert updated_item.label == "Completely New Revenue"
        assert updated_item.category == "income"
        assert updated_item.values == {2023: 200000, 2024: 240000, 2025: 280000}
        assert updated_item.value_format == "two_decimals"
        
        # Verify old name is gone
        with pytest.raises(KeyError):
            sample_model.get_line_item_definition("revenue")
        
        # Verify accessible by new name
        assert sample_model["new_revenue", 2023] == 200000

    def test_update_line_item_nonexistent_fails(self, sample_model: Model):
        """Test that updating a non-existent line item fails."""
        with pytest.raises(KeyError) as excinfo:
            sample_model.update.line_item("nonexistent_item", label="New Label")
        
        assert "Line item 'nonexistent_item' not found in model" in str(excinfo.value)
        
        # Verify original model is unchanged
        assert len(sample_model._line_item_definitions) == 3

    def test_update_line_item_invalid_category_fails(self, sample_model: Model):
        """Test that updating to an invalid category fails."""
        with pytest.raises(ValueError) as excinfo:
            sample_model.update.line_item("revenue", category="nonexistent_category")
        
        assert "Failed to update line item 'revenue'" in str(excinfo.value)
        assert "not defined category" in str(excinfo.value)
        
        # Verify original item is unchanged
        revenue_item = sample_model.get_line_item_definition("revenue")
        assert revenue_item.category == "income"

    def test_update_line_item_invalid_formula_fails(self, sample_model: Model):
        """Test that updating to an invalid formula fails."""
        with pytest.raises(ValueError) as excinfo:
            # Clear values to force formula evaluation during validation
            sample_model.update.line_item("costs", formula="nonexistent_variable * 2", values={})
        
        assert "Failed to update line item 'costs'" in str(excinfo.value)
        assert "not found" in str(excinfo.value)
        
        # Verify original item is unchanged
        costs_item = sample_model.get_line_item_definition("costs")
        assert costs_item.formula is None

    def test_update_line_item_invalid_name_fails(self, sample_model: Model):
        """Test that updating to an invalid name fails."""
        with pytest.raises(ValueError) as excinfo:
            sample_model.update.line_item("revenue", new_name="invalid name with spaces")
        
        assert "Failed to update line item 'revenue'" in str(excinfo.value)
        
        # Verify original item is unchanged
        revenue_item = sample_model.get_line_item_definition("revenue")
        assert revenue_item.name == "revenue"

    def test_update_line_item_duplicate_name_fails(self, sample_model: Model):
        """Test that updating to a duplicate name fails."""
        with pytest.raises(ValueError) as excinfo:
            sample_model.update.line_item("revenue", new_name="costs")
        
        assert "Failed to update line item 'revenue'" in str(excinfo.value)
        assert "Duplicate defined names" in str(excinfo.value)
        
        # Verify original item is unchanged
        revenue_item = sample_model.get_line_item_definition("revenue")
        assert revenue_item.name == "revenue"

    def test_update_line_item_returns_none(self, sample_model: Model):
        """Test that the method returns None (emphasizing side effect over return value)."""
        result = sample_model.update.line_item("revenue", label="New Label")
        
        # Verify method returns None
        assert result is None
        
        # Verify the line item was still updated
        revenue_item = sample_model.get_line_item_definition("revenue")
        assert revenue_item.label == "New Label"

    def test_update_line_item_preserves_other_items(self, sample_model: Model):
        """Test that updating one item doesn't affect others."""
        # Record initial values of other items
        initial_costs = sample_model["costs", 2023]
        initial_marketing = sample_model["marketing", 2023]
        
        # Update revenue
        sample_model.update.line_item("revenue", label="Updated Revenue")
        
        # Verify other items are unchanged
        assert sample_model["costs", 2023] == initial_costs
        assert sample_model["marketing", 2023] == initial_marketing
        
        # Verify their attributes are unchanged
        costs_item = sample_model.get_line_item_definition("costs")
        assert costs_item.label == "Operating Costs"
        marketing_item = sample_model.get_line_item_definition("marketing")
        assert marketing_item.label == "Marketing Expenses"

    def test_update_line_item_updates_defined_names(self, sample_model: Model):
        """Test that updating a line item properly updates the model's defined names."""
        initial_names = [name['name'] for name in sample_model.defined_names]
        assert "revenue" in initial_names
        
        # Rename the item
        sample_model.update.line_item("revenue", new_name="total_revenue")
        
        updated_names = [name['name'] for name in sample_model.defined_names]
        assert "revenue" not in updated_names
        assert "total_revenue" in updated_names
        assert len(updated_names) == len(initial_names)

    def test_update_line_item_model_validation(self, sample_model: Model):
        """Test that model validation still works after update."""
        # Update a line item
        sample_model.update.line_item("revenue", values={2023: 150000, 2024: 180000, 2025: 210000})
        
        # Add a new line item to ensure model is still functional
        sample_model.add.line_item(
            name="profit",
            category="income",
            formula="revenue - costs"
        )
        
        # Verify the new item works with updated values
        assert sample_model["profit", 2023] == 90000  # 150000 - 60000
        assert len(sample_model._line_item_definitions) == 4

    def test_update_line_item_edge_case_single_item(self):
        """Test updating the only line item in a model."""
        single_item_model = Model(
            line_items=[LineItem(name="only_item", category="test", values={2023: 100}, label="Original")],
            years=[2023]
        )
        
        # Update the only item
        single_item_model.update.line_item("only_item", label="Updated")
        
        # Verify the model still works
        assert len(single_item_model._line_item_definitions) == 1
        updated_item = single_item_model.get_line_item_definition("only_item")
        assert updated_item.label == "Updated"
        assert single_item_model["only_item", 2023] == 100

    def test_update_multiple_line_items(self, sample_model: Model):
        """Test updating multiple line items in sequence."""
        # Update first item
        sample_model.update.line_item("revenue", label="Updated Revenue")
        updated_revenue = sample_model.get_line_item_definition("revenue")
        assert updated_revenue.label == "Updated Revenue"
        
        # Update second item
        sample_model.update.line_item("costs", label="Updated Costs")
        updated_costs = sample_model.get_line_item_definition("costs")
        assert updated_costs.label == "Updated Costs"
        
        # Verify both updates persisted
        assert sample_model.get_line_item_definition("revenue").label == "Updated Revenue"
        assert sample_model.get_line_item_definition("costs").label == "Updated Costs"
        
        # Verify all items still accessible
        assert len(sample_model._line_item_definitions) == 3
        assert sample_model["revenue", 2023] == 100000
        assert sample_model["costs", 2023] == 60000


class TestUpdateGenerator:
    
    @pytest.fixture
    def sample_generator(self):
        """Create a sample generator for testing."""
        from pyproforma.generators.debt import Debt
        return Debt(
            name="test_debt",
            par_amounts={2023: 100000, 2024: 50000},
            interest_rate=0.05,
            term=5
        )
    
    @pytest.fixture
    def sample_model_with_generator(self, sample_generator):
        """Create a sample model with a generator for testing."""
        revenue = LineItem(
            name="revenue",
            category="income",
            values={2023: 100000, 2024: 120000, 2025: 140000}
        )
        
        categories = [
            Category(name="income", label="Income", include_total=True)
        ]
        
        return Model(
            line_items=[revenue],
            years=[2023, 2024, 2025],
            categories=categories,
            generators=[sample_generator]
        )

    def test_update_generator_replacement(self, sample_model_with_generator):
        """Test replacing a generator with a new instance."""
        from pyproforma.generators.debt import Debt
        
        # Create a new debt generator with different parameters
        new_debt = Debt(
            name="test_debt",
            par_amounts={2023: 200000, 2024: 100000},  # Different amounts
            interest_rate=0.06,  # Different rate
            term=10  # Different term
        )
        
        # Get original values for comparison
        original_principal_2023 = sample_model_with_generator["test_debt.principal", 2023]
        
        # Update generator
        sample_model_with_generator.update.generator("test_debt", generator=new_debt)
        
        # Verify the generator was replaced
        updated_generator = next(gen for gen in sample_model_with_generator.generators if gen.name == "test_debt")
        assert updated_generator is new_debt
        
        # Verify values changed (should be different due to different parameters)
        new_principal_2023 = sample_model_with_generator["test_debt.principal", 2023]
        assert new_principal_2023 != original_principal_2023

    def test_update_generator_not_found(self, sample_model_with_generator):
        """Test error when trying to update non-existent generator."""
        from pyproforma.generators.debt import Debt
        
        new_debt = Debt(
            name="new_debt",
            par_amounts={2023: 100000},
            interest_rate=0.05,
            term=5
        )
        
        with pytest.raises(KeyError, match="Generator 'nonexistent' not found in model"):
            sample_model_with_generator.update.generator("nonexistent", generator=new_debt)

    def test_update_generator_invalid_type(self, sample_model_with_generator):
        """Test error when trying to update with non-Generator instance."""
        with pytest.raises(TypeError, match="Expected Generator instance, got str"):
            sample_model_with_generator.update.generator("test_debt", generator="not_a_generator")

    def test_update_generator_validation_failure(self, sample_model_with_generator):
        """Test that validation failures are properly handled."""
        from pyproforma.generators.generator_class import Generator
        
        # Create a mock generator that will cause validation issues
        class BadGenerator(Generator):
            def __init__(self):
                self.name = "test_debt"
            
            @property 
            def defined_names(self):
                return ["invalid.name.with.duplicate", "invalid.name.with.duplicate"]  # Duplicate names
            
            def get_values(self, year):
                return {"invalid.name.with.duplicate": 100}
                
            @classmethod
            def from_config(cls, config):
                """Required abstract method implementation."""
                return cls()
                
            def to_dict(self):
                """Required abstract method implementation."""
                return {"type": "bad", "name": self.name}
        
        bad_generator = BadGenerator()
        
        with pytest.raises(ValueError, match="Failed to update generator 'test_debt'"):
            sample_model_with_generator.update.generator("test_debt", generator=bad_generator)
