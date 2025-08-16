import pytest
from pyproforma.models.formula import validate_formula


class TestValidateFormula:
    """Test cases for the validate_formula function."""

    def test_valid_simple_formula(self):
        """Test formula with valid variables passes validation."""
        formula = "revenue - expenses"
        name = "profit"
        valid_names = ["revenue", "expenses", "profit"]
        
        # Should not raise any exception
        validate_formula(formula, name, valid_names)

    def test_valid_complex_formula(self):
        """Test complex formula with multiple operations and valid variables."""
        formula = "revenue * (1 - tax_rate) - expenses + depreciation"
        name = "profit"
        valid_names = ["revenue", "tax_rate", "expenses", "depreciation", "profit"]
        
        # Should not raise any exception
        validate_formula(formula, name, valid_names)

    def test_valid_formula_with_time_offsets(self):
        """Test formula with time offset references."""
        formula = "revenue[-1] * growth_rate + expenses[-2]"
        name = "projected_revenue"
        valid_names = ["revenue", "growth_rate", "expenses", "projected_revenue"]
        
        # Should not raise any exception
        validate_formula(formula, name, valid_names)

    def test_valid_formula_with_mixed_references(self):
        """Test formula with both current year and time offset references."""
        formula = "revenue - expenses + revenue[-1] * 0.1"
        name = "adjusted_profit"
        valid_names = ["revenue", "expenses", "adjusted_profit"]
        
        # Should not raise any exception
        validate_formula(formula, name, valid_names)

    def test_invalid_line_item_name_not_in_valid_names(self):
        """Test that line item name must be in valid_names."""
        formula = "revenue - expenses"
        name = "missing_item"
        valid_names = ["revenue", "expenses", "profit"]
        
        with pytest.raises(ValueError, match="Line item name 'missing_item' is not found in valid names"):
            validate_formula(formula, name, valid_names)

    def test_circular_reference_without_offset(self):
        """Test that circular reference without time offset raises error."""
        formula = "profit + expenses"
        name = "profit"
        valid_names = ["profit", "expenses"]
        
        with pytest.raises(ValueError, match="Circular reference detected: formula for 'profit' references itself without a time offset"):
            validate_formula(formula, name, valid_names)

    def test_valid_self_reference_with_offset(self):
        """Test that self-reference with time offset is allowed."""
        formula = "profit[-1] * 1.1"
        name = "profit"
        valid_names = ["profit"]
        
        # Should not raise any exception
        validate_formula(formula, name, valid_names)

    def test_valid_self_reference_with_positive_offset(self):
        """Test that self-reference with positive time offset is not allowed."""
        formula = "profit[1] + profit[2]"
        name = "profit"
        valid_names = ["profit"]
        
        # Should raise an exception for positive offsets
        with pytest.raises(ValueError, match="Future time references are not allowed: profit\\[1\\], profit\\[2\\]"):
            validate_formula(formula, name, valid_names)

    def test_invalid_positive_offset_single(self):
        """Test that positive time offset raises error for single reference."""
        formula = "revenue[1] + expenses"
        name = "projected_revenue"
        valid_names = ["revenue", "expenses", "projected_revenue"]
        
        with pytest.raises(ValueError, match="Future time references are not allowed: revenue\\[1\\]"):
            validate_formula(formula, name, valid_names)

    def test_invalid_positive_offset_multiple(self):
        """Test that multiple positive time offsets are all reported."""
        formula = "revenue[1] + expenses[2] + costs[3]"
        name = "projection"
        valid_names = ["revenue", "expenses", "costs", "projection"]
        
        with pytest.raises(ValueError, match="Future time references are not allowed: revenue\\[1\\], expenses\\[2\\], costs\\[3\\]"):
            validate_formula(formula, name, valid_names)

    def test_circular_reference_with_zero_offset(self):
        """Test that circular reference with [0] time offset raises error."""
        formula = "profit[0] + expenses"
        name = "profit"
        valid_names = ["profit", "expenses"]
        
        with pytest.raises(ValueError, match="Circular reference detected: formula for 'profit' references itself with \\[0\\] time offset, which is equivalent to no time offset"):
            validate_formula(formula, name, valid_names)

    def test_invalid_single_missing_variable(self):
        """Test formula with one missing variable raises ValueError."""
        formula = "revenue - missing_var"
        name = "profit"
        valid_names = ["revenue", "expenses", "profit"]
        
        with pytest.raises(ValueError, match="Formula contains undefined line item names: missing_var"):
            validate_formula(formula, name, valid_names)

    def test_invalid_multiple_missing_variables(self):
        """Test formula with multiple missing variables raises ValueError."""
        formula = "missing_a + missing_b - revenue"
        name = "result"
        valid_names = ["revenue", "expenses", "result"]
        
        with pytest.raises(ValueError) as exc_info:
            validate_formula(formula, name, valid_names)
        
        error_msg = str(exc_info.value)
        assert "Formula contains undefined line item names:" in error_msg
        assert "missing_a" in error_msg
        assert "missing_b" in error_msg

    def test_invalid_missing_variable_in_time_offset(self):
        """Test formula with missing variable in time offset reference."""
        formula = "revenue + missing_var[-1]"
        name = "total"
        valid_names = ["revenue", "expenses", "total"]

        with pytest.raises(ValueError, match="Formula contains undefined line item names: missing_var"):
            validate_formula(formula, name, valid_names)

    def test_formula_with_numeric_literals(self):
        """Test that numeric literals don't cause validation errors."""
        formula = "revenue * 1.5 + 1000 - expenses"
        name = "adjusted_revenue"
        valid_names = ["revenue", "expenses", "adjusted_revenue"]
        
        # Should not raise any exception
        validate_formula(formula, name, valid_names)

    def test_formula_with_decimal_numbers(self):
        """Test that decimal numbers don't cause validation errors."""
        formula = "revenue * 0.85 + expenses * 1.2"
        name = "weighted_total"
        valid_names = ["revenue", "expenses", "weighted_total"]
        
        # Should not raise any exception
        validate_formula(formula, name, valid_names)

    def test_formula_with_parentheses_and_operators(self):
        """Test formula with various mathematical operators and parentheses."""
        formula = "(revenue + other_income) * (1 - tax_rate) / shares_outstanding"
        name = "earnings_per_share"
        valid_names = ["revenue", "other_income", "tax_rate", "shares_outstanding", "earnings_per_share"]
        
        # Should not raise any exception
        validate_formula(formula, name, valid_names)

    def test_formula_with_whitespace(self):
        """Test that whitespace is handled correctly."""
        formula = "  revenue   -   expenses  "
        name = "profit"
        valid_names = ["revenue", "expenses", "profit"]
        
        # Should not raise any exception
        validate_formula(formula, name, valid_names)

    def test_empty_formula(self):
        """Test empty formula doesn't raise errors."""
        formula = ""
        name = "empty_item"
        valid_names = ["revenue", "expenses", "empty_item"]
        
        # Should not raise any exception
        validate_formula(formula, name, valid_names)

    def test_formula_with_only_numbers(self):
        """Test formula with only numeric values."""
        formula = "1000 + 500 * 1.2"
        name = "constant"
        valid_names = ["revenue", "expenses", "constant"]
        
        # Should not raise any exception
        validate_formula(formula, name, valid_names)

    def test_formula_with_negative_time_offsets(self):
        """Test formula with various negative time offsets."""
        formula = "revenue[-1] + revenue[-2] + revenue[-3]"
        name = "moving_average"
        valid_names = ["revenue", "moving_average"]
        
        # Should not raise any exception
        validate_formula(formula, name, valid_names)

    def test_formula_with_positive_time_offsets(self):
        """Test formula with positive time offsets raises error."""
        formula = "revenue[1] + revenue[2]"
        name = "future_projection"
        valid_names = ["revenue", "future_projection"]
        
        # Should raise an exception for positive time offsets
        with pytest.raises(ValueError, match="Future time references are not allowed: revenue\\[1\\], revenue\\[2\\]"):
            validate_formula(formula, name, valid_names)

    def test_formula_with_underscore_variables(self):
        """Test formula with variable names containing underscores."""
        formula = "gross_revenue - cost_of_goods_sold"
        name = "net_income"
        valid_names = ["gross_revenue", "cost_of_goods_sold", "net_income"]
        
        # Should not raise any exception
        validate_formula(formula, name, valid_names)

    def test_formula_ignores_python_keywords(self):
        """Test that Python keywords in formulas don't cause issues."""
        # Note: This tests the filtering logic, though in practice formulas 
        # shouldn't contain Python keywords as variable names
        formula = "revenue + if + for"  # 'if' and 'for' are Python keywords
        name = "test_item"
        valid_names = ["revenue", "test_item"]
        
        # Should raise error only for the undefined variables that aren't keywords
        # Keywords should be ignored by the validation
        # This test verifies the keyword filtering works
        validate_formula(formula, name, valid_names)

    def test_case_sensitive_validation(self):
        """Test that variable name validation is case sensitive."""
        formula = "Revenue + EXPENSES"  # Different case
        name = "total"
        valid_names = ["revenue", "expenses", "total"]  # lowercase
        
        with pytest.raises(ValueError) as exc_info:
            validate_formula(formula, name, valid_names)
        
        error_msg = str(exc_info.value)
        assert "Revenue" in error_msg or "EXPENSES" in error_msg

    def test_formula_with_dots_in_variable_names(self):
        """Test formula with variable names containing dots (if supported)."""
        formula = "company.revenue - company.expenses"
        name = "company.profit"
        valid_names = ["company.revenue", "company.expenses", "company.profit"]
        
        # Should not raise any exception
        validate_formula(formula, name, valid_names)

    def test_duplicate_variables_in_formula(self):
        """Test formula where same variable appears multiple times."""
        formula = "revenue + revenue * 0.1 + revenue[-1]"
        name = "adjusted_revenue"
        valid_names = ["revenue", "adjusted_revenue"]
        
        # Should not raise any exception
        validate_formula(formula, name, valid_names)

    def test_complex_mathematical_expression(self):
        """Test complex mathematical expression with all valid variables."""
        formula = "((revenue - cogs) / revenue) * 100 + margin[-1]"
        name = "current_margin"
        valid_names = ["revenue", "cogs", "margin", "current_margin"]
        
        # Should not raise any exception
        validate_formula(formula, name, valid_names)

    def test_error_message_sorted_variables(self):
        """Test that error message contains sorted variable names."""
        formula = "zebra + alpha + beta"
        name = "test_item"
        valid_names = ["revenue", "test_item"]
        
        with pytest.raises(ValueError) as exc_info:
            validate_formula(formula, name, valid_names)
        
        error_msg = str(exc_info.value)
        # Check that variables appear in sorted order
        assert "alpha, beta, zebra" in error_msg
    
    def test_circular_reference_complex_formula(self):
        """Test circular reference detection in complex formulas."""
        formula = "revenue + profit * 0.1 - expenses"
        name = "profit"
        valid_names = ["revenue", "profit", "expenses"]
        
        with pytest.raises(ValueError, match="Circular reference detected: formula for 'profit' references itself without a time offset"):
            validate_formula(formula, name, valid_names)
    
    def test_no_false_positive_circular_reference(self):
        """Test that similar names don't trigger false positive circular references."""
        formula = "profit_margin + profit_tax"
        name = "profit"
        valid_names = ["profit", "profit_margin", "profit_tax"]
        
        # Should not raise any exception - profit_margin and profit_tax are different from profit
        validate_formula(formula, name, valid_names)
    
    def test_circular_reference_with_zero_offset(self):
        """Test that circular reference with [0] time offset raises error."""
        formula = "profit[0] + expenses"
        name = "profit"
        valid_names = ["profit", "expenses"]
        
        with pytest.raises(ValueError, match="Circular reference detected: formula for 'profit' references itself with \\[0\\] time offset, which is equivalent to no time offset"):
            validate_formula(formula, name, valid_names)

    def test_circular_reference_with_dots(self):
        """Test circular reference detection with dotted names."""
        formula = "company.profit + revenue"
        name = "company.profit"
        valid_names = ["company.profit", "revenue"]
        
        with pytest.raises(ValueError, match="Circular reference detected: formula for 'company.profit' references itself without a time offset"):
            validate_formula(formula, name, valid_names)
