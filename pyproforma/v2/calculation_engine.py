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

    # Import here to avoid circular imports
    from .fixed_line import FixedLine
    from .formula_line import FormulaLine

    # Initialize line item values with registered names for validation
    li = LineItemValues(periods=periods, names=model.line_item_names)

    # Separate fixed and formula line items
    fixed_items = []
    formula_items = []
    
    for name in model.line_item_names:
        line_item = getattr(model.__class__, name, None)
        if isinstance(line_item, FixedLine):
            fixed_items.append(name)
        elif isinstance(line_item, FormulaLine):
            formula_items.append(name)

    # Calculate values for each period
    for period in periods:
        # First, calculate all fixed line items (they don't depend on other line items)
        for name in fixed_items:
            line_item = getattr(model.__class__, name)
            value = _calculate_single_line_item(line_item, av, li, period)
            li.set(name, period, value)
        
        # Then calculate formula items with dependency resolution
        remaining = formula_items.copy()
        max_iterations = len(formula_items) + 1
        iteration = 0
        
        while remaining and iteration < max_iterations:
            iteration += 1
            still_pending = []
            
            for name in remaining:
                line_item = getattr(model.__class__, name)
                try:
                    value = _calculate_single_line_item(line_item, av, li, period)
                    li.set(name, period, value)
                except AttributeError as e:
                    # AttributeError means accessing unregistered line item (typo)
                    # LineItemValues now raises helpful error with available names
                    error_msg = str(e)
                    if "is not registered" in error_msg:
                        # This is a typo - raise immediately with helpful message
                        raise ValueError(
                            f"Error in formula for '{line_item.name}': {e}"
                        ) from e
                    # Otherwise, it's some other AttributeError - retry
                    still_pending.append(name)
                except KeyError as e:
                    # KeyError could mean:
                    # 1. Dependency not yet calculated for current period (retry)
                    # 2. Accessing a period not in the model (fatal error)
                    # Check if the error is about the current period
                    error_msg = str(e)
                    if f"Period {period}" in error_msg:
                        # Dependency not yet calculated for current period - retry
                        still_pending.append(name)
                    else:
                        # Accessing a period outside the model - wrap in ValueError  
                        raise ValueError(
                            f"Error evaluating formula for '{line_item.name}' in period {period}: {e}"
                        ) from e
            
            # If we made no progress, we have a circular reference
            if len(still_pending) == len(remaining):
                raise ValueError(
                    f"Circular reference detected for period {period}. "
                    f"Cannot calculate: {', '.join(still_pending)}"
                )
            
            remaining = still_pending

    return li


def _calculate_single_line_item(
    line_item: Any,
    av: "AssumptionValues",
    li: "LineItemValues",
    period: int,
) -> float:
    """
    Calculate the value of a single line item for a specific period.

    This is a pure function that computes and returns a value without modifying
    the LineItemValues container. The caller is responsible for storing the result.

    Args:
        line_item: The line item definition (FixedLine or FormulaLine).
            Must have a .name attribute set by __set_name__.
        av (AssumptionValues): Assumption values.
        li (LineItemValues): Line item values container (read-only access).
        period (int): The period to calculate for.

    Returns:
        float: The calculated value.

    Raises:
        ValueError: If calculation fails.
        AttributeError: If a dependency is not yet calculated.
        KeyError: If accessing a period not yet calculated.
    """
    # Import here to avoid circular imports
    from .fixed_line import FixedLine
    from .formula_line import FormulaLine

    # Handle FixedLine
    if isinstance(line_item, FixedLine):
        value = line_item.get_value(period)
        if value is None:
            raise ValueError(
                f"No value defined for '{line_item.name}' in period {period}"
            )
        return value

    # Handle FormulaLine
    if isinstance(line_item, FormulaLine):
        # Check for override value first
        if period in line_item.values:
            return line_item.values[period]

        # Evaluate the formula
        if line_item.formula is None:
            raise ValueError(f"No formula defined for '{line_item.name}'")

        # Call formula with a, li, and t parameters
        try:
            value = line_item.formula(av, li, period)
        except (AttributeError, KeyError):
            # Re-raise these - indicate missing dependencies or periods
            # The caller will decide whether to retry or raise ValueError
            raise
        except Exception as e:
            raise ValueError(
                f"Error evaluating formula for '{line_item.name}' in period {period}: {e}"
            ) from e

        # Validate the result type
        if not isinstance(value, (int, float)):
            raise ValueError(
                f"Formula for '{line_item.name}' returned invalid type: {type(value)}"
            )

        return float(value)

    raise ValueError(f"Unknown line item type for '{line_item.name}'")
