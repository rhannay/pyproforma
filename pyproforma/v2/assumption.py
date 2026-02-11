"""
Assumption class for simple scalar values.

Assumption represents a simple value that applies to all periods or can vary by period.
This is a simplified version of FixedLine for common assumptions like growth rates,
tax rates, or other constant values.
"""

from typing import Any


class Assumption:
    """
    A simple value assumption for the model.

    Assumption is used to define simple values that can be constants (same for all
    periods) or vary by period. This is a convenience class for defining common
    model assumptions like growth rates, tax rates, or other parameters.

    Examples:
        >>> # Constant assumption
        >>> tax_rate = Assumption(value=0.21)
        >>>
        >>> # Period-varying assumption
        >>> growth_rate = Assumption(values={2024: 0.1, 2025: 0.12, 2026: 0.11})
        >>>
        >>> # In a model definition
        >>> class MyModel(ProformaModel):
        ...     tax_rate = Assumption(value=0.21)
        ...     growth_rate = Assumption(value=0.1)
        ...     revenue = FormulaLine(formula=lambda: base_revenue * (1 + growth_rate))

    Attributes:
        value (float, optional): Scalar value that applies to all periods.
        values (dict[int, float], optional): Dictionary mapping periods to values.
        label (str, optional): Human-readable label for display purposes.
        description (str, optional): Longer description of the assumption.
    """

    def __init__(
        self,
        value: float | None = None,
        values: dict[int, float] | None = None,
        label: str | None = None,
        description: str | None = None,
    ):
        """
        Initialize an Assumption.

        Args:
            value (float, optional): Scalar value for all periods. Defaults to None.
            values (dict[int, float], optional): Period-specific values. If both value
                and values are provided, values takes precedence. Defaults to None.
            label (str, optional): Human-readable label. Defaults to None.
            description (str, optional): Description of the assumption. Defaults to None.
        """
        self.value = value
        self.values = values or {}
        self.label = label
        self.description = description

    def get_value(self, period: int | None = None) -> float | None:
        """
        Get the assumption value for a specific period.

        If period-specific values are defined, return the value for that period.
        Otherwise, return the scalar value.

        Args:
            period (int, optional): The period to get the value for. If None and only
                a scalar value is defined, return the scalar. Defaults to None.

        Returns:
            float | None: The value for the specified period or the scalar value.
        """
        # If period-specific values exist and period is provided
        if self.values and period is not None:
            if period in self.values:
                return self.values[period]

        # Fall back to scalar value
        return self.value

    def __repr__(self):
        """Return a string representation of the Assumption."""
        return (
            f"Assumption(value={self.value}, "
            f"values={self.values}, "
            f"label={self.label!r}, "
            f"description={self.description!r})"
        )
