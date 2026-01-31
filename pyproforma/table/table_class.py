from dataclasses import dataclass
from typing import Any, Optional

import pandas as pd
from pandas.io.formats.style import Styler

from ..constants import ValueFormat
from .excel import to_excel
from .html_renderer import to_html as _to_html


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
        value_format (Optional[ValueFormat]): Formatting type for the value display.
            Options: 'str', 'no_decimals', 'two_decimals', 'percent', 'percent_one_decimal', 'percent_two_decimals'.
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
    value_format: Optional[ValueFormat] = None
    background_color: Optional[str] = None
    font_color: Optional[str] = None
    bottom_border: Optional[str] = None
    top_border: Optional[str] = None

    @property
    def df_css(self) -> str:
        """Return CSS style for DataFrame display."""
        styles = []
        if self.bold:
            styles.append("font-weight: bold")
        if self.align:
            styles.append(f"text-align: {self.align}")
        if self.background_color:
            styles.append(f"background-color: {self.background_color}")
        if self.font_color:
            styles.append(f"color: {self.font_color}")
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





@dataclass
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

    Note:
        All rows must have the same number of cells to form a valid rectangular grid.
        This is validated automatically during initialization.
    """  # noqa: E501

    cells: list[list[Cell]]

    # Initialization and validation
    def __post_init__(self):
        self._check_grid_consistency()

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
                    top_border=(
                        None if remove_borders else original_cell.top_border
                    ),
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
            row_data = {header: cell.formatted_value for header, cell in zip(headers, row)}
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


def format_value(
    value: Any, value_format: Optional[ValueFormat], none_returns=""
) -> Any:
    if value is None:
        return none_returns
    if value_format is None:
        return value
    if value_format == "str":
        return str(value)
    elif value_format == "no_decimals":
        return f"{int(round(value)):,}"
    elif value_format == "two_decimals":
        return f"{value:,.2f}"
    elif value_format == "percent":
        return f"{int(round(value * 100))}%"
    elif value_format == "percent_one_decimal":
        return f"{value * 100:.1f}%"
    elif value_format == "percent_two_decimals":
        return f"{value * 100:.2f}%"
    elif value_format == "year":
        return str(int(round(value)))
    else:
        raise ValueError(f"Invalid value_format: {value_format}")
