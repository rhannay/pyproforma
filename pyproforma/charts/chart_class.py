from typing import TYPE_CHECKING, List, Literal, Optional, Tuple

import plotly.express as px
import plotly.graph_objects as go

from ..constants import ValueFormat

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure


class ChartDataSet:
    """A dataset for chart plotting."""

    def __init__(
        self,
        label: str,
        data: List[Optional[float]],
        color: Optional[str] = None,
        type: Literal["line", "bar", "scatter", "pie"] = "line",
        dashed: bool = False,
    ):
        # Validate chart type
        valid_types = {"line", "bar", "scatter", "pie"}
        if type not in valid_types:
            raise ValueError(
                f"Invalid chart type '{type}'. Must be one of: {', '.join(sorted(valid_types))}"  # noqa: E501
            )

        self.label = label
        self.data = data
        self.color = color
        self.type = type
        self.dashed = dashed

    def __repr__(self):
        return f"ChartDataSet(label='{self.label}', type='{self.type}', color='{self.color}')"  # noqa: E501


class Chart:
    """A chart configuration class that supports mixed chart types."""

    def __init__(
        self,
        labels: List[str],
        data_sets: List[ChartDataSet],
        id: str = "chart",
        title: str = "Chart",
        value_format: Optional[ValueFormat] = None,
    ):
        self.id = id
        self.title = title
        self.labels = labels
        self.data_sets = data_sets
        self.value_format = value_format

        # Validate chart type combinations
        self._validate_chart_types()

        # Assign colors to datasets that don't have colors defined
        self._assign_colors()

    def __repr__(self):
        chart_types = [ds.type for ds in self.data_sets]
        return f"Chart(id='{self.id}', title='{self.title}', types={chart_types})"

    def to_plotly(
        self,
        width: int = 800,
        height: int = 600,
        show_legend: bool = True,
        template: str = "plotly_white",
    ) -> go.Figure:
        """
        Render this Chart object using Plotly with mixed chart types.

        Args:
            width: Figure width in pixels
            height: Figure height in pixels
            show_legend: Whether to show the legend
            template: Plotly template to use

        Returns:
            plotly.graph_objects.Figure object
        """
        fig = go.Figure()

        # Add traces for each dataset based on their individual types
        x_positions = list(range(len(self.labels)))

        for dataset in self.data_sets:
            if dataset.type == "bar":
                self._add_bar_trace(fig, dataset, x_positions)
            elif dataset.type == "line":
                self._add_line_trace(fig, dataset, x_positions)
            elif dataset.type == "scatter":
                self._add_scatter_trace(fig, dataset, x_positions)
            elif dataset.type == "pie":
                self._add_pie_trace(fig, dataset, x_positions)
            else:
                # Default to line chart for unknown types
                self._add_line_trace(fig, dataset, x_positions)

        # Update layout
        fig.update_layout(
            title=dict(text=self.title, x=0.5, xanchor="center"),
            width=width,
            height=height,
            template=template,
            showlegend=show_legend,
            xaxis_title="",
            yaxis_title="",
            hovermode="x unified",
        )

        # Set x-axis labels
        fig.update_xaxes(
            tickmode="array",
            tickvals=list(range(len(self.labels))),
            ticktext=self.labels,
        )

        # Format y-axis based on value_format
        if self.value_format:
            if self.value_format == "no_decimals":
                fig.update_yaxes(tickformat=",.0f")
            elif self.value_format == "two_decimals":
                fig.update_yaxes(tickformat=",.2f")
            elif self.value_format == "percent":
                fig.update_yaxes(tickformat=".0%")
            elif self.value_format == "percent_one_decimal":
                fig.update_yaxes(tickformat=".1%")
            elif self.value_format == "percent_two_decimals":
                fig.update_yaxes(tickformat=".2%")

        return fig

    def to_matplotlib(
        self,
        width: int = 10,
        height: int = 6,
        show_legend: bool = True,
    ) -> Tuple["Figure", "Axes"]:
        """
        Render this Chart object using Matplotlib.

        Args:
            width: Figure width in inches
            height: Figure height in inches
            show_legend: Whether to show the legend

        Returns:
            tuple of (matplotlib.figure.Figure, matplotlib.axes.Axes)
        """
        # Import matplotlib here to make it an optional dependency
        try:
            import matplotlib.pyplot as plt
        except ImportError as e:
            raise ImportError(
                "Matplotlib is required to use to_matplotlib(). "
                "Install it with: pip install matplotlib"
            ) from e

        # Handle pie charts separately as they need different layout
        has_pie = any(ds.type == "pie" for ds in self.data_sets)
        if has_pie:
            if len(self.data_sets) > 1:
                raise ValueError(
                    "Pie charts cannot be rendered with other datasets. "
                    "Use a single ChartDataSet with type='pie' for pie charts."
                )
            # Create pie chart
            fig, ax = plt.subplots(figsize=(width, height))
            dataset = self.data_sets[0]
            ax.pie(
                dataset.data,
                labels=self.labels,
                autopct="%1.1f%%",
                startangle=90,
            )
            ax.axis("equal")  # Equal aspect ratio for circular pie
            ax.set_title(self.title, fontsize=14, fontweight="bold")
            fig.tight_layout()
            return fig, ax

        # Create figure and axis for non-pie charts
        fig, ax = plt.subplots(figsize=(width, height))

        # X-axis positions
        x_positions = list(range(len(self.labels)))

        # Track bar datasets for positioning
        bar_datasets = [ds for ds in self.data_sets if ds.type == "bar"]
        num_bars = len(bar_datasets)

        # Calculate bar width for grouped bars
        bar_width = 0.8 / num_bars if num_bars > 0 else 0.8

        # Add traces for each dataset based on their individual types
        bar_index = 0
        for dataset in self.data_sets:
            if dataset.type == "bar":
                # Calculate bar positions for grouped bars
                if num_bars > 1:
                    offset = (bar_index - (num_bars - 1) / 2) * bar_width
                    positions = [x + offset for x in x_positions]
                else:
                    positions = x_positions

                ax.bar(
                    positions,
                    dataset.data,
                    width=bar_width,
                    label=dataset.label,
                    color=dataset.color,
                )
                bar_index += 1

            elif dataset.type == "line":
                linestyle = "--" if dataset.dashed else "-"
                ax.plot(
                    x_positions,
                    dataset.data,
                    marker="o",
                    linestyle=linestyle,
                    linewidth=2,
                    markersize=6,
                    label=dataset.label,
                    color=dataset.color,
                )

            elif dataset.type == "scatter":
                ax.scatter(
                    x_positions,
                    dataset.data,
                    s=80,
                    alpha=0.7,
                    label=dataset.label,
                    color=dataset.color,
                )

        # Set title
        ax.set_title(self.title, fontsize=14, fontweight="bold")

        # Set x-axis labels
        ax.set_xticks(x_positions)
        ax.set_xticklabels(self.labels)

        # Format y-axis based on value_format
        if self.value_format:
            if self.value_format == "no_decimals":
                ax.yaxis.set_major_formatter(
                    plt.FuncFormatter(lambda y, _: f"{y:,.0f}")
                )
            elif self.value_format == "two_decimals":
                ax.yaxis.set_major_formatter(
                    plt.FuncFormatter(lambda y, _: f"{y:,.2f}")
                )
            elif self.value_format == "percent":
                ax.yaxis.set_major_formatter(
                    plt.FuncFormatter(lambda y, _: f"{y:.0%}")
                )
            elif self.value_format == "percent_one_decimal":
                ax.yaxis.set_major_formatter(
                    plt.FuncFormatter(lambda y, _: f"{y:.1%}")
                )
            elif self.value_format == "percent_two_decimals":
                ax.yaxis.set_major_formatter(
                    plt.FuncFormatter(lambda y, _: f"{y:.2%}")
                )

        # Show legend if requested
        if show_legend:
            ax.legend()

        # Add grid for better readability
        ax.grid(True, alpha=0.3)

        # Tight layout to prevent label cutoff
        fig.tight_layout()

        return fig, ax

    def _add_bar_trace(
        self, fig: go.Figure, dataset: ChartDataSet, x_positions: List[int]
    ) -> None:
        """Add a bar trace to the figure."""
        fig.add_trace(
            go.Bar(
                x=x_positions,
                y=dataset.data,
                name=dataset.label,
                marker_color=dataset.color,
                hovertemplate="<b>%{fullData.name}</b><br>"
                + "Value: %{y}<br>"
                + "<extra></extra>",
            )
        )

    def _add_line_trace(
        self, fig: go.Figure, dataset: ChartDataSet, x_positions: List[int]
    ) -> None:
        """Add a line trace to the figure."""
        line_dash = "dash" if dataset.dashed else "solid"
        fig.add_trace(
            go.Scatter(
                x=x_positions,
                y=dataset.data,
                mode="lines+markers",
                name=dataset.label,
                line=dict(color=dataset.color, dash=line_dash, width=2),
                marker=dict(size=6),
                hovertemplate="<b>%{fullData.name}</b><br>"
                + "Value: %{y}<br>"
                + "<extra></extra>",
            )
        )

    def _add_scatter_trace(
        self, fig: go.Figure, dataset: ChartDataSet, x_positions: List[int]
    ) -> None:
        """Add a scatter trace to the figure."""
        fig.add_trace(
            go.Scatter(
                x=x_positions,
                y=dataset.data,
                mode="markers",
                name=dataset.label,
                marker=dict(color=dataset.color, size=8, opacity=0.7),
                hovertemplate="<b>%{fullData.name}</b><br>"
                + "Value: %{y}<br>"
                + "<extra></extra>",
            )
        )

    def _add_pie_trace(
        self, fig: go.Figure, dataset: ChartDataSet, x_positions: List[int]
    ) -> None:
        """Add a pie trace to the figure."""
        fig.add_trace(
            go.Pie(
                labels=self.labels,
                values=dataset.data,
                name=dataset.label,
                textinfo="label+percent",
                hovertemplate="<b>%{label}</b><br>"
                + "Value: %{value}<br>"
                + "Percent: %{percent}<br>"
                + "<extra></extra>",
            )
        )

    def _assign_colors(self) -> None:
        """Assign colors to datasets that don't have colors defined using Plotly's color palette."""  # noqa: E501
        color_index = 0
        for dataset in self.data_sets:
            if dataset.color is None:
                plotly_colors = px.colors.qualitative.Plotly
                dataset.color = plotly_colors[color_index % len(plotly_colors)]
                color_index += 1

    def _validate_chart_types(self) -> None:
        """Validate that chart types can be mixed together."""
        if len(self.data_sets) == 0:
            return

        has_pie = any(ds.type == "pie" for ds in self.data_sets)
        has_other = any(ds.type != "pie" for ds in self.data_sets)

        if has_pie and (len(self.data_sets) > 1 or has_other):
            raise ValueError(
                "Pie charts cannot be combined with other chart types or multiple datasets. "  # noqa: E501
                "Use a single ChartDataSet with type='pie' for pie charts."
            )
