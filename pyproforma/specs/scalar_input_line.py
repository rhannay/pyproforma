from typing import Union

from pyproforma.table import NumberFormatSpec

from .line_item import LineItem

_MISSING = object()


class ScalarInputLine(LineItem):
    """
    A scalar input — a single float supplied at model instantiation.

    Accessed in formulas without ``[t]``::

        discount_rate = ScalarInputLine(default=0.08)
        # formula: lambda li, t: li.cash_flow[t] / (1 + li.discount_rate) ** t

    Unlike InputLine, ScalarInputLine is not period-indexed. It has no
    period table or chart.
    """

    _is_scalar = True

    def __init__(
        self,
        default: float | None = _MISSING,
        label: str | None = None,
        value_format: Union[str, NumberFormatSpec, dict, None] = None,
    ):
        super().__init__(label=label, tags=[], value_format=value_format)
        self._default = default

    @property
    def has_default(self) -> bool:
        return self._default is not _MISSING

    @property
    def default(self) -> float:
        if self._default is _MISSING:
            raise AttributeError(f"ScalarInputLine '{self.name}' has no default value.")
        return self._default

    def get_value(self, period: int) -> float:
        raise NotImplementedError("ScalarInputLine values are resolved at model instantiation.")

    def __repr__(self):
        if self.has_default and self.label:
            return f"ScalarInputLine(default={self._default}, label={self.label!r})"
        if self.has_default:
            return f"ScalarInputLine(default={self._default})"
        if self.label:
            return f"ScalarInputLine(label={self.label!r})"
        return "ScalarInputLine()"
