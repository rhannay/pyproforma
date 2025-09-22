from unittest.mock import Mock, patch

import pytest

from pyproforma import Category, LineItem, Model
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
            values={2023: 100000, 2024: 120000, 2025: 140000},
            value_format="two_decimals",
        ),
        LineItem(
            name="expenses",
            category="costs",
            values={2023: 50000, 2024: 60000, 2025: 70000},
            value_format="two_decimals",
        ),
    ]


@pytest.fixture
def basic_categories():
    """Create basic categories for testing."""
    return [
        Category(name="income", label="Income"),
        Category(name="costs", label="Costs"),
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
            label="Minimum Revenue",
        ),
        Constraint(
            name="max_expenses",
            line_item_name="expenses",
            target=75000.0,
            operator="lt",
            label="Maximum Expenses",
        ),
        Constraint(
            name="revenue_growth",
            line_item_name="revenue",
            target={2023: 95000.0, 2024: 115000.0, 2025: 135000.0},
            operator="ge",
            label="Revenue Growth Target",
        ),
    ]


@pytest.fixture
def model_with_constraints(basic_line_items, basic_categories, basic_constraints):
    """Create a model with constraints for testing."""
    return Model(
        line_items=basic_line_items,
        years=[2023, 2024, 2025],
        categories=basic_categories,
        constraints=basic_constraints,
    )


class TestConstraintResultsInitialization:
    """Test ConstraintResults initialization and basic properties."""

    def test_init_valid_constraint(self, model_with_constraints):
        """Test ConstraintResults initialization with valid constraint."""
        constraint_results = ConstraintResults(model_with_constraints, "min_revenue")

        assert constraint_results.model is model_with_constraints
        assert constraint_results.name == "min_revenue"
        assert constraint_results.line_item_name == "revenue"
        assert constraint_results.target(2023) == 80000.0
        assert constraint_results.operator == "gt"

    def test_init_invalid_constraint_name(self, model_with_constraints):
        """Test ConstraintResults initialization with invalid constraint name."""
        with pytest.raises(
            KeyError, match="Constraint with name 'nonexistent' not found"
        ):
            ConstraintResults(model_with_constraints, "nonexistent")

    def test_init_constraint_with_dict_target(self, model_with_constraints):
        """Test ConstraintResults initialization with constraint having dict target."""
        constraint_results = ConstraintResults(model_with_constraints, "revenue_growth")

        assert constraint_results.name == "revenue_growth"
        assert constraint_results.target(2023) == 95000.0
        assert constraint_results.target(2024) == 115000.0
        assert constraint_results.target(2025) == 135000.0
        assert constraint_results.operator == "ge"


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
        assert "Line Item: revenue" in str_result
        assert "Target: > 80,000" in str_result
        assert "Status: All years pass constraint check" in str_result

    def test_repr_method(self, constraint_results):
        """Test __repr__ method returns expected format."""
        repr_result = repr(constraint_results)

        assert repr_result == "ConstraintResults(name='min_revenue')"

    def test_summary_method(self, constraint_results):
        """Test summary method returns formatted constraint information."""
        summary = constraint_results.summary()

        assert "ConstraintResults('min_revenue')" in summary
        assert "Label: Minimum Revenue" in summary
        assert "Value (2023): 100,000.00" in summary

    def test_summary_with_no_years_now_allowed(
        self, basic_line_items, basic_categories, basic_constraints
    ):
        """Test that creating a Model with no years now works."""
        # Model should now work with empty years (creating a template)
        model = Model(
            line_items=basic_line_items,
            years=[],
            categories=basic_categories,
            constraints=basic_constraints,
        )

        # Model should exist but be empty
        assert model.years == []
        assert len(model.line_item_names) > 0

        # ConstraintResults should be accessible
        constraint_result = model.constraint(basic_constraints[0].name)
        assert constraint_result.name == basic_constraints[0].name
        assert constraint_result.failing_years() == []  # No years, no failing years


class TestConstraintResultsTableMethod:
    """Test table method of ConstraintResults."""

    @pytest.fixture
    def constraint_results(self, model_with_constraints):
        """Create a ConstraintResults instance for testing."""
        return ConstraintResults(model_with_constraints, "min_revenue")

    def test_table_method_returns_table(self, constraint_results):
        """Test table method returns a Table object."""
        with patch("pyproforma.tables.tables.Tables.constraint") as mock_constraint:
            mock_table = Mock()
            mock_constraint.return_value = mock_table

            result = constraint_results.table()

            mock_constraint.assert_called_once_with("min_revenue")
            assert result is mock_table

    def test_table_method_passes_constraint_name(self, constraint_results):
        """Test table method passes correct constraint name."""
        with patch("pyproforma.tables.tables.Tables.constraint") as mock_constraint:
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
        with patch("pyproforma.charts.charts.Charts.constraint") as mock_constraint:
            mock_fig = Mock()
            mock_constraint.return_value = mock_fig

            result = constraint_results.chart()

            mock_constraint.assert_called_once_with(
                "min_revenue",
                width=800,
                height=600,
                template="plotly_white",
                line_item_type="bar",
                constraint_type="line",
            )
            assert result is mock_fig

    def test_chart_method_custom_parameters(self, constraint_results):
        """Test chart method with custom parameters."""
        with patch("pyproforma.charts.charts.Charts.constraint") as mock_constraint:
            mock_fig = Mock()
            mock_constraint.return_value = mock_fig

            result = constraint_results.chart(
                width=1000,
                height=800,
                template="plotly_dark",
                line_item_type="line",
                constraint_type="bar",
            )

            mock_constraint.assert_called_once_with(
                "min_revenue",
                width=1000,
                height=800,
                template="plotly_dark",
                line_item_type="line",
                constraint_type="bar",
            )
            assert result is mock_fig

    def test_chart_method_passes_constraint_name(self, constraint_results):
        """Test chart method passes correct constraint name."""
        with patch("pyproforma.charts.charts.Charts.constraint") as mock_constraint:
            constraint_results.chart()
            mock_constraint.assert_called_once_with(
                "min_revenue",
                width=800,
                height=600,
                template="plotly_white",
                line_item_type="bar",
                constraint_type="line",
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

    def test_line_item_value_method_for_expenses_constraint(
        self, constraint_results_expenses
    ):
        """Test line_item_value method for expenses constraint."""
        # The "max_expenses" constraint is linked to the "expenses" line item
        # Expenses values from fixture: {2023: 50000, 2024: 60000, 2025: 70000}
        assert constraint_results_expenses.line_item_value(2023) == 50000
        assert constraint_results_expenses.line_item_value(2024) == 60000
        assert constraint_results_expenses.line_item_value(2025) == 70000

    def test_line_item_value_method_calls_model_value(self, constraint_results):
        """Test that line_item_value method calls model.value with correct parameters."""  # noqa: E501
        with patch.object(constraint_results.model, "value") as mock_value:
            mock_value.return_value = 100000.0

            result = constraint_results.line_item_value(2023)

            mock_value.assert_called_once_with("revenue", 2023)
            assert result == 100000.0

    def test_line_item_value_method_propagates_key_error(self, constraint_results):
        """Test that line_item_value method propagates KeyError from model.value."""
        with patch.object(constraint_results.model, "value") as mock_value:
            mock_value.side_effect = KeyError("Year 2026 not found")

            with pytest.raises(KeyError, match="Year 2026 not found"):
                constraint_results.line_item_value(2026)

    def test_line_item_value_method_uses_correct_line_item_name(
        self, constraint_results
    ):
        """Test that line_item_value method uses the correct line item name from constraint."""  # noqa: E501
        # Verify the constraint is set up correctly
        assert constraint_results.line_item_name == "revenue"

        # Mock the model.value to verify it's called with the right line item name
        with patch.object(constraint_results.model, "value") as mock_value:
            mock_value.return_value = 100000.0

            constraint_results.line_item_value(2023)

            # Verify it was called with the constraint's line_item_name
            mock_value.assert_called_once_with(constraint_results.line_item_name, 2023)


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
        # The "revenue_growth" constraint has dict target: {2023: 95000.0, 2024: 115000.0, 2025: 135000.0}  # noqa: E501
        result = constraint_results_with_dict_target.target(2023)
        assert result == 95000.0

        result = constraint_results_with_dict_target.target(2024)
        assert result == 115000.0

        result = constraint_results_with_dict_target.target(2025)
        assert result == 135000.0

    def test_target_method_with_dict_target_missing_year(
        self, constraint_results_with_dict_target
    ):
        """Test target method with dict target for year not in dict."""
        # The "revenue_growth" constraint doesn't have a target for 2026
        result = constraint_results_with_dict_target.target(2026)
        assert result is None

    def test_target_method_with_custom_constraint(
        self, basic_line_items, basic_categories
    ):
        """Test target method with a custom constraint having specific target."""
        # Create a constraint with specific target value
        constraint_custom = Constraint(
            name="test_constraint",
            line_item_name="revenue",
            target=90000.0,
            operator="gt",
            label="Test Constraint",
        )

        model = Model(
            line_items=basic_line_items,
            years=[2023, 2024, 2025],
            categories=basic_categories,
            constraints=[constraint_custom],
        )

        constraint_results = ConstraintResults(model, "test_constraint")
        result = constraint_results.target(2023)
        assert result == 90000.0


class TestConstraintResultsEvaluateMethod:
    """Test evaluate method of ConstraintResults."""

    @pytest.fixture
    def constraint_results(self, model_with_constraints):
        """Create a ConstraintResults instance for testing."""
        return ConstraintResults(model_with_constraints, "min_revenue")

    @pytest.fixture
    def constraint_results_expenses(self, model_with_constraints):
        """Create a ConstraintResults instance for expenses constraint."""
        return ConstraintResults(model_with_constraints, "max_expenses")

    @pytest.fixture
    def constraint_results_revenue_growth(self, model_with_constraints):
        """Create a ConstraintResults instance for revenue growth constraint."""
        return ConstraintResults(model_with_constraints, "revenue_growth")

    def test_evaluate_method_returns_true_when_constraint_satisfied(
        self, constraint_results
    ):
        """Test evaluate method returns True when constraint is satisfied."""
        # The "min_revenue" constraint is: revenue > 80000
        # Revenue in 2023 is 100000, so 100000 > 80000 should be True
        result = constraint_results.evaluate(2023)
        assert result is True

    def test_evaluate_method_returns_false_when_constraint_not_satisfied(
        self, constraint_results_expenses
    ):
        """Test evaluate method returns False when constraint is not satisfied."""
        # The "max_expenses" constraint is: expenses < 75000
        # Expenses in 2025 is 70000, so 70000 < 75000 should be True
        # But let's test with a different year or modify the test
        result = constraint_results_expenses.evaluate(2025)
        assert result is True  # 70000 < 75000

        # Test with a year where it might not be satisfied
        result = constraint_results_expenses.evaluate(2023)
        assert result is True  # 50000 < 75000

        # All years should pass for this constraint based on fixture values
        for year in [2023, 2024, 2025]:
            result = constraint_results_expenses.evaluate(year)
            assert result is True

    def test_evaluate_method_with_dict_target_constraint(
        self, constraint_results_revenue_growth
    ):
        """Test evaluate method with constraint having dictionary target."""
        # The "revenue_growth" constraint has dict target and operator "ge" (>=)
        # Revenue growth targets: {2023: 95000.0, 2024: 115000.0, 2025: 135000.0}
        # Revenue values: {2023: 100000, 2024: 120000, 2025: 140000}

        # 2023: 100000 >= 95000 should be True
        result = constraint_results_revenue_growth.evaluate(2023)
        assert result is True

        # 2024: 120000 >= 115000 should be True
        result = constraint_results_revenue_growth.evaluate(2024)
        assert result is True

        # 2025: 140000 >= 135000 should be True
        result = constraint_results_revenue_growth.evaluate(2025)
        assert result is True

    def test_evaluate_method_with_invalid_year(self, constraint_results):
        """Test evaluate method with year not in model raises ValueError."""
        # Test with a year that's not in the model
        with pytest.raises(ValueError, match="Year 2026 not found in value_matrix"):
            constraint_results.evaluate(2026)

    def test_evaluate_method_with_custom_constraint(
        self, basic_line_items, basic_categories
    ):
        """Test evaluate method with a custom constraint that fails."""
        # Create a constraint that will fail
        failing_constraint = Constraint(
            name="failing_constraint",
            line_item_name="revenue",
            target=150000.0,  # Higher than any revenue value
            operator="gt",
            label="Failing Constraint",
        )

        model = Model(
            line_items=basic_line_items,
            years=[2023, 2024, 2025],
            categories=basic_categories,
            constraints=[failing_constraint],
        )

        constraint_results = ConstraintResults(model, "failing_constraint")

        # Revenue values are 100000, 120000, 140000 - all < 150000
        # So revenue > 150000 should be False for all years
        assert constraint_results.evaluate(2023) is False
        assert constraint_results.evaluate(2024) is False
        assert constraint_results.evaluate(2025) is False


class TestConstraintResultsHtmlRepr:
    """Test _repr_html_ method for Jupyter notebook integration."""

    @pytest.fixture
    def constraint_results(self, model_with_constraints):
        """Create a ConstraintResults instance for testing."""
        return ConstraintResults(model_with_constraints, "min_revenue")

    def test_repr_html_method(self, constraint_results):
        """Test _repr_html_ method returns HTML formatted summary."""
        html_result = constraint_results._repr_html_()

        assert html_result.startswith("<pre>")
        assert html_result.endswith("</pre>")
        assert "ConstraintResults('min_revenue')" in html_result
        assert "Label: Minimum Revenue" in html_result
        assert "<br>" in html_result  # Newlines converted to HTML breaks

    def test_repr_html_converts_newlines(self, constraint_results):
        """Test _repr_html_ method converts newlines to HTML breaks."""
        html_result = constraint_results._repr_html_()

        # Should not contain literal newlines
        assert "\n" not in html_result
        # Should contain HTML line breaks
        assert "<br>" in html_result


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
            label="Balance Check",
        )
        return Model(
            line_items=basic_line_items,
            years=[2023, 2024, 2025],
            categories=basic_categories,
            constraints=[constraint],
        )

    @pytest.fixture
    def model_with_no_label_constraint(self, basic_line_items, basic_categories):
        """Create a model with a constraint that has no label."""
        constraint = Constraint(
            name="no_label_constraint",
            line_item_name="revenue",
            target=100000.0,
            operator="eq",
        )
        return Model(
            line_items=basic_line_items,
            years=[2023, 2024, 2025],
            categories=basic_categories,
            constraints=[constraint],
        )

    def test_constraint_with_tolerance(self, model_with_tolerance_constraint):
        """Test ConstraintResults with a constraint that has tolerance."""
        constraint_results = ConstraintResults(
            model_with_tolerance_constraint, "balance_check"
        )

        assert constraint_results.tolerance == 0.01
        assert constraint_results.operator == "eq"

        # Test that methods still work
        summary = constraint_results.summary()
        assert "ConstraintResults('balance_check')" in summary
        assert "Label: Balance Check" in summary

    def test_constraint_with_no_label(self, model_with_no_label_constraint):
        """Test ConstraintResults with a constraint that has no label."""
        constraint_results = ConstraintResults(
            model_with_no_label_constraint, "no_label_constraint"
        )

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
    def model_with_constraints(
        self, basic_line_items, basic_categories, basic_constraints
    ):
        """Create a model with constraints for testing."""
        return Model(
            line_items=basic_line_items,
            years=[2023, 2024, 2025],
            categories=basic_categories,
            constraints=basic_constraints,
        )

    def test_chart_method_with_chart_error(self, model_with_constraints):
        """Test chart method when underlying chart method raises error."""
        constraint_results = ConstraintResults(model_with_constraints, "min_revenue")

        with patch(
            "pyproforma.charts.charts.Charts.constraint",
            side_effect=KeyError("Chart error"),
        ):
            with pytest.raises(KeyError, match="Chart error"):
                constraint_results.chart()

    def test_table_method_with_table_error(self, model_with_constraints):
        """Test table method when underlying table method raises error."""
        constraint_results = ConstraintResults(model_with_constraints, "min_revenue")

        with patch(
            "pyproforma.tables.tables.Tables.constraint",
            side_effect=KeyError("Table error"),
        ):
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
                values={2023: 100000, 2024: 120000},
                value_format="two_decimals",
            ),
            LineItem(
                name="expenses",
                category="costs",
                values={2023: 50000, 2024: 60000},
                value_format="two_decimals",
            ),
        ]

        categories = [
            Category(name="income", label="Income"),
            Category(name="costs", label="Costs"),
        ]

        constraints = [
            Constraint(
                name="profit_margin",
                line_item_name="revenue",
                target=90000.0,
                operator="gt",
                label="Minimum Profit Margin",
            )
        ]

        return Model(
            line_items=line_items,
            years=[2023, 2024],
            categories=categories,
            constraints=constraints,
        )

    def test_constraint_results_from_model_method(self, integrated_model):
        """Test creating ConstraintResults through model.constraint() method."""
        constraint_results = integrated_model.constraint("profit_margin")

        assert isinstance(constraint_results, ConstraintResults)
        assert constraint_results.name == "profit_margin"
        assert constraint_results.model is integrated_model

        # Test that methods work
        summary = constraint_results.summary()
        assert "ConstraintResults('profit_margin')" in summary
        assert "Label: Minimum Profit Margin" in summary

    def test_constraint_results_string_representation_integration(
        self, integrated_model
    ):
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


class TestConstraintResultsMetadata:
    """Test _constraint_metadata property of ConstraintResults."""

    @pytest.fixture
    def constraint_results(self, model_with_constraints):
        """Create a ConstraintResults instance for testing."""
        return ConstraintResults(model_with_constraints, "min_revenue")

    @pytest.fixture
    def constraint_results_with_dict_target(self, model_with_constraints):
        """Create a ConstraintResults instance with dict target for testing."""
        return ConstraintResults(model_with_constraints, "revenue_growth")

    def test_constraint_metadata_property_returns_dict(self, constraint_results):
        """Test that _constraint_metadata property returns a dictionary."""
        metadata = constraint_results._constraint_metadata

        assert isinstance(metadata, dict)

    def test_constraint_metadata_property_calls_model_method(self, constraint_results):
        """Test that _constraint_metadata property calls
        model._get_constraint_metadata."""
        with patch.object(
            constraint_results.model, "_get_constraint_metadata"
        ) as mock_get_metadata:
            mock_get_metadata.return_value = {"name": "min_revenue", "operator": "gt"}

            result = constraint_results._constraint_metadata

            mock_get_metadata.assert_called_once_with("min_revenue")
            assert result == {"name": "min_revenue", "operator": "gt"}

    def test_constraint_metadata_property_contains_expected_fields(
        self, constraint_results
    ):
        """Test that _constraint_metadata property contains expected fields."""
        metadata = constraint_results._constraint_metadata

        # Verify all expected fields are present
        expected_fields = [
            "name",
            "label",
            "line_item_name",
            "target",
            "operator",
            "operator_symbol",
            "tolerance",
        ]
        for field in expected_fields:
            assert field in metadata, f"Field '{field}' should be in metadata"

    def test_constraint_metadata_property_basic_constraint(self, constraint_results):
        """Test _constraint_metadata property with basic constraint values."""
        metadata = constraint_results._constraint_metadata

        assert metadata["name"] == "min_revenue"
        assert metadata["label"] == "Minimum Revenue"
        assert metadata["line_item_name"] == "revenue"
        assert metadata["target"] == 80000.0
        assert metadata["operator"] == "gt"
        assert metadata["operator_symbol"] == ">"
        assert metadata["tolerance"] == 0.0  # Default tolerance

    def test_constraint_metadata_property_dict_target_constraint(
        self, constraint_results_with_dict_target
    ):
        """Test _constraint_metadata property with constraint having dict target."""
        metadata = constraint_results_with_dict_target._constraint_metadata

        assert metadata["name"] == "revenue_growth"
        assert metadata["label"] == "Revenue Growth Target"
        assert metadata["line_item_name"] == "revenue"
        assert metadata["target"] == {2023: 95000.0, 2024: 115000.0, 2025: 135000.0}
        assert metadata["operator"] == "ge"
        assert metadata["operator_symbol"] == ">="
        assert metadata["tolerance"] == 0.0  # Default tolerance

    def test_constraint_metadata_property_with_tolerance(
        self, basic_line_items, basic_categories
    ):
        """Test _constraint_metadata property with constraint that has tolerance."""
        constraint_with_tolerance = Constraint(
            name="balance_check",
            line_item_name="revenue",
            target=100000.0,
            operator="eq",
            tolerance=0.01,
            label="Balance Check",
        )

        model = Model(
            line_items=basic_line_items,
            years=[2023, 2024, 2025],
            categories=basic_categories,
            constraints=[constraint_with_tolerance],
        )

        constraint_results = ConstraintResults(model, "balance_check")
        metadata = constraint_results._constraint_metadata

        assert metadata["name"] == "balance_check"
        assert metadata["label"] == "Balance Check"
        assert metadata["tolerance"] == 0.01
        assert metadata["operator"] == "eq"
        assert metadata["operator_symbol"] == "="

    def test_constraint_metadata_property_propagates_key_error(
        self, model_with_constraints
    ):
        """Test that _constraint_metadata property propagates
        KeyError from model method."""
        constraint_results = ConstraintResults(model_with_constraints, "min_revenue")

        with patch.object(
            constraint_results.model, "_get_constraint_metadata"
        ) as mock_get_metadata:
            mock_get_metadata.side_effect = KeyError("Constraint not found")

            with pytest.raises(KeyError, match="Constraint not found"):
                _ = constraint_results._constraint_metadata

    def test_constraint_metadata_property_uses_correct_constraint_name(
        self, constraint_results
    ):
        """Test that _constraint_metadata property uses the correct constraint name."""
        with patch.object(
            constraint_results.model, "_get_constraint_metadata"
        ) as mock_get_metadata:
            mock_get_metadata.return_value = {}

            _ = constraint_results._constraint_metadata

            # Verify it was called with the constraint's name
            mock_get_metadata.assert_called_once_with(constraint_results.name)

    def test_constraint_metadata_property_caching_behavior(self, constraint_results):
        """Test that _constraint_metadata property doesn't cache
        (calls model each time)."""
        with patch.object(
            constraint_results.model, "_get_constraint_metadata"
        ) as mock_get_metadata:
            mock_get_metadata.return_value = {"name": "min_revenue"}

            # Access the property multiple times
            _ = constraint_results._constraint_metadata
            _ = constraint_results._constraint_metadata
            _ = constraint_results._constraint_metadata

            # Should call the model method each time (no caching)
            assert mock_get_metadata.call_count == 3
            mock_get_metadata.assert_called_with("min_revenue")

    def test_constraint_metadata_property_with_different_operators(
        self, basic_line_items, basic_categories
    ):
        """Test _constraint_metadata property with constraints having different
        operators."""
        operators_tests = [
            ("eq", "="),
            ("ne", "!="),
            ("lt", "<"),
            ("le", "<="),
            ("gt", ">"),
            ("ge", ">="),
        ]

        for operator, symbol in operators_tests:
            constraint = Constraint(
                name=f"test_{operator}",
                line_item_name="revenue",
                target=100000.0,
                operator=operator,
                label=f"Test {operator.upper()}",
            )

            model = Model(
                line_items=basic_line_items,
                years=[2023, 2024, 2025],
                categories=basic_categories,
                constraints=[constraint],
            )

            constraint_results = ConstraintResults(model, f"test_{operator}")
            metadata = constraint_results._constraint_metadata

            assert metadata["operator"] == operator
            assert metadata["operator_symbol"] == symbol
            assert metadata["name"] == f"test_{operator}"
            assert metadata["label"] == f"Test {operator.upper()}"


class TestConstraintResultsEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_constraint_results_with_empty_model_years_now_allowed(self):
        """Test that creating a Model with empty years now works."""
        line_items = [LineItem(name="revenue", category="income", values={})]

        categories = [Category(name="income", label="Income")]

        constraints = [
            Constraint(
                name="test_constraint",
                line_item_name="revenue",
                target=100000.0,
                operator="gt",
            )
        ]

        # Model should now work with empty years
        model = Model(
            line_items=line_items,
            years=[],
            categories=categories,
            constraints=constraints,
        )

        # Should be able to create ConstraintResults
        constraint_result = model.constraint("test_constraint")
        assert constraint_result.name == "test_constraint"
        assert constraint_result.line_item_name == "revenue"
        assert constraint_result.failing_years() == []  # No years, no failing years

    def test_constraint_results_with_special_characters_in_name(self):
        """Test ConstraintResults with constraint names containing special characters."""  # noqa: E501
        line_items = [
            LineItem(
                name="revenue_2024",
                category="income",
                values={2024: 100000},
                value_format="two_decimals",
            )
        ]

        categories = [Category(name="income", label="Income")]

        constraints = [
            Constraint(
                name="revenue_check_2024",
                line_item_name="revenue_2024",
                target=90000.0,
                operator="gt",
                label="Revenue Check 2024",
            )
        ]

        model = Model(
            line_items=line_items,
            years=[2024],
            categories=categories,
            constraints=constraints,
        )

        constraint_results = ConstraintResults(model, "revenue_check_2024")

        assert constraint_results.name == "revenue_check_2024"
        summary = constraint_results.summary()
        assert "ConstraintResults('revenue_check_2024')" in summary
        assert "Label: Revenue Check 2024" in summary
        assert "Value (2024): 100,000.00" in summary


class TestConstraintResultsNameSetter:
    """Test the name setter functionality of ConstraintResults."""

    @pytest.fixture
    def model_with_multiple_constraints(self, basic_line_items, basic_categories):
        """Create a model with multiple constraints for testing."""
        constraints = [
            Constraint(
                name="min_revenue",
                line_item_name="revenue",
                target=80000.0,
                operator="gt",
                label="Minimum Revenue",
            ),
            Constraint(
                name="max_revenue",
                line_item_name="revenue",
                target=200000.0,
                operator="lt",
                label="Maximum Revenue",
            ),
            Constraint(
                name="expense_limit",
                line_item_name="expenses",
                target=75000.0,
                operator="lt",
                label="Expense Limit",
            ),
        ]
        return Model(
            line_items=basic_line_items,
            years=[2023, 2024, 2025],
            categories=basic_categories,
            constraints=constraints,
        )

    def test_name_setter_updates_constraint_name(self, model_with_multiple_constraints):
        """Test that setting name updates the constraint name correctly."""
        constraint_results = model_with_multiple_constraints.constraint("min_revenue")
        original_name = constraint_results.name

        # Set new name
        new_name = "revenue_floor"
        constraint_results.name = new_name

        # Verify the name was updated
        assert constraint_results.name == new_name
        assert constraint_results.name != original_name

    def test_name_setter_updates_model(self, model_with_multiple_constraints):
        """Test that setting name updates the constraint in the model."""
        constraint_results = model_with_multiple_constraints.constraint("min_revenue")
        new_name = "revenue_minimum"

        # Set new name
        constraint_results.name = new_name

        # Verify the model was updated by accessing constraint with new name
        updated_constraint = model_with_multiple_constraints.constraint(new_name)
        assert updated_constraint.name == new_name
        assert updated_constraint.line_item_name == "revenue"
        assert updated_constraint.target(2023) == 80000.0

    def test_name_setter_removes_old_name_from_model(
        self, model_with_multiple_constraints
    ):
        """Test that setting name removes the old name from the model."""
        constraint_results = model_with_multiple_constraints.constraint("min_revenue")
        original_name = constraint_results.name
        new_name = "revenue_floor"

        # Set new name
        constraint_results.name = new_name

        # Verify old name no longer exists in model
        with pytest.raises(
            KeyError, match=f"Constraint with name '{original_name}' not found"
        ):
            model_with_multiple_constraints.constraint(original_name)

    def test_name_setter_rejects_duplicate_name(self, model_with_multiple_constraints):
        """Test that setting a name that already exists raises ValueError."""
        constraint_results = model_with_multiple_constraints.constraint("min_revenue")
        original_name = constraint_results.name

        # Try to set name to an existing constraint name
        with pytest.raises(
            ValueError, match="Constraint with name 'max_revenue' already exists"
        ):
            constraint_results.name = "max_revenue"

        # Verify original name is unchanged
        assert constraint_results.name == original_name

    def test_name_setter_rejects_empty_name(self, model_with_multiple_constraints):
        """Test that setting an empty name raises ValueError."""
        constraint_results = model_with_multiple_constraints.constraint("min_revenue")
        original_name = constraint_results.name

        # Try to set empty name
        with pytest.raises(
            ValueError,
            match="Name must only contain letters, numbers, underscores, or hyphens",
        ):
            constraint_results.name = ""

        # Verify original name is unchanged
        assert constraint_results.name == original_name

    def test_name_setter_rejects_invalid_characters(
        self, model_with_multiple_constraints
    ):
        """Test that setting a name with invalid characters raises ValueError."""
        constraint_results = model_with_multiple_constraints.constraint("min_revenue")
        original_name = constraint_results.name

        # Try to set name with invalid characters
        invalid_names = ["name with spaces", "name@symbol", "name$special", "name!"]

        for invalid_name in invalid_names:
            with pytest.raises(
                ValueError,
                match="Name must only contain letters, numbers, underscores, or hyphens",
            ):
                constraint_results.name = invalid_name

            # Verify original name is unchanged after each attempt
            assert constraint_results.name == original_name

    def test_name_setter_accepts_valid_names(self, model_with_multiple_constraints):
        """Test that setting valid names works correctly."""
        constraint_results = model_with_multiple_constraints.constraint("min_revenue")

        valid_names = [
            "revenue_floor",
            "revenue-minimum",
            "rev123",
            "Revenue_Floor_2023",
            "constraint_1",
        ]

        for valid_name in valid_names:
            # Set the valid name
            constraint_results.name = valid_name

            # Verify it was set correctly
            assert constraint_results.name == valid_name

            # Verify we can access it from the model
            updated_constraint = model_with_multiple_constraints.constraint(valid_name)
            assert updated_constraint.name == valid_name

    def test_name_setter_preserves_other_properties(
        self, model_with_multiple_constraints
    ):
        """Test that setting name preserves all other constraint properties."""
        constraint_results = model_with_multiple_constraints.constraint("min_revenue")

        # Capture original properties
        original_label = constraint_results.label
        original_line_item_name = constraint_results.line_item_name
        original_target = constraint_results.target(2023)
        original_operator = constraint_results.operator
        original_tolerance = constraint_results.tolerance

        # Set new name
        constraint_results.name = "revenue_minimum"

        # Verify all other properties are preserved
        assert constraint_results.label == original_label
        assert constraint_results.line_item_name == original_line_item_name
        assert constraint_results.target(2023) == original_target
        assert constraint_results.operator == original_operator
        assert constraint_results.tolerance == original_tolerance

    def test_name_setter_updates_repr(self, model_with_multiple_constraints):
        """Test that setting name updates the __repr__ output."""
        constraint_results = model_with_multiple_constraints.constraint("min_revenue")

        # Check original repr
        original_repr = repr(constraint_results)
        assert "name='min_revenue'" in original_repr

        # Set new name
        new_name = "revenue_floor"
        constraint_results.name = new_name

        # Check updated repr
        updated_repr = repr(constraint_results)
        assert f"name='{new_name}'" in updated_repr
        assert "name='min_revenue'" not in updated_repr

    def test_name_setter_updates_summary(self, model_with_multiple_constraints):
        """Test that setting name updates the summary output."""
        constraint_results = model_with_multiple_constraints.constraint("min_revenue")

        # Set new name
        new_name = "revenue_floor"
        constraint_results.name = new_name

        # Check that summary contains new name
        summary = constraint_results.summary()
        assert f"ConstraintResults('{new_name}')" in summary
        assert "ConstraintResults('min_revenue')" not in summary
