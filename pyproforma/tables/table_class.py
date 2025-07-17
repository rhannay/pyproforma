from dataclasses import dataclass
from typing import Optional, Any
import pandas as pd
from pandas.io.formats.style import Styler
from .excel import to_excel
from typing import TYPE_CHECKING
from ..constants import ValueFormat

if TYPE_CHECKING:
    from pyproforma import LineItemSet 


@dataclass
class Cell:
    value: Optional[Any] = None
    bold: bool = False
    align: str = 'right'
    value_format: Optional[ValueFormat] = None
    background_color: Optional[str] = None

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
        return '; '.join(styles) + (';' if styles else '')
    
    @property
    def formatted_value(self) -> Optional[str]:

        return format_value(self.value, self.value_format)

@dataclass
class Row:
    cells: list[Cell]

@dataclass
class Column:
    label: str

@dataclass
class Table:
    columns: list[Column]   
    rows: list[Row]

    # Initialization and validation
    def __post_init__(self):
        self._check_column_and_cell_counts()
    
    # Public API - Conversion and Export methods
    def to_df(self) -> pd.DataFrame:
        data = []
        for row in self.rows:
            row_data = {col.label: cell.value for col, cell in zip(self.columns, row.cells)}
            data.append(row_data)
        return pd.DataFrame(data)
    
    def to_styled_df(self) -> Styler:
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
        """Return HTML representation for Jupyter display."""
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
        return f"{value:.2f}"
    elif value_format == 'percent':
        return f"{int(round(value * 100))}%"  
    elif value_format == 'percent_one_decimal':
        return f"{value * 100:.1f}%"  
    elif value_format == 'percent_two_decimals':
        return f"{value * 100:.2f}%"  
    else:
        raise ValueError(f"Invalid value_format: {value_format}")
