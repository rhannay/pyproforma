"""
Charts — model-aware namespace for building Chart objects.

Accessed via model.charts. Takes model data and builds Chart instances
via convenience methods (line_item, line_items) or the general build()
method which accepts a ChartDef or plain dict.

This layer knows about ProformaModel; the Chart class beneath it does not.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyproforma.chart.chart import Chart, ChartSeries, ChartType

if TYPE_CHECKING:
    from pyproforma.proforma_model import ProformaModel


class Charts:
    """
    Namespace for chart creation methods on a ProformaModel.

    Accessed via model.charts. Each method returns a Chart — the
    intermediate data representation — which can then be rendered via
    .show() (matplotlib) or .to_dict() (web / JSON).

    Examples:
        >>> chart = model.charts.line_item("revenue")
        >>> chart.show()

        >>> chart = model.charts.line_items(["revenue", "expenses"], chart_type="bar")
        >>> fig = chart.figure(figsize=(12, 5))
    """

    def __init__(self, model: "ProformaModel") -> None:
        self._model = model

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def line_item(
        self,
        name: str,
        chart_type: ChartType = "line",
        title: str | None = None,
    ) -> Chart:
        """
        Build a chart for a single line item.

        Args:
            name: Line item name.
            chart_type: One of "line", "bar", "stacked_bar". Defaults to "line".
            title: Chart title. Defaults to the line item's label (or name).

        Returns:
            Chart ready for rendering.

        Raises:
            ValueError: If the line item doesn't exist in the model.

        Examples:
            >>> model.charts.line_item("revenue").show()
            >>> model.charts.line_item("revenue", chart_type="bar").figure()
        """
        self._validate_line_item(name)
        result = self._model[name]
        label = result.label or name

        series = ChartSeries(
            label=label,
            x_values=list(self._model.periods),
            y_values=[result[p] for p in self._model.periods],
        )

        return Chart(
            series=[series],
            chart_type=chart_type,
            title=title if title is not None else label,
            value_format=result.value_format,
        )

    def line_items(
        self,
        names: list[str],
        chart_type: ChartType = "line",
        title: str | None = None,
        value_format=None,
    ) -> Chart:
        """
        Build a chart with one series per line item.

        Args:
            names: List of line item names to include as series.
            chart_type: One of "line", "bar", "stacked_bar". Defaults to "line".
            title: Chart title. Defaults to None (no title).

        Returns:
            Chart ready for rendering.

        Raises:
            ValueError: If any line item doesn't exist in the model.

        Examples:
            >>> model.charts.line_items(["revenue", "expenses"]).show()
            >>> model.charts.line_items(["revenue", "cogs"], chart_type="stacked_bar").show()
        """
        for name in names:
            self._validate_line_item(name)

        series = []
        for name in names:
            result = self._model[name]
            series.append(
                ChartSeries(
                    label=result.label or name,
                    x_values=list(self._model.periods),
                    y_values=[result[p] for p in self._model.periods],
                )
            )

        if value_format is None:
            formats = [self._model[n].value_format for n in names]
            value_format = formats[0] if len(set(formats)) == 1 else None

        return Chart(
            series=series,
            chart_type=chart_type,
            title=title,
            value_format=value_format,
        )

    def build(self, template: "ChartDef | dict") -> Chart:
        """
        Build a Chart from a ChartDef or equivalent dict.

        Accepts either the ChartDef dataclass (for Python code with IDE support)
        or a plain dict (for JSON-serializable configs). Both produce identical results.

        Args:
            template: A ChartDef instance or a dict with keys:
                - names (list[str]): Line item names to include as series.
                - chart_type (str, optional): "line", "bar", or "stacked_bar". Defaults to "line".
                - title (str, optional): Chart title.

        Returns:
            Chart ready for rendering.

        Examples:
            >>> model.charts.from_template(ChartDef(names=["revenue", "expenses"]))
            >>> model.charts.from_template({"names": ["revenue"], "chart_type": "bar"})
        """
        from pyproforma.charts.chart_def import ChartDef
        if isinstance(template, dict):
            template = ChartDef.from_dict(template)
        chart_spec = self.line_items(
            names=template.names,
            chart_type=template.chart_type,
            title=template.title,
        )
        if template.colors:
            for series, color in zip(chart_spec.series, template.colors):
                series.color = color
        return chart_spec

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _validate_line_item(self, name: str) -> None:
        if name not in self._model.line_item_names:
            raise ValueError(
                f"Line item '{name}' not found in model. "
                f"Available line items: {', '.join(sorted(self._model.line_item_names))}"
            )
