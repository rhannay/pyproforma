"""
ModelNamespace — unified formula namespace for line items and scalar constants.

Formulas receive a single `li` object of this type:

    expenses = FormulaLine(lambda li, t: li.revenue[t] * li.tax_rate)

Period-indexed line items are accessed with [t].
Scalar line items (FixedLine with value=, or scalar InputLine) are accessed directly.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyproforma.line_items.line_item_values import LineItemValues


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
            return scalars[name]

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
