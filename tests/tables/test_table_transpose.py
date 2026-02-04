import pandas as pd
import pytest

from pyproforma.table import Cell, Table, Format


class TestTableTranspose:
    """Test cases for the Table.transpose() method."""

    def test_transpose_simple_2x2(self):
        """Test transposing a simple 2x2 table."""
        cells = [
            [Cell("A"), Cell("B")],
            [Cell("X"), Cell(1)],
            [Cell("Y"), Cell(2)],
        ]
        table = Table(cells=cells)
        
        transposed = table.transpose()
        
        # Check structure - original is 3 rows x 2 cols, transposed is 2 rows x 3 cols
        assert len(transposed.cells) == 2
        assert len(transposed.cells[0]) == 3
        
        # Check transposed values
        assert transposed.cells[0][0].value == "A"
        assert transposed.cells[0][1].value == "X"
        assert transposed.cells[0][2].value == "Y"
        assert transposed.cells[1][0].value == "B"
        assert transposed.cells[1][1].value == 1
        assert transposed.cells[1][2].value == 2

    def test_transpose_rectangular_3x2(self):
        """Test transposing a rectangular table."""
        cells = [
            [Cell("Col1"), Cell("Col2"), Cell("Col3")],
            [Cell("Row1"), Cell(1), Cell(2)],
            [Cell("Row2"), Cell(3), Cell(4)],
        ]
        table = Table(cells=cells)
        
        transposed = table.transpose()
        
        # Original: 3 rows x 3 cols, transposed: 3 rows x 3 cols
        assert len(transposed.cells) == 3
        assert len(transposed.cells[0]) == 3
        
        # Check transposed values
        assert transposed.cells[0][0].value == "Col1"
        assert transposed.cells[0][1].value == "Row1"
        assert transposed.cells[0][2].value == "Row2"
        assert transposed.cells[1][0].value == "Col2"
        assert transposed.cells[1][1].value == 1
        assert transposed.cells[1][2].value == 3
        assert transposed.cells[2][0].value == "Col3"
        assert transposed.cells[2][1].value == 2
        assert transposed.cells[2][2].value == 4

    def test_transpose_preserves_cell_formatting(self):
        """Test that cell formatting is preserved during transpose."""
        cells = [
            [Cell("A"), Cell("B")],
            [
                Cell("X", bold=True, align="center"), 
                Cell(1, bold=True, background_color="red", value_format=Format.NO_DECIMALS)
            ],
            [
                Cell("Y", font_color="blue"), 
                Cell(2, bottom_border="double")
            ],
        ]
        table = Table(cells=cells)
        
        transposed = table.transpose()
        
        # Check that formatting is preserved
        assert transposed.cells[0][1].bold is True
        assert transposed.cells[0][1].align == "center"
        assert transposed.cells[1][1].bold is True
        assert transposed.cells[1][1].background_color == "red"
        assert transposed.cells[1][2].bottom_border == "double"

    def test_transpose_empty_table(self):
        """Test transposing an empty table."""
        table = Table(cells=[])
        transposed = table.transpose()
        
        assert len(transposed.cells) == 0

    def test_transpose_with_remove_borders_true(self):
        """Test that all borders are removed when remove_borders=True."""
        cells = [
            [Cell("A"), Cell("B")],
            [
                Cell("X", top_border="single"), 
                Cell(1, bottom_border="double")
            ],
        ]
        table = Table(cells=cells)
        
        transposed = table.transpose(remove_borders=True)
        
        # Check that all borders are removed from all cells
        for row in transposed.cells:
            for cell in row:
                assert cell.top_border is None
                assert cell.bottom_border is None
