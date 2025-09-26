import pytest

from pyproforma.models.formula.formula_2 import evaluate


class TestEvaluate:
    """Test cases for the evaluate function in formula_2.py"""

    def test_basic_arithmetic(self):
        """Test basic arithmetic operations without variables"""
        assert evaluate("2 + 3") == 5
        assert evaluate("10 - 4") == 6
        assert evaluate("3 * 4") == 12
        assert evaluate("15 / 3") == 5.0
        assert evaluate("2 ** 3") == 8
        assert evaluate("10 % 3") == 1
        assert evaluate("15 // 4") == 3

    def test_operator_precedence(self):
        """Test that operator precedence is respected"""
        assert evaluate("2 + 3 * 4") == 14  # Not 20
        assert evaluate("(2 + 3) * 4") == 20
        assert evaluate("10 - 2 * 3") == 4  # Not 24
        assert evaluate("(10 - 2) * 3") == 24

    def test_unary_operators(self):
        """Test unary plus and minus operators"""
        assert evaluate("-5") == -5
        assert evaluate("+5") == 5
        assert evaluate("-(-5)") == 5
        assert evaluate("-(2 + 3)") == -5

    def test_complex_expressions(self):
        """Test more complex mathematical expressions"""
        assert evaluate("5 * 3 - 2 + 7 / 6") == pytest.approx(14.166666666666666)
        assert evaluate("(10 + 5) / 3") == 5.0
        assert evaluate("2 ** 3 + 4 * 5") == 28
        assert evaluate("100 / (2 + 3) * 4") == 80.0

    def test_variables_basic(self):
        """Test basic variable substitution"""
        variables = {"x": 5, "y": 3}
        assert evaluate("x + y", variables) == 8
        assert evaluate("x * y", variables) == 15
        assert evaluate("x - y", variables) == 2
        assert evaluate("x / y", variables) == pytest.approx(1.6666666666666667)

    def test_variables_complex(self):
        """Test complex expressions with variables"""
        variables = {"revenue": 1000, "tax_rate": 0.1, "growth": 1.15}
        assert evaluate("revenue * tax_rate", variables) == 100.0
        assert evaluate("revenue * growth", variables) == 1150.0
        assert evaluate("revenue * (1 + tax_rate)", variables) == 1100.0

    def test_mixed_variables_and_numbers(self):
        """Test expressions mixing variables and numbers"""
        variables = {"base": 100, "multiplier": 2.5}
        assert evaluate("base * multiplier + 50", variables) == 300.0
        assert evaluate("(base + 100) * multiplier", variables) == 500.0
        assert evaluate("base / 2 + multiplier * 10", variables) == 75.0

    def test_financial_modeling_examples(self):
        """Test examples typical in financial modeling"""
        variables = {
            "previous_year": 100,
            "growth_rate": 1.15,
            "discount_rate": 0.9,
            "tax_rate": 0.25,
        }

        # Year-over-year growth
        assert evaluate("previous_year * growth_rate", variables) == pytest.approx(
            115.0
        )

        # After-tax calculation
        result = evaluate("previous_year * (1 - tax_rate)", variables)
        assert result == 75.0

        # Present value calculation
        result = evaluate("previous_year * discount_rate", variables)
        assert result == 90.0

    def test_variable_not_provided_error(self):
        """Test error when variable is used but no variables dict provided"""
        with pytest.raises(
            ValueError, match="Variable 'x' used but no variables provided"
        ):
            evaluate("x + 5")

    def test_unknown_variable_error(self):
        """Test error when unknown variable is referenced"""
        variables = {"x": 5}
        with pytest.raises(ValueError, match="Unknown variable: 'y'"):
            evaluate("x + y", variables)

    def test_division_by_zero_error(self):
        """Test division by zero error handling"""
        with pytest.raises(ZeroDivisionError, match="Division by zero in formula"):
            evaluate("10 / 0")

        variables = {"x": 0}
        with pytest.raises(ZeroDivisionError, match="Division by zero in formula"):
            evaluate("10 / x", variables)

    def test_invalid_syntax_error(self):
        """Test syntax error handling"""
        with pytest.raises(SyntaxError, match="Invalid formula syntax"):
            evaluate("2 +")

        with pytest.raises(SyntaxError, match="Invalid formula syntax"):
            evaluate("* 5")

    def test_unsupported_operations(self):
        """Test that unsupported operations raise appropriate errors"""
        # Function calls are not supported
        with pytest.raises(ValueError, match="Unsupported AST node type"):
            evaluate("abs(-5)")

        # Comparisons are not supported
        with pytest.raises(ValueError, match="Unsupported AST node type"):
            evaluate("5 > 3")

    def test_float_precision(self):
        """Test floating point calculations"""
        assert evaluate("0.1 + 0.2") == pytest.approx(0.3)
        assert evaluate("1.5 * 2.3") == pytest.approx(3.45)

        variables = {"rate": 0.075}
        assert evaluate("1000 * rate", variables) == 75.0

    def test_negative_variables(self):
        """Test with negative variable values"""
        variables = {"loss": -50, "adjustment": 25}
        assert evaluate("loss + adjustment", variables) == -25
        assert evaluate("loss * -1", variables) == 50
        assert evaluate("adjustment - loss", variables) == 75

    def test_zero_values(self):
        """Test with zero values"""
        variables = {"zero": 0, "value": 100}
        assert evaluate("zero + value", variables) == 100
        assert evaluate("zero * value", variables) == 0
        assert evaluate("value - value", variables) == 0

    def test_large_numbers(self):
        """Test with large numbers"""
        variables = {"million": 1000000, "billion": 1000000000}
        assert evaluate("million * 1000", variables) == 1000000000
        assert evaluate("billion / million", variables) == 1000.0

    def test_formula_strings_with_spaces(self):
        """Test that formulas with various spacing work correctly"""
        variables = {"x": 10, "y": 5}
        assert evaluate("x+y", variables) == 15
        assert evaluate("x + y", variables) == 15
        assert evaluate("  x + y  ", variables) == 15  # Leading/trailing spaces
        assert evaluate("x*y+2", variables) == 52
