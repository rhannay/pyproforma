"""
FormulaLine class for calculated line items.

FormulaLine represents a line item whose values are calculated using a formula function.
Values can be overridden for specific periods using the values parameter.
"""

import dis
import inspect
from typing import TYPE_CHECKING, Callable, Union

from pyproforma.table import NumberFormatSpec

from .line_item import LineItem

if TYPE_CHECKING:
    from pyproforma.model_namespace import ModelNamespace


class FormulaLine(LineItem):
    """
    A line item with values calculated from a formula.

    FormulaLine is used to define line items where values are calculated using a
    formula function. The formula can reference other line items and assumptions
    in the model through a single unified namespace.

    The formula function receives two parameters:
    - li (ModelNamespace): Unified access to line items and assumptions.
      Line items are period-indexed: li.revenue[t], li.revenue[t-1]
      Assumptions are scalar: li.tax_rate, li.growth_rate
    - t (int): Current period being calculated

    Examples:
        >>> # Simple formula
        >>> profit = FormulaLine(formula=lambda li, t: li.revenue[t] - li.expenses[t])
        >>>
        >>> # Formula using an assumption
        >>> expenses = FormulaLine(formula=lambda li, t: li.revenue[t] * li.expense_ratio)
        >>>
        >>> # Formula with overrides
        >>> adjusted_profit = FormulaLine(
        ...     formula=lambda li, t: li.profit[t] * 0.9,
        ...     values={2024: 50000}  # Override for 2024
        ... )
        >>>
        >>> # In a model definition
        >>> class MyModel(ProformaModel):
        ...     expense_ratio = Assumption(value=0.6)
        ...     revenue = FixedLine(values={2024: 100, 2025: 110})
        ...     expenses = FormulaLine(formula=lambda li, t: li.revenue[t] * li.expense_ratio)
        ...     profit = FormulaLine(formula=lambda li, t: li.revenue[t] - li.expenses[t])

    Attributes:
        formula (Callable): Function that calculates the line item values.
        values (dict[int, float], optional): Dictionary of value overrides for specific periods.
        label (str, optional): Human-readable label for display purposes.
        tags (list[str]): List of tags for categorizing the line item.
    """

    def __init__(
        self,
        formula: "Callable[[ModelNamespace, int], float] | None" = None,
        values: dict[int, float] | None = None,
        label: str | None = None,
        tags: list[str] | None = None,
        value_format: Union[str, NumberFormatSpec, dict, None] = None,
    ):
        """
        Initialize a FormulaLine.

        Args:
            formula (Callable, optional): Function that calculates values. Must accept
                two parameters:
                - li (ModelNamespace): Unified access to line items and assumptions.
                  Use li.name[t] for line items, li.name for assumptions.
                - t (int): Current period being calculated
                The function should return a float value. Defaults to None.
            values (dict[int, float], optional): Dictionary of value overrides for
                specific periods. These override calculated values. Defaults to None.
            label (str, optional): Human-readable label. Defaults to None.
            tags (list[str], optional): List of tags for categorizing the line item.
                Defaults to None (empty list).
            value_format (str | NumberFormatSpec | dict, optional):
                Format specification for displaying values.
                Defaults to None (inherits default 'no_decimals').
        """
        super().__init__(label=label, tags=tags, value_format=value_format)
        self.formula = formula
        self.values = values or {}

    @property
    def precedents(self) -> list[str] | None:
        """Names of line items and assumptions referenced by this formula.

        Inspects the formula's bytecode for attribute lookups (LOAD_ATTR instructions),
        which correspond to accesses like li.revenue, li.tax_rate, etc. Returns names
        in order of first appearance, deduplicated.

        Returns None if no formula is set.

        Note: tag-based references (li.tag["revenue"]) appear as "tag" rather than
        the individual member names, since the tag name is a string literal, not an
        attribute. Named functions and lambdas are handled identically.

        Examples:
            >>> profit = FormulaLine(formula=lambda li, t: li.revenue[t] - li.expenses[t])
            >>> profit.precedents
            ['revenue', 'expenses']

            >>> tax = FormulaLine(formula=lambda li, t: li.revenue[t] * li.tax_rate)
            >>> tax.precedents
            ['revenue', 'tax_rate']
        """
        if self.formula is None:
            return None
        seen = set()
        result = []
        for instr in dis.get_instructions(self.formula):
            if instr.opname == "LOAD_ATTR" and instr.argval not in seen:
                seen.add(instr.argval)
                result.append(instr.argval)
        return result

    @property
    def formula_source(self) -> str | None:
        """Source code of the formula function.

        For named functions, returns the full function definition. For lambdas,
        extracts just the lambda expression from its enclosing line. Returns None
        if no formula is set or if source is unavailable (e.g. defined in a REPL).

        Examples:
            >>> expenses = FormulaLine(formula=lambda li, t: li.revenue[t] * 0.6)
            >>> expenses.formula_source
            'lambda li, t: li.revenue[t] * 0.6'

            >>> def my_formula(li, t):
            ...     return li.revenue[t] * 0.6
            >>> expenses = FormulaLine(formula=my_formula)
            >>> expenses.formula_source
            'def my_formula(li, t):\\n    return li.revenue[t] * 0.6'
        """
        if self.formula is None:
            return None
        try:
            source = inspect.getsource(self.formula).strip()
        except OSError:
            return None

        if self.formula.__name__ == "<lambda>":
            # Extract just the lambda expression from its enclosing line
            idx = source.find("lambda")
            if idx != -1:
                source = source[idx:]
                # Strip trailing ), comma, quote — common line endings after the lambda arg
                source = source.rstrip(" ,)")
        return source

    def eval(
        self,
        ns: "ModelNamespace",
        t: int,
    ) -> float:
        """
        Evaluate the formula for a specific period.

        Args:
            ns (ModelNamespace): Unified namespace giving access to both line
                items (period-indexed) and assumptions (scalar).
            t (int): Current period being calculated

        Returns:
            float: Calculated value for the period

        Raises:
            ValueError: If formula is None or returns invalid type
        """
        if self.formula is None:
            raise ValueError(f"No formula defined for '{self.name}'")
        return self.formula(ns, t)

    def get_value(self, period: int) -> float | None:
        """
        Get the value for a specific period.

        If the period has an override value, return that. Otherwise,
        calculate the value using the formula.

        Args:
            period (int): The period (year) to get the value for.

        Returns:
            float | None: The value for the specified period.
        """
        # Check for override first
        if period in self.values:
            return self.values[period]

        # Scaffolding: Actual implementation would calculate from formula
        return None

    def __repr__(self):
        """Return a string representation of the FormulaLine."""
        parts = [f"formula={self.formula!r}"]
        if self.values:
            parts.append(f"values={self.values}")
        if self.label:
            parts.append(f"label={self.label!r}")
        return f"FormulaLine({', '.join(parts)})"
