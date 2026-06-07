"""LineItemStat — aggregation namespace for a LineItemResult."""

from typing import TYPE_CHECKING

from pyproforma.table import format_value

if TYPE_CHECKING:
    from pyproforma.results.line_item_result import LineItemResult


class LineItemStat:
    """
    Aggregation namespace accessed via ``model.revenue.stat``.

    Provides raw and formatted summary statistics across all periods.
    CAGR is undefined (returns None) when the first period value is zero
    or negative, or when there are fewer than two periods.

    Examples:
        >>> model.revenue.stat.sum
        2100000
        >>> model.revenue.stat.formatted_sum()
        '$2,100,000'
        >>> model.revenue.stat.cagr
        0.1
        >>> model.dscr.stat.min
        1.25
    """

    def __init__(self, result: "LineItemResult"):
        self._result = result

    def _vals(self) -> list[float]:
        return [v for v in self._result.values.values() if v is not None]

    def _fmt(self, v, value_format=None) -> str:
        if v is None:
            return ""
        fmt = value_format or self._result.value_format
        result = format_value(v, fmt)
        return result if isinstance(result, str) else str(result)

    # ------------------------------------------------------------------
    # Raw aggregations
    # ------------------------------------------------------------------

    def min(self) -> float | None:
        """Minimum value across all periods."""
        vals = self._vals()
        return min(vals) if vals else None

    def max(self) -> float | None:
        """Maximum value across all periods."""
        vals = self._vals()
        return max(vals) if vals else None

    def first(self) -> float | None:
        """Value for the first period."""
        periods = self._result._model.periods
        return self._result[periods[0]] if periods else None

    def latest(self) -> float | None:
        """Value for the last period."""
        periods = self._result._model.periods
        return self._result[periods[-1]] if periods else None

    def sum(self) -> float | None:
        """Sum of values across all periods."""
        vals = self._vals()
        return builtins_sum(vals) if vals else None

    def avg(self) -> float | None:
        """Average (mean) value across all periods."""
        vals = self._vals()
        return builtins_sum(vals) / len(vals) if vals else None

    def cagr(self) -> float | None:
        """
        Compound annual growth rate from first to last period.

        Returns None if fewer than 2 periods or if the first value is <= 0.
        """
        periods = self._result._model.periods
        if len(periods) < 2:
            return None
        first = self.first()
        latest = self.latest()
        if not first or first <= 0 or latest is None:
            return None
        n = len(periods) - 1
        return (latest / first) ** (1 / n) - 1

    # ------------------------------------------------------------------
    # Formatted aggregations
    # ------------------------------------------------------------------

    def formatted_min(self, value_format=None) -> str:
        return self._fmt(self.min(), value_format)

    def formatted_max(self, value_format=None) -> str:
        return self._fmt(self.max(), value_format)

    def formatted_first(self, value_format=None) -> str:
        return self._fmt(self.first(), value_format)

    def formatted_latest(self, value_format=None) -> str:
        return self._fmt(self.latest(), value_format)

    def formatted_sum(self, value_format=None) -> str:
        return self._fmt(self.sum(), value_format)

    def formatted_avg(self, value_format=None) -> str:
        return self._fmt(self.avg(), value_format)

    def formatted_cagr(self, value_format=None) -> str:
        return self._fmt(self.cagr(), value_format)


# avoid shadowing the built-in inside the class methods
builtins_sum = sum
