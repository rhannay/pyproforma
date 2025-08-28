from dataclasses import dataclass
from typing import Any, Optional

import pandas as pd
from pandas.io.formats.style import Styler

from ..constants import ValueFormat
from .excel import to_excel


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
class Row:
    """A horizontal row in a table containing a list of cells.

    The Row class represents a single row within a table, containing an ordered
    list of Cell objects. Each row must have the same number of cells as there
    are columns in the parent Table.

    Attributes:
        cells (list[Cell]): Ordered list of Cell objects that make up this row.

    Examples:
        >>> cell1 = Cell(value="Product A", align='left')
        >>> cell2 = Cell(value=150.00, value_format='two_decimals')
        >>> row = Row(cells=[cell1, cell2])
    """

    cells: list[Cell]


@dataclass
class Column:
    """A column definition for a table with a descriptive label.

    The Column class defines the structure and labeling for a table column.
    Column labels are used as headers in DataFrame conversions and Excel exports.

    Attributes:
        label (Any): The display name/header for this column.
        text_align (str): Text alignment for the column header
            ('left', 'center', 'right'). Defaults to 'center'.
        value_format (Optional[ValueFormat]): Formatting type for the column
            header display. Defaults to 'str'.

    Examples:
        >>> column = Column(label="Revenue")
        >>> column = Column(label="Product", text_align="left")
        >>> column = Column(label=2024, value_format="year")
        >>> columns = [Column("Product"), Column("Price"), Column("Quantity")]
    """

    label: Any
    text_align: str = "center"
    value_format: Optional[ValueFormat] = "str"

    @property
    def formatted_label(self) -> Optional[str]:
        return format_value(self.label, self.value_format)


@dataclass
class Table:
    """A structured table representation with rows, columns, and cell formatting.

    The Table class provides a flexible way to create, manipulate, and export tabular data
    with support for cell-level formatting including styling, alignment, and value formatting.
    Tables can be converted to pandas DataFrames, styled DataFrames, or exported to Excel
    with preserved formatting.

    Attributes:
        columns (list[Column]): List of Column objects defining the table structure.
        rows (list[Row]): List of Row objects containing the table data.

    Examples:
        >>> from pyproforma.tables import Table, Column, Row, Cell
        >>> columns = [Column("Name"), Column("Value")]
        >>> rows = [Row([Cell("Item 1"), Cell(100)])]
        >>> table = Table(columns=columns, rows=rows)
        >>> df = table.to_dataframe()

    Note:
        The number of cells in each row must match the number of columns.
        This is validated automatically during initialization.
    """  # noqa: E501

    columns: list[Column]
    rows: list[Row]

    # Initialization and validation
    def __post_init__(self):
        self._check_column_and_cell_counts()

    def _check_column_and_cell_counts(self):
        # Check each number of cells in each row matches the number of columns
        num_columns = len(self.columns)
        for i, row in enumerate(self.rows):
            if len(row.cells) != num_columns:
                raise ValueError(
                    (
                        f"Row {i} has {len(row.cells)} cells, expected {num_columns} "
                        "based on the number of columns."
                    )
                )

    # Public API - Conversion and Export methods
    def to_dataframe(self) -> pd.DataFrame:
        """Convert the Table to a pandas DataFrame with raw cell values.

        Creates a standard pandas DataFrame using the raw (unformatted) cell values.
        Column labels from the Table become DataFrame column names, and each row
        becomes a DataFrame row. Cell formatting and styling are not preserved.

        Returns:
            pd.DataFrame: A DataFrame containing the table data with column labels
                         as column names and raw cell values as the data.

        Note:
            This method extracts only the raw values from cells. For formatted values
            or styling preservation, use to_styled_df() instead.
        """
        data = []
        for row in self.rows:
            row_data = {
                col.label: cell.value for col, cell in zip(self.columns, row.cells)
            }
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

    def transpose(self, remove_borders: bool = False) -> "Table":
        """Return a new Table with rows and columns transposed.
        
        Creates a new Table where:
        - Column labels become the first cell in each new row
        - The first cell from each original row becomes new column labels
        - All other cells are repositioned accordingly
        
        Args:
            remove_borders (bool): If True, removes all borders from cells in the 
                                 transposed table. Defaults to False.
        
        Returns:
            Table: A new Table instance with transposed data. The original table
                   is not modified.
        
        Examples:
            >>> columns = [Column("Metric"), Column("Q1")]
            >>> rows = [Row([Cell("Revenue"), Cell(1000), Cell(1200)]), 
            ...         Row([Cell("Expenses"), Cell(800), Cell(900)])]
            >>> table = Table(columns=columns, rows=rows)
            >>> transposed = table.transpose()
            # Original:     Transposed:
            #  Metric  Q1      Metric Revenue Expenses
            # Revenue 1000      Q1    1000     800  
            # Expenses 800
            
            >>> # Remove borders from transposed table
            >>> transposed_no_borders = table.transpose(remove_borders=True)
        
        Note:
            - Empty tables return empty tables
            - Cell formatting and properties are preserved where possible
            - The first column of the transposed table preserves the original first column label
            - When remove_borders=True, all top_border and bottom_border properties are set to None
        """
        # Handle empty table case
        if not self.columns or not self.rows:
            return Table(columns=[], rows=[])
        
        # Create new column labels: preserve first column label + first cell value from each original row
        new_column_labels = [self.columns[0].label]  # Preserve the original first column label
        for row in self.rows:
            if row.cells:
                # Use the value from the first cell as the new column label
                new_column_labels.append(row.cells[0].value)
            else:
                new_column_labels.append("")
        
        # Create new columns
        new_columns = [Column(label=label) for label in new_column_labels]
        
        # Create new rows: one row for each original column (excluding the first column since its label is preserved as column header)
        new_rows = []
        for col_idx, original_column in enumerate(self.columns[1:], 1):  # Skip first column, start index at 1
            # First cell in the new row is the original column label  
            first_cell = Cell(value=original_column.label, align="left")
            new_row_cells = [first_cell]
            
            # Add cells from each original row at the corresponding column position
            # Note: col_idx because we're now using the actual column index
            for row in self.rows:
                if col_idx < len(row.cells):
                    # Copy the cell, preserving all its properties
                    original_cell = row.cells[col_idx]
                    new_cell = Cell(
                        value=original_cell.value,
                        bold=original_cell.bold,
                        align=original_cell.align,
                        value_format=original_cell.value_format,
                        background_color=original_cell.background_color,
                        font_color=original_cell.font_color,
                        bottom_border=None if remove_borders else original_cell.bottom_border,
                        top_border=None if remove_borders else original_cell.top_border
                    )
                    new_row_cells.append(new_cell)
                else:
                    # If original row doesn't have enough cells, add empty cell
                    new_row_cells.append(Cell(value=None))
            
            new_rows.append(Row(cells=new_row_cells))
        
        return Table(columns=new_columns, rows=new_rows)

    # Display methods
    def _repr_html_(self) -> str:
        """Return HTML representation for rich display in Jupyter notebooks.

        This special method is automatically called by Jupyter notebooks and other
        IPython-compatible environments to provide a rich HTML representation of
        the Table object. The method leverages the styled DataFrame to preserve
        all cell formatting including bold text, alignment, and background colors.

        Returns:
            str: HTML string representation of the table with all formatting preserved.
                 Generated from the styled DataFrame's HTML output.

        Note:
            This is a magic method that enables automatic rich display when a Table
            object is the last expression in a Jupyter cell or when explicitly displayed.
        """  # noqa: E501
        styled_df = self.to_styled_df()
        return styled_df.to_html()

    # Private helper methods
    def _to_value_formatted_df(self) -> pd.DataFrame:
        data = []
        for row in self.rows:
            row_data = {
                col.label: cell.formatted_value
                for col, cell in zip(self.columns, row.cells)
            }
            data.append(row_data)
        return pd.DataFrame(data)

    def _get_style_map(self) -> dict:
        style_map = {}
        for i, row in enumerate(self.rows):
            for j, cell in enumerate(row.cells):
                col_name = self.columns[j].label
                style_map[(i, col_name)] = cell.df_css
        return style_map

    def _get_header_styles(self) -> list[dict]:
        """Generate header styles based on column text_align property."""
        styles = []
        for i, column in enumerate(self.columns):
            styles.append(
                {
                    "selector": f"th.col_heading.level0.col{i}",
                    "props": [("text-align", column.text_align)],
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
