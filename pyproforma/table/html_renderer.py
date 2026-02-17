"""HTML renderer for Table class with Excel-like grid styling.

This module provides an alternative HTML rendering method for the Table class
that generates custom HTML output without relying on pandas DataFrame styling.
The output is designed to look like an Excel grid with support for cell formatting,
borders, colors, and other styling options.
"""

from typing import TYPE_CHECKING

from .colors import color_to_hex

if TYPE_CHECKING:
    from .table_class import Table


def to_html(table: "Table") -> str:
    """Generate custom HTML representation of a Table with Excel-like styling.

    This function creates an HTML table with Excel-like grid appearance, including:
    - Grid borders around all cells
    - Support for bold text
    - Text alignment (left, center, right)
    - Background and font colors
    - Top and bottom borders (single and double)
    - Value formatting (numbers, percentages, etc.)

    Args:
        table: The Table instance to render as HTML

    Returns:
        str: HTML string representation of the table with embedded CSS styling

    Examples:
        >>> from pyproforma.table import Table, Cell
        >>> cells = [
        ...     [Cell("Name", bold=True), Cell("Value", bold=True)],
        ...     [Cell("Item 1"), Cell(100)]
        ... ]
        >>> table = Table(cells=cells)
        >>> html = to_html(table)
    """
    # Build CSS styles
    css = _generate_css()

    # Build HTML table
    html_parts = ['<div class="pyproforma-table-container">']
    html_parts.append('<table class="pyproforma-table">')

    # Generate all rows (treat all rows equally, no special header row)
    if table.cells:
        html_parts.append("<tbody>")
        for row in table.cells:
            row_cells = []
            for cell in row:
                cell_html = _generate_cell_html(cell)
                row_cells.append(cell_html)
            html_parts.append(f"<tr>{''.join(row_cells)}</tr>")
        html_parts.append("</tbody>")

    html_parts.append("</table>")
    html_parts.append("</div>")

    # Combine CSS and HTML
    full_html = f"<style>{css}</style>\n{''.join(html_parts)}"

    return full_html


def _generate_css() -> str:
    """Generate CSS styles for the Excel-like table."""
    return """
        .pyproforma-table-container {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-size: 11pt;
            margin: 10px 0;
        }
        .pyproforma-table {
            border-collapse: collapse;
            border: 1px solid #e8e8e8;
            background-color: white;
        }
        .pyproforma-table td {
            border: 1px solid #e8e8e8;
            padding: 6px 12px;
            color: #333;
            background-color: white;
        }
        .pyproforma-table tbody tr:hover td {
            background-color: #f9f9f9;
        }
    """


def _generate_cell_html(cell) -> str:
    """Generate HTML for a single cell with all its styling."""
    styles = []

    # Text alignment
    if cell.align:
        styles.append(f"text-align: {cell.align}")

    # Bold
    if cell.bold:
        styles.append("font-weight: bold")

    # Background color
    if cell.background_color:
        hex_color = color_to_hex(cell.background_color)
        styles.append(f"background-color: {hex_color}")

    # Font color
    if cell.font_color:
        hex_color = color_to_hex(cell.font_color)
        styles.append(f"color: {hex_color}")

    # Top border
    if cell.top_border:
        if cell.top_border == "single":
            styles.append("border-top: 2px solid black")
        elif cell.top_border == "double":
            styles.append("border-top: 4px double black")

    # Bottom border
    if cell.bottom_border:
        if cell.bottom_border == "single":
            styles.append("border-bottom: 2px solid black")
        elif cell.bottom_border == "double":
            styles.append("border-bottom: 4px double black")

    # Combine styles
    style_attr = "; ".join(styles)
    style_str = f' style="{style_attr}"' if style_attr else ""

    # Get formatted value
    formatted_value = cell.formatted_value if cell.formatted_value is not None else ""

    # Return the cell HTML
    return f"<td{style_str}>{_escape_html(str(formatted_value))}</td>"


def _escape_html(text: str) -> str:
    """Escape HTML special characters to prevent XSS and display issues."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )
