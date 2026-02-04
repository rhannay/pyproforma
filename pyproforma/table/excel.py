from typing import TYPE_CHECKING, Optional, Union

import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

if TYPE_CHECKING:
    from .table_class import Table

from .colors import color_to_rgb
from .format_value import NumberFormatSpec


def value_format_to_excel_format(
    value_format: Optional[Union[NumberFormatSpec, dict]],
) -> str:
    """Convert a cell value_format to an Excel number_format.

    Args:
        value_format: Can be a NumberFormatSpec instance, dict, or None

    Returns:
        Excel number format string
    """
    # Handle None
    if value_format is None:
        return "General"
    
    # Handle dict - convert to NumberFormatSpec
    if isinstance(value_format, dict):
        try:
            value_format = NumberFormatSpec.from_dict(value_format)
        except (KeyError, TypeError, ValueError):
            return "General"
    
    # Handle NumberFormatSpec instances
    if isinstance(value_format, NumberFormatSpec):
        return _spec_to_excel_format(value_format)
    
    # Unknown type
    return "General"


def _spec_to_excel_format(spec: NumberFormatSpec) -> str:
    """Convert a NumberFormatSpec to an Excel number format string.

    Args:
        spec: NumberFormatSpec instance

    Returns:
        Excel number format string

    Note:
        Excel has limited support for custom number formats with scales.
        For formats with scale, we fall back to text format and rely on
        the Python-formatted value being written to the cell.
    """
    # If scale is set, we can't represent this in Excel number format
    # The value will already be formatted by format_value(), so use text format
    if spec.scale:
        return "@"  # Text format

    # Build the Excel format string
    # Start with the number format
    if spec.thousands:
        if spec.decimals == 0:
            number_format = "#,##0"
        else:
            number_format = "#,##0." + "0" * spec.decimals
    else:
        if spec.decimals == 0:
            number_format = "0"
        else:
            number_format = "0." + "0" * spec.decimals

    # Add prefix and suffix
    # Excel format: prefix number_format suffix
    # For simple symbols like $ and %, no quotes needed
    # Excel will format them correctly as part of the format string
    if spec.prefix or spec.suffix:
        number_format = f"{spec.prefix}{number_format}{spec.suffix}"

    return number_format


def to_excel(table: "Table", filename="table.xlsx"):
    """Export a Table to Excel with formatting.

    Args:
        table: The Table instance to export
        filename: The Excel filename to create
    """
    if not table.cells:
        # Create empty workbook if table is empty
        workbook = openpyxl.Workbook()
        workbook.save(filename)
        workbook.close()
        print(f"Empty table exported to {filename}")
        return

    # Create a new workbook and select the active worksheet
    workbook = openpyxl.Workbook()
    worksheet = workbook.active

    # Write all rows (first row is treated as header with special formatting)
    for row_idx, row in enumerate(table.cells, start=1):
        is_header = row_idx == 1
        for col_idx, cell_data in enumerate(row, start=1):
            cell = worksheet.cell(row=row_idx, column=col_idx)

            # Set the value
            cell.value = cell_data.value

            # Apply number formatting based on value_format
            cell.number_format = value_format_to_excel_format(cell_data.value_format)

            # Apply other formatting
            font_kwargs = {}

            # Handle bold (headers are always bold, or if cell specifies it)
            if is_header or cell_data.bold:
                font_kwargs["bold"] = True

            # Handle font color
            if cell_data.font_color is not None:
                r, g, b = color_to_rgb(cell_data.font_color)
                # openpyxl expects RGB hex string (RRGGBB)
                font_kwargs["color"] = f"{r:02X}{g:02X}{b:02X}"

            # Apply font if any font properties are set
            if font_kwargs:
                cell.font = Font(**font_kwargs)

            # Handle background color
            if cell_data.background_color is not None:
                r, g, b = color_to_rgb(cell_data.background_color)
                # openpyxl expects RGB hex string (RRGGBB)
                hex_color = f"{r:02X}{g:02X}{b:02X}"
                cell.fill = PatternFill(
                    start_color=hex_color, end_color=hex_color, fill_type="solid"
                )

            # Handle borders
            border_kwargs = {}
            if cell_data.bottom_border is not None:
                if cell_data.bottom_border == "single":
                    border_kwargs["bottom"] = Side(style="thin")
                elif cell_data.bottom_border == "double":
                    border_kwargs["bottom"] = Side(style="double")

            if cell_data.top_border is not None:
                if cell_data.top_border == "single":
                    border_kwargs["top"] = Side(style="thin")
                elif cell_data.top_border == "double":
                    border_kwargs["top"] = Side(style="double")

            # Apply border if any border properties are set
            if border_kwargs:
                cell.border = Border(**border_kwargs)

            # Set alignment
            if cell_data.align:
                cell.alignment = Alignment(horizontal=cell_data.align)
            elif is_header:
                # Default header alignment to center if not specified
                cell.alignment = Alignment(horizontal="center")

    # Auto-adjust column widths
    for column in worksheet.columns:
        max_length = 0
        column_letter = get_column_letter(column[0].column)

        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except Exception:
                pass

        # Set column width with some padding
        adjusted_width = min(max_length + 2, 50)  # Cap at 50 characters
        worksheet.column_dimensions[column_letter].width = adjusted_width

    # Save the workbook
    workbook.save(filename)
    workbook.close()  # Explicitly close to release file handle on Windows
    print(f"Table exported to {filename}")
