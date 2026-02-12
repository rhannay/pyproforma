"""
LineItemValues class for storing calculated line item values across periods.

This class holds the calculated values for all line items across all periods in a model.
"""

from typing import Any


class LineItemValues:
    """
    Container for line item values across all periods.

    LineItemValues stores the calculated values for all line items in the model
    across all periods. It provides convenient access to values both by direct
    attribute access and through get methods.

    The internal storage is organized as a nested dictionary:
    {line_item_name: {period: value}}

    Attributes:
        _values (dict[str, dict[int, float]]): Nested dictionary mapping line item
            names to period-value dictionaries.
        _periods (list[int]): List of periods in the model.

    Examples:
        >>> li = LineItemValues(
        ...     {"revenue": {2024: 100, 2025: 110}},
        ...     periods=[2024, 2025]
        ... )
        >>> li.get("revenue", 2024)
        100
        >>> li.revenue[2024]
        100
    """

    def __init__(
        self,
        values: dict[str, dict[int, float]] | None = None,
        periods: list[int] | None = None,
        names: list[str] | None = None,
    ):
        """
        Initialize LineItemValues.

        Args:
            values (dict[str, dict[int, float]], optional): Nested dictionary mapping
                line item names to period-value dictionaries. Defaults to None (empty dict).
            periods (list[int], optional): List of periods in the model. Defaults to None.
            names (list[str], optional): List of valid line item names to pre-register.
                If provided, only these names can be accessed. Defaults to None.
        """
        self._periods = periods or []
        self._names = set(names) if names else None  # None means any name is valid
        
        # Pre-register all valid names if provided
        if self._names:
            self._values = {name: {} for name in self._names}
            # Merge in any provided values
            if values:
                for name, period_values in values.items():
                    if name in self._names:
                        self._values[name] = period_values
        else:
            self._values = values or {}

    def get(
        self, name: str, period: int | None = None
    ) -> float | dict[int, float] | None:
        """
        Get the value(s) for a line item.

        Args:
            name (str): The name of the line item.
            period (int, optional): The period to get the value for. If None,
                returns all period values as a dict. Defaults to None.

        Returns:
            float | dict[int, float] | None: The value for the specified period,
                all period values as a dict if period is None, or None if not found.
        """
        if name not in self._values:
            return None

        if period is None:
            return self._values[name]

        return self._values[name].get(period)

    def set(self, name: str, period: int, value: float) -> None:
        """
        Set the value for a line item at a specific period.

        Args:
            name (str): The name of the line item.
            period (int): The period to set the value for.
            value (float): The value to set.
            
        Raises:
            ValueError: If name is not registered (when names were provided at init).
        """
        # If names were registered, validate
        if self._names is not None and name not in self._names:
            raise ValueError(
                f"Cannot set value for unregistered line item '{name}'. "
                f"Available line items: {', '.join(sorted(self._names))}"
            )
        
        if name not in self._values:
            self._values[name] = {}
        self._values[name][period] = value

    def __getattr__(self, name: str) -> "LineItemValue":
        """
        Get line item values via attribute access.

        Returns a LineItemValue object that supports subscript notation
        for accessing period values.

        Args:
            name (str): The name of the line item.

        Returns:
            LineItemValue: Wrapper object supporting subscript access to period values.

        Raises:
            AttributeError: If the line item name is not registered or not found.
        """
        if name.startswith("_"):
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{name}'"
            )
        
        # If names were registered, check against the registry
        if self._names is not None and name not in self._names:
            raise AttributeError(
                f"Line item '{name}' is not registered. "
                f"Available line items: {', '.join(sorted(self._names))}"
            )
        
        if name in self._values:
            return LineItemValue(name, self._values[name])
        
        # If we get here with registered names, it means the name is valid but no values yet
        # This happens when accessing a line item before it's calculated for any period
        if self._names is not None:
            return LineItemValue(name, self._values[name])
        
        raise AttributeError(f"Line item '{name}' not found")

    def __repr__(self):
        """Return a string representation of LineItemValues."""
        return f"LineItemValues({self._values!r})"


class LineItemValue:
    """
    Wrapper for a single line item's values across periods.

    This class provides a convenient interface for accessing a single line item's
    values with subscript notation (e.g., revenue[2024]).

    Attributes:
        _name (str): The name of the line item.
        _values (dict[int, float]): Dictionary mapping periods to values.

    Examples:
        >>> values = {2024: 100, 2025: 110}
        >>> item = LineItemValue("revenue", values)
        >>> item[2024]
        100
        >>> item.get(2025)
        110
    """

    def __init__(self, name: str, values: dict[int, float]):
        """
        Initialize LineItemValue.

        Args:
            name (str): The name of the line item.
            values (dict[int, float]): Dictionary mapping periods to values.
        """
        self._name = name
        self._values = values

    def get(self, period: int, default: Any = None) -> float | None:
        """
        Get the value for a specific period.

        Args:
            period (int): The period to get the value for.
            default (Any, optional): Default value if period not found. Defaults to None.

        Returns:
            float | None: The value for the period, or default if not found.
        """
        return self._values.get(period, default)

    def __getitem__(self, period: int) -> float:
        """
        Get value using subscript notation.

        Args:
            period (int): The period to get the value for.

        Returns:
            float: The value for the period.

        Raises:
            KeyError: If the period is not found.
        """
        if period not in self._values:
            raise KeyError(f"Period {period} not found for line item '{self._name}'")
        return self._values[period]

    def __repr__(self):
        """Return a string representation of LineItemValue."""
        return f"LineItemValue(name={self._name!r}, values={self._values!r})"
