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
        >>> model.revenue.stat.sum()
        2100000
        >>> model.revenue.stat.sum(start=2024, end=2025)
        1100000
        >>> model.revenue.stat.formatted_sum()
        '$2,100,000'
        >>> model.revenue.stat.cagr()
        0.1
        >>> model.dscr.stat.min()
        1.25
    """

    def __init__(self, result: "LineItemResult"):
        self._result = result

    def _period_range(self, start=None, end=None) -> list:
        periods = self._result._model.periods
        if start is not None and start not in periods:
            raise ValueError(f"start {start!r} is not in model periods {periods}")
        if end is not None and end not in periods:
            raise ValueError(f"end {end!r} is not in model periods {periods}")
        s = periods.index(start) if start is not None else 0
        e = periods.index(end) + 1 if end is not None else len(periods)
        return periods[s:e]

    def _vals(self, start=None, end=None) -> list[float]:
        periods = self._period_range(start, end)
        return [self._result[p] for p in periods if self._result[p] is not None]

    def _fmt(self, v, value_format=None) -> str:
        if v is None:
            return ""
        fmt = value_format or self._result.value_format
        result = format_value(v, fmt)
        return result if isinstance(result, str) else str(result)

    # ------------------------------------------------------------------
    # Raw aggregations
    # ------------------------------------------------------------------

    def min(self, start=None, end=None) -> float | None:
        """Minimum value across all periods (or a start/end range)."""
        vals = self._vals(start, end)
        return min(vals) if vals else None

    def max(self, start=None, end=None) -> float | None:
        """Maximum value across all periods (or a start/end range)."""
        vals = self._vals(start, end)
        return max(vals) if vals else None

    def first(self, start=None, end=None) -> float | None:
        """Value for the first period (or the first period of a start/end range)."""
        periods = self._period_range(start, end)
        return self._result[periods[0]] if periods else None

    def latest(self, start=None, end=None) -> float | None:
        """Value for the last period (or the last period of a start/end range)."""
        periods = self._period_range(start, end)
        return self._result[periods[-1]] if periods else None

    def sum(self, start=None, end=None) -> float | None:
        """Sum of values across all periods (or a start/end range)."""
        vals = self._vals(start, end)
        return builtins_sum(vals) if vals else None

    def avg(self, start=None, end=None) -> float | None:
        """Average (mean) value across all periods (or a start/end range)."""
        vals = self._vals(start, end)
        return builtins_sum(vals) / len(vals) if vals else None

    def cagr(self, start=None, end=None) -> float | None:
        """
        Compound annual growth rate from first to last period (or a start/end range).

        Returns None if fewer than 2 periods or if the first value is <= 0.
        """
        periods = self._period_range(start, end)
        if len(periods) < 2:
            return None
        first = self._result[periods[0]]
        latest = self._result[periods[-1]]
        if not first or first <= 0 or latest is None:
            return None
        n = len(periods) - 1
        return (latest / first) ** (1 / n) - 1

    # ------------------------------------------------------------------
    # Formatted aggregations
    # ------------------------------------------------------------------

    def formatted_min(self, value_format=None, start=None, end=None) -> str:
        return self._fmt(self.min(start, end), value_format)

    def formatted_max(self, value_format=None, start=None, end=None) -> str:
        return self._fmt(self.max(start, end), value_format)

    def formatted_first(self, value_format=None, start=None, end=None) -> str:
        return self._fmt(self.first(start, end), value_format)

    def formatted_latest(self, value_format=None, start=None, end=None) -> str:
        return self._fmt(self.latest(start, end), value_format)

    def formatted_sum(self, value_format=None, start=None, end=None) -> str:
        return self._fmt(self.sum(start, end), value_format)

    def formatted_avg(self, value_format=None, start=None, end=None) -> str:
        return self._fmt(self.avg(start, end), value_format)

    def formatted_cagr(self, value_format=None, start=None, end=None) -> str:
        return self._fmt(self.cagr(start, end), value_format)


# avoid shadowing the built-in inside the class methods
builtins_sum = sum
