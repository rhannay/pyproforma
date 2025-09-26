import pytest

from pyproforma.models.formula.formula_2 import evaluate


class TestEvaluate:
    """Test cases for the evaluate function in formula_2.py"""

    # Sample value matrix for testing
    @pytest.fixture
    def sample_matrix(self):
        return {
            2024: {
                "revenue": 1000.0,
                "expenses": 800.0,
                "tax_rate": 0.25,
                "x": 5.0,
                "y": 3.0,
                "base": 100.0,
                "multiplier": 2.5,
                "previous_year": 100.0,
                "growth_rate": 1.15,
                "discount_rate": 0.9,
                "loss": -50.0,
                "adjustment": 25.0,
                "zero": 0.0,
                "value": 100.0,
                "million": 1000000.0,
                "billion": 1000000000.0,
                "rate": 0.075,
            },
            2023: {
                "revenue": 900.0,
                "expenses": 750.0,
                "tax_rate": 0.25,
                "x": 4.0,
                "y": 2.0,
                "base": 90.0,
                "multiplier": 2.0,
                "previous_year": 90.0,
                "growth_rate": 1.10,
                "discount_rate": 0.85,
                "loss": -40.0,
                "adjustment": 20.0,
                "zero": 0.0,
                "value": 90.0,
                "million": 900000.0,
                "billion": 900000000.0,
                "rate": 0.070,
            },
            2022: {
                "revenue": 800.0,
                "expenses": 700.0,
                "tax_rate": 0.25,
                "x": 3.0,
                "y": 1.0,
                "base": 80.0,
                "multiplier": 1.5,
                "previous_year": 80.0,
                "growth_rate": 1.05,
                "discount_rate": 0.80,
                "loss": -30.0,
                "adjustment": 15.0,
                "zero": 0.0,
                "value": 80.0,
                "million": 800000.0,
                "billion": 800000000.0,
                "rate": 0.065,
            },
        }

    def test_basic_arithmetic(self, sample_matrix):
        """Test basic arithmetic operations without variables"""
        assert evaluate("2 + 3", sample_matrix, 2024) == 5
        assert evaluate("10 - 4", sample_matrix, 2024) == 6
        assert evaluate("3 * 4", sample_matrix, 2024) == 12
        assert evaluate("15 / 3", sample_matrix, 2024) == 5.0
        assert evaluate("2 ** 3", sample_matrix, 2024) == 8
        assert evaluate("10 % 3", sample_matrix, 2024) == 1
        assert evaluate("15 // 4", sample_matrix, 2024) == 3

    def test_operator_precedence(self, sample_matrix):
        """Test that operator precedence is respected"""
        assert evaluate("2 + 3 * 4", sample_matrix, 2024) == 14  # Not 20
        assert evaluate("(2 + 3) * 4", sample_matrix, 2024) == 20
        assert evaluate("10 - 2 * 3", sample_matrix, 2024) == 4  # Not 24
        assert evaluate("(10 - 2) * 3", sample_matrix, 2024) == 24

    def test_unary_operators(self, sample_matrix):
        """Test unary plus and minus operators"""
        assert evaluate("-5", sample_matrix, 2024) == -5
        assert evaluate("+5", sample_matrix, 2024) == 5
        assert evaluate("-(-5)", sample_matrix, 2024) == 5
        assert evaluate("-(2 + 3)", sample_matrix, 2024) == -5

    def test_complex_expressions(self, sample_matrix):
        """Test more complex mathematical expressions"""
        result = evaluate("5 * 3 - 2 + 7 / 6", sample_matrix, 2024)
        assert result == pytest.approx(14.166666666666666)
        assert evaluate("(10 + 5) / 3", sample_matrix, 2024) == 5.0
        assert evaluate("2 ** 3 + 4 * 5", sample_matrix, 2024) == 28
        assert evaluate("100 / (2 + 3) * 4", sample_matrix, 2024) == 80.0

    def test_variables_basic(self, sample_matrix):
        """Test basic variable substitution"""
        assert evaluate("x + y", sample_matrix, 2024) == 8
        assert evaluate("x * y", sample_matrix, 2024) == 15
        assert evaluate("x - y", sample_matrix, 2024) == 2
        result = evaluate("x / y", sample_matrix, 2024)
        assert result == pytest.approx(1.6666666666666667)

    def test_variables_complex(self, sample_matrix):
        """Test complex expressions with variables"""
        assert evaluate("revenue * tax_rate", sample_matrix, 2024) == 250.0
        assert evaluate("revenue - expenses", sample_matrix, 2024) == 200.0
        result = evaluate("revenue * (1 + tax_rate)", sample_matrix, 2024)
        assert result == 1250.0

    def test_negative_indexing(self, sample_matrix):
        """Test variable references with negative indexing"""
        # Previous year values
        assert evaluate("revenue[-1]", sample_matrix, 2024) == 900.0
        assert evaluate("expenses[-1]", sample_matrix, 2024) == 750.0

        # Two years ago
        assert evaluate("revenue[-2]", sample_matrix, 2024) == 800.0

        # Mixed current and previous year
        result = evaluate("revenue / revenue[-1]", sample_matrix, 2024)
        assert result == pytest.approx(1.1111111111111112)

        # Complex formula with indexing
        result = evaluate("revenue[-1] * 1.1 + expenses", sample_matrix, 2024)
        assert result == 1790.0

    def test_mixed_variables_and_numbers(self, sample_matrix):
        """Test expressions mixing variables and numbers"""
        assert evaluate("base * multiplier + 50", sample_matrix, 2024) == 300.0
        result = evaluate("(base + 100) * multiplier", sample_matrix, 2024)
        assert result == 500.0
        assert evaluate("base / 2 + multiplier * 10", sample_matrix, 2024) == 75.0

    def test_financial_modeling_examples(self, sample_matrix):
        """Test examples typical in financial modeling"""
        # Year-over-year growth
        result = evaluate("previous_year * growth_rate", sample_matrix, 2024)
        assert result == pytest.approx(115.0)

        # After-tax calculation
        result = evaluate("previous_year * (1 - tax_rate)", sample_matrix, 2024)
        assert result == 75.0

        # Present value calculation
        result = evaluate("previous_year * discount_rate", sample_matrix, 2024)
        assert result == 90.0

    def test_year_not_found_error(self, sample_matrix):
        """Test error when year is not in value matrix"""
        with pytest.raises(ValueError, match="Year 2025 not found in value matrix"):
            evaluate("revenue", sample_matrix, 2025)

    def test_variable_not_found_error(self, sample_matrix):
        """Test error when variable is not found for the given year"""
        with pytest.raises(
            ValueError, match="Variable 'unknown_var' not found for year 2024"
        ):
            evaluate("unknown_var", sample_matrix, 2024)

    def test_indexed_variable_not_found_error(self, sample_matrix):
        """Test error when indexed variable references unavailable year"""
        with pytest.raises(ValueError, match="Year 2021 not found in value matrix"):
            evaluate("revenue[-3]", sample_matrix, 2024)

    def test_positive_index_error(self, sample_matrix):
        """Test error when using positive indices"""
        with pytest.raises(
            ValueError, match="Only negative indices are allowed, got 1"
        ):
            evaluate("revenue[1]", sample_matrix, 2024)

    def test_zero_index_error(self, sample_matrix):
        """Test error when using zero index"""
        with pytest.raises(
            ValueError, match="Only negative indices are allowed, got 0"
        ):
            evaluate("revenue[0]", sample_matrix, 2024)

    def test_division_by_zero_error(self, sample_matrix):
        """Test division by zero error handling"""
        with pytest.raises(ZeroDivisionError, match="Division by zero in formula"):
            evaluate("10 / 0", sample_matrix, 2024)

        with pytest.raises(ZeroDivisionError, match="Division by zero in formula"):
            evaluate("10 / zero", sample_matrix, 2024)

    def test_invalid_syntax_error(self, sample_matrix):
        """Test syntax error handling"""
        with pytest.raises(SyntaxError, match="Invalid formula syntax"):
            evaluate("2 +", sample_matrix, 2024)

        with pytest.raises(SyntaxError, match="Invalid formula syntax"):
            evaluate("* 5", sample_matrix, 2024)

    def test_unsupported_operations(self, sample_matrix):
        """Test that unsupported operations raise appropriate errors"""
        # Function calls are not supported
        with pytest.raises(ValueError, match="Unsupported AST node type"):
            evaluate("abs(-5)", sample_matrix, 2024)

        # Comparisons are not supported
        with pytest.raises(ValueError, match="Unsupported AST node type"):
            evaluate("5 > 3", sample_matrix, 2024)

    def test_float_precision(self, sample_matrix):
        """Test floating point calculations"""
        assert evaluate("0.1 + 0.2", sample_matrix, 2024) == pytest.approx(0.3)
        result = evaluate("1.5 * 2.3", sample_matrix, 2024)
        assert result == pytest.approx(3.45)

        assert evaluate("1000 * rate", sample_matrix, 2024) == 75.0

    def test_negative_variables(self, sample_matrix):
        """Test with negative variable values"""
        assert evaluate("loss + adjustment", sample_matrix, 2024) == -25
        assert evaluate("loss * -1", sample_matrix, 2024) == 50
        assert evaluate("adjustment - loss", sample_matrix, 2024) == 75

    def test_zero_values(self, sample_matrix):
        """Test with zero values"""
        assert evaluate("zero + value", sample_matrix, 2024) == 100
        assert evaluate("zero * value", sample_matrix, 2024) == 0
        assert evaluate("value - value", sample_matrix, 2024) == 0

    def test_large_numbers(self, sample_matrix):
        """Test with large numbers"""
        assert evaluate("million * 1000", sample_matrix, 2024) == 1000000000
        assert evaluate("billion / million", sample_matrix, 2024) == 1000.0

    def test_formula_strings_with_spaces(self, sample_matrix):
        """Test that formulas with various spacing work correctly"""
        assert evaluate("x+y", sample_matrix, 2024) == 8
        assert evaluate("x + y", sample_matrix, 2024) == 8
        # Leading/trailing spaces
        assert evaluate("  x + y  ", sample_matrix, 2024) == 8
        assert evaluate("x*y+2", sample_matrix, 2024) == 17

    def test_none_values_as_zero(self):
        """Test that None values are treated as zero"""
        matrix_with_none = {
            2024: {"revenue": None, "expenses": 800.0},
            2023: {"revenue": 900.0, "expenses": None},
        }

        # Test None in current year - should be treated as 0
        result = evaluate("revenue + expenses", matrix_with_none, 2024)
        assert result == 800.0  # None (0) + 800.0

        # Test None in indexed year - should be treated as 0
        result = evaluate("expenses[-1] + 100", matrix_with_none, 2024)
        assert result == 100.0  # None (0) + 100

        # Test arithmetic with None values
        result = evaluate("revenue * 5", matrix_with_none, 2024)
        assert result == 0.0  # None (0) * 5

        # Test mixed None and non-None values
        result = evaluate("revenue + expenses + 50", matrix_with_none, 2024)
        assert result == 850.0  # 0 + 800 + 50
