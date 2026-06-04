"""
Chart data layer for PyProforma.

Chart and ChartSeries are the intermediate representation between model data
and any rendering backend (matplotlib, charts.js, plotly, etc.).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from pyproforma.table.format_value import NumberFormatSpec

ChartType = Literal["line", "bar", "stacked_bar"]


@dataclass
class ChartSeries:
    """A single data series for a chart."""

    label: str
    x_values: list[int]
    y_values: list[float]
    color: str | None = None


@dataclass
class Chart:
    """
    Intermediate representation of a chart — pure data, rendering-backend agnostic.

    Build one via model.charts.line_item() or model.charts.line_items(), then
    render it with .show() / .figure() (matplotlib) or .to_apexcharts() (web/JSON).
    """

    series: list[ChartSeries]
    chart_type: ChartType = "line"
    title: str | None = None
    x_label: str | None = None
    y_label: str | None = None
    value_format: "NumberFormatSpec | None" = None

    # ------------------------------------------------------------------
    # Matplotlib convenience (lazy import — matplotlib not required at import time)
    # ------------------------------------------------------------------

    def figure(self, figsize: tuple[float, float] = (10, 6)):
        """Return a matplotlib Figure for this chart."""
        from pyproforma.chart.renderers.matplotlib_renderer import MatplotlibRenderer
        return MatplotlibRenderer().render(self, figsize=figsize)

    def show(self, figsize: tuple[float, float] = (10, 6)) -> None:
        """Render and display this chart via matplotlib."""
        import matplotlib.pyplot as plt
        self.figure(figsize=figsize)
        plt.show()

    # ------------------------------------------------------------------
    # Web / serialisation
    # ------------------------------------------------------------------

    def to_apexcharts(self) -> dict:
        """Return a dict of ApexCharts options ready for JSON serialization."""
        result = {
            "series": [
                {"name": s.label, "data": s.y_values}
                for s in self.series
            ],
            "categories": self.series[0].x_values if self.series else [],
            "title": self.title or "",
            "chart_type": self.chart_type,
            "yaxis_format": self.value_format.to_dict() if self.value_format else None,
        }
        colors = [s.color for s in self.series]
        if any(c is not None for c in colors):
            result["colors"] = colors
        return result

    def to_dict(self) -> dict:
        """Serialise this Chart to a plain dict suitable for JSON / web renderers."""
        return {
            "chart_type": self.chart_type,
            "title": self.title,
            "x_label": self.x_label,
            "y_label": self.y_label,
            "series": [
                {
                    "label": s.label,
                    "x_values": s.x_values,
                    "y_values": s.y_values,
                    "color": s.color,
                }
                for s in self.series
            ],
            "value_format": self.value_format.to_dict() if self.value_format else None,
        }


# Backwards compatibility alias
ChartSpec = Chart
