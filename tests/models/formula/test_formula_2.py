import ast

import pytest

from pyproforma.models.formula.formula_2 import _validate_indexed_value, evaluate


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


class TestValidateIndexedValue:
    """Test cases for the _validate_indexed_value function."""

    @pytest.fixture
    def sample_matrix(self):
        """Sample value matrix for testing."""
        return {
            2024: {"revenue": 1000.0, "expenses": 800.0, "profit": None},
            2023: {"revenue": 900.0, "expenses": 750.0, "profit": None},
            2022: {"revenue": 800.0, "expenses": 700.0, "profit": 100.0},
        }

    def _create_subscript_node(self, var_name: str, index: int) -> ast.Subscript:
        """Helper to create AST Subscript nodes for testing."""
        # Create the variable name node
        name_node = ast.Name(id=var_name, ctx=ast.Load())

        # Create the index node - handle positive and negative indices differently
        if index < 0:
            # Negative index: create UnaryOp with USub
            index_node = ast.UnaryOp(
                op=ast.USub(),
                operand=ast.Constant(
                    value=-index
                ),  # Store positive value, USub makes it negative
            )
        else:
            # Positive index: create Constant directly
            index_node = ast.Constant(value=index)

        # Create the subscript node
        return ast.Subscript(value=name_node, slice=index_node, ctx=ast.Load())

    def test_valid_negative_index_lookup(self, sample_matrix):
        """Test successful lookup with negative indices."""
        # Test revenue[-1] from 2024 (should get 2023 value)
        node = self._create_subscript_node("revenue", -1)
        result = _validate_indexed_value(node, sample_matrix, 2024)
        assert result == 900.0

        # Test revenue[-2] from 2024 (should get 2022 value)
        node = self._create_subscript_node("revenue", -2)
        result = _validate_indexed_value(node, sample_matrix, 2024)
        assert result == 800.0

        # Test expenses[-1] from 2023 (should get 2022 value)
        node = self._create_subscript_node("expenses", -1)
        result = _validate_indexed_value(node, sample_matrix, 2023)
        assert result == 700.0

    def test_none_value_returns_zero(self, sample_matrix):
        """Test that None values are returned as 0.0."""
        # Current year None value
        node = self._create_subscript_node("profit", -1)
        result = _validate_indexed_value(node, sample_matrix, 2024)
        assert result == 0.0  # profit in 2023 was None -> should become 0.0

    def test_positive_index_raises_error(self, sample_matrix):
        """Test that positive indices raise ValueError."""
        node = self._create_subscript_node("revenue", 1)
        with pytest.raises(
            ValueError, match="Only negative indices are allowed, got 1"
        ):
            _validate_indexed_value(node, sample_matrix, 2024)

    def test_zero_index_raises_error(self, sample_matrix):
        """Test that zero index raises ValueError."""
        node = self._create_subscript_node("revenue", 0)
        with pytest.raises(
            ValueError, match="Only negative indices are allowed, got 0"
        ):
            _validate_indexed_value(node, sample_matrix, 2024)

    def test_missing_year_raises_error(self, sample_matrix):
        """Test that missing target year raises ValueError."""
        # Try to access revenue[-3] from 2024, which would need 2021 data
        node = self._create_subscript_node("revenue", -3)
        with pytest.raises(ValueError, match="Year 2021 not found in value matrix"):
            _validate_indexed_value(node, sample_matrix, 2024)

    def test_missing_variable_raises_error(self, sample_matrix):
        """Test that missing variable in target year raises ValueError."""
        # Add a year that doesn't have all variables
        matrix_with_missing = sample_matrix.copy()
        matrix_with_missing[2021] = {"revenue": 700.0}  # Missing expenses

        node = self._create_subscript_node("expenses", -3)
        with pytest.raises(
            ValueError, match="Variable 'expenses' not found for year 2021"
        ):
            _validate_indexed_value(node, matrix_with_missing, 2024)

    def test_non_name_variable_raises_error(self, sample_matrix):
        """Test that non-Name variable nodes raise ValueError."""
        # Create a subscript node with a non-Name variable (e.g., a constant)
        subscript_node = ast.Subscript(
            value=ast.Constant(value=5),  # Not a name
            slice=ast.Constant(value=-1),
            ctx=ast.Load(),
        )

        with pytest.raises(
            ValueError, match="Only simple variable indexing is supported"
        ):
            _validate_indexed_value(subscript_node, sample_matrix, 2024)

    def test_non_constant_index_raises_error(self, sample_matrix):
        """Test that non-constant indices raise ValueError."""
        # Create a subscript node with a variable as index
        subscript_node = ast.Subscript(
            value=ast.Name(id="revenue", ctx=ast.Load()),
            slice=ast.Name(id="x", ctx=ast.Load()),  # Variable as index, not constant
            ctx=ast.Load(),
        )

        with pytest.raises(
            ValueError, match="Only constant integer indices are supported"
        ):
            _validate_indexed_value(subscript_node, sample_matrix, 2024)

    def test_non_integer_index_raises_error(self, sample_matrix):
        """Test that non-integer indices raise ValueError."""
        # Create a subscript node with a float index
        subscript_node = ast.Subscript(
            value=ast.Name(id="revenue", ctx=ast.Load()),
            slice=ast.Constant(value=-1.5),  # Float index
            ctx=ast.Load(),
        )

        with pytest.raises(ValueError, match="Index must be an integer"):
            _validate_indexed_value(subscript_node, sample_matrix, 2024)

    def test_complex_unary_op_raises_error(self, sample_matrix):
        """Test that complex unary operations (not simple negation) raise ValueError."""
        # Create a subscript node with UnaryOp that's not simple negation
        subscript_node = ast.Subscript(
            value=ast.Name(id="revenue", ctx=ast.Load()),
            slice=ast.UnaryOp(
                op=ast.USub(),
                operand=ast.Name(id="x", ctx=ast.Load()),  # Variable in unary op
            ),
            ctx=ast.Load(),
        )

        with pytest.raises(
            ValueError, match="Only constant integer indices are supported"
        ):
            _validate_indexed_value(subscript_node, sample_matrix, 2024)

    def test_year_calculation_accuracy(self, sample_matrix):
        """Test that year calculations are accurate for various indices."""
        # Test multiple negative indices to ensure year calculation is correct
        test_cases = [
            (-1, 2023),  # 2024 + (-1) = 2023
            (-2, 2022),  # 2024 + (-2) = 2022
            (-1, 2022),  # 2023 + (-1) = 2022 (when starting from 2023)
        ]

        for index, expected_year in test_cases[
            :2
        ]:  # Test first two with 2024 as base year
            node = self._create_subscript_node("revenue", index)
            expected_value = sample_matrix[expected_year]["revenue"]
            result = _validate_indexed_value(node, sample_matrix, 2024)
            assert result == expected_value

        # Test the last case with 2023 as base year
        node = self._create_subscript_node("revenue", -1)
        result = _validate_indexed_value(node, sample_matrix, 2023)
        assert result == sample_matrix[2022]["revenue"]

    def test_edge_case_matrix_structures(self):
        """Test with various edge case matrix structures."""
        # Empty matrix
        empty_matrix = {}
        node = self._create_subscript_node("revenue", -1)
        with pytest.raises(ValueError, match="Year 2023 not found in value matrix"):
            _validate_indexed_value(node, empty_matrix, 2024)

        # Matrix with only current year
        single_year_matrix = {2024: {"revenue": 1000.0}}
        with pytest.raises(ValueError, match="Year 2023 not found in value matrix"):
            _validate_indexed_value(node, single_year_matrix, 2024)

        # Matrix with empty year dictionary
        empty_year_matrix = {2024: {"revenue": 1000.0}, 2023: {}}
        with pytest.raises(
            ValueError, match="Variable 'revenue' not found for year 2023"
        ):
            _validate_indexed_value(node, empty_year_matrix, 2024)
