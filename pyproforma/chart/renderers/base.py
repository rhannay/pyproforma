"""
ChartRenderer — abstract base for rendering a Chart to a specific backend.

Implement render(chart, **kwargs) to add a new backend (plotly, charts.js, etc.).
"""

from abc import ABC, abstractmethod

from pyproforma.chart.chart import Chart


class ChartRenderer(ABC):
    """Base class for rendering a Chart to a specific backend."""

    @abstractmethod
    def render(self, chart: Chart, **kwargs):
        """Render the Chart and return the backend's figure/output object."""
