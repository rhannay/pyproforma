"""
TableDef — declarative definition of a table to build from a model.

Used with model.tables.build() to produce a Table. Holds the row configurations
and optional metadata (title, and future: subtitle, footnotes). Accepts either
the dataclass form (IDE autocomplete, validation) or a plain list of row
configurations passed directly to build().
"""

from dataclasses import dataclass


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
        hardcoded_color: Optional CSS color applied to every hardcoded (input /
            fixed) cell in the table's ItemRow / TagItemsRow rows. A row that
            sets its own hardcoded_color overrides this table-level default.

    Examples:
        >>> TableDef(rows=[HeaderRow(), ItemRow(name="revenue")], title="Revenue")
        >>> model.tables.build(TableDef(rows=[...], title="Debt Service Coverage"))
        >>> TableDef(rows=[...], hardcoded_color="#1f6feb")  # blue inputs

    The bare list form is also accepted by build():
        >>> model.tables.build([HeaderRow(), ItemRow(name="revenue")])
    """

    rows: list
    title: str | None = None
    hardcoded_color: str | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "TableDef":
        """
        Build a TableDef from a plain dict (e.g. parsed from YAML/JSON).

        Row dicts are eagerly converted to their row dataclass instances via
        dict_to_row_config, rather than left as dicts, since downstream code
        (e.g. the explorer's href injection) relies on isinstance checks.

        Args:
            data: Dict with keys "rows" (list of BaseRow instances or
                equivalent dicts) and optionally "title" and "hardcoded_color".

        Returns:
            TableDef
        """
        from pyproforma.tables.row_types import dict_to_row_config

        rows = [dict_to_row_config(r) if isinstance(r, dict) else r for r in data["rows"]]
        return cls(
            rows=rows,
            title=data.get("title"),
            hardcoded_color=data.get("hardcoded_color"),
        )
