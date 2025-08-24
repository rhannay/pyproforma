import pytest
from pyproforma import LineItem, Model, Category, Constraint
from pyproforma.models.model.model_update import UpdateNamespace


class TestUpdateConstraintMethods:
    """Test constraint management methods in UpdateNamespace."""

    @pytest.fixture
    def sample_model(self):
        """Create a sample model for testing."""
        revenue = LineItem(
            name="revenue",
            category="income",
            values={2023: 100000, 2024: 120000, 2025: 140000}
        )
        
        expenses = LineItem(
            name="expenses", 
            category="costs",
            values={2023: 60000, 2024: 65000, 2025: 70000}
        )
        
        categories = [
            Category(name="income", label="Income", include_total=True),
            Category(name="costs", label="Costs", include_total=True)
        ]
        
        return Model(
            line_items=[revenue, expenses],
            years=[2023, 2024, 2025],
            categories=categories
        )

    @pytest.fixture
    def sample_constraint(self):
        """Create a sample constraint for testing."""
        return Constraint(
            name="min_revenue",
            line_item_name="revenue",
            target=50000.0,
            operator="ge",
            label="Minimum Revenue"
        )

    # ============================================================================
    # ADD CONSTRAINT TESTS
    # ============================================================================

    def test_add_constraint_with_constraint_object(self, sample_model: Model, sample_constraint: Constraint):
        """Test adding a constraint using a Constraint object."""
        initial_count = len(sample_model.constraints)
        
        sample_model.update.add_constraint(sample_constraint)
        
        assert len(sample_model.constraints) == initial_count + 1
        assert sample_model.constraints[-1].name == "min_revenue"
        assert sample_model.constraints[-1].line_item_name == "revenue"
        assert sample_model.constraints[-1].target == 50000.0
        assert sample_model.constraints[-1].operator == "ge"

    def test_add_constraint_with_parameters(self, sample_model: Model):
        """Test adding a constraint using parameters."""
        initial_count = len(sample_model.constraints)
        
        sample_model.update.add_constraint(
            name="max_expenses",
            line_item_name="expenses",
            target=80000.0,
            operator="le",
            tolerance=100.0,
            label="Maximum Expenses"
        )
        
        assert len(sample_model.constraints) == initial_count + 1
        constraint = sample_model.constraints[-1]
        assert constraint.name == "max_expenses"
        assert constraint.line_item_name == "expenses"
        assert constraint.target == 80000.0
        assert constraint.operator == "le"
        assert constraint.tolerance == 100.0
        assert constraint.label == "Maximum Expenses"

    def test_add_constraint_minimal_parameters(self, sample_model: Model):
        """Test adding a constraint with minimal required parameters."""
        sample_model.update.add_constraint(
            name="test_constraint",
            line_item_name="revenue",
            target=1000.0,
            operator="eq"
        )
        
        constraint = sample_model.constraints[-1]
        assert constraint.name == "test_constraint"
        assert constraint.tolerance == 0.0  # Default value
        assert constraint.label == "test_constraint"  # Should default to name

    def test_add_constraint_missing_parameters_raises_error(self, sample_model: Model):
        """Test that missing required parameters raise ValueError."""
        with pytest.raises(ValueError, match="name, line_item_name, target, and operator are required"):
            sample_model.update.add_constraint(name="test")  # Missing other required params

    def test_add_constraint_duplicate_name_raises_error(self, sample_model: Model, sample_constraint: Constraint):
        """Test that adding a constraint with duplicate name raises error."""
        sample_model.update.add_constraint(sample_constraint)
        
        with pytest.raises(ValueError, match="already exists"):
            sample_model.update.add_constraint(sample_constraint)

    def test_add_constraint_invalid_line_item_raises_error(self, sample_model: Model):
        """Test that constraint with invalid line item name raises error."""
        with pytest.raises(ValueError, match="Failed to add constraint"):
            sample_model.update.add_constraint(
                name="invalid_constraint",
                line_item_name="nonexistent_item",
                target=1000.0,
                operator="eq"
            )

    # ============================================================================
    # UPDATE CONSTRAINT TESTS
    # ============================================================================

    def test_update_constraint_with_constraint_object(self, sample_model: Model, sample_constraint: Constraint):
        """Test updating a constraint using a complete Constraint object."""
        sample_model.update.add_constraint(sample_constraint)
        
        new_constraint = Constraint(
            name="updated_revenue",
            line_item_name="revenue", 
            target=75000.0,
            operator="gt"
        )
        
        sample_model.update.update_constraint("min_revenue", constraint=new_constraint)
        
        updated = sample_model.constraints[0]
        assert updated.name == "updated_revenue"
        assert updated.target == 75000.0
        assert updated.operator == "gt"

    def test_update_constraint_with_parameters(self, sample_model: Model, sample_constraint: Constraint):
        """Test updating specific parameters of a constraint."""
        sample_model.update.add_constraint(sample_constraint)
        
        sample_model.update.update_constraint(
            "min_revenue",
            target=60000.0,
            operator="gt",
            tolerance=500.0
        )
        
        updated = sample_model.constraints[0]
        assert updated.name == "min_revenue"  # Should remain unchanged
        assert updated.line_item_name == "revenue"  # Should remain unchanged  
        assert updated.target == 60000.0  # Should be updated
        assert updated.operator == "gt"  # Should be updated
        assert updated.tolerance == 500.0  # Should be updated

    def test_update_constraint_rename(self, sample_model: Model, sample_constraint: Constraint):
        """Test renaming a constraint."""
        sample_model.update.add_constraint(sample_constraint)
        
        sample_model.update.update_constraint(
            "min_revenue",
            new_name="revenue_minimum"
        )
        
        updated = sample_model.constraints[0]
        assert updated.name == "revenue_minimum"
        assert updated.target == 50000.0  # Other properties should remain unchanged

    def test_update_constraint_not_found_raises_error(self, sample_model: Model):
        """Test that updating non-existent constraint raises KeyError."""
        with pytest.raises(KeyError, match="Constraint 'nonexistent' not found"):
            sample_model.update.update_constraint(
                "nonexistent",
                target=1000.0
            )

    def test_update_constraint_name_conflict_raises_error(self, sample_model: Model):
        """Test that renaming constraint to existing name raises error."""
        sample_model.update.add_constraint(
            name="constraint1",
            line_item_name="revenue",
            target=1000.0,
            operator="eq"
        )
        sample_model.update.add_constraint(
            name="constraint2", 
            line_item_name="revenue",
            target=2000.0,
            operator="eq"
        )
        
        with pytest.raises(ValueError, match="already exists"):
            sample_model.update.update_constraint(
                "constraint1",
                new_name="constraint2"
            )

    def test_update_constraint_invalid_line_item_raises_error(self, sample_model: Model, sample_constraint: Constraint):
        """Test that updating constraint with invalid line item raises error."""
        sample_model.update.add_constraint(sample_constraint)
        
        with pytest.raises(ValueError, match="Failed to update constraint"):
            sample_model.update.update_constraint(
                "min_revenue",
                line_item_name="nonexistent_item"
            )

    # ============================================================================
    # DELETE CONSTRAINT TESTS  
    # ============================================================================

    def test_delete_constraint_success(self, sample_model: Model, sample_constraint: Constraint):
        """Test successfully deleting a constraint."""
        sample_model.update.add_constraint(sample_constraint)
        initial_count = len(sample_model.constraints)
        
        sample_model.update.delete_constraint("min_revenue")
        
        assert len(sample_model.constraints) == initial_count - 1
        constraint_names = [c.name for c in sample_model.constraints]
        assert "min_revenue" not in constraint_names

    def test_delete_constraint_not_found_raises_error(self, sample_model: Model):
        """Test that deleting non-existent constraint raises KeyError."""
        with pytest.raises(KeyError, match="Constraint 'nonexistent' not found"):
            sample_model.update.delete_constraint("nonexistent")

    def test_delete_multiple_constraints(self, sample_model: Model):
        """Test deleting multiple constraints."""
        # Add multiple constraints
        sample_model.update.add_constraint(
            name="constraint1",
            line_item_name="revenue",
            target=1000.0,
            operator="eq"
        )
        sample_model.update.add_constraint(
            name="constraint2",
            line_item_name="expenses", 
            target=2000.0,
            operator="eq"
        )
        
        assert len(sample_model.constraints) == 2
        
        # Delete them one by one
        sample_model.update.delete_constraint("constraint1")
        assert len(sample_model.constraints) == 1
        
        sample_model.update.delete_constraint("constraint2")
        assert len(sample_model.constraints) == 0

    # ============================================================================
    # INTEGRATION TESTS
    # ============================================================================

    def test_constraint_methods_preserve_model_integrity(self, sample_model: Model):
        """Test that constraint operations preserve model integrity."""
        # Get initial model state
        initial_value_matrix = sample_model._value_matrix.copy()
        initial_line_items = len(sample_model._line_item_definitions)
        initial_categories = len(sample_model._category_definitions)
        
        # Add constraint
        sample_model.update.add_constraint(
            name="test_constraint",
            line_item_name="revenue",
            target=50000.0,
            operator="ge"
        )
        
        # Verify model integrity is preserved
        assert len(sample_model._line_item_definitions) == initial_line_items
        assert len(sample_model._category_definitions) == initial_categories  
        assert sample_model._value_matrix == initial_value_matrix
        
        # Update constraint
        sample_model.update.update_constraint(
            "test_constraint",
            target=60000.0
        )
        
        # Verify model integrity is still preserved
        assert len(sample_model._line_item_definitions) == initial_line_items
        assert len(sample_model._category_definitions) == initial_categories
        assert sample_model._value_matrix == initial_value_matrix
        
        # Delete constraint
        sample_model.update.delete_constraint("test_constraint")
        
        # Verify model is back to initial state
        assert len(sample_model._line_item_definitions) == initial_line_items
        assert len(sample_model._category_definitions) == initial_categories
        assert sample_model._value_matrix == initial_value_matrix
        assert len(sample_model.constraints) == 0

    def test_constraint_methods_work_with_existing_constraints(self, sample_model: Model):
        """Test that constraint methods work when model already has constraints."""
        # Add initial constraint directly
        initial_constraint = Constraint(
            name="initial_constraint",
            line_item_name="revenue",
            target=30000.0,
            operator="gt"
        )
        sample_model.constraints.append(initial_constraint)
        sample_model._recalculate()
        
        # Add another constraint via update method
        sample_model.update.add_constraint(
            name="added_constraint",
            line_item_name="expenses",
            target=70000.0,
            operator="le"  
        )
        
        assert len(sample_model.constraints) == 2
        
        # Update existing constraint
        sample_model.update.update_constraint(
            "initial_constraint",
            target=35000.0
        )
        
        updated = sample_model.constraint_definition("initial_constraint")
        assert updated.target == 35000.0
        
        # Delete one constraint
        sample_model.update.delete_constraint("added_constraint")
        
        assert len(sample_model.constraints) == 1
        assert sample_model.constraints[0].name == "initial_constraint"

    def test_error_messages_are_informative(self, sample_model: Model):
        """Test that error messages provide helpful information."""
        # Test add constraint with existing name
        sample_model.update.add_constraint(
            name="test_constraint",
            line_item_name="revenue", 
            target=1000.0,
            operator="eq"
        )
        
        with pytest.raises(ValueError) as exc_info:
            sample_model.update.add_constraint(
                name="test_constraint",
                line_item_name="revenue",
                target=2000.0, 
                operator="eq"
            )
        assert "already exists" in str(exc_info.value)
        
        # Test update non-existent constraint  
        with pytest.raises(KeyError) as exc_info:
            sample_model.update.update_constraint("nonexistent", target=1000.0)
        assert "not found" in str(exc_info.value)
        assert "Available constraints:" in str(exc_info.value)
        
        # Test delete non-existent constraint
        with pytest.raises(KeyError) as exc_info:
            sample_model.update.delete_constraint("nonexistent")
        assert "not found" in str(exc_info.value)
        assert "Available constraints:" in str(exc_info.value)