"""Tests for Model.to_dataframe() method."""

import pandas as pd
import pytest

from pyproforma import LineItem, Model


@pytest.fixture
def basic_model():
    """Create a basic model for testing."""
    line_items = [
        LineItem(
            name="revenue",
            category="income",
            label="Revenue",
            values={2023: 1000, 2024: 1200, 2025: 1400},
        ),
        LineItem(
            name="expenses",
            category="costs",
            label="Expenses",
            values={2023: 600, 2024: 700, 2025: 800},
        ),
        LineItem(
            name="profit",
            category="income",
            label="Profit",
            formula="revenue - expenses",
        ),
    ]
    return Model(line_items=line_items, years=[2023, 2024, 2025])


class TestModelToDataFrameBasic:
    """Test basic functionality of Model.to_dataframe()."""

    def test_to_dataframe_returns_dataframe(self, basic_model):
        """Test that to_dataframe returns a pandas DataFrame."""
        df = basic_model.to_dataframe()
        assert isinstance(df, pd.DataFrame)

    def test_to_dataframe_default_line_item_as_index(self, basic_model):
        """Test default behavior with line items as index."""
        df = basic_model.to_dataframe()

        # Check that line items are the index
        assert df.index.tolist() == ["revenue", "expenses", "profit"]

        # Check that years are the columns
        assert df.columns.tolist() == [2023, 2024, 2025]

        # Check values
        assert df.loc["revenue", 2023] == 1000
        assert df.loc["revenue", 2024] == 1200
        assert df.loc["revenue", 2025] == 1400
        assert df.loc["expenses", 2023] == 600
        assert df.loc["expenses", 2024] == 700
        assert df.loc["expenses", 2025] == 800
        assert df.loc["profit", 2023] == 400
        assert df.loc["profit", 2024] == 500
        assert df.loc["profit", 2025] == 600

    def test_to_dataframe_line_item_as_column(self, basic_model):
        """Test with line_item_as_index=False."""
        df = basic_model.to_dataframe(line_item_as_index=False)

        # Check that 'name' is a column
        assert "name" in df.columns
        assert df.columns.tolist() == ["name", 2023, 2024, 2025]

        # Check that line items are in the name column
        assert df["name"].tolist() == ["revenue", "expenses", "profit"]

        # Check values
        assert df.loc[0, 2023] == 1000
        assert df.loc[0, 2024] == 1200
        assert df.loc[1, 2023] == 600
        assert df.loc[2, 2023] == 400


class TestModelToDataFrameWithLabels:
    """Test to_dataframe with include_label parameter."""

    def test_to_dataframe_include_label_with_index(self, basic_model):
        """Test include_label=True with line_item_as_index=True."""
        df = basic_model.to_dataframe(include_label=True)

        # Check columns - should have 'label' and years
        assert df.columns.tolist() == ["label", 2023, 2024, 2025]

        # Check that line items are still the index
        assert df.index.tolist() == ["revenue", "expenses", "profit"]

        # Check label values
        assert df.loc["revenue", "label"] == "Revenue"
        assert df.loc["expenses", "label"] == "Expenses"
        assert df.loc["profit", "label"] == "Profit"

        # Check numeric values still work
        assert df.loc["revenue", 2023] == 1000

    def test_to_dataframe_include_label_with_column(self, basic_model):
        """Test include_label=True with line_item_as_index=False."""
        df = basic_model.to_dataframe(line_item_as_index=False, include_label=True)

        # Check columns - should have 'name', 'label', and years
        assert df.columns.tolist() == ["name", "label", 2023, 2024, 2025]

        # Check values
        assert df.loc[0, "name"] == "revenue"
        assert df.loc[0, "label"] == "Revenue"
        assert df.loc[1, "name"] == "expenses"
        assert df.loc[1, "label"] == "Expenses"
        assert df.loc[2, "name"] == "profit"
        assert df.loc[2, "label"] == "Profit"


class TestModelToDataFrameWithCategories:
    """Test to_dataframe with include_category parameter."""

    def test_to_dataframe_include_category_with_index(self, basic_model):
        """Test include_category=True with line_item_as_index=True."""
        df = basic_model.to_dataframe(include_category=True)

        # Check columns - should have 'category' and years
        assert df.columns.tolist() == ["category", 2023, 2024, 2025]

        # Check that line items are still the index
        assert df.index.tolist() == ["revenue", "expenses", "profit"]

        # Check category values
        assert df.loc["revenue", "category"] == "income"
        assert df.loc["expenses", "category"] == "costs"
        assert df.loc["profit", "category"] == "income"

        # Check numeric values still work
        assert df.loc["revenue", 2023] == 1000

    def test_to_dataframe_include_category_with_column(self, basic_model):
        """Test include_category=True with line_item_as_index=False."""
        df = basic_model.to_dataframe(line_item_as_index=False, include_category=True)

        # Check columns - should have 'name', 'category', and years
        assert df.columns.tolist() == ["name", "category", 2023, 2024, 2025]

        # Check values
        assert df.loc[0, "name"] == "revenue"
        assert df.loc[0, "category"] == "income"
        assert df.loc[1, "name"] == "expenses"
        assert df.loc[1, "category"] == "costs"
        assert df.loc[2, "name"] == "profit"
        assert df.loc[2, "category"] == "income"


class TestModelToDataFrameWithAllOptions:
    """Test to_dataframe with all parameters combined."""

    def test_to_dataframe_all_options_with_index(self, basic_model):
        """Test all options enabled with line_item_as_index=True."""
        df = basic_model.to_dataframe(include_label=True, include_category=True)

        # Check columns - should have 'label', 'category', and years
        assert df.columns.tolist() == ["label", "category", 2023, 2024, 2025]

        # Check that line items are still the index
        assert df.index.tolist() == ["revenue", "expenses", "profit"]

        # Check all values
        assert df.loc["revenue", "label"] == "Revenue"
        assert df.loc["revenue", "category"] == "income"
        assert df.loc["revenue", 2023] == 1000

        assert df.loc["expenses", "label"] == "Expenses"
        assert df.loc["expenses", "category"] == "costs"
        assert df.loc["expenses", 2023] == 600

    def test_to_dataframe_all_options_with_column(self, basic_model):
        """Test all options enabled with line_item_as_index=False."""
        df = basic_model.to_dataframe(
            line_item_as_index=False,
            include_label=True,
            include_category=True,
        )

        # Check columns - should have 'name', 'label', 'category', and years
        assert df.columns.tolist() == ["name", "label", "category", 2023, 2024, 2025]

        # Check first row
        assert df.loc[0, "name"] == "revenue"
        assert df.loc[0, "label"] == "Revenue"
        assert df.loc[0, "category"] == "income"
        assert df.loc[0, 2023] == 1000

        # Check second row
        assert df.loc[1, "name"] == "expenses"
        assert df.loc[1, "label"] == "Expenses"
        assert df.loc[1, "category"] == "costs"
        assert df.loc[1, 2023] == 600


class TestModelToDataFrameEdgeCases:
    """Test edge cases for Model.to_dataframe()."""

    def test_to_dataframe_empty_years(self):
        """Test to_dataframe with empty years list."""
        line_items = [
            LineItem(name="revenue", category="income"),
            LineItem(name="expenses", category="costs"),
        ]
        model = Model(line_items=line_items, years=[])

        df = model.to_dataframe()

        # Should have line items as index but no year columns
        assert df.index.tolist() == ["revenue", "expenses"]
        assert df.columns.tolist() == []

    def test_to_dataframe_single_line_item(self):
        """Test to_dataframe with a single line item."""
        line_items = [
            LineItem(
                name="revenue",
                category="income",
                label="Revenue",
                values={2023: 1000, 2024: 1200},
            ),
        ]
        model = Model(line_items=line_items, years=[2023, 2024])

        df = model.to_dataframe()

        assert df.index.tolist() == ["revenue"]
        assert df.columns.tolist() == [2023, 2024]
        assert df.loc["revenue", 2023] == 1000
        assert df.loc["revenue", 2024] == 1200

    def test_to_dataframe_single_year(self):
        """Test to_dataframe with a single year."""
        line_items = [
            LineItem(name="revenue", category="income", values={2023: 1000}),
            LineItem(name="expenses", category="costs", values={2023: 600}),
        ]
        model = Model(line_items=line_items, years=[2023])

        df = model.to_dataframe()

        assert df.index.tolist() == ["revenue", "expenses"]
        assert df.columns.tolist() == [2023]
        assert df.loc["revenue", 2023] == 1000
        assert df.loc["expenses", 2023] == 600

    def test_to_dataframe_no_line_items(self):
        """Test to_dataframe with no line items."""
        model = Model(line_items=[], years=[2023, 2024, 2025])

        df = model.to_dataframe()

        # Should be an empty DataFrame with year columns
        assert len(df) == 0
        assert df.columns.tolist() == [2023, 2024, 2025]

    def test_to_dataframe_preserves_data_types(self, basic_model):
        """Test that to_dataframe preserves data types correctly."""
        df = basic_model.to_dataframe(
            line_item_as_index=False,
            include_label=True,
            include_category=True,
        )

        # Check that name, label, and category are strings
        assert df["name"].dtype == object
        assert df["label"].dtype == object
        assert df["category"].dtype == object

        # Check that year columns are numeric
        assert pd.api.types.is_numeric_dtype(df[2023])
        assert pd.api.types.is_numeric_dtype(df[2024])
        assert pd.api.types.is_numeric_dtype(df[2025])


class TestModelToDataFrameWithComplexModel:
    """Test to_dataframe with a more complex model."""

    @pytest.fixture
    def complex_model(self):
        """Create a more complex model with multiple categories."""
        line_items = [
            LineItem(
                name="product_sales",
                category="revenue",
                label="Product Sales",
                values={2023: 5000, 2024: 5500, 2025: 6000},
            ),
            LineItem(
                name="service_revenue",
                category="revenue",
                label="Service Revenue",
                values={2023: 3000, 2024: 3500, 2025: 4000},
            ),
            LineItem(
                name="salaries",
                category="expenses",
                label="Salaries",
                values={2023: 2000, 2024: 2200, 2025: 2400},
            ),
            LineItem(
                name="rent",
                category="expenses",
                label="Rent",
                values={2023: 1000, 2024: 1000, 2025: 1000},
            ),
            LineItem(
                name="marketing",
                category="expenses",
                label="Marketing",
                values={2023: 500, 2024: 600, 2025: 700},
            ),
            LineItem(
                name="net_income",
                category="results",
                label="Net Income",
                formula="product_sales + service_revenue - salaries - rent - marketing",
            ),
        ]
        return Model(line_items=line_items, years=[2023, 2024, 2025])

    def test_complex_model_to_dataframe_default(self, complex_model):
        """Test to_dataframe on complex model with default settings."""
        df = complex_model.to_dataframe()

        assert len(df) == 6
        assert df.index.tolist() == [
            "product_sales",
            "service_revenue",
            "salaries",
            "rent",
            "marketing",
            "net_income",
        ]
        assert df.columns.tolist() == [2023, 2024, 2025]

        # Check calculated value
        assert df.loc["net_income", 2023] == 4500  # 5000 + 3000 - 2000 - 1000 - 500

    def test_complex_model_with_all_options(self, complex_model):
        """Test to_dataframe on complex model with all options."""
        df = complex_model.to_dataframe(
            line_item_as_index=False,
            include_label=True,
            include_category=True,
        )

        assert len(df) == 6
        assert df.columns.tolist() == ["name", "label", "category", 2023, 2024, 2025]

        # Check that all categories are present
        assert set(df["category"].tolist()) == {"revenue", "expenses", "results"}

        # Check specific rows
        product_row = df[df["name"] == "product_sales"].iloc[0]
        assert product_row["label"] == "Product Sales"
        assert product_row["category"] == "revenue"
        assert product_row[2023] == 5000


class TestModelToDataFrameLineItemsFilter:
    """Test to_dataframe with line_items parameter for filtering."""

    def test_to_dataframe_line_items_none_includes_all(self, basic_model):
        """Test that line_items=None includes all line items (default behavior)."""
        df_all = basic_model.to_dataframe()
        df_none = basic_model.to_dataframe(line_items=None)

        # Should be identical
        pd.testing.assert_frame_equal(df_all, df_none)
        assert df_none.index.tolist() == ["revenue", "expenses", "profit"]

    def test_to_dataframe_line_items_subset_with_index(self, basic_model):
        """Test filtering to a subset of line items with line_item_as_index=True."""
        df = basic_model.to_dataframe(line_items=["revenue", "expenses"])

        # Check that only specified line items are included
        assert df.index.tolist() == ["revenue", "expenses"]
        assert df.columns.tolist() == [2023, 2024, 2025]

        # Check values
        assert df.loc["revenue", 2023] == 1000
        assert df.loc["expenses", 2023] == 600

        # Check that profit is not included
        assert "profit" not in df.index

    def test_to_dataframe_line_items_subset_with_column(self, basic_model):
        """Test filtering to a subset of line items with line_item_as_index=False."""
        df = basic_model.to_dataframe(
            line_items=["revenue", "profit"], line_item_as_index=False
        )

        # Check columns and row count
        assert df.columns.tolist() == ["name", 2023, 2024, 2025]
        assert len(df) == 2

        # Check that only specified line items are included
        assert df["name"].tolist() == ["revenue", "profit"]

        # Check values
        assert df.loc[0, "name"] == "revenue"
        assert df.loc[0, 2023] == 1000
        assert df.loc[1, "name"] == "profit"
        assert df.loc[1, 2023] == 400

    def test_to_dataframe_line_items_single_item(self, basic_model):
        """Test filtering to a single line item."""
        df = basic_model.to_dataframe(line_items=["revenue"])

        assert df.index.tolist() == ["revenue"]
        assert df.columns.tolist() == [2023, 2024, 2025]
        assert df.loc["revenue", 2023] == 1000
        assert df.loc["revenue", 2024] == 1200
        assert df.loc["revenue", 2025] == 1400

    def test_to_dataframe_line_items_preserve_order(self, basic_model):
        """Test that line_items parameter preserves the specified order."""
        # Specify in different order than model definition
        df = basic_model.to_dataframe(line_items=["profit", "revenue", "expenses"])

        # Should preserve the order from line_items parameter
        assert df.index.tolist() == ["profit", "revenue", "expenses"]

        # Check values are correct
        assert df.loc["profit", 2023] == 400
        assert df.loc["revenue", 2023] == 1000
        assert df.loc["expenses", 2023] == 600

    def test_to_dataframe_line_items_with_labels_and_categories(self, basic_model):
        """Test line_items filtering with include_label and include_category."""
        df = basic_model.to_dataframe(
            line_items=["revenue", "profit"],
            line_item_as_index=False,
            include_label=True,
            include_category=True,
        )

        # Check structure
        assert df.columns.tolist() == ["name", "label", "category", 2023, 2024, 2025]
        assert len(df) == 2

        # Check first row (revenue)
        assert df.loc[0, "name"] == "revenue"
        assert df.loc[0, "label"] == "Revenue"
        assert df.loc[0, "category"] == "income"
        assert df.loc[0, 2023] == 1000

        # Check second row (profit)
        assert df.loc[1, "name"] == "profit"
        assert df.loc[1, "label"] == "Profit"
        assert df.loc[1, "category"] == "income"
        assert df.loc[1, 2023] == 400

    def test_to_dataframe_line_items_empty_list(self, basic_model):
        """Test with empty line_items list."""
        df = basic_model.to_dataframe(line_items=[])

        # Should result in empty DataFrame with year columns
        assert len(df) == 0
        assert df.columns.tolist() == [2023, 2024, 2025]

    def test_to_dataframe_line_items_invalid_name_raises_error(self, basic_model):
        """Test that invalid line item name raises ValueError."""
        with pytest.raises(ValueError, match="Invalid line item names"):
            basic_model.to_dataframe(line_items=["revenue", "invalid_name"])

        # Check error message contains helpful information
        with pytest.raises(ValueError) as exc_info:
            basic_model.to_dataframe(line_items=["nonexistent"])

        error_msg = str(exc_info.value)
        assert "Invalid line item names: ['nonexistent']" in error_msg
        assert "Available line items:" in error_msg
        assert "revenue" in error_msg
        assert "expenses" in error_msg
        assert "profit" in error_msg

    def test_to_dataframe_line_items_mixed_valid_invalid_raises_error(
        self, basic_model
    ):
        """Test that mix of valid and invalid names raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            basic_model.to_dataframe(line_items=["revenue", "bad1", "expenses", "bad2"])

        error_msg = str(exc_info.value)
        assert "Invalid line item names: ['bad1', 'bad2']" in error_msg

    def test_to_dataframe_line_items_duplicate_names(self, basic_model):
        """Test behavior with duplicate line item names."""
        # Should handle duplicates gracefully by including each occurrence
        df = basic_model.to_dataframe(line_items=["revenue", "revenue", "expenses"])

        # Should include revenue twice
        assert df.index.tolist() == ["revenue", "revenue", "expenses"]
        assert len(df) == 3

        # Values should be correct for both revenue rows
        revenue_values = df.loc["revenue", 2023]
        if hasattr(revenue_values, "__iter__"):
            # Multiple rows with same index return Series
            assert all(revenue_values == 1000)
        else:
            # Single row returns scalar
            assert revenue_values == 1000

        # Check by position to be sure
        assert df.iloc[0, df.columns.get_loc(2023)] == 1000  # First revenue
        assert df.iloc[1, df.columns.get_loc(2023)] == 1000  # Second revenue
        assert df.iloc[2, df.columns.get_loc(2023)] == 600  # expenses


class TestModelToDataFrameLineItemsComplexModel:
    """Test line_items filtering with complex model."""

    @pytest.fixture
    def complex_model(self):
        """Create a more complex model for line_items testing."""
        line_items = [
            LineItem(
                name="product_sales",
                category="revenue",
                label="Product Sales",
                values={2023: 5000, 2024: 5500, 2025: 6000},
            ),
            LineItem(
                name="service_revenue",
                category="revenue",
                label="Service Revenue",
                values={2023: 3000, 2024: 3500, 2025: 4000},
            ),
            LineItem(
                name="salaries",
                category="expenses",
                label="Salaries",
                values={2023: 2000, 2024: 2200, 2025: 2400},
            ),
            LineItem(
                name="rent",
                category="expenses",
                label="Rent",
                values={2023: 1000, 2024: 1000, 2025: 1000},
            ),
            LineItem(
                name="marketing",
                category="expenses",
                label="Marketing",
                values={2023: 500, 2024: 600, 2025: 700},
            ),
            LineItem(
                name="net_income",
                category="results",
                label="Net Income",
                formula="product_sales + service_revenue - salaries - rent - marketing",
            ),
        ]
        return Model(line_items=line_items, years=[2023, 2024, 2025])

    def test_to_dataframe_line_items_revenue_only(self, complex_model):
        """Test filtering to only revenue line items."""
        df = complex_model.to_dataframe(line_items=["product_sales", "service_revenue"])

        assert df.index.tolist() == ["product_sales", "service_revenue"]
        assert df.columns.tolist() == [2023, 2024, 2025]

        # Check values
        assert df.loc["product_sales", 2023] == 5000
        assert df.loc["service_revenue", 2023] == 3000

        # Ensure other items are not included
        assert "salaries" not in df.index
        assert "net_income" not in df.index

    def test_to_dataframe_line_items_expenses_only(self, complex_model):
        """Test filtering to only expense line items."""
        df = complex_model.to_dataframe(
            line_items=["salaries", "rent", "marketing"],
            line_item_as_index=False,
            include_category=True,
        )

        assert len(df) == 3
        assert df.columns.tolist() == ["name", "category", 2023, 2024, 2025]

        # Check that all rows are expenses
        assert all(df["category"] == "expenses")

        # Check specific values
        salaries_row = df[df["name"] == "salaries"].iloc[0]
        assert salaries_row[2023] == 2000

        rent_row = df[df["name"] == "rent"].iloc[0]
        assert rent_row[2023] == 1000

    def test_to_dataframe_line_items_mixed_categories(self, complex_model):
        """Test filtering to line items from different categories."""
        df = complex_model.to_dataframe(
            line_items=["product_sales", "salaries", "net_income"],
            line_item_as_index=False,
            include_category=True,
        )

        assert len(df) == 3
        assert df["name"].tolist() == ["product_sales", "salaries", "net_income"]

        # Check categories are preserved correctly
        assert df.loc[0, "category"] == "revenue"  # product_sales
        assert df.loc[1, "category"] == "expenses"  # salaries
        assert df.loc[2, "category"] == "results"  # net_income

        # Check calculated value is correct
        assert df.loc[2, 2023] == 4500  # net_income calculated value

    def test_to_dataframe_line_items_preserve_complex_order(self, complex_model):
        """Test that complex reordering is preserved."""
        # Specify a custom order mixing categories
        custom_order = ["net_income", "rent", "product_sales", "marketing"]
        df = complex_model.to_dataframe(line_items=custom_order)

        # Order should be preserved exactly
        assert df.index.tolist() == custom_order

        # Values should be correct
        assert df.loc["net_income", 2023] == 4500
        assert df.loc["rent", 2023] == 1000
        assert df.loc["product_sales", 2023] == 5000
        assert df.loc["marketing", 2023] == 500
