"""Bootstrap HTML renderer for Table class.

Generates HTML using Bootstrap utility classes rather than inline CSS,
suitable for embedding in Flask/Jinja2 templates that already load Bootstrap.
No <style> block is injected — assumes Bootstrap CSS is provided by the page.
"""

from typing import TYPE_CHECKING

from .colors import color_to_hex

if TYPE_CHECKING:
    from .table_class import Table

# Map pyproforma align values to Bootstrap text alignment classes
_ALIGN_CLASS = {
    "left": "text-start",
    "center": "text-center",
    "right": "text-end",
}


def to_bootstrap_html(table: "Table") -> str:
    """Generate Bootstrap-compatible HTML for a Table.

    Outputs a <div class="table-responsive"> wrapping a
    <table class="table table-bordered table-hover"> with Bootstrap utility
    classes for alignment and bold. Inline styles are used only where Bootstrap
    has no equivalent (background color, font color, border overrides).

    No <style> block is emitted — the page must include Bootstrap CSS.

    Args:
        table: The Table instance to render.

    Returns:
        str: HTML fragment ready to embed in a Bootstrap page.
    """
    html_parts = ['<div class="table-responsive">']
    html_parts.append('<table class="table table-bordered table-hover mb-0">')

    if table.col_widths:
        html_parts.append("<colgroup>")
        for width in table.col_widths:
            if width is not None:
                html_parts.append(f'<col style="width: {width}px">')
            else:
                html_parts.append("<col>")
        html_parts.append("</colgroup>")

    if table.cells:
        html_parts.append("<tbody>")
        for row in table.cells:
            row_cells = [_generate_cell_html(cell) for cell in row]
            html_parts.append(f"<tr>{''.join(row_cells)}</tr>")
        html_parts.append("</tbody>")

    html_parts.append("</table>")
    html_parts.append("</div>")

    return "".join(html_parts)


def _generate_cell_html(cell) -> str:
    """Generate Bootstrap HTML for a single cell."""
    classes = []
    styles = []

    # Alignment — Bootstrap utility class
    align_class = _ALIGN_CLASS.get(cell.align)
    if align_class:
        classes.append(align_class)

    # Bold — Bootstrap utility class
    if cell.bold:
        classes.append("fw-bold")

    # Background color — no Bootstrap equivalent for arbitrary colors
    if cell.background_color:
        hex_color = color_to_hex(cell.background_color)
        styles.append(f"background-color: {hex_color}")

    # Font color
    if cell.font_color:
        hex_color = color_to_hex(cell.font_color)
        styles.append(f"color: {hex_color}")

    # Top border override
    if cell.top_border == "single":
        styles.append("border-top: 2px solid black")
    elif cell.top_border == "double":
        styles.append("border-top: 4px double black")

    # Bottom border override
    if cell.bottom_border == "single":
        styles.append("border-bottom: 2px solid black")
    elif cell.bottom_border == "double":
        styles.append("border-bottom: 4px double black")

    class_attr = f' class="{" ".join(classes)}"' if classes else ""
    style_attr = f' style="{"; ".join(styles)}"' if styles else ""

    formatted_value = cell.formatted_value if cell.formatted_value is not None else ""
    cell_content = _escape_html(str(formatted_value)) if formatted_value != "" else "&nbsp;"

    if cell.href and formatted_value != "":
        cell_content = f'<a href="{_escape_html(cell.href)}">{cell_content}</a>'

    return f"<td{class_attr}{style_attr}>{cell_content}</td>"


def _escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )
