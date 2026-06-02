"""ChartDef — declarative config for registering a chart."""

from dataclasses import dataclass, field
from typing import Union

from pyproforma.chart.chart_spec import ChartType


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

    The dict form is equivalent:
        >>> {"names": ["revenue"], "chart_type": "bar"}
    """

    names: list[str]
    chart_type: ChartType = "line"
    title: str | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "ChartDef":
        return cls(
            names=data["names"],
            chart_type=data.get("chart_type", "line"),
            title=data.get("title"),
        )
