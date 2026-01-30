"""HTML renderer for Table class with Excel-like grid styling.

This module provides an alternative HTML rendering method for the Table class
that generates custom HTML output without relying on pandas DataFrame styling.
The output is designed to look like an Excel grid with support for cell formatting,
borders, colors, and other styling options.
"""

from typing import TYPE_CHECKING

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
        >>> from pyproforma.tables import Table, Column, Row, Cell
        >>> columns = [Column("Name"), Column("Value")]
        >>> rows = [Row([Cell("Item 1", bold=True), Cell(100)])]
        >>> table = Table(columns=columns, rows=rows)
        >>> html = to_html(table)
    """
    # Build CSS styles
    css = _generate_css()

    # Build HTML table
    html_parts = ['<div class="pyproforma-table-container">']
    html_parts.append('<table class="pyproforma-table">')

    # Generate header row
    html_parts.append(_generate_header_row(table))

    # Generate data rows
    html_parts.extend(_generate_data_rows(table))

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
            border: 1px solid #d0d0d0;
            background-color: white;
        }
        .pyproforma-table th {
            background-color: #f0f0f0;
            border: 1px solid #d0d0d0;
            padding: 6px 12px;
            font-weight: 600;
            text-align: center;
            color: #333;
        }
        .pyproforma-table td {
            border: 1px solid #d0d0d0;
            padding: 6px 12px;
            color: #333;
            background-color: white;
        }
        .pyproforma-table tbody tr:hover td {
            background-color: #f9f9f9;
        }
    """


def _generate_header_row(table: "Table") -> str:
    """Generate the header row HTML."""
    header_cells = []
    for column in table.columns:
        # Get column alignment style
        align_style = f"text-align: {column.text_align};"
        formatted_label = column.formatted_label or ""
        header_cells.append(
            f'<th style="{align_style}">{_escape_html(str(formatted_label))}</th>'
        )

    return f"<thead><tr>{''.join(header_cells)}</tr></thead>"


def _generate_data_rows(table: "Table") -> list[str]:
    """Generate all data row HTML."""
    rows_html = []
    rows_html.append("<tbody>")

    for row in table.rows:
        row_cells = []
        for cell in row.cells:
            cell_html = _generate_cell_html(cell)
            row_cells.append(cell_html)
        rows_html.append(f"<tr>{''.join(row_cells)}</tr>")

    rows_html.append("</tbody>")
    return rows_html


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
        styles.append(f"background-color: {cell.background_color}")

    # Font color
    if cell.font_color:
        styles.append(f"color: {cell.font_color}")

    # Top border
    if cell.top_border:
        if cell.top_border == "single":
            styles.append("border-top: 1px solid black")
        elif cell.top_border == "double":
            styles.append("border-top: 3px double black")

    # Bottom border
    if cell.bottom_border:
        if cell.bottom_border == "single":
            styles.append("border-bottom: 1px solid black")
        elif cell.bottom_border == "double":
            styles.append("border-bottom: 3px double black")

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
