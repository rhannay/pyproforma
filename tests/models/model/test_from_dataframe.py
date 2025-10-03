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
        df = pd.DataFrame({
            'name': ['revenue', 'expenses', 'profit'],
            2023: [1000, 600, 400],
            2024: [1200, 700, 500],
            2025: [1400, 800, 600]
        })

        model = Model.from_dataframe(df)

        assert model.years == [2023, 2024, 2025]
        # Note: Model automatically creates category totals,
        # so there are more line items
        assert 'revenue' in model.line_item_names
        assert 'expenses' in model.line_item_names
        assert 'profit' in model.line_item_names

        assert model.value("revenue", 2023) == 1000
        assert model.value("revenue", 2024) == 1200
        assert model.value("revenue", 2025) == 1400
        assert model.value("expenses", 2023) == 600
        assert model.value("profit", 2025) == 600

    def test_dataframe_with_string_years(self):
        """Test creating a model from DataFrame with string year columns."""
        df = pd.DataFrame({
            'item_name': ['revenue', 'costs'],
            '2023': [1000, 400],
            '2024': [1100, 450],
        })

        model = Model.from_dataframe(df)

        assert model.years == [2023, 2024]
        assert 'revenue' in model.line_item_names
        assert 'costs' in model.line_item_names
        assert model.value("revenue", 2023) == 1000
        assert model.value("costs", 2024) == 450

    def test_dataframe_with_mixed_string_and_int_years(self):
        """Test DataFrame with both string and integer year columns."""
        df = pd.DataFrame({
            'name': ['revenue'],
            2023: [1000],
            '2024': [1100],
            2025: [1200]
        })

        model = Model.from_dataframe(df)

        assert model.years == [2023, 2024, 2025]
        assert model.value("revenue", 2024) == 1100

    def test_dataframe_unsorted_years(self):
        """Test that years are sorted even if DataFrame columns are not."""
        df = pd.DataFrame({
            'name': ['revenue'],
            2025: [1200],
            2023: [1000],
            2024: [1100]
        })

        model = Model.from_dataframe(df)

        assert model.years == [2023, 2024, 2025]

    def test_dataframe_with_nan_values(self):
        """Test that NaN values are handled correctly."""
        df = pd.DataFrame({
            'name': ['revenue', 'expenses'],
            2023: [1000, None],
            2024: [1200, 700],
            2025: [None, 800]
        })

        model = Model.from_dataframe(df)

        assert model.years == [2023, 2024, 2025]
        assert model.value("revenue", 2023) == 1000
        assert model.value("revenue", 2024) == 1200
        # Revenue 2025 should be None/missing
        assert model.value("expenses", 2024) == 700

    def test_fill_in_periods_false(self):
        """Test that gaps in years are not filled when fill_in_periods=False."""
        df = pd.DataFrame({
            'name': ['revenue'],
            2023: [1000],
            2025: [1400]
        })

        # Note: validate_periods will not fill gaps by default,
        # but validate_years (used in Model.__init__) requires sequential years
        # So this should raise an error
        with pytest.raises(ValueError) as exc_info:
            Model.from_dataframe(df, fill_in_periods=False)

        error_msg = str(exc_info.value)
        assert "Years must be sequential with no gaps" in error_msg

    def test_fill_in_periods_true(self):
        """Test that gaps in years are filled when fill_in_periods=True."""
        df = pd.DataFrame({
            'name': ['revenue', 'expenses'],
            2023: [1000, 600],
            2025: [1400, 800]
        })

        model = Model.from_dataframe(df, fill_in_periods=True)

        assert model.years == [2023, 2024, 2025]
        assert model.value("revenue", 2023) == 1000
        # 2024 should exist but revenue should be None/0
        assert model.value("revenue", 2025) == 1400

    def test_single_line_item(self):
        """Test creating a model with single line item."""
        df = pd.DataFrame({
            'name': ['revenue'],
            2023: [1000],
            2024: [1100]
        })

        model = Model.from_dataframe(df)

        assert model.years == [2023, 2024]
        assert 'revenue' in model.line_item_names
        assert model.value("revenue", 2023) == 1000

    def test_single_year(self):
        """Test creating a model with single year."""
        df = pd.DataFrame({
            'name': ['revenue', 'expenses'],
            2023: [1000, 600]
        })

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
        df = pd.DataFrame({
            'name': ['revenue', 'expenses']
        })

        with pytest.raises(ValueError) as exc_info:
            Model.from_dataframe(df)

        error_msg = str(exc_info.value)
        assert "must have at least 2 columns" in error_msg

    def test_invalid_year_columns_raise_error(self):
        """Test that invalid year columns raise ValueError."""
        df = pd.DataFrame({
            'name': ['revenue'],
            'invalid': [1000],
            2023: [1100]
        })

        with pytest.raises(ValueError) as exc_info:
            Model.from_dataframe(df)

        error_msg = str(exc_info.value)
        assert "Invalid year" in error_msg or "cannot be converted" in error_msg

    def test_duplicate_years_raise_error(self):
        """Test that duplicate year columns raise ValueError."""
        # Create a DataFrame with duplicate column names by directly
        # using the constructor with duplicate column names
        data = {'name': ['revenue'], 'col1': [1000], 'col2': [1100]}
        df = pd.DataFrame(data, columns=['name', 2023, 2023])

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
        df = pd.DataFrame({
            'item': ['revenue', 'costs'],
            2023: [1000, 400],
            2024: [1100, 450]
        })

        model = Model.from_dataframe(df)

        assert 'revenue' in model.line_item_names
        assert 'costs' in model.line_item_names

    def test_dataframe_with_numeric_line_item_names(self):
        """Test that numeric line item names are converted to strings."""
        df = pd.DataFrame({
            'id': [100, 200],
            2023: [1000, 400],
            2024: [1100, 450]
        })

        model = Model.from_dataframe(df)

        assert '100' in model.line_item_names
        assert '200' in model.line_item_names
        assert model.value("100", 2023) == 1000

    def test_dataframe_skips_rows_with_missing_names(self):
        """Test that rows with missing names are skipped."""
        df = pd.DataFrame({
            'name': ['revenue', None, 'profit'],
            2023: [1000, 600, 400],
            2024: [1200, 700, 500]
        })

        model = Model.from_dataframe(df)

        # Only revenue and profit should be created (row with None name is skipped)
        assert 'revenue' in model.line_item_names
        assert 'profit' in model.line_item_names
        # Check that we only have the 2 defined items (plus category total)
        defined_items = [
            name for name in model.line_item_names
            if not name.startswith('total_')
        ]
        assert len(defined_items) == 2

    def test_dataframe_with_negative_years(self):
        """Test creating model with negative years."""
        df = pd.DataFrame({
            'name': ['revenue'],
            -1: [900],
            0: [1000],
            1: [1100]
        })

        model = Model.from_dataframe(df)

        assert model.years == [-1, 0, 1]
        assert model.value("revenue", -1) == 900
        assert model.value("revenue", 0) == 1000

    def test_dataframe_with_large_years(self):
        """Test creating model with very large year values."""
        df = pd.DataFrame({
            'name': ['revenue'],
            9998: [1000],
            9999: [1100],
            10000: [1200]
        })

        model = Model.from_dataframe(df)

        assert model.years == [9998, 9999, 10000]
        assert model.value("revenue", 9998) == 1000

    def test_fill_in_periods_with_large_gap(self):
        """Test fill_in_periods with a larger gap."""
        df = pd.DataFrame({
            'name': ['revenue'],
            2020: [1000],
            2025: [1500]
        })

        model = Model.from_dataframe(df, fill_in_periods=True)

        assert model.years == [2020, 2021, 2022, 2023, 2024, 2025]
        assert model.value("revenue", 2020) == 1000
        assert model.value("revenue", 2025) == 1500
        # Middle years should have None/0 values

    def test_dataframe_preserves_line_item_order(self):
        """Test that line item order from DataFrame is preserved."""
        df = pd.DataFrame({
            'name': ['zebra', 'alpha', 'beta'],
            2023: [100, 200, 300]
        })

        model = Model.from_dataframe(df)

        # Get line item names in order
        names = model.line_item_names
        assert names[0] == 'zebra'
        assert names[1] == 'alpha'
        assert names[2] == 'beta'

    def test_dataframe_sanitizes_names_with_spaces(self):
        """Test that names with spaces are converted to lowercase with underscores."""
        df = pd.DataFrame({
            'name': ['Gross Profit', 'Net Income', 'Cost of Goods Sold'],
            2023: [100, 200, 300]
        })

        model = Model.from_dataframe(df)

        # Names should be lowercase with spaces replaced with underscores
        assert 'gross_profit' in model.line_item_names
        assert 'net_income' in model.line_item_names
        assert 'cost_of_goods_sold' in model.line_item_names
        assert model.value("gross_profit", 2023) == 100
        assert model.value("net_income", 2023) == 200
        assert model.value("cost_of_goods_sold", 2023) == 300
