"""
FormulaLine class for calculated line items.

FormulaLine represents a line item whose values are calculated using a formula function.
Values can be overridden for specific periods using the values parameter.
"""

from typing import Any, Callable


class FormulaLine:
    """
    A line item with values calculated from a formula.

    FormulaLine is used to define line items where values are calculated using a
    formula function. The formula can reference other line items in the model.
    Specific period values can be overridden using the values parameter.

    Examples:
        >>> # Simple formula
        >>> profit = FormulaLine(formula=lambda: revenue - expenses)
        >>>
        >>> # Formula with overrides
        >>> adjusted_profit = FormulaLine(
        ...     formula=lambda: profit * 0.9,
        ...     values={2024: 50000}  # Override for 2024
        ... )
        >>>
        >>> # In a model definition
        >>> class MyModel(ProformaModel):
        ...     revenue = FixedLine(values={2024: 100, 2025: 110})
        ...     expenses = FormulaLine(formula=lambda: revenue * 0.6)
        ...     profit = FormulaLine(formula=lambda: revenue - expenses)

    Attributes:
        formula (Callable): Function that calculates the line item values.
        values (dict[int, float], optional): Dictionary of value overrides for specific periods.
        label (str, optional): Human-readable label for display purposes.
        description (str, optional): Longer description of the line item.
    """

    def __init__(
        self,
        formula: Callable | None = None,
        values: dict[int, float] | None = None,
        label: str | None = None,
        description: str | None = None,
    ):
        """
        Initialize a FormulaLine.

        Args:
            formula (Callable, optional): Function that calculates values. The function
                should return a value or reference other line items. Defaults to None.
            values (dict[int, float], optional): Dictionary of value overrides for
                specific periods. These override calculated values. Defaults to None.
            label (str, optional): Human-readable label. Defaults to None.
            description (str, optional): Description of the line item. Defaults to None.
        """
        self.formula = formula
        self.values = values or {}
        self.label = label
        self.description = description

    def calculate(self) -> Any:
        """
        Calculate the formula result.

        Returns:
            Any: The result of evaluating the formula function.
        """
        # Scaffolding: Actual implementation would evaluate the formula
        # in the context of the model and return calculated values
        if self.formula is not None:
            return self.formula()
        return None

    def get_value(self, period: int) -> float | None:
        """
        Get the value for a specific period.

        If the period has an override value, return that. Otherwise,
        calculate the value using the formula.

        Args:
            period (int): The period (year) to get the value for.

        Returns:
            float | None: The value for the specified period.
        """
        # Check for override first
        if period in self.values:
            return self.values[period]

        # Scaffolding: Actual implementation would calculate from formula
        return None

    def __repr__(self):
        """Return a string representation of the FormulaLine."""
        return (
            f"FormulaLine(formula={self.formula!r}, "
            f"values={self.values}, "
            f"label={self.label!r}, "
            f"description={self.description!r})"
        )
