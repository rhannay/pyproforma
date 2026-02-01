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
