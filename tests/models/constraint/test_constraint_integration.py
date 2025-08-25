import pytest

from pyproforma import Category, LineItem, Model
from pyproforma.models.constraint import Constraint


class TestConstraintSerialization:
    """Test that constraints are properly serialized and deserialized."""

    @pytest.fixture
    def sample_model_with_constraints(self) -> Model:
        """Create a sample model with constraints for testing."""
        line_items = [
            LineItem(
                name="revenue", category="income", values={2023: 100000, 2024: 120000}
            ),
            LineItem(
                name="expenses", category="costs", values={2023: 50000, 2024: 60000}
            ),
        ]

        categories = [
            Category(name="income", label="Income"),
            Category(name="costs", label="Costs"),
        ]

        constraints = [
            Constraint(
                name="min_revenue",
                line_item_name="revenue",
                target=80000.0,
                operator="gt",
            ),
            Constraint(
                name="max_expenses",
                line_item_name="expenses",
                target=70000.0,
                operator="le",
            ),
        ]

        return Model(
            line_items=line_items,
            years=[2023, 2024],
            categories=categories,
            constraints=constraints,
        )

    def test_to_dict_includes_constraints(self, sample_model_with_constraints: Model):
        """Test that to_dict includes constraints in the output."""
        model_dict = sample_model_with_constraints.to_dict()

        assert "constraints" in model_dict
        assert len(model_dict["constraints"]) == 2

        # Check first constraint
        constraint1 = model_dict["constraints"][0]
        assert constraint1["name"] == "min_revenue"
        assert constraint1["line_item_name"] == "revenue"
        assert constraint1["target"] == 80000.0
        assert constraint1["operator"] == "gt"

        # Check second constraint
        constraint2 = model_dict["constraints"][1]
        assert constraint2["name"] == "max_expenses"
        assert constraint2["line_item_name"] == "expenses"
        assert constraint2["target"] == 70000.0
        assert constraint2["operator"] == "le"

    def test_from_dict_reconstructs_constraints(
        self, sample_model_with_constraints: Model
    ):
        """Test that from_dict properly reconstructs constraints."""
        model_dict = sample_model_with_constraints.to_dict()
        reconstructed_model = Model.from_dict(model_dict)

        assert len(reconstructed_model.constraints) == 2

        # Check first constraint
        constraint1 = reconstructed_model.constraints[0]
        assert constraint1.name == "min_revenue"
        assert constraint1.line_item_name == "revenue"
        assert constraint1.target == 80000.0
        assert constraint1.operator == "gt"

        # Check second constraint
        constraint2 = reconstructed_model.constraints[1]
        assert constraint2.name == "max_expenses"
        assert constraint2.line_item_name == "expenses"
        assert constraint2.target == 70000.0
        assert constraint2.operator == "le"

    def test_to_yaml_includes_constraints(self, sample_model_with_constraints: Model):
        """Test that to_yaml includes constraints in the output."""
        yaml_str = sample_model_with_constraints.to_yaml()

        assert "constraints:" in yaml_str
        assert "min_revenue" in yaml_str
        assert "max_expenses" in yaml_str
        assert "line_item_name: revenue" in yaml_str
        assert "target: 80000.0" in yaml_str
        assert "operator: gt" in yaml_str

    def test_to_yaml_returns_none_when_file_path_provided(
        self, sample_model_with_constraints: Model
    ):
        """Test that to_yaml returns None when file_path is provided."""
        import os
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            temp_path = f.name

        try:
            # Test that it returns None when file path is provided
            result = sample_model_with_constraints.to_yaml(temp_path)
            assert result is None

            # Test that the file was still written correctly
            with open(temp_path, "r") as f:
                file_content = f.read()

            assert len(file_content) > 0
            assert "constraints:" in file_content
            assert "min_revenue" in file_content
            assert "max_expenses" in file_content

        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_from_yaml_reconstructs_constraints(
        self, sample_model_with_constraints: Model
    ):
        """Test that from_yaml properly reconstructs constraints."""
        yaml_str = sample_model_with_constraints.to_yaml()
        reconstructed_model = Model.from_yaml(yaml_str=yaml_str)

        assert len(reconstructed_model.constraints) == 2

        # Check that constraints are properly reconstructed
        constraint_names = [c.name for c in reconstructed_model.constraints]
        assert "min_revenue" in constraint_names
        assert "max_expenses" in constraint_names

    def test_to_json_includes_constraints(self, sample_model_with_constraints: Model):
        """Test that to_json includes constraints in the output."""
        json_str = sample_model_with_constraints.to_json()

        assert '"constraints":' in json_str
        assert '"min_revenue"' in json_str
        assert '"max_expenses"' in json_str
        assert '"line_item_name": "revenue"' in json_str
        assert '"target": 80000.0' in json_str
        assert '"operator": "gt"' in json_str

    def test_from_json_reconstructs_constraints(
        self, sample_model_with_constraints: Model
    ):
        """Test that from_json properly reconstructs constraints."""
        json_str = sample_model_with_constraints.to_json()
        reconstructed_model = Model.from_json(json_str=json_str)

        assert len(reconstructed_model.constraints) == 2

        # Check that constraints are properly reconstructed
        constraint_names = [c.name for c in reconstructed_model.constraints]
        assert "min_revenue" in constraint_names
        assert "max_expenses" in constraint_names

    def test_to_dict_with_no_constraints(self):
        """Test that to_dict works correctly when there are no constraints."""
        line_items = [
            LineItem(name="revenue", category="income", values={2023: 100000})
        ]

        model = Model(line_items=line_items, years=[2023])

        model_dict = model.to_dict()

        assert "constraints" in model_dict
        assert model_dict["constraints"] == []

    def test_from_dict_with_no_constraints(self):
        """Test that from_dict works correctly when there are no constraints in the dict."""
        model_dict = {
            "years": [2023],
            "line_items": [
                {"name": "revenue", "category": "income", "values": {2023: 100000}}
            ],
            "categories": [{"name": "income", "label": "Income"}],
            "generators": [],
            # Note: no 'constraints' key
        }

        model = Model.from_dict(model_dict)

        assert model.constraints == []
        assert len(model.constraints) == 0


class TestConstraintCopy:
    """Test that constraints are properly copied when using Model.copy()."""

    def test_copy_includes_constraints(self):
        """Test that Model.copy() includes constraints in the copied model."""
        line_items = [
            LineItem(name="revenue", category="income", values={2023: 100000})
        ]

        constraints = [
            Constraint(
                name="min_revenue",
                line_item_name="revenue",
                target=50000.0,
                operator="gt",
            )
        ]

        original_model = Model(
            line_items=line_items, years=[2023], constraints=constraints
        )

        copied_model = original_model.copy()

        # Check that constraints are copied
        assert len(copied_model.constraints) == 1
        assert copied_model.constraints[0].name == "min_revenue"
        assert copied_model.constraints[0].line_item_name == "revenue"
        assert copied_model.constraints[0].target == 50000.0

    def test_copy_constraints_are_independent(self):
        """Test that copied constraints are independent from original."""
        line_items = [
            LineItem(name="revenue", category="income", values={2023: 100000})
        ]

        constraints = [
            Constraint(
                name="min_revenue",
                line_item_name="revenue",
                target=50000.0,
                operator="gt",
            )
        ]

        original_model = Model(
            line_items=line_items, years=[2023], constraints=constraints
        )

        copied_model = original_model.copy()

        # Check that constraints are different objects
        assert original_model.constraints[0] is not copied_model.constraints[0]
        assert original_model.constraints is not copied_model.constraints

        # But they should have the same values
        assert original_model.constraints[0].name == copied_model.constraints[0].name
        assert (
            original_model.constraints[0].target == copied_model.constraints[0].target
        )

    def test_copy_with_no_constraints(self):
        """Test that Model.copy() works correctly when there are no constraints."""
        line_items = [
            LineItem(name="revenue", category="income", values={2023: 100000})
        ]

        original_model = Model(line_items=line_items, years=[2023])

        copied_model = original_model.copy()

        assert copied_model.constraints == []
        assert len(copied_model.constraints) == 0


class TestConstraintValidation:
    """Test constraint validation during model operations."""

    def test_recalculate_validates_constraints(self):
        """Test that _recalculate method validates constraints."""
        line_items = [
            LineItem(name="revenue", category="income", values={2023: 100000})
        ]

        constraints = [
            Constraint(
                name="min_revenue",
                line_item_name="revenue",
                target=50000.0,
                operator="gt",
            )
        ]

        model = Model(line_items=line_items, years=[2023], constraints=constraints)

        # Add a duplicate constraint manually to test validation
        duplicate_constraint = Constraint(
            name="min_revenue",  # Same name
            line_item_name="revenue",
            target=80000.0,
            operator="lt",
        )

        model.constraints.append(duplicate_constraint)

        # This should raise an error when recalculating
        with pytest.raises(ValueError, match="Duplicate constraint names not allowed"):
            model._recalculate()

    def test_constraint_validation_with_empty_list(self):
        """Test that constraint validation works with empty constraint list."""
        line_items = [
            LineItem(name="revenue", category="income", values={2023: 100000})
        ]

        model = Model(line_items=line_items, years=[2023], constraints=[])

        # This should not raise any errors
        model._recalculate()

        assert model.constraints == []


class TestConstraintIntegration:
    """Test integration of constraints with other model functionality."""

    def test_model_functions_normally_with_constraints(self):
        """Test that model functions normally when constraints are present."""
        line_items = [
            LineItem(
                name="revenue", category="income", values={2023: 100000, 2024: 120000}
            ),
            LineItem(
                name="expenses", category="costs", values={2023: 50000, 2024: 60000}
            ),
        ]

        constraints = [
            Constraint(
                name="min_revenue",
                line_item_name="revenue",
                target=80000.0,
                operator="gt",
            ),
            Constraint(
                name="max_expenses",
                line_item_name="expenses",
                target=70000.0,
                operator="le",
            ),
        ]

        model = Model(
            line_items=line_items, years=[2023, 2024], constraints=constraints
        )

        # Test that normal model operations work
        assert model.value("revenue", 2023) == 100000
        assert model.value("expenses", 2024) == 60000
        assert model["revenue", 2023] == 100000
        assert model["expenses", 2024] == 60000

        # Test that category totals work
        assert model.value("total_income", 2023) == 100000
        assert model.value("total_costs", 2024) == 60000

        # Test that constraints are still accessible
        assert len(model.constraints) == 2
        assert model.constraints[0].name == "min_revenue"
        assert model.constraints[1].name == "max_expenses"

    def test_constraints_do_not_interfere_with_defined_names(self):
        """Test that constraints don't interfere with the defined names namespace."""
        line_items = [
            LineItem(name="revenue", category="income", values={2023: 100000})
        ]

        constraints = [
            Constraint(
                name="revenue_constraint",
                line_item_name="revenue",
                target=50000.0,
                operator="gt",
            )
        ]

        model = Model(line_items=line_items, years=[2023], constraints=constraints)

        # Check that defined names doesn't include constraint names
        defined_names = [item["name"] for item in model.line_item_metadata]
        assert "revenue" in defined_names
        assert "total_income" in defined_names
        assert (
            "revenue_constraint" not in defined_names
        )  # Constraints shouldn't be in defined names

        # Check that constraints are still accessible
        assert len(model.constraints) == 1
        assert model.constraints[0].name == "revenue_constraint"
