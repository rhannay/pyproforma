"""
LineItemSelection class for working with a subset of line items.

This module provides functionality for selecting and working with a subset
of line items from a ProformaModel.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyproforma.v2.proforma_model import ProformaModel
from pyproforma.table import Table

class LineItemSelection:
    """
    A selection of line items from a ProformaModel.

    LineItemSelection allows users to work with a subset of line items,
    making it easier to analyze or output specific groups of items.

    Args:
        model: The parent ProformaModel instance
        names: List of line item names to include in the selection

    Examples:
        >>> selection = model.select(['revenue', 'expenses', 'profit'])
        >>> selection.names
        ['revenue', 'expenses', 'profit']
    """

    def __init__(self, model: "ProformaModel", names: list[str]):
        """
        Initialize LineItemSelection.

        Args:
            model: The parent ProformaModel instance
            names: List of line item names to include in the selection

        Raises:
            ValueError: If any name is not a valid line item in the model
        """
        # Validate all names exist
        invalid_names = [name for name in names if name not in model.line_item_names]
        if invalid_names:
            raise ValueError(
                f"Line item(s) not found in model: {', '.join(invalid_names)}. "
                f"Available line items: {', '.join(sorted(model.line_item_names))}"
            )

        self._model = model
        self._names = names

    @property
    def names(self) -> list[str]:
        """
        Get the list of selected line item names.

        Returns:
            list[str]: List of line item names in the selection.

        Examples:
            >>> selection = model.select(['revenue', 'expenses'])
            >>> selection.names
            ['revenue', 'expenses']
        """
        return self._names

    def value(self, period: int) -> dict[str, float]:
        """
        Get values for all selected line items at a specific period.

        Args:
            period: The period to get values for.

        Returns:
            dict[str, float]: Dictionary mapping line item names to their values
                for the specified period.

        Raises:
            KeyError: If the period is not found for any line item.

        Examples:
            >>> selection = model.select(['revenue', 'expenses', 'profit'])
            >>> selection.value(2024)
            {'revenue': 100, 'expenses': 60, 'profit': 40}
        """
        result = {}
        for name in self._names:
            line_item = getattr(self._model.li, name)
            result[name] = line_item[period]
        return result

    def table(
        self,
        include_name: bool = True,
        include_label: bool = False,
    ) -> Table:
        """
        Generate a table containing the selected line items.

        Args:
            include_name: Whether to include the name column. Defaults to True.
            include_label: Whether to include the label column. Defaults to False.

        Returns:
            Table: A Table object containing the selected line items.

        Examples:
            >>> selection = model.select(['revenue', 'expenses', 'profit'])
            >>> table = selection.table()
            >>> table = selection.table(include_name=False, include_label=True)
        """
        return self._model.tables.line_items(
            line_items=self._names,
            include_name=include_name,
            include_label=include_label,
        )

    def __repr__(self):
        """Return a string representation of LineItemSelection."""
        return f"LineItemSelection(names={self._names!r})"
