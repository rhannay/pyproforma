from dataclasses import dataclass
from typing import Any, Literal, Optional, Union

import pandas as pd
from pandas.io.formats.style import Styler

from .colors import color_to_hex
from .excel import to_excel
from .format_value import NumberFormatSpec, format_value
from .html_renderer import to_html as _to_html

# Define a type alias for border styles
BorderStyle = Literal["single", "double"]


@dataclass
class Cell:
    """A single cell in a table with value, formatting, and styling properties.

    The Cell class represents an individual cell within a table, containing both
    the data value and its presentation formatting. Cells support various styling
    options including bold text, alignment, background colors, font colors, top borders, bottom borders, and value formatting
    for numbers, percentages, and strings.

    Attributes:
        value (Optional[Any]): The raw data value stored in the cell. Can be any type.
        bold (bool): Whether the cell text should be displayed in bold. Defaults to False.
        align (str): Text alignment for the cell ('left', 'center', 'right'). Defaults to 'right'.
        value_format (Optional[Union[NumberFormatSpec, dict]]): Formatting specification for the value display.
            Can be a NumberFormatSpec instance, dict, or None.
        background_color (Optional[str]): CSS color string for cell background.
        font_color (Optional[str]): CSS color string for font color.
        bottom_border (Optional[str]): Bottom border style. Can be None, 'single', or 'double'.
        top_border (Optional[str]): Top border style. Can be None, 'single', or 'double'.

    Examples:
        >>> cell = Cell(value=1000, bold=True, value_format='no_decimals')
        >>> cell.formatted_value
        '1,000'

        >>> cell = Cell(value=0.25, value_format='percent')
        >>> cell.formatted_value
        '25%'

        >>> cell = Cell(value=1000, font_color='blue', background_color='lightgray')
        >>> 'color: blue' in cell.df_css
        True

        >>> cell = Cell(value="Total", bottom_border='double')
        >>> 'border-bottom: 3px double black' in cell.df_css
        True

        >>> cell = Cell(value="Header", top_border='single')
        >>> 'border-top: 1px solid black' in cell.df_css
        True
    """  # noqa: E501

    value: Optional[Any] = None
    bold: bool = False
    align: str = "right"
    value_format: Optional[Union[NumberFormatSpec, dict]] = None
    background_color: Optional[str] = None
    font_color: Optional[str] = None
    bottom_border: Optional[BorderStyle] = None
    top_border: Optional[BorderStyle] = None

    def __post_init__(self):
        """Validate color values and border styles after initialization."""
        if self.background_color is not None:
            # Validate the color - will raise ValueError if invalid
            color_to_hex(self.background_color)
        if self.font_color is not None:
            # Validate the color - will raise ValueError if invalid
            color_to_hex(self.font_color)

        # Validate border styles
        valid_borders = ("single", "double")
        if self.bottom_border is not None and self.bottom_border not in valid_borders:
            raise ValueError(
                f"Invalid bottom_border value: '{self.bottom_border}'. "
                "Must be None, 'single', or 'double'."
            )
        if self.top_border is not None and self.top_border not in valid_borders:
            raise ValueError(
                f"Invalid top_border value: '{self.top_border}'. "
                "Must be None, 'single', or 'double'."
            )

    @property
    def df_css(self) -> str:
        """Return CSS style for DataFrame display."""
        styles = []
        if self.bold:
            styles.append("font-weight: bold")
        if self.align:
            styles.append(f"text-align: {self.align}")
        if self.background_color:
            hex_color = color_to_hex(self.background_color)
            styles.append(f"background-color: {hex_color}")
        if self.font_color:
            hex_color = color_to_hex(self.font_color)
            styles.append(f"color: {hex_color}")
        if self.bottom_border:
            if self.bottom_border == "single":
                styles.append("border-bottom: 1px solid black")
            elif self.bottom_border == "double":
                styles.append("border-bottom: 3px double black")
            else:
                raise ValueError(
                    (
                        f"Invalid bottom_border value: '{self.bottom_border}'. "
                        "Must be None, 'single', or 'double'."
                    )
                )
        if self.top_border:
            if self.top_border == "single":
                styles.append("border-top: 1px solid black")
            elif self.top_border == "double":
                styles.append("border-top: 3px double black")
            else:
                raise ValueError(
                    (
                        f"Invalid top_border value: '{self.top_border}'. "
                        "Must be None, 'single', or 'double'."
                    )
                )
        return "; ".join(styles) + (";" if styles else "")

    @property
    def formatted_value(self) -> Optional[str]:
        return format_value(self.value, self.value_format)


class Table:
    """A structured table representation as a grid of cells with formatting.

    The Table class provides a flexible way to create, manipulate, and export tabular data
    with support for cell-level formatting including styling, alignment, and value formatting.
    Tables can be converted to pandas DataFrames, styled DataFrames, or exported to Excel
    with preserved formatting.

    Attributes:
        cells (list[list[Cell]]): A 2D grid of Cell objects. Each inner list represents a row.
                                  All rows must have the same length to form a valid grid.

    Examples:
        >>> from pyproforma.table import Table, Cell
        >>> cells = [
        ...     [Cell("Name", bold=True), Cell("Value", bold=True)],  # Header row
        ...     [Cell("Item 1"), Cell(100)],
        ...     [Cell("Item 2"), Cell(200)]
        ... ]
        >>> table = Table(cells=cells)
        >>> df = table.to_dataframe()

        >>> # Access and modify cells using indexing
        >>> value = table[0, 0]  # Get cell at row 0, col 0
        >>> table[1, 1] = Cell(300)  # Set cell at row 1, col 1
        >>> table[0, 0].bold = True  # Modify cell properties

        >>> # Initialize from list of lists of values
        >>> table = Table(cells=[
        ...     ["Name", "Value"],
        ...     ["Item 1", 100],
        ...     ["Item 2", 200]
        ... ])

    Note:
        All rows must have the same number of cells to form a valid rectangular grid.
        This is validated automatically during initialization.
    """  # noqa: E501

    def __init__(self, cells: list[list[Cell] | list[Any]] | None = None):
        """Initialize a Table with cells.

        Args:
            cells: Can be:
                - A list of lists of Cell objects
                - A list of lists of values (will be converted to Cells)
                - None (creates an empty table)
        """
        if cells is None:
            self.cells = []
        else:
            # Convert to list of list of Cell if needed
            self.cells = self._normalize_cells(cells)
        self._check_grid_consistency()

    def _normalize_cells(self, cells: list[list[Any]]) -> list[list[Cell]]:
        """Convert input cells to list of list of Cell objects."""
        normalized = []
        for row in cells:
            normalized_row = []
            for item in row:
                if isinstance(item, Cell):
                    normalized_row.append(item)
                else:
                    # Convert raw value to Cell
                    normalized_row.append(Cell(value=item))
            normalized.append(normalized_row)
        return normalized

    def _check_grid_consistency(self):
        """Ensure all rows have the same number of cells."""
        if not self.cells:
            return  # Empty table is valid

        if not all(isinstance(row, list) for row in self.cells):
            raise ValueError("cells must be a list of lists of Cell objects")

        num_cols = len(self.cells[0]) if self.cells else 0
        for i, row in enumerate(self.cells):
            if len(row) != num_cols:
                raise ValueError(
                    f"Row {i} has {len(row)} cells, expected {num_cols} cells. "
                    "All rows must have the same number of cells."
                )

    # Indexing support
    def __getitem__(self, key: tuple[int, int]) -> Cell:
        """Get a cell using table[row, col] syntax.

        Args:
            key: A tuple of (row_index, col_index) using zero-based indexing.

        Returns:
            The Cell at the specified position.

        Raises:
            IndexError: If the row or column index is out of range.
            TypeError: If key is not a tuple of two integers.

        Examples:
            >>> cell = table[0, 1]  # Get cell at row 0, column 1
            >>> cell.value
        """
        if not isinstance(key, tuple) or len(key) != 2:
            raise TypeError("Table indices must be a tuple of (row, col)")

        row, col = key

        if not isinstance(row, int) or not isinstance(col, int):
            raise TypeError("Row and column indices must be integers")

        # Check bounds
        if not self.cells:
            raise IndexError("Cannot index into an empty table")

        if row < 0 or row >= len(self.cells):
            raise IndexError(
                f"Row index {row} is out of range. Table has {len(self.cells)} rows (0-{len(self.cells) - 1})"
            )

        if col < 0 or col >= len(self.cells[0]):
            raise IndexError(
                f"Column index {col} is out of range. Table has {len(self.cells[0])} columns (0-{len(self.cells[0]) - 1})"
            )

        return self.cells[row][col]

    def __setitem__(self, key: tuple[int, int], value: Cell | Any):
        """Set a cell using table[row, col] = cell syntax.

        Args:
            key: A tuple of (row_index, col_index) using zero-based indexing.
            value: A Cell object or a value to convert to a Cell.

        Raises:
            IndexError: If the row or column index is out of range.
            TypeError: If key is not a tuple of two integers.

        Examples:
            >>> table[0, 1] = Cell(100, bold=True)  # Set with Cell object
            >>> table[1, 0] = "New Value"  # Set with raw value (converts to Cell)
        """
        if not isinstance(key, tuple) or len(key) != 2:
            raise TypeError("Table indices must be a tuple of (row, col)")

        row, col = key

        if not isinstance(row, int) or not isinstance(col, int):
            raise TypeError("Row and column indices must be integers")

        # Check bounds
        if not self.cells:
            raise IndexError("Cannot index into an empty table")

        if row < 0 or row >= len(self.cells):
            raise IndexError(
                f"Row index {row} is out of range. Table has {len(self.cells)} rows (0-{len(self.cells) - 1})"
            )

        if col < 0 or col >= len(self.cells[0]):
            raise IndexError(
                f"Column index {col} is out of range. Table has {len(self.cells[0])} columns (0-{len(self.cells[0]) - 1})"
            )

        # Convert value to Cell if needed
        if isinstance(value, Cell):
            self.cells[row][col] = value
        else:
            self.cells[row][col] = Cell(value=value)

    # Properties for table dimensions
    @property
    def row_count(self) -> int:
        """Return the number of rows in the table.

        Returns:
            The number of rows (0 for empty table).

        Examples:
            >>> table.row_count
            3
        """
        return len(self.cells)

    @property
    def col_count(self) -> int:
        """Return the number of columns in the table.

        Returns:
            The number of columns (0 for empty table).

        Examples:
            >>> table.col_count
            2
        """
        if not self.cells:
            return 0
        return len(self.cells[0])

    # Backward compatibility properties
    @property
    def columns(self):
        """Backward compatibility: Returns header cells as pseudo-columns.

        Note: This is for backward compatibility only. Direct access to cells
        is preferred. Returns an empty list if there are no cells.
        """
        if not self.cells:
            return []

        # Return the first row cells as pseudo-column objects
        class PseudoColumn:
            def __init__(self, cell):
                self.label = cell.value
                self.text_align = cell.align if cell.align else "center"
                self.value_format = cell.value_format

        return [PseudoColumn(cell) for cell in self.cells[0]]

    @property
    def rows(self):
        """Backward compatibility: Returns data rows (excluding header) as pseudo-rows.

        Note: This is for backward compatibility only. Direct access to cells
        is preferred. Returns an empty list if there are no data rows.
        """
        if not self.cells or len(self.cells) < 2:
            return []

        # Return rows starting from index 1 (skip header)
        class PseudoRow:
            def __init__(self, cell_list):
                self.cells = cell_list

            def __getitem__(self, index):
                """Allow subscripting like row[0]."""
                return self.cells[index]

            def __len__(self):
                """Allow len(row)."""
                return len(self.cells)

        return [PseudoRow(row) for row in self.cells[1:]]

    # Helper method for validation
    @staticmethod
    def _validate_border(border_value: Optional[str], border_name: str) -> None:
        """Validate that a border value is valid.

        Args:
            border_value: The border value to validate.
            border_name: Name of the border parameter (for error messages).

        Raises:
            ValueError: If border_value is not None, 'single', or 'double'.
        """
        if border_value is not None and border_value not in ("single", "double"):
            raise ValueError(
                f"Invalid {border_name} value: '{border_value}'. "
                "Must be None, 'single', or 'double'."
            )

    # Public API - Styling methods
    def style_row(
        self,
        row_idx: int,
        bold: Optional[bool] = None,
        bottom_border: Optional[BorderStyle] = None,
        top_border: Optional[BorderStyle] = None,
        background_color: Optional[str] = None,
        font_color: Optional[str] = None,
        align: Optional[str] = None,
        value_format: Optional[Union[NumberFormatSpec, dict]] = None,
    ) -> None:
        """Apply styling to all cells in a row.

        This method modifies the styling properties of all cells in the specified row.
        Only the provided parameters will be applied; omitted parameters leave the
        corresponding cell properties unchanged.

        Args:
            row_idx: Zero-based row index to style.
            bold: If provided, sets bold formatting for all cells in the row.
            bottom_border: If provided, sets bottom border style ('single' or 'double').
            top_border: If provided, sets top border style ('single' or 'double').
            background_color: If provided, sets background color (CSS color string).
            font_color: If provided, sets font color (CSS color string).
            align: If provided, sets text alignment ('left', 'center', or 'right').
            value_format: If provided, sets value format for all cells.

        Raises:
            IndexError: If row_idx is out of range.

        Examples:
            >>> table.style_row(0, bold=True, align='center')  # Style header row
            >>> table.style_row(5, bottom_border='double')     # Add total line
            >>> table.style_row(2, background_color='lightgray', bold=True)
        """
        if row_idx < 0 or row_idx >= len(self.cells):
            raise IndexError(
                f"Row index {row_idx} is out of range. Table has {len(self.cells)} rows (0-{len(self.cells) - 1})"
            )

        # Validate border values before applying
        self._validate_border(bottom_border, "bottom_border")
        self._validate_border(top_border, "top_border")

        for cell in self.cells[row_idx]:
            if bold is not None:
                cell.bold = bold
            if bottom_border is not None:
                cell.bottom_border = bottom_border
            if top_border is not None:
                cell.top_border = top_border
            if background_color is not None:
                cell.background_color = background_color
            if font_color is not None:
                cell.font_color = font_color
            if align is not None:
                cell.align = align
            if value_format is not None:
                cell.value_format = value_format

    def style_col(
        self,
        col_idx: int,
        bold: Optional[bool] = None,
        align: Optional[str] = None,
        background_color: Optional[str] = None,
        font_color: Optional[str] = None,
        value_format: Optional[Union[NumberFormatSpec, dict]] = None,
        bottom_border: Optional[BorderStyle] = None,
        top_border: Optional[BorderStyle] = None,
    ) -> None:
        """Apply styling to all cells in a column.

        This method modifies the styling properties of all cells in the specified column.
        Only the provided parameters will be applied; omitted parameters leave the
        corresponding cell properties unchanged.

        Args:
            col_idx: Zero-based column index to style.
            bold: If provided, sets bold formatting for all cells in the column.
            align: If provided, sets text alignment ('left', 'center', or 'right').
            background_color: If provided, sets background color (CSS color string).
            font_color: If provided, sets font color (CSS color string).
            value_format: If provided, sets value format for all cells.
            bottom_border: If provided, sets bottom border style ('single' or 'double').
            top_border: If provided, sets top border style ('single' or 'double').

        Raises:
            IndexError: If col_idx is out of range or table is empty.

        Examples:
            >>> table.style_col(0, bold=True, align='left')     # Style first column
            >>> table.style_col(1, value_format='two_decimals', align='right')
            >>> table.style_col(2, background_color='lightblue')
        """
        if not self.cells:
            raise IndexError("Cannot style column in empty table")
        if col_idx < 0 or col_idx >= len(self.cells[0]):
            raise IndexError(
                f"Column index {col_idx} is out of range. Table has {len(self.cells[0])} columns (0-{len(self.cells[0]) - 1})"
            )

        # Validate border values before applying
        self._validate_border(bottom_border, "bottom_border")
        self._validate_border(top_border, "top_border")

        for row in self.cells:
            cell = row[col_idx]
            if bold is not None:
                cell.bold = bold
            if align is not None:
                cell.align = align
            if background_color is not None:
                cell.background_color = background_color
            if font_color is not None:
                cell.font_color = font_color
            if value_format is not None:
                cell.value_format = value_format
            if bottom_border is not None:
                cell.bottom_border = bottom_border
            if top_border is not None:
                cell.top_border = top_border

    def set_row_values(
        self,
        row_idx: int,
        values: list[Any],
        start_col: int = 0,
        preserve_formatting: bool = True,
    ) -> None:
        """Set values for cells in a row, optionally starting at a specific column.

        This method allows updating a subset of columns in a row, useful when you want
        to skip label columns or update only certain data columns. The length of values
        must exactly match the number of columns to be updated (from start_col to end).

        Args:
            row_idx: Zero-based row index.
            values: List of values to set. Must exactly match the number of columns
                   from start_col to the end of the row.
            start_col: Column index to start setting values (0-based). Defaults to 0.
                      Use start_col=1 to skip a label column.
            preserve_formatting: If True, only updates cell values while keeping
                               existing formatting. If False, replaces cells entirely
                               with new Cell objects (losing formatting).

        Raises:
            IndexError: If row_idx or start_col is out of range.
            ValueError: If the length of values doesn't exactly match the number of
                       columns to update (table columns - start_col).

        Examples:
            >>> # Table with 4 columns: ["", "Q1", "Q2", "Q3"]
            >>> # Skip first column (label), update 3 data columns
            >>> table.set_row_values(1, [100, 200, 300], start_col=1)

            >>> # Update all 4 columns including label
            >>> table.set_row_values(1, ["New Label", 100, 200, 300])

            >>> # ERROR: Too few values - table has 4 columns, need 3 values from col 1
            >>> table.set_row_values(2, [400, 500], start_col=1)  # Raises ValueError
        """
        if row_idx < 0 or row_idx >= len(self.cells):
            raise IndexError(
                f"Row index {row_idx} is out of range. Table has {len(self.cells)} rows (0-{len(self.cells) - 1})"
            )

        if start_col < 0 or start_col >= len(self.cells[row_idx]):
            raise IndexError(
                f"start_col {start_col} is out of range. Table has {len(self.cells[row_idx])} columns (0-{len(self.cells[row_idx]) - 1})"
            )

        expected_length = len(self.cells[row_idx]) - start_col
        if len(values) != expected_length:
            raise ValueError(
                f"Length of values ({len(values)}) must exactly match number of columns to update. "
                f"start_col={start_col}, table has {len(self.cells[row_idx])} columns, "
                f"expected {expected_length} values but got {len(values)}"
            )

        if preserve_formatting:
            # Update only the value property of existing cells
            for i, new_value in enumerate(values):
                self.cells[row_idx][start_col + i].value = new_value
        else:
            # Replace cells with new Cell objects
            for i, new_value in enumerate(values):
                self.cells[row_idx][start_col + i] = (
                    Cell(value=new_value)
                    if not isinstance(new_value, Cell)
                    else new_value
                )

    def set_col_values(
        self,
        col_idx: int,
        values: list[Any],
        start_row: int = 0,
        preserve_formatting: bool = True,
    ) -> None:
        """Set values for cells in a column, optionally starting at a specific row.

        This method allows updating a subset of rows in a column, useful when you want
        to skip header rows or update only certain data rows. The length of values must
        exactly match the number of rows to be updated (from start_row to end).

        Args:
            col_idx: Zero-based column index.
            values: List of values to set. Must exactly match the number of rows
                   from start_row to the end of the table.
            start_row: Row index to start setting values (0-based). Defaults to 0.
                      Use start_row=1 to skip a header row.
            preserve_formatting: If True, only updates cell values while keeping
                               existing formatting. If False, replaces cells entirely
                               with new Cell objects (losing formatting).

        Raises:
            IndexError: If col_idx or start_row is out of range or table is empty.
            ValueError: If the length of values doesn't exactly match the number of
                       rows to update (table rows - start_row).

        Examples:
            >>> # Table with 4 rows: header + 3 data rows
            >>> # Skip header row, update 3 data rows
            >>> table.set_col_values(1, [100, 200, 300], start_row=1)

            >>> # Update all 4 rows including header
            >>> table.set_col_values(1, ["Total", 100, 200, 300])

            >>> # ERROR: Too few values - table has 4 rows, need 2 values from row 2
            >>> table.set_col_values(2, [400], start_row=2)  # Raises ValueError
        """
        if not self.cells:
            raise IndexError("Cannot set column values in empty table")
        if col_idx < 0 or col_idx >= len(self.cells[0]):
            raise IndexError(
                f"Column index {col_idx} is out of range. Table has {len(self.cells[0])} columns (0-{len(self.cells[0]) - 1})"
            )

        if start_row < 0 or start_row >= len(self.cells):
            raise IndexError(
                f"start_row {start_row} is out of range. Table has {len(self.cells)} rows (0-{len(self.cells) - 1})"
            )

        expected_length = len(self.cells) - start_row
        if len(values) != expected_length:
            raise ValueError(
                f"Length of values ({len(values)}) must exactly match number of rows to update. "
                f"start_row={start_row}, table has {len(self.cells)} rows, "
                f"expected {expected_length} values but got {len(values)}"
            )

        if preserve_formatting:
            # Update only the value property of existing cells
            for i, new_value in enumerate(values):
                self.cells[start_row + i][col_idx].value = new_value
        else:
            # Replace cells with new Cell objects
            for i, new_value in enumerate(values):
                self.cells[start_row + i][col_idx] = (
                    Cell(value=new_value)
                    if not isinstance(new_value, Cell)
                    else new_value
                )

    def _validate_range_coordinates(
        self, start: tuple[int, int], end: tuple[int, int], operation_name: str
    ) -> tuple[int, int, int, int]:
        """Validate range coordinates and return unpacked values.

        Args:
            start: Tuple of (row, col) for the top-left corner of the range.
            end: Tuple of (row, col) for the bottom-right corner of the range.
            operation_name: Name of the operation (for error messages).

        Returns:
            Tuple of (start_row, start_col, end_row, end_col).

        Raises:
            TypeError: If start or end are not tuples of two integers.
            IndexError: If start or end coordinates are out of range or table is empty.
            ValueError: If start is after end.
        """
        # Validate start and end tuples
        if not isinstance(start, tuple) or len(start) != 2:
            raise TypeError("start must be a tuple of (row, col)")
        if not isinstance(end, tuple) or len(end) != 2:
            raise TypeError("end must be a tuple of (row, col)")

        start_row, start_col = start
        end_row, end_col = end

        if not isinstance(start_row, int) or not isinstance(start_col, int):
            raise TypeError("start coordinates must be integers")
        if not isinstance(end_row, int) or not isinstance(end_col, int):
            raise TypeError("end coordinates must be integers")

        # Check bounds
        if not self.cells:
            raise IndexError(f"Cannot {operation_name} in empty table")

        if start_row < 0 or start_row >= len(self.cells):
            raise IndexError(
                f"start row {start_row} is out of range. Table has {len(self.cells)} rows (0-{len(self.cells) - 1})"
            )
        if end_row < 0 or end_row >= len(self.cells):
            raise IndexError(
                f"end row {end_row} is out of range. Table has {len(self.cells)} rows (0-{len(self.cells) - 1})"
            )
        if start_col < 0 or start_col >= len(self.cells[0]):
            raise IndexError(
                f"start col {start_col} is out of range. Table has {len(self.cells[0])} columns (0-{len(self.cells[0]) - 1})"
            )
        if end_col < 0 or end_col >= len(self.cells[0]):
            raise IndexError(
                f"end col {end_col} is out of range. Table has {len(self.cells[0])} columns (0-{len(self.cells[0]) - 1})"
            )

        # Validate that start is before or equal to end
        if start_row > end_row:
            raise ValueError(f"start row ({start_row}) must be <= end row ({end_row})")
        if start_col > end_col:
            raise ValueError(f"start col ({start_col}) must be <= end col ({end_col})")

        return start_row, start_col, end_row, end_col

    def set_range_values(
        self,
        start: tuple[int, int],
        end: tuple[int, int],
        values: list[list[Any]],
        preserve_formatting: bool = True,
    ) -> None:
        """Set values for a rectangular range of cells.

        This method allows updating a 2D range of cells specified by start and end corner
        coordinates. The values are provided as a 2D list matching the range dimensions.

        Args:
            start: Tuple of (row, col) for the top-left corner of the range (0-based).
            end: Tuple of (row, col) for the bottom-right corner of the range (0-based, inclusive).
            values: 2D list of values to set. Must match the dimensions of the range.
                   Outer list represents rows, inner lists represent columns.
            preserve_formatting: If True, only updates cell values while keeping
                               existing formatting. If False, replaces cells entirely
                               with new Cell objects (losing formatting).

        Raises:
            TypeError: If start or end are not tuples of two integers.
            IndexError: If start or end coordinates are out of range.
            ValueError: If start is after end, or if values dimensions don't match range.

        Examples:
            >>> # Set a 2x3 range starting at (1, 1)
            >>> table.set_range_values(
            ...     start=(1, 1),
            ...     end=(2, 3),
            ...     values=[[10, 20, 30], [40, 50, 60]]
            ... )

            >>> # Set a single cell using range notation
            >>> table.set_range_values(
            ...     start=(0, 0),
            ...     end=(0, 0),
            ...     values=[[100]]
            ... )
        """
        # Validate coordinates using helper method
        start_row, start_col, end_row, end_col = self._validate_range_coordinates(
            start, end, "set range"
        )

        # Calculate expected dimensions
        expected_rows = end_row - start_row + 1
        expected_cols = end_col - start_col + 1

        # Validate values dimensions
        if len(values) != expected_rows:
            raise ValueError(
                f"values has {len(values)} rows but range requires {expected_rows} rows"
            )
        for i, row in enumerate(values):
            if len(row) != expected_cols:
                raise ValueError(
                    f"values row {i} has {len(row)} columns but range requires {expected_cols} columns"
                )

        # Set values
        if preserve_formatting:
            # Update only the value property of existing cells
            for i, row_values in enumerate(values):
                for j, new_value in enumerate(row_values):
                    self.cells[start_row + i][start_col + j].value = new_value
        else:
            # Replace cells with new Cell objects
            for i, row_values in enumerate(values):
                for j, new_value in enumerate(row_values):
                    self.cells[start_row + i][start_col + j] = (
                        Cell(value=new_value)
                        if not isinstance(new_value, Cell)
                        else new_value
                    )

    def style_range(
        self,
        start: tuple[int, int],
        end: tuple[int, int],
        bold: Optional[bool] = None,
        bottom_border: Optional[BorderStyle] = None,
        top_border: Optional[BorderStyle] = None,
        background_color: Optional[str] = None,
        font_color: Optional[str] = None,
        align: Optional[str] = None,
        value_format: Optional[Union[NumberFormatSpec, dict]] = None,
    ) -> None:
        """Apply styling to a rectangular range of cells.

        This method modifies the styling properties of all cells in the specified range.
        Only the provided parameters will be applied; omitted parameters leave the
        corresponding cell properties unchanged.

        Args:
            start: Tuple of (row, col) for the top-left corner of the range (0-based).
            end: Tuple of (row, col) for the bottom-right corner of the range (0-based, inclusive).
            bold: If provided, sets bold formatting for all cells in the range.
            bottom_border: If provided, sets bottom border style ('single' or 'double').
            top_border: If provided, sets top border style ('single' or 'double').
            background_color: If provided, sets background color (CSS color string).
            font_color: If provided, sets font color (CSS color string).
            align: If provided, sets text alignment ('left', 'center', or 'right').
            value_format: If provided, sets value format for all cells.

        Raises:
            TypeError: If start or end are not tuples of two integers.
            IndexError: If start or end coordinates are out of range.
            ValueError: If start is after end.

        Examples:
            >>> # Style a range as a header
            >>> table.style_range(
            ...     start=(0, 0),
            ...     end=(0, 3),
            ...     bold=True,
            ...     background_color='lightgray',
            ...     align='center'
            ... )

            >>> # Style a data range with formatting
            >>> table.style_range(
            ...     start=(1, 1),
            ...     end=(5, 3),
            ...     value_format='two_decimals',
            ...     align='right'
            ... )

            >>> # Add a total line border
            >>> table.style_range(
            ...     start=(6, 0),
            ...     end=(6, 3),
            ...     bold=True,
            ...     top_border='single',
            ...     bottom_border='double'
            ... )
        """
        # Validate coordinates using helper method
        start_row, start_col, end_row, end_col = self._validate_range_coordinates(
            start, end, "style range"
        )

        # Validate border values before applying
        self._validate_border(bottom_border, "bottom_border")
        self._validate_border(top_border, "top_border")

        # Apply styling to all cells in the range
        for row_idx in range(start_row, end_row + 1):
            for col_idx in range(start_col, end_col + 1):
                cell = self.cells[row_idx][col_idx]
                if bold is not None:
                    cell.bold = bold
                if bottom_border is not None:
                    cell.bottom_border = bottom_border
                if top_border is not None:
                    cell.top_border = top_border
                if background_color is not None:
                    cell.background_color = background_color
                if font_color is not None:
                    cell.font_color = font_color
                if align is not None:
                    cell.align = align
                if value_format is not None:
                    cell.value_format = value_format

    # Public API - Conversion and Export methods
    def to_dataframe(self) -> pd.DataFrame:
        """Convert the Table to a pandas DataFrame with raw cell values.

        Creates a standard pandas DataFrame using the raw (unformatted) cell values.
        The first row of the table is used as column headers, and subsequent rows
        become DataFrame rows. Cell formatting and styling are not preserved.

        Returns:
            pd.DataFrame: A DataFrame containing the table data with first row
                         as column names and raw cell values as the data.

        Note:
            This method extracts only the raw values from cells. For formatted values
            or styling preservation, use to_styled_df() instead.
            If the table is empty or has only one row, returns an empty DataFrame.
        """
        if not self.cells or len(self.cells) < 2:
            return pd.DataFrame()

        # First row becomes column headers
        headers = [cell.value for cell in self.cells[0]]

        # Remaining rows become data
        data = []
        for row in self.cells[1:]:
            row_data = {header: cell.value for header, cell in zip(headers, row)}
            data.append(row_data)

        return pd.DataFrame(data)

    def to_styled_df(self) -> Styler:
        """Convert the Table to a styled pandas DataFrame with formatting preserved.

        Creates a pandas Styler object that includes all cell-level formatting from the Table,
        including bold text, text alignment, background colors, and value formatting.
        This is useful for rich display in Jupyter notebooks or HTML output.

        Returns:
            pd.io.formats.style.Styler: A styled DataFrame object with CSS formatting
                                       applied based on the cell properties (bold, align,
                                       background_color) and formatted values.

        Note:
            The returned Styler preserves all visual formatting from the original Table cells,
            making it ideal for presentation purposes where formatting matters.
            The first row is used as column headers.
        """  # noqa: E501
        # get a dataframe with formatted values
        df = self._to_value_formatted_df()
        style_map = self._get_style_map()

        def apply_styles(df):
            styled = pd.DataFrame("", index=df.index, columns=df.columns)
            for row_idx in df.index:
                for col_name in df.columns:
                    styled.at[row_idx, col_name] = style_map.get(
                        (row_idx, col_name), ""
                    )
            return styled

        styled_df = df.style.apply(apply_styles, axis=None)

        # Apply column header styles
        styled_df = styled_df.set_table_styles(self._get_header_styles())
        return styled_df

    def to_excel(self, filename="table.xlsx"):
        """Export the Table to an Excel file with formatting."""
        to_excel(self, filename)

    def to_html(self) -> str:
        """Generate custom HTML representation with Excel-like grid styling.

        This method creates an HTML table with Excel-like grid appearance without
        relying on pandas DataFrame styling. The output includes:
        - Excel-like grid borders around all cells
        - Support for bold text, alignment, and colors
        - Top and bottom borders (single and double)
        - Value formatting (numbers, percentages, etc.)

        Returns:
            str: HTML string representation of the table with embedded CSS styling.

        Examples:
            >>> table.to_html()  # Returns HTML string
            >>> from IPython.display import HTML, display
            >>> display(HTML(table.to_html()))  # Display in Jupyter notebook

        Note:
            This is an alternative to the default _repr_html_() which uses
            pandas styled DataFrames. Use this when you want more control over
            the HTML output or prefer not to depend on pandas styling.
        """
        return _to_html(self)

    def show(self) -> None:
        """Display the table in HTML format within a notebook environment.

        This method automatically displays the table in Jupyter notebooks or other
        IPython-based environments by rendering the HTML representation. It provides
        a convenient way to visualize tables without explicitly using IPython.display.

        The method will:
        - Automatically detect if running in a notebook environment
        - Use IPython.display.HTML to render the table
        - Provide a helpful error message if IPython is not available

        Returns:
            None

        Raises:
            ImportError: If IPython is not installed. Install it with:
                        pip install ipython
                        (or include it in your notebook environment)

        Examples:
            >>> from pyproforma.table import Table, Cell
            >>> table = Table(cells=[
            ...     [Cell("Name", bold=True), Cell("Value", bold=True)],
            ...     [Cell("Item 1"), Cell(100)],
            ...     [Cell("Item 2"), Cell(200)]
            ... ])
            >>> table.show()  # Displays the table in a notebook

        Note:
            This method is primarily intended for interactive notebook use.
            For programmatic HTML generation, use to_html() instead.
            Similar to plotly's Figure.show() method for displaying visualizations.
        """
        try:
            from IPython.display import HTML, display
        except ImportError as e:
            raise ImportError(
                "IPython is required to use the show() method. "
                "Install it with: pip install ipython\n"
                "Alternatively, use table.to_html() to get the HTML string "
                "and display it manually."
            ) from e

        # Get the HTML representation and display it
        html_content = self.to_html()
        display(HTML(html_content))

    def transpose(self, remove_borders: bool = False) -> "Table":
        """Return a new Table with rows and columns transposed.

        Creates a new Table where rows become columns and columns become rows.
        All cell properties are preserved during transposition.

        Args:
            remove_borders (bool): If True, removes all borders from cells in the
                                 transposed table. Defaults to False.

        Returns:
            Table: A new Table instance with transposed data. The original table
                   is not modified.

        Examples:
            >>> cells = [
            ...     [Cell("Metric"), Cell("Q1"), Cell("Q2")],
            ...     [Cell("Revenue"), Cell(1000), Cell(1200)],
            ...     [Cell("Expenses"), Cell(800), Cell(900)]
            ... ]
            >>> table = Table(cells=cells)
            >>> transposed = table.transpose()
            # Original:          Transposed:
            #  Metric  Q1  Q2      Metric Revenue Expenses
            # Revenue 1000 1200      Q1    1000     800
            # Expenses 800  900      Q2    1200     900

            >>> # Remove borders from transposed table
            >>> transposed_no_borders = table.transpose(remove_borders=True)

        Note:
            - Empty tables return empty tables
            - Cell formatting and properties are preserved where possible
            - When remove_borders=True, all top_border and bottom_border properties are set to None
        """  # noqa: E501
        # Handle empty table case
        if not self.cells:
            return Table(cells=[])

        num_rows = len(self.cells)
        num_cols = len(self.cells[0]) if self.cells else 0

        # Create transposed cells
        transposed_cells = []
        for col_idx in range(num_cols):
            new_row = []
            for row_idx in range(num_rows):
                original_cell = self.cells[row_idx][col_idx]
                # Copy the cell, preserving all its properties
                new_cell = Cell(
                    value=original_cell.value,
                    bold=original_cell.bold,
                    align=original_cell.align,
                    value_format=original_cell.value_format,
                    background_color=original_cell.background_color,
                    font_color=original_cell.font_color,
                    bottom_border=(
                        None if remove_borders else original_cell.bottom_border
                    ),
                    top_border=(None if remove_borders else original_cell.top_border),
                )
                new_row.append(new_cell)
            transposed_cells.append(new_row)

        return Table(cells=transposed_cells)

    # Display methods
    def _repr_html_(self) -> str:
        """Return HTML representation for rich display in Jupyter notebooks.

        This special method is automatically called by Jupyter notebooks and other
        IPython-compatible environments to provide a rich HTML representation of
        the Table object. The method uses custom HTML rendering with Excel-like
        grid styling.

        Returns:
            str: HTML string representation of the table with all formatting preserved.
                 Generated from the to_html() method.

        Note:
            This is a magic method that enables automatic rich display when a Table
            object is the last expression in a Jupyter cell or when explicitly displayed.
        """  # noqa: E501
        return _to_html(self)

    # Private helper methods
    def _to_value_formatted_df(self) -> pd.DataFrame:
        """Create DataFrame with formatted values."""
        if not self.cells or len(self.cells) < 2:
            return pd.DataFrame()

        # First row becomes column headers
        headers = [cell.value for cell in self.cells[0]]

        # Remaining rows become data with formatted values
        data = []
        for row in self.cells[1:]:
            row_data = {
                header: cell.formatted_value for header, cell in zip(headers, row)
            }
            data.append(row_data)

        return pd.DataFrame(data)

    def _get_style_map(self) -> dict:
        """Create a mapping of (row_idx, col_name) -> CSS style string."""
        if not self.cells or len(self.cells) < 2:
            return {}

        # First row becomes column headers
        headers = [cell.value for cell in self.cells[0]]

        style_map = {}
        # Start from row 1 (skip header row which is cells[0])
        for i, row in enumerate(self.cells[1:]):
            for j, cell in enumerate(row):
                col_name = headers[j]
                style_map[(i, col_name)] = cell.df_css
        return style_map

    def _get_header_styles(self) -> list[dict]:
        """Generate header styles based on first row cells."""
        if not self.cells:
            return []

        styles = []
        for i, cell in enumerate(self.cells[0]):
            # Use the cell's alignment if set, otherwise default to center
            align = cell.align if cell.align else "center"
            styles.append(
                {
                    "selector": f"th.col_heading.level0.col{i}",
                    "props": [("text-align", align)],
                }
            )
        return styles
