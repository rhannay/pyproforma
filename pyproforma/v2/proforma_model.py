"""
Base class for ProForma models in v2 API.

The ProformaModel class is inspired by Pydantic's design pattern where class attributes
become model fields. Users define models by subclassing ProformaModel and declaring
line items as class attributes using FixedLine, FormulaLine, or Assumption.
"""

from typing import Any

from pyproforma.v2.assumption import Assumption
from pyproforma.v2.assumption_values import AssumptionValues
from pyproforma.v2.calculation_engine import CalculationEngine
from pyproforma.v2.line_item import LineItem
from pyproforma.v2.line_item_values import LineItemValues


class ProformaModel:
    """
    Base class for user-defined financial models.

    ProformaModel provides a Pydantic-inspired interface for defining financial models.
    Users subclass ProformaModel and declare line items as class attributes. Each line
    item can be a FixedLine (with explicit period values), FormulaLine (with calculation
    logic), or Assumption (simple value).

    The class automatically discovers all line items declared as class attributes and
    manages the model structure. Periods (years) are defined when creating model instances.

    Examples:
        >>> class MyModel(ProformaModel):
        ...     revenue = FixedLine(values={2024: 100, 2025: 110})
        ...     expenses = FormulaLine(formula=lambda: revenue * 0.6)
        ...     profit = FormulaLine(formula=lambda: revenue - expenses)
        ...
        >>> model = MyModel(periods=[2024, 2025])

    Attributes:
        periods (list[int]): List of periods (typically years) for the model.
    """

    def __init_subclass__(cls, **kwargs):
        """
        Called when a subclass is created.

        This method automatically discovers and stores the names of all Assumption
        and LineItem attributes defined on the subclass.

        Args:
            **kwargs: Additional keyword arguments passed to super().__init_subclass__
        """
        super().__init_subclass__(**kwargs)

        # Discover assumption names from class attributes
        assumption_names = []
        line_item_names = []
        
        for name, value in cls.__dict__.items():
            if isinstance(value, Assumption):
                assumption_names.append(name)
            elif isinstance(value, LineItem):
                line_item_names.append(name)

        # Store as class attributes
        cls._assumption_names = assumption_names
        cls._line_item_names = line_item_names

    def __init__(self, periods: list[int] | None = None):
        """
        Initialize a ProformaModel instance.

        Args:
            periods (list[int], optional): List of periods (years) for the model.
                Defaults to None.
        """
        self.periods = periods or []
        
        # Initialize assumption values
        self.av = self._initialize_assumptions()
        
        # Initialize line item values (empty initially)
        self.li = LineItemValues(periods=self.periods)
        
        # Run calculation engine if periods are defined
        if self.periods:
            engine = CalculationEngine(self, self.av, self.li, self.periods)
            engine.calculate()

    def _initialize_assumptions(self) -> AssumptionValues:
        """
        Initialize assumption values from class attributes.

        Returns:
            AssumptionValues: Container with all assumption values.
        """
        assumption_values = {}
        
        # Get assumption names discovered during __init_subclass__
        assumption_names = getattr(self.__class__, "_assumption_names", [])
        
        # Extract values from each assumption
        for name in assumption_names:
            assumption = getattr(self.__class__, name)
            if isinstance(assumption, Assumption):
                assumption_values[name] = assumption.value
        
        return AssumptionValues(assumption_values)

    def __repr__(self):
        """Return a string representation of the model."""
        line_item_count = len(getattr(self.__class__, "_line_item_names", []))
        return (
            f"{self.__class__.__name__}("
            f"periods={self.periods}, "
            f"line_items={line_item_count})"
        )
