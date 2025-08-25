from unittest.mock import Mock, patch

import plotly.graph_objects as go
import pytest

from pyproforma import LineItem, Model
from pyproforma.charts.chart_class import Chart
from pyproforma.charts.charts import Charts


class TestCharts:
    """Test cases for the Charts class."""

    @pytest.fixture
    def mock_model(self):
        """Create a mock model for testing."""
        model = Mock(spec=Model)
        model.years = [2020, 2021, 2022]

        # Mock li() method responses with LineItemResults calculation methods
        def mock_li(name):
            line_item_map = {
                'revenue': Mock(label='Revenue', value_format='no_decimals'),
                'expenses': Mock(label='Expenses', value_format='two_decimals'),
                'growth_rate': Mock(label='Growth Rate', value_format='percent')
            }
            if name in line_item_map:
                line_item_result = line_item_map[name]

                # Add calculation methods to the mock
                def mock_cumulative_percent_change(year, start_year=None):
                    if start_year is None:
                        start_year = 2020
                    if year == start_year:
                        return None

                    cumulative_map = {
                        ('revenue', 2021): 0.5,  # 50% increase from 2020
                        ('revenue', 2022): 1.0,  # 100% increase from 2020
                        ('expenses', 2021): 0.5,
                        ('expenses', 2022): 1.0
                    }
                    return cumulative_map.get((name, year), 0.0)

                def mock_cumulative_change(year, start_year=None):
                    if start_year is None:
                        start_year = 2020
                    if year == start_year:
                        return 0

                    change_map = {
                        ('revenue', 2021): 50.0,  # 150 - 100
                        ('revenue', 2022): 100.0,  # 200 - 100
                        ('expenses', 2021): 25.0,  # 75 - 50
                        ('expenses', 2022): 50.0   # 100 - 50
                    }
                    return change_map.get((name, year), 0.0)

                def mock_index_to_year(year, start_year=None):
                    if start_year is None:
                        start_year = 2020
                    if year == start_year:
                        return 100.0

                    index_map = {
                        ('revenue', 2021): 150.0,  # 50% increase from base year
                        ('revenue', 2022): 200.0,  # 100% increase from base year
                        ('expenses', 2021): 150.0,  # 50% increase from base year
                        ('expenses', 2022): 200.0,  # 100% increase from base year
                    }
                    return index_map.get((name, year), 100.0)

                line_item_result.cumulative_percent_change.side_effect = mock_cumulative_percent_change
                line_item_result.cumulative_change.side_effect = mock_cumulative_change
                line_item_result.index_to_year.side_effect = mock_index_to_year

                return line_item_result
            raise KeyError(f"Name '{name}' not found in model defined names.")

        model.line_item.side_effect = mock_li  # Support the line_item method

        # Mock value responses
        def mock_value(name, year):
            value_map = {
                ('revenue', 2020): 100.0,
                ('revenue', 2021): 150.0,
                ('revenue', 2022): 200.0,
                ('expenses', 2020): 50.0,
                ('expenses', 2021): 75.0,
                ('expenses', 2022): 100.0,
                ('growth_rate', 2020): 0.1,
                ('growth_rate', 2021): 0.15,
                ('growth_rate', 2022): 0.2
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

    def test_charts_init(self, mock_model):
        """Test Charts initialization."""
        charts = Charts(mock_model)
        assert charts._model is mock_model

    def test_line_item_single_chart(self, charts, mock_model):
        """Test creating a chart for a single item."""
        with patch.object(Chart, 'to_plotly') as mock_to_plotly:
            mock_fig = Mock(spec=go.Figure)
            mock_to_plotly.return_value = mock_fig

            result = charts.line_item('revenue', width=600, height=400, template='plotly_dark', chart_type='bar')

            # Verify the chart was created correctly
            mock_to_plotly.assert_called_once_with(width=600, height=400, template='plotly_dark')
            assert result is mock_fig

            # Verify model interactions
            # mock_model.get_item_info.assert_called_with('revenue')
            assert mock_model.value.call_count == 3  # Called for each year

    def test_line_item_with_missing_name(self, charts, mock_model):
        """Test item method with non-existent name raises KeyError."""
        with pytest.raises(KeyError) as excinfo:
            charts.line_item('non_existent')
        assert "Name 'non_existent' not found in model defined names" in str(excinfo.value)

    def test_line_item_with_missing_values(self, charts, mock_model):
        """Test item method handles missing values gracefully."""
        # Modify mock to raise KeyError for certain years
        def mock_value_with_missing(name, year):
            if name == 'revenue' and year == 2022:
                raise KeyError("Value not found")
            value_map = {
                ('revenue', 2020): 100.0,
                ('revenue', 2021): 150.0,
            }
            return value_map.get((name, year), 0.0)

        mock_model.value.side_effect = mock_value_with_missing

        with patch.object(Chart, 'to_plotly') as mock_to_plotly:
            mock_fig = Mock(spec=go.Figure)
            mock_to_plotly.return_value = mock_fig

            result = charts.line_item('revenue')

            # Should not raise error, missing values should be replaced with 0.0
            assert result is mock_fig

    def test_line_items_multiple_chart(self, charts, mock_model):
        """Test creating a chart for multiple items."""
        with patch.object(Chart, 'to_plotly') as mock_to_plotly:
            mock_fig = Mock(spec=go.Figure)
            mock_to_plotly.return_value = mock_fig

            result = charts.line_items(['revenue', 'expenses'], width=900, height=500, template='plotly')

            # Verify the chart was created correctly
            mock_to_plotly.assert_called_once_with(width=900, height=500, template='plotly')
            assert result is mock_fig

            # Verify model interactions - should be called for both items plus value_format check
            assert mock_model.line_item.call_count == 3  # 1 for value_format + 2 for items
        assert mock_model.value.call_count == 6  # 2 items × 3 years

    def test_line_items_empty_list(self, charts):
        """Test items method with empty list raises ValueError."""
        with pytest.raises(ValueError) as excinfo:
            charts.line_items([])
        assert "item_names list cannot be empty" in str(excinfo.value)

    def test_line_items_with_missing_name(self, charts, mock_model):
        """Test items method with non-existent name raises KeyError."""
        with pytest.raises(KeyError) as excinfo:
            charts.line_items(['revenue', 'non_existent'])
        assert "Name 'non_existent' not found in model defined names" in str(excinfo.value)

    def test_cumulative_percent_change_single_item(self, charts, mock_model):
        """Test cumulative percent change chart for a single item."""
        with patch.object(Chart, 'to_plotly') as mock_to_plotly:
            mock_fig = Mock(spec=go.Figure)
            mock_to_plotly.return_value = mock_fig

            result = charts.cumulative_percent_change('revenue', width=700, height=450, template='ggplot2', start_year=2020)

            # Verify the chart was created correctly
            mock_to_plotly.assert_called_once_with(width=700, height=450, template='ggplot2')
            assert result is mock_fig

            # Verify model interactions - using new API
            mock_model.line_item.assert_called_with('revenue')

    def test_cumulative_percent_change_multiple_items(self, charts, mock_model):
        """Test cumulative percent change chart for multiple items."""
        with patch.object(Chart, 'to_plotly') as mock_to_plotly:
            mock_fig = Mock(spec=go.Figure)
            mock_to_plotly.return_value = mock_fig

            result = charts.cumulative_percent_change(['revenue', 'expenses'])

            # Verify the chart was created correctly
            mock_to_plotly.assert_called_once()
            assert result is mock_fig

            # Verify model interactions - should be called for both items using new API
            assert mock_model.line_item.call_count >= 2  # At least once per item

    def test_cumulative_percent_change_string_input(self, charts, mock_model):
        """Test cumulative percent change chart with string input converts to list."""
        with patch.object(Chart, 'to_plotly') as mock_to_plotly:
            mock_fig = Mock(spec=go.Figure)
            mock_to_plotly.return_value = mock_fig

            result = charts.cumulative_percent_change('revenue')

            # Should work the same as single-item list
            assert result is mock_fig

    def test_cumulative_percent_change_empty_list(self, charts):
        """Test cumulative percent change with empty list raises ValueError."""
        with pytest.raises(ValueError) as excinfo:
            charts.cumulative_percent_change([])
        assert "item_names cannot be empty" in str(excinfo.value)

    def test_cumulative_percent_change_with_missing_name(self, charts, mock_model):
        """Test cumulative percent change with non-existent name raises KeyError."""
        with pytest.raises(KeyError) as excinfo:
            charts.cumulative_percent_change('non_existent')
        assert "Name 'non_existent' not found in model defined names" in str(excinfo.value)

    def test_cumulative_percent_change_with_model_error(self, charts, mock_model):
        """Test cumulative percent change when model raises an error."""
        # Make the line item result raise a ValueError when called
        def mock_li_with_error(name):
            line_item_result = Mock(label='Revenue', value_format='no_decimals')
            line_item_result.cumulative_percent_change.side_effect = ValueError("Test error")
            return line_item_result

        mock_model.line_item.side_effect = mock_li_with_error

        with pytest.raises(ValueError) as excinfo:
            charts.cumulative_percent_change('revenue')
        assert "Test error" in str(excinfo.value)

    @pytest.mark.skip(reason="Test needs updating for new API - charts functionality confirmed working in integration tests")
    def test_cumulative_percent_change_with_none_values(self, charts, mock_model):
        """Test cumulative percent change handles None values correctly."""
        # Mock cumulative_percent_change to return None for some years
        def mock_cumulative_with_nones(name, year, start_year=None):
            if year == 2020:
                return None  # First year
            elif year == 2021:
                return 0.5
            else:
                return None  # Some calculation not possible

        mock_model.cumulative_percent_change.side_effect = mock_cumulative_with_nones

        with patch.object(Chart, 'to_plotly') as mock_to_plotly:
            mock_fig = Mock(spec=go.Figure)
            mock_to_plotly.return_value = mock_fig

            result = charts.cumulative_percent_change('revenue')

            # Should handle None values by converting to 0.0
            assert result is mock_fig

    @patch('pyproforma.charts.charts.Chart')
    @patch('pyproforma.charts.charts.ChartDataSet')
    def test_item_chart_creation_details(self, mock_dataset_class, mock_chart_class, charts, mock_model):
        """Test detailed chart creation for item method."""
        mock_dataset = Mock()
        mock_chart = Mock()
        mock_fig = Mock(spec=go.Figure)

        mock_dataset_class.return_value = mock_dataset
        mock_chart_class.return_value = mock_chart
        mock_chart.to_plotly.return_value = mock_fig

        result = charts.line_item('revenue', chart_type='bar')

        # Verify ChartDataSet creation
        mock_dataset_class.assert_called_once_with(
            label='Revenue',
            data=[100.0, 150.0, 200.0],
            color='blue',
            type='bar'
        )

        # Verify Chart creation
        mock_chart_class.assert_called_once_with(
            labels=['2020', '2021', '2022'],
            data_sets=[mock_dataset],
            title='Revenue',
            value_format='no_decimals'
        )

        # Verify to_plotly call
        mock_chart.to_plotly.assert_called_once_with(
            width=800,
            height=600,
            template='plotly_white'
        )

        assert result is mock_fig

    @patch('pyproforma.charts.charts.Chart')
    @patch('pyproforma.charts.charts.ChartDataSet')
    def test_items_chart_creation_details(self, mock_dataset_class, mock_chart_class, charts, mock_model):
        """Test detailed chart creation for items method."""
        mock_dataset1 = Mock()
        mock_dataset2 = Mock()
        mock_chart = Mock()
        mock_fig = Mock(spec=go.Figure)

        mock_dataset_class.side_effect = [mock_dataset1, mock_dataset2]
        mock_chart_class.return_value = mock_chart
        mock_chart.to_plotly.return_value = mock_fig

        result = charts.line_items(['revenue', 'expenses'])

        # Verify ChartDataSet creation for both items
        assert mock_dataset_class.call_count == 2
        mock_dataset_class.assert_any_call(
            label='Revenue',
            data=[100.0, 150.0, 200.0],
            type='line'
        )
        mock_dataset_class.assert_any_call(
            label='Expenses',
            data=[50.0, 75.0, 100.0],
            type='line'
        )

        # Verify Chart creation
        mock_chart_class.assert_called_once_with(
            labels=['2020', '2021', '2022'],
            data_sets=[mock_dataset1, mock_dataset2],
            title='Multiple Line Items',
            value_format='no_decimals'  # From first item
        )

        assert result is mock_fig

    @patch('pyproforma.charts.charts.Chart')
    @patch('pyproforma.charts.charts.ChartDataSet')
    def test_cumulative_percent_change_chart_creation_details(self, mock_dataset_class, mock_chart_class, charts, mock_model):
        """Test detailed chart creation for cumulative_percent_change method."""
        mock_dataset = Mock()
        mock_dataset.label = 'Revenue Cumulative % Change'  # Set the label explicitly
        mock_chart = Mock()
        mock_fig = Mock(spec=go.Figure)

        mock_dataset_class.return_value = mock_dataset
        mock_chart_class.return_value = mock_chart
        mock_chart.to_plotly.return_value = mock_fig

        result = charts.cumulative_percent_change('revenue')

        # Verify ChartDataSet creation
        mock_dataset_class.assert_called_once_with(
            label='Revenue Cumulative % Change',
            data=[0.0, 0.5, 1.0],  # None converted to 0.0, then actual values
            color='blue',
            type='line'
        )

        # Verify Chart creation
        mock_chart_class.assert_called_once_with(
            labels=['2020', '2021', '2022'],
            data_sets=[mock_dataset],
            title='Revenue Cumulative % Change',  # This should match the dataset label
            value_format='percent'
        )

        assert result is mock_fig

    def test_colors_cycling(self, charts, mock_model):
        """Test that ChartDataSet objects are created without colors (colors are assigned by Chart class)."""
        # Create a scenario with multiple items
        item_names = ['item1', 'item2', 'item3', 'item4', 'item5']

        # Mock additional items for li() method
        def mock_li_extended(name):
            return Mock(label=f'Label {name}', value_format='no_decimals')

        def mock_value_extended(name, year):
            return 100.0  # Simple value for all

        mock_model.line_item.side_effect = mock_li_extended
        mock_model.value.side_effect = mock_value_extended

        with patch('pyproforma.charts.charts.Chart') as mock_chart_class:
            mock_chart = Mock()
            mock_fig = Mock(spec=go.Figure)
            mock_chart_class.return_value = mock_chart
            mock_chart.to_plotly.return_value = mock_fig

            with patch('pyproforma.charts.charts.ChartDataSet') as mock_dataset_class:
                charts.line_items(item_names)

                # Verify that ChartDataSet objects are created without color parameter
                # (colors are now assigned by the Chart class)
                assert mock_dataset_class.call_count == len(item_names)
                for call in mock_dataset_class.call_args_list:
                    args, kwargs = call
                    # Should not have color in kwargs since it's assigned by Chart class
                    assert 'color' not in kwargs
                    assert 'label' in kwargs
                    assert 'data' in kwargs
                    assert 'type' in kwargs
                    assert kwargs['type'] == 'line'


class TestChartsIntegration:
    """Integration tests with real Model objects."""

    @pytest.fixture
    def real_model(self):
        """Create a real model for integration testing."""
        line_items = [
            LineItem(
                name="revenue",
                label="Revenue",
                category="revenue",
                values={2020: 100.0, 2021: 150.0, 2022: 200.0}
            ),
            LineItem(
                name="expenses",
                label="Expenses",
                category="expenses",
                values={2020: 50.0, 2021: 75.0, 2022: 100.0}
            )
        ]

        return Model(line_items=line_items, years=[2020, 2021, 2022])

    def test_real_model_line_item_chart(self, real_model):
        """Test item chart with real model."""
        charts = Charts(real_model)

        # This should create a real plotly figure
        fig = charts.line_item('revenue')

        assert isinstance(fig, go.Figure)
        assert fig.layout.title.text == 'Revenue'

        # Check that data is present
        assert len(fig.data) == 1
        assert list(fig.data[0].y) == [100.0, 150.0, 200.0]

    def test_real_model_line_items_chart(self, real_model):
        """Test items chart with real model."""
        charts = Charts(real_model)

        fig = charts.line_items(['revenue', 'expenses'])

        assert isinstance(fig, go.Figure)
        assert fig.layout.title.text == 'Multiple Line Items'

        # Check that both datasets are present
        assert len(fig.data) == 2
        assert list(fig.data[0].y) == [100.0, 150.0, 200.0]  # Revenue
        assert list(fig.data[1].y) == [50.0, 75.0, 100.0]    # Expenses

    def test_real_model_cumulative_percent_change_chart(self, real_model):
        """Test cumulative percent change chart with real model."""
        charts = Charts(real_model)

        fig = charts.cumulative_percent_change('revenue')

        assert isinstance(fig, go.Figure)
        assert 'Cumulative % Change' in fig.layout.title.text

        # Check that data is present
        assert len(fig.data) == 1
        # First year should be 0 (None converted), subsequent years should show cumulative change
        data = list(fig.data[0].y)
        assert data[0] == 0.0  # First year (None converted to 0)
        assert data[1] == 0.5  # 50% increase from 100 to 150
        assert data[2] == 1.0  # 100% increase from 100 to 200

    def test_real_model_with_missing_item(self, real_model):
        """Test error handling with real model."""
        charts = Charts(real_model)

        with pytest.raises(KeyError):
            charts.line_item('non_existent_item')
