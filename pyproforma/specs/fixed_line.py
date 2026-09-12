from typing import Union

from pyproforma.table import NumberFormatSpec

from .line_item import LineItem


class FixedLine(LineItem):
    """
    A period-indexed line item with hardcoded values per period.

    Values are supplied as a dict mapping periods to floats. For a scalar
    constant that applies across all periods use ``ScalarLine`` instead.

    A period may be explicitly mapped to ``None`` to mean "not applicable"
    (e.g. a line item that doesn't exist yet in an early period) — it
    resolves to ``None`` rather than raising, formats as blank in tables, and
    is skipped by tag sums. This is different from omitting the period
    entirely, which still raises ``ValueError`` when the model tries to
    calculate it.

    Examples:
        >>> revenue = FixedLine(values={2024: 100_000, 2025: 110_000})
        >>> # 2024 not applicable — the product launched in 2025
        >>> new_product_revenue = FixedLine(values={2024: None, 2025: 50_000})
    """

    def __init__(
        self,
        values: dict[int, float | None] | None = None,
        label: str | None = None,
        tags: list[str] | None = None,
        value_format: Union[str, NumberFormatSpec, dict, None] = None,
    ):
        super().__init__(label=label, tags=tags, value_format=value_format)
        self.values = values or {}

    def get_value(self, period: int) -> float | None:
        return self.values.get(period)

    def __repr__(self):
        if self.label:
            return f"FixedLine(values={self.values}, label={self.label!r})"
        return f"FixedLine(values={self.values})"
