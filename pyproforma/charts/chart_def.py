"""
ChartDef — declarative definition of a chart to build from a model.

Used with model.charts.build() to produce a Chart. Holds the line item names,
chart type, title, optional per-series colors, and an optional value transform
("indexed"). Accepts either the dataclass form (IDE autocomplete, validation)
or a plain dict (JSON-serializable configs).
"""

from dataclasses import dataclass

from pyproforma.chart.chart import ChartType


@dataclass
class ChartDef:
    """
    Declarative definition of a chart to build from a model.

    Used with model.charts.from_template() to produce a ChartSpec.
    Accepts either the dataclass form (for Python code with IDE support)
    or a plain dict (for JSON-serializable configs).

    Examples:
        >>> ChartDef(names=["revenue", "expenses"])
        >>> ChartDef(names=["revenue"], chart_type="bar", title="Revenue")
        >>> ChartDef(names=["revenue", "expenses"], colors=["#206bc4", "#d63939"])
        >>> ChartDef(names=["revenue", "headcount"], transform="indexed")

    The dict form is equivalent:
        >>> {"names": ["revenue"], "chart_type": "bar", "colors": ["#206bc4"]}
        >>> {"names": ["revenue", "headcount"], "transform": "indexed"}
    """

    names: list[str]
    chart_type: ChartType = "line"
    title: str | None = None
    colors: list[str] | None = None
    transform: str | None = None
    base_period: int | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "ChartDef":
        return cls(
            names=data["names"],
            chart_type=data.get("chart_type", "line"),
            title=data.get("title"),
            colors=data.get("colors"),
            transform=data.get("transform"),
            base_period=data.get("base_period"),
        )
