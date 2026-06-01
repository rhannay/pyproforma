"""
FixedLine class for line items with explicit period values or a scalar constant.

FixedLine represents a line item whose values are either specified per-period
as a dict, or as a single scalar constant that applies to every period.
"""

from typing import Union

from pyproforma.table import NumberFormatSpec

from .line_item import LineItem


class FixedLine(LineItem):
    """
    A line item with fixed values for each period, or a scalar constant.

    Use ``values`` to specify a per-period dict, or ``value`` to specify a
    scalar constant that is the same for every period. Specifying both raises
    a ValueError at class definition time.

    Scalar FixedLines are accessed in formulas without ``[t]``::

        tax_rate = FixedLine(value=0.21)
        # formula: lambda li, t: li.revenue[t] * li.tax_rate

    Period-indexed FixedLines require ``[t]``::

        revenue = FixedLine(values={2024: 100_000, 2025: 110_000})
        # formula: lambda li, t: li.revenue[t] * 0.9

    Examples:
        >>> revenue = FixedLine(values={2024: 100000, 2025: 110000})
        >>> tax_rate = FixedLine(value=0.21, label="Tax Rate")
    """

    def __init__(
        self,
        values: dict[int, float] | None = None,
        label: str | None = None,
        tags: list[str] | None = None,
        value_format: Union[str, NumberFormatSpec, dict, None] = None,
        value: float | None = None,
    ):
        if value is not None and values is not None:
            raise ValueError(
                "FixedLine cannot have both 'value' (scalar) and 'values' (dict). "
                "Use one or the other."
            )
        super().__init__(label=label, tags=tags, value_format=value_format)
        self._scalar_value = value
        self.values = values or {}

    @property
    def is_scalar(self) -> bool:
        """True if this FixedLine was defined with a scalar value."""
        return self._scalar_value is not None

    def get_value(self, period: int) -> float | None:
        if self.is_scalar:
            return self._scalar_value
        return self.values.get(period)

    def __repr__(self):
        if self.is_scalar:
            if self.label:
                return f"FixedLine(value={self._scalar_value}, label={self.label!r})"
            return f"FixedLine(value={self._scalar_value})"
        if self.label:
            return f"FixedLine(values={self.values}, label={self.label!r})"
        return f"FixedLine(values={self.values})"
