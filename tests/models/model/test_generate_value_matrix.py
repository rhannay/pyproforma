import pytest
from pyproforma import LineItem, Model, Category
from pyproforma.models.line_item_generator.debt import Debt
from pyproforma.models.model.value_matrix import generate_value_matrix


class TestGenerateValueMatrix:
    """Test cases for the generate_value_matrix() function."""
    
    @pytest.fixture
    def basic_categories(self):
        """Create basic categories for testing."""
        return [
            Category(name="revenue", label="Revenue"),
            Category(name="expenses", label="Expenses"),
            Category(name="net_income", label="Net Income")
        ]
    
    def test_order_of_line_items_does_not_matter(self, basic_categories):
        """Test that the order of line items in the list does not affect the calculation results."""
        # Create line items with dependencies - net_income depends on revenue and expenses
        revenue = LineItem(name="revenue", category="revenue", values={2023: 1000, 2024: 1200})
        expenses = LineItem(name="expenses", category="expenses", values={2023: 600, 2024: 700})
        net_income = LineItem(name="net_income", category="net_income", formula="revenue - expenses")
        
        # Create models with different orders of the same line items
        model1 = Model(
            line_items=[revenue, expenses, net_income],  # Dependencies first
            years=[2023, 2024],
            categories=basic_categories
        )
        
        model2 = Model(
            line_items=[net_income, revenue, expenses],  # Dependent item first
            years=[2023, 2024], 
            categories=basic_categories
        )
        
        model3 = Model(
            line_items=[expenses, net_income, revenue],  # Mixed order
            years=[2023, 2024],
            categories=basic_categories
        )
        
        # All models should produce the same value matrix
        matrix1 = generate_value_matrix(
            model1.years, model1._line_item_definitions, model1.line_item_generators,
            model1._category_definitions, model1.line_item_metadata
        )
        matrix2 = generate_value_matrix(
            model2.years, model2._line_item_definitions, model2.line_item_generators,
            model2._category_definitions, model2.line_item_metadata
        )
        matrix3 = generate_value_matrix(
            model3.years, model3._line_item_definitions, model3.line_item_generators,
            model3._category_definitions, model3.line_item_metadata
        )
        
        # Verify all matrices are identical
        for year in [2023, 2024]:
            assert matrix1[year] == matrix2[year] == matrix3[year]
            # Verify specific calculations are correct
            assert matrix1[year]["revenue"] == revenue.values[year]
            assert matrix1[year]["expenses"] == expenses.values[year]
            assert matrix1[year]["net_income"] == revenue.values[year] - expenses.values[year]
    
    def test_order_with_complex_dependencies(self, basic_categories):
        """Test order independence with more complex dependency chains."""
        # Create a chain: base -> intermediate -> final
        base = LineItem(name="base", category="revenue", values={2023: 100})
        intermediate = LineItem(name="intermediate", category="revenue", formula="base * 2")
        final = LineItem(name="final", category="revenue", formula="intermediate + base")
        
        # Try different orders
        model1 = Model(
            line_items=[base, intermediate, final],
            years=[2023],
            categories=basic_categories
        )
        
        model2 = Model(
            line_items=[final, intermediate, base], 
            years=[2023],
            categories=basic_categories
        )
        
        matrix1 = generate_value_matrix(
            model1.years, model1._line_item_definitions, model1.line_item_generators,
            model1._category_definitions, model1.line_item_metadata
        )
        matrix2 = generate_value_matrix(
            model2.years, model2._line_item_definitions, model2.line_item_generators,
            model2._category_definitions, model2.line_item_metadata
        )
        
        assert matrix1[2023] == matrix2[2023]
        assert matrix1[2023]["base"] == 100
        assert matrix1[2023]["intermediate"] == 200
        assert matrix1[2023]["final"] == 300
    
    def test_formula_with_invalid_variable_raises_useful_exception(self, basic_categories):
        """Test that a formula with an unknown variable raises a clear exception."""
        revenue = LineItem(name="revenue", category="revenue", values={2023: 1000})
        # Formula references 'unknown_variable' which doesn't exist
        invalid_item = LineItem(
            name="invalid_calculation", 
            category="expenses", 
            formula="revenue - unknown_variable"
        )
        
        # Create model without triggering _generate_value_matrix in constructor
        model = Model.__new__(Model)
        model._line_item_definitions = [revenue, invalid_item]
        model.years = [2023]
        model._category_definitions = basic_categories
        model.line_item_generators = []
        model.line_item_metadata = model._gather_line_item_metadata()
        
        with pytest.raises(ValueError) as exc_info:
            generate_value_matrix(
                model.years, model._line_item_definitions, model.line_item_generators,
                model._category_definitions, model.line_item_metadata
            )
        
        # Verify the exception message is useful - should detect invalid variable
        error_msg = str(exc_info.value)
        assert "'unknown_variable' not found" in error_msg
    
    def test_formula_with_invalid_variable_in_formula_calculation(self, basic_categories):
        """Test that the underlying formula calculation raises a clear error for unknown variables."""
        from pyproforma.models.formula import calculate_formula
        
        # Test the formula calculation directly to ensure it gives useful errors
        value_matrix = {2023: {"revenue": 1000}}
        
        with pytest.raises(ValueError) as exc_info:
            calculate_formula("revenue - unknown_variable", value_matrix, 2023)
        
        error_msg = str(exc_info.value)
        assert "'unknown_variable' not found" in error_msg
    
    def test_circular_reference_simple(self, basic_categories):
        """Test detection of simple circular references."""
        # Create circular dependency: a depends on b, b depends on a
        item_a = LineItem(name="item_a", category="revenue", formula="item_b + 10")
        item_b = LineItem(name="item_b", category="revenue", formula="item_a - 5")
        
        # Create model without triggering _generate_value_matrix in constructor
        model = Model.__new__(Model)
        model._line_item_definitions = [item_a, item_b]
        model.years = [2023]
        model._category_definitions = basic_categories
        model.line_item_generators = []        
        model.line_item_metadata = model._gather_line_item_metadata()
        
        with pytest.raises(ValueError) as exc_info:
            generate_value_matrix(
                model.years, model._line_item_definitions, model.line_item_generators,
                model._category_definitions, model.line_item_metadata
            )
        
        error_msg = str(exc_info.value)
        assert "Could not calculate line items due to missing dependencies or circular references" in error_msg
        # Both items should be mentioned as they're both unresolvable
        assert "item_a" in error_msg
        assert "item_b" in error_msg
    
    def test_circular_reference_complex(self, basic_categories):
        """Test detection of complex circular references involving multiple items."""
        # Create circular dependency chain: a -> b -> c -> a
        item_a = LineItem(name="item_a", category="revenue", formula="item_c + 10")
        item_b = LineItem(name="item_b", category="revenue", formula="item_a * 2")
        item_c = LineItem(name="item_c", category="revenue", formula="item_b - 5")
        # Add a non-circular item to ensure it still gets calculated
        item_d = LineItem(name="item_d", category="revenue", values={2023: 100})
        
        # Create model without triggering _generate_value_matrix in constructor
        model = Model.__new__(Model)
        model._line_item_definitions = [item_a, item_b, item_c, item_d]
        model.years = [2023]
        model._category_definitions = basic_categories
        model.line_item_generators = []

        model.line_item_metadata = model._gather_line_item_metadata()
        
        with pytest.raises(ValueError) as exc_info:
            generate_value_matrix(
                model.years, model._line_item_definitions, model.line_item_generators,
                model._category_definitions, model.line_item_metadata
            )
        
        error_msg = str(exc_info.value)
        assert "Could not calculate line items due to missing dependencies or circular references" in error_msg
        # All three circular items should be mentioned
        assert "item_a" in error_msg
        assert "item_b" in error_msg  
        assert "item_c" in error_msg
        # item_d should not be mentioned since it's not part of the circular reference
        assert "item_d" not in error_msg
    
    def test_self_reference_circular(self, basic_categories):
        """Test detection of self-referencing formulas."""
        # Item that references itself
        self_ref = LineItem(name="self_ref", category="revenue", formula="self_ref + 1")
        
        # Create model without triggering _generate_value_matrix in constructor
        model = Model.__new__(Model)
        model._line_item_definitions = [self_ref]
        model.years = [2023]
        model._category_definitions = basic_categories
        model.line_item_generators = []
        model.line_item_metadata = model._gather_line_item_metadata()
        
        with pytest.raises(ValueError) as exc_info:
            generate_value_matrix(
                model.years, model._line_item_definitions, model.line_item_generators,
                model._category_definitions, model.line_item_metadata
            )
        
        error_msg = str(exc_info.value)
        assert "Could not calculate line items due to missing dependencies or circular references" in error_msg
        assert "self_ref" in error_msg
    
    def test_partial_circular_reference(self, basic_categories):
        """Test that items not involved in circular references still get calculated."""
        # Create items where some are circular but others are not
        good_item1 = LineItem(name="good1", category="revenue", values={2023: 100})
        good_item2 = LineItem(name="good2", category="revenue", formula="good1 * 2")
        
        # Circular items
        bad_item1 = LineItem(name="bad1", category="expenses", formula="bad2 + 10")
        bad_item2 = LineItem(name="bad2", category="expenses", formula="bad1 - 5")
        
        # Create model without triggering _generate_value_matrix in constructor
        model = Model.__new__(Model)
        model._line_item_definitions = [good_item1, good_item2, bad_item1, bad_item2]
        model.years = [2023]
        model._category_definitions = basic_categories
        model.line_item_generators = []
        model.line_item_metadata = model._gather_line_item_metadata()
        
        with pytest.raises(ValueError) as exc_info:
            generate_value_matrix(
                model.years, model._line_item_definitions, model.line_item_generators,
                model._category_definitions, model.line_item_metadata
            )
        
        error_msg = str(exc_info.value)
        # Only the circular items should be mentioned
        assert "bad1" in error_msg
        assert "bad2" in error_msg
        assert "good1" not in error_msg
        assert "good2" not in error_msg
    
    def test_generate_value_matrix_with_line_item_generators(self, basic_categories):
        """Test that line item generators are included in the value matrix and order doesn't matter."""
        # Create a debt line item generator
        debt_generator = Debt(
            name="loan",
            par_amount={2023: 100000},
            interest_rate=0.05,
            term=5
        )
        
        # Create line items that depend on line item generator values
        revenue = LineItem(name="revenue", category="revenue", values={2023: 150000})
        # Use the first defined name from the line item generator
        debt_names = debt_generator.defined_names
        debt_payment_var = debt_names[0]  # Usually something like "loan.principal"
        
        net_income = LineItem(
            name="net_income", 
            category="net_income", 
            formula=f"revenue - {debt_payment_var}"
        )
        
        # Test different orders
        model1 = Model(
            line_items=[revenue, net_income],
            years=[2023],
            categories=basic_categories,
            line_item_generators=[debt_generator]
        )
        
        model2 = Model(
            line_items=[net_income, revenue],  # Different order
            years=[2023],
            categories=basic_categories,
            line_item_generators=[debt_generator]
        )
        
        matrix1 = generate_value_matrix(
            model1.years, model1._line_item_definitions, model1.line_item_generators,
            model1._category_definitions, model1.line_item_metadata
        )
        matrix2 = generate_value_matrix(
            model2.years, model2._line_item_definitions, model2.line_item_generators,
            model2._category_definitions, model2.line_item_metadata
        )
        
        # Both should produce the same result
        assert matrix1[2023] == matrix2[2023]
        
        # Verify line item generator values are included
        for debt_name in debt_names:
            assert debt_name in matrix1[2023]
            assert isinstance(matrix1[2023][debt_name], (int, float))
        
        # Verify line items calculated correctly
        assert matrix1[2023]["revenue"] == 150000
        assert matrix1[2023]["net_income"] == 150000 - matrix1[2023][debt_payment_var]
    
    def test_generate_value_matrix_with_assumptions(self, basic_categories):
        """Test that assumptions (now as line items) are included in the value matrix."""
        # Create assumptions as line items
        growth_rate = LineItem(name="growth_rate", category="assumptions", values={2023: 0.05, 2024: 0.07})
        base_value = LineItem(name="base_value", category="assumptions", values={2023: 1000, 2024: 1200})
        
        # Create line items that use assumptions
        calculated_revenue = LineItem(
            name="calculated_revenue",
            category="revenue", 
            formula="base_value * (1 + growth_rate)"
        )
        
        # Add assumptions category
        assumption_category = Category(name="assumptions", label="Assumptions")
        all_categories = basic_categories + [assumption_category]
        
        model = Model(
            line_items=[calculated_revenue, growth_rate, base_value],
            years=[2023, 2024],
            categories=all_categories
        )
        
        matrix = generate_value_matrix(
            model.years, model._line_item_definitions, model.line_item_generators,
            model._category_definitions, model.line_item_metadata
        )
        
        # Verify assumptions are in the matrix
        for year in [2023, 2024]:
            assert "growth_rate" in matrix[year]
            assert "base_value" in matrix[year]
            assert matrix[year]["growth_rate"] == growth_rate.values[year]
            assert matrix[year]["base_value"] == base_value.values[year]
            
            # Verify calculation using assumptions
            expected_revenue = base_value.values[year] * (1 + growth_rate.values[year])
            assert matrix[year]["calculated_revenue"] == expected_revenue
    
    def test_missing_dependency_clear_error(self, basic_categories):
        """Test that missing dependencies produce clear error messages."""
        # Create item that depends on non-existent variable
        revenue = LineItem(name="revenue", category="revenue", values={2023: 1000})
        dependent = LineItem(
            name="dependent_item",
            category="expenses", 
            formula="revenue + nonexistent_variable"
        )
        
        # Create model without triggering _generate_value_matrix in constructor
        model = Model.__new__(Model)
        model._line_item_definitions = [revenue, dependent]
        model.years = [2023]
        model._category_definitions = basic_categories
        model.assumptions = []
        model.line_item_generators = []
        model.line_item_metadata = model._gather_line_item_metadata()
        
        with pytest.raises(ValueError) as exc_info:
            generate_value_matrix(
                model.years, model._line_item_definitions, model.line_item_generators,
                model._category_definitions, model.line_item_metadata
            )
        
        error_msg = str(exc_info.value)
        assert "'nonexistent_variable' not found" in error_msg

    def test_formula_referencing_own_category_total_raises_error(self, basic_categories):
        """Test that a formula referencing its own category total raises a clear error."""
        # Suppose the convention is that category totals are referenced as e.g. 'revenue_total'
        revenue = LineItem(name="revenue", category="revenue", values={2023: 1000})
        # This line item tries to reference its own category total, which should not be allowed
        bad_item = LineItem(
            name="bad_item",
            category="revenue",
            formula="revenue_total + 100"
        )

        # Create model without triggering _generate_value_matrix in constructor
        model = Model.__new__(Model)
        model._line_item_definitions = [revenue, bad_item]
        model.years = [2023]
        model._category_definitions = basic_categories
        model.assumptions = []
        model.line_item_generators = []
        model.line_item_metadata = model._gather_line_item_metadata()

        with pytest.raises(ValueError) as exc_info:
            generate_value_matrix(
                model.years, model._line_item_definitions, model.line_item_generators,
                model._category_definitions, model.line_item_metadata
            )

        error_msg = str(exc_info.value)
        # The error should mention that referencing own category total is not allowed or not found
        assert "revenue_total" in error_msg
        assert "not found" in error_msg or "not allowed" in error_msg

    def test_order_with_category_total_dependencies(self, basic_categories):
        """Test that order of line items does not affect calculation when using category totals."""
        # Add two revenue and two expense line items
        rev1 = LineItem(name="rev1", category="revenue", values={2023: 100, 2024: 200})
        rev2 = LineItem(name="rev2", category="revenue", values={2023: 300, 2024: 400})
        exp1 = LineItem(name="exp1", category="expenses", values={2023: 50, 2024: 60})
        exp2 = LineItem(name="exp2", category="expenses", values={2023: 70, 2024: 80})
        # net_revenues depends on category totals
        net_revenues = LineItem(
            name="net_revenues",
            category="net_income",
            formula="total_revenue - total_expenses"
        )

        # Intentionally shuffled order
        line_items = [net_revenues, exp1, rev1, exp2, rev2]

        model = Model(
            line_items=line_items,
            years=[2023, 2024],
            categories=basic_categories
        )

        matrix = generate_value_matrix(
            model.years, model._line_item_definitions, model.line_item_generators,
            model._category_definitions, model.line_item_metadata
        )

        for year in [2023, 2024]:
            expected_revenue_total = rev1.values[year] + rev2.values[year]
            expected_expenses_total = exp1.values[year] + exp2.values[year]
            assert matrix[year]["rev1"] == rev1.values[year]
            assert matrix[year]["rev2"] == rev2.values[year]
            assert matrix[year]["exp1"] == exp1.values[year]
            assert matrix[year]["exp2"] == exp2.values[year]
            assert matrix[year]["total_revenue"] == expected_revenue_total
            assert matrix[year]["total_expenses"] == expected_expenses_total
            assert matrix[year]["net_revenues"] == expected_revenue_total - expected_expenses_total
