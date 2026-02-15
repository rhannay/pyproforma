"""
LineItemResult class for v2 API.

This class provides a results namespace wrapper similar to v1's LineItemResults,
but adapted for the v2 API design. It provides read-only access to line item
values and basic analysis methods.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyproforma.table import Table
    from pyproforma.v2.proforma_model import ProformaModel


class LineItemResult:
    """
    A read-only results wrapper for a single line item in a v2 model.

    LineItemResult provides convenient access to calculated values for a specific
    line item across all periods. It supports subscript notation for accessing
    period values and provides basic properties for exploring the item.

    This class is similar to v1's LineItemResults but simplified for v2:
    - Read-only access (no setters)
    - No chart/table support (may be added later)
    - Simpler metadata access

    Args:
        model: The parent ProformaModel instance
        name: The name of the line item

    Examples:
        >>> result = model['revenue']
        >>> result[2024]  # Get value for 2024
        100000
        >>> result.values  # Get all period values
        {2024: 100000, 2025: 110000}
        >>> result.name
        'revenue'
    """

    def __init__(self, model: "ProformaModel", name: str):
        """
        Initialize LineItemResult.

        Args:
            model: The parent ProformaModel instance
            name: The name of the line item

        Raises:
            AttributeError: If the line item name doesn't exist in the model
        """
        self._model = model
        self._name = name

        # Validate that the line item exists
        if name not in model.line_item_names:
            raise AttributeError(
                f"Line item '{name}' not found in model. "
                f"Available line items: {', '.join(sorted(model.line_item_names))}"
            )
        
        # Cache the line item specification for metadata access
        self._line_item_spec = getattr(model.__class__, name, None)

    def __repr__(self) -> str:
        """Return a string representation of the LineItemResult."""
        return f"LineItemResult(name='{self._name}')"

    def __str__(self) -> str:
        """Return a string representation showing the item name and values."""
        values_str = ", ".join(f"{period}: {value}" for period, value in self.values.items())
        return f"{self._name}: {{{values_str}}}"

    def __getitem__(self, period: int) -> float:
        """
        Get value for a specific period using subscript notation.

        Args:
            period (int): The period to get the value for

        Returns:
            float: The value for the specified period

        Raises:
            KeyError: If the period doesn't exist

        Examples:
            >>> result = model['revenue']
            >>> result[2024]
            100000
        """
        return self._model.get_value(self._name, period)

    @property
    def name(self) -> str:
        """
        Get the name of the line item.

        Returns:
            str: The line item name
        """
        return self._name

    @property
    def label(self) -> str | None:
        """
        Get the display label of the line item.

        Returns the user-defined label if available, otherwise returns None.
        This is a read-only property.

        Returns:
            str | None: The line item's display label, or None if not set

        Examples:
            >>> result = model['revenue']
            >>> result.label
            'Revenue'
        """
        if self._line_item_spec is not None and hasattr(self._line_item_spec, 'label'):
            return self._line_item_spec.label
        return None

    @property
    def values(self) -> dict[int, float]:
        """
        Get all period values for the line item.

        Returns:
            dict[int, float]: Dictionary mapping periods to values

        Examples:
            >>> result = model['revenue']
            >>> result.values
            {2024: 100000, 2025: 110000, 2026: 121000}
        """
        result = self._model._li.get(self._name, period=None)
        return result if result is not None else {}

    def value(self, period: int) -> float:
        """
        Get the value for a specific period.

        This is equivalent to using subscript notation: result[period]

        Args:
            period (int): The period to get the value for

        Returns:
            float: The value for the specified period

        Raises:
            KeyError: If the period doesn't exist

        Examples:
            >>> result = model['revenue']
            >>> result.value(2024)
            100000
        """
        return self._model.get_value(self._name, period)

    def table(self, include_name: bool = False) -> "Table":
        """
        Generate a table for this line item showing its values across periods.

        Args:
            include_name (bool, optional): Whether to include the name column.
                Defaults to False.

        Returns:
            Table: A formatted table with the line item's label and values

        Examples:
            >>> result = model['revenue']
            >>> table = result.table()
            >>> table = result.table(include_name=True)
        """
        from pyproforma.v2.tables.line_items import create_line_item_table

        return create_line_item_table(self._model, self._name, include_name=include_name)
