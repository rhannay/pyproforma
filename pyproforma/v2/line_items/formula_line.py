"""
FormulaLine class for calculated line items.

FormulaLine represents a line item whose values are calculated using a formula function.
Values can be overridden for specific periods using the values parameter.
"""

from typing import TYPE_CHECKING, Callable, Union

from pyproforma.table import NumberFormatSpec

from .line_item import LineItem

if TYPE_CHECKING:
    from pyproforma.v2.assumption_values import AssumptionValues

    from .line_item_values import LineItemValues


class FormulaLine(LineItem):
    """
    A line item with values calculated from a formula.

    FormulaLine is used to define line items where values are calculated using a
    formula function. The formula can reference other line items in the model.
    Specific period values can be overridden using the values parameter.

    The formula function receives three parameters:
    - a (AssumptionValues): Access to assumption values (e.g., a.growth_rate)
    - li (LineItemValues): Access to other line item values (e.g., li.revenue[t])
    - t (int): Current period being calculated

    Examples:
        >>> # Simple formula
        >>> profit = FormulaLine(formula=lambda a, li, t: li.revenue[t] - li.expenses[t])
        >>>
        >>> # Formula using assumptions
        >>> expenses = FormulaLine(formula=lambda a, li, t: li.revenue[t] * a.expense_ratio)
        >>>
        >>> # Formula with overrides
        >>> adjusted_profit = FormulaLine(
        ...     formula=lambda a, li, t: li.profit[t] * 0.9,
        ...     values={2024: 50000}  # Override for 2024
        ... )
        >>>
        >>> # In a model definition
        >>> class MyModel(ProformaModel):
        ...     revenue = FixedLine(values={2024: 100, 2025: 110})
        ...     expenses = FormulaLine(formula=lambda a, li, t: li.revenue[t] * 0.6)
        ...     profit = FormulaLine(formula=lambda a, li, t: li.revenue[t] - li.expenses[t])

    Attributes:
        formula (Callable): Function that calculates the line item values.
        values (dict[int, float], optional): Dictionary of value overrides for specific periods.
        label (str, optional): Human-readable label for display purposes.
        tags (list[str]): List of tags for categorizing the line item.
    """

    def __init__(
        self,
        formula: "Callable[[AssumptionValues, LineItemValues, int], float] | None" = None,
        values: dict[int, float] | None = None,
        label: str | None = None,
        tags: list[str] | None = None,
        value_format: Union[str, NumberFormatSpec, dict, None] = None,
    ):
        """
        Initialize a FormulaLine.

        Args:
            formula (Callable, optional): Function that calculates values. Must accept
                three parameters:
                - a (AssumptionValues): Access to assumption values
                - li (LineItemValues): Access to line item values
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

    def eval(
        self,
        a: "AssumptionValues",
        li: "LineItemValues",
        t: int,
    ) -> float:
        """
        Evaluate the formula for a specific period.

        This method provides explicit documentation of the three parameters
        that formulas receive, making it clear what the formula function should expect.

        Args:
            a (AssumptionValues): Container for accessing assumption values
            li (LineItemValues): Container for accessing other line item values
            t (int): Current period being calculated

        Returns:
            float: Calculated value for the period

        Raises:
            ValueError: If formula is None or returns invalid type
        """
        if self.formula is None:
            raise ValueError(f"No formula defined for '{self.name}'")
        return self.formula(a, li, t)

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
