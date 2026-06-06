"""
Calculation engine for ProformaModel.

Calculates line item values from formulas, handling dependencies and resolving
values across periods.
"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .line_item_values import LineItemValues


def calculate_line_items(
    model: Any,
    scalars: dict,
    periods: list[int],
) -> "LineItemValues":
    """
    Calculate all line item values for the given model.

    Args:
        model: The ProformaModel instance containing line item definitions.
        scalars: Dict of scalar line item values (FixedLine(value=) or scalar InputLine).
        periods: List of periods to calculate.

    Returns:
        LineItemValues: Populated container with all calculated values.
    """
    from pyproforma.specs.debt_line import DebtBase
    from pyproforma.specs.fixed_line import FixedLine
    from pyproforma.specs.formula_line import FormulaLine
    from pyproforma.specs.input_line import InputLine
    from .line_item_values import LineItemValues
    from .model_namespace import ModelNamespace

    # scalar_names are already resolved into the scalars dict — skip them here
    li = LineItemValues(periods=periods, names=model.line_item_names, model=model)

    fixed_items = []
    formula_items = []

    for name in model.line_item_names:
        line_item = getattr(model.__class__, name, None)
        if isinstance(line_item, (FixedLine, InputLine)):
            fixed_items.append(name)
        elif isinstance(line_item, (FormulaLine, DebtBase)):
            formula_items.append(name)

    for period in periods:
        ns = ModelNamespace(li, scalars)

        for name in fixed_items:
            line_item = getattr(model.__class__, name)
            value = _calculate_single_line_item(line_item, ns, period, model)
            li.set(name, period, value)

        remaining = formula_items.copy()
        max_iterations = len(formula_items) + 1
        iteration = 0

        while remaining and iteration < max_iterations:
            iteration += 1
            still_pending = []

            for name in remaining:
                line_item = getattr(model.__class__, name)
                try:
                    value = _calculate_single_line_item(line_item, ns, period, model)
                    li.set(name, period, value)
                except AttributeError as e:
                    error_msg = str(e)
                    if "is not registered" in error_msg:
                        raise ValueError(
                            f"Error in formula for '{line_item.name}': {e}"
                        ) from e
                    still_pending.append(name)
                except KeyError as e:
                    error_msg = str(e)
                    if f"Period {period}" in error_msg:
                        still_pending.append(name)
                    else:
                        raise ValueError(
                            f"Error evaluating formula for '{line_item.name}' in period {period}: {e}"
                        ) from e

            if len(still_pending) == len(remaining):
                raise ValueError(
                    f"Circular reference detected for period {period}. "
                    f"Cannot calculate: {', '.join(still_pending)}"
                )

            remaining = still_pending

    return li


def _calculate_single_line_item(
    line_item: Any,
    ns: Any,
    period: int,
    model: Any = None,
) -> Any:
    from pyproforma.specs.debt_line import DebtBase
    from pyproforma.specs.fixed_line import FixedLine
    from pyproforma.specs.formula_line import FormulaLine
    from pyproforma.specs.input_line import InputLine

    if isinstance(line_item, InputLine):
        input_values = getattr(model, "_input_line_values", {})
        period_values = input_values.get(line_item.name, {})
        value = period_values.get(period)
        if value is None:
            raise ValueError(
                f"No input value for '{line_item.name}' in period {period}"
            )
        return value

    if isinstance(line_item, FixedLine):
        value = line_item.get_value(period)
        if value is None:
            raise ValueError(
                f"No value defined for '{line_item.name}' in period {period}"
            )
        return value

    if isinstance(line_item, FormulaLine):
        if period in line_item.values:
            return line_item.values[period]
        try:
            value = line_item.eval(ns, period)
        except (AttributeError, KeyError):
            raise
        except Exception as e:
            raise ValueError(
                f"Error evaluating formula for '{line_item.name}' in period {period}: {e}"
            ) from e
        if value is None:
            raise ValueError(
                f"Formula for '{line_item.name}' returned None"
            )
        return value

    if isinstance(line_item, DebtBase):
        debt_calculators = getattr(model, "_debt_calculators", {})
        calculator = debt_calculators.get(id(line_item.config))
        if calculator is None:
            raise ValueError(
                f"No calculator found for debt line '{line_item.name}'. "
                f"Ensure the model was instantiated via ProformaModel.__init__."
            )
        try:
            value = line_item.eval(ns, period, calculator)
        except (AttributeError, KeyError):
            raise
        except Exception as e:
            raise ValueError(
                f"Error evaluating debt line for '{line_item.name}' in period {period}: {e}"
            ) from e
        if not isinstance(value, (int, float)):
            raise ValueError(
                f"Debt line '{line_item.name}' returned invalid type: {type(value)}"
            )
        return float(value)

    raise ValueError(f"Unknown line item type for '{line_item.name}'")
