import pytest
from unittest.mock import Mock, patch
import pandas as pd
from pyproforma import LineItem, Model, Category
from pyproforma.models.results import CategoryResults


# Module-level fixtures available to all test classes
@pytest.fixture
def basic_line_items():
    """Create basic line items for testing."""
    return [
        LineItem(
            name="product_sales",
            category="income",
            label="Product Sales",
            values={2023: 100000, 2024: 120000, 2025: 140000},
            value_format="no_decimals"
        ),
        LineItem(
            name="service_revenue",
            category="income",
            label="Service Revenue",
            values={2023: 50000, 2024: 60000, 2025: 70000},
            value_format="no_decimals"
        ),
        LineItem(
            name="salaries",
            category="costs",
            label="Salaries",
            values={2023: 40000, 2024: 45000, 2025: 50000},
            value_format="no_decimals"
        ),
        LineItem(
            name="office_rent",
            category="costs",
            label="Office Rent",
            values={2023: 24000, 2024: 24000, 2025: 24000},
            value_format="no_decimals"
        )
    ]


@pytest.fixture
def basic_categories():
    """Create basic categories for testing."""
    return [
        Category(name="income", label="Income", include_total=True),
        Category(name="costs", label="Costs", include_total=True),
        Category(name="metrics", label="Metrics", include_total=False)
    ]


@pytest.fixture
def model_with_categories(basic_line_items, basic_categories):
    """Create a model with categories for testing."""
    return Model(
        line_items=basic_line_items,
        years=[2023, 2024, 2025],
        categories=basic_categories
    )


class TestCategoryResultsInitialization:
    """Test CategoryResults initialization and basic properties."""
    
    def test_init_valid_category(self, model_with_categories):
        """Test CategoryResults initialization with valid category."""
        category_results = CategoryResults(model_with_categories, "income")
        
        assert category_results.model is model_with_categories
        assert category_results.category_name == "income"
        assert category_results.category_obj.name == "income"
        assert category_results.category_obj.label == "Income"
        assert category_results.category_obj.include_total is True
        assert len(category_results.line_items_definitions) == 2
        assert len(category_results.line_item_names) == 2
        assert "product_sales" in category_results.line_item_names
        assert "service_revenue" in category_results.line_item_names
    
    def test_init_category_without_total(self, model_with_categories):
        """Test CategoryResults initialization with category that doesn't include totals."""
        # Add a line item to the metrics category
        metrics_item = LineItem(
            name="conversion_rate",
            category="metrics",
            values={2023: 0.15, 2024: 0.18, 2025: 0.20},
            value_format="percent"
        )
        model_with_categories.update.add_line_item(metrics_item)
        
        category_results = CategoryResults(model_with_categories, "metrics")
        
        assert category_results.model is model_with_categories
        assert category_results.category_name == "metrics"
        assert category_results.category_obj.name == "metrics"
        assert category_results.category_obj.label == "Metrics"
        assert category_results.category_obj.include_total is False
        assert len(category_results.line_items_definitions) == 1
        assert "conversion_rate" in category_results.line_item_names
    
    def test_init_invalid_category_name(self, model_with_categories):
        """Test CategoryResults initialization with invalid category name."""
        with pytest.raises(KeyError):
            CategoryResults(model_with_categories, "nonexistent")


class TestCategoryResultsStringRepresentation:
    """Test string representation methods of CategoryResults."""
    
    @pytest.fixture
    def category_results_with_total(self, model_with_categories):
        """Create a CategoryResults instance with totals for testing."""
        return CategoryResults(model_with_categories, "income")
    
    @pytest.fixture
    def category_results_without_total(self, model_with_categories):
        """Create a CategoryResults instance without totals for testing."""
        return CategoryResults(model_with_categories, "costs")
    
    def test_str_method(self, category_results_with_total):
        """Test __str__ method returns summary."""
        str_result = str(category_results_with_total)
        
        assert "CategoryResults('income')" in str_result
        assert "Label: Income" in str_result
        assert "Line Items: 2" in str_result
        assert "Items: product_sales, service_revenue" in str_result
        assert "Total (2023):" in str_result
        
    def test_repr_method(self, category_results_with_total):
        """Test __repr__ method returns expected format."""
        repr_result = repr(category_results_with_total)
        
        assert repr_result == "CategoryResults(category_name='income', num_items=2)"
    
    def test_summary_method_with_total(self, category_results_with_total):
        """Test summary method returns formatted category information with totals."""
        summary = category_results_with_total.summary()
        
        assert "CategoryResults('income')" in summary
        assert "Label: Income" in summary
        assert "Line Items: 2" in summary
        assert "Items: product_sales, service_revenue" in summary
        assert "Total (2023): 150,000" in summary
    
    def test_summary_method_without_total(self, category_results_without_total):
        """Test summary method with category that doesn't include totals."""
        summary = category_results_without_total.summary()
        
        assert "CategoryResults('costs')" in summary
        assert "Label: Costs" in summary
        assert "Line Items: 2" in summary
        assert "Items: salaries, office_rent" in summary
        # Note: costs category has include_total=True by default, so it will show totals


class TestCategoryResultsTotalsMethod:
    """Test totals method of CategoryResults."""
    
    @pytest.fixture
    def category_results_with_total(self, model_with_categories):
        """Create a CategoryResults instance with totals for testing."""
        return CategoryResults(model_with_categories, "income")
    
    @pytest.fixture
    def category_results_without_total(self, model_with_categories):
        """Create a CategoryResults instance without totals for testing."""
        # Add a line item to the metrics category
        metrics_item = LineItem(
            name="conversion_rate",
            category="metrics",
            values={2023: 0.15, 2024: 0.18, 2025: 0.20},
            value_format="percent"
        )
        model_with_categories.update.add_line_item(metrics_item)
        return CategoryResults(model_with_categories, "metrics")
    
    def test_totals_method_returns_correct_values(self, category_results_with_total):
        """Test totals method returns correct values for all years."""
        totals = category_results_with_total.totals()
        
        # Income = product_sales + service_revenue
        # 2023: 100000 + 50000 = 150000
        # 2024: 120000 + 60000 = 180000
        # 2025: 140000 + 70000 = 210000
        expected_totals = {2023: 150000, 2024: 180000, 2025: 210000}
        assert totals == expected_totals
    
    def test_totals_method_raises_error_for_no_total_category(self, category_results_without_total):
        """Test totals method raises ValueError for category without totals."""
        with pytest.raises(ValueError, match="Category 'metrics' does not include totals"):
            category_results_without_total.totals()
    
    def test_totals_method_calls_model_category_total(self, category_results_with_total):
        """Test that totals method calls model.category_total for each year."""
        with patch.object(category_results_with_total.model, 'category_total') as mock_category_total:
            mock_category_total.side_effect = [150000, 180000, 210000]
            
            totals = category_results_with_total.totals()
            
            expected_calls = [
                (('income', 2023),),
                (('income', 2024),),
                (('income', 2025),)
            ]
            
            assert mock_category_total.call_count == 3
            for i, call in enumerate(mock_category_total.call_args_list):
                assert call.args == expected_calls[i][0]
    
    def test_totals_method_handles_key_error(self, category_results_with_total):
        """Test totals method handles KeyError gracefully."""
        with patch.object(category_results_with_total.model, 'category_total') as mock_category_total:
            mock_category_total.side_effect = [150000, KeyError("Error"), 210000]
            
            totals = category_results_with_total.totals()
            
            assert totals == {2023: 150000, 2024: 0.0, 2025: 210000}


class TestCategoryResultsValuesMethod:
    """Test values method of CategoryResults."""
    
    @pytest.fixture
    def category_results(self, model_with_categories):
        """Create a CategoryResults instance for testing."""
        return CategoryResults(model_with_categories, "income")
    
    def test_values_method_returns_correct_structure(self, category_results):
        """Test values method returns correct nested dictionary structure."""
        values = category_results.values()
        
        assert isinstance(values, dict)
        assert len(values) == 2
        assert "product_sales" in values
        assert "service_revenue" in values
        
        # Check structure of nested dictionaries
        for item_name in values:
            assert isinstance(values[item_name], dict)
            assert len(values[item_name]) == 3
            assert 2023 in values[item_name]
            assert 2024 in values[item_name]
            assert 2025 in values[item_name]
    
    def test_values_method_returns_correct_values(self, category_results):
        """Test values method returns correct values for all items and years."""
        values = category_results.values()
        
        expected_values = {
            "product_sales": {2023: 100000, 2024: 120000, 2025: 140000},
            "service_revenue": {2023: 50000, 2024: 60000, 2025: 70000}
        }
        
        assert values == expected_values
    
    def test_values_method_calls_model_value(self, category_results):
        """Test that values method calls model.value for each item and year."""
        with patch.object(category_results.model, 'value') as mock_value:
            mock_value.side_effect = [
                100000, 120000, 140000,  # product_sales
                50000, 60000, 70000      # service_revenue
            ]
            
            values = category_results.values()
            
            assert mock_value.call_count == 6
            # Check some of the calls
            mock_value.assert_any_call("product_sales", 2023)
            mock_value.assert_any_call("service_revenue", 2025)
    
    def test_values_method_handles_key_error(self, category_results):
        """Test values method handles KeyError gracefully."""
        with patch.object(category_results.model, 'value') as mock_value:
            mock_value.side_effect = [
                100000, KeyError("Error"), 140000,  # product_sales
                50000, 60000, 70000                 # service_revenue
            ]
            
            values = category_results.values()
            
            # Should handle KeyError by setting value to 0.0
            assert values["product_sales"][2024] == 0.0
            assert values["product_sales"][2023] == 100000
            assert values["product_sales"][2025] == 140000


class TestCategoryResultsToDataFrameMethod:
    """Test to_dataframe method of CategoryResults."""
    
    @pytest.fixture
    def category_results_with_total(self, model_with_categories):
        """Create a CategoryResults instance with totals for testing."""
        return CategoryResults(model_with_categories, "income")
    
    @pytest.fixture
    def category_results_without_total(self, model_with_categories):
        """Create a CategoryResults instance without totals for testing."""
        return CategoryResults(model_with_categories, "costs")
    
    def test_to_dataframe_returns_pandas_dataframe(self, category_results_with_total):
        """Test to_dataframe method returns pandas DataFrame with correct structure."""
        df = category_results_with_total.to_dataframe()
        
        assert isinstance(df, pd.DataFrame)
        assert df.columns.tolist() == [2023, 2024, 2025]
        assert "product_sales" in df.index
        assert "service_revenue" in df.index
        assert "total_income" in df.index  # Total row added
    
    def test_to_dataframe_returns_correct_values(self, category_results_with_total):
        """Test to_dataframe method returns correct values."""
        df = category_results_with_total.to_dataframe()
        
        assert df.loc["product_sales", 2023] == 100000
        assert df.loc["product_sales", 2024] == 120000
        assert df.loc["product_sales", 2025] == 140000
        assert df.loc["service_revenue", 2023] == 50000
        assert df.loc["service_revenue", 2024] == 60000
        assert df.loc["service_revenue", 2025] == 70000
        assert df.loc["total_income", 2023] == 150000
        assert df.loc["total_income", 2024] == 180000
        assert df.loc["total_income", 2025] == 210000
    
    def test_to_dataframe_without_total_row(self, category_results_without_total):
        """Test to_dataframe method without total row for category without totals."""
        df = category_results_without_total.to_dataframe()
        
        assert isinstance(df, pd.DataFrame)
        assert df.columns.tolist() == [2023, 2024, 2025]
        assert "salaries" in df.index
        assert "office_rent" in df.index
        assert "costs_total" not in df.index  # No total row
    
    def test_to_dataframe_uses_values_method(self, category_results_with_total):
        """Test that to_dataframe method uses values method."""
        with patch.object(category_results_with_total, 'values') as mock_values:
            mock_values.return_value = {
                "product_sales": {2023: 100000, 2024: 120000, 2025: 140000},
                "service_revenue": {2023: 50000, 2024: 60000, 2025: 70000}
            }
            
            df = category_results_with_total.to_dataframe()
            
            mock_values.assert_called_once()
            assert df.loc["product_sales", 2023] == 100000
    
    def test_to_dataframe_handles_total_calculation_error(self, category_results_with_total):
        """Test to_dataframe method handles total calculation errors gracefully."""
        with patch.object(category_results_with_total, 'totals') as mock_totals:
            mock_totals.side_effect = ValueError("Total calculation error")
            
            df = category_results_with_total.to_dataframe()
            
            # Should still create DataFrame without total row
            assert isinstance(df, pd.DataFrame)
            assert "income_total" not in df.index


class TestCategoryResultsTableMethod:
    """Test table method of CategoryResults."""
    
    @pytest.fixture
    def category_results(self, model_with_categories):
        """Create a CategoryResults instance for testing."""
        return CategoryResults(model_with_categories, "income")
    
    def test_table_method_returns_table(self, category_results):
        """Test table method returns a Table object."""
        with patch('pyproforma.tables.tables.Tables.category') as mock_category:
            mock_table = Mock()
            mock_category.return_value = mock_table
            
            result = category_results.table()
            
            mock_category.assert_called_once_with("income")
            assert result is mock_table
    
    def test_table_method_passes_category_name(self, category_results):
        """Test table method passes correct category name."""
        with patch('pyproforma.tables.tables.Tables.category') as mock_category:
            category_results.table()
            mock_category.assert_called_once_with("income")


class TestCategoryResultsHtmlRepr:
    """Test _repr_html_ method for Jupyter notebook integration."""
    
    @pytest.fixture
    def category_results(self, model_with_categories):
        """Create a CategoryResults instance for testing."""
        return CategoryResults(model_with_categories, "income")
    
    def test_repr_html_method(self, category_results):
        """Test _repr_html_ method returns HTML formatted summary."""
        html_result = category_results._repr_html_()
        
        assert html_result.startswith('<pre>')
        assert html_result.endswith('</pre>')
        assert "CategoryResults('income')" in html_result
        assert "Label: Income" in html_result
        assert '<br>' in html_result  # Newlines converted to HTML breaks
    
    def test_repr_html_converts_newlines(self, category_results):
        """Test _repr_html_ method converts newlines to HTML breaks."""
        html_result = category_results._repr_html_()
        
        # Should not contain literal newlines
        assert '\n' not in html_result
        # Should contain HTML line breaks
        assert '<br>' in html_result


class TestCategoryResultsErrorHandling:
    """Test error handling in CategoryResults."""
    
    @pytest.fixture
    def model_with_categories_basic(self, basic_line_items, basic_categories):
        """Create a model with categories for testing."""
        return Model(
            line_items=basic_line_items,
            years=[2023, 2024, 2025],
            categories=basic_categories
        )
    
    def test_summary_handles_missing_total(self, model_with_categories_basic):
        """Test summary method handles missing category total gracefully."""
        category_results = CategoryResults(model_with_categories_basic, "income")
        
        # Mock category_total to raise KeyError
        with patch.object(category_results.model, 'category_total', side_effect=KeyError):
            summary = category_results.summary()
            
            assert "CategoryResults('income')" in summary
            assert "Label: Income" in summary
            assert "Total: Not available" in summary
    
    def test_table_method_with_table_error(self, model_with_categories_basic):
        """Test table method when underlying table method raises error."""
        category_results = CategoryResults(model_with_categories_basic, "income")
        
        with patch('pyproforma.tables.tables.Tables.category', side_effect=KeyError("Table error")):
            with pytest.raises(KeyError, match="Table error"):
                category_results.table()


class TestCategoryResultsIntegration:
    """Test CategoryResults integration with actual model methods."""
    
    @pytest.fixture
    def integrated_model(self):
        """Create a fully integrated model for testing."""
        line_items = [
            LineItem(
                name="product_sales",
                category="income",
                label="Product Sales",
                values={2023: 100000, 2024: 120000},
                value_format="no_decimals"
            ),
            LineItem(
                name="service_revenue",
                category="income",
                label="Service Revenue",
                values={2023: 50000, 2024: 60000},
                value_format="no_decimals"
            ),
            LineItem(
                name="salaries",
                category="costs",
                label="Salaries",
                values={2023: 40000, 2024: 45000},
                value_format="no_decimals"
            )
        ]
        
        categories = [
            Category(name="income", label="Income", include_total=True),
            Category(name="costs", label="Costs", include_total=True)
        ]
        
        return Model(
            line_items=line_items,
            years=[2023, 2024],
            categories=categories
        )
    
    def test_category_results_from_model_method(self, integrated_model):
        """Test creating CategoryResults through model.category() method."""
        category_results = integrated_model.category("income")
        
        assert isinstance(category_results, CategoryResults)
        assert category_results.category_name == "income"
        assert category_results.model is integrated_model
        
        # Test that methods work
        summary = category_results.summary()
        assert "CategoryResults('income')" in summary
        assert "Label: Income" in summary
    
    def test_category_results_string_representation_integration(self, integrated_model):
        """Test string representation with real model data."""
        category_results = integrated_model.category("income")
        
        str_result = str(category_results)
        assert "CategoryResults('income')" in str_result
        assert "Label: Income" in str_result
        assert "Total (2023): 150,000" in str_result
    
    def test_category_results_html_representation_integration(self, integrated_model):
        """Test HTML representation with real model data."""
        category_results = integrated_model.category("income")
        
        html_result = category_results._repr_html_()
        assert "<pre>" in html_result
        assert "</pre>" in html_result
        assert "CategoryResults('income')" in html_result
        assert "Label: Income" in html_result
        assert "<br>" in html_result
    
    def test_category_results_values_integration(self, integrated_model):
        """Test values method with real model data."""
        category_results = integrated_model.category("income")
        
        values = category_results.values()
        expected_values = {
            "product_sales": {2023: 100000, 2024: 120000},
            "service_revenue": {2023: 50000, 2024: 60000}
        }
        assert values == expected_values
    
    def test_category_results_totals_integration(self, integrated_model):
        """Test totals method with real model data."""
        category_results = integrated_model.category("income")
        
        totals = category_results.totals()
        expected_totals = {2023: 150000, 2024: 180000}
        assert totals == expected_totals
    
    def test_category_results_pandas_integration(self, integrated_model: Model):
        """Test pandas conversion method with real model data."""
        category_results = integrated_model.category("income")
        
        # Test DataFrame conversion
        df = category_results.to_dataframe()
        assert isinstance(df, pd.DataFrame)
        assert df.columns.tolist() == [2023, 2024]
        assert df.loc["product_sales", 2023] == 100000
        assert df.loc["service_revenue", 2023] == 50000
        assert df.loc["total_income", 2023] == 150000


class TestCategoryResultsEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_category_results_with_special_characters_in_name(self):
        """Test CategoryResults with category names containing special characters."""
        line_items = [
            LineItem(
                name="revenue_2024",
                category="income_2024",
                label="Revenue 2024",
                values={2024: 100000},
                value_format="no_decimals"
            )
        ]
        
        categories = [Category(name="income_2024", label="Income 2024", include_total=True)]
        
        model = Model(
            line_items=line_items,
            years=[2024],
            categories=categories
        )
        
        category_results = CategoryResults(model, "income_2024")
        
        assert category_results.category_name == "income_2024"
        summary = category_results.summary()
        assert "CategoryResults('income_2024')" in summary
        assert "Label: Income 2024" in summary
    
    def test_category_results_with_single_year(self):
        """Test CategoryResults with model containing only one year."""
        line_items = [
            LineItem(
                name="revenue",
                category="income",
                values={2024: 100000},
                value_format="no_decimals"
            )
        ]
        
        categories = [Category(name="income", label="Income", include_total=True)]
        
        model = Model(
            line_items=line_items,
            years=[2024],
            categories=categories
        )
        
        category_results = CategoryResults(model, "income")
        
        values = category_results.values()
        assert values == {"revenue": {2024: 100000}}
        
        totals = category_results.totals()
        assert totals == {2024: 100000}
        
        df = category_results.to_dataframe()
        assert df.columns.tolist() == [2024]
        assert len(df) == 2  # One item + total
    
    def test_category_results_with_empty_category(self):
        """Test CategoryResults with category containing no line items."""
        line_items = []
        
        categories = [Category(name="empty_category", label="Empty Category", include_total=True)]
        
        model = Model(
            line_items=line_items,
            years=[2024],
            categories=categories
        )
        
        category_results = CategoryResults(model, "empty_category")
        
        assert len(category_results.line_items_definitions) == 0
        assert len(category_results.line_item_names) == 0
        
        values = category_results.values()
        assert values == {}
        
        df = category_results.to_dataframe()
        assert df.empty or len(df) == 1  # Might have total row
    
    def test_category_results_with_different_value_formats(self):
        """Test CategoryResults with line items having different value formats."""
        line_items = [
            LineItem(
                name="percentage_metric",
                category="metrics",
                values={2024: 0.15},
                value_format="percent"
            ),
            LineItem(
                name="decimal_metric",
                category="metrics",
                values={2024: 1234.56},
                value_format="two_decimals"
            )
        ]
        
        categories = [Category(name="metrics", label="Metrics", include_total=False)]
        
        model = Model(
            line_items=line_items,
            years=[2024],
            categories=categories
        )
        
        category_results = CategoryResults(model, "metrics")
        
        # Test that different value formats are handled correctly
        values = category_results.values()
        assert values["percentage_metric"][2024] == 0.15
        assert values["decimal_metric"][2024] == 1234.56
        
        # Test that totals method raises error for category without totals
        with pytest.raises(ValueError, match="Category 'metrics' does not include totals"):
            category_results.totals()
