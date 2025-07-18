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
        assert "Value (2023):" in str_result
        
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
        assert "Value (2023): 100,000" in summary
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
    
    def test_values_method_calls_model_get_value(self, line_item_results):
        """Test that values method calls model.get_value for each year."""
        with patch.object(line_item_results.model, 'get_value') as mock_get_value:
            mock_get_value.side_effect = [100000, 120000, 140000]
            
            values = line_item_results.values()
            
            expected_calls = [
                (('revenue', 2023),),
                (('revenue', 2024),),
                (('revenue', 2025),)
            ]
            
            assert mock_get_value.call_count == 3
            for i, call in enumerate(mock_get_value.call_args_list):
                assert call.args == expected_calls[i][0]
    
    def test_value_method_calls_model_get_value(self, line_item_results):
        """Test that value method calls model.get_value with correct parameters."""
        with patch.object(line_item_results.model, 'get_value') as mock_get_value:
            mock_get_value.return_value = 100000
            
            result = line_item_results.value(2023)
            
            mock_get_value.assert_called_once_with("revenue", 2023)
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
            
            mock_line_item.assert_called_once_with("revenue")
            assert result is mock_table
    
    def test_table_method_passes_item_name(self, line_item_results):
        """Test table method passes correct item name."""
        with patch('pyproforma.tables.tables.Tables.line_item') as mock_line_item:
            line_item_results.table()
            mock_line_item.assert_called_once_with("revenue")


class TestLineItemResultsChartMethods:
    """Test chart methods of LineItemResults."""
    
    @pytest.fixture
    def line_item_results(self, model_with_line_items):
        """Create a LineItemResults instance for testing."""
        return LineItemResults(model_with_line_items, "revenue")
    
    def test_chart_method_default_parameters(self, line_item_results):
        """Test chart method with default parameters."""
        with patch('pyproforma.charts.charts.Charts.item') as mock_item:
            mock_fig = Mock()
            mock_item.return_value = mock_fig
            
            result = line_item_results.chart()
            
            mock_item.assert_called_once_with(
                "revenue",
                width=800,
                height=600,
                template='plotly_white',
                chart_type='line'
            )
            assert result is mock_fig
    
    def test_chart_method_custom_parameters(self, line_item_results):
        """Test chart method with custom parameters."""
        with patch('pyproforma.charts.charts.Charts.item') as mock_item:
            mock_fig = Mock()
            mock_item.return_value = mock_fig
            
            result = line_item_results.chart(
                width=1000,
                height=800,
                template='plotly_dark',
                chart_type='bar'
            )
            
            mock_item.assert_called_once_with(
                "revenue",
                width=1000,
                height=800,
                template='plotly_dark',
                chart_type='bar'
            )
            assert result is mock_fig
    
    def test_chart_method_passes_item_name(self, line_item_results):
        """Test chart method passes correct item name."""
        with patch('pyproforma.charts.charts.Charts.item') as mock_item:
            line_item_results.chart()
            mock_item.assert_called_once_with(
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
        
        # Mock get_value to raise KeyError
        with patch.object(line_item_results.model, 'get_value', side_effect=KeyError):
            summary = line_item_results.summary()
            
            assert "LineItemResults('revenue')" in summary
            assert "Label: Revenue" in summary
            assert "Value: Not available" in summary
    
    def test_chart_method_with_chart_error(self, model_with_line_items_basic):
        """Test chart method when underlying chart method raises error."""
        line_item_results = LineItemResults(model_with_line_items_basic, "revenue")
        
        with patch('pyproforma.charts.charts.Charts.item', side_effect=KeyError("Chart error")):
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
        assert "Value (2023): 100,000" in str_result
    
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
        assert "Value (2024): 100,000" in summary
    
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
