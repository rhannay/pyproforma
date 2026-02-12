"""
Calculation engine for v2 ProformaModel.

This module contains the logic for calculating line item values from formulas,
handling dependencies, and resolving values across periods.
"""

import ast
import inspect
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from .assumption_values import AssumptionValues
    from .line_item_values import LineItemValues


class TimeSeriesValue:
    """
    Wrapper for line item values that supports time-offset subscript access.

    This class allows formulas to reference previous period values using
    subscript notation, e.g., revenue[-1] for the previous period's revenue.

    Attributes:
        _name (str): The name of the line item.
        _li (LineItemValues): Line item values container.
        _period (int): Current period being calculated.
        _value (float): The value for the current period.
    """

    def __init__(
        self, name: str, li: "LineItemValues", period: int, value: float
    ):
        """
        Initialize TimeSeriesValue.

        Args:
            name (str): The name of the line item.
            li (LineItemValues): Line item values container.
            period (int): Current period.
            value (float): The value for the current period.
        """
        self._name = name
        self._li = li
        self._period = period
        self._value = value

    def __getitem__(self, offset: int) -> float:
        """
        Get value with time offset using subscript notation.

        Args:
            offset (int): Time offset (must be negative for lookback).

        Returns:
            float: The value at the offset period.

        Raises:
            ValueError: If offset is not negative or period not found.
        """
        if offset >= 0:
            raise ValueError(
                f"Only negative time offsets are allowed, got [{offset}]. "
                "Future references are not permitted."
            )

        target_period = self._period + offset
        value = self._li.get(self._name, target_period)

        if value is None:
            raise ValueError(
                f"No value found for '{self._name}' in period {target_period}"
            )

        return value

    def __float__(self) -> float:
        """Convert to float (returns current period value)."""
        return float(self._value)

    def __int__(self) -> int:
        """Convert to int (returns current period value)."""
        return int(self._value)

    def __add__(self, other):
        """Add operation."""
        return self._value + other

    def __radd__(self, other):
        """Reverse add operation."""
        return other + self._value

    def __sub__(self, other):
        """Subtract operation."""
        return self._value - other

    def __rsub__(self, other):
        """Reverse subtract operation."""
        return other - self._value

    def __mul__(self, other):
        """Multiply operation."""
        return self._value * other

    def __rmul__(self, other):
        """Reverse multiply operation."""
        return other * self._value

    def __truediv__(self, other):
        """Divide operation."""
        return self._value / other

    def __rtruediv__(self, other):
        """Reverse divide operation."""
        return other / self._value

    def __repr__(self):
        """String representation."""
        return f"TimeSeriesValue(name={self._name!r}, period={self._period}, value={self._value})"


class FormulaContext:
    """
    Context object passed to formulas during evaluation.

    This class provides access to assumption values, line item values,
    and supports time-offset lookback.

    Attributes:
        av: Assumption values.
        li: Line item values.
        period: Current period being calculated.
    """

    def __init__(self, av: "AssumptionValues", li: "LineItemValues", period: int):
        """
        Initialize FormulaContext.

        Args:
            av: Assumption values.
            li: Line item values.
            period: Current period.
        """
        self._av = av
        self._li = li
        self._period = period

    def __getattr__(self, name: str):
        """
        Get a value by name, checking assumptions first, then line items.

        For assumptions, returns the scalar value.
        For line items, returns a TimeSeriesValue that supports subscript access.

        Args:
            name (str): The name to look up.

        Returns:
            float | TimeSeriesValue: The value or time series wrapper.

        Raises:
            AttributeError: If the name is not found.
        """
        if name.startswith("_"):
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

        # Check assumptions first (return scalar value)
        assumption_value = self._av.get(name)
        if assumption_value is not None:
            return assumption_value

        # Check line items (return TimeSeriesValue for subscript support)
        line_value = self._li.get(name, self._period)
        if line_value is not None:
            return TimeSeriesValue(name, self._li, self._period, line_value)

        raise AttributeError(
            f"'{name}' not found in assumptions or line items for period {self._period}"
        )


class CalculationEngine:
    """
    Engine for calculating line item values from formulas.

    The CalculationEngine processes formulas in dependency order, evaluates them
    for each period, and stores the results in LineItemValues.

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
        self._current_period = None

    def calculate(self) -> None:
        """
        Calculate all line item values for all periods.

        This method processes each period in order, calculating all line items
        for that period before moving to the next. This allows for time-offset
        references (e.g., revenue[-1]) to work correctly.
        """
        # Get all line item names from the model class
        line_item_names = getattr(self.model.__class__, "_line_item_names", [])

        # Calculate values for each period
        for period in self.periods:
            self._current_period = period

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
                raise ValueError(
                    f"No value defined for '{name}' in period {period}"
                )
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

            # Create formula context
            context = FormulaContext(self.av, self.li, period)

            # Inject context into formula's globals
            formula_func = self._inject_context_into_formula(
                line_item.formula, context
            )

            # Evaluate the formula
            try:
                value = formula_func()
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

    def _inject_context_into_formula(
        self, formula: Callable, context: FormulaContext
    ) -> Callable:
        """
        Inject FormulaContext into a formula's globals.

        This creates a new function with the same code but updated globals
        that include references from the context.

        Args:
            formula (Callable): The formula function.
            context (FormulaContext): The context to inject.

        Returns:
            Callable: The formula with injected context.
        """
        import types

        # Get the formula's code and globals
        formula_globals = formula.__globals__.copy()

        # For each variable referenced in the formula, try to get it from context
        code = formula.__code__
        for name in code.co_names:
            # Skip built-ins and existing globals
            if name in formula_globals or name in dir(__builtins__):
                continue

            # Try to get from context
            try:
                value = getattr(context, name)
                formula_globals[name] = value
            except AttributeError:
                # Variable not in context - will fail during evaluation
                pass

        # Create new function with updated globals
        new_func = types.FunctionType(
            code,
            formula_globals,
            formula.__name__,
            formula.__defaults__,
            formula.__closure__,
        )

        return new_func
