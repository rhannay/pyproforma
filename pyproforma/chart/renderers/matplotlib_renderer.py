"""
MatplotlibRenderer — renders a Chart to a matplotlib Figure.

Called by Chart.show() and Chart.figure(). Supports line, bar, and stacked_bar
chart types. Applies NumberFormatSpec to y-axis tick labels when set.
"""

from __future__ import annotations

from pyproforma.chart.chart import Chart as ChartSpec
from pyproforma.chart.renderers.base import ChartRenderer


def _as_gaps(y_values: list[float | None]) -> list[float]:
    """Convert None to NaN — matplotlib's documented "break the plot here" sentinel.

    A plain Python list mixing floats and None becomes a numpy object array,
    which matplotlib doesn't reliably render; NaN keeps it a clean float array.
    """
    return [v if v is not None else float("nan") for v in y_values]


class MatplotlibRenderer(ChartRenderer):
    """Renders a ChartSpec to a matplotlib Figure."""

    def render(self, spec: ChartSpec, figsize: tuple[float, float] = (10, 6)):
        """
        Render a ChartSpec and return a matplotlib Figure.

        Args:
            spec: The chart specification to render.
            figsize: (width, height) in inches. Defaults to (10, 6).

        Returns:
            matplotlib.figure.Figure
        """
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=figsize)

        if spec.chart_type == "line":
            self._render_line(ax, spec)
        elif spec.chart_type == "bar":
            self._render_bar(ax, spec)
        elif spec.chart_type == "stacked_bar":
            self._render_stacked_bar(ax, spec)

        self._apply_labels(ax, spec)
        self._apply_y_format(ax, spec)

        if len(spec.series) > 1:
            ax.legend()

        ax.grid(True, alpha=0.3)
        plt.tight_layout()

        return fig

    # ------------------------------------------------------------------
    # Chart type renderers
    # ------------------------------------------------------------------

    def _render_line(self, ax, spec: ChartSpec) -> None:
        for series in spec.series:
            ax.plot(
                series.x_values,
                _as_gaps(series.y_values),
                label=series.label,
                color=series.color,
                marker="o",
                linewidth=2,
                markersize=5,
            )

    def _render_bar(self, ax, spec: ChartSpec) -> None:
        import numpy as np

        n = len(spec.series)
        x = np.arange(len(spec.series[0].x_values))
        width = 0.8 / n

        for i, series in enumerate(spec.series):
            offset = (i - n / 2 + 0.5) * width
            ax.bar(
                x + offset, _as_gaps(series.y_values), width,
                label=series.label, color=series.color,
            )

        ax.set_xticks(x)
        ax.set_xticklabels([str(v) for v in spec.series[0].x_values])

    def _render_stacked_bar(self, ax, spec: ChartSpec) -> None:
        import numpy as np

        x = np.arange(len(spec.series[0].x_values))
        bottom = np.zeros(len(spec.series[0].x_values))

        for series in spec.series:
            # None contributes nothing to the running stack height, but its own
            # segment doesn't draw (NaN) rather than rendering as a visible
            # zero-height bar — so a gap in one series doesn't blank out the
            # segments stacked above it.
            ax.bar(
                x, _as_gaps(series.y_values), bottom=bottom,
                label=series.label, color=series.color,
            )
            bottom += np.array([v if v is not None else 0.0 for v in series.y_values])

        ax.set_xticks(x)
        ax.set_xticklabels([str(v) for v in spec.series[0].x_values])

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------

    def _apply_labels(self, ax, spec: ChartSpec) -> None:
        if spec.title:
            ax.set_title(spec.title)
        if spec.x_label:
            ax.set_xlabel(spec.x_label)
        if spec.y_label:
            ax.set_ylabel(spec.y_label)

    def _apply_y_format(self, ax, spec: ChartSpec) -> None:
        if spec.value_format is None:
            return

        from matplotlib.ticker import FuncFormatter

        from pyproforma.table.format_value import format_value

        fmt = spec.value_format
        ax.yaxis.set_major_formatter(FuncFormatter(lambda val, _pos: format_value(val, fmt)))
