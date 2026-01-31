"""General table creation and formatting module.

This module provides the core table infrastructure for creating, formatting,
and exporting tables with rich styling and formatting options.
"""

from .excel import to_excel as to_excel
from .html_renderer import to_html as to_html
from .table_class import Cell as Cell
from .table_class import Table as Table
from .table_class import format_value as format_value

__all__ = [
    "Cell",
    "Table",
    "format_value",
    "to_excel",
    "to_html",
]
