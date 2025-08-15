import pytest
from pyproforma.models.formula import validate_formula


class TestValidateFormula:
    """Test cases for the validate_formula function."""

    def test_valid_simple_formula(self):
        """Test formula with valid variables passes validation."""
        formula = "revenue - expenses"
        variables = ["revenue", "expenses", "profit"]
        
        # Should not raise any exception
        validate_formula(formula, variables)

    def test_valid_complex_formula(self):
        """Test complex formula with multiple operations and valid variables."""
        formula = "revenue * (1 - tax_rate) - expenses + depreciation"
        variables = ["revenue", "tax_rate", "expenses", "depreciation", "profit"]
        
        # Should not raise any exception
        validate_formula(formula, variables)

    def test_valid_formula_with_time_offsets(self):
        """Test formula with time offset references."""
        formula = "revenue[-1] * growth_rate + expenses[-2]"
        variables = ["revenue", "growth_rate", "expenses"]
        
        # Should not raise any exception
        validate_formula(formula, variables)

    def test_valid_formula_with_mixed_references(self):
        """Test formula with both current year and time offset references."""
        formula = "revenue - expenses + revenue[-1] * 0.1"
        variables = ["revenue", "expenses"]
        
        # Should not raise any exception
        validate_formula(formula, variables)

    def test_invalid_single_missing_variable(self):
        """Test formula with one missing variable raises ValueError."""
        formula = "revenue - missing_var"
        variables = ["revenue", "expenses"]
        
        with pytest.raises(ValueError, match="Formula contains undefined line item names: missing_var"):
            validate_formula(formula, variables)

    def test_invalid_multiple_missing_variables(self):
        """Test formula with multiple missing variables raises ValueError."""
        formula = "missing_a + missing_b - revenue"
        variables = ["revenue", "expenses"]
        
        with pytest.raises(ValueError) as exc_info:
            validate_formula(formula, variables)
        
        error_msg = str(exc_info.value)
        assert "Formula contains undefined line item names:" in error_msg
        assert "missing_a" in error_msg
        assert "missing_b" in error_msg

    def test_invalid_missing_variable_in_time_offset(self):
        """Test formula with missing variable in time offset reference."""
        formula = "revenue + missing_var[-1]"
        variables = ["revenue", "expenses"]

        with pytest.raises(ValueError, match="Formula contains undefined line item names: missing_var"):
            validate_formula(formula, variables)

    def test_formula_with_numeric_literals(self):
        """Test that numeric literals don't cause validation errors."""
        formula = "revenue * 1.5 + 1000 - expenses"
        variables = ["revenue", "expenses"]
        
        # Should not raise any exception
        validate_formula(formula, variables)

    def test_formula_with_decimal_numbers(self):
        """Test that decimal numbers don't cause validation errors."""
        formula = "revenue * 0.85 + expenses * 1.2"
        variables = ["revenue", "expenses"]
        
        # Should not raise any exception
        validate_formula(formula, variables)

    def test_formula_with_parentheses_and_operators(self):
        """Test formula with various mathematical operators and parentheses."""
        formula = "(revenue + other_income) * (1 - tax_rate) / shares_outstanding"
        variables = ["revenue", "other_income", "tax_rate", "shares_outstanding"]
        
        # Should not raise any exception
        validate_formula(formula, variables)

    def test_formula_with_whitespace(self):
        """Test that whitespace is handled correctly."""
        formula = "  revenue   -   expenses  "
        variables = ["revenue", "expenses"]
        
        # Should not raise any exception
        validate_formula(formula, variables)

    def test_empty_formula(self):
        """Test empty formula doesn't raise errors."""
        formula = ""
        variables = ["revenue", "expenses"]
        
        # Should not raise any exception
        validate_formula(formula, variables)

    def test_formula_with_only_numbers(self):
        """Test formula with only numeric values."""
        formula = "1000 + 500 * 1.2"
        variables = ["revenue", "expenses"]
        
        # Should not raise any exception
        validate_formula(formula, variables)

    def test_formula_with_negative_time_offsets(self):
        """Test formula with various negative time offsets."""
        formula = "revenue[-1] + revenue[-2] + revenue[-3]"
        variables = ["revenue"]
        
        # Should not raise any exception
        validate_formula(formula, variables)

    def test_formula_with_positive_time_offsets(self):
        """Test formula with positive time offsets."""
        formula = "revenue[1] + revenue[2]"
        variables = ["revenue"]
        
        # Should not raise any exception
        validate_formula(formula, variables)

    def test_formula_with_underscore_variables(self):
        """Test formula with variable names containing underscores."""
        formula = "gross_revenue - cost_of_goods_sold"
        variables = ["gross_revenue", "cost_of_goods_sold", "net_income"]
        
        # Should not raise any exception
        validate_formula(formula, variables)

    def test_formula_ignores_python_keywords(self):
        """Test that Python keywords in formulas don't cause issues."""
        # Note: This tests the filtering logic, though in practice formulas 
        # shouldn't contain Python keywords as variable names
        formula = "revenue + if + for"  # 'if' and 'for' are Python keywords
        variables = ["revenue"]
        
        # Should raise error only for the undefined variables that aren't keywords
        # Keywords should be ignored by the validation
        # This test verifies the keyword filtering works
        validate_formula(formula, variables)

    def test_case_sensitive_validation(self):
        """Test that variable name validation is case sensitive."""
        formula = "Revenue + EXPENSES"  # Different case
        variables = ["revenue", "expenses"]  # lowercase
        
        with pytest.raises(ValueError) as exc_info:
            validate_formula(formula, variables)
        
        error_msg = str(exc_info.value)
        assert "Revenue" in error_msg or "EXPENSES" in error_msg

    def test_formula_with_dots_in_variable_names(self):
        """Test formula with variable names containing dots (if supported)."""
        formula = "company.revenue - company.expenses"
        variables = ["company.revenue", "company.expenses"]
        
        # Should not raise any exception
        validate_formula(formula, variables)

    def test_duplicate_variables_in_formula(self):
        """Test formula where same variable appears multiple times."""
        formula = "revenue + revenue * 0.1 + revenue[-1]"
        variables = ["revenue"]
        
        # Should not raise any exception
        validate_formula(formula, variables)

    def test_complex_mathematical_expression(self):
        """Test complex mathematical expression with all valid variables."""
        formula = "((revenue - cogs) / revenue) * 100 + margin[-1]"
        variables = ["revenue", "cogs", "margin"]
        
        # Should not raise any exception
        validate_formula(formula, variables)

    def test_error_message_sorted_variables(self):
        """Test that error message contains sorted variable names."""
        formula = "zebra + alpha + beta"
        variables = ["revenue"]
        
        with pytest.raises(ValueError) as exc_info:
            validate_formula(formula, variables)
        
        error_msg = str(exc_info.value)
        # Check that variables appear in sorted order
        assert "alpha, beta, zebra" in error_msg
