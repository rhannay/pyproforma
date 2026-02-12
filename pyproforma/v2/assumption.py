"""
Assumption class for simple scalar values.

Assumption represents a simple scalar value that applies across all periods.
This is a simplified version of FixedLine for common assumptions like growth rates,
tax rates, or other constant values.
"""


class Assumption:
    """
    A simple value assumption for the model.

    Assumption is used to define simple scalar values that apply across all periods.
    This is a convenience class for defining common model assumptions like growth rates,
    tax rates, or other parameters.

    Examples:
        >>> # Simple assumption
        >>> tax_rate = Assumption(value=0.21)
        >>>
        >>> # Assumption with label
        >>> growth_rate = Assumption(value=0.1, label="Annual Growth Rate")
        >>>
        >>> # In a model definition
        >>> class MyModel(ProformaModel):
        ...     tax_rate = Assumption(value=0.21)
        ...     growth_rate = Assumption(value=0.1)
        ...     revenue = FormulaLine(formula=lambda: base_revenue * (1 + growth_rate))

    Attributes:
        value (float): Scalar value that applies to all periods.
        label (str, optional): Human-readable label for display purposes.
    """

    def __init__(
        self,
        value: float,
        label: str | None = None,
    ):
        """
        Initialize an Assumption.

        Args:
            value (float): Scalar value for all periods.
            label (str, optional): Human-readable label. Defaults to None.
        """
        self.value = value
        self.label = label

    def get_value(self, period: int | None = None) -> float:
        """
        Get the assumption value.

        The period parameter is accepted for API consistency but is ignored since
        assumptions are scalar values that apply to all periods.

        Args:
            period (int, optional): Ignored - provided for API consistency. Defaults to None.

        Returns:
            float: The scalar value.
        """
        return self.value

    def __repr__(self):
        """Return a string representation of the Assumption."""
        if self.label:
            return f"Assumption(value={self.value}, label={self.label!r})"
        return f"Assumption(value={self.value})"
