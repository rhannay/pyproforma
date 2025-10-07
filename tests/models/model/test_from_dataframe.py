"""
Test cases for Model.from_dataframe class method.
"""

import pandas as pd
import pytest

from pyproforma import Model


class TestFromDataFrame:
    """Test the Model.from_dataframe class method."""

    def test_basic_dataframe_to_model(self):
        """Test creating a model from a basic DataFrame."""
        df = pd.DataFrame(
            {
                "name": ["revenue", "expenses", "profit"],
                2023: [1000, 600, 400],
                2024: [1200, 700, 500],
                2025: [1400, 800, 600],
            }
        )

        model = Model.from_dataframe(df)

        assert model.years == [2023, 2024, 2025]
        # Note: Model automatically creates category totals,
        # so there are more line items
        assert "revenue" in model.line_item_names
        assert "expenses" in model.line_item_names
        assert "profit" in model.line_item_names

        assert model.value("revenue", 2023) == 1000
        assert model.value("revenue", 2024) == 1200
        assert model.value("revenue", 2025) == 1400
        assert model.value("expenses", 2023) == 600
        assert model.value("profit", 2025) == 600

    def test_dataframe_with_string_years(self):
        """Test creating a model from DataFrame with string year columns."""
        df = pd.DataFrame(
            {
                "item_name": ["revenue", "costs"],
                "2023": [1000, 400],
                "2024": [1100, 450],
            }
        )

        model = Model.from_dataframe(df)

        assert model.years == [2023, 2024]
        assert "revenue" in model.line_item_names
        assert "costs" in model.line_item_names
        assert model.value("revenue", 2023) == 1000
        assert model.value("costs", 2024) == 450

    def test_dataframe_with_mixed_string_and_int_years(self):
        """Test DataFrame with both string and integer year columns."""
        df = pd.DataFrame(
            {"name": ["revenue"], 2023: [1000], "2024": [1100], 2025: [1200]}
        )

        model = Model.from_dataframe(df)

        assert model.years == [2023, 2024, 2025]
        assert model.value("revenue", 2024) == 1100

    def test_dataframe_unsorted_years(self):
        """Test that years are sorted even if DataFrame columns are not."""
        df = pd.DataFrame(
            {"name": ["revenue"], 2025: [1200], 2023: [1000], 2024: [1100]}
        )

        model = Model.from_dataframe(df)

        assert model.years == [2023, 2024, 2025]

    def test_dataframe_with_nan_values(self):
        """Test that NaN values are handled correctly."""
        df = pd.DataFrame(
            {
                "name": ["revenue", "expenses"],
                2023: [1000, None],
                2024: [1200, 700],
                2025: [None, 800],
            }
        )

        model = Model.from_dataframe(df)

        assert model.years == [2023, 2024, 2025]
        assert model.value("revenue", 2023) == 1000
        assert model.value("revenue", 2024) == 1200
        # Revenue 2025 should be None/missing
        assert model.value("expenses", 2024) == 700

    def test_fill_in_periods_false(self):
        """Test that gaps in years are not filled when fill_in_periods=False."""
        df = pd.DataFrame({"name": ["revenue"], 2023: [1000], 2025: [1400]})

        # Note: validate_periods will not fill gaps by default,
        # but validate_years (used in Model.__init__) requires sequential years
        # So this should raise an error
        with pytest.raises(ValueError) as exc_info:
            Model.from_dataframe(df, fill_in_periods=False)

        error_msg = str(exc_info.value)
        assert "Years must be sequential with no gaps" in error_msg

    def test_fill_in_periods_true(self):
        """Test that gaps in years are filled when fill_in_periods=True."""
        df = pd.DataFrame(
            {"name": ["revenue", "expenses"], 2023: [1000, 600], 2025: [1400, 800]}
        )

        model = Model.from_dataframe(df, fill_in_periods=True)

        assert model.years == [2023, 2024, 2025]
        assert model.value("revenue", 2023) == 1000
        # 2024 should exist but revenue should be None/0
        assert model.value("revenue", 2025) == 1400

    def test_single_line_item(self):
        """Test creating a model with single line item."""
        df = pd.DataFrame({"name": ["revenue"], 2023: [1000], 2024: [1100]})

        model = Model.from_dataframe(df)

        assert model.years == [2023, 2024]
        assert "revenue" in model.line_item_names
        assert model.value("revenue", 2023) == 1000

    def test_single_year(self):
        """Test creating a model with single year."""
        df = pd.DataFrame({"name": ["revenue", "expenses"], 2023: [1000, 600]})

        model = Model.from_dataframe(df)

        assert model.years == [2023]
        assert model.value("revenue", 2023) == 1000
        assert model.value("expenses", 2023) == 600

    def test_empty_dataframe_raises_error(self):
        """Test that empty DataFrame raises ValueError."""
        df = pd.DataFrame()

        with pytest.raises(ValueError) as exc_info:
            Model.from_dataframe(df)

        error_msg = str(exc_info.value)
        assert "DataFrame cannot be empty" in error_msg

    def test_dataframe_with_only_one_column_raises_error(self):
        """Test that DataFrame with only one column raises ValueError."""
        df = pd.DataFrame({"name": ["revenue", "expenses"]})

        with pytest.raises(ValueError) as exc_info:
            Model.from_dataframe(df)

        error_msg = str(exc_info.value)
        assert "must have at least 2 columns" in error_msg

    def test_invalid_year_columns_raise_error(self):
        """Test that invalid year columns raise ValueError."""
        df = pd.DataFrame({"name": ["revenue"], "invalid": [1000], 2023: [1100]})

        with pytest.raises(ValueError) as exc_info:
            Model.from_dataframe(df)

        error_msg = str(exc_info.value)
        assert "Invalid year" in error_msg or "cannot be converted" in error_msg

    def test_duplicate_years_raise_error(self):
        """Test that duplicate year columns raise ValueError."""
        # Create a DataFrame with duplicate column names by directly
        # using the constructor with duplicate column names
        data = {"name": ["revenue"], "col1": [1000], "col2": [1100]}
        df = pd.DataFrame(data, columns=["name", 2023, 2023])

        with pytest.raises(ValueError) as exc_info:
            Model.from_dataframe(df)

        error_msg = str(exc_info.value)
        assert "Duplicate years not allowed" in error_msg

    def test_not_dataframe_raises_type_error(self):
        """Test that non-DataFrame input raises TypeError."""
        with pytest.raises(TypeError) as exc_info:
            Model.from_dataframe("not a dataframe")

        error_msg = str(exc_info.value)
        assert "Expected pandas DataFrame" in error_msg

    def test_dataframe_with_different_first_column_name(self):
        """Test that any first column name works for line item names."""
        df = pd.DataFrame(
            {"item": ["revenue", "costs"], 2023: [1000, 400], 2024: [1100, 450]}
        )

        model = Model.from_dataframe(df)

        assert "revenue" in model.line_item_names
        assert "costs" in model.line_item_names

    def test_dataframe_with_numeric_line_item_names(self):
        """Test that numeric line item names are converted to strings."""
        df = pd.DataFrame({"id": [100, 200], 2023: [1000, 400], 2024: [1100, 450]})

        model = Model.from_dataframe(df)

        assert "100" in model.line_item_names
        assert "200" in model.line_item_names
        assert model.value("100", 2023) == 1000

    def test_dataframe_skips_rows_with_missing_names(self):
        """Test that rows with missing names are skipped in various scenarios."""
        # Test with None in name column
        df = pd.DataFrame(
            {
                "name": ["revenue", None, "profit"],
                2023: [1000, 600, 400],
                2024: [1200, 700, 500],
            }
        )

        model = Model.from_dataframe(df)

        # Only revenue and profit should be created (row with None name is skipped)
        assert "revenue" in model.line_item_names
        assert "profit" in model.line_item_names
        # Check that we only have the 2 defined items
        user_defined_names = [item.name for item in model._line_item_definitions]
        assert len(user_defined_names) == 2
        assert "revenue" in user_defined_names
        assert "profit" in user_defined_names

        # Test with None in label column when using label_col only
        df_label = pd.DataFrame(
            {
                "display_label": ["Total Revenue", None, "Net Profit"],
                2023: [1000, 600, 400],
                2024: [1200, 700, 500],
            }
        )

        model_label = Model.from_dataframe(df_label, label_col="display_label")

        # Only total_revenue and net_profit should be created
        # (row with None label is skipped)
        assert "total_revenue" in model_label.line_item_names
        assert "net_profit" in model_label.line_item_names
        # Check that we only have the 2 defined items
        user_defined_names_label = [
            item.name for item in model_label._line_item_definitions
        ]
        assert len(user_defined_names_label) == 2
        assert "total_revenue" in user_defined_names_label
        assert "net_profit" in user_defined_names_label

        # Test with empty string in name column
        df_empty = pd.DataFrame(
            {
                "name": ["revenue", "", "profit"],
                2023: [1000, 600, 400],
                2024: [1200, 700, 500],
            }
        )

        model_empty = Model.from_dataframe(df_empty)

        # Only revenue and profit should be created (empty string is skipped)
        assert "revenue" in model_empty.line_item_names
        assert "profit" in model_empty.line_item_names
        # Empty string should be skipped, so only 2 items
        user_defined_names_empty = [
            item.name for item in model_empty._line_item_definitions
        ]
        assert len(user_defined_names_empty) == 2

    def test_dataframe_with_negative_years(self):
        """Test creating model with negative years."""
        df = pd.DataFrame({"name": ["revenue"], -1: [900], 0: [1000], 1: [1100]})

        model = Model.from_dataframe(df)

        assert model.years == [-1, 0, 1]
        assert model.value("revenue", -1) == 900
        assert model.value("revenue", 0) == 1000

    def test_dataframe_with_large_years(self):
        """Test creating model with very large year values."""
        df = pd.DataFrame(
            {"name": ["revenue"], 9998: [1000], 9999: [1100], 10000: [1200]}
        )

        model = Model.from_dataframe(df)

        assert model.years == [9998, 9999, 10000]
        assert model.value("revenue", 9998) == 1000

    def test_fill_in_periods_with_large_gap(self):
        """Test fill_in_periods with a larger gap."""
        df = pd.DataFrame({"name": ["revenue"], 2020: [1000], 2025: [1500]})

        model = Model.from_dataframe(df, fill_in_periods=True)

        assert model.years == [2020, 2021, 2022, 2023, 2024, 2025]
        assert model.value("revenue", 2020) == 1000
        assert model.value("revenue", 2025) == 1500
        # Middle years should have None/0 values

    def test_dataframe_preserves_line_item_order(self):
        """Test that line item order from DataFrame is preserved."""
        df = pd.DataFrame({"name": ["zebra", "alpha", "beta"], 2023: [100, 200, 300]})

        model = Model.from_dataframe(df)

        # Get line item names in order
        names = model.line_item_names
        assert names[0] == "zebra"
        assert names[1] == "alpha"
        assert names[2] == "beta"

    def test_dataframe_sanitizes_names_with_spaces(self):
        """Test that names with spaces are converted to lowercase with underscores."""
        df = pd.DataFrame(
            {
                "name": ["Gross Profit", "Net Income", "Cost of Goods Sold"],
                2023: [100, 200, 300],
            }
        )

        model = Model.from_dataframe(df)

        # Names should be lowercase with spaces replaced with underscores
        assert "gross_profit" in model.line_item_names
        assert "net_income" in model.line_item_names
        assert "cost_of_goods_sold" in model.line_item_names
        assert model.value("gross_profit", 2023) == 100
        assert model.value("net_income", 2023) == 200
        assert model.value("cost_of_goods_sold", 2023) == 300

    def test_dataframe_with_name_col(self):
        """Test using name_col parameter to specify name column."""
        df = pd.DataFrame(
            {
                "item_name": ["revenue", "expenses"],
                2023: [1000, 600],
                2024: [1200, 700],
                2025: [1500, 900],
            }
        )

        model = Model.from_dataframe(df, name_col="item_name")

        assert "revenue" in model.line_item_names
        assert "expenses" in model.line_item_names
        assert model.value("revenue", 2023) == 1000
        assert model.value("expenses", 2024) == 700
        assert model.value("revenue", 2025) == 1500

    def test_dataframe_with_name_and_label_col(self):
        """Test using name_col and label_col parameters."""
        df = pd.DataFrame(
            {
                "item_name": ["revenue", "expenses"],
                "display_label": ["Total Revenue", "Total Expenses"],
                2023: [1000, 600],
                2024: [1200, 700],
            }
        )

        model = Model.from_dataframe(
            df, name_col="item_name", label_col="display_label"
        )

        assert "revenue" in model.line_item_names
        assert "expenses" in model.line_item_names

        # Check that labels are set correctly
        revenue_item = [
            item for item in model._line_item_definitions if item.name == "revenue"
        ][0]
        expenses_item = [
            item for item in model._line_item_definitions if item.name == "expenses"
        ][0]
        assert revenue_item.label == "Total Revenue"
        assert expenses_item.label == "Total Expenses"

    def test_dataframe_with_label_col_only(self):
        """Test using label_col without name_col (names derived from labels)."""
        df = pd.DataFrame(
            {
                "display_label": ["Total Revenue", "Total Expenses", "Net Profit"],
                2023: [1000, 600, 400],
                2024: [1200, 700, 500],
            }
        )

        model = Model.from_dataframe(df, label_col="display_label")

        # Names should be derived from labels using convert_to_name
        assert "total_revenue" in model.line_item_names
        assert "total_expenses" in model.line_item_names
        assert "net_profit" in model.line_item_names

        # Labels should be preserved exactly as they appear in the DataFrame
        revenue_item = [
            item
            for item in model._line_item_definitions
            if item.name == "total_revenue"
        ][0]
        expenses_item = [
            item
            for item in model._line_item_definitions
            if item.name == "total_expenses"
        ][0]
        profit_item = [
            item for item in model._line_item_definitions if item.name == "net_profit"
        ][0]

        # Verify labels are used as-is (not converted)
        assert revenue_item.label == "Total Revenue"  # Not "total_revenue"
        assert expenses_item.label == "Total Expenses"  # Not "total_expenses"
        assert profit_item.label == "Net Profit"  # Not "net_profit"

        # Verify names are converted from labels
        assert revenue_item.name == "total_revenue"  # Converted from "Total Revenue"
        assert expenses_item.name == "total_expenses"  # Converted from "Total Expenses"
        assert profit_item.name == "net_profit"  # Converted from "Net Profit"

        assert model.value("total_revenue", 2023) == 1000
        assert model.value("total_expenses", 2024) == 700

    def test_label_col_only_preserves_labels_converts_names(self):
        """Test that when only label_col is provided, labels are preserved as-is
        and names are converted."""
        # Test with labels that have mixed case, spaces, and special characters
        df = pd.DataFrame(
            {
                "item_label": [
                    "Gross Revenue & Income",
                    "Operating Expenses (OPEX)",
                    "EBITDA Margin %",
                ],
                2023: [5000, 3000, 40],
                2024: [6000, 3500, 42],
            }
        )

        model = Model.from_dataframe(df, label_col="item_label")

        # Get the line items
        gross_revenue_item = [
            item
            for item in model._line_item_definitions
            if item.name == "gross_revenue_income"
        ][0]
        opex_item = [
            item
            for item in model._line_item_definitions
            if item.name == "operating_expenses_opex"
        ][0]
        ebitda_item = [
            item
            for item in model._line_item_definitions
            if item.name == "ebitda_margin"
        ][0]

        # Verify labels are preserved exactly as they appear in DataFrame
        assert gross_revenue_item.label == "Gross Revenue & Income"
        assert opex_item.label == "Operating Expenses (OPEX)"
        assert ebitda_item.label == "EBITDA Margin %"

        # Verify names are converted/sanitized versions
        assert gross_revenue_item.name == "gross_revenue_income"
        assert opex_item.name == "operating_expenses_opex"
        assert ebitda_item.name == "ebitda_margin"

        # Verify values work correctly with converted names
        assert model.value("gross_revenue_income", 2023) == 5000
        assert model.value("operating_expenses_opex", 2024) == 3500
        assert model.value("ebitda_margin", 2024) == 42

    def test_dataframe_with_category_col(self):
        """Test using category_col parameter."""
        df = pd.DataFrame(
            {
                "item_name": ["revenue", "expenses"],
                "category": ["income", "costs"],
                2023: [1000, 600],
                2024: [1200, 700],
            }
        )

        model = Model.from_dataframe(df, name_col="item_name", category_col="category")

        assert "revenue" in model.line_item_names
        assert "expenses" in model.line_item_names

        # Check that categories are set correctly
        revenue_item = [
            item for item in model._line_item_definitions if item.name == "revenue"
        ][0]
        expenses_item = [
            item for item in model._line_item_definitions if item.name == "expenses"
        ][0]
        assert revenue_item.category == "income"
        assert expenses_item.category == "costs"

    def test_dataframe_with_all_metadata_cols(self):
        """Test using name_col, label_col, and category_col together."""
        df = pd.DataFrame(
            {
                "item_name": ["revenue", "expenses"],
                "display_label": ["Total Revenue", "Total Expenses"],
                "category": ["income", "costs"],
                2023: [1000, 600],
                2024: [1200, 700],
            }
        )

        model = Model.from_dataframe(
            df, name_col="item_name", label_col="display_label", category_col="category"
        )

        assert "revenue" in model.line_item_names

        # Check all attributes are set correctly
        revenue_item = [
            item for item in model._line_item_definitions if item.name == "revenue"
        ][0]
        assert revenue_item.name == "revenue"
        assert revenue_item.label == "Total Revenue"
        assert revenue_item.category == "income"
        assert model.value("revenue", 2023) == 1000

    def test_dataframe_with_label_and_category_col(self):
        """Test using label_col and category_col without name_col."""
        df = pd.DataFrame(
            {
                "display_label": ["Total Revenue", "Total Expenses"],
                "category": ["income", "costs"],
                2023: [1000, 600],
                2024: [1200, 700],
            }
        )

        model = Model.from_dataframe(
            df, label_col="display_label", category_col="category"
        )

        # Names should be derived from labels
        assert "total_revenue" in model.line_item_names
        assert "total_expenses" in model.line_item_names

        # Check categories are set
        revenue_item = [
            item
            for item in model._line_item_definitions
            if item.name == "total_revenue"
        ][0]
        assert revenue_item.category == "income"
        assert revenue_item.label == "Total Revenue"

    def test_dataframe_category_col_only_raises_error(self):
        """Test that providing only category_col raises error."""
        df = pd.DataFrame(
            {"category": ["income", "costs"], 2023: [1000, 600], 2024: [1200, 700]}
        )

        with pytest.raises(ValueError) as exc_info:
            Model.from_dataframe(df, category_col="category")

        error_msg = str(exc_info.value)
        assert (
            "category_col cannot be provided without name_col or label_col" in error_msg
        )
        assert "LineItems require names" in error_msg

    def test_dataframe_invalid_name_col_raises_error(self):
        """Test that non-existent name_col raises error."""
        df = pd.DataFrame({"item_name": ["revenue", "expenses"], 2023: [1000, 600]})

        with pytest.raises(ValueError) as exc_info:
            Model.from_dataframe(df, name_col="nonexistent")

        error_msg = str(exc_info.value)
        assert "name_col 'nonexistent' not found in DataFrame" in error_msg

    def test_dataframe_invalid_label_col_raises_error(self):
        """Test that non-existent label_col raises error."""
        df = pd.DataFrame({"item_name": ["revenue", "expenses"], 2023: [1000, 600]})

        with pytest.raises(ValueError) as exc_info:
            Model.from_dataframe(df, name_col="item_name", label_col="nonexistent")

        error_msg = str(exc_info.value)
        assert "label_col 'nonexistent' not found in DataFrame" in error_msg

    def test_dataframe_invalid_category_col_raises_error(self):
        """Test that non-existent category_col raises error."""
        df = pd.DataFrame({"item_name": ["revenue", "expenses"], 2023: [1000, 600]})

        with pytest.raises(ValueError) as exc_info:
            Model.from_dataframe(df, name_col="item_name", category_col="nonexistent")

        error_msg = str(exc_info.value)
        assert "category_col 'nonexistent' not found in DataFrame" in error_msg

    def test_dataframe_with_missing_labels(self):
        """Test rows with missing labels when using label_col."""
        df = pd.DataFrame(
            {
                "display_label": ["Revenue", None, "Net Profit"],
                2023: [1000, 600, 400],
                2024: [1200, 700, 500],
            }
        )

        model = Model.from_dataframe(df, label_col="display_label")

        # Row with None label should be skipped (no name can be derived)
        assert "revenue" in model.line_item_names
        assert "net_profit" in model.line_item_names

        # Should only have 2 defined items (excluding category totals)
        defined_items = [
            name for name in model.line_item_names if not name.startswith("total_")
        ]
        assert len(defined_items) == 2
