import pytest

from pyproforma.models.results.constraint_results import _evaluate_constraint


class TestEvaluateConstraint:
    """Test cases for the _evaluate_constraint function."""

    def test_eq_operator_within_tolerance(self):
        """Test equality operator when value is within tolerance."""
        assert _evaluate_constraint(
            value=100.0, target_value=102.0, operator="eq", tolerance=5.0
        )

    def test_eq_operator_outside_tolerance(self):
        """Test equality operator when value is outside tolerance."""
        assert not _evaluate_constraint(
            value=100.0, target_value=110.0, operator="eq", tolerance=5.0
        )

    def test_eq_operator_exact_match(self):
        """Test equality operator when value exactly matches target."""
        assert _evaluate_constraint(
            value=100.0, target_value=100.0, operator="eq", tolerance=0.0
        )

    def test_eq_operator_at_tolerance_boundary(self):
        """Test equality operator at tolerance boundary."""
        # Exactly at tolerance should pass
        assert _evaluate_constraint(
            value=100.0, target_value=105.0, operator="eq", tolerance=5.0
        )
        # Just outside tolerance should fail
        assert not _evaluate_constraint(
            value=100.0, target_value=105.1, operator="eq", tolerance=5.0
        )

    def test_lt_operator_true(self):
        """Test less than operator when condition is true."""
        assert _evaluate_constraint(
            value=90.0, target_value=100.0, operator="lt", tolerance=5.0
        )

    def test_lt_operator_false(self):
        """Test less than operator when condition is false."""
        assert not _evaluate_constraint(
            value=100.0, target_value=100.0, operator="lt", tolerance=5.0
        )

    def test_lt_operator_with_tolerance(self):
        """Test less than operator considers tolerance."""
        # value < target_value - tolerance
        # 90 < 100 - 5 = 95, so should be true
        assert _evaluate_constraint(
            value=90.0, target_value=100.0, operator="lt", tolerance=5.0
        )
        # 96 < 100 - 5 = 95, so should be false
        assert not _evaluate_constraint(
            value=96.0, target_value=100.0, operator="lt", tolerance=5.0
        )

    def test_le_operator_true(self):
        """Test less than or equal operator when condition is true."""
        assert _evaluate_constraint(
            value=100.0, target_value=100.0, operator="le", tolerance=5.0
        )

    def test_le_operator_false(self):
        """Test less than or equal operator when condition is false."""
        assert not _evaluate_constraint(
            value=110.0, target_value=100.0, operator="le", tolerance=5.0
        )

    def test_le_operator_with_tolerance(self):
        """Test less than or equal operator considers tolerance."""
        # value <= target_value + tolerance
        # 105 <= 100 + 5 = 105, so should be true
        assert _evaluate_constraint(
            value=105.0, target_value=100.0, operator="le", tolerance=5.0
        )
        # 106 <= 100 + 5 = 105, so should be false
        assert not _evaluate_constraint(
            value=106.0, target_value=100.0, operator="le", tolerance=5.0
        )

    def test_gt_operator_true(self):
        """Test greater than operator when condition is true."""
        assert _evaluate_constraint(
            value=110.0, target_value=100.0, operator="gt", tolerance=5.0
        )

    def test_gt_operator_false(self):
        """Test greater than operator when condition is false."""
        assert not _evaluate_constraint(
            value=100.0, target_value=100.0, operator="gt", tolerance=5.0
        )

    def test_gt_operator_with_tolerance(self):
        """Test greater than operator considers tolerance."""
        # value > target_value + tolerance
        # 110 > 100 + 5 = 105, so should be true
        assert _evaluate_constraint(
            value=110.0, target_value=100.0, operator="gt", tolerance=5.0
        )
        # 104 > 100 + 5 = 105, so should be false
        assert not _evaluate_constraint(
            value=104.0, target_value=100.0, operator="gt", tolerance=5.0
        )

    def test_ge_operator_true(self):
        """Test greater than or equal operator when condition is true."""
        assert _evaluate_constraint(
            value=100.0, target_value=100.0, operator="ge", tolerance=5.0
        )

    def test_ge_operator_false(self):
        """Test greater than or equal operator when condition is false."""
        assert not _evaluate_constraint(
            value=90.0, target_value=100.0, operator="ge", tolerance=5.0
        )

    def test_ge_operator_with_tolerance(self):
        """Test greater than or equal operator considers tolerance."""
        # value >= target_value - tolerance
        # 95 >= 100 - 5 = 95, so should be true
        assert _evaluate_constraint(
            value=95.0, target_value=100.0, operator="ge", tolerance=5.0
        )
        # 94 >= 100 - 5 = 95, so should be false
        assert not _evaluate_constraint(
            value=94.0, target_value=100.0, operator="ge", tolerance=5.0
        )

    def test_ne_operator_true(self):
        """Test not equal operator when condition is true."""
        assert _evaluate_constraint(
            value=90.0, target_value=100.0, operator="ne", tolerance=5.0
        )

    def test_ne_operator_false(self):
        """Test not equal operator when condition is false."""
        assert not _evaluate_constraint(
            value=100.0, target_value=102.0, operator="ne", tolerance=5.0
        )

    def test_ne_operator_with_tolerance(self):
        """Test not equal operator considers tolerance."""
        # abs(value - target_value) > tolerance
        # abs(100 - 110) = 10 > 5, so should be true
        assert _evaluate_constraint(
            value=100.0, target_value=110.0, operator="ne", tolerance=5.0
        )
        # abs(100 - 103) = 3 > 5, so should be false
        assert not _evaluate_constraint(
            value=100.0, target_value=103.0, operator="ne", tolerance=5.0
        )

    def test_unknown_operator_raises_error(self):
        """Test that unknown operator raises ValueError."""
        with pytest.raises(ValueError, match="Unknown operator: unknown"):
            _evaluate_constraint(
                value=100.0, target_value=100.0, operator="unknown", tolerance=5.0
            )

    def test_zero_tolerance(self):
        """Test behavior with zero tolerance."""
        # eq with zero tolerance should require exact match
        assert _evaluate_constraint(
            value=100.0, target_value=100.0, operator="eq", tolerance=0.0
        )
        assert not _evaluate_constraint(
            value=100.0, target_value=100.1, operator="eq", tolerance=0.0
        )

    def test_negative_values(self):
        """Test function works with negative values."""
        assert _evaluate_constraint(
            value=-50.0, target_value=-45.0, operator="lt", tolerance=2.0
        )
        assert _evaluate_constraint(
            value=-50.0, target_value=-50.0, operator="eq", tolerance=1.0
        )

    def test_large_tolerance(self):
        """Test function works with large tolerance values."""
        assert _evaluate_constraint(
            value=100.0, target_value=200.0, operator="eq", tolerance=150.0
        )

    @pytest.mark.parametrize(
        "value,target_value,operator,tolerance,expected",
        [
            # eq operator tests
            (100.0, 100.0, "eq", 0.0, True),
            (100.0, 101.0, "eq", 0.5, False),
            (100.0, 100.5, "eq", 0.5, True),
            # lt operator tests
            (95.0, 100.0, "lt", 0.0, True),
            (100.0, 100.0, "lt", 0.0, False),
            (90.0, 100.0, "lt", 5.0, True),
            # le operator tests
            (100.0, 100.0, "le", 0.0, True),
            (105.0, 100.0, "le", 5.0, True),
            (106.0, 100.0, "le", 5.0, False),
            # gt operator tests
            (105.0, 100.0, "gt", 0.0, True),
            (100.0, 100.0, "gt", 0.0, False),
            (110.0, 100.0, "gt", 5.0, True),
            # ge operator tests
            (100.0, 100.0, "ge", 0.0, True),
            (95.0, 100.0, "ge", 5.0, True),
            (94.0, 100.0, "ge", 5.0, False),
            # ne operator tests
            (90.0, 100.0, "ne", 5.0, True),
            (100.0, 103.0, "ne", 5.0, False),
        ],
    )
    def test_parametrized_cases(
        self, value, target_value, operator, tolerance, expected
    ):
        """Test various combinations of parameters."""
        result = _evaluate_constraint(
            value=value,
            target_value=target_value,
            operator=operator,
            tolerance=tolerance,
        )
        assert result == expected
