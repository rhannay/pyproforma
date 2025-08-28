import pandas as pd
import pytest

from pyproforma.tables.table_class import Cell, Column, Row, Table


class TestTableTranspose:
    """Test cases for the Table.transpose() method."""

    def test_transpose_simple_2x2(self):
        """Test transposing a simple 2x2 table."""
        columns = [Column(label="A"), Column(label="B")]
        rows = [
            Row(cells=[Cell("X"), Cell(1)]),
            Row(cells=[Cell("Y"), Cell(2)]),
        ]
        table = Table(columns=columns, rows=rows)
        
        transposed = table.transpose()
        
        # Check structure
        assert len(transposed.columns) == 3  # "A", "X", "Y"
        assert len(transposed.rows) == 1     # "B" row
        
        # Check column labels
        assert transposed.columns[0].label == "A"  # Preserved original first column header
        assert transposed.columns[1].label == "X"  
        assert transposed.columns[2].label == "Y"
        
        # Check row data
        # First row should be ["B", 1, 2] (values from original second column)
        assert transposed.rows[0].cells[0].value == "B"
        assert transposed.rows[0].cells[1].value == 1
        assert transposed.rows[0].cells[2].value == 2

    def test_transpose_rectangular_3x2(self):
        """Test transposing a rectangular 3x2 table."""
        columns = [Column(label="Col1"), Column(label="Col2"), Column(label="Col3")]
        rows = [
            Row(cells=[Cell("Row1"), Cell(1), Cell(2)]),
            Row(cells=[Cell("Row2"), Cell(3), Cell(4)]),
        ]
        table = Table(columns=columns, rows=rows)
        
        transposed = table.transpose()
        
        # Check dimensions: should be 3 columns x 2 rows  
        assert len(transposed.columns) == 3  # "Col1", "Row1", "Row2"
        assert len(transposed.rows) == 2     # "Col2", "Col3" rows
        
        # Check column labels
        assert transposed.columns[0].label == "Col1"  # Preserved original first column header
        assert transposed.columns[1].label == "Row1"
        assert transposed.columns[2].label == "Row2"
        
        # Check first row (original second column data)
        assert transposed.rows[0].cells[0].value == "Col2"  
        assert transposed.rows[0].cells[1].value == 1
        assert transposed.rows[0].cells[2].value == 3
        
        # Check second row (original third column data)
        assert transposed.rows[1].cells[0].value == "Col3"
        assert transposed.rows[1].cells[1].value == 2  
        assert transposed.rows[1].cells[2].value == 4

    def test_transpose_with_different_data_types(self):
        """Test transposing with various data types."""
        columns = [Column(label="Numbers"), Column(label="Strings"), Column(label="Extra")]
        rows = [
            Row(cells=[Cell("Type1"), Cell(42), Cell("hello")]),
            Row(cells=[Cell("Type2"), Cell(3.14), Cell("world")]),
            Row(cells=[Cell("Type3"), Cell(None), Cell(None)]),
        ]
        table = Table(columns=columns, rows=rows)
        
        transposed = table.transpose()
        
        # Check that different data types are preserved
        assert transposed.columns[0].label == "Numbers"  # Preserved original first column header
        assert transposed.columns[1].label == "Type1"
        assert transposed.columns[2].label == "Type2" 
        assert transposed.columns[3].label == "Type3"
        
        # Check strings column (original second column)
        assert transposed.rows[0].cells[0].value == "Strings"
        assert transposed.rows[0].cells[1].value == 42
        assert transposed.rows[0].cells[2].value == 3.14
        assert transposed.rows[0].cells[3].value is None
        
        # Check extra column (original third column)
        assert transposed.rows[1].cells[0].value == "Extra"
        assert transposed.rows[1].cells[1].value == "hello"
        assert transposed.rows[1].cells[2].value == "world"
        assert transposed.rows[1].cells[3].value is None

    def test_transpose_preserves_cell_formatting(self):
        """Test that cell formatting is preserved during transpose."""
        columns = [Column(label="A"), Column(label="B")]
        rows = [
            Row(cells=[
                Cell("X", bold=True, align="center"), 
                Cell(1, bold=True, background_color="red", value_format="no_decimals")
            ]),
            Row(cells=[
                Cell("Y", font_color="blue"), 
                Cell(2, bottom_border="double")
            ]),
        ]
        table = Table(columns=columns, rows=rows)
        
        transposed = table.transpose()
        
        # Check that formatting is preserved in the transposed cells
        # Original cell (0,1) -> transposed cell (0,1)  
        assert transposed.rows[0].cells[1].bold is True
        assert transposed.rows[0].cells[1].background_color == "red"
        assert transposed.rows[0].cells[1].value_format == "no_decimals"
        
        # Original cell (1,1) -> transposed cell (0,2)
        assert transposed.rows[0].cells[2].bottom_border == "double"
        
        # Check that row label cells have left alignment (this is set by transpose)
        assert transposed.rows[0].cells[0].align == "left"

    def test_transpose_empty_table(self):
        """Test transposing an empty table."""
        table = Table(columns=[], rows=[])
        transposed = table.transpose()
        
        assert len(transposed.columns) == 0
        assert len(transposed.rows) == 0

    def test_transpose_single_row(self):
        """Test transposing a table with a single row."""
        columns = [Column(label="A"), Column(label="B"), Column(label="C")]
        rows = [Row(cells=[Cell("Only"), Cell(1), Cell(2)])]
        table = Table(columns=columns, rows=rows)
        
        transposed = table.transpose()
        
        assert len(transposed.columns) == 2  # "A", "Only"
        assert len(transposed.rows) == 2     # B, C
        
        assert transposed.columns[0].label == "A"  # Preserved original first column header
        assert transposed.columns[1].label == "Only"
        assert transposed.rows[0].cells[0].value == "B"
        assert transposed.rows[0].cells[1].value == 1
        assert transposed.rows[1].cells[0].value == "C"
        assert transposed.rows[1].cells[1].value == 2

    def test_transpose_single_column(self):
        """Test transposing a table with a single column."""
        columns = [Column(label="OnlyCol")]
        rows = [
            Row(cells=[Cell("First")]),
            Row(cells=[Cell("Second")]),
            Row(cells=[Cell("Third")]),
        ]
        table = Table(columns=columns, rows=rows)
        
        transposed = table.transpose()
        
        assert len(transposed.columns) == 4  # "OnlyCol", "First", "Second", "Third"  
        assert len(transposed.rows) == 0     # No additional columns to create rows from
        
        assert transposed.columns[0].label == "OnlyCol"  # Preserved original first column header
        assert transposed.columns[1].label == "First"
        assert transposed.columns[2].label == "Second"
        assert transposed.columns[3].label == "Third"

    def test_transpose_does_not_modify_original(self):
        """Test that transpose creates a new table and doesn't modify the original."""
        columns = [Column(label="A"), Column(label="B")]
        rows = [
            Row(cells=[Cell("X"), Cell(1)]),
            Row(cells=[Cell("Y"), Cell(2)]),
        ]
        original_table = Table(columns=columns, rows=rows)
        
        # Store original values for comparison
        orig_col_count = len(original_table.columns)
        orig_row_count = len(original_table.rows)
        orig_first_col_label = original_table.columns[0].label
        orig_first_cell_value = original_table.rows[0].cells[0].value
        
        # Transpose
        transposed = original_table.transpose()
        
        # Verify original is unchanged
        assert len(original_table.columns) == orig_col_count
        assert len(original_table.rows) == orig_row_count
        assert original_table.columns[0].label == orig_first_col_label
        assert original_table.rows[0].cells[0].value == orig_first_cell_value
        
        # Verify they are different objects
        assert original_table is not transposed
        assert original_table.columns is not transposed.columns
        assert original_table.rows is not transposed.rows

    def test_transpose_twice_returns_different_structure(self):
        """Test that transposing twice doesn't return to original structure due to row label handling."""
        columns = [Column(label="A"), Column(label="B")]
        rows = [
            Row(cells=[Cell("X"), Cell(1)]),
            Row(cells=[Cell("Y"), Cell(2)]),
        ]
        table = Table(columns=columns, rows=rows)
        
        # Transpose twice
        transposed_once = table.transpose()
        transposed_twice = transposed_once.transpose()
        
        # The structure should be different from original due to how row labels are handled
        # Original: 2 cols, 2 rows  
        # After 1st transpose: 3 cols, 1 row (preserves "A" as first column header)
        # After 2nd transpose: 2 cols, 2 rows (but different structure)
        assert len(table.columns) == 2
        assert len(table.rows) == 2
        
        assert len(transposed_once.columns) == 3
        assert len(transposed_once.rows) == 1
        
        assert len(transposed_twice.columns) == 2  
        assert len(transposed_twice.rows) == 2

    def test_transpose_with_missing_cells(self):
        """Test transpose when some rows have fewer cells than columns (edge case)."""
        # Note: This should normally raise an error during Table creation,
        # but let's test the transpose logic assuming it could happen
        columns = [Column(label="A"), Column(label="B"), Column(label="C")]
        
        # This would normally fail validation, but let's create manually for testing
        rows = [Row(cells=[Cell("X"), Cell(1)])]  # Missing third cell
        table = Table.__new__(Table)  # Bypass __init__ validation
        table.columns = columns
        table.rows = rows
        
        transposed = table.transpose()
        
        # Should handle missing cells gracefully by adding None values
        assert len(transposed.columns) == 2  # "A", "X"
        assert len(transposed.rows) == 2     # B, C
        
        # All transposed rows should have the same number of cells
        for row in transposed.rows:
            assert len(row.cells) == 2
        
        # Check that missing cells become None
        assert transposed.rows[1].cells[1].value is None  # C row, X column

    def test_transpose_to_dataframe_integration(self):
        """Test that transposed tables work correctly with to_dataframe()."""
        columns = [Column(label="Metric"), Column(label="Value")]
        rows = [
            Row(cells=[Cell("Q1"), Cell(100)]),
            Row(cells=[Cell("Q2"), Cell(200)]),
            Row(cells=[Cell("Q3"), Cell(300)]),
        ]
        table = Table(columns=columns, rows=rows)
        
        transposed = table.transpose()
        df = transposed.to_dataframe()
        
        # Check DataFrame structure  
        expected_columns = ["Metric", "Q1", "Q2", "Q3"]  # First column header preserved
        assert list(df.columns) == expected_columns
        
        # Check DataFrame data
        assert df.iloc[0, 0] == "Value"   # First row (Value row), first column (Metric)
        assert df.iloc[0, 1] == 100       # First row (Value row), Q1 column
        assert df.iloc[0, 2] == 200       # First row (Value row), Q2 column
        assert df.iloc[0, 3] == 300       # First row (Value row), Q3 column
        
        # Verify there's only one row in the transposed table
        assert len(df) == 1

    def test_transpose_with_remove_borders_false(self):
        """Test that borders are preserved when remove_borders=False (default)."""
        columns = [Column(label="A"), Column(label="B")]
        rows = [
            Row(cells=[
                Cell("X", top_border="single"), 
                Cell(1, bottom_border="double")
            ]),
        ]
        table = Table(columns=columns, rows=rows)
        
        transposed = table.transpose(remove_borders=False)
        
        # Check that borders are preserved
        assert transposed.rows[0].cells[1].bottom_border == "double"
        
        # Test default behavior too (should be same as remove_borders=False)
        transposed_default = table.transpose()
        assert transposed_default.rows[0].cells[1].bottom_border == "double"

    def test_transpose_with_remove_borders_true(self):
        """Test that all borders are removed when remove_borders=True."""
        columns = [Column(label="A"), Column(label="B")]
        rows = [
            Row(cells=[
                Cell("X", top_border="single"), 
                Cell(1, bottom_border="double")
            ]),
        ]
        table = Table(columns=columns, rows=rows)
        
        transposed = table.transpose(remove_borders=True)
        
        # Check that all borders are removed from all cells
        for row in transposed.rows:
            for cell in row.cells:
                assert cell.top_border is None
                assert cell.bottom_border is None

    def test_transpose_remove_borders_preserves_other_formatting(self):
        """Test that remove_borders only removes borders, preserving other formatting."""
        columns = [Column(label="Category"), Column(label="Value")]
        rows = [
            Row(cells=[
                Cell("Revenue", bold=True, align="center"), 
                Cell(1000, 
                     bottom_border="single", 
                     top_border="double",
                     background_color="lightblue",
                     font_color="red",
                     value_format="no_decimals")
            ]),
        ]
        table = Table(columns=columns, rows=rows)
        
        transposed = table.transpose(remove_borders=True)
        
        # Check that non-border formatting is preserved
        value_cell = transposed.rows[0].cells[1]  # The "1000" cell
        assert value_cell.value == 1000
        assert value_cell.background_color == "lightblue"
        assert value_cell.font_color == "red"
        assert value_cell.value_format == "no_decimals"
        
        # But borders should be removed
        assert value_cell.top_border is None
        assert value_cell.bottom_border is None
        
        # Check first cell too
        first_cell = transposed.rows[0].cells[0]  # The "Value" cell
        assert first_cell.value == "Value"
        assert first_cell.top_border is None
        assert first_cell.bottom_border is None