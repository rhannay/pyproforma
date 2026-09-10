"""
Declarative definitions for the explorer's compare mode.

CompareTableDef / CompareChartDef are lightweight specs (parsed from a config's
`compare:` block) that map onto ModelComparison.table() / .chart(). They are
distinct from TableDef / ChartDef — a compare artifact is always a cross-scenario
comparison, so it exposes comparison knobs (difference rows, value rows) rather
than row templates.
"""

from dataclasses import dataclass, field
from typing import Optional

_VALID_CHART_TYPES = ("line", "bar", "stacked_bar")


@dataclass
class CompareTableDef:
    """A cross-scenario comparison table.

    Attributes:
        title: Display title (the config key it was declared under).
        items: Line item names to include. Empty means all common items.
        include_values: Show the per-scenario value rows. Defaults to True.
        include_difference: Show absolute difference row(s). Defaults to True.
        include_percent_difference: Show percent difference row(s). Defaults to False.
    """

    title: str
    items: list[str] = field(default_factory=list)
    include_values: bool = True
    include_difference: bool = True
    include_percent_difference: bool = False

    @classmethod
    def from_dict(cls, title: str, data: dict) -> "CompareTableDef":
        unknown = set(data) - {
            "items",
            "include_values",
            "include_difference",
            "include_percent_difference",
        }
        if unknown:
            raise ValueError(
                f"compare table '{title}': unknown key(s) {sorted(unknown)}. "
                f"Allowed: items, include_values, include_difference, "
                f"include_percent_difference."
            )
        return cls(
            title=title,
            items=list(data.get("items", []) or []),
            include_values=bool(data.get("include_values", True)),
            include_difference=bool(data.get("include_difference", True)),
            include_percent_difference=bool(data.get("include_percent_difference", False)),
        )


@dataclass
class CompareChartDef:
    """A cross-scenario comparison chart (one series per scenario).

    Attributes:
        title: Display title (the config key it was declared under).
        item: Line item name to plot. Required.
        chart_type: "line", "bar", or "stacked_bar". Defaults to "line".
    """

    title: str
    item: str
    chart_type: str = "line"

    @classmethod
    def from_dict(cls, title: str, data: dict) -> "CompareChartDef":
        unknown = set(data) - {"item", "chart_type"}
        if unknown:
            raise ValueError(
                f"compare chart '{title}': unknown key(s) {sorted(unknown)}. "
                f"Allowed: item, chart_type."
            )
        item: Optional[str] = data.get("item")
        if not item:
            raise ValueError(f"compare chart '{title}': 'item' is required.")
        chart_type = data.get("chart_type", "line")
        if chart_type not in _VALID_CHART_TYPES:
            raise ValueError(
                f"compare chart '{title}': chart_type '{chart_type}' must be one "
                f"of {list(_VALID_CHART_TYPES)}."
            )
        return cls(title=title, item=item, chart_type=chart_type)
