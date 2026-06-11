"""
ModelNamespace — unified formula namespace for line items and scalar constants.

Formulas receive a single `li` object of this type:

    expenses = FormulaLine(lambda li, t: li.revenue[t] * li.tax_rate)

Period-indexed line items are accessed with [t].
Scalar line items (FixedLine with value=, or scalar InputLine) are accessed directly.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyproforma.engine.line_item_values import LineItemValues


class _ScalarValue(float):
    """float subclass returned for scalar line items in formulas.

    Raises a clear TypeError if the caller tries li.rate[t] instead of li.rate.
    """

    def __new__(cls, value: float, name: str):
        inst = super().__new__(cls, value)
        inst._name = name
        return inst

    def __getitem__(self, key):
        raise TypeError(
            f"'{self._name}' is a scalar — use li.{self._name}, not li.{self._name}[{key}]"
        )


class ModelNamespace:
    """
    Unified namespace passed to formula functions.

    Wraps LineItemValues and a scalar dict into a single object.
    Scalars are returned directly; all other line items return a period-indexable object.

    Examples:
        >>> # Scalar: no [t] needed
        >>> expenses = FormulaLine(lambda li, t: li.revenue[t] * li.tax_rate)
        >>> # Period-indexed: [t] required
        >>> growth = FormulaLine(lambda li, t: li.revenue[t - 1] * (1 + li.rate[t]))
    """

    __slots__ = ("_li", "_scalars")

    def __init__(self, li: "LineItemValues", scalars: dict):
        object.__setattr__(self, "_li", li)
        object.__setattr__(self, "_scalars", scalars)

    def __getattr__(self, name: str):
        if name.startswith("_"):
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{name}'"
            )

        scalars = object.__getattribute__(self, "_scalars")
        li = object.__getattribute__(self, "_li")

        if name == "tag":
            return li.tag

        if name in scalars:
            value = scalars[name]
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                return _ScalarValue(value, name)
            return value

        li_error = None
        try:
            return getattr(li, name)
        except AttributeError as e:
            li_error = e

        if li_error is not None and "is not registered" in str(li_error):
            raise li_error

        raise AttributeError(
            f"'{name}' not found. "
            "Check that it is declared as a line item in the model."
        )

    def __repr__(self) -> str:
        return "ModelNamespace(...)"
