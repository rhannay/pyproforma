import pytest
from unittest.mock import Mock, patch
import pandas as pd
from pyproforma import LineItem, Model, Category
from pyproforma.models.results import LineItemResults


# Module-level fixtures available to all test classes
@pytest.fixture
def basic_line_items():
    """Create basic line items for testing."""
    return [
        LineItem(
            name="revenue",
            category="income",
            label="Revenue",
            values={2023: 100000, 2024: 120000, 2025: 140000},
            value_format="no_decimals"
        ),
        LineItem(
            name="expenses",
            category="costs",
            label="Expenses",
            values={2023: 50000, 2024: 60000, 2025: 70000},
            value_format="no_decimals"
        ),
        LineItem(
            name="profit",
            category="income",
            label="Profit",
            formula="revenue - expenses",
            value_format="no_decimals"
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
def model_with_line_items(basic_line_items, basic_categories):
    """Create a model with line items for testing."""
    return Model(
        line_items=basic_line_items,
        years=[2023, 2024, 2025],
        categories=basic_categories
    )


class TestLineItemResultsInitialization:
    """Test LineItemResults initialization and basic properties."""
    
    def test_init_valid_line_item(self, model_with_line_items):
        """Test LineItemResults initialization with valid line item."""
        line_item_results = LineItemResults(model_with_line_items, "revenue")
        
        assert line_item_results.model is model_with_line_items
        assert line_item_results.item_name == "revenue"
        assert line_item_results.source_type == "line_item"
        assert line_item_results.label == "Revenue"
        assert line_item_results.value_format == "no_decimals"
    
    def test_init_line_item_with_formula(self, model_with_line_items):
        """Test LineItemResults initialization with line item that has formula."""
        line_item_results = LineItemResults(model_with_line_items, "profit")
        
        assert line_item_results.model is model_with_line_items
        assert line_item_results.item_name == "profit"
        assert line_item_results.source_type == "line_item"
        assert line_item_results.label == "Profit"
        assert line_item_results.value_format == "no_decimals"
    
    def test_init_invalid_item_name(self, model_with_line_items):
        """Test LineItemResults initialization with invalid item name."""
        with pytest.raises(KeyError):
            LineItemResults(model_with_line_items, "nonexistent")


class TestLineItemResultsStringRepresentation:
    """Test string representation methods of LineItemResults."""
    
    @pytest.fixture
    def line_item_results(self, model_with_line_items):
        """Create a LineItemResults instance for testing."""
        return LineItemResults(model_with_line_items, "revenue")
    
    @pytest.fixture
    def line_item_results_with_formula(self, model_with_line_items):
        """Create a LineItemResults instance with formula for testing."""
        return LineItemResults(model_with_line_items, "profit")
    
    def test_str_method(self, line_item_results):
        """Test __str__ method returns summary."""
        str_result = str(line_item_results)
        
        assert "LineItemResults('revenue')" in str_result
        assert "Label: Revenue" in str_result
        assert "Source Type: line_item" in str_result
        assert "Value Format: no_decimals" in str_result
        assert "Values:" in str_result
        
    def test_repr_method(self, line_item_results):
        """Test __repr__ method returns expected format."""
        repr_result = repr(line_item_results)
        
        assert repr_result == "LineItemResults(item_name='revenue', source_type='line_item')"
    
    def test_summary_method(self, line_item_results):
        """Test summary method returns formatted line item information."""
        summary = line_item_results.summary()
        
        assert "LineItemResults('revenue')" in summary
        assert "Label: Revenue" in summary
        assert "Source Type: line_item" in summary
        assert "Value Format: no_decimals" in summary
        assert "Values: 100,000, 120,000, 140,000" in summary
        assert "Formula: None (explicit values)" in summary
    
    def test_summary_method_with_formula(self, line_item_results_with_formula):
        """Test summary method with line item that has formula."""
        summary = line_item_results_with_formula.summary()
        
        assert "LineItemResults('profit')" in summary
        assert "Label: Profit" in summary
        assert "Source Type: line_item" in summary
        assert "Value Format: no_decimals" in summary
        assert "Formula: revenue - expenses" in summary


class TestLineItemResultsValueMethods:
    """Test value retrieval methods of LineItemResults."""
    
    @pytest.fixture
    def line_item_results(self, model_with_line_items):
        """Create a LineItemResults instance for testing."""
        return LineItemResults(model_with_line_items, "revenue")
    
    def test_values_method_returns_correct_values(self, line_item_results):
        """Test values method returns correct values for all years."""
        values = line_item_results.values()
        
        expected_values = {2023: 100000, 2024: 120000, 2025: 140000}
        assert values == expected_values
    
    def test_value_method_returns_correct_value(self, line_item_results):
        """Test value method returns correct value for specific year."""
        assert line_item_results.value(2023) == 100000
        assert line_item_results.value(2024) == 120000
        assert line_item_results.value(2025) == 140000
    
    def test_value_method_raises_key_error_for_invalid_year(self, line_item_results):
        """Test value method raises KeyError for invalid year."""
        with pytest.raises(KeyError):
            line_item_results.value(2026)
    
    def test_getitem_method_returns_correct_value(self, line_item_results):
        """Test __getitem__ method returns correct value for specific year."""
        assert line_item_results[2023] == 100000
        assert line_item_results[2024] == 120000
        assert line_item_results[2025] == 140000
    
    def test_getitem_method_raises_key_error_for_invalid_year(self, line_item_results):
        """Test __getitem__ method raises KeyError for invalid year."""
        with pytest.raises(KeyError):
            line_item_results[2026]
    
    def test_values_method_calls_model_value(self, line_item_results):
        """Test that values method calls model.value for each year."""
        with patch.object(line_item_results.model, 'value') as mock_value:
            mock_value.side_effect = [100000, 120000, 140000]
            
            values = line_item_results.values()
            
            expected_calls = [
                (('revenue', 2023),),
                (('revenue', 2024),),
                (('revenue', 2025),)
            ]
            
            assert mock_value.call_count == 3
            for i, call in enumerate(mock_value.call_args_list):
                assert call.args == expected_calls[i][0]
    
    def test_value_method_calls_model_value(self, line_item_results):
        """Test that value method calls model.value with correct parameters."""
        with patch.object(line_item_results.model, 'value') as mock_value:
            mock_value.return_value = 100000
            
            result = line_item_results.value(2023)
            
            mock_value.assert_called_once_with("revenue", 2023)
            assert result == 100000


class TestLineItemResultsDataFrameMethods:
    """Test DataFrame and Series conversion methods of LineItemResults."""
    
    @pytest.fixture
    def line_item_results(self, model_with_line_items):
        """Create a LineItemResults instance for testing."""
        return LineItemResults(model_with_line_items, "revenue")
    
    def test_to_series_method_returns_pandas_series(self, line_item_results):
        """Test to_series method returns pandas Series with correct data."""
        series = line_item_results.to_series()
        
        assert isinstance(series, pd.Series)
        assert series.name == "revenue"
        assert series.index.tolist() == [2023, 2024, 2025]
        assert series.values.tolist() == [100000, 120000, 140000]
    
    def test_to_dataframe_method_returns_pandas_dataframe(self, line_item_results):
        """Test to_dataframe method returns pandas DataFrame with correct data."""
        df = line_item_results.to_dataframe()
        
        assert isinstance(df, pd.DataFrame)
        assert df.index.tolist() == ["revenue"]
        assert df.columns.tolist() == [2023, 2024, 2025]
        assert df.loc["revenue"].values.tolist() == [100000, 120000, 140000]
    
    def test_to_series_uses_values_method(self, line_item_results):
        """Test that to_series method uses values method."""
        with patch.object(line_item_results, 'values') as mock_values:
            mock_values.return_value = {2023: 100000, 2024: 120000, 2025: 140000}
            
            series = line_item_results.to_series()
            
            mock_values.assert_called_once()
            assert series.name == "revenue"
    
    def test_to_dataframe_uses_values_method(self, line_item_results):
        """Test that to_dataframe method uses values method."""
        with patch.object(line_item_results, 'values') as mock_values:
            mock_values.return_value = {2023: 100000, 2024: 120000, 2025: 140000}
            
            df = line_item_results.to_dataframe()
            
            mock_values.assert_called_once()
            assert df.index.tolist() == ["revenue"]


class TestLineItemResultsTableMethod:
    """Test table method of LineItemResults."""
    
    @pytest.fixture
    def line_item_results(self, model_with_line_items):
        """Create a LineItemResults instance for testing."""
        return LineItemResults(model_with_line_items, "revenue")
    
    def test_table_method_returns_table(self, line_item_results):
        """Test table method returns a Table object."""
        with patch('pyproforma.tables.tables.Tables.line_item') as mock_line_item:
            mock_table = Mock()
            mock_line_item.return_value = mock_table
            
            result = line_item_results.table()
            
            mock_line_item.assert_called_once_with("revenue", include_name=False)
            assert result is mock_table
    
    def test_table_method_passes_item_name(self, line_item_results):
        """Test table method passes correct item name."""
        with patch('pyproforma.tables.tables.Tables.line_item') as mock_line_item:
            line_item_results.table()
            mock_line_item.assert_called_once_with("revenue", include_name=False)


class TestLineItemResultsChartMethods:
    """Test chart methods of LineItemResults."""
    
    @pytest.fixture
    def line_item_results(self, model_with_line_items):
        """Create a LineItemResults instance for testing."""
        return LineItemResults(model_with_line_items, "revenue")
    
    def test_chart_method_default_parameters(self, line_item_results):
        """Test chart method with default parameters."""
        with patch('pyproforma.charts.charts.Charts.line_item') as mock_line_item:
            mock_fig = Mock()
            mock_line_item.return_value = mock_fig
            
            result = line_item_results.chart()
            
            mock_line_item.assert_called_once_with(
                "revenue",
                width=800,
                height=600,
                template='plotly_white',
                chart_type='line'
            )
            assert result is mock_fig
    
    def test_chart_method_custom_parameters(self, line_item_results):
        """Test chart method with custom parameters."""
        with patch('pyproforma.charts.charts.Charts.line_item') as mock_line_item:
            mock_fig = Mock()
            mock_line_item.return_value = mock_fig
            
            result = line_item_results.chart(
                width=1000,
                height=800,
                template='plotly_dark',
                chart_type='bar'
            )
            
            mock_line_item.assert_called_once_with(
                "revenue",
                width=1000,
                height=800,
                template='plotly_dark',
                chart_type='bar'
            )
            assert result is mock_fig
    
    def test_chart_method_passes_item_name(self, line_item_results):
        """Test chart method passes correct item name."""
        with patch('pyproforma.charts.charts.Charts.line_item') as mock_line_item:
            line_item_results.chart()
            mock_line_item.assert_called_once_with(
                "revenue",
                width=800,
                height=600,
                template='plotly_white',
                chart_type='line'
            )
    
    def test_cumulative_percent_change_chart_method_default_parameters(self, line_item_results):
        """Test cumulative_percent_change_chart method with default parameters."""
        with patch('pyproforma.charts.charts.Charts.cumulative_percent_change') as mock_cumulative:
            mock_fig = Mock()
            mock_cumulative.return_value = mock_fig
            
            result = line_item_results.cumulative_percent_change_chart()
            
            mock_cumulative.assert_called_once_with(
                "revenue",
                width=800,
                height=600,
                template='plotly_white'
            )
            assert result is mock_fig
    
    def test_cumulative_percent_change_chart_method_custom_parameters(self, line_item_results):
        """Test cumulative_percent_change_chart method with custom parameters."""
        with patch('pyproforma.charts.charts.Charts.cumulative_percent_change') as mock_cumulative:
            mock_fig = Mock()
            mock_cumulative.return_value = mock_fig
            
            result = line_item_results.cumulative_percent_change_chart(
                width=1000,
                height=800,
                template='plotly_dark'
            )
            
            mock_cumulative.assert_called_once_with(
                "revenue",
                width=1000,
                height=800,
                template='plotly_dark'
            )
            assert result is mock_fig


class TestLineItemResultsHtmlRepr:
    """Test _repr_html_ method for Jupyter notebook integration."""
    
    @pytest.fixture
    def line_item_results(self, model_with_line_items):
        """Create a LineItemResults instance for testing."""
        return LineItemResults(model_with_line_items, "revenue")
    
    def test_repr_html_method(self, line_item_results):
        """Test _repr_html_ method returns HTML formatted summary."""
        html_result = line_item_results._repr_html_()
        
        assert html_result.startswith('<pre>')
        assert html_result.endswith('</pre>')
        assert "LineItemResults('revenue')" in html_result
        assert "Label: Revenue" in html_result
        assert '<br>' in html_result  # Newlines converted to HTML breaks
    
    def test_repr_html_converts_newlines(self, line_item_results):
        """Test _repr_html_ method converts newlines to HTML breaks."""
        html_result = line_item_results._repr_html_()
        
        # Should not contain literal newlines
        assert '\n' not in html_result
        # Should contain HTML line breaks
        assert '<br>' in html_result


class TestLineItemResultsErrorHandling:
    """Test error handling in LineItemResults."""
    
    @pytest.fixture
    def model_with_line_items_basic(self, basic_line_items, basic_categories):
        """Create a model with line items for testing."""
        return Model(
            line_items=basic_line_items,
            years=[2023, 2024, 2025],
            categories=basic_categories
        )
    
    def test_summary_handles_missing_value(self, model_with_line_items_basic):
        """Test summary method handles missing line item value gracefully."""
        line_item_results = LineItemResults(model_with_line_items_basic, "revenue")
        
        # Mock value to raise KeyError
        with patch.object(line_item_results.model, 'value', side_effect=KeyError):
            summary = line_item_results.summary()
            
            assert "LineItemResults('revenue')" in summary
            assert "Label: Revenue" in summary
            assert "Values: Not available" in summary
    
    def test_chart_method_with_chart_error(self, model_with_line_items_basic):
        """Test chart method when underlying chart method raises error."""
        line_item_results = LineItemResults(model_with_line_items_basic, "revenue")
        
        with patch('pyproforma.charts.charts.Charts.line_item', side_effect=KeyError("Chart error")):
            with pytest.raises(KeyError, match="Chart error"):
                line_item_results.chart()
    
    def test_table_method_with_table_error(self, model_with_line_items_basic):
        """Test table method when underlying table method raises error."""
        line_item_results = LineItemResults(model_with_line_items_basic, "revenue")
        
        with patch('pyproforma.tables.tables.Tables.line_item', side_effect=KeyError("Table error")):
            with pytest.raises(KeyError, match="Table error"):
                line_item_results.table()


class TestLineItemResultsIntegration:
    """Test LineItemResults integration with actual model methods."""
    
    @pytest.fixture
    def integrated_model(self):
        """Create a fully integrated model for testing."""
        line_items = [
            LineItem(
                name="revenue",
                category="income",
                label="Revenue",
                values={2023: 100000, 2024: 120000},
                value_format="no_decimals"
            ),
            LineItem(
                name="expenses",
                category="costs",
                label="Expenses",
                values={2023: 50000, 2024: 60000},
                value_format="no_decimals"
            )
        ]
        
        categories = [
            Category(name="income", label="Income"),
            Category(name="costs", label="Costs")
        ]
        
        return Model(
            line_items=line_items,
            years=[2023, 2024],
            categories=categories
        )
    
    def test_line_item_results_from_model_method(self, integrated_model):
        """Test creating LineItemResults through model.line_item() method."""
        line_item_results = integrated_model.line_item("revenue")
        
        assert isinstance(line_item_results, LineItemResults)
        assert line_item_results.item_name == "revenue"
        assert line_item_results.model is integrated_model
        
        # Test that methods work
        summary = line_item_results.summary()
        assert "LineItemResults('revenue')" in summary
        assert "Label: Revenue" in summary
    
    def test_line_item_results_string_representation_integration(self, integrated_model):
        """Test string representation with real model data."""
        line_item_results = integrated_model.line_item("revenue")
        
        str_result = str(line_item_results)
        assert "LineItemResults('revenue')" in str_result
        assert "Label: Revenue" in str_result
        assert "Values: 100,000, 120,000" in str_result
    
    def test_line_item_results_html_representation_integration(self, integrated_model):
        """Test HTML representation with real model data."""
        line_item_results = integrated_model.line_item("revenue")
        
        html_result = line_item_results._repr_html_()
        assert "<pre>" in html_result
        assert "</pre>" in html_result
        assert "LineItemResults('revenue')" in html_result
        assert "Label: Revenue" in html_result
        assert "<br>" in html_result
    
    def test_line_item_results_values_integration(self, integrated_model):
        """Test values method with real model data."""
        line_item_results = integrated_model.line_item("revenue")
        
        values = line_item_results.values()
        assert values == {2023: 100000, 2024: 120000}
    
    def test_line_item_results_pandas_integration(self, integrated_model):
        """Test pandas conversion methods with real model data."""
        line_item_results = integrated_model.line_item("revenue")
        
        # Test Series conversion
        series = line_item_results.to_series()
        assert isinstance(series, pd.Series)
        assert series.name == "revenue"
        assert series.loc[2023] == 100000
        assert series.loc[2024] == 120000
        
        # Test DataFrame conversion
        df = line_item_results.to_dataframe()
        assert isinstance(df, pd.DataFrame)
        assert df.index.tolist() == ["revenue"]
        assert df.loc["revenue", 2023] == 100000
        assert df.loc["revenue", 2024] == 120000


class TestLineItemResultsEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_line_item_results_with_special_characters_in_name(self):
        """Test LineItemResults with line item names containing special characters."""
        line_items = [
            LineItem(
                name="revenue_2024",
                category="income",
                label="Revenue 2024",
                values={2024: 100000},
                value_format="no_decimals"
            )
        ]
        
        categories = [Category(name="income", label="Income")]
        
        model = Model(
            line_items=line_items,
            years=[2024],
            categories=categories
        )
        
        line_item_results = LineItemResults(model, "revenue_2024")
        
        assert line_item_results.item_name == "revenue_2024"
        summary = line_item_results.summary()
        assert "LineItemResults('revenue_2024')" in summary
        assert "Label: Revenue 2024" in summary
        assert "Values: 100,000" in summary
    
    def test_line_item_results_with_single_year(self):
        """Test LineItemResults with model containing only one year."""
        line_items = [
            LineItem(
                name="revenue",
                category="income",
                values={2024: 100000},
                value_format="no_decimals"
            )
        ]
        
        categories = [Category(name="income", label="Income")]
        
        model = Model(
            line_items=line_items,
            years=[2024],
            categories=categories
        )
        
        line_item_results = LineItemResults(model, "revenue")
        
        values = line_item_results.values()
        assert values == {2024: 100000}
        
        series = line_item_results.to_series()
        assert len(series) == 1
        assert series.loc[2024] == 100000
    
    def test_line_item_results_with_different_value_formats(self):
        """Test LineItemResults with different value formats."""
        line_items = [
            LineItem(
                name="percentage_item",
                category="metrics",
                values={2024: 0.15},
                value_format="percent"
            ),
            LineItem(
                name="decimal_item",
                category="metrics",
                values={2024: 1234.56},
                value_format="two_decimals"
            )
        ]
        
        categories = [Category(name="metrics", label="Metrics")]
        
        model = Model(
            line_items=line_items,
            years=[2024],
            categories=categories
        )
        
        # Test percentage format
        percentage_results = LineItemResults(model, "percentage_item")
        assert percentage_results.value_format == "percent"
        
        # Test decimal format
        decimal_results = LineItemResults(model, "decimal_item")
        assert decimal_results.value_format == "two_decimals"


class TestLineItemResultsCalculationMethods:
    """Test the calculation methods added to LineItemResults."""
    
    @pytest.fixture
    def calculation_model(self):
        """Create a model for testing calculation methods."""
        line_items = [
            LineItem(
                name="revenue",
                category="income",
                values={2020: 100, 2021: 120, 2022: 150, 2023: 120},
                value_format="no_decimals"
            ),
            LineItem(
                name="expense",
                category="costs",
                values={2020: 50, 2021: 50, 2022: 75, 2023: 0},
                value_format="no_decimals"
            ),
            LineItem(
                name="zero_item",
                category="other",
                values={2020: 0, 2021: 10, 2022: 0, 2023: 5},
                value_format="no_decimals"
            )
        ]
        
        categories = [
            Category(name="income", label="Income"),
            Category(name="costs", label="Costs"),
            Category(name="other", label="Other")
        ]
        
        return Model(
            line_items=line_items,
            years=[2020, 2021, 2022, 2023],
            categories=categories
        )
    
    def test_percent_change_method(self, calculation_model):
        """Test percent_change method on LineItemResults."""
        revenue_item = calculation_model.line_item("revenue")
        
        # Revenue: 100 -> 120 = 20% increase = 0.2
        assert revenue_item.percent_change(2021) == 0.2
        
        # Revenue: 120 -> 150 = 25% increase = 0.25  
        assert revenue_item.percent_change(2022) == 0.25
        
        # Revenue: 150 -> 120 = -20% decrease = -0.2
        assert revenue_item.percent_change(2023) == -0.2
        
        # First year should return None
        assert revenue_item.percent_change(2020) is None
    
    def test_percent_change_with_zero_previous_value(self, calculation_model):
        """Test percent_change when previous value is zero."""
        zero_item = calculation_model.line_item("zero_item")
        
        # zero_item: 0 -> 10, can't calculate percent change from zero
        assert zero_item.percent_change(2021) is None
        
        # zero_item: 0 -> 5, can't calculate percent change from zero  
        assert zero_item.percent_change(2023) is None
    
    def test_cumulative_percent_change_method(self, calculation_model):
        """Test cumulative_percent_change method on LineItemResults."""
        revenue_item = calculation_model.line_item("revenue")
        
        # Base year (2020) should return 0
        assert revenue_item.cumulative_percent_change(2020) == 0
        
        # 2021: (120 - 100) / 100 = 0.2
        assert revenue_item.cumulative_percent_change(2021) == 0.2
        
        # 2022: (150 - 100) / 100 = 0.5
        assert revenue_item.cumulative_percent_change(2022) == 0.5
        
        # 2023: (120 - 100) / 100 = 0.2
        assert revenue_item.cumulative_percent_change(2023) == 0.2
    
    def test_cumulative_percent_change_with_start_year(self, calculation_model):
        """Test cumulative_percent_change with custom start year."""
        revenue_item = calculation_model.line_item("revenue")
        
        # Using 2021 as start year (120 as base)
        assert revenue_item.cumulative_percent_change(2021, start_year=2021) == 0
        # 2022: (150 - 120) / 120 = 0.25
        assert revenue_item.cumulative_percent_change(2022, start_year=2021) == 0.25
        # 2023: (120 - 120) / 120 = 0.0
        assert revenue_item.cumulative_percent_change(2023, start_year=2021) == 0.0
    
    def test_cumulative_change_method(self, calculation_model):
        """Test cumulative_change method on LineItemResults."""
        revenue_item = calculation_model.line_item("revenue")
        
        # Base year (2020) should return 0
        assert revenue_item.cumulative_change(2020) == 0
        
        # 2021: 120 - 100 = 20
        assert revenue_item.cumulative_change(2021) == 20
        
        # 2022: 150 - 100 = 50
        assert revenue_item.cumulative_change(2022) == 50
        
        # 2023: 120 - 100 = 20
        assert revenue_item.cumulative_change(2023) == 20
    
    def test_cumulative_change_with_start_year(self, calculation_model):
        """Test cumulative_change with custom start year."""
        revenue_item = calculation_model.line_item("revenue")
        
        # Using 2021 as start year (120 as base)
        assert revenue_item.cumulative_change(2021, start_year=2021) == 0
        # 2022: 150 - 120 = 30
        assert revenue_item.cumulative_change(2022, start_year=2021) == 30
        # 2023: 120 - 120 = 0
        assert revenue_item.cumulative_change(2023, start_year=2021) == 0
    
    def test_index_to_year_method(self, calculation_model):
        """Test index_to_year method on LineItemResults."""
        revenue_item = calculation_model.line_item("revenue")
        
        # Base year (2020) should return 100
        assert revenue_item.index_to_year(2020) == 100.0
        
        # 2021: (120 / 100) * 100 = 120.0
        assert revenue_item.index_to_year(2021) == 120.0
        
        # 2022: (150 / 100) * 100 = 150.0
        assert revenue_item.index_to_year(2022) == 150.0
        
        # 2023: (120 / 100) * 100 = 120.0
        assert revenue_item.index_to_year(2023) == 120.0
    
    def test_index_to_year_with_start_year(self, calculation_model):
        """Test index_to_year with custom start year."""
        revenue_item = calculation_model.line_item("revenue")
        
        # Using 2021 as start year (120 as base)
        assert revenue_item.index_to_year(2021, start_year=2021) == 100.0
        # 2022: (150 / 120) * 100 = 125.0
        assert revenue_item.index_to_year(2022, start_year=2021) == 125.0
        # 2023: (120 / 120) * 100 = 100.0
        assert revenue_item.index_to_year(2023, start_year=2021) == 100.0
    
    def test_index_to_year_with_zero_base_value(self, calculation_model):
        """Test index_to_year when base year value is zero."""
        zero_item = calculation_model.line_item("zero_item")
        
        # zero_start has 0 in 2020, so indexed calculation should return None
        assert zero_item.index_to_year(2021) is None
        assert zero_item.index_to_year(2022) is None
    
    def test_calculation_methods_error_handling(self, calculation_model):
        """Test error handling for calculation methods."""
        revenue_item = calculation_model.line_item("revenue")
        
        # Test invalid year
        with pytest.raises(KeyError) as excinfo:
            revenue_item.percent_change(2025)
        assert "Year 2025 not found in model years" in str(excinfo.value)
        
        with pytest.raises(KeyError) as excinfo:
            revenue_item.cumulative_percent_change(2025)
        assert "Year 2025 not found in model years" in str(excinfo.value)
        
        with pytest.raises(KeyError) as excinfo:
            revenue_item.cumulative_change(2025)
        assert "Year 2025 not found in model years" in str(excinfo.value)
        
        with pytest.raises(KeyError) as excinfo:
            revenue_item.index_to_year(2025)
        assert "Year 2025 not found in model years" in str(excinfo.value)
        
        # Test invalid start year
        with pytest.raises(KeyError) as excinfo:
            revenue_item.cumulative_percent_change(2021, start_year=2025)
        assert "Start year 2025 not found in model years" in str(excinfo.value)
    
    def test_calculation_methods_basic_functionality(self, calculation_model):
        """Test that LineItemResults calculation methods work correctly."""
        revenue_item = calculation_model.line_item("revenue")
        
        # Test percent_change
        assert revenue_item.percent_change(2020) is None  # First year
        assert revenue_item.percent_change(2021) == 0.2   # 20% increase
        
        # Test cumulative_percent_change  
        assert revenue_item.cumulative_percent_change(2020) == 0  # Base year
        assert revenue_item.cumulative_percent_change(2022) == 0.5  # 50% increase from base
        
        # Test cumulative_change
        assert revenue_item.cumulative_change(2020) == 0   # Base year
        assert revenue_item.cumulative_change(2022) == 50  # 50 increase from base
        
        # Test index_to_year
        assert revenue_item.index_to_year(2020) == 100.0  # Base year = 100
        assert revenue_item.index_to_year(2022) == 150.0  # 150% of base
        
        # Test cumulative
        assert revenue_item.cumulative() == 490  # 100 + 120 + 150 + 120 = 490
        assert revenue_item.cumulative([2020, 2021]) == 220  # 100 + 120 = 220
    
    def test_cumulative_method(self, calculation_model):
        """Test cumulative method on LineItemResults."""
        revenue_item = calculation_model.line_item("revenue")
        
        # Test with no years specified (should use all years)
        # Revenue values: 2020=100, 2021=120, 2022=150, 2023=120
        # Total: 100 + 120 + 150 + 120 = 490
        assert revenue_item.cumulative() == 490
        
        # Test with specific years
        assert revenue_item.cumulative([2020]) == 100
        assert revenue_item.cumulative([2020, 2021]) == 220  # 100 + 120
        assert revenue_item.cumulative([2021, 2022]) == 270  # 120 + 150
        assert revenue_item.cumulative([2020, 2022, 2023]) == 370  # 100 + 150 + 120
        
        # Test with all years explicitly
        assert revenue_item.cumulative([2020, 2021, 2022, 2023]) == 490
        
        # Test with years in different order
        assert revenue_item.cumulative([2023, 2020, 2022]) == 370  # 120 + 100 + 150
    
    def test_cumulative_method_with_zero_values(self, calculation_model):
        """Test cumulative method with line item that has zero values."""
        expense_item = calculation_model.line_item("expense")
        
        # Expense values: 2020=50, 2021=50, 2022=75, 2023=0
        # Total: 50 + 50 + 75 + 0 = 175
        assert expense_item.cumulative() == 175
        
        # Test with years including zero
        assert expense_item.cumulative([2023]) == 0
        assert expense_item.cumulative([2022, 2023]) == 75  # 75 + 0
    
    def test_cumulative_method_error_handling(self, calculation_model):
        """Test cumulative method error handling."""
        revenue_item = calculation_model.line_item("revenue")
        
        # Test with invalid year
        with pytest.raises(KeyError) as excinfo:
            revenue_item.cumulative([2025])
        assert "Year 2025 not found in model years" in str(excinfo.value)
        
        # Test with mix of valid and invalid years
        with pytest.raises(KeyError) as excinfo:
            revenue_item.cumulative([2020, 2025, 2021])
        assert "Year 2025 not found in model years" in str(excinfo.value)
        
        # Test with empty list (should return 0)
        assert revenue_item.cumulative([]) == 0
    
    def test_cumulative_method_with_none_values(self, calculation_model):
        """Test cumulative method when line item has None values."""
        # Create a mock line item that returns None for some years
        from unittest.mock import patch
        
        revenue_item = calculation_model.line_item("revenue")
        
        # Mock model.value to return None for 2021
        with patch.object(revenue_item.model, 'value') as mock_value:
            def side_effect(item_name, year):
                if item_name == "revenue" and year == 2021:
                    return None
                # Return original values for other years
                original_values = {2020: 100, 2021: 120, 2022: 150, 2023: 120}
                return original_values.get(year, 0)
            
            mock_value.side_effect = side_effect
            
            # Should treat None values as zero and return sum of non-None values
            # 100 (2020) + 0 (2021 None treated as 0) + 150 (2022) = 250
            assert revenue_item.cumulative([2020, 2021, 2022]) == 250
            
            # Should work fine with years that don't include the None value
            assert revenue_item.cumulative([2020, 2022]) == 250
