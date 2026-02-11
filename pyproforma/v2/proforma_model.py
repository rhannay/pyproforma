"""
Base class for ProForma models in v2 API.

The ProformaModel class is inspired by Pydantic's design pattern where class attributes
become model fields. Users define models by subclassing ProformaModel and declaring
line items as class attributes using FixedLine, FormulaLine, or Assumption.
"""

from typing import Any


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

    def __init__(self, periods: list[int] | None = None):
        """
        Initialize a ProformaModel instance.

        Args:
            periods (list[int], optional): List of periods (years) for the model.
                Defaults to None.
        """
        self.periods = periods or []
        self._line_items = {}
        self._initialize_line_items()

    def _initialize_line_items(self):
        """
        Discover and initialize all line items declared as class attributes.

        This method scans the class hierarchy for line item declarations
        (FixedLine, FormulaLine, Assumption) and initializes them for this
        model instance.
        """
        # Scaffolding: Actual implementation would discover line items from class
        # attributes and initialize them with the model's periods
        pass

    def __repr__(self):
        """Return a string representation of the model."""
        return (
            f"{self.__class__.__name__}("
            f"periods={self.periods}, "
            f"line_items={len(self._line_items)})"
        )
