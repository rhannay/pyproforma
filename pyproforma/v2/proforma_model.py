"""
Base class for ProForma models in v2 API.

The ProformaModel class is inspired by Pydantic's design pattern where class attributes
become model fields. Users define models by subclassing ProformaModel and declaring
line items as class attributes using FixedLine, FormulaLine, or Assumption.
"""

from pyproforma.v2.assumption import Assumption
from pyproforma.v2.assumption_values import AssumptionValues
from pyproforma.v2.calculation_engine import calculate_line_items
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

        # Store instance copies of discovered names
        self.line_item_names = self.__class__._line_item_names
        self.assumption_names = self.__class__._assumption_names

        # Initialize assumption values
        self.av = self._initialize_assumptions()

        # Calculate line item values
        if self.periods:
            self._li = calculate_line_items(self, self.av, self.periods)
        else:
            self._li = LineItemValues(periods=[])

    def _initialize_assumptions(self) -> AssumptionValues:
        """
        Initialize assumption values from class attributes.

        Returns:
            AssumptionValues: Container with all assumption values.
        """
        assumption_values = {}

        # Extract values from each assumption
        for name in self.assumption_names:
            assumption = getattr(self.__class__, name)
            if isinstance(assumption, Assumption):
                assumption_values[name] = assumption.value

        return AssumptionValues(assumption_values)

    def get_value(self, name: str, period: int) -> float:
        """
        Get the calculated value for a line item at a specific period.

        Args:
            name (str): The name of the line item.
            period (int): The period to get the value for.

        Returns:
            float: The calculated value.

        Raises:
            AttributeError: If the line item name doesn't exist.
            KeyError: If the period hasn't been calculated.
        """
        # Use attribute access which raises proper errors
        line_item = getattr(self._li, name)  # Raises AttributeError if name doesn't exist
        return line_item[period]  # Raises KeyError if period doesn't exist

    def __repr__(self):
        """Return a string representation of the model."""
        line_item_count = len(self.line_item_names)
        return (
            f"{self.__class__.__name__}("
            f"periods={self.periods}, "
            f"line_items={line_item_count})"
        )
