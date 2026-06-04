"""Matplotlib rendering backend for ChartSpec."""

from __future__ import annotations

from pyproforma.chart.renderers.base import ChartRenderer
from pyproforma.chart.chart import Chart as ChartSpec


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
        import numpy as np

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
                series.y_values,
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
            ax.bar(x + offset, series.y_values, width, label=series.label, color=series.color)

        ax.set_xticks(x)
        ax.set_xticklabels([str(v) for v in spec.series[0].x_values])

    def _render_stacked_bar(self, ax, spec: ChartSpec) -> None:
        import numpy as np

        x = np.arange(len(spec.series[0].x_values))
        bottom = np.zeros(len(spec.series[0].x_values))

        for series in spec.series:
            y = np.array(series.y_values)
            ax.bar(x, y, bottom=bottom, label=series.label, color=series.color)
            bottom += y

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
