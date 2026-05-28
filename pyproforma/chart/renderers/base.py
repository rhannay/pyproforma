"""Abstract base class for chart renderers."""

from abc import ABC, abstractmethod

from pyproforma.chart.chart_spec import ChartSpec


class ChartRenderer(ABC):
    """Base class for rendering a ChartSpec to a specific backend."""

    @abstractmethod
    def render(self, spec: ChartSpec, **kwargs):
        """Render the ChartSpec and return the backend's figure/output object."""
