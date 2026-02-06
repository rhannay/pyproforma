"""General table creation and formatting module.

This module provides the core table infrastructure for creating, formatting,
and exporting tables with rich styling and formatting options.
"""

from .excel import to_excel as to_excel
from .format_value import Format as Format
from .format_value import NumberFormatSpec as NumberFormatSpec
from .format_value import format_value as format_value
from .format_value import normalize_format as normalize_format
from .html_renderer import to_html as to_html
from .table_class import Cell as Cell
from .table_class import Table as Table

__all__ = [
    "Cell",
    "Table",
    "NumberFormatSpec",
    "Format",
    "format_value",
    "normalize_format",
    "to_excel",
    "to_html",
]
