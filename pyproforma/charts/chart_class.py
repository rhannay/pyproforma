from typing import List, Optional, Union, Literal
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from ..constants import ValueFormat


class ChartDataSet:
    """A dataset for chart plotting."""
    
    def __init__(
        self,
        label: str,
        data: List[Optional[float]],
        color: Optional[str] = None,
        type: Literal['line', 'bar', 'scatter', 'pie'] = 'line',
        dashed: bool = False
    ):
        # Validate chart type
        valid_types = {'line', 'bar', 'scatter', 'pie'}
        if type not in valid_types:
            raise ValueError(f"Invalid chart type '{type}'. Must be one of: {', '.join(sorted(valid_types))}")
        
        self.label = label
        self.data = data
        self.color = color
        self.type = type
        self.dashed = dashed
    
    def __repr__(self):
        return f"ChartDataSet(label='{self.label}', type='{self.type}', color='{self.color}')"


class Chart:
    """A chart configuration class that supports mixed chart types."""
    
    def __init__(
        self,
        labels: List[str],
        data_sets: List[ChartDataSet],
        id: str = 'chart',
        title: str = 'Chart',
        value_format: Optional[ValueFormat] = None
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
        template: str = 'plotly_white'
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
            if dataset.type == 'bar':
                self._add_bar_trace(fig, dataset, x_positions)
            elif dataset.type == 'line':
                self._add_line_trace(fig, dataset, x_positions)
            elif dataset.type == 'scatter':
                self._add_scatter_trace(fig, dataset, x_positions)
            elif dataset.type == 'pie':
                self._add_pie_trace(fig, dataset, x_positions)
            else:
                # Default to line chart for unknown types
                self._add_line_trace(fig, dataset, x_positions)
        
        # Update layout
        fig.update_layout(
            title=dict(
                text=self.title,
                x=0.5,
                xanchor='center'
            ),
            width=width,
            height=height,
            template=template,
            showlegend=show_legend,
            xaxis_title="",
            yaxis_title="",
            hovermode='x unified'
        )
        
        # Set x-axis labels
        fig.update_xaxes(
            tickmode='array',
            tickvals=list(range(len(self.labels))),
            ticktext=self.labels
        )
        
        # Format y-axis based on value_format
        if self.value_format:
            if self.value_format == 'no_decimals':
                fig.update_yaxes(tickformat=',.0f')
            elif self.value_format == 'two_decimals':
                fig.update_yaxes(tickformat=',.2f')
            elif self.value_format == 'percent':
                fig.update_yaxes(tickformat='.0%')
            elif self.value_format == 'percent_one_decimal':
                fig.update_yaxes(tickformat='.1%')
            elif self.value_format == 'percent_two_decimals':
                fig.update_yaxes(tickformat='.2%')
        
        return fig

    def _add_bar_trace(self, fig: go.Figure, dataset: ChartDataSet, x_positions: List[int]) -> None:
        """Add a bar trace to the figure."""
        fig.add_trace(go.Bar(
            x=x_positions,
            y=dataset.data,
            name=dataset.label,
            marker_color=dataset.color,
            hovertemplate='<b>%{fullData.name}</b><br>' +
                         'Value: %{y}<br>' +
                         '<extra></extra>'
        ))

    def _add_line_trace(self, fig: go.Figure, dataset: ChartDataSet, x_positions: List[int]) -> None:
        """Add a line trace to the figure."""
        line_dash = 'dash' if dataset.dashed else 'solid'
        fig.add_trace(go.Scatter(
            x=x_positions,
            y=dataset.data,
            mode='lines+markers',
            name=dataset.label,
            line=dict(color=dataset.color, dash=line_dash, width=2),
            marker=dict(size=6),
            hovertemplate='<b>%{fullData.name}</b><br>' +
                         'Value: %{y}<br>' +
                         '<extra></extra>'
        ))

    def _add_scatter_trace(self, fig: go.Figure, dataset: ChartDataSet, x_positions: List[int]) -> None:
        """Add a scatter trace to the figure."""
        fig.add_trace(go.Scatter(
            x=x_positions,
            y=dataset.data,
            mode='markers',
            name=dataset.label,
            marker=dict(color=dataset.color, size=8, opacity=0.7),
            hovertemplate='<b>%{fullData.name}</b><br>' +
                         'Value: %{y}<br>' +
                         '<extra></extra>'
        ))

    def _add_pie_trace(self, fig: go.Figure, dataset: ChartDataSet, x_positions: List[int]) -> None:
        """Add a pie trace to the figure."""
        fig.add_trace(go.Pie(
            labels=self.labels,
            values=dataset.data,
            name=dataset.label,
            textinfo='label+percent',
            hovertemplate='<b>%{label}</b><br>' +
                         'Value: %{value}<br>' +
                         'Percent: %{percent}<br>' +
                         '<extra></extra>'
        ))

    def _assign_colors(self) -> None:
        """Assign colors to datasets that don't have colors defined using Plotly's color palette."""
        color_index = 0
        for dataset in self.data_sets:
            if dataset.color is None:
                dataset.color = px.colors.qualitative.Plotly[color_index % len(px.colors.qualitative.Plotly)]
                color_index += 1

    def _validate_chart_types(self) -> None:
        """Validate that chart types can be mixed together."""
        if len(self.data_sets) == 0:
            return
            
        has_pie = any(ds.type == 'pie' for ds in self.data_sets)
        has_other = any(ds.type != 'pie' for ds in self.data_sets)
        
        if has_pie and (len(self.data_sets) > 1 or has_other):
            raise ValueError(
                "Pie charts cannot be combined with other chart types or multiple datasets. "
                "Use a single ChartDataSet with type='pie' for pie charts."
            )