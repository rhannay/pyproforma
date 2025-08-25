import pytest

from pyproforma import Category, LineItem, Model
from pyproforma.models.constraint import Constraint


class TestModelGetConstraint:
    """Test the get_constraint method of the Model class."""

    @pytest.fixture
    def basic_line_items(self):
        """Create basic line items for testing."""
        return [
            LineItem(
                name="revenue",
                category="income",
                values={2023: 100000, 2024: 120000}
            ),
            LineItem(
                name="expenses",
                category="costs",
                values={2023: 50000, 2024: 60000}
            )
        ]

    @pytest.fixture
    def basic_categories(self):
        """Create basic categories for testing."""
        return [
            Category(name="income", label="Income"),
            Category(name="costs", label="Costs")
        ]

    @pytest.fixture
    def basic_constraints(self):
        """Create basic constraints for testing."""
        return [
            Constraint(
                name="min_revenue",
                line_item_name="revenue",
                target=50000.0,
                operator="gt"
            ),
            Constraint(
                name="max_expenses",
                line_item_name="expenses",
                target=70000.0,
                operator="lt"
            ),
            Constraint(
                name="revenue_growth",
                line_item_name="revenue",
                target={2023: 100000.0, 2024: 110000.0},
                operator="ge"
            )
        ]

    @pytest.fixture
    def model_with_constraints(self, basic_line_items, basic_categories, basic_constraints):
        """Create a model with constraints for testing."""
        return Model(
            line_items=basic_line_items,
            years=[2023, 2024],
            categories=basic_categories,
            constraints=basic_constraints
        )

    def test_get_constraint_valid_name(self, model_with_constraints: Model):
        """Test getting a constraint with a valid name."""
        constraint = model_with_constraints.constraint_definition("min_revenue")

        assert constraint.name == "min_revenue"
        assert constraint.line_item_name == "revenue"
        assert constraint.target == 50000.0
        assert constraint.operator == "gt"

    def test_get_constraint_with_dict_target(self, model_with_constraints: Model):
        """Test getting a constraint with a dictionary target."""
        constraint = model_with_constraints.constraint_definition("revenue_growth")

        assert constraint.name == "revenue_growth"
        assert constraint.line_item_name == "revenue"
        assert constraint.target == {2023: 100000.0, 2024: 110000.0}
        assert constraint.operator == "ge"

    def test_get_constraint_invalid_name(self, model_with_constraints):
        """Test that getting a constraint with invalid name raises KeyError."""
        with pytest.raises(KeyError, match="Constraint with name 'nonexistent' not found"):
            model_with_constraints.constraint_definition("nonexistent")

    def test_get_constraint_error_message_includes_valid_names(self, model_with_constraints):
        """Test that error message includes list of valid constraint names."""
        with pytest.raises(KeyError) as excinfo:
            model_with_constraints.constraint_definition("invalid_constraint")

        error_msg = str(excinfo.value)
        assert "Valid constraint names are:" in error_msg
        assert "min_revenue" in error_msg
        assert "max_expenses" in error_msg
        assert "revenue_growth" in error_msg

    def test_get_constraint_from_model_with_no_constraints(self, basic_line_items, basic_categories):
        """Test getting constraint from model with no constraints."""
        model = Model(
            line_items=basic_line_items,
            years=[2023, 2024],
            categories=basic_categories,
            constraints=[]
        )

        with pytest.raises(KeyError, match="Valid constraint names are: \\[\\]"):
            model.constraint_definition("any_constraint")

    def test_get_constraint_returns_constraint_object(self, model_with_constraints):
        """Test that get_constraint returns actual Constraint object."""
        constraint = model_with_constraints.constraint_definition("max_expenses")

        assert isinstance(constraint, Constraint)
        assert hasattr(constraint, 'evaluate')
        assert hasattr(constraint, 'variance')
        assert hasattr(constraint, 'get_target')

    def test_get_constraint_case_sensitive(self, model_with_constraints):
        """Test that constraint names are case sensitive."""
        # This should work
        constraint = model_with_constraints.constraint_definition("min_revenue")
        assert constraint.name == "min_revenue"

        # This should fail due to case sensitivity
        with pytest.raises(KeyError):
            model_with_constraints.constraint_definition("Min_Revenue")

    def test_get_constraint_whitespace_sensitive(self, model_with_constraints):
        """Test that constraint names are whitespace sensitive."""
        # This should work
        constraint = model_with_constraints.constraint_definition("min_revenue")
        assert constraint.name == "min_revenue"

        # This should fail due to whitespace
        with pytest.raises(KeyError):
            model_with_constraints.constraint_definition(" min_revenue ")

    def test_get_constraint_with_tolerance(self, basic_line_items, basic_categories):
        """Test getting a constraint that has tolerance."""
        constraint_with_tolerance = Constraint(
            name="balance_check",
            line_item_name="revenue",
            target=100000.0,
            operator="eq",
            tolerance=0.01
        )

        model = Model(
            line_items=basic_line_items,
            years=[2023, 2024],
            categories=basic_categories,
            constraints=[constraint_with_tolerance]
        )

        retrieved_constraint = model.constraint_definition("balance_check")
        assert retrieved_constraint.tolerance == 0.01
        assert retrieved_constraint.operator == "eq"
        assert retrieved_constraint.target == 100000.0
