import pytest
from pyproforma.tables.table_class import format_value, Table, Cell, Row, Column
import pandas as pd


class TestFormatValue:
    """Test cases for the format_value function."""

    def test_format_value_none(self):
        """Test that None value_format returns the original value."""
        assert format_value(123.45, None) == 123.45
        assert format_value("test", None) == "test"
        assert format_value(0, None) == 0

    def test_format_value_str(self):
        """Test string formatting."""
        assert format_value(123.45, 'str') == "123.45"
        assert format_value(0, 'str') == "0"
        assert format_value(-42, 'str') == "-42"

    def test_format_value_no_decimals(self):
        """Test no_decimals formatting - should round and add commas."""
        assert format_value(123.45, 'no_decimals') == "123"
        assert format_value(123.6, 'no_decimals') == "124"  # rounds up
        assert format_value(123.5, 'no_decimals') == "124"
        assert format_value(1234567.89, 'no_decimals') == "1,234,568"  # rounds and adds commas
        assert format_value(0, 'no_decimals') == "0"
        assert format_value(-123.45, 'no_decimals') == "-123"

    def test_format_value_two_decimals(self):
        """Test two_decimals formatting."""
        assert format_value(123.456, 'two_decimals') == "123.46"
        assert format_value(123, 'two_decimals') == "123.00"
        assert format_value(0, 'two_decimals') == "0.00"
        assert format_value(-123.456, 'two_decimals') == "-123.46"

    def test_format_value_percent(self):
        """Test percent formatting - should round to nearest whole percent."""
        assert format_value(0.1234, 'percent') == "12%"
        assert format_value(0.1256, 'percent') == "13%"  # rounds up
        assert format_value(0.5, 'percent') == "50%"
        assert format_value(1.0, 'percent') == "100%"
        assert format_value(0, 'percent') == "0%"
        assert format_value(-0.1234, 'percent') == "-12%"

    def test_format_value_percent_one_decimal(self):
        """Test percent_one_decimal formatting."""
        assert format_value(0.1234, 'percent_one_decimal') == "12.3%"
        assert format_value(0.1256, 'percent_one_decimal') == "12.6%"
        assert format_value(0.1255, 'percent_one_decimal') == "12.6%"
        assert format_value(0.5, 'percent_one_decimal') == "50.0%"
        assert format_value(0, 'percent_one_decimal') == "0.0%"

    def test_format_value_percent_two_decimals(self):
        """Test percent_two_decimals formatting (note the typo in the original)."""
        assert format_value(0.1234, 'percent_two_decimals') == "12.34%"
        assert format_value(0.1256, 'percent_two_decimals') == "12.56%"
        assert format_value(0.5, 'percent_two_decimals') == "50.00%"
        assert format_value(0, 'percent_two_decimals') == "0.00%"

    def test_format_value_invalid_format(self):
        """Test that invalid value_format raises ValueError."""
        with pytest.raises(ValueError, match="Invalid value_format: invalid_format"):
            format_value(123, 'invalid_format')

    def test_format_value_edge_cases(self):
        """Test edge cases and boundary values."""
        # Test very large numbers
        assert format_value(1000000, 'no_decimals') == "1,000,000"
        
        # Test very small percentages
        assert format_value(0.001, 'percent') == "0%"  # rounds to 0
        assert format_value(0.005, 'percent') == "0%"  # rounds to 0 (banker's rounding)
        assert format_value(0.006, 'percent') == "1%"  # rounds to 1
        
        # Test negative values
        assert format_value(-1234.56, 'no_decimals') == "-1,235"
        assert format_value(-0.1234, 'percent') == "-12%"


class TestTableClass:
    """Test cases for the Table, Cell, Row, and Column classes."""

    def test_table_cell_column_number_mismatch(self):
        columns = [Column(label="A"), Column(label="B")]
        rows = [
            Row(cells=[Cell(1), Cell(2)]),
            Row(cells=[Cell(3)])  # This row has only one cell instead of two
        ]
        try:
            table = Table(columns=columns, rows=rows)
        except ValueError as e:
            assert str(e) == "Row 1 has 1 cells, expected 2 based on the number of columns."
        else:
            assert False, "Expected ValueError was not raised."

    def test_table_to_df_simple(self):
        columns = [Column(label="A"), Column(label="B")]
        rows = [
            Row(cells=[Cell(1), Cell(2)]),
            Row(cells=[Cell(3), Cell(4)]),
        ]
        table = Table(columns=columns, rows=rows)
        df = table.to_df()
        expected = pd.DataFrame({"A": [1, 3], "B": [2, 4]})
        pd.testing.assert_frame_equal(df, expected)

    def test_table_to_df_with_none(self):
        columns = [Column(label="X"), Column(label="Y")]
        rows = [
            Row(cells=[Cell(None), Cell(5)]),
            Row(cells=[Cell(7), Cell(None)]),
        ]
        table = Table(columns=columns, rows=rows)
        df = table.to_df()
        expected = pd.DataFrame({"X": [None, 7], "Y": [5, None]})
        pd.testing.assert_frame_equal(df, expected)

    def test_table_to_df_empty(self):
        columns = []
        rows = []
        table = Table(columns=columns, rows=rows)
        df = table.to_df()
        expected = pd.DataFrame()
        pd.testing.assert_frame_equal(df, expected)

    def test_table_get_style_map(self):
        columns = [Column(label="A"), Column(label="B")]
        rows = [
            Row(cells=[Cell(1, bold=True), Cell(2)]),
            Row(cells=[Cell(3, align='center'), Cell(4, bold=True)]),
        ]
        table = Table(columns=columns, rows=rows)
        style_map = table._get_style_map()
        
        expected_style_map = {
            (0, 'A'): 'font-weight: bold; text-align: right;',
            (0, 'B'): 'text-align: right;',
            (1, 'A'): 'text-align: center;',
            (1, 'B'): 'font-weight: bold; text-align: right;'
        }
        
        assert style_map == expected_style_map