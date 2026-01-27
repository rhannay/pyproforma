from typing import List, Literal, Optional

import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go

from ..constants import ValueFormat


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
        width: int = 8,
        height: int = 6,
        show_legend: bool = True,
        style: str = "seaborn-v0_8-whitegrid",
    ):
        """
        Render this Chart object using Matplotlib with mixed chart types.

        Args:
            width: Figure width in inches
            height: Figure height in inches
            show_legend: Whether to show the legend
            style: Matplotlib style to use

        Returns:
            tuple of (matplotlib.figure.Figure, matplotlib.axes.Axes)
        """
        # Create figure and axis
        fig, ax = plt.subplots(figsize=(width, height))

        # Apply style
        try:
            plt.style.use(style)
        except:
            # If style doesn't exist, continue with default
            pass

        # Add plots for each dataset based on their individual types
        x_positions = list(range(len(self.labels)))

        for dataset in self.data_sets:
            if dataset.type == "bar":
                self._add_bar_matplotlib(ax, dataset, x_positions)
            elif dataset.type == "line":
                self._add_line_matplotlib(ax, dataset, x_positions)
            elif dataset.type == "scatter":
                self._add_scatter_matplotlib(ax, dataset, x_positions)
            elif dataset.type == "pie":
                self._add_pie_matplotlib(ax, dataset)
            else:
                # Default to line chart for unknown types
                self._add_line_matplotlib(ax, dataset, x_positions)

        # Set title
        ax.set_title(self.title, fontsize=14, pad=20)

        # Set x-axis labels (not for pie charts)
        if not any(ds.type == "pie" for ds in self.data_sets):
            ax.set_xticks(x_positions)
            ax.set_xticklabels(self.labels)
            ax.set_xlabel("")
            ax.set_ylabel("")

        # Format y-axis based on value_format
        if self.value_format and not any(ds.type == "pie" for ds in self.data_sets):
            if self.value_format == "no_decimals":
                ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y:,.0f}'))
            elif self.value_format == "two_decimals":
                ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y:,.2f}'))
            elif self.value_format == "percent":
                ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y:.0%}'))
            elif self.value_format == "percent_one_decimal":
                ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y:.1%}'))
            elif self.value_format == "percent_two_decimals":
                ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y:.2%}'))

        # Show legend
        if show_legend and len(self.data_sets) > 0:
            ax.legend()

        # Adjust layout
        fig.tight_layout()

        return fig, ax

    def _add_bar_matplotlib(self, ax, dataset: ChartDataSet, x_positions: List[int]) -> None:
        """Add a bar plot to the matplotlib axis."""
        ax.bar(
            x_positions,
            dataset.data,
            label=dataset.label,
            color=dataset.color,
            alpha=0.8,
        )

    def _add_line_matplotlib(self, ax, dataset: ChartDataSet, x_positions: List[int]) -> None:
        """Add a line plot to the matplotlib axis."""
        linestyle = '--' if dataset.dashed else '-'
        ax.plot(
            x_positions,
            dataset.data,
            label=dataset.label,
            color=dataset.color,
            linestyle=linestyle,
            linewidth=2,
            marker='o',
            markersize=6,
        )

    def _add_scatter_matplotlib(self, ax, dataset: ChartDataSet, x_positions: List[int]) -> None:
        """Add a scatter plot to the matplotlib axis."""
        ax.scatter(
            x_positions,
            dataset.data,
            label=dataset.label,
            color=dataset.color,
            s=80,
            alpha=0.7,
        )

    def _add_pie_matplotlib(self, ax, dataset: ChartDataSet) -> None:
        """Add a pie chart to the matplotlib axis."""
        ax.pie(
            dataset.data,
            labels=self.labels,
            autopct='%1.1f%%',
            startangle=90,
            colors=[dataset.color] if dataset.color else None,
        )
        ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle

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
