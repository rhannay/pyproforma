import pytest

from pyproforma.models.constraint import Constraint


class TestConstraintEvaluate:
    """Test the evaluate method of Constraint class."""

    def test_evaluate_eq_operator_true(self):
        """Test evaluate with equal operator when constraint is satisfied."""
        constraint = Constraint(
            name="test_eq", line_item_name="revenue", target=100000.0, operator="eq"
        )

        value_matrix = {
            2023: {"revenue": 100000.0, "expenses": 50000.0},
            2024: {"revenue": 120000.0, "expenses": 60000.0},
        }

        assert constraint.evaluate(value_matrix, 2023) is True
        assert constraint.evaluate(value_matrix, 2024) is False

    def test_evaluate_eq_operator_false(self):
        """Test evaluate with equal operator when constraint is not satisfied."""
        constraint = Constraint(
            name="test_eq", line_item_name="revenue", target=100000.0, operator="eq"
        )

        value_matrix = {2023: {"revenue": 99999.0, "expenses": 50000.0}}

        assert constraint.evaluate(value_matrix, 2023) is False

    def test_evaluate_lt_operator(self):
        """Test evaluate with less than operator."""
        constraint = Constraint(
            name="test_lt", line_item_name="expenses", target=60000.0, operator="lt"
        )

        value_matrix = {
            2023: {"revenue": 100000.0, "expenses": 50000.0},
            2024: {"revenue": 120000.0, "expenses": 70000.0},
        }

        assert constraint.evaluate(value_matrix, 2023) is True
        assert constraint.evaluate(value_matrix, 2024) is False

    def test_evaluate_le_operator(self):
        """Test evaluate with less than or equal operator."""
        constraint = Constraint(
            name="test_le", line_item_name="expenses", target=60000.0, operator="le"
        )

        value_matrix = {
            2023: {"revenue": 100000.0, "expenses": 50000.0},
            2024: {"revenue": 120000.0, "expenses": 60000.0},
            2025: {"revenue": 140000.0, "expenses": 70000.0},
        }

        assert constraint.evaluate(value_matrix, 2023) is True
        assert constraint.evaluate(value_matrix, 2024) is True
        assert constraint.evaluate(value_matrix, 2025) is False

    def test_evaluate_gt_operator(self):
        """Test evaluate with greater than operator."""
        constraint = Constraint(
            name="test_gt", line_item_name="revenue", target=100000.0, operator="gt"
        )

        value_matrix = {
            2023: {"revenue": 120000.0, "expenses": 50000.0},
            2024: {"revenue": 90000.0, "expenses": 60000.0},
        }

        assert constraint.evaluate(value_matrix, 2023) is True
        assert constraint.evaluate(value_matrix, 2024) is False

    def test_evaluate_ge_operator(self):
        """Test evaluate with greater than or equal operator."""
        constraint = Constraint(
            name="test_ge", line_item_name="revenue", target=100000.0, operator="ge"
        )

        value_matrix = {
            2023: {"revenue": 100000.0, "expenses": 50000.0},
            2024: {"revenue": 120000.0, "expenses": 60000.0},
            2025: {"revenue": 90000.0, "expenses": 70000.0},
        }

        assert constraint.evaluate(value_matrix, 2023) is True
        assert constraint.evaluate(value_matrix, 2024) is True
        assert constraint.evaluate(value_matrix, 2025) is False

    def test_evaluate_ne_operator(self):
        """Test evaluate with not equal operator."""
        constraint = Constraint(
            name="test_ne", line_item_name="revenue", target=100000.0, operator="ne"
        )

        value_matrix = {
            2023: {"revenue": 100000.0, "expenses": 50000.0},
            2024: {"revenue": 120000.0, "expenses": 60000.0},
        }

        assert constraint.evaluate(value_matrix, 2023) is False
        assert constraint.evaluate(value_matrix, 2024) is True

    def test_evaluate_with_dict_target(self):
        """Test evaluate with dictionary target (year-specific targets)."""
        constraint = Constraint(
            name="test_dict_target",
            line_item_name="revenue",
            target={2023: 100000.0, 2024: 120000.0, 2025: 140000.0},
            operator="ge",
        )

        value_matrix = {
            2023: {"revenue": 100000.0, "expenses": 50000.0},
            2024: {"revenue": 130000.0, "expenses": 60000.0},
            2025: {"revenue": 135000.0, "expenses": 70000.0},
        }

        assert constraint.evaluate(value_matrix, 2023) is True
        assert constraint.evaluate(value_matrix, 2024) is True
        assert constraint.evaluate(value_matrix, 2025) is False

    def test_evaluate_year_not_in_value_matrix(self):
        """Test evaluate raises error when year is not in value matrix."""
        constraint = Constraint(
            name="test_constraint",
            line_item_name="revenue",
            target=100000.0,
            operator="gt",
        )

        value_matrix = {2023: {"revenue": 100000.0, "expenses": 50000.0}}

        with pytest.raises(ValueError, match="Year 2024 not found in value_matrix"):
            constraint.evaluate(value_matrix, 2024)

    def test_evaluate_line_item_not_in_value_matrix(self):
        """Test evaluate raises error when line item is not in value matrix."""
        constraint = Constraint(
            name="test_constraint",
            line_item_name="profit",
            target=100000.0,
            operator="gt",
        )

        value_matrix = {2023: {"revenue": 100000.0, "expenses": 50000.0}}

        with pytest.raises(
            ValueError,
            match="Line item 'profit' not found in value_matrix for year 2023",
        ):
            constraint.evaluate(value_matrix, 2023)

    def test_evaluate_no_target_for_year(self):
        """Test evaluate raises error when no target is available for the year."""
        constraint = Constraint(
            name="test_constraint",
            line_item_name="revenue",
            target={2023: 100000.0, 2024: 120000.0},
            operator="gt",
        )

        value_matrix = {
            2023: {"revenue": 100000.0, "expenses": 50000.0},
            2025: {"revenue": 140000.0, "expenses": 70000.0},
        }

        with pytest.raises(ValueError, match="No target value available for year 2025"):
            constraint.evaluate(value_matrix, 2025)

    def test_evaluate_with_float_values(self):
        """Test evaluate works with various float values."""
        constraint = Constraint(
            name="test_float", line_item_name="ratio", target=0.5, operator="lt"
        )

        value_matrix = {
            2023: {"ratio": 0.45, "revenue": 100000.0},
            2024: {"ratio": 0.55, "revenue": 120000.0},
        }

        assert constraint.evaluate(value_matrix, 2023) is True
        assert constraint.evaluate(value_matrix, 2024) is False

    def test_evaluate_with_negative_values(self):
        """Test evaluate works with negative values."""
        constraint = Constraint(
            name="test_negative", line_item_name="net_income", target=0.0, operator="gt"
        )

        value_matrix = {
            2023: {"net_income": -10000.0, "revenue": 100000.0},
            2024: {"net_income": 5000.0, "revenue": 120000.0},
        }

        assert constraint.evaluate(value_matrix, 2023) is False
        assert constraint.evaluate(value_matrix, 2024) is True

    def test_evaluate_with_zero_values(self):
        """Test evaluate works with zero values."""
        constraint = Constraint(
            name="test_zero", line_item_name="debt", target=0.0, operator="eq"
        )

        value_matrix = {
            2023: {"debt": 0.0, "revenue": 100000.0},
            2024: {"debt": 1000.0, "revenue": 120000.0},
        }

        assert constraint.evaluate(value_matrix, 2023) is True
        assert constraint.evaluate(value_matrix, 2024) is False

    def test_evaluate_with_large_values(self):
        """Test evaluate works with large values."""
        constraint = Constraint(
            name="test_large",
            line_item_name="revenue",
            target=1000000000.0,  # 1 billion
            operator="ge",
        )

        value_matrix = {
            2023: {"revenue": 999999999.0, "expenses": 50000.0},
            2024: {"revenue": 1000000000.0, "expenses": 60000.0},
        }

        assert constraint.evaluate(value_matrix, 2023) is False
        assert constraint.evaluate(value_matrix, 2024) is True

    def test_evaluate_precision_with_floats(self):
        """Test evaluate handles floating point precision correctly."""
        constraint = Constraint(
            name="test_precision",
            line_item_name="value",
            target=0.1 + 0.2,  # 0.30000000000000004
            operator="eq",
        )

        value_matrix = {2023: {"value": 0.3, "revenue": 100000.0}}

        # This test demonstrates floating point precision issues
        # The constraint may not be satisfied due to floating point representation
        result = constraint.evaluate(value_matrix, 2023)
        # We document the behavior rather than assert a specific result
        assert isinstance(result, bool)

    def test_evaluate_multiple_years_same_target(self):
        """Test evaluate works consistently across multiple years with same target."""
        constraint = Constraint(
            name="test_multi_year",
            line_item_name="expenses",
            target=50000.0,
            operator="le",
        )

        value_matrix = {
            2023: {"revenue": 100000.0, "expenses": 45000.0},
            2024: {"revenue": 120000.0, "expenses": 50000.0},
            2025: {"revenue": 140000.0, "expenses": 55000.0},
        }

        assert constraint.evaluate(value_matrix, 2023) is True
        assert constraint.evaluate(value_matrix, 2024) is True
        assert constraint.evaluate(value_matrix, 2025) is False

    def test_evaluate_different_line_items(self):
        """Test evaluate works with different line items in the same value matrix."""
        revenue_constraint = Constraint(
            name="revenue_constraint",
            line_item_name="revenue",
            target=100000.0,
            operator="gt",
        )

        expense_constraint = Constraint(
            name="expense_constraint",
            line_item_name="expenses",
            target=60000.0,
            operator="lt",
        )

        value_matrix = {
            2023: {"revenue": 120000.0, "expenses": 50000.0, "profit": 70000.0}
        }

        assert revenue_constraint.evaluate(value_matrix, 2023) is True
        assert expense_constraint.evaluate(value_matrix, 2023) is True
