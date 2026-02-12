"""
Calculation engine for v2 ProformaModel.

This module contains the logic for calculating line item values from formulas,
handling dependencies, and resolving values across periods.
"""

from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from .assumption_values import AssumptionValues
    from .line_item_values import LineItemValues

class CalculationEngine:
    """
    Engine for calculating line item values from formulas.

    The CalculationEngine processes formulas in dependency order, evaluates them
    for each period, and stores the results in LineItemValues.

    Formulas receive three parameters:
    - a (AssumptionValues): Access assumptions via a.tax_rate, a.growth_rate, etc.
    - li (LineItemValues): Access line items via li.revenue[t], li.revenue[t-1], etc.
    - t (int): Current period being calculated

    Attributes:
        model: The ProformaModel instance being calculated.
        av (AssumptionValues): Assumption values for the model.
        li (LineItemValues): Line item values being calculated.
        periods (list[int]): List of periods to calculate.
    """

    def __init__(
        self,
        model: Any,
        av: "AssumptionValues",
        li: "LineItemValues",
        periods: list[int],
    ):
        """
        Initialize the CalculationEngine.

        Args:
            model: The ProformaModel instance.
            av (AssumptionValues): Assumption values.
            li (LineItemValues): Line item values (initially empty).
            periods (list[int]): List of periods to calculate.
        """
        self.model = model
        self.av = av
        self.li = li
        self.periods = periods

    def calculate(self) -> None:
        """
        Calculate all line item values for all periods.

        This method processes each period in order, calculating all line items
        for that period before moving to the next. This allows for time-offset
        references (e.g., li.revenue[t-1]) to work correctly.
        """
        # Get all line item names from the model class
        line_item_names = getattr(self.model.__class__, "_line_item_names", [])

        # Calculate values for each period
        for period in self.periods:
            # Calculate each line item for this period
            for name in line_item_names:
                self._calculate_line_item(name, period)

    def _calculate_line_item(self, name: str, period: int) -> float:
        """
        Calculate the value of a line item for a specific period.

        Args:
            name (str): The name of the line item.
            period (int): The period to calculate for.

        Returns:
            float: The calculated value.

        Raises:
            ValueError: If the line item is not found or calculation fails.
        """
        # Get the line item definition from the model class
        line_item = getattr(self.model.__class__, name, None)
        if line_item is None:
            raise ValueError(f"Line item '{name}' not found in model")

        # Import here to avoid circular imports
        from .fixed_line import FixedLine
        from .formula_line import FormulaLine

        # Handle FixedLine
        if isinstance(line_item, FixedLine):
            value = line_item.get_value(period)
            if value is None:
                raise ValueError(f"No value defined for '{name}' in period {period}")
            self.li.set(name, period, value)
            return value

        # Handle FormulaLine
        if isinstance(line_item, FormulaLine):
            # Check for override value first
            if period in line_item.values:
                value = line_item.values[period]
                self.li.set(name, period, value)
                return value

            # Evaluate the formula
            if line_item.formula is None:
                raise ValueError(f"No formula defined for '{name}'")

            # Call formula with a, li, and t parameters
            try:
                value = line_item.formula(self.av, self.li, period)
            except Exception as e:
                raise ValueError(
                    f"Error evaluating formula for '{name}' in period {period}: {e}"
                ) from e

            # Handle the result
            if isinstance(value, (int, float)):
                self.li.set(name, period, float(value))
                return float(value)
            else:
                raise ValueError(
                    f"Formula for '{name}' returned invalid type: {type(value)}"
                )

        raise ValueError(f"Unknown line item type for '{name}'")
