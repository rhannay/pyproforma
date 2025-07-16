import pytest
from unittest.mock import Mock, patch
from pyproforma import LineItem, Model, Category
from pyproforma.models.constraint import Constraint
from pyproforma.models.results import ConstraintResults


# Module-level fixtures available to all test classes
@pytest.fixture
def basic_line_items():
    """Create basic line items for testing."""
    return [
        LineItem(
            name="revenue",
            category="income",
            values={2023: 100000, 2024: 120000, 2025: 140000}
        ),
        LineItem(
            name="expenses",
            category="costs",
            values={2023: 50000, 2024: 60000, 2025: 70000}
        )
    ]


@pytest.fixture
def basic_categories():
    """Create basic categories for testing."""
    return [
        Category(name="income", label="Income"),
        Category(name="costs", label="Costs")
    ]


@pytest.fixture
def basic_constraints():
    """Create basic constraints for testing."""
    return [
        Constraint(
            name="min_revenue",
            line_item_name="revenue",
            target=80000.0,
            operator="gt",
            label="Minimum Revenue"
        ),
        Constraint(
            name="max_expenses",
            line_item_name="expenses",
            target=75000.0,
            operator="lt",
            label="Maximum Expenses"
        ),
        Constraint(
            name="revenue_growth",
            line_item_name="revenue",
            target={2023: 95000.0, 2024: 115000.0, 2025: 135000.0},
            operator="ge",
            label="Revenue Growth Target"
        )
    ]


@pytest.fixture
def model_with_constraints(basic_line_items, basic_categories, basic_constraints):
    """Create a model with constraints for testing."""
    return Model(
        line_items=basic_line_items,
        years=[2023, 2024, 2025],
        categories=basic_categories,
        constraints=basic_constraints
    )


class TestConstraintResultsInitialization:
    """Test ConstraintResults initialization and basic properties."""
    
    def test_init_valid_constraint(self, model_with_constraints):
        """Test ConstraintResults initialization with valid constraint."""
        constraint_results = ConstraintResults(model_with_constraints, "min_revenue")
        
        assert constraint_results.model is model_with_constraints
        assert constraint_results.constraint_name == "min_revenue"
        assert constraint_results.constraint_definition.name == "min_revenue"
        assert constraint_results.constraint_definition.line_item_name == "revenue"
        assert constraint_results.constraint_definition.target == 80000.0
        assert constraint_results.constraint_definition.operator == "gt"
    
    def test_init_invalid_constraint_name(self, model_with_constraints):
        """Test ConstraintResults initialization with invalid constraint name."""
        with pytest.raises(KeyError, match="Constraint with name 'nonexistent' not found"):
            ConstraintResults(model_with_constraints, "nonexistent")
    
    def test_init_constraint_with_dict_target(self, model_with_constraints):
        """Test ConstraintResults initialization with constraint having dict target."""
        constraint_results = ConstraintResults(model_with_constraints, "revenue_growth")
        
        assert constraint_results.constraint_name == "revenue_growth"
        assert constraint_results.constraint_definition.target == {2023: 95000.0, 2024: 115000.0, 2025: 135000.0}
        assert constraint_results.constraint_definition.operator == "ge"


class TestConstraintResultsStringRepresentation:
    """Test string representation methods of ConstraintResults."""
    
    @pytest.fixture
    def constraint_results(self, model_with_constraints):
        """Create a ConstraintResults instance for testing."""
        return ConstraintResults(model_with_constraints, "min_revenue")
    
    def test_str_method(self, constraint_results):
        """Test __str__ method returns summary."""
        str_result = str(constraint_results)
        
        assert "ConstraintResults('min_revenue')" in str_result
        assert "Label: Minimum Revenue" in str_result
        assert "Value (2023):" in str_result
        
    def test_repr_method(self, constraint_results):
        """Test __repr__ method returns expected format."""
        repr_result = repr(constraint_results)
        
        assert repr_result == "ConstraintResults(constraint_name='min_revenue')"
    
    def test_summary_method(self, constraint_results):
        """Test summary method returns formatted constraint information."""
        summary = constraint_results.summary()
        
        assert "ConstraintResults('min_revenue')" in summary
        assert "Label: Minimum Revenue" in summary
        assert "Value (2023): 100,000.00" in summary
    
    def test_summary_with_no_years_raises_error(self, basic_line_items, basic_categories, basic_constraints):
        """Test that creating a Model with no years raises ValueError."""
        # Model should raise ValueError when years is empty
        with pytest.raises(ValueError, match="Years cannot be an empty list"):
            Model(
                line_items=basic_line_items,
                years=[],
                categories=basic_categories,
                constraints=basic_constraints
            )


class TestConstraintResultsTableMethod:
    """Test table method of ConstraintResults."""
    
    @pytest.fixture
    def constraint_results(self, model_with_constraints):
        """Create a ConstraintResults instance for testing."""
        return ConstraintResults(model_with_constraints, "min_revenue")
    
    def test_table_method_returns_table(self, constraint_results):
        """Test table method returns a Table object."""
        with patch('pyproforma.tables.tables.Tables.constraint') as mock_constraint:
            mock_table = Mock()
            mock_constraint.return_value = mock_table
            
            result = constraint_results.table()
            
            mock_constraint.assert_called_once_with("min_revenue")
            assert result is mock_table
    
    def test_table_method_passes_constraint_name(self, constraint_results):
        """Test table method passes correct constraint name."""
        with patch('pyproforma.tables.tables.Tables.constraint') as mock_constraint:
            constraint_results.table()
            mock_constraint.assert_called_once_with("min_revenue")


class TestConstraintResultsChartMethod:
    """Test chart method of ConstraintResults."""
    
    @pytest.fixture
    def constraint_results(self, model_with_constraints):
        """Create a ConstraintResults instance for testing."""
        return ConstraintResults(model_with_constraints, "min_revenue")
    
    def test_chart_method_default_parameters(self, constraint_results):
        """Test chart method with default parameters."""
        with patch('pyproforma.charts.charts.Charts.constraint') as mock_constraint:
            mock_fig = Mock()
            mock_constraint.return_value = mock_fig
            
            result = constraint_results.chart()
            
            mock_constraint.assert_called_once_with(
                "min_revenue",
                width=800,
                height=600,
                template='plotly_white',
                line_item_type='bar',
                constraint_type='line'
            )
            assert result is mock_fig
    
    def test_chart_method_custom_parameters(self, constraint_results):
        """Test chart method with custom parameters."""
        with patch('pyproforma.charts.charts.Charts.constraint') as mock_constraint:
            mock_fig = Mock()
            mock_constraint.return_value = mock_fig
            
            result = constraint_results.chart(
                width=1000,
                height=800,
                template='plotly_dark',
                line_item_type='line',
                constraint_type='bar'
            )
            
            mock_constraint.assert_called_once_with(
                "min_revenue",
                width=1000,
                height=800,
                template='plotly_dark',
                line_item_type='line',
                constraint_type='bar'
            )
            assert result is mock_fig
    
    def test_chart_method_passes_constraint_name(self, constraint_results):
        """Test chart method passes correct constraint name."""
        with patch('pyproforma.charts.charts.Charts.constraint') as mock_constraint:
            constraint_results.chart()
            mock_constraint.assert_called_once_with(
                "min_revenue",
                width=800,
                height=600,
                template='plotly_white',
                line_item_type='bar',
                constraint_type='line'
            )


class TestConstraintResultsLineItemValueMethod:
    """Test line_item_value method of ConstraintResults."""
    
    @pytest.fixture
    def constraint_results(self, model_with_constraints):
        """Create a ConstraintResults instance for testing."""
        return ConstraintResults(model_with_constraints, "min_revenue")
    
    @pytest.fixture
    def constraint_results_expenses(self, model_with_constraints):
        """Create a ConstraintResults instance for expenses constraint."""
        return ConstraintResults(model_with_constraints, "max_expenses")
    
    def test_line_item_value_method_returns_correct_values(self, constraint_results):
        """Test line_item_value method returns correct values for each year."""
        # The "min_revenue" constraint is linked to the "revenue" line item
        # Revenue values from fixture: {2023: 100000, 2024: 120000, 2025: 140000}
        assert constraint_results.line_item_value(2023) == 100000
        assert constraint_results.line_item_value(2024) == 120000
        assert constraint_results.line_item_value(2025) == 140000
    
    def test_line_item_value_method_for_expenses_constraint(self, constraint_results_expenses):
        """Test line_item_value method for expenses constraint."""
        # The "max_expenses" constraint is linked to the "expenses" line item
        # Expenses values from fixture: {2023: 50000, 2024: 60000, 2025: 70000}
        assert constraint_results_expenses.line_item_value(2023) == 50000
        assert constraint_results_expenses.line_item_value(2024) == 60000
        assert constraint_results_expenses.line_item_value(2025) == 70000
    
    def test_line_item_value_method_calls_model_get_value(self, constraint_results):
        """Test that line_item_value method calls model.get_value with correct parameters."""
        with patch.object(constraint_results.model, 'get_value') as mock_get_value:
            mock_get_value.return_value = 100000.0
            
            result = constraint_results.line_item_value(2023)
            
            mock_get_value.assert_called_once_with("revenue", 2023)
            assert result == 100000.0
    
    def test_line_item_value_method_propagates_key_error(self, constraint_results):
        """Test that line_item_value method propagates KeyError from model.get_value."""
        with patch.object(constraint_results.model, 'get_value') as mock_get_value:
            mock_get_value.side_effect = KeyError("Year 2026 not found")
            
            with pytest.raises(KeyError, match="Year 2026 not found"):
                constraint_results.line_item_value(2026)
    
    def test_line_item_value_method_uses_correct_line_item_name(self, constraint_results):
        """Test that line_item_value method uses the correct line item name from constraint."""
        # Verify the constraint is set up correctly
        assert constraint_results.line_item_name == "revenue"
        
        # Mock the model.get_value to verify it's called with the right line item name
        with patch.object(constraint_results.model, 'get_value') as mock_get_value:
            mock_get_value.return_value = 100000.0
            
            constraint_results.line_item_value(2023)
            
            # Verify it was called with the constraint's line_item_name
            mock_get_value.assert_called_once_with(constraint_results.line_item_name, 2023)


class TestConstraintResultsTargetMethod:
    """Test target method of ConstraintResults."""
    
    @pytest.fixture
    def constraint_results(self, model_with_constraints):
        """Create a ConstraintResults instance for testing."""
        return ConstraintResults(model_with_constraints, "min_revenue")
    
    @pytest.fixture
    def constraint_results_with_dict_target(self, model_with_constraints):
        """Create a ConstraintResults instance with dict target for testing."""
        return ConstraintResults(model_with_constraints, "revenue_growth")
    
    def test_target_method_with_float_target(self, constraint_results):
        """Test target method with constraint having float target."""
        # The "min_revenue" constraint has a float target of 80000.0
        result = constraint_results.target(2023)
        assert result == 80000.0
        
        # Should return same value for any year when target is a float
        result = constraint_results.target(2024)
        assert result == 80000.0
        
        result = constraint_results.target(2025)
        assert result == 80000.0
    
    def test_target_method_with_dict_target(self, constraint_results_with_dict_target):
        """Test target method with constraint having dict target."""
        # The "revenue_growth" constraint has dict target: {2023: 95000.0, 2024: 115000.0, 2025: 135000.0}
        result = constraint_results_with_dict_target.target(2023)
        assert result == 95000.0
        
        result = constraint_results_with_dict_target.target(2024)
        assert result == 115000.0
        
        result = constraint_results_with_dict_target.target(2025)
        assert result == 135000.0
    
    def test_target_method_with_dict_target_missing_year(self, constraint_results_with_dict_target):
        """Test target method with dict target for year not in dict."""
        # The "revenue_growth" constraint doesn't have a target for 2026
        result = constraint_results_with_dict_target.target(2026)
        assert result is None
    
    def test_target_method_calls_constraint_definition(self, constraint_results):
        """Test that target method calls get_target on constraint definition."""
        with patch.object(constraint_results.constraint_definition, 'get_target') as mock_get_target:
            mock_get_target.return_value = 80000.0
            
            result = constraint_results.target(2023)
            
            mock_get_target.assert_called_once_with(2023)
            assert result == 80000.0
    
    def test_target_method_propagates_exceptions(self, constraint_results):
        """Test that target method propagates exceptions from constraint definition."""
        with patch.object(constraint_results.constraint_definition, 'get_target') as mock_get_target:
            mock_get_target.side_effect = ValueError("Custom error")
            
            with pytest.raises(ValueError, match="Custom error"):
                constraint_results.target(2023)
    
    def test_target_method_with_custom_constraint(self, basic_line_items, basic_categories):
        """Test target method with a custom constraint having specific target."""
        # Create a constraint with specific target value
        constraint_custom = Constraint(
            name="test_constraint",
            line_item_name="revenue",
            target=90000.0,
            operator="gt",
            label="Test Constraint"
        )
        
        model = Model(
            line_items=basic_line_items,
            years=[2023, 2024, 2025],
            categories=basic_categories,
            constraints=[constraint_custom]
        )
        
        constraint_results = ConstraintResults(model, "test_constraint")
        result = constraint_results.target(2023)
        assert result == 90000.0


class TestConstraintResultsHtmlRepr:
    """Test _repr_html_ method for Jupyter notebook integration."""
    
    @pytest.fixture
    def constraint_results(self, model_with_constraints):
        """Create a ConstraintResults instance for testing."""
        return ConstraintResults(model_with_constraints, "min_revenue")
    
    def test_repr_html_method(self, constraint_results):
        """Test _repr_html_ method returns HTML formatted summary."""
        html_result = constraint_results._repr_html_()
        
        assert html_result.startswith('<pre>')
        assert html_result.endswith('</pre>')
        assert "ConstraintResults('min_revenue')" in html_result
        assert "Label: Minimum Revenue" in html_result
        assert '<br>' in html_result  # Newlines converted to HTML breaks
    
    def test_repr_html_converts_newlines(self, constraint_results):
        """Test _repr_html_ method converts newlines to HTML breaks."""
        html_result = constraint_results._repr_html_()
        
        # Should not contain literal newlines
        assert '\n' not in html_result
        # Should contain HTML line breaks
        assert '<br>' in html_result


class TestConstraintResultsWithDifferentConstraintTypes:
    """Test ConstraintResults with different constraint configurations."""
    
    @pytest.fixture
    def model_with_tolerance_constraint(self, basic_line_items, basic_categories):
        """Create a model with a constraint that has tolerance."""
        constraint = Constraint(
            name="balance_check",
            line_item_name="revenue",
            target=100000.0,
            operator="eq",
            tolerance=0.01,
            label="Balance Check"
        )
        return Model(
            line_items=basic_line_items,
            years=[2023, 2024, 2025],
            categories=basic_categories,
            constraints=[constraint]
        )
    
    @pytest.fixture
    def model_with_no_label_constraint(self, basic_line_items, basic_categories):
        """Create a model with a constraint that has no label."""
        constraint = Constraint(
            name="no_label_constraint",
            line_item_name="revenue",
            target=100000.0,
            operator="eq"
        )
        return Model(
            line_items=basic_line_items,
            years=[2023, 2024, 2025],
            categories=basic_categories,
            constraints=[constraint]
        )
    
    def test_constraint_with_tolerance(self, model_with_tolerance_constraint):
        """Test ConstraintResults with a constraint that has tolerance."""
        constraint_results = ConstraintResults(model_with_tolerance_constraint, "balance_check")
        
        assert constraint_results.constraint_definition.tolerance == 0.01
        assert constraint_results.constraint_definition.operator == "eq"
        
        # Test that methods still work
        summary = constraint_results.summary()
        assert "ConstraintResults('balance_check')" in summary
        assert "Label: Balance Check" in summary
    
    def test_constraint_with_no_label(self, model_with_no_label_constraint):
        """Test ConstraintResults with a constraint that has no label."""
        constraint_results = ConstraintResults(model_with_no_label_constraint, "no_label_constraint")
        
        # Should use name as label when no label is provided
        summary = constraint_results.summary()
        assert "ConstraintResults('no_label_constraint')" in summary
        assert "Label: no_label_constraint" in summary
    
    def test_constraint_with_dict_target_summary(self, model_with_constraints):
        """Test ConstraintResults summary with dict target constraint."""
        constraint_results = ConstraintResults(model_with_constraints, "revenue_growth")
        
        summary = constraint_results.summary()
        assert "ConstraintResults('revenue_growth')" in summary
        assert "Label: Revenue Growth Target" in summary
        assert "Value (2023): 100,000.00" in summary


class TestConstraintResultsErrorHandling:
    """Test error handling in ConstraintResults."""
    
    @pytest.fixture
    def model_with_constraints(self, basic_line_items, basic_categories, basic_constraints):
        """Create a model with constraints for testing."""
        return Model(
            line_items=basic_line_items,
            years=[2023, 2024, 2025],
            categories=basic_categories,
            constraints=basic_constraints
        )
    
    def test_summary_handles_missing_value(self, model_with_constraints):
        """Test summary method handles missing constraint value gracefully."""
        constraint_results = ConstraintResults(model_with_constraints, "min_revenue")
        
        # Mock get_value to raise KeyError
        with patch.object(constraint_results.model, 'get_value', side_effect=KeyError):
            summary = constraint_results.summary()
            
            assert "ConstraintResults('min_revenue')" in summary
            assert "Label: Minimum Revenue" in summary
            assert "Value: Not available" in summary
    
    def test_chart_method_with_chart_error(self, model_with_constraints):
        """Test chart method when underlying chart method raises error."""
        constraint_results = ConstraintResults(model_with_constraints, "min_revenue")
        
        with patch('pyproforma.charts.charts.Charts.constraint', side_effect=KeyError("Chart error")):
            with pytest.raises(KeyError, match="Chart error"):
                constraint_results.chart()
    
    def test_table_method_with_table_error(self, model_with_constraints):
        """Test table method when underlying table method raises error."""
        constraint_results = ConstraintResults(model_with_constraints, "min_revenue")
        
        with patch('pyproforma.tables.tables.Tables.constraint', side_effect=KeyError("Table error")):
            with pytest.raises(KeyError, match="Table error"):
                constraint_results.table()


class TestConstraintResultsIntegration:
    """Test ConstraintResults integration with actual model methods."""
    
    @pytest.fixture
    def integrated_model(self):
        """Create a fully integrated model for testing."""
        line_items = [
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
        
        categories = [
            Category(name="income", label="Income"),
            Category(name="costs", label="Costs")
        ]
        
        constraints = [
            Constraint(
                name="profit_margin",
                line_item_name="revenue",
                target=90000.0,
                operator="gt",
                label="Minimum Profit Margin"
            )
        ]
        
        return Model(
            line_items=line_items,
            years=[2023, 2024],
            categories=categories,
            constraints=constraints
        )
    
    def test_constraint_results_from_model_method(self, integrated_model):
        """Test creating ConstraintResults through model.constraint() method."""
        constraint_results = integrated_model.constraint("profit_margin")
        
        assert isinstance(constraint_results, ConstraintResults)
        assert constraint_results.constraint_name == "profit_margin"
        assert constraint_results.model is integrated_model
        
        # Test that methods work
        summary = constraint_results.summary()
        assert "ConstraintResults('profit_margin')" in summary
        assert "Label: Minimum Profit Margin" in summary
    
    def test_constraint_results_string_representation_integration(self, integrated_model):
        """Test string representation with real model data."""
        constraint_results = integrated_model.constraint("profit_margin")
        
        str_result = str(constraint_results)
        assert "ConstraintResults('profit_margin')" in str_result
        assert "Label: Minimum Profit Margin" in str_result
        assert "Value (2023): 100,000.00" in str_result
    
    def test_constraint_results_html_representation_integration(self, integrated_model):
        """Test HTML representation with real model data."""
        constraint_results = integrated_model.constraint("profit_margin")
        
        html_result = constraint_results._repr_html_()
        assert "<pre>" in html_result
        assert "</pre>" in html_result
        assert "ConstraintResults('profit_margin')" in html_result
        assert "Label: Minimum Profit Margin" in html_result
        assert "<br>" in html_result


class TestConstraintResultsEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_constraint_results_with_empty_model_years_raises_error(self):
        """Test that creating a Model with empty years raises ValueError."""
        line_items = [
            LineItem(
                name="revenue",
                category="income",
                values={}
            )
        ]
        
        categories = [Category(name="income", label="Income")]
        
        constraints = [
            Constraint(
                name="test_constraint",
                line_item_name="revenue",
                target=100000.0,
                operator="gt"
            )
        ]
        
        # Model should raise ValueError when years is empty
        with pytest.raises(ValueError, match="Years cannot be an empty list"):
            Model(
                line_items=line_items,
                years=[],
                categories=categories,
                constraints=constraints
            )
    
    def test_constraint_results_with_special_characters_in_name(self):
        """Test ConstraintResults with constraint names containing special characters."""
        line_items = [
            LineItem(
                name="revenue_2024",
                category="income",
                values={2024: 100000}
            )
        ]
        
        categories = [Category(name="income", label="Income")]
        
        constraints = [
            Constraint(
                name="revenue_check_2024",
                line_item_name="revenue_2024",
                target=90000.0,
                operator="gt",
                label="Revenue Check 2024"
            )
        ]
        
        model = Model(
            line_items=line_items,
            years=[2024],
            categories=categories,
            constraints=constraints
        )
        
        constraint_results = ConstraintResults(model, "revenue_check_2024")
        
        assert constraint_results.constraint_name == "revenue_check_2024"
        summary = constraint_results.summary()
        assert "ConstraintResults('revenue_check_2024')" in summary
        assert "Label: Revenue Check 2024" in summary
        assert "Value (2024): 100,000.00" in summary