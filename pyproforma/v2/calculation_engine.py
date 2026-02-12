"""
Calculation engine for v2 ProformaModel.

This module contains the logic for calculating line item values from formulas,
handling dependencies, and resolving values across periods.
"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .assumption_values import AssumptionValues
    from .line_item_values import LineItemValues


def calculate_line_items(
    model: Any,
    av: "AssumptionValues",
    periods: list[int],
) -> "LineItemValues":
    """
    Calculate all line item values for the given model.

    This function processes formulas in dependency order, evaluates them for
    each period, and returns a populated LineItemValues container.

    Formulas receive three parameters:
    - a (AssumptionValues): Access assumptions via a.tax_rate, a.growth_rate, etc.
    - li (LineItemValues): Access line items via li.revenue[t], li.revenue[t-1], etc.
    - t (int): Current period being calculated

    This function processes each period in order, calculating all line items
    for that period before moving to the next. This allows for time-offset
    references (e.g., li.revenue[t-1]) to work correctly.

    Args:
        model: The ProformaModel instance containing line item definitions.
        av (AssumptionValues): Assumption values for the model.
        periods (list[int]): List of periods to calculate.

    Returns:
        LineItemValues: Populated container with all calculated values.

    Raises:
        ValueError: If line items are not found or calculation fails.
    """
    # Import here to avoid circular imports
    from .line_item_values import LineItemValues

    # Initialize empty line item values
    li = LineItemValues(periods=periods)

    # Get all line item names from the model class
    line_item_names = getattr(model.__class__, "_line_item_names", [])

    # Calculate values for each period
    for period in periods:
        # Calculate each line item for this period
        for name in line_item_names:
            _calculate_single_line_item(model, av, li, name, period)

    return li


def _calculate_single_line_item(
    model: Any,
    av: "AssumptionValues",
    li: "LineItemValues",
    name: str,
    period: int,
) -> float:
    """
    Calculate the value of a single line item for a specific period.

    Args:
        model: The ProformaModel instance.
        av (AssumptionValues): Assumption values.
        li (LineItemValues): Line item values container.
        name (str): The name of the line item.
        period (int): The period to calculate for.

    Returns:
        float: The calculated value.

    Raises:
        ValueError: If the line item is not found or calculation fails.
    """
    # Get the line item definition from the model class
    line_item = getattr(model.__class__, name, None)
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
        li.set(name, period, value)
        return value

    # Handle FormulaLine
    if isinstance(line_item, FormulaLine):
        # Check for override value first
        if period in line_item.values:
            value = line_item.values[period]
            li.set(name, period, value)
            return value

        # Evaluate the formula
        if line_item.formula is None:
            raise ValueError(f"No formula defined for '{name}'")

        # Call formula with a, li, and t parameters
        try:
            value = line_item.formula(av, li, period)
        except Exception as e:
            raise ValueError(
                f"Error evaluating formula for '{name}' in period {period}: {e}"
            ) from e

        # Handle the result
        if isinstance(value, (int, float)):
            li.set(name, period, float(value))
            return float(value)
        else:
            raise ValueError(
                f"Formula for '{name}' returned invalid type: {type(value)}"
            )

    raise ValueError(f"Unknown line item type for '{name}'")
