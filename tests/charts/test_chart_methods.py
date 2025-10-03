"""Tests for Charts.line_items_pie() and Charts.constraint() methods."""
from unittest.mock import Mock, patch

import plotly.graph_objects as go
import pytest

from pyproforma import Category, Constraint, LineItem, Model
from pyproforma.charts.chart_class import Chart
from pyproforma.charts.charts import ChartGenerationError, Charts


class TestChartsLineItemsPie:
    """Test cases for the Charts.line_items_pie() method."""

    @pytest.fixture
    def mock_model(self):
        """Create a mock model for testing pie charts."""
        model = Mock(spec=Model)
        model.years = [2020, 2021, 2022]

        # Mock line_item() method responses
        def mock_li(name):
            line_item_map = {
                "revenue": Mock(label="Revenue", value_format="no_decimals"),
                "expenses": Mock(label="Expenses", value_format="no_decimals"),
                "profit": Mock(label="Profit", value_format="no_decimals"),
            }
            if name in line_item_map:
                return line_item_map[name]
            raise KeyError(f"Name '{name}' not found in model defined names.")

        model.line_item.side_effect = mock_li

        # Mock value responses
        def mock_value(name, year):
            value_map = {
                ("revenue", 2020): 100.0,
                ("revenue", 2021): 150.0,
                ("revenue", 2022): 200.0,
                ("expenses", 2020): 50.0,
                ("expenses", 2021): 75.0,
                ("expenses", 2022): 100.0,
                ("profit", 2020): 50.0,
                ("profit", 2021): 75.0,
                ("profit", 2022): 100.0,
            }
            if (name, year) in value_map:
                return value_map[(name, year)]
            raise KeyError(f"Value for '{name}' in year {year} not found.")

        model.value.side_effect = mock_value

        return model

    @pytest.fixture
    def charts(self, mock_model):
        """Create a Charts instance with mock model."""
        return Charts(mock_model)

    def test_line_items_pie_default_year(self, charts, mock_model):
        """Test line_items_pie with default year (latest year)."""
        with patch.object(Chart, "to_plotly") as mock_to_plotly:
            mock_fig = Mock(spec=go.Figure)
            mock_to_plotly.return_value = mock_fig

            result = charts.line_items_pie(["revenue", "expenses", "profit"])

            # Should use the latest year (2022)
            mock_to_plotly.assert_called_once_with(
                width=800, height=600, template="plotly_white", show_legend=False
            )
            assert result is mock_fig

            # Verify model interactions
            assert mock_model.line_item.call_count >= 3
            # Should call value for each item with year 2022
            value_calls = [
                call for call in mock_model.value.call_args_list if call[0][1] == 2022
            ]
            assert len(value_calls) == 3

    def test_line_items_pie_specific_year(self, charts, mock_model):
        """Test line_items_pie with specific year."""
        with patch.object(Chart, "to_plotly") as mock_to_plotly:
            mock_fig = Mock(spec=go.Figure)
            mock_to_plotly.return_value = mock_fig

            result = charts.line_items_pie(
                ["revenue", "expenses"], year=2021, width=1000, height=800
            )

            mock_to_plotly.assert_called_once_with(
                width=1000, height=800, template="plotly_white", show_legend=False
            )
            assert result is mock_fig

            # Should call value for each item with year 2021
            value_calls = [
                call for call in mock_model.value.call_args_list if call[0][1] == 2021
            ]
            assert len(value_calls) == 2

    def test_line_items_pie_custom_template(self, charts):
        """Test line_items_pie with custom template."""
        with patch.object(Chart, "to_plotly") as mock_to_plotly:
            mock_fig = Mock(spec=go.Figure)
            mock_to_plotly.return_value = mock_fig

            result = charts.line_items_pie(
                ["revenue", "expenses"], template="plotly_dark"
            )

            mock_to_plotly.assert_called_once_with(
                width=800, height=600, template="plotly_dark", show_legend=False
            )
            assert result is mock_fig

    def test_line_items_pie_empty_list_raises_error(self, charts):
        """Test line_items_pie with empty list raises ValueError."""
        with pytest.raises(ValueError) as excinfo:
            charts.line_items_pie([])
        assert "item_names list cannot be empty" in str(excinfo.value)

    def test_line_items_pie_invalid_year_raises_error(self, charts, mock_model):
        """Test line_items_pie with year not in model years raises ValueError."""
        with pytest.raises(ValueError) as excinfo:
            charts.line_items_pie(["revenue"], year=2030)
        assert "Year 2030 not found in model years" in str(excinfo.value)

    def test_line_items_pie_missing_item_name_raises_error(self, charts, mock_model):
        """Test line_items_pie with non-existent item name raises KeyError."""
        with pytest.raises(KeyError) as excinfo:
            charts.line_items_pie(["revenue", "nonexistent"])
        assert "Name 'nonexistent' not found in model defined names" in str(
            excinfo.value
        )

    def test_line_items_pie_no_positive_values_raises_error(self, charts, mock_model):
        """Test line_items_pie raises error when no positive values found."""
        # Mock all values to be negative or zero
        def mock_value_negative(name, year):
            return -10.0

        mock_model.value.side_effect = mock_value_negative

        with pytest.raises(ValueError) as excinfo:
            charts.line_items_pie(["revenue", "expenses"])
        assert "No positive values found for the specified items" in str(excinfo.value)

    def test_line_items_pie_empty_model_years_raises_error(self, mock_model):
        """Test line_items_pie with empty model years raises ChartGenerationError."""
        mock_model.years = []
        charts = Charts(mock_model)

        with pytest.raises(ChartGenerationError) as excinfo:
            charts.line_items_pie(["revenue"])
        assert "Cannot create chart: model has no years defined" in str(excinfo.value)

    @patch("pyproforma.charts.charts.Chart")
    @patch("pyproforma.charts.charts.ChartDataSet")
    def test_line_items_pie_chart_creation_details(
        self, mock_dataset_class, mock_chart_class, charts, mock_model
    ):
        """Test detailed chart creation for line_items_pie method."""
        mock_dataset = Mock()
        mock_chart = Mock()
        mock_fig = Mock(spec=go.Figure)

        mock_dataset_class.return_value = mock_dataset
        mock_chart_class.return_value = mock_chart
        mock_chart.to_plotly.return_value = mock_fig

        result = charts.line_items_pie(["revenue", "expenses"], year=2022)

        # Verify ChartDataSet creation - pie chart should have positive values
        mock_dataset_class.assert_called_once_with(
            label="Line Items Distribution (2022)", data=[200.0, 100.0], type="pie"
        )

        # Verify Chart creation - labels should be the item labels
        mock_chart_class.assert_called_once_with(
            labels=["Revenue", "Expenses"],
            data_sets=[mock_dataset],
            title="Line Items Distribution - 2022",
            value_format="no_decimals",
        )

        # Verify to_plotly call
        mock_chart.to_plotly.assert_called_once_with(
            width=800, height=600, template="plotly_white", show_legend=False
        )

        assert result is mock_fig


class TestChartsConstraint:
    """Test cases for the Charts.constraint() method."""

    @pytest.fixture
    def mock_model_with_constraints(self):
        """Create a mock model with constraints for testing."""
        model = Mock(spec=Model)
        model.years = [2023, 2024, 2025]

        # Mock line_item() method
        def mock_li(name):
            if name == "revenue":
                return Mock(label="Revenue", value_format="no_decimals")
            raise KeyError(f"Name '{name}' not found in model defined names.")

        model.line_item.side_effect = mock_li

        # Mock value() method
        def mock_value(name, year):
            value_map = {
                ("revenue", 2023): 100000,
                ("revenue", 2024): 120000,
                ("revenue", 2025): 140000,
            }
            if (name, year) in value_map:
                return value_map[(name, year)]
            raise KeyError(f"Value for '{name}' in year {year} not found.")

        model.value.side_effect = mock_value

        # Mock constraint() method
        def mock_constraint(name):
            if name == "min_revenue":
                constraint_result = Mock()
                constraint_result.name = "min_revenue"
                constraint_result.label = "Minimum Revenue"
                constraint_result.line_item_name = "revenue"

                def target_by_year(year):
                    target_map = {2023: 80000, 2024: 90000, 2025: 100000}
                    return target_map.get(year)

                constraint_result.target_by_year = target_by_year
                return constraint_result
            raise KeyError(f"Constraint '{name}' not found in model constraints.")

        model.constraint.side_effect = mock_constraint

        return model

    @pytest.fixture
    def charts(self, mock_model_with_constraints):
        """Create a Charts instance with mock model."""
        return Charts(mock_model_with_constraints)

    def test_constraint_default_parameters(self, charts, mock_model_with_constraints):
        """Test constraint method with default parameters."""
        with patch.object(Chart, "to_plotly") as mock_to_plotly:
            mock_fig = Mock(spec=go.Figure)
            mock_to_plotly.return_value = mock_fig

            result = charts.constraint("min_revenue")

            mock_to_plotly.assert_called_once_with(
                width=800, height=600, template="plotly_white"
            )
            assert result is mock_fig

            # Verify model interactions
            mock_model_with_constraints.constraint.assert_called_once_with(
                "min_revenue"
            )
            mock_model_with_constraints.line_item.assert_called_with("revenue")
            assert mock_model_with_constraints.value.call_count == 3

    def test_constraint_custom_parameters(self, charts, mock_model_with_constraints):
        """Test constraint method with custom parameters."""
        with patch.object(Chart, "to_plotly") as mock_to_plotly:
            mock_fig = Mock(spec=go.Figure)
            mock_to_plotly.return_value = mock_fig

            result = charts.constraint(
                "min_revenue",
                width=1000,
                height=800,
                template="plotly_dark",
                line_item_type="line",
                constraint_type="bar",
            )

            mock_to_plotly.assert_called_once_with(
                width=1000, height=800, template="plotly_dark"
            )
            assert result is mock_fig

    def test_constraint_invalid_constraint_name_raises_error(
        self, charts, mock_model_with_constraints
    ):
        """Test constraint with non-existent constraint name raises KeyError."""
        with pytest.raises(KeyError) as excinfo:
            charts.constraint("nonexistent_constraint")
        assert "Constraint 'nonexistent_constraint' not found" in str(excinfo.value)

    def test_constraint_empty_model_years_raises_error(
        self, mock_model_with_constraints
    ):
        """Test constraint with empty model years raises ChartGenerationError."""
        mock_model_with_constraints.years = []
        charts = Charts(mock_model_with_constraints)

        with pytest.raises(ChartGenerationError) as excinfo:
            charts.constraint("min_revenue")
        assert "Cannot create chart: model has no years defined" in str(excinfo.value)

    @patch("pyproforma.charts.charts.Chart")
    @patch("pyproforma.charts.charts.ChartDataSet")
    def test_constraint_chart_creation_details(
        self, mock_dataset_class, mock_chart_class, charts, mock_model_with_constraints
    ):
        """Test detailed chart creation for constraint method."""
        mock_dataset1 = Mock()
        mock_dataset2 = Mock()
        mock_chart = Mock()
        mock_fig = Mock(spec=go.Figure)

        mock_dataset_class.side_effect = [mock_dataset1, mock_dataset2]
        mock_chart_class.return_value = mock_chart
        mock_chart.to_plotly.return_value = mock_fig

        result = charts.constraint(
            "min_revenue", line_item_type="bar", constraint_type="line"
        )

        # Verify ChartDataSet creation for both datasets
        assert mock_dataset_class.call_count == 2

        # First dataset is line item values
        mock_dataset_class.assert_any_call(
            label="Revenue", data=[100000, 120000, 140000], color="blue", type="bar"
        )

        # Second dataset is constraint target values
        mock_dataset_class.assert_any_call(
            label="Minimum Revenue Target",
            data=[80000, 90000, 100000],
            color="red",
            type="line",
        )

        # Verify Chart creation
        mock_chart_class.assert_called_once_with(
            labels=["2023", "2024", "2025"],
            data_sets=[mock_dataset1, mock_dataset2],
            title="Revenue vs Minimum Revenue Target",
            value_format="no_decimals",
        )

        # Verify to_plotly call
        mock_chart.to_plotly.assert_called_once_with(
            width=800, height=600, template="plotly_white"
        )

        assert result is mock_fig

    def test_constraint_handles_none_target_values(
        self, charts, mock_model_with_constraints
    ):
        """Test constraint handles None target values correctly."""
        # Mock constraint to return None for some years
        def mock_constraint_with_nones(name):
            if name == "min_revenue":
                constraint_result = Mock()
                constraint_result.name = "min_revenue"
                constraint_result.label = "Minimum Revenue"
                constraint_result.line_item_name = "revenue"

                def target_by_year(year):
                    if year == 2023:
                        return 80000
                    return None  # Return None for other years

                constraint_result.target_by_year = target_by_year
                return constraint_result
            raise KeyError(f"Constraint '{name}' not found in model constraints.")

        mock_model_with_constraints.constraint.side_effect = mock_constraint_with_nones

        with patch.object(Chart, "to_plotly") as mock_to_plotly:
            mock_fig = Mock(spec=go.Figure)
            mock_to_plotly.return_value = mock_fig

            # Should not raise error, None values should be converted to 0.0
            result = charts.constraint("min_revenue")
            assert result is mock_fig


class TestChartsConstraintIntegration:
    """Integration tests for Charts.constraint() with real Model objects."""

    @pytest.fixture
    def real_model_with_constraints(self):
        """Create a real model with constraints for integration testing."""
        line_items = [
            LineItem(
                name="revenue",
                label="Revenue",
                category="income",
                values={2023: 100000, 2024: 120000, 2025: 140000},
                value_format="no_decimals",
            ),
        ]

        categories = [Category(name="income", label="Income")]

        constraints = [
            Constraint(
                name="min_revenue",
                line_item_name="revenue",
                target=80000.0,
                operator="gt",
                label="Minimum Revenue",
            ),
        ]

        return Model(
            line_items=line_items,
            years=[2023, 2024, 2025],
            categories=categories,
            constraints=constraints,
        )

    def test_real_model_constraint_chart(self, real_model_with_constraints):
        """Test constraint chart with real model."""
        charts = Charts(real_model_with_constraints)

        # This should create a real plotly figure
        fig = charts.constraint("min_revenue")

        assert isinstance(fig, go.Figure)
        assert "Revenue vs Minimum Revenue Target" in fig.layout.title.text

        # Check that both datasets are present
        assert len(fig.data) == 2
        # First dataset should be revenue values
        assert list(fig.data[0].y) == [100000, 120000, 140000]
        # Second dataset should be constraint target values
        assert list(fig.data[1].y) == [80000.0, 80000.0, 80000.0]


class TestChartsLineItemsPieIntegration:
    """Integration tests for Charts.line_items_pie() with real Model objects."""

    @pytest.fixture
    def real_model(self):
        """Create a real model for integration testing."""
        line_items = [
            LineItem(
                name="revenue",
                label="Revenue",
                category="income",
                values={2020: 100.0, 2021: 150.0, 2022: 200.0},
            ),
            LineItem(
                name="expenses",
                label="Expenses",
                category="costs",
                values={2020: 50.0, 2021: 75.0, 2022: 100.0},
            ),
            LineItem(
                name="profit",
                label="Profit",
                category="income",
                values={2020: 50.0, 2021: 75.0, 2022: 100.0},
            ),
        ]

        return Model(line_items=line_items, years=[2020, 2021, 2022])

    def test_real_model_line_items_pie_chart(self, real_model):
        """Test line_items_pie chart with real model."""
        charts = Charts(real_model)

        # This should create a real plotly figure
        fig = charts.line_items_pie(["revenue", "expenses", "profit"], year=2022)

        assert isinstance(fig, go.Figure)
        assert "Line Items Distribution - 2022" in fig.layout.title.text

        # Check that data is present (pie chart should have one trace)
        assert len(fig.data) == 1
        assert list(fig.data[0].values) == [200.0, 100.0, 100.0]
        assert list(fig.data[0].labels) == ["Revenue", "Expenses", "Profit"]

    def test_real_model_line_items_pie_default_year(self, real_model):
        """Test line_items_pie chart uses latest year when year not specified."""
        charts = Charts(real_model)

        fig = charts.line_items_pie(["revenue", "expenses"])

        assert isinstance(fig, go.Figure)
        # Should use latest year (2022)
        assert "2022" in fig.layout.title.text
        assert list(fig.data[0].values) == [200.0, 100.0]
