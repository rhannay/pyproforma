"""
ModelNamespace — unified formula namespace combining line items and assumptions.

Formulas receive a single `li` object of this type, giving uniform access to
both line items (period-indexed) and assumptions (scalar):

    expenses = FormulaLine(lambda li, t: li.revenue[t] * li.tax_rate)

Line items are accessed with [t]; assumptions are accessed directly (no [t]).
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyproforma.assumption_values import AssumptionValues
    from pyproforma.line_items.line_item_values import LineItemValues


class ModelNamespace:
    """
    Unified namespace passed to formula functions.

    Wraps both LineItemValues and AssumptionValues into a single object.
    Attribute access checks line items first, then falls back to assumptions.

    - Line items   → returns a period-indexable object: li.revenue[t]
    - Assumptions  → returns the scalar value directly: li.tax_rate

    Examples:
        >>> # In a formula:
        >>> expenses = FormulaLine(lambda li, t: li.revenue[t] * li.tax_rate)
        >>> growth   = FormulaLine(lambda li, t: li.revenue[t-1] * (1 + li.growth_rate))
    """

    __slots__ = ("_li", "_av")

    def __init__(
        self,
        li: "LineItemValues",
        av: "AssumptionValues",
    ):
        object.__setattr__(self, "_li", li)
        object.__setattr__(self, "_av", av)

    def __getattr__(self, name: str):
        if name.startswith("_"):
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{name}'"
            )

        li = object.__getattribute__(self, "_li")
        av = object.__getattribute__(self, "_av")

        # Special case: tag namespace lives on li
        if name == "tag":
            return li.tag

        # Try line items first
        li_error = None
        try:
            return getattr(li, name)
        except AttributeError as e:
            li_error = e

        # Fall back to assumptions (scalar)
        try:
            return getattr(av, name)
        except AttributeError:
            pass

        # Not found in either — if li gave "is not registered", preserve it for
        # typo detection in the calculation engine (which checks for that message).
        if li_error is not None and "is not registered" in str(li_error):
            raise li_error

        raise AttributeError(
            f"'{name}' not found. "
            "Check that it is declared as a line item or assumption in the model."
        )

    def __repr__(self) -> str:
        return "ModelNamespace(...)"
