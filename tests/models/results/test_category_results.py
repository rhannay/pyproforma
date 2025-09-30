from unittest.mock import Mock, patch

import pandas as pd
import pytest

from pyproforma import Category, LineItem, Model
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
            value_format="no_decimals",
        ),
        LineItem(
            name="service_revenue",
            category="income",
            label="Service Revenue",
            values={2023: 50000, 2024: 60000, 2025: 70000},
            value_format="no_decimals",
        ),
        LineItem(
            name="salaries",
            category="costs",
            label="Salaries",
            values={2023: 40000, 2024: 45000, 2025: 50000},
            value_format="no_decimals",
        ),
        LineItem(
            name="office_rent",
            category="costs",
            label="Office Rent",
            values={2023: 24000, 2024: 24000, 2025: 24000},
            value_format="no_decimals",
        ),
    ]


@pytest.fixture
def basic_categories():
    """Create basic categories for testing."""
    return [
        Category(name="income", label="Income", include_total=True),
        Category(name="costs", label="Costs", include_total=True),
        Category(name="metrics", label="Metrics", include_total=False),
    ]


@pytest.fixture
def model_with_categories(basic_line_items, basic_categories):
    """Create a model with categories for testing."""
    return Model(
        line_items=basic_line_items,
        years=[2023, 2024, 2025],
        categories=basic_categories,
    )


class TestCategoryResultsInitialization:
    """Test CategoryResults initialization and basic properties."""

    def test_init_valid_category(self, model_with_categories):
        """Test CategoryResults initialization with valid category."""
        category_results = CategoryResults(model_with_categories, "income")

        assert category_results.model is model_with_categories
        assert category_results.name == "income"
        assert len(category_results.line_item_names) == 2
        assert "product_sales" in category_results.line_item_names
        assert "service_revenue" in category_results.line_item_names

    def test_init_category_without_total(self, model_with_categories):
        """Test CategoryResults initialization with category that doesn't include totals."""  # noqa: E501
        # Add a line item to the metrics category
        metrics_item = LineItem(
            name="conversion_rate",
            category="metrics",
            values={2023: 0.15, 2024: 0.18, 2025: 0.20},
            value_format="percent",
        )
        model_with_categories.update.add_line_item(metrics_item)

        category_results = CategoryResults(model_with_categories, "metrics")

        assert category_results.model is model_with_categories
        assert category_results.name == "metrics"
        assert category_results._category_metadata["name"] == "metrics"
        assert category_results._category_metadata["label"] == "Metrics"
        assert category_results._category_metadata["include_total"] is False
        assert len(category_results.line_item_names) == 1
        assert "conversion_rate" in category_results.line_item_names

    def test_init_invalid_category_name(self, model_with_categories):
        """Test CategoryResults initialization with invalid category name."""
        with pytest.raises(KeyError):
            CategoryResults(model_with_categories, "nonexistent")


class TestCategoryResultsProperties:
    """Test property access and modification for CategoryResults."""

    @pytest.fixture
    def model_for_property_tests(self):
        """Create a model specifically for property testing."""
        model = Model(years=[2024, 2025])
        model.update.add_category(name="revenue", label="Revenue Items")
        model.update.add_line_item(
            name="sales", category="revenue", values={2024: 100000, 2025: 110000}
        )
        return model

    def test_name_getter(self, model_for_property_tests):
        """Test that the name property returns the correct category name."""
        category_results = CategoryResults(model_for_property_tests, "revenue")
        assert category_results.name == "revenue"

    def test_name_setter_basic(self, model_for_property_tests):
        """Test that the name setter updates the category name in the model."""
        category_results = CategoryResults(model_for_property_tests, "revenue")

        # Change the name
        category_results.name = "sales_revenue"

        # Verify the CategoryResults object has the new name
        assert category_results.name == "sales_revenue"

        # Verify the line item's category was updated in the model
        sales_item = model_for_property_tests._line_item_definition("sales")
        assert sales_item.category == "sales_revenue"

        # Verify we can access the category with the new name
        new_category_results = CategoryResults(
            model_for_property_tests, "sales_revenue"
        )
        assert new_category_results.name == "sales_revenue"
        assert "sales" in new_category_results.line_item_names

    def test_name_setter_with_invalid_name(self, model_for_property_tests):
        """Test that the name setter raises appropriate errors for invalid names."""
        category_results = CategoryResults(model_for_property_tests, "revenue")

        # Test setting to an existing category name should fail
        model_for_property_tests.update.add_category(name="expenses")

        with pytest.raises(ValueError):
            category_results.name = "expenses"

        # Verify the original name is unchanged after the failed update
        assert category_results.name == "revenue"

    def test_name_setter_preserves_state_on_failure(self, model_for_property_tests):
        """Test that the CategoryResults state is preserved if the setter fails."""
        category_results = CategoryResults(model_for_property_tests, "revenue")
        original_name = category_results.name

        # Add another category to create a conflict
        model_for_property_tests.update.add_category(name="existing_category")

        # Try to set to an existing name (should fail)
        with pytest.raises(ValueError):
            category_results.name = "existing_category"

        # Verify the original state is preserved
        assert category_results.name == original_name
        assert category_results.line_item_names == ["sales"]

    def test_label_getter(self, model_for_property_tests):
        """Test that the label property returns the correct category label."""
        category_results = CategoryResults(model_for_property_tests, "revenue")
        assert category_results.label == "Revenue Items"

    def test_label_setter_basic(self, model_for_property_tests):
        """Test that the label setter updates the category label in the model."""
        category_results = CategoryResults(model_for_property_tests, "revenue")

        # Change the label
        category_results.label = "Sales Revenue"

        # Verify the CategoryResults object has the new label
        assert category_results.label == "Sales Revenue"

        # Verify the category definition was updated in the model
        category_def = next(
            cat
            for cat in model_for_property_tests._category_definitions
            if cat.name == "revenue"
        )
        assert category_def.label == "Sales Revenue"

    def test_label_setter_preserves_state_on_failure(self, model_for_property_tests):
        """Test that CategoryResults state is preserved if label setter fails."""
        category_results = CategoryResults(model_for_property_tests, "revenue")
        original_label = category_results.label

        # Try to create a scenario that might cause an update failure
        # Note: Since label updates are generally safe, we'll simulate this
        # by temporarily breaking the model reference
        original_model = category_results.model
        category_results.model = None

        try:
            with pytest.raises(AttributeError):
                category_results.label = "New Label"
        finally:
            # Restore the model reference
            category_results.model = original_model

        # Verify the original state is preserved
        assert category_results.label == original_label


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
        assert "Totals:" in str_result

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
        assert "Totals: 150,000, 180,000, 210,000" in summary

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
            value_format="percent",
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

    def test_totals_method_raises_error_for_no_total_category(
        self, category_results_without_total
    ):
        """Test totals method raises ValueError for category without totals."""
        with pytest.raises(
            ValueError, match="Category 'metrics' does not include totals"
        ):
            category_results_without_total.totals()

    def test_totals_method_calls_model_category_total(
        self, category_results_with_total
    ):
        """Test that totals method calls model.category_total for each year."""
        with patch.object(
            category_results_with_total.model, "category_total"
        ) as mock_category_total:
            mock_category_total.side_effect = [150000, 180000, 210000]

            category_results_with_total.totals()

            expected_calls = [
                (("income", 2023),),
                (("income", 2024),),
                (("income", 2025),),
            ]

            assert mock_category_total.call_count == 3
            for i, call in enumerate(mock_category_total.call_args_list):
                assert call.args == expected_calls[i][0]

    def test_totals_method_handles_key_error(self, category_results_with_total):
        """Test totals method handles KeyError gracefully."""
        with patch.object(
            category_results_with_total.model, "category_total"
        ) as mock_category_total:
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
            "service_revenue": {2023: 50000, 2024: 60000, 2025: 70000},
        }

        assert values == expected_values

    def test_values_method_calls_model_value(self, category_results):
        """Test that values method calls model.value for each item and year."""
        with patch.object(category_results.model, "value") as mock_value:
            mock_value.side_effect = [
                100000,
                120000,
                140000,  # product_sales
                50000,
                60000,
                70000,  # service_revenue
            ]

            category_results.values()

            assert mock_value.call_count == 6
            # Check some of the calls
            mock_value.assert_any_call("product_sales", 2023)
            mock_value.assert_any_call("service_revenue", 2025)

    def test_values_method_handles_key_error(self, category_results):
        """Test values method handles KeyError gracefully."""
        with patch.object(category_results.model, "value") as mock_value:
            mock_value.side_effect = [
                100000,
                KeyError("Error"),
                140000,  # product_sales
                50000,
                60000,
                70000,  # service_revenue
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
        with patch.object(category_results_with_total, "values") as mock_values:
            mock_values.return_value = {
                "product_sales": {2023: 100000, 2024: 120000, 2025: 140000},
                "service_revenue": {2023: 50000, 2024: 60000, 2025: 70000},
            }

            df = category_results_with_total.to_dataframe()

            mock_values.assert_called_once()
            assert df.loc["product_sales", 2023] == 100000

    def test_to_dataframe_handles_total_calculation_error(
        self, category_results_with_total
    ):
        """Test to_dataframe method handles total calculation errors gracefully."""
        with patch.object(category_results_with_total, "totals") as mock_totals:
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
        with patch("pyproforma.tables.tables.Tables.category") as mock_category:
            mock_table = Mock()
            mock_category.return_value = mock_table

            result = category_results.table()

            mock_category.assert_called_once_with("income", hardcoded_color=None)
            assert result is mock_table

    def test_table_method_passes_category_name(self, category_results):
        """Test table method passes correct category name."""
        with patch("pyproforma.tables.tables.Tables.category") as mock_category:
            category_results.table()
            mock_category.assert_called_once_with("income", hardcoded_color=None)


class TestCategoryResultsPieChartMethod:
    """Test pie_chart method of CategoryResults."""

    @pytest.fixture
    def category_results(self, model_with_categories):
        """Create a CategoryResults instance for testing."""
        return CategoryResults(model_with_categories, "income")

    def test_pie_chart_method_returns_figure(self, category_results):
        """Test pie_chart method returns a plotly figure."""
        with patch("pyproforma.charts.charts.Charts.line_items_pie") as mock_pie_chart:
            mock_figure = Mock()
            mock_pie_chart.return_value = mock_figure

            result = category_results.pie_chart(year=2023)

            mock_pie_chart.assert_called_once_with(
                ["product_sales", "service_revenue"],
                2023,
                width=800,
                height=600,
                template="plotly_white",
            )
            assert result is mock_figure

    def test_pie_chart_method_passes_custom_parameters(self, category_results):
        """Test pie_chart method passes custom parameters correctly."""
        with patch("pyproforma.charts.charts.Charts.line_items_pie") as mock_pie_chart:
            category_results.pie_chart(
                year=2024, width=1000, height=800, template="plotly_dark"
            )

            mock_pie_chart.assert_called_once_with(
                ["product_sales", "service_revenue"],
                2024,
                width=1000,
                height=800,
                template="plotly_dark",
            )

    def test_pie_chart_method_with_empty_category(self, model_with_categories):
        """Test pie_chart method raises error for empty category."""
        # Create an empty category
        model_with_categories.update.add_category(name="empty", label="Empty Category")
        category_results = CategoryResults(model_with_categories, "empty")

        with pytest.raises(ValueError, match="No line items found in category 'empty'"):
            category_results.pie_chart(year=2023)

    def test_pie_chart_method_uses_line_item_names(self, category_results):
        """Test pie_chart method uses the correct line item names from the category."""
        with patch("pyproforma.charts.charts.Charts.line_items_pie") as mock_pie_chart:
            # Verify that the method uses the line_item_names property
            expected_item_names = category_results.line_item_names

            category_results.pie_chart(year=2023)

            mock_pie_chart.assert_called_once()
            call_args = mock_pie_chart.call_args
            assert call_args[0][0] == expected_item_names  # First positional argument


class TestCategoryResultsHtmlRepr:
    """Test _repr_html_ method for Jupyter notebook integration."""

    @pytest.fixture
    def category_results(self, model_with_categories):
        """Create a CategoryResults instance for testing."""
        return CategoryResults(model_with_categories, "income")

    def test_repr_html_method(self, category_results):
        """Test _repr_html_ method returns HTML formatted summary."""
        html_result = category_results._repr_html_()

        assert html_result.startswith("<pre>")
        assert html_result.endswith("</pre>")
        assert "CategoryResults('income')" in html_result
        assert "Label: Income" in html_result
        assert "<br>" in html_result  # Newlines converted to HTML breaks

    def test_repr_html_converts_newlines(self, category_results):
        """Test _repr_html_ method converts newlines to HTML breaks."""
        html_result = category_results._repr_html_()

        # Should not contain literal newlines
        assert "\n" not in html_result
        # Should contain HTML line breaks
        assert "<br>" in html_result


class TestCategoryResultsErrorHandling:
    """Test error handling in CategoryResults."""

    @pytest.fixture
    def model_with_categories_basic(self, basic_line_items, basic_categories):
        """Create a model with categories for testing."""
        return Model(
            line_items=basic_line_items,
            years=[2023, 2024, 2025],
            categories=basic_categories,
        )

    def test_summary_handles_missing_total(self, model_with_categories_basic):
        """Test summary method handles missing category total gracefully."""
        category_results = CategoryResults(model_with_categories_basic, "income")

        # Mock category_total to raise KeyError
        with patch.object(
            category_results.model, "category_total", side_effect=KeyError
        ):
            summary = category_results.summary()

            assert "CategoryResults('income')" in summary
            assert "Label: Income" in summary
            assert "Totals: Not available" in summary

    def test_table_method_with_table_error(self, model_with_categories_basic):
        """Test table method when underlying table method raises error."""
        category_results = CategoryResults(model_with_categories_basic, "income")

        with patch(
            "pyproforma.tables.tables.Tables.category",
            side_effect=KeyError("Table error"),
        ):
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
                value_format="no_decimals",
            ),
            LineItem(
                name="service_revenue",
                category="income",
                label="Service Revenue",
                values={2023: 50000, 2024: 60000},
                value_format="no_decimals",
            ),
            LineItem(
                name="salaries",
                category="costs",
                label="Salaries",
                values={2023: 40000, 2024: 45000},
                value_format="no_decimals",
            ),
        ]

        categories = [
            Category(name="income", label="Income", include_total=True),
            Category(name="costs", label="Costs", include_total=True),
        ]

        return Model(line_items=line_items, years=[2023, 2024], categories=categories)

    def test_category_results_from_model_method(self, integrated_model):
        """Test creating CategoryResults through model.category() method."""
        category_results = integrated_model.category("income")

        assert isinstance(category_results, CategoryResults)
        assert category_results.name == "income"
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
        assert "Totals: 150,000, 180,000" in str_result

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
            "service_revenue": {2023: 50000, 2024: 60000},
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


class TestCategoryResultsDeleteMethod:
    """Test the delete method of CategoryResults."""

    @pytest.fixture
    def delete_test_model(self):
        """Create a model specifically for testing delete functionality."""
        line_items = [
            LineItem(
                name="product_sales",
                category="revenue",
                label="Product Sales",
                values={2023: 100000, 2024: 120000},
                value_format="no_decimals",
            ),
            LineItem(
                name="service_revenue",
                category="revenue",
                label="Service Revenue",
                values={2023: 50000, 2024: 60000},
                value_format="no_decimals",
            ),
            LineItem(
                name="salaries",
                category="expenses",
                label="Salaries",
                values={2023: 40000, 2024: 45000},
                value_format="no_decimals",
            ),
        ]

        categories = [
            Category(name="revenue", label="Revenue", include_total=True),
            Category(name="expenses", label="Expenses", include_total=True),
            Category(name="unused", label="Unused Category", include_total=False),
        ]

        return Model(line_items=line_items, years=[2023, 2024], categories=categories)

    def test_delete_method_successfully_deletes_empty_category(self, delete_test_model):
        """Test that delete method successfully removes category with no line items."""
        # Get initial count
        initial_count = len(delete_test_model._category_definitions)

        # Create CategoryResults for unused category
        unused_category = CategoryResults(delete_test_model, "unused")

        # Verify the category exists and has no line items
        assert unused_category.name == "unused"
        assert len(unused_category.line_item_names) == 0

        # Delete the category
        unused_category.delete()

        # Verify the category was deleted
        assert len(delete_test_model._category_definitions) == initial_count - 1
        category_names = [cat.name for cat in delete_test_model._category_definitions]
        assert "unused" not in category_names

    def test_delete_method_fails_when_line_items_exist(self, delete_test_model):
        """Test that delete method raises ValueError when line items exist."""
        # Create CategoryResults for revenue category (which has line items)
        revenue_category = CategoryResults(delete_test_model, "revenue")

        # Verify the category has line items
        assert len(revenue_category.line_item_names) == 2
        assert "product_sales" in revenue_category.line_item_names
        assert "service_revenue" in revenue_category.line_item_names

        # Attempt to delete should fail
        with pytest.raises(ValueError) as excinfo:
            revenue_category.delete()

        error_msg = str(excinfo.value)
        assert "Cannot delete category 'revenue'" in error_msg
        assert "still contains line items" in error_msg
        assert "product_sales, service_revenue" in error_msg
        assert "Delete or move these line items" in error_msg

    def test_delete_method_fails_when_single_line_item_exists(self, delete_test_model):
        """Test that delete method fails even with just one line item in category."""
        # Create CategoryResults for expenses category (which has one line item)
        expenses_category = CategoryResults(delete_test_model, "expenses")

        # Verify the category has one line item
        assert len(expenses_category.line_item_names) == 1
        assert "salaries" in expenses_category.line_item_names

        # Attempt to delete should fail
        with pytest.raises(ValueError) as excinfo:
            expenses_category.delete()

        error_msg = str(excinfo.value)
        assert "Cannot delete category 'expenses'" in error_msg
        assert "still contains line items: salaries" in error_msg

    def test_delete_method_calls_model_delete_category(self, delete_test_model):
        """Test that delete method calls model.update.delete_category correctly."""
        unused_category = CategoryResults(delete_test_model, "unused")

        # Track the initial state
        initial_count = len(delete_test_model._category_definitions)

        # Call delete - this should succeed and actually delete the category
        unused_category.delete()

        # Verify the category was actually deleted
        assert len(delete_test_model._category_definitions) == initial_count - 1
        category_names = [cat.name for cat in delete_test_model._category_definitions]
        assert "unused" not in category_names

    def test_delete_method_after_moving_line_items(self, delete_test_model):
        """Test that delete method succeeds after moving all line items."""
        # Create CategoryResults for revenue category
        revenue_category = CategoryResults(delete_test_model, "revenue")

        # Initially should fail due to line items
        with pytest.raises(ValueError):
            revenue_category.delete()

        # Move all line items to expenses category
        for item_name in revenue_category.line_item_names.copy():
            delete_test_model.update.update_line_item(item_name, category="expenses")

        # Verify category now has no line items
        assert len(revenue_category.line_item_names) == 0

        # Now deletion should succeed
        initial_count = len(delete_test_model._category_definitions)
        revenue_category.delete()

        # Verify category was deleted
        assert len(delete_test_model._category_definitions) == initial_count - 1
        category_names = [cat.name for cat in delete_test_model._category_definitions]
        assert "revenue" not in category_names

    def test_delete_method_after_deleting_line_items(self, delete_test_model):
        """Test that delete method succeeds after deleting all line items."""
        # Create CategoryResults for expenses category
        expenses_category = CategoryResults(delete_test_model, "expenses")

        # Initially should fail due to line items
        with pytest.raises(ValueError):
            expenses_category.delete()

        # Delete all line items in the category
        for item_name in expenses_category.line_item_names.copy():
            delete_test_model.update.delete_line_item(item_name)

        # Verify category now has no line items
        assert len(expenses_category.line_item_names) == 0

        # Now deletion should succeed
        initial_count = len(delete_test_model._category_definitions)
        expenses_category.delete()

        # Verify category was deleted
        assert len(delete_test_model._category_definitions) == initial_count - 1
        category_names = [cat.name for cat in delete_test_model._category_definitions]
        assert "expenses" not in category_names

    def test_delete_method_handles_model_delete_error(self, delete_test_model):
        """Test that delete method properly propagates errors from model."""
        # Create a category that has line items (so it should fail)
        revenue_category = CategoryResults(delete_test_model, "revenue")

        # This should raise ValueError due to line items existing
        with pytest.raises(ValueError) as excinfo:
            revenue_category.delete()

        error_msg = str(excinfo.value)
        assert "Cannot delete category 'revenue'" in error_msg
        assert "still contains line items" in error_msg

    def test_delete_method_preserves_state_on_line_item_check_failure(
        self, delete_test_model
    ):
        """Test that CategoryResults state is preserved if check fails."""
        revenue_category = CategoryResults(delete_test_model, "revenue")
        original_name = revenue_category.name

        # Mock the model's line_item_names_by_category method to raise an error
        with patch.object(
            revenue_category.model,
            "line_item_names_by_category",
            side_effect=RuntimeError("Check failed"),
        ):
            with pytest.raises(RuntimeError, match="Check failed"):
                revenue_category.delete()

        # Verify the original state is preserved
        assert revenue_category.name == original_name

    def test_delete_method_error_message_formatting(self, delete_test_model):
        """Test that delete method error message is properly formatted."""
        revenue_category = CategoryResults(delete_test_model, "revenue")

        with pytest.raises(ValueError) as excinfo:
            revenue_category.delete()

        error_msg = str(excinfo.value)

        # Check all parts of the error message
        assert error_msg.startswith("Cannot delete category 'revenue'")
        assert "still contains line items:" in error_msg
        assert "product_sales, service_revenue" in error_msg
        assert "Delete or move these line items to other categories first." in error_msg

    def test_delete_method_integration_with_model_category_method(
        self, delete_test_model
    ):
        """Test delete method integration when CategoryResults created via model."""
        # Create CategoryResults through model.category() method
        unused_category = delete_test_model.category("unused")

        # Verify it's the correct type and has expected properties
        assert isinstance(unused_category, CategoryResults)
        assert unused_category.name == "unused"
        assert len(unused_category.line_item_names) == 0

        # Delete should work
        initial_count = len(delete_test_model._category_definitions)
        unused_category.delete()

        # Verify deletion worked
        assert len(delete_test_model._category_definitions) == initial_count - 1

    def test_delete_method_with_complex_category_names(self):
        """Test delete method with categories that have complex names."""
        line_items = []
        categories = [
            Category(
                name="category_with_underscores", label="Category with Underscores"
            ),
            Category(name="category-with-dashes", label="Category with Dashes"),
            Category(name="category123", label="Category with Numbers"),
        ]

        model = Model(line_items=line_items, years=[2024], categories=categories)

        # Test deleting each category type
        for category_name in [
            "category_with_underscores",
            "category-with-dashes",
            "category123",
        ]:
            category_results = CategoryResults(model, category_name)
            initial_count = len(model._category_definitions)

            category_results.delete()

            assert len(model._category_definitions) == initial_count - 1
            remaining_names = [cat.name for cat in model._category_definitions]
            assert category_name not in remaining_names

    def test_delete_method_with_line_items_in_other_categories(self, delete_test_model):
        """Test that delete method only checks line items in the specific category."""
        # This test ensures that having line items in OTHER categories doesn't
        # prevent deletion of an empty category

        unused_category = CategoryResults(delete_test_model, "unused")

        # Verify there are line items in other categories but not in 'unused'
        assert len(unused_category.line_item_names) == 0

        # Verify other categories have line items
        revenue_category = CategoryResults(delete_test_model, "revenue")
        assert len(revenue_category.line_item_names) > 0

        # Delete should succeed for unused category despite other categories
        # having items
        initial_count = len(delete_test_model._category_definitions)
        unused_category.delete()

        assert len(delete_test_model._category_definitions) == initial_count - 1


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
                value_format="no_decimals",
            )
        ]

        categories = [
            Category(name="income_2024", label="Income 2024", include_total=True)
        ]

        model = Model(line_items=line_items, years=[2024], categories=categories)

        category_results = CategoryResults(model, "income_2024")

        assert category_results.name == "income_2024"
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
                value_format="no_decimals",
            )
        ]

        categories = [Category(name="income", label="Income", include_total=True)]

        model = Model(line_items=line_items, years=[2024], categories=categories)

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

        categories = [
            Category(name="empty_category", label="Empty Category", include_total=True)
        ]

        model = Model(line_items=line_items, years=[2024], categories=categories)

        category_results = CategoryResults(model, "empty_category")

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
                value_format="percent",
            ),
            LineItem(
                name="decimal_metric",
                category="metrics",
                values={2024: 1234.56},
                value_format="two_decimals",
            ),
        ]

        categories = [Category(name="metrics", label="Metrics", include_total=False)]

        model = Model(line_items=line_items, years=[2024], categories=categories)

        category_results = CategoryResults(model, "metrics")

        # Test that different value formats are handled correctly
        values = category_results.values()
        assert values["percentage_metric"][2024] == 0.15
        assert values["decimal_metric"][2024] == 1234.56

        # Test that totals method raises error for category without totals
        with pytest.raises(
            ValueError, match="Category 'metrics' does not include totals"
        ):
            category_results.totals()


class TestCategoryResultsDeleteWithLineItems:
    """Test the delete method of CategoryResults with include_line_items parameter."""

    @pytest.fixture
    def delete_test_model(self):
        """Create a model specifically for testing delete functionality with line items."""
        line_items = [
            LineItem(
                name="product_sales",
                category="revenue",
                label="Product Sales",
                values={2023: 100000, 2024: 120000},
            ),
            LineItem(
                name="service_revenue",
                category="revenue",
                label="Service Revenue",
                values={2023: 50000, 2024: 60000},
            ),
            LineItem(
                name="salaries",
                category="expenses",
                label="Salaries",
                values={2023: 80000, 2024: 85000},
            ),
        ]

        categories = [
            Category(name="revenue", label="Revenue"),
            Category(name="expenses", label="Expenses"),
            Category(name="unused", label="Unused Category"),
        ]

        years = [2023, 2024]

        return Model(line_items=line_items, categories=categories, years=years)

    def test_delete_with_line_items_false_default_fails(self, delete_test_model):
        """Test that delete() with default parameter fails when line items exist."""
        revenue_category = CategoryResults(delete_test_model, "revenue")

        # Should fail because line items exist
        with pytest.raises(ValueError) as excinfo:
            revenue_category.delete()

        error_msg = str(excinfo.value)
        assert "Cannot delete category 'revenue'" in error_msg
        assert "still contains line items" in error_msg

    def test_delete_with_line_items_false_explicit_fails(self, delete_test_model):
        """Test that delete(include_line_items=False) explicitly fails when line items exist."""
        revenue_category = CategoryResults(delete_test_model, "revenue")

        # Should fail because line items exist
        with pytest.raises(ValueError) as excinfo:
            revenue_category.delete(include_line_items=False)

        error_msg = str(excinfo.value)
        assert "Cannot delete category 'revenue'" in error_msg
        assert "still contains line items" in error_msg

    def test_delete_with_line_items_true_succeeds(self, delete_test_model):
        """Test that delete(include_line_items=True) deletes category and its line items."""
        revenue_category = CategoryResults(delete_test_model, "revenue")

        initial_category_count = len(delete_test_model._category_definitions)
        initial_line_item_count = len(delete_test_model._line_item_definitions)

        # Should succeed and delete line items too
        revenue_category.delete(include_line_items=True)

        # Verify category is deleted
        assert len(delete_test_model._category_definitions) == initial_category_count - 1
        assert "revenue" not in [
            cat.name for cat in delete_test_model._category_definitions
        ]

        # Verify line items in that category are deleted
        assert len(delete_test_model._line_item_definitions) == initial_line_item_count - 2
        remaining_names = [item.name for item in delete_test_model._line_item_definitions]
        assert "product_sales" not in remaining_names
        assert "service_revenue" not in remaining_names
        assert "salaries" in remaining_names

    def test_delete_empty_category_with_flag_succeeds(self, delete_test_model):
        """Test that delete(include_line_items=True) works for empty categories."""
        unused_category = CategoryResults(delete_test_model, "unused")

        initial_count = len(delete_test_model._category_definitions)

        # Should succeed even though there are no line items to delete
        unused_category.delete(include_line_items=True)

        assert len(delete_test_model._category_definitions) == initial_count - 1
        assert "unused" not in [
            cat.name for cat in delete_test_model._category_definitions
        ]

    def test_delete_preserves_other_categories(self, delete_test_model):
        """Test that deleting one category doesn't affect others."""
        revenue_category = CategoryResults(delete_test_model, "revenue")

        # Delete revenue category with its line items
        revenue_category.delete(include_line_items=True)

        # Verify other categories and their line items are preserved
        assert "expenses" in [cat.name for cat in delete_test_model._category_definitions]
        assert "salaries" in [
            item.name for item in delete_test_model._line_item_definitions
        ]
