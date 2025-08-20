from dataclasses import dataclass
from typing import Optional, Any
import pandas as pd
from pandas.io.formats.style import Styler
from .excel import to_excel
from typing import TYPE_CHECKING
from ..constants import ValueFormat


@dataclass
class Cell:
    """A single cell in a table with value, formatting, and styling properties.
    
    The Cell class represents an individual cell within a table, containing both
    the data value and its presentation formatting. Cells support various styling
    options including bold text, alignment, background colors, font colors, bottom borders, and value formatting
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
    """
    value: Optional[Any] = None
    bold: bool = False
    align: str = 'right'
    value_format: Optional[ValueFormat] = None
    background_color: Optional[str] = None
    font_color: Optional[str] = None
    bottom_border: Optional[str] = None

    @property
    def df_css(self) -> str:
        """Return CSS style for DataFrame display."""
        styles = []
        if self.bold:
            styles.append('font-weight: bold')
        if self.align:
            styles.append(f'text-align: {self.align}')
        if self.background_color:
            styles.append(f'background-color: {self.background_color}')
        if self.font_color:
            styles.append(f'color: {self.font_color}')
        if self.bottom_border:
            if self.bottom_border == 'single':
                styles.append('border-bottom: 1px solid black')
            elif self.bottom_border == 'double':
                styles.append('border-bottom: 3px double black')
            else:
                raise ValueError(f"Invalid bottom_border value: '{self.bottom_border}'. Must be None, 'single', or 'double'.")
        return '; '.join(styles) + (';' if styles else '')
    
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
        label (str): The display name/header for this column.
    
    Examples:
        >>> column = Column(label="Revenue")
        >>> columns = [Column("Product"), Column("Price"), Column("Quantity")]
    """
    label: str

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
    """
    columns: list[Column]   
    rows: list[Row]

    # Initialization and validation
    def __post_init__(self):
        self._check_column_and_cell_counts()
    
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
            row_data = {col.label: cell.value for col, cell in zip(self.columns, row.cells)}
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
        """
        # get a dataframe with formatted values
        df = self._to_value_formatted_df()
        style_map = self._get_style_map()

        def apply_styles(df):
            styled = pd.DataFrame('', index=df.index, columns=df.columns)
            for row_idx in df.index:
                for col_name in df.columns:
                    styled.at[row_idx, col_name] = style_map.get((row_idx, col_name), '')
            return styled

        styled_df = df.style.apply(apply_styles, axis=None)
        return styled_df
    
    def to_excel(self, filename="table.xlsx"):
        """Export the Table to an Excel file with formatting."""
        to_excel(self, filename)
    
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
        """
        styled_df = self.to_styled_df()
        return styled_df.to_html()
    
    # Private helper methods
    def _check_column_and_cell_counts(self):
        # Check each number of cells in each row matches the number of columns
        num_columns = len(self.columns)
        for i, row in enumerate(self.rows):
            if len(row.cells) != num_columns:
                raise ValueError(
                    f"Row {i} has {len(row.cells)} cells, expected {num_columns} based on the number of columns."
                )            
    
    def _to_value_formatted_df(self) -> pd.DataFrame:
        data = []
        for row in self.rows:
            row_data = {col.label: cell.formatted_value for col, cell in zip(self.columns, row.cells)}
            data.append(row_data)
        return pd.DataFrame(data)
    
    def _get_style_map(self) -> dict:
        style_map = {}
        for i, row in enumerate(self.rows):
            for j, cell in enumerate(row.cells):
                col_name = self.columns[j].label
                style_map[(i, col_name)] = cell.df_css
        return style_map
    

def format_value(value: Any, value_format: Optional[ValueFormat], none_returns='') -> Any:
    if value is None:
        return none_returns
    if value_format is None:
        return value
    if value_format == 'str':
        return str(value)
    elif value_format == 'no_decimals':
        return f"{int(round(value)):,}"  # Format as rounded number with commas, no decimals
    elif value_format == 'two_decimals':
        return f"{value:,.2f}"
    elif value_format == 'percent':
        return f"{int(round(value * 100))}%"  
    elif value_format == 'percent_one_decimal':
        return f"{value * 100:.1f}%"  
    elif value_format == 'percent_two_decimals':
        return f"{value * 100:.2f}%"  
    else:
        raise ValueError(f"Invalid value_format: {value_format}")
