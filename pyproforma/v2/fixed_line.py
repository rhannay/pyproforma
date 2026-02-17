"""
FixedLine class for line items with explicit period values.

FixedLine represents a line item with fixed values specified for each period.
Values are provided as a dictionary mapping periods (years) to numeric values.
"""

from pyproforma.v2.line_item import LineItem


class FixedLine(LineItem):
    """
    A line item with fixed values for each period.

    FixedLine is used to define line items where values are explicitly provided
    for each period in a period-value dictionary. This is the simplest way to
    define line items when you know the exact values for each period.

    Examples:
        >>> revenue = FixedLine(values={2024: 100000, 2025: 110000, 2026: 121000})
        >>> growth_rate = FixedLine(values={2024: 0.1, 2025: 0.1, 2026: 0.1})
        >>> # Can also use in a model definition
        >>> class MyModel(ProformaModel):
        ...     revenue = FixedLine(values={2024: 100, 2025: 110})

    Attributes:
        values (dict[int, float]): Dictionary mapping periods to numeric values.
        label (str, optional): Human-readable label for display purposes.
        tags (list[str]): List of tags for categorizing the line item.
    """

    def __init__(
        self,
        values: dict[int, float] | None = None,
        label: str | None = None,
        tags: list[str] | None = None,
    ):
        """
        Initialize a FixedLine.

        Args:
            values (dict[int, float], optional): Dictionary mapping periods (years)
                to numeric values. Defaults to None (empty dict).
            label (str, optional): Human-readable label. Defaults to None.
            tags (list[str], optional): List of tags for categorizing the line item.
                Defaults to None (empty list).
        """
        super().__init__(label=label, tags=tags)
        self.values = values or {}

    def get_value(self, period: int) -> float | None:
        """
        Get the value for a specific period.

        Args:
            period (int): The period (year) to get the value for.

        Returns:
            float | None: The value for the specified period, or None if not defined.
        """
        return self.values.get(period)

    def __repr__(self):
        """Return a string representation of the FixedLine."""
        if self.label:
            return f"FixedLine(values={self.values}, label={self.label!r})"
        return f"FixedLine(values={self.values})"
