"""
TableDef — declarative definition of a table to build from a model.

Used with model.tables.build() to produce a Table. Holds the row configurations
and optional metadata (title, and future: subtitle, footnotes). Accepts either
the dataclass form (IDE autocomplete, validation) or a plain list of row
configurations passed directly to build().
"""

from dataclasses import dataclass, field
from typing import Union


@dataclass
class TableDef:
    """
    Declarative definition of a table to build from a model.

    Used with model.tables.build() to produce a Table. Accepts either the
    dataclass form (for Python code with IDE support) or a plain list of row
    configurations (for quick inline use).

    Attributes:
        rows: Row configurations — a list of BaseRow instances or equivalent dicts.
        title: Optional display title rendered above the table.

    Examples:
        >>> TableDef(rows=[HeaderRow(), ItemRow(name="revenue")], title="Revenue")
        >>> model.tables.build(TableDef(rows=[...], title="Debt Service Coverage"))

    The bare list form is also accepted by build():
        >>> model.tables.build([HeaderRow(), ItemRow(name="revenue")])
    """

    rows: list
    title: str | None = None
