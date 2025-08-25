import pytest

from pyproforma.models.constraint import Constraint


class TestConstraintTolerance:
    """Test tolerance functionality in Constraint class."""

    def test_tolerance_eq_within_tolerance(self):
        """Test eq operator with tolerance - values within tolerance should pass."""
        constraint = Constraint(
            name="test_tolerance_eq",
            line_item_name="revenue",
            target=100000.0,
            operator="eq",
            tolerance=0.01,  # 1 cent tolerance
        )

        value_matrix = {
            2023: {"revenue": 100000.005, "expenses": 50000.0},  # Within tolerance
            2024: {"revenue": 99999.995, "expenses": 60000.0},  # Within tolerance
        }

        assert constraint.evaluate(value_matrix, 2023) is True
        assert constraint.evaluate(value_matrix, 2024) is True

    def test_tolerance_eq_outside_tolerance(self):
        """Test eq operator with tolerance - values outside tolerance should fail."""
        constraint = Constraint(
            name="test_tolerance_eq",
            line_item_name="revenue",
            target=100000.0,
            operator="eq",
            tolerance=0.01,  # 1 cent tolerance
        )

        value_matrix = {
            2023: {"revenue": 100000.02, "expenses": 50000.0},  # Outside tolerance
            2024: {"revenue": 99999.98, "expenses": 60000.0},  # Outside tolerance
        }

        assert constraint.evaluate(value_matrix, 2023) is False
        assert constraint.evaluate(value_matrix, 2024) is False

    def test_tolerance_ne_within_tolerance(self):
        """Test ne operator with tolerance - values within tolerance should fail."""
        constraint = Constraint(
            name="test_tolerance_ne",
            line_item_name="revenue",
            target=100000.0,
            operator="ne",
            tolerance=0.01,  # 1 cent tolerance
        )

        value_matrix = {
            2023: {"revenue": 100000.005, "expenses": 50000.0},  # Within tolerance
            2024: {"revenue": 99999.995, "expenses": 60000.0},  # Within tolerance
        }

        assert constraint.evaluate(value_matrix, 2023) is False
        assert constraint.evaluate(value_matrix, 2024) is False

    def test_tolerance_ne_outside_tolerance(self):
        """Test ne operator with tolerance - values outside tolerance should pass."""
        constraint = Constraint(
            name="test_tolerance_ne",
            line_item_name="revenue",
            target=100000.0,
            operator="ne",
            tolerance=0.01,  # 1 cent tolerance
        )

        value_matrix = {
            2023: {"revenue": 100000.02, "expenses": 50000.0},  # Outside tolerance
            2024: {"revenue": 99999.98, "expenses": 60000.0},  # Outside tolerance
        }

        assert constraint.evaluate(value_matrix, 2023) is True
        assert constraint.evaluate(value_matrix, 2024) is True

    def test_tolerance_lt_with_buffer(self):
        """Test lt operator with tolerance - creates a buffer zone."""
        constraint = Constraint(
            name="test_tolerance_lt",
            line_item_name="expenses",
            target=100000.0,
            operator="lt",
            tolerance=1000.0,  # $1000 buffer
        )

        value_matrix = {
            2023: {
                "revenue": 150000.0,
                "expenses": 98000.0,
            },  # < target - tolerance (99000)
            2024: {
                "revenue": 150000.0,
                "expenses": 99500.0,
            },  # > target - tolerance (99000)
            2025: {"revenue": 150000.0, "expenses": 100000.0},  # = target
        }

        assert constraint.evaluate(value_matrix, 2023) is True
        assert constraint.evaluate(value_matrix, 2024) is False
        assert constraint.evaluate(value_matrix, 2025) is False

    def test_tolerance_le_with_buffer(self):
        """Test le operator with tolerance - extends acceptable range."""
        constraint = Constraint(
            name="test_tolerance_le",
            line_item_name="expenses",
            target=100000.0,
            operator="le",
            tolerance=1000.0,  # $1000 buffer
        )

        value_matrix = {
            2023: {"revenue": 150000.0, "expenses": 100000.0},  # = target
            2024: {"revenue": 150000.0, "expenses": 101000.0},  # = target + tolerance
            2025: {"revenue": 150000.0, "expenses": 101500.0},  # > target + tolerance
        }

        assert constraint.evaluate(value_matrix, 2023) is True
        assert constraint.evaluate(value_matrix, 2024) is True
        assert constraint.evaluate(value_matrix, 2025) is False

    def test_tolerance_gt_with_buffer(self):
        """Test gt operator with tolerance - creates a buffer zone."""
        constraint = Constraint(
            name="test_tolerance_gt",
            line_item_name="revenue",
            target=100000.0,
            operator="gt",
            tolerance=1000.0,  # $1000 buffer
        )

        value_matrix = {
            2023: {
                "revenue": 102000.0,
                "expenses": 50000.0,
            },  # > target + tolerance (101000)
            2024: {
                "revenue": 100500.0,
                "expenses": 60000.0,
            },  # < target + tolerance (101000)
            2025: {"revenue": 100000.0, "expenses": 70000.0},  # = target
        }

        assert constraint.evaluate(value_matrix, 2023) is True
        assert constraint.evaluate(value_matrix, 2024) is False
        assert constraint.evaluate(value_matrix, 2025) is False

    def test_tolerance_ge_with_buffer(self):
        """Test ge operator with tolerance - extends acceptable range."""
        constraint = Constraint(
            name="test_tolerance_ge",
            line_item_name="revenue",
            target=100000.0,
            operator="ge",
            tolerance=1000.0,  # $1000 buffer
        )

        value_matrix = {
            2023: {"revenue": 99000.0, "expenses": 50000.0},  # = target - tolerance
            2024: {"revenue": 99500.0, "expenses": 60000.0},  # > target - tolerance
            2025: {"revenue": 98500.0, "expenses": 70000.0},  # < target - tolerance
        }

        assert constraint.evaluate(value_matrix, 2023) is True
        assert constraint.evaluate(value_matrix, 2024) is True
        assert constraint.evaluate(value_matrix, 2025) is False

    def test_tolerance_zero_default(self):
        """Test that tolerance defaults to 0.0 and behaves like exact comparison."""
        constraint = Constraint(
            name="test_zero_tolerance",
            line_item_name="revenue",
            target=100000.0,
            operator="eq",
            # tolerance defaults to 0.0
        )

        value_matrix = {
            2023: {"revenue": 100000.0, "expenses": 50000.0},  # Exactly equal
            2024: {"revenue": 100000.01, "expenses": 60000.0},  # Slightly different
        }

        assert constraint.tolerance == 0.0
        assert constraint.evaluate(value_matrix, 2023) is True
        assert constraint.evaluate(value_matrix, 2024) is False

    def test_tolerance_validation_negative(self):
        """Test that negative tolerance raises ValueError."""
        with pytest.raises(ValueError, match="Tolerance must be non-negative"):
            Constraint(
                name="test_negative_tolerance",
                line_item_name="revenue",
                target=100000.0,
                operator="eq",
                tolerance=-0.01,
            )

    def test_tolerance_floating_point_precision(self):
        """Test tolerance with floating point precision issues."""
        constraint = Constraint(
            name="test_fp_tolerance",
            line_item_name="ratio",
            target=0.3,  # 0.1 + 0.2 = 0.30000000000000004
            operator="eq",
            tolerance=1e-10,  # Very small tolerance
        )

        value_matrix = {2023: {"ratio": 0.1 + 0.2, "revenue": 100000.0}}

        # With tolerance, this should pass despite floating point precision
        assert constraint.evaluate(value_matrix, 2023) is True

    def test_tolerance_with_dict_target(self):
        """Test tolerance works with dictionary targets."""
        constraint = Constraint(
            name="test_dict_tolerance",
            line_item_name="revenue",
            target={2023: 100000.0, 2024: 120000.0},
            operator="eq",
            tolerance=100.0,  # $100 tolerance
        )

        value_matrix = {
            2023: {"revenue": 100050.0, "expenses": 50000.0},  # Within tolerance
            2024: {"revenue": 120150.0, "expenses": 60000.0},  # Outside tolerance
        }

        assert constraint.evaluate(value_matrix, 2023) is True
        assert constraint.evaluate(value_matrix, 2024) is False

    def test_tolerance_serialization(self):
        """Test that tolerance is properly serialized and deserialized."""
        constraint = Constraint(
            name="test_serialize",
            line_item_name="revenue",
            target=100000.0,
            operator="eq",
            tolerance=0.01,
        )

        # Convert to dict and back
        constraint_dict = constraint.to_dict()
        assert constraint_dict["tolerance"] == 0.01

        restored_constraint = Constraint.from_dict(constraint_dict)
        assert restored_constraint.tolerance == 0.01
        assert restored_constraint.name == constraint.name
        assert restored_constraint.line_item_name == constraint.line_item_name
        assert restored_constraint.target == constraint.target
        assert restored_constraint.operator == constraint.operator

    def test_tolerance_backward_compatibility(self):
        """Test that old constraint dicts without tolerance still work."""
        constraint_dict = {
            "name": "test_backward_compat",
            "line_item_name": "revenue",
            "target": 100000.0,
            "operator": "eq",
            # No tolerance key
        }

        constraint = Constraint.from_dict(constraint_dict)
        assert constraint.tolerance == 0.0  # Should default to 0.0

    def test_tolerance_large_values(self):
        """Test tolerance with large values."""
        constraint = Constraint(
            name="test_large_tolerance",
            line_item_name="revenue",
            target=1000000000.0,  # 1 billion
            operator="eq",
            tolerance=1000.0,  # $1000 tolerance
        )

        value_matrix = {
            2023: {"revenue": 1000000500.0, "expenses": 50000.0},  # Within tolerance
            2024: {"revenue": 1000001500.0, "expenses": 60000.0},  # Outside tolerance
        }

        assert constraint.evaluate(value_matrix, 2023) is True
        assert constraint.evaluate(value_matrix, 2024) is False
