import pandas as pd
import pytest

from pyproforma.table import Cell, Table, format_value


class TestFormatValue:
    """Test cases for the format_value function."""

    def test_format_value_none(self):
        """Test that None value_format returns the original value."""
        assert format_value(123.45, None) == 123.45
        assert format_value("test", None) == "test"
        assert format_value(0, None) == 0

    def test_format_value_str(self):
        """Test string formatting."""
        assert format_value(123.45, "str") == "123.45"
        assert format_value(0, "str") == "0"
        assert format_value(-42, "str") == "-42"

    def test_format_value_no_decimals(self):
        """Test no_decimals formatting - should round and add commas."""
        assert format_value(123.45, "no_decimals") == "123"
        assert format_value(123.6, "no_decimals") == "124"  # rounds up
        assert format_value(123.5, "no_decimals") == "124"
        assert (
            format_value(1234567.89, "no_decimals") == "1,234,568"
        )  # rounds and adds commas
        assert format_value(0, "no_decimals") == "0"
        assert format_value(-123.45, "no_decimals") == "-123"

    def test_format_value_two_decimals(self):
        """Test two_decimals formatting."""
        assert format_value(123.456, "two_decimals") == "123.46"
        assert format_value(123, "two_decimals") == "123.00"
        assert format_value(0, "two_decimals") == "0.00"
        assert format_value(-123.456, "two_decimals") == "-123.46"
        assert (
            format_value(1234.56, "two_decimals") == "1,234.56"
        )  # Test with commas for larger numbers

    def test_format_value_percent(self):
        """Test percent formatting - should round to nearest whole percent."""
        assert format_value(0.1234, "percent") == "12%"
        assert format_value(0.1256, "percent") == "13%"  # rounds up
        assert format_value(0.5, "percent") == "50%"
        assert format_value(1.0, "percent") == "100%"
        assert format_value(0, "percent") == "0%"
        assert format_value(-0.1234, "percent") == "-12%"

    def test_format_value_percent_one_decimal(self):
        """Test percent_one_decimal formatting."""
        assert format_value(0.1234, "percent_one_decimal") == "12.3%"
        assert format_value(0.1256, "percent_one_decimal") == "12.6%"
        assert format_value(0.1255, "percent_one_decimal") == "12.6%"
        assert format_value(0.5, "percent_one_decimal") == "50.0%"
        assert format_value(0, "percent_one_decimal") == "0.0%"

    def test_format_value_percent_two_decimals(self):
        """Test percent_two_decimals formatting (note the typo in the original)."""
        assert format_value(0.1234, "percent_two_decimals") == "12.34%"
        assert format_value(0.1256, "percent_two_decimals") == "12.56%"
        assert format_value(0.5, "percent_two_decimals") == "50.00%"
        assert format_value(0, "percent_two_decimals") == "0.00%"

    def test_format_value_invalid_format(self):
        """Test that invalid value_format raises ValueError."""
        with pytest.raises(ValueError, match="Invalid value_format: invalid_format"):
            format_value(123, "invalid_format")

    def test_format_value_edge_cases(self):
        """Test edge cases and boundary values."""
        # Test very large numbers
        assert format_value(1000000, "no_decimals") == "1,000,000"

        # Test very small percentages
        assert format_value(0.001, "percent") == "0%"  # rounds to 0
        assert format_value(0.005, "percent") == "0%"  # rounds to 0 (banker's rounding)
        assert format_value(0.006, "percent") == "1%"  # rounds to 1

        # Test negative values
        assert format_value(-1234.56, "no_decimals") == "-1,235"
        assert format_value(-0.1234, "percent") == "-12%"


class TestTableClass:
    """Test cases for the Table and Cell classes."""

    def test_table_grid_consistency_mismatch(self):
        """Test that mismatched row lengths raise ValueError."""
        cells = [
            [Cell(1), Cell(2)],
            [Cell(3)],  # This row has only one cell instead of two
        ]
        with pytest.raises(ValueError, match="Row 1 has 1 cells, expected 2 cells"):
            Table(cells=cells)

    def test_style_row_bold(self):
        """Test styling a row with bold."""
        table = Table(cells=[
            [Cell("A"), Cell("B"), Cell("C")],
            [Cell(1), Cell(2), Cell(3)],
            [Cell(4), Cell(5), Cell(6)],
        ])
        
        # Style row 0 to be bold
        table.style_row(0, bold=True)
        
        # Check all cells in row 0 are bold
        assert table[0, 0].bold is True
        assert table[0, 1].bold is True
        assert table[0, 2].bold is True
        
        # Check other rows are not affected
        assert table[1, 0].bold is False
        assert table[2, 0].bold is False

    def test_style_row_multiple_properties(self):
        """Test styling a row with multiple properties."""
        table = Table(cells=[
            [Cell("Name"), Cell("Value")],
            [Cell("Item 1"), Cell(100)],
            [Cell("Total"), Cell(200)],
        ])
        
        # Style last row as a total row
        table.style_row(2, bold=True, bottom_border='double', background_color='lightgray')
        
        assert table[2, 0].bold is True
        assert table[2, 0].bottom_border == 'double'
        assert table[2, 0].background_color == 'lightgray'
        assert table[2, 1].bold is True
        assert table[2, 1].bottom_border == 'double'
        assert table[2, 1].background_color == 'lightgray'
        
        # Check other rows are not affected
        assert table[1, 0].bold is False
        assert table[1, 0].bottom_border is None
        assert table[1, 0].background_color is None

    def test_style_row_partial_update(self):
        """Test that style_row only updates specified properties."""
        table = Table(cells=[
            [Cell("A", bold=True, align='left'), Cell("B")],
            [Cell(1, background_color='red'), Cell(2)],
        ])
        
        # Only update bold, should preserve other properties
        table.style_row(1, bold=True)
        
        assert table[1, 0].bold is True
        assert table[1, 0].background_color == 'red'  # Preserved
        assert table[1, 1].bold is True

    def test_style_row_out_of_range(self):
        """Test that styling an out-of-range row raises IndexError."""
        table = Table(cells=[
            [Cell(1), Cell(2)],
            [Cell(3), Cell(4)],
        ])
        
        with pytest.raises(IndexError, match="Row index 2 is out of range"):
            table.style_row(2, bold=True)
        
        with pytest.raises(IndexError, match="Row index -1 is out of range"):
            table.style_row(-1, bold=True)

    def test_style_row_all_properties(self):
        """Test styling a row with all available properties."""
        table = Table(cells=[
            [Cell("A"), Cell("B")],
            [Cell(1), Cell(2)],
        ])
        
        table.style_row(
            1,
            bold=True,
            bottom_border='single',
            top_border='double',
            background_color='yellow',
            font_color='blue',
            align='center',
            value_format='two_decimals'
        )
        
        cell = table[1, 0]
        assert cell.bold is True
        assert cell.bottom_border == 'single'
        assert cell.top_border == 'double'
        assert cell.background_color == 'yellow'
        assert cell.font_color == 'blue'
        assert cell.align == 'center'
        assert cell.value_format == 'two_decimals'

    def test_style_col_bold(self):
        """Test styling a column with bold."""
        table = Table(cells=[
            [Cell("A"), Cell("B"), Cell("C")],
            [Cell(1), Cell(2), Cell(3)],
            [Cell(4), Cell(5), Cell(6)],
        ])
        
        # Style column 0 to be bold
        table.style_col(0, bold=True)
        
        # Check all cells in column 0 are bold
        assert table[0, 0].bold is True
        assert table[1, 0].bold is True
        assert table[2, 0].bold is True
        
        # Check other columns are not affected
        assert table[0, 1].bold is False
        assert table[0, 2].bold is False

    def test_style_col_value_format(self):
        """Test styling a column with value format."""
        table = Table(cells=[
            [Cell("Name"), Cell("Value"), Cell("Percent")],
            [Cell("Item 1"), Cell(100.123), Cell(0.456)],
            [Cell("Item 2"), Cell(200.789), Cell(0.789)],
        ])
        
        # Style value column to have two decimals
        table.style_col(1, value_format='two_decimals', align='right')
        
        assert table[0, 1].value_format == 'two_decimals'
        assert table[1, 1].value_format == 'two_decimals'
        assert table[2, 1].value_format == 'two_decimals'
        assert table[0, 1].align == 'right'
        assert table[1, 1].align == 'right'
        
        # Check other columns are not affected
        assert table[0, 0].value_format is None
        assert table[0, 2].value_format is None

    def test_style_col_multiple_properties(self):
        """Test styling a column with multiple properties."""
        table = Table(cells=[
            [Cell("A"), Cell("B")],
            [Cell(1), Cell(2)],
            [Cell(3), Cell(4)],
        ])
        
        table.style_col(0, bold=True, align='left', background_color='lightblue')
        
        assert table[0, 0].bold is True
        assert table[0, 0].align == 'left'
        assert table[0, 0].background_color == 'lightblue'
        assert table[1, 0].bold is True
        assert table[2, 0].bold is True
        
        # Check other column is not affected
        assert table[0, 1].bold is False
        assert table[0, 1].align == 'right'  # default

    def test_style_col_out_of_range(self):
        """Test that styling an out-of-range column raises IndexError."""
        table = Table(cells=[
            [Cell(1), Cell(2)],
            [Cell(3), Cell(4)],
        ])
        
        with pytest.raises(IndexError, match="Column index 2 is out of range"):
            table.style_col(2, bold=True)
        
        with pytest.raises(IndexError, match="Column index -1 is out of range"):
            table.style_col(-1, bold=True)

    def test_style_col_empty_table(self):
        """Test that styling a column in an empty table raises IndexError."""
        table = Table(cells=[])
        
        with pytest.raises(IndexError, match="Cannot style column in empty table"):
            table.style_col(0, bold=True)

    def test_style_col_partial_update(self):
        """Test that style_col only updates specified properties."""
        table = Table(cells=[
            [Cell("A", bold=True), Cell("B")],
            [Cell(1, background_color='red'), Cell(2)],
        ])
        
        # Only update align, should preserve other properties
        table.style_col(0, align='center')
        
        assert table[0, 0].bold is True  # Preserved
        assert table[0, 0].align == 'center'  # Updated
        assert table[1, 0].background_color == 'red'  # Preserved
        assert table[1, 0].align == 'center'  # Updated

    def test_style_col_all_properties(self):
        """Test styling a column with all available properties."""
        table = Table(cells=[
            [Cell("A"), Cell("B")],
            [Cell(1), Cell(2)],
        ])
        
        table.style_col(
            1,
            bold=True,
            align='right',
            background_color='pink',
            font_color='green',
            value_format='no_decimals',
            bottom_border='single',
            top_border='double'
        )
        
        cell = table[0, 1]
        assert cell.bold is True
        assert cell.align == 'right'
        assert cell.background_color == 'pink'
        assert cell.font_color == 'green'
        assert cell.value_format == 'no_decimals'
        assert cell.bottom_border == 'single'
        assert cell.top_border == 'double'

    def test_style_row_and_col_combined(self):
        """Test that row and column styling can be combined."""
        table = Table(cells=[
            [Cell("Name"), Cell("Value")],
            [Cell("Item 1"), Cell(100)],
            [Cell("Item 2"), Cell(200)],
        ])
        
        # Style header row
        table.style_row(0, bold=True, background_color='gray')
        
        # Style value column
        table.style_col(1, value_format='no_decimals', align='right')
        
        # Header cell in value column should have both styles
        assert table[0, 1].bold is True
        assert table[0, 1].background_color == 'gray'
        assert table[0, 1].value_format == 'no_decimals'
        assert table[0, 1].align == 'right'
        
        # Data cell in value column should only have column styles
        assert table[1, 1].bold is False
        assert table[1, 1].value_format == 'no_decimals'
        assert table[1, 1].align == 'right'

    def test_set_row_values_basic(self):
        """Test basic row value setting with formatting preserved."""
        table = Table(cells=[
            [Cell("A"), Cell("B"), Cell("C")],
            [Cell(1, bold=True), Cell(2, bold=True), Cell(3, bold=True)],
            [Cell(4), Cell(5), Cell(6)],
        ])
        
        # Update row 1, preserving formatting
        table.set_row_values(1, [10, 20, 30])
        
        assert table[1, 0].value == 10
        assert table[1, 1].value == 20
        assert table[1, 2].value == 30
        # Formatting should be preserved
        assert table[1, 0].bold is True
        assert table[1, 1].bold is True
        assert table[1, 2].bold is True

    def test_set_row_values_with_offset(self):
        """Test setting row values with start_col offset."""
        table = Table(cells=[
            [Cell(""), Cell("Q1"), Cell("Q2"), Cell("Q3")],
            [Cell("Revenue"), Cell(1000), Cell(1200), Cell(1100)],
            [Cell("Expenses"), Cell(800), Cell(900), Cell(850)],
        ])
        
        # Update data columns only, skip label
        table.set_row_values(1, [1100, 1250, 1150], start_col=1)
        
        assert table[1, 0].value == "Revenue"  # Label unchanged
        assert table[1, 1].value == 1100
        assert table[1, 2].value == 1250
        assert table[1, 3].value == 1150

    def test_set_row_values_without_preserving_formatting(self):
        """Test setting row values without preserving formatting."""
        table = Table(cells=[
            [Cell("A"), Cell("B")],
            [Cell(1, bold=True, background_color='red'), Cell(2, bold=True)],
        ])
        
        # Update without preserving formatting
        table.set_row_values(1, [100, 200], preserve_formatting=False)
        
        assert table[1, 0].value == 100
        assert table[1, 1].value == 200
        # Formatting should be lost
        assert table[1, 0].bold is False
        assert table[1, 0].background_color is None
        assert table[1, 1].bold is False

    def test_set_row_values_out_of_range_row(self):
        """Test that out of range row index raises IndexError."""
        table = Table(cells=[
            [Cell(1), Cell(2)],
            [Cell(3), Cell(4)],
        ])
        
        with pytest.raises(IndexError, match="Row index 2 is out of range"):
            table.set_row_values(2, [10, 20])

    def test_set_row_values_out_of_range_start_col(self):
        """Test that out of range start_col raises IndexError."""
        table = Table(cells=[
            [Cell(1), Cell(2)],
            [Cell(3), Cell(4)],
        ])
        
        with pytest.raises(IndexError, match="start_col 2 is out of range"):
            table.set_row_values(0, [10], start_col=2)

    def test_set_row_values_too_many_values(self):
        """Test that too many values raises ValueError."""
        table = Table(cells=[
            [Cell(1), Cell(2), Cell(3)],
            [Cell(4), Cell(5), Cell(6)],
        ])
        
        with pytest.raises(ValueError, match="must exactly match number of columns to update"):
            table.set_row_values(0, [10, 20, 30, 40])  # Too many values
        
        with pytest.raises(ValueError, match="must exactly match number of columns to update"):
            table.set_row_values(0, [10, 20, 30], start_col=1)  # Would need only 2 values

    def test_set_row_values_too_few_values(self):
        """Test that too few values raises ValueError."""
        table = Table(cells=[
            [Cell(1), Cell(2), Cell(3)],
            [Cell(4), Cell(5), Cell(6)],
        ])
        
        with pytest.raises(ValueError, match="must exactly match number of columns to update"):
            table.set_row_values(0, [10, 20])  # Too few values (expected 3)
        
        with pytest.raises(ValueError, match="must exactly match number of columns to update"):
            table.set_row_values(0, [10], start_col=1)  # Too few values (expected 2)

    def test_set_row_values_with_cell_objects(self):
        """Test setting row values with Cell objects when not preserving formatting."""
        table = Table(cells=[
            [Cell(1), Cell(2), Cell(3)],
            [Cell(4), Cell(5), Cell(6)],
        ])
        
        # Set with Cell objects
        table.set_row_values(
            1,
            [Cell(40, bold=True), Cell(50, background_color='blue'), 60],
            preserve_formatting=False
        )
        
        assert table[1, 0].value == 40
        assert table[1, 0].bold is True
        assert table[1, 1].value == 50
        assert table[1, 1].background_color == 'blue'
        assert table[1, 2].value == 60

    def test_set_col_values_basic(self):
        """Test basic column value setting with formatting preserved."""
        table = Table(cells=[
            [Cell("A"), Cell("B", bold=True)],
            [Cell(1), Cell(2, bold=True)],
            [Cell(3), Cell(4, bold=True)],
        ])
        
        # Update column 1, preserving formatting
        table.set_col_values(1, ["Updated", 20, 40])
        
        assert table[0, 1].value == "Updated"
        assert table[1, 1].value == 20
        assert table[2, 1].value == 40
        # Formatting should be preserved
        assert table[0, 1].bold is True
        assert table[1, 1].bold is True
        assert table[2, 1].bold is True

    def test_set_col_values_with_offset(self):
        """Test setting column values with start_row offset."""
        table = Table(cells=[
            [Cell(""), Cell("Q1"), Cell("Q2")],
            [Cell("Revenue"), Cell(1000), Cell(1200)],
            [Cell("Expenses"), Cell(800), Cell(900)],
            [Cell("Profit"), Cell(200), Cell(300)],
        ])
        
        # Update data rows only, skip header
        table.set_col_values(1, [1100, 850, 250], start_row=1)
        
        assert table[0, 1].value == "Q1"  # Header unchanged
        assert table[1, 1].value == 1100
        assert table[2, 1].value == 850
        assert table[3, 1].value == 250

    def test_set_col_values_without_preserving_formatting(self):
        """Test setting column values without preserving formatting."""
        table = Table(cells=[
            [Cell("A"), Cell("B")],
            [Cell(1), Cell(2, bold=True, align='center')],
            [Cell(3), Cell(4, bold=True)],
        ])
        
        # Update without preserving formatting
        table.set_col_values(1, ["New", 20, 40], preserve_formatting=False)
        
        assert table[0, 1].value == "New"
        assert table[1, 1].value == 20
        assert table[2, 1].value == 40
        # Formatting should be lost
        assert table[1, 1].bold is False
        assert table[1, 1].align == 'right'  # default
        assert table[2, 1].bold is False

    def test_set_col_values_empty_table(self):
        """Test that setting column values in empty table raises IndexError."""
        table = Table(cells=[])
        
        with pytest.raises(IndexError, match="Cannot set column values in empty table"):
            table.set_col_values(0, [1, 2, 3])

    def test_set_col_values_out_of_range_col(self):
        """Test that out of range column index raises IndexError."""
        table = Table(cells=[
            [Cell(1), Cell(2)],
            [Cell(3), Cell(4)],
        ])
        
        with pytest.raises(IndexError, match="Column index 2 is out of range"):
            table.set_col_values(2, [10, 20])

    def test_set_col_values_out_of_range_start_row(self):
        """Test that out of range start_row raises IndexError."""
        table = Table(cells=[
            [Cell(1), Cell(2)],
            [Cell(3), Cell(4)],
        ])
        
        with pytest.raises(IndexError, match="start_row 2 is out of range"):
            table.set_col_values(0, [10], start_row=2)

    def test_set_col_values_too_many_values(self):
        """Test that too many values raises ValueError."""
        table = Table(cells=[
            [Cell(1), Cell(2)],
            [Cell(3), Cell(4)],
            [Cell(5), Cell(6)],
        ])
        
        with pytest.raises(ValueError, match="must exactly match number of rows to update"):
            table.set_col_values(0, [10, 20, 30, 40])  # Too many values
        
        with pytest.raises(ValueError, match="must exactly match number of rows to update"):
            table.set_col_values(0, [10, 20, 30], start_row=1)  # Would need only 2 values

    def test_set_col_values_too_few_values(self):
        """Test that too few values raises ValueError."""
        table = Table(cells=[
            [Cell(1), Cell(2)],
            [Cell(3), Cell(4)],
            [Cell(5), Cell(6)],
        ])
        
        with pytest.raises(ValueError, match="must exactly match number of rows to update"):
            table.set_col_values(0, [10, 20])  # Too few values (expected 3)
        
        with pytest.raises(ValueError, match="must exactly match number of rows to update"):
            table.set_col_values(0, [10], start_row=1)  # Too few values (expected 2)

    def test_set_col_values_with_cell_objects(self):
        """Test setting column values with Cell objects when not preserving formatting."""
        table = Table(cells=[
            [Cell(1), Cell(2)],
            [Cell(3), Cell(4)],
            [Cell(5), Cell(6)],
        ])
        
        # Set with Cell objects
        table.set_col_values(
            1,
            [Cell(20, bold=True), Cell(40, background_color='green'), 60],
            preserve_formatting=False
        )
        
        assert table[0, 1].value == 20
        assert table[0, 1].bold is True
        assert table[1, 1].value == 40
        assert table[1, 1].background_color == 'green'
        assert table[2, 1].value == 60

    def test_set_row_and_col_values_combined(self):
        """Test that row and column value setting can be combined."""
        table = Table(cells=[
            [Cell(""), Cell("Q1"), Cell("Q2")],
            [Cell("Revenue"), Cell(1000), Cell(1200)],
            [Cell("Expenses"), Cell(800), Cell(900)],
        ])
        
        # Update a row of data
        table.set_row_values(1, [1100, 1250], start_col=1)
        
        # Update a column of data
        table.set_col_values(1, [1150, 850], start_row=1)
        
        assert table[1, 1].value == 1150  # Updated by col (last operation)
        assert table[1, 2].value == 1250  # Updated by row
        assert table[2, 1].value == 850   # Updated by col

    def test_table_to_dataframe_simple(self):
        """Test basic table to DataFrame conversion."""
        cells = [
            [Cell("A"), Cell("B")],  # Header row
            [Cell(1), Cell(2)],
            [Cell(3), Cell(4)],
        ]
        table = Table(cells=cells)
        df = table.to_dataframe()
        expected = pd.DataFrame({"A": [1, 3], "B": [2, 4]})
        pd.testing.assert_frame_equal(df, expected)

    def test_table_to_dataframe_with_none(self):
        """Test DataFrame conversion with None values."""
        cells = [
            [Cell("X"), Cell("Y")],  # Header row
            [Cell(None), Cell(5)],
            [Cell(7), Cell(None)],
        ]
        table = Table(cells=cells)
        df = table.to_dataframe()
        expected = pd.DataFrame({"X": [None, 7], "Y": [5, None]})
        pd.testing.assert_frame_equal(df, expected)

    def test_table_to_dataframe_empty(self):
        """Test DataFrame conversion with empty table."""
        cells = []
        table = Table(cells=cells)
        df = table.to_dataframe()
        expected = pd.DataFrame()
        pd.testing.assert_frame_equal(df, expected)

    def test_table_to_dataframe_only_header(self):
        """Test DataFrame conversion with only header row."""
        cells = [
            [Cell("A"), Cell("B")],  # Header row only
        ]
        table = Table(cells=cells)
        df = table.to_dataframe()
        expected = pd.DataFrame()
        pd.testing.assert_frame_equal(df, expected)

    def test_table_get_style_map(self):
        """Test that style map is generated correctly."""
        cells = [
            [Cell("A"), Cell("B")],  # Header row
            [Cell(1, bold=True), Cell(2)],
            [Cell(3, align="center"), Cell(4, bold=True)],
        ]
        table = Table(cells=cells)
        style_map = table._get_style_map()

        expected_style_map = {
            (0, "A"): "font-weight: bold; text-align: right;",
            (0, "B"): "text-align: right;",
            (1, "A"): "text-align: center;",
            (1, "B"): "font-weight: bold; text-align: right;",
        }

        assert style_map == expected_style_map


class TestTableIndexing:
    """Test cases for Table indexing functionality."""

    def test_getitem_basic(self):
        """Test basic cell access using table[row, col]."""
        cells = [
            [Cell("A"), Cell("B")],
            [Cell(1), Cell(2)],
            [Cell(3), Cell(4)],
        ]
        table = Table(cells=cells)
        
        assert table[0, 0].value == "A"
        assert table[0, 1].value == "B"
        assert table[1, 0].value == 1
        assert table[1, 1].value == 2
        assert table[2, 0].value == 3
        assert table[2, 1].value == 4

    def test_getitem_with_formatting(self):
        """Test accessing cells with formatting properties."""
        cells = [
            [Cell("Header", bold=True, align="center")],
            [Cell(100, value_format="no_decimals")],
        ]
        table = Table(cells=cells)
        
        header_cell = table[0, 0]
        assert header_cell.value == "Header"
        assert header_cell.bold is True
        assert header_cell.align == "center"
        
        value_cell = table[1, 0]
        assert value_cell.value == 100
        assert value_cell.value_format == "no_decimals"

    def test_getitem_out_of_range_row(self):
        """Test that accessing out of range row raises IndexError."""
        cells = [[Cell(1), Cell(2)]]
        table = Table(cells=cells)
        
        with pytest.raises(IndexError, match="Row index 1 is out of range"):
            _ = table[1, 0]
        
        with pytest.raises(IndexError, match="Row index -1 is out of range"):
            _ = table[-1, 0]

    def test_getitem_out_of_range_col(self):
        """Test that accessing out of range column raises IndexError."""
        cells = [[Cell(1), Cell(2)]]
        table = Table(cells=cells)
        
        with pytest.raises(IndexError, match="Column index 2 is out of range"):
            _ = table[0, 2]
        
        with pytest.raises(IndexError, match="Column index -1 is out of range"):
            _ = table[0, -1]

    def test_getitem_empty_table(self):
        """Test that accessing empty table raises IndexError."""
        table = Table(cells=[])
        
        with pytest.raises(IndexError, match="Cannot index into an empty table"):
            _ = table[0, 0]

    def test_getitem_invalid_key_type(self):
        """Test that invalid key types raise TypeError."""
        cells = [[Cell(1), Cell(2)]]
        table = Table(cells=cells)
        
        with pytest.raises(TypeError, match="Table indices must be a tuple"):
            _ = table[0]
        
        with pytest.raises(TypeError, match="Row and column indices must be integers"):
            _ = table["0", 0]
        
        with pytest.raises(TypeError, match="Row and column indices must be integers"):
            _ = table[0, "1"]

    def test_setitem_with_cell(self):
        """Test setting a cell using table[row, col] = Cell()."""
        cells = [
            [Cell("A"), Cell("B")],
            [Cell(1), Cell(2)],
        ]
        table = Table(cells=cells)
        
        new_cell = Cell(value=100, bold=True, align="center")
        table[1, 1] = new_cell
        
        assert table[1, 1].value == 100
        assert table[1, 1].bold is True
        assert table[1, 1].align == "center"

    def test_setitem_with_value(self):
        """Test setting a cell with a raw value (auto-converts to Cell)."""
        cells = [
            [Cell("A"), Cell("B")],
            [Cell(1), Cell(2)],
        ]
        table = Table(cells=cells)
        
        table[1, 0] = 999
        
        assert table[1, 0].value == 999
        assert isinstance(table[1, 0], Cell)

    def test_setitem_out_of_range_row(self):
        """Test that setting out of range row raises IndexError."""
        cells = [[Cell(1), Cell(2)]]
        table = Table(cells=cells)
        
        with pytest.raises(IndexError, match="Row index 1 is out of range"):
            table[1, 0] = Cell(100)

    def test_setitem_out_of_range_col(self):
        """Test that setting out of range column raises IndexError."""
        cells = [[Cell(1), Cell(2)]]
        table = Table(cells=cells)
        
        with pytest.raises(IndexError, match="Column index 2 is out of range"):
            table[0, 2] = Cell(100)

    def test_setitem_empty_table(self):
        """Test that setting in empty table raises IndexError."""
        table = Table(cells=[])
        
        with pytest.raises(IndexError, match="Cannot index into an empty table"):
            table[0, 0] = Cell(1)

    def test_modify_cell_in_place(self):
        """Test modifying a cell's properties in place like table[row, col].bold = True."""
        cells = [
            [Cell("Header"), Cell("Value")],
            [Cell(1), Cell(2)],
        ]
        table = Table(cells=cells)
        
        # Modify cell properties in place
        table[0, 0].bold = True
        table[0, 0].align = "left"
        table[1, 1].value_format = "no_decimals"
        
        # Verify changes
        assert table[0, 0].bold is True
        assert table[0, 0].align == "left"
        assert table[1, 1].value_format == "no_decimals"


class TestTableProperties:
    """Test cases for Table properties (row_count, col_count)."""

    def test_row_count_basic(self):
        """Test row_count property."""
        cells = [
            [Cell(1), Cell(2)],
            [Cell(3), Cell(4)],
            [Cell(5), Cell(6)],
        ]
        table = Table(cells=cells)
        assert table.row_count == 3

    def test_col_count_basic(self):
        """Test col_count property."""
        cells = [
            [Cell(1), Cell(2), Cell(3)],
            [Cell(4), Cell(5), Cell(6)],
        ]
        table = Table(cells=cells)
        assert table.col_count == 3

    def test_row_count_empty_table(self):
        """Test row_count for empty table."""
        table = Table(cells=[])
        assert table.row_count == 0

    def test_col_count_empty_table(self):
        """Test col_count for empty table."""
        table = Table(cells=[])
        assert table.col_count == 0

    def test_row_count_single_row(self):
        """Test row_count with single row."""
        cells = [[Cell(1), Cell(2), Cell(3)]]
        table = Table(cells=cells)
        assert table.row_count == 1
        assert table.col_count == 3


class TestTableInitialization:
    """Test cases for Table initialization with different input types."""

    def test_init_with_cells(self):
        """Test initializing with Cell objects."""
        cells = [
            [Cell("A"), Cell("B")],
            [Cell(1), Cell(2)],
        ]
        table = Table(cells=cells)
        
        assert table.row_count == 2
        assert table.col_count == 2
        assert table[0, 0].value == "A"
        assert table[1, 1].value == 2

    def test_init_with_values(self):
        """Test initializing with raw values (auto-converts to Cells)."""
        cells = [
            ["Name", "Age"],
            ["Alice", 30],
            ["Bob", 25],
        ]
        table = Table(cells=cells)
        
        assert table.row_count == 3
        assert table.col_count == 2
        assert table[0, 0].value == "Name"
        assert table[1, 0].value == "Alice"
        assert table[1, 1].value == 30
        assert isinstance(table[0, 0], Cell)
        assert isinstance(table[1, 1], Cell)

    def test_init_with_mixed_cells_and_values(self):
        """Test initializing with mix of Cells and raw values."""
        cells = [
            [Cell("Header1", bold=True), "Header2"],
            [100, Cell(200, value_format="no_decimals")],
        ]
        table = Table(cells=cells)
        
        assert table[0, 0].value == "Header1"
        assert table[0, 0].bold is True
        assert table[0, 1].value == "Header2"
        assert isinstance(table[0, 1], Cell)
        assert table[1, 0].value == 100
        assert table[1, 1].value == 200
        assert table[1, 1].value_format == "no_decimals"

    def test_init_empty(self):
        """Test initializing with empty cells list."""
        table = Table(cells=[])
        assert table.row_count == 0
        assert table.col_count == 0

    def test_init_none(self):
        """Test initializing with None (creates empty table)."""
        table = Table(cells=None)
        assert table.row_count == 0
        assert table.col_count == 0
        
    def test_init_default(self):
        """Test initializing without arguments (creates empty table)."""
        table = Table()
        assert table.row_count == 0
        assert table.col_count == 0

    def test_init_validates_grid_consistency(self):
        """Test that initialization validates grid consistency."""
        cells = [
            ["A", "B"],
            ["C"],  # Mismatched row length
        ]
        with pytest.raises(ValueError, match="Row 1 has 1 cells, expected 2 cells"):
            Table(cells=cells)

    def test_set_range_values_basic(self):
        """Test basic range value setting with formatting preserved."""
        table = Table(cells=[
            [Cell("A", bold=True), Cell("B", bold=True), Cell("C", bold=True)],
            [Cell(1, align="left"), Cell(2, align="left"), Cell(3, align="left")],
            [Cell(4), Cell(5), Cell(6)],
            [Cell(7), Cell(8), Cell(9)],
        ])
        
        # Update a 2x2 range, preserving formatting
        table.set_range_values(
            start=(1, 1),
            end=(2, 2),
            values=[[20, 30], [50, 60]]
        )
        
        # Check values were updated
        assert table[1, 1].value == 20
        assert table[1, 2].value == 30
        assert table[2, 1].value == 50
        assert table[2, 2].value == 60
        # Check formatting was preserved
        assert table[1, 1].align == "left"
        assert table[1, 2].align == "left"
        # Check unaffected cells
        assert table[1, 0].value == 1
        assert table[2, 0].value == 4
        assert table[3, 1].value == 8

    def test_set_range_values_single_cell(self):
        """Test setting a single cell using range notation."""
        table = Table(cells=[
            [Cell(1), Cell(2), Cell(3)],
            [Cell(4), Cell(5), Cell(6)],
        ])
        
        table.set_range_values(start=(0, 1), end=(0, 1), values=[[99]])
        
        assert table[0, 1].value == 99
        assert table[0, 0].value == 1  # Unchanged
        assert table[0, 2].value == 3  # Unchanged

    def test_set_range_values_full_table(self):
        """Test setting values for the entire table."""
        table = Table(cells=[
            [Cell(1), Cell(2)],
            [Cell(3), Cell(4)],
        ])
        
        table.set_range_values(
            start=(0, 0),
            end=(1, 1),
            values=[[10, 20], [30, 40]]
        )
        
        assert table[0, 0].value == 10
        assert table[0, 1].value == 20
        assert table[1, 0].value == 30
        assert table[1, 1].value == 40

    def test_set_range_values_without_preserving_formatting(self):
        """Test setting range values without preserving formatting."""
        table = Table(cells=[
            [Cell(1, bold=True), Cell(2, bold=True), Cell(3, bold=True)],
            [Cell(4, background_color='red'), Cell(5, background_color='red'), Cell(6)],
        ])
        
        table.set_range_values(
            start=(1, 0),
            end=(1, 1),
            values=[[40, 50]],
            preserve_formatting=False
        )
        
        assert table[1, 0].value == 40
        assert table[1, 1].value == 50
        # Formatting should be lost
        assert table[1, 0].background_color is None
        assert table[1, 1].background_color is None
        # Unaffected cell should preserve formatting
        assert table[1, 2].value == 6

    def test_set_range_values_invalid_start_tuple(self):
        """Test that invalid start tuple raises TypeError."""
        table = Table(cells=[[Cell(1), Cell(2)], [Cell(3), Cell(4)]])
        
        with pytest.raises(TypeError, match="start must be a tuple of \\(row, col\\)"):
            table.set_range_values(start=[0, 0], end=(1, 1), values=[[10, 20], [30, 40]])
        
        with pytest.raises(TypeError, match="start must be a tuple of \\(row, col\\)"):
            table.set_range_values(start=(0,), end=(1, 1), values=[[10, 20], [30, 40]])

    def test_set_range_values_invalid_end_tuple(self):
        """Test that invalid end tuple raises TypeError."""
        table = Table(cells=[[Cell(1), Cell(2)], [Cell(3), Cell(4)]])
        
        with pytest.raises(TypeError, match="end must be a tuple of \\(row, col\\)"):
            table.set_range_values(start=(0, 0), end=[1, 1], values=[[10, 20], [30, 40]])

    def test_set_range_values_non_integer_coordinates(self):
        """Test that non-integer coordinates raise TypeError."""
        table = Table(cells=[[Cell(1), Cell(2)], [Cell(3), Cell(4)]])
        
        with pytest.raises(TypeError, match="start coordinates must be integers"):
            table.set_range_values(start=(0.5, 0), end=(1, 1), values=[[10, 20], [30, 40]])
        
        with pytest.raises(TypeError, match="end coordinates must be integers"):
            table.set_range_values(start=(0, 0), end=(1, "1"), values=[[10, 20], [30, 40]])

    def test_set_range_values_out_of_range(self):
        """Test that out of range coordinates raise IndexError."""
        table = Table(cells=[[Cell(1), Cell(2)], [Cell(3), Cell(4)]])
        
        with pytest.raises(IndexError, match="start row 2 is out of range"):
            table.set_range_values(start=(2, 0), end=(2, 1), values=[[10, 20]])
        
        with pytest.raises(IndexError, match="end col 2 is out of range"):
            table.set_range_values(start=(0, 0), end=(1, 2), values=[[10, 20, 30], [40, 50, 60]])

    def test_set_range_values_start_after_end(self):
        """Test that start after end raises ValueError."""
        table = Table(cells=[[Cell(1), Cell(2), Cell(3)], [Cell(4), Cell(5), Cell(6)]])
        
        with pytest.raises(ValueError, match="start row \\(1\\) must be <= end row \\(0\\)"):
            table.set_range_values(start=(1, 0), end=(0, 1), values=[[10, 20]])
        
        with pytest.raises(ValueError, match="start col \\(2\\) must be <= end col \\(1\\)"):
            table.set_range_values(start=(0, 2), end=(0, 1), values=[[10]])

    def test_set_range_values_dimension_mismatch_rows(self):
        """Test that values with wrong number of rows raises ValueError."""
        table = Table(cells=[[Cell(1), Cell(2)], [Cell(3), Cell(4)], [Cell(5), Cell(6)]])
        
        # Range needs 2 rows, but values has 3
        with pytest.raises(ValueError, match="values has 3 rows but range requires 2 rows"):
            table.set_range_values(start=(0, 0), end=(1, 1), values=[[10, 20], [30, 40], [50, 60]])

    def test_set_range_values_dimension_mismatch_cols(self):
        """Test that values with wrong number of columns raises ValueError."""
        table = Table(cells=[[Cell(1), Cell(2), Cell(3)], [Cell(4), Cell(5), Cell(6)]])
        
        # Range needs 2 columns, but values row has 3
        with pytest.raises(ValueError, match="values row 0 has 3 columns but range requires 2 columns"):
            table.set_range_values(start=(0, 0), end=(1, 1), values=[[10, 20, 30], [40, 50]])

    def test_set_range_values_empty_table(self):
        """Test that setting range in empty table raises IndexError."""
        table = Table(cells=[])
        
        with pytest.raises(IndexError, match="Cannot set range in empty table"):
            table.set_range_values(start=(0, 0), end=(0, 0), values=[[10]])

    def test_style_range_basic(self):
        """Test basic range styling."""
        table = Table(cells=[
            [Cell("A"), Cell("B"), Cell("C")],
            [Cell(1), Cell(2), Cell(3)],
            [Cell(4), Cell(5), Cell(6)],
        ])
        
        # Style a 2x2 range
        table.style_range(
            start=(0, 0),
            end=(1, 1),
            bold=True,
            background_color='lightgray'
        )
        
        # Check range was styled
        assert table[0, 0].bold is True
        assert table[0, 0].background_color == 'lightgray'
        assert table[0, 1].bold is True
        assert table[0, 1].background_color == 'lightgray'
        assert table[1, 0].bold is True
        assert table[1, 0].background_color == 'lightgray'
        assert table[1, 1].bold is True
        assert table[1, 1].background_color == 'lightgray'
        
        # Check unaffected cells
        assert table[0, 2].bold is False
        assert table[0, 2].background_color is None
        assert table[2, 0].bold is False

    def test_style_range_single_cell(self):
        """Test styling a single cell using range notation."""
        table = Table(cells=[
            [Cell(1), Cell(2), Cell(3)],
            [Cell(4), Cell(5), Cell(6)],
        ])
        
        table.style_range(
            start=(1, 1),
            end=(1, 1),
            bold=True,
            font_color='red'
        )
        
        assert table[1, 1].bold is True
        assert table[1, 1].font_color == 'red'
        # Other cells should be unchanged
        assert table[1, 0].bold is False
        assert table[1, 2].bold is False

    def test_style_range_all_properties(self):
        """Test styling a range with all available properties."""
        table = Table(cells=[
            [Cell(1), Cell(2), Cell(3)],
            [Cell(4), Cell(5), Cell(6)],
        ])
        
        table.style_range(
            start=(0, 1),
            end=(1, 2),
            bold=True,
            bottom_border='double',
            top_border='single',
            background_color='yellow',
            font_color='blue',
            align='center',
            value_format='two_decimals'
        )
        
        # Check all properties on one cell in the range
        cell = table[0, 1]
        assert cell.bold is True
        assert cell.bottom_border == 'double'
        assert cell.top_border == 'single'
        assert cell.background_color == 'yellow'
        assert cell.font_color == 'blue'
        assert cell.align == 'center'
        assert cell.value_format == 'two_decimals'
        
        # Check another cell in the range
        cell2 = table[1, 2]
        assert cell2.bold is True
        assert cell2.background_color == 'yellow'

    def test_style_range_partial_update(self):
        """Test that style_range only updates specified properties."""
        table = Table(cells=[
            [Cell(1, bold=True, align='left'), Cell(2)],
            [Cell(3, background_color='red'), Cell(4)],
        ])
        
        # Only update background_color
        table.style_range(start=(0, 0), end=(1, 1), background_color='green')
        
        # Should preserve existing properties and add new one
        assert table[0, 0].bold is True  # Preserved
        assert table[0, 0].align == 'left'  # Preserved
        assert table[0, 0].background_color == 'green'  # Updated
        assert table[1, 0].background_color == 'green'  # Updated from red

    def test_style_range_header_row(self):
        """Test styling entire header row as a range."""
        table = Table(cells=[
            [Cell("Name"), Cell("Q1"), Cell("Q2"), Cell("Q3")],
            [Cell("Item 1"), Cell(100), Cell(200), Cell(300)],
            [Cell("Item 2"), Cell(150), Cell(250), Cell(350)],
        ])
        
        # Style header row
        table.style_range(
            start=(0, 0),
            end=(0, 3),
            bold=True,
            background_color='lightgray',
            align='center'
        )
        
        for col in range(4):
            assert table[0, col].bold is True
            assert table[0, col].background_color == 'lightgray'
            assert table[0, col].align == 'center'
        
        # Data rows should be unchanged
        assert table[1, 0].bold is False

    def test_style_range_data_area(self):
        """Test styling a data area (excluding labels)."""
        table = Table(cells=[
            [Cell(""), Cell("Q1"), Cell("Q2")],
            [Cell("Revenue"), Cell(1000), Cell(1200)],
            [Cell("Expenses"), Cell(800), Cell(900)],
        ])
        
        # Style only the numeric data
        table.style_range(
            start=(1, 1),
            end=(2, 2),
            value_format='no_decimals',
            align='right'
        )
        
        assert table[1, 1].value_format == 'no_decimals'
        assert table[1, 1].align == 'right'
        assert table[2, 2].value_format == 'no_decimals'
        # Labels should be unchanged
        assert table[1, 0].value_format is None

    def test_style_range_total_line(self):
        """Test styling a total line with borders."""
        table = Table(cells=[
            [Cell("Item"), Cell("Value")],
            [Cell("A"), Cell(100)],
            [Cell("B"), Cell(200)],
            [Cell("Total"), Cell(300)],
        ])
        
        # Style total row with borders
        table.style_range(
            start=(3, 0),
            end=(3, 1),
            bold=True,
            top_border='single',
            bottom_border='double'
        )
        
        assert table[3, 0].bold is True
        assert table[3, 0].top_border == 'single'
        assert table[3, 0].bottom_border == 'double'
        assert table[3, 1].bold is True
        assert table[3, 1].bottom_border == 'double'

    def test_style_range_invalid_start_tuple(self):
        """Test that invalid start tuple raises TypeError."""
        table = Table(cells=[[Cell(1), Cell(2)], [Cell(3), Cell(4)]])
        
        with pytest.raises(TypeError, match="start must be a tuple of \\(row, col\\)"):
            table.style_range(start=[0, 0], end=(1, 1), bold=True)

    def test_style_range_invalid_end_tuple(self):
        """Test that invalid end tuple raises TypeError."""
        table = Table(cells=[[Cell(1), Cell(2)], [Cell(3), Cell(4)]])
        
        with pytest.raises(TypeError, match="end must be a tuple of \\(row, col\\)"):
            table.style_range(start=(0, 0), end=[1, 1], bold=True)

    def test_style_range_non_integer_coordinates(self):
        """Test that non-integer coordinates raise TypeError."""
        table = Table(cells=[[Cell(1), Cell(2)], [Cell(3), Cell(4)]])
        
        with pytest.raises(TypeError, match="start coordinates must be integers"):
            table.style_range(start=(0.5, 0), end=(1, 1), bold=True)
        
        with pytest.raises(TypeError, match="end coordinates must be integers"):
            table.style_range(start=(0, 0), end=(1, "1"), bold=True)

    def test_style_range_out_of_range(self):
        """Test that out of range coordinates raise IndexError."""
        table = Table(cells=[[Cell(1), Cell(2)], [Cell(3), Cell(4)]])
        
        with pytest.raises(IndexError, match="start row 2 is out of range"):
            table.style_range(start=(2, 0), end=(2, 1), bold=True)
        
        with pytest.raises(IndexError, match="end col 2 is out of range"):
            table.style_range(start=(0, 0), end=(1, 2), bold=True)

    def test_style_range_start_after_end(self):
        """Test that start after end raises ValueError."""
        table = Table(cells=[[Cell(1), Cell(2), Cell(3)], [Cell(4), Cell(5), Cell(6)]])
        
        with pytest.raises(ValueError, match="start row \\(1\\) must be <= end row \\(0\\)"):
            table.style_range(start=(1, 0), end=(0, 1), bold=True)
        
        with pytest.raises(ValueError, match="start col \\(2\\) must be <= end col \\(1\\)"):
            table.style_range(start=(0, 2), end=(0, 1), bold=True)

    def test_style_range_empty_table(self):
        """Test that styling range in empty table raises IndexError."""
        table = Table(cells=[])
        
        with pytest.raises(IndexError, match="Cannot style range in empty table"):
            table.style_range(start=(0, 0), end=(0, 0), bold=True)

    def test_set_range_values_and_style_range_combined(self):
        """Test that set_range_values and style_range work together."""
        table = Table(cells=[
            [Cell("Name"), Cell("Q1"), Cell("Q2")],
            [Cell("Revenue"), Cell(0), Cell(0)],
            [Cell("Expenses"), Cell(0), Cell(0)],
        ])
        
        # Set values for data area
        table.set_range_values(
            start=(1, 1),
            end=(2, 2),
            values=[[1000, 1200], [800, 900]]
        )
        
        # Style the same area
        table.style_range(
            start=(1, 1),
            end=(2, 2),
            value_format='no_decimals',
            align='right',
            background_color='lightyellow'
        )
        
        # Check both values and styling
        assert table[1, 1].value == 1000
        assert table[1, 1].value_format == 'no_decimals'
        assert table[1, 1].background_color == 'lightyellow'
        assert table[2, 2].value == 900
        assert table[2, 2].align == 'right'
