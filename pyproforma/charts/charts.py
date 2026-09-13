"""
Charts — model-aware namespace for building Chart objects.

Accessed via model.charts. Takes model data and builds Chart instances
via convenience methods (line_item, line_items) or the general build()
method which accepts a ChartDef or plain dict.

This layer knows about ProformaModel; the Chart class beneath it does not.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from pyproforma.chart.chart import Chart, ChartSeries, ChartType
from pyproforma.table import Format

if TYPE_CHECKING:
    from pyproforma.charts.chart_def import ChartDef
    from pyproforma.proforma_model import ProformaModel

Transform = Literal["indexed"]


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
        value_format=None,
    ) -> Chart:
        """
        Build a chart for a single line item.

        Args:
            name: Line item name.
            chart_type: One of "line", "bar", "stacked_bar". Defaults to "line".
            title: Chart title. Defaults to the line item's label (or name).
            value_format: Override the line item's value format for the y-axis.

        Returns:
            Chart ready for rendering.

        Raises:
            ValueError: If the line item doesn't exist in the model.

        Examples:
            >>> model.charts.line_item("revenue").show()
            >>> model.charts.line_item("revenue", chart_type="bar").figure()
            >>> model.charts.line_item("revenue", value_format=Format.MILLIONS_M).show()
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
            value_format=value_format or result.value_format,
        )

    def line_items(
        self,
        names: list[str],
        chart_type: ChartType = "line",
        title: str | None = None,
        value_format=None,
        transform: Transform | None = None,
        base_period: int | None = None,
    ) -> Chart:
        """
        Build a chart with one series per line item.

        If all line items share the same value_format it is applied to the chart
        automatically. Pass value_format explicitly to override.

        Args:
            names: List of line item names to include as series.
            chart_type: One of "line", "bar", "stacked_bar". Defaults to "line".
            title: Chart title. Defaults to None (no title).
            value_format: Override the auto-detected format for the y-axis.
                Defaults to Format.NO_DECIMALS when transform="indexed".
            transform: Optional value transform applied to every series before
                charting. "indexed" rebases each series to 100 at base_period:
                value[t] / value[base_period] * 100 — useful for comparing
                items with different units or scales (e.g. revenue vs.
                headcount) on a common axis. Defaults to None (raw values).
            base_period: Reference period for transform="indexed". Defaults to
                the model's first period. Raising if set without a transform
                catches the likely mistake of forgetting transform="indexed".

        Returns:
            Chart ready for rendering.

        Raises:
            ValueError: If any line item doesn't exist in the model, transform
                is not a recognized value, base_period is set without
                transform, base_period is not one of the model's periods, or
                (for transform="indexed") a series' base_period value is None
                or 0.

        Examples:
            >>> model.charts.line_items(["revenue", "expenses"]).show()
            >>> model.charts.line_items(["revenue", "cogs"], chart_type="stacked_bar").show()
            >>> model.charts.line_items(  # noqa: E501
            ...     ["revenue", "expenses"], value_format=Format.MILLIONS_M
            ... ).show()
            >>> # Compare growth trajectories on a common scale
            >>> model.charts.line_items(["revenue", "headcount"], transform="indexed").show()
        """
        for name in names:
            self._validate_line_item(name)

        if transform is not None and transform != "indexed":
            raise ValueError(f"Unrecognized transform {transform!r}. Valid values: 'indexed'.")
        if base_period is not None and transform is None:
            raise ValueError(
                "base_period is only valid with transform='indexed'. "
                "Did you forget to pass transform='indexed'?"
            )

        resolved_base_period = base_period
        if transform == "indexed" and resolved_base_period is None:
            resolved_base_period = self._model.periods[0]

        series = []
        for name in names:
            result = self._model[name]
            y_values = [result[p] for p in self._model.periods]
            if transform == "indexed":
                y_values = self._index_values(name, y_values, resolved_base_period)
            series.append(
                ChartSeries(
                    label=result.label or name,
                    x_values=list(self._model.periods),
                    y_values=y_values,
                )
            )

        if value_format is None:
            if transform == "indexed":
                value_format = Format.NO_DECIMALS
            else:
                formats = [self._model[n].value_format for n in names]
                value_format = formats[0] if len(set(formats)) == 1 else None

        y_label = f"Index (Base = 100, {resolved_base_period})" if transform == "indexed" else None

        return Chart(
            series=series,
            chart_type=chart_type,
            title=title,
            value_format=value_format,
            y_label=y_label,
        )

    def indexed_line_items(
        self,
        names: list[str],
        base_period: int | None = None,
        title: str | None = None,
        value_format=None,
    ) -> Chart:
        """
        Build a line chart with every series rebased to 100 at base_period.

        Convenience wrapper for line_items(names, transform="indexed", ...).
        Lets you compare line items with different units or scales (e.g.
        revenue in dollars vs. headcount) on a common relative axis.

        Args:
            names: List of line item names to include as series.
            base_period: Reference period; value[t] / value[base_period] * 100.
                Defaults to the model's first period.
            title: Chart title. Defaults to None (no title).
            value_format: Override the default (Format.NO_DECIMALS) y-axis format.

        Returns:
            Chart ready for rendering.

        Raises:
            ValueError: If any line item doesn't exist in the model, base_period
                is not one of the model's periods, or a series' base_period
                value is None or 0.

        Examples:
            >>> model.charts.indexed_line_items(["revenue", "headcount"]).show()
            >>> model.charts.indexed_line_items(["revenue"], base_period=2025).show()
        """
        return self.line_items(
            names,
            title=title,
            value_format=value_format,
            transform="indexed",
            base_period=base_period,
        )

    def _index_values(
        self, name: str, y_values: list[float | None], base_period: int
    ) -> list[float | None]:
        """Rebase a series to 100 at base_period. None stays None (a gap)."""
        try:
            base_index = self._model.periods.index(base_period)
        except ValueError:
            raise ValueError(
                f"base_period {base_period} is not in model periods {self._model.periods}"
            ) from None
        base_value = y_values[base_index]
        if not base_value:
            raise ValueError(
                f"Cannot index '{name}': base period {base_period} value is "
                f"{base_value!r} (must be a non-zero number)."
            )
        return [v / base_value * 100 if v is not None else None for v in y_values]

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
                - transform (str, optional): "indexed" to rebase every series to
                  100 at base_period. Defaults to None (raw values).
                - base_period (int, optional): Reference period for
                  transform="indexed". Defaults to the model's first period.

        Returns:
            Chart ready for rendering.

        Examples:
            >>> model.charts.from_template(ChartDef(names=["revenue", "expenses"]))
            >>> model.charts.from_template({"names": ["revenue"], "chart_type": "bar"})
            >>> model.charts.from_template(
            ...     {"names": ["revenue", "headcount"], "transform": "indexed"}
            ... )
        """
        from pyproforma.charts.chart_def import ChartDef
        if isinstance(template, dict):
            template = ChartDef.from_dict(template)
        chart_spec = self.line_items(
            names=template.names,
            chart_type=template.chart_type,
            title=template.title,
            transform=template.transform,
            base_period=template.base_period,
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
