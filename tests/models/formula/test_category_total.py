"""Tests for category_total function and evaluate function with category_total usage."""

import pytest

from pyproforma.models.formula import category_total, evaluate


class TestCategoryTotal:
    """Test the category_total function directly."""

    def test_category_total_basic(self):
        """Test basic category total calculation."""
        value_matrix = {
            2024: {
                "revenue": 1000.0,
                "salary": 500.0,
                "rent": 200.0,
                "utilities": 100.0,
            }
        }

        line_item_metadata = [
            {"name": "revenue", "category": "income"},
            {"name": "salary", "category": "expenses"},
            {"name": "rent", "category": "expenses"},
            {"name": "utilities", "category": "expenses"},
        ]

        # Test income category
        result = category_total("income", value_matrix, 2024, line_item_metadata)
        assert result == 1000.0

        # Test expenses category
        result = category_total("expenses", value_matrix, 2024, line_item_metadata)
        assert result == 800.0  # 500 + 200 + 100

    def test_category_total_empty_category(self):
        """Test category total with no items in category."""
        value_matrix = {
            2024: {
                "revenue": 1000.0,
                "salary": 500.0,
            }
        }

        line_item_metadata = [
            {"name": "revenue", "category": "income"},
            {"name": "salary", "category": "expenses"},
        ]

        result = category_total("nonexistent", value_matrix, 2024, line_item_metadata)
        assert result == 0.0

    def test_category_total_with_none_values(self):
        """Test category total handling None values."""
        value_matrix = {
            2024: {
                "revenue": 1000.0,
                "salary": None,
                "rent": 200.0,
            }
        }

        line_item_metadata = [
            {"name": "revenue", "category": "income"},
            {"name": "salary", "category": "expenses"},
            {"name": "rent", "category": "expenses"},
        ]

        result = category_total("expenses", value_matrix, 2024, line_item_metadata)
        assert result == 200.0  # None is treated as 0

    def test_category_total_missing_year(self):
        """Test category total with missing year in value matrix."""
        value_matrix = {
            2023: {
                "revenue": 1000.0,
                "salary": 500.0,
            }
        }

        line_item_metadata = [
            {"name": "revenue", "category": "income"},
            {"name": "salary", "category": "expenses"},
        ]

        # Should raise error when year is missing and category has line items
        with pytest.raises(ValueError, match="Year 2024 not found in value matrix"):
            category_total("income", value_matrix, 2024, line_item_metadata)

        # Should also raise error for empty category when year is missing
        with pytest.raises(ValueError, match="Year 2024 not found in value matrix"):
            category_total("nonexistent", value_matrix, 2024, line_item_metadata)

    def test_category_total_missing_line_items_in_matrix(self):
        """Test category total with line items missing from value matrix."""
        value_matrix = {
            2024: {
                "revenue": 1000.0,
                # salary is missing from matrix
            }
        }

        line_item_metadata = [
            {"name": "revenue", "category": "income"},
            {"name": "salary", "category": "expenses"},
        ]

        # Should raise error when line item exists in metadata but not in value matrix
        with pytest.raises(
            ValueError,
            match=(
                "Line item 'salary' with category 'expenses' "
                "not found in value matrix for year 2024"
            ),
        ):
            category_total("expenses", value_matrix, 2024, line_item_metadata)

        # Should work fine for category with all items present
        result = category_total("income", value_matrix, 2024, line_item_metadata)
        assert result == 1000.0

    def test_category_total_metadata_without_category(self):
        """Test category total with metadata missing category field."""
        value_matrix = {
            2024: {
                "revenue": 1000.0,
                "salary": 500.0,
            }
        }

        line_item_metadata = [
            {"name": "revenue", "category": "income"},
            {"name": "salary"},  # Missing category field
        ]

        result = category_total("income", value_matrix, 2024, line_item_metadata)
        assert result == 1000.0

    def test_category_total_metadata_without_name(self):
        """Test category total with metadata missing name field."""
        value_matrix = {
            2024: {
                "revenue": 1000.0,
                "salary": 500.0,
            }
        }

        line_item_metadata = [
            {"name": "revenue", "category": "income"},
            {"category": "expenses"},  # Missing name field
        ]

        result = category_total("expenses", value_matrix, 2024, line_item_metadata)
        assert result == 0.0  # None name doesn't match anything

    def test_category_total_error_propagation_in_evaluate(self):
        """Test that category_total errors propagate correctly through evaluate."""
        value_matrix = {
            2024: {
                "revenue": 1000.0,
                # salary is missing
            }
        }

        line_item_metadata = [
            {"name": "revenue", "category": "income"},
            {"name": "salary", "category": "expenses"},
        ]

        # Error should propagate through evaluate function
        formula = 'category_total("expenses")'
        with pytest.raises(
            ValueError,
            match=(
                "Error evaluating formula.*Line item 'salary' with category "
                "'expenses' not found in value matrix for year 2024"
            ),
        ):
            evaluate(formula, value_matrix, 2024, line_item_metadata)

    def test_category_total_mixed_value_types(self):
        """Test category total with mixed numeric types."""
        value_matrix = {
            2024: {
                "revenue": 1000,  # int
                "bonus": 500.5,  # float
                "other": 99.5,  # float
            }
        }

        line_item_metadata = [
            {"name": "revenue", "category": "income"},
            {"name": "bonus", "category": "income"},
            {"name": "other", "category": "income"},
        ]

        result = category_total("income", value_matrix, 2024, line_item_metadata)
        assert result == 1600.0  # 1000 + 500.5 + 99.5


class TestEvaluateWithCategoryTotal:
    """Test the evaluate function with category_total usage in formulas."""

    def test_evaluate_category_total_basic(self):
        """Test evaluate with basic category_total usage."""
        value_matrix = {
            2024: {
                "revenue": 1000.0,
                "salary": 500.0,
                "rent": 200.0,
            }
        }

        line_item_metadata = [
            {"name": "revenue", "category": "income"},
            {"name": "salary", "category": "expenses"},
            {"name": "rent", "category": "expenses"},
        ]

        formula = 'category_total("income")'
        result = evaluate(formula, value_matrix, 2024, line_item_metadata)
        assert result == 1000.0

    def test_evaluate_category_total_in_expression(self):
        """Test evaluate with category_total in mathematical expression."""
        value_matrix = {
            2024: {
                "revenue": 1000.0,
                "salary": 500.0,
                "rent": 200.0,
            }
        }

        line_item_metadata = [
            {"name": "revenue", "category": "income"},
            {"name": "salary", "category": "expenses"},
            {"name": "rent", "category": "expenses"},
        ]

        # Test profit calculation: income - expenses
        formula = 'category_total("income") - category_total("expenses")'
        result = evaluate(formula, value_matrix, 2024, line_item_metadata)
        assert result == 300.0  # 1000 - 700

    def test_evaluate_category_total_with_constants(self):
        """Test evaluate with category_total mixed with constants."""
        value_matrix = {
            2024: {
                "revenue": 1000.0,
                "salary": 500.0,
            }
        }

        line_item_metadata = [
            {"name": "revenue", "category": "income"},
            {"name": "salary", "category": "expenses"},
        ]

        formula = 'category_total("income") * 0.1'
        result = evaluate(formula, value_matrix, 2024, line_item_metadata)
        assert result == 100.0  # 1000 * 0.1

    def test_evaluate_category_total_with_variables(self):
        """Test evaluate with category_total mixed with variables."""
        value_matrix = {
            2024: {
                "revenue": 1000.0,
                "salary": 500.0,
                "tax_rate": 0.2,
            }
        }

        line_item_metadata = [
            {"name": "revenue", "category": "income"},
            {"name": "salary", "category": "expenses"},
            {"name": "tax_rate", "category": "other"},
        ]

        formula = 'category_total("income") * tax_rate'
        result = evaluate(formula, value_matrix, 2024, line_item_metadata)
        assert result == 200.0  # 1000 * 0.2

    def test_evaluate_category_total_invalid_argument_count(self):
        """Test evaluate with category_total having wrong number of arguments."""
        value_matrix = {2024: {"revenue": 1000.0}}
        line_item_metadata = [{"name": "revenue", "category": "income"}]

        # Too many arguments
        formula = 'category_total("income", "extra")'
        with pytest.raises(
            ValueError, match="category_total expects exactly 1 argument"
        ):
            evaluate(formula, value_matrix, 2024, line_item_metadata)

        # No arguments
        formula = "category_total()"
        with pytest.raises(
            ValueError, match="category_total expects exactly 1 argument"
        ):
            evaluate(formula, value_matrix, 2024, line_item_metadata)

    def test_evaluate_category_total_non_string_argument(self):
        """Test evaluate with category_total having non-string argument."""
        value_matrix = {2024: {"revenue": 1000.0}}
        line_item_metadata = [{"name": "revenue", "category": "income"}]

        formula = "category_total(123)"
        with pytest.raises(
            ValueError, match="category_total expects a string category name"
        ):
            evaluate(formula, value_matrix, 2024, line_item_metadata)

    def test_evaluate_unsupported_function(self):
        """Test evaluate with unsupported function call."""
        value_matrix = {2024: {"revenue": 1000.0}}
        line_item_metadata = [{"name": "revenue", "category": "income"}]

        formula = 'unsupported_function("test")'
        with pytest.raises(
            ValueError, match="Unsupported function: unsupported_function"
        ):
            evaluate(formula, value_matrix, 2024, line_item_metadata)

    def test_evaluate_category_total_no_metadata(self):
        """Test evaluate with category_total when line_item_metadata is None."""
        value_matrix = {2024: {"revenue": 1000.0}}

        formula = 'category_total("income")'
        result = evaluate(formula, value_matrix, 2024, None)
        assert result == 0.0  # Should return 0.0 when no metadata provided

    def test_evaluate_complex_formula_with_category_total(self):
        """Test evaluate with complex formula using category_total."""
        value_matrix = {
            2024: {
                "revenue": 1000.0,
                "cost_of_goods": 300.0,
                "salary": 200.0,
                "rent": 100.0,
                "tax_rate": 0.25,
            }
        }

        line_item_metadata = [
            {"name": "revenue", "category": "income"},
            {"name": "cost_of_goods", "category": "cogs"},
            {"name": "salary", "category": "operating_expenses"},
            {"name": "rent", "category": "operating_expenses"},
            {"name": "tax_rate", "category": "other"},
        ]

        # Calculate: (income - cogs - operating_expenses) * (1 - tax_rate)
        formula = (
            '(category_total("income") - category_total("cogs") - '
            'category_total("operating_expenses")) * (1 - tax_rate)'
        )
        result = evaluate(formula, value_matrix, 2024, line_item_metadata)
        expected = (1000 - 300 - 300) * (1 - 0.25)  # 400 * 0.75 = 300
        assert result == expected
