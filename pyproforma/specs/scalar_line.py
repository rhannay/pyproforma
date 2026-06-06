from typing import Union

from pyproforma.table import NumberFormatSpec

from .line_item import LineItem


class ScalarLine(LineItem):
    """
    A scalar constant line item — same value for all periods.

    Accessed in formulas without ``[t]``::

        tax_rate = ScalarLine(value=0.21)
        # formula: lambda li, t: li.revenue[t] * li.tax_rate

    Unlike FixedLine, ScalarLine has no period-indexed values and does not
    appear in period tables or charts.
    """

    _is_scalar = True

    def __init__(
        self,
        value: float,
        label: str | None = None,
        value_format: Union[str, NumberFormatSpec, dict, None] = None,
    ):
        super().__init__(label=label, tags=[], value_format=value_format)
        self.value = value

    def get_value(self, period: int) -> float:
        return self.value

    def __repr__(self):
        if self.label:
            return f"ScalarLine(value={self.value}, label={self.label!r})"
        return f"ScalarLine(value={self.value})"
