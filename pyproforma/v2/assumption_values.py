"""
AssumptionValues class for storing assumption values across periods.

This class holds the calculated/resolved values for all assumptions in a model.
"""

from typing import Any


class AssumptionValues:
    """
    Container for assumption values across all periods.

    AssumptionValues stores the resolved values for all assumptions in the model.
    Since assumptions are scalar values that apply to all periods, this class
    provides a simple interface to access assumption values.

    Attributes:
        _values (dict[str, float]): Dictionary mapping assumption names to their values.

    Examples:
        >>> av = AssumptionValues({"tax_rate": 0.21, "growth_rate": 0.1})
        >>> av.get("tax_rate")
        0.21
        >>> av.tax_rate
        0.21
    """

    def __init__(self, values: dict[str, float] | None = None):
        """
        Initialize AssumptionValues.

        Args:
            values (dict[str, float], optional): Dictionary mapping assumption names
                to their values. Defaults to None (empty dict).
        """
        self._values = values or {}

    def get(self, name: str, default: Any = None) -> float | None:
        """
        Get the value of an assumption.

        Args:
            name (str): The name of the assumption.
            default (Any, optional): Default value if assumption not found. Defaults to None.

        Returns:
            float | None: The assumption value, or default if not found.
        """
        return self._values.get(name, default)

    def __getattr__(self, name: str) -> float:
        """
        Get assumption value via attribute access.

        Args:
            name (str): The name of the assumption.

        Returns:
            float: The assumption value.

        Raises:
            AttributeError: If the assumption name is not found.
        """
        if name.startswith("_"):
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{name}'"
            )
        if name in self._values:
            return self._values[name]
        raise AttributeError(f"Assumption '{name}' not found")

    def __repr__(self):
        """Return a string representation of AssumptionValues."""
        return f"AssumptionValues({self._values!r})"
