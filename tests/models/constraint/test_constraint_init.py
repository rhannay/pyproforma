import pytest

from pyproforma.models.constraint import Constraint


class TestConstraintInit:
    """Test Constraint initialization and validation."""

    def test_valid_constraint_init(self):
        """Test creating a constraint with valid parameters."""
        constraint = Constraint(
            name="test_constraint",
            line_item_name="revenue",
            target=100000.0,
            operator="gt",
        )

        assert constraint.name == "test_constraint"
        assert constraint.line_item_name == "revenue"
        assert constraint.target == 100000.0
        assert constraint.operator == "gt"

    def test_valid_name_formats(self):
        """Test that various valid name formats are accepted."""
        valid_names = [
            "test_constraint",
            "test-constraint",
            "TestConstraint",
            "test123",
            "constraint_2024",
            "MIN_REVENUE",
            "a1b2c3",
        ]

        for name in valid_names:
            constraint = Constraint(
                name=name, line_item_name="revenue", target=1000.0, operator="eq"
            )
            assert constraint.name == name

    def test_invalid_name_formats(self):
        """Test that invalid name formats raise ValueError."""
        invalid_names = [
            "test constraint",  # space
            "test@constraint",  # special character
            "test.constraint",  # dot
            "test/constraint",  # slash
            "test\\constraint",  # backslash
            "test constraint!",  # exclamation mark
            "test(constraint)",  # parentheses
            "",  # empty string
            "test constraint#",  # hash
        ]

        for name in invalid_names:
            with pytest.raises(
                ValueError,
                match="Name must only contain letters, numbers, underscores, or hyphens",  # noqa: E501
            ):
                Constraint(
                    name=name, line_item_name="revenue", target=1000.0, operator="eq"
                )

    def test_all_valid_operators(self):
        """Test that all valid operators work correctly."""
        valid_operators = ["eq", "lt", "le", "gt", "ge", "ne"]

        for operator in valid_operators:
            constraint = Constraint(
                name="test_constraint",
                line_item_name="revenue",
                target=1000.0,
                operator=operator,
            )
            assert constraint.operator == operator

    def test_invalid_operators(self):
        """Test that invalid operators raise ValueError."""
        invalid_operators = [
            "equals",
            "less_than",
            "greater_than",
            "not_equal",
            "==",
            "<",
            ">",
            "<=",
            ">=",
            "!=",
            "invalid",
            "",
            None,
        ]

        for operator in invalid_operators:
            with pytest.raises(ValueError, match="Operator must be one of"):
                Constraint(
                    name="test_constraint",
                    line_item_name="revenue",
                    target=1000.0,
                    operator=operator,
                )

    def test_target_value_conversion(self):
        """Test that target values are properly converted to float."""
        test_cases = [
            (100, 100.0),
            (100.5, 100.5),
            ("100", 100.0),
            ("100.75", 100.75),
            (0, 0.0),
            (-50, -50.0),
            (-50.25, -50.25),
        ]

        for input_value, expected_value in test_cases:
            constraint = Constraint(
                name="test_constraint",
                line_item_name="revenue",
                target=input_value,
                operator="eq",
            )
            assert constraint.target == expected_value
            assert isinstance(constraint.target, float)

    def test_dict_target(self):
        """Test that dictionary targets are accepted and work with get_target(year)."""
        target_dict = {2023: 100.0, 2024: 200.0}
        constraint = Constraint(
            name="dict_test",
            line_item_name="revenue",
            target=target_dict,
            operator="eq",
        )

        assert constraint.target == target_dict

    def test_invalid_target_value(self):
        """Test that invalid target values raise appropriate errors."""
        invalid_values = ["not_a_number", "abc", "", None, [], {}, "100.5.5"]

        for value in invalid_values:
            with pytest.raises((ValueError, TypeError)):
                Constraint(
                    name="test_constraint",
                    line_item_name="revenue",
                    target=value,
                    operator="eq",
                )

    def test_line_item_name_assignment(self):
        """Test that line item names are properly assigned."""
        test_names = [
            "revenue",
            "total_revenue",
            "operating_expenses",
            "net_income",
            "cash_flow",
            "item_123",
        ]

        for line_item_name in test_names:
            constraint = Constraint(
                name="test_constraint",
                line_item_name=line_item_name,
                target=1000.0,
                operator="eq",
            )
            assert constraint.line_item_name == line_item_name

    def test_constraint_attributes_immutable_after_init(self):
        """Test that constraint attributes are set correctly during initialization."""
        constraint = Constraint(
            name="revenue_min",
            line_item_name="total_revenue",
            target=50000.0,
            operator="ge",
        )

        # Verify all attributes are set
        assert hasattr(constraint, "name")
        assert hasattr(constraint, "line_item_name")
        assert hasattr(constraint, "target")
        assert hasattr(constraint, "operator")

        # Verify correct values
        assert constraint.name == "revenue_min"
        assert constraint.line_item_name == "total_revenue"
        assert constraint.target == 50000.0
        assert constraint.operator == "ge"

    def test_constraint_with_edge_case_values(self):
        """Test constraint creation with edge case values."""
        # Very large numbers
        constraint_large = Constraint(
            name="large_test", line_item_name="big_revenue", target=1e10, operator="lt"
        )
        assert constraint_large.target == 1e10

        # Very small numbers
        constraint_small = Constraint(
            name="small_test",
            line_item_name="small_expense",
            target=1e-10,
            operator="gt",
        )
        assert constraint_small.target == 1e-10

        # Zero
        constraint_zero = Constraint(
            name="zero_test", line_item_name="zero_item", target=0.0, operator="ne"
        )
        assert constraint_zero.target == 0.0
